"""VI-4901 and VI-0501: the crash corpus on the real supervisor modules.

AC-0015, AC-0016, AC-0017, AC-0018, AC-0026, AC-0032; and, for the product ref,
AC-0007 and AC-0017. A synthetic three-task
code run — one TDD task, one task declaring an external effect, one plain task
whose first gate fails — with one review round carrying a finding, run once
uninterrupted and then once per variant: killed at each kill point, the
journal deleted at each kill point, and four live-lease and rebase scenarios.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import subprocess
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
STEP_KINDS = {"approval", "replan", "reanchor", "stub", "red", "implement", "evidence", "gate-fail", "review",
              "effect-intent", "effect-dispatch", "effect-receipt", "claim", "resolution",
              "terminal"}
RUN_FIELDS = {"run_id", "active", "stage", "gate_pending", "gate_question", "refusal"}
STAGES = {"admitted", "implementing", "gating", "reviewing", "awaiting-human", "terminal"}
# Kill points in the uninterrupted run: 13 steps x (built, refs moved, made
# recorded, synced, event), 11 journal appends, and 1 effect dispatch. The
# reviewer-selection exchange is one of those steps and one of those appends.
BOUNDARIES = 78


def _run_store(repo: Path) -> Path | None:
    """The run's store directory (never a leftover temporary one), or None before it exists."""
    base = repo / ".git" / "agentbundle-supervisor"
    runs = [p for p in base.iterdir() if p.name.startswith("run-")] if base.exists() else []
    assert len(runs) <= 1
    return runs[0] if runs else None


def _rev(repo: Path, name: str) -> str:
    done = subprocess.run(["git", "rev-parse", "--verify", "-q", name], cwd=repo,
                          capture_output=True, text=True, check=False)
    return done.stdout.strip()


def _manifest(repo: Path, revision: str) -> dict[str, str]:
    pairs = {}
    for line in h.git(repo, "ls-tree", "-r", revision).splitlines():
        meta, path = line.split("\t", 1)
        pairs[path] = meta.split()[2]
    return {p: o for p, o in pairs.items() if not p.startswith(h.SPEC_DIR + "/")}


def assert_three_way_parity(repo: Path) -> None:
    """The working tree's tracked files, the HEAD subject, and the product-ref subject agree."""
    store = _run_store(repo)
    assert store is not None
    name = json.loads((store / "product-ref").read_text("utf-8"))["name"]
    working = {
        p: h.git(repo, "hash-object", p).strip()
        for p in h.git(repo, "ls-files").splitlines()
        if not p.startswith(h.SPEC_DIR + "/") and (repo / p).exists()
    }
    assert _rev(repo, name) == _rev(repo, "HEAD")
    assert _manifest(repo, "HEAD") == _manifest(repo, name) == working


STEP_POINTS = ("refs-moved", "made-recorded", "synced")
# The recorder of each repository under test, so a diversion can read where it struck.
_RECORDERS: dict[Path, Recorder] = {}


class Recorder:
    """Counts kill points, crashes or deletes the journal at one, and checks the index."""

    def __init__(self, repo: Path, *, kill_at: int = 0, delete_at: int = 0) -> None:
        self.repo, self.kill_at, self.delete_at = repo, kill_at, delete_at
        self.seen: list[str] = []
        # The operation of the step in flight at each kill point, "" outside a step.
        self.ops: list[str] = []
        self._op = ""
        self.staged_after_sync: list[list[str]] = []

    def check_product_ref(self, name: str) -> None:
        """At every kill point the ref names the commit before or after the write in flight."""
        store = _run_store(self.repo)
        if store is None or not (store / "product-ref").exists():
            return
        record = json.loads((store / "product-ref").read_text("utf-8"))
        value = _rev(self.repo, record["name"])
        head = _rev(self.repo, "HEAD")
        if name == "refs-moved":
            # After the transaction, before the run recorded it: past the record.
            assert value != record["recorded"] and value == head, (name, record)
        elif name in ("commit-built", "made-recorded", "synced"):
            assert value == record["recorded"], (name, record)
        else:
            # Between steps, or while an earlier cut-off step awaits the owner: the ref is
            # at the record, or at the unrecorded commit whose parent is the record.
            assert value == record["recorded"] or _rev(
                self.repo, f"{value}^") == record["recorded"], (name, record)
        if name in ("made-recorded", "synced"):
            assert h.git(self.repo, "symbolic-ref", "HEAD").strip() == "refs/heads/main"
            assert value == head == record["recorded"]

    def _operation(self) -> str:
        """The operation trailer of the commit ``HEAD`` was just moved to."""
        body = h.git(self.repo, "log", "-1", "--format=%B", "HEAD")
        return next((x.split(": ", 1)[1] for x in body.splitlines()
                     if x.startswith("Supervisor-Operation: ")), "")

    def __call__(self, name: str) -> None:
        self.seen.append(name)
        if name == "refs-moved":
            self._op = self._operation()
        self.ops.append(self._op if name in STEP_POINTS else "")
        if name == "synced":
            self._op = ""
        n = len(self.seen)
        self.check_product_ref(name)
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


