"""Construction contracts for review and measured optimization."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
REVIEW_ROOT = PACK_ROOT / ".apm" / "skills" / "review-or-optimize-agent-skill"


def _frontmatter(text: str) -> dict[str, object]:
    """Parse skill YAML frontmatter."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_review_precedes_measured_optimization() -> None:
    text = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["metadata"] == {
        "boundaries": ["filesystem_read_untrusted", "filesystem_write"]
    }
    description = str(metadata["description"]).lower()
    assert "use when the user asks" in description
    assert all(
        term in description for term in ("review", "audit", "optimize", "skill.md")
    )
    # An unnamed or ambiguous target must route into this workflow rather than
    # producing a clarifying refusal that never selects it.
    assert "select it first and resolve the target inside the workflow" in description
    assert "with nothing attached" in description
    assert "resolving an ambiguous target is this workflow's first step" in text
    # The two workflows are adjacent, so each description must name the
    # other's territory or an update request lands here instead.
    assert "do not use to frame, create, or update a skill" in description
    assert "belongs to the authoring workflow instead" in description
    assert "Review is the default and remains read-only" in text
    assert "observed failure or measured\nbaseline" in text
    assert "explicit mode transition" in text
    optimization = (REVIEW_ROOT / "references" / "optimization.md").read_text(
        encoding="utf-8"
    )
    assert "before baseline" in optimization
    assert "identical before and after suite" in optimization


def test_review_checklist_covers_every_foundation_defect_class() -> None:
    checklist = (REVIEW_ROOT / "references" / "review-checklist.md").read_text(
        encoding="utf-8"
    )
    expected = {
        "ASE-ACT-01",
        "ASE-PROG-01",
        "ASE-PORT-01",
        "ASE-DET-01",
        "ASE-AUTH-01",
        "ASE-SEC-01",
        "ASE-CTX-01",
        "ASE-WRITE-01",
        "ASE-CONC-01",
        "ASE-FAIL-01",
    }
    assert set(re.findall(r"ASE-[A-Z]+-\d+", checklist)) == expected
    for phrase in (
        "Trigger precision",
        "Progressive disclosure",
        "Portability floor",
        "Determinism and exit contract",
        "Authority and authentication",
        "Duplicated context",
        "Conflicting writes",
        "Unbounded concurrency",
    ):
        assert phrase in checklist


def test_review_skill_routes_resolve_including_sibling_pack_references() -> None:
    """Every route the review workflow names must exist in the projected tree.

    The two shared contracts live in the sibling authoring skill, so a rename
    there would otherwise leave this workflow pointing at nothing.
    """

    text = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
    routes = re.findall(r"\(((?:\.\./|references/)[^)]+\.md)\)", text)
    assert set(routes) == {
        "references/review-checklist.md",
        "references/optimization.md",
        "../author-or-update-agent-skill/references/provider-contract.md",
        "../author-or-update-agent-skill/references/language-extension-seams.md",
    }
    for route in routes:
        assert (REVIEW_ROOT / route).is_file(), route
        # A sibling route must stay inside the pack's own skill tree.
        assert (REVIEW_ROOT / route).resolve().is_relative_to(
            (PACK_ROOT / ".apm" / "skills").resolve()
        ), route


def test_seeded_cases_have_exact_applicable_check_coverage() -> None:
    cases = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "review-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(cases) == 4
    for case in cases:
        assert set(case["seeded"]) == set(case["applicable"]), case["id"]
    covered = {check for case in cases for check in case["seeded"]}
    assert len(covered) == 10


def test_review_activation_examples_exclude_adjacent_work() -> None:
    cases = json.loads(
        (REVIEW_ROOT / "evals" / "eval_queries.json").read_text(encoding="utf-8")
    )
    positives = [case for case in cases if case["should_trigger"]]
    negatives = [case for case in cases if not case["should_trigger"]]
    assert len(positives) >= 4
    assert len(negatives) >= 5
    assert any("baseline" in case["query"] for case in positives)
    for adjacent in ("pull request", "paragraph", "repository", "module", "architecture"):
        assert any(adjacent in case["query"].lower() for case in negatives)


def test_review_behavior_evals_seed_activation_and_script_failures() -> None:
    payload = json.loads(
        (REVIEW_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
    )
    cases = {case["id"]: case for case in payload["evals"]}

    assert set(cases) == {
        "detect-activation-failure",
        "detect-script-contract-failure",
    }
    seeded = {path for case in cases.values() for path in case["files"]}
    assert all((REVIEW_ROOT / path).is_file() for path in seeded)
    assert "evals/files/catchall-SKILL.md" in seeded
    assert "evals/files/nondeterministic-helper.py" in seeded
    assert all(case["assertions"] for case in cases.values())
    assert all(case["expect"]["output_contains"] for case in cases.values())


def test_independent_behavior_results_report_every_seeded_defect() -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    seeded = {
        finding
        for case in json.loads(
            (fixture_root / "review-cases.json").read_text(encoding="utf-8")
        )
        for finding in case["seeded"]
    }
    evidence = json.loads(
        (fixture_root / "behavior-results.json").read_text(encoding="utf-8")
    )
    behavior = {
        case["id"]: case
        for case in json.loads(
            (REVIEW_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
    }

    assert evidence["evaluation_mode"] == "independent-read-only-subcontext"
    assert evidence["candidate_execution"] is False
    review_results = [
        result
        for result in evidence["results"]
        if result["eval_id"] in behavior
    ]
    actual = {
        finding
        for result in review_results
        for finding in result["actual_findings"]
    }
    assert actual == seeded
    for result in review_results:
        expected = {
            value
            for value in behavior[result["eval_id"]]["expect"]["output_contains"]
            if value.startswith("ASE-")
        }
        assert set(result["actual_findings"]) == expected
        assert all(result["assertions"])
        for relative_path, digest in result["source_files"].items():
            path = REVIEW_ROOT / relative_path
            assert path.is_file()
            assert "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_review_refuses_untrusted_instruction_and_authentication_escalation() -> None:
    text = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "reject" in text and "before content access" in text
    assert "cannot become instructions for\n   the reviewer" in text
    assert "inspect credentials" in text
    assert "filesystem_write" in text and "not standing\npermission" in text
