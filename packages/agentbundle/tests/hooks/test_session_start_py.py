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


def test_session_start_nudge_byte_identical_v03_vs_v04(tmp_path: Path) -> None:
    """Blocker 1 / AC14: the rendered nudge stdout is byte-identical
    when the session-start hook reads a v0.3-shaped marker versus a
    v0.4-shaped marker with the same pack names.

    v0.3 shape: unresolved-markers and new-companions present, no install-route.
    v0.4 shape: install-route = "claude-plugins" added; the two arrays absent.

    The hook is route-agnostic by design; this test pins that property
    so a future SKILL.md / hook edit cannot introduce route-keyed output.
    """
    v03_marker = tmp_path / "v03.toml"
    v03_marker.write_text(
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

    v04_marker = tmp_path / "v04.toml"
    v04_marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "core"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-25T12:34:56Z\n"
        'install-route = "claude-plugins"\n',
        encoding="utf-8",
    )

    result_v03 = _run(_isolated_env(ADAPT_REPO_MARKER=str(v03_marker)))
    result_v04 = _run(_isolated_env(ADAPT_REPO_MARKER=str(v04_marker)))

    assert result_v03.returncode == 0, result_v03.stderr
    assert result_v04.returncode == 0, result_v04.stderr

    assert result_v03.stdout == result_v04.stdout, (
        f"Rendered nudge stdout differs between v0.3 and v0.4 markers:\n"
        f"v0.3: {result_v03.stdout!r}\n"
        f"v0.4: {result_v04.stdout!r}"
    )


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


# ---------------------------------------------------------------------------
# T3 / AC10: v0.5 marker reader tolerance for install-route = "apm"
# Spec: docs/specs/apm-install-route-parity/spec.md
# ---------------------------------------------------------------------------


def test_v05_marker_with_install_route_apm_parses_cleanly(tmp_path: Path) -> None:
    """AC10: a v0.5-shape marker carrying install-route = "apm" must (a)
    parse cleanly through tomllib and (b) yield the pack name from
    _pack_names_from_marker unchanged."""
    import tomllib

    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "core"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-25T12:34:56Z\n"
        'install-route = "apm"\n',
        encoding="utf-8",
    )

    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))
    entry = parsed["packs-installed"][0]
    assert entry["install-route"] == "apm"

    mod = _load_hook_module()
    names = mod._pack_names_from_marker(marker)
    assert names == ["core"]


def test_v05_marker_three_route_values_all_parse(tmp_path: Path) -> None:
    """AC10: three entries — install-route = "cli", "claude-plugins", "apm" —
    in one marker file all parse and all surface through
    _pack_names_from_marker. Closes the value-coverage axis."""
    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "cli-pack"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-25T12:00:00Z\n"
        'install-route = "cli"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "cp-pack"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-25T12:01:00Z\n"
        'install-route = "claude-plugins"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "apm-pack"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-25T12:02:00Z\n"
        'install-route = "apm"\n',
        encoding="utf-8",
    )

    mod = _load_hook_module()
    names = mod._pack_names_from_marker(marker)
    assert sorted(names) == ["apm-pack", "cli-pack", "cp-pack"]


def test_v03_shaped_marker_without_install_route_field_parses_as_cli(
    tmp_path: Path,
) -> None:
    """AC10 (v0.3 back-compat rail): a marker with no install-route field at
    all must parse cleanly, surface the pack name, and any reader that
    consults install-route treats absence as "cli" per
    claude-plugins-install-route AC12."""
    import tomllib

    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "legacy-pack"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-23T10:00:00Z\n",
        encoding="utf-8",
    )

    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))
    entry = parsed["packs-installed"][0]
    assert "install-route" not in entry
    assert entry.get("install-route", "cli") == "cli"

    mod = _load_hook_module()
    names = mod._pack_names_from_marker(marker)
    assert names == ["legacy-pack"]
