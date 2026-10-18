---
type: design-system
slug: skill-html-views
date: 2026-10-16
route: originate
governed_by:
  - docs/design/direction/skill-html-views.md
---

# Design system: skill-emitted HTML views

These are the values behind the shared style for the maintainer views that skills emit as HTML. Values are CSS custom properties. Each view joins this shared base with its own layout rules into the one hashed style element its policy names. The adopters are `navigate-intents`, `navigate-decisions`, `explain-diff` and `render-proof`; `markdown-to-html` keeps its author themes.

## Authority and route

- **Route: originate.** There is no coherent source of visual truth across the four maintainer views. `navigate-intents` and `navigate-decisions` share a copied palette, `explain-diff` has no house style, and `render-proof` has its own distinct palette.
- **Rungs.** Each domain records the rung that supplied it.
  - `stated-constraint`: fonts already on the reader's system only, offline, motion only as RFC-0108 rule 9 allows, WCAG 2.2 AA, and the 320/1280/1680/2560 checks.
  - `approved-direction`: `docs/design/direction/skill-html-views.md`, as refined by the owner on 2026-10-16.
  - `owner-approved-prototype`: the values below were measured on the prototype the owner approved on 2026-10-16, `docs/specs/intent-view-source-and-style/notes/prototype/approved-overlay.css`.
  - `derivation`: everything else.

## Colour

Neutral greys carry structure on a light canvas with white zones. One accent marks links, focus and the current selection. A violet hue marks work in progress, so the accent never doubles as a state. Each other state has a text hue and a tint; a tint only ever sits behind its own state word. The rung is `owner-approved-prototype`.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--c-bg` | `#ffffff` | `#16181d` | Zones, controls, header band |
| `--c-canvas` | `#f6f7f9` | `#0f1114` | Page behind the zones |
| `--c-raised` | `#f0f2f5` | `#20242c` | Hovered row, next-step callout, draft tint |
| `--c-detail-bg` | `#ffffff` | `#1b1e25` | Detail zone surface |
| `--c-text` | `#1b1f29` | `#e7eaf0` | Body and headings |
| `--c-muted` | `#4b5468` | `#b4bccc` | Secondary text, done and draft words |
| `--c-subtle` | `#5b6682` | `#939db1` | Meta, context tags, section labels, placeholders |
| `--c-rule` | `#e3e7ee` | `#262b35` | Row hairlines and zone outlines (decorative grouping) |
| `--c-rule-strong` | `#7d879b` | `#727b8f` | Control borders, tree guides, trail line |
| `--c-accent` | `#225bd2` | `#84a9ff` | Links, focus ring, current selection |
| `--c-accent-bg` | `#eef4ff` | `#1a2540` | Current row and current question fill |
| `--c-active` | `#6a35d4` | `#b9a4ff` | In-progress state word |
| `--c-active-bg` | `#f3edfd` | `#241b3d` | In-progress tint |
| `--c-ok` | `#04796d` | `#4fd1b0` | Approved, accepted or ready state word |
| `--c-ok-bg` | `#e9fbf6` | `#0f2a25` | Approved tint |
| `--c-warn` | `#8a5d00` | `#f2bb55` | Stale state word, notices |
| `--c-warn-bg` | `#fff6df` | `#2d2412` | Stale tint, notices |
| `--c-bad` | `#b42318` | `#ff8a80` | Broken state word, broken-entry bar |
| `--c-bad-bg` | `#fff1f0` | `#321719` | Broken tint, broken-entry callout |
| `--c-done-bg` | `#eff1f5` | `#22262f` | Done tint |

Computed contrast (WCAG 2.x relative luminance), all at or above AA:

| Pair | Light | Dark | Needs |
| --- | ---: | ---: | ---: |
| text on bg | 16.48 | 14.74 | 4.5 |
| text on canvas | 15.37 | 15.69 | 4.5 |
| text on raised | 14.69 | 12.91 | 4.5 |
| muted on bg | 7.59 | 9.31 | 4.5 |
| muted on raised | 6.77 | 8.15 | 4.5 |
| muted on done-bg | 6.71 | 7.94 | 4.5 |
| subtle on bg | 5.73 | 6.51 | 4.5 |
| subtle on canvas | 5.34 | 6.93 | 4.5 |
| subtle on raised | 5.11 | 5.70 | 4.5 |
| subtle on detail-bg | 5.73 | 6.11 | 4.5 |
| accent on bg | 6.01 | 7.70 | 4.5 |
| accent on canvas | 5.61 | 8.19 | 4.5 |
| accent on accent-bg | 5.44 | 6.58 | 4.5 |
| active on active-bg | 5.97 | 7.56 | 4.5 |
| ok on ok-bg | 4.95 | 8.04 | 4.5 |
| warn on warn-bg | 5.35 | 8.75 | 4.5 |
| bad on bad-bg | 5.98 | 7.23 | 4.5 |
| bad on detail-bg (non-text bar) | 6.57 | 7.31 | 3.0 |
| rule-strong on bg (non-text) | 3.61 | 4.18 | 3.0 |
| rule-strong on detail-bg (non-text) | 3.61 | 3.93 | 3.0 |

