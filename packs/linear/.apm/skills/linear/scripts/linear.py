#!/usr/bin/env python3
"""Linear GraphQL API CLI (api.linear.app).

Subcommands:
    check                        Verify credentials and reachability.
    get-issue IDENTIFIER         Fetch one issue by human slug (e.g. ENG-123).
    get-project PROJECT_ID       Fetch a project's issues (up to 250).

The Linear API key is never accepted on the command line. It is resolved via
the ``credbroker`` library (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile);
run ``credential-setup`` skill to populate the ``linear`` namespace.

Auth: ``Authorization: <KEY>`` (no "Bearer" prefix — Linear uses bare token).
Endpoint: https://api.linear.app/graphql
Rate limit: 5 000 req/hr for Personal API Keys; 429 + Retry-After respected.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import ipaddress
import json
import logging
import os
import re
import shlex
import socket
import ssl
import sys
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, cast
from urllib.parse import urlparse, urlsplit
from urllib.request import proxy_bypass

if __package__ in (None, "") and __spec__ is None:
    for _stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            _stream.reconfigure(encoding="utf-8")
    _here = Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    _floor = Path("~/.agentbundle/lib").expanduser()
    if _floor.is_dir() and str(_floor) not in sys.path:
        sys.path.append(str(_floor))
    __package__ = _here.name

try:
    import httpx
except ModuleNotFoundError as _import_exc:
    sys.stderr.write(
        f"error: missing dependency {_import_exc.name!r} — run: "
        "python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(2) from None

log = logging.getLogger("linear.cli")

# Banded exit-code taxonomy:
#   0     success
#   1     functional / operational error — bad args, server 5xx, transport, unexpected
#   2     user must act — credential missing/invalid/expired, 401/403
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_ACTION = 2

PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "refresh-profile.json"
GRAPHQL_URL = "https://api.linear.app/graphql"
LINEAR_PROFILE_ID = "linear-default"
LINEAR_PROFILE_VERSION = "1.0"
_REFRESH_RUNTIME: ModuleType | None = None
PAGE_SIZE = 50
MAX_PAGES = 5  # hard bound: ≤250 issues (PAGE_SIZE × MAX_PAGES)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_RETRIES = 1
RETRY_BACKOFF_SECONDS = (1,)
DEFAULT_TIMEOUT_S = 30.0

TOKEN_CLI_FLAGS = frozenset({
    "--token",
    "--api-token",
    "--api-key",
    "--bearer",
    "-t",
    "--linear-token",
    "--pat",
    "--password",
    "--access-token",
    "--auth-token",
})

_COMMENT_CREATE_MUTATION = """
mutation CommentCreate($input: CommentCreateInput!) {
  commentCreate(input: $input) { success comment { id } }
}
"""
_ATTACHMENT_CREATE_MUTATION = """
mutation AttachmentCreate($input: AttachmentCreateInput!) {
  attachmentCreate(input: $input) { success attachment { id } }
}
"""
_ISSUE_UPDATE_MUTATION = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) { success issue { id } }
}
"""


