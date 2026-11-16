"""_supervisor_tdd — the red-before-green guard and task attempts.

No production change for a task that declares stubs is admitted until the
supervisor has itself observed every stub, byte-identical to the plan, exit
with a code its fence declares as red. Red proof belongs to the task and its
stub digest. When the stub bytes are already in ``HEAD`` (the task was revised
after its stub commit), the supervisor runs them on a scratch copy of ``HEAD``
and commits a ``red`` step itself. A stub that already passes is refused with
``stub-not-red``. When that refusal answers a worker's ``write-stub`` result and
the attempt checks and the post-launch check find no difference, the attempt
closes: the files the attempt and its launch changed are discarded, nothing from
the result is committed, and the supervisor records in its store that a named
human's confirmation is owed. The next change to a trusted file is then opened
as a ``human-decision`` with its diff instead of being committed as a replan, so
the plan author fixes the fence (fails for the intended reason, moves, or is
removed) and a human confirms those exact bytes. A decline commits nothing:
``next`` refuses until the trusted files match ``HEAD`` again, whatever they hold
meanwhile. Restoring them brings back the fence that was not red, so ``next``
reissues ``write-stub`` and the stub runs again; only after that attempt is refused
and closed again does a different fence edit open a new confirmation. A file the
discard could not remove is listed in the refusal and blocks the next step until the
controller removes it or restores it to ``HEAD``. The recovery lifecycle lives in
``_supervisor_recovery``. A task with no stubs needs no red proof.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_loop = _supervisor("_supervisor_loop.py")
Refusal = _loop.Refusal

__all__ = ["commit_supervisor_red", "observe", "report_task", "task_action"]


def _stub_view(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [{k: s[k] for k in ("path", "run", "red_exit", "digest")} for s in task["stubs"]]


def task_action(ws: Any, state: Any, task: dict[str, Any]) -> Any:
    """The current action for the first incomplete task."""
    if task["stubs"] and (task["task_id"], task["stub_digest"]) not in state.red:
        if _loop.untrusted_blocked(state):
            return _loop.untrusted_decision(ws, state)
        if all(ws.git.show(s["path"]) == s["content"].encode("utf-8") for s in task["stubs"]):
            return _loop.Action("auto-red", detail={"task": task})
        return _loop.Action(
            "request",
            _loop.make_request(
                ws,
                state,
                "write-stub",
                f"stub:{task['task_id']}:{task['stub_digest']}",
                task=_loop._task_ref(task),
                stubs=_stub_view(task),
            ),
        )
    if _loop.untrusted_blocked(state):
        return _loop.untrusted_decision(ws, state)
    attempt = state.attempt(task)
    return _loop.Action(
        "request",
        _loop.make_request(
            ws,
            state,
            "implement-task",
            f"impl:{task['task_id']}:{task['revision']}:{attempt}",
            task=_loop._task_ref(task),
            attempt=attempt,
        ),
    )


def _scratch_tree(ws: Any, directory: Path) -> None:
    """Materialize HEAD's tree into *directory* with link-safe extraction only."""
    if not hasattr(tarfile, "data_filter"):
        raise Refusal(
            "red-proof-unsafe-extraction",
            "controller",
            "this Python cannot extract archives safely; use 3.11.4 or later",
        )
    archive = ws.git.run("archive", "--format=tar", "HEAD")
    try:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(directory, filter="data")
    except (tarfile.TarError, OSError) as exc:
        raise Refusal(
            "red-proof-extraction-refused",
            "controller",
            f"HEAD cannot be materialized safely: {exc}",
        ) from exc


def _write_inside(root: Path, rel: str, content: bytes) -> None:
    """Write *content* at *rel* under *root*, refusing any link on the way."""
    current = root
    parts = rel.split("/")
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise Refusal("red-proof-link-refused", "controller", f"{rel} crosses a link")
        current.mkdir(exist_ok=True)
    target = current / parts[-1]
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    try:
        if target.is_symlink():
            raise OSError("the stub path is a link")
        fd = os.open(target, flags, 0o600)
    except OSError as exc:
        raise Refusal("red-proof-link-refused", "controller", f"{rel}: {exc}") from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(content)


