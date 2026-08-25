# Spec: Journey page completion

- **Status:** Shipped (reconciled 2026-08-25: the hand-authored journey mapping deferral is complete in `a3eb381e6`; its frozen-body token was removed under owner authorization)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Readers evaluating a priority journey see an outcome-led orientation, a
credible example of good output, and decision chips that use human language to
take them directly to the corresponding decision. All journeys use stable
internal semantic IDs so labels and order can evolve without breaking links;
raw identifiers and legacy gate codes never leak into the adopter experience.

## Boundaries

### Always do

- Apply the 35 exact identifier and label mappings, fixed section copy, three
  priority eyebrows, and three transcripts in
  [`editorial-decisions.md`](editorial-decisions.md).
- Treat `(journey_id, humanGate.id)` as identity and
  `humanGates[].label` as the sole adopter-facing label source.
- Treat `packs/*/JOURNEY.md` as canonical and generated web journey copies as
  derived output.
- Keep pack versions and Claude-plugin descriptions unchanged because this
  migration does not change installed functional behavior.
- **Amendment, 2026-08-21, authorized.** Reconcile the Architect journey with
  the architecture-assessment gates that replaced its two former design-only
  gates. The accepted ledger now contains 35 mappings: Architect contributes
  `correct-current-state-map`, `choose-architecture-hotspots`, and
  `accept-architecture-action`. The exact ledger remains authoritative; this
  amendment corrects the aggregate count and does not reopen other journey
  labels or identifiers.
- **Amendment, 2026-08-19, authorized (third).** Fix the regression the second
  amendment introduced on `/journeys/atlassian/`, whose `goodOutputDescription` is
  spec-permitted prose rather than a session, and remove the duplicate focus ring
  the contrast fix made conspicuous. The `goodOutputDescription` register is now
  chosen by content shape: attributed turns render as a session, an unlabelled
  single turn renders as prose. AC15's design-review clause remains unsatisfied —
  the review's M2, the site-wide `:focus-visible` amber ring at 2.29:1 on light
  surfaces, is deferred to its own PR by owner decision because it is pre-existing,
  owned by the design-system layer, and affects every marketing route.
- **Amendment, 2026-08-19, authorized (second).** Fix the three Major findings
  from the recorded design review, and add the controls that would have caught
  them. The decision chip's `:hover`/`:focus-visible` fill paired white
  `--ds-hero-fg` with `--ds-accent` on a light surface at 2.40:1; both tokens are
  documented "on dark". The gate heading's target/focus ring was amber at
  2.29:1 on the page and 2.08:1 on the card, under the 3:1 non-text floor. And
  `goodOutputDescription` was interpolated into a `<p>`, so Astro escaped it and
  the approved transcript shipped with literal `**` and backticks while HTML
  whitespace collapsing flattened every turn into one paragraph. The approved
  transcript *text* is unchanged; only its presentation is. AC15 stays unticked
  until the design review is re-run against the fixes.
- **Amendment, 2026-08-19, authorized.** Accept `contract.decisionGateIds` in
  the published catalogue contract, additively. `#1025` landed a live contract
  test after this spec was approved; its validator treats `contract.*` as a
  closed set and so rejected the ratified field on all 12 canonical packs. The
  extension is additive only: `decisionGateIds` is optional, `yourDecisions`
  stays required and is restored to every canonical journey, and no pack
  authored against the previous contract needs an edit. `yourDecisions` and
  `decisionGateIds` therefore coexist — the IDs drive fragments and ordering,
  the strings remain adopter-facing prose, and the renderer prefers the IDs so
  nothing is shown twice. No version was bumped: `docs/product/changelog.md` is
  itself a Gate G release indicator.

### Ask first

- Change the priority set, any approved ID or label, any journey route, or the
  fixed editorial copy after it ships.
- Change a risk description, approval contract, decision meaning, installed
  payload, or runtime activation behavior while migrating identifiers.
- Extend the work beyond the approved identity, editorial, rendering,
  projection, and evidence contracts.

### Never do

- Infer an identifier by normalizing display text or use an ordinal as
  identity.
- Show a semantic ID, `globalGate`, or legacy `G…` code to adopters.
- Generate editorial eyebrow or output-transcript copy.
- Use `/skill-name` as a portable invocation contract.
- Add a dependency, route, navigation destination, new journey, pack-version
  bump, or plugin-description change without an approved amendment.

## Testing Strategy

- Journey-schema rules, the complete 35-ID mapping, uniqueness, and reference
  integrity use TDD with invalid, mutation, and valid fixtures.
- Projection parity, stable anchors, routes, labels, and absence of leaked
  identifiers use exhaustive generated-output and full-site integration checks.
- Eyebrow and transcript quality use the recorded approval in the decision
  ledger; priority pages also receive rendered visual and accessibility review.
