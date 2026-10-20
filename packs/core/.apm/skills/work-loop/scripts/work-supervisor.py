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

Standard library only; it loads only its sibling scripts. Python 3.11+.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
import traceback
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
    try:
        args = _parser().parse_args(argv)
        root = _repo_root(cwd)
        spec_rel = _spec_rel(root, args.spec_dir)
        result_data = _read_result(args.result) if args.verb == "report" else None
    except UsageError as exc:
        _emit({"error": "usage", "detail": str(exc)})
        return EXIT_USAGE
    admission = _supervisor("_supervisor_admission.py")
    loop = _supervisor("_supervisor_loop.py")
    commit = _supervisor("_supervisor_commit.py")
    statelock = commit.sibling("_statelock.py")
    workspace = admission.Workspace(root, spec_rel)
    try:
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
