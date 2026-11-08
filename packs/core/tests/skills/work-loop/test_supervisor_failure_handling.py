"""Blast radius, cancellation, the reprojection bound, and plan-change ordering.

Every test drives real Git through the ``run-concurrent`` verb with the fixture launcher. A
batch never names two tasks whose declared sets meet, so the tests that need a failed attempt
beside a running sibling that meets it replace the batch choice with one that names them
together: the cancellation path is defence in depth beyond what admission lets reach it.
Every timeout runs on the injected clock; nothing here waits in real time for one.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
# Each shared module by literal path, so every file this suite loads stays visibly in this pack.
_PATHS = {
    "launcher_support": _HERE / "launcher_support.py",
    "test_supervisor_integration": _HERE / "test_supervisor_integration.py",
}


def _load(name: str) -> ModuleType:
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _load("launcher_support")
ti = _load("test_supervisor_integration")
harness = ls.harness
L = ls.launcher_module
conc = ls.concurrent_module
integ = ti.integ
pytestmark = ls.sup.INTEGRATION

CALC, NOTE, THIRD = ti.CALC, ti.NOTE, "3\n"

# T2 reads what T1 writes, so the two meet; T3 meets neither.
MEETING_TRIPLE = ti.plan_of(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
    ("T2", "Plain note is written", "`calc.py`", "`plain.txt`", "none"),
    ("T3", "Third file is written", "`README.md`", "`third.txt`", "none"),
)
MEETING_PAIR = ti.plan_of(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
    ("T2", "Plain note is written", "`calc.py`", "`plain.txt`", "none"),
)
FAILS = {"access_raw": "garbage"}  # an access line that violates the schema: a failed attempt
T2_SCRIPT = {"reads": ["calc.py"], "write": {"plain.txt": NOTE}}


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> Any:
    yield
    ls.clear_kill_hook()
    harness.commit_module.set_kill_hook(None)
    integ.INTEGRATE_IN_COMPLETION_ORDER = False


def name_meeting_tasks_together(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every batch name each incomplete task, whether or not their declared sets meet."""

    def batch(ws: Any, state: Any, first: dict[str, Any]) -> list[dict[str, Any]]:
        limit = int(ws.policy["max_concurrent_attempts"])
        rest = [
            t for t in state.tasks
            if t is not first and not state.is_complete(t)
            and conc.read_record(ws, state.run_id, conc._rid(ws, state, t)) is None
        ]
        return [first, *rest][:limit]

    monkeypatch.setattr(conc, "_batch", batch)


def by_task(outcome: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a["task"].split("-")[0]: a for a in outcome["attempts"]}


def record_of(env: Any, prefix: str) -> dict[str, Any]:
    (found,) = [r for r in env.records() if r["task_id"].startswith(prefix)]
    return found


def records_of(env: Any, prefix: str) -> list[dict[str, Any]]:
    return [r for r in env.records() if r["task_id"].startswith(prefix)]


def complete_on_the_floor(env: Any, request: dict[str, Any], **files: str) -> None:
    for name, text in files.items():
        (env.repo / name).write_text(text, encoding="utf-8")
    code, admitted = env.report(request, gate={"passed": True})
    assert code == 0 and admitted["admitted"] == "implement", admitted


def status_attempts(env: Any) -> list[dict[str, Any]]:
    return env.run("status", ls.SPEC_DIR)[1]["concurrency"]["attempts"]  # type: ignore[no-any-return]


def journal_for(env: Any, outcome: str) -> list[dict[str, Any]]:
    return [j for j in ls.journal(env.repo) if j.get("outcome") == outcome]


def assert_group_dead(record: dict[str, Any]) -> None:
    assert ls.group_dead(int(record["pgid"]))


# ── blast radius (AC-0051) ──────────────────────────────────────────────────


