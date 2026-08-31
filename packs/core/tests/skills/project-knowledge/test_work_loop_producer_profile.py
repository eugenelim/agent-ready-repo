from __future__ import annotations

import copy
import io
import json
import os
import tomllib
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    PACK_ROOT,
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    load_project_knowledge_module,
    valid_capture_request,
)


def _semantic_input() -> dict[str, object]:
    return {
        "lesson": "Keep producer-owned persistence fields out of workflow prose.",
        "kind": "pattern",
        "project_scope": {"paths": ["packs/core"], "audience": "project"},
        "competency_facets": ["CQ-CHANGE"],
        "destination_hint": {"type": "topic", "path": "docs/knowledge/example.md"},
        "provenance": {
            "sources": [
                {"path": "docs/specs/example/spec.md", "line_start": 1, "line_end": 2}
            ]
        },
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
    }


def _events(repo: Path) -> list[dict[str, Any]]:
    root = repo / "docs" / "knowledge" / "observations"
    if not root.exists():
        return []
    return [
        json.loads(line)
        for path in sorted(root.glob("*/*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def _journal_bytes(repo: Path) -> bytes:
    root = repo / "docs" / "knowledge" / "observations"
    if not root.exists():
        return b""
    return b"".join(path.read_bytes() for path in sorted(root.glob("*/*.jsonl")))


def _write_gate_artifacts(repo: Path) -> None:
    spec_dir = repo / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_bytes(b"# Governing spec\n")
    (spec_dir / "plan.md").write_bytes(b"# Governing plan\n")


def _run_main(
    module: Any,
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    payload: dict[str, Any],
) -> int:
    stdin = io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    )
    monkeypatch.setattr(module.sys, "stdin", stdin)
    return module.main(argv)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    store = load_knowledge_store_module()
    initialized = initialize_empty_v1_repo(tmp_path, store)
    _write_gate_artifacts(initialized)
    return initialized


def _capture_args(repo: Path, gate: str, artifact: str) -> list[str]:
    return [
        "--capture",
        "--producer-profile",
        "work-loop",
        "--semantic-gate",
        gate,
        "--artifact",
        artifact,
        "--repo-root",
        str(repo),
    ]


def test_profile_capture_uses_real_bytes_and_pinned_release_version(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_project_knowledge_module()
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "spec-approved", "docs/specs/example/spec.md"),
        _semantic_input(),
    ) == 0

    event = _events(repo)[0]
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    assert event["request"]["producer"] == {
        "workflow": "work-loop",
        "workflow_version": manifest["pack"]["version"],
    }
    assert event["request"]["freshness_anchor"]["digest"] == module.digest_bytes(
        (repo / "docs/specs/example/spec.md").read_bytes()
    )
    assert json.loads(capsys.readouterr().out)["capture_id"] == event["capture_id"]


@pytest.mark.parametrize("artifact", ["../outside.md", "docs/specs/example/spec.md"])
def test_profile_refuses_escaped_or_nonregular_artifacts_without_persisting(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    artifact: str,
) -> None:
    module = load_project_knowledge_module()
    if artifact == "docs/specs/example/spec.md":
        (repo / artifact).unlink()
        (repo / artifact).mkdir()
    assert (
        _run_main(
            module, monkeypatch, _capture_args(repo, "spec-approved", artifact), _semantic_input()
        )
        == 2
    )
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["reason_code"] in {"confinement", "strict_parse"}
    assert _events(repo) == []


def test_profile_refuses_symlinked_artifact_without_persisting(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    module = load_project_knowledge_module()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    artifact = repo / "docs/specs/example/spec.md"
    artifact.unlink()
    try:
        artifact.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "spec-approved", "docs/specs/example/spec.md"),
        _semantic_input(),
    ) == 2
    assert json.loads(capsys.readouterr().err)["reason_code"] == "confinement"
    assert _events(repo) == []


