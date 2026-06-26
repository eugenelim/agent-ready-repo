"""T8b: uninstall --scope user removes hook-wiring-owned entries from
the right target file (settings.json for Claude Code, agent JSON for
Kiro) and leaves the target file otherwise untouched.

Covers spec ACs AC11 (Claude Code uninstall precision) and AC19
(Kiro uninstall removes wiring but leaves the agent file in place
until the agent primitive's own uninstall runs).
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


def _run_install(args_namespace) -> int:
    from agentbundle.commands import install

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return install.run(args_namespace)


def _run_uninstall(args_namespace) -> tuple[int, str]:
    from agentbundle.commands import uninstall

    stderr = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
        rc = uninstall.run(args_namespace)
    return rc, stderr.getvalue()


def _copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)
    for entry in dst.rglob("*.sh"):
        entry.chmod(0o755)


def _install_args(pack: str, catalogue: str, output: str, scope: str | None = None):
    return argparse.Namespace(
        pack=pack,
        catalogue=catalogue,
        output=output,
        scope=scope,
        force=False,
        force_merge=False,
    )


def _uninstall_args(pack: str, output: str, scope: str | None = None):
    return argparse.Namespace(
        pack=pack,
        root=output,
        scope=scope,
        yes=True,
    )


class _UninstallBase(unittest.TestCase):
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


class CCUserHooksUninstallTests(_UninstallBase):
    """AC11: uninstall removes only owned entries from the settings
    file; empty `hooks.<event>` arrays are pruned. Other top-level
    keys in the settings file must survive."""

    def test_uninstall_removes_owned_settings_entry(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")

        # Install first.
        rc = _run_install(_install_args(
            pack="cc-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, "setup install failed")

        settings = self.home / ".claude" / "settings.json"
        data_before = json.loads(settings.read_text(encoding="utf-8"))
        self.assertIn("UserPromptSubmit", data_before["hooks"])

        # Now uninstall.
        rc, err = _run_uninstall(_uninstall_args(
            pack="cc-user-hooks",
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, f"uninstall failed: {err}")

        data_after = json.loads(settings.read_text(encoding="utf-8"))
        # The pack's owned entry is gone — and the empty event array
        # is pruned per RFC-0005 § Uninstall.
        self.assertNotIn(
            "UserPromptSubmit",
            data_after.get("hooks", {}),
            "uninstall left an empty hooks.UserPromptSubmit",
        )


class MultiPackUninstallPrecisionTests(_UninstallBase):
    """AC11 precision: uninstalling pack A leaves pack B's entries in
    place at their original positions. Exercises the end-to-end
    integration (install A → install B → uninstall A → assert B
    survives unchanged)."""

    def test_uninstalling_first_pack_leaves_second_pack_entries(self) -> None:
        # Pack A: cc-user-hooks (the fixture).
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        # Pack B: synthesised variant with a different basename so the
        # ids are unique (`pack-b:on-prompt-b` vs `cc-user-hooks:on-prompt`).
        pack_b_dir = self.cat / "packs" / "pack-b"
        (pack_b_dir / ".apm" / "hooks").mkdir(parents=True)
        (pack_b_dir / ".apm" / "hooks" / "on-prompt-b.sh").write_text(
            "#!/bin/sh\nexit 0\n", encoding="utf-8"
        )
        (pack_b_dir / ".apm" / "hook-wiring").mkdir(parents=True)
        (pack_b_dir / ".apm" / "hook-wiring" / "on-prompt-b.toml").write_text(
            '[[hooks.UserPromptSubmit]]\ncommand = "do-b"\nmatcher = ""\n',
            encoding="utf-8",
        )
        (pack_b_dir / "pack.toml").write_text(
            '[pack]\nname = "pack-b"\nversion = "0.1.0"\n\n'
            '[pack.adapter-contract]\nversion = "0.3"\n\n'
            '[pack.install]\ndefault-scope = "user"\n'
            'allowed-scopes = ["user"]\nuser-scope-hooks = true\n',
            encoding="utf-8",
        )
        for entry in pack_b_dir.rglob("*.sh"):
            entry.chmod(0o755)

        # Install both.
        for pack in ("cc-user-hooks", "pack-b"):
            rc = _run_install(_install_args(
                pack=pack, catalogue=str(self.cat),
                output=str(self.repo), scope="user",
            ))
            self.assertEqual(rc, 0, f"install of {pack} failed")

        settings = self.home / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        entries_before = data["hooks"]["UserPromptSubmit"]
        ids_before = [e["id"] for e in entries_before]
        self.assertEqual(
            ids_before,
            ["cc-user-hooks:on-prompt", "pack-b:on-prompt-b"],
            "install sequence didn't append in order",
        )

        # Uninstall pack A.
        rc, err = _run_uninstall(_uninstall_args(
            pack="cc-user-hooks", output=str(self.repo), scope="user",
        ))
        self.assertEqual(rc, 0, f"uninstall failed: {err}")

        data_after = json.loads(settings.read_text(encoding="utf-8"))
        entries_after = data_after["hooks"]["UserPromptSubmit"]
        # Pack B's entry survives at its position.
        self.assertEqual(len(entries_after), 1)
        self.assertEqual(entries_after[0]["id"], "pack-b:on-prompt-b")
        self.assertEqual(entries_after[0]["command"], "do-b")


class KiroUserHooksUninstallTests(_UninstallBase):
    """AC19: uninstall's hook-wiring unprojection removes the owned
    entries from the agent JSON. The end-to-end uninstall ALSO runs
    the agent primitive's `direct-file` uninstall which removes the
    agent file (because `state.files` recorded it as pack-owned).
    Both behaviors are exercised below — separately."""

    def test_full_uninstall_removes_both_wiring_and_agent_file(self) -> None:
        """End-to-end: uninstall removes the agent file (direct-file
        uninstall handles it via `state.files`)."""
        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")

        rc = _run_install(_install_args(
            pack="kiro-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, "setup install failed")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        before = json.loads(agent_json.read_text(encoding="utf-8"))
        self.assertIn("agentSpawn", before["hooks"])

        rc, err = _run_uninstall(_uninstall_args(
            pack="kiro-user-hooks",
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, f"uninstall failed: {err}")
        # The pack owns the agent file (`state.files` recorded it).
        # End-to-end uninstall removes it.
        self.assertFalse(
            agent_json.exists(),
            "agent file survived uninstall — direct-file uninstall should "
            "have removed it (state.files entry)",
        )

    def test_wiring_unproject_leaves_adopter_keys_alone(self) -> None:
        """Wiring-side AC19: unproject removes only the wiring-owned
        entries. Construct a scenario where the agent file persists
        after uninstall (synthetic pre-write of an adopter key the
        pack doesn't own) and assert the adopter key survives.
        """
        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")

        rc = _run_install(_install_args(
            pack="kiro-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, "setup install failed")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        # Adopter hand-edits the projected agent file with a custom
        # `notes` field. This breaks pack ownership (the SHA no longer
        # matches state.files), so end-to-end uninstall PRESERVES the
        # file as Tier-2 — exactly the case where wiring-only unproject
        # must remove its rows without taking the body with it.
        data = json.loads(agent_json.read_text(encoding="utf-8"))
        data["notes"] = "adopter-added"
        agent_json.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8",
        )

        rc, err = _run_uninstall(_uninstall_args(
            pack="kiro-user-hooks",
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, f"uninstall failed: {err}")

        # File preserved (Tier-2 adopter edit).
        self.assertTrue(agent_json.exists(), "Tier-2 file removed by uninstall")
        after = json.loads(agent_json.read_text(encoding="utf-8"))
        # Wiring entries gone.
        self.assertNotIn("agentSpawn", after.get("hooks", {}))
        # Adopter key survived.
        self.assertEqual(after.get("notes"), "adopter-added")


class LegacyKiroJsonUninstallMigrationTests(_UninstallBase):
    """RFC-0022 / kiro-install-alias-parity AC8: an adopter who installed via
    the legacy `kiro` JSON path (agent JSON on disk, `state.adapter == "kiro"`,
    `hook_wiring_owned` rows pointing at the agent JSON) must uninstall cleanly
    under the new code — the agent JSON is removed (not orphaned) and the
    merge-family unproject routes to the agent-JSON engine, not Claude Code's
    settings engine. Simulated by installing via `kiro-cli` (which produces the
    JSON + merge), then doctoring `state.adapter` to the legacy `"kiro"`."""

    def test_legacy_kiro_recorded_state_uninstalls_agent_json_cleanly(self) -> None:
        from agentbundle.config import dump_state, load_state

        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")
        rc = _run_install(_install_args(
            pack="kiro-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, "setup install failed")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        self.assertTrue(agent_json.exists(), "setup: agent JSON should exist")

        # Doctor state to the legacy recording: pre-split, the only kiro
        # adapter was `kiro`, so an old install recorded `kiro` (not `kiro-cli`).
        state_path = self.home / ".agentbundle" / "state.toml"
        state = load_state(state_path)
        # Re-key the row from ("kiro-user-hooks", "kiro-cli") to ("kiro-user-hooks", "kiro").
        old_row = state.packs.pop(("kiro-user-hooks", "kiro-cli"))
        old_row.adapter = "kiro"
        state.packs[("kiro-user-hooks", "kiro")] = old_row
        state_path.write_text(dump_state(state), encoding="utf-8")

        rc, err = _run_uninstall(_uninstall_args(
            pack="kiro-user-hooks",
            output=str(self.repo),
            scope="user",
        ))
        self.assertEqual(rc, 0, f"uninstall of legacy kiro state failed: {err}")
        self.assertFalse(
            agent_json.exists(),
            "legacy kiro agent JSON orphaned by uninstall (adapter mis-routed)",
        )


if __name__ == "__main__":
    unittest.main()
