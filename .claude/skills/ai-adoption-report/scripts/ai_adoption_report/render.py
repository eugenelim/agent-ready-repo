"""T7 output rendering — Markdown + JSON sidecar.

Pure transformation layer. :func:`render_markdown` and :func:`render_json`
take a :class:`modes.ReportData` plus a caller-supplied ``title`` and
``generated_at`` (T8 supplies the latter; tests stub it) and return the
final wire strings. No I/O, no clock reads.

Markdown rules (spec lines 388-453, plan lines 463-500):

- Section order fixed; empty sections omitted entirely (no header).
- Numeric cells: integers bare; floats rounded to 4dp with trailing
  zeros stripped (e.g. ``38.2`` not ``38.2000``).
- Percent column: signed (``+0.0%`` for true zero; ``−`` U+2212 for
  negative; ``+∞%`` / ``−∞%`` for inf).
- None cells: ``—`` (em dash).
- Negative numerics use U+2212 unicode minus; ASCII hyphen is reserved
  for date strings like ``2024-Q1``.
- Markdown special characters in scope/team names are backslash-escaped
  via :data:`_MARKDOWN_ESCAPE_CHARS`. ASCII hyphen ``-`` is deliberately
  NOT in the set (CommonMark only treats it as a list marker at line
  start, which never happens inside a table cell, and dates like
  ``2024-Q1`` and team names like ``Mobile-Web`` are common).

JSON canonicalization (spec lines 495-516, plan lines 502-516):

- All object keys sorted codepoint-ascending EXCEPT the ``deltas``
  subtree, whose keys follow :data:`delta.CANONICAL_METRIC_ORDER`.
- Floats rounded to 4dp at serialization time via a recursive pre-walk
  (mirrors ``flow_metrics.output._round_floats``;
  :func:`json.dumps`'s ``default=`` hook does not fire on floats so a
  hook-based approach silently no-ops).
- ``meta.inputs`` sorted by basename codepoint-ascending.
- ``notes`` sorted lex and deduped.
- ``per_scope`` sorted by canonical scope-repr.

The deltas-key-order exception is implemented via a sentinel
placeholder: the document is built with ``deltas`` replaced by a
unique string, serialized with ``sort_keys=True``, and the placeholder
is then string-replaced with the separately-serialized canonical-order
deltas blob (plan line 514-516, "Recommend this over the encoder
subclass unless you find a cleaner encoder pattern").

T7 invariants and decisions (flagged for spec amendment):

1. Summary string is composed by T7 from :attr:`ReportData.deltas` (or
   ``cohort_deltas`` in cohort mode, or scope-count + window in program
   mode). The spec shows an example (lines 400-402) but doesn't pin the
   producer; T7 takes the role and emits a best-effort sentence.
2. Per-scope table column set: every canonical-order scalar metric +
   every distribution metric's p50 only (p75/p90 elided; readers wanting
   full percentile detail look at the JSON sidecar). The spec example
   (line 413) doesn't pin the full column set.
3. Aggregate row: emitted as a final ``"Aggregate"``-labeled row in the
   per-scope table, sourced from :attr:`ReportData.program_aggregates`.
   Spec doesn't require it explicitly; T6 computes the math so this
   surfaces it.
4. ``cohort_breakdown`` JSON subtree keys are sorted codepoint-ascending
   (not canonical-metric-order) — only ``deltas`` gets the order
   exception per spec line 508 ("the one intentional exception").

Stdlib only. Pure functions. Python >= 3.10.
"""
from __future__ import annotations

import json
import math
from typing import Any, Iterable, List, Literal, Optional

from .delta import (
    CANONICAL_METRIC_ORDER,
    FLOW_DISTRIBUTION_BUCKETS,
    PERCENTILES,
)
from .inputs import InputFile
from .modes import ReportData


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------
SKILL_NAME = "ai-adoption-report"
SKILL_VERSION = "1.0"

