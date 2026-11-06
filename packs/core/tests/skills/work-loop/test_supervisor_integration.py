"""Ordered integration of concurrent results: batches, held results, the apply, and recovery.

Every test drives real Git. Whole-verb tests run the fixture launcher through the
``run-concurrent`` verb; the apply-level tests call the apply directly over trees built with
Git plumbing, as defence in depth beyond what admission lets reach it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

_SUPPORT = Path(__file__).resolve().parent / "launcher_support.py"


def _support() -> ModuleType:
    alias = "core_work_loop_launcher_support"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _SUPPORT)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _support()
sup = ls.sup
harness = ls.harness
integ = ls.cli._supervisor("_supervisor_integration.py")
pytestmark = sup.INTEGRATION

CALC = "def answer():\n    return 42\n"
NOTE = "plain note\n"


def plan_of(*specs: tuple[str, str, str, str, str]) -> str:
    """A goal-based plan: ``(number, title, reads, writes, depends)`` per task."""
    return sup.plan(*[
        sup.task(
            number, title, mode="goal-based", tests="no stub (goal-based)", touches=writes,
            reads=reads, writes=writes, depends=depends,
        )
        for number, title, reads, writes, depends in specs
    ])


PAIR = plan_of(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
    ("T2", "Plain note is written", "`README.md`", "`plain.txt`", "none"),
)
TRIPLE = plan_of(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
    ("T2", "Plain note is written", "`README.md`", "`plain.txt`", "none"),
    ("T3", "Third file is written", "`README.md`", "`third.txt`", "none"),
)
REVERSE = {
    "per_task": {
        "calculator-answers": {"wait_for": "{log}/second.done"},
        "plain-note-is-written": {"write": {"plain.txt": NOTE}, "touch": "{log}/second.done"},
    }
}


def script_for(tmp_path: Path, script: dict[str, Any]) -> dict[str, Any]:
    """*script* with ``{log}`` replaced by the fixture's log directory."""
    log = str(tmp_path / "log")
    return json.loads(json.dumps(script).replace("{log}", log))  # type: ignore[no-any-return]


def make_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, plan: str = PAIR,
    script: dict[str, Any] | None = None, **kwargs: Any,
) -> Any:
    tmp_path.mkdir(parents=True, exist_ok=True)
    policy = {"max_concurrent_attempts": 2, **kwargs.pop("policy", {})}
    return ls.Env(
        tmp_path, monkeypatch, plan=plan, script=script_for(tmp_path, script or {}),
        policy=policy, **kwargs,
    )


def head(env: Any) -> str:
    return str(env.git("rev-parse", "HEAD")).strip()


def run_batch(env: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    request = env.issued()
    code, payload = env.verb(request["request_id"])
    assert code == 0, payload
    return request, payload["run_concurrent"]  # type: ignore[no-any-return]


def landed_order(env: Any) -> list[str]:
    """The ``Supervisor-Task`` trailers of the landed commits, oldest first."""
    out = env.git(
        "log", "--reverse", "--format=%(trailers:key=Supervisor-Task,valueonly,unfold)", "-E",
        "--grep=^Supervisor-Attempt: ",
    )
    return [line for line in out.splitlines() if line.strip()]


def state_of(env: Any) -> dict[str, str]:
    return {r["task_id"].split("-")[0]: r["state"] for r in env.records()}


def kill_with(point: str, action: Any) -> None:
    """Run *action* each time the supervisor reaches kill point *point*."""

    def hook(name: str) -> None:
        if name == point:
            action()

    harness.commit_module.set_kill_hook(hook)


@pytest.fixture(autouse=True)
def _clean_hooks() -> Any:
    yield
    ls.clear_kill_hook()
    harness.commit_module.set_kill_hook(None)
    ls.cli._supervisor("_supervisor_git.py").set_update_hook(None)
    integ.INTEGRATE_IN_COMPLETION_ORDER = False


# ── admission to a batch (AC-0003, AC-0004, AC-0006) ────────────────────────


def test_two_disjoint_tasks_are_named_in_one_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch)
    request = env.issued()
    assert request["kind"] == "run-concurrent" and len(request["tasks"]) == 2
    assert request["tasks"][0] == request["task"]["task_id"]  # floor order leads


def test_three_admissible_tasks_under_a_cap_of_two_name_the_first_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=TRIPLE)
    request = env.issued()
    assert [t.split("-")[0] for t in request["tasks"]] == ["calculator", "plain"]
    other = make_env(tmp_path / "cap3", monkeypatch, plan=TRIPLE, policy={"max_concurrent_attempts": 3})
    assert len(other.issued()["tasks"]) == 3


