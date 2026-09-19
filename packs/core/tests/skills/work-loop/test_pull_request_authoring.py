"""Contract tests for the shipped pull-request template and authoring reference.

Scope note the criteria depend on: the content pins below catch **deletion** of
a required element. They do not certify its wording, and a green run is not
evidence that the prose is good — only that it is still there. The template's
and the reference's wording, and the Finish item's instruction, are living
design corrected in place without an amendment.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop"
TEMPLATE = SKILL / "assets" / "pull-request-template.md"
REFERENCE = SKILL / "references" / "pr-authoring.md"
SKILL_MD = SKILL / "SKILL.md"
SUPERVISOR = SKILL / "references" / "supervisor-mode.md"

EXPECTED_HEADINGS = [
    "What does this change?",
    "Why?",
    "Review focus",
    "How do I verify it?",
    "What did you not change that you considered?",
]
DESTINATIONS = {
    ".github/pull_request_template.md",
    ".gitlab/merge_request_templates/Default.md",
}
TASK_LIST_MARKER = re.compile(r"^\s*- \[[ x]\]", re.M)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _finish_item(text: str) -> str:
    """The Finish-checklist pull-request item, bounded.

    It is the last checkbox in its section, so splitting on the next `- [ ]`
    finds none and runs to end of file -- which made these pins scan half the
    document instead of the item they name. Bound at the next heading too.
    """
    body = text.split("- [ ] **Pull request opened", 1)[1]
    for boundary in ("\n- [ ]", "\n## "):
        body = body.split(boundary, 1)[0]
    return body


def _worked_bodies(text: str) -> list[str]:
    """Fenced blocks carrying the heading as a heading, not as prose.

    A substring match would also count `### What does this change?` or a
    sentence that merely mentions it, so the criterion could pass without the
    heading it names.
    """
    return [b for b in _fences(text)
            if re.search(r"^## What does this change\?$", b, re.M)]


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Half-open line ranges of every fenced block, as CommonMark reads them.

    One scanner for both consumers. Handles backtick and tilde markers, 1-3
    spaces of indentation, and variable fence lengths. An unterminated fence
    runs to end of file -- discarding it would leave its contents to be read as
    rendered Markdown, which is how hidden text got treated as live.
    """
    spans, lines = [], text.splitlines()
    opened, marker = None, None
    for i, line in enumerate(lines):
        opener = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if opened is None:
            if opener:
                opened, marker = i, opener.group(1)
        elif opener and opener.group(1)[0] == marker[0] \
                and len(opener.group(1)) >= len(marker) and not opener.group(2).strip():
            spans.append((opened, i + 1))
            opened, marker = None, None
    if opened is not None:
        spans.append((opened, len(lines)))
    return spans


def _fences(text: str) -> list[str]:
    """Every fenced block's body, openers and closers excluded."""
    lines = text.splitlines()
    return ["\n".join(lines[a + 1:b - 1] if b <= len(lines) else lines[a + 1:b])
            for a, b in _fence_spans(text)]


def _live(text: str) -> str:
    """Markdown that actually renders: fenced spans and HTML comments removed.

    Removal is by line index, not by string replacement: an identical string
    appearing live elsewhere in the document would otherwise be erased too.
    Applied only where LIVE content is meant -- the template's install block and
    per-section guidance live inside comments by design, and the reference's
    worked bodies live inside fences by design.
    """
    lines = text.splitlines()
    fenced = set()
    for a, b in _fence_spans(text):
        fenced.update(range(a, b))
    kept = [line for i, line in enumerate(lines) if i not in fenced]
    return re.sub(r"<!--.*?-->", "", "\n".join(kept), flags=re.S)


def _flat(text: str) -> str:
    """Whitespace-normalised, for searching multi-word fragments in wrapped prose.

    Without this, a fragment like `Do not install it` fails whenever the
    paragraph is reflowed -- a formatting change, not the deletion these pins
    exist to catch. Measured: that fragment breaks at eight wrap widths between
    40 and 95 columns, and `gh api user` at seven.
    """
    return " ".join(text.split())


