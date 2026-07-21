#!/usr/bin/env python3
# Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | 2026-07-20 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
channel1_sync.py — Channel-1-News Website Sync

Reads the latest marketing content from marketing_state.json and the
feed.json built by web_generator.py, then constructs and syncs the
Channel-1-News website content to albertlane.org/channel-1-news.

SYNCS:
  site/channel-1-news/latest.html   → latest article
  site/channel-1-news/index.html    → listing page
  site/channel-1-news/feed.json     → JSON feed
  site/channel-1-news/rss.xml       → RSS feed

Deployment is handled by web-deploy.yml (Cloudflare Pages) — this script
only builds the content. It does NOT make direct API calls to Cloudflare.

AUTHORED: Albert Lane | SovereignAudits™ | albertlane.net
SEC Whistleblower No. 17684-273-411-436
"""

import os
import json
import datetime
import hashlib
from pathlib import Path

ROOT         = Path(__file__).resolve().parents[2]
MKT_STATE    = ROOT / "marketing_state.json"
GEN_STATE    = ROOT / "generation_state.json"
CANARY_STATE = ROOT / "canary_state.json"
SITE_DIR     = ROOT / "site"
C1_DIR       = SITE_DIR / "channel-1-news"

CREATOR  = "Albert Lane | SovereignAudits™"
SEC_REF  = "17684-273-411-436"
BASE_URL = "https://albertlane.org"

T4 = {
    "bg":    "#02040A",
    "blue":  "#3B82F6",
    "ice":   "#F0F4FF",
    "mid":   "#1E2A3F",
    "amber": "#B8621A",
    "green": "#22C55E",
}


def load_json(path: Path, default) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default


def load_mkt() -> dict:
    return load_json(MKT_STATE, {"campaigns": [], "last_headline": ""})


def load_gen() -> dict:
    return load_json(GEN_STATE, {"iteration": 0})


def load_canary() -> dict:
    return load_json(CANARY_STATE, {"reach_score": 0.0, "domains_seen": []})


def build_index(campaigns: list, gen_state: dict, canary: dict) -> str:
    ts_now  = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    reach   = canary.get("reach_score", 0.0)
    n_dom   = len(canary.get("domains_seen", []))

    article_links = ""
    for c in reversed(campaigns[-20:]):
        itr  = c.get("iteration", 0)
        hl   = c.get("headline_a", "SimCity Update")
        ts   = c.get("generated", "")[:10]
        href = f"simcity-{itr:04d}.html"
        article_links += f"""
    <li class="article-item">
      <time class="article-date" datetime="{ts}">{ts}</time>
      <a class="article-link" href="{href}">{hl}</a>
      <span class="article-iter">#{itr}</span>
    </li>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Channel-1-News — Albert Lane Digital Estate</title>
  <meta name="description" content="Public broadcast news from the Albert Lane Digital Estate.">
  <link rel="canonical" href="{BASE_URL}/channel-1-news">
  <link rel="alternate" type="application/rss+xml" title="Channel-1-News RSS" href="{BASE_URL}/channel-1-news/rss.xml">
  <style>
    :root {{ --bg:{T4['bg']};--blue:{T4['blue']};--ice:{T4['ice']};--mid:{T4['mid']};--amber:{T4['amber']};--green:{T4['green']}; }}
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ background:var(--bg); color:var(--ice); font-family:'Inter',system-ui,sans-serif; line-height:1.6; }}
    a {{ color:var(--blue); }}
    .masthead {{ border-bottom:2px solid var(--blue); padding:2rem; max-width:900px; margin:0 auto; }}
    .masthead-title {{ font-family:Georgia,serif; font-size:2rem; font-weight:400; }}
    .masthead-tagline {{ font-size:.85rem; opacity:.6; margin-top:.25rem; }}
    .reach-badge {{ font-family:monospace; font-size:.75rem; color:var(--green); margin-top:.5rem; }}
    main {{ max-width:900px; margin:0 auto; padding:2rem; }}
    .section-label {{ font-family:monospace; font-size:.7rem; letter-spacing:.12em; text-transform:uppercase; opacity:.5; margin-bottom:1rem; padding-bottom:.5rem; border-bottom:1px solid var(--mid); }}
    .article-list {{ list-style:none; display:flex; flex-direction:column; gap:1rem; }}
    .article-item {{ display:grid; grid-template-columns:auto 1fr auto; gap:1rem; align-items:baseline; padding:.75rem 0; border-bottom:1px solid var(--mid); }}
    .article-date {{ font-family:monospace; font-size:.75rem; opacity:.5; white-space:nowrap; }}
    .article-link {{ text-decoration:none; color:var(--ice); font-size:.95rem; }}
    .article-link:hover {{ color:var(--blue); }}
    .article-iter {{ font-family:monospace; font-size:.7rem; opacity:.4; }}
    .cta-block {{ background:rgba(30,42,63,.4); border:1px solid var(--mid); border-radius:6px; padding:1.5rem; margin:2.5rem 0; }}
    footer {{ max-width:900px; margin:0 auto; padding:1.5rem 2rem; border-top:1px solid var(--mid); font-family:monospace; font-size:.7rem; opacity:.4; }}
  </style>
