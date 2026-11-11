"""Pre-write guards and the normalized-intake contract validator."""

from __future__ import annotations

import dataclasses
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path


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


# ── Normalized-intake contract ────────────────────────────────────────────────

NORMALIZED_INTAKE_CONTRACT_VERSION = "normalized-intake.v1"
NORMALIZED_INTAKE_ACTIONS = ("start", "remember", "refresh")
SOURCE_MODES = ("repo-origin", "tracker-origin")


_FINDING_NEXT_ACTIONS = {
    "invalid_entry": "Rewrite the entry to the accepted target contract.",
    "invalid_artifact_path": "Replace it with a confined canonical repository-relative path.",
}


@dataclasses.dataclass(frozen=True)
class RoutingFinding:
    """Stable refusal emitted while parsing or evaluating workspace state."""

    code: str
    path: str
    detail: str
    next_action: str
    dispatchable: bool = False


@dataclasses.dataclass(frozen=True)
class SourceRecord:
    """Validated source provenance shared by intake and workspace entries."""

    mode: str
    ref: str | None = None
    revision: str | None = None
    parent: str | None = None
    coordination: str | None = None
    tracker_profile: dict[str, str] | None = None
    locator: str | None = None
    object_type: str | None = None


@dataclasses.dataclass(frozen=True)
class NormalizedIntake:
    """Validated transient intake envelope."""

    contract_version: str
    action: str
    content: dict[str, list[str]]
    source: SourceRecord
    constraints: dict[str, object]
    proposed_authority: str
    refresh_target: str | None = None
    handoff: NormalizedHandoff | None = None


@dataclasses.dataclass(frozen=True)
class HandoffDependency:
    """One closed, bounded dependency carried as upstream content."""

    relationship: str
    locator_kind: str
    locator: str
    semantic_role: str | None = None
    revision: str | None = None


@dataclasses.dataclass(frozen=True)
class NormalizedHandoff:
    """Validated optional shaping context; it has no routing authority."""

    boundaries: list[str]
    non_goals: list[str]
    dependencies: list[HandoffDependency]
    design_context: list[str]
    delivery_questions: list[str]


_CONSTRAINT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SENSITIVE_CONSTRAINT_RE = re.compile(
    r"(?:^|_)(?:raw|payload|prompt|instruction|credential|credentials|secret|secrets|"
    r"password|passwords|passwd|pwd|(?:api|access|private)?_?(?:token|tokens|key|keys))"
    r"(?:_|$)"
)
_SENSITIVE_LOCATOR_RE = re.compile(
    r"(?i)(?:^|[/;:])(?:password|passwd|pwd|secret|api[_-]?key|"
    r"access[_-]?token|token)\s*[:=]\s*\S+"
)
_ABSOLUTE_LOCAL_LOCATOR_RE = re.compile(r"(?i)^(?:/|[a-z]:[/\\]|\\\\)")


def _finding(code: str, path: str = "", detail: str = "") -> RoutingFinding:
    return RoutingFinding(
        code=code,
        path=path,
        detail=detail,
        next_action=_FINDING_NEXT_ACTIONS[code],
    )


