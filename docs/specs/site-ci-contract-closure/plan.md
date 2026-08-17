# Plan: Site CI contract closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

The seven modules already run in `gate-main`, a required context, so AC1 is
satisfied before this spec and is recorded with its proof rather than
reimplemented. What lands here: a standing construction test pinning that fact by
seeded deletion, focused contrast-checker tests plus the input hardening they
require, and ONE new `gate-main` step invoking the contrast checker and its test.
The two existing seven-module steps are left untouched — adding a third step
naming them would duplicate execution and create the second workflow-side source
of truth this plan exists to prevent. Parity is addressability, not set-equality:
every path the new step names must be reachable from `make ci`, which
`tools/lint-ci-parity.py` enforces.

## Constraints

- Follow RFC-0082 test ownership.
- Use existing Python and standard-library tooling.
- Keep the build-check workflow required and fail closed.

## Construction tests

**Integration tests:** run the workflow-shape test, all seven registered
modules, and the contrast checker tests as one focused local gate.

**Manual verification:** inspect the required-job and path-filter diff to ensure
the step is neither advisory nor conditionally skipped for relevant paths.

## Design (LLD)

### Design decisions

One explicit workflow step owns the exact module list. A construction test
parses that step and its path filters; it does not infer coverage from comments
or Make targets. Traces to: AC1, AC2, AC5, AC6.

### Failure, edge cases & resilience

The contract rejects missing modules, renamed modules, invalid color strings,
ratios below the threshold, and commands hidden behind non-required conditions.
Traces to: AC2-AC5.

### Dependencies & integration

The workflow reuses the repository's installed pytest and Python environment.
The contrast checker remains a direct Python command. Traces to: AC3-AC7.

## Tasks

### T1: Required-workflow construction test proves exact inclusion

**Depends on:** none

**Touches:** tools/test-build-check-workflow.py

**Tests:**
- TDD (`stub: true`): seed each of the seven module names absent in turn from an
  in-memory copy of `build-check.yml` and require failure (AC2).
- TDD (`stub: true`): seed each neutering form on the owning step and require
  failure (AC2). `continue-on-error` is already covered file-wide by
  `no-continue-on-error`; the step-level `if:` and `working-directory:` forms need
  new assertions, because the existing ones are roster-scoped to other steps and a
  step-level `if:` was a live bypass of this very gate.
- TDD (`stub: true`): seed the step into a job other than `gate-main` and require
  failure (AC2).
- Goal-based: assert no `paths:` key exists under `on.pull_request` or `on.push`
  (AC5).

**Approach:**
- Extend `tools/test-build-check-workflow.py`, the canonical owner of
  `build-check.yml` posture assertions, which the AGGREGATOR invokes. Deliberately
  not `tools/test_build_gate_chain.py`: that runs inside `gate-main`, the far side
  of the edge being protected — the same argument the aggregator's own guard makes.
- Enumerate the seven-module roster IN the test. Deriving it from the `Makefile`
  was considered and rejected: a roster read out of one of the things being
  checked is circular — deleting a module from both the Makefile and the workflow
  would then pass. Make/CI divergence is a separate concern already owned by
  `tools/lint-ci-parity.py`'s coverage layer, so nothing is lost by keeping the
  pin independent.
- Assert semantic command membership and `gate-main` placement by job id.

**Done when:** every seeded omission and neutering is distinguished. Note the
presence assertions are GREEN on current `main` — AC1 is already satisfied — so
mutation, not red-first, is the proof discipline here; only the contrast-step
assertion in T3 is genuinely red-first.

### T2: Contrast checker has a deterministic unit contract

**Depends on:** none

**Touches:** tools/check-docs-contrast.py, tools/test_check_docs_contrast.py, Makefile

**Tests:**
- TDD (`stub: true`): known passing and failing ratios, plus threshold
  inclusivity — no gray-on-gray 6-hex pair and no shipped-palette pair lands exactly
  on 4.5, so assert the boundary through the seam `main()` calls and bracket it with
  the tightest real pairs either side (AC3).
- TDD (`stub: true`): each named invalid-input case refuses with a diagnostic and
  a non-zero exit rather than an uncaught traceback — malformed hex, legal
  three-digit shorthand, and an unresolvable `var()` chain (AC3).
- TDD (`stub: true`): a seeded below-threshold registered pair returns non-zero
  (AC3-AC4).

