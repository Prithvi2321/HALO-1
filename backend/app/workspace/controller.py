"""
Workspace, Calendar & Practice Management Controller (PRD §11.2)
================================================================
Endpoints for Clients, Matters, Documents, Timeline, Calendar Events,
Statutory Deadlines, and Dashboard Summary Widgets.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Query, status, Response
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.auth.repository import get_session
from app.workspace.model import (
    Client,
    LegalMatter,
    CalendarEvent,
    MatterDocument,
    MatterNote,
    Draft,
    now_utc,
)
from app.workspace.repository import TenantRepository
from app.calendar.deadline_engine import (
    compute_statutory_deadline,
    list_deadline_rules,
    ProposedDeadline,
)

router = APIRouter(tags=["workspace"])


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class ClientCreateRequest(BaseModel):
    client_name: str
    client_type: str = "COMPANY"  # INDIVIDUAL | COMPANY | LLP | OTHER
    cin: Optional[str] = None
    pan: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class MatterCreateRequest(BaseModel):
    matter_name: str
    client_id: Optional[str] = None
    forum_type: str = "NCLT"  # NCLT | NCLAT | HIGH_COURT | SUPREME_COURT | OTHER
    forum_detail: Optional[str] = "Principal Bench"
    case_number: Optional[str] = None
    opposing_parties: Optional[str] = None
    statutory_act: str = "Companies Act, 2013"
    lead_advocate_name: Optional[str] = "Adv. Lead"
    status: str = "ACTIVE"


class EventCreateRequest(BaseModel):
    matter_id: Optional[str] = None
    event_title: str
    event_type: str = "HEARING"  # HEARING | FILING_DEADLINE | CLIENT_MEETING | COMPLIANCE | OTHER
    starts_at: datetime
    ends_at: Optional[datetime] = None
    all_day: bool = False
    priority: int = 3
    notes: Optional[str] = None
    rule_id: Optional[str] = None
    rule_version: Optional[str] = None
    computation_explanation: Optional[str] = None


class DeadlineComputeRequest(BaseModel):
    rule_id: str
    anchor_date: str
    matter_id: Optional[str] = None


class NoteCreateRequest(BaseModel):
    content: str
    author_name: Optional[str] = "Advocate"


# ─── Client Endpoints ─────────────────────────────────────────────────────────

@router.get("/clients", response_model=List[Client])
def api_list_clients(
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    return repo.list_clients()


@router.post("/clients", status_code=status.HTTP_201_CREATED, response_model=Client)
def api_create_client(
    req: ClientCreateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    client = Client(
        firm_id=firm_id,
        client_name=req.client_name,
        client_type=req.client_type,
        cin=req.cin,
        pan=req.pan,
        email=req.email,
        phone=req.phone,
    )
    return repo.create_client(client)


# ─── Matter Endpoints ─────────────────────────────────────────────────────────

@router.get("/matters", response_model=List[LegalMatter])
def api_list_matters(
    status: Optional[str] = Query(None),
    forum_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    return repo.list_matters(status=status, forum_type=forum_type, search=search)


@router.post("/matters", status_code=status.HTTP_201_CREATED, response_model=LegalMatter)
def api_create_matter(
    req: MatterCreateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    matter = LegalMatter(
        firm_id=firm_id,
        client_id=req.client_id,
        matter_name=req.matter_name,
        forum_type=req.forum_type,
        forum_detail=req.forum_detail,
        case_number=req.case_number,
        opposing_parties=req.opposing_parties,
        statutory_act=req.statutory_act,
        lead_advocate_name=req.lead_advocate_name,
        status=req.status,
    )
    return repo.create_matter(matter)


@router.get("/matters/{matter_id}")
def api_get_matter(
    matter_id: str,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    matter = repo.get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found.")

    client = repo.get_client(matter.client_id) if matter.client_id else None
    documents = repo.list_matter_documents(matter_id)
    notes = repo.list_matter_notes(matter_id)
    drafts = repo.list_drafts(matter_id=matter_id)
    events = repo.list_events(matter_id=matter_id)

    return {
        "matter": matter,
        "client": client,
        "documents": documents,
        "notes": notes,
        "drafts": drafts,
        "events": events
    }


@router.get("/matters/{matter_id}/timeline")
def api_get_matter_timeline(
    matter_id: str,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Returns a unified chronologically ordered timeline feed of hearings, drafts, notes, filings."""
    repo = TenantRepository(session, firm_id=firm_id)
    matter = repo.get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found.")

    events = repo.list_events(matter_id=matter_id)
    notes = repo.list_matter_notes(matter_id)
    drafts = repo.list_drafts(matter_id=matter_id)

    feed = []
    for e in events:
        feed.append({
            "type": "EVENT",
            "subtype": e.event_type,
            "title": e.event_title,
            "timestamp": e.starts_at.isoformat(),
            "details": e.computation_explanation or e.notes or f"Priority {e.priority}",
            "status": e.status
        })

    for n in notes:
        feed.append({
            "type": "NOTE",
            "subtype": "MEMO",
            "title": f"Note by {n.author_name}",
            "timestamp": n.created_at.isoformat(),
            "details": n.content,
            "status": "RECORDED"
        })

    for d in drafts:
        feed.append({
            "type": "DRAFT",
            "subtype": d.template_id,
            "title": f"Pleading Draft: {d.title}",
            "timestamp": d.created_at.isoformat(),
            "details": f"Status: {d.status}",
            "status": d.status
        })

    feed.sort(key=lambda x: x["timestamp"], reverse=True)
    return feed


