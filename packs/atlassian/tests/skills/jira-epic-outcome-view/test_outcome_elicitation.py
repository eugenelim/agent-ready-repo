"""Asking for an outcome, taking the answer, and never writing one.

Both directions are asserted. Only checking the declining case would
pass a design that prints a prompt and has no way to accept an answer,
which is the failure mode of every "we asked the team" feature that
nobody answers twice.
"""
from __future__ import annotations

import json

import pytest

WINDOW_ARGS = ["--from", "2026-08-25", "--to", "2026-09-24"]

RECORDED_TEXT = "Customers resolve a return without contacting support."
STATED_TEXT = "Fewer returns reach a human at all."

_SCOPE = {
    "epic_keys": ["PROJ-100", "PROJ-200"],
    "descriptions": {
        # Server/DC shape, no Outcome heading anywhere in it.
        "PROJ-100": "Build the new returns flow.\n\n## Scope\nSelf-serve only.\n",
        # Cloud shape, with one recorded.
        "PROJ-200": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Outcome"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": RECORDED_TEXT}],
                },
            ],
        },
    },
    "parent_links": {"PROJ-100": None, "PROJ-200": None},
    "jira_state": {},
    "flagged_field": None,
    "taken_at": "2026-09-24T11:30:12Z",
}


@pytest.fixture
def outcome(load_module):
    return load_module("outcome")


@pytest.fixture
def view(load_module):
    return load_module("view")


@pytest.fixture
def cli(load_module, tmp_path, monkeypatch):
    """The CLI with both upstream seams stubbed: the elicitation surface
    is what is under test, not whether a sibling skill is installed."""
    module = load_module("")
    monkeypatch.setattr(module, "resolve_jira_script", lambda: tmp_path / "jira.py")
    monkeypatch.setattr(module, "resolve_flow_scripts_dir", lambda: tmp_path / "scripts")
    monkeypatch.setattr(module.jira_read, "read_scope", lambda **_kwargs: dict(_SCOPE))
    monkeypatch.setattr(module.flow, "run_flow_metrics", lambda **_kwargs: [])
    return module


def _run(cli, capsys, *extra):
    code = cli.main(["--project", "PROJ", *WINDOW_ARGS, *extra])
    captured = capsys.readouterr()
    return code, captured


def _positions(captured):
    document = json.loads(captured.out)
    return {row["epic"]: row["outcome"] for row in document["epics"]}


def test_a_stated_outcome_comes_back_as_paste_ready_text(cli, capsys, outcome):
    """The team's exact words, and the location to put them in. A view
    that accepted the answer and paraphrased it would be authoring."""
    code, captured = _run(cli, capsys, "--outcome", f"PROJ-100={STATED_TEXT}")

    assert code == 0
    position = _positions(captured)["PROJ-100"]
    assert STATED_TEXT in position["paste_ready"]
    assert outcome.OUTCOME_LOCATION in position["paste_ready"]
    assert position["prompt"] is None
    # Still not recorded: the team has not pasted it into Jira yet, and
    # this view will not do that for them.
    assert position["recorded"] is False


def test_a_declined_prompt_renders_no_paste_ready_text(cli, capsys, outcome):
    """The other direction. The Epic still appears, with its explicit
    nothing, because an Epic with no outcome is the one a view trying to
    look complete would drop."""
    code, captured = _run(cli, capsys)

    assert code == 0
    position = _positions(captured)["PROJ-100"]
    assert position["paste_ready"] is None
    assert position["prompt"].strip() != ""
    assert outcome.OUTCOME_LOCATION in position["prompt"]
    assert position["recorded"] is False
    assert position["statement"].strip() != ""


def test_empty_text_is_a_decline_and_not_an_error(cli, capsys, outcome):
    """`--outcome PROJ-100=` matches leaving the flag off entirely. The
    decline is asserted where it is decided as well as where it shows:
    an empty answer that survived parsing would be indistinguishable
    downstream from a decline, and the next change to the row builder
    would be the one that rendered it."""
    assert outcome.parse_answers(["PROJ-100="], epic_keys={"PROJ-100"}) == {}

    code, captured = _run(cli, capsys, "--outcome", "PROJ-100=")

    assert code == 0
    position = _positions(captured)["PROJ-100"]
    assert position["paste_ready"] is None
    assert position["prompt"].strip() != ""


