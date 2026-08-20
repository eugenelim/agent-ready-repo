"""The structural-git cache in local_exclude, and the bound on its staleness.

The cache is only correct because it is dropped at a command boundary. These
tests pin both halves: that repeated identical queries inside one operation
collapse, and that a reset makes a changed repository visible again.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agentbundle import local_exclude


def _init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)


def _count_git(monkeypatch) -> list[list[str]]:
    """Record every git argv that actually reaches subprocess.run."""
    seen: list[list[str]] = []
    real = subprocess.run

    def spy(args, *a, **kw):  # noqa: ANN001, ANN002, ANN003
        if isinstance(args, (list, tuple)) and args and str(args[0]) == "git":
            seen.append([str(x) for x in args])
        return real(args, *a, **kw)

    monkeypatch.setattr(local_exclude.subprocess, "run", spy)
    return seen


def test_repeated_identical_query_runs_git_once(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init(repo)
    local_exclude.reset_git_query_cache()
    seen = _count_git(monkeypatch)

    first = local_exclude.get_exclude_path(repo)
    second = local_exclude.get_exclude_path(repo)
    third = local_exclude.get_exclude_path(repo)

    assert first == second == third
    assert len(seen) == 1, f"expected one git call, got {len(seen)}: {seen}"


def test_reset_makes_a_changed_repository_visible(tmp_path: Path, monkeypatch) -> None:
    """Without the reset the cache would answer for a repository that is gone."""
    plain = tmp_path / "plain"
    plain.mkdir()
    local_exclude.reset_git_query_cache()

    assert local_exclude.is_git_repo(plain) is False

    _init(plain)
    # Still cached: the stale answer is the whole reason the reset exists.
    assert local_exclude.is_git_repo(plain) is False

    local_exclude.reset_git_query_cache()
    assert local_exclude.is_git_repo(plain) is True


def test_distinct_questions_are_not_conflated(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init(repo)
    local_exclude.reset_git_query_cache()
    seen = _count_git(monkeypatch)

    local_exclude.get_exclude_path(repo)
    local_exclude.derive_worktree_id(repo)

    flags = {tuple(argv[3:]) for argv in seen}
    assert len(seen) == len(flags), f"a question was cached under another's key: {seen}"
