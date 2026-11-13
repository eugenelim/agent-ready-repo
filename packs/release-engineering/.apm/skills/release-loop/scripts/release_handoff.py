#!/usr/bin/env python3
"""Validate release candidates using a bounded YAML subset and local evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

MANIFEST_LIMIT = 1_048_576
EVIDENCE_LIMIT = 536_870_912
IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
DIGEST = r"^sha256:[0-9a-f]{64}$"
ENUMS = {"status": ("pass", "fail", "not-run", "not-applicable")}
RECORDS: dict[str, dict[str, str]] = {
    "Subject": {"id": "id", "sha256": "digest"},
    "Evidence": {
        "id": "id",
        "kind": "string",
        "locator": "string",
        "sha256": "digest",
        "media_type": "string",
        "producer": "string",
        "observed_at": "time",
        "subjects": "Subject[]",
    },
    "Source": {"repository": "string", "revision?": "revision", "snapshot?": "id"},
    "Check": {
        "id": "id",
        "stage": "string",
        "status": "status",
        "subjects": "Subject[]",
        "evidence": "id[]",
        "reason?": "string",
        "policy_basis?": "string",
    },
    "Target": {"environment": "string", "account": "string"},
    "Component": {
        "id": "id",
        "kind": "string",
        "image_ref?": "string",
        "artifact?": "id",
        "plan_bundle?": "id",
    },
    "ImageComponent": {"id": "id", "kind": "image-kind", "image_ref": "string", "artifact": "id"},
    "PlanComponent": {"id": "id", "kind": "plan-kind", "plan_bundle": "id"},
    "Entry": {"id": "id", "summary": "string"},
    "Changes": {"baseline": "string", "entries": "Entry[]"},
    "Phase": {"id": "id", "depends_on": "id[]", "components": "id[]", "procedures": "id[]"},
    "RepairOwner": {"id": "id", "route?": "string"},
    "Candidate": {
        "schema_version": "version",
        "candidate_id": "id",
        "created_at": "time",
        "producer": "string",
        "sources": "Source[]",
        "target": "Target",
        "components": "Component[]",
        "evidence": "Evidence[]",
        "provenance": "id[]",
        "checks": "Check[]",
        "changes": "Changes",
        "phases": "Phase[]",
        "repair_owner": "RepairOwner",
    },
    "PolicyCheck": {
        "id": "id",
        "stage": "string",
        "component_kind": "string",
        "allowed_not_applicable_reasons": "string[]",
    },
    "Policy": {
        "id": "id",
        "max_age_seconds": "positive",
        "required_checks": "PolicyCheck[]",
        "approved_procedures": "Subject[]",
    },
}
NONEMPTY = {
    ("Evidence", "subjects"),
    ("Check", "subjects"),
    ("Candidate", "sources"),
    ("Candidate", "phases"),
    ("Phase", "components"),
    ("Phase", "procedures"),
}
ENUMS.update({"image-kind": ("oci-image",), "plan-kind": ("terraform-plan",)})


class Refusal(Exception):
    """Carry only a fixed diagnostic code and its result class."""

    def __init__(self, code: str, status: str = "invalid") -> None:
        super().__init__(code)
        self.code = code
        self.status = status


def result_for(code: str, status: str = "invalid", path: str = "$") -> dict[str, Any]:
    """Build a safe single-issue result."""
    return {"status": status, "issues": [{"code": code, "path": path}], "evidence": []}


def _identity(info: os.stat_result) -> tuple[int, ...]:
    """Detect replacement and mutation while a descriptor is in use.

    A directory is identified by device, inode and type only: other processes
    legitimately add and remove entries in ancestor directories, which changes
    their size, link count and times without replacing them.
    """
    if stat.S_ISDIR(info.st_mode):
        return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


@contextmanager
def confined_file(root: Path, locator: str) -> Generator[int, None, None]:
    """Open a regular file through pinned, no-follow directory descriptors."""
    descriptors: list[int] = []
    entries: list[tuple[int, str, os.stat_result]] = []
    try:
        if (
            not locator
            or "\\" in locator
            or re.match(r"^[A-Za-z]:", locator)
            or locator.startswith("/")
        ):
            raise Refusal("unsafe-path")
        parts = locator.split("/")
        if any(p in ("", ".", "..") for p in parts):
            raise Refusal("unsafe-path")
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise Refusal("unsafe-path")
        canonical_root = root.resolve(strict=True)
        target = canonical_root.joinpath(*parts)
        if not target.resolve(strict=False).is_relative_to(canonical_root):
            raise Refusal("unsafe-path")
        current = os.open(canonical_root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(current)
        walk = list(canonical_root.parts[1:]) + parts
        for index, part in enumerate(walk):
            before = os.stat(part, dir_fd=current, follow_symlinks=False)
            final = index == len(walk) - 1
            if stat.S_ISLNK(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
                raise Refusal("unsafe-path")
            if final:
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise Refusal("unsafe-path")
            elif not stat.S_ISDIR(before.st_mode):
                raise Refusal("unsafe-path")
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if not final:
                flags |= os.O_DIRECTORY
            opened = os.open(part, flags, dir_fd=current)
            descriptors.append(opened)
            if _identity(before) != _identity(os.fstat(opened)):
                raise Refusal("unsafe-path")
            entries.append((current, part, before))
            current = opened
        start = os.fstat(current)
        yield current
        if _identity(start) != _identity(os.fstat(current)):
            raise Refusal("unsafe-path")
        for parent, name, before in entries:
            after = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if _identity(before) != _identity(after):
                raise Refusal("unsafe-path")
        if root.resolve(strict=True) != canonical_root or target.resolve(strict=True) != target:
            raise Refusal("unsafe-path")
    except FileNotFoundError as exc:
        raise Refusal("missing-evidence", "incomplete") from exc
    except (OSError, ValueError, RuntimeError) as exc:
        raise Refusal("unsafe-path") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def read_manifest(root: Path, locator: str) -> bytes:
    """Read at most one byte beyond the manifest budget."""
    try:
        with confined_file(root, locator) as descriptor:
            chunks: list[bytes] = []
            remaining = MANIFEST_LIMIT + 1
            while remaining:
                chunk = os.read(descriptor, min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        if len(raw) > MANIFEST_LIMIT:
            raise Refusal("manifest-too-large")
        return raw
    except Refusal as exc:
        if exc.code in ("unsafe-path", "missing-evidence"):
            raise Refusal("unreadable-input", "error") from exc
        raise


def hash_evidence(root: Path, locator: str, limit: int = EVIDENCE_LIMIT) -> str:
    """Stream exact bytes, stopping at the first byte beyond the budget."""
    budget = min(limit, EVIDENCE_LIMIT)
    digest = hashlib.sha256()
    with confined_file(root, locator) as descriptor:
        count = 0
        while True:
            chunk = os.read(descriptor, min(65536, budget + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            if count > budget:
                raise Refusal("evidence-too-large")
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys without disclosing their spelling."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate-key")
        result[key] = value
    return result


def _nonfinite(value: str) -> Any:
    """Reject JSON constants that are not finite numbers."""
    raise Refusal("non-finite-number")


@dataclass(frozen=True)
class OverlongInteger:
    """Preserve an integer literal without unbounded decimal conversion."""

    text: str


def _integer(text: str) -> int | OverlongInteger:
    """Convert at most 4,300 digits; retain longer literals as numeric metadata."""
    digits = len(text) - (1 if text.startswith("-") else 0)
    return int(text) if digits <= 4300 else OverlongInteger(text)


def _float(value: str) -> float:
    """Reject finite-looking decimal tokens that overflow float."""
    number = float(value)
    if not math.isfinite(number):
        raise Refusal("non-finite-number")
    return number


def parse_json(raw: bytes) -> Any:
    """Bound lexical depth before decoding; bound every decoded collection."""
    if len(raw) > MANIFEST_LIMIT:
        raise Refusal("manifest-too-large")
    if raw.startswith((
        b"\x1f\x8b",
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
        b"BZh",
        b"\xfd7zXZ\x00",
        b"7z\xbc\xaf\x27\x1c",
        b"\x28\xb5\x2f\xfd",
    )):
        raise Refusal("unsupported-input", "error")
    depth = 0
    quoted = False
    escaped = False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (91, 123):
            depth += 1
            if depth > 32:
                raise Refusal("depth-limit")
        elif char in (93, 125):
            depth -= 1
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
            parse_float=_float,
            parse_int=_integer,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refusal("malformed-input") from exc
    bound_value(value)
    return value


def bound_value(value: Any, depth: int = 0) -> None:
    """Check budgets in decoded metadata as well as normative records."""
    if isinstance(value, (dict, list)):
        if depth >= 32:
            raise Refusal("depth-limit")
        if isinstance(value, list):
            if len(value) > 1000:
                raise Refusal("list-limit")
            children = value
        else:
            children = list(value.keys()) + list(value.values())
        for child in children:
            bound_value(child, depth + 1)
    elif isinstance(value, str):
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError as exc:
            raise Refusal("malformed-input") from exc
        if size > 65536:
            raise Refusal("string-limit")
    elif isinstance(value, float) and not math.isfinite(value):
        raise Refusal("non-finite-number")


def utc_time(value: str) -> datetime:
    """Accept explicit RFC3339 UTC timestamps only."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value):
        raise Refusal("malformed-value")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Refusal("malformed-value") from exc


