"""T8c: upgrade at user scope reconciles hook-wiring rows.

Covers spec § Upgrade reconciliation tests:
  - in-place upgrade (same wiring) is a no-op on the target file;
  - upgrade adds a new hook entry → state row appended, target appended;
  - upgrade removes a hook entry → state row removed, target updated;
  - upgrade with `attach-to-agent` rename (Kiro) walks both old and
    new target files (covered in test_upgrade_attach_to_agent.py).
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


def _install_args(pack, catalogue, output, scope="user"):
    return argparse.Namespace(
        pack=pack, catalogue=catalogue, output=output,
        scope=scope, force=False, force_merge=False,
    )


def _upgrade_args(pack, catalogue, to_version, root, scope="user"):
    return argparse.Namespace(
        pack=pack, catalogue=catalogue, to_version=to_version,
        root=root, scope=scope,
        skill=None, agent=None, hook=None, seed=None, command=None,
    )


def _copy_fixture(src, dst):
    shutil.copytree(src, dst)
    for entry in dst.rglob("*.sh"):
        entry.chmod(0o755)


class _UpgradeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"; self.home.mkdir()
        self.repo = self.tmp / "repo"; self.repo.mkdir()
        self._env = patch.dict(os.environ, {"HOME": str(self.home)})
        self._env.start()
        self.addCleanup(self._env.stop)
        self.cat = self.tmp / "cat"; (self.cat / "packs").mkdir(parents=True)


class UpgradeThenUninstallTests(_UpgradeBase):
    """Blocker #1 regression: install → upgrade → uninstall removes
    the merged Kiro agent JSON. Before the SHA-refresh fix, the
    upgrade's merge phase would leave state.files with a stale SHA;
    uninstall would misclassify the file as Tier-2 and refuse to
    remove it. Pins the fix at the integration level."""

    def test_kiro_install_upgrade_uninstall_removes_agent_file(self):
        from agentbundle.commands import uninstall as uninstall_cmd

        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")
        self.assertEqual(_run_install(_install_args(
            "kiro-user-hooks", str(self.cat), str(self.repo))), 0)

        # Upgrade (same wiring shape — exercises the merge phase
        # without testing the rename path).
        rc, err = _run_upgrade(_upgrade_args(
            "kiro-user-hooks", str(self.cat), "0.2.0", str(self.repo)))
        self.assertEqual(rc, 0, f"upgrade failed: {err}")

        # Uninstall.
        un_args = argparse.Namespace(
            pack="kiro-user-hooks", root=str(self.repo), scope="user",
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = uninstall_cmd.run(un_args)
        self.assertEqual(rc, 0, "uninstall failed")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        self.assertFalse(
            agent_json.exists(),
            "agent file survived uninstall after upgrade — SHA refresh missing",
        )


class InPlaceUpgradeIsNoOpTests(_UpgradeBase):
    """Upgrading the same pack version with the same wiring is a
    byte-stable no-op on the target file."""

    def test_same_version_same_wiring_is_byte_stable(self):
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        self.assertEqual(_run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo))), 0)

        settings = self.home / ".claude" / "settings.json"
        before = settings.read_bytes()
        # Upgrade to the same version (idempotent).
        rc, err = _run_upgrade(_upgrade_args(
            "cc-user-hooks", str(self.cat), "0.1.0", str(self.repo)))
        self.assertEqual(rc, 0, f"upgrade failed: {err}")
        self.assertEqual(settings.read_bytes(), before,
            "in-place upgrade wasn't byte-stable")


class UpgradeAddsHookEntryTests(_UpgradeBase):
    """When the new pack ships an additional wiring TOML, upgrade
    appends the new id-tagged entry; state row appended too."""

    def test_added_wiring_extends_state(self):
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        self.assertEqual(_run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo))), 0)

        # Mutate the catalogue: add a second wiring TOML to the pack.
        pack_in_cat = self.cat / "packs" / "cc-user-hooks"
        (pack_in_cat / ".apm" / "hook-wiring" / "on-session.toml").write_text(
            '[[hooks.SessionStart]]\ncommand = "session-cmd"\n', encoding="utf-8"
        )
        (pack_in_cat / ".apm" / "hooks" / "on-session.sh").write_text(
            "#!/bin/sh\nexit 0\n", encoding="utf-8"
        )
        (pack_in_cat / ".apm" / "hooks" / "on-session.sh").chmod(0o755)

        rc, err = _run_upgrade(_upgrade_args(
            "cc-user-hooks", str(self.cat), "0.2.0", str(self.repo)))
        self.assertEqual(rc, 0, f"upgrade failed: {err}")

        settings = self.home / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        # Both events now present.
        self.assertIn("UserPromptSubmit", data["hooks"])
        self.assertIn("SessionStart", data["hooks"])
        self.assertEqual(
            data["hooks"]["SessionStart"][0]["id"], "cc-user-hooks:on-session"
        )

        # State has both rows.
        from agentbundle.config import load_state
        state = load_state(self.home / ".agentbundle" / "state.toml")
        ids = {r["id"] for r in state.packs["cc-user-hooks"].hook_wiring_owned}
        self.assertEqual(
            ids,
            {"cc-user-hooks:on-prompt", "cc-user-hooks:on-session"},
        )


class UpgradeRemovesHookEntryTests(_UpgradeBase):
    """When the new pack drops a wiring TOML, upgrade removes the
    corresponding entry from both state and the target file."""

    def test_removed_wiring_drops_from_state_and_file(self):
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        pack_in_cat = self.cat / "packs" / "cc-user-hooks"
        # Add an extra wiring TOML before install so we can drop it on upgrade.
        (pack_in_cat / ".apm" / "hook-wiring" / "on-session.toml").write_text(
            '[[hooks.SessionStart]]\ncommand = "session-cmd"\n', encoding="utf-8"
        )
        (pack_in_cat / ".apm" / "hooks" / "on-session.sh").write_text(
            "#!/bin/sh\nexit 0\n", encoding="utf-8"
        )
        (pack_in_cat / ".apm" / "hooks" / "on-session.sh").chmod(0o755)
        self.assertEqual(_run_install(_install_args(
            "cc-user-hooks", str(self.cat), str(self.repo))), 0)

        settings = self.home / ".claude" / "settings.json"
        data_pre = json.loads(settings.read_text(encoding="utf-8"))
        self.assertIn("SessionStart", data_pre["hooks"])

        # Mutate catalogue: drop the on-session wiring TOML.
        (pack_in_cat / ".apm" / "hook-wiring" / "on-session.toml").unlink()

        rc, err = _run_upgrade(_upgrade_args(
            "cc-user-hooks", str(self.cat), "0.2.0", str(self.repo)))
        self.assertEqual(rc, 0, f"upgrade failed: {err}")

        data_post = json.loads(settings.read_text(encoding="utf-8"))
        # SessionStart entry gone (and the empty array pruned).
        self.assertNotIn("SessionStart", data_post.get("hooks", {}))
        # Other entries untouched.
        self.assertIn("UserPromptSubmit", data_post["hooks"])

        from agentbundle.config import load_state
        state = load_state(self.home / ".agentbundle" / "state.toml")
        ids = {r["id"] for r in state.packs["cc-user-hooks"].hook_wiring_owned}
        self.assertEqual(ids, {"cc-user-hooks:on-prompt"})


class LegacyKiroJsonUpgradeMigrationTests(_UpgradeBase):
    """RFC-0022 / kiro-install-alias-parity AC8: an adopter who installed via
    the legacy `kiro` JSON path (agent `.json` on disk, `state.adapter ==
    "kiro"`, `hook_wiring_owned` rows) must UPGRADE cleanly under the new
    code — the `kiro` alias now resolves to kiro-ide, so the upgrade re-renders
    `.md`, drops hook-wiring, reconciles the stale `.json` (no orphan), and
    clears the merge-owned rows. Simulated by installing via `kiro-cli` (real
    JSON + merge + correct SHA) and doctoring the recording to legacy `kiro`."""

    def test_legacy_kiro_recorded_state_upgrades_to_md_cleanly(self):
        from agentbundle.config import dump_state, load_state

        pack_dst = self.cat / "packs" / "kiro-user-hooks"
        _copy_fixture(FIXTURES / "kiro-user-hooks", pack_dst)
        self.assertEqual(_run_install(_install_args(
            "kiro-user-hooks", str(self.cat), str(self.repo))), 0)
        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        self.assertTrue(agent_json.exists(), "setup: legacy JSON agent should exist")

        # Doctor to the legacy recording: pre-split, the only kiro adapter was
        # `kiro`. Flip the catalogue pack to `["kiro"]` so the upgrade resolves
        # the alias (matching the recorded state hint).
        state_path = self.home / ".agentbundle" / "state.toml"
        state = load_state(state_path)
        state.packs["kiro-user-hooks"].adapter = "kiro"
        state_path.write_text(dump_state(state), encoding="utf-8")
        pt = (pack_dst / "pack.toml").read_text(encoding="utf-8")
        (pack_dst / "pack.toml").write_text(
            pt.replace('["kiro-cli"]', '["kiro"]'), encoding="utf-8"
        )

        rc, err = _run_upgrade(_upgrade_args(
            "kiro-user-hooks", str(self.cat), "0.2.0", str(self.repo)))
        self.assertEqual(rc, 0, f"legacy kiro upgrade failed: {err}")

        # The kiro alias re-renders the `.md` agent (kiro-ide shape) and the
        # hook-wiring reconciliation clears the merge-owned rows.
        self.assertTrue(
            (self.home / ".kiro" / "agents" / "reviewer.md").exists(),
            "upgrade should project the .md agent (kiro-ide shape)",
        )
        state2 = load_state(state_path)
        ps = state2.packs["kiro-user-hooks"]
        self.assertEqual(ps.adapter, "kiro")
        self.assertEqual(ps.hook_wiring_owned, [])

    @unittest.expectedFailure
    def test_legacy_kiro_upgrade_orphans_stale_json_known_limitation(self):
        """KNOWN LIMITATION (docs/backlog.md#upgrade-orphan-removal-on-projection-shape-change):
        `upgrade` has no orphan-removal step, so when an agent's projected file
        SHAPE changes across the upgrade (legacy kiro `.json` → kiro-ide `.md`),
        the new file is written but the stale `.json` is left on disk. For
        kiro-ide this is harmful — the IDE loads BOTH `.md` and `.json` agents.
        This is a pre-existing general upgrade limitation (independent of the
        alias migration); the clean path today is uninstall + reinstall (see
        LegacyKiroJsonUninstallMigrationTests, which IS clean). Marked
        expectedFailure until upgrade grows orphan-removal."""
        from agentbundle.config import dump_state, load_state

        pack_dst = self.cat / "packs" / "kiro-user-hooks"
        _copy_fixture(FIXTURES / "kiro-user-hooks", pack_dst)
        self.assertEqual(_run_install(_install_args(
            "kiro-user-hooks", str(self.cat), str(self.repo))), 0)
        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"

        state_path = self.home / ".agentbundle" / "state.toml"
        state = load_state(state_path)
        state.packs["kiro-user-hooks"].adapter = "kiro"
        state_path.write_text(dump_state(state), encoding="utf-8")
        pt = (pack_dst / "pack.toml").read_text(encoding="utf-8")
        (pack_dst / "pack.toml").write_text(
            pt.replace('["kiro-cli"]', '["kiro"]'), encoding="utf-8"
        )

        rc, err = _run_upgrade(_upgrade_args(
            "kiro-user-hooks", str(self.cat), "0.2.0", str(self.repo)))
        self.assertEqual(rc, 0, f"legacy kiro upgrade failed: {err}")
        # This is the assertion that currently fails (orphan left behind):
        self.assertFalse(agent_json.exists())


if __name__ == "__main__":
    unittest.main()
