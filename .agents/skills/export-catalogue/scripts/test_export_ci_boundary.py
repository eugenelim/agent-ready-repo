"""Tests for check_ci_boundary (spec/catalogue-ci-export-boundary AC7)."""

from __future__ import annotations

from pathlib import Path

import export_verify as V


def _tree(tmp: Path, files: dict[str, str]) -> Path:
    root = tmp / "target"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_ci_contract_guide_eligible(tmp_path: Path) -> None:  # STUB: AC7
    """guides/_shared/reference/catalogue-ci-contract.md is not flagged."""
    root = _tree(tmp_path, {
        "guides/_shared/reference/catalogue-ci-contract.md": "# CI contract\n",
    })
    assert V.check_ci_boundary(root) == []


def test_github_workflow_flagged(tmp_path: Path) -> None:  # STUB: AC7
    """A .github/workflows/ file is flagged as ci_path."""
    root = _tree(tmp_path, {
        ".github/workflows/publish-catalogue.yml": "on: push\n",
    })
    v = V.check_ci_boundary(root)
    assert v and any(x.anchor == "ci_path" for x in v)


def test_github_adapter_path_passes(tmp_path: Path) -> None:  # STUB: AC7
    """A .github/skills/ file (Copilot adapter projection) is NOT flagged."""
    root = _tree(tmp_path, {
        ".github/skills/core/SKILL.md": "# core skill\n",
    })
    assert V.check_ci_boundary(root) == []


def test_ci_root_file_flagged(tmp_path: Path) -> None:  # STUB: AC7
    """A root Jenkinsfile is flagged as ci_path (exercises Check 2)."""
    root = _tree(tmp_path, {"Jenkinsfile": "pipeline {}\n"})
    v = V.check_ci_boundary(root)
    assert v and any(x.anchor == "ci_path" for x in v)


def test_unknown_provider_flagged(tmp_path: Path) -> None:  # STUB: AC7
    """A fictional .ci/step.yml (dot-directory, not in allowlist) is flagged."""
    root = _tree(tmp_path, {".ci/step.yml": "steps: []\n"})
    v = V.check_ci_boundary(root)
    assert v and any(x.anchor == "ci_path" for x in v)


def test_badge_url_in_guide_flagged(tmp_path: Path) -> None:  # STUB: AC7
    """A guide file containing a GitHub Actions badge URL is flagged."""
    root = _tree(tmp_path, {
        "guides/core/README.md": (
            "![CI](https://github.com/acme/repo/actions/workflows/ci.yml/badge.svg)\n"
        ),
    })
    v = V.check_ci_boundary(root)
    assert v and any(x.anchor == "ci_badge_url" for x in v)


def test_badge_url_outside_guides_flagged(tmp_path: Path) -> None:  # STUB: AC7
    """A root README.md containing a badge URL is also flagged (badge scan is not
    limited to guides/)."""
    root = _tree(tmp_path, {
        "README.md": (
            "![CI](https://github.com/acme/repo/actions/workflows/ci.yml/badge.svg)\n"
        ),
    })
    v = V.check_ci_boundary(root)
    assert v and any(x.anchor == "ci_badge_url" for x in v)


def test_clean_export_passes(tmp_path: Path) -> None:  # STUB: AC7
    """A realistic export scaffold with no CI files passes check_ci_boundary and
    the existing white-label verify(). Includes root dotfiles (.gitignore) seeded
    by step 4 — guards the len(parts) > 1 invariant in Check 3."""
    root = _tree(tmp_path, {
        "guides/_shared/reference/catalogue-ci-contract.md": "# CI contract\n",
        "guides/core/how-to/get-started.md": "# Getting started\n",
        "docs/CONVENTIONS.md": "# Conventions\n",
        ".claude/skills/core/SKILL.md": "# core skill\n",
        ".agents/skills/core/SKILL.md": "# core skill\n",
        ".github/skills/core/SKILL.md": "# core skill\n",
        ".gitignore": "__pycache__/\n*.pyc\n",
        ".editorconfig": "[*]\nindent_style = space\n",
        "AGENTS.md": "# Agents\n",
        "workspace.toml": "[workspace]\n",
    })
    assert V.check_ci_boundary(root) == []
    anchors = {"url": "https://example.com", "email": "", "slug": "", "owner": ""}
    assert V.verify(root, anchors, mode="white-label") == []
