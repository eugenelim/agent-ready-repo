"""``agentbundle list-installed`` subcommand.

Lists every installed ``(pack, adapter)`` row across the user and repo scope --
the state-file complement to ``list-packs`` (which queries a *catalogue* of
what is *available*). Reads the state files **read-only**; never writes.

By default it also resolves each row's recorded source catalogue once and joins
each row against its ``pack.toml`` version to report a status
(``up-to-date`` / ``upgrade-available`` / ``ahead`` / ``unknown``).
``--no-check`` (alias ``--offline``) skips that join and prints only the
state-only columns. ``--check-drift`` adds a per-row count of locally edited
files (on-disk SHA != the SHA recorded in state). ``--format json`` emits a
stable JSON contract (schema_version 1, RFC-0072 D5) to stdout with all
diagnostics on stderr. ``--updates-only`` hides ``up-to-date`` rows from
output while keeping the summary counts over the full set.

Exit codes:
  0  -- success (including "no packs installed" and unresolvable catalogues).
  1  -- only on an argument/environment error the listing genuinely can't survive.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------


class _RowCtx(NamedTuple):
    """Per-row resolution context written by ``_resolve_per_source``."""

    reason: str | None
    available_version: str | None


# ---------------------------------------------------------------------------
# Credential redaction helper
# ---------------------------------------------------------------------------


def _redact_error(msg: str) -> str:
    """Strip credentials from a ``CatalogueError`` message before output.

    Three forms are redacted:
    1. URL user-info (``user:pass@host``) -> ``***@host``
    2. Query-string credential tokens (keys containing ``token``, ``key``,
       ``secret``, ``password``, or ``auth``, case-insensitive) -> ``?k=***``
    3. Bearer-token values (``Bearer <token>``) -> ``Bearer ***``
    """
    # 1. URL user-info: anything before @ that contains : but no /
    msg = re.sub(r"[^/@]+:[^/@]+@", "***@", msg)
    # 2. Query/fragment token parameters -- keys that CONTAIN the sensitive substring
    msg = re.sub(
        r"(?i)([?&][^=&]*(?:token|key|secret|password|auth)[^=&]*=)[^&\s]*",
        r"\1***",
        msg,
    )
    # 3. Bearer tokens (with or without "Authorization:" prefix)
    msg = re.sub(r"(?i)Bearer\s+\S+", "Bearer ***", msg)
    return msg


# ---------------------------------------------------------------------------
# Status computation -- pure function (AC4, AC5, AC6)
# ---------------------------------------------------------------------------


def _compute_status_pair(
    installed: str,
    available_version: "str | None",
    *,
    reason_ctx: "str | None",
) -> "tuple[str, str | None]":
    """Return ``(status, status_reason)`` from installed/available versions.

    Four statuses: ``up-to-date``, ``upgrade-available``, ``ahead``,
    ``unknown``. ``reason_ctx`` wins over version comparisons -- it is already
    the resolved reason from ``_resolve_per_source``'s ladder.
    """
    # Ladder step 1: reason context propagated from source resolution
    if reason_ctx is not None:
        return ("unknown", reason_ctx)
    # Ladder step 2: defensive guard -- in practice T2 always supplies reason_ctx
    #                when available_version is None.
    if available_version is None:
        return ("unknown", "pack-not-found")
    # Ladder step 3: catalogue version parseability checked FIRST (spec ordering)
    b = _version_key(available_version)
    if b is None:
        return ("unknown", "unparseable-catalogue-version")
    # Ladder step 4: installed version parseability
    a = _version_key(installed)
    if a is None:
        return ("unknown", "unparseable-installed-version")
    # Zero-pad so (1,2) and (1,2,0) compare equal
    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))
    if a > b:
        return ("ahead", None)
    if b > a:
        return ("upgrade-available", None)
    return ("up-to-date", None)


# ---------------------------------------------------------------------------
# Version key helper
# ---------------------------------------------------------------------------


def _version_key(version: str) -> "tuple[int, ...] | None":
    """Parse a dotted version into a comparable int tuple, or None if non-numeric.

    A non-numeric segment (a pre-release / build tag like ``1.2.0-rc1`` or
    ``1.2.post1``) intentionally yields ``None`` -> the row reads ``unknown``
    rather than risking a wrong comparison; packs ship plain numeric versions.
    """
    parts = version.lstrip("v").split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Multi-source resolution (AC7-AC10, AC12)
# ---------------------------------------------------------------------------


def _resolve_per_source(
    rows: "list[dict]",
) -> "tuple[list[dict], dict[tuple[str, str, str], _RowCtx]]":
    """Resolve each unique canonical source exactly once; return (sources, row_ctx_map).

    ``row_ctx_map`` is keyed by ``(scope, pack, adapter)`` -- three fields --
    to avoid cross-scope collisions when the same ``(pack, adapter)`` pair is
    installed at both user and repo scope.

    Rows with ``canonicalize_source`` -> ``None`` get ``source-unknown``
    immediately and are not added to ``sources``.

    The returned ``sources`` list is sorted ascending by canonical source string
    (AC14 sources[] ordering).
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import _major
    from agentbundle.config import (
        ConfigError,
        canonicalize_source,
        load_pack_toml,
        pack_spec_version,
    )
    from agentbundle.version import SPEC_VERSION

    from agentbundle.commands.list_packs import _discover_pack_dirs

    cli_major = _major(SPEC_VERSION)

    # Group by canonical source; None-source rows get source-unknown immediately.
    by_source: "dict[str, list[dict]]" = {}
    row_ctx_map: "dict[tuple[str, str, str], _RowCtx]" = {}

    for row in rows:
        src = canonicalize_source(row["_pack_state"].source)
        key = (row["scope"], row["pack"], row["adapter"])
        if src is None:
            row_ctx_map[key] = _RowCtx(reason="source-unknown", available_version=None)
        else:
            by_source.setdefault(src, []).append(row)

    sources: "list[dict]" = []

    for src, src_rows in by_source.items():
        # Attempt catalogue resolution
        try:
            catalogue_dir = resolve_catalogue(src)
        except CatalogueError as exc:
            # source-unavailable: mark all rows in this group
            err_msg = _redact_error(str(exc))
            for row in src_rows:
                key = (row["scope"], row["pack"], row["adapter"])
                row_ctx_map[key] = _RowCtx(reason="source-unavailable", available_version=None)
            sources.append({
                "source": src,
                "resolved": False,
                "error_code": "catalogue-error",
                "error_message": err_msg,
            })
            continue

        # Walk the catalogue and build per-pack ctx map using a toml cache
        toml_cache: "dict[str, dict]" = {}
        pack_ctx: "dict[str, _RowCtx]" = {}

        for pack_dir in _discover_pack_dirs(catalogue_dir):
            try:
                toml = load_pack_toml(pack_dir / "pack.toml")
            except ConfigError:
                # malformed-catalogue -- store against the pack dir name as fallback
                pack_ctx[pack_dir.name] = _RowCtx(reason="malformed-catalogue", available_version=None)
                continue
            pack_section = toml.get("pack", {})
            name = pack_section.get("name") or pack_dir.name
            toml_cache[name] = toml
            # Ladder step 3 -- incompatible-contract
            declared = pack_spec_version(toml)
            if declared is not None and _major(declared) != cli_major:
                pack_ctx[name] = _RowCtx(reason="incompatible-contract", available_version=None)
                continue
            # Ladder step 5 -- version absent or non-string
            version = pack_section.get("version")
            if not version or not isinstance(version, str):
                pack_ctx[name] = _RowCtx(reason="unparseable-catalogue-version", available_version=None)
                continue
            pack_ctx[name] = _RowCtx(reason=None, available_version=version)

        # Apply per-row pack-not-found + adapter check
        for row in src_rows:
            key = (row["scope"], row["pack"], row["adapter"])
            pack_name = row["pack"]
            if pack_name not in pack_ctx:
                row_ctx_map[key] = _RowCtx(reason="pack-not-found", available_version=None)
                continue
            ctx = pack_ctx[pack_name]
            if ctx.reason is not None:
                # malformed-catalogue, incompatible-contract, or unparseable-catalogue-version
                row_ctx_map[key] = ctx
                continue
            # Ladder step 4 -- adapter-no-longer-supported
            toml = toml_cache.get(pack_name, {})
            allowed_adapters = (
                toml.get("pack", {}).get("install", {}).get("allowed-adapters")
            )
            if allowed_adapters is not None and row["adapter"] not in allowed_adapters:
                row_ctx_map[key] = _RowCtx(reason="adapter-no-longer-supported", available_version=None)
            else:
                row_ctx_map[key] = ctx

        sources.append({
            "source": src,
            "resolved": True,
            "error_code": None,
            "error_message": None,
        })

    # Sort sources ascending by canonical source string (AC14)
    sources.sort(key=lambda s: s["source"])
    return sources, row_ctx_map