class Validation:
    """Collect only fixed codes and trusted field paths."""

    def __init__(self) -> None:
        self.issues: list[dict[str, str]] = []
        self.evidence: list[dict[str, str]] = []
        self.status = "valid"

    def issue(self, code: str, path: str, status: str = "invalid") -> None:
        """Preserve invalid precedence over incomplete evidence."""
        self.issues.append({"code": code, "path": path})
        ranks = {"valid": 0, "incomplete": 1, "invalid": 2, "error": 3}
        if ranks[status] > ranks[self.status]:
            self.status = status

    def result(self) -> dict[str, Any]:
        """Return the complete public result object."""
        return {"status": self.status, "issues": self.issues, "evidence": self.evidence}

    def record(self, value: Any, kind: str, path: str) -> None:
        """Validate the closed fields of a specific release or policy record."""
        if type(value) is not dict:
            self.issue("malformed-type", path)
            return
        if kind == "Component":
            kind = (
                {"oci-image": "ImageComponent", "terraform-plan": "PlanComponent"}.get(
                    value.get("kind"), "Component"
                )
                if isinstance(value.get("kind"), str)
                else "Component"
            )
        fields = RECORDS[kind]
        known = {name.rstrip("?") for name in fields} | {"extensions"}
        for name in value:
            if name not in known:
                self.issue("unknown-field", path + ".<unknown>")
        if "extensions" in value and type(value["extensions"]) is not dict:
            self.issue("malformed-type", path + ".extensions")
        for name, descriptor in fields.items():
            key = name.rstrip("?")
            field_path = path + "." + key
            if key not in value:
                if not name.endswith("?"):
                    self.issue("missing-field", field_path, "incomplete")
                continue
            field = value[key]
            if descriptor.endswith("[]"):
                if type(field) is not list:
                    self.issue("malformed-type", field_path)
                    continue
                if not field and (kind, key) in NONEMPTY:
                    self.issue("malformed-value", field_path)
                for index, item in enumerate(field):
                    self.field(item, descriptor[:-2], f"{field_path}[{index}]")
                if descriptor[:-2] in (
                    "Evidence",
                    "Check",
                    "PolicyCheck",
                    "Subject",
                    "Component",
                    "Phase",
                    "Entry",
                ):
                    identifiers = [
                        item["id"]
                        for item in field
                        if type(item) is dict and type(item.get("id")) is str
                    ]
                    if len(identifiers) != len(set(identifiers)):
                        self.issue("duplicate-id", field_path)
            else:
                self.field(field, descriptor, field_path)

    def field(self, value: Any, descriptor: str, path: str) -> None:
        """Check one typed value without including it in diagnostics."""
        if descriptor in RECORDS:
            self.record(value, descriptor, path)
            return
        if descriptor == "nullable-id" and value is None:
            return
        if descriptor in ("positive", "nonnegative"):
            if type(value) is not int:
                self.issue("malformed-type", path)
            elif value < (1 if descriptor == "positive" else 0):
                self.issue("malformed-value", path)
            return
        if type(value) is not str:
            self.issue("malformed-type", path)
            return
        if descriptor in ("id", "nullable-id"):
            if not re.fullmatch(IDENTIFIER, value):
                self.issue("unsafe-identifier", path)
        elif descriptor == "version":
            if value != "2.0":
                self.issue("unsupported-version", path, "error")
        elif descriptor == "digest":
            if not re.fullmatch(DIGEST, value):
                self.issue("malformed-value", path)
        elif descriptor == "revision":
            if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", value):
                self.issue("malformed-value", path)
        elif descriptor == "time":
            try:
                utc_time(value)
            except Refusal as exc:
                self.issue(exc.code, path)
        elif descriptor in ENUMS:
            if value not in ENUMS[descriptor]:
                self.issue("malformed-value", path)
        elif not value:
            self.issue("malformed-value", path)


