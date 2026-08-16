# Plan: Project knowledge foundation

- **Spec:** [`spec.md`](spec.md) (Shipped)
- **RFC:** [`RFC-0077`](../../rfc/0077-distill-knowledge.md) (Accepted)
- **ADRs:** [`ADR-0081`](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md) and [`ADR-0082`](../../adr/0082-project-knowledge-modes-separate-authority.md) (Accepted)
- **Status:** Done
- **Mode:** full

## Approach

Build one portable file-first lifecycle in dependency order:

```text
workflow scratch
  -> semantic-gate triage
  -> project-knowledge --capture
  -> classification/month observation journal
  -> project-knowledge --distill
  -> terminal disposition + optional topic mutation
  -> per-topic JSON + deterministic body-free map
  -> committed Git snapshot
  -> project-knowledge --enquire
  -> bounded untrusted evidence
```

The smallest sound shipping slice includes the full boundary before any
automatic capture integration: published contracts, privacy refusal,
provenance, one writer and lock, observation dispositions, topic promotion,
committed-only enquiry, migration, then work-loop cutover. Implementing capture
without the downstream isolation and disposition path would create a durable
untrusted backlog with no governed consumer.

## Assumptions surfaced

- `metadata.boundaries` classifies a skill but does not grant runtime
  capabilities; mode-specific callable surfaces enforce least privilege.
- Repository publication is the only portable durable handoff available to all
  supported environments; scratch and uncommitted worktrees can still be lost.
- One coarse writer lock is acceptable at the first-slice volume; partitioning
  reduces file heat but does not replace serialization.
- Ordinary Git review is sufficient for unambiguous journal/topic proposals;
  judgment cases still Surface and wait.

## Constraints

- No Git ref updates, database, daemon, service, embedding model, or new runtime
  dependency.
- Use pure-stdlib Python for new scripts and portable path/lock behavior across
  Linux, macOS, and native Windows.
- One discoverable `project-knowledge` skill; no standalone public capture,
  distillation, or enquiry skills.
- Producer workflows use the public contract and normal skill discovery; they
  never import the writer or select a journal path.
- Observation journals are never enquiry input and rejected bodies are never
  quarantined.
- Do not change the core 2.5.9 closeout question or persist the prohibited
  comparison-product name.

## Verification design

### TDD invariants

- Strict contracts reject unknown fields, duplicate keys, non-finite numbers,
  unsafe Unicode, invalid scopes, missing provenance, and oversize bodies.
- Capture is fail-closed and idempotent. A processed capture has at most one
  terminal disposition; unresolved captures remain pending, non-queryable, and
  enumerable through the bounded maintainer drain.
- Lock ownership and recovery are deterministic and portable; no writer can
  remove or overwrite another live lock.
- Topic/map publication is coherent at `HEAD`; working-tree files and journals
  cannot leak into enquiry.
- Mode construction makes cross-mode helper calls impossible.
- Migration is count-preserving and never activates dual writers.

### Integration journeys

1. Fresh capture, exact replay, identity-integrity refusal, disposition, and promotion.
2. Interruption after each temporary/replace boundary followed by completion or
   bounded refusal.
3. Legacy migration with active, review-required, refused, and ambiguous rows.
4. Work-loop triage and core handoff with core present and absent.
5. Human and skill enquiry, source drift, injection-shaped topic text, and
   abstention.
6. Two worktrees changing distinct topics and rebuilding one deterministic map.

### Delivery gates

- Focused project-knowledge and work-loop tests.
- `make build-self` after pack-source changes.
- `make lint-ruff` and targeted mypy if touched modules are typed.
- `SKIP_SAST=1 make build-check`, then the repository-required security scan
  when available.
- `agentbundle catalogue verify` and projection-drift checks.
- Adversarial, security, and quality review; manual end-to-end evidence.

## Design

### Contracts

- Public `knowledge-captured-observation-v1` JSON Schema under
  `contracts/jsonschema/`.
- Internal strict contracts for journal events, dispositions, topics, topic
  map, mutation proposals, capture receipts, enquiry receipts/envelopes, and
  redacted `KnowledgeDiagnostic` results.
- Fixed v1 competency-question vocabulary and resource budgets.

### Components

- `packs/core/.apm/skills/project-knowledge/SKILL.md` — progressive router.
- Mode references — separate capture, distill, and enquire instructions.
- `scripts/project_knowledge.py` — public mode-specific deterministic CLI.
- `scripts/knowledge_store.py` — private confined parser/writer/index library;
  not a producer integration surface.
- `packs/core/tests/skills/project-knowledge/` — construction, contract,
  behavior, and portable-filesystem tests.
- Work-loop source — scratch/triage owner and agent-mediated core handoff.

### Write protocol

1. Mode validates its strict input before resolving a target.
2. Private storage resolves Git worktree and knowledge root with relocation
   variables removed and proves containment.
3. It acquires the global worktree-local lock by exclusive create and records a
   random token plus file identity.
