# LightWatch — Single-Village MVP Spec

This is the source of truth for what to build. Read this fully before writing code.
Build only what's described in "MVP scope" below. Everything in "Explicitly out of scope"
is a future phase — do not build it, do not scaffold placeholders for it, do not add
config for it "just in case."

## What this is

A minimal streetlight tracking system for one Indian village. It has three parts:

1. A `streetlights` inventory (loaded from a real field survey — dummy data provided for now)
2. A way for citizens to report a broken light via WhatsApp
3. An admin dashboard (map + ticket list) for whoever manages the Gram Panchayat's lights

No computer vision, no night-video analysis, no predictive maintenance. Those are
real longer-term ideas but are not part of this MVP.

## Data model

Implement exactly these tables (SQLAlchemy models, Postgres in production / SQLite fine for local dev):

```
streetlights
 ├── id (string PK, e.g. "SL-AJG-001")
 ├── latitude (float)
 ├── longitude (float)
 ├── location_note (string)        -- e.g. "near primary school gate"
 ├── pole_type (string)            -- concrete / metal / wood
 ├── fixture_type (string)         -- LED / CFL / solar
 ├── installed_by (string, nullable)
 ├── install_date (date, nullable)
 └── current_status (string)       -- working / not_working / reported / unknown

reports
 ├── id (int PK, autoincrement)
 ├── streetlight_id (FK -> streetlights.id)
 ├── reporter_phone (string)
 ├── issue_type (string)           -- not_working / broken_pole / flickering / obstructed / wiring / other
 ├── photo_url (string, nullable)
 ├── notes (string, nullable)
 ├── timestamp (datetime)
 └── status (string)               -- new / verified / assigned / in_progress / resolved

maintenance
 ├── id (int PK, autoincrement)
 ├── report_id (FK -> reports.id)
 ├── assigned_to (string, nullable)
 ├── status (string)
 ├── repair_photo_url (string, nullable)
 ├── resolved_at (datetime, nullable)
 └── resolution_time_hours (float, nullable, computed on resolve)

near_sensitive_zones
 ├── streetlight_id (FK -> streetlights.id)
 ├── zone_type (string)            -- school / hospital / bus_stop / market / junction
 └── distance_m (float)
```

Do not add an `observations` table or any AI-confidence-score fields — that's v2.

## Backend (FastAPI)

Endpoints needed for MVP:

- `GET /streetlights` — list all, with current status
- `GET /streetlights/{id}` — one light + its report history
- `POST /streetlights` — add a light (used to load survey data)
- `POST /reports` — create a report (called by the WhatsApp webhook)
- `PATCH /reports/{id}` — update report status
- `GET /reports?status=` — filter open tickets, sortable by days-open
- `GET /risk-summary` — simple weighted score per zone: `(# not_working / total lights in that stretch) * sensitivity_weight`. Not machine-learned — a plain formula. Document the weights you pick in a comment.

## WhatsApp reporting flow

Use a webhook-based bot (Twilio WhatsApp API or Gupshup — pick one, don't build both).
Flow:
1. Citizen sends photo + location pin to the LightWatch number
2. Bot asks issue type via numbered reply (1 not working / 2 broken pole / 3 flickering / 4 other)
3. Backend matches the GPS coordinate to the nearest `streetlights` row (simple haversine
   nearest-neighbor is enough — no need for PostGIS at this scale). If no light is within
   ~30m, create the report against a placeholder "unmatched" entry instead of failing silently.
4. `POST /reports` is called, a ticket is created
5. Bot replies with the ticket ID
6. When `maintenance.status` becomes `resolved`, bot sends the original reporter a
   before/after-style confirmation message

If Twilio/Gupshup credentials aren't available yet, build the webhook handler against a
mock/local endpoint that logs the payload, so the flow is provably correct and easy to
wire to a real account later.

## Admin dashboard (frontend)

Single page. No auth system needed for MVP (add a basic password gate at most).

- Map (Leaflet + OpenStreetMap tiles — no Mapbox billing needed at this scale) with
  streetlight pins colored by `current_status`
- Click a pin → panel with report history and photos
- Open-tickets list, sortable by days-open
- The `risk-summary` numbers shown per zone — labeled honestly as "risk score (formula-based)",
  not "AI risk score"

## Explicitly out of scope for this MVP

Do not build any of the following. Note them as TODOs in README if useful, nothing more:

- Night-time video / computer vision detection
- Repeated-observation confidence scoring
- Dark-zone segment detection
- Recurring-failure or predictive maintenance
- Weather correlation
- Worker mobile app / navigation
- Multi-village or multi-tenant support
- Any billing/subscription logic

## Working style

Build in this order and check in after each stage rather than doing everything at once:
1. Data models + DB setup, load the dummy CSV in `/data/dummy_streetlights.csv`
2. Backend CRUD endpoints
3. Mock WhatsApp webhook handler (logs instead of sending, until real credentials exist)
4. Admin dashboard reading from the backend
5. Wire dummy data through the full loop end to end

Prefer boring, well-known patterns over clever ones. This is a portfolio MVP for one
village, not infrastructure for scale.
