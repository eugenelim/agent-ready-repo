"""Content pins for new-spec's conditional shared-substrate preservation reference.

The reference's behavior is proved by graded runs over the frozen evaluation
cases; these pins catch a later edit that drops one of its rules or a citation.
"""

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm/skills/new-spec"
SKILL = SKILL_ROOT / "SKILL.md"
REFERENCE_NAME = "references/shared-substrate-preservation.md"
REFERENCE = SKILL_ROOT / REFERENCE_NAME

RULES = (
    ("helper exclusion", "private helper with a single caller"),
    ("filter exclusion", "behind an explicit filter"),
    ("filter must cover every path", "If any generic read path lacks the filter"),
    ("class stop rule", "counts behavior classes, never files or analogues"),
    ("map never in the spec", "never in `spec.md`"),
    ("later-discovery routing", "controlled amendment and fresh review"),
    ("sustained-finding clause", "a sustained review finding against it contradicts it"),
    ("criterion shape citation", "`assets/spec.md` § Acceptance Criteria"),
    ("rubric citation", "`references/spec-authoring-rubric.md`"),
)


def _reference_text() -> str:
    """Read the reference, failing with a clear message when it is missing."""
    assert REFERENCE.is_file(), f"missing {REFERENCE_NAME}"
    return REFERENCE.read_text(encoding="utf-8")


def _step_three(skill_text: str) -> str:
    """Return SKILL.md procedure step 3, up to the start of step 3a."""
    start = skill_text.index("3. **Surface assumptions")
    end = skill_text.index("3a. **Plan durable outputs")
    return skill_text[start:end]


def test_step_three_loads_the_reference() -> None:
    """Step 3 names the reference so the predicate path is reachable."""
    assert REFERENCE_NAME in _step_three(SKILL.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("rule", "phrase"), RULES, ids=[rule for rule, _ in RULES])
def test_reference_states_rule(rule: str, phrase: str) -> None:
    """Each rule the reference owns, or citation it defers to, is present."""
    assert phrase in " ".join(_reference_text().split()), rule


def test_reference_carries_no_repository_only_paths() -> None:
    """Shipped guidance stays portable: no catalogue-internal docs paths."""
    assert not re.search(r"\bdocs/", _reference_text())
