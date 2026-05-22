"""Build pipeline: recipe loader, pack discovery, adapter dispatch,
marketplace aggregation.

Recipes live next to this module under `recipes/`. Each recipe carries
a `type` (`per-pack` | `aggregate` | `overlay` | `composite`) that
determines how the pipeline interprets it. RFC-0001 ships the first
three (per-pack-claude-plugin, per-pack-apm-package, marketplace); the
other three (per-pack-overlay, composite-agents-md, composite-marketplace)
are consumed by T7's self-host writer.

Pack discovery globs the configured `--packs-dir` for subdirectories
whose `pack.toml` validates. Pack-internal name collisions (two
primitives with the same local name inside a single pack) are rejected
before any adapter runs, with a stderr message naming both source
paths.
"""

from __future__ import annotations

import json
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.build.validate import validate as validate_instance

PACKAGE_ROOT = Path(__file__).resolve().parent
RECIPES_DIR = PACKAGE_ROOT / "recipes"
REPO_ROOT = PACKAGE_ROOT.parent.parent.parent.parent
CONTRACT_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"
PACK_SCHEMA_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "pack-schema.json"
PLUGIN_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "specs" / "adapter-contract" / "plugin-manifest-schema.json"
)
PRIMITIVE_DIRS = ("skills", "agents", "hooks", "hook-wiring", "commands")

# The three RFC-0001 recipes that plain `make build` invokes.
# RFC-0002 recipes (per-pack-overlay, composite-agents-md,
# composite-marketplace) fire only under --self.
DEFAULT_RECIPES = (
    "per-pack-claude-plugin",
    "per-pack-apm-package",
    "marketplace",
)


@dataclass
class Recipe:
    name: str
    type: str
    adapter: str | None
    output_subdir: str | None
    input_subdir: str | None
    output_file: str | None
    units: list[str]
    fragment_path: str | None
    manifest_path: str | None


@dataclass
class Pack:
    name: str
    path: Path


def load_recipe(name: str, recipes_dir: Path = RECIPES_DIR) -> Recipe:
    recipe_path = recipes_dir / f"{name}.toml"
    if not recipe_path.exists():
        raise FileNotFoundError(f"recipe {name!r} not found at {recipe_path}")
    return _parse_recipe(recipe_path)


def load_recipe_from_path(path: Path) -> Recipe:
    return _parse_recipe(path)


def _parse_recipe(path: Path) -> Recipe:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    body = data["recipe"]
    return Recipe(
        name=body["name"],
        type=body["type"],
        adapter=body.get("adapter"),
        output_subdir=body.get("output-subdir"),
        input_subdir=body.get("input-subdir"),
        output_file=body.get("output-file"),
        units=body.get("units", []),
        fragment_path=body.get("fragment-path"),
        manifest_path=body.get("manifest-path"),
    )


def discover_packs(packs_dir: Path) -> list[Pack]:
    if not packs_dir.exists():
        return []
    packs: list[Pack] = []
    for entry in sorted(packs_dir.iterdir()):
        if entry.is_dir() and (entry / "pack.toml").exists():
            validate_pack_metadata(entry / "pack.toml")
            packs.append(Pack(name=entry.name, path=entry))
    return packs


def validate_pack_metadata(pack_toml_path: Path) -> None:
    """Validate a pack.toml against pack-schema.json. Raise on errors."""
    metadata = tomllib.loads(pack_toml_path.read_text(encoding="utf-8"))
    schema = json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = validate_instance(metadata, schema)
    if errors:
        raise ValueError(
            f"pack metadata at {pack_toml_path} failed schema: "
            + "; ".join(errors)
        )


