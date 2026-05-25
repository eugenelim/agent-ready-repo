"""On-disk cache for per-issue derived rows.

Implements docs/specs/flow-metrics.md § "Caching":

- :func:`cache_key` derives the sha256 over a canonical-JSON dict whose
  fields are exactly those listed in the spec. Cohort JQL, ``--metrics``
  and ``--include-subtasks`` are deliberately absent — they affect only
  post-fetch aggregation, so the same cache feeds multiple aggregation
  modes. ``align_join_field`` and ``align_teams_path`` are pinned to
  ``None`` for project-scope runs (they have no effect on what's fetched)
  and included as-is for program/portfolio scope.
- :func:`read_cache` streams rows back from ``<key>.jsonl`` lazily.
- :func:`write_cache_tee` tees the source iterator to
  ``<key>.jsonl.<pid>.tmp`` per row and ``os.replace``s to the final
  name only on full drain. Partial drains (exception, generator close)
  leave the ``.tmp`` behind for :func:`cleanup_stale_tmps` to remove.
- :func:`cleanup_stale_tmps` removes any ``*.tmp`` older than one hour
  at startup. The glob matches both ``<key>.jsonl.tmp`` and
  ``<key>.jsonl.<pid>.tmp`` so a future name variant doesn't strand
  partial files indefinitely.

The cache module operates on :class:`~flow_metrics.per_issue.PerIssueRow`
iterators. It serialises datetime-typed fields to ISO-8601 strings and
parses them back on read — every other field is JSON-native.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import types
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Iterator,
    Mapping,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .per_issue import PerIssueRow


CACHE_SCHEMA_VERSION = "1.1"  # 1.1: PerIssueRow grew the `teams` tuple field
STALE_TMP_AGE_SECONDS = 3600
TMP_GLOB = "*.tmp"
_PROGRAM_SCOPE_KINDS = frozenset({"program", "portfolio"})


def _normalize_clause(s: Optional[str]) -> str:
    """v1 normalization: strip + collapse whitespace.

    Same shape for JQL and OData — both follow the spec's conservative
    rule that any non-whitespace edit invalidates the cache.
    """
    if s is None:
        return ""
    return " ".join(s.split())


def cache_key(
    scope: Mapping[str, Any],
    window: Mapping[str, str],
    user_jql: Optional[str],
    user_align_filter: Optional[str],
    state_config_sha: str,
    issuetype_config_sha: str,
    team_field_override: Optional[str],
    align_join_field: Optional[str],
    align_teams_path: Optional[str],
) -> str:
    """Return the sha256 cache key for a fetch.

    ``scope`` carries ``kind`` (``"project"`` | ``"program"`` |
    ``"portfolio"``), ``value`` (project key or align id), and optional
    ``team`` (NAME for project-scope sub-runs, None otherwise).

    ``window`` carries ``from`` and ``to`` as ``YYYY-MM-DD`` strings.

    For project-scope runs ``align_join_field`` and ``align_teams_path``
    are pinned to None regardless of what the caller passes — they have
    no effect on the project-scope fetch, so changing them mustn't
    invalidate the cache.
    """
    scope_kind = scope["kind"]
    if scope_kind not in _PROGRAM_SCOPE_KINDS:
        align_join_field = None
        align_teams_path = None

    d = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "scope_kind": scope_kind,
        "scope_value": str(scope["value"]),
        "team": scope.get("team"),
        "from": window["from"],
        "to": window["to"],
        "user_jql": _normalize_clause(user_jql),
        "user_align_filter": _normalize_clause(user_align_filter),
        "state_config_sha": state_config_sha,
        "issuetype_config_sha": issuetype_config_sha,
        "team_field_override": team_field_override,
        "align_join_field": align_join_field,
        "align_teams_path": align_teams_path,
    }
    canonical = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ensure_cache_dir(cache_dir: Path) -> None:
    """Create ``cache_dir`` (and parents) with mode 0700 on Unix.

    Idempotent — re-runs leave an existing directory untouched (except
    for the chmod, which is also idempotent). Windows has no equivalent
    of the 0700 bit; we just skip the chmod there.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(cache_dir, 0o700)
        except OSError:
            pass


# Cached at first call: which PerIssueRow fields carry datetime values
# (directly or as Optional[datetime]) and which carry tuples. Computed
# by introspecting the dataclass so the cache module stays robust to
# PerIssueRow growing new datetime / tuple fields.
_DATETIME_FIELD_NAMES: Optional[frozenset] = None
_TUPLE_FIELD_NAMES: Optional[frozenset] = None


def _datetime_field_names() -> frozenset:
    global _DATETIME_FIELD_NAMES
    if _DATETIME_FIELD_NAMES is None:
        names = []
        hints = get_type_hints(PerIssueRow)
        # Accept both ``Optional[datetime]`` (origin ``typing.Union``) and
        # PEP 604 ``datetime | None`` (origin ``types.UnionType``). Without
        # the second arm, a future ``per_issue.py`` switch to the ``|``
        # syntax would silently break the cache: datetimes would still
        # be *written* as ISO strings (via ``isinstance`` at write-time)
        # but never *parsed back*, leaving ``PerIssueRow`` carrying raw
        # strings where datetimes are expected.
        for f in fields(PerIssueRow):
            ann = hints.get(f.name, f.type)
            if ann is datetime:
                names.append(f.name)
                continue
            origin = get_origin(ann)
            is_union = origin is Union or origin is types.UnionType
            if is_union and datetime in get_args(ann):
                names.append(f.name)
        _DATETIME_FIELD_NAMES = frozenset(names)
    return _DATETIME_FIELD_NAMES


