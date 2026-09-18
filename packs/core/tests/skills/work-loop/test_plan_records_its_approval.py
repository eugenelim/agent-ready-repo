"""The plan records each approval, and the two surfaces split the obligation.

Nothing in a spec directory said when its contract froze or on whose authority.
A replay across seven completed deliveries needed that datum and could not get
it from any artifact, so a test it had adopted mid-flight had to be withdrawn.
Each approval is now a dated Changelog entry in the plan.

The obligation is split deliberately. The plan template owns the entry's
**form**; `work-loop`'s G-plan sequence owns **when** it is written and why the
order is load-bearing. These arms assert each surface carries its own half and
neither restates the other's, because two copies of one rule drift.

Anchored at the owning pack: `lint-pack-test-boundary` forbids a pack test from
reading above `packs/<pack>/`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_PACK = Path(__file__).resolve().parents[3]
_PLAN_ASSET = _PACK / ".apm" / "skills" / "new-spec" / "assets" / "plan.md"
_WORK_LOOP = _PACK / ".apm" / "skills" / "work-loop" / "SKILL.md"
_RESUMPTION = (
    _PACK / ".apm" / "skills" / "work-loop" / "references" / "session-resumption.md"
)

# The two entry forms the template fixes. A gate reads these, so they are a
# fixture here rather than a shape inferred from whatever the file happens to say.
_ENTRY_FORMS = (
    "- YYYY-MM-DD: spec approved by <handle>",
    "- YYYY-MM-DD: plan approved by <handle>",
)


def _flat(text: str) -> str:
    """Whitespace-flattened. Both files hard-wrap prose mid-phrase, so a
    line-oriented search reports a present phrase absent."""
    return re.sub(r"\s+", " ", text)


def _flat_shell_comments(text: str) -> str:
    """Flatten, first dropping the `#` leader on *indented* continuation lines.

    The G-plan instructions live in a bash fence, so a wrapped sentence carries
    a `#` at each continuation. Flattening alone leaves those inside the phrase
    and every assertion misses. The leading-space requirement keeps a top-level
    Markdown heading (`## Step 1`) intact.
    """
    return _flat(re.sub(r"\n\s+#\s*", " ", text))


def _changelog_note(asset: str) -> str:
    """The template's Changelog guidance block only."""
    start = asset.index("## Changelog")
    return asset[start:asset.index("\n## ", start + 1)] if "\n## " in asset[start + 1:] else asset[start:]


class ThePlanTemplateOwnsTheEntryForm(unittest.TestCase):
    def setUp(self) -> None:
        self.note = _flat(_changelog_note(_PLAN_ASSET.read_text(encoding="utf-8")))

    def test_both_entry_forms_are_stated_verbatim(self) -> None:
        for form in _ENTRY_FORMS:
            with self.subTest(form=form):
                self.assertIn(form, self.note)

    def test_the_entry_forms_are_exactly_these_two(self) -> None:
        found = re.findall(r"- YYYY-MM-DD: \w+ approved by <handle>", self.note)
        self.assertEqual(list(_ENTRY_FORMS), found)

    def test_the_note_says_why_the_datum_exists(self) -> None:
        # Without the reason the entry reads as bookkeeping and gets skipped.
        self.assertIn("when the contract froze", self.note)
        self.assertIn("on whose authority", self.note)

    def test_the_template_defers_timing_rather_than_restating_it(self) -> None:
        self.assertIn("owns *when* each is written", self.note)
        # It must not carry work-loop's half: the pin mechanics.
        self.assertNotIn("splices out only the status token", self.note)

    def test_the_approval_paragraph_carries_no_ordering_language(self) -> None:
        """The split is only real if the template does not creep back into timing.

        Asserting the absence of the one mechanics phrase was not enough: the
        paragraph re-acquired ordering with "written last" and the arm stayed
        green. This checks a closed set of ordering terms inside that paragraph
        alone, so the surrounding guidance -- which legitimately says what
        happens *after* approval -- is out of scope. It is exactly that set and
        claims nothing about a paraphrase outside it.
        """
        para = self.note[self.note.index("**Each approval is an entry.**"):]
        para = para[:para.index("this\ntemplate owns only the form.")
                    if "this\ntemplate owns only the form." in para
                    else para.index("template owns only the form.")]
        # Instruction-shaped ordering only. "afterwards" is deliberately absent
        # from the set: the paragraph uses it to say why the datum matters --
        # which claims arrived after approval -- not to tell an author when to
        # write. Keeping it would have failed the artifact for its rationale.
        for term in ("last", "first", "before", "same edit"):
            with self.subTest(term=term):
                self.assertNotIn(term, para)


