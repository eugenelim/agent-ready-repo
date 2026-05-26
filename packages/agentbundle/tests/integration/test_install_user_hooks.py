"""T8b: install --scope user routes hook-wiring through the v0.3 merge
engines (user_merge_json for Claude Code; merge_into_agent_json for
Kiro) and writes hook-wiring-owned state rows.

Covers spec ACs AC11, AC20, AC23, AC24, AC25; the CLI binding rails
for the new ``--force-merge`` flag also live here.
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


def _run_install(args_namespace) -> tuple[int, str, str]:
    """Invoke install.run() with stdout + stderr capture."""
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args_namespace)
    return rc, stdout.getvalue(), stderr.getvalue()


def _install_args(
    *,
    pack: str,
    catalogue: str,
    output: str,
    scope: str | None = None,
    force: bool = False,
    force_merge: bool = False,
) -> argparse.Namespace:
    """Build the install command's namespace shape, matching cli.py."""
    return argparse.Namespace(
        pack=pack,
        catalogue=catalogue,
        output=output,
        scope=scope,
        force=force,
        force_merge=force_merge,
    )


class _UserScopeInstallBase(unittest.TestCase):
    """Common setup: redirect the home directory to a tmp_path so the
    test never touches the developer's real home tree.

    Sets both ``HOME`` (POSIX) and ``USERPROFILE`` (Windows) — ``Path.home()``
    consults ``USERPROFILE`` first on Windows and ignores ``HOME`` there,
    so patching only ``HOME`` is a no-op on the Windows CI runner. Setting
    both is harmless on POSIX (``USERPROFILE`` is unused) and correct on
    Windows."""

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
        # Construct a temporary catalogue layout: <cat>/packs/<pack>/
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)


def _copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)
    # CI checkouts may strip +x; re-apply for hook bodies.
    for entry in dst.rglob("*.sh"):
        entry.chmod(0o755)


