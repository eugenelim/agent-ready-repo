# Plan: Architecture and decision surface portability

- **Spec:** [spec.md](spec.md)
- **Status:** Done
- **Repository anchors:** `ARCHITECTURE.md` and
  `docs/architecture/work-intake-and-artifact-routing.md` own the routing
  boundary; `contracts/jsonschema/semantic-surface-resolution.schema.json` and
  `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py` are the
  unchanged published contract and implementation; `packs/architect/DESIGN.md`
  and Architect skill save sections own design/current-architecture guidance;
  `packs/governance-extras/.apm/skills/new-adr/SKILL.md` owns ADR creation. Named
  deviation: Architect currently collapses designs, diagrams, and assessments
  under one `[architecture] output_dir`, while `new-adr` recognizes custom ADR
  locations only inside a catalogue-default procedure. Wave 3 replaces those
  universal path claims with role-aware resolution and explicit standalone
  modes, without changing either authoring method.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Land Wave 3 in four dependency-ordered tasks. First create the cross-surface
construction harness around the real shipped resolver, pin its contract bytes,
and express custom-location, policy, external, ambiguity, absence, and
boundary-change expectations before prompt changes. Second migrate Architect's
three output-producing skills and living pack documentation to the three
semantic roles and four operating modes while preserving every reasoning and
write gate. Third migrate `new-adr` and the smallest set of Core/specialist
architecture consumers so boundary changes can hand current architecture and
decision records to their existing methods without product prose. Fourth close
the portable matrix, adopter/current-state documentation, release metadata, and
source-generated projections, then run the authority-derived gate set and
installed `.agents/` exercises.

The design deliberately has no new runtime resolver or published contract. A
compatible repository workflow gathers bounded candidate/evidence records and
passes them to Wave 1; a standalone Architect workflow names its reduced
authority. This avoids turning a user-scope pack into a hidden Core dependency
while preventing its personal-workspace convenience path from masquerading as
repository policy resolution.

## Constraints

- RFC-0096 sections 2, 4, 8, and 9 fix the roles, precedence, portability,
  representative boundary-change case, and Wave 3 scope.
- The shipped Wave 1 resolver and `semantic-surface-resolution.v1` are consumed
  by reference and remain byte-for-byte unchanged. Their candidate/evidence
  bounds, confinement, stable dispositions, and authority model are not widened.
- Architect remains default user-scope and independently useful. Core remains
  optional for it; no mandatory pack dependency or global registry is added.
- Existing `agentbundle-layout.toml` adapters remain optional. No configuration
  or suitable durable surface is silently created.
- Architecture design, assessment, diagram, review, and ADR authoring methods
  remain unchanged. Only role selection, destination resolution, and related
  receipts/guidance migrate.
- Source, write, and deletion authority remain independent; external locators
  remain opaque and external; untrusted content cannot select a role,
  destination, tool, or write action.
- No Wave 4+ lifecycle behavior, top-level directory, dependency, product
  direction artifact, research artifact, or Wave-3 ADR is introduced.
- Pack content changes update affected pack/plugin versions once against the
  then-current base, update the literal core-version roster and top changelog
  entry when applicable, and regenerate projections only from source.
- Git metadata stays read-only. The base-freshness check remains intentionally
  skipped because this environment cannot fetch or update refs.

## Construction tests

**Integration tests:**

- `tests/roster/` owns cross-pack and repository-level tests; no pack test reads
  above its declaring pack and no conformance test names a shipped pack.
- A table-driven fixture matrix calls the real Wave 1 resolver for all claimed
  repository resolutions and asserts the complete role, locator, provenance,
  evidence, capability, confinement, revision, confirmation, and independent
  authority result consumed by each prompt surface.
- The matrix fingerprints fixture roots before and after terminal outcomes and
  proves zero artifacts, directories, indexes, configuration, or product prose
  for refusal, ambiguity, absence, unsafe, and prompt-injection cases.
- Contract-preservation assertions hash the resolver and schema from the base
  and fail if Wave 3 changes either.
- Pack-local tests/evals assert role/mode prose, method invariants, metadata
  boundaries, source/install parity, and the absence of universal catalogue-path
  claims.

**Manual verification:**

- Exercise installed `architect-design` in chat-only mode and confirm its
  receipt reports no write.
- Exercise installed Architect with an explicit personal-workspace fixture and
  confirm it surfaces the absolute destination and personal authority without
  claiming a Wave 1 result.
