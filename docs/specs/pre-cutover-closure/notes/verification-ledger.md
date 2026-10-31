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
