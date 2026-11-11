"""Tests for the shipped (adopter-facing) pre-pr hook.

The shipped `pre-pr.py` runs only gates over files that ship with the pack —
the knowledge lint over `docs/knowledge/patterns.jsonl` and the supervisor
readiness gate (`work-supervisor.py status --check`) — plus a wire-your-gate stub. It references
**none** of this catalogue's artifact linters, and degrades gracefully (a
missing tool is a skip, never a crash). The catalogue's own gate lives in the
repo-native `tools/catalogue/pre_pr_catalogue.py` (tested separately).

These repository-owned assertions span core-pack content and catalogue tooling,
so they live in the root roster rather than either component's local suite.

Sandbox construction mirrors the working tree (tracked + untracked-not-ignored),
then `git init` so any git-aware probe resolves. Runs on Linux, macOS, and
Windows (Gate A-tests runs it on all three).
"""

from __future__ import annotations

import importlib.util
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


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "packs" / "core" / ".apm" / "hooks" / "pre-pr.py"
CATALOGUE_HOOK = REPO_ROOT / "tools" / "catalogue" / "pre_pr_catalogue.py"


def test_repository_hook_copy_matches_the_shipped_hook() -> None:
    """`tools/hooks/pre-pr.py` is a hand-kept copy; the pack's tests run only the shipped one."""
    tools_copy = REPO_ROOT / "tools" / "hooks" / "pre-pr.py"
    assert tools_copy.read_bytes() == HOOK.read_bytes()


def test_catalogue_hook_runs_core_checks_and_delegates() -> None:
    """The repo-native catalogue hook runs the core check set, then delegates
    to the shipped pre-pr.py. Agent-artifact, seeds, credentialed-skill, and
    profiles checks are now covered by agentbundle catalogue verify/lint."""
    src = CATALOGUE_HOOK.read_text(encoding="utf-8")
    for tool in (
        "tools/lint-agents-md.py",
        # skill-spec lint now invokes agentbundle catalogue lint --deep (not a tools/ script)
        "tools/lint-build.py",
    ):
        assert tool in src, f"catalogue hook must run {tool}"
    for removed_tool in (
        # knowledge lint moved into the shipped pre-pr.py when the linter moved
        # into the core pack — see test_shipped_hook_runs_knowledge_lint.
        "tools/lint-knowledge.py",
        "tools/lint-agent-artifacts.py",
        "tools/lint-catalogue-seeds.py",
        "tools/lint_credentialed_skills.py",
        "tools/test-lint-credentialed-skills.py",
        "tools/lint-profiles.py",
    ):
        assert removed_tool not in src, (
            f"catalogue hook must not reference deleted script {removed_tool}"
        )
    # skill-spec lint step now delegates to agentbundle package instead of tools/ script
    assert '"--deep"' in src, "catalogue hook must run agentbundle catalogue lint --deep"
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
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


# --- The shipped hook references no catalogue check ---------------------------

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
    """Clean run: passes, and emits none of the catalogue-linter labels.

    `knowledge lint` is deliberately absent from this list: `lint-knowledge.py`
    ships inside the core pack and gates `docs/knowledge/patterns.jsonl`, a file
    the pack seeds — so it is an adopter gate, not a catalogue linter. The next
    test pins that it does run.
    """
    result = _run(sandbox)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    for gone in ("agents-md hygiene", "agent-artifact lint", "build lint"):
        assert gone not in result.stdout, (
            f"shipped hook still runs catalogue linter {gone!r}\nstdout: {result.stdout}"
        )
    assert "pre-pr: all checks passed" in result.stdout


def test_shipped_pre_pr_gates_the_knowledge_base(sandbox: Path) -> None:
    """The knowledge lint runs on a clean tree and *fails* the hook on an entry
    missing a required key — the PR#870 regression, end-to-end through the
    shipped hook rather than through the linter alone."""
    entries = sandbox / "docs" / "knowledge" / "patterns.jsonl"
    entries.parent.mkdir(parents=True, exist_ok=True)
    # Seed a known-good entry: whether the *repo's* live file is clean is
    # test_work_loop_lint_knowledge.py's signal to own, not this one's.
    entries.write_text(
        '{"id": "K-0001", "kind": "gotcha", "scope": "*", '
        '"title": "T", "body": "B", "source": "PR#1"}\n',
        encoding="utf-8",
    )
    assert "pre-pr: ✓ knowledge lint" in _run(sandbox).stdout

    entries.write_text(
        '{"id": "K-0001", "kind": "gotcha", "scope": "*", '
        '"title": "T", "body": "B"}\n',  # no `source`
        encoding="utf-8",
    )
    result = _run(sandbox)
    assert result.returncode == 1
    assert "missing required keys: ['source']" in result.stdout + result.stderr
    assert "pre-pr: ✖ knowledge lint failed" in result.stderr


# --- Graceful in an adopter-shaped tree (no catalogue tooling) ----------------

def test_pre_pr_adopter_tree_no_tooling_is_graceful(tmp_path: Path) -> None:
    """An adopter tree with no catalogue linters and no active specs → exit 0."""
    repo = tmp_path / "adopter"
    repo.mkdir()
    result = subprocess.run(
        [sys.executable, str(HOOK)], cwd=repo, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "pre-pr: all checks passed" in result.stdout


def test_pre_pr_fails_on_an_approved_run_that_cannot_be_checked(sandbox: Path) -> None:
    """A spec holding `delivery/approvals.jsonl` with no run behind it fails the
    supervisor check: the hook discovers runs from the committed record."""
    delivery = sandbox / "docs" / "specs" / "example" / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    (delivery / "approvals.jsonl").write_text("{}\n", encoding="utf-8")
    result = _run(sandbox)
    assert result.returncode != 0
    assert "pre-pr: ✖ supervisor status docs/specs/example --check failed" in result.stderr


def test_pre_pr_passes_when_no_spec_holds_approvals(sandbox: Path) -> None:
    """Positive path: a spec directory with no `delivery/approvals.jsonl` adds no
    supervisor failure, and the hook exits 0.

    The sandbox mirrors the working tree, so any spec there that already holds
    committed `delivery/` records is removed first: this case is about a tree in
    which no spec holds approvals.
    """
    for delivery in (sandbox / "docs" / "specs").glob("*/delivery"):
        shutil.rmtree(delivery)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "no delivery"],
        cwd=sandbox, check=False,
    )
    spec_dir = sandbox / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    result = _run(sandbox)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "skipping supervisor check" in result.stdout
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


# --- Adapter-agnostic script discovery -----------------------------------

def test_find_work_loop_script_discovers_non_claude_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The work-loop skill installed under a non-Claude adapter root (here
    Codex's `.agents/skills/`) is still found — the hook must not assume Claude
    Code's `.claude/` layout. Guards the adopter-agnostic contract."""
    mod = _load_hook()
    skill = tmp_path / ".agents" / "skills" / "work-loop" / "scripts" / "work-supervisor.py"
    skill.parent.mkdir(parents=True)
    skill.write_text("# stub", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    found = mod._find_work_loop_script("work-supervisor.py")
    assert found == Path(".agents/skills/work-loop/scripts/work-supervisor.py")


def test_find_work_loop_script_returns_none_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No work-loop skill under any adapter root → None (the supervisor check
    then fails only when a run was approved)."""
    mod = _load_hook()
    monkeypatch.chdir(tmp_path)
    assert mod._find_work_loop_script("work-supervisor.py") is None
    assert mod._find_work_loop_script("lint-knowledge.py") is None


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
