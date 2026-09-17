"""Endpoint resolution across the two configuration scopes.

Four sources in a fixed order: two environment variables, then `[telemetry]`
from each of two optional TOML files. Each file is opened under the same
open-time discipline the input file gets -- no-follow, proven on the descriptor
to be a regular file that is neither a reparse point nor multiply linked -- but
deliberately without root confinement, because a configuration file legitimately
lives outside any data root, and with a second scope that is the normal case
rather than the tolerated one.

The two files merge per setting rather than per file, so a configuration split
across them reaches the command whole. The caller names both paths; nothing here
derives a filename or searches a directory, which is what keeps this command
free of any particular product's layout.
"""

from __future__ import annotations

import os
import stat
import threading
import time
import tomllib
from pathlib import Path
from typing import Any, Callable, Mapping

__all__ = [
    "ConfigRefused",
    "MAX_CONFIG_BYTES",
    "read_config_file",
    "resolve_endpoint",
    "resolve_telemetry",
]

# AC-0075. The settings `[telemetry]` admits, and the only declaration of them.
# Deliberately private: nothing outside this module reads it. It backs the
# refusal message, and a wrong value shows up as a wrong message rather than as
# a second declaration drifting from a first -- which is the failure that made
# the repository-side resolver worth retiring rather than keeping in step.
_TELEMETRY_SETTINGS = ("endpoint", "service_name")

# AC-0056. The ceiling is on the file, checked on the opened descriptor before a
# byte is parsed, so a hostile file cannot be parsed and then measured.
MAX_CONFIG_BYTES = 64 * 1024

# AC-0077. Configuration acquisition -- opening, proving and reading every
# supplied file -- is abandoned this many seconds after it begins. Deliberately
# private: nothing outside this module needs the number, and the README states
# the bound as a behaviour an adopter can hit rather than as an importable
# constant. Not derived from transport.REQUEST_TIMEOUT_SECONDS or
# RUN_TIMEOUT_SECONDS -- both start at the first destination resolution, which
# happens only after this I/O has finished, so there is no ordering relation
# to preserve.
_CONFIG_TIMEOUT_SECONDS = 5

_LOGS_ENDPOINT_VAR = "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"
_BASE_ENDPOINT_VAR = "OTEL_EXPORTER_OTLP_ENDPOINT"
_LOGS_PATH = "/v1/logs"


class ConfigRefused(Exception):
    """A configuration input was refused. The run sends nothing and exits 1."""


def _shown(path: Path | str) -> str:
    """A path rendered so it cannot forge a diagnostic line or repaint a terminal.

    Every path in this module is caller-supplied and every refusal below reaches
    stderr through `cli.main`, so a filename carrying a newline could otherwise
    invent a second diagnostic and one carrying an escape sequence could recolour
    or erase the display. `repr` escapes both. Applied at *every* site rather
    than where hostile input seems likely: a reviewer found the unknown-key
    message escaping its path while eight others did not, which is what a
    per-site judgement call degrades into.
    """
    return repr(str(path))


def read_config_file(path: Path | str | None) -> dict[str, Any]:
    """Read `path` as TOML, or return `{}` when there is no file to read.

    Absence is not a refusal: `--config` is optional, and an absent file simply
    contributes no values. Everything else about the path *is* a refusal, and it
    is decided on the object the descriptor names rather than on the pathname --
    a pathname check is a different question, asked at a different instant, about
    a thing that can be swapped in between.

    AC-0077: the open, the descriptor checks and the read are all bounded
    together, by a deadline this call establishes for itself from
    `_CONFIG_TIMEOUT_SECONDS` -- so a direct caller is bounded by default, the
    same as `resolve_telemetry` below, which instead shares one deadline across
    both configuration scopes.
    """
    return _read_config_file(path, time.monotonic() + _CONFIG_TIMEOUT_SECONDS)


def _read_config_file(path: Path | str | None, deadline: float) -> dict[str, Any]:
    """`read_config_file`'s body, taking an already-established deadline.

    Split out so `resolve_telemetry` can pass one shared deadline down both
    scopes -- AC-0077's bound covers acquiring every supplied file together,
    not a file at a time, so a second file must not be able to extend it.
    """
    if path is None:
        return {}
    raw = _acquire_bytes(path, deadline)
    if raw is None:
        return {}
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigRefused(f"config file does not parse as TOML: {_shown(path)} ({exc})") from exc


