"""Parity-net smoke tests for the Python session-start hook.

These tests guarantee Claude-Code-expected stdout/stderr shape and exit
codes regardless of platform. They invoke the hook as a subprocess
with ``sys.executable`` so the parent's interpreter is what runs the
child — same discipline the ported ``pre-pr.py`` uses when spawning
linters.

Companion to ``packages/agentbundle/tests/hooks/test_session_start.sh``,
which exercises the same surfaces against the bash sandbox runner.
The bash runner is the second oracle; this pytest layer is
self-sufficient and the parity net per the windows-hooks-phase3 spec.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
HOOK = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "session-start.py"


def _load_hook_module():
    """Load session-start.py as a module so helpers can be called in-process."""
    spec = importlib.util.spec_from_file_location("session_start", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(env_overrides: dict, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, str(HOOK), *args],
        env=env, capture_output=True, text=True,
    )


def _isolated_env(**overrides: str) -> dict:
    """Build an env dict that points the hook at empty/missing markers
    so the adapt-nudge block stays silent for tests that only care
    about the knowledge block (or vice versa)."""
    base = {
        "KNOWLEDGE_FILE": "/dev/null",
        "ADAPT_REPO_MARKER": "/dev/null",
        "ADAPT_USER_MARKER": "/dev/null",
    }
    base.update(overrides)
    return base


def test_session_start_emits_knowledge_block(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge.jsonl"
    kb.write_text(
        '{"id":"K-0001","kind":"pattern","scope":"*","title":"T","body":"B","source":"S"}\n',
        encoding="utf-8",
    )
    result = _run(_isolated_env(KNOWLEDGE_FILE=str(kb)))
    assert result.returncode == 0, result.stderr
    assert "=== knowledge ===" in result.stdout
    assert "[K-0001]" in result.stdout
    assert "(pattern, *)" in result.stdout
    assert result.stderr == ""


def test_session_start_malformed_warns_to_stderr(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge.jsonl"
    kb.write_text("{not json\n", encoding="utf-8")
    result = _run(_isolated_env(KNOWLEDGE_FILE=str(kb)))
    assert result.returncode == 0
    assert "skipped 1 malformed line(s)" in result.stderr
    assert "run tools/lint-knowledge.py" in result.stderr


def test_session_start_mixed_valid_and_malformed(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge.jsonl"
    kb.write_text(
        "{not json\n"
        '{"id":"K-0001","kind":"pattern","scope":"*","title":"T","body":"B","source":"S"}\n',
        encoding="utf-8",
    )
    result = _run(_isolated_env(KNOWLEDGE_FILE=str(kb)))
    assert result.returncode == 0
    assert "[K-0001]" in result.stdout
    assert "skipped 1 malformed" in result.stderr


def test_session_start_empty_file_silent(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge.jsonl"
    kb.write_text("", encoding="utf-8")
    result = _run(_isolated_env(KNOWLEDGE_FILE=str(kb)))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_session_start_missing_file_silent(tmp_path: Path) -> None:
    result = _run(_isolated_env(KNOWLEDGE_FILE=str(tmp_path / "absent.jsonl")))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_session_start_adapt_nudge_repo_marker(tmp_path: Path) -> None:
    marker = tmp_path / "repo-marker.toml"
    marker.write_text('[[packs-installed]]\nname = "core"\n', encoding="utf-8")
    result = _run(_isolated_env(ADAPT_REPO_MARKER=str(marker)))
    assert result.returncode == 0
    assert "=== adapt-to-project:" in result.stdout
    assert "core" in result.stdout
    assert "1 pack(s) pending" in result.stdout
    assert "1 scope(s)" in result.stdout


def test_session_start_adapt_nudge_both_scopes(tmp_path: Path) -> None:
    repo_marker = tmp_path / "repo.toml"
    repo_marker.write_text(
        '[[packs-installed]]\nname = "core"\n', encoding="utf-8"
    )
    user_marker = tmp_path / "user.toml"
    user_marker.write_text(
        '[[packs-installed]]\nname = "monorepo-extras"\n', encoding="utf-8"
    )
    result = _run(_isolated_env(
        ADAPT_REPO_MARKER=str(repo_marker),
        ADAPT_USER_MARKER=str(user_marker),
    ))
    assert result.returncode == 0
    assert "2 pack(s) pending" in result.stdout
    assert "2 scope(s)" in result.stdout
    assert "core" in result.stdout
    assert "monorepo-extras" in result.stdout


def test_session_start_scope_arg_requires_value() -> None:
    result = _run(_isolated_env(), "--scope")
    assert result.returncode == 2
    assert "--scope requires a path or glob value" in result.stderr


def test_session_start_help_describes_scope_arg() -> None:
    result = _run(_isolated_env(), "--help")
    assert result.returncode == 0
    assert "--scope" in result.stdout


def test_session_start_scope_coverage_glob(tmp_path: Path) -> None:
    kb = tmp_path / "kb.jsonl"
    kb.write_text(
        '{"id":"K-0001","kind":"pattern","scope":"packages/auth/**","title":"T1","body":"B1","source":"S1"}\n'
        '{"id":"K-0002","kind":"gotcha","scope":"src/other/x.ts","title":"T2","body":"B2","source":"S2"}\n',
        encoding="utf-8",
    )
    result = _run(
        _isolated_env(KNOWLEDGE_FILE=str(kb)),
        "--scope", "packages/auth/server.ts",
    )
    assert result.returncode == 0
    assert "K-0001" in result.stdout
    assert "K-0002" not in result.stdout


def test_session_start_unknown_arg() -> None:
    result = _run(_isolated_env(), "--frobnicate")
    assert result.returncode == 2
    assert "unknown argument" in result.stderr


# ---------------------------------------------------------------------------
# AC12 / AC14: v0.4 marker reader tolerance via _pack_names_from_marker
# ---------------------------------------------------------------------------


def test_v04_marker_omits_unresolved_markers_and_new_companions(
    tmp_path: Path,
) -> None:
    """AC12 + AC14: a v0.4-shape marker carrying only name/version/installed-at
    /install-route (no unresolved-markers, no new-companions) must (a) parse
    cleanly through tomllib and (b) yield the pack name from
    _pack_names_from_marker unchanged.

    This pins that the v0.4 field relaxation does not break the existing core
    session-start nudge reader."""
    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "core"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-24T10:00:00Z\n"
        'install-route = "claude-plugins"\n',
        encoding="utf-8",
    )

    import tomllib

    # (a) parses cleanly; no unresolved-markers / new-companions keys present
    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))
    entry = parsed["packs-installed"][0]
    assert "unresolved-markers" not in entry
    assert "new-companions" not in entry
    assert entry["install-route"] == "claude-plugins"

    # (b) _pack_names_from_marker returns the pack name correctly
    mod = _load_hook_module()
    names = mod._pack_names_from_marker(marker)
    assert names == ["core"]


def test_v03_marker_still_parses_under_v04_reader(tmp_path: Path) -> None:
    """AC12: a v0.3-shape marker (unresolved-markers and new-companions present,
    no install-route) must be read correctly by the v0.4-era
    _pack_names_from_marker helper — backward-compat with pre-PR markers.

    The read-side rule is 'treat absence as install-route = cli'; this test
    pins that the reader is not destabilised by the missing optional field."""
    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "core"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-24T10:00:00Z\n"
        "unresolved-markers = []\n"
        "new-companions = []\n",
        encoding="utf-8",
    )

    mod = _load_hook_module()
    names = mod._pack_names_from_marker(marker)
    assert names == ["core"]
