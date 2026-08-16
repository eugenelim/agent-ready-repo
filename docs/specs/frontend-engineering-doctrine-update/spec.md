# Spec: frontend-engineering-doctrine-update

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071, ADR-0057
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter evaluating or using the frontend-engineering pack can identify the
right operating mode, follow the implementation journey, write a page/screen
contract at the right level of detail, and apply the pack's performance policy
without reading the skill source. The marketing page, journey, and guide tree
present one evidence-backed account of the pack. A doctrine benchmark checks
that account against every shipped frontend-engineering skill and reviewer
before publication; any behavior gap becomes explicit follow-on work rather
than an unsupported adopter-facing claim.

## Boundaries

### Always do

- Benchmark all nine frontend-engineering skills and the `frontend-reviewer`
  against RFC-0071 and the Digital Experience Contract before authoring, then
  extract and re-check every claim from the finished adopter-facing material.
- Treat `packs/frontend-engineering/JOURNEY.md` as the canonical journey source
  and generate `web/src/content/journeys/frontend-engineering.md` from it.
- Keep guidance proportional: distinguish significant new surfaces, smaller
  component changes, retrofit work, audits, and verification runs.
- Keep shipped pack content free of repository-internal governance citations.

### Ask first

- Any change to a `.apm` skill or reviewer body prompted by the benchmark;
  record the gap as follow-on work unless the scope is explicitly expanded.
- Any universal numeric asset ceiling not already required by RFC-0071 or the
  canonical frontend-engineering skill.
- Any restructuring outside the frontend-engineering pack page, journey, and
  guide tree.

### Never do

- Edit the generated web journey directly or create a second canonical journey.
- Publish a capability claim that the benchmark cannot trace to shipped pack
  content.
- Change frontend-engineering skill or reviewer behavior, add a dependency, or
  add a new top-level directory in this implementation. The required
  benchmark-derived activation eval update is the only authorized `.apm`
  change.
- Turn the page/screen contract into a mandatory ritual for trivial changes.

## Testing Strategy

- **Goal-based checks** verify benchmark coverage, guide frontmatter and index
  registration, journey generation, version synchronization, catalogue
  projection, and site builds. These outcomes are structural and are best
  proved by the repository's existing validators and generators.
- **Visual / manual QA** exercises the rendered marketing pack page, journey,
  page-contract how-to, and performance reference at small-phone, tablet, and
  desktop widths. A cold reader must be able to identify the pack's four jobs,
  follow the journey, and choose the appropriate contract/performance guidance.
- **TDD is not used.** This change adds no runtime logic with a compressible
  invariant; construction checks operate on published artifacts instead.

## Acceptance Criteria

- [x] AC1: `benchmark.md` contains an initial obligation matrix covering all
  nine skills named by `packs/frontend-engineering/pack.toml` and the
  `frontend-reviewer`, plus a final claim inventory extracted from the completed
  marketing page, journey, two new guides, and frontend-engineering guide index.
  Both sections map their rows to `Pass`, `Gap`, or `Not applicable` with
  canonical file-path citations.

- [x] AC2: A final adopter-facing claim with no shipped evidence is removed or
  narrowed before publication. Every shipped-skill behavior `Gap` has a
  cold-start-sufficient follow-on entry in `workspace.toml [backlog].open`; when
  no behavior gaps remain, the benchmark states that result explicitly. No
  skill or reviewer body changes; the only authorized `.apm` change is
  `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json`.

  **Both behaviour gaps this AC recorded are now closed** (2026-08-16,
  `spec/frontend-manifest-production-fields`, pack 0.2.0). The narrowing was the
  right call at the time — claiming coverage FE did not have would have been
  worse — but it left the Digital Experience Contract asking at production tier
  for evidence nothing collected. The evidence manifest now carries
  `security/privacy review status` and `reliability/recovery status`, recording
  review state and handoff rather than a verdict, so FE still performs neither
  review.

- [x] AC3: `web/src/content/packs/frontend-engineering.md` presents create,
  retrofit, audit, and verify as four adopter jobs with their expected outputs;
  a five-second scan answers what the pack is, who it serves, and which job to
  choose before the detailed skill inventory. Its frontmatter links to both the
  guide home and the frontend-engineering journey.

- [x] AC4: `packs/frontend-engineering/JOURNEY.md` satisfies the journey
  frontmatter contract and names the page/screen contract, implementation
  sequence, verification gates, evidence manifest, and independent review as
  distinct steps. It describes the adopter's inputs, outputs, decisions, and
  recovery path without repository-internal governance citations.

