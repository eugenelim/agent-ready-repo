"""_supervisor_concurrent — admission to the concurrent path, its blocking verb, and recovery.

Under a concurrent ``concurrency`` policy, ``next`` names the first ready task in a
``run-concurrent`` request when every condition of the closed admission set holds, and
otherwise issues it on the sequential floor with one closed reason code. A batch holds
one attempt. The controller then runs the blocking verb ``run-concurrent``, which:

1. marks the request consumed in the run store, before anything is spawned;
2. makes the attempt directory, spawns the pinned launcher copy, and records its process
   group and its leader's start time before it sends a single line;
3. verifies the launcher's containment attestation, releases the worker, and reads the one
   access line the launcher sends at the end, all over the launcher's own pipes;
4. confirms the launcher's process group has ended, ingests the attempt directory itself,
   writes its own ``execution-result`` record, and integrates by exact source: the product
   ref must still name the commit the attempt was issued against.

Every other verb first settles the attempts a dead verb left: a commit carrying the
attempt's trailer means landed, and anything else has its launcher's process group ended
and confirmed, and its task issued on the floor.

A failure has task blast radius. An attempt that fails, is refused, or conflicts cancels each
running sibling whose declared sets meet its own: the launcher is sent ``abort``, its process
group is ended, and the end must be confirmed within the confirmation window before the task
is projected again onto a fresh attempt directory. An end that is not confirmed sends the
task to the floor and leaves the directory as residue. A cancelled attempt's result is never
admitted, however late it arrives. Each projection again counts toward ``reprojection_bound``,
and a replan or stub-fence revision discards every held result without counting.

The run store keeps one record per consumed request under ``consumed/``. A request is
consumed once; whatever the attempt's outcome, a task whose attempt did not land is
issued on the floor for that attempt.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import stat
import sys
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module."""
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


_commit = _supervisor("_supervisor_commit.py")
_conc = _supervisor("_supervisor_concurrency.py")
_launcher = _supervisor("_supervisor_launcher.py")
_integration = _supervisor("_supervisor_integration.py")
sibling = _commit.sibling
kill_point = _commit.kill_point
ensure_directory = _commit.ensure_directory

__all__ = [
    "CLOSED_REASONS",
    "admit",
    "recover",
    "discard_stale",
    "report_completion",
    "request_id",
    "results_pending",
    "run_concurrent",
    "status_view",
]

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 64 * 1024
OPEN_STATES = frozenset({"consumed", "running"})
# What integration closes an attempt with besides landing: the reasons of integration-conflict.v1.
CONFLICT_REASONS = frozenset({
    "meets", "content", "merge-attribute", "merge-config", "outside-changed-paths",
    "stale-authority", "cas-lost", "incomplete-attestation", "link-target",
})
# The closed set of reason codes a fall to the floor can carry, none of them launcher text.
CLOSED_REASONS = frozenset({
    # admission
    "reads-missing", "writes-missing", "invalid-path", "invalid-glob", "writes-listing",
    "protected-path", "stub-fence", "reprojection-bound", "non-posix-host", "git-version",
    "merge-config", "launcher-pin",
    # the containment attestation
    "containment-timeout", "containment-oversized", "containment-schema", "containment-missing",
    "binding-run-id", "binding-attempt-id", "binding-grant-id", "binding-nonce",
    "binding-launcher", "read-enforcement", "allowlist-mismatch", "network-allowed",
    "write-roots", "broader-than-grant", "denial-missing",
    # the launcher and the access attestation
    "launcher-changed", "launcher-closed", "launcher-spawn-failed", "access-timeout",
    "access-oversized", "access-schema", "access-binding", "access-token", "access-extra-line",
    "access-missing", "processes-not-ended",
    # a valid but incomplete attestation (exact source only)
    "access-mode", "access-read-outside", "access-bad-path", "access-too-many",
    "access-write-missing", "access-incomplete",
    # ingestion and integration
    "attempt-location", "attempt-too-large", "attempt-special-file", "attempt-hard-link",
    "attempt-bad-path", "attempt-git-name", "attempt-unsafe-link", "attempt-changed",
    "attempt-unreadable", "protected-path-changed",
    # the refusal reasons of an integration that did not land
    "meets", "content", "merge-attribute", "outside-changed-paths", "stale-authority",
    "cas-lost", "incomplete-attestation", "link-target",
    # recovery, cancellation, and plan changes
    "attempt-lost", "end-unconfirmed", "attempt-error", "sibling-failed",
    "plan-changed",
})
_SECURITY_REASONS = frozenset({
    "binding-run-id", "binding-attempt-id", "binding-grant-id", "binding-nonce",
    "binding-launcher", "launcher-changed", "access-schema", "access-oversized",
    "access-binding", "access-token", "access-extra-line",
})


def _loop() -> ModuleType:
    return _supervisor("_supervisor_loop.py")


# ── the run store's attempt records ─────────────────────────────────────────


def request_id(
    task: dict[str, Any], attempt: int, reprojections: int = 0, discards: int = 0
) -> str:
    """The deterministic id of *task*'s request for *attempt*.

    *reprojections* counts the attempts projected again toward the bound, *discards* the held
    results a plan change threw away, which never count toward it.
    """
    base = f"conc:{task['task_id']}:{task['revision']}:{attempt}"
    return base + _suffix(reprojections, discards)


