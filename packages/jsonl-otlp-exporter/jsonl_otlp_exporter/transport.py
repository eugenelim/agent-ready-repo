"""Where a request may go, how often, and how long it may take.

The destination rules are the security boundary. `https` is accepted anywhere
with the chain and hostname verified; `http` is accepted only when every address
the host resolves to is a loopback address, and the request is then issued to one
of *those verified addresses* rather than to the hostname again. Re-resolving at
connect time reopens exactly the hole the check closed, because the second answer
need not match the first.

Everything with a clock in it takes one by injection, so the bounds are tested
deterministically instead of by waiting.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import ssl
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
from urllib.parse import urlsplit

__all__ = [
    "Destination",
    "DestinationRefused",
    "SendOutcome",
    "MAX_ATTEMPTS_PER_RUN",
    "MAX_BODY_BYTES",
    "MAX_RECORDS_PER_REQUEST",
    "MAX_RESPONSE_BYTES",
    "MAX_RETRY_AFTER_SECONDS",
    "REQUEST_TIMEOUT_SECONDS",
    "RUN_TIMEOUT_SECONDS",
    "batch_records",
    "render_endpoint",
    "resolve_destination",
    "send_batches",
]

MAX_RECORDS_PER_REQUEST = 512          # AC-0011
MAX_BODY_BYTES = 8 * 1024 * 1024       # AC-0019
MAX_RESPONSE_BYTES = 1024 * 1024       # AC-0041, plus the one byte that proves it
MAX_ATTEMPTS_PER_RUN = 3               # AC-0010
MAX_RETRY_AFTER_SECONDS = 30           # AC-0009
REQUEST_TIMEOUT_SECONDS = 30           # AC-0040
RUN_TIMEOUT_SECONDS = 120              # AC-0055

_RETRYABLE_STATUSES = frozenset({429, 503})
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class DestinationRefused(Exception):
    """The endpoint may not be used. Nothing is sent and the run exits 1."""


def render_endpoint(url: str) -> str:
    """Render an endpoint for a human, safely. AC-0045.

    One representation, used by every message: no user-info, no query, no
    fragment, and no control character. Credentials reach logs by being printed
    in an error, and a control character in a hostname can rewrite the line
    around it.
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        port = parts.port
    except ValueError:
        # This function is called precisely when the endpoint is wrong, so it
        # must never raise: `urlsplit` rejects a malformed authority (a stray
        # "[" reads as an IPv6 literal), and a renderer that throws there turns
        # a clean refusal into an unhandled exception. Fall back to stripping
        # the dangerous parts off the raw string.
        rendered = url.split("?", 1)[0].split("#", 1)[0]
        if "@" in rendered:
            scheme, _, rest = rendered.partition("://")
            rendered = f"{scheme}://{rest.partition('@')[2]}" if rest else rendered
        return _strip_control(rendered)
    if port:
        host = f"{host}:{port}"
    return _strip_control(f"{parts.scheme}://{host}{parts.path}")


def _strip_control(text: str) -> str:
    """Drop C0 and C1 control characters.

    A newline or an ANSI escape inside a hostname rewrites the log line around
    it, so a message naming an attacker-influenced endpoint can forge the lines
    next to it.
    """
    return "".join(ch for ch in text if not (ord(ch) < 0x20 or 0x7F <= ord(ch) <= 0x9F))


@dataclass(frozen=True)
class Destination:
    """A checked endpoint, plus the address the request will actually go to."""

    url: str
    scheme: str
    host: str
    port: int
    path: str
    connect_host: str

    @property
    def safe_url(self) -> str:
        return render_endpoint(self.url)


def resolve_destination(url: str, resolver: Callable[..., Sequence] | None = None) -> Destination:
    """Check the endpoint and pin the address the request will be issued to."""
    resolver = resolver or socket.getaddrinfo
    try:
        parts = urlsplit(url)
        _ = parts.port  # also raises on a non-numeric port
    except ValueError as exc:
        # `urlsplit` interpolates the ORIGINAL netloc into its message, so
        # letting this escape puts an unsanitised endpoint -- control characters
        # and all -- on stderr, which is exactly what AC-0045 forbids.
        # `render_endpoint` handles its own ValueError and cannot re-raise.
        raise DestinationRefused(
            f"endpoint is not a usable URL: {render_endpoint(url)} ({type(exc).__name__})"
        ) from exc

    if parts.scheme not in ("https", "http"):
        raise DestinationRefused(
            f"endpoint scheme {parts.scheme!r} is not https or http: {render_endpoint(url)}"
        )
    if parts.username or parts.password or "@" in (parts.netloc or ""):
        # Rendered without the user-info, so refusing a credentialed endpoint
        # does not print the credential.
        raise DestinationRefused(f"endpoint carries user-info: {render_endpoint(url)}")
    if not parts.hostname:
        raise DestinationRefused(f"endpoint names no host: {render_endpoint(url)}")

    port = parts.port or (443 if parts.scheme == "https" else 80)
    path = parts.path or "/"

    if parts.scheme == "https":
        # Accepted at any host; the chain and hostname are verified at connect.
        return Destination(url, "https", parts.hostname, port, path, parts.hostname)

    infos = resolver(parts.hostname, port, 0, socket.SOCK_STREAM)
    addresses = [info[4][0] for info in infos]
    if not addresses:
        raise DestinationRefused(f"endpoint host does not resolve: {render_endpoint(url)}")
    for address in addresses:
        if not ipaddress.ip_address(address).is_loopback:
            raise DestinationRefused(
                f"plaintext endpoint resolves to the non-loopback address {address}: "
                f"{render_endpoint(url)}"
            )
    # Pin the first verified address. The connection is made to THIS, never to
    # the hostname again -- a second resolution could answer differently.
    return Destination(url, "http", parts.hostname, port, path, addresses[0])


