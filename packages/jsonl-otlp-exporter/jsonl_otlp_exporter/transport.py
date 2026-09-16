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

import contextlib
import ipaddress
import json
import socket
import ssl
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
from urllib.parse import urlsplit

__all__ = [
    "IDLE",
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


class _Idle:
    """Yielded by the reader when it has caught up and is waiting for more."""


IDLE = _Idle()

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
            # RIGHTmost '@': a password may itself contain one, and splitting on
            # the first leaves a fragment of it in the rendered endpoint.
            rendered = f"{scheme}://{rest.rpartition('@')[2]}" if rest else rendered
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
    query: str = ""

    @property
    def target(self) -> str:
        """The request target: path plus query.

        AC-0003 requires a value from the logs-specific variable to be requested
        unmodified, and a query string is part of it -- a Collector behind a
        gateway may carry a tenant there. `render_endpoint` strips the query
        independently, so keeping it on the wire does not put it in a message.
        """
        return f"{self.path}?{self.query}" if self.query else self.path

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
        # Accepted at any host, with the chain and hostname verified at connect.
        #
        # The lookup is bounded here even though the address is NOT pinned. The
        # http branch pins its address because re-resolving would reopen the
        # loopback check (AC-0025); https must connect by hostname or TLS
        # verification has nothing to check against (AC-0024), so pinning is the
        # wrong trade. What this call buys is failing fast on a resolver that
        # never answers: during `connect` there is no socket yet, so the watchdog
        # has nothing to shut down and a stalled lookup would outrun both bounds.
        # The connect's own resolution then hits the OS cache this warmed.
        try:
            _resolve_bounded(resolver, parts.hostname, port, REQUEST_TIMEOUT_SECONDS)
        except DestinationRefused:
            raise
        except OSError as exc:
            # A host that does not resolve cannot be sent to. Refusing here gives
            # the operator the endpoint and the reason; letting `gaierror` escape
            # would surface as an unhandled failure instead.
            raise DestinationRefused(
                f"endpoint host does not resolve: {render_endpoint(url)}"
            ) from exc
        return Destination(url, "https", parts.hostname, port, path,
                           parts.hostname, parts.query)

    infos = _resolve_bounded(resolver, parts.hostname, port, REQUEST_TIMEOUT_SECONDS)
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
    return Destination(url, "http", parts.hostname, port, path,
                       addresses[0], parts.query)


def batch_records(
    # The sentinel is part of the accepted input, not an intruder: `records` is
    # the reader's iterator, which yields (IDLE, position) to say it has caught
    # up. It is filtered out below, so it never reaches a batch or the encoder.
    records: Iterable[tuple[Mapping[str, Any] | _Idle, int]],
    encode: Callable[[Sequence[Mapping[str, Any]]], bytes],
    max_records: int = MAX_RECORDS_PER_REQUEST,
    max_bytes: int = MAX_BODY_BYTES,
    on_oversize: Callable[[int], None] | None = None,
) -> Iterator[tuple[list[Mapping[str, Any]], bytes, int]]:
    """Yield (records, encoded body, end offset) triples, inside both bounds.

    Each triple carries the end offset of its own last line, not the parent
    batch's. That matters at exactly one place -- the split below -- because
    giving both halves the parent's offset would credit the second half when
    only the first was accepted, and the records in between would be lost.

    The byte bound is measured on the *encoded* body, because encoding expands
    the payload and an input-side estimate cannot establish an output-side limit.
    An over-large batch is split rather than dropped: a sender that discards the
    overflow loses records silently, which is worse than sending two requests.

    Records are consumed from an iterator and never accumulated beyond one
    batch, which is what makes the residency bound true by construction.
    """
    pending: list[Mapping[str, Any]] = []
    offsets: list[int] = []
    for record, position in records:
        # `isinstance`, not `is IDLE`: `_Idle` has exactly one instance, so the
        # two are equivalent here, and only this form narrows the union for a
        # type checker -- which is what lets `pending.append` below be checked
        # rather than merely asserted by the `continue`.
        if isinstance(record, _Idle):
            # The reader went quiet. Under bare `--follow` the iterator never
            # ends, so waiting for a full batch means an appended record is held
            # forever and AC-0021 is never satisfied. Flushing on idle sends what
            # is in hand without terminating the reader, and cannot breach the
            # record or byte ceilings because it only ever shrinks a batch.
            if pending:
                yield from _emit(pending, offsets, encode, max_bytes, on_oversize)
                pending, offsets = [], []
            continue
        pending.append(record)
        offsets.append(position)
        if len(pending) < max_records:
            continue
        yield from _emit(pending, offsets, encode, max_bytes, on_oversize)
        pending, offsets = [], []
    if pending:
        yield from _emit(pending, offsets, encode, max_bytes, on_oversize)


def _emit(batch, offsets, encode, max_bytes, on_oversize=None, diagnostics=True):
    body = encode(batch, diagnostics)
    if len(body) <= max_bytes:
        yield list(batch), body, offsets[-1]
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
    # The parent encode already fired every per-record callback for exactly
    # these records, so the halves must not fire them again -- double-counting
    # made "400 records affected" report as 800.
    middle = len(batch) // 2
    yield from _emit(batch[:middle], offsets[:middle], encode, max_bytes,
                     on_oversize, diagnostics=False)
    yield from _emit(batch[middle:], offsets[middle:], encode, max_bytes,
                     on_oversize, diagnostics=False)


@dataclass
class SendOutcome:
    status: int = 0
    attempts: int = 0
    requests: int = 0
    rejected_records: int = 0
    reason: str = ""
    partial_success: bool = False
    # The end offset of the last batch in the unbroken accepted run starting at
    # the first batch. NOT a high-water mark: this loop continues to the next
    # batch after a non-retryable status, so a high-water mark would credit a
    # later batch and lose the records of the one that failed.
    accepted_offset: int = 0
    all_accepted: bool = True


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
    batches: Iterable[tuple[list[Mapping[str, Any]], bytes, int]],
    destination: Destination,
    connection_factory: Callable[..., Any],
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    stream=None,
    best_effort: bool = False,
    run_started: float | None = None,
    for_seconds: int | None = None,
    first_read_at: Callable[[], float | None] | None = None,
    start_offset: int = 0,
) -> SendOutcome:
    """POST each batch, honouring the attempt, retry and time bounds.

    The run clock starts here, at the first destination resolution, and every
    later deadline is measured against it on a monotonic clock so a wall-clock
    step cannot extend or collapse a bound.
    """
    out = SendOutcome(accepted_offset=start_offset)
    stream = stream if stream is not None else sys.stderr
    # AC-0055 anchors the run bound at the first destination resolution, which
    # already happened by the time this is called. Defaulting to now would
    # restart the clock and let a run that spent 119 seconds resolving take
    # another 120 sending.
    run_started = clock() if run_started is None else run_started
    run_deadline = run_started + RUN_TIMEOUT_SECONDS

    def _deadline() -> float:
        """The effective deadline: the run bound, and `--for` if one is set.

        AC-0042 anchors `--for` at the instant the FIRST READ begins, not at the
        run's start. Anchoring it at `run_started` made a run whose destination
        resolution took two seconds exceed `--for 1` before a single record was
        pulled, so nothing was sent at all. The reader stamps its own first read
        and this asks for it, falling back to `run_started` until it exists.
        """
        if for_seconds is None:
            return run_deadline
        anchor = first_read_at() if first_read_at is not None else None
        return min(run_deadline, (run_started if anchor is None else anchor) + for_seconds)

    for _records, body, end_offset in batches:
        while True:
            if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                out.status = out.status or 1
                out.reason = out.reason or "attempt budget exhausted"
                out.all_accepted = False
                return out
            # ONE sample for both the bound check and the remaining budget. Two
            # readings can straddle the deadline, admitting an iteration at
            # 119.999 and then computing a zero timeout -- and a zero timeout is
            # not "expired" to `http.client`, it is non-blocking mode, so the
            # request is issued anyway and consumes one of the three attempts.
            now = clock()
            remaining = _deadline() - now
            if remaining <= 0:
                out.status = out.status or 1
                out.reason = out.reason or "run time bound reached"
                out.all_accepted = False
                return out

            # AC-0040 anchors the request bound at that request's own destination
            # resolution. The first request's resolution is the run's, so its
            # budget is measured from `run_started`, not from now -- otherwise a
            # 29-second resolution grants a fresh 30 seconds on top of it.
            request_anchor = run_started if out.attempts == 0 else now
            deadline = min(request_anchor + REQUEST_TIMEOUT_SECONDS, _deadline())
            timeout = max(0.0, deadline - now)
            if timeout <= 0:
                out.status = out.status or 1
                out.reason = out.reason or "request bound reached before issue"
                out.all_accepted = False
                return out

            out.attempts += 1
            try:
                status, headers, payload = _post(
                    destination, body, connection_factory, timeout,
                    deadline=deadline, clock=clock,
                )
            except Exception as exc:  # noqa: BLE001 - any transport failure is one outcome
                print(
                    f"jsonl-otlp-export: request to {destination.safe_url} failed: {exc}",
                    file=stream,
                )
                if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                    out.status = 1
                    out.reason = "attempt budget exhausted"
                    out.all_accepted = False
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
                out.all_accepted = False
                return out

            if status in _RETRYABLE_STATUSES:
                delay = _retry_after_seconds(headers.get("retry-after"))
                if out.attempts >= MAX_ATTEMPTS_PER_RUN:
                    out.status = 1
                    out.reason = "attempt budget exhausted"
                    out.all_accepted = False
                    return out
                # Measured from when THIS response was received, not from when
                # the request was issued: the two differ by the request's own
                # duration, and the server's instruction is about now.
                wake = received_at + delay
                if wake >= _deadline():
                    out.status = 1
                    out.reason = "retry would exceed the run bound"
                    out.all_accepted = False
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
                    out.all_accepted = False
                elif out.all_accepted:
                    # Only while the prefix is still unbroken. A batch accepted
                    # after an earlier refusal must not advance the offset past
                    # the records that refusal left unsent.
                    out.accepted_offset = end_offset
                break

            print(
                f"jsonl-otlp-export: {destination.safe_url} returned HTTP {status}",
                file=stream,
            )
            out.status = 1
            out.reason = f"http {status}"
            out.all_accepted = False
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