def test_a_key_outside_the_scope_is_refused_by_name(cli, capsys):
    """Rendering nothing for a key the team answered would lose the words
    they just typed, with no sign that anything went missing."""
    code, captured = _run(cli, capsys, "--outcome", f"PROJ-999={STATED_TEXT}")

    assert code != 0
    assert "PROJ-999" in captured.err
    assert captured.out == ""


def test_the_same_key_given_twice_is_refused_by_name(cli, capsys):
    """Keeping the first or the last answer would discard one of two."""
    code, captured = _run(
        cli, capsys,
        "--outcome", f"PROJ-100={STATED_TEXT}",
        "--outcome", "PROJ-100=Something else entirely.",
    )

    assert code != 0
    assert "PROJ-100" in captured.err
    assert captured.out == ""


def test_a_scaffold_with_no_team_input_is_never_labelled_paste_ready(cli, capsys):
    """"Paste-ready" means the team's substance. Handing a team its own
    boilerplate back under that label teaches it that the label means
    nothing."""
    _code, captured = _run(cli, capsys)

    position = _positions(captured)["PROJ-100"]
    assert position["paste_ready"] is None
    assert "paste" not in position["prompt"].lower()


def test_the_view_supplies_no_outcome_substance_of_its_own(view):
    """Two Epics with different keys and different delivery data. With
    nothing recorded and nothing stated, their outcome positions have to
    be the same fixed scaffold: any wording that varied with the Epic
    would be substance this view invented, which the guardrail makes
    non-waivable."""
    rows = view.build_epic_rows(
        per_issue_rows=[
            {"key": "PROJ-1", "issuetype_bucket": "feature",
             "delivered_in_window": True, "wip_at_to": False},
            {"key": "PROJ-2", "issuetype_bucket": "defect",
             "delivered_in_window": False, "wip_at_to": True},
        ],
        parents={"PROJ-1": "PROJ-100", "PROJ-2": "PROJ-200"},
        jira_state={
            "PROJ-2": {
                "status_category": "In Progress",
                "status_category_changed_at": "2026-09-01T09:00:00+00:00",
                "flagged": False,
                "flagged_changed_at": None,
            }
        },
        outcomes={"PROJ-100": None, "PROJ-200": None},
        window={"from": "2026-08-25", "to": "2026-09-24"},
        flow_taken_at="2026-09-24T11:30:00Z",
        jira_taken_at="2026-09-24T11:30:12Z",
    )

    positions = {row["epic"]: row["outcome"] for row in rows}
    first, second = positions["PROJ-100"], positions["PROJ-200"]

    assert first == second, "the outcome position varied with the Epic's own data"
    assert first["text"] is None
    assert first["paste_ready"] is None
    # Nor may it name the Epic. A statement written around the key reads
    # as something said about that Epic, and one Epic is all it takes.
    for epic, position in positions.items():
        rendered = " ".join(
            value for value in position.values() if isinstance(value, str)
        )
        assert epic not in rendered


def test_a_recorded_outcome_is_rendered_and_left_unassessed(cli, capsys):
    """The guard on the no-assessment check. That check scans the
    rendered document for assessment words, so it passes trivially while
    no outcome text is rendered at all -- this asserts the text is
    actually there, which is what makes the scan discriminate."""
    _code, captured = _run(cli, capsys)

    rendered = json.loads(captured.out)
    row = next(row for row in rendered["epics"] if row["epic"] == "PROJ-200")

    assert row["outcome"]["recorded"] is True
    assert row["outcome"]["text"] == RECORDED_TEXT
    assert RECORDED_TEXT in captured.out
    for marker in ("score", "grade", "rating", "judgement", "judgment"):
        assert marker not in captured.out.lower()


def test_the_location_is_fixed_and_not_configurable_per_invocation(cli, pack_root):
    """Documented in one place a team can follow without reading code,
    and with no flag that would let two teams read the same view from two
    different locations."""
    options = {
        option
        for action in cli.build_parser()._actions
        for option in action.option_strings
    }
    assert options == {
        "-h", "--help", "--project", "--from", "--to",
        "--include-subtasks", "--jql", "--outcome",
    }

    # Whitespace-normalised: the documentation is hard-wrapped, so a
    # sentence the reader sees as one line is two in the file.
    skill_md = " ".join(
        (
            pack_root / ".apm" / "skills" / "jira-epic-outcome-view" / "SKILL.md"
        ).read_text(encoding="utf-8").split()
    )
    assert "`description`" in skill_md
    assert "`Outcome` heading" in skill_md
    assert "not configurable per invocation" in skill_md
    assert "--outcome EPIC-KEY=<text>" in skill_md
