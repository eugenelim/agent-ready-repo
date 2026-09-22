"""The skill's close-time branch table must not drift from the spec's own.

`docs/specs/work-item-capture/spec.md` § D9 is the contract for how a
DECIDE-pass scratch note that names a defect is routed once it is not
generalisable practice. `work-loop/references/capture.md` § Capturing and
routing a note restates that table for the agent reading the skill without
the spec open; `SKILL.md` § Capture points at it. The table moved out of
`SKILL.md` to keep that file under the 1,000-line cap
`tests/roster/test_wave4_durable_outputs_and_release.py` enforces, so this
suite reads the reference. It still pins the restatement to the contract so
the two cannot silently diverge.

The one permitted difference is citation-shaped: `packs/AGENTS.md` § Shipped
pack content carries no internal-governance citations forbids shipped pack
prose from citing an internal decision label such as "D4", so the fifth
row's trailing ", per D4" is stripped from the spec side before comparing.
Every other character must match.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_REFERENCE = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "references"
    / "capture.md"
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


def test_restated_branch_table_matches_spec_d9_table() -> None:
    restated_rows = _branch_table_rows(CAPTURE_REFERENCE.read_text(encoding="utf-8"))
    spec_rows = _branch_table_rows(SPEC.read_text(encoding="utf-8"))

    assert len(spec_rows) == 5, (
        f"expected § D9's table to carry exactly five rows, found "
        f"{len(spec_rows)}: {spec_rows}"
    )
    normalized_spec_rows = [
        (what, _strip_internal_citation(where)) for what, where in spec_rows
    ]
    assert restated_rows == normalized_spec_rows, (
        "capture.md's close-time branch table has drifted from "
        "docs/specs/work-item-capture/spec.md § D9's table (citation "
        "suffixes stripped from the spec side per packs/AGENTS.md):\n"
        f"capture.md: {restated_rows}\n"
        f"§ D9:      {normalized_spec_rows}"
    )


def test_restated_branch_table_names_generalisable_practice_unchanged_route() -> None:
    """Row one must keep the pre-existing route, or the branch is a widening."""
    restated_rows = dict(_branch_table_rows(CAPTURE_REFERENCE.read_text(encoding="utf-8")))
    assert (
        restated_rows["Generalisable practice"]
        == "The existing `project-knowledge` route, unchanged"
    )


def test_restated_branch_table_omits_no_row_and_adds_none() -> None:
    """`AC-0001` membership: the branch gains a row for declined work and
    never widens row one. The declined set is rows two to five; generalisable
    practice is not a member and keeps its existing route. This is the
    membership assertion, distinct from the outcome vocabulary `AC-0002`
    pins."""
    restated_rows = _branch_table_rows(CAPTURE_REFERENCE.read_text(encoding="utf-8"))
    whats = [what for what, _ in restated_rows]
    assert whats == [
        "Generalisable practice",
        "Specific, real, blocked",
        "Specific, real, ready now, ride-along eligible",
        "Specific, real, ready now, not ride-along eligible",
        "Specific, failing the razor",
    ]