def _acquire_bytes(path: Path | str, deadline: float) -> bytes | None:
    """Open, prove and read one file's bytes, bounded by `deadline`.

    Returns `None` for a path that does not exist -- mirroring
    `read_config_file`'s absence-is-not-a-refusal contract -- and the file's
    raw bytes otherwise. The open, the descriptor checks and the read all run
    inside `_do`, on the single abandonable worker `_run_bounded` starts:
    `open(2)` on an unresponsive mount blocks before `O_NONBLOCK` applies, and
    neither `fstat(2)` nor a regular-file `read(2)` accepts a timeout, so none
    of the three can be bounded from the calling thread alone.
    """

    def _do() -> bytes | None:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0))
        except FileNotFoundError:
            return None
        except OSError as exc:
            # O_NOFOLLOW on a symlink raises ELOOP here (EMLINK on some BSDs), and a
            # FIFO with no writer is why O_NONBLOCK is set: without it the open
            # itself would hang before any check could run.
            raise ConfigRefused(
                f"config file refused at open: {_shown(path)} ({exc.strerror})"
            ) from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ConfigRefused(f"config file is not a regular file: {_shown(path)}")
            # Both were applied by the confinement helper this read replaced, and
            # neither needs a root, so both survive a path-valued interface. A
            # reparse point is Windows' redirection primitive and `O_NOFOLLOW` does
            # not catch it; a hard link means the bytes have a second name that can
            # be rewritten after this descriptor was checked.
            if getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
            ):
                raise ConfigRefused(f"config file is a reparse point: {_shown(path)}")
            if info.st_nlink > 1:
                raise ConfigRefused(f"config file is hard-linked: {_shown(path)}")
            if info.st_size > MAX_CONFIG_BYTES:
                raise ConfigRefused(
                    f"config file is {info.st_size} bytes, over the "
                    f"{MAX_CONFIG_BYTES}-byte ceiling: {_shown(path)}"
                )
            # AC-0056/AC-0001. One extra byte beyond the ceiling: a file that was
            # exactly `MAX_CONFIG_BYTES` at the sample above and has not grown
            # still returns exactly that many bytes here, so the accepted side is
            # unaffected; a file that grew past the ceiling since the sample
            # returns more, which the re-sample below turns into a refusal rather
            # than a silently-accepted prefix.
            raw = os.read(fd, MAX_CONFIG_BYTES + 1)
            grown = os.fstat(fd)
            if grown.st_size != info.st_size:
                # Decided on the complete file, not the sampled one: a concurrent
                # writer that appends -- or truncates -- between the sample above
                # and this read leaves the sampled size stale, and a size
                # unchanged across the read is what establishes that the bytes
                # obtained are the whole file as of the read. Placed ahead of the
                # short-read comparison below so a grown file gets a message
                # naming the change rather than that comparison's "read returned
                # N of M bytes", which reads as truncation when the real event
                # can be either direction -- stated as a size change, not as
                # growth, so a concurrent shrink is not reported as having grown.
                raise ConfigRefused(
                    f"config file size changed from {info.st_size} to "
                    f"{grown.st_size} bytes during the read: {_shown(path)}"
                )
            if len(raw) != info.st_size:
                # `os.read` is one `read(2)` and may return fewer bytes than asked
                # for. A prefix of a TOML file can be valid TOML, so parsing it would
                # accept an incomplete config as complete -- and enable sending from
                # a file whose full content does not parse. Not reachable for a local
                # regular file under the ceiling; reachable on a network or FUSE
                # mount, which is exactly where a truncated read is plausible.
                raise ConfigRefused(
                    f"config file read returned {len(raw)} of {info.st_size} bytes: {_shown(path)}"
                )
            # AC-0001. The buffer and the re-sample above still leave one
            # residue: a read that returns exactly the sampled bytes while the
            # file has grown underneath it *and* the re-sampled `fstat` reports
            # stale, pre-growth metadata -- the same cached-metadata divergence
            # a network or FUSE mount can produce between a `read(2)` and an
            # `fstat(2)` on the same descriptor, seen here in the direction the
            # two checks above cannot catch. One more single-byte `os.read`
            # proves no byte remains beyond what was obtained: at genuine EOF it
            # returns `b""`, and any other result means the file holds more than
            # this call just accepted. One fixed-size probe, not a read loop --
            # a loop trades this rare case for an unbounded read over a file a
            # writer can keep extending.
            if os.read(fd, 1):
                raise ConfigRefused(
                    f"config file has bytes beyond the {len(raw)} obtained "
                    f"during the read: {_shown(path)}"
                )
            return raw
        finally:
            os.close(fd)

    return _run_bounded(_do, path, deadline)


def _acquisition_bound_refused(path: Path | str) -> ConfigRefused:
    """The one raise site for both ways `_run_bounded` can time out.

    A deadline found already spent, and a join that timed out, are the same
    fact from the caller's perspective -- the bound was exceeded -- so they
    carry one message rather than two that could drift apart. Same move
    `_shown` already makes for path rendering in this module: one place for
    a fact several sites would otherwise each restate.
    """
    return ConfigRefused(
        f"config file acquisition exceeded the {_CONFIG_TIMEOUT_SECONDS:g}s "
        f"bound: {_shown(path)}"
    )


