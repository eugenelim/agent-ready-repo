"""Construction tests for reviewed tracker refresh and guarded write-back."""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

_ROOT = Path(__file__).resolve().parents[5]
_REFRESH_PATH = (
    _ROOT / "packs/core/.apm/skills/work-intake/scripts/refresh.py"
)
_ROUTER_PATH = (
    _ROOT / "packs/core/.apm/skills/work-intake/scripts/intake_router.py"
)
_CONTRACT_ROOT = _ROOT / "contracts/jsonschema"


def _load_refresh():
    spec = importlib.util.spec_from_file_location("work_intake_refresh", _REFRESH_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["work_intake_refresh"] = module
    spec.loader.exec_module(module)
    return module


def _load_router():
    spec = importlib.util.spec_from_file_location("work_intake_refresh_router", _ROUTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["work_intake_refresh_router"] = module
    spec.loader.exec_module(module)
    return module


def test_refresh_result_code_enum_matches_coordinator_vocabulary() -> None:
    """Schema and construction enforce the one coordinator result vocabulary."""
    refresh = _load_refresh()
    schema = json.loads((_CONTRACT_ROOT / "refresh-result.schema.json").read_text())
    assert set(schema["properties"]["code"]["enum"]) == refresh.RESULT_CODES
    for code in refresh.RESULT_CODES:
        assert refresh.RefreshResult(code, "completed").code == code
    with pytest.raises(ValueError, match="unknown refresh result code"):
        refresh.RefreshResult("invented-code", "completed")


def test_every_coordinator_result_code_has_a_schema_valid_refusal_shape() -> None:
    """Every public coordinator result, including refusals, remains schema-valid."""

    refresh = _load_refresh()
    schema = json.loads(
        (_CONTRACT_ROOT / "refresh-result.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    for code in refresh.RESULT_CODES:
        validator.validate(refresh.RefreshResult(code, "not-started").as_record())


def test_remote_receipt_store_rejects_spoofed_subclass() -> None:
    refresh = _load_refresh()

    class Evil(refresh.RemoteReceiptStore):
        pass

    Evil.__name__ = "RemoteReceiptStore"
    Evil.__qualname__ = "RemoteReceiptStore"
    Evil.__module__ = refresh.__name__
    assert not refresh.is_remote_receipt_store(Evil.__new__(Evil))


def _authority_block(*, extra: str = "", duplicate: bool = False) -> str:
    block = f'''```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "example-service://work/ITEM-1"
source_revision = "rev-1"
accepted_revision = "rev-1"
{extra}

[owned_fields]
Outcome = "local"
Constraint = "source"

[acceptance]
identity = "Example Approver"
role = "maintainer"
decided_at = "2026-08-17T00:00:00Z"
authorization_source = "workspace.authorization.refresh"
```
'''
    return f"# Artifact\n\n{block}{block if duplicate else ''}"


def _policy() -> str:
    return '''
[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["maintainer"]
accepted_approver_roles = ["maintainer"]
remote_mutation_approver_roles = ["maintainer"]
'''


def _approver(refresh):
    return refresh.ApproverEvidence(
        identity="Example Approver",
        role="maintainer",
        confirmed_at="2026-08-17T00:00:00Z",
        authorization_source="current-human-session",
    )


def _unreached_acquire(_locator: str, _revision: str) -> dict[str, object]:
    raise AssertionError("acquisition should not run in this test")


def test_refresh_contract_schemas_are_closed() -> None:
    for name in (
        "source-authority.schema.json",
        "refresh-authorization-policy.schema.json",
        "refresh-result.schema.json",
    ):
        schema = json.loads((_CONTRACT_ROOT / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False


def test_authority_block_is_unique_closed_and_structured() -> None:
    refresh = _load_refresh()
    authority = refresh.parse_source_authority(_authority_block())

    assert authority.source_revision == "rev-1"
    assert authority.owned_fields == {"Outcome": "local", "Constraint": "source"}
    with pytest.raises(refresh.RefreshRefusal, match="duplicate_source_authority"):
        refresh.parse_source_authority(_authority_block(duplicate=True))
    with pytest.raises(refresh.RefreshRefusal, match="invalid_source_authority"):
        refresh.parse_source_authority(_authority_block(extra='unknown = "value"'))


def test_draft_authority_can_omit_acceptance_and_accepted_revision() -> None:
    refresh = _load_refresh()
    markdown = _authority_block().replace('accepted_revision = "rev-1"\n', "").replace(
        '\n[acceptance]\nidentity = "Example Approver"\nrole = "maintainer"\n'
        'decided_at = "2026-08-17T00:00:00Z"\n'
        'authorization_source = "workspace.authorization.refresh"\n',
        "\n",
    )
    authority = refresh.parse_source_authority(markdown)

    assert authority.acceptance is None
    assert authority.accepted_revision is None


def test_authority_nested_records_validate_closed_schema_types() -> None:
    refresh = _load_refresh()
    malformed = _authority_block(
        extra='''
[[remote_actions]]
confirmation_id = "confirm-1"
binding_digest = "not-a-digest"
profile_version = "1.0"
payload_digest = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "pending"
'''
    )
    with pytest.raises(refresh.RefreshRefusal, match="invalid_source_authority"):
        refresh.parse_source_authority(malformed)


def test_durable_remote_receipt_requires_profile_version() -> None:
    refresh = _load_refresh()
    missing_profile_version = _authority_block(
        extra=f'''
[[remote_actions]]
confirmation_id = "confirm-1"
binding_digest = "{'a' * 64}"
payload_digest = "{'b' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "pending"
'''
    )

    with pytest.raises(refresh.RefreshRefusal, match="invalid_source_authority"):
        refresh.parse_source_authority(missing_profile_version)


@pytest.mark.parametrize(
    "records",
    [
        '''
[[source_decisions]]
source_revision = "rev-2"
field = "Outcome"
decision = "keep-local"
identity = "Example Approver"
role = "maintainer"
decided_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
[[source_decisions]]
source_revision = "rev-2"
field = "Outcome"
decision = "accept-source"
identity = "Example Approver"
role = "maintainer"
decided_at = "2026-08-17T00:00:01Z"
authorization_source = "current-human-session"
''',
        '''
[[conflicts]]
source_revision = "rev-2"
field = "Outcome"
status = "unresolved"
[[conflicts]]
source_revision = "rev-2"
field = "Outcome"
status = "resolved"
decision = "keep-local"
''',
        f'''
[[local_receipts]]
update_id = "update-1"
artifact_digest = "{'a' * 64}"
workspace_digest = "{'b' * 64}"
status = "pending"
recorded_at = "2026-08-17T00:00:00Z"
[[local_receipts]]
update_id = "update-1"
artifact_digest = "{'c' * 64}"
workspace_digest = "{'d' * 64}"
status = "committed"
recorded_at = "2026-08-17T00:00:01Z"
''',
        f'''
[[remote_actions]]
confirmation_id = "confirm-1"
binding_digest = "{'a' * 64}"
profile_version = "1.0"
payload_digest = "{'b' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "pending"
[[remote_actions]]
confirmation_id = "confirm-1"
binding_digest = "{'c' * 64}"
profile_version = "1.0"
payload_digest = "{'d' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:01Z"
authorization_source = "current-human-session"
action = "closure"
target = "ITEM-1"
status = "failed"
''',
        f'''
[[remote_actions]]
confirmation_id = "confirm-1"
binding_digest = "{'a' * 64}"
profile_version = "1.0"
payload_digest = "{'b' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "pending"
[[remote_actions]]
confirmation_id = "confirm-2"
binding_digest = "{'a' * 64}"
profile_version = "1.0"
payload_digest = "{'c' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:01Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "failed"
''',
    ],
)
def test_authority_rejects_duplicate_semantic_record_keys(records: str) -> None:
    refresh = _load_refresh()

    with pytest.raises(refresh.RefreshRefusal, match="invalid_source_authority"):
        refresh.parse_source_authority(_authority_block(extra=records))


def test_repository_policy_authorizes_roles_without_identities() -> None:
    refresh = _load_refresh()
    policy = refresh.parse_refresh_authorization_policy(_policy())

    assert policy.draft_approver_roles == ("maintainer",)
    assert "Example Approver" not in repr(policy)
    with pytest.raises(refresh.RefreshRefusal, match="invalid_refresh_policy"):
        refresh.parse_refresh_authorization_policy(
            _policy().replace(
                'remote_mutation_approver_roles = ["maintainer"]',
                'remote_mutation_approver_roles = ["maintainer"]\nidentity = "forbidden"',
            )
        )


def test_repository_policy_loads_from_complete_workspace() -> None:
    refresh = _load_refresh()
    workspace = '''
["ini-001"]
name = "Example"
status = "active"
milestone = "M1"

["ini-001".work]
queue = []
active = []
shipped = []

[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["maintainer"]
accepted_approver_roles = ["maintainer"]
remote_mutation_approver_roles = ["maintainer"]

[backlog]
open = []
'''

    policy = refresh.parse_refresh_authorization_policy(workspace)

    assert policy.remote_mutation_approver_roles == ("maintainer",)


def test_confirmation_ledger_is_seeded_from_durable_receipts() -> None:
    refresh = _load_refresh()
    authority = refresh.SourceAuthority(
        source_ref="example-service://work/ITEM-1",
        source_revision="rev-1",
        accepted_revision="rev-1",
        owned_fields={"Outcome": "local"},
        acceptance=None,
        remote_actions=(
            {"confirmation_id": "already-consumed", "status": "succeeded"},
            {"confirmation_id": "failed-confirmation", "status": "failed"},
        ),
    )

    assert refresh.confirmation_ledger(authority) == {
        "already-consumed",
        "failed-confirmation",
    }


@pytest.mark.parametrize(
    ("lifecycle", "expected_code"),
    [
        ("Draft", "ready"),
        ("Accepted", "ready"),
        ("Ready", "ready"),
        ("Approved", "ready"),
        ("Implementing", "implementing_requirements_locked"),
        ("Executing", "executing_requirements_locked"),
        ("Shipped", "shipped_requirements_locked"),
    ],
)
def test_lifecycle_matrix_is_shared(lifecycle: str, expected_code: str) -> None:
    refresh = _load_refresh()
    authority = refresh.parse_source_authority(_authority_block())
    policy = refresh.parse_refresh_authorization_policy(_policy())
    comparison = refresh.RefreshComparison(
        artifact_path="docs/specs/example/spec.md",
        artifact_kind="spec",
        lifecycle=lifecycle,
        authority_mode="tracker-origin",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        changed_fields=(
            refresh.ChangedField("Outcome", "local", "source"),
        ),
    )

    result = refresh.evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=policy,
        approver=_approver(refresh),
        decisions={"Outcome": "keep-local"},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == expected_code
    assert result.remote_action is None


def test_repo_origin_reports_drift_without_requirement_mutation() -> None:
    refresh = _load_refresh()
    comparison = refresh.RefreshComparison(
        artifact_path="docs/specs/example/spec.md",
        artifact_kind="spec",
        lifecycle="Approved",
        authority_mode="repo-origin",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
    )

    result = refresh.evaluate_refresh(
        comparison=comparison,
        authority=None,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={},
    )

    assert result.code == "projection_drift"
    assert result.local_mutation == "none"
    assert result.field_updates == {}


def test_unauthorized_or_missing_decisions_have_zero_effects() -> None:
    refresh = _load_refresh()
    authority = refresh.parse_source_authority(_authority_block())
    policy = refresh.parse_refresh_authorization_policy(_policy())
    comparison = refresh.RefreshComparison(
        artifact_path="docs/specs/example/spec.md",
        artifact_kind="spec",
        lifecycle="Approved",
        authority_mode="tracker-origin",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
    )

    unauthorized = refresh.ApproverEvidence(
        identity="Example Reviewer",
        role="viewer",
        confirmed_at="2026-08-17T00:00:00Z",
        authorization_source="current-human-session",
    )
    result = refresh.evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=policy,
        approver=unauthorized,
        decisions={"Outcome": "accept-source"},
    )
    assert result.code == "unauthorized_approver"
    assert result.field_updates == {}

    stale = refresh.evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=policy,
        approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        now=datetime(2026, 8, 17, 0, 6, tzinfo=UTC),
    )
    assert stale.code == "unauthorized_approver"
    assert stale.local_mutation == "refused"

    missing = refresh.evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=policy,
        approver=_approver(refresh),
        decisions={},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert missing.code == "decision_required"
    assert missing.field_updates == {}


def test_stale_authority_and_draft_local_field_change_fail_closed() -> None:
    refresh = _load_refresh()
    authority = refresh.parse_source_authority(_authority_block())
    base = {
        "artifact_path": "docs/specs/example/spec.md",
        "artifact_kind": "spec",
        "lifecycle": "Draft",
        "authority_mode": "tracker-origin",
        "current_revision": "rev-1",
        "compared_revision": "rev-2",
        "profile_id": "example-service",
        "profile_version": "1.0",
        "changed_fields": (refresh.ChangedField("Outcome", "local", "source"),),
    }
    stale = refresh.evaluate_refresh(
        comparison=refresh.RefreshComparison(**{**base, "current_revision": "rev-0"}),
        authority=authority,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "keep-local"},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert stale.code == "authority_revision_mismatch"
    assert stale.local_mutation == "refused"

    local_change = refresh.evaluate_refresh(
        comparison=refresh.RefreshComparison(**base),
        authority=authority,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert local_change.code == "local_field_locked"
    assert local_change.field_updates == {}


@pytest.mark.parametrize(
    ("decision", "expected_updates", "expected_accepted", "expected_conflict"),
    [
        ("keep-local", {}, "rev-1", "none"),
        ("accept-source", {"Outcome": "source"}, "rev-2", "none"),
        ("revise-both", {}, "rev-1", "unresolved"),
    ],
)
def test_every_accepted_decision_is_recorded(
    decision: str,
    expected_updates: dict[str, str],
    expected_accepted: str,
    expected_conflict: str,
) -> None:
    refresh = _load_refresh()
    result = refresh.evaluate_refresh(
        comparison=refresh.RefreshComparison(
            artifact_path="docs/specs/example/spec.md",
            artifact_kind="spec",
            lifecycle="Approved",
            authority_mode="tracker-origin",
            current_revision="rev-1",
            compared_revision="rev-2",
            profile_id="example-service",
            profile_version="1.0",
            changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
        ),
        authority=refresh.parse_source_authority(_authority_block()),
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": decision},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.field_updates == expected_updates
    assert result.accepted_revision == expected_accepted
    assert result.conflict_state == expected_conflict
    assert result.decision_records[0]["decision"] == decision
    schema = json.loads((_CONTRACT_ROOT / "refresh-result.schema.json").read_text())
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(
        result.as_record()
    )


def test_accepted_refresh_requires_existing_local_ownership() -> None:
    refresh = _load_refresh()
    source_owned = refresh.parse_source_authority(
        _authority_block().replace('Outcome = "local"', 'Outcome = "source"')
    )

    result = refresh.evaluate_refresh(
        comparison=refresh.RefreshComparison(
            artifact_path="docs/specs/example/spec.md",
            artifact_kind="spec",
            lifecycle="Approved",
            authority_mode="tracker-origin",
            current_revision="rev-1",
            compared_revision="rev-2",
            profile_id="example-service",
            profile_version="1.0",
            changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
        ),
        authority=source_owned,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "accepted_field_not_local"
    assert result.local_mutation == "refused"


def test_comparison_failure_advances_no_revision() -> None:
    refresh = _load_refresh()
    result = refresh.failed_comparison()

    assert result.comparison_status == "failed"
    assert result.compared_revision is None
    assert result.accepted_revision is None
    assert result.field_updates == {}


def test_completed_keep_local_advances_only_compared_revision() -> None:
    refresh = _load_refresh()
    authority = refresh.parse_source_authority(_authority_block())
    result = refresh.evaluate_refresh(
        comparison=refresh.RefreshComparison(
            artifact_path="docs/specs/example/spec.md",
            artifact_kind="spec",
            lifecycle="Approved",
            authority_mode="tracker-origin",
            current_revision="rev-1",
            compared_revision="rev-2",
            profile_id="example-service",
            profile_version="1.0",
            changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
        ),
        authority=authority,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "keep-local"},
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "ready"
    assert result.compared_revision == "rev-2"
    assert result.accepted_revision == "rev-1"
    assert result.field_updates == {}


def test_processor_registry_fails_closed() -> None:
    refresh = _load_refresh()
    registry = refresh.RefreshProcessorRegistry()
    with pytest.raises(refresh.RefreshRefusal, match="invalid_processor_registration"):
        registry.register(
            refresh.ProcessorRegistration(
                name="detached-refresh",
                profile_id="detached-service",
                profile_version="1.0",
                capabilities=frozenset({"acquire"}),
                revision_field="updatedAt",
                field_mapping=(("Outcome", "title"),),
            )
        )
    registry.register(
        refresh.ProcessorRegistration(
            name="example-refresh",
            profile_id="example-service",
            profile_version="1.0",
            capabilities=frozenset({"acquire", "comment"}),
            acquire=_unreached_acquire,
            revision_field="updatedAt",
            field_mapping=(("Outcome", "title"), ("User stories", "description")),
        )
    )

    assert registry.resolve("example-service", "1.0").name == "example-refresh"
    with pytest.raises(refresh.RefreshRefusal, match="processor_unavailable"):
        registry.resolve("missing", "1.0")
    with pytest.raises(refresh.RefreshRefusal, match="profile_version_mismatch"):
        registry.resolve("example-service", "2.0")
    with pytest.raises(refresh.RefreshRefusal, match="unsupported_capability"):
        registry.resolve("example-service", "1.0", "closure")


def test_front_door_uses_only_the_configured_refresh_registry() -> None:
    refresh = _load_refresh()
    router = _load_router()
    registry = refresh.RefreshProcessorRegistry()
    registry.register(
        refresh.ProcessorRegistration(
            name="example-refresh",
            profile_id="example-service",
            profile_version="1.0",
            capabilities=frozenset({"acquire"}),
            acquire=_unreached_acquire,
            revision_field="updatedAt",
            field_mapping=(("Outcome", "title"), ("User stories", "description")),
        )
    )
    signals = router.RoutingSignals(
        action="refresh",
        artifact="docs/specs/example/spec.md",
        artifact_kind="spec",
        authority_mode="tracker-origin",
        profile_id="example-service",
        profile_version="1.0",
    )

    assert router.route_intake(signals, registry).processor == "example-refresh"
    unavailable = router.route_intake(
        router.RoutingSignals(
            action="refresh",
            artifact=signals.artifact,
            artifact_kind=signals.artifact_kind,
            authority_mode=signals.authority_mode,
            profile_id="source-says-use-another-processor",
            profile_version="1.0",
        ),
        registry,
    )
    assert unavailable.processor == "none"


def test_front_door_invokes_acquire_map_validate_and_compare() -> None:
    refresh = _load_refresh()
    router = _load_router()
    calls: list[tuple[str, str]] = []

    def acquire(locator: str, revision: str) -> dict[str, object]:
        calls.append((locator, revision))
        return {
            "locator": locator,
            "type": "issue",
            "updatedAt": revision,
            "title": "source outcome",
            "description": "existing story",
            "ignored": "untrusted raw field",
        }

    registry = refresh.RefreshProcessorRegistry()
    registry.register(
        refresh.ProcessorRegistration(
            name="example-refresh",
            profile_id="example-service",
            profile_version="1.0",
            capabilities=frozenset({"acquire"}),
            acquire=acquire,
            revision_field="updatedAt",
            field_mapping=(("Outcome", "title"), ("User stories", "description")),
        )
    )

    signals = router.RoutingSignals(
        action="refresh",
        artifact="docs/specs/example/spec.md",
        artifact_kind="spec",
        authority_mode="tracker-origin",
        profile_id="example-service",
        profile_version="1.0",
    )
    request = refresh.RefreshAcquisitionRequest(
        artifact_path=signals.artifact,
        artifact_kind=signals.artifact_kind,
        lifecycle="Approved",
        authority_mode=signals.authority_mode,
        source_ref="example-service://work/ITEM-1",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        local_fields={"Outcome": "local outcome", "User stories": "existing story"},
    )

    result = router.invoke_refresh(signals, registry, request)

    assert result.code == "completed"
    assert result.remediation == "none"
    assert calls == [("example-service://work/ITEM-1", "rev-2")]
    assert result.invocation is not None
    assert result.invocation.normalized_record["action"] == "refresh"
    assert result.invocation.normalized_record["refresh_target"] == signals.artifact
    assert result.invocation.comparison.changed_fields == (
        refresh.ChangedField("Outcome", "local outcome", "source outcome"),
    )
    assert "acquire" not in {field.name for field in fields(refresh.RefreshAcquisitionRequest)}


def test_front_door_refuses_mismatched_acquisition_without_raw_output() -> None:
    refresh = _load_refresh()
    router = _load_router()
    registry = refresh.RefreshProcessorRegistry()
    registry.register(
        refresh.ProcessorRegistration(
            name="example-refresh",
            profile_id="example-service",
            profile_version="1.0",
            capabilities=frozenset({"acquire"}),
            acquire=lambda _locator, _revision: {
                "locator": "example-service://work/OTHER",
                "type": "issue",
                "updatedAt": "rev-2",
                "title": "do not reveal this tracker payload",
            },
            revision_field="updatedAt",
            field_mapping=(("Outcome", "title"),),
        )
    )
    signals = router.RoutingSignals(
        action="refresh",
        artifact="docs/specs/example/spec.md",
        artifact_kind="spec",
        authority_mode="tracker-origin",
        profile_id="example-service",
        profile_version="1.0",
    )
    request = refresh.RefreshAcquisitionRequest(
        artifact_path=signals.artifact,
        artifact_kind=signals.artifact_kind,
        lifecycle="Approved",
        authority_mode=signals.authority_mode,
        source_ref="example-service://work/ITEM-1",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        local_fields={"Outcome": "local"},
    )

    result = router.invoke_refresh(signals, registry, request)

    assert result.code == "acquired_source_mismatch"
    assert result.remediation == "retry-or-repair-configured-refresh-processor"
    assert result.invocation is not None
    assert result.invocation.normalized_record is None


def test_confirmation_is_exact_fresh_and_single_use() -> None:
    refresh = _load_refresh()
    now = datetime(2026, 8, 17, tzinfo=UTC)
    binding = refresh.ConfirmationBinding(
        artifact_path="docs/specs/example/spec.md",
        source_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        destination="https://tracker.example/api",
        action="comment",
        target="ITEM-1",
        payload_digest="a" * 64,
    )
    confirmation = refresh.RemoteConfirmation.issue(
        confirmation_id="confirm-1",
        binding=binding,
        approver=_approver(refresh),
        confirmed_at=now,
    )
    used: set[str] = set()

    receipt = refresh.consume_remote_confirmation(
        confirmation=confirmation,
        expected_binding=binding,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        used_confirmation_ids=used,
        now=now,
    )
    assert receipt.status == "pending"
    assert receipt.confirmation_id == "confirm-1"
    assert receipt.profile_version == "1.0"
    assert receipt.payload_digest == "a" * 64
    assert receipt.authorization_source == "current-human-session"
    assert len(receipt.binding_digest) == 64
    assert used == set()
    durable_confirmation_ids = {receipt.confirmation_id}
    with pytest.raises(refresh.RefreshRefusal, match="confirmation_reused"):
        refresh.consume_remote_confirmation(
            confirmation=confirmation,
            expected_binding=binding,
            policy=refresh.parse_refresh_authorization_policy(_policy()),
            used_confirmation_ids=durable_confirmation_ids,
            now=now,
        )
    authority_schema = json.loads(
        (_CONTRACT_ROOT / "source-authority.schema.json").read_text()
    )
    Draft202012Validator(
        authority_schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    ).validate(
        {
            "contract_version": "source-authority.v1",
            "mode": "tracker-origin",
            "source_ref": "example-service://work/ITEM-1",
            "source_revision": "rev-2",
            "owned_fields": {"Outcome": "local"},
            "remote_actions": [dict(receipt.__dict__)],
        }
    )

    version_two_binding = replace(binding, profile_version="2.0")
    version_two = refresh.RemoteConfirmation.issue(
        confirmation_id="confirm-version-2",
        binding=version_two_binding,
        approver=_approver(refresh),
        confirmed_at=now,
    )
    version_two_receipt = refresh.consume_remote_confirmation(
        confirmation=version_two,
        expected_binding=version_two_binding,
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        used_confirmation_ids=used,
        now=now,
    )
    assert version_two_receipt.binding_digest != receipt.binding_digest
    assert version_two_receipt.profile_version == "2.0"

    mismatched_version = refresh.RemoteConfirmation.issue(
        confirmation_id="confirm-version-mismatch",
        binding=binding,
        approver=_approver(refresh),
        confirmed_at=now,
    )
    with pytest.raises(refresh.RefreshRefusal, match="confirmation_binding_mismatch"):
        refresh.consume_remote_confirmation(
            confirmation=mismatched_version,
            expected_binding=version_two_binding,
            policy=refresh.parse_refresh_authorization_policy(_policy()),
            used_confirmation_ids=durable_confirmation_ids,
            now=now,
        )
    assert "confirm-version-mismatch" not in used

    with pytest.raises(refresh.RefreshRefusal, match="confirmation_reused"):
        refresh.consume_remote_confirmation(
            confirmation=confirmation,
            expected_binding=binding,
            policy=refresh.parse_refresh_authorization_policy(_policy()),
            used_confirmation_ids=durable_confirmation_ids,
            now=now,
        )
    stale = refresh.RemoteConfirmation.issue(
        confirmation_id="confirm-2",
        binding=binding,
        approver=replace(
            _approver(refresh), confirmed_at="2026-08-16T23:54:00Z"
        ),
        confirmed_at=now - timedelta(minutes=6),
    )
    with pytest.raises(refresh.RefreshRefusal, match="confirmation_stale"):
        refresh.consume_remote_confirmation(
            confirmation=stale,
            expected_binding=binding,
            policy=refresh.parse_refresh_authorization_policy(_policy()),
            used_confirmation_ids=used,
            now=now,
        )


def test_remote_receipt_store_persists_pending_before_terminal_state(
    tmp_path: Path,
) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(_authority_block(), encoding="utf-8")
    workspace.write_text(_policy(), encoding="utf-8")
    original_artifact_digest = refresh.digest_bytes(artifact.read_bytes())
    workspace_digest = refresh.digest_bytes(workspace.read_bytes())
    store = refresh.RemoteReceiptStore.open(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=original_artifact_digest,
        expected_workspace_digest=workspace_digest,
    )
    receipt = refresh.RemoteActionReceipt(
        confirmation_id="confirm-durable",
        binding_digest="a" * 64,
        profile_version="1.0",
        payload_digest="b" * 64,
        identity="Example Approver",
        role="maintainer",
        confirmed_at="2026-08-17T00:00:00Z",
        authorization_source="current-human-session",
        action="comment",
        target="ITEM-1",
    )

    store.record(receipt)

    pending = refresh.parse_source_authority(artifact.read_text()).remote_actions
    assert pending == (dict(receipt.__dict__),)
    assert store.confirmation_ids() == {"confirm-durable"}
    assert store.artifact_digest != original_artifact_digest
    store.record(replace(receipt, status="succeeded"))
    terminal = refresh.parse_source_authority(artifact.read_text()).remote_actions
    assert terminal[0]["status"] == "succeeded"
    assert workspace.read_text() == _policy()
    with pytest.raises(refresh.RefreshRefusal, match="fingerprint_mismatch"):
        refresh.RemoteReceiptStore.open(
            repository_root=repo,
            artifact_path="docs/specs/example/spec.md",
            expected_artifact_digest=original_artifact_digest,
            expected_workspace_digest=workspace_digest,
        )


def test_remote_payload_digest_is_canonical_and_action_allowlisted() -> None:
    refresh = _load_refresh()
    assert refresh.canonical_payload_digest({"b": 2, "a": 1}) == refresh.canonical_payload_digest(
        {"a": 1, "b": 2}
    )
    now = datetime(2026, 8, 17, tzinfo=UTC)
    binding = refresh.ConfirmationBinding(
        artifact_path="docs/specs/example/spec.md",
        source_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        destination="https://tracker.example/api",
        action="rewrite-requirements",
        target="ITEM-1",
        payload_digest="a" * 64,
    )
    confirmation = refresh.RemoteConfirmation.issue(
        confirmation_id="confirm-forbidden",
        binding=binding,
        approver=_approver(refresh),
        confirmed_at=now,
    )
    with pytest.raises(refresh.RefreshRefusal, match="unsupported_remote_action"):
        refresh.consume_remote_confirmation(
            confirmation=confirmation,
            expected_binding=binding,
            policy=refresh.parse_refresh_authorization_policy(_policy()),
            used_confirmation_ids=set(),
            now=now,
        )


def test_destination_validation_rejects_forbidden_addresses() -> None:
    refresh = _load_refresh()
    policy = refresh.DestinationPolicy(
        schemes=frozenset({"https"}),
        hosts=frozenset({"tracker.example"}),
        ports=frozenset({443}),
        allow_redirects=False,
    )

    pinned = refresh.validate_destination(
        "https://tracker.example/api",
        policy=policy,
        resolver=lambda _host: ("203.0.113.10",),
    )
    assert pinned.addresses == ("203.0.113.10",)
    for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"):
        with pytest.raises(refresh.RefreshRefusal, match="destination_forbidden"):
            refresh.validate_destination(
                "https://tracker.example/api",
                policy=policy,
                resolver=lambda _host, address=address: (address,),
            )
    with pytest.raises(refresh.RefreshRefusal, match="redirect_refused"):
        refresh.validate_redirect(
            "https://tracker.example/other",
            policy=policy,
            resolver=lambda _host: ("203.0.113.10",),
        )


def test_destination_validation_rejects_credentials_and_mapped_loopback() -> None:
    refresh = _load_refresh()
    credentialed = refresh.DestinationPolicy(
        schemes=frozenset({"http", "https"}),
        hosts=frozenset({"tracker.example"}),
        ports=frozenset({80, 443}),
        credentials_attached=True,
    )
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        refresh.validate_destination(
            "http://tracker.example/api",
            policy=credentialed,
            resolver=lambda _host: ("203.0.113.10",),
        )
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        refresh.validate_destination(
            "https://user:secret@tracker.example/api",
            policy=credentialed,
            resolver=lambda _host: ("203.0.113.10",),
        )
    with pytest.raises(refresh.RefreshRefusal, match="destination_forbidden"):
        refresh.validate_destination(
            "https://tracker.example/api",
            policy=credentialed,
            resolver=lambda _host: ("::ffff:127.0.0.1",),
        )


def _semantic_refresh_pair(
    refresh,
    tmp_path: Path,
    *,
    decision: str = "revise-both",
    proposed_owner: str = "local",
    mutate_dependency: bool = False,
    mutate_coordination_receipt: bool = False,
    authority_injection: str = "",
    workspace_policy: str = _policy(),
) -> dict[str, Any]:
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    coordination = '''
```toml coordination-receipts
[[coordination_receipts]]
receipt_id = "receipt-1"
accepted_revision = "upstream-rev-1"
source_ref = "example-service://work/UPSTREAM-1"
recorded_at = "2026-08-17T00:00:00Z"
```
'''
    requirement_sections = """
## Outcome

local

## Constraint

stable
"""
    before_artifact = (
        _authority_block() + requirement_sections + coordination
    ).encode()
    before_workspace = workspace_policy.encode() + b'''
["ini-001"]
name = "Example"
status = "active"
milestone = "M1"

["ini-001".work]
active = [{path = "docs/specs/example/spec.md", kind = "spec", source = {mode = "tracker-origin", ref = "example-service://work/ITEM-1", revision = "rev-1", tracker_profile = {id = "example-service", version = "1.0"}}, summary = "Example", needs = [{type = "cross-repo", kind = "brief", path = "docs/product/briefs/upstream.md", containing_brief = "docs/product/briefs/example.md", receipt_id = "receipt-1", accepted_revision = "upstream-rev-1"}]}]
'''
    artifact.write_bytes(before_artifact)
    workspace.write_bytes(before_workspace)
    artifact_digest = refresh.digest_bytes(before_artifact)
    workspace_digest = refresh.digest_bytes(before_workspace)
    proposed_artifact_text = (
        _authority_block(extra=authority_injection)
        + requirement_sections
        + coordination
    )
    if decision == "accept-source":
        proposed_artifact_text = proposed_artifact_text.replace(
            "## Outcome\n\nlocal\n", "## Outcome\n\nsource\n", 1
        )
    if proposed_owner != "local":
        proposed_artifact_text = proposed_artifact_text.replace(
            'Outcome = "local"', f'Outcome = "{proposed_owner}"', 1
        )
    if mutate_coordination_receipt:
        proposed_artifact_text = proposed_artifact_text.replace(
            'accepted_revision = "upstream-rev-1"',
            'accepted_revision = "upstream-rev-2"',
            1,
        )
    proposed_artifact = proposed_artifact_text.encode()
    proposed_workspace = before_workspace.replace(
        b'revision = "rev-1"', b'revision = "rev-2"'
    )
    if mutate_dependency:
        proposed_workspace = proposed_workspace.replace(
            b'accepted_revision = "upstream-rev-1"',
            b'accepted_revision = "upstream-rev-2"',
        )
    comparison = refresh.RefreshComparison(
        artifact_path="docs/specs/example/spec.md",
        artifact_kind="spec",
        lifecycle="Approved",
        authority_mode="tracker-origin",
        current_revision="rev-1",
        compared_revision="rev-2",
        profile_id="example-service",
        profile_version="1.0",
        changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
    )
    return {
        "repo": repo,
        "artifact": artifact,
        "workspace": workspace,
        "before_artifact": before_artifact,
        "before_workspace": before_workspace,
        "artifact_digest": artifact_digest,
        "workspace_digest": workspace_digest,
        "proposed_artifact": proposed_artifact,
        "proposed_workspace": proposed_workspace,
        "comparison": comparison,
        "authority": refresh.parse_source_authority(before_artifact.decode()),
    }


def test_coordinator_commits_authority_mirror_receipt_and_dependency_pin(
    tmp_path: Path,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.local_mutation == "committed"
    durable = refresh.parse_source_authority(fixture["artifact"].read_text())
    assert durable.source_revision == "rev-2"
    assert durable.source_decisions[0]["decision"] == "revise-both"
    assert durable.conflicts[0]["status"] == "unresolved"
    assert durable.local_receipts[0]["status"] == "committed"
    assert durable.owned_fields["Outcome"] == "local"
    workspace_text = fixture["workspace"].read_text()
    assert 'revision = "rev-2"' in workspace_text


def test_coordinator_accepts_authority_after_changed_section(tmp_path: Path) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path, decision="accept-source")
    authority = _authority_block()
    before = fixture["before_artifact"].decode().replace(authority, "") + authority
    proposed = fixture["proposed_artifact"].decode().replace(authority, "") + authority
    proposed = proposed.replace("source\n", "a longer source outcome\n", 1)
    fixture["comparison"] = refresh.RefreshComparison(
        artifact_path="docs/specs/example/spec.md", artifact_kind="spec",
        lifecycle="Approved", authority_mode="tracker-origin", current_revision="rev-1",
        compared_revision="rev-2", profile_id="example-service", profile_version="1.0",
        changed_fields=(
            refresh.ChangedField("Outcome", "local", "a longer source outcome"),
        ),
    )
    fixture["artifact"].write_text(before, encoding="utf-8")
    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"], comparison=fixture["comparison"],
        authority=refresh.parse_source_authority(before),
        policy=refresh.parse_refresh_authorization_policy(_policy()), approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        expected_artifact_digest=refresh.digest_bytes(before.encode()),
        expected_workspace_digest=fixture["workspace_digest"], artifact_bytes=proposed.encode(),
        workspace_bytes=fixture["proposed_workspace"], now=datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert result.local_mutation == "committed"


def test_coordinator_refuses_relocated_authority_after_changed_section(tmp_path: Path) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    authority = _authority_block()
    before = fixture["before_artifact"].decode().replace(authority, "") + authority
    relocated = authority + fixture["proposed_artifact"].decode().replace(authority, "")
    fixture["artifact"].write_text(before, encoding="utf-8")
    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"], comparison=fixture["comparison"],
        authority=refresh.parse_source_authority(before),
        policy=refresh.parse_refresh_authorization_policy(_policy()), approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=refresh.digest_bytes(before.encode()),
        expected_workspace_digest=fixture["workspace_digest"], artifact_bytes=relocated.encode(),
        workspace_bytes=fixture["proposed_workspace"], now=datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert result.code == "invalid_local_update"
    assert fixture["artifact"].read_bytes() == before.encode()
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize(
    "workspace_policy",
    [
        "",
        _policy().replace(
            'accepted_approver_roles = ["maintainer"]',
            'accepted_approver_roles = ["reviewer"]',
        ),
    ],
)
def test_coordinator_rejects_missing_or_substituted_workspace_policy(
    tmp_path: Path,
    workspace_policy: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(
        refresh,
        tmp_path,
        workspace_policy=workspace_policy,
    )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_refresh_policy"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize(
    "authority_injection",
    [
        '''
[[source_decisions]]
source_revision = "rev-extra"
field = "Constraint"
decision = "keep-local"
identity = "Example Approver"
role = "maintainer"
decided_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
''',
        '''
[[conflicts]]
source_revision = "rev-extra"
field = "Constraint"
status = "unresolved"
''',
        f'''
[[local_receipts]]
update_id = "update-extra"
artifact_digest = "{'a' * 64}"
workspace_digest = "{'b' * 64}"
status = "committed"
recorded_at = "2026-08-17T00:00:00Z"
''',
        f'''
[[remote_actions]]
confirmation_id = "confirm-extra"
binding_digest = "{'a' * 64}"
profile_version = "1.0"
payload_digest = "{'b' * 64}"
identity = "Example Approver"
role = "maintainer"
confirmed_at = "2026-08-17T00:00:00Z"
authorization_source = "current-human-session"
action = "comment"
target = "ITEM-1"
status = "succeeded"
''',
    ],
)
def test_coordinator_rejects_extra_authority_history(
    tmp_path: Path,
    authority_injection: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(
        refresh,
        tmp_path,
        authority_injection=authority_injection,
    )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize(
    ("mutate_dependency", "mutate_coordination_receipt"),
    [(True, False), (False, True)],
)
def test_coordinator_rejects_dependency_or_coordination_receipt_changes(
    tmp_path: Path,
    mutate_dependency: bool,
    mutate_coordination_receipt: bool,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(
        refresh,
        tmp_path,
        mutate_dependency=mutate_dependency,
        mutate_coordination_receipt=mutate_coordination_receipt,
    )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


def test_coordinator_rejects_ownership_map_changes_from_authorized_refresh(
    tmp_path: Path,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(
        refresh,
        tmp_path,
        decision="accept-source",
        proposed_owner="source",
    )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize("tamper", ["unapplied-source", "unrelated-field"])
def test_coordinator_rejects_unverified_requirement_body_changes(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(
        refresh,
        tmp_path,
        decision="accept-source",
    )
    if tamper == "unapplied-source":
        fixture["proposed_artifact"] = fixture["proposed_artifact"].replace(
            b"## Outcome\n\nsource\n", b"## Outcome\n\nlocal\n", 1
        )
    else:
        fixture["proposed_artifact"] = fixture["proposed_artifact"].replace(
            b"## Constraint\n\nstable\n", b"## Constraint\n\nchanged\n", 1
        )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "accept-source"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize("tamper", ["missing-summary", "unknown-field"])
def test_coordinator_rejects_workspace_entry_contract_violations(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    if tamper == "missing-summary":
        fixture["proposed_workspace"] = fixture["proposed_workspace"].replace(
            b'summary = "Example", ', b"", 1
        )
    else:
        fixture["proposed_workspace"] = fixture["proposed_workspace"].replace(
            b'summary = "Example", ',
            b'summary = "Example", unexpected = "tracker-data", ',
            1,
        )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize("tamper", ["provenance", "unknown-field"])
def test_coordinator_rejects_invalid_current_workspace_entry_instead_of_repairing(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    if tamper == "provenance":
        bad_current = fixture["before_workspace"].replace(
            b"example-service://work/ITEM-1",
            b"example-service://work/OTHER-1",
            1,
        )
    else:
        bad_current = fixture["before_workspace"].replace(
            b'summary = "Example", ',
            b'summary = "Example", unexpected = "tracker-data", ',
            1,
        )
    fixture["workspace"].write_bytes(bad_current)
    fixture["before_workspace"] = bad_current
    fixture["workspace_digest"] = refresh.digest_bytes(bad_current)

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == bad_current


@pytest.mark.parametrize("tamper", ["initiative", "authorization-policy"])
def test_coordinator_rejects_unrelated_workspace_changes(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    if tamper == "initiative":
        fixture["proposed_workspace"] = fixture["proposed_workspace"].replace(
            b'name = "Example"', b'name = "Changed by tracker"', 1
        )
    else:
        fixture["proposed_workspace"] += b'''

[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["tracker-role"]
accepted_approver_roles = ["tracker-role"]
remote_mutation_approver_roles = ["tracker-role"]
'''

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize("tamper", ["comment", "formatting"])
def test_coordinator_rejects_nonsemantic_workspace_byte_injection(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    if tamper == "comment":
        fixture["proposed_workspace"] += (
            b"\n# untrusted tracker text must not enter workspace comments\n"
        )
    else:
        fixture["proposed_workspace"] = fixture["proposed_workspace"].replace(
            b'name = "Example"', b'name  = "Example"', 1
        )

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


@pytest.mark.parametrize(
    "tamper", ["comment", "formatting", "key-order", "position"]
)
def test_coordinator_rejects_source_authority_byte_injection(
    tmp_path: Path,
    tamper: str,
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    proposed = fixture["proposed_artifact"]
    if tamper == "comment":
        proposed = proposed.replace(
            b'mode = "tracker-origin"\n',
            b'mode = "tracker-origin"\n# injected tracker comment\n',
            1,
        )
    elif tamper == "formatting":
        proposed = proposed.replace(b"source_ref = ", b"source_ref  = ", 1)
    elif tamper == "key-order":
        proposed = proposed.replace(
            b'contract_version = "source-authority.v1"\nmode = "tracker-origin"\n',
            b'mode = "tracker-origin"\ncontract_version = "source-authority.v1"\n',
            1,
        )
    else:
        authority_block = _authority_block().encode()
        assert proposed.startswith(authority_block)
        proposed = proposed[len(authority_block) :] + authority_block

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=proposed,
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "invalid_local_update"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


def test_coordinator_workspace_replace_failure_rolls_back_semantic_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refresh = _load_refresh()
    fixture = _semantic_refresh_pair(refresh, tmp_path)
    original_replace = Path.replace

    def fail_workspace_replace(source: Path, target: Path) -> Path:
        if source.name.startswith(".workspace.toml."):
            raise OSError("injected")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_workspace_replace)

    result = refresh.coordinate_local_refresh(
        repository_root=fixture["repo"],
        comparison=fixture["comparison"],
        authority=fixture["authority"],
        policy=refresh.parse_refresh_authorization_policy(_policy()),
        approver=_approver(refresh),
        decisions={"Outcome": "revise-both"},
        expected_artifact_digest=fixture["artifact_digest"],
        expected_workspace_digest=fixture["workspace_digest"],
        artifact_bytes=fixture["proposed_artifact"],
        workspace_bytes=fixture["proposed_workspace"],
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    assert result.code == "local_write_failed"
    assert result.local_mutation == "refused"
    assert fixture["artifact"].read_bytes() == fixture["before_artifact"]
    assert fixture["workspace"].read_bytes() == fixture["before_workspace"]


def test_guarded_pair_write_rolls_back_workspace_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("before artifact\n", encoding="utf-8")
    workspace.write_text("before workspace\n", encoding="utf-8")
    before_artifact = artifact.read_bytes()
    before_workspace = workspace.read_bytes()

    original_replace = Path.replace

    def fail_workspace_replace(source: Path, target: Path) -> Path:
        if source.name.startswith(".workspace.toml."):
            raise OSError("injected")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_workspace_replace)
    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(before_artifact),
        expected_workspace_digest=refresh.digest_bytes(before_workspace),
        artifact_bytes=b"after artifact\n",
        workspace_bytes=b"after workspace\n",
    )
    assert result.code == "local_write_failed"
    assert artifact.read_bytes() == before_artifact
    assert workspace.read_bytes() == before_workspace


def test_guarded_pair_write_redacts_rollback_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("before artifact\n", encoding="utf-8")
    workspace.write_text("before workspace\n", encoding="utf-8")
    calls = 0
    original_replace = Path.replace

    def fail_commit_and_rollback(source: Path, target: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls >= 2:
            raise OSError("injected")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_commit_and_rollback)
    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(b"before artifact\n"),
        expected_workspace_digest=refresh.digest_bytes(b"before workspace\n"),
        artifact_bytes=b"after artifact\n",
        workspace_bytes=b"after workspace\n",
    )
    assert result.code == "local_write_failed"


def test_guarded_pair_write_respects_shared_workspace_lock(tmp_path: Path) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("before artifact\n", encoding="utf-8")
    workspace.write_text("before workspace\n", encoding="utf-8")
    lock = repo / ".workspace-repair.lock"
    lock.write_text("another writer", encoding="utf-8")

    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh.digest_bytes(workspace.read_bytes()),
        artifact_bytes=b"after artifact\n",
        workspace_bytes=b"after workspace\n",
    )

    assert result.code == "lock_busy"
    assert lock.read_text(encoding="utf-8") == "another writer"
    assert artifact.read_text(encoding="utf-8") == "before artifact\n"
    assert workspace.read_text(encoding="utf-8") == "before workspace\n"


def test_guarded_pair_rechecks_both_fingerprints_immediately_before_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("before artifact\n", encoding="utf-8")
    workspace.write_text("before workspace\n", encoding="utf-8")
    original_mkstemp = refresh.tempfile.mkstemp
    stage_count = 0

    def mutate_during_second_stage(*args, **kwargs):
        nonlocal stage_count
        stage_count += 1
        result = original_mkstemp(*args, **kwargs)
        if stage_count == 2:
            workspace.write_text("concurrent workspace\n", encoding="utf-8")
        return result

    monkeypatch.setattr(refresh.tempfile, "mkstemp", mutate_during_second_stage)
    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(b"before artifact\n"),
        expected_workspace_digest=refresh.digest_bytes(b"before workspace\n"),
        artifact_bytes=b"after artifact\n",
        workspace_bytes=b"after workspace\n",
    )

    assert result.code == "fingerprint_mismatch"
    assert artifact.read_text(encoding="utf-8") == "before artifact\n"
    assert workspace.read_text(encoding="utf-8") == "concurrent workspace\n"
    assert not (repo / ".workspace-repair.lock").exists()


def test_guarded_pair_write_preserves_existing_file_modes(tmp_path: Path) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("before artifact\n", encoding="utf-8")
    workspace.write_text("before workspace\n", encoding="utf-8")
    artifact.chmod(0o640)
    workspace.chmod(0o644)

    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh.digest_bytes(workspace.read_bytes()),
        artifact_bytes=b"after artifact\n",
        workspace_bytes=b"after workspace\n",
    )
    assert result.code == "written"
    assert artifact.stat().st_mode & 0o777 == 0o640
    assert workspace.stat().st_mode & 0o777 == 0o644


def test_guarded_pair_write_rejects_symlink_escape(tmp_path: Path) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    link = repo / "docs/specs/example/spec.md"
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    (repo / "workspace.toml").write_text("workspace\n", encoding="utf-8")

    result = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(b"outside\n"),
        expected_workspace_digest=refresh.digest_bytes(b"workspace\n"),
        artifact_bytes=b"changed\n",
        workspace_bytes=b"changed\n",
    )
    assert result.code == "invalid_target"
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_guarded_pair_write_rejects_stale_fingerprint_and_traversal(tmp_path: Path) -> None:
    refresh = _load_refresh()
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("artifact\n", encoding="utf-8")
    (repo / "workspace.toml").write_text("workspace\n", encoding="utf-8")

    stale = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest="0" * 64,
        expected_workspace_digest=refresh.digest_bytes(b"workspace\n"),
        artifact_bytes=b"changed\n",
        workspace_bytes=b"changed\n",
    )
    traversing = refresh.guarded_write_pair(
        repository_root=repo,
        artifact_path="docs/specs/example/../../../workspace.toml",
        expected_artifact_digest=refresh.digest_bytes(b"workspace\n"),
        expected_workspace_digest=refresh.digest_bytes(b"workspace\n"),
        artifact_bytes=b"changed\n",
        workspace_bytes=b"changed\n",
    )
    assert stale.code == "fingerprint_mismatch"
    assert traversing.code == "invalid_target"
    assert artifact.read_text(encoding="utf-8") == "artifact\n"
    assert (repo / "workspace.toml").read_text(encoding="utf-8") == "workspace\n"
