"""Weekly scoreboard: recomputed from the checkins table (source of truth), upserted into scoreboard.

Tally happens in Python (not SQL) so the same code runs on SQLite and Postgres.
Volume is a few rows/day — this is deliberate, not lazy (spec §11: boring before clever).
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src import db

ET = ZoneInfo("America/New_York")

TARGETS = {
    "outreach": 25,
    "calls": 3,
    "clay": 1,
    "lifts": 5,
    "steps": 10000,
    "milestone": 1,
}


def week_start(now: datetime | None = None) -> str:
    now = now or datetime.now(ET)
    monday = now.date() - timedelta(days=now.weekday())
    return monday.isoformat()


def tally_week(
    conn,
    chat_id: int | None = None,
    now: datetime | None = None,
    targets: dict | None = None,
) -> dict[str, float]:
    """Recompute this week's metrics from structured checkins and upsert scoreboard rows."""
    chat_id = db.default_chat_id() if chat_id is None else chat_id
    targets = targets or TARGETS
    ws = week_start(now)
    rows = conn.execute(
        "SELECT ts, structured FROM checkins "
        "WHERE structured IS NOT NULL AND ts >= ? AND chat_id = ?",
        (ws, chat_id),  # ISO timestamps: 'YYYY-MM-DD...' >= 'YYYY-MM-DD' string-compares correctly
    ).fetchall()

    outreach = calls = 0
    clay = milestone = 0
    gym_days: set[str] = set()
    step_readings: list[float] = []
    for ts, structured in rows:
        s = json.loads(structured)
        outreach += s.get("outreach") or 0
        calls += s.get("calls") or 0
        clay = max(clay, 1 if s.get("clay") else 0)
        milestone = max(milestone, 1 if s.get("milestone") else 0)
        if s.get("gym"):
            gym_days.add(ts[:10])
        if s.get("steps") is not None:
            step_readings.append(float(s["steps"]))

    values: dict[str, float] = {
        "outreach": float(outreach),
        "calls": float(calls),
        "clay": float(clay),
        "lifts": float(len(gym_days)),
        "steps": (sum(step_readings) / len(step_readings)) if step_readings else 0.0,
        "milestone": float(milestone),
    }
    for metric, value in values.items():
        conn.execute(
            "INSERT INTO scoreboard (chat_id, week_start, metric, value, target) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(chat_id, week_start, metric) DO UPDATE SET value = excluded.value, target = excluded.target",
            (chat_id, ws, metric, value, float(targets.get(metric, TARGETS[metric]))),
        )
    conn.commit()
    return values


def week_summary_text(
    conn, chat_id: int | None = None, now: datetime | None = None, targets: dict | None = None
) -> str:
    targets = targets or TARGETS
    values = tally_week(conn, chat_id, now, targets)
    parts = [f"{m}: {values[m]:g}/{targets.get(m, TARGETS[m]):g}" for m in TARGETS]
    green = sum(1 for m in TARGETS if values[m] >= targets.get(m, TARGETS[m]))
    return f"Weekly scoreboard so far ({green}/6 hit): " + " · ".join(parts)
