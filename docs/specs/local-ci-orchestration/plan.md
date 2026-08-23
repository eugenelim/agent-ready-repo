# Plan: Local CI orchestration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence develops.

## Approach

Pin the desired Make graph and interpreter behavior with construction tests
before changing the Makefile. The graph change removes `pre-pr` only from the
direct prerequisites of `ci`; `build-check` remains the sole path from `ci` to
the pre-PR aggregator. The interpreter change keeps the public `PYTHON ?=`
override surface but makes its default a lazy, self-replacing expression: on
first use it asks isolated, bytecode-disabled `python3` for `sys.executable`,
emits a shell-quoted value only when that raw value is non-empty, stores the
simple result, and otherwise raises an actionable Make error. Existing chain
and workflow tests then prove that coverage and CI
topology did not move before the real local entry points are exercised.

## Constraints

- ADR-0017 keeps SAST/SCA in the developer-facing `build-check` chain.
- ADR-0086 keeps GitHub SAST in a separate job and has `gate-main` delegate the
  scan; this change does not alter that split.
- The shipped `build-check-single-verify` contract preserves standalone
  verification-first `pre-pr` and one portable verification inside
  `build-check`.
- The shipped `local-gate-ci-parity` contract requires all GitHub gate targets
  to remain locally reachable or explicitly dispositioned.
- GNU Make 3.81 and POSIX shell behavior are the minimum observed local Make
  surface; the make-free Windows chain remains unchanged.
- No dependency, scanner, GitHub workflow, generated projection, or frozen spec
  body changes are permitted.
- Repository edits use `apply_patch`; Git index and refs remain read-only in the
  managed enterprise environment.

## Execution frame

- **Files touched:** `Makefile`, `tools/test-lint-ci-parity.py`, this spec/plan,
  `docs/specs/README.md`, and the canonical `workspace.toml` registration plus
  work-loop state. No workflow or scanner implementation is an edit target.
- **Done evidence:** focused mutation-sensitive Make tests, existing build-chain
  and workflow posture tests, SAST reachability plus unchanged-slice evidence,
  lint/type gates, and real non-SAST `build-check` and `ci` journeys.
- **Not changing:** gate membership, SAST/pip-audit/scanner behavior, GitHub job
  graphs, Windows's make-free route, dependencies, or shipped spec bodies.
- **Review shape:** narrow and below 2,000 behavior/test lines; the test change
  and the two Makefile edits form one independently reviewable unit.

Temptations declined:

- Parallelize SAST scanners — concurrent tails would reduce diagnostic clarity,
  and the user kept feasibility investigation out of implementation scope.
- Cache or parallelize pip-audit — the managed-environment prototype could not
  establish safe behavior with high confidence.
- Introduce a resolver script or dependency — Make plus the Python standard
  library already express the invariant.
- Export `PYTHON` to nested Make processes — that would broaden the public
  contract and alter the intentionally untouched SAST path.

Resolve-vs-surface disposition:

- Resolved locally: current Make/build-chain/workflow topology, standalone and
  transitive pre-PR semantics, GNU Make 3.81 behavior, Python shim/direct-launch
  timing, override precedence, and policy-compatible temporary prototypes.
- Surface to the human: only the repository-required separate approvals of the
  spec contract and implementation plan.
- Explicitly unavailable but non-blocking: an end-to-end pip-audit optimization
  prototype under the managed policy; the behavior is excluded rather than
  guessed.
- Explicit workflow exception: the base-freshness check is skipped because the
  enterprise environment prohibits the fetch/ref mutation it performs.

## Construction tests

**Integration tests:**

- Run `python3 tools/test-lint-ci-parity.py` to exercise the real Make graph,
  mutation cases, lazy selector cases where POSIX execution and Make are
  available, and live
  workflow-to-local reachability.
- Run `python3 -m pytest tools/test_build_gate_chain.py -q` and
  `python3 tools/test-build-check-workflow.py` to pin build-chain sequencing and
  GitHub workflow posture.
