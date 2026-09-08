---
type: screen-flow-brief
screen: marketing-home
flow: team-orientation
surface: responsive-web
surface-genre: marketing
---

# Screen brief: marketing-home · agent-ready-repo · surface: responsive-web

## Place in the whole

- **Type:** screen-brief
- Journey step(s): future-state Stage 1 (Evaluate), Stage 2 (Prove on real work), Stage 3 (Win buy-in)
- Enters from: search engine · package page · direct or bookmark · S2 unfurl rendering · S2 sanitised static · S2 text alternative
- Exits to: S2 (canvas) · terminal (primary action) · S3 (guides index, transitional action) · guide: create a catalogue
- Traces to outcome: the champion can re-explain the operating model to someone who has not seen this page
- Surface genre: marketing — hero approach, above-fold contract, and scroll story apply

## Job

Show a champion the whole operating model and give them something they can repeat.

## States

Defer to the shared quality floor for the state set. Which apply here:

- **success/default:** the only state. Eleven zones, canvas above the fold.
- empty / loading / error / partial / disabled: **not applicable.** The screen has
  no data dependency and no gated content, so these are decisions rather than
  omissions. The rendering-state burden lives on S2, not here.
- permission/denied: not applicable — the screen is not gated.

## Data & actions

- **Shows:** the operating-model canvas; the problem statement; the five adoption
  stations with their real costs and stated first results; the work sequence; the
  human decision points; three checkable proofs; the outcome router; the adapter
  matrix; the install commands; the route into the ordered paths.
- **Actions:**
  - Copy an install command → client-side clipboard. On failure the command stays
    selectable as text, so the action degrades rather than dead-ends.
  - Follow the primary action → terminal, outside our surfaces. ⚠ Install or
    first run fails → S3, where troubleshooting lives. The flow cannot guarantee
    the reader gets there; the terminal owns its own output.
    - Follow the transitional action → S3.
  - Follow zone 10's internal-case route → S6. This is the marketing-side route
    to the screen built for the journey's highest-weight stage; without it a
    Stage 3 champion would have to complete Stage 4 to reach it.
  - Interact with the canvas → S2's emphasis state. Additive only.
  - Narrow viewport, or the graphic does not render → S2 text alternative. ⚠
  - Follow the closer → guide: create a catalogue.
  - Open a pack from the outcome router → pack page (existing, out of scope).

## Interaction & behavior

See `interaction-design` enrichment. One constraint set here and not negotiable
downstream: **any behaviour whose removal loses information is out of contract**,
because this screen's primary element must render as a static image in a
sanitising Markdown pipeline. Emphasis may add weight; it may not add meaning.

## Copy

See `docs/design/copy/marketing-home.md` for the four ranked copy goals and their
arbitration, and `docs/design/content/marketing-home.md` for the per-zone content
direction and the above-fold contract. Strings come from `ux-writing`.

**One prohibition that belongs in the brief rather than only in the copy deck:**
no string on this screen may contain `G0`, `G1.5`, `G2`, `G3`, `G4`, or `G5`.
Eleven such strings render today.

## Shared contract — REFERENCE, do not restate

- Design system: `web/src/styles/tokens.css` — 97 unique `--ds-*` semantic tokens
  over a separate primitive tier. **Amend, never re-establish.** Reuse the
  existing section band, CTA, card, table-in-scroll-region, and copy-button
  components. The two scoped `--ds-focus-ring` overrides are deliberate and
  documented; leave them alone.
- Aesthetic direction: `docs/specs/platform-site/aesthetic-direction.md` —
  dominant goal Precision authority; alternating-band model; single amber accent;
  static, never looping.
- Navigation / chrome: the marketing header and footer. Deliberately shares no
  CSS, component, palette, breakpoint, or focus implementation with the
  documentation renderer.
- Quality floor: WCAG at the level this context requires · reduced-motion ·
  handle-all-states.

## Consistency invariants

- **Reuse, never reinvent:** marketing header, footer, section band, primary and
  ghost CTA, outcome card, scrollable-table region, copy button.
- **Must stay consistent with:** S2 (embeds it), S6 (reuses this screen's
  components entirely and introduces none).
- **The load-bearing invariant:** the five station names appear here in zones 4 and 5 and in S2 — marketing-side only. S3's job groups are the seven existing job names, a different axis; what this screen shares with S3 is those seven names and the work-lifecycle decision phrasing.
- Zones 4 and 5 must not merge. Their separation is the two-lifecycle design.

## Done

- [ ] all applicable states designed — default only, others explicitly n/a
- [ ] every action wired to a named service
- [ ] error/edge flows route to a real screen or state
- [ ] copy in per state
- [ ] WCAG + reduced-motion honored
- [ ] uses the design system (no off-system components)
- [ ] interaction/behavior section enriched by `interaction-design`
- [ ] zero gate-code strings
- [ ] design-review clean

### If marketing

- **Hero approach: narrative.** One of the five named types, chosen and argued in `../../discovery/team-orientation-marketing-structure.md`. The category is unfamiliar, the product is complex, and the champion must picture their own team inside it — and narrative is the only one of the five whose natural centrepiece is a diagram of a sequence. Problem-agitation was the runner-up and is rejected because the reader is already Problem-Aware. Statement is what ships today and fails the tweet test.
- **Above-fold contract:** headline naming who this is for and what problem it
  solves, in the reader's words, without naming the mechanism · subheadline
  carrying the product insight the headline cannot · one primary action in
  outcome language · one transitional action for the reader who is not the
  installer · proof signal adjacent to the actions, and it must be checkable
  rather than self-reported · friction microcopy removing the dominant objection.
  Tone-collision check: the headline is problem-framed, so the subheadline must
  build conviction and must not agitate a second problem.
- **Scroll story:** this screen is the whole story. Zone assignment is in
  `docs/design/discovery/team-orientation-ia.md` — eleven zones, each with one
  job. `conversion-design` owns any merging.
- **IC-first check:** the copy must lead with the reader's recognized problem
  before naming the product. The current hero fails this and it is finding 5 in
  the heuristic baseline.