def _is_bounded_text(value: object, max_length: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= max_length


def _is_safe_locator(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 1000 and not any(
        marker in value for marker in ("@", "?", "#")
    )


def _is_strict_locator(value: object) -> bool:
    """Reject whitespace and control characters on top of `_is_safe_locator`.

    Workspace source references and external surface locators are consumed as
    identifiers rather than rendered as escaped data, so they carry the tighter
    form the semantic-surface contract requires. Normalized-intake locators stay
    on the looser predicate: they are untrusted source text that the intake
    guard escapes at render time.
    """
    if not _is_safe_locator(value):
        return False
    text = str(value)
    return (
        not _SENSITIVE_LOCATOR_RE.search(text)
        and not _ABSOLUTE_LOCAL_LOCATOR_RE.match(text)
        and "\\" not in text
        and not any(part in {".", ".."} for part in text.split("/"))
        and not any(
        character.isspace() or ord(character) <= 31 or ord(character) == 127
            for character in text
        )
    )


def _is_repository_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 1000:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    if "\\" in value:
        return False
    if any(ord(character) <= 31 or ord(character) == 127 for character in value):
        return False
    parts = value.split("/")
    return not (".." in parts or "." in parts or "" in parts)


def _path_finding_or_invalid(path: object, detail: str) -> RoutingFinding:
    code = "invalid_artifact_path" if not _is_repository_relative_path(path) else "invalid_entry"
    return _finding(code, str(path or ""), detail)


def _validate_tracker_profile(raw: object) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None
    if set(raw) != {"id", "version"}:
        return None
    if not _is_bounded_text(raw.get("id"), 200):
        return None
    if not _is_bounded_text(raw.get("version"), 100):
        return None
    return {"id": raw["id"], "version": raw["version"]}


def _parse_intake_source(raw: object) -> tuple[SourceRecord | None, list[RoutingFinding]]:
    allowed = {"mode", "locator", "revision", "tracker_profile", "object_type"}
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="source must be an object")]
    if not set(raw).issubset(allowed):
        return None, [_finding("invalid_entry", detail="source has unknown fields")]
    mode = raw.get("mode")
    locator = raw.get("locator")
    revision = raw.get("revision")
    if mode not in SOURCE_MODES:
        return None, [_finding("invalid_entry", detail="source.mode is not accepted")]
    if not _is_safe_locator(locator):
        return None, [_finding("invalid_entry", detail="source.locator is not safe")]
    if not _is_bounded_text(revision, 200):
        return None, [_finding("invalid_entry", detail="source.revision is invalid")]
    parsed_profile = None
    if "tracker_profile" in raw:
        parsed_profile = _validate_tracker_profile(raw["tracker_profile"])
        if parsed_profile is None:
            return None, [_finding("invalid_entry", detail="tracker_profile is invalid")]
    object_type = raw.get("object_type")
    if object_type is not None and not _is_bounded_text(object_type, 120):
        return None, [_finding("invalid_entry", detail="object_type is invalid")]
    return SourceRecord(
        mode=mode,
        revision=revision,
        tracker_profile=parsed_profile,
        locator=locator,
        object_type=object_type,
    ), []


def _validate_intake_content(raw: object) -> dict[str, list[str]] | None:
    required = {"outcomes", "constraints", "evidence", "behaviors", "assumptions", "named_gaps"}
    if not isinstance(raw, dict) or set(raw) != required:
        return None
    parsed: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not isinstance(value, list) or len(value) > 50:
            return None
        if not all(_is_bounded_text(item, 2000) for item in value):
            return None
        parsed[key] = list(value)
    return parsed


def _validate_intake_constraints(raw: object) -> dict[str, object] | None:
    if not isinstance(raw, dict) or len(raw) > 40:
        return None
    for key, value in raw.items():
        if not _CONSTRAINT_NAME_RE.fullmatch(key):
            return None
        if _SENSITIVE_CONSTRAINT_RE.search(key):
            return None
        values = value if isinstance(value, list) else [value]
        if isinstance(value, list) and len(value) > 20:
            return None
        for item in values:
            if isinstance(item, str):
                if len(item) > 1000:
                    return None
            elif item is not None:
                if not isinstance(item, (int, float, bool)):
                    return None
                if isinstance(item, float) and not math.isfinite(item):
                    return None
    return dict(raw)


