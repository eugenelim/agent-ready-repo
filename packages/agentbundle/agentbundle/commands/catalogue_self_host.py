"""``agentbundle catalogue self-host`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    from agentbundle.catalogue_tooling.self_host import check_self_host, write_self_host

    root = Path(getattr(args, "root", ".")).resolve()
    do_check = getattr(args, "check", False)
    do_write = getattr(args, "write", False)
    force = getattr(args, "force", False)
    fmt = getattr(args, "format", "table")

    if not do_check and not do_write:
        print("catalogue self-host: specify --check or --write", file=sys.stderr)
        return 2

    if do_write:
        result = write_self_host(root, force=force)
    else:
        result = check_self_host(root)

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
        print(f"catalogue self-host --{'write' if do_write else 'check'}: {status}", file=sys.stderr)

    return 0 if result.ok else 1
