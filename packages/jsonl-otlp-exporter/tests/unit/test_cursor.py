"""AC-0012, AC-0023, AC-0013, AC-0024, AC-0015, AC-0016, AC-0030 — the cursor.

A new module, tests/unit/test_cursor.py. Self-contained: it imports `io`,
`json`, `os`, `pytest` and the `cursor` module under test.
"""
import dataclasses
import io
import json
import os

import pytest
from jsonl_otlp_exporter import cursor as cur


class TestRoundTrip:
    def test_render_parses_back_to_the_same_cursor(self):
        """The output of one run is the input of the next, or resume is a fiction."""
        text = cur.render_cursor(4096, 12, 34)
        assert json.loads(text) == {"v": 1, "offset": 4096, "device": 12, "inode": 34}
        back = cur.parse_cursor(text)
        assert (back.offset, back.device, back.inode) == (4096, 12, 34)

    def test_render_emits_compact_json(self):
        """The README documents the compact form, so the code must emit it.

        `separators=(",", ":")` survived the wiring sweep: nothing asserted the
        spacing, so dropping it produced `{"v": 1, ...}` while every other check
        still passed. That would silently falsify the worked example under
        `## Resuming a run`, which a reader copies onto a command line.
        """
        text = cur.render_cursor(4096, 12, 34)
        assert " " not in text
        assert text == '{"v":1,"offset":4096,"device":12,"inode":34}'

    def test_a_cursor_is_immutable(self):
        """`frozen=True` survived the sweep with no control behind it.

        A cursor is compared against a descriptor's identity and then seeked to;
        code that could rewrite it between those two steps is exactly the
        check-then-act the boundary proof exists to close.
        """
        cursor = cur.Cursor(offset=10, device=1, inode=2)
        with pytest.raises(dataclasses.FrozenInstanceError):
            cursor.offset = 0  # type: ignore[misc]

    def test_render_emits_exactly_one_line(self):
        """AC-0001's 'exactly one line' is decided here, not at the print."""
        assert "\n" not in cur.render_cursor(0, 1, 2)