Floor adaptations:
- `--c-rule` outlines zones and divides rows that already carry their own text, so it marks no boundary a user must perceive. Control boundaries use `--c-rule-strong`.
- State is always a word plus a glyph, so a tint never carries meaning alone.

Theme selection follows the system `prefers-color-scheme`. A view may add a manual toggle that sets `data-theme` on the root; both paths read the same roles.

## Radius

The rung is `owner-approved-prototype` (soft, quiet corners).

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--r-1` | `6px` | | Chips, small tags, the current row |
| `--r-2` | `8px` | | Controls, disclosures, callouts, rail links |
| `--r-3` | `12px` | | Zones |

State marks use a full pill (`999px`), which is a shape, not a role.

## Elevation

The rung is `owner-approved-prototype`. Only the list zone and the detail zone are raised; rows, rail links and controls stay flat.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--e-1` | `0 1px 2px rgba(16, 24, 40, 0.05)` | `0 0 0 1px rgba(255, 255, 255, 0.02)` | List zone; detail zone with nothing picked |
| `--e-2` | `0 1px 3px rgba(12, 13, 22, 0.06), 0 12px 32px -16px rgba(12, 13, 22, 0.16)` | `0 0 0 1px rgba(255, 255, 255, 0.04), 0 18px 40px -20px rgba(0, 0, 0, 0.8)` | Detail zone with an item picked |

## Type

