"""Claude plugin-hook compiler behavior and execution contract."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from agentbundle.build.projections.plugin_hooks import compile_plugin_hooks


def _fixture(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "capture.py").write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['CAPTURE']).write_text(json.dumps(sys.argv))\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "hook-wiring" / "a.toml").write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "command", command = "python3 tools/hooks/capture.py" }]\n',
        encoding="utf-8",
    )
    return pack


def _compile(pack: Path) -> dict:
    return compile_plugin_hooks(
        pack,
        repo_hook_prefix="tools/hooks/",
        plugin_hook_prefix="hooks/",
        hook_source_path=".apm/hooks/",
        wiring_source_path=".apm/hook-wiring/",
        pack_name=pack.name,
    )


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("sh") is None,
    reason="POSIX shell contract test",
)
def test_compiled_command_executes_with_literal_space_and_dollar_root(tmp_path: Path) -> None:
    pack = _fixture(tmp_path)
    command = _compile(pack)["SessionStart"][0]["hooks"][0]["command"]
    plugin_root = tmp_path / "plugin $ root"
    (plugin_root / "hooks").mkdir(parents=True)
    (plugin_root / "hooks" / "capture.py").write_bytes(
        (pack / ".apm" / "hooks" / "capture.py").read_bytes()
    )
    capture = tmp_path / "argv.json"
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_root), CAPTURE=str(capture))
    result = subprocess.run(["sh", "-c", command], env=env, check=False)
    assert result.returncode == 0
    assert json.loads(capture.read_text(encoding="utf-8")) == [
        str(plugin_root / "hooks" / "capture.py")
    ]


def test_filename_and_entry_order_is_stable(tmp_path: Path) -> None:
    pack = _fixture(tmp_path)
    (pack / ".apm" / "hook-wiring" / "b.toml").write_text(
        "[[hooks.UserPromptSubmit]]\n"
        'hooks = [{ type = "command", command = "python3 tools/hooks/capture.py", timeout = 9 }]\n',
        encoding="utf-8",
    )
    hooks = _compile(pack)
    assert list(hooks) == ["SessionStart", "UserPromptSubmit"]
    assert hooks["SessionStart"][0]["hooks"][0]["timeout"] == 60
    assert hooks["UserPromptSubmit"][0]["hooks"][0]["timeout"] == 9


def test_no_wiring_compiles_to_empty_block(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    assert _compile(pack) == {}
