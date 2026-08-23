"""Durability, authorization, recovery, and rollback tests for migration effects."""

from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK_ROOT / ".apm/skills/workspace-status/scripts"
_ENGINE = _SCRIPTS / "workspace_status_engine.py"
_STATUS = _SCRIPTS / "workspace_status.py"


def _load_engine(module_name: str):
    """Load the authored engine under a unique test module name."""
    spec = importlib.util.spec_from_file_location(module_name, _ENGINE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_status(module_name: str):
    """Load the authored CLI/effect module under a unique test module name."""
    spec = importlib.util.spec_from_file_location(module_name, _STATUS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _workspace() -> bytes:
    """Return an authorized workspace containing one exact legacy source slice."""
    return b'''[authorization.migration]
contract_version = "work-intake-migration-authorization.v1"
approver_roles = ["migration-approver"]

["ini-001"]
name = "Migration"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [
  # Exact rollback context.
  "spec/legacy", # exact punctuation
]
active = []
shipped = []
'''


def _setup(tmp_path: Path):
    """Create one planned migration and return its modules and reviewed input."""
    engine = _load_engine(f"effects_engine_{tmp_path.name}")
    status = _load_status(f"effects_status_{tmp_path.name}")
    assert status._bind_engine()
    workspace_path = tmp_path / "workspace.toml"
    workspace_path.write_bytes(_workspace())
    target = tmp_path / "docs/specs/target"
    target.mkdir(parents=True)
    (target / "spec.md").write_text("# Target\n\n**Status:** Approved\n", encoding="utf-8")
    (target / "plan.md").write_text("# Plan\n\n**Status:** Approved\n", encoding="utf-8")
    workspace = engine.parse_workspace(workspace_path)
    canonical = engine.run_canonical_reconciliation(workspace, tmp_path)
    finding = engine.build_migration_finding(
        workspace_path.read_bytes(), canonical.legacy_memberships[0]
    )
    selection = {
        "contract_version": "work-intake-migration-selection.v1",
        "legacy_finding_id": finding["legacy_finding_id"],
        "workspace_fingerprint": hashlib.sha256(workspace_path.read_bytes()).hexdigest(),
        "source_membership": finding["source_membership"],
        "target_entry": {
            "path": "docs/specs/target/spec.md",
            "kind": "spec",
            "source": {"mode": "repo-origin", "ref": "tracker/example"},
            "summary": "Reviewed target",
            "needs": [],
        },
        "target_membership": {"ini_slug": "ini-001", "collection": "work.queue"},
        "owning_processor": "new-spec",
        "provenance_reference": "docs/specs/target/spec.md",
        "legacy_content_approved_for_ledger": True,
    }
    plan = engine.compute_migration_plan(tmp_path, workspace_path, selection)
    assert plan.proposed_operation is not None
    return engine, status, selection, plan.proposed_operation


def _confirmation(
    operation: dict[str, object],
    *,
    action: str,
    evidence_digit: str,
    when: datetime.datetime,
) -> dict[str, object]:
    """Build out-of-band evidence with deterministic opaque test identifiers."""
    return {
        "contract_version": "work-intake-migration-confirmation.v1",
        "confirmation_id": f"confirmation-{evidence_digit * 32}",
        "action": action,
        "operation_id": operation["operation_id"],
        "operation_digest": operation["operation_digest"],
        "authorization_subject": f"subject-{evidence_digit * 32}",
        "role": "migration-approver",
        "confirmed_at": when.isoformat().replace("+00:00", "Z"),
        "authorization_source": "current-human-session",
    }


def test_ac8_apply_is_ledger_first_and_ac10_rollback_restores_exact_bytes(
    tmp_path: Path,
) -> None:
    engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    original_workspace = (tmp_path / "workspace.toml").read_bytes()
    artifact = tmp_path / "docs/specs/target/spec.md"
    artifact_before = artifact.read_bytes()

    applied = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )

    assert applied["result_code"] == "applied"
    ledger = json.loads((tmp_path / ".workspace-migrations.json").read_text())
    assert engine.validate_migration_ledger_shape(ledger) is None
    assert ledger["operations"][0]["state"] == "applied"
    receipt = ledger["operations"][0]["confirmation_receipts"][0]
    assert receipt["consumed_before_effect"] is True
    assert "role" not in receipt
    assert artifact.read_bytes() == artifact_before

    rolled_back = status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="2", when=now),
        now=now,
    )

    assert rolled_back["result_code"] == "rolled_back"
    assert (tmp_path / "workspace.toml").read_bytes() == original_workspace
    assert artifact.read_bytes() == artifact_before
    ledger = json.loads((tmp_path / ".workspace-migrations.json").read_text())
    assert ledger["operations"][0]["state"] == "rolled_back"
    assert [item["action"] for item in ledger["operations"][0]["confirmation_receipts"]] == [
        "apply",
        "rollback",
    ]


