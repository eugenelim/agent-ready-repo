from __future__ import annotations

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "receive-brief"
    / "SKILL.md"
)


def _gate_section() -> str:
    text = SKILL.read_text(encoding="utf-8")
    return text.split("## Project-knowledge gate: `brief-ready`", 1)[1]


def test_brief_ready_gate_follows_the_complete_write_back() -> None:
    text = SKILL.read_text(encoding="utf-8")

    ready = text.index("1. **Set `Status: Ready`**")
    workspace = text.index("2. **Move the complete structured brief entry in `workspace.toml`**")
    gate = text.index("## Project-knowledge gate: `brief-ready`")
    assert ready < workspace < gate
    section = _gate_section()
    assert "complete DoR gate in step 4" in section
    assert "zero specs" in section
    assert "without a confirmed slice cut" in section
    assert "durable workspace move" in section
    assert "failed or rolled-back workspace transition" in section
    assert "abandoned or incomplete" in section


def test_brief_ready_constructs_the_published_request() -> None:
    section = _gate_section()

    for field in (
        "contract_version",
        "lesson",
        "kind",
        "project_scope",
        "competency_facets",
        "destination_hint",
        "producer",
        "semantic_gate",
        "provenance",
        "freshness_anchor",
        "observed_at",
        "privacy_attestation",
    ):
        assert f"`{field}`" in section
    assert "`producer.workflow: receive-brief`" in section
    assert "`producer.workflow_version`" in section
    assert "`semantic_gate.name: brief-ready`" in section
    assert "`semantic_gate.artifact`" in section
    assert "project-knowledge --capture" in section
    assert "project-knowledge unavailable" in section
    assert "no fallback file" in section


def test_brief_ready_declares_and_preserves_the_public_boundary() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = _gate_section()

    assert re.search(r"boundaries:\s*\n\s*- filesystem_write", text)
    assert re.search(r"boundaries:[\s\S]*?- filesystem_read_untrusted", text)
    assert "imports a private writer" in section
    assert "locates journals" in section
    assert "invents a capture or mutation ID" in section
    assert "selects a partition" in section
    assert "no fallback file" in section
    for private_surface in (
        "knowledge_store.py",
        "append-knowledge.py",
        "patterns.jsonl",
    ):
        assert private_surface not in text


def test_brief_ready_preserves_authority_and_receipt_scope() -> None:
    section = _gate_section()

    assert "incoming brief corpus" in section
    assert "outcome, scope, appetite, rabbit holes, stories, or spec map" in section
    assert "workflow-receipts" in section
    assert "same `brief-ready` gate" in section
    assert "direct-maintainer-pending" in section
    assert "must not guess" in section
    assert "native real-path" in section
    assert "Git relocation variables removed" in section
    assert "lexical dot-segment traversal" in section
    for refusal in ("symlink", "junction", "reparse-point", "non-file", "I/O", "containment uncertainty"):
        assert refusal in section
    assert "committed Git blob" in section
    assert "verification and review barrier" in section
    assert "one query plus at most one refinement" in section
    assert "CQ-DESIGN" in section
