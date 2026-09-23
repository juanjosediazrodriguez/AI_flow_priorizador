"""planner.check_plan / apply_plan: schema, policy, repair and idempotency.

Run from the repo root:  .venv/bin/python -m unittest discover -s _scripts/gcal/tests
"""

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import planner  # noqa: E402

CFG = {
    "timezone": "America/Bogota",
    "default_area": "personal",
    "areas": {
        "personal": {"folder": "20-personal", "calendar": "primary", "tasklist": "@default"},
        "university": {"folder": "10-university", "calendar": "uni@group", "tasklist": "uni-list"},
    },
    "policy": {
        "earliest_start": "09:00",
        "block_min_minutes": 30,
        "block_max_minutes": 120,
        "preferred_block_minutes": [90, 120],
        "break_minutes": 15,
        "all_day_events_block": False,
    },
}
TODAY = date(2026, 9, 22)


def block(**over):
    b = {
        "task": "Laboratorio 3: árbol AVL",
        "ctx": "10-university/2026-2/estructuras-de-datos/assignments/lab-3-avl.md",
        "area": "university",
        "date": "2026-09-24",
        "start": "14:00",
        "end": "16:00",
        "priority": "high",
        "reason": "Vale 10 % y las rotaciones dobles toman tiempo.",
    }
    b.update(over)
    return b


def plan(*blocks, confirm=False):
    return {"requires_confirmation": confirm, "notes": "", "blocks": list(blocks)}


def event(title, start, end, **extra):
    return {"title": title, "start": start, "end": end, **extra}


def hours(row):
    return [(p["start"], p["end"]) for p in row["pieces"]]


class SchemaTest(unittest.TestCase):
    def test_free_block_is_ready(self):
        r = planner.check_plan(plan(block()), [], CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.READY)
        self.assertEqual(len(r["to_insert"]), 1)
        self.assertIsNotNone(r["review_hash"])

    def test_extra_block_field_is_rejected(self):
        r = planner.check_plan(plan(block(duration=120)), [], CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.REJECTED)
        self.assertIn("fuera del esquema", r["rows"][0]["detail"][0])
        self.assertIsNone(r["review_hash"])

    def test_extra_plan_field_rejects_everything(self):
        raw = plan(block())
        raw["prioridad"] = "alta"
        r = planner.check_plan(raw, [], CFG, TODAY)
        self.assertTrue(r["plan_errors"])
        self.assertEqual(r["rows"][0]["status"], planner.REJECTED)
        self.assertEqual(r["to_insert"], [])

    def test_bad_values(self):
        for over in ({"date": "2026-02-30"}, {"start": "7:00"}, {"end": "13:00"},
                     {"priority": "alta"}, {"area": "gym"}, {"reason": ""}):
            with self.subTest(over=over):
                r = planner.check_plan(plan(block(**over)), [], CFG, TODAY)
                self.assertEqual(r["rows"][0]["status"], planner.REJECTED)

    def test_past_date_is_rejected(self):
        r = planner.check_plan(plan(block(date="2026-09-21")), [], CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.REJECTED)
        self.assertIn("ya pasó", r["rows"][0]["detail"][0])

    def test_not_a_plan(self):
        r = planner.check_plan(["no"], [], CFG, TODAY)
        self.assertTrue(r["plan_errors"])
        self.assertIsNone(r["review_hash"])


