"""Self-hosted catalogue init engine — agentbundle catalogue init --preset self-hosted.

Two tooling modes:
  external  — packs and profiles copied; catalogue-curation installed repo-scope
              from PyPI/registry by the operator separately.
  vendored  — everything in external, plus agentbundle source and catalogue-curation
              source copied to .agentbundle/tooling/ for air-gapped deployments.

Two identity modes:
  white-label  — identity anchors (source name, owner, email, URL) replaced in all
                 copied text files; verify() must return empty list.
  attributed   — anchors allowed only in declared attribution surfaces
                 (catalogue.toml, ATTRIBUTION.md); verify() allows them there.

Python 3.11 stdlib only.  No network, no subprocess, no third-party deps.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentbundle.catalogue_tooling.identity import (
    BINARY_EXT,
    Violation,
    check_ci_boundary,
    verify,
)
from agentbundle.catalogue_tooling.initialise import (
    PlannedFile,
    atomic_write,
    classify_conflicts,
    commit_files,
    rollback,
)
from agentbundle.catalogue_tooling.results import FileAction

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")
_URL_RE = re.compile(r"^https?://\S+$")
# Reject userinfo (credentials) in URLs: https://user:pass@host is disallowed.
_URL_USERINFO_RE = re.compile(r"^https?://[^/@]*@", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Packs never copied to the target (they're tooling, not catalogue content).
_TOOLING_PACKS: frozenset[str] = frozenset({"catalogue-curation"})

# Attribution surfaces where upstream identity is allowed in attributed mode.
_ATTRIBUTION_SURFACES: list[str] = ["catalogue.toml", "ATTRIBUTION.md"]

# State file written to .agentbundle/ in the target.
_OWNERSHIP_STATE_FILE = ".agentbundle/self-host-state.json"

# Vendored tooling root inside the target.
_VENDORED_TOOLING_ROOT = ".agentbundle/tooling"

# RFC-0082 / ADR-0075 D3: the vendored copy is wheel-class — the command tells
# the adopter to `pip install -e` it, so it is an install source, not a source
# tree, and carries no test content. Relative to each vendored call's own root.
# The engine root is `packages/agentbundle/`, so its suite sits at `tests/` and
# a root `conftest.py` sits beside the package; both are test content.
_VENDORED_ENGINE_EXCLUDE: tuple[str, ...] = ("tests/", "conftest.py")

# Build residue, matched by *name at any depth* rather than by relative path.
# A maintainer's working tree carries all of these, and `_collect_dir_bytes`
# walks the filesystem rather than the git index, so without this they are
# copied into the adopter's repository and committed there. Two of them are
# more than noise:
#   * `__pycache__/*.pyc` embeds the absolute build path — a real username and
#     filesystem layout — which AGENTS.md § Privacy forbids committing.
#   * `.pytest_cache/` and `*.egg-info/SOURCES.txt` enumerate engine test node
#     IDs and paths: test content, shipped past a control whose whole purpose
#     is that no test content ships.
_BUILD_RESIDUE_DIRS: frozenset[str] = frozenset(
    {"__pycache__", ".pytest_cache", "build", "dist"}
)
_VENDORED_PACK_EXCLUDE: tuple[str, ...] = ("tests/",)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SelfHostedSource:
    """Logical source identity for self-hosted catalogue init."""

    name: str
    display_name: str
    release: str | None = None
    archive_uri: str | None = None
    sha256: str | None = None
    revision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "release": self.release,
            "archive_uri": self.archive_uri,
        }


@dataclass
class SelfHostedInitConfig:
    target: Path
    source: Path
    tooling: str = "external"  # "external" | "vendored"
    attribution: str = "white-label"  # "white-label" | "attributed"
    guides: str = "selected"  # "none" | "selected"
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    preferred_adapter: str | None = None
    repository_url: str | None = None
    archive_uri: str | None = None  # B3/B12: source archive URI for provenance
    packs: list[str] | None = None  # None = all; explicit list = filtered
    adapters: list[str] | None = None
    profiles: list[str] | None = None
    dry_run: bool = False


@dataclass
class SelfHostedInitResult:
    ok: bool
    dry_run: bool
    name: str
    files_written: list[tuple[str, str]] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    # B12 additional fields
    preset: str = "self-hosted"
    tooling_mode: str = "external"
    attribution_mode: str = "white-label"
    selected_packs: list[str] = field(default_factory=list)
    selected_profiles: list[str] = field(default_factory=list)
    selected_adapters: list[str] = field(default_factory=list)
    field_collection_mode: str = "default"
    identity_replacements: list[dict] = field(default_factory=list)
    leak_scan_result: dict = field(default_factory=lambda: {"ok": True, "violation_count": 0})
    source: SelfHostedSource | None = None
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "command": "catalogue init",
            "operation": "self-hosted-init",
            "ok": self.ok,
            "dry_run": self.dry_run,
            "name": self.name,
            "preset": self.preset,
            "tooling_mode": self.tooling_mode,
            "attribution_mode": self.attribution_mode,
            "source": self.source.to_dict() if self.source else None,
            "selected_packs": self.selected_packs,
            "selected_profiles": self.selected_profiles,
            "selected_adapters": self.selected_adapters,
            "field_collection_mode": self.field_collection_mode,
            "identity_replacements": self.identity_replacements,
            "leak_scan_result": self.leak_scan_result,
            "summary": self.summary,
            "files_written": [{"action": a, "path": p} for a, p in self.files_written],
            "diagnostics": self.diagnostics,
            "violations": [
                {"path": v.path, "anchor": v.anchor, "line": v.line}
                for v in self.violations
            ],
            "next_steps": self.next_steps,
        }


@dataclass
class SelfHostOwnershipState:
    """Tracks which paths were written so future updates only remove our files."""

    schema_version: str = "2"
    managed_paths: list[dict] = field(default_factory=list)  # [{path, sha256}]
    adapters: list[str] = field(default_factory=list)
    managed_target_path: str = ""
    source_pack_identity: str = ""
    source_root_kind: str = "self-hosted-source"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "managed_paths": sorted(self.managed_paths, key=lambda x: x.get("path", "")),
            "adapters": sorted(self.adapters),
            "managed_target_path": self.managed_target_path,
            "source_pack_identity": self.source_pack_identity,
            "source_root_kind": self.source_root_kind,
        }


# ---------------------------------------------------------------------------
# Source validation
# ---------------------------------------------------------------------------

def _read_source_catalogue(source: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Return (parsed catalogue.toml dict, error_str).  error_str is None on success."""
    toml_path = source / "catalogue.toml"
    if not toml_path.is_file():
        return None, f"source path does not contain catalogue.toml: {source}"
    try:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"failed to parse source catalogue.toml: {exc}"
    return data, None


