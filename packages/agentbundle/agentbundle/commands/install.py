"""``agentbundle install`` — constrained-network pack installer.

Per RFC-0004 the install verb is the load-bearing CLI surface for the
scope dimension. The handler enforces:

  - **Scope resolution** via :mod:`agentbundle.scope` (CLI flag > pack
    ``default-scope`` > built-in ``"repo"``).
  - **Cross-scope conflict** with ``--force`` semantics:
      - Pack already at the *requested* scope → refused (use ``upgrade``).
      - Pack at the *other* scope, no ``--force`` → refused; stderr
        names the other scope and the bypass flag.
      - Pack at the other scope, with ``--force`` → dual-scope install:
        re-confirms the existing scope and installs at the new scope,
        printing two ``installed:`` lines in repo-then-user order.
  - **Pre-flight order**: every scope's preconditions (``~``-expansion,
    Rails A/B/C re-check, path-jail probe) run **before** any write to
    either scope. A user-scope failure after a repo write would leave a
    half-applied install on disk, so we sequence: resolve → check → write.
  - **State-file v0.1 refusal** is delegated to
    :func:`config.load_state(..., for_write=True)`.

Tier-1/2/3 classification is unchanged from the pre-RFC-0004 shape;
both scope roots use :func:`_classify_for_install`. Writes go through
:func:`safety.write_jailed` with the matching ``scope`` and
``allowed_prefixes`` so the user-scope jail fires.
"""

from __future__ import annotations

import functools
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State
    from agentbundle.safety import Tier


