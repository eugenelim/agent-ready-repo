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


def _bundled_or_repo(name: str) -> Path:
    """Locate a data file shipped under both `agentbundle/_data/` and
    `<repo>/docs/contracts/`.

    Prefer the bundled copy when present on disk (works in a `pip install`
    and a dev checkout); fall back to the repo path for dev checkouts
    whose `_data/` hasn't been synced. Inside a `zipapp` neither path is
    a real filesystem location — callers should use `_read_bundled` to
    get the text content instead of trying to open the returned Path.
    """
    bundled = PACKAGE_ROOT.parent / "_data" / name
    if bundled.exists():
        return bundled
    return REPO_ROOT / "docs" / "contracts" / name


def _read_bundled(name: str) -> str:
    """Read a packaged data file, transparently handling the zipapp case.

    Resolution order:
      1. `<package>/_data/<name>` via `importlib.resources` — works for
         filesystem installs AND inside a `zipapp` archive.
      2. `<repo>/docs/contracts/<name>` — dev fallback for source trees
         whose `_data/` hasn't been populated.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath(f"_data/{name}")
        if resource.is_file():
            return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return (REPO_ROOT / "docs" / "contracts" / name).read_text(encoding="utf-8")


CONTRACT_PATH = _bundled_or_repo("adapter.toml")
PACK_SCHEMA_PATH = _bundled_or_repo("pack.schema.json")
PLUGIN_MANIFEST_SCHEMA_PATH = _bundled_or_repo("plugin-manifest.schema.json")
PRIMITIVE_DIRS = ("skills", "agents", "hooks", "hook-wiring", "commands")

# The canonical SessionStart hook command synthesised into each derived
# plugin.json (claude-plugins route). Shell-exec contract (AC9 sub-assertion):
# when CLAUDE_PLUGIN_ROOT is substituted the double-quoted path survives
# spaces. The trailing `--install-route claude-plugins` flag is required by
# the writer's argparse (apm-install-route-parity AC2/AC8); the build
# pipeline and the projected command stay coupled at projection time via
# `make build` so a refreshed writer always ships next to a refreshed
# command — see RFC-0010 / spec apm-install-route-parity §Rollout.
_SESSION_START_COMMAND = (
    'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'
    ' --install-route claude-plugins'
)

# The canonical APM-route SessionStart hook command synthesised into each
# derived dist/apm/<pack>/.apm/hooks/install-marker.json. APM's HookIntegrator
# rewrites ${PLUGIN_ROOT} to per-target tokens (${CLAUDE_PLUGIN_ROOT},
# ${CURSOR_PLUGIN_ROOT}, …); the writer's data-directory shim resolves the
# hash-file location per spec AC3 precedence.
_SESSION_START_COMMAND_APM = (
    'python3 "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"'
    ' --install-route apm'
)

# JSON shape emitted into dist/apm/<pack>/.apm/hooks/install-marker.json
# (spec AC7). Authored as a Python dict so json.dumps controls indentation.
_APM_INSTALL_MARKER_HOOK_JSON = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": _SESSION_START_COMMAND_APM,
                        "timeout": 10,
                    }
                ]
            }
        ]
    }
}


def _read_install_marker_template() -> bytes:
    """Read the canonical install-marker.py template as bytes.

    Resolution order (mirrors _read_bundled pattern):
      1. `<package>/_data/install-marker.py` via importlib.resources — works
         for filesystem installs AND inside a zipapp archive.
      2. `<repo>/packages/agentbundle/templates/install-marker.py` — dev
         fallback for source trees.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/install-marker.py")
        if resource.is_file():
            return resource.read_bytes()
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return (REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py").read_bytes()


def _project_pack_readme(pack_path: Path, per_pack_output: Path) -> None:
    """Copy a pack's ``README.md`` into its per-pack dist route, if present.

    enriched-pack-manifest T5: the README is the sole portable per-pack doc,
    and the manifest's ``readme = "README.md"`` pointer resolves relative to
    the route directory. A pack without a README projects none and does not
    error (the ``readme`` field is then simply absent / unresolved — never a
    build failure). ``follow_symlinks=False`` mirrors the pack.toml copy so a
    symlinked README is not dereferenced into ``dist/`` at build time.
    """
    readme_src = pack_path / "README.md"
    if readme_src.is_file():
        shutil.copy2(
            readme_src, per_pack_output / "README.md", follow_symlinks=False
        )


def validate_derived_plugin_manifest_dict(manifest: dict, label: str = "<derived>") -> None:
    """Validate an in-memory derived plugin manifest dict against the derived schema.

    Call this BEFORE writing to disk so a synthesis bug does not land a
    malformed plugin.json in dist/ (Blocker-3: pre-write validation).
    """
    schema = json.loads(_read_bundled("plugin-manifest.derived.schema.json"))
    errors = validate_instance(manifest, schema)
    if errors:
        raise ValueError(
            f"derived plugin manifest {label} failed schema: "
            + "; ".join(errors)
        )


def validate_derived_plugin_manifest(plugin_json_path: Path) -> None:
    """Validate a derived .claude-plugin/plugin.json (with synthesised hooks) against derived schema.

    Defence-in-depth: also available as validate_derived_plugin_manifest_dict
    for pre-write validation before the file is written to disk.
    """
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    validate_derived_plugin_manifest_dict(manifest, label=str(plugin_json_path))


def derive_projectable_subset(pack_toml: dict) -> dict:
    """Map a parsed ``pack.toml`` to the projectable plugin-manifest subset.

    enriched-pack-manifest (RFC-0031 / ADR-0021): ``pack.toml`` is the rich
    metadata source of truth; the build projects a *lossy*, schema-compliant
    subset into the claude-plugins + apm routes (the ``plugin.json`` /
    ``marketplace.json`` entry). Fixed mapping:

      - ``author``      ← first ``[[pack.maintainers]]``, rendered
        ``"Name <email>"`` (name alone when no email).
      - ``license``     ← ``[pack].license`` (verbatim).
      - ``homepage``    ← ``[pack.links].homepage`` (verbatim).
      - ``repository``  ← ``[pack.links].repository`` (verbatim).
      - ``keywords``    ← ``[pack].keywords`` (string entries, verbatim).
      - ``category``    ← ``categories[0]``.
      - ``displayName`` ← ``[pack].display_name``.

    **Emit-only-when-present** is the load-bearing invariant: a key appears in
    the output only when its source field is present and non-empty, so a
    legacy ``pack.toml`` declaring none of the enriched fields yields ``{}``
    and the projected manifest is byte-identical to the pre-enrichment output
    (legacy-invariance AC). This is a pure function — no I/O, no schema read.
    """
    pack = pack_toml.get("pack", {})
    if not isinstance(pack, dict):
        return {}
    out: dict = {}

    maintainers = pack.get("maintainers")
    if isinstance(maintainers, list) and maintainers:
        first = maintainers[0]
        if isinstance(first, dict):
            name = first.get("name")
            email = first.get("email")
            if isinstance(name, str) and name:
                if isinstance(email, str) and email:
                    out["author"] = f"{name} <{email}>"
                else:
                    out["author"] = name

    license_ = pack.get("license")
    if isinstance(license_, str) and license_:
        out["license"] = license_

    links = pack.get("links")
    if isinstance(links, dict):
        homepage = links.get("homepage")
        if isinstance(homepage, str) and homepage:
            out["homepage"] = homepage
        repository = links.get("repository")
        if isinstance(repository, str) and repository:
            out["repository"] = repository

    keywords = pack.get("keywords")
    if isinstance(keywords, list):
        kws = [k for k in keywords if isinstance(k, str) and k]
        if kws:
            out["keywords"] = kws

    categories = pack.get("categories")
    if isinstance(categories, list) and categories:
        first_cat = categories[0]
        if isinstance(first_cat, str) and first_cat:
            out["category"] = first_cat

    display_name = pack.get("display_name")
    if isinstance(display_name, str) and display_name:
        out["displayName"] = display_name

    return out

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
    """Load a recipe by name.

    Tries the filesystem first (dev/install case), then falls back to
    `importlib.resources` (zipapp case where the package contents live
    inside a `.pyz` archive that `Path.exists()` cannot traverse).
    """
    recipe_path = recipes_dir / f"{name}.toml"
    if recipe_path.exists():
        return _parse_recipe_text(recipe_path.read_text(encoding="utf-8"))
    # Zipapp fallback: read via importlib.resources.
    try:
        from importlib.resources import files

        resource = files("agentbundle.build").joinpath(f"recipes/{name}.toml")
        if resource.is_file():
            return _parse_recipe_text(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    raise FileNotFoundError(f"recipe {name!r} not found at {recipe_path}")


def load_recipe_from_path(path: Path) -> Recipe:
    return _parse_recipe(path)


def _parse_recipe(path: Path) -> Recipe:
    return _parse_recipe_text(path.read_text(encoding="utf-8"))


def _parse_recipe_text(toml_text: str) -> Recipe:
    data = tomllib.loads(toml_text)
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
    """Validate a pack.toml against pack.schema.json. Raise on errors."""
    metadata = tomllib.loads(pack_toml_path.read_text(encoding="utf-8"))
    schema = json.loads(_read_bundled("pack.schema.json"))
    errors = validate_instance(metadata, schema)
    if errors:
        raise ValueError(
            f"pack metadata at {pack_toml_path} failed schema: "
            + "; ".join(errors)
        )


def validate_plugin_manifest(plugin_json_path: Path) -> None:
    """Validate a per-pack .claude-plugin/plugin.json against schema."""
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    schema = json.loads(_read_bundled("plugin-manifest.schema.json"))
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
        try:
            _run_per_pack_single(
                pack, recipe, project, output_dir, contract, produced
            )
        except Exception as exc:
            # Concern-9: surface the pack name so the operator knows which pack failed.
            raise RuntimeError(f"pack {pack.name!r}: {exc}") from exc
    return {"recipe": recipe.name, "type": recipe.type, "produced": produced}


def _run_per_pack_single(
    pack: Pack,
    recipe: Recipe,
    project,
    output_dir: Path,
    contract: dict,
    produced: dict[str, str],
) -> None:
    """Execute the derivation pipeline for a single pack."""
    per_pack_output = output_dir / recipe.output_subdir / pack.name
    _assert_under(per_pack_output, output_dir)
    # Transactional cleanup (Blocker-4): remove any prior partial or
    # crashed build so phantom files do not survive into this build.
    if per_pack_output.exists():
        shutil.rmtree(per_pack_output)
    per_pack_output.mkdir(parents=True, exist_ok=True)
    project(pack.path, contract, per_pack_output)
    plugin_manifest = pack.path / ".claude-plugin" / "plugin.json"
    if plugin_manifest.exists():
        # Validate source-tree manifest against the source schema
        # (forbids hooks; additionalProperties: false ensures any stray
        # hooks block is caught here before synthesis).
        validate_plugin_manifest(plugin_manifest)
        destination = per_pack_output / ".claude-plugin" / "plugin.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Load, splice in synthesised SessionStart hook, re-serialise.
        derived = json.loads(plugin_manifest.read_text(encoding="utf-8"))
        derived["hooks"] = {
            "SessionStart": [{"command": _SESSION_START_COMMAND}]
        }
        # enriched-pack-manifest: merge the projectable metadata subset derived
        # from this pack's pack.toml (emit-only-when-present, so a legacy pack
        # adds no keys and the output stays byte-identical).
        pack_toml_for_subset = pack.path / "pack.toml"
        if pack_toml_for_subset.exists():
            pack_meta = tomllib.loads(
                pack_toml_for_subset.read_text(encoding="utf-8")
            )
            derived.update(derive_projectable_subset(pack_meta))
        # Validate the derived manifest IN MEMORY before writing to disk
        # (Blocker-3: pre-write validation so a synthesis bug never lands
        # a malformed plugin.json in dist/).
        validate_derived_plugin_manifest_dict(
            derived, label=str(destination)
        )
        destination.write_text(
            json.dumps(derived, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        # Defence-in-depth: re-validate the written file against the schema
        # to catch any serialise/parse divergence introduced by json.dumps.
        validate_derived_plugin_manifest(destination)

    # Project pack.toml verbatim (writer reads it for name/version/allowed-scopes).
    pack_toml_src = pack.path / "pack.toml"
    if pack_toml_src.exists():
        shutil.copy2(pack_toml_src, per_pack_output / "pack.toml", follow_symlinks=False)

    # enriched-pack-manifest T5: project the pack's README.md into the route so
    # the manifest's `readme = "README.md"` pointer resolves. The README is the
    # sole portable per-pack doc. follow_symlinks=False mirrors the pack.toml
    # copy's posture (a symlinked README is not dereferenced into dist/).
    _project_pack_readme(pack.path, per_pack_output)

    # Project the canonical install-marker.py writer into scripts/.
    scripts_dir = per_pack_output / ".claude-plugin" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "install-marker.py").write_bytes(_read_install_marker_template())

    # Issue #190: ship the pack's seeds/ inside the plugin artifact so the
    # governance content travels with the pack on the Claude-plugin route
    # (RFC-0001 §281-284). symlinks=True preserves a seed symlink as a
    # symlink rather than dereferencing the build host's file into dist/
    # at build time — matching the APM recipe's copytree posture.
    seeds_src = pack.path / "seeds"
    if seeds_src.is_dir():
        shutil.copytree(seeds_src, per_pack_output / "seeds", symlinks=True)

    produced[pack.name] = str(per_pack_output)


def _run_per_pack_apm(recipe: Recipe, packs: list[Pack], output_dir: Path) -> dict:
    produced: dict[str, str] = {}
    writer_bytes = _read_install_marker_template()
    for pack in packs:
        per_pack_output = output_dir / recipe.output_subdir / pack.name
        _assert_under(per_pack_output, output_dir)
        # Transactional cleanup: remove any prior partial or crashed build
        # so phantom files do not survive into this build (mirrors the
        # claude-plugins derivation rail).
        if per_pack_output.exists():
            shutil.rmtree(per_pack_output)
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

        # apm-install-route-parity T4 / AC11: project install-marker
        # artifacts (writer + JSON hook) and pack.toml into the per-pack
        # output. The writer is byte-identical to the canonical template
        # — drift gate (AC16) enforces this at make build-check.
        hooks_dir = per_pack_output / ".apm" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "install-marker.py").write_bytes(writer_bytes)
        (hooks_dir / "install-marker.json").write_text(
            json.dumps(_APM_INSTALL_MARKER_HOOK_JSON, indent=2) + "\n",
            encoding="utf-8",
        )

        # Project pack.toml verbatim. The writer reads it for
        # name/version/allowed-scopes — same role as in the claude-plugins
        # derivation (spec AC11 c).
        pack_toml_src = pack.path / "pack.toml"
        if pack_toml_src.exists():
            shutil.copy2(
                pack_toml_src,
                per_pack_output / "pack.toml",
                follow_symlinks=False,
            )

        # enriched-pack-manifest T5: project the pack's README into the APM
        # route too (the sole portable per-pack doc; same posture as above).
        _project_pack_readme(pack.path, per_pack_output)

        # Issue #190 / RFC-0001 §595: ship the pack's seeds/ inside the APM
        # package so the governance content travels with the pack on the APM
        # route. symlinks=True preserves a seed symlink as a symlink rather
        # than dereferencing the build host's file into dist/ at build time.
        seeds_src = pack.path / "seeds"
        if seeds_src.is_dir():
            shutil.copytree(seeds_src, per_pack_output / "seeds", symlinks=True)

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
    _assert_under(input_dir, output_dir)
    entries: list[dict] = []
    if input_dir.exists():
        for plugin_dir in sorted(input_dir.iterdir()):
            manifest = plugin_dir / ".claude-plugin" / "plugin.json"
            if manifest.exists():
                entries.append(json.loads(manifest.read_text(encoding="utf-8")))
    output_path = output_dir / recipe.output_file
    _assert_under(output_path, output_dir)
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
        contract = tomllib.loads(_read_bundled("adapter.toml"))
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
        contract = tomllib.loads(_read_bundled("adapter.toml"))
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