def observe(
    ws: Any, task: dict[str, Any], overlay: dict[str, bytes]
) -> list[tuple[str, int | None]]:
    """Run each stub on a scratch copy of HEAD plus *overlay*; return its exit code.

    The stubs share one budget, so red proof ends inside the run lock's stale
    window however many stubs a task declares.
    """
    timeout = float(ws.policy["stub_timeout_seconds"])
    deadline = time.monotonic() + float(ws.policy["red_proof_budget_seconds"])
    results: list[tuple[str, int | None]] = []
    with tempfile.TemporaryDirectory(prefix="work-supervisor-red-") as scratch:
        directory = Path(scratch).resolve()
        _scratch_tree(ws, directory)
        for rel, content in overlay.items():
            _write_inside(directory, rel, content)
        for stub in task["stubs"]:
            argv = [part.replace("{path}", stub["path"]) for part in shlex.split(stub["run"])]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                results.append((stub["path"], None))
                continue
            try:
                done = subprocess.run(
                    argv,
                    cwd=str(directory),
                    capture_output=True,
                    timeout=min(timeout, remaining),
                    check=False,
                )
                results.append((stub["path"], done.returncode))
            except (OSError, subprocess.TimeoutExpired):
                results.append((stub["path"], None))
    return results


def _refuse_untrusted_launch(state: Any) -> None:
    """Refuse a red proof for an untrusted run that has no verified containment."""
    if _loop.untrusted_blocked(state):
        raise Refusal(
            "untrusted-code-refused",
            "owner",
            "the run is untrusted and no verified containment is available, so no red "
            "proof or scratch receipt is launched",
        )


def _all_red(task: dict[str, Any], observed: list[tuple[str, int | None]]) -> bool:
    by_path = {s["path"]: s for s in task["stubs"]}
    return all(code is not None and code in by_path[path]["red_exit"] for path, code in observed)


def _not_red(
    task: dict[str, Any],
    observed: list[tuple[str, int | None]],
    leftovers: dict[str, str] | None = None,
    *,
    closed: bool = False,
) -> Any:
    detail = ", ".join(f"{p} exited {c}" for p, c in observed)
    message = f"{task['position']} stubs are not red ({detail}); "
    if not closed:
        return Refusal(
            "stub-not-red",
            "plan author",
            message + "make the `stub` fence fail for the intended reason or remove it",
        )
    message += "the attempt is closed and nothing from it is committed. "
    if leftovers:
        message += (
            "These files could not be discarded and must be removed or restored to "
            "HEAD before the run continues: " + _loop._attempt._named(leftovers) + ". "
        )
    else:
        message += "Its files are discarded. "
    return Refusal(
        "stub-not-red",
        "plan author",
        message + "Make the `stub` fence fail for the intended reason, move it, or remove it: "
        "the next `next` shows that plan change and its diff for a named human to confirm "
        "or decline before it is committed",
    )


def _trailers(task: dict[str, Any]) -> dict[str, str]:
    return {
        "Supervisor-Task": task["task_id"],
        "Supervisor-Task-Revision": task["revision"],
        "Supervisor-Stub-Digest": task["stub_digest"] or "none",
    }


def _red_receipt(ws: Any, state: Any, step: str, task: dict[str, Any]) -> dict[str, Any]:
    return _loop.receipt(
        state,
        step,
        criterion=f"task:{task['task_id']}",
        term=f"red:{task['stub_digest']}",
        observation="red",
        outcome="red",
        fingerprint=task["stub_digest"],
        revision=task["revision"],
    )


