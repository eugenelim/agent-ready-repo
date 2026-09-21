"""SKILL.md's close-time branch table must not drift from the spec's own.

`docs/specs/work-item-capture/spec.md` § D9 is the contract for how a
DECIDE-pass scratch note that names a defect is routed once it is not
generalisable practice. `work-loop/SKILL.md` § Capture restates that table
for the agent reading the skill without the spec open. This suite pins the
restatement to the contract so the two cannot silently diverge.

The one permitted difference is citation-shaped: `packs/AGENTS.md` § Shipped
pack content carries no internal-governance citations forbids `SKILL.md`
from citing an internal decision label such as "D4", so the fourth row's
trailing ", per D4" is stripped from the spec side before comparing. Every
other character must match.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "SKILL.md"
)
SPEC = REPO_ROOT / "docs" / "specs" / "work-item-capture" / "spec.md"

_TABLE_HEADER = "| What the note is | Where it goes |"
_CITATION_SUFFIX = re.compile(r",\s*per\s+D\d+\s*$")


def _branch_table_rows(text: str) -> list[tuple[str, str]]:
    """Return the data rows of the `_TABLE_HEADER` pipe table in *text*."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == _TABLE_HEADER)
    rows: list[tuple[str, str]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 2:
            break
        if set(cells[0]) <= set("-") and set(cells[1]) <= set("-"):
            continue  # the `| --- | --- |` separator row
        rows.append((cells[0], cells[1]))
    return rows


def _strip_internal_citation(cell: str) -> str:
    return _CITATION_SUFFIX.sub("", cell)


def test_skill_branch_table_matches_spec_d9_table() -> None:
    skill_rows = _branch_table_rows(SKILL.read_text(encoding="utf-8"))
    spec_rows = _branch_table_rows(SPEC.read_text(encoding="utf-8"))

    assert len(spec_rows) == 4, (
        f"expected § D9's table to carry exactly four rows, found "
        f"{len(spec_rows)}: {spec_rows}"
    )
    normalized_spec_rows = [
        (what, _strip_internal_citation(where)) for what, where in spec_rows
    ]
    assert skill_rows == normalized_spec_rows, (
        "SKILL.md's close-time branch table has drifted from "
        "docs/specs/work-item-capture/spec.md § D9's table (citation "
        "suffixes stripped from the spec side per packs/AGENTS.md):\n"
        f"SKILL.md:  {skill_rows}\n"
        f"§ D9:      {normalized_spec_rows}"
    )


def test_skill_branch_table_names_generalisable_practice_unchanged_route() -> None:
    """Row one must keep the pre-existing route, or the branch is a widening."""
    skill_rows = dict(_branch_table_rows(SKILL.read_text(encoding="utf-8")))
    assert (
        skill_rows["Generalisable practice"]
        == "The existing `project-knowledge` route, unchanged"
    )


def test_skill_branch_table_omits_no_row_and_adds_none() -> None:
    """The branch must gain a row for declined work, never widen row one."""
    skill_rows = _branch_table_rows(SKILL.read_text(encoding="utf-8"))
    whats = [what for what, _ in skill_rows]
    assert whats == [
        "Generalisable practice",
        "Specific, real, blocked",
        "Specific, real, ready now",
        "Specific, failing the razor",
    ]
