"""Cross-pack contract tests for the Linear refresh processor.

The Linear processor drives core's work-intake refresh coordinator, so this
coverage spans two packs and lives here rather than under `packs/linear/`
(`lint-pack-test-boundary.py` § pack-tests-stay-in-pack).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

httpx = pytest.importorskip("httpx")

ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = ROOT / "packs" / "linear"
LINEAR_SCRIPT = (
    PACK_ROOT / ".apm" / "skills" / "linear" / "scripts" / "linear.py"
)
REFRESH_SCRIPT = (
    ROOT / "packs" / "core" / ".apm" / "skills" / "work-intake" / "scripts" / "refresh.py"
)


def _unreached_acquire(_locator: str, _revision: str) -> dict[str, object]:
    raise AssertionError("acquisition should not run in this test")


@pytest.fixture(scope="module")
def linear_mod() -> types.ModuleType:
    """Load linear.py once per session; stub credbroker to avoid import-time auth."""
    credbroker_stub = types.ModuleType("credbroker")
    credbroker_stub.CredentialsMissingError = Exception  # type: ignore[attr-defined]
    credbroker_stub.load_credentials = lambda *a, **kw: None  # type: ignore[attr-defined]
    sys.modules.setdefault("credbroker", credbroker_stub)

    spec = importlib.util.spec_from_file_location("linear_script", LINEAR_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture(scope="module")
def refresh_mod() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("work_intake_refresh", REFRESH_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _policy(refresh_mod: types.ModuleType):
    return refresh_mod.RefreshAuthorizationPolicy(
        draft_approver_roles=("product",),
        accepted_approver_roles=("product",),
        remote_mutation_approver_roles=("product",),
    )


def _approver(refresh_mod: types.ModuleType):
    return refresh_mod.ApproverEvidence(
        identity="approver@example.com",
        role="product",
        confirmed_at="2026-08-17T12:00:00Z",
        authorization_source="current-human-session",
    )


def _confirmation(
    refresh_mod: types.ModuleType,
    *,
    action: str = "comment",
    payload: dict[str, object] | None = None,
    confirmation_id: str = "confirm-1",
):
    payload = payload or {"issue_id": "lin-1", "body": "Looks good"}
    binding = refresh_mod.ConfirmationBinding(
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        profile_id="linear-default",
        profile_version="1.0",
        destination="https://api.linear.app:443",
        action=action,
        target="lin-1",
        payload_digest=refresh_mod.canonical_payload_digest(payload),
    )
    return refresh_mod.RemoteConfirmation.issue(
        confirmation_id=confirmation_id,
        binding=binding,
        approver=_approver(refresh_mod),
        confirmed_at=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )


def _receipt_store(refresh_mod: types.ModuleType, tmp_path: Path):
    repo = tmp_path / "repo"
    artifact = repo / "docs/product/briefs/example.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        '''# Example

```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "linear://issue/lin-1"
source_revision = "remote-rev-2"

[owned_fields]
Outcome = "local"
```
''',
        encoding="utf-8",
    )
    workspace.write_text(
        '''[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["product"]
accepted_approver_roles = ["product"]
remote_mutation_approver_roles = ["product"]
''',
        encoding="utf-8",
    )
    return refresh_mod.RemoteReceiptStore.open(
        repository_root=repo,
        artifact_path="docs/product/briefs/example.md",
        expected_artifact_digest=refresh_mod.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh_mod.digest_bytes(workspace.read_bytes()),
    )


class TestLinearRefreshProcessor:
    """Linear refresh write-back stays inside the shared refresh contract."""

    @pytest.mark.parametrize(
        "url",
        (
            "https://user:secret@example.test/trace",
            "http://example.test/trace",
            "https://example.test/trace link",
        ),
    )
    def test_linear_refuses_untrusted_coordination_urls_before_transport(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
        url: str,
    ) -> None:
        calls: list[dict[str, object]] = []
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **kwargs: calls.append(kwargs) or {},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="trace-link",
            target="lin-1",
            url=url,
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod, action="trace-link"),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "invalid_remote_payload"
        assert result.transport_calls == 0
        assert calls == []

    def test_linear_accepts_https_trace_link_with_explicit_port(
        self, linear_mod: types.ModuleType
    ) -> None:
        assert linear_mod._trusted_https_url(
            "https://git.example.test:8443/org/repo/-/merge_requests/1"
        )

    def test_linear_shipped_write_is_allowlisted(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        calls: list[dict[str, object]] = []
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **kwargs: calls.append(kwargs)
            or {"data": {"commentCreate": {"success": True}}},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="Looks good",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.action == "comment"
        assert result.code == "remote_action_succeeded"
        assert result.payload_digest == refresh_mod.canonical_payload_digest(
            {"issue_id": "lin-1", "body": "Looks good"}
        )
        assert result.transport_calls == 1
        assert calls[0]["variables"]["input"] == {
            "issueId": "lin-1",
            "body": "Looks good",
        }
        assert calls[0]["pinned_destination"].addresses == ("93.184.216.34",)

    def test_linear_refuses_undeclared_mutation_field(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **_kwargs: {"data": {}},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="requirement_body",
            target="lin-1",
            body="Change the requirement",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod, action="requirement_body"),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "unsupported_capability"
        assert result.transport_calls == 0

    def test_linear_rejects_confirmation_reuse(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        calls: list[dict[str, object]] = []
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **kwargs: calls.append(kwargs)
            or {"data": {"commentCreate": {"success": True}}},
            resolver=lambda _host: ("93.184.216.34",),
        )
        confirmation = _confirmation(refresh_mod)
        kwargs = {
            "action": "comment",
            "target": "lin-1",
            "body": "Looks good",
            "artifact_path": "docs/product/briefs/example.md",
            "source_revision": "remote-rev-2",
            "policy": _policy(refresh_mod),
            "confirmation": confirmation,
            "now": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        }

        processor.write(**kwargs)
        replay = processor.write(**kwargs)

        assert replay.code == "confirmation_reused"
        assert replay.transport_calls == 0
        assert len(calls) == 1

    def test_linear_requires_durable_confirmation_ledger(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        calls: list[dict[str, object]] = []
        confirmation = _confirmation(refresh_mod)
        kwargs = {
            "action": "comment",
            "target": "lin-1",
            "body": "Looks good",
            "artifact_path": "docs/product/briefs/example.md",
            "source_revision": "remote-rev-2",
            "policy": _policy(refresh_mod),
            "confirmation": confirmation,
            "now": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        }
        without_ledger = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **values: calls.append(values) or {},
            resolver=lambda _host: ("93.184.216.34",),
        )
        store = _receipt_store(refresh_mod, tmp_path)
        binding = confirmation.binding
        durable_receipt = refresh_mod.consume_remote_confirmation(
            confirmation=confirmation,
            expected_binding=binding,
            policy=_policy(refresh_mod),
            receipt_store=store,
            used_confirmation_ids=set(),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )
        store.record(durable_receipt)
        seeded_from_artifact = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=store,
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **values: calls.append(values) or {},
            resolver=lambda _host: ("93.184.216.34",),
        )

        assert without_ledger.write(**kwargs).code == "receipt_store_required"
        assert seeded_from_artifact.write(**kwargs).code == "confirmation_reused"
        assert calls == []

    def test_destination_is_validated_before_credentials_and_transport(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        events: list[str] = []
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: events.append("credentials") or "opaque-key",
            graphql_transport=lambda **kwargs: events.append("transport") or {"data": {}},
            resolver=lambda _host: ("127.0.0.1",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="Looks good",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "destination_forbidden"
        assert result.transport_calls == 0
        assert events == []

    def test_remote_failure_is_retry_safe_without_secondary_mutation(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        calls: list[dict[str, object]] = []

        def fail_once(**kwargs: object) -> dict[str, object]:
            calls.append(dict(kwargs))
            raise RuntimeError("rate limited")

        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=_receipt_store(refresh_mod, tmp_path),
            api_key_loader=lambda: "opaque-key",
            graphql_transport=fail_once,
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="Looks good",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "remote_action_failed"
        assert result.receipt["status"] == "failed"
        assert result.receipt["profile_version"] == "1.0"
        assert result.transport_calls == 1
        assert len(calls) == 1

    def test_successful_action_reports_terminal_receipt_update_failure(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[dict[str, object]] = []
        store = _receipt_store(refresh_mod, tmp_path)
        original_record = refresh_mod.RemoteReceiptStore.record

        def fail_terminal_record(self: object, receipt: object) -> None:
            if getattr(receipt, "status", None) == "succeeded":
                raise OSError("concurrent artifact update")
            original_record(self, receipt)

        monkeypatch.setattr(
            refresh_mod.RemoteReceiptStore, "record", fail_terminal_record
        )
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=store,
            api_key_loader=lambda: "opaque-key",
            graphql_transport=lambda **kwargs: calls.append(dict(kwargs))
            or {"data": {"commentCreate": {"success": True}}},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="Looks good",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "receipt_update_failed"
        assert result.transport_calls == 1
        assert len(calls) == 1
        durable = refresh_mod.parse_source_authority(
            (store.repository_root / store.artifact_path).read_text()
        ).remote_actions
        assert durable[-1]["status"] == "pending"

    def test_linear_refresh_registration_declares_profile_capabilities(
        self, linear_mod: types.ModuleType, refresh_mod: types.ModuleType
    ) -> None:
        registration = linear_mod.linear_refresh_registration(
            refresh_mod, acquire=_unreached_acquire
        )
        profile = linear_mod.load_refresh_profile()
        assert registration.profile_id == profile["id"]
        assert registration.profile_version == profile["version"]
        assert registration.revision_field == profile["revision_field"]
        assert registration.field_mapping == tuple(profile["field_mapping"].items())
        assert registration.capabilities == frozenset(profile["capabilities"])

    def test_refresh_profile_refuses_redirects_enabled_before_transport(
        self, linear_mod: types.ModuleType, tmp_path: Path
    ) -> None:
        profile = json.loads(linear_mod.PROFILE_PATH.read_text(encoding="utf-8"))
        profile["destination"]["redirects"] = True
        path = tmp_path / "refresh-profile.json"
        path.write_text(json.dumps(profile), encoding="utf-8")

        with pytest.raises(RuntimeError, match="invalid_refresh_profile"):
            linear_mod.load_refresh_profile(path)

    def test_missing_receipt_store_refuses_before_credentials(
        self, linear_mod: types.ModuleType, refresh_mod: types.ModuleType
    ) -> None:
        events: list[str] = []
        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            api_key_loader=lambda: events.append("credentials") or "opaque-key",
            graphql_transport=lambda **_kwargs: events.append("transport") or {},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="Looks good",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(refresh_mod),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "receipt_store_required"
        assert events == []

    def test_pending_receipt_failure_refuses_before_credentials_and_transport(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        tmp_path: Path,
    ) -> None:
        events: list[str] = []
        store = _receipt_store(refresh_mod, tmp_path)
        artifact = store.repository_root / store.artifact_path
        artifact.write_text(artifact.read_text() + "\n# concurrent change\n")

        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=store,
            api_key_loader=lambda: events.append("credentials") or "opaque-key",
            graphql_transport=lambda **_kwargs: events.append("transport") or {},
            resolver=lambda _host: ("93.184.216.34",),
        )

        result = processor.write(
            action="comment",
            target="lin-1",
            body="sensitive tracker content",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=_confirmation(
                refresh_mod,
                payload={
                    "issue_id": "lin-1",
                    "body": "sensitive tracker content",
                },
            ),
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        )

        assert result.code == "fingerprint_mismatch"
        assert result.transport_calls == 0
        assert "sensitive tracker content" not in repr(result.__dict__)
        assert events == []

    @pytest.mark.parametrize(
        ("action", "kwargs", "result_key", "expected_input"),
        [
            (
                "trace-link",
                {"url": "https://example.invalid/trace/1"},
                "attachmentCreate",
                {
                    "issueId": "lin-1",
                    "url": "https://example.invalid/trace/1",
                    "title": "Trace link",
                },
            ),
            (
                "pull-request-link",
                {"url": "https://example.invalid/pull/1"},
                "attachmentCreate",
                {
                    "issueId": "lin-1",
                    "url": "https://example.invalid/pull/1",
                    "title": "Pull request",
                },
            ),
            (
                "display-status",
                {"status": "state-open"},
                "issueUpdate",
                {"stateId": "state-open"},
            ),
            (
                "closure",
                {"status": "state-done"},
                "issueUpdate",
                {"stateId": "state-done"},
            ),
        ],
    )
    def test_linear_actions_use_documented_mutations_after_pending_receipt(
        self,
        linear_mod: types.ModuleType,
        refresh_mod: types.ModuleType,
        action: str,
        kwargs: dict[str, str],
        result_key: str,
        expected_input: dict[str, str],
        tmp_path: Path,
    ) -> None:
        events: list[object] = []
        store = _receipt_store(refresh_mod, tmp_path)

        def transport(**transport_kwargs: object) -> dict[str, object]:
            durable = refresh_mod.parse_source_authority(
                (store.repository_root / store.artifact_path).read_text()
            ).remote_actions
            events.append(("receipt", durable[-1]["status"]))
            events.append(("transport", transport_kwargs))
            return {"data": {result_key: {"success": True}}}

        processor = linear_mod.LinearRefreshProcessor(
            refresh_runtime=refresh_mod,
            receipt_store=store,
            api_key_loader=lambda: events.append("credentials") or "opaque-key",
            graphql_transport=transport,
            resolver=lambda _host: ("93.184.216.34",),
        )
        payload = {"issue_id": "lin-1"}
        if action in {"trace-link", "pull-request-link"}:
            payload.update(
                {
                    "url": kwargs["url"],
                    "title": "Pull request" if action == "pull-request-link" else "Trace link",
                }
            )
        else:
            payload["state_id"] = kwargs["status"]
        confirmation = _confirmation(
            refresh_mod,
            action=action,
            payload=payload,
            confirmation_id=f"confirm-{action}",
        )

        result = processor.write(
            action=action,
            target="lin-1",
            artifact_path="docs/product/briefs/example.md",
            source_revision="remote-rev-2",
            policy=_policy(refresh_mod),
            confirmation=confirmation,
            now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
            **kwargs,
        )

        assert result.code == "remote_action_succeeded"
        assert events[0] == "credentials"
        assert events[1] == ("receipt", "pending")
        assert events[2][0] == "transport"
        transport_kwargs = events[2][1]
        if action in {"trace-link", "pull-request-link"}:
            assert transport_kwargs["variables"] == {"input": expected_input}
        else:
            assert transport_kwargs["variables"] == {
                "id": "lin-1",
                "input": expected_input,
            }
        durable = refresh_mod.parse_source_authority(
            (store.repository_root / store.artifact_path).read_text()
        ).remote_actions
        assert durable[-1]["status"] == "succeeded"


# STUB: AC19
def test_linear_profile_is_in_the_integrated_routing_matrix() -> None:
    matrix = json.loads(
        (ROOT / "packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json").read_text(
            encoding="utf-8"
        )
    )
    assert any(case.get("profile_id") == "linear-default" for case in matrix["cases"])
