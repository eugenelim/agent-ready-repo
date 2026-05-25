"""Integration tests for the APM-route surface of the install-marker writer.

Spec: docs/specs/apm-install-route-parity/spec.md

T1 layer (this file's rail-level tests): exercise individual writer rails —
``--install-route`` argparse, data-directory precedence shim, APM scope
detection by projected-hook path, allowed-scopes refusal, and the route-
flag-driven branch selection between APM and claude-plugins paths. T5's
later end-to-end tests (added in the same PR) stage realistic apm_modules/
layouts and assert on the full marker write.

Each test runs ``packages/agentbundle/templates/install-marker.py`` in a
subprocess against a fixture-controlled environment quintet:
  - ``${CLAUDE_PLUGIN_DATA}``  — APM-Claude-Code data dir (optional under APM)
  - ``${PLUGIN_ROOT}``         — APM's generic per-target token
  - ``${CURSOR_PLUGIN_ROOT}``  — APM-Cursor pack-root token
  - ``${HOME}``                — user home directory
  - writer's own projected location — tests symlink/copy the writer into
    a fixture path so ``Path(__file__).resolve()`` yields the fixture-
    resident location.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import textwrap
import tomllib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Source template path — tests project copies of this into fixture pack roots
# so ``__file__`` resolves under the fixture, not the source tree.
# ---------------------------------------------------------------------------

SOURCE_WRITER = Path(__file__).resolve().parents[2] / "templates" / "install-marker.py"
assert SOURCE_WRITER.exists(), f"Writer template not found at {SOURCE_WRITER}"

# packages/agentbundle/tests/integration/ → parents[4] = <repo-root>
REPO_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project_writer(pack_root: Path) -> Path:
    """Copy the canonical writer into ``<pack_root>/.apm/hooks/install-marker.py``.

    Returns the projected path. APM's HookIntegrator projects a single authored
    hook command into per-target cache locations; this helper mirrors that
    derivation for the test fixture.
    """
    hooks_dir = pack_root / ".apm" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    projected = hooks_dir / "install-marker.py"
    projected.write_bytes(SOURCE_WRITER.read_bytes())
    return projected


def _write_pack_toml(
    pack_root: Path,
    *,
    name: str = "core",
    version: str = "0.1.0",
    allowed_scopes: "list[str] | None" = None,
) -> None:
    if allowed_scopes is None:
        allowed_scopes = ["repo", "user"]
    content = textwrap.dedent(f"""
        [pack]
        name = {json.dumps(name)}
        version = {json.dumps(version)}
        description = "Test pack."

        [pack.install]
        default-scope = {json.dumps(allowed_scopes[0])}
        allowed-scopes = {json.dumps(allowed_scopes)}
    """).lstrip()
    (pack_root / "pack.toml").write_text(content, encoding="utf-8")


def _run_writer(
    projected_writer: Path,
    *,
    env: dict,
    cwd: Path,
    install_route: str = "apm",
    extra_args: "list[str] | None" = None,
) -> "subprocess.CompletedProcess":
    import subprocess
    args = [sys.executable, str(projected_writer), "--install-route", install_route]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        env=env,
        cwd=str(cwd),
        capture_output=True,
        check=False,
        text=True,
    )


def _base_env(extra: "dict | None" = None) -> dict:
    env = {"PATH": os.environ.get("PATH", "")}
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


def _read_marker(marker_path: Path) -> dict:
    return tomllib.loads(marker_path.read_text(encoding="utf-8"))


# ===========================================================================
# AC1 — import allow-list grows by one entry (argparse)
# ===========================================================================


ALLOWED_POST_EDIT_MODULES = frozenset({
    "argparse", "datetime", "hashlib", "json", "os", "pathlib",
    "re", "sys", "tempfile", "tomllib",
})


def test_writer_imports_argparse_only_added_to_allowlist():
    """AC1: the writer's top-level imports are exactly the post-edit module set."""
    import re
    content = SOURCE_WRITER.read_text(encoding="utf-8")
    pattern = re.compile(r"^(?:import|from)\s+(\S+)", re.MULTILINE)
    imported = {m.group(1).split(".")[0] for m in pattern.finditer(content)}
    imported.discard("__future__")
    imported.discard("typing")
    forbidden = imported - ALLOWED_POST_EDIT_MODULES
    assert not forbidden, (
        f"Writer imports outside the post-edit allow-list: {sorted(forbidden)}"
    )
    missing = ALLOWED_POST_EDIT_MODULES - imported
    # argparse must be in the actual import set; others are also expected.
    assert "argparse" in imported, "argparse must be imported by the writer"
    # The other entries are inherited from the precedent spec; they must
    # remain imported (regression guard against an accidental drop).
    assert not missing or missing == {"argparse"}, (
        f"Writer is missing expected stdlib imports: {sorted(missing)}"
    )


