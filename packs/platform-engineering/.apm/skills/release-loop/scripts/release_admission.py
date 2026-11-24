#!/usr/bin/env python3
"""Pin validated release candidates without granting execution authority."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import unquote, urlsplit


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


def validate_record(raw: bytes) -> dict[str, Any]:
    """Apply the same serialized admission limits before publication and on read."""
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
        return record
    except handoff.Refusal:
        raise Refusal("record-malformed") from None


def read_record(root: Path, locator: str) -> tuple[dict[str, Any], bytes]:
    """Read confined admission bytes and validate their entire shape."""
    raw = read_manifest(root, locator)
    return validate_record(raw), raw


def clock_time(now: str | None) -> str:
    """Use an explicit UTC clock, rejecting invalid clock arguments as usage."""
    value = now if now is not None else datetime.now(UTC).isoformat().replace("+00:00", "Z")
    try:
        handoff.utc_time(value)
    except handoff.Refusal:
        raise Refusal("usage", "error") from None
    return value


def evidence_pins(candidate: dict[str, Any], root: Path) -> list[dict[str, str]]:
    """Rehash local evidence and retain supplied external digests without fetching."""
    pins = []
    for item in candidate["evidence"]:
        value = (
            item["sha256"] if handoff.external_locator(item["locator"])
            else hash_evidence(root, item["locator"])
        )
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
        "target": {name: candidate["target"][name] for name in ("environment", "account")},
        "evidence": pins,
        "admitted_at": clock,
        "attempt": attempt,
        "max_attempts": maximum,
        "replaces": previous_digest,
    }
    record_raw = json.dumps(record, ensure_ascii=True).encode("utf-8") + b"\n"
    try:
        validate_record(record_raw)
    except handoff.Refusal:
        raise Refusal("candidate-invalid") from None
    try:
        with handoff.output_directory(root, output, locator) as (directory, name, recheck):
            handoff.save_candidate(
                directory,
                name,
                record_raw,
                recheck,
                handoff.write_candidate,
                handoff.publish_candidate,
            )
    except handoff.Refusal as exc:
        if exc.code in ("output-exists", "output-is-input"):
            raise Refusal("exists") from None
        raise
    return {"status": "admitted", "issues": []}


def verified_admission(
    locator: str, *, root: Path, now: str | None = None
) -> tuple[dict[str, Any], bytes]:
    """Check admission pins, target and freshness and retain the exact source bytes."""
    clock = clock_time(now)
    record, record_raw = read_record(root, locator)
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
        if any(candidate["target"][name] != value for name, value in record["target"].items()):
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
    return record, record_raw


def load_verified_admission(
    locator: str, *, root: Path, now: str | None = None
) -> dict[str, Any]:
    """Return only the checked snapshot, refusing replacement during verification."""
    record, raw = verified_admission(locator, root=root, now=now)
    if read_manifest(root, locator) != raw:
        raise Refusal("record-malformed")
    return record


def verify(locator: str, *, root: Path, now: str | None = None) -> dict[str, Any]:
    """Report freshness without exposing the verified admission snapshot."""
    load_verified_admission(locator, root=root, now=now)
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
    locator: str, *, root: Path, admission: str, rubric: str | None, now: str | None = None
) -> dict[str, Any]:
    """Derive coverage and blocker results and bind them to a current admission."""
    try:
        record = review_shape(handoff.parse_json(read_manifest(root, locator)))
    except handoff.Refusal:
        return {"status": "insufficient-evidence", "issues": [{"code": "malformed-record"}]}
    return review_result(record, root=root, admission=admission, rubric=rubric, now=now)


def review_result(
    record: dict[str, Any],
    *,
    root: Path,
    admission: str,
    rubric: str | None,
    now: str | None = None,
) -> dict[str, Any]:
    """Check one parsed review snapshot without reopening caller-controlled bytes."""
    issues: list[str] = []
    try:
        admitted = load_verified_admission(admission, root=root, now=now)
    except handoff.Refusal:
        issues.append("admission-stale")
    else:
        if record["subject"] != {key: admitted["candidate"][key] for key in ("id", "sha256")}:
            issues.append("subject-mismatch")
        if record["target"] != admitted["target"]:
            issues.append("target-mismatch")
    try:
        rubric_raw = (
            read_manifest(root, rubric)
            if rubric is not None
            else read_manifest(
                Path(__file__).resolve().parents[1],
                f"references/{record['rubric']['role']}-review.md",
            )
        )
        if sha256(rubric_raw) != record["rubric"]["sha256"]:
            issues.append("stale-rubric")
    except handoff.Refusal:
        issues.append("stale-rubric")
    verified: set[str] = set()
    for evidence in record["evidence"]:
        try:
            if hash_evidence(root, evidence["path"]) == evidence["sha256"]:
                verified.add(evidence["id"])
        except handoff.Refusal as exc:
            if exc.code != "missing-evidence":
                raise
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


# Baseline prerequisites are code, never a caller-controlled policy field.
STAGE_REQUIREMENTS = {
    "admission": (),
    "pre-deploy": ("pre-deploy",),
    "post-deploy": ("pre-deploy", "post-deploy"),
    "recovery": ("pre-deploy", "recovery"),
    "final": ("pre-deploy", "post-deploy", "final"),
}
STAGE_PROGRESSION = {
    "admission": "preparation",
    "pre-deploy": "execution-eligible",
    "post-deploy": "evaluation-or-recovery",
    "recovery": "authorized-recovery-or-pause",
    "final": "human-decision-required",
}
STAGE_ORDER = {stage: index for index, stage in enumerate(STAGE_REQUIREMENTS)}
RUNTIME_KINDS = {"telemetry", "health-check", "config-snapshot", "exposure-scan"}


def cited_evidence(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Select evidence actually cited by the review's coverage areas."""
    cited = {ref for area in record["areas"] for ref in area["evidence"]}
    return [item for item in record["evidence"] if item["id"] in cited]


