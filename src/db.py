"""Storage layer (JARVIS_BUILD.md §5), dual-driver in this one file.

DATABASE_URL=postgres://... -> psycopg (Supabase in prod).
Otherwise DATABASE_PATH / :memory: -> sqlite3 (local dev + tests).

All SQL in the codebase uses `?` placeholders; the Conn wrapper rewrites to `%s`
for Postgres. Keep every dialect difference HERE — nowhere else.
"""
import json
import os
import sqlite3

DEFAULT_TZ = "America/New_York"


def default_chat_id() -> int:
    """Single-user compatibility: Zaki's chat_id from env (0 in tests without env)."""
    return int(os.environ.get("TELEGRAM_CHAT_ID", "0"))


class Conn:
    """Thin wrapper so sqlite3 and psycopg connections look identical to callers."""

    def __init__(self, raw, is_pg: bool):
        self.raw = raw
        self.is_pg = is_pg

    def execute(self, sql: str, params=()):
        if self.is_pg:
            # psycopg treats % as a placeholder marker, so escape literal % first
            # (some queries use LIKE '[%'), THEN translate our ?-style to %s.
            sql = sql.replace("%", "%%").replace("?", "%s")
        return self.raw.execute(sql, params)

    def commit(self) -> None:
        self.raw.commit()

    def close(self) -> None:
        self.raw.close()


# id column is the only piece of DDL that differs by dialect.
def _schema(auto_id: str) -> list[str]:
    return [
        f"""CREATE TABLE IF NOT EXISTS checkins (
              id {auto_id},
              chat_id BIGINT DEFAULT 0,
              ts TEXT NOT NULL,
              run_type TEXT NOT NULL,
              direction TEXT NOT NULL,
              raw_text TEXT,
              structured TEXT
            )""",
        """CREATE TABLE IF NOT EXISTS scoreboard (
              chat_id BIGINT DEFAULT 0,
              week_start TEXT,
              metric TEXT,
              value REAL,
              target REAL,
              PRIMARY KEY (chat_id, week_start, metric)
            )""",
        """CREATE TABLE IF NOT EXISTS kv (
              key TEXT PRIMARY KEY,
              value TEXT
            )""",
        """CREATE TABLE IF NOT EXISTS users (
              chat_id BIGINT PRIMARY KEY,
              name TEXT,
              active INTEGER DEFAULT 0,
              state TEXT DEFAULT 'new',
              plan_md TEXT,
              personality_md TEXT,
              facts_md TEXT,
              targets TEXT,
              tz TEXT DEFAULT 'America/New_York',
              interview TEXT
            )""",
        f"""CREATE TABLE IF NOT EXISTS facts (
              id {auto_id},
              chat_id BIGINT,
              ts TEXT,
              fact TEXT,
              status TEXT DEFAULT 'proposed'
            )""",
        f"""CREATE TABLE IF NOT EXISTS evals (
              id {auto_id},
              checkin_id BIGINT,
              chat_id BIGINT,
              ts TEXT,
              brevity REAL,
              specificity REAL,
              personality REAL,
              actionability REAL,
              notes TEXT,
              prompt_version TEXT
            )""",
    ]


def _migrate_legacy_sqlite(conn: Conn) -> None:
    """Pre-multi-user local dbs: add chat_id to checkins; rebuild scoreboard (derived table)."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(checkins)").fetchall()]
    if cols and "chat_id" not in cols:
        conn.execute("ALTER TABLE checkins ADD COLUMN chat_id BIGINT DEFAULT 0")
        conn.execute("UPDATE checkins SET chat_id = ?", (default_chat_id(),))
    sb_cols = [r[1] for r in conn.execute("PRAGMA table_info(scoreboard)").fetchall()]
    if sb_cols and "chat_id" not in sb_cols:
        conn.execute("DROP TABLE scoreboard")  # recomputed from checkins on next tally
        conn.execute(
            """CREATE TABLE scoreboard (
                 chat_id BIGINT DEFAULT 0, week_start TEXT, metric TEXT, value REAL, target REAL,
                 PRIMARY KEY (chat_id, week_start, metric))"""
        )
    conn.commit()


def connect(path: str | None = None) -> Conn:
    """Connect + ensure schema. `path` overrides env (tests pass ':memory:')."""
    url = os.environ.get("DATABASE_URL", "") if path is None else ""
    if url.startswith(("postgres://", "postgresql://")):
        import psycopg

        raw = psycopg.connect(url, autocommit=False)
        # Supabase transaction pooler (pgbouncer, :6543) can't keep server-side
        # prepared statements across transactions — disable psycopg auto-prepare.
        raw.prepare_threshold = None
        conn = Conn(raw, is_pg=True)
        for stmt in _schema("BIGSERIAL PRIMARY KEY"):
            conn.execute(stmt)
        conn.commit()
        return conn

    db_path = path or os.environ.get("DATABASE_PATH", "./jarvis.db")
    # check_same_thread=False: the server hands each request's connection to a
    # worker thread (asyncio.to_thread) — one connection per request, used
    # sequentially, so this is safe.
    raw = sqlite3.connect(db_path, check_same_thread=False)
    conn = Conn(raw, is_pg=False)
    # Legacy check BEFORE create-if-not-exists so old scoreboard shape is detected.
    _migrate_legacy_sqlite(conn)
    for stmt in _schema("INTEGER PRIMARY KEY"):
        conn.execute(stmt)
    conn.commit()
    return conn


def kv_get(conn: Conn, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def kv_set(conn: Conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO kv (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


# ---------- users ----------

def get_user(conn: Conn, chat_id: int) -> dict | None:
    row = conn.execute(
        "SELECT chat_id, name, active, state, plan_md, personality_md, facts_md, targets, tz, interview "
        "FROM users WHERE chat_id = ?",
        (chat_id,),
    ).fetchone()
    if not row:
        return None
    keys = ("chat_id", "name", "active", "state", "plan_md", "personality_md", "facts_md", "targets", "tz", "interview")
    user = dict(zip(keys, row))
    user["targets"] = json.loads(user["targets"]) if user["targets"] else None
    user["interview"] = json.loads(user["interview"]) if user["interview"] else None
    return user


def upsert_user(conn: Conn, chat_id: int, **fields) -> None:
    """Insert or update a user. Only the given fields change; dict/list values are JSON-encoded."""
    encoded = {
        k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in fields.items()
    }
    cols = ", ".join(encoded)
    placeholders = ", ".join("?" for _ in encoded)
    updates = ", ".join(f"{k} = excluded.{k}" for k in encoded)
    conn.execute(
        f"INSERT INTO users (chat_id, {cols}) VALUES (?, {placeholders}) "
        f"ON CONFLICT(chat_id) DO UPDATE SET {updates}",
        (chat_id, *encoded.values()),
    )
    conn.commit()


def active_users(conn: Conn) -> list[dict]:
    rows = conn.execute("SELECT chat_id FROM users WHERE active = 1 ORDER BY chat_id").fetchall()
    return [get_user(conn, r[0]) for r in rows]