- Browser evidence proves keyboard activation, focus transfer, scrolling,
  fragment updates, and direct-fragment loading at the approved widths/themes.

## Acceptance Criteria

- [x] Every canonical journey source represents contract decisions as ordered
  `decisionGateIds`, and every referenced ID resolves to exactly one human gate
  in that journey.
- [x] All 35 human gates use the exact internal IDs and adopter-facing labels in
  `editorial-decisions.md`; IDs satisfy the lowercase semantic-key contract and
  are unique within their journey.
- [x] Identity is exactly `(journey_id, humanGate.id)`, independent of the gate
  label and position; mutation tests prove that copy changes and reordering do
  not change fragments.
- [x] Decision chips display only `humanGates[].label`, follow
  `decisionGateIds` order, and derive human ordinals from that order without
  storing them as identity.
- [x] The decision section uses the approved “Where you decide” heading and
  intro; no visible content exposes a raw semantic ID, `globalGate`, or legacy
  `G…` code.
- [x] Every chip is a real link to exactly one
  `#decision-<semantic-id>` heading; click and keyboard activation update the
  URL, bring the heading into view, move focus to it, and show a clear
  renderer-native focused/targeted state.
- [x] Duplicate, malformed, missing, and unresolved ID fixtures fail before
  rendering; a direct fragment load resolves without consulting label text.
- [x] The exact priority set is `core`, `product-engineering`, and
  `release-engineering`; each emits its approved eyebrow and transcript
  verbatim, and no non-priority journey is required to gain either field.
  "Verbatim" is enforced line for line against canonical source, interior blank
  lines and indentation included, after decoding and line-ending normalisation.
  Exactly three differences are tolerated, each a presentation artefact one
  format cannot express: the ledger's Markdown blockquote markers, its
  hard-break trailing spaces (two or more -- a single trailing space is not a
  hard break and does not pass), and trailing blank lines that YAML `|-` chomps.
  Trailing whitespace inside canonical transcript lines is not tolerated.
- [x] Priority transcript invocations follow the approved harness-neutral
  convention: ordinary language demonstrates routing, while `discovery-loop`
  and `release-loop` are explicitly named where their complete supervisor is
  required; canonical content contains no slash-prefixed invocation.
- [x] The living journey-priority template identifies
  `product-engineering` and `release-engineering` by their canonical IDs rather
  than the stale `discovery` and `release` IDs.
- [x] Generated journey content matches canonical pack sources exactly after
  the normal generation command; no generated copy is maintained by hand.
- [x] All 12 emitted journey pages contain the exact approved labels, one link
  and one matching target per gate, and no adopter-visible internal or legacy
  identifier; the combined rendered-link checker reports no broken fragment.
- [x] Pack and plugin versions and plugin descriptions remain unchanged; if an
  installed functional behavior change is discovered, implementation stops for
  a spec amendment rather than silently versioning it.
- [x] Shipped journey content contains no repository-internal governance
  citation or dead repository-only path, and every pre-change journey route and
  navigation destination still resolves.
- [x] At 360, 375, 390, 414, and 1440 CSS-pixel widths, priority journey
  interaction has at most 1px horizontal overflow, zero serious or critical axe
  findings, correct keyboard focus/fragment behavior, and no Major
  design-review issue against the governing principles. Journey routes are
  marketing routes, which `site-browser-quality-gate` AC1 exercises without
  theme mutation; their emitted pages carry no `data-theme`, so the dual-theme
  requirement belongs to the two `/docs/` routes under that spec's AC2, not
  here. Recorded design review, third pass: "no Major or worse exists" — the two
  contrast Majors and the transcript Major are resolved, the regression the second
  fix introduced on `/journeys/atlassian/` is resolved, and the site-wide light-zone
  focus ring now measures 16.49:1 where it measured 2.29:1. Five Minors and one Nit
  from that pass are also resolved; `install-block__code--light` is deferred as a
  naming-only concern.

## Assumptions

- Technical: journey frontmatter is validated in
  `web/src/content.config.ts`, canonical sources live in
  `packs/*/JOURNEY.md`, and `web/src/content/journeys/` is generated (source:
  repository inspection on 2026-08-17).
- Technical: the current renderer displays legacy gate codes but does not use
  them as fragment identities, so no pre-existing gate deep-link contract must
  be migrated (source: repository inspection on 2026-08-17).
- Product: the exact 35 mappings, three priority journeys, copy, interaction,
  and evidence contract are accepted in `editorial-decisions.md` (source: user
  approvals 2026-08-17).
- Product: internal IDs solve referential integrity and stable-link needs but
  are not adopter content (source: user approval 2026-08-17).
- Process: this site/content migration does not change installed pack behavior,
  so pack versions and plugin descriptions stay unchanged (source: user
  approval 2026-08-17).
- Process: the platform aesthetic direction and tech-site principles govern
  journey-page review (source: `docs/design/principles/tech-site.md`).
