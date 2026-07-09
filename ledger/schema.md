# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-26 | SEC Whistleblower No. 17684-273-411-436

# Node Certification Ledger — Schema Reference

SimCity acts as the **Tier 2 Central Node** of the Three-Tier Node Certification
Ledger (NCL). It receives Forensic State Hashes from Tier 1 Repo Nodes, maintains
a cryptographic chain of those events, and publishes a non-PII "Phone Book" of
certified node coordinates.

---

## Architecture Overview

```
Tier 1 — Repo Nodes (e.g., roadmaps, lane-mcp, sqlxml...)
    │  push: node_push_event → dispatch
    ▼
Tier 2 — Central Node (simcity)
    │  ledger/chain.jsonl  — append-only chain
    │  ledger/index.json   — Phone Book (public cert directory)
    │  dispatch: ledger_update_event
    ▼
Tier 3 — Enterprise Node (roadmaps)
    │  ledger/seating-state.json — seating evaluation result
    │  evaluates: T-30 to T-45 window, weakest-node score, oscillation gate
    └→ SEATED when all conditions pass
```

All node identifiers are HMAC-derived and non-reversible. No repo names, user
names, or PII appear in any public ledger file.

---

## `ledger/chain.jsonl` — Cryptographic Append-Only Chain

One JSON object per line. **Never edited — only appended.**

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `prev_hash` | string (64 hex) | SHA-256 of the previous entry's raw JSON string. Genesis uses `sha256("")`. |
| `seq` | integer | Strictly monotonic 1-indexed sequence number. Gap = tampering indicator. |
| `node_id` | string (16 hex) | HMAC-SHA256(LEDGER_SECRET, repo_full_name)[:16]. Non-reversible. |
| `tier` | integer | Always `1` for Repo Nodes. `0` for genesis. |
| `fsh` | string (64 hex) | Forensic State Hash — SHA-256 of sorted file manifest. |
| `timestamp` | string (ISO-8601) | UTC receipt time, set by SimCity. Not trusting sender clock. |
| `hmac_tag` | string (16 hex) | HMAC-SHA256(LEDGER_SECRET, fsh)[:16]. Proves FSH integrity in transit. |
| `level` | string | `nominal` \| `warning` \| `alert` \| `genesis`. Set by SimCity at append time. |
| `self_hash` | string (64 hex) | SHA-256 of all fields except `self_hash`, in sorted-key JSON. Tamper-evident. |

### Level Assignment Logic

- `genesis` — seq 0 only
- `nominal` — FSH matches node's previous entry (no state change)
- `warning` — FSH differs from previous entry (state changed)
- `alert` — FSH has changed 3+ times in the last 10 entries for this node

### Self-Hash Computation

```python
import json, hashlib

def compute_self_hash(entry: dict) -> str:
    d = {k: v for k, v in entry.items() if k != "self_hash"}
    canonical = json.dumps(d, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

The canonical form is deterministic: sorted keys, no whitespace. Any field change
invalidates the self_hash, allowing chain integrity verification without a
trusted third party.

### Chain Integrity Verification

To verify the full chain:
```python
import json, hashlib

with open("ledger/chain.jsonl") as f:
    entries = [json.loads(line) for line in f if line.strip()]

for i, entry in enumerate(entries):
    # Verify self_hash
    d = {k: v for k, v in entry.items() if k != "self_hash"}
    canonical = json.dumps(d, sort_keys=True, separators=(',', ':'))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert entry["self_hash"] == expected, f"self_hash mismatch at seq {entry['seq']}"

    # Verify chain linkage (skip genesis)
    if i > 0:
        prev_json = json.dumps(
            {k: v for k, v in entries[i-1].items()},
            sort_keys=False, separators=(',', ':')
        )
        # Note: prev_hash is sha256 of the previous entry's raw line text
        assert entry["prev_hash"] == entries[i-1]["self_hash"], \
            f"Chain broken at seq {entry['seq']}"

