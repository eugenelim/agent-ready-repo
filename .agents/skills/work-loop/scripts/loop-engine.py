#!/usr/bin/env python
"""loop-engine — work-loop phase FSM validator (Phase 1, Option A).

Validates legal phase ordering, runs read-only guards, and records the
current phase in engine-state.json. Does NOT invoke loop-cohort mutations.
The skill invokes all mutations explicitly.

Two modes in Phase 1:
  code       — full ten-state lifecycle with implementation waves
  spec-plan  — spec/plan drafting only (six-state; terminates at DONE via plan-locked)

Human-wait states in the spec/plan phase:
  SPEC-HUMAN-GATE  — scope decision: does this spec define the right thing to build?
  PLAN-HUMAN-GATE  — build decision: does this plan describe the right way to build it?

Verb surface
------------
    loop-engine init <spec-dir> --mode {code|spec-plan} [--json]
    loop-engine transition <spec-dir> <event> [--wave-index <n>]
    loop-engine status <spec-dir> [--json]
    loop-engine reset <spec-dir>

Exit contract: 0 on success; non-zero with a one-line reason on stderr.

Schema reference: references/state-schema.md
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid as _uuid_mod
from datetime import UTC, datetime
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent

# ── the lock-hold budget (ADR-0074 / spec/work-loop-in-process-guards AC22) ─
#
# `cmd_transition` holds the state lock across a read-decide-write section. Three
# numbers are ONE budget, and breaking the ordering silently reinstates the lost
# update this lock exists to prevent:
#
#     statelock timeout (10s)  <  max hold  <  statelock stale_after (300s)
#
# `timeout` must be shorter than a legitimate hold, or contenders give up on a
# live holder. `stale_after` must exceed one, or a merely-slow holder is judged
# dead, its lock is reclaimed, and a second writer is admitted.
#
# THE BUDGET IS IN TWO HALVES, and saying so is the point — the previous version of
# this comment implied one number bounded everything, which stopped being true the
# moment the guards moved in-process.
#
# 1. The SUBPROCESS half is time-bounded:
#
#        max hold = SUBPROCESS_TIMEOUT_S x MAX_SUBPROCESS_CALLS_UNDER_LOCK
#                 = 20 x 2 = 40s, comfortably inside 300s.
#
#    The constant counts INVOCATION EDGES on the reachable call graph, not call
#    sites. There is exactly ONE `subprocess.run` site under the lock — inside
#    `_get_repo_root` — reached along two edges from `cmd_transition`: once via its
#    own `_resolve_spec_dir`, once directly. The `_locked` decorator's
#    `_resolve_spec_dir` runs BEFORE `sl.exclusive()` and is deliberately not
#    counted. It was 6 before the guards moved in-process, which was a conservative
#    bound over a measured maximum of five.
#
# 2. The IN-PROCESS half is byte-bounded, NOT time-bounded. Every file the guard
#    layer reads goes through `read_managed_json` / `read_managed_text`, capped at
#    8 MiB, and `canonical_contract` costs roughly 0.14 s/MiB — so about 1.0 s at
#    the cap. Guard calls are function calls and are deliberately NOT counted as
#    subprocesses; counting them would make the arithmetic describe something it
#    does not measure.
#
#    A byte cap bounds bytes, not seconds. `O_NONBLOCK` closes the reachable local
#    case — a FIFO or device swapped in after the type pre-check, which would
#    otherwise block `os.open` forever — but a stalled network mount can still block
#    `os.read`, and `_recover_pending` reads repo-global state under this same lock.
#    That residual is ACCEPTED and named rather than papered over: its only recovery
#    is the stale-lock reclaim, which is itself the hazard this budget exists to
#    prevent. There is no stdlib way to bound a blocking read without threads or
#    signals, and adding either under the lock would be a worse trade.
#
# `test_loop_concurrency.py`'s budget case derives all of this from source: it walks
# the locked call graph, fails if a subprocess call appears without a `timeout=`,
# fails if this constant disagrees with the edge count, and fails if the inequality
# breaks. Adding a guard cannot quietly break the arithmetic.
SUBPROCESS_TIMEOUT_S = 20.0
MAX_SUBPROCESS_CALLS_UNDER_LOCK = 2
SCHEMA_VERSION = 1
_LOOP_RUN_DIR_NAME = ".loop-run"

# Environment variables that could redirect git to a foreign repo root.
_GIT_OVERRIDE_VARS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
})

# ── FSM tables ─────────────────────────────────────────────────────────────
#
# Normative transition matrix.
# Key: (mode, source_state, event) → target_state
# "both" modes share the SPEC-PLAN-* states.

# ── repo-root helper ───────────────────────────────────────────────────────


# Control-character neutralisation for the engine's own diagnostics.
#
# A DELIBERATE second copy of `_loop_guards._CONTROL_ESCAPES`, and the duplication is
# the point: these warnings fire on paths where the guard module may be unavailable or
# unloadable, which is exactly when a diagnostic matters most. Reaching through
# `_guards()` here would make the sanitiser fail in the case it exists for.
#
# Not cosmetic. `_recover_engine_state_tmp` interpolates a filename that comes from a
# `glob()`, under the same planted-file threat model it already accepts for the file's
# CONTENT — so a `.engine-state-<ESC>[2J<ESC>[31mFAKE-OK.json.tmp` emitted a real
# screen-clear and colour change into the stream a supervising agent captures.
_CONTROL_ESCAPES = str.maketrans({c: f"\\x{c:02x}" for c in [*range(32), 127]})


def _diag(text: object) -> str:
    """One-line, control-character-safe text for a warning or refusal."""
    return " ".join(str(text).split()).translate(_CONTROL_ESCAPES)


def _get_repo_root() -> Path:
    safe_env = {k: v for k, v in os.environ.items() if k not in _GIT_OVERRIDE_VARS}
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", check=False,
            env=safe_env, timeout=SUBPROCESS_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        # Raised as ValueError because every caller already handles that; a bare
        # TimeoutExpired would surface as a traceback.
        raise ValueError(
            f"git rev-parse --show-toplevel timed out after "
            f"{SUBPROCESS_TIMEOUT_S:.0f}s"
        ) from exc
    if r.returncode != 0 or not r.stdout.strip():
        raise ValueError("could not determine repo root (git rev-parse --show-toplevel failed)")
    return Path(r.stdout.strip()).resolve()


# ── loop-run path helpers ───────────────────────────────────────────────────


def _loop_run_dir(repo_root: Path) -> Path:
    return repo_root / _LOOP_RUN_DIR_NAME


def _events_jsonl_path(repo_root: Path) -> Path:
    return _loop_run_dir(repo_root) / "events.jsonl"


def _events_pending_path(repo_root: Path) -> Path:
    return _loop_run_dir(repo_root) / "events.pending"


def _read_managed_json(path: Path, label: str) -> dict:
    """Delegate to the shared bounded reader.

    This was a byte-identical copy of `loop-cohort.py`'s. After this change the
    engine loads `_loop_guards` anyway, so a third copy of the bounded,
    symlink-safe, dev/ino-checked reader is exactly the drift AC3 forbids — and it
    would have been the one copy missing `O_NONBLOCK`.
    """
    return _guards().read_managed_json(path, label)


def _discard_regular_file(path: Path) -> bool:
    """Best-effort discard of an owned regular file, never a link or directory."""
    try:
        observed = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISREG(observed.st_mode):
        try:
            path.unlink()
        except OSError:
            return False
        return True
    return False


def _ensure_gitignore_entry(gitignore_path: Path, entry: str) -> None:
    """Append `entry` to `.gitignore` unless already present.

    Reached from `cmd_init`, which is `@_locked`, so the read happens inside the
    critical section. It used to be a plain `read_text()`: unbounded and BLOCKING, and
    the caller's `is_symlink()` pre-check does not exclude a FIFO. With the repo-root
    `.gitignore` as a FIFO, `init` hung indefinitely holding
    `engine-state.json.lock` — past `stale_after`, at which point the lock is
    reclaimed and a second writer admitted, which is exactly the lost update the lock
    exists to prevent. `O_NONBLOCK` in the shared reader is what closes it, so this
    goes through the reader rather than around it.

    A read failure raises; the sole caller already wraps this in a warning, and
    skipping the gitignore courtesy is the right degradation — it is a convenience,
    not a correctness control.
    """
    try:
        existing = _guards().read_managed_text(gitignore_path, ".gitignore")
    except FileNotFoundError:
        existing = ""
    if entry in existing.splitlines():
        return
    with gitignore_path.open("a", encoding="utf-8") as fh:
        if existing and not existing.endswith("\n"):
            fh.write("\n")
        fh.write(entry + "\n")


def _write_events_pending(repo_root: Path, pending_data: dict) -> None:
    pending_path = _events_pending_path(repo_root)
    loop_run_dir = pending_path.parent
    if loop_run_dir.is_symlink() or pending_path.is_symlink():
        raise OSError(f"refusing to write: loop-run path is a symlink ({pending_path})")
    fd, tmp = tempfile.mkstemp(
        prefix=".events-pending-", suffix=".tmp", dir=str(loop_run_dir)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(pending_data, fh)
            fh.write("\n")
        Path(tmp).replace(pending_path)
    except Exception:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


def _open_regular_event_log(path: Path) -> tuple[int, tuple[int, int]]:
    """Open or create an event log without following or racing a symlink."""
    flags = os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    for _attempt in range(2):
        try:
            before = os.lstat(path)
        except FileNotFoundError:
            try:
                fd = os.open(path, flags | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            except OSError as exc:
                raise OSError(f"event log cannot be created safely: {exc}") from exc
            opened = os.fstat(fd)
            identity = (opened.st_dev, opened.st_ino)
        except OSError as exc:
            raise OSError(f"event log cannot be examined: {exc}") from exc
        else:
            if not stat.S_ISREG(before.st_mode):
                raise OSError(f"event log must be a regular file ({path})")
            identity = (before.st_dev, before.st_ino)
            try:
                fd = os.open(path, flags)
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise OSError(f"event log cannot be opened safely: {exc}") from exc
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or (
                opened.st_dev,
                opened.st_ino,
            ) != identity:
                os.close(fd)
                raise OSError(f"event log changed while being opened ({path})")
        try:
            after_path = os.lstat(path)
        except OSError as exc:
            os.close(fd)
            raise OSError(f"event log changed while being opened ({path})") from exc
        if not stat.S_ISREG(after_path.st_mode) or (
            after_path.st_dev,
            after_path.st_ino,
        ) != identity:
            os.close(fd)
            raise OSError(f"event log changed while being opened ({path})")
        return fd, identity
    raise OSError(f"event log changed while being opened ({path})")


def _append_events_jsonl(repo_root: Path, event_data: dict) -> None:
    path = _events_jsonl_path(repo_root)
    loop_run_dir = path.parent
    if loop_run_dir.is_symlink():
        raise OSError(f"refusing to write: loop-run path is a symlink ({path})")
    fd, identity = _open_regular_event_log(path)
    with os.fdopen(fd, "a+b") as fh:
        # Repair a torn tail: if the last byte is not '\n', a previous crash
        # left a partial line. Write a bare newline to isolate it so the new
        # event is parsed as a separate record, not concatenated to the fragment.
        if fh.seek(0, 2) > 0:  # seek to end; pos > 0 means file is non-empty
            fh.seek(-1, 2)
            if fh.read(1) != b"\n":
                fh.write(b"\n")
        fh.write((json.dumps(event_data) + "\n").encode())
        fh.flush()
        after_fd = os.fstat(fh.fileno())
        try:
            after_path = os.lstat(path)
        except OSError as exc:
            raise OSError(f"event log changed while being written ({path})") from exc
        if (
            (after_fd.st_dev, after_fd.st_ino) != identity
            or (after_path.st_dev, after_path.st_ino) != identity
        ):
            raise OSError(f"event log changed while being written ({path})")


def _is_content_invalid(exc: BaseException) -> bool:
    """Is this failure "the bytes are unusable" rather than "the read failed"?

    Gates the DELETION of `events.pending`, a durable audit record, so getting it
    wrong in the permissive direction destroys evidence. Asks the reader's own
    exception hierarchy — `ManagedContentError` — rather than substring-matching
    `str(exc)` against a hand-listed set of message fragments, which is what this did
    at both call sites. That list had already fallen behind the reader: it omitted the
    non-finite-number message, so a `NaN` in `events.pending` was never recognised as
    invalid content and the file was retained forever, re-warning on every transition.

    Resolved through the loaded guard module, not imported, because the engine loads
    that module by path. A load failure is deliberately NOT content-invalid: it says
    nothing about this file, and discarding a valid audit record over a build problem
    is the data loss this function exists to prevent.
    """
    try:
        return isinstance(exc, _guards().ManagedContentError)
    except GuardsUnavailable:
        return False


class _MissingRequiredFields(ValueError):
    """A promoted engine-state tmp parsed but lacks `state` or `run_id`.

    A distinct class rather than a bare `ValueError`, so the delete decision can be
    `isinstance`-based end to end: this IS invalid content (the tool wrote it and it
    is unusable), while the reader's structural `ValueError`s are not.
    """


def _recover_engine_state_tmp(spec_dir: Path) -> None:
    """Complete any crash-left atomic engine-state rename; validate JSON before promoting."""
    for tmp_path in spec_dir.glob(".engine-state-*.json.tmp"):
        try:
            data = _read_managed_json(tmp_path, "engine-state tmp")
            if not isinstance(data, dict) or not data.get("state") or not data.get("run_id"):
                raise _MissingRequiredFields(
                    "engine-state tmp is missing required fields"
                )
        except FileNotFoundError:
            continue
        except BaseException as exc:  # noqa: BLE001 — see below; nothing may escape
            # TWO separate decisions here, and conflating them caused a bug in each
            # direction on this line already.
            #
            # 1. WHAT IS CAUGHT: everything. An earlier revision narrowed this to
            #    `(FileNotFoundError, ValueError)`, which missed `RecursionError` —
            #    `json.loads` raises it on a deeply nested document, it is not a
            #    `ValueError`, and `main()` catches only `GuardsUnavailable` and
            #    `KeyboardInterrupt`. So a planted `.engine-state-*.json.tmp` holding
            #    20k nested arrays produced a traceback from inside
            #    `sl.exclusive(...)`, and because the dotfile was never removed, EVERY
            #    later transition on that spec failed identically. Reproduced.
            #
            # 2. WHAT AUTHORISES THE DELETE: only invalid content. `_read_managed_json`
            #    goes through the shared reader, so it can fail for reasons that say
            #    nothing about this file — `GuardsUnavailable` from a missing guard
            #    module, a permission error, a benign concurrent-writer race. Treating
            #    those as "content invalid" unlinked a byte-perfect crash-recovery
            #    artifact; observed. The two conditions co-occur naturally (an
            #    interrupted `make build-self` plus a crash-left rename) and the loss
            #    is irreversible.
            #
            # Catching broadly while deleting narrowly is what satisfies both.
            if isinstance(exc, KeyboardInterrupt):
                raise
            invalid = isinstance(exc, _MissingRequiredFields) or _is_content_invalid(exc)
            if invalid:
                with contextlib.suppress(OSError):
                    tmp_path.unlink(missing_ok=True)
            print(
                f"loop-engine: warning — engine-state tmp unusable "
                f"({type(exc).__name__}: {_diag(exc)}); "
                + (f"discarding {_diag(tmp_path.name)}" if invalid
                   else f"{_diag(tmp_path.name)} left in place; remove manually"),
                file=sys.stderr,
            )
            continue
        try:
            tmp_path.replace(spec_dir / "engine-state.json")
        except OSError as exc:
            print(
                f"loop-engine: warning — could not promote engine-state tmp ({_diag(exc)})",
                file=sys.stderr,
            )
        break  # only one tmp at a time


def _recover_pending(repo_root: Path) -> None:
    """Replay or discard a stale events.pending if one exists."""
    try:
        loop_run_observed = os.lstat(_loop_run_dir(repo_root))
    except FileNotFoundError:
        return
    except OSError as exc:
        print(
            f"loop-engine: warning — could not examine .loop-run ({exc}); "
            "recovery skipped",
            file=sys.stderr,
        )
        return
    if not stat.S_ISDIR(loop_run_observed.st_mode):
        print(
            "loop-engine: warning — .loop-run must be a directory, not a link "
            "or other file; recovery skipped",
            file=sys.stderr,
        )
        return

    pending_path = _events_pending_path(repo_root)
    try:
        os.lstat(pending_path)
    except FileNotFoundError:
        return
    try:
        pending = _read_managed_json(pending_path, "events.pending")
    except Exception as exc:
        content_invalid = _is_content_invalid(exc)
        action = (
            "discarded"
            if content_invalid and _discard_regular_file(pending_path)
            else "left in place; remove manually"
        )
        print(
            f"loop-engine: warning — could not parse events.pending ({_diag(exc)}); {action}",
            file=sys.stderr,
        )
        return

    # Validate owning spec path — must not escape repo root.
    spec_str = pending.get("spec", "")
    try:
        _spec_path_obj = Path(spec_str)
        # Relative paths (written since the repo-relative fix) are resolved against
        # repo_root; absolute paths (legacy pending files) are resolved as-is.
        if _spec_path_obj.is_absolute():
            pending_spec_dir = _spec_path_obj.resolve()
        else:
            pending_spec_dir = (repo_root / spec_str).resolve()
        pending_spec_dir.relative_to(repo_root)
    except Exception as exc:
        action = (
            "discarded"
            if _discard_regular_file(pending_path)
            else "left in place; remove manually"
        )
        print(
            f"loop-engine: warning — events.pending spec path invalid ({_diag(exc)}); {action}",
            file=sys.stderr,
        )
        return

    # Complete any in-progress atomic engine-state.json rename (crash during step 3).
    _recover_engine_state_tmp(pending_spec_dir)

    # Load owning spec's engine-state.json.
    owning_state_path = pending_spec_dir / "engine-state.json"
    try:
        owning_state = _read_managed_json(owning_state_path, "engine-state.json")
    except FileNotFoundError:
        _discard_regular_file(pending_path)
        return
    except Exception as exc:
        # Only a genuine CONTENT problem may authorise discarding the audit record —
        # the same discrimination the events.pending read above already makes.
        # `_read_managed_json` delegates to the shared reader now, so it can raise for
        # reasons unrelated to this file (a `GuardsUnavailable` when `_loop_guards.py`
        # cannot be loaded), and discarding `events.pending` over a build problem
        # would destroy a durable audit record.
        content_invalid = _is_content_invalid(exc)
        action = (
            "discarded"
            if content_invalid and _discard_regular_file(pending_path)
            else "left in place; remove manually"
        )
        print(
            f"loop-engine: warning — could not parse owning engine-state.json ({_diag(exc)});"
            f" pending {action}",
            file=sys.stderr,
        )
        return

    # Replay if state+seq+run_id all match (engine-state.json was written but append was not).
    if (
        pending.get("to") == owning_state.get("state")
        and pending.get("seq") == owning_state.get("transition_sequence")
        and pending.get("run_id") == owning_state.get("run_id")
    ):
        try:
            _append_events_jsonl(repo_root, pending)
            pending_path.unlink(missing_ok=True)
        except Exception as exc:
            print(
                f"loop-engine: warning — could not replay events.pending ({exc})",
                file=sys.stderr,
            )
    else:
        with contextlib.suppress(OSError):
            pending_path.unlink(missing_ok=True)


# ── FSM tables ─────────────────────────────────────────────────────────────
#
# Normative transition matrix.
# Key: (mode, source_state, event) → target_state
# "both" modes share the SPEC-PLAN-* states.

_BOTH_TRANSITIONS = {
    ("SPEC-PLAN-DRAFTING", "spec-ready"): "SPEC-PLAN-REVIEW",
    ("SPEC-PLAN-REVIEW", "reviewers-clean"): "SPEC-HUMAN-GATE",
    ("SPEC-PLAN-REVIEW", "findings-remain"): "SPEC-PLAN-DRAFTING",
    ("SPEC-HUMAN-GATE", "spec-approved"): "PLAN-HUMAN-GATE",
    ("SPEC-HUMAN-GATE", "spec-rejected"): "SPEC-PLAN-DRAFTING",
    ("PLAN-HUMAN-GATE", "plan-approved"): "SPEC-PLAN-APPROVED",
    ("PLAN-HUMAN-GATE", "plan-rejected"): "SPEC-PLAN-DRAFTING",
}

_CODE_TRANSITIONS = {
    **_BOTH_TRANSITIONS,
    ("SPEC-PLAN-APPROVED", "plan-locked"): "CODE-IMPLEMENTATION",
    ("CODE-IMPLEMENTATION", "contract-amendment"): "SPEC-PLAN-DRAFTING",
    ("CODE-IMPLEMENTATION", "wave-complete"): "CODE-VERIFICATION",
    ("CODE-VERIFICATION", "wave-passed"): "CODE-IMPLEMENTATION",
    ("CODE-VERIFICATION", "gates-clean"): "CODE-REVIEW",
    ("CODE-VERIFICATION", "gates-failed"): "CODE-IMPLEMENTATION",
    ("CODE-REVIEW", "reviewers-clean"): "CODE-HUMAN-GATE",
    ("CODE-REVIEW", "findings-remain"): "CODE-IMPLEMENTATION",
    ("CODE-HUMAN-GATE", "done"): "DONE",
    ("CODE-HUMAN-GATE", "blocker-applied"): "CODE-IMPLEMENTATION",
}

_SPEC_PLAN_TRANSITIONS = {
    **_BOTH_TRANSITIONS,
    ("SPEC-PLAN-APPROVED", "plan-locked"): "DONE",
}

_TRANSITIONS_BY_MODE = {
    "code": _CODE_TRANSITIONS,
    "spec-plan": _SPEC_PLAN_TRANSITIONS,
}

# States where pending_human_wait is True
_HUMAN_WAIT_STATES = frozenset({"SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"})

# Gate questions surfaced to the control plane via engine-state.json["gate_question"]
_GATE_QUESTIONS: dict[str, str] = {
    "SPEC-HUMAN-GATE": "Does this spec define the right thing to build?",
    "PLAN-HUMAN-GATE": "Does this plan describe the right way to build it?",
    "CODE-HUMAN-GATE": "Are these changes correct and ready to merge?",
}

# CODE-* states that require the mandatory schedule check-current pre-guard,
# EXCEPT "done" which is exempt.
_CODE_STATES = frozenset({
    "CODE-IMPLEMENTATION", "CODE-VERIFICATION", "CODE-REVIEW", "CODE-HUMAN-GATE"
})
_DONE_EXEMPT_FROM_SCHEDULE_GUARD = frozenset({"done"})

# ── guards ─────────────────────────────────────────────────────────────────
#
# Each entry: (mode, event) → guard_call_fn(spec_dir, engine_state, event_args)
# Guard functions return None on success, or a non-empty error string on failure.


class GuardsUnavailable(RuntimeError):
    """`_loop_guards.py` could not be loaded; every verb must refuse."""


_guards_module: object | None = None
_cohort_mutator_module: object | None = None


def _guards():
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


def _cohort_mutator():
    """Load the sibling cohort writer for the cross-state amendment mutation."""
    global _cohort_mutator_module
    if _cohort_mutator_module is not None:
        return _cohort_mutator_module
    path = SCRIPT_DIR / "loop-cohort.py"
    try:
        observed = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"cannot load {path}: {exc}") from exc
    if not stat.S_ISREG(observed.st_mode):
        raise ImportError(
            f"cannot load {path}: not a regular file (symlink or device)"
        )
    previous = sys.dont_write_bytecode
    module_name = "_work_loop_cohort_mutator"
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}: no import spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    if not getattr(module, "_MODULE_COMPLETE", False):
        sys.modules.pop(module_name, None)
        raise ImportError(f"cannot load {path}: module is incomplete")
    required = {
        "apply_contract_amendment",
        "contract_amendment_replay_status",
        "parse_completed_task_evidence_entries",
    }
    missing = sorted(required - set(dir(module)))
    if missing:
        sys.modules.pop(module_name, None)
        raise ImportError(
            f"cannot load {path}: missing required amendment symbols "
            + ", ".join(missing)
        )
    _cohort_mutator_module = module
    return module


# Each entry: (mode, event) → guard_fn(spec_dir, engine_state, event_args).
# Guard functions return None on success, or a non-empty error string on failure —
# the convention that predates this change and that `cmd_transition` still reads.
#
# Every one of these used to be `_run([sys.executable, LOOP_COHORT, ...])`. The
# decisions now come from `_loop_guards`, so a transition is one interpreter. The
# engine's own prefix is preserved verbatim on each; what disappeared is the nested
# `loop-cohort: stop — ` / `check-spec-status: ` marker that only existed because a
# child process's stderr was being captured.


def _guard_reason(prefix: str, result) -> str | None:
    """Compose the engine's error text from a GuardResult.

    Branches on `ok`, never on `reason` — an `ok=False, reason=None` result would
    otherwise read as success, and `GuardResult` raises rather than allowing that
    combination in the first place.
    """
    if result.ok:
        return None
    return f"{prefix}: {result.reason}"


def _guard_check_phase_implement(spec_dir: Path, engine_state: dict, _) -> str | None:
    return _guard_reason(
        "check --phase implement failed",
        _guards().check_phase(spec_dir, phase="implement"),
    )


def _guard_check_phase_gates_failed(spec_dir: Path, engine_state: dict, _) -> str | None:
    return _guard_reason(
        "check --phase gates-failed failed",
        _guards().check_phase(spec_dir, phase="gates-failed"),
    )


def _guard_wave_check_more(spec_dir: Path, engine_state: dict, event_args: dict) -> str | None:
    wave_index = event_args.get("wave_index")
    if wave_index is None:
        return "wave-passed requires --wave-index"
    return _guard_reason(
        f"wave check --expect more --wave-index {wave_index} failed",
        _guards().check_wave(spec_dir, expect="more", wave_index=wave_index),
    )


def _guard_wave_check_last(spec_dir: Path, engine_state: dict, _) -> str | None:
    return _guard_reason(
        "wave check --expect last failed",
        _guards().check_wave(spec_dir, expect="last"),
    )


def _guard_check_phase_review(
    spec_dir: Path, engine_state: dict, event_args: dict
) -> str | None:
    override = event_args.get("allow_retry_cap_override", False)
    err = _guard_reason(
        "check --phase review failed",
        _guards().check_phase(
            spec_dir, phase="review", allow_review_retry_cap_override=override,
        ),
    )
    # The shared reason names no flag, because `loop-cohort check` prints it too
    # and accepts none. This adapter does accept one, so it adds the remedy here
    # -- including the second half, which is the part that is easy to miss.
    if err and not override and "review retry cap reached" in err:
        err += (
            " — that is the default answer, because a cap firing means the loop "
            "stopped converging. Only a human directing this run may continue "
            "past it, by passing --allow-retry-cap-override to this transition "
            "AND to the matching `loop-cohort review record`; either half alone "
            "leaves the cohort and the engine a round apart"
        )
    return err


def _guard_check_spec_status(
    spec_dir: Path, engine_state: dict, event_args: dict
) -> str | None:
    """Require the status declared by the review unit's intent boundary."""
    expect = "Implementing" if event_args.get("intent_incomplete", False) else "Shipped"
    return _guard_reason(
        "check-spec-status failed",
        _guards().check_artifact_status(spec_dir, filename="spec.md", expect=expect),
    )


