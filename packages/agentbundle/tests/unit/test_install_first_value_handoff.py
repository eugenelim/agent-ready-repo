"""Tests for the install first-value handoff block (spec/agentbundle-first-value-handoff).

Part 1: Unit tests for `_emit_first_value_handoff` directly — pure function,
no install pipeline needed.

Part 2: Integration tests that drive `install.run` end-to-end and assert the
handoff appears (or does not appear) in captured stdout.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
CONVERTERS_PACK_SRC = REPO_ROOT / "packs" / "converters"
CORE_PACK_SRC = REPO_ROOT / "packs" / "core"


# ---------------------------------------------------------------------------
# Part 1: _emit_first_value_handoff unit tests
# ---------------------------------------------------------------------------


def _capture_handoff(first_value: dict) -> str:
    """Call `_emit_first_value_handoff` and return captured stdout."""
    from agentbundle.commands.install import _emit_first_value_handoff

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _emit_first_value_handoff(first_value)
    return buf.getvalue()


_LEVEL_B_DATA = {
    "audience-posture": "non-technical",
    "surfaces": ["claude-code"],
    "prerequisites": [],
    "verification": "Ask the agent about your architecture — it should reply with structural context.",
    "recovery": "If the agent does not respond, re-run adapt-to-project.",
    "level-b": True,
    "starter-task": "Get a plain-language map of how this codebase is organized",
    "starter-prompt": "Describe the architecture of this codebase and create a reference.md snapshot.",
    "expected-result": "A docs/architecture/reference.md file with the codebase's key components.",
    "next-action": "On your next design question, ask: 'Does this approach align with our reference architecture?'",
}

_LEVEL_A_DATA = {
    "audience-posture": "technical",
    "surfaces": ["claude-code"],
    "prerequisites": [],
    "verification": "Run workspace-status and confirm your queue state is displayed.",
    "recovery": "Re-run adapt-to-project to refresh your repo's skill index.",
}


class EmitFirstValueHandoffUnitTests(unittest.TestCase):
    """AC1–AC3: pure-function correctness tests for `_emit_first_value_handoff`."""

    def test_level_b_emits_verify_try_expected_next(self) -> None:
        """AC1: Level B pack emits all four labels when next-action is present."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertIn("Verify:", out)
        self.assertIn("Try:", out)
        self.assertIn("Expected:", out)
        self.assertIn("Next:", out)

    def test_level_b_verify_contains_verification_text(self) -> None:
        """AC1: Verify: line contains the verification field value."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertIn(_LEVEL_B_DATA["verification"], out)

    def test_level_b_try_contains_starter_prompt_verbatim(self) -> None:
        """AC1: Try: line is the verbatim starter-prompt value."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertIn(_LEVEL_B_DATA["starter-prompt"], out)

    def test_level_b_expected_contains_expected_result(self) -> None:
        """AC1: Expected: line contains the expected-result value."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertIn(_LEVEL_B_DATA["expected-result"], out)

    def test_level_b_next_contains_next_action(self) -> None:
        """AC1: Next: line contains the next-action value."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertIn(_LEVEL_B_DATA["next-action"], out)

    def test_level_b_without_next_action_omits_next_line(self) -> None:
        """AC1: When next-action is absent, no Next: line appears."""
        data = {k: v for k, v in _LEVEL_B_DATA.items() if k != "next-action"}
        out = _capture_handoff(data)
        self.assertIn("Verify:", out)
        self.assertIn("Try:", out)
        self.assertIn("Expected:", out)
        self.assertNotIn("Next:", out)

    def test_level_b_blank_line_before_block(self) -> None:
        """AC1: A blank line precedes the handoff block."""
        out = _capture_handoff(_LEVEL_B_DATA)
        self.assertTrue(out.startswith("\n"), "handoff block must begin with a blank line")

    def test_level_a_emits_verify_only(self) -> None:
        """AC2: Level A pack (no level-b) emits Verify: only."""
        out = _capture_handoff(_LEVEL_A_DATA)
        self.assertIn("Verify:", out)
        self.assertNotIn("Try:", out)
        self.assertNotIn("Expected:", out)
        self.assertNotIn("Next:", out)

    def test_level_a_verify_contains_verification_text(self) -> None:
        """AC2: Verify: line contains the verification field value."""
        out = _capture_handoff(_LEVEL_A_DATA)
        self.assertIn(_LEVEL_A_DATA["verification"], out)

    def test_level_a_explicit_false_level_b_emits_verify_only(self) -> None:
        """AC2: level-b = False (explicit) also shows Verify: only."""
        data = {**_LEVEL_A_DATA, "level-b": False}
        out = _capture_handoff(data)
        self.assertIn("Verify:", out)
        self.assertNotIn("Try:", out)

    def test_no_first_value_emits_nothing(self) -> None:
        """AC3: Empty dict (no [pack.first-value] section) → no output."""
        out = _capture_handoff({})
        self.assertEqual(out, "")

    def test_label_alignment(self) -> None:
        """AC1: All four labels align at column 10 (label + padding = 10 chars)."""
        out = _capture_handoff(_LEVEL_B_DATA)
        lines = out.splitlines()
        # Find the handoff lines (skip the leading blank line).
        handoff_lines = [ln for ln in lines if ln and not ln.startswith(" ")]
        label_widths = set()
        for ln in handoff_lines:
            colon_idx = ln.index(":")
            label_widths.add(colon_idx + 1)  # chars up to and including ":"
        # All labels have exactly 10 chars before the value (label + padding).
        # "Expected:" is 9 chars — longest; "Try:" is 4 chars — shortest.
        # Verify by checking each label's prefix width in the output.
        verify_line = next(ln for ln in handoff_lines if ln.startswith("Verify:"))
        try_line = next(ln for ln in handoff_lines if ln.startswith("Try:"))
        expected_line = next(ln for ln in handoff_lines if ln.startswith("Expected:"))
        next_line = next(ln for ln in handoff_lines if ln.startswith("Next:"))
        # Value starts at the same column in all four lines.
        value_col = verify_line.index(_LEVEL_B_DATA["verification"][:10])
        self.assertEqual(
            try_line.index(_LEVEL_B_DATA["starter-prompt"][:10]), value_col
        )
        self.assertEqual(
            expected_line.index(_LEVEL_B_DATA["expected-result"][:10]), value_col
        )
        self.assertEqual(
            next_line.index(_LEVEL_B_DATA["next-action"][:10]), value_col
        )


