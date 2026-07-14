"""LLM calls, provider by env var: OPENAI_API_KEY -> gpt-5.4-mini, else ANTHROPIC_API_KEY -> claude-haiku-4-5.

The provider switch lives in THIS file only (CLAUDE.md key decision) — both the
raw compose/parse calls and the LangChain chat model used by src/agent.py.
"""
import json
import os

OPENAI_MODEL = "gpt-5.4-mini"
ANTHROPIC_MODEL = "claude-haiku-4-5"


def get_chat_model():
    """LangChain chat model for the agent graph. Same provider switch as compose()."""
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL, max_completion_tokens=4000)
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=ANTHROPIC_MODEL, max_tokens=1000)


def compose(system_blocks: list[dict], user_text: str) -> tuple[str, str]:
    """Returns (message_text, usage_line). system_blocks is the Anthropic-style block list from prompts.py."""
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI

        # OpenAI caches stable prompt prefixes >=1024 tokens automatically — no markers needed.
        system_text = "\n\n".join(b["text"] for b in system_blocks)
        resp = OpenAI().chat.completions.create(
            model=OPENAI_MODEL,
            max_completion_tokens=4000,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
        )
        u = resp.usage
        cached = u.prompt_tokens_details.cached_tokens if u.prompt_tokens_details else 0
        return (
            resp.choices[0].message.content.strip(),
            f"{OPENAI_MODEL} in={u.prompt_tokens} out={u.completion_tokens} cached={cached}",
        )

    import anthropic

    resp = anthropic.Anthropic().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_text}],
    )
    u = resp.usage
    return (
        "".join(b.text for b in resp.content if b.type == "text").strip(),
        f"{ANTHROPIC_MODEL} in={u.input_tokens} out={u.output_tokens} "
        f"cache_read={u.cache_read_input_tokens} cache_write={u.cache_creation_input_tokens}",
    )


PARSE_PROMPT = (
    "Extract today's accountability data from Zaki's Telegram replies below. "
    "Return ONLY a JSON object with these keys (null when not mentioned): "
    "gym (bool, lift done), outreach (int, outreaches sent), calls (int, calls/chats booked), "
    "clay (bool, Clay table shipped), steps (int), weight (float, lbs), milestone (bool, project milestone hit).\n\n"
    "Replies:\n{replies}"
)


def json_call(prompt: str, max_tokens: int = 500) -> dict:
    """One-shot JSON-object completion on the cheap model (same provider switch). Returns {} on failure."""
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI

        resp = OpenAI().chat.completions.create(
            model=OPENAI_MODEL,
            max_completion_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content
    else:
        import anthropic

        resp = anthropic.Anthropic().messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in resp.content if b.type == "text")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}


def parse_checkin(replies: list[str]):
    """Parse free-text replies into a CheckIn. Returns None when nothing parseable."""
    from src.models import CheckIn

    data = json_call(PARSE_PROMPT.format(replies="\n".join(f"- {r}" for r in replies)))
    try:
        checkin = CheckIn.model_validate(data)
        return checkin if checkin.has_data() else None
    except Exception:
        return None


FACTS_PROMPT = (
    "Below is one week of accountability check-ins between Jarvis and {name}. "
    "Propose AT MOST 3 durable facts about {name} worth remembering permanently — patterns, "
    "preferences, recurring obstacles (e.g. 'consistently skips Thursday build blocks after long "
    "work days'). Only facts likely to still be true next month. If nothing durable emerged, "
    "return an empty list. Return ONLY a JSON object: {{\"facts\": [\"...\"]}}\n\n"
    "Week log:\n{log}"
)


def propose_facts(name: str, week_log: str) -> list[str]:
    """Sunday consolidation: distill the week into <=3 proposed durable facts."""
    facts = json_call(FACTS_PROMPT.format(name=name, log=week_log)).get("facts", [])
    return [str(f).strip() for f in facts if str(f).strip()][:3]