4. It re-reads all state controlling the mutation and checks idempotency,
   disposition, blob, source, and proposal preconditions.
5. Capture writes and atomically replaces one journal postimage. Distillation
   writes same-directory temporary postimages and replaces them in the exact
   order topic, complete map, terminal disposition.
6. It validates the final postimage and releases only the still-owned lock.
7. The occurrence stores a deterministic `mutation_id` derived from capture,
   target, and semantic fields, plus ordinary evidence digests; topic hashing
   includes the ID; the proposal stores topic pre/postimage digests and hashes
   canonical UTF-8/JCS bytes with only its self-digest omitted. No nonce or
   random replay state exists. Recovery without the proposal refuses;
   exact proposal replay reconstructs the ID, rebuilds a missing map or appends a
   disposition only for the exact topic postimage, and otherwise refuses. A
   `promoted` disposition cannot exist without its exact topic occurrence/map.

Capture derives `<kind>/YYYY-MM.jsonl` from validated values. Distillation
appends the disposition to the capture's partition and may mutate one topic plus
the map. Agent reasoning happens before lock acquisition.

### Publication and enquiry

Working-tree capture and topic edits are proposals. Git publishes topic/map
visibility as one commit tree. Enquiry resolves `HEAD` once, verifies the full
map-to-blob set, filters before ranking, opens only bounded bodies, and checks
their freshness anchors against confined current sources. Observation journals
are neither routed nor opened.

## Tasks

### T1: Publish contracts and progressive mode isolation

**Depends on:** none

**Verification mode:** TDD.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_contracts.py`
- `packs/core/tests/skills/project-knowledge/test_mode_isolation.py`
- stub: true

```python
# STUB: AC1
def test_ac1_public_capture_schema_is_strict_and_versioned():
    schema = load_public_schema("knowledge-captured-observation.schema.json")
    assert schema["additionalProperties"] is False
    assert_valid(schema, valid_capture_request())
    invalid_cases = (
        capture_request_with_unknown_field(),
        capture_request_with_duplicate_key_bytes(),
        capture_request_with_non_finite_number_bytes(),
        capture_request_with_unsafe_unicode(),
        capture_request_with_producer_supplied_capture_id(),
        capture_request_without_provenance(),
        capture_request_with_oversized_lesson(),
    )
    for case in invalid_cases:
        assert_strictly_rejected(schema, case)
    assert public_contract_bytes() == bundled_contract_bytes()


# STUB: AC1
def test_ac1_core_derives_capture_id_from_canonical_request():
    vectors = load_fixed_vector_requests("capture-id-v1")
    expected = vectors.expected_capture_id
    for equivalent_json in vectors.equivalent_key_order_whitespace_and_escapes:
        assert derive_capture_id_from_strict_json(equivalent_json) == expected
    assert expected.startswith("kco-202608-")
    assert derive_capture_id(vectors.changed_field_request) != expected
    assert "capture_id" not in capture_id_preimage_fields()


# STUB: AC5
# STUB: AC7
# STUB: AC8
# STUB: AC9
def test_ac5_topic_contract_enforces_lifecycle_freshness_and_retirement():
    assert_valid_topic(active_topic_with_fresh_source())
    for topic in (
        topic_with_unknown_lifecycle(),
        topic_with_changed_source_marked_active(),
        topic_retired_without_effective_successor(),
    ):
        assert_topic_refused(topic)


# STUB: AC6
def test_ac6_occurrence_preserves_provenance_without_transcript():
    occurrence = promoted_occurrence_with_optional_evidence_digest()
    assert occurrence["capture_id"]
    assert "transcript" not in occurrence


# STUB: AC10, AC11
def test_ac10_topic_and_map_contracts_keep_bodies_out_of_map():
    topic = valid_topic()
    topic_map = build_map([topic])
    assert topic_map["entries"][0]["topic_key"] == topic["topic_key"]
    assert "synthesis" not in canonical_json(topic_map)


# STUB: AC12
def test_ac12_scope_and_path_contracts_are_platform_equivalent():
    assert serialize_scope(r"packages\core") == "packages/core"
    for alias in (r"C:\repo", r"\\server\share", "../escape", "AUX"):
        assert_refused(lambda: serialize_scope(alias))


# STUB: AC12
def test_ac12_real_filesystem_confinement_refuses_escape_and_uncertainty(tmp_path):
    for platform_fixture in (linux_fs, macos_fs, native_windows_fs):
        fs = platform_fixture(tmp_path)
        for target in (
            fs.symlink_or_reparse_escape,
            fs.directory_cycle,
            fs.identity_alias,
            fs.non_regular_file,
            fs.io_uncertain_path,
        ):
            assert_refused(lambda: confined_read_write(fs.knowledge_root, target))


# STUB: AC26
def test_ac26_each_progressive_mode_has_a_disjoint_helper_surface():
    assert helpers_for("capture") == {"capture_observation"}
    assert "write" not in helpers_for("enquire")
    assert "read_journal" not in helpers_for("enquire")


