"""T5 — destination policy, retry, batching and the time bounds.

Covers AC-0008, AC-0009, AC-0010, AC-0011, AC-0019, AC-0024, AC-0025, AC-0026,
AC-0027, AC-0028, AC-0036, AC-0040, AC-0041, AC-0044, AC-0045, AC-0054, AC-0055,
AC-0063.

No real sockets and no real waiting: connections and the clock are injected.
"""

from __future__ import annotations

import io
import json
import socket
import time

import pytest

from jsonl_otlp_exporter import transport as tp


def _addrinfo(*addresses):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, 4318)) for a in addresses]


class _FakeResponse:
    def __init__(self, status=200, headers=None, payload=b"{}"):
        self.status = status
        self._headers = headers or {}
        self._payload = payload

    def getheaders(self):
        return list(self._headers.items())

    def read(self, amount):
        # A real HTTPResponse CONSUMES: successive reads advance and eventually
        # return b"". A fake that re-returns the whole payload lets a chunked
        # reader loop forever, which is a defect in the double, not the caller.
        chunk = self._payload[:amount]
        self._payload = self._payload[amount:]
        return chunk


class _FakeConnection:
    """Records what was actually connected to, so pinning can be asserted."""

    def __init__(self, log, responses):
        self.log = log
        self.responses = responses
        self.closed = False

    def request(self, method, path, body=None, headers=None):
        self.log.append({"method": method, "path": path, "body": body, "headers": headers})

    def getresponse(self):
        return self.responses.pop(0) if self.responses else _FakeResponse()

    def close(self):
        self.closed = True


def _factory(log, responses=None, connect_log=None):
    def make(scheme, connect_host, port, timeout, context):
        if connect_log is not None:
            connect_log.append({"scheme": scheme, "host": connect_host, "port": port,
                                "timeout": timeout, "verified": context is not None})
        return _FakeConnection(log, responses if responses is not None else [])
    return make


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _dest(url="http://localhost:4318/v1/logs", **kw):
    return tp.resolve_destination(url, resolver=lambda *a, **k: _addrinfo("127.0.0.1"), **kw)


class TestSchemeAndUserInfo:
    """AC-0044, AC-0028, AC-0024 — the accepted set is exactly two schemes."""

    @pytest.mark.parametrize("url", ["ftp://h/v1/logs", "file:///tmp/x", "gopher://h", "//h/v1"])
    def test_any_other_scheme_is_refused(self, url):
        with pytest.raises(tp.DestinationRefused):
            tp.resolve_destination(url, resolver=lambda *a, **k: _addrinfo("127.0.0.1"))

    def test_https_is_accepted_at_any_host(self):
        d = tp.resolve_destination("https://collector.example.com/v1/logs",
                                   resolver=lambda *a, **k: _addrinfo("203.0.113.10"))
        assert d.scheme == "https" and d.connect_host == "collector.example.com"

    def test_https_verifies_the_chain_and_hostname(self):
        """The default SSL context verifies both; an unverified one is the bug."""
        connect_log = []
        tp.send_batches(
            [([], b"{}")],
            tp.resolve_destination("https://collector.example.com/v1/logs",
                                   resolver=lambda *a, **k: _addrinfo("203.0.113.10")),
            _factory([], [_FakeResponse()], connect_log),
            clock=_Clock(),
        )
        assert connect_log and connect_log[0]["verified"] is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://user:pass@host/v1/logs",
            "https://user@host/v1/logs",
            "http://user:pass@localhost:4318/v1/logs",
        ],
    )
    def test_user_info_is_refused(self, url):
        with pytest.raises(tp.DestinationRefused) as excinfo:
            tp.resolve_destination(url, resolver=lambda *a, **k: _addrinfo("127.0.0.1"))
        assert "pass" not in str(excinfo.value), "refusing a credential must not print it"


