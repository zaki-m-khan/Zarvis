"""FastAPI backend (Phase 3): Telegram webhook, scheduled-run endpoints, dashboard API.

Runs on Render free tier; GitHub Actions cron curls /api/run/* on schedule.
Auth:
  - /webhook/telegram: X-Telegram-Bot-Api-Secret-Token must equal TELEGRAM_WEBHOOK_SECRET
  - /api/run/*:        X-Run-Token must equal RUN_TOKEN
  - /api/state, /api/chat: X-Dash-Token (or ?token=) must equal DASH_TOKEN
Start locally:  uvicorn src.server:app --reload --port 8787
"""
import asyncio
import hmac
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src import agent, db, llm, memory, onboarding, prompts, scoreboard, tracing
from src.models import CheckIn
from src.runs import evening, morning, sunday
from src.tools import calendar, telegram
from src.tools.telegram import BUTTON_TO_FIELD

load_dotenv()
app = FastAPI(title="ZARVIS", docs_url=None, redoc_url=None)

RUN_FNS = {"morning": morning.main, "evening": evening.main, "sunday": sunday.main}
AGENT_TIMEOUT_S = 90  # §7.3


def _check(token_env: str, provided: str | None) -> None:
    expected = os.environ.get(token_env, "")
    if not expected or not provided or not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=403, detail="forbidden")


def _conversation_history(conn, chat_id: int, limit: int = 8) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT direction, raw_text FROM checkins WHERE chat_id = ? AND raw_text != '' "
        "AND raw_text NOT LIKE '[%' ORDER BY id DESC LIMIT ?",
        (chat_id, limit),
    ).fetchall()
    return [("assistant" if d == "sent" else "user", t) for d, t in reversed(rows)]


def _ingest_text(conn, chat_id: int, text: str) -> None:
    """Log raw + best-effort structured parse (webhook-era real-time ingestion)."""
    memory.write_checkin(conn, "adhoc", "received", text, chat_id=chat_id)
    parsed: CheckIn | None = llm.parse_checkin([text])
    if parsed:
        memory.write_checkin(
            conn, "adhoc", "received", "[parsed]",
            structured={k: v for k, v in parsed.model_dump().items() if v is not None},
            chat_id=chat_id,
        )