# STUB: AC27
def test_ac27_skill_metadata_declares_exact_informational_union():
    assert skill_boundaries("project-knowledge") == [
        "filesystem_read_untrusted",
        "filesystem_write",
    ]


# STUB: AC36
def test_ac36_digest_contract_hashes_exact_bytes_without_normalization():
    assert digest_bytes(b"line\r\n") != digest_bytes(b"line\n")
    assert_refused(lambda: parse_digest(unknown_digest_algorithm()))


# STUB: AC37
def test_ac37_diagnostics_are_typed_redacted_and_allowlisted():
    failures = (
        privacy_failure(),
        provenance_failure(),
        strict_parse_failure(),
        confinement_failure(),
        lock_contention_failure(),
        lock_loss_failure(),
        journal_capacity_failure(),
        cursor_stale_failure(),
        replay_required_failure(),
        postimage_mismatch_failure(),
        map_mismatch_failure(),
        staged_dual_writer_failure(),
    )
    assert {item.code for item in failures} == REQUIRED_DIAGNOSTIC_CODES
    for failure in failures:
        diagnostic = render_diagnostic(failure)
        assert_valid_knowledge_diagnostic(diagnostic)
        assert set(diagnostic) <= SAFE_DIAGNOSTIC_FIELDS
        assert not contains_source_body_or_absolute_path(diagnostic)
```

**Implements:** AC1, AC5-AC12, AC19, AC23, AC26-AC27, AC29, AC36-AC37

**Touches:** public JSON Schema and byte-identical engine bundle,
`project-knowledge` skill/router skeleton, internal contract parser, competency
vocabulary, budgets, catalogue metadata, and contract/construction tests.

**Work:**

1. Add the strict captured-observation schema and internal strict JSON models.
   Include the allowlisted redacted `KnowledgeDiagnostic` contract.
2. Add portable structural-scope normalization and base confinement helpers.
3. Define versioned Git-blob, exact-byte SHA-256, and content-addressed
   capture-ID preimage contracts.
4. Add the progressive router with three mode references and no working
   implementation behind writer calls yet.
5. Expose disjoint helper registries for capture, distill, and enquire; make
   invalid mode/cross-mode calls fail before I/O.
6. Add catalogue activation, near-miss, metadata, and projection tests.

**Done when:** contracts are reviewable and the empty progressive shell proves
mode isolation without persisting anything.

### T2: Implement fail-closed captured-observation journals

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_observation_store.py`
- `packs/core/tests/skills/project-knowledge/test_locking.py`
- stub: true

