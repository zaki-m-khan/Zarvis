# CLAUDE.md — Project Handoff & Working Guide

This file is the complete context for continuing this project in a fresh Claude Code session. Read it fully before making changes. The full product spec is [JARVIS_BUILD.md](JARVIS_BUILD.md); the user's life plan (also the agent's memory) is [memory/plan.md](memory/plan.md).

## What this project is

**Jarvis/ZARVIS** — Zaki Khan's summer accountability system, and his flagship resume project (goal: PM/AI roles, class of 2027). Two parts:

1. **`/` (repo root) — the agent.** A Python Telegram bot that messages Zaki twice daily: a 7:00 AM ET nudge naming his real calendar blocks, and a 9:00 PM ET check-in that ingests his replies + button taps into SQLite and auto-tallies a weekly scoreboard. Runs serverless on GitHub Actions cron. LLM: `gpt-5.4-mini` via OpenAI API (~$0.0025/message; Zaki has ~$5 in OpenAI credits, budget is <$5/month).
2. **`dashboard/` — the ZARVIS HUD.** A Vite + React sci-fi dashboard (Iron-Man-JARVIS aesthetic), faithfully implemented from a claude.ai/design export. Currently displays **hardcoded demo data** — wiring it to the real SQLite data is a planned next step. Run with `npm install && npm run dev` inside `dashboard/`.

## Current status (verified live as of July 3, 2026)

- ✅ **Phase 0 complete** (spec §8): bot live (@ZARVISv1_bot), morning + evening runs verified end-to-end on Zaki's phone, GitHub Actions cron firing at 11:00/01:00 UTC, all failures fail-loud to Telegram.
- ✅ **Phase 1 complete**: free-text replies parsed into a Pydantic `CheckIn` (gym/outreach/calls/clay/steps/weight/milestone), inline keyboard buttons on the evening message (tap = structured log), weekly scoreboard auto-tallied from the `checkins` table into the `scoreboard` table.
- ✅ **Google Calendar read** connected (pulled forward from Phase 2): OAuth done locally, reads two calendars — `primary` + `zmk227@lehigh.edu` (where the recurring blocks live), merged and time-sorted. Falls back to the hardcoded weekly template on any failure.
- ✅ Tests: `pytest tests/` — 6 tests covering schema, allowlist, calendar fallback, CheckIn model, button extraction, scoreboard tally.

## Architecture (deliberately boring — see spec §11 rules)

```
GitHub Actions cron (11:00 & 01:00 UTC)
  └─ python -m src.runs.morning | evening   (plain loop, no framework yet)
       ├─ src/memory.py      loads memory/*.md (system prompt) + last-7-days checkins (SQL)
       ├─ src/tools/calendar.py  Google Calendar read-only → template fallback
       ├─ src/tools/telegram.py  send (with inline buttons) / getUpdates polling, chat_id allowlist
       ├─ src/llm.py         provider switch: OPENAI_API_KEY → gpt-5.4-mini, else claude-haiku-4-5
       │                     compose() = the message; parse_checkin() = replies → CheckIn JSON
       ├─ src/scoreboard.py  re-tallies week from checkins (json_extract), upserts scoreboard table
       └─ src/runs/guard.py  90s timeout + crash → plain-text Telegram error (fail loud)
SQLite (jarvis.db): checkins, scoreboard, kv (telegram offset). Persisted between cloud runs via actions/cache.
```