def test_a_meeting_task_is_left_out_and_a_later_disjoint_one_joins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_of(
        ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
        ("T2", "Plain note is written", "`calc.py`", "`plain.txt`", "none"),
        ("T3", "Third file is written", "`README.md`", "`third.txt`", "none"),
    )
    env = make_env(tmp_path, monkeypatch, plan=plan)
    request = env.issued()
    assert [t.split("-")[0] for t in request["tasks"]] == ["calculator", "third"]


def test_a_task_whose_dependency_is_not_complete_is_not_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_of(
        ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
        ("T2", "Plain note is written", "`README.md`", "`plain.txt`", "T1"),
    )
    env = make_env(tmp_path, monkeypatch, plan=plan)
    assert len(env.issued()["tasks"]) == 1


# ── floor order whatever order attempts finish in (AC-0034, AC-0008, AC-0009) ─


def reverse_script() -> dict[str, Any]:
    return {**REVERSE, "write": {"calc.py": CALC}}


def test_a_batch_finishing_in_reverse_order_lands_in_floor_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    seen: dict[str, Any] = {}

    def at_hold() -> None:
        if "held" not in seen:  # the first result held is the later task's
            seen["held"] = sorted(p.name for p in (env.store() / "held").iterdir())
            seen["head"] = head(env)
            seen["states"] = state_of(env)
            seen["lock"] = (env.store() / "integration.lock").exists()

    kill_with("result-held", at_hold)
    request = env.issued()
    base = head(env)
    outcome = env.verb(request["request_id"])[1]["run_concurrent"]
    assert seen["head"] == base and len(seen["held"]) == 1 and seen["states"]["plain"] == "held"
    assert [a["outcome"] for a in outcome["attempts"]] == ["landed", "landed"]
    assert landed_order(env) == request["tasks"]
    assert env.git("show", "HEAD:calc.py") == CALC and env.git("show", "HEAD:plain.txt") == NOTE
    assert not list((env.store() / "held").iterdir()) and ls.git_clean(env.repo)
    assert len(list((env.store() / "integrations").iterdir())) == 2
    assert not (env.store() / "integration.lock").exists()
    code, admitted = env.report(request)
    assert code == 0 and admitted["admitted"] == "run-concurrent"


def test_three_tasks_finishing_in_reverse_land_in_floor_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = {
        "write": {"calc.py": CALC},
        "per_task": {
            "calculator-answers": {"wait_for": "{log}/second.done"},
            "plain-note-is-written": {
                "write": {"plain.txt": NOTE}, "wait_for": "{log}/third.done",
                "touch": "{log}/second.done",
            },
            "third-file-is-written": {"write": {"third.txt": "3\n"}, "touch": "{log}/third.done"},
        },
    }
    env = make_env(
        tmp_path, monkeypatch, plan=TRIPLE, script=script, policy={"max_concurrent_attempts": 3}
    )
    request, outcome = run_batch(env)
    assert [a["outcome"] for a in outcome["attempts"]] == ["landed"] * 3
    assert landed_order(env) == request["tasks"]
    assert ls.git_clean(env.repo)


def test_the_environment_cannot_choose_completion_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in (
        "INTEGRATE_IN_COMPLETION_ORDER", "WORK_SUPERVISOR_COMPLETION_ORDER",
        "WORK_SUPERVISOR_INTEGRATE_IN_COMPLETION_ORDER", "COMPLETION_ORDER",
    ):
        monkeypatch.setenv(name, "1")
    env = make_env(
        tmp_path, monkeypatch, script=reverse_script(),
        policy={"integrate_in_completion_order": True},  # a policy key
    )
    request = env.issued()
    # A file, in the run store and in the supervisor's own directory of the work tree.
    spec_store = env.repo / harness.SPEC_DIR / ".supervisor"
    for marker in (
        env.store() / "integrate_in_completion_order", spec_store / "integrate_in_completion_order",
    ):
        marker.write_text("1\n", encoding="utf-8")
    # A command-line flag is not a switch: the CLI refuses it as a usage error.
    code, refused = env.run(
        "run-concurrent", harness.SPEC_DIR, "--request", request["request_id"],
        "--completion-order",
    )
    assert code != 0 and "request" not in refused.get("run_concurrent", {}), refused
    assert not env.records()  # nothing ran
    code, payload = env.verb(request["request_id"])
    assert code == 0, payload
    assert [a["outcome"] for a in payload["run_concurrent"]["attempts"]] == ["landed", "landed"]
    assert landed_order(env) == request["tasks"]