def circular_evidence(
    record: dict[str, Any], records: dict[str, dict[str, Any]], root: Path,
    record_pins: dict[str, str],
) -> bool:
    """Detect self and forward citations by locator, digest or review bytes."""
    for evidence in record["evidence"]:
        for locator, other in records.items():
            if (
                evidence["path"] == locator
                or evidence["sha256"] == record_pins[locator]
            ) and STAGE_ORDER[other["stage"]] >= STAGE_ORDER[record["stage"]]:
                return True
        # Hash and inspect one snapshot; a second open must not substitute new bytes.
        digest = hashlib.sha256()
        raw = bytearray()
        size = 0
        try:
            for chunk in bounded_chunks(root, evidence["path"], handoff.EVIDENCE_LIMIT):
                digest.update(chunk)
                size += len(chunk)
                if size <= handoff.MANIFEST_LIMIT:
                    raw.extend(chunk)
        except handoff.Refusal:
            raise Refusal("unresolved-evidence") from None
        if "sha256:" + digest.hexdigest() != evidence["sha256"]:
            raise Refusal("unresolved-evidence")
        # Larger documents cannot be valid review records.
        if size > handoff.MANIFEST_LIMIT:
            continue
        # A review not supplied as --review remains a review, not runtime proof.
        try:
            other = review_shape(handoff.parse_json(bytes(raw)))
        except handoff.Refusal:
            continue
        if STAGE_ORDER[other["stage"]] >= STAGE_ORDER[record["stage"]]:
            return True
    return False


def evidence_time(value: str) -> tuple[datetime, Decimal]:
    """Validate UTC evidence time and retain every fractional digit for ordering."""
    whole = handoff.utc_time(value).replace(microsecond=0)
    fraction = value.removesuffix("Z").partition(".")[2]
    return whole, Decimal("0." + (fraction or "0"))


