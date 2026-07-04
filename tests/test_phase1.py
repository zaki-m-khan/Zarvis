from src import db, memory, scoreboard
from src.models import CheckIn
from src.tools.telegram import BUTTON_TO_FIELD, _extract_updates


def test_checkin_model():
    c = CheckIn(gym=True, outreach=5)
    assert c.has_data()
    assert not CheckIn().has_data()
    dumped = {k: v for k, v in c.model_dump().items() if v is not None}
    assert dumped == {"gym": True, "outreach": 5}


def test_button_callbacks_extracted_with_allowlist():
    updates = [
        {"update_id": 1, "callback_query": {"from": {"id": 111}, "data": "gym"}},
        {"update_id": 2, "callback_query": {"from": {"id": 999}, "data": "gym"}},   # stranger
        {"update_id": 3, "callback_query": {"from": {"id": 111}, "data": "bogus"}},  # unknown button
        {"update_id": 4, "message": {"chat": {"id": 111}, "text": "sent 5 outreach"}},
    ]
    texts, taps = _extract_updates(updates, 111)
    assert texts == ["sent 5 outreach"]
    assert taps == ["gym"]
    assert BUTTON_TO_FIELD["gym"] == {"gym": True}


def test_scoreboard_tally():
    conn = db.connect(":memory:")
    memory.write_checkin(conn, "evening", "received", "[button] gym", structured={"gym": True})
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"outreach": 5, "steps": 9000})
    memory.write_checkin(conn, "evening", "received", "[parsed]", structured={"outreach": 3, "clay": True})
    memory.write_checkin(conn, "evening", "received", "", structured={"missed_checkin": True})  # no metric keys

    values = scoreboard.tally_week(conn)
    assert values["outreach"] == 8
    assert values["lifts"] == 1       # one distinct gym day
    assert values["clay"] == 1
    assert values["steps"] == 9000
    assert values["milestone"] == 0

    # upserted into scoreboard table for the dashboard later
    rows = conn.execute("SELECT metric, value, target FROM scoreboard").fetchall()
    assert ("outreach", 8.0, 25.0) in rows

    summary = scoreboard.week_summary_text(conn)
    assert "outreach: 8/25" in summary