def test_the_in_process_seam_integrates_in_completion_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    integ.INTEGRATE_IN_COMPLETION_ORDER = True
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    request, outcome = run_batch(env)
    assert [a["outcome"] for a in outcome["attempts"]] == ["landed", "landed"]
    assert landed_order(env) == list(reversed(request["tasks"]))
    assert env.git("show", "HEAD:calc.py") == CALC and env.git("show", "HEAD:plain.txt") == NOTE


def crash_second_result(env: Any) -> dict[str, Any]:
    """Kill the verb as the later task's result is held; its sibling never settles."""
    request = env.issued()
    seen: list[str] = []

    def hook(name: str) -> None:
        if name == "result-held":
            seen.append(name)
            raise harness.Crash(name)

    harness.commit_module.set_kill_hook(hook)
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    ws = harness.workspace(env.repo)
    for record in env.records():
        ls.concurrent_module._write(ws, request["run_id"], {**record, "verb_start": "gone"})
    return request


def test_a_held_result_leaves_a_floor_attempt_free_and_lands_with_its_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_of(
        ("T1", "Calculator answers", "`README.md`", "`calc.py`", "none"),
        ("T2", "Plain note is written", "`README.md`", "`plain.txt`", "none"),
        ("T3", "Third file is written", "`README.md`", "`third.txt`", "T2"),
    )
    env = make_env(tmp_path, monkeypatch, plan=plan, script=reverse_script())
    crash_second_result(env)
    held = sorted((env.store() / "held").iterdir())
    assert len(held) == 1
    # The held task is not complete, and the task that depends on it is not issued (AC-0009);
    # the first task goes to the floor beside the held result (AC-0008).
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task" and floor["task"]["title"].startswith("Calculator")
    (env.repo / "calc.py").write_text(CALC, encoding="utf-8")
    code, admitted = env.report(floor, gate={"passed": True})
    assert code == 0 and admitted["admitted"] == "implement"
    assert landed_order(env)[-1].startswith("plain-note")  # the held result followed it
    assert env.git("show", "HEAD:plain.txt") == NOTE and ls.git_clean(env.repo)
    assert not list((env.store() / "held").iterdir())
    after = env.next()["request"]
    assert after["task"]["title"].startswith("Third")


def assert_residue_after_report(env: Any, floor: dict[str, Any]) -> None:
    """The report is refused, and the next verb answers ``attempt-residue`` and no other code."""
    code, refused = env.report(floor, gate={"passed": True})
    assert code == 1 and refused["refusal"]["code"] in ("attempt-residue", "attempt-refused")
    code, again = env.run("next", harness.SPEC_DIR)
    assert code == 1 and again["refusal"]["code"] == "attempt-residue", again


def test_a_floor_attempt_that_rewrites_a_held_record_is_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    crash_second_result(env)
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    (record,) = (env.store() / "held").iterdir()
    original = record.read_bytes()
    record.write_bytes(original + b" ")
    assert_residue_after_report(env, floor)
    record.write_bytes(original)


def test_a_floor_attempt_that_rewrites_a_held_tree_ref_is_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    crash_second_result(env)
    floor = env.next()["request"]
    (record,) = (env.store() / "held").iterdir()
    held = json.loads(record.read_text("utf-8"))
    ref = [
        r for r in env.git(
            "for-each-ref", "--format=%(refname)", "refs/agentbundle/delivery"
        ).splitlines()
        if "/held/" in r
    ][0]
    original = env.git("rev-parse", ref).strip()
    other = env.git("rev-parse", "HEAD^{tree}").strip()
    assert other != held["result_tree"]
    env.git("update-ref", ref, other)
    assert_residue_after_report(env, floor)
    env.git("update-ref", ref, original)


def test_integration_reads_the_held_identity_not_the_attempt_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())

    def tamper() -> None:
        for record in env.records():
            directory = record.get("attempt_dir")
            if directory and Path(directory).exists():
                (Path(directory) / "plain.txt").write_text("tampered\n", encoding="utf-8")
                (Path(directory) / "calc.py").write_text("tampered\n", encoding="utf-8")

    kill_with("integration-start", tamper)
    _request, outcome = run_batch(env)
    assert [a["outcome"] for a in outcome["attempts"]] == ["landed", "landed"]
    assert env.git("show", "HEAD:calc.py") == CALC and env.git("show", "HEAD:plain.txt") == NOTE


def _edit_trusted_file(env: Any) -> Any:
    spec = env.repo / harness.SPEC_DIR / "spec.md"
    original = spec.read_bytes()
    spec.write_bytes(original + b"\nedited\n")
    return lambda: spec.write_bytes(original)


