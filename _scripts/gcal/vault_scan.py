"""Parse the vault's TASKS.md files, driven by index.md.

index.md is the registry of areas: every course or project it links to (its
_course.md, _project.md or TASKS.md) is scanned, and each task line becomes a
JSON object with its fields already validated. The agent plans from this output
instead of eyeballing dozens of files, so dates, estimates and priorities reach
the planner exactly as written — and a malformed line is reported, not guessed.

Task line format (see _templates/tasks.md):
  - [ ] <title> | due:YYYY-MM-DD | est:<hours>h | prio:high|med|low | ctx:<path.md>
ctx is resolved against the vault root first, then against the area folder.
"""

import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote

from config import area_for_path

ENTRY_FILES = {"_course.md", "_project.md", "TASKS.md"}
EXCLUDED_DIRS = {"90-archive"}
PRIORITIES = {"high", "med", "low"}

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
MDLINK = re.compile(r"\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)")
COMMENT = re.compile(r"<!--.*?-->", re.S)
TASK_LINE = re.compile(r"^\s*[-*] \[([ xX])\] (.*\S)\s*$")
DUE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EST = re.compile(r"^(\d+(?:\.\d+)?)h$")


def _without_comments(text: str) -> str:
    """Drop <!-- --> blocks but keep their newlines, so line numbers stay true.
    The TASKS.md template documents the format inside a comment."""
    return COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _rel(vault: Path, path: Path) -> str:
    return path.relative_to(vault).as_posix()


def index_links(index_text: str) -> list:
    """(target, line_no) for every wikilink and relative markdown link."""
    links = []
    for n, line in enumerate(_without_comments(index_text).splitlines(), 1):
        for m in WIKILINK.finditer(line):
            links.append((m.group(1).strip(), n))
        for m in MDLINK.finditer(line):
            target = unquote(m.group(1).strip("<>"))
            if not re.match(r"^[a-z]+:", target):
                links.append((target.removeprefix("./"), n))
    return links


def resolve_area(vault: Path, target: str):
    """Area folder a link points to, or None when the link is not an area entry.
    Returns (area_dir, broken) — broken is True for a dead link to an entry file."""
    base = vault / target
    candidates = [base] if base.suffix == ".md" else [base.with_name(base.name + ".md"), base]
    for c in candidates:
        if c.is_file():
            return (c.parent, False) if c.name in ENTRY_FILES else (None, False)
        if c.is_dir():
            has_entry = any((c / f).is_file() for f in ENTRY_FILES)
            return (c, False) if has_entry else (None, False)
    looks_like_entry = Path(target if target.endswith(".md") else target + ".md").name in ENTRY_FILES
    return None, looks_like_entry


def _resolve_ctx(vault: Path, area_dir: Path, value: str):
    value = value.strip().removeprefix("[[").removesuffix("]]").split("|")[0].strip()
    for root in (vault, area_dir):
        for c in (root / value, root / (value + ".md")):
            if c.is_file():
                return _rel(vault, c), True
    return value, False


def parse_task_line(text: str):
    """Split one task line into (done, title, raw fields, issues). None if not a task."""
    m = TASK_LINE.match(text)
    if not m:
        return None
    done = m.group(1) in "xX"
    parts = [p.strip() for p in re.split(r"\s+\|\s+", m.group(2))]
    title, fields, issues = parts[0], {}, []
    for part in parts[1:]:
        key, sep, value = part.partition(":")
        key = key.strip().lower()
        if not sep or key not in ("due", "est", "prio", "ctx"):
            issues.append(f"campo desconocido '{part}'")
        elif key in fields:
            issues.append(f"'{key}' repetido")
        else:
            fields[key] = value.strip()
    return done, title, fields, issues


