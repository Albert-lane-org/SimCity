#!/usr/bin/env python3
"""
SimCity Creative Engine — recursive README renderer.

Each run:
  1. Reads updates/latest.json   (sanitized dispatch from RoadMaps)
  2. Reads creative-state.json   (accumulated narrative state)
  3. Advances the state          (arc stage, motif accumulation, iteration++)
  4. Writes README.md            (full creative public output)
  5. Saves creative-state.json   (persisted for next run)

The narrative arc moves through six city-building stages over time.
Design motifs accumulate and reappear. The city grows because it runs.
"""

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

UPDATE_PATH = Path('updates/latest.json')
STATE_PATH  = Path('creative-state.json')
README_PATH = Path('README.md')

# ── Narrative arc: six stages of city growth ──────────────────────────────────
ARC_STAGES = [
    {
        'name': 'Breaking Ground',
        'prose': (
            'The site is cleared. Surveyors have been through. '
            'The plan exists in blueprint form — clean lines, honest ambitions. '
            'What follows is construction.'
        ),
        'ascii': (
            '  ·  ·  ·  ·  ·  ·  ·  ·  ·  \n'
            '      [ SITE CLEARED ]        \n'
            '  ·  ·  ·  ·  ·  ·  ·  ·  ·  '
        ),
    },
    {
        'name': 'Laying Foundations',
        'prose': (
            'Foundations go in first, out of sight. '
            'Nobody photographs foundations. '
            'But everything that follows depends on how well they are poured.'
        ),
        'ascii': (
            '  ┌─────┐          ┌─────┐   \n'
            '  │ ▓▓▓ │          │ ▓▓▓ │   \n'
            '  └─────┘          └─────┘   \n'
            '       ·  ·  ·  ·  ·         '
        ),
    },
    {
        'name': 'First Structures',
        'prose': (
            'Walls appear above grade. '
            'The shape of the thing becomes visible from the street. '
            'Passersby slow down and look.'
        ),
        'ascii': (
            '  ┌──────┐        ┌──────┐   \n'
            '  │      │        │  ██  │   \n'
            '  │  ██  │        │  ██  │   \n'
            '  └──────┘        └──────┘   \n'
            '  ──────────────────────────  '
        ),
    },
    {
        'name': 'Districts Taking Shape',
        'prose': (
            'Each district has its own character. '
            'The Gateway handles traffic. The Core stores memory. '
            'The Quarters give people somewhere to be. '
            'City Hall keeps the lights on.'
        ),
        'ascii': (
            '  ┌─────┐  ┌─────┐  ┌─────┐  \n'
            '  │  G  │  │  I  │  │  S  │  \n'
            '  │  █  │  │  █  │  │  █  │  \n'
            '  └─────┘  └─────┘  └─────┘  \n'
            '  ═══════════════════════════  '
        ),
    },
    {
        'name': 'City Humming',
        'prose': (
            'The city runs. Not perfectly — cities never run perfectly. '
            'But the trains move, the pipes hold, the lights stay on. '
            'People start to rely on it.'
        ),
        'ascii': (
            '  ╔═════╗  ╔═════╗  ╔═════╗  \n'
            '  ║  G  ║  ║  I  ║  ║  S  ║  \n'
            '  ║  ▓  ║  ║  ▓  ║  ║  ▓  ║  \n'
            '  ╚═════╝  ╚═════╝  ╚═════╝  \n'
            '  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  '
        ),
    },
    {
        'name': 'Sovereign City',
        'prose': (
            'A city that runs itself. '
            'Infrastructure that serves people rather than extracting from them. '
            'Transparent where it should be. Private where it must be. '
            'Open to collaborators. Closed to adversaries.'
        ),
        'ascii': (
            '  ╔═════╗ ╔═════╗ ╔═════╗ ╔═════╗  \n'
            '  ║  G  ║ ║  I  ║ ║  S  ║ ║  C  ║  \n'
            '  ║  ▓  ║ ║  ▓  ║ ║  ▓  ║ ║  ▓  ║  \n'
            '  ╚═════╝ ╚═════╝ ╚═════╝ ╚═════╝  \n'
            '  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  \n'
            '            SOVEREIGN CITY           '
        ),
    },
]

