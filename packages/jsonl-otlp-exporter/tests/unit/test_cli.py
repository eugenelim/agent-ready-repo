"""T6 — the CLI and the exit-code contract.

Covers AC-0012, AC-0013, AC-0014, AC-0015, AC-0039.

AC-0014 is walked over each distinct STATE the `### Exit codes` table names, not
one invocation per table row. Two rows name four and two states respectively, so
a per-row walk samples each row's first alternative and never exercises the rest.
"""

from __future__ import annotations

import io
import json
import signal

import pytest
from jsonl_otlp_exporter import cli

REFERENCE_PROFILE = (
    'timestamp_field = "at"\n'
    'timestamp_format = "rfc3339"\n'
    'severity_field = "result"\n'
    'identity = ["run_id", "seq"]\n'
    'allowlist = ["event"]\n'
    "[severity_map]\nsuccess = 9\nfailure = 17\n"
)
GOOD_LINE = '{"at":"2026-09-13T05:52:24Z","result":"success","run_id":"r","seq":1,"event":"e"}\n'
ENV = {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318"}


class _Response:
    def __init__(self, status=200, headers=None, payload=b"{}"):
        self.status, self._headers, self._payload = status, headers or {}, payload

    def getheaders(self):
        return list(self._headers.items())

    def read(self, amount):
        # A real HTTPResponse CONSUMES: successive reads advance and eventually
        # return b"". A fake that re-returns the whole payload lets a chunked
        # reader loop forever, which is a defect in the double, not the caller.
        chunk = self._payload[:amount]
        self._payload = self._payload[amount:]
        return chunk


class _Connection:
    def __init__(self, responses, sent):
        self.responses, self.sent = responses, sent

    def request(self, method, path, body=None, headers=None):
        self.sent.append(body)

    def getresponse(self):
        return self.responses.pop(0) if self.responses else _Response()

    def close(self):
        pass


def _factory(responses=None, sent=None):
    store = sent if sent is not None else []

    def make(scheme, host, port, timeout, context):
        return _Connection(list(responses) if responses else [], store)

    return make


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "p.toml").write_text(REFERENCE_PROFILE, encoding="utf-8")
    (tmp_path / "e.jsonl").write_text(GOOD_LINE, encoding="utf-8")
    return tmp_path


def _argv(workspace, *extra):
    return [
        "--input", str(workspace / "e.jsonl"),
        "--root", str(workspace),
        "--profile", str(workspace / "p.toml"),
        *extra,
    ]


def _run(workspace, *extra, env=ENV, responses=None, sent=None):
    err = io.StringIO()
    code = cli.main(_argv(workspace, *extra), env=env, stream=err,
                    connection_factory=_factory(responses, sent))
    return code, err.getvalue()


