# Aesthetic direction: agent-ready-repo tech docs site (`docs-site/`)

Authored via the `creative-direction` skill for the docs-site design refresh.
Grounded reference artifact: an external reference docs site supplied
in-session (deliberately not named in-tree) — studied for its structural
philosophy (optical-size display serif over a working sans, eyebrow-labeled
navigation sections, hairline rules as the only chrome, generous
whitespace), **not** copied for its surface treatment (its warm
paper/terracotta palette is explicitly replaced per user direction). Values (palette, type scale, spacing) are derived in the
spec's LLD, which plays the `design-system` role for this surface.

## Surface

**Target surface:** responsive-web
**Surface genre:** documentation (Diátaxis: tutorials, how-to, reference, explanation)

## Audience map (JTBD, ranked)

1. **Adopting engineer** (primary) — "When my team runs the AI operating
   model, I want to find the exact how-to or reference page for the task in
   front of me, so that I can execute without re-deriving the process."
   Cognitive mode: task-focused scanning; arrives mid-task from search or a
   skill pointer.
2. **Engineering leader / platform owner** (secondary) — "When I evaluate
   whether to standardize my org on this repo, I want the docs to signal
   maturity and rigor, so that I can defend the choice in front of my
   engineers." Cognitive mode: credibility skim — judges the docs by feel
   before reading a word.
3. **Contributor / maintainer** (tertiary) — deep linear reading of
   explanation and reference pages; long sessions, needs sustained reading
   comfort.

## Named goals (ranked)

1. **Instrument-grade clarity** (dominant)
2. **Editorial gravitas**
3. **Calibrated engineering cool**
4. **Quiet enterprise polish**

## What each goal means

- **Instrument-grade clarity** — means: hierarchy unambiguous at every zoom
  level; navigation and prose read like a well-labeled instrument panel —
  the reader always knows where they are and what a link promises. Violated
  by: equal-weight link walls, decorative section chrome, ambiguous
  landmarks, marketing inflection inside task pages.
  - *Persona:* adopting engineer (mid-task scanning).
  - *Precedent:* a leading payments platform's developer docs —
    zero-decoration precision and reference density (leave: their brand
    palette); a developer-focused issue tracker's docs — whitespace as the
    only section separator, no `<hr>` chrome. (Precedents anonymized per
    the repo privacy rule; named in-session.)
  - *Standards:* Nielsen information scent; Hick's law at navigation
    decision points; Diátaxis quadrant separation already in the IA.
  - *Platform conventions:* responsive-web — sidebar + on-page ToC patterns
    readers already hold from every major docs property.
- **Editorial gravitas** — means: the page carries authority through
  typography — a display serif with real optical sizing for headings,
  hairline rules under section heads, unhurried margins. Violated by: serif
  at body/UI sizes, cramped vertical rhythm, decoration standing in for
  typographic structure.
  - *Persona:* engineering leader (credibility skim).
  - *Precedent:* the grounded reference's serif-over-sans structure (take:
    optical-size display serif for h1/h2 + wordmark, eyebrow labels,
    hairline rules; leave: warm paper ground, terracotta accent, soft
    display axes); Bringhurst on measure and leading for long-form reading.
  - *Standards:* Hemingway's iceberg — trust built through precision, not
    self-description.
  - *Platform conventions:* variable-font optical sizing (`opsz`) is a web
    capability; use it rather than faux display weights.
- **Calibrated engineering cool** — means: the chromatic register is cool,
  precise, and technical — reads as a calibrated instrument, not a
  campaign. One disciplined accent family against a neutral cool ground.
  Violated by: warm/organic grounds, multi-hue accent play, gradients as
  decoration, saturation that shouts.
  - *Persona:* both engineer and leader — the register both trust.
  - *Precedent:* a large enterprise design system's engineering-blue
    register (take: the cool precision; leave: its grid rigidity); the same
    issue tracker's restraint-as-persuasion (take: chromatic discipline;
    leave: dark-first default).
  - *Standards:* single-accent discipline consistent with the existing
    platform design system's one-chromatic-accent rule.
  - *Platform conventions:* light-first with a complete dark theme —
    Starlight ships a theme toggle; both modes are first-class.
- **Quiet enterprise polish** — means: completeness is the polish — both
  themes fully mapped, focus states visible, reduced motion honored, every
  state designed; nothing looks defaulted. Violated by: system-font
  fallbacks standing in for the declared type, half-themed dark mode,
  color-only signaling, contrast below AA.
  - *Persona:* engineering leader; contributor on long sessions.
  - *Precedent:* a frontend-cloud vendor's docs — exactly what's needed,
    nothing more.
  - *Standards:* WCAG 2.1 AA floor (contrast, focus visibility,
    `prefers-reduced-motion`) — the quality floor, never traded.
  - *Platform conventions:* Starlight's accessibility affordances (skip
    links, landmarks, pagefind search) are kept, restyled, never removed.

## Dominant goal for arbitration

**Dominant goal:** Instrument-grade clarity.

Resolved trade-offs:

- When **editorial gravitas** and **instrument-grade clarity** conflict on a
  type choice (e.g. serif in sidebar labels, serif body text), **clarity**
  wins — the serif is display-only (h1, h2, wordmark); all navigation, UI,
  and body text stays on the working sans.
- When **calibrated engineering cool** and **quiet enterprise polish**
  conflict on an accent value (a cooler hue that misses AA contrast on the
  ground), **polish** wins — shift the value until it clears AA; the floor
  is not negotiable.
- When **editorial gravitas** and **quiet enterprise polish** conflict on
  density (larger display margins vs. reference-page scannability),
  **polish** wins on reference/how-to pages, **gravitas** wins on landing
  and explanation pages — density follows the Diátaxis quadrant.

## Open questions

- None blocking. The dark-theme accent values must be re-derived (not
  lightness-flipped) to hold AA on the dark ground — handled in the LLD
  token derivation.
