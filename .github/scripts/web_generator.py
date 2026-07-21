#!/usr/bin/env python3
# Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | 2026-07-20 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
web_generator.py — SimCity → albertlane.org/SimCity Site Builder

Reads the current SimCity creative state, SVG assets, and marketing content,
then renders a full static HTML site deployable to Cloudflare Pages at
albertlane.org/SimCity.

OUTPUTS:
  site/index.html     — main landing page (T2 GlacierNoir palette)
  site/gallery.html   — all SVG iterations with quality scores
  site/feed.json      — JSON feed for Channel-1-News sync
  site/canary.html    — Sovereign Canary marketing reach probe page

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os
import json
import datetime
import hashlib
import shutil
from pathlib import Path
from anthropic import Anthropic

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
GEN_STATE    = ROOT / "generation_state.json"
VQ_STATE     = ROOT / "visual_quality_state.json"
MKT_STATE    = ROOT / "marketing_state.json"
CANARY_STATE = ROOT / "canary_state.json"
SVG_DIR      = ROOT / "assets" / "svg"
SITE_DIR     = ROOT / "site"
UPDATES      = ROOT / "updates" / "latest.json"
FINGERPRINT  = ROOT / "ASSETS_FINGERPRINT.json"

# ── T2 GlacierNoir palette ────────────────────────────────────────────────────
T2 = {
    "bg":     "#04070E",
    "blue":   "#3B82F6",
    "ice":    "#F0F4FF",
    "mid":    "#1E3A5F",
    "dark":   "#0A1628",
    "line":   "#2563EB",
    "amber":  "#B8621A",
    "green":  "#22C55E",
    "red":    "#EF4444",
}

CREATOR  = "Albert Lane | SovereignAudits™"
SEC_REF  = "17684-273-411-436"
MODEL    = "claude-sonnet-4-6"

claude = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY", ""))


# ── State loaders ─────────────────────────────────────────────────────────────

def load_gen_state() -> dict:
    if GEN_STATE.exists():
        return json.loads(GEN_STATE.read_text())
    return {"iteration": 0, "history": [], "zone_order": [], "last_zone": None}


def load_vq_state() -> dict:
    if VQ_STATE.exists():
        return json.loads(VQ_STATE.read_text())
    return {"zones": {}}


def load_mkt_state() -> dict:
    if MKT_STATE.exists():
        return json.loads(MKT_STATE.read_text())
    return {"campaigns": [], "last_headline": "", "reach_score": 0}


def load_canary_state() -> dict:
    if CANARY_STATE.exists():
        return json.loads(CANARY_STATE.read_text())
    return {"tokens": [], "triggered": [], "reach_score": 0.0, "domains_seen": []}


def load_dispatch() -> dict:
    if UPDATES.exists():
        return json.loads(UPDATES.read_text())
    return {"signal": "Walls rise. The blueprint holds.", "zones": [], "momentum": "Construction"}


def load_fingerprint() -> dict:
    if FINGERPRINT.exists():
        return json.loads(FINGERPRINT.read_text())
    return {"assets": {}}


