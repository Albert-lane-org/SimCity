#!/usr/bin/env python3
# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-12 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
SimCity Creative Engine — v3

Phase 1 — Claude Haiku  : reads zone state + history + evolution notes
                          → writes narrative advancement
Phase 2 — Claude Sonnet : reads zone + narrative + style evolution notes
                          + previous coaching → generates isometric SVG
                          Model: claude-sonnet-5 | Budget: 8192 tokens
Phase 3 — Write outputs : SVG with provenance, VISUAL_LOG.md, gen_state
Phase 4 — Style synth   : Claude Haiku synthesizes actionable style notes
                          from recent quality coaching → stored in gen_state
Phase 5 — README update : writes README.md with latest SVG + 2x2 city grid

Runs at :20 every hour. Private infra updates updates/latest.json at :00.

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, json, sys, re, hashlib, datetime, textwrap
from pathlib import Path
from anthropic import Anthropic

# ── Paths ────────────────────────────────────────────────────────────────────────────────
ROOT               = Path(__file__).resolve().parents[2]
ZONE_STATE         = ROOT / "updates" / "latest.json"
GEN_STATE          = ROOT / "generation_state.json"
VISUAL_QUALITY     = ROOT / "visual_quality_state.json"
SVG_DIR            = ROOT / "assets" / "svg"
VISUAL_LOG         = ROOT / "VISUAL_LOG.md"
GALLERY_MD         = ROOT / "gallery.md"
README_MD          = ROOT / "README.md"

# ── Client ────────────────────────────────────────────────────────────────────────────────
CLAUDE_SVG_MODEL   = "claude-sonnet-5"
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5-20251001"

claude = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY", ""))

# ── T2 GlacierNoir palette ───────────────────────────────────────────────────────────────
T2 = {
    "bg":    "#04070E",
    "blue":  "#3B82F6",
    "ice":   "#F0F4FF",
    "mid":   "#1E3A5F",
    "dark":  "#0A1628",
    "line":  "#2563EB",
    "amber": "#B8621A",
}

# ── Zone visual vocabulary ─────────────────────────────────────────────────────────────
ZONE_VOCAB = {
    "city_hall": {
        "archetype": "imposing civic hall — symmetrical facade, central clock tower with clock face detail, wide entrance steps with railings, two flanking wings with window rows, civic flag at apex",
        "mood": "authority, permanence, civic gravity",
        "lighting": "overhead, casting short sharp shadows down-right",
        "key_elements": "clock tower (dominant vertical), entrance steps (wide parallelogram), window grid (3-4 floors visible), cornice detail, flag pole",
    },
    "gateway_district": {
        "archetype": "transit hub — elevated walkways as parallelograms, converging rail lines with sleepers, arched connector bridges, signal towers with light indicators, platform canopies",
        "mood": "motion, connection, infrastructure in use",
        "lighting": "ambient dusk, blue-tinted, long shadows cast left",
        "key_elements": "elevated walkway (large parallelogram), rail lines (converging polygons), signal tower (tall thin rectangle), arch bridge, platform shelter",
    },
    "intelligence_core": {
        "archetype": "data center block — dense server stack rows, cooling tower vents, status-light grids (red/green/blue dots), cable conduit bundles on exterior, HVAC units on roof",
        "mood": "precision, latency, controlled environment",
        "lighting": "internal glow from server indicators, cold blue wash from exterior floods",
        "key_elements": "server rack faces (grid of small rectangles), cooling tower (cylindrical polygon), status LEDs (small circles in grid), conduit bundles, HVAC box",
    },
    "sovereign_quarters": {
        "archetype": "modular interface tower — stacked terminal bays with distinct floor bands, antenna array on roof (3-5 antenna elements), glass-panel facade with screen glow, entry airlock with door detail",
        "mood": "sovereignty, attention, quiet alertness",
        "lighting": "mixed — warm amber at entry airlock, cold blue from screen panels above",
        "key_elements": "antenna array (roof, multiple thin verticals), glass panels (large rectangles with interior glow), terminal bays (stacked horizontal bands), airlock door, screen indicator strip",
    },
}

