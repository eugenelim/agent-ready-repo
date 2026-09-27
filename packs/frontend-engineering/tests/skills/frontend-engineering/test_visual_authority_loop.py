"""The render-and-observe loop: where it activates, and where it stops.

The loop is deliberately not a sixth gate. Adding one would move the gate-count
prose verify mode derives, and would put rendered observation back behind
completion — the failure this loop exists to remove.
"""

from __future__ import annotations

import re

from frontend_engineering_visual_authority_rules import (
    SKILL,
    observation_rows,
    observation_table,
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


def _members(table: dict[str, list[str]], row: str) -> list[str]:
    return [item.strip() for item in table[row][1].split(",")]


def test_the_activation_rubric_enumerates_what_it_covers() -> None:
    assert _members(observation_table("Activation"), "activates") == ACTIVATES


def test_the_activation_rubric_enumerates_what_it_skips() -> None:
    assert _members(observation_table("Activation"), "skips") == SKIPS


def test_activation_carries_a_test_and_demands_the_skip_be_recorded() -> None:
    """An unrecorded skip and a run that never asked the question read the
    same afterwards, and only one of them is a decision."""
    table = observation_table("Activation")
    assert table["test"][1].strip()
    assert table["skip-recorded"][1] == "required"


def test_the_loop_is_bounded_at_one_correction_and_one_verification() -> None:
    table = observation_table("Loop bound")
    assert table["correction-passes"][1] == "1"
    assert table["verification-renders-after-correction"][1] == "1"
    assert table["further-passes"][1] == "operator-requested"
    assert table["residual-divergence"][1] == "recorded-not-iterated"


def test_a_verification_claim_without_a_capture_is_rejected() -> None:
    """The manifest may not carry a visual-verification claim for a surface
    nothing rendered."""
    table = observation_table("Verification claims")
    assert table["claim-without-capture"][1] == "rejected"
    assert table["fabricated-observation"][1] == "never"


def test_the_execute_loop_does_not_discharge_the_gate_capture_matrix() -> None:
    """The representative set is smaller than the gate's by design. If it were
    allowed to stand in for the gate, the slice would have traded a completed
    capture matrix for two screenshots."""
    assert observation_table("Representative states")["discharges-the-gate-matrix"][1] == "no"


def test_divergence_classes_are_perceptual_and_named() -> None:
    classes = [row[0] for row in observation_rows("Divergence classes")]
    for expected in ("composition", "hierarchy", "signature-element", "responsive-intent"):
        assert expected in classes, f"{expected} is not a named divergence class"


def test_the_execute_phase_states_the_loop_and_its_bound() -> None:
    """The rules live in the reference; the always-loaded skill must carry the
    sequence, the bound and the pointer, or the loop never runs."""
    text = SKILL.read_text(encoding="utf-8")
    execute = text.split("## EXECUTE phase", 1)[1].split("\n## ", 1)[0]
    for token in ("render", "observe", "correct"):
        assert token in execute.lower(), f"EXECUTE does not state {token!r}"
    assert "one correction pass" in execute.lower()
    assert "references/visual-observation.md" in execute


def test_the_loop_did_not_become_a_sixth_gate() -> None:
    """Guards the gate-count prose verify mode derives."""
    gates = SKILL.read_text(encoding="utf-8").split("## GATES phase", 1)[1].split("\n## ", 1)[0]
    numbered = re.findall(r"^### (\d+)\. ", gates, re.M)
    assert numbered == ["1", "2", "3", "4", "5"], (
        f"the GATES phase now lists {numbered}; the observation loop belongs "
        f"in EXECUTE, not as a gate"
    )
