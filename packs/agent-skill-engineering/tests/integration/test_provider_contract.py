"""Shared semantic fixtures for provider and consumer behavior."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
# Anchored literally so every path this suite opens is statically confined.
PROVIDER_CONTRACT_MD = (
    Path(__file__).resolve().parents[2]
    / ".apm"
    / "skills"
    / "author-or-update-agent-skill"
    / "references"
    / "provider-contract.md"
)
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


def _refuse(
    diagnostic: str,
    *,
    status: str = "unavailable",
    reads: tuple[str, ...] = (),
    baseline_continues: bool = True,
) -> ProviderResult:
    """Return a fail-closed provider result.

    `reads` carries whatever the evaluation had already read when it refused,
    rather than a hard-coded empty tuple — otherwise a read-before-refusal is
    indistinguishable from a refusal that read nothing, and AC18's
    no-read-before-refusal property has no falsifiable artifact.
    """

    return ProviderResult(status, (), reads, baseline_continues, diagnostic)


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

    # AC13 separates two things a refusal must not conflate: an optional
    # provider being unusable (baseline continues) and the consumer's own
    # baseline safety check failing (baseline stops).
    baseline_continues = not bool(case.get("baseline_safety_failure", False))
    request = case.get("request")
    if not _request_is_valid(request):
        return _refuse(
            "knowledge provider request out of scope",
            status="out-of-scope",
            baseline_continues=baseline_continues,
        )
    candidates = case.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return _refuse(
            "knowledge provider unavailable",
            baseline_continues=baseline_continues,
        )
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
        return _refuse(
            "knowledge provider ambiguous",
            baseline_continues=baseline_continues,
        )
    if not eligible:
        if integrity_failure:
            return _refuse(
                "provider integrity unavailable",
                baseline_continues=baseline_continues,
            )
        if stale:
            return _refuse(
                "knowledge provider stale",
                status="stale-profile",
                baseline_continues=baseline_continues,
            )
        return _refuse(
            "knowledge provider ineligible",
            baseline_continues=baseline_continues,
        )

    response = case.get("response")
    if not isinstance(response, dict):
        return _refuse(
            "knowledge provider unavailable",
            baseline_continues=baseline_continues,
        )
    if not _response_is_valid(
        response,
        selected=eligible[0],
        maximum=request.get("max_topics", 3),
    ):
        return _refuse(
            "knowledge provider response refused",
            baseline_continues=baseline_continues,
        )
    status = response.get("status")
    if status != "ok":
        return ProviderResult(
            str(status), (), (), baseline_continues, response.get("diagnostic")
        )
    provider_reads = case.get("provider_reads")
    if not isinstance(provider_reads, list):
        return _refuse(
            "knowledge provider response refused",
            baseline_continues=baseline_continues,
        )
    reads: list[str] = []
    for reference in provider_reads:
        if not isinstance(reference, dict) or set(reference) != {
            "path",
            "digest_matches",
            "manifest_member",
        }:
            return _refuse(
                "knowledge provider response refused",
                reads=tuple(reads),
                baseline_continues=baseline_continues,
            )
        # Membership and digest are verified *before* the body is read, so a
        # failure here refuses with nothing recorded in `reads`.
        if not reference.get("manifest_member") or not reference.get("digest_matches"):
            return _refuse(
                "provider integrity unavailable",
                reads=tuple(reads),
                baseline_continues=baseline_continues,
            )
        reads.append(reference["path"])
    topics = response["topic_ids"]
    bodies = tuple(response["guidance"][topic] for topic in topics)
    return ProviderResult(
        str(status), bodies, tuple(reads), baseline_continues,
        response.get("diagnostic"),
    )


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
        # Case-driven, not a constant: AC13 lets an independently applicable
        # baseline safety failure stop the task even though provider failure
        # never does, and `baseline-safety-failure` exercises that branch.
        expected_baseline = case["expected"].get("baseline_continues", True)
        assert result.baseline_continues is expected_baseline, case["id"]
        if result.status != "ok":
            assert result.content_reads == (), case["id"]


def test_a_read_before_the_integrity_check_is_detectable() -> None:
    """The no-read-before-refusal assertion must be able to fail.

    `content_reads` is accumulated as each reference passes its manifest and
    digest check, so a case whose reference fails integrity refuses with an
    empty tuple, while one that passes records the path. If the oracle ever
    read a body before checking, the refusing case would carry that path and
    the suite would redden — which is what makes the assertion evidence.
    """

    refused = json.loads(
        (FIXTURES / "providers" / "eligible-unmanifested-reference.json").read_text(
            encoding="utf-8"
        )
    )
    assert evaluate_provider_case(refused).content_reads == ()

    # Same case with integrity satisfied: the very same path is now recorded,
    # proving the empty tuple above is a measured outcome and not a constant.
    admitted = json.loads(json.dumps(refused))
    for reference in admitted["provider_reads"]:
        reference["manifest_member"] = True
        reference["digest_matches"] = True
    result = evaluate_provider_case(admitted)
    assert result.content_reads == tuple(
        reference["path"] for reference in admitted["provider_reads"]
    )
    assert result.content_reads != ()


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


def test_shipped_contract_prose_states_the_same_bounds_as_the_fixture() -> None:
    """The agent reads the prose; the suite checks the fixture. Bind them.

    `provider-contract.md` is the artifact an agent actually follows, and until
    now no test read its content — only asserted the route existed. The plan
    designates the fixture table as "the conformance source", so the two must
    not be able to drift apart silently.
    """

    contract = json.loads(
        (FIXTURES / "provider-contract.json").read_text(encoding="utf-8")
    )
    prose = " ".join(PROVIDER_CONTRACT_MD.read_text(encoding="utf-8").split())

    assert contract["contract_version"] in prose
    for task_kind in contract["task_kinds"]:
        assert f"`{task_kind}`" in prose, task_kind
    for status in contract["response_statuses"]:
        assert f"`{status}`" in prose, status

    question = contract["request_constraints"]["question"]
    assert (
        f"{question['minimum_length']} through {question['maximum_length']}" in prose
    )
    capabilities = contract["request_constraints"]["capabilities"]
    assert f"{capabilities['maximum_items']} unique" in prose
    # The prose spells small numbers; the fixture stores them. Bind the two so
    # a change to either has to be made in both.
    words = {1: "one", 2: "two", 3: "three"}
    cap = contract["max_topics"]
    assert (
        f"{words[cap['minimum']]} through {words[cap['maximum']]}, "
        f"default {words[cap['default']]}" in prose
    )


def test_language_extension_families_are_distinct_and_populated() -> None:
    """AC7: every shipped availability-or-count statement matches the admitted set.

    Retargeted. The families are populated now, so the assertion that once
    pinned their absence would pin a sentence the corpus contradicts. What is
    checkable instead is agreement: no shipped file may state a topic count the
    corpus does not have, or assert an absence it no longer has. Reverting any
    one of the five reconciled statements reddens this test.
    """
    pack_root = Path(__file__).resolve().parents[2]
    contract = json.loads(
        (FIXTURES / "provider-contract.json").read_text(encoding="utf-8")
    )
    assert contract["language_extension_families"] == [
        "python-pytest",
        "typescript-node",
    ]

    admitted = {
        path.stem
        for path in (
            pack_root / "okf" / "agent-skill-engineering-foundation" / "concepts"
        ).glob("*.md")
        if path.is_file()
    }
    assert {"python-and-pytest", "typescript-node-and-javascript-test-runners"} <= admitted

    skills = pack_root / ".apm" / "skills"
    shipped = {
        "author SKILL.md": skills / "author-or-update-agent-skill" / "SKILL.md",
        "review SKILL.md": skills / "review-or-optimize-agent-skill" / "SKILL.md",
        "seam reference": skills
        / "author-or-update-agent-skill"
        / "references"
        / "language-extension-seams.md",
        "pack README": pack_root / "README.md",
    }

    # No shipped sentence may assert an absence the corpus no longer has.
    absence_claims = (
        "unpopulated extension",
        "ships no language-specific",
        "language guidance unavailable",
        "Neither has a language-specific topic body",
        "not active foundation modes",
        "future extension families",
    )
    for label, path in shipped.items():
        # Collapsed, not raw. These are absence assertions over hard-wrapped
        # prose, so a claim spanning a line break can never match and the check
        # becomes evadable by reflowing: the same forbidden sentence reddens on
        # one line and passes across two. Two of the six members were already
        # dead this way. Matching the slice's own precedent for wrapped prose.
        body = " ".join(path.read_text(encoding="utf-8").split())
        for claim in absence_claims:
            assert claim not in body, (label, claim)

    # The README's count is stated in words and must equal the admitted set.
    words = {7: "Seven", 12: "Twelve", 13: "Thirteen"}
    readme = shipped["pack README"].read_text(encoding="utf-8")
    assert f"{words[len(admitted)]} governed topics" in readme, len(admitted)

    # Each language family's boundary reaches the reader of the seam reference.
    seam = shipped["seam reference"].read_text(encoding="utf-8")
    assert "version range" in seam
    assert "portable floor" in seam


def test_provider_pattern_failure_surfaces_conform_as_declared() -> None:
    """Each declared failure surface refuses in a class the contract admits.

    The mode is instructions rather than code, so there is no runtime guard to
    make fail. What is checkable is that every outcome declared for the four
    surfaces satisfies the same response validator an untrusted provider is held
    to -- a declared refusal that the contract would reject is a defect in the
    pattern, not in the caller.
    """
    fixture = json.loads(
        (FIXTURES / "provider-pattern-cases.json").read_text(encoding="utf-8")
    )
    assert fixture["schema_version"] == 1
    assert fixture["contract_version"] == CONTRACT_VERSION

    cases = fixture["cases"]
    assert len(cases) == 4
    assert len({case["id"] for case in cases}) == 4
    # Each surface refuses in its own class; a shared class would let one
    # declaration stand in for four distinct failures.
    assert len({case["refusal_class"] for case in cases}) == 4

    selected = {"provider_id": fixture["provider_id"]}
    for case in cases:
        response = case["declared_response"]
        assert case["surface"]
        assert response["status"] != "ok", case["id"]
        assert _bounded_safe_text(response["diagnostic"]), case["id"]
        assert _response_is_valid(response, selected=selected, maximum=3), case["id"]