@dataclass
class _ScopePlan:
    """One scope's worth of pre-flight + write data.

    Computed during pre-flight and consumed at write time. Keeping the
    fields in a dataclass lets the dual-scope path assemble *all*
    plans (and surface any pre-flight failure across either scope)
    before any side-effect runs.
    """

    scope: str
    root: Path  # absolute path of the scope's root
    state_path: Path  # absolute path of the scope's state file
    allowed_prefixes: list[str] | None
    state: "State"  # the loaded state at this scope (read-only mode)
    already_installed: bool
    # `.upstream.<ext>` companion relpaths written during this scope's
    # step-9 projection loop. Threaded to the install marker so the
    # adapt-to-project skill can surface class-2 work without re-walking
    # the tree. Stays empty when nothing collided.
    new_companions: list[str] = field(default_factory=list)


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle install``.

    Returns 0 on success, non-zero on any failure. See module docstring
    for the dual-scope contract.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import check_spec_version_gate
    from agentbundle.config import (
        ConfigError,
        PackState,
        dump_state,
        load_pack_toml,
        load_state,
    )
    from agentbundle.render import render_pack
    from agentbundle import safety, scope as scope_mod
    from agentbundle.build import scope_rails

    pack_name: str = args.pack
    catalogue_uri: str = args.catalogue
    cli_scope: str | None = getattr(args, "scope", None)
    force: bool = bool(getattr(args, "force", False))
    force_merge: bool = bool(getattr(args, "force_merge", False))
    output_root = Path(args.output).resolve()

    # `--force-merge` runtime binding (Step 2's resolved scope is the
    # source of truth — see below). The early check here catches an
    # explicit ``--scope repo``; the resolved-scope check after
    # Step 2 catches the case where the pack defaults to repo scope.
    if force_merge and cli_scope == "repo":
        print(
            "install: --force-merge is bound to user scope; pass --scope user "
            "or omit --force-merge",
            file=sys.stderr,
        )
        return 1

    # Range-check the CLI-supplied pack name before any I/O. The manifest's
    # `pack.name` is checked by `_assert_pack_metadata_shape` below; this
    # second check covers `args.pack` itself, which becomes a TOML key in
    # `dump_state` and a TOML basic-string value in `_append_install_marker`.
    # Injection is structurally prevented by `_emit_basic_string` /
    # `_toml_key`, but refusing here is the bell-rings-loud companion.
    if not _PACK_NAME_RE.fullmatch(pack_name):
        print(
            f"install: pack {pack_name!r} has invalid name: "
            f"must match ^[a-z0-9][a-z0-9-]*$ per docs/CONVENTIONS.md",
            file=sys.stderr,
        )
        return 1

    # ── Step 1: Resolve catalogue + locate + spec gate ────────────────────────
    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1
    pack_dir = _locate_pack(catalogue_dir, pack_name)
    if pack_dir is None:
        print(
            f"install: pack {pack_name!r} not found in catalogue at {catalogue_dir}; "
            "expected packs/<pack>/ or <catalogue>/<pack>/",
            file=sys.stderr,
        )
        return 1
    try:
        pack_toml = load_pack_toml(pack_dir / "pack.toml")
    except ConfigError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1
    gate = check_spec_version_gate(pack_toml)
    if gate is not None:
        return gate
    # Defence-in-depth against pack-metadata-driven TOML injection: refuse
    # manifests whose name / version fall outside their canonical grammars
    # before any write. The relpath half of the check runs after
    # `render_pack` (it needs the projection) — see Step 7 below.
    try:
        _assert_pack_metadata_shape(pack_toml)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # ── Step 2: Resolve scope ─────────────────────────────────────────────────
    # RFC-0004 § *v0.1 vs v0.2 contract acceptance*: a stray
    # [pack.install] table on a v0.1 pack is *ignored*. We gate the
    # install table on the declared contract version so a legacy pack
    # carrying `default-scope = "user"` does NOT resolve to user scope.
    # Mirrors validate.py:_allowed_scopes, kept in sync intentionally.
    from agentbundle.config import pack_spec_version

    # v0.2 introduced `[pack.install]`; v0.3 (RFC-0005) added optional
    # `user-scope-hooks` but did not change scope-resolution semantics.
    # Mirror validate.py:_allowed_scopes — both versions carry the
    # install table. The v0.1 path stays gateless (legacy implied
    # `default-scope = "repo"`).
    if pack_spec_version(pack_toml) in ("0.2", "0.3"):
        pack_install = pack_toml.get("pack", {}).get("install")
    else:
        pack_install = None
    try:
        requested_scope = scope_mod.resolve(
            cli_scope, pack_install, pack_name=pack_name
        )
    except scope_mod.ScopeRefused as exc:
        print(
            f"install: {exc.pack_name}: scope {exc.requested!r} not in "
            f"allowed-scopes {exc.allowed}",
            file=sys.stderr,
        )
        return 1

    # RFC-0005 § Binding: ``--force-merge`` is bound to user scope only.
    # Gate on the *resolved* scope (the source of truth post-Step 2)
    # so a pack defaulting to repo scope also surfaces the refusal,
    # not just an explicit `--scope repo`.
    if force_merge and requested_scope != "user":
        print(
            "install: --force-merge is bound to user scope; pass --scope user "
            "or omit --force-merge",
            file=sys.stderr,
        )
        return 1

    # ── Step 3: Pre-flight — load state at *both* scopes ──────────────────────
    # Read-only loads (for_write=False) — we do the v0.1 refusal *only*
    # for scopes we're about to write to, after we know which they are.
    # Loading both is cheap and reveals the cross-scope conflict.
    repo_state_path = output_root / ".agent-ready-state.toml"
    user_root: Path | None
    user_state_path: Path | None
    try:
        repo_state = load_state(repo_state_path)
    except ConfigError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1

    # User scope resolution fires when the install itself touches user
    # scope, OR when the installing pack declares
    # `[[pack.dependencies.required]]` (AC17 union-of-scopes resolution
    # requires user_state to be consulted even for repo-only addons —
    # otherwise a `core` install at user scope is invisible to the
    # gate). Defer the expanduser call to avoid raising on adopters
    # with $HOME=/ when neither condition fires.
    _pack_has_required = bool(
        pack_toml.get("pack", {}).get("dependencies", {}).get("required")
    )
    needs_user_state = (
        requested_scope == "user"
        or "user" in _resolved_allowed_scopes(pack_install)
        or _pack_has_required
    )
    user_state = None
    if needs_user_state:
        try:
            user_root = scope_mod.resolve_user_root()
        except scope_mod.UserScopeUnresolvable:
            user_root = None  # surface only if we actually need to write
        if user_root is not None:
            user_state_path = user_root / ".agent-ready" / "state.toml"
            try:
                user_state = load_state(user_state_path)
            except ConfigError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
        else:
            user_state_path = None
    else:
        user_root = None
        user_state_path = None

    installed_at_repo = pack_name in repo_state.packs
    installed_at_user = user_state is not None and pack_name in user_state.packs

    # ── Step 3b: Dependency gate — [pack.dependencies.required] ──────────────
    # Resolves required deps against the union of repo + user state (AC17).
    # Gate runs before any write (and before the already-installed check, so
    # dep errors surface even when another early-exit would fire).
    from agentbundle.config import State as _State

    _effective_user_state: "State" = user_state if user_state is not None else _State()
    try:
        validate_dependencies_required(
            pack_toml, repo_state=repo_state, user_state=_effective_user_state
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # ── Step 4: Branch on already-installed shape ─────────────────────────────
    # 4a. Already at requested scope → refuse (use 'upgrade'); --force does
    #     not bypass this case.
    if (requested_scope == "repo" and installed_at_repo) or (
        requested_scope == "user" and installed_at_user
    ):
        print(
            f"install: {pack_name} already installed at {requested_scope}; "
            "use 'upgrade' to change version",
            file=sys.stderr,
        )
        return 1

    # 4b. Already at the *other* scope, no --force → refuse cross-scope.
    other_scope = "user" if requested_scope == "repo" else "repo"
    other_already = installed_at_user if requested_scope == "repo" else installed_at_repo
    if other_already and not force:
        print(
            f"install: {pack_name} already installed at {other_scope}; "
            "pass --force to install at both",
            file=sys.stderr,
        )
        return 1

    # ── Step 5: Build the scope plan(s) ───────────────────────────────────────
    # Determine which scopes this run will write to. Dual-scope is the
    # --force-and-pack-already-at-other-scope case; everything else is
    # single-scope. Pre-flight all of them before any write.
    scopes_to_install: list[str] = []
    if force and other_already:
        # Dual-scope path: repo first, then user (spec § *Output*).
        scopes_to_install = ["repo", "user"]
    else:
        scopes_to_install = [requested_scope]

    # Probe per-adapter scope metadata (for allowed-prefixes at user
    # scope). The Claude Code adapter ships a [scope] block from
    # RFC-0004; RFC-0005's T1 added one to Kiro too. Resolve which
    # adapter the user-scope install targets and use that adapter's
    # `allowed-prefixes.user`. Kiro-targeted packs (those shipping
    # `.apm/agents/`) get Kiro's `.kiro/` prefix; everything else
    # gets Claude Code's `.claude/` prefix.
    user_target_adapter = _resolve_user_scope_target_adapter(pack_dir)
    allowed_prefixes_user = _adapter_allowed_prefixes_user(user_target_adapter)

    # RFC-0005 AC25: refuse install --scope user against an adapter
    # that doesn't declare a working user-scope hook-wiring mode. The
    # heuristic above picks kiro/claude-code; this guard catches a
    # contract-misconfiguration regression (e.g. someone strips
    # `user-merge-json` from the contract or sets `dropped`) before
    # any byte is written.
    user_scope_hooks_opt_in = bool(
        isinstance(pack_install, dict)
        and pack_install.get("user-scope-hooks") is True
    )
    if (
        user_scope_hooks_opt_in
        and requested_scope == "user"
        and not _adapter_supports_user_scope_hook_wiring(user_target_adapter)
    ):
        print(
            f"install: adapter {user_target_adapter!r} does not declare a "
            f"hook-wiring mode that supports user scope; pack {pack_name} "
            f"requires it",
            file=sys.stderr,
        )
        return 1

    plans: list[_ScopePlan] = []
    for scope_value in scopes_to_install:
        if scope_value == "repo":
            plans.append(
                _ScopePlan(
                    scope="repo",
                    root=output_root,
                    state_path=repo_state_path,
                    allowed_prefixes=None,
                    state=repo_state,
                    already_installed=installed_at_repo,
                )
            )
        else:
            # User scope: surface unresolvable $HOME *now* so failures
            # land in pre-flight, before any write.
            try:
                user_root_resolved = scope_mod.resolve_user_root()
            except scope_mod.UserScopeUnresolvable:
                print(
                    "install: cannot resolve user scope: $HOME unset or invalid",
                    file=sys.stderr,
                )
                return 1
            # Print the resolved root to stderr so the adopter sees
            # the destination before any side-effect.
            print(f"install: user scope resolved to {user_root_resolved}", file=sys.stderr)
            # Re-load user state in for-write mode so a v0.1 file fails
            # here (after the resolved-root line so adopters see context).
            try:
                user_state_for_write = load_state(
                    user_root_resolved / ".agent-ready" / "state.toml", for_write=True
                )
            except ConfigError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            plans.append(
                _ScopePlan(
                    scope="user",
                    root=user_root_resolved,
                    state_path=user_root_resolved / ".agent-ready" / "state.toml",
                    allowed_prefixes=allowed_prefixes_user,
                    state=user_state_for_write,
                    already_installed=installed_at_user,
                )
            )

    # If the repo plan is going to be written to (not just a recap),
    # also load the state in for-write mode so v0.1 refusal fires.
    for plan in plans:
        if plan.scope == "repo" and not plan.already_installed:
            try:
                plan.state = load_state(plan.state_path, for_write=True)
            except ConfigError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1

    # ── Step 6: Pre-flight — rails A/B/C for any user-scope write ────────────
    # Also run the kiro attach-to-agent rail (T2's `check_kiro_wiring`)
    # for user-scope kiro-targeted packs. Catches malformed wiring TOMLs
    # (missing/typo'd `attach-to-agent`, path-traversal payloads) before
    # any render — the build-pipeline error message ("internal: <path>
    # missing") isn't actionable for adopters; this rail surfaces the
    # actual contract violation.
    if any(p.scope == "user" for p in plans) and user_target_adapter == "kiro":
        target_adapters = {"kiro"}
        kiro_refusal = scope_rails.check_kiro_wiring(
            pack_dir, pack_name, target_adapters
        )
        if kiro_refusal is not None:
            print(f"install: {kiro_refusal}", file=sys.stderr)
            return 1
    for plan in plans:
        if plan.scope == "user":
            allowed_scopes = _resolved_allowed_scopes(pack_install)
            # RFC-0005 § Rail B — user-scope lift: the
            # `[pack.install] user-scope-hooks = true` consent gesture
            # threads through to the rail at install time too. Without
            # this, validate and install would disagree on the same
            # pack: validate would accept (post-T3), install would
            # refuse — a surface-mismatch class of bug.
            user_scope_hooks = bool(pack_install.get("user-scope-hooks") is True)
            rail_refusal = scope_rails.run_all(
                pack_dir, allowed_scopes, user_scope_hooks
            )
            if rail_refusal is not None:
                print(
                    f"install: {pack_name}: {rail_refusal}",
                    file=sys.stderr,
                )
                return 1

    # ── Step 7: Render projection — per-scope shape ───────────────────────────
    # RFC-0004's user-scope install lands a Claude Code overlay (paths
    # under `.claude/...`), not the dist-tree shape `render_pack`
    # produces. We render twice when the run spans both scopes: once for
    # the dist-tree (consumed by repo-scope writes) and once for the
    # Claude-Code-only projection (consumed by user-scope writes). The
    # dist-tree render is cached for the lifetime of this run; the
    # Claude-Code render uses the same adapter the `make build --self`
    # path uses (the spec §Tier model defines this as the user-scope
    # projection target).
    repo_projection: dict[str, bytes] | None = None
    user_projection: dict[str, bytes] | None = None
    # RFC-0005 § hook-body at user scope: user-scope packs ship hook
    # bodies that project to `<adapter>/hooks/<pack>/` (not the legacy
    # `tools/hooks/`); RFC-0005 § hook-wiring lands the wiring merger
    # against the adopter's settings or pack-owned agent JSON instead
    # of writing the wiring TOML to disk. Both rewrites happen
    # post-render and pre-path-jail.
    # `user_target_adapter` resolved earlier (alongside allowed_prefixes_user).
    try:
        if any(p.scope == "repo" for p in plans):
            repo_projection = render_pack(pack_dir)
        if any(p.scope == "user" for p in plans):
            user_projection = _render_for_user_scope(pack_dir)
            user_scope_hooks_enabled = bool(
                isinstance(pack_install, dict)
                and pack_install.get("user-scope-hooks") is True
            )
            if user_scope_hooks_enabled:
                user_projection = _rewrite_user_scope_hook_paths(
                    user_projection,
                    pack_name=pack_name,
                    target_adapter=user_target_adapter,
                )
    except (FileNotFoundError, ValueError) as exc:
        print(f"install: render failed for pack {pack_name!r}: {exc}", file=sys.stderr)
        return 1

    # RFC-0005 § Binding: ``--force-merge`` is Claude-Code-only. The
    # kiro merge target is a pack-owned agent JSON; adopter collision
    # is structurally a non-case. Refuse early once the target adapter
    # is known.
    if force_merge and user_target_adapter != "claude-code" and any(
        p.scope == "user" for p in plans
    ):
        print(
            "install: --force-merge applies only to Claude-Code-targeted packs; "
            f"pack {pack_name} resolves to adapter '{user_target_adapter}' at user scope",
            file=sys.stderr,
        )
        return 1

    # Full re-check including projection relpaths now that `render_pack`
    # has produced the per-scope projection(s). Name + version are
    # idempotently re-validated (already passed once after `load_pack_toml`);
    # the load-bearing addition at this site is the relpath loop, which
    # needs the projection's keys to run. Refuses if a single bad path
    # appears at either scope.
    try:
        for _projection in (repo_projection, user_projection):
            if _projection is not None:
                _assert_pack_metadata_shape(pack_toml, projection=_projection)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    pack_version: str = pack_toml.get("pack", {}).get("version", "0.0.0")

    # ── Step 8: Pre-flight — path-jail probe every projected file ─────────────
    # The probe is read-only: assert_under + (for user) prefix check.
    # This catches a pack whose projection rule resolves under
    # ~/Documents/ before any byte is written.
    for plan in plans:
        projection = repo_projection if plan.scope == "repo" else user_projection
        if projection is None:
            continue
        for relpath in projection.keys():
            target = plan.root / relpath
            try:
                safety.assert_under(plan.root, target)
            except safety.PathJailError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            if plan.scope == "user":
                target_relpath = target.resolve().relative_to(plan.root.resolve()).as_posix()
                prefixes = plan.allowed_prefixes or []
                # Directory-boundary matching only — see safety.py.
                if not any(target_relpath.startswith(p) for p in prefixes):
                    print(
                        f"install: refusing to write outside allowed prefixes "
                        f"for scope 'user': {target.resolve()}",
                        file=sys.stderr,
                    )
                    return 1

    # ── Step 9: All pre-flight passed — perform writes ────────────────────────
    for plan in plans:
        # Skip the write for the already-installed scope in a dual-scope
        # --force run: the state file is already correct; we re-emit
        # the `installed:` line for the recap, but we don't rewrite.
        if plan.already_installed:
            continue

        projection = repo_projection if plan.scope == "repo" else user_projection
        if projection is None:
            projection = {}

        # Reset the PackState for this scope's install.
        prior = plan.state.packs.get(pack_name)
        new_pack_state = PackState(
            installed_version=pack_version,
            source="agent-ready-repo",
            install_route="cli",
            scope=plan.scope,
            primitives=_collect_primitives(pack_dir),
            files={},
            primitive_versions=dict(prior.primitive_versions) if prior else {},
        )

        for relpath, content in sorted(projection.items()):
            tier = _classify_for_install(
                relpath, plan.root, content, plan.state, pack_name=pack_name,
            )
            if tier is safety.Tier.TIER_2:
                try:
                    safety.write_companion(plan.root, relpath, content)
                except safety.PathJailError as exc:
                    print(f"install: {exc}", file=sys.stderr)
                    return 1
                plan.new_companions.append(
                    safety.companion_path(Path(relpath)).as_posix()
                )
            else:
                try:
                    safety.write_jailed(
                        plan.root,
                        relpath,
                        content,
                        scope=plan.scope,
                        allowed_prefixes=plan.allowed_prefixes,
                    )
                except safety.PathJailError as exc:
                    print(f"install: {exc}", file=sys.stderr)
                    return 1
            new_pack_state.files[relpath] = {
                "sha": safety.sha256_bytes(content),
                "from-pack-version": pack_version,
            }

        # RFC-0005 T8b — user-scope hook-wiring merge phase.
        # Runs after file writes (so hook bodies exist where wiring
        # entries reference them via $HOOK_BODY_PATH-style placeholders;
        # T8b's resolver-time substitution is the consumer's concern).
        # Captures (event, id[, target-file]) tuples and writes them
        # to ``hook_wiring_owned`` on the PackState so uninstall can
        # be precise.
        if plan.scope == "user":
            user_scope_hooks_enabled = bool(
                isinstance(pack_install, dict)
                and pack_install.get("user-scope-hooks") is True
            )
            if user_scope_hooks_enabled:
                try:
                    owned_rows = _merge_user_scope_hook_wiring(
                        pack_dir=pack_dir,
                        pack_name=pack_name,
                        target_adapter=user_target_adapter,
                        install_root=plan.root,
                        force_merge=force_merge,
                    )
                except Exception as exc:
                    print(f"install: {exc}", file=sys.stderr)
                    return 1
                new_pack_state.hook_wiring_owned = owned_rows
                if user_target_adapter == "kiro":
                    new_pack_state.adapter = "kiro"

                # The merge phase re-wrote the agent JSON (Kiro) with
                # the hook entries we just merged in. Refresh the
                # state.files SHA so uninstall's Tier-1 check still
                # passes — see ``_refresh_merge_target_shas``.
                _refresh_merge_target_shas(
                    pack_state=new_pack_state,
                    owned_rows=owned_rows,
                    root=plan.root,
                )

        plan.state.packs[pack_name] = new_pack_state
        # Stamp the post-write schema. Always emit the current
        # ``STATE_SCHEMA_VERSION`` (bumped to v0.3 in T8a) so a fresh
        # install never produces a state file pinned at a stale version.
        from agentbundle.config import STATE_SCHEMA_VERSION

        plan.state.schema_version = STATE_SCHEMA_VERSION
        serialised = dump_state(plan.state)
        try:
            safety.write_jailed(
                plan.root,
                str(plan.state_path.relative_to(plan.root)),
                serialised,
                scope=plan.scope,
                allowed_prefixes=plan.allowed_prefixes,
            )
        except safety.PathJailError as exc:
            print(f"install: {exc}", file=sys.stderr)
            return 1

    # ── Step 10: recommends cross-scope warnings (stderr) ─────────────────────
    # Emitted per scope per recommend per spec § *recommends across
    # scopes*. The warning text distinguishes three cases (compatible-
    # present / missing-installable / scope-disjoint). Output goes to
    # stderr so the `installed:` rail on stdout stays parseable.
    recommends = pack_toml.get("pack", {}).get("recommends", [])
    if isinstance(recommends, list):
        for plan in plans:
            # The recommending scope is each plan's scope; a dual-scope
            # --force install emits one warning per scope per recommend.
            for rec in recommends:
                if not isinstance(rec, str):
                    continue
                _emit_recommends_warning(
                    rec,
                    recommending_scope=plan.scope,
                    catalogue_dir=catalogue_dir,
                    repo_state=repo_state,
                    user_state=user_state,
                )

    # ── Step 11: Write install marker(s) per scope ───────────────────────────
    # Per spec AC19a: after every successful install, append a
    # `[[packs-installed]]` entry to `.adapt-install-marker.toml` at the
    # install's scope root. The file's *path* encodes the scope.
    pack_version = pack_toml.get("pack", {}).get("version", "")
    # Per AC19a: markers are repo-only, so unresolved-markers is computed
    # off the **repo-scope** projection regardless of which scopes the
    # install touched. User-scope marker files always carry [].
    repo_unresolved_markers = (
        _collect_unresolved_markers(repo_projection)
        if repo_projection is not None
        else []
    )
    for plan in plans:
        scope_markers = repo_unresolved_markers if plan.scope == "repo" else []
        try:
            _append_install_marker(
                plan.root,
                plan.scope,
                pack_name=pack_name,
                pack_version=pack_version,
                unresolved_markers=scope_markers,
                new_companions=plan.new_companions,
                allowed_prefixes=plan.allowed_prefixes,
            )
        except (OSError, safety.PathJailError) as exc:
            print(f"install: {exc}", file=sys.stderr)
            return 1

    # ── Step 12: Chained adapt (in-process) ──────────────────────────────────
    # Per spec AC19b: invoke `agentbundle.commands.adapt.run` in-process
    # with --values-from <repo>/.adapt-discovery.toml regardless of the
    # install scope (markers are repo-only). AC19d covers the two
    # failure modes.
    repo_plan = next((p for p in plans if p.scope == "repo"), None)
    repo_root_for_adapt = (
        repo_plan.root if repo_plan is not None else Path(args.output).resolve()
    )
    adapt_rc = _chain_adapt(repo_root_for_adapt)
    if adapt_rc != 0:
        # Per AC19d (ii): malformed `.adapt-discovery.toml` causes the
        # chained adapt to raise; install exits non-zero. The marker
        # file was already written in step 11 — that's by design.
        return adapt_rc

    # ── Step 13: Emit installed: lines (repo first, user last) ───────────────
    for plan in plans:
        print(f"installed: {pack_name} @ {plan.scope}")

    return 0


_PACK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_PACK_VERSION_RE = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"
)


