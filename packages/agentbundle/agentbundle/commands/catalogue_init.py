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


_SELF_HOSTED_ONLY_FLAGS: tuple[tuple[str, str], ...] = (
    ("source", "--source"),
    ("tooling", "--tooling"),
    ("guides", "--guides"),
    ("attribution", "--attribution"),
    ("repository_url", "--repository-url"),
    ("owner_email", "--owner-email"),
)


def run(args: argparse.Namespace) -> int:
    preset: str | None = getattr(args, "preset", None)
    if preset == "self-hosted":
        return _run_self_hosted(args)
    # Reject self-hosted-only flags when not in self-hosted mode.
    for attr, flag in _SELF_HOSTED_ONLY_FLAGS:
        if getattr(args, attr, None):
            print(
                f"error: {flag} requires --preset self-hosted",
                file=sys.stderr,
            )
            return 2
    return _run_plain(args)


def _run_plain(args: argparse.Namespace) -> int:
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
            "next_steps": list(result.next_steps),
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
            print("", file=sys.stderr)
            print("  Next steps:", file=sys.stderr)
            # Rendered from result.next_steps rather than rebuilt here: the
            # JSON branch emits the same list, and two hand-maintained copies
            # of the same guidance drift.
            for step in result.next_steps:
                print(f"    • {step}", file=sys.stderr)
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


def _run_self_hosted(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.initialise_self_hosted import (
        SelfHostedInitConfig,
        init_self_hosted,
    )

    target_raw = getattr(args, "target", ".")
    target_path = Path(target_raw)
    if target_path.is_symlink():
        print(
            f"error: target {target_raw!r} is a symlink. Provide a direct path.",
            file=sys.stderr,
        )
        return 2

    source_raw = getattr(args, "source", None)
    if not source_raw:
        print(
            "error: --source is required with --preset self-hosted",
            file=sys.stderr,
        )
        return 2

    tooling: str = getattr(args, "tooling", None) or "external"
    if tooling not in ("external", "vendored"):
        print("error: --tooling must be 'external' or 'vendored'", file=sys.stderr)
        return 2

    attribution: str = getattr(args, "attribution", None) or "white-label"
    if attribution not in ("white-label", "attributed"):
        print(
            "error: --attribution must be 'white-label' or 'attributed'",
            file=sys.stderr,
        )
        return 2

    guides: str = getattr(args, "guides", None) or "selected"
    if guides not in ("none", "selected"):
        print("error: --guides must be 'none' or 'selected'", file=sys.stderr)
        return 2

    cfg = SelfHostedInitConfig(
        target=target_path.resolve(),
        source=Path(source_raw).resolve(),
        tooling=tooling,
        name=getattr(args, "name", None) or None,
        display_name=getattr(args, "display_name", None) or None,
        description=getattr(args, "description", None) or None,
        owner_name=getattr(args, "owner_name", None) or None,
        owner_email=getattr(args, "owner_email", None) or None,
        preferred_adapter=getattr(args, "preferred_adapter", None) or None,
        repository_url=getattr(args, "repository_url", None) or None,
        packs=getattr(args, "packs", None) or None,
        adapters=getattr(args, "adapters", None) or None,
        profiles=getattr(args, "profiles", None) or None,
        guides=guides,
        attribution=attribution,
        dry_run=bool(getattr(args, "dry_run", False)),
    )

    fmt: str = getattr(args, "format", "table")
    result = init_self_hosted(cfg)

    if fmt == "json":
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1

    # --- table mode ---
    dry_label = " (dry run)" if result.dry_run else ""
    print(
        f"\nInitializing self-hosted catalogue in {cfg.target}{dry_label}\n",
        file=sys.stderr,
    )

    for action, path in result.files_written:
        glyph = _GLYPH.get(action, f"  {action.upper():<8}")
        print(f"{glyph}  {path}", file=sys.stderr)
    if result.files_written:
        print("", file=sys.stderr)

    for msg in result.diagnostics:
        print(f"  ⚠  {msg}", file=sys.stderr)
    if result.diagnostics:
        print("", file=sys.stderr)

    if result.violations:
        print(
            f"  ✗ Leak check found {len(result.violations)} violation(s):",
            file=sys.stderr,
        )
        for v in result.violations[:5]:
            print(f"      {v.path}:{v.line}  [{v.anchor}]", file=sys.stderr)
        if len(result.violations) > 5:
            print(f"      … and {len(result.violations) - 5} more", file=sys.stderr)
        return 1

    if result.ok:
        if result.dry_run:
            print(
                f"  ✓ Dry run complete — self-hosted catalogue '{result.name}' "
                f"would be written at {cfg.target}",
                file=sys.stderr,
            )
        else:
            print(
                f"  ✓ Done — self-hosted catalogue '{result.name}' initialized at "
                f"{cfg.target}",
                file=sys.stderr,
            )
        if result.next_steps:
            print("\n  Next steps:", file=sys.stderr)
            for step in result.next_steps:
                print(f"    • {step}", file=sys.stderr)
    else:
        print("  ✗ Init failed — see errors above.", file=sys.stderr)

    return 0 if result.ok else 1
