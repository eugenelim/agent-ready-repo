"""Contract tests for the architect pack's reference-only OKF corpus."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = PACK_ROOT / "okf" / "architecture-lenses"
CONCEPT_ROOT = BUNDLE_ROOT / "concepts"
ROUTER_ROOT = PACK_ROOT / ".apm" / "skills" / "architecture-lenses-reference"
GENERATED_ROOT = ROUTER_ROOT / "references" / "okf"

EXPECTED_CONCEPTS = {
    "foundations/evidence-confidence-and-coverage.md",
    "foundations/boundaries-and-current-state-views.md",
    "foundations/quality-attribute-scenarios.md",
    "foundations/tradeoffs-sensitivity-and-evolution.md",
    "foundations/decisions-constraints-and-cross-cutting-concerns.md",
    "enterprise-knowledge/source-detection-confidence-and-conflicts.md",
    "enterprise-knowledge/business-domain-and-meaning.md",
    "enterprise-knowledge/current-system-landscape.md",
    "enterprise-knowledge/interfaces-and-contracts.md",
    "enterprise-knowledge/operational-reality.md",
    "enterprise-knowledge/constraints-and-standards.md",
    "enterprise-knowledge/local-patterns-and-reference-architectures.md",
    "enterprise-knowledge/decisions-and-rationale.md",
    "enterprise-knowledge/in-flight-work-and-roadmap.md",
    "operating-model-patterns/governance-ownership-and-team-patterns.md",
    "operating-model-patterns/provider-and-platform-operating-models.md",
    "operating-model-patterns/delivery-runtime-and-development-patterns.md",
    "assessment-intents/baseline-and-understanding.md",
    "assessment-intents/hardening-and-risk-reduction.md",
    "assessment-intents/optimize-current-outcomes.md",
    "assessment-intents/growth-and-scale-readiness.md",
    "assessment-intents/transformation-and-modernization.md",
    "assessment-intents/rationalization-disposition-and-due-diligence.md",
    "quality-lenses/reliability-resilience-and-recovery.md",
    "quality-lenses/performance-scalability-and-capacity.md",
    "quality-lenses/security-privacy-and-trust-boundaries.md",
    "quality-lenses/operability-observability-and-supportability.md",
    "quality-lenses/maintainability-modularity-and-evolvability.md",
    "quality-lenses/data-integrity-lifecycle-and-governance.md",
    "quality-lenses/cost-and-resource-efficiency.md",
    "quality-lenses/testability-delivery-and-change-safety.md",
    "system-shapes/library-sdk-and-cli.md",
    "system-shapes/layered-and-modular-application.md",
    "system-shapes/client-server.md",
    "system-shapes/distributed-services.md",
    "system-shapes/event-driven-and-streaming.md",
    "system-shapes/monorepo-platform-and-infrastructure.md",
    "workload-lenses/transactional-request-response.md",
    "workload-lenses/background-batch-and-scheduled-work.md",
    "workload-lenses/data-analytics-and-ml.md",
    "workload-lenses/knowledge-search-and-retrieval.md",
    "workload-lenses/serverless.md",
    "workload-lenses/genai-agentic/model-access-and-policy.md",
    "workload-lenses/genai-agentic/durable-run-state-and-recovery.md",
    "workload-lenses/genai-agentic/tool-authorization-and-credentials.md",
    "workload-lenses/genai-agentic/knowledge-provenance-and-isolation.md",
    "workload-lenses/genai-agentic/evaluation-and-observability.md",
}

REQUIRED_SECTIONS = (
    "## Scope and routing signals",
    "## Decisions and minimum evidence",
    "## Architectural questions",
    "## Mechanisms and trade-offs",
    "## Evidence and counter-evidence",
    "## Failure modes and false positives",
    "## Confirmation scenarios",
    "## Related concepts and escalation",
    "## Provenance and lifecycle",
)

EXPECTED_INDEXES = {
    "index.md",
    "concepts/assessment-intents/index.md",
    "concepts/enterprise-knowledge/index.md",
    "concepts/foundations/index.md",
    "concepts/operating-model-patterns/index.md",
    "concepts/quality-lenses/index.md",
    "concepts/system-shapes/index.md",
    "concepts/workload-lenses/index.md",
    "concepts/workload-lenses/genai-agentic/index.md",
}

FROZEN_ROUTING_CASES = {
    "library baseline": {
        "foundations/evidence-confidence-and-coverage.md",
        "assessment-intents/baseline-and-understanding.md",
        "system-shapes/library-sdk-and-cli.md",
    },
    "layered hardening": {
        "foundations/evidence-confidence-and-coverage.md",
        "assessment-intents/hardening-and-risk-reduction.md",
        "system-shapes/layered-and-modular-application.md",
        "quality-lenses/security-privacy-and-trust-boundaries.md",
    },
    "client-server optimization": {
        "assessment-intents/optimize-current-outcomes.md",
        "system-shapes/client-server.md",
        "quality-lenses/performance-scalability-and-capacity.md",
    },
    "distributed growth": {
        "assessment-intents/growth-and-scale-readiness.md",
        "system-shapes/distributed-services.md",
        "quality-lenses/reliability-resilience-and-recovery.md",
    },
    "event transformation": {
        "assessment-intents/transformation-and-modernization.md",
        "system-shapes/event-driven-and-streaming.md",
        "workload-lenses/background-batch-and-scheduled-work.md",
    },
    "platform disposition": {
        "assessment-intents/rationalization-disposition-and-due-diligence.md",
        "system-shapes/monorepo-platform-and-infrastructure.md",
        "operating-model-patterns/governance-ownership-and-team-patterns.md",
    },
    "data and knowledge": {
        "workload-lenses/data-analytics-and-ml.md",
        "workload-lenses/knowledge-search-and-retrieval.md",
        "quality-lenses/data-integrity-lifecycle-and-governance.md",
    },
    "serverless agent": {
        "workload-lenses/serverless.md",
        "workload-lenses/genai-agentic/model-access-and-policy.md",
        "workload-lenses/genai-agentic/tool-authorization-and-credentials.md",
    },
}

MOVED_LOCAL_REFERENCES = {
    "cloud-primitives.md",
    "cross-cutting-questions.md",
    "lens-genai-agentic.md",
    "lens-serverless.md",
    "quality-attribute-scenarios.md",
    "tradeoffs-and-sensitivity.md",
    "well-architected-pillars.md",
}


def _frontmatter(text: str) -> dict[str, object]:
    """Return the closed YAML frontmatter from a Markdown document."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_corpus_has_the_frozen_ontology() -> None:
    actual = {
        path.relative_to(CONCEPT_ROOT).as_posix()
        for path in CONCEPT_ROOT.rglob("*.md")
        if path.name != "index.md"
    }
    assert actual == EXPECTED_CONCEPTS


