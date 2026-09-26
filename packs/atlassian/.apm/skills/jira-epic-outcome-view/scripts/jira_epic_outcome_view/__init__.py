"""jira-epic-outcome-view CLI.

One view over a Jira scope: what each Epic delivered, and what that work
was meant to change. The delivery half is composed from the flow skill's
own per-issue rows rather than recomputed; the outcome half is read from
Jira and never authored here.

Read-only. Nothing is written to Jira, and neither the working directory
tree nor the installed pack tree changes across a run. The one disclosed
write is the flow skill's per-issue file, which lands outside both and is
removed before this process returns.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from . import flow, jira_read, outcome, parents, view

EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_UPSTREAM = 3

#: Default window when the caller states neither bound: the last 90 days
#: ending today, matching the flow skill's own default so the two halves
#: of the view describe the same span.
DEFAULT_WINDOW_DAYS = 90

#: Every run says this. Jira omits an issue the calling credential cannot
#: browse without signalling that it did, so no upstream flag can trigger
#: the disclosure -- it has to be unconditional.
BROWSE_DISCLOSURE = (
    "This view covers only the work the calling credential can browse. "
    "Jira omits the rest silently, so a scope can be larger than it looks here."
)

_ENV_JIRA_SCRIPT = "JIRA_EPIC_OUTCOME_VIEW_JIRA_SCRIPT"
_ENV_FLOW_SCRIPTS = "JIRA_EPIC_OUTCOME_VIEW_FLOW_METRICS_SCRIPTS"

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent


class ValidationError(Exception):
    """A flag combination or a path this view refuses. Exit 2."""


def _reconfigure_streams() -> None:
    """Force UTF-8 on both streams before anything is printed.

    Jira text carries non-ASCII routinely, and a default-encoded stream
    raises on it partway through a render, leaving half a view on stdout.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jira-epic-outcome-view",
        description="Group a Jira project's work by Epic and show each Epic's outcome.",
    )
    parser.add_argument("--project", required=True, help="Jira project key, e.g. PROJ.")
    parser.add_argument(
        "--from", dest="from_date", metavar="YYYY-MM-DD", default=None,
        help="Window start, inclusive. Defaults to 90 days before --to.",
    )
    parser.add_argument(
        "--to", dest="to_date", metavar="YYYY-MM-DD", default=None,
        help="Window end, inclusive. Defaults to today, UTC.",
    )
    parser.add_argument(
        "--include-subtasks", dest="include_subtasks", action="store_true",
        help="Count delivered subtasks in throughput, as the flow skill does "
             "under the same flag. The reported number gets larger, not smaller.",
    )
    parser.add_argument(
        "--jql", default=None,
        help="Extra JQL narrowing the flow reading's scope.",
    )
    parser.add_argument(
        "--outcome", dest="outcome_answers", action="append", metavar="EPIC-KEY=TEXT",
        default=None,
        help="What the team says this Epic is meant to change. Repeatable, one "
             "per Epic. The words come back as text to paste into Jira; nothing "
             "is written there. Omit it, or pass empty text, to decline.",
    )
    return parser


def resolve_window(from_date: str | None, to_date: str | None) -> dict[str, str]:
    """Resolve the inclusive window both halves of the view are read over."""
    try:
        end = date.fromisoformat(to_date) if to_date else datetime.now(UTC).date()
        start = (
            date.fromisoformat(from_date)
            if from_date
            else end - timedelta(days=DEFAULT_WINDOW_DAYS)
        )
    except ValueError as exc:
        raise ValidationError(f"window bounds must be YYYY-MM-DD: {exc}") from exc
    if start > end:
        raise ValidationError(f"window start {start} is after window end {end}")
    return {"from": start.isoformat(), "to": end.isoformat()}


def resolve_jira_script() -> Path:
    """Locate the Jira client this view reads through.

    The environment override is deliberately not confined to this pack. It
    names a sibling skill's install location and that script is run as a child
    either way -- an actor able to set this process's environment already has
    arbitrary execution here -- so confining it crosses no privilege boundary
    while breaking the relocation `manifest.json` documents. The suppression
    below records that; the taint rule cannot see the reasoning.
    """
    override = os.environ.get(_ENV_JIRA_SCRIPT)
    candidate = (
        # nosemgrep: tools.semgrep.env-var-into-pathlib-path  # operator-set path; see docstring
        Path(override) if override else _SKILL_ROOT.parent / "jira" / "scripts" / "jira.py"
    )
    if not candidate.is_file():
        raise ValidationError(
            f"the jira skill was not found at {candidate}. Install it from this pack, "
            f"or set {_ENV_JIRA_SCRIPT} to its script."
        )
    return candidate.resolve()