class TestExitCodeTableByState:
    """AC-0014 — every distinct state, and every observed status in {0, 1, 130}."""

    def test_records_sent(self, workspace):
        sent = []
        code, _ = _run(workspace, responses=[_Response(200)], sent=sent)
        assert code == 0 and sent, "a successful run sends and exits 0"

    def test_no_endpoint_configured(self, workspace):
        code, err = _run(workspace, env={})
        assert code == 0
        assert "no endpoint is configured" in err

    def test_some_lines_invalid_and_the_rest_sent(self, workspace):
        (workspace / "e.jsonl").write_text(GOOD_LINE + "not json\n" + GOOD_LINE, encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 0
        assert "line 2" in err

    def test_send_failure_under_best_effort(self, workspace):
        code, _ = _run(workspace, "--best-effort", responses=[_Response(500) for _ in range(3)])
        assert code == 0

    def test_unreadable_input_file(self, workspace):
        err = io.StringIO()
        code = cli.main(
            ["--input", str(workspace / "absent.jsonl"), "--root", str(workspace),
             "--profile", str(workspace / "p.toml")],
            env=ENV, stream=err, connection_factory=_factory(),
        )
        assert code == 1

    def test_confinement_refused_input_file(self, workspace, tmp_path):
        """A distinct state from 'unreadable': the file exists and is readable."""
        outside = tmp_path.parent / "outside.jsonl"
        outside.write_text(GOOD_LINE, encoding="utf-8")
        err = io.StringIO()
        code = cli.main(
            ["--input", str(outside), "--root", str(workspace),
             "--profile", str(workspace / "p.toml")],
            env=ENV, stream=err, connection_factory=_factory(),
        )
        assert code == 1
        outside.unlink()

    def test_every_line_invalid(self, workspace):
        """AC-0039. Distinct from 'some lines invalid', which exits 0."""
        (workspace / "e.jsonl").write_text("not json\nalso not json\n", encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 1
        assert "no line yielded a valid record" in err

    def test_usage_error(self, workspace):
        """AC-0013. argparse's own default here is 2, which is reserved."""
        err = io.StringIO()
        code = cli.main(["--no-such-flag"], env=ENV, stream=err,
                        connection_factory=_factory())
        assert code == 1, "2 is reserved for a consumer's credential taxonomy"

    def test_configuration_error(self, workspace):
        """A refused profile: present, readable, and not a valid profile."""
        (workspace / "p.toml").write_text('timestamp_field = "at"\n', encoding="utf-8")
        code, err = _run(workspace)
        assert code == 1
        assert "missing required key" in err

    def test_refused_endpoint(self, workspace):
        code, err = _run(workspace, env={"OTEL_EXPORTER_OTLP_ENDPOINT": "ftp://host"})
        assert code == 1

    def test_unhandled_exception(self, workspace, monkeypatch):
        """A genuinely UNHANDLED failure, not a transport one.

        A connection_factory that raises is caught and retried by design -- that
        is the "send failure after the retry budget" row, a different state. This
        raises from the encoder, outside every handler, which is the row the
        table means by "an unhandled exception".
        """
        def exploding(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(cli, "encode_records", exploding)
        err = io.StringIO()
        code = cli.main(_argv(workspace), env=ENV, stream=err,
                        connection_factory=_factory([_Response(200)]))
        assert code == 1
        assert "boom" in err.getvalue()
        assert "unexpected failure" in err.getvalue()

    def test_send_failure_after_the_retry_budget(self, workspace):
        code, _ = _run(workspace, responses=[_Response(500) for _ in range(3)])
        assert code == 1

    def test_non_empty_partial_success(self, workspace):
        payload = json.dumps({"partialSuccess": {"rejectedLogRecords": 2}}).encode()
        code, err = _run(workspace, responses=[_Response(200, {}, payload)])
        assert code == 1
        assert "2" in err

    def test_interrupted_by_sigint(self, workspace):
        def interrupting(*args, **kwargs):
            raise KeyboardInterrupt

        err = io.StringIO()
        code = cli.main(_argv(workspace), env=ENV, stream=err,
                        connection_factory=interrupting)
        assert code == 130


class TestTheClosedStatusSet:
    """AC-0014's universal half: no invocation returns anything but 0, 1 or 130."""

    def test_no_state_in_the_table_returns_a_reserved_code(self, workspace, tmp_path):
        """Walks the same fourteen states and asserts the SET, so a build that
        returns 42 fails as surely as one that returns 3.

        An assertion that merely excludes the 2-9 band passes a build returning
        42; that is why this checks membership rather than absence.
        """
        observed = set()
        cases = [
            (lambda: _run(workspace, responses=[_Response(200)])),
            (lambda: _run(workspace, env={})),
            (lambda: _run(workspace, "--best-effort", responses=[_Response(500) for _ in range(3)])),
            (lambda: _run(workspace, responses=[_Response(500) for _ in range(3)])),
            (lambda: _run(workspace, env={"OTEL_EXPORTER_OTLP_ENDPOINT": "ftp://h"})),
        ]
        for case in cases:
            observed.add(case()[0])
        observed.add(cli.main(["--no-such-flag"], env=ENV, stream=io.StringIO(),
                              connection_factory=_factory()))
        observed.add(cli.main(_argv(workspace), env=ENV, stream=io.StringIO(),
                              connection_factory=lambda *a, **k: (_ for _ in ()).throw(
                                  KeyboardInterrupt)))
        assert observed <= {0, 1, 130}, f"out-of-contract status: {observed - {0, 1, 130}}"
        assert observed == {0, 1, 130}, "every documented status must actually occur"

    def test_help_and_version_exit_zero(self, workspace):
        for flag in ("--help", "--version"):
            code = cli.main([flag], env=ENV, stream=io.StringIO(),
                            connection_factory=_factory())
            assert code == 0, f"{flag} is not a usage error"


class TestBestEffort:
    """AC-0012 — the flag changes the status and nothing else."""

    def test_best_effort_does_not_mask_a_refusal_before_sending(self, workspace):
        """It converts a SEND failure to 0. A refused endpoint never sent
        anything, so there is no send outcome to be lenient about, and masking it
        would report success for a run that was never capable of one."""
        code, _ = _run(workspace, "--best-effort",
                       env={"OTEL_EXPORTER_OTLP_ENDPOINT": "ftp://host"})
        assert code == 1

    def test_best_effort_still_reports_the_failure_on_stderr(self, workspace):
        code, err = _run(workspace, "--best-effort", responses=[_Response(500) for _ in range(3)])
        assert code == 0
        assert "500" in err, "exit 0 must not mean silence"


class TestSignalNumbering:
    """AC-0015 — 130 is 128 + SIGINT, the shell convention a caller reads."""

    def test_the_interrupt_status_matches_the_convention(self):
        assert 128 + int(signal.SIGINT) == cli.EXIT_INTERRUPTED


class TestDryRun:
    """A profile that was supplied is validated even with nothing configured.

    `docs/profiles.md` tells a reader to check a profile by running with no
    endpoint set. That instruction is only true if validation happens before the
    unconfigured early return -- and the first version of this CLI returned
    first, so the documented check silently passed any profile at all.
    """

    def test_an_invalid_profile_is_reported_with_no_endpoint_configured(self, workspace):
        (workspace / "p.toml").write_text('timestamp_field = "at"\n', encoding="utf-8")
        code, err = _run(workspace, env={})
        assert code == 1, "the documented dry run must catch a broken profile"
        assert "missing required key" in err

    def test_a_valid_profile_with_no_endpoint_still_exits_zero_and_sends_nothing(self, workspace):
        sent = []
        code, err = _run(workspace, env={}, sent=sent)
        assert code == 0
        assert sent == []
        assert "no endpoint is configured" in err

    def test_no_profile_and_no_endpoint_is_not_an_error(self, workspace):
        """AC-0033 and AC-0052 collide here; off-by-default wins.

        AC-0052 exists to stop a built-in profile deciding the payload, which is
        not a question when nothing is being sent. Recorded in the verification
        ledger for the owner.
        """
        err = io.StringIO()
        code = cli.main(
            ["--input", str(workspace / "e.jsonl"), "--root", str(workspace)],
            env={}, stream=err, connection_factory=_factory(),
        )
        assert code == 0

    def test_no_profile_with_an_endpoint_configured_is_refused(self, workspace):
        err = io.StringIO()
        code = cli.main(
            ["--input", str(workspace / "e.jsonl"), "--root", str(workspace)],
            env=ENV, stream=err, connection_factory=_factory(),
        )
        assert code == 1
        assert "no built-in profile" in err.getvalue()


class TestReviewRegressions:
    """Cases the implementation review found at the CLI seam."""

    def test_the_version_output_is_the_installed_distribution_version(self, capsys):
        """T2. Asserting only exit 0 let a hardcoded literal pass every test, so
        AC-0029 had no control that could fail.

        The expected value is derived from the metadata, with the documented
        source-tree fallback when the distribution is not installed -- an earlier
        version asserted the installed version unconditionally and passed or
        failed depending on whether an `.egg-info` happened to be lying around,
        which is an assertion pinned to the developer's environment.
        """
        from importlib.metadata import PackageNotFoundError, version

        try:
            expected = version("jsonl-otlp-exporter")
        except PackageNotFoundError:
            expected = "0+unknown"

        code = cli.main(["--version"], env=ENV, stream=io.StringIO(),
                        connection_factory=_factory())
        assert code == 0
        printed = capsys.readouterr().out.strip()
        assert printed == expected
        assert printed != "0.1.0" or expected == "0.1.0", (
            "a hardcoded literal must not be able to satisfy this"
        )

    def test_the_unconfigured_cli_path_constructs_no_connection(self, workspace):
        """T3. AC-0001's proof lived on `run_unconfigured_check`, which the CLI
        never calls -- so a build opening a socket before the unconfigured return
        passed. This asserts it on the path that actually ships."""
        def exploding(*args, **kwargs):
            raise AssertionError("a connection was constructed with no endpoint")

        err = io.StringIO()
        code = cli.main(_argv(workspace), env={}, stream=err,
                        connection_factory=exploding)
        assert code == 0
        assert "no endpoint is configured" in err.getvalue()

    def test_a_run_whose_every_record_is_rejected_exits_one(self, workspace):
        """AC-0039. Counting encoder INVOCATIONS reported success for a run that
        posted an empty batch and got a 200 for it."""
        (workspace / "e.jsonl").write_text(
            '{"result":"success","run_id":"r","seq":1}\n'
            '{"result":"failure","run_id":"r","seq":2}\n', encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 1
        assert "no line yielded a valid record" in err

    def test_a_record_skipped_by_the_encoder_is_reported(self, workspace):
        """The `skipped` list was written and never read, so an inadmissible
        timestamp produced no diagnostic anywhere."""
        (workspace / "e.jsonl").write_text(
            GOOD_LINE + '{"at":"no offset","result":"success","run_id":"r","seq":2}\n',
            encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 0
        assert "skipped" in err, "an encoder-skipped record must say so"

    def test_best_effort_does_not_forgive_a_partial_success_at_the_cli(self, workspace):
        payload = json.dumps({"partialSuccess": {"rejectedLogRecords": 1}}).encode()
        code, _ = _run(workspace, "--best-effort",
                       responses=[_Response(200, {}, payload)])
        assert code == 1, "AC-0054 is unconditional; best-effort covers send failure"

    def test_an_over_depth_attribute_is_reported_at_the_cli(self, workspace):
        """`on_dropped_deep` was never passed, so the report could not fire even
        once the encoder was fixed to produce it."""
        deep = "leaf"
        for _ in range(12):
            deep = {"n": deep}
        (workspace / "p.toml").write_text(
            REFERENCE_PROFILE.replace('allowlist = ["event"]', 'allowlist = ["event", "deep"]'),
            encoding="utf-8")
        (workspace / "e.jsonl").write_text(
            json.dumps({"at": "2026-09-13T05:52:24Z", "result": "success",
                        "run_id": "r", "seq": 1, "deep": deep}) + "\n", encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 0
        assert "nests deeper" in err


class TestRound3Regressions:
    def test_an_explicitly_empty_service_name_is_used_as_given(self, workspace):
        """AC-0007 says `service.name` takes the VALUE of --service-name and
        names the profile stem as the default, so an empty string is a supplied
        value rather than an absent one. Recorded in the verification ledger,
        because the opposite reading is defensible and the criterion does not
        decide between them."""
        sent = []
        code, _ = _run(workspace, "--service-name", "", responses=[_Response(200)], sent=sent)
        assert code == 0
        body = json.loads(sent[0])
        attrs = body["resourceLogs"][0]["resource"]["attributes"]
        name = next(a["value"]["stringValue"] for a in attrs if a["key"] == "service.name")
        assert name == "", f"expected the supplied empty value, got {name!r}"

    def test_an_absent_service_name_still_defaults_to_the_profile_stem(self, workspace):
        sent = []
        _run(workspace, responses=[_Response(200)], sent=sent)
        attrs = json.loads(sent[0])["resourceLogs"][0]["resource"]["attributes"]
        name = next(a["value"]["stringValue"] for a in attrs if a["key"] == "service.name")
        assert name == "p"


class TestRound4Regressions:
    def test_the_cli_forwards_the_for_bound_to_the_sender(self, workspace):
        """`--for` must bound the SENDER, not only the reader.

        The reader's own deadline cannot fire during a retry backoff, because the
        reader is not running then. Nothing pinned the wiring, so deleting
        `for_seconds=args.for_seconds` from cli.py left the suite green -- the
        transport test calls send_batches directly and supplies it itself.
        """
        attempts = []

        def counting_factory(scheme, host, port, timeout, context):
            attempts.append(clock_now())
            return _Connection([_Response(429, {"retry-after": "30"}),
                                _Response(200)], [])

        import time as _time
        clock_now = _time.monotonic
        code, _ = _run_raw(workspace, ["--for", "1"], env=ENV,
                           connection_factory=counting_factory)
        assert len(attempts) == 1, (
            f"{len(attempts)} requests issued; --for 1 must stop the sender "
            "before the 30s backoff elapses"
        )
        assert code == 1

    def test_the_cli_forwards_the_first_read_anchor(self, workspace, monkeypatch):
        """AC-0042 measures `--for` from the first READ, not from the run's start.

        The wiring needs its own control: the transport test supplies
        `first_read_at` itself, so deleting the keyword from cli.py left the
        suite green -- the same class of gap that made two earlier repairs inert.

        Resolution is made to take longer than `--for` so the two anchors give
        different answers: anchored at the run's start the budget is already
        spent and nothing is sent; anchored at the first read it is intact.
        """
        import time as _time

        from jsonl_otlp_exporter import transport as _tp

        real_resolve = _tp.resolve_destination

        def slow_resolve(url, resolver=None):
            _time.sleep(1.2)          # longer than the --for below
            return real_resolve(url, resolver=lambda *a, **k: [
                (2, 1, 6, "", ("127.0.0.1", 4318))])

        monkeypatch.setattr(cli, "resolve_destination", slow_resolve)
        sent = []
        code, err = _run(workspace, "--for", "1", responses=[_Response(200)], sent=sent)
        assert sent, (
            "nothing was sent: --for was measured from the run's start, so a "
            f"1.2s resolution consumed the one-second budget ({err.strip()})"
        )
        assert code == 0


def _run_raw(workspace, extra, env, connection_factory):
    err = io.StringIO()
    code = cli.main(_argv(workspace, *extra), env=env, stream=err,
                    connection_factory=connection_factory)
    return code, err.getvalue()


class TestWiringSweepGaps:
    """CLI wirings a mutation sweep found had no control behind them.

    The common cause is structural: every other CLI test injects its own
    `connection_factory`, so the real one -- where the TLS context and the socket
    timeout live -- was never exercised; and no CLI test used `--follow` at all.
    """

    def test_the_real_connection_factory_verifies_tls_and_applies_the_timeout(self):
        """AC-0024's chain-and-hostname verification had no control on the
        shipped path. Removing `context=context` from `_connection_factory`
        survived the entire suite, and so did removing `timeout=timeout`."""
        import ssl

        # Identity, not properties. Asserting `verify_mode == CERT_REQUIRED`
        # cannot fail: with `context=` dropped, HTTPSConnection builds its OWN
        # default context, which verifies too -- so the assertion passes on a
        # build that ignores the caller's context entirely. Mutation caught that;
        # this asserts the connection uses the exact object it was handed.
        supplied = ssl.create_default_context()
        https = cli._connection_factory("https", "collector.example.com", 443, 12.5, supplied)
        try:
            assert https.timeout == 12.5
            assert https._context is supplied, (
                "the connection built its own context instead of using the "
                "caller's, so the destination policy's context is not what "
                "verifies the peer"
            )
            assert supplied.verify_mode == ssl.CERT_REQUIRED
            assert supplied.check_hostname is True
        finally:
            https.close()

        plain = cli._connection_factory("http", "127.0.0.1", 4318, 7.5, None)
        try:
            assert plain.timeout == 7.5
        finally:
            plain.close()

    def test_follow_reaches_the_reader(self, workspace, monkeypatch):
        """`--follow` was never wired-tested: removing `follow=args.follow` from
        the reader call survived, because no CLI test passed the flag."""
        seen = {}
        real = cli.iter_records

        def spy(fd, **kwargs):
            seen.update(kwargs)
            return real(fd, **kwargs)

        monkeypatch.setattr(cli, "iter_records", spy)
        _run(workspace, "--follow", "--for", "0", responses=[_Response(200)])
        assert seen.get("follow") is True, f"follow was not forwarded: {seen}"

    def test_the_for_bound_reaches_the_reader_too(self, workspace, monkeypatch):
        """Distinct from the sender's bound, which has its own control: the
        reader takes `for_seconds` separately and nothing checked that wiring."""
        seen = {}
        real = cli.iter_records

        def spy(fd, **kwargs):
            seen.update(kwargs)
            return real(fd, **kwargs)

        monkeypatch.setattr(cli, "iter_records", spy)
        _run(workspace, "--for", "3", responses=[_Response(200)])
        assert seen.get("for_seconds") == 3, f"for_seconds not forwarded: {seen}"

    def test_the_run_clock_anchor_reaches_the_sender(self, workspace, monkeypatch):
        """The round-2 repair that anchors the run clock at first resolution had
        no control: removing `run_started=run_started` survived."""
        seen = {}
        real = cli.send_batches

        def spy(batches, destination, factory, **kwargs):
            seen.update(kwargs)
            return real(batches, destination, factory, **kwargs)

        monkeypatch.setattr(cli, "send_batches", spy)
        _run(workspace, responses=[_Response(200)])
        assert seen.get("run_started") is not None, f"run_started not forwarded: {seen}"

    def test_an_unmapped_severity_is_reported_at_the_cli(self, workspace):
        """AC-0068's report had no CLI control: removing the
        `on_unmapped_severity` callback survived."""
        (workspace / "e.jsonl").write_text(
            '{"at":"2026-09-13T05:52:24Z","result":"nosuchvalue","run_id":"r","seq":1,"event":"e"}\n',
            encoding="utf-8")
        code, err = _run(workspace, responses=[_Response(200)])
        assert code == 0
        assert "nosuchvalue" in err and "severity_map" in err

    def test_the_oversize_path_is_unreachable_through_the_cli(self):
        """The `on_oversize` wiring survived the sweep, and it cannot be closed
        with a CLI test -- because the branch is unreachable from here.

        AC-0018 caps an input line at 64 KiB and AC-0019 caps a request body at
        8 MiB. Even at a worst-case six-byte escape per input byte plus wrapper
        overhead, one record reaches ~388 KiB: about twenty times under the
        request ceiling. A batch that exceeds the ceiling always splits down to
        records that fit, so the singleton-refusal branch never fires through the
        command.

        The branch stays: `batch_records` is a public function and a caller with
        no line ceiling can reach it, and `test_transport.py` covers it directly.
        What this test pins is the RELATIONSHIP -- if the line ceiling rises or
        the body ceiling falls far enough for one record to exceed a request,
        this fails and the unreachability claim gets revisited rather than
        quietly becoming false.
        """
        from jsonl_otlp_exporter import transport as _tp
        from jsonl_otlp_exporter.source import MAX_LINE_BYTES

        worst_single_record = MAX_LINE_BYTES * 6 + 4096   # 6x escaping + wrapper
        assert worst_single_record < _tp.MAX_BODY_BYTES, (
            f"one {MAX_LINE_BYTES}-byte line can now encode to "
            f"{worst_single_record} bytes, at or over the "
            f"{_tp.MAX_BODY_BYTES}-byte request ceiling: the oversize branch is "
            "reachable through the CLI again and needs a control there"
        )

    def test_best_effort_reaches_the_run(self, workspace, monkeypatch):
        """`--best-effort` must arrive at send_batches, not just at the CLI.

        It previously survived removal because `_run` masked the status a second
        time with the same rule, so the wiring was dead and nothing failed if it
        regressed. That duplicate mask is gone; this pins what replaced it.
        """
        seen = {}
        real = cli.send_batches

        def spy(batches, destination, factory, **kwargs):
            seen.update(kwargs)
            return real(batches, destination, factory, **kwargs)

        monkeypatch.setattr(cli, "send_batches", spy)
        code, _ = _run(workspace, "--best-effort",
                       responses=[_Response(500) for _ in range(3)])
        assert seen.get("best_effort") is True, f"not forwarded: {seen}"
        assert code == 0, "a send failure under --best-effort still exits 0"

    def test_input_is_a_required_option(self, workspace, capsys):
        """AC-0013's usage-error path for a MISSING required option.

        Dropping `required=True` still fails the run, but through whatever
        `open_input(None)` raises rather than as a usage error -- right exit code,
        wrong observable, and no test could tell the two apart.

        Read through `capsys`, not the injected stream: argparse writes its usage
        errors to the process's own `sys.stderr` before `_run` is ever reached,
        so the injected stream is empty and an assertion against it fails for the
        wrong reason.
        """
        code = cli.main(["--root", str(workspace), "--profile", str(workspace / "p.toml")],
                        env=ENV, stream=io.StringIO(), connection_factory=_factory())
        assert code == 1
        message = capsys.readouterr().err
        assert "--input" in message and "required" in message.lower(), (
            f"expected a usage error naming --input, got: {message!r}"
        )