- Exercise installed Architect in repository fixtures with and without
  compatible Core; confirm the former reports a real Wave 1 resolution and the
  latter stops for confirmation or renders a portable handoff.
- Exercise installed `new-adr` against a custom ADR destination and confirm
  destination resolution precedes ordinal/index work and the preview gate
  remains.
- Exercise the boundary-change fixture and confirm it selects current
  architecture and decision-record outputs only, with no product-prose route.

## Design (LLD)

### Design decisions

- Use the three existing Wave 1 roles directly. `architect-design` and proposed
  or future diagrams select `architecture-design`; documentation of the
  implemented system selects `current-architecture`; `new-adr` selects
  `decision-record`. `architect-assess` classifies the saved artifact rather
  than the skill name: a canonical current-state model/report selects
  `current-architecture`, while a remediation or future-change proposal selects
  `architecture-design`; a mixed report requires an explicit save choice and is
  never silently installed as current architecture. Traces to: AC1, AC10-AC13.
- Treat the Wave 1 result as an opaque complete record. Prompts may render and
  act on its disposition, but do not recompute precedence, confinement,
  capability, or authority. Traces to: AC2-AC8.
- Preserve Architect's user-pack value through an operating-mode branch before
  destination work. Chat-only never resolves a write; a personal workspace uses
  a user-supplied/user-configured explicit location and labels it personal;
  compatible repository Core uses Wave 1; incompatible or absent Core produces
  confirmation/handoff rather than simulated resolution. Traces to: AC5, AC9.
- Keep existing method gates after resolution. ADR numbering and sibling-index
  selection happen inside the resolved decision-record destination; design
  stages, reviews, and per-effort folders happen inside the resolved
  architecture-design destination. Traces to: AC8, AC10, AC12.
- Route the representative boundary change as two independent applicable
  outputs, not one multi-role document and not an automatic authoring command.
  Each workflow retains its own confirmation and content method. Traces to:
  AC1, AC8, AC11-AC14.
- Put non-mechanical intent in its living owner during implementation. Pack
  DESIGN and skill prose move with behavior; adopter docs move with the
  capability; contributor architecture waits until the implemented route is
  true; release history waits until versions settle. Traces to: AC15-AC17.

### Interfaces & contracts

No new or modified published JSON contract is introduced. The repository mode
consumes `semantic-surface-resolution.v1`, whose complete existing result is the
only machine contract for a claimed resolution. Candidate acquisition remains a
trusted-caller responsibility and stays within Wave 1 bounds.

The prompt-level operating-mode result is deliberately descriptive rather than a
new schema:

- `chat-only`: role may be discussed; no locator or write is resolved;
- `personal-workspace`: exact explicit/user-owned locator is surfaced and
  confirmed; an exact directory becomes the canonical confinement root and an
  exact file the sole target, with every derived child rechecked after symlink
  resolution; receipt states that it is not repository-authoritative;
- `repository-resolved`: compatible Core returns and the workflow renders the
  unchanged Wave 1 result before its existing write gate;
- `repository-handoff`: Core is absent/incompatible, so the workflow states the
  requested role plus bounded evidence and asks the user/Core-capable workflow
  to resolve it; it never labels this a Wave 1 result.

Existing layout settings act only as candidate adapters. A repository layout
value is evidence for declared configuration and remains subject to mandatory
policy and Wave 1 confinement. A user-profile value is eligible only for the
personal-workspace mode unless the repository independently declares it.

### Failure, edge cases & resilience

- A mandatory-policy conflict, unsafe local path, contradictory evidence, forged
  or malformed resolver result, unsupported role, symlink escape, or
  unconfirmed external write stops before all effects and retains the stable
  Wave 1 disposition where available.
- Ambiguity asks which permitted destination applies. Absence offers selection
  or creation but performs neither. A declined save remains chat-only.
- A missing or incompatible Core capability is normal for Architect. The skill
  emits a truthful repository handoff/confirmation path and does not import Core,
  copy the resolver, or silently reinterpret personal config as repository
  policy.
- Prompt-like text in a design, current architecture document, ADR context,
  repository instruction, or analogue is untrusted data and cannot choose a
  destination or authorize a tool/write.
- External destinations remain opaque. The workflow may report their locator
  and capability facts from Wave 1 but does not fetch, probe, credential-resolve,
  or coerce them into local paths.
- Destination resolution does not mean the artifact is applicable, approved, or
  ready to write. Existing authoring and confirmation gates still decide that.
- Personal-workspace canonicalization or confinement uncertainty fails closed
  before folder creation or write. Symlink, junction/reparse-point, exact-file
  mismatch, or an escaping derived child produces a bounded redacted stop and no
  fallback path.

