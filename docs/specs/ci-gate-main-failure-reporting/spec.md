# Spec: gate-main reports every independent failure in one round

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0122
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer whose pull request breaks several independent `gate-main` checks
sees every one of them in one CI round, and the first red is always the root
cause. A broken install reports itself alone: only the checks measured to need
it are skipped, so one missing dependency neither reddens unrelated checks nor
greys the whole job.

## What Changes

- All 11 provisioning steps move to the front of `gate-main` — `.github/workflows/build-check.yml`
- Each provisioning step gains a stable `id:` and runs independently of the others — `.github/workflows/build-check.yml`
- Each check step gains an `if:` naming the provisioning it needs — `.github/workflows/build-check.yml`
- `Run make build-check` becomes a check with declared dependencies, not an unconditional step — `.github/workflows/build-check.yml`
- `STEP_DISPOSITION` gains a phase-and-dependency axis beside its existing local/CI-only axis — `tools/lint-ci-parity.py`
- The `PR_GATED` conditional-source rule admits the sanctioned expressions instead of rejecting every `if:` — `tools/lint-ci-parity.py`
- The admitted `if:` set becomes roster-derived instead of "no `if:` at all" — `tools/test-build-check-workflow.py`
- The rule a reader must follow when adding a step moves to the two living surfaces that enforce it — the workflow header comment and the linter's failure message
- The reversal of the no-step-`if` control is recorded — `docs/adr/0122-*`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — this reverses a control three shipped specs installed | `docs/adr/0122-*.md` | spec owner | ADR Accepted, naming what it reverses and why the widening marker is not the neutering form | ADR exists, status Accepted, cited by this spec's `Constrained by:` |
| Maintainer procedure | Applicable — adding a step now obliges a phase declaration | `tools/AGENTS.md` roster bullet; the linter's failure message | spec owner | The existing `lint-ci-parity.py` bullet names the new axis; a failing run prints what to declare | `tools/AGENTS.md` names the third axis; the failure message is asserted by a test |
| Current architecture | Applicable — the job's phase structure is new and non-obvious | Header comment in the `gate-main` job | spec owner | Comment states the two phases and the containment rule | Comment present and pinned by the posture test |
| Reusable learning | Applicable — the spike produced findings a later author needs | `docs/specs/ci-gate-main-failure-reporting/notes/partition-evidence.md` | spec owner | The recorded runs, reds, and conclusions | Note committed with the run ids it cites |
| User-facing promise | Not applicable — no adopter-visible behavior changes | — | — | — | — |
| Interface compatibility | Not applicable — no published interface moves | — | — | — | — |
| Release history | Not applicable — CI-internal; no released artifact changes | — | — | — | — |

Three shipped specs state the control this reverses — `ci-gate-parallelization`,
`pr-gate-suite-disposition`, and `site-ci-contract-closure`. They are historical
records and are not edited, not even a status pointer. The frozen-document rule
names the mitigation this delivery uses instead: the operative instruction lives
in a living file at the point of use, which is why the workflow header comment
and the linter's failure message are durable outputs above.

## Agent Rules

### Always do

- Admit a step-level `if:` by exact string equality against the roster-derived
  expression, never by substring, prefix, or truthiness.
- Keep `tools/test-build-check-workflow.py` pure-stdlib, per `ci-gate-parallelization` AC13.
- Give every new or moved step a `STEP_DISPOSITION` entry on both axes.
- Populate a dependency set from a recorded measurement run, never by reading
  the step's command.

### Ask first

- Any change to which jobs `build-check.yml` declares, or to their names.
- Any dependency declaration not backed by a measurement run.
- Extending the phase vocabulary beyond the closed set this spec fixes.

### Never do

- **No new top-level directory and no new dependency**, runtime or CI.
- No `continue-on-error`, anywhere in `build-check.yml`.
- No `if:` on a `gate-main` step other than the exact roster-derived expression
  for that step.
- No splitting `gate-main` into further jobs: branch protection requires it by name.
- No weakening a guard to make a step pass; the guard's mutation coverage may not fall.

## Testing Strategy

- **Workflow text agrees with the roster (AC-0001, AC-0002, AC-0010, AC-0011,
  AC-0016, AC-0017)** — goal-based check. `tools/test-build-check-workflow.py`
  reads the workflow text and the roster and compares conditions, declared ids,
  their ordering, and the job declarations. One command answers it, and no
  behaviour is being designed, so a test that only restates the comparison would
  add nothing.
