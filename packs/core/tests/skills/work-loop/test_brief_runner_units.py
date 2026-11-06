"""Brief runner read core, unit level: Spec map parse and the supervisor-answer stage map.

No Git and no supervisor process runs here; the integration suite covers both.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
    / "brief-runner.py"
)


def _load() -> ModuleType:
    """Load the runner by path under a pack- and skill-unique name."""
    alias = "core_work_loop_brief_runner_units"
    spec = importlib.util.spec_from_file_location(alias, _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


runner = _load()

BRIEF = """# Brief: demo

- **Slug:** `demo`

## Outcome

Prose with a | pipe that is not a row.

## Spec map

Prose under the heading | with a pipe.

| Spec | Status |
| --- | --- |
| `alpha` | <auto> |
| `beta-two` | Shipped |
| gamma3 | <auto> |

## Governance references

| `not-a-row` | x |
"""


def _brief(*rows: str, heading: str = "## Spec map") -> str:
    table = "\n".join(f"| {row} | <auto> |" for row in rows)
    return f"# Brief\n\n{heading}\n\n| Spec | Status |\n| --- | --- |\n{table}\n"


# ── AC-0003: the Spec map ───────────────────────────────────────────────────


def test_the_spec_map_is_read_in_table_order() -> None:
    assert runner.parse_spec_map(BRIEF) == ["alpha", "beta-two", "gamma3"]


def test_a_commented_row_and_a_row_after_the_next_heading_are_not_rows() -> None:
    text = _brief("`one`") + "<!--\n| `hidden` | x |\n-->\n| `two` | x |\n## After\n| `late` | x |\n"
    assert runner.parse_spec_map(text) == ["one", "two"]


def test_a_repeated_spec_map_heading_reopens_the_section() -> None:
    text = _brief("`one`") + "\n## Spec map\n\n| `two` | x |\n"
    assert runner.parse_spec_map(text) == ["one", "two"]


@pytest.mark.parametrize(
    "text",
    [
        "# Brief\n\n## Outcome\n\nNothing here.\n",
        "# Brief\n\n## Spec map\n\n| Spec | Status |\n| --- | --- |\n",
        _brief("`one`", "`two`", "`one`"),
        _brief("`Upper`"),
        _brief("`under_score`"),
        _brief("`double--hyphen`"),
        _brief("`-lead`"),
        _brief("`trail-`"),
        _brief("`café`"),
        _brief("`with space`"),
        _brief("``"),
        _brief(" "),
        "# Brief\n\n## Spec map\n\n| Spec | Status |\n| --- | --- |\n|  | x |\n| `one` | x |\n",
        "# Brief\n\n<!--\n## Spec map\n| `one` | x |\n-->\n",
    ],
)
def test_an_invalid_spec_map_is_refused(text: str) -> None:
    with pytest.raises(runner.Refusal) as caught:
        runner.parse_spec_map(text)
    assert caught.value.code == "invalid-spec-map"


def test_only_the_row_before_the_separator_is_a_header() -> None:
    assert runner.parse_spec_map(_brief("`spec`", "`one`")) == ["spec", "one"]
    text = "# Brief\n\n## Spec map\n\n| `one` | x |\n| `two` | x |\n"
    assert runner.parse_spec_map(text) == ["one", "two"]  # no separator: no header


# ── header status ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("# Spec: x\n\n- **Status:** Approved <!-- Draft | Approved -->\n\n## A\n", "Approved"),
        ("- **Status:** Shipped (2026-01-01)\n", "Shipped"),
        ("- **Status:** `Draft`\n", "Draft"),
        ("# Spec\n\n## Body\n\n- **Status:** Approved\n", None),
        ("<!-- - **Status:** Approved -->\n", None),
        ("no header\n", None),
    ],
)
def test_the_header_status_token(text: str, expected: str | None) -> None:
    assert runner.parse_status(text) == expected


# ── AC-0007: worktree records ───────────────────────────────────────────────


def test_worktree_records_parse_with_the_main_worktree_first() -> None:
    raw = (
        b"worktree /r/main\0HEAD aaa\0branch refs/heads/main\0\0"
        b"worktree /r/with space\0HEAD bbb\0branch refs/heads/brief/b/one\0\0"
        b"worktree /r/gone\0HEAD ccc\0branch refs/heads/brief/b/two\0prunable gitdir file points\0\0"
        b"worktree /r/loose\0HEAD ddd\0detached\0\0"
    )
    records = runner.parse_worktrees(raw)
    assert [r.path for r in records] == ["/r/main", "/r/with space", "/r/gone", "/r/loose"]
    assert [r.branch for r in records] == [
        "refs/heads/main",
        "refs/heads/brief/b/one",
        "refs/heads/brief/b/two",
        "",
    ]
    assert [r.prunable for r in records] == [False, False, True, False]


# ── AC-0032: the stage map over canned supervisor answers ───────────────────


def _view(
    *,
    stage: str = "implementing",
    gate_pending: bool = False,
    terminal: bool = False,
    refusal: dict[str, Any] | None = None,
    ready: bool | None = None,
    readiness_refusal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    view: dict[str, Any] = {
        "run": {"stage": stage, "gate_pending": gate_pending, "refusal": {}},
        "terminal": terminal,
        "refusal": refusal or {},
    }
    if ready is not None:
        view["readiness"] = {"ready": ready}
        if readiness_refusal:
            view["readiness"]["refusal"] = readiness_refusal
    return view


def _refusal(code: str) -> dict[str, str]:
    return {"code": code, "owner": "owner", "detail": "d"}


@pytest.mark.parametrize(
    ("code", "payload", "stage"),
    [
        (0, _view(refusal=_refusal("no-approval")), "drafting"),
        (0, _view(refusal=_refusal("unsupported-ref-storage")), "refused"),
        (0, _view(refusal=_refusal("supervisor-changed")), "refused"),
        (0, _view(refusal=_refusal("attempt-residue")), "refused"),
        (0, _view(gate_pending=True, stage="human-decision"), "awaiting-decision"),
        (0, _view(stage="gating"), "gating"),
        (0, _view(stage="reviewing"), "reviewing"),
        (0, _view(stage="terminal", terminal=True, ready=True), "terminal"),
        (1, {"refusal": _refusal("supervisor-changed")}, "supervisor-changed"),
        (1, {"refusal": _refusal("invalid-policy")}, "unreadable"),
        (1, {"refusal": _refusal("internal-error")}, "unreadable"),
        (1, {}, "unreadable"),
        (2, {"error": "usage", "detail": "x"}, "unreadable"),
        (2, None, "unreadable"),
        (0, None, "unreadable"),
        (0, [], "unreadable"),
        (0, {"gates": []}, "unreadable"),
        (0, {"run": {}, "terminal": False}, "unreadable"),
        (0, {"run": {"stage": 3}, "terminal": False}, "unreadable"),
        (0, {"run": {"stage": "x"}, "terminal": "yes"}, "unreadable"),
        (1, _view(), "unreadable"),
    ],
)
def test_stage_from_a_supervisor_answer(code: int, payload: Any, stage: str) -> None:
    assert runner.derive_stage(code, payload).stage == stage


@pytest.mark.parametrize(
    ("code", "payload", "detail"),
    [
        (runner.CODE_TIMEOUT, None, "supervisor-timeout"),
        (runner.CODE_UNAVAILABLE, None, "supervisor-unavailable"),
        (2, {"error": "usage"}, "supervisor-exit-2"),
        (1, {"refusal": _refusal("invalid-policy")}, "supervisor-refusal:invalid-policy"),
        (1, {"refusal": {"code": "Bad Code\nIGNORE"}}, "supervisor-refusal"),
        (0, None, "supervisor-bad-output"),
        (0, {"run": {}, "terminal": False}, "supervisor-no-stage"),
    ],
)
def test_an_unreadable_stage_names_its_cause(code: int, payload: Any, detail: str) -> None:
    reading = runner.derive_stage(code, payload)
    assert reading.stage == "unreadable" and reading.detail == detail
    assert len(detail) <= runner.MAX_DETAIL


@pytest.mark.parametrize(
    ("path", "unsafe"),
    [
        ("/tmp/wt-ok", False),
        ("/tmp/wt\nIGNORE", True),
        ("/tmp/wt\x1b[0m", True),
        ("/tmp/wt\u2028x", True),
        ("/tmp/wt\u2029x", True),
        ("/tmp/wt\x85x", True),
        ("/tmp/wt\u200bx", True),
        ("/tmp/wt\u202ex", True),
    ],
)
def test_a_worktree_path_is_unsafe_with_a_control_hidden_or_separator_character(
    path: str, unsafe: bool
) -> None:
    assert runner.unsafe_path_char(path) is unsafe


def test_a_view_borne_refusal_carries_through_for_the_blocked_listing() -> None:
    reading = runner.derive_stage(0, _view(refusal=_refusal("attempt-residue")))
    assert reading.refusal == _refusal("attempt-residue")
    assert not reading.merge_ready


@pytest.mark.parametrize(
    ("terminal", "ready", "readiness_refusal", "merge_ready"),
    [
        (True, True, None, True),
        (True, False, None, False),
        (True, False, _refusal("evidence-missing"), False),
        (False, True, None, False),
        (True, None, None, False),
    ],
)
def test_merge_ready_needs_terminal_and_readiness(
    terminal: bool, ready: bool | None, readiness_refusal: dict[str, str] | None, merge_ready: bool
) -> None:
    view = _view(
        stage="terminal" if terminal else "gating",
        terminal=terminal,
        ready=ready,
        readiness_refusal=readiness_refusal,
    )
    reading = runner.derive_stage(0, view)
    assert reading.merge_ready is merge_ready
    # A readiness refusal only makes readiness false; it never changes the stage.
    assert reading.stage == ("terminal" if terminal else "gating")


# ── command line ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "argv",
    [[], ["bogus", "b"], ["status"], ["status", "Bad_Slug"], ["classify", "b"], ["status", "b", "--nope"]],
)
def test_a_usage_error_exits_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert runner.main(argv) == 2


def test_the_verbs_are_exactly_the_four_named() -> None:
    action = runner._parser()._subparsers._group_actions[0]  # type: ignore[union-attr]
    assert sorted(action.choices) == ["classify", "gates", "next", "status"]


# ── marker, gates join and the next decision, over canned rows ──────────────


def _row(slug: str, **kw: Any) -> Any:
    fields: dict[str, Any] = {
        "slice": slug, "spec_status": "Approved", "plan_status": "Approved", "worktree": None,
        "branch": f"brief/b/{slug}", "head": None, "stop": "none", "stage": None, "ready": False,
        "mode": None,
    }  # fmt: skip
    fields.update(kw)
    if fields["ready"] and fields["mode"] is None:
        fields["mode"] = "run"
    return runner.Row(**fields)


def _wt(slug: str, stage: str = "implementing", **kw: Any) -> Any:
    return _row(slug, worktree=f"/w/{slug}", head="a" * 40, stage=stage, **kw)


def test_the_marker_is_a_sha256_of_head_tree_and_canonical_gates() -> None:
    gates = [{"state": "pending", "a": 1}]
    marker = runner.row_marker("h", "t", gates)
    assert len(marker) == 64 and marker == runner.row_marker("h", "t", [{"a": 1, "state": "pending"}])
    assert marker != runner.row_marker("h2", "t", gates)
    assert marker != runner.row_marker("h", "t2", gates)
    assert marker != runner.row_marker("h", "t", [])
    assert runner.row_marker("h", "t", None) != runner.row_marker("h", "t", [])
    assert runner.row_marker("h", "t", None) == runner.row_marker("h", "t", None)


def test_a_joined_entry_adds_only_slice_and_worktree_and_sorts_undated_last() -> None:
    row = _wt(
        "s",
        gates=[
            {"state": "invalid"},
            {"state": "pending", "spec_dir": "docs/specs/b"},
            {"state": "stale", "spec_dir": "docs/specs/a"},
            {"state": "invalid", "record": "x.json"},
        ],
    )
    joined = runner.joined_gates(row)
    assert [e.get("spec_dir") for e in joined] == ["docs/specs/a", "docs/specs/b", None, None]
    assert [e.get("record") for e in joined[2:]] == [None, "x.json"]  # supervisor order kept
    assert all(set(e) - {"state", "spec_dir", "record"} == {"slice", "worktree"} for e in joined)


def test_unavailable_gates_join_as_one_entry() -> None:
    assert runner.joined_gates(_wt("s", gates=None)) == [
        {"slice": "s", "worktree": "/w/s", "state": "unavailable"}
    ]


def test_gates_output_shapes() -> None:
    def read(code: int, payload: Any) -> Any:
        runner.run_supervisor = lambda wt, *argv: (code, payload)
        return runner.read_gates("/w")

    saved = runner.run_supervisor
    try:
        assert read(0, {"gates": []}) == []
        assert read(0, {"gates": [{"state": "pending"}]}) == [{"state": "pending"}]
        for bad in (
            (1, {"gates": []}), (2, None), (0, None), (0, []), (0, {}), (0, {"gates": {}}),
            (0, {"gates": ["x"]}), (0, {"gates": [{"spec_dir": "d"}]}), (0, {"gates": [{"state": 1}]}),
        ):
            assert read(*bad) is None, bad
    finally:
        runner.run_supervisor = saved


def test_resume_comes_before_start_and_names_the_first_such_row() -> None:
    rows = [_wt("a", "reviewing"), _wt("b", "drafting"), _row("c", ready=True)]
    assert runner.decide_next(rows, 2) == {
        "kind": "resume-slice", "slice": "a", "worktree": "/w/a", "stage": "reviewing"
    }


@pytest.mark.parametrize("stage", ["admitted", "implementing", "gating", "reviewing", "drafting"])
def test_each_resumable_stage_is_resumed(stage: str) -> None:
    assert runner.decide_next([_wt("a", stage)], 2)["stage"] == stage


@pytest.mark.parametrize("stage", ["terminal", "awaiting-human", "other"])
def test_other_stages_are_not_resumed(stage: str) -> None:
    assert runner.decide_next([_wt("a", stage)], 2)["kind"] == "blocked"


@pytest.mark.parametrize("gates", [[{"state": "pending"}], [{"state": "stale"}], [{"state": "invalid"}], None])
def test_a_row_with_any_gate_entry_or_unavailable_gates_is_not_resumed(gates: Any) -> None:
    assert runner.decide_next([_wt("a", gates=gates)], 2)["kind"] != "resume-slice"


def test_pilot_rules_over_canned_rows() -> None:
    parked = _wt("a", gates=[{"state": "pending", "spec_dir": "d"}])
    ready = _row("b", ready=True)
    assert runner.decide_next([parked, ready], 2)["kind"] == "await-gates"  # pilot holds
    merged = _row("m", stop="merged", spec_status="Shipped")
    assert runner.decide_next([merged, parked, ready], 2) == {
        "kind": "start-slice", "slice": "b", "branch": "brief/b/b", "mode": "run",
        "spec_status": "Approved", "plan_status": "Approved",
    }  # fmt: skip
    merge_ready = _wt("w", "terminal", stop="merge-ready")
    assert runner.decide_next([merge_ready, ready], 2)["kind"] == "start-slice"  # hold ended
    assert runner.decide_next([_row("x"), ready], 2)["slice"] == "b"  # the first ready row


def test_the_cap_counts_worktree_rows_with_stop_none() -> None:
    parked = lambda s: _wt(s, gates=[{"state": "pending"}])  # noqa: E731
    merged = _row("m", stop="merged")
    ready = _row("r", ready=True)
    assert runner.decide_next([merged, parked("a"), ready], 2)["kind"] == "start-slice"
    assert runner.decide_next([merged, parked("a"), parked("b"), ready], 2)["kind"] == "await-gates"
    assert runner.decide_next([merged, parked("a"), ready], 1)["kind"] == "await-gates"
    done = _wt("d", "terminal", stop="merge-ready")  # a stopped row is not in flight
    assert runner.decide_next([done, parked("a"), parked("b"), ready], 3)["kind"] == "start-slice"
    assert runner.decide_next([merged, ready], 0)["kind"] == "blocked"  # an unreadable cap fails closed


def test_blocked_reasons_in_the_stated_order() -> None:
    both = lambda stage, **kw: _wt("x", stage, gates=[{"state": "stale"}], **kw)  # noqa: E731
    cases = [
        (both("unreadable"), "unreadable"),
        (both("supervisor-changed"), "supervisor-changed"),
        (both("refused", refusal={"code": "c", "owner": "o", "detail": "d"}), "refused"),
        (both("awaiting-decision"), "awaiting-decision"),
        (both("drafting"), "gate-not-clean"),
        (_wt("x", "terminal"), "terminal-not-ready"),
    ]
    for row, reason in cases:
        got = runner.decide_next([row], 2)
        assert got["kind"] == "blocked" and got["rows"][0]["reason"] == reason, reason
    refused = runner.decide_next(
        [_wt("x", "refused", refusal={"code": "c", "owner": "o", "detail": "d"})], 2
    )["rows"][0]
    assert refused == {"slice": "x", "reason": "refused", "code": "c", "owner": "o", "detail": "d"}


def test_a_ready_row_is_capped_before_it_is_held_by_the_pilot() -> None:
    pilot = _wt("p", "awaiting-decision")
    other = _wt("q", "awaiting-decision")
    ready = _row("r", ready=True)
    held = runner.decide_next([pilot, ready], 2)["rows"]
    assert [r["reason"] for r in held] == ["awaiting-decision", "pilot-in-flight"]
    capped = runner.decide_next([pilot, other, ready], 2)["rows"]
    assert [r["reason"] for r in capped] == ["awaiting-decision", "awaiting-decision", "in-flight-cap"]


def test_unstarted_rows_are_not_dispatchable_or_wait_for_an_earlier_row() -> None:
    rows = [
        _wt("a", "awaiting-decision"),
        _row("b", spec_status="Draft"),
        _row("c", spec_status=None),
        _row("d", spec_status="Implementing"),
        _row("e"),
    ]
    got = {r["slice"]: r["reason"] for r in runner.decide_next(rows, 2)["rows"]}
    assert got == {
        "a": "awaiting-decision", "b": "earlier-row-not-stopped", "c": "earlier-row-not-stopped",
        "d": "not-dispatchable", "e": "not-dispatchable",
    }  # fmt: skip


def test_await_gates_then_await_merge_then_complete() -> None:
    gate = {"state": "pending", "spec_dir": "d"}
    waiting = _wt("a", "drafting", gates=[gate])
    mr = _wt("b", "terminal", stop="merge-ready")
    merged = _row("m", stop="merged")
    got = runner.decide_next([waiting, mr, merged], 2)
    assert got["kind"] == "await-gates" and got["gates"] == runner.joined_gates(waiting)
    assert runner.decide_next([mr, merged], 2) == {"kind": "await-merge", "slices": ["b"]}
    assert runner.decide_next([merged, _row("n", stop="merged")], 2) == {"kind": "complete"}


# ── AC-0015: standing-orders format ─────────────────────────────────────────


def test_standing_orders_accept_a_numbered_list_with_blank_lines() -> None:
    assert runner.standing_orders_problem(b"1. First\n\n2. Second\n3. Third\n") is None
    assert runner.standing_orders_problem(b"") is None


@pytest.mark.parametrize(
    "data",
    [
        b"1. One\n3. Three\n",  # a gap
        b"2. Starts late\n",
        b"1. One\n   wrapped on\n2. Two\n",  # a wrapped line is refused, not joined
        b"1. One\nplain line\n",
        b"1.One\n",
        b"1. \n",
        b"01. One\n",
        "1. zero​width\n".encode(),  # hidden character
        b"1. one\r\n",  # carriage return
        b"1. one\x1b[2Jtwo\n",  # escape
        b"1. one\x7ftwo\n",  # delete
        "1. one\x85two\n".encode(),  # next line
        "1. one\u2028two\n".encode(),  # line separator
        "1. one\u2029two\n".encode(),  # paragraph separator
        "1. one\u200d\u200d\u200dtwo\n".encode(),  # a zero-width run over the lint's bound
        ("1. " + "x\u200d" * 40 + "\n").encode(),  # short joiner runs over the invisible budget
        b"1. one" + b" " * 9 + b"two\n",  # a whitespace run over the lint's bound
        b"1. " + b"x" * 16384 + b"\n",  # oversize
        b"1. \xff\xfe\n",  # not UTF-8
    ],
)
def test_standing_orders_refuse_a_bad_file(data: bytes) -> None:
    assert runner.standing_orders_problem(data) is not None


def test_standing_orders_accept_an_ordinary_numbered_list() -> None:
    lines = [f"{n}. Keep step {n} small, and say what changed (see `docs/x.md`)." for n in range(1, 13)]
    assert runner.standing_orders_problem(("\n".join(lines) + "\n").encode()) is None


def test_standing_orders_drop_only_the_lints_length_ceiling() -> None:
    lint = runner._lint_knowledge()
    text = "1. " + "x" * 5000 + "\n"
    assert len(text) > lint.FIELD_POLICY["body"]["lint_max"]
    ours = runner.standing_orders_problem(text.encode())
    assert ours is None
    # Any other lint problem on the same long text still refuses it.
    assert runner.standing_orders_problem((text + "2. a\x1bb\n").encode()) is not None


def test_standing_orders_at_the_size_limit_are_valid() -> None:
    data = b"1. " + b"x" * (16384 - 4) + b"\n"
    assert len(data) == 16384 and runner.standing_orders_problem(data) is None


# ── AC-0020: the classify table and its refusals ────────────────────────────

KNOWN = {
    "cap-hit": "split-task",
    "network": "retry",
    "tool-error": "retry-other-model",
    "stuck": "replace-worker",
}


@pytest.mark.parametrize("n", [0, 1, 2])
@pytest.mark.parametrize("cls", sorted(KNOWN))
def test_a_known_class_within_the_budget_gets_its_action(cls: str, n: int) -> None:
    assert runner.classify_action(cls, n, 2) == KNOWN[cls]


@pytest.mark.parametrize("cls", sorted(KNOWN))
def test_the_third_failure_abandons_whatever_the_known_class(cls: str) -> None:
    assert runner.classify_action(cls, 3, 2) == "abandon-and-replan"


@pytest.mark.parametrize("n", [0, 2, 3, 9])
def test_an_unknown_class_surfaces_to_a_human_at_every_count(n: int) -> None:
    assert runner.classify_action("gremlins", n, 2) == "surface-to-human"


def test_the_budget_edge_follows_the_policy_value() -> None:
    assert runner.classify_action("network", 1, 1) == "retry"
    assert runner.classify_action("network", 2, 1) == "abandon-and-replan"


def _crow(slug: str, worktree: str | None) -> Any:
    return runner.Row(slug, None, None, worktree, "b", None, "none", None, False, None)


def _status(tasks: Any, **extra: Any) -> tuple[int, Any]:
    return 0, {"run": {}, "terminal": False, "tasks": tasks, **extra}


def _classify(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[Any],
    answer: tuple[int, Any],
    slug: str = "alpha",
    task: str = "T1",
) -> dict[str, Any]:
    monkeypatch.setattr(runner, "run_supervisor", lambda wt, *argv: answer)
    monkeypatch.setattr(runner, "read_retry_budget", lambda root, base: 2)
    return runner.classify(Path(), "base", rows, slug, task, "network")  # type: ignore[no-any-return]


def _code(
    monkeypatch: pytest.MonkeyPatch, rows: list[Any], answer: tuple[int, Any], **kw: str
) -> str:
    with pytest.raises(runner.Refusal) as caught:
        _classify(monkeypatch, rows, answer, **kw)
    return str(caught.value.code)


def test_classify_reads_the_task_count_and_names_the_base(monkeypatch: pytest.MonkeyPatch) -> None:
    answer = _status([{"task_id": "T1", "failed_attempts": 2}])
    got = _classify(monkeypatch, [_crow("alpha", "/w")], answer)
    assert got == {"base": "base", "action": "retry", "failed_attempts": 2}


def test_classify_refuses_an_unknown_slice(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _code(monkeypatch, [_crow("alpha", "/w")], _status([]), slug="other") == "unknown-slice"


def test_classify_refuses_a_row_without_a_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _code(monkeypatch, [_crow("alpha", None)], _status([])) == "no-slice-worktree"


def test_classify_refuses_an_unknown_task(monkeypatch: pytest.MonkeyPatch) -> None:
    answer = _status([{"task_id": "T9", "failed_attempts": 0}])
    assert _code(monkeypatch, [_crow("alpha", "/w")], answer) == "unknown-task"


@pytest.mark.parametrize(
    "answer",
    [
        (2, None),
        (1, {"refusal": {"code": "x", "detail": "y"}}),
        (0, {"nonsense": True}),
        (0, {"run": {}, "terminal": False, "tasks": [], "refusal": {"code": "x", "detail": "y"}}),
        _status([{"task_id": "T1"}]),
    ],
    ids=["no-json", "refused", "not-a-view", "refusal-in-view", "no-count"],
)
def test_classify_refuses_an_unusable_status(
    monkeypatch: pytest.MonkeyPatch, answer: tuple[int, Any]
) -> None:
    assert _code(monkeypatch, [_crow("alpha", "/w")], answer) == "status-unavailable"


# ── AC-0022: the verb set ───────────────────────────────────────────────────


def test_the_parser_has_exactly_the_four_verbs() -> None:
    parser = runner._parser()
    choices = next(a.choices for a in parser._actions if getattr(a, "choices", None))
    assert sorted(choices) == ["classify", "gates", "next", "status"]
