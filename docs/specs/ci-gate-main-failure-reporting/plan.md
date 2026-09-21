# Plan: gate-main reports every independent failure in one round

- **Status:** Drafting <!-- Drafting | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Repository anchors:** `tools/AGENTS.md` (roster obligation, and that roster
  reasons are checked for presence not truth); `docs/specs/ci-gate-parallelization/spec.md`
  AC13 (the posture test is pure stdlib and runs where it is load-bearing);
  `.claude/skills/work-loop/references/delivery-contract-lifecycle.md` (a frozen
  spec is not rewritten); analogous implementation `tools/lint-ci-parity.py`
  `SUITE_DISPOSITION` and its `PR_GATED_IF` two-field entry, with its tests in
  `tools/test-lint-ci-parity.py`.

## Approach

Land the roster axis first, then the workflow and its guard in one commit,
because a workflow carrying conditions the guard does not yet admit is a red
tree. Verification of the two behavioural criteria is a dispatched CI run, not
a local harness: GitHub's step-conclusion semantics have no local equivalent.

## Constraints

- `tools/test-build-check-workflow.py` is pure stdlib. `tools/lint-ci-parity.py`
  imports `yaml` only inside functions (lines 2062, 2457), so the posture test
  can `importlib`-load it and read `STEP_DISPOSITION` without acquiring a
  third-party import at module scope.
- `tools/test_build_gate_chain.py` pins the bandit install as unconditional and
  immediately preceding the anchor, and asserts `has_if` is false for it. Bandit
  is provisioning and now carries `!cancelled()`, so that assertion must be
  retargeted in the same commit that adds that condition, or the chain
  reds — T4 owns it. The hoist orders
  the other ten installs above it, preserving the adjacency the same file pins.
  Retarget by comparison against the sanctioned value, never by deleting the
  assertion and never by a falsy conjunct: `False and <expr>` trips ruff
  `SIM223`, which is the confound the spike had to subtract.
- `_step_named` in the posture test matches by substring, so no step name may
  contain another step's name.
- `lint-ci-parity.py` runs inside `make build-check`, which is `gate-main`'s own
  anchor step. A roster or guard error therefore reds the job at the anchor,
  before any check reports.

## Construction tests

| Criterion | Suite | What it drives |
| --- | --- | --- |
| AC-0001, AC-0002, AC-0003, AC-0005, AC-0010, AC-0011, AC-0016, AC-0017 | `tools/test-build-check-workflow.py` | The workflow text against the roster-derived expression set, the declared ids, and their ordering |
| AC-0004, AC-0006, AC-0007, AC-0008, AC-0009, AC-0012 | `tools/test-lint-ci-parity.py` | The roster's completeness, vocabulary, conditional-source rule, and agreement with the measured matrix |
| AC-0013, AC-0014, AC-0015 | dispatched `build-check.yml` runs | Step conclusions on a real runner, bounded by AC-0016 |

## Durable-output map

| Durable output | Task |
| --- | --- |
| Decision rationale (ADR) | T5 |
| Maintainer procedure (`tools/AGENTS.md`, linter message) | T6 |
| Current architecture (workflow header comment) | T6 |
| Reusable learning (evidence note) | T1 |

## Design (LLD)

### Design decisions

**The marker is a derived expression, not a constant.** `!cancelled()` alone
does not contain a provisioning failure: it means "unless the workflow was
cancelled", so a check runs after an earlier step failed. Measured — breaking
one install produced nine reds where one was the cause. Conditioning each check
on the provisioning it needs is what makes containment real.

**Provisioning steps run independently of each other.** Each carries exactly
`!cancelled()`. Leaving them unconditional was the earlier design and it defeats
per-check gating: a sequential chain of unconditional installs means one failure
skips every later install, so checks needing those later installs skip too, and
a broken credbroker greys the seven Office and extraction checks that do not
need it. Marking each install makes a failure local to itself, which is what the
measured matrix is for.

**Containment is then per check.** A dependent sees a predecessor whose
conclusion is `failure`, which is not `success`, and skips — grey, not red.
A non-dependent sees all of its own dependencies succeed and runs.

**The anchor is a check, not provisioning.** The recorded matrix measures
`Run make build-check` as a dependent of `Install tools dependencies` and of
`Install bandit unconditionally`, so it carries a derived expression naming
both. Nothing downstream consumes what it produces: `dist/` and `build/` were
deleted, and separately corrupted, with all 70 downstream checks still green.

