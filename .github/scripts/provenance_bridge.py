#!/usr/bin/env python3
# Authored: Albert Lane | SEC Whistleblower No. 17684-273-411-436 | Documented: Claude Sonnet 4.6 | 2026-07-09
"""
provenance_bridge.py — Asset Provenance Attribution

Bridges the SimCity creative repo to the sovereign-provenance system:
  1. Walks all generated SVG and PNG assets
  2. Computes BLAKE3-equivalent hashes (hashlib.blake2b as proxy)
  3. Injects provenance metadata into SVGs (safe public attribution only —
     no private keys, no full DID, no internal infrastructure)
  4. Writes ASSETS_FINGERPRINT.json compatible with sc-scan compare
  5. Updates ASSETS_FINGERPRINT.md (human-readable)

SVG PROVENANCE INJECTION:
  - Adds <metadata> block with Dublin Core creator/rights
  - Adds a provenance comment with short hash (8 chars, not full DID)
  - Does NOT expose: private keys, full DID, API endpoints, internal URLs

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, sys, json, re, hashlib
import datetime
from pathlib import Path

ROOT                = Path(".")
ASSETS_SVG_DIR      = ROOT / "assets" / "svg"
ASSETS_ILLUS_DIR    = ROOT / "assets" / "illustrations"
FINGERPRINT_JSON    = ROOT / "ASSETS_FINGERPRINT.json"
FINGERPRINT_MD      = ROOT / "ASSETS_FINGERPRINT.md"

# ── Safe public attribution (never expose private key material) ───────────────
CREATOR  = "Albert Lane | SovereignAudits™"
SITE     = "https://albertlane.net"
SEC_REF  = "17684-273-411-436"
LICENSE  = "SOVEREIGN IP LICENSE v1"
SCHEMA   = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Hashing
# ─────────────────────────────────────────────────────────────────────────────

def blake3_equivalent(data: bytes) -> str:
    """
    BLAKE3-equivalent using BLAKE2b with 32-byte digest.
    Use this until the blake3 Python package is available in the workflow.
    Output format is compatible with sc-scan's ContentFingerprint.
    """
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def short_hash(full_hex: str) -> str:
    return full_hex[:8]


# ─────────────────────────────────────────────────────────────────────────────
# SVG provenance injection
# ─────────────────────────────────────────────────────────────────────────────

def inject_svg_provenance(
    svg: str,
    asset_name: str,
    content_hash: str,
    zone_key: str,
    iteration: int,
) -> str:
    """
    Inject safe attribution metadata into an SVG file.

    PUBLIC (safe to embed): creator name, short hash (8 chars), SEC ref,
        zone, iteration number.
    NEVER EMBED: private keys, full DID, API keys, internal URLs.
    """
    tag = short_hash(content_hash)

    # Dublin Core metadata block
    metadata_block = (
        f'<metadata>'
        f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        f' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        f' xmlns:sc="https://albertlane.net/sovereign/ns/">'
        f'<rdf:Description rdf:about="{asset_name}">'
        f'<dc:creator>{CREATOR}</dc:creator>'
        f'<dc:rights>{LICENSE}</dc:rights>'
        f'<dc:source>{SITE}</dc:source>'
        f'<sc:hash>{tag}</sc:hash>'
        f'<sc:sec_ref>{SEC_REF}</sc:sec_ref>'
        f'<sc:zone>{zone_key}</sc:zone>'
        f'<sc:iteration>{iteration}</sc:iteration>'
        f'</rdf:Description></rdf:RDF></metadata>'
    )

    # Provenance comment (recoverable via grep/strings)
    prov_comment = (
        f'\n<!-- SOVEREIGN: creator="{CREATOR}" hash="{tag}" '
        f'sec="{SEC_REF}" zone="{zone_key}" iteration="{iteration}" -->'
    )

    # Inject metadata after the <svg ...> opening tag (if not already present)
    if '<metadata>' not in svg:
        # Find the first > after <svg to insert metadata
        match = re.search(r'<svg[^>]*>', svg)
        if match:
            insert_at = match.end()
            svg = svg[:insert_at] + metadata_block + svg[insert_at:]

    # Append provenance comment before </svg>
    if f'hash="{tag}"' not in svg:
        svg = svg.rstrip()
        if svg.endswith('</svg>'):
            svg = svg[:-6] + prov_comment + '\n</svg>'
        else:
            svg += prov_comment

    return svg


# ─────────────────────────────────────────────────────────────────────────────
# Asset walker
# ─────────────────────────────────────────────────────────────────────────────

def walk_assets() -> list[dict]:
    """Walk all SVG and PNG asset directories and collect file records."""
    records = []

    for asset_dir in [ASSETS_SVG_DIR, ASSETS_ILLUS_DIR]:
        if not asset_dir.exists():
            continue
        for f in sorted(asset_dir.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".svg", ".png"):
                data = f.read_bytes()
                h    = blake3_equivalent(data)
                rel  = str(f.relative_to(ROOT)).replace("\\", "/")
                records.append({
                    "path":         rel,
                    "hash":         h,
                    "short_tag":    short_hash(h),
                    "size_bytes":   len(data),
                    "suffix":       f.suffix.lower(),
                    "zone_key":     _infer_zone(f.name),
                    "modified_at":  datetime.datetime.utcfromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })

    return records


def _infer_zone(filename: str) -> str:
    """Infer zone_key from filename."""
    for zone in ("city_hall", "gateway_district", "intelligence_core", "sovereign_quarters"):
        if zone in filename.lower():
            return zone
    return "unknown"


def _infer_iteration(filename: str) -> int:
    """Extract iteration number from filenames like zone_key_i0042.svg"""
    m = re.search(r"_i(\d+)\.", filename)
    return int(m.group(1)) if m else 0


# ─────────────────────────────────────────────────────────────────────────────
# Inject provenance into all SVGs in-place
# ─────────────────────────────────────────────────────────────────────────────

def inject_all_svgs():
    """Re-read each SVG, inject provenance metadata, write back."""
    if not ASSETS_SVG_DIR.exists():
        return

    for f in ASSETS_SVG_DIR.rglob("*.svg"):
        try:
            original = f.read_text(encoding="utf-8", errors="replace")
            zone_key  = _infer_zone(f.name)
            iteration = _infer_iteration(f.name)
            content_hash = blake3_equivalent(original.encode())

            if 'SOVEREIGN:' not in original:
                # Only inject if not already present
                enhanced = inject_svg_provenance(
                    original, f.name, content_hash, zone_key, iteration
                )
                f.write_text(enhanced, encoding="utf-8")
                print(f"[provenance_bridge] Injected provenance → {f.name}", file=sys.stderr)
        except Exception as e:
            print(f"[provenance_bridge] WARNING: could not process {f}: {e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Write ASSETS_FINGERPRINT.json
# ─────────────────────────────────────────────────────────────────────────────

def write_fingerprint_json(records: list[dict]):
    """
    Write ASSETS_FINGERPRINT.json in a format compatible with
    sovereign-provenance's ContentFingerprint schema.
    sc-scan compare can read this to verify asset integrity cross-repo.
    """
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Compute corpus-level fingerprint (sorted by path for determinism)
    corpus_hasher = hashlib.blake2b(digest_size=32)
    corpus_hasher.update(b"SOVEREIGN_ASSETS_V1")
    corpus_hasher.update(CREATOR.encode())
    corpus_hasher.update(SEC_REF.encode())
    for r in sorted(records, key=lambda x: x["path"]):
        corpus_hasher.update(r["path"].encode())
        corpus_hasher.update(bytes.fromhex(r["hash"]))
    corpus_digest = corpus_hasher.hexdigest()

    fingerprint = {
        "schema_version": SCHEMA,
        "digest":         corpus_digest,
        "entry_count":    len(records),
        "owner_did":      "DID_REDACTED_SEE_CITATION_CFF",  # safe — no key in public JSON
        "creator":        CREATOR,
        "sec_ref":        SEC_REF,
        "license":        LICENSE,
        "computed_at":    now,
        "label":          "simcity-assets-corpus",
        "assets":         records,
    }

    FINGERPRINT_JSON.write_text(json.dumps(fingerprint, indent=2))
    print(f"[provenance_bridge] ASSETS_FINGERPRINT.json: {len(records)} assets, digest={corpus_digest[:16]}...", file=sys.stderr)
    return corpus_digest


# ─────────────────────────────────────────────────────────────────────────────
# Write ASSETS_FINGERPRINT.md (human-readable)
# ─────────────────────────────────────────────────────────────────────────────

def write_fingerprint_md(records: list[dict], corpus_digest: str):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Asset Fingerprint Registry",
        "",
        "Immutable hash record of all generated assets.",
        f"Corpus digest: `{corpus_digest[:24]}...`",
        "",
        f"Author: {CREATOR}  ",
        f"SEC Ref: {SEC_REF}  ",
        f"Updated: {now}",
        "",
        "---",
        "",
        "| Asset | Zone | Short Hash | Size | Modified |",
        "|:------|:-----|:-----------|:-----|:---------|",
    ]

    for r in records:
        lines.append(
            f"| `{r['path']}` | {r['zone_key']} | `{r['short_tag']}` "
            f"| {r['size_bytes']:,}b | {r['modified_at'][:10]} |"
        )

    lines += ["", "---", f"*{CREATOR} | SOVEREIGN IP LICENSE v1*"]
    FINGERPRINT_MD.write_text("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run():
    print("[provenance_bridge] Starting...", file=sys.stderr)

    inject_all_svgs()

    records = walk_assets()
    print(f"[provenance_bridge] Found {len(records)} assets.", file=sys.stderr)

    if not records:
        print("[provenance_bridge] No assets found — nothing to fingerprint.", file=sys.stderr)
        return

    corpus_digest = write_fingerprint_json(records)
    write_fingerprint_md(records, corpus_digest)

    out = os.environ.get("GITHUB_OUTPUT", "")
    if out:
        with open(out, "a") as f:
            f.write(f"asset_count={len(records)}\n")
            f.write(f"corpus_digest={corpus_digest[:16]}\n")

    print(f"[provenance_bridge] Done. {len(records)} assets fingerprinted.", file=sys.stderr)


if __name__ == "__main__":
    run()
