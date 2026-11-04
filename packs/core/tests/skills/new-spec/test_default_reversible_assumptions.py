"""Content tests for the default-reversible-assumptions gate in `new-spec` step 3.

Each test reads one whitespace-flattened slice of the shipped `SKILL.md` and
asserts the literal text one acceptance criterion fixes. The file hard-wraps
its prose, so every check runs on flattened text.
"""

from __future__ import annotations

from pathlib import Path

_PACK = Path(__file__).resolve().parents[3]
_SKILL = _PACK / ".apm" / "skills" / "new-spec" / "SKILL.md"

_STEP_START = "3. **Surface assumptions before writing any spec body"
_STEP_END = "\n3a. "

AC_0001 = (
    "An item waits for the owner when it is a product or preference call, a "
    "question of who may approve, sign off, or decide, an item touching a "
    "protected class, an irreversible choice, or an item with no stated default."
)
AC_0002 = "Where you cannot tell whether an item is one of these, it is."
AC_0003_A = "Every other item is reversible with a stated default"
AC_0003_B = "It proceeds on that default without waiting."
AC_0004 = "check it against the reversibility test in the routing table above"
AC_0005 = (
    "Reversible means undoing it needs no migration, no external side effect, "
    "and no change to a user-visible contract"
)
AC_0006 = (
    "The protected classes are a security boundary, data loss or durability, "
    "migration or persisted state, a public interface, and an irreversible "
    "operation."
)
AC_0007 = (
    "Defaulting decides only whether an item waits; a load-bearing claim still "
    "routes by the routing table."
)
AC_0009 = (
    "- <category>: <item> — default: <what you build on>; "
    "if wrong: <what changes>"
)
AC_0010 = (
    "**Surface the Unverified list and wait** for confirmation or correction "
    "of every item still in it"
)
AC_0011 = (
    "When Unverified had candidates and sorting moved every one to "
    "`## Defaulted`, surface the block and proceed without waiting."
)
AC_0012 = (
    "When there were no Unverified candidates at all, name the highest-stakes "
    "Verified item. If it is a product or preference call, a question of who "
    "may approve, sign off, or decide, an item touching a protected class, or "
    "an irreversible choice, ask the user to confirm *that one specifically* "
    "and wait"
)
AC_0013 = (
    "Otherwise list it under `## Defaulted` with `default: as verified; if "
    "wrong: <what changes>` and proceed. It stays a settled fact and is not "
    "written to `## Assumptions`."
)
AC_0014 = (
    "Write each item sorted out of Unverified into the spec's `## Assumptions` "
    "as a defaulted assumption, in the line format that section's comment gives."
)
AC_0025 = "A default does not approve the spec."
AC_0015_GATE = "**Surface the Unverified list and wait**"
AC_0015_AFTER = "Only once every waiting item has been signed off"
AC_0017 = "before every waiting Unverified item has been confirmed"


def _flat(text: str) -> str:
    """Collapse every whitespace run to one space."""
    return " ".join(text.split())


def _skill() -> str:
    """Return the whole flattened `SKILL.md`."""
    return _flat(_SKILL.read_text(encoding="utf-8"))


def _step_3() -> str:
    """Return step 3 of `SKILL.md`, flattened."""
    raw = _SKILL.read_text(encoding="utf-8")
    start = raw.index(_STEP_START)
    return _flat(raw[start : raw.index(_STEP_END, start)])


def _anti_patterns() -> str:
    """Return the anti-patterns section of `SKILL.md`, flattened."""
    raw = _SKILL.read_text(encoding="utf-8")
    return _flat(raw[raw.index("## Anti-patterns") :])


def test_ac_0001_wait_list() -> None:
    assert AC_0001 in _step_3()


def test_ac_0002_tie_break() -> None:
    assert AC_0002 in _step_3()


def test_ac_0003_default_proceeds() -> None:
    step = _step_3()
    assert AC_0003_A in step
    assert AC_0003_B in step


def test_ac_0004_reversibility_check() -> None:
    assert AC_0004 in _step_3()


def test_ac_0005_reversibility_sentence_once() -> None:
    assert _skill().count(AC_0005) == 1


def test_ac_0006_protected_classes_once() -> None:
    assert _skill().count(AC_0006) == 1


def test_ac_0007_defaulting_scope() -> None:
    assert AC_0007 in _step_3()


def test_ac_0008_fence_headings_in_order() -> None:
    raw = _SKILL.read_text(encoding="utf-8")
    start = raw.index(_STEP_START)
    step = raw[start : raw.index(_STEP_END, start)]
    fence = step.split("```")[1]
    positions = [fence.index(h) for h in ("## Verified", "## Unverified", "## Defaulted")]
    assert positions == sorted(positions)


def test_ac_0009_defaulted_line() -> None:
    assert AC_0009 in _step_3()


def test_ac_0010_gate_opening() -> None:
    assert AC_0010 in _step_3()


def test_ac_0011_all_defaulted_proceeds() -> None:
    assert AC_0011 in _step_3()


def test_ac_0012_no_candidates_highest_stakes() -> None:
    assert AC_0012 in _step_3()


def test_ac_0013_verified_item_defaulted() -> None:
    assert AC_0013 in _step_3()


def test_ac_0014_defaulted_into_assumptions() -> None:
    assert AC_0014 in _step_3()


def test_ac_0025_default_is_not_approval() -> None:
    assert AC_0025 in _step_3()


def test_ac_0015_order() -> None:
    step = _step_3()
    assert (
        step.index(AC_0001) < step.index(AC_0015_GATE) < step.index(AC_0015_AFTER)
    )


def test_ac_0017_anti_pattern() -> None:
    assert AC_0017 in _anti_patterns()