**Approach:**
- Seed failures by running the script as a subprocess with `cwd` set to a temp
  tree containing a crafted `docs-site/src/styles/starlight.css`. `CSS_PATH` is a
  module-level relative path, so this needs no new flag. The shipped
  `docs-site/src/styles/starlight.css` is NEVER mutated, and no `--css` argument
  is added — that would be a public interface no acceptance criterion authorises.
- Harden `luminance()`/`resolve()` to refuse the three named cases; today all
  three raise an uncaught `ValueError`/`KeyError` past `main()`'s
  `startswith("#")` guard.
- Register the new test module in the `Makefile` test target, or it runs nowhere
  and joins the orphans the register tracks under `tools-test-runner-boundary`.
- Keep fixtures local and dependency-free.

**Done when:** the checker behavior is proved independently of CI wiring, and the
new module is reachable from `make ci`.

### T3: Required CI runs the seven modules and contrast gate

**Depends on:** T1, T2

**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- Goal-based: run the T1 construction test (AC2, AC5).
- Goal-based: execute the new step's command locally (AC4).
- Goal-based: `tools/lint-ci-parity.py` passes, proving the new step's paths are
  reachable from `make ci` (AC6).
- Goal-based: `git diff` shows no change to any dependency manifest or lockfile,
  and `tools/test_check_docs_contrast.py` conforms to RFC-0082's Tools row — a
  test of a `tools/` script, co-located in `tools/`, shipping through no surface
  (AC7).

**Approach:**
- Add exactly ONE new `gate-main` step invoking `tools/check-docs-contrast.py` and
  `tools/test_check_docs_contrast.py`. Do NOT add a step naming the seven modules:
  they already run in two steps, and a third would duplicate execution and split
  the source of truth.
- Existing `gate-main` step names are FROZEN — `tools/lint-ci-parity.py` keys its
  dispositions on the literal strings "pytest guides + catalogue navigation" and
  "pytest site build + link rewriting", so renaming either breaks the roster in
  both directions. The new step takes a distinct name and gets its own
  `STEP_DISPOSITION` row in the same commit, or the parity gate fails closed.
- Add NO `paths:` filter (see AC5 — it would make every PR unmergeable).
- Do not touch `build-check.yml` lines 266-270: that stranded credential-setup
  comment pre-dates this change and this change does not orphan it, so it falls
  outside the bundled-fixes carve-out. Record it as deferred instead.

**Done when:** the new step runs locally, `lint-ci-parity` is green, and the
construction contract recognises the gate.

## Rollout

The required job changes immediately for relevant pull requests. Reverting the
workflow step and its construction test restores the previous behavior; no data
or deployment migration exists.

## Risks

- A broad Make target may look equivalent while required CI still omits tests.
- Path filters can prevent an otherwise-correct step from running.
- A checker test that asserts implementation constants instead of emitted exit
  behavior would provide false confidence.

## Changelog

- 2026-08-17: initial plan derived from the approved tech-site completion brief.
- 2026-08-17: corrected again during implementation review, after code. T1's
  Approach had directed deriving the roster from the `Makefile`; the implementation
  hard-codes it on an anti-circularity argument, and this plan now carries that
  reasoning rather than leaving it only in the test file. Two `make-covers-*`
  assertions were written and then REMOVED: they read the real `Makefile`, so no
  workflow mutation could flip them, and they would have shipped as decorative
  assertions the posture file's own "evaluated but unmutated" rule exists to
  reject. Diff review also found a step-level `if:` bypass — `if: ${{ false }}` on
  either pytest step or the contrast step skipped the gate with the posture test
  green — and a tautological threshold assertion (`FLOOR <= FLOOR`) that stayed
  green when the production comparison was flipped; both are fixed, the latter by
  extracting a `passes()` seam.
- 2026-08-17: corrected at spec-stage review, before any code. AC1 was already
  satisfied by the shipped `build-check-coverage-gaps` spec, and the intake
  assumption that the seven modules were absent from required CI was false —
  they run in `gate-main`, which branch protection requires by name. AC5 was
  restated because adding `paths:` filters to a workflow whose jobs are required
  contexts would leave every non-matching PR permanently unmergeable. AC6 was
  restated because `ci-gate-parallelization` AC16 settled that parity is
  one-to-many after the job split. AC2 gained a job id, a definition of
  neutered, and mutation-proof discipline; AC3 gained named invalid-input
  cases. Scope is unchanged in substance: no criterion was dropped, and the
  two restatements preserve each criterion's intent.
