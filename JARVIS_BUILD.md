# JARVIS — Agentic Accountability System (Build Spec v1)

**Owner:** Zaki Khan · **Started:** July 2026
**One-liner:** A harnessed AI agent that checks in with me twice a day over Telegram, knows my summer plan and my history, nudges me toward my weekly scoreboard, and improves its own prompts through an eval loop.

This document is the starting brief for Claude Code. Read it fully before writing code. Build in phases; do not skip ahead.

---

## 1. Why This Exists (Success Criteria)

1. **It works on me.** Morning nudge + evening check-in every day, and my weekly scoreboard completion goes up because of it.
2. **It teaches harness engineering.** The build must genuinely exercise: agent loops with end-loop guardrails, a three-part memory system (procedural / semantic / episodic), tool calling, tracing, and LLM-as-judge evals.
3. **It becomes a shippable product.** By August, 2–3 friends onboarded as real users (multi-user via chat_id). This is the flagship resume project.

**Anti-goals:** No web dashboard (yet). No vector database until a real question demands semantic search. No feature that delays v0 past week one.

---

## 2. Architecture (the Harness)

```
cron (7:00 AM / 9:00 PM ET)
      │
      ▼
┌─────────────────────────────┐
│  JARVIS AGENT LOOP           │
│  Claude API (LangGraph)      │
│  end-loop guard: msg sent    │
│  hard rail: max 5 tool calls │
└──────┬───────────────┬──────┘
       │               │
   MEMORY           TOOLS
   ├ procedural     ├ read_calendar (Google Calendar API)
   │  (md files)    ├ read/write_scoreboard (SQLite)
   ├ semantic       ├ send_message (Telegram)
   │  (facts.md+db) └ read_replies (Telegram getUpdates)
   └ episodic
      (SQLite log)
       │
       ▼
   LLM OPS (weekly)
   traces (Langfuse) → eval (LLM as judge) → ship prompt v2 ↻
```

Two agent runs per day:
- **Morning run (7:00 AM):** read today's calendar blocks + last 7 days of episodic log + procedural files → compose one short, personality-driven nudge message → send → **STOP** (guard: message sent).
- **Evening run (9:00 PM):** pull my replies since last run → interpret free text, log structured button data → update scoreboard tallies → send check-in with inline keyboard buttons → **STOP**.
- **Sunday run (4:30 PM):** summarizer agent — consolidate the week's episodic log into a drafted weekly review (scoreboard tally, green/red, one observation, one suggestion) → send before my 5:00 PM review block.

---

## 3. Stack (decided — don't relitigate)

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python 3.12 | |
| Agent framework | LangGraph | Graph = the loop. Conditional edge to END = the guardrail. Prior experience from agent-prospector. |
| LLM | Claude API (claude-sonnet-4-6) | Cheap model OK for summarizer agent |
| Structured output | Pydantic | Check-in schema, judge scores |
| DB | SQLite (v0–v3) → Supabase (multi-user) | |
| Messaging | Telegram Bot API | Raw HTTP via `requests`; no heavy SDK |
| Scheduler | GitHub Actions cron (v0) → Railway worker (webhook phase) | |
| Tracing/evals | Langfuse (free cloud tier) | |
| Calendar | Google Calendar API, read-only scope | zakikhan.contact@gmail.com |

---

## 4. Repo Structure

