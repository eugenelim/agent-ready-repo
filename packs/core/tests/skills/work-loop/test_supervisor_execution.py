"""Approved gate declarations and closed supervisor execution records."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
SCRIPT_PATHS = {
    "projector": SCRIPTS / "_supervisor_projector.py",
    "execution": SCRIPTS / "_supervisor_execution.py",
    "policy": SCRIPTS / "_policy_import.py",
}


def _load(name: str) -> ModuleType:
    """Load each script under a pack- and skill-specific module name."""
    alias = "core_work_loop_execution_test_" + name
    spec = importlib.util.spec_from_file_location(alias, SCRIPT_PATHS[name])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


proj = _load("projector")
policy = _load("policy")


def _commands() -> list[dict]:
    """Commands retain argument boundaries, order, working directory and expected exit."""
    return [
        {"argv": ["python3", "-m", "pytest", "tests/a test.py"], "cwd": ".", "expected_exit": 0},
        {"argv": ["make", "check"], "cwd": "src", "expected_exit": 0},
    ]


def _spec(commands: object) -> str:
    """Place a declaration inside the approved Agent Rules section."""
    return "# Example\n\n## Agent Rules\n\n```gate-declaration\n" + json.dumps(commands) + "\n```\n"


def test_declaration_preserves_order_and_argument_boundaries() -> None:
    assert proj.gate_declaration(_spec(_commands())) == _commands()


def test_declaration_retains_empty_arguments_and_literal_shell_characters() -> None:
    commands = [{"argv": ["echo", "", "$(ignored); *"], "cwd": ".", "expected_exit": 0}]
    text = _spec(commands).replace("```", "~~~~").replace("\n", "\r\n")
    assert proj.gate_declaration(text) == commands


def test_declaration_edit_changes_existing_approval_digest(tmp_path: Path) -> None:
    path = tmp_path / "spec.md"
    text = _spec(_commands())
    path.write_text(text, encoding="utf-8")
    before = policy.compute_spec_digest(path)
    refs = proj.envelope_references(text, read_record=lambda p: "", list_dir=lambda p: []).refs
    changed = text.replace('"check"', '"lint"')
    path.write_text(changed, encoding="utf-8")
    assert policy.compute_spec_digest(path) != before
    assert proj.envelope_references(
        changed, read_record=lambda p: "", list_dir=lambda p: []
    ).refs["spec_policy"] != refs["spec_policy"]


@pytest.mark.parametrize("text", [
    "## Outcome\n```gate-declaration\n[]\n```\n",
    "## Agent Rules\nNo commands.\n",
    _spec(_commands()) + _spec(_commands()),
    _spec(_commands()) + "\n```gate-declaration\n[]\n```\n",
    "## Agent Rules\n```gate-declaration\n[\n",
    "## Agent Rules\n```gate-declaration\nnot json\n```\n",
    "## Agent Rules\n````markdown\n```gate-declaration\n[]\n```\n````\n",
    _spec([]),
    _spec([{"argv": "make check", "cwd": ".", "expected_exit": 0}]),
    _spec([{"argv": [], "cwd": ".", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": "../outside", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": "/outside", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": ".", "expected_exit": True}]),
    _spec([{"argv": ["make"], "cwd": ".", "expected_exit": 0, "shell": True}]),
])
def test_invalid_or_ambiguous_declaration_refuses(text: str) -> None:
    with pytest.raises(proj.ProjectionRefused):
        proj.gate_declaration(text)


def _record() -> dict:
    """A completed execution binds all identities and records each observed command."""
    return {
        "schema_version": 1,
        "type": "gate-execution.v1",
        "execution_id": "exec-example",
        "run_id": "run-example",
        "request_id": "req-example",
        "issuance_id": "issue-example",
        "task_revision": "a" * 64,
        "candidate_tree_digest": "b" * 64,
        "gate_declaration_digest": "c" * 64,
        "commands": [{
            **_commands()[0], "exit_code": 0, "timed_out": False,
            "stdout_digest": "d" * 64, "stderr_digest": "e" * 64,
        }],
        "outcome": "passed",
    }


def test_execution_record_round_trips() -> None:
    execution = _load("execution")
    record = _record()
    assert execution.decode_execution(execution.encode_execution(record)) == record


@pytest.mark.parametrize("outcome", ["started", "failed"])
def test_nonpassing_and_run_wide_records_round_trip(outcome: str) -> None:
    execution = _load("execution")
    record = {**_record(), "outcome": outcome, "task_revision": None}
    if outcome == "started":
        record["commands"] = []
    else:
        record["commands"][0].update(exit_code=None, timed_out=True)
    assert execution.decode_execution(execution.encode_execution(record)) == record


@pytest.mark.parametrize("field", list(_record()))
def test_each_required_execution_field_refuses_when_missing(field: str) -> None:
    execution = _load("execution")
    record = _record()
    del record[field]
    with pytest.raises(execution.ExecutionRefused):
        execution.encode_execution(record)


@pytest.mark.parametrize("mutation", ["version", "missing", "extra", "nested-extra",
    "nested-missing", "boolean-version", "bad-argv", "bad-digest", "timeout-pass",
    "nonzero-pass", "empty-pass", "bad-outcome"])
def test_invalid_execution_record_refuses(mutation: str) -> None:
    execution = _load("execution")
    record = copy.deepcopy(_record())
    if mutation == "version":
        record["schema_version"] = 2
    elif mutation == "missing":
        del record["request_id"]
    elif mutation == "extra":
        record["proof"] = True
    elif mutation == "nested-extra":
        record["commands"][0]["shell"] = True
    elif mutation == "nested-missing":
        del record["commands"][0]["exit_code"]
    elif mutation == "boolean-version":
        record["schema_version"] = True
    elif mutation == "bad-argv":
        record["commands"][0]["argv"] = "python3"
    elif mutation == "bad-digest":
        record["candidate_tree_digest"] = "invalid"
    elif mutation == "timeout-pass":
        record["commands"][0]["timed_out"] = True
    elif mutation == "nonzero-pass":
        record["commands"][0]["exit_code"] = 1
    elif mutation == "empty-pass":
        record["commands"] = []
    else:
        record["outcome"] = "unknown"
    with pytest.raises(execution.ExecutionRefused):
        execution.decode_execution(json.dumps(record).encode())


@pytest.mark.parametrize("data", [b"{", b"[]", b"\xff", b'{"schema_version":1,"schema_version":1}'])
def test_unreadable_execution_refuses(data: bytes) -> None:
    execution = _load("execution")
    with pytest.raises(execution.ExecutionRefused):
        execution.decode_execution(data)


# Real Git fixtures are shared with the supervisor's other verb suites.
def _harness() -> ModuleType:
    """Load the existing Git harness without adding scripts to sys.path."""
    alias = "core_work_loop_execution_harness"
    path = Path(__file__).resolve().parent / "supervisor_harness.py"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, path)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


def _execution_repo(tmp_path: Path, commands: list[dict]) -> tuple[Path, dict]:
    """Approve committed commands and issue one goal-based implementation request."""
    h = _harness()
    text = h.sup.SPEC.replace("## Agent Rules\n", "## Agent Rules\n\n```gate-declaration\n"
                              + json.dumps(commands) + "\n```\n")
    plan = h.sup.plan(h.sup.task("T1", "Write candidate", mode="goal-based", tests="no stub"))
    repo = h.make_repo(tmp_path, plan=plan, spec=text)
    code, result = h.start(repo)
    assert code == 0, result
    code, result = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0, result
    assert result["request"]["kind"] == "implement-task"
    return repo, result["request"]


def _command(code: str, *, cwd: str = ".") -> dict:
    """Run a literal Python program with the test interpreter."""
    return {"argv": [sys.executable, "-c", code], "cwd": cwd, "expected_exit": 0}


def _execute(repo: Path, request: dict, *, script: Path | None = None) -> dict:
    """Drive the actual CLI process boundary and decode its one JSON result."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(script or SCRIPTS / "work-supervisor.py"), "execute-gates",
         _harness().SPEC_DIR, "--request", request["request_id"]],
        cwd=repo, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)["execution"]


