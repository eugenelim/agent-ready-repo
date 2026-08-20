"""Contract tests for optional, non-mutating worktree lifecycle hooks."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import worktree_hygiene as hygiene  # noqa: E402


class LifecycleHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.current = self.root / "current"
        self.merged = self.root / "merged"
        self.no_merge_or_prune_signal = self.root / "no-merge-or-prune-signal"
        self.removed = self.root / "removed"
        # A worktree on the default branch itself. `--merged <default>` always
        # includes the default branch, so without an explicit exclusion the
        # primary checkout lands in the disposability bucket.
        self.default_branch_worktree = self.root / "default-branch"
        self.observed_argv: list[list[str]] = []
        for path in (
            self.current,
            self.merged,
            self.no_merge_or_prune_signal,
            self.removed,
            self.default_branch_worktree,
        ):
            path.mkdir()
            (path / ".git").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def runner(
        self,
        argv: list[str],
        *,
        input: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del input, env
        self.observed_argv.append(argv)
        if "worktree" in argv:
            output = "\0".join(
                (
                    f"worktree {self.current}",
                    "HEAD current",
                    "branch refs/heads/current",
                    "",
                    f"worktree {self.merged}",
                    "HEAD merged",
                    "branch refs/heads/merged",
                    "",
                    f"worktree {self.no_merge_or_prune_signal}",
                    "HEAD no-merge-or-prune-signal",
                    "branch refs/heads/no-merge-or-prune-signal",
                    "",
                    f"worktree {self.default_branch_worktree}",
                    "HEAD default-branch",
                    "branch refs/heads/main",
                    "",
                    f"worktree {self.removed}",
                    "HEAD removed",
                    "branch refs/heads/removed",
                    "prunable gitdir file points to non-existent location",
                    "",
                )
            )
            return subprocess.CompletedProcess(argv, 0, output, "")
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, str(self.root / ".git"), "")
        if "remote" in argv:
            return subprocess.CompletedProcess(argv, 0, "origin\n", "")
        if "symbolic-ref" in argv:
            return subprocess.CompletedProcess(
                argv, 0, "refs/remotes/origin/main\n", ""
            )
        if "for-each-ref" in argv:
            return subprocess.CompletedProcess(
                argv, 0, "refs/heads/merged\nrefs/heads/main\n", ""
            )
        return subprocess.CompletedProcess(argv, 1, "", "unexpected Git command")

    def inside_probe(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        del argv, cwd, env
        payload = json.dumps(
            {
                "path": str(self.current / "agentbundle/__init__.py"),
                "state": "resolved",
            }
        )
        return subprocess.CompletedProcess(
            [], 0, hygiene.IMPORT_SENTINEL + payload + "\n", ""
        )

    def outside_probe(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        del argv, cwd, env
        payload = json.dumps(
            {
                "path": "/mnt/published/agentbundle/__init__.py",
                "state": "resolved",
            }
        )
        return subprocess.CompletedProcess(
            [], 0, hygiene.IMPORT_SENTINEL + payload + "\n", ""
        )

    def test_optional_hooks_report_observed_categories_without_orca(self) -> None:
        source = Path(hygiene.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("orca", source)
        for command in ("after-create", "before-run", "after-run"):
            with self.subTest(command):
                result = hygiene.lifecycle_hook(
                    command, self.current, runner=self.runner
                )
                self.assertEqual(result.code, 0)
                self.assertIn(f"merged: {self.merged}", result.lines)
                self.assertIn(f"prune-signal: {self.removed}", result.lines)
                self.assertNotIn(f"removed: {self.removed}", result.lines)
                self.assertIn(
                    f"no-merge-or-prune-signal: {self.no_merge_or_prune_signal}",
                    result.lines,
                )
                self.assertIn(f"currently-active: {self.current}", result.lines)
                self.assertIn(
                    "currently-active observation: registered worktree containing "
                    "the invocation directory; no liveness claim",
                    result.lines,
                )
                self.assertIn(
                    "no-merge-or-prune-signal observation: registered worktree "
                    "without a prune signal, default-branch merge signal, or "
                    "current-invocation containment; no activity or liveness "
                    "inference",
                    result.lines,
                )

    def test_merged_uses_the_git_determined_default_branch(self) -> None:
        hygiene.lifecycle_hook("after-create", self.current, runner=self.runner)
        merged_argv = next(
            argv for argv in self.observed_argv if "for-each-ref" in argv
        )
        self.assertEqual(
            merged_argv[merged_argv.index("--merged") + 1],
            "refs/remotes/origin/main",
        )

    def test_merged_query_is_scoped_to_the_report_repository(self) -> None:
        hygiene.lifecycle_hook("after-create", self.current, runner=self.runner)
        merged_argv = next(
            argv for argv in self.observed_argv if "for-each-ref" in argv
        )
        self.assertEqual(merged_argv[:3], ["git", "-C", str(self.current)])

    def test_default_branch_worktree_is_not_reported_merged(self) -> None:
        # The default branch is vacuously merged into itself, so listing the
        # worktree checked out on it beside genuinely-merged feature branches
        # invites deleting the primary checkout. It belongs in the no-signal
        # bucket instead. The porcelain gives refs/heads/<name> while the
        # default arrives as refs/remotes/<remote>/<name>; comparing those two
        # directly never matches, which is how this first slipped through.
        result = hygiene.lifecycle_hook(
            "after-create", self.current, runner=self.runner
        )
        self.assertNotIn(f"merged: {self.default_branch_worktree}", result.lines)
        self.assertIn(
            f"no-merge-or-prune-signal: {self.default_branch_worktree}",
            result.lines,
        )

    def test_merged_is_undetermined_when_the_remote_is_ambiguous(self) -> None:
        # Two remotes (origin + upstream is ordinary) and zero remotes both make
        # the default branch unknowable. Picking `remote_names[0]` would answer
        # confidently from an arbitrary remote, or raise IndexError on none; the
        # only honest answer is undetermined. The sibling test above covers the
        # symbolic-ref failure, which is a different branch.
        for label, output in (("two remotes", "origin\nupstream\n"), ("none", "")):
            with self.subTest(label):

                def runner_with_remotes(
                    argv: list[str],
                    *,
                    input: str | None = None,
                    env: dict[str, str] | None = None,
                    _output: str = output,
                ) -> subprocess.CompletedProcess[str]:
                    if argv[-1] == "remote":
                        return subprocess.CompletedProcess(argv, 0, _output, "")
                    return self.runner(argv, input=input, env=env)

                result = hygiene.lifecycle_hook(
                    "after-create", self.current, runner=runner_with_remotes
                )
                self.assertIn("merged: undetermined", result.lines)
                self.assertIn(
                    "warning: could not determine default branch: "
                    "expected exactly one remote",
                    result.lines,
                )

    def test_merged_is_undetermined_when_default_branch_is_unavailable(self) -> None:
        def runner_without_default(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            if "symbolic-ref" in argv:
                return subprocess.CompletedProcess(argv, 1, "", "missing remote HEAD")
            return self.runner(argv, input=input, env=env)

        result = hygiene.lifecycle_hook(
            "after-create", self.current, runner=runner_without_default
        )
        self.assertIn("merged: undetermined", result.lines)
        self.assertIn(
            "warning: could not determine default branch: missing remote HEAD",
            result.lines,
        )

    def test_main_exposes_each_optional_lifecycle_command(self) -> None:
        result = hygiene.LifecycleResult(0, ("lifecycle report:",))
        with (
            mock.patch.object(
                hygiene, "lifecycle_hook", return_value=result
            ) as hook,
            redirect_stdout(io.StringIO()),
        ):
            for command in (
                "after-create",
                "before-run",
                "after-run",
                "before-remove",
            ):
                self.assertEqual(hygiene.main([command]), 0)
        self.assertEqual(
            [call.args[0] for call in hook.call_args_list],
            ["after-create", "before-run", "after-run", "before-remove"],
        )

    def test_before_remove_is_report_only_for_an_inside_import(self) -> None:
        result = hygiene.lifecycle_hook(
            "before-remove",
            self.current,
            runner=self.runner,
            import_runner=self.inside_probe,
        )
        self.assertEqual(result.code, 0)
        self.assertIn(
            "before-remove passed: this hook does not remove worktrees or branches",
            result.lines,
        )
        self.assertTrue(
            all(
                not ("worktree" in argv and ({"remove", "prune"} & set(argv)))
                for argv in self.observed_argv
            )
        )
        self.assertTrue(self.current.exists())
        self.assertTrue(self.merged.exists())
        self.assertTrue(self.no_merge_or_prune_signal.exists())

    def test_before_remove_reuses_its_lifecycle_discovery(self) -> None:
        discovery_available = True

        def one_discovery_runner(
            argv: list[str],
            *,
            input: str | None = None,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            nonlocal discovery_available
            if "worktree" in argv:
                if not discovery_available:
                    return subprocess.CompletedProcess(
                        argv, 1, "", "a second discovery is unavailable"
                    )
                discovery_available = False
            return self.runner(argv, input=input, env=env)

        result = hygiene.lifecycle_hook(
            "before-remove",
            self.current,
            runner=one_discovery_runner,
            import_runner=self.inside_probe,
        )
        self.assertEqual(result.code, 0)
        self.assertIn(
            "before-remove passed: this hook does not remove worktrees or branches",
            result.lines,
        )

    def test_before_remove_refuses_absent_and_inconclusive_imports(self) -> None:
        def absent_probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return subprocess.CompletedProcess(
                [], 0, hygiene.IMPORT_SENTINEL + '{"state": "absent"}\n', ""
            )

        def inconclusive_probe(
            argv: list[str], *, cwd: Path, env: dict[str, str]
        ) -> subprocess.CompletedProcess[str]:
            del argv, cwd, env
            return subprocess.CompletedProcess([], 0, "", "")

        for label, probe in (
            ("absent", absent_probe),
            ("inconclusive", inconclusive_probe),
        ):
            with self.subTest(label):
                result = hygiene.lifecycle_hook(
                    "before-remove",
                    self.current,
                    runner=self.runner,
                    import_runner=probe,
                )
                self.assertEqual(result.code, 2)
                self.assertIn(
                    "refusing worktree removal: agentbundle import resolution is "
                    f"{label}, not inside this worktree",
                    result.lines,
                )

    def test_before_remove_refuses_a_shadowing_import(self) -> None:
        result = hygiene.lifecycle_hook(
            "before-remove",
            self.current,
            runner=self.runner,
            import_runner=self.outside_probe,
        )
        self.assertEqual(result.code, 2)
        self.assertIn(
            "refusing worktree removal: agentbundle import resolution is outside, not inside this worktree",
            result.lines,
        )
        self.assertTrue(self.current.exists())

    def test_before_remove_refuses_an_existing_protection_channel(self) -> None:
        result = hygiene.lifecycle_hook(
            "before-remove",
            self.current,
            protected={self.current},
            runner=self.runner,
            import_runner=self.inside_probe,
        )
        self.assertEqual(result.code, 2)
        self.assertIn(
            f"refusing worktree removal: protected worktree: {self.current}",
            result.lines,
        )


if __name__ == "__main__":
    unittest.main()