# ===========================================================================
# AC2 — --install-route flag (required, two-valued)
# ===========================================================================


def test_install_route_flag_claude_plugins_records_claude_plugins(tmp_path):
    """AC2 (a): --install-route claude-plugins → marker carries install-route = "claude-plugins"."""
    pack_root = tmp_path / "pack_root"
    pack_root.mkdir()
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    home = tmp_path / "home"
    home.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    # Opt-in via local enabledPlugins so the claude-plugins branch fires.
    settings_dir = project_dir / ".claude"
    settings_dir.mkdir()
    (settings_dir / "settings.local.json").write_text(
        json.dumps({"enabledPlugins": ["core"]}), encoding="utf-8"
    )
    plugin_data = tmp_path / "data"
    plugin_data.mkdir()

    env = _base_env({
        "CLAUDE_PLUGIN_ROOT": pack_root,
        "CLAUDE_PLUGIN_DATA": plugin_data,
        "HOME": home,
        "CLAUDE_PROJECT_DIR": project_dir,
    })
    result = _run_writer(SOURCE_WRITER, env=env, cwd=tmp_path, install_route="claude-plugins")
    assert result.returncode == 0, result.stderr
    marker = _read_marker(project_dir / ".adapt-install-marker.toml")
    assert marker["packs-installed"][0]["install-route"] == "claude-plugins"


def test_install_route_flag_apm_records_apm(tmp_path):
    """AC2 (b): --install-route apm → marker carries install-route = "apm"."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd, install_route="apm")
    assert result.returncode == 0, result.stderr
    marker = _read_marker(cwd / ".adapt-install-marker.toml")
    assert marker["packs-installed"][0]["install-route"] == "apm"


def test_install_route_flag_invalid_fails_fast(tmp_path):
    """AC2 (c): an invalid choice value → argparse usage error on stderr."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SOURCE_WRITER), "--install-route", "foo"],
        env=_base_env(),
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr or "usage" in result.stderr.lower()


def test_install_route_flag_absent_fails_fast(tmp_path):
    """AC2 (d): flag absence → argparse "required" error."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SOURCE_WRITER)],
        env=_base_env({"HOME": tmp_path / "home"}),
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode != 0
    assert "required" in result.stderr.lower() or "install-route" in result.stderr


# ===========================================================================
# AC3 — data-directory resolution precedence
# ===========================================================================


def _make_apm_fixture(tmp_path, *, set_in_env, allowed_scopes=("repo",)):
    """Build an APM-shaped fixture.

    ``set_in_env`` is a list/tuple of token names to populate; the others
    remain unset.
    """
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=list(allowed_scopes))
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"HOME": home})
    for token in set_in_env:
        if token == "CLAUDE_PLUGIN_DATA":
            cpd = tmp_path / "cpd"
            cpd.mkdir()
            env["CLAUDE_PLUGIN_DATA"] = str(cpd)
        elif token == "PLUGIN_ROOT":
            env["PLUGIN_ROOT"] = str(pack_root)
        elif token == "CURSOR_PLUGIN_ROOT":
            env["CURSOR_PLUGIN_ROOT"] = str(pack_root)
        elif token == "CLAUDE_PLUGIN_ROOT":
            env["CLAUDE_PLUGIN_ROOT"] = str(pack_root)
    return projected, cwd, home, pack_root, env


def test_data_dir_resolves_claude_plugin_data_when_set(tmp_path):
    """AC3 (a): only ${CLAUDE_PLUGIN_DATA} set → resolved path equals it."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["CLAUDE_PLUGIN_DATA", "CLAUDE_PLUGIN_ROOT"]
    )
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    hash_file = Path(env["CLAUDE_PLUGIN_DATA"]) / "pack-manifest-hash"
    assert hash_file.exists(), f"hash file expected at {hash_file}"


