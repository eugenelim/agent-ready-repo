# Verification ledger: Intent preamble closure declarations

## 2026-09-25 — T1 comment visibility

- `make lint-ruff lint-mypy` passed.
- `python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-intake/test_intent_shape.py -q` passed: 252 tests in 0.85 seconds.
- `git diff --check` passed.
- T1 was implemented by the scheduled implementer and its dispatch receipt was recorded for wave 0.

## 2026-09-25 — T2 plan dependency error

The approved T2 completion condition requires the expanded field-reference
parity suite to pass. That suite reads
`guides/product-engineering/reference/intent-fields-and-modes.md`, but the
approved plan assigns that file to T4, which depends on T2 and T3. No valid
execution order can make the T2 gate green under those ownership boundaries.

The owner authorized reopening the plan on 2026-09-25. The amendment moves the
two field-reference row changes into T2 and leaves the remaining authoring
surfaces in T4. The accepted behavior, acceptance criteria, and non-goals do not
change.

## 2026-09-25 — T2 shared value rules

- `make lint-ruff lint-mypy` passed.
- `python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-intake/test_intent_shape.py -q` passed: 265 tests in 0.69 seconds.
- `python3 -m pytest -p no:cacheprovider tests/roster/test_intent_field_reference_parity.py -q` passed: 10 tests in 0.43 seconds.
- T2 was implemented by the scheduled implementer and its dispatch receipt was recorded for amended wave 0.

## 2026-09-25 — T3 peer resolution

- `make lint-ruff lint-mypy` passed.
- The first affected-suite run deselected the four new command cases and
  produced 13 passes plus 51 cleanup errors. Every error was a denied
  `TemporaryDirectory` removal after its test body, and the 51 node ids are
  exactly the cleanup-sensitive nodes already present at `HEAD`.
- Per the managed-profile rule, those cases were not retried. The unaffected
  suite passed: 13 tests, 55 exact node-id deselections, 4.54 seconds.
- T3 was implemented by the scheduled implementer and its dispatch receipt was
  recorded for amended wave 1. The command-level cases remain for CI or a
  supported profile.

The exact pre-existing `HEAD` deselections were:

```text
test_noop_empty
test_noop_specs_contracts_packages_only
test_degrades_malformed_sidecar
test_sidecar_converged
test_sidecar_orphan_and_strict
test_sidecar_dangling_endpoint
test_sidecar_cycle
test_sidecar_self_edge
test_sidecar_cycle_three_node
test_deep_chain_no_crash
test_drift_warn_only
test_layout_base_escape_confined
test_layout_base_circular_symlink_is_ignored_without_degrading
test_catalog_symlink_confined
test_sidecar_unknown_schema_degrades
test_standalone_clean
test_standalone_backward_orphan
test_standalone_forward_orphan
test_standalone_orphan_component
test_terminal_exemption
test_layer_skip_globally_unpopulated
test_crossrepo_pinned
test_crossrepo_unpinned
test_crossrepo_unresolvable
test_dangling_local_target
test_up_field_fallthrough_reference
test_dangling_up_field_still_fires
test_annotated_none_up_fields_are_placeholders
test_ambiguous_producer_pointer_exits_nonzero_in_both_modes
test_sidecar_ambiguous_endpoint_names_every_candidate
test_reach_dead_end_subtree_whole_not_just_tip
test_reach_floating_subtree_disconnected_from_root
test_reach_federated_resolved_terminus_not_flagged
test_reach_unresolvable_tip_surfaced_never_silently_green
test_reach_dangling_adjacent_not_double_reported
test_reach_skips_without_root
test_reach_degenerate_cases
test_container_and_file_recognition
test_screen_nested_brief_recognized
test_component_marker_symlink_outside_root_is_not_recognized
test_iter_dirs_prunes_unresolvable_children_before_descent
test_component_alias_uses_canonical_id
test_unclaimed_intent_file_becomes_intent_node
test_ordinal_prefixed_intent_filename_uses_slug_field_not_stem
test_intent_file_without_slug_is_reported
test_intent_file_without_slug_contributes_no_node
test_duplicate_derived_intent_id_caught_over_pre_insertion_sequence
test_unclaimed_intent_parent_pointer_wires_the_in_edge
test_no_semantic_vocabulary
test_output_shape
test_strict_never_promotes_softs
```

