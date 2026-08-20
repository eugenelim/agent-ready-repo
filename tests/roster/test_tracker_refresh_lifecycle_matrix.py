"""Cross-profile lifecycle parity for configured tracker refresh."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parents[2]
REFRESH = ROOT / "packs/core/.apm/skills/work-intake/scripts/refresh.py"
ROUTER = ROOT / "packs/core/.apm/skills/work-intake/scripts/intake_router.py"
PROCESSORS = {
    "jira-default": ROOT
    / "packs/atlassian/.apm/skills/jira-refresh/scripts/processor.py",
    "jira-align-default": ROOT
    / "packs/atlassian/.apm/skills/jira-align-refresh/scripts/processor.py",
    "linear-default": ROOT / "packs/linear/.apm/skills/linear/scripts/linear.py",
    "github-default": ROOT
    / "packs/github/.apm/skills/github-refresh/scripts/processor.py",
}
LIFECYCLE_EXPECTATIONS = {
    "Draft": "pending",
    "Accepted": "pending",
    "Ready": "pending",
    "Approved": "pending",
    "Implementing": "refused",
    "Executing": "refused",
    "Shipped": "refused",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def refresh():
    return _load(REFRESH, "tracker_refresh_lifecycle_runtime")


@pytest.fixture(scope="module")
def router():
    return _load(ROUTER, "tracker_refresh_lifecycle_router")


def _unreached_acquire(_locator: str, _revision: str) -> dict[str, object]:
    raise AssertionError("acquisition should not run in lifecycle-only tests")


def _registered_profiles(
    refresh,
    acquire: Callable[[str, str], dict[str, object]] = _unreached_acquire,
) -> object:
    registry = refresh.RefreshProcessorRegistry()
    for index, (profile_id, path) in enumerate(PROCESSORS.items()):
        processor = _load(path, f"tracker_refresh_processor_{index}")
        if profile_id in {"jira-default", "jira-align-default"}:
            processor.register(registry, refresh, acquire=acquire)
        elif profile_id == "linear-default":
            registry.register(
                processor.linear_refresh_registration(refresh, acquire=acquire)
            )
        else:
            registry.register(
                processor.github_refresh_registration(refresh, acquire=acquire)
            )
    return registry


def _recording_acquirer(
    raw: dict[str, object], calls: list[tuple[str, str]]
) -> Callable[[str, str], dict[str, object]]:
    def acquire(locator: str, revision: str) -> dict[str, object]:
        calls.append((locator, revision))
        return raw

    return acquire


@pytest.mark.parametrize(
    ("lifecycle", "expected_local_mutation"),
    LIFECYCLE_EXPECTATIONS.items(),
)
def test_all_tracker_profiles_share_the_same_lifecycle_matrix(
    refresh,
    router,
    lifecycle: str,
    expected_local_mutation: str,
) -> None:
    calls: list[tuple[str, str]] = []
    raw: dict[str, object] = {
        "locator": "tracker:item-1",
        "type": "work-item",
        "updatedAt": "remote-rev-2",
        "updated": "remote-rev-2",
        "modifiedDate": "remote-rev-2",
        "title": "source Outcome",
        "summary": "source Outcome",
        "description": "local User stories",
        "body": "local User stories",
    }
    registry = _registered_profiles(refresh, _recording_acquirer(raw, calls))
    policy = refresh.RefreshAuthorizationPolicy(
        draft_approver_roles=("product",),
        accepted_approver_roles=("product",),
        remote_mutation_approver_roles=("product",),
    )
    approver = refresh.ApproverEvidence(
        identity="approver@example.com",
        role="product",
        confirmed_at="2026-08-17T12:00:00Z",
        authorization_source="current-human-session",
    )
    for profile_id in PROCESSORS:
        authority = refresh.SourceAuthority(
            source_ref="tracker:item-1",
            source_revision="remote-rev-1",
            accepted_revision="remote-rev-1",
            owned_fields={
                "Outcome": "source" if lifecycle == "Draft" else "local"
            },
            acceptance=refresh.Approval(
                identity="approver@example.com",
                role="product",
                decided_at="2026-08-17T11:00:00Z",
                authorization_source="current-human-session",
            ),
        )
        registration = registry.resolve(profile_id, "1.0", "acquire")
        local_fields = {
            canonical_field: f"local {canonical_field}"
            for canonical_field, _source_field in registration.field_mapping
        }
        signals = router.RoutingSignals(
            action="refresh",
            artifact="docs/product/briefs/example.md",
            artifact_kind="brief",
            authority_mode="tracker-origin",
            profile_id=profile_id,
            profile_version="1.0",
        )
        invocation = router.invoke_refresh(
            signals,
            registry,
            refresh.RefreshAcquisitionRequest(
                artifact_path=signals.artifact,
                artifact_kind=signals.artifact_kind,
                lifecycle=lifecycle,
                authority_mode=signals.authority_mode,
                source_ref="tracker:item-1",
                current_revision="remote-rev-1",
                compared_revision="remote-rev-2",
                profile_id=profile_id,
                profile_version="1.0",
                local_fields=local_fields,
            ),
        )
        assert invocation.code == "completed", profile_id
        assert calls == [("tracker:item-1", "remote-rev-2")], profile_id
        calls.clear()
        result = refresh.evaluate_refresh(
            comparison=invocation.invocation.comparison,
            authority=authority,
            policy=policy,
            approver=approver,
            decisions={"Outcome": "accept-source"},
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.local_mutation == expected_local_mutation, profile_id


def test_work_intake_invokes_every_supported_profile_acquire_map_compare(
    refresh,
    router,
) -> None:
    calls: list[tuple[str, str]] = []
    raw: dict[str, object] = {
        "locator": "tracker:item-1",
        "type": "work-item",
        "updatedAt": "remote-rev-2",
        "updated": "remote-rev-2",
        "modifiedDate": "remote-rev-2",
        "title": "source Outcome",
        "summary": "source Outcome",
        "description": "source User stories",
        "body": "source User stories",
    }
    registry = _registered_profiles(refresh, _recording_acquirer(raw, calls))
    for profile_id in PROCESSORS:
        registration = registry.resolve(profile_id, "1.0", "acquire")
        local_fields: dict[str, str] = {}
        for canonical_field, _source_field in registration.field_mapping:
            local_fields[canonical_field] = f"local {canonical_field}"

        signals = router.RoutingSignals(
            action="refresh",
            artifact="docs/product/briefs/example.md",
            artifact_kind="brief",
            authority_mode="tracker-origin",
            profile_id=profile_id,
            profile_version="1.0",
        )
        request = refresh.RefreshAcquisitionRequest(
            artifact_path=signals.artifact,
            artifact_kind=signals.artifact_kind,
            lifecycle="Ready",
            authority_mode=signals.authority_mode,
            source_ref="tracker:item-1",
            current_revision="remote-rev-1",
            compared_revision="remote-rev-2",
            profile_id=profile_id,
            profile_version="1.0",
            local_fields=local_fields,
        )

        result = router.invoke_refresh(signals, registry, request)

        assert result.code == "completed", profile_id
        assert result.invocation.comparison.changed_fields, profile_id
        assert calls == [("tracker:item-1", "remote-rev-2")], profile_id
        calls.clear()
