"""Morning run (7:00 AM ET): compose one nudge -> send -> log -> STOP."""
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
    mem = memory.load_memory()
    blocks, source = calendar.get_today_events()
    recent = memory.recent_checkins(conn, days=7)
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %d, %Y")

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=prompts.system_blocks(mem),
        messages=[{"role": "user", "content": prompts.morning_prompt(today_str, blocks, source, recent)}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    telegram.send_message(text)
    memory.write_checkin(conn, "morning", "sent", text)
    u = resp.usage
    print(
        f"morning sent ({source} blocks) | tokens in={u.input_tokens} out={u.output_tokens} "
        f"cache_read={u.cache_read_input_tokens} cache_write={u.cache_creation_input_tokens}"
    )


if __name__ == "__main__":
    load_dotenv()
    run_guarded("morning", main)
