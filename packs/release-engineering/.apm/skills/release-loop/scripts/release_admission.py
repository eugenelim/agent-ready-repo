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
from urllib.parse import unquote


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
    if record["result"] != derived and "unresolved-evidence" not in issues:
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
    record: dict[str, Any], records: dict[str, dict[str, Any]], root: Path
) -> bool:
    """Detect self and forward citations by locator, identifier or review bytes."""
    for evidence in record["evidence"]:
        for locator, other in records.items():
            if (
                evidence["path"] == locator or evidence["id"] in (locator, Path(locator).stem)
            ) and STAGE_ORDER[other["stage"]] >= STAGE_ORDER[record["stage"]]:
                return True
        # A review not supplied as --review remains a review, not runtime proof.
        try:
            other = review_shape(handoff.parse_json(read_manifest(root, evidence["path"])))
        except handoff.Refusal:
            continue
        if STAGE_ORDER[other["stage"]] >= STAGE_ORDER[record["stage"]]:
            return True
    return False


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
        verify(admission, root=root, now=now)
    except handoff.Refusal:
        issues.append("reassessment-required")
    records: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    for locator in reviews:
        try:
            records[locator] = review_shape(handoff.parse_json(read_manifest(root, locator)))
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
        if circular_evidence(record, records, root):
            issues.append("circular-review")
    # Resolve byte and binding failures before interpreting stage semantics.
    if issues:
        if any(code in issues for code in ("subject-mismatch", "target-mismatch")):
            issues.append("reassessment-required")
        return {"status": "refused", "issues": [{"code": code} for code in dict.fromkeys(issues)]}
    for required in STAGE_REQUIREMENTS[stage]:
        roles = ("reliability",) if required == "recovery" else tuple(REVIEW_AREAS)
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
    latest = max((handoff.utc_time(item["observed_at"]) for item in previous), default=None)
    for record in records.values():
        if record["stage"] == "post-deploy" and stage in ("post-deploy", "final"):
            if not any(
                item["kind"] in RUNTIME_KINDS
                and latest is not None
                and handoff.utc_time(item["observed_at"]) > latest
                and not any(
                    item[key] == earlier[key]
                    for earlier in previous
                    for key in ("id", "path", "sha256")
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
SCRUB_PATTERNS = (
    r"(?im)^[ \t]*(?:cookie|set-cookie|authorization|proxy-authorization)[ \t]*:[^\r\n]*",
    r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----[\s\S]*?(?:-----END (?:[A-Z]+ )*PRIVATE KEY-----|$)",
    r"(?i)\b(?:basic|bearer)\s+[^\s\"'<>]+",
    r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/\"'<>@]+@[^\s\"'<>]+",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*",
    r"(?i)[\"']?(?:[\w.\[\]-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|credential)[\w.\[\]-]*)[\"']?\s*[:=]\s*(?:\"(?:\\[\s\S]|[^\"\\])*(?:\"|\\?$)|'(?:\\[\s\S]|[^'\\])*(?:'|\\?$)|[^\s,;}&]+)",
    r"[A-Za-z0-9_+/=-]{32,}",
)

CREDENTIAL_WORDS = (
    "password", "passwd", "passphrase", "pwd", "secret", "token", "apikey", "accesskey",
    "credential", "auth", "cookie", "bearer", "privatekey", "session", "signature",
)


def credential_line(body: str) -> bool:
    """Recognise credential words after common key encodings and separators."""
    decoded = re.sub(
        r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match[1], 16)), unquote(body),
    )
    normalized = re.sub(r"[^a-z0-9]", "", decoded.lower())
    return any(word in normalized for word in CREDENTIAL_WORDS) or bool(
        re.search(r"\bcurl\b.*?\s(?:-u\S*|--user(?=\s|=|$))", decoded, re.IGNORECASE)
    )


