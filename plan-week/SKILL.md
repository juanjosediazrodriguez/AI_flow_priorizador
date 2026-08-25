---
name: plan-week
description: Use when planning the week or a date range, scheduling vault tasks, or performing any Google Calendar / Google Tasks operation (pull busy blocks, insert events, create tasks with due dates, list calendars or task lists).
---

# Weekly Planning & Google Calendar/Tasks Operations

## Script usage

Every operation goes through the gcal helper, run with its own venv:

```
cd _scripts/gcal && .venv/bin/python gcal.py <command>
```

Commands: `calendars`, `tasklists`, `tasks [--tasklist <id>]`,
`pull --calendar <id> --start <iso> --end <iso>`,
`insert --title T --start <iso> --end <iso> --calendar <id> --desc D`,
`task-insert --title T --due YYYY-MM-DD --tasklist <id> --notes N`.

- Google Tasks are DATE-ONLY — the API discards times. A task marks the DEADLINE date;
  events carry the hours the work actually happens.
- Timezone: America/Bogota (-05:00). Bare dates are treated as local midnight.
- OAuth app is in testing mode: token expires ~weekly. On auth errors, run `gcal.py auth` (opens browser).
- Mark planner-created items with `--notes "vault:<ctx path>"` / `--desc "vault:<ctx path>"` (or `vault:test`).

## Area routing map

Scheduling a planned task → event in its area's CALENDAR, one per allocated time slot.
Google Tasks are the DEADLINE view and are almost always already populated — read
"Tasks are deadlines, events are work" below before ever calling `task-insert`.

| Area | Calendar ID (events) | Task list ID |
|---|---|---|
| Personal (`20-personal/`, default for unclear) | `primary` | `MDgzMTEzNzA5NTA0NjU0MzQwODI6MDow` (My Tasks) |
| University (`10-university/`) | `ca64aabb2622978f8a44e5dc4ef171340df093a38dceebac170d6faf623f975d@group.calendar.google.com` | `NkZyeVBhSUtmLUY1MGV0bQ` |
| Apolo (`30-professional/apolo/`) | `516c32a80733eac6acb09c047e63d96439892e57e83277995173b638775f349d@group.calendar.google.com` | `elNRLWwyX0tBLUQ5QW5mWQ` (APOLO) |
| Startups | `539fc58f417a7e821f3cbc41616633954ae9d3319f516e80e61a10c4c2859749@group.calendar.google.com` | `dUlnVjRoT3V2M2dRSVVRcA` |

Read-only / excluded:

| Resource | ID | Rule |
|---|---|---|
| Sports calendar | `67d220de035501296a105821ad115da882649cbdf6f7e82a11262e68f39ed23d@group.calendar.google.com` | Read: gym + table tennis count as busy, but fully negotiable — may schedule over them when the week is tight. Never write. |
| RCAC calendar | `ab25f3186012729e6c78e9aa65b50dc0c19d7201fff8ca13a1b24e32a1b71159@group.calendar.google.com` | Legacy. Exclude from busy-time entirely. Never write. |
| RCAC task list | `VHNrWVFSN1IydzBHZjl4eg` | Legacy. Never write. |
| Birthdays task list | `UTFuS295cDZiN3g0c1d3QQ` | Human-managed. Never write. |

## Tasks are deadlines, events are work

Google renders a task on the calendar at its due date. So a task written at a
*planned-work* date shows up as a fake deadline sitting right next to the real one —
which is exactly the duplication this section exists to prevent.

- **Google Task = the deadline.** One per real deliverable, `due` = the date it is
  actually handed in, mirroring the `due:` field of the vault's `TASKS.md` line.
- **Calendar event = the work.** One per allocated block, at the hours the work happens.

Therefore:

- Planning a week writes **events only**. It does NOT write tasks.
- The deadline tasks already exist in almost every case. ALWAYS run
  `tasks --tasklist <id>` and read the list before creating anything — a planned block
  and its deadline task have different titles AND different dates, so a duplicate does
  not look like one at a glance.
- NEVER create a task dated at a planned-work day.
- NEVER split one deliverable into several tasks because its work spans several
  blocks. The blocks are events; the deliverable is one task.
- `task-insert` is only for a deliverable that appears in `TASKS.md` but has NO task
  in the list at all — and then `--due` is its REAL deadline. Ask the user first.

## Rules

- Pulls for planning MUST cover every calendar above except RCAC (loop `pull --calendar <id>`).
- Ignore all-day events when computing free slots.
- A task with no clear area routes to Personal — ask if in doubt.
- ALL writes (tasks and events) happen only after explicit user approval of the proposed
  plan (CLAUDE.md hard rule 7). Never delete or move existing events or tasks.

## Weekly planning flow

Trigger: user asks to plan/organize the week (or a date range).

1. Pull busy blocks from every "read" calendar in the map (loop per calendar).
2. Scan `**/TASKS.md` (minus `90-archive/`) for open tasks with `due` in or near the
   range; include overdue open tasks.
3. For each candidate task, read its `ctx` note to validate the estimate. Ask the user
   about anything unclear — never invent an estimate.
4. Propose a schedule as a markdown table: day, start–end, task, area, rationale.
   Respect existing events; NEVER propose blocks before 9:00; default block length
   1.5–2h with breaks; deep work earlier in the day unless told otherwise.
5. Wait for explicit approval (user may edit the table).
6. On approval, route by area per the map: one `insert` into that area's calendar for
   each allocated time slot. Write NO tasks — see "Tasks are deadlines, events are
   work". If some deliverable turns out to have no deadline task at all, flag it and
   ask; do not quietly create one.
7. Append the planning session to `/log.md`.