```
jarvis/
├── README.md
├── JARVIS_BUILD.md            # this file
├── memory/
│   ├── plan.md                # procedural — the summer plan (copy of SUMMER_PLAN.md)
│   ├── personality.md         # procedural — how Jarvis talks
│   └── facts.md               # semantic — durable facts about Zaki
├── src/
│   ├── agent.py               # LangGraph graph: nodes, edges, end-loop guards
│   ├── prompts.py             # system prompts, versioned (PROMPT_VERSION constant)
│   ├── memory.py              # load md files, episodic read/write, retrieval (SQL-first)
│   ├── tools/
│   │   ├── telegram.py        # send_message, read_replies, inline keyboards
│   │   ├── calendar.py        # read today's events
│   │   └── scoreboard.py      # tally + query the 6 weekly metrics
│   ├── runs/
│   │   ├── morning.py         # entrypoint: python -m src.runs.morning
│   │   ├── evening.py
│   │   └── sunday.py          # summarizer agent
│   └── db.py                  # SQLite schema + connection
├── evals/
│   ├── judge.py               # LLM-as-judge scoring of sent messages
│   └── rubric.md              # what "good" means
├── .github/workflows/cron.yml # scheduled runs
├── .env.example
└── tests/
```

---

## 5. Memory Design

**Procedural** (`memory/*.md`, loaded into every run's system prompt):
- `plan.md` — the full summer plan (goals, scoreboard, blocks, rules)
- `personality.md` — voice spec. Draft: direct, a little funny, zero corporate fluff, hype-coach energy, calls out skipped blocks without guilt-tripping, short messages (morning ≤ 6 lines), never sends walls of text. Uses my slang sparingly. Respects event days (weddings = no grind messaging).
- `facts.md` — semantic seed: name, school, EY context, targets (1,750 cal / 160–180g protein / 25 outreach/wk), Clay ritual, key dates, halal, target companies list.

**Episodic** (SQLite):
```sql
CREATE TABLE checkins (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,              -- ISO timestamp
  run_type TEXT NOT NULL,        -- morning | evening | sunday | adhoc
  direction TEXT NOT NULL,       -- sent | received
  raw_text TEXT,                 -- message content or user reply
  structured JSON                -- parsed: {"gym": true, "outreach": 3, ...}
);

CREATE TABLE scoreboard (
  week_start TEXT,               -- Monday date
  metric TEXT,                   -- outreach|calls|clay|lifts|steps|milestone
  value REAL,
  target REAL,
  PRIMARY KEY (week_start, metric)
);

CREATE TABLE users (             -- phase 5, multi-user
  chat_id INTEGER PRIMARY KEY,
  name TEXT,
  plan_path TEXT,
  active INTEGER DEFAULT 1
);
```

**Retrieval rule (from the harness video, keep it):** SQL-first. "Last 7 days of check-ins" is a query, not a RAG problem. No embeddings/vector store unless a phase-4 eval shows the agent failing on fuzzy-history questions.

**Consolidation gate:** Sunday summarizer distills the week into 3–5 bullet facts; anything durable ("Zaki consistently skips Thursday build blocks after long EY days") gets appended to `facts.md` — with my approval via a Telegram yes/no button, never silently.

---

## 6. Telegram Integration

- Create bot via @BotFather → `TELEGRAM_TOKEN`. Get my `chat_id` via `getUpdates`.
- **Security rail (non-negotiable):** hard allowlist on `chat_id`. Ignore all other senders. Never put token/chat_id in code — env vars / GitHub secrets only.
- v0–v2: polling (`getUpdates` with offset persistence) at the start of each cron run.
- Phase 3+: webhook on Railway for real-time replies.
- Evening check-ins use **inline keyboard buttons** for the 6 metrics (tap = structured data, zero typing friction). Free-text replies always accepted and interpreted by the agent for context.

## 7. End-Loop Guardrails (write these as code, not vibes)

1. Terminal state: `message_sent == True` → END.
2. Hard rail: `tool_calls > 5` in one run → send fallback message ("check-in logged, had trouble with tools — tell me manually?") → END.
3. Timeout: run > 90 seconds → fallback → END.
4. No-reply handling: if evening replies are empty, log `missed_checkin`, do NOT re-ping more than once per run.
5. All failures fail loud: exception → plain-text Telegram error message to me. Silence is the worst failure mode for an accountability bot.

---

## 8. Build Phases (maps to calendar build blocks)

### Phase 0 — v0 "It's Alive" (Week of Jul 6: Tue 7/7, Thu 7/9, Sun 7/12)
- [ ] Repo scaffold, BotFather setup, `.env`, secrets in GitHub
- [ ] `send_message()` working from local machine
- [ ] Morning run: load `plan.md` + `facts.md` → Claude composes nudge from today's *hardcoded* block list → sends
- [ ] GitHub Actions cron firing at 7:00 AM & 9:00 PM ET (mind UTC offset)
- [ ] Evening run: `getUpdates` polling, replies logged raw to SQLite
- **Acceptance: I receive a real morning nudge on my phone by Sunday Jul 12, generated by Claude, not a template.**

### Phase 1 — Memory (week of Jul 13)
- [ ] Episodic log feeding last-7-days into morning prompt
- [ ] Pydantic `CheckIn` schema; agent parses free-text replies into it
- [ ] Inline keyboard buttons for evening check-in
- [ ] Scoreboard table auto-tallying from check-ins
- **Acceptance: Jarvis references something I told it yesterday, unprompted.**

### Phase 2 — Tools (week of Jul 20; light week — wedding Thu/Fri)
- [ ] Google Calendar read-only tool → morning nudge lists *actual* blocks
- [ ] LangGraph refactor: proper graph with tool nodes + conditional END edges + guardrails from §7
- **Acceptance: I move an event in Google Calendar and the next morning nudge reflects it.**

### Phase 3 — Sunday Summarizer + Webhook (week of Jul 27)
- [ ] Sunday 4:30 PM summarizer run drafting my weekly review
- [ ] Deploy worker to Railway; switch polling → webhook; ad-hoc conversation works mid-day
- [ ] Consolidation gate → `facts.md` appends with approval button
- **Acceptance: Sunday review takes me <15 min because the draft is waiting.**

### Phase 4 — LLM Ops (weeks of Aug 3–10)
- [ ] Langfuse tracing on every run (prompt, tool calls, tokens, latency)
- [ ] `evals/judge.py`: LLM-as-judge scores each sent message 1–5 on rubric (brevity, specificity, personality-match, actionability) + weekly correlation check: check-in compliance vs. green metrics
- [ ] Ship prompt v2 based on eval results; bump `PROMPT_VERSION`; document the diff in README
- **Acceptance: one measured, eval-justified prompt improvement shipped.**

### Phase 5 — Users (mid-Aug)
- [ ] `users` table; per-user plan/personality/facts files; migrate SQLite → Supabase
- [ ] Onboard Muz (his gym/nutrition plan already exists) + 1–2 others
- [ ] Simple onboarding: new user messages bot → Jarvis interviews them → generates their plan.md draft
- **Acceptance: 3 active users, 2 weeks of retention. Now it's a product.**

---

## 9. Eval Rubric Seed (`evals/rubric.md`)

A good Jarvis message: (1) ≤ 6 lines in the morning, (2) names today's specific blocks/times, (3) references at least one thing from episodic memory when relevant, (4) matches personality.md voice, (5) ends with exactly one clear ask or zero asks — never three questions. Judge scores 1–5 per dimension; weekly avg < 3.5 on any dimension = prompt iteration required.

## 10. Env Vars

```
ANTHROPIC_API_KEY=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
GOOGLE_CALENDAR_CREDENTIALS_JSON=   # read-only OAuth or service account
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
DATABASE_PATH=./jarvis.db
PROMPT_VERSION=v1
```

## 11. Rules for the Build (Claude Code: enforce these)

1. **v0 ships in week one.** If a task doesn't serve that, defer it.
2. Every phase has acceptance criteria — demo them before starting the next phase.
3. SQL before RAG. Files before databases. Polling before webhooks. Boring before clever.
4. The scheduled runs must never crash silently — every failure notifies via Telegram.
5. Keep costs near zero: free tiers only; cheap model for the summarizer.
6. This project supports the summer plan; it never preempts the recruiting block or the gym. If a build session runs long, cut scope, not sleep.
