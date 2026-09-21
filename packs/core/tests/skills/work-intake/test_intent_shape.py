"""Construction tests for the intent metadata shape contract.

Covers T1 of `docs/specs/intent-metadata-shape-contract/plan.md`: the contract
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
