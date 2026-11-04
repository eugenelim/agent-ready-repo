# Verification ledger: registry-upgrade-notes

## Approvals

| Date | Approver | What | File | SHA-256 |
| --- | --- | --- | --- | --- |
| 2026-11-03 | eugenelim | spec, after the spec-stage security review | `docs/specs/registry-upgrade-notes/spec.md` | `9fd87850b451b92c6b2b00a7250a0d108dcd5918d0d465ed901f22be0d80dc51` |
| 2026-11-03 | eugenelim | plan | `docs/specs/registry-upgrade-notes/plan.md` | `9a081738284606afef4f7dc9cbcb208972268566db5818f12b65bcf329170d23` |
| 2026-11-03 | eugenelim | upgrade page wording | `guides/core/how-to/upgrade-from-a-workspace-registry.md` | `5bb41e4097f29bdeacc00ee005d8f2bcfdfa8aa9ce6822a69faa6b6059806566` |
| 2026-11-03 | eugenelim | § Compatibility closure bullet | `docs/specs/workspace-retirement/retirement-record.md` | `ed601b935c5d937f86c638601c3f3cbeaba5e915500a812fc2085a3c9dc5a494` |
| 2026-11-03 | eugenelim | brief Spec map row and after-cutover item | `docs/product/briefs/workspace-registry-retirement-delivery.md` | `5392b84d7cd7101f04ec6ff75614a3328872a0a2e8f1d1ed2552caddfa625b7c` |

## Owner decisions

- 2026-11-03: publish the upgrade notes as a new page and keep the `pre-cutover-closure` draft unchanged; delete `migrate-capture-work.md` and `workspace-toml-schema.md` and rewrite three guides; include the "rerun reconciliation" next-action strings; record the closure bullet under this spec's own criteria; ship every touched package at its next patch; add the `.workspace-prune-protected.toml` lines the new roster module needs; 9F owns the intent-rename absence handling (confirmed with the 9G session).
- 2026-11-03: the round-3 spec-mode repairs were accepted unreviewed.

