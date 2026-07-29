"""Internal loader API for the bundled catalogue authoring scaffold.

The scaffold lives under ``agentbundle/_data/catalogue-scaffold/`` both in the
editable-install tree and in the installed wheel.  The canonical entry point is
:func:`scaffold_root`; the higher-level functions (:func:`load_manifest`,
:func:`list_files`, :func:`read_file`, :func:`verify_hashes`,
:func:`materialize_to`) provide a stable API for callers that need to inspect
or copy scaffold content without constructing paths manually.

All functions are stdlib-only — no third-party dependencies.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path, PurePosixPath

# Windows-reserved basenames (case-insensitive).
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})


def scaffold_root() -> Path:
    """Return the path to the bundled ``catalogue-scaffold/`` directory.

    Works under editable install (filesystem path) and installed wheel.
    The returned ``Path`` always points at a real directory on disk.

    Raises ``FileNotFoundError`` when the scaffold cannot be located.
    """
    # Primary: importlib.resources (works for both editable and wheel)
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/catalogue-scaffold")
        # Materialise the traversable to a concrete filesystem Path.
        candidate = Path(str(resource))
        if candidate.is_dir():
            return candidate
    except Exception:
        pass

    # Fallback: filesystem path relative to this file (editable install)
    here = Path(__file__).resolve()
    candidate = here.parent / "_data" / "catalogue-scaffold"
    if candidate.is_dir():
        return candidate

    raise FileNotFoundError(
        "agentbundle: catalogue-scaffold not found in bundled _data/ — "
        "re-install agentbundle to restore the scaffold."
    )


def load_manifest() -> dict:
    """Load and return the scaffold manifest (``manifest.json``).

    The manifest is a dict with keys:

    - ``"version"``: int (currently ``1``).
    - ``"files"``: dict mapping relative path strings to SHA-256 hex digests.
    """
    root = scaffold_root()
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"agentbundle: scaffold manifest not found at {manifest_path}; "
            "re-install agentbundle to restore the scaffold."
        )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def list_files() -> list[str]:
    """Return the sorted list of relative paths registered in the manifest."""
    manifest = load_manifest()
    return sorted(manifest.get("files", {}).keys())


def read_file(path: str) -> bytes:
    """Read and return the raw bytes of *path* from the scaffold.

    *path* must be a relative path string exactly as it appears in the
    manifest (e.g. ``"packs/README.md"``).

    Raises ``FileNotFoundError`` when the path is not in the manifest or does
    not exist on disk.
    """
    manifest = load_manifest()
    if path not in manifest.get("files", {}):
        raise FileNotFoundError(
            f"agentbundle scaffold: '{path}' is not a known scaffold file."
        )
    full = scaffold_root() / path
    if not full.exists():
        raise FileNotFoundError(
            f"agentbundle scaffold: '{path}' is registered in the manifest "
            f"but the file is missing at {full}."
        )
    return full.read_bytes()


def verify_hashes() -> bool:
    """Return ``True`` if every file in the manifest matches its SHA-256 hash.

    Returns ``False`` — rather than raising — when any file is missing or
    hash-mismatched, so callers can decide how to surface the error.
    """
    manifest = load_manifest()
    root = scaffold_root()
    for rel, expected_hash in manifest.get("files", {}).items():
        full = root / rel
        if not full.exists():
            return False
        actual = hashlib.sha256(full.read_bytes()).hexdigest()
        if actual != expected_hash:
            return False
    return True


def materialize_to(dest: Path) -> None:
    """Copy every scaffold file into *dest*, preserving relative paths.

    Creates *dest* and any intermediate directories.  Overwrites existing
    files byte-for-byte.  Does not copy ``manifest.json`` itself (it is
    internal bookkeeping).

    After a successful ``materialize_to(dest)`` the directory at *dest*
    contains the exact scaffold file tree an adopter catalogue would use.
    """
    root = scaffold_root()
    for rel in list_files():
        src = root / rel
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))


# ---------------------------------------------------------------------------
# Extended API for catalogue init
# ---------------------------------------------------------------------------

def validate_manifest_paths(manifest: dict) -> list[str]:
    """Validate every path in *manifest* for safety.

    Returns a list of error strings (empty when all paths are safe).
    Checks: no absolute paths, no ``..`` traversal, no duplicates,
    no case-insensitive collisions, no Windows-reserved basenames.
    """
    errors: list[str] = []
    files: dict = manifest.get("files", {})
    seen_lower: dict[str, str] = {}

    for rel in files:
        # Must be a non-empty string
        if not rel or not isinstance(rel, str):
            errors.append(f"Invalid path in manifest: {rel!r}")
            continue

        # No absolute paths
        if rel.startswith("/") or (len(rel) > 1 and rel[1] == ":"):
            errors.append(f"Absolute path in manifest: {rel!r}")
            continue

        # No .. traversal
        parts = PurePosixPath(rel).parts
        if ".." in parts:
            errors.append(f"Path traversal in manifest: {rel!r}")
            continue

        # No Windows-reserved basenames in any component
        for part in parts:
            stem = part.rsplit(".", 1)[0].lower() if "." in part else part.lower()
            if stem in _WINDOWS_RESERVED_NAMES:
                errors.append(f"Windows-reserved name in manifest path {rel!r}: {part!r}")

        # Case-insensitive duplicate detection
        lower = rel.lower()
        if lower in seen_lower:
            errors.append(
                f"Case-insensitive collision in manifest: {rel!r} vs {seen_lower[lower]!r}"
            )
        else:
            seen_lower[lower] = rel

    return errors


def list_files_with_hashes() -> dict[str, str]:
    """Return ``{relative_path: sha256_hex}`` from the manifest, sorted by path."""
    manifest = load_manifest()
    files = manifest.get("files", {})
    return dict(sorted(files.items()))


def verify_hashes_detailed() -> dict[str, str | None]:
    """Return per-file verification results.

    Values: ``None`` = verified OK, ``str`` = error message (missing or hash mismatch).
    """
    manifest = load_manifest()
    root = scaffold_root()
    results: dict[str, str | None] = {}
    for rel, expected in manifest.get("files", {}).items():
        full = root / rel
        if not full.exists():
            results[rel] = f"missing: {full}"
        else:
            actual = hashlib.sha256(full.read_bytes()).hexdigest()
            if actual != expected:
                results[rel] = f"hash mismatch: expected {expected}, got {actual}"
            else:
                results[rel] = None
    return results


def find_unexpected_files() -> list[str]:
    """Return relative paths of files present on disk but absent from the manifest.

    Only inspects files under ``scaffold_root()``; does not descend into
    subdirectories not reachable from a manifest entry.
    """
    root = scaffold_root()
    manifest = load_manifest()
    known = set(manifest.get("files", {}).keys())
    # Do not include manifest.json itself
    known.add("manifest.json")
    unexpected: list[str] = []
    for dirpath, _dirs, filenames in os.walk(root):
        for fname in filenames:
            full = Path(dirpath) / fname
            try:
                rel = str(full.relative_to(root)).replace(os.sep, "/")
            except ValueError:
                continue
            if rel not in known:
                unexpected.append(rel)
    return sorted(unexpected)