class LinearWriteBackResult:
    """Redacted result for one confirmed Linear write-back attempt."""

    def __init__(
        self,
        code: str,
        action: str,
        *,
        target: str = "",
        payload_digest: str | None = None,
        transport_calls: int = 0,
        receipt: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.action = action
        self.target = target
        self.payload_digest = payload_digest
        self.payload: dict[str, object] = {}
        self.transport_calls = transport_calls
        self.receipt = receipt or {}


def _render_windows_command(argv: list[str], fallback: str) -> str:
    """Render only cmd/PowerShell-inert Windows argv; refuse everything else."""
    safe_punctuation = frozenset(" _./:\\-")
    if any(
        not value
        or any(
            not char.isascii() or (not char.isalnum() and char not in safe_punctuation)
            for char in value
        )
        for value in argv
    ):
        return f"{fallback} (use an argv-capable terminal)"
    return " ".join(f'"{value}"' if " " in value else value for value in argv)


def _display_program() -> str:
    """Return a shell-safe display form for this verified installed entry."""
    fallback = "the installed linear.py entry point"
    try:
        entry = Path(__file__).resolve(strict=True)
        entry.relative_to(entry.parent.resolve(strict=True))
        if not entry.is_file():
            return fallback
    except (OSError, RuntimeError, ValueError):
        return fallback
    argv = [sys.executable, str(entry)]
    if sys.platform == "win32":
        return _render_windows_command(argv, fallback)
    return shlex.join(argv)


_CREDENTIAL_LOOKING_RE = re.compile(r"^[A-Za-z0-9_/+=%.~-]{20,}$")
_STRIP_CHARS = "'\"`(),;:."


def _reject_token_on_cli(argv: list[str]) -> None:
    """Linear API keys must not appear as command-line arguments."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API keys must not be passed on the command line. "
                "Run `credential-setup` skill to store LINEAR_API_KEY "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


def _load_refresh_runtime() -> ModuleType:
    """Load the shared work-intake refresh runtime from an installed skill tree."""

    global _REFRESH_RUNTIME
    if _REFRESH_RUNTIME is not None:
        return _REFRESH_RUNTIME
    here = Path(__file__).resolve()
    skills_root = here.parents[2]
    candidate = skills_root / "work-intake" / "scripts" / "refresh.py"
    try:
        resolved_root = skills_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise RuntimeError("work-intake refresh runtime unavailable") from exc
    if not resolved.is_file():
        raise RuntimeError("work-intake refresh runtime unavailable")
    module_name = "_work_intake_refresh_runtime_" + hashlib.sha256(
        str(resolved).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(module_name)
    if module is not None:
        _REFRESH_RUNTIME = module
        return _REFRESH_RUNTIME
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError("work-intake refresh runtime unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    _REFRESH_RUNTIME = module
    return _REFRESH_RUNTIME


def _trusted_https_url(value: str | None) -> bool:
    """Accept a bounded, credential-free HTTPS URL for a coordination link."""

    if not value or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and parsed.hostname is not None
        and (port is None or port > 0)
        and parsed.path.startswith("/")
    )


def load_refresh_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    """Load the strict Linear processor profile from its installed skill."""

    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
        destination = profile["destination"]
        capabilities = profile["capabilities"]
        mapping = profile["field_mapping"]
        if (
            not isinstance(profile, dict)
            or set(profile) != {
                "contract_version", "id", "version", "revision_field", "field_mapping",
                "capabilities", "destination",
            }
            or profile.get("contract_version") != "tracker-refresh-profile.v1"
            or profile.get("id") != LINEAR_PROFILE_ID
            or profile.get("version") != LINEAR_PROFILE_VERSION
            or not isinstance(profile.get("revision_field"), str)
            or not isinstance(mapping, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in mapping.items()
            )
            or not isinstance(capabilities, list)
            or any(not isinstance(value, str) for value in capabilities)
            or len(capabilities) != len(set(capabilities))
            or "acquire" not in capabilities
            or not isinstance(destination, dict)
            or destination.get("scheme") != "https"
            or not isinstance(destination.get("host"), str)
            or not isinstance(destination.get("port"), int)
            or destination.get("redirects") is not False
            or destination.get("dns_policy") != "pinned-address"
        ):
            raise ValueError
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("invalid_refresh_profile") from exc
    return cast(dict[str, Any], profile)


def linear_refresh_registration(
    refresh_runtime: ModuleType | None = None,
    *,
    acquire: Callable[[str, str], Mapping[str, object]],
) -> object:
    """Return the configured Linear refresh processor registration."""

    runtime = refresh_runtime or _load_refresh_runtime()
    profile = load_refresh_profile()
    return runtime.ProcessorRegistration(
        name="linear-refresh",
        profile_id=profile["id"],
        profile_version=profile["version"],
        capabilities=frozenset(profile["capabilities"]),
        acquire=acquire,
        revision_field=profile["revision_field"],
        field_mapping=tuple(profile["field_mapping"].items()),
    )


class _ScrubbingArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that redacts credential-shaped values from error messages."""

    def error(self, message: str) -> None:
        def _scrub(match: re.Match[str]) -> str:
            tok = match.group(0)
            if tok.startswith("-"):
                if "=" in tok:
                    flag, _, value = tok.partition("=")
                    core = value.strip(_STRIP_CHARS)
                    if _CREDENTIAL_LOOKING_RE.match(core):
                        return f"{flag}=<scrubbed>"
                return tok
            core = tok.strip(_STRIP_CHARS)
            if _CREDENTIAL_LOOKING_RE.match(core):
                return "<scrubbed>"
            return tok

        scrubbed = re.sub(r"\S+", _scrub, message)
        super().error(scrubbed)


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


def _load_api_key() -> str:
    """Resolve the Linear API key via credbroker (lazy import).

    Never logs, echoes, or returns the key to the caller's output path.
    Exits with EXIT_USER_ACTION (2) when credentials are missing.
    """
    from credbroker import (
        CredentialsMissingError,
    )
    from credbroker import (
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load("linear", required_keys=["API_KEY"])
    except CredentialsMissingError as exc:
        sys.stderr.write(
            f"error: credentials missing — {exc}\n"
            "Run `credential-setup` skill to store LINEAR_API_KEY.\n"
        )
        raise SystemExit(EXIT_USER_ACTION) from exc

    return creds.API_KEY  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# GraphQL transport
# ---------------------------------------------------------------------------


def _graphql_request(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    url: str = GRAPHQL_URL,
    timeout: float = DEFAULT_TIMEOUT_S,
    pinned_destination: object | None = None,
) -> dict[str, Any]:
    """POST one GraphQL request.  Returns the parsed JSON body.

    Raises SystemExit(EXIT_USER_ACTION) on 401/403.
    Raises SystemExit(EXIT_ERROR) on network errors, server 5xx, or non-JSON.
    On HTTP 429 the caller is responsible for reading Retry-After and retrying.
    """
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "linear-skill/0.1",
    }

    try:
        resp = _bounded_post(
            url,
            json_body=payload,
            headers=headers,
            timeout=timeout,
            pinned_destination=pinned_destination,
        )
    except httpx.TransportError as exc:
        sys.stderr.write(f"error: network error — {exc}\n")
        raise SystemExit(EXIT_ERROR) from exc

    if resp.status_code in (401, 403):
        sys.stderr.write(
            f"error: HTTP {resp.status_code} — credentials invalid or "
            "insufficient permissions. Regenerate your Personal API Key at "
            "Linear → Settings → API and re-run `credential-setup`.\n"
        )
        raise SystemExit(EXIT_USER_ACTION)

    if resp.status_code == 429:
        return resp  # type: ignore[return-value]  # caller checks is_429

    if resp.status_code >= 500:
        sys.stderr.write(f"error: Linear server error {resp.status_code}\n")
        raise SystemExit(EXIT_ERROR)

    try:
        body = json.loads(
            resp.content.decode("utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant: {value}")
            ),
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write("error: Linear returned invalid strict JSON\n")
        raise SystemExit(EXIT_ERROR) from exc

    if "errors" in body:
        sys.stderr.write("error: Linear returned a GraphQL error\n")
        raise SystemExit(EXIT_ERROR)

    return body


def _linear_ssl_context() -> ssl.SSLContext:
    """Build system trust plus the repository's corporate CA environment."""

    try:
        context = ssl.create_default_context()
        cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get(
            "REQUESTS_CA_BUNDLE"
        )
        capath = os.environ.get("SSL_CERT_DIR")
        if cafile or capath:
            context.load_verify_locations(cafile=cafile or None, capath=capath or None)
        return context
    except (OSError, ssl.SSLError) as exc:
        raise httpx.TransportError("TLS trust configuration is unavailable") from exc


def _resolved_proxy_addresses(host: str, port: int) -> frozenset[str]:
    """Resolve a configured proxy to one stable, non-empty address set."""

    try:
        resolved = socket.getaddrinfo(host, port)
        parsed = frozenset(ipaddress.ip_address(item[4][0]) for item in resolved)
    except (IndexError, OSError, TypeError, ValueError) as exc:
        raise httpx.TransportError("HTTPS proxy resolution failed") from exc
    if not parsed or any(
        address.is_unspecified
        or address.is_link_local
        # A proxy may legitimately be private, loopback, or multicast on a
        # corporate network. The IPv6 metadata endpoint is unique-local, so
        # rejecting its category would over-reject legitimate proxy hops.
        # GCP and Azure use the IPv4 IMDS address below; Alibaba uses its own
        # explicit IPv4 address. The shared 100.64.0.0/10 range stays allowed.
        or str(address) in {"169.254.169.254", "100.100.100.200", "fd00:ec2::254"}
        for address in parsed
    ):
        raise httpx.TransportError("HTTPS proxy resolution failed")
    return frozenset(str(address) for address in parsed)


def _https_proxy_settings(
    destination_host: str,
) -> tuple[str | None, tuple[str, int, frozenset[str]] | None]:
    """Honor HTTPS_PROXY/NO_PROXY and pin the configured proxy socket."""

    if proxy_bypass(destination_host):
        return None, None
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy_url:
        return None, None
    parsed = urlparse(proxy_url)
    default_ports = {"http": 80, "https": 443, "socks5": 1080, "socks5h": 1080}
    scheme = parsed.scheme.lower()
    if scheme not in default_ports:
        raise httpx.TransportError("HTTPS proxy configuration is unsupported")
    try:
        port = parsed.port or default_ports[scheme]
    except (KeyError, ValueError) as exc:
        raise httpx.TransportError("HTTPS proxy configuration is unsupported") from exc
    if (
        not parsed.hostname
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise httpx.TransportError("HTTPS proxy configuration is unsupported")
    host = parsed.hostname.rstrip(".").lower()
    return proxy_url, (host, port, _resolved_proxy_addresses(host, port))


class _PinnedSyncNetworkBackend:
    """httpcore backend that refuses proxy DNS changes at connect time."""

    def __init__(self, proxy_pin: tuple[str, int, frozenset[str]]) -> None:
        import httpcore  # noqa: PLC0415 — only pinned Linear requests need it

        self._proxy_pin = proxy_pin
        self._backend = httpcore.SyncBackend()

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[tuple[int, int, int | bytes]] | None = None,
    ) -> Any:
        proxy_host, proxy_port, expected_addresses = self._proxy_pin
        if host.rstrip(".").lower() != proxy_host or port != proxy_port:
            raise httpx.TransportError("HTTPS proxy connection escaped its pin")
        addresses = _resolved_proxy_addresses(host, port)
        if addresses != expected_addresses:
            raise httpx.TransportError("HTTPS proxy address changed before connect")
        address = sorted(addresses, key=lambda value: (":" in value, value))[0]
        return self._backend.connect_tcp(
            address, port, timeout, local_address, socket_options
        )

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[tuple[int, int, int | bytes]] | None = None,
    ) -> Any:
        return self._backend.connect_unix_socket(path, timeout, socket_options)

    def sleep(self, seconds: float) -> None:
        self._backend.sleep(seconds)


