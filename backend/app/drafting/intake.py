"""
Drafting Intake & Telegram Bridge Engine (PRD §6 & §8)
======================================================
Provides natural language parsing, structured parameter extraction,
document assembly, and court-ready PDF generation with SHA-256 seals
for both the Web Smart Forms Studio and the Telegram Bot Gateway.
"""

import os
import re
import uuid
from datetime import date, datetime
from typing import Dict, Any, Optional, Tuple, List

from app.drafting.registry import get_template, CANONICAL_TEMPLATES, TemplateManifest
from app.drafting.assembly import assemble_document, export_pdf, STORAGE_ROOT
from app.drafting.validators import format_indian_currency

# Map shorthand keywords to canonical template IDs
TEMPLATE_ALIASES = {
    "rent": "RENT_AGREEMENT_RESIDENTIAL_V1",
    "lease": "RENT_AGREEMENT_RESIDENTIAL_V1",
    "tenancy": "RENT_AGREEMENT_RESIDENTIAL_V1",
    "kiraya": "RENT_AGREEMENT_RESIDENTIAL_V1",
    "138": "NOTICE_DEMAND_138_V1",
    "cheque": "NOTICE_DEMAND_138_V1",
    "bounce": "NOTICE_DEMAND_138_V1",
    "check": "NOTICE_DEMAND_138_V1",
    "notice": "NOTICE_DEMAND_138_V1",
    "nda": "NDA_COMMERCIAL_V1",
    "confidentiality": "NDA_COMMERCIAL_V1",
    "consultant": "CONSULTANT_AGREEMENT_V1",
    "consultancy": "CONSULTANT_AGREEMENT_V1",
    "freelance": "CONSULTANT_AGREEMENT_V1",
    "contractor": "CONSULTANT_AGREEMENT_V1",
    "director": "BOARD_RES_DIR_APPT_V1",
    "board": "BOARD_RES_DIR_APPT_V1",
    "resolution": "BOARD_RES_GENERIC_V1",
    "petition": "PETITION_OPPR_MISMGMT_V1",
    "nclt": "PETITION_OPPR_MISMGMT_V1",
    "affidavit": "AFFIDAVIT_EVIDENCE_V1",
    "evidence": "AFFIDAVIT_EVIDENCE_V1",
    "due_diligence": "AFFIDAVIT_DIR_DD_V1",
    "mgt14": "MGT14_COVER_V1",
}


def resolve_template_id(query: str) -> Optional[str]:
    """Resolves a canonical template ID from a name, key, shorthand alias, or context clues."""
    clean = query.strip().lower()
    if clean in TEMPLATE_ALIASES:
        return TEMPLATE_ALIASES[clean]
    for alias, tid in TEMPLATE_ALIASES.items():
        if alias in clean:
            return tid
    for tid in CANONICAL_TEMPLATES.keys():
        if tid.lower() == clean or tid.lower().startswith(clean):
            return tid

    # Contextual keywords in full sentence
    if any(w in clean for w in ["rent", "lease", "tenant", "landlord", "kiraya"]):
        return "RENT_AGREEMENT_RESIDENTIAL_V1"
    if any(w in clean for w in ["cheque", "dishonour", "bounce", "138", "return memo", "payee", "drawer"]):
        return "NOTICE_DEMAND_138_V1"
    if any(w in clean for w in ["nda", "confidential", "trade secret", "disclosing", "receiving"]):
        return "NDA_COMMERCIAL_V1"
    if any(w in clean for w in ["consultant", "consulting", "freelance", "scope of work", "professional fee"]):
        return "CONSULTANT_AGREEMENT_V1"
    if any(w in clean for w in ["director", "din", "board meeting", "additional director"]):
        return "BOARD_RES_DIR_APPT_V1"

    return None


def parse_amount_expression(s: str) -> Optional[int]:
    """Parses expressions like '25k', '50k', '1.5 lakh', '50 lacs', '₹25,000', etc."""
    if not s:
        return None
    clean = str(s).strip()

    # 1. Lakhs
    m_lakh = re.search(r'([\d\.]+)\s*(?:lakh|lac|lacs|lakhs)', clean, re.IGNORECASE)
    if m_lakh:
        try:
            return int(float(m_lakh.group(1)) * 100000)
        except Exception:
            pass

    # 2. Thousands ('25k', '50 k')
    m_k = re.search(r'([\d\.]+)\s*k\b', clean, re.IGNORECASE)
    if m_k:
        try:
            return int(float(m_k.group(1)) * 1000)
        except Exception:
            pass

    # 3. Clean numeric digits
    num_str = re.sub(r'[^\d\.]', '', clean)
    if num_str:
        try:
            return int(float(num_str))
        except Exception:
            pass
    return None