# Markdown escape characters per plan §T7 lines 483-498. ASCII hyphen ``-``
# is deliberately excluded: date strings like ``2024-Q1`` and team names
# like ``Mobile-Web`` are common, and ``-`` only acquires list-item
# meaning at line start (never inside a table cell).
_MARKDOWN_ESCAPE_CHARS = '|`*_[]\\#+'
_MARKDOWN_ESCAPE_TABLE = str.maketrans({c: "\\" + c for c in _MARKDOWN_ESCAPE_CHARS})

# Distribution metrics + the scalar metrics per the canonical row order.
# Per-scope table column set is the scalars + each distribution metric's
# p50 only.
_DISTRIBUTION_METRICS = (
    "cycle_time_hours",
    "lead_time_hours",
    "flow_time_hours",
    "flow_efficiency",
)
_SCALAR_METRICS = ("throughput", "wip", "flow_load", "rework_rate", "defect_ratio")

# Per-metric cell kind. Used by :func:`_kind_for_label` so both the delta
# rows and the per-scope rows pick the right ``_fmt_cell`` branch.
_METRIC_CELL_KIND = {
    "throughput": "int",
    "wip": "int",
    "flow_load": "float",
    "cycle_time_hours": "hours",
    "lead_time_hours": "hours",
    "flow_time_hours": "hours",
    "flow_efficiency": "float",
    "rework_rate": "float",
    "defect_ratio": "float",
    "flow_distribution": "float",
}

# Sentinel used by the JSON splice. Long random-looking suffix so a real
# value can never collide. Includes characters json.dumps would never
# need to escape inside a string.
_DELTAS_SENTINEL = "__DELTAS_SENTINEL_a8f3b29c7e1d4f5634d8__"

# JSON ``ValueT`` for type hints in this module.
JsonValue = Any


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def render_markdown(
    report: ReportData,
    *,
    title: str,
    generated_at: str,
) -> str:
    """Render the full Markdown document for ``report``.

    ``generated_at`` is a UTC ISO-8601 string; T8 passes it. T7 never
    reads the clock. The function is pure — same inputs produce
    byte-identical output (per the ``test_byte_identical_rerun`` test).
    """
    lines: List[str] = []

    # ---- Title ----
    # The title is user-supplied (via --title or the default); apply the
    # Markdown escape so a ``|`` / ``*`` / ``_`` / ``[`` / etc. in the
    # title doesn't accidentally trigger emphasis or table parsing inside
    # the heading.
    lines.append("# {}".format(_md_escape(title)))
    lines.append("")

    # ---- Header block ----
    lines.append("**Mode:** {}".format(report.mode))
    lines.append("**Generated at:** {}".format(generated_at))
    lines.append(
        "**Inputs:** {} file(s) — see §Provenance.".format(
            len(report.inputs)
        )
    )
    lines.append(report.header_line)
    lines.append("")

    # ---- Summary ----
    summary = _build_summary(report)
    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    # ---- Metric deltas table ----
    delta_rows = _delta_rows_for_render(report.deltas)
    if delta_rows:
        a_label, b_label = _side_labels_for_mode(report.mode)
        lines.append("## Metric deltas")
        lines.append("")
        lines.extend(_render_delta_table(delta_rows, a_label, b_label))
        lines.append("")

    # ---- Per-scope rows + Aggregate ----
    if report.mode == "program" and report.per_scope_rows:
        lines.append("## Per-scope rows")
        lines.append("")
        lines.extend(
            _render_per_scope_table(
                report.per_scope_rows, report.program_aggregates
            )
        )
        lines.append("")

    # ---- Cohort breakdown ----
    if report.cohort_deltas:
        cohort_rows = _delta_rows_for_render(report.cohort_deltas)
        if cohort_rows:
            # Column labels come from the originating compute_deltas
            # ``side_labels`` so the header always matches the cell data.
            # Baseline+cohort emits ``("baseline-cohort",
            # "current-cohort")``; program-mode cohort rollup emits
            # ``("control", "cohort")``. Falls back to ``("control",
            # "cohort")`` only when the upstream layer forgot to thread
            # the labels through — the spec example (line 418) uses
            # ``cohort`` and ``control`` as the canonical column names.
            cohort_labels = report.cohort_side_labels or ("control", "cohort")
            lines.append("## Cohort breakdown")
            lines.append("")
            lines.extend(
                _render_delta_table(cohort_rows, cohort_labels[0], cohort_labels[1])
            )
            lines.append("")

    # ---- Notes ----
    finalized_notes = _finalize_notes(report.notes)
    if finalized_notes:
        lines.append("## Notes")
        lines.append("")
        for n in finalized_notes:
            lines.append("- {}".format(n))
        lines.append("")

    # ---- Provenance ----
    lines.append("## Provenance")
    lines.append("")
    lines.extend(_render_provenance(report.inputs))
    lines.append("")

    return "\n".join(lines)


