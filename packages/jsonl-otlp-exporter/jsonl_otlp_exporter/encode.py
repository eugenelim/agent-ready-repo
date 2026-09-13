"""Turning records into an OTLP/HTTP JSON logs request body.

Pure functions, no I/O. Everything here is decided by the active profile plus
the conversion rules ADR-0114 settles, so the same record and profile always
produce the same bytes.

Two emission rules are load-bearing for ingestion, measured against a real
Collector: identifiers are hex rather than base64, and attributes use the
`AnyValue` wrapper list rather than a flat object. The rest is convention.
"""

from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Iterable, Mapping

from .profile import Profile

__all__ = [
    "MAX_NESTING_DEPTH",
    "RecordSkipped",
    "any_value",
    "encode_records",
    "to_unix_nanos",
]

# AC-0072. Recursion has to stop somewhere or a hostile record walks the encoder
# without limit. Eight is well past any real envelope -- the deepest field the
# first consumer has is one object one level down.
MAX_NESTING_DEPTH = 8

_NANOS_PER_SECOND = 1_000_000_000
_NANOS_PER_MILLI = 1_000_000

# uint64 on the wire, but kept inside signed 64-bit so a consumer reading it as
# int64 -- which most do -- cannot see a negative instant.
_MAX_UNIX_NANOS = 2**63

_DIGITS = re.compile(r"^-?[0-9]+$")
_EPOCH = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)
_INF = float("inf")

# RFC 3339 with a MANDATORY offset. `fromisoformat` would happily accept a naive
# string and produce a naive datetime, which is exactly the guess this refuses.
_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d{1,9})?([Zz]|[+-]\d{2}:\d{2})$"
)


class RecordSkipped(Exception):
    """This record cannot be encoded. Skip it, report it, keep the run going."""


def to_unix_nanos(value: Any, timestamp_format: str) -> int:
    """Convert a record's timestamp to nanoseconds since the Unix epoch.

    Raises RecordSkipped rather than guessing. A wrong timestamp is worse than an
    absent record, because it is indistinguishable from a real one.
    """
    if timestamp_format == "rfc3339":
        if not isinstance(value, str) or not _RFC3339.match(value):
            raise RecordSkipped(
                f"timestamp {value!r} is not RFC 3339 with an explicit offset"
            )
        text = value.replace(" ", "T")
        # `fromisoformat` handles Z only from 3.11 onward; normalising keeps the
        # parse identical across the supported range.
        if text[-1] in "Zz":
            text = text[:-1] + "+00:00"
        try:
            parsed = _dt.datetime.fromisoformat(text)
        except ValueError as exc:
            # `2026-02-30T00:00:00Z` matches the regex -- which constrains shape,
            # not the calendar -- and only the parse knows the month has no 30th.
            # Letting this escape kills the whole run over one bad record.
            raise RecordSkipped(f"timestamp {value!r} is not a real instant ({exc})") from exc
        # Whole-second arithmetic against a fixed epoch, in integers. Going via
        # `timestamp()` would round-trip through a float and `int()` truncates
        # toward zero, so a pre-1970 instant would land one second late.
        delta = parsed - _EPOCH
        nanos = (delta.days * 86400 + delta.seconds) * _NANOS_PER_SECOND
        fraction = _RFC3339.match(value).group(1)
        if fraction:
            # Right-pad to nanoseconds. `microsecond` alone truncates at six
            # digits and would silently drop a nanosecond-precision source.
            nanos += int((fraction[1:] + "000000000")[:9])
    elif timestamp_format in ("epoch-millis", "epoch-seconds"):
        if isinstance(value, bool):
            raise RecordSkipped(f"timestamp {value!r} is a boolean, not an integer")
        if isinstance(value, int):
            number = value
        elif isinstance(value, str) and _DIGITS.match(value):
            try:
                number = int(value)
            except ValueError as exc:
                # CPython refuses to convert a decimal string past 4300 digits.
                # A 4301-digit line is well inside the 64 KiB line ceiling.
                raise RecordSkipped(
                    f"timestamp {value[:32]!r}... is not convertible ({exc})"
                ) from exc
        else:
            # A float is refused rather than rounded: it cannot represent a
            # nanosecond instant exactly, and the rounding is invisible later.
            raise RecordSkipped(
                f"timestamp {value!r} is not an integer under {timestamp_format}"
            )
        scale = _NANOS_PER_MILLI if timestamp_format == "epoch-millis" else _NANOS_PER_SECOND
        nanos = number * scale
    else:  # pragma: no cover - the profile validator closes this enum
        raise RecordSkipped(f"unknown timestamp_format {timestamp_format!r}")

    if not 0 <= nanos < _MAX_UNIX_NANOS:
        raise RecordSkipped(f"timestamp {value!r} converts outside the representable range")
    return nanos


