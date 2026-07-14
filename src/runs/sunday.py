"""Sunday run (4:30 PM ET): weekly review draft + consolidation gate (spec §5, Phase 3).

Per active user:
1. Draft the weekly review (scoreboard tally, green/red, one observation, one
   suggestion) via the agent graph -> send before the 5:00 PM review block.
2. Consolidation gate: distill the week into <=3 durable facts, insert as
   'proposed', send each with ✅/❌ inline buttons. The webhook callback
   (fact_yes:<id> / fact_no:<id>) flips status — facts NEVER become memory
   silently.
"""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src import agent, db, llm, memory, scoreboard
from src.runs.guard import run_guarded
from src.tools import telegram

SUNDAY_PROMPT = (
    "It is {today}, 4:30 PM — time to draft {name}'s weekly review (their 5:00 PM review block is in 30 min).\n\n"
    "{board}\n\n"
    "Last 7 days of check-ins:\n{log}\n\n"
    "Write the weekly review draft as a Telegram message: each scoreboard metric with ✅ (hit) or ❌ (missed), "
    "whether this counts as a GREEN WEEK (5 of 6 metrics hit), exactly ONE observation about a pattern you "
    "noticed this week, and exactly ONE concrete suggestion for next week. Keep it tight — this should make "
    "the review take under 15 minutes. Write ONLY the message text."
)


def week_log_text(conn, chat_id: int) -> str:
    rows = memory.recent_checkins(conn, days=7, chat_id=chat_id)
    if not rows:
        return "(no check-ins this week)"
    return "\n".join(f"- [{ts[:16]}] {rt}/{d}: {txt}" for ts, rt, d, txt in rows[-60:])


def run_for_user(conn, user: dict) -> None:
    chat_id = user["chat_id"]
    board = scoreboard.week_summary_text(conn, chat_id, targets=user.get("targets"))
    log = week_log_text(conn, chat_id)
    today = datetime.now(ZoneInfo(user.get("tz") or "America/New_York")).strftime("%A, %B %d, %Y")

    review, tools_used = agent.run_agent(
        conn, user,
        SUNDAY_PROMPT.format(today=today, name=user.get("name") or "the user", board=board, log=log),
    )
    telegram.send_message(review, chat_id=chat_id)
    memory.write_checkin(conn, "sunday", "sent", review, chat_id=chat_id)

    # Consolidation gate — propose, never append silently.
    for fact in llm.propose_facts(user.get("name") or "the user", log):
        fact_id = conn.execute(
            "INSERT INTO facts (chat_id, ts, fact, status) VALUES (?, ?, ?, 'proposed') RETURNING id",
            (chat_id, datetime.now(timezone.utc).isoformat(), fact),
        ).fetchone()[0]
        conn.commit()
        telegram.send_message(
            f"Worth remembering permanently?\n\n“{fact}”",
            buttons=[[
                {"text": "✅ Save it", "callback_data": f"fact_yes:{fact_id}"},
                {"text": "❌ Drop it", "callback_data": f"fact_no:{fact_id}"},
            ]],
            chat_id=chat_id,
        )

    db.kv_set(conn, f"last_run:{chat_id}", json.dumps({
        "type": "sunday", "ts": datetime.now(timezone.utc).isoformat(), "tools_used": tools_used,
    }))
    print(f"sunday review sent to {chat_id} ({tools_used} tool calls)")


def main() -> None:
    conn = db.connect()
    memory.seed_default_user(conn)
    for user in db.active_users(conn):
        run_for_user(conn, user)


if __name__ == "__main__":
    load_dotenv()
    run_guarded("sunday", main)