@pytest.mark.parametrize("exit_code", [0, 7])
def test_execute_gates_observes_frozen_candidate(tmp_path: Path, exit_code: int) -> None:
    """Argument boundaries, cwd, output and outcome come from a real frozen subprocess."""
    import hashlib

    command = _command(
        "import pathlib,sys; assert pathlib.Path('candidate.txt').read_text() == 'frozen'; "
        "assert not pathlib.Path('../.git').exists(); "
        "assert sys.argv[1:] == ['', '$(ignored); *']; "
        "pathlib.Path('candidate.txt').write_text('gate mutation'); "
        f"print('observed'); sys.exit({exit_code})", cwd="src",
    )
    command["argv"] += ["", "$(ignored); *"]
    repo, request = _execution_repo(tmp_path, [command])
    (repo / "src").mkdir()
    (repo / "src/candidate.txt").write_text("frozen")
    head = _harness().git(repo, "rev-parse", "HEAD")
    record = _execute(repo, request)
    assert record["outcome"] == ("passed" if exit_code == 0 else "failed")
    assert record["request_id"] == request["request_id"]
    assert record["task_revision"] == request["task"]["revision"]
    assert record["commands"][0] == {
        **command, "exit_code": exit_code, "timed_out": False,
        "stdout_digest": hashlib.sha256(b"observed\n").hexdigest(),
        "stderr_digest": hashlib.sha256(b"").hexdigest(),
    }
    assert _harness().git(repo, "rev-parse", "HEAD") == head
    ws = _harness().workspace(repo)
    store = ws.git.ensure_store(request["run_id"])
    frozen = json.loads((store / ("candidate-" + record["candidate_tree_digest"] + ".json")).read_bytes())
    (repo / "src/candidate.txt").write_text("later mutation")
    with _harness().git_identity():
        ws.git.build_commit(run_id=request["run_id"], step="fixture-admission", operation="implement",
                            base_tree=frozen["tree"])
    assert ws.git.product_tree() == record["candidate_tree_digest"]
    assert _harness().git(repo, "show", "HEAD:src/candidate.txt") == "frozen"
    assert (store / (record["execution_id"] + ".started.json")).exists()
    assert (store / (record["execution_id"] + ".completed.json")).exists()


