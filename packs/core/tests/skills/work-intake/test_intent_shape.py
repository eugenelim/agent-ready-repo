"""Construction tests for the intent metadata shape contract.

Covers T1 of the intent metadata shape contract's plan: the contract
table and the preamble reader that together decide every field rule. The fixture
corpus authored here is reused by T2, T3, T4 and T6, so a rule change has one
place to break rather than five.

Two shapes in this file are load-bearing rather than incidental:

* ``_preamble`` composes a field line four ways — bare, backticked, commented,
  and backticked *and* commented on one line. The composed case dominates the
  real corpus and is the one an order-sensitive normalization fails, so every
  accept case is re-asserted through all four.
* The body-level fixtures place a ``- **Status:**`` line and a bolded
  ``- **Authority:**`` line below the first ``## `` heading. Both shapes are in
  the real corpus and a whole-file pattern match corrupts them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
)


# Pack-and-skill-qualified, per `packs/AGENTS.md`: skills are independent and
# several may ship a same-named script, so a bare name would bind whichever
# directory reached the path first and then cache it for every later importer.
MODULE_NAME = "core_work_intake_intent_shape"


def _load_module():
    """Load the skill's ``intent_shape`` module by path under a unique name."""
    path = SCRIPTS / "intent_shape.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: a frozen dataclass resolves its own module.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


intent_shape = _load_module()

REQUIRED = ("Owner", "Slug", "Level", "Status")
RETIRED = ("Type", "Raised", "Stage", "Parent", "Source", "Authority")

# A conforming baseline every fixture derives from. Kept minimal: a case that
# fails must fail for the one reason its name states.
BASE = {
    "Owner": "eugenelim",
    "Slug": "a-live-intent",
    "Level": "feature",
    "Status": "Draft",
}


# ── fixture composition ───────────────────────────────────────────────────────
# BARE is the value as written. The other three wrap it the way the corpus and
# both packs' templates do; all four must reach the same verdict.
BARE = "bare"
BACKTICKED = "backticked"
COMMENTED = "commented"
COMPOSED = "backticked-and-commented"
SHAPES = (BARE, BACKTICKED, COMMENTED, COMPOSED)


def _wrap(value: str, shape: str) -> str:
    if shape == BARE:
        return value
    if shape == BACKTICKED:
        return f"`{value}`"
    if shape == COMMENTED:
        return f"{value} <!-- why this field exists -->"
    if shape == COMPOSED:
        # The comment trails the closing backtick. Stripping backticks first
        # no-ops here, which is the ordering defect this shape exists to catch.
        return f"`{value}` <!-- why this field exists -->"
    raise AssertionError(shape)


def _preamble(fields: dict[str, str] | None = None, *, shape: str = BARE,
              body: str = "") -> str:
    """Render an intent whose preamble carries ``fields``.

    ``body`` is appended below a ``## Outcome`` heading, so anything it contains
    is outside the preamble region by construction.
    """
    fields = BASE if fields is None else fields
    lines = ["# Intent: a rendered fixture", ""]
    lines += [f"- **{name}:** {_wrap(value, shape)}" for name, value in fields.items()]
    lines += ["", "## Outcome", "", "An outcome sentence.", ""]
    if body:
        lines += [body, ""]
    return "\n".join(lines)


def _without(field: str) -> dict[str, str]:
    return {k: v for k, v in BASE.items() if k != field}


def _with(**overrides: str) -> dict[str, str]:
    merged = dict(BASE)
    merged.update(overrides)
    return merged


def _fields_at_fault(text: str) -> set[str]:
    """Field names the validator refuses, as a set for order-free assertions."""
    return {v.field for v in intent_shape.validate_live_intent(text)}


def _accepted(text: str) -> bool:
    return not intent_shape.validate_live_intent(text)


# ── AC-0001: the required tier ────────────────────────────────────────────────


@pytest.mark.parametrize("field", REQUIRED)
def test_ac0001_refuses_a_preamble_missing_a_required_field(field: str) -> None:
    """Each of the four required fields is refused by name when absent."""
    violations = intent_shape.validate_live_intent(_preamble(_without(field)))
    assert violations, f"{field} absent was accepted"
    assert field in {v.field for v in violations}


def test_ac0001_accepts_the_conforming_baseline() -> None:
    """The baseline every negative case derives from is itself accepted."""
    assert _accepted(_preamble())


