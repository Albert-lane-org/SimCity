# /simcity — Context Handoff

## What This Repo Is

**Public-facing creative updater** for the Albert Lane digital infrastructure.

SimCity is the public window into a private infrastructure project. It:
- Receives sanitized hourly dispatches from `albert-lane-org/roadmaps` (private)
- Applies recursive creative stylization and rewrites `README.md` each cycle
- Maintains a `creative-state.json` that accumulates design motifs and advances a narrative arc
- Attracts designers and collaborators to the project

**This repo is fully public. No proprietary information flows here.**

---

## Pipeline

```
RoadMaps (private) → simcity-dispatch.yml @ :00/hr
  → updates/latest.json  (sanitized payload, overwritten hourly)
    → [15 min gap]
      → creative-update.yml @ :15/hr
        → scripts/creative_engine.py
          → README.md       (rewritten each cycle)
          → creative-state.json  (advanced each cycle)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `updates/latest.json` | Sanitized hourly dispatch from RoadMaps |
| `updates/schema.md` | Documents the payload format |
| `creative-state.json` | Persistent narrative state (iteration, arc stage, motifs) |
| `scripts/creative_engine.py` | Reads state + update, writes README |
| `.github/workflows/creative-update.yml` | Hourly trigger at :15 past the hour |
| `README.md` | Auto-generated public output — do not edit manually |

---

## Workflow Schedule

| Workflow | Repo | Cron | Purpose |
|----------|------|------|---------|
| `simcity-dispatch.yml` | roadmaps | `0 * * * *` | Sanitize + push to SimCity |
| `creative-update.yml` | simcity | `15 * * * *` | Read dispatch, render README |

The 15-minute gap ensures the RoadMaps dispatch has landed before the
creative engine reads it.

---

## Evolving the Creative Engine

All creative parameters live in `scripts/creative_engine.py`:

- `ARC_STAGES[]` — six stages of city growth; add more to extend the arc
- `DESIGN_ROLES[]` — designer profiles; add new roles as the project's needs evolve
- `MOTIF_POOL[]` — design language that accumulates over time; add freely
- `advance_state()` — controls arc advancement rate and motif accumulation cadence

The `creative-state.json` persists between runs via main branch commits.
The workflow commits it alongside `README.md` each cycle.

---

## Required Secrets

SimCity's own workflow needs no secrets — it only reads its own files.
The `_ROADMAPS` secret lives in RoadMaps and is used by `simcity-dispatch.yml`
to push `updates/latest.json` across repos. That token needs write access to SimCity.

---

## Attribution

Every commit: `Co-authored-by: Claude Sonnet 4.6 <claude@anthropic.com>`
All IP belongs to Albert Lane per LICENSE.md.
