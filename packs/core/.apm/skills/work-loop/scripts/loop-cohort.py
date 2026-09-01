#!/usr/bin/env python3
"""loop-cohort — work-loop execution-state owner (Phase 1).

Single tool the work-loop skill calls for every deterministic state mutation:
phase termination checks, plan approval, review-finding fingerprints, and wave
scheduling. Phase-1 parallel verbs (worktree, dispatch-decision, auto-parallel)
are disabled — they exit non-zero without touching state.json.

Cross-platform: Python 3 stdlib only, `subprocess` for git, `os.replace` for
atomic writes, `pathlib` for paths. No shell, no bash, no PATH dependency.

Verb surface
------------
    loop-cohort init <spec-dir> --run-id <uuid>
    loop-cohort identity <spec-dir> [--expect-run-id <uuid>] [--json]
    loop-cohort check <spec-dir> --phase {implement,review,gates-failed}
    loop-cohort approve-plan <spec-dir> --expect-run-id <uuid>
    loop-cohort plan check-current <spec-dir> [--require-schedule]
    loop-cohort schedule <spec-dir> --expect-run-id <uuid>
    loop-cohort schedule check-current <spec-dir>
    loop-cohort record-attempt <spec-dir> --phase implement
                               --cycle-id <run_id>:<seq> --expect-run-id <uuid>
    loop-cohort wave check <spec-dir> --expect {more,last} [--wave-index <n>]
    loop-cohort wave advance <spec-dir> --from-index <n> --expect-run-id <uuid>
    loop-cohort review classify --report <path> [--json]
    loop-cohort review raw-classify --report <path> [--json]
    loop-cohort review inspect <spec-dir> --report <path> [--adjudication] [--json]
    loop-cohort review record <spec-dir> (--direct-clean-file <raw-report-path>
                               | --structural-clean-file <raw-report-path>
                               | --report <adjudication-report-path> --adjudication
                               | --fingerprint <hex> ...) --expect-run-id <uuid>
    loop-cohort status <spec-dir> [--json]
    loop-cohort reset <spec-dir>
    loop-cohort worktree ...        (disabled in Phase 1 — exits non-zero)
    loop-cohort dispatch-decision   (disabled in Phase 1 — exits non-zero)
    loop-cohort auto-parallel ...   (disabled in Phase 1 — exits non-zero)

Exit contract: 0 on success; non-zero with a one-line reason on stderr.

Schema reference: ../assets/state.json and ../references/state-schema.md.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import fnmatch
import functools
import glob as _glob
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"

PHASES = ("implement", "review", "gates-failed")
WORKTREE_STATUSES = ("ready", "blocked", "failed")
CLEAN_SUBSTRING = "Clean — ready to commit."
INDETERMINATE_SENTINEL = "ADJUDICATION-INDETERMINATE"
# Specialist reviewers (experience-reviewer, frontend-reviewer) emit "SHIP IT"
# on its own line as their clean verdict instead of CLEAN_SUBSTRING.
_SHIP_IT_RE = re.compile(r"^SHIP IT\s*$", re.MULTILINE)
# Fingerprints are SHA-256 (64 hex). The 40-hex SHA-1 form is still accepted
# so a cohort that was mid-review when core upgraded can finish: its
# state.json holds SHA-1 values and `review record --fingerprint` would
# otherwise hard-reject them. Stasis detection compares sets computed by the
# same binary, so a straddling run misses a match for exactly one round and
# self-heals on the next. Drop the 40-hex alternative once no in-flight
# cohort predates core 2.3.0.
_RE_FINGERPRINT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


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
    print(f"loop-cohort: stop — {_diag(reason)}", file=sys.stderr)
    return code


def _disabled(verb: str) -> int:
    return stop(f"{verb} is disabled in Phase 1")


def _emit(message: str | None) -> None:
    """Print a guard's success message under THIS tool's prefix.

    The prefix belongs to the adapter, not to the guard layer: the layer is shared by
    `loop-cohort`, `loop-engine` and `check-spec-status`, so a prefix baked into a
    `message` is wrong for two of the three callers — and when it was, the adapter's
    own prefix doubled it (`check-spec-status: check-spec-status: ...`), which the
    pre-change golden capture caught. Empty message means nothing to say.
    """
    if message:
        print(f"loop-cohort: {_diag(message)}")


# Matches `loop-engine.py`'s SUBPROCESS_TIMEOUT_S. Not derived from it — these are
# separate scripts with no shared module — but deliberately the same number, so the
# two files do not drift into disagreeing about how long a local git call may take.
GIT_TIMEOUT_S = 20.0

# Environment variables that could redirect git to a foreign repo root.
_GIT_OVERRIDE_VARS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
})


def _get_repo_root() -> Path:
    """Return the repository root without caller-controlled Git overrides."""
    safe_env = {k: v for k, v in os.environ.items() if k not in _GIT_OVERRIDE_VARS}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", check=False,
            env=safe_env, timeout=GIT_TIMEOUT_S,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"could not determine repo root: {exc}") from exc
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("could not determine repo root (git rev-parse --show-toplevel failed)")
    return Path(result.stdout.strip()).resolve()


def _resolve_spec_dir(raw: str) -> Path:
    """Resolve and confine <spec-dir> to the current repository."""
    parts = Path(raw).parts
    if ".." in parts:
        raise ValueError(f"spec-dir must not contain '..': {raw!r}")
    resolved = Path(raw).resolve()
    try:
        repo_root = _get_repo_root()
    except ValueError as exc:
        raise ValueError(f"spec-dir confinement check failed: {exc}") from exc
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(
            f"spec-dir must be inside the repository ({repo_root}): {raw!r}"
        ) from exc
    return resolved


def write_state_atomic(spec_dir: Path, state: dict) -> None:
    path = state_path_for(spec_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".state-", suffix=".json.tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh, indent=2)
            fh.write("\n")
        Path(tmp).replace(path)
    except Exception:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


# ── state lock ────────────────────────────────────────────────────────────

# `write_state_atomic` makes each *write* atomic, but the read-modify-write
# around it is not: two concurrent verbs each load a snapshot, both decide from
# it, and the second replace drops the first's update — silently, with both
# callers exiting 0. Reproduced at 20/20 trials; see
# docs/specs/loop-cohort-state-lock/notes/reproduction.md.
#
# `_statelock.py` is a work-loop script owned by this skill (ADR-0074):
# stdlib-only, so it works where `agentbundle` is not installed. `agentbundle`
# has its own, separate lock for the installer's state.toml.
_statelock_module: object | None = None


def _statelock():
    """Load the sibling `_statelock.py`.

    Loaded by path rather than `import _statelock`, matching
    `_lint_spec_status()` above: a plain import resolves under file-path
    invocation but not under an importlib-based harness, which does not put this
    directory on `sys.path` — and the concurrency suites are exactly that.
    """
    global _statelock_module
    if _statelock_module is None:
        lock_path = SCRIPT_DIR / "_statelock.py"
        # See the twin in `loop-engine.py`: bytecode writing is disabled across
        # the load and restored to its PRIOR value, so a stale or poisoned
        # `__pycache__` entry for the lock module cannot be executed here.
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec = importlib.util.spec_from_file_location("_statelock", str(lock_path))
            if spec is None or spec.loader is None:
                raise ImportError(f"loop-cohort: cannot load {lock_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
        _statelock_module = module
    return _statelock_module


def with_state_lock(spec_dir: Path, verb: str, body):
    """Run *body* holding the state lock for *spec_dir*; map failures to stop().

    The lock opens *before* the body's `read_state()` and closes *after* its
    `write_state_atomic()`, so the decision is made against state that cannot
    change underneath it. Guarding only read→write would leave every defect
    intact: both contenders would still evaluate their run-id, idempotency and
    retry-cap checks against the same superseded snapshot.

    Every lock failure becomes a `stop()` refusal — non-zero, one line, no
    traceback, nothing written. A verb never proceeds unlocked. `StateLockLost`
    is caught by the same clause (it shares the base) but says something
    different: the mutation ran, and a reclaim may have overwritten it, so
    exiting 0 would be a lie.
    """
    try:
        sl = _statelock()
    except (ImportError, OSError) as exc:
        # A missing or unloadable projection must refuse, not traceback. In an
        # adopter tree this is the realistic shape, and proceeding unlocked would
        # be the fail-open this lock exists to prevent.
        return stop(f"{verb}: state lock unavailable: {exc}")
    try:
        with sl.exclusive(state_path_for(spec_dir)):
            return body()
    except sl.StateLockError as exc:
        return stop(f"{verb}: {exc}")


def _locked(verb: str):
    """Decorator form of `with_state_lock` for verbs that take `args.spec_dir`."""
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(args: argparse.Namespace) -> int:
            try:
                spec_dir = _resolve_spec_dir(args.spec_dir)
            except ValueError as exc:
                return stop(str(exc))
            return with_state_lock(spec_dir, verb, lambda: fn(args))
        return wrapper
    return decorate


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command, bounded.

    `timeout=` is not currently load-bearing: this helper has no callers (verified
    repo-wide), and it is unreachable while the ENGINE holds its lock, so it sits
    outside that budget's arithmetic. It is bounded anyway because it is the nearest
    copy-paste hazard to the guard extraction site — an unbounded `subprocess.run`
    that a future caller inherits is how a lock-holding process learns to hang.

    `TimeoutExpired` is left to propagate. Every current entry point is a CLI verb
    that already turns an exception into a non-zero exit; swallowing it here would
    invent a "git timed out so we continued" path that no caller asked for.
    """
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_S,
    )


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


