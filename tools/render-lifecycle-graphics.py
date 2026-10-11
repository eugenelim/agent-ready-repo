#!/usr/bin/env python3
"""Render the two lifecycle teaching graphics used by the operating-model guide.

Writes, next to ``guides/_shared/explanation/the-operating-model.md``:

- ``the-operating-model-overview.svg`` — four stage cards, sized to show close to
  full scale in the docs prose column.
- ``the-operating-model-full-map.svg`` — the full map: every route, step, skill,
  and decision.

The step content mirrors ``docs/architecture/lifecycle-flow.md`` and the
step-by-step list in the guide; change all three together. Run
``python3 tools/render-lifecycle-graphics.py`` after editing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "guides" / "_shared" / "explanation"

SANS = (
    "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
)
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# Dark, high-contrast palette. Every text colour clears 4.5:1 on the surface it
# sits on; arrows, connectors, and stage borders clear 3:1.
BG_TOP, BG_BOTTOM = "#0b1020", "#121a33"
SURFACE = "#161f38"
CARD = "#1b2542"
CARD_EDGE = "#2c3963"
INK = "#f1f5f9"
SOFT = "#cbd5e1"
MUTED = "#a3b1c6"
ARROW = "#8494b3"  # clears 3:1 on the brightest point of every stage gradient
GOLD_HI, GOLD_LO, GOLD_INK = "#fde68a", "#f59e0b", "#1f1300"
BORDER_OPACITY = 0.6  # stage borders use the light accent at this opacity


@dataclass(frozen=True)
class Stage:
    """One lifecycle stage: its names, colours, and icon."""

    key: str
    number: int
    name: str
    hi: str  # light accent: skill names, eyebrow, step badges, borders
    lo: str  # deep accent: gradients
    icon: str


STAGES = {
    "decide": Stage("decide", 1, "Decide what to build", "#c4b5fd", "#7c3aed", "signpost"),
    "shape": Stage("shape", 2, "Shape it", "#7dd3fc", "#2563eb", "layers"),
    "build": Stage("build", 3, "Build it", "#6ee7b7", "#059669", "code"),
    "ship": Stage("ship", 4, "Ship it", "#fda4af", "#e11d48", "flag"),
}


@dataclass
class Svg:
    """A tiny SVG writer that keeps attribute formatting in one place."""

    width: int
    height: int
    parts: list[str] = field(default_factory=list)

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(
        self,
        x: float,
        y: float,
        s: str,
        size: float = 13,
        weight: int = 400,
        fill: str = INK,
        family: str = SANS,
        anchor: str = "start",
        spacing: float = 0,
    ) -> None:
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>'
            f"{escape(s)}</text>"
        )

    def render(self) -> str:
        return "\n".join(self.parts) + "\n"


def width_of(s: str, size: float, mono: bool = False, bold: bool = False) -> float:
    """Approximate rendered width; good enough to keep text inside boxes."""
    em = 0.6 if mono else (0.58 if bold else 0.54)
    return len(s) * size * em


def defs(svg: Svg) -> None:
    """Gradients, glows, markers, and the dot grid shared by both graphics."""
    g = [
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        "</linearGradient>",
        f'<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GOLD_HI}"/><stop offset="1" stop-color="{GOLD_LO}"/>'
        "</linearGradient>",
        '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="1.5" cy="1.5" r="1.1" fill="#ffffff" fill-opacity="0.045"/></pattern>',
        '<filter id="lift" x="-10%" y="-10%" width="120%" height="140%">'
        '<feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000000" '
        'flood-opacity="0.35"/></filter>',
        '<filter id="soft" x="-5%" y="-5%" width="110%" height="130%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" '
        'flood-opacity="0.3"/></filter>',
        '<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{ARROW}"/></marker>',
    ]
    for st in STAGES.values():
        g.append(
            f'<linearGradient id="g-{st.key}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{st.hi}"/><stop offset="1" stop-color="{st.lo}"/>'
            "</linearGradient>"
        )
        g.append(
            f'<linearGradient id="col-{st.key}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{st.lo}" stop-opacity="0.30"/>'
            f'<stop offset="0.35" stop-color="{st.lo}" stop-opacity="0.08"/>'
            f'<stop offset="1" stop-color="{st.lo}" stop-opacity="0.04"/></linearGradient>'
        )
        g.append(
            f'<radialGradient id="glow-{st.key}">'
            f'<stop offset="0" stop-color="{st.lo}" stop-opacity="0.35"/>'
            f'<stop offset="1" stop-color="{st.lo}" stop-opacity="0"/></radialGradient>'
        )
        g.append(
            f'<marker id="arrow-{st.key}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{st.hi}"/>'
            "</marker>"
        )
    g.append("</defs>")
    svg.add("".join(g))


def canvas(svg: Svg, glows: list[tuple[float, float, float, str]]) -> None:
    """The dark card the graphic sits on, with soft colour glows behind stages."""
    w, h = svg.width, svg.height
    svg.add(f'<rect width="{w}" height="{h}" rx="24" fill="url(#bg)"/>')
    for cx, cy, r, key in glows:
        svg.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#glow-{key})"/>')
    svg.add(f'<rect width="{w}" height="{h}" rx="24" fill="url(#dots)"/>')
    svg.add(
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="24" fill="none" '
        'stroke="#ffffff" stroke-opacity="0.08"/>'
    )


ICONS = {
    # Drawn on a 24-unit grid centred on 0,0.
    "signpost": '<path d="M0,10 L0,-10"/><path d="M0,-7 L8,-7 L10.5,-4.5 L8,-2 L0,-2"/>'
    '<path d="M0,1 L-8,1 L-10.5,3.5 L-8,6 L0,6"/>',
    "layers": '<path d="M0,-8 L9,-3.5 L0,1 L-9,-3.5 Z"/><path d="M-9,1 L0,5.5 L9,1"/>'
    '<path d="M-9,5 L0,9.5 L9,5"/>',
    "code": '<path d="M-4,-6 L-10,0 L-4,6"/><path d="M4,-6 L10,0 L4,6"/><path d="M2,-9 L-2,9"/>',
    "flag": '<path d="M-6,10 L-6,-10"/>'
    '<path d="M-6,-9 C-2,-11 2,-7 7,-9 L7,1 C2,3 -2,-1 -6,1"/>',
}


def icon(svg: Svg, cx: float, cy: float, r: float, st: Stage) -> None:
    """A stage icon: white line art on the stage gradient."""
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#g-{st.key})" filter="url(#soft)"/>')
    svg.add(
        f'<g transform="translate({cx},{cy}) scale({r / 12:.3f})" fill="none" stroke="#ffffff" '
        f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ICONS[st.icon]}</g>'
    )


def code_badge(svg: Svg, x: float, cy: float, code: str) -> float:
    """A dark gate-code pill with gold text. Returns its width."""
    bw = 12 + 7.2 * len(code)
    svg.add(f'<rect x="{x:.1f}" y="{cy - 8.5:.1f}" width="{bw:.1f}" height="17" rx="8.5" '
            'fill="#1c1917"/>')
    svg.text(x + bw / 2, cy + 4, code, size=10.5, weight=700, fill="#fcd34d", anchor="middle")
    return bw


def gold_tag(svg: Svg, x: float, y: float, w: float, label: str, code: str | None = None,
             h: float = 30, size: float = 12.5) -> float:
    """A decision: gold, pointed ends, optional gate-code badge. Returns bottom y."""
    p = 11
    pts = (f"{x},{y + h / 2} {x + p},{y} {x + w - p},{y} {x + w},{y + h / 2} "
           f"{x + w - p},{y + h} {x + p},{y + h}")
    svg.add(f'<polygon points="{pts}" fill="url(#gold)" filter="url(#soft)"/>')
    if code:
        tx = x + p + 5
        tx += code_badge(svg, tx, y + h / 2, code) + 7
        svg.text(tx, y + h / 2 + 4.5, label, size=size, weight=700, fill=GOLD_INK)
    else:
        svg.text(x + w / 2, y + h / 2 + 4.5, label, size=size, weight=700, fill=GOLD_INK,
                 anchor="middle")
    return y + h


def auto_tag(svg: Svg, x: float, y: float, w: float, label: str, code: str) -> float:
    """A decision that usually passes without you: outline only."""
    h, p = 26, 10
    pts = (f"{x},{y + h / 2} {x + p},{y} {x + w - p},{y} {x + w},{y + h / 2} "
           f"{x + w - p},{y + h} {x + p},{y + h}")
    svg.add(f'<polygon points="{pts}" fill="none" stroke="#fcd34d" stroke-width="1.3" '
            'stroke-dasharray="4 3"/>')
    svg.text(x + p + 6, y + 17.5, code, size=10.5, weight=700, fill="#fcd34d")
    svg.text(x + p + 12 + 7.2 * len(code), y + 17.5, label, size=11.5, fill="#fde68a")
    return y + h


def stage_frame(svg: Svg, x: float, y: float, w: float, h: float, st: Stage, rx: int) -> None:
    """A stage panel: surface, accent wash, and a light-accent border."""
    dash = ' stroke-dasharray="7 6"' if st.key == "decide" else ""
    svg.add(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h:.0f}" rx="{rx}" '
            f'fill="{SURFACE}" filter="url(#lift)"/>')
    svg.add(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h:.0f}" rx="{rx}" '
            f'fill="url(#col-{st.key})" stroke="{st.hi}" stroke-opacity="{BORDER_OPACITY}" '
            f'stroke-width="1.4"{dash}/>')


def chevron(svg: Svg, cx: float, cy: float, half: float = 9) -> None:
    """A reading-order chevron between stages."""
    svg.add(f'<path d="M{cx - 5:.1f},{cy - half} L{cx + 4:.1f},{cy} L{cx - 5:.1f},{cy + half}" '
            f'fill="none" stroke="{SOFT}" stroke-width="2.5" stroke-linecap="round" '
            'stroke-linejoin="round"/>')


# ---------------------------------------------------------------------------
# Overview: four stage cards at prose-column size
# ---------------------------------------------------------------------------

OVERVIEW = [
    ("decide", ["Nobody has decided", "what's worth building", "yet. Optional."],
     ["desk-research", "product-strategy"], "You pick the outcome", None),
    ("shape", ["You know the outcome", "you want, but not yet", "the bet to build."],
     ["product-engineering", "experience-design", "architect", "contracts"],
     "You commit to build", "G3"),
    ("build", ["The work is clear", "enough to write down.", "Bug fixes start here."],
     ["core"], "You merge", "G4"),
    ("ship", ["A merged change", "needs to reach", "production safely."],
     ["release-engineering"], "You ship it", "G5"),
]

# Where architecture work meets each stage, in stage order: a label and the
# skill that runs or offers it there. Ship it has none, so its column is empty.
OVERVIEW_ARCHITECTURE: list[tuple[list[str], str]] = [
    (["Assess the area", "the work touches"], "architect-assess"),
    (["Design and revise", "the capabilities"], "architect-design"),
    (["Fold the design", "into the map"], "close-work"),
]


def render_overview() -> str:
    """Four stage cards, read left to right, each ending on its decision."""
    w_, h_ = 760, 634
    svg = Svg(w_, h_)
    svg.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_} {h_}" width="{w_}" '
            f'height="{h_}" role="img" aria-labelledby="ot od">')
    svg.add('<title id="ot">From idea to production in four stages</title>')
    svg.add('<desc id="od">Four stages, left to right. Decide what to build is optional and ends '
            'when you pick the outcome. Shape it ends when you commit to build. Build it ends '
            'when you merge. Ship it ends when you ship it to production. Below the stages, '
            'architecture work by stage. Before any work, once per repository, '
            'architect-assess maps what exists and adapt-to-project or init-project writes '
            'reference.md, which every plan follows. Then: assess the area the work touches, '
            'design and revise the capabilities with architect-design, and after the merge '
            'close-work offers to fold the design into the current-state map.</desc>')
    defs(svg)
    canvas(svg, [(110, 300, 190, "decide"), (290, 120, 200, "shape"),
                 (470, 330, 190, "build"), (650, 140, 190, "ship")])
    svg.text(28, 44, "From idea to production in four stages", size=21, weight=750)
    svg.text(28, 68, "Start at the stage your work is in. The gold, pointed tags are where you "
             "decide.", size=13.5, fill=SOFT)

    m, gap = 28, 14
    cw = (w_ - 2 * m - 3 * gap) / 4
    top, bot = 92, 442
    for i, (key, when, packs, end, code) in enumerate(OVERVIEW):
        st = STAGES[key]
        x = m + i * (cw + gap)
        stage_frame(svg, x, top, cw, bot - top, st, 16)
        icon(svg, x + 32, top + 34, 18, st)
        svg.text(x + 16, top + 80, f"STAGE {st.number}", size=10.5, weight=700, fill=st.hi,
                 spacing=1.6)
        name_lines = ["Decide what", "to build"] if key == "decide" else [st.name]
        for j, ln in enumerate(name_lines):
            svg.text(x + 16, top + 102 + j * 21, ln, size=18, weight=750)
        y = top + 102 + 21 * len(name_lines) + 8
        svg.text(x + 16, y, "Start here when", size=11, weight=600, fill=MUTED)
        for j, ln in enumerate(when):
            svg.text(x + 16, y + 18 + j * 17, ln, size=12.5, fill=SOFT)
        y += 18 + 17 * len(when) + 12
        for j, p in enumerate(packs):
            svg.text(x + 16, y + j * 16, p, size=11, family=MONO, fill=st.hi)
        svg.text(x + 16, bot - 60, "ENDS WHEN", size=10, weight=700, fill=MUTED, spacing=1.4)
        if code:
            code_badge(svg, x + 16 + 90, bot - 63.5, code)  # clears the spaced label
        gold_tag(svg, x + 6, bot - 50, cw - 12, end, None, h=36, size=11.5)
    for i in range(3):
        chevron(svg, m + (i + 1) * (cw + gap) - gap / 2, top + 34, 8)

    ay = bot + 14
    svg.add(f'<rect x="{m}" y="{ay}" width="{w_ - 2 * m}" height="{h_ - 26 - ay}" rx="14" '
            f'fill="{SURFACE}" fill-opacity="0.85" stroke="#ffffff" stroke-opacity="0.08"/>')
    svg.text(m + 16, ay + 22, "ARCHITECTURE, STAGE BY STAGE", size=10, weight=700,
             fill=MUTED, spacing=1.4)
    svg.text(m + 16, ay + 42, "Before any work, once per repository: architect-assess maps "
             "what exists,", size=12.5, fill=SOFT)
    svg.text(m + 16, ay + 60, "and adapt-to-project or init-project writes reference.md, "
             "which every plan follows.", size=12.5, fill=SOFT)
    for i, (label, name) in enumerate(OVERVIEW_ARCHITECTURE):
        st = list(STAGES.values())[i]
        x, y = m + i * (cw + gap) + 8, ay + 74
        svg.add(f'<rect x="{x:.1f}" y="{y}" width="{cw - 16:.1f}" height="62" rx="9" '
                f'fill="{CARD}" stroke="{st.hi}" stroke-opacity="0.8" stroke-dasharray="5 4"/>')
        for j, ln in enumerate(label):
            svg.text(x + 12, y + 18 + j * 16, ln, size=12, weight=650)
        svg.text(x + 12, y + 52, name, size=11, family=MONO, fill=st.hi)
    svg.add("</svg>")
    return svg.render()


# ---------------------------------------------------------------------------
# Full map: every route, step, skill, and decision
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """A step card. ``skills`` are real skill names and render in monospace."""

    title: str | list[str]
    skills: list[str] = field(default_factory=list)
    note: str | list[str] | None = None
    num: int | None = None
    dashed: bool = False


@dataclass
class Gate:
    """A decision inside a column."""

    label: str
    code: str | None = None
    auto: bool = False


@dataclass
class Loop:
    """A return to an earlier step: repeat until the condition holds."""

    label: list[str]
    back: int  # how many items above this one the return arrow points to


Item = Step | Gate | Loop


def _lines(v: str | list[str] | None) -> list[str]:
    return [] if v is None else (v if isinstance(v, list) else [v])


def step_height(s: Step) -> float:
    """Card height from its title, note, and skill lines."""
    return (18 + 18 * len(_lines(s.title)) + 16 * len(_lines(s.note)) + 16 * len(s.skills)
            + (2 if s.skills else -4))


def item_height(it: Item) -> float:
    if isinstance(it, Loop):
        return 14 + 15 * len(it.label)
    if isinstance(it, Gate):
        return 26 if it.auto else 30
    return step_height(it)


def draw_step(svg: Svg, x: float, y: float, w: float, s: Step, st: Stage) -> float:
    """Draw one step card. Returns its bottom y."""
    h = step_height(s)
    edge = (f'stroke="{st.hi}" stroke-opacity="0.8" stroke-dasharray="5 4"' if s.dashed
            else f'stroke="{CARD_EDGE}"')
    svg.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" '
            f'fill="{CARD}" {edge}/>')
    if not s.dashed:
        svg.add(f'<rect x="{x:.1f}" y="{y + 8:.1f}" width="3" height="{h - 16:.1f}" rx="1.5" '
                f'fill="url(#g-{st.key})"/>')
    tx = x + 14
    if s.num is not None:
        svg.add(f'<circle cx="{x + 22:.1f}" cy="{y + 20:.1f}" r="9" fill="{st.hi}"/>')
        svg.text(x + 22, y + 24, str(s.num), size=11, weight=800, fill="#0b1020",
                 anchor="middle")
        tx = x + 38
    title = _lines(s.title)
    for i, ln in enumerate(title):
        svg.text(tx, y + 25 + i * 18, ln, size=13.5, weight=650)
    yy = y + 25 + 18 * len(title)
    for ln in _lines(s.note):
        svg.text(x + 14, yy + 1, ln, size=11.5, fill=MUTED)
        yy += 16
    for i, sk in enumerate(s.skills):
        svg.text(x + 14, yy + 2 + i * 16, sk, size=11, family=MONO, fill=st.hi)
    return y + h


def draw_loop(svg: Svg, x: float, y: float, w: float, lp: Loop, target_mid: float,
              st: Stage) -> float:
    """A dashed note with a return arrow to an earlier step's left edge. Returns bottom y."""
    h = item_height(lp)
    svg.add(f'<rect x="{x + 10:.1f}" y="{y:.1f}" width="{w - 20:.1f}" height="{h:.1f}" '
            f'rx="{h / 2:.1f}" fill="none" stroke="{st.hi}" stroke-width="1.3" '
            'stroke-dasharray="4 3"/>')
    for i, ln in enumerate(lp.label):
        svg.text(x + w / 2, y + 18 + i * 15, ln, size=11.5, fill=st.hi, anchor="middle")
    mid = y + h / 2
    svg.add(f'<path d="M{x + 10:.1f},{mid:.1f} C{x - 16:.1f},{mid:.1f} {x - 16:.1f},'
            f'{target_mid:.1f} {x - 2:.1f},{target_mid:.1f}" fill="none" stroke="{st.hi}" '
            f'stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#arrow-{st.key})"/>')
    return y + h


