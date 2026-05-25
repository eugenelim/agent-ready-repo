"""T11 notes collector.

Buffers note strings emitted opportunistically by T5/T6/T8/T9 during a
run, then :meth:`finalize` returns the lex-sorted list T10's renderer
splices into the canonical output.

Wording rules pinned by docs/specs/flow-metrics.md § "Outputs" (the
``notes`` array in the JSON example, lines 434-444) and the Decisions
section. Where the spec gives a verbatim example string, it is
reproduced exactly. Where the spec only describes the contract (e.g.
empty-cohort) the wording is this module's call and the PR description
flags it for review.

Dedup is by **full final string**, not by counter-method-name: two calls
to ``add_cancelled(5)`` produce one notes line. Two calls to
``add_cancelled(5)`` then ``add_cancelled(3)`` produce TWO lines (the
caller's responsibility — at the collector layer both inputs render
strings and both are kept). The spec's intent is that callers accumulate
counts before emitting, not that the collector merges.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from typing import List, Optional


# Sentinel default for the rare add_* method whose wording the spec does
# not pin verbatim — kept as a module constant so the test that asserts
# the spec-example wording has a single source of truth.
_CANCELLED_TEMPLATE = (
    "{n} issues cancelled in window; excluded from throughput, "
    "cycle_time, lead_time, flow_efficiency, and flow_distribution."
)
_SKIPPED_COMMITMENT_TEMPLATE = (
    "{n} delivered without commitment-state entry; excluded from cycle_time."
)
_ZERO_DENOMINATOR_TEMPLATE = (
    "{n} cycle-eligible issues had zero (active_t + wait_t); "
    "excluded from flow_efficiency."
)
_UNMAPPED_ISSUETYPE_TEMPLATE = (
    "{n} issues had unmapped issuetype '{name}'; bucketed as 'other'."
)
_PERMISSION_UNDERCOUNT_TEMPLATE = (
    "permissions: {n} issues in project are inaccessible to the caller "
    "and are silently excluded."
)
_FIELD_PERMISSION_UNDERCOUNT_TEMPLATE = (
    "per_team: {n} issues had no readable team_field value; "
    "bucketed as '(no team)'."
)
_WINDOW_EDGE_TEMPLATE = (
    "{n} issues entered in-progress before window start and are "
    "included in lead-time computation."
)
_FLOW_LOAD_SAMPLE_TEMPLATE = "flow_load: {n} samples, weekends {policy}."
_DEFECT_RATIO_DISCLAIMER_LINES = (
    "defect_ratio is not Change Failure Rate; see spec §Out of scope.",
    "defect_ratio uses flow_distribution denominator; throughput "
    "excludes subtasks (override: --include-subtasks).",
)
_EMPTY_COHORT_LINE = (
    "cohort: --cohort-jql matched zero in-scope issues; "
    "cohort_breakdown.cohort metrics are empty."
)
_PER_TEAM_DOUBLE_COUNTED_TEMPLATE = (
    "per_team: {n} issues belong to multiple teams and are counted "
    "in each team's row."
)


class NotesCollector:
    """Append-and-dedup buffer for notes-block strings.

    Each ``add_*`` method renders one (or, for the defect-ratio
    disclaimer, two) string(s) and appends them iff not already present.
    :meth:`finalize` returns a freshly-sorted copy each call so the
    collector remains non-destructive — T10's renderer also sorts
    defensively (spec § "Output canonicalization"); both layers must be
    idempotent under repeated calls.
    """

    def __init__(self) -> None:
        # ``list + set`` rather than just a set because insertion order
        # is occasionally useful in debug prints; the dedup guarantee is
        # what the contract pins, not the in-memory order (which
        # :meth:`finalize` sorts away regardless).
        self._notes: List[str] = []
        self._seen: set = set()

    def _append(self, line: str) -> None:
        if line in self._seen:
            return
        self._seen.add(line)
        self._notes.append(line)

    # ------------------------------------------------------------------
    # Spec-pinned add methods
    # ------------------------------------------------------------------
    def add_cancelled(self, n: int) -> None:
        """Single line listing all five metrics cancelled-in-window
        issues are excluded from (spec § "Outputs" line 439)."""
        self._append(_CANCELLED_TEMPLATE.format(n=n))

    def add_skipped_commitment(self, n: int) -> None:
        """Delivered-in-window but no commitment_state entry — excluded
        from cycle_time (spec § Metric correctness line 998-999)."""
        self._append(_SKIPPED_COMMITMENT_TEMPLATE.format(n=n))

    def add_zero_denominator_flow_eff(self, n: int) -> None:
        """Cycle-eligible but ``active_t + wait_t == 0`` — excluded
        from flow_efficiency (spec § "Outputs" line 437)."""
        self._append(_ZERO_DENOMINATOR_TEMPLATE.format(n=n))

    def add_unmapped_issuetype(self, name: str, n: int) -> None:
        """One line per distinct unmapped issuetype name (spec § "Outputs"
        line 436). Callers tally per-name before calling — two calls
        with the same name+n collapse via dedup; with same name+different
        n produce TWO lines (caller bug)."""
        self._append(_UNMAPPED_ISSUETYPE_TEMPLATE.format(n=n, name=name))

    def add_permission_undercount(self, n: int) -> None:
        """Project-scope permission undercount: ``jira: get-project``
        reports a higher total than the in-scope JQL (spec § "Permission
        undercounting" line 642-643)."""
        self._append(_PERMISSION_UNDERCOUNT_TEMPLATE.format(n=n))

    def add_field_permission_undercount(self, field: Optional[str], n: int) -> None:
        """N in-scope issues had no readable team_field value (spec §
        "Permission undercounting" line 647-656). ``field`` is the
        team_field id for diagnostics; the spec wording does not embed
        the field id, but we accept it so call sites stay informative
        if the wording changes."""
        del field  # spec wording does not embed the field id today
        self._append(_FIELD_PERMISSION_UNDERCOUNT_TEMPLATE.format(n=n))

    def add_window_edge_count(self, n: int) -> None:
        """Issues that entered in-progress before window start (spec §
        "Outputs" line 435)."""
        self._append(_WINDOW_EDGE_TEMPLATE.format(n=n))

    def add_flow_load_sample_count(self, n: int, weekend_policy: str = "included") -> None:
        """Sample count + weekend policy line (spec § "Outputs" line 442;
        Metric correctness ``test_flow_load_weekend_inclusion_recorded``).
        v1 always emits ``"weekends included"`` because business-day-only
        Flow Load is deferred to v2 (spec § "Deferred to v2" line 1523);
        the parameter is kept so the v2 wiring is a one-arg change."""
        self._append(
            _FLOW_LOAD_SAMPLE_TEMPLATE.format(n=n, policy=weekend_policy)
        )

    def add_defect_ratio_disclaimer(self) -> None:
        """Spec emits **two** disclaimer lines (lines 440-441): the CFR-
        disambiguation and the denominator clarification. We add both
        from one call site to keep the disclaimer pair atomic."""
        for line in _DEFECT_RATIO_DISCLAIMER_LINES:
            self._append(line)

    def add_empty_cohort(self) -> None:
        """``--cohort-jql`` matched zero in-scope issues. Spec § "Cohort
        behaviour" test ``test_empty_cohort_does_not_exit_nonzero`` pins
        the behaviour (no exit) but not the wording — this string is
        T11's call (flagged in PR)."""
        self._append(_EMPTY_COHORT_LINE)

    def add_per_team_double_counted(self, n: int) -> None:
        """K issues belong to more than one team (array team_field kind)
        and are counted in each team's per_team row. Spec § "Outputs"
        line 230-233 mentions the note but doesn't quote it verbatim;
        wording matches the test fixture in T9's
        ``test_per_team_array_kind_double_count_flagged``."""
        self._append(_PER_TEAM_DOUBLE_COUNTED_TEMPLATE.format(n=n))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def finalize(self) -> List[str]:
        """Return a fresh lex-sorted copy of the notes buffer.

        Non-destructive: repeated calls return equivalent lists; the
        collector remains usable for further add_* calls (subsequent
        finalize calls reflect them). T10's renderer also sorts
        defensively at emit time; both passes must be idempotent.
        """
        return sorted(self._notes)


__all__ = ["NotesCollector"]
