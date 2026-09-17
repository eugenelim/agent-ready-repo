"""T2 — configuration resolution: endpoint precedence and file acquisition.

Covers AC-0002, AC-0003, AC-0004, AC-0056, AC-0062.

Every case here runs with no network. AC-0001's off-by-default proof is not
here: it lives on the path that actually ships, as
`test_the_unconfigured_cli_path_constructs_no_connection` in `test_cli.py`,
because a construction proof about a helper the CLI never calls passed while a
build opened a socket before the unconfigured return.
"""

from __future__ import annotations

import os
import pathlib
import stat
import subprocess
import sys
import textwrap
import threading
import time

import pytest
from conftest import await_released_workers
from jsonl_otlp_exporter import config as cfg


def _write(path, text: str):
    path.write_text(text, encoding="utf-8")
    return path


class TestEndpointPrecedence:
    """AC-0002 — first present of LOGS_ENDPOINT, ENDPOINT, then the config files."""

    def test_logs_endpoint_wins_over_both_others(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {
                "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "https://logs:4318/v1/logs",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318",
            },
            cfg.resolve_telemetry(config),
        )
        assert resolved == "https://logs:4318/v1/logs"

    def test_base_endpoint_wins_over_the_config_file(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318"}, cfg.resolve_telemetry(config)
        )
        assert resolved == "https://base:4318/v1/logs"

    def test_config_file_is_used_when_no_variable_is_present(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        assert cfg.resolve_endpoint({}, cfg.resolve_telemetry(config)) == "https://file:4318/v1/logs"

    def test_an_empty_variable_is_not_present(self, tmp_path):
        """An exported-but-empty variable must not shadow the next source.

        This is the case a truthiness check gets right and a `in env` check gets
        wrong, and it is how a shell export of an unset value silently disables
        a configured endpoint.
        """
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            cfg.resolve_telemetry(config),
        )
        assert resolved == "https://file:4318/v1/logs"


class TestEndpointTransformation:
    """AC-0003 — the logs variable is unmodified. AC-0004 — everything else gains /v1/logs."""

    def test_logs_endpoint_is_requested_unmodified(self):
        # Deliberately NOT already ending in /v1/logs: a build that appends
        # unconditionally, and one that appends only when absent, both fail here.
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "https://logs:4318/custom/path"},
            None,
        )
        assert resolved == "https://logs:4318/custom/path"

    def test_base_endpoint_gains_the_signal_path(self):
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318"}, None
        )
        assert resolved == "https://base:4318/v1/logs"

    def test_a_trailing_slash_does_not_double(self):
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318/"}, None
        )
        assert resolved == "https://base:4318/v1/logs"


class TestOffByDefault:
    """AC-0002 — with no source present, no endpoint resolves at all."""

    def test_no_source_resolves_to_nothing(self):
        assert cfg.resolve_endpoint({}, None) is None


