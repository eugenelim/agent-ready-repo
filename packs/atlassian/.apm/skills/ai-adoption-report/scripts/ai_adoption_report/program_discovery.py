"""T4 program-mode input discovery.

Globs ``<DIR>/*.json`` (non-recursive), filters by ``--window``, runs
duplicate + cross-kind overlap detection, flattens ``per_team`` arrays
into per-scope rows, and emits the program-mode notes. Every error
names the offending basename(s); every note goes through
:class:`ai_adoption_report.notes.Note`.

Spec references: ``docs/specs/ai-adoption-report.md`` §"Mode: program"
(lines 196-250) and §"Scope shape and ``kind`` inference" (lines
130-146). Plan references: §T4 (lines 239-308).

Stdlib only. Read-only — no subprocess, no writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import ValidationError
from .inputs import InputFile, infer_scope_kind, load_input
from .notes import Note


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class ProgramScope:
    """One row in the program-mode per-scope table.

    Carries enough state for T6 to drive per-metric aggregation without
    re-reading files. ``from_per_team=True`` rows are synthesised from
    a parent input's ``per_team`` array and are excluded from cohort
    rollups (spec lines 232-244).
    """

    scope: dict
    scope_kind: str
    aggregates: dict
    cohort_breakdown: Optional[dict]
    source_basename: str
    from_per_team: bool
    cohort_jql: Optional[str]
    per_team_double_counted: bool


@dataclass
class ProgramInputs:
    """Output of :func:`discover_inputs`.

    ``scopes`` is the post-flattening, post-dedupe, post-overlap-check
    list. ``source_inputs`` is the original :class:`InputFile` set that
    survived the window filter — T7 reads this for the Provenance
    section. ``notes`` is unsorted; T7 sorts and dedupes.
    """

    scopes: List[ProgramScope]
    source_inputs: List[InputFile]
    notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Canonical scope representation (spec lines 510-513).
# ---------------------------------------------------------------------------
_CANONICAL_FIELDS: Tuple[str, ...] = ("project", "team", "program_id", "portfolio_id")


def _double_counted(inp: InputFile) -> bool:
    """Return True iff ``inp.meta.per_team_double_counted`` is the
    boolean True.

    Strict identity check (``is True``) rather than ``bool(...)`` so
    truthy non-bool values (``1``, ``"true"``, non-empty strings) don't
    silently promote to ``True``. JSON's bool literal round-trips to
    Python ``True``/``False`` via :func:`json.loads`, so a flow-metrics
    file that follows the documented shape always satisfies the
    strict check; anything else is upstream sloppiness and shouldn't
    be auto-corrected by the report.
    """
    return inp.meta.get("per_team_double_counted") is True


def canonical_scope_repr(scope: dict, scope_kind: str) -> str:
    """Return the spec-pinned canonical scope string.

    Form: ``kind=<kind>;project=<v>;team=<v>;program_id=<v>;portfolio_id=<v>``
    with absent fields rendered as the empty string after the ``=``
    (spec lines 510-513). Used for:

    - duplicate-scope detection (group key in :func:`discover_inputs`),
    - per-scope row ordering in T7's Markdown / JSON output,
    - the canonical sort key for ``meta.inputs`` per-scope rows.

    The kind is taken as an argument (rather than re-inferred) so this
    function does not depend on :func:`inputs.infer_scope_kind` raising;
    callers pass the kind already on ``InputFile``/``ProgramScope``.
    """
    parts = ["kind={}".format(scope_kind)]
    for fname in _CANONICAL_FIELDS:
        v = scope.get(fname, "")
        parts.append("{}={}".format(fname, "" if v is None else v))
    return ";".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def discover_inputs(
    directory: Path,
    window: Tuple[str, str],
    *,
    include_cohort_breakdown: bool = False,
) -> ProgramInputs:
    """Glob, load, validate, dedupe, overlap-check, and flatten per_team.

    Pipeline (spec §"Mode: program"):

    1. ``directory.glob("*.json")`` — no recursion (spec line 200).
       Results sorted codepoint-ascending for deterministic errors.
    2. ``load_input`` each (T2). Failures exit 2 naming the basename.
    3. Window filter: ``input.window_from == FROM and
       input.window_to == TO`` (string equality; spec lines 204-208).
    4. Empty result → ValidationError (spec line 207).
    5. Pre-flatten duplicate-scope check (spec lines 222-225).
    6. Pre-flatten cross-kind overlap check (spec lines 214-228).
    7. Build one ProgramScope per surviving input.
    8. Per-team flattening (spec lines 232-244).
    9. Post-flatten duplicate-scope safeguard (plan lines 287-301).
    10. Emit notes (per_team-double-counted, per_team-cohort-deferred).

    ``window`` is the tuple returned by T1's ``parse_window_flag``.

    ``include_cohort_breakdown`` controls the
    ``per_team-cohort-deferred`` note only; T4 has no other use for it.
    """
    candidates = sorted(directory.glob("*.json"), key=lambda p: p.name)

    loaded: List[InputFile] = [load_input(p) for p in candidates]

    from_endpoint, to_endpoint = window
    matching: List[InputFile] = [
        inp
        for inp in loaded
        if inp.window_from == from_endpoint and inp.window_to == to_endpoint
    ]
    if not matching:
        raise ValidationError(
            "no inputs matched --window {}..{} in {}".format(
                from_endpoint, to_endpoint, directory
            )
        )

    _check_duplicates_preflatten(matching)
    _check_overlaps(matching)

    program_scopes: List[ProgramScope] = []
    for inp in matching:
        program_scopes.append(
            ProgramScope(
                scope=inp.scope,
                scope_kind=inp.scope_kind,
                aggregates=inp.aggregates,
                cohort_breakdown=inp.cohort_breakdown,
                source_basename=inp.basename,
                from_per_team=False,
                cohort_jql=inp.meta.get("cohort_jql"),
                per_team_double_counted=_double_counted(inp),
            )
        )

    flattened = _flatten_per_team(matching)
    combined = program_scopes + flattened

    _check_duplicates_postflatten(combined)

    notes: List[str] = []

    # Spec lines 246-250: only inputs that actually flattened (per_team
    # non-empty) AND carry per_team_double_counted=true contribute to
    # the note. An input with the flag set but no per_team produced no
    # flattened rows, so the "may double-count" warning would be
    # misleading. Spec phrasing "in any flattened input" pins this.
    double_counted_basenames = [
        inp.basename for inp in matching if _double_counted(inp) and inp.per_team
    ]
    if double_counted_basenames:
        notes.append(Note.per_team_double_counted(double_counted_basenames))

    if include_cohort_breakdown:
        n_flattened = sum(1 for s in combined if s.from_per_team)
        if n_flattened > 0:
            notes.append(Note.per_team_cohort_deferred(n_flattened))

    return ProgramInputs(scopes=combined, source_inputs=matching, notes=notes)


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
def _check_duplicates_preflatten(inputs: List[InputFile]) -> None:
    """Spec lines 222-225: across the window-filtered set, two inputs
    sharing the same ``(scope_kind, canonical_scope_repr)`` exit 2 with
    both basenames named. If more than two duplicates, all basenames
    are listed in codepoint-ascending order.
    """
    groups: Dict[str, List[Tuple[InputFile, bool]]] = {}
    for inp in inputs:
        key = canonical_scope_repr(inp.scope, inp.scope_kind)
        groups.setdefault(key, []).append((inp, False))
    for key, entries in groups.items():
        if len(entries) > 1:
            raise ValidationError(
                Note.duplicate_scope(
                    entries[0][0].scope,
                    [(inp.basename, False) for inp, _ in entries],
                )
            )


def _check_duplicates_postflatten(scopes: List[ProgramScope]) -> None:
    """Plan lines 287-301: re-run duplicate detection on the combined
    list after per_team flattening so a flattened row colliding with an
    explicit ``project+team`` input still raises (otherwise the
    spec's "never silently collapse" intent at line 224 becomes
    asymmetric — pre-existing duplicates raise but flattening-induced
    duplicates double-count).

    Reports both basenames; the per_team-flattened source is annotated
    in the message so the user can tell which side to fix.
    """
    groups: Dict[str, List[ProgramScope]] = {}
    for sc in scopes:
        key = canonical_scope_repr(sc.scope, sc.scope_kind)
        groups.setdefault(key, []).append(sc)
    for key, entries in groups.items():
        if len(entries) > 1:
            raise ValidationError(
                Note.duplicate_scope(
                    entries[0].scope,
                    [(sc.source_basename, sc.from_per_team) for sc in entries],
                )
            )


# ---------------------------------------------------------------------------
# Overlap detection
# ---------------------------------------------------------------------------
# Map every kind (spec-pinned and synthesised) to its parent family for
# overlap purposes. The synthesised ``*+team`` kinds collapse to their
# parent family so the spec rules apply consistently regardless of
# argument order — without this collapse, ``portfolio`` vs
# ``portfolio+team`` would be order-dependent (rank-equal pair) and
# silently miss real overlaps when a user writes an explicit
# ``program+team`` / ``portfolio+team`` flow-metrics file.
_PARENT_KIND: Dict[str, str] = {
    "portfolio": "portfolio",
    "portfolio+team": "portfolio",
    "program": "program",
    "program+team": "program",
    "project": "project",
    "project+team": "project",
}

# Parent-identifier field name per family. Used for the within-family
# (parent vs parent+team) declared-identifier match.
_PARENT_ID_FIELD: Dict[str, str] = {
    "portfolio": "portfolio_id",
    "program": "program_id",
    "project": "project",
}


def _overlaps(
    scope_a: dict,
    kind_a: str,
    scope_b: dict,
    kind_b: str,
) -> bool:
    """Return True if two scopes overlap per spec lines 214-228.

    Order-insensitive. Same-kind pairs are handled by duplicate
    detection upstream — this function returns ``False`` for them. The
    spec-pinned rules:

    - ``portfolio`` family vs any other family → overlap (spec line 218).
    - ``program`` family vs ``project`` family → overlap (spec line 219).
    - Within the same family, base vs ``+team`` overlaps iff the parent
      identifier matches (spec lines 220-221 for ``project`` vs
      ``project+team``; T4 extends the same rule to ``portfolio`` and
      ``program`` so explicit ``+team`` inputs of any family Just Work).
    - Same-kind same-identifier is the duplicate path; same-kind
      different-identifier is no overlap.

    The spec does NOT resolve Jira hierarchy beyond declared scope
    fields (spec line 229). The synthesised ``portfolio+team`` /
    ``program+team`` kinds inherit their parent's cross-family rules:
    portfolio+team overlaps any non-portfolio kind (because the parent
    portfolio would), program+team overlaps project family (because
    program would). This is conservative — it never under-reports
    overlaps.
    """
    if kind_a == kind_b:
        return False

    parent_a = _PARENT_KIND[kind_a]
    parent_b = _PARENT_KIND[kind_b]

    if parent_a != parent_b:
        # Cross-family: spec-pinned rules.
        if "portfolio" in (parent_a, parent_b):
            return True
        if {"program", "project"} == {parent_a, parent_b}:
            return True
        return False

    # Same family, different kind (one base, one +team). Overlap iff
    # the parent identifier matches.
    id_field = _PARENT_ID_FIELD[parent_a]
    return scope_a.get(id_field) == scope_b.get(id_field)


def _check_overlaps(inputs: List[InputFile]) -> None:
    """Pairwise overlap check across the filtered set.

    The set is bounded (a program lead's directory of flow-metrics
    JSONs), so O(N^2) is fine and easier to read than a tree.
    """
    pairs: List[Tuple[Tuple[dict, str], Tuple[dict, str]]] = []
    n = len(inputs)
    for i in range(n):
        for j in range(i + 1, n):
            a = inputs[i]
            b = inputs[j]
            if _overlaps(a.scope, a.scope_kind, b.scope, b.scope_kind):
                pairs.append(((a.scope, a.basename), (b.scope, b.basename)))
    if pairs:
        raise ValidationError(Note.overlapping_scopes(pairs))


# ---------------------------------------------------------------------------
# per_team flattening (spec lines 232-244)
# ---------------------------------------------------------------------------
def _flatten_per_team(inputs: List[InputFile]) -> List[ProgramScope]:
    """Synthesise per-team rows for every input carrying a non-empty
    ``per_team`` array.

    The source input remains in :class:`ProgramInputs.scopes`; it is
    not replaced by its flattened children. Spec lines 232-238 read as
    "both participate in the non-cohort aggregation table", and the
    plan §T4 lists the original-plus-children pattern as the expected
    behaviour. Flagged for spec amendment if reviewers disagree.

    For each ``per_team`` entry:

    - ``team`` is required; missing → ValidationError naming the
      source basename and the entry index. The spec doesn't pin this
      either; flagged.
    - The synthesised scope carries ``project`` / ``program_id`` /
      ``portfolio_id`` from the source if present, plus ``team`` from
      the entry. ``infer_scope_kind`` then re-classifies — typically
      ``project+team`` for a project-scope source, ``program+team``
      for a program-scope source, ``portfolio+team`` for a portfolio
      source.
    - ``aggregates`` is the entry's own ``aggregates`` block.
    - ``cohort_breakdown`` is ``None`` (spec lines 240-244 —
      ``flow-metrics`` v1 doesn't split per_team rows by cohort).
    - ``cohort_jql`` is ``None`` (same reason).
    - ``per_team_double_counted`` propagates from the source input's
      ``meta.per_team_double_counted``.
    """
    out: List[ProgramScope] = []
    for inp in inputs:
        if not inp.per_team:
            continue
        double_counted = _double_counted(inp)
        for idx, entry in enumerate(inp.per_team):
            if not isinstance(entry, dict):
                raise ValidationError(
                    "{}: per_team[{}] must be an object; got {}".format(
                        inp.basename, idx, type(entry).__name__
                    )
                )
            team = entry.get("team")
            if not isinstance(team, str) or not team:
                raise ValidationError(
                    "{}: per_team[{}] missing or empty 'team' field; "
                    "cannot synthesise per-team scope".format(inp.basename, idx)
                )
            entry_aggs = entry.get("aggregates", {})
            if not isinstance(entry_aggs, dict):
                raise ValidationError(
                    "{}: per_team[{}].aggregates must be an object; got {}".format(
                        inp.basename, idx, type(entry_aggs).__name__
                    )
                )

            synth_scope: dict = {}
            for key in ("project", "program_id", "portfolio_id"):
                if key in inp.scope:
                    synth_scope[key] = inp.scope[key]
            synth_scope["team"] = team

            synth_kind = infer_scope_kind(synth_scope, basename=inp.basename)

            out.append(
                ProgramScope(
                    scope=synth_scope,
                    scope_kind=synth_kind,
                    aggregates=entry_aggs,
                    cohort_breakdown=None,
                    source_basename=inp.basename,
                    from_per_team=True,
                    cohort_jql=None,
                    per_team_double_counted=double_counted,
                )
            )
    return out


__all__ = [
    "ProgramInputs",
    "ProgramScope",
    "canonical_scope_repr",
    "discover_inputs",
]