class _TooDeep:
    """Sentinel: this value nests past the ceiling.

    Distinct from `None`, which means JSON `null`. Collapsing the two is what
    made an over-depth descendant vanish while its ancestors still emitted -- so
    the attribute survived as an empty container instead of being dropped and
    reported.
    """


TOO_DEEP = _TooDeep()


def any_value(value: Any, depth: int = 0) -> dict[str, Any] | None | _TooDeep:
    """Wrap a JSON value as an OTLP `AnyValue`, or say why it is not emitted.

    Returns `None` for JSON `null` and `TOO_DEEP` for anything past the nesting
    ceiling. An omitted key is queryable ("this record has no such field"); an
    empty AnyValue is not.
    """
    if value is None:
        return None
    if depth > MAX_NESTING_DEPTH:
        return TOO_DEEP
    if isinstance(value, bool):
        # Checked before int: bool is an int subclass, and a true/false emitted
        # as intValue 1/0 loses the type a consumer filters on.
        return {"boolValue": value}
    if isinstance(value, float) and (value != value or value in (_INF, -_INF)):
        # proto3 JSON represents a non-finite double as a quoted string. Emitting
        # the bare Python repr instead produces `NaN` or `Infinity` in the body,
        # which is not JSON at all -- the receiver rejects the whole request and
        # one odd number costs every good record batched with it.
        return {"doubleValue": "NaN" if value != value else
                ("Infinity" if value > 0 else "-Infinity")}
    if isinstance(value, int):
        if -(2**63) <= value < 2**63:
            # proto3 JSON carries 64-bit integers as quoted strings. A receiver
            # accepts a bare number too, but the quoted form is what the spec
            # says and what survives a JSON parser with 53-bit floats.
            return {"intValue": str(value)}
        # An integer too large for a double raises OverflowError rather than
        # returning inf, and that escapes the encoder.
        try:
            return {"doubleValue": float(value)}
        except OverflowError:
            return {"doubleValue": "Infinity" if value > 0 else "-Infinity"}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, list):
        members = []
        for item in value:
            wrapped = any_value(item, depth + 1)
            if wrapped is TOO_DEEP:
                return TOO_DEEP
            if wrapped is not None:
                members.append(wrapped)
        return {"arrayValue": {"values": members}}
    if isinstance(value, dict):
        entries = []
        for key, item in value.items():
            wrapped = any_value(item, depth + 1)
            if wrapped is TOO_DEEP:
                return TOO_DEEP
            if wrapped is not None:
                entries.append({"key": str(key), "value": wrapped})
        return {"kvlistValue": {"values": entries}}
    return {"stringValue": str(value)}


def _attributes(
    record: Mapping[str, Any], profile: Profile, dropped_deep: list[str]
) -> list[dict[str, Any]]:
    """Build the attribute list: allowlisted fields only, routed fields excluded."""
    routed = profile.routed_fields
    attributes: list[dict[str, Any]] = []
    for name in profile.allowlist:
        if name in routed or name not in record:
            continue
        wrapped = any_value(record[name])
        if wrapped is TOO_DEEP:
            dropped_deep.append(name)
            continue
        if wrapped is not None:
            attributes.append({"key": name, "value": wrapped})
    return attributes