class TestConfigFileAcquisition:
    """AC-0056 — the size ceiling. AC-0062 — what is opened, proven on the descriptor."""

    def test_a_file_over_64_kib_is_refused_before_parsing(self, tmp_path):
        # Valid TOML, so only the size check can reject it. A build that parses
        # first and measures afterwards passes a size check and fails this.
        padding = "#" + "x" * (64 * 1024)
        config = _write(tmp_path / "big.toml", f'[telemetry]\nendpoint = "https://c:4318"\n{padding}\n')
        assert config.stat().st_size > cfg.MAX_CONFIG_BYTES
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(config)

    def test_a_file_at_exactly_the_ceiling_is_accepted(self, tmp_path):
        """The boundary belongs to the accepted side; an off-by-one rejects a legal file."""
        head = '[telemetry]\nendpoint = "https://c:4318"\n#'
        config = _write(tmp_path / "exact.toml", head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)))
        assert config.stat().st_size == cfg.MAX_CONFIG_BYTES
        assert cfg.read_config_file(config)["telemetry"]["endpoint"] == "https://c:4318"

    def test_a_symlink_is_refused(self, tmp_path):
        real = _write(tmp_path / "real.toml", '[telemetry]\nendpoint = "https://c:4318"\n')
        link = tmp_path / "link.toml"
        try:
            link.symlink_to(real)
        except OSError:  # Windows without developer mode
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(link)

    def test_a_fifo_is_refused(self, tmp_path):
        if not hasattr(os, "mkfifo"):  # Windows has no FIFO
            pytest.skip("FIFOs unavailable on this platform")
        fifo = tmp_path / "fifo.toml"
        os.mkfifo(fifo)
        assert stat.S_ISFIFO(os.lstat(fifo).st_mode)
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(fifo)

    def test_a_directory_is_refused(self, tmp_path):
        d = tmp_path / "dir.toml"
        d.mkdir()
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(d)

    def test_a_regular_file_outside_any_root_is_accepted(self, tmp_path):
        """AC-0062 imposes no --root confinement, and this is the case that proves it.

        A build that reuses --input's confined-open predicate passes every
        refusal case above and fails here, which is the whole point of the split.
        """
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        outside = _write(elsewhere / "c.toml", '[telemetry]\nendpoint = "https://c:4318"\n')
        assert cfg.read_config_file(outside)["telemetry"]["endpoint"] == "https://c:4318"

    def test_an_absent_config_path_is_not_a_refusal(self, tmp_path):
        """`--config` is optional: absent means "this source contributes nothing"."""
        assert cfg.read_config_file(tmp_path / "missing.toml") == {}

    def test_unparseable_toml_is_refused(self, tmp_path):
        config = _write(tmp_path / "bad.toml", "[telemetry\nendpoint =\n")
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(config)


class TestShortRead:
    """A short read must not be parsed as if it were the whole file.

    `os.read` is one `read(2)` and may return fewer bytes than requested. A
    prefix of a TOML file can itself be valid TOML, so parsing one would accept
    an incomplete config as complete -- and enable sending from a file whose full
    content does not parse.

    A real short read cannot be forced on a local regular file, which is why the
    defect is recorded as unreachable there and reachable on a network or FUSE
    mount. It is driven through a substituted read instead, so the length
    comparison cannot be deleted silently.
    """

    def test_a_valid_prefix_shorter_than_the_file_is_refused(self, tmp_path, monkeypatch):
        config = _write(
            tmp_path / "c.toml",
            '[telemetry]\nendpoint = "https://c:4318"\n[oops\nnot valid toml at all\n',
        )
        prefix = b'[telemetry]\nendpoint = "https://c:4318"\n'
        real_read = os.read

        def short_read(fd, size):
            return prefix if size >= len(prefix) else real_read(fd, size)

        monkeypatch.setattr(os, "read", short_read)
        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.read_config_file(config)
        assert "bytes" in str(excinfo.value)

    def test_a_complete_read_is_still_accepted(self, tmp_path):
        """The other half: the comparison must not reject a normal file."""
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://c:4318"\n')
        assert cfg.read_config_file(config)["telemetry"]["endpoint"] == "https://c:4318"