def test_execute_gates_uses_committed_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A work-tree mutation after the protected-file check cannot supply commands."""
    repo, request = _execution_repo(tmp_path, [_command("print('approved')")])
    h = _harness()
    original = h.loop._refuse_protected_change

    def change_after_check(ws: object, state: object) -> object:
        changed = original(ws, state)
        (repo / h.SPEC_DIR / "spec.md").write_text(_spec([_command("raise SystemExit(9)")]))
        return changed

    monkeypatch.setattr(h.loop, "_refuse_protected_change", change_after_check)
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, result
    assert result["execution"]["commands"][0]["argv"][-1] == "print('approved')"
    assert result["execution"]["outcome"] == "passed"


def test_execute_gates_summed_budget_and_cleanup_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Accelerate the clock, not the children: separate short commands share 1200 seconds."""
    import time

    commands = [_command("import time; time.sleep(.18)") for _ in range(3)]
    repo, request = _execution_repo(tmp_path, commands)
    h = _harness()
    execution = h.cli._supervisor("_supervisor_execution.py")
    real = time.monotonic
    monkeypatch.setattr(execution, "monotonic", lambda: real() * 4000)
    offset = [0.0]
    real_observe = execution._observe
    real_cleanup = execution._cleanup
    cleanup_times: list[float] = []

    def lock_clock() -> float:
        """Include virtual command time in the lock hold, with real setup and cleanup."""
        return real() + offset[0]

    def observe(*args: object) -> object:
        start = real()
        try:
            return real_observe(*args)
        finally:
            offset[0] += (real() - start) * 3999

    def cleanup(*args: object) -> bool:
        ws = h.workspace(repo)
        lock = ws.local.lock_target.with_name(ws.local.lock_target.name + ".lock")
        assert lock.exists()
        result = real_cleanup(*args)
        assert lock.exists()
        cleanup_times.append(lock_clock())
        return result

    monkeypatch.setattr(execution, "_observe", observe)
    monkeypatch.setattr(execution, "_cleanup", cleanup)
    monkeypatch.setattr(execution, "lock_clock", lock_clock)
    before = lock_clock()
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, result
    record = result["execution"]
    assert record["outcome"] == "failed"
    assert any(command["timed_out"] for command in record["commands"])
    assert len(record["commands"]) < 3
    assert 1200 <= cleanup_times[0] - before < 2400
    assert lock_clock() - before < 2400
    ws = h.workspace(repo)
    assert not ws.local.lock_target.with_name(ws.local.lock_target.name + ".lock").exists()


@pytest.mark.parametrize("size", [1048576, 1048577])
def test_execute_gates_output_limit(tmp_path: Path, size: int) -> None:
    """A successful exit cannot mint a pass after exceeding the combined byte cap."""
    import hashlib

    repo, request = _execution_repo(tmp_path, [_command(
        f"import os; os.write(1, b'x' * {size})",
    )])
    record = _execute(repo, request)
    assert record["outcome"] == ("passed" if size == 1048576 else "failed")
    assert record["commands"][0]["stdout_digest"] == hashlib.sha256(b"x" * 1048576).hexdigest()