## Run notes
- 2026-11-03, spec-approved gate: `project-knowledge --capture --producer-profile work-loop` refused with `map_mismatch` (not retryable); the owner chose to record it and continue. No fallback file was created.
- 2026-11-03, plan-locked gate (run run-31d6998f02a05a4d): the capture refused with the same map_mismatch; recorded under the same owner decision, with no fallback file.
- AC-0025 (T4): `git diff -U0 3b1d0279d -- packs/core/tests/skills/work-loop packs/core/tests/skills/navigate-intents packs/core/tests/skills/workspace-status packages/agentbundle/tests/test_workspace_mcp_*.py` changes 22 lines, each a next-action string moving from "rerun reconciliation" to "run `dispatch.py` again" or "run `repair-plan` again"; 0 other lines.
- AC-0022 (T11): `git diff --stat 3b1d0279d -- 'packs/core/tests/skills/work-intake/test_intent_rename_*.py'` shows no change to any base rename suite; the 45 absence cases are in the new `test_intent_rename_absent_registry.py` (36 red at the base, 45 green after).
- T5 pin moves: tests/roster/test_conventions_retirement.py::test_seeded_specs_readme_states_the_distinction_and_vocabulary needle 'lifecycle index' → 'carries its own state' (packs/core/seeds/docs/specs/README.md, sentence rewritten in T3); tests/roster/test_repo_governance_standalone_install.py AC11 providers [work-intake, workspace-status] → [work-intake] (packs/repo-governance/pack.toml); packs/core/tests/skills/work-intake/test_workspace_capture_wave4.py three tests re-pointed from the retired 'Terse workspace capture' section to 'Capture without a registry' (work-intake SKILL.md) and eval id 30's assertions; packs/core/tests/skills/work-loop/test_work_intake_dispatch.py 'not resumable through `workspace-status`' → '`dispatch.py`' (work-loop SKILL.md).
- T6 pin moves: tests/roster/test_decision_record_destination_contract.py::test_ac6_new_rfc_core_references_are_conditional_with_fallbacks new-rfc hand-off sentence drops `workspace-status` (repo-governance new-rfc SKILL.md); tests/roster/test_workspace_status_projection.py::test_t3_work_loop_step0_requires_canonical_preflight 'Raw `[work].queue` or `[work].active` membership never authorizes PLAN' → 'A registry entry never authorizes PLAN' (work-loop SKILL.md, T5); tests/fixtures/install_snapshot/core.paths.txt golden drops workspace.toml (seed removed in T3), regenerated with UPDATE_GOLDEN=1.
- Hash re-pins: tools/test_workspace_status.py _WORK_LOOP_CONTRACT_HASH (work-loop SKILL.md Step 0, T5 wording) e5a3f9e7… → a5f01881…; tests/roster/test_workspace_status_progressive_disclosure.py BACKEND_DIGESTS for workspace_status.py and workspace_status_engine.py (T4 next-action strings).
- T7 pin moves (deleted `guides/core/reference/workspace-toml-schema.md`, rewritten core guides): dropped as retired registry text — test_captured_item_files_instructions.py `_CLOSED_LIST` schema entry; test_captured_item_registration_stop.py `_AC11_FILES` schema entry; test_depends_on_headers_instructions.py `DEPENDS_ON_FILES` schema entry; test_graph_pointer_authoring.py schema classification entry; test_intent_brief_registration_stop.py schema `_ABSENT` entry; test_last_registry_entries.py schema in `_POLICY_FILES` and the stale-phrase map; test_spec_registration_stop.py schema `_PRESENT`/`_ABSENT` entries and `_RETIRED_CODE_FILES`; test_thirty_day_cooling_and_retirement.py schema pair; test_tracker_origin_registration_stop.py schema `_ABSENT`/`_PRESENT` entries, `_SCHEMA_GUIDE`, and `test_every_tracker_origin_example_sits_in_a_section_that_names_the_repair`; test_workspace_status_projection.py schema finding-table and receipt-block pins; test_cooling_scope_closure.py `test_ac27_reference_states_closeout_derivation` (pinned a retired registry sentence in work-intake-routing-and-lifecycle.md). Re-pointed — test_cooling_brief_child_scope_closure.py AC18/AC19 to workspace-status SKILL.md only, AC26 to close-and-disposition-work.md's cool-30-days row; test_wave4_durable_outputs_and_release.py `workspace-status` → `dispatch.py` for the lifecycle reference and closeout how-to (schema path and "live coordination" pin dropped); web/src/test/rendered-output.test.ts next action on start-or-remember-work `workspace-status` → `dispatch.py`; tools/test_workspace_status.py:274 docstring only.
- T9 pin moves: tests/roster/test_direct_light_documentation_boundary.py::test_workspace_dispatch_and_direct_light_have_distinct_durability 'creates no workspace entry' → 'creates no entry' (docs/architecture text).

## AC-0020 — the four test trees at the head and at the base

Head run taken 2026-11-04 at `b3f58fd77` (after T17, the last task that edits a test file); base run taken the same day at `3b1d0279d` (a detached worktree), with the same remote refs; both on the same machine (Darwin arm64, Python 3.11). Command, run in each root: `/tmp/run-trees.sh <root> <out>` — `python -m pytest tests/roster -n 6 -rfE`, `python -m pytest tools -n 6 --ignore=tools/catalogue -rfE`, `python -m pytest packs/<pack>/tests -n 4 -rfE` for each pack, and each `tools/test-*.py` run standalone; plus `npm test --prefix web` after `make site-build` at the head before T16 (T16 and T17 changed only version strings and one roster test): 24 files, 240 tests passed.

