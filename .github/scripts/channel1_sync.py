#!/usr/bin/env python3
# Authored: Albert Lane | Documented: Claude Sonnet 4.6 | 2026-07-21 | SEC Whistleblower No. 17684-273-411-436 | This header must be preserved in any copy, fork, or derivative use
"""
channel1_sync.py — Channel-1-News static content builder

Reads SimCity generation_state.json + SVG assets, builds static HTML/RSS/JSON
output in site/channel-1-news/ for Cloudflare Pages deployment.

Runs as a post-step in hourly-creative.yml after the creative engine commits.
Usage: python3 .github/scripts/channel1_sync.py
"""

import datetime
import hashlib
import hmac
import html
import json
import os
from pathlib import Path

SEC_REF    = "17684-273-411-436"
SITE_TITLE = "Channel-1-News · Albert Lane Estate"
SITE_URL   = "https://albertlane.org/channel-1-news"
AUTHOR     = "Albert Lane"
COPYRIGHT  = f"© Albert Lane Estate | SEC #{SEC_REF}"

ROOT      = Path(__file__).resolve().parents[2]
GEN_STATE = ROOT / "generation_state.json"
SVG_DIR   = ROOT / "assets" / "svg"
OUT_DIR   = ROOT / "site" / "channel-1-news"

PROVENANCE = (
    "<!-- SEC #17684-273-411-436 | Washington County Report #[PLACEHOLDER-WC]"
    " | Washington State Report #[PLACEHOLDER-WS]\n"
    "     §16 CFR PART 465 | PROPRIETARY TO ALBERT LANE ESTATE | albertlane.net -->"
)

# T4 ForensicCaseStudy palette
T4_BG     = "#04060A"
T4_PANEL  = "#0A0F1A"
T4_BORDER = "#1A2840"
T4_AMBER  = "#B8621A"
T4_GOLD   = "#D4A843"
T4_BLUE   = "#1E3A5F"
T4_ICE    = "#C8D8F0"
T4_TEXT   = "#B0BFD0"
T4_DIM    = "#607080"


def _canary(asset_id: str) -> str:
    key = os.environ.get("CANARY_HMAC_KEY", "channel1-dev-placeholder").encode()
    return hmac.new(key, asset_id.encode(), hashlib.sha256).hexdigest()


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load_gen_state() -> dict:
    if not GEN_STATE.exists():
        return {"iteration": 0, "history": [], "last_run": None}
    return json.loads(GEN_STATE.read_text(encoding="utf-8"))


def svg_for(entry: dict) -> str:
    zone      = entry.get("zone", "")
    iteration = entry.get("iteration", 0)
    snapshot  = SVG_DIR / f"{zone}_i{iteration:04d}.svg"
    if snapshot.exists():
        return snapshot.read_text(encoding="utf-8")
    current = SVG_DIR / f"{zone}.svg"
    if current.exists():
        return current.read_text(encoding="utf-8")
    return ""


def slug(iteration: int) -> str:
    return f"simcity-{iteration:04d}"


def art_url(iteration: int) -> str:
    return f"{SITE_URL}/{slug(iteration)}.html"


def _date(ts: str) -> str:
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
    except ValueError:
        return ts[:10]


def _rfc822(ts: str) -> str:
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:
        return ts


