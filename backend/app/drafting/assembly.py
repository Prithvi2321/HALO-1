"""
Document Assembly & Export Engine (PRD §6.6)
============================================
Handles validation, normalization, Jinja2 rendering, clause verification hook,
.docx generation via python-docx, and .pdf export with embedded SHA-256 footer.
"""

import os
import hashlib
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from jinja2 import Template

from app.drafting.validators import (
    validate_cin,
    validate_din,
    validate_pan,
    validate_gstin,
    validate_date_not_future,
    format_indian_currency,
    number_to_indian_words,
    format_legal_date,
)
from app.drafting.registry import get_template, TemplateManifest
from app.ports.verification import (
    verification_port,
    ClauseInput,
    VerificationReport,
)

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "exports"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


class AssemblyError(Exception):
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.field_errors = field_errors or {}


def validate_input(schema: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, str]:
    """Validates submitted inputs against schema and Indian law validators."""
    errors = {}
    fields = schema.get("fields", [])

    for f in fields:
        f_id = f.get("id")
        label = f.get("label", f_id)
        val = input_data.get(f_id)

        # Check required
        if f.get("required") and (val is None or (isinstance(val, str) and not val.strip())):
            errors[f_id] = f"{label} is required."
            continue

        if val is None or val == "":
            continue

        # Validator primitives
        val_name = f.get("validator")
        if val_name == "cin":
            valid, err = validate_cin(str(val))
            if not valid:
                errors[f_id] = err
        elif val_name == "din":
            valid, err = validate_din(str(val))
            if not valid:
                errors[f_id] = err
        elif val_name == "pan":
            valid, err = validate_pan(str(val))
            if not valid:
                errors[f_id] = err
        elif val_name == "gstin":
            valid, err = validate_gstin(str(val))
            if not valid:
                errors[f_id] = err
        elif val_name == "date_not_future":
            valid, err = validate_date_not_future(val)
            if not valid:
                errors[f_id] = err

    return errors


