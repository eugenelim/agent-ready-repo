"""T5 delta math engine.

:func:`compute_deltas` consumes two aggregate-shaped dicts (the same
shape ``flow-metrics`` emits in ``aggregates`` or in
``cohort_breakdown.<side>``) and returns a :class:`DeltaResult` carrying
per-metric rows and unsorted notes.

T5 knows nothing about modes. Baseline mode passes two ``aggregates``
blocks; cohort mode and the program cohort rollup pass two
``cohort_breakdown.<side>`` blocks. ``side_labels`` lets the caller
control the wording of any notes (``("baseline", "current")``,
``("control", "cohort")``, etc.).

Notes are returned in append order — T7 sorts and dedupes the final
merged list (see plan §T5 "Notes merge contract"). Do NOT pre-sort.

Percent deltas are decimal fractions, not formatted strings. Rounding
to 4 decimal places is T7's job; T5 emits full precision.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

from .notes import Note


# ---------------------------------------------------------------------------
# Canonical orderings (spec lines 354-364, 332-350)
# ---------------------------------------------------------------------------
CANONICAL_METRIC_ORDER: Tuple[str, ...] = (
    "throughput",
    "wip",
    "flow_load",
    "cycle_time_hours p50",
    "cycle_time_hours p75",
    "cycle_time_hours p90",
    "lead_time_hours p50",
    "lead_time_hours p75",
    "lead_time_hours p90",
    "flow_time_hours p50",
    "flow_time_hours p75",
    "flow_time_hours p90",
    "flow_efficiency p50",
    "flow_efficiency p75",
    "flow_efficiency p90",
    "rework_rate",
    "defect_ratio",
    "flow_distribution.feature",
    "flow_distribution.defect",
    "flow_distribution.debt",
    "flow_distribution.risk",
    "flow_distribution.subtask",
    "flow_distribution.other",
)

PERCENTILES: Tuple[str, ...] = ("p50", "p75", "p90")
FLOW_DISTRIBUTION_BUCKETS: Tuple[str, ...] = (
    "feature",
    "defect",
    "debt",
    "risk",
    "subtask",
    "other",
)

# (metric_name, kind) in canonical metric-iteration order. ``kind`` is
# one of ``"scalar" | "distribution" | "bucket"`` and dispatches to the
# right row-emission / n-rule branch.
_METRIC_DISPATCH: Tuple[Tuple[str, str], ...] = (
    ("throughput", "scalar"),
    ("wip", "scalar"),
    ("flow_load", "scalar"),
    ("cycle_time_hours", "distribution"),
    ("lead_time_hours", "distribution"),
    ("flow_time_hours", "distribution"),
    ("flow_efficiency", "distribution"),
    ("rework_rate", "scalar"),
    ("defect_ratio", "scalar"),
    ("flow_distribution", "bucket"),
)


Number = Union[int, float]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class DeltaRow:
    """One row in the delta table.

    ``metric_label`` is the canonical row label (e.g. ``"throughput"``,
    ``"cycle_time_hours p50"``, ``"flow_distribution.feature"``) and
    matches an entry in :data:`CANONICAL_METRIC_ORDER`.

    ``a`` / ``b`` are the raw per-side values (``None`` when absent or
    null). ``abs_delta`` is ``b - a`` (``None`` when either side is
    ``None``). ``pct_delta`` is the decimal fraction ``(b - a) / a``
    (``math.inf`` / ``-math.inf`` for the zero-baseline case, ``None``
    when undefined). T7 formats both for Markdown.
    """

    metric_label: str
    a: Optional[Number]
    b: Optional[Number]
    abs_delta: Optional[Number]
    pct_delta: Optional[float]


@dataclass
class DeltaResult:
    """Output of :func:`compute_deltas`.

    ``rows`` is in canonical metric row order; metrics absent on BOTH
    sides are omitted entirely.

    ``notes`` is in append order (unsorted). T3 / T6 concatenate this
    onto ``ReportData.notes``; T7 sorts and dedupes the final list.
    """

    rows: List[DeltaRow] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Render the ``deltas`` subtree per spec §"Output: JSON sidecar".

        Scalar metrics map to a flat ``{a, b, abs, pct}`` dict.
        Distribution metrics nest under ``p50`` / ``p75`` / ``p90``
        keys; ``flow_distribution`` nests under bucket keys. Insertion
        order follows :data:`CANONICAL_METRIC_ORDER` because :attr:`rows`
        is already in that order — T7's canonical encoder preserves
        insertion order for the ``deltas`` block (the one intentional
        exception to the global sort-keys rule, spec lines 507-509).
        """
        out: dict = {}
        for row in self.rows:
            cell = {
                "a": row.a,
                "b": row.b,
                "abs": row.abs_delta,
                "pct": row.pct_delta,
            }
            if " " in row.metric_label:
                metric, sub = row.metric_label.split(" ", 1)
                out.setdefault(metric, {})[sub] = cell
            elif "." in row.metric_label:
                metric, sub = row.metric_label.split(".", 1)
                out.setdefault(metric, {})[sub] = cell
            else:
                out[row.metric_label] = cell
        return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def compute_deltas(
    a: Mapping[str, object],
    b: Mapping[str, object],
    *,
    side_labels: Tuple[str, str],
) -> DeltaResult:
    """Compare two aggregate-shaped dicts and emit per-metric deltas.

    ``a`` is the prior / control / baseline side; ``b`` is the
    current / cohort / comparand side. ``side_labels`` is the
    ``(a_label, b_label)`` pair woven into note text — pick labels that
    will read naturally in the final report (e.g. ``("baseline",
    "current")`` for baseline mode, ``("control", "cohort")`` for
    cohort mode).

    See module docstring for the full contract.
    """
    a_label, b_label = side_labels
    result = DeltaResult()

    # Tracks (metric, side_label) tuples that have already produced a
    # null-on-side note so that, e.g., all three percentiles being null
    # on the A side produce ONE note (not three with identical wording).
    null_noted: set = set()

    for metric, kind in _METRIC_DISPATCH:
        a_has = metric in a
        b_has = metric in b
        if not a_has and not b_has:
            continue
        if not (a_has and b_has):
            _emit_absent_side(result, metric, kind, a, b, a_label, b_label)
            continue
        if kind == "scalar":
            _emit_scalar(result, metric, a, b, a_label, b_label, null_noted)
        elif kind == "distribution":
            _emit_distribution(result, metric, a, b, a_label, b_label, null_noted)
        else:  # bucket
            _emit_bucket(result, metric, a, b, a_label, b_label, null_noted)

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _as_mapping(value: object) -> Mapping:
    """Return ``value`` if it's a Mapping, else an empty dict.

    Lets the per-kind emitters call ``.get(sub_key)`` without re-doing
    the isinstance dance for every percentile / bucket. Treats both
    ``None`` and any non-Mapping value as an empty dict; flow-metrics
    always emits a Mapping for distribution / bucket keys, so this is
    a defensive guard rather than a regular code path.
    """
    return value if isinstance(value, Mapping) else {}


