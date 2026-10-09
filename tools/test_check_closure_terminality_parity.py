#!/usr/bin/env python3
"""Mutation tests for check_closure_terminality_parity.py.

Each test mutates one terminal set or the extraction rule in the navigator's
copy and proves that the parity checks detect the disagreement. Standard-
library-only; tests do not run the full corpus walk.
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


# ---------------------------------------------------------------------------
# Helpers that mirror the parity tool's navigator checks (without corpus walk)
# ---------------------------------------------------------------------------

_EXTRACT_PROBES: list[str] = [
    "Fulfilled",
    "Shipped",
    "Draft",
    "Accepted",
    # ' (' cases: delimiter after the status word
    "Fulfilled (2026-01-01)",
    "Shipped (date)",
    "Draft (something)",
    "Approved (review)",
    # ' (' case: delimiter at position 0 — changes the first word
    " (Fulfilled)",
    # ' →' cases
    "Fulfilled → next",
    "Shipped → archived",
    # '<!--' cases
    "Draft<!-- comment -->",
    "Accepted<!-- inline -->",
    "Superseded <!-- trailing -->",
    "Archived <!-- trailing -->",
    "",
    "  ",
    "Withdrawn",
]


def _check_nav_intent_terminal_set(
    nav_terminality: Any, closure_terminality: Any
) -> list[str]:
    """Return failure messages when navigator intent set disagrees."""
    failures = []
    nav_set = nav_terminality.TERMINAL_INTENT_STATUSES
    closure_set = closure_terminality.TERMINAL_INTENT_STATUSES
    for status in closure_terminality.INTENT_STATUS_VOCABULARY:
        nav_says = status in nav_set
        closure_says = status in closure_set
        if nav_says != closure_says:
            failures.append(
                f"navigator intent status {status!r}: nav says terminal={nav_says}, "
                f"closure says terminal={closure_says}"
            )
    return failures


def _check_nav_spec_terminal_set(
    nav_terminality: Any, closure_terminality: Any
) -> list[str]:
    """Return failure messages when navigator spec terminal set disagrees."""
    failures = []
    nav_set = nav_terminality.TERMINAL_SPEC_STATUSES
    closure_set = closure_terminality.TERMINAL_SPEC_STATUSES
    for status in closure_terminality.SPEC_STATUS_VOCABULARY:
        nav_says = status in nav_set
        closure_says = status in closure_set
        if nav_says != closure_says:
            failures.append(
                f"navigator spec status {status!r}: nav says terminal={nav_says}, "
                f"closure says terminal={closure_says}"
            )
    return failures


def _check_nav_extraction_rule(
    nav_terminality: Any, lint_spec_status: Any
) -> list[str]:
    """Return failure messages when navigator extraction disagrees with lint."""
    failures = []
    for probe in _EXTRACT_PROBES:
        nav_result = nav_terminality._extract_status_token(probe)
        lint_result = lint_spec_status.extract_status_token(probe)
        if nav_result != lint_result:
            failures.append(
                f"probe {probe!r}: nav returns {nav_result!r}, "
                f"lint returns {lint_result!r}"
            )
    return failures


# ---------------------------------------------------------------------------
# Baseline: all checks must pass with real modules.
# ---------------------------------------------------------------------------


def test_nav_terminality_agrees_with_closure_terminality_intent_set() -> None:
    """Navigator intent terminal set agrees with closure_terminality."""
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()
    failures = _check_nav_intent_terminal_set(nav, closure)
    assert not failures, f"Intent terminal set disagreements: {failures}"


def test_nav_terminality_agrees_with_closure_terminality_spec_set() -> None:
    """Navigator spec terminal set agrees with closure_terminality."""
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()
    failures = _check_nav_spec_terminal_set(nav, closure)
    assert not failures, f"Spec terminal set disagreements: {failures}"


def test_nav_extraction_rule_agrees_with_lint_spec_status() -> None:
    """Navigator extraction rule agrees with lint-spec-status over the probe set."""
    nav = _load_nav_terminality()
    lint = _load_lint_spec_status()
    failures = _check_nav_extraction_rule(nav, lint)
    assert not failures, f"Extraction rule disagreements: {failures}"


# ---------------------------------------------------------------------------
# Mutation: change intent terminal set — check must detect disagreement.
# ---------------------------------------------------------------------------


def test_mutated_intent_terminal_set_fails_check() -> None:
    """Removing 'Fulfilled' from the navigator's intent terminal set causes failure."""
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()

    # Mutate: remove Fulfilled from the navigator's terminal set.
    original = nav.TERMINAL_INTENT_STATUSES
    nav.TERMINAL_INTENT_STATUSES = original - {"Fulfilled"}
    try:
        failures = _check_nav_intent_terminal_set(nav, closure)
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
# Mutation: change spec terminal set — check must detect disagreement.
# ---------------------------------------------------------------------------


def test_mutated_spec_terminal_set_fails_check() -> None:
    """Removing 'Archived' from the navigator's spec terminal set causes failure."""
    nav = _load_nav_terminality()
    closure = _load_closure_terminality()

    original = nav.TERMINAL_SPEC_STATUSES
    nav.TERMINAL_SPEC_STATUSES = original - {"Archived"}
    try:
        failures = _check_nav_spec_terminal_set(nav, closure)
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
# Mutation: change extraction rule — check must detect disagreement.
# ---------------------------------------------------------------------------


def test_mutated_extraction_rule_fails_check() -> None:
    """A broken extraction rule that ignores ' (' causes parity failure."""
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
        failures = _check_nav_extraction_rule(nav, lint)
    finally:
        nav._extract_status_token = original

    assert failures, (
        "check must detect disagreement when navigator extraction ignores ' ('"
    )
    # The ' (Fulfilled)' probe (delimiter at position 0) must produce a disagreement.
    assert any("(Fulfilled)" in f for f in failures), (
        f"expected ' (Fulfilled)' probe failure, got: {failures}"
    )
