"""Tests for the repo-only OKF compiler check gate and both platforms' wiring.

The gate itself lives in `tools/check-okf-managed-packs.py`. Two callers reach
it — the Linux aggregator (`tools/catalogue/pre_pr_catalogue.py`) and the Windows
compat suite's stage list — and the last two tests here pin those call sites,
because a gate nothing invokes is indistinguishable from a gate that passes.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "catalogue"))
import pre_pr_catalogue as pre_pr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    """Import a hyphenated script by path (not importable by name)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


okf_check = _load("check_okf_managed_packs", REPO_ROOT / "tools" / "check-okf-managed-packs.py")
audit_requirements = _load("audit_requirements", REPO_ROOT / "tools" / "audit-requirements.py")


def _write_pack(root: Path, name: str, *, okf_path: str = "okf/demo") -> Path:
    pack = root / "packs" / name
    bundle = pack / okf_path
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n'
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# Demo\n",
        encoding="utf-8",
    )
    concepts = bundle / "concepts"
    concepts.mkdir(exist_ok=True)
    (concepts / "example.md").write_text(
        "---\n"
        'title: "Example"\n'
        'type: "Reference"\n'
        'status: "Active"\n'
        "---\n"
        "# Example\n",
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        "\n".join(
            [
                "[pack]",
                f'name = "{name.lstrip("_")}"',
                "",
                "[pack.metadata.okf]",
                'profile = "agentbundle-okf/v1"',
                "",
                "[[pack.metadata.okf.bundles]]",
                'id = "demo"',
                f'path = "{okf_path}"',
                '"router-skill" = "demo-router"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return pack


class OkfCheckGateTests(unittest.TestCase):
    def test_discovery_includes_underscore_pilots_and_excludes_plain_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "_okf-pilot")
            _write_pack(root, "managed")
            plain = root / "packs" / "plain"
            plain.mkdir(parents=True)
            (plain / "pack.toml").write_text('[pack]\nname = "plain"\n', encoding="utf-8")

            discovered = [path.name for path in okf_check.managed_pack_dirs(root)]

        self.assertEqual(discovered, ["_okf-pilot", "managed"])

    def test_a_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "managed")
            compiler = okf_check.compiler_script(REPO_ROOT)
            write = subprocess.run(
                [sys.executable, str(compiler), "--root", str(root), "--pack", "managed"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(write.returncode, 0, write.stderr)

            with (
                mock.patch.object(okf_check, "compiler_script", return_value=compiler),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 0)

    def test_an_unsafe_bundle_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "unsafe", okf_path="okf/../escape")
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    okf_check, "compiler_script", return_value=okf_check.compiler_script(REPO_ROOT)
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("unsafe failed", stderr.getvalue())

    def test_the_gate_runs_the_compiler_in_check_mode(self) -> None:
        """`--check` is the whole gate: without it this is a silent rewriter.

        Every other assertion in this file survives dropping `--check` — a
        drifted tree still exits non-zero (as an ownership conflict rather than
        output drift), so the failure text still matches. Only the argv
        distinguishes verifying from overwriting.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "managed")
            seen: list[list[str]] = []

            class _Ok:
                returncode = 0
                stdout = ""
                stderr = ""

            def record(argv, **kwargs):
                seen.append(list(argv))
                return _Ok()

            with (
                mock.patch.object(
                    okf_check, "compiler_script", return_value=okf_check.compiler_script(REPO_ROOT)
                ),
                mock.patch.object(okf_check.subprocess, "run", record),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 0)

        self.assertEqual(len(seen), 1)
        argv = seen[0]
        self.assertIn("--check", argv)
        self.assertIn("--pack", argv)
        self.assertEqual(argv[argv.index("--pack") + 1], "managed")

    def test_a_drifted_tree_is_reported_without_being_rewritten(self) -> None:
        """Reporting drift must not repair it.

        A gate that rewrites the tree it is checking passes on its second run
        and gates nothing.
        """
        compiler = okf_check.compiler_script(REPO_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "managed")
            subprocess.run(
                [sys.executable, str(compiler), "--root", str(root), "--pack", "managed"],
                check=True,
                capture_output=True,
            )
            router = root / "packs" / "managed" / ".apm" / "skills" / "demo-router" / "SKILL.md"
            drifted = router.read_text(encoding="utf-8") + "\nmanual drift\n"
            router.write_text(drifted, encoding="utf-8")

            with (
                mock.patch.object(okf_check, "compiler_script", return_value=compiler),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)

            self.assertEqual(router.read_text(encoding="utf-8"), drifted)

    def test_a_catalogue_with_no_managed_packs_passes_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plain = root / "packs" / "plain"
            plain.mkdir(parents=True)
            (plain / "pack.toml").write_text('[pack]\nname = "plain"\n', encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(okf_check.main(["--root", str(root)]), 0)

        self.assertIn("no packs declare managed OKF metadata", stdout.getvalue())

    def test_a_hung_compiler_fails_the_gate_rather_than_the_job(self) -> None:
        """A timeout that returns True turns a hung compiler into a passing gate.

        Without this, the natural mutation of the handler is green, and a hang
        surfaces only as a CI job timeout that names neither the gate nor the
        pack.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "slow")

            def hang(argv, **kwargs):
                raise subprocess.TimeoutExpired(argv, okf_check._COMPILE_TIMEOUT_SECONDS)

            stderr = io.StringIO()
            with (
                mock.patch.object(
                    okf_check, "compiler_script", return_value=okf_check.compiler_script(REPO_ROOT)
                ),
                mock.patch.object(okf_check.subprocess, "run", hang),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("timed out after", stderr.getvalue())

    def test_the_gate_survives_a_cp1252_console(self) -> None:
        """The Windows encoding guard is load-bearing and no other test reaches it.

        Every other test redirects stdout to a StringIO, which has no
        `reconfigure`, so the guard no-ops throughout the suite. Deleting it
        makes the gate's own success line raise UnicodeEncodeError on a cp1252
        console — a failure that looks like a broken gate, not a broken locale.
        """
        import os

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "packs").mkdir()
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "tools" / "check-okf-managed-packs.py"),
                 "--root", tmp],
                capture_output=True,
                text=True,
                # Decode as UTF-8 rather than the parent's locale. Without this
                # the one test whose subject IS encoding determinism is the only
                # locale-sensitive test in the file: under an ASCII parent it
                # dies in `communicate` on the child's correct UTF-8 bytes,
                # before any assertion runs.
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "cp1252"},
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("✓", result.stdout)

    def test_the_gate_does_not_pull_in_pyyaml(self) -> None:
        """pyyaml is an authoring-time prerequisite; the gate must not need it.

        Asserted by loading the script in a fresh interpreter and inspecting
        `sys.modules`, not by grepping for `import yaml` — that grep passes for
        `from yaml import safe_load`, `import yaml as y`, and importlib.
        """
        probe = (
            "import importlib.util, sys;"
            "spec = importlib.util.spec_from_file_location('g', sys.argv[1]);"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
            "print('yaml' in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe, str(REPO_ROOT / "tools" / "check-okf-managed-packs.py")],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "False", result.stderr)

    def test_every_managed_pack_is_checked_not_just_the_first(self) -> None:
        """The gate's whole purpose is that no platform scans a smaller set.

        Every other test here stages one pack, so `for pack_dir in packs[:1]`
        left the suite green while `core` — which sorts after the underscore
        pilot — silently stopped being verified on both platforms.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "_pilot")
            _write_pack(root, "core")
            _write_pack(root, "extra")
            seen: list[str] = []

            class _Ok:
                returncode = 0
                stdout = ""
                stderr = ""

            def record(argv, **kwargs):
                seen.append(argv[argv.index("--pack") + 1])
                return _Ok()

            with (
                mock.patch.object(
                    okf_check, "compiler_script", return_value=okf_check.compiler_script(REPO_ROOT)
                ),
                mock.patch.object(okf_check.subprocess, "run", record),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 0)

        self.assertEqual(seen, ["_pilot", "core", "extra"])

    def test_a_failing_pack_does_not_stop_the_remaining_packs(self) -> None:
        """One Windows job should report every affected pack, not just the first."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "alpha")
            _write_pack(root, "beta")
            seen: list[str] = []

            class _Fail:
                returncode = 1
                stdout = ""
                stderr = ""

            def record(argv, **kwargs):
                seen.append(argv[argv.index("--pack") + 1])
                return _Fail()

            stderr = io.StringIO()
            with (
                mock.patch.object(
                    okf_check, "compiler_script", return_value=okf_check.compiler_script(REPO_ROOT)
                ),
                mock.patch.object(okf_check.subprocess, "run", record),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)

        self.assertEqual(seen, ["alpha", "beta"])
        self.assertIn("2 of 2 pack(s) failed", stderr.getvalue())
        self.assertIn("alpha, beta", stderr.getvalue())

    def test_a_root_without_a_packs_tree_is_an_error_not_a_clean_pass(self) -> None:
        """A mis-rooted invocation must not read as verified."""
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(okf_check.main(["--root", tmp]), 1)
            self.assertIn("no packs/ directory", stderr.getvalue())

    def test_an_unclassifiable_pack_fails_instead_of_leaving_the_gate(self) -> None:
        """A typo in an OKF block must not quietly remove a pack from the scan."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = root / "packs" / "broken"
            broken.mkdir(parents=True)
            (broken / "pack.toml").write_text("[pack]\nname = ", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("unreadable", stderr.getvalue())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "packs" / "wrong"
            wrong.mkdir(parents=True)
            (wrong / "pack.toml").write_text(
                '[pack]\nname = "wrong"\n\n[pack.metadata]\nokf = "yes"\n', encoding="utf-8"
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("not a table", stderr.getvalue())

        for body, expected in (
            ('name = "x"\n', "no [pack] table"),
            ('[pack]\nname = "x"\n\n[other]\nk = 1\n', None),
            ('pack = "scalar"\n', "not a table"),
            ('[pack]\nname = "x"\nmetadata = "scalar"\n', "pack.metadata as str"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                d = root / "packs" / "odd"
                d.mkdir(parents=True)
                (d / "pack.toml").write_text(body, encoding="utf-8")
                stderr = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                    rc = okf_check.main(["--root", str(root)])
                if expected is None:
                    # A valid pack that simply declares no OKF block is the one
                    # sanctioned skip; it must stay a clean pass.
                    self.assertEqual(rc, 0)
                else:
                    self.assertEqual(rc, 1)
                    self.assertIn(expected, stderr.getvalue())

    def test_a_pack_directory_without_a_manifest_is_an_error(self) -> None:
        """A half-created or half-deleted pack must not drop out of the scan."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "packs" / "orphan").mkdir(parents=True)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("has no pack.toml", stderr.getvalue())

    def test_managed_packs_without_a_compiler_fail_rather_than_report_clean(self) -> None:
        """A broken checkout must not read as "nothing to verify"."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pack(root, "managed")
            missing = root / "no" / "such" / "compile_okf.py"
            stderr = io.StringIO()
            with (
                mock.patch.object(okf_check, "compiler_script", return_value=missing),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(okf_check.main(["--root", str(root)]), 1)
            self.assertIn("no compiler", stderr.getvalue())

    def test_linux_aggregator_invokes_the_shared_check(self) -> None:
        """Asserted by running the aggregator, not by grepping it.

        A source grep for the script name survives deleting the call, because
        the helper that builds the path still names the file — the gate would
        read as wired while nothing invoked it.
        """
        self.assertEqual(
            pre_pr._okf_check_script(REPO_ROOT),
            REPO_ROOT / "tools" / "check-okf-managed-packs.py",
        )

        calls: list[tuple[str, list[str]]] = []
        cwd = Path.cwd()
        try:
            with (
                mock.patch.object(pre_pr, "_repo_root", return_value=REPO_ROOT),
                mock.patch.object(pre_pr, "_run", lambda label, argv, env=None: calls.append(
                    (label, argv)
                )),
                # `_run` covers the gate list, but main() also shells out
                # directly to the shipped hook; unmocked, this test would fail
                # on unrelated live-tree state (knowledge lint, caps gate).
                mock.patch.object(
                    pre_pr.subprocess, "run", lambda *a, **k: mock.Mock(returncode=0)
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                pre_pr.main(["--skip-verify"])
        finally:
            import os

            os.chdir(cwd)

        labels = [label for label, _ in calls]
        self.assertIn("okf compiler checks", labels)
        argv = next(argv for label, argv in calls if label == "okf compiler checks")
        self.assertIn(str(REPO_ROOT / "tools" / "check-okf-managed-packs.py"), argv)

    def test_windows_compat_suite_invokes_the_shared_check(self) -> None:
        """Asserted by running the suite with its step runner captured.

        Kept beside its Linux twin rather than in the engine's own test tree:
        the two call sites are one contract, and splitting them is how one half
        gets deleted without the other noticing.

        Grepping the stage list for the script name passes for any arrangement
        where the tuple exists but is never reached — moved behind a branch, or
        the list rebuilt below it. The adopter-facing hook the suite already
        runs carries no OKF gate, so a silently unreachable stage would leave
        the Windows determinism claim resting on a suite that never compiles.
        """
        from agentbundle.catalogue_tooling import self_host_windows

        executed: list[tuple[str, list[str]]] = []

        def record(label, cmd, cwd):
            executed.append((label, list(cmd)))
            return 0

        with mock.patch.object(self_host_windows, "_step", record):
            self.assertEqual(self_host_windows.run_windows_compat(REPO_ROOT), 0)

        labels = [label for label, _ in executed]
        self.assertIn("okf compiler checks", labels)
        argv = next(cmd for label, cmd in executed if label == "okf compiler checks")
        self.assertIn(str(REPO_ROOT / "tools" / "check-okf-managed-packs.py"), argv)
        self.assertIn("--root", argv)

    def test_dependency_audit_and_scanners_cover_okf_compiler_paths(self) -> None:
        requirements = (REPO_ROOT / "tools" / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("pyyaml>=6.0", requirements.lower())

        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("SAST_DIRS := tools packs packages tests", makefile)
        self.assertIn("tools/run-bandit-gate.py $(SAST_DIRS)", makefile)
        self.assertIn("$(SEMGREP_EXCLUDE) $(SAST_DIRS)", makefile)
        # test-audit-requirements.py owns the comment-rejecting invocation check.
        resolved_tools_manifests = audit_requirements.tools_requirements_manifests(
            REPO_ROOT / "tools"
        )
        self.assertIn(REPO_ROOT / "tools" / "requirements.txt", resolved_tools_manifests)
        self.assertIn("$$(find packs -name requirements.txt | sort)", makefile)
        self.assertIn("--optional-group lint", makefile)
        self.assertIn("packages/agentbundle/pyproject.toml", makefile)


if __name__ == "__main__":
    unittest.main()