def _suffix(count: int, discards: int) -> str:
    return (f":r{count}" if count else "") + (f":d{discards}" if discards else "")


def batch_request_id(parts: list[str]) -> str:
    """The id of a request naming several tasks; one task keeps its own id."""
    if len(parts) == 1:
        return parts[0]
    return "conc:" + hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:32]


def _record_name(rid: str) -> str:
    return hashlib.sha256(rid.encode("utf-8")).hexdigest()[:32] + ".json"


def _store(ws: Any, run_id: str) -> Path:
    return Path(ws.git._store_dir(run_id))


def _directory(ws: Any, run_id: str, name: str) -> Path:
    git = ws.git
    git.ensure_store(run_id)
    return Path(ensure_directory(git.hardened.pins.git_dir, f"{git._store_rel(run_id)}/{name}"))


def _read(ws: Any, run_id: str, name: str) -> dict[str, Any] | None:
    """One record of the run's ``consumed/`` directory; unreadable or malformed reads as lost."""
    store = _store(ws, run_id)
    path = store / "consumed" / name
    if not os.path.lexists(path):
        return None
    fs = sibling("_file_safety.py")
    try:
        record = json.loads(
            bytes(fs.read_confined_regular_file(store, path, max_bytes=MAX_RECORD_BYTES))
        )
    except (ValueError, OSError, fs.UnsafeContentError):
        return {"state": "lost", "reason": "attempt-lost"}
    if not isinstance(record, dict) or not isinstance(record.get("state"), str):
        return {"state": "lost", "reason": "attempt-lost"}
    return record


def read_record(ws: Any, run_id: str, rid: str) -> dict[str, Any] | None:
    """The attempt record of request *rid*, or ``None`` when it was never consumed."""
    return _read(ws, run_id, _record_name(rid))


def list_records(ws: Any, run_id: str) -> list[dict[str, Any]]:
    """Every attempt record of the run, in file-name order."""
    store = _store(ws, run_id)
    directory = store / "consumed"
    if not os.path.lexists(directory):
        return []
    fs = sibling("_file_safety.py")
    try:
        files = fs.list_confined_regular_files(store, directory, max_files=10_000)
    except (OSError, fs.UnsafeContentError):
        return []
    found = []
    for path in sorted(files):
        record = _read(ws, run_id, path.name)
        if record is not None:
            found.append({"_name": path.name, **record})
    return found