```python
# STUB: AC2
def test_ac2_capture_derives_partition_and_returns_receipt(repo):
    receipt = capture(repo, valid_capture_request(kind="gotcha", month="2026-08"))
    assert receipt.partition == "observations/gotcha/2026-08.jsonl"
    assert journal_events(repo) == [captured_event(receipt)]


# STUB: AC3
def test_ac3_replay_is_idempotent_and_changed_request_gets_distinct_id(repo):
    first = capture(repo, valid_capture_request())
    before_replay = journal_bytes(repo)
    assert capture(repo, valid_capture_request()) == first
    assert journal_bytes(repo) == before_replay
    assert captured_event_count(repo, first.capture_id) == 1
    for changed in (
        request_with_changed_body(),
        request_with_changed_kind(),
        request_with_changed_observation_month_within_window(),
    ):
        assert capture(repo, changed).capture_id != first.capture_id


# STUB: AC3
def test_ac3_replay_across_writer_month_boundary_uses_original_partition(repo):
    first = capture(repo, request_observed_at_month_end(), writer_time="2026-08-31T23:59:59Z")
    before_replay = journal_bytes(repo)
    replay = capture(repo, request_observed_at_month_end(), writer_time="2026-09-01T00:00:01Z")
    assert replay == first
    assert journal_bytes(repo) == before_replay
    assert captured_event_count(repo, first.capture_id) == 1


# STUB: AC2
def test_ac2_time_window_refuses_new_but_returns_exact_persisted_replay(repo):
    cases = (
        request_observed_days_ago(8),
        request_observed_minutes_in_future(6),
        request_observed_before_v1_activation(),
    )
    for request in cases:
        before = journal_bytes(repo)
        assert_refused_reason(lambda: capture(repo, request), "observation_time")
        assert journal_bytes(repo) == before
        existing = seed_previously_admitted_capture(repo, request)
        before_replay = journal_bytes(repo)
        assert capture(repo, request) == existing.receipt
        assert journal_bytes(repo) == before_replay
        assert captured_event_count(repo, existing.capture_id) == 1


# STUB: AC3, AC18, AC37
def test_ac3_capture_and_consumers_refuse_identity_corruption_without_mutation(repo):
    corrupted = seed_event_whose_body_does_not_hash_to_capture_id(repo)
    before = journal_bytes(repo)
    for action in (
        lambda: capture(repo, corrupted.request),
        lambda: select_pending(repo, corrupted.partition),
        lambda: distill_capture(repo, corrupted.capture_id),
    ):
        diagnostic = assert_refused(action)
        assert_redacted(diagnostic)
        assert journal_bytes(repo) == before


# STUB: AC13
def test_ac13_lost_lock_is_never_removed_or_reused(repo):
    lock = foreign_live_lock(repo)
    assert_refused(lambda: capture(repo, valid_capture_request()))
    assert lock.exists()


# STUB: AC13
def test_ac13_capture_and_distill_contend_on_one_global_lock(repo):
    capture_process = hold_writer_lock(repo, mode="capture")
    assert_refused_reason(lambda: begin_distill(repo), "lock_contention")
    capture_process.release()
    distill_process = hold_writer_lock(repo, mode="distill")
    assert_refused_reason(lambda: begin_capture(repo), "lock_contention")
    assert no_unowned_postimages(repo)


# STUB: AC18, AC37
def test_ac18_pre_admission_failure_persists_no_body_or_derived_identifier(repo):
    for request in (
        request_with_private_locator(),
        request_with_insufficient_provenance(),
    ):
        diagnostic = assert_refused(lambda: capture(repo, request))
        assert "capture_id" not in diagnostic
        assert no_content_digest(diagnostic)
    assert not observation_bodies(repo)


# STUB: AC19
def test_ac19_fixed_v1_budgets_and_exhaustion_are_fail_closed(repo):
    assert budget_contract() == {
        "capture_event_bytes": 16 * KIB,
        "journal_partition_bytes": 32 * MIB,
        "journal_partition_events": 50_000,
        "retained_partitions": 240,
        "retained_journal_bytes": 512 * MIB,
        "pending_page_partitions": 6,
        "pending_page_events": 10_000,
        "pending_page_bytes": 16 * MIB,
        "topic_bytes": 128 * KIB,
        "occurrences_per_topic": 256,
        "topic_files": 50_000,
        "topic_corpus_bytes": 512 * MIB,
        "map_entries": 50_000,
        "map_bytes": 32 * MIB,
        "enquiry_bodies": 12,
        "enquiry_body_read_bytes": 1 * MIB,
        "envelope_bytes": 32 * KIB,
        "script_seconds": 30,
        "automatic_retries": 0,
    }
    exhaustions = exhaustion_case_by_budget_key(repo)
    assert set(exhaustions) == set(budget_contract()) - {"automatic_retries"}
    for exhausted in exhaustions.values():
        before = semantic_file_bytes(repo)
        assert_bounded_refusal(exhausted.action)
        assert semantic_file_bytes(repo) == before
    assert observed_automatic_retry_count(repo) == 0


# STUB: AC14
def test_ac14_capture_journal_faults_never_expose_partial_event(repo):
    for boundary in ("temp_write", "temp_verify", "journal_replace", "post_verify"):
        result = interrupt_capture(repo, after=boundary)
        assert no_partial_jsonl_event(repo)
        assert exact_replay_completes_or_returns_bounded_refusal(repo, result)


# STUB: AC32
def test_ac32_journal_merge_collapses_replay_and_refuses_collision(repo):
    distinct = merge_three_stage(repo, distinct_capture_fixture())
    assert distinct.capture_count == 2
    assert distinct.events == sorted(distinct.events, key=canonical_event_order)
    assert capture_precedes_disposition(distinct.events)
    assert merge_three_stage(repo, exact_replay_fixture()).capture_count == 1
    for conflict in (
        body_collision_fixture(),
        wrong_partition_fixture(),
        disposition_collision_fixture(),
        orphan_disposition_fixture(),
    ):
        assert_refused(lambda: merge_three_stage(repo, conflict))
```

**Implements:** AC2-AC4, AC12-AC14, AC18-AC19, AC32-AC33

**Touches:** private store, capture mode/CLI, lock and recovery helpers,
observation fixtures, and cross-platform filesystem tests.

**Work:**

1. Implement privacy/provenance refusal before any body write.
2. Derive classification/month partition paths and append strict capture and
   disposition events through locked read-validate-replace. Month comes from
   immutable request observation time, never writer time. Enforce the v1
   activation, seven-day past, and five-minute future window. Refuse general
   historical backfill in Slice 1; only AC20's existing legacy migration is
   supported, and any broader import requires separate governance.
3. Derive content-addressed capture IDs from strict canonical requests; exact
   replay returns its receipt while changed requests form distinct pending
   observations for distillation without an unbounded retained scan.
4. Implement exclusive-create lock ownership, bounded stale reclaim,
   and lost-lock detection.
5. Enforce partition, retained-corpus, and cursor-paged pending-selection
   budgets with explicit capacity refusal.
6. Add the private deterministic three-stage journal merge helper and cover
   exact replay, identity collision, orphan/competing disposition, and ordering.
7. Lint all journal events and enforce at most one terminal disposition.

**Done when:** capture is a durable, isolated, recoverable handoff with no
query path and no retention automation.

### T3: Implement canonical topics, map, and guarded mutation

**Depends on:** T1, T2