def resolve_source(source: Path, tooling: str) -> tuple[SelfHostedSource | None, str | None]:
    """Validate source path and return SelfHostedSource or (None, error).

    For vendored mode, the source must contain packages/agentbundle/.
    """
    source_meta, err = _read_source_catalogue(source)
    if err:
        return None, err
    cat = source_meta.get("catalogue", {})
    if tooling == "vendored":
        agentbundle_pkg = source / "packages" / "agentbundle"
        if not agentbundle_pkg.is_dir() or agentbundle_pkg.is_symlink():
            return None, (
                "source is missing packages/agentbundle/ — "
                "vendored mode requires a self-hosted source catalogue, not a runtime archive"
            )
    return SelfHostedSource(
        name=cat.get("name", ""),
        display_name=cat.get("display_name", ""),
    ), None


# ---------------------------------------------------------------------------
# Field resolution
# ---------------------------------------------------------------------------

def _derive_name(target: Path) -> str:
    raw = target.name or "my-catalogue"
    safe = re.sub(r"[^A-Za-z0-9_\-]", "-", raw).strip("-")
    return safe or "my-catalogue"


def _prompt(prompt_text: str) -> str:
    """Prompt on TTY; return empty string if not a TTY."""
    if not sys.stdin.isatty():
        return ""
    try:
        return input(prompt_text).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def collect_fields(
    cfg: SelfHostedInitConfig,
    source_meta: dict[str, Any],
) -> SelfHostedInitConfig:
    """Return a resolved copy of cfg with defaults filled in.

    TTY-gated: prompts for missing required fields when stdin is a TTY;
    falls back to derived defaults when not a TTY.
    """
    cat = source_meta.get("catalogue", {})

    name = cfg.name
    if not name:
        derived = _derive_name(cfg.target)
        name = _prompt(f"Catalogue name [{derived}]: ") or derived

    display_name = cfg.display_name
    if not display_name:
        derived_dn = name.replace("-", " ").replace("_", " ").title()
        display_name = _prompt(f"Display name [{derived_dn}]: ") or derived_dn

    description = cfg.description
    if not description:
        src_name = cat.get("name", "upstream")
        derived_desc = f"A self-hosted catalogue derived from {src_name}."
        description = (
            _prompt(f"Description [{derived_desc}]: ") or derived_desc
        )

    owner_name = cfg.owner_name
    if not owner_name:
        owner_name = _prompt("Owner name: ") or display_name

    owner_email = cfg.owner_email
    if not owner_email:
        owner_email = _prompt("Owner email: ") or ""

    preferred_adapter = cfg.preferred_adapter or cat.get("preferred_adapter", "claude-code")

    return SelfHostedInitConfig(
        target=cfg.target,
        source=cfg.source,
        tooling=cfg.tooling,
        attribution=cfg.attribution,
        guides=cfg.guides,
        name=name,
        display_name=display_name,
        description=description,
        owner_name=owner_name,
        owner_email=owner_email,
        preferred_adapter=preferred_adapter,
        repository_url=cfg.repository_url,
        archive_uri=cfg.archive_uri,
        packs=cfg.packs,
        adapters=cfg.adapters,
        profiles=cfg.profiles,
        dry_run=cfg.dry_run,
    )


