"""Jira Align refresh processor contract tests."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROCESSOR = ROOT / "packs/atlassian/.apm/skills/jira-align-refresh/scripts/processor.py"
REFRESH = ROOT / "packs/core/.apm/skills/work-intake/scripts/refresh.py"


def _unreached_acquire(_locator: str, _revision: str) -> dict[str, object]:
    raise AssertionError("acquisition should not run in this test")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def refresh():
    return _load(REFRESH, "jira_align_refresh_runtime")


@pytest.fixture()
def processor():
    return _load(PROCESSOR, "jira_align_refresh_processor")


class FakeJiraAlignClient:
    def __init__(self) -> None:
        self.calls: list[object] = []


def test_registers_read_refresh_profile_and_no_write_capabilities(processor, refresh) -> None:
    registry = refresh.RefreshProcessorRegistry()
    processor.register(registry, refresh, acquire=_unreached_acquire)
    registration = registry.resolve("jira-align-default", "1.0", "acquire")
    assert registration.name == "jira-align-refresh"
    assert registration.revision_field == "modifiedDate"
    assert registration.field_mapping == (
        ("Outcome", "title"),
        ("User stories", "description"),
    )
    with pytest.raises(refresh.RefreshRefusal, match="unsupported_capability"):
        registry.resolve("jira-align-default", "1.0", "comment")


def test_common_lifecycle_matrix_reuses_shared_authority(processor, refresh) -> None:
    registry = refresh.RefreshProcessorRegistry()
    processor.register(registry, refresh, acquire=_unreached_acquire)
    policy = refresh.RefreshAuthorizationPolicy(
        draft_approver_roles=("product-owner",),
        accepted_approver_roles=("product-owner",),
        remote_mutation_approver_roles=("product-owner",),
    )
    approver = refresh.ApproverEvidence(
        identity="approver@example.com",
        role="product-owner",
        confirmed_at="2026-08-17T12:00:00Z",
        authorization_source="current-human-session",
    )
    authority = refresh.SourceAuthority(
        source_ref="JA-100",
        source_revision="JA-100@6",
        accepted_revision="JA-100@5",
        owned_fields={"Outcome": "source"},
        acceptance=refresh.Approval(
            identity="approver@example.com",
            role="product-owner",
            decided_at="2026-08-17T11:00:00Z",
            authorization_source="workspace.authorization.refresh",
        ),
    )
    for lifecycle in ("Draft", "Accepted", "Ready", "Approved"):
        result = refresh.evaluate_refresh(
            comparison=refresh.RefreshComparison(
                artifact_path="docs/specs/example/spec.md",
                artifact_kind="spec",
                lifecycle=lifecycle,
                authority_mode="tracker-origin",
                current_revision="JA-100@6",
                compared_revision="JA-100@7",
                profile_id="jira-align-default",
                profile_version="1.0",
                changed_fields=(refresh.ChangedField("Outcome", "old", "new"),),
            ),
            authority=authority,
            policy=policy,
            approver=approver,
            decisions={"Outcome": "accept-source"},
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
        assert result.comparison_status == "completed"


def test_jira_align_undeclared_action_is_refused(processor) -> None:
    client = FakeJiraAlignClient()
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="requirement_body",
            target="100",
            confirmation=object(),
        )
    )
    assert result.code == "unsupported_capability"
    assert result.payload is None
    assert client.calls == []


def test_destination_guard_runs_before_request(processor, refresh) -> None:
    def public_resolver(host: str):
        assert host == "portfolio-tracker.example.test"
        return ("93.184.216.34",)

    pinned = processor.validate_destination(
        "https://portfolio-tracker.example.test",
        refresh_runtime=refresh,
        resolver=public_resolver,
    )
    assert pinned.host == "portfolio-tracker.example.test"
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        processor.validate_destination(
            "https://attacker.example.test",
            refresh_runtime=refresh,
            resolver=lambda _host: ("93.184.216.34",),
        )
    with pytest.raises(refresh.RefreshRefusal, match="destination_forbidden"):
        processor.validate_destination(
            "https://portfolio-tracker.example.test",
            refresh_runtime=refresh,
            resolver=lambda _host: ("169.254.169.254",),
        )


def test_destination_comes_only_from_resolved_profile(processor, refresh, tmp_path: Path) -> None:
    """An adopter profile may select its host; tracker data may not."""
    profile = json.loads(
        (PROCESSOR.parents[1] / "references" / "refresh-profile.json").read_text(
            encoding="utf-8"
        )
    )
    profile["destination"]["host"] = "configured.example.test"
    profile_path = tmp_path / "resolved-profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    assert processor.validate_destination(
        "https://configured.example.test",
        refresh_runtime=refresh,
        resolver=lambda _host: ("93.184.216.34",),
        profile_path=profile_path,
    ).host == "configured.example.test"
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        processor.validate_destination(
            "https://tracker-supplied.example.test",
            refresh_runtime=refresh,
            resolver=lambda _host: ("93.184.216.34",),
            profile_path=profile_path,
        )


def test_skill_metadata_preserves_credential_contract() -> None:
    body = (
        ROOT / "packs/atlassian/.apm/skills/jira-align-refresh/SKILL.md"
    ).read_text(encoding="utf-8")
    frontmatter = body.split("---", 2)[1]
    allowed_tools = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, re.MULTILINE)
    assert allowed_tools is not None
    assert allowed_tools.group(1) == "Read Bash"
    assert set(re.findall(r"^    - (.+)$", frontmatter, re.MULTILINE)) == {
        "network_fetch",
        "filesystem_read_untrusted",
        "filesystem_write",
    }
    assert "credentialed: true" in body
    assert "namespace: jiraalign" in body


def test_refresh_profile_matches_production_registration(processor, refresh) -> None:
    profile = json.loads(
        (
            ROOT
            / "packs/atlassian/.apm/skills/jira-align-refresh/references/refresh-profile.json"
        ).read_text(encoding="utf-8")
    )
    registry = refresh.RefreshProcessorRegistry()
    processor.register(registry, refresh, acquire=_unreached_acquire)
    registration = registry.resolve(profile["id"], profile["version"], "acquire")
    assert profile["revision_field"] == registration.revision_field
    assert tuple(profile["field_mapping"].items()) == registration.field_mapping
    assert frozenset(profile["capabilities"]) == registration.capabilities
    assert profile["destination"]["redirects"] is False
    assert profile["destination"]["dns_policy"] == "pinned-address"
