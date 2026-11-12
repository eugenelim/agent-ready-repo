#!/usr/bin/env python3
"""Report workflow runs stuck beyond a limit and keep one GitHub issue current.

Read-only toward Actions: the report carries the cancel commands as text and the
code never runs them. The only writes are issue create, edit, comment and close.
Spec: docs/specs/stuck-run-watchdog/spec.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re

# The only child process is `gh`, called with a fixed argv and no shell.
import subprocess  # nosec B404
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

TITLE = "Stuck workflow runs"
MARKER = "<!-- stuck-runs-watchdog:v1 -->"
BOT_LOGIN = "github-actions[bot]"

IN_PROGRESS_LIMIT_SECONDS = 3 * 3600
WAITING_LIMIT_SECONDS = 2 * 3600
WAITING_STATUSES = ("queued", "waiting", "pending", "requested")
CANDIDATE_STATUSES = ("in_progress", *WAITING_STATUSES)

PER_PAGE = 100
RUN_MAX_PAGES = 10  # GitHub caps a status-filtered search at 1,000 results
ISSUE_MAX_PAGES = 20
MAX_REPORTED_RUNS = 50
MAX_NAME_CHARS = 120
MAX_BODY_BYTES = 60_000

# A run `waiting` on a human approval of a publish environment is not stuck. Matched
# by exact workflow path (an optional `@refs/<ref>` suffix is how GitHub reports a
# run on a non-default ref); the Pages deploy is deliberately absent.
_APPROVAL_GATED_PATH = re.compile(
    r"\.github/workflows/"
    r"(?:publish-claude-plugins|release-agentbundle|release-credbroker"
    r"|release-jsonl-otlp-exporter)\.yml(?:@refs/.+)?"
)
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9 ._-]")

# (method, path, query, payload) -> decoded JSON; raises on any failure.
Gh = Callable[[str, str, "dict[str, str] | None", Any], Any]


class IncompleteListing(Exception):
    """A listing the code needs in full was cut by a page limit."""


@dataclass(frozen=True)
class StuckRun:
    run_id: int
    name: str
    status: str
    hours: int


def parse_time(value: object) -> datetime:
    """Parse a GitHub UTC timestamp; raise ValueError when it is not one."""
    if not isinstance(value, str):
        raise ValueError(f"timestamp is not a string: {type(value).__name__}")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp has no zone: {value!r}")
    return parsed.astimezone(UTC)


def safe_name(value: object) -> str:
    """Restrict a workflow name to a safe alphabet and length."""
    if not isinstance(value, str) or not value:
        return "unknown"
    return _UNSAFE_NAME.sub("_", value)[:MAX_NAME_CHARS]


def classify(
    runs: Sequence[Mapping[str, Any]], now: datetime, own_run_id: int | None
) -> list[StuckRun]:
    """Return the runs stuck beyond their limit, oldest first."""
    stuck: list[StuckRun] = []
    for item in runs:
        run_id, status = item.get("id"), item.get("status")
        if not isinstance(run_id, int) or isinstance(run_id, bool):
            raise ValueError("run id is not an integer")
        if run_id == own_run_id or status not in CANDIDATE_STATUSES:
            continue
        path = item.get("path")
        if status == "waiting" and isinstance(path, str) and _APPROVAL_GATED_PATH.fullmatch(path):
            continue
        if status == "in_progress":
            start = item.get("run_started_at")
            if start is None:
                start = item.get("created_at")
            limit = IN_PROGRESS_LIMIT_SECONDS
        else:
            start, limit = item.get("created_at"), WAITING_LIMIT_SECONDS
        age = (now - parse_time(start)).total_seconds()
        if age > limit:
            stuck.append(
                StuckRun(run_id, safe_name(item.get("name")), str(status), int(age // 3600))
            )
    return sorted(stuck, key=lambda r: (-r.hours, r.run_id))


def _render(shown: Sequence[StuckRun], repo: str, notice: str) -> str:
    lines = [
        MARKER,
        "",
        "These workflow runs look stuck. This issue is kept current by the stuck-runs watchdog.",
        "",
    ]
    if notice:
        lines += [f"**This report is incomplete: {notice}**", ""]
    for r in shown:
        url = f"https://github.com/{repo}/actions/runs/{r.run_id}"
        lines.append(f"- run {r.run_id} - `{r.name}` - {r.status} - {r.hours}h - {url}")
    lines += [
        "",
        "Cancel a run (the second form forces it when the first is refused):",
        "",
        "```sh",
    ]
    for r in shown:
        lines += [
            f"gh run cancel {r.run_id}",
            f"gh api -X POST repos/{repo}/actions/runs/{r.run_id}/force-cancel",
        ]
    lines += ["```", ""]
    return "\n".join(lines)


def render_body(stuck: Sequence[StuckRun], repo: str, incomplete: bool) -> str:
    """Render the issue body within the run and byte caps."""
    shown = list(stuck[:MAX_REPORTED_RUNS])
    while True:
        cut = len(stuck) - len(shown)
        notice = ""
        if incomplete:
            notice = "a listing limit was reached, so older stuck runs may be missing"
        if cut:
            notice = (notice + "; " if notice else "") + f"{cut} more stuck run(s) are not shown"
        body = _render(shown, repo, notice)
        if len(body.encode("utf-8")) <= MAX_BODY_BYTES or not shown:
            return body
        shown.pop()


def find_watchdog_issues(issues: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Return only open, non-PR issues the watchdog itself created."""
    found = []
    for item in issues:
        user = item.get("user") or {}
        body = item.get("body") or ""
        if (
            "pull_request" not in item
            and item.get("state") == "open"
            and user.get("login") == BOT_LOGIN
            and item.get("title") == TITLE
            and MARKER in body
        ):
            found.append(item)
    return found


