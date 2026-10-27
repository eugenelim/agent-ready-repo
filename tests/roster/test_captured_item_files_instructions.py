#!/usr/bin/env python3
"""Instruction roster for the captured-item-files feature (AC-0038 to AC-0040, AC-0044).

AC-0040: in ``work-loop``'s SKILL.md, the paragraph beginning ``Then apply the
**Shaping-item guard**`` names ``captured.items``, ``routes_to``, ``invalid``,
and ``unreadable``, and names neither ``[shaping_queue]`` nor ``[backlog].open``.
AC-0038: each file in the closed list names ``docs/product/captured/``, and no
fenced ``toml`` block in it holds a ``path`` outside the allowed locations.
AC-0044: no fenced ``toml`` block or inline code span holds a table with a
``slug`` key and no ``path`` key.
AC-0039: ``run-okr-cascade``'s SKILL.md names ``Kind: intent`` and ``Type: strategy``.
Standard library only; the checks read files and write nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_WORK_LOOP = _REPO / "packs/core/.apm/skills/work-loop/SKILL.md"
_OPENING = "Then apply the **Shaping-item guard**"

_REQUIRED = ("captured.items", "routes_to", "invalid", "unreadable")
_FORBIDDEN = ("[shaping_queue]", "[backlog].open")


def _guard_paragraph() -> str:
    """The paragraph that begins with the guard's opening phrase."""
    paragraphs = _WORK_LOOP.read_text(encoding="utf-8").split("\n\n")
    matches = [p for p in paragraphs if p.startswith(_OPENING)]
    assert len(matches) == 1, f"expected one paragraph opening {_OPENING!r}"
    return matches[0]


@pytest.mark.parametrize("phrase", _REQUIRED)
def test_guard_paragraph_names_the_captured_item_listing(phrase: str) -> None:
    assert phrase in _guard_paragraph()


@pytest.mark.parametrize("phrase", _FORBIDDEN)
def test_guard_paragraph_names_no_registry_collection(phrase: str) -> None:
    assert phrase not in _guard_paragraph()


_CAPTURED_DIR = "docs/product/captured/"
_OKR_SKILL = "packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md"
_CLOSED_LIST = (
    "packs/core/.apm/skills/work-intake/SKILL.md",
    "packs/core/.apm/skills/work-loop/SKILL.md",
    "packs/core/.apm/skills/work-loop/references/pre-flight-failures.md",
    _OKR_SKILL,
    "packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md",
    "packs/product-engineering/.apm/skills/frame-situation/SKILL.md",
    "packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md",
    "packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md",
    "packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md",
    "guides/architect/how-to/establish-reference-architecture.md",
    "guides/core/reference/workspace-toml-schema.md",
)
_ALLOWED_PATH = re.compile(
    r"docs/product/captured/[^/]+|docs/specs/[^/]+/spec\.md"
    r"|docs/product/(?:briefs|intents)/.+"
)
_PATH_KEY = re.compile(r"(?<![\w-])path\s*=\s*\"([^\"]*)\"")
_SLUG_KEY = re.compile(r"(?<![\w-])slug\s*=")
_PATH_KEY_ANY = re.compile(r"(?<![\w-])path\s*=")
_FENCE = re.compile(r"^`{3,}(\w*)[^\n]*\n(.*?)^`{3,}[ \t]*$", re.DOTALL | re.MULTILINE)
_CODE_SPAN = re.compile(r"`([^`\n]+)`")


def _text(rel: str) -> str:
    return (_REPO / rel).read_text(encoding="utf-8")


def _toml_blocks(text: str) -> list[str]:
    """The body of every fenced block whose info string is ``toml``."""
    return [body for lang, body in _FENCE.findall(text) if lang == "toml"]


def _tables(text: str) -> list[str]:
    """Every outermost ``{...}`` span in ``text``."""
    spans, depth, start = [], 0, 0
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0:
                spans.append(text[start : index + 1])
    return spans


@pytest.mark.parametrize("rel", _CLOSED_LIST)
def test_file_names_the_captured_item_directory(rel: str) -> None:
    assert _CAPTURED_DIR in _text(rel)


@pytest.mark.parametrize("rel", _CLOSED_LIST)
def test_toml_paths_are_captured_spec_brief_or_intent_paths(rel: str) -> None:
    for block in _toml_blocks(_text(rel)):
        for value in _PATH_KEY.findall(block):
            assert _ALLOWED_PATH.fullmatch(value), f"{rel}: path {value!r}"


@pytest.mark.parametrize("rel", _CLOSED_LIST)
def test_no_slug_only_table_remains(rel: str) -> None:
    text = _text(rel)
    prose = _FENCE.sub("", text)
    candidates = [t for block in _toml_blocks(text) for t in _tables(block)]
    candidates += [t for span in _CODE_SPAN.findall(prose) for t in _tables(span)]
    for table in candidates:
        assert not (_SLUG_KEY.search(table) and not _PATH_KEY_ANY.search(table)), (
            f"{rel}: slug-only table {table!r}"
        )


def test_okr_gap_file_names_its_kind_and_type() -> None:
    text = _text(_OKR_SKILL)
    assert "Kind: intent" in text
    assert "Type: strategy" in text
