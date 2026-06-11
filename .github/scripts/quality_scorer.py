#!/usr/bin/env python3
"""
quality_scorer.py — Cross-Model Visual Quality Scoring

Scores AI-generated SVG assets using the opposing model: Gemini scores
Claude's SVG output; Claude scores Gemini's raster output descriptions.

Cross-scoring prevents self-congratulatory inflation. Each model is a
genuine critic of the other's work.

FOUR SCORING DIMENSIONS (0–10 each, 40-point total):
  1. Geometric Fidelity    — isometric projection grammar adherence
  2. Palette Adherence     — T2 GlacierNoir colour discipline (no off-palette drift)
  3. Structural Richness   — architectural depth, layering, meaningful detail
  4. Progress Alignment    — construction state accuracy vs zone progress %

SCORE THRESHOLDS:
  ≥ 32  EXCELLENT  — promote to gallery best-of
  ≥ 26  ACCEPTABLE — standard commit
  ≥ 20  MARGINAL   — flag; increment below_threshold_streak
   < 20  POOR       — flag; increment streak; consider autonomous regen request

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, sys, json, re
import datetime
from pathlib import Path
import anthropic

# ── Palette reference (hard-coded — no drift allowed) ─────────────────────────
T2_PALETTE = {
    "#04070E": "background",
    "#3B82F6": "primary blue",
    "#F0F4FF": "ice white",
    "#1E3A5F": "mid shadow",
    "#0A1628": "deep shadow",
    "#2563EB": "grid line blue",
    "#B8621A": "amber accent (sparingly)",
}

SCORE_EXCELLENT  = 32
SCORE_ACCEPTABLE = 26
SCORE_MARGINAL   = 20

VISUAL_QUALITY_STATE = Path("visual_quality_state.json")

claude_client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


# ─────────────────────────────────────────────────────────────────────────────
# Core scoring function
# ─────────────────────────────────────────────────────────────────────────────

def score_svg(
    svg_content: str,
    zone_key: str,
    zone_label: str,
    zone_progress: int,
    iteration: int,
) -> dict:
    """
    Gemini analyzes Claude's SVG code and scores it across 4 dimensions.
    Returns a structured scoring record.
    """
    palette_list = ", ".join(T2_PALETTE.keys())

    prompt = f"""You are a technical visual quality auditor reviewing isometric SVG code
generated for a civic architecture project.

SCORING TASK: Analyze the SVG code below and assign scores on four dimensions.
Be precise, honest, and critical. Do not inflate scores.

ZONE CONTEXT:
  Zone: {zone_label}
  Progress: {zone_progress}% complete
  Iteration: {iteration}

T2 GlacierNoir PALETTE (only these hex values are permitted):
  {palette_list}

CONSTRUCTION STATE REFERENCE:
  0–40%:   Foundation/skeleton stage — cranes, empty frames, minimal lighting
  40–70%:  Closing in — partial facade, some windows dark/lit, one crane
  70–90%:  Near complete — all windows, interior light, no cranes
  90–100%: Operational — all lights, clean facade, antenna/flag at apex

SCORING DIMENSIONS (score each 0–10, integers only):

1. GEOMETRIC_FIDELITY (0–10)
   - Correct isometric projection? (x-axis: right-down 30°, z-axis: straight up)
   - Horizontal surfaces as parallelograms/rhombuses?
   - Consistent shadow direction (left faces darker, right faces mid-tone)?
   - Deduct heavily for: square windows, wrong projection angles, inconsistent geometry

2. PALETTE_ADHERENCE (0–10)
   - Only T2 palette colours used?
   - Background is #04070E?
   - No off-palette colours (no random greys, browns, warm whites)?
   - Amber used sparingly (maximum 1 accent element)?
   - Award 10 only if strictly on-palette with good tonal variation

3. STRUCTURAL_RICHNESS (0–10)
   - Number of distinct architectural elements (floors, windows, columns, etc.)?
   - Evidence of depth/layering (near and far surfaces differentiated)?
   - Meaningful detail (not just solid blocks — actual window grids, conduit runs, etc.)?
   - Does the scene feel like a specific building, not a generic placeholder?

