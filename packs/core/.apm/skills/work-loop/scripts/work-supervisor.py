#!/usr/bin/env python3
"""work-supervisor — derive, admit, and record an approved spec's execution.

Usage, from the repository root:

    work-supervisor.py start <spec-dir> --intent code|spec-plan \\
        --code-trust trusted|untrusted --authority-ref owner[:<hex>] \\
        --review-authority-ref plan-reviewer[:<hex>]
    work-supervisor.py next <spec-dir>
    work-supervisor.py report <spec-dir> <result.json>
    work-supervisor.py status <spec-dir> [--json] [--check]
    work-supervisor.py resolve-effect <spec-dir> --operation <key> \\
        --decision effect-confirmed|do-not-retry|retry-authorized \\
        --authority-ref effect-authority[:<hex>]

Every verb prints one JSON object. A refusal, including a Git or run-lock
failure, prints ``{"refusal": {"code", "owner", "detail"}}``. Exit codes: 0
success, 1 refusal, 2 usage error; ``status --check`` exits 3 when the
implementation retry cap is reached on a non-terminal run, which takes
precedence over 1.

Before it loads any sibling script, every verb hashes the installed supervisor
files, compares them with the digests the first admitted ``start`` pinned in the
supervisor store under the Git directory, and refuses ``supervisor-changed`` on
a difference. It also keeps bytecode files from loading or being written.

Standard library only; it loads only its sibling scripts. Python 3.11+.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).resolve().parent
_MAX_RESULT_BYTES = 16 * 1024 * 1024
EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_CAP = 0, 1, 2, 3

_STORE_ROOT = "agentbundle-supervisor"
_RUN_ID_RE = re.compile(r"run-[0-9a-f]{16}")
_HEX_RE = re.compile(r"[0-9a-f]{64}")
_POLICY_FILES = ("supervisor-policy.json", "review-rules.json")
_MAX_PIN_BYTES = 1024 * 1024
_MAX_SOURCE_BYTES = 16 * 1024 * 1024


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


class UsageError(Exception):
    """A malformed invocation."""


class _PinRefused(Exception):
    """The installed supervisor cannot be shown to match its pinned digests.

    *unverifiable* marks a check that could not be made (a record that is
    missing, malformed, or unreadable), as opposed to one that found a difference;
    only the former is written to the security-event log.
    """

    def __init__(self, detail: str, *, unverifiable: bool = False) -> None:
        super().__init__(detail)
        self.unverifiable = unverifiable


# ── the pin check: standard library only, before any sibling loads ───────────


def _isolate_bytecode() -> Callable[[], None]:
    """Keep bytecode files from loading or being written; return the undo.

    A bytecode file planted beside a pinned module would otherwise load in place of
    its source. The cache prefix points at an empty per-process directory, so no
    cache beside the source is ever read, and nothing is written.
    """
    previous = (sys.dont_write_bytecode, sys.pycache_prefix)
    scratch = tempfile.mkdtemp(prefix="work-supervisor-pyc-")
    sys.dont_write_bytecode = True
    sys.pycache_prefix = scratch

    def undo() -> None:
        sys.dont_write_bytecode, sys.pycache_prefix = previous
        shutil.rmtree(scratch, ignore_errors=True)

    return undo


def _read_plain(path: Path, limit: int) -> bytes | None:
    """The bytes of a plain file within *limit*; ``None`` when it is absent."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _PinRefused(f"{path.name} cannot be read", unverifiable=True) from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise _PinRefused(f"{path.name} is not a plain file within its bound", unverifiable=True)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as handle:
            return handle.read(limit + 1)
    except OSError as exc:
        raise _PinRefused(f"{path.name} cannot be read", unverifiable=True) from exc


