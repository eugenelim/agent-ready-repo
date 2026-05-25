"""T-C3 (RFC-0005 kiro-ide-hook): phase order + projector module.

Covers:
  - Phase order extension (PHASE_ORDER ships kiro-ide-hook between
    hook-wiring and command).
  - askAgent byte-copy shortcut (no `${` in raw + then.type ==
    "askAgent" → SHA equality between source and target).
  - runCommand placeholder expansion (single-pass, verbatim,
    `${hook-body:<name>}` → `./<hook-body-dir>/<actual-filename>`).
  - Defense-in-depth refusals on malformed / unresolvable placeholders
    at projection time (even though validate covers them upstream).
  - Output target template substitution: `<pack>` ← pack dir name,
    `<name>` ← hook file's bare name (extension stripped).
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_pack(
    root: Path,
    pack_name: str = "test-pack",
    kiro_ide_hooks: dict[str, dict] | None = None,
    hook_bodies: dict[str, str] | None = None,
) -> Path:
    pack = root / pack_name
    if kiro_ide_hooks is not None:
        kiro_dir = pack / ".apm" / "kiro-ide-hooks"
        kiro_dir.mkdir(parents=True)
        for filename, body in kiro_ide_hooks.items():
            (kiro_dir / filename).write_text(
                json.dumps(body, indent=2) + "\n", encoding="utf-8"
            )
    if hook_bodies is not None:
        body_dir = pack / ".apm" / "hooks"
        body_dir.mkdir(parents=True)
        for filename, content in hook_bodies.items():
            (body_dir / filename).write_text(content, encoding="utf-8")
    return pack


class PhaseOrderTests(unittest.TestCase):
    """Phase order has kiro-ide-hook between hook-wiring and command."""

    def test_kiro_ide_hook_after_hook_wiring(self) -> None:
        from agentbundle.build.phase_order import PHASE_ORDER

        self.assertGreater(
            PHASE_ORDER.index("kiro-ide-hook"),
            PHASE_ORDER.index("hook-wiring"),
        )

    def test_kiro_ide_hook_before_command(self) -> None:
        from agentbundle.build.phase_order import PHASE_ORDER

        self.assertLess(
            PHASE_ORDER.index("kiro-ide-hook"),
            PHASE_ORDER.index("command"),
        )

    def test_phase_order_full_sequence(self) -> None:
        from agentbundle.build.phase_order import PHASE_ORDER

        self.assertEqual(
            PHASE_ORDER,
            (
                "hook-body",
                "agent",
                "hook-wiring",
                "kiro-ide-hook",
                "command",
                "skill",
            ),
        )


class AskAgentByteCopyTests(unittest.TestCase):
    """askAgent hooks with no `${` in raw bytes byte-copy verbatim;
    assert SHA equality between source and target.

    This pins RFC-0005 § Substitution rules clause 1 — only
    then.command is scanned — by ensuring askAgent files (no command
    field) round-trip exactly."""

    def test_ask_agent_basic_byte_copies(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "ask.kiro.hook": {
                        "name": "Lint on save",
                        "description": "Run ruff.",
                        "version": "1",
                        "when": {"type": "fileSave", "patterns": ["**/*.py"]},
                        "then": {"type": "askAgent", "prompt": "Lint!"},
                    }
                },
            )
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )

            source = pack / ".apm" / "kiro-ide-hooks" / "ask.kiro.hook"
            projected = output / ".kiro" / "hooks" / "test-pack" / "ask.kiro.hook"
            self.assertTrue(projected.exists())
            # SHA equality — byte-copy preserves source exactly.
            self.assertEqual(_sha(source), _sha(projected))

    def test_target_template_substitutes_pack_and_name(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                pack_name="my-pack",
                kiro_ide_hooks={
                    "deep-hook.kiro.hook": {
                        "name": "T",
                        "version": "1",
                        "when": {"type": "fileSave"},
                        "then": {"type": "askAgent", "prompt": "P"},
                    }
                },
            )
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )
            self.assertTrue(
                (output / ".kiro" / "hooks" / "my-pack" / "deep-hook.kiro.hook").exists()
            )


class RunCommandPlaceholderExpansionTests(unittest.TestCase):
    """runCommand hooks expand `${hook-body:<name>}` to the projected
    path under the configured hook-body target directory."""

    def test_single_placeholder_expands_to_workspace_relative_path(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "cmd.kiro.hook": {
                        "name": "Lint via command",
                        "version": "1",
                        "when": {"type": "fileSave", "patterns": ["**/*.py"]},
                        "then": {
                            "type": "runCommand",
                            "command": "${hook-body:lint}",
                        },
                    }
                },
                hook_bodies={"lint.py": "#!/bin/sh\n"},
            )
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )

            projected = output / ".kiro" / "hooks" / "test-pack" / "cmd.kiro.hook"
            body = json.loads(projected.read_text(encoding="utf-8"))
            self.assertEqual(body["then"]["command"], "./tools/hooks/lint.py")
            # And no residual placeholder syntax.
            self.assertNotIn("${", projected.read_text(encoding="utf-8"))

    def test_multiple_placeholders_all_resolve(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "multi.kiro.hook": {
                        "name": "Multi",
                        "version": "1",
                        "when": {"type": "fileSave"},
                        "then": {
                            "type": "runCommand",
                            "command": "${hook-body:lint} && ${hook-body:format}",
                        },
                    }
                },
                hook_bodies={"lint.py": "x", "format.sh": "y"},
            )
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )
            body = json.loads(
                (output / ".kiro" / "hooks" / "test-pack" / "multi.kiro.hook")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(
                body["then"]["command"],
                "./tools/hooks/lint.py && ./tools/hooks/format.sh",
            )


class ProjectionDefenseInDepthRefusals(unittest.TestCase):
    """The projector defense-in-depth-refuses on cases the validate
    rail already covers. Reachable only when callers skip validate."""

    def test_malformed_placeholder_refuses(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "bad.kiro.hook": {
                        "name": "Bad",
                        "version": "1",
                        "when": {"type": "fileSave"},
                        "then": {
                            "type": "runCommand",
                            "command": "${hook-body:bad name}",
                        },
                    }
                },
                hook_bodies={"lint.py": "x"},
            )
            with self.assertRaises(kiro_ide_hook.KiroIdeHookRefusal) as cm:
                kiro_ide_hook.project(
                    pack,
                    root / "out",
                    target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                    hook_body_target_dir="tools/hooks",
                )
            self.assertIn("malformed placeholder", str(cm.exception))

    def test_unresolvable_placeholder_refuses(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "u.kiro.hook": {
                        "name": "U",
                        "version": "1",
                        "when": {"type": "fileSave"},
                        "then": {
                            "type": "runCommand",
                            "command": "${hook-body:missing}",
                        },
                    }
                },
                hook_bodies={"present.py": "x"},
            )
            with self.assertRaises(kiro_ide_hook.KiroIdeHookRefusal) as cm:
                kiro_ide_hook.project(
                    pack,
                    root / "out",
                    target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                    hook_body_target_dir="tools/hooks",
                )
            self.assertIn("unknown hook-body", str(cm.exception))


class PromptFieldPreservedThroughProjection(unittest.TestCase):
    """RFC § Substitution rules clause 1 + spec AC: a placeholder-
    shaped string in then.prompt passes through projection
    unchanged. Pin string-content preservation (byte-for-byte shape
    isn't promised when the parse-re-emit branch fires, only the
    string content)."""

    def test_prompt_placeholder_text_survives_projection(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_pack(
                root,
                kiro_ide_hooks={
                    "ask.kiro.hook": {
                        "name": "Mentions placeholder",
                        "version": "1",
                        "when": {"type": "fileSave"},
                        "then": {
                            "type": "askAgent",
                            "prompt": "The marker ${hook-body:unknown} should survive.",
                        },
                    },
                },
            )
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )
            body = json.loads(
                (output / ".kiro" / "hooks" / "test-pack" / "ask.kiro.hook")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(
                body["then"]["prompt"],
                "The marker ${hook-body:unknown} should survive.",
            )


class EmptyBareNameRefuses(unittest.TestCase):
    """A file named exactly ``.kiro.hook`` produces an empty
    ``<name>`` after stripping the extension; the projector refuses
    defense-in-depth (the validate rail catches it upstream too)."""

    def test_empty_bare_name_refuses(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = root / "test-pack"
            (pack / ".apm" / "kiro-ide-hooks").mkdir(parents=True)
            # File named exactly `.kiro.hook` — empty bare name.
            (pack / ".apm" / "kiro-ide-hooks" / ".kiro.hook").write_text(
                json.dumps({
                    "name": "Pathological",
                    "version": "1",
                    "when": {"type": "fileSave"},
                    "then": {"type": "askAgent", "prompt": "x"},
                }) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(kiro_ide_hook.KiroIdeHookRefusal) as cm:
                kiro_ide_hook.project(
                    pack,
                    root / "out",
                    target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                    hook_body_target_dir="tools/hooks",
                )
            self.assertIn("empty bare name", str(cm.exception))


class NoOpWhenSourceDirAbsent(unittest.TestCase):
    """`.apm/kiro-ide-hooks/` absent — projector returns silently."""

    def test_no_source_dir_no_op(self) -> None:
        from agentbundle.build.projections import kiro_ide_hook

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = root / "empty-pack"
            pack.mkdir()
            output = root / "out"
            kiro_ide_hook.project(
                pack,
                output,
                target_template=".kiro/hooks/<pack>/<name>.kiro.hook",
                hook_body_target_dir="tools/hooks",
            )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
