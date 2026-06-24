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
    from agentbundle.commands._common import check_spec_version_gate

    rows: list[dict] = []
    for pack_dir in pack_dirs:
        try:
            toml = load_pack_toml(pack_dir / "pack.toml")
        except ConfigError as exc:
            print(f"list-packs: skipping {pack_dir.name}: {exc}", file=sys.stderr)
            continue
        # Spec-version gate per pack; refuse cataloguing an incompatible
        # pack with a uniform message rather than silently listing it.
        if check_spec_version_gate(toml) is not None:
            return 1
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


def _render_identity(pack: dict) -> str:
    """Render a pack's canonical identity for display (enriched-pack-manifest).

    `@<catalogue>/<name>` when the optional `[pack].catalogue` is declared,
    the bare `<name>` otherwise. **Declare-only**: this is a presentation
    helper — it performs no catalogue resolution and does not touch
    ``catalogue.py``. Single-catalogue resolution in ``list-packs`` /
    ``install`` is unchanged (RFC-0031 D7).
    """
    name = pack.get("name", "")
    catalogue = pack.get("catalogue")
    if isinstance(catalogue, str) and catalogue:
        return f"@{catalogue}/{name}"
    return name


def _extract_row(toml: dict) -> dict:
    """Pull display fields out of a parsed pack.toml dict."""
    pack = toml.get("pack", {})
    name = _render_identity(pack)
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
    """Print the pack table to stdout.

    Columns: name, version, description, dependencies. Rows arrive sorted from
    the caller; column widths are content-derived so the table is
    alignment-stable. The long DESCRIPTION column word-wraps to fit an
    interactive terminal — see ``_common.render_table`` for the TTY / non-TTY
    contract.
    """
    from agentbundle.commands._common import render_table

    headers = ["NAME", "VERSION", "DESCRIPTION", "DEPENDENCIES"]
    table_rows = [
        [
            r["name"],
            r["version"],
            r["description"],
            ", ".join(r["dependencies"]) if r["dependencies"] else "-",
        ]
        for r in rows
    ]
    render_table(headers, table_rows, wrap_col=2)
