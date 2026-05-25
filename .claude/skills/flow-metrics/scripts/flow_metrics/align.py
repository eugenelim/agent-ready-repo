"""T9 Jira Align integration.

Resolves team membership for program-id / portfolio-id scope runs via
the ``jira-align`` skill's nested-resource ``raw GET`` endpoints, then
hands the resulting team-id list to the Jira side for the actual issue
query (per spec § "Data sources": Jira Align supplies team membership;
Jira's changelog supplies the metrics).

Allowlist alignment: every endpoint touched here is also enumerated in
:class:`flow_metrics.upstream.JiraAlignClient._ALLOWED_RAW_PATTERNS`, so
the wrapper-boundary contract test stays satisfied automatically.

Startup-time validation of ``--align-teams-path`` lives here too — the
override must match one of the four allowed Jira Align patterns exactly,
and ``..`` / absolute paths are rejected up front (before any subprocess
spawn). The validator is callable from argparse so failures land as
exit 2, not exit 3.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .config import StateConfig
from .upstream import JiraAlignClient


class AlignResponseError(Exception):
    """Jira Align returned a payload whose shape doesn't match the
    documented contract — e.g., a list element missing ``id``.

    Mapped to exit 3 (upstream-skill error) by the CLI: the data layer
    failed, just like a non-2xx HTTP response. Distinct from
    :class:`flow_metrics.upstream.JiraError` only in that the underlying
    subprocess exited zero but the payload is unusable.
    """


# ---------------------------------------------------------------------------
# Path-override validation (--align-teams-path)
# ---------------------------------------------------------------------------
# Exact-match regex patterns, not prefixes. ``programs/42/features`` is
# rejected even though it starts with ``programs/`` — it's not one of the
# four nested-resource paths the spec enumerates. Synced with
# JiraAlignClient._ALLOWED_RAW_PATTERNS; both must stay in lockstep.
_ALIGN_TEAMS_PATH_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"^programs/[0-9]+$"),
    re.compile(r"^programs/[0-9]+/teams$"),
    re.compile(r"^portfolios/[0-9]+$"),
    re.compile(r"^portfolios/[0-9]+/programs$"),
)


def validate_align_teams_path(path: str) -> str:
    """Return ``path`` if valid; raise :class:`ValueError` otherwise.

    Called at startup from argparse (before any upstream skill is
    invoked), so a bad override surfaces as exit 2 — the data layer is
    never reached. The four allowed patterns are exact-match: anything
    that doesn't match (including paths that are otherwise plausible
    Jira Align resources like ``programs/<id>/features``) is rejected.

    ``..`` segments and absolute paths are screened first with explicit
    messages so the rejection reason is obvious; without those guards a
    user-visible failure would just say "not in the allowlist", masking
    a possible directory-traversal attempt.
    """
    if not isinstance(path, str) or not path:
        raise ValueError("--align-teams-path: must be a non-empty string")
    if path.startswith("/"):
        raise ValueError(
            "--align-teams-path: absolute paths are not allowed; got {!r}".format(path)
        )
    if ".." in path.split("/"):
        raise ValueError(
            "--align-teams-path: path traversal ('..') is not allowed; got {!r}".format(path)
        )
    for pat in _ALIGN_TEAMS_PATH_PATTERNS:
        if pat.fullmatch(path):
            return path
    raise ValueError(
        "--align-teams-path: {!r} is not one of the allowed Jira Align "
        "nested-resource paths (programs/<id>, programs/<id>/teams, "
        "portfolios/<id>, portfolios/<id>/programs)".format(path)
    )


# ---------------------------------------------------------------------------
# Scope + team types
# ---------------------------------------------------------------------------
# Canonical scope_kind values, shared with :mod:`flow_metrics.cache` (which
# pins the same vocabulary in the cache-key payload — spec § Caching:
# ``scope_kind: "project" | "program" | "portfolio"``). Using anything
# else here would silently break cache-key derivation when T10 wires this
# module into the main run.
PROJECT_KIND = "project"
PROGRAM_KIND = "program"
PORTFOLIO_KIND = "portfolio"
_ALIGN_KINDS = frozenset({PROGRAM_KIND, PORTFOLIO_KIND})


@dataclass(frozen=True)
class AlignScope:
    """Resolved Jira Align scope from the CLI.

    ``kind`` is one of ``"program"`` / ``"portfolio"`` (matching the
    spec-pinned cache vocabulary, not the CLI flag spelling). ``value``
    is the numeric id as a string (Jira Align IDs are always integers
    in v1). ``teams_path_override`` mirrors ``--align-teams-path`` after
    :func:`validate_align_teams_path` has already accepted it.
    """

    kind: str
    value: str
    teams_path_override: Optional[str] = None


@dataclass(frozen=True)
class Team:
    """One team returned by Jira Align.

    Only ``id`` is required by the spec contract — every element of every
    team-list response is validated to carry one. ``name`` is captured
    when present (some Jira Align versions return it inline) so callers
    can sort or display by name without a second round-trip.
    """

    id: str
    name: Optional[str] = None


def _coerce_id(value: Any) -> Optional[str]:
    """Jira Align is inconsistent: some endpoints return numeric IDs,
    others return them as strings. Normalise both to the canonical
    string form so set-membership and JQL composition are well-defined.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        # ``True``/``False`` are also instances of ``int``; reject them
        # explicitly rather than silently coercing to ``"True"``.
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value if value else None
    return None


