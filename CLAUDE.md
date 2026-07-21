# /simcity — Context Handoff

## Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-07-21

---

## CRITICAL: Before Starting Any New Session

1. Read `/home/user/RoadMaps/CLAUDE.md` — master context
2. Read `.claude/roadmap/sibling-roadmap.json` — this repo's phase state

---

## What This Repo Is

**Public-facing creative updater and web publisher** for the Albert Lane digital infrastructure.

SimCity is the public window into a private infrastructure project. It:
- Receives sanitized hourly dispatches from `albert-lane-org/roadmaps` (private)
- Applies recursive creative stylization and rewrites `README.md` each cycle
- Maintains a `creative-state.json` that accumulates design motifs and advances a narrative arc
- Publishes a full static website to `albertlane.org/SimCity` via Cloudflare Pages (Phase 9)
- Runs a recursive marketing engine that generates Channel-1-News articles and self-critiques them
- Embeds Sovereign Canary reach probes and feeds trigger data back into copy generation
- Attracts designers and collaborators to the project

**This repo is fully public. No proprietary information flows here.**

---

## Core Pipeline (existing)

```
RoadMaps (private) → simcity-dispatch.yml @ :00/hr
  → updates/latest.json  (sanitized payload, overwritten hourly)
    → [15 min gap]
      → creative-update.yml @ :15/hr
        → scripts/creative_engine.py
          → README.md            (rewritten each cycle)
          → creative-state.json  (advanced each cycle)
          → generation_state.json + visual_quality_state.json
```

## Extended Pipeline (Phase 9)

```
[EXISTING] creative-update.yml
              ↓ generation_state.json + visual_quality_state.json updated
              ↓
[NEW] web-deploy.yml fires on push to main (state file changes)
    Step 1: canary_probe.py        → canary_state.json (token generation + polling)
    Step 2: marketing_engine.py    → marketing_state.json + site/channel-1-news/simcity-NNNN.html
    Step 3: channel1_sync.py       → site/channel-1-news/index.html + rss.xml + feed.json
    Step 4: web_generator.py       → site/index.html + gallery.html + styles.css + feed.json
    Step 5: Cloudflare Pages push  → albertlane.org/SimCity + albertlane.org/channel-1-news
    Step 6: commit state back      → marketing_state.json, canary_state.json

[NEW] skill-improvement.yml (Sunday 07:00 UTC)
    → skill_improver.py            → patches one of the 4 new scripts per cycle
                                   → SKILL_IMPROVEMENT_LOG.md
```

### Self-referential feedback loop

```
canary tokens embedded in site HTML + C1-News articles
  ↓ page views trigger canary beacon
  ↓ canary_probe.py polls triggers → canary_state.json.reach_score updated
  ↓ marketing_engine.py reads reach_score → self-critiques + improves copy
  ↓ skill_improver.py reads reach_score → patches marketing_engine.py if low
  ↓ improved marketing_engine.py generates sharper content next cycle
  ↓ better content → more canary triggers → higher reach_score
  ↑ loop
```

---

## Key Files

| File | Purpose |
|------|--------|
| `updates/latest.json` | Sanitized hourly dispatch from RoadMaps |
| `updates/schema.md` | Documents the payload format |
| `creative-state.json` | Persistent narrative state (iteration, arc stage, motifs) |
| `generation_state.json` | SVG generation state (zones, history, iteration) |
| `visual_quality_state.json` | Quality scores per zone |
| `scripts/creative_engine.py` | Reads state + update, writes README |
| `.github/workflows/creative-update.yml` | Hourly trigger at :15 past the hour |
| `README.md` | Auto-generated public output — do not edit manually |
| `marketing_state.json` | Rolling 48-campaign marketing history + A/B state |
| `canary_state.json` | Sovereign Canary token registry + reach score |
| `MARKETING_LOG.md` | Auto-generated campaign history (do not edit) |
| `CANARY_LOG.md` | Auto-generated canary cycle log (do not edit) |
| `SKILL_IMPROVEMENT_LOG.md` | Auto-generated skill patch history (do not edit) |
| `wrangler.simcity-site.toml` | Cloudflare Pages config (project: albertlane-simcity) |
| `.github/scripts/canary_probe.py` | Phase 9 Step 1: token generation + beacon polling |
| `.github/scripts/marketing_engine.py` | Phase 9 Step 2: recursive marketing copy (Claude Haiku) |
| `.github/scripts/channel1_sync.py` | Phase 9 Step 3: Channel-1-News HTML/RSS/JSON build |
| `.github/scripts/web_generator.py` | Phase 9 Step 4: SimCity site builder (T2 GlacierNoir, Claude Sonnet) |
| `.github/scripts/skill_improver.py` | Weekly: self-improvement of the above 4 scripts |
| `.github/workflows/web-deploy.yml` | Phase 9: full pipeline trigger (state file changes) |
| `.github/workflows/skill-improvement.yml` | Sunday 07:00 UTC skill self-improvement |

---

## Workflow Schedule

| Workflow | Repo | Cron | Purpose |
|----------|------|------|---------|
| `simcity-dispatch.yml` | roadmaps | `0 * * * *` | Sanitize + push to SimCity |
| `creative-update.yml` | simcity | `15 * * * *` | Read dispatch, render README + SVGs |
| `self-improve-creative.yml` | simcity | Weekly Sat 05:00 UTC | Improve SVG scripts |
| `web-deploy.yml` | simcity | push to main (state changes) | Full web pipeline + Cloudflare deploy |
| `skill-improvement.yml` | simcity | Sunday 07:00 UTC | Improve marketing/web scripts |

---

## Required Secrets

| Secret | Purpose | Required? |
|--------|---------|----------|
| `CLAUDE_API_KEY` | Hero copy + marketing copy generation | YES (same as existing) |
| `CF_API_TOKEN` | Cloudflare Pages deployment | YES (new — Phase 9) |
| `CF_ACCOUNT_ID` | Cloudflare account | YES (new — Phase 9) |
| `SOVEREIGN_CANARY_URL` | Sovereign Canary beacon server URL | OPTIONAL |
| `SOVEREIGN_CANARY_SECRET` | Canary token signing key | OPTIONAL |

Without `CF_API_TOKEN`/`CF_ACCOUNT_ID`: web-deploy.yml builds the site but skips Cloudflare push. Site content commits to `site/` as a fallback.

Without `SOVEREIGN_CANARY_URL`: canary_probe.py runs in local mode — tokens generated, no trigger polling, `reach_score` stays 0.0.

---

## Deploy Target

```
albertlane.org/SimCity         → site/index.html
albertlane.org/SimCity/gallery → site/gallery.html
albertlane.org/channel-1-news  → site/channel-1-news/index.html
albertlane.org/channel-1-news/simcity-NNNN.html → individual articles
```

Cloudflare Pages project name: `albertlane-simcity`

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

## Attribution

Every commit: `Co-authored-by: Claude Sonnet 4.6 <noreply@anthropic.com>`
All IP belongs to Albert Lane per LICENSE.md.
SEC Whistleblower No. 17684-273-411-436
