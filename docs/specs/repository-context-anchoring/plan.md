# Plan: Repository context anchoring

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `AGENTS.md`; `packs/core/seeds/AGENTS.md`;
  `packs/core/.apm/skills/adapt-to-project/SKILL.md`;
  `docs/architecture/overview.md`; `packs/AGENTS.md`

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn while it remains in a living state.

## Approach

Establish one conventional AGENTS.md vocabulary and dogfood it before teaching
the doctor or downstream skills. First, reshape this repository's root and the
portable seed around the four-part minimum plus conditionally justified good
sections, and remove the directly related seed leaks and generic folder map.
Second, replace `adapt-to-project`'s canonical-layout restructuring posture with
a marker-independent read-only anchoring diagnosis and approval-gated proposal.
Third, make authoring and work-loop skills consume the same bounded evidence and
record structural anchors. Finally, give reviewers a focused idiom-delta check,
then project, version, and verify both affected packs. Fixture tests hold the
distinction between minimum, conditional enrichment, inference, and authority.

## Constraints

- Preserve ADR-0037 D2's read-if-present and no-new-config-file constraints;
  interpret the core `reference.md` as one optional source, not the universal
  source.
- Preserve ADR-0037 D3: organization-stack packs compose existing seed, skill,
  profile, and detached-fork primitives; do not add live-upstream layering, a
  new distribution route, or catalogue-resolution machinery.
- Do not alter install commands, companion mechanics, marker behavior, Codex
  hooks/projection, activation diagnostics, or their tests. Seed-content edits
  may require merge sequencing with the independently owned install work.
- Edit `.apm/` sources and `seeds/**`, never generated self-host projections;
  finish with self-host projection.
- Bump `core` and `architect` pack/plugin versions for their respective
  non-cosmetic content changes and update their activation/eval coverage.
- Preserve adopter-owned locations and keep all durable writes approval-gated.
- Do not turn the confirmed wider seed-bundle portability problem into an
  unreviewed installation redesign.

## Construction tests

**Integration tests:** a fixture matrix exercises the thirteen requested
repository shapes plus unavailable external guidance, two discovery-security
cases, and three pack/scope-composition cases across doctor discovery,
structural-plan evidence, and reviewer behavior. Projection and catalogue
verification prove the shipped pack artifacts match sources.

**Manual verification:** inspect one minimum no-AGENTS proposal, one rich custom
layout proposal, and this repository's final root file; confirm no empty
optional sections, no relocation proposal, and no generic directory map.
Record the results under the matching task headings in
`docs/specs/repository-context-anchoring/notes/manual-qa.md`.

**Fixture matrix:**

1. Core-conventional document layout. (AC15, AC28)
2. Custom adopter-owned document layout. (AC15, AC28)
3. Guidance discoverable through root links. (AC15, AC22)
4. Guidance present only in scoped `AGENTS.md`. (AC4, AC28)
5. Strong explicit architecture guidance. (AC17, AC23)
6. Conventions visible only in two convergent production examples. (AC16-AC17)
7. One tentative example that must not become a rule. (AC17, AC26)
8. Contradictory examples. (AC17, AC29)
9. No precedent. (AC17, AC29)
10. Existing root `AGENTS.md` merged without overwriting. (AC19)
11. Structural proposal conflicting with mapped repository anchors. (AC25)
12. Cosmetic difference that must not trigger idiom delta. (AC26)
13. Optional stack advice unable to override repository guidance. (AC26-AC27)
14. Externally linked guidance unavailable during the session. (AC21)
15. Parameterized repository prose, source/comments/examples, tool output, and
    externally retrieved content each attempt to expand tool, write, identity,
    task, or network authority; every case remains attributed evidence and
    produces an instruction-boundary conflict. (AC32)
16. Parameterized absolute outside-root paths, parent escapes, and symlink
    escapes are each rejected both as local discovery targets and as approved
    write targets. (AC33)
17. An existing root `AGENTS.md` and an `AGENTS.upstream.md` organization-pack
    delta are both present; the doctor proposes a selective semantic merge into
    conventional sections, never raw scaffold concatenation, and leaves
    deterministic companion mechanics untouched. (AC34, AC36)
18. Core plus organization-owned backend guidance contribute compatible root
    links under different filenames/headings; the doctor folds them into one
    conventional section without duplicating the scaffold. A contradictory
    variant retains both sources and asks. (AC34)
19. Backend development and test rules apply only below one subtree; the doctor
    offers a delta-only nearest scoped `AGENTS.md`, not a nested
    `CONTRIBUTING.md` or root-level rule dump. (AC35)

