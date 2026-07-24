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

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.user_config import UserConfig


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
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import (
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
    )
    from agentbundle.render import render_pack
    from agentbundle import safety

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
            _was_dist_tree_install = any(
                rp.startswith(("apm/", "claude-plugins/"))
                or rp == "marketplace.json"
                for rp in pack_state.files
            )
            if _was_dist_tree_install:
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

    # ── Path-jail pre-flight (AC4) — probe all before any write ──────────────
    # Mirror the dry-run probe: refuse if any projected path escapes root or
    # violates allowed_prefixes, before touching disk. Without this gate a
    # prefix violation surfaces mid-loop via write_jailed, after earlier files
    # have already been written — the probe-all-before-write contract means a
    # violation is always a clean abort.
    try:
        safety.assert_projection_jailed(
            root, sorted(work_projection), allowed_prefixes, command="upgrade"
        )
    except safety.PathJailError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # ── Walk projection; apply Tier contract ──────────────────────────────────
    # Collect `.upstream.<ext>` companions dropped this run so we can surface
    # them after the walk. Without this notice the upgrade is silent on a
    # Tier-2 collision — the adopter never learns their edit was kept (and the
    # upstream parked in a companion) or where to find it. Parity with
    # install's seed-companion notice (install.py:891-904), extended to name
    # the path since upgrade has no install-state marker to record it in.
    companions: list[str] = []
    for relpath, content in sorted(work_projection.items()):
        tier = safety.classify(relpath, root, state)

        if tier is safety.Tier.TIER_3:
            # Path is in the new pack but not yet in state (first upgrade to a
            # newly-added file). Treat as Tier-1 — the upgrade contract is the
            # same as install for new paths.
            tier = safety.Tier.TIER_1

        if tier is safety.Tier.TIER_2:
            try:
                safety.write_companion(root, relpath, content)
            except safety.PathJailError as exc:
                print(f"upgrade: {exc}", file=sys.stderr)
                return 1
            companions.append(safety.companion_path(Path(relpath)).as_posix())
            pack_state.files[relpath] = {
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
                print(f"upgrade: {exc}", file=sys.stderr)
                return 1
            pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": to_version,
            }

    # ── Hook-wiring reconciliation (RFC-0005 T8c, user-scope only) ───────────
    # Compute the symmetric difference between old state's
    # ``hook_wiring_owned`` and the new pack's wiring TOMLs. The
    # ``attach-to-agent`` rename case (Kiro) lands here: rows whose
    # target-file changes between versions get dropped from the OLD
    # target file and added to the NEW one. In-place upgrades
    # (identical wiring) are a no-op; adds and removes shift state
    # rows accordingly.
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
                state_adapter=pack_state.adapter,
                command_name="upgrade",
                user_config=user_config,
            )
        except _AdapterResolutionRefused as exc:
            print(str(exc), file=sys.stderr)
            return 1
        old_adapter_recorded = pack_state.adapter or "claude-code"

        # Concern #3: cross-adapter upgrades are out of scope. AC19b
        # covers attach-to-agent renames *within Kiro*, not Kiro→CC
        # or CC→Kiro. Refuse with a refuse-and-explain shape; the
        # operator uninstalls + reinstalls instead.
        if old_adapter_recorded != new_target_adapter:
            print(
                f"upgrade: pack adapter changed from "
                f"{old_adapter_recorded!r} → {new_target_adapter!r} "
                f"between versions; run uninstall + install instead "
                f"(cross-adapter upgrade is not supported)",
                file=sys.stderr,
            )
            return 1

        try:
            new_owned = _compute_new_wiring_rows(pack_dir, pack_name, new_target_adapter)
            old_owned = list(pack_state.hook_wiring_owned)
            # Step A: unproject rows in old that aren't in new.
            _unproject_removed_rows(
                root=root,
                old_owned=old_owned,
                new_owned=new_owned,
                old_adapter=old_adapter_recorded,
            )
            # Step B: project the new pack's wiring against new targets.
            # The merger is idempotent for unchanged rows (replace-in-
            # place by id); for added rows it appends.
            new_rows = _merge_user_scope_hook_wiring(
                pack_dir=pack_dir,
                pack_name=pack_name,
                target_adapter=new_target_adapter,
                install_root=root,
                force_merge=False,
            )
            pack_state.hook_wiring_owned = new_rows
            # Record the resolved adapter faithfully (mirrors install's
            # `new_pack_state.adapter = user_target_adapter`). The old
            # `kiro`-or-`claude-code` collapse mis-recorded `kiro-cli`
            # (the merging adapter) as `claude-code`, which then routed
            # uninstall's unproject to the wrong engine and orphaned the
            # agent JSON.
            pack_state.adapter = new_target_adapter
            # Blocker #1: refresh state.files SHA for the agent JSON the
            # merge phase rewrote. Without this, post-upgrade uninstall
            # would misclassify it as Tier-2 and refuse to remove it.
            _refresh_merge_target_shas(
                pack_state=pack_state,
                owned_rows=new_rows,
                root=root,
            )
        except Exception as exc:
            print(f"upgrade: hook-wiring reconciliation failed: {exc}", file=sys.stderr)
            return 1

    # ── Update state ──────────────────────────────────────────────────────────
    if is_per_primitive:
        # Record per-primitive version override; leave installed_version alone.
        ptype, _src_dir = _PRIMITIVE_FLAG_MAP[prim_flag]
        if ptype not in pack_state.primitive_versions:
            pack_state.primitive_versions[ptype] = {}
        pack_state.primitive_versions[ptype][prim_name] = to_version
    else:
        pack_state.installed_version = to_version
        canonical = canonicalize_source(catalogue_uri)
        if canonical is not None:
            pack_state.source = canonical

    state_toml_content = dump_state(state)
    state_relpath = state_path.relative_to(root).as_posix()
    # Mirror install.py:858-861 — the repo-scope state file lives at
    # `<root>/.agentbundle-state.toml`, a top-level path that won't
    # match the per-IDE `allowed-prefixes.repo` list. Skip the prefix
    # check for that one file so the state write isn't blocked.
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
        print(f"upgrade: {exc}", file=sys.stderr)
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
