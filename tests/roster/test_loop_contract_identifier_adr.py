"""ADR-0108's confirmation state must match the tool that ships with it.

A decision record stating that no lint enforces it, on the branch that ships
the lint, is a contradiction the repository's guidance forbids resolving
silently. The ADR's `Revisit if` named "a tool that enforces no-reuse for
inline-Markdown items" as a trigger; the `new-spec` skill's alignment checker is
that tool, so the trigger fired on delivery and the record has to say so.

This lives at repository level because `docs/adr/` sits above `packs/core`, and
a test under `packs/core/tests/` whose resolved path climbs out of the pack is
rejected by `tools/lint-pack-test-boundary.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR = REPO_ROOT / "docs/adr/0108-opaque-append-only-loop-contract-identifiers.md"
CHECKER = REPO_ROOT / "packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}$(.*?)(?=^## |\Z)", body, re.S | re.M)
    assert match, f"ADR-0108 has no `## {heading}` section"
    return " ".join(match.group(1).split())


def test_the_tool_the_revisit_trigger_names_actually_ships() -> None:
    """The trigger fired only if the checker exists; assert the premise first."""
    assert CHECKER.is_file(), f"{CHECKER} is the tool the ADR's trigger names"


def test_confirmation_names_the_shipped_check_not_a_reviewer() -> None:
    confirmation = _section(ADR.read_text(encoding="utf-8"), "Confirmation")

    assert "lint/CI" in confirmation, (
        "Confirmation must move from reviewer-checked to the shipped check: "
        f"{confirmation}"
    )
    # The signal names the check by where it lives, not by a repository-only
    # path: the ADR is published and the skill ships to adopters.
    assert "alignment" in confirmation and "`scripts/`" in confirmation, confirmation


def test_revisit_if_records_that_the_trigger_fired_and_the_decision_stands() -> None:
    """Walked against every `Revisit if`, not the flattened document.

    The ADR template carries the statement twice — once in the Decision summary
    and once in Consequences, which owns it — and requires them to agree. An
    assertion over the whole flattened text is satisfied by either copy, so
    editing one and leaving the other stale passed. Both are checked.
    """
    body = ADR.read_text(encoding="utf-8")
    statements = re.findall(r"\*\*Revisit if:?\*\*(.*?)(?=\n\n|\Z)", body, re.S)
    assert len(statements) >= 2, (
        f"expected the summary and Consequences copies, found {len(statements)}"
    )

    for index, statement in enumerate(statements):
        flat = " ".join(statement.split())
        assert "fired" in flat, (
            f"`Revisit if` #{index + 1} must record that the trigger fired: {flat}"
        )
        assert "stands unchanged" in flat, (
            f"`Revisit if` #{index + 1} must record the decision stands: {flat}"
        )

    # The template requires the two to agree; divergence is how one copy goes
    # stale while the other reads correctly.
    normalised = {" ".join(s.split()) for s in statements}
    assert len(normalised) == 1, (
        f"the two `Revisit if` statements must match verbatim: {normalised}"
    )


def test_the_record_never_claims_nothing_enforces_it() -> None:
    """The exact conflict this criterion exists to prevent.

    Scoped to the claim, not the vocabulary. `Mode:` is where the confirmation
    state lives, so that is where `reviewer-checked` would be the defect; the
    ADR also says in prose that meaning-level errors "remain reviewer-checked",
    which is true and must not red this test. A predicate matching the word
    anywhere fails on correct text — the mistake this assertion was written
    with and repaired before landing.
    """
    body = ADR.read_text(encoding="utf-8")
    confirmation = _section(body, "Confirmation")
    mode = re.search(r"\*\*Mode:\*\*\s*([^.]+)\.", confirmation)
    assert mode, f"Confirmation states no `Mode:`: {confirmation}"
    assert "reviewer-checked" not in mode.group(1), (
        f"the confirmation mode is still reviewer-checked: {mode.group(1)}"
    )

    # The stale claim itself, excluding the amendment note that records having
    # held it — otherwise the history reds the check that the history is over.
    live = re.sub(r"\*\*Amended[^*]*\*\*.*?(?=\n\n)", "", body, flags=re.S)
    for stale_claim in ("no lint enforces", "no lint enforced"):
        assert stale_claim not in " ".join(live.split()), stale_claim
