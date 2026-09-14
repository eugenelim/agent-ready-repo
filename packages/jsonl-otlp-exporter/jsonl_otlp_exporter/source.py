"""Reading the input file: what may be opened, and what each line may be.

Two ideas carry this module.

The first is that refusal is decided on the *opened object*. A pathname check
answers a question about a name at one instant; the thing the name refers to can
be swapped immediately afterwards. So the walk holds a descriptor on the root,
opens every component relative to it with `O_NOFOLLOW`, and compares the leaf's
identity before and after opening.

The second is that a run is a stream. Records are yielded one at a time and
never accumulated, which is what makes the residency bound true by construction
rather than by a later check.
"""

from __future__ import annotations

import contextlib
import errno
import json
import os
import stat
import sys
import time
from pathlib import Path
from typing import Any, Iterator

__all__ = [
    "IDLE",
    "InputRefused",
    "MAX_LINE_BYTES",
    "open_input",
    "iter_records",
]

# AC-0018. Measured to and excluding the terminating newline, and enforced on
# bytes before any decode, so a hostile line cannot be decoded and then measured.
MAX_LINE_BYTES = 64 * 1024

_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)


from .transport import IDLE  # noqa: E402 - shared sentinel, one definition


class InputRefused(Exception):
    """The input could not be safely opened. The run sends nothing and exits 1."""


def _identity(info: os.stat_result) -> tuple[int, int]:
    return (info.st_dev, info.st_ino)