def _write(ws: Any, run_id: str, record: dict[str, Any], *, create: bool = False) -> None:
    """Write the record under its request's name; with *create*, only if none exists."""
    cm = sibling("_confined_mutation.py")
    directory = _directory(ws, run_id, "consumed")
    body = json.dumps(
        {k: v for k, v in record.items() if k != "_name"}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path = directory / _record_name(record["request_id"])
    store = _store(ws, run_id)
    if create:
        cm.confined_create(store, path, body)
    else:
        cm.confined_atomic_replace(store, path, body)


def _verb_alive(record: dict[str, Any]) -> bool:
    pid, start = record.get("verb_pid"), record.get("verb_start")
    return isinstance(pid, int) and _launcher.process_start(pid) == start


# ── admission ───────────────────────────────────────────────────────────────


def pinned_launcher(ws: Any, state: Any) -> Path | None:
    """The run's pinned launcher copy when the first approval names one and the copy holds it."""
    sha = state.approvals[0].get("launcher_sha256")
    if not isinstance(sha, str):
        return None
    return _launcher.copy_matches(_store(ws, state.run_id), sha)  # type: ignore[no-any-return]


def is_reprojection(record: dict[str, Any]) -> bool:
    """Whether *record* closed an attempt whose task was projected again: it counts to the bound.

    That is an integration conflict, or a cancellation whose end was confirmed. A dead verb's
    attempt, one whose end was not confirmed, and a discarded held result are not.
    """
    return record.get("state") == "conflict" or (
        record.get("state") == "cancelled" and bool(record.get("reproject"))
    )


def _reprojections(ws: Any, task: dict[str, Any]) -> int:
    """Reprojections this task has spent: the attempts that closed and were projected again."""
    return _spent(ws, task)[0]


def _spent(ws: Any, task: dict[str, Any]) -> tuple[int, int]:
    """``(reprojections, discards)`` of *task*'s current revision."""
    run_id = ws.approvals()[0]["run_id"]
    own = [
        r for r in list_records(ws, run_id)
        if r.get("task_id") == task["task_id"] and r.get("revision") == task["revision"]
    ]
    return (
        sum(1 for r in own if is_reprojection(r)),
        sum(1 for r in own if r.get("state") == "discarded"),
    )


def _rid(ws: Any, state: Any, task: dict[str, Any]) -> str:
    """The request id of *task*'s next attempt, after what its earlier attempts spent."""
    return request_id(task, state.attempt(task), *_spent(ws, task))


def _posix_host() -> bool:
    """Whether this host has process groups and descriptor-relative file access."""
    return os.name == "posix"


def floor_reason(ws: Any, state: Any, task: dict[str, Any]) -> str | None:
    """The first member of the admission set *task* lacks, as a closed code; ``None`` if none."""
    if not task["reads"]:
        return "reads-missing"
    if not task["writes"]:
        return "writes-missing"
    if task.get("floor_reason"):
        return str(task["floor_reason"])
    if task["stubs"]:
        return "stub-fence"
    if _reprojections(ws, task) >= int(ws.policy["reprojection_bound"]):
        return "reprojection-bound"
    if not _posix_host():
        return "non-posix-host"
    hardened = ws.git.hardened
    return (
        _conc.git_floor_reason(hardened.git_version)
        or _conc.merge_config_floor_reason(hardened.config_entries())
        or (None if pinned_launcher(ws, state) is not None else "launcher-pin")
    )


def _declared(task: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    return _conc.declared_reads(task["reads"]), _conc.declared_writes(task["writes"])


def _batch(ws: Any, state: Any, first: dict[str, Any]) -> list[dict[str, Any]]:
    """The floor-order-first admissible, non-meeting tasks led by *first*, up to the cap."""
    complete = {t["task_id"] for t in state.tasks if state.is_complete(t)}
    limit = int(ws.policy["max_concurrent_attempts"])
    ignore_case = _ignore_case(ws)
    chosen = [first]
    for task in state.tasks:
        if len(chosen) >= limit:
            break
        if task is first or state.is_complete(task):
            continue
        if not all(dep in complete for dep in task["depends_on"]):
            continue
        rid = _rid(ws, state, task)
        if read_record(ws, state.run_id, rid) is not None or floor_reason(ws, state, task):
            continue
        reads, writes = _declared(task)
        if any(
            _conc.tasks_meet(reads, writes, *_declared(other), ignore_case=ignore_case)
            for other in chosen
        ):
            continue
        chosen.append(task)
    return chosen


def admit(ws: Any, state: Any, task: dict[str, Any]) -> tuple[Any, str | None]:
    """``(action, None)`` to run a batch led by *task*, or ``(None, reason)`` for the floor.

    A request whose attempts are still running (its verb alive) is issued again unchanged, so
    no floor request issues while an attempt is open. An attempt that did not land sends its
    task to the floor for that attempt with its own reason, except a refused integration,
    which projects the task again under a new request until the reprojection bound is spent.
    A held result whose task is next waits for a clean working tree.
    """
    held = ws.attempts.open
    if (
        held is not None
        and held.kind == "implement-task"
        and held.request_id.startswith(f"impl:{task['task_id']}:{task['revision']}:")
    ):
        # A floor attempt is open: nothing opens beside it, and the reason it went to the floor
        # is the one the journal and status keep reporting.
        return None, floor_reason(ws, state, task)
    live = [
        r for r in list_records(ws, state.run_id)
        if r["state"] in OPEN_STATES and _verb_alive(r)
    ]
    if live:
        return _reissue(ws, state, live[0]), None
    rid = _rid(ws, state, task)
    record = read_record(ws, state.run_id, rid)
    if record is not None:
        if record["state"] == "held":
            refusal = _loop().Refusal(
                "uncommitted-changes", "controller",
                "a held result for this task waits for a clean working tree; commit or "
                "restore the working tree changes, then run next",
            )
            return _loop().Action("refusal", refusal=refusal), None
        return None, str(record.get("reason") or "attempt-lost")
    reason = floor_reason(ws, state, task)
    if reason is not None:
        return None, reason
    return _request(ws, state, _batch(ws, state, task)), None


def _request(ws: Any, state: Any, tasks: list[dict[str, Any]]) -> Any:
    loop = _loop()
    lead = tasks[0]
    rids = [_rid(ws, state, t) for t in tasks]
    return loop.Action(
        "request",
        loop.make_request(
            ws, state, "run-concurrent", batch_request_id(rids),
            task=loop._task_ref(lead), tasks=[t["task_id"] for t in tasks],
            attempt=state.attempt(lead),
        ),
    )


def _reissue(ws: Any, state: Any, record: dict[str, Any]) -> Any:
    """The request an open attempt's verb is running, built again from the record."""
    ids = record.get("batch_tasks") or [record["task_id"]]
    tasks = [next(t for t in state.tasks if t["task_id"] == i) for i in ids]
    loop = _loop()
    return loop.Action(
        "request",
        loop.make_request(
            ws, state, "run-concurrent", record.get("batch") or record["request_id"],
            task=loop._task_ref(tasks[0]), tasks=list(ids),
            attempt=record.get("batch_attempt") or record["attempt"],
        ),
    )


def status_view(ws: Any, state: Any, action: Any) -> dict[str, Any] | None:
    """What ``status`` adds under a concurrent policy: the mode, the floor reason, the attempts."""
    records = list_records(ws, state.run_id)
    if ws.policy["concurrency"] == "sequential" and not records:
        return None
    return {
        "mode": ws.policy["concurrency"],
        "floor_reason": action.detail.get("floor_reason") if action is not None else None,
        "attempts": [
            {
                "task_id": r.get("task_id"),
                "request_id": r.get("request_id"),
                "state": r.get("state"),
                "reason": r.get("reason"),
                "reprojected": is_reprojection(r),
            }
            for r in records
        ],
    }


# ── events and journal ──────────────────────────────────────────────────────


def _event(ws: Any, code: str) -> None:
    """One ``security-event.v1`` naming a defect code, and nothing the launcher sent."""
    if code in _SECURITY_REASONS:
        ws.attempts.log_denial(code, "supervisor-launcher-attestation")


def _journal(ws: Any, state: Any, record: dict[str, Any], outcome: str) -> None:
    _journal_outcome(ws, state.run_id, record, outcome)


def _journal_outcome(ws: Any, run_id: str, record: dict[str, Any], outcome: str) -> None:
    ws.local.append_journal({
        "run_id": run_id,
        "at": ws.clock(),
        "head": ws.git.head(),
        "stage": "implementing",
        "kind": "run-concurrent",
        "request_id": record["request_id"],
        "outcome": outcome,
        "reason": record.get("reason"),
        **({"reprojected": True} if is_reprojection(record) else {}),
    })


# ── the verb ────────────────────────────────────────────────────────────────


def run_concurrent(ws: Any, rid: str) -> dict[str, Any]:
    """Run the consumed request *rid* to its end; the blocking ``run-concurrent`` verb.

    Each task the request names gets its own record, attempt directory, launcher, binding,
    and settlement; the attempts run at the same time and each settles, under the run lock,
    as it finishes.
    """
    loop = _loop()
    refusal = loop.Refusal
    with ws.run_lock():
        ws.attempts.guard("run-concurrent")
        recover(ws)
        recovery = _supervisor("_supervisor_recovery.py")
        if recovery.reconcile(ws) is not None:
            raise recovery.unadopted(ws)
        state = loop.derive(ws)
        if state.refusal is not None:
            raise state.refusal
        if any(r.get("batch") == rid or r.get("request_id") == rid
               for r in list_records(ws, state.run_id)):
            raise refusal("request-consumed", "controller", "this request was already run")
        foreign = ws.git.sync(state.commits[-1].sha if state.commits else None)
        if foreign:
            raise refusal("foreign-delivery-edit", "controller", ", ".join(foreign))
        action = loop.decide(ws, state)
        current = action.request if action.kind == "request" else None
        if current is None or current["request_id"] != rid or current["kind"] != "run-concurrent":
            raise refusal("not-current-attempt", "controller", "the request is not current")
        ws.attempts.require_open_issuance(current)
        source = ws.attempts.source_commit(rid)
        if source is None or source != state.head:
            raise refusal("not-current-attempt", "controller", "a step landed since it was issued")
        dirty = ws.git.change_set()
        if dirty:
            raise refusal(
                "uncommitted-changes", "controller",
                "the working tree holds changes no task admitted: " + ", ".join(dirty[:20]),
            )
        tasks = [next(t for t in state.tasks if t["task_id"] == i) for i in current["tasks"]]
        ws.git.hardened.config_entries()  # read once here, before attempts run side by side
        for name in ("consumed", "results", "held", "integrations", "conflicts"):
            _directory(ws, state.run_id, name)
        cm = sibling("_confined_mutation.py")
        records = []
        for task in tasks:
            count, discards = _spent(ws, task)
            attempt = state.attempt(task)
            record: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "run_id": state.run_id,
                "request_id": request_id(task, attempt, count, discards),
                "batch": rid,
                "batch_tasks": list(current["tasks"]),
                "batch_attempt": current["attempt"],
                "task_id": task["task_id"],
                "revision": task["revision"],
                "attempt": attempt,
                "step": f"impl:{task['task_id']}:{task['revision']}:{attempt}"
                + _suffix(count, discards),
                "state": "consumed",
                "source": source,
                "verb_pid": os.getpid(),
                "verb_start": _launcher.process_start(os.getpid()),
            }
            try:
                _write(ws, state.run_id, record, create=True)
            except cm.MutationDenied as exc:
                if exc.denial_code != "denied-already-exists":
                    raise
                raise refusal(
                    "request-consumed", "controller", "this request was already run"
                ) from exc
            records.append(record)
        kill_point("request-consumed")
        store = _store(ws, state.run_id)
        sha = state.approvals[0]["launcher_sha256"]
        jobs: list[tuple[dict[str, Any], dict[str, Any], Path]] = []
        summaries: list[dict[str, Any]] = []
        for task, record in zip(tasks, records, strict=True):
            try:
                attempt_dir = _conc.create_attempt_directory(
                    ws.git.hardened, source, forbidden=[store]
                )
            except _conc.AttemptRefused as exc:
                summaries.append(_fall(ws, state, record, exc.code))
                continue
            record["attempt_dir"] = str(attempt_dir)
            record["attempt_id"] = "att-" + secrets.token_hex(8)
            _write(ws, state.run_id, record)
            jobs.append((task, record, attempt_dir))
    summaries += _run_attempts(ws, state, jobs, sha)
    if len(summaries) == 1:
        return {"run_concurrent": summaries[0]}
    return {"run_concurrent": {"outcome": "batch", "attempts": summaries}}


class _Control:
    """One running attempt's cancellation flag; set by a sibling's failure under the gate."""

    def __init__(self, task: dict[str, Any]) -> None:
        self.task = task
        self.cancelled = False
        self.done = False


def _meeting_siblings(
    ws: Any, failed: dict[str, Any], controls: list[_Control]
) -> list[_Control]:
    """The running attempts whose declared sets meet *failed*'s, never *failed* itself."""
    reads, writes = _declared(failed)
    ignore_case = _ignore_case(ws)
    return [
        c for c in controls
        if not c.done and c.task["task_id"] != failed["task_id"]
        and _conc.tasks_meet(reads, writes, *_declared(c.task), ignore_case=ignore_case)
    ]


def _run_attempts(
    ws: Any, state: Any, jobs: list[tuple[dict[str, Any], dict[str, Any], Path]], sha: str
) -> list[dict[str, Any]]:
    """Run each attempt (side by side when there are several) and settle each as it finishes.

    A failed, refused, or conflicting attempt cancels each running sibling whose declared sets
    meet its own; every other sibling settles as it would have.
    """
    results: dict[int, tuple[str, Any]] = {}
    gate = threading.Lock()
    dead = threading.Event()
    controls = [_Control(task) for task, _record, _dir in jobs]

    def failed(task_id: str) -> None:
        """Cancel the running siblings of *task_id*'s attempt; runs under *gate*."""
        task = next((t for t in state.tasks if t["task_id"] == task_id), None)
        if task is None:
            return
        for control in _meeting_siblings(ws, task, controls):
            control.cancelled = True
            kill_point("sibling-cancelled")

    def work(index: int) -> None:
        task, record, attempt_dir = jobs[index]
        control = controls[index]
        try:
            outcome = _drive(ws, state, task, record, sha, attempt_dir, control)
            with gate:
                if dead.is_set():
                    results[index] = ("dead", None)
                    return
                if control.cancelled and not isinstance(outcome, _Defect):
                    # A result that finished after its cancellation is never admitted.
                    outcome = _Defect("sibling-failed", "cancelled")
                results[index] = (
                    "ok", _settle(ws, state, task, record, attempt_dir, outcome, failed)
                )
                control.done = True
        except BaseException as exc:  # noqa: BLE001 - re-raised in the verb's own thread
            if not isinstance(exc, Exception):
                dead.set()
            results[index] = ("error", exc)

    if len(jobs) == 1:
        work(0)
    else:
        threads = [
            threading.Thread(target=work, args=(i,), name=f"attempt-{jobs[i][0]['task_id']}")
            for i in range(len(jobs))
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    errors = [r[1] for _i, r in sorted(results.items()) if r[0] == "error"]
    for error in errors:
        if not isinstance(error, Exception):
            raise error
    if errors:
        raise errors[0]
    return [_final(ws, state, r[1]) for _i, r in sorted(results.items()) if r[0] == "ok"]


def _final(ws: Any, state: Any, summary: dict[str, Any]) -> dict[str, Any]:
    """*summary* as the attempt ended: a result held when it settled may have landed since."""
    rid = summary.pop("request_id", None)
    if summary.get("outcome") != "held" or rid is None:
        return summary
    record = read_record(ws, state.run_id, rid)
    if record is None or record["state"] == "held":
        return summary
    final: dict[str, Any] = {"outcome": record["state"], "task": summary["task"]}
    if record["state"] == "landed":
        final["commit"] = record.get("commit")
    elif record.get("reason"):
        final["reason"] = record["reason"]
    return final


def _fall(
    ws: Any, state: Any, record: dict[str, Any], reason: str, *, state_name: str = "floor",
    attempt_dir: Path | None = None,
) -> dict[str, Any]:
    """Close the attempt with *reason*; the dir goes unless residue.

    A cancellation whose end was confirmed is marked for projection again; any other close
    leaves the task on the floor for the attempt.
    """
    record.update(state=state_name, reason=reason)
    if state_name == "cancelled":
        record["reproject"] = True
    _write(ws, state.run_id, record)
    if attempt_dir is not None and state_name != "residue":
        _conc.remove_attempt_directory(attempt_dir)
    _event(ws, reason)
    _journal(ws, state, record, state_name)
    return {"outcome": state_name, "reason": reason, "task": record["task_id"]}


class _Defect(Exception):
    """An attempt that ends before integration; *reason* is a closed code."""

    def __init__(self, reason: str, state: str = "floor") -> None:
        super().__init__(reason)
        self.reason = reason
        self.state = state


class _Result:
    """What a finished attempt hands to integration."""

    def __init__(self) -> None:
        self.tree = ""
        self.access_sha = ""
        self.access_defect: str | None = None
        self.entries: dict[str, tuple[str, str] | None] = {}
        self.attested_reads: list[dict[str, str]] = []
        self.attested_writes: list[dict[str, str]] = []


def _drive(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], sha: str,
    attempt_dir: Path, control: _Control,
) -> _Result | _Defect:
    """Spawn, verify, release, wait, and ingest. Returns the result or the defect that ended it."""
    scratch = Path(tempfile.mkdtemp(prefix="agentbundle-launcher-"))
    try:
        return _session(ws, state, task, record, sha, attempt_dir, scratch, control)
    except _Defect as defect:
        return defect
    except Exception:
        record.update(state="floor", reason="attempt-error")
        _write(ws, state.run_id, record)
        raise
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _stop(record: dict[str, Any], proc: Any) -> bool:
    """End the launcher's group; ``True`` when its end is confirmed."""
    try:
        if proc.stdin is not None:
            proc.stdin.close()
    except OSError:
        pass
    confirmed: bool = _launcher.end_group(
        int(record["pgid"]), int(record["leader_pid"]), str(record["leader_start"]), proc
    )
    if confirmed:
        proc.wait()
    return confirmed


def _session(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], sha: str,
    attempt_dir: Path, scratch: Path, control: _Control,
) -> _Result:
    """One attempt's conversation with its launcher; raises ``_Defect`` for any refusal."""
    L = _launcher  # noqa: N806 - the module this session speaks through
    store = _store(ws, state.run_id)
    if L.copy_matches(store, sha) is None:
        raise _Defect("launcher-changed")
    copy = L.copy_matches(store, sha)
    assert copy is not None
    mode = ws.policy["concurrency"]
    binding = L.Binding(
        state.run_id, record["attempt_id"], "grant-" + secrets.token_hex(8),
        secrets.token_hex(32), sha,
    )
    grant = L.Grant(
        binding.grant_id, (str(attempt_dir),),
        "allowlist" if mode == "enforced-allowlist" else "trace",
    )
    proc = L.spawn(copy, scratch)
    try:
        kill_point("launcher-spawned")
        started = L.CLOCK.now()
        pid = proc.pid
        leader_start = L.process_start(pid)
        if leader_start is None:
            raise _Defect("launcher-spawn-failed")
        record.update(
            state="running", pgid=os.getpgid(pid), leader_pid=pid, leader_start=leader_start
        )
        _write(ws, state.run_id, record)  # durable before any line is sent
        kill_point("launcher-recorded")
        reader = L.LineReader(proc.stdout.fileno(), lambda: control.cancelled)
        L.send(proc, {
            "schema_version": 1,
            "type": "attempt",
            "binding": binding.as_dict(),
            "grant": grant.as_dict(),
            "attempt_dir": str(attempt_dir),
            "request": _loop().make_request(
                ws, state, "run-concurrent", record["request_id"],
                task=_loop()._task_ref(task), tasks=[task["task_id"]], attempt=record["attempt"],
            ),
        })
        try:
            line = reader.read_line(started + L.CONTAINMENT_TIMEOUT_S)
        except L.ReadTimeout:
            raise _Defect("containment-timeout") from None
        except L.LineTooLong:
            raise _Defect("containment-oversized") from None
        except L.StreamClosed:
            raise _Defect("containment-missing") from None
        except L.ReadCancelled:
            raise _Defect("sibling-failed", "cancelled") from None
        defect, attestation = L.verify_containment(
            line, binding=binding, mode=mode, declared_reads=list(task["reads"]),
            attempt_dir=str(attempt_dir), grant=grant,
        )
        if defect is not None or attestation is None:
            raise _Defect(defect or "containment-schema")
        if L.copy_matches(store, sha) is None:
            raise _Defect("launcher-changed")
        token = secrets.token_hex(32)
        if not L.send(proc, {
            "schema_version": 1, "type": "release",
            "binding": binding.as_dict(), "release_token": token,
        }):
            raise _Defect("launcher-closed")
        kill_point("released")
        deadline = L.CLOCK.now() + float(ws.policy["attempt_timeout_seconds"])
        try:
            access_line = reader.read_line(deadline)
        except L.ReadTimeout:
            raise _Defect("access-timeout", "cancelled") from None
        except L.LineTooLong:
            raise _Defect("access-oversized") from None
        except L.StreamClosed:
            raise _Defect("access-missing") from None
        except L.ReadCancelled:
            raise _Defect("sibling-failed", "cancelled") from None
        kill_point("access-read")
        extra, ended = reader.rest(L.CLOCK.now() + L.CONFIRM_TIMEOUT_S)
        if extra:
            raise _Defect("access-extra-line")
        if not ended:
            raise _Defect("processes-not-ended")
        defect, access = L.verify_access(access_line, binding=binding, token=token)
        if defect is not None or access is None:
            raise _Defect(defect or "access-schema")
        if not access["processes_ended"] or not _wait_exit(proc):
            raise _Defect("processes-not-ended")
        if L.group_alive(int(record["pgid"])):
            raise _Defect("processes-not-ended")
        result = _ingest(ws, state, task, record, attempt_dir, attestation, access)
        result.access_sha = hashlib.sha256(access_line).hexdigest()
        return result
    except _Defect as defect:
        L.send(proc, {
            "schema_version": 1, "type": "abort",
            "binding": binding.as_dict(), "reason": defect.reason,
        })
        recorded = "pgid" in record
        confirmed = _stop(record, proc) if recorded else _kill_unrecorded(proc)
        if not confirmed:
            defect.state = "residue"
        raise
    except Exception:
        if "pgid" in record:
            _stop(record, proc)
        raise