def collect_svgs() -> list[dict]:
    """Return sorted list of SVG metadata for gallery."""
    svgs = []
    vq   = load_vq_state()
    for svg_path in sorted(SVG_DIR.glob("*.svg"), reverse=True)[:24]:
        stem  = svg_path.stem                         # e.g. city_hall_042
        parts = stem.rsplit("_", 1)
        zone  = parts[0] if len(parts) == 2 else stem
        itr   = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
        mtime = datetime.datetime.utcfromtimestamp(svg_path.stat().st_mtime)

        scores = vq.get("zones", {}).get(zone, {}).get("scores", [])
        quality = next((s["total"] for s in reversed(scores) if s.get("iteration") == itr), None)

        svgs.append({
            "path":     svg_path,
            "rel":      f"assets/svg/{svg_path.name}",
            "zone":     zone,
            "iteration": itr,
            "quality":  quality,
            "mtime":    mtime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return svgs


# ── Claude-powered copy generation ───────────────────────────────────────────

def generate_hero_copy(gen_state: dict, dispatch: dict) -> dict:
    """Use Claude Sonnet to write fresh hero copy for the site."""
    if not os.environ.get("CLAUDE_API_KEY"):
        return {
            "headline":    "A civic infrastructure project, built in public.",
            "subhead":     "SimCity is the public face of the Albert Lane Digital Estate.",
            "cta":         "Explore the city →",
            "aria_summary": "SimCity — sovereign civic infrastructure, building in public.",
        }

    history = gen_state.get("history", [])[-6:]
    history_text = "\n".join(
        f"- Iteration {h['iteration']}: {h['zone']} — {h['summary']}"
        for h in history
    ) or "First run."

    mkt = load_mkt_state()
    reach = mkt.get("reach_score", 0)
    canary = load_canary_state()
    triggered = len(canary.get("triggered", []))

    resp = claude.messages.create(
        model=MODEL,
        max_tokens=400,
        system=(
            "You write sharp, civic-first copy for a sovereign infrastructure project. "
            "No corporate buzzwords. No startup clichés. The tone is architect-meets-journalist: "
            "precise, public-interest, understated authority.\n\n"
            "Output ONLY valid JSON with keys: headline, subhead, cta, aria_summary.\n"
            "headline: ≤10 words. subhead: 1 sentence. cta: ≤5 words with →. aria_summary: ≤20 words."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Current city signal: {dispatch.get('signal', 'Walls rise.')}\n"
                f"Build phase: {dispatch.get('momentum', 'Construction')}\n"
                f"Iteration: {gen_state.get('iteration', 0)}\n"
                f"Recent history:\n{history_text}\n"
                f"Marketing reach score: {reach}/100, canary triggers: {triggered}\n\n"
                "Write the hero copy. JSON only."
            ),
        }],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "headline":    "Sovereign infrastructure, built in public.",
            "subhead":     "SimCity is the public creative window into the Albert Lane Digital Estate.",
            "cta":         "Enter the city →",
            "aria_summary": "SimCity — sovereign civic infrastructure project.",
        }


# ── Zone status card renderer ─────────────────────────────────────────────────

ZONE_LABELS = {
    "city_hall":          "City Hall",
    "gateway_district":   "Gateway District",
    "intelligence_core":  "Intelligence Core",
    "sovereign_quarters": "Sovereign Quarters",
}

PHASE_COLORS = {
    "operational": T2["green"],
    "building":    T2["blue"],
    "planned":     T2["mid"],
}


def zone_card_html(zone_key: str, zone: dict, svgs: list[dict], vq: dict) -> str:
    label    = ZONE_LABELS.get(zone_key, zone_key.replace("_", " ").title())
    progress = zone.get("progress", 0)
    status   = zone.get("status", "planned")
    phase    = zone.get("phase", "—")
    layer    = zone.get("layer", "—")

    color = PHASE_COLORS.get(status, T2["mid"])

    zone_svgs = [s for s in svgs if s["zone"] == zone_key]
    img_block  = ""
    if zone_svgs:
        latest = zone_svgs[0]
        quality_label = f"Q: {latest['quality']}/40" if latest["quality"] is not None else ""
        svg_content = latest["path"].read_text()[:8000]
        img_block = f"""
        <div class="zone-svg" aria-label="{label} isometric view">
          {svg_content}
          <span class="quality-badge">{quality_label}</span>
        </div>"""

    bar_pct = min(100, max(0, int(progress * 100) if progress <= 1 else int(progress)))

    return f"""
    <article class="zone-card" data-zone="{zone_key}" data-status="{status}">
      <header class="zone-header">
        <span class="zone-status-dot" style="background:{color}" aria-label="{status}"></span>
        <h2 class="zone-name">{label}</h2>
        <span class="zone-layer">{layer}</span>
      </header>
      {img_block}
      <div class="zone-meta">
        <div class="zone-phase">{phase}</div>
        <div class="progress-track" aria-label="{bar_pct}% complete">
          <div class="progress-fill" style="width:{bar_pct}%;background:{color}"></div>
        </div>
        <span class="progress-label">{bar_pct}%</span>
      </div>
    </article>"""


# ── Main page builder ─────────────────────────────────────────────────────────

