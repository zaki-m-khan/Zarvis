"""LangGraph agent loop — spec §2/§7: tool nodes, conditional END edges, guardrails as code.

Every composed message (morning / evening / sunday / ad-hoc conversation) goes
through this graph. Guardrails:
  1. Terminal state: the model answers without tool calls -> END (message composed).
  2. Hard rail: > MAX_TOOL_CALLS tool calls in one run -> canned fallback -> END.
  3. Timeout (90s) stays in src/runs/guard.py / the server's asyncio timeout.
"""
import json
from datetime import date as date_cls
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src import db, llm, memory, scoreboard, tracing
from src.tools import calendar

MAX_TOOL_CALLS = 5
FALLBACK_TEXT = "Check-in logged, but I had trouble with my tools just now — tell me the numbers manually?"


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tools_used: int


def _make_tools(conn, user: dict) -> dict[str, dict]:
    """Tool registry closed over (conn, user). name -> {schema, fn}."""
    chat_id = user["chat_id"]
    is_owner = chat_id == db.default_chat_id()

    def read_calendar(date: str = "") -> str:
        """Read calendar blocks for a date (YYYY-MM-DD) or today when empty."""
        if not is_owner:
            return "No external calendar connected for this user — use the blocks in their plan."
        target = date_cls.fromisoformat(date) if date else None
        blocks, source = calendar.get_events(target)
        label = date or "today"
        lines = "\n".join(f"- {t} — {n}" for t, n in blocks) or "- (none)"
        return f"Blocks for {label} (source: {source}):\n{lines}"

    def read_scoreboard() -> str:
        """Read this week's scoreboard tally."""
        return scoreboard.week_summary_text(conn, chat_id, targets=user.get("targets"))

    def log_checkin(
        gym: bool | None = None,
        outreach: int | None = None,
        calls: int | None = None,
        clay: bool | None = None,
        steps: int | None = None,
        weight: float | None = None,
        milestone: bool | None = None,
    ) -> str:
        """Log structured accountability data the user just reported (only fields they mentioned)."""
        structured = {
            k: v
            for k, v in dict(gym=gym, outreach=outreach, calls=calls, clay=clay,
                             steps=steps, weight=weight, milestone=milestone).items()
            if v is not None
        }
        if not structured:
            return "Nothing to log."
        memory.write_checkin(conn, "adhoc", "received", "[tool:log_checkin]", structured=structured, chat_id=chat_id)
        return f"Logged: {structured}. " + scoreboard.week_summary_text(conn, chat_id, targets=user.get("targets"))

    return {
        "read_calendar": {
            "fn": read_calendar,
            "schema": {
                "name": "read_calendar",
                "description": "Read calendar blocks for a date (YYYY-MM-DD) or today when date is empty.",
                "parameters": {"type": "object", "properties": {"date": {"type": "string"}}, "required": []},
            },
        },
        "read_scoreboard": {
            "fn": read_scoreboard,
            "schema": {
                "name": "read_scoreboard",
                "description": "Read this week's accountability scoreboard tally.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        "log_checkin": {
            "fn": log_checkin,
            "schema": {
                "name": "log_checkin",
                "description": "Log structured accountability data the user just reported. Only pass fields they explicitly mentioned.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gym": {"type": "boolean"}, "outreach": {"type": "integer"},
                        "calls": {"type": "integer"}, "clay": {"type": "boolean"},
                        "steps": {"type": "integer"}, "weight": {"type": "number"},
                        "milestone": {"type": "boolean"},
                    },
                    "required": [],
                },
            },
        },
    }


def _build_graph(model_with_tools, tools: dict):
    def agent_node(state: AgentState):
        resp = model_with_tools.invoke(state["messages"])
        return {"messages": [resp]}

    def tools_node(state: AgentState):
        last: AIMessage = state["messages"][-1]
        out = []
        for call in last.tool_calls:
            entry = tools.get(call["name"])
            try:
                result = entry["fn"](**call["args"]) if entry else f"Unknown tool {call['name']}"
            except Exception as e:  # a broken tool must not kill the run — fail soft, agent recovers
                result = f"Tool error: {e}"
            out.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        return {"messages": out, "tools_used": state["tools_used"] + len(last.tool_calls)}

    def limit_node(state: AgentState):
        # Hard rail (§7.2): answer for the user WITHOUT the model — tools are misbehaving.
        return {"messages": [AIMessage(content=FALLBACK_TEXT)]}

    def route(state: AgentState):
        last = state["messages"][-1]
        if not getattr(last, "tool_calls", None):
            return END  # §7.1 terminal state: message composed
        if state["tools_used"] + len(last.tool_calls) > MAX_TOOL_CALLS:
            return "limit"
        return "tools"

    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tools_node)
    g.add_node("limit", limit_node)
    g.set_entry_point("agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", "limit": "limit", END: END})
    g.add_edge("tools", "agent")
    g.add_edge("limit", END)
    return g.compile()


def run_agent(
    conn,
    user: dict,
    user_text: str,
    history: list[tuple[str, str]] | None = None,
    callbacks: list | None = None,
) -> tuple[str, int]:
    """One agent run -> (reply_text, tools_used).

    history: optional [(role, text)] turns ('user'/'assistant') for conversational context.
    callbacks: optional LangChain callbacks (Langfuse tracing).
    """
    mem = memory.load_memory(conn, user)
    system_text = (
        f"You are Jarvis, {user.get('name') or 'the user'}'s accountability agent on Telegram. "
        "Follow the personality spec exactly.\n\n"
        + mem["personality"] + "\n\n" + mem["facts"] + "\n\n" + mem["plan"]
    )
    tools = _make_tools(conn, user)
    model = llm.get_chat_model().bind_tools([t["schema"] for t in tools.values()])
    graph = _build_graph(model, tools)

    messages: list = [SystemMessage(content=system_text)]
    for role, text in history or []:
        messages.append(HumanMessage(content=text) if role == "user" else AIMessage(content=text))
    messages.append(HumanMessage(content=user_text))

    config = {"recursion_limit": 25}
    all_callbacks = (callbacks or []) + tracing.callbacks()
    if all_callbacks:
        config["callbacks"] = all_callbacks
    final = graph.invoke({"messages": messages, "tools_used": 0}, config=config)
    reply = final["messages"][-1].content
    if isinstance(reply, list):  # anthropic content blocks
        reply = "".join(b.get("text", "") for b in reply if isinstance(b, dict))
    return (reply or FALLBACK_TEXT).strip(), final["tools_used"]
