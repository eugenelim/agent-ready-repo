"""``agentbundle uninstall`` — remove a pack's Tier-1 files from the adopter tree.

Algorithm:
  1. Load ``.agentbundle-state.toml`` from ``args.root``.
     Exit non-zero with stderr if the pack is not in state.
  2a. Classify each file recorded under ``[pack.<name>.files]`` (no mutation):
      - Compute the on-disk SHA. Match (Tier-1) → ``remove``; differ / absent-
        sha (Tier-2) → ``keep``. Absent-on-disk files are skipped.
  2a'. ``--dry-run`` → print the per-file plan + a one-line summary and exit 0,
       writing nothing (no remove, unproject, prune, or state rewrite).
  2b. Confirm before the first removal (``--yes`` skips; a non-TTY stdin refuses
      rather than blocking on ``input()``).
  2c. Execute the classified plan: ``os.remove`` each ``remove``; warn-and-keep
      each ``keep``. Acts on the classification without re-hashing.
  2d. Unproject any hook-wiring-owned entries from their merge target.
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
        args.pack     — name of the pack to uninstall (required).
        args.root     — repo root directory (default '.').
        args.scope    — {repo, user} disambiguator (optional).
        args.dry_run  — preview the per-file plan; write nothing (optional).
        args.yes      — skip the confirmation prompt (optional, default off).

    Returns 0 on success, non-zero on error.
    """
    from agentbundle.config import ConfigError, dump_state, load_state
    from agentbundle import safety

    pack_name: str = args.pack
    cli_scope: str | None = getattr(args, "scope", None)
    cli_adapter: str | None = getattr(args, "adapter", None)
    root = Path(args.root).resolve()
    state_path = root / ".agentbundle-state.toml"

    # ── Step 1: Multi-scope disambiguator (RFC-0004) ──────────────────────────
    # If the pack is at both repo and user scopes, --scope is required.
    # If it's at exactly one scope, infer. The check needs *read* access
    # to both state files. Importing scope_mod lazily so --version stays fast.
    from agentbundle import scope as scope_mod

    # A legacy (non-v0.4) state file is refused on read too (RFC-0052 hard
    # cross-version refusal); surface it as a clean refuse, not a traceback.
    try:
        repo_state_for_check = load_state(state_path)
    except ConfigError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1
    installed_at_repo = repo_state_for_check.has_pack(pack_name)
    user_state_path = None
    installed_at_user = False
    user_state_for_check = None
    try:
        user_root = scope_mod.resolve_user_root()
        user_state_path = user_root / ".agentbundle" / "state.toml"
        user_state_for_check = load_state(user_state_path)
        installed_at_user = user_state_for_check.has_pack(pack_name)
    except scope_mod.UserScopeUnresolvable:
        # No accessible user root — treat user scope as empty for the
        # disambiguator. The repo write below is unaffected.
        pass
    except ConfigError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

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

    # ── Step 1b: Load state for write ────────────────────────────────────────
    try:
        state = load_state(state_path, for_write=True)
    except ConfigError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

    if not state.has_pack(pack_name):
        print(f"uninstall: pack {pack_name!r} not installed", file=sys.stderr)
        return 1

    # ── Step 1c: Multi-adapter disambiguator (RFC-0052) ──────────────────────
    # A pack can carry multiple adapter rows at one scope; uninstall targets
    # exactly one. Infer when there is a single row; require --adapter when
    # there is more than one.
    rows = state.rows_for_pack(pack_name)
    if cli_adapter is not None:
        if cli_adapter not in rows:
            print(
                f"uninstall: {pack_name} is not installed for adapter "
                f"{cli_adapter!r} at {effective_scope} scope "
                f"(installed for: {', '.join(sorted(rows)) or 'none'})",
                file=sys.stderr,
            )
            return 1
        target_adapter = cli_adapter
    elif len(rows) == 1:
        target_adapter = next(iter(rows))
    else:
        print(
            f"uninstall: {pack_name} installed for multiple adapters at "
            f"{effective_scope} scope ({', '.join(sorted(rows))}); pass --adapter",
            file=sys.stderr,
        )
        return 1

    pack_state = rows[target_adapter]

    # Per-row path-jail: at user scope, pull the *target adapter's*
    # allowed-prefixes so each removal is jailed against the removing row's
    # own prefixes, never a sibling's (RFC-0052 / ADR-0039 per-row jail).
    if effective_scope == "user":
        from agentbundle.commands.install import _adapter_allowed_prefixes_user

        user_prefixes = _adapter_allowed_prefixes_user(target_adapter or "claude-code")

    dry_run: bool = bool(getattr(args, "dry_run", False))
    yes: bool = bool(getattr(args, "yes", False))

    # ── Step 2a: Classify the pack's recorded files (no mutation) ─────────────
    # State-file relpaths are *untrusted input* — a malicious state file
    # could record `relpath = "../.ssh/authorized_keys"` and the
    # `os.remove` below would happily delete a path outside the jail.
    # At user scope that blast radius reaches the user's whole home
    # directory; at repo scope it's still wrong even though smaller.
    # `safety.assert_under` + (at user scope) the prefix-list check
    # refuses any entry that escapes the per-scope jail before any
    # filesystem operation runs. These "refusing to touch" warnings apply
    # equally to a real run and a `--dry-run` preview, so they print here.
    #
    # The classification is computed once, into `decisions`, and the
    # execution pass (Step 2c) acts on it WITHOUT re-hashing — so the bytes
    # a `--dry-run` / prompt shows are exactly the bytes a real run removes
    # (the Tier-1 SHA is captured here, once; the confirm-reading window is
    # not re-checked — see spec AC5).
    decisions: list[tuple[str, str]] = []  # (relpath, "remove" | "keep" | "shared")

    # Last-owner derivation (RFC-0052 / ADR-0039), captured ONCE here
    # against the persisted union of all rows; the execute pass below acts
    # on `decisions` without re-deriving. A relpath is removable only when
    # the row being uninstalled is its **last** owner — i.e. no other
    # `(pack, adapter)` row's footprint still claims it.
    target_key = (pack_name, target_adapter)

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

        # Shared-survival: a sibling adapter row of the same pack still owns
        # this path → it is co-owned; keep the file, just drop our claim.
        other_owners = [k for k in state.owners_of(relpath) if k != target_key]
        if other_owners:
            decisions.append((relpath, "shared"))
            continue

        # If the file is absent on disk, treat as already gone (Tier-2 edge
        # case: the adopter deleted it manually). Do not error — just skip.
        if not on_disk.exists():
            # Not present → nothing to remove; also not an adopter edit we
            # need to preserve. Skip silently.
            continue

        # Compute on-disk SHA and compare against the recorded value.
        on_disk_sha = safety.sha256_file(on_disk)
        if recorded_sha and on_disk_sha == recorded_sha:
            decisions.append((relpath, "remove"))  # Tier-1: bundle owns it (last owner).
        else:
            decisions.append((relpath, "keep"))  # Tier-2: adopter-edited.

    n_remove = sum(1 for _, d in decisions if d == "remove")
    n_shared = sum(1 for _, d in decisions if d == "shared")
    n_keep = len(decisions) - n_remove - n_shared

    # ── Step 2a': --dry-run preview — print the plan and write nothing ────────
    # Returns BEFORE the hook-wiring unproject (Step 2b), the empty-dir prune
    # (Step 3), and the state rewrite (Step 4): a dry run mutates nothing on
    # disk or in state (spec AC1).
    if dry_run:
        from agentbundle.commands._common import format_plan_line

        for relpath, decision in decisions:
            if decision == "shared":
                print(f"keep   shared   {relpath}  (co-owned by another adapter)")
                continue
            tier = "tier-1" if decision == "remove" else "tier-2"
            print(format_plan_line(decision, tier, relpath))
        _shared_note = f", {n_shared} shared (kept)" if n_shared else ""
        print(
            f"dry-run: {len(decisions)} file(s) — {n_remove} remove, "
            f"{n_keep} keep{_shared_note}. Nothing written."
        )
        return 0

    # ── Step 2b: Confirm before the first os.remove (spec AC2/AC3/AC4) ────────
    # `--yes` skips the prompt; a non-interactive stdin refuses rather than
    # blocking on input(). Mirrors `upgrade`'s posture via the shared helper.
    from agentbundle.commands._common import confirm_or_refuse

    if not confirm_or_refuse(
        yes=yes,
        question=(
            f"Uninstall {pack_name} at {effective_scope} scope? This removes "
            f"{n_remove} file(s); {n_keep} adopter-edited file(s) will be kept. "
            f"[y/N] "
        ),
        refuse_message=(
            f"uninstall: refusing to uninstall {pack_name} at {effective_scope} "
            f"scope without confirmation; pass --yes to uninstall non-interactively"
        ),
        abort_message="uninstall: aborted; no changes made",
    ):
        return 1

    # ── Step 2c: Execute the classified plan ──────────────────────────────────
    # Acts on `decisions` directly (no re-hash): the bytes shown above are the
    # bytes removed. The "keeping adopter-edited file" warning preserves the
    # pre-existing Tier-2 notice.
    removed: list[str] = []
    kept: list[str] = []
    shared: list[str] = []
    for relpath, decision in decisions:
        on_disk = root / relpath
        if decision == "remove":
            try:
                os.remove(on_disk)
            except OSError as exc:
                print(
                    f"uninstall: could not remove {relpath}: {exc}",
                    file=sys.stderr,
                )
                return 1
            removed.append(relpath)
        elif decision == "shared":
            # Co-owned by a sibling adapter row of the same pack; the file
            # survives — we only drop this row's claim (Step 4). No warning:
            # this is the normal shared-prefix coexistence path.
            shared.append(relpath)
        else:
            print(
                f"uninstall: keeping adopter-edited file: {relpath}",
                file=sys.stderr,
            )
            kept.append(relpath)

    # ── Step 2d: RFC-0005 T8b — unproject hook-wiring-owned entries ─────────
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

    # ── Step 4: Drop only the targeted adapter row from state and persist ─────
    # Sibling adapter rows of the same pack (and their co-owned shared files)
    # survive — only this `(pack, adapter)` row is removed (RFC-0052).
    del state.packs[(pack_name, target_adapter)]
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
    _shared_suffix = f", {len(shared)} kept (shared)" if shared else ""
    print(f"uninstall: {len(removed)} removed, {len(kept)} kept{_shared_suffix}")
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
