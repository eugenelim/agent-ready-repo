"""Catalogue-curation removal and retained-content checks."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_export_catalogue_skill_removed_from_pack() -> None:
    path = (
        REPO_ROOT
        / "packs"
        / "catalogue-curation"
        / ".apm"
        / "skills"
        / "export-catalogue"
    )
    assert not path.exists()


@pytest.mark.parametrize("projection", [".claude", ".agents"])
def test_export_catalogue_skill_removed_from_projection(projection: str) -> None:
    assert not (REPO_ROOT / projection / "skills" / "export-catalogue").exists()


def test_export_a_fork_guide_removed() -> None:
    path = (
        REPO_ROOT
        / "guides"
        / "catalogue-curation"
        / "how-to"
        / "export-a-fork.md"
    )
    assert not path.exists()


@pytest.mark.parametrize("skill", ["assimilate-primitive", "assimilate-repo"])
def test_write_jail_comment_no_export_catalogue(skill: str) -> None:
    path = (
        REPO_ROOT
        / "packs"
        / "catalogue-curation"
        / ".apm"
        / "skills"
        / skill
        / "scripts"
        / "write_jail.py"
    )
    assert path.exists()
    assert "export-catalogue" not in path.read_text(encoding="utf-8")
