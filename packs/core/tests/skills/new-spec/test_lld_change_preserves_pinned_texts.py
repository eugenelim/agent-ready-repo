"""Preservation and size budget for the LLD down-edge change.

The down-edge is an ADDITION to three surfaces that already carry pinned
prose. Each text below existed before the change and must survive it
byte-for-byte; asserting them here is what separates "added a traversal" from
"rewrote the list that held four of them".
"""

from __future__ import annotations

from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/new-spec/SKILL.md"
PLAN_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"

# The four traversals the pre-review walk carried before a fifth was added.
# Held as one block because the defect this catches is a rewrite of the list,
# which no single-sentence assertion would see.
PRE_EXISTING_TRAVERSALS = (
    "**Walk the whole plan once before review.** Every criterion has\n"
    "     construction evidence and every `Tests` bullet traces to a criterion; every\n"
    "     `Done when` observes what its own `Tests` require; no condition has two\n"
    "     homes; every shared bound is defined once."
)

# The routing table's reversibility condition. The residual route's cost was
# made proportionate; this condition was deliberately NOT widened, because it
# exists to remove the stakes judgement that widening reintroduces.
REVERSIBILITY = (
    "Reversible means undoing it needs no migration, no external side "
    "effect, and no change to a user-visible contract"
)

# Sentences the `reaches-the-contract` destination carried before the
# proportionality clause was appended.
RESIDUAL_PRE_EXISTING = (
    "Settle it **before approval**, by a bounded spike under the "
    "side-effect-free probe constraint above.",
    "After approval the contract is pinned, and a correction the work "
    "discovers may not be applicable to it at all.",
)

# Every `Traces to:` line the template carried, verbatim. Counting them instead
# would pass on nine rewritten lines, which is the failure this pins against:
# the field and the prompts are added in adjacent comments precisely so these
# nine lines never move.
TRACES_TO_LINES = (
    "of why each. Traces to: <AC(s) this satisfies> \u00b7 <contracts/\u2026 it implements>. -->",
    "Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "UI, the component tree. Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "UI, screen states and navigation. Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "partial failure, idempotency, degraded modes. Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
    "Traces to: <AC(s)> \u00b7 <contracts/\u2026>. -->",
)

# CAT-S003 errors above 1000 body lines. The budget reserves 100 of them.
BODY_LINE_BUDGET = 900


def _body_lines(path: Path) -> int:
    """Lines after the closing frontmatter delimiter, as CAT-S003 counts them."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", "expected YAML frontmatter"
    close = next(i for i, line in enumerate(lines[1:], start=1) if line == "---")
    return len(lines) - (close + 1)


def test_the_four_pre_existing_traversals_are_unchanged() -> None:
    assert PRE_EXISTING_TRAVERSALS in SKILL.read_text(encoding="utf-8")


def test_the_reversibility_condition_was_not_widened() -> None:
    assert REVERSIBILITY in SKILL.read_text(encoding="utf-8")


@pytest.mark.parametrize("sentence", RESIDUAL_PRE_EXISTING)
def test_the_residual_destination_kept_its_sentences(sentence: str) -> None:
    assert sentence in SKILL.read_text(encoding="utf-8")


def test_the_traces_to_lines_are_byte_identical_in_order() -> None:
    """Ordered tuple comparison, not membership.

    Five of the nine lines are the same text, so asserting each one is present
    passes while a repeated line is dropped and another duplicated. Comparing
    the extracted sequence pins multiplicity and order together.
    """
    extracted = tuple(
        line for line in PLAN_ASSET.read_text(encoding="utf-8").split("\n")
        if "Traces to:" in line
    )
    assert extracted == TRACES_TO_LINES


def assert_within_budget(path: Path) -> None:
    """The enforcing check. Shared so the red case exercises the real path."""
    body = _body_lines(path)
    if body > BODY_LINE_BUDGET:
        raise AssertionError(
            f"{path.name} body is {body} lines, over the {BODY_LINE_BUDGET} budget"
        )


def test_skill_body_is_within_the_size_budget() -> None:
    assert_within_budget(SKILL)


def test_the_first_failing_body_length_is_rejected(tmp_path: Path) -> None:
    """901 lines is the first input that fails, and it fails the same check.

    Asserting `901 > 900` instead would prove arithmetic, not enforcement.
    """
    over = tmp_path / "SKILL.md"
    over.write_text("---\nname: x\n---\n" + "line\n" * (BODY_LINE_BUDGET + 1),
                    encoding="utf-8")
    with pytest.raises(AssertionError, match=f"over the {BODY_LINE_BUDGET} budget"):
        assert_within_budget(over)


def test_the_largest_passing_body_length_is_accepted(tmp_path: Path) -> None:
    """The bound's other side: 900 passes, so the limit is not off by one."""
    at_limit = tmp_path / "SKILL.md"
    at_limit.write_text("---\nname: x\n---\n" + "line\n" * BODY_LINE_BUDGET,
                        encoding="utf-8")
    assert_within_budget(at_limit)
