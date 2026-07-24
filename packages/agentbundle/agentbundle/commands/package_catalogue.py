"""package-catalogue subcommand — deterministic catalogue archive packager.

Packages a catalogue repository into an Artifactory artifact layout:
  - <output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz
  - <output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256
  - <output>/catalogues/<bundle>/channels/<channel>.json

Maintainer/CI only. Does not install anything.

RFC-0072 D1/D5. Python 3.11 stdlib only.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from agentbundle.config import ConfigError, load_pack_toml

if TYPE_CHECKING:
    import argparse


# ---------------------------------------------------------------------------
# Path safety helpers
# ---------------------------------------------------------------------------

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9\-._]+$")


def _validate_flag_value(flag: str, value: str) -> str | None:
    """Return an error string if *value* is not safe for use as a path component.

    Safe means: only [A-Za-z0-9-._], not '.' or '..', no '..' component.
    Returns None when the value is acceptable.
    """
    if not _SAFE_NAME_RE.fullmatch(value):
        return f"error: --{flag} value {value!r} contains disallowed characters (only [A-Za-z0-9-._] permitted)"
    if value in (".", ".."):
        return f"error: --{flag} value {value!r} is not allowed"
    # Split on '.' to catch '..': e.g. "foo..bar" splits to ["foo", "", "bar"]
    # but we also need to catch paths that use '/' -- covered by the regex
    # already (no slash). Check for '..' as a dot-separated component:
    if ".." in value.split("."):
        return f"error: --{flag} value {value!r} contains '..' component"
    return None


# ---------------------------------------------------------------------------
# Content scanning
# ---------------------------------------------------------------------------


def _scan_content(root: Path) -> list[Path]:
    """Return sorted list of regular (non-symlink) files from the content allowlist.

    Allowlisted directories: packs/, profiles/, docs/contracts/
    Allowlisted root files: README.md, LICENSE
    Does not follow symlinks.
    """
    collected: list[Path] = []

    allowlisted_dirs = [
        root / "packs",
        root / "profiles",
        root / "docs" / "contracts",
    ]
    for d in allowlisted_dirs:
        if d.is_dir() and not d.is_symlink():
            for dirpath, dirnames, filenames in os.walk(str(d), followlinks=False):
                dp = Path(dirpath)
                for fname in filenames:
                    p = dp / fname
                    if p.is_file() and not p.is_symlink():
                        collected.append(p)
                # Filter out symlinked subdirs from dirnames so os.walk skips them.
                dirnames[:] = [
                    dn for dn in dirnames if not (dp / dn).is_symlink()
                ]

    allowlisted_roots = [root / "README.md", root / "LICENSE"]
    for p in allowlisted_roots:
        if p.exists() and p.is_file() and not p.is_symlink():
            collected.append(p)

    return sorted(collected, key=lambda p: p.relative_to(root).as_posix())


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------


def _validate_content(root: Path, content_paths: list[Path]) -> str | None:
    """Validate all included content before writing any output.

    Returns an error string on any violation, None on success.

    Checks (in order):
    1. Top-level and intermediate directory symlinks
    2. packs/ directory exists
    3. Root-level file symlinks (README.md, LICENSE)
    4. Symlinks anywhere inside allowlisted directories
    5. Hard links (POSIX only)
    6. Path traversal outside root
    7. pack.toml parseability and required fields
    8. Profile TOML parseability
    """
    # 1. Top-level and intermediate directory symlink check
    top_level_candidates = [
        root / "packs",
        root / "profiles",
        root / "docs",
        root / "docs" / "contracts",
    ]
    for p in top_level_candidates:
        if p.exists() and p.is_symlink():
            return f"error: symlink not allowed: {p}"

    # 2. packs/ must exist as a real directory
    packs_dir = root / "packs"
    if not packs_dir.is_dir():
        return f"error: missing required directory: {packs_dir}"

    # 3. Root-level file symlink check
    for name in ("README.md", "LICENSE"):
        p = root / name
        if p.exists() and p.is_symlink():
            return f"error: symlink not allowed: {p}"

    # 4. Symlink walk inside allowlisted dirs
    for dir_name in (
        root / "packs",
        root / "profiles",
        root / "docs" / "contracts",
    ):
        if not dir_name.is_dir() or dir_name.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(str(dir_name), followlinks=False):
            dp = Path(dirpath)
            for entry in list(dirnames) + list(filenames):
                full = dp / entry
                if os.path.islink(str(full)):
                    return f"error: symlink not allowed: {full}"

    # 5. Hard-link detection (POSIX only — st_nlink is always 1 on Windows)
    for p in content_paths:
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_nlink > 1:
            return f"error: hard link not allowed: {p}"

    # 6. Path traversal check (belt-and-suspenders)
    for p in content_paths:
        try:
            p.resolve().relative_to(root)
        except ValueError:
            return f"error: path traversal outside root: {p}"

    # 7. pack.toml validation
    for pack_dir in sorted(packs_dir.iterdir()):
        if not pack_dir.is_dir() or pack_dir.is_symlink():
            continue
        pack_toml_path = pack_dir / "pack.toml"
        try:
            pack_data = load_pack_toml(pack_toml_path)
        except ConfigError as exc:
            return f"error: invalid pack.toml in {pack_dir}: {exc}"
        try:
            _ = pack_data["pack"]["name"]
            _ = pack_data["pack"]["version"]
        except KeyError as exc:
            return f"error: pack.toml missing required field {exc} in {pack_toml_path}"

    # 8. Profile TOML validation
    profiles_dir = root / "profiles"
    if profiles_dir.is_dir() and not profiles_dir.is_symlink():
        for toml_file in sorted(profiles_dir.rglob("*.toml")):
            if toml_file.is_symlink():
                continue
            try:
                tomllib.loads(toml_file.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as exc:
                return f"error: invalid profile TOML {toml_file}: {exc}"

    return None


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------


def _read_content_files(root: Path, paths: list[Path]) -> dict[str, bytes]:
    """Read all content files once; return {posix_relative_path: bytes}.

    The same bytes are used for both digest computation and archive assembly.
    """
    result: dict[str, bytes] = {}
    for p in paths:
        key = p.relative_to(root).as_posix()
        result[key] = p.read_bytes()
    return result


# ---------------------------------------------------------------------------
# Digest computation
# ---------------------------------------------------------------------------


def _compute_file_digests(file_bytes: dict[str, bytes]) -> dict[str, str]:
    """Return {posix_relative_path: sha256_hex} computed from in-memory bytes."""
    return {key: hashlib.sha256(data).hexdigest() for key, data in file_bytes.items()}


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------


def _generate_manifest(
    *,
    bundle: str,
    release: str,
    source_revision: str | None,
    generated_at: str,
    file_digests: dict[str, str],
    packs_metadata: list[dict],
) -> bytes:
    """Build catalogue-manifest.json bytes.

    catalogue-manifest.json is NOT listed in its own files array.
    """
    files = sorted(
        [{"path": k, "sha256": v} for k, v in file_digests.items()],
        key=lambda x: x["path"],
    )
    packs = sorted(packs_metadata, key=lambda x: x["name"])
    manifest = {
        "schema": 1,
        "bundle": bundle,
        "release": release,
        "source_revision": source_revision,
        "generated_at": generated_at,
        "files": files,
        "packs": packs,
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Archive builder
# ---------------------------------------------------------------------------


def _build_archive(file_bytes: dict[str, bytes], manifest_bytes: bytes) -> bytes:
    """Build a deterministic .tar.gz archive in memory.

    Returns the complete compressed bytes.
    - All members sorted lexicographically by name.
    - All members: uid=0, gid=0, mtime=0, mode=0o644.
    - gzip header mtime field (bytes 4-7) is zeroed.
    - tarfile.GNU_FORMAT to avoid PAX toolchain-dependent headers.
    """
    members: list[tuple[str, bytes]] = list(file_bytes.items())
    members.append(("catalogue-manifest.json", manifest_bytes))
    members.sort(key=lambda x: x[0])

    buf = io.BytesIO()
    gz = gzip.GzipFile(fileobj=buf, mode="wb", mtime=0)
    tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT)  # type: ignore[arg-type]

    for member_name, data in members:
        # Explicit path safety check — NOT assert (Python -O would strip assert)
        if member_name.startswith("/"):
            raise ValueError(f"unsafe archive member name: {member_name!r}")
        parts = member_name.split("/")
        if ".." in parts:
            raise ValueError(f"unsafe archive member name: {member_name!r}")
        if len(member_name) >= 2 and member_name[1] == ":":
            raise ValueError(f"unsafe archive member name: {member_name!r}")

        info = tarfile.TarInfo(name=member_name)
        info.type = tarfile.REGTYPE
        info.size = len(data)
        info.uid = 0
        info.gid = 0
        info.mtime = 0
        info.mode = 0o644
        tar.addfile(info, io.BytesIO(data))

    tar.close()
    gz.close()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Channel descriptor writer
# ---------------------------------------------------------------------------


def _write_channel_descriptor(
    path: Path,
    *,
    bundle: str,
    channel: str,
    release: str,
    sha256_hex: str,
    published_at: str,
    source_revision: str | None,
    minimum_agentbundle_version: str | None,
) -> None:
    """Write the channel descriptor JSON to *path*, creating parent dirs."""
    descriptor: dict = {
        "schema": 1,
        "kind": "agentbundle-catalogue",
        "bundle": bundle,
        "channel": channel,
        "release": release,
        "artifact": f"../releases/{release}/catalogue-{release}.tar.gz",
        "sha256": sha256_hex,
        "published_at": published_at,
    }
    if source_revision is not None:
        descriptor["source_revision"] = source_revision
    if minimum_agentbundle_version is not None:
        descriptor["minimum_agentbundle_version"] = minimum_agentbundle_version

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(descriptor, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------


def run(args: "argparse.Namespace") -> int:
    """Entry point for the package-catalogue subcommand.

    Returns 0 on success, 1 on any error.
    """
    # Step 1: Resolve root/output; validate --bundle, --release, --channel
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    bundle: str = args.bundle
    release: str = args.release
    channel: str = args.channel

    for flag, value in (("bundle", bundle), ("release", release), ("channel", channel)):
        err = _validate_flag_value(flag, value)
        if err is not None:
            print(err, file=sys.stderr)
            return 1

    # Step 2: Compute output paths
    archive_path = output / "catalogues" / bundle / "releases" / release / f"catalogue-{release}.tar.gz"
    sidecar_path = archive_path.parent / (archive_path.name + ".sha256")
    channel_descriptor_path = output / "catalogues" / bundle / "channels" / f"{channel}.json"

    # Step 3: Refuse-to-overwrite check
    if archive_path.exists():
        print(f"error: output archive already exists: {archive_path}", file=sys.stderr)
        return 1

    # Step 4: Scan content
    content_paths = _scan_content(root)

    # Step 5: Validate
    err = _validate_content(root, content_paths)
    if err is not None:
        print(err, file=sys.stderr)
        return 1

    # Step 6: Read all file bytes once
    file_bytes = _read_content_files(root, content_paths)

    # Step 7: Compute file digests
    digests = _compute_file_digests(file_bytes)

    # Step 8: Extract pack metadata from in-memory bytes
    packs_metadata: list[dict] = []
    for key, data in file_bytes.items():
        parts = key.split("/")
        # Match exactly packs/<name>/pack.toml (3 parts, no nesting)
        if len(parts) == 3 and parts[0] == "packs" and parts[2] == "pack.toml":
            pack_data = tomllib.loads(data.decode("utf-8"))
            packs_metadata.append({
                "name": pack_data["pack"]["name"],
                "version": pack_data["pack"]["version"],
            })

    # Step 9: Determine generated_at from SOURCE_DATE_EPOCH
    epoch_val = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch_val is None or epoch_val == "":
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    else:
        try:
            epoch_int = int(epoch_val)
        except ValueError:
            print(
                f"error: SOURCE_DATE_EPOCH is not a valid integer: {epoch_val!r}",
                file=sys.stderr,
            )
            return 1
        generated_at = datetime.fromtimestamp(epoch_int, tz=timezone.utc).replace(microsecond=0).isoformat()

    # Step 9b: Determine published_at
    published_at: str = getattr(args, "published_at", None) or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # Step 10: Generate manifest bytes
    manifest_bytes = _generate_manifest(
        bundle=bundle,
        release=release,
        source_revision=getattr(args, "source_revision", None),
        generated_at=generated_at,
        file_digests=digests,
        packs_metadata=packs_metadata,
    )

    # Step 11: Build archive bytes
    archive_bytes = _build_archive(file_bytes, manifest_bytes)

    # Step 12: Compute archive SHA-256
    sha256_hex = hashlib.sha256(archive_bytes).hexdigest()

    # Step 13: Create output directories
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    (output / "catalogues" / bundle / "channels").mkdir(parents=True, exist_ok=True)

    # Step 14: Write sidecar first
    sidecar_path.write_text(sha256_hex + "\n", encoding="utf-8")

    # Step 15: Write channel descriptor
    _write_channel_descriptor(
        channel_descriptor_path,
        bundle=bundle,
        channel=channel,
        release=release,
        sha256_hex=sha256_hex,
        published_at=published_at,
        source_revision=getattr(args, "source_revision", None),
        minimum_agentbundle_version=getattr(args, "minimum_agentbundle_version", None),
    )

    # Step 16: Write archive last
    archive_path.write_bytes(archive_bytes)

    return 0
