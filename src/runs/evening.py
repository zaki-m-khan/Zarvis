"""Evening run (9:00 PM ET): poll replies + button taps -> parse structured -> tally -> check-in -> STOP."""
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import db, llm, memory, prompts, scoreboard
from src.models import CheckIn
from src.runs.guard import run_guarded
from src.tools import calendar, telegram
from src.tools.telegram import BUTTON_TO_FIELD, CHECKIN_BUTTONS


def main() -> None:
    conn = db.connect()
    texts, taps = telegram.read_replies(conn)

    # Button taps are structured data directly — no LLM needed.
    for tap in taps:
        memory.write_checkin(conn, "evening", "received", f"[button] {tap}", structured=BUTTON_TO_FIELD[tap])

    # Free-text replies: log raw, then one parse call for the batch.
    for t in texts:
        memory.write_checkin(conn, "evening", "received", t)
    if texts:
        parsed: CheckIn | None = llm.parse_checkin(texts)
        if parsed:
            memory.write_checkin(
                conn, "evening", "received", "[parsed]",
                structured={k: v for k, v in parsed.model_dump().items() if v is not None},
            )

    board = scoreboard.week_summary_text(conn)  # retallies from checkins

    mem = memory.load_memory()
    blocks, source = calendar.get_today_events()
    recent = memory.recent_checkins(conn, days=7)
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %d, %Y")

    text, usage = llm.compose(
        prompts.system_blocks(mem),
        prompts.evening_prompt(today_str, blocks, source, texts + [f"(button) {t}" for t in taps], recent, board),
    )

    telegram.send_message(text, buttons=CHECKIN_BUTTONS)
    memory.write_checkin(conn, "evening", "sent", text)
    if not texts and not taps:
        memory.write_checkin(conn, "evening", "received", "", structured={"missed_checkin": True})
    print(f"evening sent ({len(texts)} texts, {len(taps)} taps) | {usage}")


if __name__ == "__main__":
    load_dotenv()
    run_guarded("evening", main)
