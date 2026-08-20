from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from tools.repo import bootstrap


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        ("web", [("npm", "ci", "--prefix", "web")]),
        ("docs-site", [("npm", "ci", "--prefix", "docs-site")]),
        (
            "sites",
            [
                ("npm", "ci", "--prefix", "web"),
                ("npm", "ci", "--prefix", "docs-site"),
            ],
        ),
    ],
)
def test_profile_has_only_its_declared_npm_commands(
    profile: str, expected: list[tuple[str, ...]]
) -> None:
    assert list(bootstrap.profile_commands(profile)) == expected


def _fake_npm(bin_dir: Path) -> Path:
    if os.name == "nt":
        executable = bin_dir / "npm.cmd"
        executable.write_text(
            "@echo off\r\n"
            'echo ["%1","%2","%3"]>>"%NPM_TEST_LOG%"\r\n'
            "exit /b 0\r\n",
            encoding="utf-8",
        )
        return executable

    executable = bin_dir / "npm"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['NPM_TEST_LOG'], 'a', encoding='utf-8') as output:\n"
        "    output.write(json.dumps(sys.argv[1:]) + '\\n')\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        ("web", [["ci", "--prefix", "web"]]),
        ("docs-site", [["ci", "--prefix", "docs-site"]]),
        (
            "sites",
            [
                ["ci", "--prefix", "web"],
                ["ci", "--prefix", "docs-site"],
            ],
        ),
    ],
)
def test_bootstrap_executes_only_selected_profile_and_creates_no_venv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
    expected: list[list[str]],
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_npm(bin_dir)
    log = tmp_path / "npm-commands.jsonl"
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("NPM_TEST_LOG", str(log))

    result = bootstrap.bootstrap(profile, repo_root=tmp_path)

    assert result == 0
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    assert commands == expected
    assert not (tmp_path / ".venv").exists()
    assert not (tmp_path / "venv").exists()


def test_no_profile_errors_with_available_profiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    assert bootstrap.main([]) == 2

    error = capsys.readouterr().err
    assert "web, docs-site, sites" in error
    assert not (tmp_path / ".venv").exists()
    assert not (tmp_path / "venv").exists()


def test_missing_npm_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "")

    with pytest.raises(bootstrap.BootstrapError, match="npm was not found"):
        bootstrap.bootstrap("web", repo_root=tmp_path)

    assert not (tmp_path / "web" / "node_modules").exists()


def test_unknown_profile_is_actionable() -> None:
    with pytest.raises(bootstrap.BootstrapError, match="web, docs-site, sites"):
        bootstrap.profile_commands("all")


def test_docs_site_cannot_request_gate_browser(tmp_path: Path) -> None:
    with pytest.raises(bootstrap.BootstrapError, match="requires the web or sites"):
        bootstrap.bootstrap(
            "docs-site", repo_root=tmp_path, install_gate_browser=True
        )

    assert not (tmp_path / "docs-site" / "node_modules").exists()