def fetch_runs(gh: Gh, repo: str) -> tuple[list[dict[str, Any]], bool]:
    """List candidate runs; the flag is true when a status hit the search ceiling."""
    runs: list[dict[str, Any]] = []
    incomplete = False
    for status in CANDIDATE_STATUSES:
        for page in range(1, RUN_MAX_PAGES + 1):
            query = {"status": status, "per_page": str(PER_PAGE), "page": str(page)}
            items = gh("GET", f"repos/{repo}/actions/runs", query, None)["workflow_runs"]
            runs.extend(items)
            if len(items) < PER_PAGE:
                break
            incomplete = incomplete or page == RUN_MAX_PAGES
    return runs, incomplete


def fetch_issues(gh: Gh, repo: str) -> list[dict[str, Any]]:
    """List open issues; raise IncompleteListing when pages remain after the limit."""
    issues: list[dict[str, Any]] = []
    for page in range(1, ISSUE_MAX_PAGES + 1):
        query = {
            "state": "open",
            "creator": BOT_LOGIN,
            "per_page": str(PER_PAGE),
            "page": str(page),
        }
        items = gh("GET", f"repos/{repo}/issues", query, None)
        issues.extend(items)
        if len(items) < PER_PAGE:
            return issues
    raise IncompleteListing(f"open issues fill {ISSUE_MAX_PAGES} pages")


def sync(gh: Gh, repo: str, stuck: Sequence[StuckRun], incomplete: bool) -> str:
    """Create, edit, or close the one watchdog issue; return a one-line summary."""
    matches = find_watchdog_issues(fetch_issues(gh, repo))
    if len(matches) > 1:
        raise IncompleteListing(f"{len(matches)} open watchdog issues match")
    issue = matches[0] if matches else None
    base = f"repos/{repo}/issues"
    if stuck:
        body = render_body(stuck, repo, incomplete)
        if issue is None:
            gh("POST", base, None, {"title": TITLE, "body": body})
            return f"opened an issue for {len(stuck)} stuck run(s)"
        if issue.get("body") != body:
            gh("PATCH", f"{base}/{issue['number']}", None, {"body": body})
            return f"updated issue {issue['number']} for {len(stuck)} stuck run(s)"
        return f"issue {issue['number']} is already current"
    if incomplete:
        return (
            "the run listing is incomplete, so whether a run is stuck is unknown; "
            "the issue is left as it is"
        )
    if issue is None:
        return "no stuck run found"
    number = issue["number"]
    gh(
        "POST",
        f"{base}/{number}/comments",
        None,
        {"body": "No stuck workflow runs remain. Closing."},
    )
    gh("PATCH", f"{base}/{number}", None, {"state": "closed", "state_reason": "completed"})
    return f"closed issue {number}: no stuck run remains"


def run_gh(
    method: str, path: str, query: dict[str, str] | None = None, payload: Any = None
) -> Any:
    """Call the GitHub REST API through the `gh` CLI; raise on failure."""
    argv = ["gh", "api", "-X", method, path]
    for key, value in (query or {}).items():
        argv += ["-f", f"{key}={value}"]
    stdin = None
    if payload is not None:
        argv += ["--input", "-"]
        stdin = json.dumps(payload)
    # Fixed argv, no shell; the repository argument was validated by _repo_arg.
    done = subprocess.run(  # nosec B603
        argv, input=stdin, capture_output=True, text=True, check=True, timeout=120
    )
    return json.loads(done.stdout) if done.stdout.strip() else None


def _repo_arg(value: str) -> str:
    if not _REPO.fullmatch(value):
        raise argparse.ArgumentTypeError(f"not an OWNER/NAME repository: {value!r}")
    return value


def main(
    argv: Sequence[str] | None = None,
    gh: Gh = run_gh,
    now: datetime | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=_repo_arg, help="OWNER/NAME")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the report and write nothing"
    )
    args = parser.parse_args(argv)
    clock = now or datetime.now(UTC)
    own = (env if env is not None else os.environ).get("GITHUB_RUN_ID", "")
    try:
        runs, incomplete = fetch_runs(gh, args.repo)
        stuck = classify(runs, clock, int(own) if own.isdigit() else None)
        if args.dry_run:
            if stuck:
                print(render_body(stuck, args.repo, incomplete))
            else:
                print(
                    "The run listing is incomplete, so whether a run is stuck is unknown."
                    if incomplete
                    else "No stuck runs."
                )
            return 0
        print("stuck-runs-watchdog: " + sync(gh, args.repo, stuck, incomplete))
        if incomplete:
            print(
                "::warning::stuck-runs-watchdog: the run listing is incomplete "
                "(search ceiling reached)"
            )
        return 0
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
        IncompleteListing,
    ) as exc:
        detail = getattr(exc, "stderr", "") or ""
        print(
            f"stuck-runs-watchdog: failed: {type(exc).__name__}: {exc} {str(detail)[:300]}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
