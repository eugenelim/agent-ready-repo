#!/usr/bin/env python3
"""Vocabulary, coherence rules, and bounded preamble reader for delivery briefs.

This module is the single home for the brief state vocabulary, the child-
execution-evidence predicate, the legal transition set, and the bounded preamble
reader.  A reviewer or a lint carrying its own copy of any of these is a second
home that can drift from this one.

The brief state table lives in the spec that owns this module's docstring.
This module implements that table; its docstring cites rather than restating it.

**Two mirrors are maintained by hand** because cross-skill import is banned:

- ``extract_token`` mirrors ``lint-spec-status.extract_status_token`` (same
  delimiters: `` (```, `` →``, and ``<!--``).  Keep them in lockstep.
- The ``Cut-closed:`` date-grammar check mirrors ``intent_shape._check_dated_evidence``
  (same partition-at-first-space rule).  Keep them in lockstep.

Both mirrors are hand-held by design; this docstring is the only thing that
makes their absence visible.

**Refusal registry** — every refusal this module raises corresponds to one of
the following classes.  Keep this list equal to the set of errors the module
actually raises; update it in the same change that adds or removes one.

- ``cut_closed_malformed`` — a ``Cut-closed:`` value that is not absent-
  equivalent and does not follow the ISO 8601 date + evidence grammar.
"""

from __future__ import annotations

import re
import sys
from datetime import date

# Reconfigure stdout/stderr to UTF-8 so any diagnostic output is safe on
# platforms where the default encoding is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

# ── Regexes ───────────────────────────────────────────────────────────────────

# Anchored at line start: a field line must begin with `- **Name:**`.
# This ensures ATX headings (starting with `#`) and blockquote lines
# (starting with `>`) cannot match without an explicit skip check.
_FIELD_RE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")

# A level-2 ATX heading in live (non-comment) content ends the preamble.
_HEADING_PREFIX = "## "

# ISO 8601 calendar date (YYYY-MM-DD only — compact and extended-time forms
# are not accepted).
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Comment-aware line processor ──────────────────────────────────────────────


def _process_line(line: str, in_comment: bool) -> tuple[str, bool]:
    """Return ``(live_text, comment_state_after)`` for one line.

    Processes the line left-to-right, switching between comment and non-comment
    regions.  ``live_text`` contains only the characters outside HTML comments;
    ``comment_state_after`` is the state to carry into the next line.
    """
    live_parts: list[str] = []
    pos = 0
    while pos < len(line):
        if in_comment:
            close = line.find("-->", pos)
            if close == -1:
                # Remainder of the line is inside the comment.
                break
            in_comment = False
            pos = close + 3  # skip past -->
        else:
            open_ = line.find("<!--", pos)
            if open_ == -1:
                # Remainder of the line is live.
                live_parts.append(line[pos:])
                break
            live_parts.append(line[pos:open_])
            in_comment = True
            pos = open_ + 4  # skip past <!--
    return "".join(live_parts), in_comment


# ── Preamble reader ───────────────────────────────────────────────────────────


def read_preamble(text: str) -> list[tuple[str, str]]:
    """Return ``(field_name, raw_value)`` pairs from the brief's bounded preamble.

    Reads only the region before the first uncommented level-2 heading (``## ``).
    HTML comments are handled in a single left-to-right pass; a field inside a
    comment is not returned.  If the document ends with an unclosed HTML comment,
    returns an empty list — an unterminated comment invalidates the entire read.

    Fields that are themselves ATX headings or inside blockquotes are skipped.
    """
    pairs: list[tuple[str, str]] = []
    in_comment = False

    for line in text.splitlines():
        in_comment_before = in_comment
        live, in_comment = _process_line(line, in_comment)

        # An uncommented ## heading ends the preamble.
        live_stripped = live.strip()
        if live_stripped.startswith(_HEADING_PREFIX):
            break

        # Lines entered inside a comment carry no live content at their start
        # and must be skipped entirely so in_comment propagates correctly.
        if in_comment_before:
            continue

        # Skip lines whose entire live content is empty (e.g. `<!--` alone).
        if not live_stripped:
            continue

        # Blockquote lines are not preamble fields.
        if line.startswith(">"):
            continue

        # ATX heading lines (any level) are not preamble fields.
        if line.lstrip().startswith("#"):
            continue

        m = _FIELD_RE.match(line)
        if m:
            pairs.append((m.group(1).strip(), m.group(2).strip()))

    # An unterminated HTML comment invalidates the preamble: return nothing.
    if in_comment:
        return []

    return pairs


