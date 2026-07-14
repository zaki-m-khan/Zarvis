"""LLM-as-judge (Phase 4, spec §9): score every sent message 1-5 on the rubric.

Usage:
    python -m evals.judge            # score unscored sent messages + report
    python -m evals.judge --report   # report only (no new scoring)

Writes scores to the evals table; prints per-dimension averages and the
compliance-vs-greens correlation check. Iteration trigger: any dimension
averaging < 3.5 -> prompt iteration required (documented in rubric.md).
"""
import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src import db, llm, scoreboard

DIMENSIONS = ("brevity", "specificity", "personality", "actionability")

JUDGE_PROMPT = (
    "You are scoring a message sent by Jarvis, an accountability agent, against this rubric:\n"
    "- brevity: <=6 lines morning, no walls of text (1=wall of text, 5=tight)\n"
    "- specificity: names actual blocks/times/scoreboard numbers (1=generic filler, 5=concrete)\n"
    "- personality: direct hype-coach, a little funny, no corporate fluff, no guilt-tripping "
    "(1=corporate/generic, 5=nails the voice)\n"
    "- actionability: exactly ONE clear ask or zero asks, references history when relevant "
    "(1=three questions/no direction, 5=one sharp ask)\n\n"
    "Message ({run_type}):\n---\n{message}\n---\n\n"
    'Return ONLY JSON: {{"brevity": n, "specificity": n, "personality": n, "actionability": n, '
    '"notes": "<=15 words on the weakest dimension"}}'
)


class Scores(BaseModel):
    brevity: float = Field(ge=1, le=5)
    specificity: float = Field(ge=1, le=5)
    personality: float = Field(ge=1, le=5)
    actionability: float = Field(ge=1, le=5)
    notes: str = ""


def score_unscored(conn) -> int:
    rows = conn.execute(
        "SELECT c.id, c.chat_id, c.run_type, c.raw_text FROM checkins c "
        "LEFT JOIN evals e ON e.checkin_id = c.id "
        "WHERE c.direction = 'sent' AND c.raw_text != '' AND e.id IS NULL ORDER BY c.id"
    ).fetchall()
    scored = 0
    for cid, chat_id, run_type, text in rows:
        data = llm.json_call(JUDGE_PROMPT.format(run_type=run_type, message=text))
        try:
            s = Scores.model_validate(data)
        except Exception:
            print(f"  judge returned unusable scores for checkin {cid}, skipping")
            continue
        conn.execute(
            "INSERT INTO evals (checkin_id, chat_id, ts, brevity, specificity, personality, actionability, notes, prompt_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, chat_id, datetime.now(timezone.utc).isoformat(),
             s.brevity, s.specificity, s.personality, s.actionability, s.notes,
             os.environ.get("PROMPT_VERSION", "v1")),
        )
        conn.commit()
        scored += 1
        print(f"  #{cid} [{run_type}] b={s.brevity:g} s={s.specificity:g} p={s.personality:g} a={s.actionability:g}  {s.notes}")
    return scored


def report(conn) -> None:
    rows = conn.execute(
        "SELECT prompt_version, COUNT(*), AVG(brevity), AVG(specificity), AVG(personality), AVG(actionability) "
        "FROM evals GROUP BY prompt_version ORDER BY prompt_version"
    ).fetchall()
    if not rows:
        print("No evals yet.")
        return
    print("\n=== Judge report (1-5 per dimension) ===")
    for version, n, *avgs in rows:
        line = " · ".join(f"{d}={a:.2f}" for d, a in zip(DIMENSIONS, avgs))
        flags = [d for d, a in zip(DIMENSIONS, avgs) if a < 3.5]
        verdict = f"  ⚠ ITERATE ({', '.join(flags)} < 3.5)" if flags else "  ✓ holding"
        print(f"{version} (n={n}): {line}{verdict}")

    # Correlation check: compliance (received replies per sent check-in) vs greens.
    sent = conn.execute("SELECT COUNT(*) FROM checkins WHERE direction = 'sent'").fetchone()[0]
    received = conn.execute(
        "SELECT COUNT(*) FROM checkins WHERE direction = 'received' AND raw_text != ''"
    ).fetchone()[0]
    values = scoreboard.tally_week(conn)
    greens = sum(1 for m, t in scoreboard.TARGETS.items() if values[m] >= t)
    compliance = received / sent if sent else 0
    print(f"\nCompliance: {received} replies / {sent} sent = {compliance:.0%} · this week greens: {greens}/6")
    print("(Track weekly: compliance should move greens — if it doesn't, the messages aren't landing.)")


if __name__ == "__main__":
    load_dotenv()
    conn = db.connect()
    if "--report" not in sys.argv:
        n = score_unscored(conn)
        print(f"\nScored {n} new message(s).")
    report(conn)
