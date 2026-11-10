from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    load_project_knowledge_module,
    valid_capture_request,
    valid_work_item_request,
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

    monkeypatch.setattr(module, "parse_capture_request", parse_once)
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
        ["--capture", "--pending", "--repo-root", str(repo)],
        _semantic_input(),
    ) == 2


_GATE_ARTIFACT = {
    "spec-approved": "docs/specs/example/spec.md",
    "plan-locked": "docs/specs/example/plan.md",
}


def _refusal_reason(capsys: pytest.CaptureFixture[str]) -> str:
    return json.loads(capsys.readouterr().err)["reason_code"]


@pytest.mark.parametrize("gate", sorted(_GATE_ARTIFACT))
def test_work_loop_profile_refuses_capture_and_writes_nothing(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    gate: str,
) -> None:
    """Offer the exact request the removed gate path accepted: it must refuse."""
    module = load_project_knowledge_module()
    before = _journal_bytes(repo)
    assert (
        _run_main(
            module,
            monkeypatch,
            _capture_args(repo, gate, _GATE_ARTIFACT[gate]),
            _semantic_input(),
        )
        == 2
    )
    assert _refusal_reason(capsys) == "strict_parse"
    assert _journal_bytes(repo) == before
    assert _events(repo) == []


def test_work_loop_profile_refuses_distill_and_writes_nothing(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A stored receipt of the removed gate no longer selects anything.

    The receipt is stored through the raw capture path with the producer
    fields the removed profile stamped, so the base distill path accepted it.
    """
    gate = "plan-locked"  # the only gate the base distill path ever accepted
    module = load_project_knowledge_module()
    request = valid_capture_request(
        producer={
            "workflow": "work-loop",
            "workflow_version": "work-loop-producer-profile.v1",
        },
        semantic_gate={"name": gate, "artifact": _GATE_ARTIFACT[gate]},
    )
    request["observed_at"] = "2026-08-30T12:34:56Z"
    assert (
        _run_main(
            module,
            monkeypatch,
            ["--capture", "--repo-root", str(repo),
             "--writer-time", request["observed_at"]],
            request,
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    before = _journal_bytes(repo)
    stored = _events(repo)
    assert len(stored) == 1
    body = {"selection_mode": "workflow-receipts", "receipts": [receipt]}
    for extra in ([], ["--pending"]):
        assert (
            _run_main(
                module,
                monkeypatch,
                ["--distill", *extra, "--producer-profile", "work-loop",
                 "--semantic-gate", gate, "--repo-root", str(repo)],
                body,
            )
            == 2
        )
        assert _refusal_reason(capsys) == "strict_parse"
    assert _journal_bytes(repo) == before
    assert _events(repo) == stored


def test_close_time_work_item_capture_is_admitted(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_project_knowledge_module()
    request = valid_work_item_request(
        "defect",
        semantic_gate={"name": "close-time", "artifact": "docs/specs/example/plan.md"},
    )
    ordinal = "2"
    base = ["--repo-root", str(repo), "--declined-ordinal", ordinal]
    assert _run_main(module, monkeypatch, ["--reasoning-payload", *base], request) == 0
    key = json.loads(capsys.readouterr().out)["correlation_key"]
    assert _run_main(
        module,
        monkeypatch,
        ["--capture", *base, "--writer-time", request["observed_at"],
         "--reasoning-verdict", "admit", "--reasoning-correlation-key", key],
        request,
    ) == 0
    (event,) = _events(repo)
    assert event["request"]["kind"] == "work-item"
    assert event["request"]["semantic_gate"]["name"] == "close-time"


def test_plain_distill_pending_admits_a_stored_plan_locked_capture(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The store checks only the gate name's form, so an old capture stays distillable."""
    module = load_project_knowledge_module()
    store = load_knowledge_store_module()
    request = valid_capture_request(
        semantic_gate={"name": "plan-locked", "artifact": "docs/specs/example/plan.md"}
    )
    receipt = store.capture_observation(repo, request, writer_time=request["observed_at"])
    assert _events(repo)[0]["request"]["semantic_gate"]["name"] == "plan-locked"
    selector = {"capture_id": receipt["capture_id"], "partition": receipt["partition"]}
    assert _run_main(
        module,
        monkeypatch,
        ["--distill", "--pending", "--repo-root", str(repo)],
        {"selection_mode": "workflow-receipts", "receipts": [selector]},
    ) == 0
    drained = json.loads(capsys.readouterr().out)
    assert [e["capture_id"] for e in drained["pending"]] == [receipt["capture_id"]]
