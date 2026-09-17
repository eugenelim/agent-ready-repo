# Spec: Two-sided prune closure invariant

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0114](../../adr/0114-prune-success-requires-a-two-sided-post-mutation-invariant.md), [RFC-0096](../../rfc/0096-portable-delivery-artifact-lifecycle.md) 2026-09-13 Errata
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
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

`workspace-status` removes an approved, explicitly selected set of delivery
artifacts together with every `workspace.toml` membership that resolves to
them, and refuses to report success unless it has proven both removals in one
coherent observation. A maintainer running the prune either gets a result where
the artifact directory and all of its memberships are gone, or a non-zero
result naming exactly which half survived. The operation executes a selection
that was approved elsewhere; it never chooses what to delete. Slice 1's
read-only membership check supplies the membership half of the observation, and
every production writer of either side coordinates through one shared lock so
the observation cannot be fractured by a sanctioned concurrent write.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User and maintainer promise | A destructive capability must document its selection, authority, refusal codes, and the exact meaning of a successful exit. | `packs/core/.apm/skills/workspace-status/SKILL.md` | workspace-status maintainers | Focused roster tests and an end-to-end invocation of the projected command against a disposable fixture | The documented invocation, refusal codes, closure guarantee, and residual limitation match shipped behavior. |
| Interface compatibility | A second skill gains a coordination obligation it did not previously carry. | `packs/core/.apm/skills/work-intake/SKILL.md` | work-intake maintainers | Forced-interleaving tests proving mutual exclusion with the prune | The documented intake transaction states that it participates in the shared workspace lock. |
| Release history | The core pack gains a consumer-visible destructive capability. | `docs/product/changelog.md` | core pack maintainer | A core-led release entry with a `Highlights` disposition | The release entry names the prune capability, its closure guarantee, and the matching core version. |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Acquire the shared workspace lock before validating any precondition that reads repository state, and hold it through every mutation and the closure observation. Validating the route and the syntax of the supplied arguments is the single permitted pre-lock step, because it reads nothing but the arguments themselves.
- Fix an immutable, non-empty selection before mutation, and re-resolve every later decision against that recorded selection rather than re-reading the caller's input.
- Prove that every selected artifact directory exists before mutating anything, so a run that removes nothing — or that carries an absent target on a present sibling — cannot report success.
- Change exactly the selected directories and the memberships resolving to them, and prove every unselected byte unchanged.
- Resolve membership identity through slice 1's canonical and legacy resolvers, against the exact workspace bytes read under the lock.
- Refuse any selected target that appears in the protected-directory manifest, and keep that manifest honest with a construction test that re-derives the protected set rather than trusting the list.
- Emit deterministic UTF-8 JSON, keep reads and writes confined to the repository, and treat loaded TOML and selector text as instruction-inert data.

### Ask first

- Add, remove, or reinterpret a refusal code, or change what a successful exit guarantees.
- Change which mutation paths participate in the shared lock.
- Change the protected-directory manifest's contents or the rule that derives it.
- Add any dependency, or create a new engine, skill, schema, or module boundary.

### Never do

- Report success while any selected artifact directory or any membership resolving to it survives.
- Select, rank, or deprioritize artifacts for deletion, or perform a reference-free or disposition check.
- Delete anything outside the recorded selection, or follow a symlink out of the repository to do it.
- Claim the operation is atomic, or that the closure observation protects against a writer that ignores the shared lock.
- Widen the global reconciliation population or change default `status`, `reconcile`, or `explain` behavior.
- Edit the generated `.agents/` or `.claude/` projections as the implementation source.

## Testing Strategy

