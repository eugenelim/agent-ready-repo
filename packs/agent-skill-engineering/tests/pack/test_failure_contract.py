"""AC19: every declared failure class carries its four-part contract.

AC19 names classes across several fixtures. Unsupported modes live in
`unsupported-mode-cases.json`, provider absence/ambiguity/staleness in
`provider-cases.json`, router match counts in `router-cases.json`, and compiler
refusal in the shared compile-OKF suite. This fixture covers the remaining
classes — the ones a workflow reaches while acting on a target — and binds each
to the failure prose the workflows actually ship, so a class cannot be declared
in the fixture and go unstated in the instruction an agent reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills"
FAILURE_CASES = PACK_ROOT / "tests" / "fixtures" / "failure-cases.json"
AUTHOR_SKILL = SKILL_ROOT / "author-or-update-agent-skill" / "SKILL.md"
REVIEW_SKILL = SKILL_ROOT / "review-or-optimize-agent-skill" / "SKILL.md"

REQUIRED_FIELDS = ("trigger", "exit_class", "diagnostic", "retained_state", "resume")
FAILURE_IDS = (
    "missing-target",
    "ambiguous-target",
    "refused-write-authority",
    "unconfinable-read",
    "interrupted-write",
    "failed-verification",
    "cleanup-denied",
)
# A retained-state contract is one of exactly these: nothing was kept, something
# recoverable was kept and must be reported, or a temporary path survived.
RETAINED_STATES = {
    "none",
    "recoverable-partial",
    "recoverable-authored",
    "retained-temporary",
}
# The phrase each class must be answerable from in shipped workflow prose.
PROSE_ANCHORS = {
    "missing-target": "missing or ambiguous",
    "ambiguous-target": "missing or ambiguous",
    "refused-write-authority": "authority is refused",
    "unconfinable-read": "a read cannot be confined",
    "interrupted-write": "a write is interrupted",
    "failed-verification": "verification fails",
    "cleanup-denied": "cleanup is denied",
}


def _cases() -> dict[str, dict[str, str]]:
    payload = json.loads(FAILURE_CASES.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "agent-skill-engineering-foundation/v1"
    return {case["id"]: case for case in payload["cases"]}


def _flat(path: Path) -> str:
    """Skill text with runs of whitespace collapsed.

    Assertions below name a contract phrase, not a line-wrap position, so
    rewrapping a paragraph must not redden them.
    """

    return " ".join(path.read_text(encoding="utf-8").split())


def test_failure_fixture_declares_every_class_exactly_once() -> None:
    cases = _cases()
    assert tuple(sorted(cases)) == tuple(sorted(FAILURE_IDS))


@pytest.mark.parametrize("case_id", FAILURE_IDS)
def test_each_failure_class_carries_its_four_part_contract(case_id: str) -> None:
    case = _cases()[case_id]
    for field in REQUIRED_FIELDS:
        assert isinstance(case.get(field), str) and case[field].strip(), field
    assert case["retained_state"] in RETAINED_STATES
    # A resume line must say what the agent does next, not merely restate the
    # failure, so it has to be longer than the diagnostic it accompanies.
    assert len(case["resume"]) > len(case["diagnostic"])


@pytest.mark.parametrize("case_id", FAILURE_IDS)
def test_each_failure_class_is_stated_in_shipped_workflow_prose(case_id: str) -> None:
    shipped = _flat(AUTHOR_SKILL) + " " + _flat(REVIEW_SKILL)
    assert PROSE_ANCHORS[case_id] in shipped, case_id


def test_retained_state_classes_are_reachable_and_distinct() -> None:
    """Every retained-state value in the vocabulary is used by some class.

    An unused value would mean the vocabulary describes a contract the pack
    does not actually declare.
    """

    used = {case["retained_state"] for case in _cases().values()}
    assert used == RETAINED_STATES