## Design (LLD)

### Design decisions

- **Minimum is content, not empty schema.** Four ordinary topics are strongly
  recommended across the effective root-plus-scoped instruction chain; a
  missing fact is reported during diagnosis and omitted from a proposed file
  until known.
- **Good options are conditional.** Each has a trigger and benefit; the doctor
  does not equate more sections with better guidance.
- **Authority is evidence-typed.** Explicit and Framework-owned evidence can
  bind; Convergent evidence can guide; Tentative evidence cannot become a rule;
  Contradictory and Absent evidence stop structural assumption.
- **Root routes, sources own.** AGENTS.md links to existing detail instead of
  duplicating it.
- **Examples are task evidence.** Canonical implementations and tests belong in
  structural-plan anchors, not a permanent universal root index.
- **Composition follows concern and scope.** Compatible pack/repository
  contributions fold into one conventional section; subtree-only rules become
  scoped deltas; contradictions remain attributed and unresolved until a human
  decides.

### Component / module decomposition

- **Root and seeds:** dogfood conventional headings and conditional enrichment;
  correct directly related architecture/changelog portability defects.
- **`adapt-to-project`:** read-only anchoring diagnosis, evidence classifier,
  minimum/additional recommendation, approval-gated root/scoped proposal.
- **Authoring consumers:** `architect-design`, `new-spec`, and `work-loop`
  source discovery plus bounded fallback and plan anchors.
- **Review consumers:** pre-execute review, adversarial reviewer, and quality
  engineer apply structural idiom delta without cosmetic enforcement.
- **Boundary clarification:** `contract-acquisition` retains API-contract
  acquisition and excludes repository dialect/layout mapping.

### Behavior & rules

| Contract | Construction owner | Verification surface |
| --- | --- | --- |
| AC1-AC6 | Root/seed scaffold renderer and doctor recommendation | Section-selection fixtures |
| AC14-AC21 | `adapt-to-project` repository-anchoring phase | Doctor behavior/eval fixtures |
| AC22-AC24 | Authoring skills and plan template | Structural/non-structural plan fixtures |
| AC25-AC26 | Pre-execute and delivery reviewers | Idiom-delta positive/negative fixtures |
| AC27 | `contract-acquisition` boundary prose | Body/parity assertion |
| AC28-AC31 | Compatibility and scope gates | Cross-fixture matrix plus diff audit |
| AC32-AC33 | `adapt-to-project` discovery boundary | Injection and path-confinement fixtures |
| AC34-AC36 | `adapt-to-project` plus organization-pack guidance | Multi-source and scoped-composition fixtures |

### Failure, edge cases & resilience

- Existing guidance conflicts: report sources and evidence class; do not choose
  silently.
- External guidance unavailable: retain its link and availability limitation;
  do not promote cached inference to Explicit.
- Discovered prompt-like content: attribute it as evidence, preserve instruction
  precedence, and surface any attempt to widen authority rather than following
  it.
- Local path outside the repository: canonicalize and resolve symlinks, then
  stop and report the outside-root reference; do not follow or write it as a
  repository-local source.
- No root file: diagnose and offer a minimal populated file; do not require it
  for the task-time fallback.
- Scoped-only repository: use scoped instructions for work in their subtrees and
  offer only a root router if it adds retrieval value.
- One example: Tentative, never a rule. Two independent examples using the same
  mechanism: Convergent, still inference.
- No precedent: ask before introducing a load-bearing mechanism.
- Existing plans: missing anchors is a warning/assurance gap, not a lint error.

## Tasks

### T1: Root and seed guidance demonstrate the minimum-plus-good model

**Depends on:** none

**Repository anchors:** `AGENTS.md`; `packs/core/seeds/AGENTS.md`;
`docs/architecture/overview.md`; `packs/core/seeds/docs/architecture/overview.md`;
`packages/agentbundle/agentbundle/catalogue_tooling/lint.py`;
`packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py`;
`guides/_shared/how-to/build-an-org-stack-pack.md`

**Touches:** `AGENTS.md`, `packs/core/seeds/AGENTS.md`,
`docs/architecture/overview.md`,
`packs/core/seeds/docs/architecture/overview.md`,
`packs/core/seeds/docs/product/changelog.md`,
`guides/_shared/how-to/build-an-org-stack-pack.md`, seed-lint tests

