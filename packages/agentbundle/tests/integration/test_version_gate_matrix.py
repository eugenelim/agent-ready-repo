"""AC #14: every subcommand that loads a pack manifest refuses on a
major-version mismatch with a stderr line naming both versions.

This is the cross-cutting proof that the version gate is uniform — no
subcommand silently proceeds against an incompatible pack.

Subcommands tested: scaffold, install, render, validate, diff,
upgrade, init-state, list-packs. (`list-targets`, `uninstall`, and
`adapt` don't load a pack.toml — they work off the install state file
or the runtime registry — and are exempt by design.)
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from unittest import mock

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PACK = PACKAGE_ROOT / "tests" / "fixtures" / "version_gate" / "incompatible_pack"


@pytest.fixture(scope="module", autouse=True)
def stage_fixture_pack():
    """Stage a pack whose [pack.adapter-contract] version major differs from ours."""
    FIXTURE_PACK.mkdir(parents=True, exist_ok=True)
    (FIXTURE_PACK / "pack.toml").write_text(
        """[pack]
name = "incompatible"
version = "0.1.0"

[pack.adapter-contract]
version = "99.0"
""",
        encoding="utf-8",
    )
    (FIXTURE_PACK.parent / "packs").mkdir(parents=True, exist_ok=True)
    # Symlink into a packs/<name>/ layout for subcommands that take --packs-dir.
    pack_link = FIXTURE_PACK.parent / "packs" / "incompatible"
    if not pack_link.exists():
        pack_link.symlink_to(FIXTURE_PACK, target_is_directory=True)
    yield
    # Don't tear down — left in place for inspection if a test fails.


def _run(module_name: str, **kwargs) -> tuple[int, str]:
    """Run a command module's `run()` with mocked stderr and return (rc, stderr_text)."""
    import importlib

    mod = importlib.import_module(f"agentbundle.commands.{module_name}")
    captured = io.StringIO()
    args = argparse.Namespace(**kwargs)
    with mock.patch("sys.stderr", captured):
        rc = mod.run(args)
    return rc, captured.getvalue()


def _assert_refused(rc: int, stderr: str):
    """Assert the gate fired: exit 1, both versions named."""
    assert rc == 1, f"expected exit 1, got {rc}"
    assert "99.0" in stderr, f"pack version not in stderr: {stderr!r}"
    # CLI's spec version is parsed from adapter.toml at import time;
    # its major matches the bundle's, so the message names it.
    from agentbundle.version import SPEC_VERSION
    assert SPEC_VERSION in stderr, f"CLI spec version not in stderr: {stderr!r}"


def test_validate_refuses_incompatible(tmp_path):
    rc, stderr = _run("validate", pack_path=str(FIXTURE_PACK), strict=False)
    _assert_refused(rc, stderr)


def test_scaffold_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "scaffold",
        pack="incompatible",
        packs_dir=str(FIXTURE_PACK.parent / "packs"),
        output=str(tmp_path),
    )
    _assert_refused(rc, stderr)


def test_render_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "render",
        pack_path=str(FIXTURE_PACK),
        output=str(tmp_path),
        target=None,
    )
    _assert_refused(rc, stderr)


def test_diff_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "diff",
        pack_path=str(FIXTURE_PACK),
        root=str(tmp_path),
    )
    _assert_refused(rc, stderr)


def test_init_state_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "init_state",
        pack="incompatible",
        packs_dir=str(FIXTURE_PACK.parent / "packs"),
        root=str(tmp_path),
    )
    _assert_refused(rc, stderr)


def test_install_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "install",
        pack="incompatible",
        catalogue=str(FIXTURE_PACK.parent),
        output=str(tmp_path),
    )
    _assert_refused(rc, stderr)


def test_list_packs_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "list_packs",
        catalogue=str(FIXTURE_PACK.parent),
    )
    _assert_refused(rc, stderr)


def test_upgrade_refuses_incompatible(tmp_path):
    rc, stderr = _run(
        "upgrade",
        pack="incompatible",
        to_version="0.2",
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        catalogue=str(FIXTURE_PACK.parent),
        root=str(tmp_path),
    )
    _assert_refused(rc, stderr)