def _edit_git_control_state(env: Any) -> Any:
    attributes = env.repo / ".git" / "info" / "attributes"
    attributes.parent.mkdir(exist_ok=True)
    assert not attributes.exists()
    attributes.write_text("*.py merge=union\n", encoding="utf-8")
    return attributes.unlink


def _edit_delivery(env: Any) -> Any:
    note = env.repo / harness.SPEC_DIR / "delivery" / "x.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("changed\n", encoding="utf-8")
    return note.unlink


@pytest.mark.parametrize(
    "change", [_edit_trusted_file, _edit_git_control_state, _edit_delivery],
    ids=["trusted-file", "git-control-state", "delivery"],
)
def test_a_protected_change_while_a_sibling_is_open_refuses_the_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: Any
) -> None:
    script = {
        "per_task": {
            "calculator-answers": {"write": {"calc.py": CALC}, "touch": "{log}/first.done"},
            "plain-note-is-written": {
                "write": {"plain.txt": NOTE}, "wait_for": "{log}/first.done",
            },
        }
    }
    env = make_env(tmp_path, monkeypatch, script=script)
    request = env.issued()
    before = head(env)
    edited: list[Any] = []
    once = threading.Lock()  # both attempts reach the point at once; only one changes anything

    def edit(name: str) -> None:
        if name == "released" and once.acquire(blocking=False):
            edited.append(change(env))

    harness.commit_module.set_kill_hook(edit)
    code, refused = env.verb(request["request_id"])
    ls.clear_kill_hook()
    (undo,) = edited
    undo()
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue", refused
    assert head(env) == before and not (env.repo / "calc.py").exists()


# ── the intervening-change check (AC-0027, AC-0028, AC-0035) ────────────────


def test_a_traced_read_of_a_path_a_sibling_changed_is_the_refusal_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = {
        "per_task": {
            "calculator-answers": {"write": {"calc.py": CALC}, "wait_for": "{log}/second.done"},
            "plain-note-is-written": {
                "write": {"plain.txt": NOTE}, "touch": "{log}/second.done",
                "access_reads": [
                    {"path": "README.md", "kind": "file"}, {"path": "calc.py", "kind": "file"},
                ],
            },
        }
    }
    env = make_env(tmp_path, monkeypatch, script=script, mode="complete-trace")
    request, outcome = run_batch(env)
    by_task = {a["task"].split("-")[0]: a for a in outcome["attempts"]}
    assert by_task["calculator"]["outcome"] == "landed"
    assert by_task["plain"] == {
        "outcome": "conflict", "reason": "meets", "task": by_task["plain"]["task"]
    }
    assert env.git("show", "HEAD:calc.py") == CALC
    (conflict,) = (env.store() / "conflicts").iterdir()
    record = json.loads(conflict.read_text("utf-8"))
    assert record["reason"] == "meets" and record["paths"] == ["calc.py"]
    assert not list((env.store() / "held").iterdir()) and ls.git_clean(env.repo)
    # The task is projected again from the new tip, under a new request.
    again = env.next()["request"]
    assert again["kind"] == "run-concurrent" and again["request_id"].endswith(":r1")
    assert again["task"]["title"].startswith("Plain")


def test_an_undeclared_traced_read_that_meets_nothing_integrates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = {
        "per_task": {
            "calculator-answers": {"write": {"calc.py": CALC}, "wait_for": "{log}/second.done"},
            "plain-note-is-written": {
                "write": {"plain.txt": NOTE}, "touch": "{log}/second.done",
                "access_reads": [
                    {"path": "README.md", "kind": "file"}, {"path": "elsewhere.txt", "kind": "file"},
                ],
            },
        }
    }
    env = make_env(tmp_path, monkeypatch, script=script, mode="complete-trace")
    _request, outcome = run_batch(env)
    assert [a["outcome"] for a in outcome["attempts"]] == ["landed", "landed"]