def external_locator(locator: str) -> bool:
    """Refuse URL credentials and recognize supported external schemes."""
    try:
        parsed = urlsplit(locator)
        if parsed.scheme.lower() in ("https", "oci"):
            if parsed.username is not None or parsed.password is not None:
                raise Refusal("credential-locator")
            forbidden = {
                "token",
                "secret",
                "password",
                "passwd",
                "signature",
                "sig",
                "key",
                "apikey",
                "credential",
                "authorization",
            }
            for entry in parsed.query.split("&"):
                key = unquote(entry.split("=", 1)[0]).casefold()
                if forbidden.intersection(re.split(r"[^a-z0-9]+", key)):
                    raise Refusal("credential-locator")
            if not parsed.netloc or any(ord(c) < 33 for c in locator):
                raise Refusal("unsafe-path")
            return True
        if parsed.scheme:
            raise Refusal("unsafe-path")
        return False
    except ValueError as exc:
        raise Refusal("unsafe-path") from exc


def _line(text: str) -> tuple[str, int | None]:
    """Find comments and the first mapping separator in one forward pass."""
    quote = ""
    separator = None
    index = 0
    boundary = True
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 2
                    continue
                quote = ""
        elif char in "\"'" and boundary:
            quote = char
            boundary = False
        elif char == "#" and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip(), separator
        elif char == ":" and (index + 1 == len(text) or text[index + 1].isspace()):
            if separator is None:
                separator = index
                boundary = True
        elif boundary and not char.isspace():
            # Sequence markers precede a scalar; other text starts a plain scalar.
            boundary = char == "-" and (index + 1 == len(text) or text[index + 1].isspace())
        index += 1
    if quote:
        raise Refusal("malformed-input")
    return text.rstrip(), separator


def _scalar(text: str, *, key: bool = False) -> Any:
    """Decode only the declared scalar subset and empty collections."""
    text = text.strip()
    if not text:
        value: Any = None
    elif text[0] == '"':
        try:
            value = json.loads(text)
        except (ValueError, UnicodeError) as exc:
            raise Refusal("malformed-input") from exc
    elif text[0] == "'":
        if len(text) < 2 or text[-1] != "'":
            raise Refusal("malformed-input")
        inner = text[1:-1]
        index = 0
        while index < len(inner):
            if inner[index] == "'":
                if index + 1 >= len(inner) or inner[index + 1] != "'":
                    raise Refusal("malformed-input")
                index += 1
            index += 1
        value = inner.replace("''", "'")
    elif text in ("[]", "{}"):
        value = [] if text == "[]" else {}
    elif text[0] in "!&*[{|>" or text in ("---", "..."):
        raise Refusal("unsupported-input", "error")
    elif text in ("true", "false", "null"):
        value = {"true": True, "false": False, "null": None}[text]
    elif re.fullmatch(r"0|-?[1-9][0-9]*", text):
        value = _integer(text)
    else:
        value = text
    bound_value(value)
    if key:
        if not isinstance(value, str):
            raise Refusal("malformed-input")
        if value == "<<":
            raise Refusal("unsupported-input", "error")
    return value