# ---------------------------------------------------------------------------
# Part 2: Integration tests — full install.run pipeline + handoff
# ---------------------------------------------------------------------------


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


class InstallFirstValueHandoffIntegrationTests(unittest.TestCase):
    """AC1–AC6: install.run end-to-end handoff tests at repo scope.

    Uses the real converters pack (Level B) and core pack (Level A) from the
    repo. A scratch pack with no [pack.first-value] provides the AC3 baseline.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

        # Catalogue with converters (Level B) and core (Level A).
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")
        shutil.copytree(CORE_PACK_SRC, self.cat / "packs" / "core")

        # Scratch pack: no [pack.first-value] section.
        self._make_scratch_pack("nofirstvalue")

    def _make_scratch_pack(self, name: str) -> Path:
        """Create a minimal repo-scope pack without [pack.first-value]."""
        pack_dir = self.cat / "packs" / name
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            f'[pack]\n'
            f'name = "{name}"\n'
            f'version = "0.1.0"\n'
            f'description = "Scratch fixture: no first-value section."\n\n'
            f'[pack.adapter-contract]\n'
            f'version = "0.6"\n\n'
            f'[pack.install]\n'
            f'default-scope = "repo"\n'
            f'allowed-scopes = ["repo"]\n',
            encoding="utf-8",
        )
        # A minimal skill so the projection is non-empty.
        skill_dir = pack_dir / ".apm" / "skills" / "dummy"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\ndescription: Scratch skill.\n---\nScratch skill body.\n",
            encoding="utf-8",
        )
        return pack_dir

    def _install(
        self, pack: str, *, extra: dict | None = None
    ) -> tuple[int, str, str]:
        kwargs = dict(
            pack=pack,
            catalogue=str(self.cat),
            output=str(self.repo),
            scope="repo",
            force=False,
            force_merge=False,
            adapter=None,
            dry_run=False,
            yes=False,
        )
        if extra:
            kwargs.update(extra)
        return _run_install(argparse.Namespace(**kwargs))

    # AC1: Level B (converters) shows full handoff.
    def test_level_b_install_shows_full_handoff(self) -> None:
        rc, stdout, _ = self._install("converters")
        self.assertEqual(rc, 0)
        self.assertIn("installed: converters @ repo", stdout)
        self.assertIn("Verify:", stdout)
        self.assertIn("Try:", stdout)
        self.assertIn("Expected:", stdout)

    def test_level_b_installed_line_precedes_handoff(self) -> None:
        """AC5: installed: line appears before the handoff block."""
        rc, stdout, _ = self._install("converters")
        self.assertEqual(rc, 0)
        installed_pos = stdout.index("installed:")
        verify_pos = stdout.index("Verify:")
        self.assertLess(installed_pos, verify_pos)

    # AC2: Level A (core) shows Verify: only.
    def test_level_a_install_shows_verify_only(self) -> None:
        rc, stdout, _ = self._install("core")
        self.assertEqual(rc, 0)
        self.assertIn("installed: core @ repo", stdout)
        self.assertIn("Verify:", stdout)
        self.assertNotIn("Try:", stdout)
        self.assertNotIn("Expected:", stdout)

    # AC3: No [pack.first-value] → output unchanged.
    def test_no_first_value_no_handoff(self) -> None:
        rc, stdout, _ = self._install("nofirstvalue")
        self.assertEqual(rc, 0)
        self.assertIn("installed: nofirstvalue @ repo", stdout)
        self.assertNotIn("Verify:", stdout)
        self.assertNotIn("Try:", stdout)

    # AC4: dry-run shows no handoff.
    def test_dry_run_no_handoff(self) -> None:
        rc, stdout, _ = self._install("converters", extra={"dry_run": True})
        self.assertEqual(rc, 0)
        self.assertNotIn("Verify:", stdout)
        self.assertNotIn("installed:", stdout)  # dry-run exits before Step 13

    # AC7: upgrade-offer path (pack already installed at requested scope).
    def test_upgrade_offer_no_handoff(self) -> None:
        """AC7: Re-installing an already-installed pack emits no handoff.

        The upgrade-offer branch (Step 4a) calls confirm_or_refuse; in a
        non-TTY test environment with yes=False it prints the refuse_message
        to stderr and returns 1 — before Step 14 is ever reached.
        """
        rc1, _, _ = self._install("converters")
        self.assertEqual(rc1, 0)
        # Second call: non-TTY, yes=False → auto-refuses → return 1 before Step 14.
        rc2, stdout2, _ = self._install("converters")
        self.assertEqual(rc2, 1)
        self.assertNotIn("Verify:", stdout2)
        self.assertNotIn("Try:", stdout2)


class InstallFirstValueHandoffDualScopeTests(unittest.TestCase):
    """AC6: dual-scope install emits the handoff block exactly once.

    Mechanism: converters is installed at user scope first. A second install
    at repo scope with force=True triggers the dual-scope path
    (scopes_to_install = ["repo", "user"]), producing two `installed:` lines.
    Step 14 fires once after Step 13's loop, so Verify: appears exactly once.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        (self.home / ".claude").mkdir()  # adapter-detection probe
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")

    def _install(
        self, *, scope: str, force: bool = False
    ) -> tuple[int, str, str]:
        from agentbundle.commands import install

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = install.run(
                argparse.Namespace(
                    pack="converters",
                    catalogue=str(self.cat),
                    output=str(self.repo),
                    scope=scope,
                    force=force,
                    force_merge=False,
                    adapter=None,
                    dry_run=False,
                    yes=False,
                )
            )
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_dual_scope_handoff_appears_once(self) -> None:
        """AC6: two installed: lines → Verify: appears exactly once."""
        # Pre-install at user scope.
        rc1, _, _ = self._install(scope="user")
        self.assertEqual(rc1, 0)

        # Install at repo scope with force=True → dual-scope path.
        rc2, stdout, _ = self._install(scope="repo", force=True)
        self.assertEqual(rc2, 0)

        self.assertIn("installed: converters @ repo", stdout)
        self.assertIn("installed: converters @ user", stdout)
        self.assertEqual(stdout.count("Verify:"), 1,
                         "handoff block must appear exactly once after dual-scope install")


if __name__ == "__main__":
    unittest.main()
