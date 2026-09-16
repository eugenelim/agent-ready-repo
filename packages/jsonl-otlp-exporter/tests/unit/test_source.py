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
import pathlib
import signal
import time

import pytest
from jsonl_otlp_exporter import source as src


def _write(path, text: str):
    path.write_text(text, encoding="utf-8")
    return path


def _records(path, root, **kwargs):
    """Plain records, with the reader's `(record, end_offset)` pair unwrapped.

    Unwrapping here is what keeps the resume change small: the cases routed
    through this helper keep their assertions exactly as they were.
    """
    fd = src.open_input(path, root)
    try:
        return [record for record, _ in src.iter_records(fd, **kwargs)]
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
            assert next(records)[0] == {"a": 1}
            with target.open("a", encoding="utf-8") as handle:
                handle.write('{"b":2}\n')
            assert next(records)[0] == {"b": 2}
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
            assert next(records)[0] == {"a": 1}
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
            assert next(records)[0] == {"a": 1}
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
            assert next(records)[0] == {"a": 1}
            replacement = _write(tmp_path / "new.jsonl", '{"z":26}\n')
            pathlib.Path(replacement).replace(target)  # same name, new inode
            clock.now = 30.0
            assert list(records) == [], "the run holds its descriptor; it does not re-read"
        finally:
            os.close(fd)

    def test_the_first_record_is_sent_exactly_once_across_all_three(self, tmp_path):
        target = _write(tmp_path / "e.jsonl", '{"a":1}\n')
        clock = _FakeClock()
        fd, records = self._follow(target, tmp_path, clock)
        try:
            seen = [next(records)[0]]
            target.write_text("", encoding="utf-8")
            replacement = _write(tmp_path / "new.jsonl", '{"z":26}\n')
            pathlib.Path(replacement).replace(target)
            with target.open("a", encoding="utf-8") as handle:
                handle.write('{"partial":true')  # no newline
            clock.now = 30.0
            seen.extend(record for record, _ in records)
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
        before = set(tmp_path.rglob("*"))
        _records(target, tmp_path)
        assert set(tmp_path.rglob("*")) == before


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
            records = [r for r, _ in
                       src.iter_records(fd, for_seconds=3, clock=clock, poll_interval=0)]
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
            assert len([r for r, _ in src.iter_records(fd)]) == 4000
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
                        '{"a":1}\n' + f'{{"b": {token}}}\n' + '{"c":3}\n')
        err = io.StringIO()
        assert _records(target, tmp_path, stream=err) == [{"a": 1}, {"c": 3}]
        assert "line 2" in err.getvalue()

    def test_an_absolute_input_under_a_symlinked_root_is_accepted(self, tmp_path):
        """On macOS `/tmp` and `/var` are symlinks into `/private`, so comparing a
        resolved root against a lexical input refused an ordinary invocation.
        This was found by a probe hitting it, not by reading."""
        real = tmp_path / "real"
        real.mkdir()
        _write(real / "e.jsonl", '{"a":1}\n')
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


class TestRound3Regressions:
    def test_one_shot_reads_only_what_was_there_when_it_opened(self, tmp_path, monkeypatch):
        """AC-0020: one-shot reads the file ONCE and exits.

        Driven through a substituted `os.read` rather than a racing writer. The
        earlier version spawned a thread appending while the reader drained, and
        could pass for the wrong reason -- if the reader reached EOF first, a
        build with no budget passed too -- or hang forever if the writer stayed
        ahead, since no pytest timeout is configured. Neither is a reliable
        failure. Here the substitute never returns empty, so a build without the
        size budget cannot terminate at all and the test fails on the call count
        instead of hanging.
        """
        line = (json.dumps({"a": 1}) + "\n").encode()
        target = _write(tmp_path / "e.jsonl", line.decode() * 10)
        fd = src.open_input(target, tmp_path)
        real_read = os.read
        calls = []

        def endless_read(descriptor, size):
            if descriptor != fd:
                return real_read(descriptor, size)
            calls.append(size)
            if len(calls) > 50:
                raise AssertionError(
                    "one-shot kept reading past the size the file had at open"
                )
            return line * 100 if size else b""

        monkeypatch.setattr(os, "read", endless_read)
        records = [r for r, _ in src.iter_records(fd)]
        os.close(fd)
        assert records, "the records present at open must still be delivered"
        assert sum(calls) <= target.stat().st_size + 65536, (
            f"read {sum(calls)} bytes from a {target.stat().st_size}-byte file"
        )


