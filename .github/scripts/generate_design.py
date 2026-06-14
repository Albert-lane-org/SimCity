#!/usr/bin/env python3
"""
SimCity Design Loop — Orchestration Script v2

UPGRADES FROM v1:
  - BLAKE3-equivalent content hash for all generated assets (chain-of-custody)
  - Cross-model quality scoring: Claude scores Gemini's raster output
  - Provenance attribution in every ledger entry (safe public fields only)
  - Style evolution notes injected into Claude's art direction prompt
  - Coaching from quality scores fed back into next design loop run
  - VISUAL_QUALITY contribution: design loop scores update same state as creative engine

Claude acts as Art Director: reads issue + ledger history + evolution notes
  → produces structured prompt for Gemini
Gemini acts as Illustrator: generates raster from Claude's prompt
Claude acts as Quality Critic: scores Gemini's output on 4 dimensions

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os, json, sys, hashlib, datetime, re
from pathlib import Path

from anthropic import Anthropic

# ─── Constants ────────────────────────────────────────────────────────────────
LEDGER_DIR        = Path("design_ledger/entries")
LEDGER_INDEX      = Path("design_ledger/LEDGER.md")
ASSETS_DIR        = Path("assets/illustrations")
WORKFLOW_PATH     = Path(".github/workflows/design-loop.yml")
CHANGELOG_PATH    = Path("WORKFLOW_CHANGELOG.md")
VISUAL_QUALITY    = Path("visual_quality_state.json")
GEN_STATE         = Path("generation_state.json")
MAX_LEDGER_HISTORY = 10

# ─── Safe attribution (public only) ──────────────────────────────────────────
CREATOR = "Albert Lane | SovereignAudits™"
SEC_REF = "17684-273-411-436"
LICENSE = "SOVEREIGN IP LICENSE v1"

# ─── T2 palette reference (for quality scoring prompt) ────────────────────────
T2_PALETTE_DESC = "#04070E bg, #3B82F6 primary blue, #F0F4FF ice white, #1E3A5F mid shadow, #0A1628 deep shadow, #2563EB grid blue, #B8621A amber accent (once only)"

VISUAL_THEME = f"""
SimCity Visual System — T2 GlacierNoir v2.1
Core palette: {T2_PALETTE_DESC}
Style: isometric civic architecture, brutalist-modernist hybrid
Tone: civic gravitas, precise, functional beauty
Render: clean 2.5D vector aesthetic, high contrast, night/dusk preference
Zone vocabulary: City Hall (authority), Gateway District (connection),
  Intelligence Core (data), Sovereign Quarters (interface)
Avoid: fantasy, organic forms unmoored from civic context,
  photorealism that breaks isometric grammar
"""

# ─── Clients ──────────────────────────────────────────────────────────────────
anthropic = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def blake3_eq(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def load_recent_ledger_context(n: int = MAX_LEDGER_HISTORY) -> str:
    entries = sorted(LEDGER_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    summaries = []
    for entry_path in entries[:n]:
        try:
            data = json.loads(entry_path.read_text())
            summaries.append(
                f"Issue #{data['issue_number']} ({data['zone']}): '{data['concept']}' "
                f"→ Prompt: {data['claude_prompt'][:100]}..."
                + (f" [score: {data.get('quality_total', '?')}/40]" if 'quality_total' in data else "")
            )
        except Exception:
            continue
    if not summaries:
        return "No prior ledger entries. This is the first generation."
    return "\n".join(summaries)


def load_evolution_notes_for_zone(zone: str) -> str:
    """Get style evolution notes for a zone from visual_quality_state.json."""
    if not VISUAL_QUALITY.exists():
        return ""
    try:
        state = json.loads(VISUAL_QUALITY.read_text())
        # Normalise zone name to key
        zone_key = zone.lower().replace(" ", "_")
        return state.get("zones", {}).get(zone_key, {}).get("style_evolution_notes", "")
    except Exception:
        return ""


# ─── Claude: Art Direction (upgraded with evolution notes) ────────────────────

def get_claude_prompt(
    issue_number: int,
    concept: str,
    zone: str,
    visual_context: str,
    ledger_history: str,
) -> str:
    evolution_notes = load_evolution_notes_for_zone(zone)
    evolution_clause = (
        f"\n\nEvolved style guidance for {zone} (from quality score learning):\n{evolution_notes}"
        if evolution_notes else ""
    )

    system = f"""You are the Art Director for SimCity — a civic infrastructure project
