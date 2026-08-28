"""Construction contracts for the Core seed's cut-before-adding guidance.

This suite is pack-local: it only inspects `packs/core/seeds/AGENTS.md`, the
portable ladder Core actually ships. The repository-level half of the same
contract — this repository's curated root `AGENTS.md` and the published Core
explanation — lives in `tests/roster/test_razor_guidance_repository.py`,
because a pack test may not climb above its owning pack.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SEED_AGENTS = PACK_ROOT / "seeds" / "AGENTS.md"

LADDER_MARKERS = (
    "not genuinely needed",
    "repository solution",
    "standard library",
    "native platform",
    "already-installed dependency",
    "one obvious line",
    "minimum correct",
)

NEVER_CUT_ALTERNATIVES = (
    ("trust-boundary validation", "validation at a trust boundary"),
    ("data-loss", "data loss"),
    ("security or privacy",),
    ("accessibility",),
    ("accepted requirement",),
    ("tests",),
    ("migrations",),
    ("documentation",),
    ("human approval",),
    ("policy",),
    ("platform restriction",),
)


def section(text: str, heading: str) -> str:
    """Return the body of ``heading`` up to the next same-or-shallower heading."""
    start = text.index(heading) + len(heading)
    match = re.search(r"\n#{2,3} ", text[start:])
    end = start + match.start() if match else len(text)
    return text[start:end]


def numbered_rungs(text: str) -> list[tuple[str, str]]:
    """Return ``(number, body)`` for every top-level 1–7 ordered-list item."""
    return re.findall(
        r"(?ms)^[ \t]*([1-7])\. (.*?)(?=^[ \t]*[1-7]\. |\Z)", text
    )


def normalized(text: str) -> str:
    """Collapse whitespace so wrapped prose compares as one line."""
    return " ".join(text.split())


def assert_seven_rung_contract(content: str) -> None:
    """Assert one guidance body carries the ladder in RFC-0099 order."""
    rungs = numbered_rungs(content)
    assert [number for number, _ in rungs] == list("1234567")
    bodies = [normalized(body) for _, body in rungs]
    for body, required in zip(bodies, LADDER_MARKERS, strict=True):
        assert required in body
    whole = normalized(content)
    assert "first sufficient" in whole
    assert "bounded" in whole
    assert "obvious" in whole
    for alternatives in NEVER_CUT_ALTERNATIVES:
        assert any(term in whole for term in alternatives)


def assert_claims_and_completion_communication(text: str) -> None:
    """Assert one guidance body bounds claims and ends receipts completely."""
    assert "claims that do not affect the accepted outcome" in text
    assert "named repository target" in text
    assert "one bounded read or search" in text
    assert "assumption" in text
    assert "discovery condition" in text or "condition to discover" in text
    assert "outcome" in text
    assert "routine tool narration" in text
    assert "changed state" in text
    assert "verification" in text
    assert "remaining work" in text
    assert "interactive updates" in text


def test_seed_preserves_the_seven_rung_contract() -> None:
    seed = section(SEED_AGENTS.read_text(encoding="utf-8"), "### Cut before adding")
    assert_seven_rung_contract(seed)


def test_seed_carries_exactly_one_ladder_without_a_rule_loader() -> None:
    seed = SEED_AGENTS.read_text(encoding="utf-8")
    assert len(numbered_rungs(seed)) == 7
    assert "dynamic rule loader" not in seed.lower()


def test_seed_bounds_claims_and_completion_communication() -> None:
    assert_claims_and_completion_communication(
        normalized(SEED_AGENTS.read_text(encoding="utf-8"))
    )