def _assert_pack_metadata_shape(
    pack_toml: dict,
    *,
    projection: "dict[str, bytes] | None" = None,
) -> None:
    """Defence-in-depth: refuse a pack whose manifest or projection
    relpaths fall outside the canonical TOML-safe grammars.

    The structural fix for pack-metadata-driven TOML injection lives in
    :func:`config._emit_basic_string`. This validator is the bell-rings-
    loud companion at the install boundary: it stops the install before
    any write to either scope's state file. The three checks:

    - ``pack.name`` matches ``^[a-z0-9][a-z0-9-]*$`` per
      ``docs/CONVENTIONS.md``.
    - ``pack.version`` matches a SemVer-ish grammar
      ``^[0-9]+\\.[0-9]+\\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$``.
      ``pack.schema.json`` types this as a bare string today; we tighten
      here because every value that lands in a basic-string position
      should be regex-shaped, not free-form.
    - If *projection* is supplied, every relpath contains no ``"``,
      ``\\``, or control character (U+0000..U+001F, U+007F).

    Raises ``RuntimeError`` on the first violation with a message
    shaped ``install: pack '<name>' has invalid <field>: <reason>`` —
    callers print ``str(exc)`` to stderr and exit non-zero.
    """
    pack_block = pack_toml.get("pack", {}) if isinstance(pack_toml, dict) else {}
    name_raw = pack_block.get("name", "") if isinstance(pack_block, dict) else ""
    version_raw = pack_block.get("version", "") if isinstance(pack_block, dict) else ""

    # `name` is the visible identifier in the error message — if it's
    # not a string, fall back to the type-name for the operator's sake
    # but don't interpolate the raw value (which may itself be
    # adversarial). `<unknown>` matches the placeholder used by
    # validate_dependencies_required for the same reason.
    name_for_message = name_raw if isinstance(name_raw, str) else "<unknown>"

    if not isinstance(name_raw, str) or not _PACK_NAME_RE.fullmatch(name_raw):
        raise RuntimeError(
            f"install: pack {name_for_message!r} has invalid name: "
            f"must match ^[a-z0-9][a-z0-9-]*$ per docs/CONVENTIONS.md"
        )

    if not isinstance(version_raw, str) or not _PACK_VERSION_RE.fullmatch(version_raw):
        # The raw value is operator-untrusted (it's the attack vector); do
        # not interpolate it into stderr — that surface can carry ANSI or
        # other terminal-bound bytes. The operator can `cat pack.toml` to
        # inspect it themselves.
        raise RuntimeError(
            f"install: pack {name_for_message!r} has invalid version: "
            f"must match ^[0-9]+\\.[0-9]+\\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"
        )

    if projection is not None:
        for relpath in projection:
            if not isinstance(relpath, str):
                raise RuntimeError(
                    f"install: pack {name_for_message!r} has invalid "
                    f"projection relpath: not a string"
                )
            # Refuse `"`, `\`, and any control char. Newlines, tabs and
            # carriage returns are control chars; null bytes too. The
            # path-jail probe (Step 8 in `run`) catches traversal; this
            # check catches TOML-grammar bombs that the path-jail would
            # let through. Same stderr discipline as version: do not
            # interpolate the raw relpath into the message — only its
            # length, which is bounded and operator-safe.
            if any(c == '"' or c == "\\" or ord(c) < 0x20 or ord(c) == 0x7F for c in relpath):
                raise RuntimeError(
                    f"install: pack {name_for_message!r} has invalid "
                    f"projection relpath (length {len(relpath)}): contains a "
                    f"quote, backslash, or control character"
                )


