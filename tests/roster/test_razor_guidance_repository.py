"""Repository-level contracts for the cut-before-adding ladder.

The Core seed's own half of this contract lives in
`packs/core/tests/pack/test_razor_guidance.py`. This suite owns the assertions
that must read above `packs/core` — this repository's curated root `AGENTS.md`
and the published Core explanation — plus the cross-artifact check that the
ladder was adopted in exactly the two deliberate places.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED_AGENTS = ROOT / "packs" / "core" / "seeds" / "AGENTS.md"
ROOT_AGENTS = ROOT / "AGENTS.md"
CORE_GUIDE = ROOT / "guides" / "core" / "explanation" / "core-pack.md"

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


def _section(text: str, heading: str) -> str:
    """Return the body of ``heading`` up to the next same-or-shallower heading."""
    start = text.index(heading) + len(heading)
    match = re.search(r"\n#{2,3} ", text[start:])
    end = start + match.start() if match else len(text)
    return text[start:end]


def _numbered_rungs(text: str) -> list[tuple[str, str]]:
    """Return ``(number, body)`` for every top-level 1–7 ordered-list item."""
    return re.findall(
        r"(?ms)^[ \t]*([1-7])\. (.*?)(?=^[ \t]*[1-7]\. |\Z)", text
    )


def _normalized(text: str) -> str:
    """Collapse whitespace so wrapped prose compares as one line."""
    return " ".join(text.split())


def test_curated_root_preserves_the_seven_rung_contract() -> None:
    root = _section(ROOT_AGENTS.read_text(encoding="utf-8"), "## Coding conventions")

    rungs = _numbered_rungs(root)
    assert [number for number, _ in rungs] == list("1234567")
    bodies = [_normalized(body) for _, body in rungs]
    for body, required in zip(bodies, LADDER_MARKERS, strict=True):
        assert required in body
    whole = _normalized(root)
    assert "first sufficient" in whole
    assert "bounded" in whole
    assert "obvious" in whole
    for alternatives in NEVER_CUT_ALTERNATIVES:
        assert any(term in whole for term in alternatives)


def test_changed_primitives_have_only_the_two_deliberate_ladders() -> None:
    seed = SEED_AGENTS.read_text(encoding="utf-8")
    root = ROOT_AGENTS.read_text(encoding="utf-8")
    guide = CORE_GUIDE.read_text(encoding="utf-8")

    assert len(_numbered_rungs(seed)) == 7
    assert len(_numbered_rungs(root)) == 7
    assert not all(marker in guide for marker in LADDER_MARKERS)
    assert _section(seed, "### Cut before adding") != _section(
        root, "## Coding conventions"
    )
    combined = seed + root + guide
    assert "dynamic rule loader" not in combined.lower()


def test_root_guidance_bounds_claims_and_completion_communication() -> None:
    text = _normalized(ROOT_AGENTS.read_text(encoding="utf-8"))
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


def test_core_explanation_places_razor_at_the_right_principle_level() -> None:
    text = CORE_GUIDE.read_text(encoding="utf-8")
    razor = _normalized(_section(text, "### Razor: cut before adding"))

    assert "Razor product principle" in razor
    assert "first sufficient solution" in razor
    assert "smallest obvious, maintainable change" in razor
    assert "never removes" in razor
    assert "not a fifth admission principle" in razor
    assert "unrelated" in razor
    assert "tech-site" in razor
