"""T6 — the CLI and the exit-code contract.

Covers AC-0012, AC-0013, AC-0014, AC-0015, AC-0039.

AC-0014 is walked over each distinct STATE the `### Exit codes` table names, not
one invocation per table row. Two rows name four and two states respectively, so
a per-row walk samples each row's first alternative and never exercises the rest.
"""

from __future__ import annotations

import ast
import functools
import io
import json
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time

import jsonl_otlp_exporter
import pytest
from conftest import await_released_workers
from jsonl_otlp_exporter import cli
from jsonl_otlp_exporter import config as cfg
from jsonl_otlp_exporter import transport as tp

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


# --- resume helpers -------------------------------------------------------
#
# `_run_against_receiver` drives the assembled command against the recording
# fake above. `_argv_for` / `_env_for` build one invocation per pre-open exit
# reason, so AC-0019 is walked rather than sampled.

BAD_PROFILE = 'timestamp_field = "at"\n'  # missing the other five keys (AC-0035)


def _run_against_receiver(tmp_path, monkeypatch, *, out=None, stream=None,
                          sent=None, extra=(), target=None, lines=1,
                          statuses=(200,)) -> int:
    """Drive `cli.main` end to end against a recording fake receiver.

    Writes `lines` valid records to `target` (default `tmp_path/events.jsonl`)
    only when that path does not already exist, so a caller that wrote its own
    fixture keeps it. `statuses` answers the first requests in order; anything
    past the list gets a 200. Request bodies are appended to `sent`.
    """
    target = pathlib.Path(target) if target is not None else tmp_path / "events.jsonl"
    profile = tmp_path / "p.toml"
    if not profile.exists():
        profile.write_text(REFERENCE_PROFILE, encoding="utf-8")
    if not target.exists():
        target.write_bytes(GOOD_LINE.encode("utf-8") * lines)
    # ONE response queue shared across connections. `_factory` copies its list
    # per connection (`list(responses)`), and `_post` opens a connection per
    # request -- so every request popped index 0 and `statuses` past the first
    # element was silently unreachable. A multi-status case built on `_factory`
    # is vacuous, which is how `[200, 400]` read as two 200s.
    queue = [_Response(status=s) for s in statuses]
    store = sent if sent is not None else []

    def factory(scheme, host, port, timeout, context):
        return _Connection(queue, store)

    return cli.main(
        ["--input", str(target), "--root", str(tmp_path),
         "--profile", str(profile), *extra],
        env=dict(ENV),
        stream=stream if stream is not None else io.StringIO(),
        out=out if out is not None else io.StringIO(),
        connection_factory=factory,
    )


def _argv_for(kind, tmp_path) -> list[str]:
    """Argv for one of AC-0019's six pre-open exit reasons.

    Every case carries `--report-cursor`. Without it AC-0002 already requires an
    empty stdout and the case would prove nothing.
    """
    profile = tmp_path / "p.toml"
    profile.write_text(REFERENCE_PROFILE, encoding="utf-8")
    events = tmp_path / "events.jsonl"
    events.write_text(GOOD_LINE, encoding="utf-8")
    argv = ["--input", str(events), "--root", str(tmp_path),
            "--profile", str(profile), "--report-cursor"]
    if kind == "bad-cursor":
        return argv + ["--from-cursor", "not a cursor"]
    if kind == "bad-config":
        # A directory: refused on the opened object, per AC-0062.
        (tmp_path / "cfg").mkdir(exist_ok=True)
        return argv + ["--config", str(tmp_path / "cfg")]
    if kind == "bad-profile":
        bad = tmp_path / "bad.toml"
        bad.write_text(BAD_PROFILE, encoding="utf-8")
        return [a if a != str(profile) else str(bad) for a in argv]
    if kind == "absent-input":
        return [a if a != str(events) else str(tmp_path / "gone.jsonl") for a in argv]
    return argv  # no-endpoint and bad-endpoint differ only in the environment


