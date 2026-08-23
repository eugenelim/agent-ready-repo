"""Read-only planning tests for reviewed legacy workspace migrations."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE = _PACK_ROOT / ".apm/skills/workspace-status/scripts/workspace_status_engine.py"
_FIXTURES = Path(__file__).resolve().parent / "fixtures/work-intake-migration"


def _load_engine():
    """Load the runtime-neutral engine from its authored pack source."""
    spec = importlib.util.spec_from_file_location("migration_planning_engine", _ENGINE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _workspace_bytes() -> bytes:
    """Return a workspace with an exact comment-rich legacy element."""
    return b'''["ini-001"]
name = "Migration"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [
  # Adjacent review context must remain byte-exact.
  "spec/legacy", # punctuation stays
]
active = []
shipped = []
'''


def _selection(engine, root: Path) -> tuple[dict[str, object], dict[str, object]]:
    """Build reviewed selection input from the engine's observed finding."""
    workspace_bytes = (root / "workspace.toml").read_bytes()
    workspace = engine.parse_workspace(root / "workspace.toml")
    canonical = engine.run_canonical_reconciliation(workspace, root)
    membership = canonical.legacy_memberships[0]
    finding = engine.build_migration_finding(workspace_bytes, membership)
    selection = {
        "contract_version": "work-intake-migration-selection.v1",
        "legacy_finding_id": finding["legacy_finding_id"],
        "workspace_fingerprint": hashlib.sha256(workspace_bytes).hexdigest(),
        "source_membership": finding["source_membership"],
        "target_entry": {
            "path": "docs/specs/target/spec.md",
            "kind": "spec",
            "source": {"mode": "repo-origin"},
            "summary": "Reviewed migration target",
            "needs": [],
        },
        "target_membership": {"ini_slug": "ini-001", "collection": "work.queue"},
        "owning_processor": "new-spec",
        "provenance_reference": "docs/specs/target/spec.md",
        "legacy_content_approved_for_ledger": True,
    }
    return selection, finding


def test_ac2_finding_preserves_exact_slice_and_never_dispatches(tmp_path: Path) -> None:
    engine = _load_engine()
    workspace_bytes = _workspace_bytes()
    (tmp_path / "workspace.toml").write_bytes(workspace_bytes)
    workspace = engine.parse_workspace(tmp_path / "workspace.toml")
    membership = engine.run_canonical_reconciliation(workspace, tmp_path).legacy_memberships[0]

    finding = engine.build_migration_finding(workspace_bytes, membership)

    assert finding["source_representation"] == (
        '\n  # Adjacent review context must remain byte-exact.\n'
        '  "spec/legacy", # punctuation stays\n'
    )
    assert finding["source_membership"]["collection"] == "work.queue"
    assert finding["source_membership"]["entry_index"] == 0
    assert finding["candidate_routes"]
    assert finding["dispatchable"] is False
    assert finding["next_action"] == "review-migration-selection"


def test_ac3_selection_is_closed_and_requires_positive_privacy_review(tmp_path: Path) -> None:
    engine = _load_engine()
    (tmp_path / "workspace.toml").write_bytes(_workspace_bytes())
    selection, _finding = _selection(engine, tmp_path)

    parsed, error = engine.validate_migration_selection(selection)
    assert parsed is not None and error is None

    unknown = dict(selection, inferred_kind="spec")
    assert engine.validate_migration_selection(unknown) == (None, "invalid_selection")
    unreviewed = dict(selection, legacy_content_approved_for_ledger=False)
    assert engine.validate_migration_selection(unreviewed) == (
        None,
        "privacy_review_required",
    )


def test_ac4_missing_artifact_returns_processor_without_writes(tmp_path: Path) -> None:
    engine = _load_engine()
    workspace = tmp_path / "workspace.toml"
    workspace.write_bytes(_workspace_bytes())
    selection, _finding = _selection(engine, tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    plan = engine.compute_migration_plan(tmp_path, workspace, selection)

    assert plan.result["result_code"] == "artifact_missing"
    assert plan.result["next_action"] == "new-spec"
    assert plan.result["applicable"] is False
    assert plan.proposed_operation is None
    assert before == sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))


