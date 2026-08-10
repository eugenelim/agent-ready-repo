"""Every subcommand that loads a pack manifest refuses on a
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
import os
from pathlib import Path
from unittest import mock

import pytest

# The version-gate fixtures are staged into a temp directory, never into the
# shipped tests/ tree. A committed symlink materialises platform-dependently in
# the sdist — dereferenced on Linux, dropped on macOS — which breaks the engine
# suite's completeness gate. `FIXTURE_PACK` is bound by the autouse fixture
# below before any test in this module runs.
FIXTURE_PACK: Path


@pytest.fixture(scope="module", autouse=True)
def stage_fixture_pack(tmp_path_factory):
    """Stage a pack whose [pack.adapter-contract] version major differs from ours."""
    global FIXTURE_PACK
    base = tmp_path_factory.mktemp("version_gate")
    FIXTURE_PACK = base / "incompatible_pack"
    FIXTURE_PACK.mkdir(parents=True)
    (FIXTURE_PACK / "pack.toml").write_text(
        """[pack]
name = "incompatible"
version = "0.1.0"

[pack.adapter-contract]
version = "99.0"
""",
        encoding="utf-8",
        newline="\n",
    )
    # Alias the pack into a packs/<name>/ layout for subcommands that take
    # --packs-dir. A *relative* symlink target keeps the fixture self-contained;
    # staging under a temp dir keeps it out of the shipped tree entirely.
    (base / "packs").mkdir()
    pack_link = base / "packs" / "incompatible"
    pack_link.symlink_to(
        os.path.relpath(FIXTURE_PACK, pack_link.parent), target_is_directory=True
    )
    yield


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
    """Assert the gate fired: exit 1, both versions named, canonical phrase.

    The canonical phrase ("refusing to operate on incompatible pack") pins
    that the refusal came from `_common.check_spec_version_gate`, not from
    some other rc=1 path that coincidentally contains a version string
    (Nit 8 from adversarial review).
    """
    assert rc == 1, f"expected exit 1, got {rc}"
    assert "99.0" in stderr, f"pack version not in stderr: {stderr!r}"
    assert "refusing to operate on incompatible pack" in stderr, (
        f"stderr is not the canonical gate refusal: {stderr!r}"
    )
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
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        catalogue=str(FIXTURE_PACK.parent),
        root=str(tmp_path),
    )
    _assert_refused(rc, stderr)