class TestLoopbackPolicy:
    """AC-0025, AC-0026 — plaintext only to loopback, and pinned to the address."""

    @pytest.mark.parametrize("address", ["127.0.0.1", "127.0.0.5", "::1"])
    def test_plaintext_to_a_loopback_address_is_accepted(self, address):
        d = tp.resolve_destination(
            "http://localhost:4318/v1/logs", resolver=lambda *a, **k: _addrinfo(address)
        )
        assert d.connect_host == address

    @pytest.mark.parametrize("address", ["10.0.0.5", "203.0.113.9", "169.254.169.254"])
    def test_plaintext_to_any_non_loopback_address_is_refused(self, address):
        with pytest.raises(tp.DestinationRefused):
            tp.resolve_destination(
                "http://evil.example.com:4318/v1/logs",
                resolver=lambda *a, **k: _addrinfo(address),
            )

    def test_one_non_loopback_answer_among_several_refuses_the_whole_endpoint(self):
        """`every address` is the contract: a host answering with both a loopback
        and a routable address is refused, not silently narrowed to the safe one."""
        with pytest.raises(tp.DestinationRefused):
            tp.resolve_destination(
                "http://mixed.example.com:4318/v1/logs",
                resolver=lambda *a, **k: _addrinfo("127.0.0.1", "203.0.113.9"),
            )

    def test_the_request_goes_to_the_verified_address_not_a_second_resolution(self):
        """The DNS-rebinding case, and the reason the address is pinned.

        This resolver answers loopback first and routable afterwards. A build
        that resolves once and connects to the result is safe; a build that
        re-resolves at connect time reaches 203.0.113.9. A fixture returning both
        addresses at once cannot tell those two implementations apart.
        """
        answers = [_addrinfo("127.0.0.1"), _addrinfo("203.0.113.9")]

        def rebinding(*args, **kwargs):
            return answers.pop(0) if answers else _addrinfo("203.0.113.9")

        destination = tp.resolve_destination("http://rebind.example.com:4318/v1/logs",
                                             resolver=rebinding)
        connect_log = []
        tp.send_batches([([], b"{}")], destination,
                        _factory([], [_FakeResponse()], connect_log), clock=_Clock())
        assert connect_log[0]["host"] == "127.0.0.1"
        assert connect_log[0]["host"] != "203.0.113.9"


class TestEndpointRendering:
    """AC-0045 — one representation, with nothing dangerous left in it."""

    def test_user_info_query_and_fragment_are_all_omitted(self):
        rendered = tp.render_endpoint("https://u:p@host:4318/v1/logs?token=abc#frag")
        assert rendered == "https://host:4318/v1/logs"
        for secret in ("u:p", "token", "abc", "frag", "?", "#"):
            assert secret not in rendered

    def test_control_characters_are_stripped(self):
        """A newline or an escape in a hostname can rewrite the log line around it."""
        rendered = tp.render_endpoint("https://ho\rst\x1b[2K:4318/v1/logs\n")
        assert all(not (ord(c) < 0x20 or 0x7F <= ord(c) <= 0x9F) for c in rendered)


class TestBatching:
    """AC-0011, AC-0019, AC-0063 — bounded per request, and never accumulated."""

    def test_at_most_512_records_per_request(self):
        encode = lambda batch, diagnostics=True: json.dumps([dict(r) for r in batch]).encode()
        batches = list(tp.batch_records([{"i": i} for i in range(1025)], encode))
        assert [len(records) for records, _ in batches] == [512, 512, 1]

    def test_record_513_begins_the_next_request(self):
        encode = lambda batch, diagnostics=True: json.dumps([dict(r) for r in batch]).encode()
        batches = list(tp.batch_records([{"i": i} for i in range(513)], encode))
        assert batches[0][0][-1]["i"] == 511
        assert batches[1][0][0]["i"] == 512

    def test_a_batch_over_the_byte_ceiling_is_split_not_dropped(self):
        """Measured on the ENCODED body. Splitting rather than truncating is the
        difference between two requests and silently lost records."""
        payload = "x" * 40_000
        encode = lambda batch, diagnostics=True: json.dumps([dict(r) for r in batch]).encode()
        records = [{"i": i, "pad": payload} for i in range(400)]
        batches = list(tp.batch_records(records, encode))
        assert len(batches) > 1
        assert all(len(body) <= tp.MAX_BODY_BYTES for _, body in batches)
        assert sum(len(r) for r, _ in batches) == 400, "every record still sent"

    def test_no_more_than_one_batch_is_resident_over_a_large_input(self):
        """AC-0063. The generator is fed a 10,000-record iterator that counts how
        many records have been pulled; a build that materialises the input first
        pulls all 10,000 before the first batch is yielded."""
        pulled = []

        def source():
            for i in range(10_000):
                pulled.append(i)
                yield {"i": i}

        encode = lambda batch, diagnostics=True: json.dumps([dict(r) for r in batch]).encode()
        batches = tp.batch_records(source(), encode)
        next(batches)
        assert len(pulled) <= tp.MAX_RECORDS_PER_REQUEST, (
            f"{len(pulled)} records were read before the first batch was ready"
        )