def commit_supervisor_red(ws: Any, state: Any, task: dict[str, Any]) -> Any:
    """Observe committed stubs on HEAD and record the supervisor's red proof."""
    _refuse_untrusted_launch(state)
    with ws.attempts.launched(state, f"red:{task['task_id']}:{task['stub_digest']}"):
        observed = observe(ws, task, {})
    if not _all_red(task, observed):
        return _not_red(task, observed)
    step = f"red:{task['task_id']}:{task['stub_digest']}"
    evidence = ws.evidence_append([_red_receipt(ws, state, step, task)])
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="red",
        trailers=_trailers(task),
        appends={"evidence.jsonl": evidence},
        summary=f"{task['position']} red",
        known_steps=state.steps,
    )
    return None


def _commit_result(ws: Any, request: dict[str, Any], **step: Any) -> None:
    """Commit a product result against the commit its request was issued at.

    A conflict that a supervisor step caused (the product ref still holds a recorded
    value) marks the attempt stale, so the next verb issues the same request again.
    """
    try:
        ws.git.build_commit(
            **step, product_source=ws.attempts.source_commit(request["request_id"])
        )
    except Refusal as exc:
        if exc.code == "integration-conflict":
            try:
                ws.attempts.mark_stale_if_landed()
            except Exception as failure:  # noqa: BLE001 - shown beside the refusal, never instead
                _loop._commit.append_note(
                    exc, f"the attempt could not be marked stale ({type(failure).__name__})"
                )
        raise


def _same_gate_issuance(ws: Any, issuance: Any, identity: str) -> bool:
    """Keep unused proof across an identical retry, never across changed authority."""
    current = f"{issuance.run_id}:{issuance.seq:06d}"
    if identity == current:
        return True
    prefix, separator, sequence = identity.rpartition(":")
    if (not separator or prefix != issuance.run_id or len(sequence) != 6
            or not sequence.isascii() or not sequence.isdigit()
            or not 0 < int(sequence) < issuance.seq):
        return False
    fs = _loop.sibling("_file_safety.py")
    records = []
    for seq in (int(sequence), issuance.seq):
        path = issuance.store / "attempts" / f"{seq:06d}.json"
        record = json.loads(bytes(fs.read_confined_regular_file(
            issuance.store, path, max_bytes=16 * 1024 * 1024,
        )))
        if not ws.attempts._valid(record, issuance.run_id):
            raise ValueError("gate issuance record is malformed")
        records.append(record)
    # Reissuing after a refusal may change the sequence, but no bound fact:
    # request, source commit, ref, trusted files, and Git state must all agree.
    return bool(records[0] == records[1])


def validate_gate_claim(ws: Any, state: Any, gate: dict[str, Any]) -> None:
    """New protocol reports assert only a Boolean; legacy pins retain their shape."""
    pins = ws.attempts._store_record(state.run_id, "pins.json")
    if pins is not None and "gate_execution_protocol" not in pins:
        return
    if set(gate) != {"passed"}:
        raise Refusal(
            "result-fact-refused", "controller", "gate may assert only passed",
        )


