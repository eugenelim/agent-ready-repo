"""Read the Jira half of the view: the Epic set, parent links and state.

This is the pass the parent links and the state observations both come
from, which is why it states one moment for all of them. Only read verbs
reach the client, and only ``GET`` reaches the escape hatch: this view
writes nothing to Jira, including a comment, a label, a transition or a
field edit.
"""
from __future__ import annotations

import json
import os
import re
import subprocess  # noqa: S404 -- list-form only, never shell=True
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from . import state

#: Read verbs this view is allowed to ask the Jira client for. The list is
#: an allowlist rather than a denylist of write verbs: a verb added to the
#: client later is refused here until it is considered, which is the safe
#: direction for a guarantee that cannot be re-checked at run time.
READ_VERBS = frozenset({"check", "whoami", "get-issue", "search", "get-project"})

#: The field catalogue path, the only raw request this view makes. It is
#: how the flagged field is located: which field carries it varies by
#: instance, and on some instances it does not exist at all.
FIELD_CATALOGUE_PATH = "field"

#: Jira's own name for the flagged field on instances that have it.
FLAGGED_FIELD_NAME = "flagged"

# ``description`` is asked for on the same pass because it is where an
# Epic's outcome lives; a second search for it would state a second
# moment for a reading the view presents as one Jira pass.
_SEARCH_FIELDS = "parent,status,statuscategorychangedate,description,issuetype"
_EPIC_ISSUETYPE = "Epic"

# A Jira project key: a letter, then letters, digits or underscores. The
# scope's whole JQL is built around this value, so it is matched against
# the shape rather than escaped -- a value carrying a double quote would
# otherwise close the literal and change which issues the Epic set, the
# parent links and every description are read from, while the view went
# on rendering the caller's own string as the project.
_PROJECT_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,254}$")


class JiraReadError(Exception):
    """The Jira client refused, failed, or returned an unreadable payload."""


class ProjectKeyRefused(Exception):
    """A ``--project`` value that is not a Jira project key. Exit 2.

    Raised before the JQL is built, so the refusal is structural rather
    than a promise about what the caller passes.
    """


class WriteVerbRefused(Exception):
    """A verb outside the read allowlist was requested.

    Raised before any subprocess starts, so the refusal is structural
    rather than a promise about what the caller passes.
    """


def validate_project_key(project: str) -> str:
    """The project key, or a refusal. Nothing is escaped or rewritten."""
    if not _PROJECT_KEY.match(project or ""):
        raise ProjectKeyRefused(
            f"--project expects a Jira project key -- a letter followed by "
            f"letters, digits or underscores -- and got {project!r}"
        )
    return project


def run_jira(
    *,
    script: Path,
    verb: str,
    args: Sequence[str] = (),
    runner: Callable[..., Any] = subprocess.run,
) -> Any:
    """Invoke one read verb on the Jira client and parse its JSON stdout."""
    if verb == "raw":
        if not args or args[0] != "GET":
            raise WriteVerbRefused("only `raw GET` is permitted from this view")
    elif verb not in READ_VERBS:
        raise WriteVerbRefused(f"verb {verb!r} is not a read verb this view may issue")

    argv = [sys.executable, str(script), verb, *args]
    # Bytecode caching would write `__pycache__` beside the client's own
    # sources, inside the installed pack tree this view leaves unchanged.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = runner(argv, env=env, capture_output=True)
    returncode = getattr(completed, "returncode", 0)
    stdout = getattr(completed, "stdout", b"") or b""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if returncode != 0:
        stderr = getattr(completed, "stderr", b"") or b""
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise JiraReadError(f"jira {verb} failed (exit {returncode}): {stderr.strip()}")
    if not stdout.strip():
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise JiraReadError(f"jira {verb} returned unreadable output: {exc}") from exc


def resolve_flagged_field(
    *,
    script: Path,
    runner: Callable[..., Any] = subprocess.run,
) -> str | None:
    """The instance's flagged field id, or ``None`` when it has none.

    Resolved from the field catalogue rather than assumed: the field is a
    Jira Software addition with a per-instance id, and an instance without
    it must be reported as unreadable rather than as zero blocked work.
    """
    catalogue = run_jira(script=script, verb="raw", args=["GET", FIELD_CATALOGUE_PATH],
                         runner=runner)
    if not isinstance(catalogue, list):
        return None
    for field in catalogue:
        if not isinstance(field, Mapping):
            continue
        name = str(field.get("name") or "").strip().lower()
        if name == FLAGGED_FIELD_NAME:
            field_id = field.get("id") or field.get("key")
            return str(field_id) if field_id else None
    return None


def search(
    *,
    script: Path,
    jql: str,
    fields: str,
    runner: Callable[..., Any] = subprocess.run,
) -> list[dict[str, Any]]:
    """Fully paginated search. The client paginates to exhaustion by default."""
    payload = run_jira(
        script=script, verb="search", args=[jql, "--fields", fields], runner=runner
    )
    issues = payload.get("issues") if isinstance(payload, Mapping) else payload
    if not isinstance(issues, list):
        raise JiraReadError("jira search returned no issue list")
    return [issue for issue in issues if isinstance(issue, dict)]


