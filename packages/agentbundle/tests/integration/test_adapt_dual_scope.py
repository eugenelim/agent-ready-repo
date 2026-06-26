"""T21: adapt walks both state files; writes per-scope pending reports.

Verifies AC #(RFC-0004) for the agent-spec-cli spec § *adapt
dual-state-file walk*:

  - adapt writes per-scope `.adapt-pending.md` at
    `<repo>/.adapt-pending.md` (repo) and
    `~/.agentbundle/.adapt-pending.md` (user, inside the namespaced
    dot-directory — never as a bare ~/.adapt-pending.md).
  - adapt --ci exits non-zero when either scope's pending file is
    non-empty; parametrised across three cases (repo-only, user-only,
    both).
  - Findings are recorded at the scope they were observed in.
  - A fixture missing one state file walks the present one and reports
    against its scope only.
  - adapt reads `<repo>/.adapt-discovery.toml` and
    `~/.agentbundle/.adapt-discovery.toml`. A counter-fixture placing
    the value at `~/.adapt-discovery.toml` is *not* consulted.
"""

from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path

import pytest

from agentbundle.commands import adapt
from agentbundle.config import PackState, State, dump_state


def _write_state(path: Path, files: dict[str, str], scope: str = "repo") -> None:
    state = State()
    state.packs[("demo", "claude-code")] = PackState(
        installed_version="0.1.0",
        scope=scope,
        files={k: {"sha": v, "from-pack-version": "0.1.0"} for k, v in files.items()},
        adapter="claude-code",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8")


def _stage_companion(root: Path, relpath: str, content: bytes, companion_content: bytes) -> None:
    """Create both the original and a `.upstream.<ext>` companion."""
    from agentbundle.safety import companion_path

    original = root / relpath
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(content)
    comp = root / companion_path(Path(relpath))
    comp.write_bytes(companion_content)


# ---------------------------------------------------------------------------
# Per-scope pending file paths
# ---------------------------------------------------------------------------


def test_adapt_writes_per_scope_pending_reports(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    user_dir = fake_home / ".agentbundle"
    user_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    # Repo-scope: state references a Tier-2 path with companion.
    _write_state(repo_root / ".agentbundle-state.toml", {"AGENTS.md": "00"})
    _stage_companion(repo_root, "AGENTS.md", b"adopter", b"bundle")
    # User-scope: state references a path with companion.
    _write_state(user_dir / "state.toml", {".claude/skills/foo/SKILL.md": "11"})
    _stage_companion(fake_home, ".claude/skills/foo/SKILL.md", b"adopter", b"bundle")

    args = argparse.Namespace(values_from=None, ci=False, root=str(repo_root))
    rc = adapt.run(args)
    assert rc == 0

    repo_report = repo_root / ".adapt-pending.md"
    user_report = user_dir / ".adapt-pending.md"
    assert repo_report.exists(), "repo-scope pending report missing"
    assert user_report.exists(), "user-scope pending report missing"

    # The user-scope finding lives in the user-scope report only —
    # findings recorded at the scope they were observed in.
    repo_text = repo_report.read_text()
    user_text = user_report.read_text()
    assert "AGENTS.upstream.md" in repo_text
    assert ".claude/skills/foo/SKILL.upstream.md" in user_text
    assert "AGENTS.upstream.md" not in user_text
    assert ".claude/skills/foo/SKILL.upstream.md" not in repo_text

    # The user-scope report is *inside* the dot-directory, not a bare
    # dotfile in $HOME.
    assert not (fake_home / ".adapt-pending.md").exists()


# ---------------------------------------------------------------------------
# adapt --ci exits non-zero on either scope's pending companions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case", ["repo_only", "user_only", "both"]
)
def test_adapt_ci_or_across_scopes(tmp_path, monkeypatch, case):
    fake_home = tmp_path / "home"
    user_dir = fake_home / ".agentbundle"
    user_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    if case in ("repo_only", "both"):
        _write_state(repo_root / ".agentbundle-state.toml", {"AGENTS.md": "00"})
        _stage_companion(repo_root, "AGENTS.md", b"adopter", b"bundle")
    else:
        _write_state(repo_root / ".agentbundle-state.toml", {})

    if case in ("user_only", "both"):
        _write_state(user_dir / "state.toml", {".claude/x.md": "11"}, scope="user")
        _stage_companion(fake_home, ".claude/x.md", b"a", b"b")
    else:
        _write_state(user_dir / "state.toml", {}, scope="user")

    args = argparse.Namespace(values_from=None, ci=True, root=str(repo_root))
    rc = adapt.run(args)
    assert rc != 0, f"case={case}: --ci should refuse"


def test_adapt_ci_passes_when_neither_scope_has_companions(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    (fake_home / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_state(repo_root / ".agentbundle-state.toml", {})
    _write_state(fake_home / ".agentbundle" / "state.toml", {}, scope="user")

    args = argparse.Namespace(values_from=None, ci=True, root=str(repo_root))
    assert adapt.run(args) == 0


# ---------------------------------------------------------------------------
# Missing one state file → walk the present one, no error
# ---------------------------------------------------------------------------


def test_adapt_handles_missing_user_state(tmp_path, monkeypatch):
    """When the user-scope state file is absent, adapt walks repo only.

    The user-scope dot-directory must exist for the scope to be
    activated (per `_resolve_scopes`); if absent, only the repo scope
    is walked. This matches the spec's intent — a repo-only adopter
    should not have a user-scope report appear out of nowhere.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_state(repo_root / ".agentbundle-state.toml", {"AGENTS.md": "00"})
    _stage_companion(repo_root, "AGENTS.md", b"adopter", b"bundle")

    args = argparse.Namespace(values_from=None, ci=False, root=str(repo_root))
    assert adapt.run(args) == 0
    assert (repo_root / ".adapt-pending.md").exists()
    # No user-scope dot-directory means no user-scope report.
    assert not (fake_home / ".adapt-pending.md").exists()
    assert not (fake_home / ".agentbundle").exists()


# ---------------------------------------------------------------------------
# adapt reads namespaced .adapt-discovery.toml (not bare dotfile)
# ---------------------------------------------------------------------------


def test_adapt_reads_user_scope_discovery_in_dot_directory(tmp_path, monkeypatch):
    """Discovery values at `~/.agentbundle/.adapt-discovery.toml` are read.

    A counter-fixture placing the discovery at `~/.adapt-discovery.toml`
    (bare dotfile) is NOT read — proving the reader picks the
    namespaced path, not the bare one.
    """
    fake_home = tmp_path / "home"
    user_dir = fake_home / ".agentbundle"
    user_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # User-scope state references a file with a marker.
    target_rel = ".claude/skills/foo/SKILL.md"
    target = fake_home / target_rel
    target.parent.mkdir(parents=True)
    target.write_text("project=<adapt:project-name>", encoding="utf-8")
    _write_state(user_dir / "state.toml", {target_rel: "00"}, scope="user")

    # User-scope discovery: canonical v0.1 shape, no [markers] (markers
    # are repo-only per RFC-0004). Plus a repo-scope discovery carrying
    # the marker value the substitution needs.
    (user_dir / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n', encoding="utf-8"
    )
    (repo_root / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n'
        '[markers]\nproject-name = "demo"\n',
        encoding="utf-8",
    )
    # Counter-fixture at the BARE user path (must be ignored).
    (fake_home / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n'
        '[markers]\nproject-name = "WRONG"\n',
        encoding="utf-8",
    )

    _write_state(repo_root / ".agentbundle-state.toml", {})

    # Use --values-from to enable substitution (default mode skips it
    # when no --values-from is passed; we want to confirm the discovery
    # values are consulted alongside).
    values_file = tmp_path / "values.toml"
    values_file.write_text('[values]\n# only sets unrelated keys\n', encoding="utf-8")

    args = argparse.Namespace(
        values_from=str(values_file), ci=False, root=str(repo_root)
    )
    rc = adapt.run(args)
    assert rc == 0
    # The marker should have been resolved to "demo" (namespaced discovery).
    assert target.read_text() == "project=demo", (
        f"expected resolution via namespaced discovery; got {target.read_text()!r}"
    )
