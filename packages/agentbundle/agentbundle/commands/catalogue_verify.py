"""``agentbundle catalogue verify`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    root = Path(getattr(args, "root", ".")).resolve()
    archive_str = getattr(args, "archive", None)
    sha256_str = getattr(args, "sha256_file", None)
    pack = getattr(args, "pack", None)
    fmt = getattr(args, "format", "table")

    if archive_str:
        from agentbundle.catalogue_tooling.archive import verify_archive
        archive_path = Path(archive_str).resolve()
        sha256_path = Path(sha256_str).resolve() if sha256_str else None
        result = verify_archive(archive_path, sha256_file=sha256_path)
    else:
        from agentbundle.catalogue_tooling.verify import verify_catalogue
        result = verify_catalogue(root, pack=pack)

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
        print(json.dumps(doc, sort_keys=True, indent=2))
    else:
        from agentbundle.catalogue_tooling.verify import render_table
        output = render_table(result)
        print(output, file=sys.stderr)

    return 0 if result.ok else 1