def batch_records(
    records: Iterable[Mapping[str, Any]],
    encode: Callable[[Sequence[Mapping[str, Any]]], bytes],
    max_records: int = MAX_RECORDS_PER_REQUEST,
    max_bytes: int = MAX_BODY_BYTES,
    on_oversize: Callable[[int], None] | None = None,
) -> Iterator[tuple[list[Mapping[str, Any]], bytes]]:
    """Yield (records, encoded body) pairs, each inside both bounds.

    The byte bound is measured on the *encoded* body, because encoding expands
    the payload and an input-side estimate cannot establish an output-side limit.
    An over-large batch is split rather than dropped: a sender that discards the
    overflow loses records silently, which is worse than sending two requests.

    Records are consumed from an iterator and never accumulated beyond one
    batch, which is what makes the residency bound true by construction.
    """
    pending: list[Mapping[str, Any]] = []
    for record in records:
        pending.append(record)
        if len(pending) < max_records:
            continue
        yield from _emit(pending, encode, max_bytes, on_oversize)
        pending = []
    if pending:
        yield from _emit(pending, encode, max_bytes, on_oversize)


def _emit(batch, encode, max_bytes, on_oversize=None):
    body = encode(batch)
    if len(body) <= max_bytes:
        yield list(batch), body
        return
    if len(batch) == 1:
        # A single record that alone exceeds the ceiling cannot be split. AC-0019
        # states the ceiling unconditionally -- "a request body is at most 8 MiB
        # measured on the encoded bytes about to be sent" -- so it is not sent.
        # It is reported rather than dropped in silence, because losing a record
        # without saying so is the worse failure.
        #
        # The criterion names the ceiling but no replacement disposition; this
        # reading is recorded for the owner in the verification ledger.
        if on_oversize is not None:
            on_oversize(len(body))
        return
    middle = len(batch) // 2
    yield from _emit(batch[:middle], encode, max_bytes, on_oversize)
    yield from _emit(batch[middle:], encode, max_bytes, on_oversize)


@dataclass
class SendOutcome:
    status: int = 0
    attempts: int = 0
    requests: int = 0
    rejected_records: int = 0
    reason: str = ""
    partial_success: bool = False


def _retry_after_seconds(raw: str | None) -> int:
    """AC-0009. Absent, negative or unparseable is 0, and the cap is 30."""
    if raw is None:
        return 0
    try:
        seconds = int(str(raw).strip())
    except (TypeError, ValueError):
        return 0
    if seconds < 0:
        return 0
    return min(seconds, MAX_RETRY_AFTER_SECONDS)


