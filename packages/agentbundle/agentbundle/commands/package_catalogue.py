"""package-catalogue subcommand — compatibility shim (deprecated).

All logic has moved to agentbundle.catalogue_tooling.package.
This module re-exports the internal helpers so existing import paths
continue to work (AC13), and wraps ``run()`` with a deprecation warning.

Use ``agentbundle catalogue package`` instead.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Re-export all helpers from the new engine so tests importing from here
# continue to work.
from agentbundle.catalogue_tooling.package import (  # noqa: F401
    _build_archive,
    _check_required_files,
    _compute_file_digests,
    _generate_manifest,
    _read_content_files,
    _scan_content,
    _validate_content,
    _validate_flag_value,
    _write_channel_descriptor,
    package_catalogue,
)

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    """Compatibility shim for ``agentbundle package-catalogue``.

    Prints a deprecation warning and delegates to ``package_catalogue()``.
    """
    print(
        "WARNING: agentbundle package-catalogue is deprecated. "
        "Use: agentbundle catalogue package",
        file=sys.stderr,
    )

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()

    result = package_catalogue(
        root=root,
        bundle=args.bundle,
        release=args.release,
        channel=args.channel,
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