def test_ac8_existing_artifact_plan_is_byte_deterministic_and_read_only(
    tmp_path: Path,
) -> None:
    engine = _load_engine()
    workspace = tmp_path / "workspace.toml"
    workspace.write_bytes(_workspace_bytes())
    target = tmp_path / "docs/specs/target"
    target.mkdir(parents=True)
    (target / "spec.md").write_text("# Spec\n\n**Status:** Approved\n", encoding="utf-8")
    (target / "plan.md").write_text("# Plan\n\n**Status:** Approved\n", encoding="utf-8")
    selection, _finding = _selection(engine, tmp_path)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    first = engine.compute_migration_plan(tmp_path, workspace, selection)
    second = engine.compute_migration_plan(tmp_path, workspace, selection)

    assert first.result["result_code"] == "planned"
    assert first.proposed_operation is not None
    assert json.dumps(first.result, sort_keys=True) == json.dumps(second.result, sort_keys=True)
    assert first.proposed_operation == second.proposed_operation
    validated_selection, error = engine.validate_migration_selection(selection)
    assert error is None
    assert first.proposed_operation["selection_digest"] == (
        engine.migration_selection_digest(validated_selection)
    )
    assert not (tmp_path / ".workspace-migrations.json").exists()
    assert before == {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    parsed = engine.parse_workspace(workspace)
    canonical = engine.run_canonical_reconciliation(parsed, tmp_path)
    repository_identity = engine.canonical_repository_identity(
        parsed, canonical, tmp_path
    )
    assert first.proposed_operation["operation_digest"] == (
        engine._migration_operation_digest(
            first.proposed_operation, repository_identity
        )
    )
    assert first.proposed_operation["operation_digest"] != (
        engine._migration_operation_digest(first.proposed_operation, "0" * 64)
    )


def test_ac7_planner_refuses_workspace_identity_change_during_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = _load_engine()
    workspace = tmp_path / "workspace.toml"
    workspace.write_bytes(_workspace_bytes())
    target = tmp_path / "docs/specs/target"
    target.mkdir(parents=True)
    (target / "spec.md").write_text("# Spec\n\n**Status:** Approved\n", encoding="utf-8")
    (target / "plan.md").write_text("# Plan\n\n**Status:** Approved\n", encoding="utf-8")
    selection, _finding = _selection(engine, tmp_path)
    replacement = tmp_path / "replacement.toml"
    replacement.write_bytes(_workspace_bytes())
    real_open = engine.os.open

    def swapping_open(path: Path, flags: int, *args: object) -> int:
        engine.os.open = real_open
        replacement.replace(workspace)
        return real_open(path, flags, *args)

    monkeypatch.setattr(engine.os, "open", swapping_open)

    plan = engine.compute_migration_plan(tmp_path, workspace, selection)

    assert plan.result["result_code"] == "unsafe_path"
    assert plan.proposed_operation is None


def test_ac7_confinement_rejects_escape_symlink_and_hardlink(tmp_path: Path) -> None:
    engine = _load_engine()
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    assert engine.confine_migration_path(tmp_path, "../escape", require_file=False) is None
    assert engine.confine_migration_path(tmp_path, "/absolute", require_file=False) is None
    assert engine.confine_migration_path(tmp_path, "a\\b", require_file=False) is None

    (tmp_path / "linked.txt").symlink_to(tmp_path / "safe.txt")
    assert engine.confine_migration_path(tmp_path, "linked.txt", require_file=True) is None

    os.link(tmp_path / "safe.txt", tmp_path / "hardlink.txt")
    assert engine.confine_migration_path(tmp_path, "safe.txt", require_file=True) is None
    assert engine.confine_migration_path(tmp_path, "hardlink.txt", require_file=True) is None


def test_ac7_sensitive_slice_refusal_never_echoes_content(tmp_path: Path) -> None:
    engine = _load_engine()
    workspace_bytes = b'''["ini-001"]
status = "active"
["ini-001".work]
queue = [{path = "spec/legacy", token = "ghp_0123456789abcdefghijklmnopqrstuvwxyz"}]
active = []
shipped = []
'''
    (tmp_path / "workspace.toml").write_bytes(workspace_bytes)
    workspace = engine.parse_workspace(tmp_path / "workspace.toml")
    canonical = engine.run_canonical_reconciliation(workspace, tmp_path)
    assert not canonical.legacy_memberships
    assert engine.legacy_slice_contains_sensitive_content(
        b'token = "ghp_0123456789abcdefghijklmnopqrstuvwxyz"'
    )


def test_ac6_semantic_validator_returns_the_published_refusal_codes() -> None:
    engine = _load_engine()
    valid = json.loads((_FIXTURES / "ledger/valid/applied.json").read_text())
    assert engine.validate_migration_ledger_invariants(valid) is None
    semantic_fixtures = _FIXTURES / "ledger/invalid-semantic"
    expected = {
        semantic_fixtures / "operation-digest-mismatch.json": "ledger_invalid",
        semantic_fixtures / "duplicate-operation-id.json": "ledger_invalid",
        semantic_fixtures / "duplicate-confirmation-id.json": "confirmation_reused",
        semantic_fixtures / "duplicate-authorization-subject.json": "confirmation_reused",
        semantic_fixtures / "receipt-binding-mismatch.json": "confirmation_binding_mismatch",
        semantic_fixtures / "rollback-without-receipt.json": "operation_state_conflict",
        semantic_fixtures / "apply-after-rollback.json": "operation_state_conflict",
        semantic_fixtures / "skipped-state.json": "operation_state_conflict",
    }
    for fixture, code in expected.items():
        ledger = json.loads(fixture.read_text())
        assert engine.validate_migration_ledger_invariants(ledger) == code, fixture.name
        assert engine.validate_migration_ledger_shape(ledger) == code, fixture.name
