"""Content pins for the routing table in the shipped work-loop session-resumption reference.

Goal-based: reads the shipped file by literal path; no supervisor process runs.
"""

import json
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


REFERENCES = PACK_ROOT / ".apm" / "skills" / "work-loop" / "references"
MODE_MD = REFERENCES / "supervisor-mode.md"
SUPERVISOR_MD = REFERENCES / "supervisor.md"
SCHEMA_MD = REFERENCES / "state-schema.md"
REVIEWER_RULE_PHRASES = (
    "BLOCKED", "stop readiness", "loud blocker", "named skip",
    "record the mandatory reviewer outcome",
)


def _flat(path: Path) -> str:
    """Return a file's text with whitespace collapsed."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _fallback_section() -> str:
    """Return the Single-agent fallback section of supervisor-mode.md, whitespace collapsed."""
    text = MODE_MD.read_text(encoding="utf-8")
    body = text.split("## Single-agent fallback", 1)[1].split("\n## ", 1)[0]
    return " ".join(body.split())


def test_fallback_section_points_to_the_reviewer_rule() -> None:
    """The fallback section names SKILL.md Step 4 and the two review-rules.json fields."""
    section = _fallback_section()
    assert "Step 4. REVIEW" in section
    assert "SKILL.md" in section
    assert "`fallback`" in section and "`mandatory_when`" in section
    assert "review-rules.json" in section


def test_fallback_section_restates_no_reviewer_rule() -> None:
    """The section keeps its subagent sentence and holds none of the rule's phrases."""
    section = _fallback_section()
    assert "The missing capability is the subagent" in section
    for phrase in REVIEWER_RULE_PHRASES:
        assert phrase not in section


def test_supervisor_md_states_json_goes_after_the_verb() -> None:
    """supervisor.md says --json goes after the verb on every verb."""
    text = _flat(SUPERVISOR_MD)
    assert "`--json` goes after the verb" in text


def test_supervisor_md_states_status_and_next_carry_route() -> None:
    """supervisor.md says status and next carry a route field and where its strings live."""
    text = _flat(SUPERVISOR_MD)
    assert "`status` and `next` carry a `route` field" in text
    assert "the routing table in session-resumption.md" in text


def test_state_schema_lists_route_among_status_keys() -> None:
    """The status --json key sentence includes route."""
    text = _flat(SCHEMA_MD)
    sentence = text.split("`status --json` adds", 1)[1].split(". ", 1)[0]
    assert "`route`" in sentence


def test_eval_case_for_undispatchable_reviewer_is_present() -> None:
    """evals.json carries the undispatchable-reviewer case with a prompt, output, and assertions."""
    evals_path = PACK_ROOT / ".apm" / "skills" / "work-loop" / "evals" / "evals.json"
    cases = json.loads(evals_path.read_text(encoding="utf-8"))["evals"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    matches = [c for c in cases if c["id"] == "undispatchable-reviewer-follows-roster-rule"]
    assert len(matches) == 1
    case = matches[0]
    assert "adversarial-reviewer" in case["prompt"]
    assert case["expected_output"].strip()
    assert isinstance(case["assertions"], list) and case["assertions"]
    assert all(isinstance(a, str) and a.strip() for a in case["assertions"])