def adopt(c: h.Controller, request: dict[str, Any]) -> bool:
    """Answer a history-adoption decision the way the owner's controller would.

    A step cut off after its refs moved is not adopted (it changes delivery/): both refs
    go back to the recorded value and the step is rebuilt. Other history is adopted.
    """
    if request.get("reason") != "history-adoption":
        return False
    if "a step this run never recorded" in request["question"]:
        store = _run_store(c.repo)
        assert store is not None
        record = json.loads((store / "product-ref").read_text("utf-8"))
        h.git(c.repo, "update-ref", "--no-deref", record["name"], record["recorded"])
        h.git(c.repo, "reset", "-q", "--soft", record["recorded"])
        return True
    code, out = c.report({
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": "human-decision",
        "decision": {"decision": "adopt-history", "authority_ref": "owner:0123456789ab",
                     "commit": request["head_commit"]},
    })
    assert code == 0, out
    return True


def restore_cut_off_step(repo: Path) -> bool:
    """The owner's second exit for a step the run never recorded: both refs back, step rebuilt."""
    store = _run_store(repo)
    assert store is not None
    record = json.loads((store / "product-ref").read_text("utf-8"))
    if {_rev(repo, record["name"]), _rev(repo, "HEAD")} == {record["recorded"]}:
        return False
    h.git(repo, "update-ref", "--no-deref", record["name"], record["recorded"])
    h.git(repo, "reset", "-q", "--soft", record["recorded"])
    return True


def resumed_parity(repo: Path, *, allow_diverged: bool) -> None:
    """After a resumption the supervisor's repair has run: the three manifests agree.

    The exception is a kill between a step's transaction and its recording: the ref or
    ``HEAD`` names a commit the run never recorded, which is the owner's decision, not a
    state to repair. The adoption scenario may also still hold history awaiting adoption.
    """
    store = _run_store(repo)
    assert store is not None
    record = json.loads((store / "product-ref").read_text("utf-8"))
    ref, head = _rev(repo, record["name"]), _rev(repo, "HEAD")
    if ref != record["recorded"] or (allow_diverged and head != ref):
        return
    assert_three_way_parity(repo)


