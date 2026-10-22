"""Archive verification — safety and semantic checks for catalogue archives.

Two public entry points:
  ``verify_archive(archive, sha256_file=None) -> VerifyResult``
  ``check_members(members) -> list[Diagnostic]``  (for unit tests)
"""

from __future__ import annotations

import hashlib
import json
import stat
import tarfile
from collections.abc import Mapping
from pathlib import Path

from agentbundle.catalogue import CatalogueError
from agentbundle.catalogue_tooling.results import Diagnostic, Severity, VerifyResult
from agentbundle.https_catalogue import _validated_archive_destination

_MANIFEST_NAME = "catalogue-manifest.json"
_SOURCE_MANIFEST_NAME = "self-hosted-source-manifest.json"
_MAX_MEMBERS = 50_000
_MAX_COMPRESSED_BYTES = 500 * 1024 * 1024   # 500 MB
_MAX_EXPANDED_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

_AGENTBUNDLE_VERSION: str | None = None


def _get_agentbundle_version() -> str:
    global _AGENTBUNDLE_VERSION
    if _AGENTBUNDLE_VERSION is None:
        try:
            from agentbundle import __version__
            _AGENTBUNDLE_VERSION = __version__
        except Exception:
            _AGENTBUNDLE_VERSION = "unknown"
    return _AGENTBUNDLE_VERSION


def unit_digest(file_digests: Mapping[str, str], unit_path: str) -> str | None:
    """Return the unit digest of ``unit_path`` over ``file_digests``.

    ``file_digests`` maps archived relative paths to lowercase hex SHA-256.
    If it holds ``unit_path`` exactly, the unit is that one file, named by its
    basename; otherwise it is the directory of files under ``unit_path + "/"``.
    Returns ``None`` when no member file exists.
    """
    if unit_path in file_digests:
        members = {unit_path.rsplit("/", 1)[-1]: file_digests[unit_path]}
    else:
        prefix = unit_path + "/"
        members = {
            path[len(prefix):]: digest
            for path, digest in file_digests.items()
            if path.startswith(prefix)
        }
    if not members:
        return None
    # Sort by UTF-8 bytes, not code points, to honour "byte order".
    lines = sorted(
        (rel.encode("utf-8"), f"{digest}  {rel}\n")
        for rel, digest in members.items()
    )
    preimage = "".join(line for _, line in lines)
    return "sha256:" + hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def _err(code: str, message: str, path: str | None = None) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        pack=None,
        path=path,
        line=None,
        col=None,
        message=message,
        remediation=None,
    )


def _check_sha256_sidecar(archive: Path, sha256_file: Path | None) -> list[Diagnostic]:
    if sha256_file is None:
        return []
    try:
        expected_hex = sha256_file.read_text(encoding="utf-8").split()[0].lower()
    except Exception as exc:
        return [_err("CAT-V-ARC-001", f"cannot read sha256 sidecar: {exc}")]
    actual_hex = hashlib.sha256(archive.read_bytes()).hexdigest()
    if expected_hex != actual_hex:
        return [_err(
            "CAT-V-ARC-001",
            f"sha256 sidecar mismatch: expected {expected_hex}, got {actual_hex}",
        )]
    return []


def _check_gzip_parseable(archive: Path) -> list[Diagnostic]:
    try:
        with tarfile.open(archive, "r:gz"):
            pass
    except Exception as exc:
        return [_err("CAT-V-ARC-002", f"gzip parse error: {exc}")]
    return []


def _check_compressed_size(archive: Path) -> list[Diagnostic]:
    size = archive.stat().st_size
    if size > _MAX_COMPRESSED_BYTES:
        return [_err(
            "CAT-V-ARC-003",
            f"compressed size {size} exceeds limit {_MAX_COMPRESSED_BYTES}",
        )]
    return []