def check_stage(
    stage: str,
    *,
    root: Path,
    admission: str,
    reviews: list[str],
    final: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Check stage history and immutable review baselines without granting authority."""
    if stage not in STAGE_REQUIREMENTS:
        raise Refusal("usage", "error")
    issues: list[str] = []
    try:
        load_verified_admission(admission, root=root, now=now)
    except handoff.Refusal:
        issues.append("reassessment-required")
    records: dict[str, dict[str, Any]] = {}
    record_pins: dict[str, str] = {}
    results: dict[str, dict[str, Any]] = {}
    for locator in reviews:
        try:
            raw = read_manifest(root, locator)
            records[locator] = review_shape(handoff.parse_json(raw))
            record_pins[locator] = sha256(raw)
        except handoff.Refusal:
            issues.append("malformed-record")
            continue
        result = review_result(
            records[locator], root=root, admission=admission, rubric=None, now=now
        )
        results[locator] = result
        # A changed evidence digest also changes the derived verdict; report the
        # byte failure before interpreting that secondary declaration mismatch.
        issues.extend(
            issue["code"]
            for issue in result["issues"]
            if not (
                issue["code"] == "result-mismatch"
                and any(item["code"] == "unresolved-evidence" for item in result["issues"])
            )
        )
    grouped: dict[str, dict[str, list[str]]] = {}
    for locator, record in records.items():
        grouped.setdefault(record["stage"], {}).setdefault(record["rubric"]["role"], []).append(
            locator
        )
    baseline = next(iter(records.values()), None)
    for record in records.values():
        if baseline is not None and any(
            record[key] != baseline[key] for key in ("subject", "target", "permissions_digest")
        ):
            issues.append("reassessment-required")
        if circular_evidence(record, records, root, record_pins):
            issues.append("circular-review")
    # Resolve byte and binding failures before interpreting stage semantics.
    if issues:
        if any(code in issues for code in ("subject-mismatch", "target-mismatch")):
            issues.append("reassessment-required")
        return {"status": "refused", "issues": [{"code": code} for code in dict.fromkeys(issues)]}
    for required in STAGE_REQUIREMENTS[stage]:
        roles = tuple(REVIEW_AREAS)
        if required == "recovery" and not grouped.get(required, {}).get("security"):
            roles = ("reliability",)
        for role in roles:
            matching = grouped.get(required, {}).get(role, [])
            if not matching:
                issues.append("missing-reviewer")
            if len(matching) > 1:
                issues.append("malformed-record")
            if not matching or any(results[item]["status"] != "pass" for item in matching):
                issues.append("skipped-stage")
    pre = [record for record in records.values() if record["stage"] == "pre-deploy"]
    previous = [item for record in pre for item in record["evidence"]]
    latest = max((evidence_time(item["observed_at"]) for item in previous), default=None)
    for record in records.values():
        if record["stage"] == "post-deploy" and stage in ("post-deploy", "final"):
            if not any(
                item["kind"] in RUNTIME_KINDS
                and latest is not None
                and evidence_time(item["observed_at"]) > latest
                and not any(
                    item[key] == earlier[key]
                    for earlier in previous
                    for key in ("path", "sha256")
                )
                for item in cited_evidence(record)
            ):
                issues.append("runtime-evidence-missing")
        elif record["stage"] == "recovery" and not any(
            item["kind"] in RUNTIME_KINDS | {"failure-report"} for item in cited_evidence(record)
        ):
            issues.append("runtime-evidence-missing")
    if stage == "final" or final is not None:
        try:
            summary = handoff.parse_json(read_manifest(root, final)) if final is not None else None
            if (
                not isinstance(summary, dict)
                or not {"budgets", "cleanup", "remaining_risks"}.issubset(summary)
                or summary["cleanup"] == "not-torn-down"
            ):
                issues.append("final-incomplete")
        except handoff.Refusal:
            issues.append("final-incomplete")
    if issues:
        return {"status": "refused", "issues": [{"code": code} for code in dict.fromkeys(issues)]}
    return {
        "status": "pass",
        "progression": STAGE_PROGRESSION[stage],
        "authority_checks_required": True,
        "issues": [],
    }


# Scrub before truncating so a boundary cannot expose part of a recognized value.
EXCERPT_LIMIT = 4096
EXCERPT_COUNT = 20
JSON_HEADER_PATTERN = (
    r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]*){0,2}"
)
SCRUB_PATTERNS = (
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    JSON_HEADER_PATTERN,
    r"[A-Za-z0-9_+/=-]{32,}",
)

CREDENTIAL_WORDS = (
    "password", "passwd", "passphrase", "pwd", "secret", "token", "apikey", "accesskey",
    "credential", "auth", "cookie", "bearer", "privatekey", "session", "signature",
)

CREDENTIAL_QUERY_NAMES = set(CREDENTIAL_WORDS) | {
    "key", "sig", "signature", "apikey", "accesstoken", "auth", "pwd", "secret",
    "token", "password", "passwd", "credential", "session", "cookie", "authorization",
}


def url_credentials(value: str) -> bool:
    """Detect userinfo and credential query or fragment names in URL-like text."""
    # Join only authority spans so whitespace cannot split userinfo before @.
    value = re.sub(
        r"//[^/<>\"'?#]*@",
        lambda match: "".join(c for c in match[0] if not c.isspace() and ord(c) >= 32),
        value,
    )
    candidates = [match[0] for match in re.finditer(r"//[^\s<>\"']*", value)]
    if "@" in value or "%40" in value.casefold():
        candidates.extend(match[0] for match in re.finditer(r"//[^/\s<>\"'?#]*", value))
    for candidate in candidates:
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            return True
        if (parsed.username is not None or parsed.password is not None
                or "@" in unquote(parsed.netloc)):
            return True
        for component in (parsed.query, parsed.fragment):
            for entry in re.split(r"[?&#;]", component):
                name = re.sub(r"[^a-z0-9]", "", entry.split("=", 1)[0].casefold())
                if any(word in name for word in CREDENTIAL_QUERY_NAMES):
                    return True
    return False


def scrub_json_header(match: re.Match[str]) -> str:
    """Remove base64url object-shaped headers, including truncated JSON objects."""
    value = match[0]
    header = value.split(".", 1)[0]
    try:
        decoded = base64.b64decode(
            header + "=" * (-len(header) % 4), altchars=b"-_", validate=True,
        )
        if re.match(rb'\s*\{\s*(?:"|}|$)', decoded):
            return "[redacted]"
    except ValueError:
        pass
    return value


def object_header(match: re.Match[str]) -> bool:
    """Recognize a JWT object header without consuming adjacent punctuation."""
    if "." not in match[0]:
        return False
    header = match[0].split(".", 1)[0]
    try:
        decoded = base64.b64decode(
            header + "=" * (-len(header) % 4), altchars=b"-_", validate=True,
        )
        return isinstance(json.loads(decoded), dict)
    except (ValueError, UnicodeError, RecursionError):
        return False


def normalize_excerpt(value: str) -> str:
    """Decode escapes and remove quoting and non-whitespace control characters."""
    def decode(match: re.Match[str]) -> str:
        """Normalize one escape, percent sequence, quote or continued line."""
        part = match[0]
        if part.startswith("%"):
            result = unquote(part)
        elif part.startswith(chr(92)):
            suffix = part[1:]
            if len(suffix) > 1 and suffix.startswith(("x", "u", "U")):
                point = int(suffix[1:], 16)
                result = chr(point) if point <= 0x10FFFF else part
            else:
                result = "" if suffix in ("\n", "\r\n") else suffix
        else:
            result = ""
        return result.replace('"', "").replace("'", "")

    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", value)
    return re.sub(
        r"\\(?:\r?\n|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.)"
        r"|(?:%[0-9a-fA-F]{2})+|[\"']",
        decode, value,
    )


def scrub_excerpt(raw: bytes, truncated: bool, kind: str = "") -> str:
    """Withhold credential-bearing documents, then scrub shapes and clip benign text."""
    if len(raw) > handoff.EVIDENCE_LIMIT:
        return "[redacted]"
    value = raw.decode("utf-8", errors="replace")
    decoded = value
    scrubbed = value
    remaining = value
    for pass_number in range(5):
        # Conservative field scans also withhold malformed or deeply nested plans.
        plan_fields = set(re.findall(
            r'\b(?:planned_values|resource_changes|prior_state|sensitive_values|'
            r'terraform_version|configuration)\b', decoded,
        ))
        if (
            re.search(r"(?:^|[^a-z])(?:plan|state)(?:$|[^a-z])", kind.lower())
            or plan_fields & {
                "planned_values", "resource_changes", "prior_state", "sensitive_values",
            }
            or {"terraform_version", "configuration"} <= plan_fields
        ):
            return "withheld: sensitive-plan"
        normalized = re.sub(r"[^a-z0-9]", "", decoded.lower())
        # Match substrings after removing shell syntax, without parsing options.
        client_text = re.sub(r"""[$'"\\`{}()\x00-\x1f\x7f-\x9f]""", "", decoded).lower()
        client = any(name in client_text for name in (
            "curl", "wget", "http", "ssh", "scp", "sftp", "psql", "mysql", "aws",
            "gcloud", "kubectl", "helm",
        )) or ("docker" in client_text and "login" in client_text)
        scheme = decoded.find("://")
        if (
            client
            or (scheme >= 0 and "git" in client_text)
            or any(word in normalized for word in CREDENTIAL_WORDS)
            or re.search(r"(?<![\w-])(?:--user(?![\w-])|-u)", decoded)
            or re.search(r"(?i)\bbasic\s+[^\s\"'<>]+", decoded)
            or (scheme >= 0 and "@" in decoded[scheme + 3:])
            or url_credentials(decoded)
            or any(object_header(match) for match in re.finditer(
                r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.(?=[A-Za-z0-9_-])", decoded,
            ))
        ):
            return "[redacted]"
        form = decoded
        for pattern in SCRUB_PATTERNS:
            form = re.sub(
                pattern, scrub_json_header if pattern == JSON_HEADER_PATTERN else "[redacted]",
                form,
            )
        if pass_number == 0:
            scrubbed = form
            remaining = form
        elif form != decoded:
            # Preserve raw shape redactions, but withhold shapes decoding newly reveals.
            for pattern in SCRUB_PATTERNS:
                if re.sub(
                    pattern,
                    scrub_json_header if pattern == JSON_HEADER_PATTERN else "[redacted]",
                    remaining,
                ) != remaining:
                    return "[redacted]"
        if pass_number == 4:
            return "[redacted]"
        following = normalize_excerpt(decoded)
        if following == decoded:
            break
        remaining = following if remaining == decoded else normalize_excerpt(remaining)
        decoded = following
    value = scrubbed
    encoded = value.encode("utf-8")
    if truncated or len(encoded) > EXCERPT_LIMIT:
        marker = b"\n[truncated]"
        clipped = encoded[: EXCERPT_LIMIT - len(marker)].decode("utf-8", errors="ignore")
        return clipped + marker.decode()
    return value


def scrub_route(value: str) -> str:
    """Keep plain destinations with any explicit port in the range 1–65535."""
    decoded = value
    for _ in range(5):
        if any(character.isspace() or ord(character) < 32 for character in decoded):
            return "[redacted]"
        if any(character in decoded for character in "@?#"):
            return "[redacted]"
        try:
            route = urlsplit(decoded)
            port = route.port
            if (not route.scheme or not (route.netloc or route.path)
                    or (route.scheme in {"http", "https"} and not route.hostname)
                    or route.netloc.endswith(":")
                    or (port is not None and not 1 <= port <= 65535)
                    or "//" in route.path or url_credentials(decoded)):
                return "[redacted]"
        except ValueError:
            return "[redacted]"
        normalized = re.sub(r"[^a-z0-9]", "", decoded.lower())
        if any(word in normalized for word in CREDENTIAL_WORDS):
            return "[redacted]"
        for pattern in SCRUB_PATTERNS:
            if re.sub(
                pattern, scrub_json_header if pattern == JSON_HEADER_PATTERN else "[redacted]",
                decoded,
            ) != decoded:
                return "[redacted]"
        following = normalize_excerpt(decoded)
        if following == decoded:
            return value
        decoded = following
    return "[redacted]"


def handoff_label(value: str, fallback: str) -> str:
    """Keep only identifiers that pass the same whole-document safety decision."""
    return value if scrub_excerpt(value.encode("utf-8"), False) == value else fallback


def failure_shape(value: Any) -> dict[str, Any]:
    """Validate a closed failure record before interpreting its paths or bindings."""
    record = fields(value, {
        "candidate_sha256", "target", "stage", "check", "observed_at", "evidence",
    })
    target = fields(record["target"], {"environment", "account"})
    check = fields(record["check"], {"id", "status"})
    if (
        not text(record["candidate_sha256"], handoff.DIGEST)
        or not all(text(item) for item in target.values())
        or record["stage"] not in ("post-deploy", "recovery")
        or not text(check["id"], handoff.IDENTIFIER)
        or not text(check["status"])
        or not text(record["observed_at"])
        or not isinstance(record["evidence"], list)
    ):
        raise Refusal("failure-malformed")
    handoff.utc_time(record["observed_at"])
    identifiers: set[str] = set()
    for evidence in record["evidence"]:
        optional = {"kind"} if isinstance(evidence, dict) and "kind" in evidence else set()
        item = fields(evidence, {"id", "path", "sha256"} | optional)
        if (
            not text(item["id"], handoff.IDENTIFIER)
            or item["id"] in identifiers
            or not text(item["path"])
            or not text(item["sha256"], handoff.DIGEST)
            or ("kind" in item and not text(item["kind"]))
        ):
            raise Refusal("failure-malformed")
        identifiers.add(item["id"])
    return record


def repair_handoff(
    *, root: Path, admission: str, failure: str, now: str | None = None,
) -> dict[str, Any]:
    """Bind a failed deployed check to its owner and return bounded redacted proof."""
    try:
        record = failure_shape(handoff.parse_json(read_manifest(root, failure)))
    except handoff.Refusal:
        raise Refusal("failure-malformed") from None
    try:
        admitted = load_verified_admission(admission, root=root, now=now)
        raw = read_manifest(root, admitted["candidate"]["locator"])
        if sha256(raw) != admitted["candidate"]["sha256"]:
            raise Refusal("admission-stale")
        candidate = handoff.parse_yaml(raw)
    except handoff.Refusal:
        raise Refusal("admission-stale") from None
    if record["candidate_sha256"] != admitted["candidate"]["sha256"]:
        raise Refusal("subject-mismatch")
    if record["target"] != admitted["target"]:
        raise Refusal("target-mismatch")
    if record["check"]["status"] != "fail":
        raise Refusal("check-not-failed")
    if not record["evidence"]:
        raise Refusal("evidence-unresolved")
    excerpts = []
    plan_components = {
        component["plan_bundle"] for component in candidate["components"]
        if component["kind"] == "terraform-plan"
    }
    plan_artifacts = {
        item["sha256"] for item in candidate["evidence"]
        if item["id"] in plan_components
        or re.search(r"(?:^|[^a-z])(?:plan|state)(?:$|[^a-z])", item["kind"].lower())
    }
    try:
        for item in record["evidence"]:
            digest = hashlib.sha256()
            evidence = bytearray()
            for chunk in bounded_chunks(root, item["path"], handoff.EVIDENCE_LIMIT):
                digest.update(chunk)
                # Credential indicators anywhere in the bounded document withhold it.
                if len(excerpts) < EXCERPT_COUNT:
                    evidence.extend(chunk)
            if "sha256:" + digest.hexdigest() != item["sha256"]:
                raise Refusal("evidence-unresolved")
            if len(excerpts) < EXCERPT_COUNT:
                excerpts.append({
                    "id": handoff_label(item["id"], f"evidence-{len(excerpts) + 1}"),
                    "sha256": item["sha256"], "size": len(evidence),
                    "text": scrub_excerpt(
                        bytes(evidence), len(evidence) > EXCERPT_LIMIT,
                        "plan" if item["sha256"] in plan_artifacts else item.get("kind", ""),
                    ),
                })
    except handoff.Refusal:
        raise Refusal("evidence-unresolved") from None
    owner = candidate["repair_owner"]
    route = scrub_route(owner["route"]) if owner.get("route") else None
    result = {
        "status": "handoff" if route and route != "[redacted]" else "human-handoff",
        "repair_owner": handoff_label(owner["id"], "repair-owner"),
        "excerpts": excerpts, "redaction": "best-effort",
        "truncated": len(record["evidence"]) > EXCERPT_COUNT, "issues": [],
    }
    if route is not None:
        result["route"] = route
    return result


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
    repair = commands.add_parser("repair-handoff", add_help=False)
    repair.add_argument("--admission", required=True)
    repair.add_argument("--failure", required=True)
    repair.add_argument("--root", required=True)
    repair.add_argument("--now")
    stage = commands.add_parser("check-stage", add_help=False)
    stage.add_argument("--stage", required=True, choices=tuple(STAGE_REQUIREMENTS))
    stage.add_argument("--admission", required=True)
    stage.add_argument("--review", action="append", default=[])
    stage.add_argument("--final")
    stage.add_argument("--root", required=True)
    stage.add_argument("--now")
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
        elif args.command == "repair-handoff":
            result = repair_handoff(
                root=Path(args.root), admission=args.admission, failure=args.failure, now=args.now,
            )
        elif args.command == "check-stage":
            result = check_stage(
                args.stage,
                root=Path(args.root),
                admission=args.admission,
                reviews=args.review,
                final=args.final,
                now=args.now,
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
        if result["status"] in ("admitted", "current", "pass", "handoff", "human-handoff")
        else (2 if result["status"] == "error" else 1)
    )


if __name__ == "__main__":
    sys.exit(main())