# ── AC-0002: the Status vocabulary ────────────────────────────────────────────

# Pinned literally, once. The accept cases below iterate the implementation's
# own table so a new member needs no test edit, but an implementation whose
# table gained or lost a member has to fail somewhere — and iterating a table
# against itself cannot fail. This assertion is that somewhere.
STATUS_BARE_VALUES = frozenset(
    {"Draft", "Accepted", "Fulfilled", "Withdrawn", "Cancelled"}
)


def test_ac0002_status_bare_vocabulary_is_exactly_the_five_named_values() -> None:
    assert frozenset(intent_shape.STATUS_BARE_VALUES) == STATUS_BARE_VALUES


@pytest.mark.parametrize("value", sorted(STATUS_BARE_VALUES))
@pytest.mark.parametrize("shape", SHAPES)
def test_ac0002_accepts_each_bare_status_value(value: str, shape: str) -> None:
    """AC-0002 accept path, re-asserted through all four value shapes."""
    assert _accepted(_preamble(_with(Status=value), shape=shape))


@pytest.mark.parametrize("shape", SHAPES)
def test_ac0002_accepts_the_superseded_by_parameterized_form(shape: str) -> None:
    text = _preamble(_with(Status="Superseded by a-live-intent"), shape=shape)
    assert _accepted(text)


@pytest.mark.parametrize(
    "value",
    [
        "Shipped",              # a spec status, not an intent status
        "draft",                # case is not a member
        "Superseded by",        # the form with no slug payload
        "Superseded by ",       # payload present but empty
        "Superseded",           # the bare word is not a member
        "",                     # empty is absent, and absence is AC-0001's
    ],
)
def test_ac0002_refuses_a_status_value_outside_the_vocabulary(value: str) -> None:
    assert "Status" in _fields_at_fault(_preamble(_with(Status=value)))


# ── AC-0022: the three closed vocabularies ────────────────────────────────────


@pytest.mark.parametrize(
    ("field", "good", "bad"),
    [
        ("Kind", "outcome", "objective"),
        ("Scale", "app", "enterprise"),
        ("Maturity", "greenfield", "legacy"),
    ],
)
def test_ac0022_closed_vocabulary_accepts_a_member_and_refuses_a_non_member(
    field: str, good: str, bad: str
) -> None:
    assert _accepted(_preamble(_with(**{field: good})))
    assert field in _fields_at_fault(_preamble(_with(**{field: bad})))


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize(
    ("field", "good"),
    [("Kind", "opportunity"), ("Scale", "business-unit"), ("Maturity", "brownfield")],
)
def test_ac0022_accepts_each_member_through_every_value_shape(
    field: str, good: str, shape: str
) -> None:
    assert _accepted(_preamble(_with(**{field: good}), shape=shape))


# ── AC-0003: Level carries a tier and no value rule ───────────────────────────


@pytest.mark.parametrize(
    "value",
    ["feature", "capability", "product-vision", "product-strategy", "epic", "squiggle"],
)
def test_ac0003_never_refuses_level_for_its_value(value: str) -> None:
    """ADR-0033 D2 owns the open set, so no value rule may reject one."""
    assert "Level" not in _fields_at_fault(_preamble(_with(Level=value)))


# ── AC-0004 / AC-0034: the normalization stage ────────────────────────────────


def test_ac0034_normalization_discards_the_comment_before_stripping_backticks() -> None:
    """The composed shape reduces to the bare value.

    Asserted on the stage directly, not only through a verdict, because the
    reverse order yields a value that is still backticked and every downstream
    rule then fails for the wrong reason.
    """
    assert intent_shape.normalize_value("`feature` <!-- an altitude -->") == "feature"
    assert intent_shape.normalize_value("`feature`") == "feature"
    assert intent_shape.normalize_value("feature <!-- an altitude -->") == "feature"
    assert intent_shape.normalize_value("feature") == "feature"


def test_ac0034_a_value_that_is_only_a_comment_is_absent_not_malformed() -> None:
    """The `frame-intent` template seeds `Parent intent:` in exactly this shape."""
    assert intent_shape.normalize_value("<!-- the parent's slug, or none -->") == ""
    text = _preamble(_with(**{"Parent intent": "<!-- the parent's slug, or none -->"}))
    assert "Parent intent" not in _fields_at_fault(text)


