"""T7 tests for the install-time message rail (RFC-0011 / AC14, AC15).

The two new behaviours:

  - `installed: <pack> @ user via <adapter>` line (was `@ user`).
  - The `(other declared adapters: …)` suffix when multiple of the
    pack's allowed-adapters' CLI homes are populated AND `--adapter`
    was not passed.

These tests drive `install.run` in-process with `$HOME` patched, then
capture stdout/stderr to assert on the *actual* output of the
production code (not in-test f-strings). Symmetric with
`test_install_user_scope_allowed_adapters.py` but kept in `tests/unit/`
because they target message-rail behaviour specifically, not the
full install-and-uninstall round-trip.
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


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


class InstallMessageRailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")

    def _install(self, *, scope: str, adapter: str | None = None) -> tuple[int, str, str]:
        return _run_install(
            argparse.Namespace(
                pack="converters",
                catalogue=str(self.cat),
                output=str(self.repo),
                scope=scope,
                force=False,
                force_merge=False,
                adapter=adapter,
            )
        )

    def test_user_scope_install_emits_via_clause(self) -> None:
        """AC14: user-scope install stdout contains `via <adapter>`."""
        (self.home / ".kiro").mkdir()
        rc, stdout, _ = self._install(scope="user")
        self.assertEqual(rc, 0)
        self.assertIn("installed: converters @ user via kiro-ide", stdout)

    def test_user_scope_install_no_suffix_when_single_home_populated(self) -> None:
        """AC14: no suffix when only one CLI home matches."""
        (self.home / ".claude").mkdir()
        rc, stdout, _ = self._install(scope="user")
        self.assertEqual(rc, 0)
        self.assertIn("installed: converters @ user via claude-code", stdout)
        self.assertNotIn("other declared adapters", stdout)

    def test_user_scope_install_suffix_when_multiple_homes_populated(self) -> None:
        """AC14: suffix lists the other matching adapters when more
        than one CLI home is populated and `--adapter` was not passed."""
        (self.home / ".claude").mkdir()
        (self.home / ".kiro").mkdir()
        rc, stdout, _ = self._install(scope="user")
        self.assertEqual(rc, 0)
        # claude-code wins (declared first); the suffix should list kiro-ide.
        self.assertIn("installed: converters @ user via claude-code", stdout)
        self.assertIn(
            "(other declared adapters: kiro-ide; use --adapter to override)",
            stdout,
        )

    def test_user_scope_install_no_suffix_with_explicit_adapter(self) -> None:
        """AC14: suffix omitted when `--adapter` was passed (the adopter
        already chose)."""
        (self.home / ".claude").mkdir()
        (self.home / ".kiro").mkdir()
        rc, stdout, _ = self._install(scope="user", adapter="kiro-ide")
        self.assertEqual(rc, 0)
        self.assertIn("installed: converters @ user via kiro-ide", stdout)
        self.assertNotIn("other declared adapters", stdout)

    def test_greenfield_user_scope_install_no_suffix(self) -> None:
        """Greenfield $HOME (no CLI home populated): the populated-set
        intersection is empty, so the suffix doesn't render."""
        rc, stdout, _ = self._install(scope="user")
        self.assertEqual(rc, 0)
        self.assertIn("installed: converters @ user via claude-code", stdout)
        self.assertNotIn("other declared adapters", stdout)


if __name__ == "__main__":
    unittest.main()
