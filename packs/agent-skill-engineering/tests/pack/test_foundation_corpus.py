"""Contracts for the governed foundation corpus and generated router."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml

PACK_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = PACK_ROOT / "okf" / "agent-skill-engineering-foundation"
CONCEPT_ROOT = BUNDLE_ROOT / "concepts"
ROUTER_ROOT = PACK_ROOT / ".apm" / "skills" / "ase-okf-reference"
EXPECTED_TOPICS = {
    "framing-and-trigger-quality",
    "instruction-density-and-progressive-disclosure",
    "resources-scripts-and-exit-contracts",
}


def _frontmatter(path: Path) -> dict[str, object]:
    """Read YAML frontmatter from an authored concept."""

    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def _digest_tree(root: Path) -> dict[str, str]:
    """Return stable SHA-256 digests for regular files below root."""

    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _generated_tree_digest(root: Path) -> str:
    """Bind evaluation evidence to exact generated paths and bytes."""

    canonical = json.dumps(
        _digest_tree(root),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _read_staged_confined(root: Path, relative_path: str, reads: list[Path]) -> str:
    """Read one regular staged file after resolving it beneath the staged root."""

    target = (root / relative_path).resolve(strict=True)
    target.relative_to(root.resolve(strict=True))
    assert target.is_file() and not target.is_symlink()
    reads.append(target)
    return target.read_text(encoding="utf-8")


def test_foundation_corpus_is_exactly_three_inert_governed_topics() -> None:
    paths = sorted(CONCEPT_ROOT.glob("*.md"))
    assert {path.stem for path in paths} == EXPECTED_TOPICS
    for path in paths:
        metadata = _frontmatter(path)
        assert metadata == {
            "id": path.stem,
            "title": metadata["title"],
            "type": "Reference",
            "status": "Active",
            "license": "Apache-2.0 OR MIT",
        }
        text = path.read_text(encoding="utf-8")
        for forbidden in ("executor:", "attester:", "remote:", "tools:"):
            assert forbidden not in text


def test_foundation_router_cases_are_predeclared_bounded_and_include_near_misses() -> None:
    cases = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "router-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(cases) >= 20
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(set(case["expected_topics"]) <= EXPECTED_TOPICS for case in cases)
    assert all(len(case["expected_topics"]) <= 3 for case in cases)
    assert sum(not case["expected_topics"] for case in cases) >= 5
    assert any(len(case["expected_topics"]) == 3 for case in cases)


def test_independent_router_results_meet_precision_and_recall_gate() -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    cases = {
        case["id"]: set(case["expected_topics"])
        for case in json.loads(
            (fixture_root / "router-cases.json").read_text(encoding="utf-8")
        )
    }
    evidence = json.loads(
        (fixture_root / "router-results.json").read_text(encoding="utf-8")
    )
    results = {
        case["id"]: set(case["actual_topics"])
        for case in evidence["results"]
    }
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")["metadata"]

    assert evidence["evaluation_mode"] == "independent-read-only-subcontext"
    assert evidence["source_digest"] == metadata["source-digest"]
    assert evidence["router_digest"] == (
        "sha256:" + hashlib.sha256((ROUTER_ROOT / "SKILL.md").read_bytes()).hexdigest()
    )
    assert evidence["generated_tree_digest"] == _generated_tree_digest(ROUTER_ROOT)
    assert set(results) == set(cases)
    assert all(actual <= EXPECTED_TOPICS and len(actual) <= 3 for actual in results.values())

    true_positive = sum(len(results[key] & expected) for key, expected in cases.items())
    false_positive = sum(len(results[key] - expected) for key, expected in cases.items())
    false_negative = sum(len(expected - results[key]) for key, expected in cases.items())
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    exact_selection_rate = sum(
        results[key] == expected for key, expected in cases.items()
    ) / len(cases)
    bounded_selection_rate = sum(len(actual) <= 3 for actual in results.values()) / len(
        results
    )

    assert exact_selection_rate >= 0.90
    assert bounded_selection_rate >= 0.90
    assert precision >= 0.90
    assert recall >= 0.90
    assert all(not results[key] for key, expected in cases.items() if not expected)


def test_generated_router_is_inert_bounded_and_source_independent() -> None:
    router = (ROUTER_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")
    assert metadata["metadata"]["boundaries"] == ["filesystem_read_untrusted"]
    assert metadata["metadata"]["generated-by"] == (
        "compile-okf agentbundle-okf/v1"
    )
    assert "generated-by: compile-okf agentbundle-okf/v1" in router
    assert "Read `references/okf/index.md` first" in router
    assert "do not load the full bundle up front" in router
    assert "filesystem_write" not in router
    assert "../okf/" not in router
    assert "Not a selectable skill." in router
    assert (
        "Inert reference data invoked only by another skill's explicit "
        "agent-skill-engineering-reference/v1 provider call" in router
    )
    assert "must never be chosen to satisfy a user's question on any subject" in router
    # The activation surface must not restate the domain or purpose that the
    # user-facing workflows own; capability detection reads the metadata block.
    description = router.split("description:", 1)[1].split("\nmetadata:", 1)[0]
    assert "agent skill engineering" not in description
    assert "authoring, review, evaluation" not in description


def test_generated_router_exposes_explicit_provider_capability() -> None:
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")["metadata"]
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    declared = manifest["pack"]["metadata"]["okf"]["bundles"][0]["provider"]

    assert metadata["knowledge-provider"] == declared
    assert declared == {
        "contract-version": "agent-skill-engineering-reference/v1",
        "domain": "agent skill engineering",
        "purpose": (
            "Provide bounded compiled guidance for authoring, review, evaluation, "
            "and extension-design questions."
        ),
        "task-kinds": [
            "skill-authoring",
            "skill-review",
            "skill-eval-ci",
            "agent-extension-design",
        ],
        "invocation": "explicit-workflow-only",
        "ownership-manifest": ".okf-generated.json",
    }


def test_generated_manifest_owns_only_router_outputs() -> None:
    manifest = json.loads((PACK_ROOT / ".okf-generated.json").read_text(encoding="utf-8"))
    managed = manifest["managed"]
    assert len([item for item in managed if item["kind"] == "okf-router"]) == 1
    assert len([item for item in managed if item["kind"] == "okf-reference"]) == 3
    assert all(
        item["output_path"].startswith(
            ".apm/skills/ase-okf-reference/"
        )
        for item in managed
    )
    assert not any("../" in item["output_path"] for item in managed)


def test_generated_tree_has_stable_regular_file_digests() -> None:
    first = _digest_tree(ROUTER_ROOT)
    second = _digest_tree(ROUTER_ROOT)
    assert first == second
    routes = re.findall(
        r"\(([^)]+\.md)\)",
        (ROUTER_ROOT / "references" / "okf" / "concepts" / "index.md").read_text(
            encoding="utf-8"
        ),
    )
    assert set(routes) == {f"{topic}.md" for topic in EXPECTED_TOPICS}


def test_staged_router_remains_complete_without_authored_okf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    cases = json.loads((fixture_root / "router-cases.json").read_text(encoding="utf-8"))
    evidence = json.loads(
        (fixture_root / "router-results.json").read_text(encoding="utf-8")
    )
    results = {item["id"]: item["actual_topics"] for item in evidence["results"]}
    staged = tmp_path / "ase-okf-reference"
    shutil.copytree(ROUTER_ROOT, staged)
    assert not (staged / "okf").exists()

    original_read_text = Path.read_text

    def checkout_unavailable(path: Path, *args: object, **kwargs: object) -> str:
        if path.resolve(strict=False).is_relative_to(PACK_ROOT.resolve(strict=True)):
            raise AssertionError(f"staged evaluation attempted checkout read: {path}")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", checkout_unavailable)
    reads: list[Path] = []
    _read_staged_confined(staged, "SKILL.md", reads)
    _read_staged_confined(staged, "references/okf/index.md", reads)
    concept_index = _read_staged_confined(
        staged,
        "references/okf/concepts/index.md",
        reads,
    )
    routes = set(re.findall(r"\(([^)]+\.md)\)", concept_index))
    assert routes == {f"{topic}.md" for topic in EXPECTED_TOPICS}

    assert {case["id"] for case in cases} == set(results)
    for case in cases:
        assert case["prompt"]
        for topic in results[case["id"]]:
            _read_staged_confined(
                staged,
                f"references/okf/concepts/{topic}.md",
                reads,
            )
    staged_root = staged.resolve(strict=True)
    assert reads
    assert all(path.is_relative_to(staged_root) for path in reads)
