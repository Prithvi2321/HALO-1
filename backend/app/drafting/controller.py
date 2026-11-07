"""
Drafting Controller & FastAPI Router (PRD §11.1)
================================================
Endpoints:
- GET /templates
- GET /templates/{id}
- POST /drafts
- GET /drafts
- GET /drafts/{id}
- PUT /drafts/{id}/inputs
- POST /drafts/{id}/generate
- GET /drafts/{id}/preview
- POST /drafts/{id}/exports
- GET /exports/{id}
- GET /exports/download/{filename}
"""

import json
import uuid
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.auth.repository import get_session
from app.workspace.model import Draft, DraftVersion, Export, now_utc
from app.workspace.repository import TenantRepository
from app.drafting.registry import list_templates, get_template
from app.drafting.assembly import (
    assemble_document,
    export_docx,
    export_pdf,
    AssemblyError,
    STORAGE_ROOT,
)

router = APIRouter(tags=["drafting"])


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class DraftCreateRequest(BaseModel):
    template_id: str
    title: Optional[str] = None
    matter_id: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    firm_id: Optional[str] = "firm_default"


class DraftInputsUpdateRequest(BaseModel):
    inputs: Dict[str, Any]
    title: Optional[str] = None


class ExportRequest(BaseModel):
    format: str = "pdf"  # docx | pdf
    allow_partial: bool = True
    target_language: Optional[str] = None


class SmartIntakeRequest(BaseModel):
    template_id: str
    message: Optional[str] = None
    file_content: Optional[str] = None
    file_name: Optional[str] = None
    current_inputs: Dict[str, Any] = Field(default_factory=dict)
    target_language: str = "en"


# ─── Template Endpoints ───────────────────────────────────────────────────────

@router.get("/templates")
def api_list_templates(category: Optional[str] = Query(None)):
    """List available statutory and pleading templates, optionally filtered by category."""
    return list_templates(category=category)


@router.get("/templates/{template_id}")
def api_get_template(template_id: str):
    """Returns the template manifest and active JSON form schema."""
    tmpl = get_template(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found."
        )
    return tmpl


# ─── Drafts Endpoints ─────────────────────────────────────────────────────────

