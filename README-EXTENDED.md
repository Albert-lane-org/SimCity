# SimCity Extended Pipeline
## albertlane.org/SimCity · Channel-1-News · Sovereign Canary Integration

> *The city builds itself. The story broadcasts itself. The reach measures itself.*

**Authored:** Albert Lane | SovereignAudits™ | albertlane.net  
**SEC Whistleblower No.:** 17684-273-411-436  
**Rendered:** Claude Sonnet 4.6 | 2026-07-21

---

## What Phase 9 Adds

The existing SimCity creative engine generates isometric SVG art hourly. Phase 9 adds three new pipeline branches that run after each creative cycle:

1. **Web publisher** — builds and deploys `albertlane.org/SimCity` from creative state
2. **Marketing engine** — recursively generates and self-critiques Channel-1-News campaigns
3. **Sovereign Canary** — embeds reach probes and feeds trigger data back into the creative cycle

The result is a fully recursive loop:

```
Creative engine (existing)
  ↓ generation_state.json updated
  ↓
[NEW] canary_probe.py        — poll trigger data from last cycle's tokens
[NEW] marketing_engine.py    — write Channel-1-News copy, self-critique last cycle
[NEW] channel1_sync.py       — build site/channel-1-news/ (HTML + RSS + JSON)
[NEW] web_generator.py       — build site/ (T2 GlacierNoir, Claude-generated hero copy)
      ↓
Cloudflare Pages → albertlane.org/SimCity
                → albertlane.org/channel-1-news
      ↓
Canary tokens embedded in every page
      ↓
Page views trigger SOVEREIGN CANARY beacon
      ↓
canary_probe.py polls triggers → reach_score updated
      ↓
marketing_engine.py reads reach_score → improves copy next cycle
      ↓
skill_improver.py reads reach_score → patches scripts if stagnant
      ↑ (loop)
```

---

## Files Added

### Repo root

```
marketing_state.json          — initial empty state (committed)
canary_state.json             — initial empty state (committed)
wrangler.simcity-site.toml   — Cloudflare Pages config
CLAUDE.md                    — merged (core + extended pipeline)
README-EXTENDED.md           — this file
```

### .github/scripts/

```
canary_probe.py      — Sovereign Canary token manager (stdlib only)
marketing_engine.py  — recursive marketing campaign generator (Claude Haiku)
channel1_sync.py     — Channel-1-News HTML/RSS/JSON builder (stdlib only)
web_generator.py     — SimCity website builder (T2 GlacierNoir, Claude Sonnet)
skill_improver.py    — weekly self-improvement of the above 4 scripts
```

### .github/workflows/

```
web-deploy.yml         — triggered by state file changes; runs full web pipeline
skill-improvement.yml  — Sunday 07:00 UTC; patches one script per cycle
```

---

## Installation

### 1. Create Cloudflare Pages project

```bash
npm install -g wrangler
wrangler login
wrangler pages project create albertlane-simcity --production-branch main

# Create KV namespace for canary cache:
wrangler kv namespace create CANARY_CACHE
# Copy the output id into wrangler.simcity-site.toml → [[kv_namespaces]] id = "..."
```

### 2. Set GitHub Secrets

In SimCity repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `CLAUDE_API_KEY` | (already set for creative engine) |
| `CF_API_TOKEN` | Cloudflare API token with Pages:Edit permission |
| `CF_ACCOUNT_ID` | Your Cloudflare account ID |
| `SOVEREIGN_CANARY_URL` | URL of SOVEREIGN CANARY beacon server (optional) |
| `SOVEREIGN_CANARY_SECRET` | Token signing secret (optional) |

### 3. Allow third-party GitHub Actions (org-level)

> **ACT-009**: The org Actions policy may block third-party actions.
> Owner must go to Settings → Actions → General and add to the allowlist:
> - `cloudflare/pages-action`
> - `actions/setup-python`
> - `actions/github-script`

### 4. Trigger first run

```bash
gh workflow run web-deploy.yml
```

---

## Workflow Schedule

| Workflow | Trigger | Purpose |
|----------|---------|--------|
| `hourly-creative.yml` (existing) | `:15` every hour | SVG generation, quality scoring |
| `web-deploy.yml` (new) | Push to main (state file changes) | Web build + Cloudflare deploy |
| `self-improve-creative.yml` (existing) | Weekly Sat 05:00 UTC | Improve SVG scripts |
| `skill-improvement.yml` (new) | Weekly Sun 07:00 UTC | Improve marketing/web scripts |

---

## Self-Improvement Logic

`skill_improver.py` auto-selects the target script each Sunday based on metrics:

| Condition | Target |
|-----------|--------|
| `canary.trigger_rate < 10%` after ≥15 tokens | `canary_probe.py` |
| `canary.reach_score < 30%` after ≥5 campaigns | `marketing_engine.py` |
| `vq.min_zone_avg < 10/40` | `web_generator.py` |
| Campaign count divisible by 5 | `channel1_sync.py` |
| Default rotation | Rotates through all 4 |

Claude Sonnet reads the target script's first 5000 chars + relevant metrics, proposes ONE surgical patch (BEFORE/AFTER code blocks), applies it if risk ≤ MEDIUM, and appends to `SKILL_IMPROVEMENT_LOG.md`.

---

## Sovereign Canary Integration

Without the SOVEREIGN CANARY beacon server, `canary_probe.py` runs in **local mode**:
- Token generation works normally
- Tokens are embedded in HTML via `data-canary-token` attributes
- No trigger polling (no HTTP calls)
- `reach_score` stays 0.0

To activate full reach measurement, deploy `beacon/beacon_server.py` from the
[sovereign-canary repo](https://github.com/Albert-lane-org/sovereign-canary) and set
`SOVEREIGN_CANARY_URL` and `SOVEREIGN_CANARY_SECRET` in the SimCity repo secrets.

---

## Palette Reference

| Theme | Usage |
|-------|-------|
| T2 GlacierNoir | `site/index.html`, `site/gallery.html` |
| T4 ForensicCaseStudy | `site/channel-1-news/` pages |

Both use Inter + Cormorant Garamond + JetBrains Mono from Google Fonts.

---

## Attribution

Every generated file carries:
```
Authored: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
Rendered: Claude Sonnet 4.6
```

All IP belongs to Albert Lane per LICENSE.md.

---

*Contact: lane.albert@pm.me*
