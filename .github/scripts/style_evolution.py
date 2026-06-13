#!/usr/bin/env python3
"""
style_evolution.py — Creative Quality Learning Loop

Reads accumulated quality scores for each zone and runs a Claude analysis
to derive evolved visual vocabulary. The evolved notes feed back into the
creative_engine.py system prompt — this is the learning loop that was
missing from the original design.

MECHANISM:
  1. Load visual_quality_state.json (all zone score histories)
  2. For each zone: Claude reads scores + coaching notes → derives what patterns
     correlate with high scores vs. low scores
  3. Outputs concise, actionable `style_evolution_notes` per zone
  4. Updates both visual_quality_state.json and generation_state.json
  5. Appends findings to CREATIVE_CHANGELOG.md

RUNS: Weekly (Wednesday 05:00 UTC via self-improve-creative.yml) or manually.

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, sys, json, re
import datetime
from pathlib import Path
from anthropic import Anthropic

ROOT                 = Path(".")
VISUAL_QUALITY_STATE = ROOT / "visual_quality_state.json"
GEN_STATE            = ROOT / "generation_state.json"
CREATIVE_CHANGELOG   = ROOT / "CREATIVE_CHANGELOG.md"

claude = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


# ── Zone labels ───────────────────────────────────────────────────────────────
ZONE_LABELS = {
    "city_hall":         "City Hall",
    "gateway_district":  "Gateway District",
    "intelligence_core": "Intelligence Core",
    "sovereign_quarters":"Sovereign Quarters",
}

ZONE_ARCHETYPES = {
    "city_hall":         "imposing civic hall — symmetrical facade, clock tower, wide steps, flanking wings",
    "gateway_district":  "transit hub — elevated walkways, converging rail lines, signal towers",
    "intelligence_core": "data center — dense server stacks, cooling towers, status-light grids, conduit runs",
    "sovereign_quarters":"modular interface tower — stacked terminal bays, antenna array, glass-panel facade",
}


def load_quality_state() -> dict:
    if not VISUAL_QUALITY_STATE.exists():
        print("[style_evolution] No quality state found. Run quality_scorer.py first.", file=sys.stderr)
        sys.exit(0)
    return json.loads(VISUAL_QUALITY_STATE.read_text())


def load_gen_state() -> dict:
    if GEN_STATE.exists():
        return json.loads(GEN_STATE.read_text())
    return {}


def derive_zone_evolution(zone_key: str, zone_data: dict) -> str:
    """
    Claude reads the score history for one zone and derives evolved style notes.
    Returns a 2-3 sentence actionable guide for future Claude SVG generation.
    """
    scores = zone_data.get("scores", [])
    if not scores:
        return ""

    avg   = zone_data.get("avg_score", 0)
    best  = zone_data.get("best_score", 0)
    label = ZONE_LABELS.get(zone_key, zone_key)
    arch  = ZONE_ARCHETYPES.get(zone_key, "")

    # Summarise score history for Claude
    high_scores = [s for s in scores if s["total"] >= 28]
    low_scores  = [s for s in scores if s["total"] < 24]

    history_lines = [
        f"Iteration {s['iteration']}: {s['total']}/40 ({s['label']}) — coaching: {s['coaching']}"
        for s in scores[-12:]  # last 12 iterations
    ]
    history_text = "\n".join(history_lines) or "No history yet."

    high_coaching = [s["coaching"] for s in high_scores[-4:]]
    low_coaching  = [s["coaching"] for s in low_scores[-4:]]

    system = """You are a creative director analyzing quality score patterns for
an isometric SVG architecture series. Your task: derive 2-3 specific, actionable
style improvement notes from the scoring history.

Rules:
- Reference concrete visual elements: "add window grid detail to upper floors",
  not "improve detail"
