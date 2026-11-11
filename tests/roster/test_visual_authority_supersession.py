"""ADR-0132 supersedes a contract-tier rule in a Shipped spec.

Lives in tests/roster/ because it reads docs/specs/, which
tools/lint-pack-test-boundary.py forbids a pack test from reaching.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERSEDED_SPEC = REPO_ROOT / "docs/specs/frontend-visual-authority/spec.md"


def test_the_superseded_rung_condition_rule_is_annotated() -> None:
    status = next(
        line
        for line in SUPERSEDED_SPEC.read_text(encoding="utf-8").splitlines()
        if line.startswith("- **Status:**")
    )
    flat = " ".join(status.split()).lower()
    assert "adr-0132" in flat, "AC-0008: Status does not name ADR-0132"
    assert "rung condition" in flat, "AC-0008: Status does not name the rule"
    assert "ac-0003a" in flat, "AC-0008: Status does not name the superseded criterion"
    # Appended, not edited in place. `everything else stands` is scoped per
    # clause, so the ADR-0130 clause keeps its own and the ADR-0132 clause ends
    # with its own; two occurrences is the documented two-supersession form.
    assert flat.count("everything else stands") == 2, (
        "AC-0008: expected one trailing phrase per supersession clause"
    )
    assert flat.index("adr-0130") < flat.index("adr-0132"), (
        "AC-0008: the ADR-0132 clause must be appended after the ADR-0130 one"
    )