LOOP_EXIT = 34  # the connector after a loop is taller, to carry its "once settled" label


def connector_gap(prev: Item) -> float:
    """Vertical space between an item and the one before it."""
    return LOOP_EXIT if isinstance(prev, Loop) else 15


def draw_column(svg: Svg, x: float, y: float, w: float, items: list[Item],
                st: Stage) -> float:
    """Draw steps and decisions top to bottom with arrows between. Returns bottom y."""
    mids: list[float] = []
    for i, it in enumerate(items):
        if i:
            g = connector_gap(items[i - 1])
            svg.add(f'<line x1="{x + w / 2:.1f}" y1="{y + 1:.1f}" x2="{x + w / 2:.1f}" '
                    f'y2="{y + g - 2:.1f}" stroke="{ARROW}" stroke-width="1.6" '
                    'marker-end="url(#arrow)"/>')
            if isinstance(items[i - 1], Loop):
                svg.text(x + w / 2 + 8, y + g / 2 + 4, "once settled", size=11, fill=st.hi)
            y += g
        mids.append(y + item_height(it) / 2)
        if isinstance(it, Loop):
            y = draw_loop(svg, x, y, w, it, mids[i - it.back], st)
        elif isinstance(it, Gate):
            y = (auto_tag(svg, x, y, w, it.label, it.code or "") if it.auto
                 else gold_tag(svg, x, y, w, it.label, it.code))
        else:
            y = draw_step(svg, x, y, w, it, st)
    return y


