"""_supervisor_tdd — the red-before-green guard and task attempts.

No production change for a task that declares stubs is admitted until the
supervisor has itself observed every stub, byte-identical to the plan, exit
with a code its fence declares as red. Red proof belongs to the task and its
stub digest. When the stub bytes are already in ``HEAD`` (the task was revised
after its stub commit), the supervisor runs them on a scratch copy of ``HEAD``
and commits a ``red`` step itself. A stub that already passes is refused with
``stub-not-red``; the plan author replans the task with a ``no stub``
disposition. A task with no stubs needs no red proof.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
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
    """Materialize HEAD's tree into *directory*."""
    archive = ws.git.run("archive", "--format=tar", "HEAD")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(directory, filter="data")
        else:  # pragma: no cover - Python builds without extraction filters
            tar.extractall(directory)  # noqa: S202 - the archive is this repository's own HEAD


def observe(
    ws: Any, task: dict[str, Any], overlay: dict[str, bytes]
) -> list[tuple[str, int | None]]:
    """Run each stub on a scratch copy of HEAD plus *overlay*; return its exit code."""
    timeout = float(ws.policy.get("stub_timeout_seconds", 600))
    results: list[tuple[str, int | None]] = []
    with tempfile.TemporaryDirectory(prefix="work-supervisor-red-") as scratch:
        directory = Path(scratch).resolve()
        _scratch_tree(ws, directory)
        for rel, content in overlay.items():
            target = directory / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        for stub in task["stubs"]:
            argv = [part.replace("{path}", stub["path"]) for part in shlex.split(stub["run"])]
            try:
                done = subprocess.run(
                    argv, cwd=str(directory), capture_output=True, timeout=timeout, check=False
                )
                results.append((stub["path"], done.returncode))
            except (OSError, subprocess.TimeoutExpired):
                results.append((stub["path"], None))
    return results


def _all_red(task: dict[str, Any], observed: list[tuple[str, int | None]]) -> bool:
    by_path = {s["path"]: s for s in task["stubs"]}
    return all(code is not None and code in by_path[path]["red_exit"] for path, code in observed)


def _not_red(task: dict[str, Any], observed: list[tuple[str, int | None]]) -> Any:
    detail = ", ".join(f"{p} exited {c}" for p, c in observed)
    return Refusal(
        "stub-not-red",
        "plan author",
        f"{task['position']} stubs are not red ({detail}); replan the task with a "
        "`no stub` disposition or a failing stub",
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
        observed = observe(ws, task, overlay)
        if not _all_red(task, observed):
            raise _not_red(task, observed)
        evidence = ws.evidence_append([_red_receipt(ws, state, step, task)])
        ws.git.build_commit(
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
    term = f"gate:{task['task_id']}:{task['revision']}"
    fingerprint = ws.git.product_tree()
    if gate["passed"]:
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
        ws.git.build_commit(
            run_id=state.run_id,
            step=step,
            operation="implement",
            trailers=_trailers(task),
            paths=changed,
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
