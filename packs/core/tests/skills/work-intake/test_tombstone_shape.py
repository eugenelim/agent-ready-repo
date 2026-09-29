"""Construction tests for the tombstone serialiser and parser.

Covers the tombstone shape contract: every invalid value is refused with
a fixed token, and a round-trip (serialize then parse) preserves the
supplied values exactly.

Three-field rule: every tombstone carries exactly a slug, a retirement
date, and exactly one of two terminal fields — a successor path or a
retirement note.

Date rule: the retirement date is one ISO 8601 calendar date, written
exactly as supplied. No clock is consulted.

Path rule: the successor path is a repository-relative path under
``docs/product/intents/``; an absolute path, or one resolving outside
that directory, is refused.

Retired rule: the retirement note is a single non-empty line.

Partition rule (both arms): a file whose preamble carries ``Tombstone:``
is a tombstone; a file without it is not. Both arms are tested.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK_ROOT / ".apm" / "skills" / "work-intake" / "scripts"

MODULE_NAME = "core_work_intake_intent_tombstone"


def _load_module() -> Any:
    """Load the tombstone module under a pack-and-skill-qualified name."""
    path = _SCRIPTS / "intent_tombstone.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    # Register before exec so any dataclass defined in the module resolves
    # its own __module__ attribute correctly.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


tombstone = _load_module()

# ── Constants ─────────────────────────────────────────────────────────────────

_SLUG = "rename-test"
_DATE_A = "2026-09-21"  # "before midnight"
_DATE_B = "2026-09-22"  # "after midnight"
_INTENTS_PREFIX = "docs/product/intents"
_REISSUED_PATH = f"{_INTENTS_PREFIX}/FEAT-0002-renamed.md"
_RETIRED_NOTE = "no longer needed after scope change"


# ── Round-trip ────────────────────────────────────────────────────────────────


def test_round_trip_reissued_as() -> None:
    """Write and re-read a tombstone; slug, date, and successor path survive unchanged."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as=_REISSUED_PATH
    )
    assert isinstance(result, bytes), f"expected bytes, got {result!r}"
    text = result.decode("utf-8")
    parsed = tombstone.parse_tombstone(text)
    assert isinstance(parsed, tombstone.Tombstone), (
        f"parse_tombstone returned refusal {parsed!r} for valid tombstone"
    )
    assert parsed.slug == _SLUG
    assert parsed.date == _DATE_A
    assert parsed.reissued_as == _REISSUED_PATH
    assert parsed.retired is None


def test_round_trip_retired() -> None:
    """Write and re-read a retired (no-successor) tombstone; all values survive."""
    result = tombstone.serialize_tombstone(_SLUG, _DATE_A, retired=_RETIRED_NOTE)
    assert isinstance(result, bytes), f"expected bytes, got {result!r}"
    text = result.decode("utf-8")
    parsed = tombstone.parse_tombstone(text)
    assert isinstance(parsed, tombstone.Tombstone), (
        f"parse_tombstone returned refusal {parsed!r}"
    )
    assert parsed.slug == _SLUG
    assert parsed.date == _DATE_A
    assert parsed.reissued_as is None
    assert parsed.retired == _RETIRED_NOTE


# ── Date either side of midnight ─────────────────────────────────────────────


def test_date_before_midnight_written_exactly() -> None:
    """A date supplied as the 'before midnight' value is written exactly as given.

    If the serialiser consulted a clock, a test run near midnight could
    write a different date than the one supplied. Using a fixture date far
    from today catches that silent substitution.
    """
    result = tombstone.serialize_tombstone(_SLUG, _DATE_A, retired=_RETIRED_NOTE)
    assert isinstance(result, bytes)
    parsed = tombstone.parse_tombstone(result.decode("utf-8"))
    assert isinstance(parsed, tombstone.Tombstone)
    assert parsed.date == _DATE_A


def test_date_after_midnight_written_exactly() -> None:
    """A date supplied as the 'after midnight' value is written exactly as given."""
    result = tombstone.serialize_tombstone(_SLUG, _DATE_B, retired=_RETIRED_NOTE)
    assert isinstance(result, bytes)
    parsed = tombstone.parse_tombstone(result.decode("utf-8"))
    assert isinstance(parsed, tombstone.Tombstone)
    assert parsed.date == _DATE_B