def _preamble(text: str) -> str:
    """The region above the first rendered heading, where the bans live."""
    first = text.index("\n## ")
    return text[:first]


# ---------------------------------------------------------------- AC-0001..4

def test_the_template_exists():
    assert TEMPLATE.is_file()


def test_the_templates_headings_are_the_five_sections_in_order():
    found = re.findall(r"^## (.+)$", _live(_read(TEMPLATE)), re.M)
    assert found == EXPECTED_HEADINGS


def test_the_template_carries_no_task_list_marker():
    assert not TASK_LIST_MARKER.search(_read(TEMPLATE))


def test_the_templates_install_block_names_both_destinations():
    install = _read(TEMPLATE).split("Install:", 1)[1].split("\n\n", 1)[0]
    # Exact set, not containment: `.github/pull_request_template.md.old` would
    # satisfy a substring check while naming a path no forge reads.
    found = {w for w in install.split() if "/" in w}
    assert found == DESTINATIONS, found


# ------------------------------------------------------------------- AC-0005

def test_the_reference_exists():
    assert REFERENCE.is_file()


def test_the_reference_carries_exactly_two_worked_bodies():
    # Count every fence first: filtering by the heading and then counting means
    # a third fenced block never violates the contract.
    fences = _fences(_read(REFERENCE))
    assert len(fences) == 2, f"expected two fenced blocks, found {len(fences)}"
    assert all(re.search(r"^## What does this change\?$", f, re.M) for f in fences)


def test_exactly_one_worked_body_omits_review_focus():
    worked = _worked_bodies(_read(REFERENCE))
    assert sum(not re.search(r"^## Review focus$", f, re.M) for f in worked) == 1


# ------------------------------------------------------------------- AC-0008

def test_exactly_one_routing_row_targets_the_reference_under_its_predicate():
    # Scoped to the routing section: a row moved to an unrelated table would
    # otherwise still satisfy the criterion while routing nothing.
    section = _live(_read(SKILL_MD)).split("## Conditional-reference routing", 1)[1]
    section = section.split("\n## ", 1)[0]
    rows = [
        r for r in re.findall(r"^\|(.+?)\|(.+?)\|\s*$", section, re.M)
        if "pr-authoring.md" in r[1]
    ]
    assert len(rows) == 1
    assert " ".join(rows[0][0].split()) == "Authoring a pull-request body"
    targets = re.findall(r"\]\(([^)]+)\)", rows[0][1])
    assert targets == ["references/pr-authoring.md"]


# ------------------------------------------------------------------- AC-0010

def test_the_standard_template_sentence_links_to_the_asset():
    line = next(
        line for line in _live(_read(SUPERVISOR)).splitlines()
        if "standard template" in line
    )
    # Bind the link to the phrase itself, not merely to the same line: another
    # link elsewhere on the line would otherwise satisfy the criterion.
    assert "[standard template](../assets/pull-request-template.md)" in line


# --------------------------------------------------- deletion pins (no AC)

def test_the_template_still_states_its_three_prohibitions():
    """Deletion pin. Catches removal; does not certify wording."""
    preamble = _flat(_preamble(_read(TEMPLATE))).lower()
    for fragment in (
        "no round counts",
        "no findings tallies",
        "a result is evidence",
        "the reviewer has it",
    ):
        assert fragment in preamble, fragment


def test_the_template_still_states_the_keep_your_own_convention_clause():
    """Deletion pin. Catches removal; does not certify wording."""
    assert "keep it and delete this file" in _flat(_preamble(_read(TEMPLATE)))


def test_the_template_still_states_its_line_budget_as_a_convention():
    """Deletion pin. Catches removal; does not certify wording."""
    preamble = _flat(_preamble(_read(TEMPLATE)))
    assert re.search(r"Budget: \d+ lines", preamble), "no numeric budget"
    assert "house convention" in preamble


def test_every_template_section_still_carries_a_non_rendering_comment():
    """Deletion pin. Catches removal; does not certify wording."""
    body = _read(TEMPLATE)
    for heading in EXPECTED_HEADINGS:
        after = body.split(f"## {heading}\n", 1)[1]
        assert after.lstrip().startswith("<!--"), heading
        comment = after.split("-->", 1)[0]
        # An empty comment satisfies "starts with <!--" while guiding nobody.
        assert len(comment.split()) >= 8, f"{heading}: comment carries no guidance"