def test_execute_gates_killed_mid_run_never_completes(tmp_path: Path) -> None:
    """Killing the CLI after started leaves no completed passing record."""
    import subprocess
    import time

    marker = tmp_path / "launched"
    repo, request = _execution_repo(tmp_path, [_command(
        f"import pathlib,time; pathlib.Path({str(marker)!r}).touch(); time.sleep(1)",
    )])
    with subprocess.Popen(
        [sys.executable, str(SCRIPTS / "work-supervisor.py"), "execute-gates",
         _harness().SPEC_DIR, "--request", request["request_id"]], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as process:
        deadline = time.monotonic() + 10
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists()
        process.kill()
        process.communicate(timeout=5)
    store = _harness().workspace(repo).git.ensure_store(request["run_id"])
    assert len(list(store.glob("exec-*.started.json"))) == 1
    assert not list(store.glob("exec-*.completed.json"))


def test_execute_gates_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A real timed-out process leaves a completed failure, never a passing proof."""
    repo, request = _execution_repo(tmp_path, [_command("import time; time.sleep(30)")])
    h = _harness()
    execution = h.cli._supervisor("_supervisor_execution.py")
    monkeypatch.setattr(execution, "GATE_BUDGET_SECONDS", .05)
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, result
    assert result["execution"]["outcome"] == "failed"
    assert result["execution"]["commands"][0]["timed_out"] is True
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    records = [json.loads(path.read_bytes()) for path in store.glob("exec-*.completed.json")]
    assert len(records) == 1 and all(record["outcome"] != "passed" for record in records)


def test_execute_gates_runs_all_declared_commands_after_nonzero(tmp_path: Path) -> None:
    """A normal gate failure records later commands too and still cannot pass."""
    commands = [_command("raise SystemExit(7)"), _command("print('second')")]
    repo, request = _execution_repo(tmp_path, commands)
    record = _execute(repo, request)
    assert record["outcome"] == "failed"
    assert [command["exit_code"] for command in record["commands"]] == [7, 0]
    assert [command["argv"] for command in record["commands"]] == [c["argv"] for c in commands]


def test_execute_gates_combines_stdout_and_stderr_limit(tmp_path: Path) -> None:
    """Two individually small streams cannot evade the per-command output limit."""
    repo, request = _execution_repo(tmp_path, [_command(
        "import os; os.write(1, b'x' * 700000); os.write(2, b'y' * 700000)",
    )])
    assert _execute(repo, request)["outcome"] == "failed"


def test_execute_gates_run_wide_request(tmp_path: Path) -> None:
    """The same verb runs final gates with a null task revision."""
    repo, request = _execution_repo(tmp_path, [_command("print('final')")])
    h = _harness()
    controller = h.Controller(repo, tmp_path / "effects")
    code, result = controller.report({
        "schema_version": 1, "run_id": request["run_id"], "request_id": request["request_id"],
        "kind": "implement-task", "gate": {"passed": True},
    })
    assert code == 0, result
    code, result = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0, result
    assert result["request"]["kind"] == "run-gates"
    record = _execute(repo, result["request"])
    assert record["outcome"] == "passed"
    assert record["task_revision"] is None


def test_execute_gates_refuses_other_request(tmp_path: Path) -> None:
    """An execution cannot be minted for an unissued worker-supplied identity."""
    repo, request = _execution_repo(tmp_path, [_command("print('approved')")])
    h = _harness()
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", "not-issued")
    assert code == 1 and result["refusal"]["code"] == "not-current-attempt"
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    assert not list(store.glob("exec-*.json"))


def test_execute_gates_from_installed_layout(tmp_path: Path) -> None:
    """Copied runtime files load their own siblings without the source .apm hierarchy."""
    import shutil

    repo, request = _execution_repo(tmp_path, [_command("print('installed')")])
    skill = tmp_path / "installed/skills/work-loop"
    shutil.copytree(SCRIPTS.parent, skill, ignore=shutil.ignore_patterns("__pycache__"))
    record = _execute(repo, request, script=skill / "scripts" / "work-supervisor.py")
    assert record["outcome"] == "passed"


def test_execute_gates_cleanup_failure_never_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cleanup failure keeps even a successful command from minting a passing proof."""
    repo, request = _execution_repo(tmp_path, [_command("print('passed command')")])
    h = _harness()
    execution = h.cli._supervisor("_supervisor_execution.py")
    real_cleanup = execution._cleanup

    def failed_cleanup(directory: Path, budget: float) -> bool:
        real_cleanup(directory, budget)
        return False

    monkeypatch.setattr(execution, "_cleanup", failed_cleanup)
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, result
    assert result["execution"]["commands"][0]["exit_code"] == 0
    assert result["execution"]["outcome"] == "failed"


def test_execute_gates_terminates_at_exact_summed_cutoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deterministic 1199.999-to-1200 transition kills a live child at the cutoff."""
    repo, request = _execution_repo(tmp_path, [_command("import time; time.sleep(60)")])
    h = _harness()
    execution = h.cli._supervisor("_supervisor_execution.py")
    ticks = iter([0.0, 0.0, 1199.999, 1199.999, 1200.0])
    samples: list[float] = []
    stopped: list[bool] = []
    real_stop = execution._stop

    def clock() -> float:
        """The execute start, command start, two polls, cutoff, and elapsed read."""
        value = next(ticks, 1200.0)
        samples.append(value)
        return value

    def stop(process: object) -> None:
        """Assert that termination reaps the sleeping producer."""
        real_stop(process)
        stopped.append(process.poll() is not None)

    monkeypatch.setattr(execution, "monotonic", clock)
    monkeypatch.setattr(execution, "_stop", stop)
    code, out = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, out
    record = out["execution"]
    assert record["outcome"] == "failed"
    assert record["commands"][0]["timed_out"] is True
    assert record["commands"][0]["exit_code"] != 0
    assert 1199.999 in samples and samples[-1] == 1200.0
    assert stopped and all(stopped)


def test_execute_gates_overflow_terminates_live_producer(tmp_path: Path) -> None:
    """Overflow must end a child that would otherwise stay alive for a minute."""
    import time

    repo, request = _execution_repo(tmp_path, [_command(
        "import os,time; data=b'x' * (1024*1024+1); "
        "stream=os.fdopen(1, 'wb', buffering=0); stream.write(data); time.sleep(60)",
    )])
    start = time.monotonic()
    record = _execute(repo, request)
    assert time.monotonic() - start < 10
    assert record["outcome"] == "failed"
    assert record["commands"][0]["exit_code"] != 0
    assert record["commands"][0]["timed_out"] is False


def test_execute_gates_slow_preparation_and_cleanup_keep_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Near the stale deadline the lock covers cleanup and no late pass is stored."""
    import os
    import time

    repo, request = _execution_repo(tmp_path, [_command("print('done')")])
    h = _harness()
    execution = h.cli._supervisor("_supervisor_execution.py")
    now = [0.0]
    real_materialize, real_cleanup = execution._materialize, execution._cleanup
    stale = float(h.workspace(repo).policy["run_lock_stale_seconds"])
    lock = h.workspace(repo).local.lock_target
    lock = lock.with_name(lock.name + ".lock")
    seen: list[float] = []

    def prepare(*args: object) -> None:
        """Consume most of the lock window before executing any commands."""
        real_materialize(*args)
        now[0] = stale - 350
        assert lock.exists()

    def cleanup(directory: Path, budget: float) -> bool:
        """Drain the bounded cleanup allowance with the lock still held."""
        assert lock.exists()
        assert 0 < budget <= 50
        result = real_cleanup(directory, budget)
        now[0] += min(execution.CLEANUP_SECONDS, budget)
        assert now[0] < stale
        assert lock.exists()
        token = lock.read_bytes()
        # Make the real lock file as old as the simulated execution. A second
        # holder must time out instead of reclaiming it during cleanup.
        wall = time.time()
        os.utime(lock, (wall - now[0], wall - now[0]))
        locking = h.cli._supervisor("_supervisor_admission.py").sibling("_statelock.py")
        with pytest.raises(locking.StateLockTimeout), locking.exclusive(
            h.workspace(repo).local.lock_target, timeout=0, stale_after=stale,
        ):
            pytest.fail("a second holder reclaimed the live run lock")
        assert lock.read_bytes() == token
        seen.append(now[0])
        return result

    monkeypatch.setattr(execution, "lock_clock", lambda: now[0])
    monkeypatch.setattr(execution, "_materialize", prepare)
    monkeypatch.setattr(execution, "_cleanup", cleanup)
    code, out = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0, out
    assert seen == [stale - 320]
    assert not lock.exists()
    assert out["execution"]["outcome"] == "passed"


@pytest.mark.parametrize("termination", ["SIGTERM", "SIGKILL", "recovery"])
def test_orphan_gate_deadline_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, termination: str,
) -> None:
    """A dead supervisor leaves no proof; its bounded group and scratch are reclaimed."""
    import os
    import signal
    import time

    h = _harness()
    launcher = h.cli._supervisor("_supervisor_launcher.py")
    if launcher.process_start(os.getpid()) is None:
        pytest.skip("host denies reading process start times; orphan identity cannot be checked")
    marker = tmp_path / "gate-launched.json"
    parent_kill = "os.kill(os.getppid(), signal.SIGTERM); " if termination == "SIGTERM" else ""
    command = _command(
        "import os,signal,time,json,pathlib; "
        f"pathlib.Path({str(marker)!r}).write_text(json.dumps([os.getpid(), str(pathlib.Path.cwd())])); "
        + parent_kill + "time.sleep(60)",
    )
    repo, request = _execution_repo(tmp_path, [command])
    execution = h.cli._supervisor("_supervisor_execution.py")
    monkeypatch.setattr(execution, "GATE_BUDGET_SECONDS", 30 if termination == "recovery" else .6)
    child = os.fork()
    if child == 0:
        try:
            h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
        finally:
            os._exit(0)
    gate_pid = None
    try:
        deadline = time.monotonic() + 20
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists()
        gate_pid, scratch = json.loads(marker.read_text())
        gate_start = launcher.process_start(gate_pid)
        assert gate_start is not None
        if termination != "SIGTERM":
            os.kill(child, signal.SIGKILL)
        os.waitpid(child, 0)
        store = h.workspace(repo).git.ensure_store(request["run_id"])
        started, = store.glob("exec-*.started.json")
        saved = json.loads(started.read_bytes())
        assert saved["runtime"]["processes"] == [{"pgid": gate_pid, "start": gate_start}]
        assert saved["runtime"]["scratch"] == scratch
        assert not list(store.glob("exec-*.completed.json"))
        if termination != "recovery":
            deadline = time.monotonic() + 4
            while launcher.process_start(gate_pid) == gate_start and time.monotonic() < deadline:
                time.sleep(.02)
            assert launcher.process_start(gate_pid) != gate_start
        assert Path(scratch).exists()
        code, result = h.run_cli(repo, "status", h.SPEC_DIR)
        assert code == 0, result
        assert launcher.process_start(gate_pid) != gate_start
        assert not Path(scratch).exists()
        assert not list(store.glob("exec-*.completed.json"))
    finally:
        if gate_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(gate_pid, signal.SIGKILL)
        with contextlib.suppress(ProcessLookupError):
            os.kill(child, signal.SIGKILL)
        with contextlib.suppress(ChildProcessError):
            os.waitpid(child, 0)