def _run_bounded(
    func: Callable[[], bytes | None], path: Path | str, deadline: float
) -> bytes | None:
    """Run `func` on an abandonable daemon worker, bounded by `deadline`.

    Reused by shape from `transport._resolve_bounded`, not by import: `config`
    must not depend on `transport`, which pulls in `socket` and `http.client`,
    and a configuration reader that cannot be read without the transport would
    be a layering inversion in a package whose whole point is that the
    off-by-default path opens no socket. The trade is the same one
    `_resolve_bounded` makes for a hung resolver -- an abandoned worker holds
    one open descriptor until the process exits, which is strictly better than
    the caller inheriting its stall.

    A deadline already passed when called refuses without starting a worker,
    which is what keeps a second file from buying itself a fresh budget after
    the first one spent it all.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _acquisition_bound_refused(path)

    outcome: dict[str, Any] = {}

    def _call() -> None:
        try:
            outcome["value"] = func()
        except BaseException as exc:  # noqa: BLE001 - re-raised on the caller's thread
            outcome["error"] = exc

    worker = threading.Thread(target=_call, daemon=True)
    worker.start()
    worker.join(remaining)
    if worker.is_alive():
        raise _acquisition_bound_refused(path)
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


def _present(env: Mapping[str, str], name: str) -> str | None:
    """A variable exported with an empty value is not a present source.

    Treating it as present lets `export OTEL_EXPORTER_OTLP_ENDPOINT=` silently
    shadow a configured file and turn sending off with no diagnostic.
    """
    value = env.get(name, "")
    return value if value.strip() else None


def _scope_settings(path: Path | str | None, deadline: float) -> dict[str, str]:
    """Read one scope's `[telemetry]` table, or `{}` when it declares none."""
    if path is None:
        return {}
    table = _read_config_file(path, deadline).get("telemetry")
    if table is None:
        return {}
    if not isinstance(table, dict):
        raise ConfigRefused(f"[telemetry] must be a table: {_shown(path)}")
    settings: dict[str, str] = {}
    for key, value in table.items():
        if not isinstance(value, str) or not value.strip():
            # `!r` on the key: it comes from an untrusted file and reaches a
            # terminal, so a newline must not forge a second diagnostic line and
            # an escape sequence must not repaint the display.
            raise ConfigRefused(
                f"[telemetry].{key!r} must be a non-empty string: {_shown(path)}"
            )
        settings[key] = value
    return settings


def resolve_telemetry(
    config_path: Path | str | None = None,
    user_config_path: Path | str | None = None,
) -> dict[str, str]:
    """Merge both scopes' `[telemetry]` settings, refusing one we cannot deliver.

    AC-0074: the merge is per setting, not per scope. `--config` wins for each
    setting it declares, and only a setting it omits falls through to
    `--user-config` -- so a scope declaring `service_name` and no endpoint still
    contributes its `service_name` while the endpoint comes from the other file.
    Selecting one whole file instead would silently drop the other's settings,
    and no single file can carry a configuration split across two.

    AC-0075/AC-0076: every supplied file is read here, before any endpoint
    precedence runs, so a key this command cannot deliver is refused whatever
    configures the endpoint. A setting with no route is refused rather than
    dropped because these values decide where data is sent, and a dropped one
    fails open.

    AC-0077: one deadline is established here, before the repository scope's
    file is opened, and passed down both scopes -- so acquiring the second
    file cannot buy the whole read a second bound's worth of time.
    """
    deadline = time.monotonic() + _CONFIG_TIMEOUT_SECONDS
    scopes = (
        ("repository", config_path, _scope_settings(config_path, deadline)),
        ("user", user_config_path, _scope_settings(user_config_path, deadline)),
    )
    merged: dict[str, str] = {}
    for _, _, settings in reversed(scopes):
        merged.update(settings)

    undeliverable = sorted(set(merged) - set(_TELEMETRY_SETTINGS))
    if undeliverable:
        # Name the file each key came from. The merged mapping has already lost
        # that, and two files were read: without the scope the reader has to open
        # both to find out which one to edit, and a key present in both looks
        # like a key present in one. Paths are rendered with `!r` for the same
        # reason the keys are -- a path is caller-supplied and reaches the same
        # terminal.
        reported = ", ".join(
            "{} (from {})".format(
                repr(name),
                " and ".join(
                    f"{label} {_shown(path)}"
                    for label, path, settings in scopes
                    if name in settings
                ),
            )
            for name in undeliverable
        )
        raise ConfigRefused(
            "[telemetry] settings this command cannot receive: "
            + reported
            + f" (admitted: {', '.join(sorted(_TELEMETRY_SETTINGS))})"
        )
    return merged


def resolve_endpoint(
    env: Mapping[str, str], settings: Mapping[str, str] | None = None
) -> str | None:
    """Return the URL to POST to, or None when no source configures one.

    AC-0002, in order: the logs-specific variable, the base variable, then
    `[telemetry].endpoint` as `resolve_telemetry` merged it across the two
    configuration scopes. The logs-specific variable is already a signal-specific
    URL by OpenTelemetry convention, so it is used verbatim; every other source
    names a base and gains the signal path.

    This takes already-merged settings rather than a path. Reading a file here
    would make the read conditional on the variables above being absent, which is
    what AC-0076 forbids: the refusal in `resolve_telemetry` would then never fire
    for anyone who exports an endpoint variable.
    """
    logs = _present(env, _LOGS_ENDPOINT_VAR)
    if logs is not None:
        return logs

    base = _present(env, _BASE_ENDPOINT_VAR)
    if base is None:
        value = (settings or {}).get("endpoint", "")
        base = value if value.strip() else None
    if base is None:
        return None
    return base.rstrip("/") + _LOGS_PATH