def _kill_unrecorded(proc: Any) -> bool:
    """End a launcher whose group was never recorded."""
    try:
        proc.kill()
        proc.wait(timeout=_launcher.CONFIRM_TIMEOUT_S)
    except Exception:  # noqa: BLE001 - nothing more can be done for a process that will not die
        return False
    return True


def _wait_exit(proc: Any) -> bool:
    """Wait, on the injected clock, for the launcher to exit within the confirmation window."""
    L = _launcher  # noqa: N806
    deadline = L.CLOCK.now() + L.CONFIRM_TIMEOUT_S
    while proc.poll() is None:
        if L.CLOCK.now() >= deadline:
            return False
        L.CLOCK.sleep(L.POLL_S)
    return True


def _ignore_case(ws: Any) -> bool:
    return any(
        e.key.lower() == "core.ignorecase" and e.value.lower() == "true"
        for e in ws.git.hardened.config_entries()
    )


def _changed(ws: Any, source: str, tree: str) -> dict[str, tuple[str, str] | None]:
    """Each path differing from *source*'s tree: ``(mode, id)``, or ``None`` when removed."""
    out = ws.git.hardened.run("diff-tree", "-r", "-z", "--no-renames", source, tree)
    parts = out.split(b"\0")
    found: dict[str, tuple[str, str] | None] = {}
    index = 0
    while index + 1 < len(parts):
        meta = parts[index]
        if not meta.startswith(b":"):
            break
        fields = meta[1:].decode("ascii", "replace").split()
        path = parts[index + 1].decode("utf-8", "surrogateescape")
        found[path] = None if fields[4].startswith("D") else (fields[1], fields[3])
        index += 2
    return found


