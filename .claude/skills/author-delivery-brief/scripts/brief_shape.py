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
- ``cut_closed_required_on_shipped`` — a ``Shipped`` brief carries no
  ``Cut-closed:`` record.
- ``cut_closed_refused_on_draft`` — a ``Draft`` brief carries a
  ``Cut-closed:`` record.
"""

from __future__ import annotations

import re
from datetime import date

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


def process_line(line: str, in_comment: bool) -> tuple[str, bool]:
    """Return ``(live_text, comment_state_after)`` for one line.

    Public scanning primitive used by the preamble reader and the Spec-map
    parser.  Processes the line left-to-right, switching between comment and
    non-comment regions.  ``live_text`` contains only the characters outside
    HTML comments; ``comment_state_after`` is the state to carry into the next
    line.
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
        live, in_comment = process_line(line, in_comment)

        # An uncommented ## heading ends the preamble.  The check reads the
        # live prefix before leading whitespace is removed, so a line that
        # closes a comment and then carries a heading -- '--> ## Outcome',
        # whose live text starts with a space -- is not a terminator.  The
        # Spec-map scanner makes the same choice for the same reason: stripping
        # first would end the bound early and silently drop a live field below
        # it, which is the miss this reader exists to prevent.
        if live.startswith(_HEADING_PREFIX):
            break

        live_stripped = live.strip()

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
        return f"value {value!r}: {stamp!r} is not an ISO 8601 date"
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


def is_placeholder(value: str) -> bool:
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
            if stripped and not is_placeholder(stripped):
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


# ── Status vocabulary ─────────────────────────────────────────────────────────

BRIEF_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"}
)
"""The six tokens that are valid values for a brief's ``Status:`` field.

This is the single home for the vocabulary.  A check that carries its own
copy is a second home that can drift from this one.
"""


# ── Child-execution-evidence predicate ───────────────────────────────────────


def is_lifecycle_valid(status: str | None, child_states: set[str]) -> bool:
    """Return whether child execution evidence is coherent with the brief's status.

    A brief's children are its Spec-map rows together with any spec that
    back-links the brief and is absent from that map.  The predicate normalises
    child states to lower-case before comparing.

    Rules (from the brief state table):

    - ``Draft``, ``Ready``, ``Withdrawn``: no child at ``Implementing`` or
      ``Shipped``.
    - ``Executing``, ``Cancelled``: at least one child at ``Implementing`` or
      ``Shipped``.
    - ``Shipped``: non-empty child set whose every member is ``Shipped``.
    - Any other status (including ``None``): returns ``False``.
    """
    normalized = {state.lower() for state in child_states}
    execution_evidence = bool(normalized & {"implementing", "shipped"})
    if status in {"Draft", "Ready", "Withdrawn"}:
        return not execution_evidence
    if status in {"Executing", "Cancelled"}:
        return execution_evidence
    if status == "Shipped":
        return bool(normalized) and normalized == {"shipped"}
    return False


# ── Declaration matrix ────────────────────────────────────────────────────────


def validate_declaration(status: str | None, has_cut_closed: bool) -> str | None:
    """Return an error message when the ``Cut-closed:`` record conflicts with status.

    ``Shipped`` requires the record; ``Draft`` refuses it.  All other states
    accept either.  Returns ``None`` when there is no conflict.
    """
    if status == "Shipped" and not has_cut_closed:
        return "status is Shipped but no Cut-closed: record is present"
    if status == "Draft" and has_cut_closed:
        return "status is Draft but a Cut-closed: record is present"
    return None


# ── Transition table ──────────────────────────────────────────────────────────

BRIEF_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("Draft", "Ready"),
        ("Draft", "Withdrawn"),
        ("Ready", "Draft"),
        ("Ready", "Executing"),
        ("Ready", "Withdrawn"),
        ("Executing", "Ready"),
        ("Executing", "Shipped"),
        ("Executing", "Cancelled"),
    }
)
"""Legal (from, to) state pairs for a delivery brief.

Terminal states (``Shipped``, ``Withdrawn``, ``Cancelled``) have no outgoing
edges and are absent from this set.  A pair of two different states absent
from this table is an illegal move.  A state paired with itself is not a
move and is not refused.
"""


def is_transition_valid(from_state: str, to_state: str) -> bool:
    """Return ``True`` when moving from ``from_state`` to ``to_state`` is legal.

    A self-pair (same state to same state) is not a move and is not refused.
    A pair of two different states absent from ``BRIEF_TRANSITIONS`` is an
    illegal move and returns ``False``.
    """
    if from_state == to_state:
        return True
    return (from_state, to_state) in BRIEF_TRANSITIONS
