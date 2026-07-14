"""Evening run (9:00 PM ET): ingest replies -> tally -> per-user check-in via the agent graph -> STOP.

Two ingestion modes:
- Polling (local / pre-cutover): getUpdates at run time (owner's allowlist only).
- WEBHOOK_MODE=1 (Render): replies were already ingested in real time by the
  webhook — polling would 409 against Telegram once a webhook is set, so skip it.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import agent, db, llm, memory, prompts, scoreboard
from src.models import CheckIn
from src.runs.guard import run_guarded
from src.tools import calendar, telegram
from src.tools.telegram import BUTTON_TO_FIELD, CHECKIN_BUTTONS


def ingest_polled(conn) -> None:
    """Pre-webhook path: poll once, log raw + parsed for the owner."""
    texts, taps = telegram.read_replies(conn)
    for tap in taps:
        memory.write_checkin(conn, "evening", "received", f"[button] {tap}", structured=BUTTON_TO_FIELD[tap])
    for t in texts:
        memory.write_checkin(conn, "evening", "received", t)
    if texts:
        parsed: CheckIn | None = llm.parse_checkin(texts)
        if parsed:
            memory.write_checkin(
                conn, "evening", "received", "[parsed]",
                structured={k: v for k, v in parsed.model_dump().items() if v is not None},
            )


def todays_replies(conn, chat_id: int) -> list[str]:
    """Received messages in the last ~20h (since after the previous evening run)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()
    rows = conn.execute(
        "SELECT raw_text FROM checkins WHERE chat_id = ? AND direction = 'received' "
        "AND ts >= ? AND raw_text != '' ORDER BY ts",
        (chat_id, cutoff),
    ).fetchall()
    return [r[0] for r in rows if r[0] and not r[0].startswith("[parsed]") and not r[0].startswith("[tool:")]


def run_for_user(conn, user: dict) -> None:
    chat_id = user["chat_id"]
    replies = todays_replies(conn, chat_id)
    board = scoreboard.week_summary_text(conn, chat_id, targets=user.get("targets"))  # retallies

    if chat_id == db.default_chat_id():
        blocks, source = calendar.get_today_events()
    else:
        blocks, source = [], "plan"
    recent = memory.recent_checkins(conn, days=7, chat_id=chat_id)
    today_str = datetime.now(ZoneInfo(user.get("tz") or "America/New_York")).strftime("%A, %B %d, %Y")

    text, tools_used = agent.run_agent(
        conn, user, prompts.evening_prompt(today_str, blocks, source, replies, recent, board)
    )
    telegram.send_message(text, buttons=CHECKIN_BUTTONS, chat_id=chat_id)
    memory.write_checkin(conn, "evening", "sent", text, chat_id=chat_id)
    if not replies:
        memory.write_checkin(conn, "evening", "received", "", structured={"missed_checkin": True}, chat_id=chat_id)
    db.kv_set(conn, f"last_run:{chat_id}", json.dumps({
        "type": "evening", "ts": datetime.now(timezone.utc).isoformat(), "tools_used": tools_used,
    }))
    print(f"evening sent to {chat_id} ({len(replies)} replies, {tools_used} tool calls)")


def main() -> None:
    conn = db.connect()
    memory.seed_default_user(conn)
    if not os.environ.get("WEBHOOK_MODE"):
        ingest_polled(conn)
    for user in db.active_users(conn):
        run_for_user(conn, user)


if __name__ == "__main__":
    load_dotenv()
    run_guarded("evening", main)