def triple_script() -> dict[str, Any]:
    return {
        "per_task": {
            "calculator-answers": FAILS,
            "plain-note-is-written": {**T2_SCRIPT, "wait_for": "{log}/t2.go"},
            "third-file-is-written": {"write": {"third.txt": THIRD}},
        }
    }


def test_a_failed_attempt_reprojects_itself_and_the_sibling_that_meets_it_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name_meeting_tasks_together(monkeypatch)
    env = ti.make_env(
        tmp_path, monkeypatch, plan=MEETING_TRIPLE, script=triple_script(),
        policy={"max_concurrent_attempts": 3},
    )
    request = env.issued()
    assert len(request["tasks"]) == 3
    before = ti.head(env)
    code, payload = env.verb(request["request_id"])
    assert code == 0, payload
    outcomes = by_task(payload["run_concurrent"])
    assert outcomes["calculator"]["outcome"] == "floor"
    assert outcomes["calculator"]["reason"] == "access-schema"
    assert outcomes["plain"] == {
        "outcome": "cancelled", "reason": "sibling-failed", "task": outcomes["plain"]["task"]
    }
    assert outcomes["third"]["outcome"] == "held"  # the sibling that meets nothing is untouched
    assert ti.head(env) == before
    for record in env.records():
        assert_group_dead(record)
    cancelled = record_of(env, "plain")
    assert cancelled["reproject"] is True and not Path(cancelled["attempt_dir"]).exists()
    # status and the journal show the reprojection.
    shown = {a["task_id"].split("-")[0]: a for a in status_attempts(env)}
    assert shown["plain"]["reprojected"] is True and shown["calculator"]["reprojected"] is False
    (line,) = journal_for(env, "cancelled")
    assert line["reason"] == "sibling-failed" and line["reprojected"] is True
    code, admitted = env.report(request)
    assert code == 0 and admitted["admitted"] == "run-concurrent"
    # The failed task runs on the floor, and the cancelled one is projected again under a new
    # request; the unaffected sibling's result is still held, and lands behind it in floor order.
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task" and floor["task"]["title"].startswith("Calculator")
    complete_on_the_floor(env, floor, **{"calc.py": CALC})
    assert list((env.store() / "held").iterdir()) and not (env.repo / "third.txt").exists()
    again = env.next()["request"]
    assert again["kind"] == "run-concurrent" and again["request_id"].endswith(":r1")
    assert again["task"]["title"].startswith("Plain")
    (tmp_path / "log" / "t2.go").write_text("go", encoding="utf-8")
    assert env.verb(again["request_id"])[1]["run_concurrent"]["outcome"] == "landed"
    assert env.git("show", "HEAD:plain.txt") == NOTE
    assert env.git("show", "HEAD:third.txt") == THIRD and ls.git_clean(env.repo)


def test_a_conflicting_attempt_cancels_a_running_sibling_that_meets_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name_meeting_tasks_together(monkeypatch)
    script = {
        "per_task": {
            "calculator-answers": {"write": {"calc.py": CALC}},
            "plain-note-is-written": {**T2_SCRIPT, "never_access": True},
        }
    }
    env = ti.make_env(tmp_path, monkeypatch, plan=MEETING_PAIR, script=script)
    monkeypatch.setattr(
        integ, "apply_result",
        lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", ["calc.py"])),
    )
    request = env.issued()
    code, payload = env.verb(request["request_id"])
    outcomes = by_task(payload["run_concurrent"])
    assert outcomes["calculator"]["outcome"] == "conflict"
    assert outcomes["plain"]["outcome"] == "cancelled"
    assert record_of(env, "plain")["reproject"] is True
    assert record_of(env, "calculator")["state"] == "conflict"


# ── cancellation (AC-0052, AC-0053, AC-0054) ────────────────────────────────


def pair_script(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "per_task": {
            "calculator-answers": FAILS,
            "plain-note-is-written": {
                **T2_SCRIPT, "wait_for": "{log}/t2.go", **(extra or {}), "on_abort": "ignore",
            },
        }
    }


