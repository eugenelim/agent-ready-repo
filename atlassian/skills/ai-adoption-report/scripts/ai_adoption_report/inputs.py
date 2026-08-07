"""Input file loader.

Reads one flow-metrics JSON, validates the ``meta`` block, infers the
scope ``kind`` from key presence, and returns an :class:`InputFile`
dataclass that the three mode-runners (modes, program discovery) consume.

Validation rules for input file validation are enforced here. Every
error message names the file basename; the basename is the only
locator the user reliably recognises across the program-mode glob and
the single-file modes.

Stdlib only. Read-only — no subprocess, no writes.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from . import ValidationError

# Required meta keys. Order matches the documented input contract.
REQUIRED_META_KEYS: tuple[str, ...] = (
    "scope",
    "window",
    "state_config_sha",
    "issuetype_config_sha",
    "schema_version",
    "generated_at",
)

# Window dates must be YYYY-MM-DD only — no time component, no timezone.
# ``date.fromisoformat`` accepts ``2026-02-19T00:00:00`` on newer Pythons,
# so the regex is the first gate; ``date.fromisoformat`` then validates
# that the YYYY/MM/DD parts form a real calendar date.
_ISO_DATE_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")

# schema_version must be ``<int>.<int>``. Anything else exits 2.
# Trailing ``.0`` is fine (still two parts); ``1.0.0`` is not.
_SCHEMA_VERSION_RE = re.compile(r"\A(\d+)\.(\d+)\Z")


@dataclass
class InputFile:
    """One validated flow-metrics JSON file.

    Fields mirror the validated-input dataclass shape. Raw
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
    cohort_breakdown: dict | None
    per_team: list | None
    schema_version: tuple[int, int]
    notes_from_upstream: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scope-kind inference.
# ---------------------------------------------------------------------------
def infer_scope_kind(scope: dict, *, basename: str) -> str:
    """Return one of the six recognised scope kinds.

    Recognised kinds:
    ``portfolio`` / ``program`` / ``project`` / ``project+team``.

    Synthesized-only kinds (introduced when program discovery
    (program_discovery.py) flattens the per_team array of a program- or
    portfolio-scope input; flagged for spec amendment):
    ``program+team`` / ``portfolio+team``. These are not produced by
    `flow-metrics` directly — they only arise when program discovery
    synthesises a scope dict by carrying forward the source input's
    ``program_id`` / ``portfolio_id`` and attaching a ``team`` value
    from a ``per_team`` entry. Accepting them here keeps inference in
    one place; the alternative (a special-case path in program
    discovery) was rejected so that program discovery can re-infer the
    kind on the synthesised dict.

    Anything outside the table raises :class:`ValidationError`.

    ``basename`` is woven into the error message so the user can tell
    which file in a program-mode glob is offending without re-running.
    """
    if not isinstance(scope, dict):
        raise ValidationError(
            f"{basename}: meta.scope must be an object; got {type(scope).__name__}"
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
        f"unrecognised scope shape in {basename}: {scope}"
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
            f"{basename}: cannot read input file: {e}"
        ) from e

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"{basename}: invalid JSON: {e}"
        ) from e

    if not isinstance(doc, dict):
        raise ValidationError(
            f"{basename}: top-level JSON must be an object; got {type(doc).__name__}"
        )

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        raise ValidationError(
            f"{basename}: meta block missing or not an object"
        )

    for key in REQUIRED_META_KEYS:
        if key not in meta:
            raise ValidationError(
                f"{basename}: meta.{key} is required but missing"
            )

    schema_version = _parse_schema_version(meta["schema_version"], basename=basename)
    window_from, window_to = _parse_window(meta["window"], basename=basename)
    scope = meta["scope"]
    scope_kind = infer_scope_kind(scope, basename=basename)

    aggregates = doc.get("aggregates", {})
    if not isinstance(aggregates, dict):
        raise ValidationError(
            f"{basename}: aggregates must be an object; got {type(aggregates).__name__}"
        )

    cohort_breakdown = doc.get("cohort_breakdown")
    if cohort_breakdown is not None and not isinstance(cohort_breakdown, dict):
        raise ValidationError(
            f"{basename}: cohort_breakdown must be an object when present;"
            f" got {type(cohort_breakdown).__name__}"
        )

    per_team = doc.get("per_team")
    if per_team is not None and not isinstance(per_team, list):
        raise ValidationError(
            f"{basename}: per_team must be an array when present; got {type(per_team).__name__}"
        )

    # flow-metrics emits ``notes`` at the top level (see
    # flow_metrics.notes.NotesCollector + the fixture in
    # tests/fixtures/proj_alpha/golden.json). Some inputs may instead
    # carry ``meta.notes``; we read both for forward-compat with no
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