def run_variant(tmp: Path, *, kill_at: int = 0, delete_at: int = 0,
                between: Callable[..., None] | None = None,
                adopting: bool = False) -> dict[str, Any]:
    repo = h.make_repo(tmp)
    recorder = Recorder(repo, kill_at=kill_at, delete_at=delete_at)
    _RECORDERS[repo] = recorder
    h.commit_module.set_kill_hook(recorder)
    problems: list[str] = []
    log: list[dict[str, Any]] = []
    crashes = 0
    try:
        for _ in range(4):
            controller = h.Controller(repo, tmp / "effects.log", between=between, decide=adopt)
            original_cli = h.run_cli

            def checked(r: Path, *argv: str, _orig: Any = original_cli) -> tuple[int, dict]:
                code, payload = _orig(r, *argv)
                if argv[0] == "next":
                    _check_run_json(r, payload, problems)
                return code, payload

            h.run_cli = checked
            try:
                code, started = h.start(repo)
                if code == 1 and started["refusal"]["code"] in (
                    "history-adoption-required", "attempt-residue"
                ):
                    # A step killed after its refs moved: the owner restores both refs.
                    assert restore_cut_off_step(repo), started
                    code, started = h.start(repo)
                elif code == 1 and started["refusal"]["code"] == "product-ref-diverged":
                    # An adoption killed after its refs moved: only the product ref goes back;
                    # HEAD's history awaits the owner's decision again.
                    store = _run_store(repo)
                    assert store is not None
                    rec = json.loads((store / "product-ref").read_text("utf-8"))
                    h.git(repo, "update-ref", "--no-deref", rec["name"], rec["recorded"])
                    code, started = h.start(repo)
                assert code == 0, started
                if crashes and (_run_store(repo) or Path()).joinpath("product-ref").exists():
                    resumed_parity(repo, allow_diverged=adopting)
                end = controller.drive()
                # A step killed with an attempt open ends in residue: restore both refs.
                while (end.get("refusal", {}).get("code") == "attempt-residue"
                       and restore_cut_off_step(repo)):
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
    store = _run_store(repo)
    product = json.loads((store / "product-ref").read_text("utf-8"))["name"]
    head = h.git(repo, "rev-parse", "HEAD").strip()
    product_ref = {
        "commit": h.git(repo, "rev-parse", product).strip(),
        "tree": h.git(repo, "rev-parse", f"{product}^{{tree}}").strip(),
        "head_tree": h.git(repo, "rev-parse", "HEAD^{tree}").strip(),
        "manifest": sorted(
            line.split("\t", 1)[1] + line.split()[2] for line in
            h.git(repo, "ls-tree", "-r", product).splitlines()
            if f"\t{h.SPEC_DIR}/" not in line
        ),
        "head": head,
        "branch": h.git(repo, "symbolic-ref", "HEAD").strip(),
    }
    return {
        "product_ref": product_ref,
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
        "ops": recorder.ops,
        "crashes": crashes,
        "log": log,
        "repo": repo,
    }


def _collapse_adoption(decisions: list[str]) -> list[str]:
    """A kill during adoption re-issues that one decision after the restart: only it may repeat."""
    return [d for i, d in enumerate(decisions)
            if not (d == "history-adoption" and i and decisions[i - 1] == d)]


def assert_converged(base: dict[str, Any], run: dict[str, Any], *, trees: bool = True,
                     adopted: int = 0, cut_off: int = 0) -> None:
    assert run["end"] == "terminal"
    ref = run["product_ref"]
    assert ref["commit"] == ref["head"] and ref["tree"] == ref["head_tree"]
    assert ref["branch"] == "refs/heads/main"
    if trees:
        # The product manifest; the spec directory's records differ by design when
        # a kill makes the effect source be asked again.
        assert ref["manifest"] == base["product_ref"]["manifest"]
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
    # A step killed after its refs moved and before its recording is the owner's decision,
    # answered by restoring both refs; it is the only extra decision a kill may leave.
    asked = _collapse_adoption(run["decisions"]) if adopted else run["decisions"]
    expected = base["decisions"] + ["history-adoption"] * adopted
    if cut_off and asked == expected + ["history-adoption"]:
        expected = asked  # with no attempt open the cut-off step is a decision
    assert asked == expected
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


# The CI shards select these two test functions by name; keep the names apart from every
# directory name in the test's path, and the VI-0519 test checks the split.
@pytest.mark.parametrize("point", range(1, BOUNDARIES + 1))
def test_kill_variant_converges(baseline: dict[str, Any], tmp_path: Path, point: int) -> None:
    run = run_variant(tmp_path, kill_at=point)
    assert run["crashes"] == 1
    first_move = baseline["seen"].index("refs-moved") + 1  # the approval: nothing to decide
    cut_off = int(run["seen"][point - 1] == "refs-moved" and point != first_move)
    assert_converged(baseline, run, cut_off=cut_off)


@pytest.mark.parametrize("point", range(1, BOUNDARIES + 1))
def test_journal_delete_variant_converges(baseline: dict[str, Any], tmp_path: Path,
                                          point: int) -> None:
    run = run_variant(tmp_path, delete_at=point)
    assert run["crashes"] == 0
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
        # Between attempts: an edit made while the attempt is open counts against it.
        if phase == "reported" and _first("implement-task", "Release")(request) and not edited:
            spec = c.repo / h.SPEC_DIR / "spec.md"
            spec.write_text(spec.read_text("utf-8").replace(
                "that answers.", "that answers quickly."), "utf-8")
            _, again = h.run_cli(c.repo, "next", h.SPEC_DIR)
            edited.append("request" in again)

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

    run = run_variant(tmp_path, between=between, adopting=True)
    assert rebased == [True]
    assert_converged(baseline, run, trees=False, adopted=1)


