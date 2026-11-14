# Spec: supervisor trust gaps

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0154, ADR-0157
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the new verbs, records and refusals are supervisor CLI JSON documented in the work-loop supervisor reference; no `contracts/` schema changes
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface, persistent-representation, multi-feature
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

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

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->

## Outcome

The repository owner running a supervised work-loop gets task and gate success that the supervisor itself observed, ledger notes that land without a human adoption wait, a review budget that stops a run at a named cap, and a run that cannot start in a checkout another run holds. A worker or reviewer can no longer claim success without executing the approved gates, a ledger note no longer needs an owner round-trip, review rounds no longer run past their cap, and one checkout no longer serves two runs.

## What Changes

- Task and final-gate success needs a supervisor-recorded gate execution — `scripts/_supervisor_tdd.py`, `scripts/_supervisor_readiness.py`, new `scripts/_supervisor_execution.py`, verb `execute-gates` in `scripts/work-supervisor.py`.
- Gate commands come from a declaration in the approved spec's Agent Rules section — `scripts/_supervisor_projector.py`.
- An owner-confirmed, append-only `correct-task` reopens a falsely admitted task — `scripts/_supervisor_loop.py`.
- A `commit-record` verb commits exact bytes for declared ledger paths without adoption — `scripts/work-supervisor.py`, `scripts/_supervisor_loop.py`, `scripts/_supervisor_recovery.py`.
- A cumulative review budget covers spec-phase and implementation review across replan and adoption — `scripts/review-artifact.py`, `scripts/_supervisor_readiness.py`, `references/pre-execute-review.md`.
- `start` refuses a primary checkout and a checkout reserved by another run — `scripts/_supervisor_admission.py`.
- Reference, skill text and evals describe the new verbs and refusals — `references/supervisor.md`, `references/state-schema.md`, `SKILL.md`, `evals/evals.json`.
- Core releases as the next patch above `main`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | New verbs, refusals and records change how the supervisor is driven | `packs/core/.apm/skills/work-loop/references/supervisor.md`, `references/state-schema.md`, `SKILL.md` | eugenelim | Doc-pin tests and evals green | Each new verb, refusal code and record is described once, in the reference |
| Release history | Core ships a behavior change | `docs/product/changelog.d/<id>.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | eugenelim | `check-core-release` and the roster upgrade-notes suite pass | Fragment names core at the released version |
| Decision rationale | The execution-proof and record-commit designs choose among rejected alternatives | none — ADR-0144, ADR-0154 and ADR-0157 already own the supervisor's authority model, and the rejected alternatives are in the plan's Design | eugenelim | n/a | n/a |
| User-facing promise, architecture | No adopter-facing surface changes beyond the supervisor reference | none — the supervisor reference is the only documentation of these verbs | eugenelim | n/a | n/a |

## Agent Rules

The guard for an implementing agent. A flag name, record field or write order is mechanism and lives in the plan's Design.

### Always do

- Land each slice as its own PR, in order: execution proof, record commits, review budget, checkout ownership.
- Keep existing behavior for a run started before the release; its pinned scripts decide.
- Fail closed: an unreadable record, an unknown schema version or a missing proof refuses and moves no ref.
- Bump the core patch version and add the changelog fragment with each slice that changes pinned scripts.

### Ask first

- Any change to who may approve a decision (`owner`, `risk-owner`, `plan-reviewer`) or to what an authority reference proves.
- Letting `commit-record` cover knowledge-capture paths or any path outside a declared ledger path.
- Running gate commands under a sandbox, container or other privilege boundary.

### Never do

- Add a top-level dependency, a new top-level directory or a new module boundary outside `packs/core/.apm/skills/work-loop/`.
- Let a worker or reviewer result supply gate commands, execution proof, a correction or a record path.
- Delete, move or rewrite a ref the run did not create, except the supervisor's own compare-and-swap advance of `HEAD` and the product ref that ADR-0154 requires, or edit `delivery/` or `.supervisor/` by hand.
- Promote a legacy boolean receipt to execution proof.
- Change `packages/agentbundle/` engine code.

## Testing Strategy

- Gate execution, proof matching, correction and the review ledger: TDD, because each has a compressible invariant over records and refusals; unit tests at the module functions plus real-subprocess CLI cases for `execute-gates`, `report`, `correct-task` and `commit-record`.
- Record commits and checkout reservation: TDD with real Git repositories, because correctness is the resulting refs, trees and refusals; crash behavior by injecting a kill between ref move and record write.
- Legacy-run behavior: behavior pin on the current boolean `report` path under a pinned run, because it must stay byte-identical.
- Reference text, skill text and evals: goal-based, by the existing doc-pin tests and `lint-spec-status`, because they only need to stay consistent with the code.
- Release: goal-based, `make precheck` with `check-core-release`, because it is a gate, not a behavior.

## Acceptance Criteria

**Execution proof**

- [ ] **AC-0001.** `execute-gates <spec-dir> --request <id>` runs each gate command declared in the approved spec as an argument vector with no shell, in its declared working directory, against a frozen copy of the candidate tree.
- [ ] **AC-0002.** Each completed execution appends one `gate-execution.v1` record holding the request id, issuance id, task revision, candidate product-tree digest, gate-declaration digest, and per command the argument vector, working directory, exit code and timeout.
- [ ] **AC-0003.** `report` of an `implement-task` or `run-gates` result with `gate.passed: true` refuses with `gate-execution-missing` and moves no ref unless an unconsumed record exists whose commands all exited with their expected code.
- [ ] **AC-0004.** `report` refuses with `gate-execution-mismatch` and moves no ref when the record's run, request, issuance, task revision, candidate digest or gate-declaration digest differs from the current request.
- [ ] **AC-0005.** A command that exits nonzero, times out, or is interrupted before its record completes yields no passing record, and the reported task takes the existing `gate-fail` path.
- [ ] **AC-0006.** A record admits at most one result: a second `report` naming it refuses, and an identical retry of the first `report` creates no second commit.
- [ ] **AC-0007.** The product-tree digest of the commit admitted for a task, taken with the spec directory excluded as `GitPort.product_tree` does, equals the record's candidate digest even when the work tree changes between `execute-gates` and `report`.
- [ ] **AC-0008.** The commands `execute-gates` runs are exactly those in the approved spec's gate declaration; a result file carrying commands, an exit code or a record leaves them unchanged and is refused when it asserts proof.
- [ ] **AC-0009.** A gate execution ends its commands once their summed running time reaches 1200 seconds, and yields no passing record.
- [ ] **AC-0010.** A gate execution keeps at most 1 MiB of captured output per command; a command that prints more is ended and yields no passing record.
- [ ] **AC-0011.** The run lock's stale window of 2400 seconds is not reached while a gate execution, including its cleanup, holds the lock.
- [ ] **AC-0012.** `correct-task` for an admitted task opens an owner decision, and without an `owner` authority reference the request stays open and nothing is appended.
- [ ] **AC-0013.** With an `owner` authority reference, `correct-task` appends one `task-correction.v1` record naming the target commit.
- [ ] **AC-0014.** After that record the task is open again and the supervisor issues it as the next request.
- [ ] **AC-0015.** After a correction, gate records, review reports and later tasks that depended on the corrected task are stale, and every earlier record remains in place.
- [ ] **AC-0016.** A run started before the release keeps accepting a boolean `gate.passed` under its pinned scripts, and no existing receipt is rewritten as a `gate-execution.v1` record.

**Record commits**

- [ ] **AC-0017.** With record paths declared in the approved spec, `commit-record <spec-dir> --manifest <file>` creates one commit whose changes are exactly the manifest's declared paths plus one `record-commit.v1` audit entry, and issues no `history-adoption` request.
- [ ] **AC-0018.** `commit-record` advances the product ref and `HEAD` together by compare-and-swap, and moves neither when either compare fails.
- [ ] **AC-0019.** `commit-record` refuses and moves no ref when the manifest names an undeclared path, a glob, a stale base commit, content whose digest differs from the manifest, a link, or any change beyond the manifest's paths.
- [ ] **AC-0020.** `commit-record` refuses for `spec.md`, `plan.md`, a cited authority record, anything under `delivery/`, installed skill files and Git control files, even when declared.
- [ ] **AC-0021.** `commit-record` refuses while an attempt is open or residue is unresolved.
- [ ] **AC-0022.** A second `commit-record` with the same manifest creates no second commit.
- [ ] **AC-0023.** A commit made outside the supervisor still produces the `history-adoption` request, and a crash between the ref move and the record write leaves the existing adoption recovery in force.

**Review budget**

A round is one recorded findings record (`<round>-record.md`, the unit `review-artifact.py` already numbers) in a phase, either spec-stage or implementation. A repair is a round whose subject differs from the previous round's after that round left a sustained finding open. A finding class is the finding's `rule_ref` when it has one, and otherwise its recorded fingerprint, so only a repeat of the same finding counts. Active hours are the summed wall-clock time between a request issuance and its report.

- [ ] **AC-0024.** The run store holds a review-budget record with the count of rounds by phase, of repairs by finding class, the active hours and the retries.
- [ ] **AC-0025.** `status` prints each count in the review-budget record.
- [ ] **AC-0026.** The counts are unchanged across a replan and across `adopt-history`.
- [ ] **AC-0027.** The next review dispatch refuses with `review-budget-exhausted` and lists the open findings when a phase has three rounds with an open sustained finding, or when one finding class has two repairs; the existing caps keep their scopes and counts: five findings records per review run, five failed task gates per run, and two code-review rounds per unprotected unit. For one review run and phase the three-round limit fires first, so the five-record cap binds only on a route the three-round limit does not reach.
- [ ] **AC-0028.** `extend-review` with an `owner` authority reference allows exactly one further round past the three-round or two-repair limit, and leaves the other caps unchanged.
- [ ] **AC-0029.** A report rejected for format and replaced once adds no round.
- [ ] **AC-0030.** Exhaustion never records a clean result and never accepts an open Blocker or Concern.

**Checkout ownership**

- [ ] **AC-0031.** `start` in a primary checkout refuses with `checkout-not-isolated`; `--allow-primary-checkout` admits it and the run record names the override.
- [ ] **AC-0032.** `start` in a linked worktree reserved by another non-terminal run refuses with `checkout-reserved` naming that run.
- [ ] **AC-0033.** Two `start` calls for different specs in one worktree, run at the same time, leave exactly one non-terminal owner, and the loser makes no run or product-ref change.
- [ ] **AC-0034.** A reservation ends when its run is terminal, and a reservation whose run store is absent does not block `start`.
- [ ] **AC-0035.** `status` for a non-terminal run prints the run store's path and that removing the worktree discards it.

## Follow-ons

- eugenelim: engine RFC for `self_host.py` nested-worktree pruning — `docs/rfc/` (open when scheduled).
- eugenelim: run relocation and completed-task import — new spec when moving unfinished runs becomes a requirement.
- eugenelim: knowledge-capture record commits — new spec once gate-execution proof exists.

## Assumptions

- Defaulted: Process: each slice ships as a separate PR under this one spec — default: four sequential PRs, spec `Implementing` until the last; if wrong: one PR and one review unit (settled by: eugenelim).
- Defaulted: Technical: the supervisor runs gates in the owner's account with bounded time and output, not in a sandbox — default: no sandbox; if wrong: a sandbox slice is added (settled by: eugenelim).
- Defaulted: Technical: the review-budget and gate-execution limits are the values the criteria state — default: those; if wrong: the numbers change, not the shape (settled by: eugenelim).
- Technical: gate-declaration syntax inside Agent Rules is not yet fixed — it fixes the spec text adopters write (settled by: plan task T1, grounded against the projector).
