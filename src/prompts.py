"""System prompts, versioned. Keep system blocks byte-stable — no timestamps here (prompt caching).

v2 (2026-07-14, eval-justified): judge on v1 history scored specificity lowest
(4.33) with notes "could include exact time or history for stronger grounding"
— v2 requires one exact scoreboard number, one exact block time, and one
episodic reference when relevant, and pins the evening ask to a number.
"""

PROMPT_VERSION = "v2"


def system_blocks(mem: dict[str, str]) -> list[dict]:
    """Memory files as system blocks; cache_control on the last (biggest) block caches the whole prefix."""
    return [
        {
            "type": "text",
            "text": (
                "You are Jarvis, Zaki Khan's accountability agent. You message him on Telegram "
                "twice a day. Follow the personality spec exactly.\n\n" + mem["personality"]
            ),
        },
        {"type": "text", "text": mem["facts"]},
        {"type": "text", "text": mem["plan"], "cache_control": {"type": "ephemeral"}},
    ]


def _format_blocks(blocks: list[tuple[str, str]], source: str) -> str:
    lines = [f"- {time} — {name}" for time, name in blocks]
    label = "from Google Calendar" if source == "google" else "from the weekly template (calendar not connected)"
    return f"Today's blocks ({label}):\n" + ("\n".join(lines) if lines else "- (none)")


def _format_recent(recent: list[tuple[str, str, str, str]]) -> str:
    if not recent:
        return "No check-in history yet (this is a fresh start)."
    lines = [f"- [{ts[:16]}] {run_type}/{direction}: {text}" for ts, run_type, direction, text in recent]
    return "Last 7 days of check-ins:\n" + "\n".join(lines[-30:])


def morning_prompt(today_str: str, blocks: list[tuple[str, str]], source: str, recent: list, board: str = "") -> str:
    return (
        f"It is {today_str}, 7:00 AM. Compose this morning's nudge (max 6 lines).\n\n"
        f"{_format_blocks(blocks, source)}\n\n"
        f"{board}\n\n"
        f"{_format_recent(recent)}\n\n"
        "Be specific: cite at least one exact scoreboard number (e.g. 14/25) and one exact block time. "
        "If the last 7 days contain something relevant, reference it once — Jarvis remembers. "
        "Write ONLY the Telegram message text, nothing else."
    )


def evening_prompt(
    today_str: str, blocks: list[tuple[str, str]], source: str, replies: list[str], recent: list, board: str = ""
) -> str:
    replies_str = (
        "Zaki's replies since the last run:\n" + "\n".join(f"- {r}" for r in replies)
        if replies
        else "Zaki sent no replies since the last run (note it once, don't guilt-trip)."
    )
    return (
        f"It is {today_str}, 9:00 PM. Compose tonight's check-in message.\n\n"
        f"{_format_blocks(blocks, source)}\n\n"
        f"{replies_str}\n\n"
        f"{board}\n\n"
        f"{_format_recent(recent)}\n\n"
        "Ask about today's blocks and anything the scoreboard is missing (numbers like outreach count, "
        "steps, weight come from his typed replies; the buttons under your message log gym/steps/Clay/milestone). "
        "Cite exact scoreboard numbers, not vibes. End with exactly ONE ask, and make it concrete with a "
        "number (e.g. 'how many outreaches went out?'). "
        "Write ONLY the Telegram message text, nothing else."
    )
