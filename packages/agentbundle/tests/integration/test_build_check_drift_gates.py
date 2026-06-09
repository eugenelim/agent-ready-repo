"""Integration tests for the three mechanical drift gates in ``make build-check`` (T9).

The three gates are wired into ``run_build_check_drift_gates`` in
``agentbundle.build.self_host`` and called from ``cmd_check``.

  1. **Writer-template drift (AC20a):** every derived
     ``dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py``
     must be byte-identical to the canonical template.

  2. **Source-shape plugin.json (AC10 gate 2, in-Python defence-in-depth):**
     every ``packs/<pack>/.claude-plugin/plugin.json`` must not carry a
     ``hooks`` block.

  3. **Vendored ``_emit_basic_string`` parity (AC20b):** the template's
     vendored ``_emit_basic_string`` must produce byte-identical output to
     ``agentbundle.config._emit_basic_string`` across the fixed attack corpus.

All tests call ``run_build_check_drift_gates`` in-process (not via
``subprocess.run(["make", "build-check"])`` — platform-decoupled discipline).
Tests that need derived artifacts run ``agentbundle build`` via subprocess to
populate the ``<workspace>/dist/`` tree, then call the gate function in-process
against ``<workspace>`` so the gate looks at ``<workspace>/dist/claude-plugins/``.

Spec: docs/specs/claude-plugins-install-route/spec.md (AC10 gate 2, AC20)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"
FIXTURES_PACKS = (
    Path(__file__).resolve().parents[2]
    / "agentbundle"
    / "build"
    / "tests"
    / "fixtures"
    / "packs"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_build_into_dist(packs_dir: Path, workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run ``agentbundle build --output-dir <workspace>/dist``.

    Puts derived artifacts at ``<workspace>/dist/claude-plugins/<pack>/...``
    so that ``run_build_check_drift_gates(workspace, packs_dir)`` can find them
    at ``<workspace>/dist/claude-plugins/<pack>/...``.
    """
    dist_dir = workspace / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle.build",
            "build",
            "--packs-dir",
            str(packs_dir),
            "--output-dir",
            str(dist_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def _make_minimal_pack(packs_dir: Path, pack_name: str = "alpha") -> Path:
    """Create a minimal fixture pack under ``packs_dir``."""
    pack_dir = packs_dir / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        f'[pack]\nname = "{pack_name}"\nversion = "0.1.0"\n'
        f'description = "Drift-gate test pack."\n'
        f'[pack.install]\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
    )
    plugin_dir = pack_dir / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {"name": pack_name, "version": "0.1.0", "description": "Drift-gate test."}
        ),
        encoding="utf-8",
    )
    return pack_dir


# ---------------------------------------------------------------------------
# Gate 1: Writer-template drift (AC20)
# ---------------------------------------------------------------------------


