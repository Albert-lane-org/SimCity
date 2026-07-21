# SEC #17684-273-411-436 | Washington County Report #[PLACEHOLDER-WC] | Washington State Report #[PLACEHOLDER-WS]
# §16 CFR PART 465 | PROPRIETARY TO ALBERT LANE ESTATE | albertlane.net
"""
Roadmap Sync Pipeline
Pulls the latest sanitized dispatch from updates/latest.json and builds a
structured design schematic consumed by web_catalog_builder.py.
Transforms raw repo commits into billboard-style readable updates with
3D/5D coordinate metadata.
Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-07-21
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROVENANCE_ID = "SEC #17684-273-411-436"
REPO_ROOT = Path(__file__).parent.parent.parent
UPDATES_PATH = REPO_ROOT / "updates" / "latest.json"
SCHEMATIC_OUT = REPO_ROOT / "site" / "simcity" / "roadmap_schematic.json"
GENERATION_STATE_PATH = REPO_ROOT / "generation_state.json"

REPO_DOMAIN_MAP = {
    "roadmaps": 0,
    "lane-mcp": 1,
    "sqlxml": 0,
    "tauri-rustxml": 0,
    "macrohard": 3,
    "government": 2,
    "simcity": 0,
    "procurement": 1,
    "maps": 3,
    "ip-forensics": 2,
    "sovereign-canary": 2,
    "channel-1-news": 1,
    "finance-slack-other": 1,
}


def _load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _billboard_entry(repo: str, phase: str, summary: str, iteration: int, domain: int) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    col = hash(repo) % 100
    row = iteration % 50
    layer = int(phase.split()[-1]) if phase.split()[-1].isdigit() else 0
    return {
        "repo": repo,
        "phase": phase,
        "summary": summary,
        "billboard_text": f"[{repo.upper()}] {summary}",
        "coordinates_5d": {
            "col": col,
            "row": row,
            "layer": layer,
            "time": iteration,
            "domain": domain,
        },
        "rendered_at": ts,
        "provenance": PROVENANCE_ID,
    }


def build_schematic() -> dict:
    updates = _load_json(UPDATES_PATH, {})
    gen_state = _load_json(GENERATION_STATE_PATH, {})

    iteration = gen_state.get("iteration", 0)
    dispatched_at = updates.get("dispatched_at", datetime.now(timezone.utc).isoformat())

    active_deliverables = [
        ("roadmaps", "Phase 17", "C-Stream™ spec, phase 17 sovereign architecture, receiver beacon"),
        ("lane-mcp", "Phase 13", "procurement_engine + government MCP modules; 25 registered tools"),
        ("sqlxml", "Phase 8", "WriteMode::ARPayload AR/VR storage; WebSocket ar_bridge; 150+ tests"),
        ("tauri-rustxml", "Phase 8", "Froi Browser IP claim; frontend_bridge WASM; nexus.browser.* nexus.ar.*"),
        ("macrohard", "Phase 14", "5D CellAddress; kriging5d; lane-mcp cache 35 tools; 86 tests"),
        ("government", "Phase 1", "8 forensic modules; evidence ledger; logistics portal; employment system"),
        ("simcity", "Phase 9", "Autonomous web portal; T2 GlacierNoir; roadmap sync pipeline"),
        ("procurement", "Phase 11", "deliverables/ delivery hub; push/pull engine; lane_procurement_pull"),
        ("maps", "Phase 12", "Topographic analysis; contours; watershed; 78 tests passing"),
        ("ip-forensics", "Phase 12", "JS/TS structural scanner; provenance_bomber; canary_seeder"),
        ("sovereign-canary", "Phase 10", "DMCA lifecycle; /integrity endpoint; Atom feed; log verify CI"),
    ]

    billboard_entries = []
    for repo, phase, summary in active_deliverables:
        domain = REPO_DOMAIN_MAP.get(repo, 0)
        billboard_entries.append(_billboard_entry(repo, phase, summary, iteration, domain))

    sec_schematic = {
        "schematic_version": "1.0",
        "provenance": PROVENANCE_ID,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "dispatched_at": dispatched_at,
        "iteration": iteration,
        "billboard_entries": billboard_entries,
        "sec_env": {
            "source_repo": "albert-lane-org/government",
            "pipeline": "government → roadmaps → simcity",
            "forensic_modules": [
                "network_visualizer", "irs_tracker", "ftc_auditor",
                "evidence_ledger", "water_utilities", "permit_system",
                "logistics_portal", "employment_system",
            ],
        },
        "macrohard_teasers": {
            "procurement_sample": {
                "tool": "lane_procurement_pull",
                "source": "albert-lane-org/procurement",
                "preview": "Permit pipeline · EV ledger · Vendor reliability",
            },
            "maps_sample": {
                "tool": "lane_maps_contours",
                "source": "albert-lane-org/maps",
                "preview": "Oregon terrain lattice · Elevation DEM · Watershed",
            },
        },
    }

    SCHEMATIC_OUT.parent.mkdir(parents=True, exist_ok=True)
    SCHEMATIC_OUT.write_text(json.dumps(sec_schematic, indent=2), encoding="utf-8")
    print(f"[roadmap_sync] Schematic written → {SCHEMATIC_OUT}")
    print(f"[roadmap_sync] {len(billboard_entries)} billboard entries | iteration {iteration}")
    return sec_schematic


if __name__ == "__main__":
    schematic = build_schematic()
    print(json.dumps({"status": "ok", "entries": len(schematic["billboard_entries"])}, indent=2))
    sys.exit(0)
