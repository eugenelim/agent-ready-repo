"""Integration tests for the canonical install-marker writer template (T1).

Spec: docs/specs/claude-plugins-install-route/spec.md

Each test runs ``packages/agentbundle/templates/install-marker.py`` in a
subprocess against a fixture-controlled environment quartet:
  - ``${CLAUDE_PLUGIN_ROOT}``  — pack root with pack.toml + enabledPlugins seeding
  - ``${CLAUDE_PLUGIN_DATA}``  — per-session data directory (hash file lives here)
  - ``${HOME}``                — user home directory
  - ``${CLAUDE_PROJECT_DIR}``  — project directory (may be unset in some tests)

AC4 (atomic-rename crash recovery) and AC5 (no-hash-when-marker-fails) use a
``sitecustomize.py`` wrapper in PYTHONPATH that monkeypatches ``os.replace``.

AC7's CLI-handoff sub-assertion seeds via ``_append_install_marker`` in-process.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import textwrap
import tomllib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Path to the writer script (repo-relative)
# ---------------------------------------------------------------------------

WRITER = Path(__file__).resolve().parents[2] / "templates" / "install-marker.py"

assert WRITER.exists(), f"Writer not found at {WRITER}"


# ---------------------------------------------------------------------------
# Helper: run the writer in subprocess
# ---------------------------------------------------------------------------


def _run_writer(env: dict) -> "subprocess.CompletedProcess":
    import subprocess
    return subprocess.run(
        [sys.executable, str(WRITER)],
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )


# ---------------------------------------------------------------------------
# Fixture: pack_root_factory
# Builds a minimal pack root with pack.toml + enabledPlugins settings files.
# ---------------------------------------------------------------------------


@pytest.fixture
def pack_root_factory(tmp_path):
    """Factory that builds a minimal pack root directory.

    Usage::

        pack_root, plugin_data, home, project_dir = pack_root_factory(
            name="core",
            version="0.1.0",
            allowed_scopes=["repo"],
        )

    Returns a 4-tuple ``(plugin_root, plugin_data, home, project_dir)``.
    All paths live under ``tmp_path``; settings.json files are populated
    according to the ``opt_in_at`` argument.
    """

    def factory(
        *,
        name: str = "core",
        version: str = "0.1.0",
        allowed_scopes: list | None = None,
        opt_in_at: list | None = None,
    ):
        if allowed_scopes is None:
            allowed_scopes = ["repo"]
        if opt_in_at is None:
            opt_in_at = ["local"]

        # Unique sub-directories per call so multiple factories in one test
        # don't collide.
        idx = factory._counter
        factory._counter += 1

        plugin_root = tmp_path / f"plugin_root_{idx}"
        plugin_root.mkdir()
        plugin_data = tmp_path / f"plugin_data_{idx}"
        plugin_data.mkdir()
        home = tmp_path / f"home_{idx}"
        home.mkdir()
        project_dir = tmp_path / f"project_{idx}"
        project_dir.mkdir()

        # Write pack.toml
        pack_toml_content = textwrap.dedent(f"""
            [pack]
            name = {json.dumps(name)}
            version = {json.dumps(version)}
            description = "Test pack."

            [pack.install]
            default-scope = {json.dumps(allowed_scopes[0])}
            allowed-scopes = {json.dumps(allowed_scopes)}
        """).lstrip()
        (plugin_root / "pack.toml").write_text(pack_toml_content, encoding="utf-8")

        # Write settings files based on opt_in_at
        for scope in opt_in_at:
            if scope == "local":
                settings_dir = project_dir / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                settings_file = settings_dir / "settings.local.json"
                settings_file.write_text(
                    json.dumps({"enabledPlugins": [name]}),
                    encoding="utf-8",
                )
            elif scope == "project":
                settings_dir = project_dir / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                settings_file = settings_dir / "settings.json"
                settings_file.write_text(
                    json.dumps({"enabledPlugins": [name]}),
                    encoding="utf-8",
                )
            elif scope == "user":
                settings_dir = home / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                settings_file = settings_dir / "settings.json"
                settings_file.write_text(
                    json.dumps({"enabledPlugins": [name]}),
                    encoding="utf-8",
                )

        return plugin_root, plugin_data, home, project_dir

    factory._counter = 0
    return factory


def _make_env(
    *,
    plugin_root: Path,
    plugin_data: Path,
    home: Path,
    project_dir: Path | None,
    extra_pythonpath: str | None = None,
) -> dict:
    """Build a clean os.environ dict for subprocess runs."""
    import os
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(plugin_root),
        "CLAUDE_PLUGIN_DATA": str(plugin_data),
        "HOME": str(home),
    }
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)

    # Propagate PYTHONPATH so agentbundle is importable in the subprocess
    # (needed for the CLI-handoff test that imports _append_install_marker).
    existing_pp = os.environ.get("PYTHONPATH", "")
    if extra_pythonpath:
        pythonpath_parts = [extra_pythonpath]
        if existing_pp:
            pythonpath_parts.append(existing_pp)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    elif existing_pp:
        env["PYTHONPATH"] = existing_pp

    return env


def _read_marker(marker_path: Path) -> dict:
    """Parse the marker file via tomllib and return the dict."""
    return tomllib.loads(marker_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC1: stdlib-only imports and docstring
# ---------------------------------------------------------------------------

ALLOWED_MODULES = frozenset({
    "datetime", "hashlib", "json", "os", "pathlib", "sys", "tempfile", "tomllib",
})


def test_writer_is_stdlib_only():
    """AC1: the writer imports only modules from the allow-list."""
    import re
    content = WRITER.read_text(encoding="utf-8")
    pattern = re.compile(r"^(?:import|from)\s+(\S+)", re.MULTILINE)
    imported = {m.group(1).split(".")[0] for m in pattern.finditer(content)}
    # Also handle "from __future__ import" (always allowed).
    imported.discard("__future__")
    # typing module members used via "from typing import" are stdlib.
    imported.discard("typing")
    forbidden = imported - ALLOWED_MODULES
    assert not forbidden, (
        f"Writer imports modules outside the allow-list: {sorted(forbidden)}"
    )


def test_writer_docstring_names_spec():
    """AC1: the module docstring contains the spec path."""
    content = WRITER.read_text(encoding="utf-8")
    assert "docs/specs/claude-plugins-install-route/spec.md" in content


# ---------------------------------------------------------------------------
# AC2: scope detection
# ---------------------------------------------------------------------------


def test_scope_local_opt_in_for_repo_only_pack_writes_repo_marker(pack_root_factory):
    """AC2(a) + AC18 test_first_install_local_scope.

    Local opt-in for a repo-only pack → repo-scope marker written with
    install-route = "claude-plugins".
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()
    data = _read_marker(marker_path)
    entries = data.get("packs-installed", [])
    assert len(entries) == 1
    entry = entries[0]
    assert entry["name"] == "core"
    assert entry["install-route"] == "claude-plugins"

    # Hash file written.
    assert (plugin_data / "pack-manifest-hash").exists()


