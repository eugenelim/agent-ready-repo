"""Verify that export-catalogue skill has been removed from the catalogue.

These tests are structural — they assert file-system absence to pin the removal
against accidental re-introduction. They also verify that the reusable logic
(identity.py) landed in the right place.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Root of the agent-ready-repo project, found by walking up from this file.
_HERE = Path(__file__).resolve()


def _find_repo_root() -> Path:
    """Walk up to the first directory containing 'packs/' and 'packages/'."""
    p = _HERE
    for _ in range(10):
        if (p / "packs").is_dir() and (p / "packages").is_dir():
            return p
        p = p.parent
    raise RuntimeError("Could not locate repo root from test file path")


_REPO = _find_repo_root()


# ---------------------------------------------------------------------------
# Absence tests
# ---------------------------------------------------------------------------

def test_export_catalogue_skill_removed_from_packs() -> None:
    skill_dir = _REPO / "packs" / "catalogue-curation" / ".apm" / "skills" / "export-catalogue"
    assert not skill_dir.exists(), (
        f"export-catalogue skill directory still present at {skill_dir}; "
        "it should have been removed (superseded by `agentbundle catalogue init --preset"
        " self-hosted`)"
    )


def test_export_catalogue_skill_removed_from_claude_projection() -> None:
    skill_dir = _REPO / ".claude" / "skills" / "export-catalogue"
    assert not skill_dir.exists(), (
        f"export-catalogue still projected at {skill_dir}"
    )


def test_export_catalogue_skill_removed_from_agents_projection() -> None:
    skill_dir = _REPO / ".agents" / "skills" / "export-catalogue"
    assert not skill_dir.exists(), (
        f"export-catalogue still projected at {skill_dir}"
    )


def test_export_a_fork_guide_removed() -> None:
    guide = _REPO / "guides" / "catalogue-curation" / "how-to" / "export-a-fork.md"
    assert not guide.exists(), (
        f"export-a-fork.md guide still present at {guide}"
    )


# ---------------------------------------------------------------------------
# Identity module presence (replacement landed correctly)
# ---------------------------------------------------------------------------

def test_identity_module_present() -> None:
    identity_module = (
        _REPO / "packages" / "agentbundle" / "agentbundle" / "catalogue_tooling" / "identity.py"
    )
    assert identity_module.exists(), "identity.py migration target not found"


def test_identity_module_exports_expected_symbols() -> None:
    from agentbundle.catalogue_tooling.identity import (
        BINARY_EXT,
        check_ci_boundary,
        verify,
    )
    assert callable(verify)
    assert callable(check_ci_boundary)
    assert isinstance(BINARY_EXT, frozenset)


# ---------------------------------------------------------------------------
# No export-catalogue in active lint guard
# ---------------------------------------------------------------------------

def test_lint_guard_does_not_reference_export_catalogue_in_dup_groups() -> None:
    guard_path = _REPO / "tools" / "lint-catalogue-curation-guard.py"
    assert guard_path.exists()
    content = guard_path.read_text(encoding="utf-8")
    # The dup_groups should NOT list export-catalogue.
    # Locate the DUP_GROUPS dict and assert export-catalogue is absent from it.
    import ast
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DUP_GROUPS":
                    # Check no string constant in the dict is "export-catalogue"
                    for child in ast.walk(node.value):
                        if isinstance(child, ast.Constant) and child.value == "export-catalogue":
                            pytest.fail(
                                "DUP_GROUPS in lint-catalogue-curation-guard.py still "
                                "references 'export-catalogue'"
                            )


# ---------------------------------------------------------------------------
# write_jail.py comment does not reference export-catalogue
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill", ["assimilate-primitive", "assimilate-repo"])
def test_write_jail_comment_no_export_catalogue(skill: str) -> None:
    wj = (
        _REPO / "packs" / "catalogue-curation" / ".apm" / "skills"
        / skill / "scripts" / "write_jail.py"
    )
    assert wj.exists(), f"write_jail.py not found for {skill}"
    content = wj.read_text(encoding="utf-8")
    assert "export-catalogue" not in content, (
        f"write_jail.py for {skill} still references 'export-catalogue'"
    )
