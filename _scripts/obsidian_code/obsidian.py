#!/usr/bin/env python3
"""Obsidian vault scaffolder: create courses, projects and areas.

Commands:
  init                                  Create the vault skeleton + _templates/
  course  --name N --semester S ...     Scaffold 10-university/<semester>/<name>/
  project --name N --repo R             Scaffold 30-professional/<name>/
  area    --name N                      Scaffold 20-personal/<name>/
  list                                  Show what already exists (JSON to stdout)

The vault is given by --vault or the OBSIDIAN_VAULT env var.

Every scaffold honours the vault's hard rules:
  1. a TASKS.md is always written, with the standard line format in its header
  3. ONE line is appended to log.md  ->  YYYY-MM-DD HH:MM | area | action
  4. the new entry is added to index.md, as a wikilink carrying the full
     vault-relative path: gcal.py scan resolves index links as paths, not by
     note name, and an area it cannot resolve is invisible to planning
  6. templates come from _templates/ when present, and missing metadata is an
     error instead of a silent placeholder

Nothing is ever overwritten or deleted. If the target folder already exists the
command fails closed and says so -- same reason gcal.py has no delete command:
a capability that does not exist cannot be talked into running.

Use --dry-run to print the tree, the log line and the index line without
touching the disk.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# The defined structure. Change these names here and the whole script follows.
AREA_DIRS = {
    "inbox": "00-inbox",
    "university": "10-university",
    "personal": "20-personal",
    "professional": "30-professional",
    "archive": "90-archive",
}
COURSE_SUBDIRS = ("notes", "assignments", "resources", "attachments")
PROJECT_SUBDIRS = ("notes", "attachments", "code")
TEMPLATES_DIR = "_templates"

TASKS_TEMPLATE = """# {{title}} — tasks

Line format (the planner parses these lines, do not change the shape):
`- [ ] <title> | due:YYYY-MM-DD | est:<hours>h | prio:high|med|low | ctx:<relative/path.md>`

`ctx` is optional but strongly preferred for anything estimated above 2h.
A finished task is marked `[x]`, never deleted.

"""

COURSE_TEMPLATE = """---
type: course
area: university
semester: {{semester}}
professor: {{professor}}
schedule: {{schedule}}
---

# {{title}}

Entry point for this course. Read this before working anywhere inside the folder.

## Evaluation

{{grading}}

## Schedule

{{schedule}}

## Structure

- `TASKS.md` — every pending item for this course
- `notes/` — class notes, one per session
- `assignments/` — one note per deliverable, linked from `TASKS.md` via `ctx:`
- `resources/` — slides, papers, links
- `attachments/` — pasted images and PDFs for this course only
"""

PROJECT_TEMPLATE = """---
type: project
area: professional
repo: {{repo}}
---

# {{title}}

Context entry point for this project. Read this before working inside the folder.

## What it is

{{summary}}

## Structure

- `TASKS.md` — every pending item for this project
- `notes/` — decisions, research, session notes
- `code/{{repo}}/` — the git repo, with its own remote (vault git ignores `**/code/`)
- `attachments/` — images and PDFs for this project only
"""

AREA_TEMPLATE = """---
type: area
area: personal
---

# {{title}}

