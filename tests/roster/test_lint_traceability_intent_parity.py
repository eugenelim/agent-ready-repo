"""The traceability lint and the intent navigator admit the same intent files.

Loads both scripts from pack sources, runs each over the real corpus, and
compares the set of ids each reports per repo-relative path. The negative cases
use temporary roots and must fail the same shared check.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
_SKILLS = ROOT / "packs" / "core" / ".apm" / "skills"
REQUIRED_KINDS = ("outcome", "opportunity", "capability", "intent")


def _load(path: Path, module_name: str) -> Any:
    """Load a skill script by path under a unique module name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


lint = _load(
    _SKILLS / "work-loop" / "scripts" / "lint-traceability.py",
    "roster_core_work_loop_lint_traceability_parity",
)
nav = _load(
    _SKILLS / "navigate-intents" / "scripts" / "intent_graph.py",
    "roster_core_navigate_intents_intent_graph_parity",
)


def _invert(ids_to_path: dict[str, Path], root: Path) -> dict[str, set[str]]:
    """Invert id -> path into repo-relative posix path -> set of ids."""
    out: dict[str, set[str]] = {}
    for node_id, path in ids_to_path.items():
        rel = Path(path).resolve().relative_to(root).as_posix()
        out.setdefault(rel, set()).add(node_id)
    return out


def _maps(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (lint map, navigator map) of repo-relative path -> intent ids."""
    root = root.resolve()
    g = lint.Graph()
    base = root / "docs" / "product" / "intents"
    ladder = lint.recognize_ladder(base, root, g)
    intents = lint.recognize_intents(base, root, g, claimed=set(ladder.values()))
    lint_map = _invert(ladder, root)
    for rel, ids in _invert(intents, root).items():
        lint_map.setdefault(rel, set()).update(ids)
    nav_map: dict[str, set[str]] = {}
    for node in nav.derive(root)["nodes"]:
        if node["type"] == "intent":
            nav_map.setdefault(node["path"], set()).add(node["id"])
    return lint_map, nav_map


def _differences(
    lint_map: dict[str, set[str]], nav_map: dict[str, set[str]]
) -> list[str]:
    """One line per path whose id sets differ between the two sides."""
    return [
        f"{path}: lint={sorted(lint_map.get(path, set()))} "
        f"navigator={sorted(nav_map.get(path, set()))}"
        for path in sorted(set(lint_map) | set(nav_map))
        if lint_map.get(path, set()) != nav_map.get(path, set())
    ]


def _kinds(nav_map: dict[str, set[str]]) -> set[str]:
    """Kinds (the id prefix before the colon) the navigator reports."""
    return {i.split(":", 1)[0] for ids in nav_map.values() for i in ids}


def _check(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Maps, differences and non-vacuity; raise AssertionError on any failure."""
    lint_map, nav_map = _maps(root)
    diffs = _differences(lint_map, nav_map)
    assert not diffs, "lint and navigator disagree:\n" + "\n".join(diffs)
    missing = [k for k in REQUIRED_KINDS if k not in _kinds(nav_map)]
    assert not missing, f"vacuous parity check: no navigator ids of kind {missing}"
    return lint_map, nav_map


def _write(root: Path, name: str, slug: str | None, kind: str) -> None:
    base = root / "docs" / "product" / "intents"
    base.mkdir(parents=True, exist_ok=True)
    lines = ["# Title", ""]
    if slug is not None:
        lines.append(f"- **Slug:** {slug}")
    lines += [f"- **Kind:** {kind}", "", "## Body", ""]
    (base / name).write_text("\n".join(lines), encoding="utf-8")


def _four_kinds(root: Path) -> None:
    for kind in REQUIRED_KINDS:
        _write(root, f"{kind}.md", f"s-{kind}", kind)


def test_real_corpus_lint_and_navigator_agree() -> None:
    lint_map, nav_map = _check(ROOT)
    assert lint_map == nav_map


def test_vi_3001_file_name_with_space_is_a_disagreement(tmp_path: Path) -> None:
    _four_kinds(tmp_path)
    _write(tmp_path, "a b.md", "a-b", "outcome")
    with pytest.raises(AssertionError, match="a b.md"):
        _check(tmp_path)


def test_vi_3001_live_intent_without_slug_is_a_derivation_error(
    tmp_path: Path,
) -> None:
    _four_kinds(tmp_path)
    _write(tmp_path, "no-slug.md", None, "outcome")
    with pytest.raises(nav.DerivationError):
        _check(tmp_path)


def test_vi_3001_corpus_without_outcome_is_vacuous(tmp_path: Path) -> None:
    for kind in ("opportunity", "capability", "intent"):
        _write(tmp_path, f"{kind}.md", f"s-{kind}", kind)
    with pytest.raises(AssertionError, match="vacuous"):
        _check(tmp_path)