def _pinned_transport(destination: Any) -> httpx.HTTPTransport:
    """Build a corporate-network-aware transport with a pinned proxy socket."""

    proxy_url, proxy_pin = _https_proxy_settings(destination.host)
    try:
        transport = httpx.HTTPTransport(
            verify=_linear_ssl_context(),
            retries=0,
            proxy=proxy_url,
            trust_env=False,
        )
    except (ImportError, OSError, ValueError) as exc:
        raise httpx.TransportError("HTTPS proxy configuration is unavailable") from exc
    if proxy_pin is not None:
        transport._pool._network_backend = _PinnedSyncNetworkBackend(  # type: ignore[attr-defined]  # noqa: SLF001
            proxy_pin
        )
    return transport


def _bounded_post(
    url: str,
    *,
    json_body: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    pinned_destination: object | None = None,
) -> httpx.Response:
    """Stream one response and stop before the fixed profile byte cap."""
    request_url = url
    request_headers = dict(headers)
    extensions: dict[str, object] | None = None
    if pinned_destination is not None:
        addresses = tuple(pinned_destination.addresses)
        if not addresses:
            raise httpx.TransportError("pinned destination has no validated address")
        address = sorted(addresses, key=lambda value: (":" in value, value))[0]
        host_for_url = f"[{address}]" if ":" in address else address
        request_url = f"https://{host_for_url}:{pinned_destination.port}/graphql"
        request_headers["Host"] = pinned_destination.host
        extensions = {"sni_hostname": pinned_destination.host}
    with contextlib.ExitStack() as stack:
        if pinned_destination is None:
            response_context = httpx.stream(
                "POST",
                request_url,
                json=json_body,
                headers=request_headers,
                timeout=timeout,
                follow_redirects=False,
                verify=_linear_ssl_context(),
                trust_env=True,
            )
        else:
            client = stack.enter_context(
                httpx.Client(
                    timeout=timeout,
                    transport=_pinned_transport(pinned_destination),
                    trust_env=False,
                )
            )
            response_context = client.stream(
                "POST",
                request_url,
                json=json_body,
                headers=request_headers,
                follow_redirects=False,
                extensions=extensions,
            )
        response = stack.enter_context(response_context)
        content = bytearray()
        for chunk in response.iter_bytes():
            if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                sys.stderr.write(
                    "error: Linear response exceeded the 2 MiB profile budget\n"
                )
                raise SystemExit(EXIT_ERROR)
            content.extend(chunk)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=bytes(content),
            request=response.request,
            extensions=response.extensions,
        )