def test_profile_refuses_hard_linked_artifact_without_persisting(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A hard-linked artifact must not expose bytes outside the worktree."""

    module = load_project_knowledge_module()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    artifact = repo / "docs/specs/example/spec.md"
    artifact.unlink()
    try:
        os.link(outside, artifact)
    except OSError:
        pytest.skip("hard links are unavailable")

    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "spec-approved", "docs/specs/example/spec.md"),
        _semantic_input(),
    ) == 2
    assert json.loads(capsys.readouterr().err)["reason_code"] == "confinement"
    assert _events(repo) == []


def test_internal_hard_link_remains_readable_outside_untrusted_source_boundary(
    repo: Path, tmp_path: Path
) -> None:
    """Shared store reads retain hard-link compatibility outside source capture."""

    store = load_knowledge_store_module()
    internal_topic = store.topic_path_for_key(repo, "contracts/hard-link")
    internal_topic.parent.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "topic-source.json"
    source.write_bytes(b"internal topic bytes")
    try:
        os.link(source, internal_topic)
    except OSError:
        pytest.skip("hard links are unavailable")

    assert store._read_regular_file_bounded(internal_topic, 128) == b"internal topic bytes"


def test_profile_enforces_gate_artifact_pair_and_plan_sibling(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_project_knowledge_module()
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "plan-locked", "docs/specs/example/plan.md"),
        _semantic_input(),
    ) == 0
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "plan-locked", "docs/specs/example/spec.md"),
        _semantic_input(),
    ) == 2
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "spec-approved", "docs/specs/example/plan.md"),
        _semantic_input(),
    ) == 2
    (repo / "docs/specs/example/spec.md").unlink()
    sibling_input = copy.deepcopy(_semantic_input())
    sibling_input["provenance"] = {
        "sources": [
            {"path": "docs/specs/example/plan.md", "line_start": 1, "line_end": 2}
        ]
    }
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "plan-locked", "docs/specs/example/plan.md"),
        sibling_input,
    ) == 2
    assert len(_events(repo)) == 1
    capsys.readouterr()


def test_profile_terminal_distillation_refuses_wrong_gate_and_guessed_receipts(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_project_knowledge_module()
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "spec-approved", "docs/specs/example/spec.md"),
        _semantic_input(),
    ) == 0
    spec_receipt = json.loads(capsys.readouterr().out)
    plan_input = copy.deepcopy(_semantic_input())
    plan_input["lesson"] = "Keep terminal receipt selection tied to its semantic gate."
    assert _run_main(
        module,
        monkeypatch,
        _capture_args(repo, "plan-locked", "docs/specs/example/plan.md"),
        plan_input,
    ) == 0
    plan_receipt = json.loads(capsys.readouterr().out)
    args = [
        "--distill",
        "--pending",
        "--producer-profile",
        "work-loop",
        "--semantic-gate",
        "plan-locked",
        "--repo-root",
        str(repo),
    ]
    assert _run_main(
        module,
        monkeypatch,
        args,
        {"selection_mode": "workflow-receipts", "receipts": [spec_receipt]},
    ) == 2
    assert _run_main(
        module,
        monkeypatch,
        args,
        {"selection_mode": "workflow-receipts", "receipts": [plan_receipt]},
    ) == 0
    guessed = copy.deepcopy(plan_receipt)
    replacement = "0" if guessed["capture_id"][-1] != "0" else "1"
    guessed["capture_id"] = f"{guessed['capture_id'][:-1]}{replacement}"
    assert _run_main(
        module,
        monkeypatch,
        args,
        {"selection_mode": "workflow-receipts", "receipts": [guessed]},
    ) == 2
    assert _run_main(
        module,
        monkeypatch,
        args,
        {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"},
    ) == 2


def test_raw_capture_path_only_parses_the_hand_constructed_request(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = load_project_knowledge_module()
    request = valid_capture_request()
    request["observed_at"] = "2026-08-30T12:34:56Z"
    raw = json.dumps(request).encode("utf-8")
    parsed = module.parse_capture_request(raw)
    calls = 0
    original_parse = module.parse_capture_request

    def parse_once(value: bytes) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return original_parse(value)

    def profile_must_not_run(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("raw capture must not build a producer profile")

    monkeypatch.setattr(module, "parse_capture_request", parse_once)
    monkeypatch.setattr(module, "build_work_loop_capture_request", profile_must_not_run)
    assert _run_main(
        module,
        monkeypatch,
        ["--capture", "--repo-root", str(repo), "--writer-time", request["observed_at"]],
        request,
    ) == 0
    assert calls == 1
    assert _events(repo)[0]["request"] == parsed
    store = load_knowledge_store_module()
    baseline = initialize_empty_v1_repo(tmp_path / "raw-baseline", store)
    store.capture_observation(baseline, parsed, writer_time=request["observed_at"])
    assert _journal_bytes(repo) == _journal_bytes(baseline)


def test_work_loop_review_profile_constructs_the_fixed_enquiry_without_an_artifact(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_project_knowledge_module()
    request = module.build_work_loop_review_enquiry(
        {"task_summary": "work-loop review: profile seam", "scope": "packs/core"}
    )
    assert request == {
        "task_summary": "work-loop review: profile seam",
        "scope": "packs/core",
        "question": "Which recurring project risks should these reviewers verify against the current target?",
        "question_id": "CQ-REVIEW",
        "caller": "skill",
        "risk": "consequential",
    }
    with pytest.raises(ValueError):
        module.build_work_loop_review_enquiry(
            {"task_summary": "x", "scope": "packs/core", "risk": "routine"}
        )
    assert _run_main(
        module,
        monkeypatch,
        [
            "--enquire",
            "--producer-profile",
            "work-loop",
            "--semantic-gate",
            "review",
            "--repo-root",
            str(repo),
        ],
        {"task_summary": "work-loop review: profile seam", "scope": "packs/core"},
    ) == 0
    assert json.loads(capsys.readouterr().out)["receipt"]["question_id"] == "CQ-REVIEW"


@pytest.mark.parametrize(
    ("gate", "question_id", "risk"),
    [
        ("change", "CQ-CHANGE", "consequential"),
        ("verify", "CQ-VERIFY", "routine"),
    ],
)
def test_work_loop_profile_constructs_change_and_verify_enquiries_with_risk(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    gate: str,
    question_id: str,
    risk: str,
) -> None:
    module = load_project_knowledge_module()
    semantic_input = {
        "task_summary": f"work-loop {gate}: profile seam",
        "scope": "packs/core",
        "risk": risk,
    }
    request = module.build_work_loop_enquiry(semantic_input, semantic_gate=gate)
    assert request["question_id"] == question_id
    assert request["risk"] == risk
    assert module._WORK_LOOP_ENQUIRY_GATES[gate]["permits_refinement"] is True
    assert _run_main(
        module,
        monkeypatch,
        [
            "--enquire",
            "--producer-profile",
            "work-loop",
            "--semantic-gate",
            gate,
            "--refinement",
            "--repo-root",
            str(repo),
        ],
        semantic_input,
    ) == 0
    receipt = json.loads(capsys.readouterr().out)["receipt"]
    assert receipt["question_id"] == question_id
    assert receipt["risk"] == risk


def test_work_loop_review_profile_refuses_refinement_and_pending_misuse(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_project_knowledge_module()
    review_args = [
        "--enquire",
        "--producer-profile",
        "work-loop",
        "--semantic-gate",
        "review",
        "--repo-root",
        str(repo),
    ]
    review_input = {"task_summary": "work-loop review: profile seam", "scope": "packs/core"}
    assert _run_main(module, monkeypatch, [*review_args, "--refinement"], review_input) == 2
    assert _run_main(
        module,
        monkeypatch,
        ["--enquire", "--refinement", "--repo-root", str(repo)],
        {
            "task_summary": "raw enquiry",
            "scope": "packs/core",
            "question": "Which checks are relevant?",
            "question_id": "CQ-REVIEW",
            "caller": "skill",
            "risk": "routine",
        },
    ) == 2
    assert _run_main(module, monkeypatch, [*review_args, "--pending"], review_input) == 2
    assert _run_main(
        module,
        monkeypatch,
        [
            *_capture_args(repo, "spec-approved", "docs/specs/example/spec.md"),
            "--pending",
        ],
        _semantic_input(),
    ) == 2
