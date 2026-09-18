"""A spec and plan read as the current contract, not as the authoring session.

Three template rules meet here. The plan's `## Changelog` records approvals and
drops drafting history. The spec's `## Assumptions` records what is unresolved
and routes every settled fact to the artifact that acts on it. The prose
reference gives the author a pass over their own wording, advisory and gating
nothing.

Every content arm slices the file to the section it is about before asserting.
A whole-file `assertNotIn` passes when a phrase merely moves to a section where
it is wrong, and `test_every_slice_is_non_empty` is the guard for the slicer
itself: a helper returning "" makes every absence arm in this module vacuous.

Anchored at the owning pack: `lint-pack-test-boundary` forbids a pack test from
reading above `packs/<pack>/`, so the arm covering
`guides/core/how-to/plan-and-execute-non-trivial-work.md` lives in
`tests/roster/test_spec_prose_discipline_guide.py` instead.

Spec: docs/specs/spec-plan-prose-discipline/spec.md
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_PACK = Path(__file__).resolve().parents[3]
_SKILL_DIR = _PACK / ".apm" / "skills" / "new-spec"
_SPEC_ASSET = _SKILL_DIR / "assets" / "spec.md"
_PLAN_ASSET = _SKILL_DIR / "assets" / "plan.md"
_SKILL = _SKILL_DIR / "SKILL.md"
_PROSE = _SKILL_DIR / "references" / "prose-discipline.md"
_RUBRIC = _SKILL_DIR / "references" / "spec-authoring-rubric.md"
_CONTRACT = _SKILL_DIR / "references" / "spec-and-plan-contract.md"

_AGENTS = _PACK / ".apm" / "agents"
_CONSUMERS = (
    _AGENTS / "adversarial-reviewer.md",
    _AGENTS / "security-reviewer.md",
    _AGENTS / "quality-engineer.md",
    _PACK / ".apm" / "skills" / "work-loop" / "references" / "pre-execute-review.md",
)

# The slices every content arm below depends on. Named here so the guard arm
# can walk the same set rather than a list that drifts from what is used.
_SLICES = (
    (_PLAN_ASSET, "## Changelog"),
    (_SPEC_ASSET, "## Assumptions"),
    (_SPEC_ASSET, "## Outcome"),
    (_SPEC_ASSET, "## What Changes"),
    (_SPEC_ASSET, "## Agent Rules"),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """The named `## ` section, up to the next `## ` heading or end of file."""
    start = text.index(heading)
    nxt = text.find("\n## ", start + len(heading))
    return text[start:] if nxt == -1 else text[start:nxt]


def flat(text: str) -> str:
    """Whitespace-flattened. Both assets hard-wrap prose mid-phrase, so a
    line-oriented search reports a present phrase absent."""
    return re.sub(r"\s+", " ", text)


class TheSlicerIsNotVacuous(unittest.TestCase):
    """Guard for every other arm in this module.

    An absence assertion over an empty string passes. If a heading is renamed
    or deleted, `section` would raise -- but a future edit making it return ""
    instead would silently disarm the module, so the set is walked explicitly.
    """

    def test_every_slice_is_non_empty(self) -> None:
        for path, heading in _SLICES:
            with self.subTest(path=path.name, heading=heading):
                body = section(read(path), heading)
                self.assertTrue(body.startswith(heading))
                self.assertGreater(len(body.strip()), len(heading) + 40)


class ThePlanChangelogRecordsApprovalsOnly(unittest.TestCase):
    """AC-0001."""

    def setUp(self) -> None:
        self.note = section(read(_PLAN_ASSET), "## Changelog")

    def test_the_only_dated_entries_are_the_two_approvals(self) -> None:
        dated = re.findall(r"^- \d{4}-\d{2}-\d{2}:.*|^- YYYY-MM-DD:.*", self.note, re.M)
        self.assertEqual(
            [
                "- YYYY-MM-DD: spec approved by <handle>",
                "- YYYY-MM-DD: plan approved by <handle>",
            ],
            dated,
        )

    def test_the_drafting_history_examples_are_gone(self) -> None:
        for phrase in ("initial plan", "switched from approach"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.note)

    def test_the_note_says_approvals_are_its_only_content(self) -> None:
        # Paired with the absence arms above: deleting the section would pass
        # those two and fail this one.
        self.assertIn("Approvals, and nothing else", self.note)


class TheSpecAssumptionsHoldsOnlyWhatIsUnresolved(unittest.TestCase):
    """AC-0002 and AC-0017."""

    def setUp(self) -> None:
        self.note = section(read(_SPEC_ASSET), "## Assumptions")

    def test_no_settled_fact_carries_a_citation(self) -> None:
        self.assertNotIn("(source:", self.note)

    def test_the_empty_value_is_named(self) -> None:
        self.assertIn("`none`", self.note)

    def test_both_unresolved_shapes_are_admitted(self) -> None:
        # SKILL.md step 4d writes a named gap, not a question. A format
        # admitting only questions would leave that instruction unwritable.
        for shape in ("open question", "named gap"):
            with self.subTest(shape=shape):
                self.assertIn(shape, self.note)

    def test_all_four_routing_destinations_are_named(self) -> None:
        for dest in ("`Outcome`", "`Agent Rules`", "`## Design (LLD)`", "`## Constraints`"):
            with self.subTest(dest=dest):
                self.assertIn(dest, self.note)


class TheSpecTemplateCarriesTheRenamedSections(unittest.TestCase):
    """AC-0003."""

    def setUp(self) -> None:
        self.body = read(_SPEC_ASSET)

    def test_outcome_precedes_what_changes(self) -> None:
        self.assertLess(self.body.index("\n## Outcome"), self.body.index("\n## What Changes"))

    def test_agent_rules_keeps_the_three_tiers(self) -> None:
        rules = section(self.body, "## Agent Rules")
        for tier in ("### Always do", "### Ask first", "### Never do"):
            with self.subTest(tier=tier):
                self.assertIn(tier, rules)

    def test_the_old_headings_are_gone(self) -> None:
        for heading in ("\n## Objective", "\n## Boundaries"):
            with self.subTest(heading=heading):
                self.assertNotIn(heading, self.body)

    def test_the_tier_note_places_each_renamed_section(self) -> None:
        note = flat(self.body[: self.body.index("\n## Outcome")])
        self.assertIn("`Agent Rules`, `Testing Strategy` and", note)
        self.assertIn("`Outcome`, `What Changes`, `Durable Outputs`", note)


class NoSurfaceStatesTheRetiredRules(unittest.TestCase):
    """AC-0004. Differential: each stale phrase is absent AND its replacement
    is present, so deleting the passage does not pass."""

    STALE = (
        "changelog of how the approach evolved",
        "outnumber its `Approach:`",
        "comes *before* Approach",
    )

    def test_no_file_under_the_skill_carries_a_stale_phrase(self) -> None:
        targets = sorted(_SKILL_DIR.rglob("*.md"))
        # An empty glob makes every subTest below vacuous, which is the same
        # hole `TheSlicerIsNotVacuous` closes for the section slicer.
        self.assertGreaterEqual(len(targets), 4, f"no markdown found under {_SKILL_DIR}")
        for path in targets:
            body = flat(read(path))
            for phrase in self.STALE:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, body)

    def test_the_replacing_statements_are_present(self) -> None:
        self.assertIn(
            "its `## Changelog` records approvals, not how the approach evolved",
            flat(read(_SPEC_ASSET)),
        )
        self.assertIn("**`Approach:` is conditional.**", read(_PLAN_ASSET))
        self.assertIn("`Approach:` is conditional and `assets/plan.md` owns when", flat(read(_CONTRACT)))


class TheSkillRoutesSettledFactsAndPointsAtTheProsePass(unittest.TestCase):
    """AC-0005."""

    def setUp(self) -> None:
        self.body = flat(read(_SKILL))

    def test_the_copy_the_confirmed_list_instruction_is_gone(self) -> None:
        self.assertNotIn("user confirmation YYYY-MM-DD", self.body)

    def test_step_three_routes_rather_than_copies(self) -> None:
        self.assertIn("Route every settled item to where it does work", self.body)
        self.assertIn("Write only what is still unresolved into the spec's `## Assumptions`", self.body)

    def test_both_body_steps_link_the_prose_pass(self) -> None:
        raw = read(_SKILL)
        spec_step = raw[raw.index("\n4. Fill in the spec") : raw.index("\n5. Fill in the plan")]
        plan_step = raw[raw.index("\n5. Fill in the plan") : raw.index("\n5a.")]
        for name, step in (("spec-body", spec_step), ("plan-body", plan_step)):
            with self.subTest(step=name):
                self.assertIn("references/prose-discipline.md", step)


class TheProseReferenceIsAdvisory(unittest.TestCase):
    """AC-0006 and AC-0007."""

    def setUp(self) -> None:
        self.body = read(_PROSE)

    def test_it_carries_its_four_parts(self) -> None:
        self.assertEqual(
            [
                "## The signal-word scan",
                "## The structural tells",
                "## Restructure, do not word-swap",
                "## The distinctiveness test",
            ],
            re.findall(r"^## .*", self.body, re.M),
        )

    def test_it_opens_by_declaring_itself_advisory(self) -> None:
        opening = self.body[: self.body.index("## The signal-word scan")]
        self.assertIn("Advisory guidance, never a gate", opening)

    def test_it_carries_none_of_three_named_gate_words(self) -> None:
        # Exactly these three, which is AC-0007's closed list. It does not
        # establish that the reference is non-gating: "required", "must" and
        # any other imperative pass here. Whether the reference *reads* as
        # advisory is AC-0015's recorded verdict, which no word list settles.
        for word in ("exit", "fail", "blocks"):
            with self.subTest(word=word):
                self.assertNotIn(word, self.body.lower())

    def test_it_states_no_digit_shaped_threshold(self) -> None:
        # Digit-shaped only, and threshold-shaped rather than any digit,
        # because the file cites rubric "class 6". A spelled-out bound
        # ("at least three") passes, and the arm is named for that limit
        # rather than claiming the file states no threshold at all.
        thresholds = re.findall(
            r"\b(?:at least|no more than|under|over|fewer than|within)\s+\d"
            r"|\d+\s*(?:%|percent)", self.body
        )
        self.assertEqual([], thresholds)

    def test_it_defers_the_form_rules_to_the_managed_block(self) -> None:
        self.assertIn("managed output-rendering block", flat(self.body))

    def test_it_keeps_the_comparison_value_carve_out(self) -> None:
        # Without it, "short sentences" licenses shortening a byte layout.
        self.assertIn("None of this licenses shortening a comparison value", flat(self.body))


class TheRubricGainsAPointerAndNotAClass(unittest.TestCase):
    """AC-0018."""

    def setUp(self) -> None:
        self.body = read(_RUBRIC)

    def test_exactly_one_pointer(self) -> None:
        self.assertEqual(1, self.body.count("prose-discipline"))

    def test_it_still_opens_with_six_classes(self) -> None:
        self.assertIn("Six failure classes", self.body[:400])

    def test_no_seventh_class_was_added(self) -> None:
        self.assertNotIn("\n## 7.", self.body)


class EveryReviewConsumerResolvesAgainstBothHeadings(unittest.TestCase):
    """AC-0008. Roughly 490 specs on disk carry `## Boundaries`; a reviewer
    pointed only at the new name loses its standard on all of them."""

    def test_each_consumer_names_both_in_one_sentence(self) -> None:
        for path in _CONSUMERS:
            with self.subTest(path=path.name):
                body = flat(read(path))
                self.assertIn("Agent Rules", body)
                sentences = [s for s in re.split(r"(?<=[.;])\s", body) if "Agent Rules" in s]
                self.assertTrue(
                    any("Boundaries" in s for s in sentences),
                    f"{path.name} names Agent Rules without the legacy heading beside it",
                )


class TheContractReferenceNamesTheCurrentSections(unittest.TestCase):
    """AC-0009, the half a pack test can reach."""

    def test_the_old_section_list_is_replaced(self) -> None:
        body = flat(read(_CONTRACT))
        self.assertNotIn("four sections — Objective, Boundaries", body)
        self.assertIn("Agent Rules, Testing Strategy, Acceptance Criteria", body)
