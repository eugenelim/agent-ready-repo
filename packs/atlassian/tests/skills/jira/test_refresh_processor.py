"""Jira refresh processor contract tests."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[5]
PROCESSOR = ROOT / "packs/atlassian/.apm/skills/jira-refresh/scripts/processor.py"
JIRA_ALIGN_PROCESSOR = (
    ROOT / "packs/atlassian/.apm/skills/jira-align-refresh/scripts/processor.py"
)
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
    return _load(REFRESH, "jira_refresh_runtime")


@pytest.fixture()
def processor():
    return _load(PROCESSOR, "jira_refresh_processor")


def test_processors_share_path_keyed_runtime_without_hijacking_receipt_store(
    processor, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Installed Jira processors resolve one runtime module for their shared path."""

    jira_align = _load(JIRA_ALIGN_PROCESSOR, "jira_align_refresh_processor")
    skills = tmp_path / "skills"
    runtime_path = skills / "work-intake/scripts/refresh.py"
    runtime_path.parent.mkdir(parents=True)
    runtime_path.write_text(REFRESH.read_text(encoding="utf-8"), encoding="utf-8")
    jira_script = skills / "jira-refresh/scripts/processor.py"
    jira_align_script = skills / "jira-align-refresh/scripts/processor.py"
    jira_script.parent.mkdir(parents=True)
    jira_align_script.parent.mkdir(parents=True)
    jira_script.touch()
    jira_align_script.touch()
    monkeypatch.setattr(processor, "__file__", str(jira_script))
    monkeypatch.setattr(jira_align, "__file__", str(jira_align_script))
    monkeypatch.setattr(processor, "_REFRESH_RUNTIME", None)
    monkeypatch.setattr(jira_align, "_REFRESH_RUNTIME", None)

    jira_runtime = processor._load_refresh_runtime()
    jira_align_runtime = jira_align._load_refresh_runtime()
    jira_store = object.__new__(jira_runtime.RemoteReceiptStore)
    jira_align_store = object.__new__(jira_align_runtime.RemoteReceiptStore)

    assert jira_runtime is jira_align_runtime
    assert jira_runtime.is_remote_receipt_store(jira_store)
    assert jira_align_runtime.is_remote_receipt_store(jira_align_store)


def _policy(refresh):
    return refresh.RefreshAuthorizationPolicy(
        draft_approver_roles=("product-owner",),
        accepted_approver_roles=("product-owner",),
        remote_mutation_approver_roles=("product-owner",),
    )


def _approver(refresh):
    return refresh.ApproverEvidence(
        identity="approver@example.com",
        role="product-owner",
        confirmed_at="2026-08-17T12:00:00Z",
        authorization_source="current-human-session",
    )


def _confirmation(refresh, *, action: str, target: str, payload: object):
    binding = refresh.ConfirmationBinding(
        artifact_path="docs/specs/example/spec.md",
        source_revision="JIRA-1@7",
        profile_id="jira-default",
        profile_version="1.0",
        destination="https://tracker.example.test",
        action=action,
        target=target,
        payload_digest=refresh.canonical_payload_digest(payload),
    )
    return refresh.RemoteConfirmation.issue(
        confirmation_id=f"confirm-{action}",
        binding=binding,
        approver=_approver(refresh),
        confirmed_at=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )


def _safe_destination_resolver(host: str):
    assert host == "tracker.example.test"
    return ("93.184.216.34",)


def test_destination_comes_only_from_resolved_profile(processor, refresh, tmp_path: Path) -> None:
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
        resolver=lambda host: ("93.184.216.34",),
        profile_path=profile_path,
    ).host == "configured.example.test"
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        processor.validate_destination(
            "https://tracker-supplied.example.test",
            refresh_runtime=refresh,
            resolver=lambda host: ("93.184.216.34",),
            profile_path=profile_path,
        )


def _receipt_store(refresh, tmp_path: Path):
    repo = tmp_path / "repo"
    artifact = repo / "docs/specs/example/spec.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        '''# Example