def test_data_dir_resolves_plugin_root_data_when_only_plugin_root_set(tmp_path):
    """AC3 (b): only ${PLUGIN_ROOT} set → ${PLUGIN_ROOT}/.data."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["PLUGIN_ROOT"]
    )
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    expected = pack_root / ".data" / "pack-manifest-hash"
    assert expected.exists(), f"hash file expected at {expected}"


def test_data_dir_resolves_cursor_plugin_root_data_when_only_cursor_set(tmp_path):
    """AC3 (c): only ${CURSOR_PLUGIN_ROOT} set → ${CURSOR_PLUGIN_ROOT}/.data."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["CURSOR_PLUGIN_ROOT"]
    )
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    expected = pack_root / ".data" / "pack-manifest-hash"
    assert expected.exists()


def test_data_dir_unresolvable_exits_zero_no_writes(tmp_path):
    """AC3 (d): no data-dir token set → exit 0, no marker, no hash file."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(tmp_path, set_in_env=[])
    # Empty-string PLUGIN_ROOT must also be treated as unset.
    env["PLUGIN_ROOT"] = ""
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert not (cwd / ".adapt-install-marker.toml").exists()
    assert not (pack_root / ".data").exists()


def test_data_dir_created_when_absent(tmp_path):
    """AC3 (e): mkdir(parents=True, exist_ok=True) rail."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["PLUGIN_ROOT"]
    )
    # Confirm .data doesn't exist before the writer runs.
    assert not (pack_root / ".data").exists()
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert (pack_root / ".data").is_dir()
    assert (pack_root / ".data" / "pack-manifest-hash").exists()


