# Verification ledger: execution supervisor cutover

Execution observations for the approved plan. This file is not hash-pinned; it
records how tasks are verified, not new obligations.

## T1: hook discovery uses a standard-library confinement check

The plan's Design names `list_confined_regular_files` for the hooks' run
discovery. The shipped hook runs in adopter repositories where `agentbundle`
may not be importable, so both hook copies use a standard-library check
instead. It refuses a link at `docs/`, `docs/specs/`, the spec directory,
`delivery/`, and `approvals.jsonl`. It requires a regular file, and it requires
the file's real path to stay inside the repository. AC-0017's property is
unchanged, and VI-7003 covers the symlinked-spec case.

## T1: the oversize threshold for a gate question is 4 KiB

AC-0015 refuses an oversized gate question. The bridge treats a question over
4 KiB of UTF-8 as oversized and shows only the fixed placeholder; the
`review-report` content-safety check then runs on what remains. `run.json`
itself is read with a 64 KiB bound. VI-7002 covers the oversized case.

## T1: identical back-to-back gates inside one poll

`run.json` carries no request id. The bridge treats a new `run_id` or a changed
question while a gate is pending as a new gate, and notifies. Two consecutive
gates with identical question text that resolve and reopen inside one 200 ms
poll stay indistinguishable; `workspace_status` still shows the open gate.

## Dispatch accounting

T2 and T3 carry a `human-directed` dispatch decline in wave 0: the owner
directed the first review unit to cover T1 only, because T2 waits on
`execution-supervisor-attempt-security`. Both tasks stay incomplete and get
fresh receipts when they start.

## Deferred review Nits

- T1 security review, Nit: when the hook skips a linked spec that holds
  `approvals.jsonl`, it reports "no delivery/approvals.jsonl" instead of naming
  the skipped spec. Status: deferred.
- T1 quality review, Nit: `test_instruction_shaped_question_is_framed_inert_in_field_and_notification` uses harmless text; the instruction case is the next test. Status: deferred.
- T1 quality review, Nit: nothing but the parametrized hook tests catches drift between `packs/core/.apm/hooks/pre-pr.py` and `tools/hooks/pre-pr.py`; `make build-self` regeneration is the other guard. Status: deferred.
- T1 quality review, Nit: the hook test's `at-cap` case is a label only; the terminal-at-cap exit code is proven by the work-loop supervisor readiness suite. Status: deferred.
- T1 adversarial review, Nit: an untracked root `uv.lock` written by a tool run stays out of the commit. Status: deferred.

## T1: the bridge's run signal is `run_active`

AC-0013's active signal is exposed as `run_active` in `workspace_status`,
because `workspace_status` already returns an `active` list of resumable specs
and a same-named field would overwrite it.

## T2: AC-0026 extends two delivery contracts additively

AC-0026's replan confirmation is a `human-decision` request and result, and
`contracts/delivery/execution-request.v1` and `execution-result.v1` set
`additionalProperties: false`. The request gains an optional `diff` string; the
result's decision enum gains `confirm-replan` and `decline-replan`, shaped like
`reselect-review` (a `selection_key`, no `finding_ids`). Every record that
validated before still validates, so the schemas stay v1. The owner, eugenelim,
approved amending the spec's `Contract:` line for this on 2026-10-29.

## T2: AC-0026 red proof

Command, before production code:
`WORK_SUPERVISOR_INTEGRATION=1 python -m pytest packs/core/tests/skills/work-loop/test_supervisor_tdd.py -q`
Result: 9 failed, 12 passed. The closure test failed because the refused stub
file stayed in the tree, and each recovery test failed with `attempt-residue`
on `docs/specs/calc/plan.md`, today's behaviour. The 12 passing cases are the
existing suite plus three regression guards that hold before and after.

## T2: the supervisor store is the trust root for the owed confirmation

The owed confirmation lives in `recovery.json` in the run store under the Git
directory. AC-0026 requires that deleting the journal, `run.json`, or
`security-events.jsonl` cannot clear it, and the code meets that. A writer that
can delete records in the Git-directory store itself could clear it, but that
store is the attempt-security trust root, and protecting it is outside this
spec. The security reviewer's AC-0026 pass recorded this as out of scope.

## Deferred review Nits (T2, AC-0026 slice)

- Quality, Nit: the `close_not_red` docstring says a retry repeats the steps, but a crash after discard needs the reissued `write-stub` redone. Status: deferred.
- Quality, Nit: when `close_not_red` is a no-op, the `stub-not-red` text still says the attempt closed. Status: deferred.
- Quality, Nit: the authority and digest refusal test asserts only the exit code. Status: deferred.
- Quality, Nit: a comment in the local-state wipe test sits above the wrong line. Status: deferred.
- Quality, Nit: `exempt=True` makes `_refuse_protected_change` read as a skipped check. Status: deferred.
- Quality, Nit: a leftover at a path that is a symlink in HEAD never clears, because `_at_head` matches only regular files or absence. It fails closed. Status: deferred.
- Security, Not checked: two older `unexpected-change` refusals in `_supervisor_loop.py` still join paths without `_named`; they predate this change. Status: deferred.
