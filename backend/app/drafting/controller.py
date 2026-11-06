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

    try:
        rendered_text, content_hash, _ = assemble_document(draft.template_id, inputs)
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
            body {{ font-family: 'Times New Roman', serif; line-height: 1.6; color: #1e293b; background: #fff; padding: 40px; margin: 0 auto; max-width: 800px; }}
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

    try:
        rendered_text, content_hash, _ = assemble_document(draft.template_id, inputs)
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
