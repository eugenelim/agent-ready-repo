"""Tests for the ``list-installed`` subcommand (install-state-visibility spec).

Covers the pure helpers (status computation, drift count, row collection) by
TDD, and the command end-to-end via in-process ``run(args)`` over state files
written to a tmp repo root and a tmp user home (the conftest HOME sandbox).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from agentbundle.commands import list_installed as li
from agentbundle.commands._common import count_drifted_files
from agentbundle.config import PackState, State, dump_state

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent  # packages/agentbundle


# ---------------------------------------------------------------------------
# Pure helpers — _status_for (AC3, AC4)
# ---------------------------------------------------------------------------


def test_status_up_to_date():
    assert li._status_for("0.9.0", "0.9.0", catalogue_resolved=True) == "up-to-date"


def test_status_upgrade_available():
    assert (
        li._status_for("0.9.0", "0.10.0", catalogue_resolved=True)
        == "upgrade-available"
    )


def test_status_installed_ahead_is_up_to_date():
    # Local install ahead of the catalogue → nothing to upgrade to.
    assert li._status_for("0.10.0", "0.9.0", catalogue_resolved=True) == "up-to-date"


def test_status_unknown_when_catalogue_unresolved():
    assert li._status_for("0.9.0", None, catalogue_resolved=False) == "unknown"


def test_status_unknown_when_latest_missing():
    assert li._status_for("0.9.0", None, catalogue_resolved=True) == "unknown"


def test_status_unknown_when_unparseable():
    assert li._status_for("0.9.0", "main", catalogue_resolved=True) == "unknown"


# ---------------------------------------------------------------------------
# Pure helper — _drift_count (AC6)
# ---------------------------------------------------------------------------


def _write(root: Path, relpath: str, content: bytes) -> str:
    from agentbundle.safety import sha256_bytes

    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return sha256_bytes(content)


def test_drift_count_clean(tmp_path):
    sha = _write(tmp_path, "a/x.md", b"hello\n")
    ps = PackState(installed_version="1.0", files={"a/x.md": {"sha": sha}})
    assert count_drifted_files(ps, tmp_path) == 0


def test_drift_count_edited(tmp_path):
    sha = _write(tmp_path, "a/x.md", b"hello\n")
    # Now edit on disk away from the recorded sha.
    (tmp_path / "a/x.md").write_bytes(b"edited\n")
    ps = PackState(installed_version="1.0", files={"a/x.md": {"sha": sha}})
    assert count_drifted_files(ps, tmp_path) == 1


def test_drift_count_absent_is_not_drift(tmp_path):
    ps = PackState(installed_version="1.0", files={"a/x.md": {"sha": "deadbeef"}})
    assert count_drifted_files(ps, tmp_path) == 0


# ---------------------------------------------------------------------------
# Pure helper — _collect_rows ordering (AC1)
# ---------------------------------------------------------------------------


def test_collect_rows_sorted_across_scopes(tmp_path):
    repo = State(
        packs={
            ("core", "claude-code"): PackState(installed_version="0.5.0"),
            ("architect", "codex"): PackState(installed_version="0.9.0"),
        }
    )
    user = State(
        packs={("architect", "claude-code"): PackState(installed_version="0.9.0")}
    )
    rows = li._collect_rows([("repo", tmp_path, repo), ("user", tmp_path, user)])
    assert [(r["pack"], r["adapter"], r["scope"]) for r in rows] == [
        ("architect", "claude-code", "user"),
        ("architect", "codex", "repo"),
        ("core", "claude-code", "repo"),
    ]


# ---------------------------------------------------------------------------
# Command — fixtures and helpers
# ---------------------------------------------------------------------------


def _make_args(**kw) -> SimpleNamespace:
    base = dict(
        catalogue=None, root=".", scope=None, no_check=False, check_drift=False,
        _user_config=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _write_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8")


def _write_catalogue(root: Path, versions: dict[str, str]) -> Path:
    """Build a minimal catalogue at root/packs/<name>/pack.toml."""
    for name, version in versions.items():
        pd = root / "packs" / name
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "{version}"\n', encoding="utf-8"
        )
    return root


# ---------------------------------------------------------------------------
# Command — behavior (AC1, AC2, AC4, AC5, AC6, AC7)
# ---------------------------------------------------------------------------


def test_empty_state_prints_friendly_line(tmp_path, capsys):
    args = _make_args(root=str(tmp_path), no_check=True)
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no packs installed" in out


def test_lists_repo_rows_with_columns(tmp_path, capsys):
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={("architect", "codex"): PackState(installed_version="0.9.0")}),
    )
    cat = _write_catalogue(tmp_path / "cat", {"architect": "0.10.0"})
    args = _make_args(root=str(tmp_path), scope="repo", catalogue=str(cat))
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    for col in ("PACK", "ADAPTER", "SCOPE", "INSTALLED", "LATEST", "STATUS"):
        assert col in out
    assert "architect" in out and "codex" in out and "0.9.0" in out
    assert "0.10.0" in out and "upgrade-available" in out


def test_no_check_drops_latest_status(tmp_path, capsys):
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={("architect", "codex"): PackState(installed_version="0.9.0")}),
    )
    args = _make_args(root=str(tmp_path), scope="repo", no_check=True)
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "INSTALLED" in out
    assert "LATEST" not in out and "STATUS" not in out


def test_unresolvable_catalogue_degrades_to_unknown(tmp_path, capsys):
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={("architect", "codex"): PackState(installed_version="0.9.0")}),
    )
    # Point at a catalogue path that does not exist → CatalogueError → unknown.
    args = _make_args(
        root=str(tmp_path), scope="repo", catalogue=str(tmp_path / "nope")
    )
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "unknown" in out
    assert "—" in out  # LATEST sentinel


def test_resolved_catalogue_missing_pack_is_unknown(tmp_path, capsys):
    # Catalogue resolves but does not contain the installed pack → unknown
    # (AC3's "that pack's catalogue entry can't be resolved" case).
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={("architect", "codex"): PackState(installed_version="0.9.0")}),
    )
    cat = _write_catalogue(tmp_path / "cat", {"some-other-pack": "1.0.0"})
    args = _make_args(root=str(tmp_path), scope="repo", catalogue=str(cat))
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "architect" in out and "unknown" in out


def test_legacy_state_in_one_scope_is_skipped_not_fatal(tmp_path, capsys):
    # An incompatible (legacy-schema) repo state file is warned-and-skipped,
    # not a hard abort — list-installed still exits 0.
    (tmp_path / ".agentbundle-state.toml").write_text(
        'schema-version = "0.1"\n', encoding="utf-8"
    )
    args = _make_args(root=str(tmp_path), scope="repo", no_check=True)
    rc = li.run(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "skipping repo scope" in captured.err


def test_check_drift_column(tmp_path, capsys):
    sha = _write(tmp_path, ".claude/skills/x/SKILL.md", b"orig\n")
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(
            packs={
                ("architect", "codex"): PackState(
                    installed_version="0.9.0",
                    files={".claude/skills/x/SKILL.md": {"sha": sha}},
                )
            }
        ),
    )
    # Edit the file so it drifts.
    (tmp_path / ".claude/skills/x/SKILL.md").write_bytes(b"edited\n")
    args = _make_args(
        root=str(tmp_path), scope="repo", no_check=True, check_drift=True
    )
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRIFT" in out
    # The drift count of 1 should appear on the row.
    assert "1" in out


def test_scope_filter_excludes_other_scope(tmp_path, capsys):
    # Repo has a row; restrict to user scope → should not list the repo row.
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={("core", "claude-code"): PackState(installed_version="0.5.0")}),
    )
    args = _make_args(root=str(tmp_path), scope="user", no_check=True)
    rc = li.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "core" not in out
    assert "no packs installed at user scope" in out


# ---------------------------------------------------------------------------
# CLI wiring — real subprocess invocation (AC13)
# ---------------------------------------------------------------------------


def test_cli_help_registers_command():
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "list-installed", "--help"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout + proc.stderr
    for flag in ("--scope", "--no-check", "--check-drift"):
        assert flag in out


def test_cli_no_check_runs_against_empty_repo(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "list-installed",
         "--scope", "repo", "--no-check", "--root", str(tmp_path)],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "no packs installed at repo scope" in (proc.stdout + proc.stderr)


def test_cli_populated_table_and_check_drift_via_subprocess(tmp_path):
    """End-to-end through argparse (not in-process run()): a populated repo
    state lists its row, and --check-drift counts an edited file. Closes the
    gap the in-process tests leave (they bypass --check-drift/--scope wiring)."""
    from agentbundle.safety import sha256_bytes

    # A clean install: file on disk matches the recorded SHA.
    rel = ".claude/skills/x/SKILL.md"
    (tmp_path / ".claude/skills/x").mkdir(parents=True)
    (tmp_path / rel).write_text("orig\n", encoding="utf-8")
    sha = sha256_bytes(b"orig\n")
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(
            packs={
                ("architect", "codex"): PackState(
                    installed_version="0.9.0", files={rel: {"sha": sha}}
                )
            }
        ),
    )
    # Edit the file so it drifts.
    (tmp_path / rel).write_text("edited\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "list-installed",
         "--scope", "repo", "--no-check", "--check-drift", "--root", str(tmp_path)],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    for col in ("PACK", "ADAPTER", "SCOPE", "INSTALLED", "DRIFT"):
        assert col in out
    assert "architect" in out and "codex" in out and "0.9.0" in out
    # The architect row's DRIFT cell is the count 1 (one edited file).
    row = [ln for ln in out.splitlines() if ln.startswith("architect")][0]
    assert row.split()[-1] == "1", row