def test_scope_project_opt_in_for_repo_only_pack_writes_repo_marker(pack_root_factory):
    """AC2(b) + AC18 test_first_install_project_scope.

    Regression guard for Blocker-1: comparing the collapsed marker_scope="repo"
    against allowed-scopes=["repo"] must accept, not refuse.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["project"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""

    # Scope-collapse regression: must write to the repo-scope path specifically.
    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists(), f"repo-scope marker not found at {marker_path}"
    data = _read_marker(marker_path)
    entries = data.get("packs-installed", [])
    assert len(entries) == 1
    assert entries[0]["name"] == "core"


def test_scope_user_opt_in_for_user_only_pack_writes_user_marker(pack_root_factory):
    """AC2(c) + AC18 test_first_install_user_scope."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="converters",
        version="0.1.0",
        allowed_scopes=["user"],
        opt_in_at=["user"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    marker_path = home / ".agent-ready" / ".adapt-install-marker.toml"
    assert marker_path.exists()
    data = _read_marker(marker_path)
    entries = data.get("packs-installed", [])
    assert len(entries) == 1
    assert entries[0]["name"] == "converters"
    assert entries[0]["install-route"] == "claude-plugins"


def test_scope_precedence_local_beats_project_beats_user(pack_root_factory):
    """AC2(d): all three opt-ins set; most-specific (local) wins, repo-scope marker."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo", "user"],
        opt_in_at=["local", "project", "user"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    # repo-scope marker written (local wins → repo scope).
    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()
    # user-scope marker NOT written.
    user_marker = home / ".agent-ready" / ".adapt-install-marker.toml"
    assert not user_marker.exists()


def test_scope_malformed_local_json_falls_through_to_project(pack_root_factory):
    """AC2(e): malformed local-scope JSON → fall through to project."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["project"],  # project opts in
    )
    # Overwrite local settings with garbage.
    local_settings = project_dir / ".claude" / "settings.local.json"
    local_settings.write_text("{not valid json", encoding="utf-8")

    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    # Marker still written (fell through to project).
    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()


