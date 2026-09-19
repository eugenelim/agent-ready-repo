# Spec: architect-design scope-routed model-first templates

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0118
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

An architect using `architect-design` gets a document whose shape matches the
architectural scope they are working at, and whose every section leads with a
model rather than with prose about a model. Success is that the eight
architectural views the pack's own knowledge corpus names each have exactly one
home in the authored artifact, and that a subsystem too large for one document
is split by a stated criterion rather than by page count.

## What Changes

- Scope determination — a new stage in `architect-design/SKILL.md`, before
  Stage 0, resolving altitude and document count
- Three scope templates — `assets/application-system-design.md`,
  `assets/subsystem-design.md`, `assets/architecture-change-design.md`
- `assets/design-doc.md` — retained, and states in its own body that it is an
  unrouted compatibility pointer
- The decomposition rubric and the architecture-set index — one new file,
  `references/decomposition-rubric.md`
- The authoring rubric — `references/design-doc-rubric.md`, re-mapped from the
  eight Google-style sections to the model-first spine
- The reviewing rubric — `architect-review/references/rubric-design-doc.md`,
  re-mapped the same way, and carrying a decomposition check
- The cold reviewer — `.apm/agents/design-reviewer.md` routes a design artifact
  by three scopes
- The skill description's output summary and `evals/evals.json`
- The pack's five prose surfaces and the generated web journey

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the skill's IDE trigger surface states what it produces | `packs/architect/.apm/skills/architect-design/SKILL.md` frontmatter `description` | architect pack maintainer | `test_yagni_contract.py` routing-boundary assertion stays green; the middle read for routing widening | The description names the three-scope model-first output and adds no trigger |
| Current product truth | Applicable — five surfaces promise one Google-style doc | `packs/architect/README.md`, `DESIGN.md`, `JOURNEY.md`, `docs/index.md`, `guides/architect/how-to/shape-an-architecture-concept.md` | architect pack maintainer | No `Google-style` promise remains in architect-owned prose | Every surface describes scope-routed authoring |
| Interface compatibility | Applicable — adopters may reference `assets/design-doc.md` | `packs/architect/.apm/skills/architect-design/assets/design-doc.md` | architect pack maintainer | `test_document_model_contract.py` asserts the file exists and is unrouted | The path resolves and says what it is |
| Decision rationale | Already owned — ADR-0118 records the decision and its alternatives | `docs/adr/0118-architect-design-scope-routed-model-first-templates.md` | repository decision process | No new record; this spec cites the existing one | ADR-0118 needs no amendment for slice 1 |
| Release history | Applicable — pack content changes | `docs/product/changelog.md`, free-standing `## [architect][0.15.11]` | architect pack maintainer | Entry present with an explicit `### Highlights` block | Entry is top-level, never nested under `[Unreleased]` |
| Projection | Applicable — the public journey is generated | `web/src/content/journeys/architect.md` | `tools/build-site.py --journeys-only` | Regenerated output matches `packs/architect/JOURNEY.md` | `build-check` reports no staleness |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Use the names ADR-0118 fixes — the three asset filenames, the eleven
  subsystem section names in their recorded order, and the criteria `D1`
  through `D6` — exactly as recorded, without local renaming.
- State a rule directly in `packs/` rather than citing ADR-0118 there, and run
  the `packs/AGENTS.local.md` internal-citation grep before committing.
- Regenerate the web journey with `python3 tools/build-site.py --journeys-only`
  after any edit to `packs/architect/JOURNEY.md`.
- Bump `packs/architect/pack.toml` and `.claude-plugin/plugin.json` to the same
  version, then run `FORCE=1 make build-self`.

### Ask first

- Any edit to the skill description's invocation sentence, trigger list, or
  `Do NOT use` refusal — those three are routing authority, and changing them
  means scope work has grown into routing.
- Any change to `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`
  or to the OKF corpus ontology pinned by `test_architecture_lenses_corpus.py`.
- Adding a semantic role, an OKF concept, or an OKF category.

