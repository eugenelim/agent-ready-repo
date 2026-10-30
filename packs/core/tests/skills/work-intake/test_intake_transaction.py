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


def test_no_registration_step_writes_dispatches_and_leaves_workspace_untouched(
    tmp_path: Path,
) -> None:
    transaction = _load_transaction_module()
    repository_root, configured_parent, artifact_target = _transaction_paths(tmp_path)
    workspace = tmp_path / "workspace.toml"
    workspace.write_bytes(b"[backlog]\nopen = []\n")
    before = workspace.read_bytes()
    trace: list[str] = []

    def materialize(target: Path) -> None:
        trace.append("materialize")
        assert (tmp_path / transaction.WORKSPACE_LOCK_FILE).exists()
        target.write_text("artifact", encoding="utf-8")

    result = transaction.run_intake_transaction(
        repository_root=repository_root,
        configured_parent=configured_parent,
        artifact_target=artifact_target,
        materialize_artifact=materialize,
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append("reconcile"),
        dispatch_processor=lambda: trace.append("dispatch"),
    )

    assert result.status is transaction.TransactionStatus.COMMITTED
    assert trace == ["materialize", "dispatch"]
    assert (tmp_path / artifact_target).read_text(encoding="utf-8") == "artifact"
    assert not (tmp_path / transaction.WORKSPACE_LOCK_FILE).exists()
    assert workspace.read_bytes() == before


# ── Tracker-origin source: the record replaces the registration stage ─────────

_TRACKER_LOCATOR = "example-service://work/ITEM-1"
_TRACKER_REVISION = "rev-1"
_TRACKER_PROFILE = {"id": "example-tracker", "version": "1.0"}
_FOREIGN_RECORD = (
    "```toml source-authority\n"
    'contract_version = "source-authority.v1"\n'
    'mode = "tracker-origin"\n'
    'source_ref = "example-service://work/OTHER"\n'
    'source_revision = "rev-9"\n\n[owned_fields]\n```\n'
)