def test_ac9_pending_before_workspace_recovers_with_fresh_evidence(tmp_path: Path) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    failed = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
        failure_point="workspace_stage_before",
    )
    assert failed["result_code"] == "write_failed"
    ledger = json.loads((tmp_path / ".workspace-migrations.json").read_text())
    assert ledger["operations"][0]["state"] == "pending"
    assert b'"spec/legacy"' in (tmp_path / "workspace.toml").read_bytes()

    replay = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="2", when=now),
        now=now,
    )
    assert replay["result_code"] == "applied"
    ledger = json.loads((tmp_path / ".workspace-migrations.json").read_text())
    assert len(ledger["operations"][0]["confirmation_receipts"]) == 2


def test_ac9_pending_apply_rejects_shadowed_applied_fingerprint(
    tmp_path: Path,
) -> None:
    """A mutable pending fingerprint cannot relabel unchanged legacy bytes."""
    engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    failed = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
        failure_point="workspace_stage_before",
    )
    assert failed["result_code"] == "write_failed"
    workspace_before = (tmp_path / "workspace.toml").read_bytes()
    ledger_path = tmp_path / ".workspace-migrations.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    pending = ledger["operations"][0]
    pending["applied_workspace_fingerprint"] = pending[
        "pre_apply_workspace_fingerprint"
    ]
    assert engine.validate_migration_ledger_shape(ledger) is None
    ledger_path.write_text(
        json.dumps(ledger, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    refused = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="2", when=now),
        now=now,
    )

    assert refused["result_code"] == "ledger_changed"
    assert (tmp_path / "workspace.toml").read_bytes() == workspace_before
    persisted = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert persisted["operations"][0]["state"] == "pending"
    assert len(persisted["operations"][0]["confirmation_receipts"]) == 1


def test_ac10_idempotent_results_require_exact_recorded_workspace_bytes(
    tmp_path: Path,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="2", when=now),
        now=now,
    )["result_code"] == "already_applied"
    assert status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="3", when=now),
        now=now,
    )["result_code"] == "rolled_back"
    assert status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="4", when=now),
        now=now,
    )["result_code"] == "already_rolled_back"


@pytest.mark.parametrize("ledger_state", ["applied", "rolled_back"])
def test_ac10_idempotent_results_refuse_external_workspace_edits(
    tmp_path: Path,
    ledger_state: str,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"
    if ledger_state == "rolled_back":
        assert status.rollback_migration_operation(
            tmp_path,
            operation["operation_id"],
            _confirmation(
                operation, action="rollback", evidence_digit="2", when=now
            ),
            now=now,
        )["result_code"] == "rolled_back"
    workspace_path = tmp_path / "workspace.toml"
    workspace_path.write_bytes(workspace_path.read_bytes() + b"\n# external edit\n")

    if ledger_state == "applied":
        refused = status.apply_migration_operation(
            tmp_path,
            selection,
            operation["operation_id"],
            _confirmation(operation, action="apply", evidence_digit="3", when=now),
            now=now,
        )
    else:
        refused = status.rollback_migration_operation(
            tmp_path,
            operation["operation_id"],
            _confirmation(
                operation, action="rollback", evidence_digit="3", when=now
            ),
            now=now,
        )

    assert refused["result_code"] == "recovery_conflict"


def test_ac9_pending_after_workspace_replace_recovers_without_duplicate(
    tmp_path: Path,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    failed = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
        failure_point="workspace_replace_after",
    )
    assert failed["result_code"] == "write_failed"
    assert b'docs/specs/target/spec.md' in (tmp_path / "workspace.toml").read_bytes()

    recovered = status.recover_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="2", when=now),
        action="apply",
        selection_raw=selection,
        now=now,
    )
    assert recovered["result_code"] == "applied"
    parsed = _engine.parse_workspace(tmp_path / "workspace.toml")
    canonical = _engine.run_canonical_reconciliation(parsed, tmp_path)
    targets = [
        membership for membership in canonical.memberships
        if membership.entry.path == "docs/specs/target/spec.md"
    ]
    assert len(targets) == 1


def test_ac7_selection_read_refuses_identity_change_during_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    status = _load_status(f"selection_read_{tmp_path.name}")
    assert status._bind_engine()
    selection = tmp_path / "selection.json"
    selection.write_text('{"reviewed":true}', encoding="utf-8")
    replacement = tmp_path / "replacement.json"
    replacement.write_text('{"reviewed":true}', encoding="utf-8")
    real_open = status.os.open

    def swapping_open(path: Path, flags: int, *args: object) -> int:
        status.os.open = real_open
        replacement.replace(selection)
        return real_open(path, flags, *args)

    monkeypatch.setattr(status.os, "open", swapping_open)

    value, error = status._migration_input_json(
        tmp_path, "selection.json", invalid_code="invalid_selection"
    )

    assert value is None
    assert error == "unsafe_path"


