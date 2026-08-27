"""Shared semantic fixtures for provider and consumer behavior."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CONTRACT_VERSION = "agent-skill-engineering-reference/v1"
TOPICS = {
    "framing-and-trigger-quality",
    "instruction-density-and-progressive-disclosure",
    "resources-scripts-and-exit-contracts",
}
TASK_KINDS = {
    "skill-authoring",
    "skill-review",
    "skill-eval-ci",
    "agent-extension-design",
}
REQUEST_FIELDS = {
    "contract_version",
    "task_kind",
    "question",
    "capabilities",
    "runtime",
    "max_topics",
}
REQUIRED_REQUEST_FIELDS = {
    "contract_version",
    "task_kind",
    "question",
    "capabilities",
}
RESPONSE_FIELDS = {
    "contract_version",
    "status",
    "topic_ids",
    "guidance",
    "provenance",
    "profile_provenance",
    "warnings",
    "diagnostic",
}
PROVENANCE_FIELDS = {
    "provider_id",
    "contract_version",
    "source_digest",
    "ownership_manifest_digest",
}
PROFILE_FIELDS = {"profile", "retrieved_at", "verified_at"}
SLUG = re.compile(r"[a-z0-9][a-z0-9.-]{0,127}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
SENSITIVE = re.compile(r"token\s*=|secret|password|api[_-]?key", re.I)


@dataclass(frozen=True)
class ProviderResult:
    """Observable provider-evaluation result."""

    status: str
    topic_bodies: tuple[str, ...]
    content_reads: tuple[str, ...]
    baseline_continues: bool
    diagnostic: str | None


def _refuse(diagnostic: str, *, status: str = "unavailable") -> ProviderResult:
    """Return a fail-closed provider result with no content reads."""

    return ProviderResult(status, (), (), True, diagnostic)


def _request_is_valid(request: Any) -> bool:
    """Return whether a request has the exact bounded v1 semantic shape."""

    if not isinstance(request, dict):
        return False
    fields = set(request)
    if not fields >= REQUIRED_REQUEST_FIELDS or not fields <= REQUEST_FIELDS:
        return False
    question = request.get("question")
    capabilities = request.get("capabilities")
    maximum = request.get("max_topics", 3)
    if request.get("contract_version") != CONTRACT_VERSION:
        return False
    if request.get("task_kind") not in TASK_KINDS:
        return False
    if not isinstance(question, str) or not 12 <= len(question) <= 512:
        return False
    if question.strip().casefold() in {"help", "everything", "all guidance"}:
        return False
    if (
        not isinstance(capabilities, list)
        or len(capabilities) > 16
        or len(set(capabilities)) != len(capabilities)
        or any(not isinstance(item, str) or SLUG.fullmatch(item) is None for item in capabilities)
    ):
        return False
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 3:
        return False
    runtime = request.get("runtime")
    return runtime is None or (
        isinstance(runtime, str) and SLUG.fullmatch(runtime) is not None
    )


def _profiles_are_valid(value: Any) -> bool:
    """Validate bounded profile provenance with exact ISO calendar dates."""

    if not isinstance(value, list) or len(value) > 16:
        return False
    for item in value:
        if not isinstance(item, dict) or set(item) != PROFILE_FIELDS:
            return False
        if not isinstance(item.get("profile"), str) or SLUG.fullmatch(item["profile"]) is None:
            return False
        try:
            date.fromisoformat(item["retrieved_at"])
            date.fromisoformat(item["verified_at"])
        except (TypeError, ValueError):
            return False
    return True


def _bounded_safe_text(value: Any, *, nullable: bool = False) -> bool:
    """Validate a bounded diagnostic or warning without secret-shaped content."""

    if nullable and value is None:
        return True
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 160
        and SENSITIVE.search(value) is None
    )


def _response_is_valid(
    response: Any,
    *,
    selected: dict[str, Any],
    maximum: int,
) -> bool:
    """Return whether an untrusted provider response satisfies v1 exactly."""

    if not isinstance(response, dict) or set(response) != RESPONSE_FIELDS:
        return False
    if response.get("contract_version") != CONTRACT_VERSION:
        return False
    status = response.get("status")
    if status not in {"ok", "out-of-scope", "unavailable", "stale-profile"}:
        return False
    topics = response.get("topic_ids")
    guidance = response.get("guidance")
    if (
        not isinstance(topics, list)
        or len(topics) > maximum
        or len(set(topics)) != len(topics)
        or any(topic not in TOPICS for topic in topics)
        or not isinstance(guidance, dict)
        or set(guidance) != set(topics)
        or any(not isinstance(body, str) or not 1 <= len(body) <= 4_000 for body in guidance.values())
    ):
        return False
    if status == "ok" and not topics:
        return False
    if status != "ok" and (topics or guidance):
        return False
    provenance = response.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_FIELDS:
        return False
    if (
        provenance.get("provider_id") != selected.get("provider_id")
        or provenance.get("contract_version") != CONTRACT_VERSION
        or not isinstance(provenance.get("source_digest"), str)
        or DIGEST.fullmatch(provenance["source_digest"]) is None
        or not isinstance(provenance.get("ownership_manifest_digest"), str)
        or DIGEST.fullmatch(provenance["ownership_manifest_digest"]) is None
    ):
        return False
    warnings = response.get("warnings")
    return not (
        not isinstance(warnings, list)
        or len(warnings) > 3
        or any(not _bounded_safe_text(item) for item in warnings)
        or not _bounded_safe_text(response.get("diagnostic"), nullable=True)
        or not _profiles_are_valid(response.get("profile_provenance"))
    )


def evaluate_provider_case(case: dict[str, Any]) -> ProviderResult:
    """Evaluate the transport-independent selection and response contract."""

    request = case.get("request")
    if not _request_is_valid(request):
        return _refuse(
            "knowledge provider request out of scope",
            status="out-of-scope",
        )
    candidates = case.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return _refuse("knowledge provider unavailable")
    eligible: list[dict[str, Any]] = []
    stale = False
    integrity_failure = False
    task_kind = request["task_kind"]
    for candidate in candidates:
        if candidate.get("contract_version") != CONTRACT_VERSION:
            stale = True
            continue
        if not candidate.get("manifest_valid"):
            integrity_failure = True
            continue
        if candidate.get("authority") != ["filesystem_read_untrusted"]:
            continue
        declared_id = candidate.get("declared_provider_id", candidate.get("provider_id"))
        if declared_id != candidate.get("provider_id"):
            continue
        if task_kind not in candidate.get("task_kinds", []):
            continue
        eligible.append(candidate)
    if len(eligible) > 1:
        return _refuse("knowledge provider ambiguous")
    if not eligible:
        if integrity_failure:
            return _refuse("provider integrity unavailable")
        if stale:
            return _refuse("knowledge provider stale", status="stale-profile")
        return _refuse("knowledge provider ineligible")

    response = case.get("response")
    if not isinstance(response, dict):
        return _refuse("knowledge provider unavailable")
    if not _response_is_valid(
        response,
        selected=eligible[0],
        maximum=request.get("max_topics", 3),
    ):
        return _refuse("knowledge provider response refused")
    status = response.get("status")
    if status != "ok":
        return ProviderResult(str(status), (), (), True, response.get("diagnostic"))
    provider_reads = case.get("provider_reads")
    if not isinstance(provider_reads, list):
        return _refuse("knowledge provider response refused")
    for reference in provider_reads:
        if not isinstance(reference, dict) or set(reference) != {
            "path",
            "digest_matches",
            "manifest_member",
        }:
            return _refuse("knowledge provider response refused")
        if not reference.get("manifest_member") or not reference.get("digest_matches"):
            return _refuse("provider integrity unavailable")
    paths = tuple(reference["path"] for reference in provider_reads)
    topics = response["topic_ids"]
    bodies = tuple(response["guidance"][topic] for topic in topics)
    return ProviderResult(str(status), bodies, paths, True, response.get("diagnostic"))


def test_provider_contract_is_versioned_bounded_and_transport_independent() -> None:
    contract = json.loads(
        (FIXTURES / "provider-contract.json").read_text(encoding="utf-8")
    )
    assert contract["contract_version"] == CONTRACT_VERSION
    assert set(contract["task_kinds"]) == {
        "skill-authoring",
        "skill-review",
        "skill-eval-ci",
        "agent-extension-design",
    }
    assert contract["max_topics"] == {"minimum": 1, "maximum": 3, "default": 3}
    assert set(contract["request_fields"]) == REQUEST_FIELDS
    assert set(contract["response_fields"]) == RESPONSE_FIELDS
    assert contract["request_constraints"] == {
        "question": {
            "minimum_length": 12,
            "maximum_length": 512,
            "generic_values_refused": ["help", "everything", "all guidance"],
        },
        "capabilities": {
            "minimum_items": 0,
            "maximum_items": 16,
            "unique": True,
            "identifier_pattern": "[a-z0-9][a-z0-9.-]{0,127}",
        },
        "runtime": {
            "optional": True,
            "identifier_pattern": "[a-z0-9][a-z0-9.-]{0,127}",
        },
    }
    assert set(contract["response_statuses"]) == {
        "ok",
        "out-of-scope",
        "unavailable",
        "stale-profile",
    }


def test_every_provider_case_matches_the_shared_consumer_oracle() -> None:
    cases = json.loads(
        (FIXTURES / "provider-cases.json").read_text(encoding="utf-8")
    )
    assert len(cases) >= 19
    assert {case["surface_class"] for case in cases} == {
        "organization-standards",
        "framework-library",
        "architecture-reference",
        "agent-skills-reference",
    }
    for case in cases:
        result = evaluate_provider_case(case)
        assert result.status == case["expected"]["status"], case["id"]
        assert result.diagnostic == case["expected"]["diagnostic"], case["id"]
        assert result.baseline_continues is True
        if result.status != "ok":
            assert result.content_reads == ()


def test_unmanifested_independent_provider_reference_refuses_before_read() -> None:
    case = json.loads(
        (FIXTURES / "providers" / "eligible-unmanifested-reference.json").read_text(
            encoding="utf-8"
        )
    )
    result = evaluate_provider_case(case)
    assert result.status == "unavailable"
    assert result.topic_bodies == ()
    assert result.content_reads == ()
    assert result.baseline_continues is True
    assert result.diagnostic == "provider integrity unavailable"


def test_language_extension_families_are_distinct_and_unpopulated() -> None:
    contract = json.loads(
        (FIXTURES / "provider-contract.json").read_text(encoding="utf-8")
    )
    assert contract["language_extension_families"] == [
        "python-pytest",
        "typescript-node",
    ]
    seam = (
        Path(__file__).resolve().parents[2]
        / ".apm"
        / "skills"
        / "author-or-update-agent-skill"
        / "references"
        / "language-extension-seams.md"
    ).read_text(encoding="utf-8")
    assert "Neither has a language-specific topic body" in seam
    assert "foundation topics" in seam
