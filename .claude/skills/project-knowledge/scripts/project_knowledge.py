#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
import re
import secrets
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

CONTRACT_VERSION = "knowledge-captured-observation.v1"
# Deliberately NOT the pack version. This records which producer-profile
# contract emitted the observation, so it changes only when that contract's
# emitted shape changes. Mirroring `pack.toml` made every core release a
# two-file edit enforced by a red test, to populate a field no consumer reads
# for a decision — the schema validates it as free text, and nothing compares
# or branches on it. A release number also answers the wrong question here:
# "which contract produced this record" outlives "which release was current".
PRODUCER_WORKFLOW_VERSION = "work-loop-producer-profile.v1"
CAPTURE_ID_PREFIX = "kco"
COMPETENCY_QUESTIONS = (
    "CQ-ORIENT",
    "CQ-DESIGN",
    "CQ-CHANGE",
    "CQ-DIAGNOSE",
    "CQ-REVIEW",
    "CQ-VERIFY",
    "CQ-OPERATE",
    "CQ-ROUTE",
    "CQ-RETIRE",
)
REQUIRED_DIAGNOSTIC_CODES = (
    "privacy",
    "provenance",
    "strict_parse",
    "confinement",
    "lock_contention",
    "lock_loss",
    "deadline_exceeded",
    "journal_capacity",
    "cursor_stale",
    "replay_required",
    "postimage_mismatch",
    "map_mismatch",
    "staged_dual_writer",
    "ambiguous_grouping",
    "forward_recovery_required",
)
SAFE_DIAGNOSTIC_FIELDS = frozenset(
    {
        "version",
        "reason_code",
        "capture_id",
        "mutation_id",
        "path",
        "line",
        "retryable",
        "recovery_action",
    }
)
_HELPERS = {
    "capture": frozenset({"capture_observation"}),
    "distill": frozenset(
        {
            "read_journal",
            "read_topic",
            "read_source",
            "write_knowledge",
        }
    ),
    "enquire": frozenset(
        {
            "read_committed_map",
            "read_committed_topic",
            "read_freshness_source",
        }
    ),
}
_BUDGETS = {
    "capture_event_bytes": 16 * 1024,
    "journal_partition_bytes": 32 * 1024 * 1024,
    "journal_partition_events": 50_000,
    "retained_partitions": 240,
    "retained_journal_bytes": 512 * 1024 * 1024,
    "pending_page_partitions": 6,
    "pending_page_events": 10_000,
    "pending_page_bytes": 16 * 1024 * 1024,
    "topic_bytes": 128 * 1024,
    "occurrences_per_topic": 256,
    "topic_files": 50_000,
    "topic_corpus_bytes": 512 * 1024 * 1024,
    "map_entries": 50_000,
    "map_bytes": 32 * 1024 * 1024,
    "enquiry_bodies": 12,
    "enquiry_body_read_bytes": 1 * 1024 * 1024,
    "envelope_bytes": 32 * 1024,
    "script_seconds": 30,
    "automatic_retries": 0,
}
_BIDI_CONTROL = range(0x202A, 0x202F)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_STORE: Any | None = None
_WINDOWS_RESERVED = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$", re.I)
_EMAIL = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])")
_URL = re.compile(r"(?i)\bhttps?://[^\s<>'\"]+")
_NON_HTTP_LOCATOR = re.compile(
    r"(?i)(?:\b(?:ftp|sftp|ssh|git|file)://[^\s<>'\"]+|\bgit@[a-z0-9.-]+:)"
)
_BARE_HOSTNAME = re.compile(
    r"(?i)(?<![\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|org|net|io|dev|app|co|ai|gov|edu|example|internal|local|corp|lan)"
    r"(?::[0-9]{1,5})?(?:/[^\s<>'\"]*)?(?![\w.-])"
)
_USER_PATH = re.compile(
    r"(?i)(?:^|[\s'\"])(?:/users/[^/\s]+|/home/[^/\s]+|[a-z]:\\users\\[^\\\s]+)"
)
_SECRET_SHAPE = re.compile(
    r"(?i)(?:-----begin [^-]+ private key-----|"
    r"(?<![a-z0-9])bearer\s+[a-z0-9._~-]{12,}|"
    r"(?<![a-z0-9])(?:api[_ -]?key|password|secret|token)\s*[:=]\s*[^\s]{8,}|"
    r"(?<![a-z0-9])(?:api[_ -]?key|password|secret|token)[_-][^\s/]{8,}|"
    r"(?<![a-z0-9])(?:akia[0-9a-z]{16}|gh[pousr]_[0-9a-z]{20,})(?![a-z0-9]))"
)
_INSTRUCTION_SHAPE = re.compile(
    r"(?i)(?:ignore (?:all |any )?(?:previous|prior|higher[- ]priority) instructions|"
    r"(?:system|developer) message|do not follow (?:the )?(?:rules|instructions)|"
    r"run (?:this|the following) command|<\/?(?:system|developer|assistant)>)"
)
_PRIVATE_IDENTIFIER = re.compile(
    r"(?i)(?:(?<![a-z0-9])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}(?![a-z0-9])|"
    r"(?<![a-z0-9])(?:account|tenant|user)[_ -]?id(?:\s*[:=]\s*|[_-])"
    r"[a-z0-9][a-z0-9._-]{5,}(?![a-z0-9])|"
    r"(?<![a-z0-9])[a-z0-9.-]+\.(?:internal|local|corp|lan)(?![a-z0-9]))"
)
_PROFILE_DETERMINISTIC_CAPTURE_FIELDS = frozenset(
    {
        "contract_version",
        "producer",
        "semantic_gate",
        "freshness_anchor",
        "observed_at",
    }
)
_WORK_LOOP_CAPTURE_GATES = frozenset({"spec-approved", "plan-locked"})
_WORK_LOOP_ENQUIRY_GATES = {
    "change": {
        "question": "Which recurring project changes should inform this scope decision?",
        "question_id": "CQ-CHANGE",
        "semantic_fields": frozenset({"task_summary", "scope", "risk"}),
        "permits_refinement": True,
    },
    "verify": {
        "question": (
            "Which recurring verification practices should inform these construction tests?"
        ),
        "question_id": "CQ-VERIFY",
        "semantic_fields": frozenset({"task_summary", "scope", "risk"}),
        "permits_refinement": True,
    },
    "review": {
        "question": (
            "Which recurring project risks should these reviewers verify against "
            "the current target?"
        ),
        "question_id": "CQ-REVIEW",
        "semantic_fields": frozenset({"task_summary", "scope"}),
        "permits_refinement": False,
    },
}


