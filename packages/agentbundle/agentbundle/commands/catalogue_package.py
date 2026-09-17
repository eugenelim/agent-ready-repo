"""``agentbundle catalogue package`` handler."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

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
    )

    if not result.ok:
        for d in result.diagnostics:
            print(d.message, file=sys.stderr)
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
    )

    if not result.ok:
        for msg in result.diagnostics:
            print(msg, file=sys.stderr)
        return 1

    print(f"  ✓ Source archive: {result.archive_path}", file=sys.stderr)
    print(f"  ✓ Manifest:       {result.manifest_path}", file=sys.stderr)
    return 0
