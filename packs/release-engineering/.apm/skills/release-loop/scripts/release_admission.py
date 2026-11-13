#!/usr/bin/env python3
"""Pin validated release candidates without granting execution authority."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any


def load_validator() -> ModuleType:
    """Load the trusted sibling validator without adding an import search path."""
    path = Path(__file__).resolve().with_name("release_handoff.py")
    spec = importlib.util.spec_from_file_location(
        "release_engineering_release_loop_admission_handoff", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("validator unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handoff = load_validator()
Refusal = handoff.Refusal
# Keep one confinement implementation for candidate, policy, record and evidence.
confined_file = handoff.confined_file


def bounded_chunks(root: Path, locator: str, limit: int) -> Generator[bytes, None, None]:
    """Check descriptor size before reading and detect growth and replacement."""
    with confined_file(root, locator) as descriptor:
        if os.fstat(descriptor).st_size > limit:
            raise Refusal("input-too-large", "error")
        count = 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            if count > limit:
                raise Refusal("input-too-large", "error")
            yield chunk


def read_manifest(root: Path, locator: str) -> bytes:
    """Read bounded manifest, policy or internal-record bytes through confinement."""
    try:
        return b"".join(bounded_chunks(root, locator, handoff.MANIFEST_LIMIT))
    except handoff.Refusal:
        raise Refusal("unreadable-input", "error") from None


def hash_evidence(root: Path, locator: str) -> str:
    """Stream evidence bytes under the shared evidence budget."""
    digest = hashlib.sha256()
    for chunk in bounded_chunks(root, locator, handoff.EVIDENCE_LIMIT):
        digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def sha256(raw: bytes) -> str:
    """Hash the exact serialized bytes rather than a normalized object."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def fields(value: Any, names: set[str]) -> dict[str, Any]:
    """Require an object with exactly the expected fields."""
    if not isinstance(value, dict) or set(value) != names:
        raise Refusal("record-malformed")
    return value


def text(value: Any, pattern: str | None = None) -> bool:
    """Validate a nonempty bounded string, optionally with a closed grammar."""
    return (
        isinstance(value, str)
        and 0 < len(value) <= 4096
        and (pattern is None or re.fullmatch(pattern, value) is not None)
    )


def read_record(root: Path, locator: str) -> tuple[dict[str, Any], bytes]:
    """Read strictly bounded admission JSON and validate its entire shape."""
    raw = read_manifest(root, locator)
    try:
        record = fields(
            handoff.parse_json(raw),
            {
                "candidate",
                "policy",
                "target",
                "evidence",
                "admitted_at",
                "attempt",
                "max_attempts",
                "replaces",
            },
        )
        for name in ("candidate", "policy"):
            pin = fields(record[name], {"id", "locator", "sha256"})
            if (
                not text(pin["id"], handoff.IDENTIFIER)
                or not text(pin["locator"])
                or not text(pin["sha256"], handoff.DIGEST)
            ):
                raise Refusal("record-malformed")
        target = fields(record["target"], {"environment", "account"})
        if not all(text(value) for value in target.values()):
            raise Refusal("record-malformed")
        if not isinstance(record["evidence"], list) or not record["evidence"]:
            raise Refusal("record-malformed")
        identifiers: set[str] = set()
        for item in record["evidence"]:
            pin = fields(item, {"id", "sha256"})
            if (
                not text(pin["id"], handoff.IDENTIFIER)
                or pin["id"] in identifiers
                or not text(pin["sha256"], handoff.DIGEST)
            ):
                raise Refusal("record-malformed")
            identifiers.add(pin["id"])
        attempt, maximum = record["attempt"], record["max_attempts"]
        if type(attempt) is not int or type(maximum) is not int or not 1 <= attempt <= maximum:
            raise Refusal("record-malformed")
        replaced = record["replaces"]
        if (attempt == 1 and replaced is not None) or (
            attempt > 1 and not text(replaced, handoff.DIGEST)
        ):
            raise Refusal("record-malformed")
        if not text(record["admitted_at"]):
            raise Refusal("record-malformed")
        handoff.utc_time(record["admitted_at"])
        return record, raw
    except handoff.Refusal:
        raise Refusal("record-malformed") from None


