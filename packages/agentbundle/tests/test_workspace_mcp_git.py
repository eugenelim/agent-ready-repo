"""Stub tests for _GitTools — branch validation, commit path intersection, injection defence.

The behavioral tests are stubs here; the FSM-mode guard integration tests
live in tests/integration/test_workspace_mcp_git_fsm.py (disk + subprocess).
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestGitBranch:
    """git_branch validates via check-ref-format and rejects invalid names."""

    def test_valid_branch_created(self, tmp_path: Path) -> None:
        pytest.skip('STUB: git_branch({"name": "feat/my-thing"}) → success; git branch list shows it')

    def test_invalid_branch_name_rejected(self, tmp_path: Path) -> None:
        pytest.skip('STUB: git_branch({"name": "-bad"}) → error; check-ref-format rejects leading dash')

    def test_branch_unavailable_in_discovery_mode(self, tmp_path: Path) -> None:
        pytest.skip("STUB: no WORKSPACE_MCP_DISPATCHED_ITEM env → discovery mode → git_branch returns error")


class TestGitCommit:
    """git_commit intersects uncommitted paths with output_pattern."""

    def test_commit_matches_output_pattern(self, tmp_path: Path) -> None:
        pytest.skip("STUB: write file matching output_pattern; git_commit commits only that file")

    def test_commit_excludes_files_outside_output_pattern(self, tmp_path: Path) -> None:
        pytest.skip("STUB: write two files; only the one matching output_pattern is staged")

    def test_commit_unavailable_for_work_type(self, tmp_path: Path) -> None:
        pytest.skip("STUB: work type has no output_pattern → git_commit returns error")

    def test_commit_unavailable_in_discovery_mode(self, tmp_path: Path) -> None:
        pytest.skip("STUB: discovery mode → error")


class TestGitPush:
    """git_push two-sided branch check guards against mismatched branch names."""

    def test_push_rejected_when_arg_differs_from_session_branch(self, tmp_path: Path) -> None:
        pytest.skip('STUB: session_branch="feat/a"; git_push({"branch": "feat/b"}) → error')

    def test_push_rejected_when_head_differs_from_session_branch(self, tmp_path: Path) -> None:
        pytest.skip("STUB: HEAD moved to different branch; push → error")

    def test_pathspec_separator_prevents_injection(self, tmp_path: Path) -> None:
        pytest.skip('STUB (injection): path "--inject" treated as a path, not a flag (git add -- ... separator)')
