"""Tests for the lifted `merge-json` projection helper.

Originally private to ``adapters/claude_code.py`` as ``_project_merge_json``;
lifted to ``build/projections/merge_json.py`` by
docs/specs/dropped-primitives-coverage (T2). The existing claude-code
merge-json tests at ``test_adapter_claude_code.py`` remain green and
form the regression safety net for the lift; this module pins the
helper's contract directly so codex.py (T4) can rely on it.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.projections.merge_json import project_merge_json


class TestProjectMergeJson(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.source = Path(self._tmpdir.name) / "source"
        self.output = Path(self._tmpdir.name) / "output"
        self.source.mkdir()
        self.output.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _rule(
        self,
        target_path: str = ".target/hooks.json",
        managed_key: str = "hooks",
    ) -> dict:
        return {"target-path": target_path, "managed-key": managed_key}

    def test_empty_source_dir_writes_nothing(self) -> None:
        """No TOML files → no JSON output at the target path."""
        project_merge_json(self.source, self.output, self._rule())
        self.assertFalse((self.output / ".target" / "hooks.json").exists())

    def test_empty_managed_key_writes_nothing(self) -> None:
        """TOML file present but managed-key payload is empty → no output."""
        (self.source / "one.toml").write_text("[hooks]\n", encoding="utf-8")
        project_merge_json(self.source, self.output, self._rule())
        self.assertFalse((self.output / ".target" / "hooks.json").exists())

    def test_single_toml_writes_managed_key(self) -> None:
        """One TOML's managed-key payload lands at the target JSON."""
        (self.source / "one.toml").write_text(
            '[hooks]\n'
            '"SessionStart" = [{ matcher = "*", hooks = [{ type = "command", command = "echo hi" }] }]\n',
            encoding="utf-8",
        )
        project_merge_json(self.source, self.output, self._rule())
        target = self.output / ".target" / "hooks.json"
        self.assertTrue(target.exists())
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn("hooks", data)
        self.assertIn("SessionStart", data["hooks"])

    def test_merges_into_existing_json(self) -> None:
        """Existing non-managed keys in the JSON target are preserved."""
        target = self.output / ".target" / "hooks.json"
        target.parent.mkdir(parents=True)
        target.write_text(
            json.dumps({"other-key": {"keep": "this"}, "hooks": {"X": ["old"]}}),
            encoding="utf-8",
        )
        (self.source / "one.toml").write_text(
            '[hooks]\n"Y" = ["new"]\n', encoding="utf-8"
        )
        project_merge_json(self.source, self.output, self._rule())
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["other-key"], {"keep": "this"})
        # Both old and new managed-key entries merged.
        self.assertEqual(data["hooks"]["X"], ["old"])
        self.assertEqual(data["hooks"]["Y"], ["new"])

    def test_multiple_toml_files_merge_in_sorted_order(self) -> None:
        """Source files are iterated sorted; later overrides earlier."""
        (self.source / "a.toml").write_text(
            '[hooks]\n"X" = ["from-a"]\n', encoding="utf-8"
        )
        (self.source / "b.toml").write_text(
            '[hooks]\n"X" = ["from-b"]\n', encoding="utf-8"
        )
        project_merge_json(self.source, self.output, self._rule())
        target = self.output / ".target" / "hooks.json"
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"]["X"], ["from-b"])

    def test_output_serialisation_shape(self) -> None:
        """Output uses indent=2, sort_keys=True, trailing newline (idempotency)."""
        (self.source / "one.toml").write_text(
            '[hooks]\n"Y" = ["y"]\n"X" = ["x"]\n', encoding="utf-8"
        )
        project_merge_json(self.source, self.output, self._rule())
        target = self.output / ".target" / "hooks.json"
        text = target.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"), "expected trailing newline")
        # sort_keys: X before Y in the serialised hooks dict.
        x_pos = text.index('"X"')
        y_pos = text.index('"Y"')
        self.assertLess(x_pos, y_pos, "expected sort_keys=True ordering")

    def test_non_toml_files_ignored(self) -> None:
        """Files without .toml suffix are skipped."""
        (self.source / "skip.md").write_text("ignored", encoding="utf-8")
        (self.source / "one.toml").write_text(
            '[hooks]\n"X" = ["x"]\n', encoding="utf-8"
        )
        project_merge_json(self.source, self.output, self._rule())
        target = self.output / ".target" / "hooks.json"
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"], {"X": ["x"]})

    def test_target_path_at_target_root(self) -> None:
        """Target paths land where the rule says — verified for codex's
        `.codex/hooks.json` shape that T4 will dispatch to."""
        (self.source / "one.toml").write_text(
            '[hooks]\n"SessionStart" = [{matcher="*", hooks=[{type="command", command="x"}]}]\n',
            encoding="utf-8",
        )
        project_merge_json(
            self.source, self.output, self._rule(target_path=".codex/hooks.json")
        )
        self.assertTrue((self.output / ".codex" / "hooks.json").exists())


class TestClaudeCodeIntegrationStillGreen(unittest.TestCase):
    """Belt-and-braces: re-import claude-code's project_packs and confirm
    the merge-json branch still dispatches through the lifted helper."""

    def test_claude_code_imports_lifted_helper(self) -> None:
        from agentbundle.build.adapters import claude_code
        from agentbundle.build.projections import merge_json as projections_merge_json

        # The lifted symbol is the same one claude_code consumes.
        self.assertIs(
            claude_code.project_merge_json, projections_merge_json.project_merge_json
        )


if __name__ == "__main__":
    unittest.main()
