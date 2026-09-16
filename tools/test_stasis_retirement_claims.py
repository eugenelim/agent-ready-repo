"""Published claims match what the loop does after ADR-0104.

ADR-0104 retired full mode's stasis stop. The halt was stated on four audiences
with different failure modes, and the two covered here are the ones a reader
outside the repository sees: the published guides, and the public pack page.

This suite lives in `tools/` rather than beside the pack because a pack test may
not read above its own pack, and these assertions span `guides/` and
`web/src/content/`. The absence sweep that keeps the retirement pinned lives
here too, for the same reason -- its corpus spans both trees plus the tracked
projections.

Every phrase asserted absent below existed in this tree before the retirement,
each in exactly one file. That matters: an assertion naming a string the subject
never emitted survives the mutation it was written to catch, which
`packs/core/.apm/skills/work-loop/references/mutation-proof.md` names as one of
four shapes that make a test unable to fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE_PACK_GUIDE = ROOT / "guides/core/explanation/core-pack.md"
PUBLIC_PACK_PAGE = ROOT / "web/src/content/packs/core.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


# ── AC-0004: no published surface asserts a halt ─────────────────────────────

RETIRED_CLAIMS = (
    "same findings twice = stop",
    "the loop stops and surfaces",
    "stops a third pass",
    "refuses to self-certify past a red gate or a repeated finding",
    "it stops at plan approval, unresolved boundaries, repeated findings",
    "stasis detection",
)

PUBLISHED_TREES = ("guides", "web/src/content")


def _published_markdown() -> list[Path]:
    files: list[Path] = []
    for tree in PUBLISHED_TREES:
        base = ROOT / tree
        assert base.is_dir(), f"published tree is missing: {tree}"
        files.extend(sorted(base.rglob("*.md")))
    assert files, "published corpus resolved to nothing — the sweep would pass vacuously"
    return files


@pytest.mark.parametrize("claim", RETIRED_CLAIMS)
def test_no_published_surface_asserts_the_retired_halt(claim: str) -> None:
    """One case per phrasing, because a joined assertion names only its first hit."""
    offenders = sorted(
        str(p.relative_to(ROOT))
        for p in _published_markdown()
        if claim in _flat(p).lower()
    )
    assert not offenders, (
        f"retired claim {claim!r} survives in: {offenders}. ADR-0104 retired the "
        "halt; a published surface still promising it is a false capability claim."
    )


# ── AC-0005: the comparison tables claim the cap, not the detection ──────────
#
# Two tables mark a capability present for this pack and absent for two named
# tools. Retiring the stop makes the detection half false. The cap half is true,
# survives this change untouched, and is still absent from both -- so the rows
# are re-pointed rather than withdrawn. No assertion can decide whether the
# replacement claim is honest; this one decides only that it matches.

@pytest.mark.parametrize(
    "row",
    (
        "| State-machine discipline with a mechanical iteration cap | — | ✓",
        "| Mechanical iteration cap | — | ✓ |",
    ),
)
def test_comparison_tables_claim_the_iteration_cap(row: str) -> None:
    assert row in _flat(CORE_PACK_GUIDE), (
        f"comparison row missing or reworded: {row!r}"
    )


def test_the_public_pack_page_states_no_retired_capability() -> None:
    """The page a prospective adopter reads before anything else."""
    flat = _flat(PUBLIC_PACK_PAGE).lower()
    for claim in ("stasis", "repeated findings, and pr merge"):
        assert claim not in flat, (
            f"public pack page still claims {claim!r} after ADR-0104"
        )
