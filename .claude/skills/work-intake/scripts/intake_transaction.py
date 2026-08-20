"""Fail-closed sequencing for durable artifact creation, registration, and dispatch."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TransactionStatus(Enum):
    """Terminal state of one intake transaction attempt."""

    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    RECONCILIATION_RECORD_FAILED = "reconciliation_record_failed"
    INVALID_TARGET = "invalid_target"
    DISPATCH_FAILED = "dispatch_failed"


@dataclass(frozen=True)
class TransactionResult:
    """Safe-to-render outcome without exception text or source content."""

    status: TransactionStatus
    failed_stage: str | None
    dispatch_started: bool


def run_intake_transaction(
    *,
    repository_root: Path,
    configured_parent: str,
    artifact_target: str,
    materialize_artifact: Callable[[Path], None],
    register_workspace_entry: Callable[[], None],
    rollback_partial_state: Callable[[], None],
    record_reconciliation: Callable[[str], None],
    dispatch_processor: Callable[[], None],
) -> TransactionResult:
    """Materialize, register, then dispatch one durable artifact route.

    Callers supply idempotent rollback and reconciliation operations appropriate
    to their workspace writer. Exception values are intentionally not returned,
    because they may contain untrusted source data or sensitive paths.

    Direct-light routes do not create durable artifacts and must not invoke this
    transaction helper.
    """

    try:
        confined_target = resolve_confined_target(
            repository_root=repository_root,
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
        materialize_artifact(confined_target)
    except Exception:
        return _recover_partial_state(
            failed_stage="artifact_write",
            rollback_partial_state=rollback_partial_state,
            record_reconciliation=record_reconciliation,
        )

    try:
        register_workspace_entry()
    except Exception:
        return _recover_partial_state(
            failed_stage="registration_write",
            rollback_partial_state=rollback_partial_state,
            record_reconciliation=record_reconciliation,
        )

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
