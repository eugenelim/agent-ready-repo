"""Each unattributed issue says why its own chain ended.

Three chains end without an in-scope Epic for three different reasons: no
parent link was ever recorded, the chain walked out of the queried scope,
or it loops. The resolved parent mapping cannot tell them apart -- all
three are `None` by the time it is built -- so a view that derives the
reason there states one of them for all three, and two of those
statements are false about the data in front of the reader.

Asserted per reason rather than "a reason is present": a single truthy
check passes for a view that prints the same sentence three times.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# PROJ-100 is the Epic. PROJ-7 has no parent link, PROJ-8's parent is
# outside the queried scope, and PROJ-9 and PROJ-10 point at each other.
LINKS = {
    "PROJ-100": None,
    "PROJ-1": "PROJ-100",
    "PROJ-7": None,
    "PROJ-8": "PROJ-900",
    "PROJ-9": "PROJ-10",
    "PROJ-10": "PROJ-9",
}
EPICS = ["PROJ-100"]
WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}
FLOW_MOMENT = "2026-09-24T11:30:00Z"
JIRA_MOMENT = "2026-09-24T11:30:12Z"

_UNRESOLVED = ("PROJ-7", "PROJ-8", "PROJ-9")


def _row(key: str) -> dict:
    return {
        "key": key,
        "issuetype_bucket": "feature",
        "delivered_in_window": True,
        "wip_at_to": False,
    }


@pytest.fixture
def parents(load_module):
    return load_module("parents")


@pytest.fixture
def view(load_module):
    return load_module("view")


@pytest.fixture
def reasons(parents, view):
    """The reason string each unattributed issue renders, end to end."""
    rows = view.build_epic_rows(
        per_issue_rows=[_row(key) for key in ("PROJ-1", *_UNRESOLVED)],
        parents=parents.resolve_epics(LINKS, EPICS),
        chain_ends=parents.chain_end_reasons(LINKS, EPICS),
        jira_state={},
        outcomes={"PROJ-100": None},
        window=WINDOW,
        flow_taken_at=FLOW_MOMENT,
        jira_taken_at=JIRA_MOMENT,
    )
    group = {row["epic"]: row for row in rows}["unattributed"]
    return {key: entry["reason"] for key, entry in group["issues"].items()}


def test_an_issue_with_no_parent_link_says_so(reasons):
    assert reasons["PROJ-7"] == "no parent link was recorded for this issue"


def test_a_parent_outside_the_queried_scope_is_named(reasons):
    """The key the chain stopped at is the one fact that lets a reader go
    and look. "No parent link was recorded" is false here: one was."""
    assert reasons["PROJ-8"] == (
        "the parent chain ends at PROJ-900, which is not an in-scope Epic"
    )


def test_a_looping_chain_says_it_looped(reasons):
    """A cycle is a data defect in the tracker, not a missing link, and a
    reader fixes the two issues rather than looking for an absent parent."""
    reason = reasons["PROJ-9"]
    assert "loops" in reason
    assert "8-hop limit" in reason


def test_the_three_reasons_are_distinct(reasons):
    """The failure this whole file exists for: one sentence for all three
    cases reads as an answer and is wrong twice."""
    assert len({reasons[key] for key in _UNRESOLVED}) == 3


def test_a_chain_longer_than_the_hop_limit_reports_the_limit(parents):
    """Walked, not linked: the chain is well-formed and simply deeper than
    Jira's hierarchy, which is the same answer as a loop to a reader."""
    deep = {f"PROJ-{n}": f"PROJ-{n + 1}" for n in range(1, 40)}
    deep["PROJ-40"] = "PROJ-100"

    reason = parents.chain_end_reasons(deep, EPICS)["PROJ-1"]

    assert "8-hop limit" in reason


def test_a_resolved_issue_carries_no_reason(parents):
    """Only unresolved chains appear, so the mapping cannot quietly grow a
    reason for work that did reach its Epic."""
    assert set(parents.chain_end_reasons(LINKS, EPICS)) == {*_UNRESOLVED, "PROJ-10"}


def test_the_rendered_document_carries_the_distinct_reasons(load_module, monkeypatch):
    """The whole render, not the row builder alone: the walk is the only
    place the raw links are still visible, so the wiring between it and
    the rendered row is what the reader actually depends on."""
    cli = load_module("")
    scope = {
        "epic_keys": list(EPICS),
        "descriptions": {"PROJ-100": None},
        "parent_links": dict(LINKS),
        "jira_state": {},
        "flagged_field": None,
        "taken_at": JIRA_MOMENT,
    }
    monkeypatch.setattr(cli.jira_read, "read_scope", lambda **_: scope)
    monkeypatch.setattr(
        cli.flow,
        "run_flow_metrics",
        lambda **_: [_row(key) for key in ("PROJ-1", *_UNRESOLVED)],
    )

    document = cli.render(
        project="PROJ",
        window=WINDOW,
        include_subtasks=False,
        jql=None,
        jira_script=Path("jira.py"),
        flow_scripts_dir=Path("scripts"),
    )

    group = {row["epic"]: row for row in document["epics"]}["unattributed"]
    rendered = {key: entry["reason"] for key, entry in group["issues"].items()}
    assert len({rendered[key] for key in _UNRESOLVED}) == 3
    assert "PROJ-900" in rendered["PROJ-8"]
