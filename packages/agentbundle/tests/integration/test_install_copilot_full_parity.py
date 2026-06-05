"""Integration tests for copilot full parity (T6 + T7 of
docs/specs/copilot-full-parity).

End-to-end against the live `packs/` catalogue (core + research) plus a
synthetic user-scope hook pack:

  - install `core` via `--adapter copilot --scope repo` → `.github/`
    {instructions, agents, hooks} all populated; the drop-warning names
    **only** `command` (agent + hook-wiring project natively now); rc 0.
  - install `research` via `--adapter copilot` (user scope by default) →
    `~/.copilot/{instructions,agents}/` populated; **not** refused (was
    refused via `allowed-adapters` pre-bump); warning silent (no command).
  - a **synthetic** user-scope hook pack rendered via copilot at user scope →
    `~/.copilot/hooks/` has both `<name>.json` and the hook body (closes the
    validation gap: core is repo-only, research ships no hooks).
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


def _run_install(argv: list[str]) -> tuple[int, str, str]:
    """Run `agentbundle install <argv>` in-process through the real parser."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


class CopilotRepoScopeCoreTests(unittest.TestCase):
    """AC12 / AC21: core via copilot at repo scope."""

    def setUp(self) -> None:
        from agentbundle.commands import install

        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.adopter = self.tmp / "adopter"
        self.adopter.mkdir()
        self._env = patch.dict(
            os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        install._clear_inband_detection_seen()
        install._clear_dropped_warning_seen()
        self.addCleanup(install._clear_dropped_warning_seen)
        self.addCleanup(install._clear_inband_detection_seen)

    def test_core_repo_scope_projects_all_four_and_warns_only_command(self) -> None:
        rc, _out, err = _run_install(
            [
                "--pack",
                "core",
                "--adapter",
                "copilot",
                "--scope",
                "repo",
                "--output",
                str(self.adopter),
                str(REPO_ROOT),
            ]
        )
        self.assertEqual(rc, 0, f"install failed: {err!r}")

        # All four projected primitive homes are populated.
        agents = self.adopter / ".github" / "agents"
        instructions = self.adopter / ".github" / "instructions"
        hooks = self.adopter / ".github" / "hooks"
        self.assertTrue(
            list(agents.glob("*.agent.md")), f"no agents projected: {agents}"
        )
        self.assertTrue(
            list(instructions.glob("*.instructions.md")),
            f"no instructions projected: {instructions}",
        )
        # hook bodies (.py) + hook-wiring (.json) both land at .github/hooks/.
        self.assertTrue(list(hooks.glob("*.py")), f"no hook bodies: {hooks}")
        self.assertTrue(
            list(hooks.glob("*.json")), f"no hook-wiring json: {hooks}"
        )
        # No legacy tools/hooks/ output for copilot.
        self.assertFalse((self.adopter / "tools" / "hooks").exists())

        # AC12: the drop-warning names only `command`. Inspect the *dropped
        # clause* (before "these primitives will not be installed") so the
        # plural compatible-list terms ("agents", "hook-wirings") don't trip a
        # naive substring check.
        warning_lines = [ln for ln in err.splitlines() if "dropped" in ln]
        self.assertTrue(warning_lines, f"expected a drop warning; stderr: {err!r}")
        warning = " ".join(warning_lines)
        dropped_clause = warning.split("these primitives will not be installed")[0]
        self.assertIn("ships 1 command", dropped_clause)
        self.assertNotIn("agent", dropped_clause)
        self.assertNotIn("hook-wiring", dropped_clause)
        # Compatible list names the four types copilot now projects for core.
        self.assertIn("skills", warning)
        self.assertIn("agents", warning)
        self.assertIn("hook-wirings", warning)
        self.assertIn("hook-bodies", warning)


class CopilotUserScopeResearchTests(unittest.TestCase):
    """AC11 / AC13: research via copilot at user scope."""

    def setUp(self) -> None:
        from agentbundle.commands import install

        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(
            os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        install._clear_inband_detection_seen()
        install._clear_dropped_warning_seen()
        self.addCleanup(install._clear_dropped_warning_seen)
        self.addCleanup(install._clear_inband_detection_seen)

    def test_research_user_scope_lands_under_copilot_home_not_refused(self) -> None:
        rc, _out, err = _run_install(
            [
                "--pack",
                "research",
                "--adapter",
                "copilot",
                "--scope",
                "user",
                "--output",
                str(self.repo),
                str(REPO_ROOT),
            ]
        )
        self.assertEqual(
            rc, 0, f"research via copilot at user scope refused/failed: {err!r}"
        )
        instructions = self.home / ".copilot" / "instructions"
        agents = self.home / ".copilot" / "agents"
        self.assertTrue(
            list(instructions.glob("*.instructions.md")),
            f"no user-scope instructions: {instructions}",
        )
        self.assertTrue(
            list(agents.glob("*.agent.md")),
            f"no user-scope agents: {agents}",
        )
        # No path leaked under ~/.github/… (the bug the prefix rewrite prevents).
        self.assertFalse((self.home / ".github").exists())

        # AC13: research ships no command → no 'dropped' warning line.
        self.assertNotIn("dropped", err)


class CopilotUserScopeSyntheticHookPackTests(unittest.TestCase):
    """AC21 user-scope-hook validation gap: a synthetic copilot user-scope
    hook pack lands `~/.copilot/hooks/` with both the wiring JSON and the
    hook body. No shipped pack exercises this (core is repo-only; research
    ships no hooks)."""

    def setUp(self) -> None:
        from agentbundle.commands import install

        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(
            os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        install._clear_inband_detection_seen()
        install._clear_dropped_warning_seen()
        self.addCleanup(install._clear_dropped_warning_seen)
        self.addCleanup(install._clear_inband_detection_seen)

        # Synthetic catalogue: <cat>/packs/synthhooks/ — a user-scope pack
        # shipping one hook body + one SessionStart wiring, copilot-allowed.
        self.cat = self.tmp / "catalogue"
        pack = self.cat / "packs" / "synthhooks"
        (pack / ".apm" / "hooks").mkdir(parents=True)
        (pack / ".apm" / "hook-wiring").mkdir(parents=True)
        (pack / ".apm" / "hooks" / "on-start.py").write_text(
            "print('hi')\n", encoding="utf-8"
        )
        (pack / ".apm" / "hook-wiring" / "on-start.toml").write_text(
            "[[hooks.SessionStart]]\n"
            'hooks = [ { type = "command", command = "python tools/on-start.py" } ]\n',
            encoding="utf-8",
        )
        pack.joinpath("pack.toml").write_text(
            '[pack]\n'
            'name = "synthhooks"\n'
            'version = "0.1.0"\n'
            'description = "Synthetic user-scope copilot hook pack for the '
            'copilot-full-parity user-scope-hook validation gap."\n\n'
            "[pack.adapter-contract]\n"
            'version = "0.10"\n\n'
            "[pack.install]\n"
            'default-scope = "user"\n'
            'allowed-scopes = ["user"]\n'
            'allowed-adapters = ["copilot"]\n'
            # Rail-B consent gesture: a hook-shipping user-scope pack must opt
            # in. For copilot the hooks are file-based (projected + prefix-
            # rewritten), so this only lifts the consent rail — no merge.
            "user-scope-hooks = true\n",
            encoding="utf-8",
        )

    def test_synthetic_hook_pack_lands_copilot_user_hooks(self) -> None:
        rc, _out, err = _run_install(
            [
                "--pack",
                "synthhooks",
                "--adapter",
                "copilot",
                "--scope",
                "user",
                "--output",
                str(self.repo),
                str(self.cat),
            ]
        )
        self.assertEqual(rc, 0, f"synthetic hook pack install failed: {err!r}")
        hooks = self.home / ".copilot" / "hooks"
        self.assertTrue(
            (hooks / "on-start.json").is_file(),
            f"missing wiring json at {hooks}",
        )
        self.assertTrue(
            (hooks / "on-start.py").is_file(),
            f"missing hook body at {hooks}",
        )
        # No leak under ~/.github/….
        self.assertFalse((self.home / ".github").exists())


if __name__ == "__main__":
    unittest.main()
