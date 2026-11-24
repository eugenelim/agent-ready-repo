#!/usr/bin/env python3
"""Validate reviewed saved-plan bundles using local, bounded evidence only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

MANIFEST_LIMIT = 1_048_576
EVIDENCE_LIMIT = 536_870_912
IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
DIGEST = r"^sha256:[0-9a-f]{64}$"
STAGES = ("validation", "policy", "security", "review")
ENUMS = {
    "engine": ("terraform", "opentofu"),
    "stage": STAGES,
    "status": ("pass", "fail", "not-run", "not-applicable"),
    "action": ("no-op", "create", "read", "update", "delete"),
    "reversibility": ("reversible", "costly-to-reverse", "one-way-door"),
}
# A trailing question mark denotes an optional field, not a nullable value.
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
        "stage": "stage",
        "status": "status",
        "subjects": "Subject[]",
        "evidence": "id[]",
        "reason?": "string",
        "policy_basis?": "string",
    },
    "Target": {"environment": "string", "account": "string"},
    "Provider": {"source": "string", "version": "string"},
    "Toolchain": {
        "engine": "engine",
        "version": "string",
        "providers": "Provider[]",
        "lock": "id",
    },
    "State": {
        "backend": "string",
        "workspace": "string",
        "lineage?": "string",
        "serial?": "nonnegative",
        "new_workspace?": "id",
    },
    "Plan": {"saved_plan": "id", "inspection": "id"},
    "Freshness": {"policy_id": "id", "max_age_seconds": "positive"},
    "Change": {"address": "string", "actions": "action[]"},
    "Impact": {"address": "string", "impact": "string", "reversibility": "reversibility"},
    "Effects": {"changes": "Change[]", "stateful_impacts": "Impact[]", "cost": "nullable-id"},
    "Bundle": {
        "schema_version": "version",
        "source": "Source",
        "request": "id",
        "constraints": "id[]",
        "evidence": "Evidence[]",
        "toolchain": "Toolchain",
        "target": "Target",
        "state": "State",
        "plan": "Plan",
        "created_at": "time",
        "freshness": "Freshness",
        "checks": "Check[]",
        "effects": "Effects",
    },
    "PolicyCheck": {
        "id": "id",
        "stage": "stage",
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
    ("Toolchain", "providers"),
    ("Bundle", "constraints"),
}


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
        """Validate the closed fields of a specific plan or policy record."""
        if type(value) is not dict:
            self.issue("malformed-type", path)
            return
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
                if descriptor[:-2] in ("Evidence", "Check", "PolicyCheck", "Subject"):
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
            if value != "iac-plan-bundle.v1":
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


def validate_bytes(
    raw: bytes,
    *,
    root: Path,
    policy: Any = None,
    now: str | None = None,
    expectations: dict[str, Any] | None = None,
    evidence_limit: int = EVIDENCE_LIMIT,
) -> dict[str, Any]:
    """Parse and validate a bundle using caller-selected policy and clock."""
    try:
        data = parse_json(raw)
    except Refusal as exc:
        return result_for(exc.code, exc.status)
    validation = Validation()
    validation.record(data, "Bundle", "$")
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
        validation.issue("policy-missing", "$.freshness", "incomplete")
    else:
        try:
            bound_value(policy)
        except Refusal as exc:
            return result_for(exc.code, exc.status, "$.policy")
        policy_validation = Validation()
        policy_validation.record(policy, "Policy", "$.policy")
        if policy_validation.issues:
            policy_validation.status = "invalid"
            return policy_validation.result()
    try:
        clock = utc_time(now) if now is not None else datetime.now(UTC)
    except Refusal:
        return result_for("malformed-input", "error", "$.now")
    bundle_freshness = data.get("freshness", {})
    age = bundle_freshness.get("max_age_seconds")
    if policy is not None:
        age = min(age, policy["max_age_seconds"]) if age is not None else policy["max_age_seconds"]
        if "policy_id" in bundle_freshness and bundle_freshness["policy_id"] != policy["id"]:
            validation.issue("policy-mismatch", "$.freshness.policy_id")

    def freshness(value: str | None, path: str) -> bool:
        """Evaluate a present timestamp with the injected trusted clock."""
        if value is None:
            return False
        seconds = (clock - utc_time(value)).total_seconds()
        if seconds < 0:
            validation.issue("future-time", path)
            return False
        if age is not None and seconds > age:
            validation.issue("stale", path, "incomplete")
            return False
        return True

    freshness(data.get("created_at"), "$.created_at")
    evidence_items = data.get("evidence", [])
    evidence = {item["id"]: item for item in evidence_items if "id" in item}
    evidence_ids_complete = "evidence" in data and all("id" in item for item in evidence_items)
    verified: set[str] = set()
    external_ids: set[str] = set()
    for index, item in enumerate(evidence_items):
        path = f"$.evidence[{index}]"
        fresh = freshness(item.get("observed_at"), path + ".observed_at")
        verification = "unverified"
        if "locator" in item:
            try:
                if external_locator(item["locator"]):
                    if "id" in item:
                        external_ids.add(item["id"])
                else:
                    actual = hash_evidence(root, item["locator"], evidence_limit)
                    if "sha256" in item:
                        if actual != item["sha256"]:
                            validation.issue("digest-mismatch", path + ".sha256")
                        else:
                            verification = "verified"
                            if fresh and "id" in item:
                                verified.add(item["id"])
            except Refusal as exc:
                validation.issue(exc.code, path + ".locator", exc.status)
        if "id" in item:
            validation.evidence.append({"id": item["id"], "verification": verification})

    def reference(identifier: str | None, path: str) -> bool:
        """Require a present, verified and fresh evidence identity."""
        if identifier is None:
            return False
        if identifier not in evidence and not evidence_ids_complete:
            return False
        if identifier in evidence and any(
            field not in evidence[identifier] for field in ("locator", "sha256", "observed_at")
        ):
            return False
        if identifier not in evidence or identifier not in verified:
            if identifier in external_ids:
                validation.issue("unverified-evidence", path, "incomplete")
            validation.issue("missing-evidence", path, "incomplete")
            return False
        return True

    reference(data.get("request"), "$.request")
    for index, identifier in enumerate(data.get("constraints", [])):
        reference(identifier, f"$.constraints[{index}]")
    toolchain = data.get("toolchain", {})
    reference(toolchain.get("lock"), "$.toolchain.lock")
    source = data.get("source", {})
    if "source" in data:
        if "revision" in source and "snapshot" in source:
            validation.issue("malformed-value", "$.source")
        elif "revision" not in source and "snapshot" not in source:
            validation.issue("missing-field", "$.source", "incomplete")
        if "snapshot" in source:
            reference(source["snapshot"], "$.source.snapshot")
    state = data.get("state", {})
    if "new_workspace" in state:
        if "lineage" in state or "serial" in state:
            validation.issue("malformed-value", "$.state")
        reference(state["new_workspace"], "$.state.new_workspace")
    elif "state" in data:
        for field in ("lineage", "serial"):
            if field not in state:
                validation.issue("missing-field", "$.state." + field, "incomplete")
    cost = data.get("effects", {}).get("cost")
    if cost is not None:
        reference(cost, "$.effects.cost")
    plan = data.get("plan", {})
    for field in ("saved_plan", "inspection"):
        reference(plan.get(field), "$.plan." + field)
    saved = evidence.get(plan.get("saved_plan"))
    expected_subject = (
        (saved["id"], saved["sha256"]) if saved is not None and "sha256" in saved else None
    )

    def subject_keys(subjects: list[dict[str, Any]]) -> set[tuple[str, str]]:
        """Ignore inert metadata when comparing artifact identities."""
        return {
            (subject["id"], subject["sha256"])
            for subject in subjects
            if "id" in subject and "sha256" in subject
        }

    for index, item in enumerate(evidence_items):
        for subject in item.get("subjects", []):
            if "id" in subject and "sha256" in subject:
                artifact = evidence.get(subject["id"])
                if artifact is None:
                    if evidence_ids_complete:
                        validation.issue("subject-mismatch", f"$.evidence[{index}].subjects")
                elif "sha256" in artifact and artifact["sha256"] != subject["sha256"]:
                    validation.issue("subject-mismatch", f"$.evidence[{index}].subjects")
    inspection = evidence.get(plan.get("inspection"))
    if inspection is not None and expected_subject is not None and "subjects" in inspection:
        subjects = inspection["subjects"]
        if len(subject_keys(subjects)) == len(subjects) and expected_subject not in subject_keys(
            subjects
        ):
            validation.issue("subject-mismatch", "$.plan.inspection")

    def subjects_match(subjects: list[dict[str, Any]], path: str) -> bool:
        """Check each named artifact identity against bundle evidence."""
        keys = subject_keys(subjects)
        complete = len(keys) == len(subjects)
        valid = complete
        for identifier, digest in keys:
            artifact = evidence.get(identifier)
            if artifact is None:
                if evidence_ids_complete:
                    validation.issue("subject-mismatch", path)
                valid = False
            elif "sha256" not in artifact:
                valid = False
            elif artifact["sha256"] != digest:
                validation.issue("subject-mismatch", path)
                valid = False
        return valid

    requirements = policy["required_checks"] if policy is not None else []
    required = {
        item["id"]: item for item in requirements if item["component_kind"] == "terraform-plan"
    }
    successful_stages: set[str] = set()
    satisfied: set[str] = set()
    for index, check in enumerate(data.get("checks", [])):
        path = f"$.checks[{index}]"
        bound = "subjects" in check and subjects_match(check["subjects"], path + ".subjects")
        requirement = required.get(check.get("id"))
        if requirement is not None and "stage" in check and check["stage"] != requirement["stage"]:
            validation.issue("subject-mismatch", path + ".stage")
            bound = False
        status = check.get("status")
        if status != "pass":
            for identifier in check.get("evidence", []):
                if identifier not in evidence and evidence_ids_complete:
                    validation.issue("missing-evidence", path + ".evidence", "incomplete")
        if status == "fail":
            validation.issue("check-failed", path + ".status")
        elif status == "pass":
            complete = bool(check.get("evidence")) and bound
            if "evidence" in check and not check["evidence"]:
                validation.issue("missing-evidence", path + ".evidence", "incomplete")
            covered: set[tuple[str, str]] = set()
            coverage_known = bool(check.get("evidence"))
            for identifier in check.get("evidence", []):
                if not reference(identifier, path + ".evidence"):
                    complete = False
                item = evidence.get(identifier)
                if item is not None and "subjects" in item:
                    keys = subject_keys(item["subjects"])
                    covered.update(keys)
                    coverage_known = coverage_known and len(keys) == len(item["subjects"])
                else:
                    coverage_known = False
            if coverage_known and not subject_keys(check.get("subjects", [])).issubset(covered):
                validation.issue("subject-mismatch", path + ".evidence")
                complete = False
            if complete and "stage" in check and "id" in check:
                if expected_subject in subject_keys(check.get("subjects", [])):
                    successful_stages.add(check["stage"])
                satisfied.add(check["id"])
        elif status == "not-applicable" and "id" in check:
            if (
                requirement is None
                or not check.get("reason")
                or check["reason"] not in requirement["allowed_not_applicable_reasons"]
                or check.get("policy_basis") != policy["id"] + "/" + check["id"]
            ):
                validation.issue("invalid-applicability", path)
            elif bound:
                satisfied.add(check["id"])
        elif requirement is not None and "status" in check:
            validation.issue("missing-evidence", path, "incomplete")
    for stage in STAGES:
        if (
            available("$.checks")
            and available("$.evidence")
            and available("$.plan")
            and stage not in successful_stages
        ):
            validation.issue("missing-evidence", "$.checks." + stage, "incomplete")
    for identifier in required:
        if (
            available("$.checks")
            and available("$.evidence")
            and available("$.plan")
            and identifier not in satisfied
        ):
            validation.issue("missing-evidence", "$.checks." + identifier, "incomplete")
    actual_expectations = {
        "environment": data.get("target", {}).get("environment"),
        "account": data.get("target", {}).get("account"),
        "backend": state.get("backend"),
        "workspace": state.get("workspace"),
        "lineage": state.get("lineage"),
        "serial": state.get("serial"),
        "engine": toolchain.get("engine"),
        "engine_version": toolchain.get("version"),
    }
    for name, value in (expectations or {}).items():
        if name not in actual_expectations:
            validation.issue("malformed-value", "$.expectations.<unknown>", "error")
        elif (
            name in ("lineage", "serial")
            and "new_workspace" in state
            or actual_expectations[name] is not None
            and (
                type(value) is not type(actual_expectations[name])
                or value != actual_expectations[name]
            )
        ):
            validation.issue("expectation-mismatch", "$.expectations." + name)
    return validation.result()


class SafeParser(argparse.ArgumentParser):
    """Suppress argparse diagnostics that can include untrusted argv."""

    def error(self, message: str) -> Any:
        """Return a fixed usage refusal instead of printing arguments."""
        raise Refusal("usage", "error")


def main(argv: list[str] | None = None) -> int:
    """Emit exactly one UTF-8 JSON result for every validation invocation."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = SafeParser(add_help=False)
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("input")
    parser.add_argument("--root", required=True)
    parser.add_argument("--policy")
    parser.add_argument("--now")
    for name in (
        "environment",
        "account",
        "backend",
        "workspace",
        "lineage",
        "serial",
        "engine",
        "engine-version",
    ):
        parser.add_argument("--expect-" + name, type=int if name == "serial" else str)
    try:
        args = parser.parse_args(argv)
        root = Path(args.root)
        raw = read_manifest(root, args.input)
        policy = parse_json(read_manifest(root, args.policy)) if args.policy else None
        expectations = {
            name: getattr(args, "expect_" + name)
            for name in (
                "environment",
                "account",
                "backend",
                "workspace",
                "lineage",
                "serial",
                "engine",
                "engine_version",
            )
            if getattr(args, "expect_" + name) is not None
        }
        result = validate_bytes(
            raw, root=root, policy=policy, now=args.now, expectations=expectations
        )
    except Refusal as exc:
        result = result_for(exc.code, exc.status)
    except (OSError, ValueError, RuntimeError):
        result = result_for("unreadable-input", "error")
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 2 if result["status"] == "error" else 1


if __name__ == "__main__":
    sys.exit(main())