Head counts:
```text
COUNT roster: 7 failed, 3079 passed, 9 skipped, 8 warnings, 6 errors, 56 subtests passed in 216.06s (0:03:36)
COUNT tools: 13 failed, 1895 passed, 2 skipped, 70 subtests passed in 493.68s (0:08:13)
COUNT packs/agent-skill-engineering/tests: 267 passed in 5.40s
COUNT packs/architect/tests: 559 passed, 16 skipped, 72 subtests passed in 4.18s
COUNT packs/atlassian/tests: no tests ran in 1.06s
COUNT packs/catalogue-curation/tests: 193 passed in 3.42s
COUNT packs/code-intelligence/tests: 180 passed, 67 skipped in 1.32s
COUNT packs/converters/tests: no tests ran in 0.94s
COUNT packs/core/tests: 8860 passed, 750 skipped, 2 errors, 82 subtests passed in 494.17s (0:08:14)
COUNT packs/credential-brokers/tests: 31 passed, 4 skipped in 1.61s
COUNT packs/desk-research/tests: 98 passed, 6 errors in 1.04s
COUNT packs/experience-design/tests: 31 passed in 38.06s
COUNT packs/figma/tests: 13 passed in 3.70s
COUNT packs/frontend-engineering/tests: 458 passed in 1.45s
COUNT packs/github/tests: 222 passed in 1.83s
COUNT packs/linear/tests: 32 passed in 2.03s
COUNT packs/product-documentation/tests: 27 passed in 1.06s
COUNT packs/product-engineering/tests: 81 passed in 0.91s
COUNT packs/repo-governance/tests: 839 passed, 6 skipped, 2 errors in 15.40s
COUNT standalone: 56 scripts run
```

Base counts:
```text
COUNT roster: 14 failed, 3062 passed, 9 skipped, 8 warnings, 6 errors, 56 subtests passed in 149.04s (0:02:29)
COUNT tools: 14 failed, 1893 passed, 3 skipped, 70 subtests passed in 477.67s (0:07:57)
COUNT packs/agent-skill-engineering/tests: 267 passed in 6.22s
COUNT packs/architect/tests: 559 passed, 16 skipped, 72 subtests passed in 3.48s
COUNT packs/atlassian/tests: no tests ran in 0.89s
COUNT packs/catalogue-curation/tests: 193 passed in 3.62s
COUNT packs/code-intelligence/tests: 180 passed, 67 skipped in 1.47s
COUNT packs/converters/tests: no tests ran in 0.94s
COUNT packs/core/tests: 8815 passed, 750 skipped, 2 errors, 82 subtests passed in 373.90s (0:06:13)
COUNT packs/credential-brokers/tests: 31 passed, 4 skipped in 1.42s
COUNT packs/desk-research/tests: 98 passed, 6 errors in 0.76s
COUNT packs/experience-design/tests: 31 passed in 27.08s
COUNT packs/figma/tests: 13 passed in 1.32s
COUNT packs/frontend-engineering/tests: 458 passed in 0.90s
COUNT packs/github/tests: 222 passed in 0.77s
COUNT packs/linear/tests: 32 passed in 1.05s
COUNT packs/product-documentation/tests: 27 passed in 0.65s
COUNT packs/product-engineering/tests: 81 passed in 0.73s
COUNT packs/repo-governance/tests: 839 passed, 6 skipped, 2 errors in 11.05s
COUNT standalone: 56 scripts run
```

