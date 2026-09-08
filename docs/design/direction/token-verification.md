---
type: design-system
scope: verification
surface: responsive-web
verifies: web/src/styles/tokens.css
direction: docs/design/direction/tech-site-amendment.md
status: active
gate: approve-aesthetic-direction (passed 2026-09-04)
updated: 2026-09-04
---

# Token verification — what the canvas needs that the system lacks

A verification pass, not a derivation. The instruction was to amend rather than
re-establish, so the question is narrow: **what does the operating-model canvas
require that the existing system does not already provide?**

**Answer: no new semantic tokens.** One component-tier addition, and three
findings that matter more than any token would.

No palette, spacing, or type values appear below. Scale steps are referred to
symbolically. The existing file holds the values and remains their single source.

## Intent restated

Every decision below traces to a named goal in the aesthetic direction as
amended: **Precision authority** (dominant), Staged revelation, Grounded
ambition, Identity specificity, and the amendment's fifth goal **Portable
whole** — the artifact carrying the model stays whole when it leaves the page.

Portable whole is the goal that does the work here, and it pushes toward *fewer*
expressive mechanisms rather than more. A verification pass that ended up adding
tokens would be evidence the amendment had been misread.

## The measured baseline

Counts and structure, not values.

| Layer | Count | Role |
| --- | --- | --- |
| Primitive tier | 50 `--prim-*` | Raw scale steps. Never referenced by component CSS. |
| Semantic tier | 97 unique `--ds-*` | The addressable system. |
| Component tier | 2 scoped `--ds-focus-ring` overrides | Deliberate, documented, with measured ratios recorded in the file. |

The brief carried a figure of 90. The measured count is **97**, with no
duplicates inside the semantic block. The two extra `--ds-focus-ring`
declarations are the component tier working as designed, not a defect; an
earlier count in this engagement misread them as one and that correction is
recorded in the discovery brief.

Semantic families, by size: state (15), space (10), type (8), hero (8), cta (8),
z (5), weight (5), accent (5), track (4), radius (4), lead (4), on (3), dur (3),
surface (2), shadow (2), section (2), font (2), ease (2), content (2), border
(2), focus (1).

`docs-site/src/styles/tokens.css` carries 146 separately-named tokens. The two
renderers are deliberately not one palette and this pass does not converge them.

## Coverage: purpose before token

Each thing the canvas needs, named by the job it does, checked against an
existing semantic role. Purpose first, then whether a role already exists.

| What the canvas needs it for | Existing semantic role | New token? |
| --- | --- | --- |
| The line the stations sit on | a rule that is **meaningful**, so it must clear the non-text floor | no — the muted `on-surface` role. **Not the `border` family:** it measures 1.30 against the light ground and fails 3:1. |
| A station at rest | low-opacity accent fill with an edge that carries the shape | no — `accent-subtle` fill inside an `accent-deep` ring. **Not the display accent as the ring:** 2.29, fails 3:1. |
| A station's label | body text on the page ground | no — the `on-surface` families |
| The depot enclosure at station 2 | a second-level ground plus a **meaningful** border | no — `surface-alt` ground with an `accent-deep` border. The `border` family fails 3:1 here for the same reason as the rail. |
| A work step inside the depot | body text on the second-level ground | no — the `on-surface` families |
| A decision signal | emphasis mark, and it must not be colour-only | no — `accent-subtle`-family fill inside an `accent-deep` outline, **plus a different shape**; see finding 3 |
| The tracker spur and its terminus | a meaningful dashed rule plus a terminal mark | no — the muted `on-surface` role for the spur, the strongest `on-surface` for the terminus |
| The scope boundary | the faintest separation that still clears the non-text floor | no — the muted `on-surface` role |
| Label typography | small and extra-small steps, mono for identifiers | no — `type-sm`, `type-xs`, `font-mono` |
| Focus indication on an interactive station | the existing ring, including its dark-carrier override | no — `focus-ring` plus the two scoped overrides |
| Entrance, if used at all | the gentlest duration and standard easing | no — `dur-gentle`, `ease-out` |

**Verdict: zero new semantic tokens.** Every role the canvas needs is already
named. That is the expected result for a system with 97 semantic roles across 21
families, and it is what "amend, do not re-establish" looks like when it holds.

**An earlier draft of this table named the wrong roles**, and the composition
pass corrected it. Three of the canvas's marks are *meaningful graphical
objects* and therefore carry a non-text contrast floor that the lightest border
and the display accent do not clear. The roles above are the ones the built
composition actually uses, with the failing candidates named so nobody reaches
for them again. The verdict is unchanged — no new token was needed, only a
different existing one.

**One component-tier addition is warranted**, following the same pattern as the
existing focus-ring overrides: a small scoped set for the canvas, mapping its
parts to semantic roles, so the drawing references the system by role rather than
reaching for primitives. The architecture already forbids component CSS touching
the primitive tier, and this keeps the canvas inside that rule.

Named for the job, never for the appearance: station-at-rest, station-emphasis,
depot-ground, signal-mark, spur-rule, boundary-rule. Not "amber-pill" or
"grey-line" — a name that describes today's look locks the value into the name.

