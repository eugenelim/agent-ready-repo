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

# The tokens the spec names.  Spelled once here so the set comparison below
# does not repeat them.
_EXPECTED_STATUSES = frozenset(
    {"Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"}
)


def test_ac0010_vocabulary_is_exact_frozenset() -> None:
    """BRIEF_STATUSES equals the six-token vocabulary exactly (AC-0010)."""
    assert _m.BRIEF_STATUSES == _EXPECTED_STATUSES


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


def test_ac0012_draft_back_linked_only_child_refused() -> None:
    """A back-linked-only child at Implementing makes Draft invalid (AC-0012).

    A spec that back-links the brief but is absent from the Spec-map still
    contributes its state to the child set.  This fixture pins that the predicate
    treats back-linked-only children the same way as mapped ones.
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
# BRIEF_TRANSITIONS is refused (AC-0017).  A listed pair and any self-pair are
# not refused (AC-0018).


def test_ac0017_illegal_transitions_refused() -> None:
    """Every (from, to) pair of two different states absent from the table is refused.

    Iterates all 30 two-different-state pairs; the 22 that are absent from
    BRIEF_TRANSITIONS must return False.  AC-0017.
    """
    for from_s in _m.BRIEF_STATUSES:
        for to_s in _m.BRIEF_STATUSES:
            if from_s == to_s:
                continue
            if (from_s, to_s) not in _m.BRIEF_TRANSITIONS:
                assert not _m.is_transition_valid(from_s, to_s), (
                    f"Expected ({from_s!r}, {to_s!r}) to be refused as illegal"
                )


def test_ac0018_legal_transitions_and_self_pairs_not_refused() -> None:
    """All 8 table entries and 6 self-pairs are not refused.

    Iterates the 8 pairs in BRIEF_TRANSITIONS and the 6 self-pairs (one per
    state); all 14 must return True.  AC-0018.
    """
    for state in _m.BRIEF_STATUSES:
        assert _m.is_transition_valid(state, state), (
            f"Self-pair ({state!r}, {state!r}) should not be refused"
        )
    for from_s, to_s in _m.BRIEF_TRANSITIONS:
        assert _m.is_transition_valid(from_s, to_s), (
            f"Legal transition ({from_s!r}, {to_s!r}) should not be refused"
        )