def test_scope_no_match_exits_zero_no_marker_no_hash(pack_root_factory):
    """AC2(f): no opt-in at any scope → exit 0, no marker, no hash-file."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=[],  # no settings files written
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0
    assert result.stderr == ""

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert not marker_path.exists()
    assert not (plugin_data / "pack-manifest-hash").exists()


def test_scope_project_dir_unset_skips_project_and_local_checks(pack_root_factory):
    """AC2(g): CLAUDE_PROJECT_DIR unset + user opt-in for user-only pack → user-scope marker."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="converters",
        version="0.1.0",
        allowed_scopes=["user"],
        opt_in_at=["user"],
    )
    # Do NOT pass project_dir in the env.
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=None)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    marker_path = home / ".agent-ready" / ".adapt-install-marker.toml"
    assert marker_path.exists()
    data = _read_marker(marker_path)
    entries = data.get("packs-installed", [])
    assert any(e.get("name") == "converters" for e in entries)


# ---------------------------------------------------------------------------
# AC3: allowed-scopes refusal rail
# ---------------------------------------------------------------------------


def test_refuse_repo_only_pack_at_user_scope(pack_root_factory):
    """AC3(a) + AC18: repo-only pack enabled at user scope → refuse with 'detected install scope user'."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],  # repo only
        opt_in_at=["user"],       # but opted in at user scope
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0  # exits 0 on refuse-and-warn
    assert "detected install scope user" in result.stderr
    assert "skipping marker write" in result.stderr

    # No marker written.
    assert not (project_dir / ".adapt-install-marker.toml").exists()
    assert not (home / ".agent-ready" / ".adapt-install-marker.toml").exists()
    # No hash file.
    assert not (plugin_data / "pack-manifest-hash").exists()


def test_refuse_user_only_pack_at_project_scope(pack_root_factory):
    """AC3(b): user-only pack enabled at project scope → refuse with 'detected install scope project'."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="converters",
        version="0.1.0",
        allowed_scopes=["user"],   # user only
        opt_in_at=["project"],     # but opted in at project scope
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0
    assert "detected install scope project" in result.stderr
    assert "skipping marker write" in result.stderr
    assert not (plugin_data / "pack-manifest-hash").exists()


