"""The render-and-observe loop: where it activates, and where it stops.

The loop is deliberately not a sixth gate. Adding one would move the gate-count
prose verify mode derives, and would put rendered observation back behind
completion — the failure this loop exists to remove.
"""

from __future__ import annotations

import re

from frontend_engineering_visual_authority_rules import (
    OBSERVATION,
    SKILL,
    observation_rows,
    read,
    rule,
    section,
)

ACTIVATES = [
    "new-surface",
    "new-major-component",
    "substantial-redesign",
    "composition-change",
    "responsive-restructuring",
    "implementation-from-visual-target",
]
SKIPS = [
    "copy-only",
    "behaviour-only",
    "trivial-variant",
    "non-visual-accessibility-fix",
    "engineering-refactor",
]


def _members(heading: str, row: str) -> list[str]:
    return [item.strip() for item in rule(heading, row).split(",")]


def test_the_activation_rubric_enumerates_what_it_covers() -> None:
    assert _members("Activation", "activates") == ACTIVATES


def test_the_activation_rubric_enumerates_what_it_skips() -> None:
    assert _members("Activation", "skips") == SKIPS


def test_activation_carries_a_test_and_demands_the_skip_be_recorded() -> None:
    """An unrecorded skip and a run that never asked the question read the
    same afterwards, and only one of them is a decision."""
    assert rule("Activation", "test").strip()
    assert rule("Activation", "skip-recorded") == "required"


def test_the_loop_is_bounded_at_one_correction_and_one_verification() -> None:
    assert rule("Loop bound", "correction-passes") == "1"
    assert rule("Loop bound", "verification-renders-after-correction") == "1"
    assert rule("Loop bound", "further-passes") == "operator-requested"
    assert rule("Loop bound", "residual-divergence") == "recorded-not-iterated"


def test_a_verification_claim_without_a_capture_is_rejected() -> None:
    """The manifest may not carry a visual-verification claim for a surface
    nothing rendered."""
    assert rule("Verification claims", "claim-without-capture") == "rejected"
    assert rule("Verification claims", "fabricated-observation") == "never"


def test_the_execute_loop_does_not_discharge_the_gate_capture_matrix() -> None:
    """The representative set is smaller than the gate's by design. If it were
    allowed to stand in for the gate, the slice would have traded a completed
    capture matrix for two screenshots."""
    assert rule("Representative states", "discharges-the-gate-matrix") == "no"


def test_divergence_classes_are_perceptual_and_named() -> None:
    classes = [row[0] for row in observation_rows("Divergence classes")]
    for expected in ("composition", "hierarchy", "signature-element", "responsive-intent"):
        assert expected in classes, f"{expected} is not a named divergence class"


def test_the_execute_phase_states_the_loop_and_its_bound() -> None:
    """The rules live in the reference; the always-loaded skill must carry the
    sequence, the bound and the pointer, or the loop never runs.

    Anchored on the fenced flow block, not on the phase. Two weaker forms were
    tried and both were nearly vacuous: searching the whole phase for the three
    words matches the section heading itself ("Render and observe before the
    gates"), so any ordering downstream passes, and "correct responsive
    adaptation" supplies `correct` even with the flow deleted.
    """
    execute = section(read(SKILL), "## EXECUTE phase", "\n## ")
    blocks = re.findall(r"```text\n(.*?)```", execute, re.S)
    assert blocks, (
        "the EXECUTE phase carries no fenced flow block; the render -> observe "
        "-> correct sequence is the contract and prose alone does not state it"
    )
    flow = blocks[0].lower()
    positions = [flow.find(step) for step in ("render", "observe", "correct")]
    assert all(pos >= 0 for pos in positions), (
        f"the flow block is missing steps: "
        f"{[s for s, p in zip(('render', 'observe', 'correct'), positions, strict=True) if p < 0]}"
    )
    assert positions == sorted(positions), (
        f"the flow block does not run render -> observe -> correct in order; "
        f"it reads {flow.strip()!r}"
    )
    assert "one correction pass" in execute.lower(), "EXECUTE does not state the bound"
    assert OBSERVATION.name in execute, "EXECUTE does not route to the reference"


def test_the_loop_did_not_become_a_sixth_gate() -> None:
    """Guards the gate-count prose verify mode derives."""
    gates = section(read(SKILL), "## GATES phase", "\n## ")
    numbered = re.findall(r"^### (\d+)\. ", gates, re.M)
    assert numbered == ["1", "2", "3", "4", "5"], (
        f"the GATES phase now lists {numbered}; the observation loop belongs "
        f"in EXECUTE, not as a gate"
    )