### Dependencies & integration

- Core work-intake owns the shared resolver and its contract. Wave 3 changes no
  Core resolver code or schema; bounded Core prompt guidance may expose the
  existing capability to consumers.
- Architect owns design, assessment, and diagram role selection, standalone
  operating modes, personal-workspace behavior, and pack-facing documentation.
- governance-extras owns decision-record destination consumption and the ADR
  method after resolution. Its existing Core dependency is not widened.
- `init-project`, `adapt-to-project`, `new-package`, and `generate-iac` are
  candidate bounded consumers only where their current behavior creates or
  updates current architecture or decision records. They may delegate to the
  owning workflows but do not gain a second authoring method.
- Public guides explain adopter behavior; contributor architecture explains the
  current routing boundary only once it is implemented. Product docs and project
  knowledge receive nothing from Wave 3 unless an independent existing gate
  applies outside this work.

## Tasks

### T1: Pin the unchanged resolver and materialize the portable destination matrix

**Depends on:** none

**Touches:** `tests/roster/test_architecture_decision_surface_portability.py`,
`tests/roster/fixtures/architecture-decision-surface-portability/**`

**Verification mode:** TDD — the three-role precedence and zero-effect matrix is
a finite integration contract around a shipped resolver.

**Tests:**

- stub: true
- Hash assertions pin the Wave 1 resolver and schema to the pre-Wave-3 bytes
  while the test imports/calls the real resolver (AC2).
- Role-parametrized cases cover explicit, policy, repository convention,
  external convention, ambiguity, absence, mandatory-policy conflict,
  contradiction, and unsafe paths with complete result assertions (AC1-AC7).
- Operating-mode cases pin truthful receipts and prohibit claimed Wave 1 results
  outside compatible repository mode; personal-root/file cases include symlink,
  escaping-child, and exact-file mismatch refusals (AC7, AC9).
- The boundary case requests current architecture and a decision record and
  asserts no product-prose role or locator (AC13-AC14).
- Terminal cases compare before/after filesystem fingerprints and record no
  mutation callbacks (AC8, AC14).
- stub: materialized, collected, and red — the first test fails on the current
  hard-coded/collapsed prompt surfaces, not because the shipped resolver is
  absent.

**Approach:**

- Add repository-owned fixture roots with generic adopter paths and policy
  evidence; keep cross-pack reads in `tests/roster/`.
- Reuse Wave 1 candidate/evidence builders or contract fixtures by import where
  stable; do not copy resolver logic into test helpers.
- Assert prompt/source behavior by stable semantic markers and forbidden claims,
  not entire-file snapshots.

**Done when:** the matrix is collected, the shipped resolver cases pass, and the
consumer-surface assertions are red for the expected Wave 3 gaps.

### T2: Migrate Architect destinations while preserving independent user-pack operation

**Depends on:** T1

**Touches:** `packs/architect/.apm/skills/architect-design/SKILL.md`,
`packs/architect/.apm/skills/architect-assess/SKILL.md`,
`packs/architect/.apm/skills/architect-assess/references/output-layout.md`,
`packs/architect/.apm/skills/architect-diagram/SKILL.md`, affected Architect
evals/tests, `packs/architect/DESIGN.md`, `packs/architect/README.md`,
`packs/architect/JOURNEY.md`, Architect public guides

**Verification mode:** goal-based prompt/eval testing plus T1 integration — the
method is prose-owned, while resolution claims are exercised with the real
resolver.

**Tests:**

- no stub (goal-based; T1 is the executable red contract).
- Each skill selects the correct role and branches across the four AC9 modes
  before destination work (AC1-AC9).
- `architect-assess` evals separately cover a canonical current-state
  model/report (`current-architecture`), a remediation or future-change
  proposal (`architecture-design`), and mixed output. Mixed output requires an
  explicit role/save choice and invokes no current-architecture write tool until
  that choice is confirmed (AC1, AC8, AC10-AC11).
- Existing stage, rubric, template, review, save-offer, per-effort-folder, and
  receipt markers remain; no method step disappears or changes order except that
  resolution precedes mutation (AC8, AC10-AC11).
- User-profile config is personal-workspace evidence, repo config is a bounded
  repository candidate, missing config is normal, and no config is silently
  created (AC4-AC6, AC9).