def clock_time(now: str | None) -> str:
    """Use an explicit UTC clock, rejecting invalid clock arguments as usage."""
    value = now if now is not None else datetime.now(UTC).isoformat().replace("+00:00", "Z")
    try:
        handoff.utc_time(value)
    except handoff.Refusal:
        raise Refusal("usage", "error") from None
    return value


def evidence_pins(candidate: dict[str, Any], root: Path) -> list[dict[str, str]]:
    """Rehash every local evidence file, refusing unavailable external bytes."""
    pins = []
    for item in candidate["evidence"]:
        value = hash_evidence(root, item["locator"])
        if value != item["sha256"]:
            raise Refusal("evidence-changed")
        pins.append({"id": item["id"], "sha256": value})
    return pins


def admit(
    locator: str,
    *,
    root: Path,
    policy: str | None,
    environment: str,
    account: str | None,
    output: str,
    now: str | None = None,
    max_attempts: int | None = None,
    replaces: str | None = None,
) -> dict[str, Any]:
    """Validate independently, pin exact bytes and publish without overwrite."""
    if max_attempts is not None and (replaces is not None or max_attempts < 1):
        raise Refusal("usage", "error")
    if policy is None:
        raise Refusal("policy-missing")
    clock = clock_time(now)
    raw = read_manifest(root, locator)
    policy_raw = read_manifest(root, policy)
    try:
        trusted = handoff.parse_json(policy_raw)
    except handoff.Refusal:
        raise Refusal("candidate-invalid") from None
    validation = handoff.validate_bytes(raw, root=root, policy=trusted, now=clock)
    if validation["status"] != "valid":
        raise Refusal("candidate-invalid")
    candidate = handoff.parse_yaml(raw)
    if candidate["target"]["environment"] != environment or (
        account is not None and candidate["target"]["account"] != account
    ):
        raise Refusal("target-mismatch")
    attempt, maximum, previous_digest = 1, max_attempts or 3, None
    if replaces is not None:
        try:
            previous, previous_raw = read_record(root, replaces)
        except handoff.Refusal:
            raise Refusal("replaces-invalid") from None
        if previous["candidate"]["sha256"] == sha256(raw):
            raise Refusal("replaces-invalid")
        attempt, maximum = previous["attempt"] + 1, previous["max_attempts"]
        previous_digest = sha256(previous_raw)
        if attempt > maximum:
            raise Refusal("attempt-limit")
    try:
        pins = evidence_pins(candidate, root)
        # Re-read the pinned inputs after validation and hashing, before publication.
        if read_manifest(root, locator) != raw or read_manifest(root, policy) != policy_raw:
            raise Refusal("candidate-invalid")
    except handoff.Refusal:
        raise Refusal("candidate-invalid") from None
    record = {
        "candidate": {"id": candidate["candidate_id"], "locator": locator, "sha256": sha256(raw)},
        "policy": {"id": trusted["id"], "locator": policy, "sha256": sha256(policy_raw)},
        "target": candidate["target"],
        "evidence": pins,
        "admitted_at": clock,
        "attempt": attempt,
        "max_attempts": maximum,
        "replaces": previous_digest,
    }
    try:
        with handoff.output_directory(root, output, locator) as (directory, name, recheck):
            handoff.save_candidate(
                directory,
                name,
                json.dumps(record, ensure_ascii=True).encode("utf-8") + b"\n",
                recheck,
                handoff.write_candidate,
                handoff.publish_candidate,
            )
    except handoff.Refusal as exc:
        if exc.code in ("output-exists", "output-is-input"):
            raise Refusal("exists") from None
        raise
    return {"status": "admitted", "issues": []}


