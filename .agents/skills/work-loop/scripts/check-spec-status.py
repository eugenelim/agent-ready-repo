#!/usr/bin/env python3
"""check-spec-status — guard: a spec or plan file must have a specific Status value.

Used as the reviewers-clean guard in CODE-REVIEW → CODE-HUMAN-GATE (default: Status Shipped)
and as the spec-approved / plan-approved / plan-locked guards (--expect Approved).

Usage:
    check-spec-status.py <spec-dir> [--expect <status>] [--file <filename>]

    <spec-dir>          directory containing the target file
    --expect <status>   expected Status value (default: Shipped)
    --file <filename>   file to read within <spec-dir> (default: spec.md)

Exit 0 iff the canonical status parser resolves the file's Status to the expected value.
Exit non-zero with a one-line reason on stderr otherwise.

Imports parse_status / extract_status_token from lint-spec-status.py via
importlib so both tools share one canonical parser implementation.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import stat
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent


# Control-character neutralisation for this tool's own diagnostics.
#
# A DELIBERATE copy of `_loop_guards._CONTROL_ESCAPES`, and the duplication is the
# point: these lines fire on paths where the guard module may be unavailable or
# unloadable, which is exactly when a diagnostic matters most. Reaching through the
# loader here would make the sanitiser fail in the case it exists for.
#
# Not cosmetic. A refusal interpolates filenames and exception text that can originate
# in a planted file — `_recover_engine_state_tmp` reads its name from a `glob()` — so a
# `.engine-state-<ESC>[2J<ESC>[31mFAKE-OK.json.tmp` emitted a real screen-clear and
# colour change into the stream a supervising agent captures and logs.
_CONTROL_ESCAPES = str.maketrans({c: f"\\x{c:02x}" for c in [*range(32), 127]})


def _diag(text: object) -> str:
    """One-line, control-character-safe text for a warning or a refusal."""
    return " ".join(str(text).split()).translate(_CONTROL_ESCAPES)


def stop(reason: str, code: int = 1) -> int:
    """One line on stderr, a non-zero exit, never a traceback."""
    print(f"check-spec-status: {_diag(reason)}", file=sys.stderr)
    return code


class GuardsUnavailable(RuntimeError):
    """`_loop_guards.py` could not be loaded; every verb must refuse."""


_guards_module: object | None = None


def load_guards():
    """Load the sibling `_loop_guards.py` by path, once per process.

    ── This function body is identical in all three of `loop-cohort.py`,
    ── `loop-engine.py` and `check-spec-status.py`. That is a decision, not an
    ── accident: the loader cannot live in the module it loads, and importing
    ── `loop-cohort.py`'s 1500-line argparse CLI just to borrow it is the coupling
    ── the whole change exists to avoid. `test_loader_copies_are_structurally_identical`
    ── compares the three ASTs and keeps them from drifting.
    ──
    ── By path rather than `import _loop_guards`, matching `_statelock()`: a plain
    ── import resolves under file-path invocation but not under the importlib-based
    ── test harness, which does not put this directory on `sys.path`.
    ──
    ── NOT registered in `sys.modules`, also matching `_statelock()`. `exec_module`
    ── does not remove a registered entry when the module body raises, so
    ── registering would mean hand-rolling the failed-load cleanup that `import`
    ── does for free — and would make the module a session-global singleton whose
    ── memoised parser leaks between test files.
    ──
    ── `sys.dont_write_bytecode` is saved and restored to its PRIOR value, never to
    ── `False`, so a host interpreter started with `-B` keeps its setting.
    """
    global _guards_module
    if _guards_module is not None:
        return _guards_module
    path = SCRIPT_DIR / "_loop_guards.py"
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise GuardsUnavailable(
            f"cannot load {path}: {exc}. Restore the file or re-run `make build-self`."
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise GuardsUnavailable(
            f"cannot load {path}: not a regular file (symlink or device). "
            "Restore the file or re-run `make build-self`."
        )
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("_loop_guards", str(path))
        if spec is None or spec.loader is None:
            raise GuardsUnavailable(f"cannot load {path}: no import spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except GuardsUnavailable:
        raise
    except BaseException as exc:
        raise GuardsUnavailable(
            f"cannot load {path}: {type(exc).__name__}: {exc}. Restore the file or "
            "re-run `make build-self`."
        ) from exc
    finally:
        sys.dont_write_bytecode = previous
    if not getattr(module, "_MODULE_COMPLETE", False):
        raise GuardsUnavailable(
            f"cannot load {path}: module is truncated (no completeness marker). "
            "Restore the file or re-run `make build-self`."
        )
    # AC13's completeness check: the module's OWN `__all__` is the contract, so it
    # is never restated here. Three hand-enumerated copies drifted immediately —
    # `check-spec-status.py`'s omitted `check_artifact_status`, the only function it
    # calls — which is why an enumeration is explicitly rejected. A file truncated
    # at a clean statement boundary loads WITHOUT raising, so `__all__` is present
    # while the names it promises are not; that is the gap this closes.
    exported = getattr(module, "__all__", None)
    if not exported:
        raise GuardsUnavailable(
            f"cannot load {path}: module declares no __all__. Restore the file or "
            "re-run `make build-self`."
        )
    missing = sorted(set(exported) - set(dir(module)))
    if missing:
        # Naming a few is diagnostic; naming all 21 makes a 450-char "one-line"
        # refusal. The count carries the rest.
        shown = ", ".join(missing[:5])
        if len(missing) > 5:
            shown += f" (+{len(missing) - 5} more)"
        raise GuardsUnavailable(
            f"cannot load {path}: incomplete module, missing {shown}. Restore the "
            "file or re-run `make build-self`."
        )
    _guards_module = module
    return _guards_module


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="check-spec-status",
        description="Guard: verify that a spec or plan file has the expected Status value.",
    )
    parser.add_argument("spec_dir", help="directory containing the target file")
    parser.add_argument(
        "--expect",
        default="Shipped",
        help="expected Status value (default: Shipped)",
    )
    parser.add_argument(
        "--file",
        default="spec.md",
        help="file to read within spec-dir (default: spec.md)",
    )
    args = parser.parse_args()

    try:
        guards = load_guards()
    except GuardsUnavailable as exc:
        return stop(str(exc))

    spec_dir = Path(args.spec_dir).resolve()
    result = guards.check_artifact_status(
        spec_dir, filename=args.file, expect=args.expect
    )
    if not result.ok:
        return stop(result.reason)
    print(f"check-spec-status: {result.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