def _installed_digests(skill: Path) -> dict[str, str]:
    """sha256 of each installed supervisor module and of the policy and rules files."""
    found: dict[str, str] = {}
    scripts = skill / "scripts"
    try:
        names = sorted(entry.name for entry in scripts.iterdir())
    except OSError as exc:
        raise _PinRefused("the installed scripts cannot be listed", unverifiable=True) from exc
    for name in names:
        data = _read_plain(scripts / name, _MAX_SOURCE_BYTES) if name.endswith(".py") else None
        if data is not None:
            found[f"scripts/{name}"] = hashlib.sha256(data).hexdigest()
    for name in _POLICY_FILES:
        data = _read_plain(skill / name, _MAX_SOURCE_BYTES)
        if data is not None:
            found[name] = hashlib.sha256(data).hexdigest()
    return found


def _locate(cwd: Path | None) -> tuple[Path, Path] | None:
    """The work tree root and its Git directory, by direct reads; ``None`` when not found."""
    current = Path(cwd if cwd is not None else Path.cwd()).resolve()
    for directory in (current, *current.parents):
        dot_git = directory / ".git"
        try:
            kind = os.lstat(dot_git).st_mode
        except FileNotFoundError:
            continue
        except OSError:
            return None
        if stat.S_ISDIR(kind):
            return directory, dot_git
        if stat.S_ISREG(kind):
            text = _read_plain(dot_git, 64 * 1024)
            match = re.fullmatch(r"gitdir: (.+?)\r?\n?", (text or b"").decode("utf-8", "replace"))
            return (directory, directory / match.group(1)) if match else None
        return None
    return None


def _pin_map(path: Path, key: str) -> dict[str, str] | None:
    """The digest map under *key* in a store record; ``None`` when the record is absent."""
    data = _read_plain(path, _MAX_PIN_BYTES)
    if data is None:
        return None
    try:
        record = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        record = None
    digests = record.get(key) if isinstance(record, dict) else None
    if (
        not isinstance(record, dict)
        or record.get("schema_version") != 1
        or not isinstance(digests, dict)
        or not digests
        or not all(isinstance(k, str) and _HEX_RE.fullmatch(str(v)) for k, v in digests.items())
    ):
        raise _PinRefused(f"{path.name} is malformed", unverifiable=True)
    return digests  # type: ignore[no-any-return]


def _working_run_id(root: Path, spec_dir: str) -> str | None:
    """The run id on the first line of the spec's working ``approvals.jsonl``, if any."""
    parts = [p for p in spec_dir.split("/") if p]
    if not parts or "\\" in spec_dir or ":" in spec_dir or any(p in (".", "..") for p in parts):
        return None
    try:
        data = _read_plain(root.joinpath(*parts, "delivery", "approvals.jsonl"), _MAX_SOURCE_BYTES)
        first = json.loads(data.split(b"\n", 1)[0].decode("utf-8")) if data else None
    except (_PinRefused, UnicodeDecodeError, ValueError):
        return None
    run_id = first.get("run_id") if isinstance(first, dict) else None
    return run_id if isinstance(run_id, str) and _RUN_ID_RE.fullmatch(run_id) else None


def _preflight(spec_dir: str, cwd: Path | None, installed: dict[str, str]) -> None:
    """Refuse unless the installed files match the run's pins, before any sibling loads.

    The run is found from the working copy of the spec's approvals. A start that
    finds none is the first admission and pins the files itself; anything a
    missing working copy hides is caught again once HEAD can be read.
    """
    located = _locate(cwd)
    if located is None:
        return
    root, git_dir = located
    run_id = _working_run_id(root, spec_dir)
    if run_id is None:
        return
    store = git_dir / _STORE_ROOT / run_id
    pinned = _pin_map(store / "pins.json", "digests")
    if pinned is None:
        raise _PinRefused("the supervisor's pin record is missing", unverifiable=True)
    if installed == pinned:
        return
    if installed == _pin_map(store / "regenerate.json", "source"):
        return
    raise _PinRefused("the installed supervisor differs from its pinned digests")