def test_a_cancelled_attempt_is_aborted_and_ended_before_its_task_runs_again_on_a_fresh_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name_meeting_tasks_together(monkeypatch)
    sent: list[str] = []
    original = L.send

    def spy(proc: Any, message: dict[str, Any]) -> bool:
        sent.append(message["type"])
        return original(proc, message)

    monkeypatch.setattr(L, "send", spy)
    env = ti.make_env(tmp_path, monkeypatch, plan=MEETING_PAIR, script=pair_script())
    request = env.issued()
    code, payload = env.verb(request["request_id"])
    assert code == 0, payload
    assert sent.count("abort") == 2  # the failed attempt's launcher and the cancelled one's
    first = record_of(env, "plain")
    assert first["state"] == "cancelled" and first["reproject"] is True
    assert_group_dead(first)
    assert not Path(first["attempt_dir"]).exists()
    floor = env.next()["request"]
    complete_on_the_floor(env, floor, **{"calc.py": CALC})
    again = env.next()["request"]
    assert again["kind"] == "run-concurrent" and again["request_id"].endswith(":r1")
    (tmp_path / "log" / "t2.go").write_text("go", encoding="utf-8")
    code, payload = env.verb(again["request_id"])
    assert code == 0 and payload["run_concurrent"]["outcome"] == "landed", payload
    second = [r for r in records_of(env, "plain") if r["state"] == "landed"][0]
    assert second["attempt_dir"] != first["attempt_dir"]  # a fresh directory, never reused
    assert second["attempt_id"] != first["attempt_id"]
    assert env.git("show", "HEAD:plain.txt") == NOTE


def stuck_group_after_record(
    env: Any, monkeypatch: pytest.MonkeyPatch, who: str, stuck: set[int]
) -> None:
    """Make *who*'s process group look alive to every check, and name it for cleanup."""
    original = L.group_alive

    def hook(name: str) -> None:
        if name == "launcher-recorded":
            for record in env.records():
                if who in record["task_id"] and isinstance(record.get("pgid"), int):
                    stuck.add(record["pgid"])

    harness.commit_module.set_kill_hook(hook)
    monkeypatch.setattr(L, "group_alive", lambda pgid: pgid in stuck or original(pgid))


def test_a_cancelled_attempt_whose_end_is_not_confirmed_goes_to_the_floor_as_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name_meeting_tasks_together(monkeypatch)
    clock = ls.ScriptedClock(sleep_step=5.0)  # each wait for the end moves the window along
    monkeypatch.setattr(L, "CLOCK", clock)
    env = ti.make_env(tmp_path, monkeypatch, plan=MEETING_PAIR, script=pair_script())
    stuck: set[int] = set()
    original_alive = L.group_alive
    stuck_group_after_record(env, monkeypatch, "plain", stuck)
    request = env.issued()
    try:
        code, payload = env.verb(request["request_id"])
    finally:
        for pgid in stuck:
            ls.kill_group(pgid)
    assert code == 0, payload
    outcomes = by_task(payload["run_concurrent"])
    assert outcomes["plain"]["outcome"] == "residue"
    held = record_of(env, "plain")
    assert held["state"] == "residue" and Path(held["attempt_dir"]).exists()
    assert not held.get("reproject") and not list((env.store() / "held").glob("*"))
    monkeypatch.setattr(L, "CLOCK", L._RealClock())
    monkeypatch.setattr(L, "group_alive", original_alive)
    ls.clear_kill_hook()
    complete_on_the_floor(env, env.next()["request"], **{"calc.py": CALC})
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task" and floor["task"]["title"].startswith("Plain")
    assert ls.journal(env.repo)[-1]["floor_reason"] == "sibling-failed"
    assert not [j for j in ls.journal(env.repo) if j.get("reprojected")]


