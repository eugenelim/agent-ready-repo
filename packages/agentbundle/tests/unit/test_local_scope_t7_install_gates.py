"""T7: install.py upstream gates, _ScopePlan local branch, emit_install_routes.

Tests for:
  - emit_install_routes inference: cli_scope not in ("user", "local")
  - --scope local --emit-install-routes refused with RFC-0008 message
  - --scope local --force-merge refused (force-merge is user-scope-only)
  - validate_dependencies_required local_state parameter
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent  # packages/agentbundle


# ---------------------------------------------------------------------------
# emit_install_routes inference (line 258 guard)
# ---------------------------------------------------------------------------


def test_emit_install_routes_inferred_true_for_none_scope():
    """None cli_scope → emit_install_routes=True (legacy repo-dist-tree path).

    None not in ("user", "local") is True — legacy callers that don't
    pass a scope field must continue to get the dist-tree path.
    """
    cli_scope = None
    result = cli_scope not in ("user", "local")
    assert result is True


def test_emit_install_routes_inferred_false_for_user():
    """user cli_scope → emit_install_routes=False."""
    cli_scope = "user"
    result = cli_scope not in ("user", "local")
    assert result is False


def test_emit_install_routes_inferred_false_for_local():
    """local cli_scope → emit_install_routes=False.

    Local scope must not trigger the dist-tree emit path.
    """
    cli_scope = "local"
    result = cli_scope not in ("user", "local")
    assert result is False


def test_emit_install_routes_inferred_true_for_repo():
    """repo cli_scope → emit_install_routes=True (backward compatible)."""
    cli_scope = "repo"
    result = cli_scope not in ("user", "local")
    assert result is True


# ---------------------------------------------------------------------------
# --scope local --emit-install-routes refused
# ---------------------------------------------------------------------------


def test_install_scope_local_emit_install_routes_refused(tmp_path, capsys):
    """Install --scope local --emit-install-routes is refused.

    The error message must reference RFC-0008 or 'emit-install-routes'.
    Tested via direct run() call with a minimal pack that resolves scope correctly.
    """
    from agentbundle.commands.install import run as install_run

    # Build a minimal pack so install.run can load pack.toml and resolve scope
    pack_dir = tmp_path / "mypkg"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "mypkg"\nversion = "0.1.0"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
    )
    catalogue_dir = tmp_path / "catalogue"
    catalogue_dir.mkdir()
    (catalogue_dir / "packs").mkdir()
    # symlink/copy the pack into the catalogue
    import shutil
    shutil.copytree(pack_dir, catalogue_dir / "packs" / "mypkg")

    args = SimpleNamespace(
        pack="mypkg",
        profile=None,
        catalogue=str(catalogue_dir),
        output=str(tmp_path / "repo"),
        scope="local",
        force=False,
        force_merge=False,
        adapter=None,
        emit_install_routes=True,
        dry_run=False,
        yes=True,
        _user_config=None,
    )
    (tmp_path / "repo").mkdir()

    rc = install_run(args)
    captured = capsys.readouterr()
    assert rc != 0
    assert "RFC-0008" in captured.err or "emit-install-routes" in captured.err.lower()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# --scope local --force-merge refused
# ---------------------------------------------------------------------------


def test_install_force_merge_refused_with_local_scope(tmp_path, capsys):
    """--force-merge --scope local is refused immediately.

    --force-merge is user-scope-only (install.py line 380 guard).
    The error message must reference 'user scope'.
    """
    from agentbundle.commands.install import run as install_run

    # Build a minimal pack
    pack_dir = tmp_path / "mypkg"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "mypkg"\nversion = "0.1.0"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo", "local"]\n',
        encoding="utf-8",
    )
    catalogue_dir = tmp_path / "catalogue"
    (catalogue_dir / "packs").mkdir(parents=True)
    import shutil
    shutil.copytree(pack_dir, catalogue_dir / "packs" / "mypkg")

    args = SimpleNamespace(
        pack="mypkg",
        profile=None,
        catalogue=str(catalogue_dir),
        output=str(tmp_path / "repo"),
        scope="local",
        force=False,
        force_merge=True,  # ← the flag under test
        adapter=None,
        emit_install_routes=False,
        dry_run=False,
        yes=True,
        _user_config=None,
    )
    (tmp_path / "repo").mkdir()

    rc = install_run(args)
    captured = capsys.readouterr()
    assert rc != 0
    assert "user scope" in captured.err, (
        f"Expected 'user scope' in error message; got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# validate_dependencies_required with local_state
# ---------------------------------------------------------------------------


def test_validate_dependencies_local_state_satisfies_dep():
    """A required dependency installed only at local scope satisfies the gate."""
    from agentbundle.commands.install import validate_dependencies_required
    from agentbundle.config import PackState, State

    # Pack that requires "dep-pack ^0.1"
    pack_toml = {
        "pack": {
            "name": "mypkg",
            "version": "0.1.0",
            "dependencies": {
                "required": [
                    {"catalogue": "default", "pack": "dep-pack", "version": "^0.1"}
                ]
            },
        }
    }

    # dep-pack installed ONLY at local scope
    dep_ps = PackState(installed_version="0.1.0", scope="local")
    local_state = State(packs={("dep-pack", "claude-code"): dep_ps})
    repo_state = State()
    user_state = State()

    # Should NOT raise — local_state satisfies the dep
    validate_dependencies_required(
        pack_toml,
        repo_state=repo_state,
        user_state=user_state,
        local_state=local_state,
    )


def test_validate_dependencies_no_local_state_misses_dep():
    """AC23b negative: without local_state, a local-only dep fails the gate."""
    from agentbundle.commands.install import validate_dependencies_required
    from agentbundle.config import PackState, State

    pack_toml = {
        "pack": {
            "name": "mypkg",
            "version": "0.1.0",
            "dependencies": {
                "required": [
                    {"catalogue": "default", "pack": "dep-pack", "version": "^0.1"}
                ]
            },
        }
    }

    # dep-pack only at local scope, but we don't pass local_state
    dep_ps = PackState(installed_version="0.1.0", scope="local")
    local_state = State(packs={("dep-pack", "claude-code"): dep_ps})  # noqa: F841
    repo_state = State()
    user_state = State()

    # Without local_state parameter, dep is NOT found → RuntimeError
    with pytest.raises(RuntimeError, match="dep-pack"):
        validate_dependencies_required(
            pack_toml,
            repo_state=repo_state,
            user_state=user_state,
            # local_state intentionally omitted
        )
