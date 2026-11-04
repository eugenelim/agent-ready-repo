#!/usr/bin/env python3
"""evidence-gate — bounded evidence entries the controller runs for finding adjudication.

Subcommands:

* ``git-history --path <path> [--base <commit>]`` prints what a changed path was at
  the change base, from committed Git objects only.
* ``proof-run`` records one controller-observed run result as a digest envelope under
  ``.context/proof-runs/`` and prints the proof-by-run assessment it supports. It
  executes no supplied command; the controller ran it and hands over the captured
  command, stdout, and stderr as files under ``.context/``. Git is its only launch,
  and the only entry that asks Git for ``status``.

Exit 0 prints a JSON envelope on stdout. A refusal prints
``{"refused": <code>, "detail": <fixed remedy text>}`` on stdout and exits 2.
Every Git call goes through ``_supervisor_git.HardenedGit``; this script starts no process.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from typing import Any, NoReturn

SUBCOMMANDS = ("proof-run", "git-history")
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROOF_OPTIONS = (
    "--report-id",
    "--finding-id",
    "--assessment-id",
    "--review-subject-fingerprint",
    "--observed",
    "--exit-status",
    "--authority",
    "--command-file",
    "--stdout-file",
    "--stderr-file",
)
_VALUE_OPTIONS = ("--path", "--base", *_PROOF_OPTIONS)
_INPUT_CAP = 1024 * 1024
_REVIEWS_DIR = "reviews"
_PROOF_RUNS_DIR = "proof-runs"

_DETAILS = {
    "denied-not-in-catalog": (
        "Use `git-history --path <path> [--base <commit>]`, each option at most once."
    ),
    "denied-tree-dirty": "Commit or discard changes to tracked files, then retry.",
    "denied-git-config": (
        "Remove the repository config entries that make Git run a program, then retry."
    ),
    "denied-input-path": (
        "Pass files under .context/, outside .context/reviews/ and .context/proof-runs/."
    ),
    "denied-input-unreadable": (
        "Pass regular, single-link files of at most 1 MiB that are not symbolic links."
    ),
    "denied-input-too-large": "Each captured input must be at most 1 MiB.",
    "denied-proof-runs-dir": "Remove the symbolic link or non-directory at .context/proof-runs.",
    "denied-envelope-exists": "A different envelope already holds this name; do not overwrite it.",
    "denied-envelope-write": "The envelope could not be written safely; check .context/.",
    "denied-proof-run-invalid": "The assessment inputs were refused; check the argument values.",
}


class _Usage(Exception):
    """The command line is outside the catalog."""


class _Parser(argparse.ArgumentParser):
    """An argument parser that raises instead of printing usage and exiting."""

    def error(self, message: str) -> NoReturn:
        raise _Usage(message)


class _Once(argparse.Action):
    """Store a value, refusing a second occurrence of the option."""

    def __call__(
        self, parser: Any, namespace: Any, values: Any, option_string: Any = None
    ) -> None:
        if getattr(namespace, self.dest, None) is not None:
            raise _Usage(f"{option_string} given twice")
        setattr(namespace, self.dest, values)


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop module by literal path without registering it globally."""
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise RuntimeError(f"sibling module is not a regular file: {filename}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load sibling module: {filename}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


_HISTORY: list[ModuleType] = []
_SIBLINGS: dict[str, ModuleType] = {}


def _history() -> ModuleType:
    if not _HISTORY:
        _HISTORY.append(_load_sibling("_evidence_gate_git_history", "_git_history.py"))
    return _HISTORY[0]


def supervisor_git() -> ModuleType:
    """The ``_supervisor_git`` module this script's Git calls run through."""
    module: ModuleType = _history().supervisor_git()
    return module


def _sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling once per process."""
    if module_name not in _SIBLINGS:
        _SIBLINGS[module_name] = _load_sibling(module_name, filename)
    return _SIBLINGS[module_name]


def _join_option_values(argv: list[str]) -> list[str]:
    """Rewrite ``--path X`` as ``--path=X`` so a value that starts with ``-`` stays a value."""
    joined: list[str] = []
    items = iter(argv)
    for token in items:
        if token in _VALUE_OPTIONS:
            following = next(items, None)
            joined.append(token if following is None else f"{token}={following}")
        else:
            joined.append(token)
    return joined


def _parser() -> _Parser:
    parser = _Parser(prog="evidence-gate", add_help=False, allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    proof = sub.add_parser("proof-run", add_help=False, allow_abbrev=False)
    for option in _PROOF_OPTIONS:
        if option == "--exit-status":
            proof.add_argument(option, action=_Once, required=True, type=int)
        elif option == "--observed":
            proof.add_argument(option, action=_Once, required=True, choices=("fail", "pass"))
        else:
            proof.add_argument(option, action=_Once, required=True)
    history = sub.add_parser("git-history", add_help=False, allow_abbrev=False)
    history.add_argument("--path", action=_Once, required=True)
    history.add_argument("--base", action=_Once, default=None)
    return parser


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")


def _refuse(code: str, detail: str | None = None) -> int:
    _emit({"refused": code, "detail": detail or _DETAILS.get(code, "The request was refused.")})
    return 2


class _ProofRefused(Exception):
    """A proof-run refusal carrying its stable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _lstat_identity(path: Path) -> tuple[int, int] | None:
    """Return ``(st_dev, st_ino)`` of *path* without following a link, or ``None`` when absent."""
    try:
        info = os.lstat(path)
    except OSError:
        return None
    return (info.st_dev, info.st_ino)


def _passes_through_excluded(
    path_identities: Iterable[tuple[int, int] | None],
    excluded: Iterable[tuple[int, int] | None],
) -> bool:
    """Return whether any identity on an input's directory path is an excluded one."""
    barred = {identity for identity in excluded if identity is not None}
    return any(identity in barred for identity in path_identities if identity is not None)


def _input_file(context: Path, raw: str) -> Path:
    """Resolve *raw* to a path under *context*, outside the review and proof-run folders."""
    candidate = Path(os.path.normpath(Path.cwd() / raw))
    for base in (candidate, Path(os.path.realpath(candidate.parent)) / candidate.name):
        try:
            relative = base.relative_to(context)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] not in {_REVIEWS_DIR, _PROOF_RUNS_DIR}:
            folders = [
                context.joinpath(*relative.parts[: n + 1]) for n in range(len(relative.parts) - 1)
            ]
            excluded = (
                _lstat_identity(context / _REVIEWS_DIR),
                _lstat_identity(context / _PROOF_RUNS_DIR),
            )
            if not _passes_through_excluded(map(_lstat_identity, folders), excluded):
                return base
        break
    raise _ProofRefused("denied-input-path")