def render_json(
    report: ReportData,
    *,
    title: str,
    generated_at: str,
) -> str:
    """Render the JSON sidecar as a serialized string.

    Pure — no I/O, no clock reads. T8 calls this and writes the bytes.
    """
    # Build meta block.
    meta = {
        "skill": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "mode": report.mode,
        "generated_at": generated_at,
        "title": title,
        "inputs": _build_inputs_json(report.inputs),
        "options": {
            "include_cohort_breakdown": report.cohort_deltas is not None,
        },
    }

    # Top-level document. ``deltas`` is stuffed with the sentinel string;
    # we splice the real value in after json.dumps returns. Every other
    # subtree is sorted by json.dumps(sort_keys=True).
    doc: dict = {
        "meta": meta,
        "summary": _build_summary(report),
        "deltas": _DELTAS_SENTINEL,
        "notes": _finalize_notes(report.notes),
    }
    if report.mode == "program":
        doc["per_scope"] = _build_per_scope_json(report.per_scope_rows or [])
        if report.program_aggregates is not None:
            doc["program_aggregates"] = report.program_aggregates
    if report.cohort_deltas is not None:
        doc["cohort_breakdown"] = report.cohort_deltas

    # Pre-walk and round every float to 4dp.
    rounded_doc = _round_floats(doc)
    # The sentinel is a string so _round_floats passed it through;
    # defensive restore in case a future change recurses into strings.
    rounded_doc["deltas"] = _DELTAS_SENTINEL

    main_blob = json.dumps(
        rounded_doc,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=True,
        ensure_ascii=False,
    )

    # Pre-serialize the deltas subtree with sort_keys=False — insertion
    # order from :meth:`DeltaResult.to_dict` follows
    # :data:`delta.CANONICAL_METRIC_ORDER`.
    rounded_deltas = _round_floats(report.deltas)
    deltas_blob = json.dumps(
        rounded_deltas,
        sort_keys=False,
        separators=(",", ":"),
        allow_nan=True,
        ensure_ascii=False,
    )

    placeholder_in_main = json.dumps(_DELTAS_SENTINEL, ensure_ascii=False)
    out = main_blob.replace(placeholder_in_main, deltas_blob, 1)
    return out


