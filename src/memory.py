"""Procedural memory (md files) + episodic log access."""
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")


def load_memory() -> dict[str, str]:
    """Load procedural/semantic memory files. Keys: personality, facts, plan."""
    out = {}
    for name in ("personality", "facts", "plan"):
        with open(os.path.join(MEMORY_DIR, f"{name}.md"), encoding="utf-8") as f:
            out[name] = f.read()
    return out


def write_checkin(
    conn: sqlite3.Connection,
    run_type: str,
    direction: str,
    raw_text: str,
    structured: dict | None = None,
) -> None:
    conn.execute(
        "INSERT INTO checkins (ts, run_type, direction, raw_text, structured) VALUES (?, ?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            run_type,
            direction,
            raw_text,
            json.dumps(structured) if structured else None,
        ),
    )
    conn.commit()


def recent_checkins(conn: sqlite3.Connection, days: int = 7) -> list[tuple[str, str, str, str]]:
    """Last N days of check-ins as (ts, run_type, direction, raw_text). SQL-first, no RAG."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return conn.execute(
        "SELECT ts, run_type, direction, raw_text FROM checkins WHERE ts >= ? ORDER BY ts",
        (cutoff,),
    ).fetchall()