def _parse_team_items(payload: Any, path: str) -> List[Team]:
    """Validate a teams response and return the parsed Team list.

    Every element must carry an ``id`` (string or int). Missing /
    non-string ids raise :class:`AlignResponseError` referencing the
    path that produced the bad payload, so the user can map the failure
    back to a specific upstream call. Empty lists are valid (no teams
    in this program).
    """
    if not isinstance(payload, list):
        raise AlignResponseError(
            "unexpected response shape from {}: expected list, got {}".format(
                path, type(payload).__name__
            )
        )
    out: List[Team] = []
    for i, item in enumerate(payload):
        if not isinstance(item, dict):
            raise AlignResponseError(
                "unexpected response shape from {}: element {} is not an object".format(
                    path, i
                )
            )
        tid = _coerce_id(item.get("id"))
        if tid is None:
            raise AlignResponseError(
                "unexpected response shape from {}: element {} is missing 'id'".format(
                    path, i
                )
            )
        name = item.get("name")
        out.append(Team(id=tid, name=name if isinstance(name, str) else None))
    return out


def _parse_program_ids(payload: Any, path: str) -> List[str]:
    """Same shape validation as :func:`_parse_team_items` but only the
    program ids are needed; names are ignored at the portfolio level.
    """
    if not isinstance(payload, list):
        raise AlignResponseError(
            "unexpected response shape from {}: expected list, got {}".format(
                path, type(payload).__name__
            )
        )
    ids: List[str] = []
    for i, item in enumerate(payload):
        if not isinstance(item, dict):
            raise AlignResponseError(
                "unexpected response shape from {}: element {} is not an object".format(
                    path, i
                )
            )
        pid = _coerce_id(item.get("id"))
        if pid is None:
            raise AlignResponseError(
                "unexpected response shape from {}: element {} is missing 'id'".format(
                    path, i
                )
            )
        ids.append(pid)
    return ids