def open_input(path: Path | str, root: Path | str | None = None) -> int:
    """Open `path` for reading, proving it is a regular file inside `root`.

    Returns an open read-only file descriptor; the caller owns closing it.

    Every component is opened relative to a descriptor on the root rather than by
    absolute pathname, so a component replaced by a symlink partway through the
    walk cannot redirect it: the replaced component is opened with `O_NOFOLLOW`
    and the open fails. The leaf's identity is captured before the open and
    compared after it, which closes the remaining window.
    """
    root_path = Path(root if root is not None else Path.cwd()).resolve()
    target = Path(path)

    if target.is_absolute():
        # Resolve the target the same way the root was resolved before comparing
        # them. Comparing a resolved root against a lexical path refuses a
        # perfectly ordinary invocation: on macOS `/tmp` and `/var` are symlinks
        # into `/private`, so `--root /tmp/x --input /tmp/x/events.jsonl` had the
        # root resolve to `/private/tmp/x` and the input stay `/tmp/x/...`, and
        # `relative_to` failed.
        #
        # This is a prefilter for deriving components only. Containment is still
        # proven by the descriptor-relative O_NOFOLLOW walk below, so resolving
        # here grants no acceptance that the walk would not also grant.
        try:
            # The PARENT is resolved, never the leaf. Resolving the whole path
            # would follow a symlinked leaf to its target inside the root and
            # accept it -- which AC-0017 forbids and the suite caught. The leaf
            # stays lexical so the O_NOFOLLOW open below is what decides it.
            resolved = target.parent.resolve() / target.name
            relative = resolved.relative_to(root_path)
        except ValueError as exc:
            raise InputRefused(f"input path is outside --root: {target}") from exc
    else:
        relative = target

    parts = [p for p in relative.parts if p not in (".",)]
    if any(p == ".." for p in parts):
        raise InputRefused(f"input path traverses out of --root: {target}")
    if not parts:
        raise InputRefused(f"input path names no file: {target}")

    try:
        before_root = os.lstat(root_path)
        root_fd = os.open(root_path, os.O_RDONLY | _DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise InputRefused(f"--root is not an openable directory: {root_path}") from exc
    if _identity(os.fstat(root_fd)) != _identity(before_root):
        os.close(root_fd)
        raise InputRefused(f"--root changed identity while being opened: {root_path}")
    # The anchor gets the same treatment as the leaf: opened no-follow, with its
    # identity compared against what was examined. Without this the walk proved
    # containment relative to whatever directory the root NAME pointed at when it
    # was opened, not relative to the directory that was resolved.
    #
    # Residual, stated rather than implied: an intermediate component of the
    # root path itself can still be swapped between `Path.resolve()` above and
    # this open. Closing that needs a component-by-component walk from the
    # filesystem root, and the attack needs write access to a parent of --root,
    # which is a stronger position than this tool defends against.

    open_fds = [root_fd]
    try:
        cursor = root_fd
        for component in parts[:-1]:
            try:
                nxt = os.open(
                    component, os.O_RDONLY | _DIRECTORY | os.O_NOFOLLOW, dir_fd=cursor
                )
            except OSError as exc:
                raise InputRefused(
                    f"input path component {component!r} is not a followable directory "
                    f"inside --root ({exc.strerror})"
                ) from exc
            open_fds.append(nxt)
            cursor = nxt

        leaf = parts[-1]
        try:
            before = os.lstat(leaf, dir_fd=cursor)
        except FileNotFoundError as exc:
            raise InputRefused(f"input path does not exist: {target}") from exc
        except OSError as exc:
            raise InputRefused(
                f"input path cannot be examined: {target} ({exc.strerror})"
            ) from exc

        if not stat.S_ISREG(before.st_mode):
            raise InputRefused(f"input is not a regular file: {target}")

        # O_NONBLOCK guards the RACE, not the steady state: the S_ISREG check
        # above already refuses a FIFO that is a FIFO when examined. What it
        # cannot refuse is a path that is a regular file at lstat and a FIFO at
        # open, and opening that blocks until a writer appears.
        #
        # Stated plainly because it is not covered: removing this flag survives
        # the whole suite. The race needs two processes interleaved at one
        # instruction, which no deterministic test here reproduces, so the flag
        # is reasoned protection rather than tested protection.
        try:
            fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | _NONBLOCK, dir_fd=cursor)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, getattr(errno, "EMLINK", errno.ELOOP)):
                raise InputRefused(f"input path is a symbolic link: {target}") from exc
            raise InputRefused(f"input could not be opened: {target} ({exc.strerror})") from exc

        after = os.fstat(fd)
        if not stat.S_ISREG(after.st_mode) or _identity(after) != _identity(before):
            # The name resolved to one object when it was examined and another
            # when it was opened. That is the swap this walk exists to catch.
            os.close(fd)
            raise InputRefused(f"input changed identity between examination and open: {target}")
        return fd
    finally:
        for descriptor in open_fds:
            os.close(descriptor)


def _reject_constant(name: str):
    """Refuse JSON's non-standard constants at the decode seam.

    `json.loads` accepts bare `NaN`, `Infinity` and `-Infinity` by default. None
    is valid JSON, and a float carrying one is written back out by `json.dumps`
    as that same bare token -- so a single such line produces a request body that
    is not JSON and the receiver rejects the whole batch, costing every good
    record in it. Refusing here routes the line into the ordinary skip path.
    """
    raise ValueError(f"{name} is not valid JSON")


def _report(stream, message: str) -> None:
    print(f"jsonl-otlp-export: {message}", file=stream if stream is not None else sys.stderr)


