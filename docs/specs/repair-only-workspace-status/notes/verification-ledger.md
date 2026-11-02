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
- T2: the implementer inverted `test_dispatch_outside_a_skills_directory`, a seventh test pinning the layout check the plan drops. The owner accepted it on 2026-11-02, to be carried by one batched controlled amendment of AC-0002's engine-pinning list before the final `run-gates`. The owner also chose to leave the readiness bridge's `wrong_schema` reading of `unmigrated_workspace` as a follow-on.

## T4 — the dispatch replay (AC-0007)

2026-11-02, base `ab4e4b71c` (its `packs/core/.apm/skills/` extracted with `git archive`) against the working tree after T3, both run as `python -I dispatch.py --root <tree>`, comparing standard output bytes and exit codes.

- Trees: 157 — the 156 distinct repositories the four dispatch suites plant (`test_dispatch.py`, `test_header_derived_dispatch_replay.py`, `test_work_intake_dispatch.py`, `test_dispatch_isolation.py`), captured by a throwaway pytest plugin that snapshots every root passed to `dispatch()` or `dispatch.py --root`, plus this repository.
- Not entry-free, so not replayed: 101 (a `workspace.toml` holding an entry, unparseable, or a link).
- Runs compared: 202 — an argless run of each of the 56 entry-free trees, and `--start` and `--resume` of every spec either listed in `ready`, `active` or `blocked`.
- Differing outputs: 0.
- T6 (owner decisions, 2026-11-02): `repair-plan --yes`, which at the base printed the retired `work-intake-migration-result.v1` refusal, now exits 2 with empty standard output; the owner chose to treat it as a migration form, to be added to the Migration forms term in the batched amendment. The owner approved deleting seven whole suites that pinned only retired subcommand output: `tests/roster/test_work_intake_migration_contracts.py`, `test_spec_retirement_candidates_contract.py`, `test_spec_retirement_candidates_cli.py`, `test_two_sided_prune_closure_invariant.py`, `test_selection_scoped_membership_absence.py`, `test_cooled_work_entry_classes.py`, and `packs/core/tests/skills/workspace-status/test_closeout_initiative_residue.py`.
- T6: the controller also re-pointed three roster pins T5 and T10 left red — `test_priority_field_never_read.py` (packaged readiness copy in place of the dropped engine copy), `test_work_intake_refresh_coordinator.py` (the `_intake_guard_callable` seam, scoped to `validate_normalized_intake`), and `test_last_registry_entries.py` (the brief's 9E annotation) — and removed the two CI steps for the deleted retirement-candidates suites.
- T6: the first two `report` calls were refused because the supervisor's fresh-index `git add -A` exceeded its 60-second timeout while a long gate run loaded the machine (about 28 seconds when idle). A ledger commit made while that attempt was still open caused `attempt-residue`; it was undone with a soft reset and recommitted after the attempt closed.
