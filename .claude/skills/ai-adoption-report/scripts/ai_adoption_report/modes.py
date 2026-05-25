"""T3 file-consumer modes: ``baseline`` and ``cohort``.

Both modes load one or two flow-metrics JSONs via T2's
:func:`inputs.load_input`, run T5's :func:`delta.compute_deltas` on the
relevant aggregate pair, and return a :class:`ReportData` for T7 to
render. ``program`` mode (T4/T6) populates the same dataclass with
:attr:`ReportData.per_scope_rows`; the field is ``None`` for baseline
and cohort.

Notes-merge contract (plan §T5 lines 355-362): T5 returns its notes
unsorted; T3 concatenates them onto :attr:`ReportData.notes` in append
order. T7 sorts and dedupes the final list — T3 does NOT pre-sort.

All exit-2 conditions raise :class:`ValidationError`; the CLI entry
point in :mod:`ai_adoption_report` catches and prints them.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from datetime import date
from pathlib import Path

from . import ValidationError
from .aggregation import aggregate_cohort_side, aggregate_non_cohort
from .delta import compute_deltas
from .inputs import InputFile, load_input, collect_mixed_major_note
from .notes import Note
from .program_discovery import canonical_scope_repr as _program_scope_repr
from .program_discovery import discover_inputs


# ---------------------------------------------------------------------------
# Canonical scope representation (spec lines 510-515)
# ---------------------------------------------------------------------------
# Temporary home — T7 may relocate when it owns the renderer. Kept here
# because both header-line assembly (T3) and per-scope-row labels (T6)
# need the same string and the spec defines it once.
_SCOPE_FIELDS = ("project", "team", "program_id", "portfolio_id")


def canonical_scope_repr(scope: dict, kind: str) -> str:
    """Render the spec's canonical scope string.

    Form: ``kind=<kind>;project=<v>;team=<v>;program_id=<v>;portfolio_id=<v>``.
    Absent fields render as the empty string after the ``=``. The field
    order is fixed by the spec and does NOT follow the input dict's
    insertion order.
    """
    parts = ["kind={}".format(kind)]
    for f in _SCOPE_FIELDS:
        parts.append("{}={}".format(f, scope.get(f, "")))
    return ";".join(parts)


# ---------------------------------------------------------------------------
# ReportData
# ---------------------------------------------------------------------------
@dataclass
class ReportData:
    """The mode-agnostic data bundle T7 renders.

    ``deltas`` and ``cohort_deltas`` carry the
    :meth:`delta.DeltaResult.to_dict` shape (the canonical
    insertion-order metric dict that the JSON sidecar emits). T3 calls
    ``to_dict`` so T7 sees the same structure regardless of mode.

    ``per_scope_rows`` stays ``None`` for baseline + cohort; T4/T6
    populates it for program mode.

    ``notes`` is the merged unsorted list (T2's mixed-major note +
    T3's drift / per_team / cohort-jql notes + T5's compute_deltas
    notes). T7 sorts and dedupes the final list per spec line 504.
    """

    mode: Literal["baseline", "cohort", "program"]
    header_line: str
    inputs: List[InputFile]
    deltas: dict
    cohort_deltas: Optional[dict] = None
    per_scope_rows: Optional[list] = None
    program_aggregates: Optional[dict] = None
    notes: List[str] = field(default_factory=list)
    # Side labels for ``cohort_deltas`` cells. Carries the
    # ``(a_label, b_label)`` tuple that the originating ``compute_deltas``
    # call used so T7 can label the Cohort breakdown table columns
    # accurately (baseline+cohort uses ``("baseline-cohort",
    # "current-cohort")``; program mode uses ``("control", "cohort")``).
    # ``None`` whenever ``cohort_deltas`` is ``None``.
    cohort_side_labels: Optional[tuple] = None


# ---------------------------------------------------------------------------
# Mode: baseline
# ---------------------------------------------------------------------------
def run_baseline(args) -> ReportData:
    """Run baseline mode end-to-end and return :class:`ReportData`.

    ``args`` is the argparse namespace from the ``baseline`` subparser.
    Expects ``args.baseline``, ``args.current``, and
    ``args.include_cohort_breakdown``.
    """
    baseline = load_input(args.baseline)
    current = load_input(args.current)
    inputs = [baseline, current]
    notes: List[str] = []

    # T2 cross-input note (mixed schema majors). Same call pattern T4
    # will use in program mode, kept here for the baseline pair so the
    # warning surfaces in single-pair runs too.
    mixed_major = collect_mixed_major_note(inputs)
    if mixed_major is not None:
        notes.append(mixed_major)

    # Spec lines 153-156: exact dict equality on meta.scope.
    if baseline.scope != current.scope:
        raise ValidationError(
            "baseline-mode scope mismatch: baseline scope {} vs current "
            "scope {}".format(baseline.scope, current.scope)
        )

    # Spec lines 157-160: baseline.window.to <= current.window.from.
    # ISO YYYY-MM-DD strings compare correctly under lex order
    # (spec line 127 — string equality is the official match rule).
    if baseline.window_to > current.window_from:
        raise ValidationError(
            "baseline-mode window overlap: baseline {}..{} overlaps "
            "current {}..{}".format(
                baseline.window_from, baseline.window_to,
                current.window_from, current.window_to,
            )
        )

    # Spec lines 161-165: drift emits a note; deltas still compute.
    if baseline.meta.get("state_config_sha") != current.meta.get("state_config_sha"):
        notes.append(
            Note.config_sha_drift(
                "state_config_sha",
                baseline.meta.get("state_config_sha"),
                current.meta.get("state_config_sha"),
            )
        )
    if baseline.meta.get("issuetype_config_sha") != current.meta.get("issuetype_config_sha"):
        notes.append(
            Note.config_sha_drift(
                "issuetype_config_sha",
                baseline.meta.get("issuetype_config_sha"),
                current.meta.get("issuetype_config_sha"),
            )
        )

    # Spec lines 177-183: per_team is ignored in baseline mode; note
    # per input that carries one. ``per_team`` arrives as a list (or
    # None); only non-empty lists trigger the note.
    for inp in inputs:
        if inp.per_team:
            notes.append(Note.per_team_ignored_in_baseline(inp.basename))

    # Primary deltas (spec §"Delta math"). T5 returns notes unsorted;
    # T3 concatenates per the notes-merge contract.
    primary = compute_deltas(
        baseline.aggregates,
        current.aggregates,
        side_labels=("baseline", "current"),
    )
    notes.extend(primary.notes)

    cohort_deltas: Optional[dict] = None
    cohort_side_labels: Optional[tuple] = None
    if getattr(args, "include_cohort_breakdown", False):
        cohort_deltas, cohort_notes = _baseline_cohort_section(baseline, current)
        notes.extend(cohort_notes)
        if cohort_deltas is not None:
            # See :func:`_baseline_cohort_section`: compares
            # ``baseline.cohort_breakdown.cohort`` vs
            # ``current.cohort_breakdown.cohort`` (cohort sub-side moved
            # across the two windows).
            cohort_side_labels = ("baseline-cohort", "current-cohort")

    header_line = (
        "**Baseline window:** {bf}..{bt} | "
        "**Current window:** {cf}..{ct} | "
        "**Scope:** {scope}"
    ).format(
        bf=baseline.window_from,
        bt=baseline.window_to,
        cf=current.window_from,
        ct=current.window_to,
        scope=canonical_scope_repr(baseline.scope, baseline.scope_kind),
    )

    return ReportData(
        mode="baseline",
        header_line=header_line,
        inputs=inputs,
        deltas=primary.to_dict(),
        cohort_deltas=cohort_deltas,
        cohort_side_labels=cohort_side_labels,
        per_scope_rows=None,
        notes=notes,
    )


def _baseline_cohort_section(
    baseline: InputFile,
    current: InputFile,
) -> tuple[Optional[dict], List[str]]:
    """Return ``(cohort_deltas, notes)`` for the optional cohort section.

    Three branches per spec lines 167-175:
    1. Either input lacks ``cohort_breakdown`` → no-op + note,
       ``cohort_deltas`` stays ``None``.
    2. Both present but ``meta.cohort_jql`` differs → section omitted,
       mismatch note, ``cohort_deltas`` stays ``None``.
    3. Both present and JQLs match → compute deltas across the
       cohort/control pair across the two windows (NOT within-window).
    """
    notes: List[str] = []
    missing_basenames = [
        inp.basename for inp in (baseline, current) if inp.cohort_breakdown is None
    ]
    if missing_basenames:
        notes.append(Note.cohort_breakdown_absent_noop(missing_basenames))
        return None, notes

    a_jql = baseline.meta.get("cohort_jql")
    b_jql = current.meta.get("cohort_jql")
    if a_jql != b_jql:
        notes.append(Note.cohort_jql_mismatch(a_jql, b_jql))
        return None, notes

    # The spec is silent on which sub-side gets compared across windows
    # in baseline mode. The natural reading of "cohort-vs-control deltas
    # across the two windows" is: compare the cohort side at baseline
    # vs the cohort side at current (and likewise for control). Our T5
    # engine handles one pair at a time; the section here compares
    # ``baseline.cohort`` vs ``current.cohort`` because that's the
    # quantity a baseline reader asks about ("did AI adoption move the
    # cohort?"). T7 may add a second sub-table for control later;
    # extending requires only another compute_deltas call.
    result = compute_deltas(
        baseline.cohort_breakdown.get("cohort", {}),
        current.cohort_breakdown.get("cohort", {}),
        side_labels=("baseline-cohort", "current-cohort"),
    )
    notes.extend(result.notes)
    return result.to_dict(), notes


# ---------------------------------------------------------------------------
# Mode: cohort
# ---------------------------------------------------------------------------
def run_cohort(args) -> ReportData:
    """Run cohort mode end-to-end and return :class:`ReportData`.

    Side A is ``control`` and side B is ``cohort`` per spec line 194
    and plan §T3 line 230.
    """
    inp = load_input(args.input)

    if inp.cohort_breakdown is None:
        # Spec line 191: literal error string.
        raise ValidationError(
            "--input was not produced with --cohort-jql; no "
            "cohort_breakdown block present"
        )

    notes: List[str] = []
    result = compute_deltas(
        inp.cohort_breakdown.get("control", {}),
        inp.cohort_breakdown.get("cohort", {}),
        side_labels=("control", "cohort"),
    )
    notes.extend(result.notes)

    header_line = (
        "**Window:** {f}..{t} | **Scope:** {scope} | **Cohort JQL:** {jql}"
    ).format(
        f=inp.window_from,
        t=inp.window_to,
        scope=canonical_scope_repr(inp.scope, inp.scope_kind),
        jql=inp.meta.get("cohort_jql", ""),
    )

    return ReportData(
        mode="cohort",
        header_line=header_line,
        inputs=[inp],
        deltas=result.to_dict(),
        cohort_deltas=None,
        per_scope_rows=None,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Mode: program (T4 + T6)
# ---------------------------------------------------------------------------
def run_program(args) -> ReportData:
    """Run program mode end-to-end and return :class:`ReportData`.

    ``args`` is the argparse namespace from the ``program`` subparser.
    Expects ``args.inputs`` (directory), ``args.window`` (the
    ``(from, to)`` tuple from :func:`parse_window_flag`), and
    ``args.include_cohort_breakdown``.

    Pipeline:

    1. T4: ``discover_inputs`` — glob, validate, dedupe, overlap-check,
       per_team flatten.
    2. T6: ``aggregate_non_cohort`` — program-wide aggregates.
    3. T6: ``aggregate_cohort_side`` (twice) when
       ``--include-cohort-breakdown`` — cohort and control side
       rollups, computed independently per spec lines 252-311.
    4. T5: ``compute_deltas`` ONCE — only for the cohort-vs-control
       rollup comparison. Program mode's main table is per-scope rows
       + aggregate row, NOT a two-side comparison, so the global
       ``deltas`` block stays empty.
    5. Mixed-cohort-jql note: emitted when contributing cohort-rollup
       scopes carry distinct ``meta.cohort_jql`` values.
    6. Per-scope rows: every scope in :attr:`ProgramInputs.scopes`,
       sorted by canonical scope-repr per spec lines 510-513.
    7. Header line: spec line 439. Kind counting is family-collapsed —
       ``project+team`` counts as ``project``, ``program+team`` as
       ``program``, ``portfolio+team`` as ``portfolio``. The spec does
       not pin this rule; flagged for amendment.
    """
    from_endpoint, to_endpoint = args.window
    program_inputs = discover_inputs(
        Path(args.inputs),
        args.window,
        include_cohort_breakdown=getattr(args, "include_cohort_breakdown", False),
    )

    notes: List[str] = list(program_inputs.notes)

    global_agg, non_cohort_notes = aggregate_non_cohort(program_inputs.scopes)
    notes.extend(non_cohort_notes)

    # Spec line 373: throughput is reported as a raw count AND as a
    # per-week rate. The non-cohort aggregate is the only place this
    # is computed; cohort-side rollups don't carry a window-normalised
    # variant (T7's renderer can compute one if it wants).
    if "throughput" in global_agg:
        try:
            d_from = date.fromisoformat(from_endpoint)
            d_to = date.fromisoformat(to_endpoint)
            inclusive_days = (d_to - d_from).days + 1
            weeks = inclusive_days / 7
            if weeks > 0:
                global_agg["throughput_per_week"] = (
                    global_agg["throughput"] / weeks
                )
        except ValueError:
            # Window strings passed validate_args/parse_window_flag, so
            # this can only fire if a caller constructed a malformed
            # args namespace. Skip the normalisation rather than mask
            # the upstream bug.
            pass

    cohort_deltas: Optional[dict] = None
    cohort_side_labels: Optional[tuple] = None
    if getattr(args, "include_cohort_breakdown", False):
        cohort_agg, cohort_notes = aggregate_cohort_side(
            program_inputs.scopes, "cohort"
        )
        control_agg, control_notes = aggregate_cohort_side(
            program_inputs.scopes, "control"
        )
        notes.extend(cohort_notes)
        notes.extend(control_notes)

        if cohort_agg is not None and control_agg is not None:
            # Spec lines 305-308: collect cohort_jql across the scopes
            # that actually contribute (non-per_team, have
            # cohort_breakdown). Emit the mixed-cohort-jql note when
            # >1 distinct value.
            jql_groups: dict = {}
            for s in program_inputs.scopes:
                if s.from_per_team or s.cohort_breakdown is None:
                    continue
                jql_groups.setdefault(s.cohort_jql, []).append(s.source_basename)
            if len(jql_groups) > 1:
                notes.append(
                    Note.mixed_cohort_jql(
                        [(str(jql), basenames) for jql, basenames in jql_groups.items()]
                    )
                )

            delta_result = compute_deltas(
                control_agg, cohort_agg, side_labels=("control", "cohort")
            )
            notes.extend(delta_result.notes)
            cohort_deltas = delta_result.to_dict()
            cohort_side_labels = ("control", "cohort")

    # Per-scope rows: canonical sort by scope-repr (spec lines 506-507).
    sorted_scopes = sorted(
        program_inputs.scopes,
        key=lambda s: _program_scope_repr(s.scope, s.scope_kind),
    )
    per_scope_rows = [
        {
            "scope": s.scope,
            "scope_kind": s.scope_kind,
            "scope_repr": _program_scope_repr(s.scope, s.scope_kind),
            "aggregates": s.aggregates,
        }
        for s in sorted_scopes
    ]

    # Header line (spec line 439). Kind counts collapse ``+team`` into
    # the parent family — flagged in the task report.
    kind_counts = {"project": 0, "program": 0, "portfolio": 0}
    for s in program_inputs.scopes:
        family = s.scope_kind.split("+", 1)[0]
        if family in kind_counts:
            kind_counts[family] += 1
    header_line = (
        "**Window:** {f}..{t} | **Scopes:** {n} "
        "(project={p}, program={pg}, portfolio={pf})"
    ).format(
        f=from_endpoint,
        t=to_endpoint,
        n=len(program_inputs.scopes),
        p=kind_counts["project"],
        pg=kind_counts["program"],
        pf=kind_counts["portfolio"],
    )

    return ReportData(
        mode="program",
        header_line=header_line,
        inputs=program_inputs.source_inputs,
        deltas={},
        cohort_deltas=cohort_deltas,
        cohort_side_labels=cohort_side_labels,
        per_scope_rows=per_scope_rows,
        program_aggregates=global_agg,
        notes=notes,
    )


__all__ = [
    "ReportData",
    "canonical_scope_repr",
    "run_baseline",
    "run_cohort",
    "run_program",
]
