"""
Telegram Controller & FastAPI Router (PRD §11.3)
================================================
Endpoints:
- POST /telegram/pairing-codes: Generates 6-digit OTP
- DELETE /telegram/link: Unpairs Telegram link
- POST /telegram/webhook: Bot updates webhook
- GET /telegram/status: Checks user's pairing status
"""

import os
import re
import httpx
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.auth.repository import get_session
from app.workspace.model import TelegramLink
from app.telegram.service import TelegramGatewayService

router = APIRouter(prefix="/telegram", tags=["telegram"])

TELEGRAM_SECRET_TOKEN = os.environ.get("TELEGRAM_BOT_SECRET", "halo-telegram-secret-token")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _normalize_telegram_markdown(text: str) -> str:
    """Normalizes standard markdown (**bold**) to Telegram v1 (*bold*)."""
    # Replace **bold** with *bold*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    # Remove escaped dots from titles
    text = text.replace(r"\.", ".")
    return text


async def _send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
    """Sends a reply back to Telegram via Bot API sendMessage with markdown fallback."""
    if not TELEGRAM_BOT_TOKEN:
        return  # Token not configured — skip sending

    formatted_text = _normalize_telegram_markdown(text)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json={"chat_id": chat_id, "text": formatted_text, "parse_mode": parse_mode},
            )
            # If Telegram fails due to markdown parse error, send as plain text
            if resp.status_code != 200:
                clean_plain_text = re.sub(r"[\*_`\[\]\(\)]", "", text)
                await client.post(
                    f"{TELEGRAM_API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": clean_plain_text},
                )
    except Exception:
        # Gracefully handle network timeouts or testing environment mocks
        pass


async def _send_telegram_document(chat_id: int, file_path: str, caption: str = "") -> bool:
    """Sends a document (e.g. court-ready PDF) to a Telegram chat via Bot API sendDocument."""
    if not TELEGRAM_BOT_TOKEN or not file_path or not os.path.exists(file_path):
        return False

    filename = os.path.basename(file_path)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, "rb") as f:
                files = {"document": (filename, f, "application/pdf")}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption[:1000]
                resp = await client.post(
                    f"{TELEGRAM_API_BASE}/sendDocument",
                    data=data,
                    files=files,
                )
                return resp.status_code == 200
    except Exception:
        # Gracefully handle network timeouts or test mock environments
        return False


class PairingCodeResponse(BaseModel):
    otp: str
    expires_at: str
    valid_seconds: int = 300
    instructions: str = "Send /auth <otp> to @HALO_NyayaSahyak_bot in Telegram."


@router.post("/pairing-codes", response_model=PairingCodeResponse)
def api_generate_pairing_code(
    user_id: int = 1,  # In production, injected from current_user
    session: Session = Depends(get_session)
):
    """Generates a secure 6-digit OTP for Telegram bot pairing."""
    otp, expires_at = TelegramGatewayService.generate_pairing_otp(session, user_id=user_id)
    return PairingCodeResponse(
        otp=otp,
        expires_at=expires_at.isoformat(),
        valid_seconds=300
    )


@router.get("/status")
def api_get_pairing_status(
    user_id: int = 1,
    session: Session = Depends(get_session)
):
    """Checks whether the user currently has an active paired Telegram account."""
    statement = select(TelegramLink).where(
        TelegramLink.user_id == user_id,
        TelegramLink.revoked_at == None  # noqa: E711
    )
    link = session.exec(statement).first()
    return {
        "is_paired": link is not None,
        "telegram_user_id": link.telegram_user_id if link else None,
        "username": link.telegram_username if link else None,
        "paired_at": link.paired_at.isoformat() if link else None,
    }


@router.delete("/link")
def api_unpair_telegram(
    user_id: int = 1,
    session: Session = Depends(get_session)
):
    """Unpairs Telegram account for the user."""
    statement = select(TelegramLink).where(
        TelegramLink.user_id == user_id,
        TelegramLink.revoked_at == None  # noqa: E711
    )
    link = session.exec(statement).first()
    if link:
        TelegramGatewayService.unpair(session, link.telegram_user_id)
        return {"status": "unpaired"}
    return {"status": "no_active_link"}


@router.post("/webhook")
async def api_telegram_webhook(
    update: Dict[str, Any],
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
    session: Session = Depends(get_session)
):
    """
    Receives incoming webhook updates from Telegram Bot API.
    Optionally validates X-Telegram-Bot-Api-Secret-Token header.
    """
    # Verify secret token if configured
    if TELEGRAM_SECRET_TOKEN and TELEGRAM_SECRET_TOKEN != "halo-telegram-secret-token":
        if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram secret token.")

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"status": "ignored"}

    from_user = message.get("from", {})
    chat_id = message.get("chat", {}).get("id")
    telegram_user_id = from_user.get("id")
    username = from_user.get("username")
    text = message.get("text", "")

    if not text or not telegram_user_id:
        return {"status": "no_text"}

    reply_data = TelegramGatewayService.handle_command(
        session=session,
        telegram_user_id=telegram_user_id,
        text=text,
        username=username
    )

    # Send reply back to Telegram (text summary and optional document)
    reply_text = ""
    if chat_id and reply_data:
        if isinstance(reply_data, dict):
            reply_text = reply_data.get("text", "")
            doc_path = reply_data.get("document_path")
            caption = reply_data.get("caption", "")
            if reply_text:
                await _send_telegram_message(chat_id, reply_text)
            if doc_path and os.path.exists(doc_path):
                await _send_telegram_document(chat_id, doc_path, caption)
        else:
            reply_text = str(reply_data)
            await _send_telegram_message(chat_id, reply_text)

    return {
        "status": "processed",
        "chat_id": chat_id,
        "reply_text": reply_text,
    }

