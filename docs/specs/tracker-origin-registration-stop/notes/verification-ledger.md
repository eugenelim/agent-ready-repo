# Verification ledger: tracker-origin work stops being registered

## Owner approvals of wording (AC-0020)

| Target | Wording | Approval |
| --- | --- | --- |
| `docs/rfc/0106-stop-registering-derivable-work.md` § Errata (AC-0019) | The 2026-10-30 entry on the tracker-origin registration stop, the `tracker-entry-drop` repair, and the per-entry refresh status not carried over | eugenelim (owner), 2026-10-30T07:45-05:00 |
| `docs/rfc/0083-work-intake-and-artifact-routing.md` § Errata (AC-0019) | The 2026-10-30 entry: a tracker-origin artifact's tracker profile lives on the artifact | eugenelim (owner), 2026-10-30T07:45-05:00 |
| `docs/product/briefs/workspace-registry-retirement-delivery.md` slice 9 and Spec map (AC-0023) | Slice 9 lands in parts around the execution-supervisor cutover, naming the work after it; the `tracker-origin-registration-stop` Spec map row | eugenelim (owner), 2026-10-30T07:45-05:00 |

## The repair on this repository (AC-0024)

Run 2026-10-30 on this branch at commit `ca2ed7903b652e98aa89d3ef36dc547c4d152850`:

```
python3 .claude/skills/workspace-status/scripts/workspace_status.py repair-plan --root .
```

Exit code: `0`. Output summary: `mode` `repair-plan`, `plan_id` `d649b013a568c953bd1577ee6a0f3473ab65a2c7cbf970ad47e28ae22c6178c1`, 0 automatic operations and 0 manual findings, so 0 `tracker-entry-drop` operations and 0 tracker-origin manual items. `workspace.toml` SHA-256 `1213450dbc24a77a77b524033e6c92b80c9cfcc29be9fd5da238e739c6a45603`. No `repair-apply` was run: there is nothing to apply.

## Build record

The run was driven by the execution supervisor (run `run-371f640377c41db1`) in a standalone clone, because another session's branch tracking in the shared `.git/config` tripped the supervisor's attempt check during T5; that one attempt was recovered by removing and restoring the other session's three-line section byte for byte, with the owner's approval.

- **Owner approvals during the build (2026-10-30, eugenelim):** the `## Terminal Intent` section before `start`; keeping the `build-check.yml` roster step and its `tools/lint-ci-parity.py` entry once open PR #1651 had merged; three controlled amendments (AC-0008 base-test rule, the `cooling-state-unavailable` matched-entry condition, the AC-0015 Archived-tree exception), each re-approved after a clean amendment review; a locator allowlist in place of a refusal list (T15); dropping `delivery/` from the pull request and squashing it into one commit with the `Engine-Change-RFC: 0106` trailer.
- **Implementation review:** eight rounds of adversarial, security and quality review, each finding adjudicated and recorded through the supervisor; round 8 came back clean from all three. Deferred Nit: none open.
- **Gate misreports, corrected:** after T8 and again after T17 the controller reported a passing gate while `make lint-ruff` had failed (a chained command hid the exit code). Both were caught: T8's by the next run, T17's by round-7 review (finding Q1), and fixed in T9 and T18. Final gates were read with each exit code on its own.
- **Final gates (HEAD of the run):** `make lint-ruff` and `make lint-mypy` exit 0; `packs/core/tests/skills/work-intake` 1065 passed; `packs/core/tests/pack` plus `tests/roster` 3589 passed, with the same 4 failures and 18 errors as `origin/main` (credbroker wheel build, `test_work_loop_root_validation.py`) and the two `test_core_pre_pr_hook.py` cases that read this run's local supervisor state, which the pull request does not carry; `tools/check-core-release.py` and `tools/changelog.py validate` pass.