class TestRetryAndAttempts:
    """AC-0008, AC-0009, AC-0010, AC-0036, AC-0054 — how often, and how long after."""

    def test_at_most_three_attempts_across_the_whole_run(self):
        responses = [_FakeResponse(503, {"Retry-After": "1"}) for _ in range(9)]
        log = []
        clock = _Clock()
        out = tp.send_batches(
            [([], b"{}"), ([], b"{}"), ([], b"{}")],
            _dest(), _factory(log, responses), clock=clock, sleep=lambda s: None,
            stream=io.StringIO(),
        )
        assert out.attempts == tp.MAX_ATTEMPTS_PER_RUN
        assert out.status == 1

    def test_retry_after_is_measured_from_response_receipt(self):
        """Not from when the request was issued: the two differ by the request's
        own duration, and the server's instruction is about now."""
        clock = _Clock()
        slept = []

        def connection_factory(scheme, host, port, timeout, context):
            clock.now += 4.0  # the request itself takes four seconds
            return _FakeConnection([], [_FakeResponse(429, {"Retry-After": "10"}),
                                        _FakeResponse(200)])

        tp.send_batches([([], b"{}")], _dest(), connection_factory,
                        clock=clock, sleep=slept.append, stream=io.StringIO())
        assert slept and abs(slept[0] - 10.0) < 0.001, (
            "the delay must start at receipt; measuring from issue would sleep 6"
        )

    @pytest.mark.parametrize(
        "header,expected",
        [("5", 5), ("30", 30), ("31", 30), ("900", 30), ("-1", 0), ("", 0), (None, 0),
         ("soon", 0), ("3.5", 0)],
    )
    def test_the_retry_after_value_is_clamped_and_defaulted(self, header, expected):
        assert tp._retry_after_seconds(header) == expected

    def test_a_partial_success_produces_no_retry_reports_and_fails(self):
        """AC-0008, AC-0036, AC-0054 asserted separately: a build that suppresses
        the retry while reporting success passes the first alone."""
        payload = json.dumps({"partialSuccess": {"rejectedLogRecords": 7}}).encode()
        log, err = [], io.StringIO()
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory(log, [_FakeResponse(200, {}, payload), _FakeResponse(200)]),
            clock=_Clock(), stream=err,
        )
        assert out.attempts == 1, "a partialSuccess must not be retried"
        assert out.rejected_records == 7
        assert "7" in err.getvalue()
        assert out.status == 1


class TestRedirects:
    """AC-0027 — a redirect is refused, never followed."""

    @pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
    def test_a_redirect_is_refused_and_the_run_fails(self, status):
        log, err = [], io.StringIO()
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory(log, [_FakeResponse(status, {"Location": "https://elsewhere/v1/logs"})]),
            clock=_Clock(), stream=err,
        )
        assert out.status == 1
        assert out.attempts == 1, "the redirect target must not be requested"
        assert "elsewhere" in err.getvalue()

    def test_a_redirect_target_is_rendered_safely(self):
        log, err = [], io.StringIO()
        tp.send_batches(
            [([], b"{}")], _dest(),
            _factory(log, [_FakeResponse(302, {"Location": "https://u:p@elsewhere/v1?t=s"})]),
            clock=_Clock(), stream=err,
        )
        assert "u:p" not in err.getvalue() and "t=s" not in err.getvalue()