def build_index(gen_state: dict, dispatch: dict, svgs: list[dict], vq: dict, canary: dict) -> str:
    hero    = generate_hero_copy(gen_state, dispatch)
    ts_now  = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    itr     = gen_state.get("iteration", 0)
    sig     = dispatch.get("signal", "Walls rise. The blueprint holds.")

    zones_raw = dispatch.get("zones", [])
    zone_cards = ""
    for z in zones_raw:
        key = z.get("zone", "").lower().replace(" ", "_")
        zone_cards += zone_card_html(key, z, svgs, vq)

    reach   = canary.get("reach_score", 0.0)
    domains = canary.get("domains_seen", [])
    reach_html = f"""
    <div class="canary-reach" aria-label="Sovereign Canary marketing reach">
      <span class="canary-label">REACH</span>
      <span class="canary-score">{reach:.0%}</span>
      <span class="canary-domains">{len(domains)} domains confirmed</span>
    </div>""" if canary.get("triggered") else ""

    page_seed  = f"{ts_now}:{itr}:{sig}"
    page_hash  = hashlib.sha256(page_seed.encode()).hexdigest()[:16]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{hero.get('aria_summary', 'SimCity — sovereign infrastructure, built in public.')}">
  <meta property="og:title" content="SimCity — Albert Lane Digital Estate">
  <meta property="og:description" content="{hero.get('subhead', '')}">
  <meta property="og:url" content="https://albertlane.org/SimCity">
  <meta name="robots" content="index,follow">
  <title>SimCity — Albert Lane Digital Estate</title>
  <link rel="canonical" href="https://albertlane.org/SimCity">
  <link rel="stylesheet" href="styles.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Cormorant+Garamond:ital,wght@0,400;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
  <!-- Authored: {CREATOR} | Rendered: Claude Sonnet 4.6 | {ts_now} -->
  <!-- Auto-generated every hour. Direct edits will be overwritten. -->
  <!-- SEC Whistleblower No. {SEC_REF} | Page hash: {page_hash} -->

  <nav class="site-nav" aria-label="Site navigation">
    <a href="/" class="nav-brand">Albert Lane</a>
    <ul class="nav-links">
      <li><a href="/SimCity">SimCity</a></li>
      <li><a href="/SimCity/gallery.html">Gallery</a></li>
      <li><a href="https://github.com/Albert-lane-org/SimCity" rel="noopener">GitHub</a></li>
    </ul>
  </nav>

  <main id="main">
    <section class="hero" aria-labelledby="hero-headline">
      <div class="hero-content">
        <p class="hero-iteration">Iteration {itr} · {dispatch.get("momentum", "Construction")}</p>
        <h1 id="hero-headline" class="hero-headline">{hero.get("headline", "")}</h1>
        <p class="hero-subhead">{hero.get("subhead", "")}</p>
        <blockquote class="city-signal">
          <p>"{sig}"</p>
        </blockquote>
        <a href="#zones" class="hero-cta">{hero.get("cta", "Enter the city →")}</a>
      </div>
      {reach_html}
    </section>

    <section id="zones" class="zones-section" aria-labelledby="zones-heading">
      <h2 id="zones-heading" class="section-heading">The City Right Now</h2>
      <div class="zone-grid">
        {zone_cards}
      </div>
    </section>

    <section class="pipeline-section" aria-labelledby="pipeline-heading">
      <h2 id="pipeline-heading" class="section-heading">How It Works</h2>
      <div class="pipeline-diagram" role="img" aria-label="Recursive creative pipeline diagram">
        <div class="pipeline-step">
          <span class="step-label">Private Infrastructure</span>
          <span class="step-arrow">→</span>
        </div>
        <div class="pipeline-step">
          <span class="step-label">Sanitized Dispatch</span>
          <span class="step-arrow">→</span>
        </div>
        <div class="pipeline-step">
          <span class="step-label">Creative Engine</span>
          <span class="step-sub">Claude Haiku + Sonnet</span>
          <span class="step-arrow">→</span>
        </div>
        <div class="pipeline-step">
          <span class="step-label">Quality Scorer</span>
          <span class="step-sub">0–40 pts / zone</span>
          <span class="step-arrow">→</span>
        </div>
        <div class="pipeline-step">
          <span class="step-label">Style Evolution</span>
          <span class="step-sub">Learning loop</span>
          <span class="step-arrow">→</span>
        </div>
        <div class="pipeline-step pipeline-step--self">
          <span class="step-label">Self-Improve</span>
          <span class="step-sub">Rewrites own scripts</span>
          <span class="step-arrow loop-arrow">↩</span>
        </div>
        <div class="pipeline-step pipeline-step--web">
          <span class="step-label">Web Deploy</span>
          <span class="step-sub">This page · Cloudflare</span>
        </div>
      </div>
    </section>

    <section class="invite-section" aria-labelledby="invite-heading">
      <h2 id="invite-heading" class="section-heading">Open Invitation</h2>
      <p class="invite-copy">
        SimCity is the public face of a civic infrastructure project. The infrastructure
        is being built. The design needs to match its ambition.
      </p>
      <ul class="invite-list">
        <li><strong>Systems Typographers</strong> — Designers who understand that data has a visual grammar.</li>
        <li><strong>Civic UX Designers</strong> — People who've built public-facing digital infrastructure and hated how bad it was.</li>
        <li><strong>Motion Designers</strong> — Animation that communicates state, not decoration.</li>
      </ul>
      <a href="mailto:lane.albert@pm.me" class="contact-link">lane.albert@pm.me</a>
    </section>
  </main>

  <footer class="site-footer">
    <div class="footer-meta">
      <span>Albert Lane · SovereignAudits™ · albertlane.net</span>
      <span>SEC Ref: {SEC_REF}</span>
      <span>Last generated: {ts_now}</span>
      <span>Iteration {itr} · Hash: {page_hash}</span>
    </div>
    <p class="footer-copy">All IP belongs to Albert Lane. See <a href="https://github.com/Albert-lane-org/SimCity/blob/main/LICENSE.md">LICENSE.md</a>.</p>
  </footer>

  <!-- Sovereign Canary probe — passive reach beacon -->
  <script id="canary-probe" type="application/json" data-ref="{SEC_REF}">
    {{"iteration":{itr},"ts":"{ts_now}","hash":"{page_hash}"}}
  </script>
