"""Integration test — the assimilate-primitive ingest guardrails composed
end-to-end (RFC-0059 spec, assimilate-primitive ACs + ingest security).

The skill itself is agent-driven prose; this exercises the *mechanical* pipeline
it orchestrates — validate source (SSRF) → land body through the write-jail,
body-preserving — on a real temp tree, plus the negative paths (a rejected URL
scheme never lands; a traversal/symlink cannot escape the destination pack)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import ssrf_check as S
import write_jail as W

FIXTURE_SKILL = """---
name: summarize-thread
description: Use to summarize a long email thread into a short digest.
---

# Skill: summarize-thread

Summarize a thread into decisions + action items.
"""


def test_local_source_lands_body_preserving(tmp_path: Path) -> None:
    # A fixture "external primitive" on a local path.
    src = tmp_path / "external" / "summarize-thread" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(FIXTURE_SKILL, encoding="utf-8")

    # 1. validate the source (local path — allowed, classified 'path')
    assert S.check_source(str(src.parent)) == "path"

    # 2. land the body into a destination pack, through the jail, body-preserving
    dest_root = tmp_path / "packs" / "some-pack" / ".apm" / "skills"
    landed = W.jailed_write(dest_root, "summarize-thread/SKILL.md", src.read_text())

    # 3. the landed file is under the jail and byte-identical (body-preserving)
    assert landed.resolve().is_relative_to(dest_root.resolve())
    assert landed.read_text() == FIXTURE_SKILL


def test_url_source_rejected_before_landing(tmp_path: Path) -> None:
    # A file:// "URL" source must be refused at validation — never reaches a write.
    with pytest.raises(S.SsrfRejected):
        S.check_source("file:///etc/passwd")
    with pytest.raises(S.SsrfRejected):
        S.check_source("https://169.254.169.254/latest/meta-data/")


def test_traversal_cannot_escape_destination_pack(tmp_path: Path) -> None:
    dest_root = tmp_path / "packs" / "some-pack"
    dest_root.mkdir(parents=True)
    with pytest.raises(W.PathJailError):
        W.jailed_write(dest_root, "../../escaped/SKILL.md", FIXTURE_SKILL)


def test_symlinked_source_dir_cannot_redirect_the_land(tmp_path: Path) -> None:
    dest_root = tmp_path / "packs" / "some-pack"
    dest_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = dest_root / "sneaky"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    # a destination path routed through the symlink resolves outside → refused
    with pytest.raises(W.PathJailError):
        W.confined_target(dest_root, link / "SKILL.md")