```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "jira://issue/PROJ-1"
source_revision = "JIRA-1@7"

[owned_fields]
Outcome = "local"
```
''',
        encoding="utf-8",
    )
    workspace.write_text(
        '''[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["product-owner"]
accepted_approver_roles = ["product-owner"]
remote_mutation_approver_roles = ["product-owner"]
''',
        encoding="utf-8",
    )
    return refresh.RemoteReceiptStore.open(
        repository_root=repo,
        artifact_path="docs/specs/example/spec.md",
        expected_artifact_digest=refresh.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh.digest_bytes(workspace.read_bytes()),
    )


class FakeJiraClient:
    def __init__(
        self,
        *,
        auth_mode: str = "creds",
        fail: bool = False,
        guarded: bool = True,
    ) -> None:
        self._auth_mode = auth_mode
        if guarded:
            self._intake_policy = SimpleNamespace(
                origin="https://tracker.example.test",
            )
        self.fail = fail
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    async def add_comment(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("add_comment", args, kwargs))
        if self.fail:
            raise RuntimeError("transport failed")

    async def transition_issue(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("transition_issue", args, kwargs))
        if self.fail:
            raise RuntimeError("transport failed")


def test_registers_exact_jira_profile_capabilities(processor, refresh) -> None:
    registry = refresh.RefreshProcessorRegistry()
    processor.register(registry, refresh, acquire=_unreached_acquire)
    registration = registry.resolve("jira-default", "1.0", "comment")
    assert registration.name == "jira-refresh"
    assert registration.revision_field == "updated"
    assert registration.field_mapping == (
        ("Outcome", "summary"),
        ("User stories", "description"),
    )
    with pytest.raises(refresh.RefreshRefusal, match="unsupported_capability"):
        registry.resolve("jira-default", "1.0", "pull-request-link")


def test_skill_metadata_declares_workspace_write_boundary() -> None:
    body = (PROCESSOR.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "- filesystem_write" in body


def test_common_lifecycle_matrix_reuses_shared_authority(processor, refresh) -> None:
    registry = refresh.RefreshProcessorRegistry()
    processor.register(registry, refresh, acquire=_unreached_acquire)
    authority = refresh.SourceAuthority(
        source_ref="JIRA-1",
        source_revision="JIRA-1@6",
        accepted_revision="JIRA-1@5",
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
                current_revision="JIRA-1@6",
                compared_revision="JIRA-1@7",
                profile_id="jira-default",
                profile_version="1.0",
                changed_fields=(refresh.ChangedField("Outcome", "old", "new"),),
            ),
            authority=authority,
            policy=_policy(refresh),
            approver=_approver(refresh),
            decisions={"Outcome": "accept-source"},
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
        assert result.comparison_status == "completed"

    for lifecycle in ("Implementing", "Executing"):
        result = refresh.evaluate_refresh(
            comparison=refresh.RefreshComparison(
                artifact_path="docs/specs/example/spec.md",
                artifact_kind="spec",
                lifecycle=lifecycle,
                authority_mode="tracker-origin",
                current_revision="JIRA-1@6",
                compared_revision="JIRA-1@7",
                profile_id="jira-default",
                profile_version="1.0",
            ),
            authority=authority,
            policy=_policy(refresh),
            approver=_approver(refresh),
            decisions={},
        )
        assert result.local_mutation == "refused"


def test_jira_sso_write_is_zero_wire(processor, refresh) -> None:
    client = FakeJiraClient(auth_mode="sso-cookie")
    payload = {"issue_key": "PROJ-1", "body": "Linked local trace."}
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Linked local trace."},
            confirmation=_confirmation(
                refresh, action="comment", target="PROJ-1", payload=payload
            ),
            policy=_policy(refresh),
            receipt_store=object(),
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )
    assert result.code == "sso_cookie_write_refused"
    assert client.calls == []


@pytest.mark.parametrize(
    ("action", "payload", "method"),
    [
        ("comment", {"body": "Reviewed trace."}, "add_comment"),
        ("display-status", {"transition": "In Progress"}, "transition_issue"),
        ("closure", {"transition": "Done"}, "transition_issue"),
    ],
)
def test_token_write_uses_exact_allowlisted_payload(
    processor,
    refresh,
    action: str,
    payload: dict[str, str],
    method: str,
    tmp_path: Path,
) -> None:
    target = "PROJ-1"
    expected_payload = (
        {"issue_key": target, "body": payload["body"]}
        if action == "comment"
        else {"issue_key": target, "transition": payload["transition"]}
    )
    client = FakeJiraClient()
    store = _receipt_store(refresh, tmp_path)
    result = asyncio.run(
        processor.write_back(
            client=client,
            action=action,
            target=target,
            payload=payload,
            confirmation=_confirmation(
                refresh, action=action, target=target, payload=expected_payload
            ),
            policy=_policy(refresh),
            receipt_store=store,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )
    assert result.code == "succeeded"
    assert result.payload_digest == refresh.canonical_payload_digest(expected_payload)
    assert result.receipt.identity == "approver@example.com"
    assert result.receipt.confirmed_at == "2026-08-17T12:00:00Z"
    assert client.calls[0][0] == method
    assert len(client.calls) == 1
    durable = refresh.parse_source_authority(
        (store.repository_root / store.artifact_path).read_text()
    ).remote_actions
    assert durable[0]["status"] == "succeeded"
    assert durable[0]["confirmation_id"] == result.receipt.confirmation_id
    assert durable[0]["profile_version"] == "1.0"


def test_successful_jira_write_reports_terminal_receipt_update_failure(
    processor, refresh, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = FakeJiraClient()
    store = _receipt_store(refresh, tmp_path)
    payload = {"body": "Reviewed trace."}
    expected_payload = {"issue_key": "PROJ-1", **payload}
    original_record = refresh.RemoteReceiptStore.record

    def fail_terminal_record(self: object, receipt: object) -> None:
        if getattr(receipt, "status", None) == "succeeded":
            raise OSError("concurrent artifact update")
        original_record(self, receipt)

    monkeypatch.setattr(refresh.RemoteReceiptStore, "record", fail_terminal_record)
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload=payload,
            confirmation=_confirmation(
                refresh,
                action="comment",
                target="PROJ-1",
                payload=expected_payload,
            ),
            policy=_policy(refresh),
            receipt_store=store,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )

    assert result.code == "receipt_update_failed"
    assert len(client.calls) == 1
    assert result.receipt.status == "pending"
    durable = refresh.parse_source_authority(
        (store.repository_root / store.artifact_path).read_text()
    ).remote_actions
    assert durable[-1]["status"] == "pending"


def test_durable_receipt_store_preserves_confirmed_comment_payload(
    processor, refresh, tmp_path: Path
) -> None:
    target = "PROJ-1"
    original_payload = {"body": "Reviewed trace."}
    confirmed_payload = {
        "issue_key": target,
        "body": original_payload["body"],
    }
    client = FakeJiraClient()

    store = _receipt_store(refresh, tmp_path)
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target=target,
            payload=original_payload,
            confirmation=_confirmation(
                refresh,
                action="comment",
                target=target,
                payload=confirmed_payload,
            ),
            policy=_policy(refresh),
            receipt_store=store,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )

    assert result.code == "succeeded"
    assert len(client.calls) == 1
    method, args, kwargs = client.calls[0]
    receipt = kwargs["guarded_write"]
    assert (method, args) == ("add_comment", (target, "Reviewed trace."))
    assert receipt.status == "pending"
    assert (receipt.action, receipt.target) == ("comment", target)


def test_subclassed_receipt_store_is_refused_before_adapter_call(
    processor, refresh, tmp_path: Path
) -> None:
    class UnsafeStore(refresh.RemoteReceiptStore):
        pass

    client = FakeJiraClient()
    store = _receipt_store(refresh, tmp_path)
    unsafe = UnsafeStore(
        store.repository_root,
        store.artifact_path,
        store.artifact_digest,
        store.workspace_digest,
    )
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Reviewed trace."},
            confirmation=_confirmation(
                refresh,
                action="comment",
                target="PROJ-1",
                payload={"issue_key": "PROJ-1", "body": "Reviewed trace."},
            ),
            policy=_policy(refresh),
            receipt_store=unsafe,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )
    assert result.code == "receipt_store_required"
    assert client.calls == []


def test_reused_or_unauthorized_confirmation_records_zero_requests(
    processor, refresh, tmp_path: Path
) -> None:
    client = FakeJiraClient()
    payload = {"issue_key": "PROJ-1", "body": "Reviewed trace."}
    confirmation = _confirmation(
        refresh, action="comment", target="PROJ-1", payload=payload
    )
    store = _receipt_store(refresh, tmp_path)
    receipt = refresh.consume_remote_confirmation(
        confirmation=confirmation,
        expected_binding=confirmation.binding,
        policy=_policy(refresh),
        receipt_store=store,
        used_confirmation_ids=set(),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )
    store.record(receipt)
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Reviewed trace."},
            confirmation=confirmation,
            policy=_policy(refresh),
            receipt_store=store,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )
    assert result.code == "confirmation_reused"
    assert client.calls == []


def test_unknown_auth_mode_is_refused_before_receipt_or_transport(processor, refresh) -> None:
    client = SimpleNamespace(_auth_mode="unexpected")

    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Reviewed trace."},
            confirmation=object(),
            policy=_policy(refresh),
            receipt_store=object(),
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
        )
    )

    assert result.code == "unsupported_auth_mode"


def test_token_write_requires_matching_guarded_client_policy(processor, refresh) -> None:
    client = FakeJiraClient(guarded=False)
    result = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Reviewed trace."},
            confirmation=object(),
            policy=_policy(refresh),
            receipt_store=object(),
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
        )
    )
    assert result.code == "guarded_write_client_required"
    assert client.calls == []


def test_unsupported_fields_and_remote_failure_are_fail_closed(
    processor, refresh, tmp_path: Path
) -> None:
    refused = asyncio.run(
        processor.write_back(
            client=FakeJiraClient(),
            action="pull-request-link",
            target="PROJ-1",
            payload={"url": "https://example.test/pr/1"},
            confirmation=object(),
            policy=_policy(refresh),
            receipt_store=object(),
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
        )
    )
    assert refused.code == "unsupported_capability"
    assert refused.payload_digest is None

    client = FakeJiraClient(fail=True)
    store = _receipt_store(refresh, tmp_path)
    payload = {"issue_key": "PROJ-1", "body": "Reviewed trace."}
    failed = asyncio.run(
        processor.write_back(
            client=client,
            action="comment",
            target="PROJ-1",
            payload={"body": "Reviewed trace."},
            confirmation=_confirmation(
                refresh, action="comment", target="PROJ-1", payload=payload
            ),
            policy=_policy(refresh),
            receipt_store=store,
            artifact_path="docs/specs/example/spec.md",
            source_revision="JIRA-1@7",
            destination="https://tracker.example.test",
            refresh_runtime=refresh,
            destination_resolver=_safe_destination_resolver,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
    )
    assert failed.code == "remote_action_failed"
    assert failed.receipt.status == "failed"
    assert len(client.calls) == 1
    durable = refresh.parse_source_authority(
        (store.repository_root / store.artifact_path).read_text()
    ).remote_actions
    assert durable[0]["status"] == "failed"


def test_destination_guard_runs_before_request(processor, refresh) -> None:
    def public_resolver(host: str):
        assert host == "tracker.example.test"
        return ("93.184.216.34",)

    pinned = processor.validate_destination(
        "https://tracker.example.test",
        refresh_runtime=refresh,
        resolver=public_resolver,
    )
    assert pinned.host == "tracker.example.test"
    with pytest.raises(refresh.RefreshRefusal, match="destination_not_allowed"):
        processor.validate_destination(
            "https://attacker.example.test",
            refresh_runtime=refresh,
            resolver=lambda _host: ("93.184.216.34",),
        )
    with pytest.raises(refresh.RefreshRefusal, match="destination_forbidden"):
        processor.validate_destination(
            "https://tracker.example.test",
            refresh_runtime=refresh,
            resolver=lambda _host: ("127.0.0.1",),
        )


def test_skill_metadata_is_least_privilege() -> None:
    body = (ROOT / "packs/atlassian/.apm/skills/jira-refresh/SKILL.md").read_text(
        encoding="utf-8"
    )
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
    assert "auth: sso-cookie" in body
    assert "auth-fallback: creds" in body
    assert "namespace: jira" in body


def test_refresh_profile_matches_production_registration(processor, refresh) -> None:
    profile = json.loads(
        (
            ROOT
            / "packs/atlassian/.apm/skills/jira-refresh/references/refresh-profile.json"
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