class TestTimeBounds:
    """AC-0040, AC-0055 — per request and per run, on a monotonic clock."""

    def test_the_per_request_timeout_is_thirty_seconds(self):
        connect_log = []
        tp.send_batches([([], b"{}")], _dest(),
                        _factory([], [_FakeResponse()], connect_log), clock=_Clock())
        assert connect_log[0]["timeout"] == tp.REQUEST_TIMEOUT_SECONDS

    @pytest.mark.parametrize("best_effort", [False, True])
    def test_no_request_is_issued_after_the_run_bound(self, best_effort):
        """61 seconds per request, so the THIRD issuance would fall at 122s.

        At 50 seconds each, three attempts land at 0, 50 and 100 -- all inside
        the bound -- and the run stops on the attempt budget instead. Deleting
        the deadline check entirely left that version green.
        """
        clock = _Clock()
        connect_log = []

        def factory(scheme, host, port, timeout, context):
            connect_log.append(clock.now)
            clock.now += 61.0
            return _FakeConnection([], [_FakeResponse(500)])

        tp.send_batches([([], b"{}") for _ in range(5)], _dest(), factory,
                        clock=clock, stream=io.StringIO(),
                        best_effort=best_effort, run_started=0.0)
        assert len(connect_log) == 2, (
            f"third request would start at {clock.now}s, past the "
            f"{tp.RUN_TIMEOUT_SECONDS}s run bound; issued at {connect_log}"
        )

    def test_a_later_request_near_the_deadline_cannot_outlive_it(self):
        """A request begun at second 119 must not be allowed to run to 149.

        This is the half an issuance-only cutoff fails: it would refuse to
        *start* a request after 120s while letting one already started run on.

        The near-deadline request is deliberately not the FIRST one. AC-0040
        anchors a request's 30-second bound at its own destination resolution,
        and the first request's resolution is the run's -- so a first request
        issued at 119s has had its budget for 119 seconds already. Only a later
        request anchors at the moment it starts, which is the case this pins.
        """
        clock = _Clock()
        connect_log = []

        def factory(scheme, host, port, timeout, context):
            connect_log.append({"at": clock.now, "timeout": timeout})
            clock.now = 119.0          # the first attempt consumes the run
            return _FakeConnection([], [_FakeResponse(503, {"retry-after": "0"})])

        tp.send_batches([([], b"{}")], _dest(), factory, clock=clock,
                        sleep=lambda s: None, stream=io.StringIO(), run_started=0.0)
        assert len(connect_log) >= 2, "a second request at 119s is still allowed to start"
        assert connect_log[1]["at"] == 119.0
        assert connect_log[1]["timeout"] <= 1.0, (
            f"timeout {connect_log[1]['timeout']} would run past the 120s run bound"
        )

    def test_the_first_request_is_bounded_from_the_runs_own_resolution(self):
        """AC-0040 says the request bound COVERS resolution.

        Anchoring the first request at the moment sending starts would hand a run
        that spent 29 seconds resolving a fresh 30 seconds on top of it.
        """
        clock = _Clock()
        clock.now = 29.0               # resolution took 29 seconds
        connect_log = []
        tp.send_batches([([], b"{}")], _dest(),
                        _factory([], [_FakeResponse()], connect_log),
                        clock=clock, stream=io.StringIO(), run_started=0.0)
        assert connect_log, "a request at 29s still has one second of budget"
        assert connect_log[0]["timeout"] <= 1.0, (
            f"timeout {connect_log[0]['timeout']} ignores the 29s already spent"
        )


class TestResponseBound:
    """AC-0041 — at most 1 MiB plus one byte, refused without decoding."""

    def test_an_oversize_response_body_is_refused(self):
        oversize = b"x" * (tp.MAX_RESPONSE_BYTES + 1)
        log, err = [], io.StringIO()
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory(log, [_FakeResponse(200, {}, b"x" * (tp.MAX_RESPONSE_BYTES + 1)) for _ in range(3)]),
            clock=_Clock(), stream=err,
        )
        assert out.status == 1
        assert "exceeds" in err.getvalue()

    def test_a_body_at_the_ceiling_is_accepted(self):
        """EXACTLY at the ceiling, not one byte under.

        A fixture one byte short cannot tell `>` from `>=`, so flipping the
        comparison rejects a legal 1 MiB body while every test still passes.
        """
        head, tail = b'{"x":"', b'"}'
        at_limit = head + b"y" * (tp.MAX_RESPONSE_BYTES - len(head) - len(tail)) + tail
        assert len(at_limit) == tp.MAX_RESPONSE_BYTES
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory([], [_FakeResponse(200, {}, at_limit)]),
            clock=_Clock(), stream=io.StringIO(),
        )
        assert out.status == 0


