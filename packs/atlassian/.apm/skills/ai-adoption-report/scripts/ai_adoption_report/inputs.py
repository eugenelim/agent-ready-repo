"""T2 input file loader.

Reads one flow-metrics JSON, validates the ``meta`` block, infers the
scope ``kind`` from key presence, and returns an :class:`InputFile`
dataclass that the three mode-runners (T3/T4) consume.

Validation rules come from ``docs/specs/ai-adoption-report.md`` §
"Input file validation" (lines 100-146). Every error message names the
file basename; the basename is the only locator the user reliably
recognises across the program-mode glob and the single-file modes.

Stdlib only. Read-only — no subprocess, no writes.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from . import ValidationError

# Required meta keys per spec lines 102-105. Order matches the spec
# sentence so the test parameter set reads top-to-bottom against the
# spec.
REQUIRED_META_KEYS: Tuple[str, ...] = (
    "scope",
    "window",
    "state_config_sha",
    "issuetype_config_sha",
    "schema_version",
    "generated_at",
)

# Spec lines 121-124: YYYY-MM-DD only — no time component, no timezone.
# ``date.fromisoformat`` accepts ``2026-02-19T00:00:00`` on newer Pythons,
# so the regex is the first gate; ``date.fromisoformat`` then validates
# that the YYYY/MM/DD parts form a real calendar date.
_ISO_DATE_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")

# Spec lines 114-119: schema_version is ``<int>.<int>``. Anything else
# exits 2. Trailing ``.0`` is fine (still two parts); ``1.0.0`` is not.
_SCHEMA_VERSION_RE = re.compile(r"\A(\d+)\.(\d+)\Z")


@dataclass
class InputFile:
    """One validated flow-metrics JSON file.

    Fields mirror the plan §T2 dataclass shape (lines 169-175). Raw
    blocks (``scope``, ``meta``, ``aggregates``) are kept intact for
    downstream consumers; ``scope_kind``, ``window_from``, ``window_to``
    and ``schema_version`` are the parsed/inferred conveniences.
    """

    path: Path
    basename: str
    scope: dict
    scope_kind: str
    window_from: str
    window_to: str
    meta: dict
    aggregates: dict
    cohort_breakdown: Optional[dict]
    per_team: Optional[list]
    schema_version: Tuple[int, int]
    notes_from_upstream: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scope-kind inference (spec lines 130-146).
# ---------------------------------------------------------------------------
def infer_scope_kind(scope: dict, *, basename: str) -> str:
    """Return one of the six recognised scope kinds.

    Spec-pinned kinds (spec lines 130-146):
    ``portfolio`` / ``program`` / ``project`` / ``project+team``.

    Synthesized-only kinds (introduced by T4's per_team flattening of a
    program- or portfolio-scope input; flagged for spec amendment):
    ``program+team`` / ``portfolio+team``. These are not produced by
    `flow-metrics` directly — they only arise when T4 synthesises a
    scope dict by carrying forward the source input's
    ``program_id`` / ``portfolio_id`` and attaching a ``team`` value
    from a ``per_team`` entry. Accepting them here keeps inference in
    one place; the alternative (a special-case path in T4) was rejected
    so that T4 can re-infer the kind on the synthesised dict.

    Anything outside the table raises :class:`ValidationError`.

    ``basename`` is woven into the error message so the user can tell
    which file in a program-mode glob is offending without re-running.
    """
    if not isinstance(scope, dict):
        raise ValidationError(
            "{}: meta.scope must be an object; got {}".format(
                basename, type(scope).__name__
            )
        )

    has_portfolio = "portfolio_id" in scope
    has_program = "program_id" in scope
    has_project = "project" in scope
    has_team = "team" in scope

    if has_portfolio and not (has_program or has_project):
        return "portfolio+team" if has_team else "portfolio"
    if has_program and not (has_portfolio or has_project):
        return "program+team" if has_team else "program"
    if has_project and not (has_portfolio or has_program):
        return "project+team" if has_team else "project"

    raise ValidationError(
        "unrecognised scope shape in {}: {}".format(basename, scope)
    )


# ---------------------------------------------------------------------------
# load_input
# ---------------------------------------------------------------------------
def load_input(path: Path) -> InputFile:
    """Read one flow-metrics JSON and return a validated :class:`InputFile`.

    Raises :class:`ValidationError` (exit 2) on any spec violation:
    unreadable file, invalid JSON, missing required meta key, malformed
    window, unparseable schema_version, or unrecognised scope shape.
    Every message names the file basename.
    """
    p = Path(path)
    basename = p.name

    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ValidationError(
            "{}: cannot read input file: {}".format(basename, e)
        ) from e

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError(
            "{}: invalid JSON: {}".format(basename, e)
        ) from e

    if not isinstance(doc, dict):
        raise ValidationError(
            "{}: top-level JSON must be an object; got {}".format(
                basename, type(doc).__name__
            )
        )

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        raise ValidationError(
            "{}: meta block missing or not an object".format(basename)
        )

    for key in REQUIRED_META_KEYS:
        if key not in meta:
            raise ValidationError(
                "{}: meta.{} is required but missing".format(basename, key)
            )

    schema_version = _parse_schema_version(meta["schema_version"], basename=basename)
    window_from, window_to = _parse_window(meta["window"], basename=basename)
    scope = meta["scope"]
    scope_kind = infer_scope_kind(scope, basename=basename)

    aggregates = doc.get("aggregates", {})
    if not isinstance(aggregates, dict):
        raise ValidationError(
            "{}: aggregates must be an object; got {}".format(
                basename, type(aggregates).__name__
            )
        )

    cohort_breakdown = doc.get("cohort_breakdown")
    if cohort_breakdown is not None and not isinstance(cohort_breakdown, dict):
        raise ValidationError(
            "{}: cohort_breakdown must be an object when present; got {}".format(
                basename, type(cohort_breakdown).__name__
            )
        )

    per_team = doc.get("per_team")
    if per_team is not None and not isinstance(per_team, list):
        raise ValidationError(
            "{}: per_team must be an array when present; got {}".format(
                basename, type(per_team).__name__
            )
        )

    # flow-metrics emits ``notes`` at the top level (see
    # flow_metrics.notes.NotesCollector + the fixture in
    # tests/fixtures/proj_alpha/golden.json). The plan §T2 description
    # mentions ``meta.notes``; we read both for forward-compat with no
    # source of truth conflict (only one is present in practice).
    upstream_notes = _coerce_notes_list(
        doc.get("notes", meta.get("notes", [])), basename=basename
    )

    return InputFile(
        path=p,
        basename=basename,
        scope=scope,
        scope_kind=scope_kind,
        window_from=window_from,
        window_to=window_to,
        meta=meta,
        aggregates=aggregates,
        cohort_breakdown=cohort_breakdown,
        per_team=per_team,
        schema_version=schema_version,
        notes_from_upstream=upstream_notes,
    )


def _parse_schema_version(value: Any, *, basename: str) -> Tuple[int, int]:
    """Parse ``meta.schema_version`` as ``(major, minor)``.

    Anything that isn't a string matching ``<digits>.<digits>`` exits 2.
    ``1`` (no minor), ``1.0.0`` (three parts), ``v1.0`` (prefix), and
    integer / float values all fail this check.
    """
    if not isinstance(value, str):
        raise ValidationError(
            "{}: meta.schema_version must be a string of the form "
            "'<int>.<int>'; got {}".format(basename, type(value).__name__)
        )
    m = _SCHEMA_VERSION_RE.match(value)
    if not m:
        raise ValidationError(
            "{}: meta.schema_version '{}' is not of the form '<int>.<int>'".format(
                basename, value
            )
        )
    return int(m.group(1)), int(m.group(2))


def _parse_window(window: Any, *, basename: str) -> Tuple[str, str]:
    """Validate ``meta.window`` and return ``(from, to)`` strings verbatim.

    Both endpoints must be ``YYYY-MM-DD`` exactly (regex + calendar
    validity check). String equality is the spec's match rule for
    program-mode window filtering, so the returned strings are NOT
    normalised — round-trip preserves the bytes.
    """
    if not isinstance(window, dict):
        raise ValidationError(
            "{}: meta.window must be an object with 'from' and 'to'; got {}".format(
                basename, type(window).__name__
            )
        )
    for side in ("from", "to"):
        if side not in window:
            raise ValidationError(
                "{}: meta.window.{} is required but missing".format(basename, side)
            )
    out: List[str] = []
    for side in ("from", "to"):
        value = window[side]
        if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
            raise ValidationError(
                "{}: meta.window.{} '{}' is not YYYY-MM-DD "
                "(no time component allowed)".format(basename, side, value)
            )
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValidationError(
                "{}: meta.window.{} '{}' is not a valid calendar date".format(
                    basename, side, value
                )
            )
        out.append(value)
    return out[0], out[1]


def _coerce_notes_list(value: Any, *, basename: str) -> List[str]:
    """Coerce upstream notes into a list of strings.

    Missing or empty is fine. A non-list, or a list with non-string
    entries, exits 2 — the upstream contract is a list of strings.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(
            "{}: notes must be an array of strings when present; got {}".format(
                basename, type(value).__name__
            )
        )
    for i, entry in enumerate(value):
        if not isinstance(entry, str):
            raise ValidationError(
                "{}: notes[{}] must be a string; got {}".format(
                    basename, i, type(entry).__name__
                )
            )
    return list(value)


# ---------------------------------------------------------------------------
# Cross-input helpers
# ---------------------------------------------------------------------------
def collect_mixed_major_note(inputs: Iterable[InputFile]) -> Optional[str]:
    """Return the ``mixed-major-schema-versions`` note, or ``None``.

    Spec lines 114-118: if input files in the same run disagree on the
    major component of ``schema_version``, emit a note listing each
    distinct major and the basenames carrying it. Mixed minors are
    silently allowed. Lives in :mod:`inputs` (not :mod:`notes`) so the
    rule itself is testable in isolation from the wording; the wording
    is delegated to :class:`Note.mixed_major_schema_versions`.
    """
    # Local import to avoid a module-level cycle if Note ever wants to
    # call back into this module (it doesn't today, but keeping the
    # dependency one-directional is cheap).
    from .notes import Note

    pairs: List[Tuple[int, str]] = [
        (inp.schema_version[0], inp.basename) for inp in inputs
    ]
    distinct_majors = {major for major, _ in pairs}
    if len(distinct_majors) < 2:
        return None
    return Note.mixed_major_schema_versions(pairs)


__all__ = [
    "InputFile",
    "REQUIRED_META_KEYS",
    "collect_mixed_major_note",
    "infer_scope_kind",
    "load_input",
]
