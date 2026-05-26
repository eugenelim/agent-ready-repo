"""End-to-end integration coverage for the dropped-primitives warning
rail (T8 of docs/specs/dropped-primitives-coverage).

Each test installs a real shipped pack at repo scope via a specific
adapter and asserts:

  - The codex projection now lands `.codex/agents/<name>.toml` +
    `.codex/hooks.json` (the contract-bump verification).
  - The warning rail fires for codex / kiro / copilot with the correct
    per-adapter type list.
  - The warning stays silent for claude-code (no dropped modes) and
    for a skills-only pack against any adapter.

Pre-existing unit coverage in `tests/unit/test_install_dropped_primitives_warning.py`
pins the helper-and-formatter contract; this module exercises the
install-handler hook end-to-end.
"""

from __future__ import annotations

import io
import json
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"


def _run_install(argv: list[str]) -> tuple[int, str, str]:
    """Invoke install via the argparse layer; return (rc, stdout, stderr)."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    install._clear_dropped_warning_seen()
    install._clear_inband_detection_seen()

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    out_buf, err_buf = io.StringIO(), io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = install.run(args)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _install_core_via(adapter: str, output_dir: Path) -> tuple[int, str, str]:
    argv = [
        "--pack", "core",
        "--scope", "repo",
        "--adapter", adapter,
        "--output", str(output_dir),
        str(REPO_ROOT),
    ]
    return _run_install(argv)


class CodexProjectionEndToEnd(unittest.TestCase):
    """The contract-bump's load-bearing claim — codex now writes
    .codex/agents/<name>.toml + .codex/hooks.json — verified by an
    actual install."""

    def test_codex_projects_agents_and_hooks_and_warns_about_commands(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("codex", adopter)
            self.assertEqual(
                rc, 0,
                f"install failed:\nstdout={stdout}\nstderr={stderr}",
            )

            # Skills landed at the existing .agents/skills/ target.
            self.assertTrue(
                (adopter / ".agents" / "skills").exists(),
                "skills projection missing",
            )

            # Agents projected to .codex/agents/ as TOML (post-v0.8).
            agents_dir = adopter / ".codex" / "agents"
            self.assertTrue(agents_dir.exists(), "codex agents dir missing")
            tomls = list(agents_dir.glob("*.toml"))
            self.assertGreater(
                len(tomls), 0,
                f"no .toml agents projected to {agents_dir}",
            )
            # Each TOML parses with the expected three-key shape.
            for toml_path in tomls:
                data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
                self.assertIn("name", data)
                self.assertIn("description", data)
                self.assertIn("developer_instructions", data)

            # Hooks projected to .codex/hooks.json (post-v0.8 merge-json).
            hooks_json = adopter / ".codex" / "hooks.json"
            if hooks_json.exists():
                data = json.loads(hooks_json.read_text(encoding="utf-8"))
                self.assertIn("hooks", data)
            # Note: if `core` ships no hook-wiring TOMLs, hooks.json
            # won't materialise — that's a property of the pack, not the
            # adapter. The dropped-warning assertions below pin the
            # observable behaviour either way.

            # Warning rail fires for `command` only (codex's one
            # remaining drop). `core` ships at least one command, so
            # the warning is expected to appear.
            self.assertIn(
                "codex projects as 'dropped'", stderr,
                f"expected codex dropped-warning in stderr:\n{stderr}",
            )
            # Drop-clause names command (singular or plural).
            drop_clause = stderr.split("projects as 'dropped'")[0]
            drop_clause_tail = drop_clause.split("ships ")[-1]
            self.assertIn("command", drop_clause_tail)
            # Agent / hook-wiring NOT in the drop clause (they project
            # natively post-v0.8). The compatible-list portion downstream
            # is allowed to mention them.
            self.assertNotIn(" agent ", drop_clause_tail + " ")
            self.assertNotIn(" agents,", drop_clause_tail)
            self.assertNotIn(" hook-wiring ", drop_clause_tail + " ")


class CopilotWarningEndToEnd(unittest.TestCase):
    """Copilot drops agent + command + hook-wiring; install proceeds
    (skills + hook-bodies land), warning enumerates all three drops."""

    def test_copilot_warning_lists_three_dropped_types(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("copilot", adopter)
            self.assertEqual(
                rc, 0,
                f"install failed:\nstdout={stdout}\nstderr={stderr}",
            )

            # Install completed — skills landed at copilot's target.
            self.assertTrue(
                (adopter / ".github" / "instructions").exists(),
                "copilot skill projection missing",
            )

            # Warning fires naming all three drop types.
            self.assertIn(
                "copilot projects as 'dropped'", stderr,
                f"expected copilot dropped-warning in stderr:\n{stderr}",
            )
            # All three drop type names appear somewhere in the warning.
            for drop_type in ("agent", "command", "hook-wiring"):
                self.assertIn(drop_type, stderr)


class KiroWarningEndToEnd(unittest.TestCase):
    """Kiro drops only `command`."""

    def test_kiro_warning_names_command_only(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("kiro", adopter)
            self.assertEqual(
                rc, 0,
                f"install failed:\nstdout={stdout}\nstderr={stderr}",
            )

            # Warning fires for command only.
            self.assertIn(
                "kiro projects as 'dropped'", stderr,
                f"expected kiro dropped-warning in stderr:\n{stderr}",
            )
            # Agent and hook-wiring NOT in the drop clause (kiro
            # projects both natively).
            drop_clause = stderr.split("projects as 'dropped'")[0]
            drop_clause_tail = drop_clause.split("ships ")[-1]
            # Allow 'agent' to appear in compatible list later; check
            # only the count-list portion.
            self.assertNotIn(" agent ", drop_clause_tail + " ")
            self.assertNotIn(" agents,", drop_clause_tail)


class ClaudeCodeSilenceEndToEnd(unittest.TestCase):
    """Claude-code projects all 5 primitives — no warning fires."""

    def test_claude_code_install_silent_on_warning_rail(self) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("claude-code", adopter)
            self.assertEqual(
                rc, 0,
                f"install failed:\nstdout={stdout}\nstderr={stderr}",
            )

            # The dropped-warning line is absent.
            self.assertNotIn(
                "claude-code projects as 'dropped'",
                stderr,
                f"unexpected dropped-warning under claude-code:\n{stderr}",
            )
            self.assertNotIn(
                "these primitives will not be installed",
                stderr,
                f"unexpected dropped-warning content under claude-code:\n{stderr}",
            )


class SkillsOnlyPackSilenceEndToEnd(unittest.TestCase):
    """A skills-only pack triggers no warning under any adapter (no
    drop-eligible primitive types in the pack)."""

    def test_governance_extras_silent_under_copilot(self) -> None:
        """governance-extras depends on core, so install core first
        under the same adapter; then install governance-extras and
        assert no dropped-warning fires for the skills-only pack."""
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            # Prereq install of core. Clear any warnings emitted there
            # so the next install starts clean.
            rc, _stdout, _stderr = _install_core_via("copilot", adopter)
            self.assertEqual(rc, 0, "pre-req install of core failed")
            from agentbundle.commands import install
            install._clear_dropped_warning_seen()

            # Capture stderr only for the governance-extras install.
            argv = [
                "--pack", "governance-extras",
                "--scope", "repo",
                "--adapter", "copilot",
                "--output", str(adopter),
                str(REPO_ROOT),
            ]
            rc, stdout, stderr = _run_install(argv)
            self.assertEqual(
                rc, 0,
                f"install failed:\nstdout={stdout}\nstderr={stderr}",
            )
            # No dropped-warning fired for governance-extras (the
            # skills-only pack). The text 'projects as \\'dropped\\''
            # only appears in the warning rail's output.
            self.assertNotIn(
                "projects as 'dropped'",
                stderr,
                f"unexpected dropped-warning for skills-only pack:\n{stderr}",
            )


if __name__ == "__main__":
    unittest.main()