def extract_inputs_from_prompt(tmpl: TemplateManifest, text: str, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Deterministically parses natural language intake text to extract
    structured legal parameters (names, addresses, amounts, dates, IDs).
    """
    inputs = dict(initial_inputs or {})
    schema_fields = [f["id"] for f in tmpl.schema_definition.get("fields", [])]

    # 1. Target Language detection
    if re.search(r'\b(hindi|devnagari|हिंदी|हिन्दी)\b', text, re.IGNORECASE):
        inputs["target_language"] = "hi"
    elif re.search(r'\b(bilingual|dual|both|द्विभाषी)\b', text, re.IGNORECASE):
        inputs["target_language"] = "bilingual"
    elif "target_language" not in inputs:
        inputs["target_language"] = "en"

    # 2. PANs & Aadhaar
    pans = re.findall(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', text)
    if pans:
        if "landlord_pan" in schema_fields and "landlord_pan" not in inputs:
            inputs["landlord_pan"] = pans[0]
            if len(pans) > 1 and "tenant_pan" not in inputs:
                inputs["tenant_pan"] = pans[1]
        elif "consultant_pan" in schema_fields and "consultant_pan" not in inputs:
            inputs["consultant_pan"] = pans[0]
        elif "deponent_pan" in schema_fields and "deponent_pan" not in inputs:
            inputs["deponent_pan"] = pans[0]

    # 3. CINs
    cins = re.findall(r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b', text)
    if cins and "company_cin" in schema_fields and "company_cin" not in inputs:
        inputs["company_cin"] = cins[0]

    # 4. DINs
    dins = re.findall(r'\b(?:DIN\s*[:\-]?\s*)?(\d{8})\b', text, re.IGNORECASE)
    if dins:
        if "director_din" in schema_fields and "director_din" not in inputs:
            inputs["director_din"] = dins[0]
        elif "deponent_din" in schema_fields and "deponent_din" not in inputs:
            inputs["deponent_din"] = dins[0]

    # 5. Cheque Number (6 digits)
    chq_match = re.search(r'(?:cheque|chq|instrument|no\.?|#)\s*[:\-]?\s*(\d{6})\b', text, re.IGNORECASE)
    if chq_match and "cheque_no" in schema_fields and "cheque_no" not in inputs:
        inputs["cheque_no"] = chq_match.group(1)

    # 6. Currency amounts
    # Monthly rent
    rent_match = re.search(r'(?:rent|kiraya|monthly rent|monthly)\s*(?:is|of|amount|@)?\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|lakh|lac|lacs|lakhs)?)', text, re.IGNORECASE)
    if rent_match and "monthly_rent" in schema_fields and "monthly_rent" not in inputs:
        val = parse_amount_expression(rent_match.group(1))
        if val:
            inputs["monthly_rent"] = val

    # Security Deposit
    dep_match = re.search(r'(?:deposit|security|security deposit|advance)\s*(?:is|of|amount)?\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|lakh|lac|lacs|lakhs)?)', text, re.IGNORECASE)
    if dep_match and "security_deposit" in schema_fields and "security_deposit" not in inputs:
        val = parse_amount_expression(dep_match.group(1))
        if val:
            inputs["security_deposit"] = val

    # Cheque / Fee / General Amount
    amt_match = re.search(r'(?:cheque amount|amount|fee|sum of|for ₹|for rs\.?)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|lakh|lac|lacs|lakhs)?)', text, re.IGNORECASE)
    if amt_match:
        val = parse_amount_expression(amt_match.group(1))
        if val:
            if "cheque_amount" in schema_fields and "cheque_amount" not in inputs:
                inputs["cheque_amount"] = val
            if "fee_amount" in schema_fields and "fee_amount" not in inputs:
                inputs["fee_amount"] = val

    # Maintenance charges
    maint_match = re.search(r'(?:maintenance|society charges|cam charges)\s*(?:is|of|amount)?\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|lakh|lac|lacs|lakhs)?)', text, re.IGNORECASE)
    if maint_match and "maintenance_charges" in schema_fields and "maintenance_charges" not in inputs:
        val = parse_amount_expression(maint_match.group(1))
        if val:
            inputs["maintenance_charges"] = val

    # 7. Dates
    date_matches = re.findall(r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b', text)
    if date_matches:
        d, m, y = date_matches[0]
        iso_date = f"{y}-{int(m):02d}-{int(d):02d}"
        for d_field in ["commencement_date", "effective_date", "cheque_date", "meeting_date"]:
            if d_field in schema_fields and d_field not in inputs:
                inputs[d_field] = iso_date
                break

    # 8. Tenure & Lock-in Months
    tenure_m = re.search(r'(\d+)\s*(?:months?|maheene|mahine|m)\s*(?:tenure|period|lease)?\b', text, re.IGNORECASE)
    if tenure_m and "tenure_months" in schema_fields and "tenure_months" not in inputs:
        inputs["tenure_months"] = int(tenure_m.group(1))

    lockin_m = re.search(r'(?:lock[\s\-]?in|lockin)\s*(?:of|is|period)?\s*(\d+)\s*(?:months?|m)?', text, re.IGNORECASE)
    if lockin_m and "lock_in_months" in schema_fields and "lock_in_months" not in inputs:
        inputs["lock_in_months"] = int(lockin_m.group(1))

    notice_m = re.search(r'(?:notice|notice period)\s*(?:of|is)?\s*(\d+)\s*(?:days?|din)', text, re.IGNORECASE)
    if notice_m and "notice_period_days" in schema_fields and "notice_period_days" not in inputs:
        inputs["notice_period_days"] = int(notice_m.group(1))

    duration_y = re.search(r'(\d+)\s*(?:years?|saal|yr|yrs)', text, re.IGNORECASE)
    if duration_y and "duration_years" in schema_fields and "duration_years" not in inputs:
        inputs["duration_years"] = int(duration_y.group(1))

    # 9. Parties & Names
    # Landlord
    ll_m = re.search(r'(?:landlord|lessor|owner|makan malik)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\stenant|\sresiding|\swith|$|\n)', text, re.IGNORECASE)
    if ll_m and "landlord_name" in schema_fields and "landlord_name" not in inputs:
        c = ll_m.group(1).strip()
        if len(c) > 2:
            inputs["landlord_name"] = c

    # Tenant
    ten_m = re.search(r'(?:tenant|lessee|kirayedar)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\slandlord|\sresiding|\swith|$|\n)', text, re.IGNORECASE)
    if ten_m and "tenant_name" in schema_fields and "tenant_name" not in inputs:
        c = ten_m.group(1).strip()
        if len(c) > 2:
            inputs["tenant_name"] = c

    # Payee & Drawer for 138 Notice
    payee_m = re.search(r'(?:payee|client|complainant)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\sdrawer|\sto\s|$|\n)', text, re.IGNORECASE)
    if payee_m and "payee_name" in schema_fields and "payee_name" not in inputs:
        c = payee_m.group(1).strip()
        if len(c) > 2:
            inputs["payee_name"] = c

    drawer_m = re.search(r'(?:drawer|accused|issued by)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\spayee|\sagainst\s|$|\n)', text, re.IGNORECASE)
    if drawer_m and "drawer_name" in schema_fields and "drawer_name" not in inputs:
        c = drawer_m.group(1).strip()
        if len(c) > 2:
            inputs["drawer_name"] = c

    # Bank name
    bank_m = re.search(r'(?:bank|branch|drawn on|drawee bank)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+?(?:bank|branch))', text, re.IGNORECASE)
    if bank_m and "bank_name" in schema_fields and "bank_name" not in inputs:
        inputs["bank_name"] = bank_m.group(1).strip()

    # Dishonour reason
    if "dishonour_reason" in schema_fields and "dishonour_reason" not in inputs:
        if re.search(r'insufficient|funds|balance', text, re.IGNORECASE):
            inputs["dishonour_reason"] = "Funds Insufficient"
        elif re.search(r'closed', text, re.IGNORECASE):
            inputs["dishonour_reason"] = "Account Closed"
        elif re.search(r'stop', text, re.IGNORECASE):
            inputs["dishonour_reason"] = "Stop Payment by Drawer"
        elif re.search(r'signature|sign', text, re.IGNORECASE):
            inputs["dishonour_reason"] = "Signatures Differ"

    # Disclosing & Receiving for NDA
    disc_m = re.search(r'(?:disclosing|discloser|company)\s*(?:is|name|:)?\s*([A-Za-z0-9\s\.\'\-]+?)(?:,|\.|\sand\s|\sreceiving|$|\n)', text, re.IGNORECASE)
    if disc_m and "disclosing_party" in schema_fields and "disclosing_party" not in inputs:
        c = disc_m.group(1).strip()
        if len(c) > 2:
            inputs["disclosing_party"] = c

    rec_m = re.search(r'(?:receiving|recipient|counterparty)\s*(?:is|name|:)?\s*([A-Za-z0-9\s\.\'\-]+?)(?:,|\.|\sand\s|\sdisclosing|$|\n)', text, re.IGNORECASE)
    if rec_m and "receiving_party" in schema_fields and "receiving_party" not in inputs:
        c = rec_m.group(1).strip()
        if len(c) > 2:
            inputs["receiving_party"] = c

    # Client & Consultant
    cli_m = re.search(r'(?:client|hiring|company)\s*(?:is|name|:)?\s*([A-Za-z0-9\s\.\'\-]+?)(?:,|\.|\sand\s|\sconsultant|$|\n)', text, re.IGNORECASE)
    if cli_m and "client_name" in schema_fields and "client_name" not in inputs:
        c = cli_m.group(1).strip()
        if len(c) > 2:
            inputs["client_name"] = c

    cons_m = re.search(r'(?:consultant|specialist|freelancer)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\sclient|$|\n)', text, re.IGNORECASE)
    if cons_m and "consultant_name" in schema_fields and "consultant_name" not in inputs:
        c = cons_m.group(1).strip()
        if len(c) > 2:
            inputs["consultant_name"] = c

    # Director / Appointee
    dir_m = re.search(r'(?:director|appointee|candidate)\s*(?:is|name|:)?\s*([A-Za-z\s\.\'\-]+?)(?:,|\.|\sand\s|\swith|$|\n)', text, re.IGNORECASE)
    if dir_m and "director_name" in schema_fields and "director_name" not in inputs:
        c = dir_m.group(1).strip()
        if len(c) > 2:
            inputs["director_name"] = c

    # Premises / Address
    prem_m = re.search(r'(?:premises|property|flat|house|office|shop|situated at|address of property)\s*(?:is|at|:)?\s*([A-Za-z0-9\s,\-\/\#\.\'\&]+?)(?:\.|\n|monthly rent|rent|deposit|$)', text, re.IGNORECASE)
    if prem_m and "premises_address" in schema_fields and "premises_address" not in inputs:
        c = prem_m.group(1).strip()
        if len(c) > 6:
            inputs["premises_address"] = c

    # Fill schema defaults for remaining unfilled fields
    for f in tmpl.schema_definition.get("fields", []):
        f_id = f["id"]
        if f.get("default") is not None and f_id not in inputs:
            inputs[f_id] = f["default"]

    return inputs


def generate_draft_package(
    query_or_template_id: str,
    details_text: str,
    target_language: Optional[str] = None
) -> Tuple[Dict[str, Any], str, str]:
    """
    Core end-to-end legal auto-drafting execution:
    1. Resolves template manifest
    2. Extracts structured parameters
    3. Assembles document with Jinja2 and clause verification
    4. Renders stamped PDF with SHA-256 seal
    5. Returns (summary_dict, pdf_file_path, rendered_text)
    """
    tmpl_id = resolve_template_id(query_or_template_id)
    if not tmpl_id:
        tmpl_id = "RENT_AGREEMENT_RESIDENTIAL_V1"

    tmpl = get_template(tmpl_id)
    if not tmpl:
        raise ValueError(f"Template '{tmpl_id}' not found.")

    inputs = extract_inputs_from_prompt(tmpl, details_text)
    if target_language:
        inputs["target_language"] = target_language

    # Assemble legal instrument
    rendered_text, content_hash, verification_report = assemble_document(
        template_id=tmpl_id,
        input_data=inputs,
        allow_partial=True
    )

    # Export court-ready stamped PDF
    unique_suffix = uuid.uuid4().hex[:8]
    filename_base = f"HALO_{tmpl_id}_{unique_suffix}"
    pdf_path = export_pdf(rendered_text, content_hash, filename_base)

    # Compile structured summary
    lang_name = "English (Standard Legal)"
    if inputs.get("target_language") == "hi":
        lang_name = "हिंदी (Devnagari)"
    elif inputs.get("target_language") == "bilingual":
        lang_name = "Bilingual (द्विभाषी - English + Hindi)"

    summary = {
        "template_id": tmpl_id,
        "title": tmpl.title,
        "statutory_anchor": tmpl.statutory_anchor,
        "language": lang_name,
        "content_sha256": content_hash,
        "inputs": inputs,
        "pdf_path": pdf_path,
        "verification_passed": verification_report.all_verified if hasattr(verification_report, "all_verified") else True,
    }

    return summary, pdf_path, rendered_text
