"""``agentbundle catalogue sync-defaults`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.defaults import check_defaults, write_defaults

    root = Path(getattr(args, "root", ".")).resolve()
    do_write = getattr(args, "write", False)
    do_check = getattr(args, "check", False)
    getattr(args, "format", "json")

    if not do_check and not do_write:
        print("sync-defaults: specify --check or --write", file=sys.stderr)
        return 2

    if do_write:
        result = write_defaults(root)
        print("sync-defaults: wrote install-defaults.toml", file=sys.stderr)
    else:
        result = check_defaults(root)

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
    return 0 if result.ok else 1
