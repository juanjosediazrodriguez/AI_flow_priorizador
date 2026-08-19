# Google Calendar helper (direct API)

One-time setup:
1. https://console.cloud.google.com -> new project -> enable **Google Calendar API**
2. OAuth consent screen: External, add your Gmail as **test user**
3. Credentials -> Create credentials -> **OAuth client ID** -> Desktop app
4. Download the JSON, save it as `secrets/credentials.json` (folder is gitignored)
5. `pip install -r requirements.txt`
6. `python gcal.py auth`  (browser opens once; `secrets/token.json` is stored there)

Usage:
```
python gcal.py pull   --start 2026-08-10T00:00:00 --end 2026-08-17T00:00:00
python gcal.py free   --start 2026-08-10T00:00:00 --end 2026-08-17T00:00:00
python gcal.py insert --title "Deep work: TCP lab" \
    --start 2026-08-11T08:00:00 --end 2026-08-11T10:00:00 \
    --desc "vault:10-university/2026-2/networks/assignments/lab2-tcp.md"
```
Timezone defaults to America/Bogota; naive datetimes are assumed -05:00.

NEVER commit `credentials.json` or `token.json`.