def test_a_result_that_returns_after_its_cancellation_never_integrates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name_meeting_tasks_together(monkeypatch)
    flagged = threading.Event()

    def hook(name: str) -> None:
        if name == "sibling-cancelled":
            flagged.set()
        elif name == "access-read" and "plain-note" in threading.current_thread().name:
            # The sibling's access line is already in hand: let its cancellation land first.
            assert flagged.wait(60), "the sibling was never cancelled"

    harness.commit_module.set_kill_hook(hook)
    script = {
        "per_task": {
            "calculator-answers": {**FAILS, "touch": "{log}/t1.done"},
            "plain-note-is-written": {
                **T2_SCRIPT, "wait_for": "{log}/t1.done", "touch": "{log}/t2.sent",
            },
        }
    }
    env = ti.make_env(tmp_path, monkeypatch, plan=MEETING_PAIR, script=script)
    request = env.issued()
    before = ti.head(env)
    code, payload = env.verb(request["request_id"])
    assert code == 0, payload
    assert (tmp_path / "log" / "t2.sent").exists()  # the cancelled attempt did send its result
    outcomes = by_task(payload["run_concurrent"])
    assert outcomes["plain"]["outcome"] == "cancelled"
    assert ti.head(env) == before and not list((env.store() / "held").glob("*"))
    assert not list((env.store() / "integrations").glob("*"))
    assert record_of(env, "plain")["state"] == "cancelled"
    assert not (env.repo / "plain.txt").exists()
    refs = env.git("for-each-ref", "--format=%(refname)", "refs/agentbundle/delivery")
    assert "/held/" not in refs


# ── the attempt timeout (AC-0068) ───────────────────────────────────────────


def silent_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: Any, *, also: Any = None, **policy: Any
) -> Any:
    monkeypatch.setattr(L, "CLOCK", clock)
    env = ti.make_env(
        tmp_path, monkeypatch, plan=ls.ONE_TASK,
        script={"wait_for": "{log}/go", "on_abort": "ignore"},
        policy={"attempt_timeout_seconds": 60, **policy},
    )

    def hook(name: str) -> None:
        if name == "released":
            clock.arm(100.0, after=1)  # the second reading after the release passes the deadline
        if also is not None:
            also(name)

    harness.commit_module.set_kill_hook(hook)
    return env


def test_an_attempt_silent_past_its_timeout_is_cancelled_and_projected_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = silent_env(tmp_path, monkeypatch, ls.ScriptedClock())
    request = env.issued()
    before = ti.head(env)
    code, payload = env.verb(request["request_id"])
    outcome = payload["run_concurrent"]
    assert outcome["outcome"] == "cancelled" and outcome["reason"] == "access-timeout"
    (record,) = env.records()
    assert record["reproject"] is True and not Path(record["attempt_dir"]).exists()
    assert_group_dead(record)
    assert ti.head(env) == before and not (env.repo / "calc.py").exists()
    assert not list((env.store() / "held").glob("*"))
    monkeypatch.setattr(L, "CLOCK", L._RealClock())
    again = env.next()["request"]
    assert again["kind"] == "run-concurrent" and again["request_id"].endswith(":r1")
    assert ls.journal(env.repo)[-2]["reprojected"] is True


def test_an_attempt_silent_past_its_timeout_whose_end_never_confirms_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stuck: set[int] = set()
    holder: list[Any] = []

    def note(name: str) -> None:
        if name == "launcher-recorded":
            stuck.update(r["pgid"] for r in holder[0].records() if isinstance(r.get("pgid"), int))

    env = silent_env(tmp_path, monkeypatch, ls.ScriptedClock(sleep_step=5.0), also=note)
    holder.append(env)
    request = env.issued()
    original = L.group_alive
    monkeypatch.setattr(L, "group_alive", lambda pgid: pgid in stuck or original(pgid))
    try:
        code, payload = env.verb(request["request_id"])
    finally:
        for pgid in stuck:
            ls.kill_group(pgid)
    assert payload["run_concurrent"]["outcome"] == "residue"
    (record,) = env.records()
    assert record["state"] == "residue" and Path(record["attempt_dir"]).exists()
    assert not record.get("reproject") and not (env.repo / "calc.py").exists()
    monkeypatch.setattr(L, "CLOCK", L._RealClock())
    monkeypatch.setattr(L, "group_alive", original)
    ls.clear_kill_hook()
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == "access-timeout"


