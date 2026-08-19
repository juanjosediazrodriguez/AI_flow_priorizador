# Vault — Master Context

Personal knowledge base and planning system for Jero, computer science
student at EAFIT (6th semester) and developer. Working language: English.

This vault is the "second brain". Claude operates on it directly: reading
context, maintaining tasks, planning the week, and (with approval) inserting
Google Tasks and calendar events via the gcal helper.

Personal background (bio, work, preferences, goals) lives in `/me.md`. Read it
ONLY when the prompt requires knowing something personal about Jero — never
load it for routine vault, task, or calendar operations.

## Structure

- `00-inbox/` — quick capture. Anything here is unprocessed; help triage it
  into the right area when asked.
- `10-university/<semester>/<course>/` — one folder per course. Every course
  follows `_templates/course.md`: `_course.md`, `TASKS.md`, `notes/`,
  `assignments/`, `resources/`, `attachments/`.
- `20-personal/<area>/` — personal life areas (finances, health, ...).
- `30-professional/<project>/` — personal dev projects, fully in the vault:
  `_project.md` (context entry point) + `TASKS.md` + notes, with the git repo
  under `code/<repo-name>/`. Vault git ignores `**/code/` — every repo keeps
  its own git and remote. Umbrella areas group subprojects (e.g. `apolo/`).
  To work on a project, open Claude Code at its folder (docs + code together).
  Courses may also carry code the same way (`10-university/.../<course>/code/`).
- `90-archive/` — closed semesters and finished projects. Excluded from all
  task scans.
- `_templates/` — scaffolds for new courses, projects, and TASKS files.
- `_scripts/gcal/` — Google Calendar API helper (`gcal.py`). Credentials in
  this folder are gitignored and must never be committed.

Entry point for any area is its `_course.md` / `_project.md` / `_semester.md`.
Read it first before working inside that area.

Attachments (pasted images, PDFs) live in the area's own `attachments/` folder
— never in a vault-wide one, so archiving an area takes its images with it.
Obsidian is configured to drop new pastes there automatically ("In subfolder
under current folder" → `attachments`). Image links are wikilinks resolved by
filename, not by path, so moving a note between areas never breaks an image;
move its attachments along with it. Keep filenames unique vault-wide — two
files with the same name make the resolution ambiguous.

## Calendar & weekly planning

All Google Calendar / Google Tasks operations and the weekly planning flow are
defined in the `plan-week` skill (`.claude/skills/plan-week/SKILL.md`): the
area routing map (calendar + task list IDs), gcal.py usage, and the full
planning procedure. ALWAYS invoke that skill before any calendar or task
operation — never guess IDs or commands from memory.

## Hard rules

1. Every course, project, and personal area MUST contain a `TASKS.md` using
   the standard line format (see `_templates/tasks.md`). No exceptions.
2. There is NO stored central task list. The global view is always computed
   by scanning `**/TASKS.md`, excluding `90-archive/`.
3. Every structural change or task mutation gets ONE line appended to
   `/log.md`: `YYYY-MM-DD HH:MM | area | action`. Append-only — never edit
   or delete past lines.
4. Keep `/index.md` updated whenever notes are created, moved, or archived.
5. When estimating a task: read its `ctx` note first. If context is still
   insufficient, ASK the user — never invent an estimate.
6. New project or course → scaffold from the matching file in `_templates/`,
   always including `TASKS.md`. Ask for any missing metadata (schedule,
   grading %, repo path) instead of leaving placeholders silently.
7. All Google Calendar AND Google Tasks operations go through
   `_scripts/gcal/gcal.py` (direct API). Propose insertions as a table for
   approval first; only run inserts after explicit user confirmation. Never
   delete or move existing calendar events or tasks.
8. Task edits happen in the area's own `TASKS.md` (single source of truth).
   A completed task is marked `[x]`, not deleted, until its area is archived.

## TASKS.md line format

```
- [ ] <title> | due:YYYY-MM-DD | est:<hours>h | prio:high|med|low | ctx:<relative/path.md>
```

`ctx` is optional but strongly preferred for anything estimated above 2h.