def _collect_unresolved_markers(projection: dict) -> list[str]:
    """Return sorted, deduplicated list of `<adapt:NAME>` markers found
    in the projection's byte content. The skill resolves these later;
    the install marker just enumerates them for the nudge surface."""
    import re

    marker_re = re.compile(r"<adapt:([a-z][a-z0-9-]*)>")
    seen: set[str] = set()
    for _relpath, content in projection.items():
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                continue
        else:
            text = str(content)
        for name in marker_re.findall(text):
            seen.add(name)
    return sorted(seen)


def _append_install_marker(
    root: Path,
    scope: str,
    *,
    pack_name: str,
    pack_version: str,
    unresolved_markers: list[str],
    new_companions: list[str],
    allowed_prefixes: list[str] | None,
) -> None:
    """Append a `[[packs-installed]]` entry to `.adapt-install-marker.toml`
    at *root* via `os.replace` atomic rename. Repo-scope marker lives
    at `<repo>/.adapt-install-marker.toml`; user-scope at
    `<user-root>/.agent-ready/.adapt-install-marker.toml`.

    Per spec AC19a: scope is encoded by the file's location, not as a
    field — the path is the source of truth.
    """
    import os
    import tomllib
    from datetime import datetime, timezone

    from agentbundle import safety

    if scope == "user":
        # Route through `safety.user_state_path` so the dot-directory
        # is created with mode 0o700 + symlink/non-directory probe.
        # The helper returns `<home>/.agent-ready/state.toml`; we sit
        # the marker next to it.
        state_path = safety.user_state_path(home=root)
        marker_path = state_path.parent / ".adapt-install-marker.toml"
        marker_relpath = ".agent-ready/.adapt-install-marker.toml"
    else:
        marker_path = root / ".adapt-install-marker.toml"
        marker_relpath = ".adapt-install-marker.toml"

    # Read existing entries if present.
    entries: list[dict] = []
    if marker_path.exists():
        try:
            existing = tomllib.loads(marker_path.read_text(encoding="utf-8"))
        except Exception as exc:
            # Spec rail: silent discard would hide prior pack adaptations
            # from the next session's nudge. Warn explicitly so the
            # override is auditable; proceed with the fresh entry.
            print(
                f"install: warning: existing install marker at {marker_path} "
                f"is malformed ({exc}); prior entries lost — re-run install "
                f"for any earlier packs",
                file=sys.stderr,
            )
            existing = {}
        raw_entries = existing.get("packs-installed", [])
        if isinstance(raw_entries, list):
            for e in raw_entries:
                if not isinstance(e, dict):
                    continue
                # Defence-in-depth: a CLI-written marker has `installed-at`
                # as a TOML datetime literal, which `tomllib` parses to a
                # `datetime.datetime`. A hand-edited or attacker-mediated
                # marker could carry `installed-at = "...\nphantom = ..."`
                # (a TOML basic-string in the position) which `tomllib`
                # parses to a `str` containing real control chars — and
                # bare re-emission would land phantom TOML structure on
                # the next install. Drop any entry whose `installed-at`
                # isn't a `datetime`; warn so the operator can investigate.
                ts = e.get("installed-at")
                if not isinstance(ts, datetime):
                    print(
                        f"install: warning: dropping marker entry with non-"
                        f"datetime installed-at at {marker_path} "
                        f"(prior entry will not surface in the next nudge)",
                        file=sys.stderr,
                    )
                    continue
                entries.append(e)

    new_entry = {
        "name": pack_name,
        "version": pack_version,
        # Store as a `datetime` (not a strftime'd string) so the emit loop
        # has a single uniform type to handle for both new and re-read
        # entries, with the canonical strftime applied at emission time.
        "installed-at": datetime.now(timezone.utc),
        "unresolved-markers": unresolved_markers,
        "new-companions": new_companions,
    }
    entries.append(new_entry)

    # Serialise. Single source of truth: this writer (no shared helper
    # because the install marker is a different shape from the other
    # CLI artifacts). Every pack-sourced basic-string position routes
    # through `_emit_basic_string` so adversarial pack metadata cannot
    # land phantom TOML structure here (see `config._emit_basic_string`).
    from agentbundle.config import _emit_basic_string

    lines: list[str] = [
        f"marker-schema-version = {_emit_basic_string('0.1')}",
        "",
    ]
    for entry in entries:
        lines.append("[[packs-installed]]")
        lines.append(f"name = {_emit_basic_string(entry['name'])}")
        lines.append(f"version = {_emit_basic_string(entry['version'])}")
        # `installed-at` is emitted bare as a TOML offset-datetime
        # literal. The dict's value is always a `datetime` (new entries
        # are stored that way above; re-read entries are filtered to
        # datetime-only at load time). `strftime` produces the canonical
        # `YYYY-MM-DDTHH:MM:SSZ` shape; no basic-string position, no
        # injection vector.
        ts_str = entry["installed-at"].strftime("%Y-%m-%dT%H:%M:%SZ")
        lines.append(f"installed-at = {ts_str}")
        lines.append(f"install-route = {_emit_basic_string('cli')}")
        markers_repr = ", ".join(
            _emit_basic_string(m) for m in entry.get("unresolved-markers", [])
        )
        lines.append(f"unresolved-markers = [{markers_repr}]")
        comps_repr = ", ".join(
            _emit_basic_string(c) for c in entry.get("new-companions", [])
        )
        lines.append(f"new-companions = [{comps_repr}]")
        lines.append("")
    content = "\n".join(lines).rstrip() + "\n"

    # Atomic-rename write per AC19a, routed through the per-scope
    # path-jail (safety.write_jailed) so user-scope marker writes
    # honour `allowed-prefixes.user` and a future contract change
    # cannot let the marker escape the jail without code review
    # noticing.
    safety.write_jailed(
        root,
        marker_relpath,
        content,
        scope=scope,
        allowed_prefixes=allowed_prefixes,
    )


