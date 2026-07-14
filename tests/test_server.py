"""Steps C+D tests: webhook auth/routing, buttons, consolidation gate, onboarding, dashboard API."""
import json

import pytest
from fastapi.testclient import TestClient

from src import agent, db, llm, onboarding, server
from src.tools import telegram

SECRET = {"X-Telegram-Bot-Api-Secret-Token": "whsec"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "whsec")
    monkeypatch.setenv("RUN_TOKEN", "runtok")
    monkeypatch.setenv("DASH_TOKEN", "dashtok")
    monkeypatch.delenv("ONBOARDING_OPEN", raising=False)

    sent = []
    monkeypatch.setattr(telegram, "send_message",
                        lambda text, buttons=None, chat_id=None: sent.append((chat_id, text, buttons)))
    monkeypatch.setattr(telegram, "answer_callback", lambda *a, **k: None)
    monkeypatch.setattr(llm, "parse_checkin", lambda replies: None)
    monkeypatch.setattr(agent, "run_agent",
                        lambda conn, user, text, history=None, callbacks=None: ("agent says hi", 0))

    c = TestClient(server.app)
    c.sent = sent
    return c


def _msg(chat_id, text, name="Muz"):
    return {"message": {"chat": {"id": chat_id, "first_name": name}, "text": text}}


def test_webhook_rejects_bad_secret(client):
    assert client.post("/webhook/telegram", json=_msg(111, "yo")).status_code == 403
    assert client.post("/webhook/telegram", json=_msg(111, "yo"),
                       headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}).status_code == 403


def test_active_user_gets_agent_reply_and_ingestion(client):
    r = client.post("/webhook/telegram", json=_msg(111, "did my gym sesh"), headers=SECRET)
    assert r.status_code == 200
    assert client.sent[-1] == (111, "agent says hi", None)


def test_checkin_button_logs_structured(client):
    update = {"callback_query": {"id": "cb1", "from": {"id": 111}, "data": "gym"}}
    assert client.post("/webhook/telegram", json=update, headers=SECRET).status_code == 200
    conn = db.connect()
    rows = conn.execute("SELECT structured FROM checkins WHERE chat_id = 111 AND structured IS NOT NULL").fetchall()
    assert any(json.loads(r[0]).get("gym") for r in rows)


def test_fact_approval_gate(client):
    conn = db.connect()
    fact_id = conn.execute(
        "INSERT INTO facts (chat_id, ts, fact, status) VALUES (111, 't', 'skips thursdays', 'proposed') RETURNING id"
    ).fetchone()[0]
    conn.commit()
    update = {"callback_query": {"id": "cb2", "from": {"id": 111}, "data": f"fact_yes:{fact_id}"}}
    client.post("/webhook/telegram", json=update, headers=SECRET)
    conn2 = db.connect()
    assert conn2.execute("SELECT status FROM facts WHERE id = ?", (fact_id,)).fetchone()[0] == "approved"


def test_stranger_silence_when_gate_closed(client):
    before = len(client.sent)
    client.post("/webhook/telegram", json=_msg(999, "hey what is this"), headers=SECRET)
    assert len(client.sent) == before  # no reply at all — allowlist posture


def test_full_onboarding_flow(client, monkeypatch):
    monkeypatch.setenv("ONBOARDING_OPEN", "1")
    monkeypatch.setattr(llm, "json_call", lambda prompt, max_tokens=500: {
        "plan_md": "# Muz's Plan\n- gym 5x", "targets": {"lifts": 5, "steps": 9000}})

    client.post("/webhook/telegram", json=_msg(222, "hi"), headers=SECRET)          # welcome + Q1
    assert "1/4" in client.sent[-1][1]
    for i, ans in enumerate(["get shredded", "5 lifts, 9k steps", "gym M-F 6pm", "roast me"]):
        client.post("/webhook/telegram", json=_msg(222, ans), headers=SECRET)
    assert "plan draft" in client.sent[-1][1]
    assert client.sent[-1][2] == onboarding.APPROVAL_BUTTONS

    conn = db.connect()
    assert db.get_user(conn, 222)["state"] == "pending_approval"

    update = {"callback_query": {"id": "cb3", "from": {"id": 222}, "data": "onboard_yes"}}
    client.post("/webhook/telegram", json=update, headers=SECRET)
    u = db.get_user(db.connect(), 222)
    assert u["active"] == 1 and u["state"] == "active"
    assert u["targets"] == {"lifts": 5, "steps": 9000}
    assert "roast me" in u["personality_md"]
    assert "Locked in" in client.sent[-1][1]


def test_api_state_auth_and_shape(client):
    assert client.get("/api/state").status_code == 403
    r = client.get("/api/state", headers={"X-Dash-Token": "dashtok"})
    assert r.status_code == 200
    body = r.json()
    assert set(body["scoreboard"].keys()) == {"outreach", "calls", "clay", "lifts", "steps", "milestone"}
    assert all("value" in v and "target" in v for v in body["scoreboard"].values())
    assert "comms" in body and "weights" in body and "blocks" in body


def test_api_chat_roundtrip(client):
    r = client.post("/api/chat", json={"text": "status"}, headers={"X-Dash-Token": "dashtok"})
    assert r.status_code == 200 and r.json()["reply"] == "agent says hi"
    # both sides logged for the comms feed
    conn = db.connect()
    n = conn.execute("SELECT COUNT(*) FROM checkins WHERE raw_text IN ('status', 'agent says hi')").fetchone()[0]
    assert n == 2


def test_run_endpoint_auth(client, monkeypatch):
    monkeypatch.setitem(server.RUN_FNS, "morning", lambda: None)
    assert client.post("/api/run/morning").status_code == 403
    assert client.post("/api/run/morning", headers={"X-Run-Token": "runtok"}).status_code == 200
    assert client.post("/api/run/bogus", headers={"X-Run-Token": "runtok"}).status_code == 404