class PolicyTest(unittest.TestCase):
    def test_collision_splits_instead_of_discarding(self):
        # The notebook's case: a 1 h tutoring session in the middle of a 4 h window.
        ev = [event("Monitoría de Cálculo", "2026-09-24T15:00:00-05:00", "2026-09-24T16:00:00-05:00")]
        r = planner.check_plan(plan(block(start="14:00", end="18:00")), ev, CFG, TODAY)
        row = r["rows"][0]
        self.assertEqual(row["status"], planner.SPLIT)
        self.assertEqual(hours(row), [("14:00", "15:00"), ("16:00", "18:00")])
        self.assertIn("Monitoría", row["detail"][0])

    def test_long_block_is_chopped_with_break(self):
        r = planner.check_plan(plan(block(start="14:00", end="18:00")), [], CFG, TODAY)
        self.assertEqual(hours(r["rows"][0]), [("14:00", "16:00"), ("16:15", "18:00")])

    def test_nothing_before_earliest_start(self):
        r = planner.check_plan(plan(block(start="08:00", end="10:00")), [], CFG, TODAY)
        self.assertEqual(hours(r["rows"][0]), [("09:00", "10:00")])
        self.assertIn("antes de las 09:00", r["rows"][0]["detail"][0])

    def test_all_day_events_follow_policy(self):
        ev = [event("Semana de parciales", "2026-09-24", "2026-09-25")]
        r = planner.check_plan(plan(block()), ev, CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.READY)
        strict = copy.deepcopy(CFG)
        strict["policy"]["all_day_events_block"] = True
        r = planner.check_plan(plan(block()), ev, strict, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.REJECTED)

    def test_negotiable_event_only_warns(self):
        ev = [event("Gym", "2026-09-24T15:00:00-05:00", "2026-09-24T16:00:00-05:00", negotiable=True)]
        r = planner.check_plan(plan(block()), ev, CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.READY)
        self.assertIn("pisa Gym (negociable)", r["rows"][0]["detail"])

    def test_blocks_of_the_same_plan_keep_a_break(self):
        r = planner.check_plan(
            plan(block(), block(task="Quiz 2", ctx="", start="15:00", end="17:00")), [], CFG, TODAY)
        self.assertEqual(hours(r["rows"][1]), [("16:15", "17:00")])

    def test_too_short_is_rejected(self):
        r = planner.check_plan(plan(block(start="14:00", end="14:20")), [], CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.REJECTED)

    def test_requires_confirmation_schedules_nothing(self):
        r = planner.check_plan(plan(block(), confirm=True), [], CFG, TODAY)
        self.assertEqual(r["rows"][0]["status"], planner.CONFIRM)
        self.assertEqual(r["to_insert"], [])
        self.assertIsNone(r["review_hash"])


def as_calendar_events(pieces):
    """What `busy` returns after apply inserted these pieces."""
    return [event(p["task"], f"{p['date']}T{p['start']}:00-05:00", f"{p['date']}T{p['end']}:00-05:00",
                  afp_block=p["id"], afp_src=p["src"]) for p in pieces]


class IdempotencyTest(unittest.TestCase):
    def setUp(self):
        self.raw = plan(block(start="14:00", end="18:00"),
                        block(task="Quiz 2", ctx="", date="2026-09-25", start="10:00", end="11:30"))
        self.first = planner.check_plan(self.raw, [], CFG, TODAY)

    def test_ids_are_valid_calendar_ids(self):
        for p in self.first["to_insert"]:
            self.assertRegex(p["id"], r"^[a-v0-9]{5,1024}$")

    def test_recheck_after_apply_finds_everything_scheduled(self):
        again = planner.check_plan(self.raw, as_calendar_events(self.first["to_insert"]), CFG, TODAY)
        self.assertEqual(again["to_insert"], [])
        self.assertEqual(again["already_scheduled"], 3)
        self.assertTrue(all(r["status"] == planner.EXISTS for r in again["rows"]))
        # Same approval code: a retry after a partial apply is still the approved plan.
        self.assertEqual(again["review_hash"], self.first["review_hash"])

    def test_partial_apply_retry_inserts_only_the_rest(self):
        done = as_calendar_events(self.first["to_insert"][:1])
        inserted = []
        result = planner.apply_plan(self.raw, done, CFG, TODAY, self.first["review_hash"],
                                    lambda p: inserted.append(p["id"]) or "inserted")
        self.assertTrue(result["ok"])
        self.assertEqual(len(inserted), 2)
        self.assertEqual(result["existed"], 1)

    def test_apply_refuses_a_different_plan(self):
        edited = copy.deepcopy(self.raw)
        edited["blocks"][1]["start"] = "10:30"
        result = planner.apply_plan(edited, [], CFG, TODAY, self.first["review_hash"],
                                    lambda p: self.fail("must not insert"))
        self.assertFalse(result["ok"])
        self.assertIn("cambió", result["error"])

    def test_apply_refuses_when_calendar_changed(self):
        ev = [event("Clase nueva", "2026-09-25T10:00:00-05:00", "2026-09-25T11:00:00-05:00")]
        result = planner.apply_plan(self.raw, ev, CFG, TODAY, self.first["review_hash"],
                                    lambda p: self.fail("must not insert"))
        self.assertFalse(result["ok"])

    def test_google_conflict_counts_as_existing(self):
        result = planner.apply_plan(self.raw, [], CFG, TODAY, self.first["review_hash"], lambda p: "exists")
        self.assertTrue(result["ok"])
        self.assertEqual(result["inserted"], [])
        self.assertEqual(result["existed"], 3)


if __name__ == "__main__":
    unittest.main()
