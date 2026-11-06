"""
Workspace Seed Data Generator
=============================
Populates rich initial Clients, Matters, Calendar Events, Notes,
and Drafts for immediate interactive evaluation.
"""

from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select

from app.workspace.model import (
    Client,
    LegalMatter,
    CalendarEvent,
    MatterNote,
    Draft,
    DraftVersion,
    now_utc,
)


def seed_workspace_data(session: Session) -> None:
    """Seeds initial demonstration workspace data if database is empty."""
    existing_matter = session.exec(select(LegalMatter)).first()
    if existing_matter:
        return

    now = now_utc()
    today_0 = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

    # 1. Clients
    client1 = Client(
        id="cli_001",
        firm_id="firm_default",
        client_name="Nominee Directors Consortium",
        client_type="LLP",
        pan="AABFN1234F",
        email="legal@consortium.in",
        phone="+91 98200 11223"
    )
    client2 = Client(
        id="cli_002",
        firm_id="firm_default",
        client_name="Vikramaditya Infrastructure Pvt. Ltd.",
        client_type="COMPANY",
        cin="U45200MH2015PTC265431",
        pan="AACCV5432G",
        email="compliance@vikramaditya.in",
        phone="+91 98110 99887"
    )
    client3 = Client(
        id="cli_003",
        firm_id="firm_default",
        client_name="Apex Industrial Supplies LLP",
        client_type="LLP",
        pan="AAZFA9912K",
        email="accounts@apexsupplies.com",
        phone="+91 98765 43210"
    )
    session.add_all([client1, client2, client3])
    session.commit()

    # 2. Matters
    matter1 = LegalMatter(
        id="mat_001",
        firm_id="firm_default",
        client_id=client1.id,
        matter_name="Steel Authority of India Ltd. v. ITO & Ors.",
        forum_type="HIGH_COURT",
        forum_detail="High Court of Delhi (Tax Division)",
        case_number="ITA No. 447/2022",
        opposing_parties="Income Tax Officer, Ward 4(1), New Delhi",
        statutory_act="Income Tax Act, 1961 (Section 179)",
        lead_advocate_name="Adv. Supriya Mulik",
        status="ACTIVE"
    )
    matter2 = LegalMatter(
        id="mat_002",
        firm_id="firm_default",
        client_id=client2.id,
        matter_name="Vikramaditya Infra v. Bharat Commercial Transshipment Ltd.",
        forum_type="NCLT",
        forum_detail="NCLT Mumbai Bench (Court 3)",
        case_number="CP (IB) No. 102/MB/2024",
        opposing_parties="Bharat Commercial Transshipment Ltd. & Ors.",
        statutory_act="Companies Act, 2013 (Section 241/242)",
        lead_advocate_name="Adv. Prithviraj Patil",
        status="ACTIVE"
    )
    matter3 = LegalMatter(
        id="mat_003",
        firm_id="firm_default",
        client_id=client3.id,
        matter_name="Apex Supplies LLP v. Sunil Mehta (Cheque Dishonour)",
        forum_type="OTHER",
        forum_detail="Metropolitan Magistrate Court, Saket, New Delhi",
        case_number="CC No. 891/2024",
        opposing_parties="Sunil V. Mehta, Director of Shanti Logistics",
        statutory_act="Negotiable Instruments Act, 1881 (Section 138)",
        lead_advocate_name="Adv. Supriya Mulik",
        status="ACTIVE"
    )
    session.add_all([matter1, matter2, matter3])
    session.commit()

    # 3. Calendar Events & Statutory Deadlines
    events = [
        CalendarEvent(
            firm_id="firm_default",
            matter_id=matter1.id,
            event_title="Final Arguments — Sec 179 Due Diligence Defence",
            event_type="HEARING",
            starts_at=today_0 + timedelta(hours=10, minutes=30),
            ends_at=today_0 + timedelta(hours=12, minutes=0),
            status="CONFIRMED",
            priority=2,
            notes="Constitution Bench precedent in Siemens Ltd. to be cited."
        ),
        CalendarEvent(
            firm_id="firm_default",
            matter_id=matter2.id,
            event_title="First Listing on Interim Injunction / Board Restraint",
            event_type="HEARING",
            starts_at=today_0 + timedelta(days=2, hours=11, minutes=0),
            ends_at=today_0 + timedelta(days=2, hours=13, minutes=0),
            status="CONFIRMED",
            priority=3,
            notes="Notice to be served on respondents."
        ),
        CalendarEvent(
            firm_id="firm_default",
            matter_id=matter2.id,
            event_title="Statutory Deadline: File e-Form MGT-14 with ROC",
            event_type="FILING_DEADLINE",
            starts_at=today_0 + timedelta(days=4, hours=17, minutes=0),
            status="PROPOSED",
            priority=3,
            rule_id="MGT14_FILING_30D",
            rule_version="2026.1",
            computation_explanation="Board resolution passed on 20 Oct 2026 + 30 calendar days pursuant to Section 117(1) Companies Act, 2013."
        ),
        CalendarEvent(
            firm_id="firm_default",
            matter_id=matter3.id,
            event_title="Statutory 15-Day Demand Notice Expiry",
            event_type="FILING_DEADLINE",
            starts_at=today_0 + timedelta(days=6, hours=18, minutes=0),
            status="CONFIRMED",
            priority=4,
            rule_id="NI138_NOTICE_30D",
            computation_explanation="15-day statutory cure period expires; filing of Section 142 complaint accrues on following day."
        )
    ]
    session.add_all(events)

    # 4. Notes
    note1 = MatterNote(
        firm_id="firm_default",
        matter_id=matter1.id,
        author_name="Adv. Supriya Mulik",
        content="Affidavit of nominee director filed in registry. Requisitioned audited board minutes showing recorded dissents to corroborate due diligence."
    )
    note2 = MatterNote(
        firm_id="firm_default",
        matter_id=matter2.id,
        author_name="Adv. Prithviraj Patil",
        content="Petitioner shareholding audit verified: holds 18.5% equity, satisfying Section 244 threshold. Urgent listing requisitioned before Court 3."
    )
    session.add_all([note1, note2])

    session.commit()

