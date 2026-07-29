"""Tests for agentbundle.catalogue_tooling.identity."""

from __future__ import annotations

from pathlib import Path

from agentbundle.catalogue_tooling.identity import (
    BINARY_EXT,
    Violation,
    check_ci_boundary,
    verify,
)

# ---------------------------------------------------------------------------
# verify()
# ---------------------------------------------------------------------------


def test_verify_white_label_clean(tmp_path: Path) -> None:
    (tmp_path / "file.md").write_text("Hello world", encoding="utf-8")
    anchors = {"name": "example-corp"}
    violations = verify(tmp_path, anchors, mode="white-label")
    assert violations == []


def test_verify_white_label_hit(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Built by example-corp", encoding="utf-8")
    anchors = {"name": "example-corp"}
    violations = verify(tmp_path, anchors, mode="white-label")
    assert len(violations) == 1
    assert violations[0].anchor == "name"
    assert violations[0].path == "README.md"


def test_verify_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("EXAMPLE-CORP is the owner", encoding="utf-8")
    anchors = {"name": "example-corp"}
    violations = verify(tmp_path, anchors, mode="white-label")
    assert len(violations) >= 1


def test_verify_attributed_allowed_in_surface(tmp_path: Path) -> None:
    (tmp_path / "catalogue.toml").write_text(
        'upstream = "example-corp"', encoding="utf-8"
    )
    anchors = {"name": "example-corp"}
    violations = verify(
        tmp_path, anchors, mode="attributed", attribution_paths=["catalogue.toml"]
    )
    assert violations == []


def test_verify_attributed_violation_outside_surface(tmp_path: Path) -> None:
    (tmp_path / "catalogue.toml").write_text(
        'upstream = "example-corp"', encoding="utf-8"
    )
    (tmp_path / "packs").mkdir()
    (tmp_path / "packs" / "skill.md").write_text(
        "example-corp created this", encoding="utf-8"
    )
    anchors = {"name": "example-corp"}
    violations = verify(
        tmp_path, anchors, mode="attributed", attribution_paths=["catalogue.toml"]
    )
    assert any(v.path.startswith("packs") for v in violations)


def test_verify_skips_binary_extensions(tmp_path: Path) -> None:
    for ext in (".png", ".pyc", ".woff"):
        (tmp_path / f"asset{ext}").write_bytes(b"example-corp")
    anchors = {"name": "example-corp"}
    violations = verify(tmp_path, anchors, mode="white-label")
    assert violations == []


def test_verify_empty_anchors(tmp_path: Path) -> None:
    (tmp_path / "file.md").write_text("anything", encoding="utf-8")
    assert verify(tmp_path, {}, mode="white-label") == []


def test_verify_empty_anchor_value_skipped(tmp_path: Path) -> None:
    # Empty string values are skipped (if val guard in the comprehension).
    (tmp_path / "file.md").write_text("anything in the text", encoding="utf-8")
    anchors = {"x": ""}  # empty — skipped by the `if val` guard
    assert verify(tmp_path, anchors, mode="white-label") == []


# ---------------------------------------------------------------------------
# check_ci_boundary()
# ---------------------------------------------------------------------------

def test_check_ci_boundary_clean(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    violations = check_ci_boundary(tmp_path)
    assert violations == []


def test_check_ci_boundary_workflow(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("on: push", encoding="utf-8")
    violations = check_ci_boundary(tmp_path)
    assert any(v.anchor == "ci_path" for v in violations)


def test_check_ci_boundary_gitlab(tmp_path: Path) -> None:
    (tmp_path / ".gitlab-ci.yml").write_text("stages: []", encoding="utf-8")
    violations = check_ci_boundary(tmp_path)
    assert any(v.anchor == "ci_path" for v in violations)


def test_check_ci_boundary_unknown_dot_dir(tmp_path: Path) -> None:
    unknown = tmp_path / ".some-unknown-provider"
    unknown.mkdir()
    (unknown / "config.yml").write_text("x: 1", encoding="utf-8")
    violations = check_ci_boundary(tmp_path)
    assert any(v.anchor == "ci_path" for v in violations)


def test_check_ci_boundary_badge_url(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "[![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg)]()",
        encoding="utf-8",
    )
    violations = check_ci_boundary(tmp_path)
    assert any(v.anchor == "ci_badge_url" for v in violations)


def test_check_ci_boundary_allowed_github_skills(tmp_path: Path) -> None:
    gh_skills = tmp_path / ".github" / "skills"
    gh_skills.mkdir(parents=True)
    (gh_skills / "my-skill.md").write_text("---\nname: my-skill\n---\n", encoding="utf-8")
    violations = check_ci_boundary(tmp_path)
    assert violations == []


# ---------------------------------------------------------------------------
# Violation equality
# ---------------------------------------------------------------------------

def test_violation_equality() -> None:
    v1 = Violation("a/b.md", "name", 3)
    v2 = Violation("a/b.md", "name", 3)
    assert v1 == v2
    assert v1 != Violation("a/b.md", "name", 4)


def test_binary_ext_set_is_frozenset() -> None:
    assert isinstance(BINARY_EXT, frozenset)
    assert ".png" in BINARY_EXT
