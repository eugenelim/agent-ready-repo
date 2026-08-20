"""Process-level tests for the compile-okf CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from test_apply import _make_catalogue

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "compile-okf"
    / "scripts"
    / "compile_okf.py"
)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_cli_write_and_check_exit_codes_are_stable(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)

    drift = _run("--root", str(root), "--pack", "demo", "--check")
    write = _run("--root", str(root), "--pack", "demo")
    clean = _run("--root", str(root), "--pack", "demo", "--check")

    assert drift.returncode == 2
    assert "OKF011 packs/demo/.apm/skills/reviewed-runbook/SKILL.md" in drift.stderr
    assert drift.stdout == ""
    assert write.returncode == 0
    assert write.stdout == "OKF000 wrote packs/demo\n"
    assert write.stderr == ""
    assert clean.returncode == 0
    assert clean.stdout == "OKF000 check clean packs/demo\n"
    assert clean.stderr == ""


def test_cli_rejects_unknown_pack_with_stable_error(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)

    result = _run("--root", str(root), "--pack", "missing")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "OKF001 packs/missing pack not found\n"
