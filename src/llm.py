"""Single LLM call, provider by env var: OPENAI_API_KEY -> gpt-5.4-mini, else ANTHROPIC_API_KEY -> claude-haiku-4-5."""
import os

OPENAI_MODEL = "gpt-5.4-mini"
ANTHROPIC_MODEL = "claude-haiku-4-5"


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
