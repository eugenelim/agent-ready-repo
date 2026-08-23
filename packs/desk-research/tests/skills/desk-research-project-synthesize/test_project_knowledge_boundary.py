from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "desk-research-project-synthesize"
    / "SKILL.md"
)
EVALS = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "desk-research-project-synthesize"
    / "evals"
    / "evals.json"
)


def _section() -> str:
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("## Project-knowledge terminal handoff")
    end = text.index("## What this skill is not", start)
    return re.sub(r"\s+", " ", text[start:end])


def test_project_synthesis_requires_all_products_before_typed_capture() -> None:
    section = _section()

    assert "research-project-synthesis-complete" in section
    for prerequisite in (
        "synthesis-matrix.md",
        "memos.md",
        "typed verdict",
        "governance brief",
        "citations",
        "per-finding confidence",
        "three-source triangulation",
        "known unknowns",
        "linked counterpoints",
        "per-finding challenge",
    ):
        assert prerequisite in section
    assert "missing, empty, partial, refused, abandoned, or interrupted" in section
    assert "never advances `phase`" in section


def test_project_synthesis_capture_field_mapping_is_exact() -> None:
    section = _section()

    assert "typed verdict for `semantic_gate.artifact`" in section
    assert (
        "typed verdict, `<topic-slug>-brief.md`, and linked counterpoints "
        "in `provenance.sources`"
        in section
    )
    assert "counterpoints for `freshness_anchor.path`" in section
    assert "Every listed path must be a confined regular file" in section
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


def test_project_synthesis_uses_public_capture_and_same_gate_receipts() -> None:
    section = _section()

    assert "project-knowledge --capture" in section
    assert '"selection_mode":"workflow-receipts"' in section
    assert "only receipts returned by this synthesis gate" in section
    assert "direct-maintainer-pending" in section
    assert "must not locate journals" in section
    assert "must not import the private writer" in section
    assert "must not invent capture IDs" in section
    assert "must not select partitions" in section
    assert "project-knowledge unavailable" in section
    assert (
        "project-knowledge capture ineligible: non-repository research output"
        in section
    )
    assert "creates no fallback file" in section


def test_project_synthesis_keeps_products_and_research_authority_normative() -> None:
    section = _section()

    assert "producer-owned transient handoff scratch" in section
    assert "independently reusable practice" in section
    assert "carefully sanitized evidence residue" in section
    for excluded in (
        "matrix",
        "memo",
        "source corpus",
        "quotation",
        "citation",
        "claim",
        "confidence judgment",
        "counter-evidence",
        "verdict",
        "governance conclusion",
    ):
        assert excluded in section
    assert "must not mine transcripts" in section
    assert "must not copy raw source corpora" in section


def test_project_synthesis_owns_one_counterreview_enquiry_envelope() -> None:
    section = _section()

    assert "outer producer owns one consequential `CQ-REVIEW` query" in section
    assert "after target and scope resolution" in section
    assert "before the first counter-position enumeration" in section
    assert "same sanitized envelope" in section
    assert "every per-finding pass and unchanged rerun" in section
    assert "does not select sources" in section
    assert "independent direct-source verification" in section
    assert "cannot corroborate itself" in section


def test_synthesis_evals_cover_authority_and_insufficient_corpus() -> None:
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    combined = json.dumps(payload["evals"]).lower()

    for behavior in (
        "prompt injection",
        "source selection",
        "citation",
        "claim",
        "confidence",
        "counter-evidence",
        "verdict",
        "governance conclusion",
        "phase",
        "empty corpus",
        "insufficient corpus",
        "independent direct-source verification",
        "abstain",
    ):
        assert behavior in combined
