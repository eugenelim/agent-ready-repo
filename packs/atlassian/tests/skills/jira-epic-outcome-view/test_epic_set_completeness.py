"""Every Epic the credential can see reaches the rendered view.

Completeness is asserted by removal, never by presence. An omitted Epic
raises no error anywhere, so a presence assertion keeps passing while the
set silently shrinks -- and an Epic with no outcome contributes nothing
to a view trying to look complete, which makes it exactly the one an
implementation is tempted to drop.

The expected set is derived from the fully paginated Jira result for the
calling credential, through the same reader the view uses. A hand-written
fixture list would prove only that the fixture and the render agree.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

WINDOW_ARGS = ["--from", "2026-08-25", "--to", "2026-09-24"]

# Deliberately larger than the client's 50-issue page: a reader that
# stops at one page renders a smaller project than the credential can
# actually browse, and reports nothing wrong while doing it.
EPIC_COUNT = 120

_FIELD_CATALOGUE = [{"id": "customfield_10021", "name": "Flagged"}]


def _issues():
    """One project's worth of issues, as the paginated search returns them."""
    issues = []
    for index in range(1, EPIC_COUNT + 1):
        issues.append(
            {
                "key": f"PROJ-{index}",
                "fields": {
                    "issuetype": {"name": "Epic"},
                    "parent": None,
                    "status": {"statusCategory": {"name": "In Progress"}},
                    "statuscategorychangedate": "2026-09-01T09:00:00+00:00",
                    "description": (
                        f"Scope notes.\n\n## Outcome\nOutcome number {index}.\n"
                        if index % 2 == 0
                        else "Scope notes only, no heading here.\n"
                    ),
                },
            }
        )
    return issues


def _runner(seen):
    """Stands in for the Jira client, recording the argv it was handed."""

    def runner(argv, **_kwargs):
        seen.append(list(argv))
        verb = argv[2]
        payload = _FIELD_CATALOGUE if verb == "raw" else _issues()
        return SimpleNamespace(
            returncode=0, stdout=json.dumps(payload).encode("utf-8"), stderr=b""
        )

    return runner


@pytest.fixture
def jira_read(load_module):
    return load_module("jira_read")


@pytest.fixture
def real_read_scope(jira_read):
    """The unpatched reader, captured before the CLI fixture wraps it."""
    return jira_read.read_scope


@pytest.fixture
def scope_argv():
    return []


@pytest.fixture
def cli(load_module, tmp_path, monkeypatch, real_read_scope, scope_argv):
    """The CLI with the Jira client and the flow reading behind seams.

    The Jira half runs the real reader over a recorded transport, because
    the Epic set has to come from that read rather than from the test.
    """
    module = load_module("")
    runner = _runner(scope_argv)
    monkeypatch.setattr(module, "resolve_jira_script", lambda: tmp_path / "jira.py")
    monkeypatch.setattr(module, "resolve_flow_scripts_dir", lambda: tmp_path / "scripts")
    monkeypatch.setattr(
        module.jira_read,
        "read_scope",
        lambda **kwargs: real_read_scope(**kwargs, runner=runner),
    )
    monkeypatch.setattr(module.flow, "run_flow_metrics", lambda **_kwargs: [])
    return module


def _expected_epics(real_read_scope, tmp_path):
    """The Epic set, derived from the fully paginated Jira result."""
    scope = real_read_scope(
        script=tmp_path / "jira.py", project="PROJ", runner=_runner([])
    )
    return set(scope["epic_keys"])


def _rendered_epics(document):
    return {row["epic"] for row in document["epics"] if not row.get("unattributed")}