### Never do

- Add a size or density threshold, a paragraph budget, or any of the `DA1`
  through `DA10` document-architecture gates — slice 2 owns them, and a size
  trigger added here would give `D1`-`D6` a second, uncoordinated caller.
- Delete or rename `assets/design-doc.md`.
- Edit inside the `agentbundle:output-rendering` markers in `SKILL.md`, which
  `tools/add-rendering-directives.py` regenerates byte-for-byte.
- Reintroduce a positional text split in
  `test_architect_design_skill_engineering_reference_boundary.py`, or drop the
  provider block's opening scope restriction when restructuring the procedure.
- Use Mermaid's `C4Context`, `C4Container`, or `architecture-beta` directives in
  a design asset.

## Testing Strategy

- **Scope routing — `SKILL.md` resolves altitude and document count before template choice (AC-0021, AC-0022, AC-0023, AC-0024): TDD.** The ordering is a compressible invariant over the
  file's text — the scope stage's position relative to Stage 0 and to the
  template-selection step is decidable by index comparison, so a test can red
  on a reordering that prose review would pass.
- **The active-template inventory and the common spine (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0041, AC-0042): TDD.** An exact set
  comparison is the only check that fails when a fourth template is added
  silently or a spine section is dropped; a substring sweep would pass on a
  partial spine.
- **The `D1`-`D6` criteria, the mandatory-`D1` rule, the size-alone-never-splits refusal, and what a parent retains (AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020): TDD.** These are the load-bearing
  regression: the negative case asserts the refusal survives, and it is the one
  a later size-trigger slice could silently invert.
- **The C4-directive refusal inside design assets (AC-0013): TDD.** The pack already
  ships and tests that syntax in `architect-diagram` testdata, so the reuse path
  is live; a per-asset scan is what makes it fail rather than propagate.
- **The rubric re-mapping and the reviewer mirror (AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0031, AC-0032, AC-0033): goal-based check.** The
  outcome is that no rubric check names a section the templates lack and that
  the reviewer recognises three scopes — a text assertion over the three files
  decides it, and no behavior exists to drive.
- **Description, docs, projection and release surface (AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040): goal-based check.** The absence of the
  `Google-style` promise across architect-owned prose is a `grep`, and the
  journey projection's freshness is `build-check`'s own staleness check.
- **The skill as an invoked artifact: visual / manual QA.** A skill is
  instructions a model reads, so the built artifact is exercised by reading the
  authored templates end to end against the spine and confirming each section
  leads with its named question — a passing text assertion does not show that
  the questions are answerable.

## Acceptance Criteria

- [x] **AC-0001.** `packs/architect/.apm/skills/architect-design/assets/` contains exactly
      four Markdown assets besides `concept.md`: `application-system-design.md`,
      `subsystem-design.md`, `architecture-change-design.md`, and
      `design-doc.md`.
- [x] **AC-0002.** `assets/design-doc.md` states in its own body that it is a retained,
      unrouted compatibility pointer and names the three routed templates.
- [x] **AC-0003.** `assets/subsystem-design.md` carries the eleven ADR-0118 section names as
      headings in the recorded order: Scope and Context, Structural Model,
      Runtime Model, Contracts and Invariants, Data and State, Deployment and
      Operations, Quality Scenarios and Verification, Implementation Mapping,
      Decisions, Alternatives, and Risks, Rollout, Migration, and Reversal,
      Open Questions.
- [x] **AC-0004.** Each section of each routed template opens with an interrogative sentence
      — the named question that section answers — before any other prose.
- [x] **AC-0005.** `assets/subsystem-design.md`'s Contracts and Invariants section carries a
      table whose header names semantic name, parties, inputs/outputs, identity,
      compatibility, failure semantics, invariant, enforcement, and verification.
- [x] **AC-0006.** `assets/subsystem-design.md`'s Data and State section requires the word
      `stateless` to be written explicitly when an element holds no state, rather
      than left implied by an absent row.
