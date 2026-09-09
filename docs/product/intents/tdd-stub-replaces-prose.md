# A TDD stub is proved in PLAN and materialized in EXECUTE

- **Status:** Accepted
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

Core 2.15.3 correctly rejected a prose mirror of an acceptance criterion:
executable test code is the stronger statement of the same behaviour. That
release did not yet define a commit-safe lifecycle for the code. In
`spec-plan` mode there is no EXECUTE phase to make a repository test green, so
materializing a failing test before approval could leave broken gates or an
uncommitted file.

Core 2.16.3 resolved that lifecycle gap. PLAN owns a durable, validated stub
proof; EXECUTE owns the real test file. This intent preserves that delivered
contract without reopening either decision.

## Boundary

- **In scope:** the TDD stub representation and PLAN → approval → EXECUTE order
  owned by `docs/CONVENTIONS.md`, `new-spec`, `work-loop`, and their regression
  tests.
- **Out of scope:** changing the plan-approval state machine, changing normal
  red-green-refactor behavior, reopening the two accepted no-stub
  dispositions, or implementing a product-specific test.

## Owner

- Core pack guidance maintainers. No individual owner is recorded.

## Unresolved questions

- None for this migration. Human acceptance of this intent remains the
  lifecycle gate before the redundant legacy closure record can be removed.

## Projection

- No new implementation specification. The contract shipped in core 2.16.3;
  after acceptance, this intent remains its durable migration record and the
  duplicate `[backlog].closed` entry can be removed.

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

- The semantic replacement shipped in core 2.15.3: `new-spec` says a plan
  carries mechanism rather than a second copy of the criteria, and `work-loop`
  says a stub replaces its prose entry. The complete PLAN → EXECUTE lifecycle
  shipped separately in core 2.16.3. This intent does not reopen either
  decision.
- This is cross-surface: `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff* owns
  the lifecycle, `work-loop`'s `references/tdd-stubs.md` owns the procedure, and
  `new-spec` keeps only the spec-authoring boundary and its pointer to the owner.
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

## Validation evidence

- **Assumption:** A plan-contained stub can prove stubbability before approval
  and be materialized unchanged after `plan-locked` without requiring prose that
  restates the criterion.
- **Kill condition:** Kill this ordering if a representative TDD task cannot
  complete `spec-plan` with clean gates and no non-document writes, or if the
  later code-mode test cannot be shown byte-identical to the approved stub before
  implementation changes it.
- **Evidence:** `tests/roster/test_tdd_stub_lifecycle_contract.py` holds the
  cross-surface contract for planning-only writes, disposable validation,
  approval ordering, byte-identical materialization, intended-red proof, and
  completion with no failing-test residue.

## Source

- Mode: repo-origin
- Locator: docs/specs/spec-authoring-discipline/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