def _guard_done(spec_dir: Path, engine_state: dict, _) -> str | None:
    """Guard done: the accepted intent's spec must be Shipped.

    Before intent-scoped completion this held transitively — the only route into
    CODE-HUMAN-GATE required Shipped. An intermediate unit may now enter that
    state at Implementing, so DONE asserts completion explicitly instead.
    """
    return _guard_reason(
        "check-spec-status --expect Shipped failed",
        _guards().check_artifact_status(spec_dir, filename="spec.md", expect="Shipped"),
    )


def _guard_spec_approved(spec_dir: Path, engine_state: dict, _) -> str | None:
    """Guard for spec-approved: spec.md must have Status: Approved."""
    return _guard_reason(
        "check-spec-status --expect Approved failed",
        _guards().check_artifact_status(spec_dir, filename="spec.md", expect="Approved"),
    )


def _guard_plan_approved(spec_dir: Path, engine_state: dict, _) -> str | None:
    """Guard for plan-approved: plan.md must have Status: Approved."""
    return _guard_reason(
        "check-spec-status --expect Approved --file plan.md failed",
        _guards().check_artifact_status(spec_dir, filename="plan.md", expect="Approved"),
    )


def _guard_plan_locked_code(spec_dir: Path, engine_state: dict, _) -> str | None:
    """plan-locked (code mode): spec Approved, then plan check-current --require-schedule.

    Two checks in the same order as before — they were two child processes and are
    now two function calls.
    """
    err = _guard_reason(
        "check-spec-status --expect Approved failed",
        _guards().check_artifact_status(spec_dir, filename="spec.md", expect="Approved"),
    )
    if err:
        return err
    return _guard_reason(
        "plan check-current --require-schedule failed",
        _guards().check_plan_current(spec_dir, require_schedule=True),
    )