def verify(locator: str, *, root: Path, now: str | None = None) -> dict[str, Any]:
    """Recheck all pinned bytes, target bindings and the trusted freshness policy."""
    clock = clock_time(now)
    record, _ = read_record(root, locator)
    try:
        raw = read_manifest(root, record["candidate"]["locator"])
    except handoff.Refusal:
        raise Refusal("candidate-changed") from None
    if sha256(raw) != record["candidate"]["sha256"]:
        raise Refusal("candidate-changed")
    try:
        policy_raw = read_manifest(root, record["policy"]["locator"])
    except handoff.Refusal:
        raise Refusal("policy-changed") from None
    if sha256(policy_raw) != record["policy"]["sha256"]:
        raise Refusal("policy-changed")
    try:
        candidate = handoff.parse_yaml(raw)
        trusted = handoff.parse_json(policy_raw)
        shape = handoff.Validation()
        shape.record(candidate, "Candidate", "$")
        shape.record(trusted, "Policy", "$.policy")
        if shape.issues:
            raise Refusal("record-malformed")
        if (
            candidate["candidate_id"] != record["candidate"]["id"]
            or trusted["id"] != record["policy"]["id"]
        ):
            raise Refusal("record-malformed")
        if candidate["target"] != record["target"]:
            raise Refusal("target-changed")
        try:
            pins = evidence_pins(candidate, root)
        except handoff.Refusal:
            raise Refusal("evidence-changed") from None
        if pins != record["evidence"]:
            raise Refusal("evidence-changed")
        if handoff.utc_time(record["admitted_at"]) > handoff.utc_time(clock):
            raise Refusal("stale")
        validation = handoff.validate_bytes(raw, root=root, policy=trusted, now=clock)
        if validation["status"] != "valid":
            codes = {issue["code"] for issue in validation["issues"]}
            if codes.intersection({"stale", "future-time"}):
                raise Refusal("stale")
            raise Refusal("record-malformed")
    except (KeyError, TypeError):
        raise Refusal("record-malformed") from None
    return {"status": "current", "issues": []}


# These closed identifiers select coverage; the role references own the checklists.
REVIEW_AREAS = {
    "reliability": {
        "ordering",
        "partial-failure",
        "mixed-versions",
        "runtime-health",
        "rollback",
        "cost",
        "cleanup",
    },
    "security": {"provenance", "identity-permissions", "exposure", "secrets", "trust-boundaries"},
}


def review_shape(value: Any) -> dict[str, Any]:
    """Validate closed review fields before resolving any caller-supplied locator."""
    record = fields(
        value,
        {
            "subject",
            "stage",
            "target",
            "rubric",
            "reviewer",
            "permissions_digest",
            "evidence",
            "areas",
            "result",
        },
    )
    for name, names in (
        ("subject", {"id", "sha256"}),
        ("target", {"environment", "account"}),
        ("rubric", {"id", "role", "sha256"}),
        ("reviewer", {"id", "kind"}),
    ):
        item = fields(record[name], names)
        if not all(
            text(
                field,
                handoff.DIGEST if key == "sha256" else handoff.IDENTIFIER if key == "id" else None,
            )
            for key, field in item.items()
        ):
            raise Refusal("malformed-record")
    if (
        record["rubric"]["role"] not in REVIEW_AREAS
        or record["reviewer"]["kind"] not in ("local", "core-agent")
        or record["stage"] not in ("pre-deploy", "post-deploy", "recovery", "final")
        or record["result"] not in ("pass", "blocked", "insufficient-evidence")
        or not text(record["permissions_digest"], handoff.DIGEST)
        or not isinstance(record["evidence"], list)
        or not isinstance(record["areas"], list)
    ):
        raise Refusal("malformed-record")
    identifiers: set[str] = set()
    for evidence in record["evidence"]:
        item = fields(evidence, {"id", "kind", "path", "sha256", "observed_at"})
        if (
            not all(
                text(
                    field,
                    handoff.DIGEST
                    if key == "sha256"
                    else handoff.IDENTIFIER
                    if key == "id"
                    else None,
                )
                for key, field in item.items()
            )
            or item["id"] in identifiers
        ):
            raise Refusal("malformed-record")
        identifiers.add(item["id"])
        handoff.utc_time(item["observed_at"])
    finding_ids: set[str] = set()
    for area in record["areas"]:
        item = fields(area, {"area", "coverage", "evidence", "findings"})
        if (
            not text(item["area"], handoff.IDENTIFIER)
            or item["coverage"] not in ("covered", "gap")
            or not isinstance(item["evidence"], list)
            or not all(text(ref, handoff.IDENTIFIER) for ref in item["evidence"])
            or len(set(item["evidence"])) != len(item["evidence"])
            or not isinstance(item["findings"], list)
        ):
            raise Refusal("malformed-record")
        for finding in item["findings"]:
            pin = fields(finding, {"id", "severity", "status"})
            if (
                not text(pin["id"], handoff.IDENTIFIER)
                or pin["id"] in finding_ids
                or pin["severity"] not in ("blocker", "concern", "nit")
                or pin["status"] not in ("open", "resolved")
            ):
                raise Refusal("malformed-record")
            finding_ids.add(pin["id"])
    return record


