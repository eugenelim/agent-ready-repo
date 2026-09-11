"""Anchoring of a configured `output_dir` per scope (spec AC7).

`agentbundle-layout.toml` values are anchored by the layout file's own
location, never by the ambient working directory (RFC-0040 Decision 9).

Before this change `_read_scope` did `Path(raw).expanduser().resolve()`, which
anchors a relative value to the *process* working directory. The path was
reachable only through a hand-authored config; once the installer writes
repo-relative defaults it becomes the common case, so the bug ships activated.

The repo-scope case asserts from a working directory that is not the
repository root — a CWD-anchored implementation is green anywhere else.

The user-scope case asserts the stderr report rather than the absence of a
resolved path. `_read_scope` runs inside `contextlib.suppress(Exception)` and
its caller catches broadly, so an implementation that raises produces exactly
the byte-for-byte outcome of an unconfigured file; an absence-based assertion
would pass while the adopter's configured vault is silently ignored.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.workspace_mcp import _GitTools


def _reader(repo_root: Path) -> _GitTools:
    """`_read_layout_bases` lives on `_GitTools`, which owns the scope
    containment that consumes the resolved base."""
    return _GitTools(repo_root)


def _write_repo_layout(repo_root: Path, body: str) -> None:
    (repo_root / "agentbundle-layout.toml").write_text(body, encoding="utf-8")


def test_repo_scope_relative_anchors_to_the_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_layout(repo, '[design]\noutput_dir = "docs/design"\n')

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    # Keep the user-scope file out of the picture.
    monkeypatch.setenv("HOME", str(tmp_path / "nohome"))

    bases = _reader(repo)._read_layout_bases()

    assert bases["design"] == str((repo / "docs" / "design").resolve())
    assert not bases["design"].startswith(str(elsewhere.resolve())), (
        "a relative repo-scope value must not anchor to the process CWD"
    )


def test_repo_scope_absolute_is_left_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_repo_layout(repo, f'[design]\noutput_dir = "{vault}"\n')
    monkeypatch.setenv("HOME", str(tmp_path / "nohome"))

    assert _reader(repo)._read_layout_bases()["design"] == str(vault.resolve())


def test_user_scope_relative_is_reported_and_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
        '[research]\noutput_dir = "relative/vault"\n', encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    bases = _reader(repo)._read_layout_bases()

    assert "research" not in bases
    err = capsys.readouterr().err
    assert "relative/vault" in err, "the ignored value must be named"
    assert "research" in err, "the section must be named"
    assert "relative" in err


def test_user_scope_absolute_still_resolves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal must be scoped to relative values, not all user-scope ones."""
    repo = tmp_path / "repo"
    repo.mkdir()
    vault = tmp_path / "myvault"
    vault.mkdir()

    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
        f'[research]\noutput_dir = "{vault}"\n', encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    assert _reader(repo)._read_layout_bases()["research"] == str(vault.resolve())


def test_a_fix_anchoring_both_scopes_alike_fails_the_user_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The two halves of AC7 cannot be satisfied by one undifferentiated fix.

    Anchoring every relative value to the repository root passes the repo case
    above and must fail here, because the user-scope value would resolve
    instead of being reported.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
        '[research]\noutput_dir = "vault"\n', encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    bases = _reader(repo)._read_layout_bases()

    assert bases.get("research") != str((repo / "vault").resolve())
    assert "vault" in capsys.readouterr().err