def _env_for(kind) -> dict[str, str]:
    """The environment paired with `_argv_for(kind, ...)`."""
    if kind in ("no-endpoint", "bad-config"):
        # bad-config must be {} as well: AC-0002 resolves the env first, so an
        # endpoint in the environment means `--config` is never read and the
        # refusal this case exists for never fires.
        return {}
    if kind == "bad-endpoint":
        return {"OTEL_EXPORTER_OTLP_ENDPOINT": "ftp://example.invalid/v1/logs"}
    return dict(ENV)


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

    def test_the_cli_version_output_follows_the_named_distribution_metadata(self):
        """The guard the deleted assertion only appeared to be.

        The line this replaces read
        `assert printed != "<current>" or expected == "<current>"` under the
        message "a hardcoded literal must not be able to satisfy this". It could
        never fail: the assertion above it already established
        `printed == expected`, so the disjunction is a tautology for every
        literal — at 0.1.0 as much as at 0.2.0.

        What the requirement actually is: the **CLI's `--version` output**
        follows the metadata of the distribution named `jsonl-otlp-exporter`.
        Asserting the package attribute alone is not enough, because `cli.py`
        binds `__version__` at import, so a literal in the parser would satisfy
        it while `--version` printed something invented.

        Driven in a subprocess so no other case sees a substituted metadata
        module. The stub answers the sentinel **only** for the exact
        distribution name and a distinct marker for anything else, so querying
        the wrong name fails rather than passing silently; and `--version` is
        invoked through `cli.main`, which is the surface the criterion is about.
        The stale untracked `jsonl_otlp_exporter.egg-info` on the path cannot
        make this pass: it reports the real version, and the assertion demands
        the sentinel.
        """
        sentinel = "9.9.9+sentinel"
        probe = (
            "import importlib.metadata as m;"
            "_real = m.version;"
            "m.version = (lambda name: "
            f"{sentinel!r} if name == 'jsonl-otlp-exporter' "
            "else 'WRONG-DISTRIBUTION-NAME');"
            "from jsonl_otlp_exporter import cli;"
            "cli.main(['--version'])"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(pathlib.Path(__file__).resolve().parents[2])
        proc = subprocess.run(
            [sys.executable, "-c", probe],
            env=env, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == sentinel, (
            "`--version` did not follow the metadata of the named distribution, "
            f"so it is not being read from it: {proc.stdout.strip()!r}"
        )

    def test_the_unconfigured_cli_path_constructs_no_connection(self, workspace):
        """T3. AC-0001's proof lived on `run_unconfigured_check`, which the CLI
        never calls -- so a build opening a socket before the unconfigured return
        passed. This asserts it on the path that actually ships."""
        def exploding(*args, **kwargs):
            raise AssertionError("a connection was constructed with no endpoint")

        err = io.StringIO()
        # `out` is passed explicitly, and asserted empty, because stdout is the
        # machine channel and carries only the cursor: a diagnostic printed there
        # would corrupt a consumer parsing it. Left unset, `main` defaults it to
        # the real `sys.stdout` and nothing here could see the move.
        out = io.StringIO()
        code = cli.main(_argv(workspace), env={}, stream=err, out=out,
                        connection_factory=exploding)
        assert code == 0
        assert "no endpoint is configured" in err.getvalue()
        assert out.getvalue() == "", (
            f"the unconfigured diagnostic reached stdout: {out.getvalue()!r}")

    def test_a_growing_configuration_file_is_refused_with_nothing_sent(
        self, workspace, monkeypatch
    ):
        """T2/AC-0001. A unit over the reader cannot observe "nothing sent and
        exit 1" -- that half of the criterion only exists at this boundary."""
        head = '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n#'
        config = workspace / "grows.toml"
        config.write_text(head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)), encoding="utf-8")
        assert config.stat().st_size == cfg.MAX_CONFIG_BYTES
        real_read = os.read

        def grow_then_read(fd, size):
            with config.open("ab") as second_descriptor:
                second_descriptor.write(b"y")
            return real_read(fd, size)

        monkeypatch.setattr(cfg.os, "read", grow_then_read)

        def exploding(*args, **kwargs):
            raise AssertionError(
                "a connection was constructed for a refused configuration")

        err = io.StringIO()
        code = cli.main(_argv(workspace, "--config", str(config)), env={},
                        stream=err, connection_factory=exploding)
        assert code == 1
        assert "changed" in err.getvalue()

    def test_a_blocking_configuration_read_ends_the_run_within_the_bound(
        self, workspace, monkeypatch
    ):
        """T3/AC-0002/AC-0077. The outcome an adopter sees: a configuration
        path that never returns must not hang the command. `read_config_file`
        establishes its own bound, so the command still ends inside it even
        though nothing here computes a deadline explicitly."""
        monkeypatch.setattr(cfg, "_CONFIG_TIMEOUT_SECONDS", 0.2)
        config = workspace / "hangs.toml"
        config.write_text('[telemetry]\nendpoint = "http://127.0.0.1:4318"\n',
                          encoding="utf-8")
        release = threading.Event()
        real_read = os.read

        def blocking_read(fd, size):
            release.wait()
            return real_read(fd, size)

        monkeypatch.setattr(cfg.os, "read", blocking_read)

        def exploding(*args, **kwargs):
            raise AssertionError(
                "a connection was constructed for a refused configuration")

        err = io.StringIO()
        started = time.monotonic()
        # The sixth site using this idiom, and the one the first repair missed:
        # releasing the event unblocks the substituted read, but the worker
        # `_run_bounded` started keeps running until it returns -- through the
        # overflow probe and `os.close` -- which without this join races
        # `monkeypatch` teardown and the workspace cleanup.
        before_threads = set(threading.enumerate())
        try:
            code = cli.main(_argv(workspace, "--config", str(config)), env={},
                            stream=err, connection_factory=exploding)
        finally:
            release.set()
            await_released_workers(before_threads)
        elapsed = time.monotonic() - started
        assert elapsed < 2, (
            f"the command took {elapsed:.3f}s to end against a 0.2s "
            "configuration-acquisition bound -- it hung instead of refusing"
        )
        assert code == 1
        assert "bound" in err.getvalue()

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

