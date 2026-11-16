"""Closed gate-execution.v1 records and gate-command validation.

These pure codecs confer no execution authority: the supervisor must write and
bind records itself. Records have schema_version 1 and type gate-execution.v1;
unknown, missing and extra fields refuse, including per-command fields. Digests
are lowercase SHA-256. task_revision is null for a run-wide gate. outcome is
started, passed or failed; a started record has no command results, and only a
nonempty set of successful, non-timeout results can pass. A null exit_code means
no process exit was observed. stdout_digest and stderr_digest describe bounded
captured bytes, not an unbounded output stream. The supervisor runner stores
a started checkpoint and immutable completed records beside execution-bound candidate
manifests keyed by a digest that includes file modes. A completed pass is written
only after bounded command execution and scratch cleanup finish under the run
lock. Standard library only.
Python 3.11+.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import secrets
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from time import monotonic
from time import monotonic as lock_clock
from typing import Any

_COMMAND_FIELDS = {"argv", "cwd", "expected_exit"}
_RESULT_FIELDS = _COMMAND_FIELDS | {
    "exit_code", "timed_out", "stdout_digest", "stderr_digest",
}
_RECORD_FIELDS = {
    "schema_version", "type", "execution_id", "run_id", "request_id", "issuance_id",
    "task_revision", "candidate_tree_digest", "gate_declaration_digest", "commands", "outcome",
}
_DIGEST = re.compile(r"[0-9a-f]{64}")


class ExecutionRefused(ValueError):
    """An unreadable or invalid execution record cannot serve as proof."""

    code = "gate-execution-invalid"


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON fields rather than choosing one interpretation."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExecutionRefused(f"duplicate field: {key}")
        result[key] = value
    return result


def load_json(data: str | bytes) -> Any:
    """Decode strict JSON used by declarations and records; refuse unreadable data."""
    try:
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        return json.loads(text, object_pairs_hook=_unique_fields)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ExecutionRefused("unreadable gate JSON") from exc


def _text(value: Any) -> bool:
    """Require nonempty text that can be passed to a process as UTF-8."""
    if not isinstance(value, str) or not value or "\0" in value:
        return False
    try:
        value.encode("utf-8")
    except UnicodeError:
        return False
    return True


def _digest(value: Any) -> bool:
    """Recognize an exact lowercase SHA-256 digest."""
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def validate_command(command: Any, *, observed: bool = False) -> None:
    """Validate a literal argv, confined relative cwd and optional observed result."""
    fields = _RESULT_FIELDS if observed else _COMMAND_FIELDS
    if not isinstance(command, dict) or set(command) != fields:
        raise ExecutionRefused("gate command fields differ from schema")
    argv, cwd, expected = command["argv"], command["cwd"], command["expected_exit"]
    if (
        not isinstance(argv, list) or not argv or not _text(argv[0])
        or not all(arg == "" or _text(arg) for arg in argv)
    ):
        raise ExecutionRefused("argv must be a string array with a nonempty executable")
    if not _text(cwd) or (cwd != "." and (
        "\\" in cwd or ":" in cwd or any(part in ("", ".", "..") for part in cwd.split("/"))
    )):
        raise ExecutionRefused("cwd must be . or a repository-relative directory")
    if type(expected) is not int or not 0 <= expected <= 255:
        raise ExecutionRefused("expected_exit must be an integer from 0 to 255")
    if observed and (
        (command["exit_code"] is not None and type(command["exit_code"]) is not int)
        or type(command["timed_out"]) is not bool
        or not _digest(command["stdout_digest"])
        or not _digest(command["stderr_digest"])
    ):
        raise ExecutionRefused("invalid observed command result")


def validate_execution(record: Any) -> None:
    """Refuse any record outside the closed execution schema or claiming a false pass."""
    if not isinstance(record, dict) or set(record) not in (
        _RECORD_FIELDS, _RECORD_FIELDS | {"runtime"},
    ):
        raise ExecutionRefused("execution fields differ from schema")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ExecutionRefused("unsupported execution schema version")
    if record["type"] != "gate-execution.v1":
        raise ExecutionRefused("unsupported execution record type")
    identities = ("execution_id", "run_id", "request_id", "issuance_id")
    if not all(_text(record[key]) for key in identities):
        raise ExecutionRefused("execution identities must be nonempty strings")
    if (
        not _digest(record["candidate_tree_digest"])
        or not _digest(record["gate_declaration_digest"])
        or (record["task_revision"] is not None and not _digest(record["task_revision"]))
    ):
        raise ExecutionRefused("execution binding digests must be SHA-256")
    if "runtime" in record:
        runtime = record["runtime"]
        if (not isinstance(runtime, dict)
                or set(runtime) != {"scratch", "supervisor_pid", "supervisor_start", "processes"}
                or not _text(runtime["scratch"])
                or type(runtime["supervisor_pid"]) is not int or runtime["supervisor_pid"] <= 0
                or not _text(runtime["supervisor_start"])
                or not isinstance(runtime["processes"], list)
                or any(not isinstance(group, dict) or set(group) != {"pgid", "start"}
                       or type(group["pgid"]) is not int or group["pgid"] <= 0
                       or not _text(group["start"]) for group in runtime["processes"])):
            raise ExecutionRefused("invalid execution runtime identity")
    commands, outcome = record["commands"], record["outcome"]
    if not isinstance(commands, list) or outcome not in ("started", "passed", "failed"):
        raise ExecutionRefused("invalid execution commands or outcome")
    for command in commands:
        validate_command(command, observed=True)
    if outcome == "started" and commands:
        raise ExecutionRefused("started execution cannot contain results")
    if outcome == "passed" and (not commands or any(
        command["timed_out"] or command["exit_code"] != command["expected_exit"]
        for command in commands
    )):
        raise ExecutionRefused("passing execution requires successful command results")


def encode_execution(record: dict[str, Any]) -> bytes:
    """Validate and encode a record as deterministic UTF-8 JSON."""
    validate_execution(record)
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_execution(data: bytes) -> dict[str, Any]:
    """Decode and validate a stored record, failing closed on unreadable bytes."""
    record = load_json(data)
    validate_execution(record)
    return record


# The gate budget leaves half the lock window for freezing, Git calls and cleanup.
GATE_BUDGET_SECONDS = 1200.0
OUTPUT_LIMIT = 1024 * 1024
CLEANUP_SECONDS = 30.0


@contextlib.contextmanager
def lock_budget(ws: Any) -> Generator[float, None, None]:
    """Stop starting Git calls before their bounded duration can outlive the lock."""
    started = lock_clock()
    deadline = started + float(ws.policy["run_lock_stale_seconds"]) - 300
    previous = ws.git.hardened.control_check

    def check(port: Any) -> None:
        """Keep the existing Git control checks and add the lock deadline."""
        if lock_clock() >= deadline:
            raise ExecutionRefused("gate execution exceeded the lock budget")
        if previous is not None:
            previous(port)

    ws.git.hardened.control_check = check
    try:
        yield started
    finally:
        ws.git.hardened.control_check = previous


def _launcher() -> Any:
    """Load the existing process-identity port in source and installed layouts."""
    path = Path(__file__).resolve().with_name("_supervisor_launcher.py")
    alias = "_gate_launcher_" + hashlib.sha256(os.fsencode(path)).hexdigest()[:12]
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        previous = sys.dont_write_bytecode, sys.pycache_prefix
        try:
            sys.dont_write_bytecode = True
            # An uncreated, unpredictable cache root prevents reading planted bytecode too.
            sys.pycache_prefix = str(Path(tempfile.gettempdir()) / secrets.token_hex(24))
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(alias, None)
            raise
        finally:
            sys.dont_write_bytecode, sys.pycache_prefix = previous
    return sys.modules[alias]


def _end_matching(group: dict[str, Any]) -> None:
    """End the original group, including descendants after its leader has exited."""
    # The shared port checks the leader's start time before signalling. A reused
    # leader id belongs to another group; an absent leader can leave original children.
    if not _launcher().end_group(group["pgid"], group["pgid"], group["start"]):
        raise ExecutionRefused("gate process group termination could not be confirmed")


def _process_start(pid: int) -> str | None:
    """Read a live process's start time, retrying a transient failure of the process table.

    The reader shells out, and a heavily loaded host can time it out once; the gate's
    wrapper is blocked on its pipe, so a live process always has a start time to read.
    """
    for delay in (0.0, 0.05, 0.25):
        if delay:
            time.sleep(delay)
        try:
            start = _launcher().process_start(pid)
        except (OSError, subprocess.TimeoutExpired):
            start = None
        if start is not None:
            return start
    return None


def recover(ws: Any) -> None:
    """End orphan executions before lock acquisition, including from status."""
    git_error = _launcher()._supervisor("_supervisor_git.py").SupervisorGitError
    try:
        approvals = ws.approvals()
    except git_error:
        # Unreadable Git state is refused by the verb's own guard before any Git call;
        # recovery is best effort and must not pre-empt that refusal.
        return
    if not approvals:
        return
    run_id = approvals[0]["run_id"]
    store = ws.git._store_dir(run_id)
    if not os.path.lexists(store):
        return
    # Use the same confined reader as the run store's other records.
    fs = _launcher()._supervisor("_supervisor_admission.py").sibling("_file_safety.py")
    fs.validate_confined_directory(ws.git.hardened.pins.git_dir, store)
    paths = []
    with os.scandir(store) as entries:
        for count, entry in enumerate(entries, 1):
            if count > 50000:
                raise ExecutionRefused("execution store has too many entries")
            if entry.name.startswith("exec-") and entry.name.endswith(".started.json"):
                paths.append(store / entry.name)
    for path in sorted(paths):
        completed = path.with_name(path.name.replace(".started.json", ".completed.json"))
        recovered = path.with_name(path.name.replace(".started.json", ".recovered"))
        if os.path.lexists(completed) or os.path.lexists(recovered):
            continue
        record = decode_execution(
            fs.read_confined_regular_file(
                ws.git.hardened.pins.git_dir, path, max_bytes=1024 * 1024,
            ),
        )
        runtime = record.get("runtime")
        if runtime is None:
            continue  # Earlier executions did not capture an identity safe to signal.
        start = _process_start(runtime["supervisor_pid"])
        if start == runtime["supervisor_start"]:
            continue
        if start is None:
            try:
                os.kill(runtime["supervisor_pid"], 0)
            except ProcessLookupError:
                pass  # ESRCH confirms absence; a failed table read alone cannot.
            except OSError:
                continue
            else:
                continue
        for group in runtime["processes"]:
            _end_matching(group)
        directory = Path(runtime["scratch"])
        root = Path(tempfile.gettempdir()).resolve()
        if (directory.parent != root or not directory.name.startswith("work-supervisor-gates-")
                or directory.is_symlink()):
            raise ExecutionRefused("orphan scratch path is not confined")
        if os.path.lexists(directory):
            fs.validate_confined_directory(root, directory)
            if not _cleanup(directory, CLEANUP_SECONDS):
                raise ExecutionRefused("orphan scratch cleanup failed")
        ws.attempts._put(run_id, recovered.name, b"recovered\n")


def _watchdog(group: dict[str, Any], deadline: float) -> None:
    """Keep the deadline in another session even when the supervisor is killed."""
    remaining = max(0.0, deadline - time.monotonic())
    if select.select([sys.stdin.buffer], [], [], remaining)[0]:
        if sys.stdin.buffer.read(1) == b"x":
            return
        # EOF means the supervisor died; the deadline remains in force.
        time.sleep(max(0.0, deadline - time.monotonic()))
    _end_matching(group)


def _stop(process: subprocess.Popen[bytes]) -> None:
    """End the child and its process group before waiting on bounded cleanup."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    except PermissionError:
        # Some hosts disallow group signalling even for the caller's own child.
        # Reap the leader; an undrained descendant pipe still prevents a pass.
        if process.poll() is None:
            process.kill()
    process.wait(timeout=5)


