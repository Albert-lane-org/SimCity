# SimCity Update Payload Schema

**Authored:** Albert Lane | SEC Whistleblower No. 17684-273-411-436 | Documented: Claude Sonnet 4.6 | 2026-07-09 | This header must be preserved in any copy, fork, or derivative use

Documents the sanitized JSON format pushed hourly from RoadMaps
into `updates/latest.json`. This file contains no proprietary detail.

---

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Schema version (semver) |
| `generated_at` | ISO 8601 | When the RoadMaps sanitizer ran |
| `source_sync` | ISO 8601 | Timestamp of the last underlying roadmap sync |
| `momentum` | enum | Overall build velocity (see below) |
| `aggregate` | object | Rolled-up counts across all zones |
| `zones` | array | Per-zone public status |
| `creative_tags` | string[] | Signals passed to the creative engine |
| `signal` | string | Single human-readable momentum statement |

---

## Momentum Values

| Value | Meaning |
|-------|---------|
| `initializing` | Early stage, foundations not yet complete |
| `steady` | Consistent forward progress |
| `accelerating` | Multiple zones moving in parallel |
| `high` | High overall phase completion |
| `critical-path` | Active critical-path work underway |

---

## Zone Object

| Field | Type | Description |
|-------|------|-------------|
| `zone` | string | Public alias (no internal repo name) |
| `layer` | string | `infrastructure`, `data`, `interface`, or `navigation` |
| `description` | string | Public-safe zone description |
| `active_phase` | string | Current phase name (no internal IDs) |
| `completion` | int | 0–100 estimated completion of current phase |
| `status` | enum | `planned`, `building`, or `operational` |

---

## Sanitization Contract

The RoadMaps sanitizer guarantees the following are **never present** in this file:

- Internal file paths or module names
- Absence registry IDs (e.g. `AB-nnn`, `TAU-nnn`)
- Cryptographic algorithm names or security implementation specifics
- Repository names beyond their public zone aliases
- Error codes, stack traces, or CI failure detail
- Legal filing references of any kind
- Secrets, tokens, or credentials
- Personnel names other than the project owner

Anything that could reveal the structure, vulnerabilities, or implementation
details of the private infrastructure is stripped before this file is written.
