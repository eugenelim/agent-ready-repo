"""Contract tests for DECIDE cause-depth classification."""

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"

RUNGS = (
    "drop-the-claim",
    "cut-the-item",
    "demote-the-claim",
    "narrow-the-claim",
    "route-to-owner",
    "bound-out-of-scope",
    "repair-the-generator",
    "repair-the-artifact",
    "dismiss-and-re-present",
    "accept-as-proportionate",
)

CLASSIFICATION = (
    "Before taking a ladder answer, classify every sustained finding's cause "
    "as `task-level` or `LLD-level`; an unresolved cause depth authorizes no repair."
)


def _decide() -> str:
    """Return the one DECIDE section from the shipped work-loop skill."""
    text = WORK_LOOP.read_text(encoding="utf-8")
    match = re.search(r"^## Step 5\. DECIDE$.*?(?=^## )", text, re.M | re.S)
    assert match is not None
    return match.group()


def _assert_cause_depth_classification(decide: str) -> None:
    """Assert the classification that must precede a DECIDE ladder answer."""
    assert CLASSIFICATION in decide
    assert decide.index(CLASSIFICATION) < decide.index("An author answering")


def test_decide_classifies_cause_depth_before_taking_a_ladder_answer() -> None:
    """Keep unresolved cause depth from authorising a repair."""
    decide = " ".join(_decide().split())
    _assert_cause_depth_classification(decide)


def test_cause_depth_assertion_reds_for_an_in_memory_mutation() -> None:
    """Prove the classification assertion rejects its removed contract text."""
    mutated = " ".join(_decide().split()).replace(CLASSIFICATION, "")
    with pytest.raises(AssertionError):
        _assert_cause_depth_classification(mutated)


def test_decide_routes_lld_causes_to_generator_instances_and_lifecycle() -> None:
    """Keep LLD repair directed down to owned task instances without plan edits."""
    decide = " ".join(_decide().split())
    assert (
        "For an `LLD-level` cause, take `repair-the-generator`: instances are the "
        "tasks named in the implicated sub-section's `Owned by:` field."
    ) in decide
    assert "Traverse only down from the LLD decision to those tasks, never tasks up to the LLD." in decide
    # The shipped skill must route by naming the two cases, never by citing a
    # feature spec's criterion ids -- those mean nothing to an adopter and
    # dangle once the spec is archived.
    assert "verification ledger" in decide
    assert "controlled amendment" in decide
    assert "AC-00" not in decide
    assert "delivery-contract-lifecycle.md" in decide
    assert "Neither edits the sealed plan." in decide


def test_decide_preserves_the_ten_rungs_in_order() -> None:
    """Keep cause depth as a classification, not a new or reordered rung."""
    decide = _decide()
    rungs = tuple(re.findall(r"^- `([^`]+)` —", decide, re.M))
    assert rungs == RUNGS