def parse_yaml(raw: bytes) -> Any:
    """Read the bounded block-only YAML subset without resolving directives."""
    if len(raw) > MANIFEST_LIMIT:
        raise Refusal("manifest-too-large")
    if raw.startswith((
        b"\x1f\x8b",
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
        b"BZh",
        b"\xfd7zXZ\x00",
        b"7z\xbc\xaf\x27\x1c",
        b"\x28\xb5\x2f\xfd",
    )):
        raise Refusal("unsupported-input", "error")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise Refusal("malformed-input") from exc
    tokens: list[tuple[int, str, int | None]] = []
    for physical in text.split("\n"):
        physical = physical.removesuffix("\r")
        indent = len(physical) - len(physical.lstrip(" "))
        if physical[indent:].startswith("\t"):
            raise Refusal("unsupported-input", "error")
        content, _ = _line(physical[indent:])
        if not content:
            continue
        if content in ("---", "..."):
            raise Refusal("unsupported-input", "error")
        while content == "-" or content.startswith("- "):
            if indent > 64 and len(tokens) > 32:
                raise Refusal("depth-limit")
            tokens.append((indent, "-", None))
            rest = content[1:]
            spaces = len(rest) - len(rest.lstrip(" "))
            indent += 1 + spaces
            content = rest.lstrip(" ")
            if not content:
                break
        if content:
            content, separator = _line(content)
            tokens.append((indent, content, separator))
    position = 0

    def block(indent: int, depth: int) -> Any:
        """Consume one container; each token is visited once."""
        nonlocal position
        sequence = tokens[position][1] == "-"
        mapping = tokens[position][2] is not None
        if not sequence and not mapping:
            value = _scalar(tokens[position][1])
            if isinstance(value, (dict, list)) and depth > 32:
                raise Refusal("depth-limit")
            position += 1
            return value
        if depth > 32:
            raise Refusal("depth-limit")
        result: Any = [] if sequence else {}
        while position < len(tokens) and tokens[position][0] == indent:
            _, content, separator = tokens[position]
            if sequence:
                if content != "-":
                    raise Refusal("malformed-input")
                if len(result) >= 1000:
                    raise Refusal("list-limit")
                position += 1
                child = None
                if position < len(tokens) and tokens[position][0] > indent:
                    child = block(tokens[position][0], depth + 1)
                result.append(child)
            else:
                if separator is None:
                    raise Refusal("malformed-input")
                key = _scalar(content[:separator], key=True)
                if key in result:
                    raise Refusal("duplicate-key")
                tail = content[separator + 1 :].strip()
                position += 1
                if tail:
                    value = _scalar(tail)
                    if isinstance(value, (dict, list)) and depth >= 32:
                        raise Refusal("depth-limit")
                elif position < len(tokens) and tokens[position][0] > indent:
                    value = block(tokens[position][0], depth + 1)
                else:
                    value = None
                result[key] = value
        return result

    if not tokens:
        return None
    if tokens[0][0] != 0:
        raise Refusal("malformed-input")
    value = block(0, 1)
    if position != len(tokens):
        raise Refusal("malformed-input")
    bound_value(value)
    return value


def subject_keys(subjects: list[dict[str, Any]]) -> set[tuple[str, str]]:
    """Compare identities independently of inert metadata."""
    return {(item["id"], item["sha256"]) for item in subjects if "id" in item and "sha256" in item}


