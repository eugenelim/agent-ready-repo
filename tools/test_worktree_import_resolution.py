"""Contract tests for the worktree doctor's isolated agentbundle probe."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import worktree_hygiene as hygiene  # noqa: E402


class ImportResolutionTest(unittest.TestCase):
    INVALID_JSON_RECORD = "not-json"
    NON_OBJECT_RECORD = "[]"
    UNKNOWN_STATE_RECORD = '{"state": "weird"}'
    NON_STRING_PATH_RECORD = '{"state": "resolved", "path": 7}'

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / ".git").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def completed(
        self,
        payload: dict[str, object] | None = None,
        *,
        record: str | None = None,
        prefix: str = "",
        returncode: int = 0,
        stderr: str = "",
    ) -> subprocess.CompletedProcess[str]:
        stdout = ""
        if record is not None:
            stdout = prefix + hygiene.IMPORT_SENTINEL + record + "\n"
        elif payload is not None:
            stdout = prefix + hygiene.IMPORT_SENTINEL + json.dumps(payload) + "\n"
        return subprocess.CompletedProcess([], returncode, stdout, stderr)

    def resolution(
        self,
        payload: dict[str, object] | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        result = self.completed(payload, **kwargs)

        def runner(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return result

        return hygiene._agentbundle_import_resolution(self.root, runner)

    def git_runner(
        self,
        argv: list[str],
        *,
        input: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del input, env
        if "worktree" in argv:
            output = (
                f"worktree {self.root}\0HEAD abc\0branch refs/heads/test\0\0"
            )
            return subprocess.CompletedProcess(argv, 0, output, "")
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(
                argv, 0, str(self.root / ".git") + "\n", ""
            )
        if "check-ignore" in argv:
            return subprocess.CompletedProcess(argv, 1, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "")

    def test_resolution_inside_worktree_is_in_human_report(self) -> None:
        resolved = self.root / "agentbundle/__init__.py"

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return self.completed({"state": "resolved", "path": str(resolved)})

        resolution = self.resolution({"state": "resolved", "path": str(resolved)})
        self.assertEqual(resolution["status"], "inside")
        self.assertIsNone(hygiene._import_resolution_warning(resolution))
        human = hygiene._human(
            hygiene.scan(self.root, runner=self.git_runner, import_runner=probe)
        )
        self.assertIn("agentbundle resolves inside this worktree", human)
        for value in (str(resolved), sys.executable, str(self.root), "PYTHONPATH"):
            self.assertIn(value, human)

    def test_outside_resolution_is_a_json_and_human_finding(self) -> None:
        outside = Path("/mnt/published/agentbundle/__init__.py")
        calls = 0

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            nonlocal calls
            del argv, cwd, env
            calls += 1
            return self.completed({"state": "resolved", "path": str(outside)})

        report = hygiene.scan(self.root, runner=self.git_runner, import_runner=probe)
        self.assertEqual(calls, 1)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(
            set(report),
            {
                "schema_version",
                "repository",
                "git_common_dir",
                "measurement",
                "agentbundle_import",
                "worktrees",
                "shared_caches",
                "warnings",
                "totals",
            },
        )
        resolution = report["agentbundle_import"]
        self.assertEqual(resolution["status"], "outside")
        self.assertEqual(resolution["path"], str(outside))
        encoded = json.dumps(report, sort_keys=True)
        human = hygiene._human(report)
        expected = f"agentbundle resolves outside this worktree, at {outside}"
        self.assertIn(expected, encoded)
        self.assertIn(expected, human)
        self.assertEqual(human.count(expected), 1)
        for value in (sys.executable, str(self.root), "PYTHONPATH"):
            self.assertIn(value, encoded)
            self.assertIn(value, human)

    def test_human_output_keeps_unrelated_warnings_once(self) -> None:
        outside = Path("/mnt/published/agentbundle/__init__.py")

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return self.completed({"state": "resolved", "path": str(outside)})

        report = hygiene.scan(self.root, runner=self.git_runner, import_runner=probe)
        unrelated_warning = "git discovery retained warning"
        report["warnings"].append(unrelated_warning)
        human = hygiene._human(report)
        import_finding = f"agentbundle resolves outside this worktree, at {outside}"
        self.assertEqual(human.count(import_finding), 1)
        self.assertIn(f"warning: {unrelated_warning}", human)

    def test_scan_status_is_independent_of_invocation_directory(self) -> None:
        nested = self.root / "web"
        nested.mkdir()
        resolved = self.root / "packages/agentbundle/agentbundle/__init__.py"

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return self.completed({"state": "resolved", "path": str(resolved)})

        root_report = hygiene.scan(
            self.root, runner=self.git_runner, import_runner=probe
        )
        nested_report = hygiene.scan(
            nested, runner=self.git_runner, import_runner=probe
        )
        self.assertEqual(root_report["agentbundle_import"]["status"], "inside")
        self.assertEqual(
            nested_report["agentbundle_import"]["status"],
            root_report["agentbundle_import"]["status"],
        )

    def test_worktree_local_resolution_outside_invocation_cwd_is_inside(self) -> None:
        nested = self.root / "web"
        nested.mkdir()
        captured: dict[str, Path] = {}
        resolved = self.root / "packages/agentbundle/agentbundle/__init__.py"

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, env
            captured["cwd"] = cwd
            return self.completed({"state": "resolved", "path": str(resolved)})

        report = hygiene.scan(nested, runner=self.git_runner, import_runner=probe)
        self.assertEqual(report["agentbundle_import"]["status"], "inside")
        self.assertEqual(captured["cwd"], self.root)

    def test_polluted_stdout_still_uses_the_sentinel_record(self) -> None:
        resolution = self.resolution(
            {"state": "resolved", "path": "/mnt/published/agentbundle/__init__.py"},
            prefix="pyenv: cannot rehash: lock is held\n",
        )
        self.assertEqual(resolution["status"], "outside")

    def test_failed_nonzero_and_unparseable_children_are_inconclusive(self) -> None:
        def cannot_run(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            raise OSError("child unavailable")

        def times_out(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            raise subprocess.TimeoutExpired("probe", hygiene.IMPORT_TIMEOUT_SECONDS)

        with self.subTest("cannot run"):
            resolution = hygiene._agentbundle_import_resolution(self.root, cannot_run)
            self.assertEqual(resolution["status"], "inconclusive")
            self.assertIn("could not run", str(resolution["detail"]))
        with self.subTest("timeout"):
            resolution = hygiene._agentbundle_import_resolution(self.root, times_out)
            self.assertEqual(resolution["status"], "inconclusive")
            self.assertIn("timed out", str(resolution["detail"]))
        with self.subTest("non-zero"):
            resolution = self.resolution(returncode=1, stderr="probe failed")
            self.assertEqual(resolution["status"], "inconclusive")
            self.assertIn("probe failed", str(resolution["detail"]))
        with self.subTest("unparseable"):
            resolution = self.resolution(None)
            self.assertEqual(resolution["status"], "inconclusive")
            self.assertIn("unambiguous", str(resolution["detail"]))

    def test_invalid_probe_records_are_inconclusive(self) -> None:
        fixtures = (
            ("invalid JSON", self.INVALID_JSON_RECORD),
            ("non-object", self.NON_OBJECT_RECORD),
            ("unknown state", self.UNKNOWN_STATE_RECORD),
            ("non-string path", self.NON_STRING_PATH_RECORD),
        )
        for label, record in fixtures:
            with self.subTest(label):
                resolution = self.resolution(record=record)
                self.assertEqual(resolution["status"], "inconclusive")
                self.assertIn("invalid result", str(resolution["detail"]))

    def test_absent_module_is_reported_distinctly(self) -> None:
        resolution = self.resolution({"state": "absent"})
        self.assertEqual(resolution["status"], "absent")
        self.assertIn("absent", hygiene._import_resolution_warning(resolution) or "")

    def test_probe_isolated_from_pythonpath_and_cwd_imports(self) -> None:
        captured: dict[str, str] = {}
        captured_argv: list[str] = []

        def probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del cwd
            captured_argv.extend(argv)
            captured.update(env)
            return self.completed(
                {
                    "state": "resolved",
                    "path": str(self.root / "agentbundle/__init__.py"),
                }
            )

        with mock.patch.dict(os.environ, {"PYTHONPATH": "worktree-source"}):
            os.environ.pop("PYTHONDONTWRITEBYTECODE", None)
            resolution = hygiene._agentbundle_import_resolution(self.root, probe)
        self.assertEqual(
            captured_argv,
            [sys.executable, "-P", "-c", hygiene.IMPORT_PROBE],
        )
        self.assertNotIn("PYTHONPATH", captured)
        self.assertEqual(captured["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(
            resolution["removed_environment_inputs"],
            ["PYTHONPATH", "cwd sys.path entry (-P)"],
        )

    def test_failed_worktree_discovery_is_an_inconclusive_finding(self) -> None:
        def runner(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            del input, env
            if "worktree" in argv:
                return subprocess.CompletedProcess(
                    argv, 128, "", "fatal: not a git repository"
                )
            return subprocess.CompletedProcess(argv, 1, "", "")

        def import_runner(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            raise AssertionError("import probe must not run without a worktree")

        report = hygiene.scan(
            self.root, runner=runner, import_runner=import_runner
        )
        self.assertEqual(report["agentbundle_import"]["status"], "inconclusive")
        self.assertIn("fatal: not a git repository", report["warnings"])
        detail = "no registered worktree contains the invocation directory"
        self.assertEqual(report["agentbundle_import"]["detail"], detail)
        self.assertTrue(
            any(detail in warning for warning in report["warnings"])
        )

    def test_clean_worktree_fallback_is_unchanged(self) -> None:
        def runner(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            del input, env
            if "worktree" in argv:
                return subprocess.CompletedProcess(
                    argv, 128, "", "fatal: unavailable"
                )
            return subprocess.CompletedProcess(argv, 1, "", "")

        self.assertEqual(hygiene._current_worktree(self.root, runner), self.root)

    def test_empty_worktree_discovery_is_an_inconclusive_finding(self) -> None:
        def runner(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            del input, env
            if "worktree" in argv:
                return subprocess.CompletedProcess(argv, 0, "HEAD abc\0\0", "")
            if "rev-parse" in argv:
                return subprocess.CompletedProcess(
                    argv, 0, str(self.root / ".git") + "\n", ""
                )
            return subprocess.CompletedProcess(argv, 1, "", "")

        def import_runner(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            raise AssertionError("import probe must not run without a worktree")

        report = hygiene.scan(
            self.root, runner=runner, import_runner=import_runner
        )
        self.assertEqual(report["agentbundle_import"]["status"], "inconclusive")
        detail = "no registered worktree contains the invocation directory"
        self.assertEqual(report["agentbundle_import"]["detail"], detail)
        self.assertTrue(
            any(detail in warning for warning in report["warnings"])
        )

    def test_uncontained_invocation_is_an_inconclusive_finding(self) -> None:
        other_worktree = self.root / "other-worktree"
        other_worktree.mkdir()

        def runner(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            del input, env
            if "worktree" in argv:
                return subprocess.CompletedProcess(
                    argv, 0, f"worktree {other_worktree}\0HEAD abc\0\0", ""
                )
            if "rev-parse" in argv:
                return subprocess.CompletedProcess(
                    argv, 0, str(self.root / ".git") + "\n", ""
                )
            return subprocess.CompletedProcess(argv, 1, "", "")

        def import_runner(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            raise AssertionError("import probe must not run without a worktree")

        report = hygiene.scan(
            self.root, runner=runner, import_runner=import_runner
        )
        self.assertEqual(report["agentbundle_import"]["status"], "inconclusive")
        detail = "no registered worktree contains the invocation directory"
        self.assertEqual(report["agentbundle_import"]["detail"], detail)
        self.assertTrue(
            any(detail in warning for warning in report["warnings"])
        )

    def test_unmeasured_scan_emits_provenance_without_status(self) -> None:
        report = hygiene.scan(
            self.root,
            runner=self.git_runner,
            include_import_resolution=False,
        )
        provenance = report["agentbundle_import"]
        self.assertEqual(provenance["interpreter"], sys.executable)
        self.assertEqual(provenance["cwd"], str(self.root))
        self.assertEqual(
            provenance["removed_environment_inputs"],
            ["PYTHONPATH", "cwd sys.path entry (-P)"],
        )
        self.assertNotIn("status", provenance)
        report["warnings"] = ["first ordinary warning", "second ordinary warning"]
        human = hygiene._human(report)
        for warning in report["warnings"]:
            self.assertIn(f"warning: {warning}", human)


if __name__ == "__main__":
    unittest.main()