The rung is `stated-constraint` (fonts on the reader's system only; nothing is loaded) plus `owner-approved-prototype`.

- `--font-ui`: `Inter, "Inter Variable", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. Inter is used only where the reader already has it installed.
- `--font-mono`: `ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace`. It is used only for ids, paths, commands, prompts and diagnostic text.
- Counts use `font-variant-numeric: tabular-nums`.

| Level | Worklist density | Document density | Weight |
| --- | --- | --- | --- |
| `--t-title` | 1.125rem / 1.3 | 1.75rem / 1.2 | 650 |
| `--t-section` | 1rem / 1.35 | 1.3125rem / 1.3 | 650 |
| `--t-body` | 0.875rem / 1.5 | 1.0625rem / 1.6 | 400 |
| `--t-meta` | 0.78rem / 1.45 | 0.875rem / 1.5 | 400 |
| `--t-label` | 0.7rem / 1.3, uppercase, 0.07em tracking | 0.75rem / 1.3, uppercase | 650 |

`--t-label` names a section inside a zone; zone titles use `--t-title`.

## Space and rules

The rung is `approved-direction` (dense, compact, ruled), with a 4px base.

- `--s-1`, `--s-2`, `--s-3`, `--s-4`, `--s-5`, `--s-6` and `--s-7`: `0.25rem`, `0.5rem`, `0.75rem`, `1rem`, `1.5rem`, `2rem` and `3rem`.
- Inside a row, cells sit `--s-3` apart. Rows are `--s-2` apart vertically in worklist density and `--s-4` apart in document density. Groups are `--s-4` apart, and the zones sit `--s-4` apart on the canvas.
- Rules are `1px solid`. Hairlines use `--c-rule`. The current row and current question add a `3px` inset bar in `--c-accent`; a broken entry adds a `3px` left bar in `--c-bad`; the next-step callout adds a `3px` left bar in `--c-rule-strong`.

## Interaction floor

- **Target size.** Every control and row link is at least 24 by 24 CSS px, the WCAG 2.2 AA minimum; most are `--target` (`2rem`) tall.
- **Focus.** A `2px solid var(--c-accent)` outline with a `2px` offset, rounded by `--r-1`, on every focusable element. The outline is never removed. Sticky regions keep `scroll-padding` equal to their height, so focus is never obscured.
- **Keyboard.** No single-character shortcut.

## Motion

The rung is `stated-constraint`: RFC-0108 rule 9 as corrected on 2026-10-16. Every rule below sits inside `@media (prefers-reduced-motion: no-preference)`; with reduced motion the page is still.

| Role | Value | Use |
| --- | --- | --- |
| Paint transition | `120ms ease` on `background-color`, `color`, `border-color`, `box-shadow` | Rows, rail links, controls, disclosures |
| Detail fade | `160ms ease-out`, opacity 0 to 1 with a `translateY(4px)` rise | Each child of the detail body as it renders |

Nothing scrolls smoothly, nothing is tied to scroll, and nothing repeats.

## Layout

The rung is `approved-direction`: a rigid column grid, edge-aligned, filling the width.

**Worklist views** use the questions rail, the list zone and the detail zone:

| Width | Tracks |
| --- | --- |
| below 40rem (640px; the 320px check) | One column. Questions stack, then the list; the detail replaces the list when picked. |
| 40rem to below 90rem (640–1439px; the 1280px check) | Questions as a tab row above two tracks: list `minmax(0, 3fr)`, detail `minmax(22rem, 2fr)`. |
| 90rem to below 120rem (1440–1919px; the 1680px check) | Three tracks: rail `16.5rem`, list `minmax(0, 1fr)`, detail `clamp(22rem, 30%, 32rem)`. |
| 120rem and up (1920px+; the 2560px check) | Rail `16.5rem`, list `minmax(0, 1fr)`, detail `clamp(28rem, 30%, 40rem)`; a row's name cell is capped at `34rem` so the state stays near the name. |

- There is no max-width; page padding is `--s-5`.
- A row is a grid of `name minmax(10rem, 1fr)`, `state 8.5rem` and `context minmax(12rem, 1fr)` from 66rem. The name wraps within its own cell, so other cells never wrap under it.

**Track properties.** The worklist rows that align across nesting depths — the roadmap's capability rows and the Browse tree's rows — read these layout properties, declared in the shared base because the layout sheet declares none:

| Property | Value | Use |
| --- | --- | --- |
| `--name-w` | `clamp(10rem, calc(100cqw - 34rem), 34rem)` | Width of the name track at depth 0 |
| `--rm-bar` | `10rem` | Roadmap bar width |
| `--rm-share` | `11rem` | Roadmap share column width |
| `--rm-prog` | `--rm-bar` + `--s-2` + `--rm-share` | Roadmap progress track width |
| `--rm-in`, `--rm-self` | `0px`, set per nesting depth | Indent a nested roadmap row gives back to its name track |
| `--tr-in`, `--tr-self` | `0px`, set per nesting depth | Indent a nested tree row gives back to its name track |

**Document views** use a margin column, the text column and an optional contents column:

| Width | Tracks |
| --- | --- |
| below 64rem (1024px) | One column. Margin heads sit inline above their section. |
| 64rem to below 100rem | Margin `12rem`, text `minmax(0, 68ch)`, left-aligned after the margin. |
| 100rem and up (1600px+) | Margin `12rem`, text `minmax(0, 68ch)`, contents `16rem` (sticky section list). |

## State marks

Each state is a word plus a glyph inside a pill tinted by its state. Colour reinforces a mark but never carries it alone. The rung is `approved-direction` (simple shapes) and `owner-approved-prototype`.

| State | Glyph | Word | Text | Tint |
| --- | --- | --- | --- | --- |
| active (in progress) | ● | Active | `--c-active` | `--c-active-bg` |
| ready (canonical ready) | ▶ | Ready | `--c-ok` | `--c-ok-bg` |
| approved | ◆ | Approved | `--c-ok` | `--c-ok-bg` |
| draft | ◇ | Draft | `--c-muted` | `--c-raised` |
| blocked | ■ | Blocked | `--c-bad` | `--c-bad-bg` |
| broken (refused or dangling pointer) | ✕ | Broken | `--c-bad` | `--c-bad-bg` |
| stale (snapshot or link may be newer) | △ | Stale | `--c-warn` | `--c-warn-bg` |
| done (terminal) | ✓ | Done | `--c-muted` | `--c-done-bg` |

The glyph is hidden from assistive tech, and the word is read. Each view maps its own status vocabulary onto these eight marks and shows its own status word where it differs, for example "◆ Accepted".

## What may adapt

- **May adapt:** column counts and track sizes by width, the density variant by genre, and whether a view offers a manual theme toggle.
- **May not adapt:** colour, radius and elevation roles, the type scale, the motion rules, focus treatment, target floor, and the state-mark set.

## Unresolved

- None for `explain-diff`: RFC-0108 D2 has its publisher inject this base as trusted bytes and hash the joined style.
- Data-visualisation colours for `navigate-decisions`' lineage diagram beyond accent and neutrals. Its own adoption slice decides them, under this floor.
