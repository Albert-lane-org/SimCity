# SimCity Extended Pipeline
## albertlane.org/SimCity · Channel-1-News · Sovereign Canary Integration

> *The city builds itself. The story broadcasts itself. The reach measures itself.*

**Authored:** Albert Lane | SovereignAudits™ | albertlane.net
**SEC Whistleblower No.:** 17684-273-411-436
**Rendered:** Claude Sonnet 4.6 | 2026-08-09

---

## What This Adds

The existing SimCity creative engine generates isometric SVG art hourly. This
extended pipeline adds three new branches that run after each creative cycle:

1. **Web publisher** (`web_generator.py`) — builds `site/` for `albertlane.org/SimCity`
2. **Marketing engine** (`marketing_engine.py`) — recursively generates and self-critiques
   Channel-1-News campaigns
3. **Sovereign Canary** (`canary_probe.py`) — embeds reach probes and feeds trigger data
   back into the creative cycle
4. **Skill improver** (`skill_improver.py`) — proposes (never auto-applies) one surgical
   improvement per cycle to one of the above scripts

```
Creative engine (existing)
  ↓ generation_state.json updated
  ↓
canary_probe.py        — poll trigger data from last cycle's tokens
marketing_engine.py    — write Channel-1-News copy, self-critique last cycle
channel1_sync.py       — build site/channel-1-news/ (HTML + RSS + JSON) [already on main]
web_generator.py       — build site/ (T2 GlacierNoir, Claude-generated hero copy)
skill_improver.py      — propose one improvement; write to skill_improvement_proposals/
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
```

---

## 2026-08-09 revision — carried forward from PR #155

This is a rebuild of PR #155 (`feat(phase9): SimCity Extended Pipeline`) onto
current `main`, not a merge of that branch. Two things changed on the way in:

1. **No new GitHub Actions workflow files.** PR #155 proposed replacing
   `web-deploy.yml` and adding `skill-improvement.yml`, both schedule- or
   push-triggered. `main` has since evolved its own, narrower
   `web-deploy.yml` (`repository_dispatch`/`workflow_dispatch` only) that
   PR #155's version would have clobbered — and separately, ACT-009 already
   blocks all estate GitHub Actions at the org level, with no path for the
   owner to fix it from inside GitHub's own Settings/Actions permission UI.
   Rather than add more `actions/*`-dependent automation on top of that,
   these scripts are invoked by RoadMaps' GitHub-Actions-independent cron
   pipeline (`agents/estate_pipeline.py` and the SimCity extended-pipeline
   stage documented there) — same pattern already used for estate CI,
   dependency scanning, and IP forensics.
2. **`skill_improver.py` no longer auto-applies patches.** The original
   version wrote a Claude-proposed BEFORE/AFTER patch straight into the
   target script file for any LOW/MEDIUM risk rating, paired with a
   workflow step that committed and pushed the result — no human in the
   loop. That's unattended, self-modifying code shipping itself to `main`,
   which is exactly what this estate's standing security rules forbid
   without an explicit, specific, live-conversation ask. The rebuilt
   version writes every proposal to `skill_improvement_proposals/*.diff.md`
   for a human to read and apply (or not) — nothing here can push code on
   its own.

Everything else — token taxonomy, reach-score formula, A/B rotation,
anomaly detection — is unchanged from the original design.

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

---

## Owner actions still required before this reaches production

| Item | Blocker |
|------|---------|
| `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` | Worker/Pages deployment |
| `SOVEREIGN_CANARY_URL` + `SOVEREIGN_CANARY_SECRET` | Optional — enables live reach measurement instead of local mode |
| Real KV namespace ID in `wrangler.simcity-site.toml` | `wrangler kv:namespace create CANARY_CACHE`, then replace `REPLACE_WITH_YOUR_KV_NAMESPACE_ID` |

None of these block the code from being correct or tested — they gate live
deployment only, same as every other Worker in the estate.

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