**Key decisions already made (don't relitigate):**
- Plain Python loop now; LangGraph refactor is Phase 2 in the spec ("boring before clever").
- SQL-first memory, no RAG/embeddings until an eval proves the need (spec §5).
- Provider switch lives in `src/llm.py` only — one file to change models.
- Calendar is read-only; write access (via MCP) is deferred.
- Costs stay near zero: free tiers, cheap model, prompt prefix kept byte-stable for caching (memory files first in system prompt, no timestamps there).

## Secrets & machine-local files (NOT in git — must be transferred manually)

| File / secret | Where it is now | Needed for |
|---|---|---|
| `.env` | Zaki's machine, repo root | local runs — contains `OPENAI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (8749623890), `GOOGLE_CALENDAR_CREDENTIALS_JSON=./credentials.json`, `GOOGLE_CALENDAR_IDS=primary,zmk227@lehigh.edu`, `DATABASE_PATH=./jarvis.db` |
| `credentials.json` | Zaki's machine | Google OAuth client (desktop app) |
| `token.json` | Zaki's machine | cached Google consent — copy it, or re-run any run locally to redo the browser flow |
| GitHub repo secrets | github.com/zaki-m-khan/Zarvis → Settings → Actions | `OPENAI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` are set. **`GOOGLE_TOKEN_JSON` (= contents of token.json) is still MISSING** — until added, cloud runs use the template fallback instead of real calendar. |

New machine setup: clone repo → `python -m venv .venv` → `pip install -r requirements.txt` → copy `.env` + `credentials.json` + `token.json` from old machine (or recreate per README checklist) → `pytest tests/` → `python -m src.runs.morning` should put a message on Zaki's phone.

## Known caveats

- **Polling latency (by design, v1):** button taps and replies are ingested at the *next* scheduled run, not instantly. The bot cannot hold a conversation yet — that's the webhook phase.
- **DST:** cron times are UTC; after November DST they fire 1hr early ET (comment in cron.yml).
- **Two databases exist:** the local `jarvis.db` (from testing) and the cloud one in GitHub Actions cache. The cloud one is the real one going forward. Dashboard wiring must decide the single source of truth (see roadmap).
- **Double-count edge:** two parsed text check-ins in one day both reporting outreach are summed (accepted for v1).
- **Windows console:** printing emoji from calendar events crashes cp1252 — use `PYTHONIOENCODING=utf-8` for debug scripts (runtime code never prints event names).

## Roadmap (in order — next step first)

1. **Dashboard wiring** (what Zaki wants next): replace hardcoded values in `dashboard/src/App.jsx` (`renderVals()`) with real data — scoreboard panel ← `scoreboard` table, comms feed ← `checkins`, weight ← parsed weigh-ins. Needs a small API or db-sync step; the clean long-term answer is the same as #2:
2. **Phase 3 — always-on host (Railway) + Telegram webhook**: real-time conversation ("what's on my schedule Monday?" should get an answer), kills polling latency, gives the dashboard a live backend + persistent db in one move. Spec also wants the Sunday 4:30 PM summarizer run and the facts.md consolidation gate (append durable facts only with Zaki's yes/no button approval).
3. **Phase 2 leftovers**: LangGraph refactor (proper graph, tool nodes, conditional END edges).
4. **Phase 4 — LLM ops**: Langfuse tracing, LLM-as-judge eval (`evals/rubric.md` seed is in spec §9), ship a measured prompt v2, bump `PROMPT_VERSION`.
5. **Phase 5 — multi-user**: users table, per-user memory files, SQLite → Supabase, onboard Muz + 1–2 friends. This is what makes it a product.

## Working agreements (from the spec + user preferences)

- v-next ships small and fast; cut scope, not sleep (spec §11). Demo acceptance criteria before starting the next phase.
- Every scheduled run must fail loud to Telegram — silence is the worst failure mode.
- Keep per-message token usage visible (each run prints it) and monthly cost under $5.
- Zaki is a student, technical but new to harness engineering — explain architectural decisions plainly, flag security footguns proactively (he has pasted secrets into tracked files twice; check `.env.example` and `git status` before every commit/push).
- The user prefers to be asked before big scope changes, but wants autonomous execution of agreed plans.

## The user (for message-tone context, not code)

Zaki Khan — EY intern in NYC summer 2026, cutting to ~157 lbs, recruiting for PM/AI roles (Clay is target #1), building this in Tue/Thu evening build blocks and Sunday deep-work sprints. The agent's voice spec is [memory/personality.md](memory/personality.md): direct, hype-coach, ≤6 lines, one ask max, respects event days.
