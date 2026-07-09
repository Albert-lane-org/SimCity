# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-06-11 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
# Extracted from self-improve-creative.yml to fix YAML block scalar indentation.
# Called by: .github/workflows/self-improve-creative.yml
import os
import re
import sys
import json
import datetime
from pathlib import Path
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
target = os.environ.get("TARGET_SCRIPT", "auto")

SCRIPTS = {
    "creative_engine":  Path(".github/scripts/creative_engine.py"),
    "quality_scorer":   Path(".github/scripts/quality_scorer.py"),
    "style_evolution":  Path(".github/scripts/style_evolution.py"),
}

QUALITY_STATE = Path("visual_quality_state.json")
CHANGELOG     = Path("CREATIVE_CHANGELOG.md")


def load_quality_summary() -> str:
    if not QUALITY_STATE.exists():
        return "No quality data yet."
    state = json.loads(QUALITY_STATE.read_text())
    lines = []
    for zk, zd in state.get("zones", {}).items():
        lines.append(
            f"{zk}: avg={zd.get('avg_score', 0)}/40, "
            f"best={zd.get('best_score', 0)}/40, "
            f"streak={zd.get('below_threshold_streak', 0)}"
        )
    return "\n".join(lines) or "No zone data."


def load_changelog_tail(path: Path, max_chars=5000) -> str:
    if not path.exists():
        return "No changelog yet."
    text = path.read_text()
    return text[-max_chars:] if len(text) > max_chars else text


# Auto-select: pick the script with most quality pressure
if target == "auto":
    if not QUALITY_STATE.exists():
        target = "creative_engine"
    else:
        state = json.loads(QUALITY_STATE.read_text())
        worst_streak = max(
            (zd.get("below_threshold_streak", 0) for zd in state.get("zones", {}).values()),
            default=0,
        )
        if worst_streak >= 2:
            target = "quality_scorer"
        else:
            prev = state.get("last_script_improved", "style_evolution")
            target = "style_evolution" if prev == "creative_engine" else "creative_engine"

script_path = SCRIPTS.get(target, SCRIPTS["creative_engine"])
if not script_path.exists():
    print(f"[self-improve-creative] Script not found: {script_path}", file=sys.stderr)
    sys.exit(0)

script_content = script_path.read_text()
quality_summary = load_quality_summary()
changelog_tail  = load_changelog_tail(CHANGELOG)

system = (
    "You are a senior AI systems engineer specialising in creative generative pipelines.\n"
    "You are reviewing a Python script that generates isometric SVG art for a civic infrastructure project.\n\n"
    "Your task: propose ONE surgical improvement to the script that will improve creative output quality.\n\n"
    f"Quality context (current state):\n{quality_summary}\n\n"
    "Improvement priorities:\n"
    "1. Prompt engineering — make Claude prompts more precise and constraint-following\n"
    "2. Quality signal fidelity — ensure scoring captures actual visual quality\n"
    "3. Learning loop completeness — does evolution state flow correctly back into generation?\n"
    "4. Provenance integrity — is attribution embedded correctly without exposing private data?\n"
    "5. Error resilience — any step that could silently produce bad output?\n\n"
    "CRITICAL RULES:\n"
    "- ONE change only. Do not refactor the entire script.\n"
    "- BEFORE/AFTER blocks must be exact Python code snippets.\n"
    "- Risk must be LOW or MEDIUM.\n"
    "- Preserve all attribution headers and SEC ref references.\n\n"
    "Output format (machine-parsed):\n"
    "IMPROVEMENT_TARGET: <8 words>\n"
    "RISK: LOW | MEDIUM\n"
    "RATIONALE: <2 sentences>\n"
    "BEFORE:\n```python\n<exact lines to replace>\n```\n"
    "AFTER:\n```python\n<replacement lines>\n```\n"
    "END"
)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1200,
    system=system,
    messages=[{
        "role": "user",
        "content": (
            f"Script: {script_path.name}\n"
            f"Recent changelog:\n{changelog_tail}\n\n"
            f"Script content:\n```python\n{script_content[:5000]}\n```\n\n"
            "Propose one improvement."
        ),
    }],
)

output = response.content[0].text.strip()
print(f"[self-improve-creative] Response:\n{output[:500]}...\n")

# Parse
target_match = re.search(r"IMPROVEMENT_TARGET:\s*(.+)", output)
risk_match   = re.search(r"RISK:\s*(LOW|MEDIUM|HIGH)", output)
before_match = re.search(r"BEFORE:\s*```python\n(.*?)```", output, re.DOTALL)
after_match  = re.search(r"AFTER:\s*```python\n(.*?)```", output, re.DOTALL)

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
        print(f"[self-improve-creative] Patch applied to {script_path.name}: {imp_target}")
    else:
        print(f"[self-improve-creative] BEFORE block not found verbatim — logging only.", file=sys.stderr)
elif risk == "HIGH":
    print(f"[self-improve-creative] HIGH risk — deferred for human review.")

# Update last_script_improved in quality state
if QUALITY_STATE.exists():
    try:
        state = json.loads(QUALITY_STATE.read_text())
        state["last_script_improved"] = target
        QUALITY_STATE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass

# Append to CREATIVE_CHANGELOG.md
timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
status = "APPLIED" if patched else ("DEFERRED (high risk)" if risk == "HIGH" else "LOGGED")
entry = (
    f"\n\n## {timestamp} — Script Improvement: {script_path.name}\n\n"
    f"**Target:** {imp_target}  \n"
    f"**Risk:** {risk}  \n"
    f"**Status:** {status}  \n\n"
    f"{output}\n\n"
    f"---\n"
    f"*Albert Lane | SovereignAudits™ | SEC Ref: 17684-273-411-436*"
)
header_needed = not CHANGELOG.exists() or CHANGELOG.stat().st_size == 0
with open(CHANGELOG, "a") as f:
    if header_needed:
        f.write(
            "# Creative Changelog\n"
            "Running self-critique of creative pipeline scripts.\n"
            "Authored: Albert Lane | SovereignAudits™ | albertlane.net\n"
            "SEC Whistleblower No. 17684-273-411-436\n\n"
        )
    f.write(entry)

# GitHub Actions output
out = os.environ.get("GITHUB_OUTPUT", "")
if out:
    with open(out, "a") as f:
        f.write(f"improvement_target={imp_target}\n")
        f.write(f"patched={str(patched).lower()}\n")
        f.write(f"target_script={target}\n")

print(f"[self-improve-creative] Done. Target={target}, Patched={patched}")