# ── the reprojection bound (AC-0055, AC-0056) ───────────────────────────────


def refuse_every_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        integ, "apply_result",
        lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", ["calc.py"])),
    )


def test_a_task_that_conflicts_the_bound_many_times_runs_its_next_attempt_on_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ti.make_env(
        tmp_path, monkeypatch, plan=ls.ONE_TASK, policy={"reprojection_bound": 2}
    )
    refuse_every_apply(monkeypatch)
    request = env.issued()
    assert env.verb(request["request_id"])[1]["run_concurrent"]["outcome"] == "conflict"
    request = env.next()["request"]
    assert request["kind"] == "run-concurrent" and request["request_id"].endswith(":r1")
    assert env.verb(request["request_id"])[1]["run_concurrent"]["outcome"] == "conflict"
    floor = env.next()
    assert floor["request"]["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == "reprojection-bound"
    # Every reprojection is in the journal and in status.
    assert len(journal_for(env, "conflict")) == 2
    assert [a["reprojected"] for a in status_attempts(env)] == [True, True]


def test_a_cancellation_and_a_conflict_count_toward_the_same_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = ls.ScriptedClock()
    env = silent_env(tmp_path, monkeypatch, clock, reprojection_bound=2)
    request = env.issued()
    assert env.verb(request["request_id"])[1]["run_concurrent"]["outcome"] == "cancelled"
    monkeypatch.setattr(L, "CLOCK", L._RealClock())
    ls.clear_kill_hook()
    second = env.next()["request"]
    assert second["request_id"].endswith(":r1")
    (tmp_path / "log" / "go").write_text("go", encoding="utf-8")
    refuse_every_apply(monkeypatch)
    assert env.verb(second["request_id"])[1]["run_concurrent"]["outcome"] == "conflict"
    floor = env.next()
    assert floor["request"]["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == "reprojection-bound"
    assert sorted((a["state"], a["reprojected"]) for a in status_attempts(env)) == [
        ("cancelled", True), ("conflict", True),
    ]
    assert [j["outcome"] for j in ls.journal(env.repo) if j.get("reprojected")] == [
        "cancelled", "conflict",
    ]


# ── plan changes (AC-0057) ──────────────────────────────────────────────────


def edit_plan(env: Any, text: str) -> None:
    path = env.repo / ls.SPEC_DIR / "plan.md"
    path.write_text(path.read_text("utf-8").replace("Build it.", text), encoding="utf-8")


def held_refs(env: Any) -> str:
    return str(env.git("for-each-ref", "--format=%(refname)", "refs/agentbundle/delivery"))


def test_a_replan_waits_for_the_open_attempts_then_discards_held_results_without_counting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = {"per_task": {"calculator-answers": FAILS, "plain-note-is-written": {
        "write": {"plain.txt": NOTE}}}}
    env = ti.make_env(
        tmp_path, monkeypatch, plan=ti.PAIR, script=script, policy={"reprojection_bound": 1}
    )
    request = env.issued()
    base = ti.head(env)
    # While the request is open the edit is residue, nothing is committed, and nothing is lost.
    edit_plan(env, "Build it, and say so.")
    code, refused = env.run("next", ls.SPEC_DIR)
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue"
    assert ti.head(env) == base and "replan" not in env.git("log", "--format=%s")
    env.git("checkout", "--", f"{ls.SPEC_DIR}/plan.md")
    assert env.next()["request"]["request_id"] == request["request_id"]  # the refusal clears
    code, payload = env.verb(request["request_id"])
    outcomes = by_task(payload["run_concurrent"])
    assert outcomes["calculator"]["outcome"] == "floor" and outcomes["plain"]["outcome"] == "held"
    assert env.report(request)[0] == 0
    (held,) = (env.store() / "held").iterdir()
    assert "/held/" in held_refs(env)
    # No attempt is open now: the replan is admitted, and the held result goes with it.
    edit_plan(env, "Build it, and say so.")
    floor = env.next()["request"]
    assert "replan" in env.git("log", "--format=%s") and floor["kind"] == "implement-task"
    assert not list((env.store() / "held").iterdir()) and "/held/" not in held_refs(env)
    discarded = record_of(env, "plain")
    assert discarded["state"] == "discarded" and discarded["reason"] == "plan-changed"
    assert [j["reason"] for j in journal_for(env, "discarded")] == ["plan-changed"]
    assert [a["state"] for a in status_attempts(env) if a["state"] == "discarded"] == ["discarded"]
    assert not any(a["reprojected"] for a in status_attempts(env))
    # The discarded task is projected again under a new request, though the bound is one:
    # a discard does not count toward it.
    complete_on_the_floor(env, floor, **{"calc.py": CALC})
    again = env.next()["request"]
    assert again["kind"] == "run-concurrent" and again["request_id"].endswith(":d1")
    assert not (env.repo / "plain.txt").exists()


# ── evidence ordering (AC-0058) ─────────────────────────────────────────────


def test_no_gate_review_or_evidence_issues_while_a_result_is_held_and_each_names_a_held_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = {"per_task": {
        "calculator-answers": FAILS, "plain-note-is-written": {"write": {"plain.txt": NOTE}},
    }}
    env = ti.make_env(tmp_path, monkeypatch, plan=ti.PAIR, script=script)
    request = env.issued()
    assert env.verb(request["request_id"])[0] == 0
    assert env.report(request)[0] == 0
    assert list((env.store() / "held").iterdir())
    evidence = (env.repo / ls.SPEC_DIR / "delivery" / "evidence.jsonl")
    receipts = evidence.read_text("utf-8") if evidence.exists() else ""
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"  # not run-gates, review-role, or any receipt
    assert (evidence.read_text("utf-8") if evidence.exists() else "") == receipts
    assert env.run("status", ls.SPEC_DIR)[1]["request"]["kind"] == "implement-task"
    complete_on_the_floor(env, floor, **{"calc.py": CALC})
    assert not list((env.store() / "held").iterdir())
    after = env.next()["request"]
    assert after["kind"] == "run-gates"
    tree = set(env.git("rev-list", "HEAD").split())
    gating = [j for j in ls.journal(env.repo) if j["kind"] in ("run-gates", "review-role")]
    assert gating and all(j["head"] in tree for j in gating)
    assert all(j["head"] in tree for j in ls.journal(env.repo))
    # Every receipt the supervisor wrote was written by a commit the product ref holds.
    log = env.git("log", "--format=%H", "--", f"{ls.SPEC_DIR}/delivery/evidence.jsonl")
    assert set(log.split()) <= tree


def test_a_held_result_with_every_task_complete_stops_the_run_rather_than_gating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ti.make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    request = env.issued()
    assert env.verb(request["request_id"])[1]["run_concurrent"]["outcome"] == "landed"
    assert env.report(request)[0] == 0
    (landed,) = env.records()
    stray = {**landed, "attempt_id": "att-" + "0" * 16, "request_id": "conc:stray"}
    result = type("R", (), {
        "tree": env.git("rev-parse", "HEAD^{tree}").strip(), "access_sha": "0" * 64,
        "access_defect": None, "attested_reads": [], "attested_writes": [],
    })()
    ws = harness.workspace(env.repo)
    integ.hold(ws, landed["run_id"], stray, result, "impl:stray")
    code, refused = env.run("next", ls.SPEC_DIR)
    assert code == 1 and refused["refusal"]["code"] == "no-progress"
    assert "run-gates" not in json.dumps(refused)
    assert (env.store() / "held").exists()
