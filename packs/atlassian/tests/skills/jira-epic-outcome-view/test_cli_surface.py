"""The out-of-process surface: exit codes, stdout shape, stream encoding.

These are the promises a caller outside this process can see. They are
asserted here rather than inferred from the row builder, because an exit
code and a stdout document are not return values.
"""
from __future__ import annotations

import json
import sys

import pytest

WINDOW_ARGS = ["--from", "2026-08-25", "--to", "2026-09-24"]

_SCOPE = {
    "epic_keys": ["PROJ-100"],
    "parent_links": {"PROJ-1": "PROJ-100", "PROJ-100": None},
    "jira_state": {
        "PROJ-1": {
            "status_category": "Done",
            "status_category_changed_at": "2026-09-10T09:00:00+00:00",
            "flagged": False,
            "flagged_changed_at": None,
        }
    },
    "flagged_field": "customfield_10021",
    "taken_at": "2026-09-24T11:30:12Z",
}

_ROWS = [
    {
        "key": "PROJ-1",
        "issuetype_bucket": "feature",
        "delivered_in_window": True,
        "wip_at_to": False,
    }
]


@pytest.fixture
def cli(load_module, tmp_path, monkeypatch):
    """The CLI package with both upstream seams stubbed.

    Discovery is replaced too: the exit-code contract is what is under
    test, not whether a sibling skill happens to be installed here.
    """
    module = load_module("")
    monkeypatch.setattr(module, "resolve_jira_script", lambda: tmp_path / "jira.py")
    monkeypatch.setattr(module, "resolve_flow_scripts_dir", lambda: tmp_path / "scripts")
    monkeypatch.setattr(module.jira_read, "read_scope", lambda **_kwargs: dict(_SCOPE))
    monkeypatch.setattr(module.flow, "run_flow_metrics", lambda **_kwargs: list(_ROWS))
    return module


def test_a_successful_run_exits_zero_and_prints_one_json_document(cli, capsys):
    """Stdout is a single parseable document, not a log with a payload in it."""
    code = cli.main(["--project", "PROJ", *WINDOW_ARGS])

    assert code == 0
    document = json.loads(capsys.readouterr().out)
    assert document["project"] == "PROJ"
    assert document["window"] == {"from": "2026-08-25", "to": "2026-09-24"}
    assert document["flow_taken_at"] != document["jira_taken_at"]
    assert document["coverage"].strip() != ""
    assert [row["epic"] for row in document["epics"]] == ["PROJ-100"]
    assert document["epics"][0]["delivery"]["throughput"]["count"] == 1


def test_a_missing_scope_is_an_argparse_refusal(cli, monkeypatch):
    """Exit 2 for a usage error, from argparse itself -- and onto a stream
    already reconfigured. Argparse is the first thing in the process that
    can print, so it is the case that decides whether the reconfigure ran
    early enough to matter."""
    err = _Stream()
    monkeypatch.setattr(sys, "stderr", err)

    with pytest.raises(SystemExit) as excinfo:
        cli.main([])

    assert excinfo.value.code == 2
    assert err.events[0] == ("reconfigure", "utf-8")
    assert any(kind == "write" for kind, _ in err.events)


def test_an_unusable_window_exits_two_and_names_the_problem(cli, capsys):
    """A validation failure is exit 2 and says what was wrong on stderr."""
    code = cli.main(["--project", "PROJ", "--from", "2026-09-24", "--to", "2026-08-25"])

    assert code == 2
    assert "after window end" in capsys.readouterr().err


def test_an_upstream_failure_exits_three_rather_than_rendering_an_empty_scope(
    cli, capsys, monkeypatch
):
    """"Could not reach Jira" is not "this project has no Epics". Exit 0
    with an empty view would tell a reader the second."""
    def boom(**_kwargs):
        raise cli.jira_read.JiraReadError("jira search failed (exit 2)")

    monkeypatch.setattr(cli.jira_read, "read_scope", boom)

    code = cli.main(["--project", "PROJ", *WINDOW_ARGS])

    assert code == 3
    assert "jira search failed" in capsys.readouterr().err


class _Stream:
    """A stream that records reconfigure and write calls in order."""

    def __init__(self):
        self.events = []

    def reconfigure(self, **kwargs):
        self.events.append(("reconfigure", kwargs.get("encoding")))

    def write(self, text):
        self.events.append(("write", text))
        return len(text)

    def flush(self):
        return None


def test_both_streams_are_reconfigured_to_utf8_before_the_first_write(
    cli, monkeypatch
):
    """Jira text carries non-ASCII routinely. A stream reconfigured after
    the first write raises partway through a render, leaving half a view
    on stdout -- so the ordering is what is asserted, not the call."""
    out, err = _Stream(), _Stream()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    cli.main(["--project", "PROJ", *WINDOW_ARGS])

    for stream in (out, err):
        assert stream.events, "stream saw no events at all"
        assert stream.events[0] == ("reconfigure", "utf-8")
    assert any(kind == "write" for kind, _ in out.events)
