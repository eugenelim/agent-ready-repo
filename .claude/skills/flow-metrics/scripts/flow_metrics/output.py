"""T10 output rendering — JSON canonicalisation, CSV long-form, per-issue JSONL.

The renderer is the seam between the pipeline (T6 aggregate, T8 cohort,
T9 per_team, T11 notes + meta) and the wire format. It takes an already-
built :class:`Report` and emits bytes in the spec-pinned shape, applying:

* ``--metrics`` filtering — :class:`~flow_metrics.aggregate.AggregateBlock`
  always carries every metric, and ``Report.metrics_requested`` is the
  single gate that drops unrequested ones from the wire output.
* Float rounding — every ``float`` in the output is round-tripped through
  ``round(x, 4)`` via a recursive *pre-walk*, **not** via
  ``json.dumps(default=...)``: the ``default=`` hook does not fire on
  floats (only on types the encoder doesn't recognise), so a hook-based
  approach silently no-ops. The pre-walk is the only correct path.
* Codepoint-sorted object keys at every level, with one explicit
  exception: the *bucket-order maps* (``flow_distribution`` and its
  cohort / per-team copies) emit ``feature, defect, debt, risk, subtask,
  other, denominator`` in that fixed canonical order. The serializer
  detects these via a :class:`_BucketMap` marker subclass of ``dict``.
* Defensive sorting — ``notes`` is sorted at emit; ``meta.sources`` and
  ``meta.metrics_requested`` are re-sorted (lex / canonical respectively)
  so the test passes even when the caller hands an unsorted list. The
  per_team list is *not* re-sorted here — T9's :func:`per_team_rollup`
  already sorts by team name in codepoint order, and re-sorting would
  silently mask a regression there.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional

from .aggregate import (
    FLOW_DISTRIBUTION_BUCKETS,
    AggregateBlock,
    PercentileStat,
)
from .per_issue import PerIssueRow

# T9-API: imported lazily so a Report can carry rows of the spec'd shape
# even if a tester stubs PerTeamRow locally (the only attributes accessed
# are ``.team`` and ``.aggregates``).


# ---------------------------------------------------------------------------
# Canonical orders
# ---------------------------------------------------------------------------
# Spec § "Outputs" → bucket order locked here (not lex). The order matches
# :data:`flow_metrics.aggregate.FLOW_DISTRIBUTION_BUCKETS` plus the trailing
# ``denominator`` field that lives inside the same map.
BUCKET_ORDER: tuple = FLOW_DISTRIBUTION_BUCKETS + ("denominator",)

# Spec § "Outputs" → meta.metrics_requested canonical order. Matches the
# ``--metrics`` enumeration in :data:`flow_metrics.ALL_METRICS`. Duplicated
# here so the output module doesn't import the CLI module (which would
# create a cycle: __init__.py imports several submodules at import time).
CANONICAL_METRICS_ORDER: tuple = (
    "cycle_time",
    "lead_time",
    "throughput",
    "wip",
    "flow_load",
    "rework_rate",
    "flow_time",
    "flow_efficiency",
    "flow_distribution",
    "defect_ratio",
)
_METRIC_INDEX: Dict[str, int] = {m: i for i, m in enumerate(CANONICAL_METRICS_ORDER)}

# Percentile-bearing metrics (CSV emits p50/p75/p90/n).
_PERCENTILE_METRICS = frozenset({"cycle_time", "lead_time", "flow_time", "flow_efficiency"})
# Scalar metrics (CSV emits p50=value, p75/p90/count blank).
_SCALAR_METRICS = frozenset({"throughput", "wip", "flow_load", "rework_rate", "defect_ratio"})


class _BucketMap(dict):
    """Marker subclass of ``dict`` for ``flow_distribution``-style maps.

    The custom serializer detects this via ``isinstance`` and emits keys
    in the fixed bucket order rather than codepoint order. Subclassing
    ``dict`` (rather than wrapping) keeps ``round_floats`` and ``in``
    checks transparent.
    """


# ---------------------------------------------------------------------------
# Report dataclass — seam between pipeline and wire format
# ---------------------------------------------------------------------------
@dataclass
class Report:
    """Inputs the renderer consumes, bundled in one object.

    The pipeline builds a Report once it has every block computed; the
    renderer is then a pure function of the Report. Mutable defaults
    (``per_team``, ``notes``) use :func:`dataclasses.field` so callers
    don't have to construct them when there's nothing to emit.
    """

    aggregate: AggregateBlock
    meta: Mapping[str, Any]
    notes: List[str] = field(default_factory=list)
    metrics_requested: List[str] = field(default_factory=lambda: list(CANONICAL_METRICS_ORDER))
    cohort_breakdown: Optional[Mapping[str, AggregateBlock]] = None
    per_team: List[Any] = field(default_factory=list)  # list[PerTeamRow]
    # Note: per-issue rows are not carried on Report — :func:`render_jsonl`
    # takes its own ``Iterable[PerIssueRow]`` directly so the streaming
    # path is independent of the aggregate Report (no risk of holding the
    # full iterator alive on the Report dataclass).


# ---------------------------------------------------------------------------
# Pipeline → wire-dict conversion
# ---------------------------------------------------------------------------
def _percentile_to_dict(stat: PercentileStat) -> Dict[str, Any]:
    """Spec wire shape: ``{p50, p75, p90, n}``. Percentile fields are
    ``None`` when ``n < 2`` and emit as JSON ``null`` downstream.
    """
    return {"p50": stat.p50, "p75": stat.p75, "p90": stat.p90, "n": stat.n}


def _aggregates_to_dict(
    block: AggregateBlock, metrics_requested: Iterable[str]
) -> Dict[str, Any]:
    """Project the :class:`AggregateBlock` down to a wire dict honouring
    ``--metrics`` filtering.

    The mapping from ``--metrics`` name to wire key is spec-pinned:
    ``cycle_time / lead_time / flow_time`` get the ``_hours`` suffix in
    the wire output; everything else keeps its bare name. Unrequested
    metrics are absent (not emitted as ``null`` — spec § "Outputs").
    """
    requested = set(metrics_requested)
    out: Dict[str, Any] = {}
    if "cycle_time" in requested:
        out["cycle_time_hours"] = _percentile_to_dict(block.cycle_time_hours)
    if "lead_time" in requested:
        out["lead_time_hours"] = _percentile_to_dict(block.lead_time_hours)
    if "throughput" in requested:
        out["throughput"] = block.throughput
    if "wip" in requested:
        out["wip"] = block.wip
    if "flow_load" in requested:
        out["flow_load"] = block.flow_load
    if "rework_rate" in requested:
        out["rework_rate"] = block.rework_rate
    if "flow_time" in requested:
        out["flow_time_hours"] = _percentile_to_dict(block.flow_time_hours)
    if "flow_efficiency" in requested:
        out["flow_efficiency"] = _percentile_to_dict(block.flow_efficiency)
    if "flow_distribution" in requested:
        dist = _BucketMap()
        for bucket in FLOW_DISTRIBUTION_BUCKETS:
            dist[bucket] = block.flow_distribution[bucket]
        dist["denominator"] = block.flow_distribution_denominator
        out["flow_distribution"] = dist
    if "defect_ratio" in requested:
        out["defect_ratio"] = block.defect_ratio
    return out


def _sort_metrics_requested(metrics: Iterable[str]) -> List[str]:
    """Sort by canonical ``--metrics`` enumeration order, not lex.

    Also dedupes (a metric appearing twice in the input list emits once
    in ``meta.metrics_requested``) and silently drops unknown names so
    the published meta block stays consistent with what ``aggregates``
    actually carries — ``_aggregates_to_dict`` does not emit unknown
    metrics, so listing them in ``meta.metrics_requested`` would lie to
    downstream consumers. CLI flag validation (T1) catches unknown
    names before they reach the renderer; this is the last-line
    defence.
    """
    seen: set = set()
    canonical: List[str] = []
    for m in metrics:
        if m in _METRIC_INDEX and m not in seen:
            seen.add(m)
            canonical.append(m)
    return sorted(canonical, key=lambda m: _METRIC_INDEX[m])


def _meta_to_dict(
    meta: Mapping[str, Any], metrics_requested: List[str]
) -> Dict[str, Any]:
    """Build the meta wire dict, applying the defensive resorts.

    The caller is supposed to pre-sort ``meta.sources`` lex and
    ``meta.metrics_requested`` canonical, but T11 produces ``notes`` /
    ``sources`` opportunistically and the contract tests want stable
    output regardless. Re-sort here so a missing or unsorted upstream
    list doesn't surface as test churn.

    The renderer **does not** materialise ``meta.metrics_requested``
    from a passed-in meta dict — it always uses the ``Report``-level
    ``metrics_requested`` (single source of truth, also drives
    aggregate filtering). Any same-named key in ``meta`` is overridden.

    Other keys (``scope``, ``window``, ``state_config_sha``,
    ``generated_at``, ``caller``, ``per_team_double_counted``,
    optionally ``cohort_jql``) pass through as-is.
    """
    out: Dict[str, Any] = {}
    for k, v in meta.items():
        if k == "metrics_requested":
            continue  # Report-level field wins
        if k == "cohort_jql" and (v is None or (isinstance(v, str) and v == "")):
            # Spec § "Cohort behaviour": key is **absent** when --cohort-jql
            # was not provided — not null, not "". A generic meta builder
            # that always sets the field (with None when unused) would
            # otherwise leak `"cohort_jql":null` past the contract test.
            continue
        if k == "sources" and isinstance(v, (list, tuple)):
            out[k] = sorted(v)
            continue
        out[k] = v
    out["metrics_requested"] = _sort_metrics_requested(metrics_requested)
    return out


def _build_report_dict(report: Report) -> Dict[str, Any]:
    """Compose the canonical top-level dict for :func:`render_json`.

    Block order in the dict doesn't matter (the serializer sorts keys
    codepoint), but populating ``cohort_breakdown`` / ``per_team`` only
    when non-empty matters: an empty ``cohort_breakdown`` would emit as
    ``{}`` and violate the spec's "omit when --cohort-jql absent" rule.
    Same for ``per_team`` (spec: emitted iff resolved issue set spans
    more than one distinct team value; the caller decides; we just emit
    what's there).
    """
    out: Dict[str, Any] = {
        "meta": _meta_to_dict(report.meta, list(report.metrics_requested)),
        "aggregates": _aggregates_to_dict(report.aggregate, report.metrics_requested),
        "notes": sorted(report.notes),
    }
    if report.cohort_breakdown:
        # Truthy check — an empty dict slips past `is not None` and would
        # emit `"cohort_breakdown":{}`, violating the spec's "omit when
        # --cohort-jql absent" rule for any caller that defaults the
        # field to an empty dict instead of None.
        #
        # Spec lines 406-428: cohort_breakdown emits both `cohort` and
        # `control` sides together — the example always shows both, and
        # T8's :func:`build_cohort_breakdown` always returns both. A
        # partial breakdown (one side only) is upstream contract
        # violation; rather than silently produce spec-undefined output,
        # require both-or-neither and skip emission when one is missing.
        sides_present = [s for s in ("cohort", "control") if s in report.cohort_breakdown]
        if set(sides_present) == {"cohort", "control"}:
            out["cohort_breakdown"] = {
                side: _aggregates_to_dict(
                    report.cohort_breakdown[side], report.metrics_requested
                )
                for side in ("cohort", "control")
            }
    if report.per_team:
        out["per_team"] = [
            {
                "team": pt.team,
                "aggregates": _aggregates_to_dict(pt.aggregates, report.metrics_requested),
            }
            for pt in report.per_team
        ]
    return out


# ---------------------------------------------------------------------------
# Float rounding pre-walk
# ---------------------------------------------------------------------------
def _round_floats(obj: Any) -> Any:
    """Recursively rebuild ``obj`` with every ``float`` rounded to 4 dp.

    Pre-walk because :func:`json.dumps`'s ``default=`` hook does not fire
    on ``float`` (only on types the encoder doesn't recognise). Without
    this pass, the serializer would emit raw computation-precision
    floats (``38.20000000000001`` etc.), violating the
    ``test_floats_rounded_to_4dp`` regex.

    Preserves :class:`_BucketMap` subclass identity so the bucket-order
    serializer branch still triggers after rounding. Ints (including
    ``bool``) pass through unchanged — never cast through float, or
    ``throughput == 84`` would serialize as ``84.0``.
    """
    if isinstance(obj, bool):
        return obj  # bool is-a int — guard before the int branch matters
    if isinstance(obj, float):
        return round(obj, 4)
    if isinstance(obj, _BucketMap):
        out = _BucketMap()
        for k, v in obj.items():
            out[k] = _round_floats(v)
        return out
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v) for v in obj]
    if isinstance(obj, tuple):
        return [_round_floats(v) for v in obj]  # tuples → JSON arrays
    return obj


# ---------------------------------------------------------------------------
# Custom recursive serializer
# ---------------------------------------------------------------------------
def _json_str(s: str) -> bytes:
    """Encode a JSON string. ``ensure_ascii=False`` keeps non-ASCII team
    names (e.g. ``"Über-team"``) readable on the wire; the cohort /
    permission tests don't rely on escaped output.
    """
    return json.dumps(s, ensure_ascii=False).encode("utf-8")


def _serialize(obj: Any) -> bytes:
    """Recursive serialize to JSON bytes with codepoint-sorted keys,
    except :class:`_BucketMap` which emits in fixed bucket order.
    """
    if obj is None:
        return b"null"
    if obj is True:
        return b"true"
    if obj is False:
        return b"false"
    if isinstance(obj, _BucketMap):
        parts: List[bytes] = []
        emitted: set = set()
        for k in BUCKET_ORDER:
            if k in obj:
                parts.append(_json_str(k) + b":" + _serialize(obj[k]))
                emitted.add(k)
        # Defensive: a future custom-bucket extension might add keys not
        # in BUCKET_ORDER. Emit those after the canonical block in
        # codepoint order rather than dropping them silently.
        leftover = sorted(k for k in obj.keys() if k not in emitted)
        for k in leftover:
            parts.append(_json_str(k) + b":" + _serialize(obj[k]))
        return b"{" + b",".join(parts) + b"}"
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        parts2: List[bytes] = []
        for k in keys:
            parts2.append(_json_str(k) + b":" + _serialize(obj[k]))
        return b"{" + b",".join(parts2) + b"}"
    if isinstance(obj, list):
        # ``_round_floats`` normalises tuples → lists in the pre-walk, so
        # the serializer only ever sees lists for sequence-like values.
        item_parts = [_serialize(v) for v in obj]
        return b"[" + b",".join(item_parts) + b"]"
    if isinstance(obj, int):
        # bool already handled above; this is real int (incl. throughput,
        # wip, n, denominator — never serialise these through float).
        return str(obj).encode("utf-8")
    if isinstance(obj, float):
        # Already pre-rounded; json.dumps emits the shortest representation
        # consistent with the value, which for ``round(x, 4)`` outputs
        # never exceeds 4 decimal digits.
        return json.dumps(obj).encode("utf-8")
    if isinstance(obj, str):
        return _json_str(obj)
    if isinstance(obj, datetime):
        return _json_str(obj.isoformat())
    raise TypeError("flow_metrics output: unserialisable type {!r}".format(type(obj).__name__))


# ---------------------------------------------------------------------------
# Public renderers
# ---------------------------------------------------------------------------
def render_json(report: Report) -> bytes:
    """Render the full aggregate report as canonical JSON bytes.

    Steps (each one pinned by a separate contract / construction test):

    1. Compose the canonical dict (``_build_report_dict``) — applies
       ``--metrics`` filtering, materialises percentile + flow_distribution
       wire shapes, defensively re-sorts ``notes`` and ``meta.sources``.
    2. Pre-walk every ``float`` and replace with ``round(x, 4)``.
       :func:`json.dumps`'s ``default=`` hook will not fire on floats,
       so this is the only correct place to round.
    3. Custom recursive serialize with codepoint-sorted keys, except
       bucket-order maps (``flow_distribution`` and copies) which emit
       in ``feature, defect, debt, risk, subtask, other, denominator``
       order.
    """
    canonical = _build_report_dict(report)
    rounded = _round_floats(canonical)
    return _serialize(rounded)


def render_jsonl(rows: Iterable[PerIssueRow]) -> Iterator[bytes]:
    """Stream per-issue rows as JSONL bytes, one object per line.

    Each row's keys are codepoint-sorted (no bucket-order exceptions
    apply at the per-issue level — the JSONL shape has no
    ``flow_distribution`` field). Floats are rounded to 4 dp per row.
    Datetimes serialise as ISO-8601 strings.

    Line ordering matches input order. The caller is responsible for
    feeding rows in ``key`` ascending (codepoint) order; upstream this
    falls out of the ``ORDER BY key ASC`` JQL suffix that every
    :func:`~flow_metrics.compose_jql` call adds.
    """
    for row in rows:
        d = _per_issue_row_to_dict(row)
        rounded = _round_floats(d)
        yield _serialize(rounded) + b"\n"


def _per_issue_row_to_dict(row: PerIssueRow) -> Dict[str, Any]:
    """Per-issue wire dict.

    ``wip_samples`` is omitted — it's an internal flow_load aggregation
    detail, not part of the documented per-issue contract (spec § "Per-
    issue mode" lists every emitted field; ``wip_samples`` is not among
    them). Every other field is emitted; nullable fields emit JSON
    ``null`` for ``None``.

    ``cohort`` is **only** emitted when set (``True`` / ``False``). When
    ``--cohort-jql`` is not in play, T8's :func:`tag_cohort` doesn't run
    and ``row.cohort`` stays ``None``; emitting ``"cohort": null`` would
    mislead consumers into thinking the row was tagged as not-in-cohort.
    Spec § "Cohort behaviour" line 1124 binds cohort-field presence to
    cohort-jql mode; absence is the documented signal for "no cohort".
    """
    out: Dict[str, Any] = {
        "key": row.key,
        "issue_created": row.issue_created,
        "first_commitment_at": row.first_commitment_at,
        "first_delivery_at": row.first_delivery_at,
        "cycle_eligible": row.cycle_eligible,
        "cycle_time_hours": row.cycle_time_hours,
        "lead_time_hours": row.lead_time_hours,
        "flow_efficiency": row.flow_efficiency,
        "rework_count": row.rework_count,
        "issuetype_at_delivery": row.issuetype_at_delivery,
        "issuetype_bucket": row.issuetype_bucket,
        "team": row.team,
        "delivered_in_window": row.delivered_in_window,
        "cancelled_in_window": row.cancelled_in_window,
        "wip_at_to": row.wip_at_to,
    }
    if row.cohort is not None:
        out["cohort"] = row.cohort
    return out


# ---------------------------------------------------------------------------
# CSV long-form
# ---------------------------------------------------------------------------
CSV_HEADER: tuple = ("metric", "scope", "cohort", "team", "p50", "p75", "p90", "count")


def _format_scope(scope: Any) -> str:
    """Render the meta.scope dict as a single CSV-friendly string.

    Stable but human-readable: ``"PROJ"`` for plain project, ``"PROJ/Foo"``
    for project+team, ``"program-id=42"`` / ``"portfolio-id=42"`` for
    Jira Align scope. Empty when the meta block has no scope.
    """
    if not isinstance(scope, Mapping):
        return ""
    if scope.get("project"):
        team = scope.get("team")
        if isinstance(team, str) and team:
            return "{}/{}".format(scope["project"], team)
        return str(scope["project"])
    if scope.get("program_id") is not None:
        return "program-id={}".format(scope["program_id"])
    if scope.get("portfolio_id") is not None:
        return "portfolio-id={}".format(scope["portfolio_id"])
    return ""


def _csv_cell_float(value: Any) -> str:
    """CSV cell for a maybe-float maybe-None maybe-int metric value.

    ``None`` -> blank string (used for percentiles with ``n < 2`` and for
    blank ``p75 / p90`` columns on scalar-metric rows). Floats are
    rounded to 4 dp and rendered via ``json.dumps`` — same precision
    contract as the JSON / JSONL siblings, so ``38.2`` not
    ``38.20000000000001`` and ``120.0`` not ``120``. Ints pass through
    as the int repr.

    Bools are not expected (aggregate metrics are numeric / nullable),
    so no special arm: ``bool`` would hit the ``int`` branch and emit
    ``1`` / ``0``, which is fine if it ever happens.
    """
    if value is None:
        return ""
    if isinstance(value, float):
        return json.dumps(round(value, 4))
    if isinstance(value, int):
        return str(value)
    return str(value)


def _emit_aggregate_rows(
    rows_out: List[List[str]],
    scope_str: str,
    cohort_label: str,
    team_label: str,
    block: AggregateBlock,
    metrics_requested: List[str],
) -> None:
    """Append one CSV row per metric in canonical order.

    Percentile metrics fill ``p50/p75/p90`` and ``count`` from the
    :class:`PercentileStat`. Scalar metrics put the value in ``p50`` and
    leave ``p75 / p90 / count`` blank (spec § "Outputs"). flow_distribution
    expands into one row per bucket with the ratio in ``p50`` and the
    distribution denominator in ``count`` — keeping the long-form contract
    intact for downstream CSV consumers that pivot by ``(metric, scope,
    cohort, team)``.
    """
    requested = [m for m in CANONICAL_METRICS_ORDER if m in set(metrics_requested)]
    for metric in requested:
        if metric in _PERCENTILE_METRICS:
            stat = getattr(block, _percentile_attr(metric))
            rows_out.append([
                metric,
                scope_str,
                cohort_label,
                team_label,
                _csv_cell_float(stat.p50),
                _csv_cell_float(stat.p75),
                _csv_cell_float(stat.p90),
                str(stat.n),
            ])
        elif metric in _SCALAR_METRICS:
            value = getattr(block, _scalar_attr(metric))
            rows_out.append([
                metric,
                scope_str,
                cohort_label,
                team_label,
                _csv_cell_float(value),
                "",
                "",
                "",
            ])
        elif metric == "flow_distribution":
            for bucket in FLOW_DISTRIBUTION_BUCKETS:
                rows_out.append([
                    "flow_distribution.{}".format(bucket),
                    scope_str,
                    cohort_label,
                    team_label,
                    _csv_cell_float(block.flow_distribution[bucket]),
                    "",
                    "",
                    str(block.flow_distribution_denominator),
                ])


def _percentile_attr(metric: str) -> str:
    """``--metrics`` name → :class:`AggregateBlock` attribute."""
    return {
        "cycle_time": "cycle_time_hours",
        "lead_time": "lead_time_hours",
        "flow_time": "flow_time_hours",
        "flow_efficiency": "flow_efficiency",
    }[metric]


def _scalar_attr(metric: str) -> str:
    return {
        "throughput": "throughput",
        "wip": "wip",
        "flow_load": "flow_load",
        "rework_rate": "rework_rate",
        "defect_ratio": "defect_ratio",
    }[metric]


def render_csv(report: Report) -> bytes:
    """Render the report as long-form CSV bytes.

    Header row first, then one row per (metric, scope, cohort, team)
    tuple. ``cohort`` is one of ``"all"`` (global aggregate),
    ``"cohort"`` (cohort_breakdown.cohort), or ``"control"``; the
    ``team`` column is blank for global / cohort rows and the team name
    for per_team rows. Columns: ``metric, scope, cohort, team, p50,
    p75, p90, count``.
    """
    buf = io.StringIO()
    writer = _csv_writer(buf)
    writer.writerow(list(CSV_HEADER))

    scope_str = _format_scope(report.meta.get("scope", {}))
    metrics = list(report.metrics_requested)

    rows: List[List[str]] = []
    _emit_aggregate_rows(rows, scope_str, "all", "", report.aggregate, metrics)
    # Mirror the JSON-side contract: only emit cohort / control rows
    # when both sides are present (spec lines 406-428). Partial
    # breakdowns are upstream contract violations and are silently
    # skipped, same as on the JSON path.
    if report.cohort_breakdown and {"cohort", "control"}.issubset(report.cohort_breakdown):
        for side in ("cohort", "control"):
            _emit_aggregate_rows(
                rows, scope_str, side, "", report.cohort_breakdown[side], metrics
            )
    for pt in report.per_team:
        _emit_aggregate_rows(
            rows, scope_str, "all", pt.team, pt.aggregates, metrics
        )

    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8")


def _csv_writer(buf: io.StringIO):
    """``csv.writer`` with ``lineterminator='\\n'``.

    Default ``\\r\\n`` line terminator would surface as a CRLF on every
    row regardless of platform — fine for spec consumers, but it makes
    byte-level test assertions painful. Locking to LF here keeps the
    test fixtures readable and matches the JSON / JSONL sibling outputs.
    """
    import csv as _csv

    return _csv.writer(buf, lineterminator="\n")


__all__ = [
    "BUCKET_ORDER",
    "CANONICAL_METRICS_ORDER",
    "CSV_HEADER",
    "Report",
    "render_csv",
    "render_json",
    "render_jsonl",
]
