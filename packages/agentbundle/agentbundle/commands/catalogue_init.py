"""``agentbundle catalogue init`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

# Action glyphs for table output.
_GLYPH = {
    "create": "  CREATE  ",
    "already-present": "  SKIP    ",
    "conflict": "  CONFLICT",
}


def run(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    target_raw = getattr(args, "target", ".")
    target_path = Path(target_raw)
    if target_path.is_symlink():
        print(
            f"error: target {target_raw!r} is a symlink. Provide a direct path.",
            file=sys.stderr,
        )
        return 2
    target = target_path.resolve()

    dry_run: bool = getattr(args, "dry_run", False)
    name: str | None = getattr(args, "name", None) or None
    display_name: str | None = getattr(args, "display_name", None) or None
    description: str | None = getattr(args, "description", None) or None
    owner_name: str | None = getattr(args, "owner_name", None) or None
    preferred_adapter: str | None = getattr(args, "preferred_adapter", None) or None
    fmt: str = getattr(args, "format", "table")

    result = init_catalogue(
        target=target,
        name=name,
        display_name=display_name,
        description=description,
        owner_name=owner_name,
        preferred_adapter=preferred_adapter,
        dry_run=dry_run,
    )

    if fmt == "json":
        doc = {
            "schema_version": result.schema_version,
            "command": result.command,
            "operation": result.operation,
            "agentbundle_version": result.agentbundle_version,
            "catalogue_schema_version": result.catalogue_schema_version,
            "ok": result.ok,
            "dry_run": result.dry_run,
            "target": result.target,
            "catalogue": dataclasses.asdict(result.catalogue),
            "summary": dataclasses.asdict(result.summary),
            "files": [dataclasses.asdict(f) for f in result.files],
            "verification": dataclasses.asdict(result.verification),
            "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
        }
        print(json.dumps(doc, indent=2))
        return 0 if result.ok else 1

    # --- table mode ---
    dry_label = " (dry run)" if result.dry_run else ""
    print(f"\nInitializing catalogue in {target}{dry_label}\n", file=sys.stderr)

    if result.files:
        for fp in result.files:
            glyph = _GLYPH.get(fp.action.value, f"  {fp.action.value.upper():<8}")
            line = f"{glyph}  {fp.path}"
            if fp.conflict_reason:
                conflict_short = fp.conflict_reason.split(".")[0]
                line += f"  — {conflict_short}"
            print(line, file=sys.stderr)
        print("", file=sys.stderr)

    if result.diagnostics:
        for diag in result.diagnostics:
            level = diag.severity.name
            loc = f" [{diag.path}]" if diag.path else ""
            print(f"  {level}{loc}: {diag.message}", file=sys.stderr)
            if diag.remediation:
                print(f"    → {diag.remediation}", file=sys.stderr)
        print("", file=sys.stderr)

    if result.ok:
        s = result.summary
        created_msg = f"{s.create} file(s) created"
        if s.already_present:
            created_msg += f", {s.already_present} already present"
        if result.dry_run:
            print(
                f"  ✓ Dry run complete — {created_msg} would be written. "
                f"Catalogue '{result.catalogue.name}' at {result.target}",
                file=sys.stderr,
            )
        else:
            print(
                f"  ✓ Done — {created_msg}. "
                f"Catalogue '{result.catalogue.name}' initialized at {result.target}",
                file=sys.stderr,
            )
    else:
        s = result.summary
        if s.conflict > 0:
            print(
                f"  ✗ {s.conflict} conflict(s) blocked init. "
                "Resolve conflicts and re-run, or use a clean target directory.",
                file=sys.stderr,
            )
        else:
            print("  ✗ Init failed — see errors above.", file=sys.stderr)

    return 0 if result.ok else 1