# ---------------------------------------------------------------------------
# Per-kind row emitters
# ---------------------------------------------------------------------------
def _emit_absent_side(
    result: DeltaResult,
    metric: str,
    kind: str,
    a: Mapping[str, object],
    b: Mapping[str, object],
    a_label: str,
    b_label: str,
) -> None:
    """Metric missing from exactly one side.

    Emits placeholder rows (``a=None`` or ``b=None`` as appropriate,
    ``abs`` / ``pct`` both ``None``) plus ONE ``metric_absent`` note —
    not one per percentile or bucket. The note's ``<file>`` slot is
    filled with the absent side's label since T5 has no access to
    filenames.
    """
    absent_label = a_label if metric not in a else b_label
    result.notes.append(Note.metric_absent(metric, absent_label))

    if kind == "scalar":
        result.rows.append(
            DeltaRow(
                metric_label=metric,
                a=a.get(metric),
                b=b.get(metric),
                abs_delta=None,
                pct_delta=None,
            )
        )
        return
    if kind == "distribution":
        a_block = _as_mapping(a.get(metric))
        b_block = _as_mapping(b.get(metric))
        for p in PERCENTILES:
            result.rows.append(
                DeltaRow(
                    metric_label="{} {}".format(metric, p),
                    a=a_block.get(p),
                    b=b_block.get(p),
                    abs_delta=None,
                    pct_delta=None,
                )
            )
        return
    # bucket
    a_block = _as_mapping(a.get(metric))
    b_block = _as_mapping(b.get(metric))
    for bucket in FLOW_DISTRIBUTION_BUCKETS:
        result.rows.append(
            DeltaRow(
                metric_label="{}.{}".format(metric, bucket),
                a=a_block.get(bucket),
                b=b_block.get(bucket),
                abs_delta=None,
                pct_delta=None,
            )
        )


def _emit_scalar(
    result: DeltaResult,
    metric: str,
    a: Mapping[str, object],
    b: Mapping[str, object],
    a_label: str,
    b_label: str,
    null_noted: set,
) -> None:
    a_val = a[metric]
    b_val = b[metric]
    _maybe_emit_null_note(result, metric, a_val, b_val, a_label, b_label, null_noted)
    abs_delta, pct_delta = _delta_pair(metric, a_val, b_val, result.notes)
    result.rows.append(
        DeltaRow(
            metric_label=metric,
            a=a_val,
            b=b_val,
            abs_delta=abs_delta,
            pct_delta=pct_delta,
        )
    )


