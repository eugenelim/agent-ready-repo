"""AC6a: install --scope user against the converters pack writes the
state-file row, lands the three projected skill directories under
~/.claude/skills/, and uninstall reverses both effects.

The reference idiom is test_install_user_hooks.py:_UserScopeInstallBase
(in-process install.run, $HOME redirected via patch.dict). Install
takes --pack + positional catalogue + --output + --scope; uninstall
takes --pack + --root + --scope (different field name — root, not
output).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
CONVERTERS_PACK_SRC = REPO_ROOT / "packs" / "converters"
SKILL_NAMES = ("file-to-markdown", "markdown-to-html", "msg-to-markdown")


def _run_install(args: argparse.Namespace) -> tuple[int, str]:
    from agentbundle.commands import install

    stderr = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stderr.getvalue()


def _run_uninstall(args: argparse.Namespace) -> tuple[int, str]:
    from agentbundle.commands import uninstall

    stderr = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
        rc = uninstall.run(args)
    return rc, stderr.getvalue()


class ConvertersUserScopeInstallTests(unittest.TestCase):
    """End-to-end install/uninstall round-trip for the converters pack
    at user scope. Mirrors _UserScopeInstallBase from
    test_install_user_hooks.py: $HOME is redirected to a tmp path so
    the test never touches the developer's real home tree."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(os.environ, {"HOME": str(self.home)})
        self._env.start()
        self.addCleanup(self._env.stop)
        # Temporary catalogue layout: <cat>/packs/converters/ — populated
        # from the repo-local pack via copytree.
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")

    def test_install_then_uninstall_round_trip(self) -> None:
        install_args = argparse.Namespace(
            pack="converters",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
            force=False,
            force_merge=False,
        )
        rc, stderr = _run_install(install_args)
        self.assertEqual(rc, 0, f"install failed: {stderr}")

        # HOME-resolution guard: if $HOME didn't propagate into the CLI's
        # Path.home() (e.g. cached at import time), the state directory
        # lands at the developer's real home and the next assertion fires
        # with a clear message instead of a confusing AttributeError.
        agent_ready_dir = self.home / ".agent-ready"
        self.assertTrue(
            agent_ready_dir.exists(),
            f"~/.agent-ready/ absent under tmp $HOME {self.home}; "
            f"check $HOME propagation",
        )

        from agentbundle.config import STATE_SCHEMA_VERSION, load_state

        state = load_state(agent_ready_dir / "state.toml")
        # Pin against the constant rather than a literal: the spec records
        # the runtime version in plain English, but the contract the
        # install path actually writes is whatever the package exports.
        self.assertEqual(state.schema_version, STATE_SCHEMA_VERSION)
        self.assertIn("converters", state.packs)
        self.assertEqual(state.packs["converters"].scope, "user")

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertTrue(
                skill_dir.is_dir(),
                f"expected projected skill directory at {skill_dir}",
            )

        uninstall_args = argparse.Namespace(
            pack="converters",
            root=str(self.repo),
            scope="user",
        )
        rc, stderr = _run_uninstall(uninstall_args)
        self.assertEqual(rc, 0, f"uninstall failed: {stderr}")

        for name in SKILL_NAMES:
            skill_dir = self.home / ".claude" / "skills" / name
            self.assertFalse(
                skill_dir.exists(),
                f"projected skill directory at {skill_dir} survived uninstall",
            )

        state_path = agent_ready_dir / "state.toml"
        if state_path.exists():
            state_after = load_state(state_path)
            self.assertNotIn(
                "converters",
                state_after.packs,
                "converters entry survived uninstall in state.toml",
            )
