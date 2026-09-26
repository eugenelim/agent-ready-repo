# Stored and validated in PLAN's T1 Tests: subsection. Each test carries its
# own marker. Fixtures use flow-metrics' real per-issue wire contract, taken
# from `output.py::_per_issue_row_to_dict` — the field list is not invented.
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_VIEW_PKG = (
    _PACK_ROOT / ".apm" / "skills" / "jira-epic-outcome-view"
    / "scripts" / "jira_epic_outcome_view"
)
_VIEW_NAME = "atlassian_jira_epic_outcome_view"


def _load_view_submodule(submodule: str):
    """Load the view's package under a pack-and-skill-qualified name, never by
    putting `scripts/` on `sys.path`: one bare name would otherwise bind to
    whichever pack's directory landed first. Red today - the skill does not
    exist, so there is no `__init__.py` to load."""
    spec = importlib.util.spec_from_file_location(
        _VIEW_NAME, _VIEW_PKG / "__init__.py",
        submodule_search_locations=[str(_VIEW_PKG)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(_VIEW_NAME)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return importlib.import_module(f"{_VIEW_NAME}.{submodule}")


FLOW_MOMENT = "2026-09-24T11:30:00Z"
JIRA_MOMENT = "2026-09-24T11:30:12Z"
WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}

# The Jira-side half of the read that also supplies the parent links. A
# per-issue row carries no status-category timestamp and no flagged field, so
# age, blocked and since-when are unreachable without this input.
JIRA_STATE = {
    "PROJ-1": {"status_category": "Done", "status_category_changed_at": "2026-08-06T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
    "PROJ-2": {"status_category": "Done", "status_category_changed_at": "2026-08-20T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
    "PROJ-3": {"status_category": "In Progress", "status_category_changed_at": "2026-09-10T09:00:00+00:00", "flagged": True, "flagged_changed_at": "2026-09-12T09:00:00+00:00"},
    "PROJ-4": {"status_category": "Done", "status_category_changed_at": "2026-09-01T09:00:00+00:00", "flagged": False, "flagged_changed_at": None},
}


@pytest.fixture
def view():
    return _load_view_submodule("view")


def _row(key, *, delivered, wip, cycle_hours, bucket="feature"):
    """One flow-metrics per-issue row, exact wire fields."""
    return {
        "key": key,
        "issue_created": "2026-08-01T09:00:00+00:00",
        "first_commitment_at": "2026-08-02T09:00:00+00:00",
        "first_delivery_at": "2026-08-06T09:00:00+00:00" if delivered else None,
        "cycle_eligible": delivered,
        "cycle_time_hours": cycle_hours,
        "lead_time_hours": cycle_hours,
        "flow_efficiency": 0.5,
        "rework_count": 0,
        "issuetype_at_delivery": "Story",
        "issuetype_bucket": bucket,
        "team": "Atlas",
        "delivered_in_window": delivered,
        "cancelled_in_window": False,
        "wip_at_to": wip,
    }


@pytest.fixture
def per_issue_rows():
    return [
        _row("PROJ-1", delivered=True, wip=False, cycle_hours=96.0),
        _row("PROJ-2", delivered=True, wip=False, cycle_hours=12.0),
        _row("PROJ-3", delivered=False, wip=True, cycle_hours=None),
        # Delivered, but a subtask: flow-metrics excludes it from throughput
        # unless --include-subtasks is set, so the view must too.
        _row("PROJ-4", delivered=True, wip=False, cycle_hours=8.0, bucket="subtask"),
    ]


@pytest.fixture
def parents():
    """The view's own parent-link read, resolved to the Epic rung.

    Jira Software nests Epic > Story > Subtask, so a subtask's immediate
    parent is a Story and reaching its Epic takes two hops. This mapping is
    the resolved result the view supplies: issue key to Epic key, whatever
    the depth. PROJ-4 is a subtask of PROJ-1 and resolves to the same Epic.
    """
    return {
        "PROJ-1": "PROJ-100",
        "PROJ-2": "PROJ-100",
        "PROJ-3": "PROJ-100",
        "PROJ-4": "PROJ-100",
    }


def _build(view, rows, parents, outcomes, include_subtasks=False):
    return view.build_epic_rows(
        per_issue_rows=rows,
        parents=parents,
        jira_state=JIRA_STATE,
        outcomes=outcomes,
        include_subtasks=include_subtasks,
        window=WINDOW,
        flow_taken_at=FLOW_MOMENT,
        jira_taken_at=JIRA_MOMENT,
    )


# STUB: AC1
def test_each_epic_carries_a_delivery_reading_and_an_outcome_position(
    view, per_issue_rows, parents
):
    """An Epic with no outcome still carries the position — absent is an
    answer, not an omission."""
    rows = _build(view, per_issue_rows, parents, {"PROJ-100": None})

    assert len(rows) == 1
    assert rows[0]["epic"] == "PROJ-100"
    assert "delivery" in rows[0]
    assert rows[0]["outcome"]["recorded"] is False


# STUB: AC2
def test_flow_figures_are_counts_over_flow_metrics_rows(view, per_issue_rows, parents):
    """Composition, not recomputation: throughput is the count of rows
    flow-metrics marked delivered_in_window whose bucket is not subtask, and
    work in flight the count it marked wip_at_to."""
    delivery = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]["delivery"]

    assert delivery["throughput"]["count"] == 2
    assert delivery["work_in_flight"] == 1


# STUB: AC3
def test_a_delivered_subtask_does_not_raise_throughput(view, per_issue_rows, parents):
    """flow-metrics counts throughput as delivered-in-window AND not a subtask
    bucket, unless --include-subtasks. Counting every delivered row would
    report 3 here and publish a larger number under the same name."""
    delivery = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]["delivery"]

    assert delivery["throughput"]["count"] == 2


# STUB: AC3
def test_include_subtasks_counts_the_delivered_subtask(view, per_issue_rows, parents):
    """The other side of the same rule: with the flag set, flow-metrics counts
    the subtask, so the view must report 3 rather than holding 2 fixed."""
    delivery = _build(
        view, per_issue_rows, parents, {"PROJ-100": None}, include_subtasks=True
    )[0]["delivery"]

    assert delivery["throughput"]["count"] == 3


# STUB: AC6
def test_an_unresolved_parent_chain_is_rendered_not_dropped(view, per_issue_rows, parents):
    """A chain that never reaches an in-scope Epic must still surface its
    issue and the reason, and must not withhold the rest of the view."""
    orphaned = {k: v for k, v in parents.items() if k != "PROJ-2"}

    rows = _build(view, per_issue_rows, orphaned, {"PROJ-100": None})

    groups = {r["epic"]: r for r in rows}
    # PROJ-2 alone is unresolvable; the other three still group normally, so
    # the partial answer survives rather than the whole view being withheld.
    assert set(groups) == {"PROJ-100", "unattributed"}
    unattributed = groups["unattributed"]
    # The reason is carried per issue, not once for the group: two issues can
    # end for different reasons, and one group-level string cannot say so.
    assert "PROJ-2" in unattributed["issues"]
    assert unattributed["issues"]["PROJ-2"]["reason"]


# STUB: AC5
def test_rows_are_grouped_to_epics_by_the_parent_link(view, per_issue_rows):
    """The join comes from the view's own read; a per-issue row has no Epic
    field, so two parents must produce two Epic rows from the same input."""
    split = {
        "PROJ-1": "PROJ-100",
        "PROJ-2": "PROJ-200",
        "PROJ-3": "PROJ-200",
        "PROJ-4": "PROJ-100",
    }

    rows = _build(view, per_issue_rows, split, {"PROJ-100": None, "PROJ-200": None})

    by_epic = {r["epic"]: r for r in rows}
    # Every fixture row resolves here, so no unattributed group appears. The
    # sibling test omits one mapping on purpose and expects that group.
    assert set(by_epic) == {"PROJ-100", "PROJ-200"}
    assert by_epic["PROJ-100"]["delivery"]["throughput"]["count"] == 1
    assert by_epic["PROJ-200"]["delivery"]["throughput"]["count"] == 1


# STUB: AC54
def test_no_percentile_is_rendered(view, per_issue_rows, parents):
    """flow-metrics applies no sample-size threshold, so a p50 over two
    completions would reach a reader as fact. No derived duration may survive
    into the row at any depth."""
    rows = _build(view, per_issue_rows, parents, {"PROJ-100": None})

    serialized = json.dumps(rows)
    for marker in ("p50", "p75", "p90", "percentile", "cycle_time", "lead_time"):
        assert marker not in serialized


# STUB: AC55
def test_throughput_is_a_count_with_its_window(view, per_issue_rows, parents):
    """A bare count without its window is unreadable."""
    throughput = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0][
        "delivery"
    ]["throughput"]

    assert throughput["count"] == 2
    assert throughput["window"] == WINDOW


# STUB: AC9
def test_both_moments_are_stated_separately(view, per_issue_rows, parents):
    """Two passes over Jira. A single timestamp implying one atomic snapshot
    is the claim this pins against."""
    row = _build(view, per_issue_rows, parents, {"PROJ-100": None})[0]

    assert row["flow_taken_at"] == FLOW_MOMENT
    assert row["jira_taken_at"] == JIRA_MOMENT