- [x] AC5: `web/src/content/journeys/frontend-engineering.md` is generated from
  the pack journey, carries `generated: true`, and matches its canonical source
  apart from the generated marker.

- [x] AC6: `guides/frontend-engineering/how-to/page-screen-contract.md` explains
  when the full 12-field contract is required, what every field means, and when
  a smaller change needs only a proportional subset or no contract. It includes
  at least one complete significant-surface example and one smaller-change
  example without changing the canonical field names.

- [x] AC7: `guides/frontend-engineering/reference/performance-targets.md` states
  the p75 CWV targets—LCP at most 2.5 seconds, INP at most 200 milliseconds, and
  CLS at most 0.1—evaluated separately for mobile and desktop wherever field
  data exists, and covers all seven canonical asset-budget categories. Its
  surface-type table explains what to prioritize and measure for marketing,
  documentation, product/workspace, analytical/internal, and transactional
  surfaces without presenting invented universal byte ceilings.

- [x] AC8: `guides/frontend-engineering/README.md` registers both new guides and
  gives the adopter a clear route from pack overview to journey, task how-to,
  performance reference, and the existing audit/tutorial material. All added
  guide links resolve and their frontmatter passes the guide schema.

- [x] AC9: Before the detailed skill inventory, the marketing page displays four
  job headings—Create, Retrofit, Audit, and Verify—with one expected output for
  each. The journey uses separate named steps for page/screen contract,
  implementation, gates, evidence manifest, and independent review. Each new
  guide opens with a “use this when” statement and names its resulting artifact
  or decision; the two guides use the same CWV, asset-budget, mode, and contract
  terms as the benchmarked skill sources.

- [x] AC10: The frontend-engineering pack version is bumped consistently in
  `pack.toml` and `.claude-plugin/plugin.json`; the changelog records the
  adopter-facing additions, and generated catalogue/self-host projections are
  synchronized.

- [x] AC11: Guide validation, guide-index validation, site generation, catalogue
  lint/verify, self-host drift checks, and the repository build check pass.

- [x] AC12: `qa.md` durably records the local-build session boundary, build
  commands and exit results, the four routes exercised, observed reader-visible
  outcomes at 375px, 768px, and 1280px, screenshot or DOM-evidence identifiers,
  navigation/focus/code-block/overflow results, and the fresh-context reviewer
  summary. The session verifies local static reader journeys; actual skill
  execution, field CWV collection, and remote deployment are explicitly
  documented but not exercised. No severity-3-or-higher design-review finding
  remains open.

- [x] AC13: The main frontend-engineering activation eval set adds
  benchmark-derived coverage for the underrepresented retrofit,
  page/screen-contract, and project-specific asset-budget job language plus at
  least one documentation-authoring near miss; eval JSON and deep catalogue
  validation pass without changing skill or reviewer behavior.

## Assumptions

- Technical: the shipped frontend-engineering skill already contains the four
  modes, 12-field contract, WCAG 2.2 AA floor, CWV thresholds, asset-budget
  categories, brownfield inspection, and evidence manifest (source:
  `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`).
- Technical: pack-local `JOURNEY.md` files generate web journey files through
  `tools/build-site.py --journeys-only` (source: `tools/build-site.py` and
  `web/AGENTS.md`).
- Technical: the publication stack is Markdown validated and projected by
  repository Python tooling into Astro marketing content and the documentation
  site (source: `tools/build-site.py`, `web/package.json`, and
  `docs-site/AGENTS.md`).
- Technical: the required frontend-engineering journey, page-contract how-to,
  and performance reference are absent at authoring time (source: read-only
  path probe 2026-08-08).
- Process: RFC-0071 Area E defines the frontend-engineering doctrine and
  ADR-0057 makes the frontend-engineering pack its canonical owner (source:
  `docs/rfc/0071-digital-experience-doctrine.md` and
  `docs/adr/0057-frontend-engineering-pack-promotion-and-resident-deletion.md`).
- Process: a non-cosmetic pack-content change requires synchronized manifest
  version bumps, changelog entry, and regenerated projections (source:
  `packs/AGENTS.md` and `packs/AGENTS.local.md`).
- Product: the implementation remains adopter-facing but begins with a benchmark
  of shipped FE skills; skill and adopter-facing corrections discovered by that
  benchmark are eligible follow-on work, not silent scope expansion (source:
  user confirmation 2026-08-08).
- Product: the performance reference gives surface-specific budgeting guidance
  without inventing universal numeric asset ceilings (source: user confirmation
  2026-08-08).
- Metadata: this is a `ui`-shaped, non-contract feature owned by `eugenelim`
  (source: user confirmation 2026-08-08).