def _task(vault, cfg, area_dir, tasks_file, line_no, parsed, today):
    done, title, fields, issues = parsed
    area_path = _rel(vault, area_dir)
    task = {
        "area": area_for_path(cfg, area_path),
        "area_path": area_path,
        "file": _rel(vault, tasks_file),
        "line": line_no,
        "done": done,
        "title": title,
        "due": None, "days_left": None, "overdue": False,
        "est_hours": None, "prio": None,
        "ctx": None, "ctx_exists": None,
        "issues": issues,
    }
    if not title:
        issues.append("tarea sin título")

    due = fields.get("due")
    if due is None:
        issues.append("sin due: no se puede ubicar en el calendario por fecha")
    elif DUE.match(due):
        try:
            d = date.fromisoformat(due)
            task["due"], task["days_left"] = due, (d - today).days
            task["overdue"] = not done and d < today
        except ValueError:
            issues.append(f"due inválido '{due}'")
    else:
        issues.append(f"due inválido '{due}' (usa YYYY-MM-DD)")

    est = fields.get("est")
    if est:  # est/prio can stay empty until planning
        m = EST.match(est)
        if m:
            task["est_hours"] = float(m.group(1))
        else:
            issues.append(f"est inválido '{est}' (usa p. ej. 3h o 1.5h)")

    prio = fields.get("prio")
    if prio:
        if prio in PRIORITIES:
            task["prio"] = prio
        else:
            issues.append(f"prio inválida '{prio}' (high | med | low)")

    ctx = fields.get("ctx")
    if ctx:
        task["ctx"], task["ctx_exists"] = _resolve_ctx(vault, area_dir, ctx)
        if not task["ctx_exists"]:
            issues.append(f"ctx no existe: {ctx}")
    elif task["est_hours"] and task["est_hours"] > 2:
        issues.append("est > 2h sin ctx: falta la nota que explica la tarea")
    return task


def _all_tasks_files(vault: Path, private: set):
    """Every TASKS.md in the vault, skipping archive, hidden and private folders
    (private folders are pruned before descending: their contents are never listed)."""
    for root, dirs, files in os.walk(vault):
        rel_root = _rel(vault, Path(root)) if Path(root) != vault else ""
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in EXCLUDED_DIRS
            and (f"{rel_root}/{d}".strip("/") not in private)
        ]
        if "TASKS.md" in files:
            yield Path(root) / "TASKS.md"


def scan(vault: Path, cfg: dict, today: date, include_done: bool = False) -> dict:
    vault = Path(vault).resolve()
    private = {p.strip("/") for p in cfg.get("private_paths") or []}
    result = {"vault": str(vault), "today": today.isoformat(), "areas": [], "tasks": [], "issues": []}
    index = vault / "index.md"
    if not index.is_file():
        result["issues"].append({"file": "index.md", "line": None, "issue": "index.md no existe: no hay áreas registradas"})
        return result

    area_dirs = []
    for target, line_no in index_links(index.read_text()):
        area_dir, broken = resolve_area(vault, target)
        if broken:
            result["issues"].append({"file": "index.md", "line": line_no, "issue": f"enlace roto: {target}"})
        if area_dir is None or area_dir in area_dirs:
            continue
        rel = _rel(vault, area_dir)
        if rel.split("/")[0] in EXCLUDED_DIRS or any(rel == p or rel.startswith(p + "/") for p in private):
            continue
        area_dirs.append(area_dir)

    for area_dir in area_dirs:
        rel = _rel(vault, area_dir)
        entry = next((f for f in ("_course.md", "_project.md") if (area_dir / f).is_file()), None)
        tasks_file = area_dir / "TASKS.md"
        summary = {"path": rel, "area": area_for_path(cfg, rel), "entry": entry, "open": 0, "done": 0}
        result["areas"].append(summary)
        if not tasks_file.is_file():
            result["issues"].append({"file": rel, "line": None, "issue": "el área no tiene TASKS.md"})
            continue
        lines = _without_comments(tasks_file.read_text()).splitlines()
        for n, line in enumerate(lines, 1):
            parsed = parse_task_line(line)
            if parsed is None:
                continue
            task = _task(vault, cfg, area_dir, tasks_file, n, parsed, today)
            summary["done" if task["done"] else "open"] += 1
            if include_done or not task["done"]:
                result["tasks"].append(task)

    indexed = {d / "TASKS.md" for d in area_dirs}
    for f in _all_tasks_files(vault, private):
        if f not in indexed:
            result["issues"].append({"file": _rel(vault, f), "line": None, "issue": "TASKS.md no está registrado en index.md"})

    result["summary"] = {
        "areas": len(result["areas"]),
        "open": sum(a["open"] for a in result["areas"]),
        "overdue": sum(t["overdue"] for t in result["tasks"]),
        "tasks_with_issues": sum(bool(t["issues"]) for t in result["tasks"]),
        "issues": len(result["issues"]),
    }
    return result