def _log_pin_event(spec_dir: str, cwd: Path | None) -> None:
    """Append one ``security-event.v1`` denial for an unverifiable pin check; best effort."""
    located = _locate(cwd)
    parts = [p for p in spec_dir.split("/") if p]
    if located is None or not parts or any(p in (".", "..") for p in parts):
        return
    event = {
        "schema_version": 1,
        "operation_id": "op-" + secrets.token_hex(16),
        "correlation_id": "/".join(parts),
        "event_type": "supervisor-pin-check",
        "outcome": "denied",
        "reason_code": "supervisor-changed",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        current = located[0]
        for part in (*parts, ".supervisor"):
            current = current / part
            try:
                info = os.lstat(current)
            except FileNotFoundError:
                current.mkdir(mode=0o755)
                info = os.lstat(current)
            if not stat.S_ISDIR(info.st_mode):
                return
        marker = current / ".gitignore"
        if not os.path.lexists(marker):
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow, 0o644)
            with os.fdopen(fd, "wb") as handle:
                handle.write(b"*\n")
        fd = os.open(
            current / "security-events.jsonl",
            os.O_WRONLY | os.O_APPEND | os.O_CREAT | nofollow,
            0o644,
        )
        with os.fdopen(fd, "ab") as handle:
            handle.write(line)
    except OSError:
        return


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="work-supervisor.py", description=__doc__.split("\n\n")[0])
    verbs = parser.add_subparsers(dest="verb", required=True, parser_class=_Parser)
    start = verbs.add_parser("start")
    start.add_argument("spec_dir")
    start.add_argument("--intent", required=True, choices=("code", "spec-plan"))
    start.add_argument("--code-trust", required=True, choices=("trusted", "untrusted"))
    start.add_argument("--authority-ref", required=True)
    start.add_argument("--review-authority-ref", required=True)
    verbs.add_parser("next").add_argument("spec_dir")
    report = verbs.add_parser("report")
    report.add_argument("spec_dir")
    report.add_argument("result")
    status = verbs.add_parser("status")
    status.add_argument("spec_dir")
    status.add_argument("--json", action="store_true")
    status.add_argument("--check", action="store_true")
    resolve = verbs.add_parser("resolve-effect")
    resolve.add_argument("spec_dir")
    resolve.add_argument("--operation", required=True)
    resolve.add_argument("--decision", required=True)
    resolve.add_argument("--authority-ref", required=True)
    return parser


def _repo_root(cwd: Path | None) -> Path:
    """The repository root, found through the hardened Git helper."""
    git = _supervisor("_supervisor_git.py")
    try:
        return git.discover(cwd).root
    except git.SupervisorGitError as exc:
        if exc.code == "denied-git-unavailable":
            raise UsageError(f"cannot find the repository root: {exc}") from exc
        raise UsageError("run from inside a Git repository") from exc


def _spec_rel(root: Path, raw: str) -> str:
    """Confine <spec-dir> to the repository and return it repository-relative."""
    if not raw or "\\" in raw or raw.startswith("/") or ":" in raw:
        raise UsageError("<spec-dir> must be a repository-relative POSIX path")
    parts = [p for p in raw.strip("/").split("/") if p]
    if not parts or any(p in (".", "..") for p in parts):
        raise UsageError("<spec-dir> must not contain . or .. segments")
    current = root
    for part in parts:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError as exc:
            raise UsageError(f"{raw} does not exist") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise UsageError(f"{raw} must be a plain directory inside the repository")
    return "/".join(parts)


def _read_result(path: str) -> Any:
    """Read the controller's result file as data: bounded, regular, JSON."""
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise UsageError(f"cannot read {path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_RESULT_BYTES:
        raise UsageError("the result must be a regular file of at most 16 MiB")
    with Path(path).open("rb") as handle:
        data = handle.read(_MAX_RESULT_BYTES + 1)
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise UsageError("the result is not UTF-8 JSON") from exc


def _log_unverifiable(workspace: Any, code: str) -> None:
    """Write the security-event line an unverifiable Git check owes; best effort."""
    se = _supervisor("_security_events.py")
    event = se.SecurityEvent(
        schema_version=1,
        operation_id=se.make_operation_id(),
        correlation_id=workspace.spec_rel,
        event_type="supervisor-git-check",
        outcome="denied",
        reason_code=code,
        timestamp=workspace.clock(),
    )
    se.emit_denial_best_effort(workspace.local.security_sink(), event)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None, *, cwd: Path | None = None) -> int:
    """Run one verb from *cwd* (default: the process directory); the test seam."""
    undo = _isolate_bytecode()
    try:
        return _main(argv, cwd)
    finally:
        undo()