def _guard_plan_locked_spec_plan(spec_dir: Path, engine_state: dict, _) -> str | None:
    """plan-locked (spec-plan mode): spec Approved, then plan check-current."""
    err = _guard_reason(
        "check-spec-status --expect Approved failed",
        _guards().check_artifact_status(spec_dir, filename="spec.md", expect="Approved"),
    )
    if err:
        return err
    return _guard_reason(
        "plan check-current failed",
        _guards().check_plan_current(spec_dir, require_schedule=False),
    )


def _guard_check_spec_status_on_code_review(
    spec_dir: Path, engine_state: dict, event_args: dict
) -> str | None:
    # reviewers-clean fires in both SPEC-PLAN-REVIEW and CODE-REVIEW; the
    # shipped-status guard applies only on the CODE-REVIEW → CODE-HUMAN-GATE edge.
    if engine_state.get("state") != "CODE-REVIEW":
        return None
    return _guard_check_spec_status(spec_dir, engine_state, event_args)


# Guard dispatch: (mode, event) → guard_fn | None
_GUARDS: dict[tuple[str, str], object] = {
    ("code", "spec-approved"): _guard_spec_approved,
    ("spec-plan", "spec-approved"): _guard_spec_approved,
    ("code", "plan-approved"): _guard_plan_approved,
    ("spec-plan", "plan-approved"): _guard_plan_approved,
    ("code", "plan-locked"): _guard_plan_locked_code,
    ("spec-plan", "plan-locked"): _guard_plan_locked_spec_plan,
    ("code", "wave-complete"): _guard_check_phase_implement,
    ("code", "gates-failed"): _guard_check_phase_gates_failed,
    ("code", "wave-passed"): _guard_wave_check_more,
    ("code", "gates-clean"): _guard_wave_check_last,
    ("code", "findings-remain"): _guard_check_phase_review,
    ("spec-plan", "findings-remain"): _guard_check_phase_review,
    ("code", "reviewers-clean"): _guard_check_spec_status_on_code_review,
    ("code", "done"): _guard_done,
}

