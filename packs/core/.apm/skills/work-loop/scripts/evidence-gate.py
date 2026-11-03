#!/usr/bin/env python3
"""evidence-gate — bounded evidence entries the controller runs for finding adjudication.

Subcommands:

* ``git-history --path <path> [--base <commit>]`` prints what a changed path was at
  the change base, from committed Git objects only.
* ``proof-run`` is registered and refuses until its implementation lands.

Exit 0 prints a JSON envelope on stdout. A refusal prints
``{"refused": <code>, "detail": <fixed remedy text>}`` on stdout and exits 2.
Every Git call goes through ``_supervisor_git.HardenedGit``; this script starts no process.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, NoReturn

SUBCOMMANDS = ("proof-run", "git-history")
_SCRIPTS_DIR = Path(__file__).resolve().parent
_VALUE_OPTIONS = ("--path", "--base")

_DETAILS = {
    "denied-not-in-catalog": (
        "Use `git-history --path <path> [--base <commit>]`, each option at most once."
    ),
    "denied-proof-run-unavailable": "The proof-run subcommand is not available yet.",
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


def _history() -> ModuleType:
    if not _HISTORY:
        _HISTORY.append(_load_sibling("_evidence_gate_git_history", "_git_history.py"))
    return _HISTORY[0]


def supervisor_git() -> ModuleType:
    """The ``_supervisor_git`` module this script's Git calls run through."""
    module: ModuleType = _history().supervisor_git()
    return module


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
    sub.add_parser("proof-run", add_help=False, allow_abbrev=False)
    history = sub.add_parser("git-history", add_help=False, allow_abbrev=False)
    history.add_argument("--path", action=_Once, required=True)
    history.add_argument("--base", action=_Once, default=None)
    return parser


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")


def _refuse(code: str, detail: str | None = None) -> int:
    _emit({"refused": code, "detail": detail or _DETAILS.get(code, "The request was refused.")})
    return 2


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
        return _refuse("denied-proof-run-unavailable")
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
