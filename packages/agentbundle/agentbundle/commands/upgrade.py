"""``agentbundle upgrade`` — whole-pack or per-primitive upgrade.

Two shapes:

1. **Whole-pack upgrade** (no ``--skill`` / ``--agent`` / ``--hook`` /
   ``--seed`` / ``--command`` flag):

   - Resolve the catalogue URI to the new pack version directory.
   - Run the spec-version gate.
   - Render the new projection in memory.
   - Walk every (relpath, content) pair; apply the Tier-1/2/3 contract via
     ``safety.classify`` + ``safety.write_jailed``/``safety.write_companion``.
   - Update ``PackState.installed_version`` to the version the resolved
     catalogue's ``pack.toml`` declares under ``[pack] version`` — the upgrade
     target is derived from the catalogue, not supplied by the operator.
   - If the current state has any ``primitive_versions`` for this pack, emit
     a warning to stderr *before* proceeding (mixed-version surface).

2. **Per-primitive upgrade** (exactly one of the five primitive flags set):

   - Identify the named primitive's file set from the rendered projection
     using a path-segment heuristic (see ``_filter_for_primitive``).
   - Validate that the primitive exists (non-empty filter result → exists).
   - Apply Tier-1/2/3 contract for the filtered file set only.
   - Record ``PackState.primitive_versions[<ptype>][<name>]`` = the derived
     target version.
   - Leave ``PackState.installed_version`` unchanged.

Writes go through ``safety.write_jailed`` — path-jail is non-optional.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.user_config import UserConfig

from agentbundle.catalogue import CatalogueError, resolve_catalogue
from agentbundle.commands._common import (
    _major,
    check_spec_version_gate,
    confirm_or_refuse,
    format_plan_line,
    plan_action,
    resolve_catalogue_uri,
    resolve_state_path,
    summarize_plan,
)
from agentbundle.config import (
    ConfigError,
    canonicalize_source,
    dump_state,
    load_pack_toml,
    load_state,
    pack_spec_version,
)
from agentbundle.commands.list_installed import _version_key
from agentbundle.version import SPEC_VERSION
from agentbundle import safety


# Mapping from CLI flag attribute name → (primitive-type key, source-dir segment).
# The source-dir segment is the subdirectory name under ``.apm/`` that holds
# the primitive (used by ``_filter_for_primitive`` to scope path matches).
_PRIMITIVE_FLAG_MAP: dict[str, tuple[str, str]] = {
    "skill":   ("skill",        "skills"),
    "agent":   ("agent",        "agents"),
    "hook":    ("hook-body",    "hooks"),
    "seed":    ("seed",         "seeds"),
    "command": ("command",      "commands"),
}


def _was_dist_tree_install(pack_state: "object") -> bool:
    """True when the pack was installed via the dist-tree (catalogue-publishing) path."""
    return any(
        rp.startswith(("apm/", "claude-plugins/")) or rp == "marketplace.json"
        for rp in pack_state.files  # type: ignore[attr-defined]
    )


@dataclass
class _BulkRow:
    """One (pack, adapter) row in a bulk upgrade operation."""

    pack: str
    adapter: str
    scope: str
    pack_state: "object"  # PackState

    # set during preflight (source/version phase)
    canonical_source: "str | None" = None
    catalogue_dir: "object | None" = None  # Path | None
    pack_dir: "object | None" = None       # Path | None
    status: str = "unknown"
    status_reason: "str | None" = None
    installed_version: "str | None" = None
    available_version: "str | None" = None
    pack_toml: "dict | None" = None

    # set during preflight (render/path-jail phase)
    _projection: "dict | None" = None      # dict[str, bytes] | None
    allowed_prefixes: "list | None" = None  # list[str] | None
    resolved_adapter: "str | None" = None  # repo scope only

    # set during apply
    outcome: str = "planned"


def _classify_row(
    row: "_BulkRow",
    pack_toml: "dict | None",
) -> "tuple[str, str | None, str | None]":
    """Pure classification.  Returns (status, status_reason, available_version).

    ``pack_toml`` is ``None`` when the pack was not found in the catalogue.
    """
    # 1. Pack presence
    if pack_toml is None:
        return "unknown", "pack-not-found", None

    # 2. Contract compatibility — inline major comparison, NOT check_spec_version_gate()
    raw_spec_version = pack_spec_version(pack_toml)
    if raw_spec_version is not None and _major(raw_spec_version) != _major(SPEC_VERSION):
        return "unknown", "incompatible-contract", None

    # 3. Adapter allowed
    allowed = pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")
    if allowed is not None and row.adapter not in allowed:
        return "unknown", "adapter-no-longer-supported", None

    # 4. Parse catalogue version
    available_str = pack_toml.get("pack", {}).get("version", "")
    av_key = _version_key(available_str)
    if av_key is None:
        return "unknown", "unparseable-catalogue-version", None

    # 5. Parse installed version
    iv_key = _version_key(row.pack_state.installed_version or "")  # type: ignore[attr-defined]
    if iv_key is None:
        return "unknown", "unparseable-installed-version", None

    # 6. Zero-pad both tuples to equal length before comparison
    max_len = max(len(iv_key), len(av_key))
    iv_padded = iv_key + (0,) * (max_len - len(iv_key))
    av_padded = av_key + (0,) * (max_len - len(av_key))

    if iv_padded == av_padded:
        return "up-to-date", None, available_str
    elif iv_padded < av_padded:
        return "upgrade-available", None, available_str
    else:
        return "ahead", None, available_str


def _redact_credentials(text: str) -> str:
    """Sanitize text for output — remove URL user-info, credential query params, bearer tokens."""
    import re
    # 1. URL user-info: scheme://user:pass@host -> scheme://host
    text = re.sub(r"((?:https?|git\+https?|ssh)://)[^@/]*:[^@/]*@", r"\1", text)
    # 2. Query-string credential params
    text = re.sub(
        r"(?i)([?&])(access_token|token|api_key|private_token|auth)=[^&\s#]*",
        r"\1\2=[REDACTED]",
        text,
    )
    # 3. Bearer tokens
    text = re.sub(r"(?i)(Bearer\s+)\S+", r"\1[REDACTED]", text)
    return text


def _print_err(msg: str) -> None:
    """Print *msg* to stderr."""
    print(msg, file=sys.stderr)


def _run_source_version_preflight(
    state: "object",
    scope: str,
    root: "Path",
) -> "tuple[list, dict]":
    """Phase 1 preflight: source resolution and version classification.

    Returns ``(rows, source_resolution_map)`` where ``rows`` is a list of
    :class:`_BulkRow` with ``status``/``status_reason``/``available_version``
    populated, and ``source_resolution_map`` maps canonical-source →
    ``(catalogue_dir, error_code, error_message)``.
    """
    rows = [
        _BulkRow(
            pack=pack_name,
            adapter=adapter,
            scope=scope,
            pack_state=ps,
            installed_version=ps.installed_version,
        )
        for (pack_name, adapter), ps in state.packs.items()  # type: ignore[attr-defined]
    ]

    source_resolution_map: dict = {}

    for row in rows:
        cs = canonicalize_source(row.pack_state.source)  # type: ignore[attr-defined]
        row.canonical_source = cs
        if cs is None:
            row.status = "unknown"
            row.status_reason = "source-unknown"
            continue

        if cs not in source_resolution_map:
            try:
                cat_dir = resolve_catalogue(cs)
                source_resolution_map[cs] = (cat_dir, None, None)
            except CatalogueError as exc:
                source_resolution_map[cs] = (None, "catalogue-error", _redact_credentials(str(exc)))

        cat_dir, _err_code, _err_msg = source_resolution_map[cs]
        if cat_dir is None:
            row.status = "unknown"
            row.status_reason = "source-unavailable"
            continue

        pack_dir = _locate_pack(cat_dir, row.pack)
        if pack_dir is None:
            row.status = "unknown"
            row.status_reason = "pack-not-found"
            continue
        row.pack_dir = pack_dir
        row.catalogue_dir = cat_dir

        try:
            pack_toml = load_pack_toml(pack_dir / "pack.toml")
        except ConfigError:
            row.status = "unknown"
            row.status_reason = "malformed-catalogue"
            continue

        row.pack_toml = pack_toml
        row.status, row.status_reason, row.available_version = _classify_row(row, pack_toml)

    return rows, source_resolution_map


def _preflight_render_and_jail(
    row: "_BulkRow",
    root: "Path",
    user_config: "object",
) -> "tuple[dict | None, str | None]":
    """Render and path-jail check for one upgrade-available row.

    Sets ``row._projection``, ``row.allowed_prefixes``, and (repo scope)
    ``row.resolved_adapter`` on success.  Returns ``(projection, None)`` on
    success, ``(None, error_reason)`` on failure.
    """
    from agentbundle.commands.install import (
        _AdapterResolutionRefused,
        _adapter_allowed_prefixes_repo,
        _adapter_allowed_prefixes_user,
        _render_for_repo_scope,
        _render_for_user_scope,
        _resolve_target_adapter,
        _rewrite_user_scope_hook_paths,
    )

    # Dist-tree guard — bulk upgrade does not support dist-tree render path
    if _was_dist_tree_install(row.pack_state):
        return None, "render-failed"

    pack_dir = row.pack_dir
    pack_toml = row.pack_toml
    pack_name = row.pack
    adapter = row.pack_state.adapter  # type: ignore[attr-defined]

    _pack_install_table = (pack_toml or {}).get("pack", {}).get("install")
    _pack_allowed_adapters = None
    if isinstance(_pack_install_table, dict):
        _raw_aa = _pack_install_table.get("allowed-adapters")
        if isinstance(_raw_aa, list):
            _pack_allowed_adapters = [s for s in _raw_aa if isinstance(s, str)]
    _pack_contract_version = (
        (pack_toml or {}).get("pack", {}).get("adapter-contract", {}).get("version")
        if isinstance((pack_toml or {}).get("pack", {}).get("adapter-contract"), dict)
        else None
    )

    try:
        if row.scope == "user":
            try:
                projection = _render_for_user_scope(
                    pack_dir,
                    adapter=None,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=adapter,
                    command_name="upgrade",
                    user_config=user_config,
                )
            except _AdapterResolutionRefused:
                return None, "render-failed"
            try:
                target_adapter = _resolve_target_adapter(
                    pack_dir,
                    scope="user",
                    adapter=None,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=adapter,
                    command_name="upgrade",
                    user_config=user_config,
                )
            except _AdapterResolutionRefused:
                return None, "render-failed"
            projection = _rewrite_user_scope_hook_paths(
                projection,
                pack_name=pack_name,
                target_adapter=target_adapter,
            )
            allowed_prefixes = _adapter_allowed_prefixes_user(adapter or "claude-code")
            try:
                safety.assert_projection_jailed(
                    root, sorted(projection.keys()), allowed_prefixes, command="upgrade"
                )
            except safety.PathJailError:
                return None, "path-jail-violation"
            row._projection = projection
            row.allowed_prefixes = allowed_prefixes
            return projection, None
        else:
            # Repo scope
            try:
                resolved_adapter, projection = _render_for_repo_scope(
                    pack_dir,
                    adapter=None,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=adapter,
                    command_name="upgrade",
                    user_config=user_config,
                )
            except _AdapterResolutionRefused:
                return None, "render-failed"
            allowed_prefixes = _adapter_allowed_prefixes_repo(resolved_adapter)
            try:
                safety.assert_projection_jailed(
                    root, sorted(projection.keys()), allowed_prefixes, command="upgrade"
                )
            except safety.PathJailError:
                return None, "path-jail-violation"
            row._projection = projection
            row.allowed_prefixes = allowed_prefixes
            row.resolved_adapter = resolved_adapter
            return projection, None
    except Exception:
        return None, "render-failed"


def _run_preflight(
    state: "object",
    scope: str,
    root: "Path",
    user_config: "object",
) -> "tuple[list, dict]":
    """Full two-phase preflight: source/version + render/path-jail.

    Returns ``(rows, source_resolution_map)``.
    """
    rows, source_resolution_map = _run_source_version_preflight(state, scope, root)

    for row in rows:
        if row.status != "upgrade-available":
            continue
        _, error_reason = _preflight_render_and_jail(row, root, user_config)
        if error_reason is not None:
            row.status = "unknown"
            row.status_reason = error_reason
            row._projection = None

    return rows, source_resolution_map


def _apply_single_row(
    row: "_BulkRow",
    state: "object",
    state_path: "Path",
    root: "Path",
    args: "object",
) -> "tuple[bool, list[str]]":
    """Apply one upgrade row.  Returns ``(success, companions)``.

    Never re-renders — uses ``row._projection`` (pre-populated by preflight or
    by the single-pack render in ``run()``).  Does NOT emit to stdout; stdout
    in bulk mode is owned by ``_print_plan_table``/``_finalize``, and in
    single-pack mode the recap at the end of ``run()`` is emitted after reading
    the returned ``companions``.
    """
    work_projection = row._projection
    pack_state = row.pack_state
    effective_scope = row.scope
    allowed_prefixes = row.allowed_prefixes
    pack_name = row.pack
    to_version = row.available_version
    pack_dir = row.pack_dir
    pack_toml = row.pack_toml

    # Per-primitive flags — read from args so single-pack mode works unchanged.
    # In bulk mode args.skill etc. are all None → is_per_primitive is False.
    is_per_primitive = False
    prim_flag: "str | None" = None
    prim_name: "str | None" = None
    for flag_attr in _PRIMITIVE_FLAG_MAP:
        val = getattr(args, flag_attr, None)
        if val:
            prim_flag = flag_attr
            prim_name = val
            is_per_primitive = True
            break

    _pack_install_table = (pack_toml or {}).get("pack", {}).get("install")
    _pack_allowed_adapters = None
    if isinstance(_pack_install_table, dict):
        _raw_aa = _pack_install_table.get("allowed-adapters")
        if isinstance(_raw_aa, list):
            _pack_allowed_adapters = [s for s in _raw_aa if isinstance(s, str)]
    _pack_contract_version = (
        (pack_toml or {}).get("pack", {}).get("adapter-contract", {}).get("version")
        if isinstance((pack_toml or {}).get("pack", {}).get("adapter-contract"), dict)
        else None
    )

    user_config = getattr(args, "_user_config", None)

    # ── Path-jail pre-flight (AC4) ──────────────────────────────────────────────
    try:
        safety.assert_projection_jailed(
            root, sorted(work_projection), allowed_prefixes, command="upgrade"
        )
    except safety.PathJailError as exc:
        _print_err(f"upgrade: {exc}")
        return False, []

    # ── Walk projection; apply Tier contract ─────────────────────────────────────
    companions: list[str] = []
    for relpath, content in sorted(work_projection.items()):
        tier = safety.classify(relpath, root, state)

        if tier is safety.Tier.TIER_3:
            tier = safety.Tier.TIER_1

        if tier is safety.Tier.TIER_2:
            try:
                safety.write_companion(root, relpath, content)
            except safety.PathJailError as exc:
                _print_err(f"upgrade: {exc}")
                return False, companions
            companions.append(safety.companion_path(Path(relpath)).as_posix())
            pack_state.files[relpath] = {  # type: ignore[attr-defined]
                "sha": safety.sha256_bytes(content),
                "from-pack-version": to_version,
            }
        else:
            try:
                safety.write_jailed(
                    root, relpath, content,
                    scope=effective_scope,
                    allowed_prefixes=allowed_prefixes,
                )
            except safety.PathJailError as exc:
                _print_err(f"upgrade: {exc}")
                return False, companions
            pack_state.files[relpath] = {  # type: ignore[attr-defined]
                "sha": safety.sha256_bytes(content),
                "from-pack-version": to_version,
            }

    # ── Hook-wiring reconciliation (user-scope, whole-pack only) ─────────────────
    if effective_scope == "user" and not is_per_primitive:
        from agentbundle.commands.install import (
            _AdapterResolutionRefused,
            _merge_user_scope_hook_wiring,
            _refresh_merge_target_shas,
            _resolve_target_adapter,
        )

        try:
            new_target_adapter = _resolve_target_adapter(
                pack_dir,
                scope="user",
                adapter=None,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=pack_state.adapter,  # type: ignore[attr-defined]
                command_name="upgrade",
                user_config=user_config,
            )
        except _AdapterResolutionRefused as exc:
            _print_err(str(exc))
            return False, companions
        old_adapter_recorded = pack_state.adapter or "claude-code"  # type: ignore[attr-defined]

        if old_adapter_recorded != new_target_adapter:
            _print_err(
                f"upgrade: pack adapter changed from "
                f"{old_adapter_recorded!r} → {new_target_adapter!r} "
                f"between versions; run uninstall + install instead "
                f"(cross-adapter upgrade is not supported)"
            )
            return False, companions

        try:
            new_owned = _compute_new_wiring_rows(pack_dir, pack_name, new_target_adapter)
            old_owned = list(pack_state.hook_wiring_owned)  # type: ignore[attr-defined]
            _unproject_removed_rows(
                root=root,
                old_owned=old_owned,
                new_owned=new_owned,
                old_adapter=old_adapter_recorded,
            )
            new_rows = _merge_user_scope_hook_wiring(
                pack_dir=pack_dir,
                pack_name=pack_name,
                target_adapter=new_target_adapter,
                install_root=root,
                force_merge=False,
            )
            pack_state.hook_wiring_owned = new_rows  # type: ignore[attr-defined]
            pack_state.adapter = new_target_adapter  # type: ignore[attr-defined]
            _refresh_merge_target_shas(
                pack_state=pack_state,
                owned_rows=new_rows,
                root=root,
            )
        except Exception as exc:
            _print_err(f"upgrade: hook-wiring reconciliation failed: {exc}")
            return False, companions

    # ── Update state ─────────────────────────────────────────────────────────────
    if is_per_primitive:
        ptype, _src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]  # type: ignore[index]
        if ptype not in pack_state.primitive_versions:  # type: ignore[attr-defined]
            pack_state.primitive_versions[ptype] = {}  # type: ignore[attr-defined]
        pack_state.primitive_versions[ptype][prim_name] = to_version  # type: ignore[attr-defined,index]
    else:
        pack_state.installed_version = to_version  # type: ignore[attr-defined]
        if row.canonical_source is not None:
            pack_state.source = row.canonical_source  # type: ignore[attr-defined]

    state_toml_content = dump_state(state)
    state_relpath = state_path.relative_to(root).as_posix()
    state_prefixes = allowed_prefixes
    if effective_scope == "repo" and state_relpath == ".agentbundle-state.toml":
        state_prefixes = None
    try:
        safety.write_jailed(
            root, state_relpath, state_toml_content,
            scope=effective_scope,
            allowed_prefixes=state_prefixes,
        )
    except safety.PathJailError as exc:
        _print_err(f"upgrade: {exc}")
        return False, companions

    return True, companions


# ---------------------------------------------------------------------------
# Bulk-upgrade orchestration helpers
# ---------------------------------------------------------------------------


def _assign_pre_apply_outcomes(rows: "list", *, dry_run: bool) -> None:
    """Set initial ``outcome`` on each row before confirmation."""
    has_unknown = any(r.status == "unknown" for r in rows)
    for row in rows:
        if has_unknown:
            row.outcome = "blocked"
        elif row.status in ("up-to-date", "ahead"):
            row.outcome = "skipped"
        else:
            row.outcome = "planned"


def _apply_order(rows: "list") -> "list":
    """Sort rows by (canonical_source, pack, adapter) ascending."""
    return sorted(rows, key=lambda r: (r.canonical_source or "", r.pack, r.adapter))


def _build_json_doc(
    rows: "list",
    scope: str,
    dry_run: bool,
    source_resolution_map: dict,
) -> dict:
    """Build the JSON output document."""
    sources_seen: dict = {}
    for row in rows:
        cs = row.canonical_source
        if cs is None:
            continue
        if cs not in sources_seen:
            cat_dir, error_code, error_message = source_resolution_map.get(cs, (None, None, None))
            sources_seen[cs] = {
                "source": cs,
                "resolved": cat_dir is not None,
                "error_code": error_code,
                "error_message": error_message,
            }
    sources = sorted(sources_seen.values(), key=lambda s: s["source"])

    rows_out = []
    for row in sorted(rows, key=lambda r: (r.canonical_source or "", r.pack, r.adapter)):
        rows_out.append({
            "pack": row.pack,
            "adapter": row.adapter,
            "scope": row.scope,
            "source": row.canonical_source,
            "installed_version": row.pack_state.installed_version,  # type: ignore[attr-defined]
            "available_version": row.available_version,
            "status": row.status,
            "status_reason": row.status_reason,
            "outcome": row.outcome,
        })

    total = len(rows)
    upgrade_available = sum(1 for r in rows if r.status == "upgrade-available")
    up_to_date = sum(1 for r in rows if r.status == "up-to-date")
    ahead = sum(1 for r in rows if r.status == "ahead")
    unknown = sum(1 for r in rows if r.status == "unknown")
    planned = sum(1 for r in rows if r.outcome == "planned")
    completed = sum(1 for r in rows if r.outcome == "completed")
    skipped = sum(1 for r in rows if r.outcome == "skipped")
    blocked = sum(1 for r in rows if r.outcome == "blocked")
    failed = sum(1 for r in rows if r.outcome == "failed")
    not_attempted = sum(1 for r in rows if r.outcome == "not-attempted")

    return {
        "schema_version": 1,
        "command": "upgrade",
        "mode": "all",
        "scope": scope,
        "dry_run": dry_run,
        "sources": sources,
        "rows": rows_out,
        "summary": {
            "total": total,
            "upgrade_available": upgrade_available,
            "up_to_date": up_to_date,
            "ahead": ahead,
            "unknown": unknown,
            "planned": planned,
            "completed": completed,
            "skipped": skipped,
            "blocked": blocked,
            "failed": failed,
            "not_attempted": not_attempted,
        },
    }


def _print_plan_table(
    rows: "list",
    fmt: str,
    args: "object",
    source_resolution_map: dict,
) -> None:
    """Render the plan.  JSON mode: emit JSON to stdout.  Table mode: print table."""
    scope = getattr(args, "scope", "repo") or "repo"
    dry_run = getattr(args, "dry_run", False)

    if fmt == "json":
        doc = _build_json_doc(rows, scope, dry_run, source_resolution_map)
        print(json.dumps(doc, indent=2))
        return

    if not rows:
        return

    header = (
        f"{'PACK':<20} {'ADAPTER':<16} {'STATUS':<22} {'OUTCOME':<14}"
        f" {'INSTALLED':<12} {'AVAILABLE':<12} SOURCE"
    )
    sep = "-" * len(header)
    print(header)
    print(sep)
    for row in rows:
        source_display = row.canonical_source or "(unknown)"
        max_src = 40
        if len(source_display) > max_src:
            source_display = source_display[:max_src - 3] + "..."
        av = row.available_version or "-"
        inst = row.pack_state.installed_version or "-"  # type: ignore[attr-defined]
        print(
            f"{row.pack:<20} {row.adapter:<16} {row.status:<22} {row.outcome:<14}"
            f" {inst:<12} {av:<12} {source_display}"
        )


def _confirm_or_abort(rows: "list") -> None:
    """Show a confirmation prompt; raise ``SystemExit`` if user declines."""
    try:
        answer = input("Apply these upgrades? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() not in ("y", "yes"):
        print("upgrade: aborted; no changes made", file=sys.stderr)
        raise SystemExit(1)


def _finalize(
    rows_sorted: "list",
    args: "object",
    source_resolution_map: dict,
) -> int:
    """Emit final results table/JSON and return exit code."""
    fmt = getattr(args, "format", "table")
    _print_plan_table(rows_sorted, fmt, args, source_resolution_map)
    candidates = [r for r in rows_sorted if r.status == "upgrade-available"]
    if not candidates:
        return 0
    if all(r.outcome == "completed" for r in candidates):
        return 0
    return 1


def _apply_all(
    rows_sorted: "list",
    state: "object",
    state_path: "Path",
    root: "Path",
    args: "object",
    source_resolution_map: dict,
) -> int:
    """Apply upgrades in order; stop on first failure."""
    candidates = [r for r in rows_sorted if r.status == "upgrade-available"]
    for i, row in enumerate(candidates):
        success, _ = _apply_single_row(row, state, state_path, root, args)
        if success:
            row.outcome = "completed"
        else:
            row.outcome = "failed"
            for remaining in candidates[i + 1:]:
                remaining.outcome = "not-attempted"
            break
    for row in rows_sorted:
        if row.status in ("up-to-date", "ahead"):
            row.outcome = "skipped"
        elif row.status == "unknown":
            row.outcome = "blocked"
    return _finalize(rows_sorted, args, source_resolution_map)


def _run_all(args: "object", root: "Path", *, _rows_out: "list | None" = None) -> int:
    """Main bulk-upgrade dispatcher.  Returns int exit code.

    ``_rows_out``: optional test-only side channel.  If provided, ``_run_all``
    appends the final ``rows_sorted`` list to it before returning.
    """

    def _return(code: int, rows: "list | None" = None) -> int:
        if _rows_out is not None and rows is not None:
            _rows_out.extend(rows)
        return code

    # Gate: --adapter rejected with --all
    if getattr(args, "adapter", None):
        _print_err("--adapter is not compatible with --all")
        return _return(2)

    # Gate: positional catalogue rejected with --all
    if getattr(args, "catalogue", None):
        _print_err("positional <catalogue> is not compatible with --all")
        return _return(2)

    # Gate: --scope required with --all
    if not getattr(args, "scope", None):
        _print_err("--scope repo|user is required with --all")
        return _return(2)

    stdin_is_tty = sys.stdin.isatty()

    # Gate: --format json without --yes (non-dry-run) — AC6
    fmt = getattr(args, "format", "table")
    if (
        fmt == "json"
        and not getattr(args, "yes", False)
        and not getattr(args, "dry_run", False)
    ):
        _print_err("--yes is required for --format json (use --dry-run to preview)")
        return _return(2)

    # User-scope root resolution
    if args.scope == "user":  # type: ignore[attr-defined]
        from agentbundle import scope as scope_mod
        try:
            root = scope_mod.resolve_user_root()
        except scope_mod.UserScopeUnresolvable:
            _print_err("Cannot resolve user home directory; --scope user unavailable")
            return _return(2)

    state_path = resolve_state_path(args.scope, root)  # type: ignore[attr-defined]
    try:
        state = load_state(state_path, for_write=True)
    except ConfigError as exc:
        _print_err(f"upgrade: {exc}")
        return _return(1)

    source_resolution_map: dict = {}

    if not state.packs:
        if fmt == "json":
            _print_plan_table([], fmt, args, source_resolution_map)
        else:
            print(f"Nothing installed at {args.scope} scope.")  # type: ignore[attr-defined]
        return _return(0, [])

    user_config = getattr(args, "_user_config", None)
    rows, source_resolution_map = _run_preflight(state, args.scope, root, user_config)  # type: ignore[attr-defined]

    rows_sorted = sorted(rows, key=lambda r: (r.canonical_source or "", r.pack, r.adapter))
    _assign_pre_apply_outcomes(rows_sorted, dry_run=getattr(args, "dry_run", False))

    blocked = [r for r in rows_sorted if r.status == "unknown"]
    candidates = [r for r in rows_sorted if r.status == "upgrade-available"]

    if getattr(args, "dry_run", False):
        _print_plan_table(rows_sorted, fmt, args, source_resolution_map)
        return _return(1 if blocked else 0, rows_sorted)

    if blocked:
        _print_plan_table(rows_sorted, fmt, args, source_resolution_map)
        return _return(1, rows_sorted)

    if not candidates:
        if fmt == "json":
            _print_plan_table(rows_sorted, fmt, args, source_resolution_map)
        else:
            print("Nothing to upgrade.")
        return _return(0, rows_sorted)

    # Table mode only: show pre-apply plan and prompt
    if fmt == "table":
        _print_plan_table(rows_sorted, "table", args, source_resolution_map)
        if not getattr(args, "yes", False) and stdin_is_tty:
            _confirm_or_abort(rows_sorted)

    rc = _apply_all(rows_sorted, state, state_path, root, args, source_resolution_map)
    return _return(rc, rows_sorted)


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle upgrade``.

    Args:
        args.pack        — pack name (required).
        args.catalogue   — catalogue URI (local path or git+https://...).
        args.skill       — primitive name for a skill-only upgrade (optional).
        args.agent       — primitive name for an agent-only upgrade (optional).
        args.hook        — primitive name for a hook-only upgrade (optional).
        args.seed        — primitive name for a seed-only upgrade (optional).
        args.command     — primitive name for a command-only upgrade (optional).
        args.yes         — skip the confirmation prompt (optional, default off).
        args.root        — repo root (default ``'.'``).

    The upgrade target version is derived from the resolved catalogue's
    ``pack.toml`` ``[pack] version``; there is no operator-supplied ``--to``.

    Returns 0 on success, non-zero on any failure.
    """
    # --format json with --pack is not yet supported (AC5)
    if getattr(args, "format", "table") == "json" and not getattr(args, "all", False):
        _print_err(
            "upgrade: --format json is not yet supported with --pack; "
            "use --format table or use --all"
        )
        return 1

    # Dispatch to bulk mode
    if getattr(args, "all", False):
        root = Path(args.root).resolve()
        return _run_all(args, root)

    pack_name: str = args.pack
    # RFC-0046: resolve the default source when the `catalogue` positional was
    # omitted (an explicit arg short-circuits through layer 1 unchanged). On the
    # install→upgrade hand-off the synthetic namespace already carries the
    # concrete resolved URI, so layer 1 returns it verbatim — no re-resolution.
    try:
        catalogue_uri: str = resolve_catalogue_uri(args)
    except CatalogueError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1
    cli_scope: str | None = getattr(args, "scope", None)
    cli_adapter: str | None = getattr(args, "adapter", None)
    # User-config attached by `cli.py:main()` via args._user_config.
    # The pre-flight in `_resolve_target_adapter` no-ops when
    # `state_adapter` is set (upgrades preserve their existing-install
    # adapter), so on a normal upgrade this is read but unused. We
    # still thread it so the AC15(c) AST check is satisfied and so the
    # state-pin-mismatch fall-through path stays well-defined.
    user_config: "UserConfig | None" = getattr(args, "_user_config", None)
    root = Path(args.root).resolve()

    # ── Multi-scope disambiguator (RFC-0004) ──────────────────────────────────
    # If the pack is at both scopes, --scope is required; at one scope, infer.
    from agentbundle import scope as scope_mod

    repo_state_path = resolve_state_path("repo", root)
    # A legacy (non-v0.4) state file is refused on read too (RFC-0052);
    # surface it as a clean refuse rather than a traceback.
    try:
        repo_state_for_check = load_state(repo_state_path)
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1
    installed_at_repo = repo_state_for_check.has_pack(pack_name)
    user_state_path = None
    installed_at_user = False
    user_state_for_check = None
    try:
        user_root_resolved = scope_mod.resolve_user_root()
        user_state_path = resolve_state_path("user", user_root_resolved)
        user_state_for_check = load_state(user_state_path)
        installed_at_user = user_state_for_check.has_pack(pack_name)
    except scope_mod.UserScopeUnresolvable:
        pass
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    if installed_at_repo and installed_at_user and cli_scope is None:
        print(
            f"upgrade: {pack_name} installed at multiple scopes; "
            "pass --scope {repo, user}",
            file=sys.stderr,
        )
        return 1

    # Effective scope is "user" only when the CLI explicitly asked or
    # the pack is installed at user only. At user scope, `root` is the
    # user's home and the state file is `<root>/.agentbundle/state.toml`.
    effective_scope = "repo"
    allowed_prefixes: list[str] | None = None
    if cli_scope == "user" or (cli_scope is None and installed_at_user and not installed_at_repo):
        if user_state_path is None:
            print(
                "upgrade: cannot resolve user scope: $HOME unset or invalid",
                file=sys.stderr,
            )
            return 1
        root = user_state_path.parent.parent
        effective_scope = "user"

    # Multi-adapter disambiguator (RFC-0052): a pack can carry multiple
    # adapter rows at one scope; upgrade targets exactly one. Infer when a
    # single row exists; require --adapter when more than one.
    effective_check = (
        user_state_for_check if effective_scope == "user" else repo_state_for_check
    )
    _rows = effective_check.rows_for_pack(pack_name) if effective_check else {}
    if cli_adapter is not None:
        if cli_adapter not in _rows:
            print(
                f"upgrade: {pack_name} is not installed for adapter "
                f"{cli_adapter!r} at {effective_scope} scope "
                f"(installed for: {', '.join(sorted(_rows)) or 'none'})",
                file=sys.stderr,
            )
            return 1
        target_adapter = cli_adapter
    elif len(_rows) == 1:
        target_adapter = next(iter(_rows))
    elif len(_rows) > 1:
        from agentbundle.commands._common import format_adapter_versions

        print(
            f"upgrade: {pack_name} installed for multiple adapters at "
            f"{effective_scope} scope; pass --adapter to pick one: "
            f"{format_adapter_versions(_rows)}",
            file=sys.stderr,
        )
        return 1
    else:
        # No row at the effective scope; downstream "not installed" handles it.
        target_adapter = cli_adapter or "claude-code"

    if effective_scope == "user":
        from agentbundle.commands.install import _adapter_allowed_prefixes_user

        # Use the targeted row's adapter so Kiro-installed packs get .kiro/
        # prefixes, not Claude Code's .claude/ prefixes.
        allowed_prefixes = _adapter_allowed_prefixes_user(target_adapter or "claude-code")

    # ── Detect per-primitive flag ─────────────────────────────────────────────
    prim_flag: str | None = None
    prim_name: str | None = None
    for flag_attr, (ptype, _src_dir) in _PRIMITIVE_FLAG_MAP.items():
        val = getattr(args, flag_attr, None)
        if val:
            prim_flag = flag_attr
            prim_name = val
            break

    is_per_primitive = prim_flag is not None

    # ── Resolve catalogue ─────────────────────────────────────────────────────
    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    # ── Locate pack dir ───────────────────────────────────────────────────────
    pack_dir = _locate_pack(catalogue_dir, pack_name)
    if pack_dir is None:
        print(
            f"upgrade: pack {pack_name!r} not found in catalogue at {catalogue_dir}; "
            "expected packs/<pack>/ or <catalogue>/<pack>/",
            file=sys.stderr,
        )
        return 1

    # ── Spec-version gate ─────────────────────────────────────────────────────
    try:
        pack_toml = load_pack_toml(pack_dir / "pack.toml")
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    gate = check_spec_version_gate(pack_toml)
    if gate is not None:
        return gate

    # ── Load current state ────────────────────────────────────────────────────
    # upgrade is a write — refuse-and-explain on a v0.1 file (RFC-0004).
    # At user scope, the state file lives at `<root>/.agentbundle/state.toml`,
    # not the repo-style `<root>/.agentbundle-state.toml`.
    if effective_scope == "user":
        state_path = user_state_path  # already resolved above
    else:
        state_path = resolve_state_path("repo", root)
    try:
        state = load_state(state_path, for_write=True)
    except ConfigError as exc:
        print(f"upgrade: {exc}", file=sys.stderr)
        return 1

    if not state.has_pack(pack_name):
        print(f"upgrade: pack {pack_name!r} not installed", file=sys.stderr)
        return 1

    pack_state = state.row(pack_name, target_adapter)
    if pack_state is None:
        print(
            f"upgrade: {pack_name} is not installed for adapter "
            f"{target_adapter!r} at {effective_scope} scope",
            file=sys.stderr,
        )
        return 1

    # ── Mixed-version warning (whole-pack only) ────────────────────────────────
    if not is_per_primitive and pack_state.primitive_versions:
        mixed_parts: list[str] = []
        for ptype, pv_map in sorted(pack_state.primitive_versions.items()):
            for pname, ver in sorted(pv_map.items()):
                mixed_parts.append(f"{ptype}/{pname}@{ver}")
        print(
            f"warning: pack {pack_name!r} has mixed-version primitives: "
            f"{mixed_parts}; proceeding with whole-pack upgrade",
            file=sys.stderr,
        )

    # ── Derive target version; confirm before writing ─────────────────────────
    # The upgrade target is a property of the catalogue, not an operator
    # assertion: the resolved snapshot's pack.toml declares it under
    # ``[pack] version``. There is no version-history store (the catalogue is a
    # single git snapshot), so there is nothing to select and no ``--to`` to
    # validate. Guarded access — a pack.toml with no (or a non-string)
    # ``[pack] version`` cannot name an upgrade target, and the spec-version
    # gate above reads only ``[pack.adapter-contract] version``, so this is a
    # distinct check.
    _pack_table = pack_toml.get("pack", {})
    to_version = _pack_table.get("version") if isinstance(_pack_table, dict) else None
    if not isinstance(to_version, str) or not to_version:
        print(
            f"upgrade: pack {pack_name!r} in catalogue declares no [pack] "
            f"version; cannot determine upgrade target",
            file=sys.stderr,
        )
        return 1

    # The version we are moving *from*, captured before any state mutation.
    # Per-primitive uses the recorded primitive override when present, else the
    # whole-pack installed version.
    if is_per_primitive:
        _from_ptype = _PRIMITIVE_FLAG_MAP[prim_flag][0]
        from_version = (
            pack_state.primitive_versions.get(_from_ptype, {}).get(prim_name)
            or pack_state.installed_version
        )
        confirm_label = f"{pack_name} {_from_ptype}/{prim_name}"
    else:
        from_version = pack_state.installed_version
        confirm_label = pack_name

    # When the installed version already equals the catalogue's, this is a
    # re-apply (repairs local drift), not a version change — say so either way,
    # and word the prompt accordingly.
    already_current = from_version == to_version

    # Note: for a per-primitive upgrade the prompt fires before the
    # primitive-existence check (below, after render), so confirming
    # `--skill <typo>` is followed by a "not in pack" refusal. Harmless (no
    # write happens either way) and rare; left as-is to keep the confirm above
    # the expensive render.

    # Upfront drift notice (whole-pack only): before the user confirms, tell
    # them how many installed files have local edits that re-applying will
    # preserve as `*.upstream` companions. Computed from on-disk-vs-state SHAs
    # (no render needed); suppressed at zero and on a dry run (which writes
    # nothing and already names companion actions in its plan). Gated to the
    # whole-pack case: a per-primitive upgrade re-applies only that primitive's
    # files, so a whole-pack count would mislead.
    if not is_per_primitive and not getattr(args, "dry_run", False):
        from agentbundle.commands._common import count_drifted_files

        _drifted = count_drifted_files(pack_state, root)
        if _drifted:
            print(
                f"upgrade: {_drifted} installed file(s) have local edits; your "
                f"edits are preserved as .upstream companions where the file "
                f"still ships.",
                file=sys.stderr,
            )

    # Confirm before the first write — unless ``--yes`` or ``--dry-run`` (which
    # writes nothing). A non-interactive stdin cannot answer the prompt, so
    # refuse and explain rather than block on ``input()``. ``--dry-run``
    # short-circuits the refusal: a dry run never writes, so it is safe
    # non-interactively without ``--yes``.
    if not getattr(args, "yes", False) and not getattr(args, "dry_run", False):
        if already_current:
            question = (
                f"{confirm_label} is already at {to_version} at "
                f"{effective_scope} scope. Re-apply to restore any missing or "
                f"reset any unmodified bundle files? Your local edits are kept "
                f"as .upstream companions. [y/N] "
            )
        else:
            question = (
                f"Upgrade {confirm_label} at {effective_scope} scope from "
                f"{from_version} to {to_version}? [y/N] "
            )
        if not confirm_or_refuse(
            yes=False,
            question=question,
            refuse_message=(
                f"upgrade: refusing to upgrade {confirm_label} from "
                f"{from_version} to {to_version} without confirmation; pass "
                f"--yes to upgrade non-interactively"
            ),
            abort_message="upgrade: aborted; no changes made",
        ):
            return 1
    elif already_current:
        # --yes / --dry-run skipped the prompt, but still state the situation.
        # A dry run previews only, so don't claim a re-apply it won't perform.
        suffix = "" if getattr(args, "dry_run", False) else "; re-applying"
        print(
            f"upgrade: {confirm_label} is already at {to_version}{suffix}",
            file=sys.stderr,
        )

    # ── Render new projection in memory ──────────────────────────────────────
    # At user scope, render via the Claude Code adapter directly (paths
    # under `.claude/...`) — the dist-tree shape `render_pack` produces
    # (`apm/...`, `claude-plugins/...`) would fail the user-scope
    # `allowed-prefixes` jail and wouldn't match the user-scope-installed
    # state's `.claude/...` paths. Mirrors `install._render_for_user_scope`.
    # RFC-0011: thread the pack's allowed-adapters, contract version,
    # and recorded state.adapter through the resolver so v0.6+ packs
    # use the six-step (0–5) lookup (and existing adopters get the
    # state-hint short-circuit AC10b on upgrade, avoiding the
    # cross-adapter refusal when they've populated a second CLI home).
    _pack_install_table = pack_toml.get("pack", {}).get("install")
    _pack_allowed_adapters = None
    if isinstance(_pack_install_table, dict):
        _raw_aa = _pack_install_table.get("allowed-adapters")
        if isinstance(_raw_aa, list):
            _pack_allowed_adapters = [s for s in _raw_aa if isinstance(s, str)]
    _pack_contract_version = (
        pack_toml.get("pack", {}).get("adapter-contract", {}).get("version")
        if isinstance(pack_toml.get("pack", {}).get("adapter-contract"), dict)
        else None
    )
    try:
        if effective_scope == "user":
            from agentbundle.commands.install import (
                _AdapterResolutionRefused,
                _render_for_user_scope,
                _resolve_target_adapter,
                _rewrite_user_scope_hook_paths,
            )

            try:
                projection = _render_for_user_scope(
                    pack_dir,
                    adapter=None,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=pack_state.adapter,
                    command_name="upgrade",
                    user_config=user_config,
                )
            except _AdapterResolutionRefused as exc:
                print(str(exc), file=sys.stderr)
                return 1
            # Mirror install: rewrite v0.2 hook-body paths to the v0.3
            # user-scope shape (`.claude/hooks/<pack>/` or
            # `.kiro/hooks/<pack>/`) and drop the v0.2 settings.local.json
            # target. Without this, the path-jail probe refuses
            # `tools/hooks/<name>.sh` at user scope.
            try:
                _new_target_adapter = _resolve_target_adapter(
                    pack_dir,
                    scope="user",
                    adapter=None,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=pack_state.adapter,
                    command_name="upgrade",
                    user_config=user_config,
                )
            except _AdapterResolutionRefused as exc:
                print(str(exc), file=sys.stderr)
                return 1
            projection = _rewrite_user_scope_hook_paths(
                projection,
                pack_name=pack_name,
                target_adapter=_new_target_adapter,
            )
        else:
            # Repo-scope render. RFC-0012 lifted the install default at
            # this scope from the dist-tree producer to a per-IDE
            # projection (`.claude/...`, `.kiro/...`, ...). Upgrade
            # must mirror that shape, else the rendered keys won't
            # overlap the install-time state.files keys and a whole-
            # pack upgrade silently accretes a parallel dist-tree
            # subtree into state.files (and onto disk via
            # safety.write_jailed below).
            #
            # Backward compat for the `--emit-install-routes` install
            # path (RFC-0012 § *CLI surface*): if existing state.files
            # already carries dist-tree-shaped paths, this was a
            # catalogue-publishing install — keep rendering the legacy
            # shape so we don't accrete a parallel per-IDE subtree on
            # top.
            if _was_dist_tree_install(pack_state):
                from agentbundle.render import render_pack  # lazy: preserves mock.patch contract
                projection = render_pack(pack_dir)
            else:
                from agentbundle.commands.install import (
                    _AdapterResolutionRefused,
                    _adapter_allowed_prefixes_repo,
                    _render_for_repo_scope,
                )

                try:
                    _resolved_adapter, projection = _render_for_repo_scope(
                        pack_dir,
                        adapter=None,
                        allowed_adapters=_pack_allowed_adapters,
                        contract_version=_pack_contract_version,
                        state_adapter=pack_state.adapter,
                        command_name="upgrade",
                        user_config=user_config,
                    )
                except _AdapterResolutionRefused as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                allowed_prefixes = _adapter_allowed_prefixes_repo(
                    _resolved_adapter
                )
    except (FileNotFoundError, ValueError) as exc:
        print(f"upgrade: render failed for pack {pack_name!r}: {exc}", file=sys.stderr)
        return 1

    # ── Per-primitive: validate and filter ────────────────────────────────────
    if is_per_primitive:
        ptype, src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]
        filtered = _filter_for_primitive(projection, prim_name, src_dir)
        # --hook is atomic over hook-body + matching hook-wiring of the
        # same name (per spec AC #10 — wiring co-moves with body so a
        # per-hook upgrade can never land a torn pair).
        if prim_flag == "hook":
            filtered.update(
                _filter_for_primitive(projection, prim_name, "hook-wiring")
            )
        if not filtered:
            print(
                f"primitive {prim_name!r} not in pack {pack_name}",
                file=sys.stderr,
            )
            return 1
        work_projection = filtered
    else:
        work_projection = projection

    # ── Dry-run: preview the plan and stop before any write ───────────────────
    # Inserted after `work_projection` is built so it covers both the whole-pack
    # and the per-primitive (`--skill <name>`, …) shapes — and after every
    # pre-flight refusal above (catalogue resolve, version gate, adapter
    # resolution, render, pack-not-installed, primitive-not-found) has already
    # passed through with the real run's exit code. Classify each file with the
    # SAME `safety.classify` the write loop below uses — mirroring its
    # Tier-3→Tier-1 coercion for new paths — print the per-file plan to stdout,
    # and return before the walk: no companion, no state write, no hook-wiring
    # reconciliation, no `upgraded:` recap.
    if getattr(args, "dry_run", False):
        # Path-jail pre-flight (AC5). Unlike install (which probes every file in
        # its standalone Step 8 before any write), upgrade enforces the jail
        # *inside* its write loop via `write_jailed`, so a real upgrade over a
        # projection that escapes the root would fail non-zero there. Mirror
        # install's Step 8 probe here — read-only — so the dry-run surfaces the
        # same refusal before printing any plan, rather than reporting a clean
        # preview the real run would reject. Deliberately a separate pass before
        # the print loop (probe-all-then-print): a jail violation on a late file
        # aborts with a clean stderr refusal instead of a partial plan already
        # on stdout.
        try:
            safety.assert_projection_jailed(
                root, sorted(work_projection), allowed_prefixes, command="upgrade"
            )
        except safety.PathJailError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        actions: list[str] = []
        for relpath in sorted(work_projection):
            tier = safety.classify(relpath, root, state)
            if tier is safety.Tier.TIER_3:
                tier = safety.Tier.TIER_1
            action = plan_action(tier, on_disk=(root / relpath).exists())
            companion = (
                safety.companion_path(Path(relpath)).as_posix()
                if tier is safety.Tier.TIER_2
                else None
            )
            print(format_plan_line(action, tier.value, relpath, companion))
            actions.append(action)
        print(summarize_plan(actions))
        return 0

    # ── Apply via shared helper ───────────────────────────────────────────────
    # Create a _BulkRow for the single-pack path and delegate to the shared
    # _apply_single_row helper. canonical_source substitutes for the old
    # `canonicalize_source(catalogue_uri)` in the state update.
    _single_row = _BulkRow(
        pack=pack_name,
        adapter=target_adapter,
        scope=effective_scope,
        pack_state=pack_state,
        canonical_source=canonicalize_source(catalogue_uri),
        pack_dir=pack_dir,
        pack_toml=pack_toml,
        available_version=to_version,
        _projection=work_projection,
        allowed_prefixes=allowed_prefixes,
    )
    _success, companions = _apply_single_row(_single_row, state, state_path, root, args)
    if not _success:
        return 1

    # ── Surface Tier-2 companion-drops ────────────────────────────────────────
    # Printed here, after every `return 1` gate above (companion writes, hook-
    # wiring reconciliation, state write) has passed, so an announced companion
    # always implies a committed upgrade — never "kept your edits" followed by an
    # abort. The companion itself was written eagerly during the walk; this only
    # reports it. stderr (not stdout) so the `upgraded:` recap rail stays parseable.
    if companions:
        print(
            f"upgrade: {len(companions)} file(s) were modified since install and "
            f"kept as *.upstream.<ext> companions (your edits preserved):",
            file=sys.stderr,
        )
        for comp in companions:
            print(f"  {comp}", file=sys.stderr)

    if is_per_primitive:
        ptype, _src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]
        recap_label = f"{pack_name} {ptype}/{prim_name}"
    else:
        recap_label = pack_name
    print(
        _format_recap(
            recap_label,
            effective_scope,
            from_version,
            to_version,
            already_current=already_current,
            companion_count=len(companions),
        )
    )
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_recap(
    label: str,
    scope: str,
    from_version: str,
    to_version: str,
    *,
    already_current: bool,
    companion_count: int,
) -> str:
    """Render the post-upgrade recap line, honestly distinguishing the cases.

    Three verdicts, driven by the only signals available without changing what
    the walk writes (the walk re-writes bundle-owned files unconditionally, so
    "nothing changed on disk" is not knowable):

      - version changed → ``upgraded: <label> @ <scope> <from> -> <to>``
      - same version, no local edits preserved →
        ``re-applied: <label> @ <scope> <version> (already current)``
      - same version, local edits preserved as companions →
        ``re-applied: <label> @ <scope> <version> — N file(s) had local edits,
        kept as .upstream companions``

    It never prints ``upgraded: … X -> X`` for a same-version re-apply.
    """
    if not already_current:
        return f"upgraded: {label} @ {scope} {from_version} -> {to_version}"
    if companion_count:
        return (
            f"re-applied: {label} @ {scope} {to_version} — "
            f"{companion_count} file(s) had local edits, kept as .upstream companions"
        )
    return f"re-applied: {label} @ {scope} {to_version} (already current)"


