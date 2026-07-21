#!/usr/bin/env python3
# Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | 2026-07-20 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
skill_improver.py — Self-Referential Skill Improvement Engine

Extends the existing self_improve_creative.py pattern to cover the new
marketing and web scripts. Reads quality signals from:
  - marketing_state.json: reach scores, A/B test results, self-critiques
  - canary_state.json: trigger rates, domain diversity, anomalies
  - visual_quality_state.json: per-zone SVG quality scores

Then proposes and applies ONE surgical improvement to a target script.

TARGET ROTATION (auto-selects based on lowest-performing metric):
  web_generator.py       → if site build errors or low SVG embed count
  marketing_engine.py    → if reach score < 30% or A/B keeps failing
  canary_probe.py        → if trigger rate < 10% after 5+ iterations
  channel1_sync.py       → if RSS/feed errors or article count stagnating

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os
import re
import sys
import json
import datetime
from pathlib import Path
from anthropic import Anthropic

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
MKT_STATE    = ROOT / "marketing_state.json"
CANARY_STATE = ROOT / "canary_state.json"
VQ_STATE     = ROOT / "visual_quality_state.json"
SKILL_LOG    = ROOT / "SKILL_IMPROVEMENT_LOG.md"

SCRIPTS_DIR  = ROOT / ".github" / "scripts"
SCRIPTS = {
    "web_generator":    SCRIPTS_DIR / "web_generator.py",
    "marketing_engine": SCRIPTS_DIR / "marketing_engine.py",
    "canary_probe":     SCRIPTS_DIR / "canary_probe.py",
    "channel1_sync":    SCRIPTS_DIR / "channel1_sync.py",
}

CREATOR = "Albert Lane | SovereignAudits™"
SEC_REF = "17684-273-411-436"
MODEL   = "claude-sonnet-4-6"

client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY", ""))


def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default


def select_target() -> str:
    override = os.environ.get("SKILL_TARGET", "auto")
    if override != "auto":
        return override

    mkt    = load_json(MKT_STATE,    {"campaigns": [], "reach_score": 0})
    canary = load_json(CANARY_STATE, {"reach_score": 0.0, "triggered": [], "tokens": []})
    vq     = load_json(VQ_STATE,     {"zones": {}})

    reach       = canary.get("reach_score", 0.0)
    n_tokens    = len(canary.get("tokens", []))
    n_triggered = len(canary.get("triggered", []))
    campaigns   = mkt.get("campaigns", [])
    trigger_rate = n_triggered / max(1, n_tokens)

    if n_tokens >= 15 and trigger_rate < 0.1:
        return "canary_probe"
    if len(campaigns) >= 5 and reach < 0.30:
        return "marketing_engine"

    zone_avgs = [zd.get("avg_score", 40) for zd in vq.get("zones", {}).values()]
    if zone_avgs and min(zone_avgs) < 10:
        return "web_generator"
    if len(campaigns) > 2 and len(campaigns) % 5 == 0:
        return "channel1_sync"

    prev_log = SKILL_LOG.read_text()[-2000:] if SKILL_LOG.exists() else ""
    if "marketing_engine" in prev_log[-500:]:
        return "web_generator"
    if "web_generator" in prev_log[-500:]:
        return "channel1_sync"
    if "channel1_sync" in prev_log[-500:]:
        return "canary_probe"
    return "marketing_engine"


def build_marketing_context() -> str:
    mkt    = load_json(MKT_STATE, {"campaigns": [], "reach_score": 0})
    canary = load_json(CANARY_STATE, {"reach_score": 0.0})
    campaigns = mkt.get("campaigns", [])
    tail = campaigns[-3:] if campaigns else []
    return (
        f"Reach score: {canary.get('reach_score', 0.0):.0%}\n"
        f"Campaigns generated: {len(campaigns)}\n"
        f"A/B winner: {mkt.get('ab_winner', 'unknown')}\n"
        f"Last self-critique: {mkt.get('self_critique', 'none')}\n"
        f"Last 3 headlines: {[c.get('headline_a', '') for c in tail]}\n"
    )


def build_canary_context() -> str:
    canary = load_json(CANARY_STATE, {})
    n_tok  = len(canary.get("tokens", []))
    n_tri  = len(canary.get("triggered", []))
    return (
        f"Tokens issued: {n_tok}\n"
        f"Triggers received: {n_tri}\n"
        f"Trigger rate: {n_tri/max(1,n_tok):.0%}\n"
        f"Domains seen: {len(canary.get('domains_seen', []))}\n"
        f"Incidents: {len(canary.get('incidents', []))}\n"
    )


def build_vq_context() -> str:
    vq = load_json(VQ_STATE, {"zones": {}})
    lines = []
    for zk, zd in vq.get("zones", {}).items():
        lines.append(f"  {zk}: avg={zd.get('avg_score', 0):.1f}/40 streak={zd.get('below_threshold_streak', 0)}")
    return "\n".join(lines) or "  No quality data."


CONTEXT_BUILDERS = {
    "marketing_engine": build_marketing_context,
    "canary_probe":     build_canary_context,
    "web_generator":    build_vq_context,
    "channel1_sync":    build_marketing_context,
}

