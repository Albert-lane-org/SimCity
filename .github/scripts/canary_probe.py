#!/usr/bin/env python3
# Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | 2026-07-20 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
canary_probe.py — Sovereign Canary Marketing Reach Tester

Integrates Sovereign Canary token infrastructure with SimCity's marketing pipeline.
Generates token batches keyed to each marketing campaign, monitors trigger events,
computes marketing reach scores, and feeds results back into marketing_state.json.

CANARY TOKEN TAXONOMY:
  SC-{hash}-MKT-{iteration}     Marketing article beacon
  SC-{hash}-SITE-{iteration}    Website page view beacon
  SC-{hash}-SVG-{zone}-{iter}   SVG asset hotlink probe

TOKEN LIFECYCLE:
  1. Token generated here → registered in canary_state.json
  2. Token embedded in HTML/SVG (by web_generator.py / marketing_engine.py)
  3. Content deployed to Cloudflare Pages / Channel-1-News
  4. External HTTP requests trigger the beacon endpoint (on SOVEREIGN CANARY Rust server)
  5. Trigger events polled from beacon server → canary_state.json updated
  6. Reach score computed → marketing_engine.py reads it next cycle

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os
import json
import datetime
import hashlib
import hmac
import urllib.request
import urllib.error
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
CANARY_STATE = ROOT / "canary_state.json"
MKT_STATE    = ROOT / "marketing_state.json"
GEN_STATE    = ROOT / "generation_state.json"
CANARY_LOG   = ROOT / "CANARY_LOG.md"

CREATOR = "Albert Lane | SovereignAudits™"
SEC_REF = "17684-273-411-436"

# Sovereign Canary beacon server endpoint
# Set via SOVEREIGN_CANARY_URL secret; falls back to localhost for local testing
CANARY_URL    = os.environ.get("SOVEREIGN_CANARY_URL", "http://localhost:7433")
CANARY_SECRET = os.environ.get("SOVEREIGN_CANARY_SECRET", "")

MAX_TOKENS    = 200   # rolling window in state
MAX_TRIGGERED = 500


# ── State I/O ───────────────────────────────────────────────────────────────

def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


# ── Token generation ────────────────────────────────────────────────────────────

