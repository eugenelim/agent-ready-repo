"""``agentbundle catalogue package`` handler."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from agentbundle.catalogue_tooling.results import PKG_REFUSED_CODE

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    flavor: str = args.flavor
    if flavor == "source":
        return _run_source(args)
    return _run_runtime(args)


def _run_runtime(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.package import package_catalogue

    root = Path(args.root).resolve()
    output_str = args.output
    if not output_str:
        print("error: --output is required", file=sys.stderr)
        return 1
    output = Path(output_str).resolve()
    bundle = args.bundle
    release = args.release
    channel = args.channel

    for flag, value in (("bundle", bundle), ("release", release), ("channel", channel)):
        if not value:
            print(f"error: --{flag} is required", file=sys.stderr)
            return 1

    result = package_catalogue(
        root=root,
        bundle=bundle,
        release=release,
        channel=channel,
        output=output,
        source_revision=args.source_revision,
        minimum_agentbundle_version=args.minimum_agentbundle_version,
        published_at=args.published_at,
        force=getattr(args, "force", False),
    )

    if not result.ok:
        for d in result.diagnostics:
            print(f"{d.code}: {d.message}", file=sys.stderr)
        if any(d.code == PKG_REFUSED_CODE for d in result.diagnostics):
            return 2
        return 1

    return 0


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