**Verification mode:** TDD.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_topic_store.py`
- `packs/core/tests/skills/project-knowledge/test_topic_map_merge.py`
- stub: true

```python
# STUB: AC10
def test_ac10_topic_is_pretty_json_and_not_an_event_stream(repo):
    write_topic(repo, valid_topic())
    assert read_json(topic_path(repo))["topic_key"] == valid_topic()["topic_key"]
    assert topic_path(repo).read_text().endswith("\n")


# STUB: AC11
def test_ac11_map_is_body_free_and_byte_deterministic(repo):
    first = rebuild_map(repo)
    second = rebuild_map(repo)
    assert first == second
    assert "synthesis" not in first.decode()


# STUB: AC14
def test_ac14_interruption_never_changes_committed_query_snapshot(repo):
    interrupt_topic_mutation(repo, after="topic_replace")
    assert enquire_head(repo) == pre_mutation_head_result(repo)


# STUB: AC14
def test_ac14_promoted_disposition_requires_topic_and_matching_map(repo):
    for boundary in ("topic", "map", "disposition"):
        state = interrupt_and_recover(repo, after=boundary)
        assert state.promoted_implies_topic_and_map()


# STUB: AC14
def test_ac14_recovery_refuses_changed_synthesis_with_same_occurrence(repo):
    proposal = interrupt_topic_mutation(repo, after="topic_replace")
    edit_synthesis_but_keep_occurrence(repo, proposal.occurrence_id)
    assert_refused(lambda: recover(repo, exact_replay=proposal))


# STUB: AC17
def test_ac17_judgment_or_stale_precondition_leaves_semantic_files_unchanged(repo):
    before = semantic_file_bytes(repo)
    for proposal in (privacy_uncertain_proposal(), stale_precondition_proposal()):
        assert_bounded_refusal(lambda: apply_proposal(repo, proposal))
        assert semantic_file_bytes(repo) == before


# STUB: AC32
def test_ac32_topic_map_merge_rebuilds_distinct_and_refuses_same_topic(repo):
    merged = merge_two_worktrees(repo, distinct_topic_fixture())
    assert merged.map_bytes == rebuild_map_bytes(merged.topic_tree)
    assert_refused(lambda: merge_two_worktrees(repo, same_topic_conflict_fixture()))


# STUB: AC36
def test_ac36_mutation_digest_graph_matches_fixed_cross_platform_vector():
    assert mutation_digest_vector() == load_fixed_vector("mutation-proposal-v1")
    assert "proposal_digest" not in proposal_digest_preimage_fields()
    assert occurrence_digest_fields() == {"evidence_digest"}
    assert not ({"proposal_digest", "topic_postimage_digest"} & occurrence_fields())
```

**Implements:** AC5-AC17, AC31-AC32, AC36

**Touches:** topic/map validators and writer paths, corpus linter, mutation
recovery, and two-worktree fixtures.

**Work:**

1. Implement strict topic/lifecycle/freshness/retirement validation.
2. Implement one-topic mutation with stale preconditions under the shared lock.
3. Deterministically rebuild the complete body-free map and verify prospective
   topic blobs.
4. Refuse multi-topic semantic mutations while supporting deterministic
   ordered-write recovery.
5. Add map-only and same-topic conflict guidance/tests.

**Done when:** one guarded mutation can create/reconcile one topic and publish
a deterministic working-tree map proposal without partial enquiry visibility.

### T4: Implement distillation and terminal dispositions

**Depends on:** T2, T3

**Verification mode:** TDD.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_distillation.py`
- `packs/core/tests/skills/project-knowledge/test_pending_selection.py`
- stub: true

```python
# STUB: AC4
def test_ac4_capture_can_remain_pending_and_non_queryable(repo):
    receipt = capture(repo, valid_capture_request())
    assert pending(repo, receipt) is True
    assert enquire(repo, known_question()).selected_topic_ids == []


# STUB: AC19
def test_ac19_pending_cursor_refuses_partition_drift_without_skipping(repo):
    for mutate in (append_capture, append_disposition, reconcile_journal):
        first_page = pending_page(repo)
        mutate(repo, first_page)
        assert_refused_reason(
            lambda: pending_page(repo, cursor=first_page.cursor), "cursor_stale"
        )
        assert all_preexisting_pending_seen_after_restart(repo)


# STUB: AC4
def test_ac4_pending_drain_is_explicit_scoped_and_receipted(repo):
    request = direct_maintainer_pending_request(scope="packages/core")
    receipt = distill_pending(repo, request)
    assert receipt.selection_mode == "direct-maintainer-pending"
    assert receipt.scope == "packages/core"
    assert set(receipt.counts) == {"pending", "processed", "unresolved"}
    assert_refused(lambda: workflow_request_selecting_pending_corpus(repo))


# STUB: AC15
def test_ac15_distill_records_one_terminal_disposition(repo):
    capture_receipt = capture(repo, valid_capture_request())
    result = distill(repo, promote_proposal(capture_receipt))
    assert result.disposition == "promoted"
    assert terminal_dispositions(repo, capture_receipt) == ["promoted"]


# STUB: AC16
def test_ac16_script_refuses_to_invent_semantic_choice(repo):
    assert_refused(lambda: apply_proposal(repo, ambiguous_split_without_choice()))
    assert topics(repo) == []


# STUB: AC31
def test_ac31_routing_is_a_suggestion_not_an_instruction_edit(repo):
    result = distill(repo, high_friction_route_proposal())
    assert result.suggestion.competency_question == "CQ-ROUTE"
    assert not agent_instruction_files_changed(repo)
```

