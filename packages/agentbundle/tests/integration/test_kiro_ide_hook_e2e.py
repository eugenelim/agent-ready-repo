"""T-C4 (RFC-0005 kiro-ide-hook): end-to-end wiring.

Pins that the kiro adapter's ``project()`` dispatches a v0.4-shaped
synthetic contract through ``_dispatch_table_form`` into the new
``projections.kiro_ide_hook.project`` module. The on-disk v0.3
contract carries no ``kiro-ide-hook`` projection (probe-gated; lands
at T-CONTRACT), so these tests synthesise the v0.4 declaration in
memory.

The test fixture pack ships:
  - one ``.apm/hooks/lint.py`` (the placeholder target)
  - one askAgent ``.kiro.hook`` (byte-copy path)
  - one runCommand ``.kiro.hook`` with ``${hook-body:lint}`` (parse,
    expand, emit path)
"""

from __future__ import annotations

import copy
import json
import tomllib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[4]
V0_3_CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _synthesised_v0_4_contract() -> dict:
    """Load the shipped v0.3 contract and add the v0.4 kiro-ide-hook
    declaration in memory. Same shape T-CONTRACT will ship on disk."""
    contract = tomllib.loads(V0_3_CONTRACT_PATH.read_text(encoding="utf-8"))
    contract["primitive"]["kiro-ide-hook"] = {"source-path": ".apm/kiro-ide-hooks/"}
    contract["adapter"]["kiro"]["projections"]["kiro-ide-hook"] = {
        "mode": "direct-file",
        "target": {"repo": ".kiro/hooks/<pack>/<name>.kiro.hook"},
        "on-conflict": "prompt-then-preserve",
        "ide-event-vocabulary": [
            "fileCreated", "fileEdit", "fileSave", "fileDeleted",
            "promptSubmit", "agentStop", "preToolUse", "postToolUse",
            "preTaskExecution", "postTaskExecution", "manualTrigger",
        ],
        "ide-action-vocabulary": ["askAgent", "runCommand"],
    }
    return contract


def _make_fixture_pack(root: Path, pack_name: str = "kiro-ide-hooks-basic") -> Path:
    pack = root / pack_name
    # hook-body — the placeholder target.
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "lint.py").write_text(
        "#!/usr/bin/env python3\nprint('lint')\n", encoding="utf-8"
    )
    # askAgent hook (byte-copy path).
    (pack / ".apm" / "kiro-ide-hooks").mkdir(parents=True)
    (pack / ".apm" / "kiro-ide-hooks" / "lint-prompt.kiro.hook").write_text(
        json.dumps({
            "name": "Lint on save",
            "description": "Ask the agent to lint.",
            "version": "1",
            "when": {"type": "fileSave", "patterns": ["**/*.py"]},
            "then": {"type": "askAgent", "prompt": "Lint the saved file."},
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    # runCommand hook (parse, expand, emit path).
    (pack / ".apm" / "kiro-ide-hooks" / "lint-command.kiro.hook").write_text(
        json.dumps({
            "name": "Lint via command",
            "description": "Invoke the lint hook-body directly.",
            "version": "1",
            "when": {"type": "fileSave", "patterns": ["**/*.py"]},
            "then": {
                "type": "runCommand",
                "command": "${hook-body:lint}",
            },
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    return pack


class KiroAdapterDispatchesKiroIdeHook(unittest.TestCase):
    """The kiro adapter's project() routes kiro-ide-hook through the
    projection module under a v0.4-shaped contract."""

    def test_e2e_synthetic_v0_4_contract_projects_both_hook_shapes(self) -> None:
        from agentbundle.build.adapters import kiro as kiro_adapter

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_fixture_pack(root)
            output = root / "out"

            contract = _synthesised_v0_4_contract()
            kiro_adapter.project(pack, contract, output)

            # askAgent — byte-copy preserves source exactly.
            ask_path = output / ".kiro" / "hooks" / "kiro-ide-hooks-basic" / "lint-prompt.kiro.hook"
            self.assertTrue(ask_path.exists())
            ask_body = json.loads(ask_path.read_text(encoding="utf-8"))
            self.assertEqual(ask_body["then"]["type"], "askAgent")
            self.assertEqual(ask_body["then"]["prompt"], "Lint the saved file.")

            # runCommand — placeholder expanded to ./tools/hooks/lint.py
            # (Kiro adapter's legacy hook-body target is tools/hooks/).
            cmd_path = output / ".kiro" / "hooks" / "kiro-ide-hooks-basic" / "lint-command.kiro.hook"
            self.assertTrue(cmd_path.exists())
            cmd_body = json.loads(cmd_path.read_text(encoding="utf-8"))
            self.assertEqual(cmd_body["then"]["command"], "./tools/hooks/lint.py")

            # The hook-body itself also projects (phase order ensures
            # hook-body runs before kiro-ide-hook).
            self.assertTrue((output / "tools" / "hooks" / "lint.py").exists())

    def test_pre_v0_4_contract_skips_kiro_ide_hook_silently(self) -> None:
        """The shipped v0.3 contract has no kiro-ide-hook projection.
        A pack carrying .apm/kiro-ide-hooks/ but validated against
        v0.3 simply doesn't project that primitive — _iter_primitives
        won't yield it because the contract doesn't declare the
        projection. The hook-body still projects (phase order
        unchanged)."""
        from agentbundle.build.adapters import kiro as kiro_adapter

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_fixture_pack(root)
            output = root / "out"
            contract = tomllib.loads(V0_3_CONTRACT_PATH.read_text(encoding="utf-8"))
            kiro_adapter.project(pack, contract, output)
            self.assertFalse((output / ".kiro" / "hooks").exists())
            # hook-body still projects unaffected.
            self.assertTrue((output / "tools" / "hooks" / "lint.py").exists())


class ValidateCommandRailFires(unittest.TestCase):
    """commands/validate.py invokes check_kiro_ide_hook when a pack
    ships .apm/kiro-ide-hooks/. Test by malforming a hook and
    asserting the validate command refuses."""

    def test_malformed_kiro_ide_hook_refused_via_validate_command(self) -> None:
        import io
        import sys
        from contextlib import redirect_stderr

        with TemporaryDirectory() as raw:
            root = Path(raw)
            pack = _make_fixture_pack(root)
            # Drop a required field to trigger refusal path 1.
            broken = pack / ".apm" / "kiro-ide-hooks" / "broken.kiro.hook"
            broken.write_text(json.dumps({"description": "no name no version"}), encoding="utf-8")

            # pack.toml is needed for validate.run.
            (pack / "pack.toml").write_text(
                '[pack]\nname = "kiro-ide-hooks-basic"\nversion = "0.1.0"\n'
                '[pack.adapter-contract]\nversion = "0.3"\n'
                '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
                encoding="utf-8",
            )

            from agentbundle.commands.validate import run as validate_run
            import argparse
            ns = argparse.Namespace(pack_path=str(pack), strict=False)

            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = validate_run(ns)
            stderr = buf.getvalue()

            self.assertNotEqual(rc, 0, msg="validate should refuse on malformed kiro-ide-hook")
            self.assertIn("kiro-ide-hook broken.kiro.hook", stderr)
            self.assertIn("missing required field", stderr)


if __name__ == "__main__":
    unittest.main()
