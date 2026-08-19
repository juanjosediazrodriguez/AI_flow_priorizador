"""Google Tasks operations: list task lists, list tasks, insert a task.

NOTE: the Tasks API is date-only — any time component on --due is discarded.
"""

import json
import sys

from auth import get_tasks_service


def cmd_tasklists(_args):
    svc = get_tasks_service()
    items = svc.tasklists().list(maxResults=100).execute().get("items", [])
    json.dump(
        [{"name": t["title"], "id": t["id"]} for t in items],
        sys.stdout, indent=2,
    )
    print()


def cmd_tasks(args):
    svc = get_tasks_service()
    tasks = []
    page = None
    while True:
        resp = (
            svc.tasks()
            .list(
                tasklist=args.tasklist,
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
    json.dump(tasks, sys.stdout, indent=2)
    print()


def cmd_task_insert(args):
    svc = get_tasks_service()
    body = {"title": args.title, "notes": args.notes or ""}
    if args.due:
        body["due"] = args.due + "T00:00:00Z"  # API keeps the date, discards time
    created = svc.tasks().insert(tasklist=args.tasklist, body=body).execute()
    json.dump(
        {
            "id": created["id"],
            "title": created.get("title"),
            "due": (created.get("due") or "")[:10] or None,
        },
        sys.stdout,
        indent=2,
    )
    print()
