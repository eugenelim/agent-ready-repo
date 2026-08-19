"""Repository-shaped acceptance tests for the Wave 4 catalogue contracts."""

from __future__ import annotations

import re
from pathlib import Path

from agentbundle.catalogue_tooling.index_generator import generate_index

ROOT = Path(__file__).parents[2]
PUBLIC_SCHEMA = ROOT / "contracts" / "catalogue-index.schema.json"
BUNDLED_SCHEMA = (
    ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "catalogue-index.schema.json"
)


def _journey_format_section(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("## Journey format")
    end = text.find("\n## ", start + 3)
    return text[start:] if end == -1 else text[start:end]


def test_live_catalogue_indexes_every_manifest_pack() -> None:
    index = generate_index(ROOT)
    expected = {
        path.parent.name
        for path in (ROOT / "packs").glob("*/pack.toml")
        if not path.parent.name.startswith("_")
    }
    assert {pack["name"] for pack in index["packs"]} == expected  # type: ignore[index]
    with_journeys = {
        pack["name"] for pack in index["packs"] if pack["journeys"]  # type: ignore[index]
    }
    expected_journeys = {
        path.parent.name
        for path in (ROOT / "packs").glob("*/JOURNEY.md")
        if not path.parent.name.startswith("_")
    }
    assert expected_journeys
    assert with_journeys == expected_journeys


def test_public_and_bundled_schema_copies_are_byte_identical() -> None:
    assert PUBLIC_SCHEMA.read_bytes() == BUNDLED_SCHEMA.read_bytes()


def test_journey_format_section_is_portable_and_scaffolded() -> None:
    source = ROOT / "guides" / "_shared" / "reference" / "catalogue-authoring-standards.md"
    scaffold = (
        ROOT
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "_data"
        / "catalogue-scaffold"
        / "guides"
        / "_shared"
        / "reference"
        / "catalogue-authoring-standards.md"
    )
    source_section = _journey_format_section(source)
    scaffold_section = _journey_format_section(scaffold)

    assert source_section == scaffold_section
    assert "contracts/catalogue-index.schema.json" in source_section
    assert "not yet available" not in source_section.lower()
    for forbidden in (".github/workflows/", "docs/rfc/", "docs/adr/", "docs/specs/"):
        assert forbidden not in source_section
    assert re.search(r"(?i)\b(?:RFC|ADR)-\d{4}\b", source_section) is None
    assert re.search(r"(?i)\bmake\s+\S+", source_section) is None

    for match in re.finditer(r"\[[^]]+\]\(([^)]+)\)", scaffold_section):
        target = match.group(1).split("#", 1)[0]
        if not target or target.startswith(("#", "http://", "https://")):
            continue
        assert (scaffold.parent / target).resolve().is_file()