class Rig:
    """A repository with a source commit, a tip, and a result tree, for the apply on its own."""

    def __init__(self, tmp_path: Path, base: dict[str, str]) -> None:
        self.repo = harness.make_repo(tmp_path)
        self.files = base
        self.source = self.commit(self.head(), {p: ("100644", c) for p, c in base.items()})
        harness.git(self.repo, "reset", "-q", "--hard", self.source)

    def head(self) -> str:
        return harness.git(self.repo, "rev-parse", "HEAD").strip()

    def _git(self, *args: str, stdin: bytes | None = None, index: Path | None = None) -> str:
        env = {**os.environ, **harness.GIT_ENV}
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        done = subprocess.run(
            ["git", *args], cwd=self.repo, env=env, input=stdin, capture_output=True, check=True
        )
        return done.stdout.decode().strip()

    def tree(self, parent: str, files: dict[str, tuple[str, str] | None]) -> str:
        """The tree of *parent* with *files* applied: ``path -> (mode, content)`` or removal."""
        index = self.repo / ".git" / "rig-index"
        self._git("read-tree", parent, index=index)
        for path, entry in files.items():
            if entry is None:
                self._git("update-index", "--force-remove", "--", path, index=index)
                continue
            mode, content = entry
            blob = self._git("hash-object", "-w", "--stdin", stdin=content.encode())
            self._git("update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}", index=index)
        tree = self._git("write-tree", index=index)
        index.unlink()
        return tree

    def commit(self, parent: str, files: dict[str, tuple[str, str] | None]) -> str:
        tree = self.tree(parent, files)
        return self._git("commit-tree", tree, "-p", parent, "-m", "rig")

    def advance(self, files: dict[str, tuple[str, str] | None]) -> str:
        """Move the tip forward by *files* and check it out."""
        new = self.commit(self.head(), files)
        harness.git(self.repo, "update-ref", "HEAD", new)
        return new

    def held(self, files: dict[str, tuple[str, str] | None], **fields: Any) -> dict[str, Any]:
        record = {
            "attempt_id": "att-0123456789abcdef", "run_id": "run-0123456789abcdef",
            "request_id": "conc:x", "task_id": "t", "revision": "r", "attempt": 1, "step": "s",
            "source": self.source, "result_tree": self.tree(self.source, files),
            "access_attestation_sha256": "0" * 64, "access_defect": None, "reads": [],
            "writes": [], "seq": 1,
        }
        return {**record, **fields}

    def apply(self, held: dict[str, Any]) -> str:
        ws = harness.workspace(self.repo)
        state = SimpleNamespace(cited_paths=())
        return str(integ.apply_result(ws, state, held, self.head()))


def refusal_of(rig: Rig, held: dict[str, Any]) -> Any:
    with pytest.raises(integ.Refused) as caught:
        rig.apply(held)
    return caught.value


LINES = "a\nb\nc\nd\ne\nf\ng\nh\n"


def same_line_rig(tmp_path: Path) -> tuple[Rig, dict[str, Any]]:
    rig = Rig(tmp_path, {"f.txt": LINES})
    held = rig.held({"f.txt": ("100644", LINES.replace("c\n", "Y\n"))})
    rig.advance({"f.txt": ("100644", LINES.replace("c\n", "X\n"))})
    return rig, held


def test_a_clean_disjoint_apply_merges_both_sides(tmp_path: Path) -> None:
    rig = Rig(tmp_path, {"f.txt": LINES})
    held = rig.held({"g.txt": ("100644", "new\n")})
    rig.advance({"f.txt": ("100644", LINES.replace("c\n", "X\n"))})
    tree = rig.apply(held)
    listing = harness.git(rig.repo, "ls-tree", "-r", "--name-only", tree)
    assert "g.txt" in listing and "f.txt" in listing


def test_two_results_changing_the_same_line_conflict_at_the_apply(tmp_path: Path) -> None:
    rig, held = same_line_rig(tmp_path)
    refused = refusal_of(rig, held)
    assert refused.reason == "content" and refused.paths == ["f.txt"]


def test_a_union_merge_attribute_in_the_checked_out_gitattributes_resolves_nothing(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path, {"f.txt": LINES})
    held = rig.held({"f.txt": ("100644", LINES.replace("c\n", "Y\n"))})
    rig.advance({
        "f.txt": ("100644", LINES.replace("c\n", "X\n")),
        ".gitattributes": ("100644", "* merge=union\n"),
    })
    (rig.repo / ".gitattributes").write_text("* merge=union\n", encoding="utf-8")
    assert refusal_of(rig, held).reason == "content"


def test_a_merge_attribute_from_info_attributes_is_refused(tmp_path: Path) -> None:
    rig, held = same_line_rig(tmp_path)
    info = rig.repo / ".git" / "info"
    info.mkdir(exist_ok=True)
    (info / "attributes").write_text("*.txt merge=union\n", encoding="utf-8")
    refused = refusal_of(rig, held)
    assert refused.reason == "merge-attribute" and "f.txt" in refused.paths


def test_a_merge_config_key_is_refused_even_over_a_same_line_change(tmp_path: Path) -> None:
    rig, held = same_line_rig(tmp_path)
    harness.git(rig.repo, "config", "merge.default", "union")
    assert refusal_of(rig, held).reason == "merge-config"