def _validate_handoff(raw: object) -> NormalizedHandoff | None:
    """Validate the additive closed handoff object without interpreting text."""

    required = {
        "boundaries",
        "non_goals",
        "dependencies",
        "design_context",
        "delivery_questions",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        return None
    text_arrays: dict[str, list[str]] = {}
    for key in ("boundaries", "non_goals", "design_context", "delivery_questions"):
        values = raw.get(key)
        if (
            not isinstance(values, list)
            or len(values) > 50
            or not all(_is_bounded_text(value, 2000) for value in values)
        ):
            return None
        text_arrays[key] = list(values)

    raw_dependencies = raw.get("dependencies")
    if not isinstance(raw_dependencies, list) or len(raw_dependencies) > 32:
        return None
    dependencies: list[HandoffDependency] = []
    required_dependency = {"relationship", "locator_kind", "locator"}
    allowed_dependency = required_dependency | {"semantic_role", "revision"}
    for raw_dependency in raw_dependencies:
        if (
            not isinstance(raw_dependency, dict)
            or set(raw_dependency) - allowed_dependency
            or not required_dependency.issubset(raw_dependency)
        ):
            return None
        relationship = raw_dependency.get("relationship")
        locator_kind = raw_dependency.get("locator_kind")
        locator = raw_dependency.get("locator")
        semantic_role = raw_dependency.get("semantic_role")
        revision = raw_dependency.get("revision")
        if relationship not in {"blocks", "informs"}:
            return None
        if locator_kind == "repository-path":
            if not _is_repository_relative_path(locator):
                return None
        elif locator_kind == "external":
            if (
                not _is_strict_locator(locator)
                or re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*:.+", str(locator))
                is None
                or not _is_bounded_text(revision, 300)
                or not _is_strict_locator(revision)
            ):
                return None
        else:
            return None
        if semantic_role is not None and semantic_role not in {
            "delivery-brief",
            "delivery-contract",
        }:
            return None
        if revision is not None and (
            not _is_bounded_text(revision, 300) or not _is_strict_locator(revision)
        ):
            return None
        dependencies.append(
            HandoffDependency(
                relationship=str(relationship),
                locator_kind=str(locator_kind),
                locator=str(locator),
                semantic_role=str(semantic_role) if semantic_role is not None else None,
                revision=str(revision) if revision is not None else None,
            )
        )
    return NormalizedHandoff(
        boundaries=text_arrays["boundaries"],
        non_goals=text_arrays["non_goals"],
        dependencies=dependencies,
        design_context=text_arrays["design_context"],
        delivery_questions=text_arrays["delivery_questions"],
    )


def validate_normalized_intake(
    raw: object,
) -> tuple[NormalizedIntake | None, list[RoutingFinding]]:
    """Validate one normalized-intake envelope through the Group 2 contract."""
    required = {
        "contract_version",
        "action",
        "content",
        "source",
        "constraints",
        "proposed_authority",
    }
    allowed = required | {"refresh_target", "handoff"}
    if not isinstance(raw, dict):
        return None, [_finding("invalid_entry", detail="normalized intake must be an object")]
    if set(raw) - allowed or not required.issubset(raw):
        return None, [_finding("invalid_entry", detail="normalized intake fields are invalid")]
    if raw.get("contract_version") != NORMALIZED_INTAKE_CONTRACT_VERSION:
        return None, [_finding("invalid_entry", detail="contract_version is invalid")]
    action = raw.get("action")
    if action not in NORMALIZED_INTAKE_ACTIONS:
        return None, [_finding("invalid_entry", detail="action is invalid")]
    has_refresh_target = "refresh_target" in raw
    if action == "refresh" and not has_refresh_target:
        return None, [_finding("invalid_entry", detail="refresh requires refresh_target")]
    if action != "refresh" and has_refresh_target:
        return None, [_finding("invalid_entry", detail="only refresh accepts refresh_target")]
    refresh_target = raw.get("refresh_target")
    if has_refresh_target and not _is_repository_relative_path(refresh_target):
        return None, [_path_finding_or_invalid(refresh_target, "refresh_target is unsafe")]
    content = _validate_intake_content(raw.get("content"))
    if content is None:
        return None, [_finding("invalid_entry", detail="content is invalid")]
    source, source_findings = _parse_intake_source(raw.get("source"))
    if source_findings:
        return None, source_findings
    constraints = _validate_intake_constraints(raw.get("constraints"))
    if constraints is None:
        return None, [_finding("invalid_entry", detail="constraints are invalid")]
    authority = raw.get("proposed_authority")
    if authority not in SOURCE_MODES:
        return None, [_finding("invalid_entry", detail="proposed_authority is invalid")]
    handoff = None
    if "handoff" in raw:
        handoff = _validate_handoff(raw.get("handoff"))
        if handoff is None:
            return None, [_finding("invalid_entry", detail="handoff is invalid")]
    return NormalizedIntake(
        contract_version=NORMALIZED_INTAKE_CONTRACT_VERSION,
        action=action,
        content=content,
        source=source,
        constraints=constraints,
        proposed_authority=authority,
        refresh_target=refresh_target,
        handoff=handoff,
    ), []