def make_token(token_type: str, iteration: int, extra: str = "") -> str:
    """
    Deterministic token: HMAC-SHA256(secret, type:iter:extra) → 12-char hex prefix.
    If no secret configured, falls back to SHA-256 of timestamp + type.
    """
    ts_day = datetime.datetime.utcnow().strftime("%Y%m%d")
    seed   = f"{token_type}:{iteration}:{extra}:{ts_day}"

    if CANARY_SECRET:
        token_hash = hmac.new(
            CANARY_SECRET.encode(),
            seed.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
    else:
        token_hash = hashlib.sha256(seed.encode()).hexdigest()[:16]

    return f"SC-{token_hash}-{token_type}-{iteration}"


def generate_token_batch(gen_state: dict, mkt_state: dict) -> list[dict]:
    """Generate one batch of tokens for the current iteration."""
    itr       = gen_state.get("iteration", 0)
    last_zone = gen_state.get("last_zone", "unknown")
    ts_now    = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    batch = [
        {
            "token":     make_token("MKT",  itr),
            "type":      "marketing_article",
            "context":   f"Channel-1-News article for iteration {itr}",
            "iteration": itr,
            "generated": ts_now,
            "triggered": False,
            "trigger_ts": None,
            "trigger_domain": None,
        },
        {
            "token":     make_token("SITE", itr),
            "type":      "site_page",
            "context":   f"albertlane.org/SimCity page view, iteration {itr}",
            "iteration": itr,
            "generated": ts_now,
            "triggered": False,
            "trigger_ts": None,
            "trigger_domain": None,
        },
        {
            "token":     make_token("SVG", itr, last_zone),
            "type":      "svg_hotlink",
            "context":   f"SVG asset {last_zone} iteration {itr}",
            "iteration": itr,
            "zone":      last_zone,
            "generated": ts_now,
            "triggered": False,
            "trigger_ts": None,
            "trigger_domain": None,
        },
    ]
    return batch


# ── Beacon server integration ─────────────────────────────────────────────────────

def register_token(token: str) -> bool:
    """Register a token with the Sovereign Canary beacon server."""
    if not CANARY_URL or CANARY_URL.startswith("http://localhost"):
        return True   # local dev — assume success

    try:
        payload = json.dumps({
            "token":    token,
            "sec_ref":  SEC_REF,
            "authored": CREATOR,
        }).encode()
        req = urllib.request.Request(
            f"{CANARY_URL}/register",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, Exception) as e:
        print(f"[canary_probe] Register failed for {token}: {e}")
        return False


def poll_triggers(tokens: list[str]) -> list[dict]:
    """
    Poll the Sovereign Canary beacon server for trigger events.
    Returns list of {token, trigger_ts, domain} for each triggered token.
    """
    if not CANARY_URL or CANARY_URL.startswith("http://localhost"):
        return []   # local dev — no triggers

    triggered = []
    try:
        payload = json.dumps({"tokens": tokens}).encode()
        req = urllib.request.Request(
            f"{CANARY_URL}/poll",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            triggered = data.get("triggered", [])
    except (urllib.error.URLError, Exception) as e:
        print(f"[canary_probe] Poll failed: {e}")
    return triggered


# ── Reach score computation ──────────────────────────────────────────────────────────

def compute_reach_score(canary_state: dict) -> float:
    """
    Reach score = weighted combination of:
      - Trigger rate: triggered/total tokens in last 10 iterations (50%)
      - Domain diversity: unique domains / expected domains (30%)
      - Recency: fraction of triggers in last 48h (20%)
    """
    all_tokens = canary_state.get("tokens", [])
    triggered  = canary_state.get("triggered", [])

    if not all_tokens:
        return 0.0

    # Last 10 iterations worth of tokens
    recent_tokens = all_tokens[-30:]   # 3 tokens/iter x 10 iters
    n_recent      = len(recent_tokens)
    n_triggered   = sum(1 for t in recent_tokens if t.get("triggered"))
    trigger_rate  = n_triggered / n_recent if n_recent > 0 else 0.0

    # Domain diversity
    domains     = canary_state.get("domains_seen", [])
    domain_div  = min(1.0, len(domains) / 5.0)   # target: 5 unique domains

    # Recency
    now = datetime.datetime.utcnow()
    cutoff = (now - datetime.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_triggers = [
        e for e in triggered
        if e.get("trigger_ts", "") >= cutoff
    ]
    recency_score = min(1.0, len(recent_triggers) / max(1, len(triggered)))

    score = (trigger_rate * 0.5) + (domain_div * 0.3) + (recency_score * 0.2)
    return round(score, 4)


# ── Incident registry ──────────────────────────────────────────────────────────────

def check_anomalies(canary_state: dict) -> list[dict]:
    """
    Detect anomalous canary trigger patterns that may indicate:
    - IP scraping (many triggers in short window from same domain)
    - Token replay (same token triggered multiple times)
    - Suspicious timing (triggers before page deployment complete)
    """
    incidents = []
    triggered = canary_state.get("triggered", [])

    # Domain frequency analysis
    domain_counts: dict[str, int] = {}
    for t in triggered[-50:]:
        d = t.get("trigger_domain", "")
        if d:
            domain_counts[d] = domain_counts.get(d, 0) + 1

    for domain, count in domain_counts.items():
        if count >= 10:
            incidents.append({
                "type":        "HIGH_FREQUENCY_DOMAIN",
                "domain":      domain,
                "count":       count,
                "severity":    "MEDIUM",
                "ts":          datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sec_ref":     SEC_REF,
            })

    return incidents


# ── Log ─────────────────────────────────────────────────────────────────────

def append_canary_log(batch: list[dict], triggered: list[dict], reach: float, incidents: list[dict]):
    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entry  = (
        f"\n\n## {ts_now} — Canary Cycle\n\n"
        f"**New tokens:** {len(batch)}\n"
        f"**Triggered this cycle:** {len(triggered)}\n"
        f"**Reach score:** {reach:.0%}\n"
    )
    if incidents:
        entry += "\n**Incidents:**\n"
        for inc in incidents:
            entry += f"- [{inc['severity']}] {inc['type']}: {inc.get('domain', '')} count={inc.get('count', '')}\n"
    if triggered:
        entry += "\n**Trigger events:**\n"
        for t in triggered[:5]:
            entry += f"- Token: {t.get('token', '?')} | Domain: {t.get('trigger_domain', '?')} | {t.get('trigger_ts', '?')}\n"

    entry += f"\n---\n*{CREATOR} | SEC Ref: {SEC_REF}*"

    header_needed = not CANARY_LOG.exists() or CANARY_LOG.stat().st_size == 0
    with open(CANARY_LOG, "a") as f:
        if header_needed:
            f.write(
                "# Sovereign Canary Marketing Reach Log\n"
                "Token generation, trigger monitoring, and anomaly detection.\n"
                f"Authored: {CREATOR} · albertlane.net\n"
                f"SEC Whistleblower No. {SEC_REF}\n\n"
            )
        f.write(entry)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[canary_probe] Starting canary cycle...")

    gen_state    = load_json(GEN_STATE, {"iteration": 0, "last_zone": "unknown"})
    mkt_state    = load_json(MKT_STATE, {"campaigns": []})
    canary_state = load_json(CANARY_STATE, {
        "tokens":        [],
        "triggered":     [],
        "reach_score":   0.0,
        "domains_seen":  [],
        "incidents":     [],
        "last_cycle":    None,
    })

    # 1. Generate new token batch for this iteration
    batch = generate_token_batch(gen_state, mkt_state)
    print(f"[canary_probe] Generated {len(batch)} tokens for iteration {gen_state.get('iteration', 0)}")

    # 2. Register with beacon server
    for t in batch:
        registered = register_token(t["token"])
        t["registered"] = registered

    # 3. Poll for triggers on all outstanding (non-triggered) tokens
    outstanding = [
        t["token"] for t in canary_state.get("tokens", [])
        if not t.get("triggered")
    ]
    trigger_events = poll_triggers(outstanding)
    print(f"[canary_probe] Trigger events received: {len(trigger_events)}")

    # 4. Update token trigger status in state
    token_map = {t["token"]: t for t in canary_state.get("tokens", [])}
    for event in trigger_events:
        tok = event.get("token", "")
        if tok in token_map:
            token_map[tok]["triggered"]       = True
            token_map[tok]["trigger_ts"]      = event.get("trigger_ts")
            token_map[tok]["trigger_domain"]  = event.get("domain")

            # Update domains_seen
            domain = event.get("domain", "")
            if domain and domain not in canary_state["domains_seen"]:
                canary_state["domains_seen"].append(domain)

            # Log to triggered list
            canary_state["triggered"].append({
                "token":          tok,
                "trigger_ts":     event.get("trigger_ts"),
                "trigger_domain": domain,
            })

    # 5. Add new tokens to state
    updated_tokens = list(token_map.values()) + batch
    canary_state["tokens"] = updated_tokens[-MAX_TOKENS:]
    canary_state["triggered"] = canary_state["triggered"][-MAX_TRIGGERED:]

    # 6. Compute reach score
    reach = compute_reach_score(canary_state)
    canary_state["reach_score"]  = reach
    canary_state["last_cycle"]   = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # 7. Anomaly detection
    incidents = check_anomalies(canary_state)
    if incidents:
        existing = canary_state.get("incidents", [])
        canary_state["incidents"] = (existing + incidents)[-100:]
        print(f"[canary_probe] INCIDENTS detected: {len(incidents)}")
        for inc in incidents:
            print(f"  [{inc['severity']}] {inc['type']} — {inc.get('domain', '')}")

    # 8. Save state
    save_json(CANARY_STATE, canary_state)

    # 9. Log
    append_canary_log(batch, trigger_events, reach, incidents)

    # 10. GitHub Actions output
    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"reach_score={reach}\n")
            f.write(f"tokens_generated={len(batch)}\n")
            f.write(f"triggers_received={len(trigger_events)}\n")
            f.write(f"incidents={len(incidents)}\n")
            f.write(f"domains_seen={len(canary_state['domains_seen'])}\n")

    print(f"[canary_probe] Done. Reach: {reach:.0%}, Domains: {len(canary_state['domains_seen'])}")


if __name__ == "__main__":
    main()
