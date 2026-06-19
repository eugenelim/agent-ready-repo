"""Gate for the core pack's work-loop activation hook (matched pair).

The `core` pack ships a per-prompt "use the work-loop skill" nudge as two
artifacts: a `hook-wiring` (`UserPromptSubmit`) + hook body for the
hook-wiring-consuming adapters, and a standalone `kiro-ide-hook`
(`promptSubmit` + `askAgent`) for Kiro IDE.

This module is the *only* thing that gates the kiro-ide-hook rail and the
real-pack projection in CI: `make build-check` / `lint-packs` / the `make
validate` target never run `check_kiro_ide_hook` against `core` (the rail is
reachable only via the per-pack `agentbundle validate <pack>` CLI), and CI
does not auto-discover pytest. The module is wired explicitly in
`.github/workflows/build-check.yml`.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_PACK = REPO_ROOT / "packs" / "core"
CONTRACT = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
KIRO_HOOK = CORE_PACK / ".apm" / "kiro-ide-hooks" / "work-loop-check.kiro.hook"
HOOK_BODY = CORE_PACK / ".apm" / "hooks" / "work-loop-check.py"


def _kiro_ide_hook_contract() -> dict:
    """The real on-disk kiro-ide-hook projection rule — sourced, not retyped,
    so the `<pack>--<name>` separator is the contract's, not the test's."""
    contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
    return contract["adapter"]["kiro-ide"]["projections"]["kiro-ide-hook"]


class TestCoreWorkLoopHook(unittest.TestCase):
    def test_kiro_ide_hook_passes_validate_rail(self) -> None:
        """check_kiro_ide_hook returns None for core against the real vocab."""
        from agentbundle.build.scope_rails import check_kiro_ide_hook

        rule = _kiro_ide_hook_contract()
        refusal = check_kiro_ide_hook(
            CORE_PACK,
            "core",
            target_adapters=("kiro-ide",),
            ide_event_vocabulary=rule["ide-event-vocabulary"],
            ide_action_vocabulary=rule["ide-action-vocabulary"],
        )
        self.assertIsNone(refusal, msg=refusal)

    def test_kiro_ide_hook_projects_to_real_contract_path(self) -> None:
        """The shipped projector emits the flat `core--<name>` path with the
        promptSubmit / askAgent shape — using the contract's own template."""
        from agentbundle.build.projections.kiro_ide_hook import project

        target_template = _kiro_ide_hook_contract()["target"]["repo"]
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            project(
                CORE_PACK,
                out,
                target_template=target_template,
                hook_body_target_dir="tools/hooks",
            )
            projected = out / ".kiro" / "hooks" / "core--work-loop-check.kiro.hook"
            self.assertTrue(projected.is_file(), f"missing {projected}")
            body = json.loads(projected.read_text(encoding="utf-8"))

        self.assertEqual(body["when"]["type"], "promptSubmit")
        self.assertEqual(body["then"]["type"], "askAgent")
        self.assertTrue(body["then"].get("prompt", "").strip(), "empty then.prompt")

    def test_hook_body_runs_clean(self) -> None:
        """The body invokes as documented: exit 0, non-empty stdout, mentions
        work-loop, and is at most 6 lines (the spec's concision bar)."""
        result = subprocess.run(
            [sys.executable, str(HOOK_BODY)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout = result.stdout.strip()
        self.assertTrue(stdout, "empty stdout")
        self.assertIn("work-loop", stdout.lower())
        # spec work-loop-activation-hook AC1: the reminder is bounded at 6 lines.
        # A failure here means the REMINDER grew past that cap — trim it, don't
        # bump the bound (the nudge fires on every prompt).
        self.assertLessEqual(len(stdout.splitlines()), 6)

    def test_both_messages_carry_the_same_instruction(self) -> None:
        """The two reminders (hook-body stdout + .kiro.hook prompt) carry the
        same core instruction. Asserting the shared loop phrase — not just the
        `work-loop` header — is the enforceable floor against the two literals
        drifting apart (they live in separate files by mechanism necessity)."""
        prompt = json.loads(KIRO_HOOK.read_text(encoding="utf-8"))["then"]["prompt"]
        stdout = subprocess.run(
            [sys.executable, str(HOOK_BODY)],
            capture_output=True,
            text=True,
        ).stdout
        for text in (prompt, stdout):
            self.assertIn("work-loop", text.lower())
            self.assertIn("plan -> execute -> verify -> review", text.lower())


if __name__ == "__main__":
    unittest.main()
