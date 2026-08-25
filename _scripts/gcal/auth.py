"""OAuth flow and authenticated Google API service builders.

Setup (one time):
  1. Google Cloud Console -> create project -> enable "Google Calendar API"
  2. OAuth consent screen: External, add yourself as test user
  3. Credentials -> Create OAuth client ID -> Desktop app
  4. Download JSON as secrets/credentials.json (folder is gitignored)
  5. pip install -r requirements.txt
  6. python gcal.py auth   (opens browser once; secrets/token.json is saved/refreshed)
"""

import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]
HERE = Path(__file__).resolve().parent
SECRETS_DIR = HERE / "secrets"
CREDS_FILE = SECRETS_DIR / "credentials.json"
TOKEN_FILE = SECRETS_DIR / "token.json"


def _get_creds():
    creds = None
    if TOKEN_FILE.exists():
        info = json.loads(TOKEN_FILE.read_text())
        # creds.scopes reflects the REQUESTED scopes, so compare against the
        # granted scopes stored in the token file to detect missing consent.
        if not (set(SCOPES) - set(info.get("scopes") or [])):
            creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                sys.exit(
                    "credentials.json not found. Follow the setup steps in the "
                    "docstring / README first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def get_service():
    return build("calendar", "v3", credentials=_get_creds())


def get_tasks_service():
    return build("tasks", "v1", credentials=_get_creds())


def cmd_auth(_args):
    get_service()
    print("Auth OK — token.json saved.")
