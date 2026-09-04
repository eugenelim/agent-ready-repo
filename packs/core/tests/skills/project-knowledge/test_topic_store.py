from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    valid_capture_request,
)


@pytest.fixture
def store():
    return load_knowledge_store_module()


@pytest.fixture
def repo(tmp_path: Path, store) -> Path:
    return initialize_empty_v1_repo(tmp_path, store)


def valid_topic(**overrides: Any) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "schema_version": "knowledge-topic.v1",
        "topic_key": "contracts/public-contracts",
        "title": "Public contracts are the durable handoff",
        "synthesis": {
            "kind": "pattern",
            "body": "Prefer the repo-owned contract before adding a local format.",
        },
        "scopes": ["packs/core"],
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "audience": "project",
        "lifecycle": "active",
        "freshness": {
            "state": "fresh",
            "checked_at": "2026-08-13T12:40:00Z",
        },
        "owning_source": {
            "path": "contracts/jsonschema/knowledge-captured-observation.schema.json",
            "digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "a" * 64,
                "byte_length": 100,
            },
        },
        "supporting_sources": [],
        "occurrences": [
            {
                "capture_id": "kco-202608-" + "b" * 64,
                "mutation_id": "0" * 64,
                "producer": "work-loop",
                "semantic_gate": "verified-slice",
                "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
                "evidence_digest": {
                    "kind": "sha256-bytes-v1",
                    "sha256": "c" * 64,
                    "byte_length": 42,
                },
                "scope": "packs/core",
                "observed_at": "2026-08-13T12:34:56Z",
                "reviewed_disposition": "promoted",
            }
        ],
    }
    topic.update(overrides)
    return topic


def mutation_proposal(**overrides: Any) -> dict[str, Any]:
    proposal: dict[str, Any] = {
        "schema_version": "knowledge-mutation-proposal.v1",
        "capture_id": "kco-202608-" + "b" * 64,
        "topic_key": "contracts/public-contracts",
        "title": "Public contracts are the durable handoff",
        "synthesis": {
            "kind": "pattern",
            "body": "Prefer the repo-owned contract before adding a local format.",
        },
        "scopes": ["packs/core"],
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "owning_source": {
            "path": "contracts/jsonschema/knowledge-captured-observation.schema.json",
            "digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "a" * 64,
                "byte_length": 100,
            },
        },
        "supporting_sources": [],
        "occurrence": {
            "producer": "work-loop",
            "semantic_gate": "verified-slice",
            "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
            "evidence_digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "c" * 64,
                "byte_length": 42,
            },
            "scope": "packs/core",
            "observed_at": "2026-08-13T12:34:56Z",
        },
        "terminal_disposition": {
            "disposition": "promoted",
            "reason_code": "promoted_to_topic",
            "recorded_at": "2026-08-13T12:41:00Z",
        },
        "expected_topic_digest": None,
    }
    proposal.update(overrides)
    return proposal


def _semantic_bytes(repo: Path) -> bytes:
    knowledge = repo / "docs" / "knowledge"
    return b"".join(path.read_bytes() for path in sorted(knowledge.rglob("*.json")))


def _commit(repo: Path) -> None:
    subprocess.run(["git", "add", "docs/knowledge"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "test: publish knowledge"], cwd=repo, check=True)


