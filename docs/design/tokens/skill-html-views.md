---
type: design-system
slug: skill-html-views
date: 2026-10-12
route: originate
governed_by:
  - docs/design/direction/skill-html-views.md
---

# Design system: skill-emitted HTML views

These are the values behind the shared style for the maintainer views that skills emit as HTML. Values are CSS custom properties. Each view joins this shared base with its own layout rules into the one hashed style element its policy names. The adopters are `navigate-intents`, `navigate-decisions`, `explain-diff` and `render-proof`; `markdown-to-html` keeps its author themes.

## Authority and route

- **Route: originate.** There is no coherent source of visual truth across the four maintainer views. `navigate-intents` and `navigate-decisions` share a copied palette, `explain-diff` has no house style, and `render-proof` has its own distinct palette.
- **Rungs.** Each domain records the rung that supplied it.
  - `stated-constraint`: system fonts only, offline, no motion, WCAG 2.2 AA, and the 320/1280/1680/2560 checks.
  - `approved-direction`: `docs/design/direction/skill-html-views.md`.
  - `incumbent-system`: the light accent hue `#1d4ed8` from the two navigators, kept so existing users see the same link and selection colour.
  - `derivation`: everything else.

## Colour

Neutral greys carry structure; one accent marks selection, links and focus; one warning hue marks blocked, broken and stale. The rung is `approved-direction` (restrained chroma), plus `incumbent-system` for the light accent.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--c-bg` | `#fbfbfa` | `#121418` | Page |
| `--c-raised` | `#f1f2f3` | `#1b1e24` | Hovered or current row, header band |
| `--c-text` | `#1b1d21` | `#e6e8eb` | Body and headings |
| `--c-muted` | `#575d68` | `#a4aab4` | Meta, context tags, sort keys |
| `--c-rule` | `#d9dce0` | `#2b3038` | Row hairlines (decorative grouping) |
| `--c-rule-strong` | `#8a909a` | `#6c7380` | Zone boundaries, input borders |
| `--c-accent` | `#1d4ed8` | `#8ab4ff` | Links, current selection mark, focus ring |
| `--c-accent-bg` | `#e8eefc` | `#1c2a45` | Selected row fill |
| `--c-warn` | `#9a3f06` | `#f0a35e` | Blocked, broken, stale |

Computed contrast (WCAG 2.x relative luminance), all at or above AA:

| Pair | Light | Dark | Needs |
| --- | ---: | ---: | ---: |
| text on bg | 16.30 | 15.02 | 4.5 |
| text on accent-bg | 14.52 | 11.67 | 4.5 |
| muted on bg | 6.40 | 7.89 | 4.5 |
| muted on raised | 5.91 | 7.15 | 4.5 |
| accent on bg | 6.47 | 8.83 | 4.5 |
| accent on accent-bg | 5.77 | 6.86 | 4.5 |
| warn on bg | 6.57 | 8.87 | 4.5 |
| warn on accent-bg | 5.85 | 6.89 | 4.5 |
| rule-strong on bg (non-text) | 3.10 | 3.86 | 3.0 |
| focus ring (accent) on bg (non-text) | 6.47 | 8.83 | 3.0 |

Floor adaptations:
- `--c-rule` is 1.33:1 in light and 1.39:1 in dark. It is only decorative grouping between rows that already carry their own text, so it is not used for any boundary a user must perceive. Zone and input boundaries use `--c-rule-strong`.
- The accent and the warning hue have the same lightness (1.01:1 apart). They differ by hue, and state is always a word plus a glyph, so colour never carries meaning alone.

Theme selection follows the system `prefers-color-scheme`. A view may add a manual toggle that sets `data-theme` on the root; both paths read the same roles.

## Type

The rung is `stated-constraint` (system fonts) plus `approved-direction` (humanist sans, moderate four-level hierarchy).

- `--font-ui`: `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif`
- `--font-mono`: `ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace`. It is used only for ids, paths, commands and prompts.
- Counts use `font-variant-numeric: tabular-nums`.

The ratio is 1.2 per level:

| Level | Worklist density | Document density | Weight |
| --- | --- | --- | --- |
| `--t-title` | 1.375rem / 1.25 | 1.75rem / 1.2 | 650 |
| `--t-section` | 1.125rem / 1.3 | 1.3125rem / 1.3 | 650 |
| `--t-body` | 0.9375rem / 1.4 | 1.0625rem / 1.6 | 400 |
| `--t-meta` | 0.8125rem / 1.4 | 0.875rem / 1.5 | 400 |