def gate_proof(ws: Any, state: Any, request: dict[str, Any]) -> dict[str, Any]:
    """Bind supervisor proof and consume it in the admission commit's trailers.

    The run lock covers lookup and commit. Reachable commit trailers are the
    consumption ledger, so neither a failed ref compare nor a crash can consume
    proof separately from admission. Prior pin records retain boolean admission.
    """
    pins = ws.attempts._store_record(state.run_id, "pins.json")
    if pins is not None and "gate_execution_protocol" not in pins:
        return {}
    if pins is not None and (
        type(pins.get("gate_execution_protocol")) is not int
        or pins["gate_execution_protocol"] != 1
    ):
        raise Refusal("gate-execution-mismatch", "controller", "unknown gate proof protocol")
    execution = _loop.sibling("_supervisor_execution.py")
    fs = _loop.sibling("_file_safety.py")
    store = ws.git.ensure_store(state.run_id)
    consumed = {c.trailers.get("Supervisor-Gate-Execution") for c in state.commits}
    issuance = ws.attempts.open
    if issuance is None:
        raise Refusal("gate-execution-missing", "controller", "no gate issuance is open")
    approved = next((c.sha for c in reversed(state.commits) if c.operation == "approval"), None)
    try:
        records = []
        for path in fs.list_confined_regular_files(
            store, store, max_files=10000, max_entries=20000,
        ):
            if path.parent == store and path.name.endswith(".completed.json"):
                records.append(execution.decode_execution(bytes(fs.read_confined_regular_file(
                    store, path, max_bytes=1024 * 1024,
                ))))
        if not any(record["execution_id"] not in consumed for record in records):
            raise Refusal("gate-execution-missing", "controller",
                          "no unconsumed completed gate execution")
        raw = ws.git.show(ws.spec_rel + "/spec.md", approved) if approved else None
        if raw is None:
            raise ValueError("approved spec is unreadable")
        commands = _loop._projector.gate_declaration(raw.decode("utf-8"))
        declaration_digest = hashlib.sha256(json.dumps(
            commands, sort_keys=True, separators=(",", ":"),
        ).encode()).hexdigest()
        expected = {
            "run_id": state.run_id, "request_id": request["request_id"],
            "issuance_id": f"{issuance.run_id}:{issuance.seq:06d}",
            "task_revision": request.get("task", {}).get("revision"),
            "gate_declaration_digest": declaration_digest,
        }
        mismatched = False
        for record in records:
            if record["execution_id"] in consumed:
                continue
            if (any(record[key] != value for key, value in expected.items()
                    if key != "issuance_id")
                    or not _same_gate_issuance(ws, issuance, record["issuance_id"])):
                mismatched = True
                continue
            if record["outcome"] != "passed":
                continue
            declared = [{key: command[key] for key in ("argv", "cwd", "expected_exit")}
                        for command in record["commands"]]
            if declared != commands:
                mismatched = True
                continue
            digest = record["candidate_tree_digest"]
            manifest = execution.candidate_manifest(
                ws, state.run_id, "candidate-" + record["execution_id"] + ".json",
            )
            mode_digest = manifest.get("mode_tree_digest")
            if (set(manifest) != {"schema_version", "tree", "candidate_tree_digest",
                                  "mode_tree_digest"}
                    or type(manifest["schema_version"]) is not int
                    or manifest["schema_version"] != 1
                    or manifest["candidate_tree_digest"] != digest
                    or not execution._digest(mode_digest)
                    or not isinstance(manifest["tree"], str)
                    or ws.git.product_tree(manifest["tree"]) != digest
                    or execution.mode_tree_digest(ws, manifest["tree"]) != mode_digest):
                raise ValueError("candidate manifest differs from execution")
            if execution.candidate_manifest(
                ws, state.run_id, "candidate-" + mode_digest + ".json",
            ) != manifest:
                raise ValueError("candidate manifest differs from execution")
            current = ws.git.tree_modes(state.head)
            frozen = ws.git.tree_modes(manifest["tree"])
            entries = {path: frozen.get(path) for path in current.keys() | frozen.keys()
                       if not path.startswith(ws.spec_rel + "/")
                       and current.get(path) != frozen.get(path)}
            if request["kind"] == "run-gates" and entries:
                raise ValueError("run gates refer to a different product")

            def verify_tree(
                tree: str, digest: str = digest, frozen: dict[str, tuple[str, str]] = frozen,
            ) -> None:
                """Refuse before ref movement if admission changed the tested product."""
                admitted = ws.git.tree_modes(tree)
                same_modes = all(
                    admitted.get(path) == frozen.get(path)
                    for path in admitted.keys() | frozen.keys()
                    if not path.startswith(ws.spec_rel + "/")
                )
                if ws.git.product_tree(tree) != digest or not same_modes:
                    raise Refusal("gate-execution-mismatch", "controller",
                                  "the admission tree differs from the tested candidate")

            return {"trailers": {"Supervisor-Gate-Execution": record["execution_id"]},
                    "entries": entries, "verify_tree": verify_tree}
    except (ValueError, OSError, fs.UnsafeContentError,
            _loop._projector.ProjectionRefused) as exc:
        raise Refusal("gate-execution-mismatch", "controller", str(exc)) from exc
    code = "gate-execution-mismatch" if mismatched else "gate-execution-missing"
    raise Refusal(code, "controller", "no matching unconsumed passing gate execution")


