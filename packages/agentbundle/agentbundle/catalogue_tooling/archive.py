"""Catalogue archive verification stub.

Wave 4 (catalogue-tooling-package-enhanced spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path


def verify_archive(archive: Path, sha256_file: Path | None = None) -> bool:
    """Verify a packaged catalogue archive and optional SHA-256 checksum file.

    Wave 4 implementation: validates archive integrity and channel descriptor.
    """
    raise NotImplementedError(
        "verify_archive is not yet implemented — see catalogue-tooling-package-enhanced spec"
    )
