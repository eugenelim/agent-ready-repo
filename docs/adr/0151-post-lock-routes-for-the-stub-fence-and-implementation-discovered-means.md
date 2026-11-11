# ADR-0151: After the whole-plan lock retires, the stub fence is a task-start revision and an implementation-discovered means is a working-plan change

- **Status:** Accepted
- **Date:** 2026-10-28
- **Areas:** work-loop, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0150 D3,D5; ADR-0144 D3,D11
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0150 (D3 and D5 left both routes to the cutover; its other decisions stay in force); ADR-0144 (D3 lets an in-envelope working-plan or task change proceed without approval, D5 is the red-before-green guard, D11 refuses a worker attempt that changes the plan); spec `execution-supervisor-cutover` (AC-0022 to AC-0025 carry these routes into the shipped skill)

## Decision summary

- **Decision:** Once the supervisor owns procedure and the whole-plan lock is gone, the controller writes a supervisor TDD task's `stub` fence as a task-start revision before the supervisor issues that task's first request, and it records the grounding of an `implementation-discovered` seam or design means, and each later correction, as an in-envelope edit to the plan's `## Design (LLD)`. Both edits are made only while no supervisor attempt is open. After a not-red fence's attempt closes, the next trusted-file change waits for a named human to confirm its exact bytes, which narrows ADR-0144 D3 and D11 for that one change.
- **Because:** ADR-0150 kept both in place only because the whole plan was hash-locked at approval; with the lock gone, the plan itself can carry them without approval, and the supervisor still observes red before green.
- **Applies to:** `work-loop` full-mode EXECUTE under the supervisor, `tdd-stubs.md`, `delivery-contract-lifecycle.md`, `new-spec`'s plan template and plan contract, and the supervisor's attempt closure and `report` for a fence that is not red.
- **Tradeoff accepted:** the approved plan no longer shows a task's fence or a design means at plan review; the fence is still proven red by the supervisor, and the design edit is still a commit the supervisor records. A fence that is not red costs one human confirmation before the run continues.
- **Revisit if:** controllers routinely hit `attempt-residue` because a plan edit was needed while an attempt was open, or a design edit changed a protected reference without a refusal.

## Context

ADR-0150 D3 has the plan author carry a supervisor task's `stub` fence in the
approved task, because the whole-plan hash lock froze the plan at approval. D5
sends an `implementation-discovered` means and its corrections to the
verification ledger for the same reason. Both decisions say the cutover that
retires the lock owns the replacement and state no rule for it.

ADR-0144 D3 removes the lock. A working-plan or task change that leaves the
reviewed envelope and terminal intent unchanged reprojects tasks without
approval and cancels only unintegrated attempts. D11 refuses the result of any
worker attempt that changes the plan, so a plan change during execution must
come from the trusted controller.

The supervisor that shipped dark already behaves this way. A controller edit to
the plan is committed as one `replan` step on the next request. A task's `Tests:`
with its stub fences and the plan's `## Design (LLD)` sit outside the reviewed
envelope. The task revision covers the stub fences, so a new fence makes a new
revision that must be proven red before it is implemented. So guidance
decides where the author is sent, except for a fence that is not red. A
`stub-not-red` refusal of a `write-stub` result leaves that attempt open, so
the fence fix it asks for is refused too. Closing the attempt instead would let
a surviving child of the stub launch write a trusted file after closure and have
it admitted as a controller replan, because nothing tells the two writers apart.
Two supervisor changes follow: the refusal closes the attempt, and the first
trusted-file change after that closure waits for a named human to confirm its
exact bytes. That confirmation is an approval of an in-envelope change, which
ADR-0144 D3 says needs none, and a named-human decision kind D11 does not list,
so this record narrows both for that one case.

One timing limit comes with it. The supervisor opens an attempt when `next`
issues a request and records the plan's bytes with it. Until that request's
result is reported, any change to the plan refuses the attempt with
`attempt-residue`, whoever made it. So a controller plan edit is in-envelope
only while no attempt is open.

## Decision

- **D1:** A supervisor TDD task's `stub` fence is a task-start revision. The controller writes it into the task's `Tests:` after the previous request's result is reported and before the `next` that issues the task's first request. The supervisor commits the edit as an in-envelope replan, materializes the fence unchanged, and proves it red before admitting production change. When the fence is not red, D3 applies. An implementer attempt never writes or changes a fence; ADR-0144 D11 refuses that result. The approved plan does not need to carry the fence.
- **D2:** The grounding of an `implementation-discovered` seam or design means, and each later correction, is a controller edit to the plan's `## Design (LLD)`, made as an in-envelope working-plan change after the open attempt's result is reported and before the next `next`. It is not recorded in the verification ledger. The ledger keeps execution observations, such as a red test's command and failing output, and what a worker attempt reports about a seam until the controller writes it into the design.
- **D3:** A `stub-not-red` refusal of a `write-stub` result closes that attempt with nothing from it committed, once the attempt checks find no difference. The first change to a trusted file after that closure is committed as a `replan` only after a named human confirms its exact bytes, and the decision is recorded with that human's authority reference. This narrows ADR-0144 D3 for that one change, which otherwise reprojects without approval, and adds a replan confirmation to the named-human decisions ADR-0144 D11 lists. Every other in-envelope change still needs no approval.
- **D4:** These routes take effect when the cutover's skill rewrite ships. Until then ADR-0150 D3 and D5 and ADR-0144 D3 and D11 govern unchanged.

## Consequences

**Positive:**
- A fence can follow the code the task is about to touch, rather than a guess made at plan review.
- The design section stays the one place a reader finds a mechanism and its corrections.

**Negative:**
- Plan review no longer sees a supervisor task's fence.
- A fence that is not red costs one human confirmation before the run continues.
- A design correction shows up as a plan commit rather than a ledger line, so a reader of the ledger alone misses it.

**Revisit if:** controllers routinely hit `attempt-residue` because a plan edit was needed while an attempt was open, or a design edit changed a protected reference without a refusal.

## Confirmation

- **Mode:** lint/CI
- **Signal:** after the cutover's skill rewrite, `tests/roster/test_tdd_stub_lifecycle_contract.py` reads every work-loop and new-spec skill source, requires the task-start fence and the working-plan route, and refuses the approved-plan fence and the ledger route; `packs/core/tests/skills/work-loop/test_supervisor_tdd.py` proves a controller-added fence is red before implementation, and that a worker-added fence or a plan edit while an attempt is open is refused, and that after a not-red closure the next trusted-file change commits as a `replan` only after a `human-decision` recorded with its authority reference.
- **Owner:** eugenelim

## Alternatives considered

- **Keep the plan-author fence and the ledger route.** Rejected: both exist only because of the lock this cutover removes.
- **Let the implementer write the fence.** Rejected: ADR-0144 D11 refuses a worker attempt that changes the plan, and the supervisor would no longer observe red independently of the worker.
- **Fold the routes into ADR-0144.** Rejected: its prose is frozen, and these routes replace ADR-0150 decisions, not ADR-0144 ones.