## Finding 1 — The canvas cannot consume the token system in its binding rendering

This is the finding that matters, and no token can fix it.

The canvas's binding rendering is a sanitised GitHub README, where `<style>`
blocks inside SVG, `class`, and `id` are stripped. A custom property needs a
cascade to resolve. **With no stylesheet and no class hooks, `var()` has nothing
to resolve against.** The canvas is therefore the one element on this site whose
most important rendering cannot reference the design system at all.

It needs resolved literal values in element-level `fill` and `stroke` attributes.

**The hazard that follows is silent drift.** Hand-author those literals once and
the README canvas becomes a snapshot of the palette at authoring time. Change a
token later — and the amended direction expects the accent family to keep
serving new work — and the site updates while the README does not. Nothing would
fail. The two renderings would simply disagree, and the disagreement would be
invisible until somebody compared them side by side.

**Recommendation: generate the canvas SVG from the token values; do not
hand-author the literals.** A snapshot of a system that is expected to change is
not a copy of the system, it is a future contradiction. This is a build
requirement, and it is the second thing the canvas needs from the pipeline
alongside the raster export — which means the export path is now carrying two
jobs, not one.

Checked rather than assumed: nothing in `tools/` reads `tokens.css` to emit an
asset today. `tools/build-site.py` and `tools/lint_zone_violations.py` reference
`--ds-*` for other purposes, and no SVG asset is generated anywhere. This is new
pipeline work.

## Finding 2 — There is no contrast check for the marketing palette

`tools/check-docs-contrast.py` resolves custom properties and fails below the
body-text requirement — **for `docs-site/src/styles/starlight.css` only.** It
reads the docs palette, per the docs-site design-refresh spec's criteria. There
is no equivalent for the marketing renderer's `--ds-*` palette.

That matters now because of a hazard the aesthetic direction already identified
and resolved *by convention*: the display accent measures below the body-text
requirement on light grounds, and a separate text-safe accent is the compliant
choice there. The convention is followed correctly today — every use of the
display accent as text colour sits in a dark zone, which this engagement verified
by inspection. But nothing mechanically enforces it.

**The canvas is the first element to put text inside a graphic on a light band.**
Text inside an SVG carries the same contrast requirement as page text, and the
canvas has more small labels than any existing component. It is exactly where the
unenforced convention would first be broken, and where a break would be hardest
to see.

**Recommendation:** extend the existing checker to the marketing palette, or add
a sibling for it, and include the canvas's text-on-ground pairs. The existing
tool's shape is the model — it lists real text-on-real-ground pairs and
deliberately excludes decorative fills, which is the right discrimination for a
diagram full of tints and rules.

This is a gate-relevant scope fact, not a design artifact.

## Finding 3 — Contrast budget, and the one thing colour may not carry

The floor is a constraint at derivation time, not a later pass, and contrast is
budgeted across a surface rather than maximised on every element.

The canvas's budget, in rank order: **station labels and work-step text spend
the most**, because they are the smallest text on the surface and carry the
model. **Signals and the spur terminus spend almost none** — they are shapes, and
their meaning must not depend on their colour. **The line, the depot ground, and
the boundary spend the least**, and deliberately: three separations at similar
strength would produce the visual noise the dominant goal calls chartjunk.

The hard rule, from the floor rather than from taste: **no station, signal,
scope boundary, or spur may be distinguished by colour alone.** Each needs
shape, label, or position as well. This is why the decision signals are shapes
that happen to be accented rather than accents that happen to be shaped — and it
is the same requirement that makes the canvas legible when the README renders it
without any of the emphasis the web version can add.

One live dispute, resolved for this system: minimising decorative ink is right,
but it must not be applied to encoding redundancy. Cut chartjunk; keep the
redundant cue the floor requires.

## Serialization

Record the canvas's component-tier set in the W3C design-tokens interchange
shape, alongside the existing semantic tier, so the generator in finding 1 has a
machine-readable source and the values live in exactly one place. The interchange
shape is the reason finding 1's recommendation is cheap rather than speculative —
the generator reads a serialized token document, not a stylesheet it has to parse.

Values stay in `tokens.css`. This document adds none.

## Open questions for the gate

1. **Is the SVG generator in scope?** Finding 1 makes it the difference between
   two renderings that agree and two that silently drift. It is pipeline work,
   and it is the same pipeline the raster export needs.
2. **Is extending the contrast check in scope?** Finding 2 is a pre-existing gap
   that the canvas is about to walk into. Cheap, and it is the only mechanical
   guard available for the one hazard this palette is known to have.
3. **Nothing to decide on tokens themselves.** Zero new semantic tokens is the
   verification result, not a proposal, and the component-tier set follows an
   existing pattern.

## Hand-off

`interaction-design` for the canvas's behaviour half. Note the focus
architecture is **one image, one control** — not a per-station focus order. `frontend-engineering`, through the build handoff, for the generator
and the contrast check. Nothing here needs `creative-direction` to run again —
the amendment already resolved the direction this pass verifies against.