def read_scope(
    *,
    script: Path,
    project: str,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """One Jira pass: the Epic set and descriptions, parent links, state.

    Returns the moment the pass was taken alongside its data, because the
    view states that moment separately from the flow reading's own.
    """
    validate_project_key(project)
    flagged_field = resolve_flagged_field(script=script, runner=runner)
    fields = _SEARCH_FIELDS if flagged_field is None else f"{_SEARCH_FIELDS},{flagged_field}"
    issues = search(
        script=script, jql=f'project = "{project}"', fields=fields, runner=runner
    )
    taken_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    epic_keys: list[str] = []
    descriptions: dict[str, Any] = {}
    parent_links: dict[str, str | None] = {}
    jira_state: dict[str, dict[str, Any]] = {}
    for issue in issues:
        key = str(issue.get("key") or "")
        if not key:
            continue
        issue_fields = issue.get("fields") or {}
        if _issuetype_name(issue_fields) == _EPIC_ISSUETYPE:
            epic_keys.append(key)
            # Kept raw, in whichever shape this deployment returned: a
            # structured document on Cloud, plain or wiki text on
            # Server. The outcome reader takes both; parsing here would
            # decide the shape question in the wrong module.
            descriptions[key] = issue_fields.get("description")
        parent = issue_fields.get("parent") or {}
        parent_links[key] = str(parent.get("key")) if parent.get("key") else None
        jira_state[key] = _state_record(issue_fields, flagged_field)

    if flagged_field is not None:
        for key, record in jira_state.items():
            if record.get("flagged"):
                record["flagged_changed_at"] = flagged_since(
                    script=script,
                    issue_key=key,
                    flagged_field=flagged_field,
                    runner=runner,
                )

    epic_keys.sort()
    return {
        "epic_keys": epic_keys,
        "descriptions": descriptions,
        "parent_links": parent_links,
        "jira_state": jira_state,
        "flagged_field": flagged_field,
        "taken_at": taken_at,
    }


def _issuetype_name(issue_fields: Mapping[str, Any]) -> str:
    issuetype = issue_fields.get("issuetype") or {}
    return str(issuetype.get("name") or "")


def flagged_since(
    *,
    script: Path,
    issue_key: str,
    flagged_field: str,
    runner: Callable[..., Any] = subprocess.run,
) -> str | None:
    """When the flag on this issue was last changed, from its change history.

    A search response carries no change history, so this is a second read
    and it is made only for issues that are actually flagged. Returning
    ``None`` means the history does not record the change -- a flag set
    before the instance kept history, for instance -- which the view
    reports as unknown rather than as "just now".
    """
    issue = run_jira(
        script=script,
        verb="get-issue",
        args=[issue_key, "--expand", "changelog"],
        runner=runner,
    )
    if not isinstance(issue, Mapping):
        return None
    histories = (issue.get("changelog") or {}).get("histories") or []
    # Compared as instants, never as strings. Jira renders `created` in
    # the requesting user's offset, so two entries either side of a
    # daylight-saving change order by their local clock faces under a
    # string comparison and the wrong one wins "last changed". The string
    # itself is what comes back, so the reported moment stays verbatim.
    latest: str | None = None
    latest_at: datetime | None = None
    for history in histories:
        if not isinstance(history, Mapping):
            continue
        created = history.get("created")
        if not created:
            continue
        for item in history.get("items") or []:
            if not isinstance(item, Mapping):
                continue
            # Cloud reports the change under the field's id, Server under
            # its name, so both are accepted.
            names = {flagged_field.lower(), FLAGGED_FIELD_NAME}
            changed_field = str(item.get("fieldId") or item.get("field") or "").lower()
            if changed_field not in names:
                continue
            created_at = state.parse_moment(str(created))
            if _is_later(created_at, latest_at, seen_any=latest is not None):
                latest, latest_at = str(created), created_at
    return latest


def _is_later(
    candidate: datetime | None, incumbent: datetime | None, *, seen_any: bool
) -> bool:
    """Whether ``candidate`` replaces ``incumbent`` as the latest change.

    An unreadable timestamp never displaces a readable one, and is kept
    only while nothing readable has been seen: reporting a moment the
    view could not parse is still better than reporting none at all.
    """
    if not seen_any:
        return True
    if candidate is None:
        return False
    if incumbent is None:
        return True
    return candidate > incumbent


def _state_record(
    issue_fields: Mapping[str, Any], flagged_field: str | None
) -> dict[str, Any]:
    """One issue's state, in the shape the row builder reads.

    ``flagged`` is ``None`` -- not ``False`` -- when the instance exposes
    no flagged field. That distinction is the whole point: ``False`` says
    "not blocked", ``None`` says "this instance cannot answer".
    """
    status = issue_fields.get("status") or {}
    category = status.get("statusCategory") or {}
    flagged: bool | None = None
    if flagged_field is not None:
        flagged = bool(issue_fields.get(flagged_field))
    return {
        "status_category": category.get("name"),
        "status_category_changed_at": issue_fields.get("statuscategorychangedate"),
        "flagged": flagged,
        # Filled in by a second, per-issue read for flagged issues only:
        # a search response carries no change history.
        "flagged_changed_at": None,
    }
