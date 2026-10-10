"""Impact-evidence routing: grep wording is gone from work-loop and bug-fix.

Spec: docs/specs/core-impact-evidence-routing/spec.md
"""

from __future__ import annotations

from pathlib import Path

# File location: packs/core/tests/pack/test_impact_evidence_routing.py
#   parents[2] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[2]

# Literal paths within the pack — satisfies lint-pack-test-boundary.py.
_WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
_BUG_FIX_SKILL = PACK_ROOT / ".apm" / "skills" / "bug-fix" / "SKILL.md"


def _flat(path: Path) -> str:
    """Return the file's text with whitespace collapsed for phrase matching."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_work_loop_has_no_grep_for_callers() -> None:
    """The DECIDE execution-path check no longer says "grep for callers"."""
    assert "grep for callers" not in _flat(_WORK_LOOP_SKILL).lower()


def test_bug_fix_step_6_has_no_grep_for() -> None:
    """Step 6 of bug-fix says "search", not "Grep for"."""
    text = _flat(_BUG_FIX_SKILL)
    start = text.index("**Trace the root cause backward.**")
    end = text.index(" 7. ", start)
    assert "Grep for" not in text[start:end]


_EXPLORATION_SKILL = (
    PACK_ROOT / ".apm" / "skills" / "repository-exploration" / "SKILL.md"
)
_README = PACK_ROOT / "README.md"
_TESTS_DIR = PACK_ROOT / "tests"

_DESCRIPTION_REQUIRED = (
    "pending decision",
    "The caller keeps the decision",
    "no provider is required",
    "repository-grounding",
    "Do NOT use it to plan, build, or fix",
)
_DESCRIPTION_FORBIDDEN = (
    "blast radius",
    "what calls",
    "what depends on",
    "what breaks",
    "callers and callees",
    "find callers",
)
_PROVIDER_LITERALS = (
    "wicked estate",
    "wicked-estate",
    "code-intelligence pack",
    "code-intelligence skill",
    "`code-intelligence`",
    "packs/code-intelligence",
)


def _description(path: Path) -> str:
    """Return the single-line frontmatter ``description:`` value of a skill."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("description: "):
            return line[len("description: "):]
    raise AssertionError(f"no description line in {path}")


def test_exploration_description_routes_pending_decisions() -> None:
    """The description carries the required phrases and none of the forbidden."""
    desc = _description(_EXPLORATION_SKILL)
    low = desc.lower()
    missing = [s for s in _DESCRIPTION_REQUIRED if s.lower() not in low]
    present = [s for s in _DESCRIPTION_FORBIDDEN if s in low]
    assert not missing, f"missing from description: {missing}"
    assert not present, f"forbidden in description: {present}"
    assert ": " not in desc, "plain YAML scalar must not contain a colon-space"


def test_pack_names_no_provider_outside_tests() -> None:
    """No shipped pack file names a provider pack, skill, or product."""
    offenders: list[str] = []
    for path in sorted(PACK_ROOT.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.is_relative_to(_TESTS_DIR):
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if any(lit in text for lit in _PROVIDER_LITERALS):
            offenders.append(str(path.relative_to(PACK_ROOT)))
    assert not offenders, f"provider names found in: {offenders}"


def test_readme_exploration_section_names_both_callers() -> None:
    """The README section names both workflows that route to the skill."""
    text = _README.read_text(encoding="utf-8")
    start = text.index("## Repository exploration")
    end = text.find("\n## ", start + 1)
    section = text[start : end if end != -1 else len(text)]
    assert "`work-loop`" in section
    assert "`bug-fix`" in section
