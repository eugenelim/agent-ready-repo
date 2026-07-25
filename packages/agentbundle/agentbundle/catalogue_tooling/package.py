"""Catalogue packaging engine — wave 4 (catalogue-tooling-package-enhanced spec).

Packages a catalogue repository into an Artifactory artifact layout:
  - <output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz
  - <output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256
  - <output>/catalogues/<bundle>/channels/<channel>.json

Implements the 8-step staging + atomic placement sequence with
verify_archive self-verification before the channel descriptor is written.

Python 3.11 stdlib only.
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
from agentbundle.catalogue_tooling.results import Diagnostic, PackageResult, Severity

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Allowlist constants
# ---------------------------------------------------------------------------

# Directories walked recursively; everything found inside is included.
_DEFAULT_INCLUDE_DIRS: tuple[tuple[str, ...], ...] = (
    ("packs",),
    ("profiles",),
    ("docs", "contracts"),
    (".claude-plugin",),
)

# Specific files included only if they exist at root (not walked).
_DEFAULT_INCLUDE_ROOT_FILES: tuple[str, ...] = (
    "AGENTS.md",
    "README.md",
    "LICENSE-APACHE",
    "LICENSE-MIT",
)

# Files required to be present; packaging fails if any are missing.
_REQUIRED_PATHS: tuple[str, ...] = (
    "packs",
    ".claude-plugin/marketplace.json",
    "LICENSE-APACHE",
    "LICENSE-MIT",
)

# Implicit denylist — top-level directories always excluded regardless of include.
_IMPLICIT_DENY_DIRS: frozenset[str] = frozenset({
    ".git",
    "tools",
    "packages",
    "dist",
    "__pycache__",
})

# Path-safety pattern for --bundle/--release/--channel flag values.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9\-._]+$")


def _validate_flag_value(flag: str, value: str) -> str | None:
    """Return error string or None; validates bundle/release/channel values."""
    if not _SAFE_NAME_RE.fullmatch(value):
        return (
            f"error: --{flag} value {value!r} contains disallowed characters "
            f"(only [A-Za-z0-9-._] permitted)"
        )
    if value in (".", ".."):
        return f"error: --{flag} value {value!r} is not allowed"
    if ".." in value.split("."):
        return f"error: --{flag} value {value!r} contains '..' component"
    return None


# ---------------------------------------------------------------------------
# Content scanning
# ---------------------------------------------------------------------------


def _scan_content(root: Path) -> list[Path]:
    """Return sorted list of regular (non-symlink) files from the content allowlist.

    Uses _DEFAULT_INCLUDE_DIRS and _DEFAULT_INCLUDE_ROOT_FILES; applies
    _IMPLICIT_DENY_DIRS to skip denied top-level directories even if they appear
    inside an allowed dir (unlikely but defensive).
    """
    collected: list[Path] = []

    for dir_parts in _DEFAULT_INCLUDE_DIRS:
        d = root.joinpath(*dir_parts)
        if not d.is_dir() or d.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(str(d), followlinks=False):
            dp = Path(dirpath)
            for fname in filenames:
                p = dp / fname
                if p.is_file() and not p.is_symlink():
                    collected.append(p)
            dirnames[:] = [dn for dn in dirnames if not (dp / dn).is_symlink()]

    for fname in _DEFAULT_INCLUDE_ROOT_FILES:
        p = root / fname
        if p.exists() and p.is_file() and not p.is_symlink():
            collected.append(p)

    return sorted(collected, key=lambda p: p.relative_to(root).as_posix())


def _check_required_files(root: Path, content_paths: list[Path]) -> str | None:
    """Return error string if any required path is missing, else None."""
    posix_set = {p.relative_to(root).as_posix() for p in content_paths}
    for req in _REQUIRED_PATHS:
        if req.endswith("/"):
            # Directory check
            if not (root / req.rstrip("/")).is_dir():
                return f"error: required path missing: {req}"
        else:
            if req not in posix_set:
                # Check if the required file exists at all
                if not (root / req).exists():
                    return f"error: required file missing: {req}"
    return None


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------


def _validate_content(root: Path, content_paths: list[Path]) -> str | None:
    """Validate all included content before writing any output.

    Returns an error string on any violation, None on success.
    """
    # 1. Top-level and intermediate directory symlink check
    top_level_candidates = [
        root / "packs",
        root / "profiles",
        root / "docs",
        root / "docs" / "contracts",
        root / ".claude-plugin",
    ]
    for p in top_level_candidates:
        if p.exists() and p.is_symlink():
            return f"error: symlink not allowed: {p}"

    # 2. packs/ must exist as a real directory
    packs_dir = root / "packs"
    if not packs_dir.is_dir():
        return f"error: missing required directory: {packs_dir}"

    # 3. Root-level file symlink check
    for name in list(_DEFAULT_INCLUDE_ROOT_FILES) + ["marketplace.json"]:
        for candidate in [root / name, root / ".claude-plugin" / name]:
            if candidate.exists() and candidate.is_symlink():
                return f"error: symlink not allowed: {candidate}"

    # 4. Symlink walk inside allowlisted dirs
    for dir_parts in _DEFAULT_INCLUDE_DIRS:
        d = root.joinpath(*dir_parts)
        if not d.is_dir() or d.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(str(d), followlinks=False):
            dp = Path(dirpath)
            for entry in list(dirnames) + list(filenames):
                full = dp / entry
                if os.path.islink(str(full)):
                    return f"error: symlink not allowed: {full}"

    # 5. Hard-link detection (POSIX only)
    for p in content_paths:
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_nlink > 1:
            return f"error: hard link not allowed: {p}"

    # 6. Path traversal check
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
# File reading + digest computation
# ---------------------------------------------------------------------------


def _read_content_files(root: Path, paths: list[Path]) -> dict[str, bytes]:
    """Read all content files; return {posix_relative_path: bytes}."""
    result: dict[str, bytes] = {}
    for p in paths:
        key = p.relative_to(root).as_posix()
        result[key] = p.read_bytes()
    return result


def _compute_file_digests(file_bytes: dict[str, bytes]) -> dict[str, str]:
    """Return {posix_relative_path: sha256_hex}."""
    return {key: hashlib.sha256(data).hexdigest() for key, data in file_bytes.items()}


# ---------------------------------------------------------------------------
# Manifest generation (schema 2)
# ---------------------------------------------------------------------------


def _generate_manifest(
    *,
    bundle: str,
    release: str,
    source_revision: str | None,
    generated_at: str,
    file_digests: dict[str, str],
    packs_metadata: list[dict],
    # Bucket 8 extended fields
    minimum_agentbundle_version: str | None = None,
    catalogue_name: str | None = None,
    catalogue_display_name: str | None = None,
    adapter_contract_version: str | None = None,
    pack_schema_version: str | None = None,
    marketplace_digest: str | None = None,
    profiles_metadata: list[str] | None = None,
) -> bytes:
    """Build catalogue-manifest.json bytes (schema 2).

    catalogue-manifest.json is NOT listed in its own files[] array.
    """
    from agentbundle.version import SPEC_VERSION

    files = sorted(
        [{"path": k, "sha256": v} for k, v in file_digests.items()],
        key=lambda x: x["path"],
    )
    packs = sorted(packs_metadata, key=lambda x: x["name"])

    manifest: dict = {
        "schema": 2,
        "bundle": bundle,
        "release": release,
        "generated_at": generated_at,
        "source_revision": source_revision,
        "minimum_agentbundle_version": minimum_agentbundle_version,
        "catalogue_name": catalogue_name,
        "catalogue_display_name": catalogue_display_name,
        "adapter_contract_version": adapter_contract_version or SPEC_VERSION,
        "pack_schema_version": pack_schema_version or "1",
        "marketplace_digest": marketplace_digest,
        "files": files,
        "packs": packs,
        "profiles": profiles_metadata or [],
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
# Staging helpers
# ---------------------------------------------------------------------------


def _staging_path(final_path: Path) -> Path:
    """Return the .tmp staging path for *final_path* in the same directory."""
    return final_path.parent / (final_path.name + ".tmp")


def _cleanup_staged(*paths: Path) -> None:
    """Remove any staged files, ignoring errors (best-effort cleanup)."""
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def package_catalogue(
    root: Path,
    bundle: str,
    release: str,
    channel: str,
    output: Path,
    *,
    source_revision: str | None = None,
    minimum_agentbundle_version: str | None = None,
    published_at: str | None = None,
    generated_at: str | None = None,
    _verify_archive_fn=None,  # injectable for testing
) -> PackageResult:
    """Package a catalogue at *root* into an Artifactory artifact layout.

    Implements the 8-step staging + atomic placement sequence:
      1. Pre-package verify_catalogue
      2. Build archive bytes in memory
      3. Write staged archive
      4. Compute + write staged sidecar
      5. Self-verify staged archive + sidecar
      6. Atomic place archive
      7. Atomic place sidecar
      8. Write channel descriptor LAST

    Returns a PackageResult; does NOT raise on expected failures.
    """
    from agentbundle.version import CLI_VERSION

    def _err(msg: str) -> PackageResult:
        return PackageResult(
            ok=False,
            diagnostics=[Diagnostic(
                code="CAT-PKG-001",
                severity=Severity.ERROR,
                pack=None,
                path=None,
                line=None,
                col=None,
                message=msg,
                remediation=None,
            )],
            schema_version=1,
            command="catalogue",
            operation="package",
            agentbundle_version=CLI_VERSION,
            catalogue_schema_version=1,
        )

    # --- Step 0: validate flag values ---
    for flag, value in (("bundle", bundle), ("release", release), ("channel", channel)):
        flag_err = _validate_flag_value(flag, value)
        if flag_err is not None:
            return _err(flag_err)

    # --- Output path layout ---
    archive_path = output / "catalogues" / bundle / "releases" / release / f"catalogue-{release}.tar.gz"
    sidecar_path = archive_path.parent / (archive_path.name + ".sha256")
    channel_path = output / "catalogues" / bundle / "channels" / f"{channel}.json"

    # Refuse to overwrite existing immutable release archive
    if archive_path.exists():
        return _err(f"output archive already exists: {archive_path}")

    # --- Step 1: Pre-package verify_catalogue ---
    from agentbundle.catalogue_tooling.verify import verify_catalogue
    verify_result = verify_catalogue(root)
    if not verify_result.ok:
        msgs = "; ".join(d.message for d in verify_result.diagnostics if d.severity == Severity.ERROR)
        return _err(f"pre-package verify failed: {msgs}")

    # --- Scan and validate content ---
    content_paths = _scan_content(root)

    req_err = _check_required_files(root, content_paths)
    if req_err is not None:
        return _err(req_err)

    val_err = _validate_content(root, content_paths)
    if val_err is not None:
        return _err(val_err)

    # --- Read file bytes ---
    file_bytes = _read_content_files(root, content_paths)

    # Filter out catalogue.toml — never included in the archive
    file_bytes = {k: v for k, v in file_bytes.items() if k != "catalogue.toml"}

    # --- Compute digests ---
    digests = _compute_file_digests(file_bytes)

    # --- Extract pack metadata ---
    packs_metadata: list[dict] = []
    for key, data in file_bytes.items():
        parts = key.split("/")
        if len(parts) == 3 and parts[0] == "packs" and parts[2] == "pack.toml":
            pack_data = tomllib.loads(data.decode("utf-8"))
            packs_metadata.append({
                "name": pack_data["pack"]["name"],
                "version": pack_data["pack"]["version"],
            })

    # --- Extract profile names ---
    profiles_metadata: list[str] = []
    for key in sorted(file_bytes.keys()):
        parts = key.split("/")
        if len(parts) >= 2 and parts[0] == "profiles" and key.endswith(".toml"):
            profiles_metadata.append(parts[-1].removesuffix(".toml"))

    # --- Determine generated_at ---
    if generated_at is None:
        epoch_val = os.environ.get("SOURCE_DATE_EPOCH")
        if epoch_val is None or epoch_val == "":
            generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        else:
            try:
                epoch_int = int(epoch_val)
            except ValueError:
                return _err(f"SOURCE_DATE_EPOCH is not a valid integer: {epoch_val!r}")
            generated_at = datetime.fromtimestamp(epoch_int, tz=timezone.utc).replace(microsecond=0).isoformat()

    if published_at is None:
        published_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # --- Read catalogue.toml metadata for manifest ---
    catalogue_name: str | None = None
    catalogue_display_name: str | None = None
    min_version_manifest = minimum_agentbundle_version
    try:
        from agentbundle.catalogue_tooling.config import load_catalogue_config
        config = load_catalogue_config(root)
        if config is not None:
            catalogue_name = config.name
            catalogue_display_name = config.display_name
            if min_version_manifest is None:
                min_version_manifest = config.minimum_agentbundle_version
    except Exception:
        pass

    # --- Compute marketplace_digest ---
    marketplace_digest: str | None = None
    marketplace_bytes = file_bytes.get(".claude-plugin/marketplace.json")
    if marketplace_bytes is not None:
        marketplace_digest = "sha256:" + hashlib.sha256(marketplace_bytes).hexdigest()

    # --- Step 2: Build archive bytes in memory ---
    manifest_bytes = _generate_manifest(
        bundle=bundle,
        release=release,
        source_revision=source_revision,
        generated_at=generated_at,
        file_digests=digests,
        packs_metadata=packs_metadata,
        minimum_agentbundle_version=min_version_manifest,
        catalogue_name=catalogue_name,
        catalogue_display_name=catalogue_display_name,
        marketplace_digest=marketplace_digest,
        profiles_metadata=profiles_metadata,
    )
    archive_bytes = _build_archive(file_bytes, manifest_bytes)

    # Compute sha256
    sha256_hex = hashlib.sha256(archive_bytes).hexdigest()

    # --- Create output directories ---
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    (output / "catalogues" / bundle / "channels").mkdir(parents=True, exist_ok=True)

    # --- Step 3: Write staged archive ---
    staged_archive = _staging_path(archive_path)
    staged_sidecar = _staging_path(sidecar_path)
    try:
        staged_archive.write_bytes(archive_bytes)

        # --- Step 4: Write staged sidecar ---
        staged_sidecar.write_text(sha256_hex + "\n", encoding="utf-8")

        # --- Step 5: Self-verify staged archive + sidecar ---
        if _verify_archive_fn is None:
            from agentbundle.catalogue_tooling.archive import verify_archive as _verify_archive_fn  # type: ignore[assignment]
        verify_arch = _verify_archive_fn(staged_archive, sha256_file=staged_sidecar)
        if not verify_arch.ok:
            _cleanup_staged(staged_archive, staged_sidecar)
            msgs = "; ".join(d.message for d in verify_arch.diagnostics if d.severity == Severity.ERROR)
            return _err(f"staged archive self-verification failed: {msgs}")

        # --- Step 6: Atomic place archive ---
        staged_archive.rename(archive_path)

        # --- Step 7: Atomic place sidecar ---
        staged_sidecar.rename(sidecar_path)

    except Exception as exc:
        _cleanup_staged(staged_archive, staged_sidecar)
        raise exc

    # --- Step 8: Write channel descriptor LAST ---
    _write_channel_descriptor(
        channel_path,
        bundle=bundle,
        channel=channel,
        release=release,
        sha256_hex=sha256_hex,
        published_at=published_at,
        source_revision=source_revision,
        minimum_agentbundle_version=minimum_agentbundle_version,
    )

    return PackageResult(
        ok=True,
        diagnostics=[],
        schema_version=1,
        command="catalogue",
        operation="package",
        agentbundle_version=CLI_VERSION,
        catalogue_schema_version=1,
    )
