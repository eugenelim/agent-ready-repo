# Plan: Local CI shared-test deduplication

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `Makefile`; `tools/repo/build_gate_chain.py`;
  `tools/test_build_gate_chain.py`; `tools/test-lint-ci-parity.py`;
  `tools/test_catalogue_tooling_rewire.py`; the five shared test files;
  `docs/specs/local-ci-orchestration/` (frozen precedent and constraint)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn while it is Drafting. Once
> approved, substantive replanning returns to the human gate.

## Approach

Keep `build-check` as the sole owner of the five shared executions inside the
composed route. Add an explicit, lease-wrapped `test-after-build-check` target
whose prerequisite edge to `build-check` makes serial and parallel Make wait
for that owner, and whose recursive unleased target expands the existing test
recipe with only three exact `--ignore` arguments and one explicitly omitted
workspace-status pytest command. Standalone `test` expands the same recipe
without exclusions. Before exclusion, replace the mismatched manual wrappers in
`tools/test_workspace_status.py` with one 86-case registry consumed by both the
direct runner and one parametrized pytest node family.

This is Option A plus the smallest recipe parameterization needed to avoid a
second copy. Accepted ADR-0096 licenses its narrow partial supersession of the
shipped direct-prerequisite contract. It introduces no profile variable,
runtime manifest, persistent state, or general runner.

## Investigation evidence

### Current graph and baseline

`ci` currently has direct prerequisites `build-check lint-ruff lint-mypy test`.
`build-check` acquires the coordination lease, runs the make-free Python gate
chain, then takes the existing SAST/delegation branch. `test` independently
acquires the same kind of lease and recursively runs `test-unleased`.

The five candidate files each enter both halves, so one current `make ci` has
10 candidate file executions. The build-check half uses five outer processes
(three pytest, two direct Python). The test half uses three candidate-bearing
pytest processes (work-loop directory, receive-brief directory, and the two
workspace files together), for eight candidate-bearing outer launches total.
The selected route preserves the two directory processes because they still own
other tests and removes the now-empty workspace pair process: 10 → 5 file
executions and 8 → 7 candidate-bearing outer launches.

Current overlap by semantic case is 326 executions: 31 + 15 + 45 + 77 + 158.
Aligning the workspace-status registry adds the nine one-sided cases to both
standalone routes, producing a 335-case shared contract that composed `ci`
executes once. Baseline collection of the three Make-test-side commands took
6.439 seconds on the managed host (two consecutive focused observations were
6.546 and 6.439 seconds); this is collection/launch timing, not an execution
runtime claim. A focused execution of the 31 spec-status tests completed their
assertions and then reported 31 cleanup failures in 19.38 seconds because the
managed profile denies `os.rmdir` in `TemporaryDirectory.cleanup`. Per the
enterprise rule, that case is recorded once and is not retried or weakened.
Nested child-process savings are not yet claimed: source proves equivalent
functions invoke the same helpers, but the environment did not permit a clean
dynamic execution count.

### Equivalence matrix

