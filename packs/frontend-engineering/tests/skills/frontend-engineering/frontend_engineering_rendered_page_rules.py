"""Readers for the frontend-engineering rendered-page inspection rule tables.

Shared by the suites in this directory. The module name carries both the pack
and the skill, per `packs/AGENTS.md` § *Writing pack tests*: skills are
independent and several may ship a file of the same short name, so a bare name
here would bind whichever directory reached the path first.

Nothing in this module states a rule. It only reads the tables in
`references/rendered-page-inspection.md`, so that a rule change moves the tests
rather than being restated alongside them.
"""

from __future__ import annotations

import re
from pathlib import Path

# This file sits at `<pack>/tests/skills/frontend-engineering/`.
PACK_ROOT = Path(__file__).resolve().parents[3]
RULES = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "frontend-engineering"
    / "references"
    / "rendered-page-inspection.md"
)

# The pack's severity scale, as the main skill and the reviewer agent already
# use it. The inspection step does not introduce a parallel one.
SEVERITIES = {"Blocker", "Major", "Minor", "Note"}


def read_rules() -> str:
    return RULES.read_text(encoding="utf-8")


def table_rows(markdown: str, heading: str) -> list[list[str]]:
    """Rows of the first pipe table under ``heading``, cells stripped.

    The header and its `---` separator are dropped. A cell is returned exactly
    as written, so an empty cell stays empty rather than disappearing — the
    completeness check depends on being able to see one.
    """
    section = markdown.split(f"\n## {heading}\n", 1)
    if len(section) != 2:
        raise AssertionError(f"no '## {heading}' section in {RULES.name}")
    rows: list[list[str]] = []
    for line in section[1].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:  # the table ended
                break
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", stripped):
            continue  # separator
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows[1:]  # drop the header row


