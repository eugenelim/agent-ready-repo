#!/usr/bin/env python3
"""Tests for brief_shape.py at the module boundary.

Covers AC-0001 through AC-0006 (preamble bounding rules) and AC-0008,
AC-0009 (Cut-closed: value grammar).  Each criterion has one fixture pair
— a refusing case and an accepting case — exercised through the module's
public API.

Spec: docs/specs/brief-lifecycle-contract/spec.md
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Resolve the skill directory the same way test_lint_brief_coverage.py does.
_SKILL_DIR = (
    Path(__file__).resolve().parents[3] / ".apm" / "skills" / "author-delivery-brief"
)
_MODULE_PATH = _SKILL_DIR / "scripts" / "brief_shape.py"
if not _MODULE_PATH.is_file():
    raise SystemExit(
        f"subject not found at {_MODULE_PATH} — check the parents[] depth"
    )

# Load the module under a pack-and-skill-qualified name.  A bare import is
# banned: skills are independent and several may ship a same-named script.
# Production precedent: work-intake/scripts/intent_corpus_lint.py:58-75.
_MODULE_NAME = "core_author_delivery_brief_brief_shape"


def _load_module() -> object:
    """Load brief_shape.py under the pack-and-skill-qualified name."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module at {_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_m = _load_module()


# ── AC-0001: a field below the first uncommented ## heading is not read ────────


def test_ac0001_field_below_heading_not_read() -> None:
    """A Status field that appears below a live ## heading is absent."""
    text = (
        "# Brief: My Title\n"
        "\n"
        "## Section\n"
        "\n"
        "- **Status:** Shipped\n"
    )
    assert _m.get_status(text) is None


def test_ac0001_field_above_heading_is_read() -> None:
    """A Status field that appears before any ## heading is returned."""
    text = (
        "- **Status:** Shipped\n"
        "\n"
        "## Section\n"
        "\n"
        "- **Status:** NotRead\n"
    )
    assert _m.get_status(text) == "Shipped"


# ── AC-0002: a field inside an HTML comment is not read ───────────────────────


