"""``agentbundle catalogue package`` handler."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    flavor: str = getattr(args, "flavor", "runtime")
    if flavor == "source":
        return _run_source(args)
    return _run_runtime(args)


def _run_runtime(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.package import package_catalogue

    root = Path(getattr(args, "root", ".")).resolve()
    output_str = getattr(args, "output", None)
    if not output_str:
        print("error: --output is required", file=sys.stderr)
        return 1
    output = Path(output_str).resolve()
    bundle = getattr(args, "bundle", None)
    release = getattr(args, "release", None)
    channel = getattr(args, "channel", None)

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
        source_revision=getattr(args, "source_revision", None),
        minimum_agentbundle_version=getattr(args, "minimum_agentbundle_version", None),
        published_at=getattr(args, "published_at", None),
    )

    if not result.ok:
        for d in result.diagnostics:
            print(d.message, file=sys.stderr)
        return 1

    return 0


def _run_source(args: argparse.Namespace) -> int:
    from agentbundle.catalogue_tooling.package import package_source_flavour

    channel = getattr(args, "channel", None)
    if channel:
        print(
            "error: --channel is not valid with --flavor source; "
            "source distributions are not channel-bound",
            file=sys.stderr,
        )
        return 2

    root = Path(getattr(args, "root", ".")).resolve()
    output_str = getattr(args, "output", None)
    if not output_str:
        print("error: --output is required", file=sys.stderr)
        return 1
    output = Path(output_str).resolve()
    bundle = getattr(args, "bundle", None)
    release = getattr(args, "release", None)

    for flag, value in (("bundle", bundle), ("release", release)):
        if not value:
            print(f"error: --{flag} is required", file=sys.stderr)
            return 1

    result = package_source_flavour(
        root=root,
        bundle=bundle,
        release=release,
        output=output,
        source_revision=getattr(args, "source_revision", None),
    )

    if not result.ok:
        for msg in result.diagnostics:
            print(msg, file=sys.stderr)
        return 1

    print(f"  ✓ Source archive: {result.archive_path}", file=sys.stderr)
    print(f"  ✓ Manifest:       {result.manifest_path}", file=sys.stderr)
    return 0