def _graphql_with_retry(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    url: str = GRAPHQL_URL,
) -> dict[str, Any]:
    """Call _graphql_request and apply exactly one Retry-After retry on 429."""
    result = _graphql_request(api_key, query, variables, url=url)

    # Check if the raw httpx.Response came back (429 path)
    if isinstance(result, httpx.Response) and result.status_code == 429:
        try:
            requested_delay = max(0, int(result.headers.get("Retry-After", "1")))
        except ValueError:
            requested_delay = RETRY_BACKOFF_SECONDS[0]
        retry_after = min(RETRY_BACKOFF_SECONDS[0], requested_delay)
        log.debug("429 rate-limited; sleeping %s s (Retry-After)", retry_after)
        time.sleep(retry_after)
        # Second attempt — if it 429s again, surface as error
        result2 = _graphql_request(api_key, query, variables, url=url)
        if isinstance(result2, httpx.Response) and result2.status_code == 429:
            sys.stderr.write("error: rate limited by Linear twice in a row; try again later.\n")
            raise SystemExit(EXIT_ERROR)
        return result2

    return result


class LinearRefreshProcessor:
    """Configured Linear refresh/write-back edge using the shared lifecycle."""

    def __init__(
        self,
        *,
        refresh_runtime: ModuleType | None = None,
        api_key_loader: Callable[[], str] = _load_api_key,
        graphql_transport: Callable[..., dict[str, Any]] | None = None,
        resolver: Callable[[str], Iterable[str]] | None = None,
        receipt_store: object | None = None,
    ) -> None:
        self._refresh = refresh_runtime or _load_refresh_runtime()
        self._profile = load_refresh_profile()
        self._api_key_loader = api_key_loader
        self._graphql_transport = graphql_transport or self._default_transport
        self._resolver = resolver
        self._receipt_store = receipt_store

    def write(
        self,
        *,
        action: str,
        target: str,
        artifact_path: str,
        source_revision: str,
        policy: object,
        confirmation: object | None,
        now: datetime | None = None,
        body: str | None = None,
        url: str | None = None,
        status: str | None = None,
    ) -> LinearWriteBackResult:
        """Execute one confirmed Linear mutation with fakeable transport."""

        if action not in set(self._profile["capabilities"]) - {"acquire"}:
            return LinearWriteBackResult("unsupported_capability", action, target=target)
        receipt_store = self._receipt_store
        if not self._refresh.is_remote_receipt_store(receipt_store):
            return LinearWriteBackResult("receipt_store_required", action, target=target)
        if receipt_store.artifact_path != artifact_path:
            return LinearWriteBackResult("receipt_store_mismatch", action, target=target)
        payload = self._payload_for_action(
            action=action,
            target=target,
            body=body,
            url=url,
            status=status,
        )
        if payload is None:
            return LinearWriteBackResult("invalid_remote_payload", action, target=target)
        try:
            pinned = self._validate_destination()
            payload_digest = self._refresh.canonical_payload_digest(payload)
            binding = self._refresh.ConfirmationBinding(
                artifact_path=artifact_path,
                source_revision=source_revision,
                profile_id=self._profile["id"],
                profile_version=self._profile["version"],
                destination=f"{pinned.scheme}://{pinned.host}:{pinned.port}",
                action=action,
                target=target,
                payload_digest=payload_digest,
            )
            if confirmation is None:
                raise self._refresh.RefreshRefusal("confirmation_required")
            receipt = self._refresh.consume_remote_confirmation(
                confirmation=confirmation,
                expected_binding=binding,
                policy=policy,
                used_confirmation_ids=receipt_store.confirmation_ids(),
                now=now or datetime.now(UTC),
            )
        except self._refresh.RefreshRefusal as exc:
            return LinearWriteBackResult(str(exc), action, target=target)
        try:
            receipt_store.record(receipt)
        except Exception:
            return LinearWriteBackResult(
                "pending_receipt_failed",
                action,
                target=target,
                payload_digest=payload_digest,
                transport_calls=0,
            )

        transport_called = False
        try:
            api_key = self._api_key_loader()
            query, variables, result_key = self._operation_for_action(action, payload)
            transport_called = True
            response = self._graphql_transport(
                api_key=api_key,
                query=query,
                variables=variables,
                url=GRAPHQL_URL,
                pinned_destination=pinned,
            )
            if response.get("data", {}).get(result_key, {}).get("success") is not True:
                raise RuntimeError("remote action was not acknowledged")
        except (SystemExit, Exception):
            failed_receipt = replace(receipt, status="failed")
            try:
                receipt_store.record(failed_receipt)
                failed = dict(failed_receipt.__dict__)
                code = "remote_action_failed"
            except Exception:
                failed = dict(receipt.__dict__)
                code = "receipt_update_failed"
            return LinearWriteBackResult(
                code,
                action,
                target=target,
                payload_digest=payload_digest,
                transport_calls=int(transport_called),
                receipt=failed,
            )
        succeeded_receipt = replace(receipt, status="succeeded")
        succeeded = dict(succeeded_receipt.__dict__)
        try:
            receipt_store.record(succeeded_receipt)
        except Exception:
            return LinearWriteBackResult(
                "receipt_update_failed",
                action,
                target=target,
                payload_digest=payload_digest,
                transport_calls=1,
                receipt={**receipt.__dict__, "status": "pending"},
            )
        return LinearWriteBackResult(
            "remote_action_succeeded",
            action,
            target=target,
            payload_digest=payload_digest,
            transport_calls=1,
            receipt=succeeded,
        )

    def _validate_destination(self) -> object:
        destination = self._profile["destination"]
        policy = self._refresh.DestinationPolicy(
            schemes=frozenset({destination["scheme"]}),
            hosts=frozenset({destination["host"]}),
            ports=frozenset({destination["port"]}),
            allow_redirects=destination["redirects"],
            credentials_attached=True,
        )
        kwargs: dict[str, object] = {"policy": policy}
        if self._resolver is not None:
            kwargs["resolver"] = self._resolver
        return self._refresh.validate_destination(
            f"{destination['scheme']}://{destination['host']}:{destination['port']}", **kwargs
        )

    @staticmethod
    def _payload_for_action(
        *,
        action: str,
        target: str,
        body: str | None,
        url: str | None,
        status: str | None,
    ) -> dict[str, object] | None:
        if not target:
            return None
        if action == "comment" and body:
            return {"issue_id": target, "body": body}
        if (
            action in {"trace-link", "pull-request-link"}
            and _trusted_https_url(url)
        ):
            title = "Pull request" if action == "pull-request-link" else "Trace link"
            return {"issue_id": target, "url": url, "title": title}
        if action == "display-status" and status:
            return {"issue_id": target, "state_id": status}
        if action == "closure" and status:
            return {"issue_id": target, "state_id": status}
        return None

    @staticmethod
    def _operation_for_action(
        action: str, payload: dict[str, object]
    ) -> tuple[str, dict[str, object], str]:
        if action == "comment":
            return (
                _COMMENT_CREATE_MUTATION,
                {"input": {"issueId": payload["issue_id"], "body": payload["body"]}},
                "commentCreate",
            )
        if action in {"trace-link", "pull-request-link"}:
            return (
                _ATTACHMENT_CREATE_MUTATION,
                {
                    "input": {
                        "issueId": payload["issue_id"],
                        "url": payload["url"],
                        "title": payload["title"],
                    }
                },
                "attachmentCreate",
            )
        return (
            _ISSUE_UPDATE_MUTATION,
            {"id": payload["issue_id"], "input": {"stateId": payload["state_id"]}},
            "issueUpdate",
        )

    @staticmethod
    def _default_transport(
        *,
        api_key: str,
        query: str,
        variables: dict[str, Any],
        url: str,
        pinned_destination: object,
    ) -> dict[str, Any]:
        return _graphql_request(
            api_key,
            query,
            variables,
            url=url,
            pinned_destination=pinned_destination,
        )