| Test file | Build-check label | Build runner / cwd / command | Build environment | Make-test route | Collected cases | Nested behavior | Verdict and evidence |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| `packs/core/tests/skills/work-loop/test_lint_spec_status.py` | `test-lint-spec-status` | `_pytest_step`; repo root; `python -m pytest <file> -q` | In `make ci`, inherits exported source `PYTHONPATH` and `PYTHONDONTWRITEBYTECODE`; direct Python chain adds no pytest options | work-loop directory process; `python -m pytest packs/core/tests/skills/work-loop/ -q` | 31 / 31 | Cases launch the same linter subprocesses under both routes | Equivalent. Focused individual and directory collection produced the same ordered 31 node IDs; same root config, plugins, conftest, cwd, flags, fixtures, and no candidate xfails/skips. |
| `packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py` | `test-lint-brief-coverage` | `_pytest_step`; repo root; `python -m pytest <file> -q` | Same inherited Make environment; direct chain remains repo-relative | receive-brief directory process; `python -m pytest packs/core/tests/skills/receive-brief/ -q` | 15 / 15 | Each route calls the same `run_lint` subprocess helper | Equivalent. Same ordered node IDs, root config/plugins/cwd/flags, no local conftest or fixture difference, and no candidate skip/xfail. |
| `packs/core/tests/skills/work-loop/test_lint_traceability.py` | `test-lint-traceability` | `_pytest_step`; repo root; `python -m pytest <file> -q` | Same inherited Make environment | work-loop directory process; same command as first row | 45 / 45 | Both routes execute the same linter/import helpers; symlink fallback is the same node-level policy | Equivalent. Same ordered 45 node IDs and runner context. The work-loop conftest only supplies an unused legacy fixture. |
| `tools/test_workspace_status.py` | `test-workspace-status` | `_script_step`; repo root; `python tools/test_workspace_status.py` | Inherits caller environment; custom `main` aggregates failures and `SkipTest` | combined tools pytest process; `python -m pytest tools/test_workspace_status.py tools/test_workspace_status_cli.py -q` | 84 direct / 79 pytest; 77 common | No subprocess import or launch appears in the file; cases exercise the in-process engine | **Not equivalent now.** Seven migration cases are direct-only; two spec-status parser cases are pytest-only. Plan aligns both to the 86-case union through one registry before exclusion. |
| `tools/test_workspace_status_cli.py` | `test-workspace-status-cli` | `_script_step`; repo root; `python tools/test_workspace_status_cli.py`; `unittest.main()` | Inherits caller environment; unittest result/warning presentation | same combined tools pytest process | 158 / 158 methods | Many methods launch the CLI through `_run_cli`; exact nested launch count was not measured | Semantically equivalent. Default unittest and pytest collect the same methods. Order differs, but `_CliBase` creates a fresh temp root per test, class setup is read-only source caching, persistent module injections use unique names, and `skipIf(win32)` is shared. Characterization coverage pins this relationship. |

### Runner comparison details

- The three core `_pytest_step` calls and their Make pytest collectors run from
  the repository root with `-q`, the same root `pyproject.toml`, plugins, and
  candidate conftest exposure. Focused collection used
  `-p no:cacheprovider --collect-only` only to avoid investigation residue; it
  was not treated as production equivalence evidence for plugins.
- The Makefile exports source-package `PYTHONPATH` and disables bytecode. A
  direct make-free Windows chain does not depend on those Make exports for the
  five repo-relative tests. No production command gains `-p no:cacheprovider`.
- `test_workspace_status.py` uses a custom `main`, not `unittest.main`; its
  current manual pytest wrappers are a distinct contract and cannot be omitted
  until both runner entrypoints consume one registry.
- `test_workspace_status_cli.py` uses ordinary `unittest.main()`. Pytest's
  unittest collection changes presentation and ordering, not the test methods,
  setup/cleanup hooks, platform skip, assertions, or non-zero failure result.

## Candidate implementation shapes

| Option | Assessment | Decision |
| --- | --- | --- |
| A — explicit composed test target | Names the composition at the Make graph, can require `build-check`, reuses the existing lease, has no ambient selector, and lets the standalone target remain literal. A small parameterized recipe avoids duplication. | **Selected.** Narrowest route that makes ownership and ordering observable. |
| B — target-specific composition profile | GNU Make 3.81 `override` assignments can defeat ambient and command-line activation while retaining `test` as the direct prerequisite, but they cannot also create a real `build-check`-before-reduced dependency under `make -j` without changing standalone `test`, serializing more broadly, or adding coordination. | Rejected after a focused Make probe. It cannot satisfy both provenance and parallel ownership without a broader mechanism. |
| C — shared manifest or runner | A five-path manifest could reduce textual drift, but either Make must parse Python-owned data or Python must begin owning the long Make test recipe. The real build steps and recipes are already mechanically inspectable. | Rejected as a runtime mechanism. Construction tests compare the real surfaces directly, avoiding a second authority or a general runner. |

## Constraints

- ADR-0017 keeps SAST/SCA in the developer-facing build-check chain.
- ADR-0086 keeps the GitHub SAST job split and the delegated local branch; no
  workflow or scanner behavior moves.
