"""Serialise and parse a tombstone for a retired repository intent.

A tombstone is a Markdown file whose preamble holds exactly three fields:
the original slug, the retirement date, and exactly one of two terminal
fields — a successor path (when the intent was reissued under a new name)
or a retirement note (when it was retired with no successor).

This module is pure: it performs no writes and reads no clock. The caller
supplies all values, including the retirement date. Sampling the date here
would put a clock inside a pure function and let an operation spanning
midnight write two different dates.

The tombstone field vocabulary and structural rules are owned by the sibling
corpus-lint module. This module imports those constants and functions rather
than re-declaring them, so the field set has one canonical home.

What this module adds — because no sibling implements it — is the writer,
plus three value-shape rules the corpus lint does not enforce:

    - The retirement date is one ISO 8601 calendar date in YYYY-MM-DD form.
    - The successor path is a repository-relative path whose normalised form
      stays inside ``docs/product/intents/``; an absolute path, or one that
      resolves outside that directory, is refused.
    - The retirement note is a single non-empty line.

Serialize refusal tokens:
    ``pointer-conflict``   — both successor-path and retirement-note were supplied.
    ``pointer-missing``    — neither was supplied.
    ``invalid-date``       — the date is not a valid ISO 8601 calendar date.
    ``invalid-path``       — the successor path is absolute or resolves outside
                             ``docs/product/intents/``.
    ``empty-retired``      — the retirement note is empty or whitespace only.

Parse refusal tokens:
    ``not-tombstone``      — the text carries no ``Tombstone:`` field.
    ``bad-shape``          — a structural rule is violated (wrong field count,
                             missing required field, or wrong pointer count).
    ``invalid-date``       — the ``Tombstone:`` value is not a valid ISO 8601 date.
    ``invalid-path``       — the ``Reissued as:`` value is an invalid path.
    ``empty-retired``      — the ``Retired:`` value is empty or whitespace only.
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Bytecode is a write; this module promises none.
sys.dont_write_bytecode = True

# ── Sibling loader ────────────────────────────────────────────────────────────


def _load_sibling(name: str, module_name: str) -> object:
    """Load a sibling script by path under a pack-and-skill-qualified name.

    Skills are independent and several may ship a same-named script, so a
    bare ``import`` would bind whichever directory reached the path first
    and then cache it for every later importer. Loading by path under a
    unique name avoids that collision.

    The module is registered in ``sys.modules`` **before** ``exec_module``
    runs, so any frozen dataclass defined inside it can resolve its own
    ``__module__`` attribute correctly.
    """
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot locate sibling module {name!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_shape = _load_sibling("intent_shape", "core_work_intake_intent_shape")
_lint = _load_sibling("intent_corpus_lint", "core_work_intake_intent_corpus_lint")

# ── Reuse the canonical tombstone vocabulary from the corpus lint ──────────────
# The corpus lint is the single home for these constants and structural
# functions. Importing them here keeps the field set in one place and
# prevents the two modules from drifting apart.

TOMBSTONE_PARTITION_FIELD: str = _lint.TOMBSTONE_PARTITION_FIELD  # type: ignore[attr-defined]
TOMBSTONE_REQUIRED: tuple[str, ...] = _lint.TOMBSTONE_REQUIRED  # type: ignore[attr-defined]
TOMBSTONE_EDGES: tuple[str, ...] = _lint.TOMBSTONE_EDGES  # type: ignore[attr-defined]
TOMBSTONE_FIELD_COUNT: int = _lint.TOMBSTONE_FIELD_COUNT  # type: ignore[attr-defined]

# ── Internal constants ────────────────────────────────────────────────────────

# The only directory a successor path may resolve into.
_INTENTS_PREFIX = "docs/product/intents"

# Strict ISO 8601 calendar-date pattern. ``datetime.date.fromisoformat``
# accepts ISO-8601 datetime strings in Python 3.11+, so a regex pre-check
# pins the format to YYYY-MM-DD before the parser runs.
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Tombstone dataclass ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Tombstone:
    """The three field values carried by a well-formed tombstone.

    Exactly one of ``reissued_as`` and ``retired`` is non-``None``.
    """

    slug: str
    """Original slug, unchanged from the retired artifact."""

    date: str
    """Retirement date — one ISO 8601 calendar date (YYYY-MM-DD)."""

    reissued_as: str | None
    """Repository-relative successor path, or ``None`` when not reissued."""

    retired: str | None
    """Single non-empty retirement note, or ``None`` when reissued."""


# ── Internal helpers ──────────────────────────────────────────────────────────


def _check_date(value: str) -> str | None:
    """Return ``"invalid-date"`` if value is not a valid ISO 8601 calendar date."""
    if not _ISO_DATE_RE.match(value):
        return "invalid-date"
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return "invalid-date"
    return None


def _check_reissued_path(path: str) -> str | None:
    """Return ``"invalid-path"`` unless path is repository-relative under intents.

    The value is repository-relative, so it is normalised as given rather than
    joined onto the intents prefix: joining would read a caller's
    ``docs/other/a.md`` as a name *inside* the intents directory and accept it,
    and would let ``docs/product/intents/../../x.md`` normalise back under the
    prefix it had already escaped.

    The check is purely lexical -- ``os.path.normpath`` rather than filesystem
    resolution -- because the successor named here need not exist yet. A
    backslash is rejected before normalisation, which treats it as an ordinary
    character on POSIX while Windows would read it as a separator.
    """
    if Path(path).is_absolute() or "\\" in path:
        return "invalid-path"
    normalised = os.path.normpath(path)
    if normalised != _INTENTS_PREFIX and not normalised.startswith(
        _INTENTS_PREFIX + "/"
    ):
        return "invalid-path"
    return None


# ── Public callables ──────────────────────────────────────────────────────────


def serialize_tombstone(
    slug: str,
    date: str,
    *,
    reissued_as: str | None = None,
    retired: str | None = None,
) -> bytes | str:
    """Validate inputs and return the tombstone's UTF-8 bytes, or a refusal token.

    The caller supplies the retirement date; this function never samples it.
    An operation spanning midnight therefore writes the date the caller held
    at the start of the transaction, not the one it finished on.

    Args:
        slug: The original slug from the retired artifact, unchanged.
        date: Retirement date as an ISO 8601 calendar date string (YYYY-MM-DD).
        reissued_as: Repository-relative successor path under
            ``docs/product/intents/``. Supply exactly one of ``reissued_as``
            or ``retired``.
        retired: Single non-empty retirement note. Supply exactly one of
            ``reissued_as`` or ``retired``.

    Returns:
        UTF-8 encoded tombstone bytes when all inputs are valid, or one of
        the fixed refusal tokens when a check fails.
    """
    # ── Pointer exclusivity ───────────────────────────────────────────────────
    has_reissued = reissued_as is not None
    has_retired = retired is not None
    if has_reissued and has_retired:
        return "pointer-conflict"
    if not has_reissued and not has_retired:
        return "pointer-missing"

    # ── Date shape ────────────────────────────────────────────────────────────
    date_fault = _check_date(date)
    if date_fault is not None:
        return date_fault

    # ── Path shape ────────────────────────────────────────────────────────────
    if has_reissued:
        path_fault = _check_reissued_path(reissued_as)  # type: ignore[arg-type]
        if path_fault is not None:
            return path_fault

    # ── Retired non-empty ─────────────────────────────────────────────────────
    if has_retired and not retired.strip():  # type: ignore[union-attr]
        return "empty-retired"

    # ── Build the tombstone text ──────────────────────────────────────────────
    lines = [
        f"# Tombstone: {slug}",
        "",
        f"- **Slug:** `{slug}`",
        f"- **Tombstone:** {date}",
    ]
    if has_reissued:
        lines.append(f"- **Reissued as:** {reissued_as}")
    else:
        lines.append(f"- **Retired:** {retired}")

    text = "\n".join(lines) + "\n"
    return text.encode("utf-8")


def parse_tombstone(text: str) -> Tombstone | str:
    """Parse a tombstone from its Markdown text and validate its field values.

    Uses the structural rules from the sibling corpus-lint module to decide
    whether the text is a tombstone and whether it conforms to the three-field
    contract. Applies the value-shape rules — ISO date, confined path, non-empty
    retirement note — that the corpus lint does not enforce.

    Args:
        text: The full Markdown text of the candidate tombstone file.

    Returns:
        A ``Tombstone`` when the text is structurally and value-valid, or
        one of the fixed refusal tokens when a check fails.
    """
    # ── Partition check ───────────────────────────────────────────────────────
    # Liveness is established positively. A text with no ``Tombstone:`` field
    # is not a tombstone; do not infer tombstonehood from any other signal.
    if not _lint._is_tombstone(text):  # type: ignore[attr-defined]
        return "not-tombstone"

    # ── Structural validation ─────────────────────────────────────────────────
    # Delegates to the corpus lint's structural check: required fields present,
    # exactly one pointer field, and exactly three fields total.
    faults = _lint._validate_tombstone(text)  # type: ignore[attr-defined]
    if faults:
        return "bad-shape"

    # ── Field extraction ──────────────────────────────────────────────────────
    pairs = _shape.read_preamble(text)  # type: ignore[attr-defined]
    fields: dict[str, str] = {}
    for name, value in pairs:
        if name not in fields:  # first occurrence wins (duplicates already refused above)
            fields[name] = value

    slug = fields.get("Slug", "")
    date_val = fields.get("Tombstone", "")
    reissued_as = fields.get("Reissued as")
    retired = fields.get("Retired")

    # ── Value-shape rules ─────────────────────────────────────────────────────

    # Date: must be a valid ISO 8601 calendar date.
    date_fault = _check_date(date_val)
    if date_fault is not None:
        return date_fault

    # Reissued as: must be a confined path when present.
    if reissued_as is not None:
        path_fault = _check_reissued_path(reissued_as)
        if path_fault is not None:
            return path_fault

    # Retired: must be non-empty when present.
    if retired is not None and not retired.strip():
        return "empty-retired"

    return Tombstone(
        slug=slug,
        date=date_val,
        reissued_as=reissued_as if reissued_as else None,
        retired=retired if retired else None,
    )