@router.post("/matters/{matter_id}/notes", status_code=status.HTTP_201_CREATED)
def api_add_matter_note(
    matter_id: str,
    req: NoteCreateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    note = MatterNote(
        firm_id=firm_id,
        matter_id=matter_id,
        author_name=req.author_name or "Advocate",
        content=req.content,
    )
    return repo.add_matter_note(note)


# ─── Calendar & Deadline Endpoints ───────────────────────────────────────────

@router.get("/deadlines/rules")
def api_list_rules():
    """Returns catalog of declarative deadline rules."""
    return list_deadline_rules()


@router.post("/deadlines/compute", response_model=ProposedDeadline)
def api_compute_deadline(
    req: DeadlineComputeRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Computes statutory deadline deterministically from anchor date with explanation."""
    repo = TenantRepository(session, firm_id=firm_id)
    matter_title = None
    if req.matter_id:
        m = repo.get_matter(req.matter_id)
        if m:
            matter_title = m.matter_name

    try:
        proposed = compute_statutory_deadline(
            rule_id=req.rule_id,
            anchor_date_str=req.anchor_date,
            matter_title=matter_title
        )
        return proposed
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/events")
def api_list_events(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    matter_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Range query for calendar events with optional type/matter filtering."""
    repo = TenantRepository(session, firm_id=firm_id)
    try:
        from_dt = datetime.fromisoformat(from_date) if from_date else None
    except Exception:
        from_dt = None
    try:
        to_dt = datetime.fromisoformat(to_date) if to_date else None
    except Exception:
        to_dt = None
    return repo.list_events(from_date=from_dt, to_date=to_dt, matter_id=matter_id, event_type=event_type)


@router.post("/events", status_code=status.HTTP_201_CREATED, response_model=CalendarEvent)
def api_create_event(
    req: EventCreateRequest,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    repo = TenantRepository(session, firm_id=firm_id)
    ev = CalendarEvent(
        firm_id=firm_id,
        matter_id=req.matter_id,
        event_title=req.event_title,
        event_type=req.event_type,
        starts_at=req.starts_at,
        ends_at=req.ends_at,
        all_day=req.all_day,
        status="CONFIRMED",
        priority=req.priority,
        notes=req.notes,
        rule_id=req.rule_id,
        rule_version=req.rule_version,
        computation_explanation=req.computation_explanation
    )
    return repo.create_event(ev)


@router.post("/events/{event_id}/confirm")
def api_confirm_event(
    event_id: str,
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Confirms a proposed statutory deadline into an active calendar event."""
    repo = TenantRepository(session, firm_id=firm_id)
    ev = repo.confirm_event(event_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return ev


# ─── Dashboard Summary Widgets (PRD §7.2) ────────────────────────────────────

@router.get("/dashboard/summary")
def api_dashboard_summary(
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Aggregates widget data: Today's agenda, Upcoming 7-day hearings, Overdue deadlines, Forum breakdowns, Drafts."""
    repo = TenantRepository(session, firm_id=firm_id)
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)
    seven_days_later = today_start + timedelta(days=7)

    all_matters = repo.list_matters()
    all_events = repo.list_events()
    all_drafts = repo.list_drafts()

    today_agenda = [
        e for e in all_events
        if today_start <= e.starts_at < today_end and e.status != "CANCELLED"
    ]

    upcoming_hearings = [
        e for e in all_events
        if today_start <= e.starts_at <= seven_days_later and e.event_type == "HEARING" and e.status != "CANCELLED"
    ]
    upcoming_hearings.sort(key=lambda x: (x.priority, x.starts_at))

    overdue_deadlines = [
        e for e in all_events
        if e.starts_at < now and e.event_type == "FILING_DEADLINE" and e.status in ["PROPOSED", "CONFIRMED"]
    ]

    forum_breakdown: Dict[str, int] = {}
    for m in all_matters:
        forum_breakdown[m.forum_type] = forum_breakdown.get(m.forum_type, 0) + 1

    drafts_in_progress = [d for d in all_drafts if d.status in ["DRAFT", "GENERATING"]]

    return {
        "metrics": {
            "active_matters_count": len([m for m in all_matters if m.status == "ACTIVE"]),
            "today_events_count": len(today_agenda),
            "upcoming_hearings_count": len(upcoming_hearings),
            "overdue_deadlines_count": len(overdue_deadlines),
            "drafts_in_progress_count": len(drafts_in_progress),
        },
        "today_agenda": today_agenda,
        "upcoming_hearings": upcoming_hearings[:5],
        "overdue_deadlines": overdue_deadlines[:5],
        "forum_breakdown": forum_breakdown,
        "drafts_in_progress": drafts_in_progress[:5],
        "server_time_utc": now.isoformat(),
    }


# ─── iCal Subscription Feed (PRD §7.2 & §11.2) ───────────────────────────────

@router.get("/calendar.ics")
def api_calendar_ics(
    token: Optional[str] = Query(None),
    firm_id: str = "firm_default",
    session: Session = Depends(get_session)
):
    """Exports calendar events in iCalendar (.ics) format."""
    from icalendar import Calendar, Event as ICalEvent

    repo = TenantRepository(session, firm_id=firm_id)
    events = repo.list_events()

    cal = Calendar()
    cal.add("prodid", "-//HALO Nyaya Sahayak Legal Practice Management//IN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "HALO Legal Practice Calendar")

    for ev in events:
        ie = ICalEvent()
        ie.add("summary", f"[{ev.event_type}] {ev.event_title}")
        ie.add("dtstart", ev.starts_at)
        ie.add("dtend", ev.ends_at or (ev.starts_at + timedelta(hours=1)))
        ie.add("description", ev.computation_explanation or ev.notes or ev.event_title)
        ie.add("uid", f"{ev.id}@halo.legal")
        cal.add_component(ie)

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=halo_calendar.ics"}
    )

