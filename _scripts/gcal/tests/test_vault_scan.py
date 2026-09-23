"""vault_scan.scan: index-driven discovery and TASKS.md line parsing.

Run from the repo root:  .venv/bin/python -m unittest discover -s _scripts/gcal/tests
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vault_scan import parse_task_line, scan  # noqa: E402

CFG = {
    "default_area": "personal",
    "private_paths": ["20-personal/diary"],
    "areas": {
        "personal": {"folder": "20-personal", "calendar": "primary", "tasklist": "@default"},
        "university": {"folder": "10-university", "calendar": "u", "tasklist": "u"},
        "professional": {"folder": "30-professional", "calendar": "p", "tasklist": "p"},
    },
}
TODAY = date(2026, 9, 22)
TEMPLATE_COMMENT = """<!--
  - [ ] <title> | due:YYYY-MM-DD | est:<hours>h | prio:high|med|low | ctx:<relative/path.md>
-->
"""


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        self.write("index.md", """# Index
- **Datos** — [[10-university/2026-2/datos/_course|curso]] · [[10-university/2026-2/datos/TASKS|tasks]]
- **Web** — [proyecto](30-professional/web/_project.md)
- **Viejo** — [[10-university/2026-2/borrado/_course]]
""")
        self.write("10-university/2026-2/datos/_course.md", "# Datos")
        self.write("10-university/2026-2/datos/TASKS.md", "# Tasks\n" + TEMPLATE_COMMENT + """
- [ ] Lab AVL | due:2026-09-28 | est:5h | prio:high | ctx:10-university/2026-2/datos/lab avl.md
- [ ] Quiz | due:2026-09-20 | est:1h | prio:med
- [x] Lab listas | due:2026-09-14 | est:4h | prio:high
- [ ] Taller roto | due:28/09 | est:dos horas | prio:alta | tag:x
- [ ] Proyecto grande | due:2026-10-10 | est:6h
""")
        self.write("10-university/2026-2/datos/lab avl.md", "# Lab")
        self.write("30-professional/web/_project.md", "# Web")
        self.write("30-professional/web/TASKS.md", "- [ ] Deploy | due:2026-10-05 | ctx:notes/deploy.md\n")
        self.write("30-professional/web/notes/deploy.md", "# Deploy")
        self.write("30-professional/huerfano/TASKS.md", "- [ ] Nadie me ve | due:2026-10-01\n")
        self.write("20-personal/diary/TASKS.md", "- [ ] privado | due:2026-10-01\n")
        self.write("90-archive/viejo/TASKS.md", "- [ ] archivado | due:2026-01-01\n")
        self.result = scan(self.vault, CFG, TODAY)
        self.tasks = {t["title"]: t for t in self.result["tasks"]}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def test_areas_come_from_the_index_once_each(self):
        self.assertEqual([a["path"] for a in self.result["areas"]],
                         ["10-university/2026-2/datos", "30-professional/web"])
        self.assertEqual([a["area"] for a in self.result["areas"]], ["university", "professional"])

    def test_template_comment_and_done_tasks_are_skipped(self):
        self.assertNotIn("<title>", self.tasks)
        self.assertNotIn("Lab listas", self.tasks)
        self.assertEqual(self.result["areas"][0]["done"], 1)

    def test_valid_line(self):
        t = self.tasks["Lab AVL"]
        self.assertEqual((t["due"], t["days_left"], t["est_hours"], t["prio"]), ("2026-09-28", 6, 5.0, "high"))
        self.assertTrue(t["ctx_exists"])  # vault-relative path with a space
        self.assertEqual(t["issues"], [])

    def test_ctx_relative_to_the_area(self):
        self.assertEqual(self.tasks["Deploy"]["ctx"], "30-professional/web/notes/deploy.md")

    def test_overdue(self):
        self.assertTrue(self.tasks["Quiz"]["overdue"])

    def test_malformed_fields_are_reported_not_guessed(self):
        t = self.tasks["Taller roto"]
        self.assertIsNone(t["due"])
        self.assertIsNone(t["est_hours"])
        self.assertIsNone(t["prio"])
        self.assertEqual(len(t["issues"]), 4)

    def test_big_task_without_ctx_is_flagged(self):
        self.assertIn("est > 2h sin ctx", self.tasks["Proyecto grande"]["issues"][0])

    def test_vault_level_issues(self):
        issues = {(i["file"], i["issue"].split(":")[0]) for i in self.result["issues"]}
        self.assertIn(("index.md", "enlace roto"), issues)
        self.assertIn(("30-professional/huerfano/TASKS.md", "TASKS.md no está registrado en index.md"), issues)
        files = {i["file"] for i in self.result["issues"]}
        self.assertFalse(any(f.startswith(("20-personal/diary", "90-archive")) for f in files))

    def test_missing_index(self):
        (self.vault / "index.md").unlink()
        r = scan(self.vault, CFG, TODAY)
        self.assertEqual(r["tasks"], [])
        self.assertIn("index.md no existe", r["issues"][0]["issue"])


class LineTest(unittest.TestCase):
    def test_not_a_task(self):
        self.assertIsNone(parse_task_line("# Tasks — Datos"))
        self.assertIsNone(parse_task_line("- sin checkbox"))

    def test_duplicate_field(self):
        _, _, _, issues = parse_task_line("- [ ] X | due:2026-01-01 | due:2026-01-02")
        self.assertIn("'due' repetido", issues)


if __name__ == "__main__":
    unittest.main()
