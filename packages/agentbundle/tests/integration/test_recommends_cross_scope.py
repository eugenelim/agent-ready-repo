"""T20: `recommends` cross-scope warning text split.

Verifies AC #(RFC-0004) for the agent-spec-cli spec § *recommends
across scopes*. The five test rows cover:

  - Disjoint, recommended is repo-only (recommender at user scope).
  - Disjoint, recommended is user-only (recommender at repo scope).
  - Compatible-scope present (recommended already installed).
  - Missing entirely (recommended not installed anywhere).
  - Dual-scope --force install emits one warning per scope per recommend.

All warnings emit on stderr; stdout reserved for the `installed:` rail.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path

import pytest

from agentbundle.commands import install


PACK_A_REPO_RECS_B = """
[pack]
name = "alpha-rec"
version = "0.1.0"
recommends = ["beta-rec"]

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""

PACK_A_DUAL_RECS_B = """
[pack]
name = "alpha-rec"
version = "0.1.0"
recommends = ["beta-rec"]

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "user"]
"""

PACK_A_USER_RECS_B = """
[pack]
name = "alpha-rec"
version = "0.1.0"
recommends = ["beta-rec"]

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
"""

PACK_B_REPO_ONLY = """
[pack]
name = "beta-rec"
version = "0.1.0"

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""

PACK_B_USER_ONLY = """
[pack]
name = "beta-rec"
version = "0.1.0"

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
"""


def _stage_pack(catalogue_root: Path, name: str, toml: str) -> Path:
    pack = catalogue_root / "packs" / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(toml, encoding="utf-8")
    (pack / ".apm").mkdir()
    return pack


def _run(args_dict) -> tuple[int, str, str]:
    # Set emit_install_routes=False explicitly so the per-IDE projection
    # path is used (not the dist-tree legacy path), consistent with what
    # the real argparse parser default produces.
    d = {"emit_install_routes": False, **args_dict}
    args = argparse.Namespace(**d)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def test_disjoint_recommended_is_repo_only(tmp_path, monkeypatch):
    """Recommender at user scope, recommended is repo-only → disjoint warning."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha-rec", PACK_A_USER_RECS_B)
    _stage_pack(cat, "beta-rec", PACK_B_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc, _out, err = _run(
        dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope="user", force=False)
    )
    assert rc == 0
    assert (
        "note: recommends 'beta-rec', which is repo-only; install it in your active project"
        in err
    )


def test_disjoint_recommended_is_user_only(tmp_path, monkeypatch):
    """Recommender at repo scope, recommended is user-only → mirror warning."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha-rec", PACK_A_REPO_RECS_B)
    _stage_pack(cat, "beta-rec", PACK_B_USER_ONLY)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc, _out, err = _run(
        dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope="repo", force=False)
    )
    assert rc == 0
    assert (
        "note: recommends 'beta-rec', which is user-only; install it at user scope"
        in err
    )


def test_compatible_present_at_recommended_scope(tmp_path):
    """When the recommended pack is installed at any compatible scope,
    the warning names the observed scope."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha-rec", PACK_A_REPO_RECS_B)
    _stage_pack(cat, "beta-rec", PACK_B_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()

    # Install B first.
    _run(dict(pack="beta-rec", catalogue=str(cat), output=str(target), scope=None, force=False))
    # Now install A — should see B at repo.
    rc, _out, err = _run(
        dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0
    assert "note: recommends 'beta-rec' (found at repo scope)" in err


def test_missing_entirely(tmp_path):
    """When the recommended pack is not installed, warning is `(not installed)`."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha-rec", PACK_A_REPO_RECS_B)
    _stage_pack(cat, "beta-rec", PACK_B_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _out, err = _run(
        dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0
    assert "note: recommends 'beta-rec' (not installed)" in err


def test_dual_scope_force_emits_one_warning_per_scope(tmp_path, monkeypatch):
    """A `--force` dual-scope install emits one warning per scope per recommend."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha-rec", PACK_A_DUAL_RECS_B)
    _stage_pack(cat, "beta-rec", PACK_B_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Install A at repo first.
    _run(dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope="repo", force=False))
    # Now install A at user with --force — emits warnings for both scopes.
    rc, _out, err = _run(
        dict(pack="alpha-rec", catalogue=str(cat), output=str(target), scope="user", force=True)
    )
    assert rc == 0
    # Two stderr lines per recommend per scope. The repo-line warning
    # is `(not installed)`; the user-scope plan emits the disjoint
    # warning because B is repo-only.
    assert "note: recommends 'beta-rec' (not installed)" in err
    assert (
        "note: recommends 'beta-rec', which is repo-only; install it in your active project"
        in err
    )
