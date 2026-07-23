"""Tests for the make-free self-host gate chains (`tools/build_gate_chain.py`).

The load-bearing invariant is "run these steps, in this order, stop at the first
failure, return its code" — verified against stubbed step outcomes — plus the
step assembly (which handler/script, in what order, with which namespace
attributes) and Windows-cleanliness of the spawned argv.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_gate_chain as gc  # noqa: E402


class RunChainTest(unittest.TestCase):
    """The generic runner: order, all-pass, and first-failure short-circuit."""

    def test_runs_all_in_order_returns_zero(self):
        calls: list[str] = []
        steps = [
            ("a", lambda: (calls.append("a"), 0)[1]),
            ("b", lambda: (calls.append("b"), 0)[1]),
            ("c", lambda: (calls.append("c"), 0)[1]),
        ]
        rc = gc._run_chain(steps)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["a", "b", "c"])

    def test_stops_at_first_failure_and_returns_its_code(self):
        calls: list[str] = []
        steps = [
            ("a", lambda: (calls.append("a"), 0)[1]),
            ("b", lambda: (calls.append("b"), 3)[1]),  # fails
            ("c", lambda: (calls.append("c"), 0)[1]),  # must not run
        ]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            rc = gc._run_chain(steps)
        self.assertEqual(rc, 3)
        self.assertEqual(calls, ["a", "b"])  # "c" never ran
        # The failure-legibility signal: names the failing label and its code.
        line = stderr.getvalue()
        self.assertIn("✖", line)
        self.assertIn("b", line)
        self.assertIn("3", line)


class BuildSelfChainTest(unittest.TestCase):
    """`build_self` assembles lint-packs → self with the right namespaces."""

    def test_steps_order_and_namespaces(self):
        recorded: list[tuple[str, argparse.Namespace]] = []

        def rec(label):
            def _f(ns):
                recorded.append((label, ns))
                return 0
            return _f

        with mock.patch.object(gc, "cmd_lint_packs", rec("lint-packs")), \
             mock.patch.object(gc, "cmd_self", rec("self")):
            args = argparse.Namespace(
                packs_dir="packs", dry_run=True, force=False, no_symlink=True
            )
            rc = gc.build_self(args)

        self.assertEqual(rc, 0)
        self.assertEqual([label for label, _ in recorded], ["lint-packs", "self"])

        lint_ns = recorded[0][1]
        self.assertEqual(lint_ns.packs_dir, "packs")

        self_ns = recorded[1][1]
        # Every attribute cmd_self reads must be present (AttributeError guard).
        self.assertEqual(self_ns.packs_dir, "packs")
        self.assertEqual(self_ns.output_dir, ".")
        self.assertEqual(self_ns.dry_run, True)
        self.assertEqual(self_ns.force, False)
        self.assertEqual(self_ns.no_symlink, True)


class BuildCheckChainTest(unittest.TestCase):
    """`build_check` assembles every Windows-clean step, in order, no SAST."""

    def test_full_step_sequence_and_namespaces(self):
        order: list[str] = []
        ns_by_label: dict[str, argparse.Namespace] = {}

        def rec(label):
            def _f(ns):
                order.append(label)
                ns_by_label[label] = ns
                return 0
            return _f

        script_argvs: list[list[str]] = []

        def fake_run(argv, check):
            order.append("script")
            script_argvs.append(argv)
            self.assertFalse(check)  # check=False — never raises on script failure
            return mock.Mock(returncode=0)

        with mock.patch.object(gc, "cmd_lint_packs", rec("lint-packs")), \
             mock.patch.object(gc, "cmd_build", rec("build")), \
             mock.patch.object(gc, "cmd_check", rec("check")), \
             mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            rc = gc.build_check(args)

        self.assertEqual(rc, 0)
        # Handlers first three, then ten spawned scripts — Makefile order, no SAST.
        self.assertEqual(
            order,
            ["lint-packs", "build", "check"] + ["script"] * 10,
        )

        self.assertEqual(ns_by_label["lint-packs"].packs_dir, "packs")
        build_ns = ns_by_label["build"]
        self.assertEqual(build_ns.packs_dir, "packs")
        self.assertEqual(build_ns.output_dir, "dist")  # from args.output_dir
        self.assertIsNone(build_ns.recipe)
        self.assertIsNone(build_ns.pack)
        check_ns = ns_by_label["check"]
        self.assertEqual(check_ns.packs_dir, "packs")
        self.assertEqual(check_ns.output_dir, ".")  # working tree, not dist

        # The ten spawned scripts, in Makefile order.
        spawned = [Path(argv[1]).as_posix() for argv in script_argvs]
        self.assertEqual(
            spawned,
            [
                "tools/pre-pr-catalogue.py",
                ".claude/skills/work-loop/scripts/test-lint-spec-status.py",
                ".claude/skills/work-loop/scripts/lint-spec-status.py",
                ".claude/skills/receive-brief/scripts/test-lint-brief-coverage.py",
                ".claude/skills/receive-brief/scripts/lint-brief-coverage.py",
                ".claude/skills/work-loop/scripts/test-lint-traceability.py",
                ".claude/skills/work-loop/scripts/lint-traceability.py",
                "tools/test-lint-first-value-contract.py",
                "tools/lint-first-value-contract.py",
                "tools/validate-claude-plugin-manifests.py",
            ],
        )

    def test_spawned_argv_is_windows_clean(self):
        """Every spawned argv is [sys.executable, path] — no shell token."""
        seen: list[list[str]] = []

        def fake_run(argv, check):
            seen.append(argv)
            return mock.Mock(returncode=0)

        with mock.patch.object(gc, "cmd_lint_packs", lambda ns: 0), \
             mock.patch.object(gc, "cmd_build", lambda ns: 0), \
             mock.patch.object(gc, "cmd_check", lambda ns: 0), \
             mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        self.assertTrue(seen)
        for argv in seen:
            self.assertEqual(argv[0], sys.executable)
            self.assertEqual(len(argv), 2)
            for token in argv:
                self.assertNotIn(token, ("bash", "sh", "-c"))
                self.assertFalse(token.endswith(".sh"))


class ParserWiringTest(unittest.TestCase):
    """The two subcommands parse and dispatch to the chain functions."""

    def test_subcommands_dispatch_to_chain_functions(self):
        parser = gc._build_parser()
        self.assertIs(parser.parse_args(["build-self"]).func, gc.build_self)
        self.assertIs(parser.parse_args(["build-check"]).func, gc.build_check)

    def test_build_check_output_dir_default(self):
        args = gc._build_parser().parse_args(["build-check"])
        self.assertEqual(args.packs_dir, "packs")
        self.assertEqual(args.output_dir, "dist")


class MissingScriptTest(unittest.TestCase):
    """A missing spawned script yields the interpreter's exit 2 and stops the chain."""

    def test_missing_script_step_fails_and_short_circuits(self):
        ran_after: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "nope.py")  # does not exist
            steps = [
                gc._script_step("missing", missing),
                ("after", lambda: (ran_after.append("after"), 0)[1]),
            ]
            rc = gc._run_chain(steps)
        # The interpreter exits 2 ("can't open file") — pin the propagated value,
        # not just "non-zero", so we prove the missing step's code surfaced.
        self.assertEqual(rc, 2)
        self.assertEqual(ran_after, [])   # later step never ran


if __name__ == "__main__":
    unittest.main()