def check_members(members: list[tarfile.TarInfo]) -> list[Diagnostic]:
    """Member-level safety checks. Exported for unit tests (T1)."""
    diags: list[Diagnostic] = []

    # No absolute, traversal, or platform-ambiguous paths. Tar member names
    # are POSIX paths; backslashes are rejected rather than reinterpreted on
    # Windows during extraction.
    for m in members:
        try:
            _validated_archive_destination(Path("/"), m.name)
        except CatalogueError as exc:
            code = (
                "CAT-V-ARC-004"
                if m.name.startswith("/") or (len(m.name) > 1 and m.name[1] == ":")
                else "CAT-V-ARC-005"
            )
            diags.append(_err(code, str(exc), path=m.name))

    # No symlinks or hard links
    for m in members:
        if m.issym():
            diags.append(_err("CAT-V-ARC-006", f"symlink in archive: {m.name!r}", path=m.name))
        elif m.islnk():
            diags.append(_err("CAT-V-ARC-006", f"hard link in archive: {m.name!r}", path=m.name))

    # no device/special files or FIFOs
    for m in members:
        if m.isdev() or m.isfifo():
            diags.append(_err(
                "CAT-V-ARC-007",
                f"device/special/FIFO in archive: {m.name!r}",
                path=m.name,
            ))

    # No duplicate members
    seen: set[str] = set()
    for m in members:
        if m.name in seen:
            diags.append(_err("CAT-V-ARC-008", f"duplicate member: {m.name!r}", path=m.name))
        seen.add(m.name)

    # No case-insensitive collisions
    lower_seen: dict[str, str] = {}
    for m in members:
        lower = m.name.lower()
        if lower in lower_seen and lower_seen[lower] != m.name:
            diags.append(_err(
                "CAT-V-ARC-009",
                f"case collision: {m.name!r} vs {lower_seen[lower]!r}",
                path=m.name,
            ))
        lower_seen[lower] = m.name

    # member count limit
    if len(members) > _MAX_MEMBERS:
        diags.append(_err(
            "CAT-V-ARC-003",
            f"member count {len(members)} exceeds limit {_MAX_MEMBERS}",
        ))

    return diags


def _check_expanded_size(members: list[tarfile.TarInfo]) -> list[Diagnostic]:
    total = sum(m.size for m in members if m.isreg())
    if total > _MAX_EXPANDED_BYTES:
        return [_err(
            "CAT-V-ARC-003",
            f"expanded size {total} exceeds limit {_MAX_EXPANDED_BYTES}",
        )]
    return []


def _detect_prefix(members: list[tarfile.TarInfo]) -> str:
    """Detect a common single-level path prefix (e.g. 'catalogue-1.0/') in the archive."""
    reg_names = [m.name for m in members if m.isreg() or m.isdir()]
    if not reg_names:
        return ""
    first = reg_names[0]
    if "/" in first:
        candidate = first.split("/")[0] + "/"
        if all(n.startswith(candidate) for n in reg_names):
            return candidate
    return ""


def _parse_manifest(
    tf: tarfile.TarFile, members: list[tarfile.TarInfo]
) -> tuple[dict | None, list[Diagnostic]]:
    prefix = _detect_prefix(members)
    manifest_member = next(
        (
            m
            for m in members
            if m.name == f"{prefix}{_MANIFEST_NAME}" or m.name == _MANIFEST_NAME
        ),
        None,
    )
    if manifest_member is None:
        return None, [_err("CAT-V-ARC-010", f"{_MANIFEST_NAME} not found in archive")]
    try:
        fobj = tf.extractfile(manifest_member)
        assert fobj is not None
        data = json.loads(fobj.read().decode("utf-8"))
        return data, []
    except Exception as exc:
        return None, [_err("CAT-V-ARC-010", f"{_MANIFEST_NAME} parse error: {exc}")]


def _entry_label(kind: str, index: int, item: object) -> str:
    """Name a manifest entry for a diagnostic: its ``name`` when a string, else its index."""
    if isinstance(item, str):
        return f"{kind}[{index}] {item!r}"
    if isinstance(item, dict) and isinstance(item.get("name"), str):
        return f"{kind}[{index}] {item['name']!r}"
    return f"{kind}[{index}]"