def _observe(
    command: dict[str, Any], directory: Path, budget: float,
    on_start: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Drain both pipes within one combined output cap and the remaining run budget."""
    observed: dict[str, Any] = {**command, "exit_code": None, "timed_out": False,
                "stdout_digest": hashlib.sha256(b"").hexdigest(),
                "stderr_digest": hashlib.sha256(b"").hexdigest()}
    if budget <= 0:
        observed["timed_out"] = True
        return observed, False
    cwd = (directory / command["cwd"]).resolve()
    if not cwd.is_relative_to(directory) or not cwd.is_dir():
        return observed, False
    deadline = monotonic() + budget
    try:
        process = subprocess.Popen(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--gate", *command["argv"]],
            cwd=cwd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name == "posix",
        )
    except OSError:
        return observed, False
    watchdog = None
    try:
        start = _process_start(process.pid)
        if start is None:
            raise ExecutionRefused("gate process start time cannot be read")
        group = {"pgid": process.pid, "start": start}
        watchdog = subprocess.Popen(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--watchdog",
             str(process.pid), start, str(time.monotonic() + budget)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if on_start is not None:
            on_start(group)
        assert process.stdin is not None
        process.stdin.write(b"x")
        process.stdin.close()
    except BaseException:
        _stop(process)
        if watchdog is not None:
            _stop(watchdog)
        raise
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    mutex = threading.Lock()
    overflow = threading.Event()
    read_error = threading.Event()

    def drain(name: str) -> None:
        """Retain at most OUTPUT_LIMIT bytes across both streams."""
        stream = getattr(process, name)
        try:
            while chunk := os.read(stream.fileno(), 65536):
                with mutex:
                    remaining = OUTPUT_LIMIT - sum(len(data) for data in captured.values())
                    captured[name].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        overflow.set()
                        return
        except (OSError, ValueError):
            read_error.set()
        finally:
            stream.close()

    readers = [threading.Thread(target=drain, args=(name,), daemon=True) for name in captured]
    try:
        for reader in readers:
            reader.start()
        while True:
            if monotonic() >= deadline:
                observed["timed_out"] = True
                break
            if overflow.is_set() or read_error.is_set():
                break
            if process.poll() is not None and not any(reader.is_alive() for reader in readers):
                break
            # A short poll also observes a child that closes both streams before exiting.
            overflow.wait(min(.01, max(0.0, deadline - monotonic())))
    finally:
        _stop(process)
        assert watchdog.stdin is not None
        with contextlib.suppress(BrokenPipeError):
            watchdog.stdin.write(b"x")
            watchdog.stdin.close()
        watchdog.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=5)
    with mutex:
        for name, data in captured.items():
            observed[name + "_digest"] = hashlib.sha256(data).hexdigest()
    observed["exit_code"] = process.returncode
    passed = (not observed["timed_out"] and not overflow.is_set() and not read_error.is_set()
              and not any(reader.is_alive() for reader in readers)
              and process.returncode == command["expected_exit"])
    return observed, passed


def mode_tree_digest(ws: Any, tree: str) -> str:
    """Hash every frozen path, mode and blob without changing the product digest."""
    digest = hashlib.sha256()
    for path, (mode, oid) in sorted(ws.git.tree_modes(tree).items()):
        digest.update(f"{path}\0{mode}\0{oid}\n".encode("utf-8", "surrogateescape"))
    return digest.hexdigest()


def candidate_manifest(
    ws: Any, run_id: str, name: str, expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read a confined manifest and verify retained bytes before reusing its key."""
    store = ws.git.ensure_store(run_id)
    fs = _launcher()._supervisor("_supervisor_admission.py").sibling("_file_safety.py")
    if expected is not None:
        ws.attempts._put(run_id, name, json.dumps(expected, sort_keys=True).encode())
    manifest = load_json(bytes(fs.read_confined_regular_file(
        store, store / name, max_bytes=4096,
    )))
    if not isinstance(manifest, dict) or (expected is not None and manifest != expected):
        raise ExecutionRefused("candidate manifest differs from execution")
    return manifest


def _freeze(ws: Any, state: Any, deadline: float) -> tuple[str, str]:
    """Retain an exact candidate tree without touching the public index or refs."""
    changes = ws.git.working_changes()
    with ws.git._private_index(state.head) as env:
        for path, entry in changes.items():
            if lock_clock() >= deadline:
                raise ExecutionRefused("candidate freezing exceeded the lock budget")
            if entry is None:
                ws.git.run("update-index", "--force-remove", "--", path, env=env)
            else:
                mode, oid = entry
                ws.git.run("update-index", "--add", "--cacheinfo", f"{mode},{oid},{path}", env=env)
        tree = ws.git.text("write-tree", env=env).strip()
    digest = ws.git.product_tree(tree)
    # Retain the earlier diagnostic snapshot; admission uses the execution binding.
    ws.attempts._put(state.run_id, f"candidate-{digest}.json", json.dumps({
        "schema_version": 1, "tree": tree, "candidate_tree_digest": digest,
    }, sort_keys=True).encode())
    return tree, digest


def _materialize(ws: Any, tree: str, directory: Path, deadline: float) -> None:
    """Copy raw Git blobs, retaining modes and only confined symlink targets."""
    # Archives apply export-ignore/subst, so materialize the recorded blobs directly.
    # Git trees cannot contain both a file and its descendant. Write links last as well.
    entries = ws.git.tree_modes(tree)
    links: list[tuple[Path, bytes]] = []
    for path, (mode, oid) in entries.items():
        if lock_clock() >= deadline:
            raise ExecutionRefused("candidate materialization exceeded the lock budget")
        target = directory / path
        if not target.resolve().is_relative_to(directory) or ".git" in Path(path).parts:
            raise ExecutionRefused("candidate path escapes scratch")
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "120000":
            links.append((target, ws.git.blob(oid)))
        elif mode in ("100644", "100755"):
            target.write_bytes(ws.git.blob(oid))
            target.chmod(0o755 if mode == "100755" else 0o644)
        else:
            raise ExecutionRefused("candidate contains an unsupported Git entry")
    for target, content in links:
        value = os.fsdecode(content)
        if not (target.parent / value).resolve().is_relative_to(directory):
            raise ExecutionRefused("candidate symlink escapes scratch")
        target.symlink_to(value)


def _cleanup(directory: Path, budget: float) -> bool:
    """Bound deletion too: a gate may have created arbitrarily many scratch files."""
    if budget <= 0:
        return False
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", "import shutil,sys; shutil.rmtree(sys.argv[1])",
         str(directory)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=os.name == "posix",
    )
    try:
        return process.wait(timeout=min(CLEANUP_SECONDS, budget)) == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        _stop(process)


