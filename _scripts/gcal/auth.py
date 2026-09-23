"""OAuth flow and authenticated Google API service builders.

Setup (one time):
  1. Google Cloud Console -> create project -> enable "Google Calendar API"
     AND "Google Tasks API" (both are used below)
  2. OAuth consent screen: External, add yourself as test user
  3. Credentials -> Create OAuth client ID -> Desktop app
  4. Download JSON as secrets/credentials.json (folder is gitignored)
  5. pip install -r requirements.txt   (from the repo root)
  6. python gcal.py auth   (opens browser once; secrets/token.json is saved/refreshed)
"""

import json
import sys
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Least privilege. Google has no insert-only scope, so events can still be
# deleted through the API — but not calendars, their sharing (ACLs) or settings,
# which the full `calendar` scope allowed. gcal.py itself never deletes.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",  # list calendars, events, free/busy
    "https://www.googleapis.com/auth/calendar.events",    # insert events (apply)
    "https://www.googleapis.com/auth/tasks",              # list + insert Google Tasks
]
HERE = Path(__file__).resolve().parent
SECRETS_DIR = HERE / "secrets"
CREDS_FILE = SECRETS_DIR / "credentials.json"
TOKEN_FILE = SECRETS_DIR / "token.json"


def _run_consent_flow():
    if not CREDS_FILE.exists():
        sys.exit(
            "credentials.json not found. Follow the setup steps in the "
            "docstring / README first."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    return flow.run_local_server(port=0)


def _get_creds():
    creds = None
    if TOKEN_FILE.exists():
        info = json.loads(TOKEN_FILE.read_text())
        # creds.scopes reflects the REQUESTED scopes, so compare against the
        # granted scopes stored in the token file to detect missing consent.
        # A token from the old full-`calendar` scope fails this check, so the
        # user is asked once to consent to the narrower set.
        if not (set(SCOPES) - set(info.get("scopes") or [])):
            creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # While the OAuth app is in testing mode Google expires refresh
            # tokens after ~7 days. A dead or revoked one must fall back to a
            # fresh browser consent — otherwise `gcal.py auth`, whose whole job
            # is to recover from this, crashes instead of re-authenticating.
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = _run_consent_flow()
        else:
            creds = _run_consent_flow()
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def get_service():
    return build("calendar", "v3", credentials=_get_creds())


def get_tasks_service():
    return build("tasks", "v1", credentials=_get_creds())


def cmd_auth(_args):
    get_service()
    print("Auth OK — token.json saved.")