- **A falsy or unknown condition is rejected, and coverage does not fall
  (AC-0003, AC-0004, AC-0005)** — TDD. This is the shipped fail-open control the
  ADR reverses part of. Its replacement is written against seeded mutations
  before the admitting code exists, in both guards, because a widening written
  first and tested second is how the control silently stops working.
- **The roster's own rules hold (AC-0006, AC-0007, AC-0008, AC-0009, AC-0012)** —
  TDD, in `tools/test-lint-ci-parity.py`, which runs its cases from `main()`.
  Each rule is a compressible invariant over the roster and the committed
  matrix, which is what TDD is for.
- **Containment and independence on a real runner (AC-0013, AC-0014, AC-0015)** —
  goal-based check on dispatched runs, read from each run's step conclusions.
  No local harness reproduces GitHub's step-conclusion semantics, so this is the
  one group whose oracle is CI itself. AC-0013 ranges over the recorded matrix,
  so it is one run per provisioning step rather than one run total.

## Acceptance Criteria

Throughout, **derived expression** means `!cancelled()` followed by one
`&& steps.<id>.conclusion == 'success'` per dependency the step's `CHECK` entry
declares, in roster order. **Recorded matrix** means the table and member lists
in [`notes/partition-evidence.md`](notes/partition-evidence.md).

- [x] **AC-0001.** Every check step's condition is its derived expression.
  `tools/test-build-check-workflow.py` exits 1, naming the step, when a
  `gate-main` step whose roster phase is `CHECK` carries no `if:`, or carries
  one differing by any byte from its derived expression.
- [x] **AC-0002.** Every provisioning step runs independently.
  `tools/test-build-check-workflow.py` exits 1, naming the step, when a
  `gate-main` step whose roster phase is `PROVISIONING` carries an `if:` other
  than exactly `!cancelled()`.
- [x] **AC-0003.** A falsy or unknown condition is rejected by the posture test.
  `tools/test-build-check-workflow.py` exits 1 for each of: `if: false`,
  `if: ${{ false }}`, `'if': ${{ false }}`, and the step's correct derived
  expression with ` && false` appended.
- [x] **AC-0004.** A falsy or unknown condition is rejected by the parity linter.
  `tools/lint-ci-parity.py` exits 1, naming the step, when a step reached by a
  `PR_GATED` entry carries an `if:` that is not exactly that step's derived
  expression, including each of the four forms AC-0003 enumerates.
- [x] **AC-0005.** The posture test's mutation coverage does not fall below its
  recorded baseline. The baseline is the spike run recorded in
  `notes/partition-evidence.md`: 180 mutations caught across 80 assertion
  families. `tools/test-build-check-workflow.py` exits 1 when its self-test
  catches fewer than 180 mutations, when fewer than 80 assertion families are
  exercised, or when any family has no mutation.
- [x] **AC-0006.** Every workflow step has a roster entry.
  `tools/lint-ci-parity.py` exits 1, naming the step, when a `run:` or `uses:`
  step of `build-check.yml` has no phase entry.
- [x] **AC-0007.** No roster entry is stale.
  `tools/lint-ci-parity.py` exits 1, naming the entry, when a phase entry names
  no step in `build-check.yml`.
- [x] **AC-0008.** The phase vocabulary is closed.
  `tools/lint-ci-parity.py` exits 1, naming the entry, when a phase entry's
  value is outside the set `PROVISIONING`, `CHECK`.
- [x] **AC-0009.** A declared dependency resolves to a provisioning step.
  `tools/lint-ci-parity.py` exits 1, naming the entry, when a `CHECK` entry
  declares a dependency that is not the id of a step declared `PROVISIONING` in
  the same roster.
- [x] **AC-0010.** Every declared provisioning id sits on the step that declares it.
  `tools/test-build-check-workflow.py` exits 1, naming the entry, when the
  `gate-main` step whose name matches a roster entry declared `PROVISIONING`
  with id `X` does not itself carry `id: X`. Binding the id to the job rather
  than to its own step would let two provisioning steps exchange ids while both
  ids remain present, and every derived condition would then read the wrong
  install's conclusion.