def validate_bytes(
    raw: bytes,
    *,
    root: Path,
    policy: Any = None,
    now: str | None = None,
    evidence_limit: int = EVIDENCE_LIMIT,
) -> dict[str, Any]:
    """Validate a candidate without executing procedures or fetching evidence."""
    try:
        data = parse_yaml(raw)
    except Refusal as exc:
        return result_for(exc.code, exc.status)
    validation = Validation()
    validation.record(data, "Candidate", "$")
    if validation.status in ("invalid", "error"):
        return validation.result()
    missing = tuple(
        issue["path"] for issue in validation.issues if issue["code"] == "missing-field"
    )

    def available(path: str) -> bool:
        """Require the named subtree and all its required facts before deriving gaps."""
        return not any(
            path == absent
            or path.startswith((absent + ".", absent + "["))
            or absent.startswith((path + ".", path + "["))
            for absent in missing
        )

    if policy is None:
        validation.issue("policy-missing", "$.policy", "incomplete")
    else:
        try:
            bound_value(policy)
        except Refusal as exc:
            return result_for(exc.code, exc.status, "$.policy")
        checked_policy = Validation()
        checked_policy.record(policy, "Policy", "$.policy")
        if checked_policy.issues:
            checked_policy.status = "invalid"
            return checked_policy.result()
    try:
        clock = utc_time(now) if now is not None else datetime.now(UTC)
    except Refusal:
        return result_for("malformed-input", "error", "$.now")

    def fresh(value: str | None, path: str) -> bool:
        """Use only the caller's clock and trusted maximum age."""
        if value is None:
            return False
        seconds = (clock - utc_time(value)).total_seconds()
        if seconds < 0:
            validation.issue("future-time", path)
            return False
        if policy is not None and seconds > policy["max_age_seconds"]:
            validation.issue("stale", path, "incomplete")
            return False
        return True

    fresh(data.get("created_at"), "$.created_at")
    evidence_items = data.get("evidence", [])
    evidence = {item["id"]: item for item in evidence_items if "id" in item}
    evidence_ids_complete = "evidence" in data and all("id" in item for item in evidence_items)
    evidence_paths = {
        item["id"]: f"$.evidence[{index}]"
        for index, item in enumerate(evidence_items)
        if "id" in item
    }
    verified: set[str] = set()
    external: set[str] = set()
    for index, item in enumerate(evidence_items):
        path = f"$.evidence[{index}]"
        current = fresh(item.get("observed_at"), path + ".observed_at")
        verification = "unverified"
        if "locator" in item:
            try:
                if external_locator(item["locator"]):
                    if "id" in item:
                        external.add(item["id"])
                else:
                    digest = hash_evidence(root, item["locator"], evidence_limit)
                    if "sha256" in item:
                        if digest != item["sha256"]:
                            validation.issue("digest-mismatch", path + ".sha256")
                        else:
                            verification = "verified"
                            if current and "id" in item:
                                verified.add(item["id"])
            except Refusal as exc:
                validation.issue(exc.code, path + ".locator", exc.status)
        if "id" in item:
            validation.evidence.append({"id": item["id"], "verification": verification})

    def reference(identifier: str | None, path: str) -> bool:
        """Require verified, fresh evidence for every live reference."""
        if identifier is None:
            return False
        if identifier not in evidence and not evidence_ids_complete:
            return False
        if identifier in evidence and any(
            field not in evidence[identifier] for field in ("locator", "sha256", "observed_at")
        ):
            return False
        if identifier not in verified:
            if identifier in external:
                validation.issue("unverified-evidence", path, "incomplete")
            validation.issue("missing-evidence", path, "incomplete")
            return False
        return True

    for index, source in enumerate(data.get("sources", [])):
        path = f"$.sources[{index}]"
        if "revision" in source and "snapshot" in source:
            validation.issue("malformed-value", path)
        elif "revision" not in source and "snapshot" not in source:
            validation.issue("missing-field", path, "incomplete")
        if "snapshot" in source:
            reference(source["snapshot"], path + ".snapshot")

    components = data.get("components", [])
    if "components" in data and not components:
        validation.issue("empty-components", "$.components")
    component_by_id = {item["id"]: item for item in components if "id" in item}
    identities: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for index, component in enumerate(components):
        path = f"$.components[{index}]"
        kind = component.get("kind")
        if "id" in component and kind is not None:
            kinds[component["id"]] = kind
        if kind is None:
            continue
        if kind not in ("oci-image", "terraform-plan"):
            validation.issue("unsupported-component-kind", path + ".kind", "incomplete")
            continue
        identifier = component.get("artifact" if kind == "oci-image" else "plan_bundle")
        reference(identifier, path)
        artifact = evidence.get(identifier)
        if artifact is not None and "sha256" in artifact and "id" in component:
            identities[component["id"]] = artifact["sha256"]
        if kind == "oci-image" and "image_ref" in component:
            image = component["image_ref"]
            # The tag belongs to the final path segment, not a registry port.
            match = re.fullmatch(r"[^\s@]+:[^\s/:@]+@(sha256:[0-9a-f]{64})", image)
            if match is None or ":" not in image.split("@", 1)[0].rsplit("/", 1)[-1]:
                validation.issue("invalid-image-reference", path + ".image_ref")
            elif artifact is not None and "sha256" in artifact and match[1] != artifact["sha256"]:
                validation.issue("subject-mismatch", path + ".image_ref")

    def subjects_match(subjects: list[dict[str, Any]], path: str) -> bool:
        """Bind all declared subjects to component or evidence identities."""
        complete = len(subject_keys(subjects)) == len(subjects)
        for identifier, digest in subject_keys(subjects):
            expected = identities.get(identifier)
            if expected is None and identifier in evidence:
                expected = evidence[identifier].get("sha256")
            if expected is None:
                if (
                    "components" in data
                    and all("id" in item for item in components)
                    and evidence_ids_complete
                    and identifier not in component_by_id
                    and identifier not in evidence
                ):
                    validation.issue("subject-mismatch", path)
                complete = False
            elif expected != digest:
                validation.issue("subject-mismatch", path)
                complete = False
        return complete

    for index, item in enumerate(evidence_items):
        subjects_match(item.get("subjects", []), f"$.evidence[{index}].subjects")

    provenance: set[tuple[str, str]] = set()
    for index, identifier in enumerate(data.get("provenance", [])):
        if reference(identifier, f"$.provenance[{index}]"):
            provenance.update(subject_keys(evidence[identifier].get("subjects", [])))
    for identifier, digest in identities.items():
        if (
            available("$.provenance")
            and available("$.evidence")
            and (identifier, digest) not in provenance
        ):
            validation.issue("missing-evidence", "$.provenance", "incomplete")

    requirements = policy["required_checks"] if policy is not None else []
    required = {item["id"]: item for item in requirements}
    satisfied: dict[str, set[str]] = {}
    for index, check in enumerate(data.get("checks", [])):
        path = f"$.checks[{index}]"
        subjects = check.get("subjects", [])
        bound = subjects_match(subjects, path + ".subjects") and bool(subjects)
        requirement = required.get(check.get("id"))
        if requirement is not None and "stage" in check and check["stage"] != requirement["stage"]:
            validation.issue("subject-mismatch", path + ".stage")
            bound = False
        status = check.get("status")
        if status == "fail":
            validation.issue("check-failed", path + ".status")
        elif status == "pass":
            complete = bound and bool(check.get("evidence"))
            covered: set[tuple[str, str]] = set()
            for identifier in check.get("evidence", []):
                if not reference(identifier, path + ".evidence"):
                    complete = False
                covered.update(subject_keys(evidence.get(identifier, {}).get("subjects", [])))
            if "evidence" in check and not check["evidence"]:
                validation.issue("missing-evidence", path + ".evidence", "incomplete")
            elif (
                "evidence" in check
                and all(
                    identifier in evidence and available(evidence_paths[identifier] + ".subjects")
                    for identifier in check.get("evidence", [])
                )
                and not subject_keys(subjects).issubset(covered)
            ):
                validation.issue("subject-mismatch", path + ".evidence")
                complete = False
            if complete and "id" in check:
                satisfied[check["id"]] = {item["id"] for item in subjects if "id" in item}
        elif status == "not-applicable" and "id" in check:
            if (
                requirement is None
                or not check.get("reason")
                or check["reason"] not in requirement["allowed_not_applicable_reasons"]
                or check.get("policy_basis") != policy["id"] + "/" + check["id"]
            ):
                validation.issue("invalid-applicability", path)
            elif bound:
                satisfied[check["id"]] = {item["id"] for item in subjects if "id" in item}
        elif requirement is not None and "status" in check:
            validation.issue("missing-evidence", path, "incomplete")
        if status != "pass":
            for identifier in check.get("evidence", []):
                if identifier not in evidence and evidence_ids_complete:
                    validation.issue("missing-evidence", path + ".evidence", "incomplete")
    for requirement in requirements:
        for identifier, kind in kinds.items():
            if (
                available("$.checks")
                and available("$.components")
                and available("$.evidence")
                and kind == requirement["component_kind"]
                and identifier not in satisfied.get(requirement["id"], set())
            ):
                validation.issue("missing-evidence", "$.checks." + requirement["id"], "incomplete")

    phases_seen: set[str] = set()
    phase_ids_complete = True
    placed: set[str] = set()
    approved = (
        {item["id"]: item["sha256"] for item in policy["approved_procedures"]}
        if policy is not None
        else {}
    )
    for index, phase in enumerate(data.get("phases", [])):
        path = f"$.phases[{index}]"
        if phase_ids_complete and any(
            identifier not in phases_seen for identifier in phase.get("depends_on", [])
        ):
            validation.issue("invalid-phase-order", path + ".depends_on")
        if "id" in phase:
            phases_seen.add(phase["id"])
        else:
            phase_ids_complete = False
        for identifier in phase.get("components", []):
            if available("$.components") and identifier not in component_by_id:
                validation.issue("missing-evidence", path + ".components", "incomplete")
            placed.add(identifier)
        for identifier in phase.get("procedures", []):
            reference(identifier, path + ".procedures")
            artifact = evidence.get(identifier)
            if (
                policy is not None
                and artifact is not None
                and "sha256" in artifact
                and approved.get(identifier) != artifact["sha256"]
            ):
                validation.issue("unapproved-procedure", path + ".procedures")
    if available("$.phases") and any(identifier not in placed for identifier in component_by_id):
        validation.issue("missing-evidence", "$.phases", "incomplete")
    return validation.result()