def send_batches(
    batches: Iterable[tuple[list[Mapping[str, Any]], bytes]],
    destination: Destination,
    connection_factory: Callable[..., Any],
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    stream=None,
    best_effort: bool = False,
    run_started: float | None = None,
) -> SendOutcome:
    """POST each batch, honouring the attempt, retry and time bounds.

    The run clock starts here, at the first destination resolution, and every
    later deadline is measured against it on a monotonic clock so a wall-clock
    step cannot extend or collapse a bound.
    """
    out = SendOutcome()
    stream = stream if stream is not None else sys.stderr
    # AC-0055 anchors the run bound at the first destination resolution, which
    # already happened by the time this is called. Defaulting to now would
    # restart the clock and let a run that spent 119 seconds resolving take
    # another 120 sending.
    run_started = clock() if run_started is None else run_started
    run_deadline = run_started + RUN_TIMEOUT_SECONDS

    for records, body in batches:
        while True:
            if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                out.status = out.status or 1
                out.reason = out.reason or "attempt budget exhausted"
                return out
            if clock() >= run_deadline:
                out.status = out.status or 1
                out.reason = out.reason or "run time bound reached"
                return out

            # The per-request timeout covers resolution, connection, write and
            # read, and is clamped so it can never outlive the run bound -- a
            # request begun at second 119 must not run to second 149.
            remaining = max(0.0, run_deadline - clock())
            timeout = min(float(REQUEST_TIMEOUT_SECONDS), remaining)

            out.attempts += 1
            try:
                status, headers, payload = _post(
                    destination, body, connection_factory, timeout,
                    deadline=min(clock() + timeout, run_deadline), clock=clock,
                )
            except Exception as exc:  # noqa: BLE001 - any transport failure is one outcome
                print(
                    f"jsonl-otlp-export: request to {destination.safe_url} failed: {exc}",
                    file=stream,
                )
                if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                    out.status = 1
                    out.reason = "attempt budget exhausted"
                    return out
                continue

            received_at = clock()

            if status in _REDIRECT_STATUSES:
                location = headers.get("location", "")
                print(
                    f"jsonl-otlp-export: refusing a redirect from "
                    f"{destination.safe_url} to {render_endpoint(location)}",
                    file=stream,
                )
                out.status = 1
                out.reason = "redirect refused"
                return out

            if status in _RETRYABLE_STATUSES:
                delay = _retry_after_seconds(headers.get("retry-after"))
                if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                    out.status = 1
                    out.reason = "attempt budget exhausted"
                    return out
                # Measured from when THIS response was received, not from when
                # the request was issued: the two differ by the request's own
                # duration, and the server's instruction is about now.
                wake = received_at + delay
                if wake >= run_deadline:
                    out.status = 1
                    out.reason = "retry would exceed the run bound"
                    return out
                sleep(max(0.0, wake - clock()))
                continue

            if 200 <= status < 300:
                out.requests += 1
                present, rejected = _partial_success(payload)
                if present:
                    out.rejected_records += rejected
                    out.partial_success = True
                    print(
                        f"jsonl-otlp-export: the receiver reported a partial success "
                        f"rejecting {rejected} record(s) ({destination.safe_url})",
                        file=stream,
                    )
                    # No retry. A partialSuccess names records the receiver
                    # refused on their content; sending them again produces the
                    # same refusal and doubles the traffic.
                    out.status = 1
                    out.reason = "partial success"
                break

            print(
                f"jsonl-otlp-export: {destination.safe_url} returned HTTP {status}",
                file=stream,
            )
            out.status = 1
            out.reason = f"http {status}"
            if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                out.reason = "attempt budget exhausted"
                return out
            break

    if best_effort and not out.partial_success:
        # AC-0012 scopes the allowance to "send failure after the retry budget",
        # and the flag's own help says "even when sending fails". A partial
        # success is not a send failure: the request succeeded with HTTP 200 and
        # the receiver refused records on their content. AC-0054 states its exit
        # obligation unconditionally, and AC-0055 shows the spec writes an
        # explicit best-effort carve-out when it means one.
        out.status = 0
    return out


def _partial_success(payload: bytes) -> tuple[bool, int]:
    """Return (a non-empty partialSuccess was present, rejected-record count).

    The criteria key on the OBJECT being non-empty, not on the count being
    positive: a body carrying `{"rejectedLogRecords": 0, "errorMessage": "..."}`
    is the receiver telling you something went wrong, and reading only the count
    reports success for it.
    """
    try:
        parsed = json.loads(payload.decode("utf-8")) if payload else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, 0
    partial = (parsed or {}).get("partialSuccess")
    if not isinstance(partial, dict) or not partial:
        return False, 0
    try:
        return True, int(partial.get("rejectedLogRecords", 0) or 0)
    except (TypeError, ValueError):
        return True, 0


def _post(destination: Destination, body: bytes, connection_factory, timeout: float,
          deadline: float | None = None, clock: Callable[[], float] = time.monotonic):
    """One request, abandoned at `deadline` however slowly it makes progress.

    A socket timeout alone is not enough: it bounds each blocking operation, so a
    receiver returning one byte every 29 seconds keeps every `recv` inside a
    30-second timeout while the request as a whole runs without limit. The
    response is read in bounded chunks with the monotonic deadline checked
    between them.
    """
    context = ssl.create_default_context() if destination.scheme == "https" else None
    connection = connection_factory(
        destination.scheme,
        destination.connect_host,
        destination.port,
        timeout,
        context,
    )
    try:
        connection.request(
            "POST",
            destination.path,
            body=body,
            headers={
                "Content-Type": "application/json",
                # The Host header keeps virtual hosting correct even though the
                # connection was made to a pinned address.
                "Host": destination.host
                if destination.port in (80, 443)
                else f"{destination.host}:{destination.port}",
                "Content-Length": str(len(body)),
            },
        )
        response = connection.getresponse()
        # One byte past the ceiling is read on purpose: reading exactly the
        # ceiling cannot distinguish "at the limit" from "over it".
        remaining = MAX_RESPONSE_BYTES + 1
        chunks: list[bytes] = []
        while remaining > 0:
            if deadline is not None and clock() >= deadline:
                raise DestinationRefused(
                    "request abandoned at its deadline while reading the response"
                )
            chunk = response.read(min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise DestinationRefused(
                f"response body exceeds {MAX_RESPONSE_BYTES} bytes; refused without decoding"
            )
        # Lowercased keys: field names are case-insensitive per RFC 9110 and
        # HTTP/2 mandates lowercase, while `getheaders()` preserves exactly what
        # the server sent. A literal "Retry-After" lookup misses "retry-after"
        # and the backoff is silently ignored.
        headers = {name.lower(): value for name, value in response.getheaders()}
        return response.status, headers, payload
    finally:
        connection.close()
