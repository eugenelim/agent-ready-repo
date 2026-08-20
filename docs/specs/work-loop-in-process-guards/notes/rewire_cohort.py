#!/usr/bin/env python3
"""One-shot: rewire `loop-cohort.py` onto `_loop_guards.py`.

Removes the relocated definitions and re-binds every one of their names at module
level, so no call site in the file changes — which is what keeps the six mutation
verbs, `test_loop_cohort.py`, and `test_loop_cohort_max_iter_single_source.py`
working untouched.

Same anchor discipline as the extractor: every block is matched exactly once and
the script fails loudly rather than cutting the wrong range.
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
COHORT = REPO / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"

# (start_anchor, end_anchor_exclusive) — the definitions now living in _loop_guards.
REMOVE = [
    ("_MAX_MANAGED_JSON_BYTES = ", "CLEAN_SUBSTRING = "),
    ("def _template_max_implementation_retries(", "def stop("),
    ("def state_path_for(", "def write_state_atomic("),
    ("_lint_module: object | None = None", "# The approved baseline pins"),
    ("_STATUS_PLACEHOLDER = ", "# ── run_id / schema_version validation"),
    ("def _validate_run_id(", "# ── scheduler"),
    ("class UnreadableArtifact(", '@_locked("approve-plan")'),
]

LOADER = '''
# ── shared read-only guard API ─────────────────────────────────────────────
#
# The guard decisions, the bounded readers, the canonical-contract hashing and the
# status parser loader all live in `_loop_guards.py` now, so `loop-engine.py` can
# call them in-process instead of starting an interpreter per guard. This file keeps
# its CLI surface and delegates the deciding.


class GuardsUnavailable(RuntimeError):
    """`_loop_guards.py` could not be loaded; every verb must refuse."""


_guards_module: object | None = None
_guards_error: str | None = None

# The symbols a load must provide. Checked against the loaded module rather than
# trusted, because a file truncated at a clean statement boundary loads WITHOUT
# raising and would otherwise hand back a half-configured guard.
_GUARDS_REQUIRED = (
    "GuardResult", "read_managed_json", "read_managed_text", "read_state",
    "state_path_for", "canonical_contract", "sha256_canonical_contract",
    "UnreadableArtifact", "read_md_status", "assert_status_legal",
    "validate_run_id", "DEFAULTS",
)


def load_guards():
    """Load the sibling `_loop_guards.py` by path, once per process.

    ── This function body is duplicated verbatim in `loop-engine.py` and
    ── `check-spec-status.py`. That is a decision, not an accident: the loader cannot
    ── live in the module it loads, and importing this 1800-line argparse CLI from
    ── `check-spec-status.py` just to borrow it is the coupling the whole change
    ── exists to avoid. A normalized-source-comparison test keeps the three copies
    ── from drifting.
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
    missing = [n for n in _GUARDS_REQUIRED if not hasattr(module, n)]
    if missing:
        raise GuardsUnavailable(
            f"cannot load {path}: incomplete module, missing {missing}. Restore the "
            "file or re-run `make build-self`."
        )
    _guards_module = module
    return _guards_module


def _guards_unavailable(*_args, **_kwargs):
    """Bound in place of every relocated callable when the load fails.

    RAISES rather than returning a reason. A stub that returned one would let a verb
    which skipped the sentinel check keep going and write that string where a digest
    belongs — `cmd_approve_plan` would store it as `approved_spec_hash`, and a later
    drift comparison between two stub-produced values would compare *equal* and pass
    vacuously. Raising when called is safe; only *import* must not raise.
    """
    raise GuardsUnavailable(_guards_error or "_loop_guards.py is unavailable")


try:
    _g = load_guards()
