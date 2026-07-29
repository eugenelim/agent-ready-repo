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

import json
import os
import re
import shutil
import sys
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")
_URL_RE = re.compile(r"^https?://\S+$")
# Reject userinfo (credentials) in URLs: https://user:pass@host is disallowed.
_URL_USERINFO_RE = re.compile(r"^https?://[^/@]*@")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Packs never copied to the target (they're tooling, not catalogue content).
_TOOLING_PACKS: frozenset[str] = frozenset({"catalogue-curation"})

# Attribution surfaces where upstream identity is allowed in attributed mode.
_ATTRIBUTION_SURFACES: list[str] = ["catalogue.toml", "ATTRIBUTION.md"]

# State file written to .agentbundle/ in the target.
_OWNERSHIP_STATE_FILE = ".agentbundle/self-host-state.json"

# Vendored tooling root inside the target.
_VENDORED_TOOLING_ROOT = ".agentbundle/tooling"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "command": "catalogue init",
            "operation": "self-hosted-init",
            "ok": self.ok,
            "dry_run": self.dry_run,
            "name": self.name,
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

    schema_version: str = "1"
    managed_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "managed_paths": sorted(self.managed_paths),
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
# File copy helpers
# ---------------------------------------------------------------------------

def _copy_dir(
    src_dir: Path,
    dst_dir: Path,
    *,
    dry_run: bool,
    written: list[tuple[str, str]],
    target_root: Path,
) -> None:
    """Recursively copy src_dir into dst_dir, following no symlinks."""
    for dirpath, dirnames, filenames in os.walk(str(src_dir), followlinks=False):
        dp = Path(dirpath)
        # Prune symlink dirs.
        dirnames[:] = [dn for dn in dirnames if not (dp / dn).is_symlink()]
        rel_to_src = dp.relative_to(src_dir)
        out_dir = dst_dir / rel_to_src
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
        for fname in filenames:
            src_file = dp / fname
            if src_file.is_symlink():
                continue
            dst_file = out_dir / fname
            rel_from_target = str(dst_file.relative_to(target_root))
            action = "already-present" if dst_file.exists() else "create"
            if not dry_run:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_file), str(dst_file))
            written.append((action, rel_from_target))


# ---------------------------------------------------------------------------
# Identity transformation
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
        # Remove the URL without a replacement — use a placeholder.
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


