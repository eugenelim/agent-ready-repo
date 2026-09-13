"""T3 — input acquisition: confinement, bounds, modes, lifecycle.

Covers AC-0016, AC-0017, AC-0018, AC-0020, AC-0021, AC-0022, AC-0038, AC-0042,
AC-0043, AC-0061, AC-0073.

No network, no sleeping on a wall clock: `--for` is driven through an injected
monotonic clock so the timing cases are deterministic.
"""

from __future__ import annotations

import io
import json
import os
import signal
import time
import pytest

from jsonl_otlp_exporter import source as src


def _write(path, text: str):
    path.write_text(text, encoding="utf-8")
    return path


def _records(path, root, **kwargs):
    fd = src.open_input(path, root)
    try:
        return list(src.iter_records(fd, **kwargs))
    finally:
        os.close(fd)


class _FakeClock:
    """A monotonic clock the test advances, so `--for` needs no real waiting.

    It also advances on its own by `step` per reading. That is not a
    convenience: with a purely manual clock, a build that never yields an
    expected record spins in the follow loop forever and the test *hangs*
    instead of failing. A self-advancing clock guarantees every follow loop
    reaches its deadline, so a wrong build fails in bounded time.
    """

    def __init__(self, step: float = 0.001):
        self.now = 0.0
        self.step = step

    def __call__(self):
        self.now += self.step
        return self.now


