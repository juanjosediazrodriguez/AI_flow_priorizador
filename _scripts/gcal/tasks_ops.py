"""Google Tasks operations: list task lists, list tasks, insert a task.

NOTE: the Tasks API is date-only — any time component on --due is discarded.
Task lists are addressed by area (config.json), so no ID lives in the skill.
"""

import json
import sys

import config as conf
from auth import get_tasks_service


def resolve_tasklist(args) -> str:
    if getattr(args, "area", None):
        cfg = conf.load_config(args.config)
        return conf.require_real_id(conf.area(cfg, args.area)["tasklist"], f"areas.{args.area}.tasklist")
    return args.tasklist


def cmd_tasklists(_args):
    svc = get_tasks_service()
    items = svc.tasklists().list(maxResults=100).execute().get("items", [])
    json.dump(
        [{"name": t["title"], "id": t["id"]} for t in items],
        sys.stdout, indent=2, ensure_ascii=False,
    )
    print()


def cmd_tasks(args):
    svc = get_tasks_service()
    tasklist = resolve_tasklist(args)
    tasks = []
    page = None
    while True:
        resp = (
            svc.tasks()
            .list(
                tasklist=tasklist,
                showCompleted=False,
                maxResults=100,
                pageToken=page,
            )
            .execute()
        )
        for t in resp.get("items", []):
            tasks.append(
                {
                    "id": t["id"],
                    "title": t.get("title", ""),
                    "due": (t.get("due") or "")[:10] or None,
                    "notes": t.get("notes", ""),
                }
            )
        page = resp.get("nextPageToken")
        if not page:
            break
    json.dump(tasks, sys.stdout, indent=2, ensure_ascii=False)
    print()


def cmd_task_insert(args):
    svc = get_tasks_service()
    body = {"title": args.title, "notes": args.notes or ""}
    if args.due:
        body["due"] = args.due + "T00:00:00Z"  # API keeps the date, discards time
    created = svc.tasks().insert(tasklist=resolve_tasklist(args), body=body).execute()
    json.dump(
        {
            "id": created["id"],
            "title": created.get("title"),
            "due": (created.get("due") or "")[:10] or None,
        },
        sys.stdout,
        indent=2,
        ensure_ascii=False,
    )
    print()