def _parse_schema_version(value: Any, *, basename: str) -> tuple[int, int]:
    """Parse ``meta.schema_version`` as ``(major, minor)``.

    Anything that isn't a string matching ``<digits>.<digits>`` exits 2.
    ``1`` (no minor), ``1.0.0`` (three parts), ``v1.0`` (prefix), and
    integer / float values all fail this check.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{basename}: meta.schema_version must be a string of the form "
            f"'<int>.<int>'; got {type(value).__name__}"
        )
    m = _SCHEMA_VERSION_RE.match(value)
    if not m:
        raise ValidationError(
            f"{basename}: meta.schema_version '{value}' is not of the form '<int>.<int>'"
        )
    return int(m.group(1)), int(m.group(2))


def _parse_window(window: Any, *, basename: str) -> tuple[str, str]:
    """Validate ``meta.window`` and return ``(from, to)`` strings verbatim.

    Both endpoints must be ``YYYY-MM-DD`` exactly (regex + calendar
    validity check). String equality is the spec's match rule for
    program-mode window filtering, so the returned strings are NOT
    normalised — round-trip preserves the bytes.
    """
    if not isinstance(window, dict):
        raise ValidationError(
            f"{basename}: meta.window must be an object with 'from' and 'to';"
            f" got {type(window).__name__}"
        )
    for side in ("from", "to"):
        if side not in window:
            raise ValidationError(
                f"{basename}: meta.window.{side} is required but missing"
            )
    out: list[str] = []
    for side in ("from", "to"):
        value = window[side]
        if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
            raise ValidationError(
                f"{basename}: meta.window.{side} '{value}' is not YYYY-MM-DD "
                "(no time component allowed)"
            )
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError(
                f"{basename}: meta.window.{side} '{value}' is not a valid calendar date"
            ) from exc
        out.append(value)
    return out[0], out[1]


def _coerce_notes_list(value: Any, *, basename: str) -> list[str]:
    """Coerce upstream notes into a list of strings.

    Missing or empty is fine. A non-list, or a list with non-string
    entries, exits 2 — the upstream contract is a list of strings.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(
            f"{basename}: notes must be an array of strings when present;"
            f" got {type(value).__name__}"
        )
    for i, entry in enumerate(value):
        if not isinstance(entry, str):
            raise ValidationError(
                f"{basename}: notes[{i}] must be a string; got {type(entry).__name__}"
            )
    return list(value)


# ---------------------------------------------------------------------------
# Cross-input helpers
# ---------------------------------------------------------------------------
def collect_mixed_major_note(inputs: Iterable[InputFile]) -> str | None:
    """Return the ``mixed-major-schema-versions`` note, or ``None``.

    If input files in the same run disagree on the major component of
    ``schema_version``, emit a note listing each distinct major and the
    basenames carrying it. Mixed minors are silently allowed. Lives in
    :mod:`inputs` (not :mod:`notes`) so the rule itself is testable in
    isolation from the wording; the wording is delegated to
    :class:`Note.mixed_major_schema_versions`.
    """
    # Local import to avoid a module-level cycle if Note ever wants to
    # call back into this module (it doesn't today, but keeping the
    # dependency one-directional is cheap).
    from .notes import Note

    pairs: list[tuple[int, str]] = [
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
