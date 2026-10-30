"""Fail-closed sequencing for durable artifact creation, registration, and dispatch."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType

WORKSPACE_LOCK_FILE = ".workspace-repair.lock"


class TransactionStatus(Enum):
    """Terminal state of one intake transaction attempt."""

    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    RECONCILIATION_RECORD_FAILED = "reconciliation_record_failed"
    INVALID_TARGET = "invalid_target"
    LOCK_BUSY = "lock_busy"
    DISPATCH_FAILED = "dispatch_failed"


@dataclass(frozen=True)
class TransactionResult:
    """Safe-to-render outcome without exception text or source content."""

    status: TransactionStatus
    failed_stage: str | None
    dispatch_started: bool


@dataclass(frozen=True)
class TrackerSource:
    """A tracker-origin source whose first record the transaction writes."""

    locator: str
    revision: str
    profile: dict[str, str] | None
    mode: str = "tracker-origin"


def _load_sibling(name: str) -> ModuleType:
    """Load a sibling script of this skill by path under a unique module name.

    Skills may ship same-named scripts, so a bare import could bind another
    skill's copy. The module is registered before it runs so its frozen
    dataclasses resolve their own ``__module__``.
    """

    module_name = f"core_work_intake_intake_transaction_{name}"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot locate sibling module {name!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


def _append_source_authority(
    repository_root: Path, target: Path, source: TrackerSource
) -> None:
    """Append the first record to the materialized artifact and verify it.

    Raises on any refusal: a source the renderer refuses, a missing, linked or
    non-regular target, an artifact that already holds a record, or a record
    that does not read back equal to the declared values.
    """

    refresh = _load_sibling("refresh")
    file_safety = _load_sibling("file_safety")
    record = refresh.render_first_source_authority(
        mode=source.mode,
        locator=source.locator,
        revision=source.revision,
        profile=source.profile,
    )
    current = file_safety.read_confined_regular_file(repository_root, target)
    text = current.decode("utf-8")
    # Leave one blank line between the artifact text and the record.
    separator = "\n" * max(0, 2 - (len(text) - len(text.rstrip("\n")))) if text else ""
    file_safety.write_confined_regular_file(
        repository_root,
        target,
        (text + separator + record).encode("utf-8"),
        expect_sha256=hashlib.sha256(current).hexdigest(),
    )
    written = file_safety.read_confined_regular_file(repository_root, target).decode(
        "utf-8"
    )
    authority = refresh.parse_source_authority(written)
    if (
        authority.source_ref != source.locator
        or authority.source_revision != source.revision
        or authority.tracker_profile != source.profile
        or authority.mode != "tracker-origin"
        or dict(authority.owned_fields)
    ):
        raise ValueError("source authority record does not match the declared source")


def run_intake_transaction(
    *,
    repository_root: Path,
    configured_parent: str,
    artifact_target: str,
    materialize_artifact: Callable[[Path], None],
    rollback_partial_state: Callable[[], None],
    record_reconciliation: Callable[[str], None],
    dispatch_processor: Callable[[], None],
    register_workspace_entry: Callable[[], None] | None = None,
    tracker_source: TrackerSource | None = None,
) -> TransactionResult:
    """Materialize, optionally register, then dispatch one durable artifact route.

    With no ``register_workspace_entry`` the transaction takes the lock,
    materializes, releases the lock, and dispatches: no registration stage runs
    and so no registration rollback applies.

    With ``tracker_source`` set, the artifact's first source-authority record
    replaces the registration stage: it is appended under the same lock and
    read back, and the transaction commits only when the artifact holds exactly
    one record equal to the declared locator, revision and profile. Any other
    outcome recovers with ``failed_stage="source_authority_write"`` and starts
    no dispatch. Values pass as arguments, never through a shell string.

    Callers supply idempotent rollback and reconciliation operations appropriate
    to their workspace writer. Exception values are intentionally not returned,
    because they may contain untrusted source data or sensitive paths.

    Direct-light routes do not create durable artifacts and must not invoke this
    transaction helper.
    """

    try:
        resolved_root = repository_root.resolve(strict=True)
        confined_target = resolve_confined_target(
            repository_root=resolved_root,
            configured_parent=configured_parent,
            artifact_target=artifact_target,
        )
    except (OSError, RuntimeError, ValueError):
        return TransactionResult(
            status=TransactionStatus.INVALID_TARGET,
            failed_stage="path_validation",
            dispatch_started=False,
        )

    try:
        lock_path = _acquire_workspace_lock(resolved_root)
    except FileExistsError:
        return TransactionResult(
            status=TransactionStatus.LOCK_BUSY,
            failed_stage="lock_acquisition",
            dispatch_started=False,
        )

    try:
        try:
            materialize_artifact(confined_target)
        except Exception:
            return _recover_partial_state(
                failed_stage="artifact_write",
                rollback_partial_state=rollback_partial_state,
                record_reconciliation=record_reconciliation,
            )

        if tracker_source is not None:
            try:
                _append_source_authority(resolved_root, confined_target, tracker_source)
            except Exception:
                return _recover_partial_state(
                    failed_stage="source_authority_write",
                    rollback_partial_state=rollback_partial_state,
                    record_reconciliation=record_reconciliation,
                )
        elif register_workspace_entry is not None:
            try:
                register_workspace_entry()
            except Exception:
                return _recover_partial_state(
                    failed_stage="registration_write",
                    rollback_partial_state=rollback_partial_state,
                    record_reconciliation=record_reconciliation,
                )
    finally:
        with contextlib.suppress(FileNotFoundError):
            lock_path.unlink()

    try:
        dispatch_processor()
    except Exception:
        return TransactionResult(
            status=TransactionStatus.DISPATCH_FAILED,
            failed_stage="processor_dispatch",
            dispatch_started=True,
        )
    return TransactionResult(
        status=TransactionStatus.COMMITTED,
        failed_stage=None,
        dispatch_started=True,
    )


def _acquire_workspace_lock(repository_root: Path) -> Path:
    """Acquire the shared lock used by every workspace writer.

    The file protocol coordinates this transaction with repair-apply,
    migration apply and rollback, guarded refresh, and prune operations.
    """

    lock_path = repository_root / WORKSPACE_LOCK_FILE
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    try:
        pid = str(os.getpid()).encode("ascii")
        if os.write(descriptor, pid) != len(pid):
            raise OSError("short write while recording lock owner")
        os.fsync(descriptor)
    except Exception:
        os.close(descriptor)
        lock_path.unlink()
        raise
    os.close(descriptor)
    return lock_path


def resolve_confined_target(
    *,
    repository_root: Path,
    configured_parent: str,
    artifact_target: str,
) -> Path:
    """Resolve a target confined to both the repository and configured parent."""

    _validate_relative_path(configured_parent)
    _validate_relative_path(artifact_target)

    parent_parts = Path(configured_parent).parts
    target_parts = Path(artifact_target).parts
    if target_parts[: len(parent_parts)] != parent_parts:
        raise ValueError("artifact target is outside the configured parent")

    resolved_root = repository_root.resolve(strict=True)
    resolved_parent = (resolved_root / configured_parent).resolve(strict=True)
    resolved_target = (resolved_root / artifact_target).resolve(strict=False)
    _require_descendant(resolved_parent, resolved_root)
    _require_descendant(resolved_target, resolved_parent)
    return resolved_target


def _validate_relative_path(value: str) -> None:
    """Reject ambiguous or platform-dependent repository-relative paths."""

    if not isinstance(value, str) or not value:
        raise ValueError("path is empty")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("path is absolute")
    if "\\" in value:
        raise ValueError("path contains a backslash")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("path contains an unsafe segment")


def _require_descendant(candidate: Path, parent: Path) -> None:
    """Require candidate to remain below parent after symlink resolution."""

    try:
        candidate.relative_to(parent)
    except ValueError as exc:
        raise ValueError("resolved path escapes its configured parent") from exc


def _recover_partial_state(
    *,
    failed_stage: str,
    rollback_partial_state: Callable[[], None],
    record_reconciliation: Callable[[str], None],
) -> TransactionResult:
    """Rollback partial state or persist a non-dispatchable finding."""

    try:
        rollback_partial_state()
    except Exception:
        try:
            record_reconciliation(failed_stage)
        except Exception:
            return TransactionResult(
                status=TransactionStatus.RECONCILIATION_RECORD_FAILED,
                failed_stage=failed_stage,
                dispatch_started=False,
            )
        return TransactionResult(
            status=TransactionStatus.RECONCILIATION_REQUIRED,
            failed_stage=failed_stage,
            dispatch_started=False,
        )

    return TransactionResult(
        status=TransactionStatus.ROLLED_BACK,
        failed_stage=failed_stage,
        dispatch_started=False,
    )
