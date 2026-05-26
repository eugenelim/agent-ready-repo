"""Unit tests for the codex-agent-toml serialiser (T3 of
docs/specs/dropped-primitives-coverage).

The serialiser converts ``.apm/agents/<name>.md`` (YAML frontmatter + body)
into codex-style ``<name>.toml`` with three keys: ``name``, ``description``,
``developer_instructions``. Tests pin the round-trip contract:
``tomllib.loads`` of the output must reproduce the input frontmatter
values + body, byte-for-byte.
"""

from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

from agentbundle.build.projections.codex_agent_toml import (
    project_codex_agent_toml,
    _apply_mapping,
)

# The contract's `[frontmatter-mapping."codex-agent-frontmatter-v0.8"]`
# after T1; mirrored here as a literal for unit isolation.
CODEX_AGENT_FRONTMATTER_V08 = {
    "name": {"rename": "name"},
    "description": {"rename": "description"},
}

RULE = {
    "target-path": ".codex/agents/",
    "frontmatter-mapping": "codex-agent-frontmatter-v0.8",
}


class TestCodexAgentTomlSerialiser(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.source = Path(self._tmpdir.name) / "source"
        self.output = Path(self._tmpdir.name) / "output"
        self.source.mkdir()
        self.output.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _run(self) -> dict:
        project_codex_agent_toml(
            self.source, self.output, RULE, CODEX_AGENT_FRONTMATTER_V08
        )
        target = self.output / ".codex" / "agents" / "agent.toml"
        self.assertTrue(target.exists(), f"missing {target}")
        return tomllib.loads(target.read_text(encoding="utf-8"))

    def _write(self, body: str) -> None:
        (self.source / "agent.md").write_text(body, encoding="utf-8")

    def test_trivial_round_trip(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\n---\nBody content.\n"
        )
        data = self._run()
        self.assertEqual(data["name"], "foo")
        self.assertEqual(data["description"], "bar")
        self.assertEqual(data["developer_instructions"], "Body content.\n")

    def test_multiline_body_preserved(self) -> None:
        body = (
            "---\nname: foo\ndescription: bar\n---\n"
            "First line.\nSecond line with \"hello\" and a backslash \\.\n"
            "\nThird line after blank.\n"
        )
        self._write(body)
        data = self._run()
        expected_body = (
            "First line.\nSecond line with \"hello\" and a backslash \\.\n"
            "\nThird line after blank.\n"
        )
        self.assertEqual(data["developer_instructions"], expected_body)

    def test_unmapped_fields_dropped(self) -> None:
        self._write(
            "---\nname: foo\ndescription: bar\ntools: [a, b]\nmodel: opus\n---\n"
            "Body.\n"
        )
        data = self._run()
        self.assertEqual(set(data.keys()), {"name", "description", "developer_instructions"})

    def test_frontmatter_rename_applied(self) -> None:
        """A mapping that renames ``summary`` → ``description`` is honoured."""
        custom_mapping = {
            "name": {"rename": "name"},
            "summary": {"rename": "description"},
        }
        (self.source / "agent.md").write_text(
            "---\nname: foo\nsummary: it's a summary\n---\nBody.\n",
            encoding="utf-8",
        )
        project_codex_agent_toml(self.source, self.output, RULE, custom_mapping)
        target = self.output / ".codex" / "agents" / "agent.toml"
        data = tomllib.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["description"], "it's a summary")
        self.assertNotIn("summary", data)

    def test_empty_body_emits_empty_developer_instructions(self) -> None:
        self._write("---\nname: foo\ndescription: bar\n---\n")
        data = self._run()
        self.assertEqual(data["developer_instructions"], "")

    def test_markdown_body_lands_in_developer_instructions(self) -> None:
        """Mode-level convention — the body always lands in
        ``developer_instructions`` regardless of mapping shape."""
        self._write("---\nname: foo\n---\nThis is the body.\n")
        data = self._run()
        self.assertEqual(data["developer_instructions"], "This is the body.\n")

    def test_developer_instructions_not_in_frontmatter_mapping(self) -> None:
        """Contract assertion — the mapping must NOT contain a `body` or
        `developer_instructions` sub-table; the body-to-DI is a mode-level
        convention per spec AC4. This test pins the assumption the
        serialiser relies on."""
        self.assertNotIn("body", CODEX_AGENT_FRONTMATTER_V08)
        self.assertNotIn("developer_instructions", CODEX_AGENT_FRONTMATTER_V08)

    def test_quote_in_description(self) -> None:
        """A double-quote in a basic-string field round-trips."""
        self._write('---\nname: foo\ndescription: a "quoted" name\n---\nBody.\n')
        data = self._run()
        self.assertEqual(data["description"], 'a "quoted" name')

    def test_multiple_files_sorted(self) -> None:
        """Multiple agent.md files each project independently."""
        (self.source / "b.md").write_text(
            "---\nname: b\ndescription: B\n---\nB body.\n", encoding="utf-8"
        )
        (self.source / "a.md").write_text(
            "---\nname: a\ndescription: A\n---\nA body.\n", encoding="utf-8"
        )
        project_codex_agent_toml(
            self.source, self.output, RULE, CODEX_AGENT_FRONTMATTER_V08
        )
        target_dir = self.output / ".codex" / "agents"
        self.assertTrue((target_dir / "a.toml").exists())
        self.assertTrue((target_dir / "b.toml").exists())

    def test_non_md_files_ignored(self) -> None:
        """Files without ``.md`` suffix are skipped."""
        (self.source / "skip.txt").write_text("ignored", encoding="utf-8")
        self._write("---\nname: foo\n---\nBody.\n")
        data = self._run()
        # If `skip.txt` had been processed we'd get .codex/agents/skip.toml;
        # check it's absent.
        self.assertFalse(
            (self.output / ".codex" / "agents" / "skip.toml").exists()
        )


class TestApplyMapping(unittest.TestCase):
    """Unit-isolate the mapping logic."""

    def test_rename_propagates_value(self) -> None:
        result = _apply_mapping(
            {"name": "foo"}, {"name": {"rename": "name"}}
        )
        self.assertEqual(result, {"name": "foo"})

    def test_unmapped_key_dropped(self) -> None:
        result = _apply_mapping(
            {"name": "foo", "tools": ["x"]},
            {"name": {"rename": "name"}},
        )
        self.assertEqual(result, {"name": "foo"})

    def test_list_collapsed_to_comma_joined(self) -> None:
        """Degenerate case — packs that ship ``description: [a, b]``
        get a comma-joined string rather than a serialiser crash."""
        result = _apply_mapping(
            {"description": ["a", "b"]},
            {"description": {"rename": "description"}},
        )
        self.assertEqual(result, {"description": "a, b"})


if __name__ == "__main__":
    unittest.main()
