"""One-off: copy SQLite jarvis.db data into Supabase Postgres.

Usage:
    python -m scripts.migrate_to_pg path/to/jarvis.db [path/to/other.db ...]

Reads DATABASE_URL (postgres) from env/.env, unions checkins from every given
SQLite file (dedup on (ts, direction, raw_text)), stamps rows missing chat_id
with TELEGRAM_CHAT_ID, copies kv (tg_offset), and seeds Zaki's user row.
Scoreboard is NOT copied — it's derived; re-tallied on next run.
"""
import sqlite3
import sys

from dotenv import load_dotenv

from src import db, memory, scoreboard


def rows_from_sqlite(path: str) -> list[tuple]:
    src = sqlite3.connect(path)
    cols = [r[1] for r in src.execute("PRAGMA table_info(checkins)").fetchall()]
    has_chat = "chat_id" in cols
    sel = "SELECT ts, run_type, direction, raw_text, structured" + (", chat_id" if has_chat else "") + " FROM checkins ORDER BY id"
    out = []
    for row in src.execute(sel).fetchall():
        ts, run_type, direction, raw_text, structured = row[:5]
        chat_id = row[5] if has_chat and row[5] else db.default_chat_id()
        out.append((chat_id, ts, run_type, direction, raw_text, structured))
    offset = src.execute("SELECT value FROM kv WHERE key='tg_offset'").fetchone()
    src.close()
    return out, (offset[0] if offset else None)


def main(paths: list[str]) -> None:
    load_dotenv()
    pg = db.connect()  # DATABASE_URL must point at Postgres
    if not pg.is_pg:
        sys.exit("DATABASE_URL is not postgres:// — refusing (this script writes to Supabase only).")

    existing = {
        (ts, direction, raw) for ts, direction, raw in
        (r for r in pg.execute("SELECT ts, direction, raw_text FROM checkins").fetchall())
    }
    inserted = skipped = 0
    best_offset = 0
    for path in paths:
        rows, offset = rows_from_sqlite(path)
        best_offset = max(best_offset, int(offset or 0))
        for chat_id, ts, run_type, direction, raw_text, structured in rows:
            if (ts, direction, raw_text) in existing:
                skipped += 1
                continue
            pg.execute(
                "INSERT INTO checkins (chat_id, ts, run_type, direction, raw_text, structured) VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, ts, run_type, direction, raw_text, structured),
            )
            existing.add((ts, direction, raw_text))
            inserted += 1
    if best_offset:
        db.kv_set(pg, "tg_offset", str(best_offset))
    pg.commit()

    user = memory.seed_default_user(pg)
    values = scoreboard.tally_week(pg, user["chat_id"])
    print(f"migrated: {inserted} checkins inserted, {skipped} dups skipped, tg_offset={best_offset}")
    print(f"user seeded: {user['name']} ({user['chat_id']}), week tally: {values}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
