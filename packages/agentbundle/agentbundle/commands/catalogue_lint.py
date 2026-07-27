"""``agentbundle catalogue lint`` and ``agentbundle lint packs`` handler."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    from agentbundle.catalogue_tooling.lint import lint_catalogue, render_json, render_table

    root = Path(getattr(args, "root", ".")).resolve()
    pack = getattr(args, "pack", None)
    fmt = getattr(args, "format", "table")
    deep = getattr(args, "deep", False)

    try:
        result = lint_catalogue(root, pack=pack, deep=deep)
    except ImportError as exc:
        # PyYAML absent; --deep requires it
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if fmt == "json":
        print(render_json(result))
    else:
        table = render_table(result)
        print(table, file=sys.stderr)

    return 0 if result.ok else 1
