"""``agentbundle catalogue package`` handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from agentbundle.catalogue_tooling.results import (
    PKG_REFUSED_CODE,
    Diagnostic,
    PackageResult,
    Severity,
)

if TYPE_CHECKING:
    import argparse


def _escape(text: str) -> str:
    """Write every non-printable character as its ``\\x``, ``\\u`` or ``\\U`` escape."""
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch.isprintable():
            out.append(ch)
        elif code <= 0xFF:
            out.append(f"\\x{code:02x}")
        elif code <= 0xFFFF:
            out.append(f"\\u{code:04x}")
        else:
            out.append(f"\\U{code:08x}")
    return "".join(out)


def _eprint(line: str) -> None:
    """Print one stderr line, escaped: any line may carry prior-archive text."""
    print(_escape(line), file=sys.stderr)


def _failure(message: str) -> PackageResult:
    """Build a CAT-PKG-001 failure result for a handler-level refusal."""
    from agentbundle.version import CLI_VERSION

    return PackageResult(
        ok=False,
        diagnostics=[Diagnostic(
            code="CAT-PKG-001", severity=Severity.ERROR, pack=None, path=None,
            line=None, col=None, message=message, remediation=None,
        )],
        schema_version=1,
        command="catalogue",
        operation="package",
        agentbundle_version=CLI_VERSION,
        catalogue_schema_version=1,
    )


def _comparison_lines(comparison: dict) -> list[str]:
    """Render the human comparison."""
    prior = comparison["prior"]
    lines = [f"Comparison with prior release: bundle {prior['bundle']} release {prior['release']}"]
    for kind, label in (("packs", "Packs"), ("profiles", "Profiles")):
        group = comparison[kind]
        lines.append(f"{label}:")
        for item in group["added"]:
            version = f" {item['version']}" if "version" in item else ""
            lines.append(f"  added: {item['name']}{version}")
        for item in group["removed"]:
            version = f" {item['version']}" if "version" in item else ""
            lines.append(f"  removed: {item['name']}{version}")
        for item in group["changed"]:
            detail = ""
            if "version" in item:
                old, new = item["version"]["from"], item["version"]["to"]
                detail = f" {old} -> {new}"
                if old == new:
                    detail += " (content changed, version unchanged)"
            lines.append(f"  changed: {item['name']}{detail}")
        lines.append(f"  unchanged: {group['unchanged']}")
    return lines


def _emit(result: PackageResult, fmt: str) -> int:
    """The one output exit point of a runtime run; returns the exit code."""
    for d in result.diagnostics:
        _eprint(f"{d.code}: {d.message}")
    if result.ok and result.comparison is not None:
        for line in _comparison_lines(result.comparison):
            _eprint(line)
    if fmt == "json":
        doc: dict[str, object] = {
            "schema_version": result.schema_version,
            "command": result.command,
            "operation": result.operation,
            "agentbundle_version": result.agentbundle_version,
            "catalogue_schema_version": result.catalogue_schema_version,
            "ok": result.ok,
            "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
        }
        if result.ok and result.comparison is not None:
            doc["comparison"] = result.comparison
        print(json.dumps(doc, indent=2, sort_keys=True))
    if result.ok:
        return 0
    return 2 if any(d.code == PKG_REFUSED_CODE for d in result.diagnostics) else 1


def run(args: argparse.Namespace) -> int:
    flavor: str = args.flavor
    if flavor == "source":
        if getattr(args, "compare", None) or getattr(args, "format", "table") == "json":
            print(
                "error: --compare and --format json are not valid with --flavor source",
                file=sys.stderr,
            )
            return 2
        return _run_source(args)
    return _emit(_run_runtime(args), getattr(args, "format", "table"))


def _run_runtime(args: argparse.Namespace) -> PackageResult:
    from agentbundle.catalogue_tooling.package import package_catalogue

    root = Path(args.root).resolve()
    output_str = args.output
    if not output_str:
        return _failure("--output is required")
    output = Path(output_str).resolve()
    bundle = args.bundle
    release = args.release
    channel = args.channel

    for flag, value in (("bundle", bundle), ("release", release), ("channel", channel)):
        if not value:
            return _failure(f"--{flag} is required")

    return package_catalogue(
        root=root,
        bundle=bundle,
        release=release,
        channel=channel,
        output=output,
        source_revision=args.source_revision,
        minimum_agentbundle_version=args.minimum_agentbundle_version,
        published_at=args.published_at,
        force=getattr(args, "force", False),
        compare=getattr(args, "compare", None),
    )


def _run_source(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.package import package_source_flavour

    channel = args.channel
    if channel:
        print(
            "error: --channel is not valid with --flavor source; "
            "source distributions are not channel-bound",
            file=sys.stderr,
        )
        return 2

    root = Path(args.root).resolve()
    output_str = args.output
    if not output_str:
        print("error: --output is required", file=sys.stderr)
        return 1
    output = Path(output_str).resolve()
    bundle = args.bundle
    release = args.release

    for flag, value in (("bundle", bundle), ("release", release)):
        if not value:
            print(f"error: --{flag} is required", file=sys.stderr)
            return 1

    result = package_source_flavour(
        root=root,
        bundle=bundle,
        release=release,
        output=output,
        source_revision=args.source_revision,
        force=getattr(args, "force", False),
    )

    if not result.ok:
        for msg in result.diagnostics:
            print(f"{PKG_REFUSED_CODE}: {msg}" if result.refused else msg, file=sys.stderr)
        return 2 if result.refused else 1

    print(f"  ✓ Source archive: {result.archive_path}", file=sys.stderr)
    print(f"  ✓ Manifest:       {result.manifest_path}", file=sys.stderr)
    return 0