def report_task(
    ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any], changed: list[str]
) -> str:
    """Admit a write-stub or implement-task result; refuse without writing otherwise."""
    task = next(t for t in state.tasks if t["task_id"] == request["task"]["task_id"])
    step = request["request_id"]
    if request["kind"] == "write-stub":
        stub_paths = sorted(s["path"] for s in task["stubs"])
        if sorted(changed) != stub_paths:
            raise Refusal(
                "not-exactly-stub",
                "controller",
                "a stub attempt may change exactly the stub files: " + ", ".join(changed),
            )
        _refuse_untrusted_launch(state)
        overlay = {}
        for stub in task["stubs"]:
            content = ws.git.read_working(stub["path"])
            if content != stub["content"].encode("utf-8"):
                raise Refusal(
                    "stub-bytes-differ",
                    "controller",
                    f"{stub['path']} is not byte-identical to the plan",
                )
            overlay[stub["path"]] = content
        with ws.attempts.launched(state, f"stub:{task['task_id']}:{task['stub_digest']}"):
            observed = observe(ws, task, overlay)
        if not _all_red(task, observed):
            leftovers = _supervisor("_supervisor_recovery.py").close_not_red(
                ws, state, request["request_id"], changed
            )
            raise _not_red(task, observed, leftovers, closed=True)
        evidence = ws.evidence_append([_red_receipt(ws, state, step, task)])
        _commit_result(
            ws,
            request,
            run_id=state.run_id,
            step=step,
            operation="stub",
            trailers=_trailers(task),
            paths=stub_paths,
            appends={"evidence.jsonl": evidence},
            summary=f"{task['position']} stub",
            known_steps=state.steps,
        )
        return "stub"
    gate = result.get("gate")
    if not isinstance(gate, dict) or not isinstance(gate.get("passed"), bool):
        raise Refusal("invalid-result", "controller", "an implement-task result needs gate.passed")
    validate_gate_claim(ws, state, gate)
    term = f"gate:{task['task_id']}:{task['revision']}"
    fingerprint = ws.git.product_tree()
    if gate["passed"]:
        proof = gate_proof(ws, state, request)
        evidence = ws.evidence_append([
            _loop.receipt(
                state,
                step,
                criterion=f"task:{task['task_id']}",
                term=term,
                observation="task-gate",
                outcome="pass",
                fingerprint=fingerprint,
                revision=task["revision"],
            )
        ])
        _commit_result(
            ws,
            request,
            run_id=state.run_id,
            step=step,
            operation="implement",
            trailers={**_trailers(task), **proof.get("trailers", {})},
            paths=() if proof else changed,
            **{key: value for key, value in proof.items() if key != "trailers"},
            appends={"evidence.jsonl": evidence},
            summary=f"{task['position']} {task['title']}"[:200],
            known_steps=state.steps,
        )
        return "implement"
    fail_step = f"{step}:fail"
    evidence = ws.evidence_append([
        _loop.receipt(
            state,
            fail_step,
            criterion=f"task:{task['task_id']}",
            term=term,
            observation="task-gate",
            outcome="fail",
            fingerprint=fingerprint,
            revision=task["revision"],
        )
    ])
    ws.git.build_commit(
        run_id=state.run_id,
        step=fail_step,
        operation="gate-fail",
        trailers=_trailers(task),
        appends={"evidence.jsonl": evidence},
        summary=f"{task['position']} gate failed",
        known_steps=state.steps,
    )
    return "gate-fail"