def _load_refresh_module():
    path = _TRANSACTION_PATH.with_name("refresh.py")
    spec = importlib.util.spec_from_file_location("test_tx_tracker_refresh", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_tx_tracker_refresh"] = module
    spec.loader.exec_module(module)
    return module


def _run_tracker_transaction(
    tmp_path: Path,
    *,
    body: str,
    source_kwargs: dict | None = None,
    materialize=None,
    target_name: str = "intent.md",
):
    transaction = _load_transaction_module()
    parent = tmp_path / "docs" / "product" / "intents"
    parent.mkdir(parents=True)
    artifact_target = f"docs/product/intents/{target_name}"
    artifact = tmp_path / artifact_target
    trace: list[str] = []

    def default_materialize(target: Path) -> None:
        trace.append("materialize")
        target.write_text(body, encoding="utf-8")

    def rollback() -> None:
        trace.append("rollback")
        artifact.unlink(missing_ok=True)

    source = transaction.TrackerSource(
        **{
            "locator": _TRACKER_LOCATOR,
            "revision": _TRACKER_REVISION,
            "profile": dict(_TRACKER_PROFILE),
            **(source_kwargs or {}),
        }
    )
    result = transaction.run_intake_transaction(
        repository_root=tmp_path,
        configured_parent="docs/product/intents",
        artifact_target=artifact_target,
        materialize_artifact=materialize or default_materialize,
        rollback_partial_state=rollback,
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
        tracker_source=source,
    )
    return transaction, result, trace, artifact


@pytest.mark.parametrize(
    "body",
    (
        "# Brief\n\nBody text.\n",
        "# Spec\n\n- **Status:** Draft\n\nNo record yet.\n",
    ),
    ids=("brief", "spec"),
)
def test_ac0029_tracker_source_commits_one_record_equal_to_the_declared_values(
    tmp_path: Path, body: str
) -> None:
    refresh = _load_refresh_module()
    transaction, result, trace, artifact = _run_tracker_transaction(tmp_path, body=body)

    assert result.status is transaction.TransactionStatus.COMMITTED
    assert result.dispatch_started is True
    assert trace == ["materialize", "dispatch"]
    written = artifact.read_text(encoding="utf-8")
    assert written.startswith(body)
    authority = refresh.parse_source_authority(written)
    assert authority.source_ref == _TRACKER_LOCATOR
    assert authority.source_revision == _TRACKER_REVISION
    assert authority.tracker_profile == _TRACKER_PROFILE
    assert dict(authority.owned_fields) == {}
    assert not (tmp_path / transaction.WORKSPACE_LOCK_FILE).exists()


def test_ac0029_a_materializer_record_of_its_own_rolls_back_without_dispatch(
    tmp_path: Path,
) -> None:
    transaction, result, trace, artifact = _run_tracker_transaction(
        tmp_path, body="# Brief\n\n" + _FOREIGN_RECORD
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "source_authority_write"
    assert result.dispatch_started is False
    assert trace == ["materialize", "rollback"]
    assert not artifact.exists()
    assert not (tmp_path / transaction.WORKSPACE_LOCK_FILE).exists()


def test_ac0029_a_symlink_left_at_the_target_rolls_back_without_dispatch(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "elsewhere.md"
    outside.write_text("# Elsewhere\n", encoding="utf-8")
    trace: list[str] = []

    def materialize(target: Path) -> None:
        trace.append("materialize")
        target.symlink_to(outside)

    transaction, result, trace2, artifact = _run_tracker_transaction(
        tmp_path, body="", materialize=materialize
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "source_authority_write"
    assert result.dispatch_started is False
    assert trace2 == ["rollback"]
    assert not artifact.is_symlink() and not artifact.exists()
    assert outside.read_text(encoding="utf-8") == "# Elsewhere\n"


def test_ac0029_a_materializer_that_wrote_nothing_rolls_back_without_dispatch(
    tmp_path: Path,
) -> None:
    transaction, result, trace, artifact = _run_tracker_transaction(
        tmp_path, body="", materialize=lambda target: None
    )

    assert result.failed_stage == "source_authority_write"
    assert result.dispatch_started is False
    assert trace == ["rollback"]
    assert not artifact.exists()


@pytest.mark.parametrize(
    "source_kwargs",
    (
        {"profile": None},
        {"profile": {"id": "example-tracker"}},
        {"profile": {"id": "bad\nid", "version": "1.0"}},
        {"mode": "repo-origin"},
        {"locator": "example-service://work/ITEM-1\nuntrusted"},
    ),
    ids=repr,
)
def test_ac0029_a_refused_source_rolls_back_leaving_no_artifact_and_no_dispatch(
    tmp_path: Path, source_kwargs: dict
) -> None:
    transaction, result, trace, artifact = _run_tracker_transaction(
        tmp_path, body="# Brief\n", source_kwargs=source_kwargs
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "source_authority_write"
    assert result.dispatch_started is False
    assert trace == ["materialize", "rollback"]
    assert not artifact.exists()


@pytest.mark.parametrize(
    "locator",
    (
        "example-service://work/ITEM-1\x07",
        "/srv/work/ITEM-1",
        "/Users/someone/work/ITEM-1",
        "example-service://work/../ITEM-1",
        "example-service://work/./ITEM-1",
        "example-service://work\\ITEM-1",
        "example-service://work/someone@example.com",
        "example-service://work/access_token=abc123",
        "example-service://work/ITEM-1?view=full",
        "example-service://work/ITEM-1#section",
    ),
    ids=(
        "control-character",
        "absolute-path",
        "personal-path",
        "parent-segment",
        "dot-segment",
        "backslash",
        "email",
        "secret",
        "query",
        "fragment",
    ),
)
def test_ac0029_a_locator_the_minimizer_would_refuse_or_change_rolls_back(
    tmp_path: Path, locator: str
) -> None:
    transaction, result, trace, artifact = _run_tracker_transaction(
        tmp_path, body="# Brief\n", source_kwargs={"locator": locator}
    )

    assert result.status is transaction.TransactionStatus.ROLLED_BACK
    assert result.failed_stage == "source_authority_write"
    assert result.dispatch_started is False
    assert trace == ["materialize", "rollback"]
    assert not artifact.exists()


def test_ac0029_a_failed_rollback_reports_reconciliation_and_never_dispatches(
    tmp_path: Path,
) -> None:
    transaction = _load_transaction_module()
    (tmp_path / "docs" / "product" / "intents").mkdir(parents=True)
    trace: list[str] = []

    def failing_rollback() -> None:
        raise OSError("injected")

    result = transaction.run_intake_transaction(
        repository_root=tmp_path,
        configured_parent="docs/product/intents",
        artifact_target="docs/product/intents/intent.md",
        materialize_artifact=lambda target: target.write_text(
            "# Brief\n" + _FOREIGN_RECORD, encoding="utf-8"
        ),
        rollback_partial_state=failing_rollback,
        record_reconciliation=lambda stage: trace.append(f"reconcile:{stage}"),
        dispatch_processor=lambda: trace.append("dispatch"),
        tracker_source=transaction.TrackerSource(
            locator=_TRACKER_LOCATOR,
            revision=_TRACKER_REVISION,
            profile=dict(_TRACKER_PROFILE),
        ),
    )

    assert result.status is transaction.TransactionStatus.RECONCILIATION_REQUIRED
    assert result.failed_stage == "source_authority_write"
    assert trace == ["reconcile:source_authority_write"]


def test_ac0029_tracker_source_replaces_the_registration_stage(tmp_path: Path) -> None:
    transaction = _load_transaction_module()
    (tmp_path / "docs" / "product" / "intents").mkdir(parents=True)
    trace: list[str] = []
    result = transaction.run_intake_transaction(
        repository_root=tmp_path,
        configured_parent="docs/product/intents",
        artifact_target="docs/product/intents/intent.md",
        materialize_artifact=lambda target: target.write_text("# Brief\n", encoding="utf-8"),
        rollback_partial_state=lambda: trace.append("rollback"),
        record_reconciliation=lambda stage: trace.append("reconcile"),
        dispatch_processor=lambda: trace.append("dispatch"),
        register_workspace_entry=lambda: trace.append("register"),
        tracker_source=transaction.TrackerSource(
            locator=_TRACKER_LOCATOR,
            revision=_TRACKER_REVISION,
            profile=dict(_TRACKER_PROFILE),
        ),
    )

    assert result.status is transaction.TransactionStatus.COMMITTED
    assert trace == ["dispatch"]