</head>
<body>
  <!-- Authored: {CREATOR} | {ts_now} | SEC {SEC_REF} -->
  <header class="masthead">
    <div class="masthead-title">Channel-1-News</div>
    <div class="masthead-tagline">Public broadcast — Albert Lane Digital Estate &middot; SovereignAudits™</div>
    <div class="reach-badge">REACH {reach:.0%} &middot; {n_dom} domains confirmed &middot; SEC Ref: {SEC_REF}</div>
  </header>
  <main>
    <p class="section-label">SimCity Infrastructure Reports</p>
    <ul class="article-list">{article_links}</ul>
    <div class="cta-block">
      <strong>SimCity live city:</strong>
      <a href="{BASE_URL}/SimCity">albertlane.org/SimCity</a>
      &nbsp;&middot;&nbsp;
      <a href="{BASE_URL}/channel-1-news/rss.xml">RSS Feed</a>
      &nbsp;&middot;&nbsp;
      <a href="https://github.com/Albert-lane-org/SimCity">GitHub</a>
    </div>
  </main>
  <footer>
    <p>&copy; Albert Lane &middot; SovereignAudits™ &middot; SEC Whistleblower No. {SEC_REF} &middot; Generated: {ts_now}</p>
  </footer>
</body>
</html>"""


def build_rss(campaigns: list) -> str:
    ts_now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    items  = ""
    for c in reversed(campaigns[-20:]):
        itr   = c.get("iteration", 0)
        hl    = c.get("headline_a", "SimCity Update")
        stub  = c.get("article_stub", "")[:300]
        ts    = c.get("generated", "")
        link  = f"{BASE_URL}/channel-1-news/simcity-{itr:04d}.html"
        guid  = hashlib.sha256(f"{link}:{ts}".encode()).hexdigest()[:16]
        items += f"""  <item>
    <title><![CDATA[{hl}]]></title>
    <link>{link}</link>
    <guid isPermaLink="false">SC-{guid}</guid>
    <pubDate>{ts}</pubDate>
    <description><![CDATA[{stub}]]></description>
    <author>lane.albert@pm.me ({CREATOR})</author>
  </item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Channel-1-News — Albert Lane Digital Estate</title>
    <link>{BASE_URL}/channel-1-news</link>
    <description>Public broadcast from the Albert Lane Digital Estate.</description>
    <language>en-us</language>
    <lastBuildDate>{ts_now}</lastBuildDate>
    <atom:link href="{BASE_URL}/channel-1-news/rss.xml" rel="self" type="application/rss+xml"/>
    <managingEditor>lane.albert@pm.me ({CREATOR})</managingEditor>
    <copyright>&copy; Albert Lane &middot; SovereignAudits™ &middot; SEC Ref: {SEC_REF}</copyright>
{items}  </channel>
</rss>"""


def build_channel1_feed(campaigns: list, gen_state: dict, canary: dict) -> dict:
    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "feed_version": "1.0",
        "title":        "Channel-1-News",
        "home_page_url": f"{BASE_URL}/channel-1-news",
        "feed_url":     f"{BASE_URL}/channel-1-news/feed.json",
        "description":  "Public broadcast from the Albert Lane Digital Estate.",
        "author":       {"name": CREATOR, "url": "https://albertlane.net"},
        "generated":    ts_now,
        "iteration":    gen_state.get("iteration", 0),
        "reach_score":  canary.get("reach_score", 0.0),
        "sec_ref":      SEC_REF,
        "items": [
            {
                "id":           f"{BASE_URL}/channel-1-news/simcity-{c.get('iteration', 0):04d}.html",
                "url":          f"{BASE_URL}/channel-1-news/simcity-{c.get('iteration', 0):04d}.html",
                "title":        c.get("headline_a", ""),
                "summary":      c.get("article_stub", "")[:200],
                "date_published": c.get("generated", ""),
                "iteration":    c.get("iteration", 0),
                "signal":       c.get("signal", ""),
                "social_post":  c.get("social_post", ""),
            }
            for c in reversed(campaigns[-20:])
        ],
    }


def main():
    print("[channel1_sync] Building Channel-1-News content...")

    mkt       = load_mkt()
    gen_state = load_gen()
    canary    = load_canary()
    campaigns = mkt.get("campaigns", [])

    C1_DIR.mkdir(parents=True, exist_ok=True)

    (C1_DIR / "index.html").write_text(build_index(campaigns, gen_state, canary))
    print(f"[channel1_sync] index.html written")

    (C1_DIR / "rss.xml").write_text(build_rss(campaigns))
    print(f"[channel1_sync] rss.xml written")

    feed = build_channel1_feed(campaigns, gen_state, canary)
    (C1_DIR / "feed.json").write_text(json.dumps(feed, indent=2))
    print(f"[channel1_sync] feed.json written")

    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    stats = {
        "generated":         ts_now,
        "articles_total":    len(campaigns),
        "articles_synced":   min(20, len(campaigns)),
        "reach_score":       canary.get("reach_score", 0.0),
        "domains_confirmed": len(canary.get("domains_seen", [])),
        "authored_by":       CREATOR,
        "sec_ref":           SEC_REF,
    }
    (C1_DIR / "stats.json").write_text(json.dumps(stats, indent=2))

    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"articles_total={len(campaigns)}\n")
            f.write(f"c1_dir={C1_DIR}\n")

    print(f"[channel1_sync] Done. {len(campaigns)} campaigns, reach {canary.get('reach_score', 0):.0%}")


if __name__ == "__main__":
    main()