def _tuple_field_names() -> frozenset:
    """PerIssueRow fields whose annotation is ``Tuple[...]``.

    JSON has no tuple type, so ``asdict`` → ``json.dumps`` → ``json.loads``
    on a tuple-valued field returns a list. Without re-tupling on read,
    a cached round-trip would not compare equal to the source row, which
    breaks both T7's roundtrip equality guarantee and any downstream
    code that relies on tuple semantics (immutability, hashing).
    """
    global _TUPLE_FIELD_NAMES
    if _TUPLE_FIELD_NAMES is None:
        names = []
        hints = get_type_hints(PerIssueRow)
        for f in fields(PerIssueRow):
            ann = hints.get(f.name, f.type)
            if get_origin(ann) is tuple:
                names.append(f.name)
        _TUPLE_FIELD_NAMES = frozenset(names)
    return _TUPLE_FIELD_NAMES


def _row_to_json(row: PerIssueRow) -> str:
    d = asdict(row)
    for name in _datetime_field_names():
        v = d.get(name)
        if isinstance(v, datetime):
            d[name] = v.isoformat()
    return json.dumps(d, separators=(",", ":"))


def _json_to_row(line: str) -> PerIssueRow:
    d = json.loads(line)
    dt_fields = _datetime_field_names()
    tup_fields = _tuple_field_names()
    kwargs = {}
    for f in fields(PerIssueRow):
        v = d.get(f.name)
        if v is not None and f.name in dt_fields:
            v = datetime.fromisoformat(v)
        elif v is not None and f.name in tup_fields and isinstance(v, list):
            v = tuple(v)
        kwargs[f.name] = v
    return PerIssueRow(**kwargs)


def read_cache(cache_dir: Path, key: str) -> Optional[Iterator[PerIssueRow]]:
    """Stream cached rows for ``key`` if a finalised file exists.

    Returns None on miss (no ``<key>.jsonl`` in ``cache_dir``). The
    returned iterator opens the file lazily and yields one
    :class:`PerIssueRow` per line — peak memory is O(one row).
    """
    path = cache_dir / "{}.jsonl".format(key)
    if not path.is_file():
        return None

    def _iter() -> Iterator[PerIssueRow]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                yield _json_to_row(line)

    return _iter()


def write_cache_tee(
    cache_dir: Path,
    key: str,
    source: Iterator[PerIssueRow],
) -> Iterator[PerIssueRow]:
    """Tee ``source`` to ``<key>.jsonl.<pid>.tmp`` while yielding each row.

    On full drain, ``os.replace`` promotes the tmp to ``<key>.jsonl``.
    On any exception during the source iteration — or when the consumer
    abandons the generator mid-stream — the tmp is left in place for
    :func:`cleanup_stale_tmps` to remove on a later startup.

    Concurrent runs with the same key are tolerated: each gets its own
    PID-suffixed tmp, drains independently, and finalises by ``os.replace``-
    ing *its own* tmp onto ``<key>.jsonl``. Whichever process replaces
    last wins the final filename; the earlier process's promoted final
    is simply overwritten. Cache content is a pure function of the key,
    so the winner is content-identical to the loser. Neither tmp is
    orphaned by a successful drain: each is consumed by its own replace.
    """
    _ensure_cache_dir(cache_dir)
    tmp_name = "{}.jsonl.{}.tmp".format(key, os.getpid())
    tmp_path = cache_dir / tmp_name
    final_path = cache_dir / "{}.jsonl".format(key)

    f = open(tmp_path, "w", encoding="utf-8")
    drained = False
    try:
        for row in source:
            f.write(_row_to_json(row))
            f.write("\n")
            f.flush()
            yield row
        drained = True
    finally:
        f.close()
        if drained:
            os.replace(tmp_path, final_path)


def cleanup_stale_tmps(cache_dir: Path) -> None:
    """Remove ``*.tmp`` files in ``cache_dir`` older than 1 hour.

    No-op when ``cache_dir`` does not exist (fresh installs). The
    1-hour cutoff is the spec's threshold; concurrent fresh runs are
    safe because their tmp names include the PID and are well under
    one hour old by the time this runs on a sibling startup.
    """
    if not cache_dir.is_dir():
        return
    cutoff = time.time() - STALE_TMP_AGE_SECONDS
    for path in cache_dir.glob(TMP_GLOB):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            try:
                path.unlink()
            except OSError:
                pass


__all__ = [
    "CACHE_SCHEMA_VERSION",
    "cache_key",
    "cleanup_stale_tmps",
    "read_cache",
    "write_cache_tee",
]
