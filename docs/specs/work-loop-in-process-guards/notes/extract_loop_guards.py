#!/usr/bin/env python3
"""One-shot: assemble `_loop_guards.py` by SLICING `loop-cohort.py`, not retyping it.

`canonical_contract` is ~100 lines whose output is a pinned digest: every approved
baseline in every in-flight run compares against it. Retyping it — even carefully —
risks a whitespace or ordering change that silently re-pins everything. So the
relocation is mechanical: each block is cut from the source between verified
anchors and reassembled, which makes byte-fidelity a property of the process rather
than of attention. T0's `test_recomputed_digests_match_golden` is the proof.

Run once, from the repo root. Refuses if the destination already exists.
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
SRC = SCRIPTS / "loop-cohort.py"
DEST = SCRIPTS / "_loop_guards.py"

# (start_anchor, end_anchor_exclusive, label). Both anchors are full-line prefixes
# and each must match exactly once, so a source edit that moves a block fails loudly
# here instead of producing a silently truncated slice.
BLOCKS: list[tuple[str, str, str]] = [
    ("_MAX_MANAGED_JSON_BYTES = ", "CLEAN_SUBSTRING = ", "managed-read cap"),
    ("def _template_max_implementation_retries(", "def stop(", "template readers + DEFAULTS"),
    ("def state_path_for(", "def write_state_atomic(", "state paths + managed JSON read"),
    ("_lint_module: object | None = None", "# The approved baseline pins",
     "parser loader + sha helper"),
    ("_STATUS_PLACEHOLDER = ", "# ── run_id / schema_version validation", "canonical contract"),
    ("def _validate_run_id(", "# ── scheduler", "run-id validation"),
    ("class UnreadableArtifact(", "@_locked(\"approve-plan\")", "status legality"),
]


def slice_block(text: str, start: str, end: str, label: str) -> str:
    starts = [i for i, line in enumerate(text.split("\n")) if line.startswith(start)]
    ends = [i for i, line in enumerate(text.split("\n")) if line.startswith(end)]
    if len(starts) != 1:
        raise SystemExit(f"{label}: start anchor {start!r} matched {len(starts)} lines")
    if not ends:
        raise SystemExit(f"{label}: end anchor {end!r} matched nothing")
    a = starts[0]
    after = [i for i in ends if i > a]
    if not after:
        raise SystemExit(f"{label}: end anchor {end!r} never follows the start")
    lines = text.split("\n")[a:after[0]]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


HEADER = '''"""_loop_guards — the work-loop's shared read-only guard API.

`loop-engine.py transition` used to shell out to `loop-cohort.py` and
`check-spec-status.py` for every read-only FSM guard, costing up to three extra
Python interpreters per transition. The guard *decisions* live here now, so the
engine and those CLIs call one implementation and cannot drift into disagreeing
about whether a transition is legal.

Contract — every public function in this module:

  * takes explicit typed arguments and returns a `GuardResult`;
  * prints NOTHING to stdout or stderr;
  * parses no arguments, reads no `sys.argv`, never calls `sys.exit`;
  * mutates no state file and creates no file anywhere;
  * never spawns a process and never opens a socket.

Two named exceptions to the first bullet, kept because their six mutation-verb
callers consume a reason string directly and rewriting those call sites is out of
scope: `validate_run_id` and `assert_status_legal` return `str | None`.

`spec_dir` precondition: callers pass an absolute, already-resolved,
already-confined `Path`. Confinement stays with the caller that owns it —
`loop-engine._resolve_spec_dir` (repo-root anchored), `loop-cohort._resolve_spec_dir`
(`..`-rejecting), and `check-spec-status.py`'s bare `resolve()`, which is the
weakest of the three and stays that way under its frozen argument surface. What a
callee can actually check, it does: that `spec_dir` exists and is a directory.
Re-testing "absolute, no `..`" would be dead code, because every caller resolves
first.

NOTE ON `from __future__ import annotations` — deliberately absent, unlike every
sibling script. `GuardResult` is a frozen dataclass, and under future-annotations
`dataclasses` resolves the defining module via `sys.modules.get(cls.__module__)`
with no `None` guard — so class creation raises `AttributeError` in a module loaded
by `exec_module` without being registered in `sys.modules`. Registering instead
would mean hand-rolling the failed-load cleanup that `import` does for free, and
would make this module a session-global singleton whose memoised parser leaks
across tests. PEP 604 unions evaluate natively above the 3.11 floor, so the import
buys nothing here. Probe-verified in both directions.