- Accepted ADR-0096 is the one-decision governance record for the explicit
  composed target. After owner approval it becomes Accepted; the shipped
  local-CI spec and plan receive only the permitted Status-line annotation
  naming the superseded AC1 clause. Their bodies remain byte-unchanged.
- Pack skill test directories retain one pytest process each. Only exact file
  exclusions enter the two already-existing directory processes.
- The enterprise environment permits read-only Git only, so the work-loop
  base-freshness fetch is skipped. HEAD equals the current local `origin/main`.
- Cleanup-sensitive execution uses the one recorded HEAD failure and exact
  deselections for unaffected focused coverage; code and tests are not weakened
  to accommodate the managed `os.rmdir` denial.

## Construction tests

**Integration tests:**

- Focused real-surface suite covering build-chain assembly, local Make graph,
  CI parity, SAST reachability, Python selection and recursive Make,
  workspace-status collection contracts, and failure injection.
- One final `SKIP_SAST=1 make ci` attempt. The expected successful route ends
  with the existing incomplete-SAST verdict; an enterprise cleanup denial is
  reported separately and the unaffected route is checked with exact
  deselections.

**Manual verification:** none. Browser control and Apple builds are irrelevant
to this Make/Python orchestration change.

## Design (LLD)

### Design decisions

- `ci` directly names `build-check`, `lint-ruff`, `lint-mypy`, and
  `test-after-build-check`. The composed test target also depends on
  `build-check`; GNU Make coalesces the duplicate node and the edge prevents a
  parallel ownership race. Traces to AC2, AC5, AC8, AC11, AC12.
- `test` and `test-after-build-check` each acquire the existing coordination
  lease exactly once and recursively select their own unleased target. There is
  no composition variable. Traces to AC4, AC9-AC11.
- One Make recipe macro contains the current test commands. Its lexical
  arguments add exact ignores to the work-loop and receive-brief commands and
  omit the workspace pair line only for the composed target. Blank/broad
  directory ignores are forbidden. Traces to AC4, AC5, AC7, AC14.
- The workspace-status custom runner and pytest parameterization share one
  ordered 86-case registry. The CLI file retains `unittest.main()` and gains
  characterization only. Traces to AC5, AC6, AC15.

### State & control flow

```text
make ci
├── build-check ── lease ── build-check-unleased
│   ├── build_gate_chain.py (owns all five shared tests)
│   └── unchanged SAST/delegation decision + verdict
├── lint-ruff
├── lint-mypy
└── test-after-build-check ── requires successful build-check
    └── lease ── test-after-build-check-unleased
        └── shared test recipe
            ├── work-loop pytest, ignoring exactly two owned files
            ├── receive-brief pytest, ignoring exactly one owned file
            ├── workspace pair invocation omitted
            └── every other command unchanged

make test ── lease ── test-unleased ── same recipe, no exclusions
python tools/repo/build_gate_chain.py build-check ── unchanged five owners
```

### Failure, edge cases & resilience

- If `build-check` fails, the dependency edge prevents the reduced target from
  running; failure output keeps the build-chain label.
- If a path or owner drifts, construction comparison of actual build argv and
  actual Make exclusions fails before a false-green composed route.
- If an unrelated test fails, the shared macro retains Make's ordinary
  fail-fast recipe semantics.
- A directly invoked `test-after-build-check` remains safe because its
  prerequisite runs `build-check`; the internal unleased target is documented
  as an implementation detail, like the existing unleased targets.

## Human approval transaction (pre-EXECUTE gate)

No implementation task is schedulable until this gate is complete. The owner's
explicit response must separately and unambiguously approve the spec scope, the
plan strategy, and the ADR-0096 decision preview below. Using that authority,
the controller performs these governance and baseline operations in order:

1. Create ADR-0096 as Proposed and add its `docs/adr/README.md` row.
2. Treat the same explicit ADR approval as decision-maker sign-off and change
   ADR-0096 to Accepted; do not alter its body after that transition.
3. Before either approval transition, update the ADR index row, this spec's
   `Constrained by` qualifier, this plan's ADR preview status, and the active
   specs index from Proposed/pending to Accepted/current ADR-0096.