def load_guards():
    """Load the sibling `_loop_guards.py` by path, once per process.

    ── This function body is identical in all three of `loop-cohort.py`,
    ── `loop-engine.py` and `check-spec-status.py`. That is a decision, not an
    ── accident: the loader cannot live in the module it loads, and importing this
    ── 1500-line argparse CLI from `check-spec-status.py` just to borrow it is the
    ── coupling the whole change exists to avoid.
    ── `test_loader_copies_are_structurally_identical` compares the three ASTs and
    ── keeps them from drifting.
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
    non_negative_int = _guards_unavailable
    _lint_spec_status = _guards_unavailable
    UnreadableArtifact = GuardsUnavailable
    _BOTH_CAUSES = ""
else:
    # Re-bound at module level so no call site in this file changes, and so the
    # existing tests that reach for these attributes keep working.
    GuardResult = _g.GuardResult
    DEFAULTS = _g.DEFAULTS
    non_negative_int = _g.non_negative_int
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
    _lint_spec_status = _g._lint_spec_status
    _template_max_implementation_retries = _g._template_max_implementation_retries
    _template_max_review_retries = _g._template_max_review_retries
    _BOTH_CAUSES = _g._BOTH_CAUSES


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

# Lazy handle on the sibling lint-spec-status.py. Status and acceptance-criterion
# recognition has exactly one implementation in this repo — a shipped spec
# (docs/specs/loop-approved-spec-state, Constrained by ADR-0061) requires every
# status read to go through its `parse_status`, and a second copy of the AC
# regexes is how the two silently disagree about what an AC line is.
# The approved baseline pins the *scope a human approved*. It deliberately does
# not pin the two field families this skill mandates writing after approval —
# the preamble status token (SKILL.md: `Implementing` before code, `Shipped` at
# finish, plan `Done`) and progress checkboxes (every AC to `[x]`). Pinning
# those made `plan check-current` and `schedule check-current` fail by
# construction, one mandated step after `approve-plan`.
#
# Everything else stays pinned, including anything else on the status line: a
# `- **Status:** Implementing — scope now also covers X` still moves the digest.
# ── run_id / schema_version validation ───────────────────────────────────


# ── scheduler (wave-scheduled supervisor mode) ────────────────────────────
#
# Pure functions over a plan's `Depends on:` graph. Sequential by default.

# Accepts both '## T<n>' (level-2) and '### T<n>' (level-3) headings for
# backward compatibility with existing plans that predate the Phase-1 spec.
TASK_HEADING_RE = re.compile(r"^#{2,3}\s+(T\d+[a-z]?)\b", re.MULTILINE)
DEPENDS_LINE_RE = re.compile(r"^\*\*Depends on:\*\*\s*(.+)$", re.MULTILINE)
TOUCHES_LINE_RE = re.compile(r"^\*\*Touches:\*\*\s*(.+)$", re.MULTILINE)
_RANGE_RE = re.compile(r"(T\d+)\s*-\s*(T\d+)")
_TASK_ID_RE = re.compile(r"T\d+[a-z]?")
_CROSS_MARKER_RE = re.compile(r"spec:([A-Za-z0-9._-]+)/(T\d+[a-z]?)")
_CROSS_LEGACY_RE = re.compile(r"`(?!T\d+[a-z]?`)([A-Za-z0-9._-]+)`\s*(T\d+[a-z]?)")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_AMENDMENT_HISTORY = 20
MAX_AMENDMENT_REF_LENGTH = 1000
MAX_AMENDMENT_EVIDENCE_REFS = 64
MAX_AMENDMENT_STATE_BYTES = 1024 * 1024


def parse_depends_on(field: str, local_task_ids):
    """Parse a 'Depends on:' field value into local task IDs and cross-spec markers."""
    head = field.split("(")[0]
    cross = _CROSS_MARKER_RE.findall(head) + _CROSS_LEGACY_RE.findall(head)
    cleaned = _CROSS_MARKER_RE.sub("", head)
    cleaned = _CROSS_LEGACY_RE.sub("", cleaned)
    if not cleaned.strip() or re.fullmatch(r"\s*none\s*", cleaned, re.IGNORECASE):
        return set(), cross
    ids: set[str] = set()
    for lo, hi in _RANGE_RE.findall(cleaned):
        ids.update(f"T{i}" for i in range(int(lo[1:]), int(hi[1:]) + 1))
    ids.update(_TASK_ID_RE.findall(cleaned))
    return {t for t in ids if t in local_task_ids}, cross


def parse_plan(text: str):
    """Extract ordered task IDs and dependency map from plan.md text."""
    matches = list(TASK_HEADING_RE.finditer(text))
    ordered = [m.group(1) for m in matches]
    taskset = set(ordered)
    deps: dict[str, set] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        dm = DEPENDS_LINE_RE.search(text[m.end():end])
        local, _ = parse_depends_on(dm.group(1), taskset) if dm else (set(), [])
        deps[m.group(1)] = local
    return ordered, deps


def _task_sections(text: str) -> dict[str, str]:
    """Return exact authored task sections keyed by unique task ID."""
    matches = list(TASK_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        task_id = match.group(1)
        if task_id in sections:
            raise ValueError(f"duplicate task section {task_id}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[match.start():end].replace("\r\n", "\n").replace("\r", "\n")
        canonical = "\n".join(line.rstrip() for line in raw.split("\n")).rstrip() + "\n"
        sections[task_id] = canonical
    return sections


def task_section_hashes(text: str, task_ids: set[str]) -> dict[str, str]:
    """Fingerprint completed task sections without normalising authored content."""
    sections = _task_sections(text)
    missing = sorted(task_ids - sections.keys())
    if missing:
        raise ValueError(f"completed task section missing: {', '.join(missing)}")
    return {
        task_id: hashlib.sha256(sections[task_id].encode("utf-8")).hexdigest()
        for task_id in sorted(task_ids)
    }


def validate_completed_task_sections(plan_text: str, state: dict) -> str | None:
    """Return a stable refusal when an amended plan rewrites completed work."""
    completed = state.get("completed_task_ids", [])
    pins = state.get("completed_task_section_hashes", {})
    if not completed and not pins:
        return None
    if not isinstance(completed, list) or any(not isinstance(item, str) for item in completed):
        return "completed_task_ids must be a list of task IDs"
    if not isinstance(pins, dict) or set(pins) != set(completed):
        return "completed task section pins do not match completed_task_ids"
    try:
        current = task_section_hashes(plan_text, set(completed))
    except ValueError as exc:
        return str(exc)
    changed = [task_id for task_id in completed if current.get(task_id) != pins.get(task_id)]
    if changed:
        return f"completed task section changed: {', '.join(changed)}"
    return None


def schedule_unfinished_plan(plan_text: str, state: dict) -> list[list[str]]:
    """Schedule only unfinished tasks while treating completed dependencies as met."""
    pin_error = validate_completed_task_sections(plan_text, state)
    if pin_error is not None:
        raise ValueError(pin_error)
    ordered, dependencies = parse_plan(plan_text)
    completed = set(state.get("completed_task_ids", []))
    remaining = [task_id for task_id in ordered if task_id not in completed]
    if not remaining:
        raise ValueError("amended plan has no unfinished task sections")
    remaining_set = set(remaining)
    remaining_dependencies = {
        task_id: dependencies.get(task_id, set()) & remaining_set
        for task_id in remaining
    }
    cycles = detect_cycles(remaining, remaining_dependencies)
    if cycles:
        raise ValueError(
            "dependency cycle among unfinished tasks: " + ", ".join(cycles)
        )
    waves, _ = topological_waves(remaining, remaining_dependencies)
    return waves


def _bounded_amendment_ref(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    if len(value) > MAX_AMENDMENT_REF_LENGTH:
        raise ValueError(f"{name} exceeds {MAX_AMENDMENT_REF_LENGTH} characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{name} contains a control character")
    return value


def parse_completed_task_evidence_entries(
    entries: tuple[str, ...], allowed_task_ids: set[str] | None = None
) -> dict[str, list[str]]:
    """Parse repeated `Tn=<stable-ref>` arguments into an auditable task map."""
    if len(entries) > MAX_AMENDMENT_EVIDENCE_REFS:
        raise ValueError(
            f"completed_evidence_ref count exceeds {MAX_AMENDMENT_EVIDENCE_REFS}"
        )
    result: dict[str, list[str]] = {}
    for entry in entries:
        if not isinstance(entry, str) or "=" not in entry:
            raise ValueError("completed_evidence_ref must use Tn=<stable-ref>")
        task_id, raw_ref = entry.split("=", 1)
        if not _TASK_ID_RE.fullmatch(task_id):
            raise ValueError(
                f"completed_evidence_ref has invalid task ID {task_id!r}"
            )
        if allowed_task_ids is not None and task_id not in allowed_task_ids:
            raise ValueError(
                f"completed_evidence_ref names non-completed task {task_id}"
            )
        reference = _bounded_amendment_ref("completed_evidence_ref", raw_ref)
        bucket = result.setdefault(task_id, [])
        if reference not in bucket:
            bucket.append(reference)
    return result


def _normalize_completed_task_evidence_map(
    mapping: dict[str, list[str]], allowed_task_ids: set[str]
) -> dict[str, list[str]]:
    if not isinstance(mapping, dict):
        raise ValueError("completed_task_evidence must be a mapping")
    entries: list[str] = []
    for task_id, references in mapping.items():
        if not isinstance(task_id, str):
            raise ValueError("completed_task_evidence task ID must be a string")
        if not isinstance(references, list) or not references:
            raise ValueError(
                f"completed_task_evidence[{task_id!r}] must be a non-empty list"
            )
        for reference in references:
            if not isinstance(reference, str):
                raise ValueError(
                    f"completed_task_evidence[{task_id!r}] reference must be a string"
                )
            entries.append(f"{task_id}={reference}")
    return parse_completed_task_evidence_entries(tuple(entries), allowed_task_ids)


def begin_contract_amendment(
    state: dict,
    *,
    expected_run_id: str,
    owner_authority_ref: str,
    reason_ref: str,
    completed_task_section_hashes: dict[str, str],
    completed_task_evidence: dict[str, list[str]],
    amendment_id: str,
) -> dict:
    """Return the cohort snapshot for one authorized, replay-safe amendment."""
    if state.get("schema_version") != 1:
        raise ValueError("contract-amendment requires schema_version=1")
    if state.get("run_id") != expected_run_id:
        raise ValueError("contract-amendment run_id mismatch")
    owner_authority_ref = _bounded_amendment_ref(
        "owner_authority_ref", owner_authority_ref
    )
    reason_ref = _bounded_amendment_ref("reason_ref", reason_ref)
    amendment_id = _bounded_amendment_ref("amendment_id", amendment_id)
    history = state.get("amendment_history", [])
    if not isinstance(history, list):
        raise ValueError("amendment_history must be a list")
    if history and history[-1].get("amendment_id") == amendment_id:
        snapshot = history[-1]
        stored_completed = state.get("completed_task_ids", [])
        if not isinstance(stored_completed, list):
            raise ValueError("completed_task_ids must be a list")
        incoming_evidence = _normalize_completed_task_evidence_map(
            completed_task_evidence, set(stored_completed)
        )
        snapshot_matches = (
            snapshot.get("amendment_id") == amendment_id
            and snapshot.get("owner_authority_ref") == owner_authority_ref
            and snapshot.get("reason_ref") == reason_ref
            and stored_completed == snapshot.get("completed_task_ids")
            and state.get("completed_task_section_hashes")
            == snapshot.get("completed_task_section_hashes")
            and state.get("completed_task_evidence")
            == snapshot.get("completed_task_evidence")
        )
        expected_pending = {
            "amendment_id": amendment_id,
            "owner_authority_ref": owner_authority_ref,
            "reason_ref": reason_ref,
            "completed_task_evidence": incoming_evidence,
        }
        if (
            snapshot_matches
            and state.get("plan_review_status") == "pending"
            and state.get("schedule_waves") == []
            and state.get("amendment_pending") == expected_pending
        ):
            return copy.deepcopy(state)
        raise ValueError("contract-amendment replay facts do not match stored state")
    if len(history) >= MAX_AMENDMENT_HISTORY:
        raise ValueError("contract-amendment history limit reached; retain and restart")
    if state.get("plan_review_status") != "approved":
        raise ValueError("contract-amendment requires an approved plan baseline")
    for field in ("approved_spec_hash", "approved_plan_hash", "plan_hash"):
        if not _SHA256_RE.fullmatch(str(state.get(field, ""))):
            raise ValueError(f"contract-amendment requires a pinned {field}")

    waves = state.get("schedule_waves", [])
    current_index = state.get("current_wave_index", 0)
    if (
        not isinstance(waves, list)
        or isinstance(current_index, bool)
        or not isinstance(current_index, int)
        or not 0 <= current_index < len(waves)
    ):
        raise ValueError("contract-amendment requires a current scheduled wave")
    prior_completed = state.get("completed_task_ids", [])
    if not isinstance(prior_completed, list):
        raise ValueError("completed_task_ids must be a list")
    newly_completed = [task for wave in waves[:current_index] for task in wave]
    completed = list(dict.fromkeys([*prior_completed, *newly_completed]))
    if set(completed_task_section_hashes) != set(completed):
        raise ValueError("completed task section hashes do not match completed task IDs")
    if any(
        not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest)
        for digest in completed_task_section_hashes.values()
    ):
        raise ValueError("completed task section hash must be SHA-256")

    incoming_evidence = _normalize_completed_task_evidence_map(
        completed_task_evidence, set(completed)
    )
    previous_evidence_raw = state.get("completed_task_evidence", {})
    if previous_evidence_raw:
        previous_evidence = _normalize_completed_task_evidence_map(
            previous_evidence_raw, set(prior_completed)
        )
    else:
        previous_evidence = {}
    all_evidence = copy.deepcopy(previous_evidence)
    for task_id, references in incoming_evidence.items():
        bucket = all_evidence.setdefault(task_id, [])
        for reference in references:
            if reference not in bucket:
                bucket.append(reference)
    missing_evidence = sorted(set(completed) - set(all_evidence))
    if missing_evidence:
        raise ValueError(
            "completed task has no evidence binding: " + ", ".join(missing_evidence)
        )
    evidence_count = sum(len(references) for references in all_evidence.values())
    if evidence_count > MAX_AMENDMENT_EVIDENCE_REFS:
        raise ValueError(
            f"aggregate completed evidence exceeds {MAX_AMENDMENT_EVIDENCE_REFS} refs"
        )
    snapshot = {
        "amendment_id": amendment_id,
        "owner_authority_ref": owner_authority_ref,
        "reason_ref": reason_ref,
        "approved_spec_hash": state["approved_spec_hash"],
        "approved_plan_hash": state["approved_plan_hash"],
        "plan_hash": state["plan_hash"],
        "schedule_waves": copy.deepcopy(waves),
        "current_wave_index": current_index,
        "completed_task_ids": completed,
        "completed_task_section_hashes": dict(completed_task_section_hashes),
        "completed_task_evidence": all_evidence,
    }
    amended = copy.deepcopy(state)
    amended.update(
        {
            "plan_review_status": "pending",
            "approved_spec_hash": None,
            "approved_plan_hash": None,
            "plan_hash": None,
            "schedule_waves": [],
            "current_wave_index": 0,
            "completed_task_ids": completed,
            "completed_task_section_hashes": dict(completed_task_section_hashes),
            "completed_task_evidence": all_evidence,
            "amendment_history": [*history, snapshot],
            "amendment_pending": {
                "amendment_id": amendment_id,
                "owner_authority_ref": owner_authority_ref,
                "reason_ref": reason_ref,
                "completed_task_evidence": incoming_evidence,
            },
        }
    )
    serialized_size = len(
        json.dumps(amended, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if serialized_size > MAX_AMENDMENT_STATE_BYTES:
        raise ValueError(
            "contract-amendment state exceeds "
            f"{MAX_AMENDMENT_STATE_BYTES}-byte aggregate limit"
        )
    return amended


def complete_contract_amendment_reapproval(state: dict) -> dict:
    """Clear only the replay marker after fresh plan approval is atomically pinned."""
    if state.get("plan_review_status") != "approved":
        raise ValueError("amendment replay marker clears only after plan approval")
    for field in ("approved_spec_hash", "approved_plan_hash"):
        if not _SHA256_RE.fullmatch(str(state.get(field, ""))):
            raise ValueError(f"amendment replay marker requires pinned {field}")
    approved = copy.deepcopy(state)
    approved["amendment_pending"] = None
    return approved


def apply_contract_amendment(
    spec_dir: Path,
    *,
    expected_run_id: str,
    owner_authority_ref: str,
    reason_ref: str,
    completed_task_evidence: dict[str, list[str]],
    amendment_id: str,
) -> dict:
    """Lock, derive completed-section pins, and persist one amendment snapshot."""
    sl = _statelock()
    with sl.exclusive(state_path_for(spec_dir)):
        state = read_state(spec_dir)
        waves = state.get("schedule_waves", [])
        current_index = state.get("current_wave_index", 0)
        prior = state.get("completed_task_ids", [])
        if not isinstance(waves, list) or not isinstance(current_index, int):
            raise ValueError("contract-amendment requires a current scheduled wave")
        newly_completed = [task for wave in waves[:current_index] for task in wave]
        completed = list(dict.fromkeys([*prior, *newly_completed]))
        history = state.get("amendment_history", [])
        if history and history[-1].get("amendment_id") == amendment_id:
            try:
                plan_text = read_managed_text(spec_dir / "plan.md", "plan.md")
            except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
                raise ValueError(
                    f"contract-amendment cannot read plan.md: {exc}"
                ) from exc
            pin_error = validate_completed_task_sections(plan_text, state)
            if pin_error is not None:
                raise ValueError(f"contract-amendment replay refused: {pin_error}")
            hashes = dict(state.get("completed_task_section_hashes", {}))
        else:
            try:
                plan_text = read_managed_text(spec_dir / "plan.md", "plan.md")
            except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
                raise ValueError(
                    f"contract-amendment cannot read plan.md: {exc}"
                ) from exc
            hashes = task_section_hashes(plan_text, set(completed))
        amended = begin_contract_amendment(
            state,
            expected_run_id=expected_run_id,
            owner_authority_ref=owner_authority_ref,
            reason_ref=reason_ref,
            completed_task_section_hashes=hashes,
            completed_task_evidence=completed_task_evidence,
            amendment_id=amendment_id,
        )
        if amended != state:
            write_state_atomic(spec_dir, amended)
        return amended


def contract_amendment_replay_status(
    spec_dir: Path,
    *,
    amendment_id: str,
    owner_authority_ref: str,
    reason_ref: str,
    completed_task_evidence: dict[str, list[str]],
) -> str:
    """Classify the cohort-first crash window without mutating state."""
    state = read_state(spec_dir)
    pending = state.get("amendment_pending")
    if pending is None:
        return "absent"
    expected = {
        "amendment_id": amendment_id,
        "owner_authority_ref": owner_authority_ref,
        "reason_ref": reason_ref,
        "completed_task_evidence": completed_task_evidence,
    }
    history = state.get("amendment_history", [])
    if not history or history[-1].get("amendment_id") != amendment_id:
        return "conflict"
    snapshot = history[-1]
    snapshot_matches = (
        snapshot.get("amendment_id") == amendment_id
        and snapshot.get("owner_authority_ref") == owner_authority_ref
        and snapshot.get("reason_ref") == reason_ref
        and state.get("completed_task_ids") == snapshot.get("completed_task_ids")
        and state.get("completed_task_section_hashes")
        == snapshot.get("completed_task_section_hashes")
        and state.get("completed_task_evidence")
        == snapshot.get("completed_task_evidence")
    )
    if not snapshot_matches or pending != expected:
        return "conflict"
    try:
        plan_text = read_managed_text(spec_dir / "plan.md", "plan.md")
    except (OSError, UnicodeDecodeError, ValueError, ImportError):
        return "conflict"
    if validate_completed_task_sections(plan_text, state) is not None:
        return "conflict"
    return "applied"


def parse_touches(field: str):
    head = field.split("(")[0]
    return {g.strip() for g in head.split(",") if g.strip()}


def parse_touches_by_task(text: str):
    matches = list(TASK_HEADING_RE.finditer(text))
    out: dict[str, set] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        tm = TOUCHES_LINE_RE.search(text[m.end():end])
        if tm:
            globs = parse_touches(tm.group(1))
            if globs:
                out[m.group(1)] = globs
    return out


def _is_literal_seg(seg: str) -> bool:
    return _glob.escape(seg) == seg


def _seg_provably_disjoint(x: str, y: str) -> bool:
    xl, yl = _is_literal_seg(x), _is_literal_seg(y)
    if xl and yl:
        return x != y
    if xl and not yl:
        return not fnmatch.fnmatch(x, y)
    if yl and not xl:
        return not fnmatch.fnmatch(y, x)
    return False


def globs_overlap(a: str, b: str) -> bool:
    if "**" in a or "**" in b:
        return True
    sa, sb = a.split("/"), b.split("/")
    if len(sa) != len(sb):
        return False
    return not any(_seg_provably_disjoint(x, y) for x, y in zip(sa, sb, strict=False))


def wave_touches_disjoint(per_task_globs) -> str:
    declared = [g for g in per_task_globs if g]
    for i in range(len(declared)):
        for j in range(i + 1, len(declared)):
            if any(globs_overlap(x, y) for x in declared[i] for y in declared[j]):
                return "no"
    if any(not g for g in per_task_globs):
        return "unknown"
    return "yes"


def build_dag(ordered, deps):
    taskset = set(ordered)
    indeg = dict.fromkeys(ordered, 0)
    children = defaultdict(list)
    for t in ordered:
        for d in deps.get(t, ()):
            if d in taskset:
                indeg[t] += 1
                children[d].append(t)
    return indeg, children


def topological_waves(ordered, deps):
    indeg, children = build_dag(ordered, deps)
    order = {t: i for i, t in enumerate(ordered)}
    work = dict(indeg)
    frontier = sorted([t for t in ordered if work[t] == 0], key=order.get)
    waves = []
    while frontier:
        waves.append(frontier)
        nxt = []
        for t in frontier:
            for c in children[t]:
                work[c] -= 1
                if work[c] == 0:
                    nxt.append(c)
        frontier = sorted(nxt, key=order.get)
    return waves, sum(len(w) for w in waves)


def detect_cycles(ordered, deps):
    """Return task IDs that form cycles (topological sort excludes them)."""
    waves, placed = topological_waves(ordered, deps)
    if placed == len(ordered):
        return []
    scheduled = {t for w in waves for t in w}
    return [t for t in ordered if t not in scheduled]


def detect_forward_refs(ordered, deps):
    """Return (task, dep) pairs where dep appears after task in the declared order."""
    order = {t: i for i, t in enumerate(ordered)}
    return [
        (t, d)
        for t in ordered
        for d in deps.get(t, ())
        if d in order and order[d] > order[t]
    ]


# ── auto-classification helpers (kept; dispatch-decision verb disabled) ───

SAFE_CATEGORIES = frozenset({"cannot-collide", "typed-group-b", "textual-loud"})

_DANGER_PATH_RE = re.compile(
    r"(^|/)(poetry\.lock|package-lock\.json|Cargo\.lock|go\.sum|uv\.lock"
    r"|yarn\.lock|requirements\.txt|pyproject\.toml|package\.json|__init__\.py"
    r"|index\.(ts|js|tsx|jsx|mjs|cjs)|mod\.rs|barrel\.\w+|registry\.\w+"
    r"|Makefile|marketplace\.json)$"
    r"|(^|/)migrations?/|(^|/)\.github/workflows/"
)


def classify_task(name_status) -> str:
    statuses = [row[0][0] for row in name_status]
    paths = [p for row in name_status for p in row[1:]]
    if any(s in ("R", "C", "D") for s in statuses):
        return "move-or-delete"
    if any(_DANGER_PATH_RE.search(p) for p in paths):
        return "danger-path"
    if statuses and all(s == "A" for s in statuses):
        return "cannot-collide"
    return "modified-existing"


def dispatch_decision(categories, *, merge_tree_clean):
    if not merge_tree_clean:
        return "serial"
    if any(c not in SAFE_CATEGORIES for c in categories):
        return "serial"
    return "parallel"


# ── init ──────────────────────────────────────────────────────────────────


@_locked("init")
def cmd_init(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    dest = state_path_for(spec_dir)
    if dest.exists():
        return stop(
            f"state.json already exists at {dest}; run 'loop-cohort reset' first"
        )
    if not TEMPLATE_PATH.exists():
        return stop(f"template missing at {TEMPLATE_PATH}")
    # Through the shared bounded reader, not a raw `read_text()`. `cmd_init` holds the
    # state lock, so an unbounded read here has the same shape as the ones this change
    # removed everywhere else: a replaced or oversized template would read without
    # limit inside the critical section, and a symlinked one would be followed.
    try:
        template = read_managed_json(TEMPLATE_PATH, "state.json template")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return stop(f"init: {exc}")
    template["run_id"] = args.run_id
    template["feature"] = Path(spec_dir).resolve().name
    write_state_atomic(spec_dir, template)
    print(f"loop-cohort: initialised {dest} (feature={template['feature']} run_id={args.run_id})")
    return 0


# ── identity ──────────────────────────────────────────────────────────────


def cmd_identity(args: argparse.Namespace) -> int:
    """CLI adapter over `check_identity`. Branches on `ok`, never on `reason`."""
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    result = _g.check_identity(spec_dir, expect_run_id=args.expect_run_id)
    if not result.ok:
        return stop(result.reason)
    if args.json:
        print(json.dumps(result.data))
    else:
        _emit(result.message)
    return 0


# ── status ────────────────────────────────────────────────────────────────


def cmd_status(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    if state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return stop(f"status: unsupported schema_version={sv!r} (expected 1)")
    result = {
        "schema_version": state.get("schema_version"),
        "run_id": state.get("run_id"),
        "plan_review_status": state.get("plan_review_status", "pending"),
        "approved_spec_hash": state.get("approved_spec_hash"),
        "approved_plan_hash": state.get("approved_plan_hash"),
        "plan_hash": state.get("plan_hash"),
        "schedule_waves": state.get("schedule_waves", []),
        "current_wave_index": state.get("current_wave_index", 0),
        "completed_task_ids": state.get("completed_task_ids", []),
        "completed_task_section_hashes": state.get(
            "completed_task_section_hashes", {}
        ),
        "completed_task_evidence": state.get("completed_task_evidence", {}),
        "amendment_history": state.get("amendment_history", []),
        "amendment_pending": state.get("amendment_pending"),
        "implementation_retry_count": state.get("implementation_retry_count", 0),
        "review_round_count": state.get("review_round_count", 0),
        "last_review_record_operation_id": state.get("last_review_record_operation_id"),
        "last_review_record_payload_digest": state.get("last_review_record_payload_digest"),
        "review_retry_count": state.get("review_retry_count", 0),
        "finding_fingerprints": state.get("finding_fingerprints", []),
        "previous_finding_fingerprints": state.get("previous_finding_fingerprints", []),
    }
    if args.json:
        print(json.dumps(result))
    else:
        print(f"loop-cohort status for {spec_dir.name}:")
        for k, v in result.items():
            print(f"  {k}: {v!r}")
    return 0


# ── reset ─────────────────────────────────────────────────────────────────


@_locked("reset")
def cmd_reset(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    path = state_path_for(spec_dir)
    if path.exists():
        path.unlink()
        print(f"loop-cohort: deleted {path}")
    else:
        print(f"loop-cohort: reset — state.json already absent at {path}")
    return 0


# ── approve-plan ──────────────────────────────────────────────────────────

@_locked("approve-plan")
def cmd_approve_plan(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="approve-plan")
    if err is not None:
        return err

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    if not spec_path.exists():
        return stop(f"approve-plan: spec.md not found at {spec_path}")
    if not plan_path.exists():
        return stop(f"approve-plan: plan.md not found at {plan_path}")

    if state.get("completed_task_ids") or state.get("completed_task_section_hashes"):
        try:
            plan_text_for_pins = read_managed_text(plan_path, "plan.md")
        except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
            return stop(f"approve-plan: cannot verify completed task sections: {exc}")
        pin_error = validate_completed_task_sections(plan_text_for_pins, state)
        if pin_error is not None:
            return stop(f"approve-plan: {pin_error}")

    # Idempotency: if already approved, verify hashes before writing.
    current_status = state.get("plan_review_status", "pending")
    if current_status == "approved":
        try:
            spec_hash = sha256_canonical_contract(spec_path)
            plan_hash = sha256_canonical_contract(plan_path)
        except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
            # ValueError is the bounded reader's failure vocabulary (oversized,
            # non-regular, symlinked, replaced mid-read). This verb holds the cohort
            # state lock and `with_state_lock` catches only StateLockError, while
            # `main()` catches only KeyboardInterrupt — so without this clause an
            # unsafe artifact is a traceback out of a lock-holding process.
            return stop(f"approve-plan: cannot read the approved artifacts: {exc}")
        stored_spec_hash = state.get("approved_spec_hash", "")
        stored_plan_hash = state.get("approved_plan_hash", "")
        if spec_hash == stored_spec_hash and plan_hash == stored_plan_hash:
            # The crash-window guard below sits on the pending branch only, so
            # without this a replay after a status regression reports a clean
            # no-op against a spec that no longer claims to be approved.
            err = _assert_status_legal("approve-plan", spec_path, plan_path)
            if err is not None:
                return err
            if state.get("amendment_pending") is not None:
                try:
                    state = complete_contract_amendment_reapproval(state)
                except ValueError as exc:
                    return stop(f"approve-plan: {exc}")
                write_state_atomic(spec_dir, state)
                print(
                    "loop-cohort: approve-plan completed pending amendment "
                    f"reapproval for {spec_dir.name}"
                )
                return 0
            print(
                f"loop-cohort: approve-plan already recorded for {spec_dir.name} (no-op)"
            )
            return 0
        spec_changed = spec_hash != stored_spec_hash
        plan_changed = plan_hash != stored_plan_hash
        return stop(
            f"approve-plan: artifact changed since approval — "
            f"spec_changed={spec_changed}, plan_changed={plan_changed}; "
            + _BOTH_CAUSES
        )

    # Crash-window guard: verify that both spec.md and plan.md still carry
    # Status: Approved before recording the baseline.  This detects the common
    # crash-window scenario (a file reverted to an earlier status while
    # plan_review_status was still "pending") but does NOT detect content
    # changes that leave the Status token unchanged.
    try:
        spec_status = _read_md_status(spec_path)
        plan_status_now = _read_md_status(plan_path)
    except UnreadableArtifact as exc:
        return stop(f"approve-plan: {exc}")
    if spec_status != "Approved":
        return stop(
            f"approve-plan: spec.md Status is {spec_status!r}; expected Approved "
            "(files may have changed in the crash window after plan-approved)"
        )
    if plan_status_now != "Approved":
        return stop(
            f"approve-plan: plan.md Status is {plan_status_now!r}; expected Approved "
            "(files may have changed in the crash window after plan-approved)"
        )

    state["plan_review_status"] = "approved"
    try:
        state["approved_spec_hash"] = sha256_canonical_contract(spec_path)
        state["approved_plan_hash"] = sha256_canonical_contract(plan_path)
    except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
        # Previously unguarded, and it WRITES what it computes — so an unsafe
        # artifact would either traceback out of the lock or, with a returning
        # fallback stub, store a non-digest as the approved baseline.
        return stop(f"approve-plan: cannot pin the approved artifacts: {exc}")
    if state.get("amendment_pending") is not None:
        try:
            state = complete_contract_amendment_reapproval(state)
        except ValueError as exc:
            return stop(f"approve-plan: {exc}")
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: approve-plan for {spec_dir.name} "
        f"(approved_spec_hash={state['approved_spec_hash'][:12]}… "
        f"approved_plan_hash={state['approved_plan_hash'][:12]}…)"
    )
    return 0


# ── plan check-current ────────────────────────────────────────────────────


def cmd_plan_check_current(args: argparse.Namespace) -> int:
    """CLI adapter over `check_plan_current`."""
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    result = _g.check_plan_current(spec_dir, require_schedule=args.require_schedule)
    if not result.ok:
        return stop(result.reason)
    _emit(result.message)
    return 0


# ── schedule ──────────────────────────────────────────────────────────────


def _schedule_check_current_impl(spec_dir: Path) -> int:
    """CLI adapter over `check_schedule_current`."""
    result = _g.check_schedule_current(spec_dir)
    if not result.ok:
        return stop(result.reason)
    _emit(result.message)
    return 0


def _schedule_run_impl(spec_dir: Path, expect_run_id: str, plan_override: str | None) -> int:
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, expect_run_id, verb="schedule")
    if err is not None:
        return err

    plan_path_canonical = spec_dir / "plan.md"
    if plan_override and Path(plan_override).resolve() != plan_path_canonical.resolve():
        return stop(
            f"schedule: --plan must point to {plan_path_canonical}; alternate paths create "
            "unusable state because schedule check-current always hashes plan.md"
        )
    plan_path = plan_path_canonical
    if not plan_path.exists():
        return stop(f"plan not found at {plan_path}")
    try:
        plan_text = read_managed_text(plan_path, "plan.md")
    except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
        # Was a raw `read_text()` under `@_locked("schedule")`: unbounded, symlink-
        # following, and a FIFO here blocked the cohort lock until it went stale.
        return stop(f"schedule: cannot read {plan_path.name}: {exc}")
    ordered, deps = parse_plan(plan_text)
    if not ordered:
        return stop(f"no '## T<n>' or '### T<n>' tasks found in {plan_path}")

    pin_error = validate_completed_task_sections(plan_text, state)
    if pin_error is not None:
        return stop(f"schedule: {pin_error}")
    completed = set(state.get("completed_task_ids", []))
    if completed:
        ordered = [task_id for task_id in ordered if task_id not in completed]
        if not ordered:
            return stop("schedule: amended plan has no unfinished task sections")
        remaining = set(ordered)
        deps = {
            task_id: deps.get(task_id, set()) & remaining
            for task_id in ordered
        }

    try:
        waves = schedule_unfinished_plan(plan_text, state)
    except ValueError as exc:
        return stop(f"schedule: {exc}")
    fwd = detect_forward_refs(ordered, deps)
    if fwd:
        pairs = ", ".join(f"{a}->{b}" for a, b in fwd)
        print(
            f"loop-cohort: warning — forward-reference(s) in {spec_dir.name} "
            f"(dep authored later; reordered below): {pairs}",
            file=sys.stderr,
        )

    touches = parse_touches_by_task(plan_text)
    print(
        f"loop-cohort: topological order for {spec_dir.name} "
        "(run sequentially by default; waves mark what *could* parallelize):"
    )
    for i, wave in enumerate(waves, 1):
        print(f"  wave {i}: {', '.join(wave)}")
        if len(wave) > 1:
            verdict = wave_touches_disjoint([touches.get(t) for t in wave])
            print(
                f"    predicted-disjoint: {verdict}  "
                "(Touches: screen — serialize-only, never a greenlight)"
            )

    try:
        plan_hash = sha256_canonical_contract(plan_path)
    except (OSError, UnicodeDecodeError, ValueError, ImportError) as exc:
        return stop(f"schedule: cannot hash {plan_path.name}: {exc}")
    state["plan_hash"] = plan_hash
    state["schedule_waves"] = waves
    state["current_wave_index"] = 0
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: schedule persisted for {spec_dir.name} "
        f"({len(waves)} wave(s), plan_hash={plan_hash[:12]}…)"
    )
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    first = args.schedule_first
    second = getattr(args, "schedule_second", None)
    if first == "check-current":
        if not second:
            return stop("schedule check-current: <spec-dir> required")
        try:
            spec_dir = _resolve_spec_dir(second)
        except ValueError as exc:
            return stop(str(exc))
        return _schedule_check_current_impl(spec_dir)
    # first is the spec-dir
    try:
        spec_dir = _resolve_spec_dir(first)
    except ValueError as exc:
        return stop(str(exc))
    if not args.expect_run_id:
        return stop("schedule: --expect-run-id is required")
    plan_override = getattr(args, "plan", None)
    return with_state_lock(
        spec_dir,
        "schedule",
        lambda: _schedule_run_impl(spec_dir, args.expect_run_id, plan_override),
    )


# ── check (phase termination) ─────────────────────────────────────────────


def cmd_check(args: argparse.Namespace) -> int:
    """CLI adapter over `check_phase`.

    Note the guard reads state for EVERY phase including `implement` — this verb has
    always refused on a missing or malformed `state.json` before reaching the
    `implement` stub, and the engine's `wave-complete` guard depends on that.
    """
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    result = _g.check_phase(spec_dir, phase=args.phase)
    if not result.ok:
        return stop(result.reason)
    _emit(result.message)
    return 0


# ── wave check / advance ──────────────────────────────────────────────────


def cmd_wave_check(args: argparse.Namespace) -> int:
    """CLI adapter over `check_wave`."""
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    result = _g.check_wave(spec_dir, expect=args.expect, wave_index=args.wave_index)
    if not result.ok:
        return stop(result.reason)
    _emit(result.message)
    return 0


@_locked("wave advance")
def cmd_wave_advance(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="wave advance")
    if err is not None:
        return err

    n_arg = args.from_index
    waves = state.get("schedule_waves", [])
    n = len(waves)

    if n == 0:
        return stop("wave advance: schedule_waves is empty")
    if n_arg < 0:
        return stop(f"wave advance: --from-index must be >= 0 (got {n_arg})")
    if n_arg >= n:
        return stop(
            f"wave advance: --from-index {n_arg} >= len(schedule_waves) {n}"
        )
    if n_arg == n - 1:
        return stop(
            f"wave advance: cannot advance from the final wave (index={n_arg}); "
            "use gates-clean to exit the final wave"
        )

    idx = int(state.get("current_wave_index", 0))
    if idx == n_arg:
        state["current_wave_index"] = n_arg + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: wave advance {n_arg} → {n_arg + 1} for {spec_dir.name}"
        )
        return 0
    if idx == n_arg + 1:
        print(
            f"loop-cohort: wave advance already applied "
            f"(current_wave_index={idx}) for {spec_dir.name}"
        )
        return 0
    return stop(
        f"wave advance: current_wave_index={idx} does not match "
        f"--from-index {n_arg} or {n_arg + 1}"
    )


# ── record-attempt ────────────────────────────────────────────────────────


@_locked("record-attempt")
def cmd_record_attempt(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    if args.phase != "implement":
        return stop(f"record-attempt: --phase must be 'implement' (got {args.phase!r})")
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="record-attempt")
    if err is not None:
        return err

    # The cycle-id must be <run_id>:<decimal-sequence>; the run_id prefix must match.
    cycle_id = args.cycle_id
    _parts = cycle_id.split(":", 1)
    if len(_parts) != 2 or not _parts[1].isdigit():
        return stop(
            f"record-attempt: --cycle-id must be '<run_id>:<decimal-sequence>' "
            f"(got {cycle_id!r})"
        )
    run_id_prefix = _parts[0]
    if run_id_prefix != args.expect_run_id:
        return stop(
            f"record-attempt: run_id prefix in --cycle-id ({run_id_prefix!r}) "
            f"does not match --expect-run-id ({args.expect_run_id!r})"
        )

    last_id = state.get("last_record_attempt_cycle_id")
    if last_id == cycle_id:
        print(
            f"loop-cohort: record-attempt already applied for cycle {cycle_id!r} "
            f"(idempotent no-op)"
        )
        return 0

    state["implementation_retry_count"] = int(state.get("implementation_retry_count", 0)) + 1
    state["last_record_attempt_cycle_id"] = cycle_id
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: record-attempt implementation_retry_count="
        f"{state['implementation_retry_count']} cycle={cycle_id!r} "
        f"for {spec_dir.name}"
    )
    return 0


# ── review inspect / record ───────────────────────────────────────────────

FINDING_LINE_RE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*`(?P<citation>[^`]+)`"
)
# frontend-reviewer: **title.** file:line. (unquoted file:line after title)
FINDING_LINE_RE_UNQUOTED = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*(?P<citation>\S+:\d+)"
)
# experience-reviewer: **title.** Where: <location>. (no file:line)
FINDING_LINE_RE_WHERE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*Where:\s*(?P<location>[^.]+)"
)
ADJUDICATION_HEADINGS = (
    "## Main-loop result",
    "## Refuted audit",
    "## Indeterminate audit",
)
NUMBERED_FINDING_MARKER_RE = re.compile(r"\*\*\d+\.")
NOT_CHECKED_HEADING = "## Not checked"
# Shape only, deliberately. Two earlier revisions tried to make footer bullets
# safe to skip adjudication — first by rejecting finding-shaped markers, then by
# requiring a `Did not ` opener. Both were defeated, because separating
# disclosure prose from finding prose is undecidable by pattern
# ("- Did not complete authorization review: unauthenticated requests can set
# is_admin=true" satisfies both). The footer's content is therefore never
# trusted: `not_checked_present` disqualifies a report from the clean fast path
# and routes it to full adjudication, which reads the whole body. That makes a
# content rule here non-load-bearing, and a guard that looks load-bearing but
# is not is worse than none.
NOT_CHECKED_BULLET_RE = re.compile(r"^- ")
STRICT_SUSTAINED_FINDING_LINE_RE = re.compile(
    r"^\*\*\d+\.[^*\n]+\*\*\s*"
    r"(?:`[^`\n]+:\d+[^`\n]*`|\S+:\d+|Where:\s+[^.\n]+)\.\s+"
    r"\S(?:.*\S)?\s+Fix:\s+\S.*$"
)


def parse_findings(report_text: str) -> list[str]:
    """Return SHA-256 fingerprints for findings in a reviewer report.

    Algorithm pinned by the work-loop SKILL §REVIEW:
        sha256("<file>|<line>|<title>")
    where <file> is the cited path exactly as written, <line> is the first
    integer after the first colon in the citation, and <title> is the
    bolded heading including the surrounding `**` markers.

    Supports three formats:
    - adversarial-reviewer: **title** `file:line`  (backtick-quoted citation)
    - frontend-reviewer:    **title.** file:line.  (unquoted file:line)
    - experience-reviewer:  **title.** Where: loc. (location; key uses loc|0|title)
    """
    fingerprints: list[str] = []
    for raw in report_text.splitlines():
        line = raw.strip()
        if not line.startswith("**"):
            continue
        # Try backtick-quoted citation first (adversarial-reviewer)
        m = FINDING_LINE_RE.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            if ":" not in citation:
                continue
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            key = f"{file_part}|{line_match.group(0)}|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
            continue
        # Try Where: <location> (experience-reviewer)
        m = FINDING_LINE_RE_WHERE.match(line)
        if m:
            title = m.group("title").strip()
            location = m.group("location").strip()
            key = f"{location}|0|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
            continue
        # Try unquoted file:line (frontend-reviewer)
        m = FINDING_LINE_RE_UNQUOTED.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            key = f"{file_part}|{line_match.group(0)}|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
    return fingerprints


def _is_strict_actionable_result(actionable: str) -> bool:
    """Accept exact clean or complete parser-compatible sustained lines."""
    if actionable == CLEAN_SUBSTRING:
        return True

    finding_lines = [line for line in actionable.splitlines() if line.strip()]
    return bool(finding_lines) and all(
        STRICT_SUSTAINED_FINDING_LINE_RE.fullmatch(line.strip()) is not None
        and len(NUMBERED_FINDING_MARKER_RE.findall(line)) == 1
        and len(parse_findings(line)) == 1
        for line in finding_lines
    )


def _invalid(reason: str) -> dict:
    """Refuse a report, naming which rule refused it.

    `invalid` returns at exit 0 and stops the loop, so an unnamed refusal costs
    the operator a parser read to act on. The reason is enumerated and
    content-free, matching `review-artifact.py`'s refusal codes.
    """
    print(
        f"loop-cohort: report classified invalid ({reason})",
        file=sys.stderr,
    )
    return {
        "classification": "invalid",
        "fingerprints": [],
        "matches_previous_round": False,
        "reason": reason,
    }


def _actionable_review_text(
    report_text: str,
    *,
    require_adjudication: bool = False,
) -> tuple[str, str | None]:
    """Return the main-loop result and a refusal reason, or None when accepted.

    Legacy reviewer reports have no adjudication headings and remain unchanged.
    When any adjudication heading is present, require the exact three-section
    envelope, keep only the main-loop result, and reject finding-shaped audit
    text rather than allowing it to reach fingerprinting.

    The second element is `None` when the structure is acceptable, otherwise an
    enumerated, content-free code naming which rule refused it. Codes mirror
    `review-artifact.py`'s `INVALID <code>` refusal vocabulary — the other half
    of this gateway — so a fail-closed stop is diagnosable without reopening the
    artifact or reverse-engineering the parser. They carry no report content,
    no path, and no line text.
    """
    lines = report_text.splitlines()
    found_headings = [
        line.strip() for line in lines if line.strip().startswith("## ")
    ]
    if not any(heading in found_headings for heading in ADJUDICATION_HEADINGS):
        return report_text, "legacy-report" if require_adjudication else None
    if found_headings != list(ADJUDICATION_HEADINGS):
        return "", "envelope-headings"

    heading_indexes = [
        next(index for index, line in enumerate(lines) if line.strip() == heading)
        for heading in ADJUDICATION_HEADINGS
    ]
    if any(line.strip() for line in lines[: heading_indexes[0]]):
        return "", "prose-before-envelope"

    main_start, refuted_start, indeterminate_start = heading_indexes
    audit_lines = lines[refuted_start + 1 :]
    if any(NUMBERED_FINDING_MARKER_RE.search(line) for line in audit_lines):
        return "", "audit-numbered-finding"

    actionable = "\n".join(lines[main_start + 1 : refuted_start]).strip()
    indeterminate_audit = "\n".join(lines[indeterminate_start + 1 :]).strip()

    # The refusals below are NOT gated on `require_adjudication`. Reaching here
    # already proves the exact three-section envelope is present, so the report
    # is an adjudication whichever flag the caller passed — and an indeterminate
    # verdict must never classify as clean (AC5), including on a flagless
    # `review inspect` or a replayed `review record`. Envelope-free legacy
    # reports returned earlier and are unaffected.
    #
    # Order matters for the operator, not for soundness — every `if` below
    # refuses. Report the most specific cause first: an indeterminate verdict is
    # a decision the adjudicator made and the owner must resolve, whereas a
    # shape complaint about the same report would send them to the wrong place.
    if INDETERMINATE_SENTINEL in report_text:
        return "", "indeterminate-present"
    if indeterminate_audit != "None.":
        return "", "indeterminate-audit-not-none"
    if not _is_strict_actionable_result(actionable):
        return "", "sustained-line-shape"
    return actionable, None


def _resolved_report(candidate: str) -> Path:
    """Normalise the CLI-supplied `--report` path at the argv boundary.

    Normalise-only, deliberately. The two `--root` linters in this skill raise
    on an unusable path, but `--report` must not: `review inspect` classifies an
    unreadable report as `invalid`, which the work-loop SKILL documents as a
    Surface signal rather than a crash. Raising here would convert a defined
    outcome into an operational error.

    The `resolve()` still does the job it is here for — it puts the
    normalisation adjacent to the argv read, where a taint analyser can see it,
    instead of leaving a raw `Path(args.report)` as the boundary.
    """
    try:
        return Path(candidate).resolve()
    except (OSError, ValueError, RuntimeError):
        # resolve() raises on an embedded null (ValueError) and on Windows
        # reserved names (OSError). Falling back to the unresolved path keeps
        # the value flowing to _classify_report, which classifies it `invalid`
        # at exit 0 — the defined outcome. Raising here would reintroduce
        # exactly the operational error this helper's docstring rules out.
        return Path(candidate)


def _classify_raw_report(report_path: Path) -> dict[str, object]:
    """Classify a raw reviewer return without widening adjudication semantics.

    This remains separate from `_classify_report`: that function's optional
    adjudication envelope is a high-stakes path, where a third mode could
    silently weaken strict classification.
    """
    reason: str | None = None
    try:
        report_text = read_managed_text(report_path.resolve(), report_path.name)
    except (OSError, UnicodeDecodeError, ValueError):
        classification = "invalid"
        finding_count = 0
        classified_digest = None
        reason = "unreadable"
        lines: list[str] = []
    else:
        # Digest the bytes this call actually classified, not a second read.
        # `read_managed_text` decodes bytes strictly without folding newlines, so
        # re-encoding is byte-identical to the file. A caller that re-opened the
        # path for its audit anchor could digest content nobody classified.
        classified_digest = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
        # LF and CRLF only (AC2.3b). `str.splitlines()` also breaks on \v, \f,
        # \x1c-\x1e, \x85, U+2028 and U+2029, so a single visual line could be
        # split into a grammar that reads clean. Any of those left embedded here
        # makes its line unequal to the sentinel, which fails closed.
        lines = report_text.replace("\r\n", "\n").split("\n")
        finding_count = len(parse_findings(report_text))
        if finding_count:
            classification = "findings"
        else:
            sentinel_count = sum(line == CLEAN_SUBSTRING for line in lines)
            sentinel_index = next(
                (index for index, line in enumerate(lines) if line == CLEAN_SUBSTRING),
                -1,
            )
            footer_started = False
            clean_shape = sentinel_count == 1
            if not clean_shape:
                reason = "sentinel-absent" if sentinel_count == 0 else "sentinel-repeated"
            for index, line in enumerate(lines):
                if not clean_shape:
                    break
                if not line or index == sentinel_index:
                    continue
                if index < sentinel_index:
                    clean_shape = False
                    reason = "content-before-sentinel"
                    break
                if line == NOT_CHECKED_HEADING:
                    if footer_started:
                        clean_shape = False
                        reason = "footer-heading-repeated"
                        break
                    footer_started = True
                    continue
                if footer_started and NOT_CHECKED_BULLET_RE.match(line):
                    continue
                clean_shape = False
                reason = (
                    "footer-bullet-malformed" if footer_started else "unpermitted-content"
                )
                break
            classification = "clean" if clean_shape else "invalid"

    # Disclosure metadata is deliberately computed after classification.
    not_checked_present = NOT_CHECKED_HEADING in lines
    return {
        "classification": classification,
        "finding_count": finding_count,
        "not_checked_present": not_checked_present,
        # Internal only — never emitted in the JSON payload.
        # `_raw_classification_payload` projects the closed public field set so a
        # key added here cannot leak into the documented contract. The reason is
        # a fixed, content-free code surfaced on stderr, mirroring
        # `_actionable_review_text`'s refusal vocabulary: a bare `invalid` leaves
        # an operator unable to tell a missing sentinel from a malformed footer.
        "_classified_digest": classified_digest,
        "_reason": reason,
    }


RAW_REFUSAL_REASONS = frozenset(
    {
        "unreadable",
        "sentinel-absent",
        "sentinel-repeated",
        "content-before-sentinel",
        "footer-heading-repeated",
        "footer-bullet-malformed",
        "unpermitted-content",
    }
)


def _warn_raw_refusal(result: dict[str, object]) -> None:
    """Name which grammar rule refused the report, without echoing its content."""
    reason = result.get("_reason")
    if result["classification"] == "invalid" and reason:
        print(f"loop-cohort: raw report refused ({reason})", file=sys.stderr)


RAW_CLASSIFICATION_FIELDS = ("classification", "finding_count", "not_checked_present")


def _raw_classification_payload(result: dict[str, object]) -> dict[str, object]:
    """Project the closed emitted field set for the raw-classify contract."""
    return {field: result[field] for field in RAW_CLASSIFICATION_FIELDS}


def _classify_report(
    report_path: Path,
    state: dict,
    *,
    require_adjudication: bool = False,
) -> dict:
    """Classify a reviewer report. Exits 0 for all report-content outcomes.

    Returns a dict with keys: classification, fingerprints, matches_previous_round.
    """
    # Bounded read, reached from `cmd_review_record`, which holds the state lock — so a
    # reviewer report that is a FIFO or an arbitrarily large file would otherwise block
    # or read without limit inside the critical section.
    #
    # The path is RESOLVED first, deliberately. Unlike `spec.md` / `plan.md` this is a
    # user-supplied `--report` argument, not managed state: it carries no confinement
    # claim, and a symlinked report worked before this change. Reading the unresolved
    # path would make `O_NOFOLLOW` refuse it, narrowing a shipped CLI's accepted inputs
    # for no security benefit — the author chose the path. Resolving keeps the size and
    # FIFO bounds, which are the parts that matter under the lock.
    try:
        report_text = read_managed_text(report_path.resolve(), report_path.name)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # The reason is REPORTED, not discarded. This returns `invalid` at exit 0, so
        # without a diagnostic an unreadable report is indistinguishable from one that
        # genuinely contains no findings — and that classification feeds the review
        # retry accounting.
        print(
            f"loop-cohort: warning — {_diag(report_path.name)} could not be read "
            f"({_diag(exc)}); classified invalid",
            file=sys.stderr,
        )
        return _invalid("unreadable")

    actionable_text, refusal = _actionable_review_text(
        report_text,
        require_adjudication=require_adjudication,
    )
    if refusal is not None:
        return _invalid(refusal)

    fps = parse_findings(actionable_text)
    if require_adjudication:
        has_clean = actionable_text == CLEAN_SUBSTRING
    else:
        has_clean = (
            CLEAN_SUBSTRING in actionable_text
            or _SHIP_IT_RE.search(actionable_text) is not None
        )

    if fps:
        classification = "findings"
    elif has_clean:
        classification = "clean"
    else:
        # No fingerprints and no clean sentinel. Reachable on the flagless
        # legacy path; name it like every other refusal so a consumer reading
        # `reason` never sees a missing key.
        return _invalid("no-actionable-result")

    canonical_fps = sorted(set(fps))
    previous = sorted(set(state.get("finding_fingerprints", [])))

    # Empty-vs-empty is always false (not stasis — no meaningful comparison)
    matches_prev = bool(canonical_fps and canonical_fps == previous)

    return {
        "classification": classification,
        "fingerprints": canonical_fps,
        "matches_previous_round": matches_prev,
    }


def _print_review_result(result: dict, *, as_json: bool, verb: str) -> None:
    """Print one review classification without report content or path data."""
    if as_json:
        print(json.dumps(result))
        return
    print(
        f"loop-cohort: review {verb} classification={result['classification']} "
        f"fingerprints={len(result['fingerprints'])} "
        f"matches_previous_round={result['matches_previous_round']}"
    )


def cmd_review_classify(args: argparse.Namespace) -> int:
    """Strictly classify an adjudication report without cohort state."""
    report_path = _resolved_report(args.report)
    result = _classify_report(
        report_path,
        {},
        require_adjudication=True,
    )
    _print_review_result(result, as_json=args.json, verb="classify")
    return 0


def cmd_review_raw_classify(args: argparse.Namespace) -> int:
    """Classify a raw reviewer report without cohort state."""
    full = _classify_raw_report(_resolved_report(args.report))
    _warn_raw_refusal(full)
    result = _raw_classification_payload(full)
    if args.json:
        print(json.dumps(result))
    else:
        print(
            "loop-cohort: review raw-classify "
            f"classification={result['classification']} "
            f"finding_count={result['finding_count']} "
            f"not_checked_present={result['not_checked_present']}"
        )
    return 0


def cmd_review_inspect(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        # Operational error (spec-dir unresolvable or state.json unreadable)
        return stop(str(exc))

    report_path = _resolved_report(args.report)
    result = _classify_report(
        report_path,
        state,
        require_adjudication=args.adjudication,
    )

    _print_review_result(result, as_json=args.json, verb="inspect")
    return 0  # content outcomes always exit 0


# ── review-record idempotency ─────────────────────────────────────────────
#
# `--operation-id` names the round being recorded, so a session that re-issues a
# recording after losing its own record of whether the write landed gets one
# write rather than two. The id is `<run_id>:<transition_sequence>` supplied by
# the caller and validated here; this module never reads `engine-state.json`.
#
# The payload digest is STORED, not derived on read. Deriving it is unsound: the
# fingerprint and all-skipped branches overwrite `finding_fingerprints` and never
# touch `last_review_clean_source`, the clean branches do the reverse, and no
# field records which form closed a round — so `state.json` stops describing a
# round's payload as soon as the next round lands.

# `\A`/`\Z`, not `^`/`$`: Python's `$` also matches before a trailing newline,
# so `"<run>:1\n"` would pass and then compare unequal to `"<run>:1"` -- two
# spellings of one round, each recording separately. `[0-9]` rather than `\d`
# for the same reason: `\d` accepts Unicode decimal digits.
_REVIEW_OP_ID_RE = re.compile(r"\A(?P<run>[^:\n]+):(?P<seq>[0-9]{1,18})\Z")
_REVIEW_OP_ID_MAX = 200


def _review_payload_digest(form: str, payload: str) -> str:
    r"""`sha256(form + "\n" + payload)`. The form prefix stops two forms colliding."""
    return hashlib.sha256(f"{form}\n{payload}".encode()).hexdigest()


def _review_operation_gate(
    state: dict,
    operation_id: str | None,
    payload_digest: str | None,
    *,
    expect_run_id: str,
    spec_name: str,
) -> tuple[str, int | None]:
    """Decide the recorded round's fate before any mutation.

    Returns `(outcome, exit_code)`. `outcome` is one of:

    - `"unflagged"` — no id supplied; behave exactly as before and leave the two
      recorded fields alone. They name the last round recorded *under an id*,
      which a flagless round does not become.
    - `"already"`   — this id and this payload are already recorded; no mutation.
    - `"record"`    — proceed with the mutation and set both fields.
    - `"refuse"`    — caller must return the accompanying exit code.
    """
    if operation_id is None:
        return "unflagged", None

    if len(operation_id) > _REVIEW_OP_ID_MAX:
        # Its own message. Folding this into the format refusal below would tell
        # an operator the format was wrong when the format may be perfectly
        # correct and only the length is not.
        return "refuse", stop(
            f"review record: --operation-id is {len(operation_id)} characters, "
            f"over the {_REVIEW_OP_ID_MAX}-character limit, for {spec_name}"
        )

    matched = _REVIEW_OP_ID_RE.match(operation_id)
    # A leading zero is a second spelling of the same sequence, and the recorded
    # id is compared by exact string equality, so `:01` and `:1` would each
    # record the round once.
    canonical = matched is not None and (
        matched.group("seq") == "0" or not matched.group("seq").startswith("0")
    )
    if not canonical:
        return "refuse", stop(
            f"review record: --operation-id must be "
            f"'<expect-run-id>:<decimal-sequence>' with no leading zero "
            f"(got {operation_id!r}) for {spec_name}"
        )
    if matched.group("run") != expect_run_id:
        return "refuse", stop(
            f"review record: --operation-id names run {matched.group('run')!r} "
            f"but --expect-run-id is {expect_run_id!r} for {spec_name}"
        )
    if payload_digest is None:
        # Refusing here is what keeps a later repeat decidable: an id recorded
        # without a comparison value could never be judged a replay.
        return "refuse", stop(
            "review record: this round's payload digest could not be computed, "
            "so recording it under an operation id would leave a later repeat "
            f"undecidable; re-run once the payload is readable, for {spec_name}"
        )

    recorded_id = state.get("last_review_record_operation_id")
    if recorded_id == operation_id:
        if state.get("last_review_record_payload_digest") == payload_digest:
            _emit(
                f"review record already recorded for operation "
                f"{operation_id!r} (idempotent no-op) for {spec_name}"
            )
            return "already", 0
        return "refuse", stop(
            f"review record: operation {operation_id!r} is already recorded with "
            f"a different payload; a replay must carry the payload it recorded. "
            f"Compare against last_review_record_payload_digest in "
            f"`loop-cohort status --json` for {spec_name}"
        )
    return "record", None


@_locked("review record")
def cmd_review_record(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="review record")
    if err is not None:
        return err

    operation_id = getattr(args, "operation_id", None)

    if getattr(args, "all_skipped", False):
        # All-skipped branch: every warranted reviewer was a named skip
        digest = _review_payload_digest("all-skipped", "")
        outcome, code = _review_operation_gate(
            state, operation_id, digest,
            expect_run_id=args.expect_run_id, spec_name=spec_dir.name,
        )
        if outcome in ("refuse", "already"):
            return code
        if outcome == "record":
            state["last_review_record_operation_id"] = operation_id
            state["last_review_record_payload_digest"] = digest
        state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
        state["finding_fingerprints"] = []
        rounds = non_negative_int(state, "review_round_count", 0)
        if isinstance(rounds, str):
            return stop(f"review record: {rounds} for {spec_dir.name}")
        state["review_round_count"] = rounds + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: review record (all-skipped) "
            f"round={state['review_round_count']} for {spec_dir.name}"
        )
        return 0

    if args.fingerprint:
        # Findings branch: --fingerprint <hex> ...
        fingerprints = sorted(set(args.fingerprint))
        bad = [fp for fp in fingerprints if not _RE_FINGERPRINT.match(fp)]
        if bad:
            return stop(
                f"review record: --fingerprint must be lowercase 64-char SHA-256 hex "
                f"(40-char SHA-1 still accepted for a run that predates core 2.3.0); "
                f"invalid: {bad!r}"
            )
        digest = _review_payload_digest("fingerprint", "\n".join(fingerprints))
        outcome, code = _review_operation_gate(
            state, operation_id, digest,
            expect_run_id=args.expect_run_id, spec_name=spec_dir.name,
        )
        if outcome in ("refuse", "already"):
            return code
        # The cap belongs here, not before the gate: a replay of an
        # already-recorded round writes nothing, so refusing it would break the
        # decidability this flag exists for at exactly the crash window that
        # matters. Only a round that would actually be recorded is capped.
        #
        # It previously held only because the shipped instructions chained this
        # command to a capped transition with `&&`. Splitting those statements
        # showed the cap was carried by shell punctuation rather than by code.
        retries = non_negative_int(state, "review_retry_count", 0)
        cap = non_negative_int(state, "max_review_retries",
                               DEFAULTS["max_review_retries"])
        if isinstance(retries, str):
            return stop(f"review record: {retries} for {spec_dir.name}")
        if isinstance(cap, str):
            return stop(f"review record: {cap} for {spec_dir.name}")
        if retries >= cap and not getattr(args, "allow_retry_cap_override", False):
            return stop(
                f"review record: review retry cap reached ({retries}/{cap}) for "
                f"{spec_dir.name}; a findings round past the cap is the runaway "
                f"the cap exists to stop — stop and surface it. Only a human "
                f"directing this run may continue: reset and start a new run, or "
                f"pass --allow-retry-cap-override to this command AND to the "
                f"`loop-engine transition findings-remain` that opens the round "
                f"(either half alone leaves the cohort and the engine a round apart)"
            )
        if outcome == "record":
            state["last_review_record_operation_id"] = operation_id
            state["last_review_record_payload_digest"] = digest
        state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
        state["finding_fingerprints"] = fingerprints
        state["review_retry_count"] = retries + 1  # the value the cap above validated
        rounds = non_negative_int(state, "review_round_count", 0)
        if isinstance(rounds, str):
            return stop(f"review record: {rounds} for {spec_dir.name}")
        state["review_round_count"] = rounds + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: review record (findings) "
            f"round={state['review_round_count']} retry={state['review_retry_count']} "
            f"fingerprints={len(fingerprints)} for {spec_dir.name}"
        )
        return 0

    # Clean branches: a persisted byte-equal or structural raw return, or a
    # validated adjudication report. Each rests on bytes read back from disk, so a
    # recorded clean round is never the caller's own assertion about what a
    # reviewer said.
    direct_clean_file = getattr(args, "direct_clean_file", None)
    if direct_clean_file is not None:
        if args.adjudication:
            return stop(
                "review record: --direct-clean-file and --adjudication name two "
                "different recording forms; use --report <path> --adjudication "
                "for an adjudicated clean"
            )
        artifact_path = _resolved_report(direct_clean_file)
        try:
            raw = artifact_path.read_bytes()
        except OSError:
            return stop(
                "review record: --direct-clean-file is unreadable; persist the "
                "reviewer's complete return before recording"
            )
        # Byte comparison, not a decode-then-compare: an encoding that merely
        # round-trips to the sentinel is not the sentinel.
        if raw != CLEAN_SUBSTRING.encode("utf-8"):
            return stop(
                "review record: --direct-clean-file requires the exact clean sentinel"
            )
        clean_source = "direct-clean"
        clean_digest = hashlib.sha256(raw).hexdigest()
    elif structural_clean_file := getattr(args, "structural_clean_file", None):
        if args.adjudication:
            return stop(
                "review record: --structural-clean-file and --adjudication name two "
                "different recording forms"
            )
        artifact_path = _resolved_report(structural_clean_file)
        result = _classify_raw_report(artifact_path)
        if result["classification"] != "clean":
            _warn_raw_refusal(result)
            return stop(
                "review record: --structural-clean-file requires a clean raw-report classification"
            )
        # A disclosure footer is prose, and prose is what the adjudicator exists
        # to read. Its content is never trusted here, so a footer-bearing report
        # is never fast-pathed however well-formed it looks. This reads
        # `not_checked_present` for ROUTING only; classification above is
        # decided without it (AC2.4).
        if result["not_checked_present"]:
            return stop(
                "review record: a report carrying a '## Not checked' footer is not "
                "eligible for the clean fast path; route it through "
                "finding-adjudicator and record with --report … --adjudication"
            )
        clean_source = "structural-clean"
        # The digest comes from the same read that classified the artifact. A
        # second open here would let a concurrent write make the recorded audit
        # anchor attest to content that was never classified clean.
        clean_digest = result["_classified_digest"]
        if not isinstance(clean_digest, str):
            return stop(
                "review record: --structural-clean-file produced no digest for "
                "the classified bytes; re-persist the reviewer's return"
            )
    else:
        if not args.report:
            return stop(
                "review record: one of --direct-clean-file, --structural-clean-file, --report, or "
                "--fingerprint is required"
            )
        if not args.adjudication:
            return stop(
                "review record: --report requires --adjudication; use "
                "--direct-clean-file for a persisted exact raw clean return"
            )
        report_path = _resolved_report(args.report)
        result = _classify_report(
            report_path,
            state,
            require_adjudication=True,
        )
        if result["classification"] != "clean":
            cls = result["classification"]
            return stop(
                f"review record --report: report classified as {cls!r}; "
                "use --fingerprint for a findings round"
            )
        clean_source = "report"
        try:
            clean_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
        except OSError:
            # _classify_report already read it; a race here loses provenance
            # but must not undo a classification that succeeded.
            clean_digest = None

    digest = (None if clean_digest is None
              else _review_payload_digest(clean_source, clean_digest))
    outcome, code = _review_operation_gate(
        state, operation_id, digest,
        expect_run_id=args.expect_run_id, spec_name=spec_dir.name,
    )
    if outcome in ("refuse", "already"):
        return code
    if outcome == "record":
        state["last_review_record_operation_id"] = operation_id
        state["last_review_record_payload_digest"] = digest
    state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
    state["finding_fingerprints"] = []
    rounds = non_negative_int(state, "review_round_count", 0)
    if isinstance(rounds, str):
        return stop(f"review record: {rounds} for {spec_dir.name}")
    state["review_round_count"] = rounds + 1
    # Provenance: which recording form closed this round, and the digest of the
    # artifact it rested on. Session resumption reads these to replay the form
    # instead of inferring it from an artifact whose absence is ambiguous.
    state["last_review_clean_source"] = clean_source
    state["last_review_clean_digest"] = clean_digest
    # review_retry_count unchanged on clean review
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: review record (clean:{clean_source}) "
        f"round={state['review_round_count']} "
        f"retry={state['review_retry_count']} for {spec_dir.name}"
    )
    return 0


# ── disabled Phase-1 verbs ────────────────────────────────────────────────


def cmd_dispatch_decision(args: argparse.Namespace) -> int:
    return _disabled("dispatch-decision")


def cmd_auto_parallel(args: argparse.Namespace) -> int:
    return _disabled("auto-parallel")


def cmd_worktree_preflight(args: argparse.Namespace) -> int:
    return _disabled("worktree preflight")


def cmd_worktree_add(args: argparse.Namespace) -> int:
    return _disabled("worktree add")


def cmd_worktree_record(args: argparse.Namespace) -> int:
    return _disabled("worktree record")


def cmd_worktree_list(args: argparse.Namespace) -> int:
    return _disabled("worktree list")


def cmd_worktree_merge(args: argparse.Namespace) -> int:
    return _disabled("worktree merge")


def cmd_worktree_cleanup(args: argparse.Namespace) -> int:
    return _disabled("worktree cleanup")


# ── dispatcher ────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loop-cohort", description=__doc__)
    sub = p.add_subparsers(dest="verb", required=True)

    # init
    sp = sub.add_parser("init", help="initialise state.json from the bundled template")
    sp.add_argument("spec_dir")
    sp.add_argument("--run-id", required=True, dest="run_id",
                    help="UUID generated by loop-engine init")
    sp.set_defaults(func=cmd_init)

    # identity
    sp = sub.add_parser(
        "identity",
        help="read-only: verify schema_version=1 and optionally run_id match",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect-run-id", dest="expect_run_id", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_identity)

    # status
    sp = sub.add_parser(
        "status",
        help="read-only: return cohort fields for session resumption",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_status)

    # reset
    sp = sub.add_parser("reset", help="delete state.json; idempotent")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_reset)

    # check
    sp = sub.add_parser("check", help="phase termination check")
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=PHASES)
    sp.set_defaults(func=cmd_check)

    # approve-plan
    sp = sub.add_parser(
        "approve-plan",
        help="record plan_review_status=approved and hash spec/plan",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_approve_plan)

    # plan (namespace with sub-verbs)
    sp_plan = sub.add_parser("plan", help="plan-approval guard verbs")
    plan_sub = sp_plan.add_subparsers(dest="plan_verb", required=True)
    sp = plan_sub.add_parser(
        "check-current",
        help="verify plan_review_status, spec/plan hashes, and optionally schedule",
    )
    sp.add_argument("spec_dir")
    sp.add_argument(
        "--require-schedule", action="store_true", dest="require_schedule",
        help="also verify plan_hash matches approved_plan_hash and schedule_waves non-empty",
    )
    sp.set_defaults(func=cmd_plan_check_current)

    # schedule (custom dispatch: first positional is spec-dir or "check-current")
    sp_sched = sub.add_parser(
        "schedule",
        help="DAG-order schedule (persists plan_hash + waves) or 'check-current'",
    )
    sp_sched.add_argument(
        "schedule_first",
        metavar="<spec-dir> | check-current",
        help="spec directory path, or 'check-current' for the read-only hash check",
    )
    sp_sched.add_argument(
        "schedule_second",
        nargs="?",
        metavar="<spec-dir>",
        help="spec directory path when first arg is 'check-current'",
    )
    sp_sched.add_argument("--expect-run-id", dest="expect_run_id", default=None)
    sp_sched.add_argument(
        "--plan", default=None,
        help="path to plan.md (default: <spec-dir>/plan.md)",
    )
    sp_sched.set_defaults(func=cmd_schedule)

    # record-attempt
    sp = sub.add_parser(
        "record-attempt",
        help="record a gates-failed repair attempt (idempotent per cycle-id)",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=["implement"])
    sp.add_argument("--cycle-id", required=True, dest="cycle_id")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_record_attempt)

    # wave (namespace with sub-verbs)
    sp_wave = sub.add_parser("wave", help="wave-advance and guard verbs")
    wave_sub = sp_wave.add_subparsers(dest="wave_verb", required=True)

    sp = wave_sub.add_parser(
        "check",
        help="read-only: verify more/last wave guard",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect", required=True, choices=["more", "last"])
    sp.add_argument("--wave-index", type=int, dest="wave_index", default=None)
    sp.set_defaults(func=cmd_wave_check)

    sp = wave_sub.add_parser(
        "advance",
        help="idempotent: advance current_wave_index from n to n+1",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--from-index", required=True, type=int, dest="from_index")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_wave_advance)

    # review (namespace with sub-verbs)
    sp_review = sub.add_parser("review", help="review-phase state mutations")
    review_sub = sp_review.add_subparsers(dest="review_verb", required=True)

    sp = review_sub.add_parser(
        "classify",
        help="state-free: strictly classify a finding-adjudicator report",
    )
    sp.add_argument("--report", required=True)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_review_classify)

    sp = review_sub.add_parser(
        "raw-classify",
        help="state-free: classify a raw reviewer report with the closed footer grammar",
    )
    sp.add_argument("--report", required=True)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_review_raw_classify)

    sp = review_sub.add_parser(
        "inspect",
        help="read-only: classify a reviewer report (clean/findings/invalid)",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--report", required=True)
    sp.add_argument(
        "--adjudication",
        action="store_true",
        help="require the exact finding-adjudicator report envelope",
    )
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_review_inspect)

    sp = review_sub.add_parser(
        "record",
        help="rotate fingerprints and bump counters after a CODE-REVIEW round",
    )
    sp.add_argument("spec_dir")
    _rr_grp = sp.add_mutually_exclusive_group(required=True)
    _rr_grp.add_argument(
        "--direct-clean-file",
        default=None,
        help=(
            "path to the persisted complete reviewer return; its bytes must "
            "equal the exact clean sentinel"
        ),
    )
    _rr_grp.add_argument(
        "--structural-clean-file",
        default=None,
        help="path to a raw reviewer return accepted by review raw-classify",
    )
    _rr_grp.add_argument(
        "--report",
        default=None,
        help="path to a clean adjudication report; requires --adjudication",
    )
    _rr_grp.add_argument(
        "--fingerprint",
        action="append",
        default=None,
        help="explicit fingerprint (hex sha256); use for findings rounds",
    )
    _rr_grp.add_argument(
        "--all-skipped",
        action="store_true",
        default=False,
        dest="all_skipped",
        help="all warranted reviewers were named skips; bumps round count, clears fingerprints",
    )
    sp.add_argument(
        "--adjudication",
        action="store_true",
        help="require the exact finding-adjudicator envelope for --report",
    )
    sp.add_argument(
        "--allow-retry-cap-override",
        action="store_true",
        dest="allow_retry_cap_override",
        help=(
            "record a findings round even though review_retry_count has reached "
            "max_review_retries; for a human who has looked, not for an "
            "unattended loop"
        ),
    )
    sp.add_argument(
        "--operation-id",
        default=None,
        dest="operation_id",
        help=(
            "'<run_id>:<transition_sequence>' naming this round; a repeat under "
            "the same id and payload is a completed write, not a new round"
        ),
    )
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_review_record)

    # dispatch-decision (disabled)
    sp = sub.add_parser(
        "dispatch-decision",
        help="(disabled in Phase 1 — exits non-zero)",
    )
    sp.add_argument("--category", action="append", default=[])
    sp.add_argument("--branch", action="append", default=[])
    sp.add_argument("--base", default=None)
    sp.set_defaults(func=cmd_dispatch_decision)

    # auto-parallel (disabled)
    sp = sub.add_parser(
        "auto-parallel",
        help="(disabled in Phase 1 — exits non-zero)",
    )
    sp.add_argument("spec_dir", nargs="?")
    sp.add_argument("--off", action="store_true")
    sp.set_defaults(func=cmd_auto_parallel)

    # worktree (disabled)
    sp_wt = sub.add_parser("worktree", help="(disabled in Phase 1 — exits non-zero)")
    wt_sub = sp_wt.add_subparsers(dest="worktree_verb", required=True)

    for wt_verb, wt_func, wt_help in [
        ("preflight", cmd_worktree_preflight, "disabled"),
        ("add", cmd_worktree_add, "disabled"),
        ("record", cmd_worktree_record, "disabled"),
        ("list", cmd_worktree_list, "disabled"),
        ("merge", cmd_worktree_merge, "disabled"),
        ("cleanup", cmd_worktree_cleanup, "disabled"),
    ]:
        sp = wt_sub.add_parser(wt_verb, help=wt_help)
        sp.add_argument("spec_dir", nargs="?")
        if wt_verb == "record":
            # Preserve original signature so callers get the "disabled" message
            # instead of an argparse "unrecognized arguments" error.
            sp.add_argument("task_id", nargs="?")
            sp.add_argument("--status", choices=WORKTREE_STATUSES)
            sp.add_argument("--report")
        else:
            sp.add_argument("args", nargs="*")
        sp.set_defaults(func=wt_func)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # One chokepoint, not ~20 verb entries. Every verb reaches its body through this
    # line, so a missed sentinel check is impossible here in a way it is not when the
    # check is copied into each verb — and a verb that slipped through would run on
    # stub callables that raise, which is loud but later than it needs to be.
    if _g is None:
        return stop(_guards_error or "_loop_guards.py is unavailable")
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return stop("interrupted")


_MODULE_COMPLETE = True


if __name__ == "__main__":
    sys.exit(main())
