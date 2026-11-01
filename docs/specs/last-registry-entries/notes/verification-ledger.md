# Verification ledger: last-registry-entries

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-10-31 | eugenelim | RFC-0106 errata entry of 2026-10-31, before the run | `docs/rfc/0106-stop-registering-derivable-work.md` | `c24afbde4576cb815648e69f89a210c9461a2a5caff22aaeb183edfa8a41304a` |
| 2026-10-31 | eugenelim | brief Spec map row and after-cutover slug annotations | `docs/product/briefs/workspace-registry-retirement-delivery.md` | `2c4e141ec8c3f3e34367a8fdfc0fb2da5401acdefecba99b6177adb77acc20a8` |

## Run notes

- 2026-10-31. The run started on a base three commits behind `origin/main`, one of them changing the supervisor (#1666). With the owner's approval the unpushed run was discarded, its stale pin record removed, and the approved spec and plan rebased unchanged onto `origin/main`; the run is `run-a394276c9fc55bff`.
- T1: the implementer wrote the refresh change before its tests; the red run was then reproduced by restoring the base `refresh.py` and schema against the new tests: 100 failed, 125 passed.
- T3: `test_captured_item_files_repair.py` and `test_intent_brief_registration_stop.py` assertions that captured entries stay after an apply are updated to the state `captured-entry-drop` leaves.
- T4: the work-loop, new-spec and agent sources changed without regenerating their projections, which the supervisor pins; the projections are regenerated before the PR.
- T5: the errata entry lives in a cited record the supervisor protects from workers, so T5's first attempt was reported as a failed gate (retry 1 of 5) and the controller committed the owner-approved entry between attempts.
- T5: projections for work-intake, workspace-status, new-spec and the reviewer agent were regenerated with `make build-self`, and the supervisor-pinned `.claude/skills/work-loop/` and `.agents/skills/work-loop/` were restored to their committed bytes; the two agent-projection inventory rows that no longer name the registry were removed.
