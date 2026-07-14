"""Step B tests: graph guardrails (terminal state, hard rail, tool errors fail soft) with a fake model."""
from langchain_core.messages import AIMessage

from src import agent, db, memory


class FakeModel:
    """Scripted model: returns queued responses in order."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return self.responses.pop(0)


def _user(conn, chat_id=111):
    db.upsert_user(conn, chat_id, name="Test", active=1, state="active",
                   plan_md="plan", personality_md="direct", facts_md="facts")
    return db.get_user(conn, chat_id)


def _run(conn, user, model):
    tools = agent._make_tools(conn, user)
    graph = agent._build_graph(model, tools)
    final = graph.invoke({"messages": [], "tools_used": 0}, config={"recursion_limit": 25})
    return final


def test_terminal_state_no_tools(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    user = _user(conn)
    model = FakeModel([AIMessage(content="Morning. Three blocks today.")])
    final = _run(conn, user, model)
    assert final["messages"][-1].content == "Morning. Three blocks today."
    assert final["tools_used"] == 0 and model.calls == 1


def test_tool_call_then_answer(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    user = _user(conn)
    model = FakeModel([
        AIMessage(content="", tool_calls=[{"name": "log_checkin", "args": {"outreach": 5}, "id": "c1"}]),
        AIMessage(content="Logged 5 outreach. Green is close."),
    ])
    final = _run(conn, user, model)
    assert final["tools_used"] == 1
    # tool actually wrote to the db
    rows = conn.execute("SELECT structured FROM checkins WHERE chat_id = 111").fetchall()
    assert rows and "outreach" in rows[0][0]


def test_hard_rail_max_tool_calls(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    user = _user(conn)
    # model keeps demanding tools forever -> rail must cut it off with the fallback
    model = FakeModel([
        AIMessage(content="", tool_calls=[{"name": "read_scoreboard", "args": {}, "id": f"x{i}"}])
        for i in range(6)
    ])
    final = _run(conn, user, model)
    assert final["messages"][-1].content == agent.FALLBACK_TEXT
    assert final["tools_used"] <= agent.MAX_TOOL_CALLS


def test_tool_error_fails_soft(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    user = _user(conn)
    model = FakeModel([
        AIMessage(content="", tool_calls=[{"name": "read_calendar", "args": {"date": "not-a-date"}, "id": "c1"}]),
        AIMessage(content="Couldn't read that date, but here's the plan."),
    ])
    final = _run(conn, user, model)
    tool_msgs = [m for m in final["messages"] if m.type == "tool"]
    assert "Tool error" in tool_msgs[0].content  # exception surfaced to the model, run survived
    assert final["messages"][-1].content.startswith("Couldn't")


def test_non_owner_calendar_redirects_to_plan(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111")
    conn = db.connect(":memory:")
    friend = _user(conn, chat_id=222)
    tools = agent._make_tools(conn, friend)
    out = tools["read_calendar"]["fn"]()
    assert "plan" in out.lower() and "no external calendar" in out.lower()