def _resolve_bounded(resolver, host, port, seconds: float):
    """Resolve `host`, giving up after `seconds`.

    Neither `socket.getaddrinfo` nor `socket.create_connection` accepts a
    timeout, and a resolver that never answers hangs the process -- which defeats
    AC-0040 and AC-0055 before either clock is ever consulted. The lookup runs on
    a daemon thread that the caller abandons; the thread cannot outlive the
    process, and abandoning it is strictly better than inheriting its stall.
    """
    outcome: dict = {}

    def _lookup():
        try:
            outcome["value"] = resolver(host, port, 0, socket.SOCK_STREAM)
        except BaseException as exc:  # noqa: BLE001 - re-raised on the caller's thread
            outcome["error"] = exc

    worker = threading.Thread(target=_lookup, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        raise DestinationRefused(
            f"destination resolution did not answer within {seconds:g}s"
        )
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


class _Watchdog:
    """Close the connection at an absolute deadline, whatever it is blocked on.

    Re-arming the socket timeout per phase is not enough and three separate
    findings said so from three directions: the connect and the header read each
    get the full timeout independently, `http.client`'s reader restarts the timer
    on every `readline`, and a `Connection: close` response sets
    `connection.sock = None` so there is nothing left to re-arm at all.

    Closing the connection from another thread makes whichever call is blocked
    raise, so one mechanism covers connect, write, header read and body read --
    rather than four patches that each cover one and miss the next.
    """

    def __init__(self, connection, seconds: float):
        self._timer = threading.Timer(max(0.0, seconds), self._abandon)
        self._timer.daemon = True
        self._connection = connection
        self._socket = None
        self.fired = False

    def attach(self, sock) -> None:
        """Retain the connected socket.

        Looking `connection.sock` up when the timer fires is too late: a
        `Connection: close` response makes `getresponse()` clear it while the
        response keeps reading through its own file object, so the watchdog would
        find nothing to shut down and closing alone does not wake a blocked
        reader. Retained here, the reference survives that.
        """
        self._socket = sock

    def _abandon(self):
        self.fired = True
        # `shutdown` FIRST, and that is the whole point. Closing a socket another
        # thread is blocked reading does not reliably wake it -- the descriptor
        # is duplicated into the response's file object, so the blocked `recv`
        # keeps waiting and the watchdog achieves nothing. `shutdown(SHUT_RDWR)`
        # tears the connection down underneath the reader and the call returns.
        # Measured: without this the request blocked for the full 120s socket
        # timeout despite a 1s deadline.
        sock = self._socket or getattr(self._connection, "sock", None)
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
        with contextlib.suppress(Exception):
            self._connection.close()

    def __enter__(self):
        self._timer.start()
        return self

    def __exit__(self, *exc_info):
        self._timer.cancel()
        return False


def _host_header(destination: Destination) -> str:
    """Build a valid Host authority, bracketing an IPv6 literal.

    `http.client` brackets correctly on its own, but only when it builds the
    header; passing an explicit `Host` key suppresses that path entirely, so the
    bracketing has to be done here or `::1` ships as `Host: ::1:4318`.
    """
    host = destination.host
    if ":" in host:
        host = f"[{host}]"
    if destination.port in (80, 443):
        return host
    return f"{host}:{destination.port}"


def _post(destination: Destination, body: bytes, connection_factory, timeout: float,
          deadline: float | None = None, clock: Callable[[], float] = time.monotonic):
    """One request, abandoned at `deadline` whatever it is blocked on.

    A socket timeout bounds each blocking operation, not the request: the connect
    and the header read each get the full timeout independently, and
    `http.client` restarts the timer on every `recv`, so a receiver trickling
    bytes keeps a single call blocked indefinitely. The watchdog closes the
    connection at the deadline instead, which covers connect, write, header read
    and body read with one mechanism.
    """
    context = ssl.create_default_context() if destination.scheme == "https" else None
    connection = connection_factory(
        destination.scheme,
        destination.connect_host,
        destination.port,
        timeout,
        context,
    )
    watchdog = (
        _Watchdog(connection, deadline - clock())
        if deadline is not None
        else contextlib.nullcontext()
    )
    try:
        with watchdog:
            return _exchange(destination, body, connection, deadline, clock, watchdog)
    except OSError as exc:
        if getattr(watchdog, "fired", False):
            raise DestinationRefused(
                "request abandoned at its deadline"
            ) from exc
        raise
    finally:
        connection.close()


def _exchange(destination, body, connection, deadline, clock, watchdog=None):
    """The exchange itself. The caller owns the deadline and the connection."""
    connection.request(
        "POST",
        destination.target,
        body=body,
        headers={
            "Content-Type": "application/json",
            # The Host header keeps virtual hosting correct even though the
            # connection was made to a pinned address.
            "Host": _host_header(destination),
            "Content-Length": str(len(body)),
        },
    )
    # The connect has happened, so the socket exists now. Hand it to the
    # watchdog BEFORE reading the response: `getresponse()` clears
    # `connection.sock` for a `Connection: close` reply while the response keeps
    # reading through its own file object.
    if watchdog is not None and hasattr(watchdog, "attach"):
        watchdog.attach(getattr(connection, "sock", None))
    response = connection.getresponse()
    # One byte past the ceiling is read on purpose: reading exactly the
    # ceiling cannot distinguish "at the limit" from "over it".
    remaining = MAX_RESPONSE_BYTES + 1
    chunks: list[bytes] = []
    socket_ = getattr(connection, "sock", None)
    while remaining > 0:
        if deadline is not None:
            left = deadline - clock()
            if left <= 0:
                raise DestinationRefused(
                    "request abandoned at its deadline while reading the response"
                )
            # Re-arm the socket to what is LEFT, not to the per-operation
            # timeout. `HTTPResponse.read(n)` loops over `recv` until it has
            # n bytes, and each `recv` restarts the timer -- so a receiver
            # trickling one byte just inside the timeout keeps a single call
            # blocking forever. Bounding each call by the remaining budget
            # caps the overrun at one chunk.
            if socket_ is not None:
                with contextlib.suppress(OSError):
                    socket_.settimeout(left)
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
