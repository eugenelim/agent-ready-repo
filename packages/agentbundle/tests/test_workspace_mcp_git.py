"""Tests for _GitTools — branch validation, commit path intersection, injection defence."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from agentbundle.workspace_mcp import _GitTools


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


class TestFsmModeGuard:
    """FSM mode (any valid SPEC_PATH) must block all mutating git tools (AC15a).

    Covers two sub-cases:
    - SPEC_PATH only (canonical FSM session)
    - SPEC_PATH + DISPATCHED_ITEM both set (unsupported; SPEC_PATH wins)
    """

    def _make_tools(
        self, tmp_path: Path, env: dict, monkeypatch: pytest.MonkeyPatch
    ) -> _GitTools:
        """Construct _GitTools with only the given env vars for workspace-mcp keys."""
        monkeypatch.delenv("WORKSPACE_MCP_SPEC_PATH", raising=False)
        monkeypatch.delenv("WORKSPACE_MCP_DISPATCHED_ITEM", raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return _GitTools(tmp_path)

    def _spec_path(self, repo: Path) -> str:
        """Create a spec directory inside the repo and return its absolute path string."""
        spec_dir = repo / "docs" / "specs" / "my-feature"
        spec_dir.mkdir(parents=True, exist_ok=True)
        return str(spec_dir)

    def test_git_branch_blocked_in_fsm_mode_named_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_branch returns FSM-mode error on a named branch (not a subprocess call)."""
        repo = _init_git_repo(tmp_path)
        tools = self._make_tools(repo, {"WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo)}, monkeypatch)
        result = tools.git_branch({"name": "feat/my-thing"})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    def test_git_commit_blocked_in_fsm_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_commit returns FSM-mode error regardless of output_pattern logic."""
        repo = _init_git_repo(tmp_path)
        tools = self._make_tools(repo, {"WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo)}, monkeypatch)
        result = tools.git_commit({"message": "test commit"})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    def test_git_push_blocked_in_fsm_mode_named_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_push returns FSM-mode error even when branch matches startup HEAD (AC14 regression)."""
        repo = _init_git_repo(tmp_path)
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True, capture_output=True, text=True, cwd=str(repo),
        ).stdout.strip()
        tools = self._make_tools(repo, {"WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo)}, monkeypatch)
        result = tools.git_push({"branch": branch})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    # --- Both-vars sub-case (AC15a): SPEC_PATH wins even when DISPATCHED_ITEM is also set ---

    def test_git_branch_blocked_when_both_vars_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_branch blocked when both env vars set — FSM mode wins (AC15a)."""
        repo = _init_git_repo(tmp_path)
        tools = self._make_tools(
            repo,
            {
                "WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo),
                "WORKSPACE_MCP_DISPATCHED_ITEM": "my-ini/shape:my-shape",
            },
            monkeypatch,
        )
        result = tools.git_branch({"name": "feat/my-thing"})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    def test_git_commit_blocked_when_both_vars_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_commit blocked when both env vars set — FSM mode wins (AC15a)."""
        repo = _init_git_repo(tmp_path)
        tools = self._make_tools(
            repo,
            {
                "WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo),
                "WORKSPACE_MCP_DISPATCHED_ITEM": "my-ini/shape:my-shape",
            },
            monkeypatch,
        )
        result = tools.git_commit({"message": "test"})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    def test_git_push_blocked_when_both_vars_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_push blocked when both env vars set — FSM mode wins (AC15a)."""
        repo = _init_git_repo(tmp_path)
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True, capture_output=True, text=True, cwd=str(repo),
        ).stdout.strip()
        tools = self._make_tools(
            repo,
            {
                "WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo),
                "WORKSPACE_MCP_DISPATCHED_ITEM": "my-ini/shape:my-shape",
            },
            monkeypatch,
        )
        result = tools.git_push({"branch": branch})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]