- Run `python3 tools/assert-sast-chain-reachable.py` to prove the unchanged local
  SAST tail is still callable from `build-check`.
- Compare the worktree `sast:` rule through the next Make target against
  `git show HEAD:Makefile`; fail unless the two slices are byte-identical. This
  is a change-scoped falsification artifact for the explicit SAST/pip-audit
  exclusion rather than a permanent snapshot that would obstruct later SAST
  work.
- Run `SKIP_SAST=1 make build-check` and `SKIP_SAST=1 make ci` as end-to-end
  developer-path checks. Their terminal banners must identify the runs as
  incomplete because SAST was deliberately skipped for verification.
- Run the repository lint and type-check gates and inspect final worktree status
  for generated residue.

**Manual verification:** Compare the terminal phase ordering of the real
non-SAST runs with the documented lifecycle: `ci` enters `build-check` once,
the pre-PR aggregator appears once inside it, and lint/type/test continue after
`build-check` without a second pre-PR phase.

## Design (LLD)

### Design decisions

- Remove an orchestration edge rather than changing either gate implementation.
  `ci -> build-check -> pre_pr_catalogue --skip-verify` becomes the sole pre-PR
  route inside `ci`; direct `make pre-pr` remains available. Traces to: AC1-AC4.
- Retain `PYTHON ?=` so environment and command-line override precedence stays
  native to Make. Its default uses deferred expansion plus `eval` to replace
  itself with a simply-expanded executable after the first lookup. Traces to:
  AC5-AC7, AC9.
- Ask `python3 -I -B` to emit
  `shlex.quote(sys.executable) if sys.executable else ""`. The raw-value guard
  must precede quoting because `shlex.quote("")` is the non-empty token `''`.
  Isolation avoids local import influence, `-B` prevents bytecode, and quoting
  makes a non-empty resolved path a safe recipe command token. Traces to:
  AC8-AC9.
- Do not export `PYTHON`: nested tools already propagate their interpreter via
  `sys.executable`, and nested `make sast` intentionally retains its current
  public behavior. Traces to: AC4, AC10-AC11.

### Interfaces & contracts

The only changed public surface is Make's orchestration contract. Target names,
arguments, exit behavior, terminal verdicts, and the operator-overridable
`PYTHON` variable remain stable. No API/event contract artifact applies.
Traces to: AC1-AC11.

### Failure, edge cases & resilience

- If `python3` cannot resolve an executable, expansion stops with a Make error
  before an empty recipe command can run.
- A target that never references `PYTHON` never triggers resolution.
- Explicit operator overrides bypass all resolver logic, including failure.
- Real-Make launcher construction cases skip cleanly unless both POSIX
  execution and `make` are available; structural graph assertions remain
  platform-independent.
- End-to-end commands use `SKIP_SAST=1` only to keep scanner/network behavior
  outside this change's verification and must retain the conspicuous incomplete
  verdict.

### Dependencies & integration

The selector uses only GNU Make functions and Python standard-library modules.
It integrates with existing POSIX Make recipes; the Windows make-free Python
entry point and every GitHub workflow remain untouched. Traces to: AC5-AC11.

## Tasks

### T1: Construction tests reject duplicate CI orchestration and repeated Python selection

**Depends on:** none

**Touches:** `tools/test-lint-ci-parity.py`

**Tests:**

**Mode:** TDD

- `stub: true` — `_test_local_ci_orchestration_stub` is materialized in
  `tools/test-lint-ci-parity.py` and invoked by its `main()` runner (AC1-AC9).
  Its pre-implementation run on 2026-08-21 compiled, executed 133 cases, and
  failed exactly the ten expected current-state assertions: direct/reachable
  `pre-pr`, direct aggregator reachability, missing isolated/error selector
  form, zero selector launches/quoting, and no empty-resolution failure.

- A real-Makefile mutation test rejects `pre-pr` as a direct `ci` prerequisite
  while proving the aggregator is still reachable through `build-check` (AC1-AC4).
- Real-Make temporary-launcher cases prove one selector launch across multiple
  recipe expansions, zero launches for a non-Python target, bypass for both
  override forms, safe space-containing output, and failure on empty resolution
  (AC5-AC9).
