"""Telegram send/receive via raw HTTP. Hard chat_id allowlist — ignore all other senders."""
import os
import sqlite3

import requests

from src import db


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/{method}"


def _allowed_chat_id() -> int:
    return int(os.environ["TELEGRAM_CHAT_ID"])


def send_message(text: str) -> None:
    resp = requests.post(
        _api("sendMessage"),
        json={"chat_id": _allowed_chat_id(), "text": text},
        timeout=30,
    )
    resp.raise_for_status()


def _extract_messages(updates: list[dict], allowed_chat_id: int) -> list[str]:
    """Security rail: only messages from the allowlisted chat_id, only text."""
    texts = []
    for u in updates:
        msg = u.get("message") or {}
        if msg.get("chat", {}).get("id") == allowed_chat_id and msg.get("text"):
            texts.append(msg["text"])
    return texts


def read_replies(conn: sqlite3.Connection) -> list[str]:
    """Poll getUpdates with the offset persisted in the kv table."""
    offset = int(db.kv_get(conn, "tg_offset", "0"))
    resp = requests.get(_api("getUpdates"), params={"offset": offset + 1, "timeout": 0}, timeout=30)
    resp.raise_for_status()
    updates = resp.json().get("result", [])
    if updates:
        db.kv_set(conn, "tg_offset", str(max(u["update_id"] for u in updates)))
    return _extract_messages(updates, _allowed_chat_id())


if __name__ == "__main__":
    # Helper: `python -m src.tools.telegram --whoami` — message your bot first, then run this.
    import sys

    from dotenv import load_dotenv

    load_dotenv()
    if "--whoami" in sys.argv:
        r = requests.get(_api("getUpdates"), timeout=30)
        r.raise_for_status()
        chats = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "?")
                 for u in r.json().get("result", []) if u.get("message")}
        print("Chat IDs seen:", chats or "(none — send your bot a message first)")
