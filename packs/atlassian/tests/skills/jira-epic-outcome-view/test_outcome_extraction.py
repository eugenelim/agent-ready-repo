# Stored and validated in PLAN's T2 Tests: subsection. Each test carries its
# own marker and pins one criterion. These are full assertions: the criteria
# pin the behaviour exactly, so nothing here is a shape placeholder. The
# Epic-set and elicitation criteria are not stubbed here — see T2's `no stub`
# dispositions.
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


@pytest.fixture
def outcome():
    return _load_view_submodule("outcome")


def _adf(*nodes: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(nodes)}


def _heading(text: str) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": text}],
    }


def _para(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


# STUB: AC12
def test_reads_the_block_under_the_heading_from_server_plain_text(outcome):
    """Server/DC REST v2 shape: description is plain text."""
    description = (
        "Build the new returns flow for self-serve customers.\n"
        "\n"
        "## Outcome\n"
        "Customers resolve a return without contacting support.\n"
    )

    assert (
        outcome.extract_outcome(description)
        == "Customers resolve a return without contacting support."
    )


# STUB: AC12
def test_reads_the_block_under_the_heading_from_cloud_adf(outcome):
    """Cloud REST v3 shape: description is an ADF document. A reader that
    handles only plain text returns nothing here, which is indistinguishable
    from an Epic with no outcome — the failure this pins."""
    description = _adf(
        _para("Build the new returns flow for self-serve customers."),
        _heading("Outcome"),
        _para("Customers resolve a return without contacting support."),
    )

    assert (
        outcome.extract_outcome(description)
        == "Customers resolve a return without contacting support."
    )


# STUB: AC16
def test_text_outside_the_block_is_not_returned_as_the_outcome(outcome):
    """The description is shared with scope and acceptance criteria, so
    verbatim reproduction is scoped to the block, not the whole field."""
    description = (
        "Scope: self-serve only.\n"
        "\n"
        "## Outcome\n"
        "Customers resolve a return without contacting support.\n"
        "\n"
        "## Acceptance criteria\n"
        "- Returns portal ships.\n"
    )

    extracted = outcome.extract_outcome(description)

    assert extracted == "Customers resolve a return without contacting support."
    assert "Scope: self-serve only." not in extracted
    assert "Returns portal ships." not in extracted


@pytest.mark.parametrize(
    "description",
    [
        pytest.param(
            "Build the new returns flow.\n\n## Scope\nSelf-serve only.\n",
            id="heading-absent-plain-text",
        ),
        pytest.param(
            "Build the new returns flow.\n\n## Outcome\n\n## Scope\nSelf-serve.\n",
            id="heading-present-but-empty-plain-text",
        ),
        pytest.param(
            _adf(_para("Build the new returns flow.")),
            id="heading-absent-adf",
        ),
        pytest.param(
            _adf(_heading("Outcome"), _heading("Scope"), _para("Self-serve.")),
            id="heading-present-but-empty-adf",
        ),
        pytest.param(None, id="description-null"),
    ],
)
# STUB: AC15
def test_absent_or_empty_block_is_no_outcome_recorded(outcome, description):
    """A missing heading and a present-but-empty heading are the same
    answer to the reader. Treating only the first as absent renders a blank
    for the second, which is the failure the absent-outcome path exists to
    prevent."""
    assert outcome.extract_outcome(description) is None


# The three tests below assert the row builder rather than the extractor,
# which is why they sit alongside the extraction tests in the same task.
@pytest.fixture
def view():
    return _load_view_submodule("view")


# One contract, shared with T1: per-issue rows in flow-metrics' wire shape, the
# view's own parent-link read, and the two moments stated separately. An
# earlier draft called this with an Epic-keyed aggregate that flow-metrics does
# not emit, which would have pinned two incompatible signatures for one
# function.
def _rows(view, outcome_text):
    return view.build_epic_rows(
        per_issue_rows=[
            {
                "key": "PROJ-1",
                "issue_created": "2026-08-01T09:00:00+00:00",
                "first_commitment_at": "2026-08-02T09:00:00+00:00",
                "first_delivery_at": "2026-08-06T09:00:00+00:00",
                "cycle_eligible": True,
                "cycle_time_hours": 96.0,
                "lead_time_hours": 96.0,
                "flow_efficiency": 0.5,
                "rework_count": 0,
                "issuetype_at_delivery": "Story",
                "issuetype_bucket": "feature",
                "team": "Atlas",
                "delivered_in_window": True,
                "cancelled_in_window": False,
                "wip_at_to": False,
            }
        ],
        parents={"PROJ-1": "PROJ-100"},
        jira_state={"PROJ-1": {"status_category": "Done", "status_category_changed_at": "2026-08-06T09:00:00+00:00", "flagged": False, "flagged_changed_at": None}},
        outcomes={"PROJ-100": outcome_text},
        window={"from": "2026-08-25", "to": "2026-09-24"},
        flow_taken_at="2026-09-24T11:30:00Z",
        jira_taken_at="2026-09-24T11:30:12Z",
    )


# STUB: AC21
def test_outcome_less_epic_renders_an_explicit_nothing(view):
    """An explicit statement that none is recorded, not a blank and not
    an omitted row."""
    row = _rows(view, None)[0]

    assert row["outcome"]["recorded"] is False
    assert row["outcome"]["statement"].strip() != ""


# STUB: AC22
def test_outcome_less_epic_also_renders_a_prompt(view):
    """The prompt names the location to write the outcome into."""
    row = _rows(view, None)[0]

    prompt = row["outcome"]["prompt"]
    assert prompt.strip() != ""
    assert "Outcome" in prompt
    assert "description" in prompt.lower()


# STUB: AC26
def test_no_score_grade_or_judgement_is_rendered(view):
    """The view reports the outcome, it does not assess it."""
    serialized = json.dumps(_rows(view, "Customers resolve a return."))

    for marker in ("score", "grade", "rating", "judgement", "judgment"):
        assert marker not in serialized.lower()
