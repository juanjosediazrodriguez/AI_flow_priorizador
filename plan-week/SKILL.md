---
name: plan-week
description: Use when planning the week or a date range, scheduling vault tasks, or performing any Google Calendar / Google Tasks operation (pull busy blocks, insert events, create tasks with due dates, list calendars or task lists).
---

# Weekly Planning & Google Calendar/Tasks Operations

## Script usage

Every operation goes through the gcal helper, run from the repo root with the
shared venv (dependencies live in the root `requirements.txt`):

```
.venv/bin/python _scripts/gcal/gcal.py <command>
```

| Command | What it does |
|---|---|
| `scan` | Parses every `TASKS.md` linked from `vault/index.md` → JSON with validated `due`, `est_hours`, `prio`, `ctx`, `days_left`, `overdue` and `issues` per task |
| `busy --start <iso> --end <iso>` | Events from every calendar that counts as busy time |
| `check <plan.json> [--table]` | Validates a proposed plan against the policy and the real calendar; prints the review table and an approval code |
| `apply <plan.json> --approved <code>` | The ONLY way to create events |
| `tasks --area <area>` | Open Google Tasks (deadlines) of an area |
| `task-insert --title T --due YYYY-MM-DD --area <area> --notes N` | One deadline task (date-only) |
| `calendars`, `tasklists` | Only to fill `config.json` |

- Timezone, calendars and task lists come from `config.json`: address them by **area name**
  (`--area university`), never by ID.
- Google Tasks are DATE-ONLY — the API discards times. A task marks the DEADLINE date;
  events carry the hours the work actually happens.
- OAuth app is in testing mode: token expires ~weekly. On auth errors, run `gcal.py auth` (opens browser).

## Configuration — IDs never live in this file

Calendar IDs, task-list IDs, timezone, vault path and the planning policy live in
`_scripts/gcal/config.json` (gitignored; committed template: `config.example.json`).

If `config.json` is missing or still has `<...>` placeholders:

1. Run `calendars` and `tasklists`.
2. Propose the area → calendar / task-list mapping to the user as the exact JSON that
   will be written.
3. Write `config.json` only after the user approves it. Never copy IDs into this skill,
   `CLAUDE.md` or any other committed file.

## The policy lives in config.json

`config.json → policy` is the single source of the scheduling rules: earliest start,
minimum and maximum block length, break between blocks, and whether all-day events count
as busy. `check` enforces them. Do not restate their numbers here or in a proposal, and
never override what `check` returns.

- Aim each block at `policy.preferred_block_minutes`; `check` splits or rejects anything
  outside the hard limits.
- Soft preference `check` does not enforce: deep work earlier in the day unless the user
  says otherwise.
- `read_only_calendars` with `"busy": "negotiable"` (e.g. sports) count as busy but may be
  scheduled over when the week is tight — `check` only warns about them.

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
  `tasks --area <area>` and read the list before creating anything — a planned block
  and its deadline task have different titles AND different dates, so a duplicate does
  not look like one at a glance.
- NEVER create a task dated at a planned-work day.
- NEVER split one deliverable into several tasks because its work spans several
  blocks. The blocks are events; the deliverable is one task.
- `task-insert` is only for a deliverable that appears in `TASKS.md` but has NO task
  in the list at all — and then `--due` is its REAL deadline. Ask the user first.

## The plan: what you must output

Write the proposal to `vault/.plans/<first-day-of-range>.json` with EXACTLY this schema.
Missing or extra keys are rejected — do not add fields, do not rename them:

```json
{
  "requires_confirmation": false,
  "notes": "anything the user should know about this plan",
  "blocks": [
    {
      "task": "Laboratorio 3: árbol AVL",
      "ctx": "10-university/2026-2/estructuras-de-datos/assignments/lab-3-avl.md",
      "area": "university",
      "date": "2026-09-23",
      "start": "14:00",
      "end": "16:00",
      "priority": "high",
      "reason": "Due on the 28th, worth 10 %, not started yet."
    }
  ]
}
```

- `task`, `ctx` and `area` are copied from the `scan` output (`ctx` is `""` when the task
  has none). `priority` is `high | med | low`; `reason` is the one-line rationale the user
  reviews.
- Every date comes from `scan`, `busy` or the user — never from "today"/"tomorrow" guesses.
- If the input is ambiguous, contradictory or insufficient, set
  `"requires_confirmation": true`, put the question in `notes`, and ask. `check` will
  schedule nothing from that plan.

## Weekly planning flow

Trigger: user asks to plan/organize the week (or a date range).

1. `scan` → open tasks with `due` in or near the range, plus `overdue` ones. Raise any
   `issues` that affect planning (bad `due`, missing `ctx`, TASKS.md missing from the index).
2. `busy --start <range start> --end <range end>`.
3. For each candidate task, read its `ctx` note to validate the estimate. Ask the user
   about anything unclear — never invent an estimate.
4. Write the plan JSON (schema above).
5. `check <plan> --table` and show the user the table and its approval code. You may
   adjust the plan for rows marked PARTIDO/RECHAZADO and re-run `check`; always show the
   final table.
6. Wait for explicit approval of that table. If the user changes anything, edit the plan
   and re-run `check` — the approval code changes with it.
7. `apply <plan> --approved <code>`. It re-reads the calendar and refuses if the plan or
   the calendar changed since the approval. It never duplicates events, so it is safe to
   re-run after a failure, and it appends the session to `vault/log.md`.
8. Write NO tasks — see "Tasks are deadlines, events are work". If some deliverable has no
   deadline task at all, flag it and ask; do not quietly create one.

## Rules

- ALL writes (tasks and events) happen only after explicit user approval (CLAUDE.md hard
  rule 7). Events are written only through `apply`.
- Never delete or move existing events or tasks. gcal.py has no command for it; never
  script one around the token, and never read or print `_scripts/gcal/secrets/`.
- A task with no clear area routes to `default_area` — ask if in doubt.