def test_ac0002_field_inside_multiline_comment_not_read() -> None:
    """A Status field wrapped in a multi-line HTML comment is not read."""
    text = (
        "<!--\n"
        "- **Status:** Shipped\n"
        "-->\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) is None


def test_ac0002_field_outside_comment_is_read() -> None:
    """A Status field outside any comment is read normally."""
    text = (
        "- **Status:** Shipped\n"
        "<!--\n"
        "- **Status:** Hidden\n"
        "-->\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) == "Shipped"


# ── AC-0003: a ## heading inside a comment does not end the preamble ──────────


def test_ac0003_heading_inside_comment_does_not_end_preamble() -> None:
    """A field after a commented-out ## heading is still in the preamble."""
    text = (
        "- **Status:** Shipped\n"
        "<!--\n"
        "## Fake heading inside comment\n"
        "-->\n"
        "- **Cut-closed:** 2026-01-01 evidence text\n"
        "\n"
        "## Real heading\n"
    )
    cut = _m.get_cut_closed(text)
    assert cut is not None
    assert "2026-01-01" in cut


def test_ac0003_live_heading_ends_preamble() -> None:
    """A field below a live ## heading is not in the preamble."""
    text = (
        "- **Status:** Shipped\n"
        "\n"
        "## Real heading\n"
        "\n"
        "- **Cut-closed:** 2026-01-01 evidence text\n"
    )
    assert _m.get_cut_closed(text) is None


# ── AC-0004: a field-shaped ATX heading is not read as a preamble field ───────


def test_ac0004_field_shaped_atx_heading_not_read() -> None:
    """A level-1 ATX heading that looks field-shaped is not read as a field."""
    text = (
        "# **Status:** Shipped\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) is None


def test_ac0004_regular_field_not_in_heading_is_read() -> None:
    """A properly formed field line (not a heading) is read."""
    text = (
        "- **Status:** Shipped\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) == "Shipped"


# ── AC-0005: a field-shaped line inside a blockquote is not read ──────────────


def test_ac0005_field_in_blockquote_not_read() -> None:
    """A field line prefixed with > (blockquote) is not read."""
    text = (
        "> - **Status:** Shipped\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) is None


def test_ac0005_field_outside_blockquote_is_read() -> None:
    """A field line without a blockquote prefix is read."""
    text = (
        "- **Status:** Shipped\n"
        "> - **Status:** InBlockquote\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_status(text) == "Shipped"


# ── AC-0006: a preamble with an unclosed HTML comment returns no fields ────────


def test_ac0006_unclosed_comment_returns_empty_preamble() -> None:
    """When the preamble opens a comment that never closes, read_preamble
    returns an empty list — even for fields that appear before the comment."""
    text = (
        "- **Status:** Shipped\n"
        "<!--\n"
        "- **Cut-closed:** 2026-01-01 evidence\n"
    )
    result = _m.read_preamble(text)
    assert result == []


def test_ac0006_closed_comment_allows_prior_fields() -> None:
    """When a comment closes normally, fields before it are returned."""
    text = (
        "- **Status:** Shipped\n"
        "<!-- ignored -->\n"
        "\n"
        "## Section\n"
    )
    result = _m.read_preamble(text)
    assert any(name == "Status" for name, _ in result)


# ── AC-0008: a malformed Cut-closed value is refused ──────────────────────────


def test_ac0008_malformed_value_refused() -> None:
    """A value that is not an ISO 8601 date followed by evidence is refused."""
    err = _m.validate_cut_closed("not-a-date some evidence")
    assert err is not None
    assert "not-a-date" in err


def test_ac0008_date_only_refused() -> None:
    """A bare date with no evidence text is refused."""
    err = _m.validate_cut_closed("2026-01-01")
    assert err is not None
    assert "2026-01-01" in err


def test_ac0008_well_formed_value_accepted() -> None:
    """An ISO 8601 date followed by non-empty evidence text is accepted."""
    err = _m.validate_cut_closed("2026-01-01 slice-2 spec map all Shipped")
    assert err is None


# ── AC-0009: an empty or comment-only value is absent, not malformed ──────────


def test_ac0009_empty_value_is_absent() -> None:
    """A Cut-closed: line with an empty value counts as absent (None)."""
    text = (
        "- **Status:** Draft\n"
        "- **Cut-closed:**\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_cut_closed(text) is None


def test_ac0009_comment_only_value_is_absent() -> None:
    """A Cut-closed: line whose value is only an HTML comment is absent."""
    text = (
        "- **Status:** Draft\n"
        "- **Cut-closed:** <!-- not set yet -->\n"
        "\n"
        "## Section\n"
    )
    assert _m.get_cut_closed(text) is None


def test_ac0009_well_formed_value_is_present() -> None:
    """A well-formed Cut-closed: value is returned as present (not None)."""
    text = (
        "- **Status:** Executing\n"
        "- **Cut-closed:** 2026-01-01 evidence text\n"
        "\n"
        "## Section\n"
    )
    result = _m.get_cut_closed(text)
    assert result is not None
    assert "2026-01-01" in result


# ── AC-0010: the vocabulary is exactly the six-token frozenset ────────────────

# The six tokens from the spec's brief-state table (§ The brief state table in
# docs/specs/brief-lifecycle-contract/spec.md).  This is the spec oracle; it
# must NOT be derived from BRIEF_STATUSES or any other implementation constant.
# Both the vocabulary test (AC-0010) and the transition sweep (AC-0017/AC-0018)
# use this constant so they range over the same set.
_SPEC_STATUS_TOKENS: frozenset[str] = frozenset(
    {"Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"}
)


def test_ac0010_vocabulary_is_exact_frozenset() -> None:
    """BRIEF_STATUSES equals the six-token vocabulary exactly (AC-0010)."""
    assert _m.BRIEF_STATUSES == _SPEC_STATUS_TOKENS


# ── AC-0011: absent or unknown status is not lifecycle-valid ──────────────────


def test_ac0011_none_status_is_not_lifecycle_valid() -> None:
    """is_lifecycle_valid returns False when status is None (AC-0011)."""
    assert not _m.is_lifecycle_valid(None, set())


def test_ac0011_unknown_status_is_not_lifecycle_valid() -> None:
    """is_lifecycle_valid returns False for an out-of-vocabulary status (AC-0011)."""
    assert not _m.is_lifecycle_valid("UnknownStatus", set())


# ── AC-0012: child-execution-evidence matrix over all six states ──────────────


def test_ac0012_draft_no_children_valid() -> None:
    """Draft with no children is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Draft", set())


def test_ac0012_draft_non_execution_child_valid() -> None:
    """Draft with a child at Planning is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Draft", {"Planning"})


def test_ac0012_draft_implementing_child_refused() -> None:
    """Draft with a child at Implementing is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Draft", {"Implementing"})


def test_ac0012_draft_shipped_child_refused() -> None:
    """Draft with a child at Shipped is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Draft", {"Shipped"})


def test_ac0012_draft_child_state_from_either_arm_refused() -> None:
    """A Draft brief with an Implementing child state is refused (AC-0012).

    The predicate takes a set of child states and cannot see which arm a state
    arrived by, so this pins the verdict only -- not the mapped-versus-
    back-linked join, which lives in the lint and is covered through the CLI
    in test_lint_brief_coverage.py.
    """
    back_linked_only: set[str] = {"Implementing"}
    assert not _m.is_lifecycle_valid("Draft", back_linked_only)


def test_ac0012_ready_no_children_valid() -> None:
    """Ready with no children is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Ready", set())


def test_ac0012_ready_implementing_child_refused() -> None:
    """Ready with a child at Implementing is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Ready", {"Implementing"})


def test_ac0012_ready_shipped_child_refused() -> None:
    """Ready with a child at Shipped is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Ready", {"Shipped"})


def test_ac0012_executing_implementing_child_valid() -> None:
    """Executing with a child at Implementing is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Executing", {"Implementing"})


def test_ac0012_executing_shipped_child_valid() -> None:
    """Executing with a child at Shipped is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Executing", {"Shipped"})


def test_ac0012_executing_no_children_refused() -> None:
    """Executing with no children is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Executing", set())


def test_ac0012_executing_only_non_execution_child_refused() -> None:
    """Executing with only a Planning child is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Executing", {"Planning"})


def test_ac0012_shipped_all_shipped_children_valid() -> None:
    """Shipped with a non-empty all-Shipped child set is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Shipped", {"Shipped"})


def test_ac0012_shipped_empty_child_set_refused() -> None:
    """Shipped with an empty child set is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Shipped", set())


def test_ac0012_shipped_mixed_children_refused() -> None:
    """Shipped with a Shipped+Implementing child set is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Shipped", {"Shipped", "Implementing"})


def test_ac0012_withdrawn_no_children_valid() -> None:
    """Withdrawn with no children is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Withdrawn", set())


def test_ac0012_withdrawn_implementing_child_refused() -> None:
    """Withdrawn with a child at Implementing is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Withdrawn", {"Implementing"})


def test_ac0012_cancelled_implementing_child_valid() -> None:
    """Cancelled with a child at Implementing is lifecycle-valid (AC-0012)."""
    assert _m.is_lifecycle_valid("Cancelled", {"Implementing"})


def test_ac0012_cancelled_no_children_refused() -> None:
    """Cancelled with no children is refused (AC-0012)."""
    assert not _m.is_lifecycle_valid("Cancelled", set())


# ── AC-0013 through AC-0016: the twelve-cell declaration matrix ───────────────


def test_ac0013_shipped_without_cut_closed_refused() -> None:
    """Shipped + absent Cut-closed: is refused (AC-0013)."""
    err = _m.validate_declaration("Shipped", False)
    assert err is not None


def test_ac0014_draft_without_cut_closed_not_refused() -> None:
    """Draft + absent Cut-closed: is not refused (AC-0014)."""
    assert _m.validate_declaration("Draft", False) is None


def test_ac0014_ready_without_cut_closed_not_refused() -> None:
    """Ready + absent Cut-closed: is not refused (AC-0014)."""
    assert _m.validate_declaration("Ready", False) is None


def test_ac0014_executing_without_cut_closed_not_refused() -> None:
    """Executing + absent Cut-closed: is not refused (AC-0014)."""
    assert _m.validate_declaration("Executing", False) is None


def test_ac0015_withdrawn_without_cut_closed_not_refused() -> None:
    """Withdrawn + absent Cut-closed: is not refused (AC-0015)."""
    assert _m.validate_declaration("Withdrawn", False) is None


def test_ac0015_cancelled_without_cut_closed_not_refused() -> None:
    """Cancelled + absent Cut-closed: is not refused (AC-0015)."""
    assert _m.validate_declaration("Cancelled", False) is None


def test_ac0016_draft_with_cut_closed_refused() -> None:
    """Draft + present Cut-closed: is refused (AC-0016)."""
    err = _m.validate_declaration("Draft", True)
    assert err is not None


def test_ac0016_ready_with_cut_closed_not_refused() -> None:
    """Ready + present Cut-closed: is not refused (AC-0016)."""
    assert _m.validate_declaration("Ready", True) is None


def test_ac0016_executing_with_cut_closed_not_refused() -> None:
    """Executing + present Cut-closed: is not refused (AC-0016)."""
    assert _m.validate_declaration("Executing", True) is None


def test_ac0016_shipped_with_cut_closed_not_refused() -> None:
    """Shipped + present Cut-closed: is not refused (AC-0016)."""
    assert _m.validate_declaration("Shipped", True) is None


def test_ac0016_withdrawn_with_cut_closed_not_refused() -> None:
    """Withdrawn + present Cut-closed: is not refused (AC-0016)."""
    assert _m.validate_declaration("Withdrawn", True) is None


def test_ac0016_cancelled_with_cut_closed_not_refused() -> None:
    """Cancelled + present Cut-closed: is not refused (AC-0016)."""
    assert _m.validate_declaration("Cancelled", True) is None


# ── AC-0017 and AC-0018: all 36 ordered pairs have a verdict ─────────────────
#
# 6 states × 6 states = 36 pairs.  A pair of two different states absent from
# the spec's legal-moves table is refused (AC-0017).  A listed pair and any
# self-pair are not refused (AC-0018).
#
# The oracle is the spec's table (§ The brief state table), spelled here as a
# literal constant.  Deriving the oracle from the implementation's
# BRIEF_TRANSITIONS would make the tests trivially true regardless of what the
# table contains — any edit to the table (adding or removing an edge) would
# silently pass.

_SPEC_LEGAL_PAIRS: frozenset[tuple[str, str]] = frozenset({
    ("Draft", "Ready"),
    ("Draft", "Withdrawn"),
    ("Ready", "Draft"),
    ("Ready", "Executing"),
    ("Ready", "Withdrawn"),
    ("Executing", "Ready"),
    ("Executing", "Shipped"),
    ("Executing", "Cancelled"),
})

# _SPEC_STATUS_TOKENS (defined near AC-0010 above) is also used here for the
# transition sweep; it is the same spec oracle, not a second copy.


def test_ac0017_illegal_transitions_refused() -> None:
    """Every (from, to) pair of two different states absent from the spec table is refused.

    Iterates all 30 two-different-state pairs; the 22 that are absent from
    _SPEC_LEGAL_PAIRS (the literal spec oracle) must each return False.  AC-0017.
    Any edit to BRIEF_TRANSITIONS that removes a legal edge or adds an illegal
    one makes at least one assertion fail, because the oracle does not update
    with the implementation.
    """
    for from_s in _SPEC_STATUS_TOKENS:
        for to_s in _SPEC_STATUS_TOKENS:
            if from_s == to_s:
                continue
            if (from_s, to_s) not in _SPEC_LEGAL_PAIRS:
                assert not _m.is_transition_valid(from_s, to_s), (
                    f"Expected ({from_s!r}, {to_s!r}) to be refused as illegal"
                )


def test_ac0018_legal_transitions_and_self_pairs_not_refused() -> None:
    """All 8 spec-table entries and 6 self-pairs are not refused.

    Iterates the 8 pairs in _SPEC_LEGAL_PAIRS (the literal spec oracle) and
    the 6 self-pairs; all 14 must return True.  AC-0018.
    """
    for state in _SPEC_STATUS_TOKENS:
        assert _m.is_transition_valid(state, state), (
            f"Self-pair ({state!r}, {state!r}) should not be refused"
        )
    for from_s, to_s in _SPEC_LEGAL_PAIRS:
        assert _m.is_transition_valid(from_s, to_s), (
            f"Legal transition ({from_s!r}, {to_s!r}) should not be refused"
        )


# ── AC-0023: a brief copied from the seed template is not refused ─────────────

_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "seeds"
    / "docs"
    / "product"
    / "briefs"
    / "_template.md"
)


def test_ac0023_template_cut_closed_is_absent_to_parser() -> None:
    """The seed template's Cut-closed: row parses as absent (None).

    AC-0009 lets a comment-only value count as absent.  This drives the real
    template bytes so a malformed row would be caught before it seeds a bad
    preamble into every brief copied from it.  AC-0023.
    """
    template_text = _TEMPLATE_PATH.read_text(encoding="utf-8")
    assert _m.get_cut_closed(template_text) is None


def test_ac0023_template_as_draft_brief_refused_by_no_spec_rule() -> None:
    """A Draft brief copied verbatim from the seed template is refused by no rule.

    Exercises the declaration matrix (AC-0013 through AC-0016) and the
    lifecycle predicate (AC-0012) against the template's actual preamble.
    A new brief has no mapped specs yet, so child_states is empty.  AC-0023.
    """
    template_text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    status = _m.get_status(template_text)
    cut_closed = _m.get_cut_closed(template_text)

    assert status == "Draft", (
        f"template Status: expected 'Draft', got {status!r}"
    )
    assert cut_closed is None, (
        f"template Cut-closed: expected absent (None), got {cut_closed!r}"
    )
    assert _m.validate_declaration(status, cut_closed is not None) is None, (
        "declaration matrix refused the template preamble"
    )
    assert _m.is_lifecycle_valid(status, set()), (
        "lifecycle predicate refused the template preamble with no children"
    )


# ── T6: durable-output checks ─────────────────────────────────────────────────


import re as _re  # noqa: E402


def test_t6_refusal_registry_equals_actual_refusals() -> None:
    """Module docstring refusal registry equals the set of refusals the module raises.

    T6: set comparison.  Extracts registry class names from the
    ``**Refusal registry**`` section of the module docstring and checks them
    against the canonical set of refusal classes the module's public validators
    can return.

    Two defects the fix addresses:

    1. ``validate_cut_closed`` was swept with three inputs that all fail before
       the ISO check; a fourth refusal added *after* the ISO check would not
       fire on any of them and the test would pass silently.  The sweep now
       includes a valid input (``2026-01-01 evidence``) that passes the ISO
       check, so any new refusal added after it fires and surfaces as
       ``UNREGISTERED_cut_closed``.  Each returned message is mapped to a
       registered class name by content pattern; an unrecognised message is
       ``UNREGISTERED_cut_closed``, not silently folded into a known class.

    2. The registry side was filtered to names starting with ``cut_closed_``,
       so a class outside that namespace added to the docstring would be dropped
       before the comparison.  The extraction is now scoped to the
       ``**Refusal registry**`` section of the docstring so that other
       ``...`` spans (mirror documentation, etc.) do not participate, and the
       namespace filter is removed.
    """
    doc = _m.__doc__ or ""

    # Scope extraction to the **Refusal registry** section so that ``...``
    # spans that document mirrors (e.g. ``extract_token``) do not participate
    # as registry entries.
    reg_start = doc.find("**Refusal registry**")
    registry_section = doc[reg_start:] if reg_start != -1 else ""
    registry = {
        m.group(1)
        for m in _re.finditer(r"^- ``([^`]+)``", registry_section, _re.MULTILINE)
    }
    # No namespace filter — all entries in the registry section participate so
    # a class outside cut_closed_ is not silently dropped from the comparison.

    # Derive the actual side from behaviour rather than restating it: sweep
    # every input shape the module's public validators accept and collect the
    # distinct conditions under which each returns a refusal.  A hand-written
    # expected-set would stay green when a fourth refusal is added to the code
    # with neither the docstring nor this test updated, which is exactly the
    # drift this test exists to catch.
    observed: set[str] = set()

    # validate_cut_closed: map each returned message to a class by content
    # pattern.  Known patterns → registered class name.  Unrecognised message →
    # UNREGISTERED_cut_closed, which surfaces immediately as a set mismatch.
    # The sweep includes "2026-01-01 evidence" (a valid input that currently
    # returns None) so that any refusal added after the ISO check fires on it.
    _CUT_CLOSED_CLASS_SIGNS: list[tuple[str, str]] = [
        ("is not an ISO 8601 date followed by evidence text", "cut_closed_malformed"),
        ("is not an ISO 8601 date", "cut_closed_malformed"),
    ]
    for bad in (
        "not-a-date evidence",
        "2026-08-25",
        "2026-13-99 bad month",
        "2026-01-01 evidence",  # valid under current rules; detects new post-ISO refusals
    ):
        msg = _m.validate_cut_closed(bad)
        if msg is None:
            continue
        cls = "UNREGISTERED_cut_closed"
        for sign, name in _CUT_CLOSED_CLASS_SIGNS:
            if sign in msg:
                cls = name
                break
        observed.add(cls)

    # validate_declaration: sweep all six states against present and absent.
    for status in ("Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"):
        for present in (False, True):
            if _m.validate_declaration(status, present) is None:
                continue
            if status == "Shipped" and not present:
                observed.add("cut_closed_required_on_shipped")
            elif status == "Draft" and present:
                observed.add("cut_closed_refused_on_draft")
            else:
                observed.add(f"UNREGISTERED_{status.lower()}_{'present' if present else 'absent'}")

    assert registry == observed, (
        "Refusal registry does not match the refusals the module actually "
        "raises.\n"
        f"Docstring registry: {sorted(registry)!r}\n"
        f"Observed by driving the validators: {sorted(observed)!r}\n"
        "An UNREGISTERED_ entry means the code refuses a case the docstring "
        "does not name."
    )


def test_t6_skill_md_cites_brief_shape_not_child_rule() -> None:
    """author-delivery-brief/SKILL.md § Brief lifecycle cites brief_shape.py.

    T6: checks (a) the section names brief_shape.py, and (b) does not state
    the child-execution-evidence rule in prose (the rule is delegated to the
    module).
    """
    skill_md = (_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    start = skill_md.find("## Brief lifecycle")
    assert start != -1, "§ Brief lifecycle section not found in SKILL.md"
    next_section = skill_md.find("\n## ", start + 1)
    section = (
        skill_md[start:next_section] if next_section != -1 else skill_md[start:]
    )

    assert "brief_shape.py" in section, (
        "§ Brief lifecycle does not name brief_shape.py"
    )
    # Spelling-level guard against the one phrase that was removed, not a
    # check that the rule is absent: any rewording that still restates the
    # child-execution-evidence rule would pass this. The closeout read the
    # Durable Outputs row assigns is what covers the general case.
    assert "Implementing` or `Shipped` child" not in section, (
        "§ Brief lifecycle still states the child-execution-evidence rule in prose"
    )


def test_comment_closer_then_heading_does_not_end_the_preamble() -> None:
    """A line that closes a comment and then carries a heading is not a heading.

    `-->  ## Outcome` has live text starting with a space, so the preamble
    bound does not fall there and a field below it is still read.  The
    Spec-map scanner answers the same shape the same way; the two readers
    must not diverge, because stripping first ends the bound early and
    silently drops a live field, which is the miss the bounded reader exists
    to prevent.
    """
    text = "# B\n\n- **Status:** Draft\n<!--\n-->  ## Outcome\n- **Slug:** `x`\n"
    fields = dict(_m.read_preamble(text))
    assert fields.get("Slug") == "`x`", (
        "a live field below a comment-closer-then-heading line was dropped"
    )
    # An ordinary heading still terminates.
    ordinary = "# B\n\n- **Status:** Draft\n\n## Outcome\n- **Slug:** `x`\n"
    assert "Slug" not in dict(_m.read_preamble(ordinary))


def test_indented_heading_bounds_preamble() -> None:
    """An indented ## heading (up to three spaces) ends the preamble.

    CommonMark allows up to three leading spaces on a heading.  The preamble
    reader must not silently admit a field that appears below an indented
    heading on the grounds that the heading is not flush-left.

    Mutation: remove the ``.lstrip()`` call in the heading check so that
    ``  ## Section`` is not recognised as a heading.  The Cut-closed field
    below it would then be read, and this test reds.
    """
    text = (
        "- **Status:** Draft\n"
        "\n"
        "  ## Section\n"  # two leading spaces — still a heading in CommonMark
        "\n"
        "- **Cut-closed:** 2026-01-01 evidence text\n"
    )
    assert _m.get_cut_closed(text) is None, (
        "field below indented ## heading must not be read"
    )


def test_bounding_heading_opening_comment_keeps_prior_fields() -> None:
    """A heading that itself opens a comment does not erase fields already read.

    The preamble reader returns early on finding the heading line.  Comment
    state opened on that same line belongs to the body, not to the preamble
    already collected; the early return must preserve the fields already in
    ``pairs``.

    Mutation: move the unclosed-comment check before the early return so that
    the open comment on the heading line invalidates the preamble.  The
    Status field would then be dropped and this test reds.
    """
    text = (
        "- **Status:** Draft\n"
        "## Section <!--\n"  # heading that opens (but never closes) a comment
        "- **Cut-closed:** 2026-01-01 evidence\n"  # inside comment, body
        "-->\n"
    )
    assert _m.get_status(text) == "Draft", (
        "fields read before the bounding heading must be returned even when "
        "the heading line itself opens a comment"
    )
