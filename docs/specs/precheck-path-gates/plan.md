# Plan: Path-triggered precheck

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `tools/check-core-release.py` (argparse CLI, fails closed on an unresolvable `--base`); `tools/run-bandit-gate.py` (`FLOOR`, `CONFIG`); `tools/lint-agents-md.py` with the `tools/test_lint_agents_md_*.py` suites, which sit in `FINAL_TOOL_BATCH` in `tools/test_local_ci_shared_test_deduplication.py`, the Makefile `run-test-suite` define, and the `build-check.yml` mirror; `tools/AGENTS.md`. A new suite line in the `run-test-suite` define needs one `PR_GATED` `SUITE_DISPOSITION` entry per target, like its `test_lint_agents_md_*` neighbours.

## Approach

Build the runner as a pure mapping from changed paths to checks, add the lint rule, then register both new suites and add the make target in one task, then make the documentation edits so the pinning suites verify them. The riskiest part is the root `AGENTS.md`, at its line cap and under a readability floor: the commands block gains a line by editing the existing gate line, not by growing the file.

## Constraints

- Pure standard library under `tools/` (`tools/AGENTS.md`).
- Root and scoped line caps and the readability floor are enforced by `tools/lint-agents-md.py` and `tools/test_agents_md_readability_floor.py`.
- Local CI time is expensive: only the suites named in each task's `Done when` run locally. `make test` and the whole roster are not run.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** one real `make precheck` on a throwaway branch that touches a `packs/**/.apm` file, with its wall time, in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure: `docs/VERIFICATION.md`, root `AGENTS.md`, `AGENT_RULES.md` | T4 | AC-0013, AC-0014, AC-0016, AC-0017 checks | entry present; manual run in the ledger |

## Design (LLD)

### Component / module decomposition
Traces to: AC-0001 to AC-0010. Owned by: T1.
- `tools/precheck.py` holds a function mapping a path list to ordered check descriptors, and a runner that executes them with an injectable executor. A descriptor names its trigger, its argv, and the tool whose absence makes it a named skip.
- Changed paths are the union of `git diff --name-only <base>...HEAD` and the working-tree changes. The base comes from `--base`, defaulting to `origin/main`, resolved with `git rev-parse --verify`; failure exits 2. `git` itself missing also exits 2, because there is no path list without it.
- The bandit check reuses `FLOOR`, `CONFIG`, the scan roots (`SAST_DIRS`) and the any-stderr-fails rule from `tools/run-bandit-gate.py` instead of copying them. Whether that import or a subprocess call to the script fits is `implementation-discovered`: the script scans configured directories, and the check must restrict to the changed files.
- Trigger globs are fixed by AC-0002 to AC-0006; their exact form is not.

### Behavior & rules
Traces to: AC-0015. Owned by: T2.
- The rule reads each `AGENTS.md`, finds a `local gate` mention, collects every target of each `make` invocation in the same paragraph or fenced block (`make a b` yields both), and compares each with the targets the Makefile defines (`^<name>:` lines). The red case is a fenced-block fixture whose `make` line names two targets and omits the second from the fixture Makefile; it asserts on the diagnostic `local-gate target not defined: <target>`.

## Tasks

### T1: precheck maps paths to checks and reports skips

**Depends on:** none

**Tests:**
- TDD, at the mapping function and at the runner with an injected executor that records argv: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010. Each AC is one case, with a LOW-only bandit result as the green case for AC-0006.

**Done when:** `python3 -m pytest tools/test_precheck.py -q` passes.

### T2: the AGENTS.md lint rejects an unknown local-gate target

**Depends on:** none

**Tests:**
- TDD, at `tools/lint-agents-md.py` against fixture files: the AC-0015 fixture fails, this repository passes. The suite is `tools/test_lint_agents_md_local_gate.py`, beside its `test_lint_agents_md_*.py` neighbours.

**Done when:** `python3 -m pytest tools/test_lint_agents_md_local_gate.py -q` passes and `python3 tools/lint-agents-md.py` exits 0.

### T3: the target exists, is chained into nothing, and its suites run in CI

**Depends on:** T1, T2

**Tests:**
- Goal-based: `make -n precheck` prints the runner invocation, and a grep over every Makefile prerequisite list and recipe finds `precheck` only on its own target (AC-0011).
- Goal-based: both new suites sit in the batch the existing `test_lint_agents_md_*` suites sit in, in the Makefile define, the `build-check.yml` mirror and the dedup tuple, and a `PR_GATED` `SUITE_DISPOSITION` entry for each (AC-0012).

**Done when:** `make -n precheck` exits 0, the AC-0011 grep matches only the target line, `python3 tools/lint-ci-parity.py` exits 0, and `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` passes.

### T4: guidance and verification entry carry the new rules

**Depends on:** T3

**Tests:**
- Goal-based: AC-0013, AC-0014 and AC-0016 by grep, plus the pinning suites; AC-0017 by reading the entry against § Verify entries → Fields.
- Manual QA: the throwaway-branch run, recorded in the ledger.

**Approach:**
- Widen the existing `AGENT_RULES.md` row's `when` instead of adding a row, and keep its `read` cell one plain path: the doctrine adds a row only when none routes to the file, and a roster test pins the `read` cell.
- The precheck entry sits last in `docs/VERIFICATION.md`, because two suites slice an entry at the next `## `.

**Done when:** `python3 tools/lint-agents-md.py` exits 0, and `python3 -m pytest tests/roster/test_cognitive_load_repository_contract.py tests/roster/test_verify_entry_receipts.py tools/test_agents_md_readability_floor.py -q` passes.

## Rollout

Local tooling and guidance only; reversible by revert. No sequencing.

## Risks

- The root file's readability floor (`test_agents_md_readability_floor.py`) can fail on an added sentence; T4 runs it by name.
- `AGENT_RULES.md` may have a seed twin whose parity a suite checks; T4 greps `tests/` and `tools/` for it before editing.

## Changelog

- 2026-11-05: spec approved by eugenelim.
- 2026-11-05: plan approved by eugenelim.