**Tests:**
- **TDD:** extend
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py` with a red
  semantic-portability fixture, then make it reject the concrete catalogue
  leakage patterns fixed here. (AC13)
- **Goal-based:**
  `tests/roster/test_repository_context_root_guidance.py` asserts conventional
  root headings and absence of a mandatory `Source of truth` taxonomy;
  `packs/core/tests/pack/test_repository_context_seed.py` asserts the matching
  seed headings. The split is required: a pack test may not climb above its
  owning pack, so this checkout's own root guidance is roster-owned coverage.
  (AC7-AC9)
- **Goal-based:**
  `packs/core/tests/pack/test_repository_context_seed.py` asserts no prefilled
  generic monorepo tree, no real core release entry in adopter seeds, and that
  `docs/CONVENTIONS.md` is conditional rather than adopter-preempting.
  (AC10-AC12)
- **Goal-based:**
  `tests/roster/test_repository_context_root_guidance.py` also asserts
  organization-pack guidance contributes root links or scoped deltas without
  prescribing a second full root scaffold or nested `CONTRIBUTING.md`.
  (AC35-AC36)
- **Manual QA:** render and compare root and seed files; under `T1 — scaffold
  parity` in `notes/manual-qa.md`, record why each retained optional root
  section meets AC2-AC5. (AC1-AC9)

**Approach:**
- Merge root-only useful rules into conventional sections and retain a compact
  `Documentation` router because this repository has several authoritative
  sources.
- Rewrite the AGENTS seed as the four-part minimum plus clearly conditional
  good options and adopter-source precedence.
- Keep this repository's structure documentation only where it records real
  ownership/change boundaries; correct stale routes. Make the seed structure
  asset optional and responsibility-oriented.
- Scrub the adopter changelog seed. Clarify the optional status of core workflow
  conventions in the AGENTS seed without rewriting the large conventions file
  or changing seed projection mechanics.
- Correct the organization-stack guide's mandatory core-layout and duplicate
  root-seed advice: organization standards remain in adopter/organization-owned
  sources, while root or scoped `AGENTS.md` contributes only the necessary
  routing and action-changing deltas.

**Done when:** targeted seed/root tests pass and a manual comparison shows the
root is a justified rich instance of the same scaffold the seed teaches.

### T2: The anchoring doctor recommends minimum guidance and justifies enrichment

**Depends on:** T1

**Repository anchors:** `packs/core/.apm/skills/adapt-to-project/SKILL.md`;
`packs/core/.apm/skills/adapt-to-project/assets/reference.md`;
`packs/core/tests/skills/adapt-to-project/test_adapt_skill_body.py`;
`packs/core/seeds/AGENTS.md`

**Touches:** `packs/core/.apm/skills/adapt-to-project/SKILL.md`,
`packs/core/.apm/skills/adapt-to-project/assets/reference.md`,
`packs/core/.apm/skills/adapt-to-project/evals/eval_queries.json`,
`packs/core/tests/skills/adapt-to-project/test_adapt_skill_body.py`,
`packs/core/tests/fixtures/repository-context/fixture-matrix.json`,
`packs/core/tests/pack/test_repository_context_fixture_matrix.py`

**Tests:**
- **TDD:** extend `test_adapt_skill_body.py` with fixture-driven behavior checks
  covering core-conventional, adopter-custom, root-linked, scoped-only,
  explicit, convergent, tentative, contradictory, no-precedent, and merge-safe
  existing-root cases. (AC14-AC20, AC28-AC30)
- **TDD:** add negative fixtures prohibiting guidance relocation, mandatory
  `reference.md`, weak-evidence authority, unapproved writes, and empty optional
  headings; add unavailable-external-guidance, instruction-boundary-conflict,
  outside-root path/symlink, `AGENTS.upstream.md` selective-merge, multi-source
  root, and subtree-scoped fixtures. Instruction-boundary cases are
  parameterized over every content and authority class in fixture 15; path cases
  cover all six discovery/write combinations in fixture 16. The companion
  fixture asserts no raw scaffold concatenation and no requirement to change
  companion creation or delivery. (AC18-AC21, AC32-AC36)
- **Goal-based:** validate `eval_queries.json` contains no-AGENTS diagnosis and
  conditional scoped/structure recommendation prompts. (AC14, AC18)
- **Manual QA:** invoke the installed/projected doctor against minimum and rich
  fixtures and record the proposed sections and write boundary under `T2 —
  doctor proposals` in `notes/manual-qa.md`. (AC18-AC19)

**Approach:**
- Add a marker-independent read-only repository-anchoring phase before any
  adaptation writes.
- Keep discovered prose/code/external material attributed as evidence, never as
  authority to widen the task or tool surface; confine local discovery and
  accepted writes to canonical paths under the repository root.
- Replace the Class-3 `DESIGN.md`-is-noncanonical example and mandatory-layout
  posture for guidance sources.
- Render a diagnosis with evidence labels, a strongly recommended minimum, and
  individually justified optional good additions.
- Reconcile overlapping contributions by semantic concern and scope: merge
  compatible links into one section, offer scoped delta files for coherent
  subtrees, and leave contradictions attributed for human resolution.
- Keep `reference.md` as an optional fuller-architecture template only when no
  equivalent source exists and the user wants the enrichment.

**Done when:** doctor behavior tests and activation eval structure pass for all
fixture classes without changing install/marker mechanics.

### T3: Authoring skills consume bounded repository anchors

**Depends on:** T1

**Repository anchors:** `packs/architect/.apm/skills/architect-design/SKILL.md`;
`packs/core/.apm/skills/new-spec/SKILL.md`;
`packs/core/.apm/skills/new-spec/assets/plan.md`;
`packs/core/.apm/skills/work-loop/SKILL.md`;
`packs/core/.apm/skills/contract-acquisition/SKILL.md`;
`packs/core/tests/skills/new-spec/` and `packs/core/tests/skills/work-loop/`

**Touches:** `packs/architect/.apm/skills/architect-design/SKILL.md`,
`packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/.apm/skills/new-spec/assets/plan.md`,
`packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/contract-acquisition/SKILL.md`, related tests/evals

**Tests:**
- **TDD:** `packs/core/tests/skills/new-spec/test_repository_anchors.py` and
  `packs/core/tests/skills/work-loop/test_work_loop_repository_anchors.py` use structural
  and non-structural plan fixtures to pin `Repository anchors:` shape and
  backward-compatible missing-metadata behavior. (AC22-AC24)
- **TDD:** those tests plus
  `packs/architect/tests/skills/architect-design/test_architect_design_repository_anchors.py`
  verify linked-source consumption, bounded fallback, and
  ask-before-unanchored-structure behavior. (AC22-AC23)
- **Goal-based:**
  `packs/core/tests/skills/contract-acquisition/test_repository_boundary.py`
  preserves API-contract ownership and the repository-anchoring exclusion.
  (AC27)
- **Manual QA:** author one structural and one non-structural plan from fixtures
  and record the resulting anchor line under `T3 — task plans` in
  `notes/manual-qa.md`. (AC23-AC24)

**Approach:**
- Replace direct `docs/architecture/reference.md` and `CONVENTIONS.md`
  assumptions with root-link consumption and the shared bounded fallback.
- Add the plan metadata line and use it only for task-relevant evidence.
- Clarify, without broadening, the contract-acquisition boundary.

**Done when:** authoring fixtures demonstrate equivalent behavior with core and
custom layouts, and existing plans remain valid.

### T4: Reviewers flag only load-bearing repository idiom deltas

**Depends on:** T3

**Repository anchors:**
`packs/core/.apm/skills/work-loop/references/pre-execute-review.md`;
`packs/core/.apm/agents/adversarial-reviewer.md`;
`packs/core/.apm/agents/quality-engineer.md`;
`packs/core/tests/skills/work-loop/test_golden_fixtures.py`

**Touches:** `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`,
`packs/core/.apm/agents/adversarial-reviewer.md`,
`packs/core/.apm/agents/quality-engineer.md`, related rubric/eval tests

**Tests:**
- **TDD:**
  `packs/core/tests/skills/work-loop/test_repository_idiom_delta.py` includes a
  structural proposal conflicting with mapped anchors and requires the focused
  idiom-delta finding. (AC25)
- **TDD:** that file's cosmetic-difference, one-tentative-neighbor, and optional
  stack-advice fixtures produce no idiom-delta finding. (AC26-AC27)
- **TDD:** that file's weak, contradictory, and outcome-critical citation
  fixtures trigger independent example inspection; strong non-load-bearing
  citations do not. (AC25-AC26)
- **Manual QA:** record reviewer output for the exact X-versus-Y formulation and
  absence of product-scope expansion under `T4 — focused review` in
  `notes/manual-qa.md`. (AC25-AC26)

**Approach:**
- Add one scoped idiom-delta rule and explicit prohibitions against incidental
  precedent, cosmetic uniformity, scope expansion, and pack-layout enforcement.
- Align pre-execute and delivery reviewers on when independent inspection is
  warranted.

**Done when:** focused-review fixtures distinguish structural conflict from
cosmetic difference and all rubric parity checks pass.

### T5: Shipped packs, docs, and projections are coherent

**Depends on:** T2, T3, T4

**Repository anchors:** `packs/AGENTS.md`; `packs/core/AGENTS.md`;
`packs/core/pack.toml`; `packs/architect/pack.toml`;
`guides/_shared/reference/catalogue-ci-contract.md`

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`,
pack changelog/docs/evals, generated self-host projections

