# Spec: Local pytest process optimization

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071; ADR-0094; ADR-0096; [`local-ci-shared-test-deduplication`](../local-ci-shared-test-deduplication/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Local repository gates spend less time on repeated pytest startup, collection,
and interpreter churn while remaining trustworthy in isolation. Standalone
`make test` and composed `test-after-build-check` preserve their existing test
ownership and semantic surfaces, compatible root/tool tests share only
evidence-backed pytest sessions, and four existing collection floors execute in
the same pytest processes as their real tests. Every retained process boundary
has a recorded correctness reason, and the historically dangerous
source-resolution direction remains independently guarded.

## Exact optimization contract

This section is the canonical home for approval-sensitive values. Tables in
`plan.md` may display these values beside commands and evidence, but they are
derived views; this section controls if a drafting error creates a conflict.

| Floor owner | Minimum collected items | Characterized baseline items |
| --- | ---: | ---: |
| `packs/desk-research/tests/skills/desk-research/` | 9 | 15 |
| `packs/desk-research/tests/skills/desk-research-project-start/` | 7 | 8 |
| `packs/catalogue-curation/tests/skills/assimilate-primitive/` | 30 | 30 |
| `packs/catalogue-curation/tests/skills/assimilate-repo/` | 7 | 7 |

The sole approved new root/tool compatibility class contains exactly:

- `tools/test_import_time_path_leaks.py`
- `tools/test_managed_child.py`
- `tools/test_coordination_lease.py`
- `tools/test_branch_added_paths.py`
- `tools/test_bootstrap.py`

All other pre-existing root/tool classes remain separate. The canonical outer
root/tool counts are 19 → 15 for standalone and 18 → 14 for composed. Ordinary
floor probes are 4 → 0 while the four real floor-bearing executions remain
4 → 4. The specialized import-path child remains unchanged.

A candidate is materially regressive when median focused wall time rises both
more than 10 percent and more than 2 seconds, or peak resident memory rises both
more than 10 percent and more than 16 MiB.

## Boundaries

### Always do

- Preserve the exact pre-existing standalone `make test` semantic union and the
  exact composed `test-after-build-check` union, including the shipped five-file
  Opportunity-1 ownership contract, with every applicable pre-existing root/tool
  node ID executed exactly once.
- Keep every pack and skill test process boundary unchanged, preserve explicit
  paths, working directories, source-package resolution, environments,
  skip/xfail/warning/error behavior, failure propagation, and every existing
  node ID. The only pack-invocation argument/plugin changes are the explicit
  one-pass floor options on the four owners in the Exact optimization contract;
  their membership, process boundaries, cwd, environment, and existing pytest
  configuration remain unchanged.
- Require isolated, combined, reversed-order, source-resolution, failure-shaped,
  wall-time, CPU-time where available, and peak-RSS evidence before removing a
  root/tool process boundary; retain a boundary when evidence is ambiguous.
- Enforce the four minima in the Exact optimization contract from pytest's real
  collected items in the owning execution, before any test body runs when the
  floor is unmet, with no persistent state.
- Keep the make-free build-chain argv shell-free and Windows-valid, including
  exact `cwd`, `_source_packages_env()`, `-q`, and existing
  `-p no:cacheprovider` behavior.
- Retain the specialized child collection in
  `tools/test_import_time_path_leaks.py` unless every full-roster,
  sanitized-environment, carrier, attribution, collection-error, and
  anti-vacuity invariant has an exact proven replacement.
- Leave the worktree without bytecode files, pytest cache files, measurement
  output, generated artifacts, or other task residue.

### Ask first

- Change any test or gate membership, add a previously unexecuted tool test,
  remove an existing test, or change an existing node ID.
- Change the workspace-status pair's Opportunity-1 composition, remove or
  materially redesign the import-time path guard, or change the approved `ci`
  prerequisite graph.
- Modify `.github/workflows/**`, add a repository-wide test manifest or general
  execution engine, change production code only to make sessions compatible,
  add an ADR, or alter a shipped/frozen spec body.
- Accept a consolidation whose measured median wall time or peak resident
  memory crosses the plan's material-regression threshold.

### Never do

- Consolidate `packs/*/tests` globally or remove documented skill-level process
  isolation for duplicate test basenames and ambiguous sibling imports.
- Introduce pytest-xdist, background or parallel test execution, a persistent
  daemon, process pool, test server, machine-wide coordination, or changes to
  coordination leases, run-slot policy, or concurrency limits.
- Replace the explicit root/tool roster with broad `pytest tools/`, accept a
  green combined run as sole compatibility evidence, or weaken isolation to
  optimize a process-count headline.
- Rely on timestamps, caches, marker files, Git revisions, prior-run receipts,
  or ambient environment variables to select a reduced or altered profile.
- Hide collection floors in shell-output parsing or expand into bytecode-cache,
  pack-namespace, broad in-process gate, scheduling, or language-rewrite work.

## Testing Strategy

- **Collection-floor semantics — TDD at unit and subprocess-integration
  surfaces.** Focused tests make below-floor, zero, collection-error, partial
  collection, interrupted collection, real test failure, ordinary opt-out, and
  pre-body failure observable before the opt-in pytest plugin exists.
- **Build-chain and Make wiring — TDD construction tests.** Existing
  `tools/test_build_gate_chain.py` and
  `tools/test_local_ci_shared_test_deduplication.py` derive argv, cwd,
  environment, roster membership, profile ownership, and process topology from
  the real sources; mutation-shaped copies prove omissions, duplicates, stale
  exclusions, collection failures, and path leaks make those tests red.
- **Compatibility classes — goal-based characterization plus focused
  integration tests.** Isolated and grouped collections must have the same
  non-empty node-ID union, skip/xfail disposition, rootdir, config, import
  resolution, and outcome under approved file orders and repeated clean
  processes. The existing import-path guard receives a controlled mutation to
  prove it still detects the historical defect.
- **End-to-end gate preservation — goal-based checks.** One final `make test`
  and one final `SKIP_SAST=1 make ci` exercise the public standalone and
  composed routes. The latter retains the repository's documented incomplete
  SAST verdict rather than being presented as a full pass.
- **Performance and hygiene — goal-based measurements.** Comparable focused
  repeated runs report medians for wall time, CPU time where available, and
  peak RSS where available; final status and diff checks prove no repository
  residue. No browser or visual QA applies.

TDD stub coverage is recorded per task in `plan.md`: all implementation tasks
have concrete pytest-shaped red stubs; measurement and final convergence are
goal-based and declare no stub.

## Implementation evidence

Evidence was recorded on the approved `f871fe506053ea17dd1702ccea37c802b78de557`
checkout on 2026-08-26. Git refs were not changed.

- Wave A began with 15 focused failures against the missing plugin and the
  probe-plus-run owners. The final contract has one pure-stdlib opt-in plugin,
  no terminal-output parsing, no stream capture, and exactly one real pytest
  child for each 9, 7, 30, and 7 floor. The real suites collected 15, 8, 30,
  and 7 items. Plugin/build-chain focused verification passed 14 tests and 12
  subtests; the unaffected build-chain surface passed 33 tests and 28 subtests
  with the six policy-denied cleanup cases exactly deselected.
- Wave B began with the real Make topology red at 19 standalone and 18
  composed outer root/tool processes. The final expansions are 15 and 14. The
  workspace-status pair remains one standalone-only class, all pack lines are
  unchanged, and the only new class is the five paths in the Exact optimization
  contract. Its isolated, forward, and reverse collections are the same 58
  unique node IDs with sorted hash
  `efa4ae209fbba434d71b9c090415ed0c77d6f14674094f410a992def9082bdc3`;
  skip/xfail-selected subsets also match. The first existing tool batch moved
  from 323 to 346 nodes solely because 23 approved construction tests were
  added to its two already-owned files, so the inferred post-change totals are
  1,765 standalone and 1,521 composed while every pre-existing node remains.
- State controls fail on persistent environment, cwd, logging, warnings,
  signal, locale, timezone, asyncio-policy, non-daemon-thread,
  multiprocessing-child, and designated-filesystem changes. Collection allows
  only the characterized repo-root +1 and `tools/` +2 path delta; package-path
  counts and watched resolution remain unchanged. A temporary packaged-source
  mutator was attributed by the retained broad child, and a synthetic grouped
  test failed with normal pytest file/node attribution. The construction suite
  passed all 26 tests.
- The exact focused candidate measurement remains the applicable runtime
  evidence because the measured grouped argv is byte-for-byte the command now
  expanded by Make and none of its five participant files changed: isolated
  median wall 40.402 s, child CPU 18.184 s, peak RSS 99,483,648 bytes; grouped
  median wall 29.641 s, child CPU 13.662 s, peak RSS 99,401,728 bytes. The
  post-wiring durable verifier recorded grouped wall summaries of 23.40,
  23.59, and 22.99 seconds; it did not remeasure CPU or RSS, so the comparable
  pre-wiring medians remain the resource claim.
- Canonical `make lint-ruff` and `make lint-mypy` passed. The initial
  authorized `make test` attempt exited 2 after approximately 325 seconds
  inside its first unchanged `packages/agentbundle/tests/` process because
  Python directory cleanup is policy-denied. After the reviewer fix, one final
  standalone attempt again exited 2 in that same first process with widespread
  `PermissionError: os.rmdir` failures and never reached the changed routes.
  The one authorized `SKIP_SAST=1 make ci` attempt exited 2 after 15.2 seconds
  in unchanged catalogue verification cleanup and likewise never reached the
  changed routes. These are environment failures, not green public-gate
  verdicts; none was weakened or retried after its post-fix confirmation.
- Ordinary collection-only floor processes are 4 → 0, real floor processes
  remain 4 → 4, and the specialized import-time broad collector remains one
  nested child per owning guard invocation. Other test-owned Python children
  were not exhaustively counted and no nested-child reduction is claimed.
- Post-GATES round 1 sustained one blocker: all 58 real bodies still needed
  post-wiring execution under the checked-in state guard. The first supported-
  profile attempt exposed a guard false positive: its setup-phase baseline
  included pytest's two runner-owned `LogCaptureHandler` instances, while its
  post-final-teardown snapshot correctly did not. The guard now excludes only
  that exact pytest-owned handler class while retaining participant logger and
  handler state; the `logging.NullHandler` mutation control still fails. Its
  warning-filter control was also moved to the outer runtest-protocol boundary
  so pytest cannot restore the synthetic leak before the next-file comparison.
  The corrected guard passed all five files separately (4, 16, 21, 7, and 10
  bodies), then the exact group forward (58), reverse (58), and forward again
  (58), with no unexplained state or source-resolution delta.
- Post-GATES round 2 required that evidence to be durably rerunnable. The
  checked-in command
  `python3 tools/test_local_ci_shared_test_deduplication.py --verify-approved-compatibility-class`
  now owns the exact eight-session fail-fast sequence and reproduced the same
  isolated and 58/58/58 grouped outcomes. Its focused construction test pins
  every path, order, path allowance, and early-failure behavior without running
  those 232 repeated bodies during ordinary `make test`; adding them to the
  default route would violate the exact-once semantic surface this spec owns.
- Post-GATES round 3 required real deep-cwd plugin evidence beyond the existing
  argv/env/cwd construction assertions. A focused integration test now invokes
  the production `_pytest_step_cwd` closure from both catalogue suite
  directories with `_source_packages_env()` and `-p no:cacheprovider`. A
  one-item success asserts the repository rootdir, `pyproject.toml` config, and
  loaded `tools.pytest_collection_floor` plugin; a one-item/two-floor run exits
  1 before its failing body; and a collection exception exits natively with 2
  instead of becoming a low-count diagnostic. The integration node and ten
  adjacent plugin/build-chain tests passed, with six subtests.

## Acceptance Criteria

- [x] **AC1 — Exact standalone surface.** Standalone `make test` executes every
  pre-existing root/tool node ID in its approved explicit roster exactly once,
  with no omission, duplicate, newly discovered test, or changed existing node
  ID; approved construction tests added inside already-owned files are the only
  new node IDs.
- [x] **AC2 — Exact composed surface.** `test-after-build-check` preserves the
  shipped five-file ownership contract: build-check owns all five, the composed
  test route owns none, every other standalone node remains owned exactly once,
  and standalone `make test` still owns the five once.
- [x] **AC3 — Explicit isolation classes.** The Make surface names every
  root/tool compatibility class with explicit test paths, and every retained
  process boundary has an evidence-backed rationale in the plan.
- [x] **AC4 — Evidence-backed mergers.** Every removed boundary has non-empty
  isolated collection, exact combined union, forward and reversed order,
  repeated execution, source-resolution, failure-shaped, and resource evidence;
  ambiguity retains the boundary.
- [x] **AC5 — Pack boundaries unchanged.** Every current pack or skill test
  directory remains in its own existing pytest process with unchanged command
  membership and ordering.
- [x] **AC6 — Four one-pass floors.** Each owner in the Exact optimization
  contract launches one real pytest process carrying its canonical minimum;
  its ordinary collect-only process is absent.
- [x] **AC7 — No vacuous floor pass.** Missing, renamed, zero-item,
  uncollectable, and under-floor suites fail, and a low count cannot be confused
  with a collection error.
- [x] **AC8 — Floor failure precedes execution.** An unmet floor stops in the
  real pytest collection phase before any test body executes and reports the
  suite, actual collected count, and expected minimum.
- [x] **AC9 — Native pytest outcomes preserved.** Collection errors and
  interrupted collection retain pytest's failure behavior, real test failures
  retain their status, and the mechanism is inactive unless explicitly loaded
  and requested.
- [x] **AC10 — Invocation parity.** All four suites retain their cwd,
  environment, rootdir, configuration, plugin resolution, standard streams,
  and existing flags; both catalogue-curation invocations retain exact
  `_source_packages_env()` and `-p no:cacheprovider` behavior.
- [x] **AC11 — Windows parity.** The catalogue-curation floor commands remain
  list argv with `shell=False` semantics and valid direct make-free Windows
  path handling; later build-chain steps do not run after a floor, collection,
  or test failure.
- [x] **AC12 — Source-resolution parity.** Approved grouped sessions resolve
  `agentbundle`, `credbroker`, and watched packaged-source paths from the same
  intended locations as isolated sessions, before and after collection, in
  every approved order.
- [x] **AC13 — Order independence.** Each approved group has the same
  collection and execution outcome under forward and reversed explicit file
  order and the focused repeated orders defined by the plan.
- [x] **AC14 — Failure detection remains trustworthy.** Construction controls
  prove a missing or duplicated grouped path, grouped test failure, stale
  Opportunity-1 exclusion, under-floor suite, collection failure, source-path
  mutation, and leaked child/global state cannot silently pass.
- [x] **AC15 — Specialized guard preserved.** The import-time path-leak child
  retains its broader `tools` plus `tests` collection, sanitized `PYTHONPATH`
  and `PYTEST_ADDOPTS`, carrier modules, declared-package baseline, attribution,
  continue-on-collection-errors behavior, anti-vacuity floor, and ability to
  catch the original fails-alone/passes-combined defect.
- [x] **AC16 — Opportunity-1 composition preserved.** Workspace-status tests
  run exactly once in standalone test, never in `test-after-build-check`, and
  once under build-check in composed CI; recursive and parallel Make cannot
  double-run or omit the shared contract.
- [x] **AC17 — Measured process reduction.** Claims derive from the expanded
  real command plans and separately report standalone and composed root/tool
  outer pytest launches, ordinary floor probes, real floor executions, measured
  nested Python children, and specialized children intentionally retained.
- [x] **AC18 — No material performance regression.** Comparable focused
  medians and peak RSS remain within the approved thresholds, or any exception
  receives explicit human approval before implementation continues.
- [x] **AC19 — Failure attribution remains clear.** Consolidated output retains
  pytest node/file attribution and any group failure fails its owning Make
  route without being converted to a count-only diagnostic.
- [x] **AC20 — No persistent or ambient profile state.** The floor and grouping
  mechanisms use explicit argv/Make text only and create no receipt, cache,
  daemon, environment-selected reduced profile, or persistent coordination
  state.
- [x] **AC21 — Protected surfaces unchanged.** No workflow, gate membership,
  SAST/SCA behavior, machine coordination, shipped/frozen spec body, ADR body,
  or import-time guard implementation changes without separately approved
  scope.
- [x] **AC22 — Clean completion.** Focused gates, `make test`, and
  `SKIP_SAST=1 make ci` receive honest recorded outcomes; adversarial and
  quality reviews are clean; `git diff --check` passes; and no bytecode, pytest
  cache files, temporary measurements, or generated artifacts remain.

## Assumptions

- Technical: the checked-out Make expansion establishes the canonical baseline
  root/tool counts in the Exact optimization contract, with the
  workspace-status pair as the one composed omission (source: `Makefile`
  expansion and focused command-plan probe at
  `f871fe506053ea17dd1702ccea37c802b78de557`).
- Technical: the pre-change root/tool roster contains 1,742 unique standalone
  node IDs and 1,498 unique composed node IDs; the 244-node difference is the
  workspace-status pair (source: isolated pytest collection inventory,
  2026-08-26).
- Technical: the Exact optimization contract's floor/actual pairs and their
  current two-pass cwd, environment, flags, and failure behavior are confirmed
  by `Makefile`, `tools/repo/build_gate_chain.py`, and focused collection probes
  (source: repository and probe evidence, 2026-08-26).
- Technical: a pure-stdlib, explicitly loaded pytest plugin using the public
  collection hook is the narrowest one-pass mechanism that preserves deep-cwd
  rootdir/import behavior and native collection interruption; wrapper and
  conftest prototypes are broader or alter loading (source: focused plugin,
  cwd, collection-error, and interrupt probes, 2026-08-26).
- Technical: only the five-file tool class named in `plan.md` has complete
  isolated, exact-union, forward/reverse, repeated, import-resolution,
  mutation-control, CPU, wall-time, and RSS evidence; every other proposed
  merger remains isolated (source: focused compatibility experiment,
  2026-08-26).
- Process: the base-freshness command is skipped because it force-fetches and
  updates a protected remote-tracking ref. At investigation start, local `HEAD`
  and local `origin/main` both named
  `f871fe506053ea17dd1702ccea37c802b78de557`; during plan review the external
  ref moved to `fdacdb66c481c92035e5626a32e4f43579d78180` while the checkout
  remained unchanged. The owner approved completing this initiative on the
  investigated `f871fe5` source and resynchronizing later; the worktree was
  clean before intake artifacts were added (source: read-only Git probes and
  user approval 2026-08-26).
- Process: managed policy denies Python `os.rmdir`, so cleanup-sensitive
  characterization failures are recorded once and not retried or weakened;
  ambiguous boundaries remain intact and supported CI owns those cases (source:
  user enterprise constraint and focused HEAD executions, 2026-08-26).
- Product: the Exact optimization contract's material-regression rule is the
  approved acceptance boundary (source: user confirmation 2026-08-26).
- Product: the Exact optimization contract's candidate class and retained
  boundaries are the approved optimization shape (source: user confirmation
  2026-08-26).