class TestReviewRegressions:
    """Cases the implementation review found in the transport."""

    @pytest.mark.parametrize("name", ["Retry-After", "retry-after", "RETRY-AFTER"])
    def test_retry_after_is_found_whatever_case_the_server_used(self, name):
        """HTTP field names are case-insensitive (RFC 9110) and HTTP/2 mandates
        lowercase. `getheaders()` preserves what the server sent, so a literal
        "Retry-After" lookup silently ignored the backoff and retried at once."""
        slept = []
        tp.send_batches(
            [([], b"{}")], _dest(),
            _factory([], [_FakeResponse(503, {name: "10"}), _FakeResponse(200)]),
            clock=_Clock(), sleep=slept.append, stream=io.StringIO(),
        )
        assert slept and abs(slept[0] - 10.0) < 0.01, f"{name} was not honoured"

    def test_a_zero_count_partial_success_is_still_a_partial_success(self):
        """The criteria key on the OBJECT being non-empty, not the count.

        A receiver saying "I rejected records, here is why" with a zero count was
        read as complete success and exited 0.
        """
        payload = json.dumps(
            {"partialSuccess": {"rejectedLogRecords": 0, "errorMessage": "invalid"}}
        ).encode()
        err = io.StringIO()
        out = tp.send_batches([([], b"{}")], _dest(),
                              _factory([], [_FakeResponse(200, {}, payload)]),
                              clock=_Clock(), stream=err)
        assert out.partial_success is True
        assert out.status == 1
        assert "partial success" in err.getvalue()

    def test_an_absent_or_empty_partial_success_is_success(self):
        for payload in (b"{}", b'{"partialSuccess":{}}', b""):
            out = tp.send_batches([([], b"{}")], _dest(),
                                  _factory([], [_FakeResponse(200, {}, payload)]),
                                  clock=_Clock(), stream=io.StringIO())
            assert out.status == 0 and out.partial_success is False, payload

    def test_best_effort_does_not_forgive_a_partial_success(self):
        """AC-0012 scopes the allowance to a send FAILURE. This send succeeded --
        HTTP 200 -- and the receiver refused records on their content, which
        AC-0054 makes an unconditional exit 1."""
        payload = json.dumps({"partialSuccess": {"rejectedLogRecords": 3}}).encode()
        out = tp.send_batches([([], b"{}")], _dest(),
                              _factory([], [_FakeResponse(200, {}, payload)]),
                              clock=_Clock(), stream=io.StringIO(), best_effort=True)
        assert out.status == 1

    def test_best_effort_still_forgives_an_ordinary_send_failure(self):
        out = tp.send_batches([([], b"{}")], _dest(),
                              _factory([], [_FakeResponse(500) for _ in range(3)]),
                              clock=_Clock(), stream=io.StringIO(), best_effort=True)
        assert out.status == 0

    def test_a_trickling_response_is_abandoned_at_the_request_deadline(self):
        """A socket timeout bounds each recv, not the request. One byte every
        29 seconds kept every operation inside a 30-second timeout while the
        request as a whole ran without limit."""
        clock = _Clock()

        class _Trickle:
            def getheaders(self):
                return []

            def read(self, amount):
                clock.now += 29.0     # inside any per-operation timeout
                return b"x"           # ... and never finishes

            status = 200

        def factory(scheme, host, port, timeout, context):
            return _FakeConnection([], [_Trickle()])

        err = io.StringIO()
        out = tp.send_batches([([], b"{}")], _dest(), factory,
                              clock=clock, stream=err, run_started=0.0)
        assert out.status == 1
        assert "deadline" in err.getvalue()

    def test_an_unsplittable_oversize_record_is_not_sent_and_is_reported(self):
        """AC-0019's ceiling is unconditional. A single record over it cannot be
        split, so it is refused and reported rather than sent."""
        encode = lambda batch, diagnostics=True: json.dumps([dict(r) for r in batch]).encode()
        seen = []
        batches = list(tp.batch_records(
            [{"pad": "x" * (tp.MAX_BODY_BYTES + 100)}], encode, on_oversize=seen.append))
        assert batches == []
        assert seen and seen[0] > tp.MAX_BODY_BYTES

    def test_a_malformed_endpoint_is_refused_without_leaking_its_bytes(self):
        """`urlsplit` interpolates the ORIGINAL netloc into its ValueError, so an
        unguarded call put an unsanitised endpoint on stderr."""
        with pytest.raises(tp.DestinationRefused) as excinfo:
            tp.resolve_destination("https://ho\x1bst／evil:4318/v1/logs")
        message = str(excinfo.value)
        assert all(not (ord(c) < 0x20 or 0x7F <= ord(c) <= 0x9F) for c in message)


