"""Google Calendar operations: list calendars, pull events, free/busy, busy, check, apply.

Named calendar_ops (not calendar) to avoid shadowing Python's stdlib
`calendar` module — the script directory is prepended to sys.path.

There is no delete or move here, and the only way to write an event is
`apply`: a plan that went through planner.check_plan and whose review hash the
student approved.
"""

import json
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError

import config as conf
import planner
from auth import get_service


def _norm(dt: str, tz: str) -> str:
    """RFC3339 datetime for the API; naive input is interpreted in `tz`."""
    if "T" not in dt:
        dt += "T00:00:00"
    parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(tz))
    return parsed.isoformat()


def _dump(obj):
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    print()


def resolve_calendar(args, cfg) -> str:
    if getattr(args, "area", None):
        return conf.require_real_id(conf.area(cfg, args.area)["calendar"], f"areas.{args.area}.calendar")
    return args.calendar


def list_events(svc, calendar_id: str, start: str, end: str, tz: str) -> list:
    events, page = [], None
    while True:
        resp = (
            svc.events()
            .list(
                calendarId=calendar_id,
                timeMin=_norm(start, tz),
                timeMax=_norm(end, tz),
                timeZone=tz,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page,
                maxResults=250,
            )
            .execute()
        )
        for e in resp.get("items", []):
            private = e.get("extendedProperties", {}).get("private", {})
            events.append(
                {
                    "id": e.get("id"),
                    "title": e.get("summary", "(no title)"),
                    "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
                    "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
                    "all_day": "date" in e.get("start", {}),
                    "description": e.get("description", ""),
                    "afp_block": private.get("afp_block"),
                    "afp_src": private.get("afp_src"),
                }
            )
        page = resp.get("nextPageToken")
        if not page:
            break
    return events


def fetch_busy(cfg, start: str, end: str) -> list:
    """Events from every calendar that counts as busy time (config.read_calendars)."""
    svc = get_service()
    out = []
    for cal in conf.read_calendars(cfg):
        cal_id = conf.require_real_id(cal["id"], f"calendar '{cal['name']}'")
        for e in list_events(svc, cal_id, start, end, cfg["timezone"]):
            out.append({**e, "calendar": cal["name"], "negotiable": cal["negotiable"]})
    out.sort(key=lambda e: e["start"])
    return out


def cmd_calendars(_args):
    svc = get_service()
    items = svc.calendarList().list().execute().get("items", [])
    _dump([{"name": c["summary"], "id": c["id"]} for c in items])


def cmd_pull(args):
    cfg = conf.load_config(args.config)
    _dump(list_events(get_service(), resolve_calendar(args, cfg), args.start, args.end, cfg["timezone"]))


def cmd_free(args):
    cfg = conf.load_config(args.config)
    calendar_id = resolve_calendar(args, cfg)
    resp = (
        get_service()
        .freebusy()
        .query(
            body={
                "timeMin": _norm(args.start, cfg["timezone"]),
                "timeMax": _norm(args.end, cfg["timezone"]),
                "timeZone": cfg["timezone"],
                "items": [{"id": calendar_id}],
            }
        )
        .execute()
    )
    _dump({"busy": resp["calendars"][calendar_id]["busy"]})


def cmd_busy(args):
    cfg = conf.load_config(args.config)
    _dump(fetch_busy(cfg, args.start, args.end))


# ---------- plan: check / apply ----------

def _today(args, cfg) -> date:
    return date.fromisoformat(args.today) if args.today else datetime.now(ZoneInfo(cfg["timezone"])).date()


def _plan_range(raw):
    """[first day, day after last day] of the plan's well-formed dates, or None."""
    days = []
    for b in raw.get("blocks", []) if isinstance(raw, dict) else []:
        try:
            days.append(date.fromisoformat(b["date"]))
        except (TypeError, KeyError, ValueError):
            continue
    if not days:
        return None
    return min(days).isoformat(), (max(days) + timedelta(days=1)).isoformat()


def _events_for(raw, cfg, events_file):
    if events_file:
        with open(events_file) as fh:
            return json.load(fh)
    span = _plan_range(raw)
    return fetch_busy(cfg, *span) if span else []


def cmd_check(args):
    cfg = conf.load_config(args.config)
    raw = planner.load_plan(args.plan)
    review = planner.check_plan(raw, _events_for(raw, cfg, args.events), cfg, _today(args, cfg))
    if args.table:
        print(review["table"])
    else:
        _dump(review)


def _insert_piece(svc, cfg):
    def insert(piece) -> str:
        description = f"vault:{piece['ctx']}\n\n{piece['reason']}" if piece["ctx"] else piece["reason"]
        body = {
            "id": piece["id"],
            "summary": piece["task"],
            "description": description,
            "start": {"dateTime": f"{piece['date']}T{piece['start']}:00", "timeZone": cfg["timezone"]},
            "end": {"dateTime": f"{piece['date']}T{piece['end']}:00", "timeZone": cfg["timezone"]},
            "extendedProperties": {"private": {
                "afp_block": piece["id"], "afp_src": piece["src"], "afp_ctx": piece["ctx"],
            }},
        }
        calendar_id = conf.require_real_id(piece["calendar"], f"areas.{piece['area']}.calendar")
        try:
            svc.events().insert(calendarId=calendar_id, body=body).execute()
            return "inserted"
        except HttpError as exc:
            # Same deterministic id already used in this calendar (Google keeps
            # the ids of deleted events too): never create a second copy.
            if exc.resp.status == 409:
                return "exists"
            raise
    return insert


def _append_log(cfg, line: str):
    log = conf.vault_dir(cfg) / "log.md"
    if log.parent.is_dir():
        with open(log, "a") as fh:
            fh.write(f"{datetime.now(ZoneInfo(cfg['timezone'])):%Y-%m-%d %H:%M} | calendar | {line}\n")


def cmd_apply(args):
    cfg = conf.load_config(args.config)
    raw = planner.load_plan(args.plan)
    events = _events_for(raw, cfg, None)  # always re-read the real calendar before writing
    result = planner.apply_plan(
        raw, events, cfg, _today(args, cfg), args.approved, _insert_piece(get_service(), cfg)
    )
    if result["ok"]:
        _append_log(cfg, f"apply {result['review_hash']}: {len(result['inserted'])} evento(s) creados, "
                         f"{result['existed']} ya existían ({args.plan})")
    _dump(result)
    if not result["ok"]:
        sys.exit(1)