def _reset_two_back(c: h.Controller, request: dict[str, Any], phase: str,
                    done: list[int]) -> None:
    if phase == "reported" and _first("implement-task", "Calculator")(request) and not done:
        h.git(c.repo, "reset", "-q", "--hard", "HEAD~2")
        done.append(len(_RECORDERS[c.repo].seen))


def _rebase_between(c: h.Controller, request: dict[str, Any], phase: str,
                    done: list[int]) -> None:
    if phase == "reported" and _first("implement-task", "Calculator")(request) and not done:
        root = h.git(c.repo, "rev-list", "--max-parents=0", "HEAD").strip()
        h.git(c.repo, "checkout", "-q", "-b", "upstream", root)
        (c.repo / "OTHER.md").write_text("upstream\n", "utf-8")
        h.git(c.repo, "add", "OTHER.md")
        h.git(c.repo, "commit", "-q", "-m", "unrelated upstream change")
        h.git(c.repo, "checkout", "-q", "main")
        h.git(c.repo, "rebase", "-q", "upstream")
        done.append(len(_RECORDERS[c.repo].seen))


SCENARIOS = {"lag-repair": (_reset_two_back, 0), "adoption": (_rebase_between, 1)}
# The kill points each scenario's own writes pass through.
SCENARIO_POINTS = {
    "lag-repair": {"projection-updated", "repaired"},
    "adoption": {"commit-built", "refs-moved", "made-recorded", "synced"},
}
WINDOW = 12


def _scenario(tmp: Path, name: str, *, kill_at: int = 0) -> tuple[dict[str, Any], int]:
    """Run the full synthetic run with a diversion in the middle; return it and where it struck."""
    divert, _adopted = SCENARIOS[name]
    done: list[int] = []
    run = run_variant(tmp, kill_at=kill_at, between=lambda c, r, p: divert(c, r, p, done),
                      adopting=name == "adoption")
    assert done, "the diversion never struck"
    return run, done[0]


@pytest.fixture(scope="module", params=sorted(SCENARIOS))
def diverted(request: pytest.FixtureRequest,
             tmp_path_factory: pytest.TempPathFactory) -> tuple[str, dict[str, Any], int]:
    run, at = _scenario(tmp_path_factory.mktemp(request.param), request.param)
    return request.param, run, at


def test_a_reset_or_a_rebase_converges_uninterrupted(baseline: dict[str, Any],
                                                     diverted: tuple[str, dict[str, Any], int]
                                                     ) -> None:
    name, run, at = diverted
    adopted = SCENARIOS[name][1]
    assert_converged(baseline, run, trees=name == "lag-repair", adopted=adopted)
    # The window the kill tests walk covers every write the repair or adoption makes.
    struck = set(run["seen"][at:at + WINDOW])
    assert SCENARIO_POINTS[name] <= struck, (name, sorted(struck))
    if name == "adoption":
        # The window holds the reanchor step's own writes, not only another step's.
        own = {point for point, op in zip(run["seen"][at:at + WINDOW], run["ops"][at:at + WINDOW], strict=True)
               if op == "reanchor"}
        assert set(STEP_POINTS) <= own, sorted(own)


@pytest.mark.parametrize("offset", range(1, WINDOW + 1))
def test_every_write_of_lag_repair_and_adoption_converges(
    baseline: dict[str, Any], diverted: tuple[str, dict[str, Any], int], tmp_path: Path,
    offset: int,
) -> None:
    name, base_run, at = diverted
    run, struck_at = _scenario(tmp_path, name, kill_at=at + offset)
    assert run["crashes"] == 1
    assert struck_at == at, "the diversion struck at another point than in the uninterrupted run"
    assert run["seen"][at + offset - 1] == base_run["seen"][at + offset - 1], "struck elsewhere"
    assert_converged(baseline, run, trees=name == "lag-repair", adopted=SCENARIOS[name][1])
