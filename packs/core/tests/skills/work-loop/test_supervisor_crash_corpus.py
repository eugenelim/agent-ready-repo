"""VI-4901: the crash corpus on the real supervisor modules.

AC-0015, AC-0016, AC-0017, AC-0018, AC-0026, AC-0032. A synthetic three-task
code run — one TDD task, one task declaring an external effect, one plain task
whose first gate fails — with one review round carrying a finding, run once
uninterrupted and then once per variant: killed at each kill point, the
journal deleted at each kill point, and four live-lease and rebase scenarios.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

pytestmark = sup.INTEGRATION
# The event envelope's required fields and their types; the roster validates
# emitted lines against the canonical schema itself.
EVENT_FIELDS = {"seq": int, "run_id": str, "spec": str, "from": str, "event": str, "to": str,
                "at": str, "schema": int, "step_id": str, "awaiting_input": bool}
ATTEMPT_KINDS = ("write-stub", "implement-task", "run-gates", "review-role", "assess-finding")
STEP_KINDS = {"approval", "replan", "stub", "red", "implement", "evidence", "gate-fail", "review",
              "effect-intent", "effect-dispatch", "effect-receipt", "claim", "resolution",
              "terminal"}
RUN_FIELDS = {"run_id", "active", "stage", "gate_pending", "gate_question", "refusal"}
STAGES = {"admitted", "implementing", "gating", "reviewing", "awaiting-human", "terminal"}
# Kill points in the uninterrupted run: 13 steps x (built, moved, synced, event),
# 11 journal appends, and 1 effect dispatch. The reviewer-selection exchange is
# one of those steps and one of those appends.
BOUNDARIES = 64


class Recorder:
    """Counts kill points, crashes or deletes the journal at one, and checks the index."""

    def __init__(self, repo: Path, *, kill_at: int = 0, delete_at: int = 0) -> None:
        self.repo, self.kill_at, self.delete_at = repo, kill_at, delete_at
        self.seen: list[str] = []
        self.staged_after_sync: list[list[str]] = []

    def __call__(self, name: str) -> None:
        self.seen.append(name)
        n = len(self.seen)
        if name == "synced":
            staged = h.git(self.repo, "diff", "--cached", "--name-only").split()
            if staged:
                self.staged_after_sync.append(staged)
        if n == self.delete_at:
            (self.repo / h.SPEC_DIR / ".supervisor" / "journal.jsonl").unlink(missing_ok=True)
        if n == self.kill_at:
            raise h.Crash(name)


def _check_run_json(repo: Path, payload: dict[str, Any], problems: list[str]) -> None:
    run = json.loads((repo / h.SPEC_DIR / ".supervisor" / "run.json").read_text("utf-8"))
    if set(run) != RUN_FIELDS or run["stage"] not in STAGES:
        problems.append(f"run.json fields {sorted(run)}")
        return
    request = payload.get("request")
    if payload.get("terminal"):
        expected = ("terminal", False, False)
    elif "refusal" in payload:
        expected = ("awaiting-human", True, False)
    else:
        assert request is not None
        expected = (request["stage"], True, request["kind"] == "human-decision")
    if (run["stage"], run["active"], run["gate_pending"]) != expected:
        problems.append(f"run.json {run} for {payload}")


def run_variant(tmp: Path, *, kill_at: int = 0, delete_at: int = 0,
                between: Callable[..., None] | None = None) -> dict[str, Any]:
    repo = h.make_repo(tmp)
    recorder = Recorder(repo, kill_at=kill_at, delete_at=delete_at)
    h.commit_module.set_kill_hook(recorder)
    problems: list[str] = []
    log: list[dict[str, Any]] = []
    crashes = 0
    try:
        for _ in range(4):
            controller = h.Controller(repo, tmp / "effects.log", between=between)
            original_cli = h.run_cli

            def checked(r: Path, *argv: str, _orig: Any = original_cli) -> tuple[int, dict]:
                code, payload = _orig(r, *argv)
                if argv[0] == "next":
                    _check_run_json(r, payload, problems)
                return code, payload

            h.run_cli = checked
            try:
                code, started = h.start(repo)
                assert code == 0, started
                end = controller.drive()
                log.extend(controller.log)
                break
            except h.Crash:
                crashes += 1
                log.extend(controller.log)
            finally:
                h.run_cli = original_cli
        else:
            raise AssertionError("the run did not finish after restarts")
    finally:
        h.commit_module.set_kill_hook(None)
    return summarize(repo, tmp / "effects.log", end, log, recorder, problems, crashes)


def _normalize(record: Any) -> Any:
    if isinstance(record, dict):
        return {k: ("<t>" if k in ("at", "timestamp") else _normalize(v)) for k, v in record.items()}
    if isinstance(record, list):
        return [_normalize(v) for v in record]
    return record


def _unfingerprinted(record: Any) -> Any:
    if isinstance(record, dict):
        return {k: ("<fp>" if "fingerprint" in k or k in ("review_subject_id", "receipt_id")
                    else _unfingerprinted(v)) for k, v in record.items()}
    if isinstance(record, list):
        return [_unfingerprinted(v) for v in record]
    return record


def summarize(repo: Path, effect_log: Path, end: dict[str, Any], log: list[dict[str, Any]],
              recorder: Recorder, problems: list[str], crashes: int) -> dict[str, Any]:
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    commits = ws.git.supervisor_commits(run_id)
    done = []
    for c in commits:
        if c.operation == "implement":
            tree = [line for line in h.git(repo, "ls-tree", "-r", c.sha).splitlines()
                    if f"{h.SPEC_DIR}/delivery/" not in line]
            done.append((c.trailers["Supervisor-Task"], c.trailers["Supervisor-Task-Revision"],
                         "\n".join(tree)))
    delivery = {}
    for name in ("approvals.jsonl", "effect-resolutions.jsonl"):
        lines = ws.records(name)
        delivery[name] = [_normalize(r) for r in lines if r.get("entry") != "dispatch"]
    es = h.loop.sibling("_evidence_store.py")
    frames = es.replay_admitted_frames(ws.evidence_bytes())["frames"]
    delivery["evidence.jsonl"] = [_normalize(records) for _tx, records in frames]
    steps = [c.step for c in commits]
    events_path = repo / ".loop-run" / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text("utf-8").splitlines()]
    events_ok = (
        sorted(e["step_id"] for e in events) == sorted(steps)
        and len({e["step_id"] for e in events}) == len(events)
        and all(set(e) == set(EVENT_FIELDS) for e in events)
        and all(isinstance(e[k], kind) and (kind is not str or e[k])
                for e in events for k, kind in EVENT_FIELDS.items())
        and all(e["event"] in STEP_KINDS for e in events)
        and all(c.operation in STEP_KINDS for c in commits)
    )
    dispatched = effect_log.read_text("utf-8").split() if effect_log.exists() else []
    working_matches_head = all(
        (repo / ws.git.delivery_rel / name).read_bytes()
        == ws.git.show(f"{ws.git.delivery_rel}/{name}")
        for name in ws.git.delivery_names()
    )
    attempts: list[str] = []
    for payload in log:
        request = payload.get("request") or {}
        if request.get("kind") in ATTEMPT_KINDS and request["request_id"] not in attempts:
            attempts.append(request["request_id"])
    _, view = h.run_cli(repo, "status", h.SPEC_DIR, "--json")
    return {
        "working_matches_head": working_matches_head,
        "attempts": attempts,
        "retry_count": view["retry_count"],
        "end": "terminal" if end.get("terminal") else json.dumps(end)[:300],
        "done": done,
        "delivery": delivery,
        "effects": dict(collections.Counter(dispatched)),
        "decisions": [p["request"]["reason"] for p in log
                      if p.get("request", {}).get("kind") == "human-decision"],
        "events_ok": events_ok,
        "staged_after_sync": recorder.staged_after_sync,
        "run_json_problems": problems,
        "seen": recorder.seen,
        "crashes": crashes,
        "log": log,
        "repo": repo,
    }


def assert_converged(base: dict[str, Any], run: dict[str, Any], *, trees: bool = True) -> None:
    assert run["end"] == "terminal"
    if trees:
        assert run["done"] == base["done"]
    else:
        assert [d[:2] for d in run["done"]] == [d[:2] for d in base["done"]]
    if trees:
        assert run["delivery"] == base["delivery"]
    else:
        # A rebase onto new upstream content changes every product-derived
        # fingerprint; the records must otherwise be the same.
        assert _unfingerprinted(run["delivery"]) == _unfingerprinted(base["delivery"])
    assert run["effects"] == base["effects"] == {next(iter(base["effects"])): 1}
    assert run["decisions"] == base["decisions"]
    assert run["events_ok"]
    assert run["working_matches_head"]
    assert run["retry_count"] == base["retry_count"] == 1
    if trees:
        assert run["attempts"] == base["attempts"]
    assert run["staged_after_sync"] == []
    assert run["run_json_problems"] == []


@pytest.fixture(scope="module")
def baseline(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    return run_variant(tmp_path_factory.mktemp("baseline"))


def test_uninterrupted_run_reaches_terminal(baseline: dict[str, Any]) -> None:
    assert baseline["end"] == "terminal"
    assert len(baseline["done"]) == 3
    assert baseline["decisions"] == []
    assert baseline["events_ok"]
    assert baseline["staged_after_sync"] == []
    assert baseline["run_json_problems"] == []
    assert len(baseline["seen"]) == BOUNDARIES, collections.Counter(baseline["seen"])


@pytest.mark.parametrize("mode", ["kill", "delete"])
@pytest.mark.parametrize("point", range(1, BOUNDARIES + 1))
def test_variant_converges(baseline: dict[str, Any], tmp_path: Path, mode: str,
                           point: int) -> None:
    run = run_variant(tmp_path, **({"kill_at": point} if mode == "kill" else {"delete_at": point}))
    assert run["crashes"] == (1 if mode == "kill" else 0)
    assert_converged(baseline, run)


def _first(kind: str, title: str) -> Callable[[dict[str, Any]], bool]:
    return lambda r: r["kind"] == kind and r.get("task", {}).get("title", "").startswith(title)


def test_journal_deleted_during_a_live_lease(baseline: dict[str, Any], tmp_path: Path) -> None:
    seen: list[bool] = []

    def between(c: h.Controller, request: dict[str, Any], phase: str) -> None:
        if phase == "worked" and _first("implement-task", "Release")(request) and not seen:
            (c.repo / h.SPEC_DIR / ".supervisor" / "journal.jsonl").unlink()
            _, again = h.run_cli(c.repo, "next", h.SPEC_DIR)
            seen.append(again["request"]["request_id"] == request["request_id"])

    assert_converged(baseline, run_variant(tmp_path, between=between))
    assert seen == [True]


def test_supervisor_commit_during_a_live_lease(baseline: dict[str, Any], tmp_path: Path) -> None:
    edited: list[bool] = []

    def between(c: h.Controller, request: dict[str, Any], phase: str) -> None:
        if phase == "worked" and _first("implement-task", "Release")(request) and not edited:
            spec = c.repo / h.SPEC_DIR / "spec.md"
            spec.write_text(spec.read_text("utf-8").replace(
                "that answers.", "that answers quickly."), "utf-8")
            _, again = h.run_cli(c.repo, "next", h.SPEC_DIR)
            edited.append(again["request"]["request_id"] == request["request_id"])

    run = run_variant(tmp_path, between=between)
    assert edited == [True]
    ws = h.workspace(run["repo"])
    commits = ws.git.supervisor_commits(ws.approvals()[0]["run_id"])
    replans = [c for c in commits if c.operation == "replan"]
    assert len(replans) == 1
    assert ws.git.touched_paths(replans[0].sha) == [f"{h.SPEC_DIR}/spec.md"]
    release = next(c for c in commits if c.operation == "implement"
                   and c.trailers["Supervisor-Task"].startswith("release"))
    assert f"{h.SPEC_DIR}/spec.md" not in ws.git.touched_paths(release.sha)
    assert [d[:2] for d in run["done"]] == [d[:2] for d in baseline["done"]]
    assert run["effects"] == baseline["effects"]
    assert run["events_ok"] and run["staged_after_sync"] == []


def test_next_during_a_live_lease_with_worker_files(baseline: dict[str, Any],
                                                    tmp_path: Path) -> None:
    checks: list[tuple[bool, bool]] = []

    def between(c: h.Controller, request: dict[str, Any], phase: str) -> None:
        if phase == "worked" and request["kind"] == "implement-task" and request["attempt"] == 2:
            before = h.git(c.repo, "status", "--porcelain", "--ignored")
            head = h.git(c.repo, "rev-parse", "HEAD")
            _, again = h.run_cli(c.repo, "next", h.SPEC_DIR)
            checks.append((again["request"] == request,
                           before == h.git(c.repo, "status", "--porcelain", "--ignored")
                           and head == h.git(c.repo, "rev-parse", "HEAD")))

    assert_converged(baseline, run_variant(tmp_path, between=between))
    assert checks == [(True, True)]


def test_rebase_preserving_messages_converges(baseline: dict[str, Any], tmp_path: Path) -> None:
    rebased: list[bool] = []

    def between(c: h.Controller, request: dict[str, Any], phase: str) -> None:
        if phase == "reported" and _first("implement-task", "Calculator")(request) and not rebased:
            root = h.git(c.repo, "rev-list", "--max-parents=0", "HEAD").strip()
            h.git(c.repo, "checkout", "-q", "-b", "upstream", root)
            (c.repo / "OTHER.md").write_text("upstream\n", "utf-8")
            h.git(c.repo, "add", "OTHER.md")
            h.git(c.repo, "commit", "-q", "-m", "unrelated upstream change")
            h.git(c.repo, "checkout", "-q", "main")
            h.git(c.repo, "rebase", "-q", "upstream")
            rebased.append(True)

    run = run_variant(tmp_path, between=between)
    assert rebased == [True]
    assert_converged(baseline, run, trees=False)