def test_orphan_recovery_does_not_signal_recycled_pid(tmp_path: Path) -> None:
    """A live bystander with the same pid but another start token is preserved."""
    import os
    import subprocess
    import tempfile

    h = _harness()
    launcher = h.cli._supervisor("_supervisor_launcher.py")
    if launcher.process_start(os.getpid()) is None:
        pytest.skip("host denies reading process start times; orphan identity cannot be checked")
    repo, request = _execution_repo(tmp_path, [_command("print('ok')")])
    record = _execute(repo, request)
    execution = h.cli._supervisor("_supervisor_execution.py")
    ws = h.workspace(repo)
    scratch = Path(tempfile.mkdtemp(prefix="work-supervisor-gates-")).resolve()
    with subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                          start_new_session=True) as bystander:
        try:
            record.update(execution_id="exec-recycled", commands=[], outcome="started")
            record["runtime"] = {
                "scratch": str(scratch), "supervisor_pid": 99999999,
                "supervisor_start": "gone", "processes": [
                    {"pgid": bystander.pid, "start": "a-different-process-start"},
                ],
            }
            ws.attempts._put(request["run_id"], "exec-recycled.started.json",
                             execution.encode_execution(record))
            execution.recover(ws)
            assert bystander.poll() is None
            assert not scratch.exists()
        finally:
            bystander.kill()
            bystander.wait(timeout=5)


def test_watchdog_ends_descendants_after_leader_exit(tmp_path: Path) -> None:
    """A command's departed leader cannot leave its same-group child past the deadline."""
    import os
    import signal
    import subprocess
    import time

    execution = _load("execution")
    launcher = execution._launcher()
    if launcher.process_start(os.getpid()) is None:
        pytest.skip("host denies reading process start times; orphan identity cannot be checked")
    marker = tmp_path / "descendant"
    code = (
        "import sys,subprocess,pathlib; sys.stdin.buffer.read(1); "
        f"p=subprocess.Popen([{sys.executable!r}, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(marker)!r}).write_text(str(p.pid))"
    )
    with subprocess.Popen([sys.executable, "-c", code], stdin=subprocess.PIPE,
                          start_new_session=True) as leader:
        try:
            start = launcher.process_start(leader.pid)
            assert start is not None
            assert leader.stdin is not None
            leader.stdin.write(b"x")
            leader.stdin.close()
            leader.wait(timeout=5)
            child = int(marker.read_text())
            child_start = launcher.process_start(child)
            assert child_start is not None
            subprocess.run(
                [sys.executable, "-I", str(SCRIPTS / "_supervisor_execution.py"), "--watchdog",
                 str(leader.pid), start, str(time.monotonic() + .1)],
                stdin=subprocess.DEVNULL, check=True, timeout=10,
            )
            deadline = time.monotonic() + 3
            while launcher.process_start(child) == child_start and time.monotonic() < deadline:
                time.sleep(.01)
            assert launcher.process_start(child) != child_start
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(leader.pid, signal.SIGKILL)