def _proposal_with_pending(
    repo: Path,
    store,
    *,
    existing_topic_bytes: bytes | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    request = valid_capture_request(
        lesson=overrides.pop(
            "lesson",
            "Prefer the repo-owned contract before adding a local format.",
        )
    )
    request["observed_at"] = "2026-08-13T12:34:56Z"
    receipt = store.seed_previously_admitted_capture(repo, request)
    return store.complete_mutation_proposal(
        mutation_proposal(capture_id=receipt["capture_id"], **overrides),
        existing_topic_bytes=existing_topic_bytes,
    )


def _hand_built_proposal_with_pending(
    repo: Path, store, **overrides: Any
) -> dict[str, Any]:
    receipt = store.seed_previously_admitted_capture(repo, valid_capture_request())
    proposal = mutation_proposal(capture_id=receipt["capture_id"], **overrides)
    topic = store._topic_from_proposal(proposal)
    proposal["topic_postimage_digest"] = store.PK.digest_bytes(
        store._pretty_json_bytes(topic)
    )
    proposal["proposal_digest"] = store.PK.digest_bytes(
        store._canonical_json_bytes(store._proposal_without_derived(proposal))
    )
    return proposal


def test_ac10_topic_is_pretty_json_and_not_an_event_stream(repo: Path, store) -> None:
    path = store.write_topic(repo, valid_topic())
    assert json.loads(path.read_text(encoding="utf-8"))["topic_key"] == "contracts/public-contracts"
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert "\n  " in path.read_text(encoding="utf-8")
    assert path.suffix == ".json"


def test_ac12_persisted_topic_and_proposal_paths_are_canonical(repo: Path, store) -> None:
    topic = valid_topic(scopes=[r"packs\core"])
    topic["owning_source"]["path"] = r"contracts\schema.json"
    topic["occurrences"][0]["source"]["path"] = r"packs\core\AGENTS.md"
    topic["occurrences"][0]["scope"] = "cafe\u0301/component"
    path = store.write_topic(repo, topic)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["scopes"] == ["packs/core"]
    assert persisted["owning_source"]["path"] == "contracts/schema.json"
    assert persisted["occurrences"][0]["source"]["path"] == "packs/core/AGENTS.md"
    assert persisted["occurrences"][0]["scope"] == "caf\u00e9/component"

    proposal = mutation_proposal(scopes=[r"packs\core"])
    proposal["owning_source"]["path"] = r"contracts\schema.json"
    proposal["occurrence"]["scope"] = r"packs\core"
    completed = store.complete_mutation_proposal(proposal)
    assert completed["scopes"] == ["packs/core"]
    assert completed["owning_source"]["path"] == "contracts/schema.json"
    assert completed["occurrence"]["scope"] == "packs/core"


@pytest.mark.parametrize(
    "target",
    (
        "scope",
        "owning",
        "supporting",
        "occurrence_source",
        "occurrence_scope",
        "successor",
        "non_effective_successor",
    ),
)
def test_ac18_topic_repository_paths_refuse_private_identifiers(
    repo: Path, store, target: str
) -> None:
    topic = valid_topic()
    private_path = "docs/user@example.com/notes.md"
    if target == "scope":
        topic["scopes"] = [private_path]
    elif target == "owning":
        topic["owning_source"]["path"] = private_path
    elif target == "supporting":
        topic["supporting_sources"] = [
            {"path": private_path, "digest": topic["owning_source"]["digest"]}
        ]
    elif target == "occurrence_source":
        topic["occurrences"][0]["source"]["path"] = private_path
    elif target == "occurrence_scope":
        topic["occurrences"][0]["scope"] = private_path
    else:
        topic["lifecycle"] = "retired"
        topic["freshness"] = {
            "state": "retired",
            "checked_at": "2026-08-13T12:40:00Z",
        }
        topic["retirement"] = {
            "reason": "obsolete" if target == "non_effective_successor" else "canonicalized",
            "successors": [private_path],
            "coverage_verified": target != "non_effective_successor",
        }

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_topic(repo, topic)
    assert refused.value.diagnostic["reason_code"] == "privacy"


@pytest.mark.parametrize(
    "target", ("scope", "owning", "supporting", "occurrence_source", "occurrence_scope")
)
def test_ac18_proposal_repository_paths_refuse_private_identifiers(
    store, target: str
) -> None:
    proposal = mutation_proposal()
    private_path = "docs/user@example.com/notes.md"
    if target == "scope":
        proposal["scopes"] = [private_path]
    elif target == "owning":
        proposal["owning_source"]["path"] = private_path
    elif target == "supporting":
        proposal["supporting_sources"] = [
            {"path": private_path, "digest": proposal["owning_source"]["digest"]}
        ]
    elif target == "occurrence_source":
        proposal["occurrence"]["source"]["path"] = private_path
    else:
        proposal["occurrence"]["scope"] = private_path

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.complete_mutation_proposal(proposal)
    assert refused.value.diagnostic["reason_code"] == "privacy"


def test_ac18_domain_shaped_repository_paths_remain_valid(repo: Path, store) -> None:
    domain_path = "docs/fixtures/example.com/contract.json"
    topic = valid_topic(scopes=[domain_path])
    topic["owning_source"]["path"] = domain_path
    topic["occurrences"][0]["source"]["path"] = domain_path
    topic["occurrences"][0]["scope"] = domain_path
    assert store.write_topic(repo, topic).is_file()

    proposal = mutation_proposal(scopes=[domain_path])
    proposal["owning_source"]["path"] = domain_path
    proposal["occurrence"]["source"]["path"] = domain_path
    proposal["occurrence"]["scope"] = domain_path
    assert store.complete_mutation_proposal(proposal)["scopes"] == [domain_path]


@pytest.mark.parametrize("surface", ("topic", "proposal"))
@pytest.mark.parametrize(
    "private_key",
    (
        "contracts/aaaaaaaa-bbbb-7ccc-8ddd-eeeeeeeeeeee",
        "contracts/aaaaaaaa-bbbb-8ccc-8ddd-eeeeeeeeeeee",
    ),
)
def test_ac18_topic_keys_refuse_private_identifiers(
    repo: Path, store, surface: str, private_key: str
) -> None:
    with pytest.raises(store.KnowledgeStoreError) as refused:
        if surface == "topic":
            store.write_topic(repo, valid_topic(topic_key=private_key))
        else:
            store.complete_mutation_proposal(mutation_proposal(topic_key=private_key))
    assert refused.value.diagnostic["reason_code"] == "privacy"


@pytest.mark.parametrize("field", ("producer", "semantic_gate"))
def test_ac18_topic_occurrence_metadata_refuses_private_identifiers(
    repo: Path, store, field: str
) -> None:
    topic = valid_topic()
    topic["occurrences"][0][field] = "aaaaaaaa-bbbb-8ccc-8ddd-eeeeeeeeeeee"

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_topic(repo, topic)
    assert refused.value.diagnostic["reason_code"] == "privacy"


def test_ac18_mutation_reason_refuses_private_identifiers(store) -> None:
    proposal = mutation_proposal()
    proposal["terminal_disposition"]["reason_code"] = (
        "aaaaaaaa-bbbb-8ccc-8ddd-eeeeeeeeeeee"
    )

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.complete_mutation_proposal(proposal)
    assert refused.value.diagnostic["reason_code"] == "privacy"


@pytest.mark.parametrize("topic_key", ("con", "area/aux", "LPT1", "com9"))
def test_ac12_topic_keys_refuse_windows_reserved_filenames(
    repo: Path, store, topic_key: str
) -> None:
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_topic(repo, valid_topic(topic_key=topic_key))
    assert refused.value.diagnostic["reason_code"] == "confinement"


def test_ac6_topic_occurrences_refuse_malformed_provenance(repo: Path, store) -> None:
    bad_capture = valid_topic()
    bad_capture["occurrences"][0]["capture_id"] = "kco-invalid"
    promoted_with_legacy = valid_topic()
    promoted_with_legacy["occurrences"][0]["legacy_identity"] = "K-1001"
    promoted_with_legacy["occurrences"][0]["legacy_source"] = "commit abc123"

    for topic in (bad_capture, promoted_with_legacy):
        with pytest.raises(store.KnowledgeStoreError) as refused:
            store.write_topic(repo, topic)
        assert refused.value.diagnostic["reason_code"] == "strict_parse"


def test_ac11_map_is_body_free_and_byte_deterministic(repo: Path, store) -> None:
    store.write_topic(repo, valid_topic())
    first = store.rebuild_topic_map(repo)
    second = store.rebuild_topic_map(repo)
    assert first == second
    assert b"synthesis" not in first
    assert b"occurrences" not in first
    parsed = json.loads(first)
    assert parsed["entries"][0]["topic_key"] == "contracts/public-contracts"
    assert parsed["entries"][0]["blob"]["kind"] == "git-blob-v1"


@pytest.mark.parametrize(
    "budget_name",
    ("topic_bytes", "topic_corpus_bytes", "topic_files", "map_entries", "map_bytes"),
)
def test_ac19_live_and_staged_map_rebuilds_share_corpus_budgets(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch, budget_name: str
) -> None:
    store.write_topic(repo, valid_topic())
    store.write_topic(
        repo,
        valid_topic(
            topic_key="contracts/secondary-contract",
            title="Secondary contract handoff",
        ),
    )
    monkeypatch.setitem(store.PK._BUDGETS, budget_name, 1)

    with pytest.raises(store.KnowledgeStoreError) as live_refused:
        store.rebuild_topic_map(repo)
    assert live_refused.value.diagnostic["reason_code"] == "journal_capacity"
    with pytest.raises(store.KnowledgeStoreError) as staged_refused:
        store.rebuild_map_bytes(repo / "docs/knowledge", repository_root=repo)
    assert staged_refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac12_topic_rebuild_refuses_symlinked_topics_root(repo: Path, store) -> None:
    topics = repo / "docs/knowledge/topics"
    target = repo / "outside-topics"
    target.mkdir()
    topic_path = target / "contracts" / "public-contracts.json"
    topic_path.parent.mkdir()
    topic_path.write_text(
        json.dumps(valid_topic(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        topics.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.rebuild_topic_map(repo)

    assert refused.value.diagnostic["reason_code"] == "confinement"


def test_ac14_interruption_never_changes_committed_query_snapshot(repo: Path, store) -> None:
    proposal = _proposal_with_pending(repo, store)
    store.apply_guarded_mutation(repo, proposal)
    _commit(repo)
    before = store.enquire_head(repo)
    updated = _proposal_with_pending(
        repo,
        store,
        lesson="Use the published contract as the durable handoff.",
        synthesis={
            "kind": "pattern",
            "body": "Use the published contract as the durable handoff.",
        },
        expected_topic_digest=store.topic_digest_for_key(repo, "contracts/public-contracts"),
        existing_topic_bytes=store.topic_path_for_key(
            repo, "contracts/public-contracts"
        ).read_bytes(),
    )
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, updated, interrupt_after="topic_replace")
    assert store.enquire_head(repo) == before


def test_ac14_promoted_disposition_requires_topic_and_matching_map(repo: Path, store) -> None:
    for boundary in ("topic", "map", "disposition"):
        isolated = repo / boundary
        isolated.mkdir()
        proposal = _proposal_with_pending(isolated, store)
        with pytest.raises(store.KnowledgeStoreError):
            store.apply_guarded_mutation(isolated, proposal, interrupt_after=boundary)
        state = store.recover_guarded_mutation(isolated, proposal)
        assert state["promoted_implies_topic_and_map"] is True


def test_ac14_recovery_refuses_changed_synthesis_with_same_occurrence(repo: Path, store) -> None:
    proposal = _proposal_with_pending(repo, store)
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, proposal, interrupt_after="topic")
    path = store.topic_path_for_key(repo, proposal["topic_key"])
    topic = json.loads(path.read_text(encoding="utf-8"))
    topic["synthesis"]["body"] = "Tampered synthesis."
    path.write_text(json.dumps(topic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.recover_guarded_mutation(repo, proposal)
    assert refused.value.diagnostic["reason_code"] == "postimage_mismatch"


@pytest.mark.parametrize("verification_path", ("recovery", "promoted_state"))
@pytest.mark.parametrize("mismatched_field", ("capture_id", "mutation_id"))
def test_ac14_recovery_requires_the_promoted_occurrence(
    repo: Path, store, verification_path: str, mismatched_field: str
) -> None:
    topic_path = store.write_topic(repo, valid_topic())
    topic_bytes = topic_path.read_bytes()
    proposal = _proposal_with_pending(
        repo,
        store,
        expected_topic_digest=store.PK.digest_bytes(topic_bytes),
        existing_topic_bytes=topic_bytes,
    )
    topic = json.loads(topic_bytes)
    if mismatched_field == "capture_id":
        topic["occurrences"][-1]["mutation_id"] = store._mutation_id(proposal)
    else:
        topic["occurrences"][-1]["capture_id"] = proposal["capture_id"]
    forged_topic_bytes = store._pretty_json_bytes(store.validate_topic(topic))
    topic_path.write_bytes(forged_topic_bytes)
    store.rebuild_topic_map(repo)
    proposal["topic_postimage_digest"] = store.PK.digest_bytes(forged_topic_bytes)
    proposal["proposal_digest"] = store.PK.digest_bytes(
        store._canonical_json_bytes(store._proposal_without_derived(proposal))
    )

    if verification_path == "promoted_state":
        store._write_disposition(repo, proposal)
        _partition, _capture, disposition = store._find_capture(
            repo, proposal["capture_id"]
        )
        with pytest.raises(store.KnowledgeStoreError) as refused:
            store._verify_promoted_state(repo, proposal, disposition)
    else:
        with pytest.raises(store.KnowledgeStoreError) as refused:
            store.recover_guarded_mutation(repo, proposal)

    assert refused.value.diagnostic["reason_code"] == "postimage_mismatch"


@pytest.mark.parametrize(
    "mismatched_field", ("lifecycle", "lifecycle_only", "retirement")
)
def test_ac14_recovery_requires_explicit_topic_state_to_match(
    repo: Path, store, mismatched_field: str
) -> None:
    # `lifecycle_only` is the case that isolates the lifecycle comparison. The
    # `lifecycle` case forges a retirement record too, so the retirement
    # comparison alone still refuses it and the lifecycle guard can be deleted
    # without reddening anything.
    original_retirement = {
        "reason": "enforced",
        "successors": ["contracts/original.json"],
        "coverage_verified": True,
    }
    proposal = _proposal_with_pending(
        repo,
        store,
        lifecycle="retired" if mismatched_field == "retirement" else "active",
        **(
            {"retirement": original_retirement}
            if mismatched_field == "retirement"
            else {}
        ),
    )
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, proposal, interrupt_after="topic")
    topic_path = store.topic_path_for_key(repo, proposal["topic_key"])
    actual_topic_bytes = topic_path.read_bytes()
    conflicting = copy.deepcopy(proposal)
    if mismatched_field == "lifecycle_only":
        # No retirement on either side, so only the lifecycle comparison can refuse.
        conflicting["lifecycle"] = "needs_review"
    elif mismatched_field == "lifecycle":
        conflicting["lifecycle"] = "retired"
        conflicting["retirement"] = original_retirement
    else:
        conflicting["retirement"] = {
            "reason": "merged",
            "successors": ["contracts/replacement.json"],
            "coverage_verified": True,
        }
    conflicting["topic_postimage_digest"] = store.PK.digest_bytes(actual_topic_bytes)
    conflicting["proposal_digest"] = store.PK.digest_bytes(
        store._canonical_json_bytes(store._proposal_without_derived(conflicting))
    )

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.recover_guarded_mutation(repo, conflicting)

    assert store._mutation_id(conflicting) == store._mutation_id(proposal)
    assert refused.value.diagnostic["reason_code"] == "postimage_mismatch"


def test_ac14_recovery_resumes_update_before_topic_replacement(repo: Path, store) -> None:
    first = _proposal_with_pending(repo, store)
    store.apply_guarded_mutation(repo, first)
    topic_path = store.topic_path_for_key(repo, first["topic_key"])
    existing_topic_bytes = topic_path.read_bytes()
    update = _proposal_with_pending(
        repo,
        store,
        lesson="Keep the full evidence history when recovery resumes an update.",
        synthesis={
            "kind": "pattern",
            "body": "Keep the full evidence history when recovery resumes an update.",
        },
        expected_topic_digest=store.PK.digest_bytes(existing_topic_bytes),
        existing_topic_bytes=existing_topic_bytes,
    )

    state = store.recover_guarded_mutation(repo, update)

    topic = json.loads(topic_path.read_bytes())
    assert state["promoted_implies_topic_and_map"] is True
    assert store.PK.digest_bytes(topic_path.read_bytes()) == update[
        "topic_postimage_digest"
    ]
    assert topic["occurrences"][-1]["capture_id"] == update["capture_id"]
    assert topic["occurrences"][-1]["mutation_id"] == store._mutation_id(update)


def test_ac14_recovery_revalidates_committed_activation(repo: Path, store) -> None:
    proposal = _proposal_with_pending(repo, store)
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, proposal, interrupt_after="topic")
    subprocess.run(
        ["git", "rm", "docs/knowledge/topics.index.json"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "test: remove activation map"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.recover_guarded_mutation(repo, proposal)

    assert refused.value.diagnostic["reason_code"] == "staged_dual_writer"
    assert all(
        event["event_type"] != "observation.dispositioned"
        for partition in store._observation_partitions(repo)
        for event in store._read_events(store._journal_path(repo, partition), partition)
    )


def test_ac17_worktree_activation_map_refuses_symlink(repo: Path, store) -> None:
    map_path = repo / "docs/knowledge/topics.index.json"
    target = repo / "map-target.json"
    target.write_bytes(map_path.read_bytes())
    map_path.unlink()
    try:
        map_path.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store._coherent_worktree_map(repo)

    assert refused.value.diagnostic["reason_code"] == "confinement"


def test_ac21_current_tree_snapshot_refuses_symlink_map(repo: Path, store) -> None:
    map_path = repo / "docs/knowledge/topics.index.json"
    target = repo / "snapshot-map-target.json"
    target.write_bytes(map_path.read_bytes())
    map_path.unlink()
    try:
        map_path.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.current_tree_snapshot(repo)

    assert refused.value.diagnostic["reason_code"] == "confinement"


def test_ac19_topic_precondition_digest_refuses_oversized_file(repo: Path, store) -> None:
    path = store.topic_path_for_key(repo, "contracts/public-contracts")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * (store.budget_contract()["topic_bytes"] + 1))

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.topic_digest_for_key(repo, "contracts/public-contracts")

    assert refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac14_recovery_refuses_oversized_topic_before_comparison(repo: Path, store) -> None:
    proposal = _proposal_with_pending(repo, store)
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, proposal, interrupt_after="topic")
    path = store.topic_path_for_key(repo, proposal["topic_key"])
    path.write_bytes(path.read_bytes() + b"x" * store.budget_contract()["topic_bytes"])

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.recover_guarded_mutation(repo, proposal)

    assert refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac17_judgment_or_stale_precondition_leaves_semantic_files_unchanged(
    repo: Path, store
) -> None:
    topic_path = store.write_topic(repo, valid_topic())
    base_bytes = topic_path.read_bytes()
    stale = _proposal_with_pending(
        repo,
        store,
        expected_topic_digest=store.PK.digest_bytes(base_bytes),
        existing_topic_bytes=base_bytes,
    )
    changed_topic = valid_topic()
    changed_topic["synthesis"]["body"] = "The base changed after proposal completion."
    store.write_topic(repo, changed_topic)
    store.rebuild_topic_map(repo)
    before = _semantic_bytes(repo)
    unsafe = store.complete_mutation_proposal(mutation_proposal())
    unsafe["synthesis"]["body"] = "Contact user@example.com before promotion."
    for proposal, reason_code in ((unsafe, "privacy"), (stale, "postimage_mismatch")):
        with pytest.raises(store.KnowledgeStoreError) as refused:
            store.apply_guarded_mutation(repo, proposal)
        assert refused.value.diagnostic["reason_code"] == reason_code
        assert _semantic_bytes(repo) == before

    with pytest.raises(store.KnowledgeStoreError) as unknown_field:
        store.apply_guarded_mutation(
            repo,
            store.complete_mutation_proposal(mutation_proposal())
            | {"refusal_reason": "privacy"},
        )
    assert unknown_field.value.diagnostic["reason_code"] == "strict_parse"


def test_promoted_update_accumulates_occurrences_and_returns_applied_id(
    repo: Path, store
) -> None:
    first = _proposal_with_pending(repo, store)
    first_result = store.apply_guarded_mutation(repo, first)
    topic_path = store.topic_path_for_key(repo, first["topic_key"])
    existing_topic_bytes = topic_path.read_bytes()
    second = _proposal_with_pending(
        repo,
        store,
        lesson="Use the complete evidence history when revising a topic.",
        synthesis={
            "kind": "pattern",
            "body": "Use the complete evidence history when revising a topic.",
        },
        expected_topic_digest=store.PK.digest_bytes(existing_topic_bytes),
        existing_topic_bytes=existing_topic_bytes,
    )

    second_result = store.apply_guarded_mutation(repo, second)

    topic = json.loads(topic_path.read_bytes())
    mutation_ids = [occurrence["mutation_id"] for occurrence in topic["occurrences"]]
    assert mutation_ids == [first_result["mutation_id"], second_result["mutation_id"]]
    assert second_result["mutation_id"] == store._mutation_id(second)
    assert second_result["mutation_id"] != first_result["mutation_id"]


def test_promoted_update_preserves_retired_lifecycle_by_default(
    repo: Path, store
) -> None:
    retirement = {
        "reason": "enforced",
        "successors": ["contracts/successor.json"],
        "coverage_verified": True,
    }
    first = _proposal_with_pending(
        repo,
        store,
        lifecycle="retired",
        retirement=retirement,
    )
    store.apply_guarded_mutation(repo, first)
    topic_path = store.topic_path_for_key(repo, first["topic_key"])
    existing_topic_bytes = topic_path.read_bytes()
    update = _proposal_with_pending(
        repo,
        store,
        lesson="Retired knowledge can still gain supporting evidence.",
        synthesis={
            "kind": "pattern",
            "body": "Retired knowledge can still gain supporting evidence.",
        },
        expected_topic_digest=store.PK.digest_bytes(existing_topic_bytes),
        existing_topic_bytes=existing_topic_bytes,
    )

    store.apply_guarded_mutation(repo, update)

    topic = json.loads(topic_path.read_bytes())
    assert topic["lifecycle"] == "retired"
    assert topic["retirement"] == retirement


def test_promoted_update_materializes_retired_lifecycle_for_replacement_retirement(
    repo: Path, store
) -> None:
    first_retirement = {
        "reason": "enforced",
        "successors": ["contracts/original.json"],
        "coverage_verified": True,
    }
    first = _proposal_with_pending(
        repo,
        store,
        lifecycle="retired",
        retirement=first_retirement,
    )
    store.apply_guarded_mutation(repo, first)
    topic_path = store.topic_path_for_key(repo, first["topic_key"])
    existing_topic_bytes = topic_path.read_bytes()
    replacement_retirement = {
        "reason": "merged",
        "successors": ["contracts/replacement.json"],
        "coverage_verified": True,
    }
    update = _proposal_with_pending(
        repo,
        store,
        lesson="Retired knowledge can point to its replacement.",
        synthesis={
            "kind": "pattern",
            "body": "Retired knowledge can point to its replacement.",
        },
        retirement=replacement_retirement,
        expected_topic_digest=store.PK.digest_bytes(existing_topic_bytes),
        existing_topic_bytes=existing_topic_bytes,
    )

    assert update["lifecycle"] == "retired"
    store.apply_guarded_mutation(repo, update)

    topic = json.loads(topic_path.read_bytes())
    assert topic["lifecycle"] == "retired"
    assert topic["retirement"] == replacement_retirement


def test_mutation_completion_refuses_existing_topic_digest_mismatch(
    repo: Path, store
) -> None:
    topic_path = store.write_topic(repo, valid_topic())
    existing_topic_bytes = topic_path.read_bytes()
    proposal = mutation_proposal(
        expected_topic_digest={
            "kind": "sha256-bytes-v1",
            "sha256": "d" * 64,
            "byte_length": 1,
        }
    )

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.complete_mutation_proposal(
            proposal,
            existing_topic_bytes=existing_topic_bytes,
        )

    assert refused.value.diagnostic["reason_code"] == "postimage_mismatch"


@pytest.mark.parametrize(
    ("lifecycle", "retirement"),
    (
        ("unknown", None),
        (
            "retired",
            {
                "reason": "enforced",
                "successors": [],
                "coverage_verified": False,
            },
        ),
    ),
)
def test_mutation_completion_validates_lifecycle_and_retirement(
    store, lifecycle: str, retirement: dict[str, Any] | None
) -> None:
    proposal = mutation_proposal(lifecycle=lifecycle)
    if retirement is not None:
        proposal["retirement"] = retirement

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.complete_mutation_proposal(proposal)

    assert refused.value.diagnostic["reason_code"] == "strict_parse"


@pytest.mark.parametrize(
    ("lifecycle", "retirement"),
    (
        ("unknown", None),
        (
            "retired",
            {
                "reason": "enforced",
                "successors": [],
                "coverage_verified": False,
            },
        ),
    ),
    ids=("invalid-lifecycle", "invalid-retirement"),
)
def test_guarded_mutation_validates_hand_built_lifecycle_and_retirement(
    repo: Path,
    store,
    monkeypatch: pytest.MonkeyPatch,
    lifecycle: str,
    retirement: dict[str, Any] | None,
) -> None:
    overrides: dict[str, Any] = {"lifecycle": lifecycle}
    if retirement is not None:
        overrides["retirement"] = retirement
    proposal = _hand_built_proposal_with_pending(repo, store, **overrides)
    monkeypatch.setattr(store, "validate_topic", lambda topic: topic)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.apply_guarded_mutation(repo, proposal)

    assert refused.value.diagnostic["reason_code"] == "strict_parse"


def test_mutation_completion_refuses_occurrence_overflow(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(store.PK._BUDGETS, "topic_bytes", 1_000_000)
    existing_topic = valid_topic()
    existing_topic["occurrences"] = [
        copy.deepcopy(existing_topic["occurrences"][0])
        for _ in range(store.budget_contract()["occurrences_per_topic"])
    ]
    topic_path = store.write_topic(repo, existing_topic)
    existing_topic_bytes = topic_path.read_bytes()
    proposal = mutation_proposal(
        expected_topic_digest=store.PK.digest_bytes(existing_topic_bytes)
    )

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.complete_mutation_proposal(
            proposal,
            existing_topic_bytes=existing_topic_bytes,
        )

    assert refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac36_mutation_digest_graph_matches_fixed_cross_platform_vector(store) -> None:
    proposal = store.complete_mutation_proposal(mutation_proposal())
    vector = store.mutation_digest_vector(proposal)
    assert vector == store.load_fixed_vector("mutation-proposal-v1")
    assert "proposal_digest" not in store.proposal_digest_preimage_fields()
    assert "topic_postimage_digest" in store.proposal_digest_preimage_fields()
    assert store.occurrence_digest_fields() == {"evidence_digest"}
    assert not ({"proposal_digest", "topic_postimage_digest"} & store.occurrence_fields())


def test_ac36_proposal_digest_binds_topic_postimage(repo: Path, store) -> None:
    proposal = _proposal_with_pending(repo, store)
    proposal["topic_postimage_digest"] = {
        "kind": "sha256-bytes-v1",
        "sha256": "e" * 64,
        "byte_length": 1,
    }
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.apply_guarded_mutation(repo, proposal)
    assert refused.value.diagnostic["reason_code"] == "strict_parse"


def test_ac36_sha256_git_repository_uses_sha256_blob_identity(
    tmp_path: Path, store
) -> None:
    repo = tmp_path / "sha256-repo"
    repo.mkdir()
    result = subprocess.run(
        ["git", "init", "--object-format=sha256"],
        cwd=repo,
        capture_output=True,
    )
    if result.returncode != 0:
        pytest.skip("installed Git does not support SHA-256 repositories")
    subprocess.run(
        ["git", "config", "user.email", "user@example.com"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Example User"], cwd=repo, check=True
    )
    (repo / "docs/knowledge").mkdir(parents=True)
    store.rebuild_topic_map(repo)
    subprocess.run(["git", "add", "docs/knowledge/topics.index.json"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test: activate empty knowledge"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    proposal = _proposal_with_pending(repo, store)
    store.apply_guarded_mutation(repo, proposal)

    topic_map = json.loads((repo / "docs/knowledge/topics.index.json").read_text())
    blob = topic_map["entries"][0]["blob"]
    assert blob["algorithm"] == "sha256"
    assert len(blob["object_id"]) == 64
    _commit(repo)
    assert store.enquire_head(repo)["entries"][0]["blob"] == blob


def test_topic_contract_enforces_lifecycle_freshness_and_retirement(repo: Path, store) -> None:
    store.validate_topic(valid_topic())
    for topic in (
        valid_topic(lifecycle="unknown"),
        valid_topic(freshness={"state": "changed", "checked_at": "2026-08-13T12:40:00Z"}),
        valid_topic(
            lifecycle="retired",
            retirement={"reason": "canonicalized", "successors": []},
        ),
    ):
        with pytest.raises(store.KnowledgeStoreError):
            store.validate_topic(copy.deepcopy(topic))
