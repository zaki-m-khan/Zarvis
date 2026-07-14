"""Procedural memory (md files / users table) + episodic log access.

Single-user era: memory came from memory/*.md. Multi-user: each user's plan /
personality / facts live on their users row (Zaki's row is seeded from the md
files); approved durable facts accumulate in the facts table (the disk on
Render is ephemeral, so the DB — not facts.md — is the durable store).
"""
import json
import os
from datetime import datetime, timedelta, timezone

from src import db

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")


def load_memory_files() -> dict[str, str]:
    """Load the md seed files. Keys: personality, facts, plan."""
    out = {}
    for name in ("personality", "facts", "plan"):
        with open(os.path.join(MEMORY_DIR, f"{name}.md"), encoding="utf-8") as f:
            out[name] = f.read()
    return out


def seed_default_user(conn) -> dict:
    """Ensure Zaki's user row exists (seeded from memory/*.md). Returns the user dict."""
    chat_id = db.default_chat_id()
    user = db.get_user(conn, chat_id)
    if user is None or not user.get("plan_md"):
        files = load_memory_files()
        db.upsert_user(
            conn,
            chat_id,
            name="Zaki",
            active=1,
            state="active",
            plan_md=files["plan"],
            personality_md=files["personality"],
            facts_md=files["facts"],
            targets=None,
        )
        user = db.get_user(conn, chat_id)
    return user


def approved_facts(conn, chat_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT fact FROM facts WHERE chat_id = ? AND status = 'approved' ORDER BY id",
        (chat_id,),
    ).fetchall()
    return [r[0] for r in rows]


def load_memory(conn=None, user: dict | None = None) -> dict[str, str]:
    """Memory for one user: personality / facts (seed + approved) / plan.

    Called with no args (legacy paths, tests) -> md files only.
    """
    if conn is None or user is None:
        return load_memory_files()
    files_fallback = None
    personality = user.get("personality_md")
    plan = user.get("plan_md")
    facts = user.get("facts_md")
    if not (personality and plan):
        files_fallback = load_memory_files()
    extra = approved_facts(conn, user["chat_id"])
    facts_text = facts or (files_fallback or load_memory_files())["facts"]
    if extra:
        facts_text += "\n\n## Learned facts (approved via consolidation gate)\n" + "\n".join(
            f"- {f}" for f in extra
        )
    return {
        "personality": personality or files_fallback["personality"],
        "facts": facts_text,
        "plan": plan or files_fallback["plan"],
    }


def write_checkin(
    conn,
    run_type: str,
    direction: str,
    raw_text: str,
    structured: dict | None = None,
    chat_id: int | None = None,
) -> None:
    conn.execute(
        "INSERT INTO checkins (chat_id, ts, run_type, direction, raw_text, structured) VALUES (?, ?, ?, ?, ?, ?)",
        (
            db.default_chat_id() if chat_id is None else chat_id,
            datetime.now(timezone.utc).isoformat(),
            run_type,
            direction,
            raw_text,
            json.dumps(structured) if structured else None,
        ),
    )
    conn.commit()


def recent_checkins(conn, days: int = 7, chat_id: int | None = None) -> list[tuple[str, str, str, str]]:
    """Last N days of check-ins as (ts, run_type, direction, raw_text). SQL-first, no RAG."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return conn.execute(
        "SELECT ts, run_type, direction, raw_text FROM checkins WHERE ts >= ? AND chat_id = ? ORDER BY ts",
        (cutoff, db.default_chat_id() if chat_id is None else chat_id),
    ).fetchall()
