from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    PROJECT_KNOWLEDGE_SCRIPT,
    load_knowledge_store_module,
    valid_capture_request,
)


@pytest.fixture
def store():
    return load_knowledge_store_module()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    knowledge = tmp_path / "docs" / "knowledge"
    knowledge.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "user@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Example User"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


def _commit_staged_activation(repo: Path, store) -> dict[str, Any]:
    stage = repo / "docs/knowledge/.migration-stage/docs/knowledge"
    knowledge = repo / "docs/knowledge"
    shutil.copytree(stage / "topics", knowledge / "topics", dirs_exist_ok=True)
    shutil.copy2(stage / "topics.index.json", knowledge / "topics.index.json")
    subprocess.run(
        ["git", "add", "docs/knowledge/patterns.jsonl", "docs/knowledge/topics", "docs/knowledge/topics.index.json"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "test: activate project knowledge"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    snapshot = store.committed_knowledge_snapshot(repo)
    return store.activate_staged_migration(repo, committed_snapshot=snapshot)


def _legacy_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "K-1001",
            "kind": "pattern",
            "scope": "packs/core",
            "title": "Use the public contract for workflow handoff",
            "body": "Route reusable workflow residue through the published capture contract.",
            "source": "PR#example / commit abc123",
        },
        {
            "id": "K-1002",
            "kind": "gotcha",
            "scope": "packs/core",
            "title": "Use the public contract for workflow handoff",
            "body": "Duplicate-looking lessons need maintainer review before grouping.",
            "source": "PR#example / commit def456",
        },
        {
            "id": "K-1003",
            "kind": "antipattern",
            "scope": "**/*.py",
            "title": "Do not persist refused source bodies",
            "body": "",
            "source": "PR#example / commit bad999",
        },
    ]


def _write_legacy(repo: Path, rows: list[dict[str, Any]], *, raw_suffix: bytes = b"") -> bytes:
    raw = b"".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
        for row in rows
    ) + raw_suffix
    (repo / "docs" / "knowledge" / "patterns.jsonl").write_bytes(raw)
    return raw


def _semantic_bytes(repo: Path) -> bytes:
    knowledge = repo / "docs" / "knowledge"
    return b"".join(path.read_bytes() for path in sorted(knowledge.rglob("*.json")))


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_ac20_migration_strictly_prevalidates_every_row_before_staging(
    repo: Path, store
) -> None:
    before = _write_legacy(repo, _legacy_rows(), raw_suffix=b'{"id":"bad","id":"dup"}\n')

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.stage_legacy_migration(repo)

    assert refused.value.diagnostic == {
        "version": "knowledge-diagnostic.v1",
        "reason_code": "strict_parse",
        "path": "docs/knowledge/patterns.jsonl",
        "line": 4,
        "retryable": False,
        "recovery_action": "fix_request",
    }
    assert (repo / "docs" / "knowledge" / "patterns.jsonl").read_bytes() == before
    assert not store.staged_migration_files(repo)


def test_ac20_migration_counts_and_preserves_legacy_occurrences(repo: Path, store) -> None:
    before = _write_legacy(repo, _legacy_rows())

    result = store.stage_legacy_migration(repo)

    assert result["counts"] == {
        "input_rows": 3,
        "active_import": 0,
        "needs_review_import": 2,
        "refused": 1,
    }
    assert result["diagnostics"] == [
        {
            "version": "knowledge-diagnostic.v1",
            "reason_code": "ambiguous_grouping",
            "path": "docs/knowledge/patterns.jsonl",
            "line": 1,
            "retryable": False,
            "recovery_action": "review_topic_grouping",
        },
        {
            "version": "knowledge-diagnostic.v1",
            "reason_code": "ambiguous_grouping",
            "path": "docs/knowledge/patterns.jsonl",
            "line": 2,
            "retryable": False,
            "recovery_action": "review_topic_grouping",
        }
    ]
    assert (repo / "docs" / "knowledge" / "patterns.jsonl").read_bytes() == before

    staged_topics = sorted(store.staged_topic_files(repo))
    assert [path.name for path in staged_topics] == [
        "use-the-public-contract-for-workflow-handoff.json",
    ]
    topics = [json.loads(path.read_text(encoding="utf-8")) for path in staged_topics]
    occurrences = [occurrence for topic in topics for occurrence in topic["occurrences"]]
    assert {item["legacy_identity"] for item in occurrences} == {"K-1001", "K-1002"}
    assert {item["source"]["path"] for item in occurrences} == {
        "docs/knowledge/patterns.jsonl"
    }
    assert {item["legacy_identity"]: item["legacy_source"] for item in occurrences} == {
        row["id"]: row["source"] for row in _legacy_rows() if row["body"]
    }
    assert {item["reviewed_disposition"] for item in occurrences} == {"needs_review_import"}
    assert "bad999" not in b"".join(path.read_bytes() for path in staged_topics).decode("utf-8")
    staged_knowledge = repo / "docs/knowledge/.migration-stage/docs/knowledge"
    independently_rebuilt = store.rebuild_map_bytes(
        staged_knowledge,
        repository_root=repo,
    )
    assert store.staged_map_bytes(repo) == independently_rebuilt


