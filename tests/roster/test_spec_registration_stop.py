#!/usr/bin/env python3
"""Instruction roster for the spec registration stop and the readiness bridge's input.

Spec: docs/specs/spec-registration-stop/spec.md
Spec: docs/specs/readiness-bridge-dispatch-input/spec.md

Each task of those two plans adds its own rows here: closed lists of files and
phrases a writer, guide or instruction must no longer hold (each present at
commit ``dfa3fe067``, so an absence cannot come from a typo in the list), the
phrases they must hold, the governing errata and amendments, and the ledger rows.
Standard library only; the checks read files and git history and write nothing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BASELINE = "dfa3fe067"

# file -> phrases it must not hold (each present at the baseline).
_ABSENT: dict[str, tuple[str, ...]] = {}

# file -> phrases it must hold.
_PRESENT: dict[str, tuple[str, ...]] = {}


def _flat_text(text: str) -> str:
    """The text with each run of whitespace, line breaks included, read as one space."""
    return " ".join(text.split())


def _flat(rel: str) -> str:
    return _flat_text((_REPO / rel).read_text(encoding="utf-8"))


def _baseline(rel: str) -> str:
    """The file's text at the baseline commit, whitespace-normalised."""
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    return _flat_text(result.stdout)


def test_roster_lists_are_well_formed() -> None:
    for table in (_ABSENT, _PRESENT):
        for rel, phrases in table.items():
            assert (_REPO / rel).is_file(), rel
            assert phrases and all(isinstance(p, str) and p for p in phrases), rel


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_no_listed_phrase_remains(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _ABSENT[rel]:
        assert phrase not in flat, f"{rel} holds {phrase!r}"


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_every_banned_phrase_was_present_at_the_baseline(rel: str) -> None:
    flat = _baseline(rel)
    for phrase in _ABSENT[rel]:
        assert phrase in flat, f"{rel} did not hold {phrase!r} at {_BASELINE}"


@pytest.mark.parametrize("rel", sorted(_PRESENT))
def test_every_required_phrase_is_present(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _PRESENT[rel]:
        assert phrase in flat, f"{rel} lacks {phrase!r}"
