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
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Import from tools/repo/ (the real implementation, not the shim at tools/).
sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import build_gate_chain as gc  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent / "catalogue"))
import pre_pr_catalogue as pre_pr  # noqa: E402


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


class BanditRegistryProvisioningTest(unittest.TestCase):
    """`build-check` installs bandit unconditionally, last, and proves it worked.

    `make build-check` chains `tools/lint-nosec-form.py`, whose unknown-test-id
    check reads bandit's registry through `id_checker()` and **degrades to an
    exit-0 caveat** when it cannot. So a provisioning step that quietly does
    nothing leaves the required check green with that check inert — which is the
    defect `docs/specs/build-check-coverage-gaps` exists to remove.

    Nothing else pins the step. `tools/lint-ci-parity.py`'s roster only demands
    a disposition for steps that *exist*, so deleting the step together with its
    `STEP_DISPOSITION` row passes the parity gate in both directions.

    The step body is **executed**, not pattern-matched: `pip` is stubbed so the
    run is offline, and the cases below are its negative controls. The full
    mutation set — body-level and workflow-level — is enumerated once, in
    `docs/specs/build-check-coverage-gaps/spec.md` AC4b; it is not restated
    here, so the number cannot drift between the two. An assertion never seen to
    fail is an unverified one, and this file's older `workflow.index(...)` cases
    are exactly the source-substring shape
    `docs/knowledge/observations/antipattern/2026-08.jsonl` warns about.
    """

    STEP = "Install bandit unconditionally (lint-nosec-form's ID registry)"
    GATE = "Run make build-check"

    @classmethod
    def _parse_steps(cls, text: str) -> list[dict]:
        """Return `build-check.yml`'s steps as {name, has_if, run} dicts.

        Hand-parsed rather than PyYAML on purpose. This module is pure stdlib
        (AGENTS.md § New tool scripts) AND runs in Gate F of
        catalogue-tooling-ci-gates.yml, whose job installs only agentbundle —
        which declares no dependencies — so importing yaml here fails at
        collection there. A pin that cannot run in one of the two jobs that run
        it is not a pin.

        Only the fixed shape of a steps list is read: a step opens at six
        spaces + "- ", its keys sit at eight, and a block scalar's body sits
        deeper. That is structure, not a substring search for the control.
        """
        steps: list[dict] = []
        lines = text.splitlines()
        index = 0
        while index < len(lines) and lines[index] != "    steps:":
            index += 1
        index += 1
        current: dict | None = None
        run_indent: int | None = None
        for line in lines[index:]:
            stripped = line.strip()
            if line and not line.startswith("      ") and stripped:
                break  # dedented out of the steps list
            if line.startswith("      - "):
                current = {
                    "name": None, "has_if": False, "run": None,
                    "style": None, "continue_on_error": False,
                }
                steps.append(current)
                run_indent = None
                # Re-indent the first key onto the eight-space level the rest of
                # the step's keys sit at, and re-strip: `stripped` above still
                # carries the "- " that would otherwise land in the key name.
                line = "        " + line[8:]
                stripped = line.strip()
            if current is None:
                continue
            if run_indent is not None:
                if not stripped or len(line) - len(line.lstrip(" ")) >= run_indent:
                    current["run"].append(line[run_indent:])
                    continue
                current["run"] = cls._join(current["run"], current["style"])
                run_indent = None
            if line.startswith("        ") and not line.startswith("         "):
                key, _, value = stripped.partition(":")
                if key == "name":
                    current["name"] = value.strip()
                elif key == "if":
                    current["has_if"] = True
                elif key == "continue-on-error":
                    current["continue_on_error"] = value.strip() not in ("false", "")
                elif key == "run" and value.strip() in ("|", "|-", ">-", ">"):
                    current["run"] = []
                    current["style"] = value.strip()
                    run_indent = 10
                elif key == "run":
                    current["run"] = value.strip()
                    current["style"] = "plain"
        for step in steps:
            if isinstance(step["run"], list):
                step["run"] = cls._join(step["run"], step["style"])
        return steps

    @staticmethod
    def _join(body: list[str], style: str | None) -> str:
        """Join a block scalar's lines the way YAML would, per its style.

        `|` keeps newlines; `>` folds a single newline to a space (blank lines
        stay newlines). Getting this wrong is not cosmetic: a folded body run as
        if it were literal is a different script — `set -euo pipefail pin=…` on
        one line, which bash rejects — so a test that "executes the real body"
        would be executing something GitHub never runs.
        """
        if style in (">", ">-"):
            out: list[str] = []
            for line in body:
                if not line.strip():
                    out.append("\n")
                elif out and out[-1] != "\n":
                    out[-1] = out[-1] + " " + line.strip()
                else:
                    out.append(line.strip())
            return "".join(out).strip()
        return "\n".join(body).rstrip("\n")

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.steps = self._parse_steps(
            (self.root / ".github/workflows/build-check.yml").read_text(encoding="utf-8")
        )
        self.names = [step["name"] for step in self.steps]
        # The parse itself must not be the thing that silently breaks: if the
        # workflow's shape ever stops matching, this fails loudly here rather
        # than reporting an absent step.
        self.assertGreater(len(self.steps), 30, "step parse collapsed")
        self.assertIn(self.GATE, self.names, "step parse lost a known step")

    def _step(self):
        self.assertIn(
            self.STEP, self.names,
            "the unconditional bandit install is gone; lint-nosec-form's "
            "unknown-id check is inert again and no other gate notices",
        )
        return self.steps[self.names.index(self.STEP)]

    def _run_body(self, cwd: Path, extra_env: dict[str, str] | None = None):
        """Run the real step body with `pip` stubbed out. Returns CompletedProcess."""
        bash = shutil.which("bash")
        if bash is None:  # pragma: no cover - POSIX runners always have it
            self.skipTest("bash unavailable; the step body is a bash script")
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        stub = Path(holder.name) / "bin"
        stub.mkdir()
        (stub / "pip").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (stub / "pip").chmod(0o755)
        (stub / "python").write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8"
        )
        (stub / "python").chmod(0o755)
        env = dict(os.environ, PATH=f"{stub}{os.pathsep}{os.environ.get('PATH', '')}")
        env.update(extra_env or {})
        return subprocess.run(  # noqa: S603
            [bash, "-c", self._step()["run"]],
            cwd=cwd, env=env, capture_output=True, text=True, check=False,
        )

    def test_step_is_unconditional_and_immediately_precedes_the_gate(self):
        index = self.names.index(self._step()["name"])
        self.assertFalse(
            self._step()["has_if"],
            "an `if:` here is what made the bandit install skippable in the "
            "first place; the whole point is that it is not",
        )
        self.assertIn(self.GATE, self.names)
        self.assertFalse(
            self._step()["continue_on_error"],
            "continue-on-error neuters the step as completely as deleting it, "
            "and neither lint-ci-parity nor the position check notices",
        )
        self.assertEqual(
            self._step()["style"], "|",
            "the body below is executed verbatim; a folded scalar would run as "
            "one line and is a different script",
        )
        self.assertEqual(
            self.names[index + 1], self.GATE,
            "another step between the install and the gate can replace a shared "
            "transitive dependency of bandit while exiting 0",
        )

    def test_step_body_passes_against_the_real_tree(self):
        try:
            import bandit.core.extension_loader  # noqa: F401,PLC0415
        except Exception:  # noqa: BLE001 - a broken plugin raises more than ImportError
            self.skipTest("bandit not installed; the positive control needs it")
        result = self._run_body(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bandit", result.stdout)

    def test_step_body_fails_when_the_requirements_file_names_no_bandit(self):
        """`pip install ""` exits 0 with no output — the substitution must fail first."""
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        fake = Path(holder.name)
        (fake / "tools").mkdir()
        (fake / "tools/requirements-sast.txt").write_text(
            "pip-audit>=2.10,<3\nsemgrep>=1.166,<2\n", encoding="utf-8"
        )
        result = self._run_body(fake)
        self.assertNotEqual(result.returncode, 0)
        # Assert the cause, not just the exit code: with bandit absent (Gate F's
        # env, where the positive control skips) a step that can never succeed
        # for an unrelated reason would satisfy a bare non-zero check.
        self.assertNotIn("installing pinned:", result.stdout)

    def _bandit_shim(self, extension_loader_source: str) -> str:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        shim = Path(holder.name)
        (shim / "bandit" / "core").mkdir(parents=True)
        (shim / "bandit/__init__.py").write_text("", encoding="utf-8")
        (shim / "bandit/core/__init__.py").write_text("", encoding="utf-8")
        (shim / "bandit/core/extension_loader.py").write_text(
            extension_loader_source, encoding="utf-8"
        )
        return str(shim)

    def test_step_body_fails_when_the_bandit_registry_is_unusable(self):
        """`id_checker()` swallows every exception, so an API move must fail here."""
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        shim = Path(holder.name)
        (shim / "bandit").mkdir()
        (shim / "bandit/__init__.py").write_text("", encoding="utf-8")
        result = self._run_body(self.root, {"PYTHONPATH": str(shim)})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        # It got past the grep and the install, and died on the import.
        self.assertIn("installing pinned:", result.stdout)
        self.assertIn("bandit.core", result.stderr)

    def test_step_body_fails_when_the_registry_resolves_every_id(self):
        """The probe's second direction, which the other cases cannot reach.

        A `check_id` that says yes to everything satisfies the real-id half and
        would leave `lint-nosec-form` reporting no unknown ids while resolving
        `B999` — the same silent pass, from the opposite direction. Without this
        case, deleting ` or loader.MANAGER.check_id("B999")` from the probe
        leaves the suite green; measured.
        """
        shim = self._bandit_shim(
            "class _Manager:\n"
            "    def check_id(self, test_id):\n"
            "        return True\n"
            "MANAGER = _Manager()\n"
        )
        result = self._run_body(self.root, {"PYTHONPATH": shim})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("did not resolve as lint-nosec-form", result.stderr)

    def test_step_body_fails_when_the_registry_resolves_nothing(self):
        """The probe's first direction, so neither half can be deleted unnoticed.

        An importable registry that resolves no id is not the silent-pass shape
        — `lint-nosec-form` would flag every valid suppression instead — but
        without this case the `check_id("B307")` half of the probe can be
        removed and the suite stays green. Both halves get a negative control.
        """
        shim = self._bandit_shim(
            "class _Manager:\n"
            "    def check_id(self, test_id):\n"
            "        return False\n"
            "MANAGER = _Manager()\n"
        )
        result = self._run_body(self.root, {"PYTHONPATH": shim})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("did not resolve as lint-nosec-form", result.stderr)


class CiPytestProvisioningTest(unittest.TestCase):
    """CI provisions pytest before entering pytest-backed gate paths."""

    def test_build_check_installs_pytest_before_make_build_check(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/build-check.yml").read_text(encoding="utf-8")

        # Scoped to the gate-main block. Both offsets used to be file-wide
        # index() calls, and after spec/ci-gate-parallelization split this workflow
        # the install string exists in gate-main AND gate-export-boundary — the pair
        # compared the right occurrences only because gate-main is declared first.
        block = workflow.split("  gate-main:\n", 1)[1].split("\n  gate-sast:\n", 1)[0]

        install = block.index(
            "run: python -m pip install -e packages/agentbundle/ pytest"
        )
        build_check = block.index("- name: Run make build-check")

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

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append(argv)
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

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
    "tools/test-capture-publish-control-evidence.py",
    "tools/test-lint-plugin-route-docs.py",
    "tools/lint-plugin-route-docs.py",
    "tools/test-lint-site-scope-parity.py",
    "tools/lint-site-scope-parity.py",
    "tools/test-check-site-plugin-offers.py",
    "tools/test-lint-pack-descriptions.py",
    "tools/lint-pack-descriptions.py",
    "tools/test-lint-nosec-form.py",
    "tools/lint-nosec-form.py",
    "tools/test-lint-ci-parity.py",
    "tools/test-build-check-windows-workflow.py",
    "tools/test-build-check-workflow.py",
    "tools/assert-sast-chain-reachable.py",
    "tools/lint-ci-parity.py",
    "tools/test-test-all.py",
    "tools/repo/check_contract_drift.py",
]

EXPECTED_PRE_PR_REPO_STEPS = [
    ("agents-md hygiene", [sys.executable, "tools/lint-agents-md.py"]),
    (
        "skill-spec lint",
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "lint",
            "--root",
            ".",
            "--deep",
        ],
    ),
    ("build lint", [sys.executable, "tools/lint-build.py"]),
    ("sso-config lint", [sys.executable, "tools/lint-sso-config.py"]),
    (
        "sso-config lint self-test",
        [sys.executable, "tools/test-lint-sso-config.py"],
    ),
    (
        "knowledge-surface parity",
        [sys.executable, "tools/lint-knowledge-surface-parity.py"],
    ),
    (
        "knowledge-surface parity self-test",
        [sys.executable, "tools/test-lint-knowledge-surface-parity.py"],
    ),
    (
        "pack-evals runner self-test",
        [sys.executable, "tools/test-run-pack-evals.py"],
    ),
    (
        "pack-evals workflow posture",
        [sys.executable, "tools/test-pack-evals-workflow.py"],
    ),
    (
        "pack-journey sync",
        [sys.executable, "tools/build-site.py", "--journeys-only"],
    ),
    (
        "web-journey parity",
        [sys.executable, "tools/lint-web-journey-parity.py"],
    ),
    (
        "web-journey parity self-test",
        [sys.executable, "tools/test-lint-web-journey-parity.py"],
    ),
    (
        "pack-journey lint",
        [sys.executable, "tools/lint-pack-journeys.py"],
    ),
    (
        "pack-journey lint self-test",
        [sys.executable, "tools/test-lint-pack-journeys.py"],
    ),
    (
        "journey-contract lint",
        [sys.executable, "tools/lint-journey-contract.py"],
    ),
    (
        "journey-contract lint self-test",
        [sys.executable, "tools/test-lint-journey-contract.py"],
    ),
]

