"""Lint and navigator agree on ``Related intents``; one derivation reads it.

Covers AC-0006 and AC-0016 of ``docs/specs/related-intents-field/``. The lint
and the navigator are separate ports; these tests hold them to one verdict per
fixture and pin which scripts in the pack may name the field.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = Path(__file__).resolve().parents[3]
_APM = _PACK / ".apm"
_SKILLS = _APM / "skills"
_FIELD = "Related intents"


def _load(path: Path, module_name: str) -> Any:
    """Load a skill script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


lint = _load(
    _SKILLS / "work-intake" / "scripts" / "intent_corpus_lint.py",
    "core_related_parity_lint",
)
nav = _load(
    _SKILLS / "navigate-intents" / "scripts" / "navigate_intents.py",
    "core_related_parity_nav",
)


# -- Fixture helpers -----------------------------------------------------------


def _intent(
    root: Path,
    slug: str,
    *,
    level: str = "Feature",
    kind: str | None = None,
    related: list[str] | None = None,
    tombstone: bool = False,
) -> None:
    """Write one lint-clean intent; each ``related`` entry is its own field line."""
    directory = root / "docs" / "product" / "intents"
    directory.mkdir(parents=True, exist_ok=True)
    if tombstone:
        lines = [f"# Retired: {slug}", "", f"- **Slug:** `{slug}`", "- **Tombstone:** 2026-09-21",
                 "- **Superseded by:** intent:keeper", ""]
    else:
        lines = [f"# Intent: {slug}", "", "- **Owner:** eugenelim", f"- **Slug:** `{slug}`",
                 f"- **Level:** {level}"]
        if kind:
            lines.append(f"- **Kind:** {kind}")
        lines.append("- **Status:** Draft")
        lines += [f"- **{_FIELD}:** {value}" for value in related or []]
        lines += ["", "## Outcome", "", "An outcome sentence.", ""]
    (directory / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


def _lint(root: Path) -> Any:
    return lint.lint_corpus(root, root / "docs" / "product" / "intents")


def _nav_written_here(root: Path) -> dict[str, list[dict[str, Any]]]:
    """Each intent's ``related_written_here`` list from the navigator's tree query."""
    result, code = nav.run_query(root, ["query", "--operation", "tree"])
    assert code == 0, result
    return {entry["id"]: entry["related_written_here"] for entry in result["intents"]}


# -- AC-0006: a clean corpus ---------------------------------------------------


def test_clean_corpus_lints_clean_and_resolves_every_edge(tmp_path: Path) -> None:
    """AC-0006: normalized Kind/Level spellings and every prefix agree."""
    _intent(tmp_path, "t-cap", level="Capability")
    _intent(tmp_path, "t-legacy", level="capability (legacy)")
    _intent(tmp_path, "t-retired-name", level="capability → retired name")
    _intent(tmp_path, "t-outcome", kind="`outcome`")
    _intent(tmp_path, "t-opp", kind="<!-- c --> opportunity")
    _intent(tmp_path, "t-plain")
    _intent(tmp_path, "src-all", related=[
        "capability:t-cap, capability:t-legacy, capability:t-retired-name, "
        "outcome:t-outcome, opportunity:t-opp, intent:t-plain",
    ])
    _intent(tmp_path, "src-note", related=["`intent:t-plain, capability:t-cap` <!-- note -->"])
    _intent(tmp_path, "src-none", related=["None — later"])

    result = _lint(tmp_path)
    assert result.exit_code == 0, (result.violations, result.unreadable)
    assert result.violations == []

    written_here = _nav_written_here(tmp_path)
    edges = [e for lst in written_here.values() for e in lst]
    assert edges and all("state" not in e for e in edges), edges
    by_source = {s: written_here[f"intent:{s}"] for s in ("src-all", "src-note", "src-none")}
    assert [e["to"] for e in by_source["src-all"]] == [
        "capability:t-cap", "capability:t-legacy", "capability:t-retired-name",
        "outcome:t-outcome", "opportunity:t-opp", "intent:t-plain",
    ]
    assert [e["to"] for e in by_source["src-note"]] == ["intent:t-plain", "capability:t-cap"]
    assert by_source["src-none"] == []


# -- AC-0006: each refusal state -----------------------------------------------


def _build_refusal(root: Path, state: str) -> None:
    _intent(root, "keeper")
    _intent(root, "other", level="Capability")
    if state == "self_reference":
        _intent(root, "src", related=["intent:src"])
    elif state == "kind_mismatch":
        _intent(root, "src", related=["intent:other"])
    elif state == "retired_target":
        _intent(root, "gone", tombstone=True)
        _intent(root, "src", related=["intent:gone"])
    elif state == "dangling":
        _intent(root, "src", related=["intent:ghost"])
    elif state == "out_of_type":
        _intent(root, "src", related=["brief:keeper"])
    elif state == "unparseable":
        _intent(root, "src", related=["wibble"])
    else:
        assert state == "multiple_values"
        _intent(root, "src", related=["intent:keeper", "capability:other"])


@pytest.mark.parametrize("state", [
    "self_reference", "kind_mismatch", "retired_target", "dangling",
    "out_of_type", "unparseable", "multiple_values",
])
def test_navigator_refusal_is_a_lint_violation(tmp_path: Path, state: str) -> None:
    """AC-0006: every state the navigator refuses, the lint exits 1 on."""
    _build_refusal(tmp_path, state)
    edges = _nav_written_here(tmp_path)["intent:src"]
    assert [e.get("state") for e in edges] == [state], edges
    result = _lint(tmp_path)
    assert result.exit_code == 1, (result.violations, result.unreadable)
    assert any(v.field == _FIELD and v.path.endswith("src.md") for v in result.violations)


def test_none_among_items_is_refused_by_both(tmp_path: Path) -> None:
    """AC-0006: `none, intent:a` is an unparseable `none` edge beside the intent edge."""
    _intent(tmp_path, "a")
    _intent(tmp_path, "src", related=["none, intent:a"])
    edges = _nav_written_here(tmp_path)["intent:src"]
    assert [(e["value"], e.get("state")) for e in edges] == [
        ("none", "unparseable"), ("intent:a", None),
    ]
    assert _lint(tmp_path).exit_code == 1


# -- AC-0016: one derivation reads the field -----------------------------------

_EXPECTED_READERS = {
    "navigate-intents/scripts/intent_graph.py",
    "close-work/scripts/intent_graph.py",
    "navigate-intents/scripts/navigate_intents.py",
    "work-intake/scripts/intent_shape.py",
}


def _scan(apm: Path) -> set[str]:
    """Skill-relative paths of every ``*.py`` under *apm* that names the field."""
    skills = apm / "skills"
    return {
        path.relative_to(skills).as_posix()
        for path in apm.rglob("*.py")
        if _FIELD in path.read_text(encoding="utf-8")
    }


def test_only_the_derivation_lint_and_navigator_name_the_field() -> None:
    """AC-0016: no reconciler or closure script reads `Related intents`."""
    assert _scan(_APM) == _EXPECTED_READERS


def test_scan_reports_a_planted_reader(tmp_path: Path) -> None:
    """AC-0016 positive control: the scan finds a planted literal."""
    copy = tmp_path / ".apm"
    shutil.copytree(_APM, copy, ignore=shutil.ignore_patterns("__pycache__"))
    planted = copy / "skills" / "close-work" / "scripts" / "closure_index.py"
    planted.write_text(planted.read_text(encoding="utf-8") + f'\n_X = "{_FIELD}"\n', encoding="utf-8")
    assert "close-work/scripts/closure_index.py" in _scan(copy)