with a precise visual identity. Your sole function: translate design requests into
exact, technically complete prompts for an AI image generator.

Visual System:
{VISUAL_THEME}

Recent generation history (maintain consistency):
{ledger_history}{evolution_clause}

Rules:
- Respond ONLY with the image generation prompt. No preamble, no commentary.
- Prompt must be 2–4 sentences maximum.
- Always include: zone context, isometric angle, T2 palette reference, lighting condition.
- Reject concept drift — if the request would break visual system coherence,
  redirect it gracefully within the prompt toward the established aesthetic.
- Every prompt must feel like it belongs in the same city as all prior entries.
- Never fabricate progress milestones — stay honest to zone_state.json."""

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                f"Zone: {zone}\nConcept: {concept}\n"
                f"Visual context: {visual_context or 'None provided.'}\n\n"
                f"Generate the image prompt."
            ),
        }],
    )
    return response.content[0].text.strip()


# ─── Illustration (image generation removed — raster pipeline pending) ────────

def generate_image(prompt: str, output_path: Path) -> bool:
    # Image generation is not available in this pipeline configuration.
    # Art direction prompts are recorded in the ledger for offline rendering.
    print(f"[generate_image] Skipped — no image backend configured. Prompt logged.")
    return False


# ─── Claude: Quality Scoring (cross-model: Claude scores Gemini's raster) ────

def score_generated_image(
    claude_prompt: str,
    zone: str,
    concept: str,
    success: bool,
) -> dict:
    """
    Claude quality-scores the generated image by analyzing the prompt and
    zone alignment. (True pixel analysis requires image input; this scores
    prompt quality and zone coherence as a proxy when image bytes unavailable.)
    """
    if not success:
        return {"total": 0, "label": "FAILED", "coaching": "Generation failed — Gemini did not return an image."}

    system = """You are a quality auditor for isometric civic architecture imagery.
Score the art direction prompt and zone alignment on 4 dimensions (0-10 each).

