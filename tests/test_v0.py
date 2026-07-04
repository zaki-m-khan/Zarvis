from datetime import datetime
from zoneinfo import ZoneInfo

from src import db, memory
from src.tools import calendar
from src.tools.telegram import _extract_messages


def test_schema_and_checkin_roundtrip():
    conn = db.connect(":memory:")
    memory.write_checkin(conn, "morning", "sent", "test nudge")
    rows = memory.recent_checkins(conn, days=1)
    assert len(rows) == 1
    assert rows[0][1] == "morning" and rows[0][3] == "test nudge"
    db.kv_set(conn, "tg_offset", "42")
    assert db.kv_get(conn, "tg_offset") == "42"


def test_allowlist_rejects_other_senders():
    updates = [
        {"update_id": 1, "message": {"chat": {"id": 111}, "text": "from zaki"}},
        {"update_id": 2, "message": {"chat": {"id": 999}, "text": "from stranger"}},
        {"update_id": 3, "message": {"chat": {"id": 111}}},  # no text (sticker etc.)
    ]
    assert _extract_messages(updates, 111) == ["from zaki"]


def test_calendar_fallback_template(monkeypatch):
    # No token.json / creds env -> _google_events raises -> template fallback, never raises.
    monkeypatch.delenv("GOOGLE_CALENDAR_CREDENTIALS_JSON", raising=False)
    monkeypatch.setattr(calendar, "TOKEN_PATH", "nonexistent-token.json")
    blocks, source = calendar.get_today_events()
    assert source == "template"

    # Template contents by weekday
    tue = datetime(2026, 7, 7, tzinfo=ZoneInfo("America/New_York"))
    names = [n for _, n in calendar.fallback_blocks(tue)]
    assert any("Recruiting" in n for n in names) and any("Build Block" in n for n in names)
    sat = datetime(2026, 7, 4, tzinfo=ZoneInfo("America/New_York"))
    assert calendar.fallback_blocks(sat) == [("ALL DAY", "Social / flex — guilt-free")]
