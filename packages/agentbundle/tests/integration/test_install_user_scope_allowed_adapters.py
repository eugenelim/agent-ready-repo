"""T8 integration tests for RFC-0011 / pack-allowed-adapters at install
time (spec AC25).

End-to-end: invoke `agentbundle install --pack <name> --scope user`
in-process against fixture catalogues with `$HOME` redirected, and
assert (a) the right `~/.<ide>/skills/` directory receives the pack
and (b) `~/.agentbundle/state.toml` records the resolved adapter.

Reference idiom mirrors `test_install_converters_user_scope.py`:
in-process `install.run`, `$HOME` patched via `patch.dict`. The four
catalogue user-scope packs ship `allowed-adapters = ["claude-code",
"kiro-ide", "codex"]` (the bare `kiro` alias was de-staled to its
current RFC-0022 name), so this test covers the resolver's three
adapter-target paths without fabricating fixtures.
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


def _install_args(*, catalogue: str, repo: str, scope: str, adapter: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        pack="converters",
        catalogue=catalogue,
        output=repo,
        scope=scope,
        force=False,
        force_merge=False,
        adapter=adapter,
    )


class AllowedAdaptersInstallTests(unittest.TestCase):
    """The four cases that exercise the resolver's distinct paths:

      - kiro-only $HOME → install lands at ~/.kiro/skills/ (via kiro-ide)
      - codex-only $HOME (via ~/.codex/) → install lands at ~/.agents/skills/
      - greenfield $HOME (no CLI home) → install lands at ~/.claude/skills/
      - --adapter kiro-ide override against claude-code-populated $HOME →
        install lands at ~/.kiro/skills/
    """

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

    def _assert_pack_landed(self, ide_root_relpath: str, expected_adapter: str) -> None:
        skill_dir = self.home / ide_root_relpath / "file-to-markdown"
        self.assertTrue(
            skill_dir.is_dir(),
            f"expected skill directory at {skill_dir}",
        )
        # State records the resolved adapter (AC10a).
        from agentbundle.config import load_state

        state_path = self.home / ".agentbundle" / "state.toml"
        state = load_state(state_path)
        pack_state = state.packs.get("converters")
        self.assertIsNotNone(pack_state)
        self.assertEqual(pack_state.adapter, expected_adapter)

    def test_kiro_only_home_lands_at_kiro_skills(self) -> None:
        (self.home / ".kiro").mkdir()
        rc, stdout, stderr = _run_install(
            _install_args(catalogue=str(self.cat), repo=str(self.repo), scope="user")
        )
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")
        self._assert_pack_landed(".kiro/skills", "kiro-ide")
        self.assertIn("installed: converters @ user via kiro-ide", stdout)

    def test_codex_only_home_lands_at_agents_skills(self) -> None:
        (self.home / ".codex").mkdir()
        rc, stdout, stderr = _run_install(
            _install_args(catalogue=str(self.cat), repo=str(self.repo), scope="user")
        )
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")
        self._assert_pack_landed(".agents/skills", "codex")
        self.assertIn("installed: converters @ user via codex", stdout)

    def test_greenfield_home_lands_at_claude_skills(self) -> None:
        rc, stdout, stderr = _run_install(
            _install_args(catalogue=str(self.cat), repo=str(self.repo), scope="user")
        )
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")
        self._assert_pack_landed(".claude/skills", "claude-code")

    def test_adapter_override_wins_over_probe(self) -> None:
        (self.home / ".claude").mkdir()  # probe would pick claude-code
        rc, stdout, stderr = _run_install(
            _install_args(
                catalogue=str(self.cat),
                repo=str(self.repo),
                scope="user",
                adapter="kiro-ide",
            )
        )
        self.assertEqual(rc, 0, f"install failed: stdout={stdout!r} stderr={stderr!r}")
        self._assert_pack_landed(".kiro/skills", "kiro-ide")

    def test_upgrade_state_hint_preserves_adapter(self) -> None:
        """AC10b / AC25: install under claude-code; populate ~/.kiro/
        post-install; upgrade — state.adapter stays claude-code and
        the cross-adapter refusal at upgrade.py does NOT fire."""
        # Step 1: greenfield install → claude-code.
        rc, stdout, stderr = _run_install(
            _install_args(catalogue=str(self.cat), repo=str(self.repo), scope="user")
        )
        self.assertEqual(rc, 0, stderr)
        from agentbundle.config import load_state

        state_path = self.home / ".agentbundle" / "state.toml"
        before = load_state(state_path)
        self.assertEqual(before.packs["converters"].adapter, "claude-code")

        # Step 2: populate ~/.kiro/ post-install (would normally
        # redirect a fresh install to kiro on the probe path).
        (self.home / ".kiro").mkdir()

        # Step 3: upgrade — state hint should win, no cross-adapter
        # refusal.
        from agentbundle.commands import upgrade

        # Same source version → no-op upgrade, but the resolver runs
        # and the cross-adapter refusal can fire.
        upgrade_args = argparse.Namespace(
            pack="converters",
            catalogue=str(self.cat),
            to_version="0.1.0",
            root=str(self.repo),
            scope="user",
        )
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            rc = upgrade.run(upgrade_args)
        # The cross-adapter refusal text from upgrade.py:318-326 must
        # NOT appear; either rc == 0 (upgrade ran clean) or an
        # unrelated failure surfaced. State.adapter must stay
        # claude-code in either case.
        self.assertNotIn(
            "pack adapter changed from",
            stderr_buf.getvalue(),
            f"upgrade triggered cross-adapter refusal despite state hint",
        )
        after = load_state(state_path)
        self.assertEqual(
            after.packs["converters"].adapter,
            "claude-code",
            f"upgrade should preserve state.adapter; got {after.packs['converters'].adapter!r}",
        )

    # Note: `test_adapter_at_repo_scope_refused` was deleted by RFC-0012 —
    # `--adapter` is admitted at both scopes now. The new mutex with
    # `--emit-install-routes` is covered by
    # `tests/unit/test_install_argparse_emit_install_routes.py`.


if __name__ == "__main__":
    unittest.main()
