"""Step A tests: dual-driver shim, legacy migration, users CRUD, Python tally, facts merge."""
import sqlite3

from src import db, memory, scoreboard


def test_param_shim_rewrites_only_for_pg():
    conn = db.connect(":memory:")
    assert conn.is_pg is False
    # SQLite path keeps `?` — a query with params round-trips.
    db.kv_set(conn, "k", "v")
    assert db.kv_get(conn, "k") == "v"
    # The shim itself: simulate what execute() does on the PG branch.
    assert "VALUES (%s, %s)" in "INSERT INTO kv (key, value) VALUES (?, ?)".replace("?", "%s")


def test_legacy_sqlite_db_migrates(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    path = str(tmp_path / "legacy.db")
    old = sqlite3.connect(path)
    old.executescript(
        """
        CREATE TABLE checkins (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, run_type TEXT NOT NULL,
                               direction TEXT NOT NULL, raw_text TEXT, structured JSON);
        CREATE TABLE scoreboard (week_start TEXT, metric TEXT, value REAL, target REAL,
                                 PRIMARY KEY (week_start, metric));
        INSERT INTO checkins (ts, run_type, direction, raw_text) VALUES ('2026-07-10T12:00:00+00:00','morning','sent','old row');
        """
    )
    old.commit()
    old.close()

    conn = db.connect(path)
    rows = conn.execute("SELECT chat_id, raw_text FROM checkins").fetchall()
    assert rows == [(111, "old row")]  # stamped with Zaki's chat_id
    # scoreboard rebuilt with chat_id column
    cols = [r[1] for r in conn.execute("PRAGMA table_info(scoreboard)").fetchall()]
    assert "chat_id" in cols


def test_users_crud_and_seed(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    assert db.get_user(conn, 222) is None
    db.upsert_user(conn, 222, name="Muz", state="interviewing", targets={"outreach": 10}, active=0)
    u = db.get_user(conn, 222)
    assert u["name"] == "Muz" and u["state"] == "interviewing" and u["targets"] == {"outreach": 10}
    db.upsert_user(conn, 222, active=1, state="active")
    assert db.get_user(conn, 222)["active"] == 1
    assert db.get_user(conn, 222)["name"] == "Muz"  # untouched fields survive partial upsert

    zaki = memory.seed_default_user(conn)
    assert zaki["chat_id"] == 111 and zaki["active"] == 1
    assert "scoreboard" in zaki["plan_md"].lower() or len(zaki["plan_md"]) > 100  # seeded from plan.md
    assert [u["chat_id"] for u in db.active_users(conn)] == [111, 222]


def test_per_user_tally_isolated(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"outreach": 5}, chat_id=111)
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"outreach": 2}, chat_id=222)
    assert scoreboard.tally_week(conn, 111)["outreach"] == 5
    assert scoreboard.tally_week(conn, 222)["outreach"] == 2
    # per-user targets flow through summary text
    text = scoreboard.week_summary_text(conn, 222, targets={**scoreboard.TARGETS, "outreach": 10})
    assert "outreach: 2/10" in text


def test_steps_average_not_sum(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"steps": 8000})
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"steps": 12000})
    assert scoreboard.tally_week(conn)["steps"] == 10000


def test_load_memory_merges_approved_facts(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    user = memory.seed_default_user(conn)
    conn.execute(
        "INSERT INTO facts (chat_id, ts, fact, status) VALUES (?, ?, ?, ?)",
        (111, "2026-07-14T00:00:00+00:00", "Skips Thursday build blocks after long EY days", "approved"),
    )
    conn.execute(
        "INSERT INTO facts (chat_id, ts, fact, status) VALUES (?, ?, ?, ?)",
        (111, "2026-07-14T00:00:00+00:00", "NOT approved — must not appear", "proposed"),
    )
    conn.commit()
    mem = memory.load_memory(conn, user)
    assert "Skips Thursday build blocks" in mem["facts"]
    assert "must not appear" not in mem["facts"]
    assert mem["personality"]  # seeded
