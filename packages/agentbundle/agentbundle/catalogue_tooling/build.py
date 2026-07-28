"""Catalogue build wrapper.

Spec: docs/specs/catalogue-tooling-build-self/spec.md (ini-005 Bucket 7).

Thin wrapper over agentbundle.build.main.cmd_build that exposes structured
result types and reads catalogue.toml defaults for output path and recipe.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from agentbundle.catalogue_tooling.config import load_catalogue_config
from agentbundle.catalogue_tooling.results import BuildResult

_AGENTBUNDLE_VERSION: str | None = None


def _get_agentbundle_version() -> str:
    global _AGENTBUNDLE_VERSION
    if _AGENTBUNDLE_VERSION is None:
        try:
            from agentbundle import __version__
            _AGENTBUNDLE_VERSION = __version__
        except Exception:
            _AGENTBUNDLE_VERSION = "unknown"
    return _AGENTBUNDLE_VERSION


def _validate_recipe_path(root: Path, recipe: str | None) -> None:
    """Raise ValueError for unsafe recipe paths (absolute, traversal, out-of-root)."""
    if recipe is None:
        return
    if not recipe:
        raise ValueError("recipe path must not be empty")
    rp = Path(recipe)
    # Reject absolute paths (Windows drive-absolute, POSIX absolute, or Unix-
    # style root on Windows where Path.is_absolute() returns False for "/foo").
    if rp.is_absolute() or (len(recipe) > 1 and recipe[1] == ":") or recipe.startswith("/"):
        raise ValueError(f"recipe path must be relative, not absolute: {recipe!r}")
    # Reject traversal
    if ".." in rp.parts:
        raise ValueError(f"recipe path must not traverse outside root: {recipe!r}")
    # Reject out-of-root via symlink or other resolution
    if recipe.endswith(".toml"):
        try:
            resolved = (root / recipe).resolve()
            if not resolved.is_relative_to(root.resolve()):
                raise ValueError(
                    f"recipe path escapes catalogue root: {recipe!r}"
                )
        except OSError as exc:
            raise ValueError(f"recipe path cannot be resolved: {recipe!r}: {exc}") from exc


def build_catalogue(
    root: Path,
    output: Path | None = None,
    pack: str | None = None,
    recipe: str | None = None,
) -> BuildResult:
    """Thin wrapper over agentbundle.build.main.cmd_build.

    Reads catalogue.toml defaults for output path and recipe when those
    arguments are None. When catalogue.toml is absent, existing hardcoded
    values in build/main.py are used unchanged.
    """
    import importlib
    # importlib.import_module uses sys.modules directly, bypassing the attribute
    # lookup that `import agentbundle.build.main as x` would do — which would
    # resolve to the `main()` function in build/__init__.py instead of the submodule.
    _build_main = importlib.import_module("agentbundle.build.main")
    from agentbundle.build.main import cmd_build

    config = load_catalogue_config(root)

    if output is None:
        build_output = config.paths.build_output if config else "dist"
        output = root / build_output

    if recipe is None and config and config.build.recipes:
        recipe = config.build.recipes[0]

    # "default" is a sentinel recognised by the config layer (see _BUNDLED_RECIPES)
    # meaning "run the default build (DEFAULT_RECIPES)".  Pass None so cmd_build
    # triggers its default-build path rather than trying to load a non-existent
    # default.toml recipe file.
    if recipe == "default":
        recipe = None

    _validate_recipe_path(root, recipe)

    packs_dir = root / (config.paths.packs if config else "packs")

    args = Namespace(
        output_dir=str(output),
        packs_dir=str(packs_dir),
        pack=pack,
        recipe=recipe,
    )

    # Temporarily override module-level constants when config is present.
    # Restored in finally to avoid cross-test pollution.
    saved_branch = _build_main._DIST_BRANCH  # type: ignore[attr-defined]
    saved_desc = _build_main._MARKETPLACE_DESCRIPTION  # type: ignore[attr-defined]
    try:
        if config and config.build.claude_plugin_branch:
            _build_main._DIST_BRANCH = config.build.claude_plugin_branch  # type: ignore[attr-defined]
        if config and config.build.marketplace_description:
            _build_main._MARKETPLACE_DESCRIPTION = config.build.marketplace_description  # type: ignore[attr-defined]

        rc = cmd_build(args)
    finally:
        _build_main._DIST_BRANCH = saved_branch  # type: ignore[attr-defined]
        _build_main._MARKETPLACE_DESCRIPTION = saved_desc  # type: ignore[attr-defined]

    return BuildResult(
        ok=(rc == 0),
        diagnostics=[],
        schema_version=1,
        command="catalogue build",
        operation="build",
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=config.schema if config else 1,
    )
