"""Morning run (7:00 AM ET): compose one nudge -> send -> log -> STOP."""
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import db, llm, memory, prompts, scoreboard
from src.runs.guard import run_guarded
from src.tools import calendar, telegram


def main() -> None:
    conn = db.connect()
    mem = memory.load_memory()
    blocks, source = calendar.get_today_events()
    recent = memory.recent_checkins(conn, days=7)
    board = scoreboard.week_summary_text(conn)
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %d, %Y")

    text, usage = llm.compose(
        prompts.system_blocks(mem),
        prompts.morning_prompt(today_str, blocks, source, recent, board),
    )

    telegram.send_message(text)
    memory.write_checkin(conn, "morning", "sent", text)
    print(f"morning sent ({source} blocks) | {usage}")


if __name__ == "__main__":
    load_dotenv()
    run_guarded("morning", main)