**Implements:** AC4, AC6-AC9, AC15-AC17, AC19, AC31

**Touches:** distill mode instructions/CLI, proposal contract, behavior evals,
disposition writer, and routing/retirement fixtures.

**Work:**

1. Select bounded pending captures by explicit receipt or cursor-paged project
   scope. Terminal workflows attempt their own receipts; core maintainers own
   later pending drains.
2. Read only bounded candidate topics and named sources before semantic
   reconciliation.
3. Have the agent propose one disposition and optional one-topic mutation;
   deterministic code validates and applies it.
4. Surface contradictions, ambiguous splits, routing, or retirement judgment
   without guessing.
5. Add route-to-agent-map and verification-enforcement suggestion behavior.

**Done when:** every processed observation is explicitly dispositioned and
promotion cannot bypass semantic or canonical-routing boundaries.

### T5: Migrate and activate without dual writers

**Depends on:** T3, T4

**Verification mode:** TDD.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_migration.py`
- stub: true

```python
# STUB: AC20
def test_ac20_migration_accounting_equals_input_rows(repo):
    legacy_rows = mixed_legacy_corpus()
    result = migrate(repo, legacy_rows)
    assert sum(result.counts.values()) == result.input_rows
    assert set(result.counts) == {
        "active_import",
        "needs_review_import",
        "refused",
    }
    assert result.unmapped_ids == []
    occurrences = staged_import_occurrences(repo)
    for row in importable_rows(legacy_rows):
        matches = occurrences_for_legacy_id(occurrences, row["id"])
        assert len(matches) == 1
        assert matches[0].legacy_identity == row["id"]
        assert matches[0].source_provenance == normalized_legacy_source(row["source"])
        assert matches[0].classification == row["kind"]
        assert matches[0].import_disposition in {
            "active_import",
            "needs_review_import",
        }
    assert result.ambiguous_legacy_ids == expected_ambiguous_ids(legacy_rows)
    for row in refused_rows(legacy_rows):
        assert occurrences_for_legacy_id(occurrences, row["id"]) == []
        assert row_body_absent_from_staged_files(repo, row)
    assert legacy_source_bytes(repo) == legacy_rows.original_bytes


# STUB: AC20
def test_ac20_migration_rejects_ambiguous_json_before_staging(repo):
    write_legacy_row(repo, '{"id":"K-0001","id":"K-9999","kind":NaN}')
    result = migrate(repo)
    assert result.diagnostic_fields == {"path", "line", "reason_code"}
    assert not staged_migration_files(repo)


# STUB: AC20
def test_ac20_migration_failures_leave_source_and_staging_unchanged(repo):
    for failure in (
        validation_failure(),
        privacy_failure(),
        accounting_failure(),
        interrupted_staged_write(),
    ):
        reset_legacy_fixture(repo)
        before = legacy_source_bytes(repo)
        assert_bounded_refusal(lambda: migrate(repo, inject=failure))
        assert legacy_source_bytes(repo) == before
        assert not staged_migration_files(repo)


# STUB: AC21
def test_ac21_staged_v1_map_blocks_both_writer_generations(repo):
    stage_v1_without_commit(repo)
    assert_refused(lambda: legacy_append(repo))
    assert_refused(lambda: capture(repo, valid_capture_request()))
    assert_refused(lambda: distill(repo, valid_distillation_proposal()))


# STUB: AC21
def test_ac21_activation_and_bounded_rollback_states(repo):
    assert legacy_append(repo).succeeded
    assert_refused(lambda: capture(repo, valid_capture_request()))
    assert_refused(lambda: enquire(repo, known_question()))

    activation = commit_coherent_v1_topics_and_map(repo)
    assert activation.tree_contains_complete_topic_map()
    assert capture(repo, valid_capture_request()).succeeded
    assert_refused(lambda: legacy_append(repo))

    before = semantic_file_bytes(repo)
    assert_refused_reason(lambda: reverse_migrate(repo), "forward_recovery_required")
    assert semantic_file_bytes(repo) == before
    assert_refused(lambda: legacy_append(repo))


# STUB: AC21
def test_ac21_activation_revert_is_allowed_only_before_first_v1_capture(repo):
    activation = commit_coherent_v1_topics_and_map(repo)
    revert_activation_before_v1_capture(repo, activation)
    assert legacy_append(repo).succeeded
    assert_refused(lambda: capture(repo, valid_capture_request()))
