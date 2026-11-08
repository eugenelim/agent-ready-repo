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
sibling = _commit.sibling
kill_point = _commit.kill_point
ensure_directory = _commit.ensure_directory

__all__ = [
    "CLOSED_REASONS",
    "admit",
    "recover",
    "report_completion",
    "request_id",
    "run_concurrent",
    "status_view",
]

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 64 * 1024
OPEN_STATES = frozenset({"consumed", "running"})
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
    "attempt-unreadable", "protected-path-changed", "integration-conflict", "working-tree-dirty",
    # recovery
    "attempt-lost", "end-unconfirmed", "attempt-error", "floor-attempt-open",
})
_SECURITY_REASONS = frozenset({
    "binding-run-id", "binding-attempt-id", "binding-grant-id", "binding-nonce",
    "binding-launcher", "launcher-changed", "access-schema", "access-oversized",
    "access-binding", "access-token", "access-extra-line",
})


def _loop() -> ModuleType:
    return _supervisor("_supervisor_loop.py")


# ── the run store's attempt records ─────────────────────────────────────────


def request_id(task: dict[str, Any], attempt: int) -> str:
    """The deterministic id of the ``run-concurrent`` request for *task*'s *attempt*."""
    return f"conc:{task['task_id']}:{task['revision']}:{attempt}"


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


def _reprojections(ws: Any, task: dict[str, Any]) -> int:
    """Reprojections this task has spent. Nothing reprojects yet: a batch of one lands or falls."""
    return 0


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


def admit(ws: Any, state: Any, task: dict[str, Any]) -> tuple[Any, str | None]:
    """``(action, None)`` to run *task* concurrently, or ``(None, reason)`` to put it on the floor.

    A request whose attempt is still running (its verb alive) is issued again unchanged, so
    no floor request issues while an attempt is open. A request consumed whose attempt did
    not land sends its task to the floor for that attempt, with the attempt's own reason.
    """
    attempt = state.attempt(task)
    rid = request_id(task, attempt)
    held = ws.attempts.open
    if (
        held is not None
        and held.kind == "implement-task"
        and held.request_id.startswith(f"impl:{task['task_id']}:{task['revision']}:")
    ):
        return None, "floor-attempt-open"  # a floor attempt is open: nothing opens beside it
    record = read_record(ws, state.run_id, rid)
    if record is not None:
        if record["state"] in OPEN_STATES and _verb_alive(record):
            return _request(ws, state, task, attempt, rid), None
        return None, str(record.get("reason") or "attempt-lost")
    reason = floor_reason(ws, state, task)
    if reason is not None:
        return None, reason
    return _request(ws, state, task, attempt, rid), None