# ── Attribution ──────────────────────────────────────────────────────────────────────────────
CREATOR  = "Albert Lane | SovereignAudits™"
SEC_REF  = "17684-273-411-436"
LICENSE  = "SOVEREIGN IP LICENSE v1"

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
    raw = json.loads(ZONE_STATE.read_text())

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

    if GEN_STATE.exists():
        gen_state = json.loads(GEN_STATE.read_text())
    else:
        gen_state = {
            "iteration": 0,
            "zone_index": 0,
            "zone_order": ["city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"],
            "last_run": None,
            "last_zone": None,
            "history": [],
            "style_evolution": {
                "city_hall": "",
                "gateway_district": "",
                "intelligence_core": "",
                "sovereign_quarters": "",
            },
        }
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
    return gen_state.get("style_evolution", {}).get(zone_key, "")


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
        f"Description: {zone['description']}\n\n"
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
        model=CLAUDE_HAIKU_MODEL,
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
# Phase 2 — Claude Sonnet 5: isometric SVG
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
        evolution_clause = f"\nLEARNED STYLE IMPROVEMENTS (apply these first):\n{style_evolution_notes}\n"

    coaching_clause = ""
    if previous_coaching:
        coaching_clause = f"\nPREVIOUS ITERATION CRITIQUE (address this directly):\n{previous_coaching}\n"

    system = (
        f"You are a technical SVG illustrator specialising in isometric civic architecture. "
        f"You produce complete, valid, browser-renderable SVG — nothing else. "
        f"No preamble. No explanation. No markdown fences. Raw SVG only, starting with <svg.\n\n"
        f"ISOMETRIC GEOMETRY (enforce exactly):\n"
        f"- ViewBox: 0 0 800 520\n"
        f"- Isometric projection: x-axis right-down 30°, y-axis left-down 30°, z-axis straight up\n"
        f"- Horizontal surfaces: rhombus/parallelogram shapes only\n"
        f"- Background: solid {T2['bg']} rect covering full 800x520 viewBox\n"
        f"- Primary accent: {T2['blue']}\n"
        f"- Window/light colour: {T2['ice']} at varying opacity (50-90%)\n"
        f"- Grid lines: {T2['line']} at 20% opacity\n"
        f"- Amber accent: {T2['amber']} — MAXIMUM ONE element\n\n"
        f"DEPTH LAYERS (paint back to front in this order):\n"
        f"1. Sky/background gradient or solid dark\n"
        f"2. Distant city silhouette or ground plane extension\n"
        f"3. Primary building structure (largest element)\n"
        f"4. Secondary structures and infrastructure details\n"
        f"5. Ground plane, street level, entry features\n"
        f"6. Foreground details: signage, lighting, texture elements\n\n"
        f"GEOMETRIC PRECISION:\n"
        f"- All isometric angles exactly 30°/60° (use tan(30°)=0.577 for calculations)\n"
        f"- Minimum 50 distinct SVG elements (polygons, rects, circles, lines)\n"
        f"- Building height: minimum 8 visible floor bands\n"
        f"- Each floor: distinct horizontal parallelogram with window elements\n"
        f"- Shadow polygons on all major structures (offset +8px right, +8px down, 40% opacity)\n\n"
        f"STRUCTURE VOCABULARY:\n{vocab['archetype']}\n"
        f"KEY ELEMENTS TO INCLUDE: {vocab['key_elements']}\n\n"
        f"MOOD: {vocab['mood']}\n"
        f"LIGHTING: {vocab['lighting']}\n\n"
        f"CONSTRUCTION STATE (iteration {iteration}, {pct}% complete):\n"
        f"{construction_note}\n\n"
        f"NARRATIVE CONTEXT:\n{narrative[:200]}\n"
        f"{evolution_clause}{coaching_clause}\n"
        "Produce a single complete <svg> element. Portfolio quality. Minimum 50 elements."
    )

    response = claude.messages.create(
        model=CLAUDE_SVG_MODEL,
        max_tokens=8192,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                f"Generate the isometric SVG for {zone['label']}. "
                f"Phase: {zone['phase']}. Progress: {pct}%. "
                f"Iteration {iteration}. Include all key elements for this zone."
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
# Phase 4 — Style evolution synthesis
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_style_evolution(zone_key: str, quality_state: dict, gen_state: dict) -> None:
    """Use Claude Haiku to synthesize actionable style notes from recent quality coaching.
    Updates gen_state['style_evolution'][zone_key] in-place; caller must save gen_state."""
    zone_scores = quality_state.get("zones", {}).get(zone_key, {}).get("scores", [])
    if len(zone_scores) < 2:
        return

    recent = zone_scores[-4:]
    coaching_parts = [
        f"Score {s.get('total', 0)}/40: {s.get('coaching', '')}"
        for s in recent
        if s.get("coaching")
    ]
    if not coaching_parts:
        return

    vocab = ZONE_VOCAB.get(zone_key, {})
    try:
        response = claude.messages.create(
            model=CLAUDE_HAIKU_MODEL,
            max_tokens=350,
            system=(
                "You are a technical art director for isometric SVG illustration. "
                "Synthesize quality coaching into 3-5 concrete actionable bullet points. "
                "Each bullet: one specific geometric, color, or composition instruction. "
                "Start each with a dash. No vague adjectives. Direct instructions only."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Zone: {zone_key}\nArchetype: {vocab.get('archetype', '')}\n"
                    f"Key elements: {vocab.get('key_elements', '')}\n\n"
                    f"Quality coaching from recent iterations:\n" +
                    "\n".join(coaching_parts) +
                    "\n\nSynthesize into 3-5 actionable style improvements:"
                ),
            }],
        )
        notes = response.content[0].text.strip()
        if "style_evolution" not in gen_state:
            gen_state["style_evolution"] = {}
        gen_state["style_evolution"][zone_key] = notes
        print(f"[style_evolution] {zone_key}: synthesized {len(notes)} chars")
    except Exception as e:
        print(f"[style_evolution] {zone_key}: synthesis failed ({e}) — skipping")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — README generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_readme(
    zone_data: dict,
    gen_state: dict,
    quality_state: dict,
    zone_key: str,
    narrative: str,
    iteration: int,
    timestamp: str,
) -> None:
    """Write README.md with latest SVG as hero and full 2x2 city zone grid."""
    meta  = zone_data["city_meta"]
    zones = zone_data["zones"]

    def bar(pct: int) -> str:
        filled = min(10, int(pct / 10))
        return "█" * filled + "░" * (10 - filled) + f" {pct}%"

    rows = []
    for zk, z in zones.items():
        q     = quality_state.get("zones", {}).get(zk, {})
        avg   = q.get("avg_score", 0)
        q_str = f"{avg:.0f}/40" if avg else "—"
        star  = " ★" if zk == zone_key else ""
        rows.append(
            f"| **{z['label']}{star}** | {z['layer']} | {z['phase']}"
            f" | {bar(z['progress'])} | {q_str} |"
        )

    current_zone = zones[zone_key]

    lines = [
        f"# {meta['name']}",
        "",
        f"> {meta['tagline']}",
        "",
        f"*{CREATOR} &nbsp;·&nbsp; SEC Ref: {SEC_REF} &nbsp;·&nbsp; Iteration {iteration:04d}*",
        "",
        "---",
        "",
        f"## Latest — {current_zone['label']}",
        "",
        f'<img src="assets/svg/{zone_key}.svg" width="100%" alt="{current_zone["label"]}"/>',
        "",
        f"*{current_zone['phase']} · {current_zone['progress']}% complete*",
        "",
        narrative,
        "",
        "---",
        "",
        "## City Status",
        "",
        "| Zone | Layer | Phase | Progress | Quality |",
        "|------|-------|-------|----------|---------||",
        *rows,
        "",
        f"**Overall momentum:** {meta['overall_phase']}",
        "",
        "---",
        "",
        "## All Zones",
        "",
        "<table>",
        "<tr>",
        '<td width="50%">',
        f'<img src="assets/svg/city_hall.svg" width="100%" alt="City Hall"/>',
        '<p align="center"><strong>City Hall</strong></p>',
        "</td>",
        '<td width="50%">',
        f'<img src="assets/svg/gateway_district.svg" width="100%" alt="Gateway District"/>',
        '<p align="center"><strong>Gateway District</strong></p>',
        "</td>",
        "</tr>",
        "<tr>",
        '<td width="50%">',
        f'<img src="assets/svg/intelligence_core.svg" width="100%" alt="Intelligence Core"/>',
        '<p align="center"><strong>Intelligence Core</strong></p>',
        "</td>",
        '<td width="50%">',
        f'<img src="assets/svg/sovereign_quarters.svg" width="100%" alt="Sovereign Quarters"/>',
        '<p align="center"><strong>Sovereign Quarters</strong></p>',
        "</td>",
        "</tr>",
        "</table>",
        "",
        "---",
        "",
        f"*Updated: {timestamp} &nbsp;·&nbsp; [Construction log](VISUAL_LOG.md) &nbsp;·&nbsp; [Gallery](gallery.md)*",
        "",
        f"*{LICENSE} &nbsp;·&nbsp; Albert Lane*",
    ]

    README_MD.write_text("\n".join(lines))
    print(f"[generate_readme] README.md written — iteration {iteration:04d}, {len(lines)} lines")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[main] Creative engine v3 — {timestamp}")

    if not os.environ.get("CLAUDE_API_KEY", ""):
        print("[main] CLAUDE_API_KEY not configured — skipping this run")
        sys.exit(0)

    if GEN_STATE.exists():
        age = datetime.datetime.utcnow().timestamp() - GEN_STATE.stat().st_mtime
        if age > 4 * 3600:
            print(f"[STALL] generation_state.json is {age/3600:.1f}h old — pipeline may be stalled", flush=True)

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

    print(f"[main] Phase 2 — {CLAUDE_SVG_MODEL} SVG generation...")
    svg = generate_zone_svg(
        zone_key, zone_data, narrative, iteration,
        style_evolution_notes=style_notes,
        previous_coaching=previous_coaching,
    )
    print(f"[main] SVG: {len(svg)} chars, valid={svg.startswith('<svg')}")

    svg_path = write_svg(zone_key, svg, iteration)
    append_visual_log(zone_key, zone_data, narrative, iteration, timestamp)
    update_gallery(zone_data, gen_state, quality_state)

    print("[main] Phase 4 — Style evolution synthesis...")
    synthesize_style_evolution(zone_key, quality_state, gen_state)
    save_gen_state(gen_state, zone_key, narrative[:120])

    print("[main] Phase 5 — Writing README.md...")
    generate_readme(zone_data, gen_state, quality_state, zone_key, narrative, iteration, timestamp)

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