**The admitted set is derived from the roster rather than listed twice.** A
second independent list of admitted expressions is a copy that drifts from the
roster it duplicates. The cost is stated in the spec's Assumptions: a roster
edit can widen what the guard accepts, and the roster is a human-review control.

### Interfaces & contracts

`STEP_DISPOSITION` gains a second tuple position beside its existing
`LOCAL`/`CI_ONLY` value. `PROVISIONING(id=...)` declares a provisioning step and
its stable workflow `id:`; `CHECK(needs=(...), evidence=...)` declares a check,
the provisioning ids it needs, and the measurement run that establishes them.
The two-field shape follows `PR_GATED_IF`, whose module comment records why the
fields stay separate rather than joined into one string.

A `CHECK` entry derives to `!cancelled()`, followed by one
`&& steps.<id>.conclusion == 'success'` per declared dependency in roster order.
`Set up Python` is declared `PROVISIONING` with id `python` and is a dependency
of every check, so every derived expression carries that conjunct and none is
the bare marker. The earlier reading — that it needed no declaration because a
`uses:` failure stops the job — is refuted by this spec's own evidence:
`!cancelled()` does not skip on a prior failure, so an unconditioned check would
run against the runner's fallback interpreter.

Beyond that universal conjunct the graph is sparse: 19 measured edges over 15
checks, so most checks carry `python` alone.

### Failure, edge cases & resilience

A provisioning step that is skipped rather than failed has conclusion `skipped`,
which is not `success`, so dependents skip. That is the intended reading and is
what makes a mid-provisioning failure contain rather than cascade.

## Tasks

### T1: The dependency matrix is recorded and citable

**Depends on:** none

**Tests:**
- Goal-based: `docs/specs/ci-gate-main-failure-reporting/notes/partition-evidence.md`
  contains one row per breakable provisioning step, each naming the run id and
  the set of check steps that failed when only that step was broken.
- Goal-based: every run id in the note resolves to a completed run on this
  repository.

**Done when:** the note is committed and every row cites a run id.

### T2: The roster carries a phase and dependency axis that cannot be left blank

**Depends on:** T1

**Tests:** in `tools/test-lint-ci-parity.py`, which runs its cases from `main()`
rather than pytest collection —
- A step of `build-check.yml` with no phase entry exits 1 naming the step (AC-0006).
- A phase entry naming no step in the workflow exits 1 naming the entry (AC-0007).
- A phase value outside `PROVISIONING`, `CHECK` exits 1 naming the entry (AC-0008).
- A `CHECK` dependency that is not a declared `PROVISIONING` id exits 1 naming
  the entry (AC-0009).
- A `CHECK` entry whose dependency set differs from the recorded matrix row, or
  whose evidence string does not name that row's run id, exits 1 naming the
  entry (AC-0012). `Set up Python` is exempt per the spec's Assumptions.

**Approach:**
- The matrix comparison reads the committed note rather than re-deriving the
  sets, so a roster edit that invents a dependency fails against evidence.

**Done when:** `python3 tools/lint-ci-parity.py` exits 0 on the populated roster
and the five cases above are green.

### T3: The conditional-source rule admits the sanctioned expressions and nothing else

**Depends on:** T2

**Tests:** in `tools/test-lint-ci-parity.py` —
- A step reached by a `PR_GATED` entry carrying its exact derived expression
  exits 0 (the rule no longer rejects every `if:`).
- The same step carrying each of `if: false`, `if: ${{ false }}`,
  `'if': ${{ false }}`, and its derived expression with ` && false` appended
  exits 1 naming the step (AC-0004).
- A step carrying an `if:` that is well-formed but is not that step's derived
  expression exits 1 naming the step (AC-0004).

**Approach:**
- This is the shipped fail-open control being widened. It is a separate task
  from T2 because T2 adds a new axis while this changes an existing rule whose
  current behaviour — a presence test at `tools/lint-ci-parity.py:2103` feeding
  the violation at 2268-2269 — produced 59 violations on the spike tree.

**Done when:** `python3 tools/lint-ci-parity.py` exits 0 on a tree carrying the
conditions, and the six cases above are green.

### T4: The workflow carries derived conditions and the posture test demands them

**Depends on:** T3

**Tests:** in `tools/test-build-check-workflow.py` —
- A `CHECK` step with no `if:`, or one differing by any byte from its derived
  expression, exits 1 naming the step (AC-0001).
- A `PROVISIONING` step carrying an `if:` other than exactly `!cancelled()`
  exits 1 naming the step (AC-0002).