class TestConfinement:
    """AC-0017 — refusal decided on the opened object, never on the pathname."""

    def test_a_regular_file_inside_the_root_is_opened(self, tmp_path):
        target = _write(tmp_path / "events.jsonl", '{"a":1}\n')
        fd = src.open_input(target, tmp_path)
        try:
            assert os.read(fd, 64) == b'{"a":1}\n'
        finally:
            os.close(fd)

    def test_a_symlinked_leaf_is_refused(self, tmp_path):
        real = _write(tmp_path / "real.jsonl", '{"a":1}\n')
        link = tmp_path / "link.jsonl"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(src.InputRefused):
            src.open_input(link, tmp_path)

    def test_a_symlinked_directory_component_is_refused(self, tmp_path):
        """The component swap is what separates descriptor walking from path checks.

        The leaf itself is a perfectly ordinary regular file. Only the directory
        above it is a link, so a build that resolves the whole path once and then
        opens the result accepts this.
        """
        outside = tmp_path / "outside"
        outside.mkdir()
        _write(outside / "events.jsonl", '{"a":1}\n')
        root = tmp_path / "root"
        root.mkdir()
        try:
            (root / "data").symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(src.InputRefused):
            src.open_input(root / "data" / "events.jsonl", root)

    def test_a_non_regular_file_is_refused(self, tmp_path):
        """A FIFO must be refused, and refused *without blocking*.

        Opening a FIFO that has no writer blocks until one appears, so a build
        that omits O_NONBLOCK hangs here forever instead of refusing -- an
        unauthenticated denial of service through nothing but a named pipe. The
        alarm turns that hang into a failure; without it this test would never
        report at all.
        """
        if not hasattr(os, "mkfifo") or not hasattr(signal, "SIGALRM"):
            pytest.skip("FIFOs or SIGALRM unavailable on this platform")
        fifo = tmp_path / "events.jsonl"
        os.mkfifo(fifo)

        def _blocked(signum, frame):
            raise TimeoutError("open_input blocked on a FIFO instead of refusing it")

        previous = signal.signal(signal.SIGALRM, _blocked)
        signal.alarm(5)
        try:
            with pytest.raises(src.InputRefused):
                src.open_input(fifo, tmp_path)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)

    def test_a_path_escaping_the_root_is_refused(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        _write(tmp_path / "outside.jsonl", '{"a":1}\n')
        with pytest.raises(src.InputRefused):
            src.open_input("../outside.jsonl", root)

    def test_an_absolute_path_outside_the_root_is_refused(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        outside = _write(tmp_path / "outside.jsonl", '{"a":1}\n')
        with pytest.raises(src.InputRefused):
            src.open_input(outside, root)

    def test_an_absent_path_is_refused(self, tmp_path):
        """AC-0043 — nothing is sent and the run fails, distinct from an empty file."""
        with pytest.raises(src.InputRefused):
            src.open_input(tmp_path / "missing.jsonl", tmp_path)


class TestLineHandling:
    """AC-0016, AC-0018, AC-0038, AC-0073 — one bad line never costs the others."""

    def test_a_non_parsing_line_is_skipped_and_the_rest_sent(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\nnot json\n{"b":2}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"b": 2}]
        assert "line 2" in err.getvalue()

    def test_a_top_level_non_object_is_skipped_and_reported(self, tmp_path):
        """AC-0073. Each of these parses as JSON, so AC-0016's check accepts them."""
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n[1,2]\n"str"\n7\nnull\n{"b":2}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"b": 2}]
        report = err.getvalue()
        for line in ("line 2", "line 3", "line 4", "line 5"):
            assert line in report

    def test_an_oversize_line_is_skipped_and_the_rest_sent(self, tmp_path):
        big = '{"pad":"' + "x" * (src.MAX_LINE_BYTES + 10) + '"}'
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n' + big + '\n{"b":2}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"b": 2}]
        assert "over" in err.getvalue()

    def test_a_line_at_exactly_the_ceiling_is_accepted(self, tmp_path):
        """The bound is measured excluding the newline, so this line is legal."""
        head, tail = '{"pad":"', '"}'
        pad = "x" * (src.MAX_LINE_BYTES - len(head) - len(tail))
        line = head + pad + tail
        assert len(line.encode()) == src.MAX_LINE_BYTES
        target = _write(tmp_path / "e.jsonl", line + "\n")
        assert _records(target, tmp_path) == [{"pad": pad}]

    def test_line_numbers_stay_correct_after_an_oversize_line(self, tmp_path):
        """The oversize line's own tail must not be counted as another line.

        Counting it shifts every later report by one, so the numbers a reader
        uses to find the bad record point at the wrong record.
        """
        big = '{"pad":"' + "x" * (src.MAX_LINE_BYTES + 10) + '"}'
        target = _write(tmp_path / "e.jsonl", f'{{"a":1}}\n{big}\nnot json\n{{"b":2}}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"b": 2}]
        assert "line 3: does not parse" in err.getvalue()

    def test_a_trailing_line_with_no_newline_is_not_sent(self, tmp_path):
        """A fragment is not a record yet; sending it sends a truncated record."""
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n{"b":2')
        assert _records(target, tmp_path) == [{"a": 1}]


class TestModes:
    """AC-0020, AC-0021, AC-0042 — one-shot by default; follow bounded by --for."""

    def test_one_shot_reads_once_and_returns(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n{"b":2}\n')
        start = time.monotonic()
        assert _records(target, tmp_path) == [{"a": 1}, {"b": 2}]
        assert time.monotonic() - start < 1.0, "one-shot must not wait for more lines"

    def test_follow_delivers_a_line_appended_after_start(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        fd = src.open_input(target, tmp_path)
        clock = _FakeClock()
        try:
            records = src.iter_records(
                fd, follow=True, for_seconds=10, clock=clock, poll_interval=0
            )
            assert next(records) == {"a": 1}
            with target.open("a", encoding="utf-8") as handle:
                handle.write('{"b":2}\n')
            assert next(records) == {"b": 2}
            clock.now = 10.0  # jump past the deadline
            with pytest.raises(StopIteration):
                next(records)
        finally:
            os.close(fd)

    def test_for_ends_the_run_at_its_deadline(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        fd = src.open_input(target, tmp_path)
        clock = _FakeClock()
        try:
            records = src.iter_records(
                fd, follow=True, for_seconds=5, clock=clock, poll_interval=0
            )
            assert next(records) == {"a": 1}
            clock.now = 5.0
            assert list(records) == []
        finally:
            os.close(fd)


class TestLifecycle:
    """AC-0022 — truncation, inode replacement and a partial tail send nothing extra."""

    def _follow(self, target, root, clock):
        fd = src.open_input(target, root)
        return fd, src.iter_records(fd, follow=True, for_seconds=30, clock=clock, poll_interval=0)

    def test_truncation_sends_no_further_record(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        clock = _FakeClock()
        fd, records = self._follow(target, tmp_path, clock)
        try:
            assert next(records) == {"a": 1}
            target.write_text("", encoding="utf-8")  # truncate to zero
            clock.now = 30.0
            assert list(records) == [], "truncation is not a record"
        finally:
            os.close(fd)

    def test_replacement_by_a_new_inode_sends_no_further_record(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        clock = _FakeClock()
        fd, records = self._follow(target, tmp_path, clock)
        try:
            assert next(records) == {"a": 1}
            replacement = _write(tmp_path / "new.jsonl", '{"z":26}\n')
            os.replace(replacement, target)  # same name, new inode
            clock.now = 30.0
            assert list(records) == [], "the run holds its descriptor; it does not re-read"
        finally:
            os.close(fd)

    def test_the_first_record_is_sent_exactly_once_across_all_three(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        clock = _FakeClock()
        fd, records = self._follow(target, tmp_path, clock)
        try:
            seen = [next(records)]
            target.write_text("", encoding="utf-8")
            replacement = _write(tmp_path / "new.jsonl", '{"z":26}\n')
            os.replace(replacement, target)
            with target.open("a", encoding="utf-8") as handle:
                handle.write('{"partial":true')  # no newline
            clock.now = 30.0
            seen.extend(records)
            assert seen == [{"a": 1}], "exactly once, and nothing for the conditions"
        finally:
            os.close(fd)


class TestInputImmutability:
    """AC-0061 — after any run the file is byte-for-byte and stat-for-stat unchanged."""

    @pytest.mark.parametrize(
        "content",
        [
            '{"a":1}\n{"b":2}\n',
            '{"a":1}\nnot json\n{"b":2}\n',
            '{"a":1}\n[1,2]\n{"b":2}\n',
            '{"a":1}\n{"b":2',
        ],
        ids=["clean", "unparseable", "non-object", "partial-tail"],
    )
    def test_the_input_is_untouched(self, tmp_path, content):
        target = _write(tmp_path / "e.jsonl", content)
        before_bytes = target.read_bytes()
        before_stat = target.stat()
        list(src.iter_records(src.open_input(target, tmp_path), stream=io.StringIO()))
        after_stat = target.stat()
        assert target.read_bytes() == before_bytes
        assert after_stat.st_size == before_stat.st_size
        assert after_stat.st_mtime_ns == before_stat.st_mtime_ns

    def test_no_position_file_is_written_anywhere_under_the_root(self, tmp_path):
        """A checkpoint is durable state, which the Boundaries forbid outright."""
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n{"b":2}\n')
        before = {p for p in tmp_path.rglob("*")}
        _records(target, tmp_path)
        assert {p for p in tmp_path.rglob("*")} == before


class TestDeadlineWhileBytesKeepArriving:
    """AC-0042 — the `--for` bound must hold whether or not the file goes quiet.

    The deadline used to be tested only in the "no bytes available" branch, so a
    file being appended at least as fast as it is parsed never reached it and the
    run was unbounded. This drives many full chunks so the reader never once sees
    an empty read, and the clock passes the deadline while data is still coming.
    """

    def test_the_run_ends_even_though_every_read_returns_data(self, tmp_path):
        line = json.dumps({"a": 1, "pad": "x" * 200}) + "\n"
        target = _write(tmp_path / "e.jsonl", line * 4000)  # many 64 KiB reads
        clock = _FakeClock(step=1.0)
        fd = src.open_input(target, tmp_path)
        try:
            records = list(src.iter_records(fd, for_seconds=3, clock=clock, poll_interval=0))
        finally:
            os.close(fd)
        assert records, "the run must deliver what it read before the deadline"
        assert len(records) < 4000, (
            f"all {len(records)} records were read: the deadline was never "
            "evaluated while bytes kept arriving"
        )

    def test_without_a_deadline_the_whole_file_is_read(self, tmp_path):
        """The control's other half: the bound must not truncate an unbounded run."""
        line = json.dumps({"a": 1, "pad": "x" * 200}) + "\n"
        target = _write(tmp_path / "e.jsonl", line * 4000)
        fd = src.open_input(target, tmp_path)
        try:
            assert len(list(src.iter_records(fd))) == 4000
        finally:
            os.close(fd)


class TestRound2Regressions:
    """Untrusted lines that used to end the whole run."""

    def test_a_line_past_the_recursion_limit_is_skipped_not_fatal(self, tmp_path):
        """~16,000 levels of nesting is 40 KB -- inside the 64 KiB line ceiling --
        and the decoder raises RecursionError, which is not a JSONDecodeError.

        The reviewer's stated depth of 2,000 parses fine; measuring found the
        real threshold, and the defect is real above it.
        """
        deep = "[" * 20000 + "]" * 20000
        good = '{"a":1}\n'
        target = _write(tmp_path / "e.jsonl", good + deep + "\n" + good)
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"a": 1}]
        assert "line 2" in err.getvalue()

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
    def test_a_non_standard_json_constant_is_skipped(self, tmp_path, token):
        """`json.loads` accepts these by default and `json.dumps` writes them back
        as bare tokens, producing a body that is not JSON -- so one such line
        would cost every good record batched with it."""
        target = _write(tmp_path / "e.jsonl",
                        '{"a":1}\n' + '{"b": %s}\n' % token + '{"c":3}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"c": 3}]
        assert "line 2" in err.getvalue()

    def test_an_absolute_input_under_a_symlinked_root_is_accepted(self, tmp_path):
        """On macOS `/tmp` and `/var` are symlinks into `/private`, so comparing a
        resolved root against a lexical input refused an ordinary invocation.
        This was found by a probe hitting it, not by reading."""
        real = tmp_path / "real"
        real.mkdir()
        target = _write(real / "e.jsonl", '{"a":1}\n')
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks unavailable on this platform")
        fd = src.open_input(link / "e.jsonl", link)
        try:
            assert os.read(fd, 32) == b'{"a":1}\n'
        finally:
            os.close(fd)
