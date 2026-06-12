"""Unit tests for the copilot-agent-md serialiser (T1 of
docs/specs/copilot-full-parity).

The serialiser converts ``.apm/agents/<name>.md`` (YAML frontmatter + body)
into Copilot's ``<name>.agent.md`` shape: ``name`` / ``description`` pass
through the mapping's rename rules, ``model`` is dropped, ``target`` is never
emitted, and ``tools`` passes through verbatim **after** an allow-list
validation that fails the build on an unknown token (fail-closed).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentbundle.build.projections.copilot_agent_md import (
    project_copilot_agent_md,
    _KNOWN_TOOLS,
)


def test_known_tools_matches_spec_allow_list() -> None:
    # Pin the module's allow-list against the spec-documented set
    # (docs/specs/copilot-full-parity/spec.md § Always do / AC7) so the two
    # can't drift silently — mirrors the `_EVENT_MAP` pin in the hooks-json
    # test. The web tools `WebFetch`/`WebSearch` pass through and resolve to
    # Copilot's `web` tool on the CLI + app (docs/specs/copilot-skills-and-web /
    # RFC-0024 § Errata E1; only the cloud agent lacks it), so they are
    # known-and-recorded, not unknown.
    assert _KNOWN_TOOLS == frozenset(
        {
            "Read",
            "Grep",
            "Glob",
            "Edit",
            "Write",
            "MultiEdit",
            "Bash",
            "WebFetch",
            "WebSearch",
        }
    )

# The contract's `[frontmatter-mapping."copilot-agent-frontmatter-v0.10"]`
# after T3; mirrored here as a literal for unit isolation. `tools` is handled
# by the mode's allow-list pass-through, not a rename rule, so it is absent.
COPILOT_AGENT_FRONTMATTER_V010 = {
    "name": {"rename": "name"},
    "description": {"rename": "description"},
}

RULE = {
    "target-path": ".github/agents/",
    "frontmatter-mapping": "copilot-agent-frontmatter-v0.10",
}


class TestCopilotAgentMdSerialiser(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.source = Path(self._tmpdir.name) / "source"
        self.output = Path(self._tmpdir.name) / "output"
        self.source.mkdir()
        self.output.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write(self, body: str, name: str = "agent.md") -> None:
        (self.source / name).write_text(body, encoding="utf-8")

    def _run(self, stem: str = "agent") -> str:
        project_copilot_agent_md(
            self.source, self.output, RULE, COPILOT_AGENT_FRONTMATTER_V010
        )
        target = self.output / ".github" / "agents" / f"{stem}.agent.md"
        self.assertTrue(target.exists(), f"missing {target}")
        return target.read_text(encoding="utf-8")

    def _frontmatter_lines(self, text: str) -> list[str]:
        """Return the frontmatter lines (between the two `---` fences)."""
        lines = text.splitlines()
        self.assertEqual(lines[0], "---")
        end = lines.index("---", 1)
        return lines[1:end]

    def test_trivial_round_trip(self) -> None:
        self._write("---\nname: foo\ndescription: bar\n---\nBody content.\n")
        text = self._run()
        fm = self._frontmatter_lines(text)
        self.assertIn("name: foo", fm)
        self.assertIn("description: bar", fm)
        self.assertTrue(text.endswith("---\nBody content.\n"))

    def test_model_dropped(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\nmodel: sonnet\n---\nBody.\n"
        )
        text = self._run()
        self.assertNotIn("model", text)

    def test_target_never_emitted(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\ntarget: vscode\n---\nBody.\n"
        )
        text = self._run()
        self.assertNotIn("target", self._frontmatter_lines(text))

    def test_tools_verbatim_read_only(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\ntools: Read, Grep, Glob\n---\nB.\n"
        )
        text = self._run()
        fm = self._frontmatter_lines(text)
        self.assertIn("tools: Read, Grep, Glob", fm)
        # No widening: the emitted `tools:` line carries no write/execute
        # tokens. Scope the negative assertion to that line (not the whole
        # text — a description could legitimately contain "Edit").
        tools_line = next(ln for ln in fm if ln.startswith("tools:"))
        self.assertNotIn("Edit", tools_line)
        self.assertNotIn("Write", tools_line)
        self.assertNotIn("Bash", tools_line)

    def test_quoted_description_preserved_verbatim(self) -> None:
        # Some shipped agents (implementer, quality-engineer) quote their
        # description. The serialiser preserves the source value byte-for-byte
        # (valid YAML either way — Copilot's Claude-format parser strips the
        # quotes on read). Pin the quoted-source path the unquoted fixtures miss.
        self._write(
            '---\nname: foo\ndescription: "bar: baz (quux)"\ntools: Read\n---\nBody.\n'
        )
        fm = self._frontmatter_lines(self._run())
        self.assertIn('description: "bar: baz (quux)"', fm)

    def test_list_form_tools_fails_closed(self) -> None:
        # YAML list-form `tools:` is parsed as empty by the line-based parser;
        # emitting a bare `tools:` line would let Copilot widen to all tools.
        # Fail closed instead.
        self._write(
            "---\nname: foo\ndescription: bar\ntools:\n  - Read\n  - Grep\n---\nB.\n"
        )
        with self.assertRaises(ValueError) as ctx:
            project_copilot_agent_md(
                self.source, self.output, RULE, COPILOT_AGENT_FRONTMATTER_V010
            )
        self.assertIn("tools", str(ctx.exception))

    def test_bare_empty_tools_fails_closed(self) -> None:
        self._write("---\nname: foo\ndescription: bar\ntools: \n---\nB.\n")
        with self.assertRaises(ValueError):
            project_copilot_agent_md(
                self.source, self.output, RULE, COPILOT_AGENT_FRONTMATTER_V010
            )

    def test_tools_web_tools_known_recorded(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\n"
            "tools: Read, Grep, Glob, WebFetch, WebSearch\n---\nB.\n"
        )
        text = self._run()
        fm = self._frontmatter_lines(text)
        self.assertIn("tools: Read, Grep, Glob, WebFetch, WebSearch", fm)

    def test_unknown_tool_token_fails_closed(self) -> None:
        self._write("---\nname: foo\ndescription: bar\ntools: Read, Bogus\n---\nB.\n")
        with self.assertRaises(ValueError) as ctx:
            project_copilot_agent_md(
                self.source, self.output, RULE, COPILOT_AGENT_FRONTMATTER_V010
            )
        self.assertIn("Bogus", str(ctx.exception))

    def test_empty_body_preserved(self) -> None:
        self._write("---\nname: foo\ndescription: bar\n---\n")
        text = self._run()
        # Frontmatter present, body empty (no crash, no spurious content).
        self.assertTrue(text.endswith("---\n"))
        self.assertIn("name: foo", self._frontmatter_lines(text))


if __name__ == "__main__":
    unittest.main()