def _ingest(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], attempt_dir: Path,
    containment: dict[str, Any], access: dict[str, Any],
) -> _Result:
    """Ingest the attempt directory after its launcher ended; check the access attestation."""
    L = _launcher  # noqa: N806
    delivery = ws.git.delivery_rel
    excluded = (f"{ws.spec_rel}/.supervisor/", ".loop-run/", f"{delivery}/")
    ignore_case = _ignore_case(ws)
    try:
        ingested = _conc.ingest_attempt_directory(
            ws.git.hardened, attempt_dir, source=record["source"],
            trusted_paths=ws.attempts.trusted_paths(state),
            protected_prefixes=(delivery, "delivery"), excluded_prefixes=excluded,
            product_root=str(ws.root), ignore_case=ignore_case,
        )
    except _conc.AttemptRefused as exc:
        raise _Defect(exc.code) from exc
    changed = _changed(ws, record["source"], ingested.tree)
    protected = [
        p for p in changed
        if p.startswith(ws.spec_rel + "/") or p in set(state.cited_paths)
    ]
    if protected:
        raise _Defect("protected-path-changed")
    result = _Result()
    result.tree = ingested.tree
    result.entries = changed
    result.attested_reads = L.attested_reads(access)
    result.attested_writes = list(access["writes"])
    result.access_defect = L.access_defect(
        access, read_enforcement=str(containment["read_enforcement"]),
        declared_reads=list(task["reads"]), changed_paths=changed, ignore_case=ignore_case,
    )
    return result