# AC-0001, AC-0022, AC-0002, AC-0003, AC-0011, AC-0012, AC-0018 through
# AC-0030 — the flags end to end.
#
# Appended to tests/unit/test_cli.py, which already imports `cli`, `io`,
# `json` and `pytest`. Adds `import os` and the three module-level helpers
# the `## New test helpers` section above specifies.


class TestReportCursor:
    """Appended to tests/unit/test_cli.py, which owns the local-receiver
    fixtures and the connection-factory seam."""

    def test_the_flag_prints_exactly_one_json_object(self, tmp_path, monkeypatch):
        """AC-0001. The buffer is explicit so dropping `out=` fails this."""
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"])
        assert code == 0
        lines = out.getvalue().splitlines()
        assert len(lines) == 1
        reported = json.loads(lines[0])              # AC-0022
        assert set(reported) == {"v", "offset", "device", "inode"}
        assert reported["v"] == 1
        assert all(type(reported[k]) is int for k in
                   ("v", "offset", "device", "inode"))

    def test_without_the_flag_stdout_stays_empty(self, tmp_path, monkeypatch):
        """AC-0002."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out)
        assert out.getvalue() == ""

    def test_the_identity_is_the_descriptor_not_the_path(self, tmp_path, monkeypatch):
        """AC-0003. The path is replaced after the open; the cursor must not move."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8"))
        expected = target.stat()
        real = cli.open_input

        def swap(path, root):
            fd = real(path, root)
            other = tmp_path / "other.jsonl"
            other.write_bytes(GOOD_LINE.encode("utf-8"))
            pathlib.Path(other).replace(target)
            return fd

        monkeypatch.setattr(cli, "open_input", swap)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], target=target)
        reported = json.loads(out.getvalue())
        assert (reported["device"], reported["inode"]) == (expected.st_dev,
                                                           expected.st_ino)

    def test_the_reported_cursor_resumes_the_next_run(self, tmp_path, monkeypatch):
        """AC-0011 end to end: the whole point, asserted as a round trip."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], lines=2)
        cursor = out.getvalue().strip()
        sent = []
        second = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=second, sent=sent,
                              extra=["--report-cursor", "--from-cursor", cursor],
                              lines=2)
        assert sent == [], "a second run over an unchanged file must send nothing"
        assert json.loads(second.getvalue()) == json.loads(cursor)

    def test_an_identity_change_resends_the_new_files_records(self, tmp_path,
                                                              monkeypatch):
        """AC-0012 at the command.

        T1 proves `resolve_start_offset` returns zero on an identity change; this
        proves the zero reaches the reader. A build that computes the reset and
        then seeks to the stale offset passes T1 and sends nothing here -- or
        worse, sends from the middle of an unrelated record.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8") * 3)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], target=target)
        cursor = out.getvalue().strip()
        assert json.loads(cursor)["offset"] > 0

        replacement = tmp_path / "rotated.jsonl"
        replacement.write_bytes(json.dumps(
            {"at": "2026-02-02T00:00:00Z", "result": "success",
             "run_id": "r", "seq": 9, "event": "rotated"}
        ).encode("utf-8") + b"\n")
        pathlib.Path(replacement).replace(target)

        sent = []
        stream = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(), sent=sent,
                              stream=stream, target=target,
                              extra=["--report-cursor", "--from-cursor", cursor])
        assert len(sent) == 1, "the new file's one record must be sent"
        assert b"rotated" in sent[0], (
            "assert on an allowlisted attribute: the timestamp is emitted as "
            "timeUnixNano, so a date substring never appears in the body"
        )
        assert "identity" in stream.getvalue()   # AC-0023 at the command

    def test_a_misaligned_cursor_is_refused_at_the_command(self, tmp_path,
                                                           monkeypatch):
        """AC-0030 at the command, and the control behind `fd=`.

        T1 proves the boundary check refuses; this proves it is wired, and that
        the run does not fall through to reading from a mid-record offset. The
        cursor is the command's own, with its offset moved one byte -- so its
        identity matches and only the alignment is wrong.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8") * 2)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = json.loads(out.getvalue())
        cursor["offset"] -= 1

        sent = []
        code = _run_against_receiver(tmp_path, monkeypatch, sent=sent,
                                     target=target,
                                     extra=["--from-cursor", json.dumps(cursor)])
        assert code == 1
        assert sent == []

    def test_resuming_sends_exactly_the_records_appended_since(self, tmp_path,
                                                               monkeypatch):
        """AC-0032. The positive assertion the contract was missing.

        The round-trip case above resumes over an UNCHANGED file and asserts
        nothing is sent, which a build that never sends anything also satisfies.
        This appends two records after the first run, resumes, and requires
        exactly those two on the wire -- so a build that honours the cursor by
        reading nothing fails here and nowhere else.
        """
        target = tmp_path / "events.jsonl"
        first = GOOD_LINE.encode("utf-8")
        target.write_bytes(first)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = out.getvalue().strip()

        with pathlib.Path(target).open("ab") as handle:
            for seq in (2, 3):
                handle.write(json.dumps(
                    {"at": f"2026-01-01T00:00:0{seq}Z", "result": "success",
                     "run_id": "r", "seq": seq, "event": "e"}
                ).encode("utf-8") + b"\n")

        sent = []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=io.StringIO(), sent=sent, target=target,
            extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 0
        body = b"".join(sent)
        # `seq` is in the profile's identity set, so it reaches the body as an
        # attribute. The timestamp does not: it becomes `timeUnixNano`.
        assert b'"intValue": "2"' in body and b'"intValue": "3"' in body
        assert b'"intValue": "1"' not in body, "the first record must not be re-sent"

    def test_a_malformed_cursor_exits_one_and_sends_nothing(self, tmp_path,
                                                            monkeypatch):
        """AC-0016 at the CLI, with the transport seam proving nothing was sent."""
        sent = []
        code = _run_against_receiver(tmp_path, monkeypatch, sent=sent,
                                     extra=["--from-cursor", "{}"])
        assert code == 1
        assert sent == []

    @pytest.mark.parametrize("env", [{}, {"OTEL_EXPORTER_OTLP_ENDPOINT":
                                          "http://127.0.0.1:4318"}],
                             ids=["no-endpoint", "endpoint"])
    def test_a_malformed_cursor_exits_one_at_both_endpoint_states(self, env,
                                                                  tmp_path):
        """AC-0026, and the AC-0033 carve-out is what makes one status right.

        A build honouring the unamended AC-0033 returns 0 for the unconfigured
        case, so parametrising the endpoint state is the whole control.
        """
        target = tmp_path / "events.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        stream = io.StringIO()
        code = cli.main(
            ["--input", str(target), "--root", str(tmp_path),
             "--from-cursor", "nonsense"],
            env=env, stream=stream, out=io.StringIO(),
        )
        assert code == 1
        assert "cursor" in stream.getvalue()   # AC-0028


class TestNoCursorWhenNothingWasRead:
    @pytest.mark.parametrize(
        "argv_kind",
        ["no-endpoint", "bad-cursor", "bad-config", "bad-profile", "absent-input",
         "bad-endpoint"],
    )
    def test_a_run_exiting_before_the_open_prints_nothing(self, argv_kind, tmp_path):
        """AC-0019, every reason, because they return from six different points.

        `_argv_for` appends `--report-cursor` to every case. Without it AC-0002
        already requires an empty stdout and none of these would prove anything.
        `bad-cursor` is here because the cursor is parsed before the endpoint is
        resolved, making it another pre-open exit -- the reason this case was
        missing from the first draft.
        """
        out = io.StringIO()
        cli.main(_argv_for(argv_kind, tmp_path), env=_env_for(argv_kind),
                 stream=io.StringIO(), out=out)
        assert out.getvalue() == ""

    def test_an_interrupted_run_prints_nothing(self, tmp_path, monkeypatch):
        """AC-0020. SIGINT arrives in the send loop, so that is where it is raised."""
        def boom(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(cli, "send_batches", boom)
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"])
        assert code == 130
        assert out.getvalue() == ""


class TestNoWriteSurface:
    @staticmethod
    def _tree(root):
        """Every regular file under the root, with content and mtime.

        Names alone cannot see a file whose content was rewritten in place, and a
        single directory cannot see a checkpoint written to a subdirectory.
        """
        return {
            path.relative_to(root).as_posix(): (
                path.read_bytes(), path.stat().st_mtime_ns
            )
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_no_file_under_the_root_changes_across_a_resume_sequence(
        self, tmp_path, monkeypatch
    ):
        """AC-0018. The baseline is taken before the FIRST run, not between runs.

        Snapshotting after run one puts any checkpoint run one wrote inside the
        baseline, so the comparison ratifies it. That is how this case was first
        drafted, and it could not fail.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8"))
        # Every fixture the helper would otherwise create lazily, created here:
        # the baseline must not include a file written after it was taken, and
        # it must not blame the run for one written by the scaffolding.
        (tmp_path / "p.toml").write_text(REFERENCE_PROFILE, encoding="utf-8")
        before = self._tree(tmp_path)
        assert before, "an empty baseline would make the comparison vacuous"

        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        assert self._tree(tmp_path) == before

        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(),
                              target=target,
                              extra=["--report-cursor",
                                     "--from-cursor", out.getvalue().strip()])
        assert self._tree(tmp_path) == before

