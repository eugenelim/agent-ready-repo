"""Contracts for architect-design's subsystem-decomposition rubric.

The rubric routes a candidate to one of three places: its own architecture
document, a row in this one's element catalogue, or out from under this
document entirely when the accepting owners are not the ones who accept it.
The third route is judged rather than computed — none of `D1`-`D6` says at
what altitude an owner holds authority — so it is deliberately not pinned as
a decision table here. Two properties are load-bearing and neither is visible
to a spell-check.

The first is that ``D1`` is mandatory. It is also the recursion's stopping rule,
so a rubric that lets a child qualify on ``D2``-``D6`` alone does not terminate.

The second is the refusal that size alone never justifies a split. It is the one
a later slice can silently invert: wiring a size trigger into this file would
give an author a number to cut boundaries against, and arbitrary boundaries
chosen to get under a threshold are worse architecture than a large document.
``test_size_alone_never_justifies_a_split`` is therefore written as a negative
over the whole file, not as a phrase match on one sentence.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "decomposition-rubric.md"
)
REVIEW_RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-review"
    / "references"
    / "rubric-design-doc.md"
)

# The distinguishing phrase for each criterion, held here rather than parsed
# from the rubric. An ID-presence check passes when two definitions are swapped;
# this map is what fails on it.
CRITERIA = {
    "D1": "live architectural decision",
    "D2": "boundary",
    "D3": "release or failure unit",
    "D4": "system shape or workload class",
    "D5": "owners or reviewers",
    "D6": "quality scenarios",
}

REFUSALS = (
    "`D1` is unmet",
    "one contract two homes",
    "only large",
)

PARENT_RETAINS = (
    "scope table",
    "structural model",
    "contracts between",
    "cross-child invariants",
    "links",
)


WORD_NUMBERS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|"
    "thirty|forty|fifty|hundred|thousand"
)
UNITS = (
    r"(?:lines?|pages?|bytes?|KB|kB|MB|words?|paragraphs?|sections?|"
    r"characters?|items?|rows?)"
)


def _size_thresholds(text: str) -> list[str]:
    """Return every size figure in the text, in any form it can take.

    Five forms, because a scan that catches only `<digits> <unit>` reads clean
    on the four others and each is still a number an author writes to: a
    digit-and-unit pair, a spelled-out number and unit, a percentage, a colon
    ratio, and a unit-first range.

    **What it does not reach.** ``WORD_NUMBERS`` is a list, so a spelled-out
    number outside it — "thirteen pages" — passes. Closing that needs a
    number-word grammar, and the looser alternative, flagging any word next to
    a unit, reds on ordinary prose. The scan is one defense and not the only
    one: the rule it protects is also stated in the rubric's own text, which a
    reviewer reads. Narrowed here rather than overclaimed in the test name.
    """
    patterns = (
        rf"\b\d[\d,]*\s*{UNITS}\b",
        rf"\b(?:{WORD_NUMBERS})\s+{UNITS}\b",
        rf"{UNITS}\s*[:=]?\s*\d",
        rf"{UNITS}\s*[<>\u2264\u2265]=?\s*\d",
        r"\b\d[\d.,]*\s*%",
        r"\b\d[\d,]*\s*:\s*\d",
        # Tied to a unit, a percent or a ratio on purpose: a bare comparator
        # matches "`D1` plus more than one other criterion", which states no
        # size at all, and a control that reds on correct prose gets removed.
        rf"\b(?:under|over|above|below|exceeds?|longer than|more than|fewer than)"
        rf"\s+(?:{WORD_NUMBERS}|\d[\d,]*)\s*(?:{UNITS}|%)",
    )
    found: list[str] = []
    for pattern in patterns:
        found += re.findall(pattern, text, flags=re.IGNORECASE)
    return found


def _flat(path: Path) -> str:
    """Return the rubric with line wrapping collapsed."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _rows(path: Path = RUBRIC) -> dict[str, str]:
    """Map each criterion ID to the table row that defines it."""
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*\|\s*`(D[1-6])`\s*\|(.+)", line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


