"""AC-0052: the events poller does not branch on the `schema` key.

The repository owns one reader of `.loop-run/events.jsonl` besides the engine
itself. A versioned record and a legacy record that differ only by the presence
of `schema` must produce the same parsed result, or adding the key would have
quietly changed what an existing consumer reports.

The two results are compared to each other rather than to a literal. A test that
pinned the expected output would still pass if both sides drifted together, and
it is the *difference* that this criterion is about.
"""
from __future__ import annotations

from pathlib import Path

from agentbundle.workspace_mcp import _EventBridge

_LEGACY = {
    "seq": 7,
    "run_id": "11111111-2222-3333-4444-555555555555",
    "spec": "docs/specs/demo",
    "from": "CODE-VERIFICATION",
    "event": "gates-clean",
    "to": "CODE-REVIEW",
    "at": "2026-09-13T12:00:00Z",
    "phase_started_at": "2026-09-13T11:59:00Z",
    "phase_s": 60,
    "result": "success",
    "awaiting_input": False,
    "waived": False,
    "budgets": {
        "implementation_retry_count": 0,
        "max_implementation_retries": 5,
        "review_retry_count": 0,
        "max_review_retries": 5,
    },
}


def _parsed_result(record: dict, tmp_path: Path) -> tuple:
    """Drive one record through the poller and capture everything it derived."""
    bridge = _EventBridge(repo_root=tmp_path)
    bridge._bound_run_id = record["run_id"]
    notifications = bridge._apply_event(record)
    return (
        notifications,
        bridge._current_state,
        bridge._gate_pending,
        bridge._gate,
        bridge._gate_question,
        bridge._gate_seq,
        bridge._review_findings,
    )


def test_poller_reads_a_versioned_record_exactly_as_it_reads_a_legacy_one(
    tmp_path: Path,
) -> None:
    # AC-0052
    versioned = {**_LEGACY, "schema": 1}
    assert versioned.keys() - _LEGACY.keys() == {"schema"}, "the records must differ only by `schema`"

    legacy_result = _parsed_result(_LEGACY, tmp_path / "legacy")
    versioned_result = _parsed_result(versioned, tmp_path / "versioned")

    assert versioned_result == legacy_result


def test_the_target_records_are_actually_observed(tmp_path: Path) -> None:
    """The equality control is meaningless unless THESE records are observed.

    Proving that some *other* event produces a difference is not enough: an
    implementation that ignored both `gates-clean` records while still handling
    `reviewers-clean` would leave that weaker check green, and the criterion's
    own pair would produce no observation at all.

    So this asserts the target record's own content reaches the parsed result.
    """
    for record, label in ((_LEGACY, "legacy"), ({**_LEGACY, "schema": 1}, "versioned")):
        notifications, current_state, *_ = _parsed_result(record, tmp_path / label)
        assert current_state == record["to"], (
            f"{label}: the poller did not take its state from this record"
        )
        assert notifications, f"{label}: this record produced no notification at all"
        assert any(
            record["to"] in repr(notification) for notification in notifications
        ), f"{label}: no notification carries this record's destination state"


def test_the_comparison_can_fail(tmp_path: Path) -> None:
    """A differing record must still produce a differing result."""
    other = {**_LEGACY, "to": "CODE-HUMAN-GATE", "event": "reviewers-clean"}

    assert _parsed_result(other, tmp_path / "other") != _parsed_result(_LEGACY, tmp_path / "base")
