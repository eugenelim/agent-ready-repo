#!/usr/bin/env python3
"""flow-metrics CLI entry point.

T1 scaffold: argparse, version guard, window resolution, path safety,
flag-combo validation. Every command path is a stub that prints
"not yet implemented" and exits 0. Later tasks fill in the actual work.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Sequence

PYTHON_FLOOR = (3, 10)

EXIT_OK = 0
EXIT_USER_ABORT = 1
EXIT_VALIDATION = 2
EXIT_UPSTREAM = 3


def _check_python_version(version_info=None) -> None:
    info = version_info if version_info is not None else sys.version_info
    if (info[0], info[1]) < PYTHON_FLOOR:
        floor = ".".join(str(x) for x in PYTHON_FLOOR)
        have = ".".join(str(info[i]) for i in range(min(3, len(info))))
        print(
            "flow-metrics requires Python {} or later; running under {}".format(floor, have),
            file=sys.stderr,
        )
        sys.exit(EXIT_VALIDATION)


# Run guard BEFORE internal imports so any 3.10+ syntax in sibling modules
# (T2+: config.py, upstream.py, ...) only parses on a supported interpreter.
# The stdlib imports above are 3.7-safe; siblings below need the guard
# to print a friendly message instead of a SyntaxError on 3.9 and older.
_check_python_version()

from . import clock  # noqa: E402  (intentionally after version guard)
from .jql import compose_jql as compose_jql  # noqa: E402  (canonical iteration-order anchor)
from .upstream import AllowlistError, JiraError, UpstreamNotFoundError  # noqa: E402


class ValidationError(Exception):
    """Flag-combo / config-shape / path-safety errors. Exit 2."""


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------
_POSIX_SYSTEM_ROOTS = ("/etc", "/sys", "/proc", "/dev", "/boot")
# macOS firmlinks: /etc -> /private/etc. After Path.resolve() "/etc/foo"
# becomes "/private/etc/foo" on darwin. /var and /tmp are NOT spec-banned
# roots (only /etc /sys /proc /dev /boot are), and the user's temp dir
# lives under /private/var, so don't touch it.
_DARWIN_RESOLVED_ROOTS = ("/private/etc",)
_WINDOWS_SYSTEM_ROOTS = (
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
)


def _is_under_system_root(p: Path) -> bool:
    s = str(p)
    if os.name == "nt":
        # Normalize separators so "C:/Windows/foo" and "C:\\Windows\\foo" both
        # match the canonical roots stored with backslashes. Case-insensitive
        # per Windows filesystem semantics.
        sl = s.lower().replace("\\", "/")
        for r in _WINDOWS_SYSTEM_ROOTS:
            rl = r.lower().replace("\\", "/")
            if sl == rl or sl.startswith(rl + "/"):
                return True
        return False
    # posix (linux, darwin)
    roots = _POSIX_SYSTEM_ROOTS
    if sys.platform == "darwin":
        roots = roots + _DARWIN_RESOLVED_ROOTS
    for r in roots:
        if s == r or s.startswith(r + "/"):
            return True
    return False


def validate_path(p: str, label: str) -> Path:
    """Reject null bytes and any path inside an OS system root.

    Checks both the raw path string and the resolved form (so users can't
    sneak past via /private/etc on darwin or via symlinks).
    """
    if "\x00" in p:
        raise ValidationError("--{}: path contains a null byte".format(label))
    raw = Path(p)
    candidates = [raw]
    try:
        candidates.append(raw.resolve())
    except OSError:
        pass
    for c in candidates:
        if _is_under_system_root(c):
            raise ValidationError(
                "--{}: path '{}' is under a system root and is refused".format(label, p)
            )
    return raw


# ---------------------------------------------------------------------------
# Window parsing
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Window:
    """Resolved window. ``to_exclusive`` is one day past the named end day."""
    from_date: date           # inclusive named day
    to_date: date             # inclusive named day
    from_utc: datetime        # from_date 00:00:00 UTC
    to_exclusive_utc: datetime  # (to_date + 1d) 00:00:00 UTC


def _parse_iso_date(s: str, label: str) -> date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(
            "--{}: invalid date '{}'; expected YYYY-MM-DD".format(label, s)
        )


def parse_window(
    from_str: Optional[str],
    to_str: Optional[str],
    now: Optional[datetime] = None,
) -> Window:
    """Resolve the window.

    Both ``--from`` and ``--to`` are inclusive of the named day. Internally
    the window is ``[from 00:00 UTC, (to + 1 day) 00:00 UTC)`` — the
    ``to_exclusive_utc`` field is the open upper bound.

    Default window is the last 90 days ending today (UTC). "90 days" refers
    to the ``to − from`` difference; the inclusive-day count is 91.
    """
    src = now if now is not None else clock.today_utc()
    # Treat naive datetimes as UTC rather than letting astimezone() interpret
    # them as local-tz; clock.today_utc() always returns tz-aware UTC, but
    # tests / future callers might pass naive instants by mistake.
    if src.tzinfo is None:
        src = src.replace(tzinfo=timezone.utc)
    else:
        src = src.astimezone(timezone.utc)
    today = src.date()
    if to_str is None:
        to_d = today
    else:
        to_d = _parse_iso_date(to_str, "to")
    if from_str is None:
        from_d = to_d - timedelta(days=90)
    else:
        from_d = _parse_iso_date(from_str, "from")
    if from_d > to_d:
        raise ValidationError(
            "--from ({}) must be <= --to ({})".format(from_d.isoformat(), to_d.isoformat())
        )
    from_utc = datetime(from_d.year, from_d.month, from_d.day, tzinfo=timezone.utc)
    to_excl = datetime(to_d.year, to_d.month, to_d.day, tzinfo=timezone.utc) + timedelta(days=1)
    return Window(from_date=from_d, to_date=to_d, from_utc=from_utc, to_exclusive_utc=to_excl)


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------
ALL_METRICS = (
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow-metrics",
        description=(
            "Compute DORA / Flow Framework metrics for a Jira project, team, "
            "Jira Align program, or portfolio over a time window."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Scope (exactly one of project / program-id / portfolio-id required;
    # validated manually so we can also enforce --team coupling).
    parser.add_argument("--project", help="Jira project key. Mutually exclusive with --program-id / --portfolio-id.")
    parser.add_argument("--team", help="Sub-scope within a --project. Only valid with --project.")
    parser.add_argument("--program-id", dest="program_id", help="Jira Align program ID.")
    parser.add_argument("--portfolio-id", dest="portfolio_id", help="Jira Align portfolio ID.")

    # Window
    parser.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD",
                        help="Window start (inclusive). Default: --to minus 90 days.")
    parser.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD",
                        help="Window end (inclusive). Default: today (UTC).")

    # Filters
    parser.add_argument("--jql", help="Extra JQL ANDed into the scope query. Always parenthesized.")
    parser.add_argument("--align-filter", dest="align_filter",
                        help="Extra OData ANDed into Jira Align queries. Always parenthesized.")
    parser.add_argument("--cohort-jql", dest="cohort_jql",
                        help="JQL marking matching issues with cohort: true.")

    # Output selection
    parser.add_argument("--metrics", help="Comma list. Default: all. Names: " + ", ".join(ALL_METRICS))

    # Config files
    parser.add_argument("--state-config", dest="state_config",
                        help="JSON state-mapping config. Defaults to shipped references/states.default.json.")
    parser.add_argument("--issuetype-config", dest="issuetype_config",
                        help="JSON issuetype-bucket config. Defaults to shipped references/issuetypes.default.json.")

    # Overrides
    parser.add_argument("--team-field-override", dest="team_field_override",
                        help="Override team_field.id from the state config.")
    parser.add_argument("--align-join-field", dest="align_join_field",
                        help="Override the Jira <-> Jira Align join field.")
    parser.add_argument("--align-teams-path", dest="align_teams_path",
                        help="Override the Jira Align teams enumeration path.")
    parser.add_argument("--include-subtasks", dest="include_subtasks", action="store_true",
                        help="Include subtasks in throughput / cycle / lead / flow_efficiency / rework_rate.")

    # Output format
    parser.add_argument("--format", choices=("json", "csv"), default="json", help="Output format.")
    parser.add_argument("--output", help="Write to file instead of stdout. Required for --per-issue.")
    parser.add_argument("--per-issue", dest="per_issue", action="store_true",
                        help="Emit one JSONL row per issue. Requires --output.")
    parser.add_argument("--yes", action="store_true",
                        help="Overwrite --output without prompting.")

    # Cache / debug
    parser.add_argument("--no-cache", dest="no_cache", action="store_true", help="Bypass the on-disk cache.")
    parser.add_argument("--verbose", action="store_true", help="Debug logging.")

    return parser


# ---------------------------------------------------------------------------
# Flag-combo validation
# ---------------------------------------------------------------------------
def validate_args(args: argparse.Namespace) -> None:
    """Apply flag-combo rules. Raise ``ValidationError`` (exit 2) on miss.

    Runs before any upstream call. Order matters only for error-message
    clarity — every check is total.
    """
    scopes = [
        ("--project", args.project),
        ("--program-id", args.program_id),
        ("--portfolio-id", args.portfolio_id),
    ]
    present = [name for name, value in scopes if value is not None]
    if len(present) == 0:
        raise ValidationError(
            "exactly one of --project / --program-id / --portfolio-id is required; none given"
        )
    if len(present) > 1:
        raise ValidationError(
            "exactly one of --project / --program-id / --portfolio-id may be given; got {}".format(
                ", ".join(present)
            )
        )

    if args.team is not None and args.project is None:
        raise ValidationError("--team is only valid with --project")

    if args.per_issue and args.output is None:
        raise ValidationError("--per-issue requires --output FILE")

    # Path safety on every path-bearing flag.
    if args.output is not None:
        validate_path(args.output, "output")
    if args.state_config is not None:
        validate_path(args.state_config, "state-config")
    if args.issuetype_config is not None:
        validate_path(args.issuetype_config, "issuetype-config")

    # Metrics list (just shape-check here; no fail-on-unknown until T10
    # owns the canonical list emission. But typo'd metric names should
    # surface early).
    if args.metrics is not None:
        names = [m.strip() for m in args.metrics.split(",") if m.strip()]
        unknown = [n for n in names if n not in ALL_METRICS]
        if unknown:
            raise ValidationError(
                "--metrics: unknown metric(s) {}; valid: {}".format(
                    ", ".join(unknown), ", ".join(ALL_METRICS)
                )
            )


# ---------------------------------------------------------------------------
# Overwrite-confirm helper (T1 ships the prompt + TTY-detection helper that
# the test exercises via a stub; the actual write path is T10).
# ---------------------------------------------------------------------------
def confirm_overwrite(
    path: Path,
    *,
    yes: bool,
    stdin_isatty: Optional[bool] = None,
    stdout_isatty: Optional[bool] = None,
    prompt_response: Optional[str] = None,
) -> bool:
    """Return True iff overwrite is allowed.

    - ``--yes`` short-circuits to True.
    - No TTY and no ``--yes`` -> abort (False). Caller exits 1.
    - TTY present -> consult ``prompt_response`` (test seam) or stdin.
    """
    if yes:
        return True
    if not path.exists():
        return True
    if stdin_isatty is None:
        stdin_isatty = sys.stdin.isatty()
    if stdout_isatty is None:
        stdout_isatty = sys.stdout.isatty()
    if not (stdin_isatty and stdout_isatty):
        return False
    if prompt_response is None:
        try:
            prompt_response = input("Overwrite {} ? [y/N] ".format(path))
        except EOFError:
            return False
    return prompt_response.strip().lower() in ("y", "yes")


# ---------------------------------------------------------------------------
# Pipeline wiring (T13 — orchestrates T2-T11 module APIs end-to-end)
# ---------------------------------------------------------------------------
def _format_team_id_literal(team_id: str) -> str:
    """Render a Jira Align team id as a JQL literal for the IN clause.

    Numeric ids pass through unquoted; everything else is double-quoted with
    embedded quotes escaped. Mirrors per_team._format_team_id_for_jql so the
    bare-scope clause we hand to iter_per_issue_rows formats identically to
    the compose_program_scope_jql path used by per_team rollup.
    """
    s = str(team_id)
    if s == "":
        raise ValidationError("jira-align returned an empty team id")
    if s.lstrip("-").isdigit():
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _build_scope_clause(args: argparse.Namespace, state_config, teams) -> Optional[str]:
    """Compose the bare scope JQL (no user clause, no ORDER BY).

    Project scope returns ``project = <KEY>`` optionally narrowed by
    ``--team`` against the configured team_field. Program/portfolio scope
    returns ``"<field>" in (id1, id2, ...)`` against the resolved team list,
    or None when the team list is empty (the caller emits an empty report).
    """
    if args.project is not None:
        clause = "project = " + args.project
        if args.team:
            tf = state_config.team_field
            if tf is not None and tf.id:
                # Escape backslashes + double-quotes inside the JQL string
                # literal so a --team value containing either renders as
                # valid JQL rather than truncating the clause early.
                team_lit = args.team.replace("\\", "\\\\").replace('"', '\\"')
                clause += ' AND "{}" = "{}"'.format(tf.id, team_lit)
        return clause
    # program / portfolio
    if not teams:
        return None
    from .align import require_align_join_field
    align_join_field = require_align_join_field(state_config, args.align_join_field)
    rendered = ", ".join(_format_team_id_literal(t.id) for t in teams)
    return '"{}" in ({})'.format(align_join_field, rendered)


def _scope_kind_and_value(args: argparse.Namespace):
    if args.project is not None:
        return "project", args.project
    if args.program_id is not None:
        return "program", args.program_id
    return "portfolio", args.portfolio_id


def _scope_meta_dict(args: argparse.Namespace) -> dict:
    if args.project is not None:
        out = {"project": args.project}
        if args.team:
            out["team"] = args.team
        return out
    if args.program_id is not None:
        return {"program_id": args.program_id}
    return {"portfolio_id": args.portfolio_id}


def _resolve_metrics(args: argparse.Namespace):
    if args.metrics is None:
        return list(ALL_METRICS)
    return [m.strip() for m in args.metrics.split(",") if m.strip()]


def _run_pipeline(args: argparse.Namespace, window: "Window") -> int:
    """Drive the full pipeline end-to-end. Returns a process exit code.

    Orchestration only — every computation step lives in a T2-T11 module.
    Exceptions raised by modules (ValidationError, AllowlistError,
    UpstreamNotFoundError, JiraError, CallerResolutionError, ConfigError,
    AlignResponseError, ValueError from align_join_field / align_teams_path)
    bubble out to main()'s try/except, which maps to the right exit code.
    """
    # Local imports — keep top-level import surface minimal so the T1
    # stub-only paths (--help, validation errors) don't pay the full
    # module-graph cost.
    from dataclasses import replace as _replace
    from .config import ConfigError, TeamField, load_issuetype_config, load_state_config
    from .upstream import JiraAlignClient, JiraClient, discover_skill_path
    from .align import (
        AlignScope,
        compute_sources,
        teams_for_scope,
        validate_align_teams_path,
    )
    from .per_issue import iter_per_issue_rows
    from .per_team import (
        bucket_by_team,
        per_team_double_counted,
        per_team_rollup,
    )
    from .aggregate import aggregate
    from .cohort import build_cohort_breakdown, resolve_cohort_keys
    from .notes import NotesCollector
    from .meta import build_meta, resolve_caller
    from .output import Report, render_csv, render_json, render_jsonl
    from .cache import cache_key, read_cache, write_cache_tee, cleanup_stale_tmps

    # --align-teams-path: validate up-front so a bad value lands as exit 2
    # before any subprocess fires.
    if args.align_teams_path is not None:
        validate_align_teams_path(args.align_teams_path)

    # 1. Configs ----------------------------------------------------------
    try:
        state_config = load_state_config(
            Path(args.state_config) if args.state_config else None
        )
        issuetype_config = load_issuetype_config(
            Path(args.issuetype_config) if args.issuetype_config else None
        )
    except ConfigError as e:
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION

    # --team-field-override replaces only the id; kind is preserved (or
    # defaults to single_value when the source config did not set one).
    if args.team_field_override is not None:
        original_tf = state_config.team_field
        kind = (original_tf.kind if original_tf and original_tf.kind else "single_value")
        state_config = _replace(
            state_config,
            team_field=TeamField(id=args.team_field_override, kind=kind),
        )

    scope_kind, scope_value = _scope_kind_and_value(args)
    scope_meta = _scope_meta_dict(args)

    # 2. Upstream discovery ----------------------------------------------
    jira_script = discover_skill_path("jira")
    jira = JiraClient(jira_script)
    align: Optional[JiraAlignClient] = None
    if scope_kind in ("program", "portfolio"):
        align_script = discover_skill_path("jira-align")
        align = JiraAlignClient(align_script)

    # 3. Resolve align teams (None for project scope) ---------------------
    if scope_kind in ("program", "portfolio"):
        align_scope = AlignScope(
            kind=scope_kind,
            value=scope_value,
            teams_path_override=args.align_teams_path,
        )
        teams = teams_for_scope(align, align_scope)
    else:
        teams = []

    scope_clause = _build_scope_clause(args, state_config, teams)

    # 4. Cache key + read --------------------------------------------------
    cache_dir = Path.cwd() / ".context" / "flow-metrics" / "cache"
    cleanup_stale_tmps(cache_dir)
    window_dict = {
        "from": window.from_date.isoformat(),
        "to": window.to_date.isoformat(),
    }
    cache_scope = {"kind": scope_kind, "value": scope_value}
    if scope_kind == "project" and args.team:
        cache_scope["team"] = args.team
    key = cache_key(
        cache_scope,
        window_dict,
        args.jql,
        args.align_filter,
        state_config.sha,
        issuetype_config.sha,
        args.team_field_override,
        args.align_join_field,
        args.align_teams_path,
    )

    # 5. Fetch + derive (or read from cache) ------------------------------
    rows: list
    if scope_clause is None:
        # No teams resolved in program / portfolio scope — emit an empty
        # report rather than building a malformed empty IN () clause.
        rows = []
    else:
        cached = None if args.no_cache else read_cache(cache_dir, key)
        if cached is not None:
            rows = list(cached)
        else:
            user_clause = args.jql
            stream = iter_per_issue_rows(
                jira,
                scope_clause,
                user_clause,
                state_config,
                issuetype_config,
                window,
            )
            if args.no_cache:
                rows = list(stream)
            else:
                rows = list(write_cache_tee(cache_dir, key, stream))

    notes = NotesCollector()

    # 6. Cohort split ------------------------------------------------------
    cohort_breakdown_dict = None
    if args.cohort_jql and scope_clause is not None and not args.per_issue:
        cohort_keys = resolve_cohort_keys(jira, args.cohort_jql, scope_clause)
        cohort_breakdown_dict = build_cohort_breakdown(
            rows,
            cohort_keys,
            state_config,
            window,
            notes,
            include_subtasks=args.include_subtasks,
        )
    elif args.cohort_jql and scope_clause is not None and args.per_issue:
        # Per-issue with cohort: tag each row but don't compute breakdown.
        from .cohort import tag_cohort as _tag_cohort
        cohort_keys = resolve_cohort_keys(jira, args.cohort_jql, scope_clause)
        rows = list(_tag_cohort(rows, cohort_keys))

    # 7. Top-level aggregate ----------------------------------------------
    agg_block = aggregate(
        iter(rows),
        window,
        state_config,
        include_subtasks=args.include_subtasks,
    )

    # 8. Per-team rollup --------------------------------------------------
    per_team_rows: list = []
    team_field = state_config.team_field
    distinct_teams = {r.team for r in rows}
    should_per_team = scope_kind in ("program", "portfolio") or (
        scope_kind == "project" and len(distinct_teams) > 1
    )
    if should_per_team and rows:
        # Array-kind team_field: enumerate the full membership list per
        # row so an issue with N>1 teams lands in each team's bucket.
        # The list is canonical on the row (T5 derive_row populates
        # ``teams`` deduped, in encounter order) — bucket_by_team
        # dedupes within the row again defensively. NO_TEAM rows have
        # an empty ``teams`` tuple; bucket_by_team's "no teams →
        # NO_TEAM bucket" branch handles that.
        def _array_teams_cb(r):
            return r.teams

        if team_field is not None and team_field.kind == "array":
            teams_cb = _array_teams_cb
        else:
            teams_cb = None
        buckets = bucket_by_team(
            iter(rows), team_field, teams_for_row=teams_cb, notes=notes
        )
        per_team_rows = per_team_rollup(
            buckets,
            state_config,
            window,
            include_subtasks=args.include_subtasks,
        )
    pt_double = per_team_double_counted(team_field)

    # 9. Notes from aggregate counters ------------------------------------
    if agg_block.cancelled_in_window > 0:
        notes.add_cancelled(agg_block.cancelled_in_window)
    if agg_block.delivered_without_commitment > 0:
        notes.add_skipped_commitment(agg_block.delivered_without_commitment)
    if agg_block.flow_efficiency_zero_denominator > 0:
        notes.add_zero_denominator_flow_eff(agg_block.flow_efficiency_zero_denominator)
    notes.add_flow_load_sample_count(agg_block.flow_load_sample_count, "included")
    notes.add_defect_ratio_disclaimer()

    # 10. Meta ------------------------------------------------------------
    whoami_payload = jira.whoami()
    caller = resolve_caller(whoami_payload)
    sources = compute_sources(scope_kind)
    metrics_requested = _resolve_metrics(args)
    meta_dict = build_meta(
        caller=caller,
        scope=scope_meta,
        window=window,
        sources=sources,
        metrics_requested=metrics_requested,
        state_config_sha=state_config.sha,
        issuetype_config_sha=issuetype_config.sha,
        generated_at=clock.today_utc(),
        per_team_double_counted=pt_double,
        cohort_jql=args.cohort_jql,
    )

    # 11. Render + write --------------------------------------------------
    if args.per_issue:
        out_path = Path(args.output)
        with open(out_path, "wb") as f:
            for line in render_jsonl(iter(rows)):
                f.write(line)
        return EXIT_OK

    report = Report(
        aggregate=agg_block,
        meta=meta_dict,
        notes=notes.finalize(),
        metrics_requested=metrics_requested,
        cohort_breakdown=cohort_breakdown_dict,
        per_team=per_team_rows,
    )
    if args.format == "json":
        payload = render_json(report)
    else:
        payload = render_csv(report)

    if args.output:
        with open(args.output, "wb") as f:
            f.write(payload)
    else:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()
    return EXIT_OK


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_args(args)
        window = parse_window(args.from_date, args.to_date)
    except ValidationError as e:
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except (AllowlistError, UpstreamNotFoundError) as e:
        # T3 test seam — these exceptions are raised by the upstream
        # wrapper layer, never by validate_args itself in production, but
        # T3's test_main_catches_* contract tests monkeypatch validate_args
        # to inject them and assert main()'s exit-code mapping.
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except JiraError:
        return EXIT_UPSTREAM

    # Overwrite confirmation gate (T1 contract — applies before the
    # pipeline so a missing TTY aborts before any subprocess fires).
    if args.output is not None:
        out_path = Path(args.output)
        if not confirm_overwrite(out_path, yes=args.yes):
            print(
                "error: --output {} exists and overwrite was not confirmed".format(out_path),
                file=sys.stderr,
            )
            return EXIT_USER_ABORT

    # Locally-imported exception types — keep the catch list explicit so
    # Python picks the right branch by isinstance, not by clause order.
    from .timeline import UnmappedStatusError as _UnmappedStatusError
    from .align import AlignResponseError as _AlignResponseError
    from .meta import CallerResolutionError as _CallerResolutionError

    try:
        return _run_pipeline(args, window)
    except ValidationError as e:
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except (AllowlistError, UpstreamNotFoundError) as e:
        # Wrapper-boundary refusals (disallowed verbs, missing upstream
        # skill) are validation-class failures.
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except _UnmappedStatusError as e:
        # Spec § "Unmapped-status policy": data-dependent exit 2 naming
        # the offending raw status. The exception message already does so.
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except ValueError as e:
        # require_align_join_field / validate_align_teams_path /
        # compose_program_scope_jql raise ValueError on bad inputs the
        # spec maps to exit 2.
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION
    except JiraError:
        # Upstream stderr was already forwarded inside the wrapper; here
        # we only need to translate to the right exit code.
        return EXIT_UPSTREAM
    except (_AlignResponseError, _CallerResolutionError) as e:
        # Upstream-side data-shape errors — subprocess exited zero but
        # the payload was unusable. Spec maps to exit 3.
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_UPSTREAM


if __name__ == "__main__":
    sys.exit(main())