def _request(ws: Any, state: Any, task: dict[str, Any], attempt: int, rid: str) -> Any:
    loop = _loop()
    return loop.Action(
        "request",
        loop.make_request(
            ws,
            state,
            "run-concurrent",
            rid,
            task=loop._task_ref(task),
            tasks=[task["task_id"]],
            attempt=attempt,
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
    ws.local.append_journal({
        "run_id": state.run_id,
        "at": ws.clock(),
        "head": ws.git.head(),
        "stage": "implementing",
        "kind": "run-concurrent",
        "request_id": record["request_id"],
        "outcome": outcome,
        "reason": record.get("reason"),
    })


# ── the verb ────────────────────────────────────────────────────────────────


def run_concurrent(ws: Any, rid: str) -> dict[str, Any]:
    """Run the consumed request *rid* to its end; the blocking ``run-concurrent`` verb."""
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
        if read_record(ws, state.run_id, rid) is not None:
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
        task = next(t for t in state.tasks if t["task_id"] == current["tasks"][0])
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": state.run_id,
            "request_id": rid,
            "task_id": task["task_id"],
            "revision": task["revision"],
            "attempt": current["attempt"],
            "state": "consumed",
            "source": source,
            "verb_pid": os.getpid(),
            "verb_start": _launcher.process_start(os.getpid()),
        }
        cm = sibling("_confined_mutation.py")
        try:
            _write(ws, state.run_id, record, create=True)
        except cm.MutationDenied as exc:
            if exc.denial_code != "denied-already-exists":
                raise
            raise refusal(
                "request-consumed", "controller", "this request was already run"
            ) from exc
        kill_point("request-consumed")
        store = _store(ws, state.run_id)
        sha = state.approvals[0]["launcher_sha256"]
        try:
            attempt_dir = _conc.create_attempt_directory(
                ws.git.hardened, source, forbidden=[store]
            )
        except _conc.AttemptRefused as exc:
            return _fall(ws, state, record, exc.code)
        record["attempt_dir"] = str(attempt_dir)
        record["attempt_id"] = "att-" + secrets.token_hex(8)
        _write(ws, state.run_id, record)
    outcome = _drive(ws, state, task, record, sha, attempt_dir)
    return _finish(ws, state, task, record, attempt_dir, outcome)


def _fall(
    ws: Any, state: Any, record: dict[str, Any], reason: str, *, state_name: str = "floor",
    attempt_dir: Path | None = None,
) -> dict[str, Any]:
    """Close the attempt as a fall to the floor with *reason*; the dir goes unless residue."""
    record.update(state=state_name, reason=reason)
    _write(ws, state.run_id, record)
    if attempt_dir is not None and state_name != "residue":
        _conc.remove_attempt_directory(attempt_dir)
    _event(ws, reason)
    _journal(ws, state, record, state_name)
    return {"run_concurrent": {"outcome": state_name, "reason": reason, "task": record["task_id"]}}


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


def _drive(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], sha: str, attempt_dir: Path
) -> _Result | _Defect:
    """Spawn, verify, release, wait, and ingest. Returns the result or the defect that ended it."""
    scratch = Path(tempfile.mkdtemp(prefix="agentbundle-launcher-"))
    try:
        return _session(ws, state, task, record, sha, attempt_dir, scratch)
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
    attempt_dir: Path, scratch: Path,
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
        reader = L.LineReader(proc.stdout.fileno())
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
    result.access_defect = L.access_defect(
        access, read_enforcement=str(containment["read_enforcement"]),
        declared_reads=list(task["reads"]), changed_paths=changed, ignore_case=ignore_case,
    )
    return result


def _finish(
    ws: Any, state: Any, task: dict[str, Any], record: dict[str, Any], attempt_dir: Path,
    outcome: _Result | _Defect,
) -> dict[str, Any]:
    """Settle the attempt: a defect falls to the floor; a result integrates by exact source."""
    loop = _loop()
    if isinstance(outcome, _Defect):
        with ws.run_lock():
            return _fall(
                ws, state, record, outcome.reason, state_name=outcome.state,
                attempt_dir=attempt_dir,
            )
    try:
        with ws.run_lock():
            ws.attempts.guard("run-concurrent")
            sha = _integrate(ws, loop, task, record, outcome)
    except Exception as exc:
        code = getattr(exc, "code", "")
        reason = {"integration-conflict": "integration-conflict"}.get(code) or (
            "working-tree-dirty" if code == "uncommitted-changes" else "attempt-error"
        )
        with ws.run_lock():
            _fall(ws, state, record, reason, attempt_dir=attempt_dir)
        raise
    _conc.remove_attempt_directory(attempt_dir)
    return {
        "run_concurrent": {
            "outcome": "landed", "task": task["task_id"], "commit": sha,
            "exact_source_only": outcome.access_defect is not None,
            "access_defect": outcome.access_defect,
        }
    }


def _integrate(
    ws: Any, loop: Any, task: dict[str, Any], record: dict[str, Any], result: _Result
) -> str:
    """Commit the result by exact source and bring the working tree to it."""
    tdd = _supervisor("_supervisor_tdd.py")
    state = loop.derive(ws)
    if state.refusal is not None:
        raise state.refusal
    refusal = loop.Refusal
    source = record["source"]
    current = next(
        (t for t in state.tasks
         if t["task_id"] == task["task_id"] and t["revision"] == task["revision"]),
        None,
    )
    if current is None or state.head != source:
        raise refusal("integration-conflict", "controller", "the product moved during the attempt")
    dirty = ws.git.change_set()
    if dirty:
        raise refusal("uncommitted-changes", "controller", "the working tree changed meanwhile")
    step = f"impl:{task['task_id']}:{task['revision']}:{record['attempt']}"
    execution_result = {
        "schema_version": 1,
        "request_id": record["request_id"],
        "run_id": state.run_id,
        "kind": "implement-task",
        "gate": {"passed": True},
        "result_tree": result.tree,
        "access_attestation_sha256": result.access_sha,
    }
    record.update(result_tree=result.tree, access_attestation_sha256=result.access_sha)
    results = _directory(ws, state.run_id, "results")
    cm = sibling("_confined_mutation.py")
    cm.confined_atomic_replace(
        _store(ws, state.run_id), results / _record_name(record["request_id"]),
        json.dumps(execution_result, sort_keys=True).encode("utf-8"),
    )
    evidence = ws.evidence_append([
        loop.receipt(
            state, step, criterion=f"task:{task['task_id']}",
            term=f"gate:{task['task_id']}:{task['revision']}", observation="task-gate",
            outcome="pass", fingerprint=ws.git.product_tree(), revision=task["revision"],
        )
    ])
    new = ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="implement",
        trailers={**tdd._trailers(task), "Supervisor-Attempt": record["attempt_id"]},
        entries=result.entries,
        appends={"evidence.jsonl": evidence},
        summary=f"{task['position']} {task['title']}"[:200],
        known_steps=state.steps,
        product_source=source,
    )
    if new is None:
        raise refusal("integration-conflict", "controller", "the step is already reachable")
    kill_point("integrated")
    _materialize(ws, new)
    record.update(state="landed", commit=new)
    _write(ws, state.run_id, record)
    after = loop.derive(ws)
    ws.local.reconcile_events(after.run_id, after.commits)
    _journal(ws, state, record, "landed")
    return str(new)