def test_ac8_changed_repository_identity_is_rejected_by_ledger_validation(
    tmp_path: Path,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"
    ledger_path = tmp_path / ".workspace-migrations.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["repository_identity"] = "0" * 64
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    workspace_before = (tmp_path / "workspace.toml").read_bytes()

    refused = status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="2", when=now),
        now=now,
    )

    assert refused["result_code"] == "ledger_invalid"
    assert (tmp_path / "workspace.toml").read_bytes() == workspace_before


def test_ac10_independent_workspace_change_refuses_before_rollback_receipt(
    tmp_path: Path,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"
    workspace_path = tmp_path / "workspace.toml"
    workspace_path.write_bytes(workspace_path.read_bytes() + b"\n# independent change\n")
    workspace_before = workspace_path.read_bytes()
    ledger_before = (tmp_path / ".workspace-migrations.json").read_bytes()

    refused = status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="2", when=now),
        now=now,
    )

    assert refused["result_code"] == "recovery_conflict"
    assert workspace_path.read_bytes() == workspace_before
    assert (tmp_path / ".workspace-migrations.json").read_bytes() == ledger_before


def test_ac10_external_exact_revert_refuses_applied_rollback(tmp_path: Path) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    original_workspace = (tmp_path / "workspace.toml").read_bytes()
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"
    (tmp_path / "workspace.toml").write_bytes(original_workspace)
    ledger_before = (tmp_path / ".workspace-migrations.json").read_bytes()

    refused = status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="2", when=now),
        now=now,
    )

    assert refused["result_code"] == "recovery_conflict"
    assert (tmp_path / "workspace.toml").read_bytes() == original_workspace
    assert (tmp_path / ".workspace-migrations.json").read_bytes() == ledger_before


def test_ac10_rollback_pending_recovers_only_recorded_exact_bytes(
    tmp_path: Path,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    original_workspace = (tmp_path / "workspace.toml").read_bytes()
    assert status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
    )["result_code"] == "applied"

    failed = status.rollback_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="2", when=now),
        now=now,
        failure_point="workspace_replace_after",
    )
    assert failed["result_code"] == "write_failed"
    ledger = json.loads((tmp_path / ".workspace-migrations.json").read_text())
    assert ledger["operations"][0]["state"] == "rollback_pending"
    assert ledger["operations"][0]["rolled_back_workspace_fingerprint"] == (
        hashlib.sha256(original_workspace).hexdigest()
    )
    assert (tmp_path / "workspace.toml").read_bytes() == original_workspace

    recovered = status.recover_migration_operation(
        tmp_path,
        operation["operation_id"],
        _confirmation(operation, action="rollback", evidence_digit="3", when=now),
        action="rollback",
        now=now,
    )

    assert recovered["result_code"] == "rolled_back"
    assert (tmp_path / "workspace.toml").read_bytes() == original_workspace


@pytest.mark.parametrize(
    ("field", "replacement", "expected_code"),
    [
        ("legacy_finding_id", "legacy-" + "0" * 64, "selection_mismatch"),
        ("workspace_fingerprint", "0" * 64, "selection_mismatch"),
        ("provenance_reference", "tracker/example", "selection_mismatch"),
        ("legacy_content_approved_for_ledger", False, "privacy_review_required"),
    ],
)
def test_ac8_pending_apply_rejects_any_changed_closed_selection_field(
    tmp_path: Path,
    field: str,
    replacement: object,
    expected_code: str,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    failed = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
        failure_point="workspace_stage_before",
    )
    assert failed["result_code"] == "write_failed"
    workspace_before = (tmp_path / "workspace.toml").read_bytes()
    ledger_before = (tmp_path / ".workspace-migrations.json").read_bytes()
    changed_selection = json.loads(json.dumps(selection))
    changed_selection[field] = replacement

    refused = status.apply_migration_operation(
        tmp_path,
        changed_selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="2", when=now),
        now=now,
    )

    assert refused["result_code"] == expected_code
    assert (tmp_path / "workspace.toml").read_bytes() == workspace_before
    assert (tmp_path / ".workspace-migrations.json").read_bytes() == ledger_before