def test_ac0034_an_absent_optional_field_and_a_comment_only_one_agree() -> None:
    """Absence and comment-only absence reach the same verdict."""
    absent = intent_shape.validate_live_intent(_preamble())
    commented = intent_shape.validate_live_intent(
        _preamble(_with(**{"Parent intent": "<!-- none -->"}))
    )
    assert [v.field for v in absent] == [v.field for v in commented]


def test_ac0034_a_required_field_whose_value_is_comment_only_is_refused() -> None:
    """Comment-only is absent, and absence of a required field is AC-0001's."""
    text = _preamble(_with(Slug="<!-- fill this in -->"))
    assert "Slug" in _fields_at_fault(text)


# ── AC-0009: the retired names, both halves ───────────────────────────────────


@pytest.mark.parametrize("name", RETIRED)
def test_ac0009_refuses_each_retired_preamble_field_name(name: str) -> None:
    fields = dict(BASE)
    fields[name] = "some value"
    violations = intent_shape.validate_live_intent(_preamble(fields))
    assert name in {v.field for v in violations}, f"{name} was accepted"


@pytest.mark.parametrize("name", ["Milestone", "Depends on", "Invented field"])
def test_ac0009_accepts_a_field_named_outside_both_sets(name: str) -> None:
    """The open half: an unrecognized name is accepted, which is what keeps
    `Milestone:` and any future organic field passing."""
    fields = dict(BASE)
    fields[name] = "some value"
    assert _accepted(_preamble(fields))


def test_ac0009_governed_by_replaces_the_retired_authority_name() -> None:
    fields = dict(BASE)
    fields["Governed by"] = "adr:0033"
    assert _accepted(_preamble(fields))


# ── AC-0025: a repeated preamble field ────────────────────────────────────────


def test_ac0025_refuses_a_preamble_field_occurring_more_than_once() -> None:
    """Rendered by hand: `_preamble` takes a dict and cannot express a repeat."""
    text = "\n".join(
        [
            "# Intent: a rendered fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** `a-live-intent`",
            "- **Level:** feature",
            "- **Status:** Draft",
            "- **Governed by:** adr:0033",
            "- **Governed by:** adr:0098",
            "",
            "## Outcome",
            "",
            "An outcome sentence.",
        ]
    )
    violations = intent_shape.validate_live_intent(text)
    assert "Governed by" in {v.field for v in violations}


def test_ac0025_names_the_intent_and_the_field_on_a_repeat() -> None:
    """AC-0025 requires the field named; the corpus lint adds the intent."""
    text = "\n".join(
        [
            "# Intent: a rendered fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Owner:** someone-else",
            "- **Slug:** a-live-intent",
            "- **Level:** feature",
            "- **Status:** Draft",
            "",
            "## Outcome",
            "",
            "Text.",
        ]
    )
    repeats = [v for v in intent_shape.validate_live_intent(text) if v.field == "Owner"]
    assert repeats
    assert any("more than once" in v.reason for v in repeats)


# ── AC-0011: the preamble is a bounded region ─────────────────────────────────


def test_ac0011_a_body_level_status_line_neither_satisfies_nor_violates() -> None:
    """Two real intents carry this shape inside a de-risk record body."""
    body = "- **Status:** Run 2026-09-09; killed on the second probe"
    # Satisfies nothing: the preamble still lacks its own Status.
    assert "Status" in _fields_at_fault(_preamble(_without("Status"), body=body))
    # Violates nothing: the narrative value is not judged against AC-0002.
    assert _accepted(_preamble(body=body))


def test_ac0011_a_bolded_body_level_authority_line_is_not_the_retired_field() -> None:
    """About 40 intents carry this inside `## Source` as an owner attribution."""
    body = "\n".join(
        [
            "## Source",
            "",
            "- **Authority:** eugenelim, lifecycle owner",
        ]
    )
    assert _accepted(_preamble(body=body))
    assert "Authority" not in _fields_at_fault(_preamble(body=body))


def test_ac0011_an_unbolded_source_provenance_token_is_not_a_field() -> None:
    """The third `Authority` usage: unbolded in `## Source`, a provenance token."""
    body = "\n".join(["## Source", "", "Authority: repo-origin"])
    assert _accepted(_preamble(body=body))


