"""T11 ``meta`` block builder.

Composes the meta dict T10's renderer splices into the canonical
output. Owns one upstream call — ``jira: whoami`` for ``meta.caller``
— and the spec-pinned omission rules (``cohort_jql`` absent when
unset, ``sources`` lex-sorted, ``metrics_requested`` in canonical
``--metrics`` order).

Scope rendering matches the spec example (§ "Outputs" line 374):
``{ "project": "PROJ", "team": "Foo" }`` for project scope (team
omitted when ``--team`` was not provided); ``{ "program_id": "42" }``
or ``{ "portfolio_id": "42" }`` for Jira Align scope. Mirrors the
``_format_scope`` CSV helper in :mod:`flow_metrics.output`.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .output import CANONICAL_METRICS_ORDER


# Per spec § "Outputs" line 382: schema_version is pinned at "1.0" for
# the v1 wire format. Future major versions bump this; T10's renderer
# does not interpret the value, so the bump is single-source-changeable
# here.
SCHEMA_VERSION = "1.0"


class CallerResolutionError(Exception):
    """``jira: whoami`` returned a payload with neither ``accountId``
    nor ``name`` — spec § "Permission undercounting" line 637-638 maps
    to exit 3 (``test_caller_unrecognized_whoami_exits_3``).

    Distinct from :class:`flow_metrics.upstream.JiraError`: the upstream
    subprocess exited zero but the payload shape is unusable. The CLI
    maps both to exit 3, but separating the exceptions keeps the error
    message pointing at the *right* failure mode (the spec test asserts
    the message mentions ``whoami``).
    """


def resolve_caller(whoami_payload: Any) -> str:
    """Pick the caller identifier from a ``jira: whoami`` response.

    Cloud responses carry ``accountId`` (24-char opaque); Server / Data
    Center responses carry ``name`` (username). If both are present,
    prefer ``accountId`` (spec § "Permission undercounting" line 637).
    If neither is present, raise :class:`CallerResolutionError` —
    the CLI maps to exit 3 with a message mentioning ``whoami`` so the
    user can tell which upstream call produced the bad shape.

    Accepts any mapping; the ``whoami`` payload is decoded JSON, which
    is a dict in practice but typed as ``Any`` to keep the function
    callable from sites that haven't yet shape-validated the payload.
    """
    if not isinstance(whoami_payload, Mapping):
        raise CallerResolutionError(
            "jira: whoami returned a non-object payload; expected an "
            "object with 'accountId' (Cloud) or 'name' (Server)"
        )
    account_id = whoami_payload.get("accountId")
    if isinstance(account_id, str) and account_id:
        return account_id
    name = whoami_payload.get("name")
    if isinstance(name, str) and name:
        return name
    raise CallerResolutionError(
        "jira: whoami returned an object with neither 'accountId' "
        "(Cloud) nor 'name' (Server); cannot identify the caller"
    )


def _format_scope(
    *,
    project: Optional[str] = None,
    team: Optional[str] = None,
    program_id: Optional[str] = None,
    portfolio_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the ``meta.scope`` dict matching the spec example shape.

    Exactly one of ``project`` / ``program_id`` / ``portfolio_id``
    should be set; the CLI's flag-combo validation (T1) already enforces
    that. ``team`` is only emitted on the project path and only when
    non-empty — an empty team is the same wire shape as no team for the
    test that pins meta.scope passthrough.
    """
    if project is not None:
        out: Dict[str, Any] = {"project": project}
        if team:
            out["team"] = team
        return out
    if program_id is not None:
        return {"program_id": program_id}
    if portfolio_id is not None:
        return {"portfolio_id": portfolio_id}
    return {}


def _format_window(window: Any) -> Dict[str, str]:
    """Render ``window`` as the ``{from, to}`` shape T10 emits.

    Accepts either a :class:`flow_metrics.Window` (the runtime type
    from T1) or a dict with ``from`` / ``to`` keys (tests). Date values
    serialise as ISO ``YYYY-MM-DD``; datetime values strip to date.
    """
    if isinstance(window, Mapping):
        return {"from": str(window.get("from", "")), "to": str(window.get("to", ""))}
    from_date = getattr(window, "from_date", None)
    to_date = getattr(window, "to_date", None)
    if from_date is None or to_date is None:
        raise ValueError(
            "build_meta: window must be a flow_metrics.Window or a "
            "mapping with 'from'/'to' keys"
        )
    return {
        "from": _iso_date(from_date),
        "to": _iso_date(to_date),
    }


