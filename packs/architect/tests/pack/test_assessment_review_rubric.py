"""Parity and planted-failure contracts for assessment report review."""

from __future__ import annotations

from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = PACK_ROOT / ".apm" / "skills" / "architect-review"
REVIEW_SKILL = REVIEW_ROOT / "SKILL.md"
RUBRIC = REVIEW_ROOT / "references" / "rubric-assessment.md"
REVIEWER = PACK_ROOT / ".apm" / "agents" / "design-reviewer.md"
FIXTURE = (
    PACK_ROOT
    / "tests"
    / "skills"
    / "architect-assess"
    / "testdata"
    / "flawed-assessment.md"
)
EXPECTED_REVIEW = FIXTURE.with_name("flawed-assessment.expected-review.yaml")
REVIEW_TRANSCRIPT = FIXTURE.with_name("flawed-assessment.review-transcript.md")
REVIEW_EVALS = REVIEW_ROOT / "evals" / "evals.json"

RUBRIC_CONCERNS = (
    "Scope fidelity",
    "Evidence strength and provenance",
    "Current-state model coherence",
    "Attention heat and hotspot selection",
    "Lens and scenario completeness",
    "Findings, calibration, and alternative explanations",
    "Action traceability and sequencing",
)


def test_inline_and_cold_reviewers_route_assessment_reports_without_rescanning() -> None:
    inline = REVIEW_SKILL.read_text(encoding="utf-8")
    reviewer = REVIEWER.read_text(encoding="utf-8")
    for carrier in (inline, reviewer):
        assert "assessment report" in carrier.lower()
        assert "rubric-assessment.md" in carrier
        assert "do not rescan the repository" in carrier.lower()
    assert "architect-assess" in inline


def test_assessment_rubric_covers_every_methodological_failure_class() -> None:
    rubric = RUBRIC.read_text(encoding="utf-8")
    normalized = " ".join(rubric.split())
    for concern in RUBRIC_CONCERNS:
        assert f"## {concern}" in rubric
    for required in (
        "generic knowledge is never cited as proof",
        "Heat is used only to select investigation priority",
        "Severity expresses consequence; confidence expresses evidence strength",
        "Every action wave names intended outcome",
        "backend compliance audit presented as a whole-platform modernization assessment",
    ):
        assert required in normalized


def test_planted_fixture_exercises_scope_heat_lens_evidence_and_action_failures() -> None:
    fixture = FIXTURE.read_text(encoding="utf-8")
    normalized = " ".join(fixture.lower().split())
    planted_signals = {
        "scope_overclaim": ("whole platform", "backend request handlers only"),
        "folders_as_architecture": ("folders are the three runtime components",),
        "missing_evidence": ("All other evidence is green",),
        "heat_as_severity": ("Architecture risk score", "blocker-severity defects"),
        "weak_finding": ("grep found",),
        "missing_agentic_lenses": ("were not assessed", "not production-ready"),
        "untraceable_action": ("Split every file above 500 lines",),
        "unsafe_sequence": ("investigate the known cross-tenant write defect after the cleanup",),
        "uncalibrated_confidence": ("Confidence: high",),
    }
    for planted, needles in planted_signals.items():
        for needle in needles:
            assert needle.lower() in normalized, (planted, needle)


def test_cold_review_transcript_detects_every_expected_failure_class() -> None:
    """The planted artifact has a real cold-context verdict, not string-only seeds."""

    expected = yaml.safe_load(EXPECTED_REVIEW.read_text(encoding="utf-8"))
    assert isinstance(expected, dict)
    transcript = REVIEW_TRANSCRIPT.read_text(encoding="utf-8")
    normalized = " ".join(transcript.lower().split())
    assert f"## Verdict {expected['verdict']}".lower() in normalized
    assert set(expected["review_surfaces"]) == {"architect-review", "design-reviewer"}
    for finding_class, needles in expected["required_finding_classes"].items():
        for needle in needles:
            assert needle.lower() in normalized, (finding_class, needle)


def test_both_review_surfaces_are_wired_to_the_expected_failure_contract() -> None:
    """Inline and forked review carry the same fixture verdict and rubric classes."""

    inline = REVIEW_SKILL.read_text(encoding="utf-8")
    reviewer = REVIEWER.read_text(encoding="utf-8")
    rubric = RUBRIC.read_text(encoding="utf-8")
    evals = REVIEW_EVALS.read_text(encoding="utf-8")
    for carrier in (inline, reviewer):
        assert "assessment report" in carrier.lower()
        assert "rubric-assessment.md" in carrier
    assert "flawed-assessment.expected-review.yaml" in evals
    for anchor in (
        "Scope fidelity",
        "Evidence strength and provenance",
        "Attention heat and hotspot selection",
        "Lens and scenario completeness",
        "Action traceability and sequencing",
    ):
        assert anchor in rubric