# ---------------------------------------------------------------------------
# GraphQL queries
# ---------------------------------------------------------------------------

_VIEWER_QUERY = """
{ viewer { id name email } }
"""

_GET_ISSUE_QUERY = """
query GetIssueByIdentifier($identifier: String!) {
  issues(filter: { identifier: { eq: $identifier } }) {
    nodes {
      id
      identifier
      updatedAt
      title
      description
      children {
        nodes {
          identifier
          updatedAt
          title
        }
      }
      project {
        id
        name
        url
      }
    }
  }
}
"""

_GET_PROJECT_QUERY = """
query GetProject($id: String!, $first: Int!, $cursor: String) {
  project(id: $id) {
    id
    name
    updatedAt
    issues(first: $first, after: $cursor) {
      nodes {
        identifier
        updatedAt
        title
        description
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def cmd_check(args: argparse.Namespace, api_key: str) -> None:
    data = _graphql_with_retry(api_key, _VIEWER_QUERY)
    viewer = data.get("data", {}).get("viewer", {})
    _write_output({"authenticated": True, "viewer": viewer}, args)


def cmd_get_issue(args: argparse.Namespace, api_key: str) -> None:
    data = _graphql_with_retry(api_key, _GET_ISSUE_QUERY, {"identifier": args.identifier})
    nodes = data.get("data", {}).get("issues", {}).get("nodes", [])
    if not nodes:
        sys.stderr.write(f"error: issue {args.identifier!r} not found — check the identifier.\n")
        raise SystemExit(EXIT_ERROR)
    _write_output(nodes[0], args)


def cmd_get_project(args: argparse.Namespace, api_key: str) -> None:
    result = _get_project_pages(api_key, args.project_id)
    _write_output(result, args)


def _get_project_pages(
    api_key: str,
    project_id: str,
    *,
    url: str = GRAPHQL_URL,
) -> dict[str, Any]:
    """Fetch project issues up to MAX_PAGES pages; return combined result dict."""
    all_issues: list[dict[str, Any]] = []
    cursor: str | None = None
    project_meta: dict[str, Any] = {}

    complete = True
    for page_index in range(MAX_PAGES):
        variables: dict[str, Any] = {
            "id": project_id,
            "first": PAGE_SIZE,
            "cursor": cursor,
        }
        data = _graphql_with_retry(api_key, _GET_PROJECT_QUERY, variables, url=url)
        project_node = data.get("data", {}).get("project")
        if project_node is None:
            sys.stderr.write(f"error: project {project_id!r} not found or inaccessible.\n")
            raise SystemExit(EXIT_ERROR)

        if not project_meta:
            project_meta = {
                "id": project_node.get("id"),
                "name": project_node.get("name"),
                "updatedAt": project_node.get("updatedAt"),
            }

        issues_conn = project_node.get("issues", {})
        all_issues.extend(issues_conn.get("nodes", []))
        page_info = issues_conn.get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break
        if page_index == MAX_PAGES - 1:
            complete = False
            break
        cursor = page_info.get("endCursor")

    return {
        **project_meta,
        "issues": {"nodes": all_issues},
        "intake_budget": {
            "complete": complete,
            "result": "complete" if complete else "marked-incomplete",
        },
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _write_output(data: Any, args: argparse.Namespace) -> None:
    fmt = getattr(args, "format", "json")
    output_path = getattr(args, "output", None)

    if fmt == "jsonl":
        items = data if isinstance(data, list) else [data]
        text = (
            "\n".join(json.dumps(item, ensure_ascii=False, allow_nan=False) for item in items)
            + "\n"
        )
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"

    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        log.info("Written to %s", output_path)
    else:
        sys.stdout.write(text)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def _build_parser() -> _ScrubbingArgumentParser:
    p = _ScrubbingArgumentParser(
        prog=_display_program(),
        description="Linear GraphQL API CLI. API key is resolved via credbroker.",
    )
    p.add_argument("--format", choices=["json", "jsonl"], default="json")
    p.add_argument("--output", metavar="FILE")
    p.add_argument("--verbose", action="store_true")

    sub = p.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("check", help="Verify credentials and reachability.")

    get_issue = sub.add_parser("get-issue", help="Fetch one issue by identifier.")
    get_issue.add_argument("identifier", help="Issue identifier e.g. ENG-123")

    get_project = sub.add_parser("get-project", help="Fetch a project's issues.")
    get_project.add_argument("project_id", help="Project UUID")

    return p


def main(argv: list[str] | None = None) -> None:
    _reject_token_on_cli(argv if argv is not None else sys.argv[1:])
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    api_key = _load_api_key()

    dispatch = {
        "check": cmd_check,
        "get-issue": cmd_get_issue,
        "get-project": cmd_get_project,
    }
    handler = dispatch.get(args.subcommand)
    if handler is None:
        parser.error(f"unknown subcommand: {args.subcommand!r}")

    try:
        handler(args, api_key)
    except SystemExit:
        raise
    except Exception as exc:
        log.debug("unexpected error", exc_info=True)
        sys.stderr.write(f"error: unexpected — {exc}\n")
        raise SystemExit(EXIT_ERROR) from exc


if __name__ == "__main__":
    main()