## Space and rules

The rung is `approved-direction` (dense, compact, ruled), with a 4px base.

- `--s-1` to `--s-7`: `0.25rem`, `0.5rem`, `0.75rem`, `1rem`, `1.5rem`, `2rem` and `3rem`.
- Inside a row, cells sit `--s-3` apart. Rows are `--s-2` apart vertically in worklist density and `--s-4` apart in document density. Groups are `--s-5` apart.
- Rules are `1px solid`. Hairlines use `--c-rule`; zone boundaries and inputs use `--c-rule-strong`. The selected row adds a `3px` left bar in `--c-accent`.
- Corners are square (`0`) everywhere. There are no shadows and no elevation; a sticky region is marked by a `--c-rule-strong` rule.

## Interaction floor

- **Target size.** Every control and row link is at least `2rem` (32px) tall and at least 24px wide, above the WCAG 2.2 AA 24px minimum.
- **Focus.** A `2px solid var(--c-accent)` outline with a `2px` offset on every focusable element. It is never removed. Sticky regions keep `scroll-padding` equal to their height, so focus is never obscured.
- **Motion.** None. There are no transitions, animations or smooth scrolling, so a reduced-motion variant is unnecessary.

## Layout

The rung is `approved-direction`: a rigid column grid, edge-aligned, filling the width.

**Worklist views** use the questions rail, the list and the detail zone:

| Width | Tracks |
| --- | --- |
| below 40rem (640px; the 320px check) | One column. Questions stack, then the list; the detail replaces the list when picked. |
| 40rem to below 90rem (640–1439px; the 1280px check) | Questions as a tab row above two tracks: list `minmax(0, 3fr)`, detail `minmax(22rem, 2fr)`. |
| 90rem and up (1440px+; the 1680px and 2560px checks) | Three tracks: rail `14rem`, list `minmax(0, 3fr)`, detail `minmax(26rem, 2fr)`. |

- There is no max-width; page padding is `--s-5`.
- A row is a grid of `name minmax(0, 1fr)`, `state 8.5rem` and `context minmax(8rem, 16rem)`. The name wraps within its own cell, so other cells never wrap under it.

**Document views** use a margin column, the text column and an optional contents column:

| Width | Tracks |
| --- | --- |
| below 64rem (1024px) | One column. Margin heads sit inline above their section. |
| 64rem to below 100rem | Margin `12rem`, text `minmax(0, 68ch)`, left-aligned after the margin. |
| 100rem and up (1600px+) | Margin `12rem`, text `minmax(0, 68ch)`, contents `16rem` (sticky section list). |

## State marks

Each state is a word plus a glyph. Colour reinforces a mark but never carries it alone. The rung is `approved-direction` (rectilinear simple shapes) and `derivation`.

| State | Glyph | Word | Colour |
| --- | --- | --- | --- |
| active (in progress) | ● | Active | `--c-accent` |
| ready (canonical ready) | ▶ | Ready | `--c-accent` |
| approved | ◆ | Approved | `--c-text` |
| draft | ◇ | Draft | `--c-muted` |
| blocked | ■ | Blocked | `--c-warn` |
| broken (refused or dangling pointer) | ✕ | Broken | `--c-warn` |
| stale (snapshot or link may be newer) | △ | Stale | `--c-warn` |
| done (terminal) | ✓ | Done | `--c-muted` |

The glyph is hidden from assistive tech, and the word is read. Each view maps its own status vocabulary onto these eight marks and shows its own status word where it differs, for example "◆ Accepted".

## What may adapt

- **May adapt:** column counts and track sizes by width, the density variant by genre, and whether a view offers a manual theme toggle.
- **May not adapt:** colour roles, the type ratio, square corners, the absence of shadows and motion, focus treatment, target floor, and the state-mark set.

## Unresolved

- None for `explain-diff`: RFC-0108 D2 has its publisher inject this base as trusted bytes and hash the joined style.
- Data-visualisation colours for `navigate-decisions`' lineage diagram beyond accent and neutrals. Its own adoption slice decides them, under this floor.