</body>
</html>"""


def build_gallery(svgs: list[dict], vq: dict) -> str:
    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    cards = ""
    for s in svgs:
        label   = ZONE_LABELS.get(s["zone"], s["zone"].replace("_", " ").title())
        quality = s["quality"]
        q_color = T2["green"] if (quality or 0) >= 26 else T2["amber"] if (quality or 0) >= 15 else T2["red"]
        q_label = f"{quality}/40" if quality is not None else "—"

        try:
            svg_content = s["path"].read_text()[:6000]
        except Exception:
            svg_content = '<rect width="400" height="300" fill="#0A1628"/>'

        cards += f"""
    <figure class="gallery-card" data-zone="{s['zone']}" data-iteration="{s['iteration']}">
      <div class="gallery-svg">{svg_content}</div>
      <figcaption class="gallery-caption">
        <span class="gallery-zone">{label}</span>
        <span class="gallery-iter">#{s['iteration']}</span>
        <span class="gallery-quality" style="color:{q_color}">{q_label}</span>
        <span class="gallery-ts">{s['mtime']}</span>
      </figcaption>
    </figure>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>SimCity Gallery — Albert Lane Digital Estate</title>
  <link rel="canonical" href="https://albertlane.org/SimCity/gallery.html">
  <link rel="stylesheet" href="styles.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
  <!-- Authored: {CREATOR} | Rendered: Claude Sonnet 4.6 | {ts_now} -->
  <!-- SEC Whistleblower No. {SEC_REF} -->
  <nav class="site-nav">
    <a href="/SimCity" class="nav-brand">← SimCity</a>
    <ul class="nav-links">
      <li><a href="/SimCity/gallery.html" class="active">Gallery</a></li>
      <li><a href="https://github.com/Albert-lane-org/SimCity" rel="noopener">GitHub</a></li>
    </ul>
  </nav>
  <main>
    <h1 class="gallery-heading">SVG Gallery</h1>
    <p class="gallery-meta">Isometric city zones · T2 GlacierNoir palette · Quality scored 0–40</p>
    <div class="gallery-grid">
      {cards}
    </div>
  </main>
  <footer class="site-footer">
    <div class="footer-meta">
      <span>Albert Lane · SovereignAudits™ · albertlane.net</span>
      <span>Generated: {ts_now}</span>
    </div>
  </footer>