def validate_fields(cfg: SelfHostedInitConfig) -> list[str]:
    """Return list of validation error messages (empty = valid)."""
    errors: list[str] = []
    if not cfg.name or not _SAFE_NAME_RE.match(cfg.name):
        errors.append(
            f"name {cfg.name!r} is invalid: must match [A-Za-z0-9][A-Za-z0-9_-]*"
        )
    if cfg.repository_url:
        if not _URL_RE.match(cfg.repository_url):
            errors.append(
                f"repository-url {cfg.repository_url!r} must be an http:// or https:// URL"
            )
        elif _URL_USERINFO_RE.match(cfg.repository_url):
            errors.append(
                f"repository-url {cfg.repository_url!r} must not contain credentials"
            )
    if cfg.archive_uri and _URL_USERINFO_RE.match(cfg.archive_uri):
        errors.append(
            f"archive-uri {cfg.archive_uri!r} must not contain credentials"
        )
    if cfg.owner_email and not _EMAIL_RE.match(cfg.owner_email):
        errors.append(
            f"owner-email {cfg.owner_email!r} does not look like a valid email address"
        )
    return errors


# ---------------------------------------------------------------------------
# Pack / profile selection
# ---------------------------------------------------------------------------

def select_packs(source: Path, explicit: list[str] | None) -> list[str]:
    """Return sorted list of pack names to copy, excluding tooling packs.

    ``explicit`` narrows the set; an empty or absent list includes all packs.
    """
    packs_dir = source / "packs"
    if not packs_dir.is_dir():
        return []
    available = sorted(
        d.name
        for d in packs_dir.iterdir()
        if d.is_dir() and not d.is_symlink() and d.name not in _TOOLING_PACKS
        and not d.name.startswith("_")
    )
    if not explicit:
        return available
    chosen = [p for p in explicit if p not in _TOOLING_PACKS]
    missing = [p for p in chosen if p not in available]
    if missing:
        raise ValueError(
            f"requested pack(s) not found in source: {', '.join(missing)}"
        )
    return sorted(set(chosen))


def _select_profiles(source: Path, explicit: list[str] | None) -> list[str]:
    profiles_dir = source / "profiles"
    if not profiles_dir.is_dir():
        return []
    available = sorted(
        f.stem
        for f in profiles_dir.iterdir()
        if f.is_file() and f.suffix == ".toml" and not f.is_symlink()
    )
    if not explicit:
        return available
    missing = [p for p in explicit if p not in available]
    if missing:
        raise ValueError(
            f"requested profile(s) not found in source: {', '.join(missing)}"
        )
    return sorted({p for p in explicit if p in available})


# ---------------------------------------------------------------------------
# In-memory file collection
# ---------------------------------------------------------------------------

