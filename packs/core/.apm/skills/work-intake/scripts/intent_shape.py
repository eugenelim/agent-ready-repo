#!/usr/bin/env python3
"""Decide the metadata shape contract for a repository intent.

This module is the single home for the field rules, and a reviewer or a lint
carrying its own copy of the table is a second home that drifts from this one.

Two surfaces read it. ``validate_live_intent`` decides a rule from one artifact
alone, and is the surface the shaping reviewer's preamble condition refers to —
that condition names the obligation and defers every member list here rather
than restating it. ``validate_supersession`` is called by the corpus lint alone,
and holds the rules that need more than one artifact or that ask what another
field's value requires.

What a shaping reviewer then emits is not this module's to state: it retrieves
nothing, so that depends on what a caller puts in its packet.

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

STATUS_VALUES: tuple[str, ...] = (
    "Draft",
    "Accepted",
    "Fulfilled",
    "Withdrawn",
    "Cancelled",
    "Superseded",
)

# `Status` is one bare lifecycle token and the supersession pointer is a field of
# its own, mirroring the ADR corpus rather than embedding a payload in a status.
# The two are paired in both directions: the forward rule carries what the old
# parameterized form said by refusing an empty payload, and the reverse rule
# catches the failure the split introduces, a pointer that outlives its status.
SUPERSEDED_STATUS = "Superseded"
SUPERSEDED_BY_FIELD = "Superseded by"

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
    if value in STATUS_VALUES:
        return None
    permitted = ", ".join(STATUS_VALUES)
    return f"value {value!r} is outside {permitted}"


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


def _check_dated_evidence(value: str) -> str | None:
    """Require an ISO 8601 calendar date, a space, then non-empty text.

    `Accepted:` and `Fulfilled:` assert that a bet was ratified or delivered,
    and the record exists to carry what says so — a bare date carries none, and
    the literal `no` that the progress fields accept is not an available answer
    here, because an unratified intent omits the field rather than denying it.

    The calendar-date rule stays in `_is_iso_date`: this partitions at the first
    space and hands the head over, exactly as `_check_decomposed` does. Keeping
    one home is what makes `2026-09-20,` refuse — the trailing comma is inside
    the date token, and a second, looser pattern here would silently admit it.
    """
    stamp, separator, evidence = value.partition(" ")
    if not separator or not evidence.strip():
        return (
            f"value {value!r} is not an ISO 8601 date followed by evidence text"
        )
    if not _is_iso_date(stamp):
        return f"{stamp!r} is not an ISO 8601 date"
    return None


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
    "Accepted": _check_dated_evidence,
    "Fulfilled": _check_dated_evidence,
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
    present = present_fields(text)

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


def present_fields(text: str) -> dict[str, str]:
    """Return each preamble field's effective value, first non-empty wins.

    One home for the rule that a repeated field is judged on its first stated
    value and that an emptied value is absent. Every consumer that asks "what
    does this preamble say" reads it here, so a second consumer cannot answer
    the question differently.
    """
    present: dict[str, str] = {}
    for name, value in read_preamble(text):
        if value and name not in present:
            present[name] = value
    return present


def slug_of(text: str) -> str | None:
    """Return the intent's normalized ``Slug:`` value, or None when absent."""
    for name, value in read_preamble(text):
        if name == "Slug" and value:
            return value
    return None