- [x] **AC-0007.** `assets/subsystem-design.md`'s Runtime Model section requires at least one
      normal-path and one failure-or-recovery-path sequence diagram.
- [x] **AC-0008.** `assets/subsystem-design.md`'s Quality Scenarios and Verification section
      carries all six scenario parts — source, stimulus, environment, artifact,
      response, measurable target — plus business consequence, mechanism, and
      verification.
- [x] **AC-0009.** `assets/application-system-design.md`'s element-catalogue table
      admits exactly the element types Person, System, and Container.
- [x] **AC-0041.** `assets/application-system-design.md` carries no internal
      component inventory, no file-or-module mapping, and no ports/adapters
      section.
- [x] **AC-0042.** Every model-bearing section carries exactly one
      `<!-- model -->` token and exactly one `<!-- rationale -->` token, and the
      model token's index is lower. The model-bearing set is fixed here, not
      read from the templates: in `subsystem-design.md` and
      `application-system-design.md` it is Scope and Context, Structural Model,
      Runtime Model, Contracts and Invariants, Data and State, Deployment and
      Operations, Quality Scenarios and Verification, and Implementation
      Mapping; in `architecture-change-design.md` it is all eight sections.
      Decisions, Alternatives, and Risks, Rollout, Migration, and Reversal, and
      Open Questions are excluded because they carry no model.
- [x] **AC-0010.** `assets/architecture-change-design.md` requires the authoritative
      current-architecture artifact in its header.
- [x] **AC-0011.** `assets/architecture-change-design.md` carries the eight delta-shaped
      section names: Scope and Baseline, Structural Change, Runtime Change,
      Contract and Invariant Change, Data/State Migration,
      Deployment/Operational Change, Quality Regression and Verification,
      Build Mapping.
- [x] **AC-0012.** No routed template carries a section named `Appendix`.
- [x] **AC-0013.** No routed template contains the Mermaid directives `C4Context`,
      `C4Container`, or `architecture-beta`.
- [x] **AC-0014.** `references/decomposition-rubric.md` defines the six criteria `D1` through
      `D6` with the meanings ADR-0118 records.
- [x] **AC-0015.** `references/decomposition-rubric.md` states that a child earns its own
      document only when it meets `D1` plus at least one other criterion.
- [x] **AC-0016.** `references/decomposition-rubric.md` states that `D1` is also the
      recursion's stopping rule — the descent terminates when no remaining child
      has a live architectural decision of its own.
- [x] **AC-0017.** `references/decomposition-rubric.md` carries the three refusals: `D1`
      unmet, one contract given two homes, and a child that is only large.
- [x] **AC-0018.** `references/decomposition-rubric.md` states that size alone never
      justifies a split.
- [x] **AC-0019.** `references/decomposition-rubric.md` states that a parent retains the
      scope table, the structural model with children as named elements, the
      contracts between children, the cross-child invariants, and the links.
- [x] **AC-0020.** `references/decomposition-rubric.md` states that a parent does not restate
      child internals.
- [x] **AC-0021.** `SKILL.md` resolves architectural scope — altitude and document count —
      in a stage whose text appears before the Stage 0 heading.
- [x] **AC-0022.** `SKILL.md`'s scope stage names the three altitudes:
      application/system, subsystem, and architecture change.
- [x] **AC-0023.** `SKILL.md`'s scope stage routes document count through
      `references/decomposition-rubric.md`.
- [x] **AC-0024.** `SKILL.md` selects a template only after scope is resolved, so the
      template-selection text appears after the scope stage's text.
- [x] **AC-0025.** Every `##` heading in `references/design-doc-rubric.md`, other
      than the two cross-cutting headings `Cross-cutting` and `Decomposition`,
      appears in the union of the three routed templates' `##` headings. The
      comparison set is that union, derived by parsing the three assets, so a
      heading naming a retired section fails.
