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
APM_ROOT = PACK_ROOT / ".apm"
WORK_LOOP_REFS = APM_ROOT / "skills" / "work-loop" / "references"

# Named per file rather than joined from a variable at call time: the
# pack-test-boundary lint reads path construction statically and cannot tell
# that a runtime join stays inside the pack.
SKILL = APM_ROOT / "skills" / "work-loop" / "SKILL.md"
EVALS = APM_ROOT / "skills" / "work-loop" / "evals" / "evals.json"
LIFECYCLE = WORK_LOOP_REFS / "delivery-contract-lifecycle.md"
ADJUDICATION = WORK_LOOP_REFS / "finding-adjudication.md"
STATE_SCHEMA = WORK_LOOP_REFS / "state-schema.md"

RUNTIME_REFERENCES = (ADJUDICATION, STATE_SCHEMA, LIFECYCLE)


def _flat(path: Path) -> str:
    """Whitespace-normalized file text, for phrases that wrap across lines."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _rel(path: Path) -> str:
    """Pack-relative path, so a failure names the file a reader can open."""
    return str(path.relative_to(PACK_ROOT))


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
        LIFECYCLE,
        "session end, retry cap, stasis, or model judgment never invokes this "
        "transition or creates a follow-on",
    ),
    (
        LIFECYCLE,
        "Retry caps, review stasis, and a clean intermediate unit never complete "
        "intent or create follow-ons",
    ),
    (
        SKILL,
        "an intermediate clean unit, retry cap, or stasis never completes "
        "accepted intent",
    ),
    (
        SKILL,
        "A merged PR, retry cap, or review stasis alone is not completion",
    ),
    (
        EVALS,
        "Required work, session end, retry caps, stasis, or model judgment "
        "cannot invoke it automatically",
    ),
    (
        EVALS,
        "Rejects automatic amendment from time, retry, stasis, or model judgment",
    ),
)


@pytest.mark.parametrize(("target", "statement"), AUTHORITY_STATEMENTS)
def test_authority_statement_survives_in_its_own_file(
    target: Path, statement: str
) -> None:
    """A statement that stasis confers no authority stays true after retirement.

    One case per statement rather than one joined assertion, because a joined
    one names only the first surface it loses.
    """
    assert target.is_file(), f"pinned surface is missing: {_rel(target)}"
    assert statement in _flat(target), (
        f"authority statement lost from {_rel(target)}: {statement!r}. "
        "Retiring the halt must not reach the statements beside it."
    )


# ── AC-0001: the halt is gone, the Surface is not ────────────────────────────
#
# Absence alone would be satisfied by deleting the rows outright, which would
# leave an emitted field undocumented and -- on two of these surfaces -- would
# delete a Surface disposition ADR-0104 requires. So each surface carries both
# an absence and a presence case.

HALT_PHRASES = (
    "do not start another round",
    "surface immediately; do not run",
    "stops immediately for human replanning",
)


@pytest.mark.parametrize("target", RUNTIME_REFERENCES)
@pytest.mark.parametrize("phrase", HALT_PHRASES)
def test_no_runtime_surface_instructs_a_halt(target: Path, phrase: str) -> None:
    """One case per surface per phrasing, so a missed surface is named."""
    assert target.is_file(), f"swept surface is missing: {_rel(target)}"
    assert phrase not in _flat(target).lower(), (
        f"retired halt {phrase!r} survives in {_rel(target)}"
    )


@pytest.mark.parametrize(
    ("target", "surface_disposition"),
    (
        (ADJUDICATION, "Surface it, and continue the round sequence"),
        (STATE_SCHEMA, "Surface it; it starts no transition and stops no loop"),
        # The lifecycle file carries no Surface disposition, but its rewritten
        # stop-condition clause still needs a presence half: absence cases alone
        # are satisfied by deleting the clause, which would leave the numbered
        # stop conditions silent about a signal the loop still emits.
        (LIFECYCLE, "is Surfaced, not a stop"),
    ),
)
def test_the_surface_disposition_survives(target: Path, surface_disposition: str) -> None:
    """ADR-0104 requires the signal to stay reported to the human.

    Both of these shared a sentence with the halt that was removed, which is
    the way an edit satisfying absence alone loses them.
    """
    assert surface_disposition in _flat(target), (
        f"required disposition lost from {_rel(target)}: {surface_disposition!r}. "
        "ADR-0104 requires the signal to stay reported, and two of these share a "
        "sentence with the halt that was removed."
    )


# ── AC-0002: the refuted detection claim ─────────────────────────────────────

@pytest.mark.parametrize("target", RUNTIME_REFERENCES)
def test_no_surface_claims_a_fingerprint_detects_stasis(target: Path) -> None:
    """The preimage carries a line and an ordinal, so equality is not detection."""
    flat = _flat(target).lower()
    for claim in ("used for stasis detection", "is stasis and stops"):
        assert claim not in flat, (
            f"refuted detection claim {claim!r} survives in {_rel(target)}"
        )
