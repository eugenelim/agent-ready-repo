"""T6 aggregation — percentiles, throughput, WIP, Flow Load, Flow
Distribution, defect ratio, rework rate, flow efficiency.

:func:`aggregate` consumes an :class:`Iterator[PerIssueRow]` exactly
once. Per-metric float lists accumulate as rows stream through; scalar
counters and per-day WIP samples update inline. After the stream is
drained, percentiles are computed via :func:`statistics.quantiles` (n=
100, ``method="exclusive"``) at indices 49 / 74 / 89 for p50 / p75 / p90
— full-precision floats in, one :func:`_round` call per percentile per
metric on the way out (the round-once contract, locked in by
``test_percentile_computed_at_full_precision``).

T6 owns the zero-denominator / unmapped-issuetype / delivered-without-
commitment counters that T11 turns into ``notes`` lines. Cohort split
(T8), caching (T7), output filtering and rendering (T10), and notes
wording (T11) are downstream.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Mapping, Optional

from .config import StateConfig
from .per_issue import PerIssueRow


PERCENTILE_DECIMALS = 4

FLOW_DISTRIBUTION_BUCKETS = ("feature", "defect", "debt", "risk", "subtask", "other")
SUBTASK_BUCKET = "subtask"
OTHER_BUCKET = "other"


_round = round  # rebound here so percentile-rounding can be monkey-patched
                # independently of the per-metric scalar rounds below.


@dataclass(frozen=True)
class PercentileStat:
    """Median / p75 / p90 + sample count.

    Percentile values are ``None`` when ``n < 2`` (the smallest sample
    that :func:`statistics.quantiles` will accept). Aggregates over the
    empty-throughput case therefore carry ``PercentileStat(None, None,
    None, 0)`` rather than raising.
    """
    p50: Optional[float]
    p75: Optional[float]
    p90: Optional[float]
    n: int


@dataclass(frozen=True)
class AggregateBlock:
    """Flat one-field-per-metric aggregate.

    Carries every metric the spec defines; the T10 serializer filters to
    ``--metrics``. Notes-block counters live alongside the metrics so the
    aggregator's single pass is the only place that needs to touch the
    raw row stream.
    """

    cycle_time_hours: PercentileStat
    lead_time_hours: PercentileStat
    flow_time_hours: PercentileStat  # alias of lead_time_hours, byte-equal
    throughput: int
    wip: int
    flow_load: float
    rework_rate: Optional[float]
    flow_efficiency: PercentileStat
    flow_distribution: Mapping[str, float]
    flow_distribution_denominator: int
    defect_ratio: float
    # Notes-block counters (T11 wordsmiths them into notes lines).
    cancelled_in_window: int
    delivered_without_commitment: int
    flow_efficiency_zero_denominator: int
    unmapped_issuetype: int
    flow_load_sample_count: int


def _percentiles(values: List[float]) -> PercentileStat:
    """Compute p50 / p75 / p90 of ``values`` via the exclusive method.

    statistics.quantiles requires at least two data points. For
    ``len(values) < 2`` we return percentile-``None`` with the actual
    count, so the downstream serializer can emit ``null`` percentiles
    without re-deriving ``n``.
    """
    n = len(values)
    if n < 2:
        return PercentileStat(p50=None, p75=None, p90=None, n=n)
    q = statistics.quantiles(values, n=100, method="exclusive")
    return PercentileStat(
        p50=_round(q[49], PERCENTILE_DECIMALS),
        p75=_round(q[74], PERCENTILE_DECIMALS),
        p90=_round(q[89], PERCENTILE_DECIMALS),
        n=n,
    )


def aggregate(
    rows: Iterator[PerIssueRow],
    window: Any,
    config: StateConfig,
    *,
    include_subtasks: bool = False,
) -> AggregateBlock:
    """Single-pass aggregation over ``rows``.

    Consumes the iterator exactly once. Per-metric float lists buffer
    only the values that contribute to a percentile (subtasks excluded
    by default — they're added back when ``include_subtasks=True``);
    per-day WIP samples are summed column-wise across rows so the peak
    additional memory is ``O(days_in_window + delivered_count)`` rather
    than ``O(rows)``.

    ``config`` is reserved for future metric-config hooks (e.g., a
    rework-signal override at aggregate time). T6 does not read it
    today — every populated PerIssueRow already carries the
    state-config-derived booleans — but threading it keeps the
    signature stable for T7+.
    """
    del config  # reserved; rows are pre-derived against state config

    sample_count = (window.to_date - window.from_date).days + 1
    per_day_wip: List[int] = [0] * sample_count

    cycle_times: List[float] = []
    lead_times: List[float] = []
    flow_effs: List[float] = []

    throughput = 0
    wip = 0
    cancelled = 0
    delivered_without_commitment = 0
    flow_efficiency_zero_denominator = 0
    unmapped_issuetype = 0
    rework_numerator = 0

    buckets: Dict[str, int] = {b: 0 for b in FLOW_DISTRIBUTION_BUCKETS}

    for row in rows:
        if row.delivered_in_window:
            raw_bucket = row.issuetype_bucket or OTHER_BUCKET
            # Custom user-configured buckets (anything outside the spec's
            # standard six) funnel to "other" for the AggregateBlock's
            # fixed-shape distribution. They are NOT counted as unmapped
            # — only T5's None-mapped-to-"other" sink (raw issuetype not
            # in any user bucket) signals "unmapped" for the notes line.
            bucket = raw_bucket if raw_bucket in buckets else OTHER_BUCKET
            buckets[bucket] += 1
            if raw_bucket == OTHER_BUCKET:
                unmapped_issuetype += 1

            # Rework numerator: sum across ALL delivered-in-window rows
            # (spec: numerator-population is delivered-in-window even
            # when subtasks are excluded from the throughput denominator).
            rework_numerator += row.rework_count

            is_subtask = bucket == SUBTASK_BUCKET
            if include_subtasks or not is_subtask:
                throughput += 1
                if row.lead_time_hours is not None:
                    lead_times.append(row.lead_time_hours)
                if row.cycle_eligible:
                    if row.cycle_time_hours is not None:
                        cycle_times.append(row.cycle_time_hours)
                    if row.flow_efficiency is not None:
                        flow_effs.append(row.flow_efficiency)
                    else:
                        # Cycle-eligible but ``(active_t + wait_t) == 0``
                        # — excluded from the flow_efficiency percentile
                        # array, surfaced in notes by T11.
                        flow_efficiency_zero_denominator += 1
                else:
                    delivered_without_commitment += 1

        if row.cancelled_in_window:
            cancelled += 1

        if row.wip_at_to:
            wip += 1

        # Per-day WIP samples sum column-wise. Tolerate rows whose
        # ``wip_samples`` length differs from ``sample_count`` (e.g.,
        # synthetically constructed rows in tests that don't exercise
        # Flow Load) — only contributions inside the window count.
        for i, sample in enumerate(row.wip_samples):
            if i >= sample_count:
                break
            if sample:
                per_day_wip[i] += 1

    cycle_stat = _percentiles(cycle_times)
    lead_stat = _percentiles(lead_times)
    flow_eff_stat = _percentiles(flow_effs)
    # Flow Time aliases Lead Time byte-for-byte; the spec is explicit
    # that flow_time_hours is the same value, not a separate computation.
    flow_time_stat = lead_stat

    flow_load = (sum(per_day_wip) / sample_count) if sample_count > 0 else 0.0

    distribution_denominator = sum(buckets.values())
    if distribution_denominator > 0:
        distribution_ratios: Dict[str, float] = {
            b: round(buckets[b] / distribution_denominator, PERCENTILE_DECIMALS)
            for b in FLOW_DISTRIBUTION_BUCKETS
        }
    else:
        distribution_ratios = {b: 0.0 for b in FLOW_DISTRIBUTION_BUCKETS}

    defect_ratio = distribution_ratios["defect"]

    rework_rate: Optional[float] = None
    if throughput > 0:
        rework_rate = round(rework_numerator / throughput, PERCENTILE_DECIMALS)

    return AggregateBlock(
        cycle_time_hours=cycle_stat,
        lead_time_hours=lead_stat,
        flow_time_hours=flow_time_stat,
        throughput=throughput,
        wip=wip,
        flow_load=round(flow_load, PERCENTILE_DECIMALS),
        rework_rate=rework_rate,
        flow_efficiency=flow_eff_stat,
        flow_distribution=distribution_ratios,
        flow_distribution_denominator=distribution_denominator,
        defect_ratio=defect_ratio,
        cancelled_in_window=cancelled,
        delivered_without_commitment=delivered_without_commitment,
        flow_efficiency_zero_denominator=flow_efficiency_zero_denominator,
        unmapped_issuetype=unmapped_issuetype,
        flow_load_sample_count=sample_count,
    )


__all__ = [
    "AggregateBlock",
    "FLOW_DISTRIBUTION_BUCKETS",
    "OTHER_BUCKET",
    "PERCENTILE_DECIMALS",
    "PercentileStat",
    "SUBTASK_BUCKET",
    "aggregate",
]