def test_data_dir_claude_plugin_data_wins_when_all_set(tmp_path):
    """AC3 (f, precedence pin): all three set → ${CLAUDE_PLUGIN_DATA} wins."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["CLAUDE_PLUGIN_DATA", "PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT"]
    )
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    cpd_hash = Path(env["CLAUDE_PLUGIN_DATA"]) / "pack-manifest-hash"
    pr_hash = pack_root / ".data" / "pack-manifest-hash"
    assert cpd_hash.exists(), "CLAUDE_PLUGIN_DATA must win precedence"
    assert not pr_hash.exists(), "PLUGIN_ROOT/.data must NOT be used when CLAUDE_PLUGIN_DATA is set"


def test_data_dir_plugin_root_wins_over_cursor_plugin_root(tmp_path):
    """AC3 (g, second adjacent-pair pin): PLUGIN_ROOT wins over CURSOR_PLUGIN_ROOT."""
    projected, cwd, home, pack_root, env = _make_apm_fixture(
        tmp_path, set_in_env=["PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT"]
    )
    # In _make_apm_fixture both tokens point at the same pack_root; set the
    # cursor token to a separate path so we can see which directory wins.
    cur_root = tmp_path / "cursor_root"
    cur_root.mkdir()
    # Write a stand-in pack.toml so a (wrong-branch) read wouldn't crash.
    _write_pack_toml(cur_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    env["CURSOR_PLUGIN_ROOT"] = str(cur_root)
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert (pack_root / ".data" / "pack-manifest-hash").exists()
    assert not (cur_root / ".data").exists()


# ===========================================================================
# AC4 — APM scope detection by projected-hook path
# ===========================================================================


def test_apm_scope_writer_under_cwd_nested_under_home_is_repo(tmp_path):
    """AC4 (a, first-branch-wins precedence test). Fixture: home=$tmp/home,
    cwd=$tmp/home/proj, writer at $tmp/home/proj/apm_modules/<pack>/. Both
    containment checks succeed in the abstract; the first-branch-wins rule
    must pick repo. A buggy home-first impl would silently flip to user.
    """
    home = tmp_path / "home"
    home.mkdir()
    cwd = home / "proj"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    projected = _project_writer(pack_root)

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    repo_marker = cwd / ".adapt-install-marker.toml"
    user_marker = home / ".agentbundle" / ".adapt-install-marker.toml"
    assert repo_marker.exists(), "expected repo-scope marker"
    assert not user_marker.exists(), "user-scope marker must NOT have been written"


def test_apm_scope_writer_under_home_is_user(tmp_path):
    """AC4 (b): writer under $HOME (and not under cwd) → user scope."""
    home = tmp_path / "home"
    home.mkdir()
    pack_root = home / ".apm" / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    projected = _project_writer(pack_root)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    user_marker = home / ".agentbundle" / ".adapt-install-marker.toml"
    assert user_marker.exists()


def test_apm_scope_writer_under_neither_exits_zero(tmp_path):
    """AC4 (c): writer under neither cwd nor $HOME → exit 0, no writes."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pack_root = elsewhere / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert not (cwd / ".adapt-install-marker.toml").exists()
    assert not (home / ".agentbundle").exists()


