"""The profile: what a caller is allowed to declare, and how it is loaded.

A profile is *data*. It is parsed as TOML and nothing else -- never imported,
never evaluated -- and that is what keeps the extension point affordable. Had a
profile been code, loading one would be arbitrary execution inside a process
that reads untrusted files and holds a network endpoint, and a hostile profile
could disable the very payload control it exists to declare.

The key set is closed in both directions. A missing key is a profile that does
not say what it must; an extra key is a profile expressing something this format
does not define, which would be silently ignored and silently wrong.
"""

from __future__ import annotations

import os
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "Profile",
    "ProfileRefused",
    "MAX_PROFILE_BYTES",
    "REQUIRED_KEYS",
    "TIMESTAMP_FORMATS",
    "default_service_name",
    "load_profile",
    "parse_profile",
]

# AC-0051. Same ceiling as the config file, for the same reason.
MAX_PROFILE_BYTES = 64 * 1024

# AC-0035. Exactly these, in both directions.
REQUIRED_KEYS = frozenset(
    {
        "timestamp_field",
        "timestamp_format",
        "severity_field",
        "severity_map",
        "identity",
        "allowlist",
    }
)

# AC-0049. A closed enum, so an unrecognised format cannot be guessed at.
TIMESTAMP_FORMATS = frozenset({"rfc3339", "epoch-millis", "epoch-seconds"})

# AC-0067. OTLP severity numbers run 1-24. Zero is SEVERITY_NUMBER_UNSPECIFIED,
# which a backend cannot tell apart from a field that was never set, so admitting
# it would let a profile express "unknown" in a way no consumer can query.
MIN_SEVERITY_NUMBER = 1
MAX_SEVERITY_NUMBER = 24

_NONBLOCK = getattr(os, "O_NONBLOCK", 0)


class ProfileRefused(Exception):
    """The profile is not usable. The run sends nothing and exits 1."""


@dataclass(frozen=True)
class Profile:
    """A validated profile. Every field here has already been type-checked."""

    timestamp_field: str
    timestamp_format: str
    severity_field: str
    severity_map: Mapping[str, int]
    identity: tuple[str, ...]
    allowlist: tuple[str, ...]

    @property
    def routed_fields(self) -> frozenset[str]:
        """Fields with a declared destination of their own.

        These reach their destination whether or not the allowlist names them,
        and are never *also* emitted as attributes -- one field, one place.
        """
        return frozenset({self.timestamp_field, self.severity_field, *self.identity})


def _require_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str):
        raise ProfileRefused(f"{key} must be a string, not {type(value).__name__}")
    return value


def _require_str_list(raw: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = raw[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileRefused(f"{key} must be a list of strings")
    return tuple(value)


def parse_profile(raw: Mapping[str, Any]) -> Profile:
    """Validate an already-parsed TOML mapping into a Profile, or refuse it."""
    present = set(raw)
    missing = REQUIRED_KEYS - present
    if missing:
        raise ProfileRefused(f"profile is missing required key(s): {sorted(missing)}")
    extra = present - REQUIRED_KEYS
    if extra:
        raise ProfileRefused(
            f"profile carries key(s) this format does not define: {sorted(extra)}"
        )

    timestamp_format = _require_str(raw, "timestamp_format")
    if timestamp_format not in TIMESTAMP_FORMATS:
        raise ProfileRefused(
            f"timestamp_format {timestamp_format!r} is not one of {sorted(TIMESTAMP_FORMATS)}"
        )

    severity_map = raw["severity_map"]
    if not isinstance(severity_map, dict):
        raise ProfileRefused("severity_map must be a table")
    for key, value in severity_map.items():
        # `bool` is an `int` subclass in Python, so `true` in TOML would sail
        # through an isinstance check and be emitted as severity 1.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProfileRefused(f"severity_map[{key!r}] must be an integer")
        if not MIN_SEVERITY_NUMBER <= value <= MAX_SEVERITY_NUMBER:
            raise ProfileRefused(
                f"severity_map[{key!r}] is {value}, outside OTLP's "
                f"{MIN_SEVERITY_NUMBER}-{MAX_SEVERITY_NUMBER} severity range"
            )

    return Profile(
        timestamp_field=_require_str(raw, "timestamp_field"),
        timestamp_format=timestamp_format,
        severity_field=_require_str(raw, "severity_field"),
        severity_map=dict(severity_map),
        identity=_require_str_list(raw, "identity"),
        allowlist=_require_str_list(raw, "allowlist"),
    )


def default_service_name(profile_path: Path | str) -> str:
    """AC-0007's default: the stem of the --profile filename.

    The profile itself cannot supply a name -- AC-0035 closes it at six keys and
    none of them is one -- so the default comes from the filename the caller
    chose. That keeps the name under the caller's control without adding a
    seventh key or making --service-name mandatory.
    """
    return Path(profile_path).stem


def load_profile(path: Path | str | None, root: Path | str | None = None) -> Profile:
    """Load and validate the profile at `path`.

    `path` is required: there is no built-in profile to fall back to. A default
    would decide what leaves the machine on the caller's behalf, which is the one
    decision this tool must never make for them.
    """
    if path is None:
        raise ProfileRefused(
            "no --profile given; this command has no built-in profile and will not "
            "guess what may be sent"
        )

    # Opened under the same discipline as the input file, root confinement
    # included: a profile decides the payload, so it is data this tool acts on,
    # not configuration the operator points at from anywhere.
    from .source import InputRefused, open_input

    try:
        fd = open_input(path, root)
    except InputRefused as exc:
        raise ProfileRefused(f"profile could not be opened: {exc}") from exc

    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ProfileRefused(f"profile is not a regular file: {path}")
        if info.st_size > MAX_PROFILE_BYTES:
            raise ProfileRefused(
                f"profile is {info.st_size} bytes, over the {MAX_PROFILE_BYTES}-byte ceiling"
            )
        raw_bytes = os.read(fd, MAX_PROFILE_BYTES)
        if len(raw_bytes) != info.st_size:
            # Same reasoning as the config file: a valid prefix would be accepted
            # as a whole profile, and the profile decides what may be sent.
            raise ProfileRefused(
                f"profile read returned {len(raw_bytes)} of {info.st_size} bytes"
            )
    finally:
        os.close(fd)

    try:
        parsed = tomllib.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ProfileRefused(f"profile does not parse as TOML: {exc}") from exc
    return parse_profile(parsed)