The four new CI-only command cases were:

```text
test_ac0002_unresolved_outcome_co_owner_refuses
test_ac0003_self_co_owner_refuses
test_ac0004_outcome_co_owner_does_not_add_graph_edges
test_ac0019_commented_outcome_co_owner_is_absent
```

## 2026-09-25 — T4 live intents and authoring surfaces

- `make lint-ruff lint-mypy` passed.
- The template/status conformance suites passed: 12 tests in 0.72 seconds.
- The three changed how-tos passed guide validation, title lint, and the
  repository-only-reference lint.
- The production parser returned the required `Outcome co-owner` and
  `Decomposed` values from both live intents.
- Whole-file closeout reads confirmed that the three authoring surfaces offer
  the optional peer field and `closed-empty`, and that the refusal guide covers
  malformed shape, unresolved target, self-reference, and comment-hidden
  absence.
- T4 was implemented by the scheduled implementer and its dispatch receipt was
  recorded for amended wave 2.

## 2026-09-25 — T5 release surfaces and managed-profile blocker

- Core `2.26.45` and Product Engineering `0.13.19` carry matching pack/plugin
  version pairs, focused eval cases, and release-history entries.
- `make lint-ruff lint-mypy`, all nine unfiltered handoff gates,
  `git diff --check`, the affected pack suites, and the cleanup-free
  traceability helper test passed. The intent corpus remained clean at 152 live
  entries; traceability remained at 727 nodes and 138 edges.
- The canonical forced self-host generator succeeded in a fresh approved temp
  root whose generated destinations did not already exist. Its three changed
  `.claude/` skill files and marketplace aggregate were synchronized back and
  are byte-equal to their sources/generated result.
- The active profile refused the first write beneath `.agents/`; that subtree
  is explicitly read-only in the managed permission profile. Per policy, it
  was not retried or escalated.
- These three generated projections remain stale and block AC-0016, T5 wave
  completion, final review, and closeout:
  `.agents/skills/work-intake/evals/evals.json`,
  `.agents/skills/work-intake/scripts/intent_shape.py`, and
  `.agents/skills/work-loop/scripts/lint-traceability.py`.
- T5's scheduled implementer receipt was recorded for amended wave 3, but the
  wave is intentionally left open. A supported writable profile or CI must run
  `env FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self`, then rerun the final
  gates and reviews.

## 2026-09-25 — T5 projection blocker cleared

- The owner completed projection regeneration in a profile that could write
  `.agents/`.
- The three formerly stale `.agents/` files are byte-equal to their `.apm/`
  sources. Their matching `.claude/` projections remain byte-equal as well.
- `knowledge provider unavailable` for the optional
  `agent-skill-engineering-reference/v1` capability handoff.

## 2026-09-25 — Final verification after projection regeneration

- `make lint-ruff lint-mypy` passed: Ruff reported no findings and mypy
  reported no issues across 149 source files.
- The parser plus field-reference parity suites passed: 275 tests in 0.86
  seconds. The template/status suites passed: 12 tests in 0.65 seconds.
- The intent corpus remained clean at 152 live entries. Traceability passed at
  727 nodes and 138 edges, with 464 informational structural orphans.
- Spec-status lint, the pack-test boundary suite, and `git diff --check`
  passed.
- The four repository-wide handoff gates rerun after regeneration passed:
  brief coverage, workspace reconciliation, CI parity, and contract-item
  alignment. Together with the five unchanged gates rerun before the managed
  projection blocker, all nine handoff gates are clean.
- The final T5 cohort wave check passed, and the work-loop advanced through
  `wave-complete` and `gates-clean` to `CODE-REVIEW`.

## 2026-09-25 — Review round 1 repair

- The adversarial reviewer reported that `Outcome co-owner` validation ran
  only through standalone graph derivation and could be skipped when an
  authoritative sidecar was present. Independent adjudication sustained the
  finding as a Blocker against AC-0002 and AC-0003.
