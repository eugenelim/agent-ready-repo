# Spec: Journey page completion

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** tech-site-completion
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Readers evaluating a priority journey see an outcome-led orientation, a
credible example of good output, and decision chips that take them directly to
the corresponding human gate. Every journey uses stable gate identifiers so
labels can evolve without breaking links, while existing routes and navigation
remain unchanged.

## Boundaries

### Always do

- Use canonical gate IDs as the relationship between decision chips and gate
  cards; render human-facing chip labels from the gate definitions.
- Author and review priority-journey eyebrows and output transcripts as
  product content.
- Treat `packs/*/JOURNEY.md` as canonical and generated web journey copies as
  derived output.
- Apply the pack version, plugin-manifest, marketplace, and changelog rules to
  every pack whose shipped journey source changes.

### Ask first

- Change which journeys are priority, any journey route, or a public gate ID
  after it ships.
- Change a human-gate label, risk description, approval contract, or decision
  meaning while migrating identifiers.
- Extend the work beyond orientation, output evidence, anchors, and the known
  priority-template ID correction.

### Never do

- Infer an identifier by normalizing display text.
- Generate editorial eyebrow or output-transcript copy.
- Add a dependency, route, navigation destination, or new journey.

## Testing Strategy

- Journey-schema rules, unique gate IDs, and reference integrity use TDD with
  invalid and valid fixtures.
- Projection, stable anchors, routes, and fragment links use goal-based
  generated-output and full-site integration checks.
- Eyebrow and transcript quality use recorded content/design review; priority
  journey pages also receive rendered visual and accessibility review.

## Acceptance Criteria

- [ ] Every canonical journey source represents contract decisions as
  `decisionGateIds`, and every referenced ID resolves to exactly one human gate
  in that journey.
- [ ] Every human gate has a stable, unique canonical ID that is independent of
  its display label.
- [ ] Each rendered decision chip uses its gate's current label and links to the
  matching gate card's DOM fragment.
- [ ] The combined rendered-link checker validates every decision-chip fragment
  and reports no broken page or anchor.
- [ ] The `core`, `product-engineering`, and `release-engineering` journeys each
  have a human-reviewed, outcome-led eyebrow and a human-reviewed
  `goodOutputDescription` transcript.
- [ ] No non-priority journey is required to gain new eyebrow or transcript
  copy through this spec.
- [ ] The living journey-priority template identifies
  `product-engineering` and `release-engineering` by their canonical IDs rather
  than the stale `discovery` and `release` IDs.
- [ ] Generated journey content matches canonical pack sources after the normal
  generation command; no generated copy is maintained by hand.
- [ ] Every pack whose `JOURNEY.md` changes receives matching patch-version
  updates in `pack.toml` and `.claude-plugin/plugin.json`; self-hosted catalogue
  projections, marketplace data, and changelog entries are synchronized and
  catalogue lint/verification pass.
- [ ] Shipped journey content contains no repository-internal governance
  citation or dead repository-only path.
- [ ] Every pre-change journey route and navigation destination still resolves.
- [ ] At 360, 375, 390, 414, and 1440 CSS-pixel widths, each priority journey
  exposes its eyebrow, output transcript, and keyboard-usable decision-to-gate
  links with at most 1px horizontal overflow and zero serious or critical axe
  findings.
- [ ] A rendered design review finds no Major issue against the platform
  aesthetic direction or the tech-site principles, including evidence beside
  claims and stable orientation.

## Assumptions

- Technical: journey frontmatter is validated in
  `web/src/content.config.ts`, canonical sources live in
  `packs/*/JOURNEY.md`, and `web/src/content/journeys/` is generated (source:
  repository inspection on 2026-08-17).
- Technical: display decision text is currently duplicated separately from
  human-gate definitions and gate cards lack stable DOM IDs (source: repository
  inspection on 2026-08-17).
- Product: the priority set for this programme is exactly `core`,
  `product-engineering`, and `release-engineering` (source: user confirmation
  2026-08-17).
- Product: canonical `decisionGateIds`, labels rendered from gate definitions,
  and stable gate-card IDs are approved (source: user approval of
  `docs/product/briefs/tech-site-completion.md`).
- Product: eyebrow and transcript content is human-written (source:
  `docs/product/briefs/tech-site-completion.md`).
- Process: the platform aesthetic direction and tech-site principles govern
  journey-page review (source: user confirmation 2026-08-17 and
  `docs/design/principles/tech-site.md`).
- Process: any non-cosmetic `packs/` content change requires synchronized pack
  and plugin patch versions, self-hosting projection, marketplace regeneration,
  and a changelog entry (source: `packs/AGENTS.md` and
  `packs/AGENTS.local.md`).
