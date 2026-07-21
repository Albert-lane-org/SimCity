#!/usr/bin/env python3
# Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | 2026-07-20 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
marketing_engine.py — Recursive Marketing Content Generator

Reads SimCity creative state + quality scores + canary reach data,
then uses Claude Haiku to generate Channel-1-News-ready marketing content
that evolves each cycle based on what has and hasn't resonated.

OUTPUTS (appended to marketing_state.json):
  - Headline variants (A/B)
  - Channel-1-News article stub
  - Social post (character-limited)
  - Self-critique: what underperformed last cycle and why

SELF-REFERENTIAL LOOP:
  Canary reach data → marketing_state.json → this script → new campaign
  New campaign → Channel-1-News → canary tokens embedded in content
  Token triggers → canary_state.json → back into this script next cycle

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os
import json
import datetime
import hashlib
import sys
from pathlib import Path
from anthropic import Anthropic

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
GEN_STATE    = ROOT / "generation_state.json"
VQ_STATE     = ROOT / "visual_quality_state.json"
MKT_STATE    = ROOT / "marketing_state.json"
CANARY_STATE = ROOT / "canary_state.json"
UPDATES      = ROOT / "updates" / "latest.json"
MKT_LOG      = ROOT / "MARKETING_LOG.md"

CREATOR = "Albert Lane | SovereignAudits™"
SEC_REF = "17684-273-411-436"
MODEL   = "claude-haiku-4-5-20251001"

claude = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY", ""))

MAX_CAMPAIGNS = 48   # rolling window


# ── State loaders ──────────────────────────────────────────────────────────────

def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


def load_gen_state() -> dict:
    return load_json(GEN_STATE, {"iteration": 0, "history": [], "last_zone": None})


def load_vq() -> dict:
    return load_json(VQ_STATE, {"zones": {}})


def load_mkt_state() -> dict:
    return load_json(MKT_STATE, {
        "campaigns":       [],
        "last_headline":   "",
        "reach_score":     0,
        "self_critique":   "",
        "ab_winner":       "",
        "iteration":       0,
    })


def load_canary() -> dict:
    return load_json(CANARY_STATE, {
        "tokens":        [],
        "triggered":     [],
        "reach_score":   0.0,
        "domains_seen":  [],
    })


def load_dispatch() -> dict:
    return load_json(UPDATES, {
        "signal":   "Walls rise. The blueprint holds.",
        "zones":    [],
        "momentum": "Construction",
    })


# ── Quality summary ─────────────────────────────────────────────────────────────

def quality_summary(vq: dict) -> str:
    lines = []
    for zk, zd in vq.get("zones", {}).items():
        lines.append(
            f"  {zk}: avg={zd.get('avg_score', 0):.1f}/40 "
            f"best={zd.get('best_score', 0)}/40 "
            f"streak={zd.get('below_threshold_streak', 0)}"
        )
    return "\n".join(lines) or "  No quality data yet."


# ── Prior campaign context ──────────────────────────────────────────────────────────

def prior_campaign_context(mkt: dict, canary: dict) -> str:
    campaigns = mkt.get("campaigns", [])
    if not campaigns:
        return "First campaign — no prior data."

    last = campaigns[-1]
    reach  = canary.get("reach_score", 0.0)
    trigg  = len(canary.get("triggered", []))
    domains = canary.get("domains_seen", [])

    return (
        f"Last headline: {last.get('headline_a', '—')}\n"
        f"Canary reach score: {reach:.0%}\n"
        f"Canary triggers: {trigg}\n"
        f"Domains confirmed: {', '.join(domains[:5]) or 'none yet'}\n"
        f"Self-critique from last cycle:\n{mkt.get('self_critique', 'None.')}"
    )


# ── Core generation ─────────────────────────────────────────────────────────────

