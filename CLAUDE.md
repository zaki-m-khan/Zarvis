# CLAUDE.md — Project Handoff & Working Guide

This file is the complete context for continuing this project in a fresh Claude Code session. Read it fully before making changes. The full product spec is [JARVIS_BUILD.md](JARVIS_BUILD.md); the user's life plan (also the agent's memory) is [memory/plan.md](memory/plan.md).

## What this project is

**Jarvis/ZARVIS** — Zaki Khan's summer accountability system, and his flagship resume project (goal: PM/AI roles, class of 2027). Now Phase 5, deployed. Two parts, one always-on service:

1. **the agent** (`src/`). A Python Telegram bot that messages Zaki twice daily (7:00 AM nudge, 9:00 PM check-in) plus a Sunday 4:30 PM weekly review. Runs through a **LangGraph** loop (`src/agent.py`) with tool nodes + coded guardrails. Real-time conversation via Telegram **webhook** (no more polling latency). LLM: `gpt-5.4-mini` via OpenAI (provider switch in `src/llm.py` only). Multi-user: friends self-onboard.
2. **the ZARVIS HUD** (`dashboard/`). Vite + React sci-fi dashboard, now **wired to live data** via `GET /api/state` (poll) and `POST /api/chat` (the Comms panel talks to the real agent). Falls back to demo values only when the API is unreachable.

Both are served by one **FastAPI** app (`src/server.py`) on Render, backed by **Supabase Postgres**. GitHub Actions cron is now just the scheduler (curls the run endpoints).

## Current status (deployed & verified live, July 14, 2026)