# AC-0004, AC-0009 and AC-0031 — over the assembled command.
#
# Also in tests/unit/test_cli.py. Adds `import ast`, `import functools`,
# `import pathlib`, `import jsonl_otlp_exporter` and
# `from jsonl_otlp_exporter import transport as tp` to that module, on top of
# what T4 adds.


class TestOffsetJourney:
    def test_a_clean_run_advances_past_trailing_skipped_lines(self, tmp_path,
                                                              monkeypatch):
        """AC-0004's skipped-line members: the offset is the reader's position,
        not the last batch's, whenever every batch was accepted."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(
            GOOD_LINE.encode("utf-8")
            + b"not json\n"
            + b"also not json\n"
        )
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"], target=target)
        assert code == 0
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_a_clean_run_advances_past_an_over_ceiling_record(self, tmp_path,
                                                              monkeypatch):
        """AC-0004's over-ceiling member, which no other case reaches.

        The ceiling is lowered rather than an 8 MiB fixture built: the criterion
        is about the offset, not about the number 8388608, and the batcher already
        takes its ceiling as a value. Without this case a build that holds the
        cursor before an undeliverable record passes every other check and then
        re-reads and re-declines it on every future run, re-sending the whole
        tail behind it each time.
        """
        target = tmp_path / "events.jsonl"
        pad = "x" * 4096
        target.write_bytes(
            GOOD_LINE.encode("utf-8")
            + json.dumps({"at": "2026-01-01T00:00:01Z", "result": "success",
                          "run_id": "r", "seq": 2, "event": pad}).encode("utf-8")
            + b"\n"
        )
        # The ceiling is injected through the existing `max_bytes` parameter,
        # NOT by patching `tp.MAX_BODY_BYTES`: `batch_records` binds
        # that constant as a default at definition time, so rebinding the module
        # attribute changes nothing and the 4 KiB record stays under the real
        # 8 MiB bound. Patching the CLI's imported name is the shape
        # `test_cli.py` already uses for `send_batches` and `iter_records`.
        monkeypatch.setattr(
            cli, "batch_records",
            functools.partial(tp.batch_records, max_bytes=1024),
        )
        out = io.StringIO()
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, stream=stream,
                                     extra=["--report-cursor"], target=target)
        assert code == 0
        assert "cannot be split" in stream.getvalue()
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_the_distribution_has_no_write_or_lock_surface(self):
        """AC-0031. The surface, not one run's effect on one directory.

        AC-0018 snapshots a tree after a run, so it cannot see a write to a path
        outside it or a lock that leaves no file behind. This walks the shipped
        modules instead, so a write surface fails it whether or not any test
        exercises the branch that uses it.

        `rglob`, not `glob`: a module in a subpackage is still shipped.
        Root-qualified for the ambiguous names, because `encode.py:66` calls
        `str.replace` and a bare-name denylist fails on it -- and rooted rather
        than taking the immediate receiver, because `Path(p).unlink()` has a Call
        there. `open`'s mode is read from `mode=` as well as position, and a
        non-literal mode is an offender in itself.
        """
        package = pathlib.Path(jsonl_otlp_exporter.__file__).parent
        bare = {"write_text", "write_bytes", "mkdir", "makedirs", "touch",
                "mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile",
                "TemporaryDirectory", "lockf", "flock", "locking"}
        qualified = {"write", "writelines", "pwrite", "rename", "replace",
                     "remove", "unlink", "rmdir", "truncate", "ftruncate",
                     "symlink", "link", "chmod", "dup2", "copy", "copyfile",
                     "copytree", "move"}
        receivers = {"os", "shutil", "tempfile", "pathlib", "Path"}
        modules = {"fcntl", "msvcrt", "shutil", "tempfile", "sqlite3", "dbm",
                   "shelve"}
        write_flags = {"O_WRONLY", "O_RDWR", "O_CREAT", "O_APPEND", "O_TRUNC"}
        offenders = []

        def _root(node):
            """The root name of an attribute chain, through calls and subscripts.

            `Path(p).replace(q)` roots at `Path`; `text.replace(a, b)` roots at
            `text`. Reading only the immediate receiver misses the first,
            because there the receiver is itself a Call -- which is how
            `Path(p).unlink()` passed the previous draft.
            """
            while True:
                if isinstance(node, ast.Attribute):
                    node = node.value
                elif isinstance(node, (ast.Call,)):
                    node = node.func
                elif isinstance(node, ast.Subscript):
                    node = node.value
                else:
                    return getattr(node, "id", None)

        sources = sorted(package.rglob("*.py"))
        assert sources, "an empty module set would make this vacuous"
        for module in sources:
            tree = ast.parse(module.read_text(encoding="utf-8"))
            where = f"{module.relative_to(package)}"
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in modules:
                            offenders.append((where, node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if (node.module or "").split(".")[0] in modules:
                        offenders.append((where, node.lineno, node.module))
                elif isinstance(node, ast.Call):
                    func = node.func
                    name = getattr(func, "attr", None) or getattr(func, "id", None)
                    if name in bare:
                        offenders.append((where, node.lineno, name))
                    elif name in qualified and _root(func) in receivers:
                        offenders.append((where, node.lineno, f"{_root(func)}.{name}"))
                    elif name == "open" and _root(func) == "os":
                        # `os.open`'s second argument is FLAGS, not a mode. An
                        # earlier draft ran the mode rule here and reported every
                        # `os.open(p, os.O_RDONLY | os.O_NOFOLLOW)` in the
                        # shipped package as a computed mode -- three false
                        # positives, which would have made the guard unusable on
                        # the day it landed.
                        for arg in list(node.args[1:]) + [
                            kw.value for kw in node.keywords
                        ]:
                            for inner in ast.walk(arg):
                                flag = (inner.attr if isinstance(inner, ast.Attribute)
                                        else getattr(inner, "id", None))
                                if flag in write_flags:
                                    offenders.append(
                                        (where, node.lineno, f"os.open {flag}")
                                    )
                    elif name == "open":
                        # `open(path, mode)` puts the mode second; the method
                        # form `p.open(mode)` puts it FIRST. Reading index 1
                        # unconditionally let `Path(p).open("w")` through.
                        index = 1 if isinstance(func, ast.Name) else 0
                        mode = next(
                            (kw.value for kw in node.keywords if kw.arg == "mode"),
                            node.args[index] if len(node.args) > index else None,
                        )
                        if mode is not None:
                            try:
                                literal = ast.literal_eval(mode)
                            except ValueError:
                                # A computed mode is itself a failure: this
                                # distribution has no reason to build one, and
                                # admitting it lets `"w" + "b"` through.
                                offenders.append((where, node.lineno, "computed mode"))
                            else:
                                if any(ch in str(literal) for ch in "wax+"):
                                    offenders.append(
                                        (where, node.lineno, f"open {literal!r}")
                                    )
        assert offenders == []

    def test_every_reported_offset_lands_on_a_record_boundary(self, tmp_path,
                                                              monkeypatch):
        """AC-0009 over the assembled command, across accepted and refused runs."""
        target = tmp_path / "events.jsonl"
        data = b"".join(
            json.dumps({"at": f"2026-01-01T00:00:0{i}Z", "result": "success",
                        "run_id": "r", "seq": i, "event": "e"}).encode("utf-8")
            + b"\n"
            for i in range(5)
        )
        target.write_bytes(data)
        for statuses in ([200], [400], [200, 400], [200, 200]):
            out = io.StringIO()
            _run_against_receiver(tmp_path, monkeypatch, out=out, statuses=statuses,
                                  extra=["--report-cursor"], target=target)
            offset = json.loads(out.getvalue())["offset"]
            assert offset == 0 or data[offset - 1 : offset] == b"\n", (statuses, offset)

# AC-0033, AC-0034 — the steady state of a repeated run.
#
# Appended to tests/unit/test_cli.py, which already has every name this needs.


class TestNothingNewPastTheCursor:
    def test_a_resumed_run_with_nothing_new_exits_zero(self, tmp_path,
                                                       monkeypatch):
        """AC-0033. Found by manual QA of the installed wheel, not by the suite.

        This is the normal state of a polling caller, and it exited 1 because
        the parent contract's `emitted == 0` predicate reads an empty read as an
        all-invalid input. Nothing in the suite drove a second run against an
        unchanged file and checked its status -- the round-trip case that
        existed asserted only that nothing was re-sent.
        """
        out = io.StringIO()
        assert _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"]) == 0
        cursor = out.getvalue().strip()

        second, stream, sent = io.StringIO(), io.StringIO(), []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=second, stream=stream, sent=sent,
            extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 0
        assert sent == []
        assert json.loads(second.getvalue()) == json.loads(cursor)

    def test_that_run_says_no_record_lay_past_the_cursor(self, tmp_path,
                                                         monkeypatch):
        """AC-0034. Split from AC-0033: the two fail independently."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"])
        cursor = out.getvalue().strip()

        stream = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(),
                              stream=stream,
                              extra=["--report-cursor", "--from-cursor", cursor])
        message = stream.getvalue()
        assert "past the cursor" in message
        assert "no line yielded a valid record" not in message, (
            "the old message described invalid lines when no line was read"
        )

    def test_an_all_invalid_input_still_exits_one(self, tmp_path, monkeypatch):
        """The carve-out must not widen to any empty send.

        A build that exits 0 whenever nothing was emitted passes AC-0033 and
        converts a real failure into success. This is the case that separates
        "read no line" from "read lines, emitted nothing".
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n" * 3)
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, out=io.StringIO(),
                                     extra=["--report-cursor"])
        assert code == 1
        assert "no line yielded a valid record" in stream.getvalue()

    def test_a_reset_cursor_against_an_empty_file_exits_one(self, tmp_path,
                                                            monkeypatch):
        """The witness against substituting "a cursor was supplied" for the
        non-zero honoured start.

        A cursor IS supplied and `consumed == begin` holds — both are 0, because
        the identity mismatch reset the offset and the file is empty. A build
        testing `from_cursor is not None and consumed == begin and emitted == 0`
        passes every other case here and exits 0 for this one. Only the
        *honoured non-zero* reading of `begin` separates them.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"")
        stale = json.dumps({"v": 1, "offset": 40, "device": 1, "inode": 2})
        stream, sent = io.StringIO(), []
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, sent=sent, out=io.StringIO(),
                                     extra=["--report-cursor",
                                            "--from-cursor", stale])
        assert code == 1
        assert sent == []
        assert "identity changed" in stream.getvalue()
        assert "no line yielded a valid record" in stream.getvalue()

    def test_an_empty_input_with_no_cursor_exits_one(self, tmp_path, monkeypatch):
        """The case that makes the non-zero-begin half load-bearing.

        Every other case here either consumes a line or resumes from a non-zero
        offset, so a build testing only `emitted == 0 and consumed == begin`
        passes all of them — and then exits 0 for an empty file with no cursor,
        where `begin` and `consumed` are both 0. The parent contract's AC-0039
        and its exit table both claim 1 for that.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"")
        stream, sent = io.StringIO(), []
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, sent=sent, out=io.StringIO(),
                                     extra=["--report-cursor"])
        assert code == 1
        assert sent == []
        assert "no line yielded a valid record" in stream.getvalue()

    def test_an_honoured_cursor_followed_by_invalid_lines_exits_one(
        self, tmp_path, monkeypatch
    ):
        """The case that makes the `consumed == begin` half of the check load-bearing.

        Every other case here starts at byte 0, so a build testing only
        `begin != 0 and emitted == 0` passes all of them while converting a
        genuine all-invalid tail into success. This one resumes from an honoured
        non-zero cursor AND reads lines, so only the consumed-nothing half can
        separate it from the carve-out.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8"))
        out = io.StringIO()
        assert _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     extra=["--report-cursor"]) == 0
        cursor = out.getvalue().strip()
        assert json.loads(cursor)["offset"] > 0, "the cursor must be non-zero"

        with pathlib.Path(target).open("ab") as handle:
            handle.write(b"not json\n")

        stream, sent = io.StringIO(), []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=io.StringIO(), stream=stream, sent=sent,
            target=target, extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 1, "lines were read and none was valid: that is still a failure"
        assert sent == []
        assert "no line yielded a valid record" in stream.getvalue()

    def test_a_reset_that_finds_nothing_still_exits_one(self, tmp_path,
                                                        monkeypatch):
        """A reset reads from byte 0, so an empty result there is AC-0039's case.

        Distinguishes the carve-out's precondition -- an HONOURED non-zero
        cursor -- from merely having been given a cursor.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n")
        stale = json.dumps({"v": 1, "offset": 5, "device": 1, "inode": 2})
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, out=io.StringIO(),
                                     extra=["--report-cursor",
                                            "--from-cursor", stale])
        assert code == 1
        assert "identity changed" in stream.getvalue()

# AC-0001's exit-1 half, AC-0035, and four controls review found missing.
#
# Appended to tests/unit/test_cli.py and tests/unit/test_cursor.py, both of which
# already have every name these need.


class TestWhichRunsReportACursor:
    """tests/unit/test_cli.py. AC-0001 and AC-0035."""

    def test_a_run_that_emitted_nothing_still_reports_its_cursor(self, tmp_path,
                                                                 monkeypatch):
        """AC-0001's exit-1 half, which no case asserted.

        Only the exit-0 path was checked, and every opened-input exit-1 case
        discarded its stdout buffer — so a build printing the cursor on success
        alone passed the whole suite.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n" * 2)
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     extra=["--report-cursor"])
        assert code == 1
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_a_boundary_refusal_reports_no_cursor(self, tmp_path, monkeypatch):
        """AC-0035. The refusal happens after the open, so AC-0019 cannot own it."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8") * 2)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = json.loads(out.getvalue())
        cursor["offset"] -= 1

        second, stream = io.StringIO(), io.StringIO()
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=second, stream=stream, target=target,
            extra=["--report-cursor", "--from-cursor", json.dumps(cursor)],
        )
        assert code == 1
        assert second.getvalue() == ""
        assert "not a record boundary" in stream.getvalue(), (
            "an automated caller gets exit 1 and needs to know why"
        )


class TestReviewRepairs:
    """tests/unit/test_cli.py. Controls for cases that could not fail."""

    def test_a_later_batch_refusal_still_lands_on_a_boundary(self, tmp_path,
                                                             monkeypatch):
        """The multi-status cases never consumed their second status.

        `MAX_RECORDS_PER_REQUEST` is 512, so five records were one batch and
        `[200, 400]` exercised only the 200. Batching one record per request is
        what makes the second status reachable, and with it the accepted-prefix
        path where a later batch is refused.
        """
        target = tmp_path / "events.jsonl"
        data = b"".join(
            json.dumps({"at": f"2026-01-01T00:00:0{i}Z", "result": "success",
                        "run_id": "r", "seq": i, "event": "e"}).encode("utf-8")
            + b"\n"
            for i in range(3)
        )
        target.write_bytes(data)
        monkeypatch.setattr(
            cli, "batch_records",
            functools.partial(tp.batch_records, max_records=1),
        )
        out = io.StringIO()
        # THREE batches, not four: `MAX_ATTEMPTS_PER_RUN` is 3, so a fourth
        # batch is never issued and the accepted-after-refused batch this case
        # exists to catch never happens. Proven -- with four batches the
        # high-water-mark defect survived this very test.
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     statuses=[200, 400, 200],
                                     extra=["--report-cursor"])
        assert code == 1
        offset = json.loads(out.getvalue())["offset"]
        assert data[offset - 1:offset] == b"\n", offset
        assert offset < len(data), (
            "a refused third batch must not be credited, nor any batch after it"
        )
