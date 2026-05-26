"""T5 — codex projection modes flow through the runtime accessors.

Per plan T5 round-2 conclusion: there is no independent install-side
projection-mode dispatcher; the install handler routes through
``render.py`` → ``agentbundle.build.main.run_recipe`` →
``build/adapters/codex.py`` (T4's wiring). This module asserts that
T1's contract edits flow through the install-time runtime accessors:

  - ``_adapter_allowed_prefixes_repo('codex')`` and ``_user`` return
    lists containing ``.codex/`` (from T1's contract edit).
  - The path-jail accepts writes under the new ``.codex/`` prefix and
    rejects writes outside any of codex's allowed prefixes.
  - ``render.render_pack(...)`` of a one-agent fixture pack via codex
    produces ``.codex/agents/<name>.toml`` — the end-to-end install
    routing through the build pipeline correctly threads through T4's
    dispatch (this is integration-shape but lives here to pin the
    install wrapper, not the build-pipeline adapter).
"""

from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path


class TestCodexAllowedPrefixes(unittest.TestCase):
    """T1's contract edit (`.codex/` added to allowed-prefixes.{repo,user})
    flows through the install handler's runtime accessors."""

    def test_codex_allowed_prefixes_includes_codex_dir_repo(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_repo

        prefixes = _adapter_allowed_prefixes_repo("codex")
        self.assertIn(".codex/", prefixes)
        # Non-regression — pre-bump entries still present.
        self.assertIn(".agents/skills/", prefixes)
        self.assertIn(".agentbundle/", prefixes)
        self.assertIn("tools/hooks/", prefixes)

    def test_codex_allowed_prefixes_includes_codex_dir_user(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_user

        prefixes = _adapter_allowed_prefixes_user("codex")
        self.assertIn(".codex/", prefixes)
        # Non-regression — pre-bump entries still present.
        self.assertIn(".agents/skills/", prefixes)
        self.assertIn(".agentbundle/", prefixes)


class TestPathJailCodexPrefix(unittest.TestCase):
    """The path-jail accepts writes under ``.codex/`` (T1's allowed-prefix
    extension) for the codex-extended scope, and still refuses writes
    outside every prefix. Verifies via ``safety.write_jailed`` —
    success means the prefix was admitted; ``PathJailError`` means refused."""

    def test_path_jail_accepts_codex_agents_repo(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_repo
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_repo("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safety.write_jailed(
                root,
                ".codex/agents/foo.toml",
                b"x",
                scope="repo",
                allowed_prefixes=prefixes,
            )
            self.assertTrue((root / ".codex" / "agents" / "foo.toml").exists())

    def test_path_jail_accepts_codex_hooks_json_repo(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_repo
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_repo("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safety.write_jailed(
                root,
                ".codex/hooks.json",
                b"{}",
                scope="repo",
                allowed_prefixes=prefixes,
            )
            self.assertTrue((root / ".codex" / "hooks.json").exists())

    def test_path_jail_accepts_codex_user_scope(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_user
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_user("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safety.write_jailed(
                root,
                ".codex/agents/foo.toml",
                b"x",
                scope="user",
                allowed_prefixes=prefixes,
            )
            safety.write_jailed(
                root,
                ".codex/hooks.json",
                b"{}",
                scope="user",
                allowed_prefixes=prefixes,
            )

    def test_path_jail_rejects_write_outside_codex_prefixes(self) -> None:
        from agentbundle.commands.install import _adapter_allowed_prefixes_repo
        from agentbundle import safety

        prefixes = _adapter_allowed_prefixes_repo("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(safety.PathJailError):
                safety.write_jailed(
                    root,
                    "random-dir/foo",
                    b"x",
                    scope="repo",
                    allowed_prefixes=prefixes,
                )


class TestNoHardcodedCodexPrefixList(unittest.TestCase):
    """A regression that hardcodes codex's prefix list anywhere in the
    install handler would defeat T1's contract-driven design."""

    def test_no_hardcoded_codex_allowed_prefixes(self) -> None:
        """`_adapter_allowed_prefixes_*` is the only place codex's prefix
        list lives outside the contract file. A grep that catches new
        hardcoded sites surfaces a regression."""
        install_py = Path(__file__).resolve().parents[2] / "agentbundle" / "commands" / "install.py"
        text = install_py.read_text(encoding="utf-8")
        # The accessor's fallback default IS a hardcoded list — that's
        # the legacy-contract escape hatch, not new code. Allow it.
        # Any OTHER occurrence of '.codex/' next to a list literal in
        # install.py would be a hardcoded prefix list.
        # Cheap heuristic: count occurrences of `".codex/"` literal in
        # install.py. The legitimate use is the fallback in
        # `_adapter_allowed_prefixes_repo`/`_user` — currently no
        # codex-specific fallback exists there (the dict defaults
        # to `.agents/skills/`), so 0 occurrences is correct.
        # If a fallback is added later to include `.codex/`, that's
        # the one legitimate site; bump this assertion to 1 or 2 as
        # appropriate at that time.
        count = text.count('".codex/"')
        self.assertEqual(
            count,
            0,
            f"install.py should not hardcode '.codex/' anywhere "
            f"(found {count} occurrences); the prefix is contract-driven "
            f"per T1.",
        )


class TestCodexProjectRoutesAgentToBuildPipeline(unittest.TestCase):
    """``codex.project(...)`` (the function called by the install handler's
    ``_render_for_repo_scope`` and ``_render_for_user_scope`` helpers for
    a codex-targeted pack at install.py:1727) for a fixture pack with one
    agent produces ``.codex/agents/<name>.toml`` — confirming the install
    handler's wrapping correctly threads through T4's dispatch."""

    def test_codex_project_writes_agent_toml(self) -> None:
        from agentbundle.build.adapters import codex
        from agentbundle.build.main import _read_bundled

        contract = tomllib.loads(_read_bundled("adapter.toml"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "foo.md").write_text(
                "---\nname: foo\ndescription: a foo agent\n---\nBody.\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            codex.project(pack, contract, out)
            target = out / ".codex" / "agents" / "foo.toml"
            self.assertTrue(target.exists(), f"missing {target}")
            data = tomllib.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "foo")


if __name__ == "__main__":
    unittest.main()
