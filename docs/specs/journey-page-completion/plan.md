# Plan: Journey page completion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Establish the ID-based journey contract and its failure cases first, migrate
all canonical sources through the normal generator, then author the three
priority content additions. Renderer changes consume only canonical IDs and
gate definitions. Full emitted-site tests prove routes and fragments, while a
bounded browser pass proves the user-facing orientation and interaction.

## Constraints

- `packs/*/JOURNEY.md` remains canonical; generated web copies are never edited
  independently.
- `docs/design/principles/tech-site.md` and
  `docs/specs/platform-site/aesthetic-direction.md` govern visual decisions.
- Priority content is limited to `core`, `product-engineering`, and
  `release-engineering`.
- No dependency, public route, or navigation change.
- Every changed pack receives its own patch bump in `pack.toml` and
  `.claude-plugin/plugin.json`; self-hosting runs only after all pack edits.
- Shipped `JOURNEY.md` content carries no internal governance citation.

## Construction tests

**Integration tests:** regenerate journey content, build the marketing site,
assert decision-chip hrefs and gate IDs in emitted HTML, then run combined
page-and-fragment checking.

**Manual verification:** record editorial approval for six content fields and
rendered design review of all three priority routes. Record the programme's
physical-device release gesture separately from deterministic browser tests.

## Design (LLD)

### Design decisions

- `decisionGateIds` is the sole decision-to-gate relationship. Keeping display
  strings as a parallel source is rejected because labels and links drift.
  Traces to: AC1-AC4.
- All journey sources adopt the identifier contract in one migration, while
  new editorial copy remains P1-only. Traces to: AC1, AC5, AC6.

### Data & schema

- Every human gate owns one stable ID; `contract.decisionGateIds` is an ordered
  array of those IDs. Validation rejects duplicates and missing references.
  Traces to: AC1, AC2.
- Optional `eyebrow` and `goodOutputDescription` are required by construction
  tests only for the approved priority IDs. Traces to: AC5, AC6.

### Component / module decomposition

- `JourneyContract.astro` resolves decision IDs to gate labels and emits links.
- `GateDetail.astro` owns the matching fragment target.
- The journey page owns eyebrow and transcript placement without changing the
  route shell. Traces to: AC3-AC5, AC10, AC11.

### State & control flow

- Build-time validation fails before rendering when a decision ID is missing or
  ambiguous. Valid IDs flow from canonical pack source through generated
  content to both chip href and gate DOM ID. Traces to: AC1-AC4, AC8.

### Behavior & rules

- Chip order follows `decisionGateIds`; labels follow gate definitions. IDs do
  not change when a label changes. Traces to: AC2, AC3.
- Editorial fields are authored and reviewed, never synthesized. Traces to:
  AC5, AC6.

### Quality attributes (NFRs)

- Anchor links are keyboard-usable and browser checks enforce the approved
  overflow and axe thresholds. Traces to: AC10.

## Tasks

### T1: Invalid journey gate relationships fail before rendering

**Depends on:** none

**Touches:** web/src/content.config.ts, tools/test_build_site_routing.py, tools/test_catalogue_navigation.py

**Tests:**
- TDD: add failing fixtures for a missing gate ID, duplicate gate ID, duplicate
  decision ID, and display text supplied instead of an ID (AC1, AC2).
- TDD: add a passing fixture that changes a gate label without changing its ID
  (AC2, AC3).

**Approach:**
- Define the internal ID/reference shape and validate referential integrity at
  build time.
- Keep editorial labels on human-gate definitions only.

**Done when:** focused tests demonstrate all invalid relationships fail and the
label-change fixture remains valid.

### T2: Every canonical journey and generated copy uses stable gate IDs

**Depends on:** T1

**Touches:** packs/*/JOURNEY.md, packs/*/pack.toml, packs/*/.claude-plugin/plugin.json, web/src/content/journeys/*.md, tools/build-site.py, marketplace.json, docs/product/changelog.md

**Tests:**
- Goal-based: regenerate all journey copies and assert no source-shape drift remains (AC1,
  AC8).
- Goal-based: validate every ID reference and the complete existing route inventory (AC1,
  AC2, AC11).
- Goal-based: run catalogue lint, verification, self-host projection checks, version
  consistency, and the shipped-content governance-citation check for every
  changed pack (AC9, AC10).

**Approach:**
- Assign explicit semantic IDs to existing gates and replace parallel decision
  display strings with ordered `decisionGateIds`.
- Change canonical sources and let the existing generator project copies.
- Patch-bump every changed pack and its plugin manifest, then run self-host once
  after all pack edits and add the required changelog entries.

**Done when:** generation and catalogue projection are clean, all references
resolve uniquely, version/provenance checks pass, and every pre-change journey
route remains present.

### T3: Priority journeys have reviewed orientation and good-output evidence

**Depends on:** T2

**Touches:** packs/core/JOURNEY.md, packs/product-engineering/JOURNEY.md, packs/release-engineering/JOURNEY.md

**Tests:**
- Goal-based: assert the three exact priority IDs carry non-empty eyebrow and transcript
  fields and non-priority journeys remain optional (AC5, AC6).
- Visual/manual QA: record content review for outcome focus, specificity, and credible evidence
  (AC5, AC13).

**Approach:**
- Author one outcome-led eyebrow and one transcript for each P1 source.
- Regenerate web copies after approval.

**Done when:** all six fields have recorded approval and generated copies match
their canonical sources.

### T4: Decision chips navigate to their canonical gate cards

**Depends on:** T2

**Touches:** web/src/components/journeys/JourneyContract.astro, web/src/components/journeys/GateDetail.astro

**Tests:**
- Goal-based: assert emitted chip labels come from gate definitions, each href targets the
  corresponding gate ID, and every target occurs exactly once (AC2-AC4).
- TDD: seed a broken fragment and prove the combined checker fails (AC4).

**Approach:**
- Resolve IDs once in the journey renderer and pass the stable ID to both link
  and gate card.
- Use ordinary fragment links so keyboard and browser behavior remain native.

**Done when:** emitted HTML and the combined fragment checker prove every chip
lands on exactly one matching gate.

### T5: Living priority IDs and emitted priority pages pass completion evidence

**Depends on:** T3, T4

**Touches:** docs/specs/platform-site/journey-page-template.md, tools/test_build_site_routing.py, web/src/test/e2e/**/*.ts

**Tests:**
- Goal-based: assert the living priority template contains `product-engineering` and
  `release-engineering`, not their stale aliases (AC7).
- Goal-based E2E: exercise the three priority routes at all approved widths for keyboard links,
  overflow, and axe thresholds (AC12).
- Visual/manual QA: run rendered design review against the named aesthetic direction and
  principles (AC13).

**Approach:**
- Correct only the stale template IDs.
- Add deterministic browser assertions without screenshot writes.

**Done when:** the template check, full build/link suite, browser matrix, and
recorded design review all pass.

## Rollout

Land the schema and all-source migration atomically so no generated journey
observes a mixed contract. Editorial and renderer work can follow behind that
contract. Rollback is a normal source revert; no infrastructure changes.

## Risks

- Hand-assigned IDs can accidentally collide; schema fixtures and all-source
  validation make uniqueness a build invariant.
- Editorial transcript scope can expand; exact P1 IDs keep the programme
  bounded.

## Changelog

- 2026-08-17: initial plan after approval of the P1 and canonical gate-ID
  contracts.
