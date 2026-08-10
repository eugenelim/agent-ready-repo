#!/usr/bin/env python3
"""Stdlib mirror of `commands/validate.py:_allowed_scopes`, shared by `tools/`.

`tools/` scripts must run from a clean checkout with no `agentbundle` on the
path, so they cannot import the canonical resolver. Before this module there
were four independent copies — one per script — with nothing keeping them in
step, so a change to `validate.py` would have silently desynced the publish gate
from the build.

One copy, and `tools/test-pack-scope.py` differentially tests it against the
canonical over the full contract-version x install-table matrix, skipping only
when `agentbundle` is genuinely unimportable.

The gate is `[pack.adapter-contract].version`, **not** `[pack.install]`: a pack
declaring `allowed-scopes` with no contract version resolves `["repo"]`.
"""

from __future__ import annotations


def allowed_scopes(pack_meta: dict) -> list[str]:
    """Resolve a parsed `pack.toml`'s install scopes."""
    pack = pack_meta.get("pack", {})
    if not isinstance(pack, dict):
        return ["repo"]
    contract = pack.get("adapter-contract")
    version = contract.get("version") if isinstance(contract, dict) else None
    if version is None or version == "0.1":
        return ["repo"]
    install = pack.get("install", {})
    if not isinstance(install, dict):
        return ["repo"]
    declared = install.get("allowed-scopes")
    if isinstance(declared, list) and declared:
        return [s for s in declared if isinstance(s, str)]
    default = install.get("default-scope")
    return [default] if isinstance(default, str) else ["repo"]


def is_user_capable(pack_meta: dict) -> bool:
    """Does this pack permit the user-scope install the plugin route offers?"""
    return "user" in allowed_scopes(pack_meta)
