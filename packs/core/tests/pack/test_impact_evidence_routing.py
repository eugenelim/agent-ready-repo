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