def severity_by_class(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Severity by finding class")}


def resolution_rules(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Severity resolution")}


def required_captures(markdown: str) -> dict[str, tuple[str, str]]:
    """`{capture name: (height predicate, scroll predicate)}` as written."""
    return {
        row[0]: (row[1], row[2]) for row in table_rows(markdown, "Required captures")
    }


def _required_fields(markdown: str, heading: str) -> list[str]:
    return [
        row[0]
        for row in table_rows(markdown, heading)
        if row[1].strip().lower() == "yes"
    ]


def capture_record_fields(markdown: str) -> list[str]:
    return _required_fields(markdown, "Capture record")


def judgement_request_fields(markdown: str) -> list[str]:
    return _required_fields(markdown, "Judgement request")


def step_rules(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Step separation")}


def satisfies(predicate: str, value: int) -> bool:
    """Evaluate a predicate cell such as `<=600`, `>=900`, `>0` or `0`."""
    match = re.fullmatch(r"(<=|>=|<|>|=)?\s*(\d+)", predicate.strip())
    if match is None:
        raise AssertionError(f"unparseable predicate in the table: {predicate!r}")
    op, bound = match.group(1) or "=", int(match.group(2))
    return {
        "<=": value <= bound,
        ">=": value >= bound,
        "<": value < bound,
        ">": value > bound,
        "=": value == bound,
    }[op]


def resolve_severity(
    markdown: str, finding_class: str, judge_supplied: str | None
) -> str:
    """The severity a finding carries, per the rules the reference states.

    This honours the `Severity resolution` table rather than hard-coding the
    outcome: if that table stopped saying the judge's label is discarded, this
    would start returning the judge's label and the provenance test would fail.
    That is the point — the rule is the data, not this function.
    """
    rules = resolution_rules(markdown)
    if rules.get("judge-supplied-severity") != "discarded" and judge_supplied:
        return judge_supplied
    if rules.get("severity-source") != "finding-class":
        raise AssertionError(
            "severity-source is not 'finding-class'; the reference no longer "
            "derives severity from the class"
        )
    return severity_by_class(markdown)[finding_class]


def _scroll_rule_met(rule: str, capture: dict[str, int | str]) -> bool:
    """Whether one capture satisfies a scroll-position rule cell.

    A rule may carry an alternative branch, `>0, or page-scrollable: no`. The
    branch is satisfied only by the value **recorded** on the capture, never
    inferred from a scroll position of 0 — a page nobody scrolled and a page that
    cannot scroll both sit at 0, and telling them apart is the whole point.
    """
    primary, _, alternative = rule.partition(",")
    if satisfies(primary, int(capture["scroll-position"])):
        return True
    if "page-scrollable: no" in alternative:
        return str(capture.get("page-scrollable", "")).lower() == "no"
    return False


def evaluate_capture_set(
    markdown: str, captures: list[dict[str, int | str]]
) -> tuple[str, list[str]]:
    """`("complete", [])` or `("incomplete", [missing capture names])`."""
    missing = [
        name
        for name, (height_rule, scroll_rule) in required_captures(markdown).items()
        if not any(
            satisfies(height_rule, int(c["viewport-height"]))
            and _scroll_rule_met(scroll_rule, c)
            for c in captures
        )
    ]
    return ("incomplete", missing) if missing else ("complete", [])


def evaluate_record(markdown: str, record: dict[str, object]) -> tuple[str, list[str]]:
    """`("usable", [])` or `("unusable", [absent field names])`."""
    absent = [
        f
        for f in capture_record_fields(markdown)
        if f not in record or record[f] is None or record[f] == ""
    ]
    return ("unusable", absent) if absent else ("usable", [])


def findings_for(markdown: str, record: dict[str, object]) -> list[str]:
    """A record that is not usable yields no finding at all."""
    status, _ = evaluate_record(markdown, record)
    if status != "usable":
        return []
    return ["occlusion"]  # stand-in for whatever the judge reported


# ── result states, surfaces, and the observations field ─────────────────────

SKILL = PACK_ROOT / ".apm" / "skills" / "frontend-engineering" / "SKILL.md"


def read_skill() -> str:
    return SKILL.read_text(encoding="utf-8")


INSPECTION_HEADING = "### 5. Rendered-page inspection"


def inspection_section(skill_markdown: str) -> str:
    """Just the rendered-page inspection section of `SKILL.md`, whitespace
    normalized.

    Scoped deliberately. `SKILL.md` carries a shared output-rendering block that
    already contains phrases like "data, not instruction authority", so a check
    run against the whole file would pass on boilerplate whether or not this
    step states the rule — a control that cannot fail.
    """
    if INSPECTION_HEADING not in skill_markdown:
        raise AssertionError(f"no {INSPECTION_HEADING!r} section in SKILL.md")
    section = skill_markdown.split(INSPECTION_HEADING, 1)[1]
    # The section ends at the next top-level heading.
    end = section.find("\n## ")
    if end != -1:
        section = section[:end]
    return " ".join(section.split())


def result_states(markdown: str) -> dict[str, str]:
    """`{result state: "yes"|"no"}` — whether it is a completed inspection."""
    return {
        row[0]: row[1].strip().lower()
        for row in table_rows(markdown, "Result states")
    }


def is_completed_inspection(markdown: str, state: str) -> bool:
    states = result_states(markdown)
    if state not in states:
        raise AssertionError(f"{state!r} is not a declared result state")
    return states[state] == "yes"


def result_surfaces(markdown: str) -> dict[str, str]:
    return {
        row[0]: row[1].strip().lower()
        for row in table_rows(markdown, "Result surfaces")
    }


def observations_rules(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Observations field")}


def manifest_fields(skill_markdown: str) -> list[str]:
    """Field names from the evidence manifest's required-field table.

    Read from `SKILL.md` rather than the reference, because the manifest is the
    adopter-facing surface and the criterion is about what it carries.
    """
    section = skill_markdown.split("**Required fields (", 1)
    if len(section) != 2:
        raise AssertionError("no required-field table found in SKILL.md")
    fields: list[str] = []
    started = False
    for line in section[1].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if started:
                break
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not started:  # header row
            started = True
            continue
        fields.append(cells[0])
    return fields


def observations_value_is_acceptable(markdown: str, value: str) -> bool:
    """Whether a proposed `inspection observations` value satisfies the field.

    Honours the `Observations field` table: if `filenames-only` stopped being
    `rejected`, a bare filename list would start passing and the test that says
    it must not would fail. The rule is the data, not this function.
    """
    rules = observations_rules(markdown)
    if rules.get("filenames-only") != "rejected":
        return True
    tokens = [t for t in re.split(r"[\s,;]+", value.strip()) if t]
    if not tokens:
        return False
    image = re.compile(r".+\.(png|jpe?g|webp|gif|avif)$", re.IGNORECASE)
    return not all(image.fullmatch(t) for t in tokens)


# ── route handling and judge authority ──────────────────────────────────────

def route_rules(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Route recording")}


def judging_rules(markdown: str) -> dict[str, str]:
    return {row[0]: row[1] for row in table_rows(markdown, "Judging captured content")}


def sensitive_view_rules(markdown: str) -> dict[str, str]:
    return {
        row[0]: row[1]
        for row in table_rows(markdown, "Capturing a signed-in or sensitive view")
        if len(row) == 2
    }


def sensitive_view_exposure(markdown: str) -> dict[str, str]:
    """The `Carried to the judge` rows — what a sensitive capture exposes.

    The section holds two tables; this reads the wider one, whose header names
    what is carried rather than a rule and its value.
    """
    rows = table_rows(markdown, "Capturing a signed-in or sensitive view")
    section = markdown.split("\n## Capturing a signed-in or sensitive view\n", 1)[1]
    if "| Carried to the judge |" not in section:
        raise AssertionError(
            "the sensitive-view section no longer names what a capture carries "
            "to the judge"
        )
    start = section.index("| Carried to the judge |")
    exposure: dict[str, str] = {}
    for line in section[start:].splitlines()[1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        if re.fullmatch(r"\|[\s:|-]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) == 2:
            exposure[cells[0]] = cells[1]
    del rows  # the narrow rule table is read by sensitive_view_rules
    return exposure


def recorded_route(markdown: str, url: str) -> str:
    """The route as it is recorded and transmitted, per the `Route recording` table.

    Honours the table: if either exclusion stopped saying `excluded`, the
    corresponding part would survive and the exclusion test would fail.
    """
    rules = route_rules(markdown)

    # Split the three parts first, then reassemble only the ones the table
    # keeps. Stripping one part on the way to the other would drop the second
    # as a side effect, and a mutation that re-admits it would go unnoticed.
    head, sep, fragment = url.partition("#")
    path, qsep, query = head.partition("?")

    route = path
    if rules.get("route-query-string") != "excluded" and qsep:
        route += "?" + query
    if rules.get("route-fragment") != "excluded" and sep:
        route += "#" + fragment
    return route


def judgement_request_route(markdown: str, url: str) -> str:
    """The route stated to the judge. Same rule, one definition."""
    return recorded_route(markdown, url)
