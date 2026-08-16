from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    PROJECT_KNOWLEDGE_SCRIPT,
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    valid_capture_request,
)


@pytest.fixture
def store():
    return load_knowledge_store_module()


@pytest.fixture
def repo(tmp_path: Path, store) -> Path:
    initialize_empty_v1_repo(tmp_path, store)
    (tmp_path / "AGENTS.md").write_text("existing instructions\n", encoding="utf-8")
    return tmp_path


def _request(**overrides: Any) -> dict[str, Any]:
    request = valid_capture_request()
    request["observed_at"] = "2026-08-13T12:34:56Z"
    request.update(overrides)
    return request


def _capture(repo: Path, store, **overrides: Any) -> dict[str, Any]:
    return store.capture_observation(
        repo,
        _request(**overrides),
        writer_time="2026-08-13T12:40:00Z",
    )


def _promotion(receipt: dict[str, Any], store) -> dict[str, Any]:
    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "promoted",
        "reason_code": "promoted_to_topic",
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": ["contracts/public-contracts"],
        "named_sources": ["contracts/jsonschema/knowledge-captured-observation.schema.json"],
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
        },
    }
    proposal["mutation"] = store.complete_mutation_proposal(proposal["mutation"])
    return proposal


def _terminal_dispositions(repo: Path, capture_id: str) -> list[str]:
    root = repo / "docs" / "knowledge" / "observations"
    dispositions: list[str] = []
    for path in sorted(root.glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if (
                event["event_type"] == "observation.dispositioned"
                and event["capture_id"] == capture_id
            ):
                dispositions.append(event["disposition"])
    return dispositions


def test_ac15_distill_records_one_terminal_disposition(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    result = store.distill_observation(repo, _promotion(receipt, store))
    assert result["disposition"] == "promoted"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == ["promoted"]

    (repo / "docs/knowledge/topics.index.json").write_text(
        '{"entries":[],"schema_version":"knowledge-topic-map.v1"}\n',
        encoding="utf-8",
    )
    with pytest.raises(store.KnowledgeStoreError):
        store.distill_observation(repo, _promotion(receipt, store))


def test_ac14_generic_terminal_writer_cannot_create_promoted_disposition(
    repo: Path, store
) -> None:
    receipt = _capture(repo, store)
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_terminal_disposition(
            repo,
            receipt["capture_id"],
            "promoted",
            reason_code="promoted_to_topic",
            recorded_at="2026-08-13T12:41:00Z",
        )
    assert refused.value.diagnostic["reason_code"] == "strict_parse"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == []

    replay = store.distill_observation(repo, _promotion(receipt, store))
    assert replay["disposition"] == "promoted"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == ["promoted"]


def test_ac14_terminal_reason_code_refuses_before_journal_write(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_terminal_disposition(
            repo,
            receipt["capture_id"],
            "rejected",
            reason_code="Not-Reusable",
            recorded_at="2026-08-13T12:41:00Z",
        )
    assert refused.value.diagnostic["reason_code"] == "strict_parse"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == []

    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "rejected",
        "reason_code": "Not-Reusable",
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": [],
        "named_sources": [],
        "mutation": None,
    }
    with pytest.raises(store.KnowledgeStoreError):
        store.distill_observation(repo, proposal)
    assert _terminal_dispositions(repo, receipt["capture_id"]) == []


@pytest.mark.parametrize(
    "private_reason",
    (
        "aaaaaaaa-bbbb-7ccc-8ddd-eeeeeeeeeeee",
        "user_id_abcdef",
        "token_abcdefghijklmnop",
        "build_aaaaaaaa-bbbb-7ccc-8ddd-eeeeeeeeeeee_suffix",
    ),
)
def test_ac18_terminal_reason_refuses_private_identifier(
    repo: Path, store, private_reason: str
) -> None:
    receipt = _capture(repo, store)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.write_terminal_disposition(
            repo,
            receipt["capture_id"],
            "rejected",
            reason_code=private_reason,
            recorded_at="2026-08-13T12:41:00Z",
        )
    assert refused.value.diagnostic["reason_code"] == "privacy"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == []

    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "rejected",
        "reason_code": private_reason,
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": [],
        "named_sources": [],
        "mutation": None,
    }
    with pytest.raises(store.KnowledgeStoreError) as proposal_refused:
        store.distill_observation(repo, proposal)
    assert proposal_refused.value.diagnostic["reason_code"] == "privacy"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == []


def test_ac15_non_promoted_terminal_disposition_records_no_body(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    result = store.distill_observation(
        repo,
        {
            "schema_version": "knowledge-distillation-proposal.v1",
            "capture_id": receipt["capture_id"],
            "disposition": "rejected",
            "reason_code": "not_reusable",
            "recorded_at": "2026-08-13T12:41:00Z",
            "candidate_topic_keys": [],
            "named_sources": [],
            "mutation": None,
        },
    )
    assert result["disposition"] == "rejected"
    assert not (repo / "docs" / "knowledge" / "topics").exists()


def test_ac15_distill_cli_records_workflow_receipt_terminal_disposition(
    repo: Path, store
) -> None:
    receipt = _capture(repo, store)
    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "duplicate",
        "reason_code": "already_known",
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": [],
        "named_sources": [],
        "mutation": None,
    }

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_KNOWLEDGE_SCRIPT),
            "--distill",
            "--repo-root",
            str(repo),
        ],
        input=json.dumps(proposal).encode("utf-8"),
        capture_output=True,
        check=True,
    )

    output = json.loads(result.stdout)
    assert output["disposition"] == "duplicate"
    assert _terminal_dispositions(repo, receipt["capture_id"]) == ["duplicate"]