def _materialize(ws: Any, sha: str) -> None:
    """Bring the working tree and index to the commit's own entries, idempotently.

    Only the paths the commit changed outside ``delivery/`` are written; a path the commit
    removed is removed from the working tree, a link anywhere on its way refused.
    """
    git = ws.git
    prefix = git.delivery_rel + "/"
    paths = [p for p in git.touched_paths(sha) if not p.startswith(prefix)]
    held = git.tree_modes(sha)
    adds = sorted(p for p in paths if p in held)
    if adds:
        git.hardened.run(
            "checkout-index", "-f", "-z", "--stdin",
            stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in adds) + b"\0",
        )
    for rel in sorted(p for p in paths if p not in held):
        _remove_working_file(Path(ws.root), rel)
    git.refresh_index(paths)


def _remove_working_file(root: Path, rel: str) -> None:
    """Remove *rel* under *root* when every directory on its way is a plain directory."""
    current = root
    for part in rel.split("/")[:-1]:
        current = current / part
        try:
            if not stat.S_ISDIR(os.lstat(current).st_mode):
                return
        except OSError:
            return
    target = root.joinpath(*rel.split("/"))
    try:
        target.unlink()
    except FileNotFoundError:
        return
    parent = target.parent
    while parent != root:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


# ── recovery ────────────────────────────────────────────────────────────────


def recover(ws: Any) -> None:
    """Settle every attempt a dead ``run-concurrent`` recorded; runs first in every verb.

    A commit carrying the attempt's trailer means landed (and the working tree is brought to
    it). Otherwise the launcher's group is ended and its end confirmed within the window, the
    attempt closes as cancelled, and its task goes to the floor; an end that cannot be
    confirmed leaves the attempt directory as residue and goes to the floor the same way.
    """
    try:
        approvals = ws.approvals()
    except _loop().Refusal:
        return  # the verb's own derivation names a malformed record
    if not approvals:
        return
    run_id = approvals[0]["run_id"]
    pending = [
        r for r in list_records(ws, run_id) if r["state"] in OPEN_STATES and not _verb_alive(r)
    ]
    if not pending:
        return
    commits = ws.git.supervisor_commits(run_id)
    for record in pending:
        attempt_id = record.get("attempt_id")
        by_attempt = (c for c in commits if c.trailers.get("Supervisor-Attempt") == attempt_id)
        landed = next(by_attempt, None) if attempt_id else None
        if landed is not None:
            _materialize(ws, landed.sha)
            record.update(state="landed", commit=landed.sha)
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
        ws.local.append_journal({
            "run_id": run_id,
            "at": ws.clock(),
            "head": ws.git.head(),
            "stage": "implementing",
            "kind": "run-concurrent",
            "request_id": record["request_id"],
            "outcome": record["state"],
            "reason": record.get("reason"),
        })


# ── report ──────────────────────────────────────────────────────────────────


def report_completion(ws: Any, state: Any, result: dict[str, Any]) -> str:
    """Admit a ``run-concurrent`` completion: only a request whose attempt landed completes."""
    record = read_record(ws, state.run_id, result["request_id"])
    if record is None or record["state"] != "landed":
        raise _loop().Refusal(
            "not-current-attempt", "controller", "the request's attempt has not landed"
        )
    return "run-concurrent"
