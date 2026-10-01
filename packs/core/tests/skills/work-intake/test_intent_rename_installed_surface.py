"""AC-0025: installed Core exposes intent rename and recovery to operators."""

from __future__ import annotations

import datetime
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from types import TracebackType
from typing import Any, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-rename-test.md"
TOMBSTONE_DATE = "2026-09-30"
HOSTILE_RESOLVE_PATHS = (
    "/outside/ABSOLUTE_HOSTILE.md",
    "docs/product/intents/FEAT-0002-hostile\nINJECTED.md",
)
_SANDBOX_RMDIR_SHIM = """
from __future__ import annotations

import os

_original_rmdir = os.rmdir


def _sandbox_rmdir(path: str, *args: object, **kwargs: object) -> None:
    dir_fd = kwargs.get("dir_fd")
    if (
        dir_fd is not None
        and isinstance(path, str)
        and path.startswith(".intent-rename-")
    ):
        opened = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0), dir_fd=dir_fd)
        try:
            if os.listdir(opened):
                raise OSError("stage-not-empty")
        finally:
            os.close(opened)
        return None
    return _original_rmdir(path, *args, **kwargs)


os.rmdir = _sandbox_rmdir
"""


@pytest.fixture
def workspace_tmp() -> Path:
    """Create a disposable tree under the writable repository workspace."""
    base = REPOSITORY_ROOT / ".pytest-tmp-intent-rename" / "installed-surface"
    base.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=f"{uuid.uuid4().hex}-", dir=base))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _install_core(repo: Path, tmp_path: Path) -> Path:
    """Install the real Core pack into *repo* through Codex repo scope."""
    catalogue = tmp_path / "catalogue"
    core = catalogue / "packs" / "core"
    core.parent.mkdir(parents=True)
    shutil.copytree(REPOSITORY_ROOT / "packs" / "core", core, symlinks=False)

    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    args = _build_parser().parse_args([
        "install",
        str(catalogue),
        "--pack",
        "core",
        "--output",
        str(repo),
        "--scope",
        "repo",
        "--adapter",
        "codex",
        "--yes",
    ])
    temp_parent = tmp_path
    install_tmp = Path(tempfile.mkdtemp(prefix="intent-rename-install-", dir=temp_parent))
    previous_tempdir = tempfile.tempdir
    previous_temporary_directory = tempfile.TemporaryDirectory

    class NoCleanupTemporaryDirectory:
        """TemporaryDirectory shape that avoids sandbox-denied cleanup."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.pop("ignore_cleanup_errors", None)
            kwargs.pop("delete", None)
            self.name = tempfile.mkdtemp(*args, **kwargs)

        def __enter__(self) -> str:
            return self.name

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        def cleanup(self) -> None:
            return None

    try:
        tempfile.tempdir = str(install_tmp)
        tempfile.TemporaryDirectory = cast(Any, NoCleanupTemporaryDirectory)
        assert install.run(args) == 0
    finally:
        tempfile.TemporaryDirectory = previous_temporary_directory
        tempfile.tempdir = previous_tempdir
    installed = repo / ".agents/skills/work-intake/scripts/intent_rename.py"
    assert installed.is_file()
    return installed


def _write_sandbox_shim(root: Path) -> Path:
    """Install a child-only shim for the managed sandbox rmdir limitation."""
    shim = root / "python-shim"
    shim.mkdir()
    (shim / "sitecustomize.py").write_text(_SANDBOX_RMDIR_SHIM, encoding="utf-8")
    return shim


def _commit(repo: Path) -> None:
    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(repo.parent)
    git_dir = repo.parent / "repo.gitdir"
    if (repo / ".git").is_dir():
        shutil.rmtree(repo / ".git")
    subprocess.run(
        ["git", "init", "-q", "--separate-git-dir", str(git_dir), "."],
        cwd=repo,
        env=env,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        env=env,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=repo,
        env=env,
        check=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, env=env, check=True)


def _fixture(repo: Path, tmp_path: Path) -> Path:
    installed = _install_core(repo, tmp_path)
    _write_sandbox_shim(repo.parent)
    source = repo / SOURCE
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "# Rename test\n\n"
        "- **Slug:** `rename-test`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n\n"
        f"Self: {SOURCE}\n",
        encoding="utf-8",
    )
    (repo / "citation.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    (repo / "workspace.toml").write_text(
        "[backlog]\n"
        f'open = [{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}]\n',
        encoding="utf-8",
    )
    _commit(repo)
    return installed


# Drives the operator's real CLI `main` with an in-process checkpoint that
# SIGKILLs the process; the installed entry point exposes no such seam.
_KILL_CHILD = """
import datetime
import importlib.util
import os
import signal
import sys
from pathlib import Path

