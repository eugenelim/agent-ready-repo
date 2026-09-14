"""Guards the journey's promise about the inspection step, and its skip cost.

What a named skip costs at the `accept-frontend-evidence` gate sits under this
delivery's `Ask first` boundary: changing it is a decision about a human gate,
not a thing to do on the way past. Nothing else reads that text — the catalogue
gates do not, and the journey prose does not — so without the pin below the
boundary could be crossed with no signal at all.

The pin is deliberately byte-exact. A reworded line is a failure here by design;
the right response is to get the decision made, then update the constant.
"""

from __future__ import annotations

import pytest
from frontend_engineering_rendered_page_rules import PACK_ROOT

JOURNEY = PACK_ROOT / "JOURNEY.md"

GATE_ID = "accept-frontend-evidence"

# The skip cost as it stood before this delivery, byte for byte. These three
# lines are what the gate says a reader should do about work that could not be
# verified, and what happens if they wave it through.
PINNED_SKIP_COST = {
    "whatGoodLooksLike": (
        'whatGoodLooksLike: "The manifest names what was tested, what passed, '
        'what could not be tested, and what remains accepted risk."'
    ),
    "whatBadLooksLike": (
        'whatBadLooksLike: "Completion is claimed from source inspection alone, '
        "or field performance, manual WCAG 2.2 checks, and screenshots are left "
        'implicit."'
    ),
    "consequence": (
        'consequence: "Without evidence, the surface may look complete while '
        'still failing in browser, accessibility, or performance review."'
    ),
    "known-exceptions": (
        '"Known exceptions are explicit decisions, not hidden missing work."'
    ),
}


@pytest.fixture(scope="module")
def journey() -> str:
    return JOURNEY.read_text(encoding="utf-8")


def gate_block(journey_markdown: str) -> str:
    """The `accept-frontend-evidence` gate entry, up to the next gate."""
    marker = f"- id: {GATE_ID}"
    assert marker in journey_markdown, f"the {GATE_ID} gate is gone from the journey"
    block = journey_markdown.split(marker, 1)[1]
    end = block.find("\n  - id: ")
    return block[:end] if end != -1 else block


@pytest.mark.parametrize("field", sorted(PINNED_SKIP_COST))
def test_skip_cost_at_the_acceptance_gate_is_unchanged(
    journey: str, field: str
) -> None:
    """Verifies: what a named skip costs at `accept-frontend-evidence` is
    byte-identical before and after this delivery."""
    block = gate_block(journey)
    expected = PINNED_SKIP_COST[field]
    assert expected in block, (
        f"the {GATE_ID} gate's {field} changed. Changing what a named skip costs "
        f"at this gate is an `Ask first` decision for this delivery — get the "
        f"decision made, then update PINNED_SKIP_COST.\n\nexpected: {expected}"
    )


def test_the_unverified_items_field_still_accepts_a_written_reason() -> None:
    """The other half of the skip cost lives in the manifest: `unverified items`
    takes a reason, and a named skip remains acceptable with one.

    This delivery does not change that. It makes the skip *visible*, which is a
    different thing from making it cost more.
    """
    skill = (PACK_ROOT / ".apm" / "skills" / "frontend-engineering" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert (
        "| unverified items | Items that could not be verified in this session "
        "with reason (no Chromium, no network, etc.) |" in skill
    ), "the unverified-items field changed; that is an `Ask first` decision here"


# ── the journey promises the step ───────────────────────────────────────────

def test_the_journey_step_names_the_inspection(journey: str) -> None:
    """Verifies: the journey names the step."""
    step = journey.split("### 4. Run verification gates", 1)
    assert len(step) == 2, "journey step 4 is gone or renamed"
    body = " ".join(step[1].split("---", 1)[0].split())
    assert "rendered-page inspection" in body.lower(), (
        "journey step 4 does not name the rendered-page inspection"
    )


def test_the_journey_step_names_its_output(journey: str) -> None:
    """Verifies: the journey names the step's output."""
    body = " ".join(
        journey.split("### 4. Run verification gates", 1)[1].split("---", 1)[0].split()
    )
    assert "observations" in body.lower(), (
        "journey step 4 does not name what the inspection produces"
    )


def test_the_journey_step_names_the_named_skip(journey: str) -> None:
    """Verifies: the journey names the named skip.

    Asserted separately from the step and its output: a journey can promise a
    step and its result while leaving a reader with no idea that it can be
    skipped, or what that looks like when it is.
    """
    body = " ".join(
        journey.split("### 4. Run verification gates", 1)[1].split("---", 1)[0].split()
    )
    assert "named skip" in body.lower() or "skipped" in body.lower(), (
        "journey step 4 does not say the inspection can be skipped"
    )
    assert "browser" in body.lower(), (
        "journey step 4 does not say what a skip depends on"
    )


def test_the_acceptance_gate_checks_the_observations_field(journey: str) -> None:
    """The gate's `whatToCheck` list enumerates the manifest fields a human
    should look for. A field nobody is told to look at is not read."""
    block = gate_block(journey)
    assert "inspection observations" in block, (
        f"the {GATE_ID} gate does not tell the reader to check the inspection "
        f"observations field"
    )