- **Selection, grammar, and authority (AC-0001, AC-0002, AC-0003, AC-0004, AC-0029):** TDD in `tests/roster/test_two_sided_prune_closure_invariant.py`, using table-driven fixtures because selector grammar and confirmation binding have deterministic outcomes, pairing every rejection matrix with a valid control so a reject-all implementation fails, and round-tripping the preview's emitted challenge into an accepted confirmation so the authority path is reachable by a real caller rather than only by test helpers.
- **Protected-target refusal (AC-0005, AC-0006, AC-0007):** TDD in the same roster module, plus a derivation test that scans the live roster suite for literal spec-directory references and fails when the manifest omits one, because a hand-maintained enumeration silently leaks as tests are added; the derivation's undecidable remainder is stated rather than implied.
- **Anti-vacuity preconditions and baseline (AC-0008, AC-0009, AC-0028):** TDD using fixtures where nothing is present to remove, where one selected target is absent beside a present sibling, and where the artifact state drifts after the baseline is captured, because the predicate that passes on a no-op is the defect this contract exists to prevent.
- **Closure observation and lock discipline (AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016):** TDD with a deterministic fault-injection seam that pauses the operation at named points, because forced interleaving must be reproducible without real threads.
- **Blast-radius containment (AC-0027):** TDD byte-snapshot comparison over a fixture carrying unselected neighbours and unrelated workspace entries, because a success predicate scoped to the selection alone cannot detect collateral destruction.
- **Participating mutators (AC-0017, AC-0018, AC-0019):** TDD two-order forced-interleaving cases entered inside each participating writer's mutation interval, because frozen-output equality cannot detect a writer that stopped taking the shared lock.
- **Membership identity resolution (AC-0020, AC-0021, AC-0022):** TDD with canonical-duplicate, legacy-alias, and parse-blocked fixtures, asserting that a single survivor of any form denies success.
- **Safety, compatibility, and delivery (AC-0023, AC-0024, AC-0025, AC-0026):** TDD byte-snapshot checks around every refusal path, frozen fixtures for the existing subcommands, and goal-based checks for the eval harness, the version pair including its increase over the merge base, and the core-led changelog entry.

## Acceptance Criteria

