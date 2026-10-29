# Session resumption

A full-mode run needs no checkpoint file of its own: `work-supervisor.py` derives
the current action from Git history and the committed records on every call, so a
lost session, a deleted `run.json`, or a rebased branch loses nothing. Resume as
follows.

## Resuming a full-mode run

1. **Find the run.** When `<spec-dir>/delivery/approvals.jsonl` exists, a run was
   admitted. Run `python '<skill-dir>/scripts/work-supervisor.py' status <spec-dir> --json`
   and read `run.run_id`, `run.stage`, `terminal`, `retry_count`, `tasks`, `request`,
   and `refusal`. A refusal in the answer is the first thing to deal with: read its
   `code`, `owner`, and `detail`, and follow [`supervisor.md`](supervisor.md).
2. **Read the artifact statuses before acting on the stage.** If `spec.md` is
   `Draft` or `plan.md` is `Drafting`, no run exists yet; resume PLAN and the
   approvals. If both are `Approved` and no `approvals.jsonl` exists, the humans
   approved and `start` did not run: check that the plan's Changelog carries both
   approval entries, then request the missing `spec-approved` capture if it was
   not made, write `Implementing` and `Executing`, and run `start`. An `Approved`
   status with no Changelog entry is **Surface and stop**: the approver's handle
   cannot be inferred. `Archived` is terminal, so **Surface and stop**.
3. **Route by what `status` shows.**

   | `status` shows | Action |
   | --- | --- |
   | `terminal: true` | The run is ready or ended. Run `status --check`, then the Finish checklist and PR if they are not done. |
   | a `request` of a worker kind | Answer it. A request is re-issued, with the same identity, until its result is reported, so run `next` and answer what it returns. |
   | a `human-decision` request | Wait for the named human, then report only the answers [`supervisor.md`](supervisor.md) lists for that reason. |
   | a `refusal` | Follow its `owner`, and look its `code` up in [`supervisor.md`](supervisor.md#refusals-and-their-owners). |
   | `retry_count` at the cap | The run is stopped. Surface it; no replan or approval resets it. |
   | `recovery_leftovers` not empty | Remove each named path or restore it to `HEAD`, then `next`. |

4. **Do not re-run completed steps.** Every admitted step is a Git commit; `next`
   never reissues a task whose commits and receipts show it complete for its
   current revision. `start` on an admitted run answers `current` and changes
   nothing. A `report` for a request that was already reported is refused
   `not-current-attempt`: run `next` instead.
5. **Check an interrupted effect.** After a crash between performing an external
   effect and reporting it, `next` issues `effect-query` instead of the effect:
   ask the effect's source and report what it says. Never repeat an effect by
   hand.

## A run left by an earlier release

A run begun under an earlier release is not resumed in place. The supervisor
derives its tasks from the spec, the plan, Git history, and the committed
records; a task counts as incomplete until the loop re-runs or replans it. Files
an earlier release left in the spec directory are inert: nothing reads them, and
they need no reset. Start the run again with `start`.

## Legacy light mode

Legacy light-mode resumption applies only to a persisted spec that carries
`Mode: light (no risk trigger fired)` and has no `<spec-dir>/delivery/approvals.jsonl`.
These existing specs remain readable, valid, and resumable; direct-light itself
does not create or resume one:

| spec `Status` | Resume at |
|---|---|
| `Draft` | resume PLAN. |
| `Approved` | Resume at Step 2 EXECUTE. Write `Status: Implementing` before any code change. |
| `Implementing` | Reconstruct progress from the task list and working tree. |
| `Shipped` / `Archived` | Terminal. No further work needed. |

**If `delivery/approvals.jsonl` is present**: use the full-mode protocol even if spec Status is `Approved`. Never infer light mode from spec Status alone when a run's records exist.

**Ambiguous** (no `Mode: light` line AND no `delivery/approvals.jsonl`): surface to the human rather than guessing.