Every file read goes through `read_managed_json` / `read_managed_text`, which
`lstat`, require a regular file, open `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, re-check
type and dev/ino on the descriptor, and cap the read. `O_NONBLOCK` is load-bearing,
not defensive: the type pre-check is path-based and racy, and `os.open` on a FIFO
without it blocks forever — which, in-process, would block inside the engine's
critical section until the lock went stale and a second writer was admitted.

Python 3.11+ standard library only. No third-party imports, no packaging, no
installation.
"""

import contextlib
import functools
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    # result type
    "GuardResult",
    # bounded, symlink-safe readers
    "read_managed_json",
    "read_managed_text",
    "read_state",
    "state_path_for",
    # canonical contract hashing
    "canonical_contract",
    "sha256_canonical_contract",
    # status parsing + legality
    "UnreadableArtifact",
    "read_md_status",
    "assert_status_legal",
    "validate_run_id",
    # retry caps
    "DEFAULTS",
]

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"
'''

RESULT_TYPE = '''

# ── result type ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GuardResult:
    """The outcome of one read-only guard.

    `ok` and `reason` cannot disagree: `__post_init__` raises when they do. That
    matters because the pre-existing convention in `loop-engine.py` was "None on
    success, a non-empty string on failure", so an adapter written `if
    result.reason:` would read an `ok=False, reason=None` result — the natural
    output of a containment bug or a missed branch — as success. Adapters branch on
    `ok`.

    `ValueError`, not `assert`: `-O` / `PYTHONOPTIMIZE` strips assertions, and this
    is the invariant the no-silent-success guarantee rests on.
    """

    ok: bool
    reason: str | None = None
    message: str | None = None
    data: dict | None = None

    def __post_init__(self):
        if self.ok != (self.reason is None):
            raise ValueError(
                "GuardResult invariant violated: ok must be True exactly when "
                f"reason is None (ok={self.ok!r}, reason={self.reason!r})"
            )


# Marker prefix distinguishing a crash-refusal from a policy refusal. An operator
# reading `internal-error:` knows the guard could not decide, rather than that it
# decided against them.
INTERNAL_ERROR = "internal-error"

_MAX_REASON_CHARS = 400


def _one_line(text: str) -> str:
    """Collapse whitespace and cap length. Reasons are a one-line CLI contract."""
    collapsed = " ".join(str(text).split())
    if len(collapsed) > _MAX_REASON_CHARS:
        collapsed = collapsed[: _MAX_REASON_CHARS - 1] + "\\u2026"
    return collapsed


def contained(fn):
    """Turn any escaping `Exception` into a refusal.

    This restores what the child-process boundary used to provide for free: its exit
    code converted every unexpected exception into a refusal, so nothing reached the
    caller as a traceback. In-process there is no such boundary, and an
    `OverflowError` from `int(float("inf"))` on a malformed retry cap would surface
    out of a process holding the engine-state lock.

    `Exception` only. `BaseException` — `KeyboardInterrupt`, `SystemExit` — passes
    through untouched. Lock-integrity exceptions need no clause here: this module
    never acquires a lock, so `_statelock`'s `StateLockLost` cannot originate inside
    a contained call; `loop-cohort.with_state_lock`'s own handler remains its only
    one. Naming the class would force this layer to import the lock module, which
    its import allowlist forbids.

    The reason never carries raw artifact content — only an exception type and a
    message — because a refusal is printed to a stderr the agent captures.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — the containment boundary itself
            return GuardResult(
                ok=False,
                reason=_one_line(f"{INTERNAL_ERROR}: {type(exc).__name__}: {exc}"),
            )

    return wrapper
'''

FOOTER = '''

# Last statement in the file, on purpose. A module truncated at a clean statement
# boundary — an interrupted `make build-self`, a half-finished checkout — loads
# WITHOUT raising and returns a handle missing everything after the cut. The
# loaders require this to be truthy and `set(__all__) <= set(dir(module))`, so a
# truncation anywhere above becomes a load failure rather than a live handle
# serving a half-configured guard. Detects accidental truncation only; tampering is
# the accepted write-access residual documented in the spec.
_MODULE_COMPLETE = True
'''


def main() -> int:
    if DEST.exists():
        print(f"refusing: {DEST} already exists", file=sys.stderr)
        return 1
    text = SRC.read_text(encoding="utf-8")
    parts = [HEADER.rstrip("\n"), RESULT_TYPE.rstrip("\n")]
    for start, end, label in BLOCKS:
        body = slice_block(text, start, end, label)
        parts.append("\n\n# ── " + label + " " + "─" * max(0, 68 - len(label)) + "\n\n" + body)
        print(f"  sliced {label:34} {len(body.splitlines()):4} lines")
    parts.append(FOOTER.rstrip("\n"))
    DEST.write_text("\n".join(parts) + "\n", encoding="utf-8")
    written = len(DEST.read_text(encoding="utf-8").splitlines())
    print(f"\nwrote {DEST.relative_to(REPO)} ({written} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