@pytest.mark.parametrize("lookup", [
    "transient", "unknown", "alive-unreadable", "timeout", "read-error", "gone", "reused",
])
@pytest.mark.parametrize("verb", ["recover", "status"])
def test_recovery_requires_confirmed_supervisor_death(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lookup: str, verb: str,
) -> None:
    """An unreadable process table cannot terminate an active gate from another verb."""
    import os
    from types import SimpleNamespace

    h = _harness()
    repo, request = _execution_repo(tmp_path, [_command("pass")])
    execution = h.cli._supervisor("_supervisor_execution.py")
    ws = h.workspace(repo)
    record = _record()
    record.update(execution_id="exec-live", run_id=request["run_id"], commands=[], outcome="started")
    record["runtime"] = {
        "scratch": str(tmp_path / "must-not-clean"), "supervisor_pid": os.getpid(),
        "supervisor_start": "original", "processes": [{"pgid": 12345, "start": "gate"}],
    }
    ws.attempts._put(request["run_id"], "exec-live.started.json",
                     execution.encode_execution(record))
    real_launcher = execution._launcher()
    reads: list[int] = []
    ended: list[dict] = []

    def reader(pid: int) -> str | None:
        """Return transient failure, sustained uncertainty, absence, or PID reuse."""
        reads.append(pid)
        if lookup == "transient":
            return None if len(reads) == 1 else "original"
        if lookup == "timeout":
            import subprocess
            raise subprocess.TimeoutExpired("ps", 10)
        if lookup == "read-error":
            raise OSError("process table unreadable")
        return "replacement" if lookup == "reused" else None

    def probe(pid: int, sig: int) -> None:
        """Only ESRCH proves absence; permission failure leaves identity unknown."""
        assert pid == os.getpid() and sig == 0
        if lookup == "gone":
            raise ProcessLookupError
        if lookup == "unknown":
            raise PermissionError

    monkeypatch.setattr(execution, "_launcher", lambda: SimpleNamespace(
        process_start=reader, _supervisor=real_launcher._supervisor))
    monkeypatch.setattr(execution.os, "kill", probe)
    monkeypatch.setattr(execution, "_end_matching", ended.append)
    if lookup in ("gone", "reused"):
        # Recovery may clean only its own scratch namespace.
        import tempfile
        scratch = Path(tempfile.mkdtemp(prefix="work-supervisor-gates-")).resolve()
        record["runtime"]["scratch"] = str(scratch)
        ws.attempts._put(request["run_id"], "exec-live.started.json",
                         execution.encode_execution(record), replace=True)
    if verb == "status":
        code, payload = h.run_cli(repo, "status", h.SPEC_DIR)
        assert code == 0, payload
    else:
        execution.recover(ws)
    recovered = ws.git._store_dir(request["run_id"]) / "exec-live.recovered"
    assert ended == ([{"pgid": 12345, "start": "gate"}] if lookup in ("gone", "reused") else [])
    assert recovered.exists() == (lookup in ("gone", "reused"))
    if lookup == "transient":
        assert len(reads) >= 2


@pytest.mark.parametrize("executable", [False, True])
def test_mode_only_candidates_keep_execution_specific_manifests(
    tmp_path: Path, executable: bool,
) -> None:
    """Each proof admits the exact executable bit its subprocess observed."""
    import hashlib

    h = _harness()
    repo, request = _execution_repo(tmp_path, [_command(
        "import pathlib; print(oct(pathlib.Path('mode.txt').stat().st_mode & 0o777))",
    )])
    target = repo / "mode.txt"
    target.write_text("same bytes")
    target.chmod(0o644)
    first = _execute(repo, request)
    target.chmod(0o755)
    second = _execute(repo, request)
    assert first["candidate_tree_digest"] == second["candidate_tree_digest"]
    ws = h.workspace(repo)
    store = ws.git.ensure_store(request["run_id"])
    manifests = [json.loads((store / ("candidate-" + record["execution_id"] + ".json")).read_bytes())
                 for record in (first, second)]
    assert manifests[0]["mode_tree_digest"] != manifests[1]["mode_tree_digest"]
    for manifest in manifests:
        assert (store / ("candidate-" + manifest["mode_tree_digest"] + ".json")).exists()
    chosen, unused = (second, first) if executable else (first, second)
    (store / (unused["execution_id"] + ".completed.json")).unlink()
    target.chmod(0o644 if executable else 0o755)
    result = {"schema_version": 1, "request_id": request["request_id"],
              "run_id": request["run_id"], "kind": "implement-task", "gate": {"passed": True}}
    path = tmp_path / "mode-result.json"
    path.write_text(json.dumps(result))
    code, out = h.run_cli(repo, "report", h.SPEC_DIR, str(path))
    assert code == 0, out
    assert h.git(repo, "ls-tree", "HEAD", "mode.txt").startswith(
        "100755" if executable else "100644")
    assert h.workspace(repo).git.product_tree() == chosen["candidate_tree_digest"]
    output = b"0o755\n" if executable else b"0o644\n"
    assert chosen["commands"][0]["stdout_digest"] == hashlib.sha256(output).hexdigest()


