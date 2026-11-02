# Verification ledger: repair-only-workspace-status

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-11-02 | eugenelim | spec, at `63ed6819e` | `docs/specs/repair-only-workspace-status/spec.md` | `00feb77618d02fb9e344ba0be72ecbdef1e8943e94928c5e7fff338f110c9d8b` |
| 2026-11-02 | eugenelim | plan, at `63ed6819e` | `docs/specs/repair-only-workspace-status/plan.md` | `ba1d914af95098b7fa5d46b0c26729d1dc287696e9bf829b0c5764de7f01b6ae` |
| 2026-11-02 | eugenelim | agreement, as owner of the readiness hand-over, to re-point `navigate-intents`'s finding table and its parity tests to `work-loop`'s table | — | — |

## Run notes
- 2026-11-02, spec-approved gate: `project-knowledge --capture --producer-profile work-loop` refused with `map_mismatch` (not retryable); the owner chose to record it and continue. No fallback file was created.
- 2026-11-02, plan-locked gate (run `run-33b41daae1a10319`): the capture refused with the same `map_mismatch`; recorded under the same owner decision, with no fallback file.
