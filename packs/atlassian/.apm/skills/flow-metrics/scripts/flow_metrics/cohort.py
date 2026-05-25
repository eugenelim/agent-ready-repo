"""T8 cohort split — `--cohort-jql` resolution + `cohort_breakdown`.

Implements docs/specs/flow-metrics.md § "Cohort behaviour":

- :func:`resolve_cohort_keys` issues exactly one ``jira: search`` for
  ``(scope) AND (cohort_jql) ORDER BY key ASC`` and returns the matching
  issue-key set. No window clause is added — intersection against the
  main fetch's in-scope rows happens at tagging time, per spec.
- :func:`tag_cohort` stamps each :class:`PerIssueRow` with a
  ``cohort: bool`` derived from set membership in the resolved key set.
- :func:`aggregate_cohort` filters tagged rows by the ``cohort`` flag
  and runs T6's :func:`aggregate` on the subset. The cohort-restricted
  denominators (throughput, rework_rate, flow_distribution) follow
  automatically: the subset has its own throughput and its own backward-
  edge sum, so ``rework_rate = cohort_edges / cohort_throughput`` and
  ``flow_distribution.denominator`` covers only cohort delivered-in-
  window issues (incl subtasks — same ``--include-subtasks`` semantics
  as the main aggregate).
- :func:`build_cohort_breakdown` is the orchestration entry point:
  materialise the (already-tagged) rows once, then emit the
  ``{"cohort": AggregateBlock, "control": AggregateBlock}`` pair. When
  the resolved cohort set is disjoint from in-scope rows, the duck-
  typed ``notes`` collector is asked to record the empty-cohort note
  (T11 owns the wording).
- :func:`cohort_meta` is the meta-block helper T10 will call: returns a
  one-key dict when ``--cohort-jql`` was set, empty dict otherwise.
  Locked in here because the spec contract-tests "meta.cohort_jql is
  omitted entirely when --cohort-jql is absent".

JQL composition (scope, cohort, align filter) routes through
:func:`flow_metrics.jql.compose_jql` — never string-concat manually.
That helper is the canonical iteration-order anchor and the
parenthesization contract is locked in there.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Set

from .aggregate import AggregateBlock, aggregate
from .config import StateConfig
from .jql import compose_jql
from .per_issue import PerIssueRow
from .upstream import JiraClient


# Minimal field set for the cohort search: we only need the issue keys.
# ``summary`` is requested as a defensive "non-empty fields list" so a
# future ``jira`` skill that rejects an empty ``--fields`` keeps working.
_COHORT_SEARCH_FIELDS = "summary"


def resolve_cohort_keys(
    jira: JiraClient,
    cohort_jql: str,
    scope: str,
) -> Set[str]:
    """Return the set of issue keys matching ``(scope) AND (cohort_jql)``.

    Issues exactly one ``jira: search`` call. The composed JQL ends in
    ``ORDER BY key ASC`` — :func:`compose_jql` is the canonical iteration-
    order anchor and applies the suffix uniformly to every JQL the skill
    builds, even when (as here) the call site returns a set.

    No window clause is added. Cohort membership is a property of the
    issue, not of the window; the main fetch's in-scope rows define the
    intersection point at tagging time.

    Raises :class:`ValueError` on an empty / whitespace ``cohort_jql``.
    Without that guard, :func:`compose_jql`'s no-user-clause branch
    would yield scope-only JQL and silently mark every in-scope issue
    ``cohort=True`` — plausible-looking output with the cohort/control
    split inverted. Callers gate on ``--cohort-jql`` being set; this
    raise is the building-block's last-line defence.
    """
    if cohort_jql is None or cohort_jql.strip() == "":
        raise ValueError(
            "resolve_cohort_keys: cohort_jql must be a non-empty JQL expression"
        )
    full_jql = compose_jql(scope, cohort_jql, order_by_key=True)
    keys: Set[str] = set()
    for issue in jira.search(full_jql, fields=_COHORT_SEARCH_FIELDS):
        key = issue.get("key") if isinstance(issue, dict) else None
        if isinstance(key, str) and key:
            keys.add(key)
    return keys


def tag_cohort(
    rows: Iterable[PerIssueRow],
    cohort_keys: Set[str],
) -> Iterator[PerIssueRow]:
    """Yield rows after stamping ``row.cohort = (row.key in cohort_keys)``.

    Mutates each :class:`PerIssueRow` in place (dataclass field is not
    frozen). Callers iterating ``cache_read`` output land on freshly
    materialised rows where the cohort field starts ``None``; this
    helper is the one place that flips it to a definite ``True`` /
    ``False`` for every in-scope row.
    """
    for row in rows:
        row.cohort = row.key in cohort_keys
        yield row


def aggregate_cohort(
    rows: Iterable[PerIssueRow],
    cohort: bool,
    config: StateConfig,
    window: Any,
    *,
    include_subtasks: bool = False,
) -> AggregateBlock:
    """Aggregate the subset of ``rows`` whose ``cohort`` flag matches.

    Wraps T6's :func:`aggregate` against a generator that filters by
    ``row.cohort``. The subset carries its own throughput and backward-
    edge totals, so the spec's "denominator-restricted" cohort metrics
    fall out for free: ``rework_rate`` divides by the cohort throughput,
    ``flow_distribution.denominator`` counts the cohort's delivered-in-
    window issues, etc.

    Uses strict ``is`` comparison: untagged rows (``cohort is None``)
    match neither the cohort nor the control subset and are dropped.
    That's load-bearing — callers must run :func:`tag_cohort` first;
    silently bucketing untagged rows as "control" would invert the
    cohort/control split when cohort tagging was skipped by mistake.
    """
    subset = (r for r in rows if r.cohort is cohort)
    # T6-API: aggregate(rows, window, config, *, include_subtasks=False).
    return aggregate(subset, window, config, include_subtasks=include_subtasks)


def build_cohort_breakdown(
    rows: Iterable[PerIssueRow],
    cohort_keys: Set[str],
    config: StateConfig,
    window: Any,
    notes: Any,
    *,
    include_subtasks: bool = False,
) -> Dict[str, AggregateBlock]:
    """Tag ``rows`` and emit ``{"cohort": ..., "control": ...}``.

    Materialises the row stream once (two passes are required —
    cohort+control — and the source is single-pass). For very large
    runs T10 may replace this with a T7 ``read_cache`` re-iteration to
    avoid the materialisation; the interface is identical either way.

    When the resolved cohort set is disjoint from the in-scope rows
    (i.e. zero tagged rows have ``cohort=True``), ``notes`` is asked to
    record the empty-cohort note. ``notes`` is duck-typed — the T11
    :class:`NotesCollector` will satisfy the interface, but tests pass
    a ``MagicMock()`` and assert the call.
    """
    materialised: List[PerIssueRow] = list(tag_cohort(rows, cohort_keys))
    cohort_rows = [r for r in materialised if r.cohort]
    control_rows = [r for r in materialised if not r.cohort]

    if not cohort_rows:
        notes.add_empty_cohort()

    # T6-API: aggregate(rows, window, config, *, include_subtasks=False).
    cohort_block = aggregate(
        iter(cohort_rows), window, config, include_subtasks=include_subtasks
    )
    control_block = aggregate(
        iter(control_rows), window, config, include_subtasks=include_subtasks
    )
    return {"cohort": cohort_block, "control": control_block}


def cohort_meta(cohort_jql: Optional[str]) -> Dict[str, str]:
    """Return a meta-block fragment carrying ``cohort_jql`` when set.

    Empty dict when ``--cohort-jql`` was not provided (None or empty
    string). The spec contract-test ``test_meta_cohort_jql_omitted_when
    _absent`` pins this: the key must be missing, not null, not empty.
    T10 merges the returned dict into the top-level ``meta`` object.
    """
    if cohort_jql is None or cohort_jql.strip() == "":
        return {}
    return {"cohort_jql": cohort_jql}


__all__ = [
    "aggregate_cohort",
    "build_cohort_breakdown",
    "cohort_meta",
    "resolve_cohort_keys",
    "tag_cohort",
]
