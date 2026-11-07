import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.main import app
from app.auth.repository import get_session
from app.drafting.validators import (
    validate_cin,
    validate_din,
    validate_pan,
    validate_gstin,
    validate_date_not_future,
    number_to_indian_words,
    format_indian_currency,
)
from app.drafting.assembly import assemble_document, export_docx, export_pdf

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    with Session(test_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(name="client", autouse=True)
def client_fixture():
    SQLModel.metadata.create_all(test_engine)
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)


# ─── Unit Tests: Indian Legal Validators ──────────────────────────────────────

def test_indian_legal_validators():
    # Valid & Invalid CIN
    ok, _ = validate_cin("U72200MH2013PTC248912")
    assert ok is True
    ok, err = validate_cin("INVALID_CIN")
    assert ok is False
    assert "Invalid CIN format" in err

    # Valid & Invalid DIN
    ok, _ = validate_din("08945612")
    assert ok is True
    ok, err = validate_din("1234")
    assert ok is False
    assert "Expected exactly 8 numeric digits" in err

    # Valid & Invalid PAN
    ok, _ = validate_pan("ABCDE1234F")
    assert ok is True
    ok, _ = validate_pan("12345ABCDE")
    assert ok is False

    # Valid & Invalid GSTIN
    ok, _ = validate_gstin("27ABCDE1234F1Z5")
    assert ok is True
    ok, _ = validate_gstin("1234567")
    assert ok is False

    # Past vs Future dates
    ok, _ = validate_date_not_future("2024-01-01")
    assert ok is True
    ok, _ = validate_date_not_future("2099-01-01")
    assert ok is False

    # Indian Currency & Words
    assert format_indian_currency(1250000) == "₹ 12,50,000"
    words = number_to_indian_words(1250000)
    assert words == "Rupees Twelve Lakh Fifty Thousand Only"


# ─── API Tests: Template Registry & Generation ───────────────────────────────

def test_template_registry_endpoints(client: TestClient):
    # List templates
    res = client.get("/api/v1/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 5

    # Check specific template manifest
    res2 = client.get("/api/v1/templates/BOARD_RES_DIR_APPT_V1")
    assert res2.status_code == 200
    data = res2.json()
    assert data["template_id"] == "BOARD_RES_DIR_APPT_V1"
    assert "schema_definition" in data
    assert len(data["schema_definition"]["fields"]) >= 8


def test_board_resolution_assembly_and_export(client: TestClient):
    payload = {
        "company_cin": "U72200MH2013PTC248912",
        "company_name": "Apex Innovations Private Limited",
        "registered_office": "401, Nariman Point, Mumbai - 400021",
        "meeting_date": "2024-10-15",
        "meeting_venue": "Registered Office, Mumbai",
        "director_name": "Ananya Sen",
        "director_din": "09876543",
        "effective_date": "2024-10-16",
        "articles_authorise": True,
        "co_signatory": "Rajesh Malhotra (Managing Director, DIN: 01234567)"
    }

    # Direct assembly
    text, sha, report = assemble_document("BOARD_RES_DIR_APPT_V1", payload)
    assert "APEX INNOVATIONS PRIVATE LIMITED" in text
    assert "ANANYA SEN" in text
    assert len(sha) == 64
    assert report.overall_status == "NOT_VERIFIED"

    # Export docx & pdf
    docx_file = export_docx(text, "test_br_export")
    assert docx_file.endswith(".docx")

    pdf_file = export_pdf(text, sha, "test_br_export")
    assert pdf_file.endswith(".pdf")


def test_draft_lifecycle_endpoints(client: TestClient):
    # 1. Create draft
    create_res = client.post("/api/v1/drafts", json={
        "template_id": "BOARD_RES_DIR_APPT_V1",
        "title": "Board Resolution - Ananya Sen Appointment",
        "inputs": {"company_name": "Apex Innovations"}
    })
    assert create_res.status_code == 201
    draft_id = create_res.json()["draft"]["id"]

    # 2. Autosave inputs
    save_res = client.put(f"/api/v1/drafts/{draft_id}/inputs", json={
        "inputs": {
            "company_cin": "U72200MH2013PTC248912",
            "company_name": "Apex Innovations Private Limited",
            "registered_office": "401, Nariman Point, Mumbai - 400021",
            "meeting_date": "2024-10-15",
            "meeting_venue": "Registered Office, Mumbai",
            "director_name": "Ananya Sen",
            "director_din": "09876543",
            "effective_date": "2024-10-16",
            "articles_authorise": True,
            "co_signatory": "Rajesh Malhotra (MD)"
        }
    })
    assert save_res.status_code == 200

    # 3. Generate draft
    gen_res = client.post(f"/api/v1/drafts/{draft_id}/generate")
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert data["status"] == "READY"
    assert "content_sha256" in data

    # 4. Preview HTML
    prev_res = client.get(f"/api/v1/drafts/{draft_id}/preview")
    assert prev_res.status_code == 200
    assert "text/html" in prev_res.headers["content-type"]
    assert "APEX INNOVATIONS PRIVATE LIMITED" in prev_res.text

    # 5. Export PDF
    exp_res = client.post(f"/api/v1/drafts/{draft_id}/exports", json={"format": "pdf"})
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["format"] == "pdf"
    assert "download_url" in exp_data

    # 6. Download file
    dl_res = client.get(exp_data["download_url"])
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"

    # 7. Multilingual Hindi Preview check
    prev_hi_res = client.get(f"/api/v1/drafts/{draft_id}/preview?target_language=hi")
    assert prev_hi_res.status_code == 200
    # Must contain Hindi text for director appointment resolution
    assert "निदेशक मंडल" in prev_hi_res.text or "अतिरिक्त निदेशक" in prev_hi_res.text

    # 8. Multilingual Bilingual Preview check
    prev_bi_res = client.get(f"/api/v1/drafts/{draft_id}/preview?target_language=bilingual")
    assert prev_bi_res.status_code == 200
    assert "CERTIFIED TRUE COPY" in prev_bi_res.text
    assert "प्रमाणित प्रतिलिपि" in prev_bi_res.text
