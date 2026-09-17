"""Construction tests for ``tools/lint_harness.py`` and ``tools/selftest_harness.py``.

Underscored so a directory sweep collects this file; the subjects it guards are
imported by scripts whose own self-tests are hyphenated and are not swept.

Two properties carry the weight. The first is that a rule module can import the
driver in all three ways this repository loads one — as a script, as a
subprocess from a test, and in-process through ``importlib`` from a collected
test. That resolution is incidental to ``tools/`` having no ``__init__.py``, so
it is pinned here rather than rediscovered when a future ``__init__.py`` or a
changed ``importmode`` breaks twelve lints at once.

The second is that an *empty* target directory and an *absent* one stay apart.
Eight of the twelve lints answer those two conditions differently, three of
them by exit status, and ``if not targets`` is the single line that would merge
them.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent

sys.path.insert(0, str(TOOLS)) if str(TOOLS) not in sys.path else None
import lint_harness  # noqa: E402
import selftest_harness  # noqa: E402


def _rule(**overrides: object) -> lint_harness.Rule:
    """A minimal rule; each test overrides only the field it is about."""
    base = {
        "parse": lambda argv: Path(argv[0]) if argv else Path(),
        "files": lambda root: [Path("a")],
        "predicate": lambda path: [],
        "pass_line": lambda root, n: f"probe: ok ({n})",
        "empty_scan": lambda root: lint_harness.Outcome("probe: nothing scanned", 2),
        "absent_root": lambda root: lint_harness.Outcome("probe: no root", 3),
    }
    base.update(overrides)
    return lint_harness.Rule(**base)  # type: ignore[arg-type]


class EmptyVersusAbsent(unittest.TestCase):
    """The distinction the driver exists to preserve."""

    def test_absent_root_is_reported_by_none_not_by_emptiness(self) -> None:
        self.assertEqual(lint_harness.run(_rule(files=lambda root: None), []), 3)

    def test_empty_sequence_is_an_empty_scan_not_an_absent_root(self) -> None:
        self.assertEqual(lint_harness.run(_rule(files=lambda root: []), []), 2)

    def test_the_two_outcomes_do_not_share_an_exit_status(self) -> None:
        """Guards the merge directly: if `if not targets` ever handles both,
        these two calls collapse onto one status and this fails."""
        absent = lint_harness.run(_rule(files=lambda root: None), [])
        empty = lint_harness.run(_rule(files=lambda root: []), [])
        self.assertNotEqual(absent, empty)


class ExitContracts(unittest.TestCase):
    def test_a_violation_exits_1(self) -> None:
        rule = _rule(predicate=lambda path: ["bad"])
        self.assertEqual(lint_harness.run(rule, []), 1)

    def test_a_clean_walk_exits_0(self) -> None:
        self.assertEqual(lint_harness.run(_rule(), []), 0)

    def test_rule_abort_stops_the_walk_with_its_own_status(self) -> None:
        seen: list[Path] = []

        def predicate(path: Path) -> list[str]:
            seen.append(path)
            raise lint_harness.RuleAbort(lint_harness.Outcome("unreadable", 2))

        rule = _rule(files=lambda root: [Path("a"), Path("b")], predicate=predicate)
        self.assertEqual(lint_harness.run(rule, []), 2)
        self.assertEqual(len(seen), 1, "abort must stop the walk, not finish it")

    def test_report_replaces_default_emission(self) -> None:
        """A rule whose header precedes its findings cannot use the default.

        The streams are captured, not just the callback: a driver that called
        `report` and *also* emitted the default findings and summary would
        satisfy a callback-only assertion while doubling every rule's output.
        """
        written: list[str] = []
        rule = _rule(
            predicate=lambda path: ["finding"],
            summary=lambda n: "SHOULD NOT APPEAR",
            report=lambda violations: written.extend(violations),
        )
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = lint_harness.run(rule, [])
        self.assertEqual(status, 1)
        self.assertEqual(written, ["finding"])
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "", "default emission ran alongside report")


class ImportTimePathHygiene(unittest.TestCase):
    def test_neither_module_mutates_sys_path_at_import(self) -> None:
        probe = textwrap.dedent(
            """
            import sys
            before = list(sys.path)
            import lint_harness, selftest_harness  # noqa: F401
            print("CHANGED" if list(sys.path) != before else "UNCHANGED")
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True, text=True, cwd=str(TOOLS), check=False,
        )
        self.assertEqual(result.stdout.strip(), "UNCHANGED", result.stderr)

    def test_both_modules_import_only_the_standard_library(self) -> None:
        probe = textwrap.dedent(
            """
            import sys, pathlib
            names = set(sys.stdlib_module_names)
            before = set(sys.modules)
            import lint_harness, selftest_harness  # noqa: F401
            added = {m.split(".")[0] for m in set(sys.modules) - before}
            here = {"lint_harness", "selftest_harness"}
            print(sorted(added - names - here))
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True, text=True, cwd=str(TOOLS), check=False,
        )
        self.assertEqual(result.stdout.strip(), "[]", result.stderr)


class ThreeLoadContexts(unittest.TestCase):
    """`import lint_harness` must resolve however the caller was started."""

    SUBJECT = TOOLS / "lint-pack-descriptions.py"

    def test_as_a_script(self) -> None:
        """Assert the real success line, not merely a tolerated exit status.

        An earlier version accepted any exit in (0, 1) and only excluded
        `ModuleNotFoundError`, which a `SyntaxError` or any unrelated crash
        also satisfies — a control that could not fail for most breakages.
        """
        result = subprocess.run(
            [sys.executable, str(self.SUBJECT), "--root", str(REPO_ROOT)],
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.startswith("lint-pack-descriptions: no pack description"),
            result.stdout,
        )
        self.assertEqual(result.stderr, "")

    def test_as_a_subprocess_from_a_test(self) -> None:
        """The shape every pytest-collected lint test already uses."""
        result = subprocess.run(
            [sys.executable, str(self.SUBJECT), "--root", str(REPO_ROOT)],
            capture_output=True, text=True, cwd=str(TOOLS), check=False,
        )
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_in_process_via_importlib(self) -> None:
        """The context that fails at COLLECTION if resolution ever breaks."""
        module = selftest_harness.load("lint-pack-descriptions.py")
        self.assertTrue(hasattr(module, "RULE"))


class SelftestHarness(unittest.TestCase):
    def test_load_resolves_a_hyphenated_filename(self) -> None:
        module = selftest_harness.load("lint-pack-descriptions.py")
        self.assertEqual(module.MAX_DESCRIPTION, 800)

    def test_run_cases_reports_a_seeded_failure(self) -> None:
        """A runner that cannot report a failure is the defect this module
        could otherwise introduce across ten callers at once."""
        ns = {"test_passes": lambda: None, "test_fails": lambda: (_ for _ in ()).throw(AssertionError("seeded"))}
        self.assertEqual(selftest_harness.run_cases(ns, "probe"), 1)

    def test_run_cases_passes_when_every_case_passes(self) -> None:
        self.assertEqual(selftest_harness.run_cases({"test_ok": lambda: None}, "probe"), 0)

    def test_case_failures_reports_a_seeded_failure(self) -> None:
        failures = selftest_harness.CaseFailures("probe")
        failures.check("holds", True)
        failures.check("does not hold", False, "detail")
        # Exactly one, and the right one: recording the passing check too would
        # still return 1 and would still look like a working accumulator.
        self.assertEqual(len(failures.failures), 1, failures.failures)
        self.assertIn("does not hold", failures.failures[0])
        self.assertEqual(failures.report(), 1)

    def test_case_failures_passes_when_empty(self) -> None:
        self.assertEqual(selftest_harness.CaseFailures("probe").report(), 0)

    def test_case_names_are_in_definition_order(self) -> None:
        def test_b() -> None: ...
        def test_a() -> None: ...
        ns = {"test_b": test_b, "test_a": test_a}
        self.assertEqual(selftest_harness.case_names(ns), ["test_b", "test_a"])


if __name__ == "__main__":
    unittest.main()