# ---------------------------------------------------------------------------
# JSON renderer (T4)
# ---------------------------------------------------------------------------


def _render_json(
    rows: "list[dict]",
    sources: "list[dict]",
    *,
    scope_val: str,
    updates_only: bool,
    check: bool,
) -> str:
    """Serialize the list-installed result to a JSON string (schema_version 1).

    ``rows`` carry enriched fields written by the run() enrichment step:
    ``available_version``, ``canonical_source``, ``status``, ``status_reason``.
    ``drift`` is present only when ``--check-drift`` was active.

    Per-row JSON dicts are constructed explicitly -- no raw row dicts are
    serialized -- to emit exactly the nine contract keys and avoid serialization
    crashes (``PackState`` is not JSON-serializable).
    """
    # Sort rows deterministically (AC14)
    display_rows = sorted(rows, key=lambda r: (r["scope"], r["pack"], r["adapter"]))
    # Sort sources ascending by canonical source string (AC14)
    sources = sorted(sources, key=lambda s: s["source"])

    # Summary counts over full pre-filter set
    summary = {"total": 0, "up_to_date": 0, "upgrade_available": 0, "ahead": 0, "unknown": 0}
    for row in display_rows:
        summary["total"] += 1
        if check:
            st = row.get("status")
            if st == "up-to-date":
                summary["up_to_date"] += 1
            elif st == "upgrade-available":
                summary["upgrade_available"] += 1
            elif st == "ahead":
                summary["ahead"] += 1
            elif st == "unknown":
                summary["unknown"] += 1

    # Apply --updates-only filter (only when check is True)
    if updates_only and check:
        display_rows = [r for r in display_rows if r.get("status") != "up-to-date"]

    # Build per-row JSON dicts with exactly nine contract keys
    json_rows = []
    for row in display_rows:
        json_rows.append({
            "pack": row["pack"],
            "adapter": row["adapter"],
            "scope": row["scope"],
            "source": row.get("canonical_source"),
            "installed_version": row["installed"],
            "available_version": row.get("available_version"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
            "drift_count": row.get("drift"),  # None when --check-drift not active
        })

    result = {
        "schema_version": 1,
        "command": "list-installed",
        "scope": scope_val,
        "updates_only": updates_only,
        "sources": sources,
        "rows": json_rows,
        "summary": summary,
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Table renderer (T5)
# ---------------------------------------------------------------------------


def _print_table(
    rows: "list[dict]",
    *,
    check: bool,
    want_drift: bool,
    updates_only: bool,
) -> None:
    """Render the installed-packs table to stdout.

    Reads enriched fields (``available_version``, ``canonical_source``,
    ``status``, ``status_reason``) directly from row dicts -- no separate
    ``latest_by_pack`` or ``catalogue_resolved`` parameters.

    SOURCE column: shown only when 2+ distinct canonical sources are present
    in the full pre-filter row set (OQ1). Source strings truncated to 40
    visible chars.

    ``--updates-only`` filter: skip rows where ``status == "up-to-date"``
    (only when ``check is True``).
    """
    from agentbundle.commands._common import render_table

    # Determine whether to show SOURCE column -- computed over pre-filter rows
    distinct_non_null_sources = {
        r["canonical_source"] for r in rows if r.get("canonical_source") is not None
    }
    show_source = check and len(distinct_non_null_sources) >= 2

    headers = ["PACK", "ADAPTER", "SCOPE", "INSTALLED"]
    if show_source:
        headers.append("SOURCE")
    if check:
        headers += ["LATEST", "STATUS"]
    if want_drift:
        headers += ["DRIFT"]

    # Apply --updates-only filter (only when check is True)
    display_rows = rows
    if updates_only and check:
        display_rows = [r for r in rows if r.get("status") != "up-to-date"]

    table_rows: "list[list[str]]" = []
    for r in display_rows:
        cells = [r["pack"], r["adapter"], r["scope"], r["installed"]]
        if show_source:
            src = r.get("canonical_source")
            if src is None:
                cells.append("—")  # em dash
            elif len(src) > 40:
                cells.append(src[:39] + "…")  # ellipsis
            else:
                cells.append(src)
        if check:
            available = r.get("available_version")
            cells.append(available if available is not None else "—")
            cells.append(r.get("status") or "unknown")
        if want_drift:
            cells.append(str(r.get("drift", 0)))
        table_rows.append(cells)

    render_table(headers, table_rows)


# ---------------------------------------------------------------------------
# Row collection
# ---------------------------------------------------------------------------


def _collect_rows(
    scope_states: "list[tuple[str, Path, State]]",
) -> "list[dict]":
    """Flatten every ``(pack, adapter)`` row across scopes into sorted dicts.

    Each row carries the display fields plus ``_pack_state`` / ``_root`` for a
    later (optional) drift pass. Sorted by (scope, pack, adapter) so output is
    deterministic (RFC-0072 D5).
    """
    rows: "list[dict]" = []
    for scope_name, root, state in scope_states:
        for (pack, adapter), ps in state.packs.items():
            rows.append(
                {
                    "pack": pack,
                    "adapter": adapter,
                    "scope": scope_name,
                    "installed": ps.installed_version,
                    "_pack_state": ps,
                    "_root": root,
                }
            )
    rows.sort(key=lambda r: (r["scope"], r["pack"], r["adapter"]))
    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle list-installed``."""
    import sys

    from agentbundle import scope as scope_mod
    from agentbundle.config import ConfigError, canonicalize_source, load_state

    # Read format/filter args at the very top -- before the empty-result check
    fmt = getattr(args, "format", "table")
    updates_only = getattr(args, "updates_only", False)
    scope_val = getattr(args, "scope", None) or "all"

    # Deprecation warning for the (now-ignored) catalogue positional
    if getattr(args, "catalogue", None) is not None:
        print(
            "agentbundle list-installed: the catalogue positional is ignored; "
            "rows are resolved against their recorded provenance. "
            "Use --no-check to skip resolution entirely.",
            file=sys.stderr,
        )

    requested_scope = getattr(args, "scope", None)
    scopes = [requested_scope] if requested_scope else ["user", "repo"]
    check = not getattr(args, "no_check", False)
    want_drift = getattr(args, "check_drift", False)

    # Gather (scope, root, State) read-only
    repo_root = Path(getattr(args, "root", ".")).resolve()
    scope_states: "list[tuple[str, Path, State]]" = []
    for sc in scopes:
        if sc == "repo":
            base, state_path = repo_root, repo_root / ".agentbundle-state.toml"
        else:  # user
            try:
                base = scope_mod.resolve_user_root()
            except scope_mod.UserScopeUnresolvable:
                continue
            state_path = base / ".agentbundle" / "state.toml"
        try:
            state = load_state(state_path)
        except ConfigError as exc:
            print(f"list-installed: skipping {sc} scope: {exc}", file=sys.stderr)
            continue
        scope_states.append((sc, base, state))

    rows = _collect_rows(scope_states)

    # Empty-result path (format-aware)
    if not rows:
        where = f"{requested_scope} scope" if requested_scope else "user or repo scope"
        if fmt == "json":
            json_str = _render_json(
                [], [], scope_val=scope_val, updates_only=updates_only, check=check
            )
            print(json_str)
        else:
            print(f"no packs installed at {where}.")
        return 0

    # Catalogue join for LATEST / STATUS (unless --no-check)
    sources_list: "list[dict]" = []
    if check:
        sources_list, row_ctx_map = _resolve_per_source(rows)
    else:
        row_ctx_map = {
            (row["scope"], row["pack"], row["adapter"]): _RowCtx(reason=None, available_version=None)
            for row in rows
        }

    # Row enrichment: write computed fields into each row dict
    for row in rows:
        key = (row["scope"], row["pack"], row["adapter"])
        ctx = row_ctx_map[key]
        row["canonical_source"] = canonicalize_source(row["_pack_state"].source)
        row["available_version"] = ctx.available_version
        if check:
            status, reason = _compute_status_pair(
                row["installed"], ctx.available_version, reason_ctx=ctx.reason
            )
        else:
            status, reason = None, None
        row["status"] = status
        row["status_reason"] = reason

    # Drift count (only when requested)
    if want_drift:
        from agentbundle.commands._common import count_drifted_files

        for row in rows:
            row["drift"] = count_drifted_files(row["_pack_state"], row["_root"])

    # Render
    if fmt == "json":
        json_str = _render_json(
            rows, sources_list, scope_val=scope_val, updates_only=updates_only, check=check
        )
        print(json_str)
    else:
        _print_table(rows, check=check, want_drift=want_drift, updates_only=updates_only)

    return 0
