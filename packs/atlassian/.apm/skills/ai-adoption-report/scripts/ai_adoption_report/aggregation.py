"""T6 program-mode aggregation engine.

Turns a list of :class:`program_discovery.ProgramScope` into:

- ``aggregates`` — the program-wide non-cohort aggregation (matches
  ``flow-metrics``'s top-level ``aggregates`` block in shape).
- ``cohort_breakdown.<side>`` — per-side cohort rollup (matches
  ``flow-metrics``'s ``cohort_breakdown.<side>`` shape), produced only
  when ``--include-cohort-breakdown`` is set.

Aggregation rules (spec §"Aggregation math (program mode only)" lines
366-384 and §"Mode: program" lines 252-311):

- ``throughput`` / ``wip`` / ``flow_load`` — sum across scopes.
- ``cycle_time_hours`` / ``lead_time_hours`` / ``flow_time_hours`` /
  ``flow_efficiency`` (distribution metrics) — median-of-medians per
  percentile; ``n`` is the sum across contributing scopes.
- ``rework_rate`` — throughput-weighted average. Side's own throughput
  is the weight (cohort uses cohort throughput, control uses control
  throughput, non-cohort uses per-scope ``aggregates.throughput``).
- ``defect_ratio`` — flow_distribution.denominator-weighted average
  (spec lines 273-281 + line 378). NOT throughput-weighted.
- ``flow_distribution.<bucket>`` — denominator-weighted average. The
  aggregated ``flow_distribution.denominator`` is the integer sum
  across contributing scopes.

Insertion order matches :data:`delta.CANONICAL_METRIC_ORDER` so T7's
``CanonicalEncoder`` reads insertion order for the aggregates / cohort
subtrees the way it does for ``deltas``.

Notes are returned in append order — T7 sorts and dedupes the merged
list. T6 does NOT pre-sort.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import statistics
from typing import Dict, List, Literal, Optional, Tuple

from .delta import FLOW_DISTRIBUTION_BUCKETS, PERCENTILES
from .notes import Note
from .program_discovery import ProgramScope


# Top-level keys in the order they appear in the aggregates / cohort
# side dicts T6 produces. Derived from spec §"Metric row order" (lines
# 352-364) collapsed to one entry per top-level metric.
_TOP_LEVEL_METRIC_ORDER: Tuple[str, ...] = (
    "throughput",
    "wip",
    "flow_load",
    "cycle_time_hours",
    "lead_time_hours",
    "flow_time_hours",
    "flow_efficiency",
    "rework_rate",
    "defect_ratio",
    "flow_distribution",
)

_DISTRIBUTION_METRICS: Tuple[str, ...] = (
    "cycle_time_hours",
    "lead_time_hours",
    "flow_time_hours",
    "flow_efficiency",
)


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------
def weighted_sum_and_average(
    values: List[Optional[float]],
    weights: List[float],
) -> Tuple[float, Optional[float]]:
    """Return ``(sum_of_weights, weighted_mean_or_None)``.

    Skips ``(value, weight)`` pairs where ``value`` is ``None`` or
    ``weight`` is ``0`` (defensively also when ``weight`` is ``None`` —
    flow-metrics never emits ``null`` denominators, but treating ``None``
    as a zero weight keeps callers from special-casing). Returns
    ``weighted_mean=None`` when ``sum_of_weights == 0``.

    Lengths must match; mismatched lengths exit ``ValueError`` because
    the caller built the pairs and a divergence is a programming bug.
    """
    if len(values) != len(weights):
        raise ValueError(
            "weighted_sum_and_average: len(values)={} != len(weights)={}".format(
                len(values), len(weights)
            )
        )
    total_w: float = 0
    total_wv: float = 0
    for v, w in zip(values, weights):
        if v is None or w is None or w == 0:
            continue
        total_w += w
        total_wv += w * v
    if total_w == 0:
        return total_w, None
    return total_w, total_wv / total_w


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def aggregate_non_cohort(
    scopes: List[ProgramScope],
) -> Tuple[dict, List[str]]:
    """Return ``(aggregates_dict, notes)`` for the non-cohort rollup.

    Includes every scope (per_team-flattened rows participate in the
    non-cohort aggregation per spec lines 232-244). Side label woven
    into zero-denominator notes is ``"non-cohort"``.

    The returned dict matches the shape of flow-metrics's ``aggregates``
    block: same keys, same nesting. T7 may layer on derived fields
    (e.g. ``throughput_per_week``) at the renderer boundary.
    """
    blocks_with_basenames = [(s.aggregates, s.source_basename) for s in scopes]
    out, _missing_fd, notes = _aggregate_blocks(
        blocks_with_basenames, side_label="non-cohort"
    )
    # One median-of-medians-approximation note per report, anchored on
    # whichever side surfaces distribution metrics first. Non-cohort
    # always carries them (the program mode header table), so this is
    # the canonical emission point.
    if any(m in out for m in _DISTRIBUTION_METRICS):
        notes.append(Note.median_of_medians_approximation())
    return out, notes


def aggregate_cohort_side(
    scopes: List[ProgramScope],
    side: Literal["cohort", "control"],
) -> Tuple[Optional[dict], List[str]]:
    """Return ``(cohort_breakdown_side_dict | None, notes)`` for one side.

    Exclusions per spec lines 252-311:

    - ``from_per_team=True`` scopes are excluded from BOTH cohort and
      control rollups (flow-metrics v1 doesn't split per_team rows by
      cohort; T4 already emits the per_team-cohort-deferred note).
    - Scopes missing ``cohort_breakdown`` are excluded from both sides;
      a ``cohort-breakdown-missing`` note records the basenames.
    - Scopes whose ``cohort_breakdown.<side>.flow_distribution`` is
      missing are dropped from THAT side's defect_ratio and
      flow_distribution rollups only (other side-metrics still include
      them); a ``cohort-flow_distribution-missing`` note records the
      basenames.

    Returns ``(None, notes)`` when zero scopes contribute, and emits a
    ``cohort-breakdown-section-empty`` note. T7 dedupes the duplicate
    emission across the two side calls.
    """
    notes: List[str] = []

    eligible = [s for s in scopes if not s.from_per_team]
    total_m = len(eligible)
    if total_m == 0:
        # No eligible scopes at all (every input was per_team-flattened).
        # The per_team-cohort-deferred note is T4's responsibility; we
        # only need to record the section-empty literal.
        notes.append(Note.cohort_breakdown_section_empty())
        return None, notes

    contributing: List[Tuple[dict, str, ProgramScope]] = []
    missing_cb: List[str] = []
    for s in eligible:
        if s.cohort_breakdown is None:
            missing_cb.append(s.source_basename)
            continue
        side_block = s.cohort_breakdown.get(side)
        if not isinstance(side_block, dict):
            # cohort_breakdown present but this side missing — treat as
            # cohort_breakdown-missing for this side (the symmetric side
            # would still get the scope). flow-metrics emits both sides
            # together, so this branch is defensive.
            missing_cb.append(s.source_basename)
            continue
        contributing.append((side_block, s.source_basename, s))

    if missing_cb:
        notes.append(Note.cohort_breakdown_missing(missing_cb, total_m))

    if not contributing:
        notes.append(Note.cohort_breakdown_section_empty())
        return None, notes

    blocks_with_basenames = [(b, name) for b, name, _ in contributing]
    out, missing_fd, agg_notes = _aggregate_blocks(
        blocks_with_basenames, side_label=side
    )
    notes.extend(agg_notes)

    # Spec lines 381-384: emit the median-of-medians approximation note
    # whenever distribution aggregates are produced. aggregate_non_cohort
    # is the canonical emission point, but firing here too defends
    # against the (contrived) case where the non-cohort table has no
    # distribution metrics yet a cohort side does. T7 dedupes by exact
    # match, so the duplicate emission is free.
    if any(m in out for m in _DISTRIBUTION_METRICS):
        notes.append(Note.median_of_medians_approximation())

    if missing_fd:
        notes.append(
            Note.cohort_flow_distribution_missing(
                side, missing_fd, len(contributing)
            )
        )

    return out, notes


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
def _aggregate_blocks(
    blocks_with_basenames: List[Tuple[dict, str]],
    *,
    side_label: str,
) -> Tuple[Dict[str, object], List[str], List[str]]:
    """Aggregate a list of ``(aggregates-shaped block, basename)`` pairs.

    Generic over non-cohort and cohort-side: the caller passes
    ``scope.aggregates`` for non-cohort and ``scope.cohort_breakdown.<side>``
    for cohort. ``side_label`` is woven into zero-denominator notes
    (``"non-cohort"`` / ``"cohort"`` / ``"control"``).

    Returns ``(aggregate_dict, missing_flow_dist_basenames, notes)``.
    The dict's keys are inserted in :data:`_TOP_LEVEL_METRIC_ORDER` —
    T7's CanonicalEncoder relies on insertion order for the aggregates
    subtree the same way it does for ``deltas``.

    ``missing_flow_dist_basenames`` is the list of basenames whose
    block lacked a ``flow_distribution`` sub-block. The caller decides
    whether that's a notable condition (cohort side: emit a note;
    non-cohort: silently drop because flow-metrics emits flow_distribution
    by default unless ``--metrics`` excluded it).
    """
    notes: List[str] = []
    out: Dict[str, object] = {}

    # ---- 1-3. Simple sums (throughput, wip, flow_load).
    for metric in ("throughput", "wip", "flow_load"):
        vals = [b.get(metric) for b, _ in blocks_with_basenames]
        present = [v for v in vals if v is not None]
        if present:
            out[metric] = sum(present)

    # ---- 4-7. Distribution metrics: median-of-medians per percentile.
    for metric in _DISTRIBUTION_METRICS:
        scope_blocks = [
            b.get(metric)
            for b, _ in blocks_with_basenames
            if isinstance(b.get(metric), dict)
        ]
        if not scope_blocks:
            continue
        result: Dict[str, object] = {}
        for p in PERCENTILES:
            p_vals = [sb.get(p) for sb in scope_blocks if sb.get(p) is not None]
            result[p] = statistics.median(p_vals) if p_vals else None
        n_vals = [sb.get("n") for sb in scope_blocks if sb.get("n") is not None]
        if n_vals:
            result["n"] = sum(n_vals)
        out[metric] = result

    # ---- 8. rework_rate (side-throughput-weighted).
    rew_vals = [b.get("rework_rate") for b, _ in blocks_with_basenames]
    rew_weights: List[float] = []
    for b, _ in blocks_with_basenames:
        w = b.get("throughput")
        rew_weights.append(w if isinstance(w, (int, float)) else 0)
    if any(v is not None for v in rew_vals):
        _, rew_avg = weighted_sum_and_average(rew_vals, rew_weights)
        if rew_avg is None:
            notes.append(
                Note.aggregation_zero_denominator("rework_rate", side_label)
            )
        out["rework_rate"] = rew_avg

    # ---- Collect flow_distribution-side data once (used by both
    # defect_ratio and flow_distribution rollups).
    missing_fd: List[str] = []
    fd_present = False
    denominator_sum = 0
    defect_vals: List[Optional[float]] = []
    defect_weights: List[float] = []
    bucket_vals_by_key: Dict[str, List[Optional[float]]] = {
        bk: [] for bk in FLOW_DISTRIBUTION_BUCKETS
    }
    bucket_weights: List[float] = []

    for block, basename in blocks_with_basenames:
        fd = block.get("flow_distribution")
        if not isinstance(fd, dict):
            missing_fd.append(basename)
            continue
        fd_present = True
        denom = fd.get("denominator")
        if not isinstance(denom, (int, float)):
            denom = 0
        denominator_sum += denom
        defect_vals.append(block.get("defect_ratio"))
        defect_weights.append(denom)
        bucket_weights.append(denom)
        for bucket in FLOW_DISTRIBUTION_BUCKETS:
            bucket_vals_by_key[bucket].append(fd.get(bucket))

    # ---- 9. defect_ratio (denominator-weighted).
    if fd_present and any(v is not None for v in defect_vals):
        _, defect_avg = weighted_sum_and_average(defect_vals, defect_weights)
        if defect_avg is None:
            notes.append(
                Note.aggregation_zero_denominator("defect_ratio", side_label)
            )
        out["defect_ratio"] = defect_avg

    # ---- 10. flow_distribution.<bucket> (denominator-weighted) +
    # denominator (sum).
    if fd_present:
        fd_out: Dict[str, object] = {}
        zero_noted = False
        for bucket in FLOW_DISTRIBUTION_BUCKETS:
            vals = bucket_vals_by_key[bucket]
            if not any(v is not None for v in vals):
                continue
            _, avg = weighted_sum_and_average(vals, bucket_weights)
            fd_out[bucket] = avg
            if avg is None and not zero_noted:
                notes.append(
                    Note.aggregation_zero_denominator(
                        "flow_distribution", side_label
                    )
                )
                zero_noted = True
        fd_out["denominator"] = denominator_sum
        out["flow_distribution"] = fd_out

    return out, missing_fd, notes


__all__ = [
    "aggregate_cohort_side",
    "aggregate_non_cohort",
    "weighted_sum_and_average",
]
