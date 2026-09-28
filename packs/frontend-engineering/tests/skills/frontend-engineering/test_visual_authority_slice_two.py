"""Slice 2's pack-side criteria: the journey, and the token-value source.

Every assertion here reads a file inside this pack. The guide-tree criteria live
in `tests/roster/` instead, because `lint-pack-test-boundary.py` check 8 stops a
pack suite reading another source tree and `guides/` is not this pack's.

Both predicates below normalize whitespace before matching. That is not a
formality: three of the strings these criteria govern wrap mid-phrase in the
shipped files, and a raw containment check reports them absent while they are
present. The same trap has now cost this delivery a criterion that passed
against unchanged text, a sweep that missed the always-loaded entrypoint, and a
mutation proof that reported green because the mutation never applied.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "frontend-engineering" / "SKILL.md"
JOURNEY = PACK_ROOT / "JOURNEY.md"
EXPORT_TREE = PACK_ROOT / ".apm"


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def holds(haystack: str, literal: str) -> bool:
    return re.search(re.escape(literal).replace(r"\ ", r"\s+"), haystack, re.I) is not None


def gate_block(gate_id: str) -> str:
    """One gate's frontmatter entry, up to the next gate."""
    text = JOURNEY.read_text(encoding="utf-8")
    marker = f"- id: {gate_id}"
    assert marker in text, f"the {gate_id} gate is gone from the journey"
    rest = text.split(marker, 1)[1]
    end = rest.find("\n  - id: ")
    return re.sub(r"\s+", " ", rest[:end] if end != -1 else rest)


# --- the journey -----------------------------------------------------------


def test_the_review_gate_names_the_visual_authority_lens() -> None:
    """Scoped to the gate, not the file. The journey mentions the reviewer in
    several places; only this gate is what a human reads before merging."""
    block = gate_block("review-frontend-implementation")
    assert holds(block, "visual-authority"), (
        "the review-frontend-implementation gate does not name the "
        "visual-authority lens, so the gate a human reads before merge "
        "describes a six-lens review of a seven-lens reviewer"
    )


def test_the_acceptance_gate_asks_for_the_manifest_field() -> None:
    """`whatToCheck` is deliberately the target: the gate's other three fields
    are byte-pinned by `test_rendered_page_journey_promise.py`, and this
    delivery stays outside them."""
    block = gate_block("accept-frontend-evidence")
    assert holds(block, "visual authority"), (
        "the accept-frontend-evidence gate does not ask for `visual authority`, "
        "so a manifest missing the field passes the human gate"
    )


def test_the_stage_three_sequence_describes_the_precedence() -> None:
    """The stage-3 implementation line, scoped to stage 3.

    Searching the whole journey would pass on the gate text above, which is a
    different promise to a different reader.
    """
    text = JOURNEY.read_text(encoding="utf-8")
    stage = text.split("### 3. Implement or audit the surface", 1)
    assert len(stage) == 2, "journey stage 3 is gone"
    body = re.sub(r"\s+", " ", stage[1].split("### 4.", 1)[0])
    assert holds(body, "resolves visual authority"), (
        "journey stage 3 does not describe visual-authority resolution"
    )
    for banned, why in (
        ("aesthetic reference", "the named-aesthetic-reference step is gone"),
        ("seed token block", "the seed block moved out of the entrypoint"),
    ):
        assert not holds(body, banned), (
            f"journey stage 3 still names {banned!r} as a step, but {why}"
        )


@pytest.mark.parametrize(
    "cues",
    [("inapplicable", "omitted"), ("narrows the state matrix", "absent or broken")],
    ids=["omit-inapplicable", "narrowed-retrofit"],
)
def test_the_rewritten_line_keeps_each_allowance_pair_co_located(cues: tuple[str, str]) -> None:
    """`tests/roster/test_experience_journey_composition.py` requires both cue
    words of an allowance on one physical line, and the stage-3 line is the sole
    carrier of these two. A rewrite that splits the sentence reds that roster
    test with every word surviving; this asserts the property here too, so the
    failure names the line that moved rather than the suite that noticed.
    """
    lines = [line.lower() for line in JOURNEY.read_text(encoding="utf-8").splitlines()]
    assert any(all(cue in line for cue in cues) for line in lines), (
        f"no single line of the frontend journey carries both of {cues}; the "
        f"roster composition test will red even though every word survives"
    )


