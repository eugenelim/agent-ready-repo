"""The traceability lint reads an intent's kind, slug and retirement from its
visible preamble, the way the intent navigator does.

Expected ids are literals; nothing here computes them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"


def _load(path: Path, module_name: str) -> Any:
    """Load a skill script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


lint = _load(
    _SKILLS / "work-loop" / "scripts" / "lint-traceability.py",
    "core_work_loop_lint_traceability_intent_parity",
)


def _observe(tmp_path: Path, content: str) -> tuple[set[str], list[str]]:
    """Write one intent file and return the lint's ids for it plus its notes."""
    base = tmp_path / "docs" / "product" / "intents"
    base.mkdir(parents=True, exist_ok=True)
    (base / "sample-file.md").write_text(content, encoding="utf-8")
    root = tmp_path.resolve()
    g = lint.Graph()
    ladder = lint.recognize_ladder(base, root, g)
    intents = lint.recognize_intents(base, root, g, claimed=set(ladder.values()))
    ids = set(ladder) | set(intents)
    return ids, list(g.notes)


def _doc(preamble: str, body: str = "") -> str:
    return f"# Title\n\n{preamble}\n\n## Body\n\n{body}\n"


_SLUG = "- **Slug:** sample-slug\n"


_VI_1001_CASES = [
        (_doc(_SLUG, "- **Kind:** outcome"), {"intent:sample-slug"}),
        (_doc(_SLUG + "<!-- - **Kind:** opportunity -->"), {"intent:sample-slug"}),
        (_doc(_SLUG + "- **Kind:** `outcome` extra"), {"intent:sample-slug"}),
        (_doc(_SLUG + "- **kind:** outcome"), {"intent:sample-slug"}),
        (_doc(_SLUG + "Text **Kind:** outcome"), {"intent:sample-slug"}),
        (
            _doc(_SLUG + "- **Kind:** opportunity (note)\n- **Level:** capability"),
            {"opportunity:sample-slug"},
        ),
        (_doc(_SLUG + "- **Kind:** `outcome (note)`"), {"outcome:sample-slug"}),
        (_doc(_SLUG + "- **Level:** `capability (note)`"), {"capability:sample-slug"}),
        (_doc(_SLUG + "- **Level:** Capability"), {"capability:sample-slug"}),
]
_VI_1001_IDS = [

        "kind-below-heading",
        "kind-in-comment",
        "kind-backtick-extra",
        "kind-lowercase-label",
        "kind-not-field-line",
        "kind-opportunity-beats-level",
        "kind-backtick-note",
        "level-backtick-note",
        "level-capitalised",
]


@pytest.mark.parametrize(
    ("content", "expected"), _VI_1001_CASES, ids=_VI_1001_IDS
)
def test_vi_1001_kind_and_level(tmp_path: Path, content: str, expected: set[str]) -> None:
    ids, _ = _observe(tmp_path, content)
    assert ids == expected


def test_vi_1002_body_only_slug(tmp_path: Path) -> None:
    ids, notes = _observe(tmp_path, _doc("", "- **Slug:** body-slug"))
    assert ids == set()
    assert len(notes) == 1 and "sample-file.md" in notes[0]


def test_vi_1002_comment_only_slug(tmp_path: Path) -> None:
    ids, notes = _observe(tmp_path, _doc("<!-- - **Slug:** hidden-slug -->"))
    assert ids == set()
    assert len(notes) == 1 and "sample-file.md" in notes[0]


def test_vi_1002_ladder_without_slug_uses_stem(tmp_path: Path) -> None:
    ids, _ = _observe(tmp_path, _doc("- **Kind:** outcome"))
    assert ids == {"outcome:sample-file"}


def test_vi_1002_non_ladder_without_slug(tmp_path: Path) -> None:
    ids, notes = _observe(tmp_path, _doc("- **Status:** live"))
    assert ids == set()
    assert len(notes) == 1 and "sample-file.md" in notes[0]


def test_vi_1002_slug_none(tmp_path: Path) -> None:
    ids, notes = _observe(tmp_path, _doc("- **Slug:** none"))
    assert ids == set()
    assert len(notes) == 1 and "sample-file.md" in notes[0]


_VI_1003_CASES = [
        (_doc(_SLUG + "- **Kind:** outcome\n- **Tombstone:** 2026-01-01"), set()),
        (_doc(_SLUG + "- **Kind:** outcome\n- **Tombstone:**"), set()),
        (_doc(_SLUG, "- **Tombstone:** 2026-01-01"), {"intent:sample-slug"}),
        (
            _doc(_SLUG + "- **Kind:** outcome\n<!-- - **Tombstone:** 2026-01-01 -->"),
            {"outcome:sample-slug"},
        ),
]
_VI_1003_IDS = [
    "tombstone-ladder",
    "tombstone-empty",
    "tombstone-body-only",
    "tombstone-comment",
]


@pytest.mark.parametrize(
    ("content", "expected"), _VI_1003_CASES, ids=_VI_1003_IDS
)
def test_vi_1003_tombstone(tmp_path: Path, content: str, expected: set[str]) -> None:
    ids, _ = _observe(tmp_path, content)
    assert ids == expected


# ---------------------------------------------------------------------------
# VI-2001: three-port agreement (lint, navigator, lint-graph-pointers)
# ---------------------------------------------------------------------------

_NAV = _load(
    _SKILLS / "navigate-intents" / "scripts" / "intent_graph.py",
    "core_navigate_intents_intent_graph_parity",
)
_GRAPH_POINTERS = _load(
    _SKILLS / "work-loop" / "scripts" / "lint-graph-pointers.py",
    "core_work_loop_lint_graph_pointers_parity",
)

# The empty-valued `Tombstone:` fixture is outside the check: the navigator and
# lint-graph-pointers read that file as live while the lint reads it as retired.
_PARITY_CASES = [
    pytest.param(content, id=case_id)
    for (content, _), case_id in zip(_VI_1001_CASES, _VI_1001_IDS, strict=True)
] + [
    pytest.param(content, id=case_id)
    for (content, _), case_id in zip(_VI_1003_CASES, _VI_1003_IDS, strict=True)
    if case_id != "tombstone-empty"
]


@pytest.mark.parametrize("content", _PARITY_CASES)
def test_vi_2001_three_ports_agree(tmp_path: Path, content: str) -> None:
    lint_ids, _ = _observe(tmp_path, content)

    graph = _NAV.derive(tmp_path.resolve())
    rel = "docs/product/intents/sample-file.md"
    nav_ids = {n["id"] for n in graph["nodes"] if n["type"] == "intent" and n["path"] == rel}

    fields = _GRAPH_POINTERS._preamble(content)
    retired = any(fields.get("Tombstone", []))

    if retired:
        assert lint_ids == set()
        assert nav_ids == set()
        assert retired is True
    else:
        assert len(lint_ids) == 1
        assert lint_ids == nav_ids
        (lint_id,) = lint_ids
        assert lint_id.split(":", 1)[0] == _GRAPH_POINTERS._registered_kind(fields)