def column_height(items: list[Item]) -> float:
    return sum(item_height(i) for i in items) + sum(connector_gap(p) for p in items[:-1])


DECIDE: list[Item] = [
    Step("Find out what's true", ["desk-research"]),
    Step(["Assess the area the", "work touches", "(optional)"], ["architect-assess"],
         dashed=True),
    Step("Make the strategic call", ["write-prfaq", "run-okr-cascade", "define-ux-strategy"]),
]
SHORT: list[Item] = [
    Step("Frame the intent", ["frame-intent"]), Gate("Approve the intent", "G0"),
    Step(["Test the riskiest", "assumption"], ["de-risk-intent"]),
    Step(["Shape the architecture", "(optional)"], ["architect-design"],
         note=["Offered while framing.", "Take it before you cut",
               "the work. If it changes", "the capabilities, take",
               "the longer route."],
         dashed=True),
    Step(["Break it into", "buildable pieces"], ["decompose-intent"]),
]
LONGER: list[Item] = [
    Step("Frame the situation", ["frame-situation"]),
    Step("Find the opportunities", ["identify-opportunities"]),
    Step("Generate options", ["diverge-solutions"]),
    Step(["Test the riskiest", "assumption"], ["de-risk-intent"]),
    Step("Place a bet", ["place-bet"]),
    Step(["Map the capabilities", "and a build order"], ["map-capabilities"]),
    Step(["Design against the", "capabilities (optional)"], ["architect-design"],
         note=["offered once the build", "order is set"], dashed=True),
    Loop(["Not settled? Revise", "the capabilities and", "design again"], back=2),
    Step(["Design the subsystems", "that earn a doc"], ["architect-design", "architect-review"],
         dashed=True),
]
SUPERVISED: list[Item] = [
    Step("Frame the intent", ["frame-intent"]), Gate("Approve the intent", "G0"),
    Step("De-risk and explore", ["de-risk-intent", "explore-options"]),
    Gate("Usually automatic", "G1", auto=True),
    Step("Ground the domain", ["frame-domain"]), Gate("Set the MVP", "G1.5"),
    Step(["Design, system, and", "contracts in parallel"],
         ["journey-mapping", "user-flow", "architect-design", "architect-diagram",
          "api-contract"],
         note=["then a threat and", "reliability review"]),
    Gate("Approve the brief", "G2"),
    Step(["Break it into", "buildable pieces"], ["decompose-intent"]),
]
BUILD: list[Item] = [
    Step("Route the work", ["work-intake"], note="picks a spec, a brief, or an intent", num=1),
    Step("Write the spec and plan", ["new-spec"],
         note=["follows reference.md and", "reads the design as context"], num=2),
    Gate("Approve spec and plan"),
    Step("Build and check", ["work-loop"], note="lint, types, tests, three reviews", num=3),
]
SHIP: list[Item] = [
    Step(["Set an error budget", "(optional)"], ["define-slo"], dashed=True),
    Step(["Deploy somewhere", "safe and test it"], ["release-loop"],
         note="end-to-end tests, telemetry"),
    Step(["Read the readiness", "record"], note="operations, security, cost"),
]