def test_ac0011_the_preamble_ends_at_the_first_heading() -> None:
    """The region boundary is the whole defence, so assert it directly."""
    text = _preamble(body="- **Owner:** a-second-owner")
    names = [name for name, _ in intent_shape.read_preamble(text)]
    assert names.count("Owner") == 1
    # And the body-level repeat does not trip AC-0025.
    assert _accepted(text)


def test_ac0011_read_preamble_returns_nothing_for_a_body_only_field() -> None:
    text = "\n".join(["# Intent", "", "## Source", "", "- **Authority:** someone"])
    assert intent_shape.read_preamble(text) == []


# ══ T2: the progress fields and the direct-light decomposition ════════════════


def _with_decomposition(decomposed: str, items: list[str] | None = None,
                        *, section: bool = True) -> str:
    """Render an intent carrying ``Decomposed:`` and optionally the section.

    ``items`` are checkbox lines' text; an empty list renders the heading with
    no items, and ``section=False`` omits the heading entirely.
    """
    lines = ["# Intent: a rendered fixture", ""]
    for name, value in BASE.items():
        lines.append(f"- **{name}:** {value}")
    lines.append(f"- **Decomposed:** {decomposed}")
    lines += ["", "## Outcome", "", "An outcome sentence.", ""]
    if section:
        lines += ["## Decomposition", ""]
        for text in items or []:
            lines.append(f"- [ ] {text}")
        lines.append("")
    return "\n".join(lines)


# ── AC-0005: the two date-or-literal progress fields ──────────────────────────


@pytest.mark.parametrize("field", ["De-risked", "Shaping-reviewed"])
@pytest.mark.parametrize("value", ["2026-09-21", "no", "1999-01-01"])
def test_ac0005_accepts_an_iso_date_or_the_literal_no(field: str, value: str) -> None:
    assert _accepted(_preamble(_with(**{field: value})))


@pytest.mark.parametrize("field", ["De-risked", "Shaping-reviewed"])
@pytest.mark.parametrize("shape", SHAPES)
def test_ac0005_accepts_a_date_through_every_value_shape(field: str, shape: str) -> None:
    assert _accepted(_preamble(_with(**{field: "2026-09-21"}), shape=shape))


@pytest.mark.parametrize("field", ["De-risked", "Shaping-reviewed"])
@pytest.mark.parametrize(
    "value",
    [
        "yes",           # the affirmative literal is not in the contract
        "No",            # only the lowercase literal is the literal
        "2026-13-01",    # shaped like a date, is not a date
        "2026-09-31",    # September has 30 days
        "21-09-2026",    # a date in the wrong order
        "2026-09",       # a month, not a date
        "20260921",      # compact form is not `YYYY-MM-DD`
        "2026-09-21 and then some",
        "soon",
    ],
)
def test_ac0005_refuses_any_other_value(field: str, value: str) -> None:
    assert field in _fields_at_fault(_preamble(_with(**{field: value})))


# ── AC-0023: absence is distinguished from the literal `no` ───────────────────


@pytest.mark.parametrize("field", ["De-risked", "Shaping-reviewed", "Decomposed"])
def test_ac0023_reports_absent_and_no_as_different_states(field: str) -> None:
    """Absence and the literal `no` are the pair AC-0023 separates, which is
    why it takes its own cases rather than sharing AC-0005's."""
    absent = intent_shape.progress_state(_preamble())
    declared = intent_shape.progress_state(_preamble(_with(**{field: "no"})))
    assert absent[field] == intent_shape.PROGRESS_ABSENT
    assert declared[field] == intent_shape.PROGRESS_NO
    assert absent[field] != declared[field]


@pytest.mark.parametrize("field", ["De-risked", "Shaping-reviewed", "Decomposed"])
def test_ac0023_a_date_is_a_third_state(field: str) -> None:
    value = "2026-09-21 spec" if field == "Decomposed" else "2026-09-21"
    state = intent_shape.progress_state(_preamble(_with(**{field: value})))
    assert state[field] not in (intent_shape.PROGRESS_ABSENT, intent_shape.PROGRESS_NO)


def test_ac0023_reports_every_progress_field_for_every_intent() -> None:
    """One line per intent covers all three fields, so none may be omitted."""
    assert set(intent_shape.progress_state(_preamble())) == set(
        intent_shape.PROGRESS_FIELDS
    )