def resolve_flow_scripts_dir() -> Path:
    """Locate the flow skill's package directory.

    The override is unconfined for the same reason `resolve_jira_script`
    records: it names an install location whose contents this view runs as a
    child regardless.
    """
    override = os.environ.get(_ENV_FLOW_SCRIPTS)
    candidate = (
        # nosemgrep: tools.semgrep.env-var-into-pathlib-path  # operator-set path; see docstring
        Path(override) if override else _SKILL_ROOT.parent / "flow-metrics" / "scripts"
    )
    if not (candidate / "flow_metrics").is_dir():
        raise ValidationError(
            f"the flow-metrics skill was not found at {candidate}. Install it from this "
            f"pack, or set {_ENV_FLOW_SCRIPTS} to its scripts directory."
        )
    return candidate.resolve()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def render(
    *,
    project: str,
    window: dict[str, str],
    include_subtasks: bool,
    jql: str | None,
    jira_script: Path,
    flow_scripts_dir: Path,
    outcome_answers: Sequence[str] | None = None,
) -> dict[str, Any]:
    """The whole view as one JSON-serialisable document."""
    scope = jira_read.read_scope(script=jira_script, project=project)
    resolved_parents = parents.resolve_epics(scope["parent_links"], scope["epic_keys"])
    # Why each unresolved chain ended, taken from the same walk. The
    # resolved mapping alone cannot say: a parent outside the scope and a
    # parent in a cycle are both `None` by the time it is built.
    chain_ends = parents.chain_end_reasons(scope["parent_links"], scope["epic_keys"])

    scope_args = ["--project", project]
    if jql:
        scope_args += ["--jql", jql]
    per_issue_rows = flow.run_flow_metrics(
        scripts_dir=flow_scripts_dir,
        scope_args=scope_args,
        window=window,
        include_subtasks=include_subtasks,
        cwd_root=Path.cwd(),
        pack_root=_SKILL_ROOT.parent.parent.parent,
    )
    flow_taken_at = _now()

    # The Epic set is whatever the fully paginated Jira read returned for
    # this credential, never a narrower list: an Epic dropped here would
    # never reach the rendered view and no error anywhere would say so.
    # An Epic whose description Jira did not return reads as no outcome
    # recorded, which is the same answer as an empty block.
    descriptions = scope.get("descriptions") or {}
    outcomes: dict[str, str | None] = {
        epic: outcome.extract_outcome(descriptions.get(epic))
        for epic in scope["epic_keys"]
    }
    supplied = outcome.parse_answers(outcome_answers, epic_keys=set(outcomes))

    epics = view.build_epic_rows(
        per_issue_rows=per_issue_rows,
        parents=resolved_parents,
        chain_ends=chain_ends,
        jira_state=scope["jira_state"],
        outcomes=outcomes,
        supplied_outcomes=supplied,
        include_subtasks=include_subtasks,
        window=window,
        flow_taken_at=flow_taken_at,
        jira_taken_at=scope["taken_at"],
    )
    return {
        "project": project,
        "window": dict(window),
        "flow_taken_at": flow_taken_at,
        "jira_taken_at": scope["taken_at"],
        "coverage": BROWSE_DISCLOSURE,
        "epics": epics,
    }


def main(argv: Sequence[str] | None = None) -> int:
    _reconfigure_streams()
    args = build_parser().parse_args(argv)
    try:
        window = resolve_window(args.from_date, args.to_date)
        document = render(
            project=args.project,
            window=window,
            include_subtasks=args.include_subtasks,
            jql=args.jql,
            jira_script=resolve_jira_script(),
            flow_scripts_dir=resolve_flow_scripts_dir(),
            outcome_answers=args.outcome_answers,
        )
    except (
        ValidationError,
        outcome.OutcomeAnswerError,
        jira_read.ProjectKeyRefused,
        jira_read.WriteVerbRefused,
        flow.ScratchLocationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    except (jira_read.JiraReadError, flow.FlowMetricsError) as exc:
        # An upstream failure is surfaced rather than rendered as an empty
        # scope: "no Epics" and "could not reach Jira" are different facts.
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UPSTREAM
    print(json.dumps(document, indent=2, ensure_ascii=False))
    return EXIT_OK
