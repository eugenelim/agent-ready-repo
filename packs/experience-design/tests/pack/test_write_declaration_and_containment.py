"""The declared writes carry both declaration lines and one shared module.

Subject: the four skills that carry a ``**Writes:**`` line — ``creative-direction``,
``information-architecture``, ``design-principles`` and ``design-system``. Nine
folders are written across this pack, but only these four declare their target on
the literal line this contract fixes; the other writers state their target in
prose, so no predicate separates their write from a read and demanding the line
from them would fail against work nothing performed.

The containment module is one body shipped as several byte-identical copies,
because a skill installs standalone and cannot reach a sibling's ``references/``.
The copy set is derived by reading which skills cite the module, not from a
literal count: the count has already gone stale once, and the copy held by the
only skill that cites the module without writing is the one most likely to drift.

Equality is asserted between the copies rather than against a recorded digest. A
pinned digest reddens on the next legitimate edit to the module and teaches the
reader to update the constant instead of reading the change.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm" / "skills"

# The closed set of declared write targets, fixed literally by the spec this
# pack implements. Stated here so the suite cannot pass by finding nothing.
DECLARED_TARGETS = {
    "creative-direction": "<output_dir>/direction/<slug>.md",
    "design-principles": "<output_dir>/principles/<slug>.md",
    "design-system": "<output_dir>/tokens/<slug>.md",
    "information-architecture": "<output_dir>/screens/<slug>-ia.md",
}

MODULE_REFERENCE = "references/containment.md"

# Strict literal forms: the label, one space, a backticked value, nothing else.
WRITES_LINE = re.compile(r"^\*\*Writes:\*\* `([^`]+)`$", re.MULTILINE)
CONFINEMENT_LINE = re.compile(r"^\*\*Confinement:\*\* `([^`]+)`$", re.MULTILINE)


def _skill_sources() -> dict[str, str]:
    """Every skill directory name mapped to its ``SKILL.md`` text."""
    return {
        d.name: (d / "SKILL.md").read_text(encoding="utf-8")
        for d in sorted(SKILLS.iterdir())
        if (d / "SKILL.md").is_file()
    }


SOURCES = _skill_sources()


def test_the_skill_set_is_readable() -> None:
    """The pack's skills are where this suite looks for them."""
    assert len(SOURCES) >= len(DECLARED_TARGETS), f"only {len(SOURCES)} skills found under {SKILLS}"


def test_exactly_the_declared_writes_carry_a_writes_line() -> None:
    """No skill gains or loses the declaration line unobserved.

    The loose set is compared too: a malformed line — wrong spacing, trailing
    prose, an unbackticked path — would otherwise leave the skill out of the
    strict set and out of this comparison at the same time.
    """
    strict = {name for name, text in SOURCES.items() if WRITES_LINE.search(text)}
    loose = {name for name, text in SOURCES.items() if "**Writes:**" in text}
    assert strict == set(DECLARED_TARGETS), f"skills carrying a **Writes:** line: {sorted(strict)}"
    assert loose == strict, f"malformed **Writes:** line in {sorted(loose - strict)}"


def test_each_declared_write_names_its_canonical_target() -> None:
    """Each declaration line names exactly the target the contract fixes."""
    for name, expected in sorted(DECLARED_TARGETS.items()):
        found = WRITES_LINE.findall(SOURCES[name])
        assert found == [expected], f"{name} declares {found}, expected [{expected!r}]"


def test_each_declared_write_references_the_shared_module() -> None:
    """Each declaring write carries one ``**Confinement:**`` line, naming the module."""
    for name in sorted(DECLARED_TARGETS):
        found = CONFINEMENT_LINE.findall(SOURCES[name])
        assert found == [MODULE_REFERENCE], (
            f"{name} states **Confinement:** {found}, expected [{MODULE_REFERENCE!r}]"
        )


def test_every_skill_citing_the_module_ships_its_own_copy() -> None:
    """Citation and copy agree in both directions.

    A skill installs standalone, so a citation without a local copy resolves to
    nothing, and a copy no skill cites is an orphan that drifts unobserved.
    """
    citing = {name for name, text in SOURCES.items() if MODULE_REFERENCE in text}
    shipping = {p.parents[1].name for p in SKILLS.glob("*/references/containment.md")}
    assert citing, "no skill cites the shared containment module"
    assert citing == shipping, (
        f"cite without a copy: {sorted(citing - shipping)}; "
        f"copy without a citation: {sorted(shipping - citing)}"
    )
    assert set(DECLARED_TARGETS) <= shipping, (
        f"a declared write ships no module copy: {sorted(set(DECLARED_TARGETS) - shipping)}"
    )


def test_every_containment_copy_is_byte_identical() -> None:
    """The module is one body. Equality is between the copies, not to a digest."""
    copies = sorted(SKILLS.glob("*/references/containment.md"))
    assert len(copies) >= 2, f"only {len(copies)} containment copies found — equality is vacuous"
    bodies = {p: p.read_bytes() for p in copies}
    reference = bodies[copies[0]]
    differing = [p.parents[1].name for p, body in bodies.items() if body != reference]
    assert not differing, (
        f"containment.md differs from {copies[0].parents[1].name}'s copy in: {sorted(differing)}"
    )
