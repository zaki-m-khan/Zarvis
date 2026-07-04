"""Evening run (9:00 PM ET): poll replies -> log raw -> compose check-in -> send -> log -> STOP."""
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import db, llm, memory, prompts
from src.runs.guard import run_guarded
from src.tools import calendar, telegram


def main() -> None:
    conn = db.connect()
    replies = telegram.read_replies(conn)
    for r in replies:
        memory.write_checkin(conn, "evening", "received", r)

    mem = memory.load_memory()
    blocks, source = calendar.get_today_events()
    recent = memory.recent_checkins(conn, days=7)
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %d, %Y")

    text, usage = llm.compose(
        prompts.system_blocks(mem),
        prompts.evening_prompt(today_str, blocks, source, replies, recent),
    )

    telegram.send_message(text)
    memory.write_checkin(conn, "evening", "sent", text)
    if not replies:
        memory.write_checkin(conn, "evening", "received", "", structured={"missed_checkin": True})
    print(f"evening sent ({len(replies)} replies) | {usage}")


if __name__ == "__main__":
    load_dotenv()
    run_guarded("evening", main)