def test_ac16_script_refuses_to_invent_semantic_choice(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    with pytest.raises(store.KnowledgeStoreError):
        store.distill_observation(
            repo,
            _promotion(receipt, store)
            | {
                "mutation": None,
                "semantic_status": "ambiguous_split",
            },
        )
    assert not (repo / "docs" / "knowledge" / "topics").exists()


def test_ac37_malformed_mutation_container_returns_redacted_cli_diagnostic(
    repo: Path, store
) -> None:
    receipt = _capture(repo, store)
    proposal = _promotion(receipt, store)
    proposal["mutation"]["supporting_sources"] = None
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_KNOWLEDGE_SCRIPT),
            "--distill",
            "--repo-root",
            str(repo),
        ],
        input=json.dumps(proposal).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stderr)["reason_code"] == "strict_parse"
    assert "Traceback" not in result.stderr.decode("utf-8")
    assert str(repo) not in result.stderr.decode("utf-8")


def test_ac31_routing_is_a_suggestion_not_an_instruction_edit(repo: Path, store) -> None:
    before = (repo / "AGENTS.md").read_text(encoding="utf-8")
    receipt = _capture(
        repo,
        store,
        competency_facets=["CQ-ROUTE"],
        destination_hint={"type": "route-suggestion", "path": "AGENTS.md"},
    )
    result = store.distill_observation(
        repo,
        {
            "schema_version": "knowledge-distillation-proposal.v1",
            "capture_id": receipt["capture_id"],
            "disposition": "routed",
            "reason_code": "route_suggested",
            "recorded_at": "2026-08-13T12:41:00Z",
            "candidate_topic_keys": [],
            "named_sources": ["AGENTS.md"],
            "mutation": None,
            "routing_suggestion": {
                "competency_question": "CQ-ROUTE",
                "authoritative_start": "AGENTS.md",
                "generated_outputs": ["docs/knowledge/topics.index.json"],
                "verification": "python3 -m pytest packs/core/tests/skills/project-knowledge -q",
            },
        },
    )
    assert result["suggestion"]["competency_question"] == "CQ-ROUTE"
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == before
