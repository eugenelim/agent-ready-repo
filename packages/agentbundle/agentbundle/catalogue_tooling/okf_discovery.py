"""Pure metadata extraction for OKF-backed catalogue packs."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from agentbundle.catalogue_tooling import file_safety

SUPPORTED_PROFILE = "agentbundle-okf/v1"
SUPPORTED_OKF_VERSION = "0.2"
JSON_SAFE_INTEGER_MIN = -9007199254740991
JSON_SAFE_INTEGER_MAX = 9007199254740991
GENERATED_MARKER = "generated-by: compile-okf agentbundle-okf/v1"
GENERATED_FRONTMATTER = "compile-okf agentbundle-okf/v1"
WINDOWS_DEVICE = re.compile(
    r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", re.IGNORECASE
)


@dataclass(frozen=True)
class DiscoveryLimits:
    max_pack_toml_bytes: int = 1024 * 1024
    max_manifest_bytes: int = 8 * 1024 * 1024
    max_skill_dirs: int = 4096
    max_agent_dirs: int = 4096
    max_integrations: int = 128
    max_bundles: int = 128
    max_skill_bytes: int = 2 * 1024 * 1024
    max_frontmatter_bytes: int = 64 * 1024
    max_frontmatter_depth: int = 20
    max_list_items: int = 256
    max_compatibility_keys: int = 256
    max_concepts: int = 2000
    max_okf_files: int = 4096
    max_okf_bytes: int = 32 * 1024 * 1024


@dataclass(frozen=True)
class DiscoveryRecord:
    pack_metadata: dict[str, Any]
    skill_metadata: list[dict[str, Any]]
    knowledge: list[dict[str, Any]]


class DiscoveryError(ValueError):
    """A fail-closed discovery error with one safe relative diagnostic."""

    def __init__(self, diagnostic: str):
        super().__init__(diagnostic)
        self.diagnostic = diagnostic


def discover_pack(
    pack_dir: Path,
    *,
    limits: DiscoveryLimits | None = None,
) -> DiscoveryRecord:
    """Return closed show-compatible metadata for one catalogue pack."""

    active_limits = limits or DiscoveryLimits()
    pack_dir = pack_dir.resolve(strict=False)
    pack_toml = pack_dir / "pack.toml"
    pack_data = _load_pack_toml(pack_dir, pack_toml, active_limits)
    pack_table = _expect_object(pack_data.get("pack"), "pack.toml: [pack] missing")
    return DiscoveryRecord(
        pack_metadata=_pack_metadata(pack_table, active_limits),
        skill_metadata=_skill_metadata(pack_dir, active_limits),
        knowledge=_knowledge_metadata(pack_dir, pack_table, active_limits),
    )


def _load_pack_toml(
    pack_dir: Path,
    pack_toml: Path,
    limits: DiscoveryLimits,
) -> dict[str, Any]:
    data = _read_file(
        pack_dir,
        pack_toml,
        max_bytes=limits.max_pack_toml_bytes,
    )
    if len(data) > limits.max_pack_toml_bytes:
        _fail("pack.toml: exceeds size limit")
    try:
        return tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise DiscoveryError("pack.toml: malformed TOML") from exc


def _pack_metadata(pack_table: dict[str, Any], limits: DiscoveryLimits) -> dict[str, Any]:
    categories = _sorted_string_list(
        pack_table.get("categories", []), "pack.toml: invalid categories", limits
    )
    keywords = _sorted_string_list(
        pack_table.get("keywords", []), "pack.toml: invalid keywords", limits
    )
    license_value = pack_table.get("license")
    if license_value is not None and not isinstance(license_value, str):
        _fail("pack.toml: invalid license")
    return {"categories": categories, "keywords": keywords, "license": license_value}


def _skill_metadata(pack_dir: Path, limits: DiscoveryLimits) -> list[dict[str, Any]]:
    skills_root = pack_dir / ".apm" / "skills"
    try:
        skills_root.lstat()
    except FileNotFoundError:
        return []
    try:
        skill_dirs = sorted(
            file_safety.list_confined_directories(pack_dir, skills_root),
            key=lambda path: _sort_key(path.name),
        )
    except file_safety.UnsafeContentError as exc:
        raise DiscoveryError(str(exc)) from exc
    if len(skill_dirs) > limits.max_skill_dirs:
        _fail(".apm/skills: too many Skill directories")
    _reject_collisions([path.relative_to(pack_dir).as_posix() for path in skill_dirs])
    manifest = _load_manifest(pack_dir, limits)
    return [
        _one_skill(pack_dir, skill_dir, manifest, limits)
        for skill_dir in skill_dirs
    ]


def _one_skill(
    pack_dir: Path,
    skill_dir: Path,
    manifest: dict[str, Any] | None,
    limits: DiscoveryLimits,
) -> dict[str, Any]:
    rel = skill_dir.relative_to(pack_dir).as_posix()
    if not _is_safe_relative_path(rel):
        _fail(f"{rel}: unsafe Skill path")
    _scan_regular_files(pack_dir, skill_dir, max_bytes=limits.max_skill_bytes)
    skill_md = skill_dir / "SKILL.md"
    data = _read_file(pack_dir, skill_md, max_bytes=limits.max_skill_bytes)
    if len(data) > limits.max_skill_bytes:
        _fail(f"{_rel(pack_dir, skill_md)}: exceeds size limit")
    frontmatter = _parse_frontmatter(data, _rel(pack_dir, skill_md), limits)
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description:
        _fail(f"{_rel(pack_dir, skill_md)}: missing description")
    license_value = frontmatter.get("license")
    if license_value is not None and not isinstance(license_value, str):
        _fail(f"{_rel(pack_dir, skill_md)}: invalid license")
    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        _validate_compatibility(compatibility, _rel(pack_dir, skill_md), limits)
    metadata = frontmatter.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        _fail(f"{_rel(pack_dir, skill_md)}: invalid metadata")
    boundaries = _sorted_string_list(
        metadata.get("boundaries", []),
        f"{_rel(pack_dir, skill_md)}: invalid boundaries",
        limits,
    )
    generated_by = metadata.get("generated-by")
    if generated_by is None:
        generated_from = profile = digest = None
    else:
        generated_from, profile, digest = _generated_identity(
            pack_dir, skill_md, metadata, manifest, limits
        )
    return {
        "name": skill_dir.name,
        "description": description,
        "license": license_value,
        "compatibility": compatibility,
        "generated_from": generated_from,
        "profile": profile,
        "digest": digest,
        "boundaries": boundaries,
    }


def _generated_identity(
    pack_dir: Path,
    skill_md: Path,
    metadata: dict[str, Any],
    manifest: dict[str, Any] | None,
    limits: DiscoveryLimits,
) -> tuple[str, str, str]:
    rel = _rel(pack_dir, skill_md)
    if manifest is None:
        _fail(f"{rel}: generated Skill requires .okf-generated.json")
    generated_by = metadata.get("generated-by")
    source_path = metadata.get("source-path")
    source_digest = metadata.get("source-digest")
    if (
        generated_by != GENERATED_FRONTMATTER
        or not isinstance(source_path, str)
        or not isinstance(source_digest, str)
        or not _is_sha256(source_digest)
        or not _is_safe_relative_path(source_path)
    ):
        _fail(f"{rel}: incomplete generated Skill markers")
    records = _manifest_records(manifest)
    record = records.get(rel)
    if record is None:
        _fail(f"{rel}: generated Skill missing from manifest")
    if record.get("kind") == "okf-procedure-skill":
        if not isinstance(metadata.get("reviewed-projection-digest"), str):
            _fail(f"{rel}: procedure Skill missing reviewed projection digest")
    elif metadata.get("reviewed-projection-digest") is not None:
        _fail(f"{rel}: router Skill must omit reviewed projection digest")
    digest = _bytes_digest(
        _read_file(pack_dir, skill_md, max_bytes=limits.max_skill_bytes)
    )
    expected = {
        "digest": digest,
        "marker": GENERATED_MARKER,
        "source_digest": source_digest,
        "source_path": source_path,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            _fail(f"{rel}: manifest disagrees with generated Skill markers")
    if record.get("kind") not in {"okf-router", "okf-procedure-skill"}:
        _fail(f"{rel}: unsupported generated Skill kind")
    return source_path, SUPPORTED_PROFILE, source_digest


def _knowledge_metadata(
    pack_dir: Path,
    pack_table: dict[str, Any],
    limits: DiscoveryLimits,
) -> list[dict[str, Any]]:
    metadata = pack_table.get("metadata")
    if metadata is None:
        return []
    metadata = _expect_object(metadata, "pack.toml: invalid metadata")
    okf = metadata.get("okf")
    if okf is None:
        return []
    okf = _expect_object(okf, "pack.toml: invalid OKF metadata")
    if okf.get("profile") != SUPPORTED_PROFILE:
        _fail("pack.toml: unsupported OKF profile")
    bundles = okf.get("bundles", [])
    if not isinstance(bundles, list):
        _fail("pack.toml: invalid OKF bundles")
    if len(bundles) > limits.max_bundles:
        _fail("pack.toml: too many OKF bundles")
    seen_ids: set[str] = set()
    records = []
    for bundle in bundles:
        if not isinstance(bundle, dict):
            _fail("pack.toml: invalid OKF bundle")
        records.append(_one_bundle(pack_dir, bundle, seen_ids, limits))
    return sorted(records, key=lambda item: _sort_key(item["id"]))


def _one_bundle(
    pack_dir: Path,
    bundle: dict[str, Any],
    seen_ids: set[str],
    limits: DiscoveryLimits,
) -> dict[str, Any]:
    bundle_id = bundle.get("id")
    path = bundle.get("path")
    router_skill = bundle.get("router-skill")
    if not isinstance(bundle_id, str) or not bundle_id:
        _fail("pack.toml: invalid OKF bundle id")
    key = unicodedata.normalize("NFC", bundle_id).casefold()
    if key in seen_ids:
        _fail("pack.toml: duplicate OKF bundle id")
    seen_ids.add(key)
    if not isinstance(path, str) or not _is_okf_directory(path):
        _fail("pack.toml: unsafe OKF bundle path")
    _reject_declared_path_collision(pack_dir, path)
    if not isinstance(router_skill, str) or not router_skill:
        _fail("pack.toml: invalid OKF router skill")
    bundle_root = pack_dir / path
    try:
        file_safety.validate_confined_directory(pack_dir, bundle_root)
    except file_safety.UnsafeContentError as exc:
        try:
            bundle_root.lstat()
        except FileNotFoundError:
            _fail(f"{path}: OKF bundle root is missing")
        raise DiscoveryError(str(exc)) from exc
    if not bundle_root.is_dir():
        _fail(f"{path}: OKF bundle root is missing")
    files = _bundle_files(pack_dir, bundle_root, limits)
    _reject_collisions([str(PurePosixPath(path) / rel) for rel in files])
    index_meta = _parse_frontmatter(
        files.get("index.md", b""),
        f"{path}/index.md",
        limits,
    )
    if index_meta.get("okf_version") != SUPPORTED_OKF_VERSION:
        _fail(f"{path}/index.md: unsupported OKF version")
    content_license = index_meta.get("license")
    if not isinstance(content_license, str) or not content_license:
        _fail(f"{path}/index.md: missing content license")
    concept_count = _concept_count(files, path, limits)
    digest = _tree_digest(files)
    _check_router_manifest(pack_dir, router_skill, path, digest, limits)
    return {
        "id": bundle_id,
        "format": "okf",
        "okf_version": SUPPORTED_OKF_VERSION,
        "router_skill": router_skill,
        "content_license": content_license,
        "concept_count": concept_count,
        "digest": digest,
    }


def _bundle_files(
    pack_dir: Path,
    bundle_root: Path,
    limits: DiscoveryLimits,
) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total = 0
    try:
        paths = file_safety.list_confined_regular_files(pack_dir, bundle_root)
    except file_safety.UnsafeContentError as exc:
        raise DiscoveryError(str(exc)) from exc
    for path in sorted(paths, key=lambda item: item.as_posix()):
        rel = path.relative_to(bundle_root).as_posix()
        if not _is_safe_relative_path(rel):
            _fail(f"{rel}: unsafe OKF path")
        remaining = limits.max_okf_bytes - total
        data = _read_file(pack_dir, path, max_bytes=remaining)
        files[rel] = data
        total += len(data)
        if len(files) > limits.max_okf_files:
            _fail(f"{_rel(pack_dir, bundle_root)}: too many OKF files")
        if total > limits.max_okf_bytes:
            _fail(f"{_rel(pack_dir, bundle_root)}: OKF bundle exceeds size limit")
    if "index.md" not in files:
        _fail(f"{_rel(pack_dir, bundle_root)}/index.md: missing root index")
    return files


def _concept_count(files: dict[str, bytes], path: str, limits: DiscoveryLimits) -> int:
    count = 0
    for rel, data in files.items():
        if not rel.startswith("concepts/") or not rel.endswith(".md"):
            continue
        if rel.endswith("/index.md") or rel == "concepts/index.md":
            continue
        meta = _parse_frontmatter(
            data,
            f"{path}/{rel}",
            limits,
            validate_bounds=False,
        )
        if meta.get("status") not in {None, "Active", "Deprecated"}:
            _fail(f"{path}/{rel}: unsupported concept status")
        count += 1
        if count > limits.max_concepts:
            _fail(f"{path}: too many OKF concepts")
    return count


def _check_router_manifest(
    pack_dir: Path,
    router_skill: str,
    source_path: str,
    source_digest: str,
    limits: DiscoveryLimits,
) -> None:
    manifest = _load_manifest(pack_dir, limits)
    if manifest is None:
        _fail(".okf-generated.json: missing generated manifest")
    output = f".apm/skills/{router_skill}/SKILL.md"
    record = _manifest_records(manifest).get(output)
    if record is None or record.get("kind") != "okf-router":
        _fail(f"{output}: router missing from generated manifest")
    if record.get("source_path") != source_path or record.get("source_digest") != source_digest:
        _fail(f"{output}: manifest disagrees with OKF source digest")
    try:
        router = _one_skill(
            pack_dir,
            pack_dir / ".apm" / "skills" / router_skill,
            manifest,
            limits,
        )
    except DiscoveryError as exc:
        raise DiscoveryError(
            f"{output}: generated router is invalid ({exc.diagnostic})"
        ) from exc
    if router["generated_from"] != source_path or router["digest"] != source_digest:
        _fail(f"{output}: generated router identity disagrees with OKF bundle")


def _load_manifest(pack_dir: Path, limits: DiscoveryLimits) -> dict[str, Any] | None:
    manifest = pack_dir / ".okf-generated.json"
    try:
        manifest.lstat()
    except FileNotFoundError:
        return None
    data = _read_file(pack_dir, manifest, max_bytes=limits.max_manifest_bytes)
    if len(data) > limits.max_manifest_bytes:
        _fail(".okf-generated.json: exceeds size limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DiscoveryError(".okf-generated.json: malformed JSON") from exc
    _check_json_nesting(
        text,
        limits.max_frontmatter_depth,
        ".okf-generated.json: exceeds depth limit",
    )
    try:
        parsed = _strict_json_loads(text)
    except json.JSONDecodeError as exc:
        raise DiscoveryError(".okf-generated.json: malformed JSON") from exc
    except (ValueError, RecursionError, MemoryError, OverflowError) as exc:
        raise DiscoveryError(".okf-generated.json: cannot be parsed safely") from exc
    if not isinstance(parsed, dict) or parsed.get("profile") != SUPPORTED_PROFILE:
        _fail(".okf-generated.json: unsupported profile")
    if not isinstance(parsed.get("managed"), list):
        _fail(".okf-generated.json: invalid managed records")
    return parsed


def _manifest_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for item in manifest["managed"]:
        if not isinstance(item, dict) or not isinstance(item.get("output_path"), str):
            _fail(".okf-generated.json: invalid managed record")
        output = item["output_path"]
        if not _is_safe_relative_path(output):
            _fail(".okf-generated.json: unsafe output path")
        if output in records:
            _fail(".okf-generated.json: duplicate output path")
        records[output] = item
    return records


def _parse_frontmatter(
    data: bytes,
    label: str,
    limits: DiscoveryLimits,
    *,
    validate_bounds: bool = True,
) -> dict[str, Any]:
    if not data:
        _fail(f"{label}: missing file")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DiscoveryError(f"{label}: invalid UTF-8") from exc
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
    parsed = parse_frontmatter_subset(raw, label, limits)
    if _depth(parsed) > limits.max_frontmatter_depth:
        _fail(f"{label}: frontmatter exceeds depth limit")
    if validate_bounds:
        _validate_frontmatter_bounds(parsed, label, limits)
    return parsed


def parse_frontmatter_subset(
    raw: str,
    label: str,
    limits: DiscoveryLimits,
) -> dict[str, Any]:
    """Parse the constrained YAML frontmatter subset shared with linting."""
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


def _parse_value(value: str, label: str, limits: DiscoveryLimits) -> Any:
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
            raise DiscoveryError(f"{label}: inline list cannot be parsed safely") from exc
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
            raise DiscoveryError(f"{label}: unsupported numeric value") from exc
    if re.fullmatch(r"-?\d+\.\d+", value):
        _fail(f"{label}: unsupported numeric value")
    if "{" in value or "}" in value:
        _fail(f"{label}: unsupported nested value")
    return value


def _validate_frontmatter_bounds(
    data: dict[str, Any],
    label: str,
    limits: DiscoveryLimits,
) -> None:
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


def _validate_compatibility(value: Any, label: str, limits: DiscoveryLimits) -> None:
    if not isinstance(value, dict):
        _fail(f"{label}: compatibility must be an object")
    if len(value) > limits.max_compatibility_keys:
        _fail(f"{label}: compatibility has too many keys")
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 1024:
            _fail(f"{label}: compatibility key is too long")
        _validate_compatibility_value(item, label, limits)


def _validate_compatibility_value(
    value: Any,
    label: str,
    limits: DiscoveryLimits,
) -> None:
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


def _sorted_string_list(value: Any, label: str, limits: DiscoveryLimits) -> list[str]:
    if not isinstance(value, list):
        _fail(label)
    if len(value) > limits.max_list_items:
        _fail(label)
    items: dict[str, str] = {}
    for item in value:
        if not isinstance(item, str) or len(item) > 1024:
            _fail(label)
        normalized = unicodedata.normalize("NFC", item)
        key = normalized.casefold()
        if key not in items:
            items[key] = normalized
    return sorted(items.values(), key=_sort_key)


def _reject_collisions(paths: list[str]) -> None:
    seen_normalized: dict[str, str] = {}
    seen_casefolded: dict[str, str] = {}
    for path in paths:
        normalized = unicodedata.normalize("NFC", path)
        normalized_key = normalized
        case_key = normalized.casefold()
        if normalized_key in seen_normalized and seen_normalized[normalized_key] != path:
            _fail(f"{path}: normalized path collision")
        if case_key in seen_casefolded and seen_casefolded[case_key] != path:
            _fail(f"{path}: case-folded path collision")
        seen_normalized[normalized_key] = path
        seen_casefolded[case_key] = path


def _reject_declared_path_collision(pack_dir: Path, path: str) -> None:
    current = pack_dir
    declared_parts = path.split("/")
    for index, part in enumerate(declared_parts):
        try:
            file_safety.validate_confined_directory(pack_dir, current)
        except file_safety.UnsafeContentError as exc:
            raise DiscoveryError(str(exc)) from exc
        matches = [
            existing.name
            for existing in current.iterdir()
            if unicodedata.normalize("NFC", existing.name).casefold()
            == unicodedata.normalize("NFC", part).casefold()
        ]
        if not matches:
            return
        exact = next((name for name in matches if name == part), None)
        if exact is None:
            _fail(f"{path}: case-folded path collision")
        current /= exact
        if index < len(declared_parts) - 1:
            try:
                file_safety.validate_confined_directory(pack_dir, current)
            except file_safety.UnsafeContentError as exc:
                raise DiscoveryError(str(exc)) from exc


def _scan_regular_files(pack_dir: Path, root: Path, *, max_bytes: int) -> None:
    try:
        paths = file_safety.list_confined_regular_files(pack_dir, root)
    except file_safety.UnsafeContentError as exc:
        raise DiscoveryError(str(exc)) from exc
    for path in paths:
        _read_file(pack_dir, path, max_bytes=max_bytes)


def _is_safe_relative_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "//" in path or path.endswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", path):
        return False
    for part in path.split("/"):
        if (
            part in {"", ".", ".."}
            or any(ord(char) < 32 or ord(char) == 127 for char in part)
            or any(char in '<>:"|?*' for char in part)
            or part.endswith((" ", "."))
            or WINDOWS_DEVICE.match(part)
        ):
            return False
    return True


def _is_okf_directory(path: str) -> bool:
    return 5 <= len(path) <= 1000 and path.startswith("okf/") and _is_safe_relative_path(path)


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
        if value.startswith("[") and re.search(
            r"(?:^\[|,)\s*[!&*][A-Za-z0-9_-]+", value
        ):
            return True
    return False


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        if not value:
            return 1
        return 1 + max(_depth(item) for item in value.values())
    if isinstance(value, list):
        if not value:
            return 1
        return 1 + max(_depth(item) for item in value)
    return 1


def _tree_digest(files: dict[str, bytes]) -> str:
    payload = [
        {"path": path, "sha256": _bytes_digest(data)}
        for path, data in sorted(files.items(), key=lambda item: _sort_key(item[0]))
    ]
    return _bytes_digest(_canonical_json_bytes(payload))


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _bytes_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def _sort_key(value: str) -> bytes:
    return unicodedata.normalize("NFC", value).encode("utf-8")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _read_file(root: Path, path: Path, *, max_bytes: int) -> bytes:
    try:
        return file_safety.read_confined_regular_file(
            root,
            path,
            max_bytes=max_bytes,
        )
    except file_safety.UnsafeContentError as exc:
        raise DiscoveryError(str(exc)) from exc


def _expect_object(value: Any, diagnostic: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(diagnostic)
    return value


def _fail(diagnostic: str) -> None:
    safe = diagnostic.replace("\n", " ")
    raise DiscoveryError(safe)