Personal life area. `TASKS.md` holds its pending items.
"""


def render(text: str, meta: dict) -> str:
    """Fill {{key}} placeholders. Deliberately not str.format: a user template
    full of literal braces (code samples, dataview queries) must survive."""
    for key, value in meta.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def load_template(vault: Path, name: str, builtin: str) -> str:
    """Hard rule 6: scaffold from _templates/ when the file is there."""
    candidate = vault / TEMPLATES_DIR / f"{name}.md"
    return candidate.read_text(encoding="utf-8") if candidate.exists() else builtin


def resolve_vault(args, must_exist=True) -> Path:
    raw = args.vault or os.environ.get("OBSIDIAN_VAULT")
    if not raw:
        sys.exit("No vault given. Pass --vault PATH or set OBSIDIAN_VAULT.")
    vault = Path(raw).expanduser().resolve()
    if must_exist and not vault.is_dir():
        sys.exit(f"Vault not found: {vault}")
    return vault


def require(args, *fields) -> dict:
    """Hard rule 6: missing metadata is an error, never a silent placeholder."""
    missing = [f for f in fields if not getattr(args, f, None)]
    if missing:
        sys.exit("Missing required metadata: "
                 + ", ".join(f"--{f.replace('_', '-')}" for f in missing)
                 + "\nAsk for it instead of scaffolding a folder with holes in it.")
    return {f: getattr(args, f) for f in fields}


class Plan:
    """Collects everything a command would write, so --dry-run and the real run
    walk exactly the same path."""

    def __init__(self, vault: Path, dry_run: bool):
        self.vault = vault
        self.dry_run = dry_run
        self.dirs: list[Path] = []
        self.files: list[tuple[Path, str]] = []
        self.log_line = ""
        self.index_entry = ("", "")

    def mkdir(self, path: Path):
        self.dirs.append(path)

    def write(self, path: Path, content: str):
        if path.exists():
            sys.exit(f"Refusing to overwrite an existing file: {self.rel(path)}")
        self.files.append((path, content))

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.vault)).replace("\\", "/")
        except ValueError:
            return str(path)

    def log(self, area: str, action: str):
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.log_line = f"{stamp} | {area} | {action}"

    def index(self, section: str, entry: str):
        self.index_entry = (section, entry)

    def commit(self):
        print("Vault:", self.vault)
        for d in self.dirs:
            print(f"  dir   {self.rel(d)}/")
        for path, _ in self.files:
            print(f"  file  {self.rel(path)}")
        if self.log_line:
            print(f"  log   {self.log_line}")
        if self.index_entry[1]:
            print(f"  index [{self.index_entry[0]}] {self.index_entry[1]}")

        if self.dry_run:
            print("\n--dry-run: nothing was written.")
            return

        for d in self.dirs:
            d.mkdir(parents=True, exist_ok=True)
        for path, content in self.files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        if self.log_line:
            append_log(self.vault, self.log_line)
        if self.index_entry[1]:
            append_index(self.vault, *self.index_entry)
        print("\nDone.")


def append_log(vault: Path, line: str):
    """Hard rule 3: append-only, one line, never edit what is already there."""
    log = vault / "log.md"
    prefix = "" if not log.exists() or log.read_text(encoding="utf-8").endswith("\n") else "\n"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(prefix + line + "\n")


def append_index(vault: Path, section: str, entry: str):
    """Hard rule 4: keep index.md current. Inserts under the section heading
    when it exists, otherwise appends the heading at the end."""
    index = vault / "index.md"
    if not index.exists():
        index.write_text(f"---\ntype: indice\n---\n\n# Index\n\n## {section}\n\n{entry}\n",
                         encoding="utf-8")
        return

    lines = index.read_text(encoding="utf-8").splitlines()
    heading = f"## {section}"
    if heading not in lines:
        lines += ["", heading, "", entry]
    else:
        start = lines.index(heading) + 1
        end = start
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        # Sit right after the last bullet of the section, before its blank tail.
        insert = end
        while insert > start and not lines[insert - 1].strip():
            insert -= 1
        lines.insert(insert, entry)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_init(args):
    vault = resolve_vault(args, must_exist=False)
    plan = Plan(vault, args.dry_run)

    for name in AREA_DIRS.values():
        plan.mkdir(vault / name)
    plan.mkdir(vault / TEMPLATES_DIR)

    for name, body in (("course", COURSE_TEMPLATE),
                       ("project", PROJECT_TEMPLATE),
                       ("area", AREA_TEMPLATE),
                       ("tasks", TASKS_TEMPLATE)):
        target = vault / TEMPLATES_DIR / f"{name}.md"
        if not target.exists():
            plan.write(target, body)

    for name, body in (("index.md", "---\ntype: indice\n---\n\n# Index\n"),
                       ("log.md", "# Log\n\nAppend-only. One line per structural change.\n\n")):
        if not (vault / name).exists():
            plan.write(vault / name, body)

    plan.commit()


def cmd_course(args):
    vault = resolve_vault(args)
    meta = require(args, "name", "semester", "professor", "schedule", "grading")
    meta["title"] = meta["name"]

    root = vault / AREA_DIRS["university"] / meta["semester"] / meta["name"]
    if root.exists():
        sys.exit(f"Course already exists: {root}. Nothing was touched.")

    plan = Plan(vault, args.dry_run)
    plan.mkdir(root)
    for sub in COURSE_SUBDIRS:
        plan.mkdir(root / sub)
    plan.write(root / "_course.md", render(load_template(vault, "course", COURSE_TEMPLATE), meta))
    plan.write(root / "TASKS.md", render(load_template(vault, "tasks", TASKS_TEMPLATE), meta))
    plan.log(f"university/{meta['semester']}/{meta['name']}", "course scaffolded")
    plan.index("Courses", f"- [[{plan.rel(root)}/_course.md|{meta['name']}]]"
                          f" — {meta['semester']}, {meta['professor']}")
    plan.commit()


def cmd_project(args):
    vault = resolve_vault(args)
    meta = require(args, "name", "repo")
    meta["title"] = meta["name"]
    meta["summary"] = args.summary or "TODO: one paragraph on what this project is."

    root = vault / AREA_DIRS["professional"] / meta["name"]
    if root.exists():
        sys.exit(f"Project already exists: {root}. Nothing was touched.")

    plan = Plan(vault, args.dry_run)
    plan.mkdir(root)
    for sub in PROJECT_SUBDIRS:
        plan.mkdir(root / sub)
    plan.mkdir(root / "code" / meta["repo"])
    plan.write(root / "_project.md", render(load_template(vault, "project", PROJECT_TEMPLATE), meta))
    plan.write(root / "TASKS.md", render(load_template(vault, "tasks", TASKS_TEMPLATE), meta))
    plan.log(f"professional/{meta['name']}", "project scaffolded")
    plan.index("Projects", f"- [[{plan.rel(root)}/_project.md|{meta['name']}]]"
                           f" — repo `code/{meta['repo']}`")
    plan.commit()


def cmd_area(args):
    vault = resolve_vault(args)
    meta = require(args, "name")
    meta["title"] = meta["name"]

    root = vault / AREA_DIRS["personal"] / meta["name"]
    if root.exists():
        sys.exit(f"Area already exists: {root}. Nothing was touched.")

    plan = Plan(vault, args.dry_run)
    plan.mkdir(root)
    plan.mkdir(root / "attachments")
    plan.write(root / "_area.md", render(load_template(vault, "area", AREA_TEMPLATE), meta))
    plan.write(root / "TASKS.md", render(load_template(vault, "tasks", TASKS_TEMPLATE), meta))
    plan.log(f"personal/{meta['name']}", "area scaffolded")
    # Points at TASKS.md, not _area.md: vault_scan's ENTRY_FILES only knows
    # _course.md / _project.md / TASKS.md, and a link it cannot resolve makes
    # the whole area invisible to planning.
    plan.index("Personal areas", f"- [[{plan.rel(root)}/TASKS.md|{meta['name']}]]")
    plan.commit()


def cmd_list(args):
    vault = resolve_vault(args)
    uni = vault / AREA_DIRS["university"]
    out = {
        "vault": str(vault),
        "courses": sorted(
            f"{sem.name}/{course.name}"
            for sem in uni.iterdir() if sem.is_dir()
            for course in sem.iterdir() if course.is_dir()
        ) if uni.is_dir() else [],
        "projects": sorted(
            p.name for p in (vault / AREA_DIRS["professional"]).iterdir() if p.is_dir()
        ) if (vault / AREA_DIRS["professional"]).is_dir() else [],
        "areas": sorted(
            p.name for p in (vault / AREA_DIRS["personal"]).iterdir() if p.is_dir()
        ) if (vault / AREA_DIRS["personal"]).is_dir() else [],
    }
    # Hard rule 1: a folder without TASKS.md is a bug, so make it visible.
    missing = []
    for rel, base in (("courses", uni), ("projects", vault / AREA_DIRS["professional"]),
                      ("areas", vault / AREA_DIRS["personal"])):
        for item in out[rel]:
            if not (base / item / "TASKS.md").exists():
                missing.append(f"{base.name}/{item}")
    out["missing_tasks_md"] = missing
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vault", help="Vault root (or set OBSIDIAN_VAULT)")
    p.add_argument("--dry-run", action="store_true", help="Print the plan, write nothing")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("list")

    s = sub.add_parser("course")
    s.add_argument("--name", required=True)
    s.add_argument("--semester", help="e.g. 2026-2")
    s.add_argument("--professor")
    s.add_argument("--schedule", help='e.g. "Tue 10:00-12:00, Thu 08:00-10:00"')
    s.add_argument("--grading", help='e.g. "Parcial 30%%, Talleres 30%%, Proyecto 40%%"')

    s = sub.add_parser("project")
    s.add_argument("--name", required=True)
    s.add_argument("--repo", help="Repo folder name under code/")
    s.add_argument("--summary", default="")

    s = sub.add_parser("area")
    s.add_argument("--name", required=True)

    args = p.parse_args()
    {
        "init": cmd_init,
        "course": cmd_course,
        "project": cmd_project,
        "area": cmd_area,
        "list": cmd_list,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
