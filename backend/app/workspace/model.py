"""
Workspace Data Models (PRD §10)
================================
Supports Clients, Matters, Documents, Notes, Calendar Events,
Statutory Deadlines, Reminders, Drafts, and Telegram Links.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlmodel import Field, SQLModel


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Firm(SQLModel, table=True):
    __tablename__ = "firms"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    client_name: str = Field(nullable=False)
    client_type: str = Field(default="COMPANY", nullable=False)  # INDIVIDUAL | COMPANY | LLP | OTHER
    cin: Optional[str] = Field(default=None)
    pan: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)


class LegalMatter(SQLModel, table=True):
    __tablename__ = "legal_matters"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    client_id: Optional[str] = Field(default=None, index=True)
    matter_name: str = Field(nullable=False)
    forum_type: str = Field(default="NCLT", nullable=False)  # NCLT | NCLAT | HIGH_COURT | SUPREME_COURT | OTHER
    forum_detail: Optional[str] = Field(default="Principal Bench")  # e.g. "Mumbai Bench", "Delhi High Court"
    case_number: Optional[str] = Field(default=None)
    opposing_parties: Optional[str] = Field(default=None)
    statutory_act: str = Field(default="Companies Act, 2013")
    lead_advocate_id: Optional[int] = Field(default=None)
    lead_advocate_name: Optional[str] = Field(default="Adv. Lead")
    status: str = Field(default="ACTIVE", nullable=False)  # INTAKE | ACTIVE | STAYED | RESERVED_FOR_ORDERS | DISPOSED | ARCHIVED
    created_by: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)
    updated_at: datetime = Field(default_factory=now_utc, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)


class CalendarEvent(SQLModel, table=True):
    __tablename__ = "calendar_events"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    matter_id: Optional[str] = Field(default=None, index=True)
    event_title: str = Field(nullable=False)
    event_type: str = Field(default="HEARING", nullable=False)  # HEARING | FILING_DEADLINE | CLIENT_MEETING | COMPLIANCE | OTHER
    starts_at: datetime = Field(nullable=False)
    ends_at: Optional[datetime] = Field(default=None)
    all_day: bool = Field(default=False)
    status: str = Field(default="CONFIRMED", nullable=False)  # PROPOSED | CONFIRMED | DONE | CANCELLED
    priority: int = Field(default=3)  # 1=Supreme Court, 2=High Court/NCLAT, 3=NCLT, 4=Lower, 5=Routine
    rule_id: Optional[str] = Field(default=None)
    rule_version: Optional[str] = Field(default=None)
    computation_explanation: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_by: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)


class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    event_id: str = Field(nullable=False, index=True)
    user_id: Optional[int] = Field(default=None, index=True)
    offset_minutes: int = Field(default=1440)  # e.g. 1440 = 24h, 120 = 2h
    channel: str = Field(default="TELEGRAM")  # TELEGRAM | EMAIL | IN_APP
    fire_at: datetime = Field(nullable=False, index=True)
    sent_at: Optional[datetime] = Field(default=None)


class MatterDocument(SQLModel, table=True):
    __tablename__ = "matter_documents"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    matter_id: str = Field(nullable=False, index=True)
    title: str = Field(nullable=False)
    file_key: str = Field(nullable=False)
    file_type: str = Field(default="pdf")
    file_size: int = Field(default=0)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)


class MatterNote(SQLModel, table=True):
    __tablename__ = "matter_notes"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    matter_id: str = Field(nullable=False, index=True)
    author_id: Optional[int] = Field(default=None)
    author_name: str = Field(default="Advocate")
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)
    updated_at: datetime = Field(default_factory=now_utc, nullable=False)


class Draft(SQLModel, table=True):
    __tablename__ = "drafts"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    firm_id: str = Field(default="firm_default", index=True, nullable=False)
    matter_id: Optional[str] = Field(default=None, index=True)
    template_id: str = Field(nullable=False)
    title: str = Field(nullable=False)
    status: str = Field(default="DRAFT", nullable=False)  # DRAFT | GENERATING | READY | FINALISED
    created_by: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)
    updated_at: datetime = Field(default_factory=now_utc, nullable=False)


class DraftVersion(SQLModel, table=True):
    __tablename__ = "draft_versions"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    draft_id: str = Field(nullable=False, index=True)
    version_no: int = Field(default=1, nullable=False)
    input_json: str = Field(default="{}", nullable=False)
    content_sha256: Optional[str] = Field(default=None)
    verification_report: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)


class Export(SQLModel, table=True):
    __tablename__ = "exports"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    draft_version_id: str = Field(nullable=False, index=True)
    format: str = Field(nullable=False)  # docx | pdf
    storage_key: Optional[str] = Field(default=None)
    status: str = Field(default="READY")  # QUEUED | READY | FAILED
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)


class TelegramLink(SQLModel, table=True):
    __tablename__ = "telegram_links"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    user_id: int = Field(unique=True, index=True, nullable=False)
    telegram_user_id: int = Field(unique=True, index=True, nullable=False)
    telegram_username: Optional[str] = Field(default=None)
    paired_at: datetime = Field(default_factory=now_utc, nullable=False)
    revoked_at: Optional[datetime] = Field(default=None)


class TelegramPairingCode(SQLModel, table=True):
    __tablename__ = "telegram_pairing_codes"

    code_hash: str = Field(primary_key=True)  # SHA-256 of 6-digit OTP
    user_id: int = Field(nullable=False, index=True)
    expires_at: datetime = Field(nullable=False)
    used_at: Optional[datetime] = Field(default=None)

