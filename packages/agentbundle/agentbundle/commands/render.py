"""`agentbundle render` — project a pack to --output via the F-build pipeline.

Option (b) from the task spec: call `render.render_pack()` in-memory,
then walk the dict-of-bytes and write each entry via `safety.write_jailed`.
This is the more defensive shape: the path-jail check fires on every write,
not just as a pre-flight.

The three RFC-0001 default recipes are run when --target is absent. When
--target is given, only recipes whose adapter matches the target are run
(the aggregate `marketplace` recipe has no adapter and is included unless
filtered by a named target that doesn't match it).
"""

from __future__ import annotations

import sys
from pathlib import Path

from agentbundle import render as _render
from agentbundle.build.main import DEFAULT_RECIPES, load_recipe
from agentbundle.safety import PathJailError, write_jailed


def run(args) -> int:
    """Entry point for `agentbundle render <pack_path> --output <dir> [--target <t>]`."""
    pack_path = Path(args.pack_path).resolve()
    output_dir = Path(args.output).resolve()

    # Validate pack_path
    if not (pack_path / "pack.toml").exists():
        print(
            f"render: no pack.toml found at {pack_path}",
            file=sys.stderr,
        )
        return 1

    # Determine recipe set
    recipes = _select_recipes(getattr(args, "target", None))
    if recipes is None:
        # Unknown target
        from agentbundle.build.adapters import ADAPTERS

        known = sorted(ADAPTERS.keys())
        target = getattr(args, "target", None)
        print(
            f"render: unknown target {target!r}; known targets: {', '.join(known)}",
            file=sys.stderr,
        )
        return 1

    # Render in-memory
    try:
        file_tree = _render.render_pack(pack_path, recipes=recipes)
    except FileNotFoundError as exc:
        print(f"render: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"render: schema error: {exc}", file=sys.stderr)
        return 1

    # Write each file via write_jailed (path-jail is non-optional)
    output_dir.mkdir(parents=True, exist_ok=True)
    for relpath, content in sorted(file_tree.items()):
        try:
            write_jailed(output_dir, relpath, content)
        except PathJailError as exc:
            print(f"render: {exc}", file=sys.stderr)
            return 1
        print(relpath)

    return 0


def _select_recipes(target: str | None) -> list[str] | None:
    """Return the recipe list for the given target (or DEFAULT_RECIPES if None).

    Returns None if the target is specified but unknown.
    """
    if target is None:
        return list(DEFAULT_RECIPES)

    # Validate target against known adapters
    from agentbundle.build.adapters import ADAPTERS

    # ADAPTERS uses hyphenated contract names (claude-code, kiro, copilot, codex, apm)
    # The registry uses Python module names (claude_code, kiro, copilot, codex).
    # Accept both forms for usability.
    normalised = target.replace("-", "_")
    known_hyphenated = set(ADAPTERS.keys()) | {"apm"}
    known_underscored = {k.replace("-", "_") for k in known_hyphenated}

    if target not in known_hyphenated and normalised not in known_underscored:
        return None

    # Canonicalise to hyphenated form for recipe adapter field comparison.
    canonical = target if target in known_hyphenated else target.replace("_", "-")

    # Filter DEFAULT_RECIPES to those whose adapter matches, plus adapter-less recipes.
    selected: list[str] = []
    for recipe_name in DEFAULT_RECIPES:
        try:
            recipe = load_recipe(recipe_name)
        except FileNotFoundError:
            continue
        if recipe.adapter is None or recipe.adapter == canonical:
            selected.append(recipe_name)
    return selected