</body>
</html>"""


def build_feed_json(gen_state: dict, dispatch: dict, svgs: list[dict], mkt: dict) -> dict:
    """JSON feed consumed by Channel-1-News sync."""
    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    latest_svg = svgs[0] if svgs else {}

    return {
        "feed_version":    "1.0",
        "generated":       ts_now,
        "source":          "SimCity · Albert Lane Digital Estate",
        "author":          CREATOR,
        "sec_ref":         SEC_REF,
        "iteration":       gen_state.get("iteration", 0),
        "city_signal":     dispatch.get("signal", ""),
        "momentum":        dispatch.get("momentum", "Construction"),
        "headline":        mkt.get("last_headline", "Sovereign infrastructure, built in public."),
        "reach_score":     mkt.get("reach_score", 0),
        "latest_zone":     gen_state.get("last_zone", ""),
        "latest_svg_url":  f"https://raw.githubusercontent.com/Albert-lane-org/SimCity/main/{latest_svg.get('rel', '')}",
        "site_url":        "https://albertlane.org/SimCity",
        "gallery_url":     "https://albertlane.org/SimCity/gallery.html",
        "zones":           dispatch.get("zones", []),
        "history_tail":    gen_state.get("history", [])[-3:],
    }


# ── CSS ───────────────────────────────────────────────────────────────────────

def build_css() -> str:
    return f""":root {{
  --bg:     {T2["bg"]};
  --blue:   {T2["blue"]};
  --ice:    {T2["ice"]};
  --mid:    {T2["mid"]};
  --dark:   {T2["dark"]};
  --line:   {T2["line"]};
  --amber:  {T2["amber"]};
  --green:  {T2["green"]};
  --red:    {T2["red"]};
  --font-sans:  'Inter', system-ui, sans-serif;
  --font-serif: 'Cormorant Garamond', Georgia, serif;
  --font-mono:  'JetBrains Mono', 'Courier New', monospace;
  --radius:  6px;
  --gap:    1.5rem;
  --max-w:  1200px;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html {{ scroll-behavior: smooth; }}

body {{
  background: var(--bg);
  color: var(--ice);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* ── Nav ── */
.site-nav {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--mid);
  position: sticky;
  top: 0;
  background: rgba(4,7,14,0.92);
  backdrop-filter: blur(12px);
  z-index: 100;
}}
.nav-brand {{ color: var(--ice); text-decoration: none; font-weight: 500; letter-spacing: .05em; }}
.nav-links {{ list-style: none; display: flex; gap: 1.5rem; }}
.nav-links a {{ color: var(--ice); text-decoration: none; opacity: .7; transition: opacity .2s; font-size: .875rem; }}
.nav-links a:hover, .nav-links a.active {{ opacity: 1; color: var(--blue); }}

/* ── Hero ── */
.hero {{
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 5rem 2rem 4rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--gap);
  align-items: start;
}}
.hero-iteration {{
  font-family: var(--font-mono);
  font-size: .75rem;
  color: var(--blue);
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: .75rem;
}}
.hero-headline {{
  font-family: var(--font-serif);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 400;
  line-height: 1.15;
  color: var(--ice);
  margin-bottom: 1rem;
}}
.hero-subhead {{
  font-size: 1.125rem;
  opacity: .75;
  max-width: 56ch;
  margin-bottom: 1.5rem;
}}
.city-signal {{
  border-left: 2px solid var(--blue);
  padding-left: 1rem;
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--ice);
  opacity: .85;
  margin-bottom: 2rem;
}}
.hero-cta {{
  display: inline-block;
  background: var(--blue);
  color: var(--bg);
  padding: .75rem 1.75rem;
  border-radius: var(--radius);
  text-decoration: none;
  font-weight: 500;
  font-size: .9rem;
  transition: background .2s, transform .15s;
}}
.hero-cta:hover {{ background: var(--line); transform: translateY(-1px); }}