- The new cases fail against the current Makefile for the intended reasons.

**Approach:** Extend the existing CI-parity self-test, which already owns real
Makefile reachability mutations and conditionally executes GNU Make behavior.
Use an isolated temporary `python3` launcher and log, never the developer's
configuration or protected paths.

**Done when:** the new focused cases are present, mutation-sensitive, and the
pre-implementation run records only the expected failures.

### T2: Local CI has one pre-PR route and one default-Python resolution per Make process

**Depends on:** T1

**Touches:** `Makefile`

**Tests:**

**Mode:** Goal-based check — `no stub (goal-based)`.

- `python3 tools/test-lint-ci-parity.py` passes all graph and selector cases
  (AC1-AC9).
- Existing build-chain, workflow-posture, and SAST-reachability tests pass
  without fixture or workflow changes (AC2-AC4, AC10-AC11).
- A Python one-liner extracts the `sast:`-through-next-target slice from both
  `git show HEAD:Makefile` and the worktree Makefile and exits non-zero unless
  the bytes match (AC11).

**Approach:** Replace the eager literal default with the tested lazy
self-replacing `PYTHON ?=` expression, document its override and lazy semantics,
remove only `pre-pr` from `ci`'s direct prerequisite list, and document the
remaining transitive path.

**Done when:** focused tests are green and the Makefile diff contains no gate,
recipe, SAST, or workflow behavior change beyond the two specified edits.

### T3: Local and CI-parity gates validate the optimized developer journey

**Depends on:** T2

**Touches:** `docs/specs/local-ci-orchestration/spec.md`, `docs/specs/local-ci-orchestration/plan.md`, `docs/specs/README.md`, `workspace.toml`

**Tests:**

**Mode:** Goal-based check plus visual/manual QA — `no stub (goal-based and
manual-QA)`.

- Focused Python, Make, workflow posture, build-chain, and SAST-reachability
  tests all pass (AC1-AC11).
- `SKIP_SAST=1 make build-check` completes with its incomplete verdict (AC4,
  AC10-AC12).
- `SKIP_SAST=1 make ci` reaches the unchanged test tail after one pre-PR
  aggregator phase and successful lint/type phases, then stops on the
  registered enterprise `.pem` denial. Only full-tail completion and the final
  incomplete verdict remain deferred under
  `pre-existing-enterprise-agentbundle-full-suite` (AC1-AC4, AC12a-AC12b).
- Final lint/type checks pass and `git status --short` contains only intended
  source and governance edits (AC12).

**Approach:** Run narrow checks first, then the two long-running developer
entry points in observable sessions. Record any enterprise-only inability as
verification evidence rather than changing gate behavior. Update acceptance
criteria and lifecycle metadata only from observed results.

**Done when:** every acceptance criterion is evidenced, the spec is ready to
ship, and adversarial plus quality reviews are clean.

## Rollout

This is an immediate, repository-local Makefile change with no infrastructure,
deployment, migration, or external-system sequencing. Reversion is the inverse
two-line Makefile change; no persisted data or published interface is
irreversible.

## Risks

- GNU Make's lazy self-replacement is less familiar than a literal variable;
  comments and executable behavioral tests carry the maintenance burden.
- `make -n` still expands recipe variables and therefore performs the one
  interpreter lookup for Python-backed targets; this is normal Make expansion,
  but tests must not claim dry-run means zero selector activity.
- System load and caches make wall-clock thresholds flaky. The contract uses
  structural launch-count and graph invariants instead of a time budget.
- Removing the direct edge could hide a future divergence if `build-check`
  stops reaching the aggregator. A transitive-reachability mutation test makes
  that edge load-bearing.
- A selector test that assumes POSIX execution would fail on make-free Windows;
  those cases are explicitly capability-gated while platform-independent graph
  checks still run.

## Changelog

- 2026-08-21: Initial plan from the approved scope; SAST concurrency and
  pip-audit optimization remain excluded after investigation.
