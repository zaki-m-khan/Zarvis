"""Read-only calendar blocks: Google Calendar, with fallback to the SUMMER_PLAN weekly template."""
import json
import os
from datetime import date as date_cls, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
TOKEN_PATH = "token.json"

# SUMMER_PLAN.md §3 weekly template — same block logic as the dashboard.
# weekday(): Mon=0 … Sun=6
def fallback_blocks(now: datetime) -> list[tuple[str, str]]:
    dow = now.weekday()
    blocks: list[tuple[str, str]] = []
    if dow <= 4:  # Mon–Fri
        blocks.append(("12:30–13:00", "Recruiting Block — 5 outreaches"))
        blocks.append(("18:30–20:00", "Gym — PPL"))
    if dow in (1, 3):  # Tue, Thu
        blocks.append(("20:45–22:45", "Build Block — Jarvis"))
    if dow == 4:  # Fri
        blocks.append(("17:15–18:00", "Clay Send Ritual"))
    if dow == 6:  # Sun
        blocks = [
            ("10:00–14:00", "Sunday Deep Work"),
            ("17:00–17:30", "Weekly Review"),
            ("18:00–19:30", "Meal Prep"),
        ]
    if dow == 5:  # Sat
        blocks = [("ALL DAY", "Social / flex — guilt-free")]
    return blocks


def _google_events(now: datetime) -> list[tuple[str, str]]:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    elif os.environ.get("GOOGLE_TOKEN_JSON"):
        # Render/CI: no token file on the ephemeral disk — token comes via env.
        creds = Credentials.from_authorized_user_info(json.loads(os.environ["GOOGLE_TOKEN_JSON"]), scopes)
    else:
        # One-time local OAuth flow; caches token.json for future runs.
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds_path = os.environ["GOOGLE_CALENDAR_CREDENTIALS_JSON"]
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    start = datetime.combine(now.date() if isinstance(now, datetime) else now, time.min, tzinfo=ET)
    end = start + timedelta(days=1)
    calendar_ids = os.environ.get("GOOGLE_CALENDAR_IDS", "primary").split(",")
    events = []
    for cal_id in calendar_ids:
        events += (
            service.events()
            .list(
                calendarId=cal_id.strip(),
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )
    events.sort(key=lambda e: e["start"].get("dateTime", ""))
    blocks = []
    for e in events:
        start_raw = e["start"].get("dateTime")
        when = start_raw[11:16] if start_raw else "ALL DAY"
        blocks.append((when, e.get("summary", "(untitled)")))
    return blocks


def get_events(on_date: date_cls | None = None) -> tuple[list[tuple[str, str]], str]:
    """Blocks for a given date (default today). Returns (blocks, source: 'google'|'template'). Never raises."""
    now = datetime.now(ET)
    target = on_date or now.date()
    try:
        return _google_events(target), "google"
    except Exception:
        fake_now = datetime.combine(target, time(hour=12), tzinfo=ET)
        return fallback_blocks(fake_now), "template"


def get_today_events() -> tuple[list[tuple[str, str]], str]:
    """Returns (blocks, source) where source is 'google' or 'template'. Never raises."""
    return get_events()
