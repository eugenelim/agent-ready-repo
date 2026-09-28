"""Adopter-facing prose agrees with what the visual-authority slice ships.

Three claims live across two packs, two guide trees and a generated journey
mirror. Nothing else compares them: `lint-web-journey-parity` counts skills, and
no lint reads a pack's guide tree against its shipped skill. A carrier left
behind therefore ships a page describing a mechanism that is gone, with every
other gate green -- which is the defect this module exists to catch, and which
the slice's own history records happening four times before the predicates below
were written this way.

Two design rules, both learned the hard way in that history:

* **Normalized, not raw.** Every predicate here reads the file with runs of
  whitespace collapsed. Four of the carriers wrap mid-phrase, and a raw
  containment check reports them absent while they are present.
* **Anchored, not file-wide.** A presence check asserting only that a literal
  appears somewhere in a file passes while the sentence that needed correcting
  still says the old thing. Each presence assertion below is scoped -- to a
  sentence via an anchor that survives the correction, or to a named section.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# --- shared reading -------------------------------------------------------


def normalized(path: Path) -> str:
    """File text with whitespace runs collapsed, so a wrapped phrase matches."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def contains(haystack: str, literal: str) -> bool:
    """Case-insensitive containment tolerant of the wrap points in these files."""
    return re.search(re.escape(literal).replace(r"\ ", r"\s+"), haystack, re.I) is not None


def sentences(text: str) -> list[str]:
    """Split on sentence enders and table-cell pipes.

    The pipe matters: one carrier is a cell in a Markdown table, where the
    sentence boundary is the cell edge rather than a full stop.
    """
    return re.split(r"(?<=[.!|])\s+", text)


def markdown_files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in (".md", ".json")]


# --- the deleted fallback -------------------------------------------------


BANNED_FALLBACK = "falls back to its own canonical reference"

SWEPT_ROOTS = ("packs/experience-design", "guides/experience-design", "guides/frontend-engineering")
NAMED_MIRROR = "web/src/content/journeys/experience-design.md"

# Site -> the clause that survives the correction and locates its sentence.
# Without an anchor there is nothing to scope to: the phrase that identified
# the sentence is exactly what the correction deletes.
FALLBACK_CARRIERS = {
    "packs/experience-design/JOURNEY.md": "is not an error",
    "guides/experience-design/how-to/choose-the-depth.md": "is not an error",
    "guides/experience-design/README.md": "is not an error",
    NAMED_MIRROR: "is not an error",
    "guides/frontend-engineering/how-to/read-the-design-handoff.md": "for whatever is missing",
}


def test_the_swept_roots_are_not_empty() -> None:
    """A sweep over an empty root passes trivially."""
    for rel in SWEPT_ROOTS:
        assert markdown_files(ROOT / rel), f"{rel} yielded no files to sweep"


def test_no_surface_describes_the_deleted_canonical_fallback() -> None:
    """The absence half. The frontend pre-flight resolves down a precedence
    chain; it has no canonical reference of its own to fall back to."""
    swept = [p for rel in SWEPT_ROOTS for p in markdown_files(ROOT / rel)]
    swept.append(ROOT / NAMED_MIRROR)
    stale = [
        str(p.relative_to(ROOT)) for p in swept if contains(normalized(p), BANNED_FALLBACK)
    ]
    assert not stale, (
        f"these surfaces still describe the deleted canonical fallback: {stale}"
    )


@pytest.mark.parametrize("relative_path,anchor", sorted(FALLBACK_CARRIERS.items()))
def test_each_corrected_site_hands_the_slot_to_a_lower_rung(
    relative_path: str, anchor: str
) -> None:
    """The presence half, scoped by anchor rather than by file.

    Deleting the phrase is not enough: the replacement has to say what actually
    happens now. Scoping to the sentence carrying the anchor is what stops
    `a lower rung` satisfying this from somewhere else on the page.
    """
    path = ROOT / relative_path
    assert path.exists(), f"{relative_path} is gone; this carrier list is stale"
    text = normalized(path)
    assert contains(text, anchor), (
        f"{relative_path} no longer carries its anchor {anchor!r}, so this "
        f"assertion can no longer locate the sentence it checks"
    )
    located = [s for s in sentences(text) if contains(s, anchor) and contains(s, "a lower rung")]
    assert located, (
        f"{relative_path}: no single sentence carries both {anchor!r} and "
        f"'a lower rung'. The phrase was removed but its replacement does not "
        f"say the slot resolves from a lower rung, or the two ended up in "
        f"different sentences"
    )


# --- the reviewer's seventh lens ------------------------------------------

REFERENCE_PAGE = "guides/frontend-engineering/reference/frontend-engineering.md"

# Banned because a presence check alone cannot evict a stale count. `a sixth`
# rather than `for a sixth`: the shorter literal occurs nowhere legitimate in
# this tree, and the longer one leaves "and a sixth for the rendered page" legal.
STALE_LENS_COUNTS = ("five lenses", "a sixth", "six lenses")


def test_the_reference_page_counts_seven_lenses() -> None:
    """The shipped agent carries seven lenses. Nothing pinned this page's count,
    so it sat at six after the lens landed."""
    text = normalized(ROOT / REFERENCE_PAGE)
    assert contains(text, "seven lenses"), (
        f"{REFERENCE_PAGE} does not say seven lenses, so it disagrees with the "
        f"agent it documents"
    )
    stale = [literal for literal in STALE_LENS_COUNTS if contains(text, literal)]
    assert not stale, (
        f"{REFERENCE_PAGE} still carries stale lens counts {stale}, which "
        f"contradict its own seven-lens claim"
    )


def test_the_visual_authority_row_is_the_tables_last() -> None:
    """The lens table is unnumbered, so `lenses 1-5` and `lens 6` resolve by row
    order alone. A row inserted anywhere but last silently repoints both ranges
    while every literal check stays green."""
    text = normalized(ROOT / REFERENCE_PAGE)
    row = text.rfind("| Visual authority |")
    assert row != -1, f"{REFERENCE_PAGE} has no visual-authority lens row"
    # Every other lens row must appear before it. Checked against the row that
    # is last today rather than against a count, so adding an eighth lens fails
    # here loudly instead of passing on an arithmetic coincidence.
    assert "| Reader-visible layout failure |" not in text[row:], (
        f"{REFERENCE_PAGE}: the visual-authority row is not the table's last "
        f"row, so the page's `lenses 1-5` and `lens 6` ranges now point at the "
        f"wrong lenses"
    )


def test_the_reference_page_states_what_confirms_the_seventh_lens() -> None:
    """A page can say seven, table seven, and still account for the evidence
    basis of six. The agent file is held to this by its own criterion; this is
    the guide-side counterpart."""
    text = normalized(ROOT / REFERENCE_PAGE)
    assert contains(text, "Evidence per lens"), (
        f"{REFERENCE_PAGE} no longer carries a per-lens evidence rule"
    )
    assert contains(text, "manifest confirms lens 7"), (
        f"{REFERENCE_PAGE}'s per-lens evidence rule does not say what confirms "
        f"the seventh lens, so it accounts for six of seven"
    )
