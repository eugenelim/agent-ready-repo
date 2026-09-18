"""Both spec READMEs carry one identical delivery-time-contract note.

`docs/specs/README.md` is the live copy and
`packs/core/seeds/docs/specs/README.md` is what an adopter is seeded with.
Nothing syncs them: the seed is on the self-host check's Excluded list, so the
two drift silently unless something compares them. The note tells a reader that
a shipped spec is the record of an agreement rather than a standing constraint,
which is only worth saying if every adopter meets the same words.

Section bodies are compared, not whole files. The two files legitimately differ
elsewhere and may differ again — `packs/AGENTS.md` forbids shipped pack content
from citing this repository's own records, so the seed can never carry a live
copy's internal citation. Equality is asserted where the contract is, and the
presence arm keeps a section that was deleted from both from passing as equal.

Clauses are matched against whitespace-normalised text, so re-wrapping a
paragraph does not redden a note that is fully present. Not detected, and named
so the blind spot is visible: a clause moved into an HTML comment, and a fenced
block whose first line starts with `# `, which also ends the section early.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIVE = ROOT / "docs/specs/README.md"
SEED = ROOT / "packs/core/seeds/docs/specs/README.md"

HEADING = "## A spec is a delivery-time contract, not a permanent constraint"

#: Each clause is listed separately so deleting any one of them reddens. A
#: single whole-section comparison would hold the two files together while
#: letting them agree on a note that had lost its point.
CLAUSES = (
    "once the feature ships it freezes and the code becomes the truth",
    "is the system moving on, not a rule being broken",
    "correct it by superseding it, not by editing the body",
    "record the erratum where the original cites it",
)


def section(body: str, heading: str) -> str:
    """The text under `heading`, up to the next heading of any level.

    Returned verbatim: `test_the_live_and_seed_notes_are_identical` compares
    wrapping too, and only the clause arms normalise whitespace.
    """
    start = body.find(heading)
    if start == -1:
        return ""
    rest = body[start + len(heading):]
    end = re.search(r"^#{1,6} ", rest, flags=re.MULTILINE)
    return rest[: end.start()].strip() if end else rest.strip()


@pytest.mark.parametrize("path", [LIVE, SEED], ids=["live", "seed"])
def test_the_spec_readme_carries_the_delivery_time_contract_note(
    path: pathlib.Path,
) -> None:
    """A reader of either copy is told a shipped spec is a record, not a rule."""
    body = path.read_text(encoding="utf-8")
    assert HEADING in body, f"{path} lost the delivery-time-contract heading"
    under = section(body, HEADING)
    assert under, f"{path} carries the heading with no body under it"
    flat = " ".join(under.split())
    missing = [clause for clause in CLAUSES if clause not in flat]
    assert missing == [], f"{path} lost {missing}"


def test_the_live_and_seed_notes_are_identical() -> None:
    """An adopter and this repository must read the same words."""
    live = section(LIVE.read_text(encoding="utf-8"), HEADING)
    seed = section(SEED.read_text(encoding="utf-8"), HEADING)
    assert live == seed, "the live and seed notes have drifted apart"
