"""End-loop guardrails (JARVIS_BUILD.md §7): 90s timeout, fail loud via Telegram, then exit."""
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

TIMEOUT_S = 90


def run_guarded(run_type: str, fn) -> None:
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn)
        try:
            future.result(timeout=TIMEOUT_S)
            from src import tracing

            tracing.flush()  # short-lived process: don't lose Langfuse spans on exit
            return
        except FutureTimeout:
            error = f"Jarvis {run_type} run timed out after {TIMEOUT_S}s. Check in manually?"
        except Exception:
            error = f"Jarvis {run_type} run crashed:\n{traceback.format_exc()[-500:]}"
    # Fail loud: silence is the worst failure mode for an accountability bot.
    try:
        from src.tools import telegram

        telegram.send_message(error)
    except Exception:
        pass
    print(error, file=sys.stderr)
    sys.exit(1)
