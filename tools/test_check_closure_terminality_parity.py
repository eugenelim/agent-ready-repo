#!/usr/bin/env python3
"""Mutation tests for check_closure_terminality_parity.py.

Each test mutates one terminal set or the extraction rule in the navigator's
copy and proves that the parity checks detect the disagreement.  The tests
drive the tool's own check functions (_check_nav_intent_parity,
_check_nav_brief_parity, _check_nav_spec_parity, _check_nav_extraction)
rather than re-implementing them locally.  Standard-library-only; tests do
not run the full corpus walk.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        pytest.fail(f"{path}: not importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_parity_tool() -> Any:
    return _load(
        "check_closure_terminality_parity",
        _TOOLS / "check_closure_terminality_parity.py",
    )


def _load_closure_terminality() -> Any:
    return _load(
        "closure_terminality_mut",
        _ROOT / "packs/core/.apm/skills/close-work/scripts/closure_terminality.py",
    )


def _load_nav_terminality() -> Any:
    return _load(
        "nav_intent_terminality_mut",
        _ROOT / "packs/core/.apm/skills/navigate-intents/scripts/intent_terminality.py",
    )


def _load_lint_spec_status() -> Any:
    return _load(
        "lint_spec_status_mut",
        _ROOT / "packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py",
    )


def _load_brief_shape() -> Any:
    return _load(
        "brief_shape_mut",
        _ROOT / "packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py",
    )


def _synthetic_intent_terminal_col(closure: Any) -> dict[str, bool]:
    """Build a terminal-column dict from closure_terminality (already upstream-verified)."""
    return {
        status: (status in closure.TERMINAL_INTENT_STATUSES)
        for status in closure.INTENT_STATUS_VOCABULARY
    }


# ---------------------------------------------------------------------------
# Baseline: unmutated copies must pass all checks.
# ---------------------------------------------------------------------------


def test_nav_intent_parity_passes_baseline() -> None:
    """Unmutated navigator intent set agrees with the upstream Terminal column."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()
    failures = tool._check_nav_intent_parity(nav, _synthetic_intent_terminal_col(closure))
    assert not failures, f"Unexpected intent disagreements: {failures}"


def test_nav_brief_parity_passes_baseline() -> None:
    """Unmutated navigator brief terminality agrees with brief_shape.BRIEF_TRANSITIONS."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    brief_shape = _load_brief_shape()
    failures = tool._check_nav_brief_parity(nav, brief_shape.BRIEF_TRANSITIONS)
    assert not failures, f"Unexpected brief disagreements: {failures}"


def test_nav_spec_parity_passes_baseline() -> None:
    """Unmutated navigator spec terminal set agrees with closure_terminality."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()
    failures = tool._check_nav_spec_parity(nav, closure)
    assert not failures, f"Unexpected spec disagreements: {failures}"


def test_nav_extraction_passes_baseline() -> None:
    """Unmutated navigator extraction rule agrees with lint-spec-status."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    lint = _load_lint_spec_status()
    failures = tool._check_nav_extraction(nav, lint)
    assert not failures, f"Unexpected extraction disagreements: {failures}"


# ---------------------------------------------------------------------------
# Mutation: remove a status from the intent terminal set — check must detect.
# ---------------------------------------------------------------------------


def test_mutated_intent_terminal_set_removal_fails_check() -> None:
    """Removing 'Fulfilled' from the navigator's intent terminal set causes failure."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()

    original = nav.TERMINAL_INTENT_STATUSES
    nav.TERMINAL_INTENT_STATUSES = original - {"Fulfilled"}
    try:
        failures = tool._check_nav_intent_parity(nav, _synthetic_intent_terminal_col(closure))
    finally:
        nav.TERMINAL_INTENT_STATUSES = original

    assert failures, (
        "check must detect disagreement when 'Fulfilled' is removed from "
        "the navigator's intent terminal set"
    )
    assert any("Fulfilled" in f for f in failures), (
        f"expected 'Fulfilled' in failure messages, got: {failures}"
    )


# ---------------------------------------------------------------------------
# Mutation: add an extra status to the intent terminal set — check must detect.
# ---------------------------------------------------------------------------


def test_mutated_intent_terminal_set_addition_fails_check() -> None:
    """Adding an extra status to the navigator's intent terminal set causes failure.

    'Executing' is not a terminal intent status in the upstream Terminal column.
    The check must detect this extra claim even though the status may not
    appear in the upstream's vocabulary.
    """
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()

    original = nav.TERMINAL_INTENT_STATUSES
    nav.TERMINAL_INTENT_STATUSES = original | {"Executing"}
    try:
        failures = tool._check_nav_intent_parity(nav, _synthetic_intent_terminal_col(closure))
    finally:
        nav.TERMINAL_INTENT_STATUSES = original

    assert failures, (
        "check must detect disagreement when an extra status 'Executing' is "
        "added to the navigator's intent terminal set"
    )
    assert any("Executing" in f for f in failures), (
        f"expected 'Executing' in failure messages, got: {failures}"
    )


# ---------------------------------------------------------------------------
# Mutation: change brief terminal set — check must detect.
# ---------------------------------------------------------------------------


