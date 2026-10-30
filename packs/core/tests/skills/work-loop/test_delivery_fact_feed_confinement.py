"""Confinement suite for the delivery fact feed (Slice 3, task T1, AC-0013).

Every refusal below makes the log an unread source with a closed reason code
and contributes no fact and no candidate; a refused ``docs/specs/`` root or
entry refuses the whole scan and never yields a complete snapshot.

Mode: TDD through contract and integration tests.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from types import ModuleType

import delivery_feed_support as dfs
import pytest


@pytest.fixture(scope="module")
def feed() -> ModuleType:
    """The feed module, loaded by path under a unique name."""
    return dfs.load_script("dfp_confinement_feed", "_delivery_feed.py")


@pytest.fixture
def repo(tmp_path: Path) -> dfs.FeedRepo:
    """A repository whose ``alpha`` spec holds one real review-failure receipt."""
    fixture = dfs.FeedRepo(tmp_path)
    store = fixture.open_store("alpha")
    fixture.add_review_failure("alpha", store, "one")
    return fixture


def entries(feed: ModuleType, repo: dfs.FeedRepo, **kwargs: object) -> list[dict]:
    """Return the first page's entries."""
    page = feed.feed_page(repo.root, **kwargs)
    assert page["continuation"] is None
    return page["entries"]


def assert_unread(feed: ModuleType, repo: dfs.FeedRepo, reason: str, **kwargs: object) -> None:
    """The log is one unread-source entry with *reason* and nothing else."""
    found = entries(feed, repo, **kwargs)
    assert found == [{
        "entry_kind": "unread-source",
        "ordinal": 0,
        "spec_path": "docs/specs/alpha",
        "reason_code": reason,
    }]


def test_symlinked_log_is_refused(feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path) -> None:
    real = tmp_path / "elsewhere.log"
    shutil.copy(repo.log_path("alpha"), real)
    repo.log_path("alpha").unlink()
    repo.log_path("alpha").symlink_to(real)
    assert_unread(feed, repo, "log-unsafe")


def test_fifo_log_is_refused_without_blocking(feed: ModuleType, repo: dfs.FeedRepo) -> None:
    repo.log_path("alpha").unlink()
    os.mkfifo(repo.log_path("alpha"))
    assert_unread(feed, repo, "log-unsafe")


def test_hard_linked_log_is_refused(feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path) -> None:
    os.link(repo.log_path("alpha"), tmp_path / "second-name.log")
    assert_unread(feed, repo, "log-unsafe")


def test_log_directory_outside_the_root_is_refused(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    """A symlinked .shadow-acceptance pointing outside the repository is never followed."""
    outside = tmp_path / "outside"
    shutil.copytree(repo.shadow_dir("alpha"), outside)
    shutil.rmtree(repo.shadow_dir("alpha"))
    repo.shadow_dir("alpha").symlink_to(outside, target_is_directory=True)
    assert_unread(feed, repo, "log-unsafe")


def test_log_directory_that_is_a_file_is_refused(feed: ModuleType, repo: dfs.FeedRepo) -> None:
    shutil.rmtree(repo.shadow_dir("alpha"))
    repo.shadow_dir("alpha").write_text("not a directory")
    assert_unread(feed, repo, "log-unsafe")


def test_over_cap_log_is_refused(feed: ModuleType, repo: dfs.FeedRepo) -> None:
    size = repo.log_path("alpha").stat().st_size
    assert_unread(feed, repo, "log-oversized", log_max_bytes=size - 1)
    assert entries(feed, repo, log_max_bytes=size)  # exactly at the cap is read


def test_refused_log_does_not_hide_other_specs(feed: ModuleType, repo: dfs.FeedRepo) -> None:
    other = repo.open_store("beta")
    repo.add_engine_transition("beta", other)
    repo.log_path("alpha").write_bytes(b"{not a frame}\n")
    found = entries(feed, repo)
    assert [e["entry_kind"] for e in found] == ["unread-source", "fact"]
    assert found[1]["source"]["spec_path"] == "docs/specs/beta"


# ── The docs/specs listing ───────────────────────────────────────────────────


def refused(feed: ModuleType, repo: dfs.FeedRepo) -> str:
    """Run a scan that must refuse, and return its code."""
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(repo.root)
    return caught.value.code


def test_symlinked_entry_under_specs_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    (tmp_path / "away").mkdir()
    (repo.root / "docs" / "specs" / "linked").symlink_to(tmp_path / "away", target_is_directory=True)
    assert refused(feed, repo) == "specs-entry-refused"


def test_symlinked_file_under_specs_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    (tmp_path / "away.md").write_text("x")
    (repo.root / "docs" / "specs" / "README.md").symlink_to(tmp_path / "away.md")
    assert refused(feed, repo) == "specs-entry-refused"


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_unreadable_specs_directory_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    specs = repo.root / "docs" / "specs"
    specs.chmod(0o000)
    try:
        assert refused(feed, repo) == "specs-entry-refused"
    finally:
        specs.chmod(0o755)


def test_symlinked_specs_root_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    moved = tmp_path / "moved-specs"
    (repo.root / "docs" / "specs").rename(moved)
    (repo.root / "docs" / "specs").symlink_to(moved, target_is_directory=True)
    assert refused(feed, repo) == "specs-root-refused"


def test_symlinked_docs_directory_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    moved = tmp_path / "moved-docs"
    (repo.root / "docs").rename(moved)
    (repo.root / "docs").symlink_to(moved, target_is_directory=True)
    assert refused(feed, repo) == "specs-root-refused"


def test_specs_root_that_is_a_file_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    shutil.rmtree(repo.root / "docs" / "specs")
    (repo.root / "docs" / "specs").write_text("not a directory")
    assert refused(feed, repo) == "specs-root-refused"


def test_spec_directory_name_outside_the_path_grammar_refuses_the_whole_scan(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    (repo.root / "docs" / "specs" / "has space").mkdir()
    assert refused(feed, repo) == "specs-entry-name-invalid"


def test_missing_specs_root_is_a_complete_empty_snapshot(feed: ModuleType, tmp_path: Path) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    page = feed.feed_page(root)
    assert page["entries"] == [] and page["continuation"] is None
    assert page["shadow_services"] == "enabled"


@pytest.mark.parametrize("kind", ["missing", "file", "symlink"])
def test_invalid_repository_root_is_refused(feed: ModuleType, tmp_path: Path, kind: str) -> None:
    real = tmp_path / "real"
    real.mkdir()
    root = tmp_path / "root"
    if kind == "file":
        root.write_text("x")
    elif kind == "symlink":
        root.symlink_to(real, target_is_directory=True)
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(root)
    assert caught.value.code == "root-invalid"