@router.get("/drafts")
def api_list_drafts(
    matter_id: Optional[str] = Query(None),
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Lists drafts for the firm, optionally filtered by matter_id."""
    repo = TenantRepository(session, firm_id=firm_id)
    return repo.list_drafts(matter_id=matter_id)


@router.post("/drafts", status_code=status.HTTP_201_CREATED)
def api_create_draft(
    req: DraftCreateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Creates a new draft from template and initial inputs."""
    tmpl = get_template(req.template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{req.template_id}' does not exist."
        )

    repo = TenantRepository(session, firm_id=firm_id)
    title = req.title or tmpl.title

    draft = Draft(
        firm_id=firm_id,
        matter_id=req.matter_id,
        template_id=req.template_id,
        title=title,
        status="DRAFT"
    )
    repo.create_draft(draft)

    draft_data = draft.model_dump()

    # Initial version
    v1 = DraftVersion(
        draft_id=draft.id,
        version_no=1,
        input_json=json.dumps(req.inputs or {}),
    )
    repo.add_draft_version(v1)

    return {"draft": draft_data, "version": v1.model_dump()}


@router.get("/drafts/{draft_id}")
def api_get_draft(
    draft_id: str,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Returns draft metadata, versions, and current working input."""
    repo = TenantRepository(session, firm_id=firm_id)
    draft = repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    versions = repo.get_draft_versions(draft_id)
    latest_inputs = json.loads(versions[0].input_json) if versions else {}

    return {
        "draft": draft.model_dump(),
        "versions": [v.model_dump() for v in versions],
        "current_inputs": latest_inputs,
        "latest_version": versions[0].model_dump() if versions else None
    }


@router.put("/drafts/{draft_id}/inputs")
def api_autosave_inputs(
    draft_id: str,
    req: DraftInputsUpdateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Autosaves inputs to draft record, updating the latest draft version."""
    repo = TenantRepository(session, firm_id=firm_id)
    draft = repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    if req.title:
        draft.title = req.title
    repo.update_draft(draft)

    versions = repo.get_draft_versions(draft_id)
    if versions:
        latest = versions[0]
        latest.input_json = json.dumps(req.inputs)
        session.add(latest)
        session.commit()
    else:
        v = DraftVersion(draft_id=draft.id, version_no=1, input_json=json.dumps(req.inputs))
        repo.add_draft_version(v)

    return {"status": "saved", "updated_at": draft.updated_at.isoformat()}


@router.post("/drafts/{draft_id}/generate")
def api_generate_draft(
    draft_id: str,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Validates, assembles legal text, computes SHA-256 hash, and performs clause verification."""
    repo = TenantRepository(session, firm_id=firm_id)
    draft = repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    versions = repo.get_draft_versions(draft_id)
    if not versions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs found for draft.")

    latest = versions[0]
    inputs = json.loads(latest.input_json)

    try:
        rendered_text, content_hash, verification_report = assemble_document(draft.template_id, inputs)
    except AssemblyError as ae:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(ae), "fields": ae.field_errors}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assembly failed: {str(e)}"
        )

    # Save to a new version record
    new_version_no = latest.version_no + 1
    new_version = DraftVersion(
        draft_id=draft.id,
        version_no=new_version_no,
        input_json=json.dumps(inputs),
        content_sha256=content_hash,
        verification_report=json.dumps(verification_report.model_dump())
    )
    repo.add_draft_version(new_version)

    draft.status = "READY"
    repo.update_draft(draft)

    return {
        "status": "READY",
        "draft_id": draft.id,
        "version_no": new_version_no,
        "content_sha256": content_hash,
        "verification_report": verification_report,
        "rendered_preview": rendered_text
    }


@router.get("/drafts/{draft_id}/preview")
def api_preview_draft(
    draft_id: str,
    target_language: Optional[str] = None,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Returns HTML preview of the assembled document text."""
    repo = TenantRepository(session, firm_id=firm_id)
    draft = repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    versions = repo.get_draft_versions(draft_id)
    inputs = json.loads(versions[0].input_json) if versions else {}
    if target_language:
        inputs["target_language"] = target_language

    try:
        rendered_text, content_hash, _ = assemble_document(draft.template_id, inputs, allow_partial=True)
    except AssemblyError as ae:
        return HTMLResponse(
            content=f"<div style='color:#b91c1c;padding:20px;font-family:sans-serif;'><h3>Validation Pending</h3><p>{str(ae)}</p></div>"
        )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Nirmala UI', 'Mangal', 'Times New Roman', serif; line-height: 1.6; color: #1e293b; background: #fff; padding: 40px; margin: 0 auto; max-width: 800px; }}
            pre {{ white-space: pre-wrap; font-family: inherit; font-size: 15px; }}
            .seal {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-family: monospace; font-size: 11px; color: #64748b; }}
        </style>
    </head>
    <body>
        <pre>{rendered_text}</pre>
        <div class="seal">
            🔒 HALO Cryptographic Seal: SHA-256 <code>{content_hash}</code><br>
            Statutory Anchor: {get_template(draft.template_id).statutory_anchor}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/drafts/{draft_id}/exports")
def api_export_draft(
    draft_id: str,
    req: ExportRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Exports draft to .docx or .pdf with embedded SHA-256 checksum."""
    repo = TenantRepository(session, firm_id=firm_id)
    draft = repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")

    versions = repo.get_draft_versions(draft_id)
    if not versions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft has no inputs.")

    latest = versions[0]
    inputs = json.loads(latest.input_json)
    if req.target_language:
        inputs["target_language"] = req.target_language

    try:
        rendered_text, content_hash, _ = assemble_document(draft.template_id, inputs, allow_partial=req.allow_partial)
    except AssemblyError as ae:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(ae), "fields": ae.field_errors}
        )

    base_name = f"{draft.template_id}_{draft_id[:8]}_v{latest.version_no}"
    fmt = req.format.lower()

    if fmt == "docx":
        out_path = export_docx(rendered_text, base_name)
    elif fmt == "pdf":
        out_path = export_pdf(rendered_text, content_hash, base_name)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported formats: docx, pdf")

    filename = Path(out_path).name
    exp = Export(
        draft_version_id=latest.id,
        format=fmt,
        storage_key=filename,
        status="READY"
    )
    session.add(exp)
    session.commit()
    session.refresh(exp)

    download_url = f"/api/v1/exports/download/{filename}"
    return {
        "export_id": exp.id,
        "format": fmt,
        "filename": filename,
        "download_url": download_url,
        "content_sha256": content_hash,
        "status": "READY"
    }


@router.get("/exports/download/{filename}")
def api_download_export_file(filename: str):
    """Direct local download endpoint for exported legal instruments."""
    path = STORAGE_ROOT / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found.")

    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=filename
    )


@router.post("/drafts/smart-intake")
def api_smart_intake(req: SmartIntakeRequest):
    """
    Intelligent Conversational & Document Intake Engine:
    Parses user natural chat responses and uploaded file text in English, Hindi, or Hinglish,
    extracts structured legal variables (PAN, Aadhaar, names, addresses, amounts, dates, tenure),
    auto-populates template schema fields, and guides the lawyer with conversational feedback.
    """
    tmpl = get_template(req.template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{req.template_id}' not found."
        )

    inputs = dict(req.current_inputs or {})
    newly_extracted = []
    
    raw_texts = []
    if req.message:
        raw_texts.append(req.message)
    if req.file_content:
        raw_texts.append(req.file_content)
    combined = "\n".join(raw_texts).strip()

    # Detect language if mentioned
    lower_comb = combined.lower()
    if any(k in lower_comb for k in ["hindi", "हिंदी", "devnagari"]):
        inputs["target_language"] = "hi"
    elif any(k in lower_comb for k in ["bilingual", "द्विभाषी", "both languages"]):
        inputs["target_language"] = "bilingual"
    elif any(k in lower_comb for k in ["english", "अंग्रेजी"]):
        inputs["target_language"] = "en"
    elif req.target_language and "target_language" not in inputs:
        inputs["target_language"] = req.target_language

    # 1. PAN extraction
    pans = re.findall(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', combined)
    if pans:
        fields = [f["id"] for f in tmpl.schema_definition.get("fields", [])]
        if "landlord_pan" in fields and "landlord_pan" not in inputs:
            inputs["landlord_pan"] = pans[0]
            newly_extracted.append("landlord_pan")
            if len(pans) > 1 and "tenant_pan" not in inputs:
                inputs["tenant_pan"] = pans[1]
                newly_extracted.append("tenant_pan")
        elif "consultant_pan" in fields and "consultant_pan" not in inputs:
            inputs["consultant_pan"] = pans[0]
            newly_extracted.append("consultant_pan")

    # 2. CIN extraction
    cins = re.findall(r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b', combined)
    if cins and "company_cin" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "company_cin" not in inputs:
        inputs["company_cin"] = cins[0]
        newly_extracted.append("company_cin")

    # 3. DIN extraction
    dins = re.findall(r'\b(?:DIN\s*[:\-]?\s*)?(\d{8})\b', combined)
    if dins and "director_din" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "director_din" not in inputs:
        inputs["director_din"] = dins[0]
        newly_extracted.append("director_din")

    # 4. Cheque Number extraction (6 digits)
    chq_match = re.search(r'(?:cheque|chq|instrument|no\.?|#)\s*[:\-]?\s*(\d{6})\b', combined, re.IGNORECASE)
    if chq_match and "cheque_no" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "cheque_no" not in inputs:
        inputs["cheque_no"] = chq_match.group(1)
        newly_extracted.append("cheque_no")

    # 5. Currency Amounts
    def parse_lakh(s: str) -> Optional[int]:
        m = re.search(r'([\d\.]+)\s*(?:lakh|lac|lacs|lakhs)', s, re.IGNORECASE)
        if m:
            return int(float(m.group(1)) * 100000)
        return None

    # Monthly rent
    rent_match = re.search(r'(?:rent|kiraya|monthly rent|monthly)\s*(?:is|of|amount|@)?\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]+|\d+(?:\.\d+)?\s*lakh)', combined, re.IGNORECASE)
    if rent_match and "monthly_rent" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "monthly_rent" not in inputs:
        val_str = rent_match.group(1).replace(",", "").strip()
        lakh_val = parse_lakh(val_str)
        inputs["monthly_rent"] = lakh_val if lakh_val else int(float(val_str))
        newly_extracted.append("monthly_rent")

    # Security Deposit
    dep_match = re.search(r'(?:deposit|security|security deposit|advance)\s*(?:is|of|amount)?\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]+|\d+(?:\.\d+)?\s*lakh)', combined, re.IGNORECASE)
    if dep_match and "security_deposit" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "security_deposit" not in inputs:
        val_str = dep_match.group(1).replace(",", "").strip()
        lakh_val = parse_lakh(val_str)
        inputs["security_deposit"] = lakh_val if lakh_val else int(float(val_str))
        newly_extracted.append("security_deposit")

    # General Fee / Cheque amount
    amt_match = re.search(r'(?:amount|fee|sum of|cheque amount|for ₹|for rs\.?)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]+|\d+(?:\.\d+)?\s*lakh)', combined, re.IGNORECASE)
    if amt_match:
        val_str = amt_match.group(1).replace(",", "").strip()
        lakh_val = parse_lakh(val_str)
        extracted_amt = lakh_val if lakh_val else int(float(val_str))
        fields = [f["id"] for f in tmpl.schema_definition.get("fields", [])]
        if "amount" in fields and "amount" not in inputs:
            inputs["amount"] = extracted_amt
            newly_extracted.append("amount")
        if "fee_amount" in fields and "fee_amount" not in inputs:
            inputs["fee_amount"] = extracted_amt
            newly_extracted.append("fee_amount")

    # 6. Dates
    date_matches = re.findall(r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b', combined)
    if date_matches:
        d, m, y = date_matches[0]
        iso_date = f"{y}-{int(m):02d}-{int(d):02d}"
        for d_field in ["commencement_date", "effective_date", "cheque_date", "meeting_date"]:
            if d_field in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and d_field not in inputs:
                inputs[d_field] = iso_date
                newly_extracted.append(d_field)
                break
    else:
        for d_field in ["commencement_date", "effective_date"]:
            if d_field in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and d_field not in inputs:
                inputs[d_field] = date.today().isoformat()
                newly_extracted.append(d_field)

    # 7. Tenure & Lock-in
    tenure_m = re.search(r'(\d+)\s*(?:months?|maheene|mahine|m)\s*(?:tenure|period|lease)?\b', combined, re.IGNORECASE)
    if tenure_m and "tenure_months" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "tenure_months" not in inputs:
        inputs["tenure_months"] = int(tenure_m.group(1))
        newly_extracted.append("tenure_months")

    lockin_m = re.search(r'(?:lock[\s\-]?in|lockin)\s*(?:of|is|period)?\s*(\d+)\s*(?:months?|m)?', combined, re.IGNORECASE)
    if lockin_m and "lock_in_months" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "lock_in_months" not in inputs:
        inputs["lock_in_months"] = int(lockin_m.group(1))
        newly_extracted.append("lock_in_months")

    notice_m = re.search(r'(?:notice|notice period)\s*(?:of|is)?\s*(\d+)\s*(?:days?|din)', combined, re.IGNORECASE)
    if notice_m and "notice_period_days" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "notice_period_days" not in inputs:
        inputs["notice_period_days"] = int(notice_m.group(1))
        newly_extracted.append("notice_period_days")

    # 8. Names & Entities
    ll_m = re.search(r'(?:landlord|lessor|owner|makan malik)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\stenant|\sresiding|\swith|$|\n)', combined, re.IGNORECASE)
    if ll_m and "landlord_name" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "landlord_name" not in inputs:
        name_clean = ll_m.group(1).strip()
        if len(name_clean) > 2:
            inputs["landlord_name"] = name_clean
            newly_extracted.append("landlord_name")

    ten_m = re.search(r'(?:tenant|lessee|kirayedar)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\slandlord|\sresiding|\swith|$|\n)', combined, re.IGNORECASE)
    if ten_m and "tenant_name" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "tenant_name" not in inputs:
        name_clean = ten_m.group(1).strip()
        if len(name_clean) > 2:
            inputs["tenant_name"] = name_clean
            newly_extracted.append("tenant_name")

    prem_m = re.search(r'(?:premises|property|flat|house|office|shop|situated at|address of property)\s*(?:is|at|:)?\s*([A-Za-z0-9\s,\-\/\#\.\'\&]+?)(?:\.|\n|monthly rent|rent|deposit|$)', combined, re.IGNORECASE)
    if prem_m and "premises_address" in [f["id"] for f in tmpl.schema_definition.get("fields", [])] and "premises_address" not in inputs:
        addr_clean = prem_m.group(1).strip()
        if len(addr_clean) > 6:
            inputs["premises_address"] = addr_clean
            newly_extracted.append("premises_address")

    # 9. Apply schema defaults for fields still unfilled
    fields_list = tmpl.schema_definition.get("fields", [])
    required_fields = [f for f in fields_list if f.get("required")]
    for f in fields_list:
        if f.get("default") is not None and f["id"] not in inputs:
            inputs[f["id"]] = f["default"]

    # Calculate completion percentage
    filled_req = [f["id"] for f in required_fields if inputs.get(f["id"]) not in [None, ""]]
    completion_percent = int((len(filled_req) / len(required_fields)) * 100) if required_fields else 100

    unfilled = [f for f in required_fields if inputs.get(f["id"]) in [None, ""]]
    unfilled_labels = [f.get("label", f["id"]) for f in unfilled]

    is_hindi = inputs.get("target_language") == "hi"

    if completion_percent >= 100:
        if is_hindi:
            ai_msg = "🎉 **अनुबंध पूर्णतः तैयार है!** सभी आवश्यक विवरण सफलतापूर्वक भर दिए गए हैं। आप दाईं ओर दस्तावेज़ का पूर्वावलोकन (Preview) देख सकते हैं और ऊपर दिए गए बटन से **DOCX** या **PDF** डाउनलोड कर सकते हैं।"
        else:
            ai_msg = "🎉 **Drafting Complete!** All mandatory legal details have been verified and populated. You can inspect the live legal preview on the right and click **Download DOCX** or **Download PDF** above to export."
    else:
        next_field = unfilled[0] if unfilled else None
        next_label = next_field.get("label", "") if next_field else ""
        
        extracted_summary = ""
        if newly_extracted:
            extracted_summary = f"✅ **Extracted {len(newly_extracted)} detail(s)**: *{', '.join(newly_extracted)}*.\n\n"
        
        if is_hindi:
            ai_msg = (
                f"{extracted_summary}📋 **प्रगति: {completion_percent}% पूर्ण**\n\n"
                f"कृपया निम्नलिखित विवरण प्रदान करें:\n"
                f"👉 **{next_label}**"
            )
        else:
            ai_msg = (
                f"{extracted_summary}📋 **Progress: {completion_percent}% Completed**\n\n"
                f"To finalize the document, please provide:\n"
                f"👉 **{next_label}**"
            )

    return {
        "updated_inputs": inputs,
        "ai_response": ai_msg,
        "completion_percent": completion_percent,
        "missing_fields": unfilled_labels,
        "newly_extracted_fields": newly_extracted
    }