- The repair validates visible on-disk co-owner declarations in sidecar mode
  through a separate canonical intent-id registry. It adds findings to the
  existing hard-violation path without mutating the authoritative graph or its
  edges.
- A parameterized command-level regression covers unresolved and
  self-referential peers with an authoritative sidecar. Those two cases join
  the documented cleanup-sensitive CI-only set in this managed profile.
- The unaffected traceability suite passed: 13 tests, 57 exact node-id
  deselections, 5.33 seconds. `make lint-ruff lint-mypy` also passed.
- The source and `.claude/` projection carry the repair. The active managed
  profile still withholds writes to `.agents/`, so one supported projection
  refresh remains before the repaired wave can re-enter final gates.

## 2026-09-25 — Review round 1 repair verified

- The owner refreshed generated projections. All three changed `.agents/`
  files and all three matching `.claude/` files are byte-equal to their
  `.apm/` authoring sources.
- Final verification passed after the sidecar repair: Ruff and mypy; 275
  parser/reference tests; 12 template/status tests; 13 cleanup-safe
  traceability tests with 57 exact node-id deselections; intent corpus lint at
  152 live entries; traceability at 727 nodes and 138 edges; spec-status lint;
  the pack-test boundary; guide validation; guide-title and repository-only
  reference lints; all four repository-wide handoff gates; and
  `git diff --check`.
- The two new parameterized sidecar command cases are part of the exact
  cleanup-sensitive CI-only set required by the managed-profile rule. They
  cover unresolved and self-referential peers under an authoritative sidecar.
- The repaired final wave passed its cohort check and advanced through
  `wave-complete` and `gates-clean` to review sequence 24.

## 2026-09-26 — Review round 2 repair

- The adversarial reviewer reported that the changed shipped Work Intake
  source still contained an internal `ADR-0033 D2` citation. Independent
  adjudication sustained the finding as a Blocker against AC-0018.
- The portable replacement states the runtime rule directly: `Level` remains
  required, but its vocabulary is open and the per-artifact lint must not
  enforce a closed set.
- A bounded sweep over every changed shipped `.apm/` file found no remaining
  ADR, RFC, task, or acceptance-criterion identifier. Ruff, mypy, and all 275
  parser/reference tests passed after the repair.
- The `.apm/` source now carries the repair. The active managed profile still
  withholds writes to `.agents/`, so a supported projection refresh remains
  before the repaired wave can return to final gates.

## 2026-09-26 — Review round 2 repair verified

- The owner refreshed generated projections. All three changed `.agents/`
  files and all three matching `.claude/` files are byte-equal to their
  `.apm/` authoring sources.
- The final gate set passed again: Ruff, mypy, 275 parser/reference tests, 12
  template/status tests, 13 cleanup-safe traceability tests with 57 exact
  node-id deselections, the 152-entry live intent corpus, traceability,
  spec-status lint, pack-test boundary, guide gates, all four repository-wide
  handoff gates, and `git diff --check`.
- The bounded changed-shipped-source sweep found no ADR, RFC, task, or
  acceptance-criterion identifiers.
- The repaired wave advanced through `wave-complete` and `gates-clean` to
  review sequence 27.

## 2026-09-26 — Review round 3 repair

- The adversarial reviewer reported that the traceability linter imported
  `intent_shape.py` from the sibling Work Intake skill. Independent
  adjudication sustained the finding as a Blocker because skills are projected
  independently and the accepted contract forbids a new dependency.
- The repair removes the sibling loader. A self-contained visibility reader
  now strips closed and unclosed HTML-comment regions, bounds the preamble at
  the first visible level-two heading, and passes the result through the
  linter's existing field matcher.
- Two cleanup-free regression tests pin both the independent-skill boundary and
  comment-aware preamble behavior. The unaffected traceability suite passed:
  15 tests, 57 exact node-id deselections, 2.62 seconds.
- `make lint-ruff lint-mypy` passed after the repair. The `.apm/` source now
  carries the fix; the active managed profile still withholds writes to
  `.agents/`, so one supported projection refresh remains before final gates.

## 2026-09-26 — Review round 3 repair verified

- The owner refreshed generated projections with the supported dirty-tree
  override. All three changed `.agents/` files and their matching `.claude/`
  files are byte-equal to the `.apm/` authoring sources.
