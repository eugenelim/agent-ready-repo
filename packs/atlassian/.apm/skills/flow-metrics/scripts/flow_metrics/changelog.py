"""Per-issue changelog pagination — Cloud-regression workaround.

T4 substrate: the upstream ``jira: search ... --expand changelog`` call
inlines at most the first ~100 changelog entries per issue under
``issue.changelog``. Long-lived issues need a follow-up
``jira: raw GET issue/<KEY>/changelog`` to drain the rest, or every
downstream cycle-time and lead-time metric is silently wrong on
bot-heavy or long-running issues.

This module exposes a single streaming entry point,
:func:`iter_issue_changelog`, that:

- normalizes both Cloud and Server response shapes into a single
  :class:`ChangelogEntry` dataclass — downstream consumers never branch
  on flavour;
- yields entries lazily so the iterator's peak memory is
  O(transitions per issue), not O(total transitions across the run);
- filters to ``field in {"status", "issuetype"}`` (the only two fields
  T5 consumes) at this layer to keep per-issue memory bounded.

Pagination is detected from three signals in priority order, per
docs/specs/flow-metrics.md § "Changelog pagination (Cloud regression)":

1. ``histories.length < total`` (Server / DC) — drain with
   ``startAt=<N>`` until ``total`` is reached.
2. ``isLast == false`` (Cloud, post-``/search/jql``) — drain with
   ``pageToken=<token>`` until ``isLast: true``.
3. ``nextPageToken`` present — same as (2), kept as a separate signal
   for older Cloud responses that don't surface ``isLast``.

All ``raw_get`` calls go through :class:`JiraClient.raw_get`, which
validates ``issue/<KEY>/changelog`` against the read-only allowlist
before any subprocess fires.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator, List, Mapping, Optional

from .upstream import JiraClient


# Fields T5 consumes. Other field changes (labels, assignee, custom
# fields) are filtered out at this layer so per-issue memory stays
# bounded at O(state + issuetype transitions) rather than O(every edit).
_KEPT_FIELDS: frozenset = frozenset({"status", "issuetype"})


@dataclass(frozen=True)
class ChangelogEntry:
    """One status- or issuetype-transition, normalized across flavours.

    ``timestamp`` is always tz-aware UTC; downstream code can compare
    instants without worrying about Jira's mixed ``+0000`` / ``+0530`` /
    no-offset shapes (Cloud / Server / older Server respectively).
    """
    timestamp: datetime
    author: str
    field: str  # "status" | "issuetype"
    from_value: str
    to_value: str


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------
# Jira Cloud emits ``2026-01-15T14:30:00.000+0000`` (offset without a
# colon). Server / DC emit a similar shape — usually with milliseconds,
# occasionally without; offset may also be missing in older versions.
# ``datetime.fromisoformat`` on Python 3.10 doesn't accept the no-colon
# offset, so we normalize before delegating.
_TRAILING_OFFSET_NO_COLON = re.compile(r"([+-])(\d{2})(\d{2})$")


def _parse_jira_timestamp(s: str) -> datetime:
    """Parse Jira's timestamp shapes into tz-aware UTC.

    Accepts:
    - ``2026-01-15T14:30:00.000+0000`` (Cloud)
    - ``2026-01-15T14:30:00.000+05:30`` (already-normalized offset)
    - ``2026-01-15T14:30:00+0530`` (no milliseconds)
    - ``2026-01-15T14:30:00`` (no offset — interpreted as UTC, per spec
      § Decisions: "UTC throughout")
    - trailing ``Z``
    """
    text = s.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    m = _TRAILING_OFFSET_NO_COLON.search(text)
    if m:
        text = text[: m.start()] + "{}{}:{}".format(m.group(1), m.group(2), m.group(3))
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        # Spec is UTC-throughout; a no-offset timestamp is treated as UTC
        # rather than rejected. Server's older changelog responses
        # occasionally drop the offset.
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Author normalization
# ---------------------------------------------------------------------------
def _author_name(author: Any) -> str:
    """Best-effort human-readable author string.

    Preference order: ``displayName`` (Cloud + Server agree), then ``name``
    (Server username), then ``accountId`` (Cloud opaque id), else ``""``.
    A bot-driven transition with no author block returns ``""`` rather
    than ``None`` — keeps the dataclass field strictly ``str``.
    """
    if not isinstance(author, Mapping):
        return ""
    for key in ("displayName", "name", "accountId"):
        v = author.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------
def _histories(envelope: Any) -> List[dict]:
    """Return the list of history records from a changelog envelope.

    Cloud's ``/search/jql``-style follow-up payload may use ``values``
    instead of ``histories`` (the generic page-list key). We accept
    both so the walker doesn't need to know which endpoint produced
    the page.
    """
    if not isinstance(envelope, Mapping):
        return []
    h = envelope.get("histories")
    if isinstance(h, list):
        return h
    v = envelope.get("values")
    if isinstance(v, list):
        return v
    return []


def _entries_from_history(history: Mapping[str, Any]) -> Iterator[ChangelogEntry]:
    """Yield one :class:`ChangelogEntry` per kept item in a history record.

    A single ``history`` entry can carry multiple ``items`` (e.g. a
    transition that simultaneously changes status and assignee). We
    emit one ``ChangelogEntry`` per ``status`` / ``issuetype`` item and
    drop the rest at this layer.
    """
    created = history.get("created")
    if not isinstance(created, str):
        return
    try:
        ts = _parse_jira_timestamp(created)
    except ValueError:
        # An unparseable timestamp on a single history record should not
        # corrupt the whole iterator — skip it and let T5 surface any
        # downstream consequences via the per-issue derivation checks.
        return
    author = _author_name(history.get("author"))
    items = history.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, Mapping):
            continue
        field = item.get("field")
        if field not in _KEPT_FIELDS:
            continue
        from_value = item.get("fromString")
        if not isinstance(from_value, str):
            from_value = ""
        to_value = item.get("toString")
        if not isinstance(to_value, str):
            to_value = ""
        yield ChangelogEntry(
            timestamp=ts,
            author=author,
            field=field,
            from_value=from_value,
            to_value=to_value,
        )


# ---------------------------------------------------------------------------
# Pagination detection
# ---------------------------------------------------------------------------
def _detect_pagination_mode(envelope: Mapping[str, Any], drained: int) -> Optional[str]:
    """Return ``"server"`` / ``"cloud"`` / ``None`` per the priority signals.

    ``drained`` is the count of records walked through ``_histories(envelope)``
    so far (equivalent to ``len(_histories(envelope))`` once the inline
    walk completes). The spec evaluates ``histories.length < total``;
    using the live walked-count instead of trusting an envelope-reported
    length avoids miscounts if the source list and the metadata
    disagree.
    """
    if not isinstance(envelope, Mapping):
        return None
    total = envelope.get("total")
    if isinstance(total, int) and drained < total:
        return "server"
    is_last = envelope.get("isLast")
    if is_last is False:
        return "cloud"
    next_token = envelope.get("nextPageToken")
    if isinstance(next_token, str) and next_token:
        return "cloud"
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def iter_issue_changelog(
    jira: JiraClient,
    issue_key: str,
    inline: Any,
) -> Iterator[ChangelogEntry]:
    """Stream every kept changelog entry for ``issue_key``.

    ``inline`` is the ``issue.changelog`` object from the parent
    ``jira: search ... --expand changelog`` response. The plan
    documents it as ``list[dict]``; in practice the *envelope* (carrying
    both the ``histories`` list and the pagination signals
    ``total`` / ``isLast`` / ``nextPageToken``) is what's needed —
    without the metadata we can't tell whether to drain. A bare list is
    still tolerated and treated as a complete, unpaginated changelog.

    The follow-up ``raw_get`` calls go through the T3 allowlist:
    ``issue/<KEY>/changelog`` is one of the three permitted patterns;
    nothing else is.
    """
    # Accept both the envelope-dict (correct) and a bare-list (loose
    # interpretation of the plan's annotation). A bare list has no
    # pagination metadata so it implies "complete".
    if isinstance(inline, list):
        envelope: Mapping[str, Any] = {"histories": inline}
    elif isinstance(inline, Mapping):
        envelope = inline
    else:
        return

    drained = 0
    for history in _histories(envelope):
        if isinstance(history, Mapping):
            for entry in _entries_from_history(history):
                yield entry
        drained += 1

    mode = _detect_pagination_mode(envelope, drained)
    if mode is None:
        return

    path = "issue/{}/changelog".format(issue_key)

    if mode == "server":
        # Server / DC: advance ``startAt`` by the count of history
        # records drained so far. ``total`` is authoritative for the
        # stop condition; if the follow-up response carries an updated
        # ``total`` we re-evaluate against it.
        total = envelope.get("total")
        if not isinstance(total, int):
            return
        start_at = drained
        while start_at < total:
            resp = jira.raw_get(path, params={"startAt": str(start_at)})
            page = resp if isinstance(resp, Mapping) else {}
            page_histories = _histories(page)
            if not page_histories:
                # Defensive: a Server response that claims more pages
                # but returns an empty histories list would otherwise
                # spin forever. Treat as drained.
                break
            for history in page_histories:
                if isinstance(history, Mapping):
                    for entry in _entries_from_history(history):
                        yield entry
            start_at += len(page_histories)
            # Refresh ``total`` from the latest response in case Jira
            # revised it mid-pagination (rare, but cheap to handle).
            new_total = page.get("total")
            if isinstance(new_total, int):
                total = new_total
            if page.get("isLast") is True:
                break
        return

    # mode == "cloud"
    # Cloud: drain with ``pageToken=<token>`` until ``isLast: true``
    # or no further ``nextPageToken``. Initial token comes from the
    # inline envelope; subsequent tokens from each follow-up response.
    initial_token = envelope.get("nextPageToken")
    token: Optional[str] = initial_token if isinstance(initial_token, str) else None
    while True:
        params: dict = {}
        if token:
            params["pageToken"] = token
        resp = jira.raw_get(path, params=params)
        page = resp if isinstance(resp, Mapping) else {}
        for history in _histories(page):
            if isinstance(history, Mapping):
                for entry in _entries_from_history(history):
                    yield entry
        if page.get("isLast") is True:
            break
        next_token = page.get("nextPageToken")
        if not isinstance(next_token, str) or not next_token:
            break
        if next_token == token:
            # Defensive: a server bug that returns the same token in a
            # loop would otherwise spin forever.
            break
        token = next_token


__all__ = [
    "ChangelogEntry",
    "iter_issue_changelog",
]