# AC-0009, AC-0010, AC-0011, AC-0014, AC-0017, AC-0029 — reading from an offset.
#
# Appended to tests/unit/test_source.py, which already imports `io`, `os`,
# `src` and defines `_records`. Adds no import: the budget cases use the
# `monkeypatch` fixture, which `packages/AGENTS.md` names as the convention.


class TestPositionedReader:
    """Appended to tests/unit/test_source.py, which owns `_records` and the fd
    fixtures this reuses."""

    @staticmethod
    def _write(tmp_path, lines):
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"".join(line.encode("utf-8") + b"\n" for line in lines))
        return target

    def test_a_start_offset_skips_the_records_before_it(self, tmp_path):
        """AC-0011."""
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}', '{"i": 2}'])
        first_line = len(b'{"i": 0}\n')
        fd = src.open_input(target, tmp_path)
        try:
            pairs = list(src.iter_records(fd, start_offset=first_line))
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [1, 2]
        # The offsets must be ABSOLUTE, not relative to the seek. Discarding
        # them here let a tally initialised to 0 rather than `start_offset` pass
        # the whole suite -- measured, 0 of 349 cases noticed. A run reporting a
        # relative offset makes every later run re-send, which is the failure
        # resume exists to prevent.
        assert [offset for _, offset in pairs] == [
            first_line * 2, first_line * 3,
        ]

    def test_each_yielded_offset_follows_a_newline(self, tmp_path):
        """AC-0009, asserted on every yield rather than sampled once."""
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}', '{"i": 2}'])
        data = target.read_bytes()
        fd = src.open_input(target, tmp_path)
        try:
            offsets = [offset for _, offset in src.iter_records(fd)]
        finally:
            os.close(fd)
        assert offsets, "the reader yielded nothing, so the invariant was not exercised"
        for offset in offsets:
            assert data[offset - 1 : offset] == b"\n", offset

    def test_a_skipped_line_still_advances_the_position(self, tmp_path):
        """A line the reader consumed and declined belongs behind the offset, or
        every future run re-reads and re-declines it."""
        lines = ['{"i": 0}', "not json", '{"i": 2}']
        target = self._write(tmp_path, lines)
        fd = src.open_input(target, tmp_path)
        try:
            pairs = list(src.iter_records(fd, stream=io.StringIO()))
        finally:
            os.close(fd)
        assert pairs[-1][1] == len(target.read_bytes())
        # The DELTA, not just the final offset. The last record ends at EOF, so
        # the assertion above is also satisfied by a reader that reports the
        # descriptor's own position for every record instead of a line-accurate
        # tally -- which is the bug this case is named for. The delta across the
        # skipped line can only be right if that line was actually credited.
        assert pairs[-1][1] - pairs[0][1] == len(lines[1]) + 1 + len(lines[2]) + 1

    def test_a_final_line_with_no_newline_is_not_consumed(self, tmp_path):
        """AC-0010. The partial line's first byte is the ceiling on the offset."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n{"i": 1}')
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            pairs = list(
                src.iter_records(fd, on_position=positions.append)
            )
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [0]
        assert max(positions) == len(b'{"i": 0}\n')

    def test_on_position_reports_past_a_trailing_skipped_line(self, tmp_path):
        """AC-0004's trailing-skip member: the last yield cannot see past itself."""
        target = self._write(tmp_path, ['{"i": 0}', "not json"])
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            list(
                src.iter_records(
                    fd, stream=io.StringIO(), on_position=positions.append
                )
            )
        finally:
            os.close(fd)
        assert max(positions) == len(target.read_bytes())

    def test_an_unterminated_over_length_final_line_is_not_consumed(self, tmp_path):
        """AC-0010 on the path a short partial line never reaches.

        The reader clears an over-length line's bytes as it reads them, so an
        accounting that advances on the clear reports a position inside a line
        with no terminator -- and a later run resumes mid-record from it. A short
        partial line stays in the buffer and never exercises the discard branch,
        which is why the first draft's single fixture could not see this.
        """
        target = tmp_path / "events.jsonl"
        head = b'{"i": 0}\n'
        target.write_bytes(head + b"x" * (src.MAX_LINE_BYTES + 10))
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            list(
                src.iter_records(
                    fd, stream=io.StringIO(), on_position=positions.append
                )
            )
        finally:
            os.close(fd)
        assert max(positions) == len(head)

    def test_the_one_shot_budget_is_measured_from_the_start_offset(
        self, tmp_path, monkeypatch
    ):
        """AC-0017. Asserted against a live writer, not against the arithmetic.

        A budget left at the whole file size lets one-shot drain an appending
        writer forever; a budget of size-minus-offset cannot. The writer appends
        on every read, so a wrong budget hangs rather than returning a wrong
        count -- which is why this has a record ceiling and not just an equality.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        first_line = len(b'{"i": 0}\n')
        fd = src.open_input(target, tmp_path)
        appended = [0]

        real_read = os.read  # captured BEFORE the patch: `src.os` IS `os`,
        # so patching `src.os.read` rebinds the name this function would call
        # and the replacement recurses into itself.

        def _read(descriptor, size):
            if appended[0] < 50:
                appended[0] += 1
                with pathlib.Path(target).open("ab") as handle:
                    handle.write(b'{"i": 99}\n')
            return real_read(descriptor, size)

        try:
            monkeypatch.setattr(src.os, "read", _read)
            pairs = list(src.iter_records(fd, start_offset=first_line))
        finally:
            os.close(fd)
        assert len(pairs) == 1
        assert pairs[0][0] == {"i": 1}

    def test_the_budget_covers_the_whole_file_after_a_reset(self, tmp_path,
                                                           monkeypatch):
        """AC-0029. A reset reads from zero, so its ceiling is S, not S - N.

        Driven the same way as AC-0017 and separate from it because the two
        ceilings come from different starting offsets: a build that subtracts the
        cursor's offset unconditionally passes AC-0017 and never terminates here.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        fd = src.open_input(target, tmp_path)
        appended = [0]

        real_read = os.read  # captured BEFORE the patch: `src.os` IS `os`,
        # so patching `src.os.read` rebinds the name this function would call
        # and the replacement recurses into itself.

        def _read(descriptor, size):
            if appended[0] < 50:
                appended[0] += 1
                with pathlib.Path(target).open("ab") as handle:
                    handle.write(b'{"i": 99}\n')
            return real_read(descriptor, size)

        try:
            monkeypatch.setattr(src.os, "read", _read)
            pairs = list(src.iter_records(fd, start_offset=0))
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [0, 1]

    def test_the_modules_helper_unwraps_the_new_yield_shape(self, tmp_path):
        """`test_source.py:28`'s `_records(path, root, **kwargs)` still returns
        plain records, so cases routed through it keep their assertions.

        It takes a path and a root, not a descriptor, and opens the input itself.
        Pinned because the helper is the one site that hides the pair from a
        caller; the seven direct `iter_records` calls in that module unwrap at
        their own call site.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        assert _records(target, tmp_path) == [{"i": 0}, {"i": 1}]
