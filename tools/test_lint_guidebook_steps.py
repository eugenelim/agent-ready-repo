"""Construction tests for the guidebook step contract and its lint.

The contract lives in `guides/AGENTS.md` § The guidebook step contract. That
file is the single source of the obligation identifiers, the closed set of
judgement kinds, and the prohibited vocabulary — this module never restates
them, because a check that carries its own copy of what it checks cannot
detect the two drifting apart.

Covers AC-0001 (the contract is stated and binding) for
`docs/specs/pack-guidebook-walkability/spec.md`. The lint's own cases
(AC-0002, AC-0003, AC-0014, AC-0022) arrive with the lint in T2.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPO_ROOT / "guides" / "AGENTS.md"

SECTION_HEADING = "## The guidebook step contract"

# The normative sentence makes the list binding rather than merely present.
# Matched on its load-bearing clause, not on exact prose, so an editorial
# rewording does not red while a deletion does.
NORMATIVE = re.compile(r"every guidebook step must carry every obligation", re.I)

JUDGEMENT_HEADING = "### Judgement kinds"
VOCABULARY_HEADING = "### Prohibited vocabulary"


def _contract_section() -> str:
    """The contract section's text, or "" when the section is absent."""
    text = CONTRACT.read_text(encoding="utf-8")
    if SECTION_HEADING not in text:
        return ""
    body = text.split(SECTION_HEADING, 1)[1]
    # Ends at the next same-level heading.
    return body.split("\n## ", 1)[0]


def obligation_ids() -> tuple[str, ...]:
    """Identifiers from the contract's obligation table, in document order."""
    rows = re.findall(r"^\|\s*`([a-z_]+)`\s*\|", _contract_section(), re.M)
    return tuple(rows)


def judgement_kinds() -> tuple[str, ...]:
    """The closed set of judgement kinds the contract admits."""
    section = _contract_section()
    if JUDGEMENT_HEADING not in section:
        return ()
    body = section.split(JUDGEMENT_HEADING, 1)[1].split("\n### ", 1)[0]
    # List items only, and `[a-z_-]` rather than `[a-z-]`. Two defects found by
    # mutation while writing this: a pattern excluding underscores cannot see a
    # machine-owned obligation id, which is exactly the shape the overlap
    # assertion exists to detect; and a pattern reading the whole section
    # picked up `judgement_check` from the surrounding prose and flagged a
    # false overlap. The contract states the closed set as a list so this
    # parse is unambiguous.
    return tuple(re.findall(r"^- `([a-z][a-z_-]+)`\s*$", body, re.M))


def prohibited_terms() -> tuple[str, ...]:
    """The lexical terms no guidebook step may contain."""
    section = _contract_section()
    if VOCABULARY_HEADING not in section:
        return ()
    body = section.split(VOCABULARY_HEADING, 1)[1].split("\n### ", 1)[0]
    return tuple(re.findall(r"`([a-z][a-z ]+)`", body))


# --------------------------------------------------------------------------
# AC-0001 — the contract is stated, binding, and carries its four parts.
#
# Both halves fail independently: identifiers without the normative statement,
# and the statement without the identifiers. An earlier draft of the spec had
# this oracle compare the identifiers against the spec's own obligation table;
# that table is numbered rather than identified, so the comparison was not
# implementable. The obligation set's agreement with the *lint* is AC-0003's,
# which is where the real drift risk sits.
# --------------------------------------------------------------------------

def test_ac0001_the_contract_section_exists() -> None:
    assert _contract_section(), f"{CONTRACT} carries no {SECTION_HEADING!r}"


def test_ac0001_the_contract_is_binding_not_merely_present() -> None:
    assert NORMATIVE.search(_contract_section()), (
        "the contract enumerates obligations without stating that every step "
        "must carry them — a list with no normative force"
    )


def test_ac0001_the_contract_enumerates_obligations_by_identifier() -> None:
    ids = obligation_ids()
    assert ids, "the contract states no obligation identifiers"
    assert len(set(ids)) == len(ids), f"duplicate obligation identifier: {ids}"


def test_ac0001_the_contract_declares_its_judgement_kinds() -> None:
    kinds = judgement_kinds()
    assert kinds, f"the contract carries no {JUDGEMENT_HEADING!r} closed set"
    # AC-0014 rests on this: a judgement kind naming a structural obligation
    # would let a human check restate a machine-owned one by construction.
    overlap = set(kinds) & set(obligation_ids())
    assert not overlap, (
        f"judgement kind(s) name a machine-owned obligation: {sorted(overlap)}"
    )


def test_ac0001_the_contract_declares_its_prohibited_vocabulary() -> None:
    assert prohibited_terms(), (
        f"the contract carries no {VOCABULARY_HEADING!r} terms, so AC-0009, "
        "AC-0013 and AC-0020 have nothing lexical to scan for"
    )
