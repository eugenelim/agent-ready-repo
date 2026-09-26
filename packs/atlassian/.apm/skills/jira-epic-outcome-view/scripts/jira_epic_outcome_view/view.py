"""Group a Jira scope's work by Epic and render each Epic's reading.

Every per-Epic delivery figure here is a count over rows the flow skill
already emitted. Nothing re-derives a duration: a second definition of a
flow metric inside one pack drifts against the first with nothing
comparing them, and no distribution is rendered at any depth, so a
figure over two completions can never reach a reader as a fact.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from . import outcome as outcome_reader
from . import state

#: The group that carries work whose parent chain never reached an
#: in-scope Epic. Dropping that work would silently shrink the reading.
UNATTRIBUTED = "unattributed"

#: The outcome position's three fixed strings. Each is the same for every
#: Epic, which is what keeps the view from authoring: an absence renders
#: a scaffold nobody could mistake for a team's words, and the only
#: Epic-specific text in the position is text the team itself supplied.
OUTCOME_RECORDED = "Recorded by the team in {location}."
OUTCOME_ABSENT = "No outcome is recorded for this Epic."
OUTCOME_PROMPT = (
    "Ask the team what this Epic is meant to change, in one sentence, "
    "and write that into {location}."
)

#: Only ever formatted with words the team supplied in this session. A
#: fixed scaffold with no team input stays a prompt: labelling it
#: paste-ready would hand a team its own boilerplate back as an outcome.
OUTCOME_PASTE_READY = "Paste this into {location}, for {epic}:\n\n{text}"

# The flow skill's own distribution buckets. A bucket outside this set
# normalises to "other" before the subtask rule is applied, which is what
# that skill does -- a custom bucket named "subtask-ish" is not a subtask.
_BUCKETS = frozenset({"feature", "defect", "debt", "risk", "subtask", "other"})
_OTHER_BUCKET = "other"
_SUBTASK_BUCKET = "subtask"

_NO_PARENT_LINK = "no parent link was recorded for this issue"
_NOT_IN_SCOPE = "the parent chain ends at {parent}, which is not an in-scope Epic"


def normalised_bucket(row: Mapping[str, Any]) -> str:
    """The row's distribution bucket, funnelled to ``other`` when unknown."""
    raw = row.get("issuetype_bucket") or _OTHER_BUCKET
    return raw if raw in _BUCKETS else _OTHER_BUCKET


def count_throughput(rows: Sequence[Mapping[str, Any]], *, include_subtasks: bool) -> int:
    """Throughput as the flow skill counts it, not as a plain delivered count.

    A row counts when it was delivered in the window **and**, unless
    subtasks are included, its normalised bucket is not ``subtask``.
    Counting every delivered row would publish a larger number under the
    same name.
    """
    return sum(
        1
        for row in rows
        if row.get("delivered_in_window")
        and (include_subtasks or normalised_bucket(row) != _SUBTASK_BUCKET)
    )


def count_work_in_flight(rows: Sequence[Mapping[str, Any]]) -> int:
    """Work in flight as the flow skill counts it: ``wip_at_to``, unfiltered."""
    return sum(1 for row in rows if row.get("wip_at_to"))


