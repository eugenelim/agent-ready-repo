"""Falsification tests for the worktree hygiene deletion boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Literal
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import worktree_hygiene as hygiene  # noqa: E402


class FakeGit:
    def __init__(
        self,
        root: Path,
        ignored: set[Path] | None = None,
        tracked: set[Path] | None = None,
        worktrees: list[Path] | None = None,
        common_dir: Path | None = None,
        fail_command: str = "",
    ) -> None:
        self.root = root
        self.ignored = ignored or set()
        self.tracked = tracked or set()
        self.worktrees = worktrees or [root]
        self.common_dir = common_dir or root / ".git"
        self.fail_command = fail_command
        self.calls: list[list[str]] = []

    def __call__(
        self,
        argv: list[str],
        *,
        input: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del env
        self.calls.append(argv)
        if "worktree" in argv:
            output = "".join(
                f"worktree {worktree}\0"
                "HEAD abc\0"
                "branch refs/heads/test\0\0"
                for worktree in self.worktrees
            )
            return subprocess.CompletedProcess(argv, 0, output, "")
        if "--literal-pathspecs" in argv and "check-ignore" in argv:
            path = next(
                (value for value in (input or "").split("\0") if value),
                "",
            )
            error = (
                f"fatal: {path}: pathspec magic not supported "
                "by this command: 'literal'"
            )
            return subprocess.CompletedProcess(argv, 128, "", error)
        if self.fail_command and self.fail_command in argv:
            error = f"{self.fail_command} fixture failure"
            code = 2 if self.fail_command == "check-ignore" else 1
            return subprocess.CompletedProcess(argv, code, "", error)
        if "rev-parse" in argv:
            output = str(self.common_dir) + "\n"
            return subprocess.CompletedProcess(argv, 0, output, "")
        paths = {
            Path(value)
            for value in (input or "").split("\0")
            if value
        }
        if "ls-files" in argv:
            paths = {
                Path(value) for value in argv[argv.index("--") + 1 :]
            }
        if "ls-files" in argv and "--literal-pathspecs" not in argv:
            paths = {
                Path(str(path).removeprefix(":(literal)"))
                for path in paths
            }
        matched = self.ignored if "check-ignore" in argv else self.tracked
        output = "\0".join(str(path) for path in sorted(paths & matched))
        suffix = "\0" if output else ""
        code = 1 if "check-ignore" in argv and not output else 0
        return subprocess.CompletedProcess(argv, code, output + suffix, "")


class WorktreeHygieneTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = (Path(self.temp.name) / "work tree-é").resolve()
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.fake = FakeGit(self.root, ignored={Path("build")})

    def tearDown(self) -> None:
        self.temp.cleanup()

    def candidate(self, name: str = "build", content: str = "x") -> Path:
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "artifact").write_text(content, encoding="utf-8")
        return path

    def clean(
        self,
        category: set[str] | None = None,
        **kwargs: Any,
    ) -> tuple[int, list[str]]:
        return hygiene.clean(
            self.root,
            category or {"generated"},
            apply=kwargs.pop("apply", True),
            include_dependencies=kwargs.pop("include_dependencies", False),
            protected=kwargs.pop("protected", set()),
            runner=self.fake,
            **kwargs,
        )

    def clean_with_reported_candidate(
        self,
        target: Path,
        *,
        protected: bool,
    ) -> tuple[int, list[str]]:
        """Run clean against one deliberately shaped scan candidate."""
        report: dict[str, Any] = {
            "git_common_dir": str(self.root / ".git"),
            "warnings": [],
            "worktrees": [
                {
                    "path": str(self.root),
                    "candidates": [
                        {
                            "path": str(target),
                            "category": "generated",
                            "bytes": 1,
                            "ignored": True,
                            "protected": protected,
                            "git_admin": False,
                        }
                    ],
                }
            ],
        }
        original = hygiene.scan

        def reported_scan(*args: Any, **kwargs: Any) -> dict[str, Any]:
            del args, kwargs
            return report

        hygiene.scan = reported_scan
        try:
            return self.clean()
        finally:
            hygiene.scan = original

    def assert_guard_reason(
        self,
        target: Path,
        lines: list[str],
        expected: str,
        *,
        phase: Literal["selection", "pre-deletion"],
    ) -> None:
        """Assert that *target* was rejected in the expected safety phase."""
        display_path = str(target.parent.resolve() / target.name)
        selected = [
            index
            for index, line in enumerate(lines)
            if line.startswith(f"selected {display_path}:")
        ]
        all_skipped = [
            index
            for index, line in enumerate(lines)
            if line.startswith(f"warning: skipped {display_path}:")
        ]
        all_aborted = [
            index
            for index, line in enumerate(lines)
            if line.startswith(f"aborted {display_path}:")
        ]
        skipped = [index for index in all_skipped if expected in lines[index]]
        aborted = [index for index in all_aborted if expected in lines[index]]
        if phase == "selection":
            self.assertTrue(
                skipped,
                f"{display_path} was not rejected during selection: {lines}",
            )
            self.assertEqual(skipped, all_skipped, "unexpected selection reason")
            self.assertEqual(selected, [], "selection rejection followed selection")
            self.assertEqual(all_aborted, [], "selection rejection appeared as an abort")
        else:
            self.assertTrue(selected, f"{display_path} was not selected: {lines}")
            self.assertTrue(aborted, f"{display_path} was not aborted: {lines}")
            self.assertEqual(aborted, all_aborted, "unexpected pre-deletion reason")
            self.assertLess(selected[0], aborted[0])
            self.assertEqual(all_skipped, [], "pre-deletion rejection appeared in selection")

    def assert_selected_candidate(
        self,
        target: Path,
        lines: list[str],
    ) -> None:
        """Assert that *target* passed every safety guard and was selected."""
        display_path = str(target.parent.resolve() / target.name)
        receipt = "\n".join(lines)
        self.assertIn(f"selected {display_path}:", receipt)
        self.assertNotIn(f"warning: skipped {display_path}:", receipt)
        self.assertNotIn(f"aborted {display_path}:", receipt)

    def test_clean_without_apply_deletes_nothing(self) -> None:
        target = self.candidate()
        code, lines = self.clean(apply=False)
        receipt = "\n".join(lines)
        self.assertEqual(code, 0)
        self.assert_selected_candidate(target, lines)
        self.assertIn("clean receipt: dry run", receipt)
        self.assertIn("summary: selected=1", receipt)
        self.assertTrue(target.exists())
        self.assertIn("remaining largest candidates", receipt)

    def test_clean_defaults_to_current_worktree_only(self) -> None:
        current = self.candidate()
        peer = self.root.parent / "peer"
        peer.mkdir()
        (peer / ".git").mkdir()
        peer_candidate = peer / "build"
        peer_candidate.mkdir()
        (peer_candidate / "artifact").write_text("x", encoding="utf-8")
        runner = FakeGit(
            self.root,
            ignored={Path("build")},
            worktrees=[self.root, peer],
        )
        code, lines = hygiene.clean(
            self.root,
            {"generated"},
            apply=False,
            include_dependencies=False,
            protected=set(),
            runner=runner,
        )
        receipt = "\n".join(lines)
        self.assertEqual(code, 0)
        self.assertIn(str(current.resolve()), receipt)
        self.assertNotIn(str(peer_candidate.resolve()), receipt)

    def test_tracked_build_is_rejected(self) -> None:
        target = self.candidate()
        self.fake.tracked = {Path("build")}
        self.fake.ignored = {Path("build")}
        _, lines = self.clean()
        self.assertTrue(target.exists())
        self.assert_guard_reason(target, lines, "tracked", phase="selection")

    def test_literal_pathspec_candidate_with_tracked_content_is_rejected(self) -> None:
        target = self.root / ":(literal)foo" / "build"
        target.mkdir(parents=True)
        (target / "artifact").write_text("tracked", encoding="utf-8")
        relative = Path(":(literal)foo/build")
        self.fake.ignored = {relative}
        self.fake.tracked = {relative}
        _, lines = self.clean()
        self.assertTrue(target.exists())
        self.assert_guard_reason(target, lines, "tracked", phase="selection")

    def test_literal_pathspec_flag_is_only_used_by_ls_files(self) -> None:
        self.candidate()
        hygiene.scan(self.root, runner=self.fake)
        self.clean(apply=False)
        ignore_calls = [
            call for call in self.fake.calls if "check-ignore" in call
        ]
        tracked_calls = [call for call in self.fake.calls if "ls-files" in call]
        self.assertTrue(ignore_calls)
        self.assertTrue(tracked_calls)
        self.assertTrue(
            all("--literal-pathspecs" not in call for call in ignore_calls)
        )
        self.assertTrue(
            all("--literal-pathspecs" in call for call in tracked_calls)
        )

    def test_ignored_candidate_symlink_outside_is_rejected(self) -> None:
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "keep").write_text("keep", encoding="utf-8")
        (self.root / "build").symlink_to(
            outside,
            target_is_directory=True,
        )
        safe = self.candidate("dist")
        self.fake.ignored = {Path("build"), Path("dist")}
        code, lines = self.clean()
        self.assertEqual(code, 0)
        self.assertTrue(outside.exists())
        self.assertFalse(safe.exists())
        self.assert_guard_reason(
            self.root / "build",
            lines,
            "link or root escape",
            phase="selection",
        )

    def test_mount_point_candidate_is_rejected(self) -> None:
        target = self.candidate()

        def simulated_mount(path: Path) -> bool:
            return path == target

        _, lines = self.clean(mount_check=simulated_mount)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "mount point",
            phase="selection",
        )

    def test_nested_mount_refuses_candidate_and_continues(self) -> None:
        target = self.candidate()
        nested_mount = target / "data"
        nested_mount.mkdir()
        nested_content = nested_mount / "keep"
        nested_content.write_text("outside data", encoding="utf-8")
        safe = self.candidate("dist")
        self.fake.ignored = {Path("build"), Path("dist")}

        def simulated_mount(path: Path) -> bool:
            return path == nested_mount

        _, lines = self.clean(mount_check=simulated_mount)
        self.assertTrue(target.exists())
        self.assertTrue(nested_content.exists())
        self.assertFalse(safe.exists())
        self.assert_guard_reason(
            target,
            lines,
            "mount point",
            phase="selection",
        )

    def test_cross_device_child_refuses_candidate_and_continues(self) -> None:
        target = self.candidate()
        boundary = target / "data"
        boundary.mkdir()
        nested_content = boundary / "keep"
        nested_content.write_text("outside data", encoding="utf-8")
        safe = self.candidate("dist")
        self.fake.ignored = {Path("build"), Path("dist")}
        original_lstat = Path.lstat

        def different_device(path: Path) -> os.stat_result:
            result = original_lstat(path)
            if path != boundary:
                return result
            values = list(result)
            values[2] = result.st_dev + 1
            return os.stat_result(values)

        with mock.patch.object(Path, "lstat", different_device):
            _, lines = self.clean(mount_check=lambda _: False)
        self.assertTrue(target.exists())
        self.assertTrue(nested_content.exists())
        self.assertFalse(safe.exists())
        self.assert_guard_reason(
            target,
            lines,
            "filesystem boundary",
            phase="selection",
        )

    def test_linux_mountinfo_parser_decodes_mount_point(self) -> None:
        mountinfo = "36 25 0:32 / /tmp/work\\040tree/data rw - ext4 /dev/root rw\n"
        self.assertEqual(
            hygiene._parse_mountinfo(mountinfo),
            {Path("/tmp/work tree/data").resolve()},
        )

    def test_default_mount_check_uses_one_mountinfo_snapshot(self) -> None:
        target = self.root / "same-device-bind"
        target.mkdir()
        reads = 0
        original = hygiene._linux_mount_points

        def mount_points() -> set[Path]:
            nonlocal reads
            reads += 1
            return {target}

        hygiene._linux_mount_points = mount_points
        try:
            mount_check = hygiene._default_mount_check()
        finally:
            hygiene._linux_mount_points = original
        self.assertTrue(mount_check(target))
        self.assertTrue(mount_check(target))
        self.assertEqual(reads, 1)

    def test_mount_snapshot_refreshes_before_each_deletion(self) -> None:
        target = self.candidate()
        safe = self.candidate("dist")
        self.fake.ignored = {Path("build"), Path("dist")}
        snapshots = 0
        original = hygiene._default_mount_check

        def mount_snapshot() -> hygiene.MountCheck:
            nonlocal snapshots
            snapshots += 1
            mounted = snapshots > 1
            return lambda path: mounted and path == target

        hygiene._default_mount_check = mount_snapshot
        try:
            _, lines = self.clean()
        finally:
            hygiene._default_mount_check = original
        self.assertTrue(target.exists())
        self.assertFalse(safe.exists())
        self.assertEqual(snapshots, 3)
        self.assert_guard_reason(
            target,
            lines,
            "mount point",
            phase="pre-deletion",
        )

    def test_selected_unregistered_and_stale_are_safe(self) -> None:
        selected = self.root / ".." / "not registered"
        report = hygiene.scan(self.root, [selected], self.fake)
        self.assertIn("not registered", " ".join(report["warnings"]))
        self.assertEqual(report["worktrees"], [])

    def test_porcelain_z_preserves_quote_risk_characters(self) -> None:
        risky = self.root / 'quote"tab\tback\\slash'
        payload = (
            f"worktree {risky}\0"
            "HEAD abc\0"
            "detached\0\0"
        )
        worktrees = hygiene._parse_porcelain(payload)
        self.assertEqual(worktrees[0].path, risky.resolve())
        self.assertTrue(worktrees[0].detached)

    def test_stale_porcelain_record_is_report_only(self) -> None:
        missing = self.root.parent / "gone"
        worktree = hygiene.Worktree(
            missing,
            prunable="gitdir file points to non-existent location",
        )
        result = hygiene.scan_worktree(worktree)
        self.assertEqual(result.candidates, [])

    def test_unregistered_parent_selection_cannot_delete(self) -> None:
        target = self.candidate()
        self.fake.ignored = {Path("build")}
        outside = self.root.parent / "not-registered"
        code, lines = self.clean(selected=[outside])
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assertIn(
            "selected worktree is not registered",
            "\n".join(lines),
        )

    def test_candidate_containing_common_dir_is_not_deleted(self) -> None:
        target = self.candidate()
        common = target / "common-git-dir"
        common.mkdir()
        self.fake = FakeGit(
            self.root,
            ignored={Path("build")},
            common_dir=common,
        )
        code, lines = self.clean()
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "git administration",
            phase="selection",
        )

    def test_common_dir_discovery_failure_refuses_cleanup(self) -> None:
        target = self.candidate()
        runner = FakeGit(
            self.root,
            ignored={Path("build")},
            fail_command="rev-parse",
        )
        code, lines = hygiene.clean(
            self.root,
            {"generated"},
            apply=True,
            include_dependencies=False,
            protected=set(),
            runner=runner,
        )
        receipt = "\n".join(lines)
        self.assertEqual(code, 2)
        self.assertTrue(target.exists())
        self.assertIn("git common directory unavailable", receipt)
        self.assertIn("refusing cleanup", receipt)
        self.assertNotIn(f"selected {target.resolve()}:", receipt)

    def test_candidate_containing_nested_git_is_not_deleted(self) -> None:
        target = self.candidate()
        (target / "nested" / ".git").mkdir(parents=True)
        self.fake.ignored = {Path("build")}
        scanned = hygiene.scan_worktree(hygiene.Worktree(self.root))
        build = next(
            candidate
            for candidate in scanned.candidates
            if candidate.path.name == "build"
        )
        self.assertTrue(build.git_admin)
        code, lines = self.clean()
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "git administration",
            phase="selection",
        )

    def test_worktree_root_git_directory_is_pruned(self) -> None:
        hidden_candidate = self.root / ".git" / "build"
        hidden_candidate.mkdir()
        result = hygiene.scan_worktree(hygiene.Worktree(self.root))
        self.assertNotIn(
            hidden_candidate.resolve(),
            {candidate.canonical_path for candidate in result.candidates},
        )

    def test_loop_run_inside_candidate_isolated_guard(self) -> None:
        target = self.candidate()
        session = target / ".loop-run"
        session.mkdir()
        (session / "state").write_text("active", encoding="utf-8")
        self.fake.ignored = {Path("build")}
        code, lines = self.clean()
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected state or lock",
            phase="selection",
        )

    def test_lock_inside_candidate_rejects_candidate(self) -> None:
        target = self.candidate()
        (target / "worker.lock").write_text("held", encoding="utf-8")
        self.fake.ignored = {Path("build")}
        _, lines = self.clean()
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected state or lock",
            phase="selection",
        )

    def test_protection_is_reasserted_before_each_mutation(self) -> None:
        target = self.candidate()
        safe = self.candidate("dist")
        self.fake.ignored = {Path("build"), Path("dist")}
        original = self.fake

        class ProtectingGit(FakeGit):
            def __call__(
                inner_self,
                argv: list[str],
                *,
                input: str | None = None,
                env: dict[str, str] | None = None,
            ) -> subprocess.CompletedProcess[str]:
                result = original(argv, input=input, env=env)
                if "ls-files" in argv:
                    session = target / ".loop-run"
                    session.mkdir(exist_ok=True)
                return result

        code, lines = hygiene.clean(
            self.root,
            {"generated"},
            apply=True,
            include_dependencies=False,
            protected=set(),
            runner=ProtectingGit(self.root, self.fake.ignored),
        )
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assertFalse(safe.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected state or lock",
            phase="pre-deletion",
        )
        self.assertIn("safety changed", "\n".join(lines))

    def test_candidate_safety_predicate_runs_in_both_deletion_phases(self) -> None:
        target = self.candidate()
        calls: list[Path] = []
        original = hygiene._candidate_safety_reason

        def recording_reason(
            candidate: hygiene.Candidate,
            root: Path,
            common: Path,
            protected: set[Path],
            mount_check: hygiene.MountCheck,
        ) -> str:
            calls.append(candidate.path)
            return original(
                candidate,
                root,
                common,
                protected,
                mount_check,
            )

        hygiene._candidate_safety_reason = recording_reason
        try:
            _, lines = self.clean()
        finally:
            hygiene._candidate_safety_reason = original
        self.assertEqual(calls, [target, target])
        self.assertFalse(target.exists())
        self.assert_selected_candidate(target, lines)

    def test_dependency_needs_acknowledgement(self) -> None:
        target = self.candidate("node_modules")
        self.fake.ignored = {Path("node_modules")}
        code, lines = self.clean({"dependencies"})
        self.assertEqual(code, 2)
        self.assertTrue(target.exists())
        self.assertIn(
            "refusing dependency cleanup without --include-dependencies",
            "\n".join(lines),
        )

    def test_shared_cache_category_is_refused_programmatically(self) -> None:
        target = self.root / ".local-browsers"
        target.mkdir()
        (target / "revision").mkdir()
        self.fake.ignored = {Path(".local-browsers")}
        code, lines = self.clean({"shared_caches"})
        receipt = "\n".join(lines)
        self.assertEqual(code, 2)
        self.assertTrue(target.exists())
        self.assertIn("unsupported categories: shared_caches", receipt)
        self.assertNotIn(f"selected {target}:", receipt)

    def test_protected_category_is_refused_programmatically(self) -> None:
        target = self.root / ".loop-run"
        target.mkdir()
        (target / "state").write_text("keep", encoding="utf-8")
        self.fake.ignored = {Path(".loop-run")}
        code, lines = self.clean({"protected"})
        receipt = "\n".join(lines)
        self.assertEqual(code, 2)
        self.assertTrue(target.exists())
        self.assertIn("unsupported categories: protected", receipt)
        self.assertNotIn(f"selected {target}:", receipt)

    def test_reported_protected_candidate_flag_is_refused(self) -> None:
        target = self.candidate()
        self.fake.ignored = {Path("build")}
        _, lines = self.clean_with_reported_candidate(target, protected=True)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected state or lock",
            phase="selection",
        )

    def test_protected_candidate_name_is_refused(self) -> None:
        target = self.root / ".context"
        target.mkdir()
        (target / "state").write_text("keep", encoding="utf-8")
        self.fake.ignored = {Path(".context")}
        _, lines = self.clean_with_reported_candidate(target, protected=False)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected state or lock",
            phase="selection",
        )

    def test_nested_invocation_protects_current_dependencies(self) -> None:
        target = self.candidate("node_modules")
        nested = self.root / "tools" / "nested"
        nested.mkdir(parents=True)
        runner = FakeGit(self.root, ignored={Path("node_modules")})
        code, lines = hygiene.clean(
            nested,
            {"dependencies"},
            apply=True,
            include_dependencies=True,
            protected=set(),
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "protected worktree",
            phase="selection",
        )

    def test_check_ignore_failure_skips_entire_worktree(self) -> None:
        target = self.candidate()
        runner = FakeGit(
            self.root,
            ignored={Path("build")},
            fail_command="check-ignore",
        )
        code, lines = hygiene.clean(
            self.root,
            {"generated"},
            apply=True,
            include_dependencies=False,
            protected=set(),
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "check-ignore fixture failure",
            phase="selection",
        )

    def test_ls_files_failure_skips_entire_worktree(self) -> None:
        target = self.candidate()
        runner = FakeGit(
            self.root,
            ignored={Path("build")},
            fail_command="ls-files",
        )
        code, lines = hygiene.clean(
            self.root,
            {"generated"},
            apply=True,
            include_dependencies=False,
            protected=set(),
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "ls-files fixture failure",
            phase="selection",
        )

    def test_check_ignore_exit_one_reports_individual_not_ignored_reason(self) -> None:
        target = self.candidate("build", "x" * 10000)
        self.fake.ignored = set()
        _, lines = self.clean()
        receipt = "\n".join(lines)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "not ignored",
            phase="selection",
        )
        self.assertNotIn("git check-ignore failed", receipt)

    def test_json_is_deterministic_and_unicode_safe(self) -> None:
        self.candidate()
        options = {
            "ensure_ascii": False,
            "sort_keys": True,
            "separators": (",", ":"),
        }
        one = json.dumps(
            hygiene.scan(self.root, runner=self.fake),
            **options,
        )
        two = json.dumps(
            hygiene.scan(self.root, runner=self.fake),
            **options,
        )
        self.assertEqual(one, two)
        self.assertIn("é", one)

    def test_missing_entry_is_warning_not_failure(self) -> None:
        result = hygiene.ScanResult(hygiene.Worktree(self.root))
        hygiene._size(self.root / "gone", result.warnings)
        self.assertTrue(result.warnings)

    def test_traversal_and_git_calls_are_bounded(self) -> None:
        self.candidate("build")
        self.candidate("dist")
        result = hygiene.scan_worktree(hygiene.Worktree(self.root))
        self.assertEqual(result.traversals, 1)
        self.fake.ignored = {Path("build"), Path("dist")}
        self.clean()
        ignore_calls = sum(
            "check-ignore" in call for call in self.fake.calls
        )
        tracked_calls = sum("ls-files" in call for call in self.fake.calls)
        self.assertEqual(ignore_calls, 1)
        self.assertEqual(tracked_calls, 1)

    def test_no_liveness_claim_is_emitted(self) -> None:
        report = hygiene.scan(self.root, runner=self.fake)
        encoded = json.dumps(report)
        self.assertNotIn("live", encoded)
        self.assertNotIn("active", encoded)

    def test_hermetic_browser_directory_is_report_only(self) -> None:
        local = self.root / ".local-browsers"
        local.mkdir()
        report = hygiene.scan(self.root, runner=self.fake)
        self.assertEqual(report["shared_caches"][0]["mode"], "hermetic")
        self.assertEqual(report["worktrees"][0]["total_local"], 0)
        self.assertTrue(local.exists())

    def test_shared_cache_outside_worktrees_is_diagnostic(self) -> None:
        worktrees = [hygiene.Worktree(self.root)]
        caches = hygiene._cache_diagnostics(worktrees, self.fake, [])
        self.assertFalse(caches[0]["beneath_worktree"])

    def test_duplicate_browser_revision_across_worktrees_is_reported(self) -> None:
        first = self.root / ".local-browsers" / "chromium-1234"
        first.mkdir(parents=True)
        peer = self.root.parent / "peer-browser"
        second = peer / ".local-browsers" / "chromium-1234"
        second.mkdir(parents=True)
        (peer / ".git").mkdir()
        runner = FakeGit(self.root, worktrees=[self.root, peer])
        previous = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
        try:
            report = hygiene.scan(self.root, runner=runner)
        finally:
            if previous is None:
                os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
            else:
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = previous
        duplicates = [
            cache
            for cache in report["shared_caches"]
            if cache["kind"] == "playwright-duplicate-revision"
        ]
        self.assertEqual(duplicates[0]["revision"], "chromium-1234")
        self.assertEqual(
            duplicates[0]["paths"],
            sorted(
                [
                    str(first.parent.resolve()),
                    str(second.parent.resolve()),
                ]
            ),
        )

    def test_installed_distribution_target_is_not_deleted(self) -> None:
        peer = self.root.parent / "peer-installed"
        peer.mkdir()
        (peer / ".git").mkdir()
        target = peer / ".venv"
        target.mkdir()
        (target / "artifact").write_text("x", encoding="utf-8")
        distribution_root = target / "lib" / "example"
        runner = FakeGit(
            self.root,
            ignored={Path(".venv")},
            worktrees=[self.root, peer],
        )

        class Distribution:
            def locate_file(self, path: str) -> Path:
                del path
                return distribution_root

        original = hygiene.importlib.metadata.distributions
        hygiene.importlib.metadata.distributions = lambda: [Distribution()]
        try:
            code, lines = hygiene.clean(
                self.root,
                {"dependencies"},
                apply=True,
                include_dependencies=True,
                protected=set(),
                selected=[peer],
                runner=runner,
            )
        finally:
            hygiene.importlib.metadata.distributions = original
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assert_guard_reason(
            target,
            lines,
            "resolves into target",
            phase="selection",
        )


if __name__ == "__main__":
    unittest.main()
