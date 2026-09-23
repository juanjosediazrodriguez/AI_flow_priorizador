#!/usr/bin/env python3
"""Google Calendar / Tasks helper for the vault (direct API, no MCP).

Setup (no config needed):
  auth                          Run the OAuth flow once, store token.json
  calendars                     List all calendars (name + ID) — to fill config.json
  tasklists                     List Google Tasks lists (name + ID) — to fill config.json

Vault:
  scan [--today D] [--all]      Parse every TASKS.md registered in the vault's index.md

Planning (the only way to write events):
  busy  --start ISO --end ISO   Events from every busy calendar in config.json
  check PLAN [--events F] [--today D] [--table]
                                Validate plan.json against the policy and the real
                                calendar; prints the review table + approval code
  apply PLAN --approved CODE    Re-check and insert ONLY if CODE matches the review
                                the student approved. Idempotent: re-running it
                                never duplicates events.

Reads:
  pull  --start ISO --end ISO [--area A | --calendar ID]   Events in range
  free  --start ISO --end ISO [--area A | --calendar ID]   Free/busy blocks
  tasks [--area A | --tasklist ID]                         Open tasks in a list
  task-insert --title T [--due YYYY-MM-DD] [--notes N] [--area A | --tasklist ID]
                                Insert one Google Task (a DEADLINE). The Tasks API
                                is date-only — any time component is discarded.

IDs, timezone, vault path and planning policy live in config.json (see
config.example.json). ISO datetimes: 2026-08-10T14:00:00 (local) or with offset.
"""

import argparse
import json
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

import config as conf
from auth import cmd_auth
from calendar_ops import cmd_apply, cmd_busy, cmd_calendars, cmd_check, cmd_free, cmd_pull
from tasks_ops import cmd_task_insert, cmd_tasklists, cmd_tasks
from vault_scan import scan


def cmd_scan(args):
    cfg = conf.load_config(args.config)
    today = date.fromisoformat(args.today) if args.today else datetime.now(ZoneInfo(cfg["timezone"])).date()
    vault = conf.vault_dir(cfg)
    if not vault.is_dir():
        sys.exit(f"Vault not found at {vault} (config.json -> vault_path).")
    json.dump(scan(vault, cfg, today, include_done=args.all), sys.stdout, indent=2, ensure_ascii=False)
    print()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=None, help="Path to config.json (default: next to this script)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth")
    sub.add_parser("calendars")
    sub.add_parser("tasklists")

    s = sub.add_parser("scan")
    s.add_argument("--today", help="YYYY-MM-DD (default: today in config timezone)")
    s.add_argument("--all", action="store_true", help="Include completed tasks")

    s = sub.add_parser("busy")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)

    s = sub.add_parser("check")
    s.add_argument("plan")
    s.add_argument("--events", help="JSON from `busy` instead of calling Google (offline check)")
    s.add_argument("--today", help="YYYY-MM-DD (default: today in config timezone)")
    s.add_argument("--table", action="store_true", help="Print only the review table")

    s = sub.add_parser("apply")
    s.add_argument("plan")
    s.add_argument("--approved", required=True, help="Approval code printed by `check`")
    s.add_argument("--today", help="YYYY-MM-DD (default: today in config timezone)")

    for name in ("pull", "free"):
        s = sub.add_parser(name)
        s.add_argument("--start", required=True)
        s.add_argument("--end", required=True)
        g = s.add_mutually_exclusive_group()
        g.add_argument("--area", help="Area from config.json")
        g.add_argument("--calendar", default="primary", help="Calendar ID (default: primary)")

    s = sub.add_parser("tasks")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--area", help="Area from config.json")
    g.add_argument("--tasklist", default="@default")

    s = sub.add_parser("task-insert")
    s.add_argument("--title", required=True)
    s.add_argument("--due", default="", help="YYYY-MM-DD (Tasks API is date-only)")
    s.add_argument("--notes", default="")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--area", help="Area from config.json")
    g.add_argument("--tasklist", default="@default")

    args = p.parse_args()
    {
        "auth": cmd_auth,
        "calendars": cmd_calendars,
        "tasklists": cmd_tasklists,
        "scan": cmd_scan,
        "busy": cmd_busy,
        "check": cmd_check,
        "apply": cmd_apply,
        "pull": cmd_pull,
        "free": cmd_free,
        "tasks": cmd_tasks,
        "task-insert": cmd_task_insert,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
