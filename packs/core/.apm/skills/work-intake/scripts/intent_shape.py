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
from typing import Callable

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


VALUE_RULES: dict[str, Callable[[str], str | None]] = {
    "Status": _check_status,
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

    return violations
