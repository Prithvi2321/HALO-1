import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.main import app
from app.auth.repository import get_session

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


def test_telegram_pairing_and_commands(client: TestClient):
    # 1. Unpaired bot interaction: /start works
    res_start = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766, "username": "adv_patil"},
            "chat": {"id": 99887766},
            "text": "/start"
        }
    })
    assert res_start.status_code == 200
    assert "Welcome to HALO" in res_start.json()["reply_text"]

    # 2. Unpaired interaction on protected command: rejected
    res_agenda_unpaired = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766},
            "chat": {"id": 99887766},
            "text": "/agenda today"
        }
    })
    assert "You are not paired" in res_agenda_unpaired.json()["reply_text"]

    # 3. Generate pairing OTP from web app
    otp_res = client.post("/api/v1/telegram/pairing-codes", params={"user_id": 1})
    assert otp_res.status_code == 200
    otp = otp_res.json()["otp"]
    assert len(otp) == 6

    # 4. Pair via Telegram bot: /auth <otp>
    res_auth = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766, "username": "adv_patil"},
            "chat": {"id": 99887766},
            "text": f"/auth {otp}"
        }
    })
    assert "Successfully paired with HALO" in res_auth.json()["reply_text"]

    # 5. Check pairing status
    status_res = client.get("/api/v1/telegram/status", params={"user_id": 1})
    assert status_res.status_code == 200
    assert status_res.json()["is_paired"] is True

    # 6. Query /agenda today (now paired)
    res_agenda = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766},
            "chat": {"id": 99887766},
            "text": "/agenda today"
        }
    })
    assert res_agenda.status_code == 200
    assert "Today" in res_agenda.json()["reply_text"]

    # 7. Query /ask legal query (PRD §13 Seam: returns coming soon message)
    res_ask = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766},
            "chat": {"id": 99887766},
            "text": "/ask What is Section 161(1) of Companies Act?"
        }
    })
    assert "Legal research via Telegram is coming soon" in res_ask.json()["reply_text"]

    # 8. Unpair
    res_logout = client.post("/api/v1/telegram/webhook", json={
        "message": {
            "from": {"id": 99887766},
            "chat": {"id": 99887766},
            "text": "/logout"
        }
    })
    assert "Successfully unpaired" in res_logout.json()["reply_text"]

