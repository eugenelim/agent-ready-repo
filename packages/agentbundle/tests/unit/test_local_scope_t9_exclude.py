"""T9: exclude-file write path and worktree-id derivation.

Tests for:
  - derive_worktree_id: primary vs linked worktree
  - write_exclude_block: append, replace, union, coexistence
  - strip_exclude_block: removes block, leaves siblings
  - rollback_exclude_block: atomic restore
  - Atomic write via os.replace (not in-place append)
  - Gitignore metacharacter escaping in block paths
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from agentbundle.local_exclude import (
    derive_worktree_id,
    escape_gitignore_path,
    rollback_exclude_block,
    strip_exclude_block,
    write_exclude_block,
)


SENTINEL_PRIMARY = "primary"


# ---------------------------------------------------------------------------
# derive_worktree_id
# ---------------------------------------------------------------------------


def test_derive_worktree_id_primary(tmp_path):
    """Primary worktree: --git-dir == --git-common-dir → sentinel 'primary'."""
    # Simulate git returning the same path for both flags
    common = str(tmp_path / ".git")

    def fake_git(cmd, *args, **kwargs):
        import subprocess
        class R:
            stdout = common + "\n"
            returncode = 0
        return R()

    with patch("agentbundle.local_exclude._git_rev_parse", side_effect=[
        common,  # --git-dir
        common,  # --git-common-dir
    ]):
        wid = derive_worktree_id(tmp_path)
    assert wid == SENTINEL_PRIMARY


def test_derive_worktree_id_linked(tmp_path):
    """Linked worktree: --git-dir != --git-common-dir → last path component."""
    git_dir = str(tmp_path / ".git" / "worktrees" / "feature-branch")
    common = str(tmp_path / ".git")

    with patch("agentbundle.local_exclude._git_rev_parse", side_effect=[
        git_dir,   # --git-dir
        common,    # --git-common-dir
    ]):
        wid = derive_worktree_id(tmp_path)
    assert wid == "feature-branch"


def test_derive_worktree_id_sanitizes_colon(tmp_path):
    """Worktree-id containing ':' is sanitized (replaced with '_')."""
    git_dir = str(tmp_path / ".git" / "worktrees" / "feat:colon")
    common = str(tmp_path / ".git")

    with patch("agentbundle.local_exclude._git_rev_parse", side_effect=[
        git_dir,
        common,
    ]):
        wid = derive_worktree_id(tmp_path)
    assert ":" not in wid
    assert wid == "feat_colon"


# ---------------------------------------------------------------------------
# escape_gitignore_path
# ---------------------------------------------------------------------------


def test_escape_metacharacters():
    """[, ], *, ?, \\ are backslash-escaped; # and ! are not (leading / anchors)."""
    assert escape_gitignore_path("/refs/[draft].md") == "/refs/\\[draft\\].md"
    assert escape_gitignore_path("/glob*.txt") == "/glob\\*.txt"
    assert escape_gitignore_path("/what?.md") == "/what\\?.md"
    assert escape_gitignore_path("/back\\slash.txt") == "/back\\\\slash.txt"
    # # and ! are NOT escaped (leading / means they can't appear at line start)
    assert escape_gitignore_path("/.claude/!important") == "/.claude/!important"
    assert escape_gitignore_path("/.claude/#comment") == "/.claude/#comment"


# ---------------------------------------------------------------------------
# write_exclude_block
# ---------------------------------------------------------------------------


def test_write_exclude_block_appends_new(tmp_path):
    """write_exclude_block appends a new block when none exists."""
    exclude = tmp_path / "exclude"
    exclude.write_text("# existing line\n", encoding="utf-8")

    write_exclude_block(exclude, "mypkg", "primary", ["/.claude/skills/mypkg/SKILL.md"])

    content = exclude.read_text(encoding="utf-8")
    assert "agentbundle:local:mypkg:primary:begin" in content
    assert "/.claude/skills/mypkg/SKILL.md" in content
    assert "agentbundle:local:mypkg:primary:end" in content
    assert "# existing line" in content  # sibling content preserved