def normalize_context(template: TemplateManifest, raw_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepares enriched and normalized context dictionary for Jinja2 rendering."""
    ctx = dict(raw_inputs)
    now = datetime.now(timezone.utc)
    ctx["current_date_formatted"] = format_legal_date(now.date())

    # Date fields normalization
    for f in template.schema_definition.get("fields", []):
        f_id = f.get("id")
        f_type = f.get("type")
        val = ctx.get(f_id)
        if f_type == "date" and val:
            ctx[f"{f_id}_formatted"] = format_legal_date(val)

    # Resolution date specific due dates (e.g. MGT-14 30 days)
    if "resolution_date" in ctx and ctx["resolution_date"]:
        try:
            r_date = datetime.fromisoformat(str(ctx["resolution_date"]).split("T")[0]).date()
            due_date = r_date + timedelta(days=30)
            ctx["due_date_formatted"] = format_legal_date(due_date)
        except Exception:
            pass

    # Ensure target_language has a valid normalized value ('en', 'hi', 'bilingual')
    tl = str(ctx.get("target_language", "")).lower().strip()
    if tl in ["hi", "hindi", "devnagari"]:
        ctx["target_language"] = "hi"
    elif tl in ["bilingual", "bi", "dual"]:
        ctx["target_language"] = "bilingual"
    else:
        ctx["target_language"] = "en"

    # Cheque / Rent / Fee / Amount fields normalization
    amount_keys = ["cheque_amount", "monthly_rent", "security_deposit", "consultant_fee"]
    for amt_field in amount_keys:
        if amt_field in ctx and ctx[amt_field] is not None and str(ctx[amt_field]).strip():
            try:
                clean_str = str(ctx[amt_field]).replace(",", "").replace("₹", "").replace("/-", "").strip()
                amt = float(clean_str)
                fmt_curr = format_indian_currency(amt)
                words = number_to_indian_words(amt)
                ctx[f"{amt_field}_formatted"] = fmt_curr
                ctx[f"{amt_field}_words"] = words
                if amt_field == "cheque_amount" or "formatted_currency" not in ctx:
                    ctx["formatted_currency"] = fmt_curr
                    ctx["amount_in_words"] = words
            except Exception:
                pass

    return ctx


def assemble_document(template_id: str, input_data: Dict[str, Any], allow_partial: bool = False) -> Tuple[str, str, VerificationReport]:
    """
    Validates, normalizes, verifies clauses via VerificationPort,
    and renders text. Returns (rendered_text, content_sha256, verification_report).
    If allow_partial=True, missing required fields are populated with clean placeholders for live preview.
    """
    tmpl = get_template(template_id)
    if not tmpl:
        raise AssemblyError(f"Template '{template_id}' not found in registry.")

    # 1. Validate
    if not allow_partial:
        errors = validate_input(tmpl.schema_definition, input_data)
        if errors:
            raise AssemblyError("Validation failed for document fields.", field_errors=errors)

    # 2. Normalize
    effective_inputs = dict(input_data)
    if allow_partial:
        for f in tmpl.schema_definition.get("fields", []):
            f_id = f.get("id")
            if f_id == "target_language":
                continue
            if f_id not in effective_inputs or effective_inputs[f_id] is None or effective_inputs[f_id] == "":
                effective_inputs[f_id] = f"[Pending: {f.get('label', f_id)}]"

    ctx = normalize_context(tmpl, effective_inputs)

    # 3. Jinja2 Render
    jinja_tmpl = Template(tmpl.body_template)
    rendered_text = jinja_tmpl.render(**ctx)

    # 4. Verification Seam Hook (PRD §13)
    clauses = [
        ClauseInput(
            clause_id=f"clause_{i}",
            clause_text=para.strip(),
            statutory_anchor=tmpl.statutory_anchor
        )
        for i, para in enumerate(rendered_text.split("\n\n"))
        if len(para.strip()) > 30
    ]
    report = verification_port.verify_clauses(clauses, anchor=tmpl.statutory_anchor)
    report.template_id = template_id

    # 5. Content Hash (SHA-256)
    content_hash = hashlib.sha256(rendered_text.encode("utf-8")).hexdigest()

    return rendered_text, content_hash, report


def export_docx(rendered_text: str, filename_base: str) -> str:
    """Creates a professional .docx file using python-docx."""
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Set 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    lines = rendered_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph("")
            continue

        if stripped.startswith("----") or stripped.startswith("===="):
            continue

        p = doc.add_paragraph()
        if stripped.isupper() and len(stripped) < 80:
            # Heading-like
            run = p.add_run(stripped)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(13)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            run = p.add_run(line)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    file_path = STORAGE_ROOT / f"{filename_base}.docx"
    doc.save(str(file_path))
    return str(file_path)


def export_pdf(rendered_text: str, content_hash: str, filename_base: str) -> str:
    """
    Creates a non-editable, court-presentable .pdf document using reportlab,
    embedding the SHA-256 tamper-proof hash in the running footer.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas

    file_path = STORAGE_ROOT / f"{filename_base}.pdf"

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_footer(num_pages)
                super().showPage()
            super().save()

        def draw_footer(self, page_count):
            self.saveState()
            self.setFont("Courier", 7)
            self.setFillColor(colors.HexColor("#555555"))
            footer_text = f"HALO Grounded Legal Instrument | SHA-256: {content_hash[:24]}... | Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 36, footer_text)
            self.setStrokeColor(colors.HexColor("#dddddd"))
            self.setLineWidth(0.5)
            self.line(54, 48, 612 - 54, 48)
            self.restoreState()

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        nirmala_path = "C:/Windows/Fonts/Nirmala.ttc"
        if os.path.exists(nirmala_path):
            pdfmetrics.registerFont(TTFont("IndicFont", nirmala_path, subfontIndex=0))
            font_name = "IndicFont"
            font_bold = "IndicFont"
    except Exception:
        pass

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=12,
        leading=16,
        alignment=1,  # Centered
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )

    story = []
    lines = rendered_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
            continue
        if stripped.startswith("----") or stripped.startswith("===="):
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10, spaceBefore=6))
            continue

        safe_text = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if stripped.isupper() and len(stripped) < 90:
            story.append(Paragraph(safe_text, title_style))
        else:
            story.append(Paragraph(safe_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return str(file_path)