def test_every_concept_is_reference_only_and_investigation_shaped() -> None:
    for relative in sorted(EXPECTED_CONCEPTS):
        text = (CONCEPT_ROOT / relative).read_text(encoding="utf-8")
        metadata = _frontmatter(text)
        assert metadata["type"] == "Reference", relative
        assert metadata["status"] in {"Active", "Deprecated"}, relative
        assert metadata["license"] == "Apache-2.0 OR MIT", relative
        assert "x-agentbundle" not in metadata, relative
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{relative}: missing {section}"
        for forbidden in ("executor:", "attester:", "remote:", "tools:"):
            assert forbidden not in text, f"{relative}: unsafe authority {forbidden}"


def test_pack_declares_one_reference_router_without_projection_entries() -> None:
    pack = (PACK_ROOT / "pack.toml").read_text(encoding="utf-8")
    assert '[pack.metadata.okf]' in pack
    assert 'profile = "agentbundle-okf/v1"' in pack
    assert 'id = "architecture-lenses"' in pack
    assert 'path = "okf/architecture-lenses"' in pack
    assert '"router-skill" = "architecture-lenses-reference"' in pack
    assert "projected-concepts" not in pack


def test_architect_version_is_synchronized() -> None:
    # STUB: AC8 — pack and plugin release surfaces move together. Assert the
    # invariant, not a literal, for the reasons recorded on the
    # catalogue-curation counterpart. The third surface — the topmost changelog
    # heading — lives in tests/roster/ because a pack test may not read above
    # its own pack.
    pack = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    plugin = json.loads(
        (PACK_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert plugin["version"] == pack["pack"]["version"]


def test_generated_router_is_hierarchical_reference_only_and_manifest_owned() -> None:
    router = (ROUTER_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "generated-by: compile-okf agentbundle-okf/v1" in router
    assert "Read `references/okf/index.md` first" in router
    assert "do not load the full bundle up front" in router
    for forbidden in ("executor:", "attester:", "remote:", "tools:"):
        assert forbidden not in router

    actual_indexes = {
        path.relative_to(GENERATED_ROOT).as_posix()
        for path in GENERATED_ROOT.rglob("index.md")
    }
    assert actual_indexes == EXPECTED_INDEXES

    manifest = json.loads((PACK_ROOT / ".okf-generated.json").read_text(encoding="utf-8"))
    managed = manifest["managed"]
    references = [entry for entry in managed if entry["kind"] == "okf-reference"]
    indexes = [entry for entry in managed if entry["kind"] == "okf-index"]
    routers = [entry for entry in managed if entry["kind"] == "okf-router"]
    assert len(references) == len(EXPECTED_CONCEPTS)
    assert len(indexes) == len(EXPECTED_INDEXES)
    assert len(routers) == 1
    assert all(
        entry["source_path"] == "okf/architecture-lenses"
        or entry["source_path"].startswith("okf/architecture-lenses/")
        for entry in managed
    )
    assert all(entry["output_path"].startswith(".apm/skills/architecture-lenses-reference/") for entry in managed)


def test_frozen_routes_are_real_bounded_and_intent_sensitive() -> None:
    generated_concepts = {
        path.relative_to(GENERATED_ROOT / "concepts").as_posix()
        for path in (GENERATED_ROOT / "concepts").rglob("*.md")
        if path.name != "index.md"
    }
    for case, concepts in FROZEN_ROUTING_CASES.items():
        assert 2 <= len(concepts) <= 4, case
        for relative in concepts:
            assert relative in EXPECTED_CONCEPTS, f"{case}: fabricated path {relative}"
            assert relative in generated_concepts, case

    topology = "system-shapes/layered-and-modular-application.md"
    intent_paths = {
        "assessment-intents/baseline-and-understanding.md",
        "assessment-intents/hardening-and-risk-reduction.md",
        "assessment-intents/optimize-current-outcomes.md",
        "assessment-intents/growth-and-scale-readiness.md",
        "assessment-intents/transformation-and-modernization.md",
        "assessment-intents/rationalization-disposition-and-due-diligence.md",
    }
    for intent_path in intent_paths:
        assert topology in EXPECTED_CONCEPTS
        assert intent_path in EXPECTED_CONCEPTS

    intent_texts = {
        path.read_text(encoding="utf-8")
        for path in CONCEPT_ROOT.rglob("*.md")
        if path.relative_to(CONCEPT_ROOT).as_posix() in intent_paths
    }
    assert len(intent_texts) == len(intent_paths)


def test_design_and_review_route_shared_knowledge_without_local_duplicates() -> None:
    for consumer in ("architect-design", "architect-review"):
        skill_root = PACK_ROOT / ".apm" / "skills" / consumer
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        assert "../architecture-lenses-reference/references/okf/index.md" in skill
        assert "architecture lenses unavailable" in skill
        for filename in MOVED_LOCAL_REFERENCES:
            assert not (skill_root / "references" / filename).exists(), (consumer, filename)