Failing at both the head and the base (34; the first excused set). `test_typed_ordinal_collision_equivalence.py::test_the_baseline_agrees_with_the_hand_authored_corpus` is among them: the allocator unions the remote view, and `origin/main` gained `CAP-0012` after the base.
```text
ERROR packs/core/tests/skills/work-loop/test_project_knowledge_handoff.py
ERROR packs/core/tests/skills/work-loop/test_review_shape_guidance.py
ERROR packs/desk-research/tests/skills/desk-research-project-check/test_project_knowledge_boundary.py
ERROR packs/desk-research/tests/skills/desk-research-project-digest/test_project_knowledge_boundary.py
ERROR packs/desk-research/tests/skills/desk-research-project-start/test_project_knowledge_boundary.py
ERROR packs/desk-research/tests/skills/desk-research-project-status/test_project_knowledge_boundary.py
ERROR packs/desk-research/tests/skills/desk-research-project-synthesize/test_project_knowledge_boundary.py
ERROR packs/desk-research/tests/skills/devils-advocate/test_project_knowledge_boundary.py
ERROR packs/repo-governance/tests/skills/new-rfc/test_next_ordinal.py
ERROR packs/repo-governance/tests/skills/new-rfc/test_project_knowledge_handoff.py
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestAgentbundleWheelInstall::test_both_packages_resolve_inside_venv_site_packages
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestAgentbundleWheelInstall::test_credbroker_070_installed_as_dependency
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestBuiltCliHttpsInstall::test_anonymous_install_exits_zero
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestBuiltCliHttpsInstall::test_netrc_install_sends_basic_auth_to_loopback
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestIsolatedInstall::test_credbroker_only_venv_resolves_public_surface
ERROR tests/roster/test_portable_catalogue_authentication_packaging.py::TestVersionPrecedence::test_installed_07_wins_over_floor_06
FAILED tests/roster/test_portable_catalogue_authentication_packaging.py::TestCredbrokerWheelVersion::test_wheel_version_agrees_with_pyproject_and_version_py
FAILED tests/roster/test_typed_ordinal_collision_equivalence.py::test_the_baseline_agrees_with_the_hand_authored_corpus
FAILED tools/test-all.py (standalone)
FAILED tools/test-check-atlassian-phase3-readiness.py (standalone)
FAILED tools/test-check-contract-drift.py (standalone)
FAILED tools/test_check_artifact_contents.py::test_real_sdist_carries_and_executes_complete_engine_suite
FAILED tools/test_managed_child.py::test_a_clean_reap_reports_nothing
FAILED tools/test_managed_child.py::test_a_non_reaped_disposition_is_reported_by_the_runner
FAILED tools/test_managed_child.py::test_a_real_childless_exit_is_reaped_with_nothing_mocked
FAILED tools/test_managed_child.py::test_an_already_reaped_child_refuses_rather_than_signalling
FAILED tools/test_managed_child.py::test_an_empty_owned_group_is_a_silent_success
FAILED tools/test_managed_child.py::test_missing_nonreaping_wait_reports_unavailable_without_a_group_send
FAILED tools/test_managed_child.py::test_normal_exit_reaps_a_real_grandchild
FAILED tools/test_managed_child.py::test_normal_exit_refuses_an_unowned_group_but_reaps_an_owned_one
FAILED tools/test_managed_child.py::test_permission_error_after_the_proof_is_success_without_escalation
FAILED tools/test_managed_child.py::test_reap_uses_the_queried_group_not_the_child_pid
FAILED tools/test_managed_child.py::test_unqueryable_group_is_inconclusive_without_a_send
FAILED tools/test_release_check.py::test_release_check_refuses_when_tag_missing
```

Failing at the head only (5): exactly the five `work-loop`-copy checks of the second excused set.
```text
FAILED tests/roster/test_agent_skill_engineering_consumer_integrations.py::test_ac11_work_loop_projections_are_byte_identical_to_the_source
FAILED tests/roster/test_cognitive_load_repository_contract.py::test_self_host_skill_projections_match_their_canonical_sources
FAILED tests/roster/test_repo_governance_archive_map.py::test_archive_carries_the_map_unchanged
FAILED tests/roster/test_t9a_conformance_rollup.py::TestProjectedCopiesByteIdentical::test_agents_projected_scripts_byte_identical_to_pack_source
FAILED tests/roster/test_t9a_conformance_rollup.py::TestProjectedCopiesByteIdentical::test_claude_projected_scripts_byte_identical_to_pack_source
```

Failing at the base only (13).

