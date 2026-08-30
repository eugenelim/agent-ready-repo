"""Bounded metadata parsing for already-confined direct-source bytes.

This module deliberately has no filesystem API.  Callers must obtain bytes
through the confined-read primitive before passing them here.
"""

from __future__ import annotations

import json
import math
import re
import tomllib
from dataclasses import dataclass
from typing import Any, NoReturn

JSON_SAFE_INTEGER_MIN = -9007199254740991
JSON_SAFE_INTEGER_MAX = 9007199254740991
DIRECT_SKILL_TOP_LEVEL_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
MAX_PUBLISHER_VALUE_BYTES = 4096


@dataclass(frozen=True)
class MetadataLimits:
    """The metadata limits lifted from catalogue discovery unchanged."""

    max_pack_toml_bytes: int = 1024 * 1024
    max_skill_bytes: int = 2 * 1024 * 1024
    max_frontmatter_bytes: int = 64 * 1024
    max_frontmatter_depth: int = 20
    max_list_items: int = 256
    max_compatibility_keys: int = 256


class BoundedMetadataError(ValueError):
    """Raised when already-read metadata is malformed or exceeds a bound."""


def parse_bounded_toml(
    data: bytes,
    label: str = "pack.toml",
    limits: MetadataLimits | None = None,
) -> dict[str, Any]:
    """Parse bounded TOML bytes without opening a source file."""

    active_limits = limits or MetadataLimits()
    if len(data) > active_limits.max_pack_toml_bytes:
        _fail(f"{label}: exceeds size limit")
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except Exception as exc:
        raise BoundedMetadataError(f"{label}: malformed TOML") from exc
    if not isinstance(parsed, dict):
        _fail(f"{label}: malformed TOML")
    return parsed


def parse_bounded_metadata(
    data: bytes,
    label: str = "SKILL.md",
    limits: MetadataLimits | None = None,
    *,
    allowed_top_level_keys: frozenset[str] = DIRECT_SKILL_TOP_LEVEL_KEYS,
) -> dict[str, Any]:
    """Parse bounded YAML-subset frontmatter from already-confined bytes."""

    active_limits = limits or MetadataLimits()
    parsed = _parse_frontmatter(data, label, active_limits)
    unknown = parsed.keys() - allowed_top_level_keys
    if unknown:
        _fail(f"{label}: unknown top-level frontmatter keys: {sorted(unknown)}")
    for key in ("name", "description"):
        value = parsed.get(key)
        if value is not None:
            validate_publisher_value(value, f"{label}: invalid {key}")
    return parsed


def validate_publisher_value(value: object, label: str) -> str:
    """Return one bounded display value or fail closed before it is rendered."""

    if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_PUBLISHER_VALUE_BYTES:
        _fail(label)
    return value


def _parse_frontmatter(
    data: bytes,
    label: str,
    limits: MetadataLimits,
    *,
    validate_bounds: bool = True,
) -> dict[str, Any]:
    if not data:
        _fail(f"{label}: missing file")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BoundedMetadataError(f"{label}: invalid UTF-8") from exc
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        _fail(f"{label}: frontmatter is not closed")
    raw = text[4:end]
    if len(raw.encode("utf-8")) > limits.max_frontmatter_bytes:
        _fail(f"{label}: frontmatter exceeds size limit")
    if _contains_forbidden_yaml_syntax(raw):
        _fail(f"{label}: YAML tags and aliases are not allowed")
    parsed = _parse_subset(raw, label, limits)
    if _depth(parsed) > limits.max_frontmatter_depth:
        _fail(f"{label}: frontmatter exceeds depth limit")
    if validate_bounds:
        _validate_frontmatter_bounds(parsed, label, limits)
    return parsed


def _parse_subset(raw: str, label: str, limits: MetadataLimits) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current: str | None = None
    nested: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("    - "):
            if current is None or nested is None or not isinstance(result.get(current), dict):
                _fail(f"{label}: unsupported frontmatter shape")
            parent = result[current]
            if parent.get(nested) == {}:
                parent[nested] = []
            if not isinstance(parent.get(nested), list):
                _fail(f"{label}: unsupported frontmatter shape")
            parent[nested].append(_parse_scalar(line[6:].strip(), label))
            continue
        if line.startswith("  - "):
            if current is not None and result.get(current) == {}:
                result[current] = []
            if current is None or not isinstance(result.get(current), list):
                _fail(f"{label}: unsupported frontmatter shape")
            result[current].append(_parse_scalar(line[4:].strip(), label))
            continue
        if line.startswith("  "):
            if current is None or not isinstance(result.get(current), dict):
                _fail(f"{label}: unsupported frontmatter shape")
            key, value = _split_key_value(line.strip(), label)
            result[current][key] = _parse_value(value, label, limits)
            nested = key if value == "" else None
            continue
        key, value = _split_key_value(line, label)
        current = key
        nested = None
        if value == "":
            result[key] = {}
        else:
            result[key] = _parse_value(value, label, limits)
            current = key if isinstance(result[key], (dict, list)) else None
    return result


