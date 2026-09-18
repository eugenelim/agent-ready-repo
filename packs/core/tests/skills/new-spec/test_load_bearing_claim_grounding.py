"""Construction tests for the load-bearing-claim routing rule.

Spec: docs/specs/load-bearing-claim-grounding/spec.md

Every assertion here reads the shipped pack source, and every one is written
against **whitespace-flattened** text. The file hard-wraps its prose, so a
line-oriented check silently passes on a phrase split across two lines --
which is how the delivery's own sweep first reported not a sweep absent
when it was present.

These controls see structure and location. They cannot see whether a sentence
is true; spec.md's Testing Strategy states that limit and gates nothing on it.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import unittest
from pathlib import Path

# Anchored at the owning pack, not the repository root: `lint-pack-test-boundary`
# forbids a pack test from reaching above `packs/<pack>/`. The two
# repository-level arms this suite used to carry -- AC-0001's scan across
# `guides/` and AC-0002's pointer in the adopter how-to -- live in
# `tests/roster/test_load_bearing_claim_routing_surfaces.py`.
_PACK = Path(__file__).resolve().parents[3]
_SKILL = _PACK / ".apm" / "skills" / "new-spec" / "SKILL.md"

# AC-0006's routing-input key set. Written here, never read from the table:
# a domain taken from the artifact under test cannot fail.
_ROUTING_KEYS = frozenset(
    {"reaches-the-contract", "unstarted-task-method", "cheap-with-an-oracle"}
)

# AC-0006's five fields on the unstarted-task destination.
_TASK_FIELDS = (
    "discovery predicate",
    "constraint",
    "required outcome",
    "verification mode",
    "kill condition",
)

# AC-0008's closed fixture, transcribed from the criterion: each cut shape's
# identifier paired with the demand sentence it names. The criterion reaches
# exactly these and claims nothing about a paraphrase outside them.
_CUT_SHAPES = {
    "reused-machinery": "machinery contract plus a discriminating example",
    "set-membership": "distribution plus residuals",
    "generated-output": "representation the real gate consumes",
    "generated-measurement": "generator, a counted unit, and one home",
    "sweep-completeness": "conclusion naming its surface",
}

# AC-0003's taxonomy, as a closed set. Compared against the step's complete
# enumeration, not searched for: finding three labels cannot see a fourth.
_CATEGORIES = ("Technical", "Product", "Process")

# AC-0004's six consequences, verbatim. A count alone passes on six substituted
# consequences, so the identities are the fixture.
_CONSEQUENCES = (
    "acceptance criterion",
    "boundary",
    "task graph",
    "verification strategy",
    "consequential failure direction",
    "chosen mechanism",
)

# The predicate's own wording for each consequence. A second enumeration would
# copy these forms, so these are what the residual route must not contain.
_PREDICATE_FORMS = (
    "an acceptance criterion",
    "a boundary",
    "the task graph",
    "the verification strategy",
    "the consequential failure direction",
    "the chosen mechanism",
)

# AC-0004's firing predicate, which AC-0005 requires inside the step. The whole
# sentence, so moving the predicate out while leaving a fragment behind fails.
_FIRING_PREDICATE = (
    "It fires only on a **load-bearing claim**, which is one whose falsehood "
    "could change any of exactly six things"
)

# AC-0006's contracted semantics per destination, each phrase load-bearing.
_DESTINATION_SEMANTICS = {
    "reaches-the-contract": ("before approval", "bounded spike"),
    "unstarted-task-method": ("kill condition",),
    "cheap-with-an-oracle": ("in code", "does not belong in design prose"),
}

# AC-0007's protected region: step 5a, digested from the pre-change tree.
_5A_START = "5a. **Take the cheapest disconfirming evidence before review.**"
_5A_DIGEST = "a47111302b15372ea0c75d1119cedabd017368a6c4700660fbff8d8970b8281b"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _step_3(text: str) -> str:
    """The assumptions step only.

    AC-0005 is about placement, so it must be decided against this slice and
    never against the whole file: a whole-file search is satisfied by a
    preamble, which is the defect the criterion exists to catch.
    """
    start = text.index("3. **Surface assumptions before writing any spec body")
    end = text.index("\n3a. ", start)
    return text[start:end]


def _step_5a(text: str) -> str:
    start = text.index(_5A_START)
    return text[start:text.index("\n6. ", start)]


def _routing_rows(step: str) -> list[tuple[str, str, str]]:
    """Parse the routing table into ordered (key, input cell, destination).

    The input cell is carried as well as the destination because the table's
    totality is stated there -- the residual route says which claims it takes.

    A list, not a dict: a dict collapses a duplicated row, so uniqueness
    would be undecidable from it. Lines are stripped before matching because
    the table is indented inside a numbered list item -- a regex anchored at
    the line start with a literal pipe matches nothing there and its test passes on an empty list, which is how
    the first version of the uniqueness arm came out vacuous under mutation.
    """
    rows: list[tuple[str, str, str]] = []
    for raw in step.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "Routing input":
            continue
        m = re.match(r"`([a-z-]+)`", cells[0])
        if m:
            rows.append((m.group(1), cells[0], cells[1]))
    return rows


def _routing_table(step: str) -> dict[str, str]:
    """The same parse as key -> destination, for the destination assertions."""
    return {k: dest for k, _, dest in _routing_rows(step)}


def _routing_inputs(step: str) -> dict[str, str]:
    """The same parse as key -> input cell, for the totality assertion."""
    return {k: cell for k, cell, _ in _routing_rows(step)}


class FiringPredicate(unittest.TestCase):
    """AC-0003, AC-0004, AC-0005."""

    def test_categories_are_exactly_the_three(self) -> None:
        # Parsed as a complete set, then compared: searching for three labels
        # is satisfied by a file that also carries a fourth.
        step = _step_3(_skill_text())
        # Every bold label in the enumeration, whatever its shape: a
        # single-word-only pattern is blind to `**Customer impact** —`.
        found = tuple(re.findall(r"^\s*- \*\*(.+?)\*\* —", step, re.M))
        self.assertEqual(_CATEGORIES, found, "the taxonomy is exactly these three")

    def test_the_rule_is_stated_as_cross_category(self) -> None:
        self.assertIn(
            "applies across all three categories",
            _flat(_step_3(_skill_text())),
        )

    def test_the_six_consequences_are_exactly_the_contracted_ones(self) -> None:
        step = _flat(_step_3(_skill_text()))
        m = re.search(r"change any of exactly six things: (.*?)\.", step)
        self.assertIsNotNone(m, "the consequence test must be stated")
        # Leading articles are normalised away -- the criterion and the shipped
        # prose word them differently and neither is load-bearing. The six
        # identities are: six substituted consequences would satisfy a count
        # while changing what the rule fires on.
        items = tuple(
            re.sub(r"^(?:a|an|the) ", "", x.strip())
            for x in re.split(r",| or ", m.group(1))
            if x.strip()
        )
        self.assertEqual(_CONSEQUENCES, items)

    def test_the_firing_paragraph_carries_no_second_predicate(self) -> None:
        """AC-0004's 'no alternative test' half, at the reach a control has.

        No pattern decides whether an arbitrary added sentence is a second
        firing test, so this pins the paragraph's sentence count instead: any
        sentence added to or removed from it reddens. That catches an inserted
        predicate and does not claim to recognise one by its wording.
        """
        step = _flat(_step_3(_skill_text()))
        start = step.index("**Route a claim you cannot settle")
        para = step[start:step.index("For a load-bearing claim you cannot settle", start)]
        # Markdown is stripped first: `cost.**` blocks a space-anchored split,
        # so counting the raw text reports three where the prose has four and
        # the assertion message would be false about the paragraph it pins.
        plain = para.replace("**", "")
        sentences = [x for x in re.split(r"(?<=[.!?]) ", plain) if x.strip()]
        self.assertEqual(
            4, len(sentences),
            "The firing paragraph is four sentences and now has "
            f"{len(sentences)}. This arm is a proxy for AC-0004's 'no "
            "alternative test' half: no pattern decides whether an added "
            "sentence is a second firing predicate, so the count stands in for "
            "it. If you added a predicate, remove it. If you added a "
            "clarification and the rule still has exactly one firing test, "
            "update this expected count and say so in the spec's Testing "
            "Strategy, which owns what this proxy does not reach.",
        )

    def test_the_whole_firing_predicate_sits_inside_the_step(self) -> None:
        # Decided against the step slice, and against the whole predicate: a
        # fragment left behind would pass while the predicate moved out.
        step = _flat(_step_3(_skill_text()))
        self.assertIn(_flat(_FIRING_PREDICATE), step)
        self.assertIn("is an ordinary fact", step)
        self.assertIn("this rule does not reach it", step)


class RoutingTableIsTotalAndDisjoint(unittest.TestCase):
    """AC-0006, whose row keys, destinations and five task fields this covers."""

    def _rows(self) -> dict[str, str]:
        return _routing_table(_step_3(_skill_text()))

    def test_row_keys_equal_the_fixture_exactly(self) -> None:
        # Fixture-first: compared before any mapping is used, so an omitted,
        # renamed, or added input fails rather than redefining the domain.
        self.assertEqual(_ROUTING_KEYS, set(self._rows()))

    def test_keys_are_unique(self) -> None:
        keys = [k for k, _, _ in _routing_rows(_step_3(_skill_text()))]
        self.assertEqual(len(set(keys)), len(keys), "no routing input appears twice")

    def test_the_row_parse_is_not_vacuous(self) -> None:
        # Guards the arm above: an empty parse makes uniqueness trivially true.
        self.assertEqual(3, len(_routing_rows(_step_3(_skill_text()))))

    def test_each_key_maps_to_one_nonempty_destination(self) -> None:
        for key, dest in self._rows().items():
            with self.subTest(key=key):
                self.assertTrue(dest.strip())

    def test_each_destination_carries_its_contracted_semantics(self) -> None:
        rows = self._rows()
        for key, phrases in _DESTINATION_SEMANTICS.items():
            dest = _flat(rows[key])
            for phrase in phrases:
                with self.subTest(key=key, phrase=phrase):
                    self.assertIn(phrase, dest)

    def test_the_residual_destination_sizes_its_spike_to_the_claim(self) -> None:
        """AC-0017: the residual spike matches the cost of being wrong."""
        residual = _flat(self._rows()["reaches-the-contract"])
        proportionate = (
            "The bounded spike is proportionate to what the claim's falsehood would cost."
        )
        self.assertIn(proportionate, residual)
        with self.assertRaises(AssertionError):
            self.assertIn(proportionate, residual.replace(proportionate, ""))

    def test_the_table_is_total_over_the_firing_predicate(self) -> None:
        """No load-bearing claim can fire the rule and match no routing input.

        The contract row is the residual route, defined against the six
        consequences rather than by a second enumeration of them. A row that
        re-listed the consequences could drift from the predicate and leave one
        unrouted, which is what it did before.
        """
        residual = _flat(_routing_inputs(_step_3(_skill_text()))["reaches-the-contract"])
        self.assertIn("any of the six above", residual)
        self.assertIn("unless a row below applies", residual)
        # The guarantee clause itself, asserted rather than inferred from the
        # label beside it: deleting it is what makes the route stop being total.
        self.assertIn("no load-bearing claim is unrouted", residual)
        # And it must not restate the consequences -- a second list is free to
        # drift from the predicate, which is how one came to be omitted. The
        # predicate's own article-bearing forms are what a restatement would
        # copy, so those are what is checked; no member is exempted.
        for phrase in _PREDICATE_FORMS:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, residual)

    def test_the_two_exception_routes_are_disjoint(self) -> None:
        inputs = _routing_inputs(_step_3(_skill_text()))
        task = _flat(inputs["unstarted-task-method"])
        cheap = _flat(inputs["cheap-with-an-oracle"])
        # The discriminator between them is whether a test decides the claim.
        # Without it both rows match an unstarted task's cheap detail and
        # prescribe conflicting destinations.
        self.assertIn("no test can decide it directly", task)
        self.assertIn("a test can decide it directly", cheap)
        self.assertIn("Exactly one row applies", _flat(_step_3(_skill_text())))

    def test_the_unstarted_task_destination_names_five_fields(self) -> None:
        dest = _flat(self._rows()["unstarted-task-method"])
        for field in _TASK_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, dest)
        self.assertEqual(5, len(_TASK_FIELDS))


class PreReviewProbeStepIsUnmoved(unittest.TestCase):
    """AC-0007. The digest comes from the pre-change tree, so editing a single
    word of the protected region reddens this. The five task fields asserted
    above belong to AC-0006, not here."""

    def test_step_5a_matches_the_pre_change_digest(self) -> None:
        got = hashlib.sha256(_step_5a(_skill_text()).encode()).hexdigest()
        self.assertEqual(
            _5A_DIGEST, got,
            "Step 5a's text changed. AC-0007 makes it immutable here because "
            "that surface belongs to slice A4 of "
            "docs/product/briefs/agent-authoring-input-quality.md, not to this "
            "change. If the edit belongs to A4, it needs that slice and a "
            "controlled amendment of AC-0007 with owner authority -- not a new "
            "digest. If you edited it by accident, revert step 5a; "
            "`git show HEAD:packs/core/.apm/skills/new-spec/SKILL.md` has the "
            "text this digest was taken from.",
        )

    def test_the_digest_was_taken_from_committed_content(self) -> None:
        shown = subprocess.run(
            ["git", "show", "HEAD:packs/core/.apm/skills/new-spec/SKILL.md"],
            cwd=_PACK, capture_output=True, text=True, timeout=60, check=True,
        ).stdout
        self.assertEqual(
            _5A_DIGEST, hashlib.sha256(_step_5a(shown).encode()).hexdigest(),
            "the pin must match HEAD, not the working tree",
        )


class CutShapesStayCut(unittest.TestCase):
    """AC-0008. Exactly the five fixture entries; nothing wider is claimed."""

    def test_no_cut_identifier_is_named(self) -> None:
        step = _step_3(_skill_text())
        for ident in _CUT_SHAPES:
            with self.subTest(identifier=ident):
                self.assertNotIn(ident, step)

    def test_no_cut_demand_sentence_is_carried(self) -> None:
        step = _flat(_step_3(_skill_text()))
        for ident, demand in _CUT_SHAPES.items():
            with self.subTest(identifier=ident):
                self.assertNotIn(demand, step)

    def test_the_fixture_has_five_entries(self) -> None:
        self.assertEqual(5, len(_CUT_SHAPES))


class OneCheckCardinalityIsGoneAndTheSweepBoundStays(unittest.TestCase):
    """AC-0009. A removal-and-retention pair: removing the cardinality must not
    take the no-sweep protection with it."""

    def test_the_cardinality_is_absent_from_both_homes(self) -> None:
        flat = _flat(_skill_text())
        for phrase in (
            "one targeted check per candidate assumption",
            "run one targeted verification check per candidate",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, flat)

    def test_the_sweep_bound_is_retained(self) -> None:
        self.assertIn("not a sweep", _flat(_step_3(_skill_text())))