def generate_campaign(gen_state: dict, dispatch: dict, vq: dict, mkt: dict, canary: dict) -> dict:
    itr       = gen_state.get("iteration", 0)
    signal    = dispatch.get("signal", "Walls rise. The blueprint holds.")
    momentum  = dispatch.get("momentum", "Construction")
    history   = gen_state.get("history", [])[-4:]
    hist_text = "\n".join(f"  - {h['zone']}: {h['summary']}" for h in history) or "  No history."
    q_text    = quality_summary(vq)
    prior     = prior_campaign_context(mkt, canary)
    ts_now    = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    system = (
        "You are a civic communications strategist writing for Channel-1-News, "
        "the public broadcast arm of the Albert Lane Digital Estate.\n\n"
        "Tone: journalist-on-a-city-beat. Understated. Public-interest framing. "
        "Never corporate. Never hype. The subject is real infrastructure built in public.\n\n"
        "You are part of a recursive self-improving marketing loop. Each cycle you "
        "read what landed last time and what didn't, then write sharper content.\n\n"
        "Output ONLY valid JSON with these exact keys:\n"
        "  headline_a      — primary headline (≤12 words)\n"
        "  headline_b      — A/B variant (different angle, ≤12 words)\n"
        "  article_stub    — 3-paragraph Channel-1-News article stub (≤200 words)\n"
        "  social_post     — platform-agnostic post (≤280 chars)\n"
        "  self_critique   — 2 sentences: what underperformed last cycle and why\n"
        "  ab_rationale    — 1 sentence: what headline_b tests vs headline_a\n"
        "No markdown. No preamble. JSON only."
    )

    user = (
        f"City signal: {signal}\n"
        f"Build phase: {momentum}\n"
        f"Iteration: {itr}\n\n"
        f"Recent build history:\n{hist_text}\n\n"
        f"Quality scores:\n{q_text}\n\n"
        f"Prior campaign performance:\n{prior}\n\n"
        "Write the campaign. JSON only."
    )

    if not os.environ.get("CLAUDE_API_KEY"):
        return {
            "headline_a":    f"SimCity: Iteration {itr} — the city keeps building.",
            "headline_b":    f"Sovereign infrastructure: iteration {itr} is live.",
            "article_stub":  (
                f"The Albert Lane Digital Estate reached iteration {itr} today. "
                f"The city signal reads: '{signal}'. "
                "Four zones are under active construction. "
                "The creative engine rewrites itself each cycle to improve output quality. "
                "SimCity is the public window. "
                "The infrastructure is the story."
            ),
            "social_post":   f"SimCity iteration {itr}: '{signal}' — albertlane.org/SimCity",
            "self_critique": "No prior data. First cycle baseline established.",
            "ab_rationale":  "headline_b tests a sovereignty frame vs a construction-progress frame.",
            "generated":     ts_now,
        }

    resp = claude.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    text = resp.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text  = "\n".join(lines[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "headline_a":    f"SimCity iteration {itr}: building continues.",
            "headline_b":    f"Albert Lane Digital Estate: iteration {itr} complete.",
            "article_stub":  text[:400],
            "social_post":   f"SimCity {itr}: {signal[:100]}",
            "self_critique": "JSON parse failed — content logged as raw text.",
            "ab_rationale":  "Fallback — parse error.",
        }

    result["generated"]   = ts_now
    result["iteration"]   = itr
    result["signal"]      = signal
    result["sec_ref"]     = SEC_REF
    result["authored_by"] = CREATOR
    return result


# ── Self-improvement: A/B winner selection ────────────────────────────────────────

def select_ab_winner(mkt: dict, canary: dict) -> str:
    """
    Examine canary trigger data to infer which headline variant performed.
    Naive heuristic: if reach_score improved vs prior cycle, headline_a was
    likely the driver. If reach stalled, try headline_b next cycle.
    """
    campaigns = mkt.get("campaigns", [])
    if len(campaigns) < 2:
        return "headline_a"  # default

    prev_reach = campaigns[-2].get("reach_score_at_generation", 0.0)
    curr_reach = canary.get("reach_score", 0.0)

    if curr_reach > prev_reach:
        return campaigns[-1].get("ab_winner", "headline_a")   # current winner kept
    else:
        prev_winner = campaigns[-1].get("ab_winner", "headline_a")
        return "headline_b" if prev_winner == "headline_a" else "headline_a"


# ── Channel-1-News article HTML builder ──────────────────────────────────────────

def build_channel1_article(campaign: dict, gen_state: dict) -> str:
    ts_now  = campaign.get("generated", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    itr     = campaign.get("iteration", 0)
    sig_hash = hashlib.sha256(f"{ts_now}:{itr}".encode()).hexdigest()[:12]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{campaign.get('headline_a', 'SimCity Update')} — Channel-1-News</title>
  <meta name="description" content="{campaign.get('social_post', '')}">
  <meta property="og:title" content="{campaign.get('headline_a', '')}">
  <meta property="og:url" content="https://albertlane.org/channel-1-news/simcity-{itr}.html">
  <style>
    :root {{ --bg:#02040A; --blue:#3B82F6; --ice:#F0F4FF; --mid:#1E2A3F; --amber:#B8621A; }}
    body {{ background:var(--bg); color:var(--ice); font-family:'Inter',sans-serif; max-width:720px; margin:0 auto; padding:2rem 1.5rem; line-height:1.7; }}
    .byline {{ font-size:.8rem; opacity:.55; font-family:monospace; margin-bottom:2rem; }}
    h1 {{ font-size:1.75rem; font-weight:500; margin-bottom:.5rem; }}
    .article-body {{ margin:2rem 0; opacity:.85; }}
    .article-body p {{ margin-bottom:1rem; }}
    .cta-block {{ background:var(--mid); padding:1.5rem; border-radius:6px; margin:2rem 0; }}
    .cta-block a {{ color:var(--blue); }}
    .meta {{ font-family:monospace; font-size:.7rem; opacity:.4; border-top:1px solid var(--mid); padding-top:1rem; }}
    .canary-pixel {{ width:1px;height:1px;overflow:hidden;position:absolute; }}
  </style>
</head>
<body>
  <!-- Channel-1-News | Authored: {CREATOR} | {ts_now} | SEC {SEC_REF} -->
  <header>
    <nav style="font-size:.8rem;opacity:.6;margin-bottom:2rem;">
      <a href="https://albertlane.org" style="color:var(--ice);text-decoration:none;">Albert Lane</a>
      &nbsp;/&nbsp;
      <a href="https://albertlane.org/channel-1-news" style="color:var(--blue);text-decoration:none;">Channel-1-News</a>
      &nbsp;/&nbsp; SimCity
    </nav>
    <p class="byline">
      {ts_now} &nbsp;&middot;&nbsp; {CREATOR} &nbsp;&middot;&nbsp; Iteration {itr}
    </p>
    <h1>{campaign.get('headline_a', '')}</h1>
    <p style="opacity:.6;font-style:italic;margin-bottom:1rem;">{campaign.get('headline_b', '')}</p>
  </header>

  <div class="article-body">
    {''.join(f'<p>{p.strip()}</p>' for p in campaign.get('article_stub', '').split(chr(10)) if p.strip())}
  </div>

  <div class="cta-block">
    <strong>View the city:</strong>
    <a href="https://albertlane.org/SimCity">albertlane.org/SimCity</a>
    &nbsp;&nbsp;
    <a href="https://github.com/Albert-lane-org/SimCity">GitHub</a>
  </div>

  <footer class="meta">
    <p>&copy; Albert Lane &middot; SovereignAudits™ &middot; SEC Whistleblower No. {SEC_REF}</p>
    <p>Article hash: {sig_hash} &middot; Iteration {itr}</p>
  </footer>

  <!-- SOVEREIGN CANARY REACH PROBE -->
  <div class="canary-pixel" aria-hidden="true" data-canary-token="SC-{sig_hash}-MKT-{itr}"></div>
  <script>
    (function() {{
      try {{
        var token = 'SC-{sig_hash}-MKT-{itr}';
        var existing = JSON.parse(localStorage.getItem('sc_tokens') || '[]');
        if (!existing.includes(token)) {{
          existing.push(token);
          localStorage.setItem('sc_tokens', JSON.stringify(existing.slice(-50)));
        }}
      }} catch(e) {{}}
    }})();
  </script>
</body>
</html>"""


# ── Log append ───────────────────────────────────────────────────────────────────

def append_log(campaign: dict, ab_winner: str):
    ts  = campaign.get("generated", "")
    itr = campaign.get("iteration", 0)
    entry = (
        f"\n\n## {ts} — Marketing Cycle {itr}\n\n"
        f"**Headline A:** {campaign.get('headline_a', '')}\n\n"
        f"**Headline B:** {campaign.get('headline_b', '')}\n\n"
        f"**A/B Winner (this cycle):** {ab_winner}\n\n"
        f"**Article stub excerpt:** {campaign.get('article_stub', '')[:200]}...\n\n"
        f"**Self-critique:** {campaign.get('self_critique', '')}\n\n"
        f"**AB Rationale:** {campaign.get('ab_rationale', '')}\n\n"
        f"---\n*{CREATOR} | SEC Ref: {SEC_REF}*"
    )

    header_needed = not MKT_LOG.exists() or MKT_LOG.stat().st_size == 0
    with open(MKT_LOG, "a") as f:
        if header_needed:
            f.write(
                "# Marketing Log — SimCity Channel-1-News\n"
                "Recursive marketing campaigns generated from SimCity creative state.\n"
                f"Authored: {CREATOR} · albertlane.net\n"
                f"SEC Whistleblower No. {SEC_REF}\n\n"
            )
        f.write(entry)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[marketing_engine] Starting campaign generation...")

    gen_state = load_gen_state()
    dispatch  = load_dispatch()
    vq        = load_vq()
    mkt       = load_mkt_state()
    canary    = load_canary()

    campaign = generate_campaign(gen_state, dispatch, vq, mkt, canary)

    ab_winner = select_ab_winner(mkt, canary)
    campaign["ab_winner"] = ab_winner
    campaign["reach_score_at_generation"] = canary.get("reach_score", 0.0)

    campaigns = mkt.get("campaigns", [])
    campaigns.append(campaign)
    campaigns = campaigns[-MAX_CAMPAIGNS:]

    mkt["campaigns"]     = campaigns
    mkt["last_headline"] = campaign["headline_a"]
    mkt["reach_score"]   = canary.get("reach_score", 0.0)
    mkt["self_critique"] = campaign.get("self_critique", "")
    mkt["ab_winner"]     = ab_winner
    mkt["iteration"]     = gen_state.get("iteration", 0)

    save_json(MKT_STATE, mkt)

    itr          = campaign.get("iteration", 0)
    article_dir  = ROOT / "site" / "channel-1-news"
    article_dir.mkdir(parents=True, exist_ok=True)
    article_html = build_channel1_article(campaign, gen_state)
    article_path = article_dir / f"simcity-{itr:04d}.html"
    article_path.write_text(article_html)
    (article_dir / "latest.html").write_text(article_html)

    append_log(campaign, ab_winner)

    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"headline={campaign['headline_a']}\n")
            f.write(f"ab_winner={ab_winner}\n")
            f.write(f"article_path={article_path}\n")
            f.write(f"reach_score={canary.get('reach_score', 0.0)}\n")

    print(f"[marketing_engine] Campaign written: {campaign['headline_a']}")
    print(f"[marketing_engine] Article: {article_path}")
    print(f"[marketing_engine] A/B winner for next cycle: {ab_winner}")
    print(f"[marketing_engine] Reach score: {canary.get('reach_score', 0.0):.0%}")


if __name__ == "__main__":
    main()