except GuardsUnavailable as exc:
    # Import must not raise: `test_loop_cohort_max_iter_single_source.py` reads
    # `mod.DEFAULTS` straight after `exec_module` with no verb invoked, so the
    # re-binds below have to execute. `main()` checks the sentinel at its single
    # dispatch chokepoint and refuses before any verb body runs.
    _g = None
    _guards_error = str(exc)
    GuardResult = None
    DEFAULTS = {}
    read_managed_json = read_managed_text = _guards_unavailable
    read_state = state_path_for = _guards_unavailable
    canonical_contract = sha256_canonical_contract = _guards_unavailable
    read_md_status = assert_status_legal = validate_run_id = _guards_unavailable
    _template_max_implementation_retries = _template_max_review_retries = _guards_unavailable
    _sha256_bytes = _lint_spec_status = _guards_unavailable
    UnreadableArtifact = GuardsUnavailable
    _MAX_MANAGED_JSON_BYTES = 8 * 1024 * 1024
    _STATUS_PLACEHOLDER = "<loop-cohort:status>"
    _BOTH_CAUSES = ""
    _LEGAL_AFTER_APPROVAL = {}
else:
    # Re-bound at module level so no call site in this file changes, and so the
    # existing tests that reach for these attributes keep working.
    GuardResult = _g.GuardResult
    DEFAULTS = _g.DEFAULTS
    read_managed_json = _read_managed_json = _g.read_managed_json
    read_managed_text = _g.read_managed_text
    read_state = _g.read_state
    state_path_for = _g.state_path_for
    canonical_contract = _g.canonical_contract
    sha256_canonical_contract = _g.sha256_canonical_contract
    read_md_status = _read_md_status = _g.read_md_status
    assert_status_legal = _g.assert_status_legal
    validate_run_id = _g.validate_run_id
    UnreadableArtifact = _g.UnreadableArtifact
    _sha256_bytes = _g._sha256_bytes
    _lint_spec_status = _g._lint_spec_status
    _template_max_implementation_retries = _g._template_max_implementation_retries
    _template_max_review_retries = _g._template_max_review_retries
    _MAX_MANAGED_JSON_BYTES = _g._MAX_MANAGED_JSON_BYTES
    _STATUS_PLACEHOLDER = _g._STATUS_PLACEHOLDER
    _BOTH_CAUSES = _g._BOTH_CAUSES
    _LEGAL_AFTER_APPROVAL = _g._LEGAL_AFTER_APPROVAL


def _validate_run_id(state: dict, expect_run_id: str, *, verb: str) -> int | None:
    """CLI adapter: map the shared helper's reason to this tool's `stop()` contract.

    Kept at this signature deliberately. Six mutation verbs call it, and rewriting
    those call sites is outside this change — the `Ask first` rail covers a mutation
    verb's body and accepted arguments, and refactoring a helper they share without
    touching any of them sits outside it.
    """
    reason = validate_run_id(state, expect_run_id, verb=verb)
    return None if reason is None else stop(reason)


def _assert_status_legal(verb: str, *paths: Path) -> int | None:
    """CLI adapter: map the shared helper's reason to this tool's `stop()` contract."""
    reason = assert_status_legal(verb, *paths)
    return None if reason is None else stop(reason)

'''


def cut(text: str, start: str, end: str) -> str:
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith(start)]
    if len(starts) != 1:
        raise SystemExit(f"start {start!r} matched {len(starts)} lines")
    a = starts[0]
    ends = [i for i, ln in enumerate(lines) if ln.startswith(end) and i > a]
    if not ends:
        raise SystemExit(f"end {end!r} never follows {start!r}")
    b = ends[0]
    print(f"  removed {b - a:4} lines at {a + 1}: {start[:46]}")
    return "\n".join(lines[:a] + lines[b:])


def main() -> int:
    text = COHORT.read_text(encoding="utf-8")
    if "load_guards" in text:
        print("refusing: already rewired", file=sys.stderr)
        return 1
    for start, end in REMOVE:
        text = cut(text, start, end)
    # Insert the loader where the removed hashing helpers used to sit, after the
    # state-lock section, so `SCRIPT_DIR` / `stop` / `_locked` are already defined.
    anchor = "# ── hashing helpers ───────────────────────────────────────────────────────"
    if text.count(anchor) != 1:
        raise SystemExit("hashing-helpers anchor not found exactly once")
    text = text.replace(anchor, LOADER.strip("\n"))
    COHORT.write_text(text, encoding="utf-8")
    print(f"\nloop-cohort.py is now {len(text.splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
