"""Wave 4 completion handoff contracts for work-loop."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"
LIFECYCLE = PACK_ROOT / ".apm/skills/work-loop/references/delivery-contract-lifecycle.md"
EVALS = PACK_ROOT / ".apm/skills/work-loop/evals/evals.json"


def _text() -> str:
    return " ".join(
        (SKILL.read_text(encoding="utf-8") + LIFECYCLE.read_text(encoding="utf-8")).split()
    )


def test_work_loop_completion_handoff_is_bounded_and_close_work_owned() -> None:
    text = _text()

    assert "## Completion evidence handoff" in text
    for field in (
        "delivery ID or session identity",
        "accepted outcome and authority source",
        "implemented scope",
        "verification evidence",
        "durable-output status",
        "stable evidence references",
        "non-goals and independently scoped follow-ons",
        "unresolved obligations and dependencies",
        "completion-event candidate",
        "source, write, and deletion authority facts",
    ):
        assert field in text
    assert "`work-loop` does not declare Closeout-pending or Post-closeout" in text
    assert "select a disposition" in text
    assert "compact coordination" in text
    assert "authorize deletion" in text
    assert "`close-work` alone" in text


def test_direct_light_handoff_preserves_evidence_without_durable_spec() -> None:
    text = _text()

    assert "Direct-light completion uses the same evidence shape" in text
    assert "active-session decision record" in text
    assert "temporary plan" in text
    assert "stable evidence owner outside the temporary record" in text
    assert "session-local plan is not a closeout record" in text


def test_full_mode_handoff_preserves_approved_retention_facts() -> None:
    text = _text()

    for field in (
        "approved retention class",
        "exact locator and fingerprint",
        "required readers",
        "stable post-closeout evidence owner",
        "intended retention or immediate-disposition boundary",
    ):
        assert field in text
    assert "cannot silently change the approved retention decision" in text


def test_spec_plan_mode_does_not_invent_completion_evidence() -> None:
    text = _text()

    assert "Spec-plan mode ends after approved planning" in text
    assert "has no implementation-completion handoff" in text
    assert "never invents delivery evidence for work it did not perform" in text

    finish = text.split("## Finish checklist", 1)[1].split("## FIX", 1)[0]
    assert "Implementation completion only (code mode and direct-light)" in finish


def test_finish_checklist_requires_handoff_without_finishing_closeout() -> None:
    text = _text()

    finish = text.split("## Finish checklist", 1)[1].split("## FIX", 1)[0]
    assert "completion evidence handoff" in finish
    assert "durable-output status" in finish
    assert "close-work remains separate" in finish
    assert "tests and implementation evidence are capability proof" in finish
    assert "not product intent" in finish


def test_work_loop_evals_cover_wave4_evidence_handoff() -> None:
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}

    handoff = by_id["wave4-completion-handoff-has-no-closeout-authority"]
    assert "bounded completion evidence" in handoff["expected_output"]
    assert "does not mark Closeout-pending" in handoff["expected_output"]
    assert "does not select a disposition" in handoff["expected_output"]
    assert "does not authorize deletion" in handoff["expected_output"]
