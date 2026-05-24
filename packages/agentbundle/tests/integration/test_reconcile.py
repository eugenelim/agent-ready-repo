"""T9: `agentbundle reconcile --scope user` — read-only orphan reporter.

Covers spec AC26: walks both adapters' target files, reports
orphan-in-file (target claims own, state doesn't know) and
orphan-in-state (state claims own, file doesn't have), groups output
by adapter, and crucially **never writes**. The subcommand does not
register an ``--apply`` flag.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"


def _run_reconcile(scope: str = "user") -> tuple[int, str, str]:
    from agentbundle.commands import reconcile

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = reconcile.run(argparse.Namespace(scope=scope))
    return rc, stdout.getvalue(), stderr.getvalue()


def _run_install(args: argparse.Namespace) -> int:
    from agentbundle.commands import install

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return install.run(args)


def _install_args(pack: str, catalogue: str, output: str, scope: str = "user"):
    return argparse.Namespace(
        pack=pack, catalogue=catalogue, output=output,
        scope=scope, force=False, force_merge=False,
    )


def _copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)
    for entry in dst.rglob("*.sh"):
        entry.chmod(0o755)


class _ReconcileBase(unittest.TestCase):
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
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)


class CleanInstallReportsNoOrphansTests(_ReconcileBase):
    """AC26 empty case: a clean install produces an 'all clean' line."""

    def test_clean_install_reports_all_clean(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        rc = _run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo)
        ))
        self.assertEqual(rc, 0, "install failed")

        rc, stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertIn("all clean", stdout)

    def test_no_state_reports_all_clean(self) -> None:
        """An absent state file is the same as no installs — no orphans."""
        rc, stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertIn("all clean", stdout)


class OrphanInFileTests(_ReconcileBase):
    """AC26 type A: an id-tagged entry the file claims, that no
    installed pack owns. Surfaces under the adapter heading."""

    def test_synthetic_settings_entry_reported(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        rc = _run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo)
        ))
        self.assertEqual(rc, 0)

        settings = self.home / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        # Inject a synthetic id-tagged entry no pack owns.
        data["hooks"].setdefault("SessionStart", []).append(
            {"id": "ghost-pack:session", "command": "echo hi"}
        )
        settings.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )

        rc, stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertIn("claude-code", stdout)
        self.assertIn("orphan-in-file", stdout)
        self.assertIn("ghost-pack:session", stdout)
        self.assertIn("SessionStart", stdout)


class OrphanInStateTests(_ReconcileBase):
    """AC26 type B: state records ownership of an entry the target
    file doesn't have. Surfaces under the adapter heading."""

    def test_hand_deleted_entry_reported(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        rc = _run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo)
        ))
        self.assertEqual(rc, 0)

        settings = self.home / ".claude" / "settings.json"
        # Hand-delete the entry without uninstalling the pack.
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["hooks"]["UserPromptSubmit"] = []
        settings.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )

        rc, stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertIn("claude-code", stdout)
        self.assertIn("orphan-in-state", stdout)
        self.assertIn("cc-user-hooks:on-prompt", stdout)


class GroupedByAdapterTests(_ReconcileBase):
    """AC26: output is grouped by adapter."""

    def test_two_adapters_produce_separate_headings(self) -> None:
        # Install cc-user-hooks AND kiro-user-hooks, then inject one
        # orphan-in-file under each.
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")
        for pack in ("cc-user-hooks", "kiro-user-hooks"):
            rc = _run_install(_install_args(pack, str(self.cat), str(self.repo)))
            self.assertEqual(rc, 0, f"install of {pack} failed")

        # Inject orphans into each adapter's target file.
        settings = self.home / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["hooks"].setdefault("Other", []).append(
            {"id": "ghost-cc:x", "command": "x"}
        )
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        agent = json.loads(agent_json.read_text(encoding="utf-8"))
        agent["hooks"].setdefault("stop", []).append(
            {"id": "ghost-kiro:y", "command": "y"}
        )
        agent_json.write_text(
            json.dumps(agent, indent=2) + "\n", encoding="utf-8"
        )

        rc, stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertIn("reconcile: claude-code", stdout)
        self.assertIn("reconcile: kiro", stdout)
        self.assertIn("ghost-cc:x", stdout)
        self.assertIn("ghost-kiro:y", stdout)


class ReadOnlyContractTests(_ReconcileBase):
    """AC26 read-only invariant: target files are byte-identical
    before and after a reconcile run."""

    def test_reconcile_does_not_write(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        rc = _run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo)
        ))
        self.assertEqual(rc, 0)

        settings = self.home / ".claude" / "settings.json"
        before = settings.read_bytes()
        rc, _stdout, _err = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertEqual(settings.read_bytes(), before)


class ApplyFlagRejectedTests(unittest.TestCase):
    """AC26: `reconcile --apply` is rejected by argparse — the
    subcommand's parser does not register the flag."""

    def test_apply_flag_rejected_by_argparse(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "agentbundle", "reconcile", "--apply"],
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "agentbundle")},
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(proc.returncode, 0)
        # The default argparse "unrecognized argument" path fires.
        self.assertIn("unrecognized", proc.stderr.decode())


if __name__ == "__main__":
    unittest.main()