def _yaml_scalar(value: Any) -> str:
    """Retain marked integer spelling when emitting scalar values."""
    if isinstance(value, OverlongInteger):
        return value.text
    return json.dumps(value, ensure_ascii=True)


def yaml_bytes(value: Any, indent: int = 0) -> bytes:
    """Serialize bounded values using the reader's block-only subset."""
    prefix = " " * indent
    lines: list[bytes] = []
    if isinstance(value, dict) and value:
        for key, child in value.items():
            label = prefix + json.dumps(key, ensure_ascii=True) + ":"
            if isinstance(child, (dict, list)) and child:
                lines.append(label.encode() + b"\n" + yaml_bytes(child, indent + 2))
            else:
                lines.append((label + " " + _yaml_scalar(child) + "\n").encode())
    elif isinstance(value, list) and value:
        for child in value:
            if isinstance(child, (dict, list)) and child:
                lines.append((prefix + "-\n").encode() + yaml_bytes(child, indent + 2))
            else:
                lines.append(
                    (prefix + "- " + _yaml_scalar(child) + "\n").encode()
                )
    else:
        lines.append((prefix + _yaml_scalar(value) + "\n").encode())
    return b"".join(lines)


def translate_v1(data: Any) -> dict[str, Any]:
    """Preserve known legacy facts without inventing evidence or identities."""
    if type(data) is not dict:
        raise Refusal("malformed-type")
    if data.get("schema_version") != "1.0":
        raise Refusal("unsupported-version", "error")
    candidate: dict[str, Any] = {"schema_version": "2.0"}
    for old, new in (("built_at", "created_at"), ("built_by", "producer")):
        if old in data:
            candidate[new] = data[old]
    if "component_manifest" in data:
        if type(data["component_manifest"]) is not list:
            raise Refusal("malformed-type")
        components = []
        for item in data["component_manifest"]:
            if type(item) is not dict:
                raise Refusal("malformed-type")
            component = {"kind": "oci-image"}
            for old, new in (("name", "id"), ("image_ref", "image_ref")):
                if old in item:
                    component[new] = item[old]
            components.append(component)
        candidate["components"] = components
    if "changelog_delta" in data:
        changes = data["changelog_delta"]
        if type(changes) is not dict:
            raise Refusal("malformed-type")
        candidate["changes"] = {}
        for old, new in (("since_ref", "baseline"), ("entries", "entries")):
            if old in changes:
                candidate["changes"][new] = changes[old]
    if "test_evidence_summary" in data:
        summary = data["test_evidence_summary"]
        if type(summary) is not dict:
            raise Refusal("malformed-type")
        checks = []
        for name, status in summary.items():
            if not re.fullmatch(IDENTIFIER, name):
                raise Refusal("unsafe-identifier")
            if status not in ("pass", "fail"):
                raise Refusal("malformed-value")
            checks.append({"id": name, "status": status})
        candidate["checks"] = checks
    if "deploy_phases" in data:
        if type(data["deploy_phases"]) is not list:
            raise Refusal("malformed-type")
        phases = []
        for phase in data["deploy_phases"]:
            if type(phase) is not dict:
                raise Refusal("malformed-type")
            phases.append({"id": phase["phase"]} if "phase" in phase else {})
        candidate["phases"] = phases
    return candidate