```

**Implements:** AC20-AC21, AC32

**Touches:** migration command, legacy linter adapter, staged output and
activation checks, and disposable-repository fixtures.

**Work:**

1. Validate every legacy row with the shared strict UTF-8 decoder and produce
   complete import accounting. Reject duplicate keys, non-finite numbers,
   non-object rows, unsafe Unicode, and malformed lines before staging; report
   only redacted path, line, and reason code.
2. Preserve legacy identity/provenance as occurrences and surface ambiguous
   grouping.
3. Stage deterministic topics and map while legacy remains canonical.
4. Activate only from one coherent committed v1 snapshot; block staged dual
   writers and make legacy JSONL read-only after activation.
5. Prove activation revert works only before the first persisted v1 capture;
   afterwards refuse reverse migration and require evidence-preserving forward
   recovery.

**Done when:** the existing corpus has a count-preserving reviewed cutover and
there is never an ambiguous active write path.

### T6: Implement committed-only explicit enquiry

**Depends on:** T3, T5

**Verification mode:** TDD + manual CLI invocation.

**Tests:**

- `packs/core/tests/skills/project-knowledge/test_enquiry.py`
- `docs/specs/project-knowledge-foundation/notes/manual-qa.md` records the
  built CLI happy path and abstention output without topic bodies.
- stub: true

```python
# STUB: AC24
def test_ac24_enquiry_reads_only_one_committed_snapshot(repo):
    commit = publish_topics(repo)
    edit_working_tree_topic(repo)
    result = enquire(repo, known_question())
    assert result.receipt.commit_id == commit
    assert "working-tree-only" not in result.rendered


# STUB: AC21, AC24
def test_ac24_enquiry_activates_only_from_complete_migrated_snapshot(repo):
    activation = commit_coherent_migrated_v1_topics_and_map(repo)
    assert enquire(repo, known_question()).reads_commit(activation)
    assert_refused(lambda: legacy_append(repo))


# STUB: AC24
def test_ac24_enquiry_never_opens_observation_journals(repo):
    capture(repo, instruction_shaped_but_safe_observation())
    result = enquire(repo, known_question())
    assert result.selected_topic_ids == []
    assert journal_open_count(repo) == 0


# STUB: AC23
def test_ac23_competency_question_contract_is_exact():
    assert competency_question_ids() == {
        "CQ-ORIENT",
        "CQ-DESIGN",
        "CQ-CHANGE",
        "CQ-DIAGNOSE",
        "CQ-REVIEW",
        "CQ-VERIFY",
        "CQ-OPERATE",
        "CQ-ROUTE",
        "CQ-RETIRE",
    }


# STUB: AC25
def test_ac25_consequential_query_verifies_source_or_abstains(repo):
    result = enquire(repo, consequential_question_with_missing_source())
    assert result.receipt.abstained is True


# STUB: AC23
def test_ac23_skill_query_requires_known_question_and_consequential_default(repo):
    assert_refused(lambda: enquire(repo, skill_query(question_id="CQ-UNKNOWN")))
    result = enquire(repo, skill_query(question_id="CQ-VERIFY", risk=None))
    assert result.receipt.risk == "consequential"


# STUB: AC29
def test_ac29_all_knowledge_code_excludes_prohibited_capabilities_and_imports():
    expected = {
        "capture": {"capture_observation"},
        "distill": {"read_journal", "read_topic", "read_source", "write_knowledge"},
        "enquire": {"read_committed_map", "read_committed_topic", "read_freshness_source"},
    }
    assert all_mode_capabilities() == expected
    assert not (
        {"network", "command", "credential", "authorization", "permission"}
        & union_capabilities(expected)
    )
    assert_no_prohibited_imports(project_knowledge_module(), knowledge_store_module())
```

**Implements:** AC21, AC23-AC26, AC29

**Touches:** enquire mode/CLI, Git-tree reader, deterministic routing,
freshness verifier, evidence envelope, receipt, and adversarial fixtures.

**Work:**

1. Resolve `HEAD` once and verify the complete topic-map/blob set without
   opening every body.
2. Filter project, scope, lifecycle, privacy, and freshness before ranking.
3. Open bounded selected bodies and verify consequential owning sources.
4. Render delimited evidence and receipts with explicit abstention.
5. Prove journals, working-tree topics, and instruction-shaped bodies cannot
   create authority or a mutation path.

**Done when:** explicit enquiry is useful, bounded, attributable, and cannot
observe or amplify unpromoted evidence.

### T7: Cut work-loop over through the public capture seam

**Depends on:** T4, T5, T6

**Verification mode:** TDD + manual skill journey.

**Tests:**

- `packs/core/tests/skills/work-loop/test_project_knowledge_handoff.py`
- `docs/specs/project-knowledge-foundation/notes/manual-qa.md` records the
  projected skill journey with core present/absent.
- stub: true

```python
# STUB: AC22
def test_ac22_work_loop_calls_capture_then_terminal_distill():
    trace = run_work_loop_with_one_admitted_note()
    assert trace.mode_calls == ["project-knowledge --capture", "project-knowledge --distill"]
    assert trace.distill_request.selection_mode == "workflow-receipts"
    assert trace.distill_request.capture_ids == trace.capture_receipt.capture_ids
    assert trace.surfaces_unresolved_receipts()
    assert_refused(lambda: trace.replace_selection_with("direct-maintainer-pending"))
    assert_refused(lambda: trace.add_guessed_capture_id())


