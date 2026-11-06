"""Content pins for the routing table in the shipped work-loop session-resumption reference.

Goal-based: reads the shipped file by literal path; no supervisor process runs.
"""

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
RESUMPTION_MD = PACK_ROOT / ".apm" / "skills" / "work-loop" / "references" / "session-resumption.md"

STEP_TITLE = "Route by what `status` or `next` shows"
FIRST_MATCH = "first match wins, top to bottom"
MAX_ROUTE_CHARS = 160

EXPECTED_ROWS = [
    ("1", "status, next",
     "cap: `status` on a non-terminal run with `retry_count` at or above the cap; "
     "`next` with the `retry-cap` human decision",
     "Retry cap reached: stop and surface it; no replan or approval resets it."),
    ("2", "status, next", "refusal with code `recovery-leftovers`",
     "Remove or restore the paths the refusal detail names, then run next."),
    ("3", "status, next", "any other top-level refusal",
     "Refused (<code>, owner: <owner>): see supervisor.md, Refusals and their owners."),
    ("4", "status", "pending regenerate step",
     "Run next: it commits the pending regenerate step."),
    ("5", "status, next", "terminal",
     "Run status --check, then the Finish checklist and PR."),
    ("6", "status, next", "any other open `human-decision` request",
     "Read this request's reason under Human decisions in supervisor.md: a named human "
     "answers some; for the rest fix the cause, then run next."),
    ("7", "status", "any other open request",
     "Run next and answer the request it issues."),
    ("7", "next", "any other request",
     "Answer the request, write the result outside the spec directory, then run "
     "report <spec-dir> <result.json>."),
    ("8", "status", "none of the above", "Run next."),
]


def _lines() -> list[str]:
    """Return the reference's lines."""
    return RESUMPTION_MD.read_text(encoding="utf-8").splitlines()


def _routing_rows() -> list[tuple[str, ...]]:
    """Return the data rows of the table under step 3 as stripped cell tuples."""
    lines = _lines()
    start = next(i for i, line in enumerate(lines) if STEP_TITLE in line)
    rows: list[tuple[str, ...]] = []
    for line in lines[start + 1:]:
        text = line.strip()
        if text.startswith("4. "):
            break
        if not text.startswith("|"):
            continue
        cells = tuple(c.strip() for c in text.strip("|").split("|"))
        if cells[0] in ("Order", "---") or set(cells[0]) <= {"-", " "}:
            continue
        rows.append(cells)
    return rows


def _route(cell: str) -> str:
    """Strip the backticks that wrap a route string in the table."""
    assert cell.startswith("`") and cell.endswith("`")
    return cell[1:-1]


def test_step_three_is_titled_by_status_or_next() -> None:
    """The routing step carries the new title."""
    assert any(line.lstrip().startswith("3. **" + STEP_TITLE) for line in _lines())


def test_first_match_statement_exists() -> None:
    """The table is introduced by the first-match statement."""
    text = " ".join(RESUMPTION_MD.read_text(encoding="utf-8").split())
    assert FIRST_MATCH in text


def test_table_has_one_row_per_shape_with_the_exact_strings() -> None:
    """Nine rows, in order, with the planned verb, shape and route string."""
    rows = _routing_rows()
    assert len(rows) == len(EXPECTED_ROWS) == 9
    for cells, expected in zip(rows, EXPECTED_ROWS, strict=True):
        assert len(cells) == 4
        assert (cells[0], cells[1], cells[2], _route(cells[3])) == expected


def test_every_route_string_fits_the_length_limit() -> None:
    """Each route string is 160 characters or fewer."""
    for cells in _routing_rows():
        assert len(_route(cells[3])) <= MAX_ROUTE_CHARS


def test_step_one_points_to_the_table_and_ranks_nothing() -> None:
    """Step 1 no longer ranks a refusal and points to the routing table."""
    text = RESUMPTION_MD.read_text(encoding="utf-8")
    assert "the first thing to deal with" not in " ".join(text.split())
    step_one = text.split("1. **Find the run.**", 1)[1].split("2. **", 1)[0]
    assert "routing table in step 3" in " ".join(step_one.split())