def _iso_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _canonical_metrics(metrics: Sequence[str]) -> List[str]:
    """Sort+dedup ``metrics`` against the canonical ``--metrics`` order.

    Mirrors :func:`flow_metrics.output._sort_metrics_requested` (which
    runs again at emit time as a last-line defence). Unknown names are
    dropped silently so ``meta.metrics_requested`` never advertises a
    metric absent from ``aggregates`` — the renderer's filter is the
    single source of truth, and meta must stay consistent with it.
    """
    seen: set = set()
    out: List[str] = []
    canonical = list(CANONICAL_METRICS_ORDER)
    index = {m: i for i, m in enumerate(canonical)}
    for m in metrics:
        if m in index and m not in seen:
            seen.add(m)
            out.append(m)
    return sorted(out, key=lambda m: index[m])


def build_meta(
    *,
    caller: str,
    scope: Mapping[str, Any],
    window: Any,
    sources: Sequence[str],
    metrics_requested: Sequence[str],
    state_config_sha: str,
    issuetype_config_sha: str,
    generated_at: datetime,
    per_team_double_counted: bool,
    cohort_jql: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble the canonical ``meta`` dict.

    Keyword-only so callers can't accidentally swap ``state_config_sha``
    for ``issuetype_config_sha`` (same string type, opaque hash — any
    transposition would silently produce wrong-but-plausible output).

    Per-field rules:

    - ``caller`` — pre-resolved via :func:`resolve_caller`; the spec
      pins ``accountId`` on Cloud, ``name`` on Server.
    - ``scope`` — passes through as a mapping. Callers compose via
      :func:`_format_scope` when they have raw ``--project`` / team
      / ``--program-id`` / ``--portfolio-id`` values; pre-shaped dicts
      are also accepted so T1 can pass an existing ``args``-derived
      shape unmodified.
    - ``window`` — accepts a :class:`flow_metrics.Window` or a mapping
      with ``from`` / ``to`` keys; rendered as ``YYYY-MM-DD`` strings.
    - ``sources`` — lex-sorted at build time. T10 also sorts
      defensively, but pre-sorting keeps the on-wire shape obvious.
    - ``metrics_requested`` — canonical ``--metrics`` order, deduped,
      unknown names dropped (see :func:`_canonical_metrics`).
    - ``generated_at`` — ISO-8601 UTC string. Test fixtures
      historically use ``"2026-05-19T14:00:00Z"`` (spec example line
      380); we render via ``isoformat`` and append ``Z`` for naive UTC.
    - ``per_team_double_counted`` — set by T9; threaded through here.
    - ``cohort_jql`` — **omitted** when ``None`` or empty (spec § "Cohort
      behaviour" line 1128-1131). The key must be absent, not null, not
      "". T10's renderer also drops null / empty values; this is the
      first line of defence.
    """
    meta: Dict[str, Any] = {
        "caller": caller,
        "scope": dict(scope),
        "window": _format_window(window),
        "sources": sorted(sources),
        "metrics_requested": _canonical_metrics(metrics_requested),
        "state_config_sha": state_config_sha,
        "issuetype_config_sha": issuetype_config_sha,
        "generated_at": _iso_generated_at(generated_at),
        "schema_version": SCHEMA_VERSION,
        "per_team_double_counted": per_team_double_counted,
    }
    if cohort_jql is not None and isinstance(cohort_jql, str) and cohort_jql.strip() != "":
        meta["cohort_jql"] = cohort_jql
    return meta


def _iso_generated_at(value: datetime) -> str:
    """Render ``generated_at`` as ISO-8601 with a ``Z`` suffix for UTC.

    Naive datetimes are treated as UTC (the rest of the skill normalises
    to UTC at boundary; spec § Decisions line 1374: "Time zones: UTC
    throughout"). Tz-aware datetimes serialise via ``isoformat`` and the
    offset is normalised to ``Z`` when the offset is zero — matching the
    spec example ``"2026-05-19T14:00:00Z"``.
    """
    if not isinstance(value, datetime):
        return str(value)
    if value.tzinfo is None:
        return value.isoformat() + "Z"
    iso = value.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


__all__ = [
    "SCHEMA_VERSION",
    "CallerResolutionError",
    "build_meta",
    "resolve_caller",
]