def test_ac20_migration_surfaces_and_preserves_distinct_slug_collisions(
    repo: Path, store
) -> None:
    rows = [
        {
            "id": "K-2001",
            "kind": "pattern",
            "scope": "packs/core",
            "title": "Prefer a b",
            "body": "First distinct synthesis.",
            "source": "PR#example / commit abc123",
        },
        {
            "id": "K-2002",
            "kind": "gotcha",
            "scope": "packs/core",
            "title": "Prefer a-b",
            "body": "Second distinct synthesis.",
            "source": "PR#example / commit def456",
        },
    ]
    _write_legacy(repo, rows)

    result = store.stage_legacy_migration(repo)

    assert result["counts"] == {
        "input_rows": 2,
        "active_import": 0,
        "needs_review_import": 2,
        "refused": 0,
    }
    assert [item["line"] for item in result["diagnostics"]] == [1, 2]
    assert {item["reason_code"] for item in result["diagnostics"]} == {
        "ambiguous_grouping"
    }
    staged = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in store.staged_topic_files(repo)
    ]
    assert len(staged) == 2
    assert len({topic["topic_key"] for topic in staged}) == 2
    assert {topic["synthesis"]["body"] for topic in staged} == {
        "First distinct synthesis.",
        "Second distinct synthesis.",
    }


def test_ac20_migration_failures_leave_source_and_staging_unchanged(repo: Path, store) -> None:
    before = _write_legacy(repo, _legacy_rows())

    for failure in ("privacy", "accounting", "interrupted_staged_write"):
        store.clear_staged_migration(repo)
        assert (repo / "docs" / "knowledge" / "patterns.jsonl").read_bytes() == before
        with pytest.raises(store.KnowledgeStoreError):
            store.stage_legacy_migration(repo, inject=failure)
        assert (repo / "docs" / "knowledge" / "patterns.jsonl").read_bytes() == before
        assert not store.staged_migration_files(repo)


def test_ac20_private_legacy_scope_reports_redacted_source_line(repo: Path, store) -> None:
    rows = _legacy_rows()
    rows[0]["scope"] = "docs/user@example.com/notes.md"
    _write_legacy(repo, rows)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.stage_legacy_migration(repo)

    assert refused.value.diagnostic["reason_code"] == "privacy"
    assert refused.value.diagnostic["path"] == "docs/knowledge/patterns.jsonl"
    assert refused.value.diagnostic["line"] == 1
    assert not store.staged_migration_files(repo)


def test_ac21_staged_v1_map_blocks_both_writer_generations(repo: Path, store) -> None:
    _write_legacy(repo, _legacy_rows())
    store.stage_legacy_migration(repo)

    with pytest.raises(store.KnowledgeStoreError) as legacy_refused:
        store.legacy_append(repo, _legacy_rows()[0])
    with pytest.raises(store.KnowledgeStoreError) as capture_refused:
        store.capture_observation(
            repo,
            valid_capture_request(),
            writer_time="2026-08-13T12:40:00Z",
        )
    with pytest.raises(store.KnowledgeStoreError):
        store.distill_observation(repo, {"schema_version": "knowledge-distillation-proposal.v1"})

    assert legacy_refused.value.diagnostic["reason_code"] == "staged_dual_writer"
    assert capture_refused.value.diagnostic["reason_code"] == "staged_dual_writer"


def test_ac21_uncommitted_v1_map_blocks_both_writer_generations(repo: Path, store) -> None:
    _write_legacy(repo, _legacy_rows())
    store.stage_legacy_migration(repo)
    stage = repo / "docs/knowledge/.migration-stage/docs/knowledge"
    knowledge = repo / "docs/knowledge"
    shutil.copytree(stage / "topics", knowledge / "topics", dirs_exist_ok=True)
    shutil.copy2(stage / "topics.index.json", knowledge / "topics.index.json")
    store.clear_staged_migration(repo)

    with pytest.raises(store.KnowledgeStoreError) as legacy_refused:
        store.legacy_append(repo, _legacy_rows()[0])
    with pytest.raises(store.KnowledgeStoreError) as capture_refused:
        store.capture_observation(
            repo,
            valid_capture_request(),
            writer_time="2026-08-13T12:40:00Z",
        )

    assert legacy_refused.value.diagnostic["reason_code"] == "staged_dual_writer"
    assert capture_refused.value.diagnostic["reason_code"] == "staged_dual_writer"