def build_epic_rows(
    *,
    per_issue_rows: Sequence[Mapping[str, Any]],
    parents: Mapping[str, str | None],
    jira_state: Mapping[str, Mapping[str, Any]],
    outcomes: Mapping[str, str | None],
    window: Mapping[str, str],
    flow_taken_at: str,
    jira_taken_at: str,
    include_subtasks: bool = False,
    supplied_outcomes: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """One row per in-scope Epic, plus an unattributed group when needed.

    ``per_issue_rows`` are the flow skill's own per-issue rows, which
    carry no Epic and no parent field; ``parents`` is this view's own
    parent-link read resolved to the Epic rung, which is where the join
    comes from. ``outcomes`` keys define the in-scope Epic set, so an Epic
    with no delivered work still renders -- absent work is an answer.
    ``supplied_outcomes`` carries what the team stated this session in
    response to the prompt; it comes back as paste-ready text and is
    never written to Jira by this view.

    The two moments are carried separately on every row. They are two
    passes over Jira and the view never claims one atomic snapshot.
    """
    in_scope = set(outcomes)
    grouped: dict[str, list[Mapping[str, Any]]] = {epic: [] for epic in outcomes}
    unattributed: dict[str, dict[str, str]] = {}

    for row in per_issue_rows:
        key = row.get("key")
        if key is None:
            continue
        parent = parents.get(key)
        if parent in in_scope:
            grouped[str(parent)].append(row)
        else:
            unattributed[str(key)] = {"reason": _reason_for(key, parents, parent)}

    supplied = dict(supplied_outcomes or {})
    flagged_supported = state.flagged_field_available(jira_state)
    rows: list[dict[str, Any]] = [
        _epic_row(
            epic=epic,
            epic_rows=grouped[epic],
            outcome_text=outcomes[epic],
            supplied_text=supplied.get(epic),
            jira_state=jira_state,
            window=window,
            flow_taken_at=flow_taken_at,
            jira_taken_at=jira_taken_at,
            include_subtasks=include_subtasks,
            flagged_supported=flagged_supported,
        )
        for epic in sorted(grouped)
    ]

    if unattributed:
        rows.append(
            {
                "epic": UNATTRIBUTED,
                "unattributed": True,
                "issues": dict(sorted(unattributed.items())),
                "flow_taken_at": flow_taken_at,
                "jira_taken_at": jira_taken_at,
            }
        )
    return rows


def _reason_for(key: str, parents: Mapping[str, str | None], parent: str | None) -> str:
    """Why this issue's chain never reached an in-scope Epic.

    The reason is carried per issue rather than once for the group: two
    issues can end for different reasons, and one group-level string
    cannot say so.
    """
    if key not in parents or parent is None:
        return _NO_PARENT_LINK
    return _NOT_IN_SCOPE.format(parent=parent)


def _epic_row(
    *,
    epic: str,
    epic_rows: Sequence[Mapping[str, Any]],
    outcome_text: str | None,
    supplied_text: str | None,
    jira_state: Mapping[str, Mapping[str, Any]],
    window: Mapping[str, str],
    flow_taken_at: str,
    jira_taken_at: str,
    include_subtasks: bool,
    flagged_supported: bool,
) -> dict[str, Any]:
    issue_keys = [str(row["key"]) for row in epic_rows if row.get("key") is not None]
    in_flight_keys = [
        str(row["key"]) for row in epic_rows if row.get("wip_at_to") and row.get("key")
    ]
    delivery = {
        "throughput": {
            "count": count_throughput(epic_rows, include_subtasks=include_subtasks),
            "window": dict(window),
            "include_subtasks": include_subtasks,
        },
        "work_in_flight": count_work_in_flight(epic_rows),
        "observations": state.observe(
            issue_keys=issue_keys,
            in_flight_keys=in_flight_keys,
            jira_state=jira_state,
            window=window,
            jira_taken_at=jira_taken_at,
            flagged_supported=flagged_supported,
        ),
    }
    return {
        "epic": epic,
        "issues": issue_keys,
        "delivery": delivery,
        "outcome": outcome_position(
            epic=epic, recorded_text=outcome_text, supplied_text=supplied_text
        ),
        "flow_taken_at": flow_taken_at,
        "jira_taken_at": jira_taken_at,
    }


def outcome_position(
    *, epic: str, recorded_text: str | None, supplied_text: str | None
) -> dict[str, Any]:
    """What one Epic's outcome position renders, in all three states.

    Recorded: the team's own text, verbatim, with no assessment of it --
    this view reports an outcome, it never assesses one, because a view
    that marks what a team wrote is a view the team stops writing in.

    Not recorded and unanswered: an explicit statement that none is
    recorded, plus a prompt naming where to write one. Not a blank, and
    not an omitted row: an Epic with no outcome contributes nothing to a
    view trying to look complete, which is exactly why it must appear.

    Not recorded but answered this session: the team's exact words come
    back as text to paste into that same location. The view never writes
    them to Jira and never supplies words of its own.
    """
    location = outcome_reader.OUTCOME_LOCATION
    paste_ready = (
        OUTCOME_PASTE_READY.format(location=location, epic=epic, text=supplied_text)
        if supplied_text
        else None
    )
    recorded = recorded_text is not None
    return {
        "recorded": recorded,
        "text": recorded_text,
        "location": location,
        "statement": (
            OUTCOME_RECORDED.format(location=location) if recorded else OUTCOME_ABSENT
        ),
        "prompt": (
            None
            if recorded or paste_ready
            else OUTCOME_PROMPT.format(location=location)
        ),
        "paste_ready": paste_ready,
    }
