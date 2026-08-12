"""Tests for the make-free self-host gate chains (`tools/repo/build_gate_chain.py`).

The load-bearing invariant is "run these steps, in this order, stop at the first
failure, return its code" — verified against stubbed step outcomes — plus the
step assembly (which command, in what order) and Windows-cleanliness of spawned argv.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Import from tools/repo/ (the real implementation, not the shim at tools/).
sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import build_gate_chain as gc  # noqa: E402


class PackSkillPytestShapeTest(unittest.TestCase):
    """Every Python pack skill test exposes real pytest collection nodes."""

    def test_pack_skill_tests_use_pytest_shape(self):
        root = Path(__file__).resolve().parents[1]
        failures: list[str] = []
        aggregate_names = {
            "FAILURES", "failures", "SKIPPED", "skipped", "SKIPS", "RAN", "ran",
        }
        test_files = sorted((root / "packs").glob("*/tests/skills/**/test*.py"))
        self.assertTrue(test_files, "no Python pack skill tests found")
        for path in test_files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            functions = {
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            classes = {
                node.name
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and any(
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name.startswith("test")
                    for item in node.body
                )
            }
            if not any(name.startswith("test") for name in functions) and not classes:
                failures.append(f"{path.relative_to(root)}: no pytest collection node")
            if "main" in functions:
                failures.append(f"{path.relative_to(root)}: standalone main() remains")
            for node in tree.body:
                if isinstance(node, ast.If):
                    names = {item.id for item in ast.walk(node.test) if isinstance(item, ast.Name)}
                    if "__name__" in names:
                        failures.append(f"{path.relative_to(root)}: __main__ guard remains")
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id in aggregate_names:
                            failures.append(
                                f"{path.relative_to(root)}: aggregate state {target.id} remains"
                            )
            legacy = sorted(name for name in functions if name.startswith(("case_", "layer_")))
            if legacy:
                failures.append(f"{path.relative_to(root)}: undiscoverable cases {legacy}")
        self.assertEqual(failures, [], "\n".join(failures))


class CiPytestProvisioningTest(unittest.TestCase):
    """CI provisions pytest before entering pytest-backed gate paths."""

    def test_build_check_installs_pytest_before_make_build_check(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/build-check.yml").read_text(encoding="utf-8")

        install = workflow.index(
            "run: python -m pip install -e packages/agentbundle/ pytest"
        )
        build_check = workflow.index("- name: Run make build-check")

        self.assertLess(install, build_check)

    def test_docs_jobs_install_pytest_before_pytest_backed_steps(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/docs.yml").read_text(encoding="utf-8")
        jobs = {
            "lint-knowledge": ("loop-cohort", "run: python3 -m pytest"),
            "loop-cohort": ("hooks", "run: bash packs/core/tests/skills/work-loop/test-loop-cohort.sh"),
        }

        for job, (next_job, first_pytest_step) in jobs.items():
            with self.subTest(job=job):
                block = workflow.split(f"  {job}:\n", 1)[1].split(f"\n  {next_job}:\n", 1)[0]
                setup = block.index("uses: actions/setup-python@")
                install = block.index("run: python -m pip install pytest")
                invocation = block.index(first_pytest_step)
                self.assertLess(setup, install)
                self.assertLess(install, invocation)


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
        self.assertEqual(calls, ["a", "b"])
        line = stderr.getvalue()
        self.assertIn("✖", line)
        self.assertIn("b", line)
        self.assertIn("3", line)


class BuildSelfChainTest(unittest.TestCase):
    """`build_self` uses agentbundle catalogue self-host via subprocess."""

    def _run_with_fake_subprocess(self, args: argparse.Namespace) -> tuple[int, list[list[str]]]:
        seen: list[list[str]] = []

        def fake_run(argv, check, env=None):
            seen.append(argv)
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            rc = gc.build_self(args)
        return rc, seen

    def test_write_mode_calls_self_host_write(self):
        args = argparse.Namespace(dry_run=False, force=False, packs_dir="packs", no_symlink=False)
        rc, seen = self._run_with_fake_subprocess(args)
        self.assertEqual(rc, 0)
        self.assertEqual(len(seen), 1)
        argv = seen[0]
        self.assertIn("-m", argv)
        self.assertIn("agentbundle", argv)
        self.assertIn("catalogue", argv)
        self.assertIn("self-host", argv)
        self.assertIn("--write", argv)
        self.assertNotIn("--check", argv)
        self.assertNotIn("--force", argv)

    def test_write_force_mode_passes_force(self):
        args = argparse.Namespace(dry_run=False, force=True, packs_dir="packs", no_symlink=False)
        rc, seen = self._run_with_fake_subprocess(args)
        self.assertEqual(rc, 0)
        argv = seen[0]
        self.assertIn("--write", argv)
        self.assertIn("--force", argv)

    def test_dry_run_mode_calls_self_host_check(self):
        args = argparse.Namespace(dry_run=True, force=False, packs_dir="packs", no_symlink=False)
        rc, seen = self._run_with_fake_subprocess(args)
        self.assertEqual(rc, 0)
        argv = seen[0]
        self.assertIn("--check", argv)
        self.assertNotIn("--write", argv)


# The `build-check` chain's spawned script steps, in order. Single source for
# both the ordering assertion and the step count — a literal count drifts out of
# step with the list it is supposed to describe.
EXPECTED_SCRIPT_STEPS = [
    "tools/catalogue/pre_pr_catalogue.py",
    "tools/catalogue/check_contract_parity.py",
    "packs/core/tests/skills/work-loop/test_lint_spec_status.py",
    ".claude/skills/work-loop/scripts/lint-spec-status.py",
    "packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py",
    ".claude/skills/receive-brief/scripts/lint-brief-coverage.py",
    "packs/core/tests/skills/work-loop/test_lint_traceability.py",
    ".claude/skills/work-loop/scripts/lint-traceability.py",
    "tools/test_workspace_status.py",
    "tools/test_workspace_status_cli.py",
    "tools/test-lint-catalogue-curation-guard.py",
    "tools/lint-catalogue-curation-guard.py",
    "tools/test-lint-experience-agnostic.py",
    "tools/lint-experience-agnostic.py",
    # Claude-plugin route scope (docs/specs/claude-plugin-route-scope): each
    # lint is preceded by the sibling that proves it can fail.
    "tools/test-pack-scope.py",
    "tools/test-lint-plugin-membership.py",
    "tools/lint-plugin-membership.py",
    "tools/test-lint-plugin-roster.py",
    "tools/lint-plugin-roster.py",
    "tools/test-publish-claude-plugins.py",
    "tools/test-lint-claude-plugin-publish-control.py",
    "tools/lint-claude-plugin-publish-control.py",
    "tools/test-lint-plugin-route-docs.py",
    "tools/lint-plugin-route-docs.py",
    "tools/test-lint-site-scope-parity.py",
    "tools/lint-site-scope-parity.py",
    "tools/test-check-site-plugin-offers.py",
    "tools/test-lint-pack-descriptions.py",
    "tools/lint-pack-descriptions.py",
    "tools/test-lint-ci-parity.py",
    "tools/test-build-check-windows-workflow.py",
    "tools/lint-ci-parity.py",
    "tools/test-test-all.py",
]


class BuildCheckChainTest(unittest.TestCase):
    """`build_check` assembles every Windows-clean step, in order, no SAST."""

    def test_full_step_sequence(self):
        order: list[str] = []

        def fake_run(argv, check, env=None):
            order.append("subprocess")
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            rc = gc.build_check(args)

        self.assertEqual(rc, 0)
        # 1 module step (catalogue build) + the script steps.
        self.assertEqual(len(order), 1 + len(EXPECTED_SCRIPT_STEPS))

    def test_first_step_is_catalogue_build(self):
        """The first step must invoke agentbundle catalogue build."""
        seen: list[list[str]] = []

        def fake_run(argv, check, env=None):
            seen.append(list(argv))
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            gc.build_check(args)

        first = seen[0]
        self.assertIn("-m", first)
        self.assertIn("agentbundle", first)
        self.assertIn("catalogue", first)
        self.assertIn("build", first)
        self.assertIn("--output", first)
        self.assertIn("dist", first)

    def test_pre_pr_step_uses_new_path(self):
        """pre-pr-catalogue must call tools/catalogue/pre_pr_catalogue.py."""
        seen: list[list[str]] = []

        def fake_run(argv, check, env=None):
            seen.append(list(argv))
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            gc.build_check(args)

        # Find the pre-pr-catalogue step (index 1 = second call; first is catalogue build).
        pre_pr_argv = seen[1]
        # Path should contain tools/catalogue/pre_pr_catalogue.py
        script_path = Path(pre_pr_argv[1]).as_posix()
        self.assertIn("tools/catalogue/pre_pr_catalogue.py", script_path)

    def test_script_steps_are_windows_clean(self):
        """Every spawned argv is a shell-free Python script or pytest call."""
        seen: list[list[str]] = []

        def fake_run(argv, check, env=None):
            seen.append(list(argv))
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        pytest_paths = {
            "packs/core/tests/skills/work-loop/test_lint_spec_status.py",
            "packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py",
            "packs/core/tests/skills/work-loop/test_lint_traceability.py",
        }
        for argv in seen[1:]:  # skip first (module step has extra args)
            self.assertEqual(argv[0], sys.executable)
            path = Path(argv[3] if argv[1:3] == ["-m", "pytest"] else argv[1]).as_posix()
            if path in pytest_paths:
                self.assertEqual(argv[1:3], ["-m", "pytest"])
                self.assertEqual(argv[-1], "-q")
            else:
                self.assertEqual(len(argv), 2)
            for token in argv:
                self.assertNotIn(token, ("bash", "sh", "-c"))
                self.assertFalse(token.endswith(".sh"))

    def test_spawned_script_paths_in_order(self):
        """The spawned script paths match the expected gate order."""
        seen: list[list[str]] = []

        def fake_run(argv, check, env=None):
            seen.append(list(argv))
            return mock.Mock(returncode=0)

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        # seen[0] = module step (catalogue build); seen[1:] = script steps.
        spawned = [
            Path(argv[3] if argv[1:3] == ["-m", "pytest"] else argv[1]).as_posix()
            for argv in seen[1:]
        ]
        self.assertEqual(spawned, EXPECTED_SCRIPT_STEPS)


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
            missing = Path(tmp) / "nope.py"  # does not exist
            steps = [
                gc._script_step("missing", missing),
                ("after", lambda: (ran_after.append("after"), 0)[1]),
            ]
            rc = gc._run_chain(steps)
        self.assertEqual(rc, 2)
        self.assertEqual(ran_after, [])


if __name__ == "__main__":
    unittest.main()