def yaml_alias_lines(source: list[str]) -> set[int]:
    """Trace credential references to YAML anchor definitions and other aliases."""
    references: dict[str, list[int]] = {}
    names: list[list[str]] = []
    pending: list[str] = []
    definitions: set[str] = set()
    value_indent: int | None = None
    next_value = False
    for index, line in enumerate(source):
        nodes = re.findall(r"(?:^|[\s:,[{])([&*])([^\s,\[\]{}#]+)", line)
        found = [name for _, name in nodes]
        definitions.update(name for kind, name in nodes if kind == "&")
        names.append(found)
        for name in found:
            references.setdefault(name, []).append(index)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if value_indent is not None and indent <= value_indent and not (
            indent == value_indent and re.match(r"\s*-(?:\s|$)", line)
        ):
            value_indent = None
        named = credential_line(line)
        if named or next_value or value_indent is not None:
            pending.extend(found)
        if named:
            value_indent = indent
        next_value = named and bool(
            re.search(r"[:=]\s*(?:#.*)?$", line) or re.match(r"\s*\?\s+", line)
        )
    visited: set[str] = set()
    affected: set[int] = set()
    while pending:
        name = pending.pop()
        if name in visited or name not in definitions:
            continue
        visited.add(name)
        for index in references.get(name, []):
            if index not in affected:
                affected.add(index)
                pending.extend(names[index])
    return affected


def yaml_quote_continues(value: str, quote: str) -> bool:
    """Find a closing YAML quote, respecting escapes and doubled single quotes."""
    index = 0
    while index < len(value):
        char = value[index]
        if quote == '"' and char == "\\":
            index += 2
            continue
        if char == quote:
            if quote == "'" and value[index:index + 2] == "''":
                index += 2
                continue
            return False
        index += 1
    return True


