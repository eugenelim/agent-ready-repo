"""TDD stubs for the linear primitive script.

T2 invariants:
  - MAX_PAGES=5: _get_project_pages stops after 5 pages regardless of hasNextPage.
  - Retry-After: on HTTP 429, the client reads Retry-After, sleeps, and retries once.

The module is loaded via importlib so it does not need to be installed as a
package. credbroker is stubbed before exec to prevent import-time failures.
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

PACK_ROOT = Path(__file__).resolve().parents[3]
LINEAR_SCRIPT = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "linear"
    / "scripts"
    / "linear.py"
)
REFRESH_SCRIPT = (
    PACK_ROOT.parent
    / "core"
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "refresh.py"
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _page_response(project_id: str, *, has_next: bool, cursor: str = "cur-1") -> httpx.Response:
    """200 response with one issue per page."""
    body = {
        "data": {
            "project": {
                "id": project_id,
                "name": "Test Project",
                "issues": {
                    "nodes": [{"identifier": "ENG-1", "title": "Issue", "description": ""}],
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                },
            }
        }
    }
    return httpx.Response(200, json=body)


def _rate_limit_response(retry_after: int = 1) -> httpx.Response:
    return httpx.Response(429, headers={"Retry-After": str(retry_after)}, text="rate limited")


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
    workspace.write_text("# workspace\n", encoding="utf-8")
    return refresh_mod.RemoteReceiptStore.open(
        repository_root=repo,
        artifact_path="docs/product/briefs/example.md",
        expected_artifact_digest=refresh_mod.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh_mod.digest_bytes(workspace.read_bytes()),
    )


# ---------------------------------------------------------------------------
# T2a: pagination bound
# ---------------------------------------------------------------------------

class TestGetProjectMaxPages:
    """MAX_PAGES=5: the function stops after 5 pages even when hasNextPage is always True."""

    def test_get_project_stops_at_max_pages(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        post_calls: list[int] = []

        def _mock_post(url: str, **kwargs: object) -> httpx.Response:
            post_calls.append(1)
            return _page_response("proj-uuid", has_next=True, cursor=f"cur-{len(post_calls)}")

        monkeypatch.setattr(linear_mod, "_bounded_post", _mock_post)

        result = linear_mod._get_project_pages("fake-key", "proj-uuid")

        assert len(post_calls) == linear_mod.MAX_PAGES, (
            f"Expected exactly MAX_PAGES={linear_mod.MAX_PAGES} HTTP calls; got {len(post_calls)}"
        )
        # 1 issue per page × 5 pages
        assert len(result["issues"]["nodes"]) == linear_mod.MAX_PAGES


# ---------------------------------------------------------------------------
# T2b: Retry-After handling
# ---------------------------------------------------------------------------

class TestRetryAfterOn429:
    """On HTTP 429 with Retry-After, the client sleeps and makes exactly one retry."""

    def test_get_project_respects_retry_after_on_429(
        self,
        linear_mod: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        post_calls: list[int] = []
        sleep_args: list[float] = []

        def _mock_post(url: str, **kwargs: object) -> httpx.Response:
            post_calls.append(1)
            if len(post_calls) == 1:
                return _rate_limit_response(retry_after=30)
            return _page_response("proj-uuid", has_next=False)

        monkeypatch.setattr(linear_mod, "_bounded_post", _mock_post)
        monkeypatch.setattr(linear_mod.time, "sleep", lambda s: sleep_args.append(float(s)))

        result = linear_mod._get_project_pages("fake-key", "proj-uuid")

        assert len(post_calls) == 2, (
            f"Expected 2 HTTP calls (initial + 1 retry after 429); got {len(post_calls)}"
        )
        assert sleep_args == [1.0], (
            f"Expected profile-clamped time.sleep(1); got {sleep_args}"
        )
        assert result["id"] == "proj-uuid"


class TestIntakeAcquisitionContract:
    """The sibling read primitive preserves strict, bounded intake provenance."""

    def test_queries_request_comparable_revision(self, linear_mod: types.ModuleType) -> None:
        assert "updatedAt" in linear_mod._GET_ISSUE_QUERY
        assert "updatedAt" in linear_mod._GET_PROJECT_QUERY

    def test_retry_constants_match_profile(self, linear_mod: types.ModuleType) -> None:
        profile_path = (
            Path(__file__).resolve().parents[3]
            / ".apm/skills/linear-brief-intake/references/intake-profile.json"
        )
        budget = json.loads(profile_path.read_text(encoding="utf-8"))["budget"]
        assert budget["max_retries"] == linear_mod.MAX_RETRIES
        assert list(linear_mod.RETRY_BACKOFF_SECONDS) == budget["backoff_seconds"]

    def test_response_byte_budget_fails_closed(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        oversized = httpx.Response(200, content=b"x" * (linear_mod.MAX_RESPONSE_BYTES + 1))
        monkeypatch.setattr(linear_mod, "_bounded_post", lambda *args, **kwargs: oversized)

        with pytest.raises(SystemExit) as exc_info:
            linear_mod._graphql_request("opaque-key", "{ viewer { id } }")

        assert exc_info.value.code == linear_mod.EXIT_ERROR

    def test_response_byte_budget_stops_streaming_at_cap(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks_read = 0

        class ChunkStream(httpx.SyncByteStream):
            def __iter__(self):
                nonlocal chunks_read
                chunks_read += 1
                yield b"x" * linear_mod.MAX_RESPONSE_BYTES
                chunks_read += 1
                yield b"y"
                raise AssertionError("reader continued after crossing the byte cap")

        response = httpx.Response(
            200,
            stream=ChunkStream(),
            request=httpx.Request("POST", linear_mod.GRAPHQL_URL),
        )

        class ResponseContext:
            def __enter__(self):
                return response

            def __exit__(self, *_args: object) -> None:
                response.close()

        monkeypatch.setattr(
            linear_mod.httpx, "stream", lambda *args, **kwargs: ResponseContext()
        )
        with pytest.raises(SystemExit) as exc_info:
            linear_mod._bounded_post(
                linear_mod.GRAPHQL_URL,
                json_body={"query": "{}"},
                headers={},
                timeout=1,
            )

        assert exc_info.value.code == linear_mod.EXIT_ERROR
        assert chunks_read == 2

    def test_non_standard_json_fails_closed(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        invalid = httpx.Response(
            200,
            content=json.dumps({"data": {"value": None}}).replace("null", "NaN").encode(),
        )
        monkeypatch.setattr(linear_mod, "_bounded_post", lambda *args, **kwargs: invalid)

        with pytest.raises(SystemExit) as exc_info:
            linear_mod._graphql_request("opaque-key", "{ viewer { id } }")

        assert exc_info.value.code == linear_mod.EXIT_ERROR

    def test_pinned_transport_selects_one_of_multiple_validated_addresses(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, object] = {}

        class ResponseContext:
            def __init__(self, request: httpx.Request) -> None:
                self.response = httpx.Response(200, content=b"{}", request=request)

            def __enter__(self) -> httpx.Response:
                return self.response

            def __exit__(self, *_args: object) -> None:
                self.response.close()

        class FakeClient:
            def __enter__(self):
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def stream(self, method: str, url: str, **kwargs: object) -> ResponseContext:
                captured.update({"method": method, "url": url, **kwargs})
                return ResponseContext(httpx.Request(method, url))

        transport_marker = object()
        monkeypatch.setattr(
            linear_mod,
            "_pinned_transport",
            lambda _destination: transport_marker,
            raising=False,
        )

        def client_factory(**kwargs: object) -> FakeClient:
            captured["client_kwargs"] = kwargs
            return FakeClient()

        monkeypatch.setattr(linear_mod.httpx, "Client", client_factory)
        pinned = types.SimpleNamespace(
            addresses=("2001:4860:4860::8888", "93.184.216.34"),
            host="api.linear.app",
            port=443,
        )

        response = linear_mod._bounded_post(
            linear_mod.GRAPHQL_URL,
            json_body={"query": "{}"},
            headers={"Authorization": "opaque-key"},
            timeout=1,
            pinned_destination=pinned,
        )

        assert response.status_code == 200
        assert captured["url"] == "https://93.184.216.34:443/graphql"
        assert captured["headers"] == {
            "Authorization": "opaque-key",
            "Host": "api.linear.app",
        }
        assert captured["extensions"] == {"sni_hostname": "api.linear.app"}
        assert captured["client_kwargs"] == {
            "timeout": 1,
            "transport": transport_marker,
            "trust_env": False,
        }

    def test_pinned_transport_honors_https_proxy_and_pins_its_socket(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8443")
        monkeypatch.delenv("https_proxy", raising=False)
        monkeypatch.setattr(linear_mod, "proxy_bypass", lambda _host: False, raising=False)
        monkeypatch.setattr(
            linear_mod.socket,
            "getaddrinfo",
            lambda _host, _port: [
                (2, 1, 6, "", ("192.0.2.20", 8443)),
                (2, 1, 6, "", ("192.0.2.21", 8443)),
            ],
        )
        pinned = types.SimpleNamespace(host="api.linear.app", port=443)

        transport = linear_mod._pinned_transport(pinned)

        assert isinstance(transport, linear_mod.httpx.HTTPTransport)
        assert isinstance(
            transport._pool._network_backend, linear_mod._PinnedSyncNetworkBackend
        )
        assert transport._pool._network_backend._proxy_pin == (
            "proxy.example",
            8443,
            frozenset({"192.0.2.20", "192.0.2.21"}),
        )

    @pytest.mark.parametrize(
        "address",
        ["0.0.0.0", "169.254.169.254", "fe80::1", "fd00:ec2::254"],
    )
    def test_proxy_metadata_or_unspecified_address_is_refused_redacted(
        self,
        linear_mod: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        address: str,
    ) -> None:
        monkeypatch.setattr(
            linear_mod.socket,
            "getaddrinfo",
            lambda _host, port: [(2, 1, 6, "", (address, port))],
        )

        with pytest.raises(linear_mod.httpx.TransportError) as exc:
            linear_mod._resolved_proxy_addresses("proxy.example", 8443)

        assert str(exc.value) == "HTTPS proxy resolution failed"

    def test_no_proxy_bypasses_proxy_without_resolving_it(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8443")
        monkeypatch.setattr(linear_mod, "proxy_bypass", lambda _host: True, raising=False)
        monkeypatch.setattr(
            linear_mod.socket,
            "getaddrinfo",
            lambda *_args: pytest.fail("NO_PROXY path must not resolve proxy"),
        )

        assert linear_mod._https_proxy_settings("api.linear.app") == (None, None)

    def test_unsupported_proxy_scheme_fails_closed_redacted(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTTPS_PROXY", "ftp://proxy.example:21")
        monkeypatch.setattr(linear_mod, "proxy_bypass", lambda _host: False)

        with pytest.raises(linear_mod.httpx.TransportError) as exc:
            linear_mod._https_proxy_settings("api.linear.app")

        assert str(exc.value) == "HTTPS proxy configuration is unsupported"

    def test_unreadable_ca_bundle_fails_closed_redacted(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/unreadable/ca-bundle.pem")
        monkeypatch.delenv("SSL_CERT_FILE", raising=False)

        with pytest.raises(linear_mod.httpx.TransportError) as exc:
            linear_mod._linear_ssl_context()

        assert str(exc.value) == "TLS trust configuration is unavailable"

    def test_linear_ssl_context_honors_ca_environment(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[tuple[str | None, str | None]] = []

        class FakeContext:
            def load_verify_locations(
                self, *, cafile: str | None, capath: str | None
            ) -> None:
                calls.append((cafile, capath))

        monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/managed/example-ca.crt")
        monkeypatch.delenv("SSL_CERT_FILE", raising=False)
        monkeypatch.setenv("SSL_CERT_DIR", "/managed/example-ca-dir")
        monkeypatch.setattr(linear_mod.ssl, "create_default_context", FakeContext)

        context = linear_mod._linear_ssl_context()

        assert isinstance(context, FakeContext)
        assert calls == [("/managed/example-ca.crt", "/managed/example-ca-dir")]

    def test_proxy_rebinding_fails_closed_with_redacted_error(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend = linear_mod._PinnedSyncNetworkBackend(
            ("proxy.example", 8443, frozenset({"192.0.2.20"}))
        )
        monkeypatch.setattr(
            linear_mod.socket,
            "getaddrinfo",
            lambda _host, _port: [(2, 1, 6, "", ("192.0.2.99", 8443))],
        )

        with pytest.raises(linear_mod.httpx.TransportError) as exc:
            backend.connect_tcp("proxy.example", 8443)

        assert "proxy.example" not in str(exc.value)
        assert "192.0.2" not in str(exc.value)

    def test_project_marks_max_page_truncation_incomplete(
        self, linear_mod: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            linear_mod,
            "_bounded_post",
            lambda *args, **kwargs: _page_response("proj-uuid", has_next=True),
        )

        result = linear_mod._get_project_pages("opaque-key", "proj-uuid")

        assert result["intake_budget"] == {"complete": False, "result": "marked-incomplete"}


class TestLinearRefreshProcessor:
    """Linear refresh write-back stays inside the shared refresh contract."""

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
        assert result.payload == {}
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
        assert result.payload == {}
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
        assert result.payload == {}
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
