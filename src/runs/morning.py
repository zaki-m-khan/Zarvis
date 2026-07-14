"""Morning run (7:00 AM ET): for each active user, compose one nudge via the agent graph -> send -> log -> STOP."""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import agent, db, memory, prompts, scoreboard
from src.runs.guard import run_guarded
from src.tools import calendar, telegram


def run_for_user(conn, user: dict) -> None:
    chat_id = user["chat_id"]
    if chat_id == db.default_chat_id():
        blocks, source = calendar.get_today_events()  # Google Calendar is the owner's
    else:
        blocks, source = [], "plan"  # friends' blocks live in their plan_md (in the system prompt)
    recent = memory.recent_checkins(conn, days=7, chat_id=chat_id)
    board = scoreboard.week_summary_text(conn, chat_id, targets=user.get("targets"))
    today_str = datetime.now(ZoneInfo(user.get("tz") or "America/New_York")).strftime("%A, %B %d, %Y")

    text, tools_used = agent.run_agent(
        conn, user, prompts.morning_prompt(today_str, blocks, source, recent, board)
    )
    telegram.send_message(text, chat_id=chat_id)
    memory.write_checkin(conn, "morning", "sent", text, chat_id=chat_id)
    db.kv_set(conn, f"last_run:{chat_id}", json.dumps({
        "type": "morning", "ts": datetime.now(timezone.utc).isoformat(), "tools_used": tools_used,
    }))
    print(f"morning sent to {chat_id} ({source} blocks, {tools_used} tool calls)")


def main() -> None:
    conn = db.connect()
    memory.seed_default_user(conn)
    for user in db.active_users(conn):
        run_for_user(conn, user)


if __name__ == "__main__":
    load_dotenv()
    run_guarded("morning", main)
