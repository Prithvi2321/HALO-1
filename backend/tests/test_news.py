"""
Unit tests for Indian Legal News service and Telegram integration.
"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.main import app
from app.news.service import (
    get_indian_legal_news,
    format_news_for_telegram,
    _clean_text,
    _format_date,
)
from app.telegram.service import TelegramGatewayService

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(test_engine)

client = TestClient(app)


def test_clean_text_and_format_date():
    assert _clean_text("<b>High Court</b> Judgment &amp; order") == "High Court Judgment &amp; order"
    assert _clean_text("") == ""
    assert _format_date("Wed, 04 Nov 2026 10:00:00 GMT") == "04 Nov 2026"
    assert _format_date("invalid") == "invalid"


def test_format_news_for_telegram():
    sample_items = [
        {
            "title": "Supreme Court Upholds Arbitration Clause",
            "source": "LiveLaw",
            "link": "https://example.com/art1",
            "published_at": "04 Nov 2026",
        }
    ]
    msg = format_news_for_telegram(sample_items, query="arbitration")
    assert "Supreme Court Upholds Arbitration Clause" in msg
    assert "LiveLaw" in msg
    assert "Read Article" in msg

    empty_msg = format_news_for_telegram([], query="nonexistent")
    assert "No recent news articles found" in empty_msg


@patch("app.news.service.httpx.Client")
def test_get_indian_legal_news_mocked(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>Delhi High Court passes landmark ruling - Bar and Bench</title>
          <link>https://example.com/news1</link>
          <pubDate>Wed, 04 Nov 2026 09:30:00 GMT</pubDate>
          <source url="https://barandbench.com">Bar and Bench</source>
        </item>
      </channel>
    </rss>
    """
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.__enter__.return_value = mock_client
    mock_client_cls.return_value = mock_client

    results = get_indian_legal_news(query="Delhi High Court", limit=5)
    assert len(results) == 1
    assert "Delhi High Court passes landmark ruling" in results[0]["title"]
    assert results[0]["source"] == "Bar and Bench"
    assert results[0]["published_at"] == "04 Nov 2026"


def test_telegram_news_command():
    with Session(test_engine) as session:
        with patch("app.telegram.service.get_indian_legal_news") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "title": "SC Grants Bail in PMLA Case",
                    "source": "SCC Online",
                    "link": "https://example.com/bail",
                    "published_at": "04 Nov 2026",
                }
            ]
            reply = TelegramGatewayService.handle_command(
                session=session,
                telegram_user_id=999999,
                text="/news bail",
                username="testadvocate"
            )
            assert "SC Grants Bail in PMLA Case" in reply
            assert "SCC Online" in reply


def test_api_news_endpoint():
    with patch("app.news.controller.get_indian_legal_news") as mock_fetch:
        mock_fetch.return_value = [
            {
                "title": "NCLAT issues notice on IBC resolution",
                "source": "India Legal",
                "link": "https://example.com/ibc",
                "published_at": "04 Nov 2026",
            }
        ]
        response = client.get("/api/v1/news/legal?query=IBC")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["count"] == 1
        assert data["articles"][0]["title"] == "NCLAT issues notice on IBC resolution"