# STUB: AC28
def test_ac28_missing_core_creates_no_fallback_file(repo):
    result = run_work_loop_without_core(repo)
    assert result.named_skip == "project-knowledge unavailable"
    assert not fallback_candidate_files(repo)


# STUB: AC30
def test_ac30_closeout_question_is_unchanged():
    assert closeout_question_bytes() == CORE_2_5_9_QUESTION_BYTES
```

**Implements:** AC22, AC28, AC30

**Touches:** canonical work-loop skill, private integration fixtures,
optional pack handoff metadata, projections, and closeout byte pin.

**Work:**

1. Replace the legacy append with semantic-gate triage and an agent-mediated
   `project-knowledge --capture` handoff.
2. At terminal gates, attempt `--distill` for only the gate's receipts;
   unresolved judgment remains pending and does not invalidate capture.
3. Make missing core a named skip with no fallback store.
4. Keep the 2.5.9 closeout question byte-identical.
5. Return every knowledge diff through the next verification/review barrier.

**Done when:** the first producer uses the shared seam and no automatic capture
is broadened beyond work-loop.

### T8: Complete delivery, docs, and end-to-end proof

**Depends on:** T1-T7

**Verification mode:** Goal-based checks + manual end-to-end QA.

**Tests:**

- no stub (goal/manual mode).
- `docs/specs/project-knowledge-foundation/notes/manual-qa.md` records AC30's
  private-name scan as pass/fail only and AC34's end-to-end outputs.
- AC33: goal check proves no retention/compaction command or per-event deletion
  path exists and closed partitions remain byte-identical.
- AC35: `docs/specs/project-knowledge-foundation/notes/manual-qa.md` records
  version/changelog/manifest/eval/projection parity and full gate/reviewer
  results.

**Implements:** AC27-AC30, AC33-AC35

**Touches:** pack/version manifests, changelog, READMEs, architecture/guides,
generated projections, evals, and manual QA notes.

**Work:**

1. Update current/target and adopter documentation, including scratch loss,
   journal durability, retention deferral, retirement, and no authority
   amplification.
2. Add mode activation/near-miss and semantic judge evals.
3. Run the complete disposable-repository journey and record bounded evidence.
4. Run build, lint, catalogue, security, adversarial, and quality gates; harden
   until clean.
5. Update version authorities and changelog only with the implementing change.

**Goal-based evidence:** AC34 requires the recorded end-to-end journey; AC35
requires release and generated-surface parity, so neither has a useful isolated
red unit stub.

**Done when:** all acceptance criteria have evidence and the implementation is
ready for approval and commit through the repository's normal workflow.

## Sequencing

```text
T1 contracts + mode isolation
  -> T2 capture journal + writer safety
  -> T3 topics + map
  -> T4 distillation + dispositions
  -> T5 migration + activation
  -> T6 committed enquiry
  -> T7 work-loop cutover
  -> T8 delivery
```

Do not begin T7 until T1-T6 are green and their security construction tests
pass. Non-work-loop workflow integrations are separate later specs.

## Rollout and rollback

1. Ship migration and new runtime dormant in legacy-only repositories.
2. Stage and review a complete migrated tree; staged activation blocks writes.
3. Commit the coherent v1 map/topics to activate the new path. Observation
   journals begin with the first post-activation capture; legacy imports are
   occurrences, not duplicated events.
4. Cut work-loop over in the same release and make legacy JSONL read-only.
5. Before any v1-only capture is persisted, rollback may revert the activation
   commit. Afterwards automatic reverse migration refuses without changing
   files; recovery is a reviewed forward change that preserves journals/topics
   and never resumes legacy append.

## Risks

- **Persisted injection/privacy exposure:** refuse uncertainty before append;
  never query journals; keep dispositions bounded.
- **Lock or recovery defect:** one global lock, ownership identity, same-dir
  replace, ordered idempotent postimages, fault injection, no automatic retry.
- **Mode authority bleed:** separate references and helper registries;
  construction tests fail on cross-mode access.
- **Journal growth:** bounded monthly partitions and no silent retention;
  measure before a separately reviewed partition policy.
- **Topic poisoning or staleness:** provenance, source-relative freshness,
  committed-only enquiry, abstention, and ordinary Git review.
- **Workflow ceremony:** only semantic gates, only new explicit scratch, and no
  automatic integrations beyond work-loop in this slice.

## Changelog

- 2026-08-13: Reframed the plan around durable captured-observation journals,
  one progressive `project-knowledge` skill, mode-specific capability surfaces,
  terminal dispositions, and work-loop cutover only after retrieval and safety
  boundaries are enforceable.
