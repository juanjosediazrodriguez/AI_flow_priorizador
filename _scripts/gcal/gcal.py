#!/usr/bin/env python3
"""Google Calendar helper for the vault (direct API, no MCP).

Commands:
  auth                          Run the OAuth flow once, store token.json
  calendars                     List all calendars (name + ID, JSON to stdout)
  pull   --start ISO --end ISO  List events in range (JSON to stdout)
  free   --start ISO --end ISO  Show free/busy blocks in range (JSON)
  insert --title T --start ISO --end ISO [--desc D] [--calendar ID]
                                Insert one event (prints created event JSON)
  tasklists                     List Google Tasks lists (name + ID)
  tasks  [--tasklist ID]        List open tasks in a list (default: @default)
  task-insert --title T [--due YYYY-MM-DD] [--notes N] [--tasklist ID]
                                Insert one Google Task. NOTE: the Tasks API is
                                date-only — any time component is discarded.

Setup (one time): see auth.py docstring / README.md.

ISO datetimes: 2026-08-10T14:00:00 (local) or with offset 2026-08-10T14:00:00-05:00
"""

import argparse

from auth import cmd_auth
from calendar_ops import cmd_calendars, cmd_free, cmd_insert, cmd_pull
from tasks_ops import cmd_task_insert, cmd_tasklists, cmd_tasks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth")
    sub.add_parser("calendars")
    sub.add_parser("tasklists")

    s = sub.add_parser("tasks")
    s.add_argument("--tasklist", default="@default")

    s = sub.add_parser("task-insert")
    s.add_argument("--title", required=True)
    s.add_argument("--due", default="", help="YYYY-MM-DD (Tasks API is date-only)")
    s.add_argument("--notes", default="")
    s.add_argument("--tasklist", default="@default")

    for name in ("pull", "free"):
        s = sub.add_parser(name)
        s.add_argument("--start", required=True)
        s.add_argument("--end", required=True)
        s.add_argument("--calendar", default="primary", help="Calendar ID (default: primary)")

    s = sub.add_parser("insert")
    s.add_argument("--title", required=True)
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--desc", default="")
    s.add_argument("--calendar", default="primary", help="Calendar ID (default: primary)")
    args = p.parse_args()
    {
        "auth": cmd_auth,
        "calendars": cmd_calendars,
        "pull": cmd_pull,
        "free": cmd_free,
        "insert": cmd_insert,
        "tasklists": cmd_tasklists,
        "tasks": cmd_tasks,
        "task-insert": cmd_task_insert,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
