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


def run(args: argparse.Namespace) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    pack_path = Path(args.pack_path).resolve()
    root = Path(args.root).resolve()

    if not (pack_path / "pack.toml").exists():
        print(
            f"error: no pack.toml found at {pack_path}",
            file=sys.stderr,
        )
        return 1

    try:
        rendered: dict[str, bytes] = render.render_pack(pack_path)
    except Exception as exc:  # noqa: BLE001
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
