"""T3: fixture-pack integration tests for user-scope-hooks.

Six fixture packs under ``packages/agentbundle/tests/fixtures/packs/``
exercise the validate rails from T1/T2 via the file-on-disk loader (not
just the in-memory unit-test path T2 covers). The well-formed fixtures
demonstrate the acceptance paths T8b/T6 will project; the malformed
fixtures pin the refusal text RFC-0005 mandates.

Pascal-case-event refusal lives in T6 (Kiro's `agent-event-vocabulary`
gate); its fixture ships here for use by that task. T3 covers the
two refusal classes the T2 rail already implements:
attach-to-agent missing, and attach-to-agent naming an unknown agent.

Spec ACs covered: AC6 (refusal text), AC28 (fixtures exist + are
exercised), AC29 (no test writes to ~/.claude, ~/.kiro, ~/.agentbundle
outside tmp_path).

**T2 update (incompatible-hook-event-drop spec):** The
``test_missing_attach_to_agent_refused`` and
``test_pascal_events_refused_with_vocabulary_text`` tests below have
been updated to reflect the new T2 behaviour: these compatibility-only
refusals are now swallowed by validate, which exits 0 and emits an
``info:`` line on stdout instead. The
``test_unknown_agent_refused`` test remains exit-1 (correctness
refusal — AC4b of the incompatible-hook-event-drop spec).
"""

from __future__ import annotations

import contextlib
import io
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "packs"


WELL_FORMED = ("cc-user-hooks", "kiro-repo-hooks", "kiro-user-hooks")
MALFORMED = (
    "malformed-kiro-missing-attach",
    "malformed-kiro-pascal-events",  # T6 covers the validate refusal — fixture only
    "malformed-kiro-unknown-agent",
)


def _run_validate(pack_path: Path) -> tuple[int, str]:
    """Invoke ``agentbundle validate`` against *pack_path* and return (rc, stderr)."""
    import argparse

    from agentbundle.commands import validate as cmd

    args = argparse.Namespace(pack_path=str(pack_path), strict=False)
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = cmd.run(args)
    return rc, buf.getvalue()


def _run_validate_with_stdout(pack_path: Path) -> tuple[int, str, str]:
    """Invoke ``agentbundle validate`` and return (rc, stdout, stderr).

    Used by tests that need to assert on both streams.
    """
    import argparse

    from agentbundle.commands import validate as cmd

    args = argparse.Namespace(pack_path=str(pack_path), strict=False)
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
        rc = cmd.run(args)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _ensure_executable(path: Path) -> None:
    """Re-apply +x to a hook body whose CI checkout might have stripped it.

    Some CI runners apply restrictive umasks that drop the executable
    bit on tracked files. Hooks are run via ``sh -c "$command"``, so the
    bit doesn't affect *projection* shape — but downstream T6 tests
    that observe dispatchability (AC18) need it. Defensive re-chmod
    keeps the fixtures self-healing.
    """
    if path.exists() and not os.access(path, os.X_OK):
        path.chmod(0o755)


class FixturePresenceTests(unittest.TestCase):
    """Every fixture named in spec.md § Testing Strategy is on disk."""

    def test_all_well_formed_fixtures_exist(self) -> None:
        for name in WELL_FORMED:
            with self.subTest(fixture=name):
                self.assertTrue(
                    (FIXTURES / name / "pack.toml").exists(),
                    f"fixture {name!r} missing pack.toml",
                )

    def test_all_malformed_fixtures_exist(self) -> None:
        for name in MALFORMED:
            with self.subTest(fixture=name):
                self.assertTrue(
                    (FIXTURES / name / "pack.toml").exists(),
                    f"fixture {name!r} missing pack.toml",
                )

    def test_kiro_repo_hooks_ships_agent_body_and_wiring(self) -> None:
        """Plan T3: kiro-repo-hooks ships `.apm/agents/reviewer.md`,
        `.apm/hooks/on-spawn.sh`, `.apm/hook-wiring/on-spawn.toml`."""
        root = FIXTURES / "kiro-repo-hooks"
        self.assertTrue((root / ".apm" / "agents" / "reviewer.md").exists())
        self.assertTrue((root / ".apm" / "hooks" / "on-spawn.sh").exists())
        self.assertTrue((root / ".apm" / "hook-wiring" / "on-spawn.toml").exists())