# ── Serialiser refusals ───────────────────────────────────────────────────────


def test_non_iso_date_refuses() -> None:
    """A value that is not an ISO 8601 calendar date is refused."""
    result = tombstone.serialize_tombstone(
        _SLUG, "not-a-date", reissued_as=_REISSUED_PATH
    )
    assert result == "invalid-date", f"expected 'invalid-date', got {result!r}"


def test_non_calendar_date_refuses() -> None:
    """A value with the wrong day refuses even if the year and month are valid."""
    result = tombstone.serialize_tombstone(
        _SLUG, "2026-13-01", reissued_as=_REISSUED_PATH
    )
    assert result == "invalid-date", f"expected 'invalid-date', got {result!r}"


def test_absolute_reissued_as_refuses() -> None:
    """An absolute successor path is refused."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="/etc/passwd"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_outside_intents_reissued_as_refuses() -> None:
    """A successor path resolving outside docs/product/intents/ is refused."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="../../docs/specs/other.md"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_sibling_directory_reissued_as_refuses() -> None:
    """A repository-relative path in another directory is refused.

    The value is repository-relative, so this names a real path outside the
    intents directory. Validating it as a name *inside* that directory accepts
    it and writes a tombstone pointing out of the corpus.
    """
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="docs/other/a.md"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_reissued_as_traversing_out_after_prefix_refuses() -> None:
    """A successor path that climbs out after the prefix is refused.

    ``docs/product/intents/../../x.md`` normalises to ``docs/x.md``. Joining it
    onto the prefix instead re-enters the directory it had escaped.
    """
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as=f"{_INTENTS_PREFIX}/../../x.md"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_bare_filename_reissued_as_refuses() -> None:
    """A bare filename is not a repository-relative path under intents."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="FEAT-0002-renamed.md"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_backslash_reissued_as_refuses() -> None:
    """A backslash separator is refused before normalisation.

    POSIX normalisation treats it as an ordinary character, so a path Windows
    would read as escaping the directory would otherwise pass.
    """
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as=f"{_INTENTS_PREFIX}\\..\\..\\x.md"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_empty_retired_refuses() -> None:
    """An empty retirement note is refused."""
    result = tombstone.serialize_tombstone(_SLUG, _DATE_A, retired="")
    assert result == "empty-retired", f"expected 'empty-retired', got {result!r}"


def test_whitespace_only_retired_refuses() -> None:
    """A whitespace-only retirement note is refused."""
    result = tombstone.serialize_tombstone(_SLUG, _DATE_A, retired="   ")
    assert result == "empty-retired", f"expected 'empty-retired', got {result!r}"


def test_both_pointer_fields_refuses() -> None:
    """Supplying both pointer fields is refused."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as=_REISSUED_PATH, retired=_RETIRED_NOTE
    )
    assert result == "pointer-conflict", f"expected 'pointer-conflict', got {result!r}"


def test_neither_pointer_field_refuses() -> None:
    """Supplying neither pointer field is refused."""
    result = tombstone.serialize_tombstone(_SLUG, _DATE_A)
    assert result == "pointer-missing", f"expected 'pointer-missing', got {result!r}"


# ── Parser refusals ───────────────────────────────────────────────────────────


def test_fourth_field_refused_on_parse() -> None:
    """A tombstone text with four fields is refused by the parser."""
    # Manually construct a tombstone with an extra field.
    text = "\n".join([
        "# Tombstone: " + _SLUG,
        "",
        f"- **Slug:** `{_SLUG}`",
        f"- **Tombstone:** {_DATE_A}",
        f"- **Reissued as:** {_REISSUED_PATH}",
        "- **Extra:** unexpected",  # fourth field — one too many
    ]) + "\n"
    result = tombstone.parse_tombstone(text)
    assert result == "bad-shape", (
        f"expected 'bad-shape' for four-field tombstone, got {result!r}"
    )


def test_non_tombstone_text_refused_on_parse() -> None:
    """A live intent (no Tombstone: field) is refused by the parser."""
    live_intent_text = "\n".join([
        "# A live intent",
        "",
        "- **Slug:** `live-intent`",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** test-owner",
        "",
        "## Outcome",
        "",
        "A live intent body.",
    ])
    result = tombstone.parse_tombstone(live_intent_text)
    assert result == "not-tombstone", (
        f"expected 'not-tombstone' for live intent, got {result!r}"
    )