class PrivacyRefusal(ValueError):
    """A deterministic pre-admission privacy or injection refusal."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _assert_safe_unicode(value: Any) -> None:
    if isinstance(value, str):
        for character in value:
            codepoint = ord(character)
            if codepoint < 0x20 or codepoint == 0x7F:
                raise ValueError("control character is not allowed")
            if 0xD800 <= codepoint <= 0xDFFF:
                raise ValueError("surrogate code point is not allowed")
            if codepoint in _BIDI_CONTROL:
                raise ValueError("bidirectional control character is not allowed")
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_safe_unicode(key)
            _assert_safe_unicode(item)
    elif isinstance(value, list):
        for item in value:
            _assert_safe_unicode(item)


def _parse_strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("strict JSON parsing failed") from exc
    _assert_safe_unicode(parsed)
    return parsed


def parse_capture_request(raw: bytes) -> dict[str, Any]:
    parsed = _parse_strict_json(raw)
    if not isinstance(parsed, dict):
        raise ValueError("capture request must be an object")
    return validate_capture_request(parsed)


def _validate_work_loop_artifact(gate: str, artifact: str) -> None:
    parts = Path(artifact).parts
    if len(parts) != 4 or parts[0:2] != ("docs", "specs"):
        raise ValueError("artifact is incompatible with semantic gate")
    expected_name = "spec.md" if gate == "spec-approved" else "plan.md"
    if parts[-1] != expected_name:
        raise ValueError("artifact is incompatible with semantic gate")


def build_work_loop_capture_request(
    semantic_input: dict[str, Any],
    *,
    semantic_gate: str,
    artifact: str,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the strict capture request owned by the work-loop producer profile."""

    if semantic_gate not in _WORK_LOOP_CAPTURE_GATES:
        raise ValueError("semantic gate does not permit capture")
    if not isinstance(semantic_input, dict):
        raise ValueError("producer semantic input must be an object")
    supplied = _PROFILE_DETERMINISTIC_CAPTURE_FIELDS & set(semantic_input)
    if supplied:
        raise ValueError("producer supplied deterministic field")
    artifact = _expect_repo_path(artifact)
    _validate_work_loop_artifact(semantic_gate, artifact)
    store = _knowledge_store()
    artifact_bytes = store.read_confined_source(repo_root, artifact)
    if semantic_gate == "plan-locked":
        sibling_spec = _expect_repo_path(str(Path(artifact).with_name("spec.md")))
        store.read_confined_source(repo_root, sibling_spec)
    provenance = semantic_input.get("provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("sources"), list):
        raise ValueError("invalid provenance")
    for source in provenance["sources"]:
        if not isinstance(source, dict) or "path" not in source:
            raise ValueError("invalid provenance")
        store.read_confined_source(repo_root, _expect_repo_path(source["path"]))
    request = dict(semantic_input)
    request.update(
        {
            "contract_version": CONTRACT_VERSION,
            "producer": {
                "workflow": "work-loop",
                "workflow_version": PRODUCER_WORKFLOW_VERSION,
            },
            "semantic_gate": {"name": semantic_gate, "artifact": artifact},
            "freshness_anchor": {"path": artifact, "digest": digest_bytes(artifact_bytes)},
            "observed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    return validate_capture_request(request)


def build_work_loop_enquiry(
    semantic_input: dict[str, Any], *, semantic_gate: str
) -> dict[str, Any]:
    """Build the fixed work-loop enquiry accepted at one semantic gate."""

    gate = _WORK_LOOP_ENQUIRY_GATES.get(semantic_gate)
    if gate is None:
        raise ValueError("semantic gate does not permit enquiry")
    if not isinstance(semantic_input, dict) or set(semantic_input) != gate["semantic_fields"]:
        raise ValueError("invalid enquiry semantic input")
    request = {
        "task_summary": _expect_text(semantic_input["task_summary"], 1000),
        "scope": _expect_repo_path(semantic_input["scope"]),
        "question": gate["question"],
        "question_id": gate["question_id"],
        "caller": "skill",
        "risk": "consequential" if semantic_gate == "review" else semantic_input["risk"],
    }
    if request["risk"] not in {"routine", "consequential"}:
        raise ValueError("invalid enquiry risk")
    return request


def build_work_loop_review_enquiry(semantic_input: dict[str, Any]) -> dict[str, Any]:
    """Build the fixed review enquiry retained for public helper compatibility."""

    return build_work_loop_enquiry(semantic_input, semantic_gate="review")


def validate_work_loop_terminal_distill_request(
    request: dict[str, Any], *, repo_root: Path
) -> dict[str, Any]:
    """Refuse non-terminal or non-work-loop receipts before terminal distillation."""

    _expect_keys(request, {"selection_mode", "receipts"}, set())
    if request["selection_mode"] != "workflow-receipts":
        raise ValueError("terminal distillation requires workflow receipts")
    receipts = request["receipts"]
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("terminal distillation requires capture receipts")
    selectors = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ValueError("invalid capture receipt")
        _expect_keys(
            receipt,
            {"receipt_version", "capture_id", "partition", "event_type", "state"},
            set(),
        )
        if (
            receipt["receipt_version"] != "knowledge-capture-receipt.v1"
            or receipt["event_type"] != "observation.captured"
            or receipt["state"] != "pending"
        ):
            raise ValueError("invalid capture receipt")
        selectors.append(
            {"capture_id": receipt["capture_id"], "partition": receipt["partition"]}
        )
    normalized = {"selection_mode": "workflow-receipts", "receipts": selectors}
    page = _knowledge_store().pending_page(repo_root, normalized)
    for event in page["pending"]:
        captured_request = event["request"]
        if (
            captured_request["producer"]["workflow"] != "work-loop"
            or captured_request["semantic_gate"]["name"] != "plan-locked"
        ):
            raise ValueError("receipt does not originate at terminal gate")
    return normalized


def _expect_keys(value: dict[str, Any], required: set[str], optional: set[str]) -> None:
    keys = set(value)
    unknown = keys - required - optional
    if unknown:
        raise ValueError(f"unknown field: {sorted(unknown)[0]}")
    missing = required - keys
    if missing:
        raise ValueError(f"missing field: {sorted(missing)[0]}")


def _expect_repo_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 1000:
        raise ValueError("invalid repository path")
    normalized = unicodedata.normalize("NFC", value).replace("\\", "/")
    if normalized == ".":
        return normalized
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError("unsafe repository path")
    components = normalized.split("/")
    if any(
        not component
        or component in {".", ".."}
        or ":" in component
        or component.endswith((".", " "))
        or _WINDOWS_RESERVED.fullmatch(component)
        for component in components
    ):
        raise ValueError("unsafe repository path")
    _assert_safe_unicode(normalized)
    return normalized


def serialize_scope(value: Any) -> str:
    """Return the platform-neutral canonical form of a repository scope."""

    return _expect_repo_path(value)


def assert_persistable_text(*values: str) -> None:
    for value in values:
        if any(
            pattern.search(value)
            for pattern in (
                _EMAIL,
                _URL,
                _NON_HTTP_LOCATOR,
                _BARE_HOSTNAME,
                _USER_PATH,
                _SECRET_SHAPE,
                _INSTRUCTION_SHAPE,
                _PRIVATE_IDENTIFIER,
            )
        ):
            raise PrivacyRefusal("captured body failed deterministic privacy checks")


def assert_persistable_paths(*values: str) -> None:
    for value in values:
        if any(
            pattern.search(value)
            for pattern in (
                _EMAIL,
                _USER_PATH,
                _SECRET_SHAPE,
                _PRIVATE_IDENTIFIER,
            )
        ):
            raise PrivacyRefusal("captured path failed deterministic privacy checks")


def _deterministic_privacy_scan(request: dict[str, Any]) -> None:
    prose = [request["lesson"]]
    if "friction" in request:
        prose.append(request["friction"]["summary"])
    if "verification_route" in request:
        prose.append(request["verification_route"]["command"])
    prose.extend(
        (
            request["producer"]["workflow"],
            request["producer"]["workflow_version"],
            request["semantic_gate"]["name"],
        )
    )
    assert_persistable_text(*prose)
    paths = [
        *request["project_scope"]["paths"],
        request["destination_hint"]["path"],
        request["semantic_gate"]["artifact"],
        *(source["path"] for source in request["provenance"]["sources"]),
        request["freshness_anchor"]["path"],
    ]
    if "verification_route" in request:
        paths.append(request["verification_route"]["path"])
    assert_persistable_paths(*paths)


def _expect_text(value: Any, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise ValueError("invalid bounded text")
    _assert_safe_unicode(value)
    return value


def _expect_bool(value: Any, expected: bool) -> None:
    if value is not expected:
        raise ValueError("invalid attestation")


def validate_capture_request(request: dict[str, Any]) -> dict[str, Any]:
    required = {
        "contract_version",
        "lesson",
        "kind",
        "project_scope",
        "competency_facets",
        "destination_hint",
        "producer",
        "semantic_gate",
        "provenance",
        "freshness_anchor",
        "observed_at",
        "privacy_attestation",
    }
    optional = {"friction", "verification_route"}
    _expect_keys(request, required, optional)
    if request["contract_version"] != CONTRACT_VERSION:
        raise ValueError("invalid contract version")
    _expect_text(request["lesson"], 2000)
    if request["kind"] not in {"pattern", "gotcha", "antipattern"}:
        raise ValueError("invalid kind")
    _validate_project_scope(request["project_scope"])
    facets = request["competency_facets"]
    if (
        not isinstance(facets, list)
        or not facets
        or len(facets) > len(COMPETENCY_QUESTIONS)
        or any(not isinstance(facet, str) for facet in facets)
        or len(set(facets)) != len(facets)
        or any(facet not in COMPETENCY_QUESTIONS for facet in facets)
    ):
        raise ValueError("invalid competency facets")
    _validate_destination_hint(request["destination_hint"])
    _validate_producer(request["producer"])
    _validate_semantic_gate(request["semantic_gate"])
    _validate_provenance(request["provenance"])
    _validate_freshness_anchor(request["freshness_anchor"])
    _observation_month(request)
    _validate_privacy_attestation(request["privacy_attestation"])
    if "friction" in request:
        _validate_friction(request["friction"])
    if "verification_route" in request:
        _validate_verification_route(request["verification_route"])
    _deterministic_privacy_scan(request)
    return request


def _validate_project_scope(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid project scope")
    _expect_keys(value, {"paths", "audience"}, set())
    paths = value["paths"]
    if not isinstance(paths, list) or not paths or len(paths) > 20:
        raise ValueError("invalid project scope paths")
    value["paths"] = [_expect_repo_path(path) for path in paths]
    if value["audience"] != "project":
        raise ValueError("invalid project scope audience")


def _validate_destination_hint(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid destination hint")
    _expect_keys(value, {"type", "path"}, set())
    if value["type"] not in {"topic", "canonical-artifact", "route-suggestion"}:
        raise ValueError("invalid destination hint type")
    value["path"] = _expect_repo_path(value["path"])


def _validate_producer(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid producer")
    _expect_keys(value, {"workflow", "workflow_version"}, set())
    _expect_slug(value["workflow"])
    _expect_text(value["workflow_version"], 80)


def _validate_semantic_gate(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid semantic gate")
    _expect_keys(value, {"name", "artifact"}, set())
    _expect_slug(value["name"])
    value["artifact"] = _expect_repo_path(value["artifact"])


def _validate_provenance(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid provenance")
    _expect_keys(value, {"sources"}, set())
    sources = value["sources"]
    if not isinstance(sources, list) or not sources or len(sources) > 12:
        raise ValueError("invalid provenance sources")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("invalid provenance source")
        _expect_keys(source, {"path"}, {"line_start", "line_end"})
        source["path"] = _expect_repo_path(source["path"])
        for key in ("line_start", "line_end"):
            if key in source and (
                not isinstance(source[key], int) or not (1 <= source[key] <= 1_000_000)
            ):
                raise ValueError("invalid provenance line")


def _validate_freshness_anchor(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid freshness anchor")
    _expect_keys(value, {"path", "digest"}, set())
    value["path"] = _expect_repo_path(value["path"])
    parse_digest(value["digest"])


def _validate_privacy_attestation(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid privacy attestation")
    _expect_keys(
        value,
        {"reviewed", "contains_private_data", "contains_secrets", "contains_instructions"},
        set(),
    )
    _expect_bool(value["reviewed"], True)
    _expect_bool(value["contains_private_data"], False)
    _expect_bool(value["contains_secrets"], False)
    _expect_bool(value["contains_instructions"], False)


def _validate_friction(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid friction")
    _expect_keys(value, {"failed_attempts", "summary"}, set())
    if not isinstance(value["failed_attempts"], int) or not (1 <= value["failed_attempts"] <= 20):
        raise ValueError("invalid friction attempts")
    _expect_text(value["summary"], 500)


def _validate_verification_route(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("invalid verification route")
    _expect_keys(value, {"command", "path"}, set())
    _expect_text(value["command"], 500)
    value["path"] = _expect_repo_path(value["path"])


def _expect_slug(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", value):
        raise ValueError("invalid slug")
    return value


def _observation_month(request: dict[str, Any]) -> str:
    observed_at = request.get("observed_at")
    if not isinstance(observed_at, str):
        raise ValueError("invalid observation time")
    try:
        parsed = datetime.strptime(observed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("invalid observation time") from exc
    return f"{parsed:%Y%m}"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def derive_capture_id_from_strict_json(raw: bytes) -> str:
    return derive_capture_id(parse_capture_request(raw))


def derive_capture_id(request: dict[str, Any]) -> str:
    request = copy.deepcopy(validate_capture_request(request))
    if "capture_id" in request:
        raise ValueError("capture_id is derived by core")
    digest = hashlib.sha256(_canonical_json_bytes(request)).hexdigest()
    return f"{CAPTURE_ID_PREFIX}-{_observation_month(request)}-{digest}"


def capture_id_preimage_fields() -> tuple[str, ...]:
    return (
        "contract_version",
        "lesson",
        "kind",
        "project_scope",
        "competency_facets",
        "destination_hint",
        "producer",
        "semantic_gate",
        "provenance",
        "freshness_anchor",
        "observed_at",
        "privacy_attestation",
        "friction",
        "verification_route",
    )


def budget_contract() -> dict[str, int]:
    return dict(_BUDGETS)


def competency_questions() -> tuple[str, ...]:
    return COMPETENCY_QUESTIONS


def digest_bytes(raw: bytes) -> dict[str, Any]:
    return {
        "kind": "sha256-bytes-v1",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_length": len(raw),
    }


def parse_digest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("invalid digest")
    if value.get("kind") == "sha256-bytes-v1":
        _expect_keys(value, {"kind", "sha256", "byte_length"}, set())
        if not isinstance(value["sha256"], str) or not _HEX64.fullmatch(value["sha256"]):
            raise ValueError("invalid sha256 digest")
        if not isinstance(value["byte_length"], int) or value["byte_length"] < 0:
            raise ValueError("invalid digest length")
        return value
    if value.get("kind") == "git-blob-v1":
        _expect_keys(value, {"kind", "algorithm", "object_id"}, set())
        lengths = {"sha1": 40, "sha256": 64}
        algorithm = value["algorithm"]
        object_id = value["object_id"]
        if (
            algorithm not in lengths
            or not isinstance(object_id, str)
            or len(object_id) != lengths[algorithm]
            or any(character not in "0123456789abcdef" for character in object_id)
        ):
            raise ValueError("invalid git blob digest")
        return value
    raise ValueError("unsupported digest kind")


@dataclasses.dataclass(frozen=True)
class KnowledgeDiagnostic:
    reason_code: str
    retryable: bool
    recovery_action: str = "none"
    capture_id: str | None = None
    mutation_id: str | None = None
    path: str | None = None
    line: int | None = None

    def __post_init__(self) -> None:
        if self.reason_code not in REQUIRED_DIAGNOSTIC_CODES:
            raise ValueError("unknown diagnostic code")
        if self.path is not None:
            _expect_repo_path(self.path)
        if self.line is not None and self.line < 1:
            raise ValueError("invalid diagnostic line")


def render_diagnostic(diagnostic: KnowledgeDiagnostic) -> dict[str, Any]:
    result: dict[str, Any] = {
        "version": "knowledge-diagnostic.v1",
        "reason_code": diagnostic.reason_code,
        "retryable": diagnostic.retryable,
        "recovery_action": diagnostic.recovery_action,
    }
    for field in ("capture_id", "mutation_id", "path", "line"):
        value = getattr(diagnostic, field)
        if value is not None:
            result[field] = value
    if not set(result) <= SAFE_DIAGNOSTIC_FIELDS:
        raise ValueError("unsafe diagnostic field")
    return result


def helpers_for(mode: str) -> set[str]:
    if mode not in _HELPERS:
        raise ValueError("unknown project-knowledge mode")
    return set(_HELPERS[mode])


def all_helpers() -> set[str]:
    result: set[str] = set()
    for helpers in _HELPERS.values():
        result.update(helpers)
    return result


def all_mode_capabilities() -> dict[str, set[str]]:
    return {mode: set(helpers) for mode, helpers in _HELPERS.items()}


def union_capabilities(capabilities: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    for helpers in capabilities.values():
        result.update(helpers)
    return result


def helper_registries_are_disjoint() -> bool:
    seen: set[str] = set()
    for helpers in _HELPERS.values():
        if seen & helpers:
            return False
        seen.update(helpers)
    return True


def call_helper(mode: str, helper: str, *args: Any, **kwargs: Any) -> Any:
    if helper not in helpers_for(mode):
        raise ValueError("helper is not available in this mode")
    if mode == "capture" and helper == "capture_observation":
        return _knowledge_store().capture_observation(*args, **kwargs)
    if mode == "distill" and helper == "read_journal":
        return _knowledge_store().pending_page(*args, **kwargs)
    if mode == "distill" and helper == "read_topic":
        return _knowledge_store().read_worktree_topic(*args, **kwargs)
    if mode == "distill" and helper == "read_source":
        return _knowledge_store().read_confined_source(*args, **kwargs)
    if mode == "distill" and helper == "write_knowledge":
        return _knowledge_store().distill_observation(*args, **kwargs)
    if mode == "enquire" and helper == "read_committed_map":
        return _knowledge_store().enquire(*args, **kwargs)
    if mode == "enquire" and helper == "read_committed_topic":
        return _knowledge_store().read_committed_topic(*args, **kwargs)
    if mode == "enquire" and helper == "read_freshness_source":
        return _knowledge_store().read_freshness_source(*args, **kwargs)
    raise AssertionError(f"unrouted registered helper: {mode}:{helper}")


def _knowledge_store() -> Any:
    global _STORE
    if _STORE is not None:
        return _STORE
    script = Path(__file__).resolve().parent / "knowledge_store.py"
    spec = importlib.util.spec_from_file_location("_project_knowledge_store", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("knowledge store is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _STORE = module
    return _STORE


def new_lock_token() -> str:
    return secrets.token_hex(32)


@dataclasses.dataclass
class LockTokenState:
    token: str
    _released: bool = False

    def release(self, presented_token: str) -> bool:
        if self._released:
            return False
        if not secrets.compare_digest(self.token, presented_token):
            return False
        self._released = True
        return True


def _read_bounded_stdin(limit: int) -> bytes:
    raw = sys.stdin.buffer.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("stdin budget exceeded")
    return raw


def _run_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project knowledge mode shell.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--distill", action="store_true")
    mode.add_argument("--enquire", action="store_true")
    mode.add_argument("--migrate-legacy", action="store_true")
    mode.add_argument("--activate-staged", action="store_true")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--writer-time")
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--producer-profile")
    parser.add_argument("--semantic-gate")
    parser.add_argument("--artifact")
    parser.add_argument("--refinement", action="store_true")
    args = parser.parse_args(argv)
    selected = (
        "capture"
        if args.capture
        else "distill"
        if args.distill
        else "migrate-legacy"
        if args.migrate_legacy
        else "activate-staged"
        if args.activate_staged
        else "enquire"
    )
    store = _knowledge_store()
    store.set_deadline(_BUDGETS["script_seconds"])
    repo_root = store.resolve_worktree_root(Path(args.repo_root))
    if args.pending and selected != "distill":
        raise ValueError("pending is only valid for distillation")
    if args.refinement and selected != "enquire":
        raise ValueError("refinement is only valid for enquiry")
    if args.producer_profile is None:
        if args.semantic_gate is not None or args.artifact is not None:
            raise ValueError("producer profile is required for profile arguments")
        if args.refinement:
            raise ValueError("refinement requires a producer profile")
    elif args.producer_profile != "work-loop":
        raise ValueError("unknown producer profile")
    elif args.semantic_gate is None:
        raise ValueError("producer profile requires a semantic gate")
    elif selected == "capture" and args.artifact is None:
        raise ValueError("capture producer profile requires an artifact")
    elif selected in {"enquire", "distill"} and args.artifact is not None:
        raise ValueError("producer profile mode does not accept an artifact")
    elif selected not in {"capture", "distill", "enquire"}:
        raise ValueError("producer profile does not support this mode")
    if selected == "capture":
        raw = _read_bounded_stdin(_BUDGETS["capture_event_bytes"])
        if args.producer_profile is None:
            request = parse_capture_request(raw)
        else:
            semantic_input = _parse_strict_json(raw)
            request = build_work_loop_capture_request(
                semantic_input,
                semantic_gate=args.semantic_gate,
                artifact=args.artifact,
                repo_root=repo_root,
            )
        receipt = call_helper(
            "capture",
            "capture_observation",
            repo_root,
            request,
            writer_time=args.writer_time,
        )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if selected == "distill":
        raw = _read_bounded_stdin(_BUDGETS["topic_bytes"] * 2)
        request = _parse_strict_json(raw) if raw.strip() else {}
        if args.producer_profile is not None:
            if not args.pending or args.semantic_gate != "plan-locked":
                raise ValueError("semantic gate does not permit terminal distillation")
            request = validate_work_loop_terminal_distill_request(
                request, repo_root=repo_root
            )
        if args.pending:
            receipt = store.distill_pending(repo_root, request)
        else:
            receipt = call_helper(
                "distill",
                "write_knowledge",
                repo_root,
                request,
            )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if selected == "enquire":
        raw = _read_bounded_stdin(_BUDGETS["envelope_bytes"])
        if args.producer_profile is None:
            request = _parse_strict_json(raw) if raw.strip() else {}
        else:
            gate = _WORK_LOOP_ENQUIRY_GATES.get(args.semantic_gate)
            if gate is None:
                raise ValueError("semantic gate does not permit enquiry")
            if args.refinement and not gate["permits_refinement"]:
                raise ValueError("semantic gate does not permit enquiry refinement")
            request = build_work_loop_enquiry(
                _parse_strict_json(raw), semantic_gate=args.semantic_gate
            )
        result = call_helper(
            "enquire",
            "read_committed_map",
            repo_root,
            request,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    if selected == "migrate-legacy":
        receipt = store.stage_legacy_migration(repo_root)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if selected == "activate-staged":
        raw = _read_bounded_stdin(_BUDGETS["map_bytes"])
        snapshot = _parse_strict_json(raw)
        print(
            json.dumps(
                store.activate_staged_migration(
                    repo_root,
                    committed_snapshot=snapshot,
                ),
                sort_keys=True,
            )
        )
        return 0
    print(json.dumps({"mode": selected, "helpers": sorted(helpers_for(selected))}))
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return _run_main(argv)
    except PrivacyRefusal:
        diagnostic = render_diagnostic(
            KnowledgeDiagnostic(
                reason_code="privacy",
                retryable=False,
                recovery_action="fix_request",
            )
        )
    except ValueError:
        diagnostic = render_diagnostic(
            KnowledgeDiagnostic(
                reason_code="strict_parse",
                retryable=False,
                recovery_action="fix_request",
            )
        )
    except Exception as exc:
        store = _STORE
        if store is None or not isinstance(exc, store.KnowledgeStoreError):
            raise
        diagnostic = exc.diagnostic
    print(json.dumps(diagnostic, sort_keys=True), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
