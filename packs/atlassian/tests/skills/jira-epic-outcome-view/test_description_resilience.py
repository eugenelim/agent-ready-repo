"""One unreadable Epic description costs one Epic's outcome, not the view.

Jira accepts a description of 32,767 characters, which is room to nest
structured content far deeper than the interpreter's own stack. An
unbounded descent over that payload raises `RecursionError` -- an error
no exit-code handler catches, so the process ends on a traceback instead
of the documented 0, 2 or 3, and every other Epic's reading goes with it.
The resilient answer is the one an empty block already gives: no outcome
recorded for that Epic, and the rest of the view rendered.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}
JIRA_MOMENT = "2026-09-24T11:30:12Z"


@pytest.fixture
def outcome(load_module):
    return load_module("outcome")


def _nested_description(depth: int) -> dict:
    """An ADF document whose Outcome block nests `depth` containers deep."""
    node: dict = {"type": "paragraph", "content": [{"type": "text", "text": "deep"}]}
    for _ in range(depth):
        node = {"type": "blockquote", "content": [node]}
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Outcome"}],
            },
            node,
        ],
    }


def test_the_payload_that_crashes_an_unbounded_reader_is_a_legal_description(outcome):
    """Named so the bound cannot be dismissed as defending against input
    Jira would reject: this document is inside Jira's own size limit."""
    payload = json.dumps(_nested_description(800))

    assert len(payload) < 32767, "the reproduction must stay a description Jira accepts"


def test_an_over_nested_description_yields_no_outcome_rather_than_raising(outcome):
    """No `RecursionError`, and no exception of any other kind: neither is
    in the CLI's handler tuples, so either one leaves the process on a
    traceback instead of an exit code."""
    assert outcome.extract_outcome(_nested_description(800)) is None


def test_a_description_inside_the_bound_is_still_read(outcome):
    """The bound is a limit on absurd nesting, not on real descriptions."""
    assert outcome.extract_outcome(_nested_description(4)) == "deep"


def test_one_unreadable_description_does_not_withhold_the_other_epics(
    load_module, monkeypatch
):
    """The whole point of bounding it. An Epic whose description cannot be
    read renders the explicit absence, and every other Epic still renders
    its own reading -- which is what `RecursionError` escaping the reader
    takes away."""
    cli = load_module("")
    scope = {
        "epic_keys": ["PROJ-100", "PROJ-200"],
        "descriptions": {
            "PROJ-100": _nested_description(800),
            "PROJ-200": "## Outcome\nCustomers self-serve.\n",
        },
        "parent_links": {"PROJ-100": None, "PROJ-200": None},
        "jira_state": {},
        "flagged_field": None,
        "taken_at": JIRA_MOMENT,
    }
    monkeypatch.setattr(cli.jira_read, "read_scope", lambda **_: scope)
    monkeypatch.setattr(cli.flow, "run_flow_metrics", lambda **_: [])

    document = cli.render(
        project="PROJ",
        window=WINDOW,
        include_subtasks=False,
        jql=None,
        jira_script=Path("jira.py"),
        flow_scripts_dir=Path("scripts"),
    )

    epics = {row["epic"]: row for row in document["epics"]}
    assert epics["PROJ-100"]["outcome"]["recorded"] is False
    assert epics["PROJ-200"]["outcome"]["text"] == "Customers self-serve."
