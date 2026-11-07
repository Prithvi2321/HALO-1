"""
Telegram Bot Long-Polling Runner
================================
Runs the Telegram bot continuously using long-polling (getUpdates).
Does not require localtunnel or any open ports. Connects directly
to Telegram Bot API and handles /auth, /agenda, /cases, /case, /note,
/notes, /news, /start, and /help.
"""

import os
import sys
import time
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Ensure root backend dir is in PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load .env
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

from sqlmodel import Session
from app.auth.repository import engine
from app.telegram.service import TelegramGatewayService
from app.telegram.controller import _send_telegram_message, _send_telegram_document

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def init_bot():
    """Clears any conflicting webhooks so getUpdates works cleanly."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(f"{API_BASE}/deleteWebhook", json={"drop_pending_updates": False})
            print(f"[Telegram Bot] deleteWebhook response: {resp.json()}")
        except Exception as e:
            print(f"[Telegram Bot] Warning: failed to delete webhook: {e}")


async def process_update(update: dict):
    """Processes a single incoming Telegram update."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    from_user = message.get("from", {})
    user_id = from_user.get("id")
    username = from_user.get("username")
    text = message.get("text", "")

    if not text or not chat_id:
        return

    print(f"[Telegram Bot] Received message from @{username} (ID {user_id}): {text}")

    with Session(engine) as session:
        try:
            reply = TelegramGatewayService.handle_command(
                session=session,
                telegram_user_id=user_id,
                text=text,
                username=username,
            )
        except Exception as err:
            reply = f"⚠️ Error processing command: {str(err)}"
            print(f"[Telegram Bot] Command error: {err}")

    if reply and chat_id:
        try:
            if isinstance(reply, dict):
                text_msg = reply.get("text", "")
                doc_path = reply.get("document_path")
                caption = reply.get("caption", "")
                if text_msg:
                    await _send_telegram_message(chat_id, text_msg)
                if doc_path and os.path.exists(doc_path):
                    await _send_telegram_document(chat_id, doc_path, caption)
            else:
                await _send_telegram_message(chat_id, str(reply))
            print(f"[Telegram Bot] Sent reply to {chat_id}")
        except Exception as err:
            print(f"[Telegram Bot] Send error: {err}")


async def run_polling():
    """Main polling loop."""
    print("=" * 60)
    print("🤖 HALO Telegram Bot Gateway Starting (Long-Polling Mode)")
    print(f"Bot Username: @{os.environ.get('TELEGRAM_BOT_USERNAME', 'HALO_NyayaSahyak_bot')}")
    print("=" * 60)

    if not BOT_TOKEN:
        print("[Telegram Bot] ERROR: TELEGRAM_BOT_TOKEN is not set. Please add TELEGRAM_BOT_TOKEN to your backend/.env file.")
        return

    await init_bot()

    offset = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"timeout": 20}
            if offset is not None:
                params["offset"] = offset

            try:
                resp = await client.get(f"{API_BASE}/getUpdates", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = u["update_id"] + 1
                        await process_update(u)
                else:
                    print(f"[Telegram Bot] getUpdates failed: {resp.status_code} - {resp.text}")
                    await asyncio.sleep(3)
            except (asyncio.CancelledError, KeyboardInterrupt):
                print("[Telegram Bot] Shutting down polling loop cleanly.")
                break
            except httpx.ReadTimeout:
                continue
            except Exception as e:
                print(f"[Telegram Bot] Polling exception: {e}")
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_polling())