def test_refuse_user_only_pack_at_local_scope(pack_root_factory):
    """AC3(c): user-only pack enabled at local scope → refuse with 'detected install scope local'.

    Origin-vocabulary regression guard: the writer must use the three-valued
    origin (local/project/user) in the stderr message, not the collapsed scope.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="converters",
        version="0.1.0",
        allowed_scopes=["user"],  # user only
        opt_in_at=["local"],      # opted in at local scope
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0
    assert "detected install scope local" in result.stderr
    assert "skipping marker write" in result.stderr
    assert not (plugin_data / "pack-manifest-hash").exists()


# ---------------------------------------------------------------------------
# AC4: atomic rename crash recovery
# ---------------------------------------------------------------------------


def test_atomic_rename_uses_os_replace_and_recovers_on_crash(tmp_path, pack_root_factory):
    """AC4: crash between tempfile-write and os.replace — prior marker unchanged;
    next invocation succeeds and contains both entries.
    """
    # First: write a valid marker entry for a different pack.
    plugin_root_a, plugin_data_a, home, project_dir = pack_root_factory(
        name="pack-a",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    env_a = _make_env(plugin_root=plugin_root_a, plugin_data=plugin_data_a, home=home, project_dir=project_dir)
    result = _run_writer(env_a)
    assert result.returncode == 0, result.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()
    original_content = marker_path.read_bytes()
    # Capture inode + mtime for POSIX atomicity check after crash.
    if sys.platform != "win32":
        original_ino = marker_path.stat().st_ino
        original_mtime_ns = marker_path.stat().st_mtime_ns

    # Now prepare pack-b which will crash mid-write.
    plugin_root_b, plugin_data_b, _, _ = pack_root_factory(
        name="pack-b",
        version="0.2.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    # Point pack-b to the same project dir and home so it targets the same marker file.
    # We need to add "local" opt-in for pack-b in the project_dir settings.
    local_settings = project_dir / ".claude" / "settings.local.json"
    # Update to include both packs.
    local_settings.write_text(json.dumps({"enabledPlugins": ["pack-a", "pack-b"]}), encoding="utf-8")

    # Set up the sitecustomize.py that crashes os.replace on first call.
    sitecustomize_dir = tmp_path / "sitecustomize_crash"
    sitecustomize_dir.mkdir()
    (sitecustomize_dir / "sitecustomize.py").write_text(
        textwrap.dedent("""
            import os as _os
            _original_replace = _os.replace
            _call_count = [0]

            def _crashing_replace(src, dst):
                _call_count[0] += 1
                if _call_count[0] == 1:
                    raise RuntimeError("simulated crash before os.replace")
                return _original_replace(src, dst)

            _os.replace = _crashing_replace
        """),
        encoding="utf-8",
    )

    env_b_crash = _make_env(
        plugin_root=plugin_root_b,
        plugin_data=plugin_data_b,
        home=home,
        project_dir=project_dir,
        extra_pythonpath=str(sitecustomize_dir),
    )
    result_crash = _run_writer(env_b_crash)
    # Crash means non-zero exit.
    assert result_crash.returncode != 0

    # Prior marker must be byte-unchanged.
    assert marker_path.read_bytes() == original_content, (
        "Prior marker file was modified after crash — atomicity rail broken"
    )
    # No leftover tempfile should remain after the crash (writer cleans up on error).
    assert list(project_dir.glob("*.tmp")) == [], (
        "Leftover .tmp file(s) found after crash — cleanup rail broken"
    )
    # POSIX-only: inode and mtime must be unchanged (the file was not replaced).
    if sys.platform != "win32":
        assert marker_path.stat().st_ino == original_ino, (
            "Marker file inode changed after crash — os.replace must not have run"
        )
        assert marker_path.stat().st_mtime_ns == original_mtime_ns, (
            "Marker file mtime changed after crash — os.replace must not have run"
        )

    # Next invocation (no crash) must succeed and contain both entries.
    env_b_ok = _make_env(
        plugin_root=plugin_root_b,
        plugin_data=plugin_data_b,
        home=home,
        project_dir=project_dir,
    )
    result_ok = _run_writer(env_b_ok)
    assert result_ok.returncode == 0, result_ok.stderr

    data = _read_marker(marker_path)
    names = {e["name"] for e in data.get("packs-installed", [])}
    assert "pack-a" in names
    assert "pack-b" in names


# ---------------------------------------------------------------------------
# AC5: hash file not written when marker write fails
# ---------------------------------------------------------------------------


def test_hash_file_not_written_when_marker_write_fails(tmp_path, pack_root_factory):
    """AC5: os.replace raises PermissionError → no hash file; next invocation succeeds."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )

    # Create sitecustomize.py that raises PermissionError on os.replace.
    sitecustomize_dir = tmp_path / "sitecustomize_perm"
    sitecustomize_dir.mkdir()
    (sitecustomize_dir / "sitecustomize.py").write_text(
        textwrap.dedent("""
            import os as _os
            _original_replace = _os.replace

            def _perm_replace(src, dst):
                raise PermissionError("simulated permission denied")

            _os.replace = _perm_replace
        """),
        encoding="utf-8",
    )

    env_fail = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
        extra_pythonpath=str(sitecustomize_dir),
    )
    result = _run_writer(env_fail)
    assert result.returncode != 0  # non-zero exit on marker failure

    # No hash file on disk.
    assert not (plugin_data / "pack-manifest-hash").exists()

    # Next invocation (no crash) must succeed.
    env_ok = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
    )
    result_ok = _run_writer(env_ok)
    assert result_ok.returncode == 0, result_ok.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()
    assert (plugin_data / "pack-manifest-hash").exists()


# ---------------------------------------------------------------------------
# AC6: dual-detection branch
# ---------------------------------------------------------------------------


def test_detection_cold_start_writes(pack_root_factory):
    """AC6(a): no hash file → writes both marker and hash."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    assert (project_dir / ".adapt-install-marker.toml").exists()
    assert (plugin_data / "pack-manifest-hash").exists()


def test_detection_keep_data_reinstall_writes(pack_root_factory):
    """AC6(b) + AC18 test_reinstall_after_keep_data_uninstall.

    Hash file present and matching, but marker file absent → writes both.
    Simulates reinstall-after-``--keep-data``.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )

    # Pre-seed the hash file with the correct hash.
    import hashlib
    current_hash = hashlib.sha256((plugin_root / "pack.toml").read_bytes()).hexdigest()
    (plugin_data / "pack-manifest-hash").write_text(current_hash + "\n", encoding="utf-8")

    # Marker file is absent (simulates --keep-data reinstall).
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    assert (project_dir / ".adapt-install-marker.toml").exists()


