"""Failure-injection tests for work-intake transaction sequencing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_TRANSACTION_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_transaction.py"
)


def _load_transaction_module():
    spec = importlib.util.spec_from_file_location("intake_transaction", _TRANSACTION_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["intake_transaction"] = module
    spec.loader.exec_module(module)
    return module


def _transaction_paths(tmp_path: Path) -> tuple[Path, str, str]:
    parent = tmp_path / "docs" / "product" / "intents"
    parent.mkdir(parents=True)
    return tmp_path, "docs/product/intents", "docs/product/intents/intent.md"


def test_artifact_write_failure_rolls_back_without_registration_or_dispatch(
    tmp_path: Path,
) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    artifact = tmp_path / artifact_target
    workspace = tmp_path / "workspace.toml"
    trace: list[str] = []

    def materialize(target: Path) -> None:
        trace.append("materialize")
        target.write_text("partial", encoding="utf-8")
        raise OSError("injected artifact failure")

    def rollback() -> None:
        trace.append("rollback")
        artifact.unlink(missing_ok=True)
        workspace.unlink(missing_ok=True)

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=materialize,
        register_workspace_entry=lambda: trace.append("register"),
        rollback_partial_state=rollback,
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "artifact_write"
    assert result.dispatch_started is False
    assert trace == ["materialize", "rollback"]
    assert not artifact.exists()
    assert not workspace.exists()


def test_registration_write_failure_rolls_back_without_dispatch(tmp_path: Path) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    artifact = tmp_path / artifact_target
    workspace = tmp_path / "workspace.toml"
    trace: list[str] = []

    def materialize(target: Path) -> None:
        trace.append("materialize")
        target.write_text("durable artifact", encoding="utf-8")

    def register() -> None:
        trace.append("register")
        workspace.write_text("partial registration", encoding="utf-8")
        raise OSError("injected registration failure")

    def rollback() -> None:
        trace.append("rollback")
        artifact.unlink(missing_ok=True)
        workspace.unlink(missing_ok=True)

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=materialize,
        register_workspace_entry=register,
        rollback_partial_state=rollback,
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "registration_write"
    assert result.dispatch_started is False
    assert trace == ["materialize", "register", "rollback"]
    assert not artifact.exists()
    assert not workspace.exists()


def test_rollback_failure_records_reconciliation_and_never_dispatches(
    tmp_path: Path,
) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    artifact = tmp_path / artifact_target
    finding = tmp_path / "reconciliation.finding"
    trace: list[str] = []

    def materialize(target: Path) -> None:
        target.write_text("durable artifact", encoding="utf-8")

    def register() -> None:
        raise OSError("injected registration failure")

    def rollback() -> None:
        trace.append("rollback")
        raise OSError("injected rollback failure")

    def reconcile(stage: str) -> None:
        trace.append(f"reconcile:{stage}")
        finding.write_text(
            f"{stage}: non-dispatchable reconciliation required\n",
            encoding="utf-8",
        )

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=materialize,
        register_workspace_entry=register,
        rollback_partial_state=rollback,
        record_reconciliation=reconcile,
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.RECONCILIATION_REQUIRED
    assert result.failed_stage == "registration_write"
    assert result.dispatch_started is False
    assert trace == ["rollback", "reconcile:registration_write"]
    assert artifact.exists()
    assert finding.read_text(encoding="utf-8") == (
        "registration_write: non-dispatchable reconciliation required\n"
    )


def test_reconciliation_write_failure_returns_safe_terminal_state(
    tmp_path: Path,
) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    artifact = tmp_path / artifact_target
    trace: list[str] = []

    def materialize(target: Path) -> None:
        target.write_text("durable artifact", encoding="utf-8")

    def register() -> None:
        raise OSError("injected registration secret")

    def rollback() -> None:
        trace.append("rollback")
        raise OSError("injected rollback secret")

    def reconcile(stage: str) -> None:
        trace.append(f"reconcile:{stage}")
        raise OSError("injected reconciliation secret")

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=materialize,
        register_workspace_entry=register,
        rollback_partial_state=rollback,
        record_reconciliation=reconcile,
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert (
        result.status
        is transaction.TransactionStatus.RECONCILIATION_RECORD_FAILED
    )
    assert result.failed_stage == "registration_write"
    assert result.dispatch_started is False
    assert trace == ["rollback", "reconcile:registration_write"]
    assert artifact.exists()
    assert "secret" not in repr(result)


def test_dispatch_begins_only_after_both_durable_writes(tmp_path: Path) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    trace: list[str] = []

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=lambda target: trace.append("materialize"),
        register_workspace_entry=lambda: trace.append("register"),
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.COMMITTED
    assert result.failed_stage is None
    assert result.dispatch_started is True
    assert trace == ["materialize", "register", "dispatch"]


def test_dispatch_failure_returns_safe_terminal_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    trace: list[str] = []

    def dispatch() -> None:
        trace.append("dispatch")
        raise RuntimeError("raw source secret must not escape")

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=lambda target: trace.append("materialize"),
        register_workspace_entry=lambda: trace.append("register"),
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=dispatch,
    )

    assert result.status is transaction.TransactionStatus.DISPATCH_FAILED
    assert result.failed_stage == "processor_dispatch"
    assert result.dispatch_started is True
    assert trace == ["materialize", "register", "dispatch"]
    assert "secret" not in repr(result)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "configured_parent,artifact_target",
    [
        ("docs/product/intents", "/tmp/outside.md"),
        ("docs/product/intents", "docs/product/intents/../outside.md"),
        ("docs/product/intents", "C:\\outside.md"),
        ("docs/product/intents", "docs//product/intents/intent.md"),
        ("docs/product/intents", "docs/product/intents/./intent.md"),
    ],
)
def test_unsafe_targets_stop_before_any_callback(
    tmp_path: Path,
    configured_parent: str,
    artifact_target: str,
) -> None:
    transaction = _load_transaction_module()
    (tmp_path / "docs" / "product" / "intents").mkdir(parents=True)
    trace: list[str] = []

    result = transaction.run_intake_transaction(
        repository_root=tmp_path,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=lambda target: trace.append("materialize"),
        register_workspace_entry=lambda: trace.append("register"),
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.INVALID_TARGET
    assert result.failed_stage == "path_validation"
    assert result.dispatch_started is False
    assert trace == []


def test_symlink_escape_stops_before_any_callback(tmp_path: Path) -> None:
    transaction = _load_transaction_module()
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    parent = tmp_path / "docs" / "product"
    parent.mkdir(parents=True)
    (parent / "intents").symlink_to(outside, target_is_directory=True)
    trace: list[str] = []

    try:
        result = transaction.run_intake_transaction(
            repository_root=tmp_path,
            configured_parent="docs/product/intents",
            artifact_target="docs/product/intents/intent.md",
            materialize_artifact=lambda target: trace.append("materialize"),
            register_workspace_entry=lambda: trace.append("register"),
            rollback_partial_state=lambda: trace.append("rollback"),
            record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
            dispatch_processor=lambda: trace.append("dispatch"),
        )
    finally:
        outside.rmdir()

    assert result.status is transaction.TransactionStatus.INVALID_TARGET
    assert trace == []


def test_symlink_loop_stops_before_any_callback(tmp_path: Path) -> None:
    transaction = _load_transaction_module()
    parent = tmp_path / "docs" / "product"
    parent.mkdir(parents=True)
    (parent / "intents").symlink_to("intents", target_is_directory=True)
    trace: list[str] = []

    result = transaction.run_intake_transaction(
        repository_root=tmp_path,
        configured_parent="docs/product/intents",
        artifact_target="docs/product/intents/intent.md",
        materialize_artifact=lambda target: trace.append("materialize"),
        register_workspace_entry=lambda: trace.append("register"),
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.INVALID_TARGET
    assert trace == []
