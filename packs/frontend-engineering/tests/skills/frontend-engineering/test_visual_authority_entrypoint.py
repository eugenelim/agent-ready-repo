"""The always-loaded entrypoint carries the contract, not just a reference.

Every rule this slice adds lives in `references/visual-observation.md`. If
nothing asserts that `SKILL.md` states the contract and routes to that file, a
perfectly correct reference can ship while the skill an agent actually loads
routes to none of it — and every other criterion stays green.
"""

from __future__ import annotations

import re

from frontend_engineering_visual_authority_rules import SKILL, skill_body_lines

BODY_BUDGET = 960


def test_the_entrypoint_carries_no_token_declaration_block() -> None:
    """The seed block moved out; only its routing rule stays."""
    text = SKILL.read_text(encoding="utf-8")
    assert ":root {" not in text, (
        "a :root declaration block is back in the entrypoint; the fallback "
        "values belong in references/fallback-tokens.md"
    )
    declarations = [
        line for line in text.splitlines()
        if re.match(r"^\s*--ds-color-primary\s*:", line)
    ]
    assert not declarations, f"token declaration back in SKILL.md: {declarations}"


def test_a_token_usage_is_not_a_token_declaration() -> None:
    """Scoping guard for the test above.

    A bare containment check on the token name reds on the focus-visible rule,
    which cites `var(--ds-color-primary)` as the correct replacement for
    `outline: none`. That citation is not a declaration and must survive, so
    the predicate is anchored rather than containment-based.
    """
    text = SKILL.read_text(encoding="utf-8")
    assert "var(--ds-color-primary)" in text, (
        "the focus-visible rule's token usage was removed; the anchored "
        "predicate exists precisely so this line does not have to go"
    )


def test_the_entrypoint_routes_to_the_fallback_reference() -> None:
    """Without this, deleting the block and writing the reference satisfies
    every other criterion while the entrypoint points at nothing."""
    assert "references/fallback-tokens.md" in SKILL.read_text(encoding="utf-8")


def test_the_entrypoint_body_stays_within_budget() -> None:
    """The catalogue lint errors above 1000 lines. This budget sits under it
    with headroom, and re-runs after every task that writes the entrypoint."""
    n = skill_body_lines()
    assert n <= BODY_BUDGET, (
        f"SKILL.md body is {n} lines against a {BODY_BUDGET} budget; the "
        f"catalogue skill-spec lint hard-errors at 1000"
    )
