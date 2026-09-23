# Google Calendar helper (direct API)

One-time setup:
1. https://console.cloud.google.com -> new project -> enable BOTH
   **Google Calendar API** and **Google Tasks API** (auth.py requests both;
   with only one enabled the consent succeeds but half the commands fail)
2. OAuth consent screen: External, add your Gmail as **test user**. Under
   *Data access*, declare only the three scopes listed below.
3. Credentials -> Create credentials -> **OAuth client ID** -> Desktop app
4. Download the JSON, save it as `secrets/credentials.json` (folder is gitignored)
5. From the repo root: `pip install -r requirements.txt` (shared with the rest of
   the app, not local to this folder)
6. `python gcal.py auth`  (browser opens once; `secrets/token.json` is stored there)
7. `cp config.example.json config.json`, then fill the IDs with the output of
   `python gcal.py calendars` and `python gcal.py tasklists`. `config.json` is
   gitignored: IDs never go to git.

## Scopes (least privilege)

| Scope | Used for |
|---|---|
| `calendar.readonly` | list calendars, read events, free/busy |
| `calendar.events` | insert events (`apply`) |
| `tasks` | list and insert Google Tasks |

Google has no insert-only scope: `calendar.events` still allows deleting events
through the API. What the narrower set removes is deleting whole calendars and
changing their sharing, which the old full `calendar` scope allowed. gcal.py
itself has no delete or move command. A `token.json` created with the old scope
is detected and the browser asks once for the new consent.

## config.json

| Key | Meaning |
|---|---|
| `vault_path` | Vault folder, relative to this directory (default `../../vault`) |
| `private_paths` | Vault folders `scan` never walks into |
| `timezone` | IANA zone for every date and time |
| `areas` | area → vault `folder`, `calendar` ID, `tasklist` ID |
| `default_area` | Area for anything outside the listed folders |
| `read_only_calendars` | Extra calendars read as busy time: `busy` = `true`, `false` or `"negotiable"` |
| `policy` | The scheduling rules `check` enforces: earliest start, min/max block, break, all-day events |

## Planning flow

```
python gcal.py scan                                   # tasks from every area in vault/index.md
python gcal.py busy  --start 2026-09-28 --end 2026-10-05
python gcal.py check ../../vault/.plans/2026-09-28.json --table
python gcal.py apply ../../vault/.plans/2026-09-28.json --approved <code from check>
```

The AI writes the plan (schema in `planner.py` and in the `plan-week` skill);
`check` validates it against `policy` and the real calendar, splits blocks that
collide and prints an approval code. `apply` re-checks and writes only if that
code still matches. Every event gets a deterministic id plus private extended
properties, so re-running `apply` never duplicates anything.

Tests (no network): `.venv/bin/python -m unittest discover -s _scripts/gcal/tests`
from the repo root.

NEVER commit `credentials.json`, `token.json` or `config.json`.
