"""T9: Tests for `diff` subcommand.

Three scenarios:
  1. In sync — render core into tmpdir, run diff against that tmpdir; assert exit 0.
  2. Tampered — render then overwrite one file with adopter content; run diff;
     assert exit 1 and the tampered path appears in stdout.
  3. Missing — render then delete one file; run diff; assert exit 1 and the
     missing path appears in stdout.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from io import StringIO
import sys

from agentbundle import render
from agentbundle.commands import diff

# Resolve the repo root and core pack path relative to this file's location.
# Layout: packages/agentbundle/tests/unit/test_diff_cmd.py
# Repo root is four parents up.
REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"
CORE_PACK = PACKS_DIR / "core"


def _make_args(*, pack_path: str, root: str) -> SimpleNamespace:
    return SimpleNamespace(pack_path=pack_path, root=root)


def _project_pack_into(pack_path: Path, root: Path) -> dict[str, bytes]:
    """Render a pack in-memory and write every projected file to *root*."""
    rendered = render.render_pack(pack_path)
    for relpath, content in rendered.items():
        dest = root / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return rendered


# ---------------------------------------------------------------------------
# In sync: exit 0 when projection matches
# ---------------------------------------------------------------------------


def test_diff_in_sync(tmp_path, capsys):
    """render core into tmpdir, run diff; expect exit 0 and no drift output."""
    _project_pack_into(CORE_PACK, tmp_path)

    args = _make_args(pack_path=str(CORE_PACK), root=str(tmp_path))
    rc = diff.run(args)

    captured = capsys.readouterr()
    assert rc == 0, f"diff should exit 0 when in sync; stdout={captured.out!r}"
    assert captured.out.strip() == "", "diff should produce no output when in sync"


# ---------------------------------------------------------------------------
# Tampered: exit 1, drifted path in stdout
# ---------------------------------------------------------------------------


def test_diff_tampered(tmp_path, capsys):
    """Overwrite one rendered file with adopter content; diff must exit 1 and
    report the tampered path."""
    rendered = _project_pack_into(CORE_PACK, tmp_path)

    # Pick a deterministic file to tamper.
    tampered_relpath = sorted(rendered.keys())[0]
    tampered_file = tmp_path / tampered_relpath
    tampered_file.write_bytes(b"# adopter override\n")

    args = _make_args(pack_path=str(CORE_PACK), root=str(tmp_path))
    rc = diff.run(args)

    captured = capsys.readouterr()
    assert rc == 1, "diff should exit 1 when a file has been tampered with"
    assert tampered_relpath in captured.out, (
        f"tampered path {tampered_relpath!r} must appear in stdout; got {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Missing: exit 1, missing path in stdout
# ---------------------------------------------------------------------------


def test_diff_missing(tmp_path, capsys):
    """Delete one rendered file; diff must exit 1 and report the missing path."""
    rendered = _project_pack_into(CORE_PACK, tmp_path)

    # Pick a deterministic file to delete.
    missing_relpath = sorted(rendered.keys())[0]
    (tmp_path / missing_relpath).unlink()

    args = _make_args(pack_path=str(CORE_PACK), root=str(tmp_path))
    rc = diff.run(args)

    captured = capsys.readouterr()
    assert rc == 1, "diff should exit 1 when a file is missing"
    assert missing_relpath in captured.out, (
        f"missing path {missing_relpath!r} must appear in stdout; got {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Error path: missing pack.toml
# ---------------------------------------------------------------------------


def test_diff_missing_pack_toml(tmp_path, capsys):
    """diff against a directory without pack.toml should return non-zero."""
    empty_pack = tmp_path / "fakepak"
    empty_pack.mkdir()

    args = _make_args(pack_path=str(empty_pack), root=str(tmp_path))
    rc = diff.run(args)

    assert rc != 0, "expected non-zero exit when pack.toml is missing"
