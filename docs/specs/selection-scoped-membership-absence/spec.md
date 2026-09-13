# Spec: Selection-scoped membership absence

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0112](../../adr/0112-prune-success-requires-a-two-sided-post-mutation-invariant.md), [RFC-0096](../../rfc/0096-portable-delivery-artifact-lifecycle.md) 2026-09-13 Errata
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them when
> a finding is adjudicated is the reviewing surface's.

## Objective

`workspace-status` accepts an explicit, non-empty selection of spec directories
and reports, for each selected spec, whether any `workspace.toml` membership
resolves to its canonical artifact identity. Resolution includes canonical,
duplicate, and supported legacy-alias memberships without widening the default
reconciliation population. ADR-0112's later prune operation composes this
read-only result when proving that memberships for selected artifacts are
absent; this slice does not implement prune mutation, closure observation, or
exit gating. RFC-0096's 2026-09-13 Errata uses the same mechanical check to
re-verify the entry-less status of each selected Wave 7d candidate before any
separate reference check or deletion proceeds.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User and maintainer promise | The additive read-only capability must be discoverable and its selection and output contract must remain current. | `packs/core/.apm/skills/workspace-status/SKILL.md` | workspace-status maintainers | Focused roster tests and an end-to-end invocation of the projected command | The documented invocation, scope, result fields, and read-only limit match the shipped behavior. |
| Release history | The core pack gains a consumer-visible capability. | `docs/product/changelog.md` | core pack maintainer | A core-led release entry with a `Highlights` disposition | The release entry names the selected membership check and the matching core version. |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Require the caller to supply at least one spec directory and evaluate only the supplied selection.
- Resolve every accepted membership form to one canonical repository-relative spec artifact identity before comparing it with the selection.
- Preserve every matching membership occurrence, including duplicates, with enough repository-relative provenance to distinguish its collection and position.
- Treat loaded TOML and selector text as instruction-inert data, keep reads confined to the repository, and emit deterministic UTF-8 JSON.
- Reuse the canonical `workspace-status` engine and its established canonical and legacy parsing rules.

### Ask first

- Add or remove an accepted membership or legacy-alias shape.
- Change the public result fields, valid selector grammar, or valid-input exit behavior after approval.
- Change how malformed selected-target entries affect a presence or absence result.
- Add any dependency or create a new engine, skill, schema, or module boundary.

### Never do

- Delete, remove, rewrite, or otherwise mutate an artifact, membership, `workspace.toml`, or any other repository file.
- Implement a closure-observation protocol, lock, digest or generation baseline, observation interval, or ABA handling.
- Gate a prune's exit or claim that this read-only observation proves post-mutation closure.
- Change default reconciliation behavior or widen the global forward scan's own Approved-or-Implementing domain.
- Select which specs should be deleted or perform a reference-free check outside membership identity resolution.
- Read or edit the generated `.agents/skills/workspace-status/` projection as the implementation source.

## Testing Strategy

- **Selection and identity resolution (AC-0001, AC-0002, AC-0003, AC-0004, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0014, AC-0029, AC-0030):** TDD in `tests/roster/test_selection_scoped_membership_absence.py`, using table-driven repository fixtures because canonical, duplicate, legacy-alias, rejected nested, and non-matching identities have deterministic outcomes.
- **Presence and absence reporting (AC-0015, AC-0016, AC-0017, AC-0018, AC-0020):** TDD in the same roster module, using fixtures that contain both selected members and selected non-members so the absence predicate cannot pass vacuously.
- **Scope and compatibility (AC-0005, AC-0019, AC-0023, AC-0024):** goal-based integration checks compare the existing `status`, `reconcile`, and `explain` outputs before and after the additive command against frozen fixtures; this proves the new route does not alter their default populations or projections.
- **Read-only and confinement behavior (AC-0021, AC-0022, AC-0025, AC-0026, AC-0027):** TDD snapshots fixture bytes before and after valid, invalid, present, and absent runs, and exercises unsafe or symlink-escaped selectors without allowing a repository write.
- **Pack delivery (AC-0028):** goal-based checks exercise the self-hosted projection, the workspace-status eval cases, the matched pack/plugin version, and the core-led changelog entry.

