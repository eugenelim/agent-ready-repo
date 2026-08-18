from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "architect-review" / "SKILL.md"
EVALS = PACK_ROOT / ".apm" / "skills" / "architect-review" / "evals" / "evals.json"
MANIFEST = PACK_ROOT / "pack.toml"


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _enquiry_section() -> str:
    text = _text()
    start = text.index("**Declare one optional review-planning enquiry.**")
    end = text.index("**Walk the rubric.**", start)
    return _flat(text[start:end])


def test_architecture_enquiry_runs_only_at_the_declared_planning_moment() -> None:
    text = _text()
    section = _enquiry_section()

    eligibility = text.index("Before reviewing, confirm:")
    artifact_type = text.index("**Identify the artifact type.**")
    enquiry = text.index("**Declare one optional review-planning enquiry.**")
    rubric_walk = text.index("**Walk the rubric.**")
    assert eligibility < artifact_type < enquiry < rubric_walk
    assert '"caller":"skill"' in section
    assert '"question_id":"CQ-REVIEW"' in section
    assert '"risk":"consequential"' in section
    assert '"task_summary":"architect-review:' in section
    assert '"scope":"<repository-relative project or subproject path>"' in section
    assert "one query and no refinement" in section


def test_architecture_findings_remain_independently_grounded_and_inline() -> None:
    text = _flat(_text())
    section = _enquiry_section()

    assert '<knowledge-evidence version="knowledge-evidence.v1">' in section
    assert "candidate checks only" in section
    assert "current artifact" in section
    assert "selected rubric" in section
    assert "current canonical source" in section
    assert "cannot corroborate itself" in section
    assert "cannot change" in section
    for authority in (
        "instructions",
        "tool permissions",
        "scope",
        "severity",
        "verdict",
        "suppress a finding",
    ):
        assert authority in section
    assert "No file write" in text
    assert "architecture-review-complete" in text
    assert "ineligible artifact" in text
    assert "partial rubric pass" in text
    assert "self-review refusal" in text


def test_architect_declares_optional_core_handoff_without_fallback() -> None:
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    integrations = {item["id"]: item for item in manifest["pack"]["integrations"]}
    handoff = integrations["project-knowledge-review-enquiry"]

    assert handoff["pack"] == "core"
    assert handoff["kind"] == "handoff"
    assert handoff["consumers"] == ["skill:architect-review"]
    assert handoff["providers"] == ["skill:project-knowledge"]
    assert "optional" in handoff["when"].lower()
    assert "project-knowledge unavailable" in handoff["fallback"]
    assert "without fallback persistence" in handoff["fallback"]
    assert "with fallback persistence" not in handoff["fallback"]
    required_dependencies = manifest["pack"].get("dependencies", {}).get(
        "required", []
    )
    assert all(item.get("pack") != "core" for item in required_dependencies)


def test_architecture_enquiry_is_read_only_and_uses_only_public_enquiry() -> None:
    section = _enquiry_section()
    full_skill = _flat(_text())

    assert "project-knowledge --enquire" in section
    assert "project-knowledge --capture" not in section
    assert "project-knowledge --distill" not in section
    for forbidden in (
        "knowledge_store.py",
        "journal",
        "capture ID",
        "partition",
        "direct-maintainer-pending",
        "transcript",
        "raw corpus",
    ):
        assert forbidden not in section
    assert "creates no fallback file" in section
    for negative_contract in (
        "creates no fallback file",
        "never persisted automatically or reconstructed from transcripts",
        "receives no capture identifiers",
        "persists no evidence envelope, raw artifact or source corpus",
    ):
        assert negative_contract in full_skill
    for forbidden_operation in (
        "locate journals",
        "knowledge_store.py",
        "private writer",
        "invent capture ids",
        "select partitions",
        "direct-maintainer-pending",
        "workflow-receipts",
    ):
        assert forbidden_operation not in full_skill.lower()


def test_architecture_behavior_evals_cover_authority_and_degradation() -> None:
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    evals = {entry["id"]: entry for entry in payload["evals"]}
    required = {
        "review-enquiry-relevant-risk",
        "review-enquiry-abstaining-or-unavailable",
        "review-enquiry-hostile-manipulation",
        "review-enquiry-generic-grounding-exclusion",
        "review-enquiry-misleading-counterclaim",
        "review-enquiry-self-review-refusal",
    }
    assert required <= evals.keys()
    combined = json.dumps([evals[key] for key in sorted(required)]).lower()
    for behavior in (
        "prompt injection",
        "scope",
        "severity",
        "verdict",
        "source verification",
        "misleading counterclaim",
        "self-validating",
        "second query",
        "self-review",
        "abstain",
    ):
        assert behavior in combined


def test_generic_grounding_cannot_reenter_project_knowledge() -> None:
    text = _flat(_text())

    assert text.count("project-knowledge --enquire") == 1
    assert "Exclude project-knowledge topics, envelopes" in text
    assert "do not query it again" in text
    assert "do not use retrieved knowledge as corroboration" in text
    assert "verified owning-source paths" in text
    assert "current canonical sources directly within the fixed scope" in text