def _split_key_value(line: str, label: str) -> tuple[str, str]:
    if ":" not in line:
        _fail(f"{label}: malformed frontmatter")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key or len(key) > 1024:
        _fail(f"{label}: invalid frontmatter key")
    return key, value.strip()


def _parse_value(value: str, label: str, limits: MetadataLimits) -> Any:
    if value == "":
        return {}
    if value == "true":
        return True
    if value == "false":
        return False
    if value in {"null", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        _check_json_nesting(
            value,
            limits.max_frontmatter_depth,
            f"{label}: frontmatter exceeds depth limit",
        )
        try:
            parsed = _strict_json_loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            parsed = [
                _parse_scalar(part.strip(), label)
                for part in value[1:-1].split(",")
                if part.strip()
            ]
        except (ValueError, RecursionError, MemoryError, OverflowError) as exc:
            raise BoundedMetadataError(f"{label}: inline list cannot be parsed safely") from exc
        if not isinstance(parsed, list):
            _fail(f"{label}: invalid list")
        return parsed
    return _parse_scalar(value, label)


def _parse_scalar(value: str, label: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError as exc:
            raise BoundedMetadataError(f"{label}: unsupported numeric value") from exc
    if re.fullmatch(r"-?\d+\.\d+", value):
        _fail(f"{label}: unsupported numeric value")
    if "{" in value or "}" in value:
        _fail(f"{label}: unsupported nested value")
    return value


def _validate_frontmatter_bounds(data: dict[str, Any], label: str, limits: MetadataLimits) -> None:
    for key in ("boundaries", "consumers", "providers"):
        value = data.get(key)
        if value is not None:
            _sorted_string_list(value, f"{label}: invalid {key}", limits)
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata.get("boundaries") is not None:
        _sorted_string_list(metadata["boundaries"], f"{label}: invalid boundaries", limits)
    compatibility = data.get("compatibility")
    if compatibility is not None:
        _validate_compatibility(compatibility, label, limits)


def _validate_compatibility(value: Any, label: str, limits: MetadataLimits) -> None:
    if not isinstance(value, dict):
        _fail(f"{label}: compatibility must be an object")
    if len(value) > limits.max_compatibility_keys:
        _fail(f"{label}: compatibility has too many keys")
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 1024:
            _fail(f"{label}: compatibility key is too long")
        _validate_compatibility_value(item, label, limits)


def _validate_compatibility_value(value: Any, label: str, limits: MetadataLimits) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, str):
        if len(value) <= 1024:
            return
        _fail(f"{label}: compatibility string is too long")
    if isinstance(value, int):
        if JSON_SAFE_INTEGER_MIN <= value <= JSON_SAFE_INTEGER_MAX:
            return
        _fail(f"{label}: compatibility integer is out of range")
    if isinstance(value, list):
        if len(value) > limits.max_list_items:
            _fail(f"{label}: compatibility list has too many items")
        for item in value:
            if isinstance(item, (dict, list)):
                _fail(f"{label}: compatibility contains nested values")
            _validate_compatibility_value(item, label, limits)
        return
    _fail(f"{label}: compatibility contains unsupported value")


def _sorted_string_list(value: Any, label: str, limits: MetadataLimits) -> list[str]:
    if not isinstance(value, list) or len(value) > limits.max_list_items:
        _fail(label)
    for item in value:
        if not isinstance(item, str) or len(item) > 1024:
            _fail(label)
    return value


def _check_json_nesting(raw: str, limit: int, diagnostic: str) -> None:
    depth = 0
    quote: str | None = None
    escaped = False
    for char in raw:
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "[{":
            depth += 1
            if depth > limit:
                _fail(diagnostic)
        elif char in "]}":
            depth -= 1


def _strict_json_loads(raw: str) -> Any:
    return json.loads(
        raw,
        parse_constant=_reject_json_constant,
        parse_float=_parse_finite_json_float,
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite JSON number is not allowed: {value}")
    return parsed


def _contains_forbidden_yaml_syntax(raw: str) -> bool:
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            value = stripped[2:].lstrip()
        elif ":" in stripped:
            value = stripped.split(":", 1)[1].lstrip()
        else:
            continue
        if value.startswith(("!", "&", "*")):
            return True
        if value.startswith("[") and re.search(r"(?:^\[|,)\s*[!&*][A-Za-z0-9_-]+", value):
            return True
    return False


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 if not value else 1 + max(_depth(item) for item in value.values())
    if isinstance(value, list):
        return 1 if not value else 1 + max(_depth(item) for item in value)
    return 1


def _fail(diagnostic: str) -> NoReturn:
    # `NoReturn`, not `None`: every caller relies on this to narrow a value
    # after a refusal, and typed as `None` the checker keeps the pre-refusal
    # union alive past the call.
    raise BoundedMetadataError(diagnostic.replace("\n", " "))
