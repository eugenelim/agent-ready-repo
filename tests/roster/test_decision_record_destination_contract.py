"""Construction tests for portable decision-record destination ordering."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "packs/governance-extras/.apm/skills/new-adr/SKILL.md"


def test_decision_record_resolution_precedes_ordinal_and_filename() -> None:
    """No ADR identity or index read is selected before the destination."""
    source = SKILL.read_text(encoding="utf-8")

    resolve_at = source.index(
        "1. **Resolve the `decision-record` destination before identity or reads.**"
    )
    ordinal_at = source.index("2. Find the next number **inside the resolved destination**")
    filename_at = source.index("3. Pick a kebab-case filename title")

    assert resolve_at < ordinal_at < filename_at
    assert "semantic-surface-resolution.v1" in source[resolve_at:ordinal_at]
    assert "python3 scripts/next-ordinal.py <resolved-decision-record-directory>" in source


def test_decision_record_resolution_is_fail_closed_and_portable() -> None:
    """Custom/external destinations win without turning defaults into policy."""
    source = SKILL.read_text(encoding="utf-8")
    resolution = " ".join(
        source[
            source.index("1. **Resolve the `decision-record`") : source.index(
                "2. Find the next number"
            )
        ].split()
    )

    assert "mandatory policy is refused, not an override" in resolution
    assert "one example is inference, not a convention" in resolution
    assert "`docs/adr/` is the catalogue fallback" in resolution
    assert "external locator remains external" in resolution
    assert "confirmation may correct the handoff evidence" in resolution
    assert (
        "cannot replace Wave 1 confinement or authorize a repository write"
        in resolution
    )
    assert "zero ordinal, index, directory, configuration, or artifact effects" in resolution


def test_existing_adr_method_and_write_gate_remain() -> None:
    """Wave 3 moves the destination gate, not the ADR method."""
    source = SKILL.read_text(encoding="utf-8")

    for marker in (
        "Frame the decision before drafting",
        "Decision summary",
        "Decision drivers",
        "Preview and confirm — the write gate",
        "wait for explicit confirmation",
        "Leave the status `Proposed`",
        "## Lifecycle after acceptance",
    ):
        assert marker in source