def _settle(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], attempt_dir: Path,
    outcome: _Result | _Defect, failed: Callable[[str], None],
) -> dict[str, Any]:
    """Settle one finished attempt: a defect falls to the floor; a result is held, then integrated.

    The caller holds the verb's finishing gate, so one attempt settles at a time. The
    result is recorded by its identity first; whatever is next in floor order then lands.
    *failed* is told each task whose attempt did not land, so its running siblings can be
    cancelled; a task cancelled for a sibling's failure tells nothing.
    """
    loop = _loop()
    if isinstance(outcome, _Defect):
        with ws.run_lock():
            summary = _fall(
                ws, state, record, outcome.reason, state_name=outcome.state,
                attempt_dir=attempt_dir,
            )
        if outcome.reason != "sibling-failed":
            failed(task["task_id"])
        return summary
    held = False
    try:
        with ws.run_lock():
            ws.attempts.guard("run-concurrent")
            current = loop.derive(ws)
            if current.refusal is not None:
                raise current.refusal
            execution_result = {
                "schema_version": 1,
                "request_id": record["request_id"],
                "run_id": state.run_id,
                "kind": "implement-task",
                "gate": {"passed": True},
                "result_tree": outcome.tree,
                "access_attestation_sha256": outcome.access_sha,
            }
            cm = sibling("_confined_mutation.py")
            cm.confined_atomic_replace(
                _store(ws, state.run_id),
                _directory(ws, state.run_id, "results") / _record_name(record["request_id"]),
                json.dumps(execution_result, sort_keys=True).encode("utf-8"),
            )
            record.update(result_tree=outcome.tree, access_attestation_sha256=outcome.access_sha)
            _integration.hold(ws, state.run_id, record, outcome, record["step"])
            held = True
            record.update(state="held")
            _write(ws, state.run_id, record)
            kill_point("result-held")
            outcomes = _integration.integrate_ready(ws)
            for each in outcomes:
                if each.get("outcome") == "conflict":
                    failed(each["task"])
    except Exception:
        if not held:
            with ws.run_lock():
                _fall(ws, state, record, "attempt-error", attempt_dir=attempt_dir)
        raise
    final = read_record(ws, state.run_id, record["request_id"]) or record
    summary: dict[str, Any] = {
        "outcome": final["state"], "task": task["task_id"], "request_id": record["request_id"],
    }
    if final["state"] == "landed":
        summary.update(
            commit=final.get("commit"), exact_source_only=outcome.access_defect is not None,
            access_defect=outcome.access_defect,
        )
    elif final.get("reason"):
        summary["reason"] = final["reason"]
    return summary


