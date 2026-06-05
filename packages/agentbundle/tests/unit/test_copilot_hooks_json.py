"""Unit tests for the copilot-hooks-json serialiser (T2 of
docs/specs/copilot-full-parity).

Copilot reads **every** ``*.json`` in its hooks dir, so each source
hook-wiring ``.toml`` serialises to its own self-contained
``<name>.json`` — a per-file shape, deliberately *not* the single merged
target codex's ``merge-json`` uses. Each handler carries the source command
into **both** ``bash`` and ``powershell`` keys (our shipped wiring is
shell-agnostic — ``python tools/...``). Event names are translated through a
frozen map; an unmapped source event fails the build (fail-closed).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.projections.copilot_hooks_json import (
    project_copilot_hooks_json,
    _EVENT_MAP,
)

RULE = {"target-path": ".github/hooks/"}


class TestCopilotHooksJsonSerialiser(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.source = Path(self._tmpdir.name) / "source"
        self.output = Path(self._tmpdir.name) / "output"
        self.source.mkdir()
        self.output.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write(self, name: str, body: str) -> None:
        (self.source / name).write_text(body, encoding="utf-8")

    def _run(self) -> None:
        project_copilot_hooks_json(self.source, self.output, RULE)

    def _load(self, stem: str) -> dict:
        target = self.output / ".github" / "hooks" / f"{stem}.json"
        self.assertTrue(target.exists(), f"missing {target}")
        return json.loads(target.read_text(encoding="utf-8"))

    def test_session_start_handler_shape(self) -> None:
        # Use a command without the `tools/hooks/` prefix so this shape test
        # isn't entangled with the hook-body-path rewrite (covered separately by
        # test_hook_body_path_rewritten_to_github_hooks).
        self._write(
            "session-start.toml",
            '[[hooks.SessionStart]]\n'
            'hooks = [\n'
            '  { type = "command", command = "python scripts/x.py" },\n'
            ']\n',
        )
        self._run()
        data = self._load("session-start")
        self.assertEqual(data["version"], 1)
        handlers = data["hooks"]["sessionStart"]
        self.assertEqual(handlers[0]["type"], "command")
        self.assertEqual(handlers[0]["bash"], "python scripts/x.py")
        self.assertEqual(handlers[0]["powershell"], "python scripts/x.py")

    def test_one_file_per_wiring(self) -> None:
        self._write(
            "a.toml",
            '[[hooks.SessionStart]]\n'
            'hooks = [ { type = "command", command = "cmd-a" } ]\n',
        )
        self._write(
            "b.toml",
            '[[hooks.Stop]]\n'
            'hooks = [ { type = "command", command = "cmd-b" } ]\n',
        )
        self._run()
        hooks_dir = self.output / ".github" / "hooks"
        produced = sorted(p.name for p in hooks_dir.glob("*.json"))
        self.assertEqual(produced, ["a.json", "b.json"])

    def test_frozen_event_map_all_six(self) -> None:
        expected = {
            "SessionStart": "sessionStart",
            "SessionEnd": "sessionEnd",
            "UserPromptSubmit": "userPromptSubmitted",
            "PreToolUse": "preToolUse",
            "PostToolUse": "postToolUse",
            "Stop": "agentStop",
        }
        self.assertEqual(_EVENT_MAP, expected)
        for source_event, copilot_event in expected.items():
            self._write(
                f"{source_event}.toml",
                f'[[hooks.{source_event}]]\n'
                'hooks = [ { type = "command", command = "c" } ]\n',
            )
        self._run()
        for source_event, copilot_event in expected.items():
            data = self._load(source_event)
            self.assertIn(copilot_event, data["hooks"])

    def test_unmapped_event_fails_closed(self) -> None:
        self._write(
            "bad.toml",
            '[[hooks.BogusEvent]]\n'
            'hooks = [ { type = "command", command = "c" } ]\n',
        )
        with self.assertRaises(ValueError) as ctx:
            self._run()
        self.assertIn("BogusEvent", str(ctx.exception))

    def test_hook_body_path_rewritten_to_github_hooks(self) -> None:
        # copilot retargets hook-body tools/hooks/ -> .github/hooks/, so a
        # command referencing the body by its legacy path must be rewritten to
        # where direct-file actually lands the script (AC9-repo). Our shipped
        # core wiring is exactly `python tools/hooks/session-start.py`.
        self._write(
            "session-start.toml",
            "[[hooks.SessionStart]]\n"
            'hooks = [ { type = "command", '
            'command = "python tools/hooks/session-start.py" } ]\n',
        )
        self._run()
        handler = self._load("session-start")["hooks"]["sessionStart"][0]
        self.assertEqual(handler["bash"], "python .github/hooks/session-start.py")
        self.assertEqual(handler["powershell"], "python .github/hooks/session-start.py")

    def test_malformed_handler_missing_command_fails_closed(self) -> None:
        # A handler missing `command` must raise a friendly ValueError naming
        # the file — not a bare uncaught KeyError (which would escape the
        # install handler's `except (FileNotFoundError, ValueError)` and crash
        # with an unlocated traceback).
        self._write(
            "broken.toml",
            '[[hooks.SessionStart]]\nhooks = [ { type = "command" } ]\n',
        )
        with self.assertRaises(ValueError) as ctx:
            self._run()
        self.assertIn("broken.toml", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