# ── Shared tokenizer ──────────────────────────────────────────────────────────


def extract_token(raw: str) -> str:
    """Return the leading token from a preamble value, truncating at delimiters.

    Truncates at the first occurrence of `` (`` (parenthesised annotation),
    `` →`` (transition arrow), or ``<!--`` (inline HTML comment), then returns
    the first whitespace-delimited word.  An empty result means the value is
    absent or comment-only.

    Mirrors ``lint-spec-status.extract_status_token`` (same delimiters).
    Cross-skill import is banned, so these must be kept in lockstep by hand.
    """
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    parts = text.strip().split()
    return parts[0] if parts else ""


# ── ISO date helper ───────────────────────────────────────────────────────────


def _is_iso_date(value: str) -> bool:
    """True for a real ``YYYY-MM-DD`` calendar date.

    Checks pattern before parsing so that compact forms (``20260101``) and
    extended-time forms are rejected, not just invalid calendar dates.
    """
    if not _ISO_DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


# ── Cut-closed value rules ────────────────────────────────────────────────────


def _is_absent_cut_closed(raw: str) -> bool:
    """True when a raw ``Cut-closed:`` value counts as absent rather than set.

    A value is absent when it is empty or consists entirely of HTML comments.
    This lets a template row (``<!-- not set yet -->``) be copied into a new
    brief without producing a refusal.
    """
    stripped = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL).strip()
    return not stripped


def validate_cut_closed(value: str) -> str | None:
    """Return an error message if ``value`` is not a valid ``Cut-closed:`` value.

    A valid value is an ISO 8601 calendar date (``YYYY-MM-DD``) followed by a
    space and non-empty evidence text.  Returns ``None`` when the value is valid.

    Mirrors ``intent_shape._check_dated_evidence`` (same partition-at-first-space
    rule).  Cross-skill import is banned, so these must be kept in lockstep by
    hand.
    """
    stamp, separator, evidence = value.partition(" ")
    if not separator or not evidence.strip():
        return (
            f"value {value!r} is not an ISO 8601 date followed by evidence text"
        )
    if not _is_iso_date(stamp):
        return f"{stamp!r} is not an ISO 8601 date"
    return None


# ── Per-field accessors ───────────────────────────────────────────────────────


def get_status(text: str) -> str | None:
    """Return the brief's ``Status:`` token from the bounded preamble, or ``None``.

    Applies ``extract_token`` to normalise annotated statuses such as
    ``Shipped (2026-08-25)`` or ``Draft <!-- ... -->``.
    """
    for name, value in read_preamble(text):
        if name == "Status":
            token = extract_token(value)
            return token if token else None
    return None


def _is_placeholder(value: str) -> bool:
    """True for unset/template values: empty, ``none``, HTML comment, or ``<...>``."""
    v = value.strip()
    return (
        not v
        or v.lower() == "none"
        or v.startswith("<!--")
        or (v.startswith("<") and v.endswith(">"))
    )


def get_slug(text: str, fallback: str) -> str:
    """Return the brief's ``Slug:`` from the bounded preamble, or ``fallback``.

    Strips backtick code formatting and applies ``extract_token`` to normalise
    annotated values.  Falls back to ``fallback`` (typically the filename stem)
    when no usable ``Slug:`` field is present.
    """
    for name, value in read_preamble(text):
        if name == "Slug":
            stripped = value.strip().strip("`").strip()
            if stripped and not _is_placeholder(stripped):
                return extract_token(stripped).strip("`")
    return fallback


def get_cut_closed(text: str) -> str | None:
    """Return the raw ``Cut-closed:`` value if present, or ``None`` if absent.

    A value that is empty or consists only of HTML comments counts as absent,
    so a template row does not produce a value.  Does not validate the value;
    call ``validate_cut_closed`` separately if the value is not ``None``.
    """
    for name, value in read_preamble(text):
        if name == "Cut-closed":
            if _is_absent_cut_closed(value):
                return None
            return value
    return None
