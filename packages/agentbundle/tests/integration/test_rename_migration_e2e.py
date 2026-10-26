"""The printed rename steps carry a real repository across the rename end to end.

Pre-rename and post-rename catalogues are built under ``tmp_path`` (nothing here
reads this repository's tree). The test installs ``governance-extras`` 1.0.3 and
``iac-terraform`` 0.1.12, runs ``upgrade --pack governance-extras`` against the
post-rename catalogue, parses the printed steps, and runs each through the CLI
with ``--yes`` and no ``--force``. Both catalogues also ship an edited-seed
target (``docs/adr/README.md``) so the run shows whether an adopter's edits
survive the uninstall and reinstall.
"""

from __future__ import annotations

import re
import shlex
import socket
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from agentbundle.cli import main

from tests._rename_fixtures import (
    DEP,
    NEW,
    OLD,
    post_rename_catalogue,
    pre_rename_catalogue,
)
from tests.integration._https_archive import ServedArchive, serve_archive

SEED = "docs/adr/README.md"
SEED_TEXT = "# ADRs\n\nShipped seed text.\n"
ADOPTER_TEXT = "# ADRs\n\nAdopter-customised text that must not be lost.\n"
MOVE = "move between catalogues"
NO_SOURCE = "no recorded source"
STEP = re.compile(r"^  (\d+)\. (.+)$")


@dataclass(frozen=True)
class Catalogues:
    pre: Path
    post: Path
    pre_archive: Path
    post_archive: Path


def _add_seed(catalogue: Path, pack: str) -> None:
    seed = catalogue / "packs" / pack / "seeds" / SEED
    seed.parent.mkdir(parents=True)
    seed.write_text(SEED_TEXT, encoding="utf-8")


def _package(catalogue: Path, out: Path) -> Path:
    code = main([
        "catalogue", "package", "--root", str(catalogue), "--bundle", "demo",
        "--release", "0.1.0", "--channel", "stable", "--output", str(out),
    ])
    assert code == 0
    return out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"


@pytest.fixture(scope="module")
def cats(tmp_path_factory: pytest.TempPathFactory) -> Catalogues:
    base = tmp_path_factory.mktemp("rename-e2e")
    pre = pre_rename_catalogue(base / "pre")
    post = post_rename_catalogue(base / "post")
    _add_seed(pre, OLD)
    _add_seed(post, NEW)
    return Catalogues(
        pre, post, _package(pre, base / "pre-out"), _package(post, base / "post-out")
    )


@pytest.fixture
def network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the run on loopback and away from any proxy."""
    real_connect = socket.socket.connect

    def connect(self: socket.socket, address: object) -> None:
        if isinstance(address, tuple) and address[0] == "127.0.0.1":
            return real_connect(self, address)  # type: ignore[arg-type]
        raise AssertionError(f"unexpected network connection to {address!r}")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    for var in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(var, raising=False)


def _install(repo: Path, source: str, pack: str) -> None:
    assert main([
        "install", "--pack", pack, "--scope", "repo", "--adapter", "claude-code",
        "--output", str(repo), "--yes", source,
    ]) == 0


def _strip_source(repo: Path, pack: str) -> None:
    path = repo / ".agentbundle-state.toml"
    out: list[str] = []
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        header = re.match(r"\[pack\.([^.\]]+)\.adapters\.[^.\]]+\]$", line)
        if header:
            current = header.group(1)
        elif line.startswith("["):
            current = None
        if current == pack and line.startswith("source = "):
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _installed(repo: Path) -> dict[str, str]:
    state = tomllib.loads((repo / ".agentbundle-state.toml").read_text(encoding="utf-8"))
    return {
        pack: row["installed-version"]
        for pack, body in state.get("pack", {}).items()
        for row in body.get("adapters", {}).values()
        if isinstance(row, dict) and "installed-version" in row
    }


def _run(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, str]:
    capsys.readouterr()
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _migrate(
    repo: Path, source: str, capsys: pytest.CaptureFixture[str]
) -> tuple[str, list[str]]:
    """Run the hint, then every printed step with ``--yes``; return the hint and the steps."""
    code, hint = _run(
        capsys,
        ["upgrade", "--pack", OLD, "--scope", "repo", "--root", str(repo), source],
    )
    assert code == 1
    steps = [m.group(2) for line in hint.splitlines() if (m := STEP.match(line))]
    assert [m.group(1) for line in hint.splitlines() if (m := STEP.match(line))] == [
        str(n) for n in range(1, len(steps) + 1)
    ]
    assert len(steps) == 3
    for step in steps:
        argv = shlex.split(step)
        assert argv[0] == "agentbundle"
        assert "--force" not in argv
        code, out = _run(capsys, [*argv[1:], "--yes"])
        assert code == 0, (step, out)
    return hint, steps


def _assert_end_state(repo: Path) -> None:
    versions = _installed(repo)
    assert versions.get(NEW) == "2.0.0"
    assert versions.get(DEP) == "0.2.0"
    assert OLD not in versions
    state = (repo / ".agentbundle-state.toml").read_text(encoding="utf-8")
    assert f"[pack.{OLD}" not in state


def _setup(repo: Path, cats: Catalogues) -> None:
    repo.mkdir()
    _install(repo, str(cats.pre), OLD)
    (repo / SEED).write_text(ADOPTER_TEXT, encoding="utf-8")


@pytest.fixture
def served_pre(cats: Catalogues, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
               network: None) -> Iterator[ServedArchive]:
    with serve_archive(cats.pre_archive, tmp_path / "pre-server") as served:
        monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(served.ca_bundle))
        yield served


def test_recorded_pre_rename_archive_migrates(cats, served_pre, tmp_path, capsys):
    """AC-0024, plus the edited-seed observation."""
    repo = tmp_path / "repo"
    _setup(repo, cats)
    _install(repo, served_pre.source, DEP)
    assert _installed(repo) == {OLD: "1.0.3", DEP: "0.1.12"}
    hint, _steps = _migrate(repo, str(cats.post), capsys)
    assert MOVE in hint
    assert served_pre.source.split("#")[0] in hint
    _assert_end_state(repo)
    assert (repo / SEED).read_text(encoding="utf-8") == ADOPTER_TEXT
    companion = repo / "docs/adr/README.upstream.md"
    assert companion.read_text(encoding="utf-8") == SEED_TEXT


def test_unrecorded_dependent_migrates(cats, tmp_path, network, capsys):
    """AC-0029."""
    repo = tmp_path / "repo"
    _setup(repo, cats)
    _install(repo, str(cats.pre), DEP)
    _strip_source(repo, DEP)
    hint, _steps = _migrate(repo, str(cats.post), capsys)
    assert NO_SOURCE in hint
    _assert_end_state(repo)


def test_archive_https_source_migrates(
    cats, tmp_path, monkeypatch, network, capsys
):
    """AC-0032."""
    repo = tmp_path / "repo"
    _setup(repo, cats)
    _install(repo, str(cats.pre), DEP)
    with serve_archive(cats.post_archive, tmp_path / "post-server") as served:
        monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(served.ca_bundle))
        hint, steps = _migrate(repo, served.source, capsys)
    assert "#sha256=" in served.source
    assert all(shlex.quote(served.source) in s for s in steps[1:])
    assert f"#sha256={served.sha256}" in hint
    _assert_end_state(repo)
