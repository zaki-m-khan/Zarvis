# Jarvis — Agentic Accountability System (v0)

Telegram accountability agent for the summer lock-in plan. Morning nudge at 7:00 AM ET, evening check-in at 9:00 PM ET, composed from procedural memory (plan/personality/facts) + today's calendar blocks, logged to SQLite. Spec: `JARVIS_BUILD.md` in the parent folder.

**Model / cost:** provider is picked by env var — `OPENAI_API_KEY` set → `gpt-5.4-mini` ($0.75/M in, $4.50/M out); otherwise `claude-haiku-4-5` ($1/M in, $5/M out). ~65 single-call runs/month × ~12K input ≈ **under $1/month** on either; $5 of OpenAI credits ≈ 5–6 months. Each run prints token usage.

## Setup checklist

1. **Telegram bot:** message [@BotFather](https://t.me/BotFather) → `/newbot` → copy token into `.env` (`TELEGRAM_TOKEN`). Send your new bot any message, then run `python -m src.tools.telegram --whoami` and put your chat id in `.env` (`TELEGRAM_CHAT_ID`).
2. **Model key:** copy `.env.example` → `.env` and set `OPENAI_API_KEY` (uses gpt-5.4-mini) — or `ANTHROPIC_API_KEY` instead for Haiku.
3. **Google Calendar (optional):** GCP project → enable Calendar API → OAuth desktop-app credentials → save as `credentials.json`. First local run opens a browser once and caches `token.json`. Without this, Jarvis falls back to the weekly template blocks — v0 still works.
4. **Cron:** create a GitHub repo, push this folder, add repo secrets `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`), `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (optionally `GOOGLE_TOKEN_JSON` = contents of your local `token.json`). Test via Actions → jarvis-cron → Run workflow.

## Run locally

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
pytest tests/
python -m src.runs.morning
python -m src.runs.evening
```

## Guardrails (coded, not vibes)

- Terminal state: message sent → STOP.
- 90s timeout and any crash → plain-text Telegram error (fail loud, never silent).
- Hard `chat_id` allowlist — all other senders ignored.
- No reply in the evening → logged as `missed_checkin`, no re-ping.