EXPECTED_VERIFY_ARGV = [
    sys.executable,
    "-m",
    "agentbundle",
    "catalogue",
    "verify",
    "--root",
    ".",
]


class BuildCheckChainTest(unittest.TestCase):
    """`build_check` assembles every Windows-clean step, in order, no SAST."""

    # STUB: AC1, AC2, AC4
    def test_portable_verify_and_build_argv_are_exact(self):
        """The parent runs exact portable commands before repository gates."""
        seen: list[list[str]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append(list(argv))
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(
                argparse.Namespace(packs_dir="packs", output_dir="custom-dist")
            )

        self.assertEqual(
            seen[:2],
            [
                EXPECTED_VERIFY_ARGV,
                [
                    sys.executable,
                    "-m",
                    "agentbundle",
                    "catalogue",
                    "build",
                    "--root",
                    ".",
                    "--output",
                    "custom-dist",
                ],
            ],
        )
        self.assertEqual(seen.count(EXPECTED_VERIFY_ARGV), 1)

    # STUB: AC1, AC3, AC4
    def test_nested_pre_pr_skips_only_its_portable_verify(self):
        """The parent passes an explicit skip while standalone stays verify-first."""
        seen: list[list[str]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append(list(argv))
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        nested = next(
            argv for argv in seen
            if Path(argv[1]).as_posix().endswith("tools/catalogue/pre_pr_catalogue.py")
        )
        self.assertEqual(nested[2:], ["--skip-verify"])

    # STUB: AC4
    def test_pre_pr_modes_preserve_one_ordered_fail_fast_sequence(self):
        """Standalone verifies first; nested mode omits only that event."""
        repo_events = [
            ("repo", label, argv) for label, argv in EXPECTED_PRE_PR_REPO_STEPS
        ]
        hook_event = (
            "hook",
            "shipped pre-pr",
            [sys.executable, "tools/hooks/pre-pr.py"],
        )

        def assert_mode(argv: list[str], verify_first: bool) -> None:
            events: list[tuple[str, str, list[str]]] = []

            def fake_repo_gate(label, command, env=None):
                events.append(("repo", label, list(command)))

            def fake_subprocess(command, check, **kwargs):
                command = list(command)
                if command == EXPECTED_VERIFY_ARGV:
                    events.append(("verify", "catalogue verify", command))
                elif command == hook_event[2]:
                    events.append(hook_event)
                else:
                    self.fail(f"unexpected direct subprocess: {command!r}")
                return mock.Mock(returncode=0)

            with (
                mock.patch.object(pre_pr, "_repo_root", return_value=gc.REPO_ROOT),
                mock.patch.object(pre_pr, "_run", fake_repo_gate),
                mock.patch.object(pre_pr.subprocess, "run", fake_subprocess),
            ):
                self.assertEqual(pre_pr.main(argv), 0)

            expected = [
                *(
                    [("verify", "catalogue verify", EXPECTED_VERIFY_ARGV)]
                    if verify_first
                    else []
                ),
                *repo_events,
                hook_event,
            ]
            self.assertEqual(events, expected)

        for argv, verify_first in (([], True), (["--skip-verify"], False)):
            with self.subTest(argv=argv):
                assert_mode(argv, verify_first)

    def test_full_step_sequence(self):
        order: list[str] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            order.append("subprocess")
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            rc = gc.build_check(args)

        self.assertEqual(rc, 0)
        # 2 module steps (catalogue verify + build) + the script steps + the two
        # directory-scoped steps, each of which spawns twice: a `--collect-only`
        # floor probe and then the run itself.
        _CWD_STEPS = 2
        self.assertEqual(
            len(order), 2 + len(EXPECTED_SCRIPT_STEPS) + _CWD_STEPS * 2
        )

    def test_pre_pr_step_uses_new_path(self):
        """pre-pr-catalogue must call tools/catalogue/pre_pr_catalogue.py."""
        seen: list[list[str]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append(list(argv))
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            args = argparse.Namespace(packs_dir="packs", output_dir="dist")
            gc.build_check(args)

        # The pre-PR step follows the catalogue verify and persistent build.
        pre_pr_argv = seen[2]
        # Path should contain tools/catalogue/pre_pr_catalogue.py
        script_path = Path(pre_pr_argv[1]).as_posix()
        self.assertIn("tools/catalogue/pre_pr_catalogue.py", script_path)

    def test_script_steps_are_windows_clean(self):
        """Every spawned argv is shell-free.

        The claim this test carries is *Windows-cleanliness*, and the argv
        LENGTH was only ever a proxy for it — a cheap stand-in for "nothing
        clever is going on". The proxy became the constraint: a suite that has
        to run from its own directory could not be expressed at all, so those
        gates stayed CI-only (see `_pytest_step_cwd`). Directory-scoping is
        Windows-clean — `subprocess`'s `cwd=` needs no shell and no `cd &&` —
        so the assertion now says what it means: no shell, no `.sh`, no
        POSIX-only quoting, and an argv that is a plain list of tokens.
        """
        seen: list[tuple[list[str], object]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append((list(argv), cwd))
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        for argv, cwd in seen[2:]:  # skip verify + build module steps
            self.assertEqual(argv[0], sys.executable)
            if argv[1:3] == ["-m", "pytest"]:
                # `-q` is present but not necessarily last: a floor probe
                # appends `--collect-only` after it.
                self.assertIn("-q", argv)
                self.assertGreater(len(argv), 3, "a pytest step needs a target")
            elif Path(argv[1]).as_posix().endswith(
                "tools/catalogue/pre_pr_catalogue.py"
            ):
                self.assertEqual(argv[2:], ["--skip-verify"])
            else:
                # A plain script step: interpreter + one script path.
                self.assertEqual(len(argv), 2)
            for token in argv:
                self.assertNotIn(token, ("bash", "sh", "-c"))
                self.assertFalse(token.endswith(".sh"))
                # No shell metacharacters anywhere — the real Windows hazard,
                # and what the length check was standing in for.
                for meta in ("&&", "||", "|", ";", ">", "<", "$("):
                    self.assertNotIn(meta, token, f"shell metacharacter in {token!r}")
            if cwd is not None:
                # A cwd is a real path under the repo, not a shell expression.
                self.assertTrue(Path(cwd).is_absolute(), cwd)

    def test_a_cwd_scoped_step_is_expressible(self):
        """The vocabulary gap this replaced: no way to say "run from here".

        Without it, a suite whose conftest puts the skill's scripts/ on
        sys.path could only run in CI via `working-directory:`, so a local
        `make build-check` silently skipped that gate entirely.
        """
        seen: list[tuple[list[str], object]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append((list(argv), cwd))
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        scoped = [(argv, cwd) for argv, cwd in seen if cwd is not None]
        self.assertTrue(scoped, "no cwd-scoped step ran")
        dirs = {str(cwd) for _argv, cwd in scoped}
        self.assertTrue(
            any(d.endswith("assimilate-primitive") for d in dirs), sorted(dirs)
        )
        self.assertTrue(any(d.endswith("assimilate-repo") for d in dirs), sorted(dirs))
        for argv, _cwd in scoped:
            self.assertEqual(argv[1:3], ["-m", "pytest"])
            # No file targets: the directory IS the target, which is exactly why
            # these steps need a collected-count floor.
            self.assertNotIn("--collect-only", argv[:3])

    def test_spawned_script_paths_in_order(self):
        """The spawned script paths match the expected gate order."""
        seen: list[tuple[list[str], object]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append((list(argv), cwd))
            # `--collect-only` output for the floor probe: enough `::`
            # lines that any wired floor is satisfied under mocking.
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(gc.subprocess, "run", fake_run):
            gc.build_check(argparse.Namespace(packs_dir="packs", output_dir="dist"))

        # seen[0:2] = module steps (catalogue verify + build); the rest are
        # script or directory-scoped steps.
        # Directory-scoped steps are excluded: they name no repo-root path (the
        # cwd is the target), so they belong to the cwd test, not this one.
        spawned = [
            Path(argv[3] if argv[1:3] == ["-m", "pytest"] else argv[1]).as_posix()
            for argv, cwd in seen[2:]
            if cwd is None
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
