#!/usr/bin/env python3
"""Read a provider-returned file locator through the grounding reader.

Applies the exploration owner's own byte ceiling (MAX_PROVIDER_READ_BYTES).

This thin wrapper reuses the repository-grounding locator reader with the
exploration owner's own byte ceiling. All confinement logic stays in one place.

Usage::

    read-locator.py --root <repo> [--approved-root <dir>]... --locator-b64 <base64>

Exit codes:
  0  locator read; stdout: received: / root: / source: lines then file bytes
  2  usage error (missing or repeated --locator-b64); usage on stderr, nothing
     on stdout
  3  locator refused; stdout: received: / refused: lines
  4  grounding reader unavailable (missing, a link, not a regular file, or
     lacking required names); stderr: message, nothing on stdout
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent

# Default sibling path: ../../repository-grounding/scripts/read-locator.py
# relative to this file's scripts/ directory, i.e. the sibling Core skill.
_DEFAULT_GROUNDING_PATH: Path = (
    _SCRIPTS.parents[1] / "repository-grounding" / "scripts" / "read-locator.py"
)

_GROUNDING_MODULE_NAME = "packs_core_repository_exploration_grounding_reader"

# Byte ceiling for provider-returned files read by this skill.
# Read at call time so a test can monkeypatch it and observe the exploration
# value rather than grounding's being applied.
MAX_PROVIDER_READ_BYTES: int = 2_000_000


def _load_grounding_reader(sibling_path: Path | None = None) -> object:
    """Load the grounding locator reader from its sibling skill.

    Parameters
    ----------
    sibling_path:
        Test seam: alternate path for the reader. Uses _DEFAULT_GROUNDING_PATH
        when None. The default path is cached in sys.modules; a custom path
        is loaded fresh each call so test cases remain independent.

    Raises
    ------
    ImportError
        When the reader is missing, a symlink, not a regular file, or lacks
        ``read_locator`` or ``main``. There is no fallback route.
    """
    path = sibling_path if sibling_path is not None else _DEFAULT_GROUNDING_PATH
    use_cache = sibling_path is None

    if use_cache:
        existing = sys.modules.get(_GROUNDING_MODULE_NAME)
        if existing is not None:
            return existing

    # lstat: requires a regular file that is not a link.
    try:
        inspected = os.lstat(path)
    except OSError as exc:
        raise ImportError(
            f"repository-grounding locator reader unavailable: {exc}"
        ) from exc

    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise ImportError(
            "repository-grounding locator reader is not a regular file"
        )

    spec = importlib.util.spec_from_file_location(_GROUNDING_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise ImportError("repository-grounding locator reader cannot be loaded")

    module = importlib.util.module_from_spec(spec)
    if use_cache:
        sys.modules[_GROUNDING_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except BaseException:
        if use_cache:
            sys.modules.pop(_GROUNDING_MODULE_NAME, None)
        raise

    missing = sorted({"read_locator", "main"} - set(vars(module)))
    if missing:
        if use_cache:
            sys.modules.pop(_GROUNDING_MODULE_NAME, None)
        raise ImportError(
            f"repository-grounding locator reader is incomplete: {', '.join(missing)}"
        )
    return module


def read_locator(
    root: Path | str,
    locator: str,
    approved_roots: tuple[Path | str, ...] | list[Path | str] = (),
    *,
    _sibling_path: Path | None = None,
) -> object:
    """Read a provider-returned locator through the grounding reader.

    Applies MAX_PROVIDER_READ_BYTES as the byte ceiling. All confinement,
    refusal, and output contracts are grounding's.

    Parameters
    ----------
    root:
        Repository root.
    locator:
        Decoded locator text.
    approved_roots:
        Additional roots the user or calling workflow explicitly approved.
    _sibling_path:
        Test seam: alternate path for the grounding reader.

    Returns
    -------
    LocatorResult from the grounding reader.

    Raises
    ------
    ImportError
        When the grounding reader is unavailable.
    """
    gr = _load_grounding_reader(_sibling_path)
    return gr.read_locator(  # type: ignore[union-attr]
        root, locator, approved_roots, max_bytes=MAX_PROVIDER_READ_BYTES
    )


def main(
    argv: list[str] | None = None,
    *,
    _sibling_path: Path | None = None,
) -> int:
    """CLI entry point: delegate to the grounding reader with the exploration ceiling.

    Parameters
    ----------
    _sibling_path:
        Test seam: alternate path for the grounding reader.

    Exits 4 when the grounding reader is unavailable.
    """
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    try:
        gr = _load_grounding_reader(_sibling_path)
    except ImportError:
        print("repository-grounding locator reader unavailable", file=sys.stderr)
        return 4

    return gr.main(argv, max_bytes=MAX_PROVIDER_READ_BYTES)  # type: ignore[union-attr]


if __name__ == "__main__":
    raise SystemExit(main())