- Each of `if: false`, `if: ${{ false }}`, `'if': ${{ false }}`, and the correct
  derived expression with ` && false` appended exits 1 (AC-0003).
- The self-test catches fewer than 180 mutations, exercises fewer than 80
  assertion families, or leaves a family without a mutation — each exits 1 (AC-0005).
- A `PROVISIONING` id with no `gate-main` step carrying that `id:` exits 1
  naming the entry (AC-0010).
- A `gate-main` step whose roster phase is `PROVISIONING` appearing after any
  step whose roster phase is `CHECK` exits 1 naming both steps (AC-0011).
- A job-id set other than the five, or a job `name:` other than its written
  value, exits 1 (AC-0016, AC-0017).

**Approach:**
- One commit with the workflow change, because a workflow carrying conditions
  the posture test does not admit reds at the anchor and a posture test
  demanding conditions the workflow lacks does the same.
- Retarget `tools/test_build_gate_chain.py`'s bandit `has_if` assertion here,
  per Constraints.

**Done when:** `python3 tools/test-build-check-workflow.py`,
`python3 tools/lint-ci-parity.py` and
`python3 -m pytest tools/test_build_gate_chain.py -q` all exit 0, and
`make lint-ruff lint-mypy` is clean.

### T4a: Containment and independence hold on a real runner

**Depends on:** T4

**Tests:**
- Goal-based, one dispatched run per provisioning step in the recorded matrix:
  every `CHECK` declaring that dependency is `skipped`, and no `CHECK` that does
  not declare it is `skipped` (AC-0013); the broken step is the only `failure`
  (AC-0014).
- Goal-based, one dispatched run with a single check broken and all provisioning
  green: no other `CHECK` is `skipped` (AC-0015).

**Approach:**
- Injection branches are scratch and never merged. The branch leaves every
  delivered step condition exactly as shipped and breaks only the one
  provisioning step's command. Do not re-mark any step: the "mark every
  neighbour" setup belonged to the matrix measurement, which ran before the
  roster axis existed and before any check carried a derived condition.
  Re-marking here would overwrite those conditions and make dependents run and
  red instead of skip, so the run would exercise neither AC-0013 nor AC-0014.
- Record each run id in the verification ledger. AC-0013 ranges over the recorded
  matrix, so this is one run per provisioning step, not one run total.

**Done when:** each run is recorded with its step conclusions and matches its
criterion.

### T5: The reversal is recorded as a decision

**Depends on:** none

**Tests:**
- Goal-based: `python3 -m pytest packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py -q`
  is green for the new ADR.
- Goal-based: the ADR names the control it reverses and why a widening
  condition is not the neutering form the control forbids.

**Approach:**
- Confirm the free ordinal against `docs/adr/` at the moment it lands; `0121` is
  next as of authoring but ordinals here do not reliably hold.
- The three shipped specs stating the control are historical records and are not
  edited.

**Done when:** the ADR exists at status Accepted and `spec.md`'s
`Constrained by:` cites its confirmed ordinal.

### T6: A maintainer adding a step is told what to declare

**Depends on:** T2, T4

**Tests:**
- Goal-based: `tools/AGENTS.md`'s `lint-ci-parity.py` bullet names the phase and
  dependency axis alongside the two it already documents.
- TDD in `tools/test-build-check-workflow.py`: the `gate-main` header comment
  stating the two phases and the containment rule is present, pinned by content
  so its deletion fails.
- TDD in `tools/test-lint-ci-parity.py`: a missing phase entry's message names
  the axis and the two admissible values.

**Done when:** the three surfaces carry the rule and their assertions are green.

## Rollout

One pull request. `gate-main`, `gate-sast` and `gate-export-boundary` remain
required by name, and no job is added, removed, or renamed, so branch protection
is untouched. Reverting is a single revert: the roster axis and the workflow
conditions land together in the same history.

## Risks

- **A wrong dependency entry fails open.** A check declaring too few
  dependencies runs without them and reds spuriously — the defect this spec
  exists to remove. T2 populates from measurement rather than inspection, and
  AC-0008 forces an evidence reference so an unbacked entry is visible.
- **The matrix may not justify per-check gating.** If most checks depend on most
  provisioning, the derived expressions collapse toward one shared condition.
  That narrows the delivery rather than breaking it, and the spec's Assumptions
  record it as the spec owner's call.

## Changelog

<!-- approvals only, not how the approach evolved -->
