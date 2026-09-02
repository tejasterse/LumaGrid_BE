# LightWatch — single-village MVP

Streetlight tracking for one Gram Panchayat: an inventory, a WhatsApp reporting flow,
and an admin dashboard. See [`SPEC.md`](./SPEC.md) for the full build spec — that file
is written to be handed directly to an AI coding agent (Antigravity, Claude Code, etc.)
as its source of truth.

## Project layout

```
lightwatch-mvp/
├── SPEC.md                          <- read this first, it's the actual spec
├── backend/
│   ├── requirements.txt
│   └── app/                         <- FastAPI app goes here
├── data/
│   └── dummy_streetlights.csv       <- sample data matching the streetlights schema
├── docs/
│   └── field-survey-log-template.md <- printable log sheet for the real Week 1 survey
└── frontend/                        <- admin dashboard goes here
```

## Getting this running in Antigravity

1. Unzip this folder somewhere on disk, then in Antigravity: **File → Open Folder** and
   select `lightwatch-mvp/`.
2. Open `SPEC.md` first — pin it or keep it visible, since it's the spec the agent should work from.
3. Start a task with the agent along these lines, rather than "build the whole thing":

   > Read SPEC.md fully. Then build only stage 1 from the "working style" section:
   > the SQLAlchemy models and DB setup, and a script to load data/dummy_streetlights.csv
   > into it. Stop after that and show me the result before continuing.

4. Review what it produces, run it, then move to the next stage with a similarly scoped prompt:

   > Now build stage 2: the FastAPI CRUD endpoints listed in SPEC.md. Don't touch the
   > WhatsApp or frontend pieces yet.

   Going stage-by-stage like this (rather than "build the whole MVP") is what "proceed
   one by one" should look like in practice — it keeps each change reviewable, and it
   matches how the SPEC's own "working style" section is written.

5. Antigravity's Manager/Mission Control view lets you run these stages as separate agent
   tasks if you want to review each one's plan and artifacts (screenshots, terminal output)
   before it proceeds — worth using for stage 3 onward, since the WhatsApp webhook and the
   dashboard are the two places most likely to need correcting.

## Local setup (once the agent has scaffolded backend/)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## What's already decided (don't relitigate these in prompts)

- Postgres in production, SQLite fine for local dev — no PostGIS, the dataset is too small to need it
- Leaflet + OpenStreetMap tiles, not Mapbox — avoids API billing at this scale
- WhatsApp reporting via a webhook (Twilio or Gupshup), not a dedicated app
- No AI/CV in this MVP — that's a separate future project, see `SPEC.md`'s "explicitly out of scope"

## Status

- [ ] Stage 1 — DB models + dummy data loaded
- [ ] Stage 2 — Backend CRUD endpoints
- [ ] Stage 3 — WhatsApp webhook (mocked until real credentials exist)
- [ ] Stage 4 — Admin dashboard
- [ ] Stage 5 — End-to-end test with dummy data
- [ ] Real Week 1 field survey data replaces `dummy_streetlights.csv`
