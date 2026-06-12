#!/usr/bin/env python3
"""
quality_scorer.py - Visual Quality Scoring (Claude-only)

Scores AI-generated SVG assets using Claude with a quality auditor persona.

FOUR SCORING DIMENSIONS (0-10 each, 40-point total):
  1. Geometric Fidelity    - isometric projection grammar adherence
  2. Palette Adherence     - T2 GlacierNoir colour discipline
  3. Structural Richness   - architectural depth, layering, meaningful detail
  4. Progress Alignment    - construction state accuracy vs zone progress %

AUTHORED: Albert Lane | SovereignAudits(tm) | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, sys, json, re, datetime
from pathlib import Path
from anthropic import Anthropic

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
ZONE_KEYS = ["city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"]
QUALITY_THRESHOLD    = 26
BELOW_STREAK_TRIGGER = 3

_client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


def score_svg(svg_content, zone_key, zone_label, zone_progress, iteration):
    palette_list = ", ".join(T2_PALETTE.keys())
    prompt = (
        f"You are a technical visual quality auditor reviewing isometric SVG code.\n\n"
        f"ZONE: {zone_label} | Progress: {zone_progress}% | Iteration: {iteration}\n"
        f"T2 PALETTE (only these): {palette_list}\n\n"
        f"CONSTRUCTION STATE REFERENCE:\n"
        f"  0-40%: Foundation/skeleton, cranes, empty frames\n"
        f"  40-70%: Partial facade, some windows dark/lit, one crane\n"
        f"  70-90%: Near complete, all windows, interior light, no cranes\n"
        f"  90-100%: Operational, all lights, clean facade, antenna at apex\n\n"
        f"Score each dimension 0-10 (integers only):\n"
        f"1. GEOMETRIC_FIDELITY - isometric projection, parallelogram surfaces, consistent shadow direction\n"
        f"2. PALETTE_ADHERENCE - only T2 colors, background #04070E, amber used sparingly\n"
        f"3. STRUCTURAL_RICHNESS - depth layers, window grids, meaningful detail, not placeholders\n"
        f"4. PROGRESS_ALIGNMENT - construction state matches {zone_progress}% completion\n\n"
        f"SVG CODE:\n```\n{svg_content[:6000]}\n```\n\n"
        f"OUTPUT (machine-parsed, no other text):\n"
        f"GEOMETRIC_FIDELITY: <0-10>\n"
        f"PALETTE_ADHERENCE: <0-10>\n"
        f"STRUCTURAL_RICHNESS: <0-10>\n"
        f"PROGRESS_ALIGNMENT: <0-10>\n"
        f"TOTAL: <sum>\n"
        f"KEY_STRENGTH: <one sentence>\n"
        f"KEY_WEAKNESS: <one sentence>\n"
        f"COACHING_NOTE: <1-2 sentences for next iteration>\n"
        f"END"
    )

    resp = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    return _parse_score_response(raw, zone_key, zone_label, zone_progress, iteration)


def _parse_score_response(raw, zone_key, zone_label, zone_progress, iteration):
    def extract_int(pattern, default=0):
        m = re.search(pattern, raw)
        try:
            return int(m.group(1)) if m else default
        except (ValueError, AttributeError):
            return default

    def extract_str(pattern, default=""):
        m = re.search(pattern, raw, re.DOTALL)
        return m.group(1).strip() if m else default

    geo  = max(0, min(10, extract_int(r"GEOMETRIC_FIDELITY:\s*(\d+)")))
    pal  = max(0, min(10, extract_int(r"PALETTE_ADHERENCE:\s*(\d+)")))
    rich = max(0, min(10, extract_int(r"STRUCTURAL_RICHNESS:\s*(\d+)")))
    prog = max(0, min(10, extract_int(r"PROGRESS_ALIGNMENT:\s*(\d+)")))
    total = geo + pal + rich + prog

    label = (
        "EXCELLENT"  if total >= SCORE_EXCELLENT else
        "ACCEPTABLE" if total >= SCORE_ACCEPTABLE else
        "MARGINAL"   if total >= SCORE_MARGINAL else
        "POOR"
    )

    return {
        "zone_key":      zone_key,
        "zone_label":    zone_label,
        "zone_progress": zone_progress,
        "iteration":     iteration,
        "scored_at":     datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scorer_model":  "claude-haiku-4-5-20251001",
        "scored_by":     "claude-quality-auditor",
        "dimensions":    {"geometric_fidelity": geo, "palette_adherence": pal, "structural_richness": rich, "progress_alignment": prog},
        "total":    total,
        "label":    label,
        "strength": extract_str(r"KEY_STRENGTH:\s*(.+?)(?:\n|$)"),
        "weakness": extract_str(r"KEY_WEAKNESS:\s*(.+?)(?:\n|$)"),
        "coaching": extract_str(r"COACHING_NOTE:\s*(.+?)(?:END|$)"),
    }


def load_quality_state():
    if VISUAL_QUALITY_STATE.exists():
        try:
            return json.loads(VISUAL_QUALITY_STATE.read_text())
        except Exception:
            pass
    return _empty_quality_state()


def _empty_quality_state():
    zones = {}
    for zk in ZONE_KEYS:
        zones[zk] = {
            "scores": [], "avg_score": 0.0, "best_score": 0,
            "best_iteration": 0, "below_threshold_streak": 0,
            "style_evolution_notes": "",
        }
    return {
        "schema_version": "2.0.0",
        "quality_threshold": QUALITY_THRESHOLD,
        "zones": zones,
        "global": {"total_scored": 0, "overall_avg": 0.0},
        "sec_ref": "17684-273-411-436",
        "owner": "Albert Lane | SovereignAudits(tm)",
    }


def persist_score(score_record):
    state    = load_quality_state()
    zone_key = score_record["zone_key"]
    total    = score_record["total"]

    zone_state = state["zones"].setdefault(zone_key, {
        "scores": [], "avg_score": 0.0, "best_score": 0,
        "best_iteration": 0, "below_threshold_streak": 0, "style_evolution_notes": "",
    })
    zone_state["scores"].append({
        "iteration": score_record["iteration"],
        "total": total, "label": score_record["label"],
        "coaching": score_record["coaching"], "ts": score_record["scored_at"],
    })
    zone_state["scores"] = zone_state["scores"][-24:]

    all_totals = [s["total"] for s in zone_state["scores"]]
    zone_state["avg_score"] = round(sum(all_totals) / len(all_totals), 1)
    if total > zone_state["best_score"]:
        zone_state["best_score"]     = total
        zone_state["best_iteration"] = score_record["iteration"]
    zone_state["below_threshold_streak"] = (
        zone_state.get("below_threshold_streak", 0) + 1 if total < QUALITY_THRESHOLD else 0
    )

    state["global"]["total_scored"] += 1
    avgs = [state["zones"][zk]["avg_score"] for zk in state["zones"] if state["zones"][zk]["avg_score"] > 0]
    if avgs:
        state["global"]["overall_avg"] = round(sum(avgs) / len(avgs), 1)

    VISUAL_QUALITY_STATE.write_text(json.dumps(state, indent=2))
    return state


def zones_needing_autonomous_request(state):
    return [zk for zk, zs in state["zones"].items() if zs.get("below_threshold_streak", 0) >= BELOW_STREAK_TRIGGER]


def score_latest_output(svg_path, zone_key, zone_label, zone_progress, iteration):
    svg_content = Path(svg_path).read_text()
    record = score_svg(svg_content, zone_key, zone_label, zone_progress, iteration)
    state  = persist_score(record)
    print(f"[quality_scorer] {zone_label}: {record['total']}/40 ({record['label']}) | streak={state['zones'][zone_key]['below_threshold_streak']}", file=sys.stderr)

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
