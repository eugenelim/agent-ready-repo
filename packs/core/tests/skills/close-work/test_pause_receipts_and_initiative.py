"""Wave 4 pause, receipt, initiative, and read-only projection contracts."""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILLS = PACK_ROOT / ".apm" / "skills"
CLOSE_WORK_SCRIPT = SKILLS / "close-work" / "scripts" / "close_work.py"
WORKSPACE_STATUS_SCRIPT = (
    SKILLS / "workspace-status" / "scripts" / "workspace_status_engine.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _close_work():
    return _load(CLOSE_WORK_SCRIPT, "close_work_t4_tests")


def _workspace_status():
    return _load(WORKSPACE_STATUS_SCRIPT, "workspace_status_t4_tests")


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


# ── Uncovered refusal codes (AC6, AC17, AC19) ────────────────────────────────
#
# Each code below was reachable but asserted nowhere, so the guard producing it
# could be deleted or inverted with the whole suite green. Every case asserts
# the exact code and that nothing was mutated.


def _pause_kwargs(close_work, surface: str, **overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "work_mode": "spec-backed",
        "artifact_status": "Implementing",
        "coordination_surface": surface,
        "writable": True,
        "contract_locator": "delivery-contract:current",
        "contract_fingerprint": "sha256:contract",
        "plan_locator": "delivery-plan:current",
        "plan_fingerprint": "sha256:plan",
        "restore_action": "resume-from-pinned-contract",
    }
    values.update(_authority(close_work, "write-pause-overlay", surface))
    values.update(overrides)
    return values


def test_pause_state_ineligible_when_the_artifact_is_not_ready_or_implementing() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"

    result = close_work.plan_pause(
        **_pause_kwargs(close_work, surface, artifact_status="Shipped")
    )

    assert result.code == "pause-state-ineligible"
    assert result.overlay is None
    assert result.mutated == ()


def test_pause_envelope_invalid_when_the_restore_action_is_unstructured() -> None:
    close_work = _close_work()
    surface = "runtime-coordination:workspace"

    result = close_work.plan_pause(
        **_pause_kwargs(close_work, surface, restore_action="do whatever")
    )

    assert result.code == "pause-envelope-invalid"
    assert result.overlay is None
    assert result.record is None
    assert result.mutated == ()


def test_resume_refuses_an_envelope_that_is_not_a_pause_overlay() -> None:
    close_work = _close_work()

    result = close_work.validate_pause_resume(
        {"contract_locator": "delivery-contract:current"},
        contract_locator="delivery-contract:current",
        contract_fingerprint="sha256:contract",
        plan_locator="delivery-plan:current",
        plan_fingerprint="sha256:plan",
        artifact_status="Implementing",
        evidence_refs=("evidence:current",),
        coordination_locator="runtime-coordination:workspace",
        restore_action="resume-from-pinned-contract",
    )

    assert result.code == "pause-envelope-invalid"
    assert result.overlay is None
    assert result.mutated == ()


def test_receipt_removal_refuses_a_malformed_current_fingerprint() -> None:
    close_work = _close_work()
    resource = "runtime-coordination:workspace"

    result = close_work.plan_receipt_removal(
        receipt_fingerprint="sha256:receipt",
        current_receipt_fingerprint="not-a-fingerprint",
        current_receipt_evidence_ref="evidence:current",
        **_authority(close_work, "remove-last-completion-receipt", resource),
    )

    assert result.code == "receipt-fingerprint-invalid"


def test_receipt_removal_stops_at_a_separate_confirmation_request() -> None:
    close_work = _close_work()
    resource = "runtime-coordination:workspace"

    result = close_work.plan_receipt_removal(
        receipt_fingerprint="sha256:receipt",
        current_receipt_fingerprint="sha256:receipt",
        current_receipt_evidence_ref="evidence:current",
        **_authority(close_work, "remove-last-completion-receipt", resource),
    )

    # Intent only: the workflow asks, it does not remove.
    assert result.code == "receipt-removal-confirmation-required"
    assert result.confirmation_fingerprint == "sha256:receipt"


def _initiative_kwargs(close_work, resource: str, **overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "shaping_residue": (),
        "build_residue": (),
        "live_dependencies": (),
        "contextual_anchor": None,
        "coordination_fingerprint": "sha256:coordination",
        "current_coordination_fingerprint": "sha256:coordination",
        "current_coordination_evidence_ref": "evidence:current",
    }
    values.update(_authority(close_work, "compact-settled-coordination", resource))
    values.update(overrides)
    return values


def test_initiative_closeout_refuses_without_a_current_coordination_fingerprint() -> None:
    close_work = _close_work()
    resource = "runtime-coordination:workspace"

    result = close_work.plan_initiative_closeout(
        **_initiative_kwargs(
            close_work, resource, current_coordination_fingerprint=None
        )
    )

    assert result.code == "coordination-fingerprint-unavailable"


def test_initiative_closeout_stops_at_a_separate_compaction_confirmation() -> None:
    close_work = _close_work()
    resource = "runtime-coordination:workspace"

    result = close_work.plan_initiative_closeout(
        **_initiative_kwargs(close_work, resource)
    )

    assert result.code == "initiative-compaction-confirmation-required"
    assert result.workspace_action == "compact-settled-coordination"
    assert result.coordination_fingerprint == "sha256:coordination"


def test_artifact_closeout_blocks_on_unsettled_durable_outputs() -> None:
    close_work = _close_work()

    result = close_work.classify_artifact_closeout(
        delivery_status="Shipped",
        live_dependencies=(),
        contextual_anchor=None,
        durable_outputs_settled=False,
    )

    assert result.code == "durable-output-blocker"
    assert result.lifecycle_phase == "Closeout-pending"


def test_artifact_closeout_requires_review_of_a_contextual_anchor() -> None:
    close_work = _close_work()

    result = close_work.classify_artifact_closeout(
        delivery_status="Shipped",
        live_dependencies=(),
        contextual_anchor="rfc-family:0096",
        durable_outputs_settled=True,
    )

    assert result.code == "anchor-review-required"
    assert result.lifecycle_phase == "Closeout-pending"


def test_deterministic_seams_return_equal_results_on_a_second_run() -> None:
    """AC19: two runs over the committed matrices are byte-identical.

    The earlier version of this test called three pure constructors with literal
    arguments, which could only have failed through global mutable state. This
    drives every committed classification fixture twice and compares the
    serialized result lists, so an ordering or dict-iteration change in the
    seams actually reddens it. `preview_deletion` stays excluded on purpose: it
    embeds a fresh `secrets.token_hex` challenge and is required to differ
    between runs.
    """
    close_work = _close_work()
    fixture_root = (
        PACK_ROOT.parent.parent
        / "tests/roster/fixtures/close-work-extraction-and-immediate-disposition"
    )
    assert fixture_root.is_dir(), fixture_root

    def run() -> str:
        rendered: list[str] = []

        for raw in json.loads(
            (fixture_root / "disposition-matrix.json").read_text(encoding="utf-8")
        ):
            candidate = close_work.DispositionCandidate(
                lifecycle_outcome=raw.get(
                    "lifecycle_outcome",
                    "completed" if raw["delivered"] else "abandoned",
                ),
                persisted=raw["persisted"],
                delivered=raw["delivered"],
                pushed=raw["pushed"],
                removal_change=raw["removal_change"],
                removal_integrated=raw["removal_integrated"],
                lasting_facts_settled=raw["lasting_facts_settled"],
                obligations_settled=raw["obligations_settled"],
                live_dependencies=raw["live_dependencies"],
                retain_exception=raw["retain_exception"],
                source_authority=raw["source_authority"],
                write_authority=raw["write_authority"],
                deletion_authority=raw["deletion_authority"],
            )
            rendered.append(
                f"{raw['id']}|{dataclasses.asdict(close_work.classify_disposition(candidate))}"
            )

        for raw in json.loads(
            (fixture_root / "lifecycle-matrix.json").read_text(encoding="utf-8")
        ):
            inputs = {
                key: (tuple(value) if isinstance(value, list) else value)
                for key, value in raw.items()
                if key not in {"id", "expected", "expected_phase", "expected_blocker"}
            }
            rendered.append(
                f"{raw['id']}|{dataclasses.asdict(close_work.project_lifecycle(**inputs))}"
            )

        return "\n".join(rendered)

    first = run()
    second = run()
    assert first == second
    # A non-trivial corpus, so the equality is not vacuous.
    assert first.count("\n") >= 20, first.count("\n")


# ── Systematic result-code coverage (plan T1 Done-when, AC19) ────────────────
#
# Reviewers re-discovered unasserted result codes one at a time across two
# rounds. Rather than cover only the ones they named, these cases close the
# whole class: `test_every_result_code_has_an_asserted_trace` in the close-work
# roster file now fails when any newly added code lands without an assertion.
# Every case below drives the real public seam and asserts the exact code.


def test_classification_seams_reject_malformed_evidence() -> None:
    """Every `classify_*` / `assess_*` refusal names its exact cause."""
    close_work = _close_work()

    def candidate(**overrides):
        values = {
            "lifecycle_outcome": "completed",
            "persisted": True,
            "delivered": False,
            "pushed": False,
            "removal_change": False,
            "removal_integrated": False,
            "lasting_facts_settled": True,
            "obligations_settled": True,
            "source_authority": "repository-origin",
            "write_authority": "repository-maintainer",
            "deletion_authority": "repository-owned",
        }
        values.update(overrides)
        return close_work.DispositionCandidate(**values)

    assert close_work.classify_disposition(
        candidate(lifecycle_outcome="in-flight")
    ).blocker == "lifecycle-outcome-invalid"
    assert close_work.classify_disposition(
        candidate(pushed="yes")
    ).blocker == "disposition-facts-invalid"
    assert close_work.classify_disposition(
        candidate(write_authority="whoever")
    ).blocker == "write-authority-invalid"
    assert close_work.classify_disposition(
        candidate(deletion_authority="whatever")
    ).blocker == "deletion-authority-invalid"

    # `assess_durable_output` refusals.
    assert close_work.assess_durable_output(
        applicable=True, destination=None,
        freshness="confirmed", finding_status="none",
    ).code == "destination-unresolved"
    assert close_work.assess_durable_output(
        applicable=True, destination="docs/product/intent.md",
        freshness="stale", finding_status="none",
    ).code == "semantic-freshness-unconfirmed"
    assert close_work.assess_durable_output(
        applicable=True, destination="docs/product/intent.md",
        freshness="confirmed", finding_status="open",
    ).code == "implementation-finding-unsettled"

    # A non-inferable fact with no resolved owner blocks disposition.
    assert close_work.classify_lld_fact(
        kind="rationale", inferable_from_code=False, owner=None,
    ).code == "durable-owner-unresolved"

    # A `str` reads as a Sequence of characters, so the guard must type-check.
    assert close_work.classify_artifact_closeout(
        delivery_status="Shipped", live_dependencies="rfc-0096",
        contextual_anchor=None, durable_outputs_settled=True,
    ).code == "artifact-evidence-invalid"


def test_artifact_closeout_success_terminal_is_asserted() -> None:
    """The only success terminal of `classify_artifact_closeout`.

    Without this, inverting the anchor branch or renaming the success code ships
    with the whole suite green.
    """
    close_work = _close_work()

    result = close_work.classify_artifact_closeout(
        delivery_status="Shipped",
        live_dependencies=(),
        contextual_anchor=None,
        durable_outputs_settled=True,
    )

    assert result.code == "disposition-classification-ready"
    assert result.lifecycle_phase == "Closeout-pending"


def test_lifecycle_projection_refusals_are_asserted() -> None:
    """`project_lifecycle` names an invalid post-closeout result and a missing outcome."""
    close_work = _close_work()

    def project(**overrides):
        values = {
            "spec_status": "Shipped",
            "plan_status": "Done",
            "work_mode": "spec-backed",
            "outcome": "completed",
            "paused": False,
            "receipt_present": False,
            "workspace_room": "shipped",
            "post_closeout_result": None,
            "live_dependencies": (),
            "initiative_residue": False,
        }
        values.update(overrides)
        return close_work.project_lifecycle(**values)

    assert project(post_closeout_result="vibes").blocker == (
        "post-closeout-result-invalid"
    )
    # Same refusal on the direct-light branch.
    assert project(
        work_mode="direct-light", post_closeout_result="vibes"
    ).blocker == "post-closeout-result-invalid"
    assert project(outcome=None).blocker == "completion-outcome-required"


def test_workspace_capture_refusals_are_asserted() -> None:
    """AC2e: every `validate_workspace_capture` rejection names its exact cause."""
    close_work = _close_work()
    ok = {"summary": "Close Wave 4", "commentary": (), "needs": ()}

    def capture(**overrides):
        return close_work.validate_workspace_capture(**{**ok, **overrides})

    assert capture(summary="   ").code == "summary-required"
    assert capture(summary="x" * 5000).code == "summary-too-long"
    assert capture(commentary=("we discussed this",)).code == "commentary-forbidden"
    assert capture(
        summary="First we run tests, then merge"
    ).code == "procedure-or-history-forbidden"
    # A `str` is a Sequence of characters, so it must be type-rejected.
    assert capture(needs="docs/specs/other/spec.md").code == (
        "hard-dependencies-invalid"
    )
    # And a structurally invalid member is rejected by the second guard.
    assert capture(needs=("../escape",)).code == "hard-dependencies-invalid"
    assert capture().status == "accepted"


def test_receipt_and_initiative_evidence_refusals_are_asserted() -> None:
    """Receipt and initiative seams refuse malformed evidence with zero effect."""
    close_work = _close_work()
    resource = "runtime-coordination:workspace"

    # A non-bool dependency fact.
    bad_dependency = close_work.plan_completion_receipt(
        live_dependency="maybe",
        compatible_surface=resource,
        delivery_id="delivery:current",
        outcome="completed",
        completion_event="event:shipped",
        **_authority(close_work, "write-completion-receipt", resource),
    )
    assert bad_dependency.code == "dependency-evidence-invalid"
    assert bad_dependency.mutated == ()

    # A malformed bounded-text field after a valid binding.
    bad_receipt = close_work.plan_completion_receipt(
        live_dependency=True,
        compatible_surface=resource,
        delivery_id="",
        outcome="completed",
        completion_event="event:shipped",
        **_authority(close_work, "write-completion-receipt", resource),
    )
    assert bad_receipt.code == "receipt-evidence-required"
    assert bad_receipt.mutated == ()

    # A `str` residue reads as a Sequence of characters.
    bad_residue = close_work.plan_initiative_closeout(
        **_initiative_kwargs(close_work, resource, shaping_residue="leftover")
    )
    assert bad_residue.code == "initiative-evidence-invalid"

    # A malformed anchor reaches the second emitter.
    bad_anchor = close_work.plan_initiative_closeout(
        **_initiative_kwargs(close_work, resource, contextual_anchor="")
    )
    assert bad_anchor.code == "initiative-evidence-invalid"
