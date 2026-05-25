"""Per-issue Timeline — canonical-state walk over the changelog.

T5 substrate: builds an in-memory ordered view of one issue's
status and issuetype transitions, derived from its baseline
(``issue.fields.created`` + initial ``status`` + initial ``issuetype``)
and a stream of :class:`ChangelogEntry` records produced by T4.

Every raw status the walker encounters — baseline AND every
``from_value`` / ``to_value`` on a status transition — is mapped through
:meth:`StateConfig.canonical_for`. An unmapped raw status raises
:class:`UnmappedStatusError`; main translates this to exit 2 naming the
offending status (spec § "Unmapped-status policy", data-dependent path).

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Mapping, Optional, Tuple

from .changelog import ChangelogEntry, _parse_jira_timestamp
from .config import ReworkSignal, StateConfig


class UnmappedStatusError(Exception):
    """Walker hit a raw status not present in ``canonical_states``.

    Carries the offending raw status name so :func:`flow_metrics.main`
    can name it in the exit-2 error string (spec § "Unmapped-status
    policy" — refusal rather than silent canonicalisation).
    """

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__("unmapped Jira status: {!r}".format(status))


@dataclass(frozen=True)
class StatusTransition:
    timestamp: datetime
    from_canonical: str
    to_canonical: str


@dataclass(frozen=True)
class IssuetypeTransition:
    timestamp: datetime
    from_value: str
    to_value: str


def _issue_created(issue: Mapping) -> datetime:
    fields = issue.get("fields") or {}
    created = fields.get("created")
    if not isinstance(created, str):
        raise ValueError(
            "issue {!r} is missing fields.created (required to anchor "
            "the timeline walk)".format(issue.get("key"))
        )
    return _parse_jira_timestamp(created)


def _issue_current_status(issue: Mapping) -> str:
    fields = issue.get("fields") or {}
    status = fields.get("status")
    if isinstance(status, Mapping):
        name = status.get("name")
        if isinstance(name, str):
            return name
    return ""


def _issue_current_issuetype(issue: Mapping) -> str:
    fields = issue.get("fields") or {}
    issuetype = fields.get("issuetype")
    if isinstance(issuetype, Mapping):
        name = issuetype.get("name")
        if isinstance(name, str):
            return name
    return ""


class Timeline:
    """In-memory per-issue timeline.

    Construction:
    - Reads ``issue.fields.created`` to anchor the initial span.
    - Sorts ``changelog`` by ``timestamp`` (defensive — Jira occasionally
      returns interleaved pages out of order).
    - Splits entries into status- and issuetype-streams.
    - Derives the initial raw status: ``from_value`` of the first status
      transition if any, else ``issue.fields.status.name``. Symmetric
      logic for issuetype.
    - Maps every raw status through ``config.canonical_for``;
      :class:`UnmappedStatusError` on the first unmapped name.

    Methods walk the precomputed lists rather than re-iterating the
    changelog on each query.
    """

    def __init__(
        self,
        issue: Mapping,
        changelog: Iterable[ChangelogEntry],
        config: StateConfig,
    ) -> None:
        self.issue = issue
        self.config = config
        self.created = _issue_created(issue)

        entries = sorted(changelog, key=lambda e: e.timestamp)
        status_entries = [e for e in entries if e.field == "status"]
        issuetype_entries = [e for e in entries if e.field == "issuetype"]

        # Initial raw status: the ``from_value`` of the first status
        # transition if any, else the issue's current status (which IS
        # the initial when no transitions have happened).
        if status_entries:
            initial_status_raw = status_entries[0].from_value
        else:
            initial_status_raw = _issue_current_status(issue)
        self._initial_status = self._map_status(initial_status_raw)

        self._status_transitions: List[StatusTransition] = []
        for e in status_entries:
            self._status_transitions.append(
                StatusTransition(
                    timestamp=e.timestamp,
                    from_canonical=self._map_status(e.from_value),
                    to_canonical=self._map_status(e.to_value),
                )
            )

        if issuetype_entries:
            initial_issuetype = issuetype_entries[0].from_value
        else:
            initial_issuetype = _issue_current_issuetype(issue)
        self._initial_issuetype = initial_issuetype
        self._issuetype_transitions: List[IssuetypeTransition] = [
            IssuetypeTransition(
                timestamp=e.timestamp,
                from_value=e.from_value,
                to_value=e.to_value,
            )
            for e in issuetype_entries
        ]

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------
    def _map_status(self, raw: str) -> str:
        canonical = self.config.canonical_for(raw)
        if canonical is None:
            raise UnmappedStatusError(raw)
        return canonical

    # ------------------------------------------------------------------
    # Read-only views (exposed for predicates / per-issue derivation)
    # ------------------------------------------------------------------
    @property
    def initial_status(self) -> str:
        return self._initial_status

    @property
    def initial_issuetype(self) -> str:
        return self._initial_issuetype

    @property
    def status_transitions(self) -> Tuple[StatusTransition, ...]:
        return tuple(self._status_transitions)

    @property
    def issuetype_transitions(self) -> Tuple[IssuetypeTransition, ...]:
        return tuple(self._issuetype_transitions)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def first_canonical_transition_into(self, canonical_name: str) -> Optional[datetime]:
        """Timestamp of the first changelog transition whose ``to_canonical``
        equals ``canonical_name``. Returns ``None`` if no such transition.

        The initial-status baseline is NOT a transition — an issue
        created already in ``canonical_name`` has no such transition.
        """
        for t in self._status_transitions:
            if t.to_canonical == canonical_name:
                return t.timestamp
        return None

    def state_at(self, instant: datetime) -> str:
        """Canonical state active at ``instant``.

        Convention: at exactly a transition timestamp ``T``, the state
        is the ``to_canonical`` of that transition (the transition has
        taken effect). For ``instant`` before ``self.created`` the
        initial state is returned — callers should not rely on this,
        but it keeps the function total.
        """
        current = self._initial_status
        for t in self._status_transitions:
            if t.timestamp <= instant:
                current = t.to_canonical
            else:
                break
        return current

    def time_in(
        self, canonical_name: str, interval: Tuple[datetime, datetime]
    ) -> timedelta:
        """Total time the issue was in ``canonical_name`` within ``interval``.

        ``interval`` is ``(start, end)``. Time before ``self.created``
        is naturally excluded because the initial span starts at
        ``created``. Empty / inverted intervals return zero.
        """
        start, end = interval
        if end <= start:
            return timedelta(0)

        total = timedelta(0)
        span_start = self.created
        current = self._initial_status
        for t in self._status_transitions:
            if current == canonical_name:
                lo = max(span_start, start)
                hi = min(t.timestamp, end)
                if hi > lo:
                    total += hi - lo
            current = t.to_canonical
            span_start = t.timestamp
        # Final span: from the last transition (or created if none) onward.
        if current == canonical_name:
            lo = max(span_start, start)
            hi = end
            if hi > lo:
                total += hi - lo
        return total

    def backward_edges(
        self, rework_signals: Tuple[ReworkSignal, ...]
    ) -> List[Tuple[datetime, str, str]]:
        """Every status transition that matches at least one rework signal.

        A transition ``T`` matches signal ``S`` iff
        ``T.from_canonical in S.from_states`` AND
        ``T.to_canonical in S.to_states``. Each matching transition is
        emitted exactly once even if multiple signals would match — the
        spec is explicit that each backward edge counts once.
        """
        out: List[Tuple[datetime, str, str]] = []
        for t in self._status_transitions:
            for signal in rework_signals:
                if (
                    t.from_canonical in signal.from_states
                    and t.to_canonical in signal.to_states
                ):
                    out.append((t.timestamp, t.from_canonical, t.to_canonical))
                    break
        return out

    def issuetype_at(self, instant: datetime) -> str:
        """Raw issuetype value active at ``instant``.

        Returned value is the RAW Jira issuetype name (e.g. "Bug"); the
        canonical-bucket mapping is the consumer's job (per the spec,
        Flow Distribution uses :class:`IssuetypeConfig.bucket_for`).
        """
        current = self._initial_issuetype
        for t in self._issuetype_transitions:
            if t.timestamp <= instant:
                current = t.to_value
            else:
                break
        return current


__all__ = [
    "IssuetypeTransition",
    "StatusTransition",
    "Timeline",
    "UnmappedStatusError",
]
