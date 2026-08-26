"""Wave 4 pause, receipt, initiative, and read-only projection contracts."""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _close_work():
    return _load(
        ROOT / "packs/core/.apm/skills/close-work/scripts/close_work.py",
        "close_work_t4_tests",
    )


def _workspace_status():
    return _load(
        ROOT
        / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py",
        "workspace_status_t4_tests",
    )


def _authority(close_work, action: str, resource: str) -> dict[str, object]:
    record = {
        "authorized_actor_role": "repository-maintainer",
        "grant_source": "policy:maintainer-closeout",
        "action": action,
        "resource": resource,
        "evidence_ref": "evidence:current",
        "host_session_provenance": "session:current",
    }
    fact = close_work.resolve_mutation_authority(
        grant_record=record,
        authority_evidence_ref="authority:resolved-policy",
    )
    assert fact is not None
    return {**record, "authority_fact": fact}


def test_pause_is_reference_only_restorable_and_non_closing() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"
    result = close_work.plan_pause(
        work_mode="spec-backed",
        artifact_status="Implementing",
        coordination_surface=surface,
        writable=True,
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        restore_action="resume-from-pinned-contract",
        **_authority(close_work, "write-pause-overlay", surface),
    )

    assert result.code == "pause-overlay-ready"
    assert result.lifecycle_phase == "Implementing"
    assert result.overlay == "Paused"
    assert result.disposition is None
    assert result.cooling_started is False
    assert result.permission_granted is False
    assert set(dataclasses.asdict(result.record)) == {
        "contract_locator",
        "contract_fingerprint",
        "plan_locator",
        "plan_fingerprint",
        "artifact_status",
        "evidence_refs",
        "coordination_locator",
        "restore_action",
    }
    restored = close_work.validate_pause_resume(
        result.record,
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        artifact_status="Implementing",
        evidence_refs=("evidence:current",),
        coordination_locator=surface,
        restore_action="resume-from-pinned-contract",
    )
    assert restored.code == "pause-restorable"


def test_pause_refuses_raw_content_missing_surface_and_direct_light() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"
    common = {
        "artifact_status": "Implementing",
        "coordination_surface": surface,
        "writable": True,
        "contract_locator": "delivery-contract:current",
        "contract_fingerprint": "sha256:contract",
        "plan_locator": "delivery-plan:current",
        "plan_fingerprint": "sha256:plan",
        "restore_action": "resume-from-pinned-contract",
        **_authority(close_work, "write-pause-overlay", surface),
    }
    assert close_work.plan_pause(
        work_mode="spec-backed", raw_plan="embedded instructions", **common
    ).code == "untrusted-content-refused"
    assert close_work.plan_pause(
        work_mode="spec-backed", **{**common, "writable": False}
    ).code == "pause-surface-required"
    assert close_work.plan_pause(
        work_mode="direct-light", **common
    ).code == "work-intake-promotion-required"


def test_pause_requires_authoritative_grant_and_resume_refuses_drift() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"
    authority = _authority(close_work, "write-pause-overlay", surface)
    authority["grant_source"] = "self-asserted"
    refused = close_work.plan_pause(
        work_mode="spec-backed",
        artifact_status="Ready",
        coordination_surface=surface,
        writable=True,
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        restore_action="resume-from-pinned-contract",
        **authority,
    )
    assert refused.code == "authorization-required"
    assert refused.mutated == ()


def test_pause_resume_revalidates_every_reference() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"
    planned = close_work.plan_pause(
        work_mode="spec-backed",
        artifact_status="Implementing",
        coordination_surface=surface,
        writable=True,
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        restore_action="resume-from-pinned-contract",
        **_authority(close_work, "write-pause-overlay", surface),
    )
    current = {
        "contract_locator": "delivery-contract:current",
        "contract_fingerprint": "sha256:contract",
        "plan_locator": "delivery-plan:current",
        "plan_fingerprint": "sha256:plan",
        "artifact_status": "Implementing",
        "evidence_refs": ("evidence:current",),
        "coordination_locator": surface,
        "restore_action": "resume-from-pinned-contract",
    }
    cases = {
        "contract_locator": "delivery-contract:moved",
        "contract_fingerprint": "sha256:changed-contract",
        "plan_locator": "delivery-plan:moved",
        "plan_fingerprint": "sha256:changed-plan",
        "artifact_status": "Ready",
        "evidence_refs": ("evidence:changed",),
        "coordination_locator": "runtime-coordination:other",
        "restore_action": "resume-from-another-contract",
    }
    for field, changed in cases.items():
        result = close_work.validate_pause_resume(
            planned.record, **{**current, field: changed}
        )
        assert result.code == "pause-reference-drift", field
        assert result.mutated == (), field
    unavailable = close_work.validate_pause_resume(
        planned.record, **{**current, "evidence_refs": ()}
    )
    assert unavailable.code == "pause-evidence-unavailable"
    assert unavailable.mutated == ()


