# Node Certification Ledger — Directory Service

<!-- Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-26 -->

## What This Is

The **Node Certification Ledger (NCL)** is a cryptographic chain-of-trust
directory that certifies autonomous nodes — devices, machines, and repositories —
by their operational presence, not by PII.

Think of it as a **phone book without identity**: coordinates and trust
signatures, no entity-specific attributes. A node is certified because it
*operates continuously and predictably*, not because of who owns it.

---

## How It Works

```
Tier 1 — Repo Node          Tier 2 — Central Ledger     Tier 3 — Enterprise Node
(your repo)                 (this repo — SimCity)        (albert-lane-org/roadmaps)
     │                              │                              │
     │  FSH every push ────────────►│  Appends to chain.jsonl     │
     │                              │  Updates Phone Book         │
     │                              │  Dispatches to Enterprise ─►│
     │                              │                              │  Evaluates seating
     │                              │◄──────── Issues cert ────────│  every 15 min
```

1. **Repo Nodes** generate a Forensic State Hash (FSH) on every push and dispatch it to the Central Ledger.
2. **The Central Ledger** (SimCity) appends each entry to `ledger/chain.jsonl`, maintains `ledger/index.json` (the Phone Book), and dispatches a summary to the Enterprise Node.
3. **The Enterprise Node** (RoadMaps) evaluates seating conditions over a 30–45 period window (7.5–11.25 hours) and issues a signed certificate when criteria are met.

---

## Public Data

All certified nodes are listed in the Phone Book:

```
https://raw.githubusercontent.com/albert-lane-org/simcity/main/ledger/index.json
```

Individual certificates:

```
https://raw.githubusercontent.com/albert-lane-org/simcity/main/ledger/certs/{node_id}.json
```

These are permanently public. No authentication required to read.

---

## Seating Criteria

A node achieves **SEATED** status when, over 30–45 consecutive 15-minute periods:

- **Safety score ≥ 80.0** — measured as `(1 - variance_rate) × 100`
- **Variance rate ≤ 0.05** — fewer than 5% of periods show a state transition
- **Minimum 30 periods** of continuous operation (~7.5 hours)

---

## Paid Tier — Get Your Node Listed

**Free tier:** Read-only access to the Phone Book and chain — no registration needed.

**Listed tier:** Your repo or device node is registered as a Tier 1 candidate
in the NCL Phone Book. After achieving SEATED status, you receive a signed
certificate automatically.

**To register a node:**

1. Sponsor the project via [Open Collective](https://opencollective.com) (search: Albert Lane Digital Estate)
2. Include your `repo_full_name` (e.g. `your-org/your-repo`) in the sponsorship note
3. Your node will be onboarded as a Tier 1 candidate within 48 hours
4. After achieving SEATED status (~7.5 hours of stable operation), your certificate is issued automatically to `ledger/certs/{node_id}.json`

---

## Certificate Schema

```json
{
  "schema":      "ncl-cert-v1",
  "node_id":     "a3f7b2c1d8e4f901",
  "tier":        1,
  "seated_at":   "2026-06-26T12:00:00Z",
  "issued_at":   "2026-06-26T12:15:00Z",
  "issuer":      "albert-lane-org/roadmaps",
  "signature":   "hmac-sha256-truncated-32-hex",
  "verify_url":  "https://raw.githubusercontent.com/albert-lane-org/simcity/main/ledger/index.json",
  "service_url": "https://raw.githubusercontent.com/albert-lane-org/simcity/main/ledger/certs/{node_id}.json"
}
```

**Verification:** Compute `HMAC-SHA256(LEDGER_SECRET, "{node_id}|{seated_at}|ncl-cert-v1")` and compare the first 64 hex chars to `signature`. Contact `lane.albert@pm.me` for the verification public endpoint.

---

## Privacy

- Node IDs are derived as `HMAC(LEDGER_SECRET, repo_full_name)[:16]` — non-reversible
- No names, emails, or organization identifiers are stored in the ledger
- The chain is append-only and public; entries cannot be deleted
- The FSH is a hash of repo file state — no file contents are transmitted

---

*All IP belongs to Albert Lane. See [LICENSE.md](../LICENSE.md).*
*Contact: `lane.albert@pm.me`*