# ── Designer roles — rotated through across iterations ────────────────────────
DESIGN_ROLES = [
    ('Interface Architects',
     'People who believe software should feel like a place you want to be in.'),
    ('Systems Typographers',
     'Designers who understand that data has a visual grammar.'),
    ('Civic UX Designers',
     "People who've worked on public-facing digital infrastructure and hated how bad it was."),
    ('Motion Designers',
     'Animation that communicates state, not just decoration.'),
    ('Design Systems Engineers',
     'People who build the tools that let everyone else move faster.'),
    ('Information Architects',
     'People who make structure visible and navigable.'),
    ('Open Source Aestheticists',
     'Designers who believe open source should look as good as proprietary.'),
    ('Interaction Designers',
     'People who think about what happens between states, not just the states themselves.'),
]

# ── Motif pool: one new motif accumulates every three iterations ───────────────
MOTIF_POOL = [
    'sovereignty as infrastructure',
    'the city that updates itself',
    'data as civic resource',
    'design as a form of governance',
    'the README as a public square',
    'every commit is a brick',
    'transparency by design, not by accident',
    'beauty is not a luxury in civic software',
    'the builder and the building are the same thing',
    'open to collaborators, closed to adversaries',
    'infrastructure that does not extract',
    'the citizen is not the product',
    'distributed trust, not distributed surveillance',
]


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {'iteration': 0, 'arc_stage': 0, 'motifs': [], 'last_signal': ''}


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def load_update() -> dict:
    if UPDATE_PATH.exists():
        try:
            return json.loads(UPDATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {'momentum': 'initializing', 'zones': [], 'aggregate': {}, 'signal': ''}


def advance_state(state: dict, update: dict) -> dict:
    """Advance narrative arc, accumulate motifs, increment iteration."""
    state = dict(state)
    state['iteration'] = state.get('iteration', 0) + 1
    iteration = state['iteration']
    momentum  = update.get('momentum', 'initializing')

    # Arc advances every 8 iterations; faster under high momentum
    boost = momentum in ('high', 'critical-path', 'accelerating')
    cadence = 4 if boost else 8
    max_stage = len(ARC_STAGES) - 1
    if iteration % cadence == 0:
        state['arc_stage'] = min(state.get('arc_stage', 0) + 1, max_stage)

    # One new motif every 3 iterations
    existing = set(state.get('motifs', []))
    available = [m for m in MOTIF_POOL if m not in existing]
    if iteration % 3 == 0 and available:
        state.setdefault('motifs', []).append(random.choice(available))

    state['last_signal'] = update.get('signal', '')
    return state


def progress_bar(pct: int, width: int = 14) -> str:
    filled = int(width * pct / 100)
    return '█' * filled + '░' * (width - filled)


def zone_table(zones: list) -> str:
    if not zones:
        return '_No zone data this cycle._\n'
    icons = {'operational': '✦', 'building': '◈', 'planned': '◇'}
    rows  = [
        '| Zone | Layer | Phase | Progress | Status |',
        '|------|-------|-------|----------|--------|',
    ]
    for z in zones:
        icon = icons.get(z.get('status', 'planned'), '·')
        rows.append(
            f"| **{z.get('zone','?')}** "
            f"| {z.get('layer','?')} "
            f"| {z.get('active_phase','?')} "
            f"| `{progress_bar(z.get('completion', 0))}` {z.get('completion',0)}% "
            f"| {icon} {z.get('status','planned')} |"
        )
    return '\n'.join(rows)


def invitation_section(iteration: int, motifs: list) -> str:
    # Rotate through designer role pairings
    start = iteration % len(DESIGN_ROLES)
    roles = (DESIGN_ROLES + DESIGN_ROLES)[start:start + 3]

    lines = [
        '## Open Invitation',
        '',
        'SimCity is the public face of a civic infrastructure project.',
        'The infrastructure is being built. The design needs to match its ambition.',
        '',
        '**We are specifically looking for:**',
        '',
    ]
    for role, desc in roles:
        lines.append(f'- **{role}** — {desc}')
    lines += [
        '',
        'This is not a job listing. It is an invitation to be present at the start',
        'of something that has not been built before — a sovereign, open, civic-first',
        'digital infrastructure designed to replace broken public systems with something',
        'that actually works for the people using it.',
        '',
        '**Contact:** `lane.albert@pm.me`',
        '',
    ]
    if motifs:
        lines += [
            '---',
            '',
            '*Design motifs in current rotation:*',
            '',
        ]
        for m in motifs[-5:]:
            lines.append(f'> *"{m}"*')
        lines.append('')
    return '\n'.join(lines)


def render(update: dict, state: dict) -> str:
    now       = datetime.now(timezone.utc)
    ts        = now.strftime('%Y-%m-%d %H:%M UTC')
    arc       = ARC_STAGES[state.get('arc_stage', 0)]
    iteration = state.get('iteration', 1)
    motifs    = state.get('motifs', [])
    agg       = update.get('aggregate', {})
    zones     = update.get('zones', [])
    momentum  = update.get('momentum', 'initializing')
    signal    = update.get('signal', 'Something is being built here.')

    momentum_label = {
        'initializing':  '○ Initializing',
        'steady':        '● Steady',
        'accelerating':  '● Accelerating',
        'high':          '● High Velocity',
        'critical-path': '● Critical Path',
    }.get(momentum, momentum)

    return dedent(f"""\
        <!--
          Authored: Albert Lane | Rendered: Claude Sonnet 4.6 | {ts}
          Auto-generated every hour. Direct edits will be overwritten.
          No proprietary implementation details are present in this file.
        -->

        # SimCity

        > *{signal}*

        **{arc['name']}** &nbsp;·&nbsp; Iteration {iteration} &nbsp;·&nbsp; {momentum_label}

        ---

        ## The City Right Now

        ```
        {arc['ascii']}
        ```

        {arc['prose']}

        ---

        ## Zone Status

        {zone_table(zones)}

        &nbsp;

        | Metric | Count |
        |--------|-------|
        | Zones under construction | {agg.get('zones_active', 0)} |
        | Zones operational | {agg.get('zones_operational', 0)} |
        | Phases complete | {agg.get('phases_complete', 0)} |
        | Phases in progress | {agg.get('phases_in_progress', 0)} |

        ---

        {invitation_section(iteration, motifs)}

        ---

        ## What SimCity Is

        SimCity is the public creative window into the **Albert Lane Digital Estate** —
        a sovereign, open, civic-first software stack replacing broken public and private
        infrastructure with something that actually works.

        The underlying infrastructure is private. SimCity is not.

        SimCity publishes **what is being built** — direction, character, and design
        language — without exposing implementation detail. It exists to attract
        collaborators, especially designers, who should be present from the start.

        This README updates automatically every hour. Each iteration carries forward
        the accumulated language, visual motifs, and narrative arc of all previous
        iterations. The city grows because someone is building it.

        ---

        ## System Architecture (Public Layer)

        ```
        ┌────────────────────────────────────────────────────────┐
        │              Albert Lane Digital Estate                 │
        │                                                         │
        │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │
        │  │   Gateway   │  │ Intelligence │  │  Sovereign  │  │
        │  │   District  │  │     Core     │  │   Quarters  │  │
        │  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  │
        │         └────────────────┼──────────────────┘          │
        │                     ┌────┴─────┐                        │
        │                     │ City Hall│                        │
        │                     └──────────┘                        │
        └────────────────────────────────────────────────────────┘
                          ↑ SimCity (this repo — public)
        ```

        ---

        ## How This Works

        ```
        Private infrastructure  →  sanitized dispatch  →  SimCity
           (hourly at :00)             (no secrets)        (public)
                                                              ↓
                                                    creative engine at :15
                                                              ↓
                                                    README.md rewritten
                                                              ↓
                                                    narrative arc advances
        ```

        The creative state accumulates across runs. Each cycle the engine
        reads the previous state, adds new motifs, advances the narrative,
        and renders a README that is genuinely different from the last one.

        ---

        *Last updated: {ts} &nbsp;·&nbsp; All IP belongs to Albert Lane. See [LICENSE.md](LICENSE.md).*
        *Contact: `lane.albert@pm.me`*
    """)


def main():
    update = load_update()
    state  = load_state()
    state  = advance_state(state, update)

    README_PATH.write_text(render(update, state))
    save_state(state)

    print(f'README rendered — iteration {state["iteration"]}, arc stage {state["arc_stage"]}')
    print(f'Motifs accumulated: {len(state.get("motifs", []))}')


if __name__ == '__main__':
    main()