## Acceptance Criteria

- [ ] **AC-0001.** The CLI recognizes the selected-membership route. An empty supplied selection is rejected before analysis with that route's structured `empty_selection` response, which is distinguishable from the `unknown_subcommand` response, and cannot produce an all-clear or an empty success result. Construction test: `test_empty_selection_is_rejected_by_recognized_route`; fixtures: `empty_selection` and `unknown_subcommand`.
- [ ] **AC-0002.** Each accepted selector is a repository-relative directory of the form `docs/specs/<slug>`; absolute, drive-qualified, backslash-based, dot-segment, file-shaped, nested, and symlink-escaped selectors are rejected. The same CLI invocation path must accept the valid `docs/specs/<slug>` selector whose artifact is absent in AC-0003, so a reject-all implementation fails. Construction test: `test_selector_grammar_and_confinement_with_valid_absent_artifact_control`; fixtures: `invalid_selectors` and `selected_artifact_absent`.
- [ ] **AC-0003.** A valid selected identity can be evaluated when its spec directory or `spec.md` is absent, because membership identity does not depend on artifact existence. Construction test: `test_missing_selected_artifact_still_has_membership_result`; fixture: `selected_artifact_absent`.
- [ ] **AC-0004.** Entries resolving only to unselected specs do not change any selected spec's result; `selected_and_unselected_memberships` contains a known-present selected sentinel that remains present with exactly one retained occurrence. Construction test: `test_unselected_memberships_are_out_of_scope`; fixture: `selected_and_unselected_memberships`.
- [ ] **AC-0005.** Adding a selected-membership check leaves the default `status`, `reconcile`, and `explain` results byte-identical for the same frozen repository fixture. Construction test: `test_existing_subcommands_are_unchanged`; fixture: `default_command_compatibility`.
- [ ] **AC-0006.** A canonical `kind = "spec"` entry whose `path` is `docs/specs/<slug>/spec.md` makes the matching selected spec present. Construction test: `test_canonical_membership_is_present`; fixture: `canonical_membership`.
- [ ] **AC-0007.** A supported legacy work-list string `spec/<slug>` makes the matching selected spec present through the same canonical identity in each of `work.queue`, `work.active`, and `work.shipped`. Construction test: `test_legacy_work_alias_is_present_in_all_work_collections`; fixture: `legacy_work_collection_matrix`.
- [ ] **AC-0008.** A supported legacy `[backlog].open` object makes the matching selected spec present through the same canonical identity only when its fields are exactly `slug`, `source`, `summary`, `needs`, and `type`, with `type = "spec"`. Construction test: `test_exact_legacy_backlog_spec_object_is_present`; fixture: `legacy_backlog_membership`.
- [ ] **AC-0009.** A slug-shaped legacy shaping entry resolves to its shaping kind, not a spec identity, and cannot make an equally named selected spec present; `legacy_shaping_membership` also contains a known-present selected spec with exactly one retained canonical occurrence, while the equally named spec has zero occurrences. Construction test: `test_non_spec_legacy_slug_is_not_a_spec_membership`; fixture: `legacy_shaping_membership`.
- [ ] **AC-0010.** Two canonical occurrences resolving to one selected spec produce one present result that retains both occurrences. Construction test: `test_canonical_duplicate_occurrences_are_retained`; fixture: `duplicate_canonical_membership`.
- [ ] **AC-0011.** One canonical occurrence and one supported legacy alias resolving to one selected spec produce one present result that retains both occurrence forms. Construction test: `test_mixed_canonical_legacy_duplicates_are_retained`; fixture: `duplicate_mixed_membership`.
- [ ] **AC-0012.** Identity matching is exact: case changes, prefix matches, suffix matches, and sibling slugs do not resolve to the selected spec; `near_match_memberships` contains one exact positive match with exactly one retained occurrence alongside those near misses. Construction test: `test_membership_identity_matching_is_exact`; fixture: `near_match_memberships`.
- [ ] **AC-0014.** Matching canonical `kind = "spec"` occurrences are detected in exactly the four accepted canonical spec collections: top-level `backlog.open` and initiative-scoped `work.queue`, `work.active`, and `work.shipped`; each retained occurrence reports its collection. Construction test: `test_four_canonical_spec_collections_participate`; fixture: `canonical_collection_matrix`.
- [ ] **AC-0015.** Every supplied selector produces exactly one result in supplied order, including a fixture containing at least one present and at least one absent selected spec. Construction test: `test_one_ordered_result_per_selected_spec`; fixture: `mixed_presence_selection`.
- [ ] **AC-0016.** A selected spec reports `membership_present = true` exactly when its retained occurrence list is non-empty; `mixed_presence_selection` contains one selected result with exactly one occurrence and one selected result with exactly zero occurrences. Construction test: `test_presence_is_equivalent_to_nonempty_occurrences`; fixture: `mixed_presence_selection`.
- [ ] **AC-0017.** A selected spec reports `membership_present = false` exactly when no accepted canonical, supported legacy-alias, or selected-target parse-blocked occurrence resolves to it; `absence_occurrence_class_matrix` contains one canonical-positive result, one legacy-positive result, and one parse-blocked-positive result with exactly one occurrence each, plus one absent result with exactly zero occurrences. Construction test: `test_absence_requires_zero_resolved_occurrences`; fixture: `absence_occurrence_class_matrix`.
- [ ] **AC-0018.** Each result identifies the selected directory and canonical `spec.md` path, and each matching occurrence identifies its initiative when present, lifecycle collection, zero-based entry position, and canonical or legacy form without an absolute path; `occurrence_provenance_matrix` contains both top-level and initiative-scoped occurrences in both canonical and legacy forms. Construction test: `test_result_and_occurrence_provenance_is_complete_and_repository_relative`; fixture: `occurrence_provenance_matrix`.
- [ ] **AC-0019.** Reordering unrelated entries or changing comments and summaries leaves selected identities, presence booleans, and occurrence counts unchanged; each `identity_preserving_variants` case contains one selected result with exactly one occurrence and one with exactly zero occurrences. Construction test: `test_non_identity_edits_do_not_change_results`; fixture: `identity_preserving_variants`.
- [ ] **AC-0020.** Two clean runs over identical selector order and workspace bytes emit byte-identical JSON, including one selected result with exactly one occurrence and one selected result with exactly zero occurrences. Construction test: `test_selected_membership_output_is_deterministic`; fixture: `deterministic_output`.
- [ ] **AC-0021.** Malformed TOML and a syntactically valid workspace containing an invalid lifecycle collection produce distinguishable structured failures and neither emits an absent result for any selected spec. Construction test: `test_invalid_workspace_failure_classes_never_report_absence`; fixture: `invalid_workspace` with `malformed_toml` and `invalid_lifecycle_collection` cases.
- [ ] **AC-0022.** A target-like entry with a safe canonical path matching a selected spec but invalid non-identity fields is retained as a parse-blocked occurrence and cannot yield absence. Construction test: `test_matching_parse_blocked_entry_prevents_absence`; fixture: `parse_blocked_selected_membership`.
- [ ] **AC-0023.** An invalid target-like entry for an unselected spec does not prevent valid results for the supplied selection; `unselected_parse_blocked_membership` contains a valid selected membership that remains present with exactly one retained occurrence. Construction test: `test_unselected_parse_failure_does_not_widen_scope`; fixture: `unselected_parse_blocked_membership`.
- [ ] **AC-0024.** For valid input, the read-only command exits successfully whether selected results are present, absent, or mixed; each run returns exactly one result per supplied selector with the selected directory, canonical artifact path, `membership_present`, and occurrence-list fields, and it does not translate membership presence into prune exit gating. Construction test: `test_valid_results_have_shape_without_gating_exit`; fixture: `present_absent_and_mixed_runs`.
- [ ] **AC-0025.** Invalid selector or workspace input produces the command's structured error shape on stdout, a concise UTF-8 diagnostic on stderr, no traceback, no absolute root, and no loaded instruction text. Construction test: `test_invalid_input_error_is_safe`; fixture: `unsafe_and_instruction_like_input`.
- [ ] **AC-0026.** Valid and invalid runs leave `workspace.toml`, every selected spec path that exists, and every other file in the fixture byte-identical. Construction test: `test_membership_check_performs_no_writes`; fixture: `read_only_snapshot`.
- [ ] **AC-0027.** The source CLI configures stdout and stderr as UTF-8 before any selected-membership result or diagnostic is emitted, including non-ASCII fixture text. Construction test: `test_membership_check_emits_utf8`; fixture: `non_ascii_workspace`.
- [ ] **AC-0028.** The workspace-status eval harness contains a triggering query and a behavior case that exercise an explicit non-empty selection with both a present and an absent result. Construction test: `test_eval_harness_covers_selected_membership_check`; fixture: `workspace_status_eval_contract`.
- [ ] **AC-0029.** A nested selector of the form `docs/specs/<group>/<slug>` is rejected by the selector grammar and cannot be treated as a canonical spec identity. Construction test: `test_nested_selector_is_rejected`; fixture: `nested_selector`.
- [ ] **AC-0030.** Two surviving supported legacy occurrences that resolve to one selected spec produce one present result that retains both legacy occurrences. Construction test: `test_legacy_duplicate_occurrences_are_retained`; fixture: `duplicate_legacy_membership`.

