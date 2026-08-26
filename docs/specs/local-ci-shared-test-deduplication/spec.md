# Spec: Local CI shared-test deduplication

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017; ADR-0086; ADR-0096;
  `docs/specs/local-ci-orchestration/` (Shipped; AC1 superseded in part by
  ADR-0096)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Contributors can run one `make ci` without executing the same five shared test
files once in `build-check` and again in `test`. The composed route retains every
existing semantic gate and keeps standalone `make build-check`, standalone
`make test`, and the make-free Windows build-check route complete and
independent.

## Boundaries

### Always do

- Keep `build-check` as the owner of the shared executions inside `make ci`, so
  each linter's self-test remains before its linter and retains current
  fail-fast attribution.
- Preserve every current `build-check`, `test`, SAST/SCA, pre-PR, verdict, and
  pack-isolation behavior outside the explicitly composed `make ci` route.
- Make the five-file ownership set explicit, fail closed on drift, and keep all
  composition state local to one Make invocation.
- Keep direct-script and pytest execution equivalent through a mechanically
  checked explicit case contract before treating a file as shared work.
- Leave the worktree free of bytecode, pytest caches, and measurement residue.

### Ask first

- Change the five-file shared set, move ownership away from `build-check`, or
  change the approved `ci` prerequisite graph.
- Accept ADR-0096 and add its status-only, in-part supersession pointers to the
  frozen local-CI spec and plan.
- Change a shared test's semantic contract instead of aligning its two existing
  runner surfaces.
- Replace the narrow Make composition with a reusable runner, manifest
  protocol, cache, receipt, or other cross-gate coordination mechanism.

### Never do

- Remove a shared self-test from standalone `build-check` or from standalone
  `test`, or let both halves of the composed graph exclude it.
- Infer composition from `MAKECMDGOALS`, timestamps, Git revisions, marker
  files, caches, receipts, ambient environment alone, or machine-global state.
- Consolidate unrelated pytest processes or weaken pack-test directory
  isolation.
- Change `coordination_lease.py`, run-slot policy, concurrency limits,
  `.github/workflows/**`, SAST/SCA commands or ordering, pip-audit behavior,
  terminal verdict wording, or either frozen body in
  `docs/specs/local-ci-orchestration/`.
- Address the other Python-process opportunities, collect-only floors,
  pack-module namespace debt, bytecode caching, or in-process gate conversion.

## Testing Strategy

- **TDD, construction:** parse and execute the real build-chain and Make
  orchestration surfaces to prove exact ownership, standalone completeness,
  recursive selection, parallel ordering, fail-closed drift, and failure
  propagation. Mutation-shaped negative cases establish that each assertion
  can go red.
- **TDD, characterization:** compare real pytest node IDs for the three core
  files; make direct and pytest workspace-status execution consume one case
  registry; and compare the CLI file's unittest and pytest collections while
  pinning its isolated setup and expected platform skip.
- **Goal-based integration:** run focused build-chain, Make-graph, parity,
  SAST-reachability, Python-selection, workspace-status, work-loop, and
  receive-brief suites, followed by one `SKIP_SAST=1 make ci` attempt.
- **Goal-based measurement:** repeat the baseline command interception and
  collection-plan timing method, reporting file executions, outer launches,
  measured nested children, and wall time separately.

TDD stub coverage at PLAN: AC1-AC15 are represented by the T1/T2 construction
stubs in `plan.md`; AC17 is covered by exact verdict construction checks plus
T3's final composed-run check. AC16 and AC18 use goal-based checks and have no
code stub. Repository test files remain untouched until the human approves the
plan, as required by this change's phase boundary.

## Acceptance Criteria

- [x] **AC1 — Exact shared set.** The composed ownership set is exactly:
  `packs/core/tests/skills/work-loop/test_lint_spec_status.py`,
  `packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py`,
  `packs/core/tests/skills/work-loop/test_lint_traceability.py`,
  `tools/test_workspace_status.py`, and
  `tools/test_workspace_status_cli.py`; construction coverage enumerates and
  mechanically checks all five.
- [x] **AC2 — Standalone build-check.** Standalone `make build-check`,
  `SKIP_SAST=1 make build-check`, and
  `python tools/repo/build_gate_chain.py build-check` retain every current
  build-check step, including the five shared tests exactly once and in their
  existing self-test-before-lint order.
- [x] **AC3 — Windows route.** The make-free Windows build-check keeps the same
  shared tests, shell-free argv, working directories, fail-fast behavior, and
  failure attribution.
- [x] **AC4 — Standalone test.** Standalone `make test` retains the complete
  current test surface, including all five shared files, with the same flags,
  working directories, ordering, and per-skill process boundaries.
- [x] **AC5 — Composed exactly once.** One `make ci` executes every semantic
  case in the exact shared set once in total, owned by `build-check`; the
  composed test half excludes no other file or case.
