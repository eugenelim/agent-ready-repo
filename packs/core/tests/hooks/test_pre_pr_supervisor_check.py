"""The pre-PR hooks run the supervisor's readiness check for each approved run.

Both copies of the hook (the shipped pack source and the repository's own) are
run against a throwaway tree with a fake ``work-supervisor.py`` whose exit code
each spec directory chooses through an ``exit-code`` file.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
HOOKS = {
    "pack": PACK_ROOT / ".apm" / "hooks" / "pre-pr.py",
    "tools": PACK_ROOT.parents[1] / "tools" / "hooks" / "pre-pr.py",
}
REAL_SUPERVISOR = (
    PACK_ROOT / ".apm" / "skills" / "work-loop" / "scripts" / "work-supervisor.py"
)
# Enforces the real supervisor's argument contract: <spec-dir> is a
# repository-relative POSIX path (no leading "/", no backslash, no ":"), and the
# call runs from the repository root, so the path must exist from the cwd.
FAKE_SUPERVISOR = (
    "import sys\n"
    "from pathlib import Path\n"
    "assert sys.argv[1] == 'status' and sys.argv[3] == '--check', sys.argv\n"
    "raw = sys.argv[2]\n"
    "if not raw or '\\\\' in raw or raw.startswith('/') or ':' in raw:\n"
    "    print('<spec-dir> must be a repository-relative POSIX path')\n"
    "    raise SystemExit(2)\n"
    "if not Path(raw, 'delivery', 'approvals.jsonl').is_file():\n"
    "    print('spec dir not found from cwd')\n"
    "    raise SystemExit(2)\n"
    "code = Path(raw, 'exit-code')\n"
    "raise SystemExit(int(code.read_text()) if code.is_file() else 0)\n"
)


@pytest.fixture(params=sorted(HOOKS))
def hook(request: pytest.FixtureRequest) -> Path:
    path = HOOKS[request.param]
    if not path.is_file():
        pytest.skip(f"{path} not present")
    return path


def _install_supervisor(root: Path) -> None:
    scripts = root / ".claude" / "skills" / "work-loop" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "work-supervisor.py").write_text(FAKE_SUPERVISOR, encoding="utf-8")


def _approved_spec(root: Path, name: str, exit_code: int = 0) -> Path:
    spec = root / "docs" / "specs" / name
    (spec / "delivery").mkdir(parents=True)
    (spec / "delivery" / "approvals.jsonl").write_text("{}\n", encoding="utf-8")
    (spec / "exit-code").write_text(str(exit_code), encoding="utf-8")
    return spec


def _run(hook: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(hook)],
        cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
    )


@pytest.mark.parametrize("code", [3, 1])
def test_nonzero_status_check_fails(hook: Path, tmp_path: Path, code: int) -> None:
    # VI-7003: exit 3 and exit 1 both fail.
    _install_supervisor(tmp_path)
    _approved_spec(tmp_path, "demo", code)
    result = _run(hook, tmp_path)
    assert result.returncode == 1
    assert "supervisor status" in result.stderr and f"exit {code}" in result.stderr


def test_all_zero_passes_and_terminal_at_cap_passes(hook: Path, tmp_path: Path) -> None:
    # VI-7003: a terminal run at the retry cap exits 0 from status --check.
    _install_supervisor(tmp_path)
    _approved_spec(tmp_path, "alpha")
    _approved_spec(tmp_path, "at-cap")
    result = _run(hook, tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("✓ supervisor status") == 2


def test_no_approvals_passes_without_a_supervisor(hook: Path, tmp_path: Path) -> None:
    # VI-7003
    (tmp_path / "docs" / "specs" / "demo").mkdir(parents=True)
    result = _run(hook, tmp_path)
    assert result.returncode == 0, result.stderr


def test_deleted_run_json_still_runs_the_check(hook: Path, tmp_path: Path) -> None:
    # VI-7003: discovery comes from approvals.jsonl, never from run.json.
    _install_supervisor(tmp_path)
    spec = _approved_spec(tmp_path, "demo", 3)
    assert not (spec / ".supervisor" / "run.json").exists()
    assert _run(hook, tmp_path).returncode == 1


def test_missing_supervisor_with_an_approved_run_fails(hook: Path, tmp_path: Path) -> None:
    # VI-7003
    _approved_spec(tmp_path, "demo")
    result = _run(hook, tmp_path)
    assert result.returncode == 1
    assert "work-supervisor.py not found" in result.stderr


def test_symlinked_spec_dir_is_not_discovered(hook: Path, tmp_path: Path) -> None:
    # VI-7003: the linked spec would fail (exit 3), so passing proves it was skipped.
    _install_supervisor(tmp_path)
    outside = _approved_spec(tmp_path / "elsewhere", "real", 3)
    specs = tmp_path / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    try:
        (specs / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    result = _run(hook, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "supervisor status" not in result.stdout.replace("skipping supervisor", "")


def test_real_supervisor_accepts_the_path_shape_the_hook_passes(tmp_path: Path) -> None:
    # VI-7003: the fake's contract is the real script's: absolute is a usage
    # error (exit 2); the repository-relative path the hook passes is not.
    if not REAL_SUPERVISOR.is_file():
        pytest.skip("real work-supervisor.py not present")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    spec = _approved_spec(tmp_path, "demo")

    def call(arg: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REAL_SUPERVISOR), "status", arg, "--check"],
            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=False,
        )

    absolute = call(str(spec))
    assert absolute.returncode == 2 and "repository-relative" in absolute.stdout
    relative = call("docs/specs/demo")
    assert "repository-relative" not in relative.stdout
