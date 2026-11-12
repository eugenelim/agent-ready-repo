"""Tests for the stuck workflow run watchdog (spec: docs/specs/stuck-run-watchdog)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "stuck_runs_watchdog.py"
_spec = importlib.util.spec_from_file_location("stuck_runs_watchdog", SCRIPT)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)

REPO = "example-org/example-repo"
NOW = datetime(2026, 11, 12, 12, 0, 0, tzinfo=UTC)
BOT = "github-actions[bot]"


def iso(hours_ago: float) -> str:
    return (NOW - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(
    run_id: int,
    status: str = "queued",
    hours: float = 5,
    name: str = "pages",
    started: float | None = None,
    path: object = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": run_id,
        "name": name,
        "status": status,
        "created_at": iso(hours),
        "head_branch": "evil-branch",
        "display_title": "evil title @someone",
        "actor": {"login": "evil-actor"},
    }
    if started is not None:
        out["run_started_at"] = iso(started)
    if path is not None:
        out["path"] = path
    return out


def issue(
    number: int = 7,
    body: str | None = None,
    login: str = BOT,
    title: str = mod.TITLE,
    pull_request: bool = False,
    marker: bool = True,
) -> dict[str, Any]:
    text = (mod.MARKER + "\nold") if body is None and marker else (body or "old")
    out: dict[str, Any] = {
        "number": number,
        "title": title,
        "state": "open",
        "body": text,
        "user": {"login": login},
    }
    if pull_request:
        out["pull_request"] = {}
    return out


class FakeGh:
    """Records every call; serves runs by status and page, issues by page."""

    def __init__(
        self,
        runs: dict[str, list[list[dict[str, Any]]]] | None = None,
        issues: list[list[dict[str, Any]]] | None = None,
        fail_on: str | None = None,
    ) -> None:
        self.runs = runs or {}
        self.issues = issues or []
        self.fail_on = fail_on
        self.calls: list[tuple[str, str, dict[str, str], Any]] = []

    def __call__(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        payload: Any = None,
    ) -> Any:
        self.calls.append((method, path, dict(query or {}), payload))
        if self.fail_on and self.fail_on in path:
            raise RuntimeError("gh failed")
        if method == "GET" and path.endswith("/actions/runs"):
            pages = self.runs.get((query or {})["status"], [])
            page = int((query or {})["page"])
            return {"workflow_runs": pages[page - 1] if page <= len(pages) else []}
        if method == "GET" and path.endswith("/issues"):
            page = int((query or {})["page"])
            return self.issues[page - 1] if page <= len(self.issues) else []
        return {"number": 99}

    @property
    def writes(self) -> list[tuple[str, str, dict[str, str], Any]]:
        return [c for c in self.calls if c[0] != "GET"]

    def pages_requested(self, suffix: str, key: str | None = None) -> list[int]:
        return [
            int(c[2]["page"])
            for c in self.calls
            if c[0] == "GET"
            and c[1].endswith(suffix)
            and (key is None or c[2].get("status") == key)
        ]


# AC11: classification ---------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "hours", "stuck"),
    [
        ("in_progress", 3.5, True),
        ("in_progress", 3.0, False),
        ("in_progress", 2.9, False),
        ("queued", 2.5, True),
        ("queued", 2.0, False),
        ("waiting", 2.5, True),
        ("pending", 2.5, True),
        ("requested", 2.5, True),
        ("completed", 99, False),
        ("action_required", 99, False),
    ],
)
def test_stuck_thresholds_and_status_set(status: str, hours: float, stuck: bool) -> None:
    got = mod.classify([run(1, status, hours)], NOW, None)
    assert (len(got) == 1) is stuck


def test_in_progress_age_counts_from_run_started_at() -> None:
    created_long_ago_started_recently = run(1, "in_progress", 10, started=1)
    assert mod.classify([created_long_ago_started_recently], NOW, None) == []
    started_long_ago = run(2, "in_progress", 10, started=4)
    assert [r.run_id for r in mod.classify([started_long_ago], NOW, None)] == [2]


def test_own_run_is_never_stuck() -> None:
    assert mod.classify([run(5, "in_progress", 9)], NOW, 5) == []


def test_elapsed_hours_floor_from_classification_timestamp() -> None:
    got = mod.classify([run(1, "in_progress", 9, started=3.5)], NOW, None)
    assert got[0].hours == 3


# AC12: unparseable timestamp ---------------------------------------------------


def test_invalid_required_timestamp_exits_nonzero_with_zero_writes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad = run(1, "queued", 5)
    bad["created_at"] = "not-a-time"
    gh = FakeGh(runs={"queued": [[bad]]}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 1
    assert gh.writes == []


# AC12: approval-gated publish workflows are never flagged while waiting ---------

GATED = [
    ".github/workflows/publish-claude-plugins.yml",
    ".github/workflows/release-agentbundle.yml",
    ".github/workflows/release-credbroker.yml",
    ".github/workflows/release-jsonl-otlp-exporter.yml",
]


@pytest.mark.parametrize("gated", GATED)
@pytest.mark.parametrize("suffix", ["", "@refs/heads/x", "@refs/pull/9/merge"])
def test_waiting_run_of_an_approval_gated_workflow_is_never_stuck(gated: str, suffix: str) -> None:
    assert mod.classify([run(1, "waiting", 100, path=gated + suffix)], NOW, None) == []


@pytest.mark.parametrize("gated", GATED)
@pytest.mark.parametrize("status", ["queued", "in_progress", "pending", "requested"])
def test_other_statuses_of_an_approval_gated_workflow_are_still_classified(
    gated: str, status: str
) -> None:
    got = mod.classify([run(1, status, 100, path=gated)], NOW, None)
    assert [r.run_id for r in got] == [1]


@pytest.mark.parametrize(
    "path",
    [
        None,
        123,
        ["x"],
        ".github/workflows/pages.yml",
        "other/.github/workflows/release-agentbundle.yml",
        ".github/workflows/xrelease-agentbundle.yml",
        ".github/workflows/release-agentbundle.ymlx",
        ".github/workflows/release-agentbundle.yml@other.yml",
        ".github/workflows/release-agentbundle.yml@refs/",
        ".github/workflows/release-agentbundle.yml@",
        ".github/workflows/release-agentbundle.yml@refs/x\nhead",
    ],
)
def test_a_waiting_run_with_any_other_path_is_still_stuck(path: object) -> None:
    got = mod.classify([run(1, "waiting", 100, path=path)], NOW, None)
    assert [r.run_id for r in got] == [1]


def test_exempt_waiting_run_with_an_unparseable_timestamp_exits_zero() -> None:
    bad = run(1, "waiting", 5, path=GATED[0])
    bad["created_at"] = "not-a-time"
    gh = FakeGh(runs={"waiting": [[bad]]}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert gh.writes == []


# AC13 to AC17: rendering -------------------------------------------------------


def test_body_carries_listed_fields_and_both_cancel_commands() -> None:
    stuck = mod.classify([run(4242, "waiting", 6, name="pages")], NOW, None)
    body = mod.render_body(stuck, REPO, incomplete=False)
    assert body.startswith(mod.MARKER)
    assert "4242" in body and "pages" in body and "waiting" in body and "6" in body
    assert f"https://github.com/{REPO}/actions/runs/4242" in body
    assert "gh run cancel 4242" in body
    assert f"gh api -X POST repos/{REPO}/actions/runs/4242/force-cancel" in body


def test_hostile_workflow_name_is_sanitised_and_capped() -> None:
    hostile = "@octocat <img src=x> `rm -rf` [x](http://e) | " + "A" * 300
    stuck = mod.classify([run(1, "queued", 5, name=hostile)], NOW, None)
    assert re.fullmatch(r"[A-Za-z0-9 ._-]{1,120}", stuck[0].name)
    body = mod.render_body(stuck, REPO, incomplete=False)
    for bad in ("@octocat", "<img", "`rm", "](http"):
        assert bad not in body


def test_body_contains_no_other_run_field() -> None:
    stuck = mod.classify([run(1, "queued", 5)], NOW, None)
    body = mod.render_body(stuck, REPO, incomplete=False)
    for leaked in ("evil-branch", "evil title", "evil-actor", "someone"):
        assert leaked not in body


def test_body_lists_at_most_fifty_runs_and_says_incomplete() -> None:
    stuck = mod.classify([run(i, "queued", 5) for i in range(1, 80)], NOW, None)
    body = mod.render_body(stuck, REPO, incomplete=False)
    assert len(re.findall(r"^- run \d+", body, flags=re.M)) == 50
    assert "incomplete" in body.lower()


def test_body_is_at_most_60000_bytes() -> None:
    names = ["N" * 120 for _ in range(60)]
    stuck = mod.classify(
        [run(10**15 + i, "queued", 5, name=n) for i, n in enumerate(names)], NOW, None
    )
    body = mod.render_body(stuck, REPO, incomplete=False)
    assert len(body.encode("utf-8")) <= 60_000


def test_body_states_incomplete_when_listing_limit_hit() -> None:
    stuck = mod.classify([run(1, "queued", 5)], NOW, None)
    assert "incomplete" in mod.render_body(stuck, REPO, incomplete=True).lower()
    assert "incomplete" not in mod.render_body(stuck, REPO, incomplete=False).lower()


# AC18 to AC20: issue matching and discovery ------------------------------------


def test_only_the_marked_bot_issue_with_exact_title_matches() -> None:
    issues = [
        issue(1, login="someone-else"),
        issue(2, title="Stuck workflow runs "),
        issue(3, pull_request=True),
        issue(4, marker=False),
        issue(5, login="dependabot[bot]"),
    ]
    assert mod.find_watchdog_issues(issues) == []
    assert [i["number"] for i in mod.find_watchdog_issues(issues + [issue(8)])] == [8]


def test_two_matches_raise_before_any_write() -> None:
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[issue(1), issue(2)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 1
    assert gh.writes == []


def test_match_only_on_page_two_is_edited_not_duplicated() -> None:
    filler = [issue(1000 + i, login="x") for i in range(100)]
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[filler, [issue(77)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert [(m, p) for m, p, _, _ in gh.writes] == [("PATCH", f"repos/{REPO}/issues/77")]


def test_issue_listing_still_full_at_page_twenty_fails_before_any_write() -> None:
    full = [[issue(i * 1000 + j, login="x") for j in range(100)] for i in range(20)]
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=full)
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 1
    assert gh.writes == []
    assert gh.pages_requested("/issues") == list(range(1, 21))


# AC21 to AC26: sync ------------------------------------------------------------


def test_creates_exactly_one_issue_when_stuck_and_none_open() -> None:
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert len(gh.writes) == 1
    method, path, _, payload = gh.writes[0]
    assert (method, path) == ("POST", f"repos/{REPO}/issues")
    assert payload["title"] == mod.TITLE and mod.MARKER in payload["body"]


def test_edits_when_body_differs_and_creates_none() -> None:
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[issue(7)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert [(m, p) for m, p, _, _ in gh.writes] == [("PATCH", f"repos/{REPO}/issues/7")]


def test_identical_body_makes_no_write() -> None:
    stuck = mod.classify([run(1)], NOW, None)
    same = mod.render_body(stuck, REPO, incomplete=False)
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[issue(7, body=same)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert gh.writes == []


def test_nothing_stuck_comments_then_closes_open_issue() -> None:
    gh = FakeGh(runs={}, issues=[[issue(7)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert [(m, p) for m, p, _, _ in gh.writes] == [
        ("POST", f"repos/{REPO}/issues/7/comments"),
        ("PATCH", f"repos/{REPO}/issues/7"),
    ]
    assert gh.writes[1][3]["state"] == "closed"


def test_nothing_stuck_and_none_open_creates_nothing() -> None:
    gh = FakeGh(runs={}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert gh.writes == []


def test_full_page_ten_is_incomplete_never_closes_and_never_asks_page_eleven(
    capsys: pytest.CaptureFixture[str],
) -> None:
    full = [run(i, "completed", 1) for i in range(100)]
    gh = FakeGh(runs={"queued": [full] * 10}, issues=[[issue(7)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert gh.writes == []
    assert gh.pages_requested("/actions/runs", "queued") == list(range(1, 11))
    assert "incomplete" in capsys.readouterr().out.lower()


def test_partial_page_ten_is_a_complete_listing() -> None:
    full = [run(i, "completed", 1) for i in range(100)]
    recent = run(1000, "queued", 1)  # younger than the two-hour limit: not stuck
    gh = FakeGh(runs={"queued": [full] * 9 + [[recent]]}, issues=[[issue(7)]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    # The listing was complete and held no stuck run, so the issue is closed.
    assert [(m, p) for m, p, _, _ in gh.writes] == [
        ("POST", f"repos/{REPO}/issues/7/comments"),
        ("PATCH", f"repos/{REPO}/issues/7"),
    ]


def test_incomplete_listing_with_stuck_runs_still_reports_and_marks_incomplete() -> None:
    full = [run(i, "queued", 5) for i in range(1, 101)]
    gh = FakeGh(runs={"queued": [full] * 10}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    assert "incomplete" in gh.writes[0][3]["body"].lower()


# AC27 to AC29: writes, failures, dry run ---------------------------------------

ALLOWED_WRITES = (
    re.compile(r"POST repos/[^/]+/[^/]+/issues"),
    re.compile(r"PATCH repos/[^/]+/[^/]+/issues/\d+"),
    re.compile(r"POST repos/[^/]+/[^/]+/issues/\d+/comments"),
)


@pytest.mark.parametrize(
    ("runs", "issues"),
    [
        ({"queued": [[run(1)]]}, [[]]),
        ({"queued": [[run(1)]]}, [[issue(7)]]),
        ({}, [[issue(7)]]),
        ({}, [[]]),
        ({"in_progress": [[run(2, "in_progress", 9)]]}, [[issue(7)]]),
    ],
)
def test_only_issue_writes_are_ever_made(
    runs: dict[str, list[list[dict[str, Any]]]], issues: list[list[dict[str, Any]]]
) -> None:
    gh = FakeGh(runs=runs, issues=issues)
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    for method, path, _, _ in gh.writes:
        assert any(p.fullmatch(f"{method} {path}") for p in ALLOWED_WRITES)
        assert "cancel" not in path and "rerun" not in path


@pytest.mark.parametrize("fail_on", ["/actions/runs", "/issues"])
def test_failed_gh_call_exits_nonzero(fail_on: str) -> None:
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[]], fail_on=fail_on)
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 1
    assert gh.writes == []


def test_dry_run_prints_report_and_makes_no_write(
    capsys: pytest.CaptureFixture[str],
) -> None:
    gh = FakeGh(runs={"queued": [[run(4242)]]}, issues=[[issue(7)]])
    assert mod.main(["--repo", REPO, "--dry-run"], gh=gh, now=NOW, env={}) == 0
    assert gh.writes == []
    assert "gh run cancel 4242" in capsys.readouterr().out


def test_repo_argument_is_validated() -> None:
    gh = FakeGh()
    with pytest.raises(SystemExit):
        mod.main(["--repo", "bad repo; rm"], gh=gh, now=NOW, env={})
    assert gh.calls == []


def test_own_run_id_from_environment_is_excluded() -> None:
    gh = FakeGh(runs={"in_progress": [[run(5, "in_progress", 9)]]}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={"GITHUB_RUN_ID": "5"}) == 0
    assert gh.writes == []


def test_cli_json_payload_round_trip_is_serialisable() -> None:
    gh = FakeGh(runs={"queued": [[run(1)]]}, issues=[[]])
    mod.main(["--repo", REPO], gh=gh, now=NOW, env={})
    json.dumps(gh.writes[0][3])


# AC1 to AC10: workflow posture ---------------------------------------------------

WORKFLOW = ROOT / ".github" / "workflows" / "stuck-runs-watchdog.yml"


@pytest.fixture(scope="module")
def workflow() -> dict[Any, Any]:
    yaml = pytest.importorskip("yaml")
    loaded = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _job(wf: dict[Any, Any]) -> dict[str, Any]:
    assert list(wf["jobs"]) and len(wf["jobs"]) == 1
    return next(iter(wf["jobs"].values()))


def test_triggers_are_exactly_one_hourly_schedule_and_dispatch(workflow: dict[Any, Any]) -> None:
    triggers = workflow[True]  # YAML 1.1 reads the key `on` as True
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert len(triggers["schedule"]) == 1
    assert re.fullmatch(r"\d{1,2} \* \* \* \*", triggers["schedule"][0]["cron"])


def test_top_level_permissions_are_empty(workflow: dict[Any, Any]) -> None:
    assert workflow["permissions"] == {}


def test_job_permissions_are_exactly_actions_read_and_issues_write(
    workflow: dict[Any, Any],
) -> None:
    assert _job(workflow)["permissions"] == {"actions": "read", "issues": "write"}


def test_no_run_body_holds_an_expression(workflow: dict[Any, Any]) -> None:
    runs = [s["run"] for s in _job(workflow)["steps"] if "run" in s]
    assert runs and all("${{" not in r for r in runs)


def test_every_action_is_pinned_to_a_full_commit_sha(workflow: dict[Any, Any]) -> None:
    uses = [s["uses"] for s in _job(workflow)["steps"] if "uses" in s]
    assert all(re.search(r"@[0-9a-f]{40}$", u) for u in uses)


def test_job_timeout_is_between_one_and_five_minutes(workflow: dict[Any, Any]) -> None:
    assert 1 <= _job(workflow)["timeout-minutes"] <= 5


def test_concurrency_is_exact_and_workflow_level(workflow: dict[Any, Any]) -> None:
    assert workflow["concurrency"] == {"group": "stuck-runs-watchdog", "cancel-in-progress": False}
    assert "concurrency" not in _job(workflow)


def test_nothing_continues_on_error(workflow: dict[Any, Any]) -> None:
    job = _job(workflow)
    for node in (job, *job["steps"]):
        assert node.get("continue-on-error", False) is False


def test_watchdog_step_shell_masks_no_error(workflow: dict[Any, Any]) -> None:
    runs = [s["run"] for s in _job(workflow)["steps"] if "run" in s]
    masking = re.compile(
        r"\|\|\s*(true|:|exit\s+0)|set\s+\+e|exit\s+0|2>\s*/dev/null|&>\s*/dev/null"
    )
    assert not any(masking.search(r) for r in runs)
    assert any("stuck_runs_watchdog.py" in r for r in runs)


def test_no_if_can_skip_the_job_or_a_step(workflow: dict[Any, Any]) -> None:
    job = _job(workflow)
    assert "if" not in job and all("if" not in s for s in job["steps"])


# Review repairs ----------------------------------------------------------------


def test_incomplete_listing_never_says_nothing_is_stuck_in_dry_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    full = [run(i, "completed", 1) for i in range(100)]
    gh = FakeGh(runs={"queued": [full] * 10})
    assert mod.main(["--repo", REPO, "--dry-run"], gh=gh, now=NOW, env={}) == 0
    out = capsys.readouterr().out.lower()
    assert "incomplete" in out and "no stuck run" not in out


def test_incomplete_listing_never_says_nothing_is_stuck_when_syncing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    full = [run(i, "completed", 1) for i in range(100)]
    gh = FakeGh(runs={"queued": [full] * 10}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    out = capsys.readouterr().out.lower()
    assert "incomplete" in out and "no stuck run" not in out


def test_incomplete_listing_raises_a_workflow_warning_annotation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    full = [run(i, "completed", 1) for i in range(100)]
    gh = FakeGh(runs={"queued": [full] * 10}, issues=[[]])
    mod.main(["--repo", REPO], gh=gh, now=NOW, env={})
    assert "::warning::" in capsys.readouterr().out


def test_workflow_names_render_inside_a_code_span() -> None:
    stuck = mod.classify(
        [run(1, "queued", 5, name="__Recovery__ visit www.attacker.example")], NOW, None
    )
    body = mod.render_body(stuck, REPO, incomplete=False)
    assert re.search(r"^- run 1 - `[A-Za-z0-9 ._-]+` - queued", body, flags=re.M)
    assert "`__Recovery__ visit www.attacker.example`" in body


def test_issue_discovery_asks_only_for_issues_created_by_the_bot() -> None:
    gh = FakeGh(runs={}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 0
    queries = [c[2] for c in gh.calls if c[1].endswith("/issues") and c[0] == "GET"]
    assert queries and all(q.get("creator") == BOT for q in queries)


def test_an_empty_run_started_at_is_invalid_not_absent() -> None:
    bad = run(1, "in_progress", 30)
    bad["run_started_at"] = ""
    gh = FakeGh(runs={"in_progress": [[bad]]}, issues=[[]])
    assert mod.main(["--repo", REPO], gh=gh, now=NOW, env={}) == 1
    assert gh.writes == []


@pytest.mark.parametrize("absent", [None, "missing"])
def test_a_missing_or_null_run_started_at_falls_back_to_created_at(absent: str | None) -> None:
    item = run(1, "in_progress", 30)
    if absent is None:
        item["run_started_at"] = None
    got = mod.classify([item], NOW, None)
    assert [r.run_id for r in got] == [1]
