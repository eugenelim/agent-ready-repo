"""The resume cursor: what a caller hands back, and what the run does with it.

The sender writes no durable state. A run reads from a cursor the caller
supplies and prints the cursor the next run should start from; storing it
between runs belongs to whoever invokes the sender. That is the whole design,
and it is why nothing here opens a path for writing.

Two ideas carry this module.

The first is that a byte offset is valid for exactly one file identity. Carried
across a rotation it lands at an arbitrary byte of an unrelated file, which is a
record boundary only by luck. So the offset travels paired with the device and
inode numbers of the descriptor the run actually read, and a mismatch resets to
byte zero rather than seeking.

The second is that identity is necessary but not sufficient. A cursor whose
identity matches can still carry an offset in the middle of a record -- through
corruption, through a caller that edited it, or through a caller that built one
by hand. So the offset is proven to sit immediately after a newline before
anything seeks to it, and that proof reads the descriptor `--input` was already
opened and validated on, never the pathname again.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CURSOR_VERSION",
    "Cursor",
    "CursorRefused",
    "MAX_CURSOR_BYTES",
    "parse_cursor",
    "render_cursor",
    "resolve_start_offset",
]

# AC-0022. The schema tag exists so a cursor written by a future version is
# refused loudly rather than misread as this one.
CURSOR_VERSION = 1

# AC-0015. Measured on the argument's UTF-8 bytes, before any parse. A
# conforming cursor carries four integers and comes nowhere near this, so the
# bound only ever fires on something a caller did not get from `--report-cursor`.
#
# It also keeps a digit bomb out of the decoder. CPython refuses to convert an
# integer literal longer than `sys.get_int_max_str_digits()`, which defaults to
# 4300: every argument inside this bound is inside that limit, so `json.loads`
# never meets one.
MAX_CURSOR_BYTES = 4096

_MEMBERS = ("v", "offset", "device", "inode")


class CursorRefused(Exception):
    """The cursor may not be used. The run sends nothing and exits 1."""


@dataclass(frozen=True)
class Cursor:
    """A caller-supplied position, and the file identity it is valid for."""

    offset: int
    device: int
    inode: int


def render_cursor(offset: int, device: int, inode: int) -> str:
    """The one line `--report-cursor` writes to stdout. AC-0001, AC-0022.

    `separators` is pinned: a caller stores this string and hands it back, and
    `json.dumps`' default spacing is not something to leave to a default.
    """
    return json.dumps(
        {"v": CURSOR_VERSION, "offset": offset, "device": device, "inode": inode},
        separators=(",", ":"),
    )


def _integer(value: Any, name: str) -> int:
    """A JSON integer, and not a bool.

    `isinstance(True, int)` is true in Python, so without the bool check a
    cursor carrying `true` for its offset parses as 1 and the run resumes from
    byte one -- inside the first record.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise CursorRefused(f"--from-cursor: {name} is not an integer")
    return value


def parse_cursor(text: str) -> Cursor:
    """Parse the text a prior run printed. Refuse anything else.

    AC-0015 orders the two checks: length first, measured on bytes, before the
    decoder sees the argument. The length refusal is the only one that says
    "too long", which is what makes that ordering observable to a test.
    """
    if len(text.encode("utf-8")) > MAX_CURSOR_BYTES:
        raise CursorRefused(
            f"--from-cursor is too long: over {MAX_CURSOR_BYTES} bytes"
        )
    try:
        value = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - containment, see below
        # Deliberately broad, for the reason `source.py` gives at its own decode
        # seam: the decoder raises more than JSONDecodeError on hostile input.
        # Measured 2026-09-15 that the nesting a 4096-byte argument admits does
        # not reach RecursionError on this interpreter, but the recursion limit
        # is settable by an embedding caller and the catch costs one clause.
        raise CursorRefused(
            f"--from-cursor does not parse as JSON ({type(exc).__name__})"
        ) from exc

    if not isinstance(value, dict):
        raise CursorRefused(
            f"--from-cursor is a {type(value).__name__}, not a JSON object"
        )
    # Set EQUALITY, not containment: an extra member is a refusal rather than
    # something quietly ignored, so a cursor from a version that added a field
    # cannot be half-read by this one.
    if set(value) != set(_MEMBERS):
        raise CursorRefused(
            "--from-cursor must carry exactly "
            + ", ".join(_MEMBERS)
            + f"; got {', '.join(sorted(value)) or 'nothing'}"
        )
    if _integer(value["v"], "v") != CURSOR_VERSION:
        raise CursorRefused(
            f"--from-cursor version {value['v']} is not {CURSOR_VERSION}"
        )
    offset = _integer(value["offset"], "offset")
    if offset < 0:
        raise CursorRefused(f"--from-cursor offset is negative: {offset}")
    return Cursor(
        offset=offset,
        device=_integer(value["device"], "device"),
        inode=_integer(value["inode"], "inode"),
    )


def _report(stream, message: str) -> None:
    print(f"jsonl-otlp-export: {message}", file=stream)


def resolve_start_offset(
    cursor: Cursor | None,
    info: os.stat_result | Any,
    *,
    stream,
    fd: int,
) -> int:
    """Where this run starts reading, given a cursor and the file it opened.

    Exactly four routes, with mutually exclusive preconditions rather than an
    implied precedence:

    - no cursor, or an identity that differs -> byte 0 (AC-0014, AC-0012)
    - identity matches, offset past the end  -> byte 0 (AC-0013)
    - identity matches, in range, misaligned -> refused (AC-0030)
    - anything left                          -> honoured (AC-0011)

    An identity that differs resets whatever its offset says: the offset
    describes a file that is no longer at this path, so comparing it against the
    new file's size would be comparing two unrelated things.
    """
    if cursor is None:
        return 0

    if (cursor.device, cursor.inode) != (info.st_dev, info.st_ino):
        _report(
            stream,
            "the input's identity changed since the cursor was written; "
            "the offset was reset and the file is being read from the start",
        )
        return 0

    if cursor.offset > info.st_size:
        _report(
            stream,
            f"the input shrank below the cursor offset ({info.st_size} bytes "
            f"< {cursor.offset}); the offset was reset and the file is being "
            "read from the start",
        )
        return 0

    if cursor.offset and not _follows_a_newline(fd, cursor.offset):
        # Refused, not reset. A matching identity with a misaligned offset is a
        # corrupted or forged cursor, and resetting it to zero would silently
        # re-send the whole file rather than saying anything was wrong.
        raise CursorRefused(
            f"--from-cursor offset {cursor.offset} is not a record boundary: "
            "the byte before it is not a newline"
        )
    return cursor.offset


def _follows_a_newline(fd: int, offset: int) -> bool:
    """Is byte `offset - 1` a newline?

    Read with `os.pread` from the descriptor `open_input` already proved is a
    regular file inside `--root`. `pread` does not move the file position, so
    the reader still starts where it is told, and using the descriptor rather
    than the pathname means this check inherits that proof instead of reopening
    a name that may since have been replaced.

    `fd` is required rather than defaulted. A default would mean a caller that
    forgets it silently skips a security control, and AC-0030 is the control
    that stops a forged cursor resuming mid-record.
    """
    try:
        return os.pread(fd, 1, offset - 1) == b"\n"
    except OSError:
        return False
