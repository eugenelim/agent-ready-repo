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