def test_an_apply_that_changes_a_path_outside_the_result_is_refused(tmp_path: Path) -> None:
    body = "".join(f"line {i}\n" for i in range(30))
    rig = Rig(tmp_path, {"d/a.txt": body})
    held = rig.held({"d/a.txt": ("100644", body.replace("line 20\n", "changed\n"))})
    rig.advance({"d/a.txt": None, "e/a.txt": ("100644", body)})  # a rename the apply follows
    refused = refusal_of(rig, held)
    assert refused.reason == "outside-changed-paths" and refused.paths == ["e/a.txt"]


def test_a_link_that_resolves_through_a_merged_link_to_a_protected_path_is_refused(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path, {"p/keep.txt": "k\n"})
    held = rig.held({"p/x": ("120000", "q/delivery/approvals.jsonl")})
    rig.advance({"p/q": ("120000", "..")})  # a floor-integrated link, unknown to the attempt
    refused = refusal_of(rig, held)
    assert refused.reason == "link-target"
    assert harness.git(rig.repo, "rev-parse", "HEAD").strip() == rig.head()


def test_a_result_without_a_complete_attestation_integrates_on_exact_source_only(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path, {"f.txt": LINES})
    held = rig.held({"g.txt": ("100644", "new\n")}, access_defect="access-incomplete")
    assert rig.apply(held) == held["result_tree"]  # tip is the source: exact
    rig.advance({"f.txt": ("100644", LINES.replace("c\n", "X\n"))})
    assert refusal_of(rig, held).reason == "incomplete-attestation"


@pytest.mark.parametrize(
    ("read", "change", "meets"),
    [
        ({"path": "docs/a.txt", "kind": "file"}, {"docs/a.txt": ("100644", "z\n")}, True),
        ({"path": "docs/a.txt", "kind": "missing"}, {"docs/a.txt": ("100644", "z\n")}, False),
        ({"path": "docs/new.txt", "kind": "missing"}, {"docs/new.txt": ("100644", "z\n")}, True),
        ({"path": "docs", "kind": "listing"}, {"docs/new.txt": ("100644", "z\n")}, True),
        ({"path": "docs", "kind": "listing"}, {"docs/a.txt": ("100644", "z\n")}, False),
        ({"path": "docs", "kind": "walk"}, {"docs/a.txt": ("100644", "z\n")}, True),
        ({"path": "other.txt", "kind": "file"}, {"docs/a.txt": ("100644", "z\n")}, False),
    ],
)
def test_an_attested_read_meets_a_changed_path_by_the_closed_rows(
    tmp_path: Path, read: dict[str, str], change: dict[str, Any], meets: bool
) -> None:
    rig = Rig(tmp_path, {"docs/a.txt": "a\n", "other.txt": "o\n"})
    held = rig.held({"extra.txt": ("100644", "e\n")}, reads=[read])
    rig.advance(change)
    if meets:
        refused = refusal_of(rig, held)
        assert refused.reason == "meets"
    else:
        assert rig.apply(held)


def test_an_attested_write_meets_a_rename_at_either_end(tmp_path: Path) -> None:
    body = "".join(f"line {i}\n" for i in range(30))
    for end in ("d/a.txt", "e/a.txt"):
        rig = Rig(tmp_path / end.replace("/", "-"), {"d/a.txt": body})
        held = rig.held(
            {"extra.txt": ("100644", "e\n")}, writes=[{"path": end, "kind": "write"}]
        )
        rig.advance({"d/a.txt": None, "e/a.txt": ("100644", body)})
        assert refusal_of(rig, held).reason == "meets"


def test_a_case_alias_meets_on_an_ignore_case_repository_only(tmp_path: Path) -> None:
    for flag, meets in (("true", True), ("false", False)):
        rig = Rig(tmp_path / flag, {"calc.py": "a\n"})
        harness.git(rig.repo, "config", "core.ignoreCase", flag)
        held = rig.held(
            {"extra.txt": ("100644", "e\n")}, reads=[{"path": "calc.py", "kind": "file"}]
        )
        rig.advance({"Calc.py": ("100644", "alias\n")})
        if meets:
            assert refusal_of(rig, held).reason == "meets"
        else:
            assert rig.apply(held)


# ── the refusal outcome, crashes, and races (AC-0041 to AC-0046) ────────────


def kill_points() -> list[str]:
    return [
        "integration-start", "commit-built", "refs-moved", "made-recorded",
        "integration-before-record", "integration-materializing",
    ]


