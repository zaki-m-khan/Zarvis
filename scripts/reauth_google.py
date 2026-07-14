"""Re-authorize Google Calendar and mint a fresh token.

Google expires refresh tokens after 7 days while the OAuth consent screen is in
"Testing" status — that's why the bot silently fell back to the weekly template.

Run:  python -m scripts.reauth_google

It opens a browser for Google consent, writes a fresh token.json locally, and
prints the JSON to paste into Render's GOOGLE_TOKEN_JSON env var (and the
GitHub GOOGLE_TOKEN_JSON secret, if you still run the old cron anywhere).

PERMANENT FIX (do this once so it stops dying every 7 days):
  Google Cloud Console -> APIs & Services -> OAuth consent screen ->
  Publishing status -> "PUBLISH APP" (In production). Personal use with the
  calendar.readonly scope needs no verification for your own account — you'll
  just click past an "unverified app" screen once. Production refresh tokens
  do not expire on a 7-day clock.
"""
import os

from dotenv import load_dotenv

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main() -> None:
    load_dotenv()
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_path = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS_JSON", "./credentials.json")
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)  # opens your browser once

    with open("token.json", "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print("\n" + "=" * 70)
    print("Fresh token.json written locally.")
    print("Paste EVERYTHING below as GOOGLE_TOKEN_JSON in Render -> Environment:")
    print("=" * 70)
    print(creds.to_json())
    print("=" * 70)
    print("Then Render redeploys automatically. Verify with:")
    print('  curl -s "https://zarvis.onrender.com/api/state?token=<DASH_TOKEN>" | grep blocks_source')
    print("  -> should say \"google\", not \"template\".")


if __name__ == "__main__":
    main()
