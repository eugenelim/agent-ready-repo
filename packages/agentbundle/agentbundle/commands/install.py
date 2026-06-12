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
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State
    from agentbundle.safety import Tier
    from agentbundle.user_config import UserConfig

# enumerate_event_dropped_wirings is imported at module level so it is
# patchable from tests (the mock target is
# ``agentbundle.commands.install.enumerate_event_dropped_wirings``).
from agentbundle.commands._drop_warning import enumerate_event_dropped_wirings


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
    from agentbundle.commands._common import (
        check_spec_version_gate,
        format_plan_line,
        plan_action,
        summarize_plan,
    )
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
    dry_run: bool = bool(getattr(args, "dry_run", False))
    cli_adapter: str | None = getattr(args, "adapter", None)
    # User-config attached by `cli.py:main()` via args._user_config.
    # Default to None for callers that construct an args namespace by
    # hand (tests) or for any code path that bypasses main(). The
    # pre-flight in `_resolve_target_adapter` no-ops when this is None,
    # so legacy callers see exactly today's behavior.
    user_config: "UserConfig | None" = getattr(args, "_user_config", None)
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

    # `--dry-run` is a read-only preview; `--force` performs destructive
    # cleanup (Step 3c's rmtree / orphan unlink / state rewrite). The two are
    # contradictory — refuse up front, before Step 3c can touch anything, so a
    # preview never runs that cleanup. Previewing *what --force would clean* is
    # a separate future feature.
    if dry_run and force:
        print(
            "install: --dry-run is incompatible with --force: --force performs "
            "destructive cleanup (removing leftover files, rewriting state) that "
            "a read-only preview must not do. Run --dry-run without --force to "
            "preview, or --force without --dry-run to apply.",
            file=sys.stderr,
        )
        return 1

    # RFC-0012 removes the user-scope-only `--adapter` binding —
    # `--adapter` is admitted at both scopes now. The handler-level
    # mutex with `--emit-install-routes` runs after `scope.resolve()`
    # so it consults the resolved scope (matches the existing
    # `force_merge` precedent below).
    #
    # Backward-compat for test fixtures: argparse always sets the
    # attribute (default False) so `hasattr` is the discriminator
    # between "real CLI invocation" (attribute present) and "test
    # fixture with a bare SimpleNamespace" (attribute absent). Test
    # fixtures that pre-date RFC-0012 *at repo scope* implicitly want
    # the legacy dist-tree shape; treating absent-attribute as the
    # "legacy dist-tree" value preserves their assertions while real
    # CLI calls without the flag flow through the new per-IDE
    # projection path. The fallback is scope-dependent because the
    # `emit_install_routes` flag is only meaningful at repo scope —
    # firing the user-scope binding refusal on every legacy test
    # fixture would be a false positive. Note: cli_scope is the raw
    # CLI flag here (Step 2's `requested_scope` resolution hasn't
    # run yet); user-scope tests pass `scope="user"` explicitly so
    # the discriminator is accurate.
    if hasattr(args, "emit_install_routes"):
        emit_install_routes: bool = bool(args.emit_install_routes)
    else:
        # Absent attribute → repo-scope legacy callers want dist-tree
        # shape; user-scope callers want the new path-jail.
        emit_install_routes = cli_scope != "user"

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

    # v0.2 introduced `[pack.install]`; v0.3 (RFC-0005) added
    # `user-scope-hooks`; v0.6 (RFC-0011) added `allowed-adapters`.
    # Mirror validate.py:_allowed_scopes — every version >= 0.2 carries
    # the install table. The v0.1 path stays gateless (legacy implied
    # `default-scope = "repo"`).
    _pack_version = pack_spec_version(pack_toml)
    if _pack_version is None or _pack_version == "0.1":
        pack_install = None
    else:
        pack_install = pack_toml.get("pack", {}).get("install")
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

    # RFC-0012 handler-level mutex (after Step 2 so requested_scope is
    # the resolved value, matching install.py:197's force_merge
    # precedent). The mutex consults `requested_scope`, not
    # `args.scope`, so a pack whose `[scope] default-scope = "user"`
    # surfaces the binding correctly when `--scope` is omitted.
    if requested_scope == "user" and emit_install_routes:
        print(
            "install: --emit-install-routes is bound to --scope repo",
            file=sys.stderr,
        )
        return 1
    if (
        requested_scope == "repo"
        and cli_adapter is not None
        and emit_install_routes
    ):
        print(
            "install: --adapter and --emit-install-routes are mutually "
            "exclusive at --scope repo",
            file=sys.stderr,
        )
        return 1

    # ── Step 3: Pre-flight — load state at *both* scopes ──────────────────────
    # Read-only loads (for_write=False) — we do the v0.1 refusal *only*
    # for scopes we're about to write to, after we know which they are.
    # Loading both is cheap and reveals the cross-scope conflict.
    repo_state_path = output_root / ".agentbundle-state.toml"
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
            user_state_path = user_root / ".agentbundle" / "state.toml"
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

    # ── Step 3c: RFC-0012 AC24 in-band detection (repo scope, per-IDE) ──
    # Pre-RFC-0012 state must surface migration messaging *before* the
    # already-installed branch fires its "use 'upgrade'" refusal —
    # otherwise an adopter with stale state would receive misleading
    # advice ("just upgrade") instead of the correct uninstall +
    # reinstall path. Detection is gated to ``--scope repo`` without
    # ``--emit-install-routes`` per spec AC24's narrowed-inference rule
    # (the legacy dist-tree producer must not trigger (b) on its own
    # output). The resolver is lifted here so the (a) trigger has a
    # ``repo_target_adapter`` to compare against ``state.adapter``; the
    # same values are reused downstream and the original computation
    # block below is now a no-op for this code path.
    _pack_allowed_adapters: list[str] | None = None
    if isinstance(pack_install, dict):
        _raw = pack_install.get("allowed-adapters")
        if isinstance(_raw, list):
            _pack_allowed_adapters = [s for s in _raw if isinstance(s, str)]
    _pack_contract_version = pack_spec_version(pack_toml)
    repo_target_adapter: str | None = None
    allowed_prefixes_repo: list[str] | None = None
    if requested_scope == "repo" and not emit_install_routes:
        try:
            repo_target_adapter = _resolve_target_adapter(
                pack_dir,
                scope="repo",
                adapter=cli_adapter,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=None,
                command_name="install",
                user_config=user_config,
            )
        except _AdapterResolutionRefused as exc:
            print(str(exc), file=sys.stderr)
            return 1
        allowed_prefixes_repo = _adapter_allowed_prefixes_repo(
            repo_target_adapter
        )
        # Issue #190: render the current per-IDE projection's relpaths so
        # orphan recovery can exclude paths Step 9 companion-protects.
        # Best-effort and deterministic (same inputs as the Step-7 render).
        # On FileNotFoundError/ValueError the orphan filter degrades to off
        # (None) and Step 7 re-renders to surface the canonical error; any
        # other render exception propagates here exactly as it did from
        # Step 7 before this change (no new swallowing).
        _orphan_filter_relpaths: "set[str] | None" = None
        try:
            _, _early_repo_projection = _render_for_repo_scope(
                pack_dir,
                adapter=cli_adapter,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=None,
                command_name="install",
                user_config=user_config,
            )
            _orphan_filter_relpaths = set(_early_repo_projection.keys())
        except (FileNotFoundError, ValueError):
            _orphan_filter_relpaths = None
        rc = _classify_pre_rfc0012_state(
            output_root=output_root,
            pack_name=pack_name,
            pack_dir=pack_dir,
            repo_state=repo_state,
            repo_target_adapter=repo_target_adapter,
            allowed_prefixes_repo=allowed_prefixes_repo,
            force=force,
            projection_relpaths=_orphan_filter_relpaths,
        )
        if rc is not None:
            return rc

    # ``installed_at_*`` is computed AFTER Step 3c because (b)+--force
    # drops the stale state row inside ``_classify_pre_rfc0012_state``
    # so the subsequent install proceeds as a clean reinstall. Computing
    # the flag before detection would cache pre-cleanup state and fire
    # the misleading "use 'upgrade' to change version" refusal at
    # Step 4 even after --force succeeded.
    installed_at_repo = pack_name in repo_state.packs
    installed_at_user = user_state is not None and pack_name in user_state.packs

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
    # RFC-0004; RFC-0005's T1 added one to Kiro too; RFC-0011 added
    # one to Codex; RFC-0012 added one to Copilot. Resolve which
    # adapter the user-scope install targets via the six-step (0–5)
    # lookup and use that adapter's `allowed-prefixes.user`.
    # ``_pack_allowed_adapters`` and ``_pack_contract_version`` were
    # lifted to Step 3c above so the AC24 detection block can resolve
    # the repo-target adapter early; reuse the same values here.
    # Only resolve the user-scope target adapter when user scope is in
    # this run's plan. Resolving unconditionally at scope="user" would
    # surface the user-scope-capability subcheck refusal (e.g.
    # `--adapter copilot` against a repo-only install) even though the
    # install would never write to user scope.
    user_target_adapter: str | None = None
    allowed_prefixes_user: list[str] | None = None
    if "user" in scopes_to_install:
        try:
            user_target_adapter = _resolve_target_adapter(
                pack_dir,
                scope="user",
                adapter=cli_adapter,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=None,  # First install has no prior state here.
                command_name="install",
                user_config=user_config,
            )
        except _AdapterResolutionRefused as exc:
            print(str(exc), file=sys.stderr)
            return 1
        allowed_prefixes_user = _adapter_allowed_prefixes_user(user_target_adapter)

    # RFC-0012 repo-scope per-IDE resolution: ``repo_target_adapter``
    # and ``allowed_prefixes_repo`` were lifted to Step 3c above so the
    # AC24 detection block (which covers the AC22 orphan-refusal path
    # as trigger (c)) can run before the already-installed branch.
    # No re-resolution here.

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
            # RFC-0012: at repo scope without --emit-install-routes,
            # thread the repo-adapter's `allowed-prefixes.repo` into
            # the plan so the path-jail fences each write under the
            # per-IDE directory (`<repo>/.kiro/`, `<repo>/.claude/`,
            # etc.). With --emit-install-routes the legacy dist-tree
            # producer runs and the prefix list stays None.
            plans.append(
                _ScopePlan(
                    scope="repo",
                    root=output_root,
                    state_path=repo_state_path,
                    allowed_prefixes=allowed_prefixes_repo,
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
                    user_root_resolved / ".agentbundle" / "state.toml", for_write=True
                )
            except ConfigError as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            plans.append(
                _ScopePlan(
                    scope="user",
                    root=user_root_resolved,
                    state_path=user_root_resolved / ".agentbundle" / "state.toml",
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

    # Dropped-primitives warning rail (docs/specs/dropped-primitives-
    # coverage T6 / AC10). Pre-write barrier: Step 5's plans are built
    # and both target adapters are resolved by here; Step 6's pre-flight
    # hasn't fired yet; no byte has been written. Emit one warning per
    # (root, pack_name, adapter, scope) where the resolved adapter has
    # any `dropped` mode for a primitive type the pack actually ships.
    # Contract-driven — no hardcoded adapter literals.
    #
    # Dual-scope late-resolution: `repo_target_adapter` is set at Step 3c
    # only when ``requested_scope == "repo"``. When ``requested_scope ==
    # "user"`` AND ``force + other_already`` (Step 4b's dual-scope path),
    # the run writes to repo too but Step 3c didn't resolve. Resolve here
    # so the warning fires for both scopes — without this, the
    # ``--scope user --force`` dual-scope path silently drops the repo-
    # side warning even though the install does land at repo scope.
    if "repo" in scopes_to_install and repo_target_adapter is None:
        try:
            repo_target_adapter = _resolve_target_adapter(
                pack_dir,
                scope="repo",
                adapter=cli_adapter,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=None,
                command_name="install",
                user_config=user_config,
            )
        except _AdapterResolutionRefused:
            # Repo resolution failed; defer the actual refusal to the
            # downstream render step which already raises with adopter-
            # facing wording. Silently skipping the warning is
            # acceptable in this corner because the install itself
            # will halt before any byte is written.
            repo_target_adapter = None

    for plan in plans:
        scope_adapter = (
            repo_target_adapter if plan.scope == "repo" else user_target_adapter
        )
        if scope_adapter is None:
            continue
        _maybe_emit_dropped_warning(
            root=plan.root,
            pack_dir=pack_dir,
            pack_name=pack_name,
            adapter=scope_adapter,
            scope=plan.scope,
        )

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
            if emit_install_routes:
                # Legacy dist-tree producer (RFC-0012 § *CLI surface*'s
                # catalogue-publishing opt-in).
                repo_projection = render_pack(pack_dir)
            else:
                # RFC-0012 default: per-IDE projection at repo scope.
                # `_render_for_repo_scope` returns (adapter, projection);
                # we already resolved the adapter above for the
                # path-jail prefix list, but the helper re-resolves so
                # the caller gets a paired return.
                _resolved_adapter, repo_projection = _render_for_repo_scope(
                    pack_dir,
                    adapter=cli_adapter,
                    allowed_adapters=_pack_allowed_adapters,
                    contract_version=_pack_contract_version,
                    state_adapter=None,
                    command_name="install",
                    user_config=user_config,
                )
        if any(p.scope == "user" for p in plans):
            user_projection = _render_for_user_scope(
                pack_dir,
                adapter=cli_adapter,
                allowed_adapters=_pack_allowed_adapters,
                contract_version=_pack_contract_version,
                state_adapter=None,
                command_name="install",
                user_config=user_config,
            )
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
            if user_target_adapter == "copilot":
                # Copilot's whole prefix diverges at user scope
                # (`.github/…`→`.copilot/…`) for every primitive — not just
                # hooks — so this runs unconditionally for copilot, before
                # the path-jail probe below (RFC-0024 / copilot-full-parity).
                user_projection = _rewrite_copilot_user_scope_paths(
                    user_projection
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
            # Per-prefix probe fires whenever the plan has an
            # allowed_prefixes list (user scope always; repo scope when
            # the per-IDE path is in use — RFC-0012). With
            # `allowed_prefixes=None` the probe is skipped (legacy
            # dist-tree producer at repo scope under
            # --emit-install-routes).
            if plan.allowed_prefixes is not None:
                target_relpath = target.resolve().relative_to(plan.root.resolve()).as_posix()
                prefixes = plan.allowed_prefixes or []
                # Directory-boundary matching only — see safety.py.
                if not any(target_relpath.startswith(p) for p in prefixes):
                    print(
                        f"install: refusing to write outside allowed prefixes "
                        f"for scope {plan.scope!r}: {target.resolve()}",
                        file=sys.stderr,
                    )
                    return 1

    # ── Dry-run: all read-only pre-flight passed — preview and stop ───────────
    # At the top of Step 9 (after Step 8's path-jail probe) so every pre-flight
    # refusal in Steps 1–8 has already returned the real run's exit code (AC5).
    # Classify each plan's projection with the SAME `_classify_for_install` the
    # write loop below uses, print the per-file plan to stdout, and return
    # before any write — skipping the rest of Step 9 and Steps 10–13 (file
    # writes, seed delivery, state, install marker, chained adapt, `installed:`
    # recap). `--force` is refused up front, so there is exactly one writing
    # plan here (dual-scope writes arise only under --force).
    if dry_run:
        actions: list[str] = []
        for plan in plans:
            if plan.already_installed:
                continue
            projection = repo_projection if plan.scope == "repo" else user_projection
            if projection is None:
                continue
            for relpath, content in sorted(projection.items()):
                tier = _classify_for_install(
                    relpath, plan.root, content, plan.state, pack_name=pack_name,
                )
                action = plan_action(tier, on_disk=(plan.root / relpath).exists())
                companion = (
                    safety.companion_path(Path(relpath)).as_posix()
                    if tier is safety.Tier.TIER_2
                    else None
                )
                print(format_plan_line(action, tier.value, relpath, companion))
                actions.append(action)
        print(summarize_plan(actions))
        return 0

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

        # ── User-scope `.agentbundle/{lib,bin}/` delivery rail ────────────
        # (credbroker-user-scope T4) The vendored `credbroker` floor
        # (`.apm/user-libs/**` → `~/.agentbundle/lib/`) and the
        # `adapter-root-bins/*.py` + AC22b companion shim
        # (`~/.agentbundle/bin/`) are build-pipeline-only primitives with no
        # per-adapter projection rule, so the Step-7 render never emits them;
        # this is the install-time half of the same `.agentbundle/` rail the
        # build pipeline projects at self-host scope. Fenced by the user
        # adapter's `allowed-prefixes.user` (every one includes
        # `.agentbundle/`), so `write_jailed` admits the writes without a jail
        # change. Pure file projection — no pip, no credential value touched
        # (RFC-0006 no-leak). Skipped at repo scope (the floor is a user-scope
        # `sys.path` fallback; repo consumers run from the monorepo).
        if plan.scope == "user":
            try:
                floor_refusal = _deliver_user_scope_floor(
                    pack_dir=pack_dir,
                    root=plan.root,
                    allowed_prefixes=plan.allowed_prefixes,
                )
            except (OSError, safety.PathJailError) as exc:
                print(f"install: {exc}", file=sys.stderr)
                return 1
            if floor_refusal is not None:
                print(f"install: {floor_refusal}", file=sys.stderr)
                return 1

        # Deliver the pack's seeds (governance docs: AGENTS.md, docs/CHARTER.md,
        # …) into the repo at repo scope. Seeds land at the repo root / docs/,
        # outside the adapter projection prefixes, so they never interact with
        # the orphan scan. Tier-1/2/3 + composition-fragment handling is shared
        # with `scaffold` via `deliver_seeds`; here we also record each delivered
        # seed in state so upgrades give edited seeds Tier-2 companion safety.
        # (RFC-0001 §281-284 / file-safety contract.)
        if plan.scope == "repo":
            seeds_dir = pack_dir / "seeds"
            if seeds_dir.is_dir():
                from agentbundle.commands._common import deliver_seeds

                try:
                    seed_deliveries = deliver_seeds(seeds_dir, plan.root)
                except safety.PathJailError as exc:
                    print(f"install: {exc}", file=sys.stderr)
                    return 1
                for rec in seed_deliveries:
                    new_pack_state.files[rec.relpath] = {
                        "sha": safety.sha256_bytes(rec.content),
                        "from-pack-version": pack_version,
                    }
                    if rec.companion_relpath is not None:
                        plan.new_companions.append(rec.companion_relpath)
                # Observability: tell the operator that seeds landed and,
                # crucially, when an edited file was preserved as a companion
                # rather than overwritten (the silent-companion diagnosability
                # gap on a brownfield install). stderr so the stdout
                # `installed:` rail stays parseable.
                if seed_deliveries:
                    _n_companion = sum(
                        1 for r in seed_deliveries if r.action == "companion"
                    )
                    _summary = (
                        f"install: delivered {len(seed_deliveries)} seed(s) "
                        f"for pack {pack_name}"
                    )
                    if _n_companion:
                        _summary += (
                            f"; {_n_companion} collided with your edits and "
                            f"were kept as *.upstream.<ext> companions"
                        )
                    print(_summary, file=sys.stderr)

        # RFC-0005 T8b — user-scope hook-wiring merge phase.
        # Runs after file writes (so hook bodies exist where wiring
        # entries reference them via $HOOK_BODY_PATH-style placeholders;
        # T8b's resolver-time substitution is the consumer's concern).
        # Captures (event, id[, target-file]) tuples and writes them
        # to ``hook_wiring_owned`` on the PackState so uninstall can
        # be precise.
        if plan.scope == "user":
            # AC10a — record the resolved adapter unconditionally for
            # every user-scope install (lifted out of the kiro-hook-only
            # branch below). Without this, codex / non-hook claude-code
            # installs silently default the state field, breaking AC25's
            # state-shape assertions and the upgrade-side state-hint
            # short-circuit (AC10b) on subsequent upgrades.
            new_pack_state.adapter = user_target_adapter

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

                # The merge phase re-wrote the agent JSON (Kiro) with
                # the hook entries we just merged in. Refresh the
                # state.files SHA so uninstall's Tier-1 check still
                # passes — see ``_refresh_merge_target_shas``.
                _refresh_merge_target_shas(
                    pack_state=new_pack_state,
                    owned_rows=owned_rows,
                    root=plan.root,
                )
        elif plan.scope == "repo" and repo_target_adapter is not None:
            # RFC-0012: record the resolved adapter on every repo-scope
            # per-IDE install. State-hint short-circuit at upgrade time
            # (AC10b parity at repo scope) depends on this. Skipped
            # when `--emit-install-routes` is set — the legacy dist-tree
            # producer has no single adapter to pin.
            new_pack_state.adapter = repo_target_adapter

        plan.state.packs[pack_name] = new_pack_state
        # Stamp the post-write schema. Always emit the current
        # ``STATE_SCHEMA_VERSION`` (bumped to v0.3 in T8a) so a fresh
        # install never produces a state file pinned at a stale version.
        from agentbundle.config import STATE_SCHEMA_VERSION

        plan.state.schema_version = STATE_SCHEMA_VERSION
        serialised = dump_state(plan.state)
        # State file is CLI-owned metadata, not pack-projected content.
        # At repo scope the path is `<root>/.agentbundle-state.toml` —
        # a top-level file that wouldn't match any `.agentbundle/`-style
        # prefix. Skip the prefix check (the jail-under-root check still
        # fires) so the state-write isn't blocked by RFC-0012's
        # per-IDE prefix list. At user scope the state file is under
        # `~/.agentbundle/state.toml` which already matches the prefix.
        state_relpath = str(plan.state_path.relative_to(plan.root))
        state_prefixes = plan.allowed_prefixes
        if plan.scope == "repo" and state_relpath == ".agentbundle-state.toml":
            state_prefixes = None
        try:
            safety.write_jailed(
                plan.root,
                state_relpath,
                serialised,
                scope=plan.scope,
                allowed_prefixes=state_prefixes,
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
    # RFC-0011 extends user-scope output with ` via <adapter>` and an
    # optional ` (other declared adapters: …; use --adapter to override)`
    # suffix when multiple CLI homes match the pack's allowed-adapters.
    # RFC-0012 extends repo-scope output with the same `via <adapter>`
    # shape for per-IDE projection; the `--emit-install-routes` path
    # emits an `emitted install routes for ...` line instead (no
    # single adapter to pin). AC21: repo scope carries no "other
    # declared adapters" suffix (no probe runs).
    for plan in plans:
        if plan.scope == "user":
            line = f"installed: {pack_name} @ user via {user_target_adapter}"
            if cli_adapter is None and _pack_allowed_adapters:
                probes = _user_scope_adapter_probes()
                home = Path.home()
                populated_others = [
                    a
                    for a in _pack_allowed_adapters
                    if a != user_target_adapter
                    and a in probes
                    and probes[a](home)
                ]
                if populated_others:
                    line += (
                        f"  (other declared adapters: "
                        f"{', '.join(populated_others)}; "
                        f"use --adapter to override)"
                    )
            print(line)
        elif plan.scope == "repo" and emit_install_routes:
            # Dist-tree shape — the two per-pack-emitting recipes
            # produce `<repo>/claude-plugins/<pack>/` and
            # `<repo>/apm/<pack>/`. The `marketplace` recipe doesn't
            # produce a per-pack directory and is excluded from the
            # route list per RFC-0012 § *Install-time message rail
            # (repo scope)*.
            routes = [
                f"{output_root}/claude-plugins/{pack_name}/",
                f"{output_root}/apm/{pack_name}/",
            ]
            # Emit both the new route-list summary AND the legacy
            # plain-text line. Order: route-list first (the new info)
            # so adopters reading the tail see the existing
            # ``installed: <pack> @ repo`` recap last — preserves the
            # invariant every pre-RFC-0012 integration test asserts
            # against (last non-empty stdout line is the install
            # recap).
            print(
                f"emitted install routes for {pack_name} at "
                f"{_format_route_list(routes)}"
            )
            print(f"installed: {pack_name} @ repo")
        elif plan.scope == "repo" and repo_target_adapter is not None:
            # RFC-0012 per-IDE projection at repo scope.
            print(
                f"installed: {pack_name} @ repo via {repo_target_adapter}"
            )
        else:
            # Defensive fallback: matches pre-RFC-0012 wording for any
            # path the new branches don't capture.
            print(f"installed: {pack_name} @ {plan.scope}")

    return 0


# ---------------------------------------------------------------------------
# User-scope `.agentbundle/{lib,bin}/` delivery rail (credbroker-user-scope T4)
# ---------------------------------------------------------------------------

# Subtrees never delivered into the floor: bytecode caches and any in-package
# test tree. Mirrors ``build.user_libs.EXCLUDED_DIR_NAMES`` so importing the
# pack copy (which writes ``__pycache__/``) can't smuggle stale bytecode into
# ``~/.agentbundle/lib/``.
_USER_LIBS_EXCLUDED_DIR_NAMES = frozenset({"__pycache__", "tests"})


def _assert_user_floor_dirs_safe(root: Path) -> str | None:
    """POSIX guard: refuse delivery into a group/world-writable floor.

    The vendored floor under ``~/.agentbundle/lib`` is appended to
    ``sys.path`` at lowest precedence by every credentialed consumer
    bootstrap (credbroker-user-scope T1), and ``~/.agentbundle/bin`` carries
    executable broker scripts. A group/other-writable artifact dir is
    therefore a local code-execution vector — another account could drop a
    malicious ``credbroker/__init__.py`` or ``sso-broker.py`` that a consumer
    then imports/runs. Delivery owns the floor's integrity (T1's bootstrap
    relies on it), so refuse *before* writing if any existing artifact dir —
    ``.agentbundle`` itself, ``lib/``/``bin/``, **and every leaf already under
    them** (e.g. a pre-existing ``lib/credbroker/``) — carries a loose mode.
    Walking the whole tree, not three fixed dirs, closes the
    loose-leaf-passes-the-check gap; :func:`_harden_floor_dir_modes` only
    repairs modes *after* a successful write.

    Returns a refusal string, or ``None`` when safe. No-op on Windows: the
    POSIX mode bits don't model the DACL the floor inherits from
    ``%USERPROFILE%`` there.

    TOCTOU: this is a check-then-write guard, so it assumes a single-user
    ``$HOME`` (the floor's trust boundary). A world-loose ``$HOME`` shared
    with a hostile local account can still race the window between this check
    and the write — out of scope for the file-projection threat model.
    """
    if os.name != "posix":
        return None
    base = root / ".agentbundle"
    candidates: list[Path] = [base]
    for sub in (base / "lib", base / "bin"):
        if sub.is_dir():
            for dirpath, _dirnames, _filenames in os.walk(sub):
                candidates.append(Path(dirpath))
    for d in candidates:
        if d.is_dir():
            mode = os.stat(d).st_mode & 0o777
            if mode & 0o022:
                return (
                    f"refusing user-scope delivery: {d} is group/world-writable "
                    f"(mode {mode:#o}); a writable floor is a local "
                    f"code-execution vector — run 'chmod go-w' on it and retry"
                )
    return None


def _harden_floor_dir_modes(root: Path) -> None:
    """Strip group/world *write* bits from the delivered floor dirs (POSIX).

    ``write_jailed`` creates parent directories under the process umask; a
    permissive umask (``002``/``000``) would otherwise leave
    ``~/.agentbundle/{lib,bin}`` and their subdirs group/world-writable —
    re-opening the code-execution vector :func:`_assert_user_floor_dirs_safe`
    refuses on entry. Delivered *files* are already restrictive (``mkstemp``
    creates ``0o600``; ``bin/`` is explicitly ``0o755``), so only directory
    modes need hardening. No-op on Windows (DACL model).
    """
    if os.name != "posix":
        return
    base = root / ".agentbundle"
    for d in (base, base / "lib", base / "bin"):
        if not d.is_dir():
            continue
        for dirpath, _dirnames, _filenames in os.walk(d):
            cur = os.stat(dirpath).st_mode & 0o777
            if cur & 0o022:
                os.chmod(dirpath, cur & ~0o022)


def _deliver_user_scope_floor(
    *,
    pack_dir: Path,
    root: Path,
    allowed_prefixes: list[str] | None,
) -> str | None:
    """Deliver the user-scope ``.agentbundle/{lib,bin}/`` rail for one pack.

    Two halves, both written through ``safety.write_jailed`` under the
    user-scope path-jail (the target stays under ``.agentbundle/``, which
    every user-scope adapter's ``allowed-prefixes.user`` already permits):

    - **lib/** — the pack's ``.apm/user-libs/**`` vendored floor (e.g.
      ``credbroker/``) → ``~/.agentbundle/lib/**``. Importable Python, written
      with **default** mode (no exec bit). The consumer bootstraps append
      ``~/.agentbundle/lib`` to ``sys.path`` at lowest precedence (T1), so a
      no-repo user-scope install regains Tier-2/3 credential resolution.
    - **bin/** — the pack's ``.apm/adapter-root-bins/*.py`` plus the AC22b
      companion ``credentials_shim.py`` (ship-both) → ``~/.agentbundle/bin/``
      with POSIX ``0o755`` (Windows inherits the parent DACL). Closes the
      long-missing user-scope half of the RFC-0013 ``sso-broker`` delivery.

    These are *shared, idempotent* floor artifacts — one copy serving every
    credentialed consumer — not pack-private projected files, so they are
    delivered on every fresh user-scope install and deliberately **not**
    recorded in the pack's ``state.files``: uninstalling one pack must not
    strip a co-installed pack's floor.

    Returns a refusal string when the floor-safety guard fails (the caller
    aborts the install), or ``None`` on success / when the pack ships no
    floor content (then this is a no-op — a pack that writes nothing to the
    floor never triggers the group/world-writable refusal).
    """
    from agentbundle import safety
    from agentbundle.build import adapter_root_bins

    bin_sources = adapter_root_bins.collect_pack_root_bins(pack_dir)
    lib_src_root = pack_dir / ".apm" / "user-libs"
    # Reject a symlinked primitive dir itself (os.walk(top=symlink) enumerates
    # the link target's real files, which the per-entry is_symlink() skip below
    # would not catch) — see collect_pack_root_bins for the bin/ twin.
    has_lib = lib_src_root.is_dir() and not lib_src_root.is_symlink()
    if not bin_sources and not has_lib:
        # No floor content in this pack — nothing to deliver, and no reason to
        # gate the install on the floor dirs' modes.
        return None

    floor_refusal = _assert_user_floor_dirs_safe(root)
    if floor_refusal is not None:
        return floor_refusal

    # bin/ half — companion-aware, single-pack enumeration. 0o755 on POSIX.
    bin_mode = adapter_root_bins.EXECUTABLE_MODE if os.name == "posix" else None
    for basename, src in sorted(bin_sources.items()):
        relpath = (adapter_root_bins.TARGET_SUBDIR / basename).as_posix()
        safety.write_jailed(
            root,
            relpath,
            src.read_bytes(),
            mode=bin_mode,
            scope="user",
            allowed_prefixes=allowed_prefixes,
        )

    # lib/ half — the vendored floor, written default-mode (importable Python,
    # no exec bit). Walk the pack's whole .apm/user-libs/** tree with
    # followlinks=False and skip file symlinks: a crafted pack must not read an
    # out-of-tree file (e.g. /etc/passwd) into the floor via a symlink (the
    # write target can't escape the jail, but the *content* would). Matches the
    # repo's os.walk(followlinks=False) convention for pack-content walks.
    if has_lib:
        for dirpath, dirnames, filenames in os.walk(lib_src_root, followlinks=False):
            # Prune excluded subtrees in place (don't recurse into caches) and
            # keep the walk deterministic.
            dirnames[:] = sorted(
                d for d in dirnames if d not in _USER_LIBS_EXCLUDED_DIR_NAMES
            )
            for fname in sorted(filenames):
                src = Path(dirpath) / fname
                if src.is_symlink():
                    continue
                rel = src.relative_to(lib_src_root)
                relpath = (Path(".agentbundle") / "lib" / rel).as_posix()
                safety.write_jailed(
                    root,
                    relpath,
                    src.read_bytes(),
                    scope="user",
                    allowed_prefixes=allowed_prefixes,
                )

    _harden_floor_dir_modes(root)
    return None


_INBAND_DETECTION_SEEN: set[tuple[str, str]] = set()
"""RFC-0012 AC24 once-per-``(root, pack_name)`` short-circuit.

Process-scoped mutable state. The detection block consults this set; an
entry means "we already emitted a migration line for this (root, pack) in
this process and any further ``install`` invocation should stay silent."
Production ``agentbundle`` CLI invocations are short-lived processes so
the set resets naturally; long-running embedders (an MCP shim that loops
``install.run`` calls, a test harness) MUST reset via
:func:`_clear_inband_detection_seen` between logical sessions or detection
will silently skip on the second call."""


def _clear_inband_detection_seen() -> None:
    """Reset the once-per-session detection set.

    Public-by-convention (single leading underscore) helper for callers
    that need to bypass the once-per-process short-circuit — tests, and
    any long-running embedder restarting an install loop. Prefer this
    over reaching into :data:`_INBAND_DETECTION_SEEN` directly so the
    storage shape can change without breaking callers.
    """
    _INBAND_DETECTION_SEEN.clear()


# ---------------------------------------------------------------------------
# Dropped-primitives warning rail (docs/specs/dropped-primitives-coverage T6)
# ---------------------------------------------------------------------------


_DROPPED_WARNING_SEEN: set[tuple[str, str, str, str]] = set()
"""Once-per-``(root, pack_name, adapter, scope)`` short-circuit for the
dropped-primitives warning rail (spec AC11).

The 4-tuple key's `scope` component is load-bearing: dual-scope installs
fire one warning per scope where the resolved adapter has dropped modes,
each silenceable independently on repeat. See spec AC10/AC11 for the
dual-scope contract."""


def _clear_dropped_warning_seen() -> None:
    """Reset the once-per-session dropped-warning set.

    Public-by-convention helper for tests + long-running embedders;
    mirrors :func:`_clear_inband_detection_seen` (PR #141 precedent).
    """
    _DROPPED_WARNING_SEEN.clear()


def _enumerate_dropped_primitives(
    pack_dir: Path,
    adapter: str,
    contract: dict | None = None,
) -> dict[str, int]:
    """Return ``{primitive-type-name: count}`` for primitives the pack
    ships AND the adapter projects with ``mode = "dropped"``.

    Counts come from ``<pack_dir>/.apm/<source-dir>/`` (where
    ``<source-dir>`` is the contract's ``primitive.<type>.source-path``
    last segment — e.g., ``hook-body`` → ``hooks/``). Each entry counts
    as one primitive only if it matches the type's expected shape
    (skills/agents/commands are directories or .md files; hook-wiring is
    .toml; hook-body is any file). Junk files (``.DS_Store``, editor
    swap files) and stray directories don't inflate the count. Empty
    mapping when:

      - The adapter has no ``dropped`` entries at all (e.g. claude-code).
      - The pack ships nothing under any of the adapter's dropped types.
    """
    if contract is None:
        import tomllib as _tomllib
        from agentbundle.build.main import _read_bundled

        contract = _tomllib.loads(_read_bundled("adapter.toml"))

    primitives = contract.get("primitive", {})
    adapter_entries = contract.get("adapter", {}).get(adapter, {}).get("projection", [])
    out: dict[str, int] = {}
    for entry in adapter_entries:
        if entry.get("mode") != "dropped":
            continue
        ptype = entry.get("primitive")
        if not ptype:
            continue
        source_path = primitives.get(ptype, {}).get("source-path", "")
        source_dir = pack_dir / source_path.strip("/")
        if not source_dir.exists():
            continue
        count = _count_primitive_entries(source_dir, ptype)
        if count > 0:
            out[ptype] = count
    return out


_JUNK_NAMES = {"Thumbs.db", "desktop.ini"}
"""Cross-platform editor / OS artifacts that aren't pack content.
Leading-dot files (``.DS_Store``, editor swaps) are caught by the
dotfile skip; these are the named exceptions that don't start with a
dot but still aren't primitives."""


def _is_junk_name(name: str) -> bool:
    """Return True for entries that aren't pack content regardless of type."""
    if name.startswith("."):
        return True
    if name in _JUNK_NAMES:
        return True
    # Editor swap / backup suffixes.
    if name.endswith(("~", ".swp", ".bak")):
        return True
    return False


def _count_primitive_entries(source_dir: Path, ptype: str) -> int:
    """Count entries in ``source_dir`` that match ``ptype``'s shape.

    Per the bundled contract's primitive layout:
      - ``skill``: subdirectories (each a skill bundle with SKILL.md).
      - ``agent``, ``command``: ``.md`` files.
      - ``hook-body``: ``.sh`` or ``.py`` files (the two shapes the
        contract's adapters project via direct-file today; a future
        primitive shape extends this set explicitly).
      - ``hook-wiring``: ``.toml`` files.

    Junk entries (``.DS_Store``, ``Thumbs.db``, ``desktop.ini``, editor
    swap/backup files, stray subdirs) are skipped — they would
    otherwise inflate the warning rail's count.
    """
    count = 0
    for entry in source_dir.iterdir():
        if _is_junk_name(entry.name):
            continue
        if ptype == "skill":
            if entry.is_dir():
                count += 1
        elif ptype in ("agent", "command"):
            if entry.is_file() and entry.suffix == ".md":
                count += 1
        elif ptype == "hook-wiring":
            if entry.is_file() and entry.suffix == ".toml":
                count += 1
        elif ptype == "hook-body":
            if entry.is_file() and entry.suffix in (".sh", ".py"):
                count += 1
        else:
            # Unknown primitive type — admit conservatively but only
            # files (not stray subdirs) so a future contract addition
            # is surfaced rather than silently filtered.
            if entry.is_file():
                count += 1
    return count


def _enumerate_compatible_primitives(
    pack_dir: Path,
    adapter: str,
    contract: dict | None = None,
) -> list[str]:
    """Return primitive-type names where ``mode != "dropped"`` AND the
    pack ships at least one file. Order matches the adapter's projection
    declaration order for stable output."""
    if contract is None:
        import tomllib as _tomllib
        from agentbundle.build.main import _read_bundled

        contract = _tomllib.loads(_read_bundled("adapter.toml"))

    primitives = contract.get("primitive", {})
    adapter_entries = contract.get("adapter", {}).get(adapter, {}).get("projection", [])
    out: list[str] = []
    for entry in adapter_entries:
        if entry.get("mode") == "dropped":
            continue
        ptype = entry.get("primitive")
        if not ptype:
            continue
        source_path = primitives.get(ptype, {}).get("source-path", "")
        source_dir = pack_dir / source_path.strip("/")
        if not source_dir.exists():
            continue
        if _count_primitive_entries(source_dir, ptype) > 0:
            out.append(ptype)
    return out


def _format_dropped_warning(
    pack_name: str,
    adapter: str,
    dropped_counts: dict[str, int],
    compatible_types: list[str],
) -> str:
    """Backward-compat shim — delegates to the shared formatter.

    Thin positional-argument wrapper around
    :func:`agentbundle.commands._drop_warning.format_drop_message` so
    existing callers (tests + ``_maybe_emit_dropped_warning``) keep
    working without modification. T4 of spec incompatible-hook-event-drop
    moved the canonical implementation to ``_drop_warning.py``; this
    shim lives here for backward compat.

    Raises:
        ValueError: when ``dropped_counts`` has no nonzero entries (same
            contract as the pre-move implementation).
    """
    from agentbundle.commands._drop_warning import format_drop_message

    return format_drop_message(
        pack_name=pack_name,
        adapter=adapter,
        dropped_counts=dropped_counts,
        compatible_types=compatible_types,
    )


def _maybe_emit_dropped_warning(
    *,
    root: Path,
    pack_dir: Path,
    pack_name: str,
    adapter: str,
    scope: str,
) -> None:
    """If the pack ships any primitive type the adapter drops, or any
    hook-wiring file uses an event the adapter doesn't support, emit the
    warning to stderr. Short-circuits once per
    ``(root, pack_name, adapter, scope)`` per process so repeat calls
    in the same process stay silent (AC11).

    Covers both the coarse-grained primitive-type drop rail
    (``_enumerate_dropped_primitives``) and the per-file event-level
    drop rail (``enumerate_event_dropped_wirings``). The short-circuit
    key is unchanged — both drop kinds derive from the same inputs, so
    one warning per scope per process covers both (spec AC9).

    Pre-write barrier: callers invoke this after Step 5's plans-list is
    built (both target adapters resolved) and before Step 6's pre-flight
    rails fire / Step 9's writes execute.
    """
    from agentbundle.commands._drop_warning import format_drop_message

    key = (str(root), pack_name, adapter, scope)
    if key in _DROPPED_WARNING_SEEN:
        return

    # Load the contract once for both enumerators so we don't hit disk twice.
    import tomllib as _tomllib
    from agentbundle.build.main import _read_bundled
    contract = _tomllib.loads(_read_bundled("adapter.toml"))

    dropped = _enumerate_dropped_primitives(pack_dir, adapter, contract)
    event_drops = enumerate_event_dropped_wirings(pack_dir, adapter, contract)

    if not dropped and not event_drops:
        # Adapter has no dropped modes OR pack ships nothing droppable.
        # Record the no-op so even a "no warning" decision is short-circuited
        # — a future caller flipping the pack's primitives wouldn't expect
        # a sudden warning mid-process.
        _DROPPED_WARNING_SEEN.add(key)
        return
    compatible = _enumerate_compatible_primitives(pack_dir, adapter, contract)
    msg = format_drop_message(
        pack_name=pack_name,
        adapter=adapter,
        dropped_counts=dropped,
        compatible_types=compatible,
        event_drops=event_drops,
        mode="install_warning",
    )
    print(msg, file=sys.stderr)
    _DROPPED_WARNING_SEEN.add(key)


def _scan_dist_tree_artifacts(root: Path, pack_name: str) -> list[Path]:
    """Return pre-RFC-0012 dist-tree projection files for ``pack_name``.

    Scans ``<root>/claude-plugins/<pack>/`` and ``<root>/apm/<pack>/`` —
    the two per-pack subtrees the legacy ``per-pack-claude-plugin`` and
    ``per-pack-apm-package`` recipes produce. Other top-level
    directories (``.claude/`` etc.) belong to AC24 trigger (c)'s
    ``safety.scan_for_pack_artifacts`` scan, not this one.
    """
    out: list[Path] = []
    for top in ("claude-plugins", "apm"):
        base = root / top / pack_name
        if not base.exists():
            continue
        for entry in base.rglob("*"):
            if entry.is_file():
                out.append(entry)
    return sorted(out)


def _classify_pre_rfc0012_state(
    *,
    output_root: Path,
    pack_name: str,
    pack_dir: Path,
    repo_state: "State",
    repo_target_adapter: str,
    allowed_prefixes_repo: list[str],
    force: bool,
    projection_relpaths: "set[str] | None" = None,
) -> int | None:
    """RFC-0012 AC24: in-band detection of pre-RFC-0012 state.

    Triggers evaluated per-pack in precedence ``(b) → (a) → (c)``; only
    the first match emits. Detection runs once per
    ``(output_root, pack_name)`` per process; subsequent calls
    short-circuit to silence.

    Returns:
      - ``None`` — no trigger fired, or ``--force`` cleared the
        trigger's on-disk shape; caller proceeds with the install.
      - ``1`` — refused with pinned stderr; caller returns 1.
    """
    from agentbundle import safety

    key = (str(output_root), pack_name)
    if key in _INBAND_DETECTION_SEEN:
        return None

    state_row = repo_state.packs.get(pack_name)

    # (b) Shape-mismatch — state row exists AND dist-tree files exist.
    # Pre-RFC-0012 signal per spec AC24: state.toml carries a row AND
    # the on-disk shape is the legacy dist-tree (post-RFC-0012 the only
    # code path producing those files is ``--emit-install-routes``,
    # which short-circuits before this detection runs).
    if state_row is not None:
        dist_tree = _scan_dist_tree_artifacts(output_root, pack_name)
        if dist_tree:
            _INBAND_DETECTION_SEEN.add(key)
            if force:
                # AC25(vi): --force is the corrective action for (b)'s
                # cross-invocation false positive — clean the dist-tree
                # files AND drop the stale state row so the install
                # proceeds as a clean reinstall. Without the row drop
                # Step 4 would refuse with "use 'upgrade'", trapping the
                # adopter in a loop (upgrade at repo scope re-emits the
                # dist-tree shape today). The caller re-computes
                # ``installed_at_repo`` after this helper returns; the
                # on-disk state.toml is rewritten here too because the
                # per-scope plan loop reloads state from disk at
                # ``install.py:519`` (``load_state(for_write=True)``) and
                # an in-memory-only pop would silently resurrect.
                import shutil

                from agentbundle.config import dump_state

                for top in ("claude-plugins", "apm"):
                    subtree = output_root / top / pack_name
                    if subtree.exists():
                        try:
                            shutil.rmtree(subtree)
                        except OSError:
                            pass
                repo_state.packs.pop(pack_name, None)
                state_path = output_root / ".agentbundle-state.toml"
                if state_path.exists():
                    # Direct write (not ``safety.write_jailed``) because
                    # the path *is* the jail anchor plus a fixed top-
                    # level filename; the durability guarantee comes from
                    # the post-install atomic rewrite at line ~809 a few
                    # hundred milliseconds later. If detection is ever
                    # lifted into a standalone verb, route through
                    # ``safety.write_jailed`` for atomicity.
                    state_path.write_text(
                        dump_state(repo_state), encoding="utf-8"
                    )
                return None
            print(
                f"install: pre-RFC-0012 dist-tree files for pack "
                f"{pack_name} at "
                f"{_format_route_list([str(p) for p in dist_tree])} — "
                f"state recorded but on-disk shape predates per-IDE "
                f"projection; rerun with --force to clean and reinstall, "
                f"or delete the listed paths and rerun",
                file=sys.stderr,
            )
            return 1

        # (a) Adapter disagreement — state row exists, no dist-tree
        # files (so (b) didn't fire), AND resolver's pick disagrees
        # with the recorded adapter. AC25(iii): the corrective action
        # is uninstall + reinstall; ``--force`` does NOT clear this.
        # ``state_row.adapter`` is always a non-empty string per
        # ``load_state`` (defaults to "claude-code" at read time for
        # absent / non-string values); no coercion needed.
        recorded_adapter = state_row.adapter
        if recorded_adapter != repo_target_adapter:
            _INBAND_DETECTION_SEEN.add(key)
            print(
                f"install: state records adapter "
                f"{recorded_adapter!r} for pack {pack_name}, but "
                f"resolver picked {repo_target_adapter!r} — uninstall "
                f"the pack at repo scope and reinstall to reconcile "
                f"(cross-adapter install is not supported)",
                file=sys.stderr,
            )
            return 1
    else:
        # (c) Orphan recovery — no state row AND per-IDE artifacts
        # exist under the resolved adapter's allowed-prefixes.repo.
        # The scan is **per-pack scoped** via ``pack_dir`` +
        # ``pack_name`` so a third pack's orphan files (left under the
        # same adapter prefix by a different crashed install) don't
        # surface here as a false positive — the cross-pack residual
        # ROADMAP named after PR #141.
        orphans = safety.scan_for_pack_artifacts(
            output_root, allowed_prefixes_repo,
            pack_dir=pack_dir, pack_name=pack_name,
        )
        # Canonicalise relpaths (NFC + ``os.path.normcase``) before any
        # membership test so a case-insensitive filesystem (Windows NTFS,
        # HFS+) or one that returns paths in a different Unicode normal
        # form (macOS NFD ↔ NFC) doesn't fail-open. Shared by the
        # issue-#190 projection filter and the foreign-owned filter below;
        # both compare on-disk orphan paths against an authored relpath set.
        import os as _os
        import unicodedata as _unicodedata

        def _canon_relpath(rel: str) -> str:
            return _unicodedata.normalize("NFC", _os.path.normcase(rel))

        # Issue #190: a file the *current* projection ships is not an
        # interrupted-install orphan — it is a path Step 9 companion-
        # protects (adopter edit → ``*.upstream.<ext>``; identical →
        # clean Tier-1). Drop those from the orphan set so a first
        # install over hand-authored primitives proceeds to Step 9
        # instead of refusing. What remains is the genuine residual:
        # files under a still-shipped primitive's dir that the current
        # projection no longer includes (a stale crumb from an older or
        # interrupted install — or an adopter file the scanner's
        # primitive-name heuristic happened to match). Canonicalise both
        # sides so the comparison can't fail-open and leave a projected
        # path in the unlink set on a case-folding / NFD filesystem.
        if orphans and projection_relpaths is not None:
            _canon_projection = {_canon_relpath(r) for r in projection_relpaths}
            orphans = [
                p for p in orphans
                if _canon_relpath(p.relative_to(output_root).as_posix())
                not in _canon_projection
            ]
        # The scanner's primitive-name heuristic is best-effort scoping,
        # not authoritative ownership. When two packs ship primitives
        # whose names collide (segment-match or stem-match), the
        # scanner mis-attributes the foreign pack's file as an orphan
        # of the installing pack — and the --force branch below would
        # unlink another state-tracked pack's file. ``state.toml`` IS
        # authoritative: filter out paths claimed by any other pack's
        # state row before treating the scanner's result as orphans.
        #
        # ``state.toml`` is authoritative: filter out paths claimed by any
        # other pack's state row (compared with the same ``_canon_relpath``
        # canonicalisation defined above) before treating the scanner's
        # result as orphans.
        if orphans:
            foreign_owned: set[str] = set()
            for other_name, other_state in repo_state.packs.items():
                if other_name == pack_name:
                    continue
                foreign_owned.update(
                    _canon_relpath(rel) for rel in other_state.files.keys()
                )
            if foreign_owned:
                orphans = [
                    p for p in orphans
                    if _canon_relpath(p.relative_to(output_root).as_posix())
                    not in foreign_owned
                ]
        if orphans:
            _INBAND_DETECTION_SEEN.add(key)
            if force:
                for orphan in orphans:
                    try:
                        orphan.unlink()
                    except OSError:
                        pass
                return None
            print(
                f"install: unrecognized files at projection paths not "
                f"shipped by pack {pack_name} at "
                f"{_format_route_list([str(p) for p in orphans])} — these "
                f"may be left over from an older or interrupted install, or "
                f"your own files; rerun with --force to remove them and "
                f"reinstall, or move them aside and rerun",
                file=sys.stderr,
            )
            return 1

    _INBAND_DETECTION_SEEN.add(key)
    return None


def _format_route_list(routes: list[str]) -> str:
    """Format a list of route paths per RFC-0012 § *Install-time
    message rail (repo scope)*.

      - ``N=1`` → ``"X"``
      - ``N=2`` → ``"X and Y"``
      - ``N>=3`` → ``"X, Y, and Z"`` (serial-comma + final "and")
    """
    if not routes:
        return ""
    if len(routes) == 1:
        return routes[0]
    if len(routes) == 2:
        return f"{routes[0]} and {routes[1]}"
    return ", ".join(routes[:-1]) + f", and {routes[-1]}"


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


def _strip_markdown_code(text: str) -> str:
    """Remove fenced code blocks and inline-code spans from Markdown text.

    Issue #190 minor: a `<adapt:NAME>`-shaped token inside a code span is
    *documentation about* the marker syntax (e.g. the `adapt-to-project`
    SKILL.md says "for each `<adapt:name>` marker …"), not a live
    substitution marker. Stripping code before the marker scan keeps such
    examples from leaking into the install-marker's `unresolved-markers`.
    Heuristic, not a full CommonMark parser — fences first, then inline spans.
    """
    import re

    # Fenced blocks: a line opening with 3+ backticks/tildes to the matching
    # close fence (or end-of-text for an unclosed fence).
    no_fences = re.sub(
        r"(?ms)^[ \t]*(`{3,}|~{3,}).*?(?:^[ \t]*\1[ \t]*$|\Z)", "", text
    )
    # Inline code: a run of N backticks to the next run of exactly N backticks.
    no_inline = re.sub(r"(`+)(?:.|\n)*?\1", "", no_fences)
    return no_inline


def _collect_unresolved_markers(projection: dict) -> list[str]:
    """Return sorted, deduplicated list of `<adapt:NAME>` markers found
    in the projection's byte content. The skill resolves these later;
    the install marker just enumerates them for the nudge surface.

    Markers inside Markdown code spans/blocks are ignored — those are
    documentation examples, not live substitution points (issue #190)."""
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
        for name in marker_re.findall(_strip_markdown_code(text)):
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
    `<user-root>/.agentbundle/.adapt-install-marker.toml`.

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
        # The helper returns `<home>/.agentbundle/state.toml`; we sit
        # the marker next to it.
        state_path = safety.user_state_path(home=root)
        marker_path = state_path.parent / ".adapt-install-marker.toml"
        marker_relpath = ".agentbundle/.adapt-install-marker.toml"
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
                # Security Concern 2: type-validate name/version/install-route.
                # A tampered marker with name=42 (TOML integer) or version=[]
                # survives the installed-at filter but raises ValueError at
                # _emit_basic_string time, bricking subsequent installs.
                _skip_entry = False
                for _field in ("name", "version"):
                    _val = e.get(_field)
                    if _val is not None and not isinstance(_val, str):
                        _label = e.get("name") if _field != "name" else "<unnamed>"
                        if isinstance(_label, str):
                            _label_str = _label
                        else:
                            _label_str = "<unnamed>"
                        print(
                            f"install: warning: marker entry at {marker_path} "
                            f"has non-string {_field} "
                            f"(got {type(_val).__name__}); dropping entry for "
                            f"pack {_label_str!r}",
                            file=sys.stderr,
                        )
                        _skip_entry = True
                        break
                if not _skip_entry:
                    _route_val = e.get("install-route")
                    if _route_val is not None and not isinstance(_route_val, str):
                        _name_val = e.get("name", "<unnamed>")
                        _name_str = _name_val if isinstance(_name_val, str) else "<unnamed>"
                        print(
                            f"install: warning: marker entry for {_name_str!r} at "
                            f"{marker_path} has non-string install-route "
                            f"(got {type(_route_val).__name__}); dropping field",
                            file=sys.stderr,
                        )
                        e = dict(e)
                        del e["install-route"]
                if _skip_entry:
                    continue
                # Security Concern 1: coerce unresolved-markers and new-companions
                # to list[str]. Mirrors install-marker.py _read_entries:400-414.
                e = dict(e)  # shallow copy so we don't mutate the tomllib-parsed dict
                for _field in ("unresolved-markers", "new-companions"):
                    if _field not in e:
                        continue
                    _raw_val = e[_field]
                    if not isinstance(_raw_val, list) or not all(
                        isinstance(_item, str) for _item in _raw_val
                    ):
                        _name_val = e.get("name", "?")
                        _name_str = _name_val if isinstance(_name_val, str) else "?"
                        print(
                            f"install: warning: existing marker entry for "
                            f"{_name_str} has malformed {_field} "
                            f"({type(_raw_val).__name__}); dropping field",
                            file=sys.stderr,
                        )
                        del e[_field]
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
        # Re-emitted entries preserve their original install-route; newly
        # constructed entries (built in this function with no "install-route"
        # key) default to "cli" because this is the CLI install path.
        route = entry.get("install-route", "cli")
        lines.append(f"install-route = {_emit_basic_string(route)}")
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
    # noticing. At repo scope the marker is a top-level
    # `.adapt-install-marker.toml` (not under `.agentbundle/`); the
    # per-prefix check is skipped here because the file is CLI-owned
    # metadata, not pack-projected content, and the same root-level
    # placement was the pre-RFC-0012 contract.
    marker_prefixes = allowed_prefixes
    if scope == "repo" and marker_relpath == ".adapt-install-marker.toml":
        marker_prefixes = None
    safety.write_jailed(
        root,
        marker_relpath,
        content,
        scope=scope,
        allowed_prefixes=marker_prefixes,
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


def _render_for_user_scope(
    pack_dir: Path,
    *,
    adapter: str | None = None,
    allowed_adapters: list[str] | None = None,
    contract_version: str | None = None,
    state_adapter: str | None = None,
    command_name: str = "install",
    user_config: "UserConfig | None" = None,
) -> dict[str, bytes]:
    """Project a pack via the Claude Code / Kiro / Codex adapter
    (depending on RFC-0011 resolution), for user-scope install.

    RFC-0004 § *State file per scope* and § *Adapter-level scope roots*
    imply that user-scope installs land per-adapter outputs (paths under
    ``.claude/...``, ``.kiro/...``, or ``.agents/skills/...``) rather
    than the dist-tree shape ``render.render_pack`` produces. Calling
    the adapter's ``project`` function once into a tempdir gives us the
    per-primitive layout each IDE reads at ``~/``; we collect the
    result as a relpath→bytes mapping for the install walker.

    The five kwargs flow into ``_resolve_target_adapter`` per
    RFC-0011's six-step (0–5) lookup with ``scope="user"`` (RFC-0012
    renamed the helper and added the explicit ``scope`` kwarg). They
    default to ``None`` / ``"install"`` for backward shape with
    legacy positional callers (tests), but every production call
    site threads explicit values.

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

    from agentbundle.build.adapters import (
        claude_code,
        codex,
        copilot,
        cursor,
        kiro,
        kiro_cli,
        kiro_ide,
    )
    from agentbundle.build.main import _read_bundled
    from agentbundle.render import _collect_tree

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    target_adapter = _resolve_target_adapter(
        pack_dir,
        scope="user",
        adapter=adapter,
        allowed_adapters=allowed_adapters,
        contract_version=contract_version,
        state_adapter=state_adapter,
        user_config=user_config,
        command_name=command_name,
    )
    with tempfile.TemporaryDirectory() as raw:
        out = Path(raw)
        if target_adapter == "kiro":
            kiro.project(pack_dir, contract, out)
        elif target_adapter == "kiro-ide":
            kiro_ide.project(pack_dir, contract, out)
        elif target_adapter == "kiro-cli":
            kiro_cli.project(pack_dir, contract, out)
        elif target_adapter == "codex":
            codex.project(pack_dir, contract, out)
        elif target_adapter == "claude-code":
            claude_code.project(pack_dir, contract, out)
        elif target_adapter == "copilot":
            # The copilot build adapter is scope-agnostic and emits
            # repo-relpaths (`.github/…`); the install handler rewrites
            # them to the user-scope home (`.copilot/…`) via
            # `_rewrite_copilot_user_scope_paths` before the path-jail
            # (RFC-0024 / copilot-full-parity).
            copilot.project(pack_dir, contract, out)
        elif target_adapter == "cursor":
            # Cursor's `.cursor/` prefix is identical at both scopes (the
            # claude-code/codex pattern), so — unlike copilot — there is no
            # post-render prefix rewrite; the generic user-root rooting lands
            # the scope-agnostic `.cursor/…` relpaths under `~` (RFC-0026 /
            # cursor-full-parity).
            cursor.project(pack_dir, contract, out)
        else:
            # Defence-in-depth: every user-scope-capable adapter
            # should have an explicit branch above. A future contract
            # bump that ships a new adapter must extend this dispatch;
            # falling through to claude-code masked the gap.
            raise _AdapterResolutionRefused(
                f"{command_name}: no user-scope projection wired for "
                f"adapter {target_adapter!r}"
            )
        return _collect_tree(out)


def _render_for_repo_scope(
    pack_dir: Path,
    *,
    adapter: str | None = None,
    allowed_adapters: list[str] | None = None,
    contract_version: str | None = None,
    state_adapter: str | None = None,
    command_name: str = "install",
    user_config: "UserConfig | None" = None,
) -> tuple[str, dict[str, bytes]]:
    """Project a pack via the resolved adapter (RFC-0011 + RFC-0012
    six-step lookup at ``scope="repo"``), for repo-scope install at
    ``--scope repo`` without ``--emit-install-routes``.

    Mirrors :func:`_render_for_user_scope` but at the repo-scope root:
    the projection lands under ``<repo>/<adapter-prefix>/...`` instead
    of ``~/<adapter-prefix>/...``. Returns a ``(target_adapter,
    projection)`` tuple so the install handler can record
    ``state.adapter`` and thread the matching ``allowed-prefixes.repo``
    into the path-jail.

    RFC-0012 § *Prior art* names the build pipeline's
    ``self-host.toml`` recipe as the in-tree mechanism that already
    produces per-IDE direct writes; this helper is the generalisation
    of that mechanism to the adopter-side install path.
    """
    import tempfile

    from agentbundle.build.adapters import (
        claude_code,
        codex,
        copilot,
        cursor,
        kiro,
        kiro_cli,
        kiro_ide,
    )
    from agentbundle.build.main import _read_bundled
    from agentbundle.render import _collect_tree

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    target_adapter = _resolve_target_adapter(
        pack_dir,
        scope="repo",
        adapter=adapter,
        allowed_adapters=allowed_adapters,
        contract_version=contract_version,
        state_adapter=state_adapter,
        command_name=command_name,
        user_config=user_config,
    )
    with tempfile.TemporaryDirectory() as raw:
        out = Path(raw)
        if target_adapter == "kiro":
            kiro.project(pack_dir, contract, out)
        elif target_adapter == "kiro-ide":
            kiro_ide.project(pack_dir, contract, out)
        elif target_adapter == "kiro-cli":
            kiro_cli.project(pack_dir, contract, out)
        elif target_adapter == "codex":
            codex.project(pack_dir, contract, out)
        elif target_adapter == "claude-code":
            claude_code.project(pack_dir, contract, out)
        elif target_adapter == "copilot":
            copilot.project(pack_dir, contract, out)
        elif target_adapter == "cursor":
            cursor.project(pack_dir, contract, out)
        else:
            raise _AdapterResolutionRefused(
                f"{command_name}: no repo-scope projection wired for "
                f"adapter {target_adapter!r}"
            )
        return target_adapter, _collect_tree(out)


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

    Three shapes count:
      - Claude Code: ``mode.user = "user-merge-json"``.
      - Kiro: ``mode = "merge-into-agent-json"`` (single mode, no
        scope qualifier — the agent-file target is scope-conditional
        via `<scope-root>` resolution).
      - Copilot: ``mode = "copilot-hooks-json"`` in the **array-form**
        ``[[adapter.copilot.projection]]`` table (RFC-0024 /
        copilot-full-parity). Copilot's hooks are a *file-based* model
        (one self-contained JSON per wiring file in a directory), not a
        merge into a shared settings/agent file — so they work at user
        scope via the build projection + the install handler's prefix
        rewrite (`_rewrite_copilot_user_scope_paths`), with no
        merge step. `_merge_user_scope_hook_wiring` returns no rows for
        copilot accordingly.

    Anything else (``dropped``, ``degraded-info-log``, absent
    projection) is refused.
    """
    import tomllib
    from agentbundle.build.main import _read_bundled

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    adapter_block = contract.get("adapter", {}).get(adapter_name, {})
    projections = adapter_block.get("projections", {}) if isinstance(adapter_block, dict) else {}
    hook_wiring = projections.get("hook-wiring") if isinstance(projections, dict) else None
    if isinstance(hook_wiring, dict):
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
    # Array-form projection table (copilot): a hook-wiring entry with the
    # file-based `copilot-hooks-json` mode is user-scope-capable.
    array_form = adapter_block.get("projection", []) if isinstance(adapter_block, dict) else []
    for entry in array_form:
        if (
            isinstance(entry, dict)
            and entry.get("primitive") == "hook-wiring"
            and entry.get("mode") == "copilot-hooks-json"
        ):
            return True
    return False


class _AdapterResolutionRefused(Exception):
    """Raised by :func:`_resolve_target_adapter` for any of the pinned
    refusal paths (publisher-vs-installer drift, ``--adapter`` not in
    pack's set, ``--adapter`` not user-scope-capable at user scope,
    ``--adapter`` not shipped at repo scope). Carries the exact
    stderr text — the install handler prints ``str(exc)`` and returns
    non-zero.
    """


def _user_scope_adapter_probes() -> dict[str, "Callable[[Path], bool]"]:
    """Per-adapter CLI-home presence probe. Explicit table (not a
    single `Path.home() / f".{ide}"` interpolation) because codex is
    an OR-probe: either `~/.codex/` exists (Codex CLI installed) or
    `~/.agents/skills/` exists (the codex skills root, populated by
    a prior install). The function is module-private (leading
    underscore) — callers use the helpers below.
    """
    return {
        "claude-code": lambda home: (home / ".claude").exists(),
        "kiro":        lambda home: (home / ".kiro").exists(),
        "kiro-ide":    lambda home: (home / ".kiro").exists(),
        "kiro-cli":    lambda home: (home / ".kiro").exists(),
        "codex":       lambda home: (
            (home / ".codex").exists()
            or (home / ".agents" / "skills").exists()
        ),
    }


def _resolve_target_adapter(
    pack_dir: Path,
    *,
    scope: str,
    adapter: str | None = None,
    allowed_adapters: list[str] | None = None,
    contract_version: str | None = None,
    state_adapter: str | None = None,
    command_name: str = "install",
    user_config: "UserConfig | None" = None,
) -> str:
    """Resolve the adapter that an install/upgrade targets at *scope*
    (RFC-0011 substrate; RFC-0012 widens to repo scope).

    The six-step (0–5) lookup, with scope-branched points at 0, 1, 4,
    and 5:

      0. **Publisher-vs-installer drift refusal** — if
         ``allowed_adapters`` is declared, intersect with the bundled
         contract's shipped-adapter set; refuse on any miss with the
         pinned message. Runs first so neither ``--adapter`` (step 1)
         nor state-hint (step 2) can leak a no-longer-shipped value
         through. Refusal text is scope-uniform modulo the
         ``<verb>`` prefix; the user-scope-capability subcheck is
         **skipped at repo scope** (Copilot is admissible at repo
         scope but not at user scope).

      1. **``--adapter`` override** — validates against
         ``allowed_adapters`` (when declared) or, at user scope,
         against the contract's user-scope-capable set; at repo
         scope, against the contract's shipped-adapter set (Copilot
         admissible).

      2. **State-hint short-circuit (AC10b)** — return
         ``state_adapter`` when admissible; the install was already
         pinned. Scope-uniform.

      3. **Contract-version gate** — uses
         ``contract_supports_hook_wiring(contract_version)``;
         scope-uniform.

      4. **Per-scope branch**: at user scope, walk the per-adapter
         probe table and return the first match; at repo scope,
         **skip the probe** (RFC-0012 § *Alternatives* #4 — symmetric
         probing rejected) and return ``DEFAULT_ADAPTER``
         if in ``allowed_adapters``, else ``allowed_adapters[0]``.

      5. **Legacy heuristic** — preserved for ``< 0.7`` packs that
         omit ``allowed-adapters``. Always returns ``DEFAULT_ADAPTER``
         so downstream catalogues that monkey-patch the constant
         rebrand uniformly across every resolver branch.

    The function raises :class:`_AdapterResolutionRefused` for any of
    the pinned refusal paths; the caller prints the exception text and
    exits non-zero.

    Known limitation: two packs claiming the same Kiro agent name
    (each ships ``.apm/agents/<name>.md``) will both write to the
    same projected ``.kiro/agents/<name>.json`` and the second install
    will silently overwrite the first's wiring. A follow-on RFC for
    shared-agent ownership will need to address this; this spec
    preserves the behaviour unchanged.
    """
    from agentbundle.build.main import _read_bundled
    from agentbundle.scope import (
        DEFAULT_ADAPTER,
        configured_adapter,
        contract_supports_hook_wiring,
        contract_version_at_least,
        shipped_adapters_from_contract,
        user_scope_capable_adapters_from_contract,
    )

    pack_name = pack_dir.name
    shipped = shipped_adapters_from_contract()
    user_capable = user_scope_capable_adapters_from_contract()

    # Step 0: publisher-vs-installer drift refusal — scope-uniform
    # except the user-scope-capability subcheck is skipped at repo
    # scope (Copilot is admissible there).
    if allowed_adapters is not None:
        for declared in allowed_adapters:
            if declared not in shipped:
                from agentbundle.version import CLI_VERSION as cli_version
                contract = tomllib.loads(_read_bundled("adapter.toml"))
                cv = contract.get("contract", {}).get("version", "?")
                raise _AdapterResolutionRefused(
                    f"{command_name}: pack {pack_name!r} declares "
                    f"allowed-adapter {declared!r} which is not admitted by "
                    f"adapter contract v{cv} shipped with agentbundle "
                    f"{cli_version}"
                )
        if scope == "user":
            # User-scope-capability subcheck — fires only at user
            # scope. RFC-0012: Copilot is admissible at repo scope
            # without declaring `[scope].user`, so this subcheck
            # must not fire there.
            for declared in allowed_adapters:
                if declared not in user_capable:
                    contract = tomllib.loads(_read_bundled("adapter.toml"))
                    cv = contract.get("contract", {}).get("version", "?")
                    raise _AdapterResolutionRefused(
                        f"{command_name}: pack {pack_name!r} declares "
                        f"allowed-adapter {declared!r} which does not "
                        f"declare a user-scope root in the v{cv} adapter "
                        f"contract"
                    )

    # Step 1: --adapter override.
    if adapter is not None:
        if allowed_adapters is not None:
            if adapter not in allowed_adapters:
                raise _AdapterResolutionRefused(
                    f"{command_name}: --adapter {adapter} not in pack's "
                    f"allowed-adapters set"
                )
        else:
            if scope == "user":
                if adapter not in user_capable:
                    contract = tomllib.loads(_read_bundled("adapter.toml"))
                    cv = contract.get("contract", {}).get("version", "?")
                    raise _AdapterResolutionRefused(
                        f"{command_name}: --adapter {adapter} not admitted "
                        f"as a user-scope-capable adapter under contract v{cv}"
                    )
            else:
                # Repo scope: any shipped adapter is admissible.
                if adapter not in shipped:
                    contract = tomllib.loads(_read_bundled("adapter.toml"))
                    cv = contract.get("contract", {}).get("version", "?")
                    raise _AdapterResolutionRefused(
                        f"{command_name}: --adapter {adapter} not admitted "
                        f"as a shipped adapter under contract v{cv}"
                    )
        return adapter

    # Step 2: state-hint short-circuit (AC10b) — scope-uniform.
    if state_adapter is not None:
        if allowed_adapters is not None:
            if state_adapter in allowed_adapters:
                return state_adapter
        else:
            admissible = user_capable if scope == "user" else shipped
            if state_adapter in admissible:
                return state_adapter
        # state_adapter is not admissible — fall through to step 3+
        # and the existing upgrade.py cross-adapter refusal will fire
        # if the new resolution differs.

    # Step 2.5: user-config pre-flight (agentbundle-config-subcommand
    # spec AC12). Runs only when state_adapter is None — upgrades
    # preserve whatever adapter the existing install used; user-config
    # only affects fresh installs. When a user actively configured a
    # known adapter, either return it (when admissible at scope and
    # in pack allowed_adapters) or raise with AC13/AC14 messages. When
    # nothing is configured, this block is a no-op and Steps 3+ run
    # as today — preserving the probe-by-default behavior for users
    # who never ran `agentbundle config set`.
    candidate = (
        configured_adapter(user_config) if state_adapter is None else None
    )
    if candidate is not None:
        admissible_at_scope = user_capable if scope == "user" else shipped
        if candidate not in admissible_at_scope:
            raise _AdapterResolutionRefused(
                f"{command_name}: configured adapter {candidate!r} is "
                f"not supported at {scope} scope. Adapters supported "
                f"at {scope} scope: {sorted(admissible_at_scope)}. To "
                f"proceed: invoke the command at a different scope "
                f"(e.g. --scope repo) where {candidate!r} is "
                f"supported, or pass --adapter <name> for a per-install "
                f"override, or run `agentbundle config set adapter "
                f"<name>` to change the default, or `agentbundle "
                f"config unset adapter` to clear it."
            )
        if allowed_adapters is not None and candidate not in allowed_adapters:
            raise _AdapterResolutionRefused(
                f"{command_name}: pack {pack_name} is not supported "
                f"with your configured adapter {candidate!r}. The pack "
                f"supports: {sorted(allowed_adapters)}. To proceed: "
                f"pass --adapter <name> for a per-install override, or "
                f"run `agentbundle config set adapter <name>` to change "
                f"the default, or `agentbundle config unset adapter` to "
                f"clear it."
            )
        return candidate

    # Step 3 + Step 4: contract-version gate + per-scope branch.
    if (
        allowed_adapters is not None
        and contract_supports_hook_wiring(contract_version)
    ):
        if scope == "user":
            # Step 4 (user-scope): per-adapter probe table; first
            # match wins.
            probes = _user_scope_adapter_probes()
            home = Path.home()
            for declared in allowed_adapters:
                probe = probes.get(declared)
                if probe is not None and probe(home):
                    return declared
        # Step 4 (repo-scope): no probe. RFC-0012 § *Alternatives* #4
        # rejects symmetric probing as load-bearing asymmetry —
        # probing `<repo>/.<ide>/` would silently override an explicit
        # `--adapter` (the probe runs only when `--adapter` is omitted,
        # but the same rule reads cleaner stated uniformly).
        if DEFAULT_ADAPTER in allowed_adapters:
            return DEFAULT_ADAPTER
        return allowed_adapters[0]

    # Step 4b (repo-scope v0.7+ pack with no `allowed-adapters`):
    # AC9 step 5 — "legacy heuristic fires only for `< v0.7` packs
    # at repo scope" — means a v0.7+ pack with no `allowed-adapters`
    # at repo scope must NOT fall through to step 5; return the
    # configured default instead. Drawback #7 in RFC-0012 names the
    # repo-only-pack v0.2 → v0.7 bump as load-bearing precisely for
    # this branch. The version gate is numeric (`contract_version_at_least`)
    # — the prior lexical `>= "0.7"` string compare mis-ordered two-digit
    # minors (`"0.11" < "0.7"` lexically), which the inline comment flagged
    # would break "once major or two-digit minor bumps land." It was latent
    # (Step 4b and the Step-5 fallback both return DEFAULT_ADAPTER), but the
    # v0.11 cursor bump made it live two-digit territory, so it moves to the
    # numeric helper now (RFC-0026 / cursor-full-parity ride-along).
    if scope == "repo" and contract_version_at_least(contract_version, "0.7"):
        return DEFAULT_ADAPTER

    # Step 5: legacy heuristic — preserved for `< v0.7` packs that
    # omit `allowed-adapters`. Always returns ``DEFAULT_ADAPTER`` so
    # downstream catalogues that monkey-patch the constant rebrand
    # uniformly across every resolver branch. The pre-fix agents-
    # presence ``"kiro"`` hint was a guess about pack-author intent;
    # an explicit downstream ``DEFAULT_ADAPTER`` is authoritative.
    return DEFAULT_ADAPTER




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

    Copilot is an explicit no-op here: its hooks are file-based and the
    `.github/…`→`.copilot/…` rewrite is owned by
    ``_rewrite_copilot_user_scope_paths`` (RFC-0024 / copilot-full-parity).
    Returning early keeps copilot's no-op intentional rather than relying on
    its `.github/hooks/` paths happening to miss the `tools/hooks/` branch
    below.
    """
    import json

    if target_adapter == "copilot":
        return projection

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


def _rewrite_copilot_user_scope_paths(
    projection: dict[str, bytes],
) -> dict[str, bytes]:
    """Rewrite copilot's repo-relpath projection to the user-scope home.

    The copilot build adapter is scope-agnostic and emits ``.github/…``
    relpaths at every scope (RFC-0024 / copilot-full-parity). At user scope
    Copilot discovers content from ``~/.copilot/…`` instead, so the install
    handler swaps the prefix for **all** copilot primitives — skill, agent,
    hook-wiring, hook-body — before the path-jail check.

    Unlike claude-code (whose skills share ``.claude/`` at both scopes, so
    only its hooks diverge via ``_rewrite_user_scope_hook_paths``), copilot's
    whole prefix changes, so this rewrite is **not** hook-gated.
    """
    prefix_map = {
        ".github/instructions/": ".copilot/instructions/",
        ".github/agents/": ".copilot/agents/",
        ".github/hooks/": ".copilot/hooks/",
    }
    rewritten: dict[str, bytes] = {}
    for relpath, content in projection.items():
        for repo_prefix, user_prefix in prefix_map.items():
            if relpath.startswith(repo_prefix):
                relpath = user_prefix + relpath[len(repo_prefix) :]
                break
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

    if target_adapter == "copilot":
        # Copilot's hooks are file-based (RFC-0024 / copilot-full-parity): each
        # wiring `.toml` is already projected to a self-contained
        # `~/.copilot/hooks/<name>.json` by the build adapter + the user-scope
        # prefix rewrite. There is no shared settings/agent file to merge into,
        # so there are no merge-owned rows to record here — the files are
        # tracked as ordinary projection writes (state.files), like skills.
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
    need Kiro's prefixes (`.kiro/`, `.agentbundle/`) not Claude Code's
    (`.claude/`, `.agentbundle/`). The fallback (legacy contract
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


def _adapter_allowed_prefixes_repo(adapter_name: str) -> list[str]:
    """Read *adapter_name*'s `allowed-prefixes.repo` from the contract.

    RFC-0012 adds an `allowed-prefixes.repo` entry to every shipped
    adapter's scope table at contract v0.7. Mirrors the user-scope
    helper above; the fallback is the conservative single-prefix list
    rooted at the adapter's documented repo-scope directory.
    """
    import tomllib
    from agentbundle.build.main import _read_bundled

    contract = tomllib.loads(_read_bundled("adapter.toml"))
    try:
        return list(
            contract["adapter"][adapter_name]["scope"]["allowed-prefixes"]["repo"]
        )
    except KeyError:
        # Defensive: contract pre-dates v0.7 or the requested adapter
        # has no scope table.
        defaults = {
            "claude-code": [".claude/", ".agentbundle/"],
            "kiro": [".kiro/", ".agentbundle/"],
            "codex": [".agents/skills/", ".agentbundle/"],
            "copilot": [".github/instructions/"],
        }
        return defaults.get(adapter_name, [".agentbundle/"])


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