# ── plan changes ────────────────────────────────────────────────────────────


def discard_stale(ws: Any, run_id: str) -> list[str]:
    """Discard every held result a replan was committed after; returns the tasks reprojected.

    A controller replan or stub-fence revision is admitted only while no attempt is open
    (``attempt-residue`` refuses an edit beside one), so what remains to settle is the held
    results. Each one's record and ref are removed and its attempt closes as ``discarded``;
    its task is projected again under a new request that does not count toward the bound.
    The check reads the commits, so a kill between the replan and the discard converges on
    the next verb.
    """
    helds = _integration.list_held(ws, run_id)
    if not helds:
        return []
    replans = {c.sha for c in ws.git.supervisor_commits(run_id) if c.operation == "replan"}
    if not replans:
        return []
    tip = ws.git.fresh_head()
    discarded = []
    for each in helds:
        chain = set(
            ws.git.text("rev-list", "--first-parent", f"{each['source']}..{tip}", "--").split()
        )
        if not chain & replans:
            continue
        _integration.drop_held(ws, run_id, each["attempt_id"])
        record = read_record(ws, run_id, each["request_id"])
        if record is not None:
            record.update(state="discarded", reason="plan-changed")
            _write(ws, run_id, record)
            if record.get("attempt_dir"):
                _conc.remove_attempt_directory(Path(record["attempt_dir"]))
            _journal_outcome(ws, run_id, record, "discarded")
        discarded.append(each["task_id"])
    return discarded