class TestRefusal:
    @pytest.mark.parametrize(
        "text",
        [
            "not json at all",
            "[]",
            "3",
            '"a string"',
            '{"v": 1, "offset": 0, "device": 1}',                    # missing inode
            '{"v": 1, "offset": 0, "device": 1, "inode": 2, "x": 3}',  # extra key
            '{"v": 2, "offset": 0, "device": 1, "inode": 2}',        # future version
            '{"v": 1, "offset": "0", "device": 1, "inode": 2}',      # offset not an int
            '{"v": 1, "offset": 1.5, "device": 1, "inode": 2}',
            '{"v": 1, "offset": true, "device": 1, "inode": 2}',     # bool is not an int here
            '{"v": 1, "offset": 0, "device": true, "inode": 2}',     # nor here
            '{"v": 1, "offset": 0, "device": 1, "inode": true}',     # nor here
            '{"v": 1, "offset": -1, "device": 1, "inode": 2}',       # negative
            '{"v": 1, "offset": 0, "device": "1", "inode": 2}',
            '{"v": 1, "offset": 0, "device": 1, "inode": "2"}',
        ],
    )
    def test_a_bad_cursor_is_refused(self, text):
        """AC-0016. One predicate, every enumerated member."""
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor(text)

    def test_an_oversize_argument_is_refused_on_its_length(self):
        """AC-0015, and the fixture is the whole point of the case.

        The argument is over the byte bound and otherwise fully conforming: a
        valid member set, valid types, a non-negative integer offset. Nothing
        but the length check can refuse it, so a build that parses first and
        never measures raises nothing and this fails. A fixture padded with an
        extra member is refused on shape by that same wrong build -- which is
        how this case was first drafted, and why it was replaced.
        """
        offset = int("9" * (cur.MAX_CURSOR_BYTES + 1))
        text = json.dumps({"v": 1, "offset": offset, "device": 1, "inode": 2})
        assert len(text.encode("utf-8")) > cur.MAX_CURSOR_BYTES
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor(text)
        assert "too long" in str(excinfo.value)

    def test_the_length_check_runs_before_the_decoder(self):
        """AC-0015's ordering, with a fixture only that ordering survives.

        5000 digits is over the byte bound AND over CPython's integer-literal
        limit of 4300, so `json.loads` raises on it. A length-first build reports
        "too long"; a build that decodes first and measures second reports a
        parse failure. The 4097-digit fixture cannot tell them apart -- it is
        under the digit limit and parses cleanly -- which is why that ordering
        was unverified. The ordering is the bound's reason for existing: it keeps
        an arbitrarily large literal away from the decoder.
        """
        text = '{"v":1,"offset":' + "9" * 5000 + ',"device":1,"inode":2}'
        assert len(text.encode("utf-8")) > cur.MAX_CURSOR_BYTES
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor(text)
        assert "too long" in str(excinfo.value), (
            "reported a parse failure, so the decoder ran before the length check"
        )

    def test_the_length_refusal_is_distinguishable_from_a_shape_refusal(self):
        """AC-0015 states an ordering, and an ordering needs two outcomes.

        Without this, an argument that is both over-length and malformed cannot
        show which check fired, so "before it is parsed" is unobservable and the
        case above proves only that something refused.
        """
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor("not json at all")
        assert "too long" not in str(excinfo.value)

    def test_the_bound_is_measured_on_utf8_bytes_not_characters(self):
        """The bound's unit.

        A conforming cursor is all ASCII, so no valid-shape fixture can separate
        characters from bytes. This one is malformed too, so it asserts only that
        the LENGTH check fired -- which the case above established is a
        distinguishable reason.
        """
        text = '{"v": 1, "offset": 0, "é": "'
        text += "é" * (cur.MAX_CURSOR_BYTES // 2 + 1) + '"}'
        assert len(text) < cur.MAX_CURSOR_BYTES < len(text.encode("utf-8"))
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor(text)
        assert "too long" in str(excinfo.value)


class TestResolveStartOffset:
    @staticmethod
    def _info(device, inode, size):
        class _Stat:
            st_dev, st_ino, st_size = device, inode, size

        return _Stat()

    @staticmethod
    def _aligned_file(tmp_path, records=2):
        """A file whose every offset under test sits just after a newline."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n' * records)
        return target

    def test_a_matching_cursor_is_honoured(self, tmp_path):
        """AC-0011. Corrected from the approved stub -- see the ledger.

        The stub passed no `fd` and expected 10 back. AC-0030 was added after it
        was written and requires the offset proven against a descriptor, so the
        two contradicted. `fd` is required now; the fixture makes offset 9 a real
        record boundary.
        """
        target = self._aligned_file(tmp_path)
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            stream = io.StringIO()
            offset = cur.resolve_start_offset(
                cur.Cursor(offset=9, device=info.st_dev, inode=info.st_ino),
                info, stream=stream, fd=fd,
            )
            assert offset == 9
            assert stream.getvalue() == ""
        finally:
            os.close(fd)

    def test_a_matching_cursor_at_offset_zero_is_honoured(self, tmp_path):
        """Offset 0 must short-circuit the boundary read, not perform it.

        A checker that always reads `offset - 1` preads at -1 and refuses, or
        crashes. Byte 0 is a real cursor: it is what a caller stores after a
        reset run, so it has to be honoured rather than refused.
        """
        target = self._aligned_file(tmp_path)
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            stream = io.StringIO()
            assert cur.resolve_start_offset(
                cur.Cursor(offset=0, device=info.st_dev, inode=info.st_ino),
                info, stream=stream, fd=fd,
            ) == 0
            assert stream.getvalue() == "", "offset 0 is honoured, not reset"
        finally:
            os.close(fd)

    def test_an_offset_equal_to_the_size_is_honoured(self, tmp_path):
        """The boundary the bridge's `st_size < offset` puts on the honoured side.

        Also corrected for `fd`. The file ends with a newline, so its size is a
        record boundary and this stays an AC-0011 case rather than an AC-0030 one.
        """
        target = self._aligned_file(tmp_path)
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            assert cur.resolve_start_offset(
                cur.Cursor(offset=info.st_size, device=info.st_dev,
                           inode=info.st_ino),
                info, stream=io.StringIO(), fd=fd,
            ) == info.st_size
        finally:
            os.close(fd)

    @pytest.mark.parametrize(
        "info_args", [(9, 2, 100), (1, 9, 100)], ids=["device", "inode"]
    )
    def test_an_identity_change_resets_to_zero(self, info_args):
        """AC-0012. Device and inode each reset on their own.

        No real descriptor: an identity mismatch returns before the boundary
        proof, which is what makes the four routes mutually exclusive.
        """
        assert cur.resolve_start_offset(
            cur.Cursor(offset=10, device=1, inode=2),
            self._info(*info_args),
            stream=io.StringIO(), fd=-1,
        ) == 0

    @pytest.mark.parametrize(
        "info_args", [(9, 2, 100), (1, 9, 100)], ids=["device", "inode"]
    )
    def test_an_identity_change_is_reported(self, info_args):
        """AC-0023, split from AC-0012: a silent reset fails only this one."""
        stream = io.StringIO()
        cur.resolve_start_offset(
            cur.Cursor(offset=10, device=1, inode=2),
            self._info(*info_args),
            stream=stream, fd=-1,
        )
        assert "identity" in stream.getvalue()

    def test_an_identity_change_is_reported_even_at_offset_zero(self):
        """AC-0023 must not be skipped by an early return for offset 0.

        Every other mismatch case carries a nonzero offset, so a build that
        returns 0 the moment `cursor.offset == 0` passes them all and silently
        honours a zero-offset cursor belonging to a different file. The read
        position is the same either way; what is lost is the operator being told
        the input was replaced.
        """
        stream = io.StringIO()
        assert cur.resolve_start_offset(
            cur.Cursor(offset=0, device=9, inode=9),
            self._info(1, 2, 100), stream=stream, fd=-1,
        ) == 0
        assert "identity" in stream.getvalue()

    def test_a_shrink_below_the_offset_resets_to_zero(self):
        """AC-0013."""
        assert cur.resolve_start_offset(
            cur.Cursor(offset=200, device=1, inode=2),
            self._info(1, 2, 100),
            stream=io.StringIO(), fd=-1,
        ) == 0

    def test_a_shrink_below_the_offset_is_reported(self):
        """AC-0024, split from AC-0013."""
        stream = io.StringIO()
        cur.resolve_start_offset(
            cur.Cursor(offset=200, device=1, inode=2),
            self._info(1, 2, 100),
            stream=stream, fd=-1,
        )
        assert "shrank" in stream.getvalue()

    def test_end_of_file_is_not_automatically_a_boundary(self, tmp_path):
        """The file's size is only a boundary if the last byte is a newline.

        A build that honours `offset == st_size` unconditionally passes the
        newline-terminated fixture and the interior-misalignment case. Against a
        file whose tail record has no terminator it would accept the cursor, and
        the reader would then start past bytes belonging to a record that is not
        finished -- losing it once the writer completes it.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n{"i": 1}')  # no trailing newline
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            with pytest.raises(cur.CursorRefused):
                cur.resolve_start_offset(
                    cur.Cursor(offset=info.st_size, device=info.st_dev,
                               inode=info.st_ino),
                    info, stream=io.StringIO(), fd=fd,
                )
        finally:
            os.close(fd)

    def test_a_misaligned_offset_is_refused_not_reset(self, tmp_path):
        """AC-0030. A matching identity with a bad offset is not a rotation.

        Folding this into AC-0012's reset is the tempting shape and is wrong: it
        turns a corrupted or forged cursor into a silent re-send of the whole
        file. The check reads the preceding byte from the descriptor `--input`
        was opened on, so it inherits that descriptor's confinement proof rather
        than reopening the path.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n{"i": 1}\n')
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            aligned = cur.Cursor(offset=9, device=info.st_dev, inode=info.st_ino)
            assert cur.resolve_start_offset(aligned, info, stream=io.StringIO(),
                                            fd=fd) == 9
            misaligned = cur.Cursor(offset=4, device=info.st_dev,
                                    inode=info.st_ino)
            with pytest.raises(cur.CursorRefused):
                cur.resolve_start_offset(misaligned, info, stream=io.StringIO(),
                                         fd=fd)
        finally:
            os.close(fd)

    def test_a_decoder_failure_of_any_kind_becomes_a_refusal(self):
        """AC-0016's catch-all member.

        Measured 2026-09-15: neither scanner raises `RecursionError` at the ~2000
        nesting levels a 4096-byte argument admits, so this is insurance rather
        than a reproducing attack -- the recursion limit is settable by an
        embedding caller and `source.py:286` carries the same broad catch for the
        same reason. The case asserts the refusal either way, so it holds whether
        the decoder raises or simply rejects the shape.
        """
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor("[" * 2000 + "]" * 2000)

    def test_no_cursor_reads_from_zero_and_says_nothing(self):
        """AC-0014. The absent flag is not a reset and must not print one."""
        stream = io.StringIO()
        assert cur.resolve_start_offset(
            None, self._info(1, 2, 100), stream=stream, fd=-1
        ) == 0
        assert stream.getvalue() == ""

# tests/unit/test_cursor.py — two refusal controls review found missing.


class TestRefusalControls:
    def test_a_decoder_exception_of_any_type_becomes_a_refusal(self, monkeypatch):
        """The broad `except` had no control that could fail.

        The deep-nesting fixture does not make either scanner raise at this byte
        bound — measured — so a build that caught only `JSONDecodeError` passed
        it by refusing on shape instead. Forcing the decoder to raise something
        else is the only way to reach the clause.
        """
        class _DecoderExploded(Exception):
            """Test-local, so no whitelist can name it.

            `RecursionError` alone was not enough: an implementation catching
            `(JSONDecodeError, RecursionError)` passed while still violating
            AC-0016 for any other decoder exception. Only a general catch can
            satisfy a type the implementation cannot have heard of.
            """

        def boom(*args, **kwargs):
            raise _DecoderExploded("forced")

        monkeypatch.setattr(cur.json, "loads", boom)
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor('{"v": 1, "offset": 0, "device": 1, "inode": 2}')

    def test_a_boolean_version_is_refused(self):
        """`True == 1` in Python, so a `raw["v"] != 1` check accepts JSON `true`.

        Bool rejection was pinned for `offset` only. The version field decides
        whether a stored cursor is readable at all, so it needs its own case.
        """
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor('{"v": true, "offset": 0, "device": 1, "inode": 2}')
