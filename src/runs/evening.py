"""Evening run (9:00 PM ET): poll replies -> log raw -> compose check-in -> send -> log -> STOP."""
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic
from dotenv import load_dotenv

from src import db, memory, prompts
from src.runs.guard import run_guarded
from src.tools import calendar, telegram

MODEL = "claude-haiku-4-5"


def main() -> None:
    conn = db.connect()
    replies = telegram.read_replies(conn)
    for r in replies:
        memory.write_checkin(conn, "evening", "received", r)

    mem = memory.load_memory()
    blocks, source = calendar.get_today_events()
    recent = memory.recent_checkins(conn, days=7)
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %d, %Y")

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=prompts.system_blocks(mem),
        messages=[{"role": "user", "content": prompts.evening_prompt(today_str, blocks, source, replies, recent)}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    telegram.send_message(text)
    memory.write_checkin(conn, "evening", "sent", text)
    if not replies:
        memory.write_checkin(conn, "evening", "received", "", structured={"missed_checkin": True})
    u = resp.usage
    print(
        f"evening sent ({len(replies)} replies) | tokens in={u.input_tokens} out={u.output_tokens} "
        f"cache_read={u.cache_read_input_tokens} cache_write={u.cache_creation_input_tokens}"
    )


if __name__ == "__main__":
    load_dotenv()
    run_guarded("evening", main)
