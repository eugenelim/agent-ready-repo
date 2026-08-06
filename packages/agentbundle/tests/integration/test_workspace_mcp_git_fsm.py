"""Integration tests for _GitTools FSM-mode guard — AC15a.

These tests create git repositories on disk and invoke subprocess git,
so they belong in tests/integration/ per packages/AGENTS.md:50-51.
"""
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
    (tmp_path / "README.md").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], check=True, capture_output=True, cwd=str(tmp_path))
    subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True, cwd=str(tmp_path))
    return tmp_path


class TestFsmModeGuard:
    """FSM mode (any supplied WORKSPACE_MCP_SPEC_PATH) blocks all mutating git tools.

    Sub-cases:
    - SPEC_PATH only (canonical FSM session)
    - SPEC_PATH + DISPATCHED_ITEM both set (unsupported; SPEC_PATH wins)
    - SPEC_PATH="" (empty string counts as supplied — fail-closed)
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

    # --- SPEC_PATH only (canonical FSM session) ---

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
        """git_push returns FSM-mode error even when branch matches startup HEAD (regression)."""
        repo = _init_git_repo(tmp_path)
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True, capture_output=True, text=True, cwd=str(repo),
        ).stdout.strip()
        tools = self._make_tools(repo, {"WORKSPACE_MCP_SPEC_PATH": self._spec_path(repo)}, monkeypatch)
        result = tools.git_push({"branch": branch})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    # --- Empty SPEC_PATH sub-case: "" counts as supplied -----------

    def test_git_branch_blocked_when_spec_path_empty_string(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_branch blocked when SPEC_PATH='' (empty string) — in os.environ counts."""
        repo = _init_git_repo(tmp_path)
        tools = self._make_tools(repo, {"WORKSPACE_MCP_SPEC_PATH": ""}, monkeypatch)
        result = tools.git_branch({"name": "feat/my-thing"})
        assert "error" in result
        assert "FSM" in result["error"] or "work-loop" in result["error"]

    # --- Both-vars sub-case: SPEC_PATH wins even when DISPATCHED_ITEM is also set -----------

    def test_git_branch_blocked_when_both_vars_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git_branch blocked when both env vars set — FSM mode wins."""
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
        """git_commit blocked when both env vars set — FSM mode wins."""
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
        """git_push blocked when both env vars set — FSM mode wins."""
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
