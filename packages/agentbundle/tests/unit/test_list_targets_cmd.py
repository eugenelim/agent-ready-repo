"""Tests for `agentbundle list-targets` subcommand (T7).

Two tests per the plan:

1. Subprocess smoke-test — the real CLI entry-point exits 0 and prints all
   four adapter names.
2. Registry-not-baked-in test — monkeypatch `agentbundle.build.adapters.registry`
   with an extra fake module, call `run(args)` directly, assert the fake name
   appears in stdout.  Proves the command queries the runtime registry.
"""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from types import ModuleType
from typing import Mapping
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Subprocess smoke-test
# ---------------------------------------------------------------------------

def test_list_targets_subprocess_exit0_and_all_adapters(tmp_path):
    """Invoking `python -m agentbundle list-targets` exits 0 and lists all four
    canonical adapter names."""
    import subprocess
    import os

    pkg_root = str(
        (tmp_path.parent.parent / "packages" / "agentbundle").resolve()
        # Resolve path relative to the test file instead of tmp_path.
    )

    # The packages/ dir lives alongside tests/ under packages/agentbundle/
    import pathlib
    pkg_root = str(pathlib.Path(__file__).parent.parent.parent.resolve())

    env = {**os.environ, "PYTHONPATH": pkg_root}
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "list-targets"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"exit non-zero: {result.stderr}"

    output = result.stdout
    for name in ("claude_code", "codex", "copilot", "kiro"):
        assert name in output, f"'{name}' not found in output:\n{output}"


# ---------------------------------------------------------------------------
# Deterministic output test
# ---------------------------------------------------------------------------

def test_list_targets_deterministic(tmp_path):
    """Two consecutive subprocess runs produce identical stdout."""
    import subprocess
    import os
    import pathlib

    pkg_root = str(pathlib.Path(__file__).parent.parent.parent.resolve())
    env = {**os.environ, "PYTHONPATH": pkg_root}

    def run_once():
        return subprocess.run(
            [sys.executable, "-m", "agentbundle", "list-targets"],
            capture_output=True,
            text=True,
            env=env,
        ).stdout

    assert run_once() == run_once()


# ---------------------------------------------------------------------------
# Registry-not-baked-in test
# ---------------------------------------------------------------------------

def test_list_targets_reflects_runtime_registry(monkeypatch):
    """Monkeypatching the registry causes `run()` output to include the fake adapter."""
    import agentbundle.build.adapters as _adapters_mod
    import agentbundle.commands.list_targets as cmd_mod

    # Build a fake module to inject.
    fake_mod = ModuleType("fake_adapter")

    patched_registry: Mapping[str, ModuleType] = {
        **_adapters_mod.registry,
        "fake_adapter": fake_mod,
    }

    # Patch both the adapters module registry and re-import render's reference.
    monkeypatch.setattr(_adapters_mod, "registry", patched_registry)

    # Also patch agentbundle.render.list_adapters to pick up the change since
    # render.py caches the import at module-load time via `from ... import`.
    import agentbundle.render as render_mod
    original_list_adapters = render_mod.list_adapters

    def patched_list_adapters():
        return sorted(patched_registry.keys())

    monkeypatch.setattr(render_mod, "list_adapters", patched_list_adapters)

    # Call run(args) directly and capture stdout.
    args = argparse.Namespace()
    captured = StringIO()
    with patch("sys.stdout", captured):
        exit_code = cmd_mod.run(args)

    output = captured.getvalue()
    assert exit_code == 0
    assert "fake_adapter" in output, f"'fake_adapter' not in output:\n{output}"

    # All four real adapters should still be present.
    for name in ("claude_code", "codex", "copilot", "kiro"):
        assert name in output, f"'{name}' not found in output:\n{output}"
