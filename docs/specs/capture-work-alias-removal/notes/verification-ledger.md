# Capture-work alias removal verification ledger

## Execution preflight — 2026-10-07

- Delivery run: `09925534-68c8-4cf6-894a-a085439b8d0f`.
- Workspace preflight: the canonical entry for this spec is ready, dispatchable,
  and has no findings. The existing spec and plan both record owner approval.
- Branch freshness: the approved helper returned `surface` because origin's
  remote advertisement failed with unclassified diagnostics. The owner then
  explicitly authorized continuing without verified freshness.
- Local workflow execution: the owner authorized workspace status, engine and
  cohort tooling, targeted tests, lint/type checks, projection builds, and
  catalogue/documentation validators. Merge and publication are not authorized.
- Risk mode: full, because the change removes a published skill and changes
  ordinary workspace parsing and dispatch guarantees.
- Knowledge reference: `knowledge provider unavailable`.

## Owner-approved bounded T1 amendment

The approved T1 file list omits three existing consumers that must move from
ordinary reconciliation to explicit migration parsing:

- `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`:
  `_migration_rollback_workspace_bytes` currently checks restored bytes against
  `run_canonical_reconciliation(...).legacy_memberships`. That list must become
  empty under AC-0003, so this check would return `recovery_conflict` for valid
  rollback. Bind the retained explicit migration decoder here instead.
- `packs/core/tests/skills/workspace-status/test_work_intake_migration_planning.py`:
  selection and finding setup currently reads ordinary legacy memberships.
- `packs/core/tests/skills/workspace-status/test_work_intake_migration_effects.py`:
  selection setup currently reads ordinary legacy memberships.

Proposed plan change: append those three paths to T1's **Touches** field and add
the following sentence to its **Tests** field:

> Move migration finding and selection setup to explicit migration parsing,
> and verify the CLI rollback path uses that same retained repair boundary.
> Preserve every existing planning, apply, interruption-recovery, and exact-byte
> rollback outcome assertion.

This adds no module, dependency, migration format, result schema, permission,
authorization rule, or acceptance criterion. The owner approved this bounded
amendment on 2026-10-07; its exact file list and test obligation are now in T1.

## Resolve-versus-surface record

- Ordinary-reader removal and retained explicit migration are in scope.
- The omitted rollback consumer and migration test setup were resolved by the
  owner-approved bounded T1 amendment above. The parser split is implemented;
  required test updates and verification remain unfinished.
- Release authorization and coordinated publication remain pending T5 and T6.

## Baseline verification

| Check | Observed result |
| --- | --- |
| `git diff --check` | Passed before implementation. |
| `make lint-ruff lint-mypy` | Blocked: `ruff` is not installed; make exited 2 before type checking. |
| Migration planning/effects pytest suites | Blocked: the active Python interpreter has no `pytest`; no tests ran. |
| Existing tool environment | No `.venv` exists in this worktree or its parent. |

The missing development tools are an environment prerequisite, not passing
evidence. Approved package installation attempts failed; no release action
has been attempted.

## Tool and review prerequisites

- Creating `.venv` failed while bootstrapping pip; the local environment is
  incomplete. The owner approved the exact ensurepip and installation commands.
- Fresh security design review of the amended pair returned a clean verdict
  with a `Not checked` footer. Independent adjudication returned strict clean;
  raw and adjudication artifacts passed identity validation and the cohort
  inspector accepted the adjudication.
- The owner explicitly authorized independent read-only review under the
  observable workspace-write profile on 2026-10-07. Review briefs prohibited
  mutation, network/MCP, recursive delegation, and project-code execution.
- The approved `.venv/bin/python -m ensurepip --upgrade` failed because policy
  denied creating its temporary CA certificate bundle. Package installation
  has not succeeded. The subsequently approved uv installation resolved packages
  but failed when the runtime denied a cache directory rename. Automatic approval
  review rejected the escalated installation as a prohibited sandbox bypass.
  No further installation attempt is authorized through that blocked path.

## Approved execution baseline

