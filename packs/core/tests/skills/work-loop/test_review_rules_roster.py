"""VI-6010: `review-rules.json` carries the live reviewer roster verbatim.

The roster table left `SKILL.md` with the cutover, so the rules file is the only
home of each role, its condition, its boundary, and the high-risk definition. The
parity check below still runs against any copy of the skill that holds a table,
and stops when there is none. A second check keeps every other skill file from
pairing a role with its condition in a table row or list item.

Standard library and pytest only.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"

_TABLE_HEADER = "| The change reaches | Adds |"
_FALLBACK_RE = re.compile(r"(?:Fallback absent: [^.]*\.|Missing `[a-z-]+`[^.]*\.)")


def roster_from_skill(text: str) -> tuple[list[dict[str, object]], str] | None:
    """The roster rows and high-risk paragraph `SKILL.md` holds, or None without a table."""
    lines = text.split("\n")
    if _TABLE_HEADER not in lines:
        return None
    rows = []
    index = lines.index(_TABLE_HEADER) + 2  # skip the separator row
    while index < len(lines) and lines[index].startswith("|"):
        condition, adds = (cell.strip() for cell in lines[index].strip("|").split("|"))
        match = re.search(r"`([a-z-]+)`", adds)
        assert match, f"no role in roster row: {adds}"
        rows.append((match.group(1), condition, adds.endswith("(full mode)")))
        index += 1
    bullets: dict[str, str] = {}
    for number, line in enumerate(lines):
        match = re.match(r"- \*\*`([a-z-]+)`\*\*", line)
        if not match:
            continue
        end = number
        while end + 1 < len(lines) and lines[end + 1].strip():
            end += 1
        bullets[match.group(1)] = "\n".join(lines[number : end + 1])[2:]
    roles = []
    for role, condition, full_only in rows:
        boundary = bullets.get(role, "")
        fallback = _FALLBACK_RE.search(boundary)
        roles.append({
            "role": role,
            "condition": condition,
            "mode_limit": ["full"] if full_only else ["light", "full"],
            "boundary": boundary,
            "fallback": fallback.group(0) if fallback else "",
        })
    start = next(n for n, line in enumerate(lines) if line.startswith("**High-risk work**"))
    end = start
    while lines[end + 1].strip():
        end += 1
    return roles, "\n".join(lines[start : end + 1])


def roster_problems(skill: Path) -> list[str]:
    """What differs between the roster in `skill/SKILL.md` and `skill/review-rules.json`."""
    live = roster_from_skill((skill / "SKILL.md").read_text(encoding="utf-8"))
    if live is None:
        return []
    live_roles, live_high_risk = live
    rules = json.loads((skill / "review-rules.json").read_text(encoding="utf-8"))
    problems = []
    if rules.get("high_risk_definition") != live_high_risk:
        problems.append("high_risk_definition differs from SKILL.md")
    by_role = {r["role"]: r for r in rules.get("roles", [])}
    if list(by_role) != [r["role"] for r in live_roles]:
        problems.append("the rules roles differ from the SKILL.md roster")
    for live_role in live_roles:
        held = by_role.get(live_role["role"], {})
        for key in ("condition", "mode_limit", "boundary", "fallback"):
            if held.get(key) != live_role[key]:
                problems.append(f"{live_role['role']}.{key} differs from SKILL.md")
    return problems


def _copy(tmp_path: Path) -> Path:
    skill = tmp_path / "work-loop"
    skill.mkdir()
    for name in ("SKILL.md", "review-rules.json"):
        shutil.copyfile(SKILL / name, skill / name)
    return skill


def test_vi6010_the_roster_lives_in_the_rules_file_alone() -> None:
    """VI-6010: `SKILL.md` holds no roster table, and the rules file holds every role."""
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert roster_from_skill(skill_text) is None, "SKILL.md still holds a roster table"
    assert "`review-rules.json`" in skill_text
    rules = json.loads((SKILL / "review-rules.json").read_text(encoding="utf-8"))
    assert [r["role"] for r in rules["roles"]] == [
        "adversarial-reviewer",
        "security-reviewer",
        "experience-reviewer",
        "frontend-reviewer",
        "design-reviewer",
        "quality-engineer",
    ]
    assert rules["high_risk_definition"].startswith("**High-risk work**")
    assert roster_problems(SKILL) == []


def test_vi6010_no_other_skill_file_pairs_a_role_with_its_condition() -> None:
    """The rules file and the light-mode reference are the only homes of a role and its condition."""
    rules = json.loads((SKILL / "review-rules.json").read_text(encoding="utf-8"))
    conditional = [r for r in rules["roles"] if r["condition"] and r["kind"] != "always"]
    for path in sorted(SKILL.rglob("*.md")):
        if path.name == "light-mode.md":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith(("|", "- ", "* ", "1. ")):
                continue
            for role in conditional:
                if f"`{role['role']}`" in line and role["condition"].strip("*()").lower() in line.lower():
                    raise AssertionError(f"{path.name}:{number} pairs {role['role']} with its condition")


def test_vi6010_the_check_stops_when_the_roster_table_is_gone(tmp_path: Path) -> None:
    """VI-6010: the parity check binds only while `SKILL.md` holds a roster table."""
    skill = _copy(tmp_path)
    (skill / "SKILL.md").write_text("# Skill\n\nNo roster here.\n", encoding="utf-8")
    assert roster_problems(skill) == []