4. Add the licensed Status-line-only in-part supersession pointer to the frozen
   local-CI spec and plan; verify all content below each changed Status line
   remains byte-identical.
5. Mark this spec Approved and fire `spec-approved`, then mark this plan
   Approved and fire `plan-approved`.
6. Immediately record the approved baseline with `loop-cohort approve-plan`,
   schedule T1-T3, seal it with `plan-locked`, and change the lifecycle tokens
   to `Status: Implementing` / `Status: Executing` before any code edit.

A rejection or ambiguous approval leaves all four governance artifacts
unwritten and all implementation tasks blocked.

## Tasks

### T1: Both workspace-status runner pairs have mechanically identical semantic collections

**Depends on:** none

**Touches:** `tools/test_workspace_status.py`, `tools/test_local_ci_shared_test_deduplication.py`, `Makefile`

**Mode:** TDD — `tools/test_local_ci_shared_test_deduplication.py` owns the
collection-contract construction tests.

**Tests:**

- Add the exact collection/equivalence characterization first: the three core
  node sets match their directory routes; workspace-status direct and pytest
  both derive from one 86-case registry; CLI unittest and pytest method sets
  match and retain only the expected Windows skip. Verify the test is red
  against the current 84/79 mismatch. (AC1, AC6, AC15)
- Add missing/renamed/uncollected mutations and unexpected skip-shape checks so
  the characterization cannot pass on an empty collection. (AC6, AC7)
- `stub: true` — the following compilable test shape is materialized unchanged
  as the first EXECUTE edit; it is red because the shared registry does not yet
  exist:

```python
# STUB: AC15 — direct and pytest workspace-status routes share one contract
def test_workspace_status_runners_use_the_same_nonempty_case_registry():
    contract = load_workspace_status_case_contract()
    direct = collect_direct_workspace_status_cases()
    pytest_nodes = collect_pytest_workspace_status_cases()
    assert len(contract) == 86
    assert direct == contract
    assert pytest_nodes == contract
```

**Approach:**

- Replace manual pytest wrappers with one parametrized test over the existing
  `CASES` registry and add the two pytest-only cases plus seven direct-only
  cases to the union.
- Keep case functions, failure aggregation, direct diagnostics, working
  directory, and `main` exit behavior intact.
- Add the new focused construction file to the existing tools pytest command;
  do not add or consolidate a process.

**Red-green-refactor evidence:** record the current 84/79 red comparison, the
86/86 green comparison, then simplify only duplicated wrapper wiring while the
case functions remain unchanged.

**Done when:** focused collection reports the same ordered 86 semantic case IDs
for direct and pytest workspace status, the CLI method sets match, and all
three core node-set comparisons are green.

### T2: `make ci` selects one explicit reduced test route without changing standalone gates

**Depends on:** T1

**Touches:** `Makefile`, `tools/lint-ci-parity.py`,
`tools/test-lint-ci-parity.py`, `tools/test_catalogue_tooling_rewire.py`,
`tools/test_local_ci_shared_test_deduplication.py`

**Mode:** TDD — the new construction file owns actual-Make graph, command-plan,
and failure-injection coverage; `tools/test-lint-ci-parity.py` owns parity-roster
mutation coverage.

**Tests:**

- First extend the real Make/build-chain construction tests to assert the exact
  five build owners, full standalone test coverage, exact composed exclusions,
  a once-only composed union, no unrelated exclusions, and the approved direct
  prerequisite graph. Run red against the current duplicate graph. (AC1-AC7,
  AC12-AC14)
- Exercise the actual `Makefile` through a named temporary harness file that is
  passed as the **first** `-f` input and includes the real Makefile. The harness
  replaces only expensive recipes with event probes while retaining the real
  target graph; because `$(firstword $(MAKEFILE_LIST))` is the harness, every
  recursive child re-enters it. Assert a child-only harness sentinel as well as
  wrapper selection, environment irrelevance,
  build-before-reduced ordering under `-j`, and ordinary non-shared failure
  propagation. The harness is one temporary file that is unlinked after the
  probe, not a temporary directory, so the managed `os.rmdir` denial is
  irrelevant. Negative controls write a second temporary file from the actual
  Makefile bytes with exactly one dependency or wrapper mutation, include that
  copy from the first-file harness, and prove the assertion is observed red.
  (AC8-AC11)