# ---------------------------------------------------------------------------
# Notes merge + finalize (plan §T5 lines 357-362)
# ---------------------------------------------------------------------------
def _finalize_notes(notes: Iterable[str]) -> List[str]:
    """Dedupe + codepoint-sort. Used by both renderers so they emit the
    same list. T3/T4/T5/T6 produced notes unsorted; T7 finalizes.
    """
    return sorted(set(notes))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def _build_summary(report: ReportData) -> str:
    """Compose the one-line plain-English summary.

    T7 invention (the spec shows an example but doesn't pin the
    producer). Strategy: pick a few canonical-order key metrics from
    ``report.deltas`` (throughput, cycle_time_hours p50, rework_rate) and
    render their pct deltas in human-readable form. Falls back to a
    scope-count phrase when no deltas exist (program mode).
    """
    if report.mode == "program" and not report.deltas:
        scope_n = len(report.per_scope_rows or [])
        return (
            "Program rollup across {} scope(s); see per-scope rows and "
            "program aggregates below.".format(scope_n)
        )

    pieces: List[str] = []
    deltas = report.deltas

    # throughput (scalar)
    tp = deltas.get("throughput")
    if isinstance(tp, dict) and tp.get("pct") is not None:
        pieces.append(_summary_phrase("throughput", tp.get("pct")))

    # cycle_time_hours p50 (distribution)
    cyc = deltas.get("cycle_time_hours")
    if isinstance(cyc, dict):
        p50 = cyc.get("p50")
        if isinstance(p50, dict) and p50.get("pct") is not None:
            pieces.append(_summary_phrase("cycle time p50", p50.get("pct")))

    # rework_rate (scalar)
    rr = deltas.get("rework_rate")
    if isinstance(rr, dict) and rr.get("pct") is not None:
        pieces.append(_summary_phrase("rework rate", rr.get("pct")))

    if not pieces:
        return (
            "{} comparison; see Metric deltas table and Notes for "
            "detail.".format(report.mode.capitalize())
        )
    sentence = ", ".join(pieces) + "."
    # In cohort mode the deltas describe a within-window partition
    # (cohort side vs control side), not a temporal change. Prefix the
    # phrase so a reader skimming the report doesn't read "throughput
    # down 22.2%" as a regression — it's the cohort side being smaller
    # than control by 22.2%, which is expected when only some tickets
    # are tagged.
    if report.mode == "cohort":
        return "cohort vs control: " + sentence
    return sentence


def _summary_phrase(name: str, pct: float) -> str:
    """Render one metric's pct delta as a short human phrase.

    ``±∞%`` for infinite, ``no change`` for true zero,
    otherwise ``up X%`` or ``down X%`` with one decimal.
    """
    if pct is None:
        return "{} unchanged".format(name)
    if isinstance(pct, float) and math.isinf(pct):
        return "{} {}∞%".format(name, "+" if pct > 0 else "−")
    abs_pct = abs(pct) * 100
    direction = "up" if pct > 0 else ("down" if pct < 0 else "unchanged")
    if direction == "unchanged":
        return "{} unchanged".format(name)
    return "{} {} {:.1f}%".format(name, direction, abs_pct)


# ---------------------------------------------------------------------------
# Delta table rendering
# ---------------------------------------------------------------------------
def _side_labels_for_mode(mode: str) -> tuple[str, str]:
    """Pick the A/B column headers per mode.

    Baseline: ``("baseline", "current")``. Cohort: ``("control",
    "cohort")``. Program-mode primary table is empty so this is
    unreachable for ``mode == "program"`` callers; we still return
    sensible defaults for forward-compat.
    """
    if mode == "cohort":
        return ("control", "cohort")
    return ("baseline", "current")


def _delta_rows_for_render(deltas_dict: dict) -> list[tuple[str, dict]]:
    """Walk the deltas dict (insertion-ordered) and produce
    ``(metric_label, cell_dict)`` tuples for each row.

    ``deltas_dict`` is the :meth:`DeltaResult.to_dict` shape: top-level
    keys are metric names; scalar metrics map directly to a cell dict;
    distribution metrics nest under ``p50``/``p75``/``p90``;
    ``flow_distribution`` nests under bucket keys. We flatten back to
    one row per canonical-order label.
    """
    rows: list[tuple[str, dict]] = []
    for metric, value in deltas_dict.items():
        if not isinstance(value, dict):
            continue
        # Scalar metric: cell dict has ``a``/``b``/``abs``/``pct`` keys.
        if "a" in value and "b" in value and "abs" in value and "pct" in value:
            rows.append((metric, value))
            continue
        # Distribution or bucket metric: nested sub-dict.
        if metric in _DISTRIBUTION_METRICS:
            for p in PERCENTILES:
                if p in value:
                    rows.append(("{} {}".format(metric, p), value[p]))
        elif metric == "flow_distribution":
            for bucket in FLOW_DISTRIBUTION_BUCKETS:
                if bucket in value:
                    rows.append(("{}.{}".format(metric, bucket), value[bucket]))
        else:
            # Unknown nested metric — emit each sub-key in insertion order.
            for sub, cell in value.items():
                if isinstance(cell, dict):
                    rows.append(("{} {}".format(metric, sub), cell))
    return rows


