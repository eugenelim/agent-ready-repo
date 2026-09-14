"""AC-0019: the frozen spec points at the criterion that supersedes it.

This lives in the repository's own suite, not the pack's. The frozen spec belongs
to this repository's spec lifecycle; a pack test that failed when a `docs/specs/**`
file moved would invert the pack's test boundary, which `packs/AGENTS.md` draws
around the pack's own runtime and tests.

The unchanged half is a literal pin on the superseded criterion's own sentence
rather than a byte comparison against a stored snapshot. A snapshot would be a
decaying second copy of a document that already exists, and reading the
merge-base revision would mean spawning git from a test.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN = REPO_ROOT / "docs" / "specs" / "rendered-page-visual-inspection" / "spec.md"
SUCCESSOR = REPO_ROOT / "docs" / "specs" / "rendered-page-channel-axis" / "spec.md"

# The criterion the successor supersedes, as the frozen spec states it. Pinned
# verbatim: the point of the pointer is that this obligation did not silently
# become false, so the sentence it names has to still be there, and still ticked.
SUPERSEDED_CRITERION = (
    "- [x] For each viewport height captured, the capture set contains one capture at\n"
    "  scroll position 0 and one at a non-zero scroll position, or the page is recorded\n"
    "  as not scrollable at that height."
)


def _frozen() -> str:
    return FROZEN.read_text(encoding="utf-8")


def _status_line() -> str:
    for line in _frozen().splitlines():
        if line.startswith("- **Status:**"):
            return line
    raise AssertionError("the frozen spec carries no Status line")


def test_the_status_line_points_at_the_successor() -> None:
    """Half one: the pointer exists, on the Status line, and names the successor."""
    line = _status_line()
    assert "rendered-page-channel-axis" in line, (
        "the frozen spec's Status line does not name the spec that supersedes its "
        "height-only pair criterion"
    )
    assert "AC-0007" in line, "the pointer does not name the superseding criterion"


def test_the_pointer_is_the_only_edit_the_frozen_spec_took() -> None:
    """Half two: the superseded criterion is still present verbatim and ticked.

    Without this the pointer could sit on a spec whose body had been rewritten,
    which is the edit a frozen spec must not take. A `Status:` line pointer is
    the whole of what it may accept.
    """
    assert SUPERSEDED_CRITERION in _frozen(), (
        "the superseded criterion is no longer present verbatim in the frozen "
        "spec; a frozen spec takes a Status-line pointer and no body edit"
    )


def test_the_successor_states_the_criterion_that_supersedes_it() -> None:
    """The pointer has to point at something. AC-0007 must exist and must hold the
    obligation at the width-and-height pair rather than at the height alone."""
    successor = SUCCESSOR.read_text(encoding="utf-8")
    ac_0007 = next(
        (line for line in successor.splitlines() if "**AC-0007.**" in line), ""
    )
    assert ac_0007, "the successor spec states no AC-0007"
    assert "viewport-width" in ac_0007 and "viewport-height" in ac_0007, (
        "AC-0007 does not hold the pair obligation at the width-and-height pair"
    )
