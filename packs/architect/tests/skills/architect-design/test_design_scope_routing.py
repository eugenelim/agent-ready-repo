"""Scope routing, and the three rubric surfaces that read the routed spine.

Scope resolves two things — altitude and document count — and both precede
template choice. The ordering is the whole point: a scope stage placed after
template selection reads as correct prose while routing nothing, so it is
asserted by index rather than by presence.

The stage is located by HTML-comment markers, not by a heading or a step
number. A positional delimiter moves whenever the procedure is renumbered, and
every assertion then runs against the wrong span instead of failing.

The three rubric surfaces are checked by a *derived* comparison: the permitted
heading set is parsed out of the three routed templates, so a rubric heading
naming a retired section fails without anyone maintaining a forbidden-word
list. A hand-listed sweep for ``TL;DR`` passes the day a different retired
section reappears.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
DESIGN = PACK_ROOT / ".apm" / "skills" / "architect-design"
SKILL = DESIGN / "SKILL.md"
ASSETS = DESIGN / "assets"
AUTHOR_RUBRIC = DESIGN / "references" / "design-doc-rubric.md"
EVALS = DESIGN / "evals" / "evals.json"

REVIEW = PACK_ROOT / ".apm" / "skills" / "architect-review"
REVIEW_RUBRIC = REVIEW / "references" / "rubric-design-doc.md"
REVIEW_SKILL = REVIEW / "SKILL.md"
REVIEWER_AGENT = PACK_ROOT / ".apm" / "agents" / "design-reviewer.md"

ROUTED = (
    ASSETS / "application-system-design.md",
    ASSETS / "subsystem-design.md",
    ASSETS / "architecture-change-design.md",
)

SCOPE_START = "<!-- scope-determination:start"
SCOPE_END = "<!-- scope-determination:end -->"
TEMPLATE_SELECTION = "<!-- template-selection:start"

STAGE_ZERO = "Shape the concept first (Stage 0)"

ALTITUDES = ("application/system", "subsystem", "architecture change")

# Every section the templates put a model in. Both rubrics must check each
# one: a modelled section with no quality bar is a section nobody grades.
MODEL_BEARING_SECTIONS = (
    "Scope and Context",
    "Structural Model",
    "Runtime Model",
    "Contracts and Invariants",
    "Data and State",
    "Deployment and Operations",
    "Quality Scenarios and Verification",
    "Implementation Mapping",
)

# Headings a rubric may carry that no template section provides. Each is a
# cross-cutting concern or the reviewer's own severity vocabulary, not a
# retired document section.
AUTHOR_EXTRA = {"Cross-cutting", "Decomposition"}
REVIEW_EXTRA = {"Cross-cutting", "Decomposition", "Severity mapping (typical)"}

# The four checks the model-first spine gives no home, and what replaces each.
REPLACEMENTS = (
    "Decision sought",
    "the complete model set",
    "one named question",
    "omit",
)


def _headings(path: Path) -> set[str]:
    """Return a document's `##` heading names, numeric prefix stripped."""
    return {
        re.sub(r"^\d+[.)]\s*", "", line[3:].strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    }


def _is_indented_code(line: str) -> bool:
    """Return whether the line sits in an indented code block.

    Markdown counts indentation in columns, so a leading tab opens a code
    block just as four spaces do. Measuring `startswith("    ")` alone misses
    the tab form.
    """
    width = 0
    for ch in line:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4 - (width % 4)
        else:
            break
    return width >= 4


def _graded_items(body: str) -> list[str]:
    """Return the section's real checklist items, text only.

    A section can keep its heading and grade nothing in several ways, and each
    one satisfies a naive substring search: a bare `- [ ]`, an item inside an
    HTML comment or a fenced example, an indented code block, or an item whose
    text is a placeholder like `...` or `TODO`.

    Containers are tracked rather than listed as forbidden strings: both fence
    styles, closing only on a run at least as long as the opener with nothing
    after it; HTML comments wherever they open; raw `pre`, `code`, `script`
    and `style` blocks; and indentation of four columns, counting a tab as
    Markdown does. An item's wrapped continuation lines are joined
    before it is measured, because the shipped rubrics wrap most items and
    measuring only the marker's line would red on correct content.

    An item counts when it carries at least two words and at least one letter.
    That floor replaces a list of recognised placeholders, which cannot
    converge. It is two rather than three because `- [ ] No strawmen.` is a
    real check in the reviewing rubric — the floor has to admit the shortest
    legitimate item that actually ships, or the control blocks correct work.

    **What this does not reach.** A task item nested four spaces under a parent
    list is read as an indented code block and ignored. No shipped rubric item
    is nested, so nothing is misread today; a future nested item would red its
    section loudly and name it, rather than pass silently. Distinguishing the
    two cases needs list-context tracking, which is a Markdown parser, and the
    failure it would prevent is a visible false red rather than a silent pass.
    """
    items: list[str] = []
    fence: str | None = None
    in_comment = False
    html_block: str | None = None
    pending: list[str] = []

    def flush() -> None:
        if not pending:
            return
        text = " ".join(" ".join(pending).split())
        if len(text.split()) >= 2 and any(ch.isalpha() for ch in text):
            items.append(text)
        pending.clear()

    for line in body.splitlines():
        stripped = line.strip()
        if fence is not None:
            run = len(stripped) - len(stripped.lstrip(fence[0]))
            # A closer indented four columns is still fenced content, so the
            # indentation is measured before the run is accepted.
            if (
                run >= len(fence)
                and not stripped[run:].strip()
                and not _is_indented_code(line)
            ):
                fence = None
            continue
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith(("```", "~~~")):
            flush()
            marker_char = stripped[0]
            fence = marker_char * (len(stripped) - len(stripped.lstrip(marker_char)))
            continue
        if "<!--" in stripped:
            flush()
            if "-->" not in stripped.split("<!--", 1)[1]:
                in_comment = True
            continue
        if html_block is not None:
            if f"</{html_block}>" in stripped:
                html_block = None
            continue
        opened = re.match(r"<(pre|code|script|style)\b", stripped)
        if opened:
            flush()
            if f"</{opened.group(1)}>" not in stripped:
                html_block = opened.group(1)
            continue
        marker = next(
            (m for m in ("- [ ]", "- [x]", "- [X]") if stripped.startswith(m)),
            None,
        )
        if marker is not None:
            flush()
            # An item indented four spaces is an indented code block, not a
            # nested list item; see the docstring.
            if not _is_indented_code(line):
                pending.append(stripped[len(marker):].strip())
            continue
        # A continuation is tested before the indented-code rule, because the
        # shipped rubrics wrap continuations at six spaces and the code rule
        # would otherwise discard the text this item is measured on.
        if pending and stripped:
            pending.append(stripped)
            continue
        flush()
    flush()
    return items


def _rubric_sections(path: Path) -> list[tuple[str, str]]:
    """Return each `##` section of a rubric as (name, body)."""
    out: list[tuple[str, str]] = []
    for chunk in re.split(r"^## ", path.read_text(encoding="utf-8"), flags=re.M)[1:]:
        head, _, body = chunk.partition("\n")
        out.append((re.sub(r"^\d+[.)]\s*", "", head.strip()), body))
    return out


def _template_sections() -> set[str]:
    """The union of every section the three routed templates provide."""
    union: set[str] = set()
    for path in ROUTED:
        union |= _headings(path)
    return union


def _flat(path: Path) -> str:
    """Return the document with line wrapping collapsed."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_scope_stage_is_anchored_by_markers() -> None:
    """One start and one end marker, so no renumbering can relocate them."""
    text = SKILL.read_text(encoding="utf-8")
    assert text.count(SCOPE_START) == 1
    assert text.count(SCOPE_END) == 1
    assert text.count(TEMPLATE_SELECTION) == 1


def test_scope_resolves_before_stage_zero_and_before_template_choice() -> None:
    """Both resolutions precede the choice they are supposed to govern."""
    text = SKILL.read_text(encoding="utf-8")
    scope = text.index(SCOPE_START)
    assert scope < text.index(STAGE_ZERO), "scope stage does not precede Stage 0"
    assert scope < text.index(TEMPLATE_SELECTION), "scope does not precede the template"


def test_the_scope_stage_names_all_three_altitudes() -> None:
    """Altitude is a closed set; an unnamed fourth has no template."""
    text = SKILL.read_text(encoding="utf-8")
    section = " ".join(
        text.split(SCOPE_START, 1)[1].split(SCOPE_END, 1)[0].split()
    ).lower()
    for altitude in ALTITUDES:
        assert altitude in section, altitude


def test_document_count_routes_through_the_decomposition_rubric() -> None:
    """Scope resolves count by the rubric, not by the author's judgement."""
    section = " ".join(
        SKILL.read_text(encoding="utf-8")
        .split(SCOPE_START, 1)[1]
        .split(SCOPE_END, 1)[0]
        .split()
    )
    assert "references/decomposition-rubric.md" in section


def test_the_authoring_rubric_names_only_sections_the_templates_have() -> None:
    """Derived comparison: a retired section fails without a word list."""
    orphans = _headings(AUTHOR_RUBRIC) - _template_sections() - AUTHOR_EXTRA
    assert orphans == set(), f"rubric checks sections no template has: {orphans}"


def test_the_reviewing_rubric_names_only_sections_the_templates_have() -> None:
    """The reviewer converges toward the templates, not away from them."""
    orphans = _headings(REVIEW_RUBRIC) - _template_sections() - REVIEW_EXTRA
    assert orphans == set(), f"review rubric checks sections no template has: {orphans}"


def test_both_rubrics_cover_every_model_bearing_section() -> None:
    """Neither rubric may be silent about a section the templates model.

    The subset checks above run one way: no rubric heading names a section the
    templates lack. Nothing ran the other way, and four model sections —
    Runtime Model, Contracts and Invariants, Data and State, Quality Scenarios
    and Verification — shipped with no reviewing check at all, so a document
    could fail the authoring rubric and pass review.

    ``MODEL_BEARING_SECTIONS`` is a literal here rather than parsed from either
    rubric. A domain read from the artifact under test lets the artifact shrink
    its own coverage: deleting a section would delete the requirement to have
    it.

    Two halves, because a heading is not a guarantee. The set comparison
    catches a deleted section; the per-section assertion catches a section
    emptied of its checks, which leaves the heading in place and would
    otherwise pass. ``_graded_items`` is what makes the second half mean
    something: a bare marker, a marker in an HTML comment, and a marker in a
    fenced example all satisfy a substring search while grading nothing.
    """
    for rubric in (AUTHOR_RUBRIC, REVIEW_RUBRIC):
        missing = set(MODEL_BEARING_SECTIONS) - _headings(rubric)
        assert missing == set(), (rubric.name, sorted(missing))
        # A heading is not a check. Emptying a section keeps its heading, so
        # the heading-set comparison above stays green while the section
        # grades nothing; require a real checklist item under each one.
        for section, body in _rubric_sections(rubric):
            if section in MODEL_BEARING_SECTIONS:
                assert _graded_items(body), (rubric.name, section)


def test_the_four_homeless_checks_are_replaced_not_dropped() -> None:
    """Each retired check has a successor that reads the new spine."""
    rubric = _flat(AUTHOR_RUBRIC)
    for replacement in REPLACEMENTS:
        assert replacement in rubric, replacement


def test_the_replacement_checks_are_checklist_items() -> None:
    """A checklist item is the assertion; a comment does not satisfy it.

    Reuses ``_graded_items`` rather than re-deriving a weaker line test beside
    it. The hand-rolled version accepted a marker inside a comment or a fenced
    example — the same evasions that helper already rejects.
    """
    items = " ".join(
        item
        for _, body in _rubric_sections(AUTHOR_RUBRIC)
        for item in _graded_items(body)
    )
    for replacement in REPLACEMENTS:
        assert replacement in items, replacement


def test_the_description_still_promises_scope_routed_model_first_output() -> None:
    """The IDE-visible promise is what an adopter reads before invoking.

    The authority contract pins the description's two routing ends by equality
    and leaves the middle free, which is what lets this slice rewrite what the
    skill produces. Nothing then checks that the middle still says anything, so
    the promise could be emptied with every procedure test green. This asserts
    the content of that middle without pinning its wording.
    """
    raw = SKILL.read_text(encoding="utf-8").split("---", 2)[1]
    # Parsed, not read off the declaration line: the same description written
    # as a folded or continued YAML scalar is valid and would leave a
    # line-based read inspecting only the word `description:`.
    description = " ".join(str(yaml.safe_load(raw)["description"]).split()).lower()
    middle = description.split("nfr trade-offs.", 1)[1].split("do not use", 1)[0]
    for altitude in ("application", "subsystem", "existing architecture"):
        assert altitude in middle, altitude
    assert "model" in middle
    assert "rationale" in middle


ROUTING_ANCHOR = "Identify the artifact type"


def _routing_region(path: Path) -> str:
    """Return the artifact-type routing list, and nothing after it.

    Bounded to the list itself rather than the whole file. Whole-file presence
    of the three scope words is satisfied by prose elsewhere, so the routing
    list could be deleted or reverted to the retired genre while the check
    stayed green — which is the failure this whole slice exists to prevent.
    """
    text = path.read_text(encoding="utf-8")
    # Anchored on the structural form — a `##` heading in the agent, a
    # numbered step in the skill — not on the phrase anywhere in the file. A
    # second prose mention would otherwise red a file whose routing is intact.
    anchors = list(
        re.finditer(
            rf"^(?:##\s+|\d+\.\s+\*\*){re.escape(ROUTING_ANCHOR)}", text, re.M
        )
    )
    assert len(anchors) == 1, (path.name, len(anchors))
    after = text[anchors[0].end():]
    end = len(after)
    for line_end in re.finditer(r"^(?:##\s|\d+\.\s\*\*)", after, re.M):
        end = line_end.start()
        break
    return " ".join(after[:end].split())


def test_both_reviewers_route_by_scope_not_by_genre() -> None:
    """Either router left on the old genre sends a good document backwards."""
    for path in (REVIEWER_AGENT, REVIEW_SKILL):
        assert "google-style" not in _flat(path).lower(), path.name
        region = _routing_region(path).lower()
        for altitude in ALTITUDES:
            assert altitude in region, (path.name, altitude)
        assert "design-doc" in region or "design doc" in region, path.name


def test_the_evals_carry_one_case_per_routed_scope() -> None:
    """Each routed template has an eval, and each asserts model-first order.

    The roster suite checks that eval ids 3-7 survive, because those are the
    save-mode contracts other tests index by id. Nothing reached the scope
    cases: all three could be deleted, or reduced to a prompt with no
    scope-specific assertion, with every suite green.
    """
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {item["id"]: item for item in evals}

    # One case per routed template, and the generic case that precedes them.
    assert {1, 9, 10, 11} <= set(by_id)

    scope_cues = {
        9: ("person", "system", "container"),
        10: ("subsystem",),
        11: ("baseline", "delta"),
    }
    for eval_id, cues in scope_cues.items():
        case = by_id[eval_id]
        haystack = " ".join(
            [case["expected_output"], *case["assertions"]]
        ).lower()
        for cue in cues:
            assert cue in haystack, (eval_id, cue)
        # The model-first rule is what the whole authoring model turns on, so
        # every scope case states it rather than leaving it to the generic one.
        assert "model" in haystack and "rationale" in haystack, eval_id

    generic = " ".join(
        [by_id[1]["expected_output"], *by_id[1]["assertions"]]
    ).lower()
    assert "scope" in generic
    assert "google-style" not in generic


def test_the_review_eval_names_the_closed_gate_set_with_a_verdict_each() -> None:
    """AC-0070: id 12's expectation text pairs every DA1-DA10 with a verdict.

    Requiring only that the eval mentions the gates would let the
    implementation write its own comparison value, so this asserts the exact
    closed set — all ten, none missing, none invented — not a sample.
    """
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {item["id"]: item for item in evals}
    text = by_id[12]["expected_output"]

    named = re.findall(r"DA(10|[1-9])\b(?:[^.]*?)with a verdict", text)
    assert sorted(int(identifier) for identifier in named) == list(range(1, 11)), (
        "the eval's expectation text must pair every DA1-DA10 with its own "
        "verdict, in one closed set"
    )