- [x] **AC-0026.** `references/design-doc-rubric.md` carries a `- [ ]` checklist
      item requiring the complete model set plus Implementation Mapping to be
      sufficient to implement from. The checklist-item form is the assertion, so
      the phrase in a comment or a quotation does not satisfy it.
- [x] **AC-0027.** `references/design-doc-rubric.md` carries a `- [ ]` checklist
      item requiring every diagram to state one named question and one zoom
      level.
- [x] **AC-0028.** `references/design-doc-rubric.md` carries a `- [ ]` checklist
      item requiring Open Questions to be omitted when empty.
- [x] **AC-0029.** `references/design-doc-rubric.md` carries a `- [ ]` checklist
      item naming the structured header fields Decision sought and Title.
- [x] **AC-0031.** Every `##` heading in
      `architect-review/references/rubric-design-doc.md`, other than
      `Cross-cutting`, `Decomposition`, and `Severity mapping (typical)`,
      appears in the union of the three routed templates' `##` headings, derived
      by the same parse as AC-0025.
- [x] **AC-0032.** `architect-review/references/rubric-design-doc.md` carries the `D1`
      through `D6` criteria so a reviewer can raise that a document should have
      been several.
- [x] **AC-0033.** `.apm/agents/design-reviewer.md` and
      `architect-review/SKILL.md` each route a design artifact by the three
      scope names, and neither carries the string `Google-style`.
- [x] **AC-0034.** `SKILL.md`'s description names the three routed scopes and
      model-first authoring as what the skill produces. The invocation sentence,
      trigger list, and `Do NOT use` refusal are held byte-stable by
      `test_yagni_contract.py`'s `routing_head`/`routing_tail` equality, which
      owns that half.
- [x] **AC-0035.** `evals/evals.json` eval 1 requires model-first scope-routed output rather
      than the eight Google-style sections.
- [x] **AC-0036.** `evals/evals.json` carries one eval per routed template, each asserting
      that the model precedes its rationale.
- [x] **AC-0037.** No architect-owned prose surface promises a `Google-style` design doc:
      `README.md`, `DESIGN.md`, `JOURNEY.md`, `docs/index.md`, and
      `guides/architect/how-to/shape-an-architecture-concept.md`.
- [x] **AC-0038.** `web/src/content/journeys/architect.md` is regenerated from
      `packs/architect/JOURNEY.md` and reports no staleness.
- [x] **AC-0039.** `packs/architect/pack.toml` declares version `0.15.11`. Their
      equality with `.claude-plugin/plugin.json` is owned by
      `tests/conformance/test_pack_metadata.py`.
- [x] **AC-0040.** `docs/product/changelog.md` carries a free-standing `## [architect][0.15.11]`
      entry with a `### Highlights` subsection.

### Boundary note — rubric checks are not the `DA` gates

AC-0026 and AC-0027 place an implementation-sufficiency check and a
diagram-question check in the authoring rubric. These overlap in substance with
the `DA8` and `DA7` document-architecture gates that ADR-0118 reserves for
slice 2. They are carried here because the four checks the old rubric loses
have to land somewhere, and a rubric left with a hole is the defect this slice
exists to fix. They are rubric checklist items only: this slice adds no `DA`
identifier, no gate reporting, and no gate-ID parity, so slice 2 still owns the
gates and may supersede these two items when it lands.

## Follow-ons

- architect pack maintainer: slice 2, tracked by ADR-0118 `D5` — the `DA1`
  through `DA10` document-architecture gates, including the `DA10` size trigger
  that invokes this slice's `D1`-`D6` rubric.
- architect pack maintainer: slice 3, tracked by ADR-0118 — the system-shape and
  workload axes and the conditional ports-and-adapters view.

## Assumptions

- Process: `packs/architect/tests/skills/architect-design/` does not run on a
  pull request — `build-check` runs only `packs/architect/tests/pack/` and
  `.../architect-assess/` — so this slice's three new suites are proven only by
  a dispatched `test-corpus` run, and a later PR touching these files can merge
  green while breaking them. Moving the directory into `build-check` is a
  gate-chain change this spec does not make.
