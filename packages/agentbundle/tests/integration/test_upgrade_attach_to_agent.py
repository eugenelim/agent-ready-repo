"""T8c: upgrade reconciliation for `attach-to-agent` rename (Kiro).

Per spec AC19b: upgrading a Kiro pack whose `attach-to-agent` value
changes between versions (agent renamed, removed, or added) walks
the OLD `target-file` to remove orphan entries AND the NEW
`target-file` to add the new entries; state's `target-file` is
updated to the new value; `reconcile --scope user` reports no
orphans after the upgrade.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"


def _run_install(args):
    from agentbundle.commands import install
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return install.run(args)


def _run_upgrade(args):
    from agentbundle.commands import upgrade
    stderr = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
        rc = upgrade.run(args)
    return rc, stderr.getvalue()


def _run_reconcile():
    from agentbundle.commands import reconcile
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
        rc = reconcile.run(argparse.Namespace(scope="user"))
    return rc, stdout.getvalue()


def _copy_fixture(src, dst):
    shutil.copytree(src, dst)
    for entry in dst.rglob("*.sh"):
        entry.chmod(0o755)


class AttachToAgentRenameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"; self.home.mkdir()
        self.repo = self.tmp / "repo"; self.repo.mkdir()
        self._env = patch.dict(os.environ, {"HOME": str(self.home)})
        self._env.start()
        self.addCleanup(self._env.stop)
        self.cat = self.tmp / "cat"; (self.cat / "packs").mkdir(parents=True)

    def test_upgrade_renames_attach_to_agent(self):
        # Install kiro-user-hooks (attach-to-agent = "reviewer").
        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")
        self.assertEqual(_run_install(argparse.Namespace(
            pack="kiro-user-hooks", catalogue=str(self.cat), output=str(self.repo),
            scope="user", force=False, force_merge=False,
        )), 0)

        old_agent = self.home / ".kiro" / "agents" / "reviewer.json"
        self.assertTrue(old_agent.exists())
        before = json.loads(old_agent.read_text(encoding="utf-8"))
        self.assertIn("agentSpawn", before["hooks"])

        # Mutate catalogue: rename the agent + update the wiring's
        # attach-to-agent. (Pack-author rename.)
        pack_in_cat = self.cat / "packs" / "kiro-user-hooks"
        (pack_in_cat / ".apm" / "agents" / "reviewer.md").rename(
            pack_in_cat / ".apm" / "agents" / "code-reviewer.md"
        )
        wiring = pack_in_cat / ".apm" / "hook-wiring" / "on-spawn.toml"
        wiring.write_text(
            'attach-to-agent = "code-reviewer"\n\n'
            '[[hooks.agentSpawn]]\ncommand = "$HOOK_BODY_PATH"\nmatcher = ""\n',
            encoding="utf-8",
        )

        rc, err = _run_upgrade(argparse.Namespace(
            pack="kiro-user-hooks", catalogue=str(self.cat),
            root=str(self.repo), scope="user", yes=True,
            skill=None, agent=None, hook=None, seed=None, command=None,
        ))
        self.assertEqual(rc, 0, f"upgrade failed: {err}")

        # New agent JSON exists with the wiring merged in.
        new_agent = self.home / ".kiro" / "agents" / "code-reviewer.json"
        self.assertTrue(new_agent.exists(), f"new agent JSON not produced: {new_agent}")
        new_data = json.loads(new_agent.read_text(encoding="utf-8"))
        self.assertIn("agentSpawn", new_data["hooks"])
        self.assertEqual(
            new_data["hooks"]["agentSpawn"][0]["id"], "kiro-user-hooks:on-spawn"
        )

        # State row now points at the new target-file.
        from agentbundle.config import load_state
        state = load_state(self.home / ".agentbundle" / "state.toml")
        owned = state.row("kiro-user-hooks", "kiro-cli").hook_wiring_owned
        self.assertEqual(len(owned), 1)
        self.assertEqual(owned[0]["target-file"], ".kiro/agents/code-reviewer.json")

        # Old agent JSON: either removed (by direct-file uninstall path)
        # or no longer carries the wiring entry. Either way, reconcile
        # must report no orphans.
        if old_agent.exists():
            old_data = json.loads(old_agent.read_text(encoding="utf-8"))
            self.assertNotIn(
                "agentSpawn", old_data.get("hooks", {}),
                "old agent JSON still carries the relocated wiring entry"
            )

        rc, stdout = _run_reconcile()
        self.assertEqual(rc, 0)
        self.assertNotIn("orphan-in-file", stdout)
        self.assertNotIn("orphan-in-state", stdout)


if __name__ == "__main__":
    unittest.main()
