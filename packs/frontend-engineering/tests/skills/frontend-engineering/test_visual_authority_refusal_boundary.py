"""A refusal halts; it is never a demotion.

The precedence chain added by this slice is a general-purpose fall-through:
a rung that does not supply an axis hands it down. The handoff read's refusals
are not that. A reserved tree, a confinement failure, a non-conforming slug, a
declined confirmation, an exceeded bound or a dependency failure halts the mode
in a named state an operator resolves.

Read together without this boundary, the two contracts contradict: after a
refusal no artifact resolved, so an agent satisfying the precedence table alone
could demote to the incumbent system and carry on building — which is precisely
what the refusal exists to stop. These assertions pin the boundary in the file
that owns the demotion rule.
"""

from __future__ import annotations

from frontend_engineering_visual_authority_rules import (
    OBSERVATION,
    preflight,
    read,
    rule,
)

READ_CONTRACT = "design-handoff.md"


def test_the_reference_states_that_a_refusal_never_demotes() -> None:
    assert rule("Refusals are not demotions", "refusal-demotes") == "never"
    assert "halt" in rule("Refusals are not demotions", "refusal-outcome").lower()


def test_demotion_requires_a_completed_read() -> None:
    """Without this, 'no artifact resolved' covers both a silent rung and a
    refused read, and the two are not the same thing."""
    requires = rule("Refusals are not demotions", "demotion-requires").lower()
    assert "resolved" in requires and "skip" in requires


def test_a_lower_rung_records_how_it_was_reached() -> None:
    """The receiver-side discriminator. Without it, a legitimate demotion and a
    refusal someone absorbed are indistinguishable from the rung below, and the
    prohibition at the refusal site becomes the only control over a failure it
    cannot observe."""
    assert rule("Refusals are not demotions", "demotion-record").strip()
    assert "how it was reached" in read(OBSERVATION)


def test_the_reference_points_at_the_contract_that_owns_refusals() -> None:
    """The file is loadable on its own, and being loaded on its own is exactly
    the post-refusal state."""
    assert READ_CONTRACT in read(OBSERVATION), (
        "the page that defines demotion does not point at the page that "
        "defines refusals"
    )


def test_the_reference_does_not_widen_what_may_be_read() -> None:
    """A direction artifact's composition is the field most likely to carry an
    image or mock path, and an agent told to compare a render against it has a
    motive to open one. The read contract forbids that; the page driving the
    comparison must say so too."""
    text = read(OBSERVATION).lower()
    assert "display string" in text
    assert "no fourth" in text


def test_the_entrypoint_keeps_a_refusal_out_of_the_precedence_chain() -> None:
    assert "a refusal is not one of them" in preflight().lower(), (
        "the pre-flight does not separate a refusal from a routine demotion"
    )