def iter_records(
    fd: int,
    *,
    follow: bool = False,
    for_seconds: int | None = None,
    stream=None,
    poll_interval: float = 0.05,
    clock=time.monotonic,
    on_first_read=None,
) -> Iterator[dict[str, Any]]:
    """Yield one parsed record per well-formed line, skipping the rest.

    Records are yielded, never collected: the caller sees them one at a time and
    the reader holds at most one line plus a partial-line buffer, so the amount
    resident does not grow with the size of the input.

    A bad line never ends the run. Size, parseability and top-level shape each
    skip their own line, report it with its number, and leave the rest of the
    file to be sent -- the whole point of a telemetry sender is that one corrupt
    record does not cost you the others.
    """
    deadline = None if for_seconds is None else clock() + for_seconds
    # One-shot reads the file ONCE (AC-0020). Bounding the pass at the size the
    # descriptor had when it was opened is what makes that true: against a writer
    # appending faster than the reader drains, `os.read` never returns empty, the
    # `if not follow: return` below is unreachable, and the run neither sends nor
    # exits.
    budget = None
    if not follow:
        with contextlib.suppress(OSError):
            budget = os.fstat(fd).st_size
    buffer = bytearray()
    line_number = 0
    # True while discarding the tail of a line already refused for length. Its
    # own newline ends the discard, and it must NOT be counted again -- counting
    # it would shift every later line number by one and make every subsequent
    # report point at the wrong line.
    discarding = False
    stamped = False

    while True:
        if not stamped:
            # AC-0042 measures `--for` from here. The sender needs the same
            # instant, because its own bound cannot be anchored at the run's
            # start: resolution happens before any read.
            stamped = True
            if on_first_read is not None:
                on_first_read(clock())
        # Checked on EVERY pass, not only when the file went quiet. A file being
        # appended at least as fast as it is parsed never reaches the no-bytes
        # branch, so a deadline tested only there is never evaluated at all and
        # `--for` does not bound the run.
        if deadline is not None and clock() >= deadline:
            return
        want = 65536 if budget is None else max(0, min(65536, budget))
        chunk = os.read(fd, want) if want else b""
        if budget is not None:
            budget -= len(chunk)
        if chunk:
            buffer.extend(chunk)
            while True:
                index = buffer.find(b"\n")
                if index < 0:
                    if discarding:
                        buffer.clear()
                    elif len(buffer) > MAX_LINE_BYTES:
                        # Refuse before decoding and stop buffering: the line is
                        # already over the ceiling, so reading the rest of it in
                        # is exactly the allocation the ceiling exists to deny.
                        line_number += 1
                        _report(
                            stream,
                            f"line {line_number}: over {MAX_LINE_BYTES} bytes; skipped",
                        )
                        buffer.clear()
                        discarding = True
                    break

                raw = bytes(buffer[:index])
                del buffer[: index + 1]
                if discarding:
                    discarding = False
                    continue

                if deadline is not None and clock() >= deadline:
                    # One 64 KiB read can hold far more than a batch, so draining
                    # it without rechecking yields records -- and issues requests
                    # -- after `--for` has already elapsed.
                    return

                line_number += 1
                if len(raw) > MAX_LINE_BYTES:
                    _report(stream, f"line {line_number}: over {MAX_LINE_BYTES} bytes; skipped")
                    continue
                try:
                    value = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
                except Exception as exc:  # noqa: BLE001 - containment, see below
                    # Deliberately broad. A line is untrusted, and the decoder
                    # raises more than JSONDecodeError on hostile input: about
                    # 16,000 levels of nesting exceeds the interpreter's
                    # recursion limit while still fitting inside the 64 KiB line
                    # ceiling, and it arrives as RecursionError. Naming only the
                    # two expected exception types let one line end the run and
                    # cost every later line, which is the opposite of what the
                    # Boundaries require.
                    _report(
                        stream,
                        f"line {line_number}: does not parse as JSON "
                        f"({type(exc).__name__}); skipped",
                    )
                    continue
                if not isinstance(value, dict):
                    _report(
                        stream,
                        f"line {line_number}: top-level JSON value is "
                        f"{type(value).__name__}, not an object; skipped",
                    )
                    continue
                yield value
            continue

        # No bytes available right now.
        if not follow:
            return
        if deadline is not None and clock() >= deadline:
            return
        # Tell the consumer we have caught up. Under bare `--follow` there is no
        # deadline and the iterator never ends, so without this a partial batch
        # is held until 512 records arrive and an appended line is never sent.
        yield IDLE
        time.sleep(poll_interval)
