#!/usr/bin/env python3
# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-12 | SEC Whistleblower No. 17684-273-411-436
"""
quality_scorer.py — Visual Quality Scoring

Scores AI-generated SVG assets using Claude Haiku as an independent reviewer.
Claude Haiku reviews Claude Sonnet SVG output — cross-model scoring within
the Claude family prevents self-congratulatory inflation.

FOUR SCORING DIMENSIONS (0-10 each, 40-point total):
  1. Geometric Fidelity    — isometric projection grammar adherence
  2. Palette Adherence     — T2 GlacierNoir colour discipline
  3. Structural Richness   — architectural depth, layering, meaningful detail
  4. Progress Alignment    — construction state accuracy vs zone progress %

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, sys, json, re
import datetime
from pathlib import Path
from anthropic import Anthropic

# ── Client ────────────────────────────────────────────────────────────────────
_claude = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# ── Palette reference ─────────────────────────────────────────────────────────
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
    Claude Haiku analyzes Claude Sonnet's SVG code and scores it across 4 dimensions.
    Returns a structured scoring record.
    """
    palette_list = ", ".join(T2_PALETTE.keys())

    prompt = f"""SCORING TASK: Analyze the SVG code below and assign scores on four dimensions.
Be precise, honest, and critical. Do not inflate scores.

ZONE CONTEXT:
  Zone: {zone_label}
  Progress: {zone_progress}% complete
  Iteration: {iteration}

T2 GlacierNoir PALETTE (only these hex values are permitted):
  {palette_list}

CONSTRUCTION STATE REFERENCE:
  0-40%:   Foundation/skeleton — cranes, empty frames, minimal lighting
  40-70%:  Closing in — partial facade, some dark/lit windows, one crane
  70-90%:  Near complete — all windows, interior light, no cranes
  90-100%: Operational — all lights, clean facade, antenna/flag at apex

SCORING DIMENSIONS (score each 0-10, integers only):

1. GEOMETRIC_FIDELITY (0-10)
   - Correct isometric projection? (x-axis right-down 30 degrees, z-axis straight up)
   - Horizontal surfaces as parallelograms?
   - Consistent shadow direction?
   - Deduct heavily for square windows, wrong projection, inconsistent geometry

2. PALETTE_ADHERENCE (0-10)
   - Only T2 palette colours used?
   - Background is #04070E?
   - No off-palette colours?
   - Amber used sparingly (maximum 1 accent element)?

3. STRUCTURAL_RICHNESS (0-10)
   - Number of distinct architectural elements?
   - Evidence of depth/layering?
   - Meaningful detail (windows, grids, conduit, not just solid blocks)?

4. PROGRESS_ALIGNMENT (0-10)
   - Does construction state match {zone_progress}% completion?
   - Are correct construction signals present?
   - Would a reader correctly infer the progress?

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
KEY_STRENGTH: <one sentence>
KEY_WEAKNESS: <one sentence>
COACHING_NOTE: <1-2 sentences specific guidance for next iteration>
END"""

    response = _claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=(
            "You are a technical visual quality auditor reviewing isometric SVG code. "
            "Respond ONLY in the exact format specified. No preamble, no explanation. "
            "Machine-parsed output only."
        ),
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
    geo, pal, rich, prog = [max(0, min(10, x)) for x in (geo, pal, rich, prog)]
    total = geo + pal + rich + prog

    strength = extract_str(r"KEY_STRENGTH:\s*(.+?)(?:\n|$)")
    weakness = extract_str(r"KEY_WEAKNESS:\s*(.+?)(?:\n|$)")
    coaching = extract_str(r"COACHING_NOTE:\s*(.+?)(?:END|$)")

    label = (
        "EXCELLENT"  if total >= SCORE_EXCELLENT  else
        "ACCEPTABLE" if total >= SCORE_ACCEPTABLE else
        "MARGINAL"   if total >= SCORE_MARGINAL   else
        "POOR"
    )

    return {
        "zone_key":      zone_key,
        "zone_label":    zone_label,
        "zone_progress": zone_progress,
        "iteration":     iteration,
        "scored_at":     datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scorer_model":  "claude-haiku-4-5-20251001",
        "scored_by":     "quality-scorer (Claude Haiku reviews Claude Sonnet output)",
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
BELOW_STREAK_TRIGGER = 3


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
            "scores":               [],
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
        "global": {"total_scored": 0, "overall_avg": 0.0},
        "sec_ref": "17684-273-411-436",
        "owner":   "Albert Lane | SovereignAudits™",
    }


def persist_score(score_record: dict) -> dict:
    state    = load_quality_state()
    zone_key = score_record["zone_key"]
    total    = score_record["total"]

    zone_state = state["zones"].setdefault(zone_key, {
        "scores": [], "avg_score": 0.0, "best_score": 0,
        "best_iteration": 0, "below_threshold_streak": 0,
        "style_evolution_notes": "",
    })

    zone_state["scores"].append({
        "iteration": score_record["iteration"],
        "total":     total,
        "label":     score_record["label"],
        "coaching":  score_record["coaching"],
        "ts":        score_record["scored_at"],
    })
    zone_state["scores"] = zone_state["scores"][-24:]

    all_totals = [s["total"] for s in zone_state["scores"]]
    zone_state["avg_score"] = round(sum(all_totals) / len(all_totals), 1)

    if total > zone_state["best_score"]:
        zone_state["best_score"]     = total
        zone_state["best_iteration"] = score_record["iteration"]

    if total < QUALITY_THRESHOLD:
        zone_state["below_threshold_streak"] += 1
    else:
        zone_state["below_threshold_streak"] = 0

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
    return [
        zk for zk, zs in state["zones"].items()
        if zs.get("below_threshold_streak", 0) >= BELOW_STREAK_TRIGGER
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Standalone entry point
# ─────────────────────────────────────────────────────────────────────────────

def score_latest_output(
    svg_path: str,
    zone_key: str,
    zone_label: str,
    zone_progress: int,
    iteration: int,
) -> dict:
    svg_content = Path(svg_path).read_text()
    record = score_svg(svg_content, zone_key, zone_label, zone_progress, iteration)
    state  = persist_score(record)

    print(
        f"[quality_scorer] {zone_label}: {record['total']}/40 ({record['label']}) "
        f"| streak={state['zones'][zone_key]['below_threshold_streak']}",
        file=sys.stderr,
    )

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
    if len(sys.argv) < 6:
        print("Usage: quality_scorer.py <svg_path> <zone_key> <zone_label> <progress_pct> <iteration>")
        sys.exit(1)
    rec = score_latest_output(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    print(json.dumps(rec, indent=2))