def _check_unit_entry_fields(label: str, item: dict) -> list[Diagnostic]:
    """``path`` and ``digest`` must be strings, and ``digest`` needs ``path``."""
    diags: list[Diagnostic] = []
    for field in ("path", "digest"):
        if field in item and not isinstance(item[field], str):
            diags.append(_err("CAT-V-ARC-019", f"manifest {label} {field!r} must be a string"))
    if "digest" in item and "path" not in item:
        diags.append(_err("CAT-V-ARC-019", f"manifest {label} has a 'digest' but no 'path'"))
    return diags


def _check_manifest_shape(manifest: dict) -> list[Diagnostic]:
    """Shape checks over ``files``, ``packs`` and ``profiles``; one diagnostic per item."""
    diags: list[Diagnostic] = []
    files = manifest.get("files")
    if isinstance(files, list):
        for i, item in enumerate(files):
            if not (
                isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and isinstance(item.get("sha256"), str)
            ):
                diags.append(_err(
                    "CAT-V-ARC-019",
                    f"manifest {_entry_label('files', i, item)} must be an object "
                    "with string 'path' and 'sha256'",
                ))
    packs = manifest.get("packs")
    if isinstance(packs, list):
        for i, item in enumerate(packs):
            label = _entry_label("packs", i, item)
            if not (
                isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and isinstance(item.get("version"), str)
            ):
                diags.append(_err(
                    "CAT-V-ARC-019",
                    f"manifest {label} must be an object with string 'name' and 'version'",
                ))
            if isinstance(item, dict):
                diags.extend(_check_unit_entry_fields(label, item))
    if "profiles" in manifest:
        profiles = manifest["profiles"]
        if not isinstance(profiles, list):
            diags.append(_err("CAT-V-ARC-019", "manifest 'profiles' must be a list"))
        else:
            for i, item in enumerate(profiles):
                label = _entry_label("profiles", i, item)
                if isinstance(item, str):
                    continue
                if not (isinstance(item, dict) and isinstance(item.get("name"), str)):
                    diags.append(_err(
                        "CAT-V-ARC-019",
                        f"manifest {label} must be a string or an object with a string 'name'",
                    ))
                if isinstance(item, dict):
                    diags.extend(_check_unit_entry_fields(label, item))
    return diags


def _check_manifest_schema(manifest: object) -> list[Diagnostic]:
    """Check manifest schema and shape; accepts any parsed JSON value without raising."""
    if not isinstance(manifest, dict):
        return [_err(
            "CAT-V-ARC-019",
            f"manifest must be a JSON object, got {type(manifest).__name__}",
        )]
    diags: list[Diagnostic] = []
    schema = manifest.get("schema")
    if isinstance(schema, bool) or schema not in (1, 2):
        diags.append(_err("CAT-V-ARC-011", f"manifest schema must be 1 or 2, got {schema!r}"))
    for field in ("bundle", "release", "generated_at"):
        if not isinstance(manifest.get(field), str):
            diags.append(_err(
                "CAT-V-ARC-011",
                f"manifest missing required string field {field!r}",
            ))
    if not isinstance(manifest.get("files"), list):
        diags.append(_err("CAT-V-ARC-011", "manifest 'files' must be a list"))
    if not isinstance(manifest.get("packs"), list):
        diags.append(_err("CAT-V-ARC-011", "manifest 'packs' must be a list"))
    diags.extend(_check_manifest_shape(manifest))
    return diags


def _check_unit_digests(manifest: dict) -> list[Diagnostic]:
    """Each declared unit ``digest`` must equal the unit digest of its ``path``.

    Entries without a ``digest`` (legacy manifests) are skipped. Runs only on
    manifests that passed ``_check_manifest_schema``, so entries are well typed.
    """
    file_digests = {e["path"]: e["sha256"] for e in manifest["files"]}
    diags: list[Diagnostic] = []
    for kind in ("packs", "profiles"):
        for i, item in enumerate(manifest.get(kind, [])):
            if not isinstance(item, dict) or "digest" not in item:
                continue
            expected = item["digest"]
            actual = unit_digest(file_digests, item["path"])
            if actual != expected:
                diags.append(_err(
                    "CAT-V-ARC-018",
                    f"unit digest mismatch for {_entry_label(kind, i, item)} "
                    f"path {item['path']!r}: declared {expected!r}, computed {actual!r}",
                    path=item["path"],
                ))
    return diags


