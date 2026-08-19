"""Google Calendar operations: list calendars, pull events, free/busy, insert.

Named calendar_ops (not calendar) to avoid shadowing Python's stdlib
`calendar` module — the script directory is prepended to sys.path.
"""

import json
import sys

from auth import get_service

DEFAULT_TZ = "America/Bogota"


def _norm(dt: str) -> str:
    """Ensure an offset is present; assume local Bogota (-05:00) if missing."""
    if "T" not in dt:
        dt += "T00:00:00"
    has_offset = dt.endswith("Z") or ("+" in dt[10:]) or ("-" in dt[11:])
    return dt if has_offset else dt + "-05:00"


def cmd_calendars(_args):
    svc = get_service()
    items = svc.calendarList().list().execute().get("items", [])
    json.dump(
        [{"name": c["summary"], "id": c["id"]} for c in items],
        sys.stdout, indent=2,
    )
    print()


def cmd_pull(args):
    svc = get_service()
    events = []
    page = None
    while True:
        resp = (
            svc.events()
            .list(
                calendarId=args.calendar,
                timeMin=_norm(args.start),
                timeMax=_norm(args.end),
                singleEvents=True,
                orderBy="startTime",
                pageToken=page,
                maxResults=250,
            )
            .execute()
        )
        for e in resp.get("items", []):
            events.append(
                {
                    "id": e.get("id"),
                    "title": e.get("summary", "(no title)"),
                    "start": e.get("start", {}).get("dateTime")
                    or e.get("start", {}).get("date"),
                    "end": e.get("end", {}).get("dateTime")
                    or e.get("end", {}).get("date"),
                    "description": e.get("description", ""),
                }
            )
        page = resp.get("nextPageToken")
        if not page:
            break
    json.dump(events, sys.stdout, indent=2)
    print()


def cmd_free(args):
    svc = get_service()
    resp = (
        svc.freebusy()
        .query(
            body={
                "timeMin": _norm(args.start),
                "timeMax": _norm(args.end),
                "timeZone": DEFAULT_TZ,
                "items": [{"id": args.calendar}],
            }
        )
        .execute()
    )
    busy = resp["calendars"][args.calendar]["busy"]
    json.dump({"busy": busy}, sys.stdout, indent=2)
    print()


def cmd_insert(args):
    svc = get_service()
    body = {
        "summary": args.title,
        "description": args.desc or "",
        "start": {"dateTime": _norm(args.start), "timeZone": DEFAULT_TZ},
        "end": {"dateTime": _norm(args.end), "timeZone": DEFAULT_TZ},
    }
    created = svc.events().insert(calendarId=args.calendar, body=body).execute()
    json.dump(
        {
            "id": created["id"],
            "title": created.get("summary"),
            "start": created["start"].get("dateTime"),
            "end": created["end"].get("dateTime"),
            "link": created.get("htmlLink"),
        },
        sys.stdout,
        indent=2,
    )
    print()