def test_the_review_focus_comment_still_carries_its_discriminator():
    """Deletion pin. Catches removal; does not certify wording."""
    block = _flat(_read(TEMPLATE).split("## Review focus\n", 1)[1].split("\n## ", 1)[0])
    assert "question about the code" in block
    assert "Not what was hard" in block


def test_the_reference_still_tells_the_agent_not_to_install_the_template():
    """Deletion pin. Catches removal; does not certify wording.

    Without it, the instruction that installation is the adopter's call can
    regress while every other gate stays green.
    """
    intro = _flat(_read(REFERENCE).split("## Writing rules", 1)[0])
    for fragment in ("Do not install it", "adopter's call", "keeps it"):
        assert fragment in intro, fragment


def test_the_reference_still_states_seven_writing_rules():
    """Deletion pin over the named section only. Catches removal, not wording."""
    section = _read(REFERENCE).split("## Writing rules\n", 1)[1].split("\n## ", 1)[0]
    rules = re.findall(r"^\d+\. \*\*(.+?)\*\*", section, re.M)
    assert len(rules) == 7
    # Count alone passes after the seven rules are replaced wholesale, so bind
    # each to a distinctive fragment of the rule it guards.
    flat_section = _flat(section)
    for fragment in (
        "Lead with the result",
        "Ground every claim",
        "intended work as done",
        "bullets carry independent items",
        "table earns its place",
        "Collapse only the optional",
        "edit once",
    ):
        assert fragment in flat_section, fragment


def _decision_rows() -> list[dict[str, str]]:
    """The delimited region as closed fields, not natural language.

    Three rounds of pattern-matching over prose each traded a bypass for an
    over-broad failure, and a phrase blacklist still admitted `offer when
    authentication succeeds`. Fields end that: a row is `when | offer | message
    | record`, and every value is compared against an allowed set.
    """
    body = _read(SKILL_MD).split("<!-- pr-capability-decision:start -->", 1)[1]
    body = body.split("<!-- pr-capability-decision:end -->", 1)[0]
    rows = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Every nonblank line must BE a row. Skipping unparsed lines lets a
        # prose instruction sit inside the normative region unvalidated.
        assert line.startswith("- "), f"unparsed line in the decision region: {line}"
        fields = {}
        for part in line[2:].split("|"):
            key, _, value = part.partition(":")
            fields[key.strip()] = _flat(value).strip()
        rows.append(fields)
    return rows


def test_the_capability_decision_table_states_exactly_four_outcomes():
    """Deletion pin on the normative region. Catches removal, not wording."""
    rows = _decision_rows()
    assert len(rows) == 4, f"expected four decision rows, found {len(rows)}"
    assert all(set(r) == {"when", "offer", "message", "record"} for r in rows), rows
    records = " ".join(r["record"] for r in rows)
    for outcome in ("probe-unavailable", "permission-unavailable",
                    "permission-insufficient", "pull-request-opened",
                    "offer-declined"):
        assert outcome in records, outcome
    accepting = [r for r in rows if r["offer"] == "yes"]
    assert len(accepting) == 1, f"expected one accepting row, found {len(accepting)}"
    for role in ("WRITE", "MAINTAIN", "ADMIN"):
        assert role in accepting[0]["when"], f"accepting row omits {role}"
    assert len([r for r in rows if r["offer"] == "no"]) == 3