def test_detection_warm_cache_skips(pack_root_factory):
    """AC6(c) + AC18 test_warm_cache_skips_write.

    Hash file matches AND marker contains an entry → exit 0, no writes.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)

    # First run: cold start, writes both.
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    original_content = marker_path.read_bytes()

    # Second run: warm cache, nothing should change.
    result2 = _run_writer(env)
    assert result2.returncode == 0, result2.stderr
    assert result2.stderr == ""

    # Marker unchanged (no new write).
    assert marker_path.read_bytes() == original_content


# ---------------------------------------------------------------------------
# AC7: two-writers sequential + CLI-handoff datetime round-trip
# ---------------------------------------------------------------------------


def test_two_writers_sequential_both_entries_present(pack_root_factory):
    """AC7: two writers invoked sequentially against the same marker file
    produce a marker containing both [[packs-installed]] entries.
    """
    _, _, home, project_dir = pack_root_factory(
        name="__placeholder__",
        version="0.0.0",
        allowed_scopes=["repo"],
        opt_in_at=[],
    )

    # Pack A.
    plugin_root_a, plugin_data_a, _, _ = pack_root_factory(
        name="pack-a",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    # Make pack-a settings visible in the shared project_dir.
    local_settings = project_dir / ".claude" / "settings.local.json"
    local_settings.parent.mkdir(parents=True, exist_ok=True)
    local_settings.write_text(json.dumps({"enabledPlugins": ["pack-a", "pack-b"]}), encoding="utf-8")

    env_a = _make_env(plugin_root=plugin_root_a, plugin_data=plugin_data_a, home=home, project_dir=project_dir)
    result_a = _run_writer(env_a)
    assert result_a.returncode == 0, result_a.stderr

    # Pack B.
    plugin_root_b, plugin_data_b, _, _ = pack_root_factory(
        name="pack-b",
        version="0.2.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    env_b = _make_env(plugin_root=plugin_root_b, plugin_data=plugin_data_b, home=home, project_dir=project_dir)
    result_b = _run_writer(env_b)
    assert result_b.returncode == 0, result_b.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    data = _read_marker(marker_path)
    names = {e["name"] for e in data.get("packs-installed", [])}
    assert "pack-a" in names
    assert "pack-b" in names


def test_cli_to_claude_plugins_handoff_preserves_datetime(tmp_path, pack_root_factory):
    """AC7 sub-assertion: CLI-written entry round-trips through tomllib as datetime.datetime.

    Pre-seeds the target marker file by calling _append_install_marker in-process,
    then runs the Claude-plugins writer against the seeded file. Asserts:
      (a) both entries are present;
      (b) the CLI-seeded entry's installed-at round-trips as datetime.datetime (not str).
    """
    from agentbundle.commands.install import _append_install_marker

    # Create a project directory and home for the test.
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    # Seed via the CLI writer in-process (repo scope).
    _append_install_marker(
        project_dir,
        "repo",
        pack_name="cli-pack",
        pack_version="1.0.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()

    # Verify the CLI entry has a datetime installed-at.
    data = _read_marker(marker_path)
    cli_entries = [e for e in data.get("packs-installed", []) if e.get("name") == "cli-pack"]
    assert len(cli_entries) == 1
    import datetime as dt
    assert isinstance(cli_entries[0]["installed-at"], dt.datetime), (
        "CLI entry installed-at did not round-trip as datetime.datetime"
    )

    # Now run the Claude-plugins writer against the same marker file.
    plugin_root, plugin_data, _, _ = pack_root_factory(
        name="plugins-pack",
        version="0.5.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    # Make the project dir settings include plugins-pack.
    local_settings = project_dir / ".claude" / "settings.local.json"
    local_settings.parent.mkdir(parents=True, exist_ok=True)
    local_settings.write_text(json.dumps({"enabledPlugins": ["plugins-pack"]}), encoding="utf-8")

    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    # Both entries present.
    data = _read_marker(marker_path)
    names = {e["name"] for e in data.get("packs-installed", [])}
    assert "cli-pack" in names
    assert "plugins-pack" in names

    # CLI entry installed-at still round-trips as datetime.datetime (not str).
    cli_entries_after = [e for e in data["packs-installed"] if e.get("name") == "cli-pack"]
    assert len(cli_entries_after) == 1
    assert isinstance(cli_entries_after[0]["installed-at"], dt.datetime), (
        "CLI entry installed-at was demoted to str after Claude-plugins writer ran"
    )


# ---------------------------------------------------------------------------
# AC8: plugin upgrade replaces marker entry
# ---------------------------------------------------------------------------


def test_plugin_upgrade_replaces_entry_not_stacks(pack_root_factory):
    """AC8 + AC18 test_plugin_upgrade_replaces_entry.

    Pre-seeds marker with version 0.1.0; runs writer with version 0.2.0.
    Result: exactly one entry for the pack with version 0.2.0.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.2.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )

    # Pre-seed marker with the old version.
    marker_path = project_dir / ".adapt-install-marker.toml"
    import datetime as dt
    old_ts = dt.datetime(2026, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
    old_content = textwrap.dedent(f"""
        marker-schema-version = "0.1"

        [[packs-installed]]
        name = "core"
        version = "0.1.0"
        installed-at = {old_ts.strftime("%Y-%m-%dT%H:%M:%SZ")}
        install-route = "claude-plugins"
    """).lstrip()
    marker_path.write_text(old_content, encoding="utf-8")

    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    data = _read_marker(marker_path)
    core_entries = [e for e in data.get("packs-installed", []) if e.get("name") == "core"]
    assert len(core_entries) == 1, (
        f"Expected exactly 1 entry for 'core', got {len(core_entries)}"
    )
    assert core_entries[0]["version"] == "0.2.0"


# ---------------------------------------------------------------------------
# Path-jail tests (Blocker 1)
# ---------------------------------------------------------------------------


def test_marker_write_refuses_path_outside_jail(tmp_path, pack_root_factory):
    """Blocker-1: a marker path that resolves outside the per-scope jail is refused."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["user"],
        opt_in_at=["user"],
    )
    # The jail for user-scope is home/.agent-ready. We create a symlink inside
    # home/.agent-ready that points to a foreign directory (outside home).
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir()
    agent_ready = home / ".agent-ready"
    agent_ready.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Create a symlink escape: home/.agent-ready/escape -> foreign_dir
    escape_link = agent_ready / "escape"
    escape_link.symlink_to(foreign_dir)

    # Monkey-patch the writer by setting HOME and verifying it handles jailing.
    # The simplest approach: use a sitecustomize that overrides _marker_path
    # to return a path outside the jail.
    sitecustomize_dir = tmp_path / "sc_jail"
    sitecustomize_dir.mkdir()
    foreign_marker = foreign_dir / ".adapt-install-marker.toml"
    (sitecustomize_dir / "sitecustomize.py").write_text(
        textwrap.dedent(f"""
            import pathlib
            import sys
            # Override _marker_path in the writer module to return a path outside the jail.
            # We find the writer module by searching sys.modules after it loads.
            import importlib.util, os
            _writer_path = {str(WRITER)!r}
            _spec = importlib.util.spec_from_file_location("_install_marker_writer", _writer_path)
            _mod = importlib.util.module_from_spec(_spec)
            _original_marker_path = None

            def _patched_marker_path(marker_scope, project_dir, home):
                return pathlib.Path({str(foreign_marker)!r})

            # Patch after the module is executed by overriding at sys.modules level.
            import builtins
            _original_import = builtins.__import__

            def _patching_import(name, *args, **kwargs):
                mod = _original_import(name, *args, **kwargs)
                return mod
        """),
        encoding="utf-8",
    )

    # Use the simpler direct approach: build a fake env where the writer
    # under test is invoked but we verify via the writer's own _assert_under.
    # We test this by importing the writer and calling _write_marker directly.
    spec = importlib.util.spec_from_file_location("_install_marker_writer", WRITER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    jail = agent_ready  # user-scope jail
    outside_path = foreign_dir / ".adapt-install-marker.toml"

    import datetime as dt
    new_entry = {
        "name": "core",
        "version": "0.1.0",
        "installed-at": dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        "install-route": "claude-plugins",
    }

    with pytest.raises(ValueError, match="escapes the per-scope jail"):
        mod._write_marker(outside_path, new_entry, jail)

    # The foreign marker file must not have been created.
    assert not outside_path.exists(), (
        "Writer wrote to a path outside the jail — jail check failed"
    )


# ---------------------------------------------------------------------------
# Symlink probe test (Blocker 2)
# ---------------------------------------------------------------------------


def test_user_marker_refuses_symlinked_agent_ready(tmp_path, pack_root_factory):
    """Blocker-2: writer refuses when ~/.agent-ready is a symlink to a foreign directory."""
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["user"],
        opt_in_at=["user"],
    )
    # Pre-create home/.agent-ready as a symlink to a foreign directory.
    foreign_dir = tmp_path / "foreign_agent_ready"
    foreign_dir.mkdir()
    agent_ready = home / ".agent-ready"
    agent_ready.symlink_to(foreign_dir)

    env = _make_env(plugin_root=plugin_root, plugin_data=plugin_data, home=home, project_dir=project_dir)
    result = _run_writer(env)
    assert result.returncode != 0
    assert "not a regular directory" in result.stderr or "symlink" in result.stderr.lower()

    # Foreign directory must not have received a marker write.
    assert not (foreign_dir / ".adapt-install-marker.toml").exists()


# ---------------------------------------------------------------------------
# Pass-through unresolved-markers / new-companions test (Blocker 3)
# ---------------------------------------------------------------------------


def test_cli_seed_unresolved_markers_and_new_companions_survive_rewrite(
    tmp_path, pack_root_factory
):
    """Blocker-3: CLI-seeded unresolved-markers and new-companions survive a
    Claude-plugins writer re-serialisation pass.
    """
    from agentbundle.commands.install import _append_install_marker

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    # Seed via the CLI writer with non-empty arrays for both fields.
    _append_install_marker(
        project_dir,
        "repo",
        pack_name="cli-pack",
        pack_version="1.0.0",
        unresolved_markers=["marker-a", "marker-b"],
        new_companions=["companion-x"],
        allowed_prefixes=None,
    )

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()

    # Verify the CLI seed has the arrays.
    data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    cli_entry = next(e for e in data["packs-installed"] if e["name"] == "cli-pack")
    assert cli_entry["unresolved-markers"] == ["marker-a", "marker-b"]
    assert cli_entry["new-companions"] == ["companion-x"]

    # Now run the Claude-plugins writer against the same marker.
    plugin_root, plugin_data, _, _ = pack_root_factory(
        name="plugins-pack",
        version="0.5.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )
    local_settings = project_dir / ".claude" / "settings.local.json"
    local_settings.parent.mkdir(parents=True, exist_ok=True)
    local_settings.write_text(
        json.dumps({"enabledPlugins": ["plugins-pack"]}), encoding="utf-8"
    )

    env = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
    )
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    # Re-read and verify the CLI-seeded arrays survived.
    data2 = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    cli_entries = [e for e in data2["packs-installed"] if e["name"] == "cli-pack"]
    assert len(cli_entries) == 1, "CLI-seeded entry was lost after writer pass"
    assert cli_entries[0]["unresolved-markers"] == ["marker-a", "marker-b"], (
        "unresolved-markers was dropped during re-serialisation"
    )
    assert cli_entries[0]["new-companions"] == ["companion-x"], (
        "new-companions was dropped during re-serialisation"
    )


# ---------------------------------------------------------------------------
# _emit_basic_string parity test (Concern 5)
# ---------------------------------------------------------------------------


def test_emit_basic_string_parity_with_source():
    """Concern-5: vendored _emit_basic_string in install-marker.py produces
    byte-identical output to the source in agentbundle.config for every input
    in the fixed attack corpus.
    """
    from agentbundle.config import _emit_basic_string as source_fn

    # Load the vendored copy from the writer template via importlib.
    spec = importlib.util.spec_from_file_location("_install_marker_writer", WRITER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    vendored_fn = mod._emit_basic_string

    corpus = [
        " ", "", "hello", 'a"b', "a\\b", "\n", "\x00", "\x01", "\x1f", "\x7f",
        "café", "🚀",
    ]
    for value in corpus:
        source_out = source_fn(value)
        vendored_out = vendored_fn(value)
        assert source_out == vendored_out, (
            f"_emit_basic_string mismatch for {value!r}: "
            f"source={source_out!r} vendored={vendored_out!r}"
        )


# ---------------------------------------------------------------------------
# TOML-injection via pack name test (Concern 6)
# ---------------------------------------------------------------------------


def test_pack_toml_injection_via_name_is_neutralised(tmp_path, pack_root_factory):
    """Concern-6: adversarial pack name with embedded quote is sanitised;
    exactly one entry with the literal name survives in the parsed marker.
    """
    # Build a pack with a name containing an injection attempt.
    injected_name = 'core"injected'
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name=injected_name,
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )

    env = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
    )
    result = _run_writer(env)
    assert result.returncode == 0, result.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists()

    # Parse via tomllib — if injection succeeded, the parse would either fail
    # or produce phantom keys. We assert exactly one entry with the literal name.
    data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    entries = data.get("packs-installed", [])
    assert len(entries) == 1, f"Expected 1 entry, got {len(entries)}: {entries}"
    assert entries[0]["name"] == injected_name, (
        f"Entry name {entries[0]['name']!r} != expected {injected_name!r}"
    )


# ---------------------------------------------------------------------------
# Missing env-var tests (Concern 17)
# ---------------------------------------------------------------------------


def test_missing_claude_plugin_root_exits_nonzero_with_stderr(tmp_path):
    """Concern-17a: CLAUDE_PLUGIN_ROOT unset → exit 1 with stderr naming the variable."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_DATA": str(tmp_path / "data"),
        "HOME": str(tmp_path / "home"),
    }
    result = _run_writer(env)
    assert result.returncode != 0
    assert "CLAUDE_PLUGIN_ROOT" in result.stderr


