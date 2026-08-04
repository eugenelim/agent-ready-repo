"""Tests for _GitTools — branch validation, commit path intersection, injection defence."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _init_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    for cmd in (
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, check=True, capture_output=True, cwd=str(tmp_path))
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("init")
    subprocess.run(["git", "add", "README.md"], check=True, capture_output=True, cwd=str(tmp_path))
    subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True, cwd=str(tmp_path))
    return tmp_path


class TestGitBranch:
    """git_branch validates via check-ref-format and rejects invalid names (AC14)."""

    def test_valid_branch_created(self, tmp_path: Path) -> None:
        pytest.skip('STUB: AC14 — git_branch({"name": "feat/my-thing"}) → success; git branch list shows it')

    def test_invalid_branch_name_rejected(self, tmp_path: Path) -> None:
        pytest.skip('STUB: AC14 — git_branch({"name": "-bad"}) → error; check-ref-format rejects leading dash')

    def test_branch_unavailable_in_discovery_mode(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC14 — no WORKSPACE_MCP_DISPATCHED_ITEM env → discovery mode → git_branch returns error")


class TestGitCommit:
    """git_commit intersects uncommitted paths with output_pattern (AC14, AC15)."""

    def test_commit_matches_output_pattern(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC14 — write file matching output_pattern; git_commit commits only that file")

    def test_commit_excludes_files_outside_output_pattern(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC14 — write two files; only the one matching output_pattern is staged")

    def test_commit_unavailable_for_work_type(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC14 — work type has no output_pattern → git_commit returns error")

    def test_commit_unavailable_in_discovery_mode(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC14 — discovery mode → error")


class TestGitPush:
    """git_push two-sided branch check guards against mismatched branch names (AC15)."""

    def test_push_rejected_when_arg_differs_from_session_branch(self, tmp_path: Path) -> None:
        pytest.skip('STUB: AC15 — session_branch="feat/a"; git_push({"branch": "feat/b"}) → error')

    def test_push_rejected_when_head_differs_from_session_branch(self, tmp_path: Path) -> None:
        pytest.skip("STUB: AC15 — HEAD moved to different branch; push → error")

    def test_pathspec_separator_prevents_injection(self, tmp_path: Path) -> None:
        pytest.skip('STUB: AC14 injection — path "--inject" treated as a path, not a flag (git add -- ... separator)')
