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
from agentbundle.commands._common import check_spec_version_gate, resolve_state_path
from agentbundle.config import ConfigError, load_pack_toml


def run(args: argparse.Namespace) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    pack_path = Path(args.pack_path).resolve()
    root = Path(args.root).resolve()
    cli_scope: str | None = getattr(args, "scope", None)
    cli_adapter: str | None = getattr(args, "adapter", None)

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
    repo_state_for_check = None
    user_state_for_check = None
    if pack_name:
        # A legacy (non-v0.4) state file is refused on read too (RFC-0052
        # hard cross-version refusal); surface it as a clean refuse rather
        # than a traceback.
        try:
            repo_state_for_check = load_state(resolve_state_path("repo", root))
        except ConfigError as exc:
            print(f"diff: {exc}", file=sys.stderr)
            return 1
        installed_at_repo = repo_state_for_check.has_pack(pack_name)
        try:
            user_root_resolved = scope_mod.resolve_user_root()
            user_state_for_check = load_state(
                resolve_state_path("user", user_root_resolved)
            )
            installed_at_user = user_state_for_check.has_pack(pack_name)
        except scope_mod.UserScopeUnresolvable:
            pass
        except ConfigError as exc:
            print(f"diff: {exc}", file=sys.stderr)
            return 1

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

    # Resolve effective scope and the matching pack_state (if any) so
    # the renderer below can mirror the shape install used. A pack can
    # carry multiple adapter rows at one scope (RFC-0052); pick the row
    # via --adapter, or infer when there is exactly one.
    effective_scope = "repo"
    pack_state = None
    if cli_scope == "user" or (
        cli_scope is None and installed_at_user and not installed_at_repo
    ):
        effective_scope = "user"
        _check_state = user_state_for_check
    else:
        _check_state = repo_state_for_check
    if _check_state is not None and pack_name:
        _rows = _check_state.rows_for_pack(pack_name)
        if cli_adapter is not None:
            pack_state = _rows.get(cli_adapter)
        elif len(_rows) == 1:
            pack_state = next(iter(_rows.values()))
        elif len(_rows) > 1:
            from agentbundle.commands._common import format_adapter_versions

            print(
                f"diff: {pack_name} installed for multiple adapters at "
                f"{effective_scope} scope; pass --adapter to pick one: "
                f"{format_adapter_versions(_rows)}",
                file=sys.stderr,
            )
            return 1

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

    # Pick the projection shape to compare against. RFC-0012 changed
    # install's default at repo scope from the dist-tree producer
    # (`render_pack`) to a per-IDE projection (`.claude/...`,
    # `.kiro/...`). Comparing on-disk per-IDE files against a dist-tree
    # render flags every per-IDE path as missing — exactly what makes
    # `agentbundle diff` useless after a v0.7+ install.
    #
    # Detection rule: if the pack is recorded in state, the install
    # itself tells us which shape landed:
    #   - state.files contains `apm/<pack>/...`, `claude-plugins/<pack>/...`,
    #     or `marketplace.json` → install used `--emit-install-routes`
    #     (legacy dist-tree); keep the dist-tree render.
    #   - otherwise → install used the RFC-0012 per-IDE path; render
    #     via `_render_for_repo_scope` / `_render_for_user_scope` with
    #     the recorded `state.adapter` as the hint.
    # When state has no row (a maintainer running diff against a fresh
    # render directory, the test_diff_cmd.py shape), fall back to the
    # dist-tree render — that's the catalogue-publishing surface.
    _use_dist_tree = pack_state is None or any(
        rp.startswith(("apm/", "claude-plugins/")) or rp == "marketplace.json"
        for rp in pack_state.files
    )
    try:
        if _use_dist_tree:
            rendered: dict[str, bytes] = render.render_pack(pack_path)
        else:
            import tomllib as _tomllib

            _pack_toml = _tomllib.loads(
                (pack_path / "pack.toml").read_text(encoding="utf-8")
            )
            _install_table = _pack_toml.get("pack", {}).get("install")
            _allowed_adapters = None
            if isinstance(_install_table, dict):
                _raw_aa = _install_table.get("allowed-adapters")
                if isinstance(_raw_aa, list):
                    _allowed_adapters = [s for s in _raw_aa if isinstance(s, str)]
            _contract_version = (
                _pack_toml.get("pack", {}).get("adapter-contract", {}).get("version")
                if isinstance(_pack_toml.get("pack", {}).get("adapter-contract"), dict)
                else None
            )
            if effective_scope == "user":
                from agentbundle.commands.install import (
                    _AdapterResolutionRefused,
                    _render_for_user_scope,
                )

                try:
                    rendered = _render_for_user_scope(
                        pack_path,
                        adapter=None,
                        allowed_adapters=_allowed_adapters,
                        contract_version=_contract_version,
                        state_adapter=pack_state.adapter,
                        command_name="diff",
                    )
                except _AdapterResolutionRefused as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
            else:
                from agentbundle.commands.install import (
                    _AdapterResolutionRefused,
                    _render_for_repo_scope,
                )

                try:
                    _adapter, rendered = _render_for_repo_scope(
                        pack_path,
                        adapter=None,
                        allowed_adapters=_allowed_adapters,
                        contract_version=_contract_version,
                        state_adapter=pack_state.adapter,
                        command_name="diff",
                    )
                except _AdapterResolutionRefused as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
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