# Each phrase must appear once inside EACH mode's G-plan block. A whole-file
# count of two is satisfied by both copies drifting into one mode, which leaves
# the other uninstructed while the arm stays green.
_PER_MODE_PHRASES = (
    "adds the spec-approval entry to plan.md's Changelog",
    "in the SAME edit",
    "pins plan content and splices out only the status token",
    "invalidates the baseline hash",
)


def _gate_mode_blocks(body: str) -> dict[str, str]:
    """The `code` and `spec-plan` G-plan blocks, sliced from their own headings."""
    code_at = body.index("**`code` mode** (implementation work)")
    plan_at = body.index("**`spec-plan` mode** (spec/plan-only work")
    after = body.index("`spec-approved` = the scope decision", plan_at)
    return {"code": body[code_at:plan_at], "spec-plan": body[plan_at:after]}


class WorkLoopOwnsTheTiming(unittest.TestCase):
    def setUp(self) -> None:
        self.body = _flat_shell_comments(_WORK_LOOP.read_text(encoding="utf-8"))
        self.blocks = _gate_mode_blocks(self.body)

    def test_both_gate_modes_are_sliced(self) -> None:
        # Guards the arms below: a failed slice would make them vacuous.
        self.assertEqual({"code", "spec-plan"}, set(self.blocks))
        for mode, block in self.blocks.items():
            with self.subTest(mode=mode):
                self.assertIn("plan-approved", block)

    def test_each_mode_carries_every_required_phrase_exactly_once(self) -> None:
        for mode, block in self.blocks.items():
            for phrase in _PER_MODE_PHRASES:
                with self.subTest(mode=mode, phrase=phrase):
                    self.assertEqual(1, block.count(phrase))

    def test_work_loop_defers_the_form_rather_than_restating_it(self) -> None:
        self.assertIn("the plan template's Changelog note", self.body)
        for form in _ENTRY_FORMS:
            with self.subTest(form=form):
                self.assertNotIn(form, self.body)


class TheResumePathCannotPinAnUnrecordedApproval(unittest.TestCase):
    """The G-plan sequence is not the only route to `spec-approved`.

    A crash-recovery resume fires both approvals from the artifact's Status
    alone, so an approver who wrote `Status: Approved` and stopped would have
    the run pinned with no dated entry — the exact gap the entry closes, reached
    by the one path that skips the instruction.
    """

    def setUp(self) -> None:
        self.body = _flat(_RESUMPTION.read_text(encoding="utf-8"))

    def test_each_resumed_approval_checks_for_its_entry_first(self) -> None:
        for phrase in (
            "check `plan.md`'s Changelog carries the spec-approval entry",
            "check its Changelog carries the plan-approval entry",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.body)

    def test_a_missing_entry_surfaces_rather_than_pinning(self) -> None:
        # Two gates, so two surfacing branches. Counted: one branch alone leaves
        # the other able to pin an unrecorded approval.
        self.assertEqual(2, self.body.count("with no entry → **Surface and stop**"))

    def test_the_waiting_instruction_does_not_produce_the_rejected_state(self) -> None:
        """The route table tells an approver what to write while waiting.

        Telling them to change only the Status would walk them into the stop
        added above -- the reference would instruct the approver to create the
        state it then refuses. Both waiting rows name the entry too.
        """
        for phrase in (
            "writes `Status: Approved` in spec.md **and adds the spec-approval entry",
            "writes `Status: Approved` in plan.md **and adds the plan-approval entry",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.body)

    def test_the_surface_branch_says_why_it_cannot_just_record_it(self) -> None:
        # Without the reason a later editor reads the stop as excess caution and
        # replaces it with a generated entry, which is the failure it prevents.
        self.assertIn("approver's handle cannot be inferred", self.body)