def _check_all_manifest_digests(
    tf: tarfile.TarFile, members: list[tarfile.TarInfo], manifest: dict
) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    prefix = _detect_prefix(members)
    member_map = {m.name: m for m in members}

    for entry in manifest.get("files", []):
        rel_path = entry.get("path", "")
        expected_sha = entry.get("sha256", "")
        member_name = f"{prefix}{rel_path}" if prefix else rel_path
        member = member_map.get(member_name)
        if member is None:
            diags.append(_err(
                "CAT-V-ARC-013",
                f"manifest declares {rel_path!r} but not in archive",
                path=rel_path,
            ))
            continue
        fobj = tf.extractfile(member)
        if fobj is None:
            diags.append(_err(
                "CAT-V-ARC-012",
                f"cannot extract {rel_path!r} for digest check",
                path=rel_path,
            ))
            continue
        actual_sha = hashlib.sha256(fobj.read()).hexdigest()
        if actual_sha != expected_sha:
            diags.append(_err(
                "CAT-V-ARC-012",
                f"digest mismatch for {rel_path!r}: expected {expected_sha!r}, got {actual_sha!r}",
                path=rel_path,
            ))
    return diags


def _check_no_undeclared_members(
    members: list[tarfile.TarInfo], manifest: dict
) -> list[Diagnostic]:
    prefix = _detect_prefix(members)
    declared: set[str] = {e["path"] for e in manifest.get("files", []) if "path" in e}
    diags: list[Diagnostic] = []
    for m in members:
        if not m.isreg():
            continue
        name = m.name
        rel = name[len(prefix):] if prefix and name.startswith(prefix) else name
        if rel == _MANIFEST_NAME:
            continue
        if rel not in declared:
            diags.append(_err("CAT-V-ARC-013", f"undeclared archive member: {rel!r}", path=rel))
    return diags


def _check_catalogue_markers(members: list[tarfile.TarInfo]) -> list[Diagnostic]:
    """At least one installable-archive marker must be present at its root."""
    prefix = _detect_prefix(members)
    marker_tops = {"catalogue.toml", "AGENTS.md", ".agentbundle"}
    found: set[str] = set()
    for m in members:
        name = m.name
        rel = name[len(prefix):] if prefix and name.startswith(prefix) else name
        top = rel.split("/")[0] if "/" in rel else rel
        if top in marker_tops:
            found.add(top)
    if not found:
        return [_err(
            "CAT-V-ARC-014",
            "no catalogue marker found (expected catalogue.toml, AGENTS.md, or .agentbundle)",
        )]
    return []


def _check_marketplace_entries(
    tf: tarfile.TarFile,
    members: list[tarfile.TarInfo],
) -> list[Diagnostic]:
    """Apply source-equivalent marketplace semantics without source identity."""
    prefix = _detect_prefix(members)
    member_name = f"{prefix}.claude-plugin/marketplace.json"
    marketplace = next((m for m in members if m.name == member_name), None)
    if marketplace is None:
        return []

    try:
        fobj = tf.extractfile(marketplace)
        if fobj is None:
            raise ValueError("marketplace member is not a regular file")
        payload = json.loads(fobj.read().decode("utf-8"))

        from agentbundle.build.main import _load_bundled_json
        from agentbundle.catalogue_tooling.verify import _validate_marketplace_entries

        entry_schema = _load_bundled_json("marketplace-entry.schema.json")
    except Exception as exc:
        return [_err(
            "CAT-V-ARC-017",
            f"marketplace validation failed: {exc}",
            path=".claude-plugin/marketplace.json",
        )]

    source_diags = _validate_marketplace_entries(
        payload,
        entry_schema,
        ".claude-plugin/marketplace.json",
    )
    return [
        Diagnostic(
            code="CAT-V-ARC-017",
            severity=diagnostic.severity,
            pack=diagnostic.pack,
            path=diagnostic.path,
            line=diagnostic.line,
            col=diagnostic.col,
            message=diagnostic.message,
            remediation=diagnostic.remediation,
        )
        for diagnostic in source_diags
    ]


