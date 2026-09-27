"""Readers for the frontend-engineering visual-authority rule tables.

Named for its pack and skill per `packs/AGENTS.md` § *Writing pack tests*: a
bare module name would bind whichever directory reached the path first.

Nothing here states a rule. The rules live in
`references/visual-observation.md`, and the table readers are reused from the
sibling rendered-page module rather than reimplemented, so one pipe policy
governs both references and a rule change moves the reference, not the suite.
"""

from __future__ import annotations

from pathlib import Path

from frontend_engineering_rendered_page_rules import table_rows, unique_keyed

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "frontend-engineering"
SKILL = SKILL_DIR / "SKILL.md"
OBSERVATION = SKILL_DIR / "references" / "visual-observation.md"
FALLBACK_TOKENS = SKILL_DIR / "references" / "fallback-tokens.md"
REVIEWER = PACK_ROOT / ".apm" / "agents" / "frontend-reviewer.md"

# The sweep root for aesthetic-anchor literals. Deliberately narrower than the
# pack: `responsive-layout` legitimately says "linear interpolation", and this
# slice does not touch it.
ANCHOR_ROOTS = (SKILL_DIR, PACK_ROOT / ".apm" / "agents")


def skill_body_lines() -> int:
    """Post-frontmatter body length, counted as the catalogue skill-spec lint
    counts it: split off the frontmatter, then ``splitlines()``.

    This is the canonical counter for the body budget. The lint errors only
    above 1000, so it cannot verify the tighter ceiling the spec sets.
    """
    text = SKILL.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0].strip() == "---", "SKILL.md does not open with frontmatter"
    end = next(i for i, line in enumerate(lines[1:], start=1)
               if line.strip() == "---")
    return len(lines[end + 1:])


def observation_table(heading: str) -> dict[str, list[str]]:
    """Rows of the first table under ``heading``, keyed by first cell."""
    markdown = OBSERVATION.read_text(encoding="utf-8")
    return unique_keyed(table_rows(markdown, heading), heading)


def observation_rows(heading: str) -> list[list[str]]:
    return table_rows(OBSERVATION.read_text(encoding="utf-8"), heading)