def test_ac21_activation_refuses_caller_supplied_snapshot_before_commit(
    repo: Path, store
) -> None:
    _write_legacy(repo, _legacy_rows())
    store.stage_legacy_migration(repo)
    caller_snapshot = store.current_tree_snapshot(repo, staged=True)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.activate_staged_migration(
            repo,
            committed_snapshot=caller_snapshot,
        )

    assert refused.value.diagnostic["reason_code"] == "map_mismatch"
    assert store.staged_migration_files(repo)


def test_ac21_activation_refuses_worktree_drift_after_activation_commit(
    repo: Path, store
) -> None:
    _write_legacy(repo, _legacy_rows())
    store.stage_legacy_migration(repo)
    stage = repo / "docs/knowledge/.migration-stage/docs/knowledge"
    knowledge = repo / "docs/knowledge"
    shutil.copytree(stage / "topics", knowledge / "topics", dirs_exist_ok=True)
    shutil.copy2(stage / "topics.index.json", knowledge / "topics.index.json")
    subprocess.run(
        [
            "git",
            "add",
            "docs/knowledge/patterns.jsonl",
            "docs/knowledge/topics",
            "docs/knowledge/topics.index.json",
        ],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "test: commit activation snapshot"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    snapshot = store.committed_knowledge_snapshot(repo)
    topic_path = next((knowledge / "topics").rglob("*.json"))
    topic = json.loads(topic_path.read_text(encoding="utf-8"))
    topic["title"] = "Uncommitted activation drift"
    topic_path.write_text(json.dumps(topic, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.activate_staged_migration(repo, committed_snapshot=snapshot)

    assert refused.value.diagnostic["reason_code"] == "map_mismatch"
    assert store.staged_migration_files(repo)


def test_ac21_activation_and_bounded_rollback_states(repo: Path, store) -> None:
    _write_legacy(repo, _legacy_rows())
    assert store.legacy_append(repo, _legacy_rows()[0])["writer"] == "legacy"
    assert not (repo / "docs" / "knowledge" / "observations").exists()
    with pytest.raises(store.KnowledgeStoreError):
        store.capture_observation(
            repo,
            valid_capture_request(),
            writer_time="2026-08-13T12:40:00Z",
        )

    store.stage_legacy_migration(repo)
    activation = _commit_staged_activation(repo, store)
    assert activation["state"] == "activated"
    with pytest.raises(store.KnowledgeStoreError) as restage_refused:
        store.stage_legacy_migration(repo)
    assert restage_refused.value.diagnostic["reason_code"] == "staged_dual_writer"
    assert store.staged_migration_files(repo) == []

    request = copy.deepcopy(valid_capture_request())
    request["observed_at"] = "2026-08-13T12:34:56Z"
    assert store.capture_observation(repo, request, writer_time="2026-08-13T12:40:00Z")[
        "capture_id"
    ].startswith("kco-202608-")
    with pytest.raises(store.KnowledgeStoreError):
        store.legacy_append(repo, _legacy_rows()[0])

    before = _semantic_bytes(repo)
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.reverse_migration(repo)
    assert refused.value.diagnostic["reason_code"] == "forward_recovery_required"
    assert _semantic_bytes(repo) == before


def test_ac21_activation_revert_is_allowed_only_before_first_v1_capture(
    repo: Path, store
) -> None:
    _write_legacy(repo, _legacy_rows())
    subprocess.run(["git", "add", "docs/knowledge/patterns.jsonl"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test: legacy baseline"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    store.stage_legacy_migration(repo)
    _commit_staged_activation(repo, store)
    subprocess.run(["git", "revert", "--no-edit", "HEAD"], cwd=repo, check=True, capture_output=True)

    assert store.reverse_migration(repo)["state"] == "legacy_restored"
    assert store.legacy_append(repo, _legacy_rows()[0])["writer"] == "legacy"
    with pytest.raises(store.KnowledgeStoreError):
        store.capture_observation(
            repo,
            valid_capture_request(),
            writer_time="2026-08-13T12:40:00Z",
        )


def test_migration_cli_stages_legacy_corpus(repo: Path) -> None:
    _write_legacy(repo, _legacy_rows())

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_KNOWLEDGE_SCRIPT),
            "--migrate-legacy",
            "--repo-root",
            str(repo),
        ],
        capture_output=True,
        check=True,
    )

    receipt = json.loads(result.stdout)
    assert receipt["counts"]["input_rows"] == 3
    staged_map = (
        repo
        / "docs"
        / "knowledge"
        / ".migration-stage"
        / "docs"
        / "knowledge"
        / "topics.index.json"
    )
    assert staged_map.exists()