def _read_input(safety: ModuleType, context: Path, raw: str) -> bytes:
    """Read one captured input through the confined reader."""
    path = _input_file(context, raw)
    try:
        data = safety.read_confined_regular_file(context, path, max_bytes=_INPUT_CAP)
    except safety.BoundExceeded as exc:
        raise _ProofRefused("denied-input-too-large") from exc
    except (safety.UnsafeContentError, OSError) as exc:
        raise _ProofRefused("denied-input-unreadable") from exc
    assert isinstance(data, bytes)
    return data


def _ensure_proof_runs_dir(context: Path) -> Path:
    """Return ``.context/proof-runs``, creating it when absent and refusing a link."""
    folder = context / _PROOF_RUNS_DIR
    try:
        info = os.lstat(folder)
    except FileNotFoundError:
        try:
            folder.mkdir(mode=0o700)
        except OSError as exc:
            raise _ProofRefused("denied-envelope-write") from exc
        return folder
    if not stat.S_ISDIR(info.st_mode):
        raise _ProofRefused("denied-proof-runs-dir")
    return folder


def _store_envelope(
    safety: ModuleType, mutation: ModuleType, context: Path, name: str, content: bytes
) -> None:
    """Create the envelope file, or accept an existing file holding identical bytes.

    The existing file is read with a bound equal to the exact length of ``content``, so a
    file of any other size is refused without a fixed cap that a valid envelope could exceed.
    """
    folder = _ensure_proof_runs_dir(context)
    target = folder / name
    try:
        existing: bytes | None = safety.read_confined_regular_file(
            context, target, max_bytes=len(content)
        )
    except (safety.UnsafeContentError, OSError) as exc:
        if os.path.lexists(target):
            raise _ProofRefused("denied-envelope-exists") from exc
        existing = None
    if existing is not None:
        if existing != content:
            raise _ProofRefused("denied-envelope-exists")
        return
    try:
        mutation.confined_create(context, target, content)
    except mutation.MutationDenied as exc:
        code = "denied-envelope-exists" if exc.denial_code == "denied-already-exists" else (
            "denied-envelope-write"
        )
        raise _ProofRefused(code) from exc


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_proof(args: argparse.Namespace) -> dict[str, Any]:
    """Build and store the envelope for one observed run, and return the assessment envelope.

    The stored file holds the five digest-envelope fields plus the raw command, stdout, and
    stderr decoded as UTF-8 with ``errors="replace"``; the digests cover the raw bytes.
    """
    module = supervisor_git()
    safety = _sibling("_evidence_gate_file_safety", "_file_safety.py")
    mutation = _sibling("_evidence_gate_confined_mutation", "_confined_mutation.py")
    assessment = _sibling("_evidence_gate_review_assessment", "_review_assessment.py")
    git = module.HardenedGit(Path.cwd())
    if module.code_running_keys(git.config_entries()):
        raise _ProofRefused("denied-git-config")
    head = git.run("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    # Ignoring submodule dirtiness keeps status from running inside a submodule, whose own
    # config Git would honor; a submodule checked out at another commit still shows.
    if git.run(
        "status", "--porcelain=v1", "-z", "--untracked-files=no", "--ignore-submodules=dirty"
    ):
        raise _ProofRefused("denied-tree-dirty")
    context = git.pins.root / ".context"
    command = _read_input(safety, context, args.command_file)
    stdout = _read_input(safety, context, args.stdout_file)
    stderr = _read_input(safety, context, args.stderr_file)
    envelope = {
        "command_sha256": _sha256(command),
        "exit_status": args.exit_status,
        "stderr_sha256": _sha256(stderr),
        "stdout_sha256": _sha256(stdout),
        "subject_commit": head,
    }
    try:
        result = assessment.proof_by_run_assessment(
            assessment_id=args.assessment_id,
            report_id=args.report_id,
            finding_id=args.finding_id,
            review_subject_fingerprint=args.review_subject_fingerprint,
            observed=args.observed,
            envelope=envelope,
            current_subject_commit=head,
            judgment_authority=args.authority,
        )
        digest = assessment.proof_run_envelope_digest(envelope)
    except assessment.ReviewAssessmentRefused as exc:
        raise _ProofRefused("denied-proof-run-invalid") from exc
    stored = {
        **envelope,
        "command": command.decode("utf-8", "replace"),
        "stdout": stdout.decode("utf-8", "replace"),
        "stderr": stderr.decode("utf-8", "replace"),
    }
    name = f"{_sha256(args.assessment_id.encode('utf-8', 'surrogateescape'))}-{digest}.json"
    body = (json.dumps(stored, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    _store_envelope(safety, mutation, context, name, body)
    return result


def _proof_run(args: argparse.Namespace) -> int:
    """Run the ``proof-run`` subcommand and print the assessment or a refusal."""
    module = supervisor_git()
    try:
        _emit({"assessment": _run_proof(args)})
    except _ProofRefused as exc:
        return _refuse(exc.code)
    except module.SupervisorGitError as exc:
        return _refuse(exc.code, "The repository state could not be verified for this request.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one subcommand; return 0 on an envelope and 2 on a refusal."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        args = _parser().parse_args(_join_option_values(raw))
    except _Usage:
        return _refuse("denied-not-in-catalog")
    if args.command == "proof-run":
        return _proof_run(args)
    history = _history()
    module = history.supervisor_git()
    try:
        git = module.HardenedGit(Path.cwd())
        _emit(history.git_history(git, base=args.base, path=args.path))
    except history.GitHistoryRefused as exc:
        return _refuse(exc.code, exc.detail)
    except module.SupervisorGitError as exc:
        return _refuse(exc.code, "The repository state could not be verified for this request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
