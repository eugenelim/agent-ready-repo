"""AC-0022: the frozen channel-axis spec points at the criteria that supersede it.

This lives in the repository's own suite, not the pack's, for the reason the
predecessor's own supersession test gives: the frozen spec belongs to this
repository's spec lifecycle, and a pack test that failed when a `docs/specs/**`
file moved would invert the pack's test boundary.

The shape is that test's, case for case. The pin is each superseded criterion's
entire `- [x]` line rather than a quoted fragment: a pin on "exactly two" would
survive almost any rewrite of the criterion, which inverts what the pointer is
for.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN = REPO_ROOT / "docs" / "specs" / "rendered-page-channel-axis" / "spec.md"
SUCCESSOR = REPO_ROOT / "docs" / "specs" / "channel-minimum-width" / "spec.md"

# The two criteria the successor supersedes, as the frozen spec states them.
# Pinned whole: the point of the pointer is that these obligations did not
# silently become false, so the lines they live on have to still be there, and
# still ticked.
SUPERSEDED_AC_0001 = (
    "- [x] **AC-0001.** When the adopter declares breakpoints `b1 < ... < bn` for a surface, the required channels are exactly the bands those breakpoints bound, each stated as a separate lower-bound and upper-bound predicate that a capture must satisfy together, and each boundary value belonging to the wider band: `<b1`, then `>=bk` with `<bk+1` for each adjacent pair, then `>=bn`. An absent bound means unbounded on that side. A declared breakpoint is a positive integer of CSS pixels; a run refuses a value that is not, because the predicate cells the bands become admit whole numbers only. Origin: the breakpoint values as the adopter declares them, in CSS pixels; the boundary convention follows the mobile-first `min-width` semantics the pack's own `responsive-layout` skill states. Construction test: `test_declared_breakpoints_bound_the_required_channels`; fixtures: a one-breakpoint list, a three-breakpoint list whose interior bands are bounded on both sides, and a capture taken at a breakpoint value exactly."
)

SUPERSEDED_AC_0002 = (
    "- [x] **AC-0002.** When the adopter declares no breakpoints, the required channels are exactly two — a narrow channel at a viewport width of at most 480 CSS pixels and a wide channel at a viewport width of at least 1024 CSS pixels. These two bands are stated literally in the reference and are not produced by AC-0001's derivation, so their boundary values fall on the opposite side: 480 is narrow under the fallback, while a declared breakpoint at 480 places 480 in the band above it. Origin: the pack's own `--breakpoint-sm` and `--breakpoint-lg` tokens, both compared against the browser viewport's width in CSS pixels. A width between those bounds satisfies neither channel. Construction test: `test_fallback_channels_are_the_two_shipped_bands`; fixtures: widths of 480, 768 and 1024 against the shipped band table."
)


def _frozen() -> str:
    return FROZEN.read_text(encoding="utf-8")


def _status_line() -> str:
    for line in _frozen().splitlines():
        if line.startswith("- **Status:**"):
            return line
    raise AssertionError("the frozen spec carries no Status line")


def test_the_status_line_points_at_the_successors() -> None:
    """Half one: the pointer exists, on the Status line, and names both successors.

    Both, because the map is stated per superseded criterion and not pairwise:
    AC-0002 and AC-0003 of the successor supersede AC-0001 here, and both
    supersede AC-0002 here as well. An under-complete map is the failure this
    case exists to catch.
    """
    line = _status_line()
    assert "channel-minimum-width" in line, (
        "the frozen spec's Status line does not name the spec that supersedes "
        "its band-derivation criteria"
    )
    for criterion in ("AC-0001", "AC-0002", "AC-0003"):
        assert criterion in line, (
            f"the pointer does not name {criterion}; it must name both superseded "
            f"criteria and both superseding ones"
        )


def test_the_superseded_criteria_are_still_present_verbatim() -> None:
    """Half two: both superseded criteria are still present verbatim and ticked.

    Named for what it checks. It cannot detect an arbitrary edit elsewhere in the
    frozen body; it detects that these two obligations did not silently become
    false. A `Status:` line pointer is the whole of what a frozen spec may take.
    """
    frozen = _frozen()
    for label, pinned in (("AC-0001", SUPERSEDED_AC_0001), ("AC-0002", SUPERSEDED_AC_0002)):
        assert pinned in frozen, (
            f"the superseded {label} is no longer present verbatim in the frozen "
            f"spec; a frozen spec takes a Status-line pointer and no body edit"
        )


def test_the_successors_state_the_criteria_that_supersede_them() -> None:
    """The pointer has to point at something. Both successors must exist and hold
    the rules the pointer attributes to them: the drop and the raising clamp."""
    successor = SUCCESSOR.read_text(encoding="utf-8")
    ac_0002 = next((l for l in successor.splitlines() if "**AC-0002.**" in l), "")
    ac_0003 = next((l for l in successor.splitlines() if "**AC-0003.**" in l), "")
    assert ac_0002, "the successor spec states no AC-0002"
    assert ac_0003, "the successor spec states no AC-0003"
    assert "below the declared minimum is not a required channel" in ac_0002, (
        "AC-0002 does not hold the drop the pointer attributes to it"
    )
    assert "never lowers one" in ac_0003, (
        "AC-0003 does not hold the raising clamp the pointer attributes to it"
    )