def test_missing_claude_plugin_data_exits_nonzero_with_stderr(tmp_path):
    """Concern-17b: CLAUDE_PLUGIN_DATA unset → exit 1 with stderr naming the variable."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(tmp_path / "root"),
        "HOME": str(tmp_path / "home"),
    }
    result = _run_writer(env)
    assert result.returncode != 0
    assert "CLAUDE_PLUGIN_DATA" in result.stderr


def test_missing_home_exits_nonzero_with_stderr(tmp_path):
    """Concern-17c: HOME unset → exit 1 with stderr naming the variable."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(tmp_path / "root"),
        "CLAUDE_PLUGIN_DATA": str(tmp_path / "data"),
    }
    result = _run_writer(env)
    assert result.returncode != 0
    assert "HOME" in result.stderr


# ---------------------------------------------------------------------------
# Malformed pack.toml test (Concern 18)
# ---------------------------------------------------------------------------


def test_malformed_pack_toml_exits_nonzero_with_stderr(tmp_path):
    """Concern-18: garbage pack.toml → exit 1 with stderr mentioning 'pack.toml'."""
    plugin_root = tmp_path / "plugin_root"
    plugin_root.mkdir()
    (plugin_root / "pack.toml").write_text("not valid toml {{{{", encoding="utf-8")

    plugin_data = tmp_path / "plugin_data"
    plugin_data.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(plugin_root),
        "CLAUDE_PLUGIN_DATA": str(plugin_data),
        "HOME": str(home),
    }
    result = _run_writer(env)
    assert result.returncode != 0
    assert "pack.toml" in result.stderr


