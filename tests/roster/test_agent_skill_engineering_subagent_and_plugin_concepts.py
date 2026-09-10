"""AC11: the planned architecture records slice 3c without reserving it.

This lives in the roster rather than the pack's own suite because it reads
`docs/architecture/agent-skill-engineering.md` — coverage the pack-test boundary
lint classifies as repository-level, since a pack test may not reach above its
own pack. The pack's suite keeps AC11's other two surfaces, the declared-absent
register and the pack README, both of which are pack-local.

`packs/AGENTS.md` states the rule in its second sentence -- "The pack owns its
runtime export and test boundary" -- and `tools/lint-pack-test-boundary.py`
enforces it. Neither was consulted before the original coverage went into the
pack's own suite; a quality review then raised the relocation and it was refuted
as a preference, because the reviewer had not been given either source, and CI
failed on the lint. The rule predates the code; this file is where it puts
repository-level coverage for this slice.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = REPO_ROOT / "docs" / "architecture" / "agent-skill-engineering.md"

# The sentence the 2026-09-04 erratum retired. Held as a literal because it is
# the fixed comparison AC11 quotes for this surface, and matched against
# collapsed whitespace because the document is hard-wrapped: a claim spanning a
# line break is present to a reader and absent to a raw substring test.
RESERVING_SENTENCE = "belong to the slice that completes the eight profiles"

# The three positive facts the spec's Durable Outputs row requires of this
# document. Parametrized so one missing fact reddens on its own rather than
# being masked by the others.
SLICE_THREE_FACTS = (
    "Slice 3 now has portable skills-and-subagents, hooks, and plugin-package "
    "floors, plus the Claude Code runtime profile.",
    "are retired to open extension rather than delivery obligations.",
    "belong to the `3c-r` row of "
    "`docs/product/briefs/agent-skill-engineering.md`, scoped to the shipped ledger.",
)


def _collapsed_architecture() -> str:
    return " ".join(ARCHITECTURE.read_text(encoding="utf-8").split())


def test_architecture_does_not_reserve_the_eight_profile_slice() -> None:
    """AC11: the architecture has its own future-profile promise to remove."""
    assert RESERVING_SENTENCE not in _collapsed_architecture()


@pytest.mark.parametrize("fact", SLICE_THREE_FACTS)
def test_architecture_states_slice_three_runtime_profile_facts(fact: str) -> None:
    """The planned architecture records the implemented slice without reserving it."""
    assert " ".join(fact.split()) in _collapsed_architecture(), fact


def test_architecture_remains_planned() -> None:
    """Promotion to CURRENT is a later slice's work, not this one's.

    Without this, the two checks above are satisfied by a document that also
    claimed a status this slice has no authority to grant.
    """
    assert "STATUS: PLANNED" in _collapsed_architecture()
