"""``agentbundle catalogue build`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    from agentbundle.catalogue_tooling.build import build_catalogue

    root = Path(getattr(args, "root", ".")).resolve()
    output_str = getattr(args, "output", None)
    output = Path(output_str).resolve() if output_str else None
    pack = getattr(args, "pack", None)
    recipe = getattr(args, "recipe", None)
    fmt = getattr(args, "format", "table")

    try:
        result = build_catalogue(root, output=output, pack=pack, recipe=recipe)
    except ValueError as exc:
        print(f"catalogue build: {exc}", file=sys.stderr)
        return 1

    if fmt == "json":
        doc = {
            "schema_version": result.schema_version,
            "command": result.command,
            "operation": result.operation,
            "agentbundle_version": result.agentbundle_version,
            "catalogue_schema_version": result.catalogue_schema_version,
            "ok": result.ok,
            "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
        }
        print(json.dumps(doc, indent=2))
    else:
        status = "ok" if result.ok else "FAIL"
        print(f"catalogue build: {status}", file=sys.stderr)

    return 0 if result.ok else 1