# Before any work, once per repository: what each document is, who writes it,
# and what it does.
FOUNDATION = [
    ("The current-state map", "architect-assess",
     "maps what exists. close-work offers to fold each shipped design into it."),
    ("The engineering patterns in reference.md", "adapt-to-project or init-project",
     "write it. architect-design offers this when none exists."),
]

# Who runs each stage and who usually makes its call. The roles come from the
# "For:" line of each stage's path in guides/README.md.
WHO = {
    "decide": ("You run each skill yourself", "Product lead or strategist"),
    "shape": ("discovery-lead, on the supervised loop", "Product manager"),
    "build": ("the work-loop supervisor", "Engineer or tech lead"),
    "ship": ("release-lead", "Delivery lead or SRE"),
}


def render_full() -> str:
    """Every route, step, skill, and decision across the four stages."""
    w_ = 1500
    m, gap = 36, 40
    widths = {"decide": 212, "shape": 576, "build": 282, "ship": 238}
    xs: dict[str, float] = {}
    x: float = m
    for k, w in widths.items():
        xs[k] = x
        x += w + gap
    found_y, found_h = 140, 108
    top, head = found_y + found_h + 24, 128
    body = top + head + 16
    route_top = body + 58
    body_end = max(route_top + column_height(SUPERVISED), route_top + column_height(LONGER),
                   body + column_height(BUILD) + 220, body + column_height(DECIDE))
    bot = body_end + 200 + 104  # room for converging lines, who-runs-it, and the ending
    h_ = int(bot + 150)
    svg = Svg(w_, h_)
    svg.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_} {h_}" width="{w_}" '
            f'height="{h_}" role="img" aria-labelledby="ft fd">')
    svg.add('<title id="ft">The full map: how one piece of work moves from idea to production'
            '</title>')
    svg.add('<desc id="fd">Four stages, left to right, with every route, step, skill, and '
            'decision. Above the stages, the two documents set up once per repository before any '
            'work: the current-state map and reference.md. Below them, the packs used at any '
            'stage. The guide page lists the same flow under "The same flow, step by step" '
            'and the architecture timeline under "Where architecture comes in".</desc>')
    defs(svg)
    canvas(svg, [(140, 560, 260, "decide"), (560, 340, 380, "shape"),
                 (1060, 600, 300, "build"), (1350, 340, 260, "ship")])
    svg.text(m, 56, "How one piece of work moves from idea to production", size=28, weight=750)
    svg.text(m, 86, "Read left to right and start at the stage your work is in. The gold, "
             "pointed tags are where you decide.", size=15, fill=SOFT)
    # Legend up front, so dashes and the return curve are explained before they appear.
    ly = 118
    svg.add(f'<rect x="{m}" y="{ly - 13}" width="34" height="18" rx="5" fill="none" '
            f'stroke="{SOFT}" stroke-dasharray="4 3"/>')
    svg.text(m + 44, ly, "Dashed: optional, a shortcut, or usually automatic", size=13,
             fill=SOFT)
    lx = m + 390
    svg.add(f'<path d="M{lx},{ly - 4} H{lx + 36}" stroke="{STAGES["ship"].hi}" '
            'stroke-width="1.8" stroke-dasharray="6 4" marker-end="url(#arrow-ship)"/>')
    svg.text(lx + 46, ly, "A deployed failure goes back to the build loop", size=13, fill=SOFT)
    svg.text(w_ - m, ly, "Codes like G3 are what the agents print when they stop for you.",
             size=13, fill=MUTED, anchor="end")

    svg.add(f'<rect x="{m}" y="{found_y}" width="{w_ - 2 * m}" height="{found_h}" rx="16" '
            f'fill="{SURFACE}" fill-opacity="0.85" stroke="#ffffff" stroke-opacity="0.08"/>')
    svg.text(m + 20, found_y + 28, "BEFORE ANY WORK", size=11, weight=700, fill=MUTED,
             spacing=1.6)
    svg.text(m + 172, found_y + 28, "Once per repository, then kept current. The architect "
             "skills ground their work in these, and every plan follows reference.md.",
             size=12.5, fill=SOFT)
    fw = (w_ - 2 * m - 40 - 12) / 2
    for i, (title, maker, does) in enumerate(FOUNDATION):
        fx, fy = m + 20 + i * (fw + 12), found_y + 40
        svg.add(f'<rect x="{fx:.1f}" y="{fy}" width="{fw:.1f}" height="56" rx="10" '
                f'fill="{CARD}" stroke="{CARD_EDGE}"/>')
        svg.text(fx + 16, fy + 22, title, size=13.5, weight=650)
        tx = fx + 16
        for j, name in enumerate(maker.split(" or ")):
            if j:
                svg.text(tx + 6, fy + 42, "or", size=12, fill=MUTED)
                tx += 26
            svg.text(tx, fy + 42, name, size=11, family=MONO, fill=INK, weight=600)
            tx += width_of(name, 11, mono=True)
        svg.text(tx + 10, fy + 42, does, size=12, fill=MUTED)

    starts = {
        "decide": ["Nobody has decided what's", "worth building. Optional."],
        "shape": ["You know the outcome you want, but not yet the bet to build."],
        "build": ["The work is clear enough to", "write down. Bug fixes start here."],
        "ship": ["A merged change needs to", "reach production safely."],
    }
    for k, st in STAGES.items():
        x, w = xs[k], widths[k]
        stage_frame(svg, x, top, w, bot - top, st, 18)
        icon(svg, x + 38, top + 38, 20, st)
        svg.text(x + 68, top + 31, f"STAGE {st.number}", size=11, weight=700, fill=st.hi,
                 spacing=1.8)
        name_lines = ["Decide what", "to build"] if k == "decide" else [st.name]
        for j, ln in enumerate(name_lines):
            svg.text(x + 68, top + 53 + j * 22, ln, size=20, weight=750)
        sy = top + (100 if k == "decide" else 86)
        for j, ln in enumerate(starts[k]):
            svg.text(x + 18, sy + j * 17, ln, size=12.5, fill=SOFT)

    for k in ("decide", "shape", "build"):
        gx = xs[k] + widths[k] + gap / 2
        chevron(svg, gx, top + 38)
        chevron(svg, gx, bot - 41)

    def ending(k: str, passes: str, label: str, code: str | None) -> None:
        x, w = xs[k], widths[k]
        run_by, decider = WHO[k]
        y0 = bot - 214
        svg.add(f'<line x1="{x + 18}" y1="{y0:.1f}" x2="{x + w - 18}" y2="{y0:.1f}" '
                'stroke="#ffffff" stroke-opacity="0.08"/>')
        svg.text(x + 18, y0 + 24, "RUN BY", size=10, weight=700, fill=MUTED, spacing=1.4)
        svg.text(x + 18, y0 + 42, run_by, size=12.5, fill=SOFT)
        svg.text(x + 18, y0 + 68, "USUALLY DECIDED BY", size=10, weight=700, fill=MUTED,
                 spacing=1.4)
        svg.text(x + 18, y0 + 86, decider, size=12.5, fill=SOFT)
        svg.text(x + 18, bot - 90, passes, size=12.5, weight=600, fill=INK)
        svg.text(x + 18, bot - 66, "THIS STAGE ENDS WHEN", size=10, weight=700, fill=MUTED,
                 spacing=1.4)
        gold_tag(svg, x + 14, bot - 56, w - 28, label, code, h=32, size=13)

    draw_column(svg, xs["decide"] + 14, body, widths["decide"] - 28, DECIDE, STAGES["decide"])
    ending("decide", "Passes on: an outcome", "You pick the outcome", None)

    st = STAGES["shape"]
    sw, sg = 176, 12
    rx = [xs["shape"] + 18 + i * (sw + sg) for i in range(3)]
    routes = [("Short route", "The default, about 3 hours"),
              ("Longer route", "When the problem is unclear"),
              ("Supervised loop", "For a new product area")]
    for i, (nm, sub) in enumerate(routes):
        if i == 0:
            svg.add(f'<rect x="{rx[i]}" y="{body}" width="{sw}" height="44" rx="10" '
                    'fill="#1d4ed8"/>')
            ink, sub_ink = "#ffffff", "#ffffff"
        else:
            svg.add(f'<rect x="{rx[i]}" y="{body}" width="{sw}" height="44" rx="10" fill="none" '
                    f'stroke="{st.hi}" stroke-opacity="0.6"/>')
            ink, sub_ink = st.hi, SOFT
        svg.text(rx[i] + sw / 2, body + 19, nm, size=13.5, weight=750, fill=ink, anchor="middle")
        svg.text(rx[i] + sw / 2, body + 35, sub, size=11.5, fill=sub_ink, anchor="middle")
    for i, items in enumerate((SHORT, LONGER, SUPERVISED)):
        end_y = draw_column(svg, rx[i], route_top, sw, items, st)
        cx = rx[i] + sw / 2
        dash = "" if i == 2 else ' stroke-dasharray="5 5"'  # the two bypasses are dashed
        svg.add(f'<line x1="{cx:.1f}" y1="{end_y + 3:.1f}" x2="{cx:.1f}" y2="{bot - 222:.1f}" '
                f'stroke="{st.hi}" stroke-width="1.6"{dash} marker-end="url(#arrow-shape)"/>')
    ending("shape", "Passes on: buildable pieces, or a capability map", "You commit to build",
           "G3")

    st = STAGES["build"]
    bx, bw = xs["build"] + 14, widths["build"] - 28
    by = draw_column(svg, bx, body, bw, BUILD, st)
    work_loop_mid = by - item_height(BUILD[-1]) / 2
    svg.add(f'<rect x="{bx}" y="{by + 22:.1f}" width="{bw}" height="58" rx="10" fill="none" '
            f'stroke="{SOFT}" stroke-opacity="0.6" stroke-dasharray="5 4"/>')
    svg.text(bx + 14, by + 45, "Small, low-risk change?", size=12.5, weight=650)
    svg.text(bx + 14, by + 64, "It skips the spec and goes to step 3.", size=12, fill=SOFT)
    draw_step(svg, bx, by + 96, bw,
              Step(["After you merge (G4): fold", "the design into the map"],
                   ["close-work", "architect-diagram"], dashed=True), st)
    ending("build", "Passes on: a merged change", "You merge", "G4")

    st = STAGES["ship"]
    sx, sw2 = xs["ship"] + 14, widths["ship"] - 28
    sy = draw_column(svg, sx, body, sw2, SHIP, st)
    svg.text(sx + sw2 / 2, sy + 30, "Nothing reaches production", size=12, fill=SOFT,
             anchor="middle")
    svg.text(sx + sw2 / 2, sy + 47, "until you say so.", size=12, fill=SOFT, anchor="middle")
    ending("ship", "Ends in: production", "You ship it", "G5")

    deploy_y = body + item_height(SHIP[0]) + 15 + 34
    svg.add(f'<path d="M{sx},{deploy_y:.1f} C{sx - 30},{deploy_y:.1f} {bx + bw + 30},'
            f'{work_loop_mid:.1f} {bx + bw + 2},{work_loop_mid:.1f}" fill="none" '
            f'stroke="{st.hi}" stroke-width="1.8" stroke-dasharray="6 4" '
            'marker-end="url(#arrow-ship)"/>')
    fx, fy = (sx + bx + bw) / 2, (deploy_y + work_loop_mid) / 2
    svg.add(f'<rect x="{fx - 19:.1f}" y="{fy - 14:.1f}" width="38" height="30" rx="6" '
            f'fill="{BG_BOTTOM}"/>')
    svg.text(fx, fy - 2, "if it", size=11, fill=st.hi, anchor="middle")
    svg.text(fx, fy + 11, "fails", size=11, fill=st.hi, anchor="middle")

    ay = bot + 26
    svg.add(f'<rect x="{m}" y="{ay}" width="{w_ - 2 * m}" height="96" rx="16" fill="{SURFACE}" '
            'fill-opacity="0.85" stroke="#ffffff" stroke-opacity="0.08"/>')
    svg.text(m + 20, ay + 28, "USED AT ANY STAGE", size=11, weight=700, fill=MUTED, spacing=1.6)
    chips = [("code-intelligence", "what the code really does"),
             ("frontend-engineering", "UI work"), ("iac-terraform", "infrastructure plans"),
             ("atlassian · github · linear · figma", "your team's tools"),
             ("converters", "files into text"), ("governance-extras", "write a decision down"),
             ("product-documentation", "document what shipped")]
    nat = [max(width_of(n, 11.5, mono=True), width_of(d, 12)) + 28 for n, d in chips]
    extra = (w_ - 2 * m - 40 - 10 * (len(chips) - 1) - sum(nat)) / len(chips)
    cx = m + 20
    for (n, d), nw in zip(chips, nat, strict=True):
        w = nw + extra
        svg.add(f'<rect x="{cx:.1f}" y="{ay + 40}" width="{w:.1f}" height="44" rx="10" '
                f'fill="{CARD}" stroke="{CARD_EDGE}"/>')
        svg.text(cx + 14, ay + 58, n, size=11.5, family=MONO, fill=INK, weight=600)
        svg.text(cx + 14, ay + 75, d, size=12, fill=MUTED)
        cx += w + 10
    svg.add("</svg>")
    return svg.render()


def main() -> None:
    """Write both graphics and report where they went."""
    for name, body in (("the-operating-model-overview.svg", render_overview()),
                       ("the-operating-model-full-map.svg", render_full())):
        path = OUT_DIR / name
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
