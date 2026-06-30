"""``agentbundle list-installed`` subcommand.

Lists every installed ``(pack, adapter)`` row across the user and repo scope —
the state-file complement to ``list-packs`` (which queries a *catalogue* of
what is *available*). Reads the state files **read-only**; never writes.

By default it also resolves the catalogue once and joins each row against the
catalogue's ``pack.toml`` version to report a status (``up-to-date`` /
``upgrade-available`` / ``unknown``). ``--no-check`` (alias ``--offline``) skips
that join and prints only the state-only columns. ``--check-drift`` adds a
per-row count of locally edited files (on-disk SHA ≠ the SHA recorded in state).

Exit codes:
  0  — success (including "no packs installed" and an unresolvable catalogue).
  1  — only on an argument/environment error the listing genuinely can't survive.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import PackState, State


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle list-installed``."""
    import sys

    from agentbundle import scope as scope_mod
    from agentbundle.config import ConfigError, load_state

    requested_scope = getattr(args, "scope", None)
    scopes = [requested_scope] if requested_scope else ["user", "repo"]
    check = not getattr(args, "no_check", False)
    want_drift = getattr(args, "check_drift", False)

    # ── Gather (scope, root, State) read-only ─────────────────────────────────
    repo_root = Path(getattr(args, "root", ".")).resolve()
    scope_states: list[tuple[str, Path, "State"]] = []
    for sc in scopes:
        if sc == "repo":
            base, state_path = repo_root, repo_root / ".agentbundle-state.toml"
        else:  # user
            try:
                base = scope_mod.resolve_user_root()
            except scope_mod.UserScopeUnresolvable:
                # No resolvable home → no user-scope state to list. Not an error.
                continue
            state_path = base / ".agentbundle" / "state.toml"
        try:
            state = load_state(state_path)
        except ConfigError as exc:
            # An incompatible (e.g. legacy-schema) state file is a hard refusal
            # on read (RFC-0052). Warn and skip that scope rather than abort —
            # the other scope stays listable.
            print(f"list-installed: skipping {sc} scope: {exc}", file=sys.stderr)
            continue
        scope_states.append((sc, base, state))

    rows = _collect_rows(scope_states)
    if not rows:
        where = f"{requested_scope} scope" if requested_scope else "user or repo scope"
        print(f"no packs installed at {where}.")
        return 0

    # ── Catalogue join for LATEST / STATUS (unless --no-check) ─────────────────
    catalogue_resolved = False
    latest_by_pack: dict[str, str | None] = {}
    if check:
        catalogue_resolved, latest_by_pack = _resolve_latest(args)

    # ── Drift count (only when requested) ─────────────────────────────────────
    if want_drift:
        for row in rows:
            row["drift"] = _drift_count(row["_pack_state"], row["_root"])

    _print_table(rows, check=check, want_drift=want_drift,
                 catalogue_resolved=catalogue_resolved, latest_by_pack=latest_by_pack)
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_rows(
    scope_states: list[tuple[str, Path, "State"]],
) -> list[dict]:
    """Flatten every ``(pack, adapter)`` row across scopes into sorted dicts.

    Each row carries the display fields plus ``_pack_state`` / ``_root`` for a
    later (optional) drift pass. Sorted by (pack, adapter, scope) so output is
    deterministic.
    """
    rows: list[dict] = []
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
    rows.sort(key=lambda r: (r["pack"], r["adapter"], r["scope"]))
    return rows


def _resolve_latest(args: "argparse.Namespace") -> tuple[bool, dict[str, str | None]]:
    """Resolve the catalogue once and map each pack name to its latest version.

    Returns ``(catalogue_resolved, {pack_name: version_or_None})``. On an
    unresolvable catalogue returns ``(False, {})`` — the caller degrades every
    row to ``unknown`` rather than failing. A pack present in the catalogue but
    declaring an incompatible major version maps to ``None`` (also ``unknown``),
    detected directly (``pack_spec_version`` + ``_major``) so no refusal is
    printed — unlike ``check_spec_version_gate``, which prints and aborts.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import _major, resolve_catalogue_uri
    from agentbundle.config import ConfigError, load_pack_toml, pack_spec_version
    from agentbundle.version import SPEC_VERSION

    try:
        catalogue_dir = resolve_catalogue(resolve_catalogue_uri(args))
    except CatalogueError:
        return False, {}

    # Reuse list-packs' discovery so the layouts accepted stay identical.
    from agentbundle.commands.list_packs import _discover_pack_dirs

    cli_major = _major(SPEC_VERSION)
    latest: dict[str, str | None] = {}
    for pack_dir in _discover_pack_dirs(catalogue_dir):
        try:
            toml = load_pack_toml(pack_dir / "pack.toml")
        except ConfigError:
            continue
        pack = toml.get("pack", {})
        name = pack.get("name") or pack_dir.name
        declared = pack_spec_version(toml)
        if declared is not None and _major(declared) != cli_major:
            latest[name] = None  # incompatible major → unknown, don't compare
            continue
        latest[name] = pack.get("version") or None
    return True, latest


def _version_key(version: str) -> tuple[int, ...] | None:
    """Parse a dotted version into a comparable int tuple, or None if not numeric."""
    parts = version.lstrip("v").split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _status_for(installed: str, latest: str | None, *, catalogue_resolved: bool) -> str:
    """Compute a row's status from (installed, latest, resolvable?).

    ``up-to-date`` when installed is at or beyond latest; ``upgrade-available``
    when latest is strictly greater; ``unknown`` when the catalogue could not be
    resolved, the pack is absent from it, or either version isn't comparable.
    """
    if not catalogue_resolved or latest is None:
        return "unknown"
    a, b = _version_key(installed), _version_key(latest)
    if a is None or b is None:
        return "unknown"
    return "upgrade-available" if b > a else "up-to-date"


def _drift_count(pack_state: "PackState", root: Path) -> int:
    """Row-scoped count of locally edited files. Thin delegate to the shared
    ``_common.count_drifted_files`` so list-installed and the upgrade drift
    notice compute drift identically."""
    from agentbundle.commands._common import count_drifted_files

    return count_drifted_files(pack_state, root)


def _print_table(
    rows: list[dict],
    *,
    check: bool,
    want_drift: bool,
    catalogue_resolved: bool,
    latest_by_pack: dict[str, str | None],
) -> None:
    """Render the installed-packs table to stdout."""
    from agentbundle.commands._common import render_table

    headers = ["PACK", "ADAPTER", "SCOPE", "INSTALLED"]
    if check:
        headers += ["LATEST", "STATUS"]
    if want_drift:
        headers += ["DRIFT"]

    table_rows: list[list[str]] = []
    for r in rows:
        cells = [r["pack"], r["adapter"], r["scope"], r["installed"]]
        if check:
            latest = latest_by_pack.get(r["pack"])
            status = _status_for(
                r["installed"], latest, catalogue_resolved=catalogue_resolved
            )
            cells += [latest or "—", status]
        if want_drift:
            cells += [str(r.get("drift", 0))]
        table_rows.append(cells)

    render_table(headers, table_rows)
