"""SQLite schema + connection (JARVIS_BUILD.md §5)."""
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  run_type TEXT NOT NULL,
  direction TEXT NOT NULL,
  raw_text TEXT,
  structured JSON
);

CREATE TABLE IF NOT EXISTS scoreboard (
  week_start TEXT,
  metric TEXT,
  value REAL,
  target REAL,
  PRIMARY KEY (week_start, metric)
);

CREATE TABLE IF NOT EXISTS kv (
  key TEXT PRIMARY KEY,
  value TEXT
);
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    db_path = path or os.environ.get("DATABASE_PATH", "./jarvis.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def kv_get(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def kv_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO kv (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