- [x] **AC-0001.** The CLI recognizes the prune route. Route and selector-syntax validation is the one explicitly permitted pre-lock step: an empty supplied selection is rejected before any lock acquisition or mutation with that route's structured `empty_selection` response, distinguishable from `unknown_subcommand`, and cannot produce an all-clear or an empty success result. This pre-lock step reads no repository state other than the supplied arguments. Construction test: `test_empty_selection_is_rejected_by_recognized_route`; fixtures: `empty_selection` and `unknown_subcommand`.
- [x] **AC-0002.** Each accepted selector is a repository-relative directory of the form `docs/specs/<slug>`; absolute, drive-qualified, backslash-based, dot-segment, file-shaped, nested, and symlink-escaped selectors are rejected. The same invocation path must accept a valid selector that is pruned successfully, so a reject-all implementation fails. Construction test: `test_selector_grammar_and_confinement_with_valid_prune_control`; fixtures: `invalid_selectors` and `single_registered_target`.
- [x] **AC-0003.** The selection is fixed before mutation and is immutable for the operation's lifetime: every precondition, mutation, and closure decision reads the recorded selection, and mutating the caller-supplied input after the selection is fixed changes neither what is removed nor what is observed. Construction test: `test_selection_is_immutable_after_fixing`; fixture: `mutated_selector_input`.
- [x] **AC-0004.** The prune requires a confirmation bound to the operation identity and to AC-0028's single operation digest. Missing, malformed, stale, and binding-mismatched confirmations produce distinguishable structured refusals, and none of them mutates anything. Replay of an otherwise valid confirmation against an identical reconstructed state is explicitly **not** promised: detecting it would require durable receipt state that AC-0027's exact-delta guarantee forbids writing, and the shipped documentation states that limitation rather than implying single use. Construction test: `test_confirmation_binding_failure_classes_are_distinct_and_inert`; fixture: `confirmation_binding_matrix`.
- [x] **AC-0005.** A selected target listed in the protected-directory manifest is refused with a named `protected_target` refusal before any mutation, and the refusal names the offending selector. Construction test: `test_protected_target_is_refused_before_mutation`; fixture: `protected_target_selection`.
- [x] **AC-0006.** The protected-directory manifest is not trusted as written: a construction test re-derives, from the live roster suite, every spec directory named by a **literal** repository path and fails when the manifest omits one, so adding a roster test that literally reads a new spec directory turns that test red. The criterion's reach stops there and says so: a path assembled at runtime from parametrized segments is not statically decidable, is outside this control, and is named as its blind spot in the shipped documentation. The manifest is defense in depth, not the authority that makes a deletion safe — that authority is the approved selection and the separately required reference check. Construction test: `test_protected_manifest_covers_every_literal_roster_spec_dependency`; fixture: none — the test reads the live repository.
- [x] **AC-0007.** This spec's own directory, including its `notes/` subtree, is in the protected manifest and is refused by the same `protected_target` path. Construction test: `test_prune_refuses_its_own_spec_directory`; fixture: none — the test reads the live repository.
- [x] **AC-0008.** Artifact presence is established per selected target, not across the selection: the prune refuses with `nothing_to_remove` naming the offending selector when **any** selected artifact directory is absent at precondition time, and this refusal is reached before any mutation. A selection mixing one present and one already-absent target is refused whole, so an absent target can never be carried by a present sibling and a run that removes nothing can never exit zero. Construction test: `test_every_selected_target_must_be_present_before_mutation`; fixture: `already_absent_selection` with a `mixed_present_and_absent` case.
- [x] **AC-0009.** For a selected target that has at least one resolving membership at precondition time, both sides are recorded as present, and the operation fails unless both are later proven absent; for a selected target with no resolving membership, the artifact side alone carries the anti-vacuity requirement and the membership side must still be proven absent at closure. Construction test: `test_recorded_presence_determines_both_sided_obligation`; fixture: `registered_and_entryless_targets`.
- [x] **AC-0010.** The shared workspace lock is acquired before any repository-state precondition validation — before reading `workspace.toml`, probing any selected directory, consulting the protected manifest, or validating the confirmation. Only AC-0001's argument-syntax step may precede it. When the lock is already held, the prune refuses with `lock_busy` having read no repository state, mutated nothing, and taken no closure observation. Construction test: `test_prelocked_workspace_refuses_before_any_state_read`; fixture: `preplanted_lock`.
- [x] **AC-0011.** The lock is held continuously across artifact removal, membership removal, and the closure observation, and is released afterwards even when the operation raises. Construction test: `test_lock_spans_both_mutations_and_closure_and_is_always_released`; fixture: `lock_span_probe`.
- [x] **AC-0012.** On a run that passes every precondition and reaches mutation, the operation reads `workspace.toml` from disk exactly twice under the one held lock: once before mutation, whose bytes are the baseline, and once after both mutations, whose bytes are the sole input to closure. This criterion governs only such a run — `prune --preview` and every pre-mutation refusal, including the busy-lock refusal of AC-0010, are outside it and read less. Closure never resolves membership from bytes the operation computed in memory or intended to write. A fault case in which the membership write silently no-ops or is reverted on disk must fail the operation, because closure reads what is actually there rather than what was meant to be there. Both resolutions bind to the recorded selection. Construction test: `test_closure_reads_post_mutation_bytes_from_disk_not_intended_bytes`; fixture: `noop_write_fault`.
- [x] **AC-0013.** Artifact absence means the selected directory itself does not exist under a confined, symlink-refusing lookup. An emptied directory, a surviving directory whose `spec.md` was removed, and a symlink standing in for the directory each deny absence. Construction test: `test_artifact_absence_requires_directory_nonexistence`; fixture: `partial_artifact_removal_matrix`.
- [x] **AC-0014.** The prune exits zero only when, in one observation taken under the held lock, every selected artifact directory is absent and no canonical, supported legacy-alias, or selected-target parse-blocked occurrence resolves to any selected artifact. Construction test: `test_exit_zero_requires_both_sides_absent_in_one_locked_observation`; fixture: `clean_two_sided_prune`.
- [x] **AC-0015.** When either side survives, the prune exits non-zero and its structured result names which half survived and for which selector, without claiming rollback or atomicity. Construction test: `test_surviving_half_state_is_reported_and_fails`; fixture: `forced_half_state_matrix`.
- [x] **AC-0016.** The prune excludes an A→B→A change only for writers that take the shared lock. A characterization test demonstrates that the raw-byte digest alone does not detect A→B→A, and the shipped documentation states this residual limitation rather than claiming protection against it. Construction test: `test_aba_is_excluded_by_the_lock_not_the_digest`; fixture: `aba_characterization`.
- [x] **AC-0017.** The work-intake transaction acquires the shared workspace lock before materializing an artifact and holds it across artifact materialization, workspace registration, and any rollback. Construction test: `test_intake_transaction_holds_the_shared_lock_across_its_whole_interval`; fixture: `intake_transaction_lock_span`.
- [x] **AC-0018.** A prune in progress and a work-intake transaction are mutually exclusive in both orders: whichever acquires the lock second refuses with the busy result and mutates nothing. Construction test: `test_prune_and_intake_are_mutually_exclusive_in_both_orders`; fixture: `prune_intake_interleaving`.
- [x] **AC-0019.** Every named participating writer — `repair-apply`, migration apply, migration rollback, the work-intake guarded refresh, the work-intake transaction, and a second concurrent prune — is proven mutually exclusive with the prune in **both** orders. Each case pauses the *first* operation at a deterministic point inside its own complete mutation interval, then has the *second* operation attempt lock acquisition and assert it refuses busy without mutating. Because one paused point only samples the interval, each named writer additionally asserts the lock is held immediately before its first mutation and still held after its last mutation or rollback, and each writer class carries an early-release mutation in which the lock is dropped between its two mutations — that mutation must turn a case red. Frozen-output equality alone does not satisfy this criterion: a writer that silently stopped taking the shared lock must turn a case red while its isolated output stays identical. Construction test: `test_every_participating_writer_is_mutually_exclusive_in_both_orders`; fixture: `participating_writer_interleaving_matrix`.
- [x] **AC-0020.** Two canonical occurrences resolving to one selected artifact are both removed, and a fixture in which exactly one is removed fails closure with the surviving occurrence named. Construction test: `test_duplicate_canonical_occurrences_must_all_be_removed`; fixture: `duplicate_canonical_survivor`.
- [x] **AC-0021.** A supported legacy-alias occurrence resolving to a selected artifact is removed, and a fixture in which a legacy alias survives a canonical removal fails closure. Construction test: `test_surviving_legacy_alias_denies_closure`; fixture: `legacy_alias_survivor`.
- [x] **AC-0022.** A selected-target parse-blocked occurrence fails closure rather than reading as absence, so a malformed entry naming a selected artifact can never be mistaken for a removed one. Construction test: `test_parse_blocked_occurrence_denies_closure`; fixture: `parse_blocked_survivor`.
- [x] **AC-0023.** Adding the prune route leaves the default `status`, `reconcile`, `explain`, and `selected-membership` results byte-identical for the same frozen repository fixture. Construction test: `test_existing_subcommands_are_unchanged`; fixture: `default_command_compatibility`.
- [x] **AC-0024.** Every refusal path — invalid selector, protected target, absent artifact, confirmation failure, and busy lock — leaves `workspace.toml`, every selected directory, and every other file in the fixture byte-identical. Construction test: `test_every_refusal_path_performs_no_writes`; fixture: `refusal_snapshot_matrix`.
- [x] **AC-0025.** Invalid input and every refusal produce the command's structured error shape on stdout and a concise UTF-8 diagnostic on stderr, with no traceback, no absolute repository root, and no loaded instruction text, including for non-ASCII fixture content. Construction test: `test_refusal_output_is_safe_and_utf8`; fixture: `unsafe_and_instruction_like_input`.
- [x] **AC-0026.** The workspace-status eval harness contains a triggering query and a behavior case for the prune; the core `pack.toml` and `.claude-plugin/plugin.json` carry the same version; that version is the next patch above the merge-base core version, so leaving both files unchanged fails and so does a minor or major bump, which this pack's rules reserve for new primitives and removals respectively — a collision with a version claimed on another unmerged branch is outside what a local check can decide and is left to the pre-merge update gate; and `docs/product/changelog.md` carries a core-led entry naming the capability and that same version. Construction test: `test_pack_delivery_contract_is_complete_and_version_increased`; fixture: `workspace_status_eval_contract`.
- [x] **AC-0027.** A successful prune changes exactly the selected artifact directories and the membership occurrences resolving to them, and nothing else. For a fixture containing selected and unselected spec directories and unrelated workspace entries, every unselected directory, every unrelated entry, and every other repository path is identical before and after in content, entry type, symlink target, and tracked mode bits; the resulting `workspace.toml` still parses and retains every unrelated collection; and a nested symlink under a selected directory is unlinked rather than followed, leaving its target intact. The comparison reaches exactly those recorded elements. An implementation that removes more than the selection fails. Construction test: `test_successful_prune_changes_only_the_selected_delta`; fixture: `exact_delta_with_unselected_neighbours`.
- [x] **AC-0028.** The prune captures a pre-mutation baseline covering **every** entry below each selected directory — not only regular files — recording each entry's repository-relative path, type, and mode bits that the repository's version control tracks, the SHA-256 of each regular file's bytes, the literal target text of each symlink, and refusing any entry type it cannot represent. The operation digest is computed canonically over three inputs together: the immutable selection, that complete per-target tree manifest, and the SHA-256 of the exact `workspace.toml` bytes read under the lock. The confirmation binds to that single digest. The baseline is re-compared immediately before mutation. Drift in any recorded element — an added or removed entry of any type, a changed regular-file digest, a changed symlink target, a changed tracked mode bit, or a changed `workspace.toml` hash — produces a distinguishable stale-baseline refusal instead of a silent deletion. The guarantee reaches exactly the elements enumerated above and no further; state the manifest does not record is outside it. A constant, unused, selector-only, or regular-file-only digest fails. Construction test: `test_operation_digest_binds_selection_tree_and_workspace_and_refuses_drift`; fixture: `baseline_staleness_matrix`.
- [x] **AC-0029.** A caller can obtain the confirmation challenge from the shipped command: invoking `prune --preview` with a selection emits, without mutating anything, an **unsigned** challenge carrying the canonical operation identity and operation digest in the exact form `--confirmation-file` consumes. The preview never emits the human-authorization fields — subject, role, and confirming identity — which must be supplied independently, so the command cannot fabricate the approval it is gated on. The round-trip fixture builds a confirmation from the preview's challenge plus independently supplied authorization fields and is accepted; a confirmation built from preview output alone is refused. The preview leaves the fixture byte-identical. Construction test: `test_preview_emits_an_unsigned_challenge_requiring_independent_authorization`; fixture: `preview_to_confirmation_round_trip`.

