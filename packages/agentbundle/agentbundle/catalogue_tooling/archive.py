"""Archive verification — safety and semantic checks for catalogue archives.

Spec: docs/specs/catalogue-tooling-verify/spec.md (ini-005 Bucket 6).

Two public entry points:
  ``verify_archive(archive, sha256_file=None) -> VerifyResult``
  ``check_members(members) -> list[Diagnostic]``  (for unit tests)
"""

from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from agentbundle.catalogue_tooling.results import Diagnostic, Severity, VerifyResult

_MANIFEST_NAME = "catalogue-manifest.json"
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
        return [_err("CAT-V-ARC-001", f"sha256 sidecar mismatch: expected {expected_hex}, got {actual_hex}")]
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
        return [_err("CAT-V-ARC-003", f"compressed size {size} exceeds limit {_MAX_COMPRESSED_BYTES}")]
    return []


def check_members(members: list[tarfile.TarInfo]) -> list[Diagnostic]:
    """Member-level safety checks. Exported for unit tests (T1)."""
    diags: list[Diagnostic] = []

    # AC10: no absolute paths
    for m in members:
        if m.name.startswith("/") or (len(m.name) > 1 and m.name[1] == ":"):
            diags.append(_err("CAT-V-ARC-004", f"absolute member path: {m.name!r}", path=m.name))

    # AC11: no traversal paths
    for m in members:
        if ".." in Path(m.name).parts:
            diags.append(_err("CAT-V-ARC-005", f"traversal path: {m.name!r}", path=m.name))

    # AC12: no symlinks or hard links
    for m in members:
        if m.issym():
            diags.append(_err("CAT-V-ARC-006", f"symlink in archive: {m.name!r}", path=m.name))
        elif m.islnk():
            diags.append(_err("CAT-V-ARC-006", f"hard link in archive: {m.name!r}", path=m.name))

    # no device/special files or FIFOs
    for m in members:
        if m.isdev() or m.isfifo():
            diags.append(_err("CAT-V-ARC-007", f"device/special/FIFO in archive: {m.name!r}", path=m.name))

    # AC13: no duplicate members
    seen: set[str] = set()
    for m in members:
        if m.name in seen:
            diags.append(_err("CAT-V-ARC-008", f"duplicate member: {m.name!r}", path=m.name))
        seen.add(m.name)

    # AC14: no case-insensitive collisions
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
        diags.append(_err("CAT-V-ARC-003", f"member count {len(members)} exceeds limit {_MAX_MEMBERS}"))

    return diags


def _check_expanded_size(members: list[tarfile.TarInfo]) -> list[Diagnostic]:
    total = sum(m.size for m in members if m.isreg())
    if total > _MAX_EXPANDED_BYTES:
        return [_err("CAT-V-ARC-003", f"expanded size {total} exceeds limit {_MAX_EXPANDED_BYTES}")]
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


def _check_manifest_schema(manifest: dict) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    schema = manifest.get("schema")
    if schema not in (1, 2):
        diags.append(_err("CAT-V-ARC-011", f"manifest schema must be 1 or 2, got {schema!r}"))
    for field in ("bundle", "release", "generated_at"):
        if not isinstance(manifest.get(field), str):
            diags.append(_err("CAT-V-ARC-011", f"manifest missing required string field {field!r}"))
    if not isinstance(manifest.get("files"), list):
        diags.append(_err("CAT-V-ARC-011", "manifest 'files' must be a list"))
    if not isinstance(manifest.get("packs"), list):
        diags.append(_err("CAT-V-ARC-011", "manifest 'packs' must be a list"))
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
            diags.append(_err("CAT-V-ARC-013", f"manifest declares {rel_path!r} but not in archive", path=rel_path))
            continue
        fobj = tf.extractfile(member)
        if fobj is None:
            diags.append(_err("CAT-V-ARC-012", f"cannot extract {rel_path!r} for digest check", path=rel_path))
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
    """At least one catalogue marker must be present at the archive root."""
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
        return [_err("CAT-V-ARC-015", f"archive requires agentbundle >= {min_ver}, running {CLI_VERSION}")]
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

    Runs the full safety + semantic pipeline. Stops after safety errors.
    AC5: sha256 sidecar mismatch causes immediate early return.
    AC17: on pass, extracts to tmpdir and calls verify_catalogue for round-trip.
    """
    diags: list[Diagnostic] = []

    # AC5: sidecar — early exit
    sidecar_diags = _check_sha256_sidecar(archive, sha256_file)
    if sidecar_diags:
        return _make_result(sidecar_diags, "archive")

    gzip_diags = _check_gzip_parseable(archive)
    if gzip_diags:
        return _make_result(gzip_diags, "archive")

    diags.extend(_check_compressed_size(archive))

    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()

        diags.extend(check_members(members))
        diags.extend(_check_expanded_size(members))

        if any(d.severity == Severity.ERROR for d in diags):
            return _make_result(diags, "archive")

        manifest, manifest_diags = _parse_manifest(tf, members)
        diags.extend(manifest_diags)
        if manifest is None:
            return _make_result(diags, "archive")

        diags.extend(_check_manifest_schema(manifest))
        if any(d.severity == Severity.ERROR for d in diags):
            return _make_result(diags, "archive")

        diags.extend(_check_all_manifest_digests(tf, members, manifest))
        diags.extend(_check_no_undeclared_members(members, manifest))
        diags.extend(_check_catalogue_markers(members))
        diags.extend(_check_min_agentbundle_compat(manifest))

        # AC17: local discoverability — extract to tmpdir and verify as catalogue
        if not any(d.severity == Severity.ERROR for d in diags):
            prefix = _detect_prefix(members)
            with tempfile.TemporaryDirectory() as tmpdir_str:
                tmpdir = Path(tmpdir_str)
                try:
                    tf.extractall(tmpdir, filter="data")
                except TypeError:
                    # Python < 3.12: extract member-by-member; paths pre-validated by check_members()
                    for _m in tf.getmembers():
                        _dest = tmpdir / _m.name
                        _dest.parent.mkdir(parents=True, exist_ok=True)
                        if _m.isreg():
                            _fobj = tf.extractfile(_m)
                            if _fobj is not None:
                                _dest.write_bytes(_fobj.read())
                catalogue_root = tmpdir / prefix.rstrip("/") if prefix else tmpdir
                from agentbundle.catalogue_tooling.verify import verify_catalogue
                inner = verify_catalogue(catalogue_root)
                if not inner.ok:
                    for d in inner.diagnostics:
                        diags.append(_err(
                            "CAT-V-ARC-015",
                            f"extracted archive not locally discoverable: {d.message}",
                            path=d.path,
                        ))

    return _make_result(diags, "archive")