def test_apm_scope_resolves_symlinks_on_both_sides(tmp_path):
    """AC4 (d): writer reached via symlink → .resolve() on both sides → repo."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable on this platform")
    cwd = tmp_path / "repo"
    cwd.mkdir()
    real_pack = cwd / "apm_modules" / "core"
    real_pack.mkdir(parents=True)
    _write_pack_toml(real_pack, allowed_scopes=["repo"])
    real_writer = _project_writer(real_pack)
    # Create a symlink to the writer at a different path inside cwd.
    link_dir = cwd / "cache-link"
    link_dir.mkdir()
    link = link_dir / "install-marker.py"
    try:
        os.symlink(real_writer, link)
    except OSError:
        pytest.skip("symlink creation forbidden")
    home = tmp_path / "home"
    home.mkdir()
    env = _base_env({"PLUGIN_ROOT": real_pack, "HOME": home})
    result = _run_writer(link, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    assert (cwd / ".adapt-install-marker.toml").exists()


def test_apm_scope_writer_under_home_but_not_cwd_picks_user(tmp_path):
    """AC4 (e, home-branch coverage when writer is outside cwd): writer under
    $HOME (but not under cwd) → user. Both check orders yield "user" here
    because cwd-containment fails; this is the home-branch firing case, not
    a precedence test (that's case (a))."""
    home = tmp_path / "home"
    home.mkdir()
    cwd = home / "proj"
    cwd.mkdir()
    pack_root = home / ".apm" / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    projected = _project_writer(pack_root)

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    user_marker = home / ".agentbundle" / ".adapt-install-marker.toml"
    assert user_marker.exists()
    assert not (cwd / ".adapt-install-marker.toml").exists()


# ===========================================================================
# AC5 — allowed-scopes refusal rail unchanged under APM scope detection
# ===========================================================================


def test_apm_refuse_repo_only_pack_at_user_scope(tmp_path):
    """AC5 (a): repo-only pack, writer projected under $HOME → refuse-and-warn, exit 0."""
    home = tmp_path / "home"
    home.mkdir()
    pack_root = home / ".apm" / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0
    assert "detected install scope user" in result.stderr
    assert "skipping marker write" in result.stderr
    assert not (home / ".agentbundle" / ".adapt-install-marker.toml").exists()


def test_apm_refuse_user_only_pack_at_project_scope(tmp_path):
    """AC5 (b): user-only pack, writer projected under cwd → refuse-and-warn, exit 0."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["user"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0
    assert "detected install scope repo" in result.stderr
    assert not (cwd / ".adapt-install-marker.toml").exists()


# ===========================================================================
# AC6 — route-flag dispatches scope detection
# ===========================================================================


def test_route_flag_dispatches_claude_plugins_scope_detection(tmp_path):
    """AC6 (a): --install-route claude-plugins + enabledPlugins file + writer
    under cwd → marker scope comes from _detect_origin (enabledPlugins walk),
    NOT from the projected-path mechanism."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    _project_writer(pack_root)
    # Set the claude-plugins-route environment so the writer's CP branch
    # uses these paths; opt-in at *user* scope via $HOME/.claude/settings.json
    # so a buggy "use APM mechanism anyway" path would write repo-scope and
    # this assertion would fail.
    home = tmp_path / "home"
    home.mkdir()
    settings_dir = home / ".claude"
    settings_dir.mkdir()
    (settings_dir / "settings.json").write_text(
        json.dumps({"enabledPlugins": ["core"]}), encoding="utf-8"
    )
    plugin_data = tmp_path / "data"
    plugin_data.mkdir()

    env = _base_env({
        "CLAUDE_PLUGIN_ROOT": pack_root,
        "CLAUDE_PLUGIN_DATA": plugin_data,
        "HOME": home,
        # Do NOT set CLAUDE_PROJECT_DIR — we want enabledPlugins at user scope
        # to be the only opt-in surface.
    })
    # Run the SOURCE_WRITER (not the projected copy) — this branch doesn't
    # consult __file__'s location.
    result = _run_writer(SOURCE_WRITER, env=env, cwd=cwd, install_route="claude-plugins")
    assert result.returncode == 0, result.stderr
    user_marker = home / ".agentbundle" / ".adapt-install-marker.toml"
    assert user_marker.exists(), (
        "enabledPlugins-driven (user-scope) detection must win under --install-route claude-plugins"
    )
    assert not (cwd / ".adapt-install-marker.toml").exists()


def test_route_flag_dispatches_apm_scope_detection(tmp_path):
    """AC6 (b): --install-route apm + writer under cwd + enabledPlugins file
    present → marker scope comes from projected-path mechanism (repo), NOT
    from _detect_origin (which would yield user from the settings file)."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, allowed_scopes=["repo", "user"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()
    # Plant an enabledPlugins file at user scope; if the APM branch erroneously
    # consults it, it would land a user-scope marker instead of repo.
    settings_dir = home / ".claude"
    settings_dir.mkdir()
    (settings_dir / "settings.json").write_text(
        json.dumps({"enabledPlugins": ["core"]}), encoding="utf-8"
    )

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd, install_route="apm")
    assert result.returncode == 0, result.stderr
    assert (cwd / ".adapt-install-marker.toml").exists()
    assert not (home / ".agentbundle" / ".adapt-install-marker.toml").exists()


# ===========================================================================
# T5 — End-to-end APM integration tests (AC12)
#
# T1 above tests individual writer rails (one rail per test); T5 below
# stages full apm_modules/-shaped fixtures and asserts the integrated marker
# write. The two layers do not duplicate assertions: T1 catches a rail-level
# regression; T5 catches an integration-level regression where the rails
# interact (e.g. a fixture pack whose pack.toml allowed-scopes reads
# correctly through one route but silently bypasses validation through
# another).
# ===========================================================================


def test_first_install_end_to_end_core_project_scope(tmp_path):
    """AC12 (a) / RFC-0010 Q6 close-trigger 1: apm install core at project scope.

    Stage the projected pack at ${tmp_path}/repo/apm_modules/core/; invoke the
    writer with --install-route apm, cwd = ${tmp_path}/repo,
    ${PLUGIN_ROOT}=${tmp_path}/repo/apm_modules/core; assert the marker file
    at ${tmp_path}/repo/.adapt-install-marker.toml contains a
    [[packs-installed]] entry with name = "core", install-route = "apm",
    and a well-formed installed-at datetime."""
    cwd = tmp_path / "repo"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr

    marker = _read_marker(cwd / ".adapt-install-marker.toml")
    entries = marker["packs-installed"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["name"] == "core"
    assert entry["install-route"] == "apm"
    # installed-at must round-trip as datetime under tomllib
    import datetime
    assert isinstance(entry["installed-at"], datetime.datetime)


def test_first_install_end_to_end_converters_user_scope(tmp_path):
    """AC12 (b) / RFC-0010 Q6 close-trigger 2: apm install -g converters at user scope."""
    home = tmp_path / "home"
    home.mkdir()
    pack_root = home / ".apm" / "apm_modules" / "converters"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="converters", version="0.1.0", allowed_scopes=["user"])
    projected = _project_writer(pack_root)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr

    marker = _read_marker(home / ".agentbundle" / ".adapt-install-marker.toml")
    entries = marker["packs-installed"]
    assert len(entries) == 1
    assert entries[0]["name"] == "converters"
    assert entries[0]["install-route"] == "apm"


def test_refuse_repo_only_pack_at_user_scope_e2e(tmp_path):
    """AC12 (c) / AC5 (a) end-to-end: repo-only pack staged under
    ~/.apm/apm_modules/ → refuse-and-warn, no marker, no hash file."""
    home = tmp_path / "home"
    home.mkdir()
    pack_root = home / ".apm" / "apm_modules" / "repo-only-pack"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="repo-only-pack", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0
    assert "detected install scope user" in result.stderr
    assert not (home / ".agentbundle" / ".adapt-install-marker.toml").exists()
    assert not (pack_root / ".data" / "pack-manifest-hash").exists()


def test_refuse_user_only_pack_at_project_scope_e2e(tmp_path):
    """AC12 (c) / AC5 (b) end-to-end: user-only pack staged under
    ./apm_modules/ → refuse-and-warn, no marker, no hash file."""
    cwd = tmp_path / "repo"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "user-only-pack"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="user-only-pack", allowed_scopes=["user"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0
    assert "detected install scope repo" in result.stderr
    assert not (cwd / ".adapt-install-marker.toml").exists()


def test_lockfile_replay_replaces_entry(tmp_path):
    """AC12 (d): pre-seed a marker with name=core/version=0.1.0; stage a
    pack root with version=0.2.0; run the writer; assert exactly one entry
    for name=core with version=0.2.0 (no duplicate, no leftover)."""
    cwd = tmp_path / "repo"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.2.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    # Pre-seed the marker with an older entry for the same pack.
    import datetime
    pre_seeded = (
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "core"\n'
        'version = "0.1.0"\n'
        "installed-at = 2026-05-20T10:00:00Z\n"
        'install-route = "apm"\n'
    )
    (cwd / ".adapt-install-marker.toml").write_text(pre_seeded, encoding="utf-8")

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr

    marker = _read_marker(cwd / ".adapt-install-marker.toml")
    entries = [e for e in marker["packs-installed"] if e["name"] == "core"]
    assert len(entries) == 1, f"expected exactly one entry for core, got {len(entries)}"
    assert entries[0]["version"] == "0.2.0"


def test_per_target_characterisation_claude_code(tmp_path):
    """AC12 (e): the one HookIntegrator-covered target whose data-directory
    token (${CLAUDE_PLUGIN_DATA}) and first-session semantics are
    characterised at spec time. Copilot/Cursor/Gemini are intentionally
    absent here — their per-target tokens are unconfirmed at PR time and
    a skipped-in-CI test is not honest coverage. Per-target first-firing
    ships as AC17's manual-QA matrix rows."""
    cwd = tmp_path / "repo"
    cwd.mkdir()
    # APM's Claude Code target rewrites ${PLUGIN_ROOT} to
    # ${CLAUDE_PLUGIN_ROOT} and exports ${CLAUDE_PLUGIN_DATA}. Stage the
    # fixture in this shape.
    pack_root = cwd / ".claude" / "plugins" / "apm-claude-cache" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()
    cpd = pack_root / "data"
    cpd.mkdir()

    env = _base_env({
        "CLAUDE_PLUGIN_ROOT": pack_root,
        "CLAUDE_PLUGIN_DATA": cpd,
        "HOME": home,
    })
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr

    marker = _read_marker(cwd / ".adapt-install-marker.toml")
    assert marker["packs-installed"][0]["name"] == "core"
    assert marker["packs-installed"][0]["install-route"] == "apm"
    # ${CLAUDE_PLUGIN_DATA} wins precedence — hash file lands there.
    assert (cpd / "pack-manifest-hash").exists()


def test_data_dir_treats_empty_string_plugin_root_as_unset(tmp_path):
    """AC3 regression guard for the empty-string-as-unset rail (spec.md:585).

    A refactor from `if pr:` to `if "PLUGIN_ROOT" in env:` would silently
    break the rail; this test sets PLUGIN_ROOT="" alongside CURSOR_PLUGIN_ROOT
    pointing at a real path and asserts the cursor path wins. The truthiness
    check (`if pr:`) treats the empty string as unset; a containment check
    would not."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({
        "PLUGIN_ROOT": "",          # set-but-empty must be treated as unset
        "CURSOR_PLUGIN_ROOT": pack_root,
        "HOME": home,
    })
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr
    # Hash file lands under CURSOR_PLUGIN_ROOT/.data, NOT under PLUGIN_ROOT/.data
    # (the empty PLUGIN_ROOT was correctly skipped).
    assert (pack_root / ".data" / "pack-manifest-hash").exists()


def test_apm_writer_to_reader_integration_journey(tmp_path):
    """Quality-engineer Concern 2: integrated journey from writer to reader.

    Run the writer to produce a real marker file, then feed the produced
    marker (not a hand-authored fixture) through the core pack's
    session-start `_pack_names_from_marker` helper. Asserts the
    end-to-end chain — writer-emit → reader-parse — holds for the APM
    route. If a future regression in marker serialisation produced
    output the reader cannot parse, T1/T5 would still pass (they assert
    on `tomllib.loads`-parsed dicts) but this test would fail.
    """
    import importlib.util

    cwd = tmp_path / "repo"
    cwd.mkdir()
    pack_root = cwd / "apm_modules" / "core"
    pack_root.mkdir(parents=True)
    _write_pack_toml(pack_root, name="core", version="0.1.0", allowed_scopes=["repo"])
    projected = _project_writer(pack_root)
    home = tmp_path / "home"
    home.mkdir()

    env = _base_env({"PLUGIN_ROOT": pack_root, "HOME": home})
    result = _run_writer(projected, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr

    marker_path = cwd / ".adapt-install-marker.toml"
    assert marker_path.exists(), "writer must produce a marker file"

    # Load the core pack's session-start hook as a module and exercise
    # _pack_names_from_marker against the writer-produced marker.
    session_start_path = (
        REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "session-start.py"
    )
    spec = importlib.util.spec_from_file_location("_ss_hook", session_start_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    names = mod._pack_names_from_marker(marker_path)
    assert names == ["core"], (
        f"reader must surface the pack name the writer emitted; got {names}"
    )