class TestRound3Regressions:
    """Time bounds that must hold whatever the call is blocked on."""

    def test_a_stalled_resolver_does_not_hang_the_run(self):
        """Neither getaddrinfo nor create_connection takes a timeout, so an
        unanswering resolver hung the process before either clock was read."""
        import threading as _t

        started = _t.Event()

        def never_answers(*args, **kwargs):
            started.set()
            _t.Event().wait()  # blocks forever

        import jsonl_otlp_exporter.transport as mod
        real = mod.REQUEST_TIMEOUT_SECONDS
        mod.REQUEST_TIMEOUT_SECONDS = 1
        try:
            with pytest.raises(tp.DestinationRefused) as excinfo:
                tp.resolve_destination("http://stalled.example:4318/v1/logs",
                                       resolver=never_answers)
        finally:
            mod.REQUEST_TIMEOUT_SECONDS = real
        assert started.is_set()
        assert "did not answer" in str(excinfo.value)

    def test_the_watchdog_abandons_a_request_blocked_in_any_phase(self, monkeypatch):
        """Against a REAL socket that accepts the connection and then says nothing.

        The fakes cannot show this. The connect, the header read and the body
        read each get the socket timeout independently, and `http.client`
        restarts the timer on every recv, so no per-operation timeout bounds the
        request as a whole. Only closing the connection from outside does.

        The socket timeout handed to the connection is deliberately far LARGER
        than the request bound, so anything that finishes in time can only have
        been stopped by the watchdog. The bounds are shrunk so the proof takes
        seconds rather than two minutes.
        """
        import http.client
        import socket as _s
        import threading as _t

        monkeypatch.setattr(tp, "REQUEST_TIMEOUT_SECONDS", 1)
        monkeypatch.setattr(tp, "RUN_TIMEOUT_SECONDS", 4)

        listener = _s.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        held = []

        def accept_and_stall():
            while True:
                try:
                    conn, _ = listener.accept()
                except OSError:
                    return
                held.append(conn)  # accepted, then never answers

        _t.Thread(target=accept_and_stall, daemon=True).start()

        destination = tp.resolve_destination(
            f"http://127.0.0.1:{port}/v1/logs",
            resolver=lambda *a, **k: _addrinfo("127.0.0.1"),
        )
        started = time.monotonic()
        out = tp.send_batches(
            [([], b"{}")], destination,
            lambda scheme, host, p, timeout, ctx: http.client.HTTPConnection(
                host, p, timeout=120),   # far larger than either bound
            stream=io.StringIO(), run_started=started,
        )
        elapsed = time.monotonic() - started
        listener.close()
        for conn in held:
            conn.close()

        assert out.status == 1
        assert out.attempts >= 1
        assert elapsed < 30, (
            f"the run took {elapsed:.1f}s against a 4s run bound and a 120s "
            "socket timeout; without the watchdog it would block on the socket"
        )

    def test_the_for_deadline_bounds_a_retry_backoff(self):
        """`--follow --for 1` against `Retry-After: 30` slept thirty seconds and
        reissued, because the sender never learned about `--for` and the reader's
        own deadline cannot fire while the sender is asleep."""
        clock = _Clock()
        slept, connect_log = [], []
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory([], [_FakeResponse(429, {"retry-after": "30"}),
                          _FakeResponse(200)], connect_log),
            clock=clock, sleep=slept.append, stream=io.StringIO(),
            run_started=0.0, for_seconds=1,
        )
        assert len(connect_log) == 1, "no second request may be issued past --for"
        assert out.status == 1


