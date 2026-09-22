#!/usr/bin/env python3
"""Decide the metadata shape contract for a repository intent.

This module is the single home for the field rules. Both enforcement points
read them from here — the corpus lint by walking a directory, the shaping
reviewer by reading one supplied preamble against prose that names the field
list rather than restating it. A reviewer or a lint carrying its own copy of
the table is a second home that drifts from this one.

Two properties are load-bearing and easy to get wrong:

Normalization runs once per value, **comment first, then backticks**. The
corpus's dominant shape is ``- **Slug:** `value` <!-- ... -->``, where the
comment trails the closing backtick. Stripping backticks first no-ops on that
shape, because the line does not end in a backtick, and every later rule then
judges a value that is still quoted.

The preamble is a **bounded region**, not a pattern: the run of lines before the
first ``## `` heading. A ``- **Status:**`` line can sit inside a de-risk record
body, where its value is a probe's narrative, and a bolded
``- **Authority:**`` line can sit inside ``## Source``, where it is an owner
attribution rather than the governance pointer the preamble field holds. A
whole-file pattern match corrupts both.

A field name absent from the table is accepted. That is what keeps
``Milestone:`` and any future organic field passing while the six retired names
fail, and it is why the retired-name rule needs both halves.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

# ── The field table ───────────────────────────────────────────────────────────
# Four tiers: required, constrained-when-present, unconstrained, retired.
# `Level` is required and carries no value rule: ADR-0033 D2 keeps its set open
# and states that a lint cannot enforce a closed one.

REQUIRED_FIELDS: tuple[str, ...] = ("Owner", "Slug", "Level", "Status")

RETIRED_FIELDS: tuple[str, ...] = (
    "Type",
    "Raised",
    "Stage",
    "Parent",
    "Source",
    "Authority",
)

STATUS_BARE_VALUES: tuple[str, ...] = (
    "Draft",
    "Accepted",
    "Fulfilled",
    "Withdrawn",
    "Cancelled",
)

# `Superseded by <slug>` carries a payload the bare values do not, so `Status`
# is a membership-or-parameterized-form rule rather than plain membership.
SUPERSEDED_PREFIX = "Superseded by "

CLOSED_VOCABULARIES: dict[str, tuple[str, ...]] = {
    "Kind": ("outcome", "opportunity"),
    "Scale": ("app", "business-unit"),
    "Maturity": ("greenfield", "brownfield"),
}

# The three shaping-progress fields. Each reports one of three states, and the
# pair absence/`no` is the distinction a report must keep: an intent nobody has
# probed and one deliberately recorded as not de-risked are different facts.
PROGRESS_FIELDS: tuple[str, ...] = ("De-risked", "Shaping-reviewed", "Decomposed")
PROGRESS_ABSENT = "absent"
PROGRESS_NO = "no"

DECOMPOSITION_TERMINI: tuple[str, ...] = (
    "children",
    "brief",
    "spec",
    "direct-light",
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# `*`/`+` markers and up to three spaces of indentation are ordinary Markdown
# for a list item. Matching only an unindented hyphen made an indented item
# read as absent, which refuses a conforming intent and skips an empty one.
# Four spaces is deliberately excluded: CommonMark renders that as a code
# block, so counting it would credit an item no reader can see.
_CHECKBOX = re.compile(r"^ {0,3}[-*+] \[[ xX]\]\s*(.*)$")
_DECOMPOSITION_HEADING = "## Decomposition"

_COMMENT_SUFFIX = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)
_FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_HEADING = "## "


@dataclass(frozen=True)
class Violation:
    """One refusal, naming the field at fault and why it was refused."""

    field: str
    reason: str


# ── The normalization stage ───────────────────────────────────────────────────


def normalize_value(raw: str) -> str:
    """Reduce a written field value to the value every rule decides on.

    Discards a trailing HTML comment, then strips surrounding backticks. The
    order is the contract: reversing it leaves the corpus's dominant shape
    backticked. A value that is empty once this has run is absent, not
    malformed — that is the `frame-intent` template's comment-only
    ``Parent intent:`` line, which no rule may refuse.
    """
    value = raw.strip()
    value = _COMMENT_SUFFIX.sub("", value).strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def read_preamble(text: str) -> list[tuple[str, str]]:
    """Return the preamble's ``(field name, normalized value)`` pairs in order.

    Reads only the run of lines before the first ``## `` heading, so a
    field-shaped line in the body is neither returned nor judged.
    """
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith(_HEADING):
            break
        match = _FIELD_LINE.match(line)
        if match:
            pairs.append((match.group(1).strip(), normalize_value(match.group(2))))
    return pairs


def decomposition_items(text: str) -> list[str]:
    """Return the text of each checkbox item under ``## Decomposition``.

    An absent section and a section carrying no item both return an empty list,
    which is correct: the contract refuses both the same way.
    """
    items: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith(_HEADING):
            inside = line.strip() == _DECOMPOSITION_HEADING
            continue
        if inside:
            match = _CHECKBOX.match(line)
            if match:
                items.append(match.group(1))
    return items


def progress_state(text: str) -> dict[str, str]:
    """Report each progress field as absent, the literal ``no``, or its date.

    Absence is a reportable state rather than a fault, so this is separate from
    ``validate_live_intent``: a corpus whose only irregularity is an unprobed
    intent is clean, and the report still says so.
    """
    present: dict[str, str] = {}
    for name, value in read_preamble(text):
        if value and name not in present:
            present[name] = value

    state: dict[str, str] = {}
    for field in PROGRESS_FIELDS:
        value = present.get(field)
        if value is None:
            state[field] = PROGRESS_ABSENT
        elif value == PROGRESS_NO:
            state[field] = PROGRESS_NO
        else:
            state[field] = value
    return state


# ── Value rules ───────────────────────────────────────────────────────────────


def _check_status(value: str) -> str | None:
    if value in STATUS_BARE_VALUES:
        return None
    if value.startswith(SUPERSEDED_PREFIX):
        slug = value[len(SUPERSEDED_PREFIX) :].strip()
        if slug:
            return None
        return "`Superseded by` carries no slug"
    permitted = ", ".join(STATUS_BARE_VALUES)
    return f"value {value!r} is outside {permitted}, and `{SUPERSEDED_PREFIX}<slug>`"


def _closed_vocabulary_rule(field: str) -> Callable[[str], str | None]:
    members = CLOSED_VOCABULARIES[field]

    def check(value: str) -> str | None:
        if value in members:
            return None
        return f"value {value!r} is outside {', '.join(members)}"

    return check


def _is_iso_date(value: str) -> bool:
    """True for a real ``YYYY-MM-DD`` date.

    The pattern is checked before parsing because `date.fromisoformat` also
    accepts forms this contract does not, such as the compact ``20260921``.
    """
    if not _ISO_DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _check_date_or_no(value: str) -> str | None:
    if value == PROGRESS_NO or _is_iso_date(value):
        return None
    return f"value {value!r} is neither an ISO 8601 date nor the literal `no`"


def _check_decomposed(value: str) -> str | None:
    if value == PROGRESS_NO:
        return None
    parts = value.split()
    if len(parts) != 2:
        return (
            f"value {value!r} is neither the literal `no` nor an ISO 8601 date "
            "followed by exactly one terminus"
        )
    stamp, terminus = parts
    if not _is_iso_date(stamp):
        return f"{stamp!r} is not an ISO 8601 date"
    if terminus not in DECOMPOSITION_TERMINI:
        permitted = ", ".join(DECOMPOSITION_TERMINI)
        return f"terminus {terminus!r} is outside {permitted}"
    return None


VALUE_RULES: dict[str, Callable[[str], str | None]] = {
    "Status": _check_status,
    "De-risked": _check_date_or_no,
    "Shaping-reviewed": _check_date_or_no,
    "Decomposed": _check_decomposed,
    **{field: _closed_vocabulary_rule(field) for field in CLOSED_VOCABULARIES},
}


# ── The contract ──────────────────────────────────────────────────────────────


def validate_live_intent(text: str) -> list[Violation]:
    """Return every way ``text``'s preamble fails the live-intent contract.

    An empty list is acceptance. Violations are returned rather than raised so
    a caller reports every fault in a corpus rather than the first.
    """
    pairs = read_preamble(text)
    occurrences = Counter(name for name, _ in pairs)

    # A value that normalized to empty is absent, so it does not reach a rule.
    present: dict[str, str] = {}
    for name, value in pairs:
        if value and name not in present:
            present[name] = value

    violations: list[Violation] = []

    for name in sorted(occurrences):
        count = occurrences[name]
        if count > 1:
            violations.append(
                Violation(name, f"preamble field appears more than once ({count})")
            )
        if name in RETIRED_FIELDS:
            violations.append(Violation(name, "retired preamble field name"))

    for name in REQUIRED_FIELDS:
        if name not in present:
            violations.append(Violation(name, "required preamble field is absent"))

    for name, value in present.items():
        rule = VALUE_RULES.get(name)
        if rule is not None:
            reason = rule(value)
            if reason is not None:
                violations.append(Violation(name, reason))

    violations.extend(_check_direct_light_decomposition(text, present))
    return violations


def slug_of(text: str) -> str | None:
    """Return the intent's normalized ``Slug:`` value, or None when absent."""
    for name, value in read_preamble(text):
        if name == "Slug" and value:
            return value
    return None


