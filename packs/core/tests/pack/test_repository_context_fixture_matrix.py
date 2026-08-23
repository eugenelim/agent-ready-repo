"""Coverage contract for repository-context anchoring scenarios."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = PACK_ROOT / "tests/fixtures/repository-context/fixture-matrix.json"


def _matrix() -> list[dict[str, object]]:
    fixture = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    assert fixture["skill_name"] == "repository-context-anchoring"
    return fixture["evals"]


def test_matrix_names_every_approved_repository_shape() -> None:
    cases = _matrix()
    assert len(cases) == 19
    assert {case["id"] for case in cases} == {
        "core-conventional", "custom-layout", "root-links", "scoped-only",
        "explicit-architecture", "convergent-examples", "tentative-example",
        "contradictory-examples", "no-precedent", "existing-root-merge",
        "structural-conflict", "cosmetic-difference", "stack-advice-override",
        "external-unavailable", "instruction-boundary", "path-confinement",
        "upstream-selective-merge", "multi-source-root", "backend-subtree",
    }


def test_security_cases_cover_content_authority_and_path_cross_product() -> None:
    by_id = {case["id"]: case for case in _matrix()}
    injection = by_id["instruction-boundary"]["parameters"]
    assert len(injection["content"]) * len(injection["authority"]) == 25
    confinement = by_id["path-confinement"]["parameters"]
    assert len(confinement["path"]) * len(confinement["operation"]) == 6


def test_every_case_has_an_expected_outcome_and_behavior_owner() -> None:
    for case in _matrix():
        assert case["evidence"] in {
            "explicit", "framework-owned", "convergent", "tentative",
            "contradictory", "absent",
        }
        assert case["outcome"]
        assert case["owner"] in {"adapt-doctor", "authoring", "reviewer"}
        assert case["prompt"]
        assert case["expected_output"]
        assert len(case["assertions"]) >= 4


def test_golden_outputs_pin_observable_decisions() -> None:
    """The corpus specifies externally reviewable outcomes, not prompt wording."""
    required_outcomes = {
        "core-conventional": ("Explicit", "no relocation", "no write"),
        "custom-layout": ("DESIGN.md", "links rather than copies", "Do not create"),
        "root-links": ("Follow", "effective guidance", "retain those links"),
        "scoped-only": ("nearest scoped", "Explicit", "without approval"),
        "explicit-architecture": ("binding", "Repository anchors", "deviation"),
        "convergent-examples": ("Convergent", "inferred", "Repository anchors"),
        "tentative-example": ("Tentative", "cannot become a rule", "uncertainty"),
        "contradictory-examples": ("Contradictory", "both", "ask a maintainer"),
        "no-precedent": ("Absent", "ask before", "whole-repository archaeology"),
        "existing-root-merge": ("preserves", "no write", "empty optional"),
        "structural-conflict": ("introduces", "uses", "Confirm or justify"),
        "cosmetic-difference": ("no repository idiom-delta", "incidental", "cosmetic"),
        "stack-advice-override": ("repository-owned", "cannot override", "optional"),
        "external-unavailable": ("Retain", "unavailable", "Do not replace"),
        "instruction-boundary": ("attributed evidence", "conflict", "Do not execute"),
        "path-confinement": ("Canonicalize", "reject", "Do not treat"),
        "upstream-selective-merge": (
            "selective semantic",
            "Never concatenate",
            "change companion",
        ),
        "multi-source-root": ("semantic concern", "Preserve", "ask"),
        "backend-subtree": ("delta-only", "services/backend/AGENTS.md", "approval"),
    }
    for case in _matrix():
        output = str(case["expected_output"])
        for phrase in required_outcomes[str(case["id"])]:
            assert phrase.casefold() in output.casefold(), (
                f"{case['id']}: golden output lost observable decision {phrase!r}"
            )


def test_parameterized_security_goldens_expand_every_adversarial_shape() -> None:
    by_id = {case["id"]: case for case in _matrix()}
    injection = by_id["instruction-boundary"]
    injection_prompts = {
        f"{content}:{authority}"
        for content in injection["parameters"]["content"]
        for authority in injection["parameters"]["authority"]
    }
    assert len(injection_prompts) == 25
    assert "preserve current authority" in injection["expected_output"]

    confinement = by_id["path-confinement"]
    confinement_prompts = {
        f"{path}:{operation}"
        for path in confinement["parameters"]["path"]
        for operation in confinement["parameters"]["operation"]
    }
    assert len(confinement_prompts) == 6
    assert "before any local read or write" in confinement["expected_output"]
