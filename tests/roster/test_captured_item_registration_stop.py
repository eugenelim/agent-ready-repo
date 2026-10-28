#!/usr/bin/env python3
"""Instruction roster for the captured-item registration stop (AC-0011, AC-0012, AC-0014, AC-0015).

Spec: docs/specs/captured-item-registration-stop/spec.md

AC-0011: over a closed list of writer, suggester and guide files, no line holds
``docs/product/captured/`` together with a registration marker, and, with each
run of whitespace read as one space, none holds a registration phrase. Six pack
files also hold no ``shaping_queue``.
AC-0012: ``run-okr-cascade`` names neither ``workspace.toml`` nor ``shaping_queue``
and still names ``Kind: intent`` and ``Type: strategy``.
AC-0014: a closed list of guide and promise pages holds no shaping-queue gap
wording, and the shared routing reference has no ``defect context`` backlog row.
AC-0015: each governing record's Errata section holds a dated entry that links
RFC-0106, names ``docs/product/captured/`` and names each amended passage.
Standard library only; the checks read files and write nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]

_AC11_FILES = (
    "packs/core/.apm/skills/work-intake/SKILL.md",
    "packs/core/.apm/skills/work-intake/references/lifecycle-index.md",
    "packs/core/.apm/skills/work-loop/SKILL.md",
    "packs/core/.apm/skills/work-loop/references/pre-flight-failures.md",
    "packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md",
    "packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md",
    "packs/product-engineering/.apm/skills/frame-situation/SKILL.md",
    "packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md",
    "packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md",
    "packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md",
    "guides/architect/how-to/establish-reference-architecture.md",
    "guides/core/reference/workspace-toml-schema.md",
    "guides/core/how-to/start-or-remember-work.md",
)
_SIX_PACK_FILES = _AC11_FILES[4:10]
_LINE_MARKERS = ("path =", "path=", "[backlog].open", "shaping_queue")
_AC11_PHRASES = (
    "Do not stop registering",
    "register its path",
    "register that path",
    "registers that path",
    "register that record",
    "registers that file's path",
    "entry that registers",
    "Entry that registers",
    "writes the record and the entry",
    "writes the record and adds",
    "registered by",
    "is registered in",
    "TOML entry",
    "then register it",
    "register it through",
    "Its index entry's",
    "Its registry entry points at that file",
)

_OKR_DIR = "packs/product-strategy/.apm/skills/run-okr-cascade/"
_OKR_FILES = (_OKR_DIR + "SKILL.md", _OKR_DIR + "references/cross-pack-routing.md")

_AC14_FILES = (
    "guides/core/explanation/role-journeys.md",
    "guides/product-engineering/how-to/frame-a-situation.md",
    "guides/product-strategy/how-to/cascade-okrs-into-the-shaping-queue.md",
    "guides/product-strategy/how-to/set-the-direction.md",
    "guides/product-strategy/reference/frameworks-and-artifacts.md",
    "guides/product-strategy/explanation/why-strategy-is-its-own-seat.md",
    "packs/product-strategy/README.md",
    "packs/product-strategy/JOURNEY.md",
    "packs/product-strategy/DESIGN.md",
    "web/src/content/journeys/product-strategy.md",
)
_AC14_PHRASES = (
    '{type = "strategy"}',
    "shaping_queue",
    "gap entries in workspace.toml",
    "`workspace.toml` entries",
    "`workspace.toml` snippet",
    "workspace.toml suggestion",
    "strategy entries in `workspace.toml`",
    "strategy-type entry",
    "adds each gap to `workspace.toml`",
)
_SHARED_ROUTING = "guides/_shared/reference/work-intake-routing-and-lifecycle.md"
_DEFECT_ROW = "| defect context | `backlog.open` |"

_ERRATA = {
    "docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md": (
        "D9",
        "Cross-pack routing contract",
        "Type: strategy",
    ),
    "docs/rfc/0063-product-strategy-pack.md": (
        "Reviewer brief",
        "D9",
        "Skill set (v1)",
        "steps 4 and 5",
        "diagram",
        "Boundary",
        "Type: strategy",
    ),
    "docs/rfc/0083-work-intake-and-artifact-routing.md": (
        "§6",
        "start route",
        "remember route",
        "flow",
        "§8",
        "[backlog].open",
        "[backlog].closed",
        "unassigned-artifact sentence",
        "defect sentence",
        "defect move",
        "defect dependency rule",
    ),
}
_MIN_DATE = "2026-10-27"


def _text(rel: str) -> str:
    return (_REPO / rel).read_text(encoding="utf-8")


def _flat(rel: str) -> str:
    """The file with each run of whitespace, line breaks included, read as one space."""
    return " ".join(_text(rel).split())


@pytest.mark.parametrize("rel", _AC11_FILES)
def test_no_line_pairs_the_captured_directory_with_a_registration_marker(rel: str) -> None:
    for number, line in enumerate(_text(rel).splitlines(), 1):
        if "docs/product/captured/" in line:
            for marker in _LINE_MARKERS:
                assert marker not in line, f"{rel}:{number} holds {marker!r}"


@pytest.mark.parametrize("rel", _AC11_FILES)
def test_no_registration_phrase_remains(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _AC11_PHRASES:
        assert phrase not in flat, f"{rel} holds {phrase!r}"


@pytest.mark.parametrize("rel", _SIX_PACK_FILES)
def test_six_pack_files_name_no_shaping_queue(rel: str) -> None:
    for number, line in enumerate(_text(rel).splitlines(), 1):
        assert "shaping_queue" not in line, f"{rel}:{number}"


@pytest.mark.parametrize("rel", _OKR_FILES)
def test_okr_cascade_names_neither_workspace_toml_nor_shaping_queue(rel: str) -> None:
    text = _text(rel)
    assert "workspace.toml" not in text
    assert "shaping_queue" not in text


def test_okr_cascade_skill_still_names_kind_and_type() -> None:
    text = _text(_OKR_FILES[0])
    assert "Kind: intent" in text
    assert "Type: strategy" in text


@pytest.mark.parametrize("rel", _AC14_FILES)
def test_promise_page_holds_no_shaping_queue_gap_wording(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _AC14_PHRASES:
        assert phrase not in flat, f"{rel} holds {phrase!r}"


def test_shared_routing_reference_has_no_defect_context_backlog_row() -> None:
    assert _DEFECT_ROW not in _flat(_SHARED_ROUTING)


def _errata_entries(rel: str) -> list[str]:
    """Each top-level bullet of the record's ``## Errata`` section."""
    text = _text(rel)
    start = text.index("\n## Errata")
    section = text[start + 1 :]
    following = re.search(r"\n## (?!Errata)", section)
    if following:
        section = section[: following.start()]
    return re.split(r"\n(?=- \*\*)", section)


@pytest.mark.parametrize("rel", sorted(_ERRATA))
def test_errata_entry_names_every_amended_passage(rel: str) -> None:
    problems: list[str] = []
    for entry in _errata_entries(rel):
        match = re.match(r"- \*\*(\d{4}-\d{2}-\d{2})", entry)
        if not match or match.group(1) < _MIN_DATE:
            continue
        flat = " ".join(entry.split())
        missing = [p for p in _ERRATA[rel] if p not in flat]
        links_rfc = "0106-stop-registering-derivable-work" in entry
        if links_rfc and "docs/product/captured/" in flat and not missing:
            return
        problems.append(f"{match.group(1)} entry: missing {missing}")
    raise AssertionError(f"{rel}: no qualifying errata entry; {problems}")