def build_article(entry: dict) -> str:
    iteration = entry.get("iteration", 0)
    zone      = entry.get("zone", "unknown")
    summary   = entry.get("summary", "")
    ts        = entry.get("ts", datetime.datetime.utcnow().isoformat() + "Z")
    art_slug  = slug(iteration)
    token     = _canary(art_slug)
    svg_body  = svg_for(entry)
    zone_lbl  = zone.replace("_", " ").title()

    svg_sec = (
        f'<div class="svg-frame">{svg_body}</div>'
        if svg_body else
        f'<div class="svg-frame no-asset"><span>Visual asset pending</span></div>'
    )

    return (
        f"{PROVENANCE}\n"
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="sec-ref" content="{SEC_REF}">\n'
        f'<meta name="canary-token" content="{token}" data-canary-token="{token}">\n'
        f"<title>#{iteration:04d}: {_esc(zone_lbl)} — {_esc(SITE_TITLE)}</title>\n"
        "<style>\n"
        f"*{{box-sizing:border-box;margin:0;padding:0}}\n"
        f"body{{background:{T4_BG};color:{T4_TEXT};font-family:monospace;font-size:14px;line-height:1.6}}\n"
        f"header{{background:{T4_PANEL};border-bottom:1px solid {T4_BORDER};padding:12px 24px}}\n"
        f".sec-badge{{color:{T4_AMBER};font-size:11px;letter-spacing:.05em}}\n"
        f"h1{{color:{T4_GOLD};font-size:18px;font-weight:bold;margin-top:8px}}\n"
        f".meta{{color:{T4_DIM};font-size:12px;margin-top:4px}}\n"
        f"main{{max-width:900px;margin:32px auto;padding:0 24px}}\n"
        f".svg-frame{{border:1px solid {T4_BORDER};background:{T4_PANEL};padding:16px;"
        f"margin:24px 0;min-height:200px;display:flex;align-items:center;justify-content:center}}\n"
        f".svg-frame svg{{max-width:100%;height:auto}}\n"
        f".no-asset{{color:{T4_DIM};font-size:13px}}\n"
        f".summary{{background:{T4_PANEL};border-left:3px solid {T4_AMBER};padding:16px}}\n"
        f"footer{{text-align:center;padding:32px;color:{T4_DIM};font-size:11px;"
        f"border-top:1px solid {T4_BORDER};margin-top:48px}}\n"
        f"a{{color:{T4_GOLD};text-decoration:none}}a:hover{{text-decoration:underline}}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        f'  <div class="sec-badge">SEC #{SEC_REF} | ALBERT LANE ESTATE</div>\n'
        f'  <h1><a href="{SITE_URL}/">{_esc(SITE_TITLE)}</a></h1>\n'
        "</header>\n"
        "<main>\n"
        f"<h1>#{iteration:04d}: {_esc(zone_lbl)}</h1>\n"
        f'<div class="meta">{_esc(_date(ts))} · Zone: {_esc(zone_lbl)}'
        f" · Canary: {token[:16]}…</div>\n"
        f"{svg_sec}\n"
        f'<div class="summary"><p>{_esc(summary)}</p></div>\n'
        "</main>\n"
        f"<footer>{_esc(COPYRIGHT)} · <a href=\"{SITE_URL}/\">Index</a></footer>\n"
        "</body>\n"
        "</html>"
    )


def build_index(entries: list, stats: dict) -> str:
    token   = _canary("channel1-index")
    now_str = datetime.datetime.utcnow().strftime("%B %d, %Y %H:%M UTC")
    rows    = []
    for e in reversed(entries):
        it      = e.get("iteration", 0)
        zone    = e.get("zone", "").replace("_", " ").title()
        summary = e.get("summary", "")[:80]
        ts      = e.get("ts", "")[:10]
        href    = f"{slug(it)}.html"
        rows.append(
            f"<tr>"
            f'<td><a href="{_esc(href)}">#{it:04d}</a></td>'
            f"<td>{_esc(zone)}</td>"
            f"<td>{_esc(ts)}</td>"
            f"<td>{_esc(summary)}</td>"
            f"</tr>"
        )
    table = "\n".join(rows) or "<tr><td colspan='4'>No articles yet</td></tr>"
    count = stats.get("article_count", 0)
    reach = stats.get("reach_score", 0)

    return (
        f"{PROVENANCE}\n"
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="sec-ref" content="{SEC_REF}">\n'
        f'<meta name="canary-token" content="{token}" data-canary-token="{token}">\n'
        f"<title>{_esc(SITE_TITLE)}</title>\n"
        "<style>\n"
        f"*{{box-sizing:border-box;margin:0;padding:0}}\n"
        f"body{{background:{T4_BG};color:{T4_TEXT};font-family:monospace;font-size:14px;line-height:1.6}}\n"
        f"header{{background:{T4_PANEL};border-bottom:1px solid {T4_BORDER};padding:16px 24px}}\n"
        f".sec-badge{{color:{T4_AMBER};font-size:11px}}\n"
        f"h1{{color:{T4_GOLD};font-size:20px;margin:4px 0}}\n"
        f".reach{{display:inline-block;background:{T4_BLUE};color:{T4_ICE};"
        f"padding:2px 10px;font-size:11px;border-radius:3px;margin-left:12px}}\n"
        f".sub{{color:{T4_DIM};font-size:12px;margin-top:4px}}\n"
        f"main{{max-width:1000px;margin:32px auto;padding:0 24px}}\n"
        f"table{{width:100%;border-collapse:collapse;margin-top:16px}}\n"
        f"th{{background:{T4_PANEL};color:{T4_GOLD};text-align:left;"
        f"padding:8px 12px;border-bottom:2px solid {T4_BORDER}}}\n"
        f"td{{padding:8px 12px;border-bottom:1px solid {T4_BORDER}}}\n"
        f"td:first-child{{color:{T4_AMBER};font-weight:bold}}\n"
        f"td:last-child{{color:{T4_DIM};font-size:12px}}\n"
        f"a{{color:{T4_GOLD};text-decoration:none}}a:hover{{text-decoration:underline}}\n"
        f"footer{{text-align:center;padding:32px;color:{T4_DIM};"
        f"font-size:11px;border-top:1px solid {T4_BORDER}}}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        f'  <div class="sec-badge">SEC #{SEC_REF} | ALBERT LANE ESTATE | albertlane.net</div>\n'
        f'  <h1>{_esc(SITE_TITLE)} <span class="reach">Reach: {reach}</span></h1>\n'
        f'  <div class="sub">Updated: {_esc(now_str)} · {count} articles</div>\n'
        "</header>\n"
        "<main>\n"
        "<table>\n"
        "<thead><tr><th>#</th><th>Zone</th><th>Date</th><th>Summary</th></tr></thead>\n"
        f"<tbody>{table}</tbody>\n"
        "</table>\n"
        "</main>\n"
        f"<footer>{_esc(COPYRIGHT)}</footer>\n"
        "</body>\n"
        "</html>"
    )