def results_pending(ws: Any, state: Any) -> bool:
    """Whether an attempt is open or a result is held: nothing is gated or reviewed beside one."""
    return bool(_integration.list_held(ws, state.run_id)) or any(
        r["state"] in OPEN_STATES and _verb_alive(r) for r in list_records(ws, state.run_id)
    )


# ── recovery ────────────────────────────────────────────────────────────────


def repair_unrecorded(ws: Any) -> None:
    """Record a landed commit of a held result whose refs moved but whose record write died."""
    try:
        approvals = ws.approvals()
    except _loop().Refusal:
        return
    if not approvals:
        return
    run_id = approvals[0]["run_id"]
    helds = _integration.list_held(ws, run_id)
    if not helds:
        return
    tip = ws.git.fresh_head()
    for each in helds:
        landed = _integration.find_landed(ws, run_id, each, tip)
        if landed is not None:
            _integration.recover_landed(ws, run_id, landed)


def recover(ws: Any) -> None:
    """Settle every attempt a dead ``run-concurrent`` recorded; runs first in every verb.

    A commit carrying the attempt's trailer means landed: the run store records the landing
    and the working tree is brought to it. A held-result record means held: the result waits
    for its turn and is no longer an open attempt. Anything else has the launcher's group
    ended and its end confirmed within the window, closes as cancelled, and its task goes to
    the floor; an end that cannot be confirmed leaves the attempt directory as residue.
    """
    try:
        approvals = ws.approvals()
    except _loop().Refusal:
        return  # the verb's own derivation names a malformed record
    if not approvals:
        return
    run_id = approvals[0]["run_id"]
    discard_stale(ws, run_id)
    helds = _integration.list_held(ws, run_id)
    pending = [
        r for r in list_records(ws, run_id) if r["state"] in OPEN_STATES and not _verb_alive(r)
    ]
    if not pending and not helds:
        return
    tip = ws.git.fresh_head()
    held_by = {h["attempt_id"]: h for h in helds}
    for each in helds:
        landed = _integration.find_landed(ws, run_id, each, tip)
        if landed is not None:
            _integration.recover_landed(ws, run_id, landed)
            _integration.finalize_landing(ws, each, landed)
    for record in pending:
        record = read_record(ws, run_id, record["request_id"]) or record
        if record["state"] not in OPEN_STATES:
            continue
        attempt_id = record.get("attempt_id")
        if attempt_id in held_by:
            record.update(state="held")
        else:
            commits = ws.git.supervisor_commits(run_id)
            by_attempt = (c for c in commits if c.trailers.get("Supervisor-Attempt") == attempt_id)
            landed_commit = next(by_attempt, None) if attempt_id else None
            if landed_commit is not None:
                _integration.materialize(ws, landed_commit.sha)
                record.update(state="landed", commit=landed_commit.sha)
            else:
                confirmed = True
                if isinstance(record.get("pgid"), int):
                    confirmed = _launcher.end_group(
                        record["pgid"], int(record["leader_pid"]), str(record["leader_start"])
                    )
                record.update(
                    state="cancelled" if confirmed else "residue",
                    reason="attempt-lost" if confirmed else "end-unconfirmed",
                )
                if confirmed and record.get("attempt_dir"):
                    _conc.remove_attempt_directory(Path(record["attempt_dir"]))
        _write(ws, run_id, record)
        _journal_outcome(ws, run_id, record, record["state"])


# ── report ──────────────────────────────────────────────────────────────────


def report_completion(ws: Any, state: Any, result: dict[str, Any]) -> str:
    """Admit a ``run-concurrent`` completion once its verb ended with a result landed or held."""
    rid = result["request_id"]
    records = [
        r for r in list_records(ws, state.run_id)
        if r.get("batch") == rid or r.get("request_id") == rid
    ]
    ended = records and not any(r["state"] in OPEN_STATES for r in records)
    if not ended or not any(r["state"] in ("landed", "held") for r in records):
        raise _loop().Refusal(
            "not-current-attempt", "controller", "the request's attempt has not landed"
        )
    return "run-concurrent"
