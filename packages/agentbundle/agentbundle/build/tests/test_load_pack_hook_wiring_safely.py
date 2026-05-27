"""T1 (incompatible-hook-event-drop): construction tests for
``_load_pack_hook_wiring_safely``.

Five tests covering the three refusal paths (hook-wiring symlink, agent
symlink, TOML parse failure) and the two happy-path shapes (clean pack,
missing hook-wiring directory).

These tests are written before the implementation exists (TDD red phase).
"""

from __future__ import annotations

import os
import tempfile
import textwrap
import unittest
from pathlib import Path


def _make_pack(
    root: Path,
    pack_name: str,
    *,
    wiring: dict[str, str] | None = None,
    agents: list[str] | None = None,
    wiring_symlinks: list[str] | None = None,
    agent_symlinks: list[str] | None = None,
) -> Path:
    """Build a minimal pack fixture on disk.

    - ``wiring``: stem → TOML body strings written under `.apm/hook-wiring/`.
    - ``agents``: stems written as `.md` files under `.apm/agents/`.
    - ``wiring_symlinks``: stems that become symlinks under `.apm/hook-wiring/`.
    - ``agent_symlinks``: stems that become symlinks under `.apm/agents/`.
    """
    pack = root / pack_name
    (pack / ".apm" / "hook-wiring").mkdir(parents=True, exist_ok=True)
    (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)

    for stem, body in (wiring or {}).items():
        (pack / ".apm" / "hook-wiring" / f"{stem}.toml").write_text(
            body, encoding="utf-8"
        )

    for stem in agents or []:
        (pack / ".apm" / "agents" / f"{stem}.md").write_text(
            f"# {stem}\n", encoding="utf-8"
        )

    # Create dangling symlinks to simulate the security-rail case.
    for stem in wiring_symlinks or []:
        target_path = pack / ".apm" / "hook-wiring" / f"{stem}.toml"
        # Point at a non-existent target so it's definitely a symlink.
        os.symlink("/nonexistent/target.toml", target_path)

    for stem in agent_symlinks or []:
        target_path = pack / ".apm" / "agents" / f"{stem}.md"
        os.symlink("/nonexistent/target.md", target_path)

    return pack


class TestLoadPackHookWiringSafely(unittest.TestCase):
    """Construction tests for ``_load_pack_hook_wiring_safely``."""

    def _import_helper(self):
        from agentbundle.build.scope_rails import _load_pack_hook_wiring_safely
        return _load_pack_hook_wiring_safely

    def test_returns_loaded_tomls_when_clean(self) -> None:
        """Happy path: valid hook-wiring + agents returns the (wiring_tomls, agent_basenames) tuple."""
        helper = self._import_helper()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = _make_pack(
                tmp,
                "clean-pack",
                wiring={
                    "session-start": textwrap.dedent("""
                        attach-to-agent = "work-loop"

                        [[hooks.SessionStart]]
                        command = "python3 tools/hooks/session-start.py"
                    """).strip()
                },
                agents=["work-loop"],
            )
            result = helper(pack, "clean-pack")
            # Should return a tuple, not a string.
            self.assertIsInstance(result, tuple)
            wiring_tomls, agent_basenames = result
            self.assertIsInstance(wiring_tomls, dict)
            self.assertIsInstance(agent_basenames, set)
            # The parsed TOML dict should contain the "session-start" key.
            self.assertIn("session-start", wiring_tomls)
            # The agents set should contain the work-loop agent.
            self.assertIn("work-loop", agent_basenames)

    def test_returns_refusal_string_on_hook_wiring_symlink(self) -> None:
        """Security rail: a symlink under .apm/hook-wiring/ returns a refusal string."""
        helper = self._import_helper()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = _make_pack(
                tmp,
                "symlink-wiring-pack",
                wiring_symlinks=["malicious"],
                agents=["some-agent"],
            )
            result = helper(pack, "symlink-wiring-pack")
            self.assertIsInstance(result, str)
            self.assertIn("symlink-wiring-pack", result)
            self.assertIn("hook-wiring entry is a symlink", result)

    def test_returns_refusal_string_on_toml_parse_failure(self) -> None:
        """Correctness rail: a malformed TOML returns a refusal string."""
        helper = self._import_helper()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = _make_pack(
                tmp,
                "bad-toml-pack",
                wiring={"broken": "this is not = valid = toml ["},
                agents=["some-agent"],
            )
            result = helper(pack, "bad-toml-pack")
            self.assertIsInstance(result, str)
            self.assertIn("failed to parse", result)

    def test_returns_refusal_string_on_agent_symlink(self) -> None:
        """Security rail: a symlink under .apm/agents/ returns a refusal string."""
        helper = self._import_helper()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = _make_pack(
                tmp,
                "symlink-agent-pack",
                wiring={
                    "on-prompt": textwrap.dedent("""
                        attach-to-agent = "work-loop"

                        [[hooks.userPromptSubmit]]
                        command = "x"
                    """).strip()
                },
                agent_symlinks=["work-loop"],
            )
            result = helper(pack, "symlink-agent-pack")
            self.assertIsInstance(result, str)
            self.assertIn("symlink-agent-pack", result)
            self.assertIn("agent entry is a symlink", result)

    def test_empty_hook_wiring_dir_returns_empty_tuple(self) -> None:
        """Happy path: .apm/ exists but no hook-wiring/ subdir returns ({}, set()).

        The plan specifies returning ({}, set()) for the uniform-type-signature
        case — the helper short-circuits before agent discovery when there is
        nothing to load from hook-wiring.
        """
        helper = self._import_helper()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = tmp / "no-wiring-pack"
            # Only create .apm/ with agents — no hook-wiring/ subdir.
            (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)
            (pack / ".apm" / "agents" / "work-loop.md").write_text("# work-loop\n", encoding="utf-8")
            result = helper(pack, "no-wiring-pack")
            self.assertIsInstance(result, tuple)
            wiring_tomls, agent_basenames = result
            self.assertEqual(wiring_tomls, {})
            # Per the plan: ({}, set()) — short-circuits before agent discovery.
            self.assertEqual(agent_basenames, set())


if __name__ == "__main__":
    unittest.main()