def resolvable_slugs(texts: Iterable[str]) -> set[str]:
    """Collect the slugs a ``Superseded by:`` pointer may name.

    Two exclusions, and the second is the one that is easy to lose. A tombstone
    is already excluded by the caller, which hands over the live partition. An
    intent that is *itself* ``Superseded`` is excluded here, because resolution
    is one hop: a pointer at a superseded bet leaves a reader one step short of
    the artifact that replaced it, so the chain is refused and re-pointed
    instead. No other status is excluded — a ``Cancelled`` or ``Withdrawn``
    target resolves, because only ``Superseded`` names a successor this pointer
    would otherwise have to follow.

    That exclusion cannot be asserted from a hand-built slug set — the caller's
    partition decides it — so its control runs through the corpus lint.

    The comparand is normalized rather than raw: the corpus's dominant shape is
    a backticked slug whose comment trails the closing backtick, so a raw
    comparison would match nothing.
    """
    collected: set[str] = set()
    for text in texts:
        if present_fields(text).get("Status") == SUPERSEDED_STATUS:
            continue
        slug = slug_of(text)
        if slug:
            collected.add(slug)
    return collected


def superseding_slug(text: str) -> str | None:
    """Return the slug an intent's ``Superseded by:`` field names, if any.

    Reads the field rather than slicing a prefix off ``Status:``. A value the
    normalization stage emptied is absent, which is ``_check_supersession_pair``'s
    to refuse rather than this function's to report as a slug.
    """
    for name, value in read_preamble(text):
        if name == SUPERSEDED_BY_FIELD and value:
            return value
    return None


def validate_supersession(text: str, live: set[str]) -> list[Violation]:
    """Decide both corpus-scoped supersession rules for one intent.

    Two faults, reported in the order they can be fixed: the status and the
    pointer must be present together, and the pointer must then resolve.

    Kept out of ``validate_live_intent`` deliberately, for two reasons that
    happen to point the same way. ``validate_live_intent`` decides a rule from
    one artifact alone, and resolution needs the rest of the corpus. The pairing
    rule is settleable from one artifact, but it is a rule about which field
    another field's value requires, which the reviewer's preamble condition does
    not reach; ``_check_supersession_pair`` states that at length.
    """
    violations = _check_supersession_pair(text)
    if violations:
        # The pair is malformed, so there is no pointer worth resolving. Report
        # the structural fault alone rather than stacking a resolution failure
        # on top of it.
        return violations

    slug = superseding_slug(text)
    if slug is None or slug in live:
        return []
    return [
        Violation(
            SUPERSEDED_BY_FIELD,
            f"slug {slug!r} matches no intent this pointer may resolve to: "
            "the target must be live and not itself `Superseded`",
        )
    ]


def _check_supersession_pair(text: str) -> list[Violation]:
    """Refuse a `Superseded` status and a `Superseded by:` pointer apart.

    Both arms are needed and neither implies the other. The forward arm carries
    what the retired ``Superseded by <slug>`` form said by refusing an empty
    payload. The reverse arm is what the split newly requires: while the pointer
    lived inside the value, a status change discarded it, and now it survives one
    — so a pointer left beside `Draft` would otherwise go unread and unrefused.

    Corpus-lint-only, and the seam is the point. ``validate_live_intent`` is the
    surface the shaping reviewer's preamble condition refers to, and that
    condition obliges "every field whose values the contract fixes carries one of
    them" — a rule about one field's *value*. This is a rule about which field
    another field's value *requires*, which those words do not reach, so it is
    not a rule that condition can be read as covering. Any rule of that kind
    belongs here, beside the ones that need the whole corpus.
    """
    present = present_fields(text)
    status = present.get("Status")
    pointer = present.get(SUPERSEDED_BY_FIELD)

    if status == SUPERSEDED_STATUS and pointer is None:
        return [
            Violation(
                SUPERSEDED_BY_FIELD,
                f"`Status: {SUPERSEDED_STATUS}` carries no `{SUPERSEDED_BY_FIELD}:` "
                "field naming the intent that replaced this bet",
            )
        ]
    if pointer is not None and status != SUPERSEDED_STATUS:
        named = f"`Status: {status}`" if status else "no `Status:` value"
        return [
            Violation(
                SUPERSEDED_BY_FIELD,
                f"field is present beside {named}, and only "
                f"`Status: {SUPERSEDED_STATUS}` carries a supersession pointer",
            )
        ]
    return []


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