- Final verification passed: Ruff and mypy; 275 parser/reference tests; 31
  template-conformance tests; 15 cleanup-safe traceability tests with 57 exact
  node-id deselections; the 152-entry live intent corpus; traceability at 727
  nodes and 138 edges; spec-status lint; the eight-case pack-test boundary;
  all four guide checks; every repository-wide handoff gate; and
  `git diff --check`.
- The projected `.agents` intent-corpus and traceability commands also passed
  their documented happy paths. A bounded shipped-source sweep found no
  repository ADR, RFC, feature-spec, task, or acceptance-criterion identifier.
- The repaired final wave passed its cohort exit check and advanced through
  `wave-complete` to verification sequence 29.

## 2026-09-26 — Review round 4 repair

- The owner explicitly authorized one retry-cap override after the work-loop
  reached its three-review retry limit. The cohort recorded review round 4 and
  retry 4 under that override before implementation resumed.
- The adversarial reviewer reported that `Outcome co-owner` resolution passed
  the visible declaration through the graph-pointer token normalizer.
  Independent adjudication sustained the finding as a Blocker because a value
  such as `intent:peer extra` could resolve as the shorter `intent:peer`
  canonical id instead of being refused.
- The self-contained preamble reader now preserves the whole normalized visible
  field for exact registry comparison. It still hides comment regions, stops at
  the first visible level-two heading, removes one presentation-only pair of
  wrapping backticks, and treats template placeholders as absent.
- The cleanup-free regression now proves that a longer declaration remains
  whole and cannot resolve through its leading token. Both focused tests passed
  in 0.37 seconds; Ruff and mypy also passed.
- The `.apm/` source carries the repair. The active managed profile still
  withholds writes to `.agents/`, so one supported projection refresh remains
  before the repaired wave can return to final gates.

## 2026-09-26 — Review round 4 repair verified

- The owner refreshed generated projections with the supported dirty-tree
  override. All three changed `.agents/` files and their matching `.claude/`
  files are byte-equal to the `.apm/` authoring sources.
- Final verification passed: Ruff and mypy; 275 parser/reference tests; the
  intent template and status parity suites; 15 cleanup-safe traceability tests
  with 57 exact node-id deselections; the 152-entry live intent corpus;
  traceability at 727 nodes and 138 edges; spec-status lint; the eight-case
  pack-test boundary; all guide checks; every repository-wide handoff gate;
  and `git diff --check`.
- The projected `.agents` intent-corpus and traceability commands passed their
  documented happy paths. A bounded shipped-source sweep found no repository
  ADR, RFC, feature-spec, task, or acceptance-criterion identifier.
- Tail triage counted 1,196 tracked additions and 664 lines in the untracked
  spec, plan, and verification ledger: 1,860 additions total, below the 2,000
  reviewable-line threshold.

## 2026-09-26 — Review round 5 and dispositions

- The post-gates adversarial reviewer returned the closed clean sentinel. Its
  persisted raw artifact validated at SHA-256
  `74b12980b87d0d6bc6a2bc7f5b51d18571074f7a3c4ec52969e3394d4c582e3c`
  and strict classification reported `clean` with zero findings. The cohort
  recorded it through the structural-clean form because the persisted file has
  a trailing newline.
- Review rounds 1 through 4 produced four sustained Blockers. Each was required
  for correctness or the accepted boundaries and was resolved in the current
  unit: authoritative-sidecar peer validation, removal of an internal shipped
  citation, independent projection of the Work Loop linter, and exact rather
  than leading-token peer resolution. No Blocker, Concern, Nit, or deferral
  remains.
- Reviewer roster: `adversarial-reviewer` clean; `security-reviewer` not
  warranted; `quality-engineer` not warranted; `frontend-reviewer` not
  warranted; `design-reviewer` not warranted; `experience-reviewer` warranted
  for reader-facing guides but unavailable as an installed role, so it is a
  named non-mandatory skip.
- The managed profile cannot complete Python temporary-directory cleanup. The
  57 exact cleanup-sensitive traceability nodes remain a CI-only blind spot
  accepted by the enterprise execution rule; the unaffected 15-test suite and
  both real projected commands passed locally.