4. PROGRESS_ALIGNMENT (0–10)
   - Does the construction state visually match {zone_progress}% completion?
   - Are the correct construction signals present (cranes, lighting, facade state)?
   - Would a reader correctly infer the progress from the image alone?
   - Deduct heavily if a 60% zone looks 100% complete, etc.

SVG CODE TO SCORE:
```
{svg_content[:6000]}
```

OUTPUT FORMAT (strict — machine-parsed, no other text):
GEOMETRIC_FIDELITY: <integer 0-10>
PALETTE_ADHERENCE: <integer 0-10>
STRUCTURAL_RICHNESS: <integer 0-10>
PROGRESS_ALIGNMENT: <integer 0-10>
TOTAL: <sum>
KEY_STRENGTH: <one sentence — what this SVG does best>
KEY_WEAKNESS: <one sentence — the single most important thing to fix>
COACHING_NOTE: <1-2 sentences — specific guidance for the next iteration of this zone>
END"""

    response = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()

    return _parse_score_response(raw, zone_key, zone_label, zone_progress, iteration)


def _parse_score_response(
    raw: str,
    zone_key: str,
    zone_label: str,
    zone_progress: int,
    iteration: int,
) -> dict:
    """Parse Gemini's structured score output into a scoring record."""
    def extract_int(pattern: str, default: int = 0) -> int:
        m = re.search(pattern, raw)
        try:
            return int(m.group(1)) if m else default
        except (ValueError, AttributeError):
            return default

    def extract_str(pattern: str, default: str = "") -> str:
        m = re.search(pattern, raw, re.DOTALL)
        return m.group(1).strip() if m else default

    geo  = extract_int(r"GEOMETRIC_FIDELITY:\s*(\d+)")
    pal  = extract_int(r"PALETTE_ADHERENCE:\s*(\d+)")
    rich = extract_int(r"STRUCTURAL_RICHNESS:\s*(\d+)")
    prog = extract_int(r"PROGRESS_ALIGNMENT:\s*(\d+)")

    # Cap each dimension to 0-10
    geo, pal, rich, prog = [max(0, min(10, x)) for x in (geo, pal, rich, prog)]
    total = geo + pal + rich + prog

    strength     = extract_str(r"KEY_STRENGTH:\s*(.+?)(?:\n|$)")
    weakness     = extract_str(r"KEY_WEAKNESS:\s*(.+?)(?:\n|$)")
    coaching     = extract_str(r"COACHING_NOTE:\s*(.+?)(?:END|$)")

    label = (
        "EXCELLENT"  if total >= SCORE_EXCELLENT  else
        "ACCEPTABLE" if total >= SCORE_ACCEPTABLE else
        "MARGINAL"   if total >= SCORE_MARGINAL   else
        "POOR"
    )

    return {
        "zone_key":          zone_key,
        "zone_label":        zone_label,
        "zone_progress":     zone_progress,
        "iteration":         iteration,
        "scored_at":         datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scorer_model":      "claude-haiku-4-5-20251001",
        "scored_by":         "claude-haiku (self-scoring with adversarial prompt)",
        "dimensions": {
            "geometric_fidelity":  geo,
            "palette_adherence":   pal,
            "structural_richness": rich,
            "progress_alignment":  prog,
        },
        "total":    total,
        "label":    label,
        "strength": strength,
        "weakness": weakness,
        "coaching": coaching,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Visual quality state management
# ─────────────────────────────────────────────────────────────────────────────

ZONE_KEYS = ["city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"]
QUALITY_THRESHOLD    = 26
BELOW_STREAK_TRIGGER = 3   # consecutive below-threshold before autonomous request


def load_quality_state() -> dict:
    if VISUAL_QUALITY_STATE.exists():
        try:
            return json.loads(VISUAL_QUALITY_STATE.read_text())
        except Exception:
            pass
    return _empty_quality_state()


def _empty_quality_state() -> dict:
    zones = {}
    for zk in ZONE_KEYS:
        zones[zk] = {
            "scores":               [],   # rolling last 24 score records
            "avg_score":            0.0,
            "best_score":           0,
            "best_iteration":       0,
            "below_threshold_streak": 0,
            "style_evolution_notes":  "",
        }
    return {
        "schema_version":    "1.0.0",
        "quality_threshold": QUALITY_THRESHOLD,
        "zones":             zones,
        "global": {
            "total_scored": 0,
            "overall_avg":  0.0,
        },
        "sec_ref": "17684-273-411-436",
        "owner":   "Albert Lane | SovereignAudits™",
    }


def persist_score(score_record: dict) -> dict:
    """Update visual_quality_state.json with a new score record. Returns updated state."""
    state    = load_quality_state()
    zone_key = score_record["zone_key"]
    total    = score_record["total"]

    zone_state = state["zones"].setdefault(zone_key, {
        "scores": [], "avg_score": 0.0, "best_score": 0,
        "best_iteration": 0, "below_threshold_streak": 0,
        "style_evolution_notes": "",
    })

    # Append score; keep rolling 24
    zone_state["scores"].append({
        "iteration": score_record["iteration"],
        "total":     total,
        "label":     score_record["label"],
        "coaching":  score_record["coaching"],
        "ts":        score_record["scored_at"],
    })
    zone_state["scores"] = zone_state["scores"][-24:]

    # Recompute avg
    all_totals = [s["total"] for s in zone_state["scores"]]
    zone_state["avg_score"] = round(sum(all_totals) / len(all_totals), 1)

    # Best score tracking
    if total > zone_state["best_score"]:
        zone_state["best_score"]     = total
        zone_state["best_iteration"] = score_record["iteration"]

    # Below-threshold streak
    if total < QUALITY_THRESHOLD:
        zone_state["below_threshold_streak"] += 1
    else:
        zone_state["below_threshold_streak"] = 0

    # Global stats
    state["global"]["total_scored"] += 1
    all_zone_avgs = [
        state["zones"][zk]["avg_score"]
        for zk in state["zones"]
        if state["zones"][zk]["avg_score"] > 0
    ]
    if all_zone_avgs:
        state["global"]["overall_avg"] = round(sum(all_zone_avgs) / len(all_zone_avgs), 1)

    VISUAL_QUALITY_STATE.write_text(json.dumps(state, indent=2))
    return state


def zones_needing_autonomous_request(state: dict) -> list[str]:
    """Return zone_keys where below_threshold_streak >= BELOW_STREAK_TRIGGER."""
    return [
        zk for zk, zs in state["zones"].items()
        if zs.get("below_threshold_streak", 0) >= BELOW_STREAK_TRIGGER
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Standalone scoring entry point (used by hourly-creative.yml)
# ─────────────────────────────────────────────────────────────────────────────

def score_latest_output(
    svg_path: str,
    zone_key: str,
    zone_label: str,
    zone_progress: int,
    iteration: int,
) -> dict:
    """Score a specific SVG file and persist the result."""
    svg_content = Path(svg_path).read_text()
    record = score_svg(svg_content, zone_key, zone_label, zone_progress, iteration)
    state  = persist_score(record)

    print(
        f"[quality_scorer] {zone_label}: {record['total']}/40 ({record['label']}) "
        f"| streak={state['zones'][zone_key]['below_threshold_streak']}",
        file=sys.stderr,
    )

    # Write GitHub Actions outputs if available
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"quality_total={record['total']}\n")
            f.write(f"quality_label={record['label']}\n")
            f.write(f"quality_coaching={record['coaching'][:200]}\n")
            streaks = zones_needing_autonomous_request(state)
            f.write(f"needs_regen={'true' if zone_key in streaks else 'false'}\n")
            f.write(f"streaks_zones={','.join(streaks)}\n")

    return record


if __name__ == "__main__":
    # CLI: quality_scorer.py <svg_path> <zone_key> <zone_label> <progress_pct> <iteration>
    if len(sys.argv) < 6:
        print("Usage: quality_scorer.py <svg_path> <zone_key> <zone_label> <progress_pct> <iteration>")
        sys.exit(1)
    svg_path      = sys.argv[1]
    zone_key      = sys.argv[2]
    zone_label    = sys.argv[3]
    zone_progress = int(sys.argv[4])
    iteration     = int(sys.argv[5])
    rec = score_latest_output(svg_path, zone_key, zone_label, zone_progress, iteration)
    print(json.dumps(rec, indent=2))
