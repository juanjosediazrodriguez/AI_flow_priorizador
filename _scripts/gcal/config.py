"""Local configuration: vault location, area routing, calendars and planning policy.

config.json holds the user's calendar and task-list IDs, so it is gitignored;
config.example.json is the committed template. This file is the ONLY place the
planning policy lives — the skill and the validator both read it from here.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "config.json"
EXAMPLE_FILE = HERE / "config.example.json"

POLICY_KEYS = {
    "earliest_start": str,
    "block_min_minutes": int,
    "block_max_minutes": int,
    "preferred_block_minutes": list,
    "break_minutes": int,
    "all_day_events_block": bool,
}
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def load_config(path=None) -> dict:
    """Read and validate config.json (or `path`). Exits with a fix-it message on error."""
    path = Path(path) if path else CONFIG_FILE
    if not path.exists():
        sys.exit(
            f"{path.name} not found. Copy {EXAMPLE_FILE.name} to config.json and "
            "fill in your IDs (list them with `gcal.py calendars` and `gcal.py tasklists`)."
        )
    cfg = json.loads(path.read_text())
    errors = validate_config(cfg)
    if errors:
        sys.exit(f"{path.name} is invalid:\n  - " + "\n  - ".join(errors))
    cfg["_dir"] = path.resolve().parent
    return cfg


def validate_config(cfg: dict) -> list:
    errors = []
    for key in ("vault_path", "timezone", "default_area", "areas", "policy"):
        if key not in cfg:
            errors.append(f"missing key '{key}'")
    areas = cfg.get("areas") or {}
    for name, a in areas.items():
        for key in ("folder", "calendar", "tasklist"):
            if not isinstance(a.get(key), str) or not a.get(key):
                errors.append(f"areas.{name}.{key} must be a non-empty string")
    if cfg.get("default_area") not in areas:
        errors.append("default_area must be one of the keys in 'areas'")
    for i, c in enumerate(cfg.get("read_only_calendars") or []):
        if not c.get("id") or c.get("busy") not in (True, False, "negotiable"):
            errors.append(f"read_only_calendars[{i}] needs 'id' and 'busy' (true | false | \"negotiable\")")
    policy = cfg.get("policy") or {}
    for key, typ in POLICY_KEYS.items():
        if not isinstance(policy.get(key), typ) or (typ is int and isinstance(policy.get(key), bool)):
            errors.append(f"policy.{key} must be {typ.__name__}")
    if isinstance(policy.get("earliest_start"), str) and not HHMM.match(policy["earliest_start"]):
        errors.append("policy.earliest_start must be HH:MM")
    if not errors and policy["block_min_minutes"] > policy["block_max_minutes"]:
        errors.append("policy.block_min_minutes cannot exceed block_max_minutes")
    return errors


def vault_dir(cfg: dict) -> Path:
    return (Path(cfg.get("_dir", HERE)) / cfg["vault_path"]).resolve()


def area_for_path(cfg: dict, rel_path: str) -> str:
    """Area whose folder is the longest prefix of `rel_path` (vault-relative)."""
    rel = rel_path.strip("/") + "/"
    best, best_len = cfg["default_area"], -1
    for name, a in cfg["areas"].items():
        folder = a["folder"].strip("/") + "/"
        if rel.startswith(folder) and len(folder) > best_len:
            best, best_len = name, len(folder)
    return best


def area(cfg: dict, name: str) -> dict:
    if name not in cfg["areas"]:
        sys.exit(f"Unknown area '{name}'. Valid areas: {', '.join(cfg['areas'])}")
    return cfg["areas"][name]


def require_real_id(value: str, what: str) -> str:
    """Refuse to call Google with a placeholder copied from config.example.json."""
    if value.startswith("<"):
        sys.exit(f"{what} is still a placeholder ({value}). Replace it in config.json.")
    return value


def read_calendars(cfg: dict) -> list:
    """Every calendar that counts as busy time: all area calendars plus read-only
    ones whose `busy` is true or "negotiable". De-duplicated by ID."""
    seen, out = set(), []
    for name, a in cfg["areas"].items():
        if a["calendar"] not in seen:
            seen.add(a["calendar"])
            out.append({"name": name, "id": a["calendar"], "negotiable": False})
    for c in cfg.get("read_only_calendars") or []:
        if c["busy"] is False or c["id"] in seen:
            continue
        seen.add(c["id"])
        out.append({"name": c.get("name", c["id"]), "id": c["id"], "negotiable": c["busy"] == "negotiable"})
    return out
