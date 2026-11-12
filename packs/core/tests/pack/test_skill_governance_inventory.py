"""Both maintained AST09 sources distinguish records from host evidence."""

from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    PACK_ROOT / ".apm/skills/security-checklists/references/agentic-skills.md",
    PACK_ROOT / "okf/security-checklists/concepts/agentic-skills.md",
)


@pytest.mark.parametrize("source", SOURCES, ids=("runtime", "canonical-okf"))
def test_inventory_records_do_not_claim_missing_host_evidence(source: Path) -> None:
    """Ownership alone cannot discharge scan and execution evidence gaps."""
    text = source.read_text(encoding="utf-8")
    section = text.split("## Implementation checks", 1)[1].split("## Established-helper bypass", 1)[0]
    section = " ".join(section.split())
    for phrase in (
        "install marker", "state file", "identity/provenance",
        "per-file SHA-256 content hashes", "Scan status", "scanner or host",
        "execution evidence", "instructing skill version", "from the host",
        "Missing host evidence remains a governance gap",
        "assigning ownership is not compliance proof",
    ):
        assert phrase in section
