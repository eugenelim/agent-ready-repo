# Verification ledger: repair-only-workspace-status

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-11-02 | eugenelim | spec, at `63ed6819e` | `docs/specs/repair-only-workspace-status/spec.md` | `00feb77618d02fb9e344ba0be72ecbdef1e8943e94928c5e7fff338f110c9d8b` |
| 2026-11-02 | eugenelim | plan, at `63ed6819e` | `docs/specs/repair-only-workspace-status/plan.md` | `ba1d914af95098b7fa5d46b0c26729d1dc287696e9bf829b0c5764de7f01b6ae` |
| 2026-11-02 | eugenelim | agreement, as owner of the readiness hand-over, to re-point `navigate-intents`'s finding table and its parity tests to `work-loop`'s table | — | — |
| 2026-11-02 | eugenelim | RFC-0106 errata entry of 2026-11-02, before T6's deletions | `docs/rfc/0106-stop-registering-derivable-work.md` | `dcf5870f76ead4fcb0a962143365a022bf81753172969dbe975566b198828088` |
| 2026-11-02 | eugenelim | RFC-0083 pointer erratum of 2026-11-02 | `docs/rfc/0083-work-intake-and-artifact-routing.md` | `183fc3213c9b4ca6e41468d79dc1423f5d2f3ea805cc5a74aa60b3eae52476e2` |
| 2026-11-02 | eugenelim | brief non-goal widening, after-cutover annotations and Spec map row | `docs/product/briefs/workspace-registry-retirement-delivery.md` | `e0421a04ca7c441afc99af18721f3b8b462b079ce10ee2a2199be2851d67915b` |

## Run notes
- 2026-11-02, spec-approved gate: `project-knowledge --capture --producer-profile work-loop` refused with `map_mismatch` (not retryable); the owner chose to record it and continue. No fallback file was created.
- 2026-11-02, plan-locked gate (run `run-33b41daae1a10319`): the capture refused with the same `map_mismatch`; recorded under the same owner decision, with no fallback file.
- T10: the errata and brief texts sit in records the supervisor protects from workers, so T10's first attempt was reported as a failed gate (retry 1) and the controller committed the owner-approved texts between attempts.
