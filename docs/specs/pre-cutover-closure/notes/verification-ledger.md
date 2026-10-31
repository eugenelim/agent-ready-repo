# Verification ledger: pre-cutover-closure

## T1 — AC-0020: close-work tests compared with the base

2026-10-30. Throwaway `ast` comparison of every module-level function under `packs/core/tests/skills/close-work/` at the working tree against base `f9bbf6ea1`; a body counts as identical after removing `workspace_lookup=` and `_workspace_lookup=` keywords and the `workspace_lookup` parameter.

```text
files compared: 23
removed: ['test_ac0031_no_registration_when_lookup_returns_none', 'test_ac0031_workspace_registration_named_in_packet']
changed only by removed workspace_lookup keywords/parameter: ['test_closure_packet.py::_call_eligible', 'test_closure_packet.py::test_ac0038_a_missing_outcome_is_stated_not_omitted', 'test_closure_packet.py::test_ac0038_packet_carries_the_ancestors_stated_outcome', 'test_closure_packet.py::test_ac0039_an_unknown_denominator_is_said_not_guessed', 'test_closure_packet.py::test_ac0039_child_count_reports_resolved_against_declared', 'test_closure_packet.py::test_ac0040_a_declared_co_owner_does_carry_the_caveat', 'test_closure_packet.py::test_ac0040_no_co_owner_means_no_co_owner_caveat']
added: ['test_closure_packet.py::test_pre_cutover_ac0001_packet_fields_exclude_registration', 'test_closure_packet.py::test_pre_cutover_ac0002_check_signature_has_no_workspace_seam', 'test_closure_packet.py::test_pre_cutover_ac0003_module_text_names_no_registry']
RESULT: PASS
```

The six `test_ac0038_`, `test_ac0039_` and `test_ac0040_` functions call `_build_eligible_packet` directly; each differs only by its removed `workspace_lookup=None` keyword. Red before the source edit: the three `test_pre_cutover_` tests failed (field list held `workspace_registration`; signature held `_workspace_lookup`; module text held `workspace.toml`).

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-10-30 | eugenelim | `workspace-retirement` spec and plan amendment (AC-0029, its four rule lists, task T11), approved before the `Approved:` line note was added | `docs/specs/workspace-retirement/spec.md` | `2e36f4c4568c934d912a2846002aa36aeb9b3d2e85f536bffe02dcc6a3b7f767` |
| 2026-10-30 | eugenelim | `workspace-retirement` spec and plan amendment | `docs/specs/workspace-retirement/plan.md` | `769240e305b62c9faced0a2437a6ac493d081bb5ee8b916944bead0706fa5cfd` |
| 2026-10-30 | eugenelim | upgrade-notes draft wording | `docs/specs/pre-cutover-closure/notes/upgrade-notes.md` | `155fae191ecd34a0069a2dd11d6cafde960d88fd66f159195f8d2de2eb38d52c` |
| 2026-10-30 | eugenelim | § Compatibility closure entry | `docs/specs/workspace-retirement/retirement-record.md` | `6753959b21cdc9023d762d7b6b592d09abb5e5acc436c0754ec0b954d179d740` |
| 2026-10-30 | eugenelim | brief Spec map row and slice 9 item text | `docs/product/briefs/workspace-registry-retirement-delivery.md` | `cccbd1ebd3cbf07469bfef50f9f437e89633418416ab5d052f49de429ab096f8` |

## T3 — the owner rule

2026-10-30. Before the inventory rows moved, both real-repository tests in `tests/roster/test_workspace_retirement_inventory.py` failed with AC-0029 on exactly 19 rows, the rows slices 2 to 8 owned; every fixture test passed. After the move, 132 passed. `test_slice6_ac0005_removal_spec_is_a_slice_six_contract_row`, which pinned the `next-item-suggestions-removal` row to `contract` and owner `6`, is renamed `test_slice6_ac0005_removal_spec_is_a_historical_row` and asserts `historical` and `none`, the value AC-0008 requires.

## T4 — the draft's route

2026-10-30. The supervisor refuses any worker change under `docs/specs/pre-cutover-closure/`, so an implementer attempt cannot write the draft. T4's first attempt was reported as a failed gate (retry 1 of 5); the controller then wrote the draft, the owner approved its wording, and it was committed between attempts, the same route the ledger takes. T4's next attempt adds the roster checks and the draft's inventory row.

## T5 — the texts' route

2026-10-30. The owner's approvals live in this ledger, which no worker attempt may change, so T5's first attempt was reported as a failed gate (retry 2 of 5). The controller drafted the closure entry and the brief edits, the owner approved both, and they were committed with these rows between attempts. T5's next attempt adds the roster checks.