def test_all_six_criteria_are_defined() -> None:
    """Every criterion the rubric routes on has a row of its own."""
    assert set(_rows()) == set(CRITERIA)


def test_each_criterion_carries_its_own_meaning() -> None:
    """A row says what its ID means, so two swapped definitions fail."""
    rows = _rows()
    for ident, phrase in CRITERIA.items():
        assert phrase.lower() in rows[ident].lower(), (ident, phrase)


def test_d1_is_mandatory_and_is_the_stopping_rule() -> None:
    """A child qualifies on `D1` plus another, and `D1` ends the descent."""
    text = _flat(RUBRIC)
    assert "`D1` plus at least one other" in text
    assert "stopping rule" in text
    assert "no remaining child has a live architectural decision of its own" in text


def test_the_three_refusals_are_carried() -> None:
    """Each refusal fails on its own rather than behind a sibling."""
    text = _flat(RUBRIC).lower()
    for refusal in REFUSALS:
        assert refusal.lower() in text, refusal


def test_size_alone_never_justifies_a_split() -> None:
    """The rubric states the refusal and carries no threshold to cut against.

    The positive half is the sentence. The negative half is what protects it: no
    page count, line count, byte figure, or section count anywhere in the file.
    A size trigger belongs to the gate that invokes this rubric, never to the
    rubric itself, because a number here is a number an author optimises against.
    """
    raw = RUBRIC.read_text(encoding="utf-8")
    assert "Size alone never justifies a split" in raw

    assert _size_thresholds(raw) == [], (
        f"size threshold in the decomposition rubric: {_size_thresholds(raw)}"
    )


def test_the_size_scan_catches_every_form_a_threshold_takes() -> None:
    """The negative control is itself checked, against each evading form.

    A scan for `<digits> <unit>` alone passes `ten pages`, `50%`, `10:1`, and
    a unit-first range. Each would be a number an author writes to, so each is
    a case here: a control nobody has run against its own evasions reports a
    clean result for the wrong reason.
    """
    for phrasing in (
        "Split a document over 500 lines.",
        "Split a document over ten pages.",
        "Split when a section exceeds 30 KB.",
        "Split when one child is more than 40% of the parent.",
        "Split at a child-to-parent ratio above 10:1.",
        "Split when pages: 10-20 is exceeded.",
        "Keep it under twelve sections.",
        "A document longer than 2,000 words needs splitting.",
    ):
        assert _size_thresholds(phrasing), f"scan missed a threshold: {phrasing!r}"

    for benign in (
        "Size alone never justifies a split.",
        "A child earns its own document when it meets `D1` plus at least one other.",
        "The six criteria are `D1` through `D6`.",
        "Length is a symptom, not a decision.",
        "It must meet `D1` plus more than one other criterion.",
    ):
        assert not _size_thresholds(benign), f"scan false-positived on: {benign!r}"


def test_the_parent_keeps_the_architecture_set_index() -> None:
    """A parent retains the set-level view and restates no child internals."""
    text = _flat(RUBRIC).lower()
    for retained in PARENT_RETAINS:
        assert retained in text, retained
    assert "does not restate child internals" in text


def test_the_review_rubric_mirrors_every_criterion() -> None:
    """A reviewer can raise that one document should have been several.

    Matched as whole words: a bare substring check for `D1` is satisfied by
    `DA10`, so the mirror would look present while the reviewer had no criteria.
    """
    text = REVIEW_RUBRIC.read_text(encoding="utf-8")
    for ident in CRITERIA:
        assert re.search(rf"`{ident}`", text), ident

    # The two tables are duplicated on purpose, so nothing but a comparison
    # keeps them saying the same thing. Presence of all six IDs is satisfied
    # by a table whose definitions have been swapped or rewritten.
    mirrored = _rows(REVIEW_RUBRIC)
    assert set(mirrored) == set(CRITERIA)
    for ident, phrase in CRITERIA.items():
        assert phrase.lower() in mirrored[ident].lower(), (ident, phrase)
