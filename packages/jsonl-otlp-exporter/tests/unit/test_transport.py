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
        return self._payload[:amount]


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
        d = tp.resolve_destination("https://collector.example.com/v1/logs")
        assert d.scheme == "https" and d.connect_host == "collector.example.com"

    def test_https_verifies_the_chain_and_hostname(self):
        """The default SSL context verifies both; an unverified one is the bug."""
        connect_log = []
        tp.send_batches(
            [([], b"{}")],
            tp.resolve_destination("https://collector.example.com/v1/logs"),
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
        encode = lambda batch: json.dumps([dict(r) for r in batch]).encode()
        batches = list(tp.batch_records([{"i": i} for i in range(1025)], encode))
        assert [len(records) for records, _ in batches] == [512, 512, 1]

    def test_record_513_begins_the_next_request(self):
        encode = lambda batch: json.dumps([dict(r) for r in batch]).encode()
        batches = list(tp.batch_records([{"i": i} for i in range(513)], encode))
        assert batches[0][0][-1]["i"] == 511
        assert batches[1][0][0]["i"] == 512

    def test_a_batch_over_the_byte_ceiling_is_split_not_dropped(self):
        """Measured on the ENCODED body. Splitting rather than truncating is the
        difference between two requests and silently lost records."""
        payload = "x" * 40_000
        encode = lambda batch: json.dumps([dict(r) for r in batch]).encode()
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

        encode = lambda batch: json.dumps([dict(r) for r in batch]).encode()
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

    def test_no_request_is_issued_after_the_run_bound(self):
        clock = _Clock()
        connect_log = []

        def factory(scheme, host, port, timeout, context):
            connect_log.append(timeout)
            clock.now += 50.0
            return _FakeConnection([], [_FakeResponse(200)])

        out = tp.send_batches([([], b"{}")] * 5, _dest(), factory,
                              clock=clock, stream=io.StringIO())
        assert len(connect_log) <= tp.MAX_ATTEMPTS_PER_RUN
        assert clock.now >= tp.RUN_TIMEOUT_SECONDS or out.status == 0

    def test_a_request_beginning_near_the_deadline_cannot_outlive_it(self):
        """A request begun at second 119 must not be allowed to run to 149.

        This is the half an issuance-only cutoff fails: it would refuse to
        *start* a request after 120s while letting one already started run on.
        """
        clock = _Clock()
        clock.now = 119.0
        connect_log = []
        tp.send_batches([([], b"{}")], _dest(),
                        _factory([], [_FakeResponse()], connect_log),
                        clock=clock, run_started=0.0)
        assert connect_log, "a request at 119s is still allowed to start"
        assert connect_log[0]["timeout"] <= 1.0, (
            f"timeout {connect_log[0]['timeout']} would run past the 120s run bound"
        )


class TestResponseBound:
    """AC-0041 — at most 1 MiB plus one byte, refused without decoding."""

    def test_an_oversize_response_body_is_refused(self):
        oversize = b"x" * (tp.MAX_RESPONSE_BYTES + 1)
        log, err = [], io.StringIO()
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory(log, [_FakeResponse(200, {}, oversize)] * 3),
            clock=_Clock(), stream=err,
        )
        assert out.status == 1
        assert "exceeds" in err.getvalue()

    def test_a_body_at_the_ceiling_is_accepted(self):
        at_limit = b'{"x":"' + b"y" * (tp.MAX_RESPONSE_BYTES - 9) + b'"}'
        assert len(at_limit) <= tp.MAX_RESPONSE_BYTES
        out = tp.send_batches(
            [([], b"{}")], _dest(),
            _factory([], [_FakeResponse(200, {}, at_limit)]),
            clock=_Clock(), stream=io.StringIO(),
        )
        assert out.status == 0