script, checkpoint, today = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
spec = importlib.util.spec_from_file_location(
    "core_work_intake_intent_rename_kill_child", script
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def kill_at(name):
    if name == checkpoint:
        os.kill(os.getpid(), signal.SIGKILL)

raise SystemExit(
    module.main(
        sys.argv[4:],
        _checkpoint=kill_at,
        _today=lambda: datetime.date.fromisoformat(today),
    )
)
"""


def _run_installed(
    repo: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
    kill_at: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(repo.parent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    shim = repo.parent / "python-shim"
    python_path = os.fspath(shim)
    if env.get("PYTHONPATH"):
        python_path = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
    env["PYTHONPATH"] = python_path
    if extra_env:
        env.update(extra_env)
    installed = ".agents/skills/work-intake/scripts/intent_rename.py"
    command = (
        [sys.executable, "-c", _KILL_CHILD, installed, kill_at, TOMBSTONE_DATE, *args]
        if kill_at is not None
        else [sys.executable, installed, *args]
    )
    return subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def _non_empty_stages(repo: Path) -> list[Path]:
    return [
        stage
        for stage in (repo / "docs/product/intents").glob(".intent-rename-*")
        if any(stage.iterdir())
    ]


@pytest.mark.parametrize(
    ("arguments", "hostile_input"),
    [
        ([], None),
        (["HOSTILE_UNKNOWN_COMMAND"], "HOSTILE_UNKNOWN_COMMAND"),
        (["rename", "HOSTILE_MISSING_TARGET"], "HOSTILE_MISSING_TARGET"),
        (
            ["resolve", "docs/product/intents/example.md", "HOSTILE_EXCESS_ARGUMENT"],
            "HOSTILE_EXCESS_ARGUMENT",
        ),
        (
            [
                "recover",
                "HOSTILE_DIRECTION",
                SOURCE,
                "STRAT",
                TOMBSTONE_DATE,
            ],
            "HOSTILE_DIRECTION",
        ),
        (["--help"], "--help"),
    ],
)
def test_operator_syntax_refusal_is_fixed_and_echoes_no_input(
    arguments: list[str], hostile_input: str | None
) -> None:
    """Invalid syntax and help use one bounded, non-reflective response."""
    result = subprocess.run(
        [
            sys.executable,
            os.fspath(
                REPOSITORY_ROOT
                / "packs/core/.apm/skills/work-intake/scripts/intent_rename.py"
            ),
            *arguments,
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "refused:syntax-invalid\n"
    if hostile_input is not None:
        assert hostile_input not in result.stdout + result.stderr


def test_installed_core_rename_command_commits_end_to_end(workspace_tmp: Path) -> None:
    repo = workspace_tmp / "repo"
    repo.mkdir()
    installed = _fixture(repo, workspace_tmp)

    result = _run_installed(repo, "rename", SOURCE, "STRAT")

    assert installed.relative_to(repo).as_posix() == (
        ".agents/skills/work-intake/scripts/intent_rename.py"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("committed:committed:")
    assert (repo / SUCCESSOR).is_file()
    assert f"- **Reissued as:** {SUCCESSOR}" in (repo / SOURCE).read_text(encoding="utf-8")
    assert _non_empty_stages(repo) == []


def test_installed_core_recover_command_drives_partial_forward(workspace_tmp: Path) -> None:
    repo = workspace_tmp / "repo"
    repo.mkdir()
    _fixture(repo, workspace_tmp)

    partial = _run_installed(
        repo,
        "rename",
        SOURCE,
        "STRAT",
        kill_at="after-successor",
    )
    assert partial.returncode == -signal.SIGKILL

    recovered = _run_installed(
        repo, "recover", "forward", SOURCE, "STRAT", TOMBSTONE_DATE
    )

    assert recovered.returncode == 0, recovered.stderr
    assert recovered.stdout.startswith("committed:committed:")
    assert (repo / SUCCESSOR).is_file()
    assert _non_empty_stages(repo) == []


def test_installed_cli_ignores_environment_kill_and_date_seams(
    workspace_tmp: Path,
) -> None:
    """No environment variable can kill the installed operator or pick its date."""
    repo = workspace_tmp / "repo"
    repo.mkdir()
    _fixture(repo, workspace_tmp)
    before = datetime.datetime.now(datetime.UTC).date().isoformat()

    result = _run_installed(
        repo,
        "rename",
        SOURCE,
        "STRAT",
        extra_env={
            "INTENT_RENAME_KILL_CHECKPOINT": "after-successor",
            "INTENT_RENAME_TODAY": "2001-01-01",
        },
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("committed:committed:")
    tombstone = (repo / SOURCE).read_text(encoding="utf-8")
    after = datetime.datetime.now(datetime.UTC).date().isoformat()
    assert "2001-01-01" not in tombstone
    assert any(f"- **Tombstone:** {day}" in tombstone for day in {before, after})
    assert _non_empty_stages(repo) == []


@pytest.mark.parametrize(
    ("case", "expected_code", "exit_code"),
    [
        ("target-missing", "tombstone-target-missing", 1),
        ("target-is-tombstone", "tombstone-target-is-tombstone", 1),
        ("stops-at-tombstone", "tombstone", 0),
    ],
)
def test_installed_resolve_reports_tombstone_diagnostics(
    workspace_tmp: Path, case: str, expected_code: str, exit_code: int
) -> None:
    """AC-0007, AC-0008 and AC-0009 on the installed operator surface."""
    repo = workspace_tmp / "repo"
    repo.mkdir()
    _fixture(repo, workspace_tmp)
    old = "docs/product/intents/FEAT-0009-old.md"
    target = "docs/product/intents/STRAT-0009-new.md"
    final = "docs/product/intents/CAP-0009-final.md"

    def tombstone(reissued_as: str) -> str:
        return (
            "# Tombstone: old\n\n- **Slug:** `old`\n- **Tombstone:** 2026-09-30\n"
            f"- **Reissued as:** {reissued_as}\n"
        )

    (repo / old).write_text(tombstone(target), encoding="utf-8")
    if case == "target-is-tombstone":
        (repo / target).write_text(tombstone(final), encoding="utf-8")
    elif case == "stops-at-tombstone":
        (repo / target).write_text(
            "# New\n\n- **Slug:** `new`\n\nSUCCESSOR-BODY-MARKER\n", encoding="utf-8"
        )

    result = _run_installed(repo, "resolve", old)

    assert result.returncode == exit_code, result.stderr
    assert result.stdout == f"resolve:{expected_code}:{old}:{target}\n"
    assert result.stderr == ""
    assert "SUCCESSOR-BODY-MARKER" not in result.stdout


def test_installed_resolve_never_prints_an_unsafe_tombstone_target(
    workspace_tmp: Path,
) -> None:
    """A crafted target, which the tombstone shape admits, never reaches the output."""
    repo = workspace_tmp / "repo"
    repo.mkdir()
    _fixture(repo, workspace_tmp)
    old = "docs/product/intents/FEAT-0009-old.md"
    unsafe_target = "docs/product/intents/STRAT-0009-a:INJECTED.md"
    (repo / old).write_text(
        "# Tombstone: old\n\n- **Slug:** `old`\n- **Tombstone:** 2026-09-30\n"
        f"- **Reissued as:** {unsafe_target}\n",
        encoding="utf-8",
    )
    spaced = "docs/product/intents/FEAT 0010.md"
    (repo / spaced).write_text("# Live\n", encoding="utf-8")

    refused_target = _run_installed(repo, "resolve", old)
    refused_input = _run_installed(repo, "resolve", spaced)

    assert refused_target.stdout == f"resolve:tombstone-target-refused:{old}\n"
    assert "INJECTED" not in refused_target.stdout
    assert refused_input.stdout == "resolve:resolve-refused\n"


def test_installed_resolve_refusal_echoes_no_unconfined_input(
    workspace_tmp: Path,
) -> None:
    repo = workspace_tmp / "repo"
    repo.mkdir()
    _fixture(repo, workspace_tmp)
    newline_path = repo / HOSTILE_RESOLVE_PATHS[1]
    newline_path.write_text("# Live even though its name is unsafe\n", encoding="utf-8")

    for hostile_path in HOSTILE_RESOLVE_PATHS:
        result = _run_installed(repo, "resolve", hostile_path)

        assert result.returncode != 0
        assert result.stdout == "resolve:resolve-refused\n"
        assert result.stderr == ""
        assert hostile_path not in result.stdout + result.stderr
        assert result.stdout.splitlines() == ["resolve:resolve-refused"]
