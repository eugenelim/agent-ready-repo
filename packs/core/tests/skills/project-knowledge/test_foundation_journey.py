from __future__ import annotations

import copy
import json
import shutil
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


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _promotion(store, receipt: dict[str, Any], source: Path) -> dict[str, Any]:
    source_digest = store.PK.digest_bytes(source.read_bytes())
    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "promoted",
        "reason_code": "promoted_to_topic",
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": ["contracts/public-contracts"],
        "named_sources": [
            "contracts/jsonschema/knowledge-captured-observation.schema.json"
        ],
        "mutation": {
            "schema_version": "knowledge-mutation-proposal.v1",
            "capture_id": receipt["capture_id"],
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
                "digest": source_digest,
            },
            "supporting_sources": [],
            "occurrence": {
                "producer": "work-loop",
                "semantic_gate": "verified-slice",
                "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
                "evidence_digest": source_digest,
                "scope": "packs/core",
                "observed_at": "2026-08-13T12:34:56Z",
            },
            "terminal_disposition": {
                "disposition": "promoted",
                "reason_code": "promoted_to_topic",
                "recorded_at": "2026-08-13T12:41:00Z",
            },
            "expected_topic_digest": None,
        },
    }
    proposal["mutation"] = store.complete_mutation_proposal(proposal["mutation"])
    return proposal


def _query() -> dict[str, Any]:
    return {
        "task_summary": "Verify the project knowledge contract.",
        "scope": "packs/core",
        "question": None,
        "question_id": "CQ-VERIFY",
        "caller": "skill",
        "risk": "consequential",
    }


