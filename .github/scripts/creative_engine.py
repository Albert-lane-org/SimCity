#!/usr/bin/env python3
"""
SimCity Creative Engine - v2 (Claude-only)

Phase 1 - Claude Haiku : reads updates/latest.json + generation history
                          -> writes narrative advancement
Phase 2 - Claude Sonnet: reads zone + narrative + style evolution notes
                          + previous coaching -> generates isometric SVG
Phase 3 - Write outputs : SVG with provenance, VISUAL_LOG.md, gen_state

Runs at :20 every hour. v1 creative engine (scripts/creative_engine.py) runs at :15.
Both read from updates/latest.json dispatched by simcity-dispatch.yml at :00.

AUTHORED: Albert Lane | SovereignAudits(tm) | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, json, sys, re, hashlib, datetime, textwrap
from pathlib import Path
from anthropic import Anthropic

ROOT           = Path(__file__).parent.parent
UPDATES_LATEST = ROOT / "updates" / "latest.json"
GEN_STATE      = ROOT / "generation_state.json"
VISUAL_QUALITY = ROOT / "visual_quality_state.json"
SVG_DIR        = ROOT / "assets" / "svg"
VISUAL_LOG     = ROOT / "VISUAL_LOG.md"
GALLERY_MD     = ROOT / "gallery.md"

claude = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

T2 = {
    "bg":    "#04070E",
    "blue":  "#3B82F6",
    "ice":   "#F0F4FF",
    "mid":   "#1E3A5F",
    "dark":  "#0A1628",
    "line":  "#2563EB",
    "amber": "#B8621A",
}

ZONE_VOCAB = {
    "city_hall": {
        "archetype": "imposing civic hall - symmetrical facade, central clock tower, wide entrance steps, two flanking wings",
        "mood": "authority, permanence, civic gravity",
        "lighting": "overhead, casting short sharp shadows down-right",
    },
    "gateway_district": {
        "archetype": "transit hub - elevated walkways, converging rail lines, arched connectors, signal towers",
        "mood": "motion, connection, infrastructure in use",
        "lighting": "ambient dusk, blue-tinted, long shadows",
    },
    "intelligence_core": {
        "archetype": "data center block - dense server stacks, cooling towers venting, status-light grids, cable conduit runs",
        "mood": "precision, latency, controlled environment",
        "lighting": "internal glow from server indicators, cold blue wash",
    },
    "sovereign_quarters": {
        "archetype": "modular interface tower - stacked terminal bays, antenna array on roof, glass-panel facade, entry airlock",
        "mood": "sovereignty, attention, quiet alertness",
        "lighting": "mixed - warm amber at entry, cold blue from screens above",
    },
}

DEFAULT_ZONES = {
    "city_hall":          {"label": "City Hall",          "layer": "navigation",     "phase": "Foundation",  "progress": 50, "status": "operational",       "description": "The civic anchor.",       "detail": ""},
    "gateway_district":   {"label": "Gateway District",   "layer": "infrastructure", "phase": "Integration", "progress": 50, "status": "active_construction", "description": "The connective tissue.",   "detail": ""},
    "intelligence_core":  {"label": "Intelligence Core",  "layer": "data",           "phase": "Integration", "progress": 50, "status": "active_construction", "description": "The data layer.",          "detail": ""},
    "sovereign_quarters": {"label": "Sovereign Quarters", "layer": "interface",      "phase": "Integration", "progress": 50, "status": "active_construction", "description": "The interface layer.",     "detail": ""},
}

CREATOR = "Albert Lane | SovereignAudits(tm)"
SEC_REF = "17684-273-411-436"
LICENSE = "SOVEREIGN IP LICENSE v1"


def load_state():
    gen_state = json.loads(GEN_STATE.read_text()) if GEN_STATE.exists() else {
        "iteration": 0, "zone_index": 0,
        "zone_order": ["city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"],
        "last_run": "", "last_zone": "", "history": [], "style_evolution": {},
    }

    update = {}
    if UPDATES_LATEST.exists():
        try:
            update = json.loads(UPDATES_LATEST.read_text())
        except Exception:
            pass

    zones_list = update.get("zones", [])
    zones_dict = {}
    for z in zones_list:
        key = z.get("zone", "")
        if key:
            zones_dict[key] = {
                "label":       key.replace("_", " ").title(),
                "layer":       z.get("layer", ""),
                "phase":       z.get("active_phase", ""),
                "progress":    z.get("completion", 0),
                "status":      z.get("status", "planned"),
                "description": z.get("description", f"{key.replace('_', ' ').title()} layer"),
                "detail":      "",
            }

    for key, defaults in DEFAULT_ZONES.items():
        if key not in zones_dict:
            zones_dict[key] = defaults

    agg = update.get("aggregate", {})
    zone_data = {
        "city_meta": {
            "name":          "SimCity",
            "tagline":       "Walls rise. The blueprint holds.",
            "overall_phase": agg.get("current_phase", "Construction"),
        },
        "zones": zones_dict,
        "signal": update.get("signal", "Infrastructure in motion."),
    }

    return zone_data, gen_state


def next_zone(gen_state):
    order = gen_state["zone_order"]
    idx   = gen_state["zone_index"] % len(order)
    return order[idx]


def load_quality_state():
    if VISUAL_QUALITY.exists():
        try:
            return json.loads(VISUAL_QUALITY.read_text())
        except Exception:
            pass
    return {}


def get_previous_coaching(zone_key, quality_state):
    zone_scores = quality_state.get("zones", {}).get(zone_key, {}).get("scores", [])
    if not zone_scores:
        return ""
    return zone_scores[-1].get("coaching", "")


def get_style_evolution_notes(zone_key, gen_state):
    return gen_state.get("style_evolution", {}).get(zone_key, "")


def save_gen_state(gen_state, zone_key, narrative_summary):
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


def advance_narrative(zone_key, zone_data, gen_state):
    zone    = zone_data["zones"][zone_key]
    meta    = zone_data["city_meta"]
    history = gen_state.get("history", [])[-6:]
    history_text = "\n".join(
        f"- Iteration {h['iteration']}: {h['zone']} - {h['summary']}"
        for h in history
    ) or "First run - no prior history."

    resp = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": (
            f"You are the narrator for SimCity, a public civic infrastructure project.\n"
            f"Write ONE paragraph (3-5 sentences) advancing the narrative for the zone below.\n"
            f"Civic voice, factual, construction progress perspective. No markdown.\n\n"
            f"City: {meta['name']} - {meta['tagline']}\n"
            f"Phase: {meta['overall_phase']}\n\n"
            f"Zone: {zone['label']} ({zone['layer']} layer)\n"
            f"Progress: {zone['progress']}%\nStatus: {zone['status']}\n"
            f"Description: {zone['description']}\n\n"
            f"Recent history:\n{history_text}\n\n"
            f"Rules: One paragraph only. Civic voice. Reference progress %. "
            f"Do not say: vibrant, revolutionize, innovative, seamless."
        )}],
    )
    return resp.content[0].text.strip()


def generate_zone_svg(zone_key, zone_data, narrative, iteration, style_evolution_notes="", previous_coaching=""):
    zone  = zone_data["zones"][zone_key]
    vocab = ZONE_VOCAB.get(zone_key, {"archetype": zone_key, "mood": "civic", "lighting": "ambient"})
    pct   = zone["progress"]

    if pct < 40:
        construction_note = "Foundation poured. Steel skeleton rising to 2-3 floors. Construction crane dominant. Upper floors are empty steel frames."
    elif pct < 70:
        construction_note = "Structure closed in. Facade panels on lower floors, upper incomplete. Mix of dark and lit windows. One crane at upper-right."
    elif pct < 90:
        construction_note = "Near complete. Full facade present. All window openings filled. Interior lighting throughout. No cranes."
    else:
        construction_note = "Complete and operational. All windows lit. Clean facade. Civic flag or antenna at apex. Building is alive."

    evolution_clause = f"\nLEARNED STYLE IMPROVEMENTS:\n{style_evolution_notes}\n" if style_evolution_notes else ""
    coaching_clause  = f"\nPREVIOUS CRITIQUE - address this:\n{previous_coaching}\n" if previous_coaching else ""

    system = (
        f"You are a technical SVG illustrator specialising in isometric civic architecture.\n"
        f"Produce complete, valid, browser-renderable SVG. Raw SVG only, starting with <svg.\n\n"
        f"ISOMETRIC GEOMETRY: ViewBox: 0 0 800 520. x-axis right-down 30 deg, z-axis straight up.\n"
        f"Top face: {T2['ice']} 15% opacity over {T2['blue']}. Left face: {T2['mid']}. Right face: {T2['dark']}.\n"
        f"Background: solid {T2['bg']}. Accent: {T2['blue']}. Window: {T2['ice']}. Grid: {T2['line']} 20%.\n"
        f"Amber {T2['amber']}: MAX ONE element.\n\n"
        f"ZONE: {vocab['archetype']}\nMOOD: {vocab['mood']}\nLIGHTING: {vocab['lighting']}\n\n"
        f"CONSTRUCTION STATE (iteration {iteration}, {pct}% complete):\n{construction_note}\n"
        f"NARRATIVE: {narrative[:200]}\n"
        f"{evolution_clause}{coaching_clause}\n"
        f"Produce a single complete <svg> element. Portfolio quality."
    )

    resp = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": (
            f"Generate the isometric SVG for {zone['label']}. "
            f"Phase: {zone['phase']}. Progress: {pct}%. Iteration {iteration}."
        )}],
    )

    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    if not raw.startswith("<svg"):
        raise ValueError(f"Claude returned non-SVG output: {raw[:120]}")

    return raw


def _blake2b_hex(data):
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def inject_svg_provenance(svg, zone_key, iteration):
    content_hash = _blake2b_hex(svg.encode())
    tag = content_hash[:8]
    metadata_block = (
        f'<metadata><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        f' xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:sc="https://albertlane.net/sovereign/ns/">'
        f'<rdf:Description><dc:creator>{CREATOR}</dc:creator><dc:rights>{LICENSE}</dc:rights>'
        f'<sc:hash>{tag}</sc:hash><sc:sec_ref>{SEC_REF}</sc:sec_ref>'
        f'<sc:zone>{zone_key}</sc:zone><sc:iteration>{iteration}</sc:iteration>'
        f'</rdf:Description></rdf:RDF></metadata>'
    )
    prov_comment = f'<!-- SOVEREIGN: creator="{CREATOR}" hash="{tag}" sec="{SEC_REF}" zone="{zone_key}" iter="{iteration}" -->'
    if '<metadata>' not in svg:
        match = re.search(r'<svg[^>]*>', svg)
        if match:
            pos = match.end()
            svg = svg[:pos] + metadata_block + svg[pos:]
    svg = svg.rstrip()
    if svg.endswith('</svg>'):
        svg = svg[:-6] + '\n' + prov_comment + '\n</svg>'
    return svg


def write_svg(zone_key, svg, iteration):
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    svg_with_prov = inject_svg_provenance(svg, zone_key, iteration)
    current_path  = SVG_DIR / f"{zone_key}.svg"
    snapshot_path = SVG_DIR / f"{zone_key}_i{iteration:04d}.svg"
    current_path.write_text(svg_with_prov)
    snapshot_path.write_text(svg_with_prov)
    content_hash = _blake2b_hex(svg.encode())
    print(f"[write_svg] {current_path.name} hash={content_hash[:12]}... iter={iteration}")
    return str(current_path)


def append_visual_log(zone_key, zone_data, narrative, iteration, timestamp, quality_total=0, quality_label=""):
    zone     = zone_data["zones"][zone_key]
    repo     = os.environ.get("GITHUB_REPOSITORY", "Albert-lane-org/SimCity")
    svg_url  = f"https://raw.githubusercontent.com/{repo}/main/assets/svg/{zone_key}.svg"
    q_line   = f"**Quality:** {quality_total}/40 ({quality_label})" if quality_total else ""
    entry    = textwrap.dedent(f"""
    ## Iteration {iteration:04d} - {timestamp}
    **Zone:** {zone['label']} &nbsp;*&nbsp; **Progress:** {zone['progress']}% &nbsp;*&nbsp; **Phase:** {zone['phase']}{f' &nbsp;*&nbsp; {q_line}' if q_line else ''}
    {narrative}
    ![{zone['label']}]({svg_url})
    ---
    """).lstrip()
    header_needed = not VISUAL_LOG.exists() or VISUAL_LOG.stat().st_size == 0
    with open(VISUAL_LOG, "a") as f:
        if header_needed:
            f.write(
                "# SimCity - Visual Construction Log\n\n"
                "Hourly record of the city as it is built. Append-only.\n"
                f"Authored: {CREATOR} | {SEC_REF}\n\n---\n\n"
            )
        f.write(entry)


def update_gallery(zone_data, gen_state, quality_state):
    repo      = os.environ.get("GITHUB_REPOSITORY", "Albert-lane-org/SimCity")
    now       = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    meta      = zone_data.get("city_meta", {})
    iteration = gen_state.get("iteration", 0)
    lines     = [
        "# SimCity - Public Gallery", "",
        f"> {meta.get('tagline', 'Walls rise. The blueprint holds.')}", "",
        f"*{CREATOR} &nbsp;*&nbsp; SEC Ref: {SEC_REF}*  ",
        f"*{meta.get('name', 'SimCity')} &nbsp;*&nbsp; Iteration {iteration:04d}*",
        "", "---", "",
    ]
    for zone_key, zone in zone_data.get("zones", {}).items():
        svg_url = f"https://raw.githubusercontent.com/{repo}/main/assets/svg/{zone_key}.svg"
        zone_q  = quality_state.get("zones", {}).get(zone_key, {})
        lines  += [
            f"## {zone['label']}", "",
            f"**Layer:** {zone['layer']} &nbsp;*&nbsp; **Phase:** {zone['phase']} &nbsp;*&nbsp; **Progress:** {zone['progress']}%",
            "", f"![{zone['label']}]({svg_url})", "", zone.get("description", ""), "", "---", "",
        ]
    lines += [f"*Updated: {now} &nbsp;*&nbsp; {LICENSE}*"]
    GALLERY_MD.write_text("\n".join(lines))
    print(f"[update_gallery] gallery.md updated - iteration {iteration}")


def main():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[main] Creative engine v2 - {timestamp}")

    zone_data, gen_state = load_state()
    quality_state        = load_quality_state()
    zone_key             = next_zone(gen_state)
    iteration            = gen_state["iteration"] + 1
    zone_label           = zone_data["zones"][zone_key]["label"]

    style_notes      = get_style_evolution_notes(zone_key, gen_state)
    previous_coaching = get_previous_coaching(zone_key, quality_state)

    print(f"[main] Zone: {zone_label} | Iteration: {iteration}")

    print("[main] Phase 1 - Claude narrative...")
    narrative = advance_narrative(zone_key, zone_data, gen_state)

    print("[main] Phase 2 - Claude SVG generation...")
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