class CCUserHooksInstallTests(_UserScopeInstallBase):
    """Install the cc-user-hooks fixture; assert the user-scope merge
    landed and state captured hook-wiring-owned rows (AC23/AC20)."""

    def test_install_cc_user_hooks_writes_settings_and_state(self) -> None:
        _copy_fixture(FIXTURES / "cc-user-hooks", self.cat / "packs" / "cc-user-hooks")
        args = _install_args(
            pack="cc-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertEqual(rc, 0, f"install failed: {stderr}")

        # The Claude Code settings file received the merged entry.
        settings = self.home / ".claude" / "settings.json"
        self.assertTrue(settings.exists(), f"settings.json absent under {self.home}")
        data = json.loads(settings.read_text(encoding="utf-8"))
        entries = data["hooks"]["UserPromptSubmit"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "cc-user-hooks:on-prompt")

        # State captured a hook-wiring-owned row.
        from agentbundle.config import load_state

        state = load_state(self.home / ".agentbundle" / "state.toml")
        owned = state.packs["cc-user-hooks"].hook_wiring_owned
        self.assertEqual(len(owned), 1)
        self.assertEqual(owned[0]["event"], "UserPromptSubmit")
        self.assertEqual(owned[0]["id"], "cc-user-hooks:on-prompt")
        # adapter defaults to claude-code on read; we don't require an
        # explicit field on the row.


class KiroUserHooksInstallTests(_UserScopeInstallBase):
    """Install the kiro-user-hooks fixture; assert the agent JSON merge
    landed and state captured hook-wiring-owned rows with adapter +
    target-file fields (AC20/AC23)."""

    def test_install_kiro_user_hooks_writes_agent_json_and_state(self) -> None:
        _copy_fixture(FIXTURES / "kiro-user-hooks", self.cat / "packs" / "kiro-user-hooks")
        args = _install_args(
            pack="kiro-user-hooks",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertEqual(rc, 0, f"install failed: {stderr}")

        agent_json = self.home / ".kiro" / "agents" / "reviewer.json"
        self.assertTrue(agent_json.exists(), f"agent JSON absent: {agent_json}")
        data = json.loads(agent_json.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "reviewer")
        entries = data["hooks"]["agentSpawn"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "kiro-user-hooks:on-spawn")

        from agentbundle.config import load_state

        state = load_state(self.home / ".agentbundle" / "state.toml")
        ps = state.packs["kiro-user-hooks"]
        self.assertEqual(ps.adapter, "kiro")
        self.assertEqual(len(ps.hook_wiring_owned), 1)
        self.assertEqual(ps.hook_wiring_owned[0]["event"], "agentSpawn")
        self.assertEqual(ps.hook_wiring_owned[0]["id"], "kiro-user-hooks:on-spawn")
        self.assertEqual(
            ps.hook_wiring_owned[0]["target-file"],
            ".kiro/agents/reviewer.json",
        )


class ForceMergeFlagBindingTests(unittest.TestCase):
    """AC12 binding rails for ``--force-merge``:
       - Bound to ``install`` verb (other verbs refuse with
         ``unknown flag for <verb>: --force-merge``).
       - Bound to ``--scope user``.
       - Claude-Code-only at install time (refused on Kiro-targeted
         packs since agent JSON is pack-owned)."""

    def test_force_merge_on_uninstall_refuses_with_unknown_flag(self) -> None:
        import subprocess
        import sys as _sys

        proc = subprocess.run(
            [_sys.executable, "-m", "agentbundle", "uninstall", "--pack", "x", "--force-merge"],
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "agentbundle")},
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(
            "unknown flag for uninstall: --force-merge",
            proc.stderr.decode(),
        )

    def test_force_merge_at_repo_scope_refuses(self) -> None:
        """``--force-merge`` only makes sense at user scope (the
        merge target is a pack-owned file at repo scope). This tests
        the early gate — explicit `--scope repo` is refused."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "catalogue" / "packs").mkdir(parents=True)
            _copy_fixture(FIXTURES / "cc-user-hooks", tmp / "catalogue" / "packs" / "cc-user-hooks")
            (tmp / "repo").mkdir()
            args = _install_args(
                pack="cc-user-hooks",
                catalogue=str(tmp / "catalogue"),
                output=str(tmp / "repo"),
                scope="repo",
                force_merge=True,
            )
            rc, _stdout, stderr = _run_install(args)
            self.assertEqual(rc, 1)
            self.assertIn("--force-merge", stderr)
            self.assertIn("user scope", stderr)

    def test_force_merge_with_pack_default_repo_scope_refuses(self) -> None:
        """Tests the post-resolve gate — a pack defaulting to repo
        scope with `--force-merge` (no `--scope`) must also refuse.
        Synthesise a minimal pack with `default-scope = "repo"`."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = tmp / "catalogue" / "packs" / "repo-default"
            (pack / ".apm" / "skills" / "x").mkdir(parents=True)
            (pack / ".apm" / "skills" / "x" / "SKILL.md").write_text(
                "# x\n", encoding="utf-8"
            )
            (pack / "pack.toml").write_text(
                '[pack]\nname = "repo-default"\nversion = "0.1.0"\n\n'
                '[pack.adapter-contract]\nversion = "0.3"\n\n'
                '[pack.install]\ndefault-scope = "repo"\n'
                'allowed-scopes = ["repo"]\n',
                encoding="utf-8",
            )
            (tmp / "repo").mkdir()
            args = _install_args(
                pack="repo-default",
                catalogue=str(tmp / "catalogue"),
                output=str(tmp / "repo"),
                scope=None,
                force_merge=True,
            )
            rc, _stdout, stderr = _run_install(args)
            self.assertEqual(rc, 1)
            self.assertIn("--force-merge", stderr)
            self.assertIn("user scope", stderr)


class AttachToAgentPathTraversalRefusedTests(_UserScopeInstallBase):
    """A malicious pack declaring `attach-to-agent = "../../../tmp/escape"`
    in its wiring TOML must refuse at install time — the resolved
    target file would otherwise write outside the user-scope jail."""

    def test_dot_dot_in_attach_to_agent_refuses(self) -> None:
        pack = self.cat / "packs" / "evil-pack"
        (pack / ".apm" / "agents").mkdir(parents=True)
        # Declare kiro explicitly — the legacy agents-presence
        # heuristic that previously inferred this now defers to
        # ``DEFAULT_ADAPTER``.
        (pack / ".apm" / "agents" / "evil.md").write_text(
            "---\nname: evil\n---\nbody\n", encoding="utf-8"
        )
        (pack / ".apm" / "hooks").mkdir(parents=True)
        (pack / ".apm" / "hooks" / "on-spawn.sh").write_text(
            "#!/bin/sh\nexit 0\n", encoding="utf-8"
        )
        (pack / ".apm" / "hook-wiring").mkdir(parents=True)
        (pack / ".apm" / "hook-wiring" / "on-spawn.toml").write_text(
            # Path-traversal payload.
            'attach-to-agent = "../../../tmp/escape"\n\n'
            '[[hooks.agentSpawn]]\ncommand = "x"\n',
            encoding="utf-8",
        )
        (pack / "pack.toml").write_text(
            '[pack]\nname = "evil-pack"\nversion = "0.1.0"\n\n'
            '[pack.adapter-contract]\nversion = "0.3"\n\n'
            '[pack.install]\ndefault-scope = "user"\n'
            'allowed-scopes = ["user"]\nuser-scope-hooks = true\n'
            'allowed-adapters = ["kiro"]\n',
            encoding="utf-8",
        )
        for entry in pack.rglob("*.sh"):
            entry.chmod(0o755)
        args = _install_args(
            pack="evil-pack",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertEqual(rc, 1, "evil pack was accepted")
        self.assertIn("attach-to-agent", stderr)


class RailBStillRefusesPacksWithoutOptInTests(_UserScopeInstallBase):
    """AC24: A user-scope install of a pack that ships hooks but does
    NOT declare ``user-scope-hooks = true`` refuses at validate-rail
    time (Rail B's pre-T3 text)."""

    def test_install_user_scope_without_opt_in_refuses(self) -> None:
        # Synthesise a pack that ships hooks but lacks the opt-in flag.
        pack_dir = self.cat / "packs" / "no-opt-in"
        (pack_dir / ".apm" / "hooks").mkdir(parents=True)
        (pack_dir / ".apm" / "hooks" / "x.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (pack_dir / "pack.toml").write_text(
            "[pack]\nname = \"no-opt-in\"\nversion = \"0.1.0\"\n"
            "[pack.adapter-contract]\nversion = \"0.3\"\n"
            "[pack.install]\ndefault-scope = \"user\"\nallowed-scopes = [\"user\"]\n",
            encoding="utf-8",
        )
        args = _install_args(
            pack="no-opt-in",
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="user",
        )
        rc, _stdout, stderr = _run_install(args)
        self.assertEqual(rc, 1, f"install accepted no-opt-in pack: stderr={stderr}")
        self.assertIn("hook-shaped primitives", stderr)


if __name__ == "__main__":
    unittest.main()