**Tests:**
- **Goal-based:** `python3 -m pytest
  packs/core/tests/pack/test_repository_context_seed.py
  tests/roster/test_repository_context_root_guidance.py
  packs/core/tests/skills/adapt-to-project/test_adapt_skill_body.py
  packs/core/tests/skills/new-spec/test_repository_anchors.py
  packs/core/tests/skills/work-loop/test_work_loop_repository_anchors.py
  packs/core/tests/skills/work-loop/test_repository_idiom_delta.py
  packs/core/tests/skills/contract-acquisition/test_repository_boundary.py
  packs/architect/tests/skills/architect-design/test_architect_design_repository_anchors.py
  packs/core/tests/pack/test_repository_context_fixture_matrix.py
  packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_architecture_seed_requires_responsibility_map_placeholders
  -q` passes.
- **Goal-based:** `agentbundle catalogue lint --root . --deep`,
  `agentbundle catalogue verify --root .`, `env
  PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue self-host
  --root . --write`,
  `SKIP_SAST=1 make build-check`, and
  `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
  pass. Human-approved verification amendment (2026-08-23): in this managed
  macOS runtime, `catalogue verify`, self-host write, and `make build-check`
  may stop only while removing or renaming provenance-bearing temporary
  directories with `EPERM`, including from a fresh `/private/tmp` clone. Claude
  should retry those gates in its supported environment before merge. If the
  same platform restriction persists, the accepted replacement evidence is:
  targeted repository-context and seed-lint tests; Ruff and mypy; guide,
  AGENTS, and spec-status lint; deep catalogue lint; canonical/projection byte
  parity; clean adversarial, security, and quality review. The deferral does not
  excuse a content, test, lint, type, or projection failure.
- **Goal-based:**
  `packs/core/tests/pack/test_repository_context_fixture_matrix.py` validates
  every named case in
  `packs/core/tests/fixtures/repository-context/fixture-matrix.json`, including
  all nineteen fixture classes above, has an owning behavior test and is green.
- **Manual QA:** inspect the final diff against the parallel-work exclusion list
  and record merge sequencing for any seed-content adjacency under `T5 — final
  scope` in `notes/manual-qa.md`. That section includes an explicit
  installer/companion non-interference checklist and names every changed file,
  so AC36 fails review if deterministic companion behavior or distribution
  machinery changed. (AC31, AC36)

**Approach:**
- Bump both affected pack versions according to the scoped pack rule.
- Update user-visible changelog/eval coverage and regenerate projections only
  after canonical sources are complete.
- Inspect the final diff for overlap with the independent install/Codex work and
  record merge sequencing without absorbing it.

**Done when:** canonical sources, projections, manifests, fixtures, and
catalogue gates agree with no install/Codex surface redesign.

## Rollout

This is an additive prompt/seed behavior change with no runtime migration.
Existing repositories and plans continue to work. New metadata and durable
adaptation begin as recommendations and warnings. Rollback is a pack-content
revert; there is no data migration. Coordinate seed-content conflicts with the
parallel installation branch before merging either side.

## Risks

- A richer scaffold could recreate the context-cost problem; conditional
  sections and omission of unknown content are the control.
- Prompt-body tests can become string-shape assertions rather than behavior
  tests; prefer fixture outcomes and reserve literal greps for load-bearing
  prohibitions.
- Editing root `AGENTS.md` changes this repository's active instructions;
  preserve behavior while renaming/folding and review the final root file as a
  complete artifact.
- Full cleanup of the 1,482-line conventions seed could expand into a broader
  governance/install redesign; this plan clarifies its optional status but does
  not silently rewrite the whole core workflow.
- Parallel seed-install work may modify adjacent projection expectations; merge
  canonical content first or rebase the later branch and rerun full projection
  gates.

## Changelog

- 2026-08-22: initial plan, revised after seed pressure-testing to dogfood the
  minimum-plus-conditionally-good scaffold and exclude an ADR.
- 2026-08-23: human-approved test-path correction and environment-specific
  verification deferral after duplicate pytest basenames caused import
  collisions and macOS denied temporary artifact cleanup in a clean clone. The
  targeted command selects the new seed-lint construction test rather than
  inheriting an unrelated cleanup-sensitive package test.
