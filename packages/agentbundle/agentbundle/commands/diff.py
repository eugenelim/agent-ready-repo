"""T9: `diff` subcommand.

Compare the on-disk projection (under `args.root`) against a fresh in-memory
render of the same pack. If they match: exit 0. If anything drifted (modified
or missing): exit 1 with a one-line list of drifted paths.

Algorithm:
  1. Render `args.pack_path` in-memory via `render.render_pack`.
  2. For each `(relpath, expected_bytes)` in the render dict:
     - Compute on-disk SHA at `args.root / relpath`.
     - If absent on disk or differs from `sha256_bytes(expected_bytes)`,
       mark as drifted.
  3. If drifted set is empty, exit 0.
  4. If drifted, print one line per drifted relpath to stdout, exit 1.
  5. Exit non-zero on missing pack.toml or render failure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle import render, safety
from agentbundle.commands._common import check_spec_version_gate
from agentbundle.config import ConfigError, load_pack_toml


def run(args: argparse.Namespace) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    pack_path = Path(args.pack_path).resolve()
    root = Path(args.root).resolve()
    cli_scope: str | None = getattr(args, "scope", None)

    # ── Multi-scope disambiguator (RFC-0004) ──────────────────────────────────
    # diff is read-only but still subject to the --scope rule: pick which
    # scope's projection to compare against. If the pack is at both
    # scopes, --scope is required.
    from agentbundle import scope as scope_mod
    from agentbundle.config import load_state

    # Best-effort pack name lookup from pack.toml for the multi-scope check.
    try:
        pack_toml_data = load_pack_toml(pack_path / "pack.toml")
        pack_name = pack_toml_data.get("pack", {}).get("name", "")
    except ConfigError:
        pack_name = ""

    installed_at_repo = False
    installed_at_user = False
    user_root_resolved: Path | None = None
    if pack_name:
        repo_state_for_check = load_state(root / ".agent-ready-state.toml")
        installed_at_repo = pack_name in repo_state_for_check.packs
        try:
            user_root_resolved = scope_mod.resolve_user_root()
            user_state_for_check = load_state(
                user_root_resolved / ".agent-ready" / "state.toml"
            )
            installed_at_user = pack_name in user_state_for_check.packs
        except scope_mod.UserScopeUnresolvable:
            pass

        if installed_at_repo and installed_at_user and cli_scope is None:
            print(
                f"diff: {pack_name} installed at multiple scopes; "
                "pass --scope {repo, user}",
                file=sys.stderr,
            )
            return 1

        if cli_scope == "user" or (
            cli_scope is None and installed_at_user and not installed_at_repo
        ):
            if user_root_resolved is None:
                print(
                    "diff: cannot resolve user scope: $HOME unset or invalid",
                    file=sys.stderr,
                )
                return 1
            root = user_root_resolved

    if not (pack_path / "pack.toml").exists():
        print(
            f"error: no pack.toml found at {pack_path}",
            file=sys.stderr,
        )
        return 1

    try:
        gate = check_spec_version_gate(load_pack_toml(pack_path / "pack.toml"))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if gate is not None:
        return gate

    try:
        rendered: dict[str, bytes] = render.render_pack(pack_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: render failed for pack at '{pack_path}': {exc}", file=sys.stderr)
        return 1

    drifted: list[str] = []
    for relpath, expected_bytes in sorted(rendered.items()):
        on_disk = root / relpath
        if not on_disk.exists():
            drifted.append(relpath)
            continue
        expected_sha = safety.sha256_bytes(expected_bytes)
        actual_sha = safety.sha256_file(on_disk)
        if expected_sha != actual_sha:
            drifted.append(relpath)

    if not drifted:
        return 0

    for path in drifted:
        print(path)
    return 1