def test_pause_resume_revalidates_the_stored_overlay() -> None:
    close_work = _close_work()
    tampered = close_work.PauseOverlay(
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        artifact_status="Implementing",
        evidence_refs=("evidence:current",),
        coordination_locator="runtime-coordination:workspace",
        restore_action="resume-from-other-contract",
    )
    result = close_work.validate_pause_resume(
        tampered,
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        artifact_status="Implementing",
        evidence_refs=("evidence:current",),
        coordination_locator="runtime-coordination:workspace",
        restore_action="resume-from-pinned-contract",
    )
    assert result.code == "pause-reference-drift"
    assert result.mutated == ()


def test_receipt_is_exactly_four_fields_and_dependency_scoped() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"
    result = close_work.plan_completion_receipt(
        live_dependency=True,
        compatible_surface=surface,
        delivery_id="delivery:wave4",
        outcome="completed",
        completion_event="work-loop:gates-clean",
        **_authority(close_work, "write-completion-receipt", surface),
    )
    assert result.code == "receipt-write-confirmation-required"
    assert dataclasses.asdict(result.receipt) == {
        "delivery_id": "delivery:wave4",
        "outcome": "completed",
        "completion_event": "work-loop:gates-clean",
        "evidence_ref": "evidence:current",
    }
    assert close_work.plan_completion_receipt(
        live_dependency=False, compatible_surface=surface
    ).code == "receipt-not-required"


def test_missing_receipt_surface_and_self_asserted_effect_fail_closed() -> None:
    close_work = _close_work()
    missing = close_work.plan_completion_receipt(
        live_dependency=True, compatible_surface=None
    )
    assert missing.code == "receipt-surface-required"
    assert missing.disposition == "retain-exception"
    assert missing.schema_created is False

    authority = _authority(
        close_work,
        "remove-last-completion-receipt",
        "runtime-coordination:workspace#receipt",
    )
    authority["grant_source"] = "self-asserted"
    removal = close_work.plan_receipt_removal(
        receipt_fingerprint="sha256:receipt", **authority
    )
    assert removal.code == "authorization-required"
    assert removal.mutated == ()

    write_authority = _authority(
        close_work, "write-completion-receipt", "runtime-coordination:workspace"
    )
    write_authority["grant_source"] = "self-asserted"
    write = close_work.plan_completion_receipt(
        live_dependency=True,
        compatible_surface="runtime-coordination:workspace",
        delivery_id="delivery:wave4",
        outcome="completed",
        completion_event="work-loop:gates-clean",
        **write_authority,
    )
    assert write.code == "authorization-required"
    assert write.mutated == ()
    envelope_only = close_work.plan_completion_receipt(
        live_dependency=True,
        compatible_surface="runtime-coordination:workspace",
        delivery_id="delivery:wave4",
        outcome="completed",
        completion_event="work-loop:gates-clean",
        authorized_actor_role="repository-maintainer",
        grant_source="policy:maintainer-closeout",
        action="write-completion-receipt",
        resource="runtime-coordination:workspace",
        evidence_ref="evidence:current",
        host_session_provenance="session:current",
    )
    assert envelope_only.code == "authorization-required"
    assert envelope_only.mutated == ()


def test_receipt_removal_confirmation_expires_on_fingerprint_drift() -> None:
    close_work = _close_work()
    result = close_work.plan_receipt_removal(
        receipt_fingerprint="sha256:confirmed",
        current_receipt_fingerprint="sha256:changed",
        current_receipt_evidence_ref="evidence:current-receipt",
        **_authority(
            close_work,
            "remove-last-completion-receipt",
            "runtime-coordination:workspace#receipt",
        ),
    )
    assert result.code == "confirmation-expired"
    assert result.mutated == ()
    unavailable = close_work.plan_receipt_removal(
        receipt_fingerprint="sha256:confirmed",
        **_authority(
            close_work,
            "remove-last-completion-receipt",
            "runtime-coordination:workspace#receipt",
        ),
    )
    assert unavailable.code == "receipt-fingerprint-unavailable"


def test_initiative_cleanup_is_independent_from_rfc_family_retention() -> None:
    close_work = _close_work()
    result = close_work.plan_initiative_closeout(
        shaping_residue=(),
        build_residue=(),
        live_dependencies=(),
        contextual_anchor="rfc-wave-set",
        coordination_fingerprint="sha256:current",
        current_coordination_fingerprint="sha256:current",
        current_coordination_evidence_ref="evidence:current-coordination",
        **_authority(
            close_work,
            "compact-settled-coordination", "runtime-coordination:workspace"
        ),
    )
    assert result.workspace_action == "compact-settled-coordination"
    assert result.artifact_action == "retain-or-reclassify-anchored-family"
    assert result.lifecycle_schema_created is False
    assert result.permission_granted is False