## Follow-ons

- eugenelim: RFC-0096 Wave 7d execution — combine this prune with the separately required reference-free mechanical check before selecting or deleting a carved-out spec. Wave 7d owns selection; this slice owns execution.
- eugenelim: ~~the packaged-runtime drift gate skips a declared pair whose bundled
  copy is missing, so an incomplete packaged runtime passes build-check.~~ Closed
  in a follow-up change to that pre-existing gate. The synthetic minimal tree this
  slice ran into stays green without edits: the gate's skip now mirrors the
  real-write sync path's own write condition, so it tolerates a tree with no
  packaged-runtime directory and fails a present directory that is missing a
  declared copy. The same change also closed the half this slice hit live —
  pairs are hand-declared, so a bundled runtime could load a sibling nobody
  declared. The gate now derives that closure from the sources instead of
  trusting the list, and an unbundled sibling must carry a recorded reason.
- eugenelim: a shipped spec should be easy to retire. Today it often is not: surfaces bind directly to spec directories — roster tests read their bytes, six files are SHA-256 pinned and four of those sit inside two spec directories, and other specs, guides, and records cite their paths — so a spec that has finished its job becomes permanently unretirable and the corpus only grows. Keeping shipped specs retirable is the upstream work: surfaces should carry the content they depend on, or reference a durable owner, rather than pinning a delivery contract that is meant to age out. Then removing a spec is only ever removing the spec.
- eugenelim: the shared lock is fail-fast and PID-stamped but has no staleness recovery — a process killed while holding it leaves a lock file that refuses every later operation. Existing behavior, widened in blast radius by this slice's new participants.
- workspace-status owner decision: `docs/specs/` currently holds 285 entry-less spec directories against 168 registered ones. If the prune becomes the repository's routine registration cleanup, the durable fix is upstream — registration discipline plus RFC-0094 adoption for work that should create no artifact at all — not a larger prune.