def settle(env: Any, request: dict[str, Any]) -> None:
    """Mark the dead verb's records gone, as a real death would leave them."""
    ws = harness.workspace(env.repo)
    for record in env.records():
        ls.concurrent_module._write(ws, request["run_id"], {**record, "verb_start": "gone"})


def uninterrupted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    env = make_env(tmp_path / "base", monkeypatch, plan=ls.ONE_TASK)
    run_batch(env)
    return converged(env)


def converged(env: Any) -> dict[str, Any]:
    product = env.store() / "product-ref"
    name = json.loads(product.read_text("utf-8"))["name"]
    return {
        "calc": env.git("show", "HEAD:calc.py"),
        "attempts": env.git("log", "--format=%B").count("Supervisor-Attempt: att-"),
        "clean": ls.git_clean(env.repo),
        "ref": env.git("rev-parse", name).strip() == head(env),
        "worktree": (env.repo / "calc.py").read_text("utf-8"),
        "held": sorted(p.name for p in (env.store() / "held").iterdir()),
        "conflicts": sorted(p.name for p in (env.store() / "conflicts").iterdir()),
        "integrations": len(list((env.store() / "integrations").iterdir())),
    }


@pytest.mark.parametrize("point", kill_points())
def test_a_kill_at_each_integration_write_converges_through_the_next_verb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str
) -> None:
    expected = uninterrupted(tmp_path, monkeypatch)
    env = make_env(tmp_path / "run", monkeypatch, plan=ls.ONE_TASK)
    request = env.issued()
    old = head(env)
    product = json.loads((env.store() / "product-ref").read_text("utf-8"))["name"]
    at_the_kill: list[str] = []

    def capture() -> None:
        at_the_kill.append(env.git("rev-parse", product).strip())

    ls.crash_at(point, before=capture)
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    (new,) = at_the_kill
    swapped = point not in ("integration-start", "commit-built")
    # The product ref is exactly the recorded old commit or the new commit, by value.
    assert env.git("rev-parse", product).strip() == new == head(env)
    if swapped:
        assert new != old
        assert env.git("rev-parse", f"{new}^").strip() == old
        assert "Supervisor-Attempt: att-" in env.git("show", "-s", "--format=%B", new)
    else:
        assert new == old
    settle(env, request)
    commits_before = env.git("rev-list", "--count", "HEAD").strip()
    nxt = env.next()
    assert "refusal" not in nxt, nxt
    after = converged(env)
    assert after == expected
    assert env.git("rev-parse", product).strip() == head(env)
    if swapped:
        # The landed operation was recognised from its commit: nothing new was made, no
        # conflict was recorded, and the task was not projected again.
        assert head(env) == new
        assert env.git("rev-list", "--count", "HEAD").strip() == commits_before
        assert after["conflicts"] == [] and after["attempts"] == 1
        assert not list((env.store() / "conflicts").iterdir())
        request_again = nxt.get("request") or {}
        assert not (
            request_again.get("kind") == "run-concurrent"
            and str(request_again.get("request_id", "")).endswith(":r1")
        ), nxt
        records = env.records()
        assert [r["state"] for r in records] == ["landed"]
        assert not any(r.get("reproject") for r in records)


def move_head_with_a_foreign_commit(env: Any) -> None:
    harness.git(env.repo, "commit", "-q", "--allow-empty", "-m", "foreign")


def test_a_compare_and_swap_lost_to_a_ref_move_is_the_refusal_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    request = env.issued()
    moves: list[str] = []

    def move() -> None:
        moves.append(head(env))
        move_head_with_a_foreign_commit(env)

    kill_with("commit-built", move)
    code, payload = env.verb(request["request_id"])
    ls.clear_kill_hook()
    outcome = payload["run_concurrent"]
    assert outcome["outcome"] == "conflict" and outcome["reason"] == "cas-lost"
    assert head(env) != moves[0] and not (env.repo / "calc.py").exists()
    (conflict,) = (env.store() / "conflicts").iterdir()
    assert json.loads(conflict.read_text("utf-8"))["reason"] == "cas-lost"


def test_a_ref_moved_between_the_check_and_the_swap_is_the_refusal_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    request = env.issued()
    armed: list[bool] = []
    git_module = ls.cli._supervisor("_supervisor_git.py")

    def update_hook() -> None:
        if armed:
            armed.clear()
            move_head_with_a_foreign_commit(env)

    git_module.set_update_hook(update_hook)
    kill_with("commit-built", lambda: armed.append(True))
    code, payload = env.verb(request["request_id"])
    outcome = payload["run_concurrent"]
    assert outcome["outcome"] == "conflict" and outcome["reason"] == "cas-lost"
    assert not (env.repo / "calc.py").exists()