In files this change does not touch (13): failures of the base run alone, not fixes by this change. `tools/test_release_check.py` and `tools/test_import_time_path_leaks.py` are run-dependent: each passed at both the head and the base when run alone (5 passed each). The others were not traced further; AC-0020 excuses nothing on this list.
```text
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_are_members_or_exclusions[index]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_are_members_or_exclusions[lint]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_are_members_or_exclusions[package]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_are_members_or_exclusions[verify]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_resolve_under_bundled_data[index]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_resolve_under_bundled_data[lint]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_resolve_under_bundled_data[package]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_contract_reads_resolve_under_bundled_data[verify]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_each_command_reads_its_contracts[index]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_each_command_reads_its_contracts[lint]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_each_command_reads_its_contracts[package]
FAILED tests/roster/test_catalogue_spec_contract_loads.py::test_each_command_reads_its_contracts[verify]
FAILED tools/test_import_time_path_leaks.py::ImportTimePathLeakTest::test_no_collector_moves_a_packaged_source_tree_on_sys_path
```

## AC-0020 — test changes against the base

Command: `git diff -U0 3b1d0279d -- tests/roster web/src/test 'packs/*/tests/*' 'tools/test*'`, taken at head `b3f58fd77`. Result: 32 files differ, 1793 lines added, 146 removed. Two files are new (`tests/roster/test_registry_upgrade_notes.py`, `packs/core/tests/skills/work-intake/test_intent_rename_absent_registry.py`); no base test file was deleted. Outside these trees, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py` lost `test_workspace_toml_curated_content_preserved_on_reprojection` and its `workspace.toml` expected-pattern literal (T3, seed removed).

Files each changed pin reads:

| Changed test file | Files its changed pins read |
| --- | --- |
| `tests/roster/test_captured_item_files_instructions.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_captured_item_registration_stop.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_conventions_retirement.py` | `packs/core/seeds/docs/specs/README.md` |
| `tests/roster/test_cooling_brief_child_scope_closure.py` | `guides/core/reference/workspace-toml-schema.md` (deleted); `packs/core/.apm/skills/workspace-status/SKILL.md`; `guides/core/how-to/close-and-disposition-work.md` |
| `tests/roster/test_cooling_scope_closure.py` | `guides/core/reference/work-intake-routing-and-lifecycle.md` |
| `tests/roster/test_decision_record_destination_contract.py` | `packs/repo-governance/.apm/skills/new-rfc/SKILL.md` |
| `tests/roster/test_depends_on_headers_instructions.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_direct_light_documentation_boundary.py` | `docs/architecture/work-intake-and-artifact-routing.md` |
| `tests/roster/test_graph_pointer_authoring.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_intent_brief_registration_stop.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_last_registry_entries.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_repo_governance_standalone_install.py` | `packs/repo-governance/pack.toml` |
| `tests/roster/test_spec_registration_stop.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_thirty_day_cooling_and_retirement.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_tracker_origin_registration_stop.py` | `guides/core/reference/workspace-toml-schema.md` (deleted) |
| `tests/roster/test_wave4_durable_outputs_and_release.py` | `guides/core/reference/workspace-toml-schema.md` (deleted); `guides/core/reference/work-intake-routing-and-lifecycle.md`; `guides/core/how-to/close-and-disposition-work.md` |
| `tests/roster/test_workspace_status_progressive_disclosure.py` | `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`; `workspace_status_engine.py` |
| `tests/roster/test_workspace_status_projection.py` | `guides/core/reference/workspace-toml-schema.md` (deleted; its coordination-receipts pin re-pointed in T14 to `guides/core/reference/product-brief-fields.md`); `packs/core/.apm/skills/work-loop/SKILL.md` |
| `tools/test_workspace_status.py` | `packs/core/.apm/skills/work-loop/SKILL.md` (Step 0 hash); docstring only otherwise |
| `web/src/test/rendered-output.test.ts` | `guides/core/how-to/start-or-remember-work.md` |
| `packs/core/tests/skills/work-intake/test_workspace_capture_wave4.py` | `packs/core/.apm/skills/work-intake/SKILL.md`; `evals/evals.json` |
| `packs/core/tests/skills/work-loop/test_dispatch.py` and the three `fixtures/captured-projection/*.json` | `packs/core/.apm/skills/work-loop/scripts/_header_readiness.py` |
| `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py` | `packs/core/.apm/skills/work-loop/SKILL.md` |
| `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py` | `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` |
| `tests/roster/test_new_rfc_governance_surfaces.py` | `packs/repo-governance/pack.toml`, `.claude-plugin/plugin.json` (release version) |
| `tests/roster/test_okf_catalogue_discovery.py` | `packages/agentbundle/pyproject.toml`, `README-pypi.md`, `CHANGELOG.md` (release version) |
| `tests/roster/test_repo_governance_rename_completeness.py` | `packs/repo-governance/pack.toml`, `.claude-plugin/plugin.json` (release version) |
| `tests/fixtures/install_snapshot/core.paths.txt` (fixture, outside the four trees) | `packs/core/seeds/` (workspace.toml seed removed) |

Removed and changed lines:

```text
== packs/core/tests/skills/work-intake/test_intent_rename_absent_registry.py
== packs/core/tests/skills/work-intake/test_workspace_capture_wave4.py
-def test_workspace_entries_remain_terse_live_indexes() -> None:
-    assert "Terse workspace capture" in text
-    assert "canonical artifact first" in text
-    assert "one short present-tense summary" in text
-    assert "hard dependencies only" in text
-    assert "minimal provenance" in text
-    assert "`workspace.toml` is the pointer, not the overflow store" in text
-def test_follow_on_capture_materializes_owner_before_registration() -> None:
-    assert "materialize the follow-on's owning artifact before registration" in text
-    assert "Do not leave an open AC behind as the workspace anchor" in text
-    assert "one short current/next summary" in case["expected_output"]
-    assert "hard dependencies" in case["expected_output"]
== packs/core/tests/skills/work-loop/fixtures/captured-projection/mixed-empty-workspace.json
-        "next_action": "Restore readable repository state, then rerun reconciliation."
-        "next_action": "Fix the named field of that captured-item file, then rerun reconciliation.",
-        "next_action": "Restore readable repository state, then rerun reconciliation."
== packs/core/tests/skills/work-loop/fixtures/captured-projection/mixed-no-workspace.json
-        "next_action": "Restore readable repository state, then rerun reconciliation."
-        "next_action": "Fix the named field of that captured-item file, then rerun reconciliation.",
-        "next_action": "Restore readable repository state, then rerun reconciliation."
== packs/core/tests/skills/work-loop/fixtures/captured-projection/mixed-unmigrated-workspace.json
-        "next_action": "Restore readable repository state, then rerun reconciliation."
-        "next_action": "Fix the named field of that captured-item file, then rerun reconciliation.",
-        "next_action": "Restore readable repository state, then rerun reconciliation."
== packs/core/tests/skills/work-loop/test_dispatch.py
-_INVALID_WORKSPACE_NEXT_ACTION = "Correct workspace.toml, then rerun reconciliation."
== packs/core/tests/skills/work-loop/test_work_intake_dispatch.py
-        "A direct-light run is not resumable through `workspace-status`",
== packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py
-        "Correct the closed source-authority block, then rerun reconciliation."
== tests/roster/test_captured_item_files_instructions.py
-    "guides/core/reference/workspace-toml-schema.md",
== tests/roster/test_captured_item_registration_stop.py
-    "guides/core/reference/workspace-toml-schema.md",
== tests/roster/test_conventions_retirement.py
-    for needle in ("Implementing", "Shipped", "Executing", "lifecycle index"):
== tests/roster/test_cooling_brief_child_scope_closure.py
-SCHEMA_GUIDE = ROOT / "guides/core/reference/workspace-toml-schema.md"
-    """*AC18*: both homes carry a row for the code, with reason and action."""
-    for path in (SKILL_PATH, SCHEMA_GUIDE):
-    for path in (SKILL_PATH, SCHEMA_GUIDE):
-    """*AC26*: the `parent` row names what cooling does to an undeclared value."""
-    row = _table_row(SCHEMA_GUIDE.read_text(encoding="utf-8"), "`parent`")
-    assert "unestablished once the spec has cooled" in row
== tests/roster/test_cooling_scope_closure.py
-def test_ac27_reference_states_closeout_derivation() -> None:
-    """AC27: the reference guide states the closeout derivation."""
-    normalized = " ".join(
-        (
-            ROOT / "guides/core/reference/work-intake-routing-and-lifecycle.md"
-        ).read_text(encoding="utf-8").split()
-    )
-
-    assert (
-        "an entry named by a lifecycle record counts toward neither closeout consumer"
-        in normalized
-    )
-
-
== tests/roster/test_decision_record_destination_contract.py
-        "When core is installed, hand follow-on work to its `work-intake` / `workspace-status`",
== tests/roster/test_depends_on_headers_instructions.py
-    "guides/core/reference/workspace-toml-schema.md",
== tests/roster/test_direct_light_documentation_boundary.py
-        "An explicit direct-light request is session-local, creates no workspace "
== tests/roster/test_graph_pointer_authoring.py
-    "guides/core/reference/workspace-toml-schema.md": ("instruction", ""),
== tests/roster/test_intent_brief_registration_stop.py
-    "guides/core/reference/workspace-toml-schema.md": ("names no registered brief",),
== tests/roster/test_last_registry_entries.py
-    "guides/core/reference/workspace-toml-schema.md",
-    "guides/core/reference/workspace-toml-schema.md": "role policy outside initiative entries",
== tests/roster/test_new_rfc_governance_surfaces.py
-    """AC-0096: parsed pack.toml and plugin.json carry 2.5.1."""
-    assert pack["version"] == "2.5.1"
-    assert plugin["version"] == "2.5.1"
== tests/roster/test_okf_catalogue_discovery.py
-    expected = "0.60.0"
== tests/roster/test_registry_upgrade_notes.py
== tests/roster/test_repo_governance_rename_completeness.py
-    """AC-0001: parsed pack.toml and plugin.json name the pack and version 2.5.1."""
-        "2.5.1",
-    assert (plugin["name"], plugin["version"]) == (NEW_NAME, "2.5.1")
-    """AC-0003: the profile install into an empty repository exits 0 and records 2.5.1."""
-    assert {ps.installed_version for ps in rows.values()} == {"2.5.1"}
== tests/roster/test_repo_governance_standalone_install.py
-        "follow-on-queue-registration": ["skill:work-intake", "skill:workspace-status"],
== tests/roster/test_spec_registration_stop.py
-    "guides/core/reference/workspace-toml-schema.md": (
-        _COOLED_CHILD_ACTION,
-        "tracker-origin",
-        "spec-entry-drop",
-    ),
-    "guides/core/reference/workspace-toml-schema.md": (
-        "Register or reconcile the canonical entry explicitly",
-    ),
-_RETIRED_CODE_FILES = ("guides/core/reference/workspace-toml-schema.md",)
-    files = [_REPO / rel for rel in _RETIRED_CODE_FILES]
== tests/roster/test_thirty_day_cooling_and_retirement.py
-        (
-            "guides/core/reference/workspace-toml-schema.md",
-            "workspace.toml may point at cooling state and never owns it",
-            "gains no receipt or cooling schema in Wave 4",
-        ),
== tests/roster/test_tracker_origin_registration_stop.py
-_SCHEMA_GUIDE = "guides/core/reference/workspace-toml-schema.md"
-    _SCHEMA_GUIDE: (
-        "tracker-origin intent and brief entries stay",
-        "A tracker-origin spec keeps its entry",
-        "For a tracker-origin brief entry",
-        "tracker-origin entry moves to the matching collection",
-    ),
-    _SCHEMA_GUIDE: ("tracker-entry-drop",),
-def test_every_tracker_origin_example_sits_in_a_section_that_names_the_repair() -> None:
-    text = (_REPO / _SCHEMA_GUIDE).read_text(encoding="utf-8")
-    seen = 0
-    for _head, lines in _sections(text):
-        if any('mode = "tracker-origin"' in line for line in lines):
-            seen += 1
-            assert "tracker-entry-drop" in "\n".join(lines), lines[:3]
-    assert seen > 0
-
-
== tests/roster/test_wave4_durable_outputs_and_release.py
-        "guides/core/reference/workspace-toml-schema.md",
-    workspace = _read("guides/core/reference/workspace-toml-schema.md")
-        assert "workspace-status" in text
-    assert "live coordination, not the artifact-retention unit" in workspace
== tests/roster/test_workspace_status_progressive_disclosure.py
-        "e23226e8f8aa43f6806b5caa76c9314f81756188c83cc33ab16db993fbe47e27",
-        "bc884d0a2d08cdcc83547329a1b2f39b0d803614daea83d3f3a599524f6f0304",
== tests/roster/test_workspace_status_projection.py
-    assert "Raw `[work].queue` or `[work].active` membership never authorizes PLAN" in normalized
-    reference = (
-        REPO_ROOT / "guides" / "core" / "reference" / "workspace-toml-schema.md"
-    ).read_text(encoding="utf-8")
-    for text in (skill, reference):
-        documented_findings = _documented_finding_rows(text)
-        assert set(documented_findings) >= finding_codes
-        for code in finding_codes:
-            reason, action = documented_findings[code]
-            assert reason
-            assert action
-    # The receipt contract travelled with the reconcile depth it belongs to
-    # when the skill became a dispatcher: authoring a receipt and recovering
-    # from a bad one is remediation an agent reaches only after reconciliation
-    # reports the code, so it loads with that mode rather than on every
-    # orientation. The findings table above stays in SKILL.md and is still
-    # asserted there; only this half follows the prose.
-    for text in (reference,):
-        assert "```toml coordination-receipts" in text
-        assert "invalid_receipt" in text
-        assert "refresh_conflict = false" in text
-        receipt_blocks = re.findall(
-            r"```toml coordination-receipts\n(.*?)\n```",
-            text,
-            flags=re.DOTALL,
-        )
-        assert receipt_blocks
-        parsed_receipts = [
-            receipt
-            for block in receipt_blocks
-            for receipt in tomllib.loads(block)["coordination_receipts"]
-        ]
-        assert any(
-            set(receipt) == engine._COORDINATION_RECEIPT_FIELDS
-            and receipt["accepted_revision"] == "remote-rev-9"
-            for receipt in parsed_receipts
-        )
-        for receipt in parsed_receipts:
-            assert set(receipt).issubset(engine._COORDINATION_RECEIPT_FIELDS)
== tools/test_workspace_status.py
-    """workspace-toml-schema.md §needs: work:<path> resolves to [work].shipped only.
-    "e5a3f9e7a7f07a1ab2083603587edd27580a6dbaafeb859ffb3af0eb0b3f7bca"
== web/src/test/rendered-output.test.ts
-    const nextAction = position('workspace-status');
```

- 2026-11-04, amendment at run-gates: spec and plan re-approved by eugenelim at SHA-256 `6a714dd0bd114184d65e0c93e11c30f8f4b13fd77507e0a85d8dd91877c724a0` (spec) and `537f71451e5255e7ae33cfbbfce812b4d4af699ae12f43b5d810375199b6973b` (plan), before the status edits.
- 2026-11-04: `origin/main` shipped `core` 4.0.11 (#1681) and 4.0.12 (#1684) during the run; T15 moved `core` to 4.0.13, and `tools/check-core-release.py --base origin/main` reports the release consistent. The branch is rebased onto `origin/main` after the run ends.
- 2026-11-04: `origin/main` then shipped `core` 4.0.13 and `experience-design` 4.2.1 (#1685); T16 moved them to 4.0.14 and 4.2.2.
- 2026-11-04: run run-31d6998f02a05a4d reached terminal; `work-supervisor.py status --check` exited 0 with all 25 criteria supported and the adversarial, security and quality-engineer obligations satisfied clean. The supervisor's `regenerate` step rebuilt the installed `work-loop` copies in-run, and the five AC-0020 work-loop-copy tests and `catalogue self-host --check` passed after it.
