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
            # `core` ships .apm/hook-wiring/session-start.toml so the
            # file MUST materialise — a conditional check would let a
            # regression that drops the merge-json dispatch ship green.
            hooks_json = adopter / ".codex" / "hooks.json"
            self.assertTrue(
                hooks_json.exists(),
                f"expected .codex/hooks.json from core's hook-wiring TOMLs",
            )
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
            self.assertIn("hooks", data)
            self.assertGreater(
                len(data["hooks"]), 0,
                "expected at least one event entry under 'hooks'",
            )

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


class DualScopeWarningEndToEnd(unittest.TestCase):
    """Dual-scope path: ``--force + other_already`` triggers
    ``scopes_to_install = ['repo', 'user']``. Warning rail must fire
    per-scope for whichever scope's resolved adapter has dropped modes.

    Sub-case to pin (iter-2 reviewer Concern #1): when ``requested_scope
    == 'user'`` and the dual-scope path activates, Step 3c does NOT
    resolve ``repo_target_adapter``. The warning hook must late-resolve
    it; otherwise the repo-side warning silently drops even though the
    install lands at repo scope.
    """

    PACK_TOML = """
[pack]
name = "dual-warn"
version = "0.1.0"

[pack.adapter-contract]
version = "0.8"

[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
allowed-adapters = ["claude-code", "kiro", "codex"]
"""

    def _stage_pack(self, root: Path) -> Path:
        pack = root / "packs" / "dual-warn"
        pack.mkdir(parents=True)
        (pack / "pack.toml").write_text(self.PACK_TOML, encoding="utf-8")
        (pack / ".apm" / "commands").mkdir(parents=True)
        # Ship a command — codex drops this; the warning must name it
        # at BOTH scopes when the dual-scope path fires.
        (pack / ".apm" / "commands" / "do-thing.md").write_text(
            "# do-thing\n", encoding="utf-8"
        )
        return pack

    def _install(self, **kwargs) -> tuple[int, str, str]:
        import argparse
        import contextlib

        from agentbundle.commands import install

        install._clear_dropped_warning_seen()
        install._clear_inband_detection_seen()

        args = argparse.Namespace(**kwargs)
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(
            err_buf
        ):
            rc = install.run(args)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def _common_args(self, *, catalogue: Path, output: Path) -> dict:
        return dict(
            pack="dual-warn",
            catalogue=str(catalogue),
            output=str(output),
            force=False,
            adapter="codex",
            emit_install_routes=False,
            force_merge=False,
        )

    def test_dual_scope_warning_fires_per_scope_via_user_force(self) -> None:
        """Install at repo first (no force), then install at user with
        --force — this hits the dual-scope path with ``requested_scope
        == 'user'``. The fix resolves repo_target_adapter late so the
        repo-side warning fires too. Without the late-resolution, the
        repo warning is silently skipped."""
        from agentbundle.commands import install

        # Stage a $HOME so user-scope writes don't touch the adopter's
        # real home directory.
        with TemporaryDirectory() as raw:
            cat = Path(raw) / "cat"
            cat.mkdir()
            self._stage_pack(cat)
            repo = Path(raw) / "repo"
            repo.mkdir()
            fake_home = Path(raw) / "home"
            fake_home.mkdir()

            import os
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = str(fake_home)
            try:
                # First install at repo scope (no force).
                rc, _, err1 = self._install(
                    **self._common_args(catalogue=cat, output=repo),
                    scope="repo",
                )
                self.assertEqual(rc, 0, f"repo install failed: {err1}")
                # The repo-side warning fires here.
                self.assertIn("codex projects as 'dropped'", err1)

                # Now install at user scope WITH --force.
                # This activates the dual-scope path:
                # scopes_to_install = ['repo', 'user'].
                # Without the late-resolution fix, repo_target_adapter
                # is None and the repo-side warning is skipped silently.
                install._clear_dropped_warning_seen()
                rc, _, err2 = self._install(
                    pack="dual-warn",
                    catalogue=str(cat),
                    output=str(repo),
                    scope="user",
                    force=True,
                    adapter="codex",
                )
                self.assertEqual(rc, 0, f"dual-scope install failed: {err2}")
                # Two warnings must appear — one per scope.
                self.assertEqual(
                    err2.count("codex projects as 'dropped'"),
                    2,
                    f"expected dual-scope warning to fire per scope; "
                    f"saw {err2.count('codex projects as ' + chr(0x27) + 'dropped' + chr(0x27))} occurrence(s):\n{err2}",
                )
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home
                else:
                    os.environ.pop("HOME", None)


