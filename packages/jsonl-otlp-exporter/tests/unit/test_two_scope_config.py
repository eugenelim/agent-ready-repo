"""T9 — two configuration scopes, merged per setting, with a closed key set.

Covers AC-0074, AC-0075 and AC-0076, and the parts of AC-0007 and AC-0062 that
the second scope added.

Where a criterion is about delivery, the assertion is on the emitted request and
the resolved destination, not on a returned mapping: a mapping proves the parse,
and the parse is not what the criterion claims. Every case runs with no network.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import stat
import threading

import pytest
from conftest import await_released_workers
from jsonl_otlp_exporter import cli
from jsonl_otlp_exporter import config as cfg

REFERENCE_PROFILE = (
    'timestamp_field = "at"\n'
    'timestamp_format = "rfc3339"\n'
    'severity_field = "result"\n'
    'identity = ["run_id", "seq"]\n'
    'allowlist = ["event"]\n'
    "[severity_map]\nsuccess = 9\nfailure = 17\n"
)
GOOD_LINE = '{"at":"2026-09-13T05:52:24Z","result":"success","run_id":"r","seq":1,"event":"e"}\n'


class _Response:
    status = 200

    def __init__(self):
        self._payload = b"{}"

    def getheaders(self):
        return []

    def read(self, amount):
        chunk, self._payload = self._payload[:amount], self._payload[amount:]
        return chunk


class _Recorder:
    """Records where a run connected and what it posted."""

    def __init__(self):
        self.destinations: list[tuple[str, str, int]] = []
        self.bodies: list[bytes] = []

    def factory(self, scheme, host, port, timeout, context):
        self.destinations.append((scheme, host, port))
        recorder = self

        class _Conn:
            def request(self, method, path, body=None, headers=None):
                recorder.bodies.append(body)

            def getresponse(self):
                return _Response()

            def close(self):
                pass

        return _Conn()

    @property
    def records(self) -> list[dict]:
        out: list[dict] = []
        for body in self.bodies:
            payload = json.loads(body)
            out.extend(payload["resourceLogs"][0]["scopeLogs"][0]["logRecords"])
        return out

    def service_name(self) -> str:
        payload = json.loads(self.bodies[0])
        for attribute in payload["resourceLogs"][0]["resource"]["attributes"]:
            if attribute["key"] == "service.name":
                return attribute["value"]["stringValue"]
        raise AssertionError("no service.name resource attribute was emitted")


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.write_text(text, encoding="utf-8")
    return path


def _run(tmp_path, *, env=None, extra=(), recorder=None):
    """Drive the real CLI end to end against a recording fake receiver."""
    recorder = recorder if recorder is not None else _Recorder()
    events = tmp_path / "events.jsonl"
    if not events.exists():
        events.write_text(GOOD_LINE, encoding="utf-8")
    profile = tmp_path / "work-loop.toml"
    if not profile.exists():
        profile.write_text(REFERENCE_PROFILE, encoding="utf-8")
    stream = io.StringIO()
    status = cli.main(
        ["--input", str(events), "--root", str(tmp_path), "--profile", str(profile),
         *extra],
        env=dict(env or {}), stream=stream, out=io.StringIO(),
        connection_factory=recorder.factory,
    )
    return status, recorder, stream.getvalue()


# --- AC-0074: the merge is per setting, and it reaches the wire --------------

class TestPerSettingMerge:
    def test_each_scope_contributes_the_setting_the_other_omits(self, tmp_path):
        """The case whole-file selection cannot serve.

        The repository scope declares only `service_name` and the user scope only
        `endpoint`, so no single file carries this configuration: a build that
        picks one file and passes it loses whichever setting the other held.
        Asserted on the destination and the emitted resource attribute.
        """
        repo = _write(tmp_path / "repo.toml", '[telemetry]\nservice_name = "from-repo"\n')
        user = _write(tmp_path / "user.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4319"\n')
        status, rec, err = _run(
            tmp_path, extra=["--config", str(repo), "--user-config", str(user)])

        assert status == 0, err
        # The record floor comes first: every claim below is quantified over
        # emitted records, and a run that emitted none satisfies all of them.
        assert len(rec.records) == 1, err
        assert rec.destinations == [("http", "127.0.0.1", 4319)]
        assert rec.service_name() == "from-repo"

    def test_the_repository_scope_wins_a_setting_both_declare(self, tmp_path):
        """Disjoint settings prove arrival, not precedence.

        A disjoint fixture stays green when the two paths are swapped, so
        precedence needs a case where both scopes declare the same key.
        """
        repo = _write(tmp_path / "repo.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n'
                      'service_name = "from-repo"\n')
        user = _write(tmp_path / "user.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4319"\n'
                      'service_name = "from-user"\n')
        status, rec, err = _run(
            tmp_path, extra=["--config", str(repo), "--user-config", str(user)])

        assert status == 0, err
        assert len(rec.records) == 1
        assert rec.destinations == [("http", "127.0.0.1", 4318)]
        assert rec.service_name() == "from-repo"

    def test_an_absent_file_in_either_scope_contributes_nothing(self, tmp_path):
        user = _write(tmp_path / "user.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4319"\n')
        status, rec, err = _run(
            tmp_path,
            extra=["--config", str(tmp_path / "absent.toml"), "--user-config", str(user)])

        assert status == 0, err
        assert rec.destinations == [("http", "127.0.0.1", 4319)]


# --- AC-0076: the read is unconditional --------------------------------------

class TestTheReadIsUnconditional:
    """The ordering control, parameterized over BOTH axes.

    Two independent shortcuts have to be excluded, and one axis cannot see the
    other. Varying only the endpoint source leaves a build that always validates
    `--config` but skips `--user-config` once an endpoint is already resolved —
    a regression the second flag newly makes possible — passing every arm.
    Varying only the scope leaves the original shortcut, reading neither file
    unless both environment variables are absent. Eight combinations, and each
    must refuse.
    """

    @pytest.mark.parametrize("env,endpoint_in", [
        ({"OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "http://127.0.0.1:4318/v1/logs"}, None),
        ({"OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318"}, None),
        ({}, "repo"),
        ({}, "user"),
    ], ids=["logs-var", "base-var", "config-file", "user-config-file"])
    @pytest.mark.parametrize("bad_key_in", ["repo", "user"], ids=["bad-in-repo", "bad-in-user"])
    def test_an_inadmissible_key_is_refused_whatever_supplies_the_endpoint(
        self, tmp_path, env, endpoint_in, bad_key_in
    ):
        bodies = {"repo": "[telemetry]\n", "user": "[telemetry]\n"}
        bodies[bad_key_in] += 'not_a_setting = "x"\n'
        if endpoint_in == "repo":
            bodies["repo"] += 'endpoint = "http://127.0.0.1:4318"\n'
        elif endpoint_in == "user":
            bodies["user"] += 'endpoint = "http://127.0.0.1:4319"\n'
        repo = _write(tmp_path / "repo.toml", bodies["repo"])
        user = _write(tmp_path / "user.toml", bodies["user"])

        status, rec, err = _run(
            tmp_path, env=env,
            extra=["--config", str(repo), "--user-config", str(user)])

        assert status == 1, err
        assert "not_a_setting" in err
        assert rec.destinations == [], "nothing may be sent when a key is refused"


# --- AC-0075: the closed key set, and naming where a key came from -----------

class TestInadmissibleKeys:
    def test_the_refusal_names_the_repository_file(self, tmp_path):
        repo = _write(tmp_path / "repo.toml", '[telemetry]\nbogus = "x"\n')
        user = _write(tmp_path / "user.toml", "[telemetry]\n")
        with pytest.raises(cfg.ConfigRefused) as caught:
            cfg.resolve_telemetry(repo, user)
        message = str(caught.value)
        assert "repository" in message and str(repo) in message
        assert "user" not in message.split("(from", 1)[1].split(")", 1)[0]

    def test_the_refusal_names_the_user_file(self, tmp_path):
        repo = _write(tmp_path / "repo.toml", "[telemetry]\n")
        user = _write(tmp_path / "user.toml", '[telemetry]\nbogus = "x"\n')
        with pytest.raises(cfg.ConfigRefused) as caught:
            cfg.resolve_telemetry(repo, user)
        message = str(caught.value)
        assert "user" in message and str(user) in message
        assert str(repo) not in message

    def test_a_key_in_both_files_names_both(self, tmp_path):
        """A key present in both must not read as a key present in one.

        The merged mapping has already lost which file each key came from, so a
        build reporting from the merged view alone can only name one.
        """
        repo = _write(tmp_path / "repo.toml", '[telemetry]\nbogus = "x"\n')
        user = _write(tmp_path / "user.toml", '[telemetry]\nbogus = "y"\n')
        with pytest.raises(cfg.ConfigRefused) as caught:
            cfg.resolve_telemetry(repo, user)
        message = str(caught.value)
        assert str(repo) in message and str(user) in message

    def test_the_message_lists_the_admitted_settings(self, tmp_path):
        repo = _write(tmp_path / "repo.toml", '[telemetry]\nbogus = "x"\n')
        with pytest.raises(cfg.ConfigRefused) as caught:
            cfg.resolve_telemetry(repo, None)
        assert "endpoint" in str(caught.value)
        assert "service_name" in str(caught.value)

    def test_every_admitted_setting_is_accepted(self, tmp_path):
        """The closed set must admit what it claims to admit.

        Paired with the refusal cases above: a build refusing everything passes
        all of them and fails this one.
        """
        repo = _write(
            tmp_path / "repo.toml",
            '[telemetry]\nendpoint = "http://127.0.0.1:4318"\nservice_name = "s"\n')
        assert cfg.resolve_telemetry(repo, None) == {
            "endpoint": "http://127.0.0.1:4318", "service_name": "s"}


class TestHostileContentIsEscaped:
    def test_a_key_carrying_control_characters_cannot_forge_a_line(self, tmp_path):
        """Keys come from an untrusted file and reach a terminal."""
        repo = _write(tmp_path / "repo.toml",
                      '[telemetry]\n"a\\nb\\u001b[31m" = "x"\n')
        with pytest.raises(cfg.ConfigRefused) as caught:
            cfg.resolve_telemetry(repo, None)
        message = str(caught.value)
        assert "\\n" in message and "\\x1b" in message
        assert "\n" not in message, "a newline in a key must not split the message"
        assert "\x1b" not in message, "an escape sequence must not reach the terminal"

    def test_a_hostile_key_is_escaped_in_the_bad_value_message_too(self, tmp_path):
        """Two messages name a key, and each needs its own case.

        The case above carries a *valid* value, so it reaches the
        undeliverable-key message. A hostile key with a bad value reaches the
        non-empty-string message instead — a different format string, which a
        mutation dropping its `!r` proved was otherwise unexercised.
        """
        repo = _write(tmp_path / "repo.toml",
                      '[telemetry]\n"a\\nb\\u001b[31m" = ""\n')
        with pytest.raises(cfg.ConfigRefused, match="non-empty string") as caught:
            cfg.resolve_telemetry(repo, None)
        message = str(caught.value)
        assert "\n" not in message, "a newline in a key must not split the message"
        assert "\x1b" not in message, "an escape sequence must not reach the terminal"

    # Every refusal this module can raise with a hostile filename, walked. One
    # case per message rather than a representative: a reviewer found the
    # unknown-key message escaping its path while eight other messages did not,
    # so a single case is exactly the control that passed while the gap shipped.
    #
    # `config.py` raises `ConfigRefused` from twelve message-construction
    # sites, and all twelve are walked here. Eleven format their own message
    # inline; the twelfth is `_acquisition_bound_refused`, the one place both
    # of `_run_bounded`'s two refusals -- a deadline already spent, and a join
    # that timed out -- construct their (identical) message, so walking it
    # through either branch proves both escape. Before that extraction there
    # were thirteen raise statements for twelve distinct messages, and an arm
    # here for only one of the two identical-message sites; the coordinator
    # who found that gap also supplied the fix, folding the duplicate into
    # one site rather than adding a second arm for a message that cannot
    # drift from itself.
    #
    # The short-read, grown and acquisition-timeout sites each need a
    # substituted `os.read` -- neither a real short read, a real
    # same-instant growth nor a genuine hang can be forced on a local regular
    # file under the ceiling, which is what `TestShortRead`,
    # `TestExactCeilingGrowthRace` and `TestAcquisitionBound` in
    # `test_config.py` record -- but the substitution is orthogonal to the
    # claim under test: the hostile name is still this arm's own file, so the
    # message it formats still carries the hostile path. A case where this
    # arm's assertion could be satisfied by another site's message is exactly
    # how a previous delivery shipped an escaping control that covered one
    # site of ten -- hence one arm per site, mutated individually.
    @pytest.mark.parametrize("kind", [
        "unknown-key", "bad-value", "non-table", "bad-toml", "oversized",
        "not-regular", "hard-link", "reparse", "open-error", "short-read",
        "grown", "growth-residue", "acquisition-timeout",
    ])
    def test_every_refusal_escapes_a_hostile_path(self, tmp_path, kind, monkeypatch):
        """The path is caller-supplied and reaches the same terminal as the key."""
        hostile = tmp_path / "we\nird\x1b[31m.toml"
        release = None
        if kind == "unknown-key":
            hostile.write_text('[telemetry]\nbogus = "x"\n', encoding="utf-8")
        elif kind == "bad-value":
            hostile.write_text('[telemetry]\nendpoint = ""\n', encoding="utf-8")
        elif kind == "non-table":
            hostile.write_text('telemetry = "not a table"\n', encoding="utf-8")
        elif kind == "bad-toml":
            hostile.write_text("[telemetry\n", encoding="utf-8")
        elif kind == "oversized":
            hostile.write_text("# " + "x" * (cfg.MAX_CONFIG_BYTES + 1),
                               encoding="utf-8")
        elif kind == "not-regular":
            hostile.mkdir()
        elif kind == "hard-link":
            real = _write(tmp_path / "real.toml",
                          '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
            try:
                os.link(real, hostile)
            except OSError:  # pragma: no cover - platform without hard links
                pytest.skip("hard links unavailable")
        elif kind == "reparse":
            # Same technique as `test_a_reparse_point_is_refused`: no POSIX
            # filesystem sets the attribute, so the `os.fstat` result the reader
            # inspects is substituted. The file itself is ordinary; only the
            # attribute is forced, so the refusal under test is the reparse one.
            hostile.write_text('[telemetry]\nendpoint = "http://127.0.0.1:4318"\n',
                               encoding="utf-8")
            attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            genuine_fstat = os.fstat

            class _Stat:
                """Mirrors the real result, with the reparse attribute set."""

                def __init__(self, inner):
                    self._inner = inner
                    self.st_file_attributes = attribute

                def __getattr__(self, name):
                    return getattr(self._inner, name)

            monkeypatch.setattr(
                cfg.os, "fstat", lambda fd: _Stat(genuine_fstat(fd)))
        elif kind == "open-error":
            # `O_NOFOLLOW` on a symlink fails the `open` itself with ELOOP, which
            # is the open-error message. A FIFO does not reach it: `O_NONBLOCK`
            # makes the open succeed and the descriptor check then reports
            # not-a-regular-file, which the `not-regular` arm above already owns.
            target = _write(tmp_path / "real.toml",
                            '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
            try:
                hostile.symlink_to(target)
            except OSError:  # pragma: no cover - platform without symlinks
                pytest.skip("symlinks unavailable")
        elif kind == "short-read":
            # Same technique as `TestShortRead` in `test_config.py`: the file is
            # ordinary and valid, and `os.read` is substituted to return fewer
            # bytes than `fstat` reported. Only the read length is forced, so the
            # refusal under test is the short-read one -- and the path it formats
            # is still this arm's hostile name.
            hostile.write_text('[telemetry]\nendpoint = "http://127.0.0.1:4318"\n',
                               encoding="utf-8")
            genuine_read = os.read
            monkeypatch.setattr(
                cfg.os, "read",
                lambda fd, size: genuine_read(fd, size)[:1])
        elif kind == "grown":
            # Armed at exactly the ceiling, then grown through a second
            # descriptor from inside a substituted `os.read` -- the
            # concurrent-writer race `TestExactCeilingGrowthRace` in
            # `test_config.py` exercises directly. Only the re-sampled
            # `fstat` -- not the sampled-size or short-read checks -- can
            # catch this, so it needs its own site and its own message.
            head = '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n#'
            hostile.write_text(
                head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)), encoding="utf-8")
            assert hostile.stat().st_size == cfg.MAX_CONFIG_BYTES
            genuine_read = os.read

            def grow_then_read(fd, size):
                with hostile.open("ab") as second_descriptor:
                    second_descriptor.write(b"y")
                return genuine_read(fd, size)

            monkeypatch.setattr(cfg.os, "read", grow_then_read)
        elif kind == "growth-residue":
            # T2/AC-0001 follow-up. The residue the buffer and the re-sample
            # together still leave: a substituted read returns exactly the
            # sampled ceiling length even though the file has grown for real
            # underneath it, AND the re-sampled `fstat` reports the
            # pre-growth size -- so neither the "changed" check nor the
            # short-read comparison can catch it. Only the trailing
            # single-byte probe (run after both) still finds an unread byte
            # on the descriptor. Same technique as
            # `test_growth_hidden_by_a_capped_read_and_a_stale_resample_is_caught_by_the_probe`
            # in `test_config.py`.
            head = '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n#'
            hostile.write_text(
                head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)), encoding="utf-8")
            assert hostile.stat().st_size == cfg.MAX_CONFIG_BYTES
            genuine_read = os.read
            genuine_fstat = os.fstat
            calls = {"n": 0}

            def capped_read_after_growth(fd, size):
                if size == 1:
                    return genuine_read(fd, size)
                with hostile.open("ab") as second_descriptor:
                    second_descriptor.write(b"y")
                return genuine_read(fd, cfg.MAX_CONFIG_BYTES)

            def first_genuine_then_stale_fstat(fd):
                calls["n"] += 1
                if calls["n"] == 1:
                    return genuine_fstat(fd)
                genuine = genuine_fstat(fd)

                class _StaleStat:
                    def __init__(self, inner):
                        self._inner = inner

                    def __getattr__(self, name):
                        return getattr(self._inner, name)

                    @property
                    def st_size(self):
                        return cfg.MAX_CONFIG_BYTES

                return _StaleStat(genuine)

            monkeypatch.setattr(cfg.os, "read", capped_read_after_growth)
            monkeypatch.setattr(cfg.os, "fstat", first_genuine_then_stale_fstat)
        elif kind == "acquisition-timeout":
            # T3/AC-0077. A substituted `os.read` that blocks past the
            # (monkeypatched, short) acquisition bound rather than a real
            # short read or growth -- `TestAcquisitionBound` in
            # `test_config.py` exercises the three blocking syscalls
            # directly. Released in `finally` below so the abandoned worker
            # ends with this case rather than outliving the session.
            hostile.write_text('[telemetry]\nendpoint = "http://127.0.0.1:4318"\n',
                                encoding="utf-8")
            monkeypatch.setattr(cfg, "_CONFIG_TIMEOUT_SECONDS", 0.2)
            release = threading.Event()
            genuine_read = os.read

            def blocking_read(fd, size):
                release.wait()
                return genuine_read(fd, size)

            monkeypatch.setattr(cfg.os, "read", blocking_read)

        before_threads = set(threading.enumerate())
        try:
            with pytest.raises(cfg.ConfigRefused) as caught:
                cfg.resolve_telemetry(hostile, None)
        finally:
            if release is not None:
                release.set()
                await_released_workers(before_threads)
        message = str(caught.value)
        if kind == "reparse":
            assert "reparse point" in message, message
        elif kind == "open-error":
            assert "refused at open" in message, message
        elif kind == "short-read":
            assert "read returned" in message, message
        elif kind == "grown":
            assert "changed" in message, message
        elif kind == "growth-residue":
            assert "beyond" in message, message
        elif kind == "acquisition-timeout":
            assert "bound" in message, message
        assert "\n" not in message, (
            f"a newline in a path split the {kind} message: {message!r}")
        assert "\x1b" not in message, (
            f"an escape sequence reached the terminal in the {kind} message")


class TestMalformedTelemetryTables:
    def test_a_non_table_telemetry_value_is_refused(self, tmp_path):
        repo = _write(tmp_path / "repo.toml", 'telemetry = "not a table"\n')
        with pytest.raises(cfg.ConfigRefused, match="must be a table"):
            cfg.resolve_telemetry(repo, None)

    @pytest.mark.parametrize("body", [
        '[telemetry]\nendpoint = 4318\n',
        '[telemetry]\nendpoint = ""\n',
        '[telemetry]\nendpoint = "   "\n',
        '[telemetry]\nendpoint = true\n',
    ], ids=["integer", "empty", "whitespace", "boolean"])
    def test_a_value_that_is_not_a_non_empty_string_is_refused(self, tmp_path, body):
        repo = _write(tmp_path / "repo.toml", body)
        with pytest.raises(cfg.ConfigRefused, match="non-empty string"):
            cfg.resolve_telemetry(repo, None)

    def test_a_file_with_no_telemetry_table_contributes_nothing(self, tmp_path):
        repo = _write(tmp_path / "repo.toml", '[other]\nkey = "value"\n')
        assert cfg.resolve_telemetry(repo, None) == {}


# --- AC-0062: the second scope takes the same descriptor discipline ----------

class TestUserConfigDescriptorDiscipline:
    def test_a_symlinked_user_config_is_refused(self, tmp_path):
        real = _write(tmp_path / "real.toml", '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        link = tmp_path / "link.toml"
        try:
            link.symlink_to(real)
        except OSError:  # pragma: no cover - platform without symlink privilege
            pytest.skip("symlinks unavailable")
        with pytest.raises(cfg.ConfigRefused):
            cfg.resolve_telemetry(None, link)

    def test_a_hard_linked_user_config_is_refused(self, tmp_path):
        """A second name for the same bytes can be rewritten after the check.

        `S_ISREG` passes a hard link, so a build asserting only regular-file-ness
        admits it and fails nothing else in this module.
        """
        real = _write(tmp_path / "real.toml", '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        linked = tmp_path / "linked.toml"
        try:
            os.link(real, linked)
        except OSError:  # pragma: no cover - platform without hard-link support
            pytest.skip("hard links unavailable")
        with pytest.raises(cfg.ConfigRefused, match="hard-linked"):
            cfg.resolve_telemetry(None, linked)

    def test_a_reparse_point_is_refused(self, tmp_path, monkeypatch):
        """The Windows redirection primitive `O_NOFOLLOW` does not catch.

        No POSIX filesystem produces `FILE_ATTRIBUTE_REPARSE_POINT`, so the
        branch is driven by substituting the `os.fstat` result the reader
        inspects. That tests the guard rather than the platform: without it the
        branch ships unexercised on every machine this suite runs on, which is
        the shape a reviewer caught in the first version of these controls.
        """
        real = _write(tmp_path / "real.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        genuine_fstat = os.fstat

        class _Stat:
            """Mirrors the real result, with the reparse attribute set."""

            def __init__(self, inner):
                self._inner = inner
                self.st_file_attributes = attribute

            def __getattr__(self, name):
                return getattr(self._inner, name)

        # Only `os.fstat` is substituted. Rebinding `cfg.stat` would be a no-op:
        # it already *is* the real `stat` module, and `FILE_ATTRIBUTE_REPARSE_POINT`
        # is defined there on every platform, so the attribute lookup needs no help.
        monkeypatch.setattr(
            cfg.os, "fstat", lambda fd: _Stat(genuine_fstat(fd)))
        with pytest.raises(cfg.ConfigRefused, match="reparse point"):
            cfg.resolve_telemetry(None, real)

    def test_a_reparse_attribute_of_zero_is_not_a_reparse_point(self, tmp_path):
        """The paired case: the guard must not refuse an ordinary file.

        A build raising unconditionally in that branch passes the case above and
        fails here, so the two together pin the condition rather than the raise.
        """
        real = _write(tmp_path / "real.toml",
                      '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        assert cfg.resolve_telemetry(None, real) == {
            "endpoint": "http://127.0.0.1:4318"}

    def test_a_directory_at_the_user_config_path_is_refused(self, tmp_path):
        target = tmp_path / "a-directory"
        target.mkdir()
        with pytest.raises(cfg.ConfigRefused):
            cfg.resolve_telemetry(None, target)

    def test_an_oversized_user_config_is_refused_before_it_is_parsed(self, tmp_path):
        big = tmp_path / "big.toml"
        big.write_text("# " + "x" * (cfg.MAX_CONFIG_BYTES + 1), encoding="utf-8")
        with pytest.raises(cfg.ConfigRefused, match="ceiling"):
            cfg.resolve_telemetry(None, big)

    def test_a_user_config_outside_the_input_root_is_accepted(self, tmp_path):
        """AC-0062 imposes no `--root` confinement, and the second scope is why.

        A user-scope configuration file lives outside any data root by
        definition, so a build reusing `--input`'s predicate here refuses a
        correct invocation.
        """
        root = tmp_path / "repo"
        (root / ".loop-run").mkdir(parents=True)
        outside = _write(tmp_path / "elsewhere.toml",
                         '[telemetry]\nendpoint = "http://127.0.0.1:4320"\n')
        events = root / ".loop-run" / "events.jsonl"
        events.write_text(GOOD_LINE, encoding="utf-8")
        profile = _write(root / "work-loop.toml", REFERENCE_PROFILE)
        rec = _Recorder()
        stream = io.StringIO()
        status = cli.main(
            ["--input", str(events), "--root", str(root), "--profile", str(profile),
             "--user-config", str(outside)],
            env={}, stream=stream, out=io.StringIO(), connection_factory=rec.factory,
        )
        assert status == 0, stream.getvalue()
        assert rec.destinations == [("http", "127.0.0.1", 4320)]


# --- AC-0007: four sources for service.name, in order ------------------------

class TestServiceNamePrecedence:
    """One fixture, four sources, each removed in turn.

    Every arm carries a distinct value, so an implementation collapsing any two
    sources fails here rather than agreeing with itself.
    """

    # Loopback addresses, and distinct ports rather than distinct hostnames:
    # `resolve_destination` performs real name resolution, and the Boundaries
    # require HTTPS for any host that is not loopback -- so an invented hostname
    # fails on DNS or on scheme before reaching the behaviour under test.
    def _fixture(self, tmp_path):
        _write(tmp_path / "repo.toml",
               '[telemetry]\nendpoint = "http://127.0.0.1:4318"\nservice_name = "from-config"\n')
        _write(tmp_path / "user.toml", '[telemetry]\nservice_name = "from-user"\n')
        return ["--config", str(tmp_path / "repo.toml"),
                "--user-config", str(tmp_path / "user.toml")]

    def test_the_flag_outranks_every_file(self, tmp_path):
        extra = self._fixture(tmp_path) + ["--service-name", "from-flag"]
        status, rec, err = _run(tmp_path, extra=extra)
        assert status == 0, err
        assert rec.service_name() == "from-flag"

    def test_the_config_file_outranks_the_user_file(self, tmp_path):
        status, rec, err = _run(tmp_path, extra=self._fixture(tmp_path))
        assert status == 0, err
        assert rec.service_name() == "from-config"

    def test_the_user_file_is_used_when_the_config_file_omits_it(self, tmp_path):
        _write(tmp_path / "repo.toml", '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        _write(tmp_path / "user.toml", '[telemetry]\nservice_name = "from-user"\n')
        status, rec, err = _run(tmp_path, extra=[
            "--config", str(tmp_path / "repo.toml"),
            "--user-config", str(tmp_path / "user.toml")])
        assert status == 0, err
        assert rec.service_name() == "from-user"

    def test_the_profile_stem_is_the_final_default(self, tmp_path):
        _write(tmp_path / "repo.toml", '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n')
        status, rec, err = _run(
            tmp_path, extra=["--config", str(tmp_path / "repo.toml")])
        assert status == 0, err
        assert rec.service_name() == "work-loop"