def test_every_decision_field_holds_an_allowed_value():
    """Closed fields, so an equivalent phrasing cannot smuggle a condition in.

    `offer` and `message` admit fixed tokens only, and `when` is checked against
    an allowlist of permitted inputs -- so `offer when authentication succeeds`
    has nowhere to live.
    """
    # The two probe commands and the enum, and nothing else. Both commands are
    # named in full: a row that says `viewerPermission` without saying how it is
    # read leaves an agent to invent the command.
    permitted = ("gh api user",
                 "gh repo view --json viewerpermission --jq .viewerpermission",
                 "exits", "zero", "non-zero", "unreadable", "outside", "one of",
                 "write", "maintain", "admin", "is", "and", "the")
    for row in _decision_rows():
        assert row["offer"] in {"yes", "no"}, row
        assert row["message"] == "none", row
        leftovers = row["when"].lower().replace("`", " ")
        for term in sorted(permitted, key=len, reverse=True):
            leftovers = leftovers.replace(term, " ")
        leftovers = re.sub(r"[,.\-]", " ", leftovers)
        assert not leftovers.split(), f"row reads an unpermitted input {leftovers.split()}: {row}"


# ----------------------------------------------- hidden-Markdown decoys

def test_a_routing_row_hidden_in_a_comment_does_not_satisfy_the_criterion():
    """A row that renders nowhere routes nobody."""
    section = _live(_read(SKILL_MD)).split("## Conditional-reference routing", 1)[1]
    assert "<!--" not in section.split("\n## ", 1)[0]


def test_the_templates_headings_are_read_from_rendered_markdown_only():
    """A heading inside a fence is sample text, not a section of this document."""
    live = _live(_read(TEMPLATE))
    assert "```" not in live
    assert len(re.findall(r"^## ", live, re.M)) == len(EXPECTED_HEADINGS)


# ------------------------------------ the examples must model the template

def test_the_worked_bodies_use_only_the_templates_headings_in_its_order():
    """An example is a model; a model of the wrong shape teaches the wrong shape.

    Without this, editing the template's headings leaves the reference's worked
    bodies demonstrating sections that no longer exist, and both files stay
    green because each is internally consistent.
    """
    template_headings = re.findall(r"^## (.+)$", _live(_read(TEMPLATE)), re.M)
    for body in _worked_bodies(_read(REFERENCE)):
        headings = re.findall(r"^## (.+)$", body, re.M)
        unknown = [h for h in headings if h not in template_headings]
        assert not unknown, f"worked body uses headings the template lacks: {unknown}"
        assert headings == [h for h in template_headings if h in headings], (
            f"worked body orders sections differently from the template: {headings}"
        )


def test_the_template_renders_to_its_headings_and_nothing_else():
    """The design rests on the guidance not reaching the reviewer.

    Every rule the template states lives in an HTML comment, so a submitted but
    unfilled body shows five headings. If any guidance moved into rendered
    prose, every pull request would carry its own instructions.
    """
    rendered = [line for line in _live(_read(TEMPLATE)).splitlines() if line.strip()]
    assert rendered == [f"## {h}" for h in EXPECTED_HEADINGS]


def test_the_finish_item_names_no_forbidden_command_where_it_decides():
    """T4's negative control, which was promised and then left unwired.

    `_finish_item()` existed but nothing called it, so nothing enforced the ban.
    The ban is bounded to the DECISION region: the explanatory tail below it may
    name `gh auth status`, because explaining why a status is read is not
    reading one.
    """
    item = _finish_item(_read(SKILL_MD))
    decision = item.split("<!-- pr-capability-decision:start -->", 1)[1]
    decision = decision.split("<!-- pr-capability-decision:end -->", 1)[0]
    lowered = _flat(decision).lower()
    for forbidden in ("gh auth status", "stderr", "error message", "diagnostic"):
        assert forbidden not in lowered, f"the decision region reads {forbidden!r}"
    # And the tail that explains the choice is still present, so the ban was not
    # satisfied by deleting the rationale.
    assert "gh auth status" in _flat(item).lower(), "the rationale was removed"


def test_the_repositorys_own_template_is_authoritative():
    """The installer preserves an existing convention; the loop must honour it.

    Directing authors to the bundled asset unconditionally would hand reviewers
    a body in a shape their repository does not use — and would contradict the
    install step that deliberately kept theirs.
    """
    item = _flat(_finish_item(_read(SKILL_MD))).lower()
    assert "this repository's own pull-request template" in item
    assert "fall back" in item

    intro = _flat(_read(REFERENCE).split("## Writing rules", 1)[0]).lower()
    assert "authoritative" in intro
    assert "only when the repository has none" in intro
