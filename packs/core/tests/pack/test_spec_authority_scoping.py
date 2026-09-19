"""A shipped spec is delivery history, and the loop surfaces have to say so.

Two consumers formed the opposite belief because neither stated the limit:
`adversarial-reviewer` called the spec "the standard" without saying which
spec, and the work-loop's amendment reference described how a contract is
amended without saying what binds it or for how long. Both clauses are prose,
so each is asserted individually — a heading alone is not a check.

Not detected, and named so the blind spots are visible: every arm here matches
a substring of a whole file, so a clause moved into an HTML comment, into a
fenced code block, or out of the section its comment names still satisfies the
assertion. `POINTER_TARGETS` is hand-maintained beside the pointer it covers, so
a target added to that paragraph and not to the tuple is undetected too.
"""
from __future__ import annotations

from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2]
REVIEWER = CORE / ".apm" / "agents" / "adversarial-reviewer.md"
CONTRACT = (
    CORE / ".apm" / "skills" / "new-spec" / "references"
    / "spec-and-plan-contract.md"
)
LIFECYCLE = (
    CORE / ".apm" / "skills" / "work-loop" / "references"
    / "delivery-contract-lifecycle.md"
)


def flat(path: Path) -> str:
    """The file as one whitespace-normalised line, so wrapping is not asserted."""
    return " ".join(path.read_text(encoding="utf-8").split())


REVIEWER_CLAUSES = (
    # Read-order step 2: which spec is the standard, and what the others are.
    "That spec is the standard; a spec that has shipped or been archived is "
    "delivery history, not current-state authority.",
    # A live unshipped peer contract stays inside the standard.
    "A change contradicting one is a finding only if it also breaks the "
    "targeted spec, a live unshipped spec, a cited ADR, or working code.",
    # Drift check 5: the same scoping, where the finding is actually raised.
    "**Spec drift.** This check is about the targeted spec only.",
)

LIFECYCLE_CLAUSES = (
    "living while the plan is drafting",
    "pinned from plan approval",
    "frozen once the spec is `Shipped`",
    "A frozen spec no longer constrains how the system behaves",
    "never by rewriting the shipped spec",
    # The freeze is not total, but only the contract's two licensed pointers
    # and the body's deferral anchors survive it — there is no errata carrier.
    "its status line still takes the two pointers that contract licenses",
    "the deferral anchors its body names still have to resolve",
    # The pointer has to name every section that owns a clause above it, so a
    # reader sent there finds the rule rather than only the staging it sits in.
    "`**Lifecycle:**` and § *A spec directory freezes as a unit, when the "
    "spec ships* for the three stages",
    "§ *Superseding a frozen document* for the status line's two pointers",
    "§ *Spec metadata contract* → **Historical deferral token** for the "
    "anchors a frozen body still owes",
)


#: Every target the lifecycle pointer names, as the contract writes it. Pinning
#: the pointer's own wording cannot catch a renamed target. Four of these five
#: also have roster guards this pack cannot read, so the duplication is what an
#: adopter gets; the fifth, the bold label, was guarded nowhere, so renaming it
#: would have dangled the pointer with every gate green.
POINTER_TARGETS = (
    "**Lifecycle:** specs are",
    "### A spec directory freezes as a unit, when the spec ships",
    "### Superseding a frozen document",
    "### Spec metadata contract",
    "- **Historical deferral token.**",
)


@pytest.mark.parametrize("target", POINTER_TARGETS)
def test_every_section_the_pointer_names_still_exists(target: str) -> None:
    """A pointer is only worth pinning if what it points at is pinned too."""
    body = CONTRACT.read_text(encoding="utf-8")
    assert target in body, f"spec-and-plan-contract.md lost: {target}"


@pytest.mark.parametrize("clause", REVIEWER_CLAUSES)
def test_the_reviewer_scopes_the_standard_to_the_targeted_spec(clause: str) -> None:
    """Without this, a shipped spec elsewhere reads as a live constraint."""
    assert clause in flat(REVIEWER), f"adversarial-reviewer.md lost: {clause}"


@pytest.mark.parametrize("clause", LIFECYCLE_CLAUSES)
def test_the_lifecycle_reference_names_what_a_contract_binds(clause: str) -> None:
    """The amendment machinery below it assumes these three stages."""
    assert clause in flat(LIFECYCLE), f"delivery-contract-lifecycle.md lost: {clause}"