def validate_plugin_manifest(plugin_json_path: Path) -> None:
    """Validate a per-pack .claude-plugin/plugin.json against schema."""
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    schema = json.loads(PLUGIN_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = validate_instance(manifest, schema)
    if errors:
        raise ValueError(
            f"plugin manifest at {plugin_json_path} failed schema: "
            + "; ".join(errors)
        )


def validate_pack_uniqueness(pack: Pack) -> None:
    """Raise if a pack has two primitives with the same local name.

    The local name is the stem for most primitives, except `hooks` where
    `.sh` and `.py` are both legal (the spec § Hook extensions makes both
    valid in `packs/<pack>/.apm/hooks/`) — so for hooks we key by the
    full filename so `baz.sh` and `baz.py` coexist.
    """
    apm_root = pack.path / ".apm"
    if not apm_root.exists():
        return
    seen: dict[str, Path] = {}
    for primitive_dir_name in PRIMITIVE_DIRS:
        primitive_dir = apm_root / primitive_dir_name
        if not primitive_dir.exists():
            continue
        for child in primitive_dir.iterdir():
            local_name = child.name if primitive_dir_name == "hooks" else child.stem
            key = f"{primitive_dir_name}:{local_name}"
            if key in seen:
                raise ValueError(
                    f"pack {pack.name!r}: duplicate primitive {key!r} — "
                    f"{seen[key]} and {child}"
                )
            seen[key] = child


def run_recipe(
    recipe: Recipe,
    packs: Iterable[Pack],
    output_dir: Path,
    contract: dict,
) -> dict:
    """Execute a recipe and return a description of what it produced."""
    packs_list = list(packs)
    for pack in packs_list:
        validate_pack_uniqueness(pack)

    if recipe.type == "per-pack":
        return _run_per_pack(recipe, packs_list, output_dir, contract)
    if recipe.type == "aggregate":
        return _run_aggregate(recipe, output_dir)
    if recipe.type == "overlay":
        return _run_overlay(recipe, packs_list)
    if recipe.type == "composite":
        return _run_composite(recipe, packs_list)
    raise ValueError(f"unknown recipe type {recipe.type!r}")


def _assert_under(target: Path, base: Path) -> None:
    """Refuse if `target.resolve()` would escape `base.resolve()`.

    Defense-in-depth against traversal in recipe `output-subdir` and
    contract `target-path` values. Repo-owned today; the CLI accepts
    external recipe paths via `--recipe path.toml`, so this guard is
    load-bearing the moment an operator points the CLI at untrusted TOML.
    """
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    try:
        target_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"refusing to write outside output root: {target_resolved} not under {base_resolved}"
        ) from exc


def _run_per_pack(
    recipe: Recipe, packs: list[Pack], output_dir: Path, contract: dict
) -> dict:
    if recipe.adapter == "apm":
        return _run_per_pack_apm(recipe, packs, output_dir)
    if recipe.adapter not in ADAPTERS:
        raise ValueError(f"unknown adapter target {recipe.adapter!r}")
    if recipe.adapter not in contract["adapter"]:
        raise ValueError(
            f"adapter {recipe.adapter!r} declared in recipe but not in contract"
        )
    project = ADAPTERS[recipe.adapter]
    produced: dict[str, str] = {}
    for pack in packs:
        per_pack_output = output_dir / recipe.output_subdir / pack.name
        _assert_under(per_pack_output, output_dir)
        per_pack_output.mkdir(parents=True, exist_ok=True)
        project(pack.path, contract, per_pack_output)
        plugin_manifest = pack.path / ".claude-plugin" / "plugin.json"
        if plugin_manifest.exists():
            validate_plugin_manifest(plugin_manifest)
            destination = per_pack_output / ".claude-plugin" / "plugin.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(plugin_manifest, destination, follow_symlinks=False)
        produced[pack.name] = str(per_pack_output)
    return {"recipe": recipe.name, "type": recipe.type, "produced": produced}


def _run_per_pack_apm(recipe: Recipe, packs: list[Pack], output_dir: Path) -> dict:
    produced: dict[str, str] = {}
    for pack in packs:
        per_pack_output = output_dir / recipe.output_subdir / pack.name
        _assert_under(per_pack_output, output_dir)
        per_pack_output.mkdir(parents=True, exist_ok=True)
        pack_metadata = tomllib.loads((pack.path / "pack.toml").read_text(encoding="utf-8"))
        (per_pack_output / "apm.yml").write_text(
            _render_apm_yml(pack_metadata.get("pack", {})),
            encoding="utf-8",
        )
        apm_source = pack.path / ".apm"
        if apm_source.exists():
            apm_dest = per_pack_output / ".apm"
            if apm_dest.exists():
                shutil.rmtree(apm_dest)
            # symlinks=True preserves symlinks as symlinks rather than
            # dereferencing them — a pack containing a symlink to /etc/passwd
            # cannot exfiltrate the target into the published dist/ tree.
            shutil.copytree(apm_source, apm_dest, symlinks=True)
        produced[pack.name] = str(per_pack_output)
    return {"recipe": recipe.name, "type": recipe.type, "produced": produced}


