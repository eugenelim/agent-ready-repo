"""Endpoint resolution, and the proof that nothing is sent until one resolves.

Three sources, in a fixed order, and one optional TOML file. The file is opened
under the same open-time discipline the input file gets -- no-follow, proven a
regular file on the descriptor -- but deliberately without root confinement,
because a configuration file legitimately lives outside any data root.
"""

from __future__ import annotations

import os
import stat
import sys
import tomllib
from pathlib import Path
from typing import Any, Callable, Mapping

__all__ = [
    "ConfigRefused",
    "MAX_CONFIG_BYTES",
    "read_config_file",
    "resolve_endpoint",
    "run_unconfigured_check",
]

# AC-0056. The ceiling is on the file, checked on the opened descriptor before a
# byte is parsed, so a hostile file cannot be parsed and then measured.
MAX_CONFIG_BYTES = 64 * 1024

_LOGS_ENDPOINT_VAR = "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"
_BASE_ENDPOINT_VAR = "OTEL_EXPORTER_OTLP_ENDPOINT"
_LOGS_PATH = "/v1/logs"


class ConfigRefused(Exception):
    """A configuration input was refused. The run sends nothing and exits 1."""


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
        raise ConfigRefused(f"config file refused at open: {path} ({exc.strerror})") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ConfigRefused(f"config file is not a regular file: {path}")
        if info.st_size > MAX_CONFIG_BYTES:
            raise ConfigRefused(
                f"config file is {info.st_size} bytes, over the "
                f"{MAX_CONFIG_BYTES}-byte ceiling: {path}"
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
                f"config file read returned {len(raw)} of {info.st_size} bytes: {path}"
            )
    finally:
        os.close(fd)
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigRefused(f"config file does not parse as TOML: {path} ({exc})") from exc


def _present(env: Mapping[str, str], name: str) -> str | None:
    """A variable exported with an empty value is not a present source.

    Treating it as present lets `export OTEL_EXPORTER_OTLP_ENDPOINT=` silently
    shadow a configured file and turn sending off with no diagnostic.
    """
    value = env.get(name, "")
    return value if value.strip() else None


def resolve_endpoint(
    env: Mapping[str, str], config_path: Path | str | None
) -> str | None:
    """Return the URL to POST to, or None when no source configures one.

    The logs-specific variable is already a signal-specific URL by OpenTelemetry
    convention, so it is used verbatim; every other source names a base and gains
    the signal path.
    """
    logs = _present(env, _LOGS_ENDPOINT_VAR)
    if logs is not None:
        return logs

    base = _present(env, _BASE_ENDPOINT_VAR)
    if base is None:
        configured = read_config_file(config_path).get("telemetry", {})
        if isinstance(configured, dict):
            value = configured.get("endpoint", "")
            base = value if isinstance(value, str) and value.strip() else None
    if base is None:
        return None
    return base.rstrip("/") + _LOGS_PATH


def run_unconfigured_check(
    env: Mapping[str, str],
    config_path: Path | str | None,
    transport_factory: Callable[..., Any],
    stream=None,
) -> int | None:
    """Resolve the endpoint; when none does, say so and stop without a transport.

    Returns the run's status when there is no endpoint, and `None` when one
    resolved, meaning "not this function's case -- carry on with the run". What
    happens once an endpoint exists belongs to the transport and CLI tasks, not
    here.

    `transport_factory` is taken as an argument rather than imported so the
    off-by-default guarantee is provable: a caller can pass a factory that raises
    on construction, and "no socket was opened" becomes an assertion about this
    function instead of an assertion about the whole process.
    """
    endpoint = resolve_endpoint(env, config_path)
    if endpoint is not None:
        # Constructing here is what makes the unconfigured case's assertion mean
        # something: the factory is genuinely reached on one branch, so a test
        # passing a factory that raises proves the other branch does not reach
        # it. A parameter no branch ever uses would assert nothing.
        transport_factory(endpoint)
        return None
    print(
        "jsonl-otlp-export: no endpoint is configured; nothing was sent. "
        f"Set {_LOGS_ENDPOINT_VAR} or {_BASE_ENDPOINT_VAR}, or give --config a "
        "TOML file declaring [telemetry].endpoint.",
        file=stream if stream is not None else sys.stderr,
    )
    return 0
