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


# Every shipped text suffix in the swept roots. `.toml` is here because
# `packs/<pack>/pack.toml` carries the `first-value` starter-prompt and
# expected-result strings an adopter reads on first run -- excluding it let the
# banned phrase survive on an installed surface. An absence check's whole value
# is completeness, so an unknown suffix is surfaced rather than skipped.
SWEPT_SUFFIXES = (".md", ".json", ".toml")


def shipped_text_files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in SWEPT_SUFFIXES]


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
        assert shipped_text_files(ROOT / rel), f"{rel} yielded no files to sweep"


def test_no_surface_describes_the_deleted_canonical_fallback() -> None:
    """The absence half. The frontend pre-flight resolves down a precedence
    chain; it has no canonical reference of its own to fall back to."""
    swept = [p for rel in SWEPT_ROOTS for p in shipped_text_files(ROOT / rel)]
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
    raw = (ROOT / REFERENCE_PAGE).read_text(encoding="utf-8")
    rows = [
        line.strip() for line in raw.splitlines()
        if line.strip().startswith("| ") and "|---" not in line
    ]
    labelled = [r for r in rows if r.lower().startswith("| lens |") or "| what it checks |" in r.lower()]
    assert labelled, f"{REFERENCE_PAGE}: the lens table header is gone"
    header = rows.index(labelled[0])
    # The table runs from its header to the first non-row line after it.
    table: list[str] = []
    started = False
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped == rows[header]:
            started = True
            continue
        if started:
            if stripped.startswith("|"):
                if "|---" not in stripped:
                    table.append(stripped)
            elif stripped == "":
                continue
            else:
                break
    assert table, f"{REFERENCE_PAGE}: the lens table has no rows"
    assert table[-1].startswith("| Visual authority |"), (
        f"{REFERENCE_PAGE}: the visual-authority row is not the table's LAST "
        f"row -- the last row is {table[-1][:48]!r}. The table is unnumbered, so "
        f"`lenses 1-5` and `lens 6` resolve by row order; any row after visual "
        f"authority silently repoints both ranges"
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


# --- the guide tree describes the shipped pre-flight -----------------------
#
# These five criteria shipped with no artifact in the first implementation
# pass. Each predicate held when checked by hand, which is exactly the state
# that makes the omission easy to miss: nothing was wrong, and nothing would
# have caught the next edit.

GUIDE_TREE = "guides/frontend-engineering"
HANDOFF_HOWTO = f"{GUIDE_TREE}/how-to/read-the-design-handoff.md"

# Aesthetic anchors. Case-sensitive and whole-word by criterion: the sibling
# skill legitimately says "linear interpolation", and `Arc` is a word a
# case-folded sweep would find inside ordinary prose.
PRODUCT_ANCHORS = ("Linear", "Stripe", "Vercel", "Raycast", "Arc", "Notion", "Toss")

# The deleted set's names. Whitespace-normalized because one live pointer used
# to wrap mid-phrase, which is how an earlier sweep of this tree reported two
# of its sites absent.
DELETED_SET_PHRASES = ("canonical set", "canonical product-reference set", "canonical reference set")

RUNG_ORDER = ("approved-visual-target", "direction-and-taxonomy", "incumbent-system", "local-premise")


def test_no_guide_page_names_a_product_as_an_aesthetic_anchor() -> None:
    """A product name carries whatever a model associates with it today, which
    is the convergence this slice exists to stop. The tutorial used one as its
    worked example in six places."""
    pattern = re.compile(r"\b(" + "|".join(PRODUCT_ANCHORS) + r")\b")
    hits = {
        str(p.relative_to(ROOT)): sorted(set(pattern.findall(p.read_text(encoding="utf-8"))))
        for p in shipped_text_files(ROOT / GUIDE_TREE)
        if pattern.search(p.read_text(encoding="utf-8"))
    }
    assert not hits, f"guide pages still name products as aesthetic anchors: {hits}"


@pytest.mark.parametrize("phrase", DELETED_SET_PHRASES)
def test_no_guide_page_points_at_the_deleted_reference_set(phrase: str) -> None:
    stale = [
        str(p.relative_to(ROOT)) for p in shipped_text_files(ROOT / GUIDE_TREE)
        if contains(normalized(p), phrase)
    ]
    assert not stale, f"{phrase!r} survives in {stale}, naming a set this slice deleted"


def test_the_handoff_how_to_names_the_four_rungs_in_order() -> None:
    """Order is the criterion, not mere presence: a page listing the rungs in
    any order describes a precedence that does not exist."""
    text = normalized(ROOT / HANDOFF_HOWTO)
    positions = []
    for rung in RUNG_ORDER:
        assert contains(text, rung), f"{HANDOFF_HOWTO} does not name the {rung!r} rung"
        positions.append(text.index(rung))
    assert positions == sorted(positions), (
        f"{HANDOFF_HOWTO} names all four rungs but not in precedence order; "
        f"first-mention order was "
        f"{[r for _, r in sorted(zip(positions, RUNG_ORDER, strict=True))]}"
    )


def test_the_reference_page_describes_the_precedence_not_a_named_reference() -> None:
    """The pre-flight summary is what a reader skims to learn what the skill
    does. It listed the deleted step by name."""
    text = normalized(ROOT / REFERENCE_PAGE)
    assert contains(text, "visual-authority precedence"), (
        f"{REFERENCE_PAGE}'s pre-flight description does not name the "
        f"precedence rule"
    )
    for banned in ("named aesthetic\nreference", "seed token block"):
        assert not contains(text, banned.replace("\n", " ")), (
            f"{REFERENCE_PAGE}'s pre-flight description still lists {banned!r} "
            f"as a step"
        )


def test_every_numbered_pre_flight_reference_resolves() -> None:
    """A guide citing `step N` of the pre-flight must cite one that exists.

    The shipped steps are read from the skill rather than listed here, so a
    renumbering moves this check instead of silently invalidating it.

    Matched case-sensitively on a lowercase `step N`, which is how these guides
    cite the *pre-flight*: "(step 0)", "(step 1b -- requires experience-design)",
    "step 2 covers that". A guide's own procedure headings are `## Step N.` with
    a capital, and they are a different sequence that this criterion does not
    govern -- reading both as one list is what made the first version of this
    assertion fail against correct text.
    """
    skill = (
        ROOT / "packs" / "frontend-engineering" / ".apm" / "skills"
        / "frontend-engineering" / "SKILL.md"
    ).read_text(encoding="utf-8")
    shipped = set(re.findall(r"^### (\d+[a-z]?)\. ", skill, re.M))
    assert shipped, "no numbered pre-flight steps found in SKILL.md"
    cited: dict[str, set[str]] = {}
    for path in shipped_text_files(ROOT / GUIDE_TREE):
        found = set(re.findall(r"\bstep (\d+[a-z]?)\b", normalized(path)))
        if found:
            cited[str(path.relative_to(ROOT))] = found
    dangling = {f: sorted(v - shipped) for f, v in cited.items() if v - shipped}
    assert not dangling, (
        f"these guides cite pre-flight steps that do not exist after the "
        f"renumbering: {dangling}. Shipped steps are {sorted(shipped)}"
    )
