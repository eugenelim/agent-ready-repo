# Verification ledger: last-registry-entries

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-10-31 | eugenelim | RFC-0106 errata entry of 2026-10-31, before the run | `docs/rfc/0106-stop-registering-derivable-work.md` | `c24afbde4576cb815648e69f89a210c9461a2a5caff22aaeb183edfa8a41304a` |
| 2026-10-31 | eugenelim | brief Spec map row and after-cutover slug annotations | `docs/product/briefs/workspace-registry-retirement-delivery.md` | `2c4e141ec8c3f3e34367a8fdfc0fb2da5401acdefecba99b6177adb77acc20a8` |
| 2026-10-31 | eugenelim | six-row QA matrix copied into the captured item | `docs/product/captured/credential-broker-contract-manual-qa.md` | `d10ad4fae925ef1d1a00e8dc89defee7b2e588037704f2317e045fd052fee247` |
| 2026-10-31 | eugenelim | the repair plan applied to this repository | `.workspace-repair-plan.json` (gitignored; copy in the run notes below) | `ce89dc5880e675266953318ac10ba36add0ca65293d38c0b3bb4d3f3b38c47ca` |
| 2026-10-31 | eugenelim | § Compatibility closure entry | `docs/specs/workspace-retirement/retirement-record.md` | `8f2f27af4defde7d669f3e3ba2ae1c2ab8297f73c0182a61c68cabdc3fe6d50c` |

## Run notes

- 2026-10-31. The run started on a base three commits behind `origin/main`, one of them changing the supervisor (#1666). With the owner's approval the unpushed run was discarded, its stale pin record removed, and the approved spec and plan rebased unchanged onto `origin/main`; the run is `run-a394276c9fc55bff`.
- T1: the implementer wrote the refresh change before its tests; the red run was then reproduced by restoring the base `refresh.py` and schema against the new tests: 100 failed, 125 passed.
- T3: `test_captured_item_files_repair.py` and `test_intent_brief_registration_stop.py` assertions that captured entries stay after an apply are updated to the state `captured-entry-drop` leaves.
- T4: the work-loop, new-spec and agent sources changed without regenerating their projections, which the supervisor pins; the projections are regenerated before the PR.
- T5: the errata entry lives in a cited record the supervisor protects from workers, so T5's first attempt was reported as a failed gate (retry 1 of 5) and the controller committed the owner-approved entry between attempts.
- T5: projections for work-intake, workspace-status, new-spec and the reviewer agent were regenerated with `make build-self`, and the supervisor-pinned `.claude/skills/work-loop/` and `.agents/skills/work-loop/` were restored to their committed bytes; the two agent-projection inventory rows that no longer name the registry were removed.

## T6 — the run on this repository (AC-0011)

2026-10-31, `workspace-status` `repair-plan` then `repair-apply --yes` from the pack source, plan SHA-256 `ce89dc5880e675266953318ac10ba36add0ca65293d38c0b3bb4d3f3b38c47ca` confirmed by eugenelim.

- Planned operations: {'captured-entry-drop': 71, 'needs-to-header': 3}; `refresh-policy-move`: 0 (this repository has no `[authorization]` table); manual items: 1 (`record-differs` for `credential-broker-contract-manual-qa`, raised by the owner-approved matrix copy; its entry dropped in the same plan).
- Apply: `applied` True, `operations_applied` 74, refused 0.
- `dispatch.py` before and after: `ready`, `active`, `blocked` and `decision` identical ({'ready': True, 'active': True, 'blocked': True, 'decision': True}); `findings` 70 → 47, the removed legacy and captured entries' own findings.
- The next `repair-plan` holds no operation and no manual item.
- The first run (2026-10-31, plan `ae006455…`) applied 68 of 71 drops; three slug-only entries with legacy string `needs` were refused with `entry_has_needs`. That run's `workspace.toml` change was discarded, the contract was amended (AC-0022, task T9), and the plan above re-ran from the committed registry.
- A concurrent session's branch deletion changed the shared `.git/config` during T6's first attempt; the owner restored the exact pre-attempt bytes (SHA-256 `ef0a45e6…`) so the attempt could be reported, then restored the current config.
- The `PINNED` comment above the removed credential-broker entry was removed in a separate edit; `tests/roster/test_credential_broker_contract_docs.py` no longer names the registry, so its inventory row was removed.
- T7: the closure entry's approval lives in this ledger, which no worker attempt may change, so T7's first attempt was reported as a failed gate (retry 3 of 5) and the controller committed the owner-approved entry and its row between attempts.