def test_stale_mode_manifest_is_not_reused(tmp_path: Path) -> None:
    """A colliding stored manifest cannot replace the entries frozen for this run."""
    h = _harness()
    repo, request = _execution_repo(tmp_path, [_command("pass")])
    target = repo / "mode.txt"
    target.write_text("same bytes")
    target.chmod(0o644)
    first = _execute(repo, request)
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    original = json.loads((store / ("candidate-" + first["execution_id"] + ".json")).read_bytes())
    target.chmod(0o755)
    second = _execute(repo, request)
    newer = json.loads((store / ("candidate-" + second["execution_id"] + ".json")).read_bytes())
    stale = store / ("candidate-" + newer["mode_tree_digest"] + ".json")
    stale.write_text(json.dumps(original))
    code, out = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 1 and out["refusal"]["code"] == "gate-execution-invalid", out
    assert len(list(store.glob("exec-*.completed.json"))) == 2


@pytest.mark.parametrize("links", [
    {"b": "z/../leak", "z": "."},
    {"a": "b", "b": "z/../leak", "z": "."},
    {"a": "missing"},
    {"a": "b", "b": "a"},
    {"a": "/outside"},
])
def test_execute_gates_refuses_unsafe_link_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, links: dict[str, str],
) -> None:
    """Validate the finished link graph before launching even the first gate."""
    marker = tmp_path / "gate-started"
    repo, request = _execution_repo(tmp_path, [_command(
        f"from pathlib import Path; Path({str(marker)!r}).write_text('started')",
    )])
    h = _harness()
    ws = h.workspace(repo)
    # Supply the frozen Git port result directly: working-tree link checks are
    # another boundary and must not mask validation of an already-frozen tree.
    with ws.git._private_index("HEAD") as env:
        for name, value in links.items():
            oid = ws.git.run("hash-object", "-w", "--stdin", stdin=value.encode()).decode().strip()
            ws.git.run("update-index", "--add", "--cacheinfo", "120000," + oid + "," + name,
                       env=env)
        tree = ws.git.text("write-tree", env=env).strip()
    execution = h.cli._supervisor("_supervisor_execution.py")
    monkeypatch.setattr(execution, "_freeze", lambda *args: (tree, ws.git.product_tree(tree)))
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 1, result
    assert result["refusal"]["code"] == "gate-execution-invalid"
    assert not marker.exists()
    store = _harness().workspace(repo).git.ensure_store(request["run_id"])
    started, = store.glob("exec-*.started.json")
    runtime = json.loads(started.read_bytes())["runtime"]
    assert runtime["processes"] == []
    assert not Path(runtime["scratch"]).exists()
    assert not list(store.glob("exec-*.completed.json"))


def test_execute_gates_accepts_confined_link_chains(tmp_path: Path) -> None:
    """Forward chains and directory links still expose the frozen bytes to gates."""
    repo, request = _execution_repo(tmp_path, [_command(
        "from pathlib import Path; "
        "assert Path('a').read_text() == Path('alias/data').read_text() == 'frozen'",
    )])
    (repo / "data").mkdir()
    (repo / "data/value").write_text("frozen")
    (repo / "a").symlink_to("b")
    (repo / "b").symlink_to("data/value")
    (repo / "alias").mkdir()
    (repo / "alias/data").symlink_to("../b")
    (repo / "directory").symlink_to("data")
    record = _execute(repo, request)
    assert record["outcome"] == "passed"
    assert record["commands"][0]["exit_code"] == 0


@pytest.mark.parametrize("entries", [
    {"b": ("120000", b"z/../leak"), "z": ("120000", b".")},
    {"a": ("120000", b"missing")},
    {"a": ("120000", b"b"), "b": ("120000", b"a")},
    {"a": ("120000", b"")},
    {"a": ("120000", b"bad\0target")},
    {"a": ("120000", b"/outside")},
    {"a": ("160000", b"not a blob")},
    {"a": ("010644", b"not a regular file")},
    {".git/config": ("100644", b"bad")},
    {".GIT/config": ("100644", b"bad")},
    {"A/one": ("100644", b"one"), "a/two": ("100644", b"two")},
    {"a": ("100644", b"one"), "A": ("100755", b"two")},
    {"caf\u00e9/one": ("100644", b"one"), "cafe\u0301/two": ("100644", b"two")},
    {"a/../leak": ("100644", b"bad")},
    {"/outside": ("100644", b"bad")},
    {"a//b": ("100644", b"bad")},
    {"a\\b": ("100644", b"bad")},
    {"a:b": ("100644", b"bad")},
    {"a./b": ("100644", b"bad")},
    {"a /b": ("100644", b"bad")},
    {("d/" * 65) + "file": ("100644", b"bad")},
    {"a": ("120000", b"."), "a/file": ("100644", b"bad")},
    {"a/file": ("100644", b"bad"), "a": ("120000", b".")},
])
def test_materialize_refuses_unsafe_entries(
    tmp_path: Path, entries: dict[str, tuple[str, bytes]],
) -> None:
    """Malformed trees and host-dependent aliases fail with a closed refusal."""
    from types import SimpleNamespace

    execution = _load("execution")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "leak"
    outside.write_bytes(b"untouched")
    ws = SimpleNamespace(git=SimpleNamespace(
        tree_modes=lambda tree: {p: (mode, p) for p, (mode, _) in entries.items()},
        blob=lambda oid, limit=None: entries[oid][1],
    ))
    with pytest.raises(execution.ExecutionRefused) as error:
        execution._materialize(ws, "tree", scratch, float("inf"))
    assert error.value.code == "gate-execution-invalid"
    assert outside.read_bytes() == b"untouched"