def merge_supplement(known: Any, supplied: Any, path: str = "$") -> Any:
    """Join missing facts, refusing changes to any already known fact."""
    if type(known) is dict and type(supplied) is dict:
        merged = dict(known)
        for key, value in supplied.items():
            if key in known:
                merged[key] = merge_supplement(known[key], value, path + "." + key)
            else:
                merged[key] = value
        return merged
    if (
        type(known) is list
        and type(supplied) is list
        and path in ("$.components", "$.checks", "$.phases")
    ):
        by_id = {item["id"]: item for item in supplied if type(item) is dict and "id" in item}
        merged_items = []
        for item in known:
            if item.get("id") not in by_id:
                raise Refusal("supplement-conflict")
            merged_items.append(merge_supplement(item, by_id.pop(item["id"]), path + "[]"))
        merged_items.extend(by_id.values())
        return merged_items
    if type(known) is not type(supplied) or known != supplied:
        raise Refusal("supplement-conflict")
    return known


def legacy_bindings(legacy: dict[str, Any], candidate: dict[str, Any]) -> None:
    """Keep legacy provenance subjects and inspection references consistent."""
    evidence = {item["id"]: item for item in candidate.get("evidence", []) if "id" in item}
    provenance = legacy.get("provenance_ref", {})
    inspection = legacy.get("iac_plan_ref", {})
    if type(provenance) is not dict or type(inspection) is not dict:
        raise Refusal("malformed-type")
    if "subject_digest" in provenance:
        shape = Validation()
        shape.field(provenance["subject_digest"], "digest", "$.provenance")
        if shape.issues:
            raise Refusal("malformed-value")
        subjects = {
            subject.get("sha256")
            for identifier in candidate.get("provenance", [])
            for subject in evidence.get(identifier, {}).get("subjects", [])
        }
        if subjects and provenance["subject_digest"] not in subjects:
            raise Refusal("supplement-conflict")
    for component in candidate.get("components", []):
        if component.get("kind") == "terraform-plan":
            bundle = evidence.get(component.get("plan_bundle"), {})
            if "path" in inspection and bundle.get("locator") == inspection["path"]:
                raise Refusal("supplement-conflict")