- Note what the coaching data says is consistently working vs consistently failing
- The notes will be injected directly into an AI art generation system prompt
- Be specific enough that an AI SVG generator can act on them immediately
- Maximum 3 sentences total
- Avoid generic advice ("make it better") — give exact geometric or colour guidance"""

    user_msg = (
        f"Zone: {label}\n"
        f"Archetype: {arch}\n"
        f"Score history (avg={avg}, best={best}/40):\n{history_text}\n\n"
        f"High-scoring coaching notes: {high_coaching}\n"
        f"Low-scoring coaching notes: {low_coaching}\n\n"
        f"Derive 2-3 concise, actionable style improvement notes for this zone."
    )

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text.strip()


def run_evolution():
    print(f"[style_evolution] Starting evolution analysis...", file=sys.stderr)
    quality_state = load_quality_state()
    gen_state     = load_gen_state()

    evolved_notes = {}
    changelog_entries = []
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for zone_key, zone_data in quality_state.get("zones", {}).items():
        scores = zone_data.get("scores", [])
        if len(scores) < 3:
            print(f"[style_evolution] {zone_key}: < 3 scores, skipping.", file=sys.stderr)
            continue

        print(f"[style_evolution] Deriving evolution for {zone_key}...", file=sys.stderr)
        notes = derive_zone_evolution(zone_key, zone_data)

        if notes:
            evolved_notes[zone_key] = notes
            quality_state["zones"][zone_key]["style_evolution_notes"] = notes
            changelog_entries.append({
                "zone": zone_key,
                "notes": notes,
                "avg": zone_data.get("avg_score", 0),
                "best": zone_data.get("best_score", 0),
            })
            print(f"[style_evolution] {zone_key}: {notes[:80]}...", file=sys.stderr)

    # ── Write back to visual_quality_state.json ──────────────────────────────
    VISUAL_QUALITY_STATE.write_text(json.dumps(quality_state, indent=2))

    # ── Write evolved notes into generation_state.json ────────────────────────
    # The creative_engine.py reads this file — it now picks up evolution notes
    if gen_state and evolved_notes:
        existing = gen_state.get("style_evolution", {})
        existing.update(evolved_notes)
        gen_state["style_evolution"] = existing
        gen_state["style_evolution_last_updated"] = timestamp
        GEN_STATE.write_text(json.dumps(gen_state, indent=2))
        print(f"[style_evolution] Updated generation_state.json with evolution notes.", file=sys.stderr)

    # ── Append to CREATIVE_CHANGELOG.md ──────────────────────────────────────
    _append_changelog(changelog_entries, timestamp)

    # ── GitHub Actions outputs ────────────────────────────────────────────────
    out = os.environ.get("GITHUB_OUTPUT", "")
    if out:
        with open(out, "a") as f:
            f.write(f"zones_evolved={','.join(evolved_notes.keys())}\n")
            f.write(f"evolution_timestamp={timestamp}\n")

    print(f"[style_evolution] Done. Evolved {len(evolved_notes)} zones.", file=sys.stderr)


def _append_changelog(entries: list[dict], timestamp: str):
    """Append a creative evolution entry to CREATIVE_CHANGELOG.md."""
    if not entries:
        return

    header_needed = not CREATIVE_CHANGELOG.exists() or CREATIVE_CHANGELOG.stat().st_size == 0
    with open(CREATIVE_CHANGELOG, "a") as f:
        if header_needed:
            f.write(
                "# Creative Changelog\n\n"
                "Running record of creative quality evolution.\n"
                "Each entry captures what the quality scoring system learned "
                "and how it updated the generation vocabulary.\n\n"
                "Authored: Albert Lane | SovereignAudits™ | albertlane.net\n"
                "SEC Whistleblower No. 17684-273-411-436\n\n"
                "---\n\n"
            )

        f.write(f"\n\n## {timestamp} — Style Evolution Cycle\n\n")
        for e in entries:
            label = ZONE_LABELS.get(e["zone"], e["zone"])
            f.write(
                f"### {label}\n\n"
                f"**Avg score:** {e['avg']}/40 &nbsp;·&nbsp; **Best:** {e['best']}/40\n\n"
                f"**Evolved notes:**\n\n{e['notes']}\n\n"
            )
        f.write("---\n")
        f.write("*SEC Whistleblower No. 17684-273-411-436 | SovereignAudits™*")


if __name__ == "__main__":
    run_evolution()
