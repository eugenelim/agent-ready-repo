"""The delivery fact feed shows committed frames only.

A frame appended to ``delivery/evidence.jsonl`` and not committed never appears
in a page: the spec is reported unread.  Fixtures are built with the shipped
writers in a repository with a real Git history.

Mode: TDD through contract tests.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import delivery_feed_support as dfs
import pytest


@pytest.fixture(scope="module")
def feed() -> ModuleType:
    """The feed module, loaded by path under a unique name."""
    return dfs.load_script("dfp_head_feed", "_delivery_feed.py")


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=root, check=True, capture_output=True, env=env,
    )


@pytest.fixture
def repo(tmp_path: Path) -> dfs.FeedRepo:
    """A repository whose first receipt is committed."""
    fixture = dfs.FeedRepo(tmp_path)
    _git(fixture.root, "init", "-q")
    return fixture


def _entries(feed: ModuleType, root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    token: str | None = None
    while True:
        page = feed.feed_page(root, continuation=token)
        out.extend(page["entries"])
        token = page["continuation"]
        if token is None:
            return out


def _commit(root: Path) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "evidence")


def _receipts(entries: list[dict[str, Any]]) -> set[str]:
    return {
        e["observation"]["source"]["receipt_id"]
        for e in entries
        if e["entry_kind"] == "fact" and e["observation"]
    }


def test_an_uncommitted_frame_never_appears_in_a_page(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    store = repo.open_store("alpha")
    committed = repo.add_review_failure("alpha", store, "one")
    _commit(repo.root)
    assert _receipts(_entries(feed, repo.root)) == set(committed)

    planted = repo.add_review_failure("alpha", store, "two")

    entries = _entries(feed, repo.root)
    assert _receipts(entries) == set()  # the spec is unread, not partly shown
    assert not set(planted) & _receipts(entries)
    unread = [e for e in entries if e["entry_kind"] == "unread-source"]
    assert [u["spec_path"] for u in unread] == ["docs/specs/alpha"]


def test_a_log_that_was_never_committed_is_unread(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    _git(repo.root, "commit", "-q", "--allow-empty", "-m", "empty")

    entries = _entries(feed, repo.root)

    assert _receipts(entries) == set()
    assert [e["spec_path"] for e in entries if e["entry_kind"] == "unread-source"] == [
        "docs/specs/alpha"
    ]


def _plant_uncommitted(feed: ModuleType, repo: dfs.FeedRepo) -> list[str]:
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    _commit(repo.root)
    planted = repo.add_review_failure("alpha", store, "two")
    assert _receipts(_entries(feed, repo.root)) == set()
    return planted


def _assert_unread(feed: ModuleType, repo: dfs.FeedRepo, planted: list[str]) -> None:
    entries = _entries(feed, repo.root)
    assert not set(planted) & _receipts(entries)
    assert _receipts(entries) == set()
    assert [e["spec_path"] for e in entries if e["entry_kind"] == "unread-source"] == [
        "docs/specs/alpha"
    ]


def test_a_corrupted_head_reads_unread_not_as_outside_git(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    planted = _plant_uncommitted(feed, repo)
    (repo.root / ".git" / "HEAD").write_text("junk\n", encoding="utf-8")
    _assert_unread(feed, repo, planted)


def test_a_junk_gitfile_reads_unread_not_as_outside_git(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    planted = _plant_uncommitted(feed, repo)
    linked = tmp_path / "linked"
    _git(repo.root, "worktree", "add", "-q", "--detach", str(linked))
    spec = linked / "docs" / "specs" / "alpha" / "delivery"
    (spec / "evidence.jsonl").write_bytes(repo.log_path("alpha").read_bytes())
    (linked / ".git").write_text("not a gitfile\n", encoding="utf-8")
    entries = _entries(feed, linked)
    assert not set(planted) & _receipts(entries)
    assert _receipts(entries) == set()
    assert [e["spec_path"] for e in entries if e["entry_kind"] == "unread-source"] == [
        "docs/specs/alpha"
    ]