def test_initiative_residue_and_membership_only_anchor_refuse() -> None:
    close_work = _close_work()
    authority = _authority(
        close_work,
        "compact-settled-coordination", "runtime-coordination:workspace"
    )
    residue = close_work.plan_initiative_closeout(
        shaping_residue=("intent:open",),
        build_residue=(),
        live_dependencies=(),
        contextual_anchor=None,
        coordination_fingerprint="sha256:current",
        current_coordination_fingerprint="sha256:current",
        current_coordination_evidence_ref="evidence:current-coordination",
        **authority,
    )
    assert residue.code == "initiative-not-settled"
    assert residue.mutated == ()
    membership = close_work.plan_initiative_closeout(
        shaping_residue=(),
        build_residue=(),
        live_dependencies=(),
        contextual_anchor="initiative-only",
        coordination_fingerprint="sha256:current",
        current_coordination_fingerprint="sha256:current",
        current_coordination_evidence_ref="evidence:current-coordination",
        **authority,
    )
    assert membership.code == "initiative-membership-not-retention-authority"


def test_initiative_compaction_refuses_authority_and_fingerprint_drift() -> None:
    close_work = _close_work()
    resource = "runtime-coordination:workspace"
    authority = _authority(
        close_work, "compact-settled-coordination", resource
    )
    authority["grant_source"] = "self-asserted"
    refused = close_work.plan_initiative_closeout(
        shaping_residue=(),
        build_residue=(),
        live_dependencies=(),
        contextual_anchor=None,
        coordination_fingerprint="sha256:confirmed",
        current_coordination_fingerprint="sha256:current",
        current_coordination_evidence_ref="evidence:current-coordination",
        **authority,
    )
    assert refused.code == "authorization-required"
    assert refused.mutated == ()
    drifted = close_work.plan_initiative_closeout(
        shaping_residue=(),
        build_residue=(),
        live_dependencies=(),
        contextual_anchor=None,
        coordination_fingerprint="sha256:confirmed",
        current_coordination_fingerprint="sha256:changed",
        current_coordination_evidence_ref="evidence:current-coordination",
        **_authority(close_work, "compact-settled-coordination", resource),
    )
    assert drifted.code == "confirmation-expired"
    assert drifted.mutated == ()


def test_downstream_rfc_waves_keep_wave4_artifacts_closeout_pending() -> None:
    close_work = _close_work()
    result = close_work.classify_artifact_closeout(
        delivery_status="Shipped",
        live_dependencies=("rfc-0096-wave-5", "rfc-0096-wave-6", "rfc-0096-wave-7"),
        contextual_anchor="rfc-0096-implementation-family",
        durable_outputs_settled=True,
    )
    assert result.code == "live-dependency"
    assert result.lifecycle_phase == "Closeout-pending"
    assert result.disposition is None
    assert result.mutated == ()


def test_workspace_status_projection_has_no_policy_or_effect_surface() -> None:
    status = _workspace_status()
    projection = status.project_closeout_status(
        paused=False,
        all_specs_shipped=True,
        closeout_blockers=[],
        cooling_context_visible=True,
    )
    data = dataclasses.asdict(projection)
    assert data == {
        "paused": False,
        "all_specs_shipped": True,
        "closeout_blockers": (),
        "initiative_eligible": True,
        "next_action": "invoke-close-work",
        "cooling_context_visible": True,
    }
    assert set(data).isdisjoint(
        {"disposition", "confirmation", "distillation", "compaction", "deletion"}
    )


def test_workspace_status_projects_paused_blocked_and_incomplete_states() -> None:
    status = _workspace_status()
    cases = (
        (True, True, (), (), "resume-or-keep-paused"),
        (
            False,
            True,
            ("initiative-residue",),
            ("initiative-residue",),
            "settle-closeout-blockers",
        ),
        (False, False, (), ("unshipped-specs",), "settle-closeout-blockers"),
    )
    for paused, all_shipped, blockers, expected_blockers, next_action in cases:
        projection = status.project_closeout_status(
            paused=paused,
            all_specs_shipped=all_shipped,
            closeout_blockers=blockers,
            cooling_context_visible=True,
        )
        data = dataclasses.asdict(projection)
        assert projection.initiative_eligible is False
        assert projection.all_specs_shipped is all_shipped
        assert projection.next_action == next_action
        assert projection.closeout_blockers == expected_blockers
        assert projection.cooling_context_visible is True
        assert set(data).isdisjoint({"disposition", "compaction", "deletion"})


def test_workspace_status_refuses_wave6_context_exclusion() -> None:
    status = _workspace_status()
    try:
        status.project_closeout_status(
            paused=False,
            all_specs_shipped=True,
            closeout_blockers=(),
            cooling_context_visible=False,
        )
    except ValueError as exc:
        assert "cannot exclude cooling context" in str(exc)
    else:
        raise AssertionError("Wave 6 context exclusion became representable")
