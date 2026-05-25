"""T9 per-team rollup.

Buckets :class:`~flow_metrics.per_issue.PerIssueRow` instances by team
and runs T6's :func:`~flow_metrics.aggregate.aggregate` against each
bucket. For ``team_field.kind == "single_value"`` the buckets are
disjoint and ``sum(per_team[*].throughput) == aggregates.throughput``.
For ``team_field.kind == "array"`` the buckets overlap (an issue with
multiple teams is counted in each) and the meta-block carries
``per_team_double_counted: true`` so consumers can tell the rollup
sums to more than the global throughput by design.

Output rows are sorted by team name in **Unicode codepoint order** —
explicitly anti-locale. The contract test
``test_per_team_sort_uses_codepoint_order`` pins this with mixed-script
team names (``"Zebra"``, ``"Über-team"``, ``"alpha"``); plain
:func:`sorted` on strings is what produces the documented order.

Program-scope JQL composition lives here too: given the resolved team-id
list (from T9's :mod:`flow_metrics.align`), build the Jira-side query
that intersects the team field against those ids. Per spec § "Data
sources" v1 assumes one Jira ↔ one Jira Align instance pair, so the JQL
deliberately has no ``project = ...`` clause — the team field id is the
sole scope selector.

Field-level permission undercount: when an in-scope issue has no
readable ``team_field`` value (Jira's field-level security strips it),
its :class:`PerIssueRow` carries ``team == "(no team)"``. Those rows go
into a synthetic ``"(no team)"`` bucket so global aggregates still
reconcile with the per-team sum (for the ``single_value`` kind). The
count is surfaced through the duck-typed ``notes`` collector so T11 can
emit the spec's ``"per_team: N issues had no readable team_field
value; bucketed as '(no team)'"`` line.

``meta.per_team_double_counted`` is computed by :func:`per_team_double_counted`
and threaded into the output by T10. T9 sets the bool; T10 emits it.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from .aggregate import AggregateBlock, aggregate
from .config import StateConfig, TeamField
from .jql import compose_jql
from .per_issue import NO_TEAM, PerIssueRow


@dataclass(frozen=True)
class PerTeamRow:
    """One row of the ``per_team`` output array.

    Shape matches the spec's JSON example: ``{ "team": <name>,
    "aggregates": <AggregateBlock> }``. The ``aggregates`` value is the
    full T6 :class:`AggregateBlock` for the bucket — same shape as the
    top-level ``aggregates``, so downstream serializers can reuse the
    canonicalisation path on both.
    """

    team: str
    aggregates: AggregateBlock


# ---------------------------------------------------------------------------
# Bucketing
# ---------------------------------------------------------------------------
TeamsExtractor = Callable[[PerIssueRow], Sequence[str]]


def _default_teams_for_row(row: PerIssueRow) -> Sequence[str]:
    """Single-value default: ``row.team`` is already the canonical team
    name (or :data:`NO_TEAM` when the field was null / missing). Wrapping
    it in a one-element tuple lets :func:`bucket_by_team` treat single-
    value and array kinds with the same loop.
    """
    return (row.team,)


def bucket_by_team(
    rows: Iterable[PerIssueRow],
    team_field: Optional[TeamField],
    *,
    teams_for_row: Optional[TeamsExtractor] = None,
    notes: Any = None,
) -> Dict[str, List[PerIssueRow]]:
    """Bucket ``rows`` by team into ``{team_name: [rows]}``.

    Single-value semantics (``team_field.kind == "single_value"``, the
    default): each row lands in exactly one bucket — its
    :attr:`PerIssueRow.team`, or :data:`NO_TEAM` when the underlying
    field is null / missing. The buckets partition the in-scope rows
    exactly.

    Array semantics (``team_field.kind == "array"``): each row may land
    in multiple buckets. Callers supply ``teams_for_row`` to enumerate
    the row's team list (T5's per-issue derivation collapses array
    values to the first non-empty entry, so the full list lives on the
    caller side — usually a ``key -> [teams]`` lookup built while
    walking issues). If ``teams_for_row`` returns an empty sequence the
    row goes into :data:`NO_TEAM`.

    The input iterator is consumed exactly once — rows are materialised
    into per-bucket lists. For array semantics that means the same
    :class:`PerIssueRow` object can appear in several buckets'
    lists (intentional; the aggregator sees it once per bucket).

    Field-level permission undercount: every row that ends up in the
    :data:`NO_TEAM` bucket is counted, and ``notes`` is asked to record
    the total via ``notes.add_field_permission_undercount(field_id, n)``
    when ``notes`` is provided and ``n > 0``. ``notes`` is duck-typed —
    the T11 NotesCollector satisfies the interface; tests pass a
    ``MagicMock``.
    """
    # Array-kind footgun: PerIssueRow.team carries only the *first* team
    # for array-valued team fields (T5's _resolve_team collapses on the
    # way in). Without a teams_for_row callable to enumerate the full
    # list, bucket_by_team would silently degrade array kind to single-
    # value semantics — wrong throughput, missing overlap, no rationale
    # in the output. Refuse upfront so the caller is forced to thread
    # the team list through.
    if (
        teams_for_row is None
        and team_field is not None
        and team_field.kind == "array"
    ):
        raise ValueError(
            "bucket_by_team: team_field.kind='array' requires a teams_for_row "
            "callable; PerIssueRow.team carries only the first team for array "
            "fields (per T5), so the full team list must be supplied by the "
            "caller (e.g. from a key->teams lookup built while walking issues)."
        )

    extractor: TeamsExtractor = teams_for_row or _default_teams_for_row
    buckets: Dict[str, List[PerIssueRow]] = {}
    no_team_count = 0
    double_counted = 0

    for row in rows:
        # Filter out empties and de-duplicate within the row: if the
        # extractor returns the same team twice (e.g. an array Jira
        # field with redundant entries), the row must still land in
        # that team's bucket *once*, not twice — otherwise the team's
        # throughput is inflated for malformed upstream data.
        seen: set = set()
        team_names: List[str] = []
        for t in extractor(row):
            if not isinstance(t, str) or not t:
                continue
            if t in seen:
                continue
            seen.add(t)
            team_names.append(t)
        if not team_names:
            team_names = [NO_TEAM]
        if NO_TEAM in team_names:
            no_team_count += 1
        # An issue with two or more distinct teams is counted in each —
        # the "K issues belong to multiple teams" tally the spec asks
        # for. Post-dedupe so a redundant-entries fixture doesn't
        # inflate K either.
        if len(team_names) > 1:
            double_counted += 1
        for name in team_names:
            buckets.setdefault(name, []).append(row)

    if no_team_count and notes is not None:
        field_id = team_field.id if team_field is not None else None
        notes.add_field_permission_undercount(field_id, no_team_count)

    # Surface the per_team_double_counted note on array kind. We supply
    # the K count the spec asks for ("K issues belong to multiple teams
    # and are counted in each"); T11's NotesCollector renders the line.
    if (
        notes is not None
        and team_field is not None
        and team_field.kind == "array"
    ):
        notes.add_per_team_double_counted(double_counted)

    return buckets


# ---------------------------------------------------------------------------
# Per-team rollup
# ---------------------------------------------------------------------------
def per_team_rollup(
    buckets: Dict[str, List[PerIssueRow]],
    config: StateConfig,
    window: Any,
    *,
    include_subtasks: bool = False,
) -> List[PerTeamRow]:
    """Aggregate each team's bucket and return rows sorted by team name.

    Sort order is :func:`sorted`'s default — Python compares strings by
    Unicode codepoint, which is the documented spec contract. Locale-
    aware sorting (``locale.strcoll``) is explicitly off the table; the
    contract test pins the codepoint order with non-ASCII names so a
    future locale-driven rewrite is caught by CI.

    Aggregation is single-pass over each bucket — :func:`aggregate`
    consumes its iterator exactly once and the bucket list is fed via
    ``iter(...)``. ``include_subtasks`` is threaded through unchanged so
    each per-team block honours the same flag as the top-level run.
    """
    out: List[PerTeamRow] = []
    for team_name in sorted(buckets.keys()):
        # T6-API: aggregate(rows, window, config, *, include_subtasks=False).
        block = aggregate(
            iter(buckets[team_name]),
            window,
            config,
            include_subtasks=include_subtasks,
        )
        out.append(PerTeamRow(team=team_name, aggregates=block))
    return out


def per_team_double_counted(team_field: Optional[TeamField]) -> bool:
    """Compute ``meta.per_team_double_counted`` from the team_field config.

    ``True`` iff ``team_field.kind == "array"`` — the only kind where
    per_team rows overlap. T10 reads this value into the meta block; T9
    owns the definition so the trigger condition is documented in one
    place.
    """
    return team_field is not None and team_field.kind == "array"


# ---------------------------------------------------------------------------
# Program-scope JQL composition
# ---------------------------------------------------------------------------
def _format_team_id_for_jql(team_id: Any) -> str:
    """Render a team id as a JQL literal inside an ``IN`` clause.

    Numeric ids (typical Jira Align convention) need no quoting; non-
    numeric ids are double-quoted so embedded spaces don't break the
    parser. Boolean-ish or None values raise — they would otherwise
    serialise to ``"True"`` / ``"None"`` and silently match the wrong
    issues.
    """
    if team_id is None or isinstance(team_id, bool):
        raise ValueError("team id must be a non-null string or int; got {!r}".format(team_id))
    if isinstance(team_id, int):
        return str(team_id)
    if isinstance(team_id, str):
        if team_id == "":
            raise ValueError("team id must not be empty")
        if team_id.lstrip("-").isdigit():
            return team_id
        # Escape embedded double-quotes per Jira's JQL string-literal rules.
        return '"{}"'.format(team_id.replace("\\", "\\\\").replace('"', '\\"'))
    raise TypeError(
        "team id must be a str or int; got {}".format(type(team_id).__name__)
    )


def compose_program_scope_jql(
    team_field_id: str,
    team_ids: Sequence[Any],
    user_clause: Optional[str] = None,
) -> str:
    """Build the Jira-side JQL for a program / portfolio scope run.

    Form: ``"<team_field.id>" in (<team_a>, <team_b>, ...) ORDER BY key
    ASC`` with no ``project = ...`` clause — v1 assumes one Jira
    instance is paired with one Jira Align instance, so the team-field
    membership alone is enough to scope the fetch.

    The ``--jql`` user clause (if any) is merged via :func:`compose_jql`
    so the parenthesization and ``ORDER BY`` suffix follow the canonical
    rule shared with every other JQL the skill builds. (T8 owns the
    canonical helper; we route through it rather than reimplementing.)
    """
    # T8-API: compose_jql(scope, user, *, order_by_key=True) — canonical
    # parenthesization helper. Imported above; called below.
    if not isinstance(team_field_id, str) or not team_field_id:
        raise ValueError("team_field_id must be a non-empty string")
    # Materialise so emptiness can be tested even if a generator was
    # passed — ``bool(iter([]))`` is True and would slip past a naive
    # truthiness gate, silently producing the malformed JQL ``"f" in ()``.
    team_ids_list = list(team_ids)
    if not team_ids_list:
        raise ValueError(
            "compose_program_scope_jql: team_ids must contain at least one id; "
            "an empty IN () clause is rejected by Jira"
        )
    rendered = ", ".join(_format_team_id_for_jql(tid) for tid in team_ids_list)
    scope_clause = '"{}" in ({})'.format(team_field_id, rendered)
    return compose_jql(scope_clause, user_clause, order_by_key=True)


__all__ = [
    "PerTeamRow",
    "TeamsExtractor",
    "bucket_by_team",
    "compose_program_scope_jql",
    "per_team_double_counted",
    "per_team_rollup",
]
