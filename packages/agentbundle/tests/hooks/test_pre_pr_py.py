"""Parity-net smoke tests for the Python pre-pr hook.

Mirrors the corruption cases ``tools/test-pre-pr.sh`` exercises
against the bash version, plus a clean-repo pass and a README-wiring
grep that asserts the platform-agnostic invocation guarantee.

Sandbox construction uses ``git ls-files -z`` + NUL-split for safety
against filenames with whitespace, ``shutil.copy2(follow_symlinks=False)``
to preserve the ``CLAUDE.md → AGENTS.md`` symlink (so the lint-agents-md
check #2 stays satisfied), then ``git init`` + add + commit inside the
sandbox so the drift-watch's ``git check-ignore`` probes resolve.

Scope per windows-hooks-phase3: macOS + Linux only. Windows pre-pr
is blocked by lint-agents-md check #2 (CLAUDE.md symlink) until the
Phase-4 conventions-check relaxation lands.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
HOOK = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "pre-pr.py"


def _seed_sandbox(dst: Path) -> Path:
    """Materialise a self-contained sandbox at *dst* mirroring the working
    tree's tracked files. Mirrors the bash runner's seed_sandbox shape."""
    # Include both tracked and untracked-but-not-ignored files so a
    # mid-development sandbox (new .py files not yet committed) is
    # complete. Mirrors the bash runner's
    #   { git ls-files -z; git ls-files -z --others --exclude-standard; }
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, check=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout
    files = [p.decode() for p in (tracked + untracked).split(b"\0") if p]
    for rel in files:
        src = REPO_ROOT / rel
        # is_symlink+exists handles broken symlinks gracefully
        if not src.is_symlink() and not src.exists():
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        # follow_symlinks=False preserves CLAUDE.md → AGENTS.md
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


def test_pre_pr_readme_wiring_uses_python_not_bash() -> None:
    """Cross-platform invocation guarantee: README example wiring
    points at .py for both hook names, in both directions."""
    text = (REPO_ROOT / "tools" / "hooks" / "README.md").read_text()
    for name in ("session-start", "pre-pr"):
        assert f"python tools/hooks/{name}.py" in text, (
            f"README missing python invocation for {name}"
        )
        assert f"bash tools/hooks/{name}.sh" not in text, (
            f"README still mentions stale bash invocation for {name}"
        )


def test_pre_pr_clean_repo_passes(sandbox: Path) -> None:
    result = _run(sandbox)
    assert result.returncode == 0, (
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    for label in (
        "agents-md hygiene",
        "agent-artifact lint",
        "knowledge lint",
        "build lint",
    ):
        assert f"pre-pr: ✓ {label}" in result.stdout, (
            f"missing pre-pr: ✓ {label}\nstdout: {result.stdout}"
        )
    assert "pre-pr: all checks passed" in result.stdout


def test_pre_pr_agents_md_fail(sandbox: Path) -> None:
    (sandbox / "AGENTS.md").unlink()
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ agents-md hygiene failed" in result.stderr


def test_pre_pr_agent_artifact_fail(sandbox: Path) -> None:
    agent = sandbox / ".claude" / "agents" / "adversarial-reviewer.md"
    text = agent.read_text()
    agent.write_text(
        "\n".join(l for l in text.splitlines() if not l.startswith("model:"))
        + "\n"
    )
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ agent-artifact lint failed" in result.stderr


def test_pre_pr_knowledge_fail(sandbox: Path) -> None:
    (sandbox / "docs" / "knowledge" / "patterns.jsonl").write_text(
        "{not json\n"
    )
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ knowledge lint failed" in result.stderr


def test_pre_pr_check_done_fail(sandbox: Path) -> None:
    spec_dir = sandbox / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True, exist_ok=True)
    template = (
        sandbox / ".claude" / "skills" / "work-loop" / "assets" / "state.json"
    )
    shutil.copy(template, spec_dir / "state.json")
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ loop-cohort check" in result.stderr
