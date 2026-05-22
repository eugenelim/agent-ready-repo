"""``agentbundle list-packs`` subcommand.

Resolves a catalogue URI, enumerates every ``packs/*/pack.toml``, and prints
a stable table of name, version, description, and dependencies to stdout.

Catalogue layout accepted:
  - ``<root>/packs/<name>/pack.toml``  — standard catalogue layout.
  - ``<root>/<name>/pack.toml``        — root *is* the packs directory
    (every subdir with a pack.toml counts).

Exit codes:
  0  — success.
  1  — catalogue resolution error (one-line stderr from CatalogueError).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle list-packs``.

    Args:
        args.catalogue — catalogue URI (local path or git+https://...).

    Returns 0 on success, 1 on catalogue resolution failure.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.config import ConfigError, load_pack_toml

    catalogue_uri: str = args.catalogue

    # ── Resolve catalogue URI ──────────────────────────────────────────────────
    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"list-packs: {exc}", file=sys.stderr)
        return 1

    # ── Discover packs ────────────────────────────────────────────────────────
    pack_dirs = _discover_pack_dirs(catalogue_dir)
    if not pack_dirs:
        # Nothing to show is not an error; just print the (empty) header.
        _print_table([])
        return 0

    # ── Parse each pack.toml ──────────────────────────────────────────────────
    rows: list[dict] = []
    for pack_dir in pack_dirs:
        try:
            toml = load_pack_toml(pack_dir / "pack.toml")
        except ConfigError as exc:
            print(f"list-packs: skipping {pack_dir.name}: {exc}", file=sys.stderr)
            continue
        rows.append(_extract_row(toml))

    # Sort deterministically by pack name so output is stable across runs.
    rows.sort(key=lambda r: r["name"])
    _print_table(rows)
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _discover_pack_dirs(catalogue_dir: Path) -> list[Path]:
    """Return pack directories found under *catalogue_dir*.

    Tries ``<catalogue_dir>/packs/`` first (standard layout). If that
    directory doesn't exist or contains no packs, falls back to treating
    every direct subdirectory of *catalogue_dir* that contains a
    ``pack.toml`` as a pack.
    """
    packs_subdir = catalogue_dir / "packs"
    if packs_subdir.is_dir():
        candidates = [p for p in packs_subdir.iterdir() if p.is_dir()]
        found = [p for p in candidates if (p / "pack.toml").exists()]
        if found:
            return sorted(found, key=lambda p: p.name)

    # Fallback: catalogue root itself may be a packs directory.
    if catalogue_dir.is_dir():
        fallback = [
            p for p in catalogue_dir.iterdir()
            if p.is_dir() and (p / "pack.toml").exists()
        ]
        return sorted(fallback, key=lambda p: p.name)

    return []


def _extract_row(toml: dict) -> dict:
    """Pull display fields out of a parsed pack.toml dict."""
    pack = toml.get("pack", {})
    name = pack.get("name", "")
    version = pack.get("version", "")
    description = pack.get("description", "")

    # Dependencies: look for [[pack.dependencies.required]] and
    # [[pack.dependencies.recommended]].
    deps: list[str] = []
    dep_table = pack.get("dependencies", {})
    if isinstance(dep_table, dict):
        for kind in ("required", "recommended"):
            for entry in dep_table.get(kind, []) or []:
                if isinstance(entry, dict):
                    dep_name = entry.get("pack", "")
                    dep_version = entry.get("version", "")
                    dep_str = dep_name
                    if dep_version:
                        dep_str += f"@{dep_version}"
                    if dep_str:
                        deps.append(dep_str)

    return {
        "name": name,
        "version": version,
        "description": description,
        "dependencies": deps,
    }


def _print_table(rows: list[dict]) -> None:
    """Print a fixed-column table to stdout.

    Columns: name, version, description, dependencies.
    Output is deterministic: rows are already sorted by caller; column
    widths are derived from content so the table is alignment-stable.
    """
    headers = ["NAME", "VERSION", "DESCRIPTION", "DEPENDENCIES"]

    # Convert deps list to a display string.
    display_rows = [
        {
            "name": r["name"],
            "version": r["version"],
            "description": r["description"],
            "dependencies": ", ".join(r["dependencies"]) if r["dependencies"] else "-",
        }
        for r in rows
    ]

    # Compute column widths.
    col_keys = ["name", "version", "description", "dependencies"]
    widths = [len(h) for h in headers]
    for row in display_rows:
        for i, key in enumerate(col_keys):
            widths[i] = max(widths[i], len(row[key]))

    # Format string: left-justify each column.
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)

    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in display_rows:
        print(fmt.format(*(row[k] for k in col_keys)))
