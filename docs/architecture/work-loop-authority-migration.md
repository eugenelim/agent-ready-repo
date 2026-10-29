# Subsystem Design — Work-loop authority migration

**Decision:** Each work-loop authority moves only through an accepted record
that names what it supersedes. Core 4.0.0 moved phase, cohort, plan-lock, and
review-gate authority to the [execution supervisor](work-loop-execution-supervisor.md)
in one switch, with no compatibility adapter, reverse reader, or dual-write
path ([ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md) D7).
Parallel admission and the knowledge capture gates have not moved yet.
**Author:** Platform Core
**Status:** Current
**Last updated:** 2026-10-29
**Reviewers:** Core, `agentbundle`, and architecture-governance maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Where each work-loop authority lives now, and what still has to move | Rewriting frozen ADR bodies | A new accepted record, not implementation, changes authority |
| The governance record behind each move | Child contract fields | The owning subsystem designs define their schemas |
| Remaining obligations for Slices 7 and 8 | Slice status | The [brief's delivery slices](../product/briefs/acceptance-centered-work-loop.md#proposed-delivery-slices) own it |

An implementation never supersedes an accepted record by implication. A move
lands only with the record that authorizes it, and the baseline architecture
pages change in the same reviewed change.

## 2. Authority Map

| Former authority | Current authority | Governing record | Remaining obligation |
| --- | --- | --- | --- |
| The phase engine's transition table and its completion phase | Readiness derived by the supervisor from the approval pair, `acceptance-verdict.v1` over admitted evidence, and structured review readiness | ADR-0144 D1, D8; supersedes ADR-0061 D1, D2 and ADR-0064 D1, D2 in part | None |
| The cohort writer as writer of record, with engine-invoked cohort effects | Supervisor commits, one step each, and committed `delivery/` records | ADR-0144 D1; supersedes ADR-0125 | None |
| The whole-artifact approval pin of the spec and plan | One `approval-record.v1` plus one `initial-plan-review.v1` per `start`, bound to the reviewed-execution-envelope fingerprint and terminal intent; in-envelope plan and task changes commit as `replan` with no approval | ADR-0144 D3; [ADR-0151](../adr/0151-post-lock-routes-for-the-stub-fence-and-implementation-discovered-means.md) D3 narrows ADR-0144 D3 and D11 for the change after a not-red stub | None |
| The plan author's approved-plan stub fence, and the verification-ledger route for an `implementation-discovered` seam or design means | A controller task-start fence revision, and a controller edit to the plan's `## Design (LLD)`, each committed as `replan` while no attempt is open | ADR-0151 D1, D2; supersedes ADR-0150 D3, D5 in part | None |
| The legacy review gate (`raw-classify` and adjudication grammar) for full-mode code review | Structured review readiness: current `review-report.v1`, `finding-assessment.v1`, and `finding-disposition.v1` records, with roles selected by `review-rules.json` | ADR-0144 D8 | Light mode and pre-approval review keep `review-artifact.py`'s classifier |
| Unknown-effect handling, which had no durable form | `effect-resolution.v1` in `delivery/effect-resolutions.jsonl` | ADR-0144 D6; supplies what ADR-0061 D8 deferred | None |
| The event file's producer | The supervisor, one line per step in the unchanged `loop-run-event` envelope; the bridge reads `run.json` | ADR-0144 D10; supersedes ADR-0064 D5, D6 in part (commit-derived lines replace the outbox and pending-event replay); ADR-0064 D3, D4, D7 stand | None |
| The planned `wave-decision` contract | Retired with its schema; the supervisor dispatches sequentially | ADR-0144; the [parallelism page](loop-parallelism.md) records what remains | Slice 7 decides any parallel scheduler decision record |
| ADR-0061 D5's ban on parallel-wave orchestration | Unchanged; sequential is the only mode | ADR-0061 D5 | Slice 7: an accepted record supersedes it and names the admitted modes |
| ADR-0005 D3 safe categories and D4 post-write `git merge-tree` disjointness gate | Unchanged | ADR-0005 | Slice 7: a parallelism record supersedes D3 and D4 while keeping fail-closed admission and merge-conflict handling |
| The mutable execution-root worktree as the product result | Unchanged | ADR-0144 D9 | Slice 5: [product result integration](work-loop-result-integration.md) |
| The `project-knowledge --producer-profile work-loop` capture gates `spec-approved` and `plan-locked` | Retained under those names, beside the read-only delivery fact feed over each spec's committed `delivery/evidence.jsonl` | [Knowledge capture](knowledge-capture.md) | Slice 8 removes both gates |
| Close-time `work-item` capture | Retained as an explicit capture | [Knowledge capture](knowledge-capture.md) | None |

## 3. Data Transition

| Former artifact | Current artifact | What happens to old data |
| --- | --- | --- |
| `engine-state.json` and the cohort `state.json` | Supervisor commits, `delivery/` records, and the deletable `<spec>/.supervisor/` | Never read. `start` ignores both files, and an in-flight run is re-derived from the spec, plan, Git history, evidence, and review facts |
| The approved spec and plan digests | `delivery/approvals.jsonl` | A new `start` records the pair against the current envelope |
| Ledger observations and engine events as evidence | `delivery/evidence.jsonl` | Execution observations stay in the verification ledger; evidence is what the supervisor admits |
| Raw reviewer output and the review verdict record | Structured review records | Full-mode code review reads only the structured records |

Reversal is reinstalling the prior Core major. That release cannot read
supervisor records, so they are discarded rather than projected backwards.

## 4. Runtime and Failure Model

A move follows four steps:

1. The governing record is accepted and names the decisions it supersedes.
2. One change switches the reader and writer together.
3. The same change updates the baseline architecture pages.
4. The release names the consequence for in-flight work.

Replanning inside the reviewed envelope is not an authority move. The
supervisor commits it as a `replan` step. A change to a protected reference or
the terminal intent refuses until its owner acts.

## 5. Invariants

| Invariant | Enforcement |
| --- | --- |
| An accepted record is never superseded by code alone | Each move cites its record; the ADR shape lint checks supersession mirrors |
| One concern has one writer | Only the supervisor writes procedure state and `delivery/` records |
| Initial review is not a permanent task lock | In-envelope plan and task changes need no approval |
| Parallelism cannot arrive early | The supervisor dispatches one request at a time until Slice 7's record is accepted |

## 6. Remaining Moves

| Slice | Sources that change together | Proof |
| --- | --- | --- |
| Slice 5 result integration | `work-loop-result-integration.md`, the subject provider, `ARCHITECTURE.md` | Old and new providers yield the same manifest; conflict and crash recovery pass |
| Slice 7 parallel admission | `ARCHITECTURE.md`, `loop-parallelism.md`, a record superseding ADR-0061 D5 and ADR-0005 D3, D4, the scheduler, and security and integration ports | Missing governance or read proof serializes; permutations equal the sequential result |
| Slice 8 removal | The `spec-approved` and `plan-locked` capture gates, `knowledge-capture.md`, `work-loop-knowledge-handoff.md` | Removal rehearsal in a clean environment |

Frozen ADR bodies stay unchanged. A superseding record carries the
relationship, and the superseded record's status fields mirror it.

## 7. Quality Scenarios

| Stimulus | Response | Verification |
| --- | --- | --- |
| A spec directory holds `engine-state.json` or a cohort `state.json` | `start` never reads either | Supervisor admission fixtures |
| A working plan reorders, splits, or replaces tasks | Reproject without approval | Replan corpus |
| A replan changes a protected reference or terminal intent | Refuse and name the owner | Replan corpus |
| A parallel provider appears before Slice 7's record | Nothing dispatches concurrently | Sequential dispatch only |

## 8. Risks and Ownership

- **Risk:** an in-flight run cannot be re-derived. **Mitigation:** it restarts
  from its approved spec; the owner accepted this risk on 2026-10-11 because
  distribution is small.
- **Risk:** baseline pages and accepted records disagree after a move.
  **Mitigation:** both change in the move's reviewed change.

| Responsibility | Owner |
| --- | --- |
| Superseding work-loop authority records | Architecture-governance owner |
| Slice moves | Core and `agentbundle` maintainers |
| Parallelism supersession and safety proof | Architecture-governance, security, and Core maintainers |
| Release and reversal | Core pack release maintainers |