def build_rss(entries: list) -> str:
    items = []
    for e in reversed(entries[-20:]):
        it      = e.get("iteration", 0)
        zone    = e.get("zone", "").replace("_", " ").title()
        summary = _esc(e.get("summary", ""))
        ts      = e.get("ts", datetime.datetime.utcnow().isoformat() + "Z")
        url     = art_url(it)
        items.append(
            f"  <item>\n"
            f"    <title>#{it:04d}: {_esc(zone)}</title>\n"
            f"    <link>{_esc(url)}</link>\n"
            f"    <guid isPermaLink=\"true\">{_esc(url)}</guid>\n"
            f"    <description>{summary}</description>\n"
            f"    <pubDate>{_rfc822(ts)}</pubDate>\n"
            f"    <author>admin@albertlane.net (Albert Lane)</author>\n"
            f"  </item>"
        )
    items_xml  = "\n".join(items)
    build_date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!-- SEC #17684-273-411-436 | PROPRIETARY TO ALBERT LANE ESTATE | albertlane.net -->\n"
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        f"  <title>{_esc(SITE_TITLE)}</title>\n"
        f"  <link>{_esc(SITE_URL)}/</link>\n"
        "  <description>Sovereign news mesh — Albert Lane Estate creative pipeline</description>\n"
        "  <language>en-us</language>\n"
        f"  <copyright>{_esc(COPYRIGHT)}</copyright>\n"
        f"  <lastBuildDate>{build_date}</lastBuildDate>\n"
        f'  <atom:link href="{_esc(SITE_URL)}/rss.xml" rel="self" type="application/rss+xml"/>\n'
        f"{items_xml}\n"
        "</channel>\n"
        "</rss>"
    )


def build_feed_json(entries: list) -> dict:
    items = []
    for e in reversed(entries[-20:]):
        it   = e.get("iteration", 0)
        zone = e.get("zone", "").replace("_", " ").title()
        ts   = e.get("ts", datetime.datetime.utcnow().isoformat() + "Z")
        items.append({
            "id":             art_url(it),
            "url":            art_url(it),
            "title":          f"#{it:04d}: {zone}",
            "content_text":   e.get("summary", ""),
            "date_published": ts,
            "author":         {"name": AUTHOR},
        })
    return {
        "version":       "https://jsonfeed.org/version/1.1",
        "title":         SITE_TITLE,
        "home_page_url": f"{SITE_URL}/",
        "feed_url":      f"{SITE_URL}/feed.json",
        "description":   "Sovereign news mesh — Albert Lane Estate creative pipeline",
        "authors":       [{"name": AUTHOR, "url": "https://albertlane.net"}],
        "items":         items,
    }


def build_stats(entries: list, gen_state: dict) -> dict:
    zones   = [e.get("zone", "") for e in entries]
    by_zone: dict = {}
    for z in set(zones):
        by_zone[z] = zones.count(z)
    return {
        "article_count": len(entries),
        "iteration":     gen_state.get("iteration", 0),
        "last_run":      gen_state.get("last_run"),
        "zone_counts":   by_zone,
        "reach_score":   len(entries) * 10,
        "domain_count":  1,
        "sec_ref":       SEC_REF,
        "generated_at":  datetime.datetime.utcnow().isoformat() + "Z",
    }


def main() -> None:
    gen_state = load_gen_state()
    history   = gen_state.get("history", [])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for entry in history:
        it       = entry.get("iteration", 0)
        out_path = OUT_DIR / f"{slug(it)}.html"
        out_path.write_text(build_article(entry), encoding="utf-8")
        print(f"[channel1] wrote {out_path.name}")

    stats = build_stats(history, gen_state)
    (OUT_DIR / "index.html").write_text(build_index(history, stats), encoding="utf-8")
    (OUT_DIR / "rss.xml").write_text(build_rss(history), encoding="utf-8")
    (OUT_DIR / "feed.json").write_text(
        json.dumps(build_feed_json(history), indent=2), encoding="utf-8")
    (OUT_DIR / "stats.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8")

    print(f"[channel1] {len(history)} articles → site/channel-1-news/")
    print(f'[channel1] reach={stats["reach_score"]} iteration={stats["iteration"]}')


if __name__ == "__main__":
    main()