def _render_delta_table(
    rows: list[tuple[str, dict]],
    a_label: str,
    b_label: str,
) -> List[str]:
    """Render the deltas table (header + separator + rows).

    Column order: ``Metric | <a_label> | <b_label> | Δ abs | Δ %``.
    """
    out = [
        "| Metric | {a} | {b} | Δ abs | Δ % |".format(
            a=_md_escape(a_label), b=_md_escape(b_label)
        ),
        "|---|---|---|---|---|",
    ]
    for label, cell in rows:
        kind = _kind_for_label(label)
        out.append(
            "| {m} | {a} | {b} | {ad} | {pd} |".format(
                m=label,
                a=_fmt_cell(cell.get("a"), kind=kind),
                b=_fmt_cell(cell.get("b"), kind=kind),
                ad=_fmt_cell(cell.get("abs"), kind=kind),
                pd=_fmt_cell(cell.get("pct"), kind="percent"),
            )
        )
    return out


def _kind_for_label(label: str) -> str:
    """Pick the cell kind for a delta row label.

    Strips ``" p50"`` / ``".feature"`` suffixes back to the base metric
    name, then looks up :data:`_METRIC_CELL_KIND`. Unknown metrics
    default to ``"float"``.
    """
    base = label.split(" ", 1)[0].split(".", 1)[0]
    return _METRIC_CELL_KIND.get(base, "float")


# ---------------------------------------------------------------------------
# Per-scope table + aggregate row (program mode only)
# ---------------------------------------------------------------------------
# (column_label, agg_key_path) tuples. ``agg_key_path`` is a tuple of
# nested-dict keys; one-element tuples target a top-level scalar, longer
# tuples descend into nested blocks.
_PER_SCOPE_COLUMNS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # (label, kind, path)
    ("throughput", "int", ("throughput",)),
    ("wip", "int", ("wip",)),
    ("flow_load", "float", ("flow_load",)),
    ("cycle_p50", "hours", ("cycle_time_hours", "p50")),
    ("lead_p50", "hours", ("lead_time_hours", "p50")),
    ("flow_time_p50", "hours", ("flow_time_hours", "p50")),
    ("flow_eff_p50", "float", ("flow_efficiency", "p50")),
    ("rework_rate", "float", ("rework_rate",)),
    ("defect_ratio", "float", ("defect_ratio",)),
    ("fd.feature", "float", ("flow_distribution", "feature")),
    ("fd.defect", "float", ("flow_distribution", "defect")),
    ("fd.debt", "float", ("flow_distribution", "debt")),
    ("fd.risk", "float", ("flow_distribution", "risk")),
    ("fd.subtask", "float", ("flow_distribution", "subtask")),
    ("fd.other", "float", ("flow_distribution", "other")),
)


def _render_per_scope_table(
    per_scope_rows: list,
    program_aggregates: Optional[dict],
) -> List[str]:
    """Render the per-scope table plus the final Aggregate row.

    ``per_scope_rows`` arrives sorted by ``scope_repr`` (T6 sorts).
    """
    header_cells = ["Scope"] + [label for label, _, _ in _PER_SCOPE_COLUMNS]
    out = [
        "| " + " | ".join(header_cells) + " |",
        "|" + "|".join("---" for _ in header_cells) + "|",
    ]
    for row in per_scope_rows:
        scope_label = _md_escape(_format_scope_label(row.get("scope", {})))
        agg = row.get("aggregates", {}) or {}
        cells = [scope_label]
        for _, kind, path in _PER_SCOPE_COLUMNS:
            cells.append(_fmt_cell(_dig(agg, path), kind=kind))
        out.append("| " + " | ".join(cells) + " |")

    if program_aggregates is not None:
        cells = ["Aggregate"]
        for _, kind, path in _PER_SCOPE_COLUMNS:
            cells.append(_fmt_cell(_dig(program_aggregates, path), kind=kind))
        out.append("| " + " | ".join(cells) + " |")
    return out