def _compute_new_wiring_rows(
    pack_dir: Path,
    pack_name: str,
    target_adapter: str,
) -> list[dict[str, str]]:
    """Parse the new pack's `.apm/hook-wiring/*.toml` files and
    compute the ``hook-wiring-owned`` rows the upgraded state would
    carry — without writing anything yet. The actual writes come from
    `_unproject_removed_rows` (removes rows present in old, absent
    from new) followed by an idempotent re-call to
    `_merge_user_scope_hook_wiring` (lays down the new row set).

    The id synthesis matches T5/T6's: `<pack-name>:<basename>` per
    wiring TOML. Claude Code rows omit `target-file` (defaulted to
    `~/.claude/settings.json`); Kiro rows carry it explicitly with
    `.kiro/agents/<attach-to-agent>.json`.
    """
    import re
    import tomllib
    from agentbundle.build.projections.hook_id import synthesize_id

    # Same grammar `install._merge_user_scope_hook_wiring` enforces.
    # Validating here ensures a malformed `attach-to-agent` cannot
    # corrupt the symmetric-diff computation (e.g. a path-traversal
    # payload producing a phantom "removal" that we'd then unproject
    # against the old target file).
    _AGENT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

    from agentbundle.commands.install import _canonical_install_adapter

    wiring_dir = pack_dir / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return []
    if _canonical_install_adapter(target_adapter) == "kiro-ide":
        # `kiro` (deprecated alias) and `kiro-ide` DROP hook-wiring
        # (RFC-0022): the install-time merge returns no rows, so the
        # symmetric-diff computation must agree and yield none.
        return []
    rows: list[dict[str, str]] = []
    for entry in sorted(wiring_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".toml"):
            continue
        # Don't silently swallow TOMLDecodeError — the merger raises
        # on the same file, so the asymmetry would let step A unproject
        # entries the merger will then refuse to re-project. Propagate.
        try:
            body = tomllib.loads(entry.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise RuntimeError(
                f"upgrade: pack {pack_name}'s hook-wiring {entry.stem}.toml "
                f"failed to parse: {exc}"
            ) from exc
        entry_id = synthesize_id(pack_name, entry.stem)
        hooks_in_wiring = body.get("hooks", {}) if isinstance(body, dict) else {}
        if not isinstance(hooks_in_wiring, dict):
            continue
        attach = body.get("attach-to-agent") if isinstance(body, dict) else None
        # Grammar guard for Kiro: refuse anything that would corrupt
        # `target_file_rel` (path-traversal, special chars, …).
        if target_adapter == "kiro-cli" and isinstance(attach, str):
            if not _AGENT_NAME_RE.fullmatch(attach):
                raise RuntimeError(
                    f"upgrade: pack {pack_name}'s hook-wiring {entry.stem}.toml "
                    f"declares attach-to-agent={attach!r} which violates the "
                    f"agent-name grammar ^[a-z0-9][a-z0-9-]*$ — refusing"
                )
        for event, incoming in hooks_in_wiring.items():
            if not isinstance(incoming, list):
                continue
            row: dict[str, str] = {"event": event, "id": entry_id}
            if target_adapter == "kiro-cli" and isinstance(attach, str):
                row["target-file"] = f".kiro/agents/{attach}.json"
            rows.append(row)
    return rows


def _unproject_removed_rows(
    *,
    root: Path,
    old_owned: list[dict[str, str]],
    new_owned: list[dict[str, str]],
    old_adapter: str,
) -> None:
    """Unproject rows present in *old_owned* but absent from *new_owned*.

    A row's "presence" is the (event, id, target-file) triple — so an
    ``attach-to-agent`` rename (Kiro: same id, same event, different
    target-file) counts as a removal at the OLD target-file. The
    install-time merge step (caller's Step B) will subsequently
    project the same row at the NEW target-file.

    Walks the OLD adapter for dispatch (Claude Code vs Kiro). Claude
    Code rows default ``target-file`` to ``.claude/settings.json`` per
    RFC-0005 § State-file impact.
    """
    def _key(row: dict[str, str]) -> tuple[str, str, str]:
        return (row.get("event", ""), row.get("id", ""), row.get("target-file", ""))

    new_keys = {_key(r) for r in new_owned}
    removed = [r for r in old_owned if _key(r) not in new_keys]

    removed_by_target: dict[str, list[tuple[str, str]]] = {}
    for r in removed:
        target = r.get("target-file") or (
            ".claude/settings.json" if old_adapter == "claude-code" else ""
        )
        if not target:
            continue
        removed_by_target.setdefault(target, []).append((r["event"], r["id"]))

    for target_rel, pairs in removed_by_target.items():
        target_path = root / target_rel.lstrip("/")
        # The merge family (`kiro-cli`, plus the legacy `kiro` block that
        # pre-migration state may still record) merges into a pack-owned
        # agent JSON; everything else (claude-code) merges into a shared
        # settings file.
        if old_adapter in ("kiro", "kiro-cli"):
            from agentbundle.build.projections.merge_into_agent_json import unproject
        else:
            from agentbundle.build.projections.user_merge_json import unproject
        unproject(target_path, pairs)


def _locate_pack(catalogue_dir: Path, pack_name: str) -> Path | None:
    """Find the pack directory inside the resolved catalogue.

    Tries two layouts:
      1. ``<catalogue_dir>/packs/<pack_name>/`` — standard catalogue layout.
      2. ``<catalogue_dir>/<pack_name>/``         — catalogue is a pack root.
    """
    candidate_a = catalogue_dir / "packs" / pack_name
    if candidate_a.is_dir() and (candidate_a / "pack.toml").exists():
        return candidate_a
    candidate_b = catalogue_dir / pack_name
    if candidate_b.is_dir() and (candidate_b / "pack.toml").exists():
        return candidate_b
    return None


def _filter_for_primitive(
    projection: dict[str, bytes],
    prim_name: str,
    src_dir: str,
) -> dict[str, bytes]:
    """Return the subset of ``projection`` that belongs to the named primitive.

    Heuristic (v1):
      A projected relpath is considered part of primitive ``prim_name`` of
      source-dir type ``src_dir`` when the relpath contains a path segment
      that starts with ``/<src_dir>/<prim_name>/`` (directory primitive) or
      ``/<src_dir>/<prim_name>.`` (single-file primitive).

    For example, skill ``work-loop`` under source dir ``skills`` matches:
      - ``apm/core/.apm/skills/work-loop/SKILL.md``
      - ``claude-plugins/core/.claude/skills/work-loop/SKILL.md``

    Hook ``pre-commit`` under source dir ``hooks`` matches:
      - ``apm/core/.apm/hooks/pre-commit.sh``
      - ``apm/core/.apm/hooks/pre-commit.py``
      - ``claude-plugins/core/tools/hooks/pre-commit.sh``

    This heuristic intersects naturally with the adapter projection because
    every adapter mirrors the source-dir tree structure from the pack root.
    The heuristic is documented here rather than in a more general schema so
    that a future pack.toml ``source-path`` field can replace it without
    touching test or command logic — just update this function.

    Disambiguation: if a pack contains both `<src_dir>/<name>/...` (dir
    primitive) and `<src_dir>/<name>.<ext>` (single-file primitive), the
    primitive name is ambiguous and the function raises `ValueError`.
    F-build's `validate_pack_uniqueness` already rejects this shape at
    build time; this check is defence-in-depth at the upgrade boundary.

    Name terminators (`/` for dir, `.` for file) prevent prefix bleed:
    `skills/work-loop/` is never matched by `skills/work/`.
    """
    dir_segment = f"/{src_dir}/{prim_name}/"
    file_segment = f"/{src_dir}/{prim_name}."

    via_dir: dict[str, bytes] = {}
    via_file: dict[str, bytes] = {}
    for relpath, content in projection.items():
        norm = relpath if relpath.startswith("/") else "/" + relpath
        if dir_segment in norm:
            via_dir[relpath] = content
        elif file_segment in norm:
            via_file[relpath] = content

    if via_dir and via_file:
        raise ValueError(
            f"primitive {prim_name!r} is ambiguous in source dir {src_dir!r}: "
            f"matches both a directory and a single-file form"
        )
    return {**via_dir, **via_file}