- Inject a failing shared build step, missing path, stale exclusion, omitted
  exclusion, double skip, and unrelated test failure. Each negative control
  must fail for its intended reason. (AC6-AC8)
- Before any Make edit, extract the exact command-bearing recipe bytes for
  `build-check-unleased`, `sast`, and `sast-unleased`, together with the
  `SAST_DIRS`, `SAST_CONFIG`, and `SEMGREP_EXCLUDE` declarations, the complete
  `gate_verdict` macro, and every target-name call site of that macro. Hard-code
  their approved-baseline digests in the construction test and also assert the
  exact rendered delegated, skipped, and complete verdict outputs. Assert these
  baselines after implementation so delegation, pip-audit, npm SCA, Semgrep,
  scanner ordering, target attribution, and terminal-verdict bytes cannot
  change while an ordinary reachability test remains green. This test reads the
  real Makefile and does not call Git at test time. (AC13)
- Assert the make-free build-chain argv/order, Windows cleanliness, SAST
  reachability, workflow-byte invariants, verdict text, and coordination lease
  wrappers remain unchanged. (AC2, AC3, AC11-AC13, AC17)
- `stub: true` — the following compilable test shape is materialized unchanged
  before the Make edit and is red because `test-after-build-check` is absent:

```python
# STUB: AC1-AC14 — real composed ownership is exact and fail closed
def test_real_ci_graph_owns_each_shared_test_exactly_once():
    build_owned = collect_real_build_check_test_owners()
    standalone = collect_real_make_test_plan("test-unleased")
    composed = collect_real_make_test_plan("test-after-build-check-unleased")
    assert build_owned == EXPECTED_SHARED_TESTS
    assert EXPECTED_SHARED_TESTS <= standalone.files
    assert build_owned | composed.files == standalone.files
    assert not (EXPECTED_SHARED_TESTS & composed.files)
    assert composed.exclusions == EXPECTED_SHARED_TESTS


def test_composed_command_targets_are_phony():
    phony = parse_real_makefile_phony_targets()
    assert {"test-after-build-check", "test-after-build-check-unleased"} <= phony
```

**Approach:**

- Extract only the existing `test-unleased` recipe body into a lexical Make
  macro. Full and composed unleased targets call it with literal arguments.
- Add lease-wrapped `test-after-build-check` and its dependency edge; update
  `ci` direct prerequisites to the approved graph. Add both new command targets
  to the real `.PHONY` declaration and pin that property in the construction
  suite so a same-named filesystem entry cannot suppress either recipe.
- Change the parity roster's 32 `LOCAL("test")` dispositions and explanatory
  comments to the reachable `test-after-build-check` target, with self-tests
  proving the reduced route still covers every dispositioned non-shared path
  and the five shared paths remain reachable through `build-check`.
- Place the required ownership/safety/drift comment at the composition
  boundary and update the two living construction tests that pin the old
  shipped graph. Do not edit the frozen spec or plan.

**Red-green-refactor evidence:** capture focused red labels for the missing
target/exclusions, make the smallest Make change, run focused green, then
inspect the expanded commands to prove every unrelated line remains identical.

**Done when:** the construction and failure-injection suite is green, the real
Make graph is exactly the approved graph, and standalone/composed command plans
differ only by the five proven shared files.

### T3: Verification, measurement, and independent review close the change without residue

**Depends on:** T1, T2

**Touches:** `docs/specs/local-ci-shared-test-deduplication/spec.md`,
`docs/specs/local-ci-shared-test-deduplication/plan.md`,
`docs/specs/README.md`, `workspace.toml`

**Mode:** goal-based lifecycle and integration verification; no code stub.

**Tests:**

- Goal-based, no stub: run focused green tests, relevant lint/type checks,
  characterization and failure injection, then the regression suites named in
  Verification below. (AC2-AC17)
- Goal-based, no stub: attempt `SKIP_SAST=1 make ci` once, record the supported
  result or exact managed cleanup limitation, and run unaffected coverage with
  exact deselections only where the enterprise rule requires it. (AC17)