def test_a_refusal_leaves_refs_index_and_delivery_and_reprojects_the_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    request = env.issued()
    before = {"head": head(env), "index": env.git("ls-files", "-s"),
              "delivery": env.git("ls-tree", "-r", "HEAD", harness.SPEC_DIR + "/delivery")}
    original = integ.apply_result
    monkeypatch.setattr(
        integ, "apply_result", lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", ["x"]))
    )
    code, payload = env.verb(request["request_id"])
    assert payload["run_concurrent"]["reason"] == "content"
    assert {"head": head(env), "index": env.git("ls-files", "-s"),
            "delivery": env.git("ls-tree", "-r", "HEAD", harness.SPEC_DIR + "/delivery")} == before
    assert env.records()[0]["state"] == "conflict"
    monkeypatch.setattr(integ, "apply_result", original)
    again = env.next()["request"]
    assert again["request_id"].endswith(":r1") and again["kind"] == "run-concurrent"


def test_a_spent_reprojection_bound_sends_the_task_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK, policy={"reprojection_bound": 1})
    request = env.issued()
    original = integ.apply_result
    monkeypatch.setattr(
        integ, "apply_result", lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", ["x"]))
    )
    env.verb(request["request_id"])
    monkeypatch.setattr(integ, "apply_result", original)
    floor = env.next()
    assert floor["request"]["kind"] == "implement-task"
    assert ls.journal(env.repo)[-1]["floor_reason"] == "reprojection-bound"


# ── the records (AC-0047, AC-0048) ──────────────────────────────────────────


def held_after_crash(env: Any) -> dict[str, Any]:
    request = env.issued()
    ls.crash_at("integration-start")
    with pytest.raises(harness.Crash):
        env.verb(request["request_id"])
    ls.clear_kill_hook()
    return request


def test_a_conflict_over_the_path_cap_is_written_truncated_in_byte_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    held_after_crash(env)
    paths = [f"dir/file-{n:04d}.txt" for n in range(1001)][::-1]
    monkeypatch.setattr(
        integ, "apply_result", lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", paths))
    )
    env.next()
    (conflict,) = (env.store() / "conflicts").iterdir()
    record = json.loads(conflict.read_text("utf-8"))
    assert record["path_count"] == 1001 and record["truncated"] is True
    assert record["paths"] == sorted(paths)[:1000] and len(record["paths"]) == 1000
    assert record["reason"] == "content" and set(record) >= {
        "operation_key", "run_id", "attempt_id", "task_id", "source_commit", "observed_tip",
    }
    assert env.records()[0]["state"] == "conflict"


def test_a_conflict_record_holds_paths_and_no_file_contents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, plan=ls.ONE_TASK)
    held_after_crash(env)
    monkeypatch.setattr(
        integ, "apply_result", lambda *a, **k: (_ for _ in ()).throw(integ.Refused("content", ["calc.py"]))
    )
    env.next()
    (conflict,) = (env.store() / "conflicts").iterdir()
    text = conflict.read_text("utf-8")
    assert "return 42" not in text and json.loads(text)["paths"] == ["calc.py"]
    safety = ls.cli._supervisor("_content_safety.py")
    verdict = safety.check_content_safety(
        "integration-diagnostic", text.encode(), source_record_id="conflict"
    )
    assert verdict.accepted


def test_a_successful_integration_records_one_result_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    request, outcome = run_batch(env)
    records = [json.loads(p.read_text("utf-8")) for p in sorted((env.store() / "integrations").iterdir())]
    assert len(records) == 2
    commits = {a["commit"] for a in outcome["attempts"]}
    assert {r["result_commit"] for r in records} == commits
    for record in records:
        assert record["algorithm"]["name"] == "git-merge-tree-write-tree"
        assert record["algorithm"]["git_version"].count(".") >= 1
        assert len(record["access_attestation_sha256"]) == 64
        assert env.git("rev-parse", record["result_commit"] + "^").strip() == record["observed_tip"]
    first, second = sorted(records, key=lambda r: r["result_commit"] != outcome["attempts"][0]["commit"])
    assert second["observed_tip"] == first["result_commit"]


def test_recovery_keeps_a_real_held_result_held_and_cancels_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = make_env(tmp_path, monkeypatch, script=reverse_script())
    crash_second_result(env)
    assert env.next()["request"]["kind"] == "implement-task"
    assert state_of(env) == {"calculator": "cancelled", "plain": "held"}
    assert len(list((env.store() / "held").iterdir())) == 1
