# A TDD stub is proved in PLAN and materialized in EXECUTE

- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield

## Outcome

- **Input (steerable):** Every TDD-mode task reaches plan approval with one
  validated, plan-contained red-stub proof for each covered contract slice and
  no prose bullet that repeats the acceptance criterion.
- **Outcome (lagging):** A spec/plan-only run can be committed with clean gates,
  while a later code-mode run materializes the approved stub unchanged as its
  first EXECUTE test and completes the normal red-green-refactor cycle.
- **Guardrail:** PLAN still catches an untestable acceptance criterion before
  approval; no failing test file enters the repository during spec/plan
  authoring, no verification obligation loses its owner, and completion still
  requires the real suite to be green.

## Opportunity

The shipped guidance correctly rejects a prose mirror of an acceptance
criterion: executable test code is the stronger statement of the same
behaviour. It does not define a commit-safe lifecycle for that code. `new-spec`
says spec authoring does not commit stubs, while full-mode `work-loop` PLAN says
to materialize a failing test file before approval. In `spec-plan` mode there is
no EXECUTE phase to make that test green, so a compliant session can reach DONE
with broken gates or an uncommitted file.

The observed cost was a plan that mirrored 122 acceptance-criterion conjuncts in
prose. Four repair passes each left a different conjunct behind — the defect was
the mirror, not the passes.

The replacement rule therefore stands, but the two representations need
different homes at different times. PLAN owns a durable, validated stub proof;
EXECUTE owns the real test file.

## Lifecycle order

1. **`new-spec` authors the contract.** The acceptance criterion remains the
   checklist. A task's `Tests:` content names only mechanism the criterion cannot
   supply, such as the suite, seam, fixture, join key, or moved assertion. It
   does not create a repository test file or repeat the criterion in prose.
2. **PLAN proves stubbability without breaking the tree.** For a TDD task, the
   plan carries the exact stub code that replaces the behaviour-restating test
   bullet, plus the AC mapping and the result of compiling or collecting and
   running that code from disposable scratch. A `spec-plan` run writes no
   implementation or test artifact outside the plan.
3. **Approval seals a commit-safe plan.** Pre-EXECUTE review and human approval
   see the stub and its validation result. `plan-locked` can end `spec-plan` mode
   with clean gates and a clean working tree.
4. **Code-mode EXECUTE materializes the approved stub.** After the state machine
   enters `CODE-IMPLEMENTATION`, the agent copies the plan-contained stub
   unchanged into the repository's real test location, confirms that it fails
   for the intended missing behaviour, then writes production code and completes
   deferred assertions and edge cases until the test is green.
5. **Completion admits no red residue.** The real test remains as the regression
   test, the full gate suite passes, and no plan-time scratch artifact is
   committed.

For goal-based or manual-QA work, record `no stub (mode)` with its reason. For a
TDD obligation whose callable seam is not knowable until implementation, record
`no stub (implementation-discovered)` with the discovery predicate and proof
obligation. Neither branch substitutes behaviour prose for a missing stub.

## Assumptions

- The semantic replacement already shipped in core 2.15.3: `new-spec` says a
  plan carries mechanism rather than a second copy of the criteria, and
  `work-loop` says a stub replaces its prose entry. This intent does not reopen
  that decision; it corrects the missing lifecycle and aligns the owning
  convention.
- This is cross-surface: `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff* owns
  the lifecycle, `work-loop`'s `references/tdd-stubs.md` owns the procedure, and
  `new-spec` keeps only the spec-authoring boundary and its pointer to the owner.
- A top-level convention change may need the repository decision process before
  it can land; scope that before implementation rather than during.
- A plan-contained code block is executable evidence rather than a second prose
  contract. Disposable validation proves it compiles and earns a red without
  making the repository's normal test suite fail.
- `approve-plan` currently fingerprints `spec.md` and `plan.md`, not test files;
  materializing the real stub after `plan-locked` keeps the approved baseline and
  the implementation write boundary aligned.
- Verification needs both lifecycle paths: a TDD-bearing `spec-plan` walk reaches
  DONE with no non-document writes, and a code-mode walk proves the materialized
  test is byte-identical to the approved stub before red-green-refactor begins.
- **Knowledge surface:** repository specifications, shipped skill sources, state
  machine code, tests, changelog, and local Git history.

## Validation hook

- **Assumption:** A plan-contained stub can prove stubbability before approval
  and be materialized unchanged after `plan-locked` without requiring prose that
  restates the criterion.
- **Kill condition:** Kill this ordering if a representative TDD task cannot
  complete `spec-plan` with clean gates and no non-document writes, or if the
  later code-mode test cannot be shown byte-identical to the approved stub before
  implementation changes it.
- **Activity:** Run one representative TDD task through a full `spec-plan` walk,
  commit the approved documents, then resume it in code mode, materialize the
  stub, compare its bytes with the approved plan block, observe the intended red,
  and complete the test to green.

## Source

- Mode: repo-origin
- Locator: docs/specs/spec-authoring-discipline/spec.md
- Revision: local-2026-08-30
