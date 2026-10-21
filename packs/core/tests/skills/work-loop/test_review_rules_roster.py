"""VI-6010: `review-rules.json` carries the live reviewer roster verbatim.

While `SKILL.md` holds the reviewer roster table, each roster role's condition,
mode limit, role bullet, and fallback sentence, and the high-risk paragraph,
equal the rules file under the three named normalizations: a trailing
`(full mode)` moves into the mode limit, relative links are rewritten relative
to the skill root (`SKILL.md` sits at the skill root, so they already are), and
a role with no bullet holds an empty boundary. A one-word edit to either side
fails the check. Once the cutover removes the table, the check has nothing to
compare and stops running.

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


def test_vi6010_the_live_roster_equals_the_rules() -> None:
    """VI-6010: AC-0005 and the AC-0006 roster clause hold on the shipped files."""
    live = roster_from_skill((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    assert live is not None, "SKILL.md no longer holds the roster table; retire this check"
    assert [r["role"] for r in live[0]] == [
        "adversarial-reviewer",
        "security-reviewer",
        "experience-reviewer",
        "frontend-reviewer",
        "design-reviewer",
        "quality-engineer",
    ]
    assert roster_problems(SKILL) == []


def test_vi6010_a_one_word_edit_to_the_skill_fails(tmp_path: Path) -> None:
    """VI-6010: changing one word of a bullet, a condition, or the paragraph is caught."""
    skill = _copy(tmp_path)
    original = (skill / "SKILL.md").read_text(encoding="utf-8")
    for old, new, expected in (
        ("guarding control: auth", "guarding control: authn", "security-reviewer.boundary"),
        ("what a reader or adopter sees |", "what a reader or buyer sees |", "experience-reviewer.condition"),
        ("this is its only\ndefinition", "this is its sole\ndefinition", "high_risk_definition"),
        ("Fallback absent: named skip.", "Fallback absent: named stop.", "frontend-reviewer.fallback"),
    ):
        assert old in original, old
        (skill / "SKILL.md").write_text(original.replace(old, new), encoding="utf-8")
        assert any(expected in p for p in roster_problems(skill)), expected
    (skill / "SKILL.md").write_text(original, encoding="utf-8")
    assert roster_problems(skill) == []


def test_vi6010_a_one_word_edit_to_the_rules_fails(tmp_path: Path) -> None:
    """VI-6010: changing one word on the rules side is caught too."""
    skill = _copy(tmp_path)
    rules = json.loads((skill / "review-rules.json").read_text(encoding="utf-8"))
    rules["roles"][1]["condition"] += "!"
    rules["high_risk_definition"] = rules["high_risk_definition"].replace("three", "four", 1)
    (skill / "review-rules.json").write_text(json.dumps(rules), encoding="utf-8")
    problems = roster_problems(skill)
    assert "security-reviewer.condition differs from SKILL.md" in problems
    assert "high_risk_definition differs from SKILL.md" in problems


def test_vi6010_the_check_stops_when_the_roster_table_is_gone(tmp_path: Path) -> None:
    """VI-6010: AC-0006 binds only while `SKILL.md` holds a roster table."""
    skill = _copy(tmp_path)
    (skill / "SKILL.md").write_text("# Skill\n\nNo roster here.\n", encoding="utf-8")
    assert roster_problems(skill) == []
