"""Thin wrapper around `agentbundle.build` — the library-first render API.

The CLI's `render`, `scaffold`, `install`, and `upgrade` subcommands all
route their projection work through this module so there is exactly one
implementation of "produce the projected output tree for a pack" in the
codebase.

Two surfaces:

  - `render_pack_to_dir(pack_path, output_dir, contract=None)` — runs the
    same three RFC-0001 recipes that `make build` runs (per-pack
    claude-plugin, per-pack apm-package, marketplace) and writes them
    into `output_dir`. Byte-identical to `make build`.

  - `render_pack(pack_path, contract=None)` — same projection, but
    materialised in a tempdir and returned as a `dict[str, bytes]`
    keyed by path-relative-to-the-tempdir. Caller is responsible for
    deciding where (or whether) to write the bytes. Used by `diff`,
    `install`, `upgrade`, and the F-build parity test.

Adapter target enumeration lives at `list_adapters()`; it queries the
runtime registry at `agentbundle.build.adapters` so adding an adapter
to the registry adds it to `agentbundle list-targets` automatically.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Sequence

from agentbundle.build import adapters as _adapters
from agentbundle.build.contract import load as _load_contract
from agentbundle.build.main import (
    CONTRACT_PATH,
    DEFAULT_RECIPES,
    Pack,
    discover_packs,
    load_recipe,
    run_recipe,
    validate_pack_metadata,
)


def list_adapters() -> Sequence[str]:
    """Return the adapter names the CLI ships against, in stable sort order."""
    return sorted(_adapters.registry.keys())


def _resolve_contract(contract: dict | None) -> dict:
    return contract if contract is not None else _load_contract(CONTRACT_PATH)


def _pack_from_path(pack_path: Path) -> Pack:
    pack_path = pack_path.resolve()
    if not (pack_path / "pack.toml").exists():
        raise FileNotFoundError(f"no pack.toml at {pack_path}")
    validate_pack_metadata(pack_path / "pack.toml")
    return Pack(name=pack_path.name, path=pack_path)


def render_pack_to_dir(
    pack_path: Path,
    output_dir: Path,
    *,
    contract: dict | None = None,
    recipes: Sequence[str] = DEFAULT_RECIPES,
) -> None:
    """Render a single pack to `output_dir` using the named recipes.

    `output_dir` is created if absent. The three default recipes match
    what `make build` runs; the F-build parity test pins this.
    """
    pack = _pack_from_path(pack_path)
    contract_data = _resolve_contract(contract)
    output_dir.mkdir(parents=True, exist_ok=True)
    for recipe_name in recipes:
        recipe = load_recipe(recipe_name)
        run_recipe(recipe, [pack], output_dir, contract_data)


def render_pack(
    pack_path: Path,
    *,
    contract: dict | None = None,
    recipes: Sequence[str] = DEFAULT_RECIPES,
) -> dict[str, bytes]:
    """Render a pack to a tempdir and return its bytes keyed by relpath.

    Bytes — not str — because hook bodies may be non-UTF-8 binaries in
    principle (and because `bytes` is the right shape for hash + write).
    """
    with tempfile.TemporaryDirectory() as raw:
        out = Path(raw)
        render_pack_to_dir(pack_path, out, contract=contract, recipes=recipes)
        return _collect_tree(out)


def render_packs_to_dir(
    packs_dir: Path,
    output_dir: Path,
    *,
    contract: dict | None = None,
    recipes: Sequence[str] = DEFAULT_RECIPES,
) -> None:
    """Render every pack under `packs_dir` — the full `make build` shape."""
    contract_data = _resolve_contract(contract)
    packs = discover_packs(packs_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for recipe_name in recipes:
        recipe = load_recipe(recipe_name)
        run_recipe(recipe, packs, output_dir, contract_data)


def _collect_tree(root: Path) -> dict[str, bytes]:
    """Walk `root` and return every file's bytes keyed by relpath (POSIX-style)."""
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relpath = path.relative_to(root).as_posix()
            out[relpath] = path.read_bytes()
    return out