def test_mutated_brief_terminal_set_fails_check() -> None:
    """Mutating the navigator's _BRIEF_TRANSITIONS to remove 'Shipped' causes failure.

    Removing ('Executing', 'Shipped') means 'Shipped' still has no source edge,
    but 'Executing' gains no new outgoing edge — instead the navigator no longer
    recognises 'Shipped' as a valid brief status at all, which misaligns it
    with brief_shape.BRIEF_TRANSITIONS where 'Shipped' is a terminal state.
    To produce a clear terminality mismatch, we mutate _BRIEF_TRANSITIONS so
    that 'Shipped' gains an outgoing edge, making the navigator call it non-
    terminal while the upstream still says terminal.
    """
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    brief_shape = _load_brief_shape()

    # Add a fake outgoing edge from 'Shipped', making it non-terminal in the
    # navigator's view while brief_shape.BRIEF_TRANSITIONS still has none.
    original = nav._BRIEF_TRANSITIONS
    nav._BRIEF_TRANSITIONS = original | {("Shipped", "Draft")}
    # Also rebuild the vocabulary so is_brief_terminal can reach 'Shipped'.
    original_vocab = nav._BRIEF_STATUS_VOCABULARY
    nav._BRIEF_STATUS_VOCABULARY = frozenset(
        s for pair in nav._BRIEF_TRANSITIONS for s in pair
    )
    try:
        failures = tool._check_nav_brief_parity(nav, brief_shape.BRIEF_TRANSITIONS)
    finally:
        nav._BRIEF_TRANSITIONS = original
        nav._BRIEF_STATUS_VOCABULARY = original_vocab

    assert failures, (
        "check must detect disagreement when the navigator's _BRIEF_TRANSITIONS "
        "gives 'Shipped' an outgoing edge, making it non-terminal"
    )
    assert any("Shipped" in f for f in failures), (
        f"expected 'Shipped' in failure messages, got: {failures}"
    )


# ---------------------------------------------------------------------------
# Mutation: change spec terminal set — check must detect.
# ---------------------------------------------------------------------------


def test_mutated_spec_terminal_set_fails_check() -> None:
    """Removing 'Archived' from the navigator's spec terminal set causes failure."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()

    original = nav.TERMINAL_SPEC_STATUSES
    nav.TERMINAL_SPEC_STATUSES = original - {"Archived"}
    try:
        failures = tool._check_nav_spec_parity(nav, closure)
    finally:
        nav.TERMINAL_SPEC_STATUSES = original

    assert failures, (
        "check must detect disagreement when 'Archived' is removed from "
        "the navigator's spec terminal set"
    )
    assert any("Archived" in f for f in failures), (
        f"expected 'Archived' in failure messages, got: {failures}"
    )


# ---------------------------------------------------------------------------
# Mutation: change extraction rule — check must detect.
# ---------------------------------------------------------------------------


def test_mutated_extraction_rule_fails_check() -> None:
    """A broken extraction rule that ignores ' (' causes parity failure."""
    tool = _load_parity_tool()
    nav = _load_nav_terminality()
    lint = _load_lint_spec_status()

    def _broken_extract(raw: str) -> str:
        """Extraction that only truncates at ' →' and '<!--', ignoring ' ('."""
        text = raw
        for delim in (" →", "<!--"):
            idx = text.find(delim)
            if idx != -1:
                text = text[:idx]
        return text.strip().split()[0] if text.strip() else ""

    original = nav._extract_status_token
    nav._extract_status_token = _broken_extract
    try:
        failures = tool._check_nav_extraction(nav, lint)
    finally:
        nav._extract_status_token = original

    assert failures, (
        "check must detect disagreement when navigator extraction ignores ' ('"
    )
    # The ' (Fulfilled)' probe (delimiter at position 0) must produce a disagreement.
    assert any("(Fulfilled)" in f for f in failures), (
        f"expected ' (Fulfilled)' probe failure, got: {failures}"
    )


def test_main_fails_when_the_navigator_copy_differs(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() itself runs the navigator checks: a mutated copy makes it exit 1, the real one 0."""
    tool = _load_parity_tool()
    assert tool.main(["--root", str(_ROOT)]) == 0
    original_load = tool._load

    def _load_mutated(name: str, path: Path) -> Any:
        module = original_load(name, path)
        if name == "nav_intent_terminality":
            module.TERMINAL_INTENT_STATUSES = frozenset(
                set(module.TERMINAL_INTENT_STATUSES) | {"Draft"}
            )
        return module

    monkeypatch.setattr(tool, "_load", _load_mutated)
    assert tool.main(["--root", str(_ROOT)]) == 1


_RESOLVER = (
    _ROOT / "packs/core/.apm/skills/close-work/scripts/intent_delivery_relations.py"
)


def _run_with_resolver_copy(
    tmp_path: Path, old: str, new: str, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str]:
    """Run main() against a temporary resolver copy with ``old`` replaced by ``new``."""
    text = _RESOLVER.read_text(encoding="utf-8")
    assert old in text
    copy = tmp_path / "intent_delivery_relations.py"
    copy.write_text(text.replace(old, new, 1), encoding="utf-8")
    tool = _load_parity_tool()
    code = tool.main(["--root", str(_ROOT)], resolver_path=copy)
    return code, capsys.readouterr().err


def test_parent_kind_added_to_resolver_fails_and_names_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0016: a kind only the resolver carries makes the tool exit 1 naming it."""
    code, err = _run_with_resolver_copy(
        tmp_path,
        '_PARENT_INTENT_KINDS: tuple[str, ...] = (\n',
        '_PARENT_INTENT_KINDS: tuple[str, ...] = (\n    "zzkind",\n',
        capsys,
    )
    assert code == 1
    assert "'zzkind'" in err


def test_parent_kind_removed_from_resolver_fails_and_names_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0016: a kind upstream carries and the resolver lacks fails naming it."""
    code, err = _run_with_resolver_copy(tmp_path, '    "capability",\n', "", capsys)
    assert code == 1
    assert "'capability'" in err