def _apply_identity_transform(
    target: Path,
    anchors: dict[str, str],
    cfg: SelfHostedInitConfig,
) -> None:
    """Walk target tree and apply identity replacement in text files."""
    if cfg.attribution == "attributed":
        return  # attributed mode keeps anchors intact
    for dirpath, dirnames, filenames in os.walk(str(target), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [dn for dn in dirnames if not (dp / dn).is_symlink()]
        for fname in filenames:
            fp = dp / fname
            if fp.is_symlink() or fp.suffix.lower() in BINARY_EXT:
                continue
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
                new_content = _transform_text(content, anchors, cfg)
                if new_content != content:
                    fp.write_text(new_content, encoding="utf-8")
            except OSError:
                continue


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
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Ownership state
# ---------------------------------------------------------------------------

def _write_ownership_state(
    target: Path,
    managed_paths: list[str],
    *,
    dry_run: bool,
) -> None:
    state = SelfHostOwnershipState(managed_paths=managed_paths)
    state_path = target / _OWNERSHIP_STATE_FILE
    if not dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8"
        )


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

    # 1. Validate source.
    source_meta, err = _read_source_catalogue(cfg.source)
    if err:
        return SelfHostedInitResult(ok=False, dry_run=cfg.dry_run, name="", diagnostics=[err])

    # 2. Collect fields (TTY prompts + defaults).
    cfg = collect_fields(cfg, source_meta)

    # 3. Validate fields.
    errors = validate_fields(cfg)
    if errors:
        return SelfHostedInitResult(
            ok=False, dry_run=cfg.dry_run, name=cfg.name or "", diagnostics=errors
        )

    # 4. Select packs and profiles.
    try:
        pack_names = select_packs(cfg.source, cfg.packs)
        profile_names = _select_profiles(cfg.source, cfg.profiles)
    except ValueError as exc:
        return SelfHostedInitResult(
            ok=False, dry_run=cfg.dry_run, name=cfg.name, diagnostics=[str(exc)]
        )

    # 5. Build file plan.
    files_written: list[tuple[str, str]] = []
    target = cfg.target

    if not cfg.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    # Copy packs.
    for pack_name in pack_names:
        src_pack = cfg.source / "packs" / pack_name
        dst_pack = target / "packs" / pack_name
        _copy_dir(
            src_pack, dst_pack,
            dry_run=cfg.dry_run, written=files_written, target_root=target,
        )

    # Copy profiles.
    for profile_name in profile_names:
        src_profile = cfg.source / "profiles" / f"{profile_name}.toml"
        dst_profile = target / "profiles" / f"{profile_name}.toml"
        if src_profile.is_file() and not src_profile.is_symlink():
            action = "already-present" if dst_profile.exists() else "create"
            if not cfg.dry_run:
                dst_profile.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_profile), str(dst_profile))
            files_written.append((action, str(dst_profile.relative_to(target))))

    # Copy guides/_shared/ if requested.
    if cfg.guides == "selected":
        src_guides = cfg.source / "guides" / "_shared"
        if src_guides.is_dir() and not src_guides.is_symlink():
            dst_guides = target / "guides" / "_shared"
            _copy_dir(
                src_guides, dst_guides,
                dry_run=cfg.dry_run, written=files_written, target_root=target,
            )
        else:
            diagnostics.append("guides/_shared/ not found in source; skipping guide copy")

    # Vendored mode: copy agentbundle source and catalogue-curation.
    if cfg.tooling == "vendored":
        src_agentbundle = cfg.source / "packages" / "agentbundle"
        if src_agentbundle.is_dir() and not src_agentbundle.is_symlink():
            dst_agentbundle = target / _VENDORED_TOOLING_ROOT / "agentbundle"
            _copy_dir(
                src_agentbundle, dst_agentbundle,
                dry_run=cfg.dry_run, written=files_written, target_root=target,
            )
        else:
            diagnostics.append(
                "packages/agentbundle/ not found in source; skipping vendored agentbundle copy"
            )

        src_curation = cfg.source / "packs" / "catalogue-curation"
        if src_curation.is_dir() and not src_curation.is_symlink():
            dst_curation = target / _VENDORED_TOOLING_ROOT / "packs" / "catalogue-curation"
            _copy_dir(
                src_curation, dst_curation,
                dry_run=cfg.dry_run, written=files_written, target_root=target,
            )
        else:
            diagnostics.append(
                "packs/catalogue-curation/ not found in source; skipping vendored curation copy"
            )

    # Generate catalogue.toml.
    cat_toml_content = _generate_catalogue_toml(cfg)
    cat_toml_path = target / "catalogue.toml"
    action = "already-present" if cat_toml_path.exists() else "create"
    if not cfg.dry_run:
        cat_toml_path.write_text(cat_toml_content, encoding="utf-8")
    files_written.append((action, "catalogue.toml"))

    # 6. Identity transformation (white-label: replace anchors; attributed: skip).
    if not cfg.dry_run:
        anchors = _build_anchors(source_meta)
        _apply_identity_transform(target, anchors, cfg)

        # 7. Leak check.
        attribution_paths: list[str] | None = None
        if cfg.attribution == "attributed":
            attribution_paths = _ATTRIBUTION_SURFACES
        violations = verify(
            target, anchors, mode=cfg.attribution, attribution_paths=attribution_paths
        )
        ci_violations = check_ci_boundary(target)
        all_violations = violations + ci_violations
    else:
        anchors = _build_anchors(source_meta)
        all_violations = []

    # 8. Rollback on violation — remove files we created before surfacing the error.
    if all_violations and not cfg.dry_run:
        for file_action, rel_path in files_written:
            if file_action == "create":
                (target / rel_path).unlink(missing_ok=True)
        return SelfHostedInitResult(
            ok=False,
            dry_run=cfg.dry_run,
            name=cfg.name,
            files_written=files_written,
            diagnostics=diagnostics,
            violations=all_violations,
        )

    # Write ownership state (only on success — no violations).
    managed = [p for _, p in files_written]
    managed.append(_OWNERSHIP_STATE_FILE)
    _write_ownership_state(target, managed, dry_run=cfg.dry_run)
    if not cfg.dry_run:
        files_written.append(("create", _OWNERSHIP_STATE_FILE))

    # 9. Build next steps.
    next_steps: list[str] = []
    if cfg.tooling == "external":
        next_steps.append(
            "Install catalogue-curation: pip install agentbundle && "
            "agentbundle install catalogue-curation --scope repo"
        )
    else:
        next_steps.append(
            f"Vendored tooling at {_VENDORED_TOOLING_ROOT}/agentbundle/ — "
            "run: pip install -e .agentbundle/tooling/agentbundle/"
        )
    next_steps.append(
        f"Run: agentbundle catalogue verify --root {target} "
        "to confirm the target catalogue is well-formed"
    )
    if all_violations:
        next_steps = []  # violations supersede next steps

    return SelfHostedInitResult(
        ok=not bool(all_violations),
        dry_run=cfg.dry_run,
        name=cfg.name,
        files_written=files_written,
        diagnostics=diagnostics,
        violations=all_violations,
        next_steps=next_steps,
    )
