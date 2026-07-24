"""End-to-end cascade for `agentbundle config`.

Three integration tests cover AC15:
  - **(a)** subprocess flow exercising set/get/unset round-trip.
  - **(b)** in-process call to `_resolve_target_adapter` after a real
    file is written under the sandbox, asserting the resolver picks
    up the configured value.
  - **(c)** AST static check walking every `_resolve_target_adapter`
    call in install.py + upgrade.py — every call passes
    `user_config=` keyword; the total count equals 9.

The conftest fixture sandboxes HOME/XDG_CONFIG_HOME/APPDATA per test,
so each test's subprocess and in-process IO land under tmp_path.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import agentbundle


def _agentbundle(*args: str) -> subprocess.CompletedProcess:
    """Run `python -m agentbundle …` inheriting the test env (so the
    conftest fixture's HOME/XDG_CONFIG_HOME/APPDATA propagate)."""
    return subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        capture_output=True,
        text=True,
        env=os.environ,
    )


# ---------------------------------------------------------------------------
# AC15(a) — subprocess flow
# ---------------------------------------------------------------------------


def test_subprocess_cascade_round_trip() -> None:
    # `config path` exits 0 and prints something.
    proc = _agentbundle("config", "path")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip()  # non-empty

    # `config get adapter` on a clean sandbox reports the builtin.
    proc = _agentbundle("config", "get", "adapter")
    assert proc.returncode == 0
    assert proc.stdout.strip().endswith("(builtin)")
    assert "\tclaude-code\t" in proc.stdout

    # `config set adapter codex` succeeds.
    proc = _agentbundle("config", "set", "adapter", "codex")
    assert proc.returncode == 0, proc.stderr

    # `config get adapter` now reports the file value.
    proc = _agentbundle("config", "get", "adapter")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "adapter\tcodex\t(file)"

    # `config unset adapter` succeeds and deletes the file.
    proc = _agentbundle("config", "unset", "adapter")
    assert proc.returncode == 0, proc.stderr

    # `config get adapter` is back to the builtin.
    proc = _agentbundle("config", "get", "adapter")
    assert proc.returncode == 0
    assert proc.stdout.strip().endswith("(builtin)")
    assert "\tclaude-code\t" in proc.stdout


def test_subprocess_fail_soft_against_malformed_config() -> None:
    """A malformed config file must not break recovery commands. The
    loader fail-softs with a stderr warning and a (builtin) fallback,
    so the user can run `config path`, `config unset adapter`, or
    `config get` to recover. (`--help` is an even simpler case —
    argparse exits before the config is ever read.)"""
    from agentbundle.user_config import _user_config_path

    cfg_path = _user_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text('[settings]\nadapter = "unterminated\n')

    # `config path` works — main() unconditionally loads the config
    # before dispatch, but the loader is fail-soft (returns
    # UserConfig(adapter=None) and emits a warning) and the `path`
    # action doesn't consume the loaded value, so the malformed file
    # doesn't abort the CLI.
    proc = _agentbundle("config", "path")
    assert proc.returncode == 0, proc.stderr

    # `config get adapter` triggers the load (via main()'s
    # load_user_config), which fail-softs: warning to stderr,
    # builtin fallback reported on stdout, exit 0.
    proc = _agentbundle("config", "get", "adapter")
    assert proc.returncode == 0, proc.stderr
    assert str(cfg_path) in proc.stderr  # warning names the path
    assert proc.stdout.strip().endswith("(builtin)")


# ---------------------------------------------------------------------------
# AC15(b) — in-process resolver test
# ---------------------------------------------------------------------------


def test_in_process_resolver_honors_user_config(tmp_path: Path) -> None:
    from agentbundle.commands.install import _resolve_target_adapter
    from agentbundle.user_config import _user_config_path, load_user_config

    # Write a real config file under the sandbox.
    cfg_path = _user_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text('[settings]\nadapter = "codex"\n')

    loaded = load_user_config()
    assert loaded.adapter == "codex"

    # Minimal pack dir.
    pack = tmp_path / "demo-pack"
    (pack / ".apm").mkdir(parents=True)

    # Call the resolver directly with the loaded config. The pre-flight
    # returns "codex" before any Step 3+ logic runs.
    result = _resolve_target_adapter(
        pack,
        scope="user",
        adapter=None,
        allowed_adapters=None,
        contract_version=None,
        state_adapter=None,
        command_name="test",
        user_config=loaded,
    )
    assert result == "codex"


# ---------------------------------------------------------------------------
# AC15(c) — AST static check
# ---------------------------------------------------------------------------


def test_resolve_target_adapter_callers_thread_user_config() -> None:
    AGENTBUNDLE_DIR = Path(agentbundle.__file__).parent
    EXPECTED = 11  # 8 in install.py (2 added by pack-profiles _run_profile, 1 added by RFC-0052 multi-adapter path), 3 in upgrade.py (2 in run(), 1 in _preflight_render_and_jail for user-scope bulk upgrade)
    found = 0
    for src in [
        AGENTBUNDLE_DIR / "commands" / "install.py",
        AGENTBUNDLE_DIR / "commands" / "upgrade.py",
    ]:
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target: str | None = None
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target != "_resolve_target_adapter":
                continue
            found += 1
            kw_names = [kw.arg for kw in node.keywords]
            assert "user_config" in kw_names, (
                f"{src.name}:{node.lineno} calls _resolve_target_adapter "
                f"with keywords {kw_names}; missing 'user_config'"
            )
    assert found == EXPECTED, (
        f"expected {EXPECTED} _resolve_target_adapter call sites "
        f"across install.py + upgrade.py, found {found} — a call "
        f"site was added or removed without updating EXPECTED"
    )