def test_ac0023_absence_alone_does_not_refuse() -> None:
    """Absence changes the report, not the verdict; the exit code is T4's."""
    assert _accepted(_preamble())
    for field in intent_shape.PROGRESS_FIELDS:
        assert field not in _fields_at_fault(_preamble())


def test_ac0023_a_comment_only_progress_field_reports_absent() -> None:
    text = _preamble(_with(**{"De-risked": "<!-- not yet probed -->"}))
    assert intent_shape.progress_state(text)["De-risked"] == intent_shape.PROGRESS_ABSENT
    assert _accepted(text)


# ── AC-0006: Decomposed is a date-plus-terminus shape ─────────────────────────


def test_ac0006_accepts_the_literal_no() -> None:
    assert _accepted(_preamble(_with(Decomposed="no")))


@pytest.mark.parametrize("terminus", ["children", "brief", "spec", "direct-light"])
def test_ac0006_accepts_a_date_with_each_terminus(terminus: str) -> None:
    items = ["Do the one bounded thing"] if terminus == "direct-light" else None
    assert _accepted(_with_decomposition(f"2026-09-21 {terminus}", items))


def test_ac0006_terminus_set_is_exactly_the_four_named_termini() -> None:
    """Pinned literally for the same reason AC-0002's membership is."""
    assert frozenset(intent_shape.DECOMPOSITION_TERMINI) == frozenset(
        {"children", "brief", "spec", "direct-light"}
    )


@pytest.mark.parametrize(
    "value",
    [
        "2026-09-21",                # a date with no terminus
        "2026-09-21 brief spec",     # two termini
        "2026-09-21 rfc",            # an unlisted terminus
        "2026-09-21 children extra",  # a terminus plus noise
        "children",                  # a terminus with no date
        "2026-13-01 spec",           # shaped like a date, is not one
        "yes",
    ],
)
def test_ac0006_refuses_any_other_value(value: str) -> None:
    assert "Decomposed" in _fields_at_fault(_preamble(_with(Decomposed=value)))


@pytest.mark.parametrize("shape", SHAPES)
def test_ac0006_accepts_a_terminus_through_every_value_shape(shape: str) -> None:
    text = _preamble(_with(Decomposed="2026-09-21 spec"), shape=shape)
    assert _accepted(text)


# ── AC-0007: a direct-light terminus requires checkbox items ──────────────────


def test_ac0007_refuses_direct_light_with_an_empty_decomposition_section() -> None:
    assert "Decomposed" in _fields_at_fault(
        _with_decomposition("2026-09-21 direct-light", [])
    )


def test_ac0007_refuses_direct_light_with_the_section_absent() -> None:
    assert "Decomposed" in _fields_at_fault(
        _with_decomposition("2026-09-21 direct-light", None, section=False)
    )


def test_ac0007_accepts_direct_light_carrying_one_item() -> None:
    assert _accepted(
        _with_decomposition("2026-09-21 direct-light", ["Rename the retired field"])
    )


# ── AC-0008: every direct-light checkbox item carries text ────────────────────


@pytest.mark.parametrize("text", ["", " ", "   ", "\t"])
def test_ac0008_refuses_a_checkbox_item_whose_text_is_empty(text: str) -> None:
    assert "Decomposed" in _fields_at_fault(
        _with_decomposition("2026-09-21 direct-light", ["A real item", text])
    )


def test_ac0008_accepts_items_that_all_carry_text() -> None:
    assert _accepted(
        _with_decomposition(
            "2026-09-21 direct-light", ["First outcome", "Second outcome"]
        )
    )


@pytest.mark.parametrize("terminus", ["children", "brief", "spec"])
def test_ac0008_the_other_three_termini_leave_the_section_unread(terminus: str) -> None:
    """An empty section is refused only under `direct-light`.

    Asserted against the shape AC-0007 refuses, so a rule that reads the
    section unconditionally fails here rather than passing quietly.
    """
    assert _accepted(_with_decomposition(f"2026-09-21 {terminus}", []))
    assert _accepted(_with_decomposition(f"2026-09-21 {terminus}", ["", "  "]))
    assert _accepted(
        _with_decomposition(f"2026-09-21 {terminus}", None, section=False)
    )