# ── engine-state.json helpers ──────────────────────────────────────────────


def _engine_state_path(spec_dir: Path) -> Path:
    return spec_dir / "engine-state.json"


def _read_engine_state(spec_dir: Path) -> dict:
    path = _engine_state_path(spec_dir)
    try:
        return _read_managed_json(path, "engine-state.json")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"engine-state.json missing at {path}") from exc


def _write_engine_state_atomic(spec_dir: Path, state: dict) -> None:
    path = _engine_state_path(spec_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".engine-state-", suffix=".json.tmp", dir=str(path.parent)
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


def _resolve_spec_dir(raw: str) -> Path:
    # Confine to the repo root so absolute or out-of-tree paths are rejected.
    # Strip GIT_DIR / GIT_WORK_TREE so a caller-controlled environment cannot
    # redirect git to report "/" as the toplevel, bypassing this check.
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


def stop(reason: str, code: int = 1) -> int:
    print(f"loop-engine: stop — {_diag(reason)}", file=sys.stderr)
    return code


# ── state lock ────────────────────────────────────────────────────────────

# `_write_engine_state_atomic` makes each *write* atomic, but the
# read-decide-write around it is not. Two concurrent transitions both validate
# against the same `current_state`, so BOTH are admitted where the second must
# fail `illegal transition`, both compute the same `transition_sequence`, and the
# durable outbox records the collision. Reproduced at 10/10 trials; see
# docs/specs/loop-cohort-state-lock/notes/reproduction.md.
#
# `_statelock.py` is a work-loop script owned by this skill (ADR-0074):
# stdlib-only, so it works where `agentbundle` is not installed. `agentbundle`
# has its own, separate lock for the installer's state.toml.
_statelock_module: object | None = None


def _statelock():
    """Load the sibling `_statelock.py` by path.

    By path, not `import _statelock`: a plain import resolves under file-path
    invocation but not under an importlib-based harness, which does not put this
    directory on `sys.path` — and the concurrency suites are exactly that.
    """
    global _statelock_module
    if _statelock_module is None:
        lock_path = SCRIPT_DIR / "_statelock.py"
        # `sys.dont_write_bytecode` around the load, saved and restored to its
        # PRIOR value rather than unconditionally to False — mirroring the
        # `_loop_guards` loader above. Without it this import writes and later
        # READS `__pycache__/_statelock.*.pyc`, and a poisoned or stale entry
        # executes inside the lock-holding engine process. One that made
        # `exclusive()` a no-op would be worse than one that made a guard lie:
        # it would admit a second writer while both believe they hold the lock.
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec = importlib.util.spec_from_file_location("_statelock", str(lock_path))
            if spec is None or spec.loader is None:
                raise ImportError(f"loop-engine: cannot load {lock_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
        _statelock_module = module
    return _statelock_module


def _locked(verb: str):
    """Hold the engine-state lock across the whole decorated verb.

    For `transition` the section deliberately spans the FSM table lookup, the
    plan-hash pre-guard, the event guard AND the outbox finalisation — not just
    the state write. Releasing at the write leaves a reachable duplicate-event
    interleaving for the *same* spec: A writes events.pending, writes
    engine-state, releases; B acquires, `_recover_pending` matches on
    to/seq/run_id and replays A's event; B refuses; A then appends its own record
    again.

    Every lock failure becomes a `stop()` refusal — non-zero, one line, no
    traceback, never an unlocked write.
    """
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(args: argparse.Namespace) -> int:
            try:
                spec_dir = _resolve_spec_dir(args.spec_dir)
            except ValueError as exc:
                return stop(str(exc))
            try:
                sl = _statelock()
            except (ImportError, OSError) as exc:
                # Refuse, never traceback — see loop-cohort.py's twin.
                return stop(f"{verb}: state lock unavailable: {exc}")
            try:
                with sl.exclusive(_engine_state_path(spec_dir)):
                    return fn(args)
            except sl.StateLockError as exc:
                return stop(f"{verb}: {exc}")
        return wrapper
    return decorate


# ── init ───────────────────────────────────────────────────────────────────


@_locked("init")
def cmd_init(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))

    engine_path = _engine_state_path(spec_dir)
    if engine_path.exists():
        return stop(
            f"engine-state.json already exists at {engine_path}; "
            "run 'loop-engine reset' first (engine-orphan: prior init incomplete)"
        )

    run_id = str(_uuid_mod.uuid4())
    feature = spec_dir.name
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "feature": feature,
        "mode": args.mode,
        "state": "SPEC-PLAN-DRAFTING",
        "last_event": None,
        "last_event_context": None,
        "transition_sequence": 0,
        "last_transition_at": now,
    }
    _write_engine_state_atomic(spec_dir, state)

    # Initialize .loop-run/ and recover any stale pending (all graceful).
    try:
        repo_root = _get_repo_root()
    except Exception as exc:
        print(f"loop-engine: warning — could not determine repo root: {exc}", file=sys.stderr)
        repo_root = None

    if repo_root is not None:
        try:
            loop_run = _loop_run_dir(repo_root)
            if loop_run.is_symlink():
                print(
                    "loop-engine: warning — .loop-run/ is a symlink; refusing to initialise",
                    file=sys.stderr,
                )
            else:
                loop_run.mkdir(exist_ok=True)
                jsonl = _events_jsonl_path(repo_root)
                event_fd, _ = _open_regular_event_log(jsonl)
                os.close(event_fd)
                gitignore = repo_root / ".gitignore"
                if not gitignore.is_symlink():
                    # Its OWN handler. Sharing the outer one reported "could not
                    # initialise .loop-run/" for a failure in which `.loop-run/`, the
                    # event log and the state write had all succeeded and only the
                    # gitignore courtesy failed — sending an operator to the wrong
                    # place. It is a convenience, so skipping it is the right
                    # degradation, but it must say what it actually skipped.
                    try:
                        _ensure_gitignore_entry(gitignore, ".loop-run/")
                    except Exception as exc:  # noqa: BLE001 — a courtesy, never fatal
                        print(
                            "loop-engine: warning — could not add .loop-run/ to "
                            f".gitignore ({_diag(exc)}); add it manually",
                            file=sys.stderr,
                        )
        except Exception as exc:
            print(
                f"loop-engine: warning — could not initialise .loop-run/: {exc}",
                file=sys.stderr,
            )
        try:
            _recover_pending(repo_root)
        except Exception as exc:
            print(f"loop-engine: warning — pending recovery failed: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps({"run_id": run_id, "feature": feature, "mode": args.mode}))
    else:
        print(
            f"loop-engine: initialised {engine_path} "
            f"(feature={feature} mode={args.mode} run_id={run_id})"
        )
    return 0


# ── reset ──────────────────────────────────────────────────────────────────


@_locked("reset")
def cmd_reset(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    path = _engine_state_path(spec_dir)
    if path.exists():
        path.unlink()
        print(f"loop-engine: deleted {path}")
    else:
        print(f"loop-engine: reset — engine-state.json already absent at {path}")

    # Remove .loop-run/ (graceful — failure is a warning only).
    try:
        repo_root = _get_repo_root()
        loop_run = _loop_run_dir(repo_root)
        if loop_run.exists():
            # Repo-global, like _recover_pending in cmd_transition: this wipes
            # the outbox for EVERY spec while holding only this spec's lock. A
            # per-spec lock cannot serialise it. Tracked as backlog:
            # loop-outbox-cross-spec-rmw.
            shutil.rmtree(loop_run)
            print(f"loop-engine: removed {loop_run}")
        else:
            print(f"loop-engine: reset — .loop-run/ already absent at {loop_run}")
    except Exception as exc:
        print(f"loop-engine: warning — could not remove .loop-run/: {exc}", file=sys.stderr)

    return 0


# ── status ─────────────────────────────────────────────────────────────────


def cmd_status(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = _read_engine_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    if state.get("schema_version") != SCHEMA_VERSION:
        sv = state.get("schema_version")
        return stop(f"status: unsupported schema_version={sv!r} (expected {SCHEMA_VERSION})")

    result = dict(state)
    result["pending_human_wait"] = state.get("state") in _HUMAN_WAIT_STATES
    if args.json:
        print(json.dumps(result))
    else:
        print(f"loop-engine status for {spec_dir.name}:")
        for k, v in result.items():
            print(f"  {k}: {v!r}")
    return 0


# ── transition ─────────────────────────────────────────────────────────────


def _run_id_preflight(spec_dir: Path, engine_run_id: str) -> str | None:
    """Engine/cohort run-ID pairing. In-process; was `loop-cohort.py identity`."""
    return _guard_reason(
        "run_id preflight failed",
        _guards().check_identity(spec_dir, expect_run_id=engine_run_id),
    )


def _schedule_check_current(spec_dir: Path) -> str | None:
    """Scheduled-plan currency. In-process; was `loop-cohort.py schedule check-current`."""
    return _guard_reason(
        "schedule check-current failed",
        _guards().check_schedule_current(spec_dir),
    )


def _contract_amendment_id(
    run_id: str,
    sequence: int,
    owner_authority_ref: str,
    reason_ref: str,
    completed_task_evidence: dict[str, list[str]],
) -> str:
    evidence = json.dumps(
        completed_task_evidence,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    material = (
        f"{run_id}\0{sequence}\0{owner_authority_ref}\0{reason_ref}\0{evidence}"
    )
    return "amendment-" + hashlib.sha256(material.encode("utf-8")).hexdigest()


@_locked("transition")
def cmd_transition(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))

    event = args.event
    wave_index = args.wave_index
    intent_incomplete = args.intent_incomplete
    allow_retry_cap_override = getattr(args, "allow_retry_cap_override", False)
    owner_authority_ref = args.owner_authority_ref
    reason_ref = args.reason_ref
    completed_evidence_entries = tuple(args.completed_evidence_ref or [])
    completed_task_evidence: dict[str, list[str]] = {}

    # Validate --wave-index usage
    if event == "wave-passed":
        if wave_index is None:
            return stop("transition wave-passed requires --wave-index")
    else:
        if wave_index is not None:
            return stop(f"transition {event!r} does not accept --wave-index")
    if intent_incomplete and event != "reviewers-clean":
        return stop("transition --intent-incomplete requires reviewers-clean")
    if allow_retry_cap_override and event != "findings-remain":
        return stop("transition --allow-retry-cap-override requires findings-remain")
    if event == "contract-amendment":
        if not owner_authority_ref:
            return stop("transition contract-amendment requires --owner-authority-ref")
        if not reason_ref:
            return stop("transition contract-amendment requires --reason-ref")
        try:
            completed_task_evidence = (
                _cohort_mutator().parse_completed_task_evidence_entries(
                    completed_evidence_entries
                )
            )
        except Exception as exc:
            return stop(f"contract-amendment evidence invalid: {_diag(exc)}")
    elif owner_authority_ref or reason_ref or completed_evidence_entries:
        return stop(
            f"transition {event!r} does not accept contract-amendment evidence"
        )

    # recover at command start — before any early-exit check.
    # _recover_engine_state_tmp promotes crash-left .tmp → engine-state.json.
    # _recover_pending replays or discards a stale events.pending from a prior crash.
    # Both must run before _read_engine_state so a recovered state is read correctly,
    # and before early returns so a pending file is never left behind by validation failures.
    _recover_engine_state_tmp(spec_dir)
    _cmd_transition_repo_root: Path | None = None
    try:
        _cmd_transition_repo_root = _get_repo_root()
        # NOTE: this runs inside the critical section but is NOT protected
        # by it. It reads the repo-global events.pending and then calls
        # _recover_engine_state_tmp on whatever spec THAT record names, so
        # it can reach another spec's engine-state while we hold only this
        # spec's lock. A per-spec lock cannot serialise a repo-global
        # resource. Tracked as backlog: loop-outbox-cross-spec-rmw.
        _recover_pending(_cmd_transition_repo_root)
    except Exception as exc:
        print(f"loop-engine: warning — pending recovery failed: {exc}", file=sys.stderr)

    # Read engine-state.json
    try:
        state = _read_engine_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    if state.get("schema_version") != SCHEMA_VERSION:
        sv = state.get("schema_version")
        return stop(f"transition: unsupported schema_version={sv!r} (expected {SCHEMA_VERSION})")

    mode = state["mode"]
    current_state = state["state"]
    run_id = state["run_id"]

    if intent_incomplete and current_state != "CODE-REVIEW":
        return stop("transition --intent-incomplete requires CODE-REVIEW")

    # Step 0: run_id preflight (all transitions)
    err = _run_id_preflight(spec_dir, run_id)
    if err:
        return stop(err)

    # Recovery for a divergence between the two per-spec scratch files, where
    # engine-state records the amendment at drafting but the cohort state does
    # not. Reissuing the exact event completes only the missing cohort write and
    # does not increment the transition sequence.
    #
    # Note this is NOT the ordinary crash window. `cmd_transition` mutates the
    # cohort first and writes engine-state last, so a crash between them always
    # leaves the cohort ahead, never behind — that direction is handled on the
    # normal path by `contract_amendment_replay_status`. Reaching this branch
    # requires the two untracked files to have diverged by some other means, so
    # the plan cannot be assumed to still match what was approved.
    if (
        event == "contract-amendment"
        and mode == "code"
        and current_state == "SPEC-PLAN-DRAFTING"
        and state.get("last_event") == "contract-amendment"
    ):
        context = state.get("last_event_context") or {}
        amendment_id = _contract_amendment_id(
            run_id,
            int(state.get("transition_sequence", 0)),
            owner_authority_ref,
            reason_ref,
            completed_task_evidence,
        )
        if (
            context.get("amendment_id") != amendment_id
            or context.get("owner_authority_ref") != owner_authority_ref
            or context.get("reason_ref") != reason_ref
            or context.get("completed_task_evidence", {})
            != completed_task_evidence
        ):
            return stop("contract-amendment replay facts do not match engine state")
        # The engine-side facts above only prove the caller reissued the same
        # event. They say nothing about `plan.md`, and this branch does not fall
        # through to Step 1b, so without this check the cohort mutation reaches
        # its derive path — `task_section_hashes` over whatever the plan now
        # holds — and an edit to an already-completed task section is laundered
        # into the baseline that `validate_completed_task_sections` later
        # ratifies. Verify the plan still matches the scheduled baseline first;
        # canonical form normalises the status token and checkbox brackets, so
        # ordinary task check-offs do not trip it.
        err = _schedule_check_current(spec_dir)
        if err:
            return stop(err)
        try:
            _cohort_mutator().apply_contract_amendment(
                spec_dir,
                expected_run_id=run_id,
                owner_authority_ref=owner_authority_ref,
                reason_ref=reason_ref,
                completed_task_evidence=completed_task_evidence,
                amendment_id=amendment_id,
            )
        except Exception as exc:
            return stop(f"contract-amendment cohort recovery failed: {_diag(exc)}")
        print(
            f"loop-engine: contract-amendment replay completed cohort state "
            f"for {spec_dir.name}"
        )
        return 0

    # Step 1: validate event against FSM for current mode × state
    table = _TRANSITIONS_BY_MODE.get(mode, {})
    key = (current_state, event)
    if key not in table:
        return stop(
            f"illegal transition: mode={mode!r} state={current_state!r} event={event!r}"
        )
    next_state = table[key]

    cohort_amendment_already_applied = False
    if event == "contract-amendment":
        expected_amendment_id = _contract_amendment_id(
            run_id,
            int(state.get("transition_sequence", 0)) + 1,
            owner_authority_ref,
            reason_ref,
            completed_task_evidence,
        )
        try:
            replay_status = _cohort_mutator().contract_amendment_replay_status(
                spec_dir,
                amendment_id=expected_amendment_id,
                owner_authority_ref=owner_authority_ref,
                reason_ref=reason_ref,
                completed_task_evidence=completed_task_evidence,
            )
        except Exception as exc:
            return stop(f"contract-amendment replay check failed: {_diag(exc)}")
        if replay_status == "conflict":
            return stop("contract-amendment cohort state conflicts with this event")
        cohort_amendment_already_applied = replay_status == "applied"

    # Step 1b: mandatory plan-hash check for CODE-* states (except `done`)
    if (
        current_state in _CODE_STATES
        and event not in _DONE_EXEMPT_FROM_SCHEDULE_GUARD
        and not cohort_amendment_already_applied
    ):
        err = _schedule_check_current(spec_dir)
        if err:
            return stop(err)

    # Step 2: fire event-specific guard (if one exists)
    guard_fn = _GUARDS.get((mode, event))
    if guard_fn is not None:
        event_args = {}
        if wave_index is not None:
            event_args["wave_index"] = wave_index
        if intent_incomplete:
            event_args["intent_incomplete"] = True
        if allow_retry_cap_override:
            event_args["allow_retry_cap_override"] = True
        err = guard_fn(spec_dir, state, event_args)
        if err:
            return stop(err)

    new_seq = int(state.get("transition_sequence", 0)) + 1
    amendment_id = None
    if event == "contract-amendment":
        amendment_id = _contract_amendment_id(
            run_id,
            new_seq,
            owner_authority_ref,
            reason_ref,
            completed_task_evidence,
        )
        try:
            _cohort_mutator().apply_contract_amendment(
                spec_dir,
                expected_run_id=run_id,
                owner_authority_ref=owner_authority_ref,
                reason_ref=reason_ref,
                completed_task_evidence=completed_task_evidence,
                amendment_id=amendment_id,
            )
        except Exception as exc:
            return stop(f"contract-amendment cohort mutation failed: {_diag(exc)}")

    # Build transition metadata (shared by outbox and engine-state write).
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    last_event_context = None
    if event == "wave-passed" and wave_index is not None:
        last_event_context = {"completed_wave_index": wave_index}
    elif event == "contract-amendment":
        last_event_context = {
            "amendment_id": amendment_id,
            "owner_authority_ref": owner_authority_ref,
            "reason_ref": reason_ref,
            "completed_task_evidence": completed_task_evidence,
        }

    new_state = {
        **state,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "feature": state["feature"],
        "mode": mode,
        "state": next_state,
        "last_event": event,
        "last_event_context": last_event_context,
        "gate_question": _GATE_QUESTIONS.get(next_state),
        "transition_sequence": new_seq,
        "last_transition_at": now,
    }
    # Emit spec as a repo-relative path so WORKSPACE_MCP_SPEC_PATH (which the
    # control plane supplies as a repo-relative value) can match it directly.
    _spec_value = str(spec_dir)
    if _cmd_transition_repo_root is not None:
        with contextlib.suppress(ValueError):
            _spec_value = str(spec_dir.relative_to(_cmd_transition_repo_root))
    pending_data = {
        "seq": new_seq,
        "run_id": run_id,
        "spec": _spec_value,
        "from": current_state,
        "event": event,
        "to": next_state,
        "at": now,
    }

    # Outbox pre-flight: reuse repo root resolved at command start.
    _repo_root: Path | None = _cmd_transition_repo_root

    # Outbox step 1b: write new pending event (graceful).
    _pending_written = False
    if _repo_root is not None:
        try:
            _write_events_pending(_repo_root, pending_data)
            _pending_written = True
        except Exception as exc:
            print(f"loop-engine: warning — could not write events.pending: {exc}", file=sys.stderr)

    # Step 3: write engine-state.json atomically (critical — not wrapped).
    _write_engine_state_atomic(spec_dir, new_state)

    # Outbox steps 3–4: append events.jsonl + delete pending (graceful).
    if _pending_written and _repo_root is not None:
        try:
            _append_events_jsonl(_repo_root, pending_data)
            _events_pending_path(_repo_root).unlink(missing_ok=True)
        except Exception as exc:
            print(f"loop-engine: warning — could not finalize outbox: {exc}", file=sys.stderr)

    print(
        f"loop-engine: transition {current_state!r} → {event!r} → {next_state!r} "
        f"(seq={new_seq}) for {spec_dir.name}"
    )
    return 0


# ── dispatcher ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loop-engine", description=__doc__)
    sub = p.add_subparsers(dest="verb", required=True)

    sp = sub.add_parser("init", help="initialise engine-state.json; output run_id")
    sp.add_argument("spec_dir")
    sp.add_argument("--mode", required=True, choices=["code", "spec-plan"])
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("transition", help="fire an FSM event; enforce guards")
    sp.add_argument("spec_dir")
    sp.add_argument("event")
    sp.add_argument("--wave-index", type=int, dest="wave_index", default=None)
    sp.add_argument(
        "--intent-incomplete",
        action="store_true",
        help="declare reviewers-clean is an intermediate unit of an incomplete intent",
    )
    sp.add_argument(
        "--allow-retry-cap-override",
        action="store_true",
        dest="allow_retry_cap_override",
        help=("waive the review retry cap for this findings-remain transition; "
              "the matching `review record` needs the same flag"),
    )
    sp.add_argument("--owner-authority-ref", dest="owner_authority_ref", default=None)
    sp.add_argument("--reason-ref", dest="reason_ref", default=None)
    sp.add_argument(
        "--completed-evidence-ref",
        dest="completed_evidence_ref",
        action="append",
        default=[],
    )
    sp.set_defaults(func=cmd_transition)

    sp = sub.add_parser("status", help="read engine-state.json + pending_human_wait")
    sp.add_argument("spec_dir")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("reset", help="delete engine-state.json; idempotent")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_reset)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GuardsUnavailable as exc:
        # The engine's chokepoint, matching loop-cohort's. Without this every
        # `_loop_guards.py` load failure printed a traceback out of `cmd_transition`
        # while `sl.exclusive(...)` was held — the one outcome the whole change
        # exists to prevent. `_guards()` is called lazily from inside the locked
        # section, so the raise cannot be caught any earlier than here.
        return stop(str(exc))
    except KeyboardInterrupt:
        return stop("interrupted")


if __name__ == "__main__":
    sys.exit(main())