def _chain_adapt(repo_root: Path) -> int:
    """Per AC19b: run `agentbundle.commands.adapt.run` in-process with
    `--values-from <repo>/.adapt-discovery.toml`.

    Per AC19d:
      (i) missing `<repo>/.adapt-discovery.toml` → adapt step is
          skipped, emits one stderr line; install exits 0.
      (ii) malformed discovery → adapt returns non-zero; the install
          caller propagates non-zero. The marker file is still on disk
          because step 11 wrote it before this step.
    """
    import argparse as _argparse

    from agentbundle.commands import adapt as _adapt

    discovery_path = repo_root / ".adapt-discovery.toml"
    if not discovery_path.exists():
        print(
            "adapt: no .adapt-discovery.toml at repo root; markers left unresolved",
            file=sys.stderr,
        )
        return 0

    ns = _argparse.Namespace(
        root=str(repo_root),
        values_from=str(discovery_path),
        ci=False,
    )
    return _adapt.run(ns)


def _emit_recommends_warning(
    rec_name: str,
    *,
    recommending_scope: str,
    catalogue_dir: Path,
    repo_state,
    user_state,
) -> None:
    """Print the spec-shaped warning for a single `recommends` entry.

    Three cases the spec text distinguishes (all to stderr):
      * Found at a compatible scope → `(found at <observed-scope> scope)`.
      * Not installed anywhere, installable at recommending scope →
        `(not installed)`.
      * Disjoint scopes (recommending scope ∉ recommended's allowed-scopes)
        → ``which is <only>-only; install it in your active project`` /
        ``which is <only>-only; install it at user scope``.

    The dual-scope case (recommended permits both scopes) reduces to one
    of the first two — disjoint can only fire when the recommended
    pack's ``allowed-scopes`` is single-valued.
    """
    import re
    import tomllib

    # Pack names follow the catalogue's `^[a-z0-9][a-z0-9-]*$` shape
    # (CONVENTIONS.md). The contents of `recommends` are not currently
    # schema-validated, so a malicious pack could declare
    # ``recommends = ["../../../etc/passwd"]`` and probe the adopter's
    # filesystem via the lookup below. Refuse anything outside the
    # name-shape to keep the catalogue path-jail honest.
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", rec_name):
        print(
            f"install: warning: ignoring malformed recommends entry "
            f"{rec_name!r} (not a legal pack name)",
            file=sys.stderr,
        )
        return

    rec_repo_installed = rec_name in repo_state.packs if repo_state else False
    rec_user_installed = rec_name in user_state.packs if user_state else False

    # Look up the recommended pack's allowed-scopes from the catalogue.
    # We only need this for the disjoint branch; cache the lookup result.
    rec_pack_toml = catalogue_dir / "packs" / rec_name / "pack.toml"
    if not rec_pack_toml.exists():
        rec_pack_toml = catalogue_dir / rec_name / "pack.toml"
    rec_allowed: list[str] = ["repo"]  # legacy default
    if rec_pack_toml.exists():
        try:
            rec_data = tomllib.loads(rec_pack_toml.read_text(encoding="utf-8"))
        except Exception:
            rec_data = {}
        rec_install = rec_data.get("pack", {}).get("install")
        if isinstance(rec_install, dict):
            raw = rec_install.get("allowed-scopes")
            if isinstance(raw, list) and raw:
                rec_allowed = [s for s in raw if isinstance(s, str)]
            else:
                default = rec_install.get("default-scope")
                if isinstance(default, str):
                    rec_allowed = [default]

    # Case 1: installed at any compatible scope.
    if rec_repo_installed and "repo" in rec_allowed:
        print(
            f"note: recommends {rec_name!r} (found at repo scope)",
            file=sys.stderr,
        )
        return
    if rec_user_installed and "user" in rec_allowed:
        print(
            f"note: recommends {rec_name!r} (found at user scope)",
            file=sys.stderr,
        )
        return

    # Case 3: disjoint allowed-scopes. Reachable only when the
    # recommended pack's allowed-scopes is single-valued and excludes
    # the recommending scope (a pack permitting both scopes can never
    # be disjoint from any recommender).
    if recommending_scope not in rec_allowed:
        if rec_allowed == ["repo"]:
            print(
                f"note: recommends {rec_name!r}, which is repo-only; "
                "install it in your active project",
                file=sys.stderr,
            )
            return
        if rec_allowed == ["user"]:
            print(
                f"note: recommends {rec_name!r}, which is user-only; "
                "install it at user scope",
                file=sys.stderr,
            )
            return

    # Case 2: missing but installable at the recommending scope.
    print(
        f"note: recommends {rec_name!r} (not installed)",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_for_user_scope(pack_dir: Path) -> dict[str, bytes]:
    """Project a pack via the Claude Code adapter directly, for user-scope install.

    RFC-0004 § *State file per scope* and § *Adapter-level scope roots*
    imply that user-scope installs land *Claude Code adapter* outputs
    (paths under ``.claude/...``) rather than the dist-tree shape
    ``render.render_pack`` produces. Calling the adapter's ``project``
    function once into a tempdir gives us the per-primitive layout
    Claude Code reads at ``~/.claude/``; we collect the result as a
    relpath→bytes mapping for the install walker.

    Other adapters' projections (apm.yml, plugin manifests, etc.) are
    intentionally out of scope at user-scope install — they're
    dist-time build artifacts that the adopter's `~` should never
    carry.

    Note: for v0.3 packs declaring ``user-scope-hooks = true``, the
    install handler applies a v0.3 post-projection rewrite via
    ``_rewrite_user_scope_hook_paths`` to swap legacy hook-body
    targets (``tools/hooks/``) for the user-scope shape
    (``.claude/hooks/<pack>/`` or ``.kiro/hooks/<pack>/``) and drop
    the v0.2 wiring-target file (``.claude/settings.local.json``)
    from the projection map. The wiring TOMLs themselves are then
    consumed by ``_merge_user_scope_hook_wiring`` post-write.
    """
    import tempfile
    import tomllib

    from agentbundle.build.adapters import claude_code, kiro
    from agentbundle.build.main import _read_bundled
    from agentbundle.render import _collect_tree

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    target_adapter = _resolve_user_scope_target_adapter(pack_dir)
    with tempfile.TemporaryDirectory() as raw:
        out = Path(raw)
        if target_adapter == "kiro":
            kiro.project(pack_dir, contract, out)
        else:
            claude_code.project(pack_dir, contract, out)
        return _collect_tree(out)


def _refresh_merge_target_shas(
    *,
    pack_state,
    owned_rows: list[dict[str, str]],
    root: Path,
) -> None:
    """Refresh state.files SHA for every merge target the wiring touched.

    The merge phase (user_merge_json / merge_into_agent_json) mutates
    the target file after the projection-write loop recorded its
    pre-merge SHA. Without this refresh, uninstall's Tier-1 check
    (recorded SHA == on-disk SHA) would misclassify the file as
    adopter-edited and refuse to remove it. Claude Code rows omit
    ``target-file`` (the adapter-shared ``~/.claude/settings.json``
    isn't tracked in state.files); Kiro rows carry it explicitly.

    Shared between install and upgrade so the fix is single-sourced.
    """
    from agentbundle import safety

    for row in owned_rows:
        target_file_rel = row.get("target-file")
        if not target_file_rel:
            continue
        target_path = root / target_file_rel.lstrip("/")
        if not target_path.exists():
            continue
        if target_file_rel in pack_state.files:
            pack_state.files[target_file_rel]["sha"] = (
                safety.sha256_file(target_path)
            )


def _adapter_supports_user_scope_hook_wiring(adapter_name: str) -> bool:
    """Return True iff the adapter declares a hook-wiring projection
    mode that works at user scope (RFC-0005 AC25).

    Two shapes count:
      - Claude Code: ``mode.user = "user-merge-json"``.
      - Kiro: ``mode = "merge-into-agent-json"`` (single mode, no
        scope qualifier — the agent-file target is scope-conditional
        via `<scope-root>` resolution).

    Anything else (``dropped``, ``degraded-info-log``, absent
    projection) is refused.
    """
    import tomllib
    from agentbundle.build.main import _read_bundled

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    adapter_block = contract.get("adapter", {}).get(adapter_name, {})
    projections = adapter_block.get("projections", {}) if isinstance(adapter_block, dict) else {}
    hook_wiring = projections.get("hook-wiring") if isinstance(projections, dict) else None
    if not isinstance(hook_wiring, dict):
        return False
    mode = hook_wiring.get("mode")
    if isinstance(mode, dict):
        # Claude-Code-shape scope-map: only `user-merge-json` is the
        # documented user-scope mode. `merge-into-agent-json` would
        # be a contract misconfiguration (it targets per-agent files,
        # not a settings file) — refuse it under the scope-map branch.
        return mode.get("user") == "user-merge-json"
    # Bare-string mode: only `merge-into-agent-json` (Kiro shape)
    # implies user-scope support. `merge-json` (the v0.2 repo-only
    # form) does not.
    return mode == "merge-into-agent-json"


def _resolve_user_scope_target_adapter(pack_dir: Path) -> str:
    """Heuristic mirroring T2's `_kiro_target_adapters`: a pack ships
    ``.apm/agents/<name>.md`` iff it intends to project against Kiro
    (Kiro's hook-wiring binds inside agent JSON). Packs without agents
    project against Claude Code at user scope.

    TODO(allowed-adapters): A future RFC may add a per-pack
    ``allowed-adapters`` declaration on `pack.toml`. When it does,
    resolve via that field instead of the agents-present heuristic
    — that closes the AC25 corner case where a Copilot-only pack
    with hooks (no agents) silently resolves to ``claude-code``
    here. Until then, the heuristic is the proxy.

    Known limitation: two packs claiming the same Kiro agent name
    (each ships ``.apm/agents/<name>.md``) will both write to the
    same projected ``.kiro/agents/<name>.json`` and the second
    install will silently overwrite the first's wiring. T8c upgrade
    reconciliation (and a follow-on RFC for shared-agent ownership)
    will need to address this; T8b's single-pack ACs don't cover it.
    """
    agents_dir = pack_dir / ".apm" / "agents"
    if not agents_dir.exists():
        return "claude-code"
    for entry in agents_dir.iterdir():
        if entry.is_file() and entry.suffix == ".md":
            return "kiro"
    return "claude-code"


def _rewrite_user_scope_hook_paths(
    projection: dict[str, bytes],
    pack_name: str,
    target_adapter: str,
) -> dict[str, bytes]:
    """Rewrite legacy hook-body paths in *projection* to v0.3 user-
    scope targets per RFC-0005 § hook-body at user scope, and drop the
    v0.2 wiring-target file (the v0.3 merge engine writes through the
    user-merge-json / merge-into-agent-json path instead).

    Claude Code target: ``.claude/hooks/<pack>/<name>.{sh,py}``.
    Kiro target: ``.kiro/hooks/<pack>/<name>.{sh,py}``.

    For Kiro user-scope installs, the build pipeline's Kiro adapter
    has already merged hook-wiring into the dist's
    ``.kiro/agents/<name>.json``. The install-time merge runs again
    against the user's actual home — to keep ownership of the writes
    single-sourced (and avoid a fragile double-merge), we strip the
    ``hooks`` key from any agent JSON in the user-scope projection
    here; install copies the body-only JSON, and
    ``_merge_user_scope_hook_wiring`` re-adds the hook entries with
    the same id-shape, producing a single set of writes.
    """
    import json

    hook_subdir = ".claude/hooks" if target_adapter == "claude-code" else ".kiro/hooks"
    drop_keys = {".claude/settings.local.json"}
    hook_body_suffixes = (".sh", ".py")
    rewritten: dict[str, bytes] = {}
    for relpath, content in projection.items():
        if relpath in drop_keys:
            # The v0.2 wiring target — v0.3 merges directly into
            # `~/.claude/settings.json` via user_merge_json instead.
            continue
        if (
            relpath.startswith("tools/hooks/")
            and Path(relpath).suffix in hook_body_suffixes
        ):
            basename = Path(relpath).name
            rewritten[f"{hook_subdir}/{pack_name}/{basename}"] = content
        elif (
            target_adapter == "kiro"
            and relpath.startswith(".kiro/agents/")
            and relpath.endswith(".json")
        ):
            # Strip the `hooks` key — the install-time merge step
            # re-adds it. Single-writer discipline; double-merge
            # would be idempotent today but fragile under any
            # future timestamp/version field on entries.
            try:
                data = json.loads(content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                rewritten[relpath] = content
                continue
            if isinstance(data, dict) and "hooks" in data:
                data.pop("hooks")
            rewritten[relpath] = (
                json.dumps(data, indent=2, sort_keys=False) + "\n"
            ).encode("utf-8")
        else:
            rewritten[relpath] = content
    return rewritten


def _merge_user_scope_hook_wiring(
    pack_dir: Path,
    pack_name: str,
    target_adapter: str,
    install_root: Path,
    force_merge: bool,
) -> list[dict[str, str]]:
    """Parse the pack's ``.apm/hook-wiring/*.toml`` and dispatch to the
    appropriate v0.3 merger.

    Returns the list of ``{"event", "id", "target-file"?}`` rows the
    install handler stores on ``PackState.hook_wiring_owned``. The
    ``target-file`` field is omitted for Claude Code rows (the
    adapter's user-scope default target — ``~/.claude/settings.json``
    — is the implicit target on read; RFC-0005 § State-file impact)
    and explicit for Kiro rows.
    """
    import tomllib

    wiring_dir = pack_dir / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return []
    wiring_tomls: dict[str, dict] = {}
    for entry in sorted(wiring_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".toml":
            wiring_tomls[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
    if not wiring_tomls:
        return []

    if target_adapter == "claude-code":
        from agentbundle.build.projections.user_merge_json import project as _project

        target = install_root / ".claude" / "settings.json"
        owned = _project(target, pack_name, wiring_tomls, force_merge=force_merge)
        return [{"event": event, "id": entry_id} for event, entry_id in owned]

    # Kiro: group wiring by attach-to-agent; one merge call per agent.
    from agentbundle import safety
    from agentbundle.build.projections.merge_into_agent_json import project as _project

    # Defence-in-depth on the merge target path: a malicious
    # ``attach-to-agent`` value (e.g. ``"../../../tmp/escape"``) would
    # otherwise resolve outside the user-scope jail. The Step-8 path-
    # jail probe walks the projection dict; the merge target is
    # constructed here, post-probe, so we re-jail manually.
    _AGENT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

    wiring_by_agent: dict[str, dict[str, dict]] = {}
    for basename, body in wiring_tomls.items():
        attach = body.get("attach-to-agent") if isinstance(body, dict) else None
        if not isinstance(attach, str):
            continue
        if not _AGENT_NAME_RE.fullmatch(attach):
            raise RuntimeError(
                f"install: pack {pack_name}'s hook-wiring {basename}.toml "
                f"declares attach-to-agent={attach!r} which violates the "
                f"agent-name grammar ^[a-z0-9][a-z0-9-]*$ — refusing"
            )
        wiring_by_agent.setdefault(attach, {})[basename] = body

    rows: list[dict[str, str]] = []
    for attach_to_agent, partitioned in wiring_by_agent.items():
        target_file_rel = f".kiro/agents/{attach_to_agent}.json"
        target = install_root / target_file_rel
        try:
            safety.assert_under(install_root, target)
        except safety.PathJailError as exc:
            raise RuntimeError(f"install: merge target outside jail: {exc}") from exc
        owned = _project(target, pack_name, partitioned)
        for event, entry_id in owned:
            rows.append({"event": event, "id": entry_id, "target-file": target_file_rel})
    return rows


def _resolved_allowed_scopes(pack_install: dict | None) -> list[str]:
    """Mirror the rule the validate command applies for rails A/B/C."""
    if not isinstance(pack_install, dict):
        return ["repo"]
    raw = pack_install.get("allowed-scopes")
    if isinstance(raw, list) and raw:
        return [s for s in raw if isinstance(s, str)]
    default = pack_install.get("default-scope")
    if isinstance(default, str):
        return [default]
    return ["repo"]


@functools.cache
def _claude_code_allowed_prefixes_user() -> list[str]:
    """Read the Claude Code adapter's `allowed-prefixes.user` from the
    bundled contract. The function lives here (not in scope.py) so
    callers depending on `agentbundle.scope` don't pay the cost of
    parsing the contract for the common repo-scope path. Cached so the
    five callers (install, uninstall, upgrade, init-state --migrate,
    adapt) parse the contract at most once per CLI invocation.

    Retained as the Claude-Code-specific shortcut; new callers that
    need adapter-aware resolution should use
    ``_adapter_allowed_prefixes_user(adapter_name)`` below.
    """
    return _adapter_allowed_prefixes_user("claude-code")


def _adapter_allowed_prefixes_user(adapter_name: str) -> list[str]:
    """Read *adapter_name*'s `allowed-prefixes.user` from the contract.

    RFC-0005's T1 added a `[adapter.kiro.scope]` table alongside Claude
    Code's existing one; user-scope installs of Kiro-targeted packs
    need Kiro's prefixes (`.kiro/`, `.agent-ready/`) not Claude Code's
    (`.claude/`, `.agent-ready/`). The fallback (legacy contract
    without a scope table for the requested adapter) is the
    conservative single-prefix list rooted at the adapter's documented
    directory.
    """
    import tomllib
    from agentbundle.build.main import _read_bundled

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    try:
        return list(
            contract["adapter"][adapter_name]["scope"]["allowed-prefixes"]["user"]
        )
    except KeyError:
        # Defensive: contract didn't declare a [scope] block for this
        # adapter. Pick a sensible default rooted at the adapter's
        # documented user-scope directory.
        default_prefix = ".kiro/" if adapter_name == "kiro" else ".claude/"
        return [default_prefix]


def _classify_for_install(
    relpath: str,
    root: Path,
    incoming_content: bytes,
    state: "State",
    *,
    pack_name: str = "",
) -> "Tier":
    """Classify a projected relpath for the install command.

    Unlike ``safety.classify``, this function treats every incoming projected
    path as adapter-contract space (never Tier-3). The distinction is only
    whether the on-disk copy is safe to overwrite:

      - Not on disk OR content matches incoming bundle → Tier-1.
      - On disk with content that matches the *recorded* SHA (from a prior
        install of the same pack at the same version) → Tier-1.
      - On disk with content that differs from the bundle AND from the
        recorded SHA → Tier-2 (adopter has edited).
    """
    from agentbundle import safety as _safety

    on_disk = root / relpath
    if not on_disk.exists():
        return _safety.Tier.TIER_1

    on_disk_sha = _safety.sha256_file(on_disk)
    incoming_sha = _safety.sha256_bytes(incoming_content)

    if on_disk_sha == incoming_sha:
        return _safety.Tier.TIER_1

    for other_pack_name, ps in state.packs.items():
        recorded = ps.file_sha(relpath)
        if recorded and on_disk_sha == recorded:
            if pack_name and other_pack_name and other_pack_name != pack_name:
                print(
                    f"install: warning: {relpath!r} is also recorded under "
                    f"pack {other_pack_name!r}; the two packs project the same path",
                    file=sys.stderr,
                )
            return _safety.Tier.TIER_1

    return _safety.Tier.TIER_2


def _locate_pack(catalogue_dir: Path, pack_name: str) -> Path | None:
    """Find the pack directory inside the resolved catalogue."""
    candidate_a = catalogue_dir / "packs" / pack_name
    if candidate_a.is_dir() and (candidate_a / "pack.toml").exists():
        return candidate_a
    candidate_b = catalogue_dir / pack_name
    if candidate_b.is_dir() and (candidate_b / "pack.toml").exists():
        return candidate_b
    return None


def validate_dependencies_required(
    pack_toml: dict,
    *,
    repo_state: "State",
    user_state: "State",
) -> None:
    """Enforce [pack.dependencies.required] before any file write.

    Reads the required entries from the installing pack's manifest and
    resolves each one against the *union* of repo_state.packs and
    user_state.packs (key by pack name; a pack at either scope satisfies
    the gate).

    Version-range grammar: exactly ``^X.Y`` (caret-minor). An installed
    version ``A.B.C`` satisfies ``^X.Y`` when ``A == X AND (B > Y OR (B
    == Y AND C >= 0))``, i.e. ``>= X.Y.0 AND < (X+1).0.0``.

    Raises:
        RuntimeError: on unsupported range grammar or missing/out-of-range dep.
            Caller is expected to print str(exc) to stderr and exit 1.
    """
    import re

    _CARET_RE = re.compile(r"^\^([0-9]+)\.([0-9]+)$")

    pack_name = pack_toml.get("pack", {}).get("name", "<unknown>")
    deps = pack_toml.get("pack", {}).get("dependencies", {})
    if not isinstance(deps, dict):
        return
    required = deps.get("required")
    if not required:
        return

    # Union of installed packs across both scopes (pack name → installed version string).
    installed: dict[str, str] = {}
    for name, ps in repo_state.packs.items():
        installed[name] = ps.installed_version
    for name, ps in user_state.packs.items():
        if name not in installed:
            installed[name] = ps.installed_version

    for entry in required:
        if not isinstance(entry, dict):
            continue
        dep_name = entry.get("pack", "")
        dep_range = entry.get("version", "")

        # Validate grammar first (even before checking if the dep is installed).
        m = _CARET_RE.match(dep_range)
        if m is None:
            raise RuntimeError(
                f"install: unsupported version range {dep_range!r} for required pack "
                f"{dep_name!r}; only ^X.Y is supported"
            )

        req_major = int(m.group(1))
        req_minor = int(m.group(2))

        dep_version = installed.get(dep_name)
        if dep_version is None:
            raise RuntimeError(
                f"install: pack {pack_name!r} requires {dep_name!r} "
                f"(version {dep_range}); install {dep_name} first"
            )

        # Parse installed version X.Y.Z (allow fewer components).
        parts = dep_version.split(".")
        try:
            inst_major = int(parts[0]) if len(parts) > 0 else 0
            inst_minor = int(parts[1]) if len(parts) > 1 else 0
            inst_patch = int(parts[2]) if len(parts) > 2 else 0
        except (ValueError, IndexError):
            raise RuntimeError(
                f"install: pack {pack_name!r} requires {dep_name!r} "
                f"(version {dep_range}); install {dep_name} first"
            )

        # Satisfy: major must match AND version >= X.Y.0 AND < (X+1).0.0.
        satisfies = (
            inst_major == req_major
            and (
                inst_minor > req_minor
                or (inst_minor == req_minor and inst_patch >= 0)
            )
        )
        if not satisfies:
            raise RuntimeError(
                f"install: pack {pack_name!r} requires {dep_name!r} "
                f"(version {dep_range}); install {dep_name} first"
            )


def _collect_primitives(pack_dir: Path) -> list[str]:
    """Enumerate which primitive types exist under ``.apm/``."""
    apm = pack_dir / ".apm"
    if not apm.exists():
        return []
    names = []
    for subdir_name, ptype in (
        ("skills", "skill"),
        ("agents", "agent"),
        ("hooks", "hook-body"),
        ("hook-wiring", "hook-wiring"),
        ("commands", "command"),
    ):
        if (apm / subdir_name).exists():
            names.append(ptype)
    return names