@pytest.mark.parametrize(
    ("failure_point", "ledger_present", "target_present"),
    [
        ("ledger_stage_before", False, False),
        ("ledger_stage_after", False, False),
        ("ledger_replace_before", False, False),
        ("ledger_replace_after", True, False),
        ("workspace_stage_before", True, False),
        ("workspace_stage_after", True, False),
        ("workspace_replace_before", True, False),
        ("workspace_replace_after", True, True),
    ],
)
def test_ac9_failure_seams_leave_reviewed_legacy_or_complete_target_state(
    tmp_path: Path,
    failure_point: str,
    ledger_present: bool,
    target_present: bool,
) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    result = status.apply_migration_operation(
        tmp_path,
        selection,
        operation["operation_id"],
        _confirmation(operation, action="apply", evidence_digit="1", when=now),
        now=now,
        failure_point=failure_point,
    )
    assert result["result_code"] == "write_failed"
    assert (tmp_path / ".workspace-migrations.json").exists() is ledger_present
    workspace_bytes = (tmp_path / "workspace.toml").read_bytes()
    assert (b"docs/specs/target/spec.md" in workspace_bytes) is target_present
    assert (b'"spec/legacy"' in workspace_bytes) is (not target_present)
    assert (tmp_path / "docs/specs/target/spec.md").exists()


def test_ac25_reused_or_stale_confirmation_refuses_without_mutation(tmp_path: Path) -> None:
    _engine, status, selection, operation = _setup(tmp_path)
    now = datetime.datetime(2026, 8, 21, 12, 0, tzinfo=datetime.UTC)
    confirmation = _confirmation(
        operation, action="apply", evidence_digit="1", when=now
    )
    assert status.apply_migration_operation(
        tmp_path, selection, operation["operation_id"], confirmation, now=now
    )["result_code"] == "applied"
    workspace_before = (tmp_path / "workspace.toml").read_bytes()
    ledger_before = (tmp_path / ".workspace-migrations.json").read_bytes()

    replay = status.apply_migration_operation(
        tmp_path, selection, operation["operation_id"], confirmation, now=now
    )
    assert replay["result_code"] == "confirmation_reused"
    assert (tmp_path / "workspace.toml").read_bytes() == workspace_before
    assert (tmp_path / ".workspace-migrations.json").read_bytes() == ledger_before

    stale = _confirmation(
        operation,
        action="rollback",
        evidence_digit="2",
        when=now - datetime.timedelta(minutes=6),
    )
    refused = status.rollback_migration_operation(
        tmp_path, operation["operation_id"], stale, now=now
    )
    assert refused["result_code"] == "confirmation_stale"
    assert (tmp_path / "workspace.toml").read_bytes() == workspace_before
    assert (tmp_path / ".workspace-migrations.json").read_bytes() == ledger_before


@pytest.mark.parametrize(
    "legacy_slice",
    [
        b'password = "not-a-real-secret"\r\n',
        b"Authorization: Bearer not-a-real-token\n",
        b"https://example.invalid/?api_key=not-a-real-key",
        b"-----BEGIN PRIVATE KEY-----",
        b"ghp_0123456789abcdefghijklmnopqrstuvwxyz",
        b"xoxb-0123456789-example",
        b"AKIA0123456789ABCDEF",
    ],
)
def test_ac7_every_closed_credential_class_refuses_without_echo(
    legacy_slice: bytes,
) -> None:
    engine = _load_engine(f"detector_{hash(legacy_slice)}")
    assert engine.scan_legacy_slice_for_sensitive_content(legacy_slice) is True


@pytest.mark.parametrize(
    "near_miss",
    [
        b"password policy = reviewed",
        b"authorization = none",
        b"https://example.invalid/?token=",
        b"ghp_short",
        b"AKIA0123",
    ],
)
def test_ac7_credential_detector_near_misses_remain_reviewable(near_miss: bytes) -> None:
    engine = _load_engine(f"near_miss_{hash(near_miss)}")
    assert engine.scan_legacy_slice_for_sensitive_content(near_miss) is False


def test_ac25_policy_is_closed_to_public_capability_roles() -> None:
    status = _load_status("closed_policy_status")
    confirmation = {"role": "migration-approver"}
    valid = {
        "authorization": {
            "migration": {
                "contract_version": "work-intake-migration-authorization.v1",
                "approver_roles": ["migration-approver"],
            }
        }
    }
    digest, error = status.resolve_migration_authorization(valid, confirmation)
    assert error is None
    assert digest == hashlib.sha256(b"migration-approver").hexdigest()

    for invalid_role in ("team-platform", "person-jane", "example-org", "account-123"):
        invalid = {
            "authorization": {
                "migration": {
                    "contract_version": "work-intake-migration-authorization.v1",
                    "approver_roles": [invalid_role],
                }
            }
        }
        assert status.resolve_migration_authorization(invalid, confirmation) == (
            None,
            "migration_policy_invalid",
        )