class TestRound4Regressions:
    """Three controls that mutation showed were missing entirely."""

    def test_the_for_bound_is_measured_from_the_first_read(self):
        """AC-0042 anchors `--for` at the instant the first read begins.

        Anchored at the run's start instead, a run whose resolution took longer
        than `--for` exceeded the bound before a single record was pulled and
        sent nothing at all. Here resolution notionally took five seconds and the
        first read has just happened, so the run still has its full second.
        """
        clock = _Clock()
        clock.now = 5.0
        connect_log = []
        tp.send_batches(
            [([], b"{}")], _dest(), _factory([], [_FakeResponse()], connect_log),
            clock=clock, stream=io.StringIO(), run_started=0.0, for_seconds=1,
            first_read_at=lambda: 5.0,
        )
        assert connect_log, (
            "the record was dropped: --for was measured from the run's start, "
            "so a five-second resolution consumed a one-second budget"
        )

    def test_without_a_first_read_stamp_the_bound_falls_back_to_run_start(self):
        """The fallback must still bound a run that never read anything."""
        clock = _Clock()
        clock.now = 5.0
        connect_log = []
        out = tp.send_batches(
            [([], b"{}")], _dest(), _factory([], [_FakeResponse()], connect_log),
            clock=clock, stream=io.StringIO(), run_started=0.0, for_seconds=1,
            first_read_at=lambda: None,
        )
        assert not connect_log and out.status == 1

    def test_a_stalled_https_resolver_is_refused(self, monkeypatch):
        """The https branch never called the bounded lookup, so a resolver that
        never answers ran past both bounds -- and the watchdog cannot help,
        because during `connect` there is no socket to shut down yet."""
        import threading as _t

        monkeypatch.setattr(tp, "REQUEST_TIMEOUT_SECONDS", 1)
        started = _t.Event()

        def never_answers(*args, **kwargs):
            started.set()
            _t.Event().wait()

        with pytest.raises(tp.DestinationRefused) as excinfo:
            tp.resolve_destination("https://stalled.example/v1/logs", resolver=never_answers)
        assert started.is_set()
        assert "did not answer" in str(excinfo.value)

    def test_the_watchdog_shuts_down_the_socket_it_retained(self):
        """A `Connection: close` reply makes `getresponse()` clear
        `connection.sock` while the response keeps reading through its own file
        object -- so a watchdog that looks the socket up when it FIRES finds
        nothing, and closing alone does not wake a blocked reader.

        This pins the mechanism rather than trying to reproduce `http.client`'s
        exact blocking: the connection reports no socket, and the watchdog must
        still tear down the one it was handed. The peer's blocking `recv`
        returning is the observable -- that is precisely what a blocked reader
        being woken looks like.
        """
        import socket as _s
        import threading as _t

        near, far = _s.socketpair()

        class ClearedConnection:
            sock = None      # as http.client leaves it for `Connection: close`
            closed = False

            def close(self):
                self.closed = True

        woke = _t.Event()

        def blocked_peer():
            far.recv(1)      # blocks until the near end is shut down
            woke.set()

        _t.Thread(target=blocked_peer, daemon=True).start()
        time.sleep(0.1)
        assert not woke.is_set(), "the peer should still be blocked"

        watchdog = tp._Watchdog(ClearedConnection(), 0.05)
        watchdog.attach(near)
        with watchdog:
            woke.wait(timeout=5)

        assert watchdog.fired
        assert woke.is_set(), (
            "the retained socket was never shut down, so a blocked reader would "
            "keep waiting past the deadline"
        )
        near.close()
        far.close()