def test_write_exclude_block_replaces_existing(tmp_path):
    """write_exclude_block replaces the existing block for the same (pack, worktree_id)."""
    exclude = tmp_path / "exclude"
    write_exclude_block(exclude, "mypkg", "primary", ["/.claude/skills/mypkg/SKILL.md"])
    write_exclude_block(exclude, "mypkg", "primary", ["/.claude/skills/mypkg/SKILL.md", "/.claude/agents/mypkg/AGENT.md"])

    content = exclude.read_text(encoding="utf-8")
    # Only one block (not two)
    assert content.count("agentbundle:local:mypkg:primary:begin") == 1
    assert "/.claude/agents/mypkg/AGENT.md" in content


def test_write_exclude_block_union_replaces(tmp_path):
    """Union write: passing all patterns replaces the old block with the union."""
    exclude = tmp_path / "exclude"
    write_exclude_block(exclude, "mypkg", "primary", ["/.claude/skills/mypkg/SKILL.md"])
    # Call with union of both adapters' patterns
    write_exclude_block(
        exclude, "mypkg", "primary",
        ["/.claude/skills/mypkg/SKILL.md", "/.kiro/specs/mypkg.md"],
    )
    content = exclude.read_text(encoding="utf-8")
    assert "/.kiro/specs/mypkg.md" in content
    assert content.count("agentbundle:local:mypkg:primary:begin") == 1


def test_write_exclude_block_two_worktrees_coexist(tmp_path):
    """Two different worktree-ids produce independent blocks."""
    exclude = tmp_path / "exclude"
    write_exclude_block(exclude, "mypkg", "primary", ["/.claude/skills/mypkg/SKILL.md"])
    write_exclude_block(exclude, "mypkg", "feature-x", ["/.claude/skills/mypkg/SKILL.md"])

    content = exclude.read_text(encoding="utf-8")
    assert "agentbundle:local:mypkg:primary:begin" in content
    assert "agentbundle:local:mypkg:feature-x:begin" in content


def test_write_exclude_block_escapes_metacharacters(tmp_path):
    """Paths with gitignore metacharacters are escaped in the block."""
    exclude = tmp_path / "exclude"
    write_exclude_block(exclude, "mypkg", "primary", ["/refs/[draft].md"])

    content = exclude.read_text(encoding="utf-8")
    assert "/refs/\\[draft\\].md" in content
    # Unescaped path must NOT appear (would be misinterpreted as glob)
    assert "/refs/[draft].md" not in content.replace("/refs/\\[draft\\].md", "")


def test_write_exclude_block_atomic(tmp_path):
    """write_exclude_block uses atomic temp+replace, not in-place append."""
    exclude = tmp_path / "exclude"
    exclude.write_text("# start\n", encoding="utf-8")

    # Track if os.replace was called
    replaced = []
    original_replace = os.replace
    def spy_replace(src, dst):
        replaced.append((src, dst))
        return original_replace(src, dst)

    with patch("os.replace", side_effect=spy_replace):
        write_exclude_block(exclude, "mypkg", "primary", ["/file.md"])

    assert len(replaced) == 1, "Expected exactly one os.replace call"


# ---------------------------------------------------------------------------
# strip_exclude_block
# ---------------------------------------------------------------------------


def test_strip_exclude_block_removes_block_leaves_siblings(tmp_path):
    """strip_exclude_block removes the target block; siblings are untouched."""
    exclude = tmp_path / "exclude"
    write_exclude_block(exclude, "pkg-a", "primary", ["/a.md"])
    write_exclude_block(exclude, "pkg-b", "primary", ["/b.md"])

    strip_exclude_block(exclude, "pkg-a", "primary")

    content = exclude.read_text(encoding="utf-8")
    assert "agentbundle:local:pkg-a:primary:begin" not in content
    assert "agentbundle:local:pkg-b:primary:begin" in content
    assert "/b.md" in content


# ---------------------------------------------------------------------------
# rollback_exclude_block
# ---------------------------------------------------------------------------


def test_rollback_exclude_block_restores_prior_content(tmp_path):
    """rollback_exclude_block atomically restores prior file content."""
    exclude = tmp_path / "exclude"
    prior = b"# original content\n"
    exclude.write_bytes(prior)

    # Write a block, then roll back
    write_exclude_block(exclude, "mypkg", "primary", ["/file.md"])
    assert exclude.read_bytes() != prior  # sanity: block was written

    rollback_exclude_block(exclude, prior)
    assert exclude.read_bytes() == prior
