"""A layout failure never fails the install; a marker failure still does (AC11).

`_append_install_marker` and `_append_layout_section` sat in one `try` with a
single `except (OSError, PathJailError): return 1`. The layout append is
optional maintenance on a file the adopter owns, so a read-only layout file
would have aborted an install whose projected files were already on disk. The
marker is different — uninstall and `adapt` read what it writes, so an install
reporting success with no marker entry is worse than a failed install.

The call site is now two statements, and these two cases are what stop them
being re-merged: one relaxation covering both is green against either case
alone, and red against the pair.

Unit tests call `_append_layout_section` directly and structurally cannot see
an exit code or the projected tree, which is why this lives at integration
level.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

FIXTURE_CATALOGUE = Path(__file__).parent.parent / "fixtures" / "install" / "catalogue"


def _run_install(output: Path, catalogue: Path = FIXTURE_CATALOGUE) -> int:
    from agentbundle.commands.install import run

    return run(
        types.SimpleNamespace(
            pack="alpha",
            catalogue=str(catalogue),
            output=str(output),
            emit_install_routes=True,
        )
    )


def _projected(root: Path) -> set[str]:
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "agentbundle-layout.toml" not in p.name
    }


def _catalogue_declaring(tmp_path: Path, output_dir: str) -> Path:
    """A copy of the fixture catalogue whose pack declares a layout section."""
    import shutil

    catalogue = tmp_path / "catalogue"
    shutil.copytree(FIXTURE_CATALOGUE, catalogue)
    manifest = catalogue / "packs" / "alpha" / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + f'\n[pack.layout.repo]\nsection    = "design"\noutput_dir = "{output_dir}"\n',
        encoding="utf-8",
    )
    return catalogue


def test_a_reporting_layout_state_does_not_fail_the_install(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """A real reporting state, end to end through a real manifest.

    `output_dir` resolving outside the confinement root is one of the table's
    report rows. The install must complete with its files projected and the
    adopter's layout file untouched — the layout call sits outside the fatal
    handler precisely so this is true.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    layout = repo / "agentbundle-layout.toml"
    original = b'[research]\noutput_dir = "vault"\n'
    layout.write_bytes(original)

    code = _run_install(repo, _catalogue_declaring(tmp_path, "/etc"))

    assert code == 0, "a layout problem must not fail the install"
    assert _projected(repo), "the install must still have projected its files"
    assert layout.read_bytes() == original
    assert "outside" in capsys.readouterr().err


def test_a_declaring_pack_reaches_the_adopter_file_end_to_end(
    tmp_path: Path,
) -> None:
    """The positive half: the whole path, from manifest to adopter file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    layout = repo / "agentbundle-layout.toml"
    layout.write_bytes(b"# adopter notes\n")

    assert _run_install(repo, _catalogue_declaring(tmp_path, "docs/design")) == 0
    assert layout.read_bytes() == (
        b'# adopter notes\n[design]\noutput_dir = "docs/design"\n'
    )


def test_a_marker_failure_still_fails_the_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fatal half of the split verdict.

    Without this, widening the call site's `except` to cover both callers —
    the cheapest way to satisfy the case above — goes unnoticed.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    from agentbundle import safety
    from agentbundle.commands import install as install_mod

    def _boom(*_args, **_kwargs):
        raise safety.WriteError("simulated marker write failure")

    monkeypatch.setattr(install_mod, "_append_install_marker", _boom)

    assert _run_install(repo) == 1, (
        "a marker write failure must stay fatal: uninstall and adapt read it"
    )
