"""Tests for the shipped (adopter-facing) pre-pr hook.

Per spec `adopter-clean-enforcement-gate`: the shipped `pre-pr.py` runs only the
work-loop caps gate (`loop-cohort.py check`) plus a wire-your-gate stub — it
references **none** of this catalogue's artifact linters, and degrades gracefully
(a missing tool is a skip, never a crash). The catalogue's 8-check gate lives in
the repo-native `tools/pre-pr-catalogue.py` (tested separately); the linter
corruption-cases that used to live here moved there.

Sandbox construction mirrors the working tree (tracked + untracked-not-ignored),
then `git init` so any git-aware probe resolves. Scope: macOS + Linux.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _load_hook():
    """Import the hyphenated `pre-pr.py` as a module (for unit-level access)."""
    spec = importlib.util.spec_from_file_location("pre_pr_hook", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

REPO_ROOT = Path(__file__).resolve().parents[4]
HOOK = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "pre-pr.py"
CATALOGUE_HOOK = REPO_ROOT / "tools" / "pre-pr-catalogue.py"


def test_catalogue_hook_runs_all_8_checks_and_delegates() -> None:
    """AC3: the repo-native catalogue hook runs the exact 8-check set the old
    pre-pr.py ran, then delegates to the shipped pre-pr.py."""
    src = CATALOGUE_HOOK.read_text(encoding="utf-8")
    for tool in (
        "tools/lint-agents-md.py",
        "tools/lint-agent-artifacts.py",
        "tools/lint-skill-spec.py",
        "tools/lint-knowledge.py",
        "tools/lint-build.py",
        "tools/lint-seeds.py",
        "tools/lint_credentialed_skills.py",
        "tools/test-lint-credentialed-skills.py",
    ):
        assert tool in src, f"catalogue hook must run {tool}"
    assert "tools/hooks/pre-pr.py" in src, (
        "catalogue hook must delegate to the shipped pre-pr.py"
    )


def _seed_sandbox(dst: Path) -> Path:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout
    files = [p.decode() for p in (tracked + untracked).split(b"\0") if p]
    for rel in files:
        src = REPO_ROOT / rel
        if not src.is_symlink() and not src.exists():
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out, follow_symlinks=False)
    subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=dst, check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "baseline"],
        cwd=dst, check=True,
    )
    return dst


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    return _seed_sandbox(tmp_path / "repo")


def _run(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(cwd / "packs/core/.apm/hooks/pre-pr.py")],
        cwd=cwd, capture_output=True, text=True,
    )


# --- AC1: the shipped hook references no catalogue check ----------------------

def test_shipped_pre_pr_references_no_catalogue_checks() -> None:
    src = HOOK.read_text(encoding="utf-8")
    # Match both `tools/lint-` and the underscore `tools/lint_credentialed_skills`,
    # plus the self-test — a plain `tools/lint-` substring check would miss the
    # underscore variant.
    assert not re.search(r"tools/lint[-_]", src), (
        "shipped pre-pr.py must not reference any tools/lint-* catalogue linter"
    )
    assert "test-lint-credentialed-skills" not in src, (
        "shipped pre-pr.py must not reference the credentialed-skill self-test"
    )


def test_shipped_pre_pr_runs_no_linter_labels(sandbox: Path) -> None:
    """Clean run: passes, and emits none of the old per-linter labels."""
    result = _run(sandbox)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    for gone in ("agents-md hygiene", "agent-artifact lint", "knowledge lint", "build lint"):
        assert gone not in result.stdout, (
            f"shipped hook still runs catalogue linter {gone!r}\nstdout: {result.stdout}"
        )
    assert "pre-pr: all checks passed" in result.stdout


# --- AC2: graceful in an adopter-shaped tree (no catalogue tooling) -----------

def test_pre_pr_adopter_tree_no_tooling_is_graceful(tmp_path: Path) -> None:
    """An adopter tree with no catalogue linters and no active specs → exit 0."""
    repo = tmp_path / "adopter"
    repo.mkdir()
    result = subprocess.run(
        [sys.executable, str(HOOK)], cwd=repo, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "pre-pr: all checks passed" in result.stdout


def test_pre_pr_fails_on_unapproved_state(sandbox: Path) -> None:
    """An active state.json with plan not approved (the template's default)
    makes the work-loop caps check fail — the one gate the shipped hook keeps."""
    spec_dir = sandbox / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True, exist_ok=True)
    template = sandbox / ".claude" / "skills" / "work-loop" / "assets" / "state.json"
    shutil.copy(template, spec_dir / "state.json")
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ loop-cohort check" in result.stderr


def test_pre_pr_passes_on_approved_state(sandbox: Path) -> None:
    """AC2 positive path: an active, healthy (approved) state → loop-cohort runs
    and the hook exits 0. Guards against a regression that crashes/mis-handles a
    healthy active spec (which the unapproved-state test wouldn't catch)."""
    spec_dir = sandbox / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True, exist_ok=True)
    template = sandbox / ".claude" / "skills" / "work-loop" / "assets" / "state.json"
    state = json.loads(template.read_text())
    state["plan_review_status"] = "approved"
    state["iteration_count"] = 0
    (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    result = _run(sandbox)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "pre-pr: ✓ loop-cohort check" in result.stdout
    assert "pre-pr: all checks passed" in result.stdout


def test_run_skips_missing_tool_and_fails_present_tool() -> None:
    """The shipped `_run` (used by the adopter wire-your-gate stub) skips a
    missing tool gracefully (notice to stderr, no exit) but still fails on a
    present-but-erroring command — the spec's "degrades gracefully" contract."""
    mod = _load_hook()

    # (a) Missing tool → skip, no SystemExit.
    import contextlib
    import io
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        mod._run("phantom", ["definitely-not-a-real-binary-xyzzy"])  # no raise
    assert "skipped (not found:" in err.getvalue()

    # (b) Present command that exits non-zero → SystemExit(1).
    with pytest.raises(SystemExit) as exc:
        mod._run("boom", [sys.executable, "-c", "import sys; sys.exit(1)"])
    assert exc.value.code == 1


# --- Adapter-agnostic loop-cohort discovery -----------------------------------

def test_find_loop_cohort_discovers_non_claude_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The work-loop skill installed under a non-Claude adapter root (here
    Codex's `.agents/skills/`) is still found — the hook must not assume Claude
    Code's `.claude/` layout. Guards the adopter-agnostic contract."""
    mod = _load_hook()
    skill = tmp_path / ".agents" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"
    skill.parent.mkdir(parents=True)
    skill.write_text("# stub", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    found = mod._find_loop_cohort()
    assert found == Path(".agents/skills/work-loop/scripts/loop-cohort.py")


def test_find_loop_cohort_returns_none_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No work-loop skill under any adapter root → None (caps check is then
    skipped, not failed)."""
    mod = _load_hook()
    monkeypatch.chdir(tmp_path)
    assert mod._find_loop_cohort() is None


# --- Cross-platform wiring guarantee -----------------------------------------

def test_pre_pr_readme_wiring_uses_python_not_bash() -> None:
    text = (REPO_ROOT / "tools" / "hooks" / "README.md").read_text()
    for name in ("session-start", "pre-pr"):
        assert f"python tools/hooks/{name}.py" in text, (
            f"README missing python invocation for {name}"
        )
        assert f"bash tools/hooks/{name}.sh" not in text, (
            f"README still mentions stale bash invocation for {name}"
        )