def _collect_dir_bytes(
    src_dir: Path,
    dst_prefix: str,
    file_bytes: dict[str, bytes],
    file_kinds: dict[str, str],
    *,
    kind: str = "file",
    exclude: tuple[str, ...] = (),
) -> None:
    """Recursively collect bytes from src_dir into file_bytes under dst_prefix.

    `exclude` holds paths relative to *src_dir*: a trailing-slash entry prunes
    that subtree, a bare entry drops that exact file. It defaults to empty and
    is passed only at the two vendored call sites — the adopter's own packs and
    guides must keep their tests (ADR-0071), so excluding inside this routine
    would break them with nothing going red.
    """
    prune = tuple(e.rstrip("/") for e in exclude if e.endswith("/"))
    drop = frozenset(e for e in exclude if not e.endswith("/"))
    # Build residue is pruned by name at any depth whenever any exclusion is in
    # force — i.e. at the vendored call sites only. The adopter's own packs and
    # guides are copied with `exclude=()` and keep everything.
    residue = bool(exclude)
    for dirpath, dirnames, filenames in os.walk(str(src_dir), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [dn for dn in dirnames if not (dp / dn).is_symlink()]
        rel_to_src = dp.relative_to(src_dir)
        rel_dir = rel_to_src.as_posix()
        if residue:
            dirnames[:] = [
                dn
                for dn in dirnames
                if dn not in _BUILD_RESIDUE_DIRS and not dn.endswith(".egg-info")
            ]
        if prune:
            base = "" if rel_dir == "." else rel_dir + "/"
            dirnames[:] = [dn for dn in dirnames if base + dn not in prune]
        for fname in filenames:
            src_file = dp / fname
            if src_file.is_symlink():
                continue
            if residue and fname.endswith((".pyc", ".pyo")):
                continue
            if drop and (
                fname if rel_dir == "." else f"{rel_dir}/{fname}"
            ) in drop:
                continue
            rel_path = (Path(dst_prefix) / rel_to_src / fname).as_posix()
            file_bytes[rel_path] = src_file.read_bytes()
            file_kinds[rel_path] = kind


# ---------------------------------------------------------------------------
# Identity transformation (in-memory)
# ---------------------------------------------------------------------------

def _build_anchors(source_meta: dict[str, Any]) -> dict[str, str]:
    """Extract identity-bearing literal values from source catalogue.toml."""
    cat = source_meta.get("catalogue", {})
    anchors: dict[str, str] = {}
    for field_name in ("name", "display_name", "description"):
        val = cat.get(field_name, "")
        if val and len(val) > 3:  # skip very short or empty values
            anchors[field_name] = val
    for m in cat.get("maintainers", []):
        if m.get("name") and len(m["name"]) > 3:
            anchors["maintainer_name"] = m["name"]
        if m.get("email") and len(m["email"]) > 3:
            anchors["maintainer_email"] = m["email"]
    links = cat.get("links", {})
    for link_key in ("homepage", "repository"):
        val = links.get(link_key, "")
        if val and val.startswith("http"):
            anchors[f"link_{link_key}"] = val
    return anchors


def _transform_text(content: str, anchors: dict[str, str], cfg: SelfHostedInitConfig) -> str:
    """Replace source identity anchor values with target values in content."""
    replacements: list[tuple[str, str]] = []

    src_name = anchors.get("name", "")
    if src_name and cfg.name and src_name != cfg.name:
        replacements.append((src_name, cfg.name))

    src_display = anchors.get("display_name", "")
    if src_display and cfg.display_name and src_display != cfg.display_name:
        replacements.append((src_display, cfg.display_name))

    src_desc = anchors.get("description", "")
    if src_desc and cfg.description and src_desc != cfg.description:
        replacements.append((src_desc, cfg.description))

    src_email = anchors.get("maintainer_email", "")
    if src_email and cfg.owner_email and src_email != cfg.owner_email:
        replacements.append((src_email, cfg.owner_email))

    src_repo = anchors.get("link_repository", "")
    if src_repo and cfg.repository_url and src_repo != cfg.repository_url:
        replacements.append((src_repo, cfg.repository_url))
    elif src_repo and not cfg.repository_url:
        replacements.append((src_repo, "https://example.com/my-catalogue"))

    src_homepage = anchors.get("link_homepage", "")
    if src_homepage and cfg.repository_url and src_homepage != cfg.repository_url:
        replacements.append((src_homepage, cfg.repository_url))
    elif src_homepage and not cfg.repository_url:
        replacements.append((src_homepage, "https://example.com/my-catalogue"))

    src_owner = anchors.get("maintainer_name", "")
    if src_owner and cfg.owner_name and src_owner != cfg.owner_name:
        replacements.append((src_owner, cfg.owner_name))

    for old, new in replacements:
        content = content.replace(old, new)
    return content


def _apply_identity_transform_bytes(
    file_bytes: dict[str, bytes],
    anchors: dict[str, str],
    cfg: SelfHostedInitConfig,
) -> list[dict]:
    """Apply identity replacement in-memory over file_bytes dict.

    Returns list of {from, to} replacement dicts (for B12 identity_replacements).
    Only operates on white-label mode; attributed mode is a no-op.
    """
    if cfg.attribution == "attributed":
        return []

    applied: set[tuple[str, str]] = set()
    for rel_path in list(file_bytes.keys()):
        if Path(rel_path).suffix.lower() in BINARY_EXT:
            continue
        try:
            content = file_bytes[rel_path].decode("utf-8", errors="replace")
            new_content = _transform_text(content, anchors, cfg)
            if new_content != content:
                file_bytes[rel_path] = new_content.encode("utf-8")
                # Capture what actually changed for B12 reporting
                for anchor_name, anchor_val in anchors.items():
                    if anchor_val in content and anchor_val not in new_content:
                        applied.add(
                            (anchor_val, _get_replacement_for(anchor_name, anchor_val, cfg))
                        )
        except Exception:
            continue

    return [{"from": old, "to": new} for old, new in sorted(applied)]


def _get_replacement_for(anchor_name: str, anchor_val: str, cfg: SelfHostedInitConfig) -> str:
    """Return the replacement string for a given anchor."""
    mapping = {
        "name": cfg.name or "",
        "display_name": cfg.display_name or "",
        "description": cfg.description or "",
        "maintainer_email": cfg.owner_email or "",
        "maintainer_name": cfg.owner_name or "",
        "link_repository": cfg.repository_url or "https://example.com/my-catalogue",
        "link_homepage": cfg.repository_url or "https://example.com/my-catalogue",
    }
    return mapping.get(anchor_name, "")


# ---------------------------------------------------------------------------
# Leak verification on in-memory bytes (tmpdir verify)
# ---------------------------------------------------------------------------

def _verify_bytes_in_tmpdir(
    file_bytes: dict[str, bytes],
    anchors: dict[str, str],
    cfg: SelfHostedInitConfig,
) -> tuple[list[Violation], list[Violation]]:
    """Write planned bytes to a tmpdir and run verify + check_ci_boundary.

    Returns (identity_violations, ci_violations).
    """
    with tempfile.TemporaryDirectory(prefix="agentbundle-sh-verify-") as tmpdir:
        tmppath = Path(tmpdir)
        for rel_path, content in file_bytes.items():
            dest = tmppath / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        attribution_paths: list[str] | None = None
        if cfg.attribution == "attributed":
            attribution_paths = _ATTRIBUTION_SURFACES
        identity_violations = verify(
            tmppath, anchors, mode=cfg.attribution, attribution_paths=attribution_paths
        )
        ci_violations = check_ci_boundary(tmppath)
        return identity_violations, ci_violations


# ---------------------------------------------------------------------------
# Catalogue.toml generation
# ---------------------------------------------------------------------------

def _toml_str(val: str) -> str:
    """Escape a string value for safe embedding in a TOML double-quoted string."""
    return val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _generate_catalogue_toml(cfg: SelfHostedInitConfig) -> str:
    lines: list[str] = [
        "[catalogue]",
        f'name = "{cfg.name}"',
        f'display_name = "{_toml_str(cfg.display_name or "")}"',
        f'description = "{_toml_str(cfg.description or "")}"',
        f'preferred_adapter = "{cfg.preferred_adapter or "claude-code"}"',
        "",
    ]
    if cfg.repository_url:
        lines += [
            "[catalogue.links]",
            f'repository = "{cfg.repository_url}"',
            "",
        ]
    lines += [
        "[[catalogue.maintainers]]",
        f'name = "{_toml_str(cfg.owner_name or "")}"',
    ]
    if cfg.owner_email:
        lines.append(f'email = "{cfg.owner_email}"')

    # B6: Vendored tooling mode writes [catalogue.tooling] section.
    if cfg.tooling == "vendored":
        adapters = cfg.adapters or [cfg.preferred_adapter or "claude-code"]
        adapters_toml = "[" + ", ".join(f'"{a}"' for a in adapters) + "]"
        lines += [
            "",
            "[catalogue.tooling]",
            'pack-roots = [".agentbundle/tooling/packs"]',
            'self-host-packs = ["catalogue-curation"]',
            f"adapters = {adapters_toml}",
        ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Ownership state persistence
# ---------------------------------------------------------------------------

def _load_ownership_state(target: Path) -> dict | None:
    """Read existing ownership state from target. Returns None if absent/unreadable."""
    state_path = target / _OWNERSHIP_STATE_FILE
    if not state_path.is_file():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _migrate_managed_paths(old_state: dict) -> list[dict]:
    """Convert schema-1 managed_paths (list[str]) to list[{path, sha256}]."""
    raw = old_state.get("managed_paths", [])
    result: list[dict] = []
    for entry in raw:
        if isinstance(entry, str):
            result.append({"path": entry, "sha256": None})
        elif isinstance(entry, dict) and "path" in entry:
            result.append(entry)
    return result


def _remove_stale_owned_paths(
    target: Path,
    old_state: dict,
    current_paths: set[str],
) -> tuple[list[str], list[str]]:
    """Remove stale owned paths (in old state, not in new plan) with guards.

    Path confinement: rejects entries whose resolved path escapes target.
    SHA guard: skips entries whose on-disk sha256 differs from recorded
    (user-modified), or whose recorded sha256 is None (schema-1 migration).

    Returns (removed_paths, warning_messages).
    """
    removed: list[str] = []
    warnings: list[str] = []

    paths_with_sha = _migrate_managed_paths(old_state)
    target_resolved = target.resolve()

    for entry in paths_with_sha:
        rel_path = entry.get("path", "")
        recorded_sha = entry.get("sha256")

        if not rel_path or rel_path in current_paths:
            continue

        # Path confinement guard.
        try:
            candidate = (target / rel_path).resolve()
            candidate.relative_to(target_resolved)
        except (ValueError, OSError):
            warnings.append(
                f"skipped removal of {rel_path!r}: path resolves outside target directory"
            )
            continue

        target_file = target / rel_path
        if not target_file.exists():
            continue

        # SHA guard: skip if no recorded sha256 (migrated from schema 1).
        if recorded_sha is None:
            warnings.append(
                f"skipped removal of {rel_path!r}: "
                "no recorded sha256 (migrated from schema 1 — cannot verify ownership)"
            )
            continue

        # SHA guard: skip if on-disk content differs (user edited the file).
        try:
            on_disk_sha = hashlib.sha256(target_file.read_bytes()).hexdigest()
        except OSError:
            continue
        if on_disk_sha != recorded_sha:
            warnings.append(
                f"skipped removal of {rel_path!r}: "
                "on-disk sha256 differs from recorded value (file may have been modified)"
            )
            continue

        try:
            target_file.unlink()
            removed.append(rel_path)
        except OSError as exc:
            warnings.append(f"failed to remove {rel_path!r}: {exc}")

    return removed, warnings


def _write_ownership_state(target: Path, state: SelfHostOwnershipState) -> None:
    state_path = target / _OWNERSHIP_STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8", newline="\n"
    )


# ---------------------------------------------------------------------------
# Next-steps builder
# ---------------------------------------------------------------------------

def _build_next_steps(cfg: SelfHostedInitConfig, pack_names: list[str]) -> list[str]:
    """Build post-init next steps for the result."""
    steps: list[str] = []
    if cfg.tooling == "external":
        # B7: library-level curation install plan per adapter.
        adapters = cfg.adapters or [cfg.preferred_adapter or "claude-code"]
        for adapter in adapters:
            steps.append(
                f"agentbundle install catalogue-curation --scope repo --adapter {adapter}"
            )
    else:
        steps.append(
            f"Vendored tooling at {_VENDORED_TOOLING_ROOT}/agentbundle/ — "
            "run: pip install -e .agentbundle/tooling/agentbundle/"
        )
    steps.append(
        f"Run: agentbundle catalogue verify --root {cfg.target} "
        "to confirm the target catalogue is well-formed"
    )
    return steps


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def init_self_hosted(cfg: SelfHostedInitConfig) -> SelfHostedInitResult:
    """Initialize a self-hosted catalogue at cfg.target from cfg.source.

    Returns a SelfHostedInitResult with ok=True on success.
    Exit semantics: result.ok=False → exit 1; violations present → exit 1.
    Usage errors (bad config) are raised as ValueError before this is called.
    """
    diagnostics: list[str] = []

    def _fail(*msgs: str, violations: list[Violation] | None = None) -> SelfHostedInitResult:
        return SelfHostedInitResult(
            ok=False,
            dry_run=cfg.dry_run,
            name=cfg.name or "",
            diagnostics=list(msgs),
            violations=violations or [],
        )

    # 1. Validate source (read catalogue.toml).
    source_meta, err = _read_source_catalogue(cfg.source)
    if err:
        return _fail(err)

    # 2. Check for outdated export-catalogue skill.
    export_cat_path = (
        cfg.source / "packs" / "catalogue-curation"
        / ".apm" / "skills" / "export-catalogue"
    )
    if export_cat_path.is_dir():
        return _fail(
            "source contains outdated catalogue-curation with export-catalogue — "
            "update source to 0.2.0 or later"
        )

    # 3. Vendored mode source validation.
    if cfg.tooling == "vendored":
        agentbundle_src = cfg.source / "packages" / "agentbundle"
        if not agentbundle_src.is_dir() or agentbundle_src.is_symlink():
            return _fail(
                "source is missing packages/agentbundle/ — "
                "vendored mode requires a self-hosted source catalogue, not a runtime archive"
            )

    # Build source provenance from source_meta for B12 JSON output.
    cat_meta = source_meta.get("catalogue", {})
    source_provenance = SelfHostedSource(
        name=cat_meta.get("name", ""),
        display_name=cat_meta.get("display_name", ""),
        archive_uri=cfg.archive_uri,
    )

    # 4. Collect fields (TTY prompts + defaults).
    # Capture whether any field was already supplied before defaults are filled in.
    field_collection_mode = "explicit" if any(
        [cfg.name, cfg.display_name, cfg.description, cfg.owner_name, cfg.owner_email]
    ) else "default"
    cfg = collect_fields(cfg, source_meta)

    # 5. Validate fields.
    errors = validate_fields(cfg)
    if errors:
        return _fail(*errors)

    # 6. Select packs and profiles.
    try:
        pack_names = select_packs(cfg.source, cfg.packs)
        profile_names = _select_profiles(cfg.source, cfg.profiles)
    except ValueError as exc:
        return _fail(str(exc))

    # 7. Build in-memory file content plan.
    file_bytes: dict[str, bytes] = {}
    file_kinds: dict[str, str] = {}

    # Copy packs.
    for pack_name in pack_names:
        src_pack = cfg.source / "packs" / pack_name
        _collect_dir_bytes(src_pack, f"packs/{pack_name}", file_bytes, file_kinds, kind="pack")

    # Copy profiles.
    for profile_name in profile_names:
        src_profile = cfg.source / "profiles" / f"{profile_name}.toml"
        if src_profile.is_file() and not src_profile.is_symlink():
            rel = f"profiles/{profile_name}.toml"
            file_bytes[rel] = src_profile.read_bytes()
            file_kinds[rel] = "profile"

    # Copy guides/_shared/ if requested.
    if cfg.guides == "selected":
        src_guides = cfg.source / "guides" / "_shared"
        if src_guides.is_dir() and not src_guides.is_symlink():
            _collect_dir_bytes(
                src_guides, "guides/_shared", file_bytes, file_kinds, kind="guide"
            )
        else:
            diagnostics.append("guides/_shared/ not found in source; skipping guide copy")

    # Vendored mode: copy agentbundle source and catalogue-curation.
    if cfg.tooling == "vendored":
        src_agentbundle = cfg.source / "packages" / "agentbundle"
        _collect_dir_bytes(
            src_agentbundle,
            f"{_VENDORED_TOOLING_ROOT}/agentbundle",
            file_bytes,
            file_kinds,
            kind="vendored",
            exclude=_VENDORED_ENGINE_EXCLUDE,
        )
        src_curation = cfg.source / "packs" / "catalogue-curation"
        if src_curation.is_dir() and not src_curation.is_symlink():
            _collect_dir_bytes(
                src_curation,
                f"{_VENDORED_TOOLING_ROOT}/packs/catalogue-curation",
                file_bytes,
                file_kinds,
                kind="vendored",
                exclude=_VENDORED_PACK_EXCLUDE,
            )
        else:
            diagnostics.append(
                "packs/catalogue-curation/ not found in source; skipping vendored curation copy"
            )

    # Generate catalogue.toml.
    cat_toml_content = _generate_catalogue_toml(cfg)
    file_bytes["catalogue.toml"] = cat_toml_content.encode("utf-8")
    file_kinds["catalogue.toml"] = "catalogue"

    # 8. Apply identity transform in-memory (white-label mode only).
    anchors = _build_anchors(source_meta)
    identity_replacements = _apply_identity_transform_bytes(file_bytes, anchors, cfg)

    # 9. Leak check (in-memory via tmpdir — runs in both real and dry-run mode
    # so --dry-run correctly surfaces violations without any target writes).
    id_violations, ci_violations = _verify_bytes_in_tmpdir(file_bytes, anchors, cfg)
    all_violations = id_violations + ci_violations
    if all_violations:
        return SelfHostedInitResult(
            ok=False,
            dry_run=cfg.dry_run,
            name=cfg.name,
            files_written=[],
            diagnostics=diagnostics,
            violations=all_violations,
            preset="self-hosted",
            tooling_mode=cfg.tooling,
            attribution_mode=cfg.attribution,
            selected_packs=pack_names,
            selected_profiles=profile_names,
            selected_adapters=cfg.adapters or [cfg.preferred_adapter or "claude-code"],
            field_collection_mode=field_collection_mode,
            identity_replacements=identity_replacements,
            leak_scan_result={
                "ok": False,
                "violation_count": len(all_violations),
            },
            source=source_provenance,
            summary="self-hosted init failed: identity leak check found violations",
        )
    leak_scan_result: dict = {"ok": True, "violation_count": 0}

    # 10. Load old ownership state; split planned files into owned vs new.
    old_state = _load_ownership_state(cfg.target)
    old_owned_paths: set[str] = set()
    if old_state:
        for entry in _migrate_managed_paths(old_state):
            if isinstance(entry, dict) and "path" in entry:
                old_owned_paths.add(entry["path"])

    owned_planned: list[tuple[str, bytes]] = [
        (rp, file_bytes[rp]) for rp in sorted(file_bytes) if rp in old_owned_paths
    ]
    new_planned_files: list[PlannedFile] = [
        PlannedFile(rel_path=rp, kind=file_kinds.get(rp, "file"), content=file_bytes[rp])
        for rp in sorted(file_bytes) if rp not in old_owned_paths
    ]

    files_written: list[tuple[str, str]] = []

    if cfg.dry_run:
        # Dry run: populate plan without touching disk.
        for rp, _ in owned_planned:
            files_written.append(("update", rp))
        for pf in new_planned_files:
            files_written.append(("create", pf.rel_path))
        # Ownership state entry (not written in dry run).
        files_written.append(("create", _OWNERSHIP_STATE_FILE))
    else:
        # 11. Classify conflicts for new files only (owned files always overwrite).
        file_plan = (
            classify_conflicts(cfg.target, new_planned_files) if new_planned_files else []
        )
        conflict_plans = [fp for fp in file_plan if fp.action == FileAction.CONFLICT]
        if conflict_plans:
            msgs = [fp.conflict_reason for fp in conflict_plans if fp.conflict_reason]
            return _fail(*(msgs or ["conflict detected in target directory"]))

        target_was_new = not cfg.target.exists()
        cfg.target.mkdir(parents=True, exist_ok=True)

        created_new_files: list[str] = []
        created_new_dirs: list[str] = []
        try:
            # Write owned files (overwrite).
            for rp, content in owned_planned:
                dest = cfg.target / rp
                dest.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(dest, content)
                files_written.append(("update", rp))

            # Write new files using commit_files from initialise.py.
            if new_planned_files:
                created_new_files, created_new_dirs = commit_files(
                    cfg.target, new_planned_files, file_plan
                )
                for rp in created_new_files:
                    files_written.append(("create", rp))
                for fp in file_plan:
                    if fp.action == FileAction.ALREADY_PRESENT:
                        files_written.append(("already-present", fp.path))
        except Exception as exc:
            rollback(cfg.target, created_new_files, created_new_dirs, target_was_new)
            return _fail(f"write failed: {exc}")

        # 12. Remove stale owned paths (only after new files are safely written).
        if old_state:
            _removed, skip_warnings = _remove_stale_owned_paths(
                cfg.target, old_state, set(file_bytes.keys())
            )
            diagnostics.extend(skip_warnings)

        # 13. Write ownership state (includes sha256 for each file).
        sha_map = {
            rp: hashlib.sha256(content).hexdigest()
            for rp, content in file_bytes.items()
        }
        adapters = cfg.adapters or [cfg.preferred_adapter or "claude-code"]
        new_state = SelfHostOwnershipState(
            managed_paths=[
                {"path": rp, "sha256": sha_map[rp]}
                for rp in sorted(sha_map.keys())
            ],
            adapters=adapters,
            managed_target_path=str(cfg.target),
            source_pack_identity=source_meta.get("catalogue", {}).get("name", ""),
            source_root_kind="self-hosted-source",
        )
        _write_ownership_state(cfg.target, new_state)
        files_written.append(("create", _OWNERSHIP_STATE_FILE))

    # 14. Build next steps.
    next_steps = _build_next_steps(cfg, pack_names)

    n_written = sum(1 for a, _ in files_written if a in ("create", "update"))
    return SelfHostedInitResult(
        ok=True,
        dry_run=cfg.dry_run,
        name=cfg.name,
        files_written=files_written,
        diagnostics=diagnostics,
        violations=all_violations,
        next_steps=next_steps,
        preset="self-hosted",
        tooling_mode=cfg.tooling,
        attribution_mode=cfg.attribution,
        selected_packs=pack_names,
        selected_profiles=profile_names,
        selected_adapters=cfg.adapters or [cfg.preferred_adapter or "claude-code"],
        field_collection_mode=field_collection_mode,
        identity_replacements=identity_replacements,
        leak_scan_result=leak_scan_result,
        source=source_provenance,
        summary=(
            f"self-hosted init {'(dry run) ' if cfg.dry_run else ''}complete: "
            f"{n_written} file(s) written to {cfg.name}"
        ),
    )