class KiroPerFileDropEndToEnd(unittest.TestCase):
    """T6 of docs/specs/incompatible-hook-event-drop.

    Installs core via kiro at repo scope and asserts:
      - rc 0
      - stderr contains the exact three-clause warning (built via
        _drop_warning.format_drop_message so the test stays in sync
        with any formatter wording change — single source of truth pin).
      - each agent in core/.apm/agents/ produces a kiro agent JSON at
        <tmp>/.kiro/agents/<basename>.json
      - <tmp>/.kiro/skills/<skill>/SKILL.md exists for each core skill
      - no kiro agent JSON contains a top-level hooks.SessionStart key

    The positive-control test in ClaudeCodeSessionStartPositiveControl
    pins that the drop is per-adapter, not blanket.
    """

    def test_install_core_via_kiro_emits_three_clause_warning_and_projects_other_primitives(
        self,
    ) -> None:
        import tomllib as _tomllib

        from agentbundle.build.main import _read_bundled
        from agentbundle.commands._drop_warning import (
            enumerate_event_dropped_wirings,
            format_drop_message,
        )
        from agentbundle.commands.install import (
            _enumerate_compatible_primitives,
            _enumerate_dropped_primitives,
        )

        contract = _tomllib.loads(_read_bundled("adapter.toml"))
        pack_dir = PACKS_DIR / "core"

        # Build expected warning via the formatter — single source of truth
        # pin (spec AC10).
        expected_warning = format_drop_message(
            pack_name="core",
            adapter="kiro",
            dropped_counts=_enumerate_dropped_primitives(pack_dir, "kiro", contract),
            compatible_types=_enumerate_compatible_primitives(pack_dir, "kiro", contract),
            event_drops=enumerate_event_dropped_wirings(pack_dir, "kiro", contract),
            mode="install_warning",
        )

        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("kiro", adopter)

            self.assertEqual(
                rc, 0, f"install returned non-zero:\nstdout={stdout}\nstderr={stderr}"
            )

            # Exact three-clause warning in stderr.
            self.assertIn(
                expected_warning,
                stderr,
                f"expected three-clause kiro warning in stderr.\n"
                f"Expected substring:\n  {expected_warning}\n"
                f"Got stderr:\n  {stderr}",
            )

            # Each agent in core/.apm/agents/ produces a kiro agent JSON.
            agents_src = sorted((pack_dir / ".apm" / "agents").glob("*.md"))
            self.assertGreater(len(agents_src), 0, "no agents found in core pack")
            kiro_agents_dir = adopter / ".kiro" / "agents"
            for agent_md in agents_src:
                expected_json = kiro_agents_dir / (agent_md.stem + ".json")
                self.assertTrue(
                    expected_json.exists(),
                    f"expected kiro agent JSON at {expected_json.relative_to(adopter)}"
                    f" (derived from {agent_md.name})",
                )

            # Each skill in core/.apm/skills/ produces a SKILL.md.
            skills_src = [
                p for p in (pack_dir / ".apm" / "skills").iterdir() if p.is_dir()
            ]
            self.assertGreater(len(skills_src), 0, "no skills found in core pack")
            for skill_dir in skills_src:
                expected_skill_md = adopter / ".kiro" / "skills" / skill_dir.name / "SKILL.md"
                self.assertTrue(
                    expected_skill_md.exists(),
                    f"expected skill at {expected_skill_md.relative_to(adopter)}"
                    f" (derived from skill {skill_dir.name})",
                )

            # No kiro agent JSON contains a top-level hooks.SessionStart key.
            for json_path in sorted(kiro_agents_dir.glob("*.json")):
                data = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertNotIn(
                    "SessionStart",
                    data.get("hooks", {}),
                    f"{json_path.name} unexpectedly contains hooks.SessionStart "
                    f"— the session-start wiring was supposed to be dropped",
                )


class ClaudeCodeSessionStartPositiveControl(unittest.TestCase):
    """T6 positive control: claude-code at repo scope writes SessionStart.

    Pins that the per-file drop is per-adapter, not blanket. The kiro
    install above drops hooks/session-start.toml; the claude-code install
    here must project it (spec AC10).
    """

    def test_install_core_via_claude_code_writes_sessionstart_positive_control(
        self,
    ) -> None:
        with TemporaryDirectory() as raw:
            adopter = Path(raw) / "adopter"
            adopter.mkdir()
            rc, stdout, stderr = _install_core_via("claude-code", adopter)

            self.assertEqual(
                rc, 0, f"install returned non-zero:\nstdout={stdout}\nstderr={stderr}"
            )

            # For claude-code at repo scope (per-IDE path, not
            # --emit-install-routes), hook-wiring merges into
            # .claude/settings.local.json per
            # [adapter."claude-code".projections.hook-wiring].target.repo
            # in _data/adapter.toml.
            hook_wiring_target = adopter / ".claude" / "settings.local.json"
            self.assertTrue(
                hook_wiring_target.exists(),
                f"expected hook-wiring target at "
                f"{hook_wiring_target.relative_to(adopter)} — "
                f"claude-code repo-scope hook-wiring did not project",
            )

            data = json.loads(hook_wiring_target.read_text(encoding="utf-8"))
            session_start_entries = data.get("hooks", {}).get("SessionStart")
            self.assertTrue(
                session_start_entries,
                f"expected non-empty hooks.SessionStart in "
                f"{hook_wiring_target.relative_to(adopter)}; "
                f"got: {session_start_entries!r}",
            )


if __name__ == "__main__":
    unittest.main()
