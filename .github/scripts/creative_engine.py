#!/usr/bin/env python3
# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-12
"""
SimCity Creative Engine — v2

Phase 1 — Claude Haiku : reads zone state + history + evolution notes
                          → writes narrative advancement
Phase 2 — Claude Sonnet: reads zone + narrative + style evolution notes
                          + previous coaching → generates isometric SVG
Phase 3 — Write outputs : SVG with provenance, VISUAL_LOG.md, gen_state

Runs at :20 every hour. Private infra updates updates/latest.json at :00.

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, json, sys, re, hashlib, datetime, textwrap
from pathlib import Path
from anthropic import Anthropic

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT               = Path(__file__).parent.parent
ZONE_STATE         = ROOT / "updates" / "latest.json"
GEN_STATE          = ROOT / "generation_state.json"
VISUAL_QUALITY     = ROOT / "visual_quality_state.json"
SVG_DIR            = ROOT / "assets" / "svg"
VISUAL_LOG         = ROOT / "VISUAL_LOG.md"
GALLERY_MD         = ROOT / "gallery.md"

# ── Client ────────────────────────────────────────────────────────────────────
claude = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# ── T2 GlacierNoir palette (hard-coded — no drift ever) ───────────────────────
T2 = {
    "bg":    "#04070E",
    "blue":  "#3B82F6",
    "ice":   "#F0F4FF",
    "mid":   "#1E3A5F",
    "dark":  "#0A1628",
    "line":  "#2563EB",
    "amber": "#B8621A",
}

# ── Zone visual vocabulary ─────────────────────────────────────────────────────
ZONE_VOCAB = {
    "city_hall": {
        "archetype": "imposing civic hall — symmetrical facade, central clock tower, wide entrance steps, two flanking wings",
        "mood": "authority, permanence, civic gravity",
        "lighting": "overhead, casting short sharp shadows down-right",
    },
    "gateway_district": {
        "archetype": "transit hub — elevated walkways, converging rail lines, arched connectors, signal towers",
        "mood": "motion, connection, infrastructure in use",
        "lighting": "ambient dusk, blue-tinted, long shadows",
    },
    "intelligence_core": {
        "archetype": "data center block — dense server stacks, cooling towers venting, status-light grids, cable conduit runs",
        "mood": "precision, latency, controlled environment",
        "lighting": "internal glow from server indicators, cold blue wash",
    },
    "sovereign_quarters": {
        "archetype": "modular interface tower — stacked terminal bays, antenna array on roof, glass-panel facade, entry airlock",
        "mood": "sovereignty, attention, quiet alertness",
        "lighting": "mixed — warm amber at entry, cold blue from screens above",
    },
}

# ── Attribution (safe public values only) ─────────────────────────────────────
CREATOR  = "Albert Lane | SovereignAudits™"
SEC_REF  = "17684-273-411-436"
LICENSE  = "SOVEREIGN IP LICENSE v1"

# ── Zone key mapping from updates/latest.json display names ───────────────────
_ZONE_KEY_MAP: dict[str, str] = {
    "City Hall":          "city_hall",
    "Gateway District":   "gateway_district",
    "Intelligence Core":  "intelligence_core",
    "Sovereign Quarters": "sovereign_quarters",
}


# ─────────────────────────────────────────────────────────────────────────────
# State management
# ─────────────────────────────────────────────────────────────────────────────

def load_state() -> tuple[dict, dict]:
    """Read updates/latest.json + generation_state.json and return (zone_data, gen_state)."""
    raw = json.loads(ZONE_STATE.read_text())

    # Transform updates/latest.json array format into keyed dict
    zones: dict[str, dict] = {}
    for z in raw.get("zones", []):
        key = _ZONE_KEY_MAP.get(z["zone"], z["zone"].lower().replace(" ", "_"))
        zones[key] = {
            "label":       z["zone"],
            "layer":       z.get("layer", ""),
            "phase":       z.get("active_phase", ""),
            "progress":    z.get("completion", 0),
            "status":      z.get("status", "planned"),
            "description": z.get("description", ""),
            "detail":      z.get("description", ""),
        }

    zone_data = {
        "city_meta": {
            "name":          "SimCity",
            "tagline":       raw.get("signal", "Walls rise. The blueprint holds."),
            "overall_phase": raw.get("momentum", "Construction"),
        },
        "zones": zones,
    }
    gen_state = json.loads(GEN_STATE.read_text())
    return zone_data, gen_state


def next_zone(gen_state: dict) -> str:
    order = gen_state["zone_order"]
    idx   = gen_state["zone_index"] % len(order)
    return order[idx]


def load_quality_state() -> dict:
    if VISUAL_QUALITY.exists():
        try:
            return json.loads(VISUAL_QUALITY.read_text())
        except Exception:
            pass
    return {}


def get_previous_coaching(zone_key: str, quality_state: dict) -> str:
    zone_scores = quality_state.get("zones", {}).get(zone_key, {}).get("scores", [])
    if not zone_scores:
        return ""
    return zone_scores[-1].get("coaching", "")


def get_style_evolution_notes(zone_key: str, gen_state: dict) -> str:
    evolution = gen_state.get("style_evolution", {})
    return evolution.get(zone_key, "")


def save_gen_state(gen_state: dict, zone_key: str, narrative_summary: str):
    gen_state["iteration"]  += 1
    gen_state["zone_index"] = (gen_state["zone_index"] + 1) % len(gen_state["zone_order"])
    gen_state["last_run"]   = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    gen_state["last_zone"]  = zone_key
    gen_state["history"].append({
        "iteration": gen_state["iteration"],
        "zone":      zone_key,
        "summary":   narrative_summary[:120],
        "ts":        gen_state["last_run"],
    })
    gen_state["history"] = gen_state["history"][-24:]
    GEN_STATE.write_text(json.dumps(gen_state, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Claude Haiku: narrative advancement
# ─────────────────────────────────────────────────────────────────────────────

def advance_narrative(zone_key: str, zone_data: dict, gen_state: dict) -> str:
    zone    = zone_data["zones"][zone_key]
    meta    = zone_data["city_meta"]
    history = gen_state.get("history", [])[-6:]
    history_text = "\n".join(
        f"- Iteration {h['iteration']}: {h['zone']} — {h['summary']}"
        for h in history
    ) or "First run — no prior history."

    prompt = (
        f"City: {meta['name']} — {meta['tagline']}\n"
        f"Phase: {meta['overall_phase']}\n\n"
        f"Zone: {zone['label']} ({zone['layer']} layer)\n"
        f"Current phase: {zone['phase']}\n"
        f"Progress: {zone['progress']}%\n"
        f"Status: {zone['status']}\n"
        f"Description: {zone['description']}\n"
        f"Detail: {zone['detail']}\n\n"
        f"Recent history:\n{history_text}\n\n"
        "Rules:\n"
        "- One paragraph only. No headers, no bullets, no markdown.\n"
        "- Civic voice — like a project update, not a press release.\n"
        "- Reference the progress percentage naturally.\n"
        "- End with something implying the next step, not completion.\n"
        "- Never use: vibrant, revolutionize, innovative, seamless.\n"
        "- Be honest — don't overstate progress or fabricate milestones."
    )

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=(
            "You are the narrator for a civic infrastructure project. "
            "Write ONE paragraph (3-5 sentences) advancing the narrative for the zone below. "
            "Factual, civic in tone, no marketing language."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Claude Sonnet: isometric SVG
# ─────────────────────────────────────────────────────────────────────────────

def generate_zone_svg(
    zone_key: str,
    zone_data: dict,
    narrative: str,
    iteration: int,
    style_evolution_notes: str = "",
    previous_coaching: str = "",
) -> str:
    zone  = zone_data["zones"][zone_key]
    vocab = ZONE_VOCAB[zone_key]
    pct   = zone["progress"]

    if pct < 40:
        construction_note = (
            "Foundation poured. Steel skeleton rising to 2-3 floors. "
            "Construction crane dominant in composition. Upper floors are empty steel frames, "
            "no facade, no windows. Ground-level details show concrete forms and rebar."
        )
    elif pct < 70:
        construction_note = (
            "Structure is closed in. Facade panels installed on lower floors, "
            "upper facade incomplete. Mix of dark (empty) and lit windows. "
            "One crane remains at upper-right. Interior lighting visible through installed windows."
        )
    elif pct < 90:
        construction_note = (
            "Near complete. Full facade present on all floors. All window openings filled. "
            "Interior lighting throughout. Exterior details (signage, entry features) being finished. "
            "No cranes. Ground level clean and paved."
        )
    else:
        construction_note = (
            "Complete and operational. All windows lit. Clean facade with no scaffolding. "
            "Civic flag or zone-specific antenna at apex. Ground level activated with entries. "
            "Subtle ambient lighting effects — the building is alive."
        )

    evolution_clause = ""
    if style_evolution_notes:
        evolution_clause = f"\nLEARNED STYLE IMPROVEMENTS (apply these):\n{style_evolution_notes}\n"

    coaching_clause = ""
    if previous_coaching:
        coaching_clause = f"\nPREVIOUS ITERATION CRITIQUE (address this):\n{previous_coaching}\n"

    system = (
        "You are a technical SVG illustrator specialising in isometric civic architecture. "
        "You produce complete, valid, browser-renderable SVG — nothing else. "
        "No preamble. No explanation. No markdown fences. Raw SVG only, starting with <svg.\n\n"
        f"ISOMETRIC GEOMETRY (enforce exactly):\n"
        f"- ViewBox: 0 0 800 520\n"
        f"- Isometric projection: x-axis right-down 30°, y-axis left-down 30°, z-axis straight up\n"
        f"- Horizontal surfaces: rhombus/parallelogram shapes only\n"
        f"- Background: solid {T2['bg']} rect covering full 800x520 viewBox\n"
        f"- Primary accent: {T2['blue']}\n"
        f"- Window/light colour: {T2['ice']} at varying opacity (50-90%)\n"
        f"- Grid lines: {T2['line']} at 20% opacity\n"
        f"- Amber accent: {T2['amber']} — MAXIMUM ONE element\n\n"
        f"STRUCTURE VOCABULARY:\n{vocab['archetype']}\n\n"
        f"MOOD: {vocab['mood']}\n"
        f"LIGHTING: {vocab['lighting']}\n\n"
        f"CONSTRUCTION STATE (iteration {iteration}, {pct}% complete):\n"
        f"{construction_note}\n\n"
        f"NARRATIVE CONTEXT:\n{narrative[:200]}\n"
        f"{evolution_clause}{coaching_clause}\n"
        "Produce a single complete <svg> element. Portfolio quality."
    )

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                f"Generate the isometric SVG for {zone['label']}. "
                f"Phase: {zone['phase']}. Progress: {pct}%. "
                f"Iteration {iteration}."
            ),
        }],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```$",       "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    if not raw.startswith("<svg"):
        raise ValueError(f"Claude returned non-SVG output: {raw[:120]}")

    return raw


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Write outputs with provenance injection
# ─────────────────────────────────────────────────────────────────────────────

def _blake3_eq(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def inject_svg_provenance(svg: str, zone_key: str, iteration: int) -> str:
    content_hash = _blake3_eq(svg.encode())
    tag = content_hash[:8]

    metadata_block = (
        f'<metadata>'
        f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        f' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        f' xmlns:sc="https://albertlane.net/sovereign/ns/">'
        f'<rdf:Description>'
        f'<dc:creator>{CREATOR}</dc:creator>'
        f'<dc:rights>{LICENSE}</dc:rights>'
        f'<sc:hash>{tag}</sc:hash>'
        f'<sc:sec_ref>{SEC_REF}</sc:sec_ref>'
        f'<sc:zone>{zone_key}</sc:zone>'
        f'<sc:iteration>{iteration}</sc:iteration>'
        f'</rdf:Description></rdf:RDF></metadata>'
    )

    prov_comment = (
        f'<!-- SOVEREIGN: creator="{CREATOR}" hash="{tag}" '
        f'sec="{SEC_REF}" zone="{zone_key}" iter="{iteration}" -->'
    )

    if '<metadata>' not in svg:
        match = re.search(r'<svg[^>]*>', svg)
        if match:
            pos = match.end()
            svg = svg[:pos] + metadata_block + svg[pos:]

    svg = svg.rstrip()
    if svg.endswith('</svg>'):
        svg = svg[:-6] + '\n' + prov_comment + '\n</svg>'

    return svg


def write_svg(zone_key: str, svg: str, iteration: int) -> str:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    svg_with_prov = inject_svg_provenance(svg, zone_key, iteration)
    current_path  = SVG_DIR / f"{zone_key}.svg"
    snapshot_path = SVG_DIR / f"{zone_key}_i{iteration:04d}.svg"
    current_path.write_text(svg_with_prov)
    snapshot_path.write_text(svg_with_prov)
    content_hash = _blake3_eq(svg.encode())
    print(f"[write_svg] {current_path.name} hash={content_hash[:12]}... iter={iteration}")
    return str(current_path)


def append_visual_log(
    zone_key: str,
    zone_data: dict,
    narrative: str,
    iteration: int,
    timestamp: str,
    quality_total: int = 0,
    quality_label: str = "",
):
    zone    = zone_data["zones"][zone_key]
    repo    = os.environ.get("GITHUB_REPOSITORY", "Albert-lane-org/SimCity")
    svg_url = f"https://raw.githubusercontent.com/{repo}/main/assets/svg/{zone_key}.svg"
    quality_line = f"**Quality:** {quality_total}/40 ({quality_label})" if quality_total else ""

    entry = textwrap.dedent(f"""
    ## Iteration {iteration:04d} — {timestamp}

    **Zone:** {zone['label']} &nbsp;·&nbsp; **Progress:** {zone['progress']}% &nbsp;·&nbsp; **Phase:** {zone['phase']} &nbsp;{f'·&nbsp; {quality_line}' if quality_line else ''}

    {narrative}

    ![{zone['label']}]({svg_url})

    ---
    """).lstrip()

    header_needed = not VISUAL_LOG.exists() or VISUAL_LOG.stat().st_size == 0
    with open(VISUAL_LOG, "a") as f:
        if header_needed:
            f.write(
                "# SimCity — Visual Construction Log\n\n"
                "Hourly record of the city as it is built. Append-only.\n"
                f"Authored: {CREATOR} | {SEC_REF}\n\n"
                "---\n\n"
            )
        f.write(entry)


def update_gallery(zone_data: dict, gen_state: dict, quality_state: dict):
    repo  = os.environ.get("GITHUB_REPOSITORY", "Albert-lane-org/SimCity")
    now   = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    meta  = zone_data.get("city_meta", {})
    iteration = gen_state.get("iteration", 0)

    lines = [
        "# SimCity — Public Gallery",
        "",
        f"> {meta.get('tagline', 'Walls rise. The blueprint holds.')}",
        "",
        f"*{CREATOR} &nbsp;·&nbsp; SEC Ref: {SEC_REF}*  ",
        f"*{meta.get('name', 'SimCity')} &nbsp;·&nbsp; Phase: {meta.get('overall_phase', 'Construction')} &nbsp;·&nbsp; Iteration {iteration:04d}*",
        "",
        "---",
        "",
    ]

    for zone_key, zone in zone_data.get("zones", {}).items():
        svg_url   = f"https://raw.githubusercontent.com/{repo}/main/assets/svg/{zone_key}.svg"
        zone_q    = quality_state.get("zones", {}).get(zone_key, {})
        avg_score = zone_q.get("avg_score", 0)
        best      = zone_q.get("best_score", 0)
        evo_notes = zone_q.get("style_evolution_notes", "")

        lines += [
            f"## {zone['label']}",
            "",
            f"**Layer:** {zone['layer']} &nbsp;·&nbsp; "
            f"**Phase:** {zone['phase']} &nbsp;·&nbsp; "
            f"**Progress:** {zone['progress']}%",
            "",
        ]

        if avg_score:
            lines.append(f"*Quality avg: {avg_score}/40 &nbsp;·&nbsp; Best: {best}/40*")
            lines.append("")

        lines += [
            f"![{zone['label']}]({svg_url})",
            "",
            zone.get("description", ""),
            "",
        ]

        if evo_notes:
            lines += [
                "<details><summary>Style evolution notes</summary>",
                "",
                evo_notes,
                "",
                "</details>",
                "",
            ]

        lines.append("---")
        lines.append("")

    lines += [f"*Updated: {now} &nbsp;·&nbsp; {LICENSE}*"]
    GALLERY_MD.write_text("\n".join(lines))
    print(f"[update_gallery] gallery.md updated — iteration {iteration}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[main] Creative engine v2 — {timestamp}")

    zone_data, gen_state = load_state()
    quality_state        = load_quality_state()
    zone_key             = next_zone(gen_state)
    iteration            = gen_state["iteration"] + 1
    zone_label           = zone_data["zones"][zone_key]["label"]

    style_notes       = get_style_evolution_notes(zone_key, gen_state)
    previous_coaching = get_previous_coaching(zone_key, quality_state)

    print(f"[main] Zone: {zone_label} | Iteration: {iteration}")
    if style_notes:
        print(f"[main] Style evolution notes loaded ({len(style_notes)} chars)")
    if previous_coaching:
        print(f"[main] Previous coaching: {previous_coaching[:80]}...")

    print("[main] Phase 1 — Claude Haiku narrative...")
    narrative = advance_narrative(zone_key, zone_data, gen_state)

    print("[main] Phase 2 — Claude Sonnet SVG generation...")
    svg = generate_zone_svg(
        zone_key, zone_data, narrative, iteration,
        style_evolution_notes=style_notes,
        previous_coaching=previous_coaching,
    )
    print(f"[main] SVG: {len(svg)} chars, valid={svg.startswith('<svg')}")

    svg_path = write_svg(zone_key, svg, iteration)
    append_visual_log(zone_key, zone_data, narrative, iteration, timestamp)
    update_gallery(zone_data, gen_state, quality_state)
    save_gen_state(gen_state, zone_key, narrative[:120])

    out = os.environ.get("GITHUB_OUTPUT", "")
    if out:
        zone = zone_data["zones"][zone_key]
        with open(out, "a") as f:
            f.write(f"zone_key={zone_key}\n")
            f.write(f"zone_label={zone_label}\n")
            f.write(f"zone_progress={zone['progress']}\n")
            f.write(f"iteration={iteration}\n")
            f.write(f"svg_path={svg_path}\n")

    print(f"[main] Done. Zone={zone_key}, Iteration={iteration}")


if __name__ == "__main__":
    main()
