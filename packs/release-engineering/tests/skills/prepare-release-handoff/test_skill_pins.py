"""Pin the collector's portable procedure and authority limits."""

from pathlib import Path

SKILL = Path(__file__).resolve().parents[3] / ".apm/skills/prepare-release-handoff/SKILL.md"


def test_direct_path() -> None:
    """The skill names its command, unchanged outcomes and non-execution rule."""
    text = SKILL.read_text()
    for required in (
        "name: prepare-release-handoff", "description: Use to", "`ready`, exit 0",
        "`incomplete`, exit 1", "`error`, exit 2", "status and gaps unchanged",
        "collect_evidence.py collect", "--policy trusted-policy.json",
        "--output candidate.yaml", "Missing\nbuild, test or plan work is never executed implicitly",
        "no admission or deployment authority", "External locators are never fetched",
        "request cannot supply or override", "validator-unavailable", "install-validator",
        "optional additions only after", "refusal or failed check stops the step",
        "works without core, repo-governance or a work-loop event",
    ):
        assert required in text
    for forbidden in ("ADR-", "RFC-", "AC-", "docs/specs/", "G4", "token saving"):
        assert forbidden not in text
