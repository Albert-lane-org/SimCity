# /simcity — Context Handoff

## What This Repo Is

**Public-facing creative updater** for the Albert Lane digital infrastructure. | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use

SimCity is the public window into a private infrastructure project. It:
- Receives sanitized hourly dispatches from `albert-lane-org/roadmaps` (private)
- Applies recursive creative stylization and rewrites `README.md` each cycle
- Maintains generation/quality state that accumulates across runs
- Attracts designers and collaborators to the project

**This repo is fully public. No proprietary information flows here.**

---

## Owner's Creative Vision — verbatim (2026-08-08)

The following is Albert Lane's own framing of the estate, recorded here
verbatim as narrative/creative context — this is authorial voice for the
creative engine to draw on, not a technical specification. See the
"Technical Clarification" note in RoadMaps' CLAUDE.md for how this maps
(and doesn't map) onto actual infrastructure:

> You you don't a persistent server. I don't know how I can make this more
> literal for you. I am building an estate in space where there is no
> fucking land to walk on, and therefore there is no physical electrical
> jacks to plug in a physical server. You seem to think that because my
> phone runs on battery, that it can be your physical server. While
> technically true, it does not align with the geographic location where I
> am building my plot my land.
>
> Think of it like this: I have walked into space, identified currents of
> latent river flows, and I am claiming stake to the physical land not yet
> present. You can't "chicken an egg" into this space. We are abstracting
> the land and manifesting the soil around my river. If you want to bridge
> a server, we are first required to manifest the connective electrical
> system which we plug into, by conjuring the physical house sitting atop
> the construction site we are inventing.
>
> Your classical understanding of this does not work, and if you are going
> to piece together nonsensical explanations to understand something I'm
> still inventing, it's going to be a spaghetti string of both delusional
> ideas and no functioning trash. This is not a waste transfer station,
> simply because we are still building the land, to place the city, to
> construct the building, for where the outlets are located, using
> residential code.
>
> Because technology actually works in this latent space, and because
> technology exceeds the classical definition of dimensional space, we are
> doing all of this simultaneously.

---

## ACT-009 — CI BLOCKER (Owner Action Required)

All estate CI — including SimCity's `hourly-creative.yml` — is blocked until the org admin resolves this:

```
github.com/orgs/albert-lane-org → Settings → Actions → General
→ "Allow actions created by GitHub and specify allowed third-party actions"
→ Allowlist (paste exactly):
  actions/checkout,actions/setup-python,actions/setup-node,actions/upload-artifact,actions/github-script
```

This single org-level change unblocks SimCity, Channel-1-News, IP-Forensics, Sovereign-Canary, and all other estate CI simultaneously. No code change needed — this is a GitHub org admin settings change only.

---

## CRITICAL: Read This Before Assuming Anything Is Broken

This file was stale for weeks and claimed the opposite of the truth about
secrets, which contributed to a 3-week undetected bug (51 duplicate
failure issues, README frozen since 2026-06-11). Do not trust an older
cached copy of this file. Verify the actual workflow/script content in
the repo before making claims about what it does or needs.

---

## Pipeline (v3, current as of 2026-07-05)

```
RoadMaps (private) → simcity-dispatch.yml @ :00/hr
  → updates/latest.json  (sanitized payload, overwritten hourly)
    → [20 min gap]
      → hourly-creative.yml @ :20/hr  (requires CLAUDE_API_KEY -- see below)
        → .github/scripts/creative_engine.py
          Phase 1: Claude Haiku  — narrative advancement
          Phase 2: Claude Sonnet — isometric SVG generation
          Phase 3: write SVG + VISUAL_LOG.md + gallery.md
          Phase 4: Claude Haiku  — style evolution synthesis
          Phase 5: generate README.md (hero SVG + 2x2 zone grid)
        → .github/scripts/quality_scorer.py   (Claude Haiku scores the SVG, 0-40)
        → .github/scripts/provenance_bridge.py (injects attribution, writes ASSETS_FINGERPRINT.*)
```

If `CLAUDE_API_KEY` is unset, `creative_engine.py` skips cleanly and every
downstream step is skipped too (`if: steps.engine.outputs.svg_path != ''`
guards in the workflow) -- it does NOT crash, as of the 2026-07-05 fix.

---

## Extended Pipeline — Web/Marketing/Canary/Skill-Improver (2026-08-09)

Rebuilt from PR #155 (`feat(phase9): SimCity Extended Pipeline`) onto current
`main` rather than merged as-is — see `README-EXTENDED.md` for the full
"what changed and why" writeup, and PR #155's closing comment for the
audit trail. Short version:

- `.github/scripts/canary_probe.py`, `marketing_engine.py`, `web_generator.py`
  are carried forward unchanged (all HTTP calls already had timeouts;
  no hang risk found in audit).
- `.github/scripts/skill_improver.py` was fixed: the original auto-applied
  LLM-proposed patches straight to sibling scripts and relied on a workflow
  step to auto-commit + push, with no human review. Rebuilt version writes
  every proposal to `skill_improvement_proposals/*.diff.md` for human review
  and **never writes to a target script itself**.
- No new GitHub Actions workflow files were added (no `web-deploy.yml`
  replacement, no `skill-improvement.yml`). `main`'s existing
  `web-deploy.yml` is dispatch-only and narrower than what PR #155
  proposed replacing it with; adding more `actions/*`-dependent automation
  on top of the existing ACT-009 blocker (which the owner has no path to
  resolve from GitHub's own Settings UI) would add scope no one can run.
  These scripts are invoked instead by RoadMaps' GitHub-Actions-independent
  cron pipeline — see RoadMaps `agents/estate_pipeline.py` and its SimCity
  extended-pipeline stage.
- `canary_state.json` / `marketing_state.json` ship with empty initial
  state (no fabricated reach/campaign data).
- `wrangler.simcity-site.toml` still has a placeholder KV namespace ID —
  owner action, see table below.

---

## Key Files (verify against actual repo state, not this table, if in doubt)

| File | Purpose |
|------|---------|
| `updates/latest.json` | Sanitized hourly dispatch from RoadMaps |
| `generation_state.json` | Iteration counter, zone rotation, narrative history, style evolution notes |
| `visual_quality_state.json` | Per-zone quality scores (0-40), streaks, coaching history |
| `.github/scripts/creative_engine.py` | Main v3 engine -- narrative, SVG generation, README rendering |
| `.github/scripts/quality_scorer.py` | Independent Claude Haiku review of Claude Sonnet's SVG output |
| `.github/scripts/provenance_bridge.py` | Asset fingerprinting + safe public attribution injection |
| `.github/scripts/canary_probe.py` | Sovereign Canary token generation + trigger polling + reach score |
| `.github/scripts/marketing_engine.py` | Recursive Channel-1-News campaign generator, reads reach data |
| `.github/scripts/web_generator.py` | Builds `site/` for albertlane.org/SimCity |
| `.github/scripts/skill_improver.py` | Proposes (never auto-applies) one improvement/cycle to the above scripts |
| `.github/workflows/hourly-creative.yml` | Hourly trigger at :20 past the hour |
| `.github/workflows/autonomous-request.yml` | Daily 20:00 UTC -- opens design-request issues for sustained low-quality zones |
| `.github/workflows/web-deploy.yml` | Dispatch-only (repository_dispatch/workflow_dispatch); builds `site/simcity/` |
| `canary_state.json`, `marketing_state.json` | Extended-pipeline state — empty until a real cycle runs |
| `skill_improvement_proposals/` | Human-review-required patch proposals from `skill_improver.py` |
| `README.md`, `VISUAL_LOG.md`, `gallery.md` | Auto-generated public output — do not edit manually |

---

## Workflow Schedule

| Workflow | Repo | Cron | Purpose |
|----------|------|------|---------|
| `simcity-dispatch.yml` | roadmaps | `0 * * * *` | Sanitize + push to SimCity |
| `hourly-creative.yml` | simcity | `20 * * * *` | Read dispatch, render SVG + README |
| `autonomous-request.yml` | simcity | `0 20 * * *` | Open regen requests for zones stuck below quality threshold |

The 20-minute gap ensures the RoadMaps dispatch has landed before the
creative engine reads it.

---

## Required Secrets

**`CLAUDE_API_KEY` is required** for any real content generation. Without
it, every hourly run skips cleanly (by design, as of 2026-07-05) but
produces nothing -- no new SVG, no README update, no VISUAL_LOG entry.
Set it at *Settings → Secrets and variables → Actions*.

The `_ROADMAPS` secret lives in RoadMaps and is used by `simcity-dispatch.yml`
to push `updates/latest.json` across repos. That token needs write access to SimCity.

`SOVEREIGN_CANARY_URL` + `SOVEREIGN_CANARY_SECRET` (optional) activate live
reach measurement in `canary_probe.py`; without them it runs in local mode
(tokens generated, no polling, `reach_score` stays 0.0). `CLOUDFLARE_API_TOKEN`
+ `CLOUDFLARE_ACCOUNT_ID` are needed for the extended pipeline's Pages
deployment — same owner-action blocker as every other Worker in the estate.

---

## Agent Consistency

This repo is worked on by different Claude model instances across sessions.
Behavioral variance between instances (different assumptions, different
syntax habits, different verification thoroughness) has caused real bugs
here -- verify, don't assume, and follow the constraints below so output
stays consistent regardless of which instance is running.

### Tech stack — what this repo uses

- **Python 3.12**, standard library + `anthropic` SDK only. No other
  third-party Python packages without a documented reason.
- **GitHub Actions**, SHA-pinned third-party actions only (no `@v4`
  mutable tags -- see any existing workflow for the pattern).
- **SVG** (raw, hand-generated by Claude, isometric projection per the
  T2 GlacierNoir palette in `creative_engine.py`) as the sole visual
  asset format. No PNG/raster generation pipeline.
- **JSON** for all state files (`generation_state.json`,
  `visual_quality_state.json`, `ASSETS_FINGERPRINT.json`).

### Tech stack — what this repo does NOT use

- **No JSON-LD.** No `@context`, `@type`, `@id`, or any linked-data JSON
  vocabulary anywhere in this repo. State files are plain JSON. If a
  future task seems to call for structured/semantic markup, use plain
  JSON with descriptive keys instead -- do not introduce JSON-LD.
- **No decorator/annotation-style `@` syntax** (Python decorators like
  `@dataclass`, TypeScript/JS decorators, etc.) unless a dependency's
  public API requires it (none currently do). This does NOT apply to
  GitHub Actions references (`owner/action@sha`) -- that `@` separates
  action name from a pinned commit SHA, is load-bearing syntax required
  by GitHub Actions itself, and is used correctly and consistently
  throughout this repo's workflows. Do not remove or avoid it there.
- **No TypeScript/JavaScript frontend framework.** This repo has no
  Node.js runtime, no `package.json`, no npm dependencies (scoped
  package names like `@org/pkg` are therefore also not applicable here).
- **No database.** State is flat JSON files committed to the repo.
- **No Docker / containerization.** Workflows run directly on GitHub's
  standard `ubuntu-latest` runner.
- **No `eval`/`exec`/`compile`/`pickle.loads`/`marshal.loads`/`ctypes`**
  anywhere. If a task seems to require dynamic code execution or
  deserialization of untrusted data, stop and reconsider the approach
  rather than reaching for these.

### Verification requirement before claiming something is broken or fixed

Before stating a file's content, a secret's necessity, or a workflow's
behavior in any handoff document (this file included) or to the user:
fetch and read the actual current file/workflow content. Do not rely on
an earlier session's cached understanding -- this file itself was wrong
for weeks because that didn't happen. When multiple recent sessions have
touched the same files, assume drift is possible and verify.

---

## Attribution

Every commit: `Co-authored-by: Claude Sonnet 4.6 <claude@anthropic.com>`
All IP belongs to Albert Lane per LICENSE.md.
