#!/usr/bin/env python3
"""Destructive workspace prune implementation with two-sided closure checks."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import tempfile
import tomllib
from pathlib import Path
from types import ModuleType

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.dont_write_bytecode = True


def _load_engine() -> ModuleType:
    """Load or reuse the sibling workspace-status engine by file path."""
    module_name = "workspace_status_engine"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    engine_path = Path(__file__).with_name("workspace_status_engine.py")
    module_spec = importlib.util.spec_from_file_location(module_name, engine_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError("workspace-status engine loader unavailable")
    module = importlib.util.module_from_spec(module_spec)
    registered = sys.modules.setdefault(module_name, module)
    if registered is module:
        module_spec.loader.exec_module(module)
    return registered


_engine = _load_engine()
_confined_artifact_path = _engine._confined_artifact_path
_legacy_canonical_alias = _engine._legacy_canonical_alias
_migration_file_bytes = _engine._migration_file_bytes
_parse_membership_entry = _engine._parse_membership_entry
confine_migration_path = _engine.confine_migration_path
parse_workspace = _engine.parse_workspace
resolve_selected_memberships = _engine.resolve_selected_memberships


def _resolve_prune_closure_memberships(
    workspace: dict, selected_artifact_paths: list[str]
) -> dict[str, list[dict]]:
    """Resolve selected spec occurrences from every container in the document."""
    occurrences_by_path: dict[str, list[dict]] = {
        path: [] for path in selected_artifact_paths
    }

    def visit(value: object, occurrence_path: tuple[str | int, ...]) -> None:
        if isinstance(value, dict):
            initiative = next(
                (
                    part
                    for part in occurrence_path
                    if isinstance(part, str) and part.startswith("ini-")
                ),
                None,
            )
            string_parts = tuple(
                part for part in occurrence_path if isinstance(part, str)
            )
            collection_parts = (
                string_parts[1:] if initiative is not None else string_parts
            )
            collection = ".".join(collection_parts)
            status = value.get("status", "") if initiative is not None else ""
            status = status if isinstance(status, str) else ""
            membership, legacy, _, blocked_path = _parse_membership_entry(
                value,
                collection,
                initiative or "",
                status,
            )
            path: str | None = None
            form = ""
            if (
                membership is not None
                and membership.entry.path in occurrences_by_path
            ):
                path = membership.entry.path
                form = "canonical"
            elif legacy is not None:
                legacy_path = _legacy_canonical_alias(legacy.entry)
                if legacy_path in occurrences_by_path:
                    path = legacy_path
                    form = "legacy"
            if path is None and blocked_path in occurrences_by_path:
                path = blocked_path
                form = "parse-blocked"
            if path is not None:
                entry_index = next(
                    (
                        part
                        for part in reversed(occurrence_path)
                        if isinstance(part, int)
                    ),
                    0,
                )
                occurrence = {
                    "canonical_artifact_path": path,
                    "initiative": initiative,
                    "collection": collection,
                    "entry_index": entry_index,
                    "form": form,
                }
                if sum(isinstance(part, int) for part in occurrence_path) > 1:
                    occurrence["occurrence_path"] = list(occurrence_path)
                occurrences_by_path[path].append(occurrence)
            for raw_name, child in value.items():
                visit(child, (*occurrence_path, str(raw_name)))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, str):
                    initiative = next(
                        (
                            part
                            for part in occurrence_path
                            if isinstance(part, str) and part.startswith("ini-")
                        ),
                        None,
                    )
                    string_parts = tuple(
                        part for part in occurrence_path if isinstance(part, str)
                    )
                    collection_parts = (
                        string_parts[1:]
                        if initiative is not None
                        else string_parts
                    )
                    collection = ".".join(collection_parts)
                    status = ""
                    if initiative is not None:
                        section = workspace.get(initiative)
                        if isinstance(section, dict) and isinstance(
                            section.get("status"), str
                        ):
                            status = section["status"]
                    _, legacy, _, _ = _parse_membership_entry(
                        child,
                        collection,
                        initiative or "",
                        status,
                    )
                    if legacy is not None:
                        path = _legacy_canonical_alias(legacy.entry)
                        if path in occurrences_by_path:
                            occurrence = {
                                "canonical_artifact_path": path,
                                "initiative": initiative,
                                "collection": collection,
                                "entry_index": index,
                                "form": "legacy",
                            }
                            # Same nesting marker the dict branch records. Without it a
                            # nested string's inner index is applied to the outer array,
                            # which would cut an unselected sibling.
                            nested_path = (*occurrence_path, index)
                            if sum(isinstance(part, int) for part in nested_path) > 1:
                                occurrence["occurrence_path"] = list(nested_path)
                            occurrences_by_path[path].append(occurrence)
                visit(child, (*occurrence_path, index))

    visit(workspace, ())
    return occurrences_by_path


PRUNE_PROTECTED_MANIFEST = ".workspace-prune-protected.toml"
_PRUNE_LOCK_FILE = ".workspace-repair.lock"
_PRUNE_SELECTOR_RE = re.compile(r"^docs/specs/[a-z0-9][a-z0-9-]{0,199}$")
_PRUNE_CONFIRMATION_FIELDS = frozenset(
    {"operation_id", "operation_digest", "subject", "role", "confirming_identity"}
)


class UnsafePruneError(RuntimeError):
    """Raised when a selected tree cannot be represented without following it."""


def _prune_error(code: str, **details: object) -> dict:
    """Return one stable, non-echoing prune refusal."""
    return {"error": {"code": code, **details}}


def _fixed_prune_selection(selectors: list[str]) -> tuple[list[str] | None, dict | None]:
    """Validate argument-only selector grammar and copy the ordered selection."""
    if not selectors:
        return None, _prune_error("empty_selection")
    selection = list(selectors)
    if any(
        not isinstance(selector, str)
        or _PRUNE_SELECTOR_RE.fullmatch(selector) is None
        for selector in selection
    ) or len(set(selection)) != len(selection):
        return None, _prune_error("invalid_selector")
    return selection, None


_PRUNE_NOFOLLOW_AVAILABLE = hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")


def _prune_lock_holder(root: Path) -> int | None:
    """Read the pid recorded in the shared lock through a confined, bounded read.

    The lock file is attacker-influenceable: it is created by whoever holds the
    lock and may have been replaced by a symlink. Opening it with O_NOFOLLOW keeps
    the read inside the repository, the link count and regular-file checks reject a
    substituted target, and the byte bound stops an oversized file being loaded to
    report a diagnostic.
    """
    if not _PRUNE_NOFOLLOW_AVAILABLE:
        # Without a real no-follow open there is no safe way to read an
        # attacker-influenceable path, and a diagnostic is never worth that.
        return None
    descriptor: int | None = None
    try:
        descriptor = os.open(
            root / _PRUNE_LOCK_FILE,
            # O_NONBLOCK so a FIFO planted at the lock path cannot block forever
            # waiting for a writer; the regular-file check below then rejects it.
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
        )
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return None
        raw = os.read(descriptor, 32).decode("ascii", "replace").strip()
    except (OSError, ValueError):
        return None
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
    return int(raw) if raw.isdigit() else None


@contextlib.contextmanager
def _prune_lock(root: Path):
    """Hold the shared non-waiting workspace writer lock."""
    lock_path = root / _PRUNE_LOCK_FILE
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        descriptor = -1
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            lock_path.unlink()


def _prune_regular_digest(
    path: Path | str, expected: os.stat_result, *, dir_fd: int | None = None
) -> str:
    """Hash one regular file through a no-follow, identity-checked descriptor."""
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=dir_fd,
    )
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise UnsafePruneError("selected file changed while opening")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 65536):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (
            opened.st_size,
            opened.st_mtime_ns,
            stat.S_IMODE(opened.st_mode),
        ) != (
            after.st_size,
            after.st_mtime_ns,
            stat.S_IMODE(after.st_mode),
        ):
            raise UnsafePruneError("selected file changed while reading")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _prune_manifest_entry(root: Path, path: Path, info: os.stat_result) -> dict:
    """Describe one lstat-observed entry without following a symlink."""
    relative = path.relative_to(root).as_posix()
    mode = stat.S_IMODE(info.st_mode)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if (
        reparse
        and getattr(info, "st_file_attributes", 0) & reparse
        and not stat.S_ISLNK(info.st_mode)
    ):
        raise UnsafePruneError("unsupported reparse point")
    if stat.S_ISLNK(info.st_mode):
        return {
            "path": relative,
            "type": "symlink",
            "mode": mode,
            "sha256": None,
            "target": str(path.readlink()),
        }
    if stat.S_ISDIR(info.st_mode):
        return {
            "path": relative,
            "type": "dir",
            "mode": mode,
            "sha256": None,
            "target": None,
        }
    if stat.S_ISREG(info.st_mode):
        return {
            "path": relative,
            "type": "file",
            "mode": mode,
            "sha256": _prune_regular_digest(path, info),
            "target": None,
        }
    raise UnsafePruneError("unsupported selected-tree entry type")


def prune_tree_manifest(root: Path, selector: str) -> dict | None:
    """Return a complete, sorted, no-follow manifest of one selected tree."""
    try:
        resolved_root = root.resolve(strict=True)
        selected = resolved_root.joinpath(*selector.split("/"))
        selected.parent.resolve(strict=True).relative_to(resolved_root)
        root_info = selected.lstat()
    except FileNotFoundError:
        return None
    except (NotADirectoryError, OSError, RuntimeError, ValueError) as exc:
        raise UnsafePruneError("unsafe selected tree") from exc

    if stat.S_ISLNK(root_info.st_mode):
        return {"entries": [_prune_manifest_entry(resolved_root, selected, root_info)]}
    if not stat.S_ISDIR(root_info.st_mode):
        raise UnsafePruneError("selected artifact is not a directory")

    entries: list[dict] = []
    pending = [selected]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            raise UnsafePruneError("selected directory is unreadable") from exc
        for child in children:
            path = Path(child.path)
            try:
                info = child.stat(follow_symlinks=False)
                entry = _prune_manifest_entry(resolved_root, path, info)
            except OSError as exc:
                raise UnsafePruneError("selected entry is unreadable") from exc
            entries.append(entry)
            if entry["type"] == "dir":
                pending.append(path)
    entries.sort(key=lambda entry: entry["path"])
    return {"entries": entries}


def prune_operation_digest(
    selection: list[str], manifests: dict[str, dict], workspace_sha256: str
) -> str:
    """Bind the selection, complete trees, and workspace baseline canonically."""
    encoded = json.dumps(
        {
            "selection": selection,
            "manifests": manifests,
            "workspace_sha256": workspace_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _prune_operation_id(selection: list[str], operation_digest: str) -> str:
    """Encode the immutable selection and baseline binding into its identity."""
    identity = json.dumps(
        {"selection": selection, "operation_digest": operation_digest},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return "prune-" + identity.hex()


def _decode_prune_operation_id(value: object) -> tuple[list[str], str] | None:
    """Recover and validate immutable operation material from its identity."""
    if not isinstance(value, str) or not value.startswith("prune-"):
        return None
    try:
        raw = bytes.fromhex(value.removeprefix("prune-"))
        if len(raw) > 65536:
            return None
        identity = json.loads(raw.decode("ascii"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(identity, dict) or set(identity) != {
        "selection",
        "operation_digest",
    }:
        return None
    raw_selection = identity.get("selection")
    if not isinstance(raw_selection, list):
        return None
    selection, error = _fixed_prune_selection(raw_selection)
    digest = identity.get("operation_digest")
    if (
        error is not None
        or selection is None
        or not isinstance(digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    ):
        return None
    return selection, digest


def _load_prune_protected(root: Path) -> tuple[set[str] | None, dict | None]:
    """Load the closed protected-selector manifest, treating absence as empty."""
    path = root / PRUNE_PROTECTED_MANIFEST
    try:
        path.lstat()
    except FileNotFoundError:
        return set(), None
    except OSError:
        return None, _prune_error("malformed_toml")
    content = _migration_file_bytes(root, PRUNE_PROTECTED_MANIFEST)
    if content is None:
        return None, _prune_error("malformed_toml")
    try:
        document = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None, _prune_error("malformed_toml")
    protected = document.get("protected") if isinstance(document, dict) else None
    if (
        not isinstance(document, dict)
        or set(document) != {"protected"}
        or not isinstance(protected, list)
        or any(
            not isinstance(selector, str)
            or _PRUNE_SELECTOR_RE.fullmatch(selector) is None
            for selector in protected
        )
    ):
        return None, _prune_error("malformed_toml")
    return set(protected), None


def _parse_prune_workspace(workspace_bytes: bytes) -> tuple[dict | None, dict | None]:
    """Parse one guarded workspace byte snapshot into the shared model."""
    try:
        workspace = tomllib.loads(workspace_bytes.decode("utf-8"))
    except UnicodeDecodeError:
        return None, _prune_error("invalid_workspace")
    except tomllib.TOMLDecodeError:
        return None, _prune_error("malformed_toml")
    if not isinstance(workspace, dict):
        return None, _prune_error("invalid_workspace")
    return workspace, None


def _prune_baseline(
    root: Path, selection: list[str], *, enforce_protection: bool
) -> tuple[dict | None, dict | None]:
    """Capture all repository-backed prune preconditions under the held lock."""
    workspace_bytes = _migration_file_bytes(root, "workspace.toml")
    if workspace_bytes is None:
        return None, _prune_error("invalid_workspace")
    workspace, error = _parse_prune_workspace(workspace_bytes)
    if error is not None or workspace is None:
        return None, error

    protected, error = _load_prune_protected(root)
    if error is not None or protected is None:
        return None, error

    for selector in selection:
        confined = _confined_artifact_path(root, selector)
        if confined is None:
            return None, _prune_error("invalid_selector")
        if enforce_protection and selector in protected:
            return None, _prune_error("protected_target", selector=selector)

    manifests: dict[str, dict] = {}
    artifact_presence: dict[str, bool] = {}
    try:
        for selector in selection:
            manifest = prune_tree_manifest(root, selector)
            artifact_presence[selector] = manifest is not None
            manifests[selector] = manifest if manifest is not None else {"absent": True}
    except UnsafePruneError:
        return None, _prune_error("invalid_selector")

    artifact_paths = [f"{selector}/spec.md" for selector in selection]
    try:
        occurrences = _resolve_prune_closure_memberships(workspace, artifact_paths)
    except ValueError:
        return None, _prune_error("invalid_workspace")
    workspace_sha256 = hashlib.sha256(workspace_bytes).hexdigest()
    digest = prune_operation_digest(selection, manifests, workspace_sha256)
    return {
        "workspace_bytes": workspace_bytes,
        "workspace": workspace,
        "workspace_sha256": workspace_sha256,
        "manifests": manifests,
        "artifact_presence": artifact_presence,
        "occurrences": occurrences,
        "operation_digest": digest,
    }, None


def _prune_targets(selection: list[str], baseline: dict) -> list[dict]:
    """Project baseline state into the public per-target challenge shape."""
    targets: list[dict] = []
    for selector in selection:
        artifact_path = f"{selector}/spec.md"
        all_occurrences = baseline["occurrences"][artifact_path]
        parse_blocked = [
            occurrence
            for occurrence in all_occurrences
            if occurrence["form"] == "parse-blocked"
        ]
        occurrences = [
            occurrence
            for occurrence in all_occurrences
            if occurrence["form"] != "parse-blocked"
        ]
        targets.append(
            {
                "selector": selector,
                "artifact_present": baseline["artifact_presence"][selector],
                "membership_present": bool(all_occurrences),
                "occurrences": occurrences,
                "parse_blocked_occurrences": parse_blocked,
            }
        )
    return targets


def prune_preview(root: Path, selectors: list[str]) -> dict:
    """Return a non-mutating, unsigned challenge for an immutable selection."""
    selection, error = _fixed_prune_selection(selectors)
    if error is not None or selection is None:
        return error or _prune_error("invalid_selector")
    try:
        with _prune_lock(root):
            baseline, error = _prune_baseline(
                root, selection, enforce_protection=False
            )
            if error is not None or baseline is None:
                return error or _prune_error("invalid_workspace")
            digest = baseline["operation_digest"]
            return {
                "operation_id": _prune_operation_id(selection, digest),
                "operation_digest": digest,
                "selection": list(selection),
                "targets": _prune_targets(selection, baseline),
            }
    except FileExistsError:
        return _prune_error("lock_busy")
    except OSError:
        return _prune_error("invalid_workspace")


def _prune_scan_string(data: bytes, start: int) -> int | None:
    """Return the byte after one TOML string without interpreting its content."""
    quote = data[start]
    delimiter = bytes((quote,)) * (3 if data[start : start + 3] == bytes((quote,)) * 3 else 1)
    index = start + len(delimiter)
    while index < len(data):
        if data[index : index + len(delimiter)] == delimiter:
            if len(delimiter) == 1:
                return index + 1
            quote_end = index + len(delimiter)
            while quote_end < len(data) and data[quote_end] == quote:
                quote_end += 1
            return quote_end
        if quote == ord('"') and data[index] == ord("\\"):
            index += 2
        else:
            index += 1
    return None


def _prune_skip_trivia(data: bytes, start: int, end: int) -> int:
    """Skip TOML whitespace and comments within a bounded byte range."""
    index = start
    while index < end:
        if data[index] in b" \t\r\n":
            index += 1
        elif data[index] == ord("#"):
            newline = data.find(b"\n", index, end)
            index = end if newline < 0 else newline + 1
        else:
            break
    return index


def _prune_key_path(raw: bytes) -> tuple[str, ...] | None:
    """Parse one TOML dotted key through the standard-library parser."""
    try:
        parsed = tomllib.loads((raw + b" = 0\n").decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    path: list[str] = []
    value: object = parsed
    while isinstance(value, dict) and len(value) == 1:
        key, value = next(iter(value.items()))
        path.append(str(key))
    return tuple(path) if value == 0 else None


def _prune_header_end(data: bytes, start: int) -> int | None:
    """Return the byte after a single- or double-bracket TOML table header."""
    array_table = data[start : start + 2] == b"[["
    index = start + (2 if array_table else 1)
    while index < len(data):
        if data[index] in (ord('"'), ord("'")):
            string_end = _prune_scan_string(data, index)
            if string_end is None:
                return None
            index = string_end
            continue
        closing = b"]]" if array_table else b"]"
        if data[index : index + len(closing)] == closing:
            return index + len(closing)
        if data[index] in b"\r\n":
            return None
        index += 1
    return None


def _prune_assignment_equals(data: bytes, start: int) -> int | None:
    """Find an assignment delimiter on one logical key line."""
    index = start
    while index < len(data):
        byte = data[index]
        if byte in (ord('"'), ord("'")):
            string_end = _prune_scan_string(data, index)
            if string_end is None:
                return None
            index = string_end
            continue
        if byte == ord("="):
            return index
        if byte in b"#\r\n":
            return None
        index += 1
    return None


def _prune_value_end(data: bytes, start: int) -> int | None:
    """Find the end of one TOML value while tracking nested containers."""
    stack: list[int] = []
    index = start
    pairs = {ord("["): ord("]"), ord("{"): ord("}")}
    while index < len(data):
        byte = data[index]
        if byte in (ord('"'), ord("'")):
            string_end = _prune_scan_string(data, index)
            if string_end is None:
                return None
            index = string_end
            continue
        if byte == ord("#"):
            newline = data.find(b"\n", index)
            if not stack:
                return index
            index = len(data) if newline < 0 else newline + 1
            continue
        if byte in pairs:
            stack.append(pairs[byte])
        elif byte in (ord("]"), ord("}")):
            if not stack or stack.pop() != byte:
                return None
        elif byte in b"\r\n" and not stack:
            return index
        index += 1
    return index if not stack else None


def _prune_container_end(data: bytes, start: int, limit: int) -> int | None:
    """Return the byte after one nested TOML array or inline table."""
    pairs = {ord("["): ord("]"), ord("{"): ord("}")}
    if data[start] not in pairs:
        return None
    stack = [pairs[data[start]]]
    index = start + 1
    while index < limit:
        byte = data[index]
        if byte in (ord('"'), ord("'")):
            string_end = _prune_scan_string(data, index)
            if string_end is None or string_end > limit:
                return None
            index = string_end
            continue
        if byte == ord("#"):
            newline = data.find(b"\n", index, limit)
            index = limit if newline < 0 else newline + 1
            continue
        if byte in pairs:
            stack.append(pairs[byte])
        elif byte in (ord("]"), ord("}")):
            if not stack or stack.pop() != byte:
                return None
            if not stack:
                return index + 1
        index += 1
    return None


def _prune_array_elements(
    data: bytes, array_start: int, array_end: int
) -> tuple[list[tuple[int, int]], list[int | None]] | None:
    """Return exact element spans and following separator offsets for one array."""
    segments: list[tuple[int, int, int | None]] = []
    segment_start = array_start + 1
    stack: list[int] = []
    index = segment_start
    pairs = {ord("["): ord("]"), ord("{"): ord("}")}
    while index < array_end:
        byte = data[index]
        if byte in (ord('"'), ord("'")):
            string_end = _prune_scan_string(data, index)
            if string_end is None or string_end > array_end:
                return None
            index = string_end
            continue
        if byte == ord("#"):
            newline = data.find(b"\n", index, array_end)
            index = array_end if newline < 0 else newline + 1
            continue
        if byte in pairs:
            stack.append(pairs[byte])
        elif byte in (ord("]"), ord("}")):
            if stack:
                if stack.pop() != byte:
                    return None
            elif byte == ord("]") and index == array_end - 1:
                segments.append((segment_start, index, None))
                break
            else:
                return None
        elif byte == ord(",") and not stack:
            segments.append((segment_start, index, index))
            segment_start = index + 1
        index += 1

    elements: list[tuple[int, int]] = []
    separators: list[int | None] = []
    for raw_start, raw_end, separator in segments:
        core_start = _prune_skip_trivia(data, raw_start, raw_end)
        if core_start == raw_end:
            continue
        first = data[core_start]
        if first in (ord("["), ord("{")):
            value_end = _prune_container_end(data, core_start, raw_end)
            if value_end is None or _prune_skip_trivia(data, value_end, raw_end) != raw_end:
                return None
        elif first in (ord('"'), ord("'")):
            value_end = _prune_scan_string(data, core_start)
            if value_end is None or _prune_skip_trivia(data, value_end, raw_end) != raw_end:
                return None
        else:
            value_end = core_start
            while value_end < raw_end and data[value_end] not in b" \t\r\n#":
                value_end += 1
            if _prune_skip_trivia(data, value_end, raw_end) != raw_end:
                return None
        elements.append((core_start, value_end))
        separators.append(separator)
    return elements, separators


def _prune_workspace_array_spans(
    workspace_bytes: bytes,
    wanted: set[tuple[tuple[str, ...], str]],
) -> dict[tuple[tuple[str, ...], str], tuple[int, int]] | None:
    """Locate each requested table array exactly once in the locked bytes."""
    found: dict[tuple[tuple[str, ...], str], list[tuple[int, int]]] = {
        target: [] for target in wanted
    }
    current_table: tuple[str, ...] = ()
    index = 0
    while index < len(workspace_bytes):
        index = _prune_skip_trivia(workspace_bytes, index, len(workspace_bytes))
        if index >= len(workspace_bytes):
            break
        if workspace_bytes[index] == ord("["):
            header_end = _prune_header_end(workspace_bytes, index)
            if header_end is None:
                return None
            array_table = workspace_bytes[index : index + 2] == b"[["
            delimiter_width = 2 if array_table else 1
            inner = workspace_bytes[
                index + delimiter_width : header_end - delimiter_width
            ]
            header_path = _prune_key_path(inner)
            if header_path is None:
                return None
            current_table = header_path
            index = header_end
            continue
        equals = _prune_assignment_equals(workspace_bytes, index)
        if equals is None:
            return None
        key_path = _prune_key_path(workspace_bytes[index:equals].strip())
        value_start = equals + 1
        while value_start < len(workspace_bytes) and workspace_bytes[value_start] in b" \t":
            value_start += 1
        value_end = _prune_value_end(workspace_bytes, value_start)
        if value_end is None:
            return None
        if key_path:
            target = ((*current_table, *key_path[:-1]), key_path[-1])
            if target in found:
                if workspace_bytes[value_start : value_start + 1] != b"[":
                    return None
                array_end = _prune_container_end(
                    workspace_bytes, value_start, value_end
                )
                if array_end is None:
                    return None
                found[target].append((value_start, array_end))
        index = value_end
    if any(len(matches) != 1 for matches in found.values()):
        return None
    return {target: matches[0] for target, matches in found.items()}


def _prune_workspace_without_occurrences(
    workspace_bytes: bytes, workspace: dict, occurrences: list[dict]
) -> bytes | None:
    """Delete only recorded array elements and one separator per element."""
    grouped: dict[tuple[tuple[str, ...], str], set[int]] = {}
    for occurrence in occurrences:
        if occurrence["form"] == "parse-blocked":
            continue
        collection_parts = occurrence["collection"].split(".")
        table = tuple(collection_parts[:-1])
        if occurrence["initiative"] is not None:
            table = (occurrence["initiative"], *table)
        target = (table, collection_parts[-1])
        grouped.setdefault(target, set()).add(occurrence["entry_index"])
    if not grouped:
        return workspace_bytes

    arrays = _prune_workspace_array_spans(workspace_bytes, set(grouped))
    if arrays is None:
        return None
    removals: list[tuple[int, int]] = []
    for target, indices in grouped.items():
        array_start, array_end = arrays[target]
        parsed = _prune_array_elements(workspace_bytes, array_start, array_end)
        if parsed is None:
            return None
        elements, separators = parsed
        cursor: object = workspace
        for part in target[0]:
            cursor = cursor.get(part) if isinstance(cursor, dict) else None
        parsed_entries = cursor.get(target[1]) if isinstance(cursor, dict) else None
        if not isinstance(parsed_entries, list) or len(elements) != len(parsed_entries):
            return None
        for entry_index in indices:
            if not 0 <= entry_index < len(elements):
                return None
            removals.append(elements[entry_index])
            separator = separators[entry_index]
            if separator is None:
                separator = next(
                    (
                        candidate
                        for candidate in reversed(separators[:entry_index])
                        if candidate is not None
                    ),
                    None,
                )
            if separator is not None:
                removals.append((separator, separator + 1))

    result = workspace_bytes
    for start, end in sorted(set(removals), reverse=True):
        result = result[:start] + result[end:]
    try:
        tomllib.loads(result.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    return result


def _write_prune_workspace(root: Path, data: bytes) -> None:
    """Atomically replace workspace.toml without a non-standard dependency."""
    path = confine_migration_path(root, "workspace.toml", require_file=True)
    if path is None:
        raise OSError("unsafe workspace path")
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=".workspace.toml.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(mode)
        temp_path.replace(path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def _prune_manifest_children(
    selector: str, manifest: dict
) -> dict[tuple[str, ...], dict[str, dict]]:
    """Index the closed manifest by parent and reject paths outside its target."""
    selector_parts = tuple(selector.split("/"))
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise UnsafePruneError("selected manifest is invalid")
    children: dict[tuple[str, ...], dict[str, dict]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise UnsafePruneError("selected manifest is invalid")
        parts = tuple(entry["path"].split("/"))
        if parts[: len(selector_parts)] != selector_parts or len(parts) <= len(
            selector_parts
        ):
            raise UnsafePruneError("selected manifest escapes its target")
        parent = parts[:-1]
        siblings = children.setdefault(parent, {})
        if parts[-1] in siblings:
            raise UnsafePruneError("selected manifest contains a duplicate")
        siblings[parts[-1]] = entry
    return children


def _prune_remove_directory_entries(
    directory_fd: int,
    relative_parts: tuple[str, ...],
    children: dict[tuple[str, ...], dict[str, dict]],
    *,
    remove: bool = True,
) -> None:
    """Check, and optionally remove, one manifest-described directory.

    With ``remove=False`` this validates the whole subtree and unlinks nothing, so
    a mismatch deep in the tree is found before anything is deleted. Validating
    per entry during the removal pass as well is deliberate belt-and-braces.
    """
    expected = children.get(relative_parts, {})
    try:
        actual_names = set(os.listdir(directory_fd))
    except OSError as exc:
        raise UnsafePruneError("selected directory is unreadable") from exc
    if actual_names != set(expected):
        raise UnsafePruneError("selected directory differs from its manifest")

    directory_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    for name in sorted(expected):
        entry = expected[name]
        try:
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise UnsafePruneError("selected entry changed before removal") from exc
        entry_type = entry.get("type")
        if stat.S_IMODE(info.st_mode) != entry.get("mode"):
            raise UnsafePruneError("selected entry changed mode before removal")
        if entry_type == "file":
            if not stat.S_ISREG(info.st_mode) or _prune_regular_digest(
                name, info, dir_fd=directory_fd
            ) != entry.get("sha256"):
                raise UnsafePruneError("selected file changed before removal")
        elif entry_type == "symlink":
            try:
                target = os.readlink(name, dir_fd=directory_fd)
            except OSError as exc:
                raise UnsafePruneError("selected symlink changed before removal") from exc
            if not stat.S_ISLNK(info.st_mode) or target != entry.get("target"):
                raise UnsafePruneError("selected symlink changed before removal")
        elif entry_type != "dir" or not stat.S_ISDIR(info.st_mode):
            raise UnsafePruneError("selected entry changed type before removal")
        child_parts = (*relative_parts, name)
        if entry_type == "dir" and stat.S_ISDIR(info.st_mode):
            child_fd = os.open(name, directory_flags, dir_fd=directory_fd)
            try:
                _prune_remove_directory_entries(
                    child_fd, child_parts, children, remove=remove
                )
            finally:
                os.close(child_fd)
            final_info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if (
                not stat.S_ISDIR(final_info.st_mode)
                or (remove and stat.S_IMODE(final_info.st_mode) != entry.get("mode"))
            ):
                raise UnsafePruneError("selected directory changed before removal")
            if remove:
                os.rmdir(name, dir_fd=directory_fd)
        elif (
            entry_type == "file" and stat.S_ISREG(info.st_mode)
        ) or (
            entry_type == "symlink" and stat.S_ISLNK(info.st_mode)
        ):
            if remove:
                os.unlink(name, dir_fd=directory_fd)
        else:
            raise UnsafePruneError("selected entry changed type before removal")


def _validate_prune_tree(root: Path, selector: str, manifest: dict) -> None:
    """Validate a whole selected tree against its manifest without removing."""
    _walk_prune_tree(root, selector, manifest, remove=False)


def _remove_prune_tree(root: Path, selector: str, manifest: dict) -> None:
    """Remove only recorded entries through no-follow directory descriptors."""
    _walk_prune_tree(root, selector, manifest, remove=True)


def _walk_prune_tree(
    root: Path, selector: str, manifest: dict, *, remove: bool
) -> None:
    """Shared confined descent used by both the check and the removal pass."""
    if manifest.get("absent") is True:
        return
    resolved_root = root.resolve(strict=True)
    parts = tuple(selector.split("/"))
    directory_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    descriptors = [os.open(resolved_root, directory_flags)]
    try:
        for part in parts[:-1]:
            descriptors.append(
                os.open(part, directory_flags, dir_fd=descriptors[-1])
            )
        parent_fd = descriptors[-1]
        selected_name = parts[-1]
        selected_info = os.stat(
            selected_name, dir_fd=parent_fd, follow_symlinks=False
        )
        if stat.S_ISLNK(selected_info.st_mode):
            entries = manifest.get("entries")
            if (
                not isinstance(entries, list)
                or len(entries) != 1
                or entries[0].get("path") != selector
                or entries[0].get("type") != "symlink"
                or stat.S_IMODE(selected_info.st_mode) != entries[0].get("mode")
                or os.readlink(selected_name, dir_fd=parent_fd) != entries[0].get("target")
            ):
                raise UnsafePruneError("selected symlink differs from its manifest")
            if remove:
                os.unlink(selected_name, dir_fd=parent_fd)
            return
        if not stat.S_ISDIR(selected_info.st_mode):
            raise UnsafePruneError("selected artifact changed type before removal")
        children = _prune_manifest_children(selector, manifest)
        selected_fd = os.open(selected_name, directory_flags, dir_fd=parent_fd)
        descriptors.append(selected_fd)
        _prune_remove_directory_entries(
            selected_fd, parts, children, remove=remove
        )
        if remove:
            os.rmdir(selected_name, dir_fd=parent_fd)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _prune_artifact_absent(root: Path, selector: str) -> bool:
    """Require lexical nonexistence below real, non-link repository parents."""
    try:
        resolved_root = root.resolve(strict=True)
        cursor = resolved_root
        parts = selector.split("/")
        for part in parts[:-1]:
            cursor /= part
            try:
                info = cursor.lstat()
            except FileNotFoundError:
                return True
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if stat.S_ISLNK(info.st_mode) or (
                reparse and getattr(info, "st_file_attributes", 0) & reparse
            ):
                return False
            if not stat.S_ISDIR(info.st_mode):
                return False
        selected = cursor / parts[-1]
        selected.lstat()
        return False
    except FileNotFoundError:
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _prune_closure(root: Path, selection: list[str], workspace_bytes: bytes) -> dict:
    """Observe both closure halves from disk state held under the shared lock."""
    workspace, error = _parse_prune_workspace(workspace_bytes)
    if error is not None or workspace is None:
        return _prune_error("closure_failed", workspace_unreadable=True)
    artifact_paths = [f"{selector}/spec.md" for selector in selection]
    occurrences = _resolve_prune_closure_memberships(workspace, artifact_paths)

    observations: list[dict] = []
    for selector, artifact_path in zip(selection, artifact_paths, strict=True):
        artifact_absent = _prune_artifact_absent(root, selector)
        survivors = occurrences[artifact_path]
        observations.append(
            {
                "selector": selector,
                "artifact_absent": artifact_absent,
                "membership_absent": not survivors,
                "occurrences": survivors,
            }
        )
    artifact_absent = all(item["artifact_absent"] for item in observations)
    membership_absent = all(item["membership_absent"] for item in observations)
    closure = {
        "artifact_absent": artifact_absent,
        "membership_absent": membership_absent,
        "targets": observations,
    }
    if artifact_absent and membership_absent:
        return {"closure": closure}
    failure = next(
        item
        for item in observations
        if not item["artifact_absent"] or not item["membership_absent"]
    )
    return _prune_error(
        "closure_failed",
        selector=failure["selector"],
        artifact_survives=not failure["artifact_absent"],
        membership_survives=not failure["membership_absent"],
        occurrences=failure["occurrences"],
    )


def _validate_prune_confirmation(
    confirmation: dict, current_digest: str, fixed_selection: list[str]
) -> tuple[list[str] | None, dict | None]:
    """Validate authorization shape, identity binding, and baseline freshness."""
    if not confirmation:
        return None, _prune_error("confirmation_missing")
    if not isinstance(confirmation, dict) or set(confirmation) != _PRUNE_CONFIRMATION_FIELDS:
        return None, _prune_error("confirmation_invalid")
    if any(
        not isinstance(confirmation[field], str)
        or not confirmation[field]
        or len(confirmation[field]) > 65536
        or "\n" in confirmation[field]
        or "\r" in confirmation[field]
        for field in _PRUNE_CONFIRMATION_FIELDS
    ):
        return None, _prune_error("confirmation_invalid")
    decoded = _decode_prune_operation_id(confirmation["operation_id"])
    if decoded is None:
        return None, _prune_error("confirmation_binding_mismatch")
    selection, expected_digest = decoded
    if selection != fixed_selection:
        return None, _prune_error("confirmation_binding_mismatch")
    if confirmation["operation_digest"] != expected_digest:
        return None, _prune_error("confirmation_stale")
    if current_digest != expected_digest:
        return None, _prune_error("baseline_stale")
    return selection, None


def _load_prune_confirmation(root: Path, relative_path: str) -> dict | None:
    """Read one confined confirmation file after the prune lock is held."""
    raw = _migration_file_bytes(root, relative_path)
    if raw is None:
        return None
    try:
        confirmation = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return confirmation if isinstance(confirmation, dict) else None


def prune_execute(
    root: Path,
    selectors: list[str],
    confirmation: dict | None,
    failure_point: str | None = None,
    *,
    confirmation_file: str | None = None,
) -> dict:
    """Remove one confirmed selection and prove two-sided closure under its lock."""
    caller_selection, error = _fixed_prune_selection(selectors)
    if error is not None or caller_selection is None:
        return error or _prune_error("invalid_selector")
    # Tracks how far a mutating run got. An interrupted prune leaves a half-state by
    # design, so a failure must say which phase completed or it cannot be reconciled.
    phase = {"name": "selection_fixed"}
    try:
        with _prune_lock(root):
            if confirmation_file is not None:
                confirmation = _load_prune_confirmation(root, confirmation_file)
                if confirmation is None:
                    return _prune_error("confirmation_invalid")
            elif confirmation is None:
                confirmation = {}
            selection = caller_selection
            decoded_confirmation = (
                _decode_prune_operation_id(confirmation.get("operation_id"))
                if isinstance(confirmation, dict)
                else None
            )
            if (
                decoded_confirmation is not None
                and decoded_confirmation[0] != selection
            ):
                return _prune_error("confirmation_binding_mismatch")
            baseline, error = _prune_baseline(
                root, selection, enforce_protection=True
            )
            if error is not None or baseline is None:
                return error or _prune_error("invalid_workspace")
            for selector in selection:
                if not baseline["artifact_presence"][selector]:
                    return _prune_error("nothing_to_remove", selector=selector)

            validated_selection, error = _validate_prune_confirmation(
                confirmation, baseline["operation_digest"], selection
            )
            if error is not None or validated_selection is None:
                return error or _prune_error("confirmation_invalid")
            if failure_point in {"after_baseline", "before_closure"}:
                return _prune_error(
                    "closure_failed",
                    observation_unavailable=True,
                    selection=list(caller_selection),
                    last_completed_phase=phase["name"],
                )

            all_occurrences = [
                occurrence
                for selector in selection
                for occurrence in baseline["occurrences"][f"{selector}/spec.md"]
            ]
            # A doubly-nested lifecycle list records an inner index that the byte-span
            # editor would apply to the outer array, cutting a sibling nobody selected.
            # Refuse rather than risk removing unselected register state.
            if any(
                occurrence.get("occurrence_path") is not None
                for occurrence in all_occurrences
            ):
                return _prune_error("invalid_workspace", nested_occurrence=True)
            edited_workspace = _prune_workspace_without_occurrences(
                baseline["workspace_bytes"], baseline["workspace"], all_occurrences
            )
            if edited_workspace is None:
                return _prune_error("invalid_workspace")

            phase["name"] = "baseline_confirmed"
            if not _PRUNE_NOFOLLOW_AVAILABLE:
                # Removal confinement rests on no-follow descriptor descent. Without
                # it the two-sided guarantee cannot be honoured, so the operation
                # declines instead of deleting with weaker protection. This is its
                # own refusal rather than a closure failure: nothing was attempted
                # and nothing about the repository is wrong.
                return _prune_error(
                    "unsupported_platform",
                    selection=list(caller_selection),
                    last_completed_phase=phase["name"],
                )
            try:
                # Validate every selected tree in full before the first unlink, so a
                # mismatch deep in one tree cannot be discovered after an earlier
                # entry has already been deleted on what becomes a refusal path.
                for selector in selection:
                    _validate_prune_tree(
                        root, selector, baseline["manifests"][selector]
                    )
                for selector in selection:
                    _remove_prune_tree(root, selector, baseline["manifests"][selector])
            except UnsafePruneError:
                return _prune_error("baseline_stale")
            phase["name"] = "artifacts_removed"

            if failure_point != "after_artifact_removal" and (
                edited_workspace != baseline["workspace_bytes"]
                and failure_point != "membership_write_noop"
            ):
                _write_prune_workspace(root, edited_workspace)
                phase["name"] = "memberships_removed"

            post_bytes = _migration_file_bytes(root, "workspace.toml")
            if post_bytes is None:
                return _prune_error(
                    "closure_failed",
                    workspace_unreadable=True,
                    selection=list(caller_selection),
                    last_completed_phase=phase["name"],
                )
            closure = _prune_closure(root, selection, post_bytes)
            if failure_point == "after_membership_removal" and "error" not in closure:
                return _prune_error(
                    "closure_failed",
                    observation_unavailable=True,
                    selection=list(caller_selection),
                    last_completed_phase=phase["name"],
                )
            return closure
    except FileExistsError:
        # A busy lock is indistinguishable from a stale one without the holder, so
        # report it. The name is repository-relative; no absolute root is emitted.
        return _prune_error(
            "lock_busy",
            lock_file=_PRUNE_LOCK_FILE,
            holder_pid=_prune_lock_holder(root),
        )
    except (OSError, RuntimeError, ValueError):
        # An operator recovering from this needs to know which target was in flight
        # and how far it got; without both, a half-state cannot be reconciled safely.
        return _prune_error(
            "closure_failed",
            observation_unavailable=True,
            selection=list(caller_selection),
            last_completed_phase=phase["name"],
        )