class TestExactCeilingGrowthRace:
    """AC-0001/AC-0056 -- a file sampled at exactly the ceiling that grows
    before its bytes are fully read must be refused, not silently truncated to
    the sampled length and accepted.

    `test_a_file_at_exactly_the_ceiling_is_accepted` (above, in
    `TestConfigFileAcquisition`) already covers the non-growing side of this
    pair: a file exactly at the ceiling that does NOT grow must still parse.
    Reused rather than duplicated here.
    """

    @staticmethod
    def _armed_at_the_ceiling(tmp_path, name):
        """A valid TOML file whose size samples at exactly `MAX_CONFIG_BYTES`."""
        head = '[telemetry]\nendpoint = "https://c:4318"\n#'
        config = _write(tmp_path / name, head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)))
        assert config.stat().st_size == cfg.MAX_CONFIG_BYTES
        return config

    def test_growth_between_the_sample_and_the_read_is_refused(self, tmp_path, monkeypatch):
        """Armed at the ceiling, then appended to through a second descriptor
        between the `fstat` sample and the `read` -- the concurrent-writer race
        the defect describes. The single `read(2)` still returns the grown
        content (measured: 65,537 of 65,537 requested), so only the re-sampled
        size -- not the short-read comparison -- can catch it."""
        config = self._armed_at_the_ceiling(tmp_path, "grows.toml")
        real_read = os.read

        def grow_then_read(fd, size):
            with config.open("ab") as second_descriptor:
                second_descriptor.write(b"y")
            return real_read(fd, size)

        monkeypatch.setattr(os, "read", grow_then_read)
        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.read_config_file(config)
        assert "changed" in str(excinfo.value)

    def test_growth_a_short_read_hides_is_still_caught_by_the_resample(
        self, tmp_path, monkeypatch
    ):
        """The residue the `MAX_CONFIG_BYTES + 1` buffer alone cannot close: a
        substituted read returns exactly the sampled ceiling length -- as a
        short read on a network or FUSE mount plausibly would -- even though
        the file underneath has already grown past it. The length comparison
        against the sample matches (both are `MAX_CONFIG_BYTES`), so only the
        re-sampled `fstat` -- run before that comparison -- can catch this."""
        config = self._armed_at_the_ceiling(tmp_path, "grows_hidden.toml")
        real_read = os.read

        def short_read_after_growth(fd, size):
            with config.open("ab") as second_descriptor:
                second_descriptor.write(b"y" * 200_000)
            return real_read(fd, cfg.MAX_CONFIG_BYTES)

        monkeypatch.setattr(os, "read", short_read_after_growth)
        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.read_config_file(config)
        assert "changed" in str(excinfo.value)

    def test_growth_the_resample_cannot_see_because_fstat_is_stale(
        self, tmp_path, monkeypatch
    ):
        """This is the case that proves the `MAX_CONFIG_BYTES + 1` buffer is
        load-bearing, not redundant with the re-sample -- without it, a later
        reader has no reason not to delete the extra byte as dead weight.

        The re-sample refuses by comparing a SECOND `fstat` against the
        first. If that second `fstat` itself reports a stale size -- as a
        network or FUSE mount's cached attributes plausibly would, even
        though a real `read(2)` on the same descriptor already reflects the
        grown content -- the re-sample sees no change and cannot catch the
        growth on its own. Only the extra byte actually landing in `raw`
        catches this case, through the pre-existing short-read comparison
        (`len(raw) != info.st_size`), which is why the message here is the
        short-read one rather than the "changed" one: the resample genuinely
        saw nothing to report.
        """
        config = self._armed_at_the_ceiling(tmp_path, "grows_stale_fstat.toml")
        real_read = os.read
        real_fstat = os.fstat
        calls = {"n": 0}

        def grow_then_read(fd, size):
            with config.open("ab") as second_descriptor:
                second_descriptor.write(b"y")
            return real_read(fd, size)

        def first_genuine_then_stale_fstat(fd):
            calls["n"] += 1
            if calls["n"] == 1:
                return real_fstat(fd)
            # The second call (the re-sample) reports the file unchanged at
            # the original ceiling, even though the read above already grew
            # it -- the cached-metadata divergence a real `fstat` and a real
            # `read` can have on a network or FUSE mount.
            genuine = real_fstat(fd)

            class _StaleStat:
                def __init__(self, inner):
                    self._inner = inner

                def __getattr__(self, name):
                    return getattr(self._inner, name)

                @property
                def st_size(self):
                    return cfg.MAX_CONFIG_BYTES

            return _StaleStat(genuine)

        monkeypatch.setattr(os, "read", grow_then_read)
        monkeypatch.setattr(os, "fstat", first_genuine_then_stale_fstat)
        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.read_config_file(config)
        assert "bytes" in str(excinfo.value)
        assert "changed" not in str(excinfo.value), (
            "the stale fstat must not have been able to see the growth -- "
            "if it did, this arm is not exercising what it claims to")

    def test_growth_hidden_by_a_capped_read_and_a_stale_resample_is_caught_by_the_probe(
        self, tmp_path, monkeypatch
    ):
        """The residue the buffer and the re-sample together still leave: a
        substituted read returns exactly the sampled ceiling length even
        though the file has grown for real underneath it, AND the re-sampled
        `fstat` reports the pre-growth size -- so neither the short-read
        comparison nor the size-changed check can catch it. Only the
        trailing single-byte probe, run after both, still finds an unread
        byte on the descriptor and refuses.

        Without the probe this file is silently accepted and parsed: `raw`
        matches the sample in length, the (stale) re-sample matches the
        sample too, and the extra byte is never looked at."""
        config = self._armed_at_the_ceiling(tmp_path, "grows_stale_and_capped.toml")
        real_read = os.read
        real_fstat = os.fstat
        calls = {"n": 0}

        def capped_read_after_growth(fd, size):
            if size == 1:
                # The probe -- pass through untouched, so it sees the real,
                # grown file rather than a substituted view.
                return real_read(fd, size)
            with config.open("ab") as second_descriptor:
                second_descriptor.write(b"y")
            # Capped at the sampled length despite the real growth -- the
            # short read a network or FUSE mount can plausibly return.
            return real_read(fd, cfg.MAX_CONFIG_BYTES)

        def first_genuine_then_stale_fstat(fd):
            calls["n"] += 1
            if calls["n"] == 1:
                return real_fstat(fd)
            genuine = real_fstat(fd)

            class _StaleStat:
                def __init__(self, inner):
                    self._inner = inner

                def __getattr__(self, name):
                    return getattr(self._inner, name)

                @property
                def st_size(self):
                    return cfg.MAX_CONFIG_BYTES

            return _StaleStat(genuine)

        monkeypatch.setattr(os, "read", capped_read_after_growth)
        monkeypatch.setattr(os, "fstat", first_genuine_then_stale_fstat)
        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.read_config_file(config)
        assert "beyond" in str(excinfo.value)
        assert "changed" not in str(excinfo.value), (
            "the stale fstat must not have been able to see the growth -- "
            "if it did, this arm is not exercising what it claims to")