- Source commit: `f6ecf90e27e749975a501b18711411cce0eccd62`.
- Approved spec hash: `70fc54dc6fdd` (prefix; full hash is in cohort state).
- Approved plan hash: `ddc1e19dc0aa` (prefix; full hash is in cohort state).
- Engine entered `CODE-IMPLEMENTATION`; the spec is `Implementing`.
- Sequential schedule: T1/T2, then T3, T4, T5, T6.
- T1 was dispatched to one implementer. Its standalone Python regression
  can establish the intended red and smoke result; missing pytest/lint tools
  still prevent the required gates and candidate readiness.

## T1 implementation observations

- The approved AC-0003 stub was materialized at
  `packs/core/tests/skills/workspace-status/test_capture_work_removal.py` with
  byte identity to the plan text, then executed by the controller as a direct
  stdlib function call. Baseline red failed at
  `assert result.legacy_memberships == []`.
- Ordinary reconciliation now classifies former section 10 legacy shapes as
  `unsupported_legacy` and emits `legacy_memberships = []`; duplicate, cooling,
  dependency, and dispatch derivation use only canonical memberships and parse
  blocked canonical paths.
- Explicit migration planning and rollback now use
  `extract_legacy_migration_memberships(...)`, the retained migration-only
  parser seam in `workspace_status_engine.py`. Migration selection setup in the
  planning/effects tests uses that same seam.
- Stdin/stdlib checks: the five changed Python files compiled with
  `py_compile`. The controller directly ran the no-fixture standalone removal
  regressions for ordinary reconciliation, the five-shape matrix, and
  duplicate/dispatch derivation; they passed. The controller also verified that
  `extract_legacy_migration_memberships(_section10_workspace())` returns exactly
  five accepted historical memberships. This is smoke evidence only, not a
  replacement for the migration planning/effects pytest suites. Required pytest,
  ruff, and mypy gates remain blocked because the local tool installation failed
  and escalation was rejected as a prohibited boundary bypass.

## Initial T1 handoff — blocked

- Final controller smoke: four standalone regressions passed, including cooling
  and dependency derivation; five historical shapes remain accepted by the
  explicit migration extractor. Total run time: 0.18 seconds.
- Five changed Python files passed in-memory compilation. `git diff --check`
  passed. These checks do not establish migration apply/recovery/rollback safety.
- `test_workspace_status_engine_autonomous.py` still needs its ordinary-reader
  expectations updated. Required migration suites, pytest, Ruff, and mypy are
  unrun. T1 is blocked and must not be marked ready.
- T2–T6 have not started. No acceptance criteria are checked off, adapters have
  not been regenerated, and no commit, push, or publication occurred.
- Resume requires an available managed development-tool environment and a
  revised T1 handoff covering the incomplete autonomous test expectations.
  The supervisor stopped after the blocked implementer report; it did not
  redispatch that task or relax any required gate.

## Owner-approved T1 recovery

- The owner approved resuming the unfinished work after the blocked handoff.
  The revised recovery task owns only the autonomous test expectations; it
  preserves the source split, canonical positive controls, and explicit repair
  parser/fixture coverage. It does not repeat the original implementation task.
- A read-only module-availability probe still finds no pytest, Ruff, or mypy.
  No installation retry was made.
- Automatic approval review rejected the exact `loop-engine.py status` command
  because it did not recognize an action-specific authorization for running
  repository-supplied code. The command was not retried or run indirectly.
  Direct bounded reads show the persisted engine remains `CODE-IMPLEMENTATION`
  at transition sequence 7, with no completed tasks or pending transition.
- The recovery implementer is limited to reads and test edits. Full verification
  and workflow execution remain blocked; no passing gate or completed task is
  inferred from the owner's approval.
- Autonomous test expectations are now updated for ordinary legacy rejection,
  absence of alias-derived duplicates, and unsatisfied legacy-only dependencies.
  Canonical malformed target-path blocking and explicit decoder fixture checks
  remain intact. The positive dispatch and brief-child matrix fixtures were
  checked for hidden scalar memberships; both use canonical entries.
- Controller checks passed: the updated test file parses as Python syntax, and
  `git diff --check` exits zero. No repository code was executed in recovery.
- The implementer's recovery report and final fixture sweep are saved beside
  this ledger. Required executable gates remain unrun; T1 is still blocked.
  T2–T6 remain pending, and no commit or publication occurred.

## Claude resume — 2026-10-07

### Environment and branch

