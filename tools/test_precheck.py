"""Construction tests for tools/precheck.py (AC-0001 to AC-0010)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent / "precheck.py"
_spec = importlib.util.spec_from_file_location("precheck", _PATH)
assert _spec is not None and _spec.loader is not None
precheck = importlib.util.module_from_spec(_spec)
sys.modules["precheck"] = precheck
_spec.loader.exec_module(precheck)

PY = sys.executable


class Recorder:
    """Injected executor: records argv, returns scripted results."""

    def __init__(self, results: dict[str, tuple[int, str]] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.results = results or {}

    def __call__(self, argv: list[str], capture: str) -> tuple[int, str]:
        self.calls.append(argv)
        for key, value in self.results.items():
            if key in " ".join(argv):
                return value
        return 0, ""


def _run(
    paths: list[str],
    rec: Recorder,
    *,
    with_tests: bool = False,
    installed: bool = True,
    exists: bool = True,
    has_tests_dir: bool = True,
) -> int:
    return precheck.run_checks(
        paths,
        base="origin/main",
        python=PY,
        with_tests=with_tests,
        executor=rec,
        is_installed=lambda _tool: installed,
        file_exists=lambda _p: exists,
        dir_exists=lambda _p: has_tests_dir,
    )


def _flat(rec: Recorder) -> list[str]:
    return [" ".join(c) for c in rec.calls]


def test_ac0001_no_trigger(capsys: pytest.CaptureFixture[str]) -> None:
    rec = Recorder()
    assert _run(["docs/README.md"], rec) == 0
    assert "no trigger matched" in capsys.readouterr().out
    assert rec.calls == []


def test_ac0002_apm_runs_self_host_check() -> None:
    rec = Recorder({"self-host": (3, "")})
    assert _run(["packs/foo/.apm/skills/x/notes.md"], rec) == 3
    assert f"{PY} -m agentbundle catalogue self-host --root . --check" in _flat(rec)


def test_ac0003_skill_md_runs_deep_lint() -> None:
    rec = Recorder({"catalogue lint": (4, "")})
    assert _run(["packs/foo/skills/x/SKILL.md"], rec) == 4
    assert f"{PY} -m agentbundle catalogue lint --root . --deep" in _flat(rec)


@pytest.mark.parametrize(
    "path",
    [
        "packs/core/seeds/a.md",
        "packs/core/.apm/skills/x/SKILL.md",
        "packs/core/pack.toml",
        "packs/core/.claude-plugin/plugin.json",
    ],
)
def test_ac0004_core_content_runs_release_check(path: str) -> None:
    rec = Recorder({"check-core-release": (5, "")})
    assert _run([path], rec) == 5
    assert f"{PY} tools/check-core-release.py --base=origin/main" in _flat(rec)


def test_ac0005_core_tests_skip_release_check() -> None:
    rec = Recorder()
    _run(["packs/core/tests/test_x.py"], rec)
    assert not any("check-core-release" in c for c in _flat(rec))


def _bandit_argv(rec: Recorder) -> list[str]:
    return next(c for c in rec.calls if c[1:3] == ["-m", "bandit"])


def test_ac0006_bandit_scans_existing_files_under_roots() -> None:
    rec = Recorder()
    paths = ["tools/a.py", "packs/x/b.py", "docs/c.py", "tools/gone.py", "tools/n.md"]
    precheck_exists = {"tools/a.py", "packs/x/b.py", "docs/c.py"}
    rc = precheck.run_checks(
        paths, base="origin/main", python=PY, with_tests=False, executor=rec,
        is_installed=lambda _t: True, file_exists=lambda p: p in precheck_exists,
    )
    assert rc == 0
    argv = _bandit_argv(rec)
    assert "tools/a.py" in argv and "packs/x/b.py" in argv
    assert "docs/c.py" not in argv and "tools/gone.py" not in argv
    gate = precheck.load_gate()
    for flag in gate.FLOOR:
        assert flag in argv
    assert gate.CONFIG in argv


def test_ac0006_low_only_exits_zero_medium_and_stderr_fail() -> None:
    assert _run(["tools/a.py"], Recorder({"bandit": (0, "")})) == 0
    assert _run(["tools/a.py"], Recorder({"bandit": (1, "")})) != 0
    assert _run(["tools/a.py"], Recorder({"bandit": (0, "[main] WARNING nosec")})) != 0


def test_ac0007_missing_tools_skip(capsys: pytest.CaptureFixture[str]) -> None:
    rec = Recorder()
    paths = ["packs/foo/.apm/x.md", "packs/foo/skills/x/SKILL.md", "tools/a.py"]
    assert _run(paths, rec, installed=False) == 0
    out = capsys.readouterr().out
    assert "skipped: agentbundle not installed" in out
    assert "skipped: PyYAML not installed" in out
    assert "skipped: bandit not installed" in out
    assert not any("agentbundle" in c or "bandit" in c for c in _flat(rec))


def test_ac0007_only_the_missing_tool_skips(capsys: pytest.CaptureFixture[str]) -> None:
    rec = Recorder()
    rc = precheck.run_checks(
        ["packs/foo/.apm/x.md", "tools/a.py"], base="b", python=PY, with_tests=False,
        executor=rec, is_installed=lambda t: t != "bandit", file_exists=lambda _p: True,
    )
    assert rc == 0
    assert "skipped: bandit not installed" in capsys.readouterr().out
    assert any("self-host" in c for c in _flat(rec))


def test_ac0008_unresolvable_base(capsys: pytest.CaptureFixture[str]) -> None:
    rec = Recorder({"rev-parse": (128, "")})
    rc = precheck.main(["--base", "nope/ref"], executor=rec, python=PY)
    assert rc == 2
    assert "nope/ref" in capsys.readouterr().err
    assert all("rev-parse" in c for c in _flat(rec))


def test_ac0008_git_missing() -> None:
    def boom(argv: list[str], capture: str) -> tuple[int, str]:
        raise FileNotFoundError("git")

    assert precheck.main([], executor=boom, python=PY) == 2


def test_ac0008_paths_union_and_default_base() -> None:
    rec = Recorder({
        "diff --name-only": (0, "a.md\0b.md\0"),
        "status": (0, " M b.md\0?? c.md\0R  new.md\0old.md\0"),
    })
    paths = precheck.changed_paths("origin/main", rec)
    assert paths == ["a.md", "b.md", "c.md", "new.md", "old.md"]
    diff_argv = next(c for c in rec.calls if "diff" in c)
    assert "-z" in diff_argv and "origin/main...HEAD" in diff_argv
    assert precheck.parse_args([]).base == "origin/main"


def test_ac0009_prints_pytest_command_without_running(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rec = Recorder()
    _run(["packs/foo/tests/test_a.py", "packs/bar/.apm/x.md"], rec)
    out = capsys.readouterr().out
    assert "python -m pytest packs/foo/tests -q" in out
    assert "python -m pytest packs/bar/tests -q" in out
    assert not any("pytest" in c for c in _flat(rec))


def test_ac0010_with_tests_runs_per_pack_and_propagates() -> None:
    rec = Recorder({"packs/bar/tests": (1, "")})
    rc = _run(["packs/foo/tests/test_a.py", "packs/bar/.apm/x.md"], rec, with_tests=True)
    assert rc != 0
    flat = _flat(rec)
    assert f"{PY} -m pytest packs/foo/tests -q" in flat
    assert f"{PY} -m pytest packs/bar/tests -q" in flat


def test_ac0008_failed_diff_ends_run_with_status_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rec = Recorder({"diff --name-only": (128, "")})
    assert precheck.main(["--base", "origin/main"], executor=rec, python=PY) == 2
    captured = capsys.readouterr()
    assert "origin/main" in captured.err and "diff" in captured.err
    assert "no trigger matched" not in captured.out
    assert all(c[0] == "git" for c in rec.calls)


def test_ac0008_failed_status_ends_run_with_status_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rec = Recorder({"status": (128, "")})
    assert precheck.main(["--base", "origin/main"], executor=rec, python=PY) == 2
    assert "status" in capsys.readouterr().err
    assert all(c[0] == "git" for c in rec.calls)


def test_committed_non_ascii_path_reaches_bandit() -> None:
    rec = Recorder({"diff --name-only": (0, "packages/agentbundle/\u00e9.py\0")})
    paths = precheck.changed_paths("origin/main", rec)
    assert paths == ["packages/agentbundle/\u00e9.py"]
    diff_argv = next(c for c in rec.calls if "diff" in c)
    assert "core.quotePath=false" in diff_argv
    assert _run(paths, Recorder()) == 0


def test_ac0010_signal_killed_check_is_nonzero() -> None:
    rec = Recorder({"self-host": (-9, ""), "bandit": (0, "")})
    assert _run(["packs/foo/.apm/x.md", "tools/a.py"], rec) != 0


def test_ac0009_pack_without_tests_dir_is_named_skip(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rec = Recorder()
    assert _run(["packs/contracts/.apm/x.md"], rec, with_tests=True, has_tests_dir=False) == 0
    out = capsys.readouterr().out
    assert "packs/contracts" in out and "skipped" in out
    assert not any("pytest" in c for c in _flat(rec))
    assert "pytest" not in out
    _run(["packs/contracts/.apm/x.md"], rec, with_tests=False, has_tests_dir=False)
    assert "pytest" not in capsys.readouterr().out


def test_ac0007_skip_line_names_check_and_tool(capsys: pytest.CaptureFixture[str]) -> None:
    _run(["packs/foo/.apm/x.md", "packs/foo/skills/x/SKILL.md", "tools/a.py"], Recorder(),
         installed=False)
    lines = capsys.readouterr().out.splitlines()
    for check, text in [
        ("self-host", "skipped: agentbundle not installed"),
        ("deep lint", "skipped: PyYAML not installed"),
        ("bandit", "skipped: bandit not installed"),
    ]:
        assert any(check in line and text in line for line in lines)


def test_checkout_paths_reach_child_env_and_installed_check() -> None:
    env = precheck.child_env({"PYTHONPATH": "keep"})
    parts = env["PYTHONPATH"].split(":")
    assert str(precheck.REPO_ROOT / "packages" / "agentbundle") in parts
    assert parts[-1] == "keep"
    assert precheck._installed("agentbundle")
    assert not precheck._installed("no_such_module_xyz")


def _git(repo: Path, *args: str) -> None:
    """Run hermetic git in `repo` (no global config, fixed identity)."""
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(repo),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def _repo_executor(repo: Path) -> object:
    def execute(argv: list[str], capture: str) -> tuple[int, str]:
        proc = subprocess.run(
            argv,
            cwd=repo,
            env={"PATH": os.environ["PATH"], "GIT_CONFIG_GLOBAL": os.devnull},
            stdout=subprocess.PIPE,
            check=False,
            text=True,
        )
        return proc.returncode, proc.stdout

    return execute


def _scratch_repo(tmp_path: Path, source: str) -> Path:
    repo = tmp_path / "repo"
    (repo / Path(source).parent).mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / source).write_text("line one\nline two\nline three\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def test_committed_rename_lists_source_and_fires_triggers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = "packs/core/.apm/skills/a.md"
    repo = _scratch_repo(tmp_path, source)
    _git(repo, "checkout", "-q", "-b", "work")
    (repo / "docs").mkdir()
    _git(repo, "-c", "diff.renames=true", "mv", source, "docs/a.md")
    _git(repo, "commit", "-q", "-m", "move")
    execute = _repo_executor(repo)
    paths = precheck.changed_paths("main", execute)
    assert source in paths and "docs/a.md" in paths
    ran: list[list[str]] = []

    def record(argv: list[str], capture: str) -> tuple[int, str]:
        ran.append(argv)
        return 0, ""

    _run_paths = precheck.run_checks(
        paths,
        base="main",
        python=PY,
        with_tests=False,
        executor=record,
        is_installed=lambda _t: True,
        file_exists=lambda _p: False,
        dir_exists=lambda _p: False,
    )
    assert _run_paths == 0
    flat = [" ".join(c) for c in ran]
    assert any("self-host" in c for c in flat)
    assert any("check-core-release" in c for c in flat)


def test_worktree_rename_column_source_is_not_truncated(tmp_path: Path) -> None:
    source = "packs/core/.apm/x.md"
    repo = _scratch_repo(tmp_path, source)
    (repo / "docs").mkdir()
    (repo / source).rename(repo / "docs" / "x.md")
    _git(repo, "add", "-N", "docs/x.md")  # status: ` R docs/x.md` then the source entry
    paths = precheck.changed_paths("HEAD", _repo_executor(repo))
    assert paths == ["docs/x.md", source]


def test_status_worktree_rename_column_consumes_source() -> None:
    status = " R docs/x.md\0packs/core/.apm/x.md\0"
    rec = Recorder({"status": (0, status)})
    paths = precheck.changed_paths("origin/main", rec)
    assert paths == ["docs/x.md", "packs/core/.apm/x.md"]