@contextmanager
def output_directory(
    root: Path, output: str, source: str
) -> Generator[tuple[int, str, Callable[[], None]], None, None]:
    """Pin the output directory and refuse aliases, links and replacements."""
    descriptors: list[int] = []
    entries: list[tuple[int, str, tuple[int, int, int]]] = []
    try:
        canonical = root.resolve(strict=True)
        destination = canonical / output
        input_path = canonical / source
        if destination.resolve(strict=False) == input_path.resolve(strict=False):
            raise Refusal("output-is-input")
        try:
            before = input_path.stat()
            after = destination.stat()
            if (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino):
                raise Refusal("output-is-input")
        except FileNotFoundError:
            pass
        if (
            not output
            or output.startswith("/")
            or "\\" in output
            or re.match(r"^[A-Za-z]:", output)
            or any(part in ("", ".", "..") for part in output.split("/"))
            or not destination.resolve(strict=False).is_relative_to(canonical)
            or not hasattr(os, "O_NOFOLLOW")
            or not hasattr(os, "O_DIRECTORY")
        ):
            raise Refusal("unsafe-path")
        current = os.open(canonical.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(current)
        parts = list(canonical.parts[1:]) + output.split("/")[:-1]
        for part in parts:
            info = os.stat(part, dir_fd=current, follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise Refusal("unsafe-path")
            opened = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            descriptors.append(opened)
            if _identity(info) != _identity(os.fstat(opened)):
                raise Refusal("unsafe-path")
            entries.append((current, part, (info.st_dev, info.st_ino, info.st_mode)))
            current = opened
        name = output.split("/")[-1]
        try:
            os.stat(name, dir_fd=current, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Refusal("output-exists")

        def recheck() -> None:
            """Check directory identities while allowing our own entry changes."""
            for parent, part, identity in entries:
                info = os.stat(part, dir_fd=parent, follow_symlinks=False)
                if (info.st_dev, info.st_ino, info.st_mode) != identity:
                    raise Refusal("unsafe-path")
            if root.resolve(strict=True) != canonical:
                raise Refusal("unsafe-path")

        recheck()
        yield current, name, recheck
    except (OSError, ValueError, RuntimeError) as exc:
        raise Refusal("unsafe-path") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def write_candidate(descriptor: int, raw: bytes) -> None:
    """Write all candidate bytes, refusing a stalled or partial write."""
    remaining = memoryview(raw)
    while remaining:
        count = os.write(descriptor, remaining)
        if count <= 0:
            raise OSError("write failed")
        remaining = remaining[count:]


def publish_candidate(directory: int, temporary: str, destination: str) -> None:
    """Publish atomically without overwriting a destination that appeared."""
    os.link(
        temporary, destination, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False
    )


def save_candidate(
    directory: int,
    destination: str,
    raw: bytes,
    recheck: Callable[[], None],
    write: Callable[[int, bytes], None],
    publish: Callable[[int, str, str], None],
) -> None:
    """Fsync temporary bytes and clean up failed writes or publications."""
    # A unique, unguessable name; O_EXCL below refuses any collision.
    temporary = ".release-handoff-" + os.urandom(16).hex() + ".tmp"
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
    except OSError:
        raise Refusal("output-failed", "error") from None
    try:
        write(descriptor, raw)
        os.fsync(descriptor)
        recheck()
        publish(directory, temporary, destination)
        recheck()
        os.unlink(temporary, dir_fd=directory)
    except (OSError, Refusal, ValueError, RuntimeError):
        # The callback may fail after linking. Remove only our own inode.
        with suppress(FileNotFoundError):
            info = os.stat(destination, dir_fd=directory, follow_symlinks=False)
            own = os.fstat(descriptor)
            if (info.st_dev, info.st_ino) == (own.st_dev, own.st_ino):
                os.unlink(destination, dir_fd=directory)
        raise Refusal("output-failed", "error") from None
    finally:
        os.close(descriptor)
        with suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=directory)


def import_v1(
    source: str,
    *,
    output: str,
    root: Path,
    policy: str | None = None,
    supplement: str | None = None,
    now: str | None = None,
    evidence_limit: int = EVIDENCE_LIMIT,
    write: Callable[[int, bytes], None] = write_candidate,
    publish: Callable[[int, str, str], None] = publish_candidate,
) -> dict[str, Any]:
    """Import legacy facts into a new candidate; never open the source for writing."""
    try:
        with output_directory(root, output, source) as (directory, name, recheck):
            raw = read_manifest(root, source)
            legacy = parse_yaml(raw)
            candidate = translate_v1(legacy)
            supplied = parse_json(read_manifest(root, supplement)) if supplement else {}
            if type(supplied) is not dict:
                raise Refusal("malformed-type")
            shape = Validation()
            shape.record(candidate, "Candidate", "$")
            shape.record(supplied, "Candidate", "$")
            if shape.status in ("invalid", "error"):
                return shape.result()
            candidate = merge_supplement(candidate, supplied)
            legacy_bindings(legacy, candidate)
            gaps = Validation()
            for index, check in enumerate(candidate.get("checks", [])):
                if check.get("status") == "pass" and not (
                    check.get("subjects") and check.get("evidence")
                ):
                    check["status"] = "not-run"
                    gaps.issue("missing-evidence", f"$.checks[{index}]", "incomplete")
            if "iac_plan_ref" in legacy and not any(
                component.get("kind") == "terraform-plan" and component.get("plan_bundle")
                for component in candidate.get("components", [])
            ):
                if not any(
                    component.get("kind") == "terraform-plan"
                    for component in candidate.get("components", [])
                ):
                    candidate.setdefault("components", []).append({"kind": "terraform-plan"})
                gaps.issue("missing-evidence", "$.components", "incomplete")
            trusted = parse_json(read_manifest(root, policy)) if policy else None
            encoded = yaml_bytes(candidate)
            result = validate_bytes(
                encoded, root=root, policy=trusted, now=now, evidence_limit=evidence_limit
            )
            for item in result["issues"]:
                gaps.issue(item["code"], item["path"], result["status"])
            gaps.evidence = result["evidence"]
            if gaps.status in ("invalid", "error"):
                return gaps.result()
            verified = {
                item["id"] for item in result["evidence"] if item["verification"] == "verified"
            }
            for index, evidence in enumerate(candidate.get("evidence", [])):
                if any(
                    item["path"].startswith(f"$.evidence[{index}].") for item in result["issues"]
                ):
                    verified.discard(evidence.get("id"))
            for index, check in enumerate(candidate.get("checks", [])):
                if check.get("status") == "pass" and any(
                    identifier not in verified for identifier in check.get("evidence", [])
                ):
                    check["status"] = "not-run"
                    gaps.issue("missing-evidence", f"$.checks[{index}]", "incomplete")
            encoded = yaml_bytes(candidate)
            recheck()
            save_candidate(directory, name, encoded, recheck, write, publish)
            return gaps.result()
    except Refusal as exc:
        return result_for(exc.code, exc.status)
    except (OSError, ValueError, RuntimeError):
        return result_for("output-failed", "error")


class SafeParser(argparse.ArgumentParser):
    """Suppress diagnostics that can include untrusted arguments."""

    def error(self, message: str) -> Any:
        """Return a fixed usage refusal."""
        raise Refusal("usage", "error")


def main(argv: list[str] | None = None) -> int:
    """Emit one UTF-8 JSON result and the specified exit status."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = SafeParser(add_help=False)
    parser.add_argument("command", choices=["validate", "import-v1"])
    parser.add_argument("input")
    parser.add_argument("--root", required=True)
    parser.add_argument("--policy")
    parser.add_argument("--now")
    parser.add_argument("--output")
    parser.add_argument("--supplement")
    try:
        args = parser.parse_args(argv)
        root = Path(args.root)
        if args.command == "import-v1":
            if not args.output:
                raise Refusal("usage", "error")
            result = import_v1(
                args.input,
                output=args.output,
                root=root,
                policy=args.policy,
                supplement=args.supplement,
                now=args.now,
            )
        else:
            if args.output or args.supplement:
                raise Refusal("usage", "error")
            raw = read_manifest(root, args.input)
            policy = parse_json(read_manifest(root, args.policy)) if args.policy else None
            result = validate_bytes(raw, root=root, policy=policy, now=args.now)
    except Refusal as exc:
        result = result_for(exc.code, exc.status)
    except (OSError, ValueError, RuntimeError):
        result = result_for("unreadable-input", "error")
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 2 if result["status"] == "error" else 1


if __name__ == "__main__":
    sys.exit(main())