@pytest.mark.parametrize("obstacle", ["parent-link", "file-link", "hardlink", "fifo"])
def test_materialize_never_writes_through_existing_entries(
    tmp_path: Path, obstacle: str,
) -> None:
    """Even a planted entry cannot redirect a materialization write outside scratch."""
    import os
    from types import SimpleNamespace

    execution = _load("execution")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "file"
    victim.write_bytes(b"untouched")
    if obstacle == "parent-link":
        (scratch / "parent").symlink_to(outside, target_is_directory=True)
    else:
        (scratch / "parent").mkdir()
        target = scratch / "parent/file"
        if obstacle == "file-link":
            target.symlink_to(victim)
        elif obstacle == "hardlink":
            os.link(victim, target)
        else:
            os.mkfifo(target)
    ws = SimpleNamespace(git=SimpleNamespace(
        tree_modes=lambda tree: {"parent/file": ("100644", "blob")},
        blob=lambda oid, limit=None: b"overwritten",
    ))
    # Refusal must precede opening a FIFO, which would otherwise block the test.
    if obstacle == "fifo":
        monkey = pytest.MonkeyPatch()
        original = Path.write_bytes

        def bounded_write(path: Path, data: bytes) -> int:
            """Turn the old blocking FIFO write into a deterministic failure."""
            assert path != target, "materialization attempted to open a FIFO"
            return original(path, data)

        monkey.setattr(Path, "write_bytes", bounded_write)
    try:
        with pytest.raises(execution.ExecutionRefused):
            execution._materialize(ws, "tree", scratch, float("inf"))
    finally:
        if obstacle == "fifo":
            monkey.undo()
    assert victim.read_bytes() == b"untouched"


def test_materialize_neutralizes_source_hardlinks(tmp_path: Path) -> None:
    """Git blobs are copied to independent inodes rather than sharing source links."""
    import os
    from types import SimpleNamespace

    source = tmp_path / "source"
    source.write_bytes(b"source")
    os.link(source, tmp_path / "hardlink")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    ws = SimpleNamespace(git=SimpleNamespace(
        tree_modes=lambda tree: {"file": ("100644", "blob")},
        blob=lambda oid, limit=None: source.read_bytes(),
    ))
    _load("execution")._materialize(ws, "tree", scratch, float("inf"))
    assert (scratch / "file").stat().st_nlink == 1
    (scratch / "file").write_bytes(b"gate mutation")
    assert source.read_bytes() == b"source"


def test_materialize_refuses_absolute_target_inside_scratch(tmp_path: Path) -> None:
    """An absolute target is host-bound even when its current spelling is inside."""
    import os
    from types import SimpleNamespace

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    blobs = {"file": b"frozen", "link": os.fsencode(scratch / "file")}
    ws = SimpleNamespace(git=SimpleNamespace(
        tree_modes=lambda tree: {"file": ("100644", "file"), "link": ("120000", "link")},
        blob=lambda oid, limit=None: blobs[oid],
    ))
    execution = _load("execution")
    with pytest.raises(execution.ExecutionRefused):
        execution._materialize(ws, "tree", scratch, float("inf"))


@pytest.mark.parametrize("exit_code", [0, 7])
@pytest.mark.parametrize("expected_exit", [0, 7])
def test_observer_pass_requires_zero_independent_of_declaration(
    tmp_path: Path, exit_code: int, expected_exit: int,
) -> None:
    """Even a bypassed declaration cannot turn a nonzero process exit into a pass."""
    execution = _load("execution")
    command = {**_command(f"raise SystemExit({exit_code})"), "expected_exit": expected_exit}
    observed, passed = execution._observe(command, tmp_path, 10)
    assert observed["exit_code"] == exit_code
    assert passed is (exit_code == 0)


def test_execution_record_refuses_matching_nonzero_exit() -> None:
    """A forged expected exit never validates a nonzero passing record."""
    execution = _load("execution")
    record = _record()
    record["commands"][0].update(expected_exit=7, exit_code=7)
    with pytest.raises(execution.ExecutionRefused):
        execution.decode_execution(json.dumps(record).encode())


def test_execute_gates_refuses_nonzero_expected_exit(tmp_path: Path) -> None:
    """The real execute-gates CLI refuses the declaration before running commands."""
    command = {**_command("raise SystemExit(7)"), "expected_exit": 7}
    repo, request = _execution_repo(tmp_path, [command])
    h = _harness()
    code, result = h.run_cli(repo, "execute-gates", h.SPEC_DIR,
                             "--request", request["request_id"])
    assert code == 1, result
    assert result["refusal"]["code"] == "invalid-gate-declaration"
    assert "expected_exit must be the integer 0" in str(result["refusal"])
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    assert not list(store.glob("*.completed.json"))


def test_execute_gates_materializes_tracked_files_over_the_review_read_limit(tmp_path: Path) -> None:
    """A tracked file larger than the review read limit reaches the scratch copy intact."""
    size = 1536 * 1024
    command = _command(
        "import hashlib,pathlib; data = pathlib.Path('big.bin').read_bytes(); "
        f"assert len(data) == {size}; print(hashlib.sha256(data).hexdigest())",
    )
    repo, request = _execution_repo(tmp_path, [command])
    (repo / "big.bin").write_bytes(bytes(range(256)) * (size // 256))
    record = _execute(repo, request)
    assert record["outcome"] == "passed", record
