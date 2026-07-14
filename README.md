# Jarvis — Agentic Accountability System

Telegram accountability agent for the summer lock-in plan, now Phase 5: LangGraph agent loop, real-time webhook conversation, multi-user self-serve onboarding, live ZARVIS dashboard, Langfuse tracing + LLM-as-judge evals. Spec: `JARVIS_BUILD.md`; working guide: `CLAUDE.md`.

**Model / cost:** provider is picked by env var — `OPENAI_API_KEY` set → `gpt-5.4-mini`; otherwise `claude-haiku-4-5`. Infra is $0/mo (Render free + Supabase free + GitHub Actions cron). LLM ≈ under $1/month single-user.

## Architecture (Phase 3+)

```
GitHub Actions cron ──curl──▶ Render free web service (FastAPI, src/server.py)
  11:00 UTC morning              ├─ POST /webhook/telegram   real-time chat + buttons + onboarding
  01:00 UTC evening              ├─ POST /api/run/{type}     X-Run-Token
  20:30 UTC sunday               ├─ GET /api/state · POST /api/chat   X-Dash-Token
                                 ├─ serves dashboard/dist (ZARVIS HUD)
                                 └─ src/agent.py  LangGraph: agent ⇄ tools, ≤5 calls, END guards
                                        │
                                 Supabase Postgres (DATABASE_URL) — SQLite when unset (local/tests)
```

## Run locally

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
pytest tests/                                     # 26 tests, no network
python -m src.runs.morning                        # one-off run (SQLite ./jarvis.db)
uvicorn src.server:app --port 8787                # backend (webhook + dashboard API)
cd dashboard && npm install && npm run dev        # HUD on :5173, proxies /api → :8787
```

Local dashboard auth: `dashboard/.env.local` with `VITE_DASH_TOKEN=<your DASH_TOKEN>`; in prod open `https://<app>/?key=<DASH_TOKEN>` once (stored in localStorage).

## Env vars

| Var | Purpose |
|---|---|
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | provider switch (src/llm.py, one file) |
| `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` | bot + owner chat id |
| `DATABASE_URL` | postgres:// → Supabase; unset → SQLite `DATABASE_PATH` |
| `TELEGRAM_WEBHOOK_SECRET` | must match setWebhook secret_token |
| `RUN_TOKEN`, `DASH_TOKEN` | auth for /api/run/* and /api/state,/api/chat |
| `GOOGLE_TOKEN_JSON` | contents of token.json (server has no disk) |
| `WEBHOOK_MODE=1` | skip getUpdates polling (server ingests in real time) |
| `ONBOARDING_OPEN=1` | let unknown senders onboard themselves (default: silence) |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | optional tracing (off when unset) |
| `PROMPT_VERSION` | stamped onto eval rows |

## Guardrails (coded, not vibes — spec §7)

- Terminal state: reply composed → END (`src/agent.py` conditional edge).
- Hard rail: >5 tool calls in one run → canned fallback → END.
- 90s timeout and any crash → plain-text Telegram error (fail loud, never silent).
- `chat_id` allowlist: unknown senders get silence unless `ONBOARDING_OPEN=1`.
- Sunday consolidation gate: proposed facts need an explicit ✅ button tap before entering memory.

## LLM ops (Phase 4)

```bash
python -m evals.judge            # score unscored sent messages 1–5 × 4 dims + report
python -m evals.judge --report   # report only
```

Rubric: `evals/rubric.md`. Iteration trigger: any dimension weekly avg < 3.5.

### Prompt v2 (2026-07-14, shipped)

Judge run on v1 history: brevity **5.00**, specificity **4.33**, personality 4.33, actionability 4.67 —
specificity weakest ("could include exact time or history for stronger grounding").
**v2 diff** (`src/prompts.py`): morning prompt now requires ≥1 exact scoreboard number + 1 exact block
time + 1 episodic reference when relevant; evening prompt pins the closing ask to a number.
Sample v2 message judged **5 / 5 / 5 / 5**. `PROMPT_VERSION = "v2"`.

## Multi-user (Phase 5)

Unknown sender messages the bot (gate open) → 4-question interview → LLM drafts their plan + weekly
targets → ✅ approve / 🔁 redo buttons → active. Runs iterate all active users with per-user memory,
personality, and targets. Owner keeps Google Calendar; friends' blocks come from their plan.