/* ── Canary reach ── */
.canary-reach {{
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: .25rem;
  font-family: var(--font-mono);
  font-size: .75rem;
}}
.canary-label {{ color: var(--amber); letter-spacing: .1em; }}
.canary-score {{ font-size: 1.5rem; font-weight: 500; color: var(--green); }}
.canary-domains {{ opacity: .6; }}

/* ── Zones ── */
.zones-section {{
  max-width: var(--max-w);
  margin: 0 auto 4rem;
  padding: 0 2rem;
}}
.section-heading {{
  font-family: var(--font-serif);
  font-size: 1.75rem;
  font-weight: 400;
  color: var(--ice);
  margin-bottom: 2rem;
  padding-bottom: .5rem;
  border-bottom: 1px solid var(--mid);
}}
.zone-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--gap);
}}
.zone-card {{
  background: var(--dark);
  border: 1px solid var(--mid);
  border-radius: var(--radius);
  overflow: hidden;
  transition: border-color .2s, transform .15s;
}}
.zone-card:hover {{ border-color: var(--blue); transform: translateY(-2px); }}
.zone-header {{
  display: flex;
  align-items: center;
  gap: .75rem;
  padding: 1rem 1.25rem .75rem;
  border-bottom: 1px solid var(--mid);
}}
.zone-status-dot {{
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.zone-name {{ font-size: 1rem; font-weight: 500; flex: 1; }}
.zone-layer {{ font-family: var(--font-mono); font-size: .7rem; opacity: .5; }}
.zone-svg {{
  position: relative;
  background: var(--bg);
  padding: .5rem;
}}
.zone-svg svg {{
  width: 100%;
  height: auto;
  display: block;
}}
.quality-badge {{
  position: absolute;
  top: .5rem; right: .5rem;
  background: rgba(4,7,14,.85);
  font-family: var(--font-mono);
  font-size: .65rem;
  color: var(--blue);
  padding: .2rem .4rem;
  border-radius: 3px;
}}
.zone-meta {{
  padding: .75rem 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  gap: .4rem;
}}
.zone-phase {{ font-size: .8rem; opacity: .65; font-family: var(--font-mono); }}
.progress-track {{
  height: 4px;
  background: var(--mid);
  border-radius: 2px;
  overflow: hidden;
}}
.progress-fill {{
  height: 100%;
  border-radius: 2px;
  transition: width .4s ease;
}}
.progress-label {{ font-family: var(--font-mono); font-size: .7rem; opacity: .5; align-self: flex-end; }}

/* ── Pipeline ── */
.pipeline-section {{
  max-width: var(--max-w);
  margin: 0 auto 4rem;
  padding: 0 2rem;
}}
.pipeline-diagram {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .5rem;
  padding: 1.5rem;
  background: var(--dark);
  border: 1px solid var(--mid);
  border-radius: var(--radius);
}}
.pipeline-step {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .2rem;
}}
.step-label {{
  font-size: .8rem;
  font-weight: 500;
  white-space: nowrap;
}}
.step-sub {{
  font-family: var(--font-mono);
  font-size: .65rem;
  opacity: .55;
  white-space: nowrap;
}}
.step-arrow {{
  font-family: var(--font-mono);
  color: var(--blue);
  font-size: 1.1rem;
  align-self: center;
}}
.loop-arrow {{ color: var(--amber); }}
.pipeline-step--self .step-label {{ color: var(--amber); }}
.pipeline-step--web .step-label {{ color: var(--green); }}

/* ── Invite ── */
.invite-section {{
  max-width: var(--max-w);
  margin: 0 auto 4rem;
  padding: 0 2rem;
}}
.invite-copy {{ max-width: 60ch; opacity: .8; margin-bottom: 1.5rem; }}
.invite-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: .75rem;
  margin-bottom: 2rem;
}}
.invite-list li {{
  padding-left: 1.25rem;
  position: relative;
  opacity: .85;
}}
.invite-list li::before {{
  content: '◈';
  position: absolute;
  left: 0;
  color: var(--blue);
}}
.contact-link {{
  font-family: var(--font-mono);
  color: var(--blue);
  text-decoration: none;
  font-size: .95rem;
}}
.contact-link:hover {{ text-decoration: underline; }}