def _emit_distribution(
    result: DeltaResult,
    metric: str,
    a: Mapping[str, object],
    b: Mapping[str, object],
    a_label: str,
    b_label: str,
    null_noted: set,
) -> None:
    a_block = _as_mapping(a[metric])
    b_block = _as_mapping(b[metric])
    for p in PERCENTILES:
        a_val = a_block.get(p)
        b_val = b_block.get(p)
        # Per-metric (NOT per-percentile) null note: the percentile
        # array is all-or-nothing in flow-metrics (n<2 -> all three
        # are null), and the spec writes ``<metric> null in <side>``,
        # not ``<metric> p50 null in <side>``.
        _maybe_emit_null_note(
            result, metric, a_val, b_val, a_label, b_label, null_noted
        )
        abs_delta, pct_delta = _delta_pair(
            "{} {}".format(metric, p), a_val, b_val, result.notes
        )
        result.rows.append(
            DeltaRow(
                metric_label="{} {}".format(metric, p),
                a=a_val,
                b=b_val,
                abs_delta=abs_delta,
                pct_delta=pct_delta,
            )
        )
    _maybe_emit_n_note(
        result,
        metric,
        a_block.get("n"),
        b_block.get("n"),
        a_label,
        b_label,
    )


def _emit_bucket(
    result: DeltaResult,
    metric: str,
    a: Mapping[str, object],
    b: Mapping[str, object],
    a_label: str,
    b_label: str,
    null_noted: set,
) -> None:
    a_block = _as_mapping(a[metric])
    b_block = _as_mapping(b[metric])
    for bucket in FLOW_DISTRIBUTION_BUCKETS:
        label = "{}.{}".format(metric, bucket)
        a_val = a_block.get(bucket)
        b_val = b_block.get(bucket)
        _maybe_emit_null_note(
            result, metric, a_val, b_val, a_label, b_label, null_noted
        )
        abs_delta, pct_delta = _delta_pair(label, a_val, b_val, result.notes)
        result.rows.append(
            DeltaRow(
                metric_label=label,
                a=a_val,
                b=b_val,
                abs_delta=abs_delta,
                pct_delta=pct_delta,
            )
        )
    # n-rule equivalent for flow_distribution uses denominator.
    _maybe_emit_n_note(
        result,
        metric,
        a_block.get("denominator"),
        b_block.get("denominator"),
        a_label,
        b_label,
    )


# ---------------------------------------------------------------------------
# Delta arithmetic + note emission helpers
# ---------------------------------------------------------------------------
def _delta_pair(
    metric_label: str,
    a_val: Optional[Number],
    b_val: Optional[Number],
    notes: List[str],
) -> Tuple[Optional[Number], Optional[float]]:
    """Compute ``(abs_delta, pct_delta)`` for two known values.

    Appends a ``metric_zero_both_sides`` note when both sides are zero.
    The null-side note is emitted upstream by :func:`_maybe_emit_null_note`
    so this function only handles the arithmetic.
    """
    if a_val is None or b_val is None:
        return None, None
    abs_delta = b_val - a_val
    if a_val == 0 and b_val == 0:
        notes.append(Note.metric_zero_both_sides(metric_label))
        return abs_delta, None
    if a_val == 0 and b_val > 0:
        return abs_delta, math.inf
    if a_val == 0 and b_val < 0:
        # Unreachable today (flow-metrics emits no negative metrics);
        # coded for spec completeness, spec lines 326-327.
        return abs_delta, -math.inf
    return abs_delta, (b_val - a_val) / a_val


def _maybe_emit_null_note(
    result: DeltaResult,
    metric: str,
    a_val: Optional[Number],
    b_val: Optional[Number],
    a_label: str,
    b_label: str,
    null_noted: set,
) -> None:
    if a_val is None and (metric, a_label) not in null_noted:
        result.notes.append(Note.metric_null_on_one_side(metric, a_label))
        null_noted.add((metric, a_label))
    if b_val is None and (metric, b_label) not in null_noted:
        result.notes.append(Note.metric_null_on_one_side(metric, b_label))
        null_noted.add((metric, b_label))


def _maybe_emit_n_note(
    result: DeltaResult,
    metric: str,
    n_a,
    n_b,
    a_label: str,
    b_label: str,
) -> None:
    """Spec lines 338-345. Emits one ``n-differs`` note per metric when
    the per-side sample counts diverge by more than 10% or are zero on
    either side.

    Skipped silently when either side lacks an ``n`` / ``denominator``
    field (e.g. a synthetic test fixture). flow-metrics always emits
    both for the metric kinds that carry them, so this guard only
    matters for partial fixtures.
    """
    if n_a is None or n_b is None:
        return
    m = max(n_a, n_b)
    triggers = m == 0 or abs(n_a - n_b) / m > 0.1
    if triggers:
        result.notes.append(
            Note.n_differs(metric, n_a, n_b, (a_label, b_label))
        )


__all__ = [
    "CANONICAL_METRIC_ORDER",
    "DeltaResult",
    "DeltaRow",
    "FLOW_DISTRIBUTION_BUCKETS",
    "PERCENTILES",
    "compute_deltas",
]