def test_the_expected_set_is_the_whole_paginated_result(
    jira_read, tmp_path, scope_argv
):
    """Derived from what Jira returned for this credential, and nothing
    narrows it on the way: no argument capping the result is passed, so
    the client paginates to exhaustion as it does by default."""
    scope = jira_read.read_scope(
        script=tmp_path / "jira.py", project="PROJ", runner=_runner(scope_argv)
    )

    assert len(scope["epic_keys"]) == EPIC_COUNT
    search_argv = next(argv for argv in scope_argv if argv[2] == "search")
    assert "--limit" not in search_argv


def test_the_rendered_set_equals_the_expected_set_exactly(
    cli, real_read_scope, tmp_path
):
    """Exact equality, both directions: nothing dropped and nothing added."""
    document = cli.render(
        project="PROJ",
        window={"from": "2026-08-25", "to": "2026-09-24"},
        include_subtasks=False,
        jql=None,
        jira_script=tmp_path / "jira.py",
        flow_scripts_dir=tmp_path / "scripts",
    )

    assert _rendered_epics(document) == _expected_epics(real_read_scope, tmp_path)


def test_dropping_any_single_epic_fails_the_check(
    cli, real_read_scope, tmp_path, monkeypatch
):
    """The removal control, run for every member of the expected set.

    Each Epic is dropped at the point the rows are built -- after the
    read, before the render -- which is where a real omission would
    happen. A control that only removed a member from a local copy would
    be checking the assertion, not the view."""
    expected = _expected_epics(real_read_scope, tmp_path)
    build_rows = cli.view.build_epic_rows

    def render_dropping(dropped):
        def dropping(**kwargs):
            return [
                row for row in build_rows(**kwargs) if row.get("epic") != dropped
            ]

        monkeypatch.setattr(cli.view, "build_epic_rows", dropping)
        try:
            return cli.render(
                project="PROJ",
                window={"from": "2026-08-25", "to": "2026-09-24"},
                include_subtasks=False,
                jql=None,
                jira_script=tmp_path / "jira.py",
                flow_scripts_dir=tmp_path / "scripts",
            )
        finally:
            monkeypatch.setattr(cli.view, "build_epic_rows", build_rows)

    for member in sorted(expected):
        rendered = _rendered_epics(render_dropping(member))
        assert rendered != expected, f"dropping {member} went unnoticed"
        assert member not in rendered


@pytest.mark.parametrize("answers", [None, ["PROJ-2=Customers self-serve returns."]])
def test_every_run_states_what_the_credential_can_browse(
    cli, tmp_path, answers
):
    """Unconditional, on every run. Jira omits an issue this credential
    cannot browse with no signal that it did, and both sets compared
    above are drawn from that same query -- so nothing upstream could
    trigger this disclosure and it cannot be inferred from equality."""
    document = cli.render(
        project="PROJ",
        window={"from": "2026-08-25", "to": "2026-09-24"},
        include_subtasks=False,
        jql=None,
        jira_script=tmp_path / "jira.py",
        flow_scripts_dir=tmp_path / "scripts",
        outcome_answers=answers,
    )

    coverage = document["coverage"]
    assert coverage.strip() != ""
    assert "browse" in coverage.lower()


def test_the_disclosure_survives_an_empty_scope(cli, tmp_path, monkeypatch):
    """A project with no Epics at all still states its coverage. That is
    the run where a triggered disclosure would fall silent, and it is
    also the run where a reader most needs to know the set may be
    incomplete."""
    monkeypatch.setattr(
        cli.jira_read,
        "read_scope",
        lambda **_kwargs: {
            "epic_keys": [],
            "descriptions": {},
            "parent_links": {},
            "jira_state": {},
            "flagged_field": None,
            "taken_at": "2026-09-24T11:30:12Z",
        },
    )

    document = cli.render(
        project="PROJ",
        window={"from": "2026-08-25", "to": "2026-09-24"},
        include_subtasks=False,
        jql=None,
        jira_script=tmp_path / "jira.py",
        flow_scripts_dir=tmp_path / "scripts",
    )

    assert document["epics"] == []
    assert document["coverage"].strip() != ""