# ══ T3: a superseding slug resolves or the intent is refused ══════════════════
#
# AC-0021 is the one criterion here that reads other artifacts, so it lives in
# its own function rather than in `validate_live_intent`. That boundary is
# load-bearing: the shaping reviewer retrieves nothing, and the packet-decidable
# set is what AC-0012 and AC-0026 form a closed biconditional over. A reviewer
# that could reach this rule would refuse every intent carrying a pointer.


def _slug_line(value: str, shape: str) -> str:
    return f"- **Slug:** {_wrap(value, shape)}"


def _intent_with_slug(slug: str, *, shape: str = BARE) -> str:
    fields = dict(BASE)
    fields["Slug"] = slug
    return _preamble(fields, shape=shape)


def test_ac0021_accepts_a_superseded_by_slug_that_resolves() -> None:
    text = _preamble(_with(Status="Superseded by a-successor"))
    assert intent_shape.validate_supersession(text, {"a-successor"}) == []


def test_ac0021_refuses_a_superseded_by_slug_that_resolves_to_nothing() -> None:
    text = _preamble(_with(Status="Superseded by a-ghost"))
    violations = intent_shape.validate_supersession(text, {"a-successor"})
    assert violations
    assert any("a-ghost" in v.reason for v in violations), violations


def test_ac0021_names_the_unresolved_slug_in_its_reason() -> None:
    """AC-0021 requires both the intent and the slug named; the corpus lint
    supplies the intent, so the reason must carry the slug."""
    text = _preamble(_with(Status="Superseded by a-ghost"))
    (violation,) = intent_shape.validate_supersession(text, set())
    assert "a-ghost" in violation.reason
    assert violation.field == "Status"


def test_ac0021_an_empty_live_slug_set_resolves_nothing() -> None:
    text = _preamble(_with(Status="Superseded by a-successor"))
    assert intent_shape.validate_supersession(text, set()) != []


@pytest.mark.parametrize("status_shape", SHAPES)
def test_ac0021_reads_the_superseding_value_through_every_shape(
    status_shape: str,
) -> None:
    text = _preamble(_with(Status="Superseded by a-successor"), shape=status_shape)
    assert intent_shape.validate_supersession(text, {"a-successor"}) == []


@pytest.mark.parametrize("slug_shape", SHAPES)
def test_ac0021_comparand_is_the_normalized_slug_value(slug_shape: str) -> None:
    """The corpus's dominant `Slug:` shape is backticked *and* commented, which
    is the case an unnormalized comparison fails."""
    target = _intent_with_slug("a-successor", shape=slug_shape)
    live = intent_shape.live_slugs([target])
    assert live == {"a-successor"}, slug_shape
    superseded = _preamble(_with(Status="Superseded by a-successor"))
    assert intent_shape.validate_supersession(superseded, live) == []


def test_ac0021_live_slugs_collects_one_slug_per_intent() -> None:
    corpus = [_intent_with_slug("first"), _intent_with_slug("second", shape=COMPOSED)]
    assert intent_shape.live_slugs(corpus) == {"first", "second"}


def test_ac0021_live_slugs_ignores_a_body_level_slug_line() -> None:
    """The preamble bound applies to slug collection too."""
    text = _preamble(body="- **Slug:** a-body-level-slug")
    assert intent_shape.live_slugs([text]) == {"a-live-intent"}


def test_ac0021_a_non_superseded_status_resolves_nothing() -> None:
    for value in ("Draft", "Accepted", "Fulfilled", "Withdrawn", "Cancelled"):
        text = _preamble(_with(Status=value))
        assert intent_shape.validate_supersession(text, set()) == [], value


def test_ac0021_is_not_reachable_from_the_packet_decidable_contract() -> None:
    """`validate_live_intent` must not refuse an unresolved slug.

    This is the boundary AC-0012's biconditional rests on, so it is asserted
    rather than left to the call graph.
    """
    text = _preamble(_with(Status="Superseded by a-ghost"))
    assert _accepted(text)


# ══ An emptied value: which rules still see the line ══════════════════════════
#
# Raised by adversarial review. A value emptied by normalization makes the value
# absent, not the line. A rule about what a field is *named* still sees it; a
# rule about what a field *says* does not. Pinned so the split is a decision
# rather than an accident of evaluation order.