## Retired identifiers

- AC-0013
  - Retired because the engine's canonical artifact identity accepts only a single-segment spec slug, so the former nested-selector promise was unrepresentable and contradicted AC-0002.

## Follow-ons

- eugenelim: ADR-0112 Wave 7c Slice 2 — compose this read-only result with prune mutation, coherent closure observation, participating-mutator rules, baselines, ABA handling, and exit gating.
- eugenelim: RFC-0096 Wave 7d execution — combine this membership check with the separately required reference-free mechanical check before selecting or deleting a carved-out spec.
- workspace-status owner decision: exactly one nested spec exists, `docs/specs/platform-site/self-hosted-fonts/`; it is Shipped and appears in no workspace membership. The canonical path validator cannot represent it, so it is structurally unregisterable; decide its supported identity or disposition in separate work.

## Assumptions

- Technical: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` is the editable engine source, and `.agents/skills/workspace-status/scripts/workspace_status_engine.py` is its generated projection (source: `packs/AGENTS.md` § Self-hosting projection; byte comparison confirmed 2026-09-13).
- Technical: canonical and supported legacy membership parsing already converge through `parse_workspace_entry`, `parse_legacy_workspace_entry`, and `_legacy_canonical_alias` (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, confirmed 2026-09-13).
- Technical: the engine remains standard-library-only for this read path; `tomlkit == 0.15.1` is reserved for `repair-apply` (source: `packs/core/AGENTS.md` § Skill dependencies, confirmed 2026-09-13).
- Technical: focused tests belong in `tests/roster/` so both `make test` and the post-build CI route collect them (source: `Makefile` targets `test-unleased` and `test-after-build-check-unleased`, confirmed 2026-09-13).
- Product: ADR-0112 Slice 2 and RFC-0096's Wave 7d pre-deletion verification are the two consumers, while deletion and closure remain outside this slice (source: user confirmation 2026-09-13).
- Process: this artifact remains a Draft spec with a Drafting plan and does not advance the active work-loop (source: user confirmation 2026-09-13).
