"""T5: install-gate enforcement for [pack.dependencies.required].

AC17: The install command reads [pack.dependencies.required] from the
installing pack's manifest and resolves each entry against the union of
repo-scope and user-scope state files. Missing or out-of-range required
packs cause a non-zero exit with spec-mandated stderr.

Six tests, TDD-first:
  1. test_install_refuses_missing_required
  2. test_install_proceeds_when_required_at_repo_scope
  3. test_install_proceeds_when_required_at_user_scope
  4. test_install_refuses_out_of_range_required
  5. test_install_refuses_unsupported_range_grammar
  6. test_install_no_required_table_proceeds
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORKTREE = Path(__file__).parent.parent.parent


def _stage_pack(catalogue_root: Path, pack_name: str, toml_text: str) -> Path:
    """Create a minimal pack under catalogue_root/packs/<pack_name>/."""
    pack = catalogue_root / "packs" / pack_name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(toml_text, encoding="utf-8")
    (pack / ".apm").mkdir()  # empty projection
    return pack


def _install(args_dict) -> tuple[int, str, str]:
    """Run install with redirected stdout/stderr; return (rc, stdout, stderr)."""
    from agentbundle.commands.install import run

    args = argparse.Namespace(**args_dict)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = run(args)
    return rc, out.getvalue(), err.getvalue()


def _pre_install_core(
    cat: Path,
    target: Path,
    version: str = "0.1.0",
    scope: str = "repo",
    *,
    monkeypatch=None,
    fake_home: Path | None = None,
) -> None:
    """Write `core` into the state file directly so tests don't need a real core pack."""
    from agentbundle.config import PackState, State, dump_state

    ps = PackState(installed_version=version, scope=scope)
    state = State()
    state.packs["core"] = ps

    if scope == "repo":
        state_path = target / ".agentbundle-state.toml"
        state_path.write_text(dump_state(state), encoding="utf-8")
    else:
        assert fake_home is not None, "fake_home required for user-scope pre-seed"
        user_dir = fake_home / ".agentbundle"
        user_dir.mkdir(parents=True, exist_ok=True)
        state_path = user_dir / "state.toml"
        state_path.write_text(dump_state(state), encoding="utf-8")


# ---------------------------------------------------------------------------
# Pack TOML templates
# ---------------------------------------------------------------------------

ADDON_WITH_REQUIRED = """\
[pack]
name = "addon"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "core"
version = "^0.1"
"""

ADDON_WITH_REQUIRED_UNSUPPORTED_RANGE = """\
[pack]
name = "addon"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "core"
version = "~0.1"
"""

ADDON_NO_DEPENDENCIES = """\
[pack]
name = "addon"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""

ADDON_BOTH_SCOPES = """\
[pack]
name = "addon"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "user"]

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "core"
version = "^0.1"
"""


# ---------------------------------------------------------------------------
# Test 1: refuse when required dep is missing from both state files
# ---------------------------------------------------------------------------


def test_install_refuses_missing_required(tmp_path):
    """Gate fires when required dep is absent from both repo and user state."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_WITH_REQUIRED)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc != 0, "install must refuse when required dep is missing"
    first_line = err.strip().splitlines()[0] if err.strip() else ""
    assert first_line == "install: pack 'addon' requires 'core' (version ^0.1); install core first", (
        f"unexpected stderr first line: {first_line!r}"
    )


# ---------------------------------------------------------------------------
# Test 2: proceed when required dep is present at repo scope
# ---------------------------------------------------------------------------


def test_install_proceeds_when_required_at_repo_scope(tmp_path):
    """Gate passes when required dep exists at repo scope (any version >=0.1.0)."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_WITH_REQUIRED)
    target = tmp_path / "repo"
    target.mkdir()

    # Pre-seed core at repo scope.
    _pre_install_core(cat, target, version="0.1.0", scope="repo")

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    # Gate must not fire — install may fail for other reasons (e.g. render),
    # but the gate-specific message must NOT appear.
    assert "requires 'core'" not in err, (
        f"gate fired unexpectedly; stderr: {err!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: proceed when required dep is present at user scope only
# ---------------------------------------------------------------------------


def test_install_proceeds_when_required_at_user_scope(tmp_path, monkeypatch):
    """Gate passes when required dep exists at user scope; repo scope is empty."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_BOTH_SCOPES)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Pre-seed core at user scope only; repo state is empty.
    _pre_install_core(
        cat, target, version="0.1.0", scope="user",
        monkeypatch=monkeypatch, fake_home=fake_home,
    )

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope="repo", force=False)
    )
    assert "requires 'core'" not in err, (
        f"gate fired unexpectedly on user-scope dep; stderr: {err!r}"
    )


def test_install_proceeds_when_required_at_user_scope_repo_only_addon(
    tmp_path, monkeypatch
):
    """Regression for adversarial-review Blocker 3: a repo-only addon
    (`allowed-scopes = ["repo"]`, no `"user"` in the set) installing
    while `core` lives only at user scope. The union rule must consult
    user_state even though the installing pack itself is repo-only —
    otherwise the gate refuses spuriously.
    """
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_WITH_REQUIRED)  # repo-only
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _pre_install_core(
        cat, target, version="0.1.0", scope="user",
        monkeypatch=monkeypatch, fake_home=fake_home,
    )

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert "requires 'core'" not in err, (
        f"repo-only addon gate fired spuriously when core is at user scope; stderr: {err!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: refuse when required dep is out of version range
# ---------------------------------------------------------------------------


def test_install_refuses_out_of_range_required(tmp_path):
    """Gate fires when installed dep version does not satisfy ^0.1 (0.0.5 < 0.1.0)."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_WITH_REQUIRED)
    target = tmp_path / "repo"
    target.mkdir()

    # core 0.0.5 does not satisfy ^0.1
    _pre_install_core(cat, target, version="0.0.5", scope="repo")

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc != 0, "install must refuse when required dep version is out of range"
    first_line = err.strip().splitlines()[0] if err.strip() else ""
    assert first_line == "install: pack 'addon' requires 'core' (version ^0.1); install core first", (
        f"unexpected stderr first line: {first_line!r}"
    )


# ---------------------------------------------------------------------------
# Test 5: refuse when version range grammar is unsupported
# ---------------------------------------------------------------------------


def test_install_refuses_unsupported_range_grammar(tmp_path):
    """Gate fires with the unsupported-range message when grammar is not ^X.Y."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_WITH_REQUIRED_UNSUPPORTED_RANGE)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc != 0, "install must refuse with unsupported range grammar"
    first_line = err.strip().splitlines()[0] if err.strip() else ""
    expected = "install: unsupported version range '~0.1' for required pack 'core'; only ^X.Y is supported"
    assert first_line == expected, f"unexpected stderr first line: {first_line!r}"


# ---------------------------------------------------------------------------
# Test 6: proceed when [pack.dependencies] table is absent
# ---------------------------------------------------------------------------


def test_install_no_required_table_proceeds(tmp_path):
    """Gate is silent when pack has no [pack.dependencies]; install proceeds."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_NO_DEPENDENCIES)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert "requires" not in err, (
        f"unexpected gate message when no required table: {err!r}"
    )
