# SEC #17684-273-411-436 | Washington County Report #[PLACEHOLDER-WC] | Washington State Report #[PLACEHOLDER-WS]
# §16 CFR PART 465 | PROPRIETARY TO ALBERT LANE ESTATE | albertlane.net
"""
SimCity Web Catalog Builder
Reads generation_state.json and updates/latest.json, builds static HTML portal
at site/simcity/index.html in T2 GlacierNoir palette.
Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-07-21
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROVENANCE_ID = "SEC #17684-273-411-436"
REPO_ROOT = Path(__file__).parent.parent.parent
GENERATION_STATE_PATH = REPO_ROOT / "generation_state.json"
UPDATES_PATH = REPO_ROOT / "updates" / "latest.json"
SITE_OUT = REPO_ROOT / "site" / "simcity" / "index.html"

T2 = {
    "bg": "#0A1628",
    "surface": "#0F1F3D",
    "accent": "#153A5F",
    "accent2": "#2A5A8F",
    "danger": "#FF3868",
    "text": "#E0E8F4",
    "muted": "#7A90B0",
    "border": "#1E3A5A",
}


def _canary_token(content_id: str) -> str:
    daily_nonce = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw = f"{PROVENANCE_ID}|{content_id}|{daily_nonce}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _phase_card(phase_id: str, label: str, status: str, note: str) -> str:
    color_map = {
        "completed": "#2A7A4A",
        "in_progress": "#2A5A8F",
        "not_started": "#3A3A5A",
    }
    badge_color = color_map.get(status, "#3A3A5A")
    badge_label = status.replace("_", " ").upper()
    return f"""
    <div class="phase-card" style="border-left:3px solid {badge_color}">
      <div class="phase-header">
        <span class="phase-id">{phase_id}</span>
        <span class="phase-badge" style="background:{badge_color}">{badge_label}</span>
      </div>
      <div class="phase-label">{label}</div>
      <div class="phase-note">{note}</div>
    </div>"""


def _zone_grid(gen_state: dict) -> str:
    zones = gen_state.get("zone_order", ["city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"])
    history = gen_state.get("history", [])
    style_evo = gen_state.get("style_evolution", {})
    cells = ""
    for zone in zones:
        zone_label = zone.replace("_", " ").title()
        style_note = style_evo.get(zone, "Evolving…")
        cells += f"""
        <div class="zone-cell">
          <div class="zone-label">{zone_label}</div>
          <div class="zone-coord">5D:[{zones.index(zone)},0,0,0,0]</div>
          <div class="zone-style">{style_note[:80] if style_note else "Evolving…"}</div>
        </div>"""
    iteration = gen_state.get("iteration", 0)
    return f"""
    <section class="grid-section">
      <h2>Creative Engine — Iteration {iteration}</h2>
      <div class="zone-grid">{cells}</div>
    </section>"""


def _deliverable_section(updates: dict) -> str:
    phase = updates.get("phase", "Phase 17")
    repos = updates.get("active_repos", [
        "roadmaps", "lane-mcp", "sqlxml", "tauri-rustxml",
        "macrohard", "government", "simcity", "procurement",
        "maps", "ip-forensics", "sovereign-canary",
    ])
    cards = ""
    deliverable_map = {
        "roadmaps": ("Navigation Hub", "Phase 17", "C-Stream™ canonical spec, receiver beacon, sovereign architecture"),
        "lane-mcp": ("MCP Gateway", "Phase 13", "procurement_engine + government modules; 25 tools"),
        "sqlxml": ("XML Pipeline", "Phase 8", "AR/VR storage layer; WriteMode::ARPayload; WebSocket ar_bridge"),
        "tauri-rustxml": ("Sovereign Browser", "Phase 8", "Froi Browser fusion; frontend_bridge WASM; nexus.browser.* + nexus.ar.*"),
        "macrohard": ("MacroHarder™", "Phase 14", "5D cell model; lane-mcp cache (35 tools); kriging5d"),
        "government": ("Gov SEC-IRS-FTC", "Phase 1", "8 forensic modules; evidence ledger; logistics portal"),
        "simcity": ("Creative Hub", "Phase 9", "Autonomous web portal; T2 GlacierNoir SVG engine"),
        "procurement": ("Delivery Hub", "Phase 11", "deliverables/ scaffold; push/pull engine; lane_procurement_pull"),
        "maps": ("Terrain Intelligence", "Phase 12", "Topographic analysis; contours; watershed; 78 tests"),
        "ip-forensics": ("IP Forensics", "Phase 12", "JS/TS structural scanner; provenance bomber; canary seeder"),
        "sovereign-canary": ("Canary Monitor", "Phase 10", "DMCA lifecycle; /integrity; log verification; /feed.atom"),
        "channel-1-news": ("Channel-1 News", "Phase 9", "SimCity post-step; C-Stream /beacon; news mesh worker"),
        "finance-slack-other": ("Finance Bridge", "Phase 9", "Self-hosted OC bridge; webhook receiver; Slack notify"),
    }
    for repo in repos:
        info = deliverable_map.get(repo, (repo.title(), "Active", "Sovereign estate component"))
        title, phase_tag, desc = info
        cards += f"""
        <div class="deliverable-card">
          <div class="del-top">
            <span class="del-title">{title}</span>
            <span class="del-phase">{phase_tag}</span>
          </div>
          <div class="del-repo">albert-lane-org/{repo}</div>
          <div class="del-desc">{desc}</div>
        </div>"""
    return f"""
    <section class="deliverables-section">
      <h2>Estate Deliverables — {phase}</h2>
      <div class="deliverables-grid">{cards}</div>
    </section>"""


def _macrohard_teaser() -> str:
    return """
    <section class="teaser-section">
      <h2>MacroHarder™ — Live Preview</h2>
      <div class="teaser-grid">
        <div class="teaser-card">
          <div class="teaser-label">5D Workbook</div>
          <div class="teaser-coords">
            <span class="coord-badge">COL</span>
            <span class="coord-badge">ROW</span>
            <span class="coord-badge">LAYER</span>
            <span class="coord-badge" style="color:#FF3868">TIME</span>
            <span class="coord-badge" style="color:#2A5A8F">DOMAIN</span>
          </div>
          <div class="teaser-desc">Excel taken to a fifth-dimensional level. Cells are volumes; sheets are 5D tensors. Procurement and terrain data cached live via lane-mcp.</div>
        </div>
        <div class="teaser-card">
          <div class="teaser-label">Procurement Module</div>
          <div class="teaser-desc">
            <strong>Sample:</strong> Permit pipeline board · EV ledger · Vendor reliability<br>
            Data sourced from albert-lane-org/procurement via lane-mcp gateway.
          </div>
          <div class="teaser-status">Status: Awaiting <code>CLOUDFLARE_API_TOKEN</code> for live deploy</div>
        </div>
        <div class="teaser-card">
          <div class="teaser-label">Terrain Module</div>
          <div class="teaser-desc">
            Oregon DEM elevation lattice bound to MacroHarder (col, row, layer) volume view.<br>
            Runoff · Erosion · Hillshade · Soil pH — 78 tests passing.
          </div>
          <div class="teaser-status">Status: Code-complete · Phase 12 ✅</div>
        </div>
      </div>
    </section>"""


def _sec_forensics_section() -> str:
    modules = [
        ("network_visualizer.py", "Corporate Network & Adjacency Visualizer", "WHOIS, DNS, RDAP, Vis.js evidence graph → federal_evidence_cache.db"),
        ("irs_tracker.py", "IRS Financial Discrepancy & Flow Tracker", "XBRL concept fetcher, numpy z-score anomaly detection, circular flow DFS"),
        ("ftc_auditor.py", "FTC Trade & Corporate Identity Auditor", "Deception pattern regex, endpoint identity verification, SEC cross-check"),
        ("evidence_ledger.py", "Cross-Agency Forensic Evidence Ledger", "Cryptographic chain ledger, Merkle root, JSONL + SQLite"),
        ("water_utilities.py", "Water Treatment & Utilities Engine", "Hazen-Williams pipe flow, EPA MCL compliance check, USGS ingestion"),
        ("permit_system.py", "Commercial & Permit Acquisition System", "OR/WA zoning, EIA thresholds, expired permit detection"),
        ("logistics_portal.py", "Oregon Logistics Portal", "FMCSA carrier registry, route optimizer, underwriter matching"),
        ("employment_system.py", "Employment Department System", "UI benefit calculator (OR/WA), job matching engine, SUTA tax"),
    ]
    rows = ""
    for fname, title, desc in modules:
        rows += f"""
          <tr>
            <td class="mod-file"><code>{fname}</code></td>
            <td class="mod-title">{title}</td>
            <td class="mod-desc">{desc}</td>
          </tr>"""
    return f"""
    <section class="sec-section">
      <h2>Government SEC-IRS-FTC Forensic Suite</h2>
      <p class="sec-note">All modules write to <code>federal_evidence_cache.db</code> (SQLite). SSRF-guarded. No credentials committed.</p>
      <table class="mod-table">
        <thead><tr><th>Module</th><th>Title</th><th>Description</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>"""


def _css() -> str:
    return f"""
    :root {{
      --bg: {T2['bg']};
      --surface: {T2['surface']};
      --accent: {T2['accent']};
      --accent2: {T2['accent2']};
      --danger: {T2['danger']};
      --text: {T2['text']};
      --muted: {T2['muted']};
      --border: {T2['border']};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.6; }}
    a {{ color: var(--accent2); text-decoration: none; }}
    a:hover {{ color: var(--danger); }}
    .header {{ background: var(--surface); border-bottom: 2px solid var(--border); padding: 24px 40px; display: flex; justify-content: space-between; align-items: center; }}
    .header-title {{ font-size: 22px; font-weight: bold; letter-spacing: 2px; color: var(--text); }}
    .header-sub {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .sec-badge {{ background: var(--danger); color: #fff; padding: 3px 8px; font-size: 11px; border-radius: 3px; }}
    .nav-tabs {{ background: var(--surface); border-bottom: 1px solid var(--border); display: flex; padding: 0 40px; }}
    .tab {{ padding: 12px 20px; cursor: pointer; color: var(--muted); font-size: 13px; border-bottom: 2px solid transparent; }}
    .tab.active {{ color: var(--text); border-bottom-color: var(--accent2); }}
    .main {{ max-width: 1400px; margin: 0 auto; padding: 32px 40px; }}
    section {{ margin-bottom: 48px; }}
    h2 {{ font-size: 16px; letter-spacing: 1px; color: var(--accent2); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }}
    .zone-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
    .zone-cell {{ background: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 4px; }}
    .zone-label {{ font-weight: bold; color: var(--text); margin-bottom: 4px; }}
    .zone-coord {{ color: var(--accent2); font-size: 11px; margin-bottom: 8px; }}
    .zone-style {{ color: var(--muted); font-size: 12px; }}
    .deliverables-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .deliverable-card {{ background: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 4px; }}
    .del-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
    .del-title {{ font-weight: bold; font-size: 14px; }}
    .del-phase {{ color: var(--accent2); font-size: 11px; background: var(--accent); padding: 2px 6px; border-radius: 2px; }}
    .del-repo {{ color: var(--muted); font-size: 11px; margin-bottom: 8px; }}
    .del-desc {{ color: var(--text); font-size: 12px; line-height: 1.5; }}
    .phase-card {{ background: var(--surface); border: 1px solid var(--border); padding: 14px 16px; border-radius: 4px; margin-bottom: 8px; }}
    .phase-header {{ display: flex; justify-content: space-between; margin-bottom: 6px; }}
    .phase-id {{ font-weight: bold; color: var(--text); }}
    .phase-badge {{ font-size: 10px; padding: 2px 6px; border-radius: 2px; color: #fff; }}
    .phase-label {{ color: var(--text); font-size: 13px; margin-bottom: 4px; }}
    .phase-note {{ color: var(--muted); font-size: 11px; }}
    .teaser-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .teaser-card {{ background: var(--surface); border: 1px solid var(--accent); padding: 16px; border-radius: 4px; }}
    .teaser-label {{ font-weight: bold; color: var(--accent2); margin-bottom: 8px; font-size: 15px; }}
    .coord-badge {{ display: inline-block; background: var(--accent); color: var(--text); padding: 2px 8px; margin: 2px; font-size: 11px; border-radius: 2px; }}
    .teaser-desc {{ color: var(--text); font-size: 12px; line-height: 1.6; margin-top: 8px; }}
    .teaser-status {{ color: var(--muted); font-size: 11px; margin-top: 8px; font-style: italic; }}
    .sec-section table {{ width: 100%; border-collapse: collapse; }}
    .mod-table th {{ background: var(--accent); color: var(--text); padding: 10px 12px; text-align: left; font-size: 12px; }}
    .mod-table td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 12px; vertical-align: top; }}
    .mod-table tr:hover td {{ background: var(--surface); }}
    .mod-file {{ color: var(--accent2); white-space: nowrap; }}
    .mod-title {{ font-weight: bold; }}
    .mod-desc {{ color: var(--muted); }}
    .sec-note {{ color: var(--muted); font-size: 12px; margin-bottom: 16px; }}
    .footer {{ background: var(--surface); border-top: 1px solid var(--border); padding: 20px 40px; color: var(--muted); font-size: 11px; text-align: center; }}
    code {{ background: var(--accent); padding: 1px 4px; border-radius: 2px; font-family: 'Courier New', monospace; font-size: 11px; }}
    @media (max-width: 900px) {{
      .deliverables-grid, .teaser-grid, .zone-grid {{ grid-template-columns: 1fr; }}
      .main {{ padding: 16px; }}
    }}
    """


def build_portal() -> None:
    gen_state = _load_json(GENERATION_STATE_PATH, {})
    updates = _load_json(UPDATES_PATH, {})

    iteration = gen_state.get("iteration", 0)
    last_run = gen_state.get("last_run") or updates.get("dispatched_at") or "Not yet run"
    canary = _canary_token("simcity-portal-index")
    built_at = datetime.now(timezone.utc).isoformat()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="data-canary-token" content="{canary}">
  <meta name="provenance" content="{PROVENANCE_ID}">
  <title>Albert Lane Estate — SimCity Sovereign Portal</title>
  <style>{_css()}</style>
</head>
<body>
  <header class="header">
    <div>
      <div class="header-title">⬡ ALBERT LANE ESTATE</div>
      <div class="header-sub">Sovereign Infrastructure Portal · albertlane.net · Iteration #{iteration}</div>
    </div>
    <div>
      <span class="sec-badge">SEC #{PROVENANCE_ID.split('#')[1]}</span>
    </div>
  </header>
  <nav class="nav-tabs">
    <div class="tab active">Deliverables</div>
    <div class="tab">Architecture</div>
    <div class="tab">Forensics</div>
    <div class="tab">MacroHarder™</div>
  </nav>
  <main class="main">
    {_deliverable_section(updates)}
    {_zone_grid(gen_state)}
    {_macrohard_teaser()}
    {_sec_forensics_section()}
  </main>
  <footer class="footer">
    {PROVENANCE_ID} | §16 CFR PART 465 | PROPRIETARY TO ALBERT LANE ESTATE | albertlane.net<br>
    Built: {built_at} | Last dispatch: {last_run} | Canary: {canary[:16]}…
  </footer>
</body>
</html>"""

    SITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_OUT.write_text(html, encoding="utf-8")
    print(f"[web_catalog_builder] Portal built → {SITE_OUT}")
    print(f"[web_catalog_builder] Iteration: {iteration} | Canary: {canary[:16]}…")


if __name__ == "__main__":
    build_portal()
    sys.exit(0)