async def _agent_reply(conn, user: dict, text: str) -> str:
    """Conversational reply with the §7.3 timeout as code."""
    history = _conversation_history(conn, user["chat_id"])
    try:
        reply, _ = await asyncio.wait_for(
            asyncio.to_thread(agent.run_agent, conn, user, text, history),
            timeout=AGENT_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        reply = "That took me too long to think about — try me again in a minute?"
    return reply


@app.get("/healthz")
def healthz():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


# ---------- Telegram webhook ----------

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    _check("TELEGRAM_WEBHOOK_SECRET", request.headers.get("X-Telegram-Bot-Api-Secret-Token"))
    update = await request.json()
    conn = db.connect()
    try:
        memory.seed_default_user(conn)

        cq = update.get("callback_query")
        if cq:
            chat_id = cq.get("from", {}).get("id")
            data = cq.get("data", "")
            telegram.answer_callback(cq.get("id", ""))
            if data in BUTTON_TO_FIELD:  # evening check-in buttons
                memory.write_checkin(conn, "evening", "received", f"[button] {data}",
                                     structured=BUTTON_TO_FIELD[data], chat_id=chat_id)
            elif data.startswith(("fact_yes:", "fact_no:")):  # consolidation gate
                status = "approved" if data.startswith("fact_yes:") else "rejected"
                conn.execute("UPDATE facts SET status = ? WHERE id = ? AND chat_id = ?",
                             (status, int(data.split(":")[1]), chat_id))
                conn.commit()
                telegram.send_message("Saved to memory. 🧠" if status == "approved" else "Dropped.", chat_id=chat_id)
            else:
                onboarding.handle_callback(conn, chat_id, data)
            return {"ok": True}

        msg = update.get("message") or {}
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        if not chat_id or not text:
            return {"ok": True}

        user = db.get_user(conn, chat_id)
        if user and user.get("active"):
            _ingest_text(conn, chat_id, text)
            reply = await _agent_reply(conn, user, text)
            telegram.send_message(reply, chat_id=chat_id)
            memory.write_checkin(conn, "adhoc", "sent", reply, chat_id=chat_id)
        else:
            name = msg.get("chat", {}).get("first_name", "")
            onboarding.handle_message(conn, chat_id, name, text)  # silent when gate closed
        return {"ok": True}
    finally:
        conn.close()


# ---------- scheduled runs (GitHub Actions cron curls these) ----------

@app.post("/api/run/{run_type}")
async def api_run(run_type: str, request: Request):
    _check("RUN_TOKEN", request.headers.get("X-Run-Token"))
    fn = RUN_FNS.get(run_type)
    if not fn:
        raise HTTPException(status_code=404, detail=f"unknown run type {run_type}")
    try:
        await asyncio.wait_for(asyncio.to_thread(fn), timeout=180)
        return {"ok": True, "run": run_type}
    except Exception as e:
        # fail loud (§7.5): the run itself Telegrams errors via guard paths; surface here too
        try:
            telegram.send_message(f"Jarvis {run_type} run failed on the server: {e}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


# ---------- dashboard API ----------

def _dash_auth(request: Request) -> None:
    _check("DASH_TOKEN", request.headers.get("X-Dash-Token") or request.query_params.get("token"))


@app.get("/api/state")
async def api_state(request: Request):
    _dash_auth(request)
    conn = db.connect()
    try:
        user = memory.seed_default_user(conn)
        chat_id = user["chat_id"]
        targets = user.get("targets") or scoreboard.TARGETS
        values = scoreboard.tally_week(conn, chat_id, targets=targets)

        comms_rows = conn.execute(
            "SELECT ts, direction, raw_text FROM checkins WHERE chat_id = ? AND raw_text != '' "
            "AND raw_text NOT LIKE '[%' ORDER BY id DESC LIMIT 12",
            (chat_id,),
        ).fetchall()
        comms = [
            {"who": "ZARVIS" if d == "sent" else (user.get("name") or "YOU").upper(),
             "time": ts[11:16], "ts": ts, "text": t}
            for ts, d, t in reversed(comms_rows)
        ]

        weight_rows = conn.execute(
            "SELECT ts, structured FROM checkins WHERE chat_id = ? AND structured IS NOT NULL ORDER BY ts",
            (chat_id,),
        ).fetchall()
        weights = []
        for ts, s in weight_rows:
            w = json.loads(s).get("weight")
            if w is not None:
                weights.append({"ts": ts[:10], "weight": float(w)})

        blocks, source = await asyncio.to_thread(calendar.get_today_events)
        last_run = db.kv_get(conn, f"last_run:{chat_id}")
        checkin_count = conn.execute(
            "SELECT COUNT(*) FROM checkins WHERE chat_id = ?", (chat_id,)
        ).fetchone()[0]

        return {
            "user": user.get("name"),
            "week_start": scoreboard.week_start(),
            "scoreboard": {m: {"value": values[m], "target": float(targets.get(m, scoreboard.TARGETS[m]))}
                           for m in scoreboard.TARGETS},
            "comms": comms,
            "weights": weights,
            "blocks": [{"time": t, "name": n} for t, n in blocks],
            "blocks_source": source,
            "last_run": json.loads(last_run) if last_run else None,
            "checkin_count": checkin_count,
            "active_users": len(db.active_users(conn)),
            "prompt_version": prompts.PROMPT_VERSION,
            "model": llm.active_model(),
            "langfuse": tracing.enabled(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        conn.close()


@app.post("/api/chat")
async def api_chat(request: Request):
    _dash_auth(request)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")
    conn = db.connect()
    try:
        user = memory.seed_default_user(conn)
        _ingest_text(conn, user["chat_id"], text)
        reply = await _agent_reply(conn, user, text)
        memory.write_checkin(conn, "adhoc", "sent", reply, chat_id=user["chat_id"])
        return {"reply": reply}
    finally:
        conn.close()


# ---------- static dashboard (vite build) ----------

DIST = os.path.join(os.path.dirname(__file__), "..", "dashboard", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(DIST, "index.html"))
else:
    @app.get("/")
    def index_dev():
        return JSONResponse({"zarvis": "backend up — dashboard build missing (run vite build)"})
