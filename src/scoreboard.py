"""Weekly scoreboard: recomputed from the checkins table (source of truth), upserted into scoreboard."""
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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


def tally_week(conn: sqlite3.Connection, now: datetime | None = None) -> dict[str, float]:
    """Recompute this week's metrics from structured checkins and upsert scoreboard rows."""
    ws = week_start(now)
    row = conn.execute(
        """
        SELECT
          COALESCE(SUM(json_extract(structured, '$.outreach')), 0),
          COALESCE(SUM(json_extract(structured, '$.calls')), 0),
          COALESCE(MAX(json_extract(structured, '$.clay')), 0),
          COUNT(DISTINCT CASE WHEN json_extract(structured, '$.gym') THEN date(ts) END),
          COALESCE(AVG(json_extract(structured, '$.steps')), 0),
          COALESCE(MAX(json_extract(structured, '$.milestone')), 0)
        FROM checkins
        WHERE structured IS NOT NULL AND date(ts) >= ?
        """,
        (ws,),
    ).fetchone()
    values = dict(zip(("outreach", "calls", "clay", "lifts", "steps", "milestone"), row))
    for metric, value in values.items():
        conn.execute(
            "INSERT INTO scoreboard (week_start, metric, value, target) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(week_start, metric) DO UPDATE SET value = excluded.value",
            (ws, metric, float(value), TARGETS[metric]),
        )
    conn.commit()
    return values


def week_summary_text(conn: sqlite3.Connection, now: datetime | None = None) -> str:
    values = tally_week(conn, now)
    parts = [f"{m}: {values[m]:g}/{TARGETS[m]}" for m in TARGETS]
    green = sum(1 for m in TARGETS if values[m] >= TARGETS[m])
    return f"Weekly scoreboard so far ({green}/6 hit): " + " · ".join(parts)
