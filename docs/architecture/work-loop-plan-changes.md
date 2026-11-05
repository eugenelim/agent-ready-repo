# Work-loop plan changes and the TDD guard

The supervisor accepts a plan edit without approval while the edit leaves six
protected references and the terminal intent unchanged. It refuses any other
edit and names the owner. A task with a stub fence must be observed red before
its implementation is issued.

This page owns the replanning envelope and the TDD guard. [The supervisor
page](work-loop-execution-supervisor.md) owns the request order, the stages, and
the rest of the procedure.

## 1. Replanning

There is no whole-plan lock. The envelope covers six protected references:[^1]

- `spec_policy`: acceptance criteria, testing strategy, and agent rules;
- `scope_and_non_goals`;
- `authority_and_security`: the `Constrained by:` value and each cited record's
  decision section;
- `public_contracts`: the `Contract:` value;
- `durable_outputs`;
- `accepted_risk`.

Any edit that leaves all six and the terminal intent unchanged commits as one
`replan` step with no approval. That covers reordering, splitting, merging, or
replacing tasks, editing tests, stubs, effects, or the plan's `## Design (LLD)`,
and bookkeeping. Unintegrated attempts of superseded tasks cancel, and completed
work stays complete.

A task is complete only for its current revision. The revision digests the title
and the pinned fields `Tests:` (with its stub fences), `Touches:`, `Done when:`,
and `Effects:`.[^2] Editing a pinned field of a completed task makes that task
due again. Editing `Approach:` or `Depends on:`, renumbering, or reordering
leaves it complete.

A change to a protected reference or the terminal intent refuses. The refusal
names the spec-amendment, decision, contract, risk, or plan-review owner.

A controller plan edit is in-envelope only while no attempt is open. During an
attempt, any plan change refuses it with `attempt-residue`, so the controller
edits after reporting the open request and before the next `next`.

The grounding of an `implementation-discovered` seam or design means, and each
correction, is such an edit to the plan's `## Design (LLD)`
([ADR-0151](../adr/0151-post-lock-routes-for-the-stub-fence-and-implementation-discovered-means.md)
D2). The verification ledger keeps execution observations only.

## 2. TDD guard

The red test is written at EXECUTE
([ADR-0150](../adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md)).
A task with a stub fence runs these steps (ADR-0151 D1, ADR-0144 D5):[^3]

1. The controller writes the fence into the task's `Tests:` as a task-start
   revision, after the previous result is reported and before the `next` that
   issues the task's first request.
2. `next` commits that edit as a `replan` step.
3. `next` issues `write-stub`. The worker writes the stub files, and its result
   may change exactly the fenced stub paths. Anything else refuses
   `not-exactly-stub`.
4. The supervisor runs the stubs and checks they match the fence byte for byte
   and exit with a code the fence declares as red.
5. It commits the `stub` step with its red proof. When the stub bytes are already
   in `HEAD`, because the task was revised after its stub commit, the supervisor
   runs them on a scratch copy and commits only a `red` step.
6. Only then is `implement-task` issued. A worker attempt that writes or changes
   a fence is refused.

### A stub that is not red

When the supervisor's own red run of committed stubs finds them not red, `next`
refuses `stub-not-red`. That run uses a scratch copy, so nothing is discarded and
no confirmation is owed. The controller's fence edit commits as an ordinary
`replan`.

When a `write-stub` result's stub already passes, `report` refuses
`stub-not-red`. Once the attempt checks find no difference, that refusal closes
the attempt and discards the files it and its launch changed.

Nothing from the result commits. The run store records that a confirmation is owed (ADR-0151 D3).

The next trusted-file change then opens a `human-decision` carrying its diff and
a digest of its exact bytes:[^4]

- **Confirm.** A `confirm-replan` answer with an `owner` authority reference
  commits the change as a `replan` step only when the change set is exactly the
  bound files and the bytes still match the digest. The commit carries the
  authority reference in a `Supervisor-Authority-Ref` trailer.
- **Decline.** A `decline-replan` answer commits nothing. `next` refuses
  `replan-declined` until the trusted files match `HEAD` again. Restoring them
  brings back the fence that was not red, so `write-stub` runs again, and the
  next trusted-file change still needs a confirmation.

Both answers are recorded with their authority reference and digest in
`recovery.json` in the run store. A file the discard could not remove blocks
every step until the controller removes it or restores it to `HEAD`.

[^1]: `packs/core/.apm/skills/work-loop/scripts/_supervisor_projector.py`:
    `classify_replan` and the envelope references.

[^2]: `_supervisor_projector.py`: task projection, where the revision digests the
    title and the pinned fields.

[^3]: `_supervisor_tdd.py`: the red-before-green guard.

[^4]: `_supervisor_recovery.py`: the not-red recovery and `recovery.json`.