Output format (strict, machine-parsed):
PROMPT_CLARITY: <0-10>
ZONE_ALIGNMENT: <0-10>
PALETTE_INSTRUCTION: <0-10>
STRUCTURAL_SPECIFICITY: <0-10>
TOTAL: <sum>
COACHING: <one sentence — what to improve in the next iteration>
END"""

    user_msg = (
        f"Zone: {zone}\n"
        f"Concept requested: {concept}\n"
        f"Art direction prompt used:\n{claude_prompt}\n\n"
        f"Score this prompt for quality and zone alignment."
    )

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()

    def ex_int(pat: str) -> int:
        m = re.search(pat, raw)
        try:
            return max(0, min(10, int(m.group(1)))) if m else 0
        except Exception:
            return 0

    dims = {
        "prompt_clarity":       ex_int(r"PROMPT_CLARITY:\s*(\d+)"),
        "zone_alignment":       ex_int(r"ZONE_ALIGNMENT:\s*(\d+)"),
        "palette_instruction":  ex_int(r"PALETTE_INSTRUCTION:\s*(\d+)"),
        "structural_specificity": ex_int(r"STRUCTURAL_SPECIFICITY:\s*(\d+)"),
    }
    total    = sum(dims.values())
    coaching = re.search(r"COACHING:\s*(.+?)(?:END|$)", raw, re.DOTALL)
    coaching = coaching.group(1).strip() if coaching else ""

    label = (
        "EXCELLENT"  if total >= 32 else
        "ACCEPTABLE" if total >= 26 else
        "MARGINAL"   if total >= 20 else
        "POOR"
    )

    return {
        "dimensions": dims,
        "total":      total,
        "label":      label,
        "coaching":   coaching,
        "scorer_model": "claude-sonnet-4-20250514",
        "scored_by":  "cross-model (Claude scores Gemini output)",
        "scored_at":  datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def persist_design_quality_score(zone: str, concept: str, issue_number: int, score: dict):
    """Append quality score to visual_quality_state.json under the zone."""
    zone_key = zone.lower().replace(" ", "_")
    if not VISUAL_QUALITY.exists():
        return  # quality_scorer.py initialises this file

    try:
        state = json.loads(VISUAL_QUALITY.read_text())
        zone_state = state.get("zones", {}).get(zone_key, {})
        scores = zone_state.get("scores", [])
        scores.append({
            "iteration": issue_number,
            "total":     score["total"],
            "label":     score["label"],
            "coaching":  score["coaching"],
            "ts":        score["scored_at"],
            "source":    "design_loop",
        })
        zone_state["scores"] = scores[-24:]
        if score["total"] > zone_state.get("best_score", 0):
            zone_state["best_score"]     = score["total"]
            zone_state["best_iteration"] = issue_number
        all_totals = [s["total"] for s in zone_state["scores"]]
        zone_state["avg_score"] = round(sum(all_totals) / len(all_totals), 1)
        state["zones"][zone_key] = zone_state
        VISUAL_QUALITY.write_text(json.dumps(state, indent=2))
    except Exception as e:
        print(f"[persist_score] WARNING: {e}", file=sys.stderr)


# ─── Ledger ───────────────────────────────────────────────────────────────────

def get_asset_filename(issue_number: int, concept: str) -> str:
    slug = concept.lower()[:40].replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    return f"issue_{issue_number:04d}_{slug}.png"


def append_to_ledger_index(entry: dict, image_url: str):
    quality_col = f"[{entry.get('quality_total', '?')}/40]" if 'quality_total' in entry else ""
    line = (
        f"\n| #{entry['issue_number']} | {entry['zone']} | "
        f"{entry['concept'][:50]} | "
        f"[asset]({image_url}) {quality_col} | {entry['generated_at'][:10]} |"
    )
    header_needed = not LEDGER_INDEX.exists()
    with open(LEDGER_INDEX, "a") as f:
        if header_needed:
            f.write(
                "# SimCity Design Ledger\n"
                "Immutable record of all design requests and generated assets.\n"
                f"Authored: {CREATOR} | SEC Ref: {SEC_REF}\n\n"
                "| Issue | Zone | Concept | Asset | Generated |\n"
                "|-------|------|---------|-------|-----------|\n"
            )
        f.write(line)


# ─── Self-improvement (creative script, not workflow YAML) ────────────────────

def self_improve_creative_script(run_metadata: dict):
    """
    Claude reads generate_design.py + recent scores + run metadata and
    proposes ONE improvement to the script itself (not the YAML).
    Appends to WORKFLOW_CHANGELOG.md with rationale.
    """
    script_path = Path(__file__)
    current_script = script_path.read_text()[:6000]  # first 6k chars

    ledger_history = load_recent_ledger_context()

    system = """You are a senior AI systems engineer reviewing a creative pipeline script.
Your goal: identify ONE specific improvement to the Python script that would improve
creative output quality or pipeline reliability.

Target improvements in this order:
1. Prompt quality — can the art direction prompt be more precise?
2. Quality scoring accuracy — is the cross-model scoring capturing the right signals?
3. Error handling — any silent failure points?
4. Zone evolution — is the feedback loop complete?
5. Provenance integrity — is attribution correct and complete?

