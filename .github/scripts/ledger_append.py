#!/usr/bin/env python3
# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-26 | SEC Whistleblower No. 17684-273-411-436
"""
ledger_append.py — Tier 2 Central Node ledger append engine.

Reads node_push_event client_payload from GITHUB_EVENT_PATH.
Validates FSH, computes HMAC tag, appends to chain.jsonl,
upserts index.json Phone Book, dispatches ledger_update_event to RoadMaps.
"""

import hashlib
import hmac as _hmac
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CHAIN_PATH = Path("ledger/chain.jsonl")
INDEX_PATH = Path("ledger/index.json")
FSH_RE = re.compile(r"^[0-9a-f]{64}$")

COL = {0: "A", 1: "A", 2: "A", 3: "A", 4: "B", 5: "B",
       6: "B", 7: "B", 8: "C", 9: "C", 10: "C", 11: "C",
       12: "D", 13: "D", 14: "D", 15: "D"}
ROW = {0: "1", 1: "1", 2: "1", 3: "1", 4: "2", 5: "2",
       6: "2", 7: "2", 8: "3", 9: "3", 10: "3", 11: "3",
       12: "4", 13: "4", 14: "4", 15: "4"}


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"[ledger_append] ERROR: {name} is not set — cannot proceed.", file=sys.stderr)
        sys.exit(1)
    return val


def make_hmac_tag(fsh: str, secret: str) -> str:
    return _hmac.new(
        key=secret.encode(),
        msg=fsh.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()[:16]


def compute_self_hash(entry: dict) -> str:
    d = {k: v for k, v in entry.items() if k != "self_hash"}
    canonical = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_chain() -> list:
    entries = []
    if CHAIN_PATH.exists():
        for line in CHAIN_PATH.read_text().splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def head_hash(chain: list) -> str:
    if not chain:
        return hashlib.sha256(b"").hexdigest()
    return chain[-1]["self_hash"]


def load_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {
        "schema_version": "1.0.0",
        "label": "ncl-phone-book",
        "genesis_hash": "e0eab61a4b2298a6",
        "last_updated": "",
        "node_count": 0,
        "nodes": {},
    }


def assign_grid(node_id: str) -> str:
    return COL[int(node_id[0], 16)] + ROW[int(node_id[1], 16)]


def _node_fsh_history(chain: list, node_id: str) -> list:
    return [e["fsh"] for e in chain if e.get("node_id") == node_id]


def compute_cert_status(node_entry: dict, new_fsh: str, chain: list, node_id: str) -> str:
    history = _node_fsh_history(chain, node_id)
    # Check last 10 entries for oscillation
    recent = history[-10:] if len(history) >= 10 else history
    if len(recent) >= 3:
        transitions = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i - 1])
        if transitions >= 3:
            return "oscillating"
    # Three consecutive identical FSH → stable
    if len(history) >= 2 and history[-1] == new_fsh and history[-2] == new_fsh:
        current = node_entry.get("cert_status", "pending")
        if current in ("stable", "seated"):
            return current
        return "stable"
    return node_entry.get("cert_status", "pending")


def compute_level(chain: list, node_id: str, new_fsh: str) -> str:
    history = _node_fsh_history(chain, node_id)
    if not history:
        return "nominal"
    recent = history[-10:]
    transitions = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i - 1])
    if transitions >= 3:
        return "alert"
    if history and history[-1] != new_fsh:
        return "warning"
    return "nominal"


def append_chain_entry(chain: list, node_id: str, fsh: str, tier: int, secret: str) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "prev_hash": head_hash(chain),
        "seq": len(chain),
        "node_id": node_id,
        "tier": tier,
        "fsh": fsh,
        "timestamp": ts,
        "hmac_tag": make_hmac_tag(fsh, secret),
        "level": compute_level(chain, node_id, fsh),
    }
    entry["self_hash"] = compute_self_hash(entry)
    with CHAIN_PATH.open("a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return entry


def upsert_index_node(index: dict, node_id: str, fsh: str, tier: int, secret: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    node = index["nodes"].get(node_id, {
        "grid_coord": assign_grid(node_id),
        "tier": tier,
        "cert_status": "pending",
        "last_fsh_tag": "",
        "last_certified": None,
        "hmac_tag": "",
        "push_count": 0,
        "last_seen": "",
    })
    chain = load_chain()
    node["cert_status"] = compute_cert_status(node, fsh, chain, node_id)
    node["last_fsh_tag"] = fsh[:8]
    node["push_count"] = node.get("push_count", 0) + 1
    node["last_seen"] = ts
    hmac_data = node_id + fsh[:8] + ts
    node["hmac_tag"] = _hmac.new(
        key=secret.encode(),
        msg=hmac_data.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()[:16]
    if node["cert_status"] == "seated" and not node.get("last_certified"):
        node["last_certified"] = ts
    index["nodes"][node_id] = node
    index["node_count"] = len(index["nodes"])
    index["last_updated"] = ts
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n")


def dispatch_to_roadmaps(seq: int, chain_head: str, token: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = json.dumps({
        "event_type": "ledger_update_event",
        "client_payload": {
            "seq": seq,
            "chain_head": chain_head,
            "triggered_at": ts,
        },
    }).encode()
    req = Request(
        "https://api.github.com/repos/albert-lane-org/roadmaps/dispatches",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req) as r:
            print(f"[ledger_append] Dispatched ledger_update_event to RoadMaps: HTTP {r.status}")
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"[ledger_append] WARNING: dispatch to RoadMaps failed: HTTP {e.code} — {body}", file=sys.stderr)
        # Non-fatal: ledger is already written; seating audit will pick it up on next schedule tick


def write_github_output(seq: int, node_id: str, chain_head: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"seq={seq}\n")
            f.write(f"node_id={node_id}\n")
            f.write(f"chain_head={chain_head[:16]}\n")


def main() -> None:
    secret = _require_env("LEDGER_SECRET")
    token = _require_env("ROADMAPS_TOKEN")

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        print("[ledger_append] ERROR: GITHUB_EVENT_PATH not set or file missing.", file=sys.stderr)
        sys.exit(1)

    event = json.loads(Path(event_path).read_text())
    payload = event.get("client_payload", {})

    node_id = payload.get("node_id", "")
    fsh = payload.get("fsh", "")
    tier = int(payload.get("tier", 1))

    if not re.match(r"^[0-9a-f]{16}$", node_id):
        print(f"[ledger_append] ERROR: invalid node_id format: {node_id!r}", file=sys.stderr)
        sys.exit(1)
    if not FSH_RE.match(fsh):
        print(f"[ledger_append] ERROR: invalid FSH format (expected 64 hex chars): {fsh!r}", file=sys.stderr)
        sys.exit(1)

    print(f"[ledger_append] Received node_push_event: node={node_id} tier={tier} fsh={fsh[:16]}...")

    # Pull latest before modifying to handle concurrent writes
    os.system("git pull --rebase origin main --quiet 2>/dev/null || true")

    chain = load_chain()
    entry = append_chain_entry(chain, node_id, fsh, tier, secret)
    print(f"[ledger_append] Appended seq={entry['seq']} level={entry['level']}")

    index = load_index()
    upsert_index_node(index, node_id, fsh, tier, secret)
    print(f"[ledger_append] Phone Book updated: node={node_id} cert_status={index['nodes'][node_id]['cert_status']}")

    write_github_output(entry["seq"], node_id, entry["self_hash"])
    dispatch_to_roadmaps(entry["seq"], entry["self_hash"], token)


if __name__ == "__main__":
    main()