def encode_records(
    records: Iterable[Mapping[str, Any]],
    profile: Profile,
    service_name: str,
    on_skip=None,
    on_unmapped_severity=None,
    on_dropped_deep=None,
) -> dict[str, Any]:
    """Encode a batch into one OTLP/HTTP JSON logs request body."""
    log_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        dropped_deep: list[str] = []
        try:
            if profile.timestamp_field not in record:
                raise RecordSkipped(f"no {profile.timestamp_field!r} field")
            nanos = to_unix_nanos(record[profile.timestamp_field], profile.timestamp_format)

            entry: dict[str, Any] = {"timeUnixNano": str(nanos)}

            missing_identity = [name for name in profile.identity if record.get(name) is None]
            if missing_identity:
                # AC-0023 says every emitted record carries its identity attributes,
                # and a consumer deduplicates on exactly those. Emitting a record
                # without them produces a row nothing can deduplicate, which is worse
                # than not emitting it -- so this is skipped and reported, the same
                # disposition AC-0066 gives a record with no usable timestamp.
                if on_skip is not None:
                    on_skip(index, f"no value for identity field(s) {missing_identity}")
                continue

            severity = record.get(profile.severity_field)
            # `severity in severity_map` hashes its left operand, so a JSON array or
            # object here raises TypeError and takes the whole run down. Only a
            # string can be a TOML table key, so anything else is simply unmapped.
            mapped = profile.severity_map.get(severity) if isinstance(severity, str) else None
            if mapped is not None:
                entry["severityNumber"] = mapped
                entry["severityText"] = severity
            elif on_unmapped_severity is not None:
                # Not a skip. Severity is enrichment, not identity: of the first
                # consumer's fifteen transition events, five carry no severity
                # value at all, so dropping those records would discard a third
                # of the event vocabulary.
                #
                # Keyed by type AND rendering. The string "7" and the number 7
                # both render as 7, and collapsing them reports one value with a
                # combined count where AC-0068 asks for each distinct value with
                # its own. A rendering is used at all because the key must be
                # hashable, and a list- or object-valued severity is not.
                on_unmapped_severity(
                    severity if severity is None
                    else f"{type(severity).__name__}:{severity!r}"
                )

            attributes = _attributes(record, profile, dropped_deep)
            over_deep_identity = False
            for name in profile.identity:
                wrapped = any_value(record.get(name))
                if wrapped is TOO_DEEP:
                    # `_attributes` handles this for allowlisted fields; the identity
                    # loop is its sibling surface and was missed, so the sentinel was
                    # appended as a value and `json.dumps` raised, ending the run.
                    over_deep_identity = True
                    if on_dropped_deep is not None:
                        on_dropped_deep(name)
                    break
                if wrapped is not None:
                    attributes.append({"key": name, "value": wrapped})
            if over_deep_identity:
                # Same disposition as a missing identity field: a record without its
                # identity is one nothing can deduplicate.
                if on_skip is not None:
                    on_skip(index, "an identity field nests past the depth limit")
                continue
            if attributes:
                entry["attributes"] = attributes
            if dropped_deep and on_dropped_deep is not None:
                for name in dropped_deep:
                    on_dropped_deep(name)
            log_records.append(entry)
        except RecordSkipped as exc:
            if on_skip is not None:
                on_skip(index, str(exc))
            continue
        except Exception as exc:  # noqa: BLE001 - containment floor
            # Deliberately broad, and deliberately around the WHOLE record.
            # The first review round found three instances of an untrusted
            # value reaching a standard-library call that raises -- a digit
            # string past CPython's conversion limit, an integer too large
            # for a double, a structure past the recursion limit -- and each
            # killed the run. A narrower try caught only the timestamp, which
            # is the same partial-surface mistake in miniature. The named
            # repairs remain; this is the floor under the next sibling.
            if on_skip is not None:
                on_skip(index, f"could not be encoded ({type(exc).__name__}: {exc})")
            continue

    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}}
                    ]
                },
                "scopeLogs": [{"scope": {}, "logRecords": log_records}],
            }
        ]
    }
