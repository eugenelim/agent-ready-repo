"""Notes-string formatter.

Every ``notes`` entry the report emits goes through one of :class:`Note`'s
factory methods. Centralising the wording prevents drift across the
modes (baseline, cohort, program) and keeps the spec-literal strings in
one auditable place.

The factories are pure formatters — they return strings. Buffering and
sorting live in a higher layer (the modes and program-discovery report
assembly), mirroring the ``flow_metrics.notes`` collector-vs-formatter
split.

Note wording is pinned here as the single source of truth for each
note string emitted by the report.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from typing import Iterable, List, Tuple


class Note:
    """Spec-literal note-string factories.

    Each ``@classmethod`` renders one entry exactly as the spec pins it.
    Where the spec gives a verbatim example the wording is reproduced;
    later layers (modes, program discovery, aggregation) only fill in
    the stubbed methods, never invent new wording outside this class.
    """

    # ------------------------------------------------------------------
    # Emitted during input loading
    # ------------------------------------------------------------------
    @classmethod
    def mixed_major_schema_versions(
        cls,
        versions_and_basenames: Iterable[Tuple[int, str]],
    ) -> str:
        """Note for mixed major schema versions: ``"mixed-major-schema-versions:
        <list of distinct majors and their input basenames>"``.

        Accepts an iterable of ``(major, basename)`` pairs. Groups by
        major (ascending), sorts basenames lex within each group, and
        renders ``"<major> (<basename>, <basename>)"`` segments joined
        by ``", "``. The prefix is fixed; this format keeps the output
        stable across runs (deterministic sort) and human-readable.

        Raises ``ValueError`` on empty input or a single-major input.
        The spec only emits this note when majors disagree; calling
        with one or zero majors is a caller bug.
        ``inputs.collect_mixed_major_note`` is the canonical caller and
        already short-circuits in those cases.
        """
        groups: dict[int, list[str]] = {}
        for major, basename in versions_and_basenames:
            groups.setdefault(int(major), []).append(str(basename))
        if len(groups) < 2:
            raise ValueError(
                "Note.mixed_major_schema_versions requires >=2 distinct "
                "majors; got {}".format(sorted(groups))
            )
        parts: List[str] = []
        for major in sorted(groups):
            basenames = sorted(set(groups[major]))
            parts.append("{} ({})".format(major, ", ".join(basenames)))
        return "mixed-major-schema-versions: " + ", ".join(parts)

    # ------------------------------------------------------------------
    # Emitted by the file-consumer modes (baseline + cohort)
    # ------------------------------------------------------------------
    @classmethod
    def config_sha_drift(cls, sha_name: str, a: str, b: str) -> str:
        """Config-SHA drift note: ``"config-sha-drift: <sha_name> <a> → <b>"``.

        ``sha_name`` is ``"state_config_sha"`` or ``"issuetype_config_sha"``.
        """
        return "config-sha-drift: {} {} → {}".format(sha_name, a, b)

    @classmethod
    def cohort_jql_mismatch(cls, a_jql: str, b_jql: str) -> str:
        """Cohort JQL mismatch note: ``"cohort-jql-mismatch: <baseline-jql>
        vs <current-jql>; cohort breakdown comparison omitted"``."""
        return (
            "cohort-jql-mismatch: {} vs {}; cohort breakdown comparison "
            "omitted".format(a_jql, b_jql)
        )

    @classmethod
    def cohort_breakdown_absent_noop(cls, basenames: Iterable[str]) -> str:
        """``--include-cohort-breakdown`` set in baseline mode but at least
        one input lacks ``cohort_breakdown``; the flag no-ops.

        Literal form:
        ``"cohort-breakdown-absent: cohort_breakdown missing from
        <comma-sep basenames sorted codepoint-ascending>;
        --include-cohort-breakdown no-op"``.
        """
        names = sorted(set(str(b) for b in basenames))
        if not names:
            raise ValueError(
                "Note.cohort_breakdown_absent_noop requires >=1 basename"
            )
        return (
            "cohort-breakdown-absent: cohort_breakdown missing from {}; "
            "--include-cohort-breakdown no-op".format(", ".join(names))
        )

    @classmethod
    def per_team_ignored_in_baseline(cls, basename: str) -> str:
        """Per-team ignored note: ``"per_team data present in <file>;
        ignored in baseline mode (use program mode for multi-team
        rollup)"``."""
        return (
            "per_team data present in {}; ignored in baseline mode "
            "(use program mode for multi-team rollup)".format(basename)
        )

    # ------------------------------------------------------------------
    # Emitted by program-mode input discovery — dedupe, overlap, per_team
    # ------------------------------------------------------------------
    @classmethod
    def per_team_cohort_deferred(cls, n_rows: int) -> str:
        """Per-team cohort deferred note. Literal form:
        ``"per_team-cohort-deferred: N flattened per-team rows have no
        cohort_breakdown; excluded from cohort rollup"``.

        Program discovery emits this only when ``--include-cohort-breakdown`` is set
        and at least one per_team-flattened row exists (n_rows > 0).
        ``n_rows`` is the count of ``from_per_team=True`` rows in
        :class:`ProgramInputs.scopes`.
        """
        return (
            "per_team-cohort-deferred: {} flattened per-team rows have no "
            "cohort_breakdown; excluded from cohort rollup".format(n_rows)
        )

    @classmethod
    def per_team_double_counted(cls, basenames: Iterable[str]) -> str:
        """Per-team double-counted note. Literal form:
        ``"per_team-double-counted: <comma-separated input basenames
        whose meta.per_team_double_counted is true, sorted
        codepoint-ascending>; flattened per-team rows may double-count
        issues that span multiple teams"`` (one entry covering all such
        inputs).

        ``basenames`` need not be pre-sorted; the factory sorts
        codepoint-ascending so callers can pass any iterable.
        """
        sorted_names = sorted(set(basenames))
        if not sorted_names:
            raise ValueError(
                "Note.per_team_double_counted requires at least one basename"
            )
        return (
            "per_team-double-counted: {}; flattened per-team rows may "
            "double-count issues that span multiple teams".format(
                ", ".join(sorted_names)
            )
        )

    @classmethod
    def duplicate_scope(
        cls,
        scope: dict,
        sources: Iterable[Tuple[str, bool]],
    ) -> str:
        """Duplicate scope error. Literal form:
        ``"duplicate scope in input set: <scope dict> in <basename-a>
        and <basename-b>"``.

        Exits 2; the report never emits this as a soft note, but the
        wording lives here so the error message has a single source of
        truth.

        ``sources`` is an iterable of ``(basename, from_per_team)``
        tuples. ``from_per_team=True`` basenames are annotated with
        ``" (per_team flattened)"`` to distinguish a post-flatten
        collision from a pre-flatten duplicate of
        two explicit inputs. The annotation deliberately omits the
        source's parent kind (program/portfolio/project+team) because
        the per_team flattening path admits all three; the source's
        identity is the basename, which is already in the message.

        The factory sorts sources by basename codepoint-ascending; if
        more than two are present, every basename is listed.
        ``<scope dict>`` is rendered with keys sorted so the message is
        stable across Python dict-order accidents.
        """
        items = sorted(sources, key=lambda s: s[0])
        if len(items) < 2:
            raise ValueError(
                "Note.duplicate_scope requires at least two sources; got {}".format(
                    items
                )
            )
        labels = [
            "{} (per_team flattened)".format(b) if from_per_team else b
            for b, from_per_team in items
        ]
        if len(labels) == 2:
            joined = "{} and {}".format(labels[0], labels[1])
        else:
            joined = "{}, and {}".format(", ".join(labels[:-1]), labels[-1])
        sorted_scope = {k: scope[k] for k in sorted(scope)}
        return "duplicate scope in input set: {} in {}".format(
            sorted_scope, joined
        )

    @classmethod
    def overlapping_scopes(
        cls,
        pairs: Iterable[Tuple[Tuple[dict, str], Tuple[dict, str]]],
    ) -> str:
        """Overlapping scopes error. Exit 2 listing the overlapping scopes.
        Literal form:

        ``"overlapping scopes in input set: <a-basename> (<a-scope>) "
        "overlaps <b-basename> (<b-scope>); ..."``

        ``pairs`` is an iterable of ``((scope_a, basename_a),
        (scope_b, basename_b))`` tuples. Multiple overlaps are joined
        with ``"; "`` so a single error names every offending pair.
        """
        items = list(pairs)
        if not items:
            raise ValueError(
                "Note.overlapping_scopes requires at least one pair"
            )

        def _pair_str(pair):
            (scope_a, basename_a), (scope_b, basename_b) = pair
            sa = {k: scope_a[k] for k in sorted(scope_a)}
            sb = {k: scope_b[k] for k in sorted(scope_b)}
            return "{} ({}) overlaps {} ({})".format(
                basename_a, sa, basename_b, sb
            )

        return "overlapping scopes in input set: " + "; ".join(
            _pair_str(p) for p in items
        )

    # ------------------------------------------------------------------
    # Emitted by program-mode aggregation
    # ------------------------------------------------------------------
    @classmethod
    def aggregation_zero_denominator(cls, metric: str, side: str) -> str:
        """Aggregation zero denominator note. Zero denominator causes
        the cell to render as em-dash. Literal form:
        ``"aggregation-zero-denominator: <metric>; weighted-average
        undefined (total weight is zero on <side>)"``.

        ``side`` is one of ``"non-cohort"`` / ``"cohort"`` / ``"control"``
        — the rollup side whose denominator collapsed to zero. The
        aggregation engine fills in the side label at the call site.
        """
        return (
            "aggregation-zero-denominator: {}; weighted-average undefined "
            "(total weight is zero on {})".format(metric, side)
        )

    @classmethod
    def median_of_medians_approximation(cls) -> str:
        """Median-of-medians approximation note. Program-mode reports emit
        this once to flag that distribution aggregates are approximations;
        readers should inspect per-scope rows for honest distribution detail.

        Literal form:
        ``"median-of-medians-approximation: distribution aggregates
        (cycle_time/lead_time/flow_time/flow_efficiency) computed as
        median-of-medians across scopes; see per-scope rows for
        distribution detail"``. One note per report, not per metric.
        """
        return (
            "median-of-medians-approximation: distribution aggregates "
            "(cycle_time/lead_time/flow_time/flow_efficiency) computed as "
            "median-of-medians across scopes; see per-scope rows for "
            "distribution detail"
        )

    @classmethod
    def cohort_breakdown_missing(
        cls,
        missing_basenames: Iterable[str],
        total: int,
    ) -> str:
        """Cohort breakdown missing note. Literal form:
        ``"cohort-breakdown-missing: N of M scopes (basenames: a.json,
        b.json); cohort rollup computed over the remaining M-N"``.

        ``missing_basenames`` is the set of source basenames whose scopes
        had no ``cohort_breakdown`` block. ``total`` is the number of
        scopes considered (M). Basenames are sorted codepoint-ascending
        and deduplicated (a single source basename may have produced
        multiple per_team-flattened scopes; we list it once).
        """
        names = sorted(set(str(b) for b in missing_basenames))
        if not names:
            raise ValueError(
                "Note.cohort_breakdown_missing requires >=1 basename"
            )
        n = len(names)
        remaining = total - n
        return (
            "cohort-breakdown-missing: {} of {} scopes (basenames: {}); "
            "cohort rollup computed over the remaining {}".format(
                n, total, ", ".join(names), remaining
            )
        )

    @classmethod
    def cohort_breakdown_section_empty(cls) -> str:
        """Cohort breakdown section empty note. Literal form: ``"cohort-breakdown-section-empty"``."""
        return "cohort-breakdown-section-empty"

    @classmethod
    def cohort_flow_distribution_missing(
        cls,
        side: str,
        missing_basenames: Iterable[str],
        total: int,
    ) -> str:
        """Cohort flow_distribution missing note. Literal form:
        ``"cohort-flow_distribution-missing: side=<cohort|control>
        dropped N of M scopes (basenames: a.json, b.json); defect_ratio
        and flow_distribution rollups computed over the remaining M-N"``.

        Basenames sorted codepoint-ascending and deduplicated.
        """
        names = sorted(set(str(b) for b in missing_basenames))
        if not names:
            raise ValueError(
                "Note.cohort_flow_distribution_missing requires >=1 basename"
            )
        n = len(names)
        remaining = total - n
        return (
            "cohort-flow_distribution-missing: side={} dropped {} of {} "
            "scopes (basenames: {}); defect_ratio and flow_distribution "
            "rollups computed over the remaining {}".format(
                side, n, total, ", ".join(names), remaining
            )
        )

    @classmethod
    def mixed_cohort_jql(
        cls,
        jqls_and_basenames: Iterable[Tuple[str, Iterable[str]]],
    ) -> str:
        """Mixed cohort JQL note. Literal form:
        ``"mixed-cohort-jql: <list of distinct JQLs and their input
        basenames>; rollup proceeds but cohort definitions differ across
        scopes"``.

        ``jqls_and_basenames`` is an iterable of ``(jql,
        list_of_basenames)`` pairs. Distinct JQLs are sorted
        codepoint-ascending; the basenames within each group are also
        sorted codepoint-ascending. Each entry renders as ``"<jql>
        (<basename>, <basename>)"`` joined by ``"; "``.
        """
        entries = []
        for jql, basenames in jqls_and_basenames:
            names = sorted(set(str(b) for b in basenames))
            entries.append((str(jql), names))
        if len(entries) < 2:
            raise ValueError(
                "Note.mixed_cohort_jql requires >=2 distinct JQLs; got {}".format(
                    [e[0] for e in entries]
                )
            )
        entries.sort(key=lambda kv: kv[0])
        parts = [
            "{} ({})".format(jql, ", ".join(names)) for jql, names in entries
        ]
        return (
            "mixed-cohort-jql: " + "; ".join(parts) + "; rollup proceeds but "
            "cohort definitions differ across scopes"
        )

    # ------------------------------------------------------------------
    # Emitted by the delta engine (compute_deltas note factories)
    # ------------------------------------------------------------------
    @classmethod
    def metric_absent(cls, metric: str, side_label: str) -> str:
        """Metric absent note: ``"<metric> absent in <file>; cell omitted"``.

        The delta engine calls this when a metric key is present on one
        side of the comparison but missing on the other. ``side_label``
        is the per-side label supplied to :func:`compute_deltas`
        (``"baseline"`` / ``"current"`` / ``"cohort"`` / ``"control"`` /
        a basename in program-mode rollups) — the delta engine has no
        access to filenames, so the caller pre-resolves ``<file>`` into
        the label.
        """
        return "{} absent in {}; cell omitted".format(metric, side_label)

    @classmethod
    def metric_null_on_one_side(cls, metric: str, side_label: str) -> str:
        """Metric null on one side: ``"<metric> null in <which-side> for <scope>"``.

        The delta engine does not know the scope (it operates on raw
        aggregate dicts), so it emits the leading clause only. The modes
        or aggregation engine may later wrap or rewrite if they want to
        thread the scope through; the stable wording lives here.
        """
        return "{} null in {}".format(metric, side_label)

    @classmethod
    def metric_zero_both_sides(cls, metric: str) -> str:
        """Metric zero on both sides: ``"<metric> zero on both sides; percent
        delta undefined"``."""
        return "{} zero on both sides; percent delta undefined".format(metric)

    @classmethod
    def n_differs(
        cls,
        metric: str,
        n_a: int,
        n_b: int,
        side_labels: Tuple[str, str],
    ) -> str:
        """N-differs note (per-side ``n`` differs by more than 10%,
        or zero on either side).

        Records the per-side ``n`` values when they differ by more than 10%.
        Literal form:
        ``"n-differs: <metric> n=<n_a> in <a_label>, n=<n_b> in <b_label>
        (>10% delta)"``.
        """
        a_label, b_label = side_labels
        return (
            "n-differs: {} n={} in {}, n={} in {} (>10% delta)".format(
                metric, n_a, a_label, n_b, b_label
            )
        )


__all__ = ["Note"]
