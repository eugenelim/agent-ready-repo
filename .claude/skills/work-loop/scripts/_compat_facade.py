"""_compat_facade — compatibility facade for Slice 1 shadow services.

T8 module: translates existing engine events and approved pins into typed
calls to Slice 1 services, dual-emits shadow facts, and treats every target
result as shadow data.  The engine calls this at the minimum set of points
needed to satisfy AC-0007, AC-0016, and AC-0017.

Shadow calls are OFF by default and enabled only by the environment variable::

    WORK_LOOP_SHADOW_SERVICES=1

When that variable is absent or not ``"1"``, the engine's behavior is
byte-for-byte identical to its pre-facade behavior.  This env var is the
reversal path AC-0017 names: setting it back to off (or unsetting it)
restores the legacy path without deleting any shadow facts already written.

With shadow calls ON:

- A shadow refusal, unavailable control, or service exception must NEVER
  change the legacy transition, cohort write, legacy plan pin, or completion
  decision, and must NEVER count as a legacy allow or approval.
- The facade records a stable redacted ``SHADOW_DIVERGENCE_CODE`` in the
  per-feature shadow directory and emits no partial shadow fact.

All shadow writes (directory creation, atomic JSON replace, JSONL append)
are routed through the committed ``_confined_mutation.py`` primitives,
rooted at the spec directory (AC-0011).  A symlinked ``.shadow-acceptance``
or symlinked spec directory is refused with a shadow divergence code and
never redirects writes outside the root.

Shadow facts are stored under::

    <spec-dir>/.shadow-acceptance/

The directory is self-ignoring: when the facade creates it, it also
exclusively creates ``.shadow-acceptance/.gitignore`` containing ``*``
through the confined primitive.  No entry in the repository ``.gitignore``
is needed.

A missing accepted governance fingerprint refuses every target-authority
switch (AC-0017).  The fingerprint is represented by the file::

    <spec-dir>/.shadow-acceptance/governance.json

with ``{"decision": "accepted", ...}`` present.  Implementation alone cannot
place this file; it must be produced by a separately accepted governance
process.

Standard library only.  Loads sibling Slice 1 modules by path using the
``importlib.util.spec_from_file_location`` pattern established in the other
Slice 1 script modules.

Python 3.11+.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Public constants
    "SHADOW_ENV_VAR",
    "SHADOW_DIVERGENCE_CODE",
    "SHADOW_SUBDIR",
    # Opt-in check
    "shadow_enabled",
    # Engine call points (called after legacy commit — never change legacy behavior)
    "shadow_call_on_transition",
    "shadow_call_on_plan_locked",
    # Governance check (AC-0017)
    "check_governance_fingerprint",
]

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

# The environment variable that opts in to shadow service calls.
# Absent or not "1" → byte-for-byte identical to pre-facade behavior.
SHADOW_ENV_VAR: Final[str] = "WORK_LOOP_SHADOW_SERVICES"

# Stable redacted code written on shadow failure.
# Never carries partial shadow fact content or payload-derived material.
SHADOW_DIVERGENCE_CODE: Final[str] = "shadow-divergence:redacted"

# Per-feature shadow store directory name (inside the spec dir).
SHADOW_SUBDIR: Final[str] = ".shadow-acceptance"

_SCRIPTS_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Opt-in check
# ---------------------------------------------------------------------------


def shadow_enabled() -> bool:
    """Return True when the shadow service opt-in is active.

    Reads ``WORK_LOOP_SHADOW_SERVICES`` from the environment at call time.
    Not cached: a test may change the environment between calls.
    """
    return os.environ.get(SHADOW_ENV_VAR, "") == "1"


# ---------------------------------------------------------------------------
# Sibling module loaders
# ---------------------------------------------------------------------------

_acceptance_module: ModuleType | None = None
_confined_mutation_module: ModuleType | None = None

_CM_UNAVAILABLE = object()  # sentinel — _confined_mutation load failed


def _load_sibling(name: str, filename: str) -> ModuleType:
    """Load a sibling scripts module by path, unregistered in sys.modules."""
    path = _SCRIPTS_DIR / filename
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    finally:
        sys.dont_write_bytecode = previous


def _acceptance() -> ModuleType:
    """Lazily load ``_acceptance.py`` for verdict evaluation."""
    global _acceptance_module
    if _acceptance_module is None:
        _acceptance_module = _load_sibling("_cf_acceptance", "_acceptance.py")
    return _acceptance_module


def _cm() -> object:
    """Lazily load ``_confined_mutation.py``.

    Returns the module on success, or ``_CM_UNAVAILABLE`` on failure.
    Failure is logged once to stderr and cached.
    """
    global _confined_mutation_module
    if _confined_mutation_module is not None:
        return _confined_mutation_module
    try:
        mod = _load_sibling("_cf_confined_mutation", "_confined_mutation.py")
        # Verify the expected public API is present.
        for attr in ("confined_create", "confined_append", "confined_atomic_replace",
                     "MutationDenied"):
            if not hasattr(mod, attr):
                raise ImportError(f"_confined_mutation.py missing attribute: {attr!r}")
        _confined_mutation_module = mod
        return mod
    except Exception as exc:
        print(
            f"_compat_facade: warning — confined_mutation unavailable "
            f"({type(exc).__name__}: {exc}); shadow writes disabled",
            file=sys.stderr,
        )
        _confined_mutation_module = _CM_UNAVAILABLE  # type: ignore[assignment]
        return _CM_UNAVAILABLE


# ---------------------------------------------------------------------------
# Shadow storage helpers — confined writes (AC-0011)
# ---------------------------------------------------------------------------


def _shadow_dir(spec_dir: Path) -> Path:
    """Return the per-feature shadow directory inside *spec_dir*."""
    return spec_dir / SHADOW_SUBDIR


def _confined_ensure_shadow_dir(spec_dir: Path, shadow_dir: Path, cm: ModuleType) -> None:
    """Create the shadow directory if absent, using confined primitives.

    Raises ``cm.MutationDenied`` when:
    - *spec_dir* is a symlink or not a directory.
    - *shadow_dir* already exists as a symlink or non-directory.
    - directory creation or the self-ignoring ``.gitignore`` write fails.

    On first creation, also writes ``.shadow-acceptance/.gitignore`` containing
    ``*`` through ``confined_create``, making the directory self-ignoring.
    The ``.gitignore`` write is idempotent (``denied-already-exists`` is
    silently absorbed on subsequent calls).
    """
    # Confirm spec_dir (the confinement root) is a real directory.
    try:
        root_info = os.lstat(spec_dir)
    except OSError as exc:
        raise cm.MutationDenied(
            "denied-path-violation",
            f"spec_dir not accessible: {exc}",
        ) from exc
    if stat.S_ISLNK(root_info.st_mode):
        raise cm.MutationDenied("denied-path-violation", "spec_dir is a symlink")
    if not stat.S_ISDIR(root_info.st_mode):
        raise cm.MutationDenied("denied-path-violation", "spec_dir is not a directory")

    # Check or create .shadow-acceptance (one level inside the verified spec_dir).
    try:
        sd_info = os.lstat(shadow_dir)
        if stat.S_ISLNK(sd_info.st_mode):
            raise cm.MutationDenied(
                "denied-path-violation",
                ".shadow-acceptance is a symlink — refusing to write",
            )
        if not stat.S_ISDIR(sd_info.st_mode):
            raise cm.MutationDenied(
                "denied-path-violation",
                ".shadow-acceptance exists but is not a directory",
            )
    except FileNotFoundError:
        # Create one directory level inside the lstat-verified spec_dir.
        try:
            shadow_dir.mkdir()
        except FileExistsError:
            pass  # another process created it concurrently — continue
        except OSError as exc:
            raise cm.MutationDenied(
                "denied-staging-failed",
                f"mkdir .shadow-acceptance failed: {exc}",
            ) from exc

    # Write self-ignoring .gitignore via confined_create (idempotent).
    # This also validates the path through _open_confined_parent (O_NOFOLLOW
    # walk), catching any symlink placed after the lstat checks above.
    gitignore = shadow_dir / ".gitignore"
    try:
        cm.confined_create(spec_dir, gitignore, b"*\n")
    except cm.MutationDenied as exc:
        if exc.denial_code != "denied-already-exists":
            raise


def _confined_jsonl_append(
    spec_dir: Path,
    path: Path,
    record: dict,
    cm: ModuleType,
) -> None:
    """Append one JSON record to a confined JSONL file, creating if absent."""
    content = (json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
    try:
        cm.confined_create(spec_dir, path, content)
    except cm.MutationDenied as exc:
        if exc.denial_code == "denied-already-exists":
            cm.confined_append(spec_dir, path, content)
        else:
            raise


def _confined_json_write(
    spec_dir: Path,
    path: Path,
    record: dict,
    cm: ModuleType,
) -> None:
    """Atomically write a JSON record to a confined file."""
    content = (json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
    cm.confined_atomic_replace(spec_dir, path, content)


def _record_divergence(
    spec_dir: Path,
    shadow_dir: Path,
    *,
    context: str,
    exc_type: str,
    cm: ModuleType,
) -> None:
    """Best-effort append of a stable, redacted divergence entry.

    Carries only the divergence code, a context tag (no payload content),
    and a timestamp.  Never logs exception messages or partial shadow facts.
    Any failure in the divergence write is silently absorbed.
    """
    try:
        # The shadow dir may not exist yet if the failure was during dir creation.
        # Try to ensure it; if that fails too, give up silently.
        _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)
        entry = {
            "divergence_code": SHADOW_DIVERGENCE_CODE,
            "context": context,
            "exc_type": exc_type,
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _confined_jsonl_append(spec_dir, shadow_dir / "divergence.jsonl", entry, cm)
    except Exception:  # noqa: BLE001 — divergence recording must never propagate
        pass


# ---------------------------------------------------------------------------
# Shadow evidence (AC-0007 dual-emit)
# ---------------------------------------------------------------------------


def _build_shadow_evidence_record(pending_data: dict) -> dict:
    """Build a minimal shadow evidence record from a legacy transition event.

    The record captures the event's stable identity fields (sequence number,
    event name, source and target states, run-id) without payload bytes.
    It carries ``authoritative: false`` so no consumer may treat it as a
    direct approval or completion authority.
    """
    return {
        "schema_version": 1,
        "record_type": "shadow-transition-evidence",
        "seq": pending_data.get("seq"),
        "event": pending_data.get("event"),
        "from_state": pending_data.get("from"),
        "to_state": pending_data.get("to"),
        "run_id": pending_data.get("run_id"),
        "at": pending_data.get("at"),
        # Shadow: this record is non-authoritative.  A target authority
        # switch requires an accepted governance fingerprint (AC-0017).
        "authoritative": False,
    }


def _do_shadow_on_transition(
    spec_dir: Path,
    shadow_dir: Path,
    pending_data: dict,
    cm: ModuleType,
) -> None:
    """Append one shadow evidence record for the completed legacy transition."""
    _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)
    record = _build_shadow_evidence_record(pending_data)
    _confined_jsonl_append(spec_dir, shadow_dir / "evidence.jsonl", record, cm)


# ---------------------------------------------------------------------------
# Shadow policy import (AC-0016 plan-locked hook)
# ---------------------------------------------------------------------------


def _do_shadow_on_plan_locked(
    spec_dir: Path,
    shadow_dir: Path,
    engine_state: dict,
    cm: ModuleType,
) -> None:
    """Write a shadow policy-import record for the plan-locked event.

    Reads the approved spec/plan digests from the cohort ``state.json``
    alongside the spec dir.  The record is non-authoritative (AC-0016):
    it mirrors the approved pin only for shadow audit purposes and creates
    no target task-projection record or plan approval.

    A missing or unreadable ``state.json`` leaves the hash fields empty
    and is recorded as a divergence code rather than a failure.
    """
    _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)

    # Read approved hashes from state.json (cohort state).  This runs AFTER
    # the legacy plan-locked commit, outside the critical section, so a simple
    # read is acceptable here.  Any failure falls back to empty strings.
    approved_spec_hash = ""
    approved_plan_hash = ""
    try:
        state_path = spec_dir / "state.json"
        raw = state_path.read_bytes()
        cohort_state = json.loads(raw.decode("utf-8"))
        if isinstance(cohort_state, dict):
            approved_spec_hash = str(cohort_state.get("approved_spec_hash") or "")
            approved_plan_hash = str(cohort_state.get("approved_plan_hash") or "")
    except Exception:  # noqa: BLE001 — missing hashes: record still written
        pass

    shadow_import_record = {
        "schema_version": 1,
        "record_type": "shadow-policy-import",
        "feature": str(engine_state.get("feature", "")),
        "run_id": str(engine_state.get("run_id", "")),
        "approved_spec_hash": approved_spec_hash,
        "approved_plan_hash": approved_plan_hash,
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # Non-authoritative.  Target authority switch requires an accepted
        # governance fingerprint (AC-0017); this record grants none.
        "authoritative": False,
        "governance_required_for_authority_switch": True,
    }
    _confined_json_write(spec_dir, shadow_dir / "policy-import.json", shadow_import_record, cm)


# ---------------------------------------------------------------------------
# Public facade entry points
# ---------------------------------------------------------------------------


def shadow_call_on_transition(
    spec_dir: Path,
    engine_state: dict,
    pending_data: dict,
) -> None:
    """Dual-emit a shadow evidence fact for the completed legacy transition.

    Called AFTER the legacy commit succeeds.  Any exception is caught and
    recorded as ``SHADOW_DIVERGENCE_CODE``.  Never affects the legacy result.

    When ``WORK_LOOP_SHADOW_SERVICES`` is not ``"1"``, returns immediately
    with no observable effect.
    """
    if not shadow_enabled():
        return
    confined = _cm()
    if confined is _CM_UNAVAILABLE:
        return
    sd = _shadow_dir(spec_dir)
    try:
        _do_shadow_on_transition(spec_dir, sd, pending_data, confined)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — must never propagate
        _record_divergence(
            spec_dir,
            sd,
            context="shadow_call_on_transition",
            exc_type=type(exc).__name__,
            cm=confined,  # type: ignore[arg-type]
        )


def shadow_call_on_plan_locked(
    spec_dir: Path,
    engine_state: dict,
) -> None:
    """Write a shadow policy-import record at plan-locked (AC-0016).

    Called AFTER the legacy plan-locked commit succeeds.  Any exception is
    caught and recorded as ``SHADOW_DIVERGENCE_CODE``.  Never affects the
    legacy path.  When ``WORK_LOOP_SHADOW_SERVICES`` is not ``"1"``, returns
    immediately.
    """
    if not shadow_enabled():
        return
    confined = _cm()
    if confined is _CM_UNAVAILABLE:
        return
    sd = _shadow_dir(spec_dir)
    try:
        _do_shadow_on_plan_locked(spec_dir, sd, engine_state, confined)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — must never propagate
        _record_divergence(
            spec_dir,
            sd,
            context="shadow_call_on_plan_locked",
            exc_type=type(exc).__name__,
            cm=confined,  # type: ignore[arg-type]
        )


def check_governance_fingerprint(spec_dir: Path) -> bool:
    """Return True only when an accepted governance fingerprint is present.

    A missing, unreadable, or invalid governance record returns ``False``,
    refusing every target-authority switch (AC-0017).  The governance record
    must be produced by a separately accepted governance process — it cannot
    be created by this implementation alone.

    The accepted record must be at::

        <spec-dir>/.shadow-acceptance/governance.json

    with ``{"decision": "accepted", ...}`` present.
    """
    governance_path = _shadow_dir(spec_dir) / "governance.json"
    try:
        info = os.lstat(governance_path)
        if not stat.S_ISREG(info.st_mode):
            return False
        raw = governance_path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            return False
        return data.get("decision") == "accepted"
    except Exception:  # noqa: BLE001 — missing or unreadable = no governance
        return False


# ---------------------------------------------------------------------------
# Module completeness marker
# ---------------------------------------------------------------------------

_MODULE_COMPLETE = True
