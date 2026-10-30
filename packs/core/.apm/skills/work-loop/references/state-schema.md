# Work-loop run records

A full-mode run keeps its state where it can be checked: in Git commits, in
committed records, and in a few local files. Putting a counter in prose ("we
cap at 5 iterations…") leaves it un-enforceable; putting it in records one
writer owns lets `work-supervisor.py status` derive the same answer every time.

One tool owns these records: **`scripts/work-supervisor.py`**. Nothing else
writes them, and nothing is edited by hand. `status` reads them without writing,
and every other verb derives the current action from them before it acts. Light
mode and direct-light keep none of them.

## Where a run's facts live

| Record | Written by | Committed | What it holds |
| --- | --- | --- | --- |
| Git history | each admitted step | yes | One commit per step (`implement`, `gate-fail`, `replan`, `review`, `terminal`, and the rest), each trailered with the run id. The supervisor re-derives the run from these on every call. |
| `<spec-dir>/delivery/approvals.jsonl` | `start` | yes | The approval pair: the scope owner's and the plan reviewer's authority references, the run id, and the reviewed-envelope fingerprint and terminal intent they approved. |
| `<spec-dir>/delivery/evidence.jsonl` | `report` | yes | Evidence receipts for gates, criteria, and review findings. Readiness is evaluated from these on every call. |
| `<spec-dir>/delivery/review-selections.jsonl` | `report` | yes | One line per delivery subject and changed-path digest: the conditional reviewer roles selected and each omission with its reason. |
| `<spec-dir>/delivery/review-decisions.jsonl` | `report` | yes | Reviewer reselections and accepted risks, each under the named human's authority reference. |
| `<spec-dir>/delivery/effect-resolutions.jsonl` | `resolve-effect` | yes | A named human's decision about an external effect whose outcome could not be established. |
| `<spec-dir>/.supervisor/run.json` | `start`, `next` | no | The status view below. Deleting it loses nothing. |
| `<spec-dir>/.supervisor/journal.jsonl`, `security-events.jsonl` | `next`, refusals | no | The local request journal, and a line for each check that could not be verified. Deleting either neither reopens a closed attempt nor clears an owed confirmation. |
| `<git-dir>/agentbundle-supervisor/<run-id>/` | `start`, `next`, `report` | no | The pinned digests of the installed supervisor files, the open attempt's manifest, issuance marks, and the not-red recovery record. |
| `.loop-run/events.jsonl` | every admitted step | no | One line per supervisor step, in the event envelope that observers read. |

Never edit a record under `delivery/` by hand: an edit by anything but the
supervisor refuses the next verb with `foreign-delivery-edit`.

## `run.json`

| Field | Meaning |
| --- | --- |
| `run_id` | The run's identity, `run-` and 16 hexadecimal characters. |
| `active` | `true` while the run has a run id and is not terminal. |
| `stage` | `admitted`, `implementing`, `gating`, `reviewing`, `awaiting-human`, or `terminal`. |
| `gate_pending` | `true` while an open `human-decision` request waits for an answer. |
| `gate_question` | The question that request puts to the human; supervisor-authored text. |
| `refusal` | The standing refusal (`code`, `owner`, `detail`) or an empty object. |

`status --json` adds `terminal`, `retry_count` and `retry_cap`, `readiness`, the
`tasks` (`task_id`, `position`, `title`, `complete`), `recovery_decisions`,
`recovery_leftovers`, and the current `request`.

## What the plan contributes

The supervisor projects tasks from the plan's `### T<n>:` sections: `Depends on:`,
`Touches:`, `Tests:` with any `stub` fences, `Done when:`, and `Effects:`. A
task's identity is derived from its title without its number, and its revision
is a digest of the content that decides what the task asks for, stub fences
included. A task is complete when the commits and receipts the supervisor made
for its current revision say so, so a change to a task's text makes a new
revision, while a change elsewhere in the plan leaves finished tasks finished.

What the approval covers is the **reviewed execution envelope** and the terminal
intent. A plan edit that leaves both unchanged is committed by `next` as a
`replan` step with no approval. A change to either is refused, naming the
amendment or the plan-review authority that owns it.

## The retry count

`retry_count` counts `gate-fail` steps in the run's history. At the cap
(`implementation_retry_cap` in `supervisor-policy.json`, five by default) the
run is stopped with a `retry-cap` decision that no replan, amendment, or new
approval resets, and `status --check` exits 3.

## Repeated findings

`review-artifact.py inspect --run-id <uuid> --json`, which pre-approval and
light-mode review use, returns `matches_previous_round: true` when a round's
fingerprint set equals the previous round's exactly. Surface it; it starts no
transition and stops no loop. It is not a stasis detector and bounds nothing —
`max_review_retries` is what bounds a review loop. In a full-mode run the
supervisor assesses each finding afresh, and the retry count above is the only
cap.

## Troubleshooting

| Symptom | Cause and answer |
| --- | --- |
| A refusal `code` | Look it up in [`supervisor.md`](supervisor.md#refusals-and-their-owners): its one table lists every code, its cause, and the answer. |
| `run.json` missing or unreadable | Run `status` or `next`; both rewrite it from Git history and the committed records. |
| Records written by an earlier release | Nothing reads them. The supervisor re-derives the run from the spec, the plan, Git history, and the committed records; a task counts as incomplete until the loop re-runs or replans it. |
