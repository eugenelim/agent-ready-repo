"""Repository-level provenance checks for the architect OKF corpus."""

from __future__ import annotations

import re
import tempfile
import tomllib
from pathlib import Path

import yaml
from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "packs" / "architect"
CONCEPT_ROOT = PACK_ROOT / "okf" / "architecture-lenses" / "concepts"
PACKET_ROOT = (
    REPO_ROOT / "docs" / "product" / "research" / "architecture-assessment-corpus" / "concepts"
)
AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "architect-assessment"
    / "notes"
    / "architecture-knowledge-audit.md"
)

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


def _expected_concepts() -> set[str]:
    """Return the pack-owned concept paths that require research packets."""

    return {
        path.relative_to(CONCEPT_ROOT).as_posix()
        for path in CONCEPT_ROOT.rglob("*.md")
        if path.name != "index.md"
    }


def test_source_packets_are_one_to_one_and_claim_traceable() -> None:
    """Every shipped concept has a living, independently sourced packet."""

    expected = _expected_concepts()
    actual = {
        path.relative_to(PACKET_ROOT).as_posix()
        for path in PACKET_ROOT.rglob("*.md")
        if path.name != "index.md"
    }
    assert actual == expected

    for relative in sorted(expected):
        packet_text = (PACKET_ROOT / relative).read_text(encoding="utf-8")
        packet_metadata = _frontmatter(packet_text)
        assert packet_metadata["type"] == "architecture-corpus-source-packet", relative
        assert packet_metadata["concept_path"] == f"concepts/{relative}", relative
        assert packet_metadata["confidence"] in {"high", "moderate", "low"}, relative
        assert packet_metadata["lifecycle"] == "living", relative
        assert "## Material claims" in packet_text, relative
        assert "## Counter-evidence and downgrade factors" in packet_text, relative
        assert "## Licensing and reuse" in packet_text, relative
        assert "## Freshness" in packet_text, relative

        source_ids = set(re.findall(r"^- (S\d+):", packet_text, re.MULTILINE))
        claim_rows = re.findall(
            r"^\|\s*([A-Z][A-Z0-9-]*\d[A-Za-z]?)\s*\|\s*([^|]+)\|\s*([^|]+)\|$",
            packet_text,
            re.MULTILINE,
        )
        packet_claim_ids = {claim_id for claim_id, _, _ in claim_rows}
        assert packet_claim_ids, f"{relative}: no material claim identifiers"
        for claim_id, synthesis, sources in claim_rows:
            assert synthesis.strip(), f"{relative}: {claim_id} has no synthesis"
            cited_ids = {item.strip() for item in sources.split(",")}
            assert cited_ids and cited_ids <= source_ids, (
                f"{relative}: {claim_id} has unresolved sources {cited_ids - source_ids}"
            )

        concept_text = (CONCEPT_ROOT / relative).read_text(encoding="utf-8")
        concept_metadata = _frontmatter(concept_text)
        concept_claim_ids = concept_metadata.get("research_claims")
        assert isinstance(concept_claim_ids, list), f"{relative}: no research_claims"
        assert set(concept_claim_ids) == packet_claim_ids, (
            f"{relative}: concept and packet claim IDs diverge"
        )
        trace_ids = set(
            re.findall(r"`([^`]+)`", concept_text.split("Research claim trace:", 1)[1])
        )
        assert trace_ids == packet_claim_ids, f"{relative}: prose trace diverges"

        urls = set(re.findall(r"https://[^)\s]+", packet_text))
        if packet_metadata["confidence"] in {"high", "moderate"}:
            assert len(urls) >= 3, f"{relative}: expected three independent sources"


def test_architecture_knowledge_audit_records_migrated_pack_references() -> None:
    """The migration audit explains every removed local reference."""

    audit = AUDIT_PATH.read_text(encoding="utf-8")
    for filename in MOVED_LOCAL_REFERENCES:
        assert filename in audit
    assert "unchanged diagram/output concern" in audit


def test_every_installed_adapter_resolves_the_same_pack_progressive_router() -> None:
    """Real adapter projection keeps assessment and its knowledge router together."""

    contract = load_contract(REPO_ROOT / "contracts" / "adapter.toml")
    pack = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    adapters = pack["pack"]["install"]["allowed-adapters"]
    selected_concepts = {
        "concepts/foundations/evidence-confidence-and-coverage.md",
        "concepts/system-shapes/layered-and-modular-application.md",
        "concepts/workload-lenses/genai-agentic/tool-authorization-and-credentials.md",
    }

    for adapter in adapters:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "installed"
            ADAPTERS[adapter](PACK_ROOT, contract, output)
            assess = next(
                path
                for path in output.rglob("SKILL.md")
                if path.parent.name == "architect-assess"
            )
            router = assess.parent.parent / "architecture-lenses-reference"
            assert router.joinpath("SKILL.md").is_file(), adapter
            index = router / "references" / "okf" / "index.md"
            assert index.is_file(), adapter
            assess_text = assess.read_text(encoding="utf-8")
            assert "../architecture-lenses-reference/references/okf/index.md" in assess_text
            for relative in selected_concepts:
                assert router.joinpath("references", "okf", relative).is_file(), (
                    adapter,
                    relative,
                )
