"""
Statutory Deadline Rules Engine (PRD §7.4)
==========================================
Declarative, versioned rules producing explainable, verified statutory deadlines
under the Companies Act 2013, NCLAT Rules, and Negotiable Instruments Act.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from app.drafting.validators import format_legal_date


class OffsetRule(BaseModel):
    days: int
    type: str = "calendar"  # calendar | working


class ExtensionRule(BaseModel):
    additional_fee_window_days: int = 0
    condonable_days: int = 0
    note: str = ""


class DeadlineRule(BaseModel):
    rule_id: str
    title: str
    trigger_event: str
    anchor_date_field: str
    offset: OffsetRule
    statutory_basis: str
    extension: Optional[ExtensionRule] = None
    rule_version: str = "2026.1"
    disclaimer: str = "Computed dates are statutory aids; the advocate is responsible for verification."


class ProposedDeadline(BaseModel):
    rule_id: str
    rule_version: str
    title: str
    anchor_date: str
    due_date: str
    statutory_basis: str
    explanation: str
    extension_info: Optional[str] = None
    event_type: str = "FILING_DEADLINE"
    priority: int = 2  # 1=Supreme Court, 2=High Court/NCLAT, 3=NCLT


# ─── Seed Rules (P0) ──────────────────────────────────────────────────────────

DEADLINE_RULES: Dict[str, DeadlineRule] = {
    "MGT14_FILING_30D": DeadlineRule(
        rule_id="MGT14_FILING_30D",
        title="File e-Form MGT-14 with ROC",
        trigger_event="BOARD_RESOLUTION_PASSED",
        anchor_date_field="resolution_date",
        offset=OffsetRule(days=30, type="calendar"),
        statutory_basis="Section 117(1), Companies Act, 2013",
        extension=ExtensionRule(
            additional_fee_window_days=270,
            note="Late filing attracts additional filing fees under Section 403."
        ),
        rule_version="2026.1",
    ),
    "DIR12_APPT_30D": DeadlineRule(
        rule_id="DIR12_APPT_30D",
        title="File Form DIR-12 for Director Appointment with ROC",
        trigger_event="DIRECTOR_APPOINTED",
        anchor_date_field="appointment_date",
        offset=OffsetRule(days=30, type="calendar"),
        statutory_basis="Section 170(2), Companies Act, 2013 read with Rule 18 of Companies (Appointment and Qualification of Directors) Rules, 2014",
        extension=ExtensionRule(
            additional_fee_window_days=270,
            note="Late filing attracts additional fees and non-compliance penalty."
        ),
        rule_version="2026.1",
    ),
    "AOC4_AGM_30D": DeadlineRule(
        rule_id="AOC4_AGM_30D",
        title="File Financial Statements in Form AOC-4 with ROC",
        trigger_event="AGM_HELD",
        anchor_date_field="agm_date",
        offset=OffsetRule(days=30, type="calendar"),
        statutory_basis="Section 137(1), Companies Act, 2013",
        extension=ExtensionRule(
            additional_fee_window_days=270,
            note="Additional fee of INR 100/day applies for each day of default."
        ),
        rule_version="2026.1",
    ),
    "MGT7_AGM_60D": DeadlineRule(
        rule_id="MGT7_AGM_60D",
        title="File Annual Return in Form MGT-7 with ROC",
        trigger_event="AGM_HELD",
        anchor_date_field="agm_date",
        offset=OffsetRule(days=60, type="calendar"),
        statutory_basis="Section 92(4), Companies Act, 2013",
        extension=ExtensionRule(
            additional_fee_window_days=240,
            note="Additional fee of INR 100/day applies for each day of default."
        ),
        rule_version="2026.1",
    ),
    "NCLAT_APPEAL_45D": DeadlineRule(
        rule_id="NCLAT_APPEAL_45D",
        title="Statutory Limitation for Appeal to NCLAT against NCLT Order",
        trigger_event="NCLT_ORDER_PRONOUNCED",
        anchor_date_field="order_date",
        offset=OffsetRule(days=45, type="calendar"),
        statutory_basis="Section 421(3), Companies Act, 2013",
        extension=ExtensionRule(
            condonable_days=45,
            note="Tribunal may condone delay up to maximum 45 days if satisfied of sufficient cause (Kalpraj Dharamshi v. Kotak Investment Advisors, 2021)."
        ),
        rule_version="2026.1",
    ),
    "NI138_NOTICE_30D": DeadlineRule(
        rule_id="NI138_NOTICE_30D",
        title="Dispatch Statutory Demand Notice under Section 138 NI Act",
        trigger_event="CHEQUE_DISHONOUR_INTIMATION",
        anchor_date_field="dishonour_date",
        offset=OffsetRule(days=30, type="calendar"),
        statutory_basis="Section 138 proviso (b), Negotiable Instruments Act, 1881",
        extension=ExtensionRule(
            note="Notice must demand payment within 15 days of receipt. Criminal complaint must be filed within 1 month thereafter under Section 142(1)(b)."
        ),
        rule_version="2026.1",
    )
}


def compute_statutory_deadline(
    rule_id: str,
    anchor_date_str: str,
    matter_title: Optional[str] = None
) -> ProposedDeadline:
    """
    Computes a statutory deadline deterministically from anchor date,
    generating clear, human-readable legal explanation string.
    """
    rule = DEADLINE_RULES.get(rule_id)
    if not rule:
        raise ValueError(f"Unknown deadline rule: {rule_id}")

    try:
        a_date = datetime.fromisoformat(anchor_date_str.split("T")[0]).date()
    except Exception:
        raise ValueError(f"Invalid anchor date format: {anchor_date_str}")

    due = a_date + timedelta(days=rule.offset.days)

    anchor_formatted = format_legal_date(a_date)
    due_formatted = format_legal_date(due)

    explanation = (
        f"Anchor date on {anchor_formatted} + {rule.offset.days} calendar days = "
        f"{due_formatted}, strictly pursuant to {rule.statutory_basis}."
    )

    ext_note = None
    if rule.extension:
        parts = []
        if rule.extension.additional_fee_window_days > 0:
            parts.append(f"Extended fee window: {rule.extension.additional_fee_window_days} days.")
        if rule.extension.condonable_days > 0:
            parts.append(f"Condonable limitation period: {rule.extension.condonable_days} days.")
        if rule.extension.note:
            parts.append(rule.extension.note)
        ext_note = " ".join(parts)

    return ProposedDeadline(
        rule_id=rule.rule_id,
        rule_version=rule.rule_version,
        title=rule.title,
        anchor_date=a_date.isoformat(),
        due_date=due.isoformat(),
        statutory_basis=rule.statutory_basis,
        explanation=explanation,
        extension_info=ext_note,
        event_type="FILING_DEADLINE",
        priority=2 if "NCLAT" in rule_id else 3
    )


def list_deadline_rules() -> List[Dict[str, Any]]:
    """Returns metadata for all available declarative deadline rules."""
    return [
        {
            "rule_id": r.rule_id,
            "title": r.title,
            "trigger_event": r.trigger_event,
            "offset_days": r.offset.days,
            "statutory_basis": r.statutory_basis,
            "rule_version": r.rule_version,
            "has_extension": r.extension is not None
        }
        for r in DEADLINE_RULES.values()
    ]