def _format_scope_label(scope: dict) -> str:
    """Render a scope dict as a short human label for the Per-scope table.

    Form: ``project=PROJ team=Foo`` (space-separated, ``key=value``
    pairs). Empty fields are skipped. Unlike :func:`canonical_scope_repr`
    this is for display only — the canonical repr is in the JSON
    sidecar.
    """
    parts = []
    for key in ("project", "team", "program_id", "portfolio_id"):
        if key in scope and scope[key] not in (None, ""):
            parts.append("{}={}".format(key, scope[key]))
    return " ".join(parts) if parts else "(empty scope)"


def _dig(d: dict, path: tuple[str, ...]) -> Any:
    """Walk a nested dict via ``path``. Returns ``None`` on any missing key."""
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def _render_provenance(inputs: List[InputFile]) -> List[str]:
    """Emit one bullet per input file. Sorted by basename codepoint."""
    out: List[str] = []
    sorted_inputs = sorted(inputs, key=lambda i: i.basename)
    for inp in sorted_inputs:
        scope_text = _format_scope_label(inp.scope)
        major, minor = inp.schema_version
        out.append(
            "- {basename} — {scope} — {wf}..{wt} "
            "— sha state={s} issuetype={it} "
            "— generated {gen} — upstream schema {maj}.{mn}".format(
                basename=_md_escape(inp.basename),
                scope=_md_escape(scope_text),
                wf=inp.window_from,
                wt=inp.window_to,
                s=_md_escape(str(inp.meta.get("state_config_sha", ""))),
                it=_md_escape(str(inp.meta.get("issuetype_config_sha", ""))),
                gen=_md_escape(str(inp.meta.get("generated_at", ""))),
                maj=major,
                mn=minor,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Numeric cell formatter
# ---------------------------------------------------------------------------
def _fmt_cell(value: Any, *, kind: str) -> str:
    """Format one Markdown table cell value.

    ``kind`` is one of ``"int" | "float" | "hours" | "percent"``.
    See spec lines 441-453 + plan lines 472-482 for the rules.
    """
    if value is None:
        return "—"
    if kind == "percent":
        return _fmt_percent(value)

    # int / float / hours
    if isinstance(value, bool):
        # bool is-a int — guard before the int branch.
        return str(int(value))
    if isinstance(value, float) and math.isinf(value):
        return ("−" if value < 0 else "") + "∞"
    if kind == "int":
        if isinstance(value, float):
            # int-labeled metric whose value arrived as a float (e.g. an
            # absolute delta in throughput when one side is non-integer).
            # Round to 4dp and emit shortest repr.
            sign = "−" if value < 0 else ""
            return "{}{}".format(sign, _format_float_value(abs(value)))
        sign = "−" if value < 0 else ""
        return "{}{}".format(sign, abs(value))
    # float / hours
    if isinstance(value, int):
        sign = "−" if value < 0 else ""
        return "{}{}".format(sign, abs(value))
    if isinstance(value, float):
        sign = "−" if value < 0 else ""
        return "{}{}".format(sign, _format_float_value(abs(value)))
    return str(value)


def _format_float_value(v: float) -> str:
    """Round to 4dp, emit shortest repr with no trailing zeros.

    ``38.20000000000001`` -> ``38.2``; ``120.0`` -> ``120``;
    ``0.21428571`` -> ``0.2143``. Mirrors flow-metrics's
    ``json.dumps(round(x, 4))`` shortest-repr approach but always returns
    a string (no quotes).
    """
    rounded = round(v, 4)
    if math.isinf(rounded) or math.isnan(rounded):
        # Caller is supposed to filter inf upstream (see _fmt_cell), but
        # be defensive — round(inf, 4) returns inf and json.dumps emits
        # "Infinity". Mirror the spec's Markdown rule.
        return "∞" if rounded > 0 else "−∞"
    # Integer-valued: drop the decimal portion entirely.
    if rounded == int(rounded):
        return str(int(rounded))
    # Non-integer: json.dumps emits shortest round-trip repr.
    return json.dumps(rounded)


def _fmt_percent(value: Any) -> str:
    """Format the percent column.

    Per spec lines 446-449: signed with one decimal; ``+0.0%`` for true
    zero; ``−`` for negative; ``±∞%`` for infinite.
    """
    if value is None:
        return "—"
    if isinstance(value, float) and math.isinf(value):
        return "+∞%" if value > 0 else "−∞%"
    # value is a decimal fraction; multiply by 100 for display.
    pct = float(value) * 100
    sign = "+" if value >= 0 else "−"
    return "{}{:.1f}%".format(sign, abs(pct))


# ---------------------------------------------------------------------------
# Markdown escape helper
# ---------------------------------------------------------------------------
def _md_escape(s: str) -> str:
    """Backslash-escape Markdown special characters in ``s``.

    Applied to user-supplied strings (scope/team names, basenames,
    sha values, upstream generated_at strings) before insertion into
    Markdown. Date strings and numeric cells use other code paths and
    are NOT routed through this helper — ASCII hyphen in ``2024-Q1``
    must pass through unchanged.
    """
    return s.translate(_MARKDOWN_ESCAPE_TABLE)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------
def _build_inputs_json(inputs: List[InputFile]) -> list[dict]:
    """Build the ``meta.inputs`` array.

    Sorted by basename codepoint-ascending (spec line 502). Each entry
    carries the per-file provenance fields the spec pins (lines 469-477).
    """
    out: list[dict] = []
    for inp in sorted(inputs, key=lambda i: i.basename):
        major, minor = inp.schema_version
        out.append(
            {
                "basename": inp.basename,
                "scope": dict(inp.scope),
                "scope_kind": inp.scope_kind,
                "window": {"from": inp.window_from, "to": inp.window_to},
                "generated_at": inp.meta.get("generated_at"),
                "state_config_sha": inp.meta.get("state_config_sha"),
                "issuetype_config_sha": inp.meta.get("issuetype_config_sha"),
                "schema_version": "{}.{}".format(major, minor),
            }
        )
    return out


def _build_per_scope_json(per_scope_rows: list) -> list[dict]:
    """Build the ``per_scope`` array. Sorted by canonical scope-repr.

    Each entry carries ``scope``, ``scope_kind``, ``scope_repr``, and
    the full ``aggregates`` dict for that scope. The full aggregate
    block (incl. all percentiles) is preserved — readers wanting per-
    percentile detail look here rather than at the Markdown.
    """
    rows = sorted(per_scope_rows, key=lambda r: r.get("scope_repr", ""))
    return [
        {
            "scope": dict(r.get("scope", {})),
            "scope_kind": r.get("scope_kind"),
            "scope_repr": r.get("scope_repr"),
            "aggregates": r.get("aggregates", {}),
        }
        for r in rows
    ]


def _round_floats(obj: Any) -> Any:
    """Recursively rebuild ``obj`` with every float rounded to 4dp.

    Mirrors :func:`flow_metrics.output._round_floats`: pre-walk because
    :func:`json.dumps`'s ``default=`` hook does not fire on floats.
    ``math.inf`` / ``-math.inf`` are passed through; ``json.dumps`` will
    serialize them as ``Infinity`` / ``-Infinity`` (Python's default,
    matched by :func:`json.loads`; non-standard JSON but the spec is
    silent on the inf representation in the sidecar). ``bool`` guarded
    before ``int`` so ``True`` does not serialize as ``1.0``.
    """
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return obj
        return round(obj, 4)
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v) for v in obj]
    if isinstance(obj, tuple):
        return [_round_floats(v) for v in obj]
    return obj


__all__ = [
    "SKILL_NAME",
    "SKILL_VERSION",
    "render_markdown",
    "render_json",
]
