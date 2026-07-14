"""Phase 5: self-serve onboarding — a new user messages the bot, Jarvis interviews
them, drafts their plan, and activates them only after explicit ✅ approval.

State machine on users.state:
    (unknown)          -> welcome + Q1                    -> 'interviewing'
    'interviewing'     -> collect answers Q1..Q4          -> draft -> 'pending_approval'
    'pending_approval' -> ✅ onboard_yes -> 'active'
                       -> 🔁 onboard_redo + feedback      -> redraft -> 'pending_approval'

Gate: unknown senders are ignored entirely unless ONBOARDING_OPEN=1
(the chat_id allowlist stays the default security posture, spec §6).
"""
import json
import os

from src import db, llm, memory
from src.tools import telegram

QUESTIONS = [
    "1/4 — What are you locking in on? Give me your 1–3 big goals for the next ~8 weeks "
    "(e.g. 'cut to 157 lbs', 'land a PM internship', 'ship my app').",
    "2/4 — What weekly numbers would prove you're on track? Up to 6 measurable things with targets "
    "(e.g. '25 outreaches, 5 lifts, 10k steps/day, 1 project milestone').",
    "3/4 — What does your typical week look like? Named time blocks help "
    "(e.g. 'gym M–F 6:30pm, deep work Sun 10–2, class Tue/Thu').",
    "4/4 — How should I talk to you? (e.g. 'direct hype-coach, no fluff', 'gentle reminders', "
    "'roast me when I slack').",
]

DRAFT_PROMPT = (
    "You are drafting an accountability plan for a new user named {name} from their interview answers.\n\n"
    "Q&A:\n{qa}\n\n"
    "Return ONLY a JSON object with two keys:\n"
    "  \"plan_md\": a markdown plan (<= 40 lines): their goals, a weekly scoreboard of up to 6 metrics with "
    "targets, their weekly time blocks, and 3-5 rules in their own spirit.\n"
    "  \"targets\": an object mapping ONLY these keys to weekly numeric targets where the user's metrics fit: "
    "outreach (int/week), calls (int/week), clay (project deliverables/week), lifts (workouts/week), "
    "steps (daily average), milestone (milestones/week). Omit keys that don't apply.\n"
)

WELCOME = (
    "Hey — I'm Jarvis, an accountability agent. Twice a day I'll nudge you toward the plan WE design right now. "
    "Four quick questions and you're in.\n\n"
)

APPROVAL_BUTTONS = [[
    {"text": "✅ Lock it in", "callback_data": "onboard_yes"},
    {"text": "🔁 Change something", "callback_data": "onboard_redo"},
]]


def is_open() -> bool:
    return os.environ.get("ONBOARDING_OPEN", "0") == "1"


def _qa_text(answers: list[str]) -> str:
    return "\n".join(f"Q: {q}\nA: {a}" for q, a in zip(QUESTIONS, answers))


def _send_draft(conn, chat_id: int, name: str, answers: list[str], feedback: str | None = None) -> None:
    prompt = DRAFT_PROMPT.format(name=name, qa=_qa_text(answers))
    if feedback:
        prompt += f"\nThe user reviewed a previous draft and asked for this change: {feedback}\n"
    data = llm.json_call(prompt, max_tokens=1500)
    plan_md = data.get("plan_md") or "# Plan\n(draft failed — reply 'redo' to retry)"
    targets = {k: v for k, v in (data.get("targets") or {}).items() if k in
               ("outreach", "calls", "clay", "lifts", "steps", "milestone")}
    db.upsert_user(conn, chat_id, plan_md=plan_md, targets=targets or None, state="pending_approval")
    telegram.send_message(
        f"Here's your plan draft:\n\n{plan_md}\n\nLock it in, or tell me what to change.",
        buttons=APPROVAL_BUTTONS, chat_id=chat_id,
    )


def handle_message(conn, chat_id: int, name: str, text: str) -> bool:
    """Route a message from a non-active user. Returns True when handled."""
    user = db.get_user(conn, chat_id)

    if user is None or user.get("state") in (None, "new"):
        if not is_open():
            return False  # allowlist posture: strangers get silence
        db.upsert_user(conn, chat_id, name=name or "friend", state="interviewing",
                       interview={"answers": []}, active=0)
        telegram.send_message(WELCOME + QUESTIONS[0], chat_id=chat_id)
        return True

    state = user.get("state")
    if state == "interviewing":
        answers = (user.get("interview") or {}).get("answers", [])
        answers.append(text.strip())
        db.upsert_user(conn, chat_id, interview={"answers": answers})
        if len(answers) < len(QUESTIONS):
            telegram.send_message(QUESTIONS[len(answers)], chat_id=chat_id)
        else:
            telegram.send_message("Got everything. Drafting your plan — give me a few seconds…", chat_id=chat_id)
            _send_draft(conn, chat_id, user.get("name") or name or "friend", answers)
        return True

    if state == "pending_approval":
        # Free text at approval stage = change request -> redraft with feedback.
        answers = (user.get("interview") or {}).get("answers", [])
        telegram.send_message("On it — redrafting…", chat_id=chat_id)
        _send_draft(conn, chat_id, user.get("name") or name or "friend", answers, feedback=text)
        return True

    return False


def handle_callback(conn, chat_id: int, data: str) -> bool:
    """Handle onboard_yes / onboard_redo button taps. Returns True when handled."""
    if data not in ("onboard_yes", "onboard_redo"):
        return False
    user = db.get_user(conn, chat_id)
    if not user or user.get("state") != "pending_approval":
        return True  # stale button; swallow
    if data == "onboard_yes":
        files = memory.load_memory_files()
        answers = (user.get("interview") or {}).get("answers", [])
        personality = files["personality"]
        if len(answers) >= 4:  # Q4 = how they want to be talked to
            personality += f"\n\n## This user's tone preference (from onboarding)\n{answers[3]}\n"
        db.upsert_user(conn, chat_id, active=1, state="active",
                       personality_md=user.get("personality_md") or personality,
                       facts_md=user.get("facts_md") or f"# Facts about {user.get('name')}\n(learned over time)")
        telegram.send_message(
            "Locked in. 🤝 First nudge lands tomorrow 7:00 AM, check-in at 9:00 PM. "
            "You can message me any time — 'status', 'log gym', or just talk.",
            chat_id=chat_id,
        )
    else:
        telegram.send_message("What should change? Tell me and I'll redraft.", chat_id=chat_id)
    return True