def _render_apm_yml(pack_metadata: dict) -> str:
    """Render the per-pack APM package metadata.

    Stdlib-only — no PyYAML. Values are JSON-encoded scalars (YAML is
    a JSON superset, so a JSON-quoted string is always a valid YAML
    scalar). This blocks YAML-key injection from a pack name or
    description containing newlines or YAML control characters.
    """
    lines = [
        f"name: {json.dumps(pack_metadata.get('name', ''))}",
        f"version: {json.dumps(pack_metadata.get('version', '0.0.0'))}",
    ]
    description = pack_metadata.get("description")
    if description:
        lines.append(f"description: {json.dumps(description)}")
    return "\n".join(lines) + "\n"


def _run_aggregate(recipe: Recipe, output_dir: Path) -> dict:
    input_dir = output_dir / recipe.input_subdir
    entries: list[dict] = []
    if input_dir.exists():
        for plugin_dir in sorted(input_dir.iterdir()):
            manifest = plugin_dir / ".claude-plugin" / "plugin.json"
            if manifest.exists():
                entries.append(json.loads(manifest.read_text(encoding="utf-8")))
    output_path = output_dir / recipe.output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"plugins": entries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"recipe": recipe.name, "type": recipe.type, "entries": len(entries)}


def _run_overlay(recipe: Recipe, packs: list[Pack]) -> dict:
    expansion = {
        pack.name: [str(pack.path / unit.rstrip("/")) for unit in recipe.units]
        for pack in packs
    }
    return {"recipe": recipe.name, "type": recipe.type, "expansion": expansion}


def _run_composite(recipe: Recipe, packs: list[Pack]) -> dict:
    composed: list[str] = []
    for pack in packs:
        target = pack.path / (recipe.fragment_path or recipe.manifest_path or "")
        if target.exists():
            composed.append(str(target))
    return {"recipe": recipe.name, "type": recipe.type, "composed": composed}


def run_default_build(
    packs_dir: Path, output_dir: Path, contract: dict | None = None
) -> list[dict]:
    """Run the three RFC-0001 recipes — what plain `make build` invokes."""
    if contract is None:
        contract = load_contract(CONTRACT_PATH)
    packs = discover_packs(packs_dir)
    results: list[dict] = []
    for recipe_name in DEFAULT_RECIPES:
        recipe = load_recipe(recipe_name)
        results.append(run_recipe(recipe, packs, output_dir, contract))
    return results


def cmd_build(args) -> int:
    """argparse entrypoint for the `build` subcommand."""
    output_dir = Path(args.output_dir).resolve()
    packs_dir = Path(args.packs_dir).resolve()
    try:
        contract = load_contract(CONTRACT_PATH)
    except Exception as exc:
        print(f"build: failed to load contract: {exc}", file=sys.stderr)
        return 1

    if args.recipe:
        try:
            if "/" in args.recipe or args.recipe.endswith(".toml"):
                recipe = load_recipe_from_path(Path(args.recipe))
            else:
                recipe = load_recipe(args.recipe)
        except FileNotFoundError as exc:
            print(f"build: {exc}", file=sys.stderr)
            return 1
        try:
            packs = discover_packs(packs_dir)
            if args.pack:
                packs = [p for p in packs if p.name == args.pack]
            run_recipe(recipe, packs, output_dir, contract)
        except ValueError as exc:
            print(f"build: {exc}", file=sys.stderr)
            return 1
        return 0

    # Default `build` (no --recipe): run the three RFC-0001 recipes.
    try:
        run_default_build(packs_dir, output_dir, contract)
    except ValueError as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 1
    return 0
