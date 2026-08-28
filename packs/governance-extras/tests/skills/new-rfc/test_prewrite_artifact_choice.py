"""PLAN-time contract stub for the RFC pre-write choice."""

from pathlib import Path


SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "new-rfc" / "SKILL.md"

CHEAPER_ROUTES = (
    "skip",
    "reuse",
    "amend",
    "reference",
    "ADR",
    "spec",
    "PR",
    "issue",
    "design",
    "trial",
)


def test_artifact_choice_contract_precedes_all_rfc_effects() -> None:
    """Every cheaper route returns before RFC identity or filesystem work."""
    # STUB: AC1
    text = SKILL.read_text(encoding="utf-8")
    choice = text.find("Artifact choice")
    ordinal = text.find("Resolve the RFC ordinal")
    assert choice >= 0
    assert ordinal >= 0
    assert choice < ordinal
    contract = text[choice:ordinal]
    for route in CHEAPER_ROUTES:
        assert route in contract
    assert "return without resolving an ordinal" in contract
    assert "creating a directory" in contract
    assert "writing an index or RFC body" in contract