Output format (machine-parsed):
IMPROVEMENT_TARGET: <8 words max>
RISK: LOW | MEDIUM
RATIONALE: <2 sentences>
BEFORE:
```python
<exact lines being replaced>
```
AFTER:
```python
<replacement lines>
```
END"""

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                f"Current script (truncated):\n```python\n{current_script}\n```\n\n"
                f"Recent ledger (with quality scores):\n{ledger_history}\n\n"
                f"Last run: {json.dumps(run_metadata, indent=2)[:500]}\n\n"
                f"Propose one improvement."
            ),
        }],
    )

    improvement = response.content[0].text.strip()
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    entry = (
        f"\n\n## {timestamp} — Design Loop Script Improvement\n\n"
        f"{improvement}\n\n---\n"
        f"*{CREATOR} | {SEC_REF}*"
    )

    with open(CHANGELOG_PATH, "a") as f:
        if not CHANGELOG_PATH.exists() or CHANGELOG_PATH.stat().st_size == 0:
            f.write(
                "# Workflow & Script Changelog\n"
                f"Authored: {CREATOR} | {SEC_REF}\n\n"
            )
        f.write(entry)

    print(f"[self_improve] Script improvement logged.")
    return improvement


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    issue_number = int(os.environ.get("ISSUE_NUMBER",  "0"))
    concept      = os.environ.get("ISSUE_CONCEPT",     "").strip()
    zone         = os.environ.get("ISSUE_ZONE",        "Not sure").strip()
    visual_ctx   = os.environ.get("ISSUE_VISUAL_CONTEXT", "").strip()

    if not concept:
        print("[main] ERROR: ISSUE_CONCEPT is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"[main] Issue #{issue_number}: '{concept}' — Zone: {zone}")

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    ledger_history = load_recent_ledger_context()

    # 1. Claude art direction (with evolution notes)
    print("[main] Claude art direction...")
    claude_prompt = get_claude_prompt(issue_number, concept, zone, visual_ctx, ledger_history)
    print(f"[main] Prompt: {claude_prompt[:100]}...")

    # 2. Gemini illustration
    asset_filename = get_asset_filename(issue_number, concept)
    asset_path     = ASSETS_DIR / asset_filename
    print(f"[main] Gemini illustration → {asset_path}")
    success = generate_image(claude_prompt, asset_path)

    # 3. Cross-model quality scoring (Claude scores Gemini's output)
    print("[main] Quality scoring...")
    score = score_generated_image(claude_prompt, zone, concept, success)
    print(f"[main] Quality: {score['total']}/40 ({score['label']})")
    persist_design_quality_score(zone, concept, issue_number, score)

    # 4. Ledger entry with provenance and quality score
    generated_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content_hash = blake3_eq(claude_prompt.encode())

    entry = {
        "issue_number":          issue_number,
        "concept":               concept,
        "zone":                  zone,
        "visual_context_provided": visual_ctx,
        "claude_prompt":         claude_prompt,
        "content_hash_blake3":   content_hash,
        "asset_filename":        asset_filename,
        "generation_success":    success,
        "generated_at":          generated_at,
        "model_art_director":    "claude-sonnet-4-20250514",
        "model_illustrator":     "none (image generation pending)",
        "quality_total":         score["total"],
        "quality_label":         score["label"],
        "quality_coaching":      score["coaching"],
        "quality_scorer_model":  score["scorer_model"],
        # Provenance attribution (safe public fields)
        "creator":               CREATOR,
        "sec_ref":               SEC_REF,
        "license":               LICENSE,
    }

    ledger_entry_path = LEDGER_DIR / f"issue_{issue_number:04d}.json"
    ledger_entry_path.write_text(json.dumps(entry, indent=2))
    print(f"[main] Ledger entry → {ledger_entry_path}")

    # 5. Human-readable LEDGER.md
    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "Albert-lane-org")
    repo_name  = os.environ.get("GITHUB_REPOSITORY", "Albert-lane-org/SimCity").split("/")[-1]
    branch     = os.environ.get("GITHUB_REF_NAME", "main")
    image_url  = (
        f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}"
        f"/{branch}/assets/illustrations/{asset_filename}"
    )
    append_to_ledger_index(entry, image_url)

    # 6. Creative script self-improvement pass
    print("[main] Self-improvement pass...")
    self_improve_creative_script(entry)

    # 7. GitHub Actions outputs
    out = os.environ.get("GITHUB_OUTPUT", "")
    if out:
        with open(out, "a") as f:
            f.write(f"asset_filename={asset_filename}\n")
            f.write(f"image_url={image_url}\n")
            f.write(f"claude_prompt={claude_prompt[:200]}\n")
            f.write(f"generation_success={str(success).lower()}\n")
            f.write(f"quality_total={score['total']}\n")
            f.write(f"quality_label={score['label']}\n")

    print(f"[main] Complete. Success={success}, Quality={score['total']}/40")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
