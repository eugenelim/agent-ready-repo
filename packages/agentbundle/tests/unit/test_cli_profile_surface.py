"""T4 (pack-profiles AC10, AC11): CLI surface for profiles.

  - `--profile` and `--pack` are a required mutually-exclusive group: passing
    both, or neither, exits non-zero.
  - `--scope` combined with `--profile` is rejected at the handler.
  - `list-profiles <catalogue>` lists id + scope + description.
"""

from __future__ import annotations

import contextlib
import io

import pytest

from agentbundle import cli


def _run(argv):
    """Invoke cli.main, returning (exit_code, stdout, stderr).

    argparse errors raise SystemExit (code 2); handler returns are ints.
    """
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:  # argparse parse error
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()


def _catalogue(tmp_path):
    pdir = tmp_path / "profiles"
    pdir.mkdir()
    (pdir / "solution-architect.toml").write_text(
        'scope = "user"\ndescription = "Architect toolkit"\n'
        '[[packs]]\npack = "architect"\n[[packs]]\npack = "research"\n',
        encoding="utf-8",
    )
    (pdir / "full-ceremony.toml").write_text(
        'scope = "repo"\ndescription = "Full governance bundle"\n'
        '[[packs]]\npack = "core"\n',
        encoding="utf-8",
    )
    return tmp_path


def test_pack_and_profile_are_mutually_exclusive(tmp_path):
    code, _, err = _run(
        ["install", "--pack", "core", "--profile", "x", str(tmp_path)]
    )
    assert code == 2
    assert "not allowed with" in err or "mutually exclusive" in err.lower()


def test_neither_pack_nor_profile_is_rejected(tmp_path):
    code, _, err = _run(["install", str(tmp_path)])
    assert code == 2
    # argparse names the required group members.
    assert "--pack" in err and "--profile" in err


def test_scope_with_profile_is_rejected(tmp_path):
    code, _, err = _run(
        ["install", "--profile", "solution-architect", "--scope", "repo", str(tmp_path)]
    )
    assert code == 1
    assert "--scope is not allowed with --profile" in err


def test_list_profiles_lists_id_scope_description(tmp_path):
    cat = _catalogue(tmp_path)
    code, out, _ = _run(["list-profiles", str(cat)])
    assert code == 0
    assert "ID" in out and "SCOPE" in out and "DESCRIPTION" in out
    assert "solution-architect" in out and "user" in out and "Architect toolkit" in out
    assert "full-ceremony" in out and "repo" in out and "Full governance bundle" in out
    # id-sorted: full-ceremony before solution-architect.
    assert out.index("full-ceremony") < out.index("solution-architect")


def test_list_profiles_empty_catalogue_is_not_an_error(tmp_path):
    code, out, _ = _run(["list-profiles", str(tmp_path)])
    assert code == 0
    assert "ID" in out  # header still prints