print("Chain integrity: OK")
```

---

## `ledger/index.json` — Phone Book (Public Certificate of Trust)

### Structure

```json
{
  "schema_version": "1.0.0",
  "label": "ncl-phone-book",
  "genesis_hash": "e0eab61a4b2298a6",
  "last_updated": "2026-06-26T14:30:00Z",
  "node_count": 1,
  "nodes": {
    "<node_id>": {
      "grid_coord": "B2",
      "tier": 1,
      "cert_status": "pending",
      "last_fsh_tag": "a3f7c9d1",
      "last_certified": null,
      "hmac_tag": "a3f7c9d1e4b20856",
      "push_count": 3,
      "last_seen": "2026-06-26T14:30:00Z"
    }
  }
}
```

### `cert_status` State Machine

```
pending ──(3 consecutive same-FSH pushes)──► stable
stable  ──(seating conditions met)──────────► seated
stable  ──(oscillation detected)────────────► oscillating
oscillating ──(variance clears for 5 periods)► stable
seated  ──(seating re-confirmed each eval)──► seated (preserved)
```

### Grid Coordinate Assignment

Node coordinates are derived from the first two hex nibbles of `node_id`:

```python
COL = {0:'A', 1:'A', 2:'A', 3:'A', 4:'B', 5:'B',
       6:'B', 7:'B', 8:'C', 9:'C', 10:'C', 11:'C',
       12:'D', 13:'D', 14:'D', 15:'D'}
ROW = {0:'1', 1:'1', 2:'1', 3:'1', 4:'2', 5:'2',
       6:'2', 7:'2', 8:'3', 9:'3', 10:'3', 11:'3',
       12:'4', 13:'4', 14:'4', 15:'4'}

def assign_grid(node_id: str) -> str:
    return COL[int(node_id[0], 16)] + ROW[int(node_id[1], 16)]
```

Grid cells A1–D4 are public coordinates, not unique keys. Multiple nodes may
share a cell. The coordinate describes topology proximity, not identity.

---

## Safety Score & Seating Algorithm (Tier 3 — Enterprise Node)

The Enterprise Node (RoadMaps) evaluates seating. The formula below is documented
here for transparency:

```
transitions    = count of consecutive FSH changes in evaluation window
periods        = total chain entries in window for this node
variance_rate  = transitions / periods   (1.0 if periods == 0)
score          = (1 - variance_rate) * 100
```

**All three conditions must pass for SEATED:**

1. `weakest_score >= 80.0` — upper limit (80 = no more than 1-in-5 periods may change)
2. `variance_rate_of_weakest <= 0.05` — oscillation gate (stricter than score alone)
3. `periods_evaluated >= 30` — T-30 minimum (30 × 15 min = 7.5 hours of data)

The **weakest node** determines collective success. No node is discarded or
weighted away from the collective average.

---

## HMAC Signing Scheme

All HMAC operations use: `hmac.new(key=LEDGER_SECRET.encode(), msg=data.encode(), digestmod=sha256)`

| Tag | Data signed | Where stored |
|-----|-------------|--------------|
| `chain.hmac_tag` | `fsh` | chain.jsonl entry |
| `index.nodes[n].hmac_tag` | `node_id + last_fsh_tag + last_seen` | index.json |

The `LEDGER_SECRET` is a GitHub Actions secret present in both RoadMaps and
SimCity. It is never stored in any file or logged to workflow output.

---

## Node ID Security Properties

- **Non-reversible**: HMAC-SHA256 with secret key; repo name cannot be recovered
- **Deterministic**: Same repo + same secret → same node_id across sessions
- **Stable**: node_id does not rotate unless LEDGER_SECRET is rotated
- **Non-correlating**: Two different secrets produce two different node_ids for the same repo

The private `ledger/node-registry.json` in RoadMaps maps node_ids back to repo
names for internal audit. That mapping is never dispatched to SimCity.
