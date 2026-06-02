"""T-C2 (RFC-0005 kiro-ide-hook): validate rail tests.

Five refusal paths plus an accept case. Each refusal pins the
RFC-0005 § *validate rail* error text and the rail's first-offender
discipline (sorted enumeration; first refusal wins).

The rail lives at
``agentbundle.build.scope_rails.check_kiro_ide_hook`` — alongside
the existing Kiro rails (``check_kiro_attach_to_agent``,
``check_kiro_event_vocabulary``, ``check_kiro_wiring``) so all four
sit together.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


# E3 vocabulary — closed by RFC-0022 via static analysis of
# extension.js IDEListenableEvent enum (2026-06-01). Supersedes the
# RFC-0005 best-guess list (fileSave/fileEdit/manualTrigger).
# See RFC-0005 § Errata, E3 and probes.md Q11 Outcome.
KIRO_EVENT_VOCAB = [
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "userTriggered",
    "promptSubmit",
    "agentStop",
    "preToolUse",
    "postToolUse",
    "preTaskExecution",
    "postTaskExecution",
    "sessionStart",
]
KIRO_ACTION_VOCAB = ["askAgent", "runCommand"]


def _ask_agent_hook(*, name="Lint on save", when_type="fileEdited",
                    then_type="askAgent", prompt="Run ruff.",
                    version="1", drop: str | None = None) -> dict:
    """Build a valid askAgent .kiro.hook body; ``drop`` removes a top-level key."""
    body: dict = {
        "name": name,
        "description": "Synthetic test hook.",
        "version": version,
        "when": {"type": when_type, "patterns": ["**/*.py"]},
        "then": {"type": then_type, "prompt": prompt},
    }
    if drop is not None:
        body.pop(drop, None)
    return body


def _run_command_hook(command: str = "${hook-body:lint}") -> dict:
    return {
        "name": "Lint on save (runCommand)",
        "description": "Synthetic runCommand hook.",
        "version": "1",
        "when": {"type": "fileEdited", "patterns": ["**/*.py"]},
        "then": {"type": "runCommand", "command": command},
    }


def _make_pack(root: Path, pack_name: str = "test-pack",
               hooks: dict[str, dict] | None = None,
               hook_bodies: list[str] | None = None) -> Path:
    """Lay out a minimal pack on disk and return its path."""
    pack = root / pack_name
    hooks_dir = pack / ".apm" / "kiro-ide-hooks"
    hooks_dir.mkdir(parents=True)
    for filename, body in (hooks or {}).items():
        (hooks_dir / filename).write_text(json.dumps(body), encoding="utf-8")
    if hook_bodies:
        body_dir = pack / ".apm" / "hooks"
        body_dir.mkdir(parents=True)
        for filename in hook_bodies:
            (body_dir / filename).write_text("#!/bin/sh\n", encoding="utf-8")
    return pack


def _run_rail(pack_path: Path, pack_name: str = "test-pack",
              target_adapters=("kiro",),
              ide_event_vocabulary=KIRO_EVENT_VOCAB,
              ide_action_vocabulary=KIRO_ACTION_VOCAB) -> str | None:
    from agentbundle.build.scope_rails import check_kiro_ide_hook

    return check_kiro_ide_hook(
        pack_path,
        pack_name,
        target_adapters,
        ide_event_vocabulary=ide_event_vocabulary,
        ide_action_vocabulary=ide_action_vocabulary,
    )


class CleanPackPasses(unittest.TestCase):
    """A pack with valid askAgent + runCommand hooks (with a same-pack
    hook-body for the placeholder) passes."""

    def test_ask_agent_and_run_command_pass(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={
                    "ask.kiro.hook": _ask_agent_hook(),
                    "cmd.kiro.hook": _run_command_hook(command="${hook-body:lint}"),
                },
                hook_bodies=["lint.py"],
            )
            self.assertIsNone(_run_rail(pack))

    def test_rail_no_op_when_kiro_not_in_target_adapters(self) -> None:
        with TemporaryDirectory() as raw:
            # Even a malformed pack passes when kiro isn't a target.
            pack = _make_pack(
                Path(raw),
                hooks={"broken.kiro.hook": {"description": "no required fields"}},
            )
            self.assertIsNone(_run_rail(pack, target_adapters=("claude-code",)))

    def test_rail_no_op_when_kiro_ide_hooks_dir_absent(self) -> None:
        with TemporaryDirectory() as raw:
            pack = Path(raw) / "test-pack"
            pack.mkdir()
            self.assertIsNone(_run_rail(pack))


class MissingRequiredFieldRefuses(unittest.TestCase):
    """T-C2.1 — RFC § validate rail check 2: required fields are
    ``name``, ``version``, ``when.type``, ``then.type``."""

    def test_missing_top_level_name(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(drop="name")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("missing required field name", refusal)
            self.assertIn("hook.kiro.hook", refusal)
            self.assertIn("test-pack", refusal)

    def test_missing_version(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(drop="version")},
            )
            refusal = _run_rail(pack)
            self.assertIn("missing required field version", refusal)

    def test_missing_when_type(self) -> None:
        with TemporaryDirectory() as raw:
            body = _ask_agent_hook()
            body["when"] = {"patterns": ["**/*.py"]}  # no type
            pack = _make_pack(Path(raw), hooks={"hook.kiro.hook": body})
            refusal = _run_rail(pack)
            self.assertIn("missing required field when.type", refusal)

    def test_missing_then_type(self) -> None:
        with TemporaryDirectory() as raw:
            body = _ask_agent_hook()
            body["then"] = {"prompt": "no type"}
            pack = _make_pack(Path(raw), hooks={"hook.kiro.hook": body})
            refusal = _run_rail(pack)
            self.assertIn("missing required field then.type", refusal)


class EventVocabularyRefusal(unittest.TestCase):
    """T-C2.2 — out-of-vocabulary ``when.type``."""

    def test_pascal_case_event_refused(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="FileSave")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("uses event 'FileSave'", refusal)
            self.assertIn("ide-event-vocabulary", refusal)
            self.assertIn("hook.kiro.hook", refusal)


class ActionVocabularyRefusal(unittest.TestCase):
    """T-C2.3 — out-of-vocabulary ``then.type``."""

    def test_unknown_action_refused(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(then_type="launchShip")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("uses action 'launchShip'", refusal)
            self.assertIn("ide-action-vocabulary", refusal)


class MalformedPlaceholderRefusal(unittest.TestCase):
    """T-C2.4 — placeholder that doesn't match ``\\$\\{hook-body:[a-zA-Z0-9_-]+\\}``."""

    def test_placeholder_with_whitespace_in_name_refused(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={
                    "cmd.kiro.hook": _run_command_hook(
                        command="${hook-body:bad name}"
                    )
                },
                hook_bodies=["lint.py"],
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("malformed placeholder", refusal)
            self.assertIn("hook-body:<name>", refusal)
            self.assertIn("[a-zA-Z0-9_-]+", refusal)

    def test_placeholder_with_path_traversal_refused(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={
                    "cmd.kiro.hook": _run_command_hook(
                        command="${hook-body:../etc/passwd}"
                    )
                },
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("malformed placeholder", refusal)


class UnresolvablePlaceholderRefusal(unittest.TestCase):
    """T-C2.5 — well-formed ``${hook-body:<name>}`` whose ``<name>``
    is not a hook-body the pack ships."""

    def test_unknown_hook_body_refused(self) -> None:
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={
                    "cmd.kiro.hook": _run_command_hook(
                        command="${hook-body:nonexistent}"
                    )
                },
                hook_bodies=["lint.py"],  # not "nonexistent"
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal)
            self.assertIn("references unknown hook-body", refusal)
            self.assertIn("nonexistent", refusal)
            self.assertIn("no such hook-body in pack", refusal)


class PlaceholderScanFencedToCommand(unittest.TestCase):
    """RFC § Substitution rules clause 1 — only ``then.command`` is scanned.

    A placeholder-shaped string in ``then.prompt`` (askAgent), ``name``,
    or ``description`` is passed through verbatim and never resolved
    or refused. Pinning the fence here means a future change widening
    the scan would have to rewrite this test."""

    def test_prompt_field_with_placeholder_text_passes(self) -> None:
        with TemporaryDirectory() as raw:
            body = _ask_agent_hook(prompt="The marker ${hook-body:unknown} is just text.")
            pack = _make_pack(Path(raw), hooks={"hook.kiro.hook": body})
            self.assertIsNone(_run_rail(pack))


class E3VocabularyTests(unittest.TestCase):
    """T2 (RFC-0022): E3 vocabulary replaces the RFC-0005 best-guess list.

    Old terms (fileSave, fileEdit, manualTrigger) must be rejected;
    E3 terms (fileEdited, sessionStart, etc.) must be accepted.
    """

    def test_old_vocabulary_rejected(self) -> None:
        """fileSave is not in the E3 vocabulary — must be refused."""
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="fileSave")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal, "fileSave must be refused with E3 vocabulary")
            self.assertIn("fileSave", refusal)
            self.assertIn("ide-event-vocabulary", refusal)

    def test_old_vocabulary_rejected_file_edit(self) -> None:
        """fileEdit and manualTrigger are not in the E3 vocabulary."""
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="fileEdit")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal, "fileEdit must be refused with E3 vocabulary")
            self.assertIn("fileEdit", refusal)

        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="manualTrigger")},
            )
            refusal = _run_rail(pack)
            self.assertIsNotNone(refusal, "manualTrigger must be refused with E3 vocabulary")
            self.assertIn("manualTrigger", refusal)

    def test_e3_vocabulary_accepted(self) -> None:
        """fileEdited is in the E3 vocabulary — must pass."""
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="fileEdited")},
            )
            self.assertIsNone(_run_rail(pack), "fileEdited must pass with E3 vocabulary")

    def test_e3_session_start_accepted(self) -> None:
        """sessionStart is the last term in the E3 list — most likely to be
        truncated in a copy-paste error; pin it explicitly."""
        with TemporaryDirectory() as raw:
            pack = _make_pack(
                Path(raw),
                hooks={"hook.kiro.hook": _ask_agent_hook(when_type="sessionStart")},
            )
            self.assertIsNone(_run_rail(pack), "sessionStart must pass with E3 vocabulary")


if __name__ == "__main__":
    unittest.main()
