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
import tomllib
from pathlib import Path
from typing import Any, Mapping

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
    """
    if path is None:
        return {}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError:
        return {}
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
        raw = os.read(fd, MAX_CONFIG_BYTES)
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
    finally:
        os.close(fd)
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigRefused(f"config file does not parse as TOML: {_shown(path)} ({exc})") from exc


def _present(env: Mapping[str, str], name: str) -> str | None:
    """A variable exported with an empty value is not a present source.

    Treating it as present lets `export OTEL_EXPORTER_OTLP_ENDPOINT=` silently
    shadow a configured file and turn sending off with no diagnostic.
    """
    value = env.get(name, "")
    return value if value.strip() else None


def _scope_settings(path: Path | str | None) -> dict[str, str]:
    """Read one scope's `[telemetry]` table, or `{}` when it declares none."""
    if path is None:
        return {}
    table = read_config_file(path).get("telemetry")
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
    """
    scopes = (
        ("repository", config_path, _scope_settings(config_path)),
        ("user", user_config_path, _scope_settings(user_config_path)),
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
