"""Pre-write confidentiality and minimal-intent rendering guards."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit


class NormalizedSourceLike(Protocol):
    """Validated normalized-source fields used at the workspace boundary."""

    mode: str
    locator: str
    revision: str
    tracker_profile: dict[str, str] | None


@dataclass(frozen=True)
class GuardResult:
    """Safe-to-render pre-write decision."""

    allowed: bool
    code: str


@dataclass(frozen=True)
class HandoffReadResult:
    """Bounded repository-content read with a redacted terminal code."""

    allowed: bool
    code: str
    content: bytes | None = None


_CONFIDENTIALITY_RANK = {"public": 0, "internal": 1, "restricted": 2}
_EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_ -]?key|access[_ -]?token|token)"
    r"\s*[:=]\s*\S+"
)
_INSTRUCTION_RE = re.compile(
    r"(?i)\b(ignore (?:all |any )?(?:previous|prior) instructions|"
    r"mark this ready|dispatch this|change the rules|write the raw payload)\b"
)
_ABSOLUTE_LOCAL_RE = re.compile(r"(?i)^(?:/|[a-z]:[/\\]|\\\\)")


def check_destination_confidentiality(
    *,
    constraints: dict[str, object],
    destination_confidentiality: str,
) -> GuardResult:
    """Refuse unknown levels or a less-protective destination before writes."""

    source = constraints.get("confidentiality")
    if destination_confidentiality not in _CONFIDENTIALITY_RANK:
        return GuardResult(False, "invalid_destination_confidentiality")
    if source is None:
        return GuardResult(True, "allowed")
    if not isinstance(source, str) or source not in _CONFIDENTIALITY_RANK:
        return GuardResult(False, "invalid_source_confidentiality")
    if _CONFIDENTIALITY_RANK[source] > _CONFIDENTIALITY_RANK[destination_confidentiality]:
        return GuardResult(False, "confidentiality_mismatch")
    return GuardResult(True, "allowed")


def workspace_source_record(source: NormalizedSourceLike) -> dict[str, object]:
    """Map normalized provenance names to the workspace-entry contract."""

    record: dict[str, object] = {
        "mode": source.mode,
        "ref": _minimize_workspace_source_locator(source.locator),
        "revision": source.revision,
    }
    if source.tracker_profile is not None:
        record["tracker_profile"] = dict(source.tracker_profile)
    return record


def _minimize_workspace_source_locator(locator: str) -> str:
    """Return one non-secret source identity without dereferencing it."""

    if (
        not isinstance(locator, str)
        or not locator
        or any(character in locator for character in ("\x00", "\r", "\n"))
        or _ABSOLUTE_LOCAL_RE.match(locator)
        or "\\" in locator
        or any(part in {".", ".."} for part in locator.split("/"))
        or _EMAIL_RE.search(locator)
        or _SECRET_RE.search(locator)
    ):
        raise ValueError("unsafe_source_locator")
    if "://" not in locator:
        minimized = locator.split("?", 1)[0].split("#", 1)[0].strip()
    else:
        try:
            parsed = urlsplit(locator)
            if parsed.scheme.lower() == "file" or not parsed.hostname:
                raise ValueError
            if parsed.path in {"", "/"} and (parsed.query or parsed.fragment):
                raise ValueError
            host = parsed.hostname
            port = parsed.port
        except (TypeError, ValueError) as error:
            raise ValueError("unsafe_source_locator") from error
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = f"{host}:{port}" if port is not None else host
        minimized = urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path or "/", "", "")
        )
    if not minimized or minimized in {"/", "."}:
        raise ValueError("source_identity_lost")
    return minimized


def read_handoff_repository_content(
    repository_root: Path,
    relative_path: str,
    *,
    max_bytes: int = 1024 * 1024,
) -> HandoffReadResult:
    """Read one repository file through the blessed helper or contract parity."""

    if (
        not isinstance(repository_root, Path)
        or not isinstance(relative_path, str)
        or not relative_path
        or relative_path.startswith("/")
        or re.match(r"^[A-Za-z]:", relative_path)
        or "\\" in relative_path
        or any(part in {"", ".", ".."} for part in relative_path.split("/"))
        or isinstance(max_bytes, bool)
        or not isinstance(max_bytes, int)
        or max_bytes < 0
    ):
        return HandoffReadResult(False, "unsafe_repository_content")
    try:
        resolved_root = repository_root.resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError
        target = resolved_root / relative_path
        _validate_regular_path_chain(resolved_root, relative_path)
    except (OSError, RuntimeError, ValueError):
        return HandoffReadResult(False, "unsafe_repository_content")

    try:
        from agentbundle.catalogue_tooling.file_safety import (
            UnsafeContentError,
            read_confined_regular_file,
        )
    except ImportError:
        try:
            content = _read_confined_regular_file_fallback(
                resolved_root,
                target,
                max_bytes=max_bytes,
            )
        except (OSError, RuntimeError, ValueError):
            return HandoffReadResult(False, "unsafe_repository_content")
    else:
        try:
            content = read_confined_regular_file(
                resolved_root,
                target,
                max_bytes=max_bytes,
            )
        except (UnsafeContentError, OSError, RuntimeError, ValueError):
            return HandoffReadResult(False, "unsafe_repository_content")
    return HandoffReadResult(True, "allowed", content)


def _redact(value: str) -> str:
    """Remove common secret, personal-data, and instruction-shaped content."""

    if _INSTRUCTION_RE.search(value):
        return "[omitted untrusted instruction]"
    value = _EMAIL_RE.sub("[redacted-personal-data]", value)
    return _SECRET_RE.sub(lambda match: f"{match.group(1)}=[redacted]", value)


def _validate_regular_path_chain(root: Path, relative_path: str) -> None:
    """Reject link-like components before opening the final file."""

    current = root
    parts = relative_path.split("/")
    for index, part in enumerate(parts):
        current /= part
        inspected = current.lstat()
        if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
            raise ValueError
        if index < len(parts) - 1 and not stat.S_ISDIR(inspected.st_mode):
            raise ValueError


def _read_confined_regular_file_fallback(
    root: Path,
    path: Path,
    *,
    max_bytes: int,
) -> bytes:
    """Portable parity path for installed skills without agentbundle."""

    relative = path.relative_to(root).as_posix()
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or _is_reparse_point(before)
        or before.st_nlink > 1
    ):
        raise ValueError
    path.resolve(strict=True).relative_to(root)

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    descriptor = os.open(path, flags)
    try:
        after = os.fstat(descriptor)
        if (
            not stat.S_ISREG(after.st_mode)
            or _is_reparse_point(after)
            or after.st_nlink > 1
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            or after.st_size > max_bytes
        ):
            raise ValueError
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            content = handle.read(max_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > max_bytes:
        raise ValueError
    if relative in {"", "."}:
        raise ValueError
    return content


def _is_reparse_point(inspected: os.stat_result) -> bool:
    """Return whether a Windows filesystem entry is link-like."""

    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(inspected, "st_file_attributes", 0) & attribute)
