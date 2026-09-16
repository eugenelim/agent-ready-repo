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
    # The vocabulary two surviving claims used. Their absence from this list is
    # why both suites were green on a tree that violated two criteria: the
    # assertion named strings the non-compliant text never contained.
    "fingerprint stasis",
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


# Preserved published text. `new-rfc.md` illustrates amending a cap through an
# RFC and is deliberately untouched; it says "stasis-detection data", which the
# hyphen is all that keeps out of `RETIRED_CLAIMS`'s reach.
PRESERVED_PUBLISHED = (
    (
        "guides/governance-extras/how-to/new-rfc.md",
        "use the new-rfc skill to amend the work-loop iteration cap from 5 to 7 "
        "based on six months of stasis-detection data",
    ),
)


def _preserved(pairs: tuple[tuple[str, str], ...]) -> list[str]:
    """Establish each preserved literal from the file it is attributed to.

    The collision domain is text that lives in files. Comparing a phrase list
    against a hand-copied literal guards a copy, not the thing: if the real
    wording drifts, the sweep reds on a compliant tree while the guard that
    exists to prevent that stays green.
    """
    out: list[str] = []
    for relpath, literal in pairs:
        target = ROOT / relpath
        assert target.is_file(), f"preserved text attributed to a missing file: {relpath}"
        assert literal in _flat(target), (
            f"preserved literal no longer appears in {relpath}: {literal!r}. "
            "The collision guard is now checking a phrase that is not there."
        )
        out.append(literal)
    return out


@pytest.mark.parametrize("claim", RETIRED_CLAIMS)
def test_no_retired_claim_matches_preserved_published_text(claim: str) -> None:
    """A published-claim sweep must not be able to red on prose kept on purpose."""
    collisions = [s for s in _preserved(PRESERVED_PUBLISHED) if claim in s.lower()]
    assert not collisions, (
        f"retired claim {claim!r} matches preserved published text: {collisions}"
    )


@pytest.mark.parametrize(
    "paragraph",
    (
        "The extra five steps — gates, adversarial review, specialist reviewers, "
        "reporting repeated findings, learning capture",
        "reviewer findings send you back to FIX, and the iteration cap sends you "
        "to a human",
    ),
)
def test_the_prose_beside_each_comparison_table_claims_the_cap(paragraph: str) -> None:
    """AC-0005 names the prose as well as the rows.

    Editing only the rows left both paragraphs selling the retired capability,
    and one of them stating the halt outright.
    """
    assert paragraph in _flat(CORE_PACK_GUIDE), (
        f"prose beside a comparison table no longer reads as expected: {paragraph!r}"
    )


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


# ── AC-0006: the retirement stays retired ────────────────────────────────────
#
# Same shape as the sweep ADR-0104's own Confirmation ships for the retired
# light-mode bound. Three properties, and the third is the one that is easy to
# leave out: a phrase list that matches text the change preserves fails on the
# compliant tree. One candidate phrase already did -- `pause for human
# replanning` matched iteration-cap prose two lines from its intended target --
# so the collision is a case here rather than a discovery later.

RETIRED_PHRASES = (
    "do not start another round",
    "stops immediately for human replanning",
    "surface immediately; do not run",
    "same findings twice = stop",
    "the loop stops and surfaces",
    "stops a third pass",
    "refuses to self-certify past a red gate or a repeated finding",
    "it stops at plan approval, unresolved boundaries, repeated findings",
    # The vocabulary that made both suites green over a two-criterion violation.
    # It was added to the published list first; the runtime surfaces are edited
    # surfaces too, so the criteria reach them and the sweep must as well.
    "fingerprint stasis",
)

# Explicit, not a glob over a tree: an earlier attempt widened the path list and
# swept 198 hits against a 43-row table. `.claude/` and `.agents/` are the
# tracked projections, which carry the old prose until self-host runs — which is
# why the projection step precedes this sweep rather than following it.
SWEEP_CORPUS = (
    "packs/core/.apm/skills/work-loop/SKILL.md",
    "packs/core/.apm/skills/work-loop/references",
    "packs/core/.apm/skills/work-loop/evals/evals.json",
    "packs/core/DESIGN.md",
    ".claude/skills/work-loop",
    ".agents/skills/work-loop",
    "guides/core",
    "guides/README.md",
    "web/src/content/packs/core.md",
)

# Statements the change preserves. A retired phrase matching any of these would
# red on the compliant tree, which is the "too tight and too loose" failure.
_REFS = "packs/core/.apm/skills/work-loop/references/"
_SKILL = "packs/core/.apm/skills/work-loop/SKILL.md"

PRESERVED_TEXT = (
    (_REFS + "delivery-contract-lifecycle.md",
     "session end, retry cap, stasis, or model judgment never invokes this "
     "transition or creates a follow-on"),
    (_REFS + "delivery-contract-lifecycle.md",
     "Retry caps, review stasis, and a clean intermediate unit never complete "
     "intent or create follow-ons"),
    (_SKILL,
     "an intermediate clean unit, retry cap, or stasis never completes accepted intent"),
    (_SKILL,
     "A merged PR, retry cap, or review stasis alone is not completion"),
    (_REFS + "finding-adjudication.md",
     "Surface it, and continue the round sequence"),
    (_REFS + "state-schema.md",
     "Surface it; it starts no transition and stops no loop"),
)


def _swept_files() -> list[Path]:
    """Every swept path, with existence asserted before anything is walked.

    A mistyped path would otherwise sweep nothing and pass, which is how an
    absence sweep reports agreement it never earned.
    """
    files: list[Path] = []
    for entry in SWEEP_CORPUS:
        target = ROOT / entry
        assert target.exists(), f"sweep corpus names a path that does not exist: {entry}"
        if target.is_dir():
            found = sorted(p for p in target.rglob("*") if p.suffix in {".md", ".json"})
            assert found, f"sweep corpus directory is empty: {entry}"
            files.extend(found)
        else:
            files.append(target)
    return files


@pytest.mark.parametrize("phrase", RETIRED_PHRASES)
def test_the_retired_halt_stays_retired(phrase: str) -> None:
    offenders = sorted(
        str(p.relative_to(ROOT)) for p in _swept_files() if phrase in _flat(p).lower()
    )
    assert not offenders, f"retired halt {phrase!r} reappeared in: {offenders}"


@pytest.mark.parametrize("phrase", RETIRED_PHRASES)
def test_no_retired_phrase_matches_preserved_text(phrase: str) -> None:
    """The sweep must not be able to red on text this change keeps."""
    collisions = [s for s in _preserved(PRESERVED_TEXT) if phrase in s.lower()]
    assert not collisions, (
        f"retired phrase {phrase!r} matches preserved text: {collisions}. "
        "A sweep that fires on the compliant tree is unusable; narrow the phrase."
    )
