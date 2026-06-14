"""``agentbundle uninstall`` — remove a pack's Tier-1 files from the adopter tree.

Algorithm:
  1. Load ``.agentbundle-state.toml`` from ``args.root``.
     Exit non-zero with stderr if the pack is not in state.
  2. For each file recorded under ``[pack.<name>.files]``:
     - Compute the on-disk SHA.
     - If it matches the state-recorded SHA (Tier-1) → ``os.remove``.
     - If it differs (or file is absent) → Tier-2 → warn on stderr and keep.
  3. Best-effort: remove empty parent directories left behind by removals.
  4. Save the updated state file with ``[pack.<name>]`` table dropped.
  5. Print summary to stdout: N removed, M kept.
  6. Exit 0.

Tier-3 files (paths not recorded in the pack's state table) are never touched.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle uninstall``.

    Args:
        args.pack  — name of the pack to uninstall (required).
        args.root  — repo root directory (default '.').

    Returns 0 on success, non-zero on error.
    """
    from agentbundle.config import ConfigError, dump_state, load_state
    from agentbundle import safety

    pack_name: str = args.pack
    cli_scope: str | None = getattr(args, "scope", None)
    root = Path(args.root).resolve()
    state_path = root / ".agentbundle-state.toml"

    # ── Step 1: Multi-scope disambiguator (RFC-0004) ──────────────────────────
    # If the pack is at both repo and user scopes, --scope is required.
    # If it's at exactly one scope, infer. The check needs *read* access
    # to both state files (read-only — v0.1 refusal fires at the *write*
    # below). Importing scope_mod lazily so --version stays fast.
    from agentbundle import scope as scope_mod

    repo_state_for_check = load_state(state_path)
    installed_at_repo = pack_name in repo_state_for_check.packs
    user_state_path = None
    installed_at_user = False
    try:
        user_root = scope_mod.resolve_user_root()
        user_state_path = user_root / ".agentbundle" / "state.toml"
        user_state_for_check = load_state(user_state_path)
        installed_at_user = pack_name in user_state_for_check.packs
    except scope_mod.UserScopeUnresolvable:
        # No accessible user root — treat user scope as empty for the
        # disambiguator. The repo write below is unaffected.
        pass

    if installed_at_repo and installed_at_user and cli_scope is None:
        print(
            f"uninstall: {pack_name} installed at multiple scopes; "
            "pass --scope {repo, user}",
            file=sys.stderr,
        )
        return 1

    # Resolve the effective scope: explicit CLI flag, else the inferred
    # single-scope value, else repo (the historical default).
    if cli_scope is not None:
        effective_scope = cli_scope
    elif installed_at_user and not installed_at_repo:
        effective_scope = "user"
    else:
        effective_scope = "repo"

    # Route to the correct state file based on effective scope.
    # At user scope, `root` is the user's home (where projected files
    # live) and the state file lives at `<root>/.agentbundle/state.toml`.
    # Keep the two values separate so the path-jailed write picks the
    # right *relpath relative to root*, not a bare dotfile in $HOME.
    user_prefixes: list[str] | None = None
    if effective_scope == "user":
        if user_state_path is None:
            print(
                "uninstall: cannot resolve user scope: $HOME unset or invalid",
                file=sys.stderr,
            )
            return 1
        state_path = user_state_path
        root = user_state_path.parent.parent  # = ~ (the user-scope projection root)
        # Pull the adapter contract's allowed-prefixes so the user-scope
        # path-jail fires on the per-file removal walk below. The
        # adapter is recorded on the pack's state row (v0.3); fall back
        # to claude-code when absent (v0.2-vintage rows preserved across
        # the header-only migration, per RFC-0005 § State-file impact).
        from agentbundle.commands.install import _adapter_allowed_prefixes_user

        recorded_adapter = (
            user_state_for_check.packs[pack_name].adapter
            if pack_name in user_state_for_check.packs
            else "claude-code"
        )
        user_prefixes = _adapter_allowed_prefixes_user(recorded_adapter or "claude-code")

    # ── Step 1b: Load state for write (refuse v0.1 here, after disambig) ─────
    try:
        state = load_state(state_path, for_write=True)
    except ConfigError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

    if pack_name not in state.packs:
        print(f"uninstall: pack {pack_name!r} not installed", file=sys.stderr)
        return 1

    pack_state = state.packs[pack_name]

    # ── Step 2: Walk the pack's recorded files ────────────────────────────────
    # State-file relpaths are *untrusted input* — a malicious state file
    # could record `relpath = "../.ssh/authorized_keys"` and the
    # `os.remove` below would happily delete a path outside the jail.
    # At user scope that blast radius reaches the user's whole home
    # directory; at repo scope it's still wrong even though smaller.
    # `safety.assert_under` + (at user scope) the prefix-list check
    # refuses any entry that escapes the per-scope jail before any
    # filesystem operation runs.
    removed: list[str] = []
    kept: list[str] = []

    for relpath, entry in sorted(pack_state.files.items()):
        on_disk = root / relpath
        try:
            safety.assert_under(root, on_disk)
        except safety.PathJailError:
            print(
                f"uninstall: warning: state entry {relpath!r} resolves outside "
                f"jail root; refusing to touch",
                file=sys.stderr,
            )
            continue
        if effective_scope == "user":
            target_relpath = on_disk.resolve().relative_to(root.resolve()).as_posix()
            if not any(target_relpath.startswith(p) for p in (user_prefixes or [])):
                print(
                    f"uninstall: warning: state entry {relpath!r} lies outside "
                    f"allowed-prefixes for scope 'user'; refusing to touch",
                    file=sys.stderr,
                )
                continue
        recorded_sha = entry.get("sha") if isinstance(entry, dict) else None

        # If the file is absent on disk, treat as already gone (Tier-2 edge
        # case: the adopter deleted it manually). Do not error — just skip.
        if not on_disk.exists():
            # Not present → nothing to remove; also not an adopter edit we
            # need to preserve. Skip silently.
            continue

        # Compute on-disk SHA and compare against the recorded value.
        on_disk_sha = safety.sha256_file(on_disk)
        if recorded_sha and on_disk_sha == recorded_sha:
            # Tier-1: the bundle owns this file — safe to remove.
            try:
                os.remove(on_disk)
            except OSError as exc:
                print(
                    f"uninstall: could not remove {relpath}: {exc}",
                    file=sys.stderr,
                )
                return 1
            removed.append(relpath)
        else:
            # Tier-2: adopter-edited (or no recorded SHA) — preserve with warning.
            print(
                f"uninstall: keeping adopter-edited file: {relpath}",
                file=sys.stderr,
            )
            kept.append(relpath)

    # ── Step 2b: RFC-0005 T8b — unproject hook-wiring-owned entries ─────────
    # When the pack has hook_wiring_owned rows (v0.3 user-scope hooks),
    # dispatch to the right merge engine's `unproject` to remove those
    # entries from the merge target file. Empty `hooks.<event>` arrays
    # are pruned; the target file itself stays in place (Kiro: agent
    # primitive's direct-file uninstall handles it; Claude Code: the
    # settings file is adopter-shared and must not be deleted).
    if pack_state.hook_wiring_owned:
        adapter = pack_state.adapter or "claude-code"
        owned_by_target: dict[str, list[tuple[str, str]]] = {}
        for entry in pack_state.hook_wiring_owned:
            event = entry.get("event")
            entry_id = entry.get("id")
            if not (isinstance(event, str) and isinstance(entry_id, str)):
                continue
            target_file_rel = entry.get("target-file")
            if not target_file_rel:
                # Claude Code rows default to `~/.claude/settings.json`
                # per RFC-0005 § State-file impact (resolve via the
                # user-scope target on the adapter contract).
                target_file_rel = ".claude/settings.json"
            owned_by_target.setdefault(target_file_rel, []).append((event, entry_id))

        for target_file_rel, owned in owned_by_target.items():
            target_path = root / target_file_rel.lstrip("/")
            # The merge family (`kiro-cli`, plus the legacy `kiro` block that
            # pre-migration state may still record) merges into a pack-owned
            # agent JSON; claude-code merges into the shared settings file.
            if adapter in ("kiro", "kiro-cli"):
                from agentbundle.build.projections.merge_into_agent_json import (
                    unproject as _unproject,
                )
            else:
                from agentbundle.build.projections.user_merge_json import (
                    unproject as _unproject,
                )
            try:
                _unproject(target_path, owned)
            except Exception as exc:
                print(f"uninstall: hook-wiring unproject failed: {exc}", file=sys.stderr)
                return 1

    # ── Step 3: Best-effort cleanup of empty parent directories ──────────────
    _prune_empty_parents(root, removed)

    # ── Step 4: Remove the pack's table from state and persist ────────────────
    del state.packs[pack_name]
    serialised = dump_state(state)
    # Write the state file at the right per-scope relpath. At repo scope
    # the relpath is `.agentbundle-state.toml`; at user scope it's
    # `.agentbundle/state.toml` (the namespaced dot-directory). Compute
    # from `state_path.relative_to(root)` so the layout is single-sourced.
    state_relpath = state_path.relative_to(root).as_posix()
    try:
        safety.write_jailed(
            root,
            state_relpath,
            serialised,
            scope=effective_scope,
            allowed_prefixes=user_prefixes,
        )
    except safety.PathJailError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

    # ── Step 5: Summary ───────────────────────────────────────────────────────
    print(f"uninstall: {len(removed)} removed, {len(kept)} kept")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prune_empty_parents(root: Path, removed_relpaths: list[str]) -> None:
    """Remove empty directories left behind after file deletions.

    Works bottom-up: for each removed file, walk its parents upward until
    reaching ``root`` or a non-empty directory. Ignores all errors — this is
    best-effort housekeeping.

    `removed_relpaths` is filtered to jail-clean entries by the caller
    (see the path-jail check in `run`), so the recursive parent walk
    here is guaranteed to stay under `root`. We still defensively
    `assert_under` each candidate before `rmdir` to catch any future
    regression in the caller — leaving the rmdir unguarded would
    silently re-introduce the same path-traversal gap.
    """
    from agentbundle.safety import PathJailError, assert_under

    # Collect unique parent directories in deepest-first order.
    dirs_to_check: set[Path] = set()
    for relpath in removed_relpaths:
        parent = (root / relpath).parent
        while parent != root and parent != parent.parent:
            try:
                assert_under(root, parent)
            except PathJailError:
                break
            dirs_to_check.add(parent)
            parent = parent.parent

    # Sort deepest first (longest path first) so we remove children before
    # parents — avoids trying to remove a directory that still has children.
    for d in sorted(dirs_to_check, key=lambda p: len(p.parts), reverse=True):
        try:
            d.rmdir()  # Only succeeds if the directory is empty.
        except OSError:
            pass  # Not empty or other error — skip silently.
