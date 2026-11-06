"""
Tenant-Scoped Workspace Repository (PRD §9.2)
==============================================
All matter, client, calendar, and draft queries are strictly filtered by firm_id.
"""

from typing import List, Optional, TypeVar, Generic, Type, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, func
from app.workspace.model import (
    Client,
    LegalMatter,
    CalendarEvent,
    Reminder,
    MatterDocument,
    MatterNote,
    Draft,
    DraftVersion,
    Export,
    TelegramLink,
    TelegramPairingCode,
    generate_uuid,
    now_utc,
)

T = TypeVar("T")


class TenantRepository:
    """Base repository with mandatory tenant isolation by firm_id."""

    def __init__(self, session: Session, firm_id: str = "firm_default"):
        self.session = session
        self.firm_id = firm_id

    # ─── Clients ──────────────────────────────────────────────────────────────

    def list_clients(self) -> List[Client]:
        statement = select(Client).where(
            Client.firm_id == self.firm_id,
            Client.deleted_at == None  # noqa: E711
        ).order_by(Client.client_name)
        return list(self.session.exec(statement).all())

    def get_client(self, client_id: str) -> Optional[Client]:
        statement = select(Client).where(
            Client.id == client_id,
            Client.firm_id == self.firm_id,
            Client.deleted_at == None  # noqa: E711
        )
        return self.session.exec(statement).first()

    def create_client(self, client: Client) -> Client:
        client.firm_id = self.firm_id
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client

    # ─── Matters ──────────────────────────────────────────────────────────────

    def list_matters(
        self,
        status: Optional[str] = None,
        forum_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[LegalMatter]:
        statement = select(LegalMatter).where(
            LegalMatter.firm_id == self.firm_id,
            LegalMatter.deleted_at == None  # noqa: E711
        )
        if status and status != "ALL":
            statement = statement.where(LegalMatter.status == status)
        if forum_type and forum_type != "ALL":
            statement = statement.where(LegalMatter.forum_type == forum_type)
        if search:
            search_pat = f"%{search.lower()}%"
            statement = statement.where(func.lower(LegalMatter.matter_name).like(search_pat))
        statement = statement.order_by(LegalMatter.updated_at.desc())
        return list(self.session.exec(statement).all())

    def get_matter(self, matter_id: str) -> Optional[LegalMatter]:
        statement = select(LegalMatter).where(
            LegalMatter.id == matter_id,
            LegalMatter.firm_id == self.firm_id,
            LegalMatter.deleted_at == None  # noqa: E711
        )
        return self.session.exec(statement).first()

    def create_matter(self, matter: LegalMatter) -> LegalMatter:
        matter.firm_id = self.firm_id
        self.session.add(matter)
        self.session.commit()
        self.session.refresh(matter)
        return matter

    def update_matter(self, matter: LegalMatter) -> LegalMatter:
        matter.updated_at = now_utc()
        self.session.add(matter)
        self.session.commit()
        self.session.refresh(matter)
        return matter

    # ─── Calendar & Events ───────────────────────────────────────────────────

    def list_events(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        matter_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[CalendarEvent]:
        statement = select(CalendarEvent).where(CalendarEvent.firm_id == self.firm_id)
        if from_date:
            statement = statement.where(CalendarEvent.starts_at >= from_date)
        if to_date:
            statement = statement.where(CalendarEvent.starts_at <= to_date)
        if matter_id:
            statement = statement.where(CalendarEvent.matter_id == matter_id)
        if event_type:
            statement = statement.where(CalendarEvent.event_type == event_type)
        statement = statement.order_by(CalendarEvent.starts_at.asc())
        return list(self.session.exec(statement).all())

    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        statement = select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.firm_id == self.firm_id
        )
        return self.session.exec(statement).first()

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        event.firm_id = self.firm_id
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def confirm_event(self, event_id: str) -> Optional[CalendarEvent]:
        event = self.get_event(event_id)
        if event:
            event.status = "CONFIRMED"
            self.session.add(event)
            self.session.commit()
            self.session.refresh(event)
        return event

    # ─── Documents & Notes ───────────────────────────────────────────────────

    def list_matter_documents(self, matter_id: str) -> List[MatterDocument]:
        statement = select(MatterDocument).where(
            MatterDocument.firm_id == self.firm_id,
            MatterDocument.matter_id == matter_id
        ).order_by(MatterDocument.created_at.desc())
        return list(self.session.exec(statement).all())

    def add_matter_document(self, doc: MatterDocument) -> MatterDocument:
        doc.firm_id = self.firm_id
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return doc

    def list_matter_notes(self, matter_id: str) -> List[MatterNote]:
        statement = select(MatterNote).where(
            MatterNote.firm_id == self.firm_id,
            MatterNote.matter_id == matter_id
        ).order_by(MatterNote.created_at.desc())
        return list(self.session.exec(statement).all())

    def add_matter_note(self, note: MatterNote) -> MatterNote:
        note.firm_id = self.firm_id
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    # ─── Drafts & Versions ───────────────────────────────────────────────────

    def list_drafts(self, matter_id: Optional[str] = None) -> List[Draft]:
        statement = select(Draft).where(Draft.firm_id == self.firm_id)
        if matter_id:
            statement = statement.where(Draft.matter_id == matter_id)
        statement = statement.order_by(Draft.updated_at.desc())
        return list(self.session.exec(statement).all())

    def get_draft(self, draft_id: str) -> Optional[Draft]:
        statement = select(Draft).where(
            Draft.id == draft_id,
            Draft.firm_id == self.firm_id
        )
        return self.session.exec(statement).first()

    def create_draft(self, draft: Draft) -> Draft:
        draft.firm_id = self.firm_id
        self.session.add(draft)
        self.session.commit()
        self.session.refresh(draft)
        return draft

    def update_draft(self, draft: Draft) -> Draft:
        draft.updated_at = now_utc()
        self.session.add(draft)
        self.session.commit()
        self.session.refresh(draft)
        return draft

    def add_draft_version(self, draft_version: DraftVersion) -> DraftVersion:
        self.session.add(draft_version)
        self.session.commit()
        self.session.refresh(draft_version)
        return draft_version

    def get_draft_versions(self, draft_id: str) -> List[DraftVersion]:
        statement = select(DraftVersion).where(
            DraftVersion.draft_id == draft_id
        ).order_by(DraftVersion.version_no.desc())
        return list(self.session.exec(statement).all())