class TestAcquisitionBound:
    """AC-0002/AC-0077 -- the open, the descriptor proof and the read all run
    on one abandonable worker, bounded by a deadline established before the
    first file is opened. Each case substitutes exactly one blocking syscall:
    `os.open`, `os.fstat` or `os.read`. They are separate syscalls, and a
    build that moves only some of them onto the worker passes a case written
    for the ones it moved while an unresponsive mount still hangs it on the
    rest -- `fstat` on an open descriptor can block on attribute
    revalidation just as the read can.

    Every substituted call blocks on a `threading.Event` the test releases in
    its `finally`, and each case then joins the released worker before it
    ends -- `release.set()` alone only unblocks the call; joining is what
    establishes that the worker has actually finished, so no abandoned
    worker outlives the case.
    """

    @pytest.fixture(autouse=True)
    def _short_bound(self, monkeypatch):
        # Kept small so the suite stays fast -- a case that actually waited
        # out the real 5-second bound would cost one second-scale sleep per
        # case, times three.
        monkeypatch.setattr(cfg, "_CONFIG_TIMEOUT_SECONDS", 0.2)

    @staticmethod
    def _configured(tmp_path, name="c.toml"):
        config = tmp_path / name
        config.write_text('[telemetry]\nendpoint = "https://c:4318"\n', encoding="utf-8")
        return config

    def test_a_blocking_open_is_refused_within_the_bound(self, tmp_path, monkeypatch):
        config = self._configured(tmp_path)
        release = threading.Event()
        real_open = os.open

        def blocking_open(path, flags):
            release.wait()
            return real_open(path, flags)

        monkeypatch.setattr(cfg.os, "open", blocking_open)
        before_threads = set(threading.enumerate())
        started = time.monotonic()
        try:
            with pytest.raises(cfg.ConfigRefused) as excinfo:
                cfg.read_config_file(config)
        finally:
            release.set()
            await_released_workers(before_threads)
        elapsed = time.monotonic() - started
        assert elapsed < 2, (
            f"a blocking open took {elapsed:.3f}s to refuse against a 0.2s bound")
        assert "bound" in str(excinfo.value)

    def test_a_blocking_descriptor_proof_is_refused_within_the_bound(
        self, tmp_path, monkeypatch
    ):
        """`fstat` on an open descriptor can block on attribute revalidation
        on a network or FUSE mount, just as the read can -- a build that
        bounds only the open and the read still hangs here."""
        config = self._configured(tmp_path)
        release = threading.Event()
        real_fstat = os.fstat

        def blocking_fstat(fd):
            release.wait()
            return real_fstat(fd)

        monkeypatch.setattr(cfg.os, "fstat", blocking_fstat)
        before_threads = set(threading.enumerate())
        started = time.monotonic()
        try:
            with pytest.raises(cfg.ConfigRefused) as excinfo:
                cfg.read_config_file(config)
        finally:
            release.set()
            await_released_workers(before_threads)
        elapsed = time.monotonic() - started
        assert elapsed < 2, (
            f"a blocking fstat took {elapsed:.3f}s to refuse against a 0.2s bound")
        assert "bound" in str(excinfo.value)

    def test_a_blocking_read_is_refused_within_the_bound(self, tmp_path, monkeypatch):
        config = self._configured(tmp_path)
        release = threading.Event()
        real_read = os.read

        def blocking_read(fd, size):
            release.wait()
            return real_read(fd, size)

        monkeypatch.setattr(cfg.os, "read", blocking_read)
        before_threads = set(threading.enumerate())
        started = time.monotonic()
        try:
            with pytest.raises(cfg.ConfigRefused) as excinfo:
                cfg.read_config_file(config)
        finally:
            release.set()
            await_released_workers(before_threads)
        elapsed = time.monotonic() - started
        assert elapsed < 2, (
            f"a blocking read took {elapsed:.3f}s to refuse against a 0.2s bound")
        assert "bound" in str(excinfo.value)

    def test_the_bound_covers_both_files_together_not_one_each(
        self, tmp_path, monkeypatch
    ):
        """AC-0077's subject is the whole acquisition path, not a file at a
        time: `resolve_telemetry` shares one deadline across both scopes, so
        a slow first file must not buy the second one a fresh bound's worth
        of time. Driven by delaying the repository file's open and blocking
        the user file's open on an event that outlives the bound -- if the
        deadline were recomputed per file, the user file would get its own
        full bound after the repository file's delay, landing near double
        the configured bound instead of near one."""
        bound = 0.3
        monkeypatch.setattr(cfg, "_CONFIG_TIMEOUT_SECONDS", bound)
        repo = self._configured(tmp_path, "repo.toml")
        user = tmp_path / "user.toml"
        release = threading.Event()
        real_open = os.open

        def gated_open(path, flags):
            if str(path) == str(user):
                release.wait()
            else:
                time.sleep(bound * 0.67)
            return real_open(path, flags)

        monkeypatch.setattr(cfg.os, "open", gated_open)
        before_threads = set(threading.enumerate())
        started = time.monotonic()
        try:
            with pytest.raises(cfg.ConfigRefused):
                cfg.resolve_telemetry(repo, user)
        finally:
            release.set()
            await_released_workers(before_threads)
        elapsed = time.monotonic() - started
        assert elapsed < bound * 1.5, (
            f"two files took {elapsed:.3f}s against a {bound}s bound -- a "
            "deadline recomputed per file would let the user file buy its "
            f"own {bound}s after the repository file's delay, landing near "
            f"{bound * 2:.2f}s instead of near {bound:.2f}s"
        )

    def test_a_deadline_already_spent_refuses_the_second_file_without_a_worker(
        self, tmp_path, monkeypatch
    ):
        """`_run_bounded`'s `remaining <= 0` branch -- distinct from
        `worker.is_alive()`, which every other case here drives. This is the
        branch that actually carries AC-0077's "one deadline, not one per
        file": the repository file is acquired normally and the user file's
        call to `_run_bounded` finds the shared deadline already spent, so it
        must refuse without ever starting a worker for it.

        Reaching this deterministically by real elapsed time is a race the
        join forbids -- the first file would have to overrun the budget and
        still succeed. Substituting `cfg.time.monotonic` is the same
        technique the other cases use on `cfg.os.read` and `cfg.os.fstat`,
        but keyed by the path currently being acquired rather than by an
        ordinal call count: a thin wrapper around `cfg._run_bounded` tags
        which path is in flight *before* delegating to the real function, so
        the clock substitution reads that tag rather than counting calls.
        Real time flows for the repository file no matter how many internal
        calls its acquisition makes; the user file's own `_run_bounded` call
        is the only one that ever sees a clock jumped past the deadline --
        which is what keeps this case meaningful even against a build that
        splits one file's acquisition into more than one `_run_bounded` call
        (an ordinal count silently drifts under that kind of change, and
        already has: see the ledger).
        """
        repo = self._configured(tmp_path, "repo.toml")
        user = tmp_path / "user.toml"
        user.write_text('[telemetry]\nservice_name = "svc"\n', encoding="utf-8")

        real_monotonic = time.monotonic
        real_open = os.open
        real_run_bounded = cfg._run_bounded
        current_path: dict[str, object] = {"value": None}

        def path_aware_run_bounded(func, path, deadline):
            # Tag which file is in flight before delegating, so the clock
            # substitution below is keyed by the path actually being
            # acquired rather than by how many times this function or
            # `time.monotonic` happen to be called for it.
            current_path["value"] = path
            return real_run_bounded(func, path, deadline)

        monkeypatch.setattr(cfg, "_run_bounded", path_aware_run_bounded)

        def jumping_monotonic():
            if current_path["value"] == user:
                # The user file's own `_run_bounded` remaining-time check:
                # report a time far past the deadline established for
                # `resolve_telemetry`'s shared instant, deterministically,
                # rather than racing real elapsed time against the join.
                return real_monotonic() + 3600
            # Every other caller -- establishing the shared deadline, and
            # any number of internal checks the repository file's own
            # acquisition makes -- sees real time, so the repository file
            # is acquired normally.
            return real_monotonic()

        monkeypatch.setattr(cfg.time, "monotonic", jumping_monotonic)

        def exploding_open(path, flags):
            if str(path) == str(user):
                raise AssertionError(
                    "a worker was started for the user file after its "
                    "shared deadline had already passed")
            return real_open(path, flags)

        monkeypatch.setattr(cfg.os, "open", exploding_open)

        with pytest.raises(cfg.ConfigRefused) as excinfo:
            cfg.resolve_telemetry(repo, user)
        message = str(excinfo.value)
        assert cfg._shown(user) in message, (
            "the refusal must name the SECOND file -- naming the first "
            f"would mean the budget was reset rather than shared: {message}"
        )
        assert cfg._shown(repo) not in message

    def test_an_abandoned_worker_does_not_stop_the_process_exiting(self, tmp_path):
        """The worker is a *daemon*, and that flag is load-bearing, not decor.

        Every other case in this class releases its substituted call at
        teardown, so none of them can observe the flag at all: the worker has
        already finished by the time the interpreter shuts down. The flag only
        matters for the case the bound exists for -- a call that never returns,
        whose worker is genuinely abandoned -- and a non-daemon thread blocked
        there holds the interpreter open at shutdown forever.

        So this drives a real child process and asserts it *exits*. Measured on
        this machine: the shipped reader exits in 0.42s with the worker still
        blocked in `read`; with `daemon=True` removed the child never exits at
        all. `timeout` is what converts that hang into a failed assertion
        rather than a hung suite.
        """
        config = self._configured(tmp_path)
        child = textwrap.dedent(
            """
            import os, sys, threading
            sys.path.insert(0, sys.argv[1])
            from jsonl_otlp_exporter import config as cfg
            cfg._CONFIG_TIMEOUT_SECONDS = 0.1
            # Nothing ever releases this: the worker is abandoned for real,
            # which is the only state in which `daemon=True` has an effect.
            cfg.os.read = lambda fd, size: threading.Event().wait()
            try:
                cfg.read_config_file(sys.argv[2])
            except cfg.ConfigRefused:
                print("REFUSED", flush=True)
            """
        )
        package_root = pathlib.Path(cfg.__file__).resolve().parent.parent
        try:
            done = subprocess.run(
                [sys.executable, "-c", child, str(package_root), str(config)],
                capture_output=True, text=True, timeout=30, check=False,
            )
        except subprocess.TimeoutExpired:  # pragma: no cover - the mutant's path
            pytest.fail(
                "the child never exited: an abandoned acquisition worker held "
                "the interpreter open at shutdown, which is what `daemon=True` "
                "on that worker prevents"
            )
        assert "REFUSED" in done.stdout, (
            f"the child should have refused before exiting: {done.stdout!r} {done.stderr!r}"
        )
