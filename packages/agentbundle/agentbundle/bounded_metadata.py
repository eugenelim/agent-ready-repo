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
# The Agent Skills specification's own frontmatter field set. Every field is
# optional, including `name`, which the spec defines as a display name that
# defaults to the directory name.
DIRECT_SKILL_TOP_LEVEL_KEYS = frozenset(
    {
        "name",
        "description",
        "when_to_use",
        "argument-hint",
        "arguments",
        "disable-model-invocation",
        "user-invocable",
        "allowed-tools",
        "disallowed-tools",
        "model",
        "effort",
        "context",
        "agent",
        "background",
        "hooks",
        "paths",
        "shell",
        "metadata",
    }
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
    parsed = _parse_frontmatter(
        data, label, active_limits, allowed_top_level_keys=allowed_top_level_keys
    )
    # An unrecognised top-level key is IGNORED, never refused. The spec's field
    # set grows by release and publishers already carry keys it never defined
    # (`requires` appears 832 times across a 2,545-skill corpus). Claude Code
    # tolerates them, so refusing here would reject skills that work. Dropping
    # them keeps them out of anything we project or report.
    parsed = {k: v for k, v in parsed.items() if k in allowed_top_level_keys}
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
    allowed_top_level_keys: frozenset[str] = DIRECT_SKILL_TOP_LEVEL_KEYS,
) -> dict[str, Any]:
    if not data:
        _fail(f"{label}: missing file")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BoundedMetadataError(f"{label}: invalid UTF-8") from exc
    # Line endings are normalised for the PARSE ONLY. `data` is the byte string
    # AC15 says is written to the normalized tree and fed to the digest, and it
    # is untouched here — this rebinds `text`, never `data`.
    #
    # Without this, a `SKILL.md` saved with CRLF — the default of most Windows
    # editors, and common in real repositories — began `---\r\n`, failed the
    # `startswith` below, and was treated as carrying NO frontmatter at all.
    # Nothing refused: the identity comes from the directory name and
    # unrecognised keys are ignored, so the skill installed with its declared
    # `allowed-tools` and `metadata.credentialed` rendered as "undeclared
    # (unrestricted)". The consent surface understated what the publisher
    # actually declared, which is the one thing it exists to state.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
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
    # Unrecognised keys are dropped BEFORE their values are parsed. Filtering
    # after the parse — which is what this did — refuses the whole source when
    # an unrecognised key holds a value the bounded subset cannot represent:
    # `version: 1.0` refused while `version: 2` was dropped, and `version` is
    # the second most common publisher key in the surveyed corpus. RFC-0098 E18
    # says an unrecognised key is ignored regardless of its value type.
    parsed = _parse_subset(
        _strip_unrecognised_keys(raw, allowed_top_level_keys), label, limits
    )
    if _depth(parsed) > limits.max_frontmatter_depth:
        _fail(f"{label}: frontmatter exceeds depth limit")
    if validate_bounds:
        _validate_frontmatter_bounds(parsed, label, limits)
    return parsed


def _strip_unrecognised_keys(raw: str, allowed: frozenset[str]) -> str:
    """Drop every line belonging to an unrecognised top-level key.

    A text pre-pass rather than a parser change, so the bounded subset parser
    stays byte-identical to the catalogue one it was lifted from. A top-level
    key owns its own line plus every indented or blank line that follows it, so
    dropping the block wholesale also drops a nested mapping, a list, or a
    block scalar the direct route would otherwise have to represent.
    """

    kept: list[str] = []
    dropping = False
    for line in raw.splitlines():
        if line[:1] not in {" ", "\t", ""}:
            key = line.split(":", 1)[0].strip()
            dropping = key not in allowed
        if not dropping:
            kept.append(line)
    return "\n".join(kept)


def _parse_subset(raw: str, label: str, limits: MetadataLimits) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current: str | None = None
    nested: str | None = None
    lines = raw.splitlines()
    ends_with_break = raw.endswith("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
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
            if _is_block_scalar_header(value):
                result[current][key], index = _consume_block_scalar(
                    lines, index, 2, value, label, ends_with_break=ends_with_break
                )
                nested = None
                continue
            result[current][key] = _parse_value(value, label, limits)
            nested = key if value == "" else None
            continue
        key, value = _split_key_value(line, label)
        current = key
        nested = None
        if _is_block_scalar_header(value):
            result[key], index = _consume_block_scalar(
                lines, index, 0, value, label, ends_with_break=ends_with_break
            )
            current = None
            continue
        if value == "":
            result[key] = {}
        else:
            result[key] = _parse_value(value, label, limits)
            current = key if isinstance(result[key], (dict, list)) else None
    return result


BLOCK_SCALAR_HEADER = re.compile(r"^([|>])([-+]?)$")


def _is_block_scalar_header(value: str) -> bool:
    """Report whether a value position opens a YAML block scalar.

    ``|`` and ``>`` are YAML indicators, so a plain scalar can never begin with
    either; treating any such value as a block header is unambiguous.
    """

    return value.startswith(("|", ">"))


def _consume_block_scalar(
    lines: list[str],
    start: int,
    key_indent: int,
    header: str,
    label: str,
    *,
    ends_with_break: bool,
) -> tuple[str, int]:
    """Read a block scalar body, returning its value and the next line index.

    Supports the literal (``|``) and folded (``>``) styles with clip, strip
    (``-``), and keep (``+``) chomping.  An explicit indentation indicator is
    refused rather than guessed at, because mis-reading the indent silently
    changes the parsed value.  The body needs no separate budget: the caller
    has already bounded the whole frontmatter block by size.

    Clip and keep chomping only retain a trailing line break that the input
    actually contains, so ``ends_with_break`` reports whether the frontmatter
    slice ended in a newline.  It is false whenever the block is the document's
    last key, which is the common case for a trailing ``description``.
    """

    matched = BLOCK_SCALAR_HEADER.match(header)
    if matched is None:
        _fail(f"{label}: unsupported block scalar header")
    style, chomping = matched.groups()

    body: list[str] = []
    index = start
    block_indent: int | None = None
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            body.append("")
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= key_indent:
            break
        if block_indent is None:
            block_indent = indent
        elif indent < block_indent:
            break
        body.append(line[block_indent:])
        index += 1

    trailing = 0
    while body and not body[-1]:
        body.pop()
        trailing += 1

    if style == "|":
        content = "\n".join(body)
    else:
        content = ""
        for position, entry in enumerate(body):
            if position == 0:
                content = entry
            elif not entry:
                content += "\n"
            elif not body[position - 1]:
                content += entry
            else:
                content += " " + entry

    final_break = ends_with_break or index < len(lines)
    if content and final_break:
        if chomping == "+":
            content += "\n" * (trailing + 1)
        elif chomping != "-":
            content += "\n"
    return content, index


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
