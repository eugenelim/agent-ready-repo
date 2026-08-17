#!/usr/bin/env python3
"""Fail-closed policy and normalized-envelope checks for Jira intake."""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import re
import socket
import sys
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "intake-profile.json"
NORMALIZED_KEYS = {
    "contract_version",
    "action",
    "content",
    "source",
    "constraints",
    "proposed_authority",
}
CONTENT_KEYS = {"outcomes", "constraints", "evidence", "behaviors", "assumptions", "named_gaps"}
SENSITIVE_MARKERS = ("credential", "secret", "password", "token", "raw_payload", "instruction")
CONSTRAINT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CONSTRAINT_SENSITIVE_PATTERN = re.compile(
    r"(?:^|_)(?:raw|payload|prompt|instruction|credential|credentials|secret|secrets|"
    r"password|passwords|passwd|pwd|(?:api|access|private)?_?(?:token|tokens|key|keys))"
    r"(?:_|$)"
)


class IntakePolicyError(ValueError):
    """A tracker intake boundary refused untrusted input."""


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    """Load one strict, versioned intake profile."""
    profile = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(profile, dict) or set(profile) != {"id", "version", "destination", "budget"}:
        raise IntakePolicyError("invalid intake profile")
    if not profile["id"] or not profile["version"]:
        raise IntakePolicyError("intake profile id and version are required")
    return profile


def validate_destination(
    destination: str,
    profile: dict[str, Any],
    *,
    resolver: Callable[..., Iterable[tuple[Any, ...]]] = socket.getaddrinfo,
) -> str:
    """Validate an HTTPS allowlisted destination and stable public DNS answers."""
    parsed = urlsplit(destination)
    if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
        raise IntakePolicyError("destination must be credential-free https")
    host = (parsed.hostname or "").rstrip(".").lower()
    allowed = {str(value).rstrip(".").lower() for value in profile["destination"]["allowed_hosts"]}
    if not host or host not in allowed:
        raise IntakePolicyError("destination host is not allowed by this profile")
    port = parsed.port or 443
    first = _resolved_addresses(host, port, resolver)
    second = _resolved_addresses(host, port, resolver)
    if not first or first != second:
        raise IntakePolicyError("destination DNS identity changed during validation")
    if any(not address.is_global for address in first):
        raise IntakePolicyError("destination resolves to a non-public address")
    return f"https://{host}" + (f":{port}" if port != 443 else "")


def validate_before_credentials(
    destination: str,
    profile: dict[str, Any],
    load_credentials: Callable[[], Any],
    *,
    resolver: Callable[..., Iterable[tuple[Any, ...]]] = socket.getaddrinfo,
) -> tuple[str, Any]:
    """Make credential loading unreachable until destination policy passes."""
    validated = validate_destination(destination, profile, resolver=resolver)
    return validated, load_credentials()


