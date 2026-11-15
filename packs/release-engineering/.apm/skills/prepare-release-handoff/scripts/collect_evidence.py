#!/usr/bin/env python3
"""Assemble existing release evidence without executing work or granting authority."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

VALIDATOR = Path(__file__).resolve().parents[2] / "release-loop/scripts/release_handoff.py"
PLACEHOLDER = "sha256:" + "0" * 64
ACTIONS = {
    "missing-evidence": "produce-evidence",
    "digest-mismatch": "reconcile-digest",
    "unverified-external": "supply-digest",
    "check-not-run": "run-check",
    "check-failed": "repair-and-rebuild",
    "missing-provenance": "produce-evidence",
    "missing-target": "supply-target",
    "unsupported-component": "route-to-owner",
}


class UsageError(Exception):
    """Suppress untrusted argument text in usage errors."""


class SafeParser(argparse.ArgumentParser):
    """Parse arguments without printing caller-controlled diagnostics."""

    def error(self, message: str) -> Any:
        """Report a fixed usage error instead of echoing arguments."""
        raise UsageError


def load_validator() -> ModuleType | None:
    """Load only the installed sibling implementation, never request-supplied code."""
    spec = importlib.util.spec_from_file_location(
        "release_engineering_prepare_release_handoff_validator", VALIDATOR
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except (OSError, ImportError):
        sys.modules.pop(spec.name, None)
        return None
    return module


def gap(code: str, path: str = "$", action: str = "fix-candidate") -> dict[str, str]:
    """Return a diagnostic containing field paths, never input values or locators."""
    return {"code": code, "path": path, "next_action": action}


def chunks(handoff: ModuleType, root: Path, locator: str, limit: int) -> Iterator[bytes]:
    """Check size before streaming bounded bytes through the shared confinement gate."""
    with handoff.confined_file(root, locator) as descriptor:
        if os.fstat(descriptor).st_size > limit:
            raise handoff.Refusal("input-too-large", "error")
        count = 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            if count > limit:
                raise handoff.Refusal("input-too-large", "error")
            yield chunk


def read_json(handoff: ModuleType, root: Path, locator: str) -> Any:
    """Strictly decode a bounded, confined request or trusted policy."""
    return handoff.parse_json(b"".join(chunks(handoff, root, locator, handoff.MANIFEST_LIMIT)))


def request_shape(handoff: ModuleType, request: Any) -> None:
    """Validate request types with missing computed digests allowed temporarily."""
    # Validate a copy so supplied digests remain available for reconciliation.
    try:
        shape = json.loads(json.dumps(request))
    except (TypeError, ValueError, RecursionError):
        raise handoff.Refusal("request-malformed", "error") from None
    if isinstance(shape, dict):
        evidence = shape.get("evidence", [])
        checks = shape.get("checks", [])
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict):
                    item.setdefault("sha256", PLACEHOLDER)
        for records in (evidence, checks):
            if isinstance(records, list):
                for item in records:
                    if isinstance(item, dict) and isinstance(item.get("subjects"), list):
                        for subject in item["subjects"]:
                            if isinstance(subject, dict):
                                subject.setdefault("sha256", PLACEHOLDER)
    validation = handoff.Validation()
    validation.record(shape, "Candidate", "$")
    if validation.status in ("invalid", "error"):
        raise handoff.Refusal("request-malformed", "error")


def assemble(handoff: ModuleType, request: dict[str, Any], root: Path,
             policy: dict[str, Any]) -> list[dict[str, str]]:
    """Compute omitted digests and report collection-specific gaps without fixing work."""
    gaps: list[dict[str, str]] = []

    def add(code: str, path: str) -> None:
        """Add a collection gap with its fixed next action."""
        gaps.append(gap(code, path, ACTIONS[code]))

    evidence = request.get("evidence", [])
    by_id = {item["id"]: item for item in evidence if "id" in item}
    for index, item in enumerate(evidence):
        path = f"$.evidence[{index}]"
        locator = item.get("locator")
        if locator is None:
            add("missing-evidence", path + ".locator")
            continue
        try:
            if handoff.external_locator(locator):
                if "sha256" not in item:
                    add("unverified-external", path + ".sha256")
                continue
            digest = hashlib.sha256()
            for chunk in chunks(handoff, root, locator, handoff.EVIDENCE_LIMIT):
                digest.update(chunk)
            computed = "sha256:" + digest.hexdigest()
            if "sha256" in item and item["sha256"] != computed:
                add("digest-mismatch", path + ".sha256")
            item["sha256"] = computed
        except handoff.Refusal:
            add("missing-evidence", path + ".locator")

    evidence_digests = {identifier: item["sha256"] for identifier, item in by_id.items()
                        if "sha256" in item}
    component_digests: dict[str, str] = {}
    for index, component in enumerate(request.get("components", [])):
        path = f"$.components[{index}]"
        kind = component.get("kind")
        if kind not in ("oci-image", "terraform-plan"):
            add("unsupported-component", path + ".kind")
            continue
        key = "artifact" if kind == "oci-image" else "plan_bundle"
        identifier = component.get(key)
        if identifier not in by_id:
            add("missing-evidence", path + "." + key)
        if identifier in evidence_digests and "id" in component:
            component_digests[component["id"]] = evidence_digests[identifier]

    identities = {**evidence_digests, **component_digests}
    for group in ("evidence", "checks"):
        for index, record in enumerate(request.get(group, [])):
            for subject in record.get("subjects", []):
                if "sha256" not in subject and subject.get("id") in identities:
                    subject["sha256"] = identities[subject["id"]]
            if group == "checks":
                path = f"$.checks[{index}]"
                status = record.get("status")
                if status == "fail":
                    add("check-failed", path + ".status")
                elif status == "not-run" and any(
                    required["id"] == record.get("id") for required in policy["required_checks"]
                ):
                    add("check-not-run", path + ".status")
                for ref_index, identifier in enumerate(record.get("evidence", [])):
                    if identifier not in by_id:
                        add("missing-evidence", f"{path}.evidence[{ref_index}]")

    provenance: set[tuple[str, str]] = set()
    for index, identifier in enumerate(request.get("provenance", [])):
        if identifier not in by_id:
            add("missing-evidence", f"$.provenance[{index}]")
        else:
            provenance.update((subject.get("id"), subject.get("sha256"))
                              for subject in by_id[identifier].get("subjects", [])
                              if "id" in subject and "sha256" in subject)
    for index, component in enumerate(request.get("components", [])):
        identifier = component.get("id")
        if (identifier in component_digests
                and (identifier, component_digests[identifier]) not in provenance):
            add("missing-provenance", f"$.components[{index}]")
    target = request.get("target", {})
    for name in ("environment", "account"):
        if not target.get(name):
            add("missing-target", "$.target." + name)
    return gaps


def collect(request: str, *, root: Path, policy: str, output: str,
            now: str | None = None) -> dict[str, Any]:
    """Write a candidate only after collection and trusted validation both succeed."""
    handoff = load_validator()
    if handoff is None:
        return {"status": "incomplete", "gaps": [
            gap("validator-unavailable", action="install-validator")]}
    try:
        data = read_json(handoff, root, request)
        request_shape(handoff, data)
        trusted = read_json(handoff, root, policy)
        validation = handoff.Validation()
        validation.record(trusted, "Policy", "$.policy")
        if validation.issues:
            raise handoff.Refusal("policy-malformed", "error")
        gaps = assemble(handoff, data, root, trusted)
        raw = handoff.yaml_bytes(data)
        checked = handoff.validate_bytes(raw, root=root, policy=trusted, now=now)
        for issue in checked["issues"]:
            action = "fix-candidate"
            if (
                issue["code"] == "missing-evidence"
                and issue["path"].startswith("$.phases[")
                and issue["path"].endswith(".procedures")
            ):
                action = ACTIONS["missing-evidence"]
            gaps.append(gap(issue["code"], issue["path"], action))
        if gaps or checked["status"] != "valid":
            return {"status": "incomplete", "gaps": gaps}
        with handoff.output_directory(root, output, request) as (directory, name, recheck):
            handoff.save_candidate(directory, name, raw, recheck,
                                   handoff.write_candidate, handoff.publish_candidate)
        return {"status": "ready", "gaps": []}
    except handoff.Refusal as exc:
        return {"status": "error", "gaps": [gap(exc.code)]}
    except (OSError, ValueError, RuntimeError):
        return {"status": "error", "gaps": [gap("unreadable-input")]}


def main(argv: list[str] | None = None) -> int:
    """Emit one UTF-8 JSON result with success, gap or error exit status."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = SafeParser(add_help=False)
    parser.add_argument("command", choices=["collect"])
    parser.add_argument("request")
    parser.add_argument("--root", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--now")
    try:
        args = parser.parse_args(argv)
        result = collect(args.request, root=Path(args.root), policy=args.policy,
                         output=args.output, now=args.now)
    except UsageError:
        result = {"status": "error", "gaps": [gap("usage")]}
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return {"ready": 0, "incomplete": 1, "error": 2}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
