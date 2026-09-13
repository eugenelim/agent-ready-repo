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

    **Pipe policy: a literal `|` inside a cell is not supported.** Splitting on
    every pipe would shift later cells silently — a pipe in a description column
    moves a `yes` out of the Required column and quietly drops a required field.
    Rather than inventing an escape this markdown does not use, a row whose cell
    count does not match its header is rejected outright.
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
    if not rows:
        raise AssertionError(f"'## {heading}' in {RULES.name} holds no table")

    header, body = rows[0], rows[1:]
    for row in body:
        if len(row) != len(header):
            raise AssertionError(
                f"'## {heading}' row {row!r} has {len(row)} cells against a "
                f"{len(header)}-cell header — an unescaped '|' in a cell shifts "
                f"every cell after it"
            )
    return body


def unique_keyed(rows: list[list[str]], heading: str) -> dict[str, list[str]]:
    """`{row[0]: row}` refusing a duplicate key.

    A dict comprehension keeps the last duplicate and discards the first in
    silence. That is how "every class has exactly one severity" became a rule
    that could not fail on the one mutation it exists to catch: a second
    `occlusion` row carrying `Minor` simply replaced the first.
    """
    out: dict[str, list[str]] = {}
    for row in rows:
        if row[0] in out:
            raise AssertionError(
                f"'## {heading}' declares {row[0]!r} more than once; a rule "
                f"table row key must be unique or the rule it states is ambiguous"
            )
        out[row[0]] = row
    return out


def severity_by_class(markdown: str) -> dict[str, str]:
    rows = unique_keyed(table_rows(markdown, "Severity by finding class"), "Severity by finding class")
    return {key: row[1] for key, row in rows.items()}


def finding_content_rules(markdown: str) -> dict[str, str]:
    rows = unique_keyed(table_rows(markdown, "Finding content"), "Finding content")
    return {key: row[1] for key, row in rows.items()}


def resolution_rules(markdown: str) -> dict[str, str]:
    rows = unique_keyed(table_rows(markdown, "Severity resolution"), "Severity resolution")
    return {key: row[1] for key, row in rows.items()}


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
    rows = unique_keyed(table_rows(markdown, "Step separation"), "Step separation")
    return {key: row[1] for key, row in rows.items()}


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


def _scroll_pair_rule(markdown: str) -> str:
    """The scroll-position rule a captured height must satisfy.

    Taken from a `*-scrolled` row rather than written here, so the unscrollable
    branch stays defined in one place — the table.
    """
    rules = required_captures(markdown)
    return rules["short-scrolled"][1]


def evaluate_capture_set(
    markdown: str, captures: list[dict[str, int | str]]
) -> tuple[str, list[str]]:
    """`("complete", [])` or `("incomplete", [missing requirement names])`.

    Two rules, both scoped to **one route at a time**, because the criteria are
    "for each inspected route" and "for each viewport height captured":

    1. Every route supplies each of the named required captures — the two height
       bands, each at rest and scrolled.
    2. At every height a route actually captured, including heights beyond the
       two required bands, that route has both an at-rest capture and a scrolled
       one (or a recorded `page-scrollable: no`).

    A flat scan over all captures satisfies neither: it lets one route cover the
    short band while another covers the tall one, and it never looks at a height
    the table does not name.
    """
    if not captures:
        return ("incomplete", ["no captures"])

    by_route: dict[str, list[dict[str, int | str]]] = {}
    for capture in captures:
        by_route.setdefault(str(capture.get("route", "")), []).append(capture)

    missing: list[str] = []
    at_rest_rule = required_captures(markdown)["short-at-rest"][1]
    scrolled_rule = _scroll_pair_rule(markdown)

    for route, route_captures in sorted(by_route.items()):
        # Rule 1 — the named required captures, within this route.
        for name, (height_rule, scroll_rule) in required_captures(markdown).items():
            if not any(
                satisfies(height_rule, int(c["viewport-height"]))
                and _scroll_rule_met(scroll_rule, c)
                for c in route_captures
            ):
                missing.append(f"{name} (route {route})")

        # Rule 2 — every height this route actually captured carries the pair,
        # but ONLY because the reference says so. The quantifier is shipped
        # content, not something this module supplies; a check that authors its
        # own rule asserts behaviour the pack never promised an adopter.
        if capture_set_rules(markdown).get(
            "every-captured-height-needs-the-pair"
        ) != "required":
            continue
        for height in sorted({int(c["viewport-height"]) for c in route_captures}):
            at_height = [
                c for c in route_captures if int(c["viewport-height"]) == height
            ]
            if not any(_scroll_rule_met(at_rest_rule, c) for c in at_height):
                missing.append(f"at-rest at {height}px (route {route})")
            if not any(_scroll_rule_met(scrolled_rule, c) for c in at_height):
                missing.append(f"scrolled at {height}px (route {route})")

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
    rows = unique_keyed(table_rows(markdown, "Observations field"), "Observations field")
    return {key: row[1] for key, row in rows.items()}


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
    rows = unique_keyed(table_rows(markdown, "Route recording"), "Route recording")
    return {key: row[1] for key, row in rows.items()}