def execute(
    ws: Any, state: Any, request: dict[str, Any], issuance: Any, loop: Any, lock_started: float,
) -> dict[str, Any]:
    """Run only committed approved commands; leave started alone on interruption."""
    # Reserve a whole bounded Git call plus cleanup before the lock can become stale.
    deadline = lock_started + float(ws.policy["run_lock_stale_seconds"]) - 300
    approved = next((commit.sha for commit in reversed(state.commits)
                     if commit.operation == "approval"), None)
    if approved is None:
        raise ExecutionRefused("no committed approval revision")
    raw = ws.git.show(ws.spec_rel + "/spec.md", approved)
    if raw is None:
        raise ExecutionRefused("approved spec is unreadable")
    commands = loop._projector.gate_declaration(raw.decode("utf-8"))
    tree, digest = _freeze(ws, state, deadline)
    record: dict[str, Any] = {
        "schema_version": 1, "type": "gate-execution.v1",
        "execution_id": "exec-" + secrets.token_hex(16), "run_id": state.run_id,
        "request_id": request["request_id"],
        "issuance_id": f"{issuance.run_id}:{issuance.seq:06d}",
        "task_revision": request.get("task", {}).get("revision"),
        "candidate_tree_digest": digest,
        "gate_declaration_digest": hashlib.sha256(json.dumps(
            commands, sort_keys=True, separators=(",", ":"),
        ).encode()).hexdigest(), "commands": [], "outcome": "started",
    }
    manifest = {"schema_version": 1, "tree": tree, "candidate_tree_digest": digest,
                "mode_tree_digest": mode_tree_digest(ws, tree)}
    candidate_manifest(ws, state.run_id, "candidate-" + manifest["mode_tree_digest"] + ".json",
                       manifest)
    candidate_manifest(ws, state.run_id, "candidate-" + record["execution_id"] + ".json",
                       manifest)
    supervisor_start = _process_start(os.getpid())
    if supervisor_start is None:
        raise ExecutionRefused("supervisor process start time cannot be read")
    directory = Path(tempfile.mkdtemp(prefix="work-supervisor-gates-")).resolve()
    record["runtime"] = {"scratch": str(directory), "supervisor_pid": os.getpid(),
                         "supervisor_start": supervisor_start, "processes": []}
    ws.attempts._put(
        state.run_id, record["execution_id"] + ".started.json", encode_execution(record),
    )

    def on_start(group: dict[str, Any]) -> None:
        """Checkpoint the identity before releasing any approved gate code."""
        record["runtime"]["processes"].append(group)
        started = {**record, "commands": [], "outcome": "started"}
        ws.attempts._put(state.run_id, record["execution_id"] + ".started.json",
                         encode_execution(started), replace=True)
    passed = True
    remaining = GATE_BUDGET_SECONDS
    try:
        _materialize(ws, tree, directory, deadline)
        for command in commands:
            before = monotonic()
            observed, successful = _observe(
                command, directory, min(remaining, deadline - lock_clock()), on_start,
            )
            remaining -= monotonic() - before
            record["commands"].append(observed)
            passed = passed and successful and remaining > 0
            if (remaining <= 0 or observed["timed_out"] or observed["exit_code"] is None
                    or observed["exit_code"] < 0
                    or (not successful and observed["exit_code"] == command["expected_exit"])):
                break
    finally:
        cleaned = _cleanup(directory, deadline - lock_clock())
    record["outcome"] = "passed" if passed and cleaned and lock_clock() < deadline else "failed"
    ws.attempts._put(
        state.run_id, record["execution_id"] + ".completed.json", encode_execution(record),
    )
    return record


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if sys.argv[1] == "--gate":
        # The parent persists this process's identity before allowing exec.
        if sys.stdin.buffer.read(1) != b"x":
            raise SystemExit(1)
        with Path(os.devnull).open("rb") as null:
            os.dup2(null.fileno(), 0)
        os.execvpe(sys.argv[2], sys.argv[2:], os.environ)
    elif sys.argv[1] == "--watchdog":
        _watchdog({"pgid": int(sys.argv[2]), "start": sys.argv[3]}, float(sys.argv[4]))