- Goal-based, no stub: repeat the same collection/launch measurement method and
  check `git status --short` plus `git diff --check`. (AC16, AC18)

**Approach:**

- Run adversarial and quality-engineer reviews in fresh contexts, route every
  report through the required finding adjudicator, and resolve every sustained
  in-scope finding within the work-loop retry rules.
- Update lifecycle metadata only after gates and reviews are clean; preserve
  measurement uncertainty explicitly.
- Confirm that the pre-EXECUTE approval transaction created accepted ADR-0096
  and only the two licensed frozen Status annotations; do not defer or repeat
  those governance writes inside this post-implementation task.

**Done when:** focused gates are green, the final composed attempt is recorded,
both independent reviews adjudicate clean, measurements are comparable, and no
generated/test residue remains.

## Verification

1. Focused red tests for T1, then minimal registry alignment and focused green.
2. Focused red Make/build-chain tests for T2, then minimal composition and
   focused green.
3. `tools/test_build_gate_chain.py`, the new shared-dedup construction suite,
   local-CI Make graph, CI parity, SAST reachability plus the approved recipe
   and scanner-declaration byte digests, Python selection, and recursive Make
   coverage.
4. Workspace-status, work-loop, and receive-brief focused suites, applying only
   the enterprise-mandated exact cleanup deselections after the one recorded
   HEAD failure.
5. Relevant ruff and mypy gates.
6. One `SKIP_SAST=1 make ci` attempt; no repeated full-suite runs for timing.
7. Repeat the baseline focused collection-plan timer with the reduced commands.
8. `git diff --check`, residue search, and `git status --short`.

Construction tests prove graph membership and failure shapes; the one composed
run is integration verification. Standalone routes are proved through command
interception and real Make selection rather than three additional full gates.

## Rollback

Revert the explicit composed targets and recipe parameterization, restore
`ci: build-check lint-ruff lint-mypy test`, restore the workspace-status manual
wrappers/registries to their prior runner-specific sets, and remove the focused
construction file plus its Make listing. Restore the 32 parity dispositions to
`LOCAL("test")`. Mark ADR-0096 Deprecated only if the decision no longer
applies and remove its Status annotations in the separately authorized
governance rollback. This returns to duplicate execution without losing a gate.
No persisted runtime state or migration needs cleanup.

## Risks

- The workspace-status union strengthens each standalone route by nine cases;
  approval explicitly accepts that compatibility alignment because whole-file
  exclusion is otherwise unsound. The case bodies themselves do not change.
- Make macro whitespace or argument placement could broaden an ignore. Exact
  expanded-command assertions and unrelated-file negative controls guard this.
- A parallel Make edge could be omitted while serial runs look correct. The
  dependency graph and `-j` event-order test guard the ownership race.
- CLI unittest/pytest order differs. Fresh per-test roots and unique module
  injection names support equivalence; the characterization test fails if a
  future top-level pytest-only case or shared mutable fixture appears.
- The managed host cannot supply full execution timing for cleanup-sensitive
  cases. The report separates comparable collection/launch timing from
  unmeasured execution and nested-process effects.

## Files expected to change

- `Makefile`
- `tools/test_workspace_status.py`
- `tools/test_local_ci_shared_test_deduplication.py` (new)
- `tools/lint-ci-parity.py`
- `tools/test-lint-ci-parity.py`
- `tools/test_catalogue_tooling_rewire.py`
- `docs/adr/0096-composed-local-ci-test-target.md` (new after approval)
- `docs/adr/README.md`
- `docs/specs/local-ci-orchestration/spec.md` (Status line only)
- `docs/specs/local-ci-orchestration/plan.md` (Status line only)
- `docs/specs/local-ci-shared-test-deduplication/spec.md`
- `docs/specs/local-ci-shared-test-deduplication/plan.md`
- `docs/specs/README.md`
- `workspace.toml`

The following must remain byte-unchanged: `tools/repo/build_gate_chain.py`,
`tools/test_build_gate_chain.py`,
`tools/repo/coordination_lease.py`, `.github/workflows/**`, SAST/SCA and
pip-audit implementations/configuration, existing ADR bodies, and the bodies of
`docs/specs/local-ci-orchestration/spec.md` and `plan.md`.