@pytest.mark.parametrize("name", RETIRED)
def test_a_retired_name_is_refused_even_with_an_emptied_value(name: str) -> None:
    fields = dict(BASE)
    fields[name] = "<!-- left over from the old shape -->"
    assert name in _fields_at_fault(_preamble(fields))


def test_a_repeat_is_refused_even_with_emptied_values() -> None:
    text = "\n".join(
        [
            "# Intent: a rendered fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** a-live-intent",
            "- **Level:** feature",
            "- **Status:** Draft",
            "- **Governed by:** <!-- tbd -->",
            "- **Governed by:** <!-- also tbd -->",
            "",
            "## Outcome",
            "",
            "Text.",
        ]
    )
    assert "Governed by" in {
        v.field for v in intent_shape.validate_live_intent(text)
    }


def test_an_unknown_name_with_an_emptied_value_is_still_accepted() -> None:
    """The open half of AC-0009 is unaffected by the value being emptied."""
    fields = dict(BASE)
    fields["Milestone"] = "<!-- not yet placed -->"
    assert _accepted(_preamble(fields))


# ══ T6 / AC-0016: neither enforcement point substitutes for the other ═════════
#
# Co-located with the fixture corpus on purpose. In separate modules one rule
# could drift and both suites would stay green, which is the failure AC-0016
# exists to catch.
#
# The corpus lint decides the preamble's shape. The cold shaping review decides
# six other things, none of which the lint can see: whether the statement is an
# outcome rather than a solution, whether non-goals are present, whether the
# riskiest assumption is named, whether the altitude agrees with the parent,
# whether the decomposition partitions the outcome, and whether the owner is the
# artifact's own. A conforming preamble is therefore not a passing review.

REVIEWER = (
    Path(__file__).resolve().parents[3] / ".apm" / "agents" / "shaping-reviewer.md"
)


def _reviewer_intent_mode() -> str:
    text = REVIEWER.read_text(encoding="utf-8")
    start = text.index("### intent mode")
    end = text.index("### delivery-brief mode", start)
    return text[start:end]


def test_ac0016_a_conforming_preamble_leaves_the_reviews_conditions_unjudged() -> None:
    """The lint accepts a fixture that visibly fails the review's conditions.

    Named for what it establishes rather than for the review's verdict. The
    shaping review is prose an agent reads, so no test here can run it or
    observe its refusal; what is checkable is that the lint accepts this
    fixture and that the conditions it fails are the review's, not the lint's.
    A test asserting the refusal itself would be asserting its own fixture.
    """
    text = _preamble(
        body="We will add a dropdown to the settings page.\n\n"
        "(no non-goals, and no riskiest assumption)"
    )
    assert _accepted(text), "the preamble must conform, or the test proves nothing"

    mode = _reviewer_intent_mode()
    assert "an outcome, not a solution" in mode
    assert "Non-goals are present" in mode
    assert "riskiest assumption is named" in mode


def test_ac0016_the_review_judges_conditions_the_lint_cannot_decide() -> None:
    """Named explicitly, so collapsing the review into the lint fails here."""
    mode = _reviewer_intent_mode()
    for condition in (
        "an outcome, not a solution",
        "Non-goals are present",
        "riskiest assumption is named",
        "Altitude is consistent with the parent",
        "decomposition partitions",
        "owner is the artifact's own",
    ):
        assert condition in mode, condition

    # None of those is a preamble field rule, so none is in the contract table.
    for name in intent_shape.REQUIRED_FIELDS:
        assert name in ("Owner", "Slug", "Level", "Status"), name


def test_ac0016_the_lint_decides_shape_and_claims_nothing_more() -> None:
    """An intent with an empty body is accepted: the lint reads the preamble,
    so a passing lint cannot stand in for a passing review."""
    bare = "\n".join(
        [
            "# Intent: a fixture with nothing in it",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** a-hollow-intent",
            "- **Level:** feature",
            "- **Status:** Draft",
            "",
            "## Outcome",
            "",
        ]
    )
    assert _accepted(bare)


def test_ac0016_the_reviewer_emits_its_own_token_for_shape() -> None:
    """The two points share the rules and keep separate reports: the review
    emits a token, the lint names a file and a field."""
    mode = _reviewer_intent_mode()
    assert "MALFORMED(shape)" in mode
    assert "MALFORMED(owner)" in mode
