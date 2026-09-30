"""Locating the flagged field, and reading when it last changed.

Which field carries the flag varies by instance and some instances have
none at all, so both answers are read rather than assumed. The moment it
last changed is read from the issue's change history, where Jira renders
`created` in the requesting user's own offset -- which is why the entries
are compared as instants. Two entries either side of a daylight-saving
change order by their local clock faces under a string comparison, and
the earlier one wins "last changed".
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCRIPT = Path("/nonexistent/jira.py")
FLAGGED_ID = "customfield_10021"


@pytest.fixture
def jira_read(load_module):
    return load_module("jira_read")


class _Completed:
    def __init__(self, payload):
        self.returncode = 0
        self.stdout = json.dumps(payload).encode("utf-8")
        self.stderr = b""


def _runner(*, catalogue=None, issue=None):
    """Stand in for the Jira client at the process boundary."""

    def runner(argv, **_kwargs):
        verb = argv[2]
        if verb == "raw":
            return _Completed(catalogue)
        if verb == "get-issue":
            return _Completed(issue)
        raise AssertionError(f"unexpected verb {verb!r}")

    return runner


def _history(created: str, *, item: dict) -> dict:
    return {"created": created, "items": [item]}


def _changelog(*histories: dict) -> dict:
    return {"key": "PROJ-3", "changelog": {"histories": list(histories)}}


def test_the_flagged_field_is_resolved_from_the_catalogue(jira_read):
    """By name, case-insensitively: the id is per-instance, so hardcoding
    one reads a different field on the next instance."""
    catalogue = [
        {"id": "summary", "name": "Summary"},
        {"id": FLAGGED_ID, "name": "Flagged"},
    ]

    resolved = jira_read.resolve_flagged_field(
        script=SCRIPT, runner=_runner(catalogue=catalogue)
    )

    assert resolved == FLAGGED_ID


def test_an_instance_with_no_flagged_field_resolves_to_nothing(jira_read):
    """`None` is what makes the view say the instance cannot answer, rather
    than report zero blocked work. Those are different facts."""
    catalogue = [{"id": "summary", "name": "Summary"}]

    assert jira_read.resolve_flagged_field(
        script=SCRIPT, runner=_runner(catalogue=catalogue)
    ) is None


def test_an_unreadable_catalogue_resolves_to_nothing(jira_read):
    """An error payload is not a field list, and guessing an id from one
    would read some unrelated custom field as the flag."""
    assert jira_read.resolve_flagged_field(
        script=SCRIPT, runner=_runner(catalogue={"errorMessages": ["nope"]})
    ) is None


def test_the_cloud_field_id_spelling_is_recognised(jira_read):
    """Cloud reports the change under the field's id."""
    issue = _changelog(
        _history("2026-09-12T09:00:00.000+0000", item={"fieldId": FLAGGED_ID}),
    )

    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) == "2026-09-12T09:00:00.000+0000"


def test_the_server_field_name_spelling_is_recognised(jira_read):
    """Server reports it under the field's name. A reader that accepts only
    the Cloud spelling reports "unknown" on every Server instance."""
    issue = _changelog(
        _history("2026-09-12T09:00:00.000+0000", item={"field": "Flagged"}),
    )

    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) == "2026-09-12T09:00:00.000+0000"


def test_a_change_to_another_field_is_not_read_as_a_flag_change(jira_read):
    """Otherwise the last edit of any kind becomes "blocked since"."""
    issue = _changelog(
        _history("2026-09-12T09:00:00.000+0000", item={"field": "Sprint"}),
    )

    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) is None


def test_the_latest_change_is_chosen_by_instant_not_by_string(jira_read):
    """North America's autumn clock change: 01:15 at -05:00 is 06:15 UTC
    and happens after 01:30 at -04:00, which is 05:30 UTC. Comparing the
    strings picks the 01:30 entry, which is the earlier moment."""
    earlier_moment = "2026-11-01T01:30:00.000-0400"
    later_moment = "2026-11-01T01:15:00.000-0500"
    issue = _changelog(
        _history(later_moment, item={"field": "Flagged"}),
        _history(earlier_moment, item={"field": "Flagged"}),
    )

    assert earlier_moment > later_moment, "the fixture must discriminate"
    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) == later_moment


def test_the_moment_comes_back_exactly_as_jira_wrote_it(jira_read):
    """Parsed for the comparison, reported verbatim: the view states the
    moment Jira gave it, not a re-rendered one."""
    issue = _changelog(
        _history("2026-09-12T09:00:00.000+0530", item={"field": "Flagged"}),
    )

    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) == "2026-09-12T09:00:00.000+0530"


def test_an_unreadable_timestamp_does_not_displace_a_readable_one(jira_read):
    """A malformed entry must not win "last changed" by sorting high."""
    issue = _changelog(
        _history("not a timestamp", item={"field": "Flagged"}),
        _history("2026-09-12T09:00:00.000+0000", item={"field": "Flagged"}),
    )

    assert jira_read.flagged_since(
        script=SCRIPT, issue_key="PROJ-3", flagged_field=FLAGGED_ID,
        runner=_runner(issue=issue),
    ) == "2026-09-12T09:00:00.000+0000"
