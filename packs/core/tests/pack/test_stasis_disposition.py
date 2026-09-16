"""Contracts for full mode's retired stasis stop.

ADR-0104 retires the halt the work-loop instructed when review findings
repeated: the control was evaluated 302 times across two months of recorded
runs and never fired, because its key embeds a line number and an ordinal that
every repair moves.

Three properties are pinned here, and the second is the one that earns its
place. Retiring a halt means editing prose that sits beside prose which must not
move, so the guard against an over-broad edit matters as much as the edit.

1. No runtime reference instructs a halt on the signal (AC-0001), and each
   retains the Surface disposition ADR-0104 requires. Two of those sentences
   carry both, which is why absence alone is not the assertion.
2. Every statement that stasis confers no completion or amendment authority
   survives (AC-0003). These stay true after the retirement.
3. No surface claims a repeated fingerprint *detects* stasis (AC-0002). That is
   false independently of what detection triggers.

Every comparison normalizes whitespace. Four of the pinned statements wrap
across a line break in their source, so byte equality cannot express them --
and a phrase that wraps is exactly how an earlier absence sweep in this
repository missed four surviving restatements of a retired rule.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
WORK_LOOP = PACK_ROOT / ".apm/skills/work-loop"


def _flat(path: Path) -> str:
    """Whitespace-normalized file text, for phrases that wrap across lines."""
    return " ".join(path.read_text(encoding="utf-8").split())


# ── AC-0003: what must not move ──────────────────────────────────────────────
#
# Captured from the tree before any edit task ran, so these literals describe
# the pre-change text rather than ratifying whatever an edit left behind.
#
# Each is read from the file it must survive in. The existing precedent in
# test_contract_amendment_wave4.py asserts its phrase against SKILL.md
# concatenated with delivery-contract-lifecycle.md, which proves the statement
# exists somewhere in the union -- an over-broad edit deleting it from one file
# while it survives in the other leaves that suite green. That is the failure
# this parametrization exists to avoid, so the file is part of each case.

AUTHORITY_STATEMENTS = (
    (
        "references/delivery-contract-lifecycle.md",
        "session end, retry cap, stasis, or model judgment never invokes this "
        "transition or creates a follow-on",
    ),
    (
        "references/delivery-contract-lifecycle.md",
        "Retry caps, review stasis, and a clean intermediate unit never complete "
        "intent or create follow-ons",
    ),
    (
        "SKILL.md",
        "an intermediate clean unit, retry cap, or stasis never completes "
        "accepted intent",
    ),
    (
        "SKILL.md",
        "A merged PR, retry cap, or review stasis alone is not completion",
    ),
    (
        "evals/evals.json",
        "Required work, session end, retry caps, stasis, or model judgment "
        "cannot invoke it automatically",
    ),
    (
        "evals/evals.json",
        "Rejects automatic amendment from time, retry, stasis, or model judgment",
    ),
)


@pytest.mark.parametrize(("relpath", "statement"), AUTHORITY_STATEMENTS)
def test_authority_statement_survives_in_its_own_file(
    relpath: str, statement: str
) -> None:
    """A statement that stasis confers no authority stays true after retirement.

    One case per statement rather than one joined assertion, because a joined
    one names only the first surface it loses.
    """
    target = WORK_LOOP / relpath
    assert target.is_file(), f"pinned surface is missing: {relpath}"
    assert statement in _flat(target), (
        f"authority statement lost from {relpath}: {statement!r}. "
        "Retiring the halt must not reach the statements beside it."
    )
