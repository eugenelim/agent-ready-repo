# Work-loop run records

A full-mode run keeps its state where it can be checked: in Git commits, in
committed records, and in a few local files. Putting a counter in prose ("we
cap at 5 iterations…") leaves it un-enforceable; putting it in records one
writer owns lets `work-supervisor.py status` derive the same answer every time.

One tool owns these records: **`scripts/work-supervisor.py`**. Nothing else
writes them, and nothing is edited by hand. `status` reads them without writing,
and every other verb derives the current action from them before it acts. Light
mode and direct-light keep no supervisor run records; pre-approval and light
review use the separate numbered review artifacts listed below.

## Where a run's facts live

| Record | Written by | Committed | What it holds |
| --- | --- | --- | --- |
| Git history | each admitted step | yes | One commit per step (`implement`, `gate-fail`, `replan`, `review`, `terminal`, and the rest), each trailered with the run id. The supervisor re-derives the run from these on every call. |
| `<spec-dir>/delivery/approvals.jsonl` | `start` | yes | The approval pair: the scope owner's and the plan reviewer's authority references, the run id, and the reviewed-envelope fingerprint and terminal intent they approved. |
| `<spec-dir>/delivery/evidence.jsonl` | `report` | yes | Evidence receipts for gates, criteria, and review findings. Readiness is evaluated from these on every call. |
| `<spec-dir>/delivery/review-selections.jsonl` | `report` | yes | One line per delivery subject and changed-path digest: the conditional reviewer roles selected and each omission with its reason. |
| `<spec-dir>/delivery/review-decisions.jsonl` | `report` | yes | Reviewer reselections and accepted risks, each under the named human's authority reference. |
| `<spec-dir>/delivery/effect-resolutions.jsonl` | `resolve-effect` | yes | A named human's decision about an external effect whose outcome could not be established. |
| `<git-dir>/agentbundle-supervisor/gates/` | `park` | no | One record per spec for a gate waiting on a human: the gate, intent, code trust, both gate digests, and the commit parked. `gates` reads it. A record approves nothing. |
| `<spec-dir>/.supervisor/run.json` | `start`, `next` | no | The status view below. Deleting it loses nothing. |
| `<spec-dir>/.supervisor/journal.jsonl`, `security-events.jsonl` | `next`, refusals | no | The local request journal, and a line for each check that could not be verified. Deleting either neither reopens a closed attempt nor clears an owed confirmation. |
| `<git-dir>/agentbundle-supervisor/<run-id>/` | `start`, `next`, `report` | no | The pinned digests of the installed supervisor files, the open attempt's manifest, issuance marks, and the not-red recovery record. |
| `<spec-dir>/delivery/task-corrections.jsonl` | confirmed `report` | yes | Append-only `task-correction.v1` records; matching receipt supersessions append to `evidence.jsonl` in the same commit. |
| `<spec-dir>/delivery/record-commits.jsonl` | `commit-record` | yes | `record-commit.v1` audits admitted manifest bindings alongside the declared ledger files. |
| `<git-dir>/agentbundle-supervisor/<run-id>/exec-*.started.json`, `exec-*.completed.json`, `candidate-*.json` | `execute-gates` | no | Gate execution and the frozen Git tree binding. Admission consumes proof through a committed `Supervisor-Gate-Execution` trailer. |
| `<git-dir>/agentbundle-supervisor/<run-id>/task-correction-request.json` | `correct-task` | no | The pending owner decision; its committed correction closes it. |
| `.context/reviews/<review-run-id>/<round>-record.md` | `review-artifact.py record` | no | Strict JSON numbered review records, with cumulative budget snapshots. |
| `<git-dir>/agentbundle-supervisor/<run-id>/review-budget.json` | admission and mutating supervisor steps | no | Current cumulative budget; the first approval commits the admission snapshot. |
| `<common-git-dir>/agentbundle-checkout-<sha256-of-git-dir>.json` | `start`, terminal transitions | no | One checkout reservation, serialized across specs. |
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
| `review_budget` | The cumulative snapshot defined below; readiness exposes the same budget. |
| `refusal` | The standing refusal (`code`, `owner`, `detail`) or an empty object. |

`status --json` adds `terminal`, `retry_count` and `retry_cap`, `readiness`, the
`tasks` (`task_id`, `position`, `title`, `complete`), `recovery_decisions`,
`recovery_leftovers`, and the current `request`. The full status surface is
described in [Supervisor status](supervisor.md#status-resume-and-the-retry-cap).

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
transition and stops no loop. It is not a stasis detector and bounds nothing by itself. The cumulative
budget and the retained caps are separate guards; their procedure lives in
[Pre-EXECUTE review](pre-execute-review.md#review-round-budget) and
[Supervisor review](supervisor.md#cumulative-review-budget).

## Troubleshooting

| Symptom | Cause and answer |
| --- | --- |
| A refusal `code` | Look it up in [`supervisor.md`](supervisor.md#refusals-and-their-owners): its one table lists every code, its cause, and the answer. |
| `run.json` missing or unreadable | Run `status` to inspect derived state or `next` to rewrite the local view. |
| Records written by an earlier release | Existing pins determine the gate protocol; see [Observed gates](supervisor.md#observed-gates). Unknown record versions refuse rather than becoming proof. |


## Execution and correction schemas

These are closed records with `schema_version: 1`: missing or extra fields,
unknown versions, or unreadable bytes refuse. Storage and commit disposition
are in the table above.

`gate-execution.v1` uses `type`, `execution_id`, `run_id`, `request_id`,
`issuance_id`, `task_revision` (SHA-256 or null for final gates),
`candidate_tree_digest`, `gate_declaration_digest`, `commands`, and `outcome`.
New records also hold `runtime`: `scratch`, `supervisor_pid`, `supervisor_start`,
and `processes` (each with `pgid` and `start`). The started checkpoint atomically
adds each identity before the gate is released. Completed records are immutable.
Earlier records without `runtime` remain readable. An orphan's `.recovered`
marker records cleanup only; it never serves as completed execution proof.
Recovery requires confirmed supervisor absence or a different process start
time. Unreadable start times leave execution and scratch alone.
Each command has `argv`, `cwd`, `expected_exit`, observed `exit_code` (integer
or null), `timed_out`, `stdout_digest`, and `stderr_digest`. Digests are
lowercase SHA-256. `outcome` is `started` with no commands, or completed
`passed` or `failed`. A pass requires command results with expected exits and
no timeout. The separate candidate manifest has `schema_version`, `tree`
(the frozen Git tree object) and `candidate_tree_digest`. Neither file is
committed; the admission trailer binds consumption to its commit.
`pins.json` holds the protocol marker described in
[Observed gates](supervisor.md#observed-gates).

`task-correction.v1` uses `type`, `correction_id`, `run_id`, `task_id`,
`task_revision`, `target_commit`, unique `affected_receipt_ids`, `reason`,
`authority_ref`, and positive `invalidation_epoch`. Epochs increase by one;
the correction commit must exist in run history. Derivation ignores prior
completion of the task and transitive dependents before that epoch. Receipt
identities retain affected dependencies even if a later replan removes an edge.
The supervisor appends supersessions rather than deleting earlier evidence.

## Controller record schemas

The controller supplies `record-manifest.v1`, a closed JSON object with
`schema_version: 1`, `type: "record-manifest.v1"`, `run_id`, `base_commit`,
`envelope_fingerprint`, and nonempty `entries`. Each entry has exactly `path`,
`kind`, `old_sha256`, and `new_sha256`. `kind` is a nonempty descriptive category
of at most 128 characters, never an authority claim. `old_sha256` is null for
an absent file; other digests are lowercase SHA-256 of the exact file bytes.
Paths are unique exact files from the approved allowlist. Keep the manifest
outside the changed path set; it is input, not automatically committed.

`record-commit.v1` has the same fields and entries, changes `type` to
`record-commit.v1`, and adds `manifest_digest`. The digest is SHA-256 of the
canonical manifest JSON (sorted keys, compact separators, trailing newline).
The audit row and declared record bytes are committed together with operation
`commit-record` and step `record:<manifest_digest>`. This never auto-adopts
commits based on their paths or trailers.

## Review-budget and checkout records

The closed budget has `schema_version: 1`, `kind: "review-budget.v1"`, and
`review_run_id`. `rounds` maps `spec-stage` and `implementation` to nonnegative
counts; `repairs` maps finding classes to counts. `active_hours` is finite and
nonnegative; `retries`, `finding_records`, and `failed_task_gates` are
nonnegative integers. `code_review_rounds` maps unit identities to counts.
`phases` maps each phase to `subject` (text or null) and `open_findings`, whose
entries have `fingerprint` and nullable `rule_ref`. `last_phase` is a phase or
null. `extension` is null or `{phase, round, authority_ref}`, binding the next
allowed round to its owner's reference.

Numbered review records add `review_phase`, `review_subject`, `finding_rules`
(fingerprint to rule), `extend_review`, and `review_budget`. The tool rebuilds
and validates snapshots from those records. An implementation recorder reads a
matching extension from this checkout's run-store budget without needing a second
`--extend-review`. It embeds `supervisor_budget` in that numbered record, carries
forward its counters, and records the consumed extension and owner reference.
Replay retains the grant for its exact round; the next round needs a new grant.
`start --review-run-id` imports
the same identity and counters into the run store and initial committed
approval. Later mutating steps checkpoint the local budget; derived counts
never fall below the checkpoint after replan or adoption. A missing budget
beside pins without `gate_execution_protocol` is rebuilt from numbered records
and atomically checkpointed. Its identity comes from the approval snapshot or,
without one, the deterministic supervisor-run-derived UUID. The import uses a
separate checkpoint lock because state derivation also runs under the run lock.
Missing budgets beside current protocol pins and existing malformed budgets
refuse; a store-less checkout can use the approval snapshot. Extension decisions commit to `delivery/review-decisions.jsonl`
and carry `Supervisor-Review-Budget-Round` and `Supervisor-Authority-Ref`
trailers so replay restores the grant without minting another.

Without an imported identity, admission derives `review_run_id` deterministically
from the supervisor run identity. Repeating admission after a crash keeps it.

The supervisor measures time from a request's first issuance to its report
with its own clock. Confined run-store files named
`request-time-<SHA-256 of request_id>.json` contain `schema_version: 1`, `run_id`,
and `issued_at`. They are local, not committed; repeated `next` calls retain
the first timestamp. Accepted reports checkpoint `report-times.json` in the
run store, with `schema_version: 1`, `run_id`, and `seconds` mapping each
request identity to its elapsed seconds. This local file also covers reports
that make no commit. An admitted report's commits carry
`Supervisor-Active-Request` and `Supervisor-Active-Seconds`. Budget replay
merges the local timings and commit trailers once per request and adds
imported active hours, so a crash after commit cannot lose or double count
measured time. Backward clock movement contributes zero. Older requests
without timestamps contribute no measured time. The standalone `record` CLI
supplies no elapsed time; zero does not prove that no review time was spent.
Implementation phase counts come from
numbered records; typed supervisor reports alone do not create those records.
The existing code-review unit counter remains a separate derived guard.

The checkout reservation is a closed object with `schema_version: 1`, `run_id`,
and `spec_rel`; JSON null means released. Its filename hashes the pinned
working-tree Git directory, so linked worktrees have separate reservations in
the shared common Git directory. It is local and uncommitted. Admission
serializes reservation checks and the start transition; a reservation for an
absent run store is stale. Release holds the checkout lock then the run lock,
refreshes HEAD and re-derives terminal state; a reopened run keeps its reservation.
The approval records `allow_primary_checkout` as a
boolean. See [Before start](supervisor.md#before-start) for the override and
release behavior.
