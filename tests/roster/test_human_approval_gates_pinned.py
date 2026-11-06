"""Pin the governance text that keeps spec-plan and human approval gates uncuttable.

Roster-owned: reads the RFC, the root AGENTS.md and the ADR above any one pack.
Each pin is proved red by running its assertion against a temporary copy with the
pinned text removed; the real files are never edited.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RFC = "docs/rfc/0099-cut-before-adding-and-artifact-shaping.md"
ADR = "docs/adr/0159-brief-level-runner-chains-slices-from-committed-records.md"
AGENTS = "AGENTS.md"
RFC_HEADING = "### 7. Preserve every spec-plan and human approval gate"
D10_PREFIX = "- **D10:**"


def _never_cut_bullet(text: str) -> str:
    """The `Never cut ...` bullet of AGENTS.md, up to the next top-level bullet or blank line."""
    match = re.search(r"^- Never cut .*?(?=^\s*$|^- )", text, re.MULTILINE | re.DOTALL)
    assert match is not None, "AGENTS.md has no `Never cut ...` bullet"
    return match.group(0)


def _check_rfc(root: Path) -> None:
    lines = (root / RFC).read_text(encoding="utf-8").splitlines()
    assert RFC_HEADING in lines, f"{RFC} lost the heading {RFC_HEADING!r}"


def _check_agents(root: Path) -> None:
    text = (root / AGENTS).read_text(encoding="utf-8")
    assert "human approval" in _never_cut_bullet(text), "the never-cut rule lost `human approval`"


def _check_adr(root: Path) -> None:
    lines = (root / ADR).read_text(encoding="utf-8").splitlines()
    assert any(line.startswith(D10_PREFIX) for line in lines), f"{ADR} lost its D10"


CHECKS = {
    "rfc-0099-heading": (_check_rfc, RFC, lambda t: t.replace(RFC_HEADING, "### 7. Preserve")),
    "agents-never-cut": (
        _check_agents,
        AGENTS,
        lambda t: t.replace("human approval", "approval"),
    ),
    "adr-0159-d10": (_check_adr, ADR, lambda t: t.replace(D10_PREFIX, "- **D-10:**")),
}


@pytest.mark.parametrize("name", sorted(CHECKS))
def test_real_tree_keeps_the_pinned_text(name: str) -> None:
    """The real RFC heading, never-cut rule and ADR decision are present."""
    check, _, _ = CHECKS[name]
    check(ROOT)


@pytest.mark.parametrize("name", sorted(CHECKS))
def test_pin_fails_when_text_is_removed(name: str, tmp_path: Path) -> None:
    """Each assertion fails against a temporary copy that lost its pinned text."""
    check, rel, mutate = CHECKS[name]
    original = (ROOT / rel).read_text(encoding="utf-8")
    mutated = mutate(original)
    assert mutated != original, "the mutation changed nothing, so the pin proves nothing"
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(mutated, encoding="utf-8")
    with pytest.raises(AssertionError):
        check(tmp_path)