# ── B4: multiline value injection ─────────────────────────────────────────────


def test_multiline_retired_refuses_empty_retired() -> None:
    """A retired note with an embedded newline is refused.

    A multiline value would inject extra preamble fields into the serialised
    text. The single-line constraint maps this refusal to ``empty-retired``.
    """
    result = tombstone.serialize_tombstone(
        _SLUG,
        _DATE_A,
        retired=(
            "reason\n- **Reissued as:** docs/product/intents/FEAT-9999-injected.md"
        ),
    )
    assert result == "empty-retired", f"expected 'empty-retired', got {result!r}"


def test_newline_in_reissued_as_refuses_invalid_path() -> None:
    """A reissued_as path with an embedded newline is refused as invalid-path."""
    result = tombstone.serialize_tombstone(
        _SLUG,
        _DATE_A,
        reissued_as=f"{_REISSUED_PATH}\n- **Extra:** injected",
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_round_trip_property() -> None:
    """Every successful serialization parses back to exactly the three supplied values."""
    cases = [
        (_SLUG, _DATE_A, _REISSUED_PATH, None),
        (_SLUG, _DATE_A, None, _RETIRED_NOTE),
        (_SLUG, _DATE_B, _REISSUED_PATH, None),
        ("another-slug", "2025-01-01", f"{_INTENTS_PREFIX}/FEAT-0003-other.md", None),
    ]
    for slug, date, reissued, retired in cases:
        raw = tombstone.serialize_tombstone(slug, date, reissued_as=reissued, retired=retired)
        assert isinstance(raw, bytes), f"expected bytes for ({slug!r}, {date!r})"
        parsed = tombstone.parse_tombstone(raw.decode("utf-8"))
        assert isinstance(parsed, tombstone.Tombstone), (
            f"parse failed for ({slug!r}, {date!r}): {parsed!r}"
        )
        assert parsed.slug == slug
        assert parsed.date == date
        assert parsed.reissued_as == reissued
        assert parsed.retired == retired


# ── B6: intents directory itself accepted as successor ────────────────────────


def test_intents_directory_itself_refuses_invalid_path() -> None:
    """The intents directory path itself is refused as a successor."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="docs/product/intents"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


def test_intents_directory_trailing_slash_refuses_invalid_path() -> None:
    """The intents directory with trailing slash is refused as a successor."""
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as="docs/product/intents/"
    )
    assert result == "invalid-path", f"expected 'invalid-path', got {result!r}"


# ── Partition rule — both arms ────────────────────────────────────────────────


def test_serialized_tombstone_is_recognized_as_tombstone() -> None:
    """A serialized tombstone's text is recognized as a tombstone (forward arm).

    The partition rule says a file with ``Tombstone:`` is a tombstone.
    Parsing the serializer's output successfully proves the output carries
    that field and is recognized correctly.
    """
    result = tombstone.serialize_tombstone(
        _SLUG, _DATE_A, reissued_as=_REISSUED_PATH
    )
    assert isinstance(result, bytes)
    parsed = tombstone.parse_tombstone(result.decode("utf-8"))
    assert isinstance(parsed, tombstone.Tombstone), (
        "serialized tombstone not recognized as tombstone"
    )


def test_text_without_tombstone_field_is_not_a_tombstone() -> None:
    """A file without ``Tombstone:`` is not a tombstone (reverse arm).

    The partition rule says a file without ``Tombstone:`` is a live intent.
    Parsing such a file must refuse with ``not-tombstone``, not return a
    Tombstone. Replacing the partition guard would return ``bad-shape``
    instead, which the exact token assertion catches.
    """
    live_text = "\n".join([
        "# Not a tombstone",
        "",
        "- **Slug:** `not-a-tombstone`",
        "- **Status:** Draft",
        "- **Level:** feature",
        "- **Owner:** owner",
        "",
        "## Outcome",
        "",
        "Body.",
    ])
    result = tombstone.parse_tombstone(live_text)
    assert result == "not-tombstone", (
        f"expected 'not-tombstone' for live intent, got {result!r}"
    )