def live_slugs(texts: Iterable[str]) -> set[str]:
    """Collect the normalized ``Slug:`` value of each supplied live intent.

    The comparand is normalized rather than raw: the corpus's dominant shape is
    a backticked slug whose comment trails the closing backtick, so a raw
    comparison would match nothing.
    """
    collected: set[str] = set()
    for text in texts:
        slug = slug_of(text)
        if slug:
            collected.add(slug)
    return collected


def superseding_slug(text: str) -> str | None:
    """Return the slug an intent's ``Status:`` supersession names, if any."""
    for name, value in read_preamble(text):
        if name != "Status" or not value:
            continue
        if value.startswith(SUPERSEDED_PREFIX):
            slug = value[len(SUPERSEDED_PREFIX) :].strip()
            return slug or None
        return None
    return None


def validate_supersession(text: str, live: set[str]) -> list[Violation]:
    """Refuse a supersession pointing at no live intent's ``Slug:``.

    Kept out of ``validate_live_intent`` deliberately. Every criterion that
    function decides is settleable from the supplied artifact alone, and the
    shaping reviewer retrieves nothing — so a rule needing the rest of the
    corpus cannot live there without making the reviewer refuse every intent
    that carries a pointer.
    """
    slug = superseding_slug(text)
    if slug is None or slug in live:
        return []
    return [
        Violation(
            "Status",
            f"`Superseded by` slug {slug!r} matches no live intent's `Slug:`",
        )
    ]


def _check_direct_light_decomposition(
    text: str, present: dict[str, str]
) -> list[Violation]:
    """Judge ``## Decomposition`` only under a `direct-light` terminus.

    The section is unread for the other three termini: what a direct-light run
    owes is each item's requested outcome, which otherwise exists only in a
    session. Runs only once the value itself is well formed, so a malformed
    ``Decomposed:`` is reported once rather than twice.
    """
    value = present.get("Decomposed")
    if value is None or _check_decomposed(value) is not None:
        return []
    parts = value.split()
    if len(parts) != 2 or parts[1] != "direct-light":
        return []

    items = decomposition_items(text)
    if not items:
        return [
            Violation(
                "Decomposed",
                "`direct-light` terminus carries no checkbox item under "
                "`## Decomposition`",
            )
        ]
    if any(not item.strip() for item in items):
        return [
            Violation(
                "Decomposed",
                "a `## Decomposition` checkbox item carries no text",
            )
        ]
    return []
