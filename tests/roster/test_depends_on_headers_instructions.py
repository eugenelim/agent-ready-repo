#!/usr/bin/env python3
"""Instruction roster for the depends-on-headers spec (AC-0016, AC-0018).

AC-0016: no Markdown file under ``packs/*/.apm/``, ``packs/*/seeds/``, or
``guides/`` holds a fenced ``toml`` block with a non-empty ``needs`` array,
except the repair reference that describes the repair's input.

AC-0018: each file on a closed list names the ``Depends on:`` header, and
``close-work`` also names ``Dependency receipts:`` as the receipt's home.
Standard library only; the check reads tracked files and writes nothing.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]

# fnmatch lets `*` cross `/`, so each glob reaches every depth.
_GLOBS = ("packs/*/.apm/*.md", "packs/*/seeds/*.md", "guides/*.md")
_EXEMPT = "packs/core/.apm/skills/workspace-status/references/mutate.md"

_FENCE = re.compile(r"^(?P<fence>`{3,}|~{3,})\s*(?P<info>[^\n]*)$")
# A `needs` array with anything but whitespace and comments before its `]`.
_INLINE_NEEDS = re.compile(r"\bneeds\s*=\s*\[(?!\s*(?:#[^\n]*\n\s*)*\])")

_CLOSE_WORK = "packs/core/.apm/skills/close-work/SKILL.md"
DEPENDS_ON_FILES = (
    _CLOSE_WORK,
    "packs/core/.apm/skills/workspace-status/SKILL.md",
    "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md",
    "packs/core/.apm/skills/new-spec/assets/spec.md",
    "guides/core/reference/workspace-toml-schema.md",
    "guides/architect/how-to/establish-reference-architecture.md",
    "packs/architect/DESIGN.md",
    "docs/product/workspace-toml-deps.md",
)


def _tracked_markdown() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=_REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [p for p in out.split("\0") if p]
    return sorted(
        p
        for p in paths
        if any(fnmatch.fnmatchcase(p, g) for g in _GLOBS)
    )


def toml_blocks(text: str) -> list[str]:
    """Bodies of fenced blocks whose info string starts with ``toml``."""
    blocks: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = _FENCE.match(lines[i].strip())
        if not opening:
            i += 1
            continue
        fence = opening["fence"]
        words = opening["info"].split()
        is_toml = bool(words) and words[0].lower() == "toml"
        body: list[str] = []
        i += 1
        while i < len(lines):
            closing = lines[i].strip()
            if closing.startswith(fence[0] * len(fence)) and not closing.strip(fence[0]):
                break
            body.append(lines[i])
            i += 1
        i += 1
        if is_toml:
            blocks.append("\n".join(body))
    return blocks


def has_non_empty_needs(block: str) -> bool:
    """True when a TOML block holds a ``needs`` array with any content."""
    return bool(_INLINE_NEEDS.search(block))


def needs_offenders(root: Path = _REPO, paths: list[str] | None = None) -> list[str]:
    """Paths whose fenced ``toml`` blocks carry a non-empty ``needs`` array."""
    found: list[str] = []
    for rel in _tracked_markdown() if paths is None else paths:
        if rel == _EXEMPT:
            continue
        text = (root / rel).read_text(encoding="utf-8")
        if any(has_non_empty_needs(b) for b in toml_blocks(text)):
            found.append(rel)
    return found


def test_no_instruction_teaches_a_registry_needs_edge() -> None:
    """AC-0016."""
    assert needs_offenders() == []


def test_the_exempt_file_is_a_tracked_instruction_file() -> None:
    """The exemption names a real file, so it cannot go stale silently."""
    assert _EXEMPT in _tracked_markdown()


@pytest.mark.parametrize(
    ("block", "expected"),
    [
        ('needs = [{ type = "local", kind = "spec", path = "x" }]', True),
        ('summary = "s", needs = [ { path = "x" } ]', True),
        ('needs = [\n  { path = "x" },\n]', True),
        ('needs = ["spec:x"]', True),
        ("needs = []", False),
        ("needs = [ ]", False),
        ("needs = [\n]", False),
        ("needs = [\n  # comment\n]", False),
        ('summary = "needs = nothing"', False),
    ],
)
def test_pattern_separates_empty_from_non_empty(block: str, expected: bool) -> None:
    assert has_non_empty_needs(block) is expected


def test_only_toml_fences_are_read(tmp_path: Path) -> None:
    doc = "```json\nneeds = [1]\n```\n\n```toml\nneeds = []\n```\n\n~~~toml title\nneeds = [1]\n~~~\n"
    blocks = toml_blocks(doc)
    assert blocks == ["needs = []", "needs = [1]"]


def test_planted_offender_is_found(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_text('```toml\nneeds = [{ path = "x" }]\n```\n', encoding="utf-8")
    (tmp_path / "ok.md").write_text("```toml\nneeds = []\n```\n", encoding="utf-8")
    assert needs_offenders(tmp_path, ["bad.md", "ok.md"]) == ["bad.md"]


@pytest.mark.parametrize("rel", DEPENDS_ON_FILES)
def test_instruction_site_names_the_depends_on_header(rel: str) -> None:
    """AC-0018."""
    text = (_REPO / rel).read_text(encoding="utf-8")
    assert "Depends on:" in text, f"{rel} does not name `Depends on:`"


def test_close_work_keeps_receipts_on_the_dependency_receipts_line() -> None:
    """AC-0018: the receipt's home is the waiting item's header line."""
    text = " ".join((_REPO / _CLOSE_WORK).read_text(encoding="utf-8").split())
    assert "Dependency receipts:" in text
    assert "citing local need" not in text