def _check_min_agentbundle_compat(manifest: dict) -> list[Diagnostic]:
    min_ver = manifest.get("minimum_agentbundle_version")
    if not min_ver or not isinstance(min_ver, str):
        return []
    try:
        from agentbundle.version import CLI_VERSION
    except ImportError:
        return []
    try:
        running = tuple(int(x) for x in CLI_VERSION.split("."))
        required = tuple(int(x) for x in min_ver.split("."))
    except ValueError:
        return []
    if running < required:
        return [_err(
            "CAT-V-ARC-015",
            f"archive requires agentbundle >= {min_ver}, running {CLI_VERSION}",
        )]
    return []


def _make_result(diags: list[Diagnostic], operation: str) -> VerifyResult:
    return VerifyResult(
        ok=not any(d.severity == Severity.ERROR for d in diags),
        diagnostics=diags,
        schema_version=1,
        command="catalogue verify",
        operation=operation,
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=1,
    )


def verify_archive(archive: Path, sha256_file: Path | None = None) -> VerifyResult:
    """Verify a catalogue archive (.tar.gz).

    Runs the full safety + archive-semantic pipeline. Stops after safety errors.
    Sha256 sidecar mismatch causes immediate early return. Installable archives
    are not source catalogues, so they are not passed to ``verify_catalogue``.
    """
    diags: list[Diagnostic] = []

    # Sidecar — early exit
    sidecar_diags = _check_sha256_sidecar(archive, sha256_file)
    if sidecar_diags:
        return _make_result(sidecar_diags, "archive")

    gzip_diags = _check_gzip_parseable(archive)
    if gzip_diags:
        return _make_result(gzip_diags, "archive")

    diags.extend(_check_compressed_size(archive))

    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()

        # Refuse source-distribution archives before any further processing (B4).
        member_names = {m.name for m in members}
        prefix = _detect_prefix(members)
        source_manifest_present = (
            _SOURCE_MANIFEST_NAME in member_names
            or f"{prefix}{_SOURCE_MANIFEST_NAME}" in member_names
        )
        if source_manifest_present:
            return _make_result([_err(
                "CAT-V-ARC-016",
                "archive kind is agentbundle-self-hosted-source — "
                "this is a source distribution, not an installable catalogue archive",
            )], "archive")

        diags.extend(check_members(members))
        diags.extend(_check_expanded_size(members))

        if any(d.severity == Severity.ERROR for d in diags):
            return _make_result(diags, "archive")

        manifest, manifest_diags = _parse_manifest(tf, members)
        diags.extend(manifest_diags)
        if manifest_diags:
            return _make_result(diags, "archive")

        diags.extend(_check_manifest_schema(manifest))
        if any(d.severity == Severity.ERROR for d in diags):
            return _make_result(diags, "archive")
        assert isinstance(manifest, dict)  # a non-object manifest yields CAT-V-ARC-019 above

        diags.extend(_check_all_manifest_digests(tf, members, manifest))
        diags.extend(_check_unit_digests(manifest))
        diags.extend(_check_no_undeclared_members(members, manifest))
        diags.extend(_check_catalogue_markers(members))
        diags.extend(_check_marketplace_entries(tf, members))
        diags.extend(_check_min_agentbundle_compat(manifest))

    return _make_result(diags, "archive")


def read_verified_manifest(archive: Path) -> tuple[dict | None, VerifyResult]:
    """Return the manifest of ``archive`` only when ``verify_archive`` passes on it.

    A path that is not a regular file is refused before it is opened.
    The archive is read in memory; nothing is extracted to disk. The manifest is
    ``None`` whenever the returned result is not ok.
    """
    try:
        is_regular = stat.S_ISREG(archive.stat().st_mode)
        problem = None if is_regular else f"not a regular file: {archive}"
    except OSError as exc:
        problem = f"cannot read archive: {exc}"
    if problem is not None:
        return None, _make_result([_err("CAT-V-ARC-002", problem)], "archive")
    result = verify_archive(archive)
    if not result.ok:
        return None, result
    with tarfile.open(archive, "r:gz") as tf:
        manifest, diags = _parse_manifest(tf, tf.getmembers())
    if diags or not isinstance(manifest, dict):
        return None, _make_result(diags, "archive")
    return manifest, result