def _main(argv: list[str] | None, cwd: Path | None) -> int:
    spec_dir = ""
    try:
        args = _parser().parse_args(argv)
        spec_dir = args.spec_dir
        installed = _installed_digests(_SCRIPTS_DIR.parent)
        _preflight(args.spec_dir, cwd, installed)
        root = _repo_root(cwd)
        spec_rel = _spec_rel(root, args.spec_dir)
        result_data = _read_result(args.result) if args.verb == "report" else None
    except UsageError as exc:
        _emit({"error": "usage", "detail": str(exc)})
        return EXIT_USAGE
    except _PinRefused as exc:
        if exc.unverifiable:
            _log_pin_event(spec_dir, cwd)
        refusal = {"code": "supervisor-changed", "owner": "controller", "detail": str(exc)}
        _emit({"refusal": refusal})
        return EXIT_REFUSED
    admission = _supervisor("_supervisor_admission.py")
    loop = _supervisor("_supervisor_loop.py")
    commit = _supervisor("_supervisor_commit.py")
    statelock = commit.sibling("_statelock.py")
    workspace = admission.Workspace(root, spec_rel)
    workspace.attempts.installed = installed
    try:
        workspace.attempts.check_pins()
        if args.verb == "start":
            with workspace.run_lock():
                outcome = admission.start(
                    workspace,
                    intent=args.intent,
                    code_trust=args.code_trust,
                    authority_ref=args.authority_ref,
                    review_authority_ref=args.review_authority_ref,
                )
                state = loop.derive(workspace)
                if state.refusal is None:
                    workspace.local.reconcile_events(state.run_id, state.commits)
                    action = loop.Action("terminal") if outcome["status"] == "terminal" else None
                    workspace.local.write_run(loop.run_status(workspace, state, action))
            _emit(outcome)
            return EXIT_OK
        if args.verb == "next":
            payload = loop.next_request(workspace)
            _emit(payload)
            return EXIT_REFUSED if "refusal" in payload else EXIT_OK
        if args.verb == "report":
            _emit(loop.report(workspace, result_data))
            return EXIT_OK
        if args.verb == "resolve-effect":
            effects = _supervisor("_supervisor_effects.py")
            _emit(
                effects.resolve_effect(
                    workspace,
                    operation=args.operation,
                    decision=args.decision,
                    authority_ref=args.authority_ref,
                )
            )
            return EXIT_OK
        view = loop.status(workspace)
        _emit(view)
        if not args.check or view["terminal"]:
            return EXIT_OK
        if view["retry_count"] >= int(workspace.policy["implementation_retry_cap"]):
            return EXIT_CAP
        return EXIT_REFUSED if view.get("refusal") else EXIT_OK
    except admission.Refusal as exc:
        _emit({"refusal": exc.as_dict()})
        return EXIT_REFUSED
    except commit.SupervisorGitError as exc:
        if exc.unverifiable:
            _log_unverifiable(workspace, exc.code)
        _emit({"refusal": {"code": exc.code, "owner": "controller", "detail": str(exc)}})
        return EXIT_REFUSED
    except statelock.StateLockError as exc:
        # Includes a lock held past its stale window and then lost mid-step.
        _emit({
            "refusal": {
                "code": "run-locked",
                "owner": "controller",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        })
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - every verb ends in one JSON object
        # A defect in this script, not in the records: name where it was raised.
        frame = traceback.extract_tb(exc.__traceback__)[-1]
        _emit({
            "refusal": {
                "code": "internal-error",
                "owner": "skill maintainer",
                "detail": f"{type(exc).__name__}: {exc} at "
                f"{Path(frame.filename).name}:{frame.lineno}",
            }
        })
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