## ADR-0096 preview gate

Resolved destination: logical `docs/adr`, physical repository-confined
`docs/adr/`. Next ordinal: `0096`.

- **Identifier:** ADR-0096
- **Status:** Accepted
- **Target:**
  `<repo>/docs/adr/0096-composed-local-ci-test-target.md`
  (`docs/adr/0096-composed-local-ci-test-target.md`)
- **Index:** `docs/adr/README.md`

Content preview:

```markdown
# ADR-0096: Composed local CI uses an explicit post-build-check test target

- **Status:** Accepted
- **Date:** 2026-08-25
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** none. Per CONVENTIONS § Cite upward, an ADR does not cite specs;
  the affected frozen and current specs carry the pointer.

## Context

A shipped local-CI contract pins standalone `test` as a direct `ci`
prerequisite. Five files are also build-check self-tests, and their semantic
equivalence can be mechanically established, so that graph executes them twice.

The composed route must keep build-check ownership and self-test-before-lint
ordering, keep standalone test complete, remain safe under parallel Make, and
offer no ambient selector that can reduce a standalone gate.

## Decision

**We will make an explicit `test-after-build-check` target the test prerequisite
of composed local CI while keeping standalone `test` unchanged.**

The composed target depends on successful `build-check`, acquires the existing
test lease once, and runs the existing test recipe with only the mechanically
owned shared files excluded. Local parity dispositions point to this reachable
composed target; build-check remains the owner of the excluded files.

## Decision drivers

- Preserve standalone gate independence and build-check failure attribution.
- Make composed ownership and parallel ordering visible in the Make graph.
- Prevent environment or command-line state from selecting reduced standalone
  coverage.
- Avoid a general runner, persistent state, or duplicated long test recipe.

## Consequences

**Positive:**

- One composed invocation executes the shared semantic contract once.
- A dependency edge, rather than hidden provenance, owns parallel ordering.
- Standalone and make-free gates retain their existing entrypoints.

**Negative:**

- The shipped direct-prerequisite clause and plan receive status-only partial
  supersession pointers.
- Local CI parity dispositions name the composed target even though standalone
  `test` remains the public complete test gate.
- Construction tests must keep two route plans and five exclusions aligned.

**Revisit if:** supported Make gains a simpler explicit ordering primitive that
retains standalone `test` as the direct composed prerequisite, or the shared
set grows beyond a narrow exact-file composition.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** actual-Make construction tests prove exact graph, recursive
  delegation, parallel ordering, standalone completeness, and once-only union.
- **Owner:** repository maintainers

## Alternatives considered

**Target-specific composition profile.** Rejected because GNU Make 3.81 can
protect selector provenance but cannot also express the required parallel
ownership edge without changing standalone test or adding broader coordination.

**Skip the build-check self-tests.** Rejected because it separates each linter
from its proving self-test and changes failure ordering and attribution.

**Move the test recipe into a shared runner.** Rejected because five exact files
do not justify a general orchestration layer or moving unrelated process
boundaries into Python.
```

## Explicitly excluded optimizations

- Other Python-process reductions or pytest consolidation.
- `coordination_lease.py`, run-slot, scheduler, or concurrency changes.
- pytest-xdist, parallel tests, daemons, machine-wide coordination, or caches.
- Collect-only floors, namespace debt, bytecode caching, broad in-process gate
  conversion, and a general local-CI runner.

## Changelog

- 2026-08-25: Initial investigated plan. Selected explicit composed target;
  recorded the 84/79 workspace-status mismatch and the required 86-case shared
  contract before exclusion.
- 2026-08-25: Pre-EXECUTE round 1 sustained four findings. Added the ADR-0096
  preview and frozen-status supersession route, parity-linter source changes,
  actual-Make overlay tests, and explicit per-task verification modes.
- 2026-08-25: Pre-EXECUTE round 2 sustained two findings. Moved ADR acceptance
  and frozen annotations into an explicit approval transaction before EXECUTE,
  and changed the Make proof to a named first-file harness that recursive Make
  must re-enter.
