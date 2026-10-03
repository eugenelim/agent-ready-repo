"""_compat_facade — compatibility facade for shadow services.

Translates existing engine events and approved pins into typed calls to
shadow services, dual-emits shadow facts using registered delivery contract
types, and treats every target result as shadow data.  The engine calls this
at the minimum set of points needed to emit shadow evidence and verdicts and
to enforce the reversal contract.

Shadow calls are OFF by default and enabled only by the environment variable::

    WORK_LOOP_SHADOW_SERVICES=1

When that variable is absent or not ``"1"``, the engine's behavior is
byte-for-byte identical to its pre-facade behavior.  This env var is the
reversal path: setting it back to off (or unsetting it) restores the legacy
path without deleting any shadow facts already written.

With shadow calls ON:

- A shadow refusal, unavailable control, or service exception must NEVER
  change the legacy transition, cohort write, legacy plan pin, or completion
  decision, and must NEVER count as a legacy allow or approval.
- The facade records a stable redacted ``SHADOW_DIVERGENCE_CODE`` in the
  per-feature shadow directory using the ``security-event.v1`` registered type
  and emits no partial shadow fact.

All shadow writes are routed through the committed ``_confined_mutation.py``
primitives or through the ``EvidenceStore`` writer port, rooted at the spec
directory.  A symlinked ``.shadow-acceptance`` or symlinked spec directory is
refused with a shadow divergence code and never redirects writes outside the
root.

Shadow facts are stored under::

    <spec-dir>/.shadow-acceptance/

using only registered ``contracts/delivery/*.schema.json`` record types:

- ``evidence-receipt.v1``    — appended for each legacy transition via EvidenceStore
- ``approval-record.v1``     — spec-policy approval record, written at plan-locked
- ``initial-plan-review.v1`` — initial plan review record, written at plan-locked
- ``acceptance-verdict.v1``  — derived verdict after plan-locked
- ``delivery-subject.v1``    — optional legacy subject projection at plan-locked
- ``security-event.v1``      — divergence/failure records (best-effort, closed schema)

The directory is self-ignoring: ``<spec-dir>/.shadow-acceptance/.gitignore``
containing ``*`` is created on first use.

The governance gate for target-authority switches is the ``_policy_import``
module's ``compatibility_snapshot`` function.  Its default resolver refuses
because no accepted authority-switch governance record exists; the gate cannot
be satisfied by any file this facade can write.

Standard library only.  Loads sibling modules by path using the
``importlib.util.spec_from_file_location`` pattern established in the other
script modules.

Python 3.11+.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Callable
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

# Shadow store file names — registered contract record types only.
_EVIDENCE_LOG: Final[str] = "shadow-evidence.log"           # evidence-receipt.v1 via EvidenceStore
_APPROVAL_FILE: Final[str] = "shadow-approval.json"         # approval-record.v1
_REVIEW_FILE: Final[str] = "shadow-initial-review.json"     # initial-plan-review.v1
_VERDICT_FILE: Final[str] = "shadow-verdict.json"           # acceptance-verdict.v1
_SUBJECT_FILE: Final[str] = "shadow-delivery-subject.json"  # delivery-subject.v1 (optional)
_PROPERTY_FILE: Final[str] = "shadow-property.json"         # acceptance-property.v1
_SHADOW_PROPERTY_ID: Final[str] = "shadow:legacy-plan-locked"
_SHADOW_PRODUCER: Final[str] = "shadow-compat-facade"
_SECURITY_EVENTS_FILE: Final[str] = "shadow-security-events.jsonl"  # security-event.v1

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
_file_safety_module: ModuleType | None = None
_security_capability_module: ModuleType | None = None
_policy_import_module_cache: ModuleType | None = None
_evidence_store_module_cache: ModuleType | None = None
_subject_source_module_cache: ModuleType | None = None

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


def _file_safety() -> ModuleType:
    """Lazily load ``file_safety.py`` for bounded, no-follow file reads."""
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_sibling("_cf_file_safety", "file_safety.py")
    return _file_safety_module


def _security_capability() -> ModuleType:
    """Lazily load ``_security_capability.py`` for capability issuance."""
    global _security_capability_module
    if _security_capability_module is None:
        _security_capability_module = _load_sibling(
            "_cf_security_capability", "_security_capability.py"
        )
    return _security_capability_module


def _policy_import_mod() -> ModuleType:
    """Lazily load ``_policy_import.py`` for spec-policy import."""
    global _policy_import_module_cache
    if _policy_import_module_cache is None:
        _policy_import_module_cache = _load_sibling("_cf_policy_import", "_policy_import.py")
    return _policy_import_module_cache


def _evidence_store_mod() -> ModuleType:
    """Lazily load ``_evidence_store.py`` for the evidence transaction log."""
    global _evidence_store_module_cache
    if _evidence_store_module_cache is None:
        _evidence_store_module_cache = _load_sibling("_cf_evidence_store", "_evidence_store.py")
    return _evidence_store_module_cache


def _subject_source_mod() -> ModuleType:
    """Lazily load ``_subject_source.py`` for legacy subject projection."""
    global _subject_source_module_cache
    if _subject_source_module_cache is None:
        _subject_source_module_cache = _load_sibling(
            "_cf_subject_source", "_subject_source.py"
        )
    return _subject_source_module_cache


# ---------------------------------------------------------------------------
# Shadow storage helpers — confined writes
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


def _confined_read_json(spec_dir: Path, file_path: Path) -> dict:
    """Read and parse a JSON file using the confined file reader.

    Returns an empty dict on any failure (file absent, not parseable, etc.).
    Uses ``file_safety.read_confined_regular_file`` for bounded, no-follow reads.
    """
    try:
        fs = _file_safety()
        raw = fs.read_confined_regular_file(spec_dir, file_path, max_bytes=1024 * 1024)
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except Exception:  # noqa: BLE001 — missing or unparseable: return empty
        return {}


# ---------------------------------------------------------------------------
# Divergence recording — security-event.v1 (best-effort in error path)
# ---------------------------------------------------------------------------


def _record_divergence(
    spec_dir: Path,
    shadow_dir: Path,
    *,
    context: str,
    exc_type: str,
    cm: ModuleType,
) -> None:
    """Best-effort append of a schema-valid security-event.v1 divergence entry.

    Writes only the seven required fields of the closed ``security-event.v1``
    schema: no exception messages, no content-derived hashes, no partial
    shadow facts, and no extra fields.  Any failure is silently absorbed.

    The ``context`` and ``exc_type`` parameters are reserved for future
    structured logging; they do not enter the record under the closed schema.
    """
    try:
        # The shadow dir may not exist if the failure was during dir creation.
        _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)
        entry = {
            "schema_version": 1,
            "operation_id": "op-" + secrets.token_hex(8),
            "correlation_id": "shadow-compat-facade",
            "event_type": "capability-check",
            "outcome": "denied",
            "reason_code": SHADOW_DIVERGENCE_CODE,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _confined_jsonl_append(
            spec_dir, shadow_dir / _SECURITY_EVENTS_FILE, entry, cm
        )
    except Exception:  # noqa: BLE001 — divergence recording must never propagate
        pass


# ---------------------------------------------------------------------------
# Capability helpers
# ---------------------------------------------------------------------------


def _durable_sink(spec_dir: Path, shadow_dir: Path, cm: ModuleType) -> Callable[[object], None]:
    """Return an audit sink that durably appends each security event before returning.

    Each event is written as one ``security-event.v1`` line to the shadow
    security-event log through the confined append helper.  A failed append
    raises, so the calling service fails closed and the facade records a
    divergence instead of acknowledging an event that was never stored.
    """

    def sink(event: object) -> None:
        # Any storage failure surfaces as OSError: the security-event emitter
        # turns that into its fail-closed sink-unavailable signal whichever
        # copy of the emitter module the calling service loaded.
        if dataclasses.is_dataclass(event) and not isinstance(event, type):
            record: object = dataclasses.asdict(event)
        else:
            record = event
        if not isinstance(record, dict):
            raise OSError("security event must be a dataclass or a mapping")
        try:
            _confined_jsonl_append(spec_dir, shadow_dir / _SECURITY_EVENTS_FILE, record, cm)
        except OSError:
            raise
        except Exception as exc:
            raise OSError("shadow security-event store unavailable") from exc

    return sink


def _spec_dir_fingerprint(spec_dir: Path) -> str:
    """Return a stable acceptance fingerprint from *spec_dir*'s repository-relative path.

    Relative to the repository root so the fingerprint survives a checkout move.
    """
    resolved = spec_dir.resolve()
    relative = resolved.relative_to(_find_repo_root(spec_dir)).as_posix()
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _make_shadow_grant(scope_roots: list[str]) -> tuple:
    """Issue a short-lived shadow grant covering the requested write scopes.

    Returns ``(issuer, grant)`` where the grant authorises ``["append"]``
    operations within each of *scope_roots* and their sub-paths.
    """
    sc = _security_capability()
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["shadow-compat"],
        operations=["append"],
        trust_class="shadow-compat",
        writes_allowed_roots=scope_roots,
        control_denies=[],
    )
    return issuer, grant


# ---------------------------------------------------------------------------
# Shadow evidence — evidence-receipt.v1 via EvidenceStore
# ---------------------------------------------------------------------------


def _build_shadow_evidence_receipt(spec_dir: Path, pending_data: dict) -> dict:
    """Build an ``evidence-receipt.v1`` record for a completed legacy transition.

    Uses only stable, inert fields (sequence number, event name selector).
    No payload bytes or content-derived hashes enter the record.
    """
    event_name = str(pending_data.get("event", "unknown"))
    return {
        "schema_version": 1,
        "receipt_id": f"shadow-{secrets.token_hex(16)}",
        "acceptance_fingerprint": _spec_dir_fingerprint(spec_dir),
        "lineage": {"criterion_ref": _SHADOW_PROPERTY_ID},
        "selector": {"term": f"engine-transition:{event_name}"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "engine-transition"},
        "outcome": "observed",
        "producer": {"class": _SHADOW_PRODUCER, "identity": _SHADOW_PRODUCER},
    }


def _do_shadow_on_transition(
    spec_dir: Path,
    shadow_dir: Path,
    pending_data: dict,
    cm: ModuleType,
) -> None:
    """Append one shadow evidence-receipt.v1 for the completed legacy transition."""
    _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)

    es_mod = _evidence_store_mod()
    issuer, grant = _make_shadow_grant(["evidence"])

    log_path = shadow_dir / _EVIDENCE_LOG
    store = es_mod.EvidenceStore(log_path)
    store.open()

    receipt = _build_shadow_evidence_receipt(spec_dir, pending_data)
    store.append_receipt(
        receipt,
        transaction_id=f"shadow-tx-{secrets.token_hex(16)}",
        issuer=issuer,
        grant=grant,
        audit_sink=_durable_sink(spec_dir, shadow_dir, cm),
    )


# ---------------------------------------------------------------------------
# Shadow policy import — shadow services at plan-locked
# ---------------------------------------------------------------------------


def _find_repo_root(spec_dir: Path) -> Path:
    """Walk up from *spec_dir* to the nearest ``.git`` parent; fall back to parent."""
    current = spec_dir.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return spec_dir.resolve().parent


def _try_project_legacy_subject(
    spec_dir: Path,
    shadow_dir: Path,
    approved_spec_hash: str,
    approved_plan_hash: str,
    cm: ModuleType,
) -> None:
    """Best-effort legacy subject projection; silently skipped on any failure.

    Subject projection may fail when the working tree is dirty, git is
    unavailable, or the approved digests have drifted — all acceptable in
    shadow mode.  When successful, writes a ``delivery-subject.v1`` record.
    """
    try:
        ss = _subject_source_mod()
        repo_root = _find_repo_root(spec_dir)
        subject = ss.project_legacy_subject(
            repo_root=repo_root,
            spec_dir=spec_dir,
            approved_spec_hash=approved_spec_hash,
            approved_plan_hash=approved_plan_hash,
            audit_sink=_durable_sink(spec_dir, shadow_dir, cm),
            subject_id=f"shadow-subject:{spec_dir.name}",
            evidence_policy_ref=(
                f"compat-shadow:evidence-policy:{approved_spec_hash[:16]}"
            ),
        )
        _confined_json_write(spec_dir, shadow_dir / _SUBJECT_FILE, subject, cm)
    except Exception:  # noqa: BLE001 — subject projection is optional
        pass


def _do_shadow_on_plan_locked(
    spec_dir: Path,
    shadow_dir: Path,
    engine_state: dict,
    cm: ModuleType,
) -> None:
    """Call shadow services at plan-locked and persist registered record types.

    Sequence:
    1. Read approved spec/plan digests from ``state.json`` via the confined reader.
    2. Call ``import_policy`` with those digests to produce ``approval-record.v1``
       and ``initial-plan-review.v1`` records.
    3. Write those records as confined JSON files.
    4. Open the ``EvidenceStore`` to collect receipts from prior transitions.
    5. Optionally project a legacy delivery subject (best-effort; silently skipped).
    6. Call ``evaluate_verdict`` with the collected receipts.
    7. Write the derived verdict as a confined JSON file.

    Any failure propagates to the caller, whose outer try/except records a
    divergence and returns — never affecting the legacy path.
    """
    _confined_ensure_shadow_dir(spec_dir, shadow_dir, cm)

    # Step 1 — read approved hashes via bounded, no-follow reader.
    cohort_state = _confined_read_json(spec_dir, spec_dir / "state.json")
    approved_spec_hash = str(cohort_state.get("approved_spec_hash") or "")
    approved_plan_hash = str(cohort_state.get("approved_plan_hash") or "")
    if not approved_spec_hash or not approved_plan_hash:
        raise ValueError(
            "approved_spec_hash or approved_plan_hash absent in state.json"
        )

    # Step 2 — call import_policy with the approved pins.
    pi = _policy_import_mod()
    acc = _acceptance()
    issuer, grant = _make_shadow_grant(["delivery", "evidence"])

    digest_prefix = approved_spec_hash[:16]
    refs: dict[str, str] = {
        k: f"compat-shadow:{digest_prefix}:{k}" for k in acc.ENVELOPE_REFS_KEYS
    }

    import_store = pi.ImportStore()
    approval_record, initial_review = pi.import_policy(
        spec_path=spec_dir / "spec.md",
        plan_path=spec_dir / "plan.md",
        refs=refs,
        terminal_intent="work-loop-code-implementation",
        writer_grant=grant,
        issuer=issuer,
        audit_sink=_durable_sink(spec_dir, shadow_dir, cm),
        store=import_store,
        approval_identity="shadow-compat-facade",
        approval_role="shadow-observer",
        reviewer_identity="shadow-compat-facade",
        reviewer_role="shadow-reviewer",
        approved_spec_digest=approved_spec_hash,
        approved_plan_digest=approved_plan_hash,
        # The legacy approval pin stores no reviewed-envelope fingerprint, so
        # the facade cannot supply one.  Passing None skips the envelope
        # comparison; this is safe only because all shadow records are
        # non-authoritative.  Any authority-granting caller must supply a real pin.
        approved_envelope_fingerprint=None,
    )

    # Step 3 — persist approval-record.v1 and initial-plan-review.v1.
    _confined_json_write(spec_dir, shadow_dir / _APPROVAL_FILE, approval_record, cm)
    _confined_json_write(spec_dir, shadow_dir / _REVIEW_FILE, initial_review, cm)

    # Step 4 — open EvidenceStore to collect receipts from prior transitions.
    es_mod = _evidence_store_mod()
    store = es_mod.EvidenceStore(shadow_dir / _EVIDENCE_LOG)
    store.open()
    receipts = store.get_all_active_receipts()

    # Step 5 — optional legacy subject projection (best-effort).
    _try_project_legacy_subject(
        spec_dir, shadow_dir, approved_spec_hash, approved_plan_hash, cm
    )

    # Step 6 — evaluate verdict over the collected receipts.
    acceptance_fp = _spec_dir_fingerprint(spec_dir)
    spec_dir_ref = spec_dir.resolve().relative_to(_find_repo_root(spec_dir)).as_posix()
    property_record = {
        "schema_version": 1,
        "property_id": _SHADOW_PROPERTY_ID,
        "spec_ref": f"{spec_dir_ref}/spec.md",
        "authority_ref": "shadow-compat-observation",
        "subject_selector": {
            "paths_or_artifacts": [spec_dir_ref],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [
            {
                "term": "engine-transition:plan-locked",
                "observation_type": "engine-transition",
                "producer_class": _SHADOW_PRODUCER,
                "outcomes": ["observed"],
            },
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "any"},
        "contradiction_rule": {"expression": "none"},
        "policy_version": "shadow-compat-1",
    }
    _confined_json_write(spec_dir, shadow_dir / _PROPERTY_FILE, property_record, cm)
    verdict = acc.evaluate_verdict(
        property_record=property_record,
        receipts=receipts,
        current_acceptance_fingerprint=acceptance_fp,
        adapter="sequential-reference",
    )

    # Step 7 — persist acceptance-verdict.v1.
    _confined_json_write(spec_dir, shadow_dir / _VERDICT_FILE, verdict, cm)


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
    """Call shadow services and write registered record types at plan-locked.

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


# ---------------------------------------------------------------------------
# Module completeness marker
# ---------------------------------------------------------------------------

_MODULE_COMPLETE = True
