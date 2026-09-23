"""The design journey's say-this table records one optionality per row.

Every row names a skill an adopter types, and the guide that owns that skill is
where its optionality is decided. Both values are read from their tables rather
than pinned here, so the assertion is that the two surfaces agree — not that
either says a particular word today.

T7 extends this module with the depth-ladder and composition assertions, which
need both journeys to state their ladder and so cannot be green until the
frontend journey has been edited too.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

XD = ROOT / "packs" / "experience-design"


# ── the say-this table ──────────────────────────────────────────────────────

OPTIONALITY = ("Required", "Optional", "Choose one")

# Each say-this row names a skill an adopter types. The guide table that owns
# that skill's optionality is the how-to step it belongs to; a row with no
# owning guide (the reviewer agent) is checked for shape only.
HOW_TO = ROOT / "guides" / "experience-design" / "how-to"


def _say_this_rows() -> list[list[str]]:
    text = (XD / "JOURNEY.md").read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    rows, seen_header = [], False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    assert rows, "the say-this table has no body rows"
    return rows


def _guide_optionality() -> dict[str, str]:
    """Every `Needed?` verdict the how-to tables record, keyed by skill."""
    found: dict[str, str] = {}
    for guide in sorted(HOW_TO.glob("*.md")):
        for line in guide.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("| `"):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 4 or cells[-1] not in OPTIONALITY:
                continue
            found[cells[0].strip().strip("`")] = cells[-1]
    assert found, "no how-to table records an optionality verdict"
    return found


def test_every_say_this_row_carries_exactly_one_optionality() -> None:
    """Verifies: the criterion quantifies over every row, so the check does too.

    Sampling two rows was the earlier shape, and it left eight rows of a
    ten-row table tickable on no evidence.
    """
    wrong: dict[str, list[str]] = {}
    for row in _say_this_rows():
        skill = row[0].strip().strip("`")
        marks = [v for v in OPTIONALITY if v in row[-1]]
        # `Choose one` contains no other value, and `Required`/`Optional` are
        # disjoint strings, so a row with anything but one match is malformed.
        if len(marks) != 1:
            wrong[skill] = marks
    assert not wrong, (
        f"these say-this rows do not carry exactly one of {OPTIONALITY}: {wrong}"
    )


def test_the_say_this_optionality_agrees_with_the_how_to_guides() -> None:
    """Verifies: the journey and the guide that owns each skill agree.

    Read from both tables rather than pinned here, so re-deciding a skill's
    optionality in its guide fails this rather than silently diverging.
    """
    guides = _guide_optionality()
    disagree = {}
    for row in _say_this_rows():
        skill = row[0].strip().strip("`")
        if skill not in guides:
            continue
        marks = [v for v in OPTIONALITY if v in row[-1]]
        if marks and marks[0] != guides[skill]:
            disagree[skill] = (marks[0], guides[skill])
    assert not disagree, (
        f"the journey and its how-to disagree (skill: journey, guide): {disagree}"
    )