- ✅ **Live in production:** https://zarvis.onrender.com (Render free) + Supabase Postgres + GitHub Actions cron. Full history migrated (40 real check-ins Jul 4–14). Morning run, real-time webhook, and the GitHub-Actions→Render cron path all verified end-to-end on Zaki's phone.
- ✅ **Phase 0–1** (unchanged): bot, `CheckIn` parsing, inline buttons, weekly scoreboard.
- ✅ **Phase 2:** `src/agent.py` LangGraph graph — agent⇄tool nodes (`read_calendar`, `read_scoreboard`, `log_checkin`), conditional END edge (reply composed → END), **hard rail >5 tool calls → fallback → END**, 90s timeout.
- ✅ **Phase 3:** FastAPI webhook (real-time chat + buttons + fact-approval), `/api/run/{morning|evening|sunday}`, `src/runs/sunday.py` weekly review + **consolidation gate** (≤3 proposed facts, ✅/❌ buttons; facts enter memory only on approval, stored in the `facts` table since Render's disk is ephemeral).
- ✅ **Phase 4:** optional Langfuse tracing (`src/tracing.py`), `evals/judge.py` LLM-as-judge (4 dims) + `evals/rubric.md`, **prompt v2 shipped** (`PROMPT_VERSION="v2"`, specificity 4.33→sample 5.0, documented in README).
- ✅ **Phase 5:** `users`/`facts`/`evals` tables, per-user memory + targets, `src/onboarding.py` self-serve interview → drafted plan → approve buttons (gated by `ONBOARDING_OPEN`, default off).
- ✅ Tests: `pytest tests/` — **26 tests** (storage/dual-driver, agent guardrails, server routing/auth, onboarding, evals).

## Architecture

```
GitHub Actions cron ──curl /api/run/{type}──▶ Render web service (FastAPI, src/server.py)
  11:00 / 01:00 / Sun 20:30 UTC   (X-Run-Token)   ├─ POST /webhook/telegram  real-time chat/buttons/onboarding
                                                   ├─ GET /api/state · POST /api/chat  (X-Dash-Token)
Telegram ──webhook──▶ /webhook/telegram            ├─ serves dashboard/dist (the HUD)
                                                   └─ src/agent.py  LangGraph: agent⇄tools, ≤5 calls, END guards
                                                          │ src/memory.py (per-user md+DB facts), llm.py (provider switch),
                                                          │ tools/calendar.py (Google→template), tools/telegram.py, scoreboard.py
                                                   Supabase Postgres  (DATABASE_URL; SQLite when unset — local/tests)
                                                     checkins · scoreboard · kv · users · facts · evals
```

**Key decisions already made (don't relitigate):**
- `src/db.py` is dual-driver: `DATABASE_URL=postgres://…` → psycopg (escapes `%`→`%%`, disables auto-prepare for the Supabase transaction pooler), else SQLite. All SQL uses `?` placeholders; the shim rewrites for PG. **Keep every dialect difference in db.py.**
- Scoreboard tallies in **Python** (`src/scoreboard.py`), not SQL — runs identically on both drivers.
- Provider switch lives in `src/llm.py` only (`get_chat_model` for the graph, `compose`/`json_call` for raw calls).
- Durable facts live in the `facts` table, not `facts.md` (ephemeral disk); the md files seed Zaki's user row.
- Costs near zero: Render free + Supabase free + GH Actions. Cold starts (~50s) accepted; cron doubles as a waker.

## Secrets & machine-local files (NOT in git — must be transferred manually)

| File / secret | Where | Notes |
|---|---|---|
| `.env` | Zaki's machine, `jarvis/` | local runs (SQLite). `OPENAI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (8749623890), `GOOGLE_CALENDAR_*`, `DATABASE_PATH=./jarvis.db`. Leave `DATABASE_URL` unset locally to use SQLite. |
| `credentials.json`, `token.json` | Zaki's machine | Google OAuth client + cached consent. |
| **Render** env (dashboard → Environment) | render.com service `zarvis` | `DATABASE_URL` (Supabase pooler), `OPENAI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`, `RUN_TOKEN`, `DASH_TOKEN`, `WEBHOOK_MODE=1`, `LANGFUSE_*` (+ `LANGFUSE_HOST` US). Blueprint: `render.yaml` (non-secrets baked in). |
| **GitHub** Actions secrets | repo → Settings → Actions | `OPENAI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `GOOGLE_TOKEN_JSON`, **`RENDER_URL`, `RUN_TOKEN`** (set 2026-07-14 — cron curls Render with these). |

Tokens generated 2026-07-14 (webhook secret / RUN_TOKEN / DASH_TOKEN) live in Render + GitHub only — never committed. Dashboard access: `https://zarvis.onrender.com/?key=<DASH_TOKEN>` (stored in localStorage).

## Pending manual item (needs Zaki's Google login — can't be automated)

**Google Calendar token is expired/revoked** → `/api/state` shows `blocks_source: template`. Diagnosed 2026-07-14: `GOOGLE_TOKEN_JSON` IS set correctly on Render, but the refresh token (minted Jul 3) is dead — `invalid_grant: Token has been expired or revoked`. Root cause: the OAuth consent screen is in **"Testing"** status, and Google expires those refresh tokens after 7 days (died ~Jul 10; the real→template switch is visible in the message history). Two-step fix:
1. `python -m scripts.reauth_google` → browser consent → fresh `token.json`; paste the printed JSON into Render `GOOGLE_TOKEN_JSON` (auto-redeploys).
2. **Permanent:** Google Cloud Console → OAuth consent screen → **Publish app / "In production"** so refresh tokens stop dying every 7 days.

Everything else is done (Langfuse verified live on Render, `langfuse: true`). Non-blocking: template blocks are correct for the current fixed schedule.

## Known caveats

- **DST:** cron times are UTC; after November DST they fire 1hr early ET (comment in cron.yml).
- **Cold starts:** Render free spins down after idle (~50s first hit); Telegram retries + the cron waker cover it.
- **Fixed 6 metric slots** for all users (targets per-user) in onboarding v1.
- **Double-count edge:** two text check-ins in one day both reporting outreach are summed (accepted for v1).
- **Windows debug:** `PYTHONIOENCODING=utf-8` for scripts that print emoji (cp1252 crash). Local server needs `check_same_thread=False` (set) since requests run on worker threads.

## Roadmap (phases 0–5 done; what's next)

1. **Turn on onboarding** (`ONBOARDING_OPEN=1` on Render) and onboard Muz + 1–2 friends — the "it's a product" milestone. Interview flow is built and tested; just gated off.
2. **Weekly eval loop as a habit:** run `python -m evals.judge` after a week of v2 messages; if any dimension avg < 3.5, iterate to v3 (bump `PROMPT_VERSION`, document in README).
3. **Calendar write** (via MCP) — deferred; currently read-only.
4. Polish: real weight-logging habit lights up the Cut Trajectory (currently DEMO until a weigh-in is logged); consider per-user metric sets beyond the fixed 6.

## Working agreements (from the spec + user preferences)

- v-next ships small and fast; cut scope, not sleep (spec §11). Demo acceptance criteria before starting the next phase.
- Every scheduled run must fail loud to Telegram — silence is the worst failure mode.
- Keep per-message token usage visible (each run prints it) and monthly cost under $5.
- Zaki is a student, technical but new to harness engineering — explain architectural decisions plainly, flag security footguns proactively (he has pasted secrets into tracked files twice; check `.env.example` and `git status` before every commit/push).
- The user prefers to be asked before big scope changes, but wants autonomous execution of agreed plans.

## The user (for message-tone context, not code)

Zaki Khan — EY intern in NYC summer 2026, cutting to ~157 lbs, recruiting for PM/AI roles (Clay is target #1), building this in Tue/Thu evening build blocks and Sunday deep-work sprints. The agent's voice spec is [memory/personality.md](memory/personality.md): direct, hype-coach, ≤6 lines, one ask max, respects event days.