def check_review(
    locator: str, *, root: Path, admission: str, rubric: str, now: str | None = None
) -> dict[str, Any]:
    """Derive coverage and blocker results and bind them to a current admission."""
    try:
        record = review_shape(handoff.parse_json(read_manifest(root, locator)))
    except handoff.Refusal:
        return {"status": "insufficient-evidence", "issues": [{"code": "malformed-record"}]}
    issues: list[str] = []
    try:
        verify(admission, root=root, now=now)
        admitted, _ = read_record(root, admission)
    except handoff.Refusal:
        issues.append("admission-stale")
    else:
        if record["subject"] != {key: admitted["candidate"][key] for key in ("id", "sha256")}:
            issues.append("subject-mismatch")
        if record["target"] != admitted["target"]:
            issues.append("target-mismatch")
    try:
        if sha256(read_manifest(root, rubric)) != record["rubric"]["sha256"]:
            issues.append("stale-rubric")
    except handoff.Refusal:
        issues.append("stale-rubric")
    verified: set[str] = set()
    for evidence in record["evidence"]:
        try:
            if hash_evidence(root, evidence["path"]) == evidence["sha256"]:
                verified.add(evidence["id"])
        except handoff.Refusal:
            pass
    areas = record["areas"]
    names = [area["area"] for area in areas]
    incomplete = set(names) != REVIEW_AREAS[record["rubric"]["role"]] or len(names) != len(
        set(names)
    )
    blocker = False
    for area in areas:
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
    if record["result"] != derived:
        issues.append("result-mismatch")
    # Binding refusals cannot leave a passing status usable by a later stage.
    status = "insufficient-evidence" if issues and derived == "pass" else derived
    return {"status": status, "issues": [{"code": code} for code in dict.fromkeys(issues)]}


def main(argv: list[str] | None = None) -> int:
    """Dispatch extensible subcommands and emit one redacted UTF-8 JSON object."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = handoff.SafeParser(add_help=False)
    commands = parser.add_subparsers(dest="command", required=True)
    admission = commands.add_parser("admit", add_help=False)
    verification = commands.add_parser("verify", add_help=False)
    review = commands.add_parser("check-review", add_help=False)
    review.add_argument("--admission", required=True)
    review.add_argument("--rubric", required=True)
    for command in (admission, verification, review):
        command.add_argument("input")
        command.add_argument("--root", required=True)
        command.add_argument("--now")
    admission.add_argument("--policy")
    admission.add_argument("--expect-environment", required=True)
    admission.add_argument("--expect-account")
    admission.add_argument("--output", required=True)
    attempts = admission.add_mutually_exclusive_group()
    attempts.add_argument("--max-attempts", type=int)
    attempts.add_argument("--replaces")
    try:
        args = parser.parse_args(argv)
        if args.command == "admit":
            result = admit(
                args.input,
                root=Path(args.root),
                policy=args.policy,
                environment=args.expect_environment,
                account=args.expect_account,
                output=args.output,
                now=args.now,
                max_attempts=args.max_attempts,
                replaces=args.replaces,
            )
        elif args.command == "check-review":
            result = check_review(
                args.input,
                root=Path(args.root),
                admission=args.admission,
                rubric=args.rubric,
                now=args.now,
            )
        else:
            result = verify(args.input, root=Path(args.root), now=args.now)
    except handoff.Refusal as exc:
        result = {
            "status": "error" if exc.status == "error" else "refused",
            "issues": [{"code": exc.code}],
        }
    except (OSError, ValueError, RuntimeError):
        result = {"status": "error", "issues": [{"code": "unreadable-input"}]}
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return (
        0
        if result["status"] in ("admitted", "current", "pass")
        else (2 if result["status"] == "error" else 1)
    )


if __name__ == "__main__":
    sys.exit(main())