def judging_rules(markdown: str) -> dict[str, str]:
    rows = unique_keyed(table_rows(markdown, "Judging captured content"), "Judging captured content")
    return {key: row[1] for key, row in rows.items()}


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


# ── verdict, precedence, and the shipped height rule ────────────────────────

SEVERITY_ORDER = ("Blocker", "Major", "Minor", "Note")


def verdict_rules(markdown: str) -> dict[str, str]:
    rows = unique_keyed(table_rows(markdown, "Inspection verdict"), "Inspection verdict")
    return {key: row[1] for key, row in rows.items()}


def capture_set_rules(markdown: str) -> dict[str, str]:
    """The extra rules stated under `Required captures` beyond the four rows."""
    section = markdown.split("\n## Required captures\n", 1)[1]
    out: dict[str, str] = {}
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("| every-captured-height-needs-the-pair |"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            out[cells[0]] = cells[1]
    return out


def resolve_class(markdown: str, fitting: list[str]) -> str:
    """The class a failure takes when it fits more than one.

    Honours the `multi-class-failure` rule rather than hard-coding most-severe:
    if the reference stopped saying that, this would return the first class
    offered and the precedence test would fail.
    """
    if not fitting:
        raise AssertionError("a finding must fit at least one class")
    if resolution_rules(markdown).get("multi-class-failure") != "most-severe-class":
        return fitting[0]
    mapping = severity_by_class(markdown)
    return min(fitting, key=lambda c: SEVERITY_ORDER.index(mapping[c]))


def inspection_result(
    markdown: str,
    captures: list[dict[str, int | str]],
    findings: list[dict[str, object]] | None = None,
) -> dict[str, str]:
    """`{"state": ..., "verdict": ...}` — did it run, and did it pass.

    Two questions, two answers. "The browser would not start" and "the page is
    broken" are both not-a-pass and are not the same thing.
    """
    findings = findings or []
    set_status, _ = evaluate_capture_set(markdown, captures)
    # `evaluate_capture_set` answers "is the set complete"; the shipped
    # `Result states` table is the authority on what that state is called.
    state = "completed" if set_status == "complete" else set_status
    rules = verdict_rules(markdown)

    blocking = rules.get("verdict-blocking-severity", "Blocker")
    unresolved = [
        f for f in findings
        if not f.get("resolved")
        and resolve_severity(markdown, str(f["class"]), None) == blocking
    ]
    if rules.get("verdict-source") != "findings":
        raise AssertionError("the reference no longer derives the verdict from findings")
    verdict = "fail" if (unresolved and rules.get("blocking-finding-verdict") == "fail") else "pass"
    return {"state": state, "verdict": verdict}


def is_completed_inspection_result(markdown: str, result: dict[str, str]) -> bool:
    """A completed inspection needs BOTH a completed state and a passing verdict."""
    rules = verdict_rules(markdown)
    if rules.get("completed-inspection-requires") != "completed-state-and-passing-verdict":
        return result["state"] == "completed"
    return result["state"] == "completed" and result["verdict"] == "pass"
