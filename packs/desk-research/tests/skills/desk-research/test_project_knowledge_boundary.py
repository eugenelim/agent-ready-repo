from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "desk-research" / "SKILL.md"
EVALS = PACK_ROOT / ".apm" / "skills" / "desk-research" / "evals" / "evals.json"


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _flat(value: str) -> str:
    return re.sub(r"\s+", " ", value)


def _knowledge_section() -> str:
    text = _text()
    start = text.index("## Project-knowledge handoff")
    end = text.index("## Retrievers", start)
    return _flat(text[start:end])


def test_ephemeral_quick_and_incomplete_surveys_never_capture() -> None:
    section = _knowledge_section()

    assert "Quick mode is an absolute knowledge non-gate" in section
    for incomplete in (
        "created-only",
        "abandoned",
        "incomplete",
        "confidence",
        "known-unknown",
        "moderator",
        "counterreview",
    ):
        assert incomplete in section
    for gate in (
        "research-survey-complete",
        "research-applied-survey-complete",
        "research-survey-counterreview-complete",
    ):
        assert gate in section

    pipeline = _text().index("## Pipeline")
    handoff = _text().index("## Project-knowledge handoff")
    assert pipeline < handoff


def test_non_survey_typed_products_are_explicit_no_integration_paths() -> None:
    section = _knowledge_section()

    for product in (
        "fact-check",
        "comparison-matrix",
        "shortlist",
        "blueprint",
        "hypotheses",
        "methodology",
    ):
        assert f"`{product}`" in section
    assert "terminal and incomplete forms" in section
    assert "no capture, distillation, or enquiry" in section
    assert "`research.md`" in section


def test_terminal_survey_uses_typed_capture_and_only_same_gate_receipts() -> None:
    section = _knowledge_section()

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
    assert "producer-owned transient handoff scratch" in section
    assert "project-knowledge --capture" in section
    assert '"selection_mode":"workflow-receipts"' in section
    assert "only the receipts returned by that same gate" in section
    assert "direct-maintainer-pending" in section
    assert "project-knowledge unavailable" in section
    assert (
        "project-knowledge capture ineligible: non-repository research output"
        in section
    )
    assert "before provider discovery" in section
    assert "creates no fallback file" in section
    assert "must not locate journals" in section
    assert "must not import the private writer" in section
    assert "must not invent capture IDs" in section
    assert "must not select partitions" in section
    assert "must not mine transcripts" in section
    assert "must not copy a raw source corpus" in section


def test_instructed_producer_version_is_decoupled_from_the_pack_release() -> None:
    """The gate must instruct a contract identifier, not the pack release.

    Instructing the shipped release made every desk-research bump a prose edit
    here, and recorded a release number in a field whose job is to say which
    producer contract emitted the observation — free text the schema never
    parses and no consumer branches on. Asserting the literal, and that the
    release string is absent, means re-introducing the mirror reddens this test
    instead of shipping.
    """
    release = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))[
        "pack"
    ]["version"]
    section = _knowledge_section()

    assert "`desk-research-producer-profile.v1`" in section
    assert release != "desk-research-producer-profile.v1"
    assert release not in section


def test_capture_artifact_and_freshness_mapping_is_exact_by_gate() -> None:
    section = _knowledge_section()

    assert (
        "`research-survey-complete` and `research-applied-survey-complete` "
        "use the survey for `semantic_gate.artifact`, "
        "`provenance.sources`, and `freshness_anchor.path`"
        in section
    )
    assert (
        "`research-survey-counterreview-complete` uses the survey for "
        "`semantic_gate.artifact`, the survey and linked counterpoints in "
        "`provenance.sources`, and the counterpoints for "
        "`freshness_anchor.path`"
        in section
    )
    assert "Every listed path must be a confined regular file" in section


def test_capture_residue_never_promotes_research_authority() -> None:
    section = _knowledge_section()

    for excluded in (
        "survey",
        "source corpus",
        "quotation",
        "citation",
        "claim",
        "confidence judgment",
        "known unknown",
        "counter-evidence",
        "verdict",
    ):
        assert excluded in section
    assert "independently reusable research practice" in section
    assert "carefully sanitized evidence residue" in section
    assert "Scratch is never persisted automatically" in section


def test_behavior_evals_cover_hostile_and_degraded_knowledge() -> None:
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    combined = json.dumps(payload["evals"]).lower()

    for behavior in (
        "prompt injection",
        "source selection",
        "tool permissions",
        "citation",
        "claim",
        "confidence",
        "counter-evidence",
        "self-validating",
        "independent direct-source verification",
        "personal output root",
        "project-knowledge unavailable",
        "no fallback",
        "abstain",
    ):
        assert behavior in combined