- [x] **AC-0011.** Every provisioning step precedes every check step.
  `tools/test-build-check-workflow.py` exits 1, naming both steps, when a
  `gate-main` step whose roster phase is `PROVISIONING` appears after any step
  whose roster phase is `CHECK`. Full phase ordering rather than
  dependency-wise ordering, because a provisioning step with no dependents —
  `pip install httpx …` has none in the recorded matrix — satisfies the weaker
  rule while sitting behind the checks.
- [x] **AC-0012.** Every declared dependency set equals what the recorded
  matrix measured. `tools/lint-ci-parity.py` exits 1, naming the entry, when a
  `CHECK` entry's dependency set, with `python` removed, differs from the set of
  provisioning steps whose recorded-matrix member list names that check; and
  exits 1, naming the entry, when its evidence string does not name the run id
  of every such matrix row. `python` is removed before the comparison because
  it is declared rather than measured, for the reason Assumptions records; a
  check with two dependencies appears in two rows and so names two run ids.
- [x] **AC-0013.** A provisioning failure skips exactly its declared dependents.
  For each provisioning step listed in the recorded matrix, on a dispatched run
  of `build-check.yml` in which exactly that step fails and every other
  provisioning step succeeds: every `CHECK` step declaring a dependency on it
  has conclusion `skipped`, and no `CHECK` step that does not declare a
  dependency on it has conclusion `skipped`. The recorded matrix is the closed
  set this criterion ranges over; `Set up Python` is outside it per Assumptions.
- [x] **AC-0014.** A provisioning failure reddens nothing else.
  On each run AC-0013 ranges over, no step has conclusion `failure` except the
  failed provisioning step.
- [x] **AC-0015.** A check failure leaves every other check reporting.
  On a dispatched run in which exactly one `CHECK` step fails and every
  provisioning step succeeds, every other `CHECK` step has conclusion `success`
  or `failure`, and none has conclusion `skipped`. One run discharges this: the
  behaviour of the other checks under a sibling's failure is fixed by AC-0001,
  which pins every condition to reference only provisioning ids, so no check's
  condition can read another check's conclusion.
- [x] **AC-0016.** The five branch-protection jobs are present.
  `tools/test-build-check-workflow.py` exits 1, naming the missing id, when
  `build-check.yml` does not declare all of `gate-main`, `gate-sast`,
  `gate-export-boundary`, `gate-credbroker`, `build-check`. A job outside that
  set is permitted: these criteria exist to stop a required job being split,
  removed or renamed out from under branch protection, and an additional
  non-required job does not threaten that.
- [x] **AC-0017.** Each required job's name is the written value.
  `tools/test-build-check-workflow.py` exits 1, naming the job, when one of the
  five jobs AC-0016 names carries a `name:` other than the value written here:
  `gate-main` → `gate-main`, `gate-sast` → `gate-sast`,
  `gate-export-boundary` → `gate-export-boundary`,
  `gate-credbroker` → `gate-credbroker`, `build-check` → `make build-check`.
  A job outside that set carries no pinned name.

## Follow-ons

- spec owner: `work-intake` referral pending — the `pip install httpx …` step
  has zero measured dependents, so it is either transitive through credbroker's
  install or inert. Out of scope here; see the recorded matrix.

## Assumptions

- **Process: the ADR ordinal — settled, and it did slip.** `0121` was free at
  authoring and was taken by another change before this one merged, so the
  record is ADR-0122. Recorded here because the assumption's whole point was
  that a reserved ordinal in this repository does not hold, and it did not.
- **Design: the guard reads a human-review control.** Deriving the admitted
  `if:` set from `STEP_DISPOSITION` means a roster edit can widen what the
  posture test accepts, and `tools/AGENTS.md` records that roster reasons are
  checked for presence rather than truth. This is accepted rather than solved:
  the roster edit is visible in review, and the alternative — a second
  independent list of admitted expressions — is a copy that drifts from the
  roster it duplicates. AC-0012 narrows it by pinning dependency sets to measured
  rows, but the phase assignment itself remains human-declared.
- **Technical: `Set up Python` is declared a universal dependency without a
  measurement run.** Every other provisioning step's dependents were measured
  by breaking it. `Set up Python` is a `uses:` step, so the same instrument does
  not apply, and it is declared a dependency of every check instead. Over-
  declaring is the safe direction — if interpreter setup failed, no check's
  result is meaningful — but it is a declaration, not a measurement, and AC-0012
  exempts it for that reason.