## Assumptions

- Technical: `packs/core/.apm/skills/workspace-status/scripts/` holds the editable engine and CLI sources, and the `.agents/` and `.claude/` trees are generated by `make build-self` (source: `packs/AGENTS.md` § Self-hosting projection, confirmed 2026-09-13).
- Technical: `_migration_lock` is the shared, non-waiting, `O_CREAT|O_EXCL` workspace lock already taken by `repair-apply` before precondition validation (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py:1891`, confirmed 2026-09-13).
- Technical: `_migration_atomic_replace` already carries named fault-injection points, so forced interleaving is deterministic without real threads (source: same file, lines 1569-1605, confirmed 2026-09-13).
- Technical: no production code path removes a `docs/specs/<slug>` directory today, so the prune becomes the sole such path (source: repository-wide search of `rmtree`/`rmdir` call sites, confirmed 2026-09-13).
- Technical: `selected_membership_status` reads `workspace.toml` internally, so binding closure to the locked byte snapshot requires a pure seam over already-parsed workspace state (source: `workspace_status_engine.py:2884`, confirmed 2026-09-13).
- Product: ADR-0114's stated domain is a registered artifact and its membership, while RFC-0096 makes Wave 7d depend on the mechanics this slice ships and Wave 7d's carve-out population is entry-less. This spec therefore anchors anti-vacuity on the artifact side and requires every side observed present to be observed absent, so one mechanism serves both populations (source: ADR-0114 lines 12-27 and 56-70, RFC-0096 lines 447 and 524-534, confirmed 2026-09-13).
- Product: the prune executes an approved selection and contains no disposition logic; reference-free verification remains Wave 7d's separate condition (source: user confirmation 2026-09-13).
