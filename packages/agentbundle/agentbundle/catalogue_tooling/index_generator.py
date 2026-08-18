"""Generate the deterministic, adapter-neutral catalogue index."""

from __future__ import annotations

import hashlib
import json
import stat
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from agentbundle.build.validate import validate
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
    sha256_confined_regular_file,
)
from agentbundle.catalogue_tooling.journey_validator import parse_journey_md


class CatalogueIndexError(ValueError):
    """A confined catalogue input cannot produce a valid index."""

    def __init__(self, code: str, message: str, location: str = ".") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.location = location


_GENERATED_DIRECTORIES = {
    ".claude-code",
    ".cursor",
    ".kiro",
    ".copilot",
    ".codex",
    ".agentbundle",
    ".installed",
    "dist",
}
_CACHE_DIRECTORIES = {".cache", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
_TEMP_SUFFIXES = (".pyc", ".pyd", ".pyo", ".tmp", ".swp", "~")
_INTEGRATION_KINDS = {"augment", "handoff", "input", "review"}


def _is_link_or_reparse(path: Path) -> bool:
    try:
        path_stat = path.lstat()
    except OSError:
        return True
    if stat.S_ISLNK(path_stat.st_mode):
        return True
    if hasattr(path, "is_junction") and path.is_junction():
        return True
    attributes = getattr(path_stat, "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & flag)


def _root(root: Path) -> Path:
    supplied = root.absolute()
    try:
        resolved = root.resolve(strict=True)
        root_stat = root.lstat()
    except (OSError, RuntimeError) as exc:
        raise CatalogueIndexError("catalogue-root", "catalogue root is not readable") from exc
    if supplied != resolved or _is_link_or_reparse(root) or not stat.S_ISDIR(root_stat.st_mode):
        raise CatalogueIndexError("catalogue-root", "catalogue root is not a safe directory")
    return resolved


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return "."


def _read_toml(root: Path, path: Path) -> dict[str, Any]:
    location = _relative(root, path)
    try:
        text = read_confined_regular_file(root, path).decode("utf-8")
        value = tomllib.loads(text)
    except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError, OSError) as exc:
        raise CatalogueIndexError("invalid-toml", "cannot read valid TOML", location) from exc
    if not isinstance(value, dict):
        raise CatalogueIndexError("invalid-toml", "TOML root must be an object", location)
    return value


def _bundled_toml(name: str) -> dict[str, Any]:
    try:
        content = resources.files("agentbundle._data").joinpath(name).read_text(encoding="utf-8")
        return tomllib.loads(content)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise CatalogueIndexError("bundled-contract", f"bundled {name} is unavailable") from exc


def _bundled_schema() -> dict[str, Any]:
    try:
        content = resources.files("agentbundle._data").joinpath(
            "catalogue-index.schema.json"
        ).read_text(encoding="utf-8")
        value = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogueIndexError(
            "bundled-contract", "bundled index schema is unavailable"
        ) from exc
    if not isinstance(value, dict):
        raise CatalogueIndexError("bundled-contract", "bundled index schema is invalid")
    return value


def _directory_entries(root: Path, directory: Path) -> list[Path]:
    location = _relative(root, directory)
    try:
        directory_stat = directory.lstat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise CatalogueIndexError(
            "unsafe-path", "source directory cannot be inspected", location
        ) from exc
    if (
        stat.S_ISLNK(directory_stat.st_mode)
        or not stat.S_ISDIR(directory_stat.st_mode)
        or _is_link_or_reparse(directory)
    ):
        raise CatalogueIndexError(
            "unsafe-path",
            "source directory is not a safe directory",
            location,
        )
    try:
        resolved = directory.resolve(strict=True)
        resolved.relative_to(root)
        return sorted(directory.iterdir(), key=lambda path: path.name)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CatalogueIndexError(
            "unsafe-path", "source directory is not confined", location
        ) from exc


def _excluded(relative: Path) -> bool:
    parts = relative.parts
    if any(part in _CACHE_DIRECTORIES for part in parts):
        return True
    if parts and parts[0] in _GENERATED_DIRECTORIES:
        return True
    name = relative.name
    if name == ".DS_Store" or ".upstream." in name:
        return True
    return name.endswith(_TEMP_SUFFIXES)


def _walk_files(root: Path, directory: Path) -> list[Path]:
    files: list[Path] = []

    def visit(current: Path) -> None:
        for entry in _directory_entries(root, current):
            relative = entry.relative_to(directory)
            if _excluded(relative) or _is_link_or_reparse(entry):
                continue
            try:
                entry_stat = entry.lstat()
            except OSError as exc:
                raise CatalogueIndexError(
                    "unsafe-path", "source entry cannot be inspected", _relative(root, entry)
                ) from exc
            if stat.S_ISDIR(entry_stat.st_mode):
                visit(entry)
            elif stat.S_ISREG(entry_stat.st_mode):
                files.append(entry)

    visit(directory)
    return sorted(files, key=lambda path: path.relative_to(directory).as_posix())


def _entry_names(
    root: Path,
    directory: Path,
    *,
    directories_only: bool = False,
    keep_file_suffix: bool = False,
) -> list[str]:
    names: list[str] = []
    for entry in _directory_entries(root, directory):
        if _excluded(Path(entry.name)) or _is_link_or_reparse(entry):
            continue
        try:
            entry_stat = entry.lstat()
        except OSError:
            continue
        if directories_only and not stat.S_ISDIR(entry_stat.st_mode):
            continue
        if not (stat.S_ISDIR(entry_stat.st_mode) or stat.S_ISREG(entry_stat.st_mode)):
            continue
        names.append(
            entry.name
            if stat.S_ISDIR(entry_stat.st_mode) or keep_file_suffix
            else entry.stem
        )
    return sorted(names)


def _content(root: Path, pack_root: Path) -> tuple[dict[str, list[str]], list[str]]:
    apm = pack_root / ".apm"
    content: dict[str, list[str]] = {}
    for public_name, source_name, directories_only, keep_file_suffix in (
        ("skills", "skills", True, False),
        ("agents", "agents", False, False),
        ("commands", "commands", False, False),
        ("hooks", "hooks", False, False),
        ("shared-libs", "shared-libs", False, True),
        ("user-libs", "user-libs", False, True),
    ):
        values = _entry_names(
            root,
            apm / source_name,
            directories_only=directories_only,
            keep_file_suffix=keep_file_suffix,
        )
        if values:
            content[public_name] = values

    scripts_root = apm / "skills"
    scripts: list[str] = []
    for skill_root in _directory_entries(root, scripts_root):
        if _is_link_or_reparse(skill_root):
            continue
        try:
            is_skill_directory = stat.S_ISDIR(skill_root.lstat().st_mode)
        except OSError as exc:
            raise CatalogueIndexError(
                "unsafe-path",
                "skill directory cannot be inspected",
                _relative(root, skill_root),
            ) from exc
        if not is_skill_directory:
            continue
        scripts.extend(
            path.relative_to(pack_root).as_posix()
            for path in _walk_files(root, skill_root / "scripts")
        )
    if scripts:
        content["scripts"] = sorted(scripts)

    seeds = _entry_names(root, pack_root / "seeds", keep_file_suffix=True)
    if seeds:
        content["seeds"] = seeds

    execution: set[str] = set()
    for source_name in ("hook-wiring", "kiro-ide-hooks"):
        source = apm / source_name
        for entry in _directory_entries(root, source):
            if not _is_link_or_reparse(entry) and not _excluded(Path(entry.name)):
                execution.add(entry.name)
    for entry in _directory_entries(root, apm / "adapter-root-bins"):
        if (
            entry.name.startswith((".", "_"))
            or entry.suffix != ".py"
            or _is_link_or_reparse(entry)
            or _excluded(Path(entry.name))
        ):
            continue
        try:
            if stat.S_ISREG(entry.lstat().st_mode):
                execution.add(entry.name)
        except OSError:
            continue
    return content, sorted(execution)


def _digest(root: Path, pack_root: Path) -> str:
    digest_input = bytearray()
    for path in _walk_files(root, pack_root):
        relative = path.relative_to(pack_root).as_posix()
        try:
            file_digest = sha256_confined_regular_file(root, path)
        except (UnsafeContentError, OSError) as exc:
            raise CatalogueIndexError(
                "unreadable-pack", "pack source file cannot be hashed", _relative(root, path)
            ) from exc
        digest_input.extend(f"{relative}:{file_digest}\n".encode())
    return hashlib.sha256(digest_input).hexdigest()


def _integration(value: object, location: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise CatalogueIndexError("invalid-integration", "integration must be an object", location)
    fields = ("id", "pack", "kind", "role")
    if any(not isinstance(value.get(field), str) for field in fields):
        raise CatalogueIndexError(
            "invalid-integration", "integration requires string id, pack, kind, and role", location
        )
    if value["kind"] not in _INTEGRATION_KINDS:
        raise CatalogueIndexError(
            "invalid-integration",
            f"integration kind must be one of {sorted(_INTEGRATION_KINDS)}",
            location,
        )
    return {field: value[field] for field in fields}


def _pack_entry(
    root: Path,
    pack_root: Path,
    adapter_names: list[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest_path = pack_root / "pack.toml"
    manifest = _read_toml(root, manifest_path)
    pack = manifest.get("pack")
    location = _relative(root, manifest_path)
    if not isinstance(pack, dict):
        raise CatalogueIndexError("invalid-pack", "pack.toml requires a [pack] object", location)
    name = pack.get("name")
    version = pack.get("version")
    if not isinstance(name, str) or not isinstance(version, str):
        raise CatalogueIndexError(
            "invalid-pack", "pack requires string name and version", location
        )
    if name != pack_root.name:
        raise CatalogueIndexError("invalid-pack", "pack name must match its directory", location)

    adapter_contract = pack.get("adapter-contract")
    contract_version = (
        adapter_contract.get("version") if isinstance(adapter_contract, dict) else None
    )
    install = pack.get("install")
    install = install if isinstance(install, dict) else {}
    scope = "repo"
    adapters = adapter_names
    if contract_version not in (None, "0.1"):
        candidate_scope = install.get("default-scope", "repo")
        if candidate_scope not in ("repo", "user"):
            raise CatalogueIndexError("invalid-pack", "invalid default scope", location)
        scope = candidate_scope
        allowed = install.get("allowed-adapters")
        if allowed is not None:
            if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
                raise CatalogueIndexError(
                    "invalid-pack", "allowed-adapters must be strings", location
                )
            unknown = sorted(set(allowed) - set(adapter_names))
            if unknown:
                raise CatalogueIndexError(
                    "invalid-pack",
                    "allowed-adapters contains an unknown adapter",
                    location,
                )
            adapters = sorted(allowed)

    journey_path = pack_root / "JOURNEY.md"
    journey_location = _relative(root, journey_path)
    journey, diagnostics = parse_journey_md(root, journey_path)
    if diagnostics:
        prefix = f"{journey_location}: "
        message = diagnostics[0]
        if message.startswith(prefix):
            message = message[len(prefix):]
        raise CatalogueIndexError("invalid-journey", message, journey_location)
    if journey is not None and journey["pack"] != name:
        raise CatalogueIndexError(
            "invalid-journey",
            "journey pack must match pack.toml name",
            journey_location,
        )

    integrations_value = pack.get("integrations", [])
    if not isinstance(integrations_value, list):
        raise CatalogueIndexError(
            "invalid-integration", "pack integrations must be an array", location
        )
    integrations = [_integration(value, location) for value in integrations_value]

    content, execution = _content(root, pack_root)
    entry: dict[str, Any] = {
        "name": name,
        "version": version,
        "scope": scope,
        "adapters": adapters,
        "integrations": integrations,
        "integrations_inverse": [],
        "journeys": [],
        "effects": [],
        "digest": _digest(root, pack_root),
    }
    for key in ("description", "categories"):
        if key in pack:
            entry[key] = pack[key]
    if content:
        entry["content"] = content
    if execution:
        entry["execution"] = execution
    if journey is not None:
        summary_keys = (
            "journey_id",
            "pack",
            "start_state",
            "end_state",
            "scope",
            "tagline",
            "contract",
        )
        entry["journeys"] = [{key: journey[key] for key in summary_keys}]
        entry["effects"] = journey.get("effects", [])
        if isinstance(journey.get("docsUrl"), str):
            entry["documentation"] = journey["docsUrl"]
    return entry, integrations


def _profiles(root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in _directory_entries(root, root / "profiles"):
        if path.suffix != ".toml" or _is_link_or_reparse(path):
            continue
        profile = _read_toml(root, path)
        scope = profile.get("scope")
        if scope not in ("repo", "user"):
            raise CatalogueIndexError(
                "invalid-profile",
                "profile scope must be repo or user",
                _relative(root, path),
            )
        entry: dict[str, Any] = {"name": path.stem, "scope": scope}
        if isinstance(profile.get("description"), str):
            entry["description"] = profile["description"]
        packs = profile.get("packs")
        if packs is not None:
            if not isinstance(packs, list) or not all(
                isinstance(item, dict) and isinstance(item.get("pack"), str) for item in packs
            ):
                raise CatalogueIndexError(
                    "invalid-profile", "profile packs are invalid", _relative(root, path)
                )
            entry["packs"] = [item["pack"] for item in packs]
        result.append(entry)
    return sorted(result, key=lambda item: item["name"])


def generate_index(catalogue_root: Path, generated_at: str | None = None) -> dict[str, Any]:
    """Build and validate an index without performing any public write."""
    root = _root(catalogue_root)
    catalogue_document = _read_toml(root, root / "catalogue.toml")
    catalogue = catalogue_document.get("catalogue")
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("name"), str):
        raise CatalogueIndexError(
            "invalid-catalogue", "catalogue.toml requires [catalogue].name", "catalogue.toml"
        )
    catalogue_entry = {"name": catalogue["name"]}
    if isinstance(catalogue.get("description"), str):
        catalogue_entry["description"] = catalogue["description"]

    adapter_document = _bundled_toml("adapter.toml")
    adapters = adapter_document.get("adapter")
    if not isinstance(adapters, dict):
        raise CatalogueIndexError("bundled-contract", "bundled adapter contract is invalid")
    adapter_names = sorted(adapters)

    pack_entries: list[dict[str, Any]] = []
    seen_journeys: set[str] = set()
    for pack_root in _directory_entries(root, root / "packs"):
        if pack_root.name.startswith("_"):
            continue
        try:
            pack_stat = pack_root.lstat()
            is_junction = hasattr(pack_root, "is_junction") and pack_root.is_junction()
        except OSError as exc:
            raise CatalogueIndexError(
                "unreadable-pack",
                "pack entry cannot be inspected",
                _relative(root, pack_root),
            ) from exc
        attributes = getattr(pack_stat, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if (
            stat.S_ISLNK(pack_stat.st_mode)
            or is_junction
            or bool(attributes & reparse_flag)
        ):
            continue
        if not stat.S_ISDIR(pack_stat.st_mode):
            continue
        manifest_path = pack_root / "pack.toml"
        try:
            manifest_stat = manifest_path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise CatalogueIndexError(
                "unreadable-pack",
                "pack manifest cannot be inspected",
                _relative(root, manifest_path),
            ) from exc
        if not stat.S_ISREG(manifest_stat.st_mode):
            raise CatalogueIndexError(
                "invalid-pack",
                "pack manifest must be a regular file",
                _relative(root, manifest_path),
            )
        entry, _integrations = _pack_entry(root, pack_root, adapter_names)
        for journey in entry["journeys"]:
            journey_id = journey["journey_id"]
            if journey_id in seen_journeys:
                raise CatalogueIndexError(
                    "duplicate-journey", "journey_id must be unique", pack_root.name
                )
            seen_journeys.add(journey_id)
        pack_entries.append(entry)
    pack_entries.sort(key=lambda item: item["name"])

    by_name = {entry["name"]: entry for entry in pack_entries}
    for source in pack_entries:
        for integration in source["integrations"]:
            target = by_name.get(integration["pack"])
            if target is None:
                continue
            target["integrations_inverse"].append(
                {**integration, "pack": source["name"]}
            )
    for entry in pack_entries:
        entry["integrations"] = sorted(
            entry["integrations"], key=lambda item: (item["pack"], item["id"])
        )
        entry["integrations_inverse"] = sorted(
            entry["integrations_inverse"], key=lambda item: (item["pack"], item["id"])
        )

    index: dict[str, Any] = {
        "schema_version": "1",
        "catalogue": catalogue_entry,
        "packs": pack_entries,
        "profiles": _profiles(root),
    }
    if generated_at is not None:
        index["generated_at"] = generated_at
    errors = validate(index, _bundled_schema())
    if errors:
        raise CatalogueIndexError("schema-validation", errors[0], "catalogue-index.json")
    return index
