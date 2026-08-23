"""Tests for `tools/repo/branch_added_paths.py`.

Every case builds a real git repository. The defect these guard against is entirely about
what git reports for a given base, so a mocked git would test the mock — the thing being
claimed is kernel-and-git behaviour, and a fixture cannot testify about it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.repo.branch_added_paths import (  # noqa: E402
    added_paths,
    upstream_merge_base,
)


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, f"git {' '.join(args)} failed: {done.stderr}"
    return done.stdout


def _commit(repo: Path, relative: str, body: str, message: str) -> None:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", message)


@pytest.fixture
def peer_merge_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    """A branch that added nothing, and an upstream that gained a file after the base.

    This is the exact history that broke the original control: work starts, a base is
    pinned, someone else merges, and the branch is then asked what it created.
    """
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "--quiet", "--initial-branch=main")
    _git(origin, "config", "user.email", "fixture@example.invalid")
    _git(origin, "config", "user.name", "fixture")
    _commit(origin, "README.md", "base\n", "base")
    pinned = _git(origin, "rev-parse", "HEAD").strip()

    # The peer's merge, landing on the default branch after the pinned base.
    _commit(origin, "docs/adr/0093-a-peer-decision.md", "peer\n", "peer adr")

    work = tmp_path / "work"
    _git(tmp_path, "clone", "--quiet", str(origin), str(work))
    _git(work, "config", "user.email", "fixture@example.invalid")
    _git(work, "config", "user.name", "fixture")
    _git(work, "checkout", "--quiet", "-b", "round-branch")
    _commit(work, "docs/specs/example-round/spec.md", "round\n", "round work")
    return origin, work, pinned


def test_peer_addition_is_not_attributed_to_this_branch(peer_merge_repo) -> None:
    _origin, work, pinned = peer_merge_repo
    base, how = upstream_merge_base(work, fallback=pinned)
    assert "merge-base" in how
    assert "docs/adr/0093-a-peer-decision.md" not in added_paths(work, base)


def test_pinned_base_does_attribute_it_so_the_clean_result_is_not_vacuous(
    peer_merge_repo,
) -> None:
    """The negative control.

    Without this, the assertion above is satisfied just as well by a scan that returns
    nothing at all. Reading the same tree against the pinned base must still surface the
    peer's file, which is what makes its absence under the correct base meaningful.
    """
    _origin, work, pinned = peer_merge_repo
    assert "docs/adr/0093-a-peer-decision.md" in added_paths(work, pinned)


def test_this_branch_own_addition_is_still_caught(peer_merge_repo) -> None:
    """The positive control: narrowing the scope must not disable the scan."""
    _origin, work, pinned = peer_merge_repo
    _commit(work, "docs/adr/0094-a-round-decision.md", "round\n", "round adr")
    base, _how = upstream_merge_base(work, fallback=pinned)
    assert "docs/adr/0094-a-round-decision.md" in added_paths(work, base)


def test_uncommitted_and_untracked_additions_are_seen(peer_merge_repo) -> None:
    """`base..HEAD` misses both; a decoy once sat in a tree reported clean."""
    _origin, work, pinned = peer_merge_repo
    (work / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    (work / "docs" / "adr" / "0095-staged.md").write_text("staged\n")
    _git(work, "add", "docs/adr/0095-staged.md")
    (work / "docs" / "adr" / "0096-untracked.md").write_text("untracked\n")

    base, _how = upstream_merge_base(work, fallback=pinned)
    found = added_paths(work, base)
    assert "docs/adr/0095-staged.md" in found
    assert "docs/adr/0096-untracked.md" in found


def test_fallback_is_named_rather_than_silent(tmp_path: Path) -> None:
    """A silent fallback would reinstate the defect where nobody would look."""
    solo = tmp_path / "solo"
    solo.mkdir()
    _git(solo, "init", "--quiet", "--initial-branch=main")
    _git(solo, "config", "user.email", "fixture@example.invalid")
    _git(solo, "config", "user.name", "fixture")
    _commit(solo, "README.md", "base\n", "base")
    head = _git(solo, "rev-parse", "HEAD").strip()

    base, how = upstream_merge_base(solo, fallback=head)
    assert base == head
    assert "NO UPSTREAM REF RESOLVED" in how


def test_missing_upstream_without_a_fallback_refuses(tmp_path: Path) -> None:
    solo = tmp_path / "solo"
    solo.mkdir()
    _git(solo, "init", "--quiet", "--initial-branch=main")
    _git(solo, "config", "user.email", "fixture@example.invalid")
    _git(solo, "config", "user.name", "fixture")
    _commit(solo, "README.md", "base\n", "base")

    with pytest.raises(RuntimeError, match="no upstream ref resolved"):
        upstream_merge_base(solo)


def test_a_git_failure_raises_rather_than_reporting_nothing_added(tmp_path: Path) -> None:
    """An absence scan that swallows an error passes for the worst possible reason."""
    solo = tmp_path / "solo"
    solo.mkdir()
    _git(solo, "init", "--quiet", "--initial-branch=main")
    _git(solo, "config", "user.email", "fixture@example.invalid")
    _git(solo, "config", "user.name", "fixture")
    _commit(solo, "README.md", "base\n", "base")

    with pytest.raises(RuntimeError, match="cannot list paths added"):
        added_paths(solo, "0000000000000000000000000000000000000000")
