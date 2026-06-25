"""The tests/fixtures fixture-overwrite guard lives in the CLI handler.

`build-self` overwrites the working tree; pointing `--packs-dir` into
`tests/fixtures/` would overwrite it with fixture data. That guard used to live
only in the Makefile, so the make-free `python -m agentbundle.build self` entry
(the only one available on Windows) bypassed it. It now lives in `cmd_self` via
`_refuse_fixture_packs_dir`, honouring the same `ALLOW_FIXTURE_PACKS` override.
"""

from __future__ import annotations

import argparse
import os
import unittest
from pathlib import Path
from unittest import mock

import agentbundle.build.self_host as sh
from agentbundle.build.self_host import _refuse_fixture_packs_dir

_FIXTURE_DIR = Path("/repo/packages/agentbundle/tests/fixtures/packs")
_REAL_DIR = Path("/repo/packs")

# Empty string is falsy, so this simulates "unset" for the guard regardless of
# the ambient environment; "1" simulates the override being set.
_ENV_UNSET = {"ALLOW_FIXTURE_PACKS": ""}
_ENV_SET = {"ALLOW_FIXTURE_PACKS": "1"}


class RefuseFixturePacksDirTest(unittest.TestCase):
    def test_real_write_into_fixtures_refuses(self):
        with mock.patch.dict(os.environ, _ENV_UNSET):
            rc = _refuse_fixture_packs_dir(_FIXTURE_DIR, dry_run=False)
        self.assertEqual(rc, 2)

    def test_env_override_proceeds(self):
        with mock.patch.dict(os.environ, _ENV_SET):
            rc = _refuse_fixture_packs_dir(_FIXTURE_DIR, dry_run=False)
        self.assertIsNone(rc)

    def test_dry_run_is_never_guarded(self):
        with mock.patch.dict(os.environ, _ENV_UNSET):
            rc = _refuse_fixture_packs_dir(_FIXTURE_DIR, dry_run=True)
        self.assertIsNone(rc)

    def test_non_fixtures_dir_proceeds(self):
        with mock.patch.dict(os.environ, _ENV_UNSET):
            rc = _refuse_fixture_packs_dir(_REAL_DIR, dry_run=False)
        self.assertIsNone(rc)


class CmdSelfGuardWiringTest(unittest.TestCase):
    def test_cmd_self_refuses_and_does_not_run(self):
        args = argparse.Namespace(
            output_dir=".",
            packs_dir=str(_FIXTURE_DIR),
            dry_run=False,
            force=False,
            no_symlink=False,
        )
        with mock.patch.dict(os.environ, _ENV_UNSET), mock.patch.object(
            sh, "run_self_host"
        ) as run:
            rc = sh.cmd_self(args)
        self.assertEqual(rc, 2)
        run.assert_not_called()

    def test_cmd_self_refuses_relative_fixtures_path(self):
        # cmd_self resolves the packs-dir first; a *relative* tests/fixtures
        # path must still match after resolve() + as_posix() (the real input
        # shape, which the pure-helper tests above bypass).
        args = argparse.Namespace(
            output_dir=".",
            packs_dir="agentbundle/build/tests/fixtures/packs",
            dry_run=False,
            force=False,
            no_symlink=False,
        )
        with mock.patch.dict(os.environ, _ENV_UNSET), mock.patch.object(
            sh, "run_self_host"
        ) as run:
            rc = sh.cmd_self(args)
        self.assertEqual(rc, 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
