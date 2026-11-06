"""
seed_users.py — One-time script to seed test user accounts into halo.db

Run from the project root (with venv activated):
    python backend/scripts/seed_users.py

Idempotent: skips accounts that already exist.
"""

import sys
from pathlib import Path

# ── Make sure project root is on sys.path ──────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]  # …/HALO
sys.path.insert(0, str(ROOT / "backend"))

from sqlmodel import Session  # noqa: E402
from app.auth.repository import engine, init_db, get_user_by_email, create_user  # noqa: E402
from app.auth.model import Role, User  # noqa: E402
from app.auth.service import get_password_hash  # noqa: E402

TEST_ACCOUNTS = [
    {
        "email": "admin@halo.legal",
        "password": "HaloAdmin@2026",
        "role": Role.ADMIN,
    },
    {
        "email": "lawyer@halo.legal",
        "password": "HaloLawyer@2026",
        "role": Role.LAWYER,
    },
    {
        "email": "researcher@halo.legal",
        "password": "HaloResearch@2026",
        "role": Role.RESEARCHER,
    },
]


def main() -> None:
    init_db()
    created = []
    skipped = []

    with Session(engine, expire_on_commit=False) as session:
        for acct in TEST_ACCOUNTS:
            existing = get_user_by_email(session, acct["email"])
            if existing:
                skipped.append(acct["email"])
                continue

            user = User(
                email=acct["email"],
                password_hash=get_password_hash(acct["password"]),
                role=acct["role"],
            )
            create_user(session, user)
            created.append(acct)

    print("\n" + "=" * 60)
    print("  HALO — Test User Seed Results")
    print("=" * 60)

    if created:
        print("\n[OK]  Created accounts:\n")
        print(f"  {'Email':<35} {'Password':<20} {'Role'}")
        print(f"  {'-'*35} {'-'*20} {'-'*15}")
        for a in created:
            print(f"  {a['email']:<35} {a['password']:<20} {a['role'].value}")

    if skipped:
        print(f"\n[SKIP]  Already existed: {', '.join(skipped)}")

    if not created and not skipped:
        print("\nNothing to do.")

    print("\n  Login URL : http://localhost:5173")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
