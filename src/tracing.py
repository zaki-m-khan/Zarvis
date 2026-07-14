"""Langfuse tracing (Phase 4). Fully optional: no keys in env -> no-op.

Set LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY (and LANGFUSE_HOST for the EU
region) and every agent graph run gets traced — prompts, tool calls, tokens,
latency — with zero code changes anywhere else.
"""
import os

_handler = None


def enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def callbacks() -> list:
    """LangChain callbacks for graph.invoke — [] when tracing is off."""
    global _handler
    if not enabled():
        return []
    if _handler is None:
        from langfuse.langchain import CallbackHandler

        _handler = CallbackHandler()
    return [_handler]


def flush() -> None:
    """Call at the end of short-lived runs so spans aren't lost on exit."""
    if _handler is not None:
        try:
            from langfuse import get_client

            get_client().flush()
        except Exception:
            pass