- Prompt-injection, incompatible-Core, declined-save, ambiguity, and refusal
  evals prove truthful receipts and zero write tools; personal-workspace tests
  canonicalize the exact confirmed root/file and reject symlink or child escapes
  before any folder creation (AC7-AC10, AC14).
- DESIGN, README, JOURNEY, and guide assertions use the same roles/modes and no
  longer claim one architecture output path for all artifacts (AC15-AC16).

**Approach:**

- Replace each hard-coded resolution block with the shared role/mode doctrine,
  referring compatible repository resolution to Core by capability rather than
  importing its Python or requiring its pack.
- Keep each skill's established content method and organization after the
  destination gate. Classify each saved output by actual intent: an assessment's
  canonical current-state model/report uses `current-architecture`; its
  remediation/future-change proposal uses `architecture-design`; mixed output
  requires an explicit save choice and is not silently published into the
  current-state surface.
- Reconcile the diagram guide/source drift and update pack DESIGN first in this
  implementation task so solution intent and behavior change atomically.

**Done when:** Architect passes its affected suites/evals in all four modes, T1's
Architect cases are green, and the pack remains installable at user scope without
Core.

### T3: Migrate decision records and bounded architecture consumers

**Depends on:** T2

**Touches:** `packs/governance-extras/.apm/skills/new-adr/SKILL.md`, its exact
pack-local tests/evals and pack docs;
`packs/core/.apm/skills/work-intake/{SKILL.md,evals/evals.json,evals/eval_queries.json}`;
`packs/core/.apm/skills/init-project/{SKILL.md,evals/eval_queries.json}`;
`packs/core/.apm/skills/adapt-to-project/{SKILL.md,evals/eval_queries.json}`;
`packs/monorepo-extras/.apm/skills/new-package/{SKILL.md,evals/eval_queries.json}`;
`packs/iac-terraform/.apm/skills/generate-iac/SKILL.md`; exact affected guides
and eval assertions. Explicitly excluded from this task and every other task:
`packs/core/.apm/skills/work-intake/scripts/surface_resolver.py` and
`contracts/jsonschema/semantic-surface-resolution.schema.json`.

**Verification mode:** TDD for ADR destination-before-identity invariants;
goal-based integration for prompt consumers.

**Tests:**

- stub: true
- `new-adr` resolves `decision-record` before ordinal/index work and uses the
  resolved destination's own numbering/index conventions; its existing framing,
  template, lifecycle, preview, and confirmation behavior remains (AC3-AC8,
  AC12).
- Custom repository and external ADR destinations outrank catalogue defaults;
  mandatory-policy conflict, ambiguity, absence, and unsafe results invoke no
  ordinal helper, index read, directory creation, or write (AC4-AC8, AC12,
  AC14).
- Bounded consumers request `current-architecture` or `decision-record` from the
  owning route and do not hard-code catalogue paths as universal locations or
  invent product prose (AC11, AC13, AC15).
- Boundary-change evaluation produces two independent applicable handoffs with
  their own gates and no multi-role file (AC1, AC8, AC13-AC14).
- stub: materialized, collected, and red — a governance pack test proves the
  ordinal helper is currently described/invoked before semantic resolution.

**Approach:**

- Reorder `new-adr` destination resolution ahead of ordinal/filename/index work,
  then preserve its current authoring procedure within the resolved destination.
- Update only consumers whose present workflow actually creates or updates one
  of the three roles. Delegate to owners instead of copying ADR or architecture
  methods.
- Do not edit any Core work-intake script or the semantic-surface schema; Core
  changes in this task are limited to the exact prompt/eval files named above.
- Keep external destinations non-mutating unless the current invocation already
  has a separately authorized write adapter and explicit confirmation; Wave 3
  adds no transport.

**Done when:** governance tests/evals and T1's decision/boundary cases are green,
all bounded consumers name roles rather than universal paths, and no product
prose or later-wave output appears.

### T4: Close documentation, release, projection, and authority-derived gates

**Depends on:** T3

**Touches:** `docs/architecture/work-intake-and-artifact-routing.md`, relevant
maintainer/adopter guides, affected pack/plugin manifests, affected eval rosters,
`docs/product/changelog.md`, generated projections, T1 completion matrix, this
spec/plan and workspace registration

**Verification mode:** goal-based release/integration closure plus installed
artifact manual QA.

**Tests:**

- no stub (goal-based/manual QA).
- Current-state contributor architecture describes only implemented Wave 3
  ownership and explicitly preserves the Wave 1 resolver boundary (AC2, AC16).
