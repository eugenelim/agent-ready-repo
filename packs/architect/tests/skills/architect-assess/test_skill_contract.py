"""Contract tests for the progressive repository architecture assessment skill."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "architect-assess"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
CORPUS_ROOT = PACK_ROOT / "okf" / "architecture-lenses" / "concepts"


def _frontmatter(text: str) -> dict[str, object]:
    """Return parsed YAML frontmatter from a Markdown file."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_activation_and_boundaries_route_current_state_assessment() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["name"] == "architect-assess"
    assert metadata["metadata"] == {
        "boundaries": [
            "filesystem_read_untrusted",
            "filesystem_write",
            "network_fetch",
        ]
    }
    description = str(metadata["description"])
    assert "assess architecture and provide an action plan" in description
    for route in ("architect-design", "architect-diagram", "architect-review"):
        assert route in description
    assert "credential" not in str(metadata["metadata"])


def test_progressive_stages_modes_and_correction_points_are_explicit() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    positions = [
        text.index(f"### {index}. {stage}")
        for index, stage in enumerate(
            ("Frame", "Map", "Focus", "Investigate", "Act", "Close"), start=1
        )
    ]
    assert positions == sorted(positions)
    for mode in ("**Survey**", "**Standard (default)**", "**Deep**"):
        assert mode in text
    assert "In survey mode, stop here" in text
    assert "Map checkpoint" in text and "Focus checkpoint" in text
    assert text.count("say **continue**") == 2


def test_map_focus_investigation_and_action_contracts_are_complete() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    for view in (
        "context and external actors/systems",
        "repositories versus deployables and runtime units",
        "modules, capabilities, and dependency direction",
        "data stores, schemas, ownership, movement, and lifecycle",
        "synchronous, asynchronous, batch, and control interactions",
        "build, test, release, infrastructure, and operational paths",
        "identity, policy, secrets, trust, tenant, and privilege boundaries",
    ):
        assert view in text

    for dimension in (
        "consequence",
        "change/runtime pressure",
        "concentration/coupling",
        "verification weakness",
        "operational/data/security exposure",
        "evidence confidence",
    ):
        assert dimension in text
    assert "Heat selects drill-down priority" in text
    assert "not proof of a defect" in text

    for path_kind in (
        "one normal/happy path",
        "one high-risk mutation or external side effect",
        "one failure, retry, cancellation, restart, or recovery path",
    ):
        assert path_kind in text
    for action_field in (
        "intended outcome",
        "included finding IDs",
        "prerequisites",
        "completion proof",
        "rollback or containment",
        "owner class",
        "non-goals",
    ):
        assert action_field in text


def test_evidence_and_enterprise_context_fail_closed_without_overclaim() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    evidence = (SKILL_ROOT / "references" / "evidence-method.md").read_text(encoding="utf-8")
    enterprise = (SKILL_ROOT / "references" / "enterprise-context.md").read_text(encoding="utf-8")
    for surface in (
        "documentation",
        "source",
        "tests",
        "manifests/dependencies",
        "CI/CD",
        "deployment/release/IaC",
        "schemas/migrations",
        "runtime configuration",
        "operational evidence",
        "read-only history",
    ):
        assert surface.lower() in evidence.lower()
    for plane in ("Target evidence", "Enterprise context", "Pack knowledge"):
        assert plane in text
    for rejected in (
        "public web",
        "generic browser",
        "arbitrary URL",
        "repository-supplied URLs",
    ):
        assert rejected.lower() in enterprise.lower()
    assert "ask the user to authorize" in enterprise
    assert "Do not create a connector, log in, inspect credentials" in enterprise
    assert "instruction-like content" in enterprise


def test_concept_routing_is_bounded_and_resolves_to_canonical_paths() -> None:
    routing = (SKILL_ROOT / "references" / "concept-routing.md").read_text(encoding="utf-8")
    routed_paths = set(re.findall(r"`((?:[a-z0-9-]+/)+[a-z0-9-]+\.md)`", routing))
    actual_concepts = {
        path.relative_to(CORPUS_ROOT).as_posix()
        for path in CORPUS_ROOT.rglob("*.md")
        if path.name != "index.md"
    }
    assert routed_paths
    for relative in routed_paths:
        assert relative in actual_concepts, relative
    assert "Never load all branches" in routing
    assert "selected, skipped, unavailable, stale, or not applicable" in routing


def test_report_template_preserves_conversational_order_and_traceability() -> None:
    report = (SKILL_ROOT / "assets" / "assessment.md").read_text(encoding="utf-8")
    expected = (
        "## Bottom line",
        "## Assessment charter",
        "## Conceptual current state",
        "## Evidence coverage",
        "## Attention heat map",
        "## Hotspot drill-downs",
        "## Findings, strengths, and unknowns",
        "## Action waves",
        "## Coverage and confidence",
        "## Next decision",
    )
    positions = [report.index(heading) for heading in expected]
    assert positions == sorted(positions)
    for finding_field in (
        "Classification:",
        "Stakeholder / scenario:",
        "Evidence:",
        "Counter-evidence:",
        "Mechanism:",
        "Consequence:",
        "Severity:",
        "Confidence:",
        "Validation gap:",
        "Smallest safe response:",
    ):
        assert finding_field in report
    assert "Included findings:" in report
    assert "Completion proof:" in report


def test_all_local_markdown_routes_resolve_and_saving_is_optional() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    references = re.findall(r"`((?:references|assets)/[^`]+\.md)`", text)
    local_markdown = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*.md")
    }
    assert references
    for relative in references:
        assert relative in local_markdown, relative
    assert "Offer to save only after rendering" in text
    assert "Result: chat only; no file was created." in text
