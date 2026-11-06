import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.main import app
from app.auth.repository import get_session
from app.calendar.deadline_engine import compute_statutory_deadline

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client", autouse=True)
def client_fixture():
    SQLModel.metadata.create_all(test_engine)
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)


def test_statutory_deadline_rules_engine():
    # 1. MGT-14 rule: 30 days
    mgt14 = compute_statutory_deadline("MGT14_FILING_30D", "2026-11-01")
    assert mgt14.rule_id == "MGT14_FILING_30D"
    assert mgt14.due_date == "2026-12-01"
    assert "Section 117(1), Companies Act, 2013" in mgt14.explanation

    # 2. NCLAT Appeal rule: 45 days + condonable
    nclat = compute_statutory_deadline("NCLAT_APPEAL_45D", "2026-10-01")
    assert nclat.rule_id == "NCLAT_APPEAL_45D"
    assert nclat.due_date == "2026-11-15"
    assert "Section 421(3)" in nclat.statutory_basis
    assert "Condonable limitation period: 45 days" in (nclat.extension_info or "")

    # 3. NI Act 138 Notice rule: 30 days
    ni = compute_statutory_deadline("NI138_NOTICE_30D", "2026-11-05")
    assert ni.due_date == "2026-12-05"


def test_clients_and_matters_crud(client: TestClient):
    # Create client
    c_res = client.post("/api/v1/clients", json={
        "client_name": "Tata Motors Ltd.",
        "client_type": "COMPANY",
        "cin": "L28920MH1945PLC004520"
    })
    assert c_res.status_code == 201
    client_id = c_res.json()["id"]

    # Create matter
    m_res = client.post("/api/v1/matters", json={
        "client_id": client_id,
        "matter_name": "Tata Motors v. State Tax Authority",
        "forum_type": "HIGH_COURT",
        "forum_detail": "Bombay High Court",
        "case_number": "WP No. 1290/2026",
        "statutory_act": "Central Goods and Services Tax Act, 2017"
    })
    assert m_res.status_code == 201
    matter_id = m_res.json()["id"]

    # Add Note
    n_res = client.post(f"/api/v1/matters/{matter_id}/notes", json={
        "content": "Ad interim stay granted on recovery notice.",
        "author_name": "Adv. S. Mulik"
    })
    assert n_res.status_code == 201

    # Check timeline
    t_res = client.get(f"/api/v1/matters/{matter_id}/timeline")
    assert t_res.status_code == 200
    timeline = t_res.json()
    assert len(timeline) >= 1
    assert timeline[0]["type"] == "NOTE"


def test_multitenancy_isolation(client: TestClient):
    """PRD §9.2: User/firm A cannot read/modify firm B data."""
    # Firm A creates matter
    m_a = client.post("/api/v1/matters", json={
        "matter_name": "Firm A Confidential Matter",
        "forum_type": "NCLT"
    }, params={"firm_id": "firm_A"})
    assert m_a.status_code == 201
    matter_a_id = m_a.json()["id"]

    # Firm B creates matter
    m_b = client.post("/api/v1/matters", json={
        "matter_name": "Firm B Private Matter",
        "forum_type": "SUPREME_COURT"
    }, params={"firm_id": "firm_B"})
    assert m_b.status_code == 201

    # Firm B cannot see Firm A matters in list
    list_b = client.get("/api/v1/matters", params={"firm_id": "firm_B"}).json()
    matter_names_b = [m["matter_name"] for m in list_b]
    assert "Firm B Private Matter" in matter_names_b
    assert "Firm A Confidential Matter" not in matter_names_b

    # Firm B cannot access Firm A matter directly
    get_a_as_b = client.get(f"/api/v1/matters/{matter_a_id}", params={"firm_id": "firm_B"})
    assert get_a_as_b.status_code == 404


def test_calendar_and_dashboard_summary(client: TestClient):
    now = datetime.now(timezone.utc)
    # Create calendar event
    ev_res = client.post("/api/v1/events", json={
        "event_title": "Interlocutory Arguments before Bench 1",
        "event_type": "HEARING",
        "starts_at": (now + timedelta(hours=2)).isoformat(),
        "priority": 2
    })
    assert ev_res.status_code == 201

    # Get dashboard summary
    dash_res = client.get("/api/v1/dashboard/summary")
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert "metrics" in data
    assert "today_agenda" in data
    assert "upcoming_hearings" in data
    assert data["metrics"]["today_events_count"] >= 1