- Pack docs and public guides state roles, precedence, modes, refusals, and custom
  locations consistently; any new guide blockquote is registered in both typed
  aside ledgers (AC15-AC16).
- Version, plugin, eval, changelog, and generated projections are synchronized;
  the old version string is searched repository-wide and pinned roster surfaces
  are updated where needed (AC17).
- Every touched boundary-crossing skill declares its actual
  `metadata.boundaries` in canonical source frontmatter, and build/projection
  tests prove all installed platform variants retain and revalidate it (AC17).
- Catalogue `lint` and `verify` run independently; pack integration records, if
  touched, resolve consumers inside the declaring pack and providers inside the
  target pack (AC17).
- Installed `.agents/` end-to-end exercises cover the four Architect modes,
  custom ADR destination, and boundary-change handoff (AC9, AC12-AC17).
- Every authority-derived lint, type, catalogue, boundary, curation, spec-status,
  test, site, rendered-output, and affected pack/eval gate executes rather than
  returning a void lease result (AC14-AC18).

**Approach:**

- Update contributor architecture only after T2/T3 behavior exists, in the same
  change. Add changelog entries only after reading and setting the then-current
  versions.
- Regenerate `.agents/`, `.claude/`, `.codex/`, and package projections solely
  through the repository generators; never hand-edit them. Run generation twice
  and require the second pass to have no drift.
- Re-derive final gates from `make test-unleased`, current workflows, and scoped
  instruction blocks. Run the user-mandated commands separately so a lease skip
  or `catalogue lint` success cannot mask another gate.

**Done when:** the full matrix and all executed gates are green except an exact
confirmed pre-existing environment skip, reviewers are clean, installed
surfaces pass, and the diff contains no Wave 4+ or method-redesign behavior.

## Rollout

- **Delivery:** prompt/guide and pack release migration. Repositories with
  compatible Core gain exact shared resolution; standalone Architect users keep
  chat and explicit personal-workspace behavior; incompatible repositories get
  a truthful confirmation/handoff path.
- **Infrastructure:** none.
- **External-system integration:** none. External locators remain opaque and no
  transport, credential, fetch, or mutation adapter is added.
- **Deployment sequencing:** T1 pins evidence; T2 makes Architect independently
  portable; T3 migrates ADRs and bounded consumers; T4 publishes docs, versions,
  projections, and integration proof. Affected packs remain independently
  installable according to their existing dependency declarations.
- **Rollback:** revert prompt, guide, fixture, manifest, version, and generated
  projection changes as one ordinary change. No schema, data migration,
  lifecycle state, external write, or repository configuration requires repair.

## Risks

- Prompt consumers could accidentally reimplement resolver precedence. Mitigation:
  pin resolver/schema bytes, call the real resolver in integration tests, and
  forbid pack-local equivalent logic.
- Architect's user scope could be broken by assuming Core. Mitigation: make the
  operating mode explicit and test Core absence as a first-class supported case.
- Personal config could be mistaken for repository policy. Mitigation: personal
  mode labels its authority and repository mode admits only evidence resolved by
  Wave 1.
- ADR numbering could be selected in the wrong directory. Mitigation: test that
  no ordinal/index operation occurs before decision-record resolution and use
  destination-local conventions afterward.
- A design proposal could overwrite current-state architecture. Mitigation:
  role assertions distinguish proposed/future from implemented/current requests.
- Boundary routing could invent product documentation. Mitigation: the
  completion matrix has a closed permitted-role set and zero product-prose
  effects.
- Concurrent pack work could claim versions or change generated pins.
  Mitigation: re-query peer readiness and current local refs before version work,
  read versions immediately before the single bump, and preserve unrelated
  changes.
- A green command could represent an unexecuted coordination lease. Mitigation:
  inspect output for actual collection/execution and rerun only under a supported
  non-void path.

## Gate derivation and verification record

The final gate set is derived from the current `Makefile` `test-unleased` body,
every current `.github/workflows/` workflow, root/scoped instruction command
blocks, and the diff. At minimum it includes:

- `make lint-ruff`
- `make lint-mypy`
- `python3 -m agentbundle catalogue verify --root .`
- `python3 -m agentbundle catalogue lint --deep`
- `python3 tools/lint-pack-test-boundary.py`
- `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main`
- `python3 .agents/skills/work-loop/scripts/lint-spec-status.py --root .`
- `python3 -m pytest tests/ -q`
- affected Core, Architect, governance-extras, monorepo-extras, and
  iac-terraform suites/evals discovered from the current tree