class WellFormedFixturesValidateTests(unittest.TestCase):
    """The three well-formed fixtures pass ``agentbundle validate``."""

    def test_cc_user_hooks_validates(self) -> None:
        pack = FIXTURES / "cc-user-hooks"
        _ensure_executable(pack / ".apm" / "hooks" / "on-prompt.sh")
        rc, err = _run_validate(pack)
        self.assertEqual(rc, 0, f"cc-user-hooks refused: {err}")

    def test_kiro_repo_hooks_validates(self) -> None:
        pack = FIXTURES / "kiro-repo-hooks"
        _ensure_executable(pack / ".apm" / "hooks" / "on-spawn.sh")
        rc, err = _run_validate(pack)
        self.assertEqual(rc, 0, f"kiro-repo-hooks refused: {err}")

    def test_kiro_user_hooks_validates(self) -> None:
        pack = FIXTURES / "kiro-user-hooks"
        _ensure_executable(pack / ".apm" / "hooks" / "on-spawn.sh")
        rc, err = _run_validate(pack)
        self.assertEqual(rc, 0, f"kiro-user-hooks refused: {err}")


class MalformedFixturesRefusedTests(unittest.TestCase):
    """Fixture-pack tests for attach-to-agent rails.

    Updated for incompatible-hook-event-drop T2:
    - ``malformed-kiro-missing-attach``: the missing-attach-to-agent case
      is now a *compatibility drop* (exit 0, info on stdout) — the T2
      swallow per spec AC1.
    - ``malformed-kiro-unknown-agent``: the unknown-agent case is a
      *correctness refusal* (exit 1, stderr) — AC4b of the same spec.
    """

    def test_missing_attach_to_agent_swallowed_as_compat_drop(self) -> None:
        """T2 (incompatible-hook-event-drop): missing attach-to-agent is now
        a compatibility drop — validate exits 0 with an info: line on stdout."""
        rc, out, err = _run_validate_with_stdout(FIXTURES / "malformed-kiro-missing-attach")
        self.assertEqual(rc, 0, f"malformed-kiro-missing-attach was refused: {err}")
        self.assertNotIn("validate:", err, f"Unexpected refusal on stderr: {err!r}")
        self.assertIn("info:", out, f"Expected info: line on stdout, got: {out!r}")
        self.assertIn(
            "kiro requires 'attach-to-agent'",
            out,
            f"Expected attach-to-agent reason in stdout: {out!r}",
        )

    def test_unknown_agent_refused(self) -> None:
        rc, err = _run_validate(FIXTURES / "malformed-kiro-unknown-agent")
        self.assertEqual(rc, 1, "malformed-kiro-unknown-agent was accepted")
        # Same refusal text — "or names an unknown agent" disjunct
        # covers both shapes (RFC-0005 § Repo-scope Kiro promotion).
        self.assertIn("or names an unknown agent", err)


class PascalEventsRefusedByT6Tests(unittest.TestCase):
    """T6 introduced the per-adapter ``agent-event-vocabulary`` rail.

    Updated for incompatible-hook-event-drop T2: PascalCase events
    that fall outside Kiro's declared vocabulary are now a
    *compatibility drop* (exit 0, info on stdout) rather than a
    refusal. The test is renamed accordingly.
    """

    def test_pascal_events_swallowed_as_compat_drop(self) -> None:
        """T2 (incompatible-hook-event-drop): out-of-vocab events are now
        a compatibility drop — validate exits 0 with an info: line on stdout."""
        rc, out, err = _run_validate_with_stdout(FIXTURES / "malformed-kiro-pascal-events")
        self.assertEqual(rc, 0, f"pascal-events fixture was refused: {err}")
        self.assertNotIn("validate:", err, f"Unexpected refusal on stderr: {err!r}")
        self.assertIn("info:", out, f"Expected info: line on stdout, got: {out!r}")
        self.assertIn(
            "event not in adapter vocabulary",
            out,
            f"Expected vocab reason in stdout: {out!r}",
        )


class FixtureIsolationTests(unittest.TestCase):
    """AC29: nothing in this test module writes to ``~/.claude``,
    ``~/.kiro``, or ``~/.agentbundle``. Redirects ``$HOME`` to a
    ``tmp_path``-scoped directory and asserts the redirected tree is
    empty after validate runs against each user-scope fixture. This is
    the AC29-shaped pin: a regression that writes into ``$HOME`` from
    validate would create artifacts in the tmp tree."""

    def test_validate_does_not_write_to_redirected_home(self) -> None:
        import os
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp_home:
            with patch.dict(os.environ, {"HOME": tmp_home}):
                for fixture in ("cc-user-hooks", "kiro-user-hooks", "kiro-repo-hooks"):
                    with self.subTest(fixture=fixture):
                        _run_validate(FIXTURES / fixture)

            # After every validate run, the redirected home must be
            # empty — validate is read-only against the pack directory.
            tmp_path = Path(tmp_home)
            artifacts = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
            self.assertEqual(
                artifacts,
                [],
                f"validate wrote into $HOME during fixture validation: {artifacts}",
            )


if __name__ == "__main__":
    unittest.main()