def test_ac34_disposable_repository_foundation_journey(tmp_path: Path, store) -> None:
    repo = tmp_path
    knowledge = repo / "docs" / "knowledge"
    knowledge.mkdir(parents=True)
    source = repo / "contracts/jsonschema/knowledge-captured-observation.schema.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"schema":"v1"}\n', encoding="utf-8")
    work_loop = repo / "packs/core/.apm/skills/work-loop/SKILL.md"
    work_loop.parent.mkdir(parents=True)
    work_loop.write_text("capture through the public seam\n", encoding="utf-8")
    legacy = {
        "id": "K-1001",
        "kind": "pattern",
        "scope": "packs/core",
        "title": "Legacy knowledge remains attributable",
        "body": "Import legacy rows as occurrences.",
        "source": "commit abc123",
    }
    legacy_bytes = json.dumps(legacy, sort_keys=True).encode("utf-8") + b"\n"
    (knowledge / "patterns.jsonl").write_bytes(legacy_bytes)
    _git(repo, "init")
    _git(repo, "config", "user.email", "user@example.com")
    _git(repo, "config", "user.name", "Example User")

    migration = store.stage_legacy_migration(repo)
    assert migration["counts"]["input_rows"] == 1
    stage = knowledge / ".migration-stage/docs/knowledge"
    shutil.copytree(stage / "topics", knowledge / "topics", dirs_exist_ok=True)
    shutil.copy2(stage / "topics.index.json", knowledge / "topics.index.json")
    _git(repo, "add", "docs/knowledge/patterns.jsonl", "docs/knowledge/topics", "docs/knowledge/topics.index.json")
    _git(repo, "commit", "-m", "test: activate project knowledge")
    committed = store.committed_knowledge_snapshot(repo)
    assert store.activate_staged_migration(repo, committed_snapshot=committed)["state"] == "activated"
    assert (knowledge / "patterns.jsonl").read_bytes() == legacy_bytes

    request = valid_capture_request()
    first = store.capture_observation(
        repo, request, writer_time="2026-08-13T12:40:00Z"
    )
    partition = knowledge / first["partition"]
    captured_bytes = partition.read_bytes()
    assert store.capture_observation(
        repo, request, writer_time="2026-08-13T12:40:00Z"
    ) == first
    assert partition.read_bytes() == captured_bytes
    assert store.distill_observation(repo, _promotion(store, first, source))[
        "disposition"
    ] == "promoted"

    rejected_request = valid_capture_request(
        lesson="A rejected instruction-shaped body must remain outside retrieval."
    )
    rejected = store.capture_observation(
        repo, rejected_request, writer_time="2026-08-13T12:40:00Z"
    )
    store.distill_observation(
        repo,
        {
            "schema_version": "knowledge-distillation-proposal.v1",
            "capture_id": rejected["capture_id"],
            "disposition": "rejected",
            "reason_code": "not_reusable",
            "recorded_at": "2026-08-13T12:42:00Z",
            "candidate_topic_keys": [],
            "named_sources": [],
            "mutation": None,
        },
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test: publish project knowledge")

    result = store.enquire(repo, _query())
    assert result["receipt"]["selected_topics"] == ["contracts/public-contracts"]
    assert "rejected instruction-shaped" not in result["rendered"]
    assert result["receipt"]["opened_journals"] == 0

    topic_path = store.topic_path_for_key(repo, "contracts/public-contracts")
    committed_topic = json.loads(topic_path.read_text(encoding="utf-8"))
    working_topic = copy.deepcopy(committed_topic)
    working_topic["synthesis"]["body"] = "working-tree-only instruction"
    store.write_topic(repo, working_topic)
    store.rebuild_topic_map(repo)
    assert "working-tree-only" not in store.enquire(repo, _query())["rendered"]

    source.write_text('{"schema":"drifted"}\n', encoding="utf-8")
    drifted = store.enquire(repo, _query())
    assert drifted["receipt"]["selected_topics"] == []
    assert drifted["receipt"]["abstained"] is True
    source.write_text('{"schema":"v1"}\n', encoding="utf-8")

    retired = copy.deepcopy(committed_topic)
    retired["lifecycle"] = "retired"
    retired["freshness"] = {
        "state": "retired",
        "checked_at": "2026-08-13T13:00:00Z",
    }
    retired["retirement"] = {
        "reason": "enforced",
        "successors": ["contracts/jsonschema/knowledge-captured-observation.schema.json"],
        "coverage_verified": True,
    }
    store.write_topic(repo, retired)
    store.rebuild_topic_map(repo)
    _git(repo, "add", "docs/knowledge")
    _git(repo, "commit", "-m", "test: retire enforced knowledge")
    assert store.enquire(repo, _query())["receipt"]["selected_topics"] == []

    recovery_request = valid_capture_request(lesson="Interrupted mutations recover exactly.")
    recovery_request["observed_at"] = "2026-08-13T12:34:56Z"
    recovery = store.capture_observation(
        repo, recovery_request, writer_time="2026-08-13T12:40:00Z"
    )
    interrupted = copy.deepcopy(_promotion(store, first, source)["mutation"])
    interrupted["capture_id"] = recovery["capture_id"]
    interrupted["topic_key"] = "operations/interruption-recovery"
    interrupted["title"] = "Interrupted mutations recover exactly"
    interrupted["expected_topic_digest"] = None
    interrupted = store.complete_mutation_proposal(interrupted)
    with pytest.raises(store.KnowledgeStoreError):
        store.apply_guarded_mutation(repo, interrupted, interrupt_after="topic")
    recovered = store.recover_guarded_mutation(repo, interrupted)
    assert recovered["promoted_implies_topic_and_map"] is True


def test_ac33_closed_partitions_are_immutable_and_have_no_event_deletion_api(
    tmp_path: Path, store
) -> None:
    initialize_empty_v1_repo(tmp_path, store)
    june = valid_capture_request(observed_at="2026-06-30T12:34:56Z")
    june_receipt = store.capture_observation(
        tmp_path, june, writer_time="2026-06-30T12:40:00Z"
    )
    june_path = tmp_path / "docs/knowledge" / june_receipt["partition"]
    closed_bytes = june_path.read_bytes()

    july = valid_capture_request(
        lesson="A later partition must not rewrite a closed one.",
        observed_at="2026-07-01T12:34:56Z",
    )
    july_receipt = store.capture_observation(
        tmp_path, july, writer_time="2026-07-01T12:40:00Z"
    )
    store.distill_observation(
        tmp_path,
        {
            "schema_version": "knowledge-distillation-proposal.v1",
            "capture_id": july_receipt["capture_id"],
            "disposition": "duplicate",
            "reason_code": "already_known",
            "recorded_at": "2026-07-01T12:41:00Z",
            "candidate_topic_keys": [],
            "named_sources": [],
            "mutation": None,
        },
    )

    assert june_path.read_bytes() == closed_bytes
    public_names = {
        name
        for name in vars(store)
        if not name.startswith("_") and callable(getattr(store, name))
    }
    assert not {
        "compact_observations",
        "delete_observation",
        "delete_partition",
        "retain_observations",
    } & public_names