def test_make_build_check_fails_on_writer_drift(tmp_path):
    """AC20: gate exits non-zero when a derived install-marker.py diverges from the template.

    Sets up a tmp shadow packs dir, runs ``agentbundle build`` to populate
    ``<workspace>/dist/``, mutates one byte in a derived install-marker.py,
    calls ``run_build_check_drift_gates`` in-process, and asserts:
      - return code is non-zero; and
      - the diverged pack name appears in the failure messages printed to stderr.
    """
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    shutil.copytree(FIXTURES_PACKS, packs_shadow, symlinks=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    build_result = _run_build_into_dist(packs_shadow, workspace)
    assert build_result.returncode == 0, (
        f"build failed (setup for drift test):\n{build_result.stderr}"
    )

    # Locate all derived install-marker.py files under dist/claude-plugins/.
    dist_plugins = workspace / "dist" / "claude-plugins"
    assert dist_plugins.is_dir(), (
        f"dist/claude-plugins not found after build: {dist_plugins}"
    )

    mutated_pack = None
    for pack_dir in sorted(dist_plugins.iterdir()):
        if not pack_dir.is_dir():
            continue
        marker = pack_dir / ".claude-plugin" / "scripts" / "install-marker.py"
        if marker.exists():
            # Flip one byte — XOR the last byte so the hash changes.
            data = bytearray(marker.read_bytes())
            data[-1] ^= 0x01
            marker.write_bytes(bytes(data))
            mutated_pack = pack_dir.name
            break

    assert mutated_pack is not None, (
        "No derived install-marker.py found under dist/claude-plugins/; "
        "T4 derivation may not be running."
    )

    rc = run_build_check_drift_gates(workspace, packs_shadow)

    assert rc != 0, (
        "run_build_check_drift_gates should have returned non-zero on writer drift "
        "but returned 0."
    )


def test_make_build_check_passes_on_clean_tree(tmp_path):
    """AC20: gate exits zero when all derived install-marker.py files are byte-identical to the template.

    Runs ``agentbundle build`` against fixture packs into ``<workspace>/dist/``,
    then calls ``run_build_check_drift_gates`` in-process; expects 0.
    """
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    shutil.copytree(FIXTURES_PACKS, packs_shadow, symlinks=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    build_result = _run_build_into_dist(packs_shadow, workspace)
    assert build_result.returncode == 0, (
        f"build failed (setup for clean-tree check test):\n{build_result.stderr}"
    )

    rc = run_build_check_drift_gates(workspace, packs_shadow)

    assert rc == 0, (
        f"run_build_check_drift_gates should have returned 0 on a clean tree "
        f"but returned {rc}."
    )


# ---------------------------------------------------------------------------
# Gate 3: Vendored _emit_basic_string parity (AC20b)
# ---------------------------------------------------------------------------


def test_make_build_check_catches_emit_basic_string_drift(tmp_path, monkeypatch):
    """AC20b: gate exits non-zero when the template's _emit_basic_string diverges from source.

    Creates a copy of install-marker.py with the control-char escape branch
    removed from ``_emit_basic_string`` (so control chars are emitted verbatim
    rather than as ``\\uXXXX``), monkeypatches
    ``agentbundle.build.self_host._resolve_install_marker_template_path`` to
    return the mutated copy, calls ``run_build_check_drift_gates`` in-process,
    and asserts non-zero exit.
    """
    import agentbundle.build.self_host as self_host_mod
    from agentbundle.build.self_host import run_build_check_drift_gates

    original_text = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Neutralise the control-char escape branch inside _emit_basic_string so
    # control-char inputs are appended verbatim instead of as \\uXXXX.
    mutated_text = original_text.replace(
        "        elif ord(ch) < 0x20 or ord(ch) == 0x7F:\n"
        "            chunks.append(f\"\\\\u{ord(ch):04X}\")\n",
        "        elif False:  # drift: control-char refusal removed\n"
        "            chunks.append(f\"\\\\u{ord(ch):04X}\")\n",
    )
    assert mutated_text != original_text, (
        "Mutation did not change the template — check the literal being replaced."
    )

    mutated_path = tmp_path / "install-marker-mutated.py"
    mutated_path.write_text(mutated_text, encoding="utf-8")

    monkeypatch.setattr(
        self_host_mod,
        "_resolve_install_marker_template_path",
        lambda: mutated_path,
    )

    # No dist/ or source plugin.json files — only gate-3 (parity) exercises.
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()
    output_dir = tmp_path / "workspace"
    output_dir.mkdir()

    rc = run_build_check_drift_gates(output_dir, packs_dir)

    assert rc != 0, (
        "run_build_check_drift_gates should have returned non-zero on "
        "_emit_basic_string drift but returned 0."
    )


def test_make_build_check_passes_emit_basic_string_parity_on_clean(tmp_path):
    """AC20b: parity check passes against the unmodified install-marker.py template.

    Calls ``run_build_check_drift_gates`` in-process with:
      - an empty packs_dir (no source plugin.json → gate-2 silent), and
      - a workspace with no dist/ (no derived artifacts → gate-1 silent).
    Only gate-3 (parity) runs; expects 0.
    """
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()
    output_dir = tmp_path / "workspace"
    output_dir.mkdir()

    rc = run_build_check_drift_gates(output_dir, packs_dir)

    assert rc == 0, (
        f"_emit_basic_string parity check should pass on the unmodified template "
        f"but returned {rc}."
    )


# ---------------------------------------------------------------------------
# Gate 2: Source-shape plugin.json (AC10 gate 2)
# ---------------------------------------------------------------------------


def test_make_build_check_fails_on_source_hooks_block(tmp_path):
    """AC10 gate 2: gate exits non-zero when a source plugin.json carries a hooks block.

    Creates a tmp packs dir with a single pack whose plugin.json contains
    ``"hooks": {}``, calls ``run_build_check_drift_gates`` in-process, and asserts:
      - return code is non-zero; and
      - the pack name appears in the stderr output.
    """
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    pack_dir = _make_minimal_pack(packs_shadow, "alpha")

    # Inject a hooks block into the source plugin.json.
    plugin_json_path = pack_dir / ".claude-plugin" / "plugin.json"
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    manifest["hooks"] = {}
    plugin_json_path.write_text(json.dumps(manifest), encoding="utf-8")

    output_dir = tmp_path / "workspace"
    output_dir.mkdir()

    # Capture stderr by temporarily redirecting sys.stderr.
    import io
    captured = io.StringIO()
    import sys as _sys
    old_stderr = _sys.stderr
    _sys.stderr = captured
    try:
        rc = run_build_check_drift_gates(output_dir, packs_shadow)
    finally:
        _sys.stderr = old_stderr

    stderr_output = captured.getvalue()

    assert rc != 0, (
        f"run_build_check_drift_gates should have returned non-zero on source "
        f"hooks block but returned 0.\nstderr: {stderr_output}"
    )
    assert "alpha" in stderr_output, (
        f"stderr does not name the offending pack 'alpha'.\nstderr: {stderr_output}"
    )


def test_make_build_check_passes_on_clean_source_packs(tmp_path):
    """AC10 gate 2 + AC20a: gate exits zero on a clean source + populated dist tree.

    Shadow-copies the real ``packs/`` directory, builds into a shadow
    ``dist/`` (so the writer-template gate has projections to hash), and
    calls ``run_build_check_drift_gates`` in-process; expects 0.
    """
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    shutil.copytree(REPO_ROOT / "packs", packs_shadow, symlinks=True)

    output_dir = tmp_path / "workspace"
    output_dir.mkdir()
    _run_build_into_dist(packs_shadow, output_dir)

    # T6: adapter-root-bins/ projects to <output_dir>/.agentbundle/bin/.
    # In real `make build-check`, the working tree carries this from a
    # prior `make build-self`; for the fresh-workspace test fixture,
    # apply the projection here so the drift gate has a populated
    # target to compare against.
    from agentbundle.build.adapter_root_bins import (
        apply_projection as _adapter_root_bins_apply,
    )
    _adapter_root_bins_apply(output_dir, packs_shadow)

    rc = run_build_check_drift_gates(output_dir, packs_shadow)

    assert rc == 0, (
        f"run_build_check_drift_gates should have passed on clean source packs "
        f"+ populated dist tree but returned {rc}."
    )


# ---------------------------------------------------------------------------
# Gate 1c: APM writer-template drift (apm-install-route-parity AC16 a)
# ---------------------------------------------------------------------------


def test_make_build_check_fails_on_apm_writer_drift(tmp_path):
    """AC16 (a): gate exits non-zero when a derived APM install-marker.py
    diverges from the template.

    Mirror of the claude-plugins-side drift test, but mutates the APM-
    projected writer at dist/apm/<pack>/.apm/hooks/install-marker.py."""
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    shutil.copytree(FIXTURES_PACKS, packs_shadow, symlinks=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    build_result = _run_build_into_dist(packs_shadow, workspace)
    assert build_result.returncode == 0, (
        f"build failed (setup for APM drift test):\n{build_result.stderr}"
    )

    dist_apm = workspace / "dist" / "apm"
    assert dist_apm.is_dir(), f"dist/apm not found after build: {dist_apm}"

    mutated = None
    for pack_dir in sorted(dist_apm.iterdir()):
        if not pack_dir.is_dir():
            continue
        marker = pack_dir / ".apm" / "hooks" / "install-marker.py"
        if marker.exists():
            data = bytearray(marker.read_bytes())
            data[-1] ^= 0x01
            marker.write_bytes(bytes(data))
            mutated = pack_dir.name
            break

    assert mutated is not None, (
        "No APM-projected install-marker.py found under dist/apm/; T4 "
        "APM derivation may not be running."
    )

    rc = run_build_check_drift_gates(workspace, packs_shadow)
    assert rc != 0, (
        "run_build_check_drift_gates should have returned non-zero on APM-side "
        "writer drift but returned 0."
    )


def test_make_build_check_passes_on_clean_apm_tree(tmp_path):
    """AC16 (a) regression guard: gate exits zero when all APM-projected
    install-marker.py files are byte-identical to the template."""
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow = tmp_path / "packs"
    shutil.copytree(FIXTURES_PACKS, packs_shadow, symlinks=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    build_result = _run_build_into_dist(packs_shadow, workspace)
    assert build_result.returncode == 0, build_result.stderr

    rc = run_build_check_drift_gates(workspace, packs_shadow)
    assert rc == 0, f"clean tree should pass, got rc={rc}"


# ---------------------------------------------------------------------------
# Gate: user-libs projection drift (credbroker-user-scope T3)
# ---------------------------------------------------------------------------


def _shadow_real_tree_for_user_libs(tmp_path):
    """Shadow the real ``packs/`` + ``packages/credbroker`` so the user-libs
    gate's package source resolves via ``packs_shadow.parent``.

    Returns ``(packs_shadow, workspace)`` with ``dist/`` populated and both
    the adapter-root-bins and user-libs floors applied — a clean tree.
    """
    from agentbundle.build.adapter_root_bins import (
        apply_projection as _adapter_root_bins_apply,
    )
    from agentbundle.build.user_libs import apply_projection as _user_libs_apply

    packs_shadow = tmp_path / "packs"
    shutil.copytree(REPO_ROOT / "packs", packs_shadow, symlinks=True)
    # user_libs locates its source at <packs_shadow.parent>/packages/credbroker/...
    shutil.copytree(
        REPO_ROOT / "packages" / "credbroker",
        tmp_path / "packages" / "credbroker",
        symlinks=True,
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _run_build_into_dist(packs_shadow, workspace)
    _adapter_root_bins_apply(workspace, packs_shadow)
    _user_libs_apply(workspace, packs_shadow)
    return packs_shadow, workspace


def test_make_build_check_passes_on_clean_user_libs_tree(tmp_path):
    """T3: the gate exits zero when both vendored credbroker targets are
    byte-faithful to ``packages/credbroker/credbroker/``."""
    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow, workspace = _shadow_real_tree_for_user_libs(tmp_path)
    rc = run_build_check_drift_gates(workspace, packs_shadow)
    assert rc == 0, f"clean user-libs tree should pass, got rc={rc}"


def test_make_build_check_fails_on_user_libs_floor_drift(tmp_path):
    """T3: tampering a vendored floor file makes the gate exit non-zero and
    name the user-libs drift on stderr."""
    import io
    import sys as _sys

    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow, workspace = _shadow_real_tree_for_user_libs(tmp_path)

    floor_file = workspace / ".agentbundle" / "lib" / "credbroker" / "__init__.py"
    assert floor_file.is_file(), f"floor not applied at {floor_file}"
    data = bytearray(floor_file.read_bytes())
    data[-1] ^= 0x01
    floor_file.write_bytes(bytes(data))

    captured = io.StringIO()
    old_stderr = _sys.stderr
    _sys.stderr = captured
    try:
        rc = run_build_check_drift_gates(workspace, packs_shadow)
    finally:
        _sys.stderr = old_stderr

    stderr_output = captured.getvalue()
    assert rc != 0, f"gate should fail on floor drift.\nstderr: {stderr_output}"
    assert "user-libs" in stderr_output and "modified" in stderr_output, (
        f"stderr does not name the user-libs drift.\nstderr: {stderr_output}"
    )


def test_make_build_check_fails_on_user_libs_pack_copy_drift(tmp_path):
    """T3: tampering the pack-vendored copy (the catalogue-visible primitive)
    is also caught by the gate, and the message names the pack-copy target —
    not just the floor, so a regression that stops the pack-copy half of the
    two-target gate from contributing a message is caught."""
    import io
    import sys as _sys

    from agentbundle.build.self_host import run_build_check_drift_gates

    packs_shadow, workspace = _shadow_real_tree_for_user_libs(tmp_path)

    pack_file = (
        packs_shadow / "credential-brokers" / ".apm" / "user-libs"
        / "credbroker" / "__init__.py"
    )
    assert pack_file.is_file(), f"pack copy not applied at {pack_file}"
    data = bytearray(pack_file.read_bytes())
    data[-1] ^= 0x01
    pack_file.write_bytes(bytes(data))

    captured = io.StringIO()
    old_stderr = _sys.stderr
    _sys.stderr = captured
    try:
        rc = run_build_check_drift_gates(workspace, packs_shadow)
    finally:
        _sys.stderr = old_stderr

    stderr_output = captured.getvalue()
    assert rc != 0, f"gate should fail on pack-copy drift.\nstderr: {stderr_output}"
    assert (
        "user-libs" in stderr_output
        and "modified" in stderr_output
        and ".apm/user-libs/credbroker" in stderr_output
    ), f"stderr does not name the pack-copy drift target.\nstderr: {stderr_output}"