def resolve_teams(align: JiraAlignClient, scope: AlignScope) -> List[Team]:
    """Resolve the list of teams visible under ``scope``.

    - ``program`` kind: one ``raw GET programs/<id>/teams`` call (or the
      ``--align-teams-path`` override, validated already).
    - ``portfolio`` kind: walk ``portfolios/<id>/programs`` first, then
      for each program issue ``programs/<pid>/teams``. The contract test
      ``test_portfolio_scope_walks_programs_then_teams`` pins the call
      sequence — portfolio listing before any team listing, programs in
      the order Jira Align returned them.

    Validates every list element carries an ``id``; on any shape
    violation raises :class:`AlignResponseError` so the CLI exits 3 with
    the path that produced the bad payload.
    """
    if scope.kind == PROGRAM_KIND:
        path = scope.teams_path_override or "programs/{}/teams".format(scope.value)
        payload = align.raw_get(path)
        return _parse_team_items(payload, path)

    if scope.kind == PORTFOLIO_KIND:
        portfolios_path = "portfolios/{}/programs".format(scope.value)
        programs_payload = align.raw_get(portfolios_path)
        program_ids = _parse_program_ids(programs_payload, portfolios_path)
        teams: List[Team] = []
        for pid in program_ids:
            # The override applies to program kind only — at portfolio
            # scope we always walk each program's canonical teams path.
            teams_path = "programs/{}/teams".format(pid)
            payload = align.raw_get(teams_path)
            teams.extend(_parse_team_items(payload, teams_path))
        return teams

    raise ValueError(
        "AlignScope.kind must be 'program' or 'portfolio'; got {!r}".format(scope.kind)
    )


# ---------------------------------------------------------------------------
# Project-scope gating helper
# ---------------------------------------------------------------------------
def teams_for_scope(
    align: Optional[JiraAlignClient],
    scope: Optional[AlignScope],
) -> List[Team]:
    """Single entry point for orchestration code: resolve teams if and
    only if a Jira Align scope is present.

    Project-scope runs pass ``scope=None`` and get back an empty list
    without ``align`` ever being consulted — pinned by the contract test
    ``test_jira_only_run_does_not_call_jira_align``. Threading the
    "should we call jira-align?" decision through this helper keeps the
    gate in one place instead of duplicating ``if scope is None`` at
    every call site.
    """
    if scope is None:
        return []
    if align is None:
        raise ValueError(
            "teams_for_scope: scope is set but no JiraAlignClient was provided"
        )
    return resolve_teams(align, scope)


# ---------------------------------------------------------------------------
# --align-join-field resolution (--align-join-field > state config > error)
# ---------------------------------------------------------------------------
def require_align_join_field(
    state_config: StateConfig,
    cli_override: Optional[str],
) -> str:
    """Resolve the Jira ↔ Jira Align join field name per spec § "Data
    sources" — Joining Jira ↔ Jira Align.

    Resolution order:
      1. ``--align-join-field NAME`` CLI override (if non-empty).
      2. ``align_join_field`` entry in the state config (if set).
      3. Error — exit 2 with a clear message.

    Called only when ``--program-id`` / ``--portfolio-id`` is requested;
    project-scope runs don't need a join field. Raises
    :class:`ValueError` on miss; the CLI maps that to exit 2.
    """
    if cli_override is not None and cli_override.strip() != "":
        return cli_override
    if state_config.align_join_field:
        return state_config.align_join_field
    raise ValueError(
        "Jira Align scope (--program-id / --portfolio-id) requires an "
        "align_join_field. Set --align-join-field NAME or add "
        "'align_join_field' to the state config."
    )


# ---------------------------------------------------------------------------
# meta.sources helper (T10 emits; T9 surfaces the value)
# ---------------------------------------------------------------------------
def compute_sources(scope_kind: Optional[str]) -> List[str]:
    """Return the sorted list of upstream skill names used for this run.

    ``project`` scope hits only Jira; ``program`` / ``portfolio`` also
    hit Jira Align. ``scope_kind`` values match the spec-pinned cache
    vocabulary (also accepted in their CLI-flag spellings ``program-id``
    / ``portfolio-id`` so call sites can pass either without an explicit
    conversion). The contract test ``test_meta_sources_reflects_skills_
    called`` pins both shapes. T10 merges this into the top-level
    ``meta`` block.
    """
    sources = ["jira"]
    if scope_kind in _ALIGN_KINDS or scope_kind in ("program-id", "portfolio-id"):
        sources.append("jira-align")
    return sorted(sources)


__all__ = [
    "PORTFOLIO_KIND",
    "PROGRAM_KIND",
    "PROJECT_KIND",
    "AlignResponseError",
    "AlignScope",
    "Team",
    "compute_sources",
    "require_align_join_field",
    "resolve_teams",
    "teams_for_scope",
    "validate_align_teams_path",
]
