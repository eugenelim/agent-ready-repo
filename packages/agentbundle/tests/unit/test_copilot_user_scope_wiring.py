"""T4a — copilot user-scope install wiring (docs/specs/copilot-full-parity).

Pins the four install-side seams that the contract alone can't supply:
  - ``user_scope_capable_adapters_from_contract()`` includes ``copilot``
    (contract-derived: keys off ``[adapter.copilot.scope].user``).
  - the install handler's allowed-prefix accessors return copilot's repo +
    user prefixes (path-jail input).
  - ``_rewrite_copilot_user_scope_paths`` swaps ``.github/X/``→``.copilot/X/``
    for every primitive.
  - ``_render_for_user_scope`` dispatches copilot (was
    ``_AdapterResolutionRefused``).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class TestCopilotUserScopeCapability(unittest.TestCase):
    def test_capability_includes_copilot(self) -> None:
        from agentbundle.scope import user_scope_capable_adapters_from_contract

        self.assertIn("copilot", user_scope_capable_adapters_from_contract())

    def test_allowed_prefixes_repo(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_repo

        prefixes = _adapter_allowed_prefixes_repo("copilot")
        # v0.11 (copilot-skills-and-web): skills project as first-class
        # `.github/skills/` SKILL.md (was `.github/instructions/`).
        self.assertEqual(
            prefixes,
            [".github/skills/", ".github/agents/", ".github/hooks/"],
        )
        # Legacy tools/hooks/ prefix is gone (hook-body retargeted).
        self.assertNotIn("tools/hooks/", prefixes)

    def test_allowed_prefixes_user(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_user

        prefixes = _adapter_allowed_prefixes_user("copilot")
        self.assertEqual(
            prefixes,
            [
                ".copilot/skills/",
                ".copilot/agents/",
                ".copilot/hooks/",
                ".agentbundle/",
            ],
        )


class TestCopilotUserScopePathJail(unittest.TestCase):
    def test_jail_accepts_copilot_user_targets(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_user
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_user("copilot")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relpath in (
                ".copilot/agents/x.agent.md",
                ".copilot/skills/y/SKILL.md",
                ".copilot/hooks/z.json",
            ):
                safety.write_jailed(
                    root, relpath, b"x", scope="user", allowed_prefixes=prefixes
                )
                self.assertTrue((root / relpath).exists())

    def test_jail_rejects_github_under_home(self) -> None:
        # The bug AC10b's rewrite prevents: an unrewritten `.github/…` path
        # would resolve under `~/.github/…`, outside the user prefixes.
        from agentbundle.commands.install import _adapter_allowed_prefixes_user
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_user("copilot")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(safety.PathJailError):
                safety.write_jailed(
                    Path(tmp),
                    ".github/agents/x.agent.md",
                    b"x",
                    scope="user",
                    allowed_prefixes=prefixes,
                )


class TestRewriteCopilotUserScopePaths(unittest.TestCase):
    def test_rewrites_every_primitive_prefix(self) -> None:
        from agentbundle.commands.install import _rewrite_copilot_user_scope_paths

        projection = {
            ".github/skills/work-loop/SKILL.md": b"i",
            ".github/agents/reviewer.agent.md": b"a",
            ".github/hooks/session-start.json": b"w",
            ".github/hooks/session-start.py": b"b",
        }
        rewritten = _rewrite_copilot_user_scope_paths(projection)
        self.assertEqual(
            set(rewritten),
            {
                ".copilot/skills/work-loop/SKILL.md",
                ".copilot/agents/reviewer.agent.md",
                ".copilot/hooks/session-start.json",
                ".copilot/hooks/session-start.py",
            },
        )
        # Content is carried unchanged.
        self.assertEqual(
            rewritten[".copilot/agents/reviewer.agent.md"], b"a"
        )
        # No `.github/` path survives.
        self.assertFalse(any(p.startswith(".github/") for p in rewritten))


class TestRenderForUserScopeDispatchesCopilot(unittest.TestCase):
    """AC10a: copilot is no longer refused at the `_render_for_user_scope`
    dispatch. The helper returns repo-relpaths (`.github/…`); the
    `.copilot/…` rewrite is the caller's job."""

    def test_copilot_dispatch_not_refused(self) -> None:
        from agentbundle.commands.install import _render_for_user_scope

        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "foo.md").write_text(
                "---\nname: foo\ndescription: a foo agent\n---\nBody.\n",
                encoding="utf-8",
            )
            projection = _render_for_user_scope(
                pack,
                adapter="copilot",
                allowed_adapters=["copilot"],
                contract_version="0.10",
                command_name="install",
            )
        self.assertIn(".github/agents/foo.agent.md", projection)


if __name__ == "__main__":
    unittest.main()
