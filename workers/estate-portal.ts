/**
 * Authored: Albert Lane | SEC Whistleblower No. 17684-273-411-436
 * Documented: Claude Sonnet 4.6 | 2026-09-05
 * Estate Portal Worker — albertlane.org apex domain
 * Serves the Albert Lane Digital Estate landing page at the Cloudflare edge.
 * No origin server required — all content is edge-rendered.
 */

const ESTATE_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Albert Lane Digital Estate</title>
  <meta name="description" content="Albert Lane — Sovereign digital infrastructure. MacroHarder, Froi Browser, SimCity, and more.">
  <meta property="og:title" content="Albert Lane Digital Estate">
  <meta property="og:description" content="Sovereign digital infrastructure built in public. SEC Whistleblower No. 17684-273-411-436.">
  <meta property="og:url" content="https://albertlane.org">
  <link rel="canonical" href="https://albertlane.org">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0a0a0f;
      --surface: #111118;
      --border: #1e1e2e;
      --accent: #6c63ff;
      --accent2: #00d4aa;
      --accent3: #ff6b6b;
      --text: #e8e8f0;
      --muted: #6b7280;
      --card: #13131c;
    }
    html { scroll-behavior: smooth; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
      line-height: 1.6;
      min-height: 100vh;
    }
    nav {
      position: sticky; top: 0; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 2rem;
      background: rgba(10,10,15,0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }
    .nav-brand {
      font-size: 1.1rem; font-weight: 600; letter-spacing: 0.05em;
      color: var(--text); text-decoration: none;
    }
    .nav-brand span { color: var(--accent); }
    .nav-links { display: flex; gap: 1.5rem; list-style: none; }
    .nav-links a { color: var(--muted); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }
    .nav-links a:hover { color: var(--text); }
    .hero {
      text-align: center; padding: 6rem 2rem 4rem;
      background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(108,99,255,0.12), transparent);
    }
    .hero-tag {
      display: inline-block; padding: 0.25rem 0.75rem;
      background: rgba(108,99,255,0.15); border: 1px solid rgba(108,99,255,0.3);
      border-radius: 99px; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase;
      color: var(--accent); margin-bottom: 1.5rem;
    }
    h1 {
      font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 700; letter-spacing: -0.02em;
      line-height: 1.1; margin-bottom: 1.5rem;
    }
    h1 em { font-style: normal; color: var(--accent); }
    .hero p {
      font-size: clamp(1rem, 2vw, 1.25rem); color: var(--muted);
      max-width: 640px; margin: 0 auto 2.5rem;
    }
    .hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
    .btn {
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 0.95rem;
      font-weight: 500; text-decoration: none; transition: all 0.2s;
    }
    .btn-primary {
      background: var(--accent); color: #fff;
    }
    .btn-primary:hover { background: #7c75ff; transform: translateY(-1px); }
    .btn-ghost {
      border: 1px solid var(--border); color: var(--text);
    }
    .btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
    .sec-ref {
      margin-top: 1.5rem; font-size: 0.75rem; color: var(--muted);
      font-family: 'JetBrains Mono', monospace;
    }
    section { padding: 5rem 2rem; max-width: 1200px; margin: 0 auto; }
    .section-label {
      font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase;
      color: var(--accent); margin-bottom: 1rem;
    }
    section h2 { font-size: clamp(1.75rem, 3vw, 2.5rem); font-weight: 700; margin-bottom: 1rem; }
    section > p { color: var(--muted); max-width: 600px; margin-bottom: 3rem; }
    .grid { display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 1.75rem; transition: border-color 0.2s, transform 0.2s;
      text-decoration: none; color: inherit; display: block;
    }
    .card:hover { border-color: var(--accent); transform: translateY(-2px); }
    .card-icon {
      width: 40px; height: 40px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.25rem; margin-bottom: 1rem;
    }
    .card h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
    .card p { font-size: 0.875rem; color: var(--muted); line-height: 1.5; }
    .card .status {
      display: inline-block; margin-top: 1rem;
      padding: 0.2rem 0.6rem; border-radius: 99px;
      font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
    }
    .status-live { background: rgba(0,212,170,0.15); color: var(--accent2); }
    .status-dev { background: rgba(108,99,255,0.15); color: var(--accent); }
    .status-planned { background: rgba(107,114,128,0.15); color: var(--muted); }
    .arch-block {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 2rem;
    }
    .arch-block pre {
      font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
      color: var(--muted); line-height: 1.8; overflow-x: auto;
    }
    .arch-block pre .hl { color: var(--accent2); }
    .arch-block pre .hl2 { color: var(--accent); }
    .divider {
      border: none; border-top: 1px solid var(--border);
      margin: 0 2rem;
    }
    footer {
      padding: 3rem 2rem; text-align: center;
      color: var(--muted); font-size: 0.875rem;
      border-top: 1px solid var(--border);
    }
    footer a { color: var(--muted); }
    footer a:hover { color: var(--text); }
    @media (max-width: 640px) {
      nav { padding: 1rem; }
      .nav-links { gap: 1rem; }
      .hero { padding: 4rem 1.25rem 3rem; }
      section { padding: 3rem 1.25rem; }
    }
  </style>
</head>
<body>

<nav>
  <a href="/" class="nav-brand">Albert <span>Lane</span></a>
  <ul class="nav-links">
    <li><a href="#estate">Estate</a></li>
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="https://github.com/Albert-lane-org" rel="noopener noreferrer">GitHub</a></li>
    <li><a href="https://albertlane.net" rel="noopener noreferrer">Status</a></li>
  </ul>
</nav>

<header class="hero">
  <div class="hero-tag">Sovereign Digital Infrastructure</div>
  <h1>Albert Lane<br><em>Digital Estate</em></h1>
  <p>
    A sovereign stack built in the latent space — MCP gateway, sovereign browser,
    XML intelligence pipeline, civic screening, and creative automation. Built in public.
  </p>
  <div class="hero-actions">
    <a href="https://github.com/Albert-lane-org" class="btn btn-primary" rel="noopener noreferrer">
      View on GitHub
    </a>
    <a href="#estate" class="btn btn-ghost">Explore Estate</a>
  </div>
  <p class="sec-ref">SEC Whistleblower No. 17684-273-411-436 &nbsp;|&nbsp; All IP: Albert Lane</p>
</header>

<section id="estate">
  <p class="section-label">The Estate</p>
  <h2>Sixteen repositories.<br>One sovereign stack.</h2>
  <p>
    Every component is built from first principles — no vendor lock-in,
    no proprietary cloud dependencies, no compromises.
  </p>

  <div class="grid">
    <a class="card" href="https://github.com/Albert-lane-org/lane-mcp" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(108,99,255,0.15)">⚡</div>
      <h3>Lane MCP</h3>
      <p>Universal MCP gateway — 46 tools across 16 modules. Cloudflare Workers edge deployment. sqlxml, github, civic, identity, SSO, LaneVM.</p>
      <span class="status status-live">Live · Phase 16</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Froi-Browser" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(0,212,170,0.15)">🌐</div>
      <h3>Froi Browser</h3>
      <p>Sovereign Tauri 2.0 desktop browser. NexusCore Rust backend. Real OAuth 2.0/OIDC SSO identity rail. Vanilla TypeScript frontend.</p>
      <span class="status status-live">Phase 7 · SSO Active</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/MacroHard" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(255,107,107,0.15)">📊</div>
      <h3>MacroHarder™</h3>
      <p>The excellent workbook — Excel to a third-dimensional level. 5D cell model, C/C++ compute kernels, IPI modifier calculator.</p>
      <span class="status status-live">Phase 15 · 94 tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/sqlxml" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(108,99,255,0.15)">🗄️</div>
      <h3>SQLXML</h3>
      <p>XML-native intelligence pipeline. PostgreSQL XML columns + R2 cold storage. Rust agent with AER escape protocol. AR/VR storage interface.</p>
      <span class="status status-live">Phase 8 · 158 tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Tauri-RustXML" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(0,212,170,0.15)">🔐</div>
      <h3>Tauri-RustXML</h3>
      <p>NexusCore sovereign backend. Argon2id KDF, AES-256-GCM vault, JSON-RPC 2.0 over Axum. PQC stubs (Kyber-1024).</p>
      <span class="status status-live">Phase 8 · 44 tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/SimCity" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(255,200,50,0.15)">🏙️</div>
      <h3>SimCity</h3>
      <p>Public-facing creative updater. Hourly SVG generation. Channel-1-News content pipeline. Sovereign canary reach measurement.</p>
      <span class="status status-live">Live · Creative Engine</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Channel-1-News" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(108,99,255,0.15)">📡</div>
      <h3>Channel-1-News</h3>
      <p>Sovereign news mesh + auth transport. MCP JSON-RPC 2.0 server (8 tools). Stripe paywall. Geo Z-axis routing. C-Stream beacon.</p>
      <span class="status status-dev">Phase 10 · Code Complete</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Government" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(0,212,170,0.15)">🏛️</div>
      <h3>Government</h3>
      <p>Civic intelligence screening. OFAC, OpenSanctions, ICIJ, SEC EDGAR, USPTO. IRS + FINRA + EPA + FMCSA tooling. Proprietary RiskProfile pipeline.</p>
      <span class="status status-live">Phase 6 · 150+ tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Procurement" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(255,107,107,0.15)">📋</div>
      <h3>Procurement</h3>
      <p>Sovereign procurement tracking. IPI sourcing engine. ZIP collective valuation marketplace. Business registry. Delivery hub.</p>
      <span class="status status-live">Phase 12 · 138 tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/maps" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(0,212,170,0.15)">🗺️</div>
      <h3>Maps</h3>
      <p>Sovereign terrain intelligence. Mathematical elevation/erosion/mineral derivation. No Google Maps. 3D isometric SVG tiles. MacroHarder module.</p>
      <span class="status status-live">Phase 12 · 78 tests</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Sovereign-Canary" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(108,99,255,0.15)">🕊️</div>
      <h3>Sovereign Canary</h3>
      <p>Append-only IP violation log. HMAC-SHA256 canary tokens. Mesh node registry. C-Stream receiver. DMCA lifecycle tracking.</p>
      <span class="status status-live">Phase 11 · Active</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/IP-Forensics" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(255,107,107,0.15)">🔍</div>
      <h3>IP Forensics</h3>
      <p>Autonomous IP infringement detection. GitHub, npm, PyPI, crates.io, Docker Hub, Hugging Face scanning. AST structural fingerprinting. 208 tests.</p>
      <span class="status status-live">Phase 14 · Autonomous</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/Finance-Slack-Other" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(0,212,170,0.15)">💰</div>
      <h3>Finance</h3>
      <p>Open Collective / financial notification service. Cloudflare Worker. D1 ledger. Slack webhook router. Self-hosted OC bridge.</p>
      <span class="status status-dev">Phase 10 · Code Complete</span>
    </a>
    <a class="card" href="https://github.com/Albert-lane-org/roadmaps" rel="noopener noreferrer">
      <div class="card-icon" style="background:rgba(255,200,50,0.15)">🗂️</div>
      <h3>RoadMaps</h3>
      <p>Estate navigation hub. 4-hourly estate pipeline. Business plan pipeline. Lane-SpatialFold dependency audit. Conflict resolver.</p>
      <span class="status status-live">Phase 17 · Active</span>
    </a>
  </div>
</section>

<hr class="divider">

<section id="architecture">
  <p class="section-label">Architecture</p>
  <h2>How it fits together.</h2>
  <p>Every component speaks MCP. Every request is audited. Every secret is edge-provisioned.</p>
  <div class="arch-block">
    <pre>
<span class="hl">MCP Clients</span> (Claude Code, Claude Desktop, CI/CD, agents, MacroHarder)
  ↓ stdio (local) | WebSocket (remote) | HTTP/SSE (stateless)
<span class="hl2">Lane MCP Gateway</span>     mcp.albertlane.org
  ↓ Auth (CallerContext + RBAC) · Rate limiter · Audit log
  ↓ 46 tools / 16 modules
  sqlxml → PostgreSQL · R2 · XML pipeline
  github → albert-lane-org estate (read/write/search/push)
  civic  → SOVEREIGN_DB D1 (entities, permits)
  identity → IDENTITY_DB D1 (enrollments, sessions)
  sovereign → cache_get / cache_invalidate / read
  sso    → Google · Microsoft · Apple · Amazon · Meta · GitHub OAuth 2.0
  lanevm → sandboxed typed-instruction interpreter (no eval surface)
  aer    → 1-read-2-writes invariant, D1 + R2 dual-locale
  monitoring → health / stats / tools_list
  ...and 7 more modules

<span class="hl">Froi Browser</span>        → calls lane-mcp as an MCP client
<span class="hl">MacroHarder™</span>        → consumes procurement + maps modules directly
<span class="hl">Sovereign Canary</span>    → receives IP forensics violations, mesh registry
<span class="hl">Channel-1-News</span>      → news.albertlane.org (SimCity → Cloudflare Worker)
<span class="hl">Government</span>          → GOVERNMENT_ENDPOINT/screen → RiskProfile
    </pre>
  </div>
</section>

<footer>
  <p>
    Albert Lane Digital Estate &nbsp;|&nbsp;
    <a href="https://github.com/Albert-lane-org" rel="noopener noreferrer">GitHub</a> &nbsp;|&nbsp;
    <a href="https://albertlane.net" rel="noopener noreferrer">albertlane.net</a> &nbsp;|&nbsp;
    <a href="https://github.com/Albert-lane-org/Sovereign-Canary/blob/main/violations/log.jsonl" rel="noopener noreferrer">IP Violations Log</a>
  </p>
  <p style="margin-top:0.75rem; font-size:0.75rem;">
    SEC Whistleblower No. 17684-273-411-436 &nbsp;·&nbsp;
    All IP belongs to Albert Lane per LICENSE.md &nbsp;·&nbsp;
    Edge-served by Cloudflare Workers
  </p>
</footer>

</body>
</html>`;

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Route: /health
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        worker: 'estate-portal',
        domain: 'albertlane.org',
        timestamp: new Date().toISOString(),
        sec_ref: '17684-273-411-436',
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        },
      });
    }

    // Route: /robots.txt
    if (url.pathname === '/robots.txt') {
      return new Response(
        'User-agent: *\nAllow: /\nSitemap: https://albertlane.org/sitemap.xml\n',
        { headers: { 'Content-Type': 'text/plain' } }
      );
    }

    // Route: /sitemap.xml
    if (url.pathname === '/sitemap.xml') {
      const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://albertlane.org/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>
  <url><loc>https://albertlane.org/SimCity</loc><changefreq>hourly</changefreq><priority>0.9</priority></url>
</urlset>`;
      return new Response(sitemap, {
        headers: { 'Content-Type': 'application/xml' },
      });
    }

    // Default: serve the estate portal
    return new Response(ESTATE_HTML, {
      headers: {
        'Content-Type': 'text/html; charset=UTF-8',
        'Cache-Control': 'public, max-age=300, s-maxage=600',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'X-Estate-Node': 'albertlane.org/estate-portal',
      },
    });
  },
};
