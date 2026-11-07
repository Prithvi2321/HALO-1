"""
Telegram Bot Gateway Service (PRD §8)
=====================================
Handles 6-digit pairing OTP issuance and verification, command dispatch,
and message formatting for Telegram bot interactions.
"""

import os
import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List
from sqlmodel import Session, select

from app.workspace.model import (
    TelegramLink,
    TelegramPairingCode,
    LegalMatter,
    CalendarEvent,
    Draft,
    DraftVersion,
    MatterNote,
    now_utc,
)
from app.workspace.repository import TenantRepository
from app.news.service import get_indian_legal_news, format_news_for_telegram
from app.drafting.intake import generate_draft_package, resolve_template_id
import json


def escape_markdown_v2(text: str) -> str:
    """Escapes Telegram MarkdownV2 reserved characters."""
    reserved = r"_*[]()~`>#+-=|{}.!"
    escaped = []
    for char in text:
        if char in reserved:
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)


class TelegramGatewayService:
    """Handles pairing and command processing for the Telegram Bot."""

    @staticmethod
    def generate_pairing_otp(session: Session, user_id: int) -> Tuple[str, datetime]:
        """Generates a secure 6-digit single-use OTP valid for 5 minutes."""
        otp = f"{random.randint(100000, 999999):06d}"
        code_hash = hashlib.sha256(otp.encode("utf-8")).hexdigest()
        expires_at = now_utc() + timedelta(minutes=5)

        # Store pairing code record
        pairing_record = TelegramPairingCode(
            code_hash=code_hash,
            user_id=user_id,
            expires_at=expires_at,
        )
        session.add(pairing_record)
        session.commit()
        return otp, expires_at

    @staticmethod
    def pair_with_otp(session: Session, telegram_user_id: int, otp: str, username: Optional[str] = None) -> Tuple[bool, str]:
        """Validates OTP and pairs telegram_user_id with the user account."""
        code_hash = hashlib.sha256(otp.strip().encode("utf-8")).hexdigest()
        statement = select(TelegramPairingCode).where(
            TelegramPairingCode.code_hash == code_hash,
            TelegramPairingCode.used_at == None  # noqa: E711
        )
        record = session.exec(statement).first()

        if not record:
            return False, "Invalid or expired pairing code. Please generate a new code from the web app."

        if now_utc() > record.expires_at:
            return False, "Pairing code has expired. Please generate a new one from Settings → Telegram."

        # Mark OTP as used
        record.used_at = now_utc()
        session.add(record)

        # Bind or update telegram_link
        link_stmt = select(TelegramLink).where(TelegramLink.telegram_user_id == telegram_user_id)
        existing_link = session.exec(link_stmt).first()

        if existing_link:
            existing_link.user_id = record.user_id
            existing_link.telegram_username = username
            existing_link.paired_at = now_utc()
            existing_link.revoked_at = None
            session.add(existing_link)
        else:
            new_link = TelegramLink(
                user_id=record.user_id,
                telegram_user_id=telegram_user_id,
                telegram_username=username,
            )
            session.add(new_link)

        session.commit()
        return True, "Successfully paired with HALO. Type /agenda today to view your schedule."

    @staticmethod
    def unpair(session: Session, telegram_user_id: int) -> bool:
        """Unpairs the telegram user."""
        statement = select(TelegramLink).where(TelegramLink.telegram_user_id == telegram_user_id)
        link = session.exec(statement).first()
        if link:
            link.revoked_at = now_utc()
            session.add(link)
            session.commit()
            return True
        return False

    @staticmethod
    def get_paired_user_id(session: Session, telegram_user_id: int) -> Optional[int]:
        """Returns paired user_id if valid and active."""
        statement = select(TelegramLink).where(
            TelegramLink.telegram_user_id == telegram_user_id,
            TelegramLink.revoked_at == None  # noqa: E711
        )
        link = session.exec(statement).first()
        return link.user_id if link else None

    @classmethod
    def handle_command(
        cls,
        session: Session,
        telegram_user_id: int,
        text: str,
        username: Optional[str] = None
    ) -> str:
        """Dispatches commands as specified in PRD §8.3."""
        parts = text.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        # Unpaired accessible commands
        if command in ["/start", "/help"]:
            return (
                "⚖️ *Welcome to HALO (Nyaya Sahayak) Legal Gateway*\n\n"
                "Commands:\n"
                "• `/draft <type> <info>` — Instant court-ready legal auto-drafting & PDF export\n"
                "• `/forms` — View supported legal instruments & drafting examples\n"
                "• `/auth <6-digit-otp>` — Pair your mobile account\n"
                "• `/news [topic]` — Live Indian court cases & legal updates\n"
                "• `/agenda today|tomorrow|week` — Your court hearings & deadlines\n"
                "• `/cases [search]` — Active matters\n"
                "• `/case <name or id>` — Matter summary\n"
                "• `/note <case> <text>` — Record important points & oral orders\n"
                "• `/notes <case>` — Review all recorded notes for a case\n"
                "• `/draft_status <id>` — Check draft generation progress\n"
                "• `/ask <query>` — Legal AI research (coming soon)\n"
                "• `/logout` — Unpair this chat"
            )

        if command in ["/news", "/legalnews"]:
            articles = get_indian_legal_news(query=arg, limit=5)
            return format_news_for_telegram(articles, query=arg)

        if command == "/auth":
            if not arg:
                return "Please provide the 6-digit OTP code: `/auth 123456`"
            success, msg = cls.pair_with_otp(session, telegram_user_id, arg, username)
            return msg

        if command in ["/draft", "/drafts", "/form", "/forms"]:
            user_id = cls.get_paired_user_id(session, telegram_user_id)
            return cls.handle_draft_command(session, user_id, arg, username)

        # Check authentication for remaining commands
        user_id = cls.get_paired_user_id(session, telegram_user_id)
        if not user_id:
            return "🔒 You are not paired. Open the HALO web app, navigate to Settings → Telegram, click 'Generate Pairing Code', and send `/auth <code>` here."

        if command == "/logout":
            cls.unpair(session, telegram_user_id)
            return "✅ Successfully unpaired from HALO."

        repo = TenantRepository(session, firm_id="firm_default")

        if command == "/cases":
            matters = repo.list_matters(status="ACTIVE", search=arg)
            if not matters:
                return "No active matters found."
            lines = ["📂 *Top Active Matters:*\n"]
            for m in matters[:5]:
                lines.append(f"• *{m.matter_name}*\n  Forum: {m.forum_type} ({m.forum_detail or 'General'})\n  Case No: {m.case_number or 'Pending'}\n  ID: `{m.id[:8]}`\n")
            return "\n".join(lines)

        if command == "/case":
            if not arg:
                return "Usage: `/case <matter_id or name>`"
            matters = repo.list_matters(search=arg)
            matter = matters[0] if matters else repo.get_matter(arg)
            if not matter:
                return f"No matter found matching '{arg}'."

            events = repo.list_events(matter_id=matter.id)
            next_hearing = next((e for e in events if e.event_type == "HEARING" and e.starts_at >= now_utc()), None)
            notes = repo.list_matter_notes(matter.id)
            latest_note = notes[0].content if notes else "No notes recorded."

            res = (
                f"📋 *Matter Dossier: {matter.matter_name}*\n"
                f"• *Status*: {matter.status}\n"
                f"• *Forum*: {matter.forum_type} — {matter.forum_detail or 'Main'}\n"
                f"• *Act*: {matter.statutory_act}\n"
                f"• *Lead Advocate*: {matter.lead_advocate_name or 'Assigned'}\n"
                f"• *Next Hearing*: {next_hearing.starts_at.strftime('%d %b %Y, %H:%M') if next_hearing else 'None scheduled'}\n"
                f"• *Latest Note*: _{latest_note}_\n"
            )
            if len(notes) > 1:
                res += f"\n💡 _Total {len(notes)} notes on file. Type `/notes {arg}` to view history._"
            return res

        if command == "/note":
            if not arg or len(arg.split(maxsplit=1)) < 2:
                return "Usage: `/note <case_name> <your note or observation>`\nExample: `/note Tata Court granted 2 weeks to file counter-affidavit.`"
            case_query, note_text = arg.split(maxsplit=1)
            matters = repo.list_matters(search=case_query)
            matter = matters[0] if matters else repo.get_matter(case_query)
            if not matter:
                return f"No matter found matching '{case_query}'. Use `/cases` to check active matter names."

            note_obj = MatterNote(
                matter_id=matter.id,
                author_id=user_id,
                author_name=username or "Advocate",
                content=note_text.strip(),
            )
            repo.add_matter_note(note_obj)
            return (
                f"✅ *Note Saved to {matter.matter_name}:*\n"
                f"_{note_text.strip()}_\n\n"
                f"Stored in matter dossier and visible on your web dashboard."
            )

        if command == "/notes":
            if not arg:
                return "Usage: `/notes <case_name or id>`"
            matters = repo.list_matters(search=arg)
            matter = matters[0] if matters else repo.get_matter(arg)
            if not matter:
                return f"No matter found matching '{arg}'."

            notes = repo.list_matter_notes(matter.id)
            if not notes:
                return f"📋 *Notes for {matter.matter_name}:*\nNo notes recorded yet. Use `/note {matter.matter_name.split()[0]} <text>` to add one."

            lines = [f"📋 *Important Notes & Points: {matter.matter_name}*\n"]
            for idx, n in enumerate(notes[:5], 1):
                date_str = n.created_at.strftime("%d %b %Y, %H:%M")
                lines.append(f"{idx}\\. *{n.author_name}* ({date_str}):\n   _{n.content}_\n")
            return "\n".join(lines)

        if command == "/agenda":
            period = arg.lower() or "today"
            now = now_utc()
            today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

            if period == "tomorrow":
                from_dt = today_start + timedelta(days=1)
                to_dt = from_dt + timedelta(days=1)
                header = f"📅 *Agenda for Tomorrow ({from_dt.strftime('%d %b %Y')}):*\n"
            elif period == "week":
                from_dt = today_start
                to_dt = today_start + timedelta(days=7)
                header = "📅 *Agenda for Next 7 Days:*\n"
            else:
                from_dt = today_start
                to_dt = today_start + timedelta(days=1)
                header = f"📅 *Today's Agenda ({today_start.strftime('%d %b %Y')}):*\n"

            events = repo.list_events(from_date=from_dt, to_date=to_dt)
            if not events:
                return f"{header}\nNo hearings or deadlines scheduled."

            lines = [header]
            for e in events:
                time_str = e.starts_at.strftime("%H:%M IST") if not e.all_day else "All Day"
                type_icon = "⚖️" if e.event_type == "HEARING" else "⏰"
                lines.append(f"{type_icon} *{time_str}* — {e.event_title}")
                if e.computation_explanation:
                    lines.append(f"   _{e.computation_explanation}_")
            return "\n".join(lines)

        if command == "/draft_status":
            if not arg:
                return "Usage: `/draft_status <draft_id>`"
            draft = repo.get_draft(arg)
            if not draft:
                return f"Draft '{arg}' not found."
            return f"📄 *Draft Status:* {draft.title}\nStatus: *{draft.status}*\nTemplate: `{draft.template_id}`\nLast updated: {draft.updated_at.strftime('%d %b %Y, %H:%M')}"

        if command == "/ask":
            # Per PRD §13 seam: reply with stub message until Phase 5 RAG wiring
            return "🔍 Legal research via Telegram is coming soon."

        return "Unknown command. Send `/help` for the list of available commands."

    @classmethod
    def handle_draft_command(
        cls,
        session: Session,
        user_id: Optional[int],
        arg: str,
        username: Optional[str] = None
    ) -> Any:
        """
        Handles /draft and /forms commands:
        Extracts parameters, generates court-ready legal instrument with SHA-256 seal,
        returns structured summary text and PDF file path for Telegram delivery.
        """
        if not arg or arg.strip().lower() in ["help", "list", "types", "menu", "templates"]:
            return (
                "📄 *HALO Instant Legal Auto-Drafting Studio*\n\n"
                "Generate airtight, court-ready legal instruments with cryptographic SHA-256 seals directly from Telegram!\n\n"
                "*How to use:*\n"
                "Send: `/draft <type> <details>`\n\n"
                "*Supported Form Types:*\n"
                "• `rent` — Residential & Commercial Lease Agreement\n"
                "• `138` — Section 138 Cheque Bounce 15-Day Demand Notice\n"
                "• `nda` — Commercial Non-Disclosure Agreement\n"
                "• `consultant` — Independent Consultant Engagement Agreement\n"
                "• `director` — Board Resolution (Appoint Additional Director)\n\n"
                "*Quick Examples:*\n"
                "👉 `/draft rent Landlord Ramesh Sharma, tenant Priya Singh, rent ₹25,000, deposit ₹50,000, Flat 302 Mumbai, 11 months`\n"
                "👉 `/draft 138 Payee Apex Supplies, Drawer Sunil Mehta, cheque 409218, amount ₹15,00,000, bank HDFC Bank, reason Funds Insufficient`\n"
                "👉 `/draft nda Disclosing Alpha Tech, Receiving Beta Solutions, 2 years, Delhi`\n"
                "👉 `/draft consultant Client Acme Corp, Consultant Dr. Arvind Nair, fee ₹1,50,000, scope Compliance Audit`\n\n"
                "🌐 *Multilingual:* Add `language hindi` or `द्विभाषी` to render in Devnagari Hindi or Bilingual!"
            )

        # Handle type-specific help prompts
        arg_clean = arg.strip().lower()
        if arg_clean == "rent":
            return (
                "📄 *Rent / Lease Agreement Drafting*\n\n"
                "Please provide details in one message, e.g.:\n"
                "`/draft rent Landlord is Ramesh Sharma, tenant Rahul Verma, rent ₹28,000, deposit ₹60,000, Flat 402 Pune, 11 months, language Hindi`"
            )
        if arg_clean in ["138", "cheque", "bounce"]:
            return (
                "⚖️ *Section 138 Cheque Bounce Demand Notice*\n\n"
                "Please provide cheque details, e.g.:\n"
                "`/draft 138 Payee Apex Supplies, Drawer Sunil Mehta, cheque 409218, amount ₹15,00,000, bank HDFC Bank, reason Funds Insufficient`"
            )
        if arg_clean == "nda":
            return (
                "🔒 *Commercial Non-Disclosure Agreement (NDA)*\n\n"
                "Please provide party details, e.g.:\n"
                "`/draft nda Disclosing Alpha Tech, Receiving Beta Solutions, 2 years, Delhi`"
            )
        if arg_clean in ["consultant", "freelance"]:
            return (
                "💼 *Independent Consultant Agreement*\n\n"
                "Please provide engagement details, e.g.:\n"
                "`/draft consultant Client Acme Corp, Consultant Dr. Arvind Nair, fee ₹1,50,000, scope Software architecture advisory`"
            )
        if arg_clean in ["director", "board"]:
            return (
                "🏛️ *Board Resolution — Additional Director (S.161(1))*\n\n"
                "Please provide resolution details, e.g.:\n"
                "`/draft director Company Acme Tech, appointee Priya Sharma, DIN 08945612, venue Mumbai, chairman Rajesh Kumar`"
            )

        # Parse template and text
        parts = arg.strip().split(maxsplit=1)
        first_word = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        resolved_from_first = resolve_template_id(first_word)
        if resolved_from_first and rest:
            target_tmpl = resolved_from_first
            details_text = rest
        else:
            resolved_from_all = resolve_template_id(arg)
            target_tmpl = resolved_from_all or "RENT_AGREEMENT_RESIDENTIAL_V1"
            details_text = arg

        try:
            summary, pdf_path, _ = generate_draft_package(
                query_or_template_id=target_tmpl,
                details_text=details_text
            )
        except Exception as gen_err:
            return f"⚠️ *Drafting Error:* {str(gen_err)}\n\nPlease try again with format: `/draft <type> <details>`"

        # Build neat summary
        title = summary["title"]
        anchor = summary["statutory_anchor"]
        lang = summary["language"]
        content_hash = summary["content_sha256"]
        inp = summary["inputs"]

        lines = [
            f"⚖️ *HALO Legal Auto-Drafting Engine*",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📋 *Instrument:* {title}",
            f"🏛️ *Statutory Anchor:* {anchor}",
            f"🌐 *Language:* {lang}",
            f"",
            f"*Key Parameters Extracted:*",
        ]

        if "landlord_name" in inp:
            lines.append(f"• *Landlord / Lessor:* {inp['landlord_name']}")
        if "tenant_name" in inp:
            lines.append(f"• *Tenant / Lessee:* {inp['tenant_name']}")
        if "payee_name" in inp:
            lines.append(f"• *Payee (Client):* {inp['payee_name']}")
        if "drawer_name" in inp:
            lines.append(f"• *Accused / Drawer:* {inp['drawer_name']}")
        if "disclosing_party" in inp:
            lines.append(f"• *Disclosing Party:* {inp['disclosing_party']}")
        if "receiving_party" in inp:
            lines.append(f"• *Receiving Party:* {inp['receiving_party']}")
        if "client_name" in inp:
            lines.append(f"• *Client Organization:* {inp['client_name']}")
        if "consultant_name" in inp:
            lines.append(f"• *Consultant:* {inp['consultant_name']}")
        if "director_name" in inp:
            din_str = f" (DIN: {inp['director_din']})" if 'director_din' in inp else ""
            lines.append(f"• *Appointee Director:* {inp['director_name']}{din_str}")

        if "monthly_rent" in inp:
            lines.append(f"• *Monthly Rent:* ₹ {inp['monthly_rent']:,}/-")
        if "security_deposit" in inp:
            lines.append(f"• *Security Deposit:* ₹ {inp['security_deposit']:,}/-")
        if "cheque_amount" in inp:
            lines.append(f"• *Cheque Amount:* ₹ {inp['cheque_amount']:,}/-")
        if "fee_amount" in inp:
            lines.append(f"• *Professional Fee:* ₹ {inp['fee_amount']:,}/-")

        if "cheque_no" in inp:
            lines.append(f"• *Cheque Number:* #{inp['cheque_no']}")
        if "bank_name" in inp:
            lines.append(f"• *Drawee Bank:* {inp['bank_name']}")
        if "dishonour_reason" in inp:
            lines.append(f"• *Dishonour Reason:* {inp['dishonour_reason']}")
        if "tenure_months" in inp:
            lines.append(f"• *Lease Period:* {inp['tenure_months']} Months")
        if "duration_years" in inp:
            lines.append(f"• *Confidentiality Term:* {inp['duration_years']} Years")
        if "premises_address" in inp:
            lines.append(f"• *Premises:* {inp['premises_address']}")

        lines.extend([
            f"",
            f"🔒 *Cryptographic Seal:*",
            f"SHA-256: `{content_hash[:32]}...`",
        ])

        # If user is paired, record draft in database
        if user_id:
            try:
                repo = TenantRepository(session, firm_id="firm_default")
                draft_record = Draft(
                    firm_id="firm_default",
                    template_id=summary["template_id"],
                    title=f"{title} (via Telegram)",
                    status="READY"
                )
                repo.create_draft(draft_record)
                v = DraftVersion(
                    draft_id=draft_record.id,
                    version_no=1,
                    input_json=json.dumps(inp),
                    content_sha256=content_hash
                )
                repo.add_draft_version(v)
                lines.append(f"\n💾 _Saved to your HALO workspace as Draft `{draft_record.id[:8]}`._")
            except Exception:
                pass

        lines.append(f"\n📥 *Court-ready PDF with cryptographic seal is attached below!*")

        return {
            "text": "\n".join(lines),
            "document_path": pdf_path,
            "caption": f"📄 {title} — HALO Sealed PDF"
        }

