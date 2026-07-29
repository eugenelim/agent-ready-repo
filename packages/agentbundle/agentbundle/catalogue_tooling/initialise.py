"""Catalogue plain-init engine — agentbundle catalogue init.

Implements the plain init lifecycle:

  resolve metadata
    → verify bundled scaffold
    → generate catalogue.toml + marketplace.json
    → build plan (list of file actions)
    → detect conflicts
    → stage + verify in tmpdir
    → atomically commit additive files
    → verify final target
    → rollback newly created files on failure

Python 3.11 stdlib only.  No network, no subprocess, no third-party deps.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from agentbundle.catalogue_tooling.results import (
    Diagnostic,
    FileAction,
    FilePlan,
    InitCatalogueMeta,
    InitResult,
    InitSummary,
    InitVerification,
    Severity,
)
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_PREFERRED_ADAPTER = "claude-code"

# Pattern for a valid safe catalogue name.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")

# Characters to strip / replace when deriving a name from a directory basename.
_UNSAFE_NAME_CHARS_RE = re.compile(r"[^A-Za-z0-9_\-]")

# Unsafe / Windows-reserved path components.
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_agentbundle_version() -> str:
    try:
        from agentbundle import __version__
        return __version__
    except Exception:
        return "unknown"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _derive_name(basename: str) -> str | None:
    """Attempt to derive a lower-kebab-case name from *basename*."""
    cleaned = _UNSAFE_NAME_CHARS_RE.sub("-", basename.lower())
    # Collapse multiple dashes, strip leading/trailing dashes
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    if _SAFE_NAME_RE.match(cleaned):
        return cleaned
    return None


def _humanize_name(name: str) -> str:
    """Convert a safe name like 'acme-agents' to 'Acme Agents'."""
    return " ".join(word.capitalize() for word in re.split(r"[-_]", name))


def _load_adapter_names() -> frozenset[str]:
    """Return the set of valid adapter names from the bundled contract."""
    import tomllib
    try:
        from importlib.resources import files
        resource = files("agentbundle").joinpath("_data/adapter.toml")
        if resource.is_file():
            data = tomllib.loads(resource.read_text(encoding="utf-8"))
            adapters = data.get("adapter", {})
            if isinstance(adapters, dict):
                return frozenset(adapters.keys())
    except Exception:
        pass
    here = Path(__file__).resolve()
    fallback = here.parents[4] / "contracts" / "adapter.toml"
    if fallback.exists():
        data = tomllib.loads(fallback.read_text(encoding="utf-8"))
        adapters = data.get("adapter", {})
        if isinstance(adapters, dict):
            return frozenset(adapters.keys())
    raise ValueError(
        "catalogue init: adapter contract not found — cannot validate preferred-adapter"
    )


def _get_default_adapter() -> str:
    """Return the package-shipped organization preferred adapter, or built-in default."""
    try:
        import tomllib
        from importlib.resources import files
        resource = files("agentbundle").joinpath("_data/install-defaults.toml")
        if resource.is_file():
            data = tomllib.loads(resource.read_text(encoding="utf-8"))
            org = data.get("organization", {})
            adapter = org.get("preferred_adapter") or org.get("preferred-adapter")
            if adapter:
                return adapter
    except Exception:
        pass
    return _DEFAULT_PREFERRED_ADAPTER


def generate_empty_marketplace(
    name: str,
    description: str,
    owner_name: str,
) -> bytes:
    """Pure function. Return UTF-8 JSON bytes for an empty catalogue marketplace.

    Shape: {"name": "...", "description": "...", "owner": {"name": "..."}, "plugins": []}
    Deterministic, final newline.
    """
    payload = {
        "name": name,
        "description": description,
        "owner": {"name": owner_name},
        "plugins": [],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return text.encode("utf-8")


# ---------------------------------------------------------------------------
# Metadata resolution
# ---------------------------------------------------------------------------

@dataclass
class ResolvedMeta:
    name: str
    display_name: str
    description: str
    owner_name: str
    preferred_adapter: str
    minimum_agentbundle_version: str


def resolve_metadata(
    target: Path,
    name: str | None,
    display_name: str | None,
    description: str | None,
    owner_name: str | None,
    preferred_adapter: str | None,
) -> tuple[ResolvedMeta, list[str]]:
    """Resolve init metadata from flags and defaults.

    Returns (ResolvedMeta, errors).  Non-empty errors means resolution failed.
    """
    errors: list[str] = []

    # --- name ---
    resolved_name: str
    if name:
        if not _SAFE_NAME_RE.match(name):
            errors.append(
                f"--name {name!r} is not a valid catalogue name. "
                "Use only letters, digits, hyphens, and underscores, "
                "starting with a letter or digit."
            )
            resolved_name = name  # carry forward for early exit
        else:
            resolved_name = name
    else:
        derived = _derive_name(target.name)
        if derived:
            resolved_name = derived
        else:
            errors.append(
                f"Cannot derive a valid catalogue name from directory basename {target.name!r}. "
                "Use --name NAME to provide an explicit name."
            )
            resolved_name = "unnamed"

    if errors:
        return ResolvedMeta(
            name=resolved_name, display_name="", description="", owner_name="",
            preferred_adapter="", minimum_agentbundle_version="",
        ), errors

    # --- display_name ---
    resolved_display = display_name or _humanize_name(resolved_name)

    # --- description ---
    resolved_description = description or f"{resolved_display} AgentBundle catalogue."

    # --- owner_name ---
    resolved_owner = owner_name or resolved_display

    # --- preferred_adapter ---
    resolved_adapter: str
    if preferred_adapter:
        try:
            known = _load_adapter_names()
        except ValueError as exc:
            errors.append(str(exc))
            resolved_adapter = preferred_adapter
        else:
            if preferred_adapter not in known:
                errors.append(
                    f"--preferred-adapter {preferred_adapter!r} is not a known adapter. "
                    f"Known adapters: {sorted(known)}"
                )
            resolved_adapter = preferred_adapter
    else:
        resolved_adapter = _get_default_adapter()

    # --- minimum_agentbundle_version ---
    resolved_min_version = _get_agentbundle_version()

    return ResolvedMeta(
        name=resolved_name,
        display_name=resolved_display,
        description=resolved_description,
        owner_name=resolved_owner,
        preferred_adapter=resolved_adapter,
        minimum_agentbundle_version=resolved_min_version,
    ), errors


# ---------------------------------------------------------------------------
# Target validation
# ---------------------------------------------------------------------------

def validate_target(target_path: Path) -> list[str]:
    """Validate the init target path.

    Returns a list of errors (empty = valid).
    """
    errors: list[str] = []
    if target_path.exists() and not target_path.is_dir():
        errors.append(
            f"Target {target_path} exists and is not a directory. "
            "Provide a path to an existing or new directory."
        )
        return errors
    if target_path.is_symlink():
        errors.append(
            f"Target {target_path} is a symlink. "
            "Provide a direct path to avoid ambiguous behavior."
        )
        return errors
    # Resolve parent to check for symlink in ancestors
    try:
        resolved = target_path.resolve()
        if resolved.exists() and resolved.is_symlink():
            errors.append(f"Resolved target {resolved} is a symlink.")
    except OSError as exc:
        errors.append(f"Cannot resolve target path: {exc}")
    return errors


# ---------------------------------------------------------------------------
# Plan construction + conflict detection
# ---------------------------------------------------------------------------

@dataclass
class PlannedFile:
    rel_path: str     # target-relative path
    kind: str         # "generated" | "scaffold"
    content: bytes    # planned file content


def _build_plan(
    meta: ResolvedMeta,
    scaffold_files: dict[str, bytes],
    catalogue_toml_bytes: bytes,
    marketplace_bytes: bytes,
) -> list[PlannedFile]:
    """Build the ordered list of files to create."""
    planned: list[PlannedFile] = []

    # Generated files first
    planned.append(PlannedFile(
        rel_path="catalogue.toml",
        kind="generated",
        content=catalogue_toml_bytes,
    ))
    planned.append(PlannedFile(
        rel_path=".claude-plugin/marketplace.json",
        kind="generated",
        content=marketplace_bytes,
    ))

    # Scaffold files in manifest order (already sorted)
    for rel, content in sorted(scaffold_files.items()):
        planned.append(PlannedFile(rel_path=rel, kind="scaffold", content=content))

    return planned


def _is_safe_planned_path(rel: str, target: Path) -> str | None:
    """Return None if *rel* is safe, or an error string if not."""
    if not rel or rel.startswith("/") or (len(rel) > 1 and rel[1] == ":"):
        return f"Planned path is absolute: {rel!r}"
    parts = PurePosixPath(rel).parts
    if ".." in parts:
        return f"Planned path traverses outside target: {rel!r}"
    for part in parts:
        stem = part.rsplit(".", 1)[0].lower() if "." in part else part.lower()
        if stem in _WINDOWS_RESERVED_NAMES:
            return f"Planned path uses Windows-reserved name: {rel!r}"
    # Resolve to check symlink escape
    resolved_target = target.resolve()
    try:
        resolved_file = (target / rel).resolve()
        if resolved_file.parents[0].exists() and not resolved_file.is_relative_to(resolved_target):
            return f"Planned path escapes target (symlink): {rel!r}"
    except OSError:
        pass
    return None


def classify_conflicts(
    target: Path,
    planned: list[PlannedFile],
) -> list[FilePlan]:
    """Classify each planned file as create / already-present / conflict."""
    result: list[FilePlan] = []

    # Check for case-insensitive collision among planned paths
    lower_to_path: dict[str, str] = {}
    for pf in planned:
        lower = pf.rel_path.lower()
        if lower in lower_to_path:
            result.append(FilePlan(
                path=pf.rel_path,
                kind=pf.kind,
                action=FileAction.CONFLICT,
                sha256=_sha256_bytes(pf.content),
                conflict_reason=(
                    f"Case-insensitive collision with planned path {lower_to_path[lower]!r}"
                ),
            ))
            continue
        lower_to_path[lower] = pf.rel_path

        # Safety check on planned path
        safety_err = _is_safe_planned_path(pf.rel_path, target)
        if safety_err:
            result.append(FilePlan(
                path=pf.rel_path,
                kind=pf.kind,
                action=FileAction.CONFLICT,
                sha256=_sha256_bytes(pf.content),
                conflict_reason=safety_err,
            ))
            continue

        existing = target / pf.rel_path
        action: FileAction
        conflict_reason: str | None = None

        if existing.is_symlink():
            action = FileAction.CONFLICT
            conflict_reason = (
                f"{pf.rel_path!r} exists as a symlink — refusing to overwrite. "
                "Remove the symlink to initialize this path."
            )
        elif existing.exists() and not existing.is_file():
            action = FileAction.CONFLICT
            conflict_reason = (
                f"{pf.rel_path!r} exists but is not a regular file (got: "
                + ("directory" if existing.is_dir() else "unknown type")
                + "). Remove or rename it to initialize this path."
            )
        elif existing.is_file():
            try:
                current_content = existing.read_bytes()
            except OSError as exc:
                action = FileAction.CONFLICT
                conflict_reason = f"Cannot read existing {pf.rel_path!r}: {exc}"
            else:
                if current_content == pf.content:
                    action = FileAction.ALREADY_PRESENT
                else:
                    action = FileAction.CONFLICT
                    if pf.rel_path == "catalogue.toml":
                        conflict_reason = (
                            "catalogue.toml already exists with different content. "
                            "This directory already contains a different catalogue configuration. "
                            "Remove catalogue.toml or use a different target directory."
                        )
                    else:
                        conflict_reason = (
                            f"{pf.rel_path!r} exists with different content. "
                            "Remove or rename it to initialize this path."
                        )
        else:
            action = FileAction.CREATE

        result.append(FilePlan(
            path=pf.rel_path,
            kind=pf.kind,
            action=action,
            sha256=_sha256_bytes(pf.content),
            conflict_reason=conflict_reason,
        ))

    return result


# ---------------------------------------------------------------------------
# Staging + commit
# ---------------------------------------------------------------------------

def _stage_and_verify(
    planned: list[PlannedFile],
    meta: ResolvedMeta,
) -> tuple[bool, int]:
    """Stage planned files in a tmpdir, run verify_catalogue, return (ok, diag_count)."""
    from agentbundle.catalogue_tooling.verify import verify_catalogue

    with tempfile.TemporaryDirectory(prefix="agentbundle-init-stage-") as tmpdir:
        tmppath = Path(tmpdir)
        for pf in planned:
            dest = tmppath / pf.rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(pf.content)
        try:
            result = verify_catalogue(tmppath)
            return result.ok, len(result.diagnostics)
        except Exception:
            return False, 1


def _atomic_write(dest: Path, content: bytes) -> None:
    """Write *content* to *dest* atomically (write to .tmp then rename)."""
    tmp = dest.with_suffix(dest.suffix + ".abtmp")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(content)
        tmp.rename(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _commit_files(
    target: Path,
    planned: list[PlannedFile],
    file_plan: list[FilePlan],
) -> tuple[list[str], list[str]]:
    """Write create-classified files to target.

    Returns (created_files, created_dirs) — relative paths of files and dirs
    created by this invocation (for rollback).
    """
    plan_map = {fp.path: fp for fp in file_plan}
    created_files: list[str] = []
    created_dirs: list[str] = []

    # Track which directories existed before we started
    def _pre_exists(p: Path) -> bool:
        return p.exists()

    for pf in planned:
        fp = plan_map.get(pf.rel_path)
        if fp is None or fp.action != FileAction.CREATE:
            continue

        dest = target / pf.rel_path

        # Race-condition recheck immediately before placement
        if dest.is_symlink():
            raise RuntimeError(
                f"Race: {pf.rel_path!r} became a symlink between plan and commit."
            )
        if dest.exists() and not dest.is_file():
            raise RuntimeError(
                f"Race: {pf.rel_path!r} appeared as non-file between plan and commit."
            )
        if dest.is_file():
            current = dest.read_bytes()
            if current != pf.content:
                raise RuntimeError(
                    f"Race: {pf.rel_path!r} was modified between plan and commit."
                )
            # Already present (race-resolved to no-op)
            continue

        # Track newly created parent directories
        ancestors = list(reversed(dest.parents))
        for anc in ancestors:
            if anc == target or anc.is_relative_to(target):
                rel_anc = str(anc.relative_to(target)).replace(os.sep, "/")
                if rel_anc and rel_anc != "." and not anc.exists():
                    created_dirs.append(rel_anc)

        _atomic_write(dest, pf.content)
        created_files.append(pf.rel_path)

    return created_files, created_dirs


def _rollback(
    target: Path,
    created_files: list[str],
    created_dirs: list[str],
    target_was_new: bool,
) -> None:
    """Remove only files and directories created by this invocation."""
    import contextlib

    for rel in reversed(created_files):
        p = target / rel
        with contextlib.suppress(OSError):
            p.unlink(missing_ok=True)

    # Remove newly created directories bottom-up (deepest first)
    all_dirs = sorted(set(created_dirs), key=lambda d: d.count("/"), reverse=True)
    for rel in all_dirs:
        p = target / rel
        try:
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass

    # If the target dir itself was created by init, remove it if empty
    if target_was_new:
        try:
            if target.is_dir() and not any(target.iterdir()):
                target.rmdir()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def init_catalogue(
    target: Path,
    name: str | None = None,
    display_name: str | None = None,
    description: str | None = None,
    owner_name: str | None = None,
    preferred_adapter: str | None = None,
    dry_run: bool = False,
) -> InitResult:
    """Run plain catalogue init against *target*.

    Returns an :class:`InitResult`.  Never raises on expected failures —
    those are expressed as ``ok=False`` with diagnostics.
    """
    from agentbundle.scaffold import (
        find_unexpected_files,
        list_files_with_hashes,
        load_manifest,
        read_file,
        validate_manifest_paths,
    )

    agentbundle_version = _get_agentbundle_version()

    # --- 1. Validate target path ---
    target_errors = validate_target(target)
    if target_errors:
        diags = [Diagnostic(
            code="CAT-INIT-002",
            severity=Severity.ERROR,
            pack=None,
            path=str(target),
            line=None,
            col=None,
            message=e,
            remediation="Provide a valid directory path.",
        ) for e in target_errors]
        return InitResult(
            ok=False,
            diagnostics=diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target),
            catalogue=InitCatalogueMeta("", "", "", "", "", ""),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )

    # --- 2. Resolve metadata ---
    meta, meta_errors = resolve_metadata(
        target=target,
        name=name,
        display_name=display_name,
        description=description,
        owner_name=owner_name,
        preferred_adapter=preferred_adapter,
    )
    if meta_errors:
        diags = [Diagnostic(
            code="CAT-INIT-003",
            severity=Severity.ERROR,
            pack=None,
            path=None,
            line=None,
            col=None,
            message=e,
            remediation=None,
        ) for e in meta_errors]
        return InitResult(
            ok=False,
            diagnostics=diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target),
            catalogue=InitCatalogueMeta("", "", "", "", "", ""),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )

    # --- 3. Verify bundled scaffold ---
    try:
        manifest = load_manifest()
    except FileNotFoundError as exc:
        return InitResult(
            ok=False,
            diagnostics=[Diagnostic(
                code="CAT-INIT-004",
                severity=Severity.ERROR,
                pack=None,
                path=None,
                line=None,
                col=None,
                message=f"Scaffold manifest not found: {exc}",
                remediation="Re-install agentbundle to restore the scaffold.",
            )],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target),
            catalogue=InitCatalogueMeta("", "", "", "", "", ""),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )

    path_errors = validate_manifest_paths(manifest)
    if path_errors:
        diags = [Diagnostic(
            code="CAT-INIT-005",
            severity=Severity.ERROR,
            pack=None,
            path=None,
            line=None,
            col=None,
            message=f"Scaffold manifest path safety error: {e}",
            remediation="Re-install agentbundle to restore a valid scaffold.",
        ) for e in path_errors]
        return InitResult(
            ok=False,
            diagnostics=diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target),
            catalogue=InitCatalogueMeta("", "", "", "", "", ""),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )

    # Load scaffold bytes with hash verification
    hashes = list_files_with_hashes()
    scaffold_files: dict[str, bytes] = {}
    hash_errors: list[str] = []
    for rel, expected_hash in sorted(hashes.items()):
        try:
            content = read_file(rel)
        except FileNotFoundError as exc:
            hash_errors.append(str(exc))
            continue
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != expected_hash:
            hash_errors.append(
                f"Scaffold file {rel!r}: hash mismatch (expected {expected_hash}, "
                f"got {actual_hash})"
            )
            continue
        scaffold_files[rel] = content

    if hash_errors:
        diags = [Diagnostic(
            code="CAT-INIT-006",
            severity=Severity.ERROR,
            pack=None,
            path=None,
            line=None,
            col=None,
            message=f"Scaffold integrity error: {e}",
            remediation="Re-install agentbundle to restore the scaffold.",
        ) for e in hash_errors]
        return InitResult(
            ok=False,
            diagnostics=diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target),
            catalogue=InitCatalogueMeta("", "", "", "", "", ""),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )

    # Warn on unexpected scaffold files (non-blocking — manifested package may
    # carry extra files in some build configurations).
    unexpected = find_unexpected_files()
    unexpected_diags: list[Diagnostic] = [
        Diagnostic(
            code="CAT-INIT-011",
            severity=Severity.WARNING,
            pack=None,
            path=u,
            line=None,
            col=None,
            message=f"Unexpected file in scaffold package: {u!r}",
            remediation="Re-install agentbundle to restore a clean scaffold.",
        )
        for u in unexpected
    ]

    # --- 4. Generate catalogue.toml and marketplace.json ---
    catalogue_toml_str = emit_catalogue_toml(
        name=meta.name,
        display_name=meta.display_name,
        description=meta.description,
        minimum_agentbundle_version=meta.minimum_agentbundle_version,
        owner_name=meta.owner_name,
        preferred_adapter=meta.preferred_adapter,
    )
    catalogue_toml_bytes = catalogue_toml_str.encode("utf-8")

    marketplace_bytes = generate_empty_marketplace(
        name=meta.name,
        description=meta.description,
        owner_name=meta.owner_name,
    )

    # --- 5. Build plan ---
    planned = _build_plan(meta, scaffold_files, catalogue_toml_bytes, marketplace_bytes)

    # --- 6. Detect conflicts ---
    file_plan = classify_conflicts(target, planned)

    conflicts = [fp for fp in file_plan if fp.action == FileAction.CONFLICT]
    already_present = [fp for fp in file_plan if fp.action == FileAction.ALREADY_PRESENT]
    to_create = [fp for fp in file_plan if fp.action == FileAction.CREATE]
    summary = InitSummary(
        create=len(to_create),
        already_present=len(already_present),
        conflict=len(conflicts),
        total=len(file_plan),
    )

    catalogue_meta = InitCatalogueMeta(
        name=meta.name,
        display_name=meta.display_name,
        description=meta.description,
        owner_name=meta.owner_name,
        preferred_adapter=meta.preferred_adapter,
        minimum_agentbundle_version=meta.minimum_agentbundle_version,
    )

    if conflicts:
        conflict_diags = [
            Diagnostic(
                code="CAT-INIT-007",
                severity=Severity.ERROR,
                pack=None,
                path=fp.path,
                line=None,
                col=None,
                message=fp.conflict_reason or f"{fp.path!r} conflicts with existing content.",
                remediation="Resolve the conflict and re-run init.",
            )
            for fp in conflicts
        ]
        return InitResult(
            ok=False,
            diagnostics=conflict_diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target.resolve()),
            catalogue=catalogue_meta,
            files=file_plan,
            verification=InitVerification(ok=False, diagnostic_count=len(conflict_diags)),
            summary=summary,
        )

    # --- 7. Stage + verify in tmpdir ---
    stage_ok, stage_diag_count = _stage_and_verify(planned, meta)
    if not stage_ok:
        return InitResult(
            ok=False,
            diagnostics=[Diagnostic(
                code="CAT-INIT-008",
                severity=Severity.ERROR,
                pack=None,
                path=None,
                line=None,
                col=None,
                message=(
                    f"Staged catalogue verification failed "
                    f"({stage_diag_count} diagnostic(s)). "
                    "This is likely a bug in agentbundle — please report it."
                ),
                remediation="Report this issue at https://github.com/eugenelim/agent-ready-repo/issues",
            )],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target.resolve()),
            catalogue=catalogue_meta,
            files=file_plan,
            verification=InitVerification(ok=False, diagnostic_count=stage_diag_count),
            summary=summary,
        )

    # --- 8. Dry-run exit ---
    if dry_run:
        return InitResult(
            ok=True,
            diagnostics=unexpected_diags,
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=True,
            target=str(target.resolve()),
            catalogue=catalogue_meta,
            files=file_plan,
            verification=InitVerification(ok=stage_ok, diagnostic_count=stage_diag_count),
            summary=summary,
        )

    # --- 9. Create target dir if it doesn't exist yet ---
    target_was_new = not target.exists()
    if target_was_new:
        target.mkdir(parents=True, exist_ok=True)

    # --- 10. Atomically commit additive files ---
    created_files: list[str] = []
    created_dirs: list[str] = []
    try:
        created_files, created_dirs = _commit_files(target, planned, file_plan)
    except Exception as exc:
        _rollback(target, created_files, created_dirs, target_was_new)
        return InitResult(
            ok=False,
            diagnostics=[Diagnostic(
                code="CAT-INIT-009",
                severity=Severity.ERROR,
                pack=None,
                path=None,
                line=None,
                col=None,
                message=f"Commit failed: {exc}",
                remediation="Check file permissions on the target directory.",
            )],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target.resolve()),
            catalogue=catalogue_meta,
            files=file_plan,
            verification=InitVerification(ok=False, diagnostic_count=1),
            summary=summary,
        )

    # --- 11. Verify final target ---
    from agentbundle.catalogue_tooling.verify import verify_catalogue
    try:
        final_result = verify_catalogue(target)
        final_ok = final_result.ok
        final_diag_count = len(final_result.diagnostics)
    except Exception:
        final_ok = False
        final_diag_count = 1

    if not final_ok:
        _rollback(target, created_files, created_dirs, target_was_new)
        return InitResult(
            ok=False,
            diagnostics=[Diagnostic(
                code="CAT-INIT-010",
                severity=Severity.ERROR,
                pack=None,
                path=None,
                line=None,
                col=None,
                message=(
                    f"Final catalogue verification failed "
                    f"({final_diag_count} diagnostic(s)). "
                    "Rolled back newly created files."
                ),
                remediation=(
                    "Run 'agentbundle catalogue verify' for details. "
                    "This is likely a bug in agentbundle — please report it."
                ),
            )],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version=agentbundle_version,
            catalogue_schema_version=1,
            dry_run=dry_run,
            target=str(target.resolve()),
            catalogue=catalogue_meta,
            files=file_plan,
            verification=InitVerification(ok=False, diagnostic_count=final_diag_count),
            summary=summary,
        )

    return InitResult(
        ok=True,
        diagnostics=unexpected_diags,
        schema_version=1,
        command="catalogue init",
        operation="init",
        agentbundle_version=agentbundle_version,
        catalogue_schema_version=1,
        dry_run=False,
        target=str(target.resolve()),
        catalogue=catalogue_meta,
        files=file_plan,
        verification=InitVerification(ok=True, diagnostic_count=0),
        summary=summary,
    )