def normalize_record(record: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Minimize and validate an adapter-produced normalized intake envelope."""
    if not isinstance(record, dict) or set(record) != NORMALIZED_KEYS:
        raise IntakePolicyError("normalized intake has missing or unknown fields")
    if record.get("contract_version") != "normalized-intake.v1":
        raise IntakePolicyError("unsupported normalized intake contract")
    if record.get("action") not in {"start", "remember"}:
        raise IntakePolicyError("unsupported normalized intake action")
    if record.get("proposed_authority") not in {"repo-origin", "tracker-origin"}:
        raise IntakePolicyError("invalid proposed authority")
    content = record.get("content")
    source = record.get("source")
    if not isinstance(content, dict) or set(content) != CONTENT_KEYS:
        raise IntakePolicyError("normalized content has missing or unknown fields")
    for values in content.values():
        if (
            not isinstance(values, list)
            or len(values) > 50
            or any(
                not isinstance(value, str) or not value or len(value) > 2000
                for value in values
            )
        ):
            raise IntakePolicyError("normalized content violates the shared schema")
    if not isinstance(source, dict) or not all(
        source.get(name) for name in ("locator", "revision", "object_type")
    ):
        raise IntakePolicyError("trusted locator, revision, and object type are required")
    if not all(isinstance(source[name], str) for name in ("locator", "revision", "object_type")):
        raise IntakePolicyError("normalized source fields must be strings")
    expected_profile = {"id": profile["id"], "version": profile["version"]}
    if source.get("tracker_profile") != expected_profile:
        raise IntakePolicyError("tracker profile does not match the selected version")
    if set(source) != {"mode", "locator", "revision", "tracker_profile", "object_type"}:
        raise IntakePolicyError("normalized source has missing or unknown fields")
    if source.get("mode") not in {"repo-origin", "tracker-origin"}:
        raise IntakePolicyError("invalid source mode")
    if (
        len(source["locator"]) > 1000
        or any(char in source["locator"] for char in "@?#")
        or len(source["revision"]) > 200
        or len(source["object_type"]) > 120
    ):
        raise IntakePolicyError("normalized source violates the shared schema")
    _validate_constraints(record.get("constraints"))
    _reject_sensitive_keys(record)
    json.dumps(record, ensure_ascii=False, allow_nan=False)
    return json.loads(json.dumps(record, ensure_ascii=False, allow_nan=False))


def _validate_constraints(value: Any) -> None:
    if not isinstance(value, dict) or len(value) > 40:
        raise IntakePolicyError("constraints violate the shared schema")
    for name, item in value.items():
        if not CONSTRAINT_NAME_PATTERN.fullmatch(str(name)) or CONSTRAINT_SENSITIVE_PATTERN.search(
            str(name)
        ):
            raise IntakePolicyError("constraint name violates the shared schema")
        items = item if isinstance(item, list) else [item]
        if len(items) > 20:
            raise IntakePolicyError("constraint array violates the shared schema")
        for scalar in items:
            if isinstance(scalar, (dict, list)) or (
                isinstance(scalar, str) and len(scalar) > 1000
            ) or (
                isinstance(scalar, float) and not math.isfinite(scalar)
            ):
                raise IntakePolicyError("constraint value violates the shared schema")
            if scalar is not None and not isinstance(scalar, (str, int, float, bool)):
                raise IntakePolicyError("constraint value violates the shared schema")


def emit_and_handoff(
    *,
    content: dict[str, Any],
    requested_locator: str,
    acquired: dict[str, Any],
    constraints: dict[str, Any],
    profile: dict[str, Any],
    invoke_work_intake: Callable[[dict[str, Any]], Any],
) -> Any:
    """Build from trusted acquisition metadata and invoke the shared intake seam."""
    _assert_grounded(acquired, content, constraints)
    source = trusted_source(acquired, profile)
    if requested_locator != source["locator"]:
        raise IntakePolicyError("acquired source does not match the requested object")
    record = {
        "contract_version": "normalized-intake.v1",
        "action": "start",
        "content": content,
        "source": source,
        "constraints": constraints,
        "proposed_authority": "tracker-origin",
    }
    return invoke_work_intake(normalize_record(record, profile))


def _assert_grounded(
    acquired: dict[str, Any], content: dict[str, Any], constraints: dict[str, Any]
) -> None:
    """Require every interpreted value to be evidenced by the raw response."""
    raw_strings: list[str] = []
    raw_scalars: set[str | int | float | bool | None] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
        elif isinstance(value, str):
            raw_strings.append(value)
            raw_scalars.add(value)
        elif value is None or isinstance(value, (int, float, bool)):
            raw_scalars.add(value)

    collect(acquired)
    for values in content.values():
        if not isinstance(values, list) or any(
            not isinstance(item, str)
            or not any(item in source_text for source_text in raw_strings)
            for item in values
        ):
            raise IntakePolicyError("normalized content is not grounded in acquisition data")
    for value in constraints.values():
        values = value if isinstance(value, list) else [value]
        if any(
            item not in raw_scalars
            and not (
                isinstance(item, str)
                and any(item in source_text for source_text in raw_strings)
            )
            for item in values
        ):
            raise IntakePolicyError("normalized constraints are not grounded in acquisition data")


def trusted_source(acquired: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Derive provenance only from the trusted Jira response envelope."""
    revision = acquired.get("updated")
    key = acquired.get("key")
    selection = acquired.get("selection")
    if isinstance(key, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*-[1-9][0-9]*", key):
        locator = f"jira://{key}"
        object_type = acquired.get("issueType")
    elif isinstance(selection, str) and re.fullmatch(r"board-[1-9][0-9]*", selection):
        locator = f"jira://boards/{selection.removeprefix('board-')}"
        object_type = "Board"
    else:
        raise IntakePolicyError("trusted Jira response lacks a stable object identity")
    if not isinstance(revision, str) or not revision or not isinstance(object_type, str):
        raise IntakePolicyError("trusted Jira response lacks revision or object type")
    return {
        "mode": "tracker-origin",
        "locator": locator,
        "revision": revision,
        "tracker_profile": {"id": profile["id"], "version": profile["version"]},
        "object_type": object_type,
    }


def budget_result(
    *, pages: int, items: int, response_bytes: int, profile: dict[str, Any]
) -> dict[str, Any]:
    """Return a deterministic complete or explicitly incomplete budget result."""
    budget = profile["budget"]
    exceeded = any((
        pages > budget["max_pages"],
        items > budget["max_items"],
        response_bytes > budget["max_bytes"],
    ))
    return {
        "complete": not exceeded,
        "result": "complete" if not exceeded else budget["exhaustion"],
    }


def _resolved_addresses(
    host: str, port: int, resolver: Callable[..., Iterable[tuple[Any, ...]]]
) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    addresses = set()
    for item in resolver(host, port, type=socket.SOCK_STREAM):
        try:
            addresses.add(ipaddress.ip_address(item[4][0]))
        except (IndexError, TypeError, ValueError) as exc:
            raise IntakePolicyError("resolver returned an invalid address") from exc
    return addresses


def _reject_sensitive_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(marker in normalized for marker in SENSITIVE_MARKERS):
                raise IntakePolicyError("sensitive or instruction-shaped field refused")
            _reject_sensitive_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_sensitive_keys(child)


def _reject_constant(value: str) -> None:
    raise IntakePolicyError(f"non-standard JSON constant: {value}")


def main(argv: list[str] | None = None) -> int:
    """Run the policy checks without accepting credentials or shell input."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    destination = subparsers.add_parser("check-destination")
    destination.add_argument("url")
    record = subparsers.add_parser("validate-record")
    record.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        profile = load_profile()
        if args.command == "check-destination":
            validate_destination(args.url, profile)
            return 0
        candidate = json.loads(
            args.path.read_text(encoding="utf-8"), parse_constant=_reject_constant
        )
        normalized = normalize_record(candidate, profile)
        print(json.dumps(normalized, ensure_ascii=False, allow_nan=False))
        return 0
    except (IntakePolicyError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: intake policy refused input ({type(exc).__name__})\n")


if __name__ == "__main__":
    raise SystemExit(main())