## 2026-09-26 — Completion evidence handoff

- **Delivery:** `intent-preamble-closure-declarations`, run
  `3cd81b99-a32b-4b77-b052-90cf3f6a8972`.
- **Accepted outcome and authority:** the approved spec and plan in this
  directory. All 20 acceptance criteria are satisfied and checked.
- **Implemented scope:** optional typed `Outcome co-owner` shape and exact peer
  resolution without graph edges; `closed-empty` decomposition; comment-aware
  preamble parsing; two live migrations; adopter guidance, evals, releases,
  projections, and changelog. FEAT-0005 closure refusal behavior remains a
  non-goal owned by its separate slice.
- **Verification:** the round-4 verified record above owns the final gate set;
  this round's clean review is recorded immediately above it. All durable
  outputs in the spec are current: interface reference, authoring surfaces,
  refusal procedure, validator architecture notes, and release history.
- **Residuals and dependencies:** no unresolved accepted obligation or product
  dependency. Residual evidence limits are the named experience-reviewer skip
  and the exact CI-only cleanup-sensitive cases described above.
- **Completion-event candidate:** human acceptance and merge confirmation at
  the code human gate. A pull-request write was outside this session's granted
  authority; the recorded outcome is `offer-declined`.
- **Authority facts:** repository files are the independent source of truth;
  the managed profile allowed workspace writes but withheld generated
  `.agents/` writes, which the owner performed through the supported build;
  Git index and ref writes were prohibited; no deletion was requested or
  performed.

## 2026-09-26 — Post-rebase fixture repair (AC-0002, AC-0003, AC-0019)

- Rebasing this branch onto main surfaced two failing command-level tests:
  `test_ac0002_unresolved_outcome_co_owner_refuses` and
  `test_ac0003_self_co_owner_refuses` both expected exit 1 and observed exit 0
  with empty output. The same pair fails at the pre-rebase commit, so the
  conflict resolution did not introduce them.
- **Cause:** an `intent:` node is not a CHAIN layer, so a temporary corpus
  holding only intent files populates no discovery layer. `check()` reaches its
  documented no-chain-anchor return and exits 0 before any co-owner finding is
  reported. The linter is behaving as designed; the fixtures were unanchored.
- `test_ac0019_commented_outcome_co_owner_is_absent` shared the defect in its
  passing direction: its `rc == 0` assertion held over a corpus the lint never
  read, so it could not have failed.
- **Repair:** each of the three fixtures now writes a brief through
  `write_brief()`, the discovery anchor the ACs are read through. No linter
  behavior changed.
- **Verification:** the traceability, intent-shape, and field-reference parity
  suites pass — 347 tests, 17.6 seconds, 0 failures. `make lint-ruff lint-mypy`
  passes. Anchored fixtures were confirmed to discriminate: with the anchor,
  the unresolved peer and the self-reference both exit 1 with a report naming
  source, field, and target, and both comment-hidden corpora exit 0 with no
  co-owner mention.

## 2026-09-26 — CI repair: the shared-test node contract

- `gate-main` failed on `tools/test_local_ci_shared_test_deduplication.py`
  with `test_sidecar_outcome_co_owner_refuses_invalid_peer must declare
  explicit parameter IDs`. `make build-check` reported the same failure as a
  rollup of that gate, so the two red checks were one defect.
- **Cause:** the parametrized sidecar test shipped without `ids=`. The guard
  raises on a missing `ids=` before it compares counts, so the node-contract
  pin for `test_lint_traceability.py` never got to fire and the check was red
  for the whole branch.
- **Repair:** the arms are now named `unresolved-peer` and `self-reference`,
  and the `SHARED_TESTS[2]` pin moves from 63 to 72 with its digest. The
  re-pin is dispositioned against `origin/main` in the comment above it: 9
  additions, 0 removals, no rename, surviving 63 in their original order.
- **Verification:** the guard passes — 51 tests, 117.8 seconds. The
  traceability suite passes at 72 tests, which independently matches the
  re-pinned static node count. `make lint-ruff lint-mypy` passes.