/* ── Gallery ── */
.gallery-heading {{
  font-family: var(--font-serif);
  font-size: 2rem;
  font-weight: 400;
  max-width: var(--max-w);
  margin: 3rem auto 0.5rem;
  padding: 0 2rem;
}}
.gallery-meta {{
  font-family: var(--font-mono);
  font-size: .75rem;
  opacity: .5;
  max-width: var(--max-w);
  margin: 0 auto 2rem;
  padding: 0 2rem;
}}
.gallery-grid {{
  max-width: var(--max-w);
  margin: 0 auto 4rem;
  padding: 0 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--gap);
}}
.gallery-card {{
  background: var(--dark);
  border: 1px solid var(--mid);
  border-radius: var(--radius);
  overflow: hidden;
}}
.gallery-svg {{ background: var(--bg); padding: .5rem; }}
.gallery-svg svg {{ width: 100%; height: auto; display: block; }}
.gallery-caption {{
  display: flex;
  flex-wrap: wrap;
  gap: .4rem;
  padding: .75rem 1rem;
  font-family: var(--font-mono);
  font-size: .7rem;
  border-top: 1px solid var(--mid);
}}
.gallery-zone {{ flex: 1; font-weight: 500; }}
.gallery-iter {{ opacity: .5; }}
.gallery-quality {{ font-weight: 500; }}
.gallery-ts {{ width: 100%; opacity: .4; }}

/* ── Footer ── */
.site-footer {{
  border-top: 1px solid var(--mid);
  padding: 2rem;
  font-family: var(--font-mono);
  font-size: .7rem;
  opacity: .5;
  max-width: var(--max-w);
  margin: 0 auto;
}}
.footer-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: .5rem;
}}
.footer-copy a {{ color: var(--blue); text-decoration: none; }}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .hero {{
    grid-template-columns: 1fr;
    padding: 3rem 1.25rem 2.5rem;
  }}
  .canary-reach {{ align-items: flex-start; }}
  .pipeline-diagram {{ flex-direction: column; align-items: flex-start; }}
  .zone-grid {{ grid-template-columns: 1fr; }}
}}"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[web_generator] Starting site build...")

    gen_state = load_gen_state()
    dispatch  = load_dispatch()
    vq        = load_vq_state()
    mkt       = load_mkt_state()
    canary    = load_canary_state()
    svgs      = collect_svgs()

    SITE_DIR.mkdir(parents=True, exist_ok=True)

    site_svg = SITE_DIR / "assets" / "svg"
    site_svg.mkdir(parents=True, exist_ok=True)
    for s in svgs:
        dst = site_svg / s["path"].name
        if not dst.exists():
            shutil.copy2(s["path"], dst)

    index_html   = build_index(gen_state, dispatch, svgs, vq, canary)
    gallery_html = build_gallery(svgs, vq)
    feed         = build_feed_json(gen_state, dispatch, svgs, mkt)
    css          = build_css()

    (SITE_DIR / "index.html").write_text(index_html)
    (SITE_DIR / "gallery.html").write_text(gallery_html)
    (SITE_DIR / "feed.json").write_text(json.dumps(feed, indent=2))
    (SITE_DIR / "styles.css").write_text(css)

    (SITE_DIR / "_redirects").write_text(
        "/SimCity           /index.html    200\n"
        "/SimCity/*         /index.html    200\n"
        "/SimCity/gallery   /gallery.html  200\n"
    )

    ts_now     = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    build_hash = hashlib.sha256(index_html.encode()).hexdigest()
    provenance = {
        "generated":   ts_now,
        "iteration":   gen_state.get("iteration", 0),
        "build_hash":  build_hash,
        "authored_by": CREATOR,
        "sec_ref":     SEC_REF,
        "pages": ["index.html", "gallery.html", "feed.json"],
        "svgs_embedded": len(svgs),
    }
    (SITE_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2))

    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"build_hash={build_hash}\n")
            f.write(f"site_dir={SITE_DIR}\n")
            f.write(f"iteration={gen_state.get('iteration', 0)}\n")

    print(f"[web_generator] Done. Pages: {len(list(SITE_DIR.glob('*.html')))}, SVGs embedded: {len(svgs)}")
    print(f"[web_generator] Build hash: {build_hash}")


if __name__ == "__main__":
    main()
