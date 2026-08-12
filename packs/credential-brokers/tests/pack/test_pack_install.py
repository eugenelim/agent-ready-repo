"""Credential-brokers pack shape, installability, and delivered artifacts."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[2]
SETUP_SCRIPTS = PACK / ".apm" / "skills" / "credential-setup" / "scripts"


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


@pytest.fixture
def installed_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    home = tmp_path / "home"
    home.mkdir()
    output = tmp_path / "repo"
    output.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    catalogue = tmp_path / "catalogue"
    (catalogue / "packs").mkdir(parents=True)
    shutil.copytree(PACK, catalogue / "packs" / "credential-brokers")
    args = argparse.Namespace(
        pack="credential-brokers",
        catalogue=str(catalogue),
        output=str(output),
        scope="user",
        force=False,
        force_merge=False,
    )
    rc, stdout, stderr = _run_install(args)
    assert rc == 0, f"stdout={stdout!r} stderr={stderr!r}"
    return home, output


def test_manifest_shape() -> None:
    pack = tomllib.loads((PACK / "pack.toml").read_text(encoding="utf-8"))["pack"]
    assert pack["name"] == "credential-brokers"
    assert pack["version"] == "0.3.2"
    for subject in ("credbroker", "sso-broker", "credential-setup", "LLM-cooperative"):
        assert subject in pack["description"]
    assert pack["adapter-contract"]["version"] == "0.7"
    assert pack["install"]["default-scope"] == "user"
    assert pack["install"]["allowed-scopes"] == ["user", "repo"]
    assert pack["install"]["allowed-adapters"] == [
        "claude-code",
        "kiro-ide",
        "codex",
        "copilot",
        "cursor",
        "gemini",
    ]


def test_pack_directory_shape() -> None:
    assert (PACK / "pack.toml").is_file()
    assert {path.name for path in (PACK / ".apm").iterdir() if path.is_dir()} == {
        "shared-libs",
        "adapter-root-bins",
        "user-libs",
        "skills",
    }
    assert {
        path.name
        for path in (PACK / ".apm" / "skills").iterdir()
        if path.is_dir()
    } == {"credential-setup"}
    for forbidden in ("seeds", ".apm/hooks", ".apm/hook-wiring"):
        assert not (PACK / forbidden).exists()
    marker = re.compile(r"<adapt:[A-Z_]+>")
    for path in (PACK / ".apm").rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert marker.search(text) is None, path


def test_user_scope_install_succeeds(installed_pack: tuple[Path, Path]) -> None:
    home, _ = installed_pack
    assert (home / ".agentbundle").is_dir()


def test_floor_and_broker_artifacts_land(
    installed_pack: tuple[Path, Path],
) -> None:
    home, _ = installed_pack
    for name in ("__init__.py", "_core.py", "_vault.py"):
        assert (home / ".agentbundle" / "lib" / "credbroker" / name).is_file()
    for name in (
        "sso-broker.py",
        "credentials_shim.py",
        "_sso_keychain_macos.py",
        "_sso_credman_windows.py",
    ):
        assert (home / ".agentbundle" / "bin" / name).is_file()


def test_setup_resolves_credbroker_from_floor(
    installed_pack: tuple[Path, Path],
) -> None:
    home, _ = installed_pack
    entry = SETUP_SCRIPTS / "setup.py"
    if not entry.is_file():
        pytest.skip(f"{entry} not present in this checkout")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}
    }
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    result = subprocess.run(
        [sys.executable, "-S", "scripts/setup.py", "--help"],
        cwd=SETUP_SCRIPTS.parent,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
