# Week 1 field survey log

Print this, or copy the table into a phone notes app / spreadsheet you can fill while walking.
One row per streetlight. Fill columns 1-6 during the daylight pass; fill "status" during
the separate evening pass (see the MVP spec, step 6).

Numbering scheme: `SL-<village code>-<sequence>`, e.g. `SL-AJG-001`.

| ID | GPS lat, long | Location note | Pole type | Fixture type | Photo filename | Status (fill at night) |
|----|---------------|----------------|-----------|---------------|-----------------|--------------------------|
| SL-___-001 |  |  |  |  |  |  |
| SL-___-002 |  |  |  |  |  |  |
| SL-___-003 |  |  |  |  |  |  |
| SL-___-004 |  |  |  |  |  |  |
| SL-___-005 |  |  |  |  |  |  |

(Duplicate the row above as many times as you need — one per light.)

## Field reference

**Pole type:** concrete / metal / wood
**Fixture type:** LED / CFL / solar — usually identifiable by fixture shape even without
markings: LED fixtures are flat panel-style, CFL are the older tube/bulb-in-housing look,
solar fixtures have a visible panel mounted near or above the lamp.
**Status:** working / not_working / flickering (record separately, decide up front whether
flickering counts as "not_working" for your dataset — see the MVP spec's note on this)

## Before you start

- [ ] Got informal buy-in from the Sarpanch/GP member
- [ ] Decided the definition of "not working" (fully dark only, or also flickering/dim)
- [ ] Split the village into 4-6 walkable zones
- [ ] Charged phone, enabled location services, checked storage space for photos

## End of each day

- [ ] Transferred today's rows into `data/streetlights_survey.csv` (same columns as
  `dummy_streetlights.csv` in this repo) so nothing is lost to a full notebook or dead phone
- [ ] Flagged any illegible/uncertain entries to re-check tomorrow
