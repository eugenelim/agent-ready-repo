#!/usr/bin/env python3
"""Discover confined governance sources and check local summaries and reviews."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

SOURCE_LIMIT = 262_144
EVIDENCE_LIMIT = 536_870_912
SUMMARY_LIMIT = 1_048_576
FILE_LIMIT = 500
DECISION_DIRS = ("docs/adr", "docs/decisions", "docs/architecture/decisions", "adr", "doc/adr")
AUTHORITIES = {"instruction", "accepted", "explicit-input"}
REVIEW_AREAS = {
    "decisions", "schema", "plan-effects", "privilege", "policy", "state-impact", "reversibility",
}
REVIEW_RESULTS = {"pass", "blocked", "insufficient-evidence"}


def _load_files() -> ModuleType:
    """Reuse the sibling's bounded readers under a private, pack-qualified name."""
    name = "iac_terraform_generate_iac_authoring_gate_plan_bundle"
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("plan_bundle.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("local reader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


files = _load_files()


class Refusal(Exception):
    """Carry only fixed codes and an exit class across the command boundary."""

    def __init__(self, code: str, exit_code: int = 1) -> None:
        super().__init__(code)
        self.code = code
        self.exit_code = exit_code


def result_for(codes: list[str], **extra: Any) -> dict[str, Any]:
    """Emit fixed diagnostics without input values or failed locators."""
    return {
        "status": "stop" if codes else "ready",
        "issues": [{"code": code} for code in dict.fromkeys(codes)],
        **extra,
    }


def _parts(locator: str) -> list[str]:
    """Reject unsafe lexical forms before inspecting any filesystem entry."""
    parts = locator.split("/")
    if (
        not locator
        or locator.startswith("/")
        or "\\" in locator
        or re.match(r"^[A-Za-z]:", locator)
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise Refusal("unsafe-path")
    return parts


@contextmanager
def _directory(root: Path, locator: str = "") -> Generator[int, None, None]:
    """Pin directory ancestors and detect replacement during discovery."""
    descriptors: list[int] = []
    entries: list[tuple[int, str, os.stat_result]] = []
    try:
        parts = _parts(locator) if locator else []
        canonical = root.resolve(strict=True)
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise Refusal("unsafe-path")
        current = os.open(canonical.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(current)
        for part in [*canonical.parts[1:], *parts]:
            before = os.stat(part, dir_fd=current, follow_symlinks=False)
            if (
                not stat.S_ISDIR(before.st_mode)
                or getattr(before, "st_file_attributes", 0) & 0x400
            ):
                raise Refusal("unsafe-path")
            opened = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            descriptors.append(opened)
            if files._identity(before) != files._identity(os.fstat(opened)):
                raise Refusal("unsafe-path")
            entries.append((current, part, before))
            current = opened
        yield current
        try:
            for parent, name, before in entries:
                if files._identity(before) != files._identity(
                    os.stat(name, dir_fd=parent, follow_symlinks=False)
                ):
                    raise Refusal("unsafe-path")
            if root.resolve(strict=True) != canonical:
                raise Refusal("unsafe-path")
        except FileNotFoundError as exc:
            raise Refusal("unsafe-path") from exc
    except FileNotFoundError:
        raise
    except (OSError, ValueError, RuntimeError) as exc:
        raise Refusal("unsafe-path") from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def read_file(root: Path, locator: str, limit: int = SOURCE_LIMIT) -> bytes:
    """Refuse unsafe or oversized files before a bounded descriptor read."""
    opened_file = False
    try:
        with files.confined_file(root, locator) as fd:
            opened_file = True
            if os.fstat(fd).st_size > limit:
                raise Refusal("source-too-large")
            chunks: list[bytes] = []
            remaining = limit + 1
            while remaining:
                chunk = os.read(fd, min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        if len(raw) > limit:
            raise Refusal("source-too-large")
        return raw
    except files.Refusal as exc:
        if not opened_file and (
            exc.code == "missing-evidence" or isinstance(exc.__cause__, PermissionError)
        ):
            raise Refusal("unreadable-input", 2) from exc
        raise Refusal("unsafe-path") from exc


def hash_file(root: Path, locator: str, limit: int) -> str:
    """Stream a confined artifact with size and descriptor-identity checks."""
    opened_file = False
    digest = hashlib.sha256()
    try:
        with files.confined_file(root, locator) as fd:
            opened_file = True
            if os.fstat(fd).st_size > limit:
                raise Refusal("source-too-large")
            remaining = limit + 1
            while remaining:
                chunk = os.read(fd, min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                if not remaining:
                    raise Refusal("source-too-large")
                digest.update(chunk)
        return digest.hexdigest()
    except files.Refusal as exc:
        if not opened_file and (
            exc.code == "missing-evidence" or isinstance(exc.__cause__, PermissionError)
        ):
            raise Refusal("unreadable-input", 2) from exc
        raise Refusal("unsafe-path") from exc


def _record(value: Any, required: set[str], optional: set[str] | None = None) -> bool:
    """Check a closed record without trusting JSON field names or values."""
    return isinstance(value, dict) and required <= value.keys() <= required | (optional or set())


def _strings(value: dict[str, Any], names: set[str]) -> bool:
    """Require nonempty string fields."""
    return all(isinstance(value.get(name), str) and bool(value[name]) for name in names)


def _unique(records: list[dict[str, Any]]) -> bool:
    """Reject duplicate identifiers before building any authority lookup."""
    return len({item["id"] for item in records}) == len(records)


def _summary_shape(value: Any) -> bool:
    """Validate structure first so duplicate ids cannot disguise a conflict."""
    fields = {"sources", "constraints", "unresolved", "integrations"}
    if not _record(value, fields) or any(not isinstance(value[k], list) for k in fields):
        return False
    for source in value["sources"]:
        required = {"id", "path", "sha256", "authority"}
        if not _record(source, required, {"status_line"}) or not _strings(source, required):
            return False
        if "status_line" in source and not isinstance(source["status_line"], str):
            return False
        if not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", source["sha256"]):
            return False
    for constraint in value["constraints"]:
        required = {"id", "topic", "requirement", "source"}
        if not _record(constraint, required) or not _strings(constraint, required):
            return False
    for integration in value["integrations"]:
        if (
            not _record(integration, {"name", "status"})
            or not _strings(integration, {"name", "status"})
            or integration["status"] not in ("used", "refused", "unavailable")
        ):
            return False
    return _unique(value["sources"]) and _unique(value["constraints"])


def _accepted(source: dict[str, Any], raw: bytes) -> bool:
    """Verify a verbatim status line and normalize its list and emphasis marks."""
    line = source.get("status_line")
    if not line or "\n" in line or "\r" in line:
        return False
    try:
        if line.encode("utf-8") not in raw.splitlines():
            return False
    except UnicodeError:
        return False
    normalized = line.lstrip(" \t*-_>#").replace("*", "").replace("_", "").strip()
    normalized = re.sub(r"^status\s*:\s*", "", normalized, flags=re.IGNORECASE)
    return normalized.casefold().startswith("accepted")


def check_summary(raw: bytes, root: Path) -> dict[str, Any]:
    """Check summary authority, exact byte identity and recorded stop conditions."""
    try:
        value = files.parse_json(raw)
    except files.Refusal:
        return result_for(["malformed-summary"])
    if not _summary_shape(value):
        return result_for(["malformed-summary"])
    issues: list[str] = []
    if not value["sources"]:
        issues.append("no-governing-source")
    sources = {source["id"]: source for source in value["sources"]}
    for source in value["sources"]:
        try:
            content = read_file(root, source["path"])
        except Refusal as exc:
            issues.append("unsafe-path" if exc.code == "unreadable-input" else exc.code)
            continue
        if hashlib.sha256(content).hexdigest() != source["sha256"].removeprefix("sha256:"):
            issues.append("source-changed")
        if source["authority"] == "accepted" and not _accepted(source, content):
            issues.append("authority-unverified")
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for constraint in value["constraints"]:
        source = sources.get(constraint["source"])
        if source is None or source["authority"] not in AUTHORITIES:
            issues.append("non-authoritative-source")
        for previous in by_topic.get(constraint["topic"], []):
            if (
                previous["source"] != constraint["source"]
                and previous["requirement"] != constraint["requirement"]
            ):
                issues.append("conflict")
        by_topic.setdefault(constraint["topic"], []).append(constraint)
    if value["unresolved"]:
        issues.append("unresolved-issue")
    if any(item["status"] == "refused" for item in value["integrations"]):
        issues.append("integration-refused")
    return result_for(issues)


def _review_shape(value: Any) -> bool:
    """Validate the closed review record before any evidence resolution."""
    if not _record(value, {"subject", "rubric", "reviewers", "evidence", "areas", "result"}):
        return False
    if not isinstance(value["result"], str) or value["result"] not in REVIEW_RESULTS:
        return False
    for name in ("reviewers", "evidence", "areas"):
        if not isinstance(value[name], list):
            return False
    for items, fields in (
        ([value["subject"], value["rubric"]], {"id", "sha256"}),
        (value["evidence"], {"id", "path", "sha256"}),
    ):
        for item in items:
            if not _record(item, fields) or not _strings(item, fields):
                return False
            if not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", item["sha256"]):
                return False
    for reviewer in value["reviewers"]:
        if (
            not _record(reviewer, {"id", "kind"})
            or not _strings(reviewer, {"id", "kind"})
            or reviewer["kind"] not in ("local", "core-agent")
        ):
            return False
    findings: list[dict[str, Any]] = []
    for area in value["areas"]:
        if (
            not _record(area, {"area", "coverage", "evidence", "findings"})
            or not _strings(area, {"area", "coverage"})
            or area["area"] not in REVIEW_AREAS
            or area["coverage"] not in ("covered", "gap")
            or not isinstance(area["evidence"], list)
            or any(not isinstance(item, str) or not item for item in area["evidence"])
            or not isinstance(area["findings"], list)
        ):
            return False
        for finding in area["findings"]:
            fields = {"id", "severity", "status"}
            if (
                not _record(finding, fields)
                or not _strings(finding, fields)
                or finding["severity"] not in ("blocker", "concern", "nit")
                or finding["status"] not in ("open", "resolved")
            ):
                return False
            findings.append(finding)
    return (
        all(_unique(value[name]) for name in ("reviewers", "evidence"))
        and _unique(findings)
        and len({area["area"] for area in value["areas"]}) == len(value["areas"])
    )


def check_review(raw: bytes, root: Path, saved_plan: str, checklist: str) -> dict[str, Any]:
    """Derive local coverage and blocker status, binding exact artifact bytes."""
    try:
        value = files.parse_json(raw)
    except files.Refusal:
        return result_for(["malformed-record"], status="insufficient-evidence")
    if not _review_shape(value):
        return result_for(["malformed-record"], status="insufficient-evidence")
    issues: list[str] = []
    for name, locator, code in (
        ("subject", saved_plan, "subject-mismatch"),
        ("rubric", checklist, "stale-rubric"),
    ):
        actual = (
            hash_file(root, locator, EVIDENCE_LIMIT)
            if name == "subject" else hashlib.sha256(read_file(root, locator)).hexdigest()
        )
        if actual != value[name]["sha256"].removeprefix("sha256:"):
            issues.append(code)
    verified: set[str] = set()
    for evidence in value["evidence"]:
        try:
            actual = hash_file(root, evidence["path"], EVIDENCE_LIMIT)
        except Refusal as exc:
            if exc.code != "unreadable-input":
                issues.append(exc.code)
            continue
        if actual == evidence["sha256"].removeprefix("sha256:"):
            verified.add(evidence["id"])
    incomplete = {area["area"] for area in value["areas"]} != REVIEW_AREAS
    blocker = False
    for area in value["areas"]:
        if area["coverage"] == "gap":
            incomplete = True
        elif not area["evidence"] or not verified.issuperset(area["evidence"]):
            incomplete = True
            issues.append("unresolved-evidence")
        blocker |= any(
            finding["severity"] == "blocker" and finding["status"] == "open"
            for finding in area["findings"]
        )
    derived = "insufficient-evidence" if incomplete else "blocked" if blocker else "pass"
    if value["result"] != derived:
        issues.append("result-mismatch")
    return result_for(issues, status=derived)


def _target_instructions(root: Path, target: str) -> list[str]:
    """Confine existing ancestors and select instructions for planned outputs."""
    parts = _parts(target)
    for index in range(1, len(parts) + 1):
        locator = "/".join(parts[:index])
        try:
            with _directory(root, "/".join(parts[: index - 1])) as parent:
                info = os.stat(parts[index - 1], dir_fd=parent, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if index == len(parts):
                        raise Refusal("unsafe-path")
                    # Pin each existing ancestor before selecting its instructions.
                    with _directory(root, locator):
                        pass
                elif index == len(parts):
                    with files.confined_file(root, locator) as fd:
                        if os.fstat(fd).st_size > SOURCE_LIMIT:
                            raise Refusal("source-too-large")
                else:
                    raise Refusal("unsafe-path")
        except FileNotFoundError:
            break
        except files.Refusal as exc:
            raise Refusal("unsafe-path") from exc
    return ["AGENTS.md", *("/".join([*parts[:i], "AGENTS.md"]) for i in range(1, len(parts)))]


def discover(root: Path, targets: list[str]) -> dict[str, Any]:
    """List bounded candidates without following links or interpreting text."""
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(locator: str) -> None:
        """Read one candidate and spend one unit of the file budget."""
        if locator in seen:
            return
        if len(sources) >= FILE_LIMIT:
            raise Refusal("file-limit")
        seen.add(locator)
        raw = read_file(root, locator)
        sources.append({
            "path": locator,
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
        })

    def walk(locator: str) -> None:
        """Traverse pinned directories and fail on every unsafe entry."""
        with _directory(root, locator) as directory:
            for name in sorted(os.listdir(directory)):  # noqa: PTH208 — pinned descriptor traversal
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                child = locator + "/" + name
                if stat.S_ISDIR(info.st_mode):
                    walk(child)
                else:
                    add(child)

    try:
        # Validate the root even in an empty repository.
        with _directory(root):
            pass
        instructions = {"AGENTS.md"}
        for target in targets:
            instructions.update(_target_instructions(root, target))
        for locator in sorted(instructions):
            try:
                with _directory(
                    root, str(Path(locator).parent) if "/" in locator else ""
                ) as directory:
                    os.stat(Path(locator).name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            add(locator)
        for locator in DECISION_DIRS:
            try:
                with _directory(root, locator):
                    pass
            except FileNotFoundError:
                continue
            walk(locator)
    except (Refusal, files.Refusal) as exc:
        code = "unsafe-path" if exc.code in ("unreadable-input", "missing-evidence") else exc.code
        return result_for([code], sources=[])
    except (OSError, ValueError, RuntimeError, RecursionError):
        return result_for(["unsafe-path"], sources=[])
    return result_for([], sources=sources)


class SafeParser(argparse.ArgumentParser):
    """Prevent argparse from printing untrusted arguments."""

    def error(self, message: str) -> Any:
        """Replace variable usage messages with a fixed code."""
        raise Refusal("usage", 2)


def main(argv: list[str] | None = None) -> int:
    """Dispatch governance checks and emit exactly one safe UTF-8 JSON result."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = SafeParser(add_help=False)
    commands = parser.add_subparsers(dest="command", required=True)
    discovery = commands.add_parser("discover", add_help=False)
    discovery.add_argument("--root", required=True)
    discovery.add_argument("--target", nargs="+", action="extend", default=[])
    summary = commands.add_parser("check-summary", add_help=False)
    summary.add_argument("summary")
    summary.add_argument("--root", required=True)
    review = commands.add_parser("check-review", add_help=False)
    review.add_argument("record")
    review.add_argument("--root", required=True)
    review.add_argument("--saved-plan", required=True)
    review.add_argument("--checklist", required=True)
    exit_code = 1
    try:
        args = parser.parse_args(argv)
        root = Path(args.root)
        if args.command == "discover":
            result = discover(root, args.target)
        else:
            is_review = args.command == "check-review"
            try:
                raw = read_file(root, args.record if is_review else args.summary, SUMMARY_LIMIT)
            except Refusal as exc:
                if exc.code != "source-too-large":
                    raise
                result = result_for(
                    ["malformed-record" if is_review else "malformed-summary", "source-too-large"],
                    **({"status": "insufficient-evidence"} if is_review else {}),
                )
            else:
                result = (
                    check_review(raw, root, args.saved_plan, args.checklist)
                    if is_review else check_summary(raw, root)
                )
        if result["status"] in ("ready", "pass") and not result["issues"]:
            exit_code = 0
    except Refusal as exc:
        result = result_for([exc.code])
        exit_code = exc.exit_code
    except (OSError, ValueError, RuntimeError):
        result = result_for(["unreadable-input"])
        exit_code = 2
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