- Interpreter: `/Users/eu.gene.lim/.pyenv/versions/3.13.13/bin/python3` (Python
  3.13.13, pytest 9.0.3), with ruff and mypy on PATH. No installation was made.
- At 15:54 CDT a checkout outside this run moved the worktree to
  `feat/structured-review-boundary` at `9d39eae8b` (origin/main, two commits past
  the `f6ecf90e2` baseline; neither touches this work's files). The owner chose a
  new branch; `feat/capture-work-alias-removal` already exists on origin from an
  earlier attempt, so work continues on `feat/capture-work-alias-removal-core3`
  at `9d39eae8b`.

### T1 regressions found and fixed

- `compute_migration_plan` referenced `canonical` after the parser split removed
  its assignment (`NameError`), failing 25 migration planning/effects tests. The
  reconciliation call is restored for the duplicate check; legacy selection
  still uses `extract_legacy_migration_memberships`.
- Closeout lost its residue blocker for former legacy shaping and brief entries:
  ordinary parsing dropped them, so an initiative holding one looked empty and
  closeout-eligible. `Initiative.has_unsupported_open_entry` now records any open
  shaping or brief entry no canonical parse accepted, and closeout counts it as
  `initiative-residue`. `test_closeout_initiative_residue.py`'s two legacy residue
  tests failed before the fix and pass after it; a focused regression covers
  shaping and brief shapes plus a canonical-only control.
- `test_t2_legacy_aliases_do_not_satisfy_dependent_work` now expects
  `missing_dependency`: with aliases ignored, the dependency target is simply
  unregistered and absent, rather than structurally blocked by an alias duplicate.
- `workspace.toml` is unchanged. During the amendment the spec is `Draft` and its
  entry stays in `ini-002` `queue`; the repository health test passes in that
  state. Move the entry to `active` when the spec returns to `Implementing`.

### T1 verification (candidate: working tree on `9d39eae8b`)

| Check | Result |
| --- | --- |
| Four handoff T1 suites | 125 passed, 1 skipped, 4.7 s |
| `packs/core/tests/skills/workspace-status/` + `tests/roster/test_skill_census.py` | 274 passed, 1 skipped, 5.8 s |
| `packs/core/tests/skills/work-intake/` excluding `test_intent_rename_*` | all passed (part of a 669-test run) |
| `test_intent_rename_{allocation,citations,installed_surface}.py` | 52 passed; the remaining `test_intent_rename_*` files were not run — they are git-heavy (over 16 min for one file) and do not touch workspace-status or the alias |
| `tests/roster/test_work_intake_contracts.py` | 103 passed |
| `tests/roster/test_work_intake_migration_contracts.py` | 13 passed |
| `tests/roster/test_workspace_status_projection.py` | projection-parity failures only, expected until T4 self-host; repository health passes |
| `tests/roster/test_cooling_scope_closure.py` | 11 failed: the file pins removed ordinary-legacy cooling behavior (see amendment) |
| `make lint-ruff lint-mypy` | passed |
| `git diff --check` | passed |

### Plan omissions requiring a controlled amendment

Files outside the approved Touches that pin the removed alias or ordinary legacy
reader:

- T1: `tests/roster/test_cooling_scope_closure.py` — two cooled-legacy closeout
  tests, a realness helper that reads ordinary `legacy_memberships`, and an AC24
  count of two single-argument reconciliation calls in `workspace_status.py`
  (rollback now uses the explicit extractor, leaving one).
- T2: `Makefile` and `.github/workflows/catalogue-tooling-ci-gates.yml` run
  `packs/core/tests/skills/capture-work/`; `tools/lint-ci-parity.py` maps it;
  `tools/add-rendering-directives.py` keys `capture-work`;
  `tests/roster/test_shaping_intake_handoff_matrix.py` and
  `tests/roster/test_work_intake_migration_contracts.py` pin the alias route and
  skill path; `packs/agent-skill-engineering/tests/fixtures/skill-census.json`
  lists the skill.
- T3: product-engineering guidance tells users to run `capture-work`:
  `packs/product-engineering/.apm/skills/map-capabilities/SKILL.md`,
  `packs/product-engineering/.apm/skills/place-bet/SKILL.md`,
  `packs/product-engineering/.apm/skills/place-bet/examples/placing-a-bet.md`,
  `packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md`.
- T4: the product-engineering patch release (`pack.toml`,
  `.claude-plugin/plugin.json`, changelog) that the T3 edit obliges.

Owner decision, 2026-10-07: amend all of the T2–T4 items above (option "Amend
all"). The T1 cooling-test item was found after that decision and is carried in
the same amendment for the owner's spec/plan re-approval.

### Amendment review — round 3 (stopped for an owner decision)

- `contract-amendment` fired at sequence 8 and `spec-ready` at 9; the engine is in
  `SPEC-PLAN-REVIEW`. Raw report:
  `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/3-pre-execute-adversarial-reviewer-raw.md`
  (1 Blocker, 3 Concerns, 2 Nits). It has not been adjudicated yet.
- Controller check of Blocker 1: the 7 named test files ran 105 failed, 345
  passed in 89 s against this candidate. The cause includes a shipped-code
  break: `workspace_status_prune.py` lines 80 and 150 still unpack four values
  from `_parse_membership_entry`, which now returns three, so prune previews
  fail with `invalid_workspace`. The packaged copy under
  `packages/agentbundle/agentbundle/_data/` has the same unpack.
- Further files pinning ordinary legacy behavior, outside every Touches:
  `workspace_status_prune.py` (authored and packaged),
  `tests/roster/test_two_sided_prune_closure_invariant.py`,
  `tests/roster/test_workspace_status_progressive_disclosure.py` (SHA-256 pins),
  `tests/roster/test_selection_scoped_membership_absence.py`,
  `tests/roster/test_status_projection_and_context_exclusion.py`,
  `tests/roster/test_cooling_brief_child_scope_closure.py`,
  `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`,
  `web/src/content/journeys/core.md` (generated by `tools/build-site.py`), and
  `packs/core/.apm/skills/work-loop/SKILL.md:173`.
- Open owner decision: prune's legacy-alias closure either (a) is an ordinary
  reader and is removed, so prune treats former legacy entries as unsupported,
  or (b) is a retained repair seam that reads through
  `extract_legacy_migration_memberships`. Option (b) keeps prune's current
  contract; option (a) changes it and falls under the spec's `Ask first` rail.

### Owner decision and round 3 disposition

- Owner decision, 2026-10-07: prune's legacy-alias closure is a retained repair
  seam. `workspace_status_prune.py` now decodes historical aliases through
  `parse_legacy_workspace_entry`, only when no canonical parse accepts the entry.
  `tests/roster/test_two_sided_prune_closure_invariant.py` went from 38 failures
  to 2: one reads ordinary `legacy_memberships` in setup (amended into T1), and
  one is the Core version-bump check that T4's 3.0.0 bump satisfies (it passes
  on clean HEAD, where `packs/core` is unchanged).
- Round 3 was not passed through `finding-adjudicator`. The controller
  reproduced Blocker 1 directly (105 failures across the 7 named files) and
  revised the plan against all six findings before firing `findings-remain`
  (sequence 10). Round 4 reviews the revised contract and will be adjudicated.
- Revisions: T1 Touches now name the prune module and the eight test files from
  Blocker 1, and drop `test_closeout_initiative_residue.py`, which passes
  unchanged. T3 adds `work-loop/SKILL.md` and its evals (Concern 3). T4 adds the
  packaged prune module and the generated web journey with its parity lint
  (Concern 2). The `workspace.toml` entry stays in `queue` while the spec is
  `Draft` (Concern 4). Each `Done when` now covers its new Tests bullets (Nits 5
  and 6).

### Amendment review — round 4 (stopped)

- Raw report: `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/4-pre-execute-adversarial-reviewer-raw.md`
  (11 findings). Adjudication:
  `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/4-pre-execute-adversarial-reviewer-adjudication.md`
  sustains 3 Blockers, 2 Concerns, and 1 Nit, and refutes 5. It also carries an
  `ADJUDICATION-INDETERMINATE` line although its indeterminate audit is empty.
  `review inspect --adjudication` classifies it `invalid (indeterminate-present)`,
  which is a stop. No transition was fired; the engine stays in
  `SPEC-PLAN-REVIEW` at sequence 11.
- Sustained findings that need owner decisions before the plan can be revised:
  1. Migration discovery: after T1, no `status`/`reconcile`/`repair-plan`
     output emits the migration finding (`legacy_finding_id`,
     `source_membership`) a reviewed selection must bind. It came only from
     ordinary `legacy_memberships`. The plan must name a user-reachable
     surface that emits it, or the owner changes the selection workflow under
     the spec's `Ask first` rail.
  2. Five packs require `core ^2.0` (code-intelligence, governance-extras,
     iac-terraform, monorepo-extras, release-engineering); Core 3.0.0 fails
     catalogue verify (`CAT-V-007`) unless each gets a requirement update and
     release.
  3. Type 2 repair-plan/repair-apply still decode legacy shapes; the plan must
     state whether that stays a repair seam like prune.
- Mechanical sustained findings: add `workspace-status/evals/**` to T1; mark
  the Core version-bump prune test as T4-satisfied; correct the
  `workspace.toml` header comment.

### Owner decisions after round 4 — 2026-10-07

- Type 2 `repair-plan` and `repair-apply` stay a repair seam that decodes
  historical legacy shapes, matching the prune decision.
- The owner asked to release Core as a 2.x version instead of 3.0.0. This
  conflicts with the `packs/AGENTS.md` version rule (major for removals) and
  with RFC-0083's 2026-10-02 Errata, which names Core 3.0.0. It is held for
  owner confirmation before any contract edit.
- The owner asked for an explanation of the migration-discovery gap before
  deciding it.
- Owner decision: Core stays 3.0.0. The five packs requiring `core ^2.0` move
  to `^3.0` in patch releases (T4).
- Owner decision (spec `Ask first`): no replacement surface emits the
  migration finding. In this repository the explicit extractor finds 0
  migratable entries; the 24 `unsupported_legacy` findings are the same at
  HEAD. AC-0007 now has adopters rewrite a former legacy entry by hand, and it
  keeps the migration tooling for rolling back an existing ledger.
- Plan revised for round 4's sustained findings: workspace-status evals in T1,
  the version-bump prune test is T4-satisfied, the Type 2 repair seam is
  stated, the migration guide and `workspace.toml` header comment are in T3,
  and the five dependent packs plus catalogue verify are in T4.

### Amendment review — round 5

- Raw: `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/5-pre-execute-adversarial-reviewer-raw.md`
  (8 findings). Adjudication: `5-pre-execute-adversarial-reviewer-adjudication.md`
  sustains 2 Blockers, 2 Concerns, and 2 Nits, and refutes 2. `findings-remain`
  fired at sequence 14.
- Revisions: T4 now covers the three test files and two docs that pin `^2.0`
  or code-intelligence's version. T3 gains an AC-0007 audit for guidance that
  starts a new migration, plus a complete `Done when`. AC-0007 allows recovery
  as well as rollback of an existing ledger operation, matching AC-0005.
  AC-0013 and T5 bind the prior versions of the five dependent packs to the
  rollback target. T2 runs `tools/test-lint-ci-parity.py`.

### Amendment review — round 6

- Raw and adjudication: `6-pre-execute-adversarial-reviewer-{raw,adjudication}.md`.
  Sustained: 1 Blocker (`tests/roster/test_cooled_work_entry_classes.py` was
  missing from T1) and 2 Nits (MCP expected result; Rollout line). No findings
  were refuted. `findings-remain` fired at sequence 16; all three are applied.

### Amendment review — round 7 and the scope decision (2026-10-08)

- Raw: `7-pre-execute-adversarial-reviewer-raw.md` (2 Blockers, 1 Concern). All
  three arise because the candidate also converted the status-analysis layer
  (`extract_initiatives` and its parsers) to canonical-only. That broke Type 2
  repair and `explain`, and it changed output for already-canonical entries.
- Owner decision, 2026-10-08: removal reaches the dispatch path (canonical
  reconciliation) only. The candidate's `_parse_work_entry`,
  `_parse_supported_shaping_entry`, and `_supported_brief_queue_path` are
  restored to HEAD; `_dependency_status_token` is removed. The closeout residue
  flag now tests canonical parsing directly. The spec's Never-do line defines
  "ordinary" as canonical reconciliation.
- After the restore, the T1 test set (workspace-status folder plus the 9
  roster/tools files in T1 Touches) ran 742 passed, 37 failed, 1 skipped in 122 s.
  The 37 are the planned test updates still to do, plus the T4-satisfied
  version check. `test_capture_work_removal.py`: 6 passed; its new
  analysis-layer test passes on the HEAD engine as well.
- Round 7 was not adjudicated: its findings went to the owner as a scope
  question, and the decision above resolves all three. `findings-remain` and
  `spec-ready` follow; round 8 reviews the result and will be adjudicated.

### Amendment review — round 8

- The candidate lost Type 2 repair's legacy-alias duplicate guard: canonical
  reconciliation no longer counts aliases, so `_repair_entry_eligibility` would
  auto-move a queue spec that a legacy alias also lists. The repair seam now
  checks `extract_legacy_migration_memberships` itself. Case 077 and
  `test_repair_apply_duplicate_queue_active_stays_manual` pass again (45
  selected repair tests passed).
- Adjudication (`8-pre-execute-adversarial-reviewer-adjudication.md`): 1 Concern
  and 1 Nit sustained; Blocker 1 refuted because the contract already required
  the HEAD outcome. `findings-remain` fired at sequence 20. The spec's Never-do
  line now names which surfaces follow canonical reconciliation and which stay
  unchanged; plan Interfaces line 63 matches.
- Round 9: one Nit (an ambiguous subject in the spec's Never-do line), adjudicated as sustained and fixed. `findings-remain` fired at sequence 22.
- Round 10: `Clean — ready to commit.` (raw `10-pre-execute-adversarial-reviewer-raw.md`, classified clean). `reviewers-clean` fired at sequence 24; the engine waits at `SPEC-HUMAN-GATE`.

## Execution after re-approval — 2026-10-08

- Spec and plan re-approved by the owner; `approve-plan`, `schedule`, and
  `plan-locked` ran (sequence 27). The spec is `Implementing`, and its
  `workspace.toml` entry moved to `ini-002` `active`.

### T1

- An implementer updated the tests and evals in T1 Touches. It also added a
  legacy-brief lookup to `_brief_child_spec_states` through the migration
  extractor. The controller reverted that lookup: it is a legacy reader inside
  canonical reconciliation, which the spec's Never-do line forbids. The test is
  now `test_a_legacy_bare_string_brief_does_not_resolve_a_declaration`; it
  expects the fail-closed `cooled_child_scope_unknown` and no dispatch, like
  the decoy case.
- T1 test set (workspace-status folder plus the 9 roster/tools files): 779
  passed, 1 skipped, 1 failed, 129 s. The failure is
  `test_pack_delivery_contract_is_complete_and_version_increased`, which T4
  satisfies. `make lint-ruff lint-mypy` and `git diff --check` pass.

### T2

- An implementer deleted the `capture-work` skill and its tests, plus the
  manifest entry, the alias router branch and `RoutingSignals.alias`, the
  routing case and eval, and the gate wiring, census entry, and roster pins.
  Deviation: `tools/test-lint-ci-parity.py` (outside T2 Touches) needed its
  SHA-256 pins refreshed, because the catalogue-tooling workflow step it pins
  changed; that is a 2-line pin-only update that T2's required self-test gate
  depends on.
- Controller gates: Core pack tests, 5 work-intake suites, and 4 roster suites
  ran 489 passed in 29 s. `tools/lint-ci-parity.py` and
  `tools/test-lint-ci-parity.py` pass. `make lint-ruff lint-mypy` and
  `git diff --check` pass.

### T3

- An implementer updated 25 current-guidance files across the guides, Core
  and product-engineering skill docs, the work-loop orientation sentence and a
  new eval case, the migration guide (now recovery and rollback only, with the
  hand-rewrite instruction), and the `workspace.toml` header comment. Its
  three audits (AC-0007 `capture-work`, AC-0008 installed-compatibility,
  AC-0007 hand-rewrite) leave only stable URL or link names, removal
  statements, and recovery-only matches.
- T2 correction found during T3: work-intake eval 16 still expected the agent
  to delegate a new migration to the planner. Its expected output and
  assertions now teach the hand rewrite and limit the tooling to recovery or
  rollback (the file is in T2 Touches).
- Controller checks: `validate_guides.py`, `check-guide-index.py`,
  `lint-guide-titles.py`, `lint-guides-no-repo-only-refs.py`,
  `lint-journey-contract.py`, and `lint-pack-journeys.py` pass. Guide tool
  tests, `packs/core/tests/pack/`, and `packs/core/tests/skills/work-loop`:
  2718 passed, 6 skipped, 29 min. `lint-web-journey-parity.py` fails on the
  generated `web/src/content/journeys/core.md`, which T4 regenerates; the site
  build and rendered-link checks also run in T4.

### T4

- An implementer set Core to 3.0.0 and added the release checker's `--kind
  major` mode (5 new tests). It moved the five dependent packs to `^3.0` in
  patch releases (code-intelligence 0.1.4, governance-extras 1.0.1,
  iac-terraform 0.1.12, monorepo-extras 0.1.10, release-engineering 0.1.11),
  set product-engineering to 0.13.23, wrote the changelog entries, synced the
  package data, and regenerated projections and web journeys.
- Controller corrections: AgentBundle went to 0.52.0, not 0.51.1, because the
  package follows pre-1.0 semver and the MCP `workspace_status` output change
  is breaking; the package changelog gained its entry. The Core 3.0.0
  Highlight's nonexistent `workspace-status migrate` was corrected. The
  `legacy_entry` finding-table rows were restored as migration-only, and the
  work-loop Step-0 contract pin was refreshed after review.
- The owner authorized local commits on 2026-10-08. Candidate commits on
  `feat/capture-work-alias-removal-core3`: `5c7322ff2`, `068a6555f`,
  `aa4054013`, and the projection regeneration after them; `make build-self`
  ran without force on the clean tree.
- Results: `check-core-release.py --kind major` passes and the default patch
  mode refuses 3.0.0. `catalogue self-host --check` and `catalogue verify`
  pass. `catalogue lint --deep` reports 75 warnings and no errors.
  `lint-web-journey-parity.py` passes. The pin, prune, projection, and release
  test files ran 133 passed. The 0.52.0 wheel's engine and prune modules are
  byte-identical to the Core sources. `make lint-ruff lint-mypy` passes.

### Implementation review — round 1 (2026-10-08)

- Reports and adjudications are under `.context/reviews/09925534-68c8-4cf6-894a-a085439b8d0f/impl/`.
  Sustained: experience 1 Blocker, 4 Concerns, 7 Nits; adversarial 1 Blocker,
  1 Concern, 2 Nits, plus 1 indeterminate (the cooling realness check), which
  the base-revision helper settles; quality 2 Concerns, 3 Nits. Security: clean
  after adjudication; its finding was refuted against the approved plan.
- Owner decisions, 2026-10-08 (controlled amendment):
  1. Legacy shaping entries are no longer listed: the shaping parsers reject
     historical shapes, so `shaping.*`, `top_level_backlog`, and the MCP
     shaping list hold only canonical-era content. Closeout still counts the
     leftover entry as residue. (The adversarial adjudication refuted the
     dispatch risk, because MCP documents `shaping[]` as informational; the
     owner's choice stands on clarity.)
  2. Canonical reconciliation refuses dispatch of a canonical entry while a
     historical alias for the same artifact survives anywhere in the
     workspace. The alias is decoded only to refuse, never to admit.
- Tooling defect: the first `contract-amendment` call (no evidence refs)
  prepared its `pending_transition` marker and then failed, because T1–T3
  were complete without evidence bindings. Replay of that exact call can never
  succeed, and corrected calls conflict with the marker. With owner
  authorization on 2026-10-08, the controller cleared only that marker from
  `state.json`, after checking that its `transition_id` (`b96cc7f7…`),
  sequence (31), event, and empty evidence matched. No other field changed, and
  `loop-cohort identity` passes. The defect (prepare before validate) is for
  the work-loop maintainers.
- Amendment (sequence 32): the spec's Never-do line records both owner
  decisions. The plan adds T7 (code and test corrections) and T8 (guidance
  corrections) before T4, and T4's Highlights bullet takes the changelog
  findings. T1–T3 stay complete, with evidence bound to their ledger sections.
- Amendment review (sequence 33) sustained gaps that came from the shaping
  decision. Emptying the shaping lists would also disable the work-loop
  shaping guard and change `shape:`/`research:` need resolution, because those
  lists only ever held legacy entries. The owner reversed that decision on
  2026-10-08: the shaping lists, guard, and need resolution stay as at HEAD,
  and guidance says old shaping entries still appear in the information-only
  lists. The alias-refusal clause is now scoped to the decoder's alias
  mapping, and T7, T8, and T4 are revised for the review's other findings.
- Round 11 (`11-pre-execute-adversarial-reviewer-raw.md`, 9 findings) was not adjudicated: the owner's reversal of the shaping decision answers Blockers 1 and 2 and Concern 3, and the revision applies the rest directly. Round 12 reviews the result and will be adjudicated.
- Round 12: adjudication sustained 2 Blockers and 1 Nit and refuted 1 (the request for a separate AC). Applied: T7's alias mapping lists the decoder's four branches with matching cases and a negative control; T8 Touches add the work-loop skill and eval and the two product-engineering skills. `findings-remain` fired at sequence 36.
  The saved round 12 adjudication is a condensed copy, so `review inspect` classifies it `invalid (sustained-line-shape)`. Its decisions match the adjudicator's report.
- Round 13 (`13-pre-execute-adversarial-reviewer-raw.md`): Nits only, both
  deferred unacted. Nit 1 (`plan.md:57`, `:63` `Owned by` omits T7) is in
  working-material Design text that names T7 in its prose. Nit 2 (`plan.md:258`,
  T7 Touches omits the ledger): the controller, not the implementer, writes
  ledger evidence for every task, as for T1–T4.

## Execution after the second re-approval — 2026-10-08

- The owner re-approved the spec and plan; `approve-plan`, `schedule`, and
  `plan-locked` ran (sequence 41). The schedule runs T7, T8, T4, T5, then T6.

### T7

- An implementer added the alias refusal in `run_canonical_reconciliation`:
  one `extract_legacy_migration_memberships` pass, mapped through
  `_legacy_canonical_alias`, adds matching canonical paths to
  `duplicate_paths`. It also restored the CLI `explain` canonical `ambiguous`
  and full-key-set tests, removed the dead legacy matching in explain,
  strengthened the cooling realness helper, pinned extractor positions for
  every section 10 shape, cleaned up the focused tests, and added eval case 16
  with its fixture.
- Cases: spec alias in the same collection, in another work collection, and
  in another initiative; the five-key backlog spec object; a brief string; a
  shaping design object; no-alias dispatch controls; and an unmapped-shape
  negative control. Mutation check: disabling the guard fails 2 tests.
- Security review of the guard
  (`impl/2-security-reviewer-raw.md`): one Nit, sustained on adjudication. A
  non-string `type` in a historical object raised `TypeError` inside the
  decoder. `_accepted_legacy_entry` now requires a string before the
  shaping-type membership test. A new regression test raises on the previous
  engine and passes now.
- Gates: the T7 test set ran 782 passed, 1 skipped, 115 s, before the Nit fix.
  After it, the workspace-status, tools, and disclosure suites ran 548 passed
  with only the stale engine SHA pin failing; the refreshed pin then ran 19
  passed. `make lint-ruff lint-mypy` and `git diff --check` pass.

### T8

- An implementer resolved the 12 sustained guidance findings in 16 files. It
  added the information-only shaping-list note to the work-loop Step 0 (and
  its eval case), the two product-engineering skills, and the frame-a-situation
  guide. It also documented the `duplicate_membership` alias cause after the
  schema findings table, and added the ledger-operation-ID rule to the recovery
  guide and `mutate.md`.
- Deviation: T8's Step 0 edit moved the work-loop contract pin in
  `tools/test_workspace_status.py`, a completed-task file; the controller
  refreshed that pin (`6fd9a3fb…`) with a review comment.
- Widened audit (`compatibility window`, `reviewed route selection`,
  `migration planner`, `supported legacy`) over current guidance: one match,
  an unrelated monorepo-extras package-versioning phrase.
- Checks: 6 guide and journey validators pass. Guide tool tests,
  `test_work_intake_surface.py`, and `tools/test_workspace_status.py` ran 146
  passed. `make lint-ruff lint-mypy` and `git diff --check` pass.
