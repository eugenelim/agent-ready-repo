"""`--project` is matched against the shape of a Jira project key.

The scope's whole JQL is built around that value. A value carrying a
double quote closes the literal and changes which issues the Epic set,
the parent links and every description are read from -- while the view
goes on rendering the caller's own string as `project`, so the document
says it describes a scope it never read. The refusal is structural: it
happens before the query is built and before any process starts, rather
than resting on what a caller passes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SCRIPT = Path("/nonexistent/jira.py")

_REFUSED = [
    pytest.param('PROJ" OR project = "OTHER', id="closes-the-jql-literal"),
    pytest.param("PROJ OR key > 0", id="spaces-and-operators"),
    pytest.param("", id="empty"),
    pytest.param("PROJ-1", id="an-issue-key-is-not-a-project-key"),
    pytest.param("'PROJ'", id="quoted"),
    pytest.param("1PROJ", id="leading-digit"),
]


@pytest.fixture
def jira_read(load_module):
    return load_module("jira_read")


@pytest.mark.parametrize("project", _REFUSED)
def test_a_value_that_is_not_a_project_key_is_refused(jira_read, project):
    with pytest.raises(jira_read.ProjectKeyRefused):
        jira_read.validate_project_key(project)


@pytest.mark.parametrize("project", ["PROJ", "AB", "proj", "A1_B2"])
def test_a_project_key_is_accepted(jira_read, project):
    """The refusal must not cost a reader a scope Jira would have served."""
    assert jira_read.validate_project_key(project) == project


def test_nothing_is_asked_of_jira_before_the_value_is_refused(jira_read):
    """Before the query is built means before the first spawn: a refusal
    that arrives after the search has run has already read the wrong
    scope."""

    def runner(argv, **_kwargs):
        raise AssertionError(f"the client was reached with {argv!r}")

    with pytest.raises(jira_read.ProjectKeyRefused):
        jira_read.read_scope(
            script=SCRIPT, project='PROJ" OR project = "OTHER', runner=runner
        )


def test_the_cli_refuses_the_value_with_exit_two(load_module, capsys):
    """Exit 2 is the documented usage-or-validation refusal, and the run
    reaches no upstream skill on the way to it."""
    cli = load_module("")

    code = cli.main(["--project", 'PROJ" OR project = "OTHER'])

    assert code == cli.EXIT_VALIDATION
    assert "project key" in capsys.readouterr().err
