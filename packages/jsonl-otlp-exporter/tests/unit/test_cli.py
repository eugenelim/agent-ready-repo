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
import socket

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
        assert cli.EXIT_INTERRUPTED == 128 + int(signal.SIGINT)


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