# --- the token-value source ------------------------------------------------

SUPERSEDED = ("rather than numbers", "roles and scales", "roles rather than")

VISUAL_OBSERVATION = (
    PACK_ROOT / ".apm" / "skills" / "frontend-engineering"
    / "references" / "visual-observation.md"
)

# Each site is an explicit path constant rather than a root joined with a
# parametrised string: `lint-pack-test-boundary.py` check 8 cannot prove a
# dynamic join stays inside the pack, and it is right not to try.
RESOLVED_VALUE_SITES = (
    (SKILL, ("as given", "resolved values")),
    (VISUAL_OBSERVATION, ("every value the taxonomy resolved",)),
)

EVALS = PACK_ROOT / ".apm" / "skills" / "frontend-engineering" / "evals" / "evals.json"

# The two eval cases that grade where values come from. Pinned by case id, and
# by presence rather than absence: the absence sweep above only catches a
# *reintroduced* superseded literal, so an edit that simply drops the claim
# would red nothing. This is the criterion's fourth carrier.
VALUE_GRADING_EVAL_IDS = (
    "visual-authority-approved-target",
    "visual-authority-direction-only",
)

PROTECTED = (
    "It supplies no colour, type, spacing or motion values, so those always come from a lower rung.",
    "Because rung 1 supplies no values, step 2 resolves them from rung 2 downward.",
)


def shipped_text_files() -> list[Path]:
    return [
        p for p in sorted(EXPORT_TREE.rglob("*"))
        if p.is_file() and p.suffix in (".md", ".json")
    ]


def test_the_export_tree_sweep_is_not_empty() -> None:
    assert len(shipped_text_files()) > 10, "the export-tree sweep found almost nothing"


@pytest.mark.parametrize("literal", SUPERSEDED)
def test_no_shipped_file_describes_the_value_free_taxonomy(literal: str) -> None:
    """The taxonomy now resolves values. A file still saying it carries roles
    and scales *rather than* numbers contradicts the source it feeds."""
    stale = [
        str(p.relative_to(PACK_ROOT)) for p in shipped_text_files() if holds(flat(p), literal)
    ]
    assert not stale, (
        f"{literal!r} survives in {stale}; a raw grep misses one of these "
        f"because it wraps mid-phrase, which is why this sweep normalizes"
    )


@pytest.mark.parametrize(
    "site,literals", RESOLVED_VALUE_SITES, ids=["skill", "visual-observation"]
)
def test_each_site_says_the_taxonomy_supplies_resolved_values(
    site: Path, literals: tuple[str, ...]
) -> None:
    text = flat(site)
    missing = [literal for literal in literals if not holds(text, literal)]
    assert not missing, f"{site.name} does not carry {missing}"


@pytest.mark.parametrize("eval_id", VALUE_GRADING_EVAL_IDS)
def test_the_value_grading_evals_expect_resolved_values(eval_id: str) -> None:
    """The eval harness grades the behaviour this source change alters, which is
    why `packs/AGENTS.md` obliges a non-cosmetic pack update to update it."""
    cases = {c["id"]: c for c in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]}
    assert eval_id in cases, f"{eval_id} is gone from the eval harness"
    expected = re.sub(r"\s+", " ", cases[eval_id]["expected_output"])
    assert holds(expected, "resolved"), (
        f"eval {eval_id} no longer expects the run to take the values the "
        f"taxonomy resolved; it grades the superseded contract"
    )


@pytest.mark.parametrize("statement", PROTECTED, ids=["rung-1-binds-no-values", "step-2-from-rung-2"])
def test_the_rung_one_value_rule_survives(statement: str) -> None:
    """Pinned because the edit above lands in the adjacent source list and the
    rung-2 entry directly beside them, and a sweep keyed on values-and-rungs
    vocabulary would take them with it. The first wraps between `or` and
    `motion`, so this match must be whitespace-normalized to hold at all."""
    assert holds(flat(SKILL), statement), (
        f"SKILL.md lost {statement!r}. Rung 1 binding no values is the rule that "
        f"keeps composition and value authority apart; an upstream reference "
        f"states it independently"
    )
