# Aesthetic direction: agent-ready-repo tech docs site (`docs-site/`)

> **Superseded 2026-10-15** by [`docs/design/direction/docs-site.md`](../../design/direction/docs-site.md) (the Rail line). Kept as the record of the shipped refresh.

Authored via the `creative-direction` skill for the docs-site design refresh.
Grounded reference artifact: an external reference docs site supplied
in-session (deliberately not named in-tree) — studied for its structural
philosophy (optical-size display serif over a working sans, eyebrow-labeled
navigation sections, hairline rules as the only chrome, generous
whitespace), **not** copied for its surface treatment (its warm
paper/terracotta palette is explicitly replaced per user direction). Values (palette, type scale, spacing) are derived in the
historical token derivation below, which played the `design-system` role for
this refresh. The superseding direction above owns the current surface.

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
- Route-category hues are allowed only on orientation surfaces where they help
  readers choose between kinds of work. They are redundant cues paired with
  visible labels such as Shape, Build, Investigate, and Operate; normal links,
  primary actions, active navigation, and focus treatment stay on the single
  cobalt accent.
- When **editorial gravitas** and **quiet enterprise polish** conflict on
  density (larger display margins vs. reference-page scannability),
  **polish** wins on reference/how-to pages, **gravitas** wins on landing
  and explanation pages — density follows the Diátaxis quadrant.

## Open questions

- None blocking. The dark-theme accent values must be re-derived (not
  lightness-flipped) to hold AA on the dark ground — handled in the LLD
  token derivation.

## Historical token derivation (2026-08-05)

Playing the `design-system` role for this surface, from the four named goals.
Two-tier: `--doc-*` primitives → `--sl-*` (Starlight semantic slots).

**Type.** Display serif: **Source Serif 4 Variable** (`opsz` + `wght` axes) —
optical sizing like the reference's serif but a crisper, more restrained cut
(enterprise register; grounds: creative-direction goals 2+3). Body/UI:
**Inter Variable** (matches `web/`). Code: **JetBrains Mono** 400/500/600/700
(matches `web/`). Versions: exact pins as named canonically in spec AC1/AC9
(not restated here). Fontsource caveat: the default `index.css` of a
variable package carries the `wght` axis only — the `opsz`-carrying
stylesheet (e.g. `…/opsz.css`; exact path verified against the installed
package in T1) must be the wired import for the serif.

**Light theme (default derivation target).** Measured 2026-08-05 with the
WCAG relative-luminance formula (script below).

| Role | Value | Measured contrast |
| --- | --- | --- |
| ground | `#f7f8fa` | — |
| ground-deep (chips, tints) | `#eceff2` | — |
| ink (headings) | `#111827` | 16.69 on ground |
| ink-soft (body) | `#2b3444` | 11.78 on ground |
| ink-muted (captions, sidebar idle) | `#4b5565` | 7.09 on ground |
| ink-faint (footer small print) | `#67707f` | 4.70 on ground |
| rule (hairlines) | `#dfe3e9` | decorative |
| accent (icons, large text ≥ 24px) | `#2563eb` | 4.86 on ground |
| accent-deep (links, eyebrows, chip text) | `#1d4ed8` | 6.31 on ground; 5.81 on ground-deep |
| accent-tint | `rgba(37, 99, 235, 0.08)` | fill only |
| code-block ground | `#0d1424` | — |
| code-block text | `#c9d6ee` | 12.55 on code ground |

**Semantic state tokens (AC6 carve-out — hue-distinct, never cobalt).**
Measured fg-on-bg (light): success `#15803d` on `#dcfce7` = 4.57; danger
`#b91c1c` on `#fee2e2` = 5.30; warn `#c2410c` on `#ffedd5` = 4.52; info
`#1d4ed8` on `#dbeafe` = 5.49; neutral `#2b3444` on `#eceff2` = 10.85.
Measured fg-on-bg (dark): success `#86dfa8` on `#122a1c` = 9.56; danger
`#f4a3a3` on `#341418` = 8.43; warn `#f0b27f` on `#33200f` = 8.40; info
`#8ab0f9` on `#131f3a` = 7.52; neutral `#c3ccdb` on `#1a2130` = 9.95.
Borders take the mid value of each hue family (decorative, no AA claim).

Eyebrows and chip text use `accent-deep` (never `accent`) so they clear AA
on both ground and ground-deep. The sidebar shares the main ground (the
reference's grammar — a hairline `border-inline-end`, not a tinted panel),
so sidebar text pairs measure against `#f7f8fa`.

**Dark theme.** Measured same date.

| Role | Value | Measured contrast |
| --- | --- | --- |
| ground | `#0c111c` | — |
| surface (search modal, cards) | `#111726` | — |
| text | `#c3ccdb` | 11.67 on ground |
| text-muted | `#8b95a7` | 6.25 on ground |
| rule | `rgba(255,255,255,0.09)` | decorative |
| accent (links/active/eyebrows) | `#8ab0f9` | 8.68 on ground |
| accent-tint | `rgba(138, 176, 249, 0.12)` | fill only |

Verification script (rerun in T5 against the final CSS values):
`python3` one-liner computing WCAG 2.x relative luminance + contrast ratio
for every pair above; any pair < 4.5 fails the gate.

**Layout grammar (from the reference):** eyebrow labels 11px/500/0.18em
uppercase in accent-deep; sidebar rows 13.5px/500 with 6px-radius hover
pills; h2 hairline underline; content measure kept near Starlight's 45rem;
hairline borders, no shadows; motion 150ms color transitions only, inside
`@media (prefers-reduced-motion: no-preference)`; `:focus-visible` 2px
solid `accent-deep` (light) / `accent` (dark), offset 2px — both ≥ 3:1
against their grounds.
