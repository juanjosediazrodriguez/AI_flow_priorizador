"""Validate the weekly plan the AI proposes, before anything touches Google.

The agent writes plan.json with the FIXED schema below. This module parses it,
enforces config.policy, checks every block against the real calendar, repairs
the ones that collide (splits them instead of discarding good hours) and
returns a review table plus a hash of exactly what would be written. `apply`
only writes when the student approved that same hash.

The model proposes, the code validates, the student decides.

plan.json
{
  "requires_confirmation": false,          # true = the agent is not sure; nothing gets scheduled
  "notes": "string",                       # anything the student should know about the plan
  "blocks": [
    {
      "task": "Implementar árbol AVL",     # title of the TASKS.md line
      "ctx": "10-university/.../lab.md",   # vault-relative ctx note ("" if none)
      "area": "university",                # key of config.areas: routes the calendar
      "date": "2026-09-24",                # YYYY-MM-DD
      "start": "14:00", "end": "16:00",    # HH:MM, same day
      "priority": "high",                  # high | med | low
      "reason": "why this block, here"     # the explanation the student reviews
    }
  ]
}

Pure functions, no network: gcal.py feeds in the events fetched by `busy`.
"""

import hashlib
import json
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

PLAN_KEYS = {"requires_confirmation", "notes", "blocks"}
BLOCK_KEYS = {"task", "ctx", "area", "date", "start", "end", "priority", "reason"}
PRIORITIES = {"high", "med", "low"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

READY, SPLIT, REJECTED, CONFIRM, EXISTS = "LISTO", "PARTIDO", "RECHAZADO", "CONFIRMAR", "YA_EXISTE"
WEEKDAYS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


# ---------- schema ----------

def _block_errors(b, cfg) -> list:
    if not isinstance(b, dict):
        return [f"el bloque no es un objeto sino {type(b).__name__}"]
    errors = []
    missing, extra = BLOCK_KEYS - set(b), set(b) - BLOCK_KEYS
    if missing:
        errors.append(f"faltan campos: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"campos fuera del esquema: {', '.join(sorted(extra))}")
    if missing:
        return errors
    for key in ("task", "reason"):
        if not isinstance(b[key], str) or not b[key].strip():
            errors.append(f"'{key}' debe ser texto no vacío")
    if not isinstance(b["ctx"], str):
        errors.append("'ctx' debe ser texto (\"\" si no hay nota)")
    if b["area"] not in cfg["areas"]:
        errors.append(f"área desconocida '{b['area']}' (válidas: {', '.join(cfg['areas'])})")
    if b["priority"] not in PRIORITIES:
        errors.append(f"priority inválida '{b['priority']}' (high | med | low)")
    if not (isinstance(b["date"], str) and DATE_RE.match(b["date"])):
        errors.append(f"date inválida '{b['date']}' (YYYY-MM-DD)")
    else:
        try:
            date.fromisoformat(b["date"])
        except ValueError:
            errors.append(f"date no existe '{b['date']}'")
    times_ok = True
    for key in ("start", "end"):
        if not (isinstance(b[key], str) and TIME_RE.match(b[key])):
            errors.append(f"{key} inválido '{b[key]}' (HH:MM)")
            times_ok = False
    if times_ok and b["end"] <= b["start"]:
        errors.append("end debe ser posterior a start (el bloque no cruza la medianoche)")
    return errors


def parse_plan(raw, cfg):
    """(plan_errors, blocks). Plan-level errors reject the whole plan."""
    if not isinstance(raw, dict):
        return [f"el plan no es un objeto JSON sino {type(raw).__name__}"], []
    errors = []
    missing, extra = PLAN_KEYS - set(raw), set(raw) - PLAN_KEYS
    if missing:
        errors.append(f"faltan campos del plan: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"campos del plan fuera del esquema: {', '.join(sorted(extra))}")
    if "requires_confirmation" in raw and not isinstance(raw["requires_confirmation"], bool):
        errors.append("requires_confirmation debe ser true o false")
    if "notes" in raw and not isinstance(raw["notes"], str):
        errors.append("notes debe ser texto")
    blocks = raw.get("blocks")
    if not isinstance(blocks, list):
        errors.append("blocks debe ser una lista ([] si no hay nada que agendar)")
        blocks = []
    return errors, [{"raw": b, "errors": _block_errors(b, cfg)} for b in blocks]


# ---------- time helpers ----------

def _hm(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)


def _local(value: str, tz: ZoneInfo) -> datetime:
    """ISO datetime from Google -> naive local time in the configured zone."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(tz).replace(tzinfo=None) if dt.tzinfo else dt


def normalize_events(events: list, cfg: dict) -> list:
    """Events from `gcal.py busy` -> intervals the checker understands.
    All-day events are dropped unless policy.all_day_events_block is true."""
    tz = ZoneInfo(cfg["timezone"])
    keep_all_day = cfg["policy"]["all_day_events_block"]
    out = []
    for e in events:
        start, end = e.get("start"), e.get("end")
        if not start or not end:
            continue
        all_day = "T" not in start
        if all_day and not keep_all_day:
            continue
        if all_day:  # Google's all-day end date is exclusive
            s = datetime.combine(date.fromisoformat(start), time())
            f = datetime.combine(date.fromisoformat(end[:10]), time())
        else:
            s, f = _local(start, tz), _local(end, tz)
        out.append({
            "start": s, "end": f,
            "title": e.get("title") or "(sin título)",
            "negotiable": bool(e.get("negotiable")),
            "afp_block": e.get("afp_block"), "afp_src": e.get("afp_src"),
        })
    return out


# ---------- identity (idempotency) ----------

def _sha(*parts) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()


def source_id(b: dict, calendar_id: str) -> str:
    """Identity of a proposed block; its pieces carry it so a re-check ignores them."""
    return _sha(calendar_id, b["date"], b["start"], b["end"], b["task"], b["ctx"])[:16]


def piece_id(b: dict, calendar_id: str, start: datetime, end: datetime) -> str:
    """Deterministic Calendar event id. Base32hex (a-v, 0-9): hex digits qualify."""
    return "afp" + _sha(calendar_id, start.isoformat(), end.isoformat(), b["task"], b["ctx"])


# ---------- repair ----------

def _free_segments(start, end, blockers):
    segments, cursor = [], start
    for b_start, b_end in sorted(blockers):
        if b_end <= cursor or b_start >= end:
            continue
        if b_start > cursor:
            segments.append((cursor, min(b_start, end)))
        cursor = max(cursor, b_end)
    if cursor < end:
        segments.append((cursor, end))
    return segments


def split_block(start, end, blockers, policy):
    """Keep the free stretches of [start, end), chopped to the max length with a
    break between chunks; anything shorter than the minimum is dropped."""
    max_len = timedelta(minutes=policy["block_max_minutes"])
    min_len = timedelta(minutes=policy["block_min_minutes"])
    pause = timedelta(minutes=policy["break_minutes"])
    pieces = []
    for seg_start, seg_end in _free_segments(start, end, blockers):
        cursor = seg_start
        while cursor < seg_end:
            stop = min(cursor + max_len, seg_end)
            if stop - cursor >= min_len:
                pieces.append((cursor, stop))
            cursor = stop + pause
    return pieces


# ---------- check ----------

def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def check_plan(raw, events: list, cfg: dict, today: date) -> dict:
    policy = cfg["policy"]
    pause = timedelta(minutes=policy["break_minutes"])
    plan_errors, blocks = parse_plan(raw, cfg)
    confirm = isinstance(raw, dict) and raw.get("requires_confirmation") is True
    busy = normalize_events(events, cfg)
    existing = {e["afp_block"] for e in busy if e["afp_block"]}

    rows, pieces_out, planned = [], [], []
    for n, item in enumerate(blocks, 1):
        b = item["raw"]
        row = {"n": n, "status": None, "detail": [], "pieces": []}
        if isinstance(b, dict):
            row.update({k: b.get(k) for k in ("task", "area", "date", "start", "end", "priority")})
        rows.append(row)

        if plan_errors or item["errors"]:
            row["status"] = REJECTED
            row["detail"] = item["errors"] or ["el plan completo es inválido"]
            continue
        day = date.fromisoformat(b["date"])
        if day < today:
            row["status"], row["detail"] = REJECTED, [f"la fecha {b['date']} ya pasó"]
            continue

        calendar_id = cfg["areas"][b["area"]]["calendar"]
        src = source_id(b, calendar_id)
        start = datetime.combine(day, _hm(b["start"]))
        end = datetime.combine(day, _hm(b["end"]))
        earliest = datetime.combine(day, _hm(policy["earliest_start"]))

        hits = [e for e in busy
                if e["afp_src"] != src and _overlaps(start, end, e["start"], e["end"])]
        hard = [e for e in hits if not e["negotiable"]]
        soft = [e for e in hits if e["negotiable"]]
        blockers = [(e["start"], e["end"]) for e in hard]
        blockers.append((datetime.combine(day, time()), earliest))
        blockers += [(s - pause, f + pause) for s, f in planned]

        causes = [f"choca con {e['title']} ({e['start']:%H:%M}-{e['end']:%H:%M})" for e in hard]
        if start < earliest:
            causes.append(f"empieza antes de las {policy['earliest_start']}")
        if any(_overlaps(start, end, s - pause, f + pause) for s, f in planned):
            causes.append(f"se cruza con otro bloque del plan (descanso de {policy['break_minutes']} min)")
        if end - start > timedelta(minutes=policy["block_max_minutes"]):
            causes.append(f"dura más de {policy['block_max_minutes']} min")

        pieces = split_block(start, end, blockers, policy)
        if not pieces:
            row["status"] = REJECTED
            row["detail"] = causes or [f"dura menos de {policy['block_min_minutes']} min"]
            continue
        planned += pieces
        row["status"] = READY if pieces == [(start, end)] else SPLIT
        row["detail"] = ["libre en el calendario real"] if row["status"] == READY else causes
        row["detail"] += [f"pisa {e['title']} (negociable)" for e in soft]

        for s, f in pieces:
            pid = piece_id(b, calendar_id, s, f)
            piece = {
                "id": pid, "src": src, "calendar": calendar_id, "area": b["area"],
                "task": b["task"], "ctx": b["ctx"], "priority": b["priority"], "reason": b["reason"],
                "date": b["date"], "start": f"{s:%H:%M}", "end": f"{f:%H:%M}",
                "exists": pid in existing,
            }
            row["pieces"].append(piece)
            pieces_out.append(piece)

        if confirm:
            row["status"], row["detail"] = CONFIRM, ["el plan pidió confirmación (requires_confirmation=true)"]
        elif all(p["exists"] for p in row["pieces"]):
            row["status"], row["detail"] = EXISTS, ["ya está en el calendario; no se vuelve a crear"]

    approvable = [] if (plan_errors or confirm) else pieces_out
    review = {
        "plan_errors": plan_errors,
        "requires_confirmation": confirm,
        "notes": raw.get("notes", "") if isinstance(raw, dict) else "",
        "rows": rows,
        "to_insert": [p for p in approvable if not p["exists"]],
        "already_scheduled": sum(p["exists"] for p in approvable),
        # Hash of every approvable piece, inserted or not: a retry after a partial
        # apply still matches, and any change to the plan or calendar does not.
        "review_hash": _sha(*sorted(p["id"] for p in approvable))[:12] if approvable else None,
    }
    review["table"] = format_table(review)
    return review


# ---------- output ----------

def _day_label(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return str(iso)
    return f"{WEEKDAYS[d.weekday()]} {iso}"


def format_table(review: dict) -> str:
    """Markdown table the agent shows the student before asking for approval."""
    lines = []
    if review["plan_errors"]:
        lines.append("**Plan inválido:** " + "; ".join(review["plan_errors"]))
    lines += ["| # | Estado | Día | Horario | Área | Tarea | Detalle |",
              "|---|---|---|---|---|---|---|"]
    for r in review["rows"]:
        if r["pieces"]:
            hours = ", ".join(f"{p['start']}-{p['end']}" for p in r["pieces"])
        else:
            hours = f"{r.get('start')}-{r.get('end')}"
        detail = "; ".join(r["detail"]).replace("|", "/")
        task = str(r.get("task") or "?").replace("|", "/")
        lines.append(f"| {r['n']} | {r['status']} | {_day_label(r.get('date'))} | {hours} | "
                     f"{r.get('area') or '?'} | {task} | {detail} |")
    lines.append("")
    if review["review_hash"]:
        lines.append(f"Para agendar: {len(review['to_insert'])} evento(s) nuevo(s), "
                     f"{review['already_scheduled']} ya existían. Código de aprobación: `{review['review_hash']}`")
    else:
        lines.append("No hay nada que agendar.")
    return "\n".join(lines)


def apply_plan(raw, events, cfg, today, approved_hash: str, insert) -> dict:
    """Re-check against fresh events and write only if the student approved this
    exact review. `insert(piece)` returns "inserted" or "exists"."""
    review = check_plan(raw, events, cfg, today)
    if review["plan_errors"]:
        return {"ok": False, "error": "el plan es inválido: " + "; ".join(review["plan_errors"])}
    if review["requires_confirmation"]:
        return {"ok": False, "error": "el plan pide confirmación: corrígelo y vuelve a correr check"}
    if not review["review_hash"]:
        return {"ok": False, "error": "no hay bloques para agendar"}
    if review["review_hash"] != approved_hash:
        return {"ok": False, "error": (
            f"la propuesta cambió desde la aprobación (aprobado {approved_hash}, ahora {review['review_hash']}): "
            "corre check de nuevo y vuelve a pedir aprobación"), "table": review["table"]}
    results = [{**p, "result": insert(p)} for p in review["to_insert"]]
    return {
        "ok": True,
        "review_hash": review["review_hash"],
        "inserted": [r for r in results if r["result"] == "inserted"],
        "existed": review["already_scheduled"] + sum(r["result"] == "exists" for r in results),
    }


def load_plan(path) -> object:
    with open(path) as fh:
        return json.load(fh)
