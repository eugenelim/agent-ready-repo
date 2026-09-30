"""The always-loaded entrypoint carries the contract, not just a reference.

Every rule this slice adds lives in `references/visual-observation.md`. If
nothing asserts that `SKILL.md` states the contract and routes to that file, a
perfectly correct reference can ship while the skill an agent actually loads
routes to none of it — and every other criterion stays green.

**Assertions here are scoped to the section their criterion names.** This diff
shipped three whole-file searches that could not fail for the thing they were
written to catch; a containment check over a 960-line file is not evidence
about a named section of it.
"""

from __future__ import annotations

import re

from frontend_engineering_visual_authority_rules import (
    FALLBACK_TOKENS,
    PRINT_SURFACE,
    SKILL,
    preflight,
    read,
    section,
    skill_body_lines,
)

# Encodes design-to-build value handoff AC-0013. Raising it is a contract
# change, not a test fix.
BODY_BUDGET = 968


def _step_two() -> str:
    return section(read(SKILL), "### 2. Resolve token values", "\n### ")


def test_the_entrypoint_carries_no_token_declaration_block() -> None:
    """The seed block moved out; only its routing rule stays."""
    text = read(SKILL)
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
    `outline: none`. That citation is not a declaration and must survive.
    """
    assert "var(--ds-color-primary)" in read(SKILL), (
        "the focus-visible rule's token usage was removed; the anchored "
        "predicate exists precisely so this line does not have to go"
    )


def test_the_preflight_routes_to_the_fallback_reference() -> None:
    """Scoped to the PLAN pre-flight, which is where the criterion says the
    pointer lives. Relocating it to an EXECUTE note or a references index
    would leave the criterion false and a whole-file search green."""
    assert FALLBACK_TOKENS.name in preflight(), (
        f"the PLAN pre-flight does not name {FALLBACK_TOKENS.name}; a pointer "
        f"elsewhere in the file does not satisfy the criterion"
    )


def test_the_entrypoint_body_stays_within_budget() -> None:
    """The budget encodes AC-0013 and sits at its ceiling.

    Two responses are admissible when this reds: pay for the addition with a
    removal, or amend AC-0013. Raising the constant alone silently rewrites the
    contract in a suite whose purpose is that the ratchet cannot move quietly.
    """
    n = skill_body_lines()
    assert n <= BODY_BUDGET, (
        f"SKILL.md body is {n} lines against the {BODY_BUDGET}-line budget "
        f"AC-0013 states. Either pay for the addition with a removal, or amend "
        f"AC-0013 in docs/specs/design-to-build-value-handoff/spec.md — raising "
        f"BODY_BUDGET on its own changes the contract without saying so. "
        f"(The catalogue lint hard-errors separately at 1000.)"
    )


def test_print_guidance_is_reachable_from_every_rung() -> None:
    """Regression guard.

    Moving the seed token block out of the entrypoint carried the print/PPT
    CSS with it, into a reference the skill says to load *only* at the lowest
    authority rung. That made the page box, colour-adjust and page-break rules
    unreachable for a slide deck whose tokens came from a taxonomy or an
    incumbent system — while the skill still advertises slide decks and its own
    QA checklist still asks whether print output is correct.
    """
    assert PRINT_SURFACE.exists(), "the print/PPT guidance has no home"
    body = read(PRINT_SURFACE)
    for rule_text in ("@page", "print-color-adjust", "page-break"):
        assert rule_text in body, f"{rule_text} is not in {PRINT_SURFACE.name}"
    assert "@page" not in read(FALLBACK_TOKENS), (
        "print CSS is back in the rung-gated fallback, where a surface on a "
        "higher rung is told never to load it"
    )


def test_the_print_route_is_not_gated_on_a_rung() -> None:
    """Semantic, not positional.

    An earlier version of this guard asserted the link sat *after* the rung
    list. That is a proxy: a rewrite keeping the link at the end of the step
    while re-gating it in prose ("load it when the fallback supplied values")
    passes the position check and reintroduces the defect. What the step must
    carry is the un-gating clause itself.
    """
    step = _step_two()
    assert PRINT_SURFACE.name in step, (
        f"the token-resolution step does not route to {PRINT_SURFACE.name}"
    )
    flattened = re.sub(r"\s+", " ", step).lower()
    assert "whatever rung" in flattened, (
        "the print route carries no clause un-gating it from the rung that "
        "supplied token values; without one a deck on a higher rung is never "
        "told to load it"
    )
