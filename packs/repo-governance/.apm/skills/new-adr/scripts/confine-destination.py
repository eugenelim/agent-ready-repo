#!/usr/bin/env python3
"""Confine a destination to the repository root and print the proven path.

Usage: confine-destination.py <repo-root> <relative-dir> [--new-file NAME | --read-file NAME]
       confine-destination.py <repo-root> --root-file NAME

Exit 0 prints exactly one line: the absolute, fully resolved path to use
verbatim.  Exit 2 prints `refused: <reason>` to stderr and nothing to stdout.
Exit 3 (an absent --read-file or --root-file name) prints nothing.  Only stats
and resolves; writes nothing.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_USAGE = (
    "usage: confine-destination.py <repo-root> <relative-dir> "
    "[--new-file NAME | --read-file NAME] | <repo-root> --root-file NAME"
)


def _load_helper() -> ModuleType:
    """Load the sibling ``_record_paths.py`` by path under a unique name."""
    path = Path(__file__).resolve().parent / "_record_paths.py"
    spec = importlib.util.spec_from_file_location(
        "new_adr_confine_destination_record_paths", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Loading must not write a __pycache__ next to the script: a refusal has
    # no filesystem effect.
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _parse(argv: list[str]) -> tuple[str, str | None, dict[str, str]]:
    """Return ``(root, relative, options)`` or raise ValueError on bad usage."""
    positionals: list[str] = []
    options: dict[str, str] = {}
    items = iter(argv)
    for item in items:
        if item in ("--new-file", "--read-file", "--root-file"):
            value = next(items, None)
            if value is None or item in options:
                raise ValueError(_USAGE)
            options[item] = value
        else:
            positionals.append(item)
    if len(options) > 1:
        raise ValueError(_USAGE)
    if "--root-file" in options:
        if len(positionals) != 1:
            raise ValueError(_USAGE)
        return positionals[0], None, options
    if len(positionals) != 2:
        raise ValueError(_USAGE)
    return positionals[0], positionals[1], options


def main(argv: list[str]) -> int:
    """Run the check; return the process exit code."""
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    # A refusal message may quote a non-UTF-8 argument; never fail printing it.
    sys.stderr.reconfigure(  # type: ignore[union-attr]
        encoding="utf-8", errors="backslashreplace")
    try:
        helper = _load_helper()
        root, relative, options = _parse(argv)
        try:
            if relative is None:
                result = helper.confine_root_file(root, options["--root-file"])
            else:
                result = helper.confine_destination(
                    root, relative,
                    new_file=options.get("--new-file"),
                    read_file=options.get("--read-file"))
        except helper.EntryAbsent:
            return 3
    except BaseException as exc:  # never a traceback
        reason = str(exc) or type(exc).__name__
        print(f"refused: {reason}".replace("\n", " "), file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
