"""Core session-start reader integration with the engine marker writer."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE_WRITER = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "templates"
    / "install-marker.py"
)
SESSION_START = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "session-start.py"


def test_apm_writer_output_is_readable_by_session_start(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    pack_root = repository / "apm_modules" / "core"
    hooks = pack_root / ".apm" / "hooks"
    hooks.mkdir(parents=True)
    writer = hooks / "install-marker.py"
    writer.write_bytes(SOURCE_WRITER.read_bytes())
    (pack_root / "pack.toml").write_text(
        textwrap.dedent(f"""
            [pack]
            name = {json.dumps("core")}
            version = "0.1.0"
            description = "Test pack."

            [pack.install]
            default-scope = "repo"
            allowed-scopes = ["repo"]
        """).lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        [sys.executable, str(writer), "--install-route", "apm"],
        cwd=repository,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PLUGIN_ROOT": str(pack_root),
            "HOME": str(home),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    marker = repository / ".adapt-install-marker.toml"
    spec = importlib.util.spec_from_file_location("_session_start", SESSION_START)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._pack_names_from_marker(marker) == ["core"]