- [x] **AC6 — No double skip.** A shared test cannot be excluded from both
  halves, and a missing, renamed, uncollected, or unexpectedly skipped shared
  test fails the owning gate or a construction test instead of producing a
  false green.
- [x] **AC7 — Drift fails closed.** Removing or renaming a shared test, changing
  its build-check owner, adding a stale composed exclusion, dropping an
  exclusion, or excluding an unrelated test makes focused construction
  coverage fail.
- [x] **AC8 — Failure attribution.** A failing shared build-check test fails
  composed `ci` with its build-check label or test path; an absent shared test,
  double-skip mutation, stale exclusion, and unrelated test failure each have a
  red failure-injection case.
- [x] **AC9 — Invocation-local composition.** The implementation creates no
  persistent cache, timestamp, receipt, marker, Git-derived state, or
  cross-invocation result.
- [x] **AC10 — No ambient reduction.** No ambient environment value or
  command-line override can make standalone `make test` select the reduced
  test recipe.
- [x] **AC11 — Recursive and parallel Make.** Real GNU Make 3.81 construction
  coverage proves that the lease-wrapped recursive Make selects the intended
  full or composed target and that `make -j` cannot start the reduced half
  before its `build-check` owner succeeds.
- [x] **AC12 — Build-check internals unchanged.** Catalogue verification,
  persistent build, pre-PR aggregation, repository lints, self-test-before-lint
  ordering, SAST/delegation decision, and terminal build-check verdict behavior
  remain unchanged.
- [x] **AC13 — Governance, security, and workflow posture.** Accepted ADR-0096
  licenses the direct-prerequisite change, and the frozen local-CI spec and
  plan receive only their permitted Status-line in-part supersession pointers.
  SAST/SCA commands,
  scanner ordering, pip-audit behavior, GitHub workflow files, required-check
  boundaries, and terminal verdict wording remain byte- and behavior-unchanged.
- [x] **AC14 — Pack isolation unchanged.** Every non-shared pack-test command
  retains its existing target, flags, working directory, ordering, and process
  boundary; no skill directories are combined.
- [x] **AC15 — Runner equivalence pinned.** The three core files expose the same
  node IDs, fixtures, skips/xfails, and exit semantics under their two pytest
  routes. `tools/test_workspace_status.py` has one explicit case registry used
  by both direct and pytest runners. The CLI file's unittest and pytest routes
  collect the same methods, preserve expected platform skips, and remain
  order-independent through isolated per-test state.
- [x] **AC16 — Comparable measurement.** The final report gives before/after
  file executions, outer Python/pytest launches, measured nested workspace CLI
  children, and comparable elapsed time without claiming measurements the
  environment could not provide.
- [x] **AC17 — Full composed verdict.** One final `SKIP_SAST=1 make ci` attempt
  preserves the repository's explicit incomplete-SAST wording and exit
  behavior; if the managed cleanup denial prevents the route from reaching the
  verdict, focused construction evidence pins it and the limitation is
  reported separately without changing a gate.
- [x] **AC18 — Clean handoff.** `git status --short` and `git diff --check` are
  clean of generated bytecode, pytest cache, temporary measurement files, and
  unrelated edits at handoff.

## Assumptions

- Technical: the checked-out `HEAD` and local `origin/main` both resolve to
  `8f0e307b561fb06677a5084c7c8c04b3d494929d`; the enterprise policy forbids the
  work-loop freshness fetch, so no ref was updated (source: local Git probes
  2026-08-25).
- Technical: the three core pytest files collect 31, 15, and 45 identical node
  IDs under their build-check and Make-test routes (source: focused pytest
  collection probes 2026-08-25).
- Technical: `tools/test_workspace_status.py` is not currently equivalent: its
  direct `CASES` list has 84 cases, pytest exposes 79 wrappers, and their
  intersection is 77; the contract must be aligned before composed exclusion
  (source: AST inventory and source audit 2026-08-25).
- Technical: `tools/test_workspace_status_cli.py` exposes the same 158
  `unittest.TestCase` methods to direct unittest and pytest collection; their
  order differs, but mutable fixtures are per-test and persistent module names
  are unique (source: loader/pytest collection and state-mutation audit
  2026-08-25).
- Technical: GNU Make 3.81 is the observed supported local Make and must be
  covered by real-Make tests (source: `make --version`, 2026-08-25).
- Process: the shipped `local-ci-orchestration` spec directory is frozen and
  does not own this new composition contract; changing its pinned AC1 requires
  an ADR-backed, Status-line-only partial-supersession pointer on both frozen
  files (source: `docs/CONVENTIONS.md` and canonical workspace status
  2026-08-25).
- Process: work-intake routes this repo-origin `start/spec` request to
  `work.queue` and the `new-spec` processor (source: canonical
  `intake_router.route_intake` probe 2026-08-25).
- Product: the exact scope, exclusions, ownership presumption, investigation
  boundary, and human approval checkpoint come from the owner's session prompt
  (source: user confirmation 2026-08-25).