# ---------------------------------------------------------------------------
# Hash-write-failure self-heal test (Concern 19)
# ---------------------------------------------------------------------------


def test_hash_file_write_failure_self_heals(tmp_path, pack_root_factory):
    """Concern-19: hash-write failure → marker written, exit 0 + warning;
    second run completes both writes; final marker has exactly one entry.
    """
    plugin_root, plugin_data, home, project_dir = pack_root_factory(
        name="core",
        version="0.1.0",
        allowed_scopes=["repo"],
        opt_in_at=["local"],
    )

    # First run: make the plugin_data directory read-only so hash write fails.
    # The marker itself is in project_dir which remains writable.
    sitecustomize_dir = tmp_path / "sc_hash_fail"
    sitecustomize_dir.mkdir()
    (sitecustomize_dir / "sitecustomize.py").write_text(
        textwrap.dedent("""
            import os as _os
            _original_replace = _os.replace
            _call_count = [0]

            def _selective_replace(src, dst):
                # Allow the first replace (marker write), fail the second (hash write).
                _call_count[0] += 1
                if _call_count[0] == 2:
                    raise PermissionError("simulated hash write failure")
                return _original_replace(src, dst)

            _os.replace = _selective_replace
        """),
        encoding="utf-8",
    )

    env_fail = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
        extra_pythonpath=str(sitecustomize_dir),
    )
    result_fail = _run_writer(env_fail)
    # Exit 0 even on hash-write failure (non-fatal).
    assert result_fail.returncode == 0, result_fail.stderr
    # Warning present.
    assert "hash write failed" in result_fail.stderr

    marker_path = project_dir / ".adapt-install-marker.toml"
    assert marker_path.exists(), "Marker must be written even when hash write fails"
    # Hash file NOT written on first run.
    assert not (plugin_data / "pack-manifest-hash").exists()

    # Second run (no sabotage): both marker and hash complete.
    env_ok = _make_env(
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        home=home,
        project_dir=project_dir,
    )
    result_ok = _run_writer(env_ok)
    assert result_ok.returncode == 0, result_ok.stderr
    assert (plugin_data / "pack-manifest-hash").exists()

    # Final marker: exactly one entry for the pack (upgrade-replace, no duplication).
    data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    core_entries = [e for e in data.get("packs-installed", []) if e["name"] == "core"]
    assert len(core_entries) == 1, (
        f"Expected exactly 1 entry for 'core', got {len(core_entries)}"
    )
