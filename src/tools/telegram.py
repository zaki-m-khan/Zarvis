"""Telegram send/receive via raw HTTP. Hard chat_id allowlist — ignore all other senders."""
import os
import sqlite3

import requests

from src import db

# Inline keyboard for the evening check-in: one tap = one structured boolean.
# Numbers (outreach count, steps, weight) come in as free text and get LLM-parsed.
CHECKIN_BUTTONS = [
    [
        {"text": "💪 Gym done", "callback_data": "gym"},
        {"text": "👟 10k steps", "callback_data": "steps10k"},
    ],
    [
        {"text": "🧱 Clay shipped", "callback_data": "clay"},
        {"text": "🚀 Milestone hit", "callback_data": "milestone"},
    ],
]

BUTTON_TO_FIELD = {
    "gym": {"gym": True},
    "steps10k": {"steps": 10000},
    "clay": {"clay": True},
    "milestone": {"milestone": True},
}


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/{method}"


def _allowed_chat_id() -> int:
    return int(os.environ["TELEGRAM_CHAT_ID"])


def send_message(text: str, buttons: list | None = None) -> None:
    payload: dict = {"chat_id": _allowed_chat_id(), "text": text}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    resp = requests.post(_api("sendMessage"), json=payload, timeout=30)
    resp.raise_for_status()


def _extract_updates(updates: list[dict], allowed_chat_id: int) -> tuple[list[str], list[str]]:
    """Security rail: only the allowlisted chat_id. Returns (text_replies, button_taps)."""
    texts, taps = [], []
    for u in updates:
        msg = u.get("message") or {}
        if msg.get("chat", {}).get("id") == allowed_chat_id and msg.get("text"):
            texts.append(msg["text"])
        cq = u.get("callback_query") or {}
        if cq.get("from", {}).get("id") == allowed_chat_id and cq.get("data") in BUTTON_TO_FIELD:
            taps.append(cq["data"])
    return texts, taps


def read_replies(conn: sqlite3.Connection) -> tuple[list[str], list[str]]:
    """Poll getUpdates with the offset persisted in the kv table. Returns (texts, button_taps)."""
    offset = int(db.kv_get(conn, "tg_offset", "0"))
    resp = requests.get(_api("getUpdates"), params={"offset": offset + 1, "timeout": 0}, timeout=30)
    resp.raise_for_status()
    updates = resp.json().get("result", [])
    if updates:
        db.kv_set(conn, "tg_offset", str(max(u["update_id"] for u in updates)))
    return _extract_updates(updates, _allowed_chat_id())


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
