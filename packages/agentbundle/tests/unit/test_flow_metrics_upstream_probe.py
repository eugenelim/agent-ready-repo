"""Regression test for the flow-metrics upstream-skill probe across the
three user-scope-capable adapter directories.

Pinned by RFC-0011 (Per-pack `allowed-adapters` declaration). Before this
RFC's branch, `discover_skill_path` hardcoded `~/.claude/skills/` as the
sole user-scope and project-scope candidate. The fix walks `.claude`,
`.kiro`, and `.agents` for both user and project scope so the atlassian
pack works under all three user-scope-capable adapters.

This test pins:
- claude / kiro / codex user-scope each resolve when the sibling-walk
  (priority 2) misses;
- project scope under any of the three adapters works the same way;
- the priority-1 env-var override remains the runtime escape valve
  documented in `discover_skill_path`'s docstring.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Locate the flow-metrics module under the catalogue's pack tree.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_FLOW_METRICS_SCRIPTS = (
    _REPO_ROOT
    / "packs"
    / "atlassian"
    / ".apm"
    / "skills"
    / "flow-metrics"
    / "scripts"
)


@pytest.fixture
def upstream(monkeypatch):
    """Import `flow_metrics.upstream` with its scripts dir on `sys.path`,
    then repoint `_THIS_SKILL_DIR` at a scratch directory so the
    priority-2 sibling walk reliably misses — isolating the
    priority-3/-4 user/project candidates this test exercises."""
    sys.path.insert(0, str(_FLOW_METRICS_SCRIPTS))
    try:
        import flow_metrics.upstream as up
    finally:
        sys.path.pop(0)

    with tempfile.TemporaryDirectory() as scratch:
        scratch_path = Path(scratch) / "flow-metrics-installed"
        scratch_path.mkdir()
        monkeypatch.setattr(up, "_THIS_SKILL_DIR", scratch_path)
        yield up


@pytest.mark.parametrize("adapter_dir", [".claude", ".kiro", ".agents"])
def test_user_scope_probe_across_three_adapters(upstream, adapter_dir, monkeypatch):
    """priority-3 user-scope walk resolves under each of the three
    user-scope-capable adapter directories."""
    with tempfile.TemporaryDirectory() as home:
        home_path = Path(home)
        script = home_path / adapter_dir / "skills" / "jira" / "scripts" / "jira.py"
        script.parent.mkdir(parents=True)
        script.write_text("# stub\n")

        monkeypatch.setenv("HOME", str(home_path))
        monkeypatch.delenv("FLOW_METRICS_JIRA_SCRIPT", raising=False)

        found = upstream.discover_skill_path("jira", cwd=Path("/nonexistent-cwd"))
        assert found == script, f"adapter={adapter_dir}: got {found}"


@pytest.mark.parametrize("adapter_dir", [".claude", ".kiro", ".agents"])
def test_project_scope_probe_across_three_adapters(upstream, adapter_dir, monkeypatch):
    """priority-4 project-scope walk resolves under each of the three
    adapter directories rooted at `cwd`."""
    with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as home:
        proj_path = Path(proj)
        script = proj_path / adapter_dir / "skills" / "jira" / "scripts" / "jira.py"
        script.parent.mkdir(parents=True)
        script.write_text("# stub\n")

        # Empty HOME so user-scope candidates don't accidentally match.
        monkeypatch.setenv("HOME", str(Path(home)))
        monkeypatch.delenv("FLOW_METRICS_JIRA_SCRIPT", raising=False)

        found = upstream.discover_skill_path("jira", cwd=proj_path)
        assert found == script, f"adapter={adapter_dir}: got {found}"


def test_env_override_wins_over_user_scope(upstream, monkeypatch):
    """The priority-1 env override remains the documented runtime escape
    valve for adopters who want a specific adapter root regardless of
    probe order (mirrors the install-time `--adapter` flag admitted in
    RFC-0011 as the user-scope adopter's escape valve)."""
    with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as override:
        home_path = Path(home)
        # Place a sibling under ~/.claude/ that would win priority 3
        # were the env override absent.
        decoy = home_path / ".claude" / "skills" / "jira" / "scripts" / "jira.py"
        decoy.parent.mkdir(parents=True)
        decoy.write_text("# decoy\n")

        # The override target.
        override_path = Path(override) / "jira.py"
        override_path.write_text("# override\n")

        monkeypatch.setenv("HOME", str(home_path))
        monkeypatch.setenv("FLOW_METRICS_JIRA_SCRIPT", str(override_path))

        found = upstream.discover_skill_path("jira", cwd=Path("/nonexistent-cwd"))
        assert found == override_path, f"override should win; got {found}"


def test_all_candidates_miss_raises_with_seven_paths(upstream, monkeypatch):
    """When no candidate resolves, the error names every probed path
    (1 sibling + 3 user + 3 project = 7 paths when no env override is
    set). Regression check on the candidate-list length so future
    edits to `_USER_SCOPE_CAPABLE_ADAPTER_DIRS` are caught."""
    with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as proj:
        monkeypatch.setenv("HOME", str(Path(home)))
        monkeypatch.delenv("FLOW_METRICS_JIRA_SCRIPT", raising=False)

        with pytest.raises(upstream.UpstreamNotFoundError) as excinfo:
            upstream.discover_skill_path("jira", cwd=Path(proj))

        # The error message names every candidate path.
        msg = str(excinfo.value)
        # 3 user + 3 project = 6 adapter-rooted candidates plus 1 sibling.
        for adapter_dir in (".claude", ".kiro", ".agents"):
            assert f"{adapter_dir}/skills/jira" in msg, (
                f"missing candidate for {adapter_dir} in error: {msg}"
            )