- `make test-unleased` and applicable workflow-only helper gates
- source build/self-host drift checks and a second no-drift regeneration
- `make site-build`
- `cd web` then `npx vitest run src/test/rendered-output.test.ts`
- installed `.agents/` end-to-end exercises

For any generated `packages/agentbundle/agentbundle/_data/` change, the eventual
commit requires the `Engine-Change-RFC: RFC-0096` trailer. This session cannot
write Git metadata, so the final handoff must name that requirement if it
applies. The known ungated typed-aside ledger row-count failure is not accepted
as evidence for any gated command.

## Work-loop decision record

- **Files expected:** the Wave 3 spec/plan/registration; cross-pack fixtures in
  `tests/roster/`; Architect source skills/evals/docs; governance `new-adr`
  source/tests/docs; bounded Core/specialist consumer prompts; current
  architecture/adopter guides; affected manifests/changelog; generated
  projections.
- **Tests that demonstrate done:** the real-resolver three-role matrix; four-mode
  Architect evals; destination-before-ordinal ADR tests; boundary-change
  dual-output/zero-product-prose fixtures; source/projection parity; full
  authority-derived gates and installed-surface invocations.
- **Not changing:** Wave 1 resolver/schema/vocabulary; architecture or ADR
  reasoning methods; required pack dependencies; configuration requirements;
  product intent/history policy; project-knowledge gates; work-loop/lifecycle
  behavior; external transports; Wave 4+.
- **Temptation: add a shared architecture resolver to Architect.** Declined
  because Wave 1 already owns resolution and a user-pack copy would drift.
- **Temptation: require Core for all Architect writes.** Declined because
  Architect is an independently usable user pack; explicit personal mode and a
  truthful repository handoff preserve that contract.
- **Temptation: treat `[architecture] output_dir` as a universal registry.**
  Declined because RFC-0096 says current configuration is insufficient and the
  three roles have separate owners.
- **Temptation: add an ADR for Wave 3 itself.** Declined because this work applies
  an accepted RFC and introduces no new architectural choice beyond its
  confirmed implementation mode.
- **Temptation: use the boundary case to update product docs.** Declined because
  RFC-0096 explicitly separates architecture/decision surfaces from product
  prose.
- **Expected review shape:** DEEP but below 2,000 reviewable behavior/test lines.
  Four dependency-ordered tasks keep fixtures, user-pack migration, ADR/consumer
  migration, and release closure reviewable; no WIDE transformation is planned.

## Resolve-vs-surface disposition

| Discovery | Intent fit | Decision | Disposition |
| --- | --- | --- | --- |
| Architect is a default user-scope pack with no required Core dependency. | Matches portability | Include | Four explicit modes preserve chat/personal use and use Wave 1 only where compatible Core exists. |
| Architect currently uses one `[architecture] output_dir` for designs, diagrams, and assessments. | Conflicts with role separation | Resolve | Treat it as optional candidate evidence, separate semantic roles, and remove universal-path claims. |
| `new-adr` already looks for non-default ADR locations but starts from a `docs/adr/` procedure. | Matches method, weak routing | Resolve | Move decision-record resolution before ordinal/index work; preserve all later ADR steps. |
| Wave 1 already implements the required precedence and confinement result. | Matches dependency | Preserve | Pin and call it; make no resolver/schema change. |
| A boundary change can require both current architecture and an ADR. | Matches representative case | Include | Produce two independently gated role handoffs and explicitly exclude product prose. |
| Living docs should lead non-mechanical intent. | Matches repository doctrine | Include | Spec/plan now; pack DESIGN with behavior; adopter docs in the capability task; current architecture after behavior exists; changelog after versions. |
| Adding a Wave-3 ADR was considered. | No new decision | Exclude | The accepted RFC plus confirmed mode is sufficient; no ADR file or docs/adr fence change. |
| Wave 4+ lifecycle concepts appear adjacent in RFC-0096. | Does not match | Exclude | No implementation, documentation, fixture, or follow-on is created for them. |
| Concurrent core version work exists in other worktrees. | Matches release risk | Surface later | Re-query exact peer readiness and local refs before version edits; do not speculate or overwrite. |

No unresolved design choice remains before pre-execution review. Review findings
that change roles, operating modes, contract consumption, or task boundaries
require a plan update and renewed approval.

## Changelog

- 2026-08-24: Initial Wave 3 plan from accepted RFC-0096, shipped Wave 1
  contracts, confirmed `ini-002` registration and slug, confirmed no-ADR choice,
  documentation-first ownership, and Architect's four-mode user-pack boundary.