def scrub_excerpt(raw: bytes, truncated: bool) -> str:
    """Suppress credential lines and continuations before value scrubbing and clipping."""
    lines: list[str] = []
    block_indent: int | None = None
    sequence_indent: int | None = None
    pending_indent: int | None = None
    delimiter: str | None = None
    pem = False
    continued = False
    brackets: list[str] = []
    quoted = False
    escaped = False
    malformed = False
    collection = ""
    previous_redacted = False
    yaml_quote: str | None = None
    source = raw.decode("utf-8", errors="replace").splitlines(keepends=True)
    alias_lines = yaml_alias_lines(source)
    for index, line in enumerate(source):
        body = line.rstrip("\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")
        ending = line[len(body):]
        decoded = re.sub(
            r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match[1], 16)), unquote(body),
        )
        named = credential_line(body) or index in alias_lines
        indent = len(body) - len(body.lstrip())
        first_value = pending_indent is not None and bool(body.strip())
        if first_value:
            assert pending_indent is not None
            block_indent = min(pending_indent, indent)
            sequence_indent = indent if re.match(r"-(?:\s|$)", body.lstrip()) else None
            pending_indent = None
        elif block_indent is not None and body.strip() and indent <= block_indent:
            if not (indent == sequence_indent and re.match(r"-(?:\s|$)", body.lstrip())):
                block_indent = None
                sequence_indent = None
        in_block = (block_indent is not None or delimiter is not None or pem or continued
                    or bool(brackets) or malformed or pending_indent is not None
                    or yaml_quote is not None)
        if named or in_block:
            # Give aliased sequence values the same continuation parsing as mappings.
            structural = re.sub(r"^(\s*-[ \t]+)", r"\1: ", body) if index in alias_lines else body
            # YAML node properties precede the value whose shape controls continuation.
            structural = re.sub(
                r"([:=]\s*)(?:(?:[&*][^\s,\[\]{}#]+|!<[^>]*>|![^\s,\[\]{}#]*)[ \t]*)+",
                r"\1", structural, count=1,
            ) if named and not in_block else structural
            if first_value:
                structural = re.sub(r"^\s*:\s*", "", body)
            elif re.match(r"^\s*\?\s+", body):
                structural += ":"
            fragment = body + "\n" if brackets else ""
            opening = (
                re.match(r"\s*([\[{])", structural) if first_value else
                re.search(r"[:=]\s*([\[{])", structural) if named and not in_block else None
            )
            if opening:
                fragment = structural[opening.start(1):] + "\n"
                collection = ""
                block_indent = None
                sequence_indent = None
            for char in fragment:
                collection += char
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        quoted = False
                elif char == '"':
                    quoted = True
                elif char in "{[":
                    brackets.append("}" if char == "{" else "]")
                elif char in "}]":
                    if not brackets or char != brackets.pop():
                        malformed = True
                        break
                    if not brackets:
                        try:
                            json.loads(collection)
                        except (ValueError, RecursionError):
                            malformed = True
                        collection = ""
                        break
            if fragment or malformed:
                pass  # JSON continuation owns this line, including its closing delimiter.
            elif yaml_quote is not None:
                if not yaml_quote_continues(body, yaml_quote):
                    yaml_quote = None
                    block_indent = None
            elif delimiter is not None:
                closing = re.escape(delimiter)
                if delimiter == '"""':
                    closing = r"(?<!\\)(?:\\\\)*" + closing
                if re.search(closing, body):
                    delimiter = None
            elif pem:
                if re.search(r"-----END (?:[A-Z]+ )*PRIVATE KEY-----", body):
                    pem = False
            elif first_value or named and not in_block:
                if re.search(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----", body):
                    pem = not bool(re.search(r"-----END (?:[A-Z]+ )*PRIVATE KEY-----", body))
                elif opening := re.search(r'"{3}|\'{3}', body):
                    closing = re.escape(opening[0])
                    if opening[0] == '"""':
                        closing = r"(?<!\\)(?:\\\\)*" + closing
                    if not re.search(closing, body[opening.end():]):
                        delimiter = opening[0]
                elif any(re.search(r":\s*[|>][1-9+\-]*\s*(?:#.*)?$", value)
                         for value in (decoded, structural)):
                    block_indent = indent
                elif scalar := (
                    re.match(r"\s*(.*)", structural) if first_value else
                    re.search(r"[:=]\s*(.*)", structural)
                ):
                    value = scalar[1].strip()
                    if value.startswith(('"', "'")):
                        if yaml_quote_continues(value[1:], value[0]):
                            yaml_quote = value[0]
                        block_indent = None
                    elif not value or value.startswith("#"):
                        # A resolved alias has no following value to consume.
                        if index not in alias_lines or not re.search(r"\*[^\s]+", body):
                            pending_indent = indent
                    elif not first_value:
                        block_indent = indent
                elif not first_value and (
                    any(re.search(r"[:=]\s*(?:#.*)?$", value) for value in (decoded, structural))
                    or re.fullmatch(
                        r"\s*(?:\"[^\"]+\"|'[^']+'|[\w%\\.\[\]-]+)\s*", decoded,
                    )
                ):
                    pending_indent = indent
            continued = body.rstrip().endswith("\\")
            if previous_redacted:
                lines[-1] = "[redacted]" + ending
            else:
                lines.append("[redacted]" + ending)
            previous_redacted = True
        else:
            lines.append(line)
            previous_redacted = False
    value = "".join(lines)
    for pattern in SCRUB_PATTERNS:
        value = re.sub(pattern, "[redacted]", value)
    encoded = value.encode("utf-8")
    if truncated or len(encoded) > EXCERPT_LIMIT:
        marker = b"\n[truncated]"
        clipped = encoded[: EXCERPT_LIMIT - len(marker)].decode("utf-8", errors="ignore")
        return clipped + marker.decode()
    return value


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
        item = fields(evidence, {"id", "path", "sha256"})
        if (
            not text(item["id"], handoff.IDENTIFIER)
            or item["id"] in identifiers
            or not text(item["path"])
            or not text(item["sha256"], handoff.DIGEST)
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
        verify(admission, root=root, now=now)
        admitted, _ = read_record(root, admission)
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
    try:
        for item in record["evidence"]:
            digest = hashlib.sha256()
            evidence = bytearray()
            for chunk in bounded_chunks(root, item["path"], handoff.EVIDENCE_LIMIT):
                digest.update(chunk)
                # Alias references anywhere in the bounded file can affect early values.
                if len(excerpts) < EXCERPT_COUNT:
                    evidence.extend(chunk)
            if "sha256:" + digest.hexdigest() != item["sha256"]:
                raise Refusal("evidence-unresolved")
            if len(excerpts) < EXCERPT_COUNT:
                excerpts.append({
                    "id": item["id"],
                    "text": scrub_excerpt(bytes(evidence), len(evidence) > EXCERPT_LIMIT),
                })
    except handoff.Refusal:
        raise Refusal("evidence-unresolved") from None
    owner = candidate["repair_owner"]
    result = {
        "status": "handoff" if owner.get("route") else "human-handoff",
        "repair_owner": owner["id"], "excerpts": excerpts, "redaction": "best-effort",
        "truncated": len(record["evidence"]) > EXCERPT_COUNT, "issues": [],
    }
    if owner.get("route"):
        result["route"] = scrub_excerpt(owner["route"].encode("utf-8"), False)
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