SCRIPT_FOCUS = {
    "marketing_engine": (
        "This script generates marketing campaigns. Focus on: prompt quality, "
        "A/B test logic, reach score utilisation, self-critique depth, "
        "and JSON output reliability."
    ),
    "canary_probe": (
        "This script manages Sovereign Canary tokens. Focus on: token generation "
        "uniqueness, beacon server resilience, reach score formula accuracy, "
        "anomaly detection sensitivity, and HTTP error handling."
    ),
    "web_generator": (
        "This script builds the SimCity website. Focus on: SVG embedding fidelity, "
        "hero copy generation quality, CSS rendering of zone cards, "
        "feed.json schema completeness, and Cloudflare Pages compatibility."
    ),
    "channel1_sync": (
        "This script syncs Channel-1-News content. Focus on: RSS feed validity, "
        "JSON feed schema conformance, article listing completeness, "
        "canary token embedding in HTML, and Cloudflare routing."
    ),
}


def improve_script(target: str) -> bool:
    script_path = SCRIPTS.get(target)
    if not script_path or not script_path.exists():
        print(f"[skill_improver] Script not found: {target}", file=sys.stderr)
        return False

    script_content = script_path.read_text()
    context_fn     = CONTEXT_BUILDERS.get(target, lambda: "No specific context.")
    context        = context_fn()
    focus          = SCRIPT_FOCUS.get(target, "General quality improvement.")

    log_tail = ""
    if SKILL_LOG.exists():
        text = SKILL_LOG.read_text()
        log_tail = text[-3000:] if len(text) > 3000 else text

    system = (
        "You are a senior Python engineer reviewing scripts in a recursive "
        "self-improving marketing and creative pipeline for a civic infrastructure project.\n\n"
        f"Script focus area:\n{focus}\n\n"
        "Your task: propose ONE surgical improvement to the script.\n\n"
        "CRITICAL RULES:\n"
        "- ONE change only. No full rewrites.\n"
        "- BEFORE/AFTER must be exact Python — no ellipsis, no pseudocode.\n"
        "- Risk must be LOW or MEDIUM.\n"
        "- Preserve ALL attribution headers (Albert Lane / SEC ref).\n"
        "- No new third-party imports.\n"
        "- Do not remove the chain-of-custody/provenance outputs.\n\n"
        "Output format (machine-parsed):\n"
        "IMPROVEMENT_TARGET: <8 words>\n"
        "RISK: LOW | MEDIUM\n"
        "RATIONALE: <2 sentences>\n"
        "BEFORE:\n```python\n<exact lines to replace>\n```\n"
        "AFTER:\n```python\n<replacement lines>\n```\n"
        "END"
    )

    user = (
        f"Script: {script_path.name}\n\n"
        f"Performance context:\n{context}\n\n"
        f"Recent improvement log:\n{log_tail[-800:]}\n\n"
        f"Script content (first 5000 chars):\n```python\n{script_content[:5000]}\n```\n\n"
        "Propose one improvement. Output format as specified."
    )

    if not os.environ.get("CLAUDE_API_KEY"):
        print("[skill_improver] No CLAUDE_API_KEY — skipping improvement.")
        return False

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    output = resp.content[0].text.strip()
    print(f"[skill_improver] Response preview: {output[:300]}...")

    target_match = re.search(r"IMPROVEMENT_TARGET:\s*(.+)", output)
    risk_match   = re.search(r"RISK:\s*(LOW|MEDIUM|HIGH)", output)
    before_match = re.search(r"BEFORE:\s*```python\n(.*?)```", output, re.DOTALL)
    after_match  = re.search(r"AFTER:\s*```python\n(.*?)```",  output, re.DOTALL)

    imp_target = target_match.group(1).strip() if target_match else "unspecified"
    risk       = risk_match.group(1).strip()   if risk_match   else "UNKNOWN"
    before     = before_match.group(1)         if before_match else ""
    after      = after_match.group(1)          if after_match  else ""

    patched = False
    if risk in ("LOW", "MEDIUM") and before and after:
        if before.strip() in script_content:
            new_script = script_content.replace(before, after, 1)
            script_path.write_text(new_script)
            patched = True
            print(f"[skill_improver] Patch applied to {script_path.name}: {imp_target}")
        else:
            print(f"[skill_improver] BEFORE block not found verbatim — logged only.", file=sys.stderr)
    elif risk == "HIGH":
        print(f"[skill_improver] HIGH risk patch deferred for human review.")

    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "APPLIED" if patched else ("DEFERRED (high risk)" if risk == "HIGH" else "LOGGED")
    entry  = (
        f"\n\n## {ts_now} — Skill Improvement: {script_path.name}\n\n"
        f"**Target:** {imp_target}  \n"
        f"**Risk:** {risk}  \n"
        f"**Status:** {status}  \n\n"
        f"```\n{output[:600]}\n```\n\n"
        f"---\n*{CREATOR} | SEC Ref: {SEC_REF}*"
    )
    header_needed = not SKILL_LOG.exists() or SKILL_LOG.stat().st_size == 0
    with open(SKILL_LOG, "a") as f:
        if header_needed:
            f.write(
                "# Skill Improvement Log — SimCity Extended Pipeline\n"
                "Self-referential improvement of marketing, web, and canary scripts.\n"
                f"Authored: {CREATOR} · albertlane.net\n"
                f"SEC Whistleblower No. {SEC_REF}\n\n"
            )
        f.write(entry)

    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"improvement_target={imp_target}\n")
            f.write(f"patched={str(patched).lower()}\n")
            f.write(f"target_script={target}\n")
            f.write(f"risk={risk}\n")

    return patched


def main():
    print("[skill_improver] Starting skill improvement cycle...")
    target  = select_target()
    print(f"[skill_improver] Selected target: {target}")
    patched = improve_script(target)
    print(f"[skill_improver] Done. Patched={patched}")


if __name__ == "__main__":
    main()
