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
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

from agentbundle.build.user_libs import PACK_NAME as _USER_LIBS_PACK
from agentbundle.build.user_libs import PACKAGE_SUBPATH as _USER_LIBS_PACKAGE_SUBPATH
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
    sha256_confined_regular_file,
    validate_confined_directory,
)
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
from agentbundle.scope import shipped_adapters_from_contract

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
_OWNERSHIP_STATE_MAX_BYTES = 4 * 1024 * 1024
_RECIPE_TEXT_MAX_LENGTH = 4096

# Vendored tooling root inside the target.
_VENDORED_TOOLING_ROOT = ".agentbundle/tooling"

# RFC-0082 / ADR-0075 D3: the vendored copy is wheel-class — the command tells
# the adopter to `pip install -e` it, so it is an install source, not a source
# tree, and carries no test content. Relative to each vendored call's own root.
# The engine root is `packages/agentbundle/`, so its suite sits at `tests/` and
# a root `conftest.py` sits beside the package; both are test content.
_VENDORED_ENGINE_EXCLUDE: tuple[str, ...] = (
    "tests/",
    "conftest.py",
    # Root-relative, so `agentbundle/build/` — the shipped package — is
    # untouched. These are setuptools output at the collect root only.
    "build/",
    "dist/",
)

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
# `build` and `dist` are deliberately NOT here. `agentbundle/build/` is the
# shipped build-pipeline package — adapters, projections, recipes, self_host —
# and pruning that name at any depth removes it, leaving an engine that cannot
# import. A bare `build` matching at any depth is the trap, and it bit this
# very fix. Root-relative build output is pruned through the ordinary
# `prune` mechanism instead; see `_VENDORED_ENGINE_EXCLUDE`.
_BUILD_RESIDUE_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".tox",
        "node_modules",
        ".venv",
        "venv",
        "htmlcov",
    }
)
_BUILD_RESIDUE_FILES: frozenset[str] = frozenset({".DS_Store", "coverage.xml"})
_VENDORED_PACK_EXCLUDE: tuple[str, ...] = ("tests/",)

# The credbroker project directory: the parent of the package `user_libs`
# resolves. `user_libs._package_source_dir` looks for the package at
# `packs_dir.parent / PACKAGE_SUBPATH`, i.e. `<catalogue root>/packages/
# credbroker/credbroker/`, so a derived catalogue must carry it at exactly that
# path. Derived from the resolver's own constant rather than re-spelled, so the
# copy follows the resolver if that path ever moves.
#
# Absent it, `compute_projections` finds no sources and returns `[]`, which
# makes BOTH its consumers silent no-ops in the derived tree: `apply_projection`
# writes no `.agentbundle/lib/credbroker/` floor, and `check_drift` compares
# nothing and reports clean. The pack-vendored copy under
# `.apm/user-libs/credbroker/` still arrives with the pack, so credbroker still
# runs — as frozen content with no source and no drift signal.
#
# This is deliberately NOT the `packages/agentbundle/` treatment. That one is
# vendored to `.agentbundle/tooling/agentbundle/` because it is an *install
# source* the adopter `pip install -e`s. credbroker is a *build input resolved
# by relative path*. Same principle, different mechanics: the two paths are not
# interchangeable and must not be reconciled.
_USER_LIBS_PACKAGE_DIR: str = _USER_LIBS_PACKAGE_SUBPATH.parent.as_posix()

# No test content ships to a derived catalogue — the same boundary
# `_VENDORED_PACK_EXCLUDE` draws. `user_libs.collect_sources` already excludes
# `tests` from the projection, so the drift gate compares the same file set
# either way and this costs the gate nothing.
_USER_LIBS_PACKAGE_EXCLUDE: tuple[str, ...] = ("tests/",)


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
class SelfHostRecipe:
    """Record the resolved inputs needed to reproduce a self-hosted init."""

    packs: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    guides: str = "selected"
    attribution: str = "white-label"
    tooling: str = "external"
    name: str = ""
    display_name: str = ""
    description: str = ""
    owner_name: str = ""
    owner_email: str = ""
    preferred_adapter: str = ""
    repository_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON representation of the resolved recipe."""
        return {
            "packs": self.packs,
            "profiles": self.profiles,
            "guides": self.guides,
            "attribution": self.attribution,
            "tooling": self.tooling,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "owner_name": self.owner_name,
            "owner_email": self.owner_email,
            "preferred_adapter": self.preferred_adapter,
            "repository_url": self.repository_url,
        }


@dataclass
class _SelfHostRecipeInput:
    """Validated, optional recipe values read from an untrusted state file."""

    packs: list[str] | None = None
    profiles: list[str] | None = None
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    preferred_adapter: str | None = None
    repository_url: str | None = None


@dataclass
class SelfHostPin:
    """Record source provenance available at the time of self-hosted init."""

    source_uri: str | None = None
    source_revision: str | None = None
    archive_sha256: str | None = None
    synced_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return the pin, omitting source identity outside attributed mode."""
        result: dict[str, Any] = {
            "source_revision": self.source_revision,
            "archive_sha256": self.archive_sha256,
            "synced_at": self.synced_at,
        }
        if self.source_uri is not None:
            result["source_uri"] = self.source_uri
        return result


@dataclass
class SelfHostOwnershipState:
    """Track the write set, replay recipe, and source pin for future updates."""

    schema_version: str = "3"
    managed_paths: list[dict] = field(default_factory=list)  # [{path, sha256}]
    adapters: list[str] = field(default_factory=list)
    managed_target_path: str = ""
    source_pack_identity: str = ""
    source_root_kind: str = "self-hosted-source"
    recipe: SelfHostRecipe = field(default_factory=SelfHostRecipe)
    pin: SelfHostPin = field(default_factory=SelfHostPin)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "managed_paths": sorted(self.managed_paths, key=lambda x: x.get("path", "")),
            "adapters": sorted(self.adapters),
            "managed_target_path": self.managed_target_path,
            "source_pack_identity": self.source_pack_identity,
            "source_root_kind": self.source_root_kind,
            "recipe": self.recipe.to_dict(),
            "pin": self.pin.to_dict(),
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


def _resolve_field(prompt_text: str, default: str, *, interactive: bool) -> str:
    """Return default without prompting when not interactive.

    A replay caller (``interactive=False``) never reaches ``_prompt``: the
    resolved value must come from a flag or that flag's safe default, never
    from a recorded recipe read back through a prompt seed.
    """
    if not interactive:
        return default
    return _prompt(prompt_text) or default


def _recipe_diagnostic(field_name: str, reason: str) -> str:
    """Describe a discarded state value without echoing attacker-controlled text."""
    return (
        f"discarded recorded {field_name} from {_OWNERSHIP_STATE_FILE}: {reason}"
    )


def _is_safe_recipe_text(value: object, *, allow_empty: bool = False) -> bool:
    """Return whether a recorded scalar is bounded and terminal-safe."""
    return (
        isinstance(value, str)
        and (allow_empty or bool(value))
        and len(value) <= _RECIPE_TEXT_MAX_LENGTH
        and value == value.strip()
        and not any(
            unicodedata.category(character) in {"Cc", "Cf"} for character in value
        )
    )


def _read_recipe_selection(
    raw_recipe: dict[str, Any],
    field_name: str,
    available: set[str],
    diagnostics: list[str],
) -> list[str] | None:
    """Return a recorded selection only when every entry is a shipped name."""
    if field_name not in raw_recipe:
        return None
    value = raw_recipe[field_name]
    if not isinstance(value, list) or not all(
        _is_safe_recipe_text(item) and item in available for item in value
    ):
        diagnostics.append(
            _recipe_diagnostic(field_name, "selection is not shipped by the source")
        )
        return None
    return value


def _load_self_host_recipe(
    raw_state: dict[str, Any] | None,
    source: Path,
    diagnostics: list[str],
) -> _SelfHostRecipeInput | None:
    """Constrain the replay recipe from an already confined ownership state."""
    if raw_state is None:
        return None
    if "recipe" not in raw_state:
        return None
    raw_recipe = raw_state["recipe"]
    if not isinstance(raw_recipe, dict):
        diagnostics.append(_recipe_diagnostic("recipe", "recipe is not an object"))
        return None

    available_packs = set(select_packs(source, None))
    available_profiles = set(_select_profiles(source, None))
    recipe = _SelfHostRecipeInput(
        packs=_read_recipe_selection(
            raw_recipe, "packs", available_packs, diagnostics
        ),
        profiles=_read_recipe_selection(
            raw_recipe, "profiles", available_profiles, diagnostics
        ),
    )

    validators = {
        "name": lambda value: bool(_SAFE_NAME_RE.fullmatch(value)),
        "display_name": lambda _value: True,
        "description": lambda _value: True,
        "owner_name": lambda _value: True,
        "owner_email": lambda value: not value or bool(_EMAIL_RE.fullmatch(value)),
        "repository_url": lambda value: bool(_URL_RE.fullmatch(value))
        and not _URL_USERINFO_RE.match(value),
    }
    for field_name, validator in validators.items():
        if field_name not in raw_recipe:
            continue
        value = raw_recipe[field_name]
        if field_name == "repository_url" and value is None:
            continue
        allow_empty = field_name == "owner_email"
        if not _is_safe_recipe_text(value, allow_empty=allow_empty) or not validator(value):
            diagnostics.append(
                _recipe_diagnostic(field_name, "value failed its read-time constraint")
            )
            continue
        setattr(recipe, field_name, value)

    if "preferred_adapter" in raw_recipe:
        value = raw_recipe["preferred_adapter"]
        try:
            available_adapters = set(shipped_adapters_from_contract())
        except (OSError, RuntimeError, tomllib.TOMLDecodeError):
            available_adapters = set()
        if (
            _is_safe_recipe_text(value)
            and isinstance(value, str)
            and value in available_adapters
        ):
            recipe.preferred_adapter = value
        else:
            diagnostics.append(
                _recipe_diagnostic(
                    "preferred_adapter", "value is not a shipped adapter name"
                )
            )
    return recipe


def collect_fields(
    cfg: SelfHostedInitConfig,
    source_meta: dict[str, Any],
    recipe: _SelfHostRecipeInput | None = None,
    *,
    interactive: bool = True,
) -> SelfHostedInitConfig:
    """Return a resolved copy of cfg with defaults filled in.

    TTY-gated: prompts for missing required fields when stdin is a TTY and
    ``interactive`` is True; falls back to derived defaults otherwise. A
    replay caller passes ``interactive=False`` so a recorded recipe value
    never reaches the prompt seed on a TTY.
    """
    cat = source_meta.get("catalogue", {})

    recipe = recipe or _SelfHostRecipeInput()
    name = cfg.name
    if not name:
        default_name = recipe.name or _derive_name(cfg.target)
        name = _resolve_field(
            f"Catalogue name [{default_name}]: ", default_name, interactive=interactive
        )

    display_name = cfg.display_name
    if not display_name:
        default_display_name = recipe.display_name or (
            name.replace("-", " ").replace("_", " ").title()
        )
        display_name = _resolve_field(
            f"Display name [{default_display_name}]: ",
            default_display_name,
            interactive=interactive,
        )

    description = cfg.description
    if not description:
        src_name = cat.get("name", "upstream")
        default_description = (
            recipe.description
            or f"A self-hosted catalogue derived from {src_name}."
        )
        description = _resolve_field(
            f"Description [{default_description}]: ",
            default_description,
            interactive=interactive,
        )

    owner_name = cfg.owner_name
    if not owner_name:
        default_owner_name = recipe.owner_name or display_name
        owner_prompt = (
            f"Owner name [{default_owner_name}]: "
            if recipe.owner_name is not None
            else "Owner name: "
        )
        owner_name = _resolve_field(
            owner_prompt, default_owner_name, interactive=interactive
        )

    owner_email = cfg.owner_email
    if not owner_email:
        default_owner_email = recipe.owner_email or ""
        email_prompt = (
            f"Owner email [{default_owner_email}]: "
            if recipe.owner_email is not None
            else "Owner email: "
        )
        owner_email = _resolve_field(
            email_prompt, default_owner_email, interactive=interactive
        )

    preferred_adapter = (
        cfg.preferred_adapter
        or recipe.preferred_adapter
        or cat.get("preferred_adapter", "claude-code")
    )
    repository_url = (
        cfg.repository_url
        if cfg.repository_url is not None
        else recipe.repository_url
    )

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
        repository_url=repository_url,
        archive_uri=cfg.archive_uri,
        packs=cfg.packs if cfg.packs is not None else recipe.packs,
        adapters=cfg.adapters,
        profiles=cfg.profiles if cfg.profiles is not None else recipe.profiles,
        dry_run=cfg.dry_run,
    )


def validate_fields(
    cfg: SelfHostedInitConfig, *, recorded_recipe: SelfHostRecipe | None = None
) -> list[str]:
    """Return list of validation error messages (empty = valid)."""
    errors: list[str] = []
    recipe = recorded_recipe or SelfHostRecipe(
        name=cfg.name or "",
        display_name=cfg.display_name or "",
        description=cfg.description or "",
        owner_name=cfg.owner_name or "",
        owner_email=cfg.owner_email or "",
        preferred_adapter=cfg.preferred_adapter or "",
        repository_url=cfg.repository_url,
    )
    replay_scalars = {
        "name": recipe.name,
        "display-name": recipe.display_name,
        "description": recipe.description,
        "owner-name": recipe.owner_name,
        "owner-email": recipe.owner_email,
        "preferred-adapter": recipe.preferred_adapter,
        "repository-url": recipe.repository_url,
    }
    for field_name, value in replay_scalars.items():
        if value is None and field_name == "repository-url":
            continue
        if not _is_safe_recipe_text(value, allow_empty=field_name == "owner-email"):
            errors.append(
                f"{field_name} cannot be recorded for replay: "
                "must have no surrounding whitespace or control characters "
                f"and be at most {_RECIPE_TEXT_MAX_LENGTH} characters"
            )
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
    if cfg.preferred_adapter:
        try:
            available_adapters = set(shipped_adapters_from_contract())
        except (OSError, RuntimeError, tomllib.TOMLDecodeError):
            available_adapters = set()
        if cfg.preferred_adapter not in available_adapters:
            errors.append("preferred-adapter is not a shipped adapter name")
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
    # Build residue is never authored source. Prune it independently from
    # `exclude`: adopter pack tests remain included, while caches and bytecode
    # never leak local paths or test node IDs into a materialized catalogue.
    for dirpath, dirnames, filenames in os.walk(str(src_dir), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [dn for dn in dirnames if not (dp / dn).is_symlink()]
        rel_to_src = dp.relative_to(src_dir)
        rel_dir = rel_to_src.as_posix()
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
            if (
                fname in _BUILD_RESIDUE_FILES
                or fname.startswith(".coverage")
                or fname.endswith((".pyc", ".pyo"))
            ):
                continue
            if drop and (
                fname if rel_dir == "." else f"{rel_dir}/{fname}"
            ) in drop:
                continue
            rel_path = (Path(dst_prefix) / rel_to_src / fname).as_posix()
            file_bytes[rel_path] = read_confined_regular_file(src_dir, src_file)
            file_kinds[rel_path] = kind


# ---------------------------------------------------------------------------
# Identity transformation (in-memory)
# ---------------------------------------------------------------------------

def _is_attributed(cfg: SelfHostedInitConfig) -> bool:
    """Return whether upstream identity may be retained in generated output."""
    return cfg.attribution == "attributed"


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
    if _is_attributed(cfg):
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


def _transform_recipe_string(
    value: str | None,
    anchors: dict[str, str],
    cfg: SelfHostedInitConfig,
) -> str | None:
    """Apply the tree's identity transform semantics to one recipe value."""
    if value is None or _is_attributed(cfg):
        return value
    return _transform_text(value, anchors, cfg)


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
        if _is_attributed(cfg):
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
    escapes = {
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
        '"': '\\"',
        "\\": "\\\\",
    }
    encoded: list[str] = []
    for character in val:
        if character in escapes:
            encoded.append(escapes[character])
        elif ord(character) <= 0x1F or ord(character) == 0x7F:
            encoded.append(f"\\u{ord(character):04X}")
        else:
            encoded.append(character)
    return "".join(encoded)


def _generate_catalogue_toml(cfg: SelfHostedInitConfig) -> str:
    lines: list[str] = [
        "[catalogue]",
        f'name = "{_toml_str(cfg.name or "")}"',
        f'display_name = "{_toml_str(cfg.display_name or "")}"',
        f'description = "{_toml_str(cfg.description or "")}"',
        f'preferred_adapter = "{_toml_str(cfg.preferred_adapter or "claude-code")}"',
        "",
    ]
    if cfg.repository_url:
        lines += [
            "[catalogue.links]",
            f'repository = "{_toml_str(cfg.repository_url or "")}"',
            "",
        ]
    lines += [
        "[[catalogue.maintainers]]",
        f'name = "{_toml_str(cfg.owner_name or "")}"',
    ]
    if cfg.owner_email:
        lines.append(f'email = "{_toml_str(cfg.owner_email)}"')

    # B6: Vendored tooling mode writes [catalogue.tooling] section.
    if cfg.tooling == "vendored":
        adapters = cfg.adapters or [cfg.preferred_adapter or "claude-code"]
        adapters_toml = "[" + ", ".join(f'"{_toml_str(a)}"' for a in adapters) + "]"
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

def _load_ownership_state(
    target: Path, diagnostics: list[str]
) -> dict[str, Any] | None:
    """Read ownership state once through the bounded confinement boundary."""
    state_path = target / _OWNERSHIP_STATE_FILE
    if not state_path.exists() and not state_path.is_symlink():
        return None
    try:
        data = json.loads(
            read_confined_regular_file(
                target, state_path, max_bytes=_OWNERSHIP_STATE_MAX_BYTES
            ).decode("utf-8")
        )
        if not isinstance(data, dict):
            diagnostics.append(_recipe_diagnostic("recipe", "state is not an object"))
            return None
        return data
    except (
        UnsafeContentError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        OSError,
        RecursionError,
    ):
        diagnostics.append(
            _recipe_diagnostic("recipe", "state file could not be read safely")
        )
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


def _plan_stale_owned_paths(
    target: Path,
    old_state: dict,
    current_paths: set[str],
) -> tuple[list[str], list[str]]:
    """Plan safe removal of stale owned paths and report every decline.

    The confined hash helper rejects escaping, link-like, non-regular, and
    unreadable entries before comparison.  A reason is emitted for each entry
    that cannot leave this guard as removable.

    Returns ``(removable_paths, decline_reasons)`` in recorded-path order.
    """
    removable: list[str] = []
    reasons: list[str] = []

    paths_with_sha = _migrate_managed_paths(old_state)

    for entry in paths_with_sha:
        rel_path = entry.get("path", "")
        recorded_sha = entry.get("sha256")

        if not rel_path:
            reasons.append(
                "skipped removal of '': malformed-recorded-path"
            )
            continue
        if rel_path in current_paths:
            reasons.append(
                f"skipped removal of {rel_path!r}: path-remains-current"
            )
            continue

        target_file = target / rel_path
        try:
            validate_confined_directory(target, target_file.parent)
        except UnsafeContentError:
            reasons.append(
                f"skipped removal of {rel_path!r}: path-confinement-refused"
            )
            continue
        if not target_file.exists():
            reasons.append(
                f"skipped removal of {rel_path!r}: recorded-path-absent"
            )
            continue

        # SHA guard: skip if no recorded sha256 (migrated from schema 1).
        if recorded_sha is None:
            reasons.append(
                f"skipped removal of {rel_path!r}: missing-recorded-sha256"
            )
            continue

        # SHA guard: skip if on-disk content differs (user edited the file).
        try:
            on_disk_sha = sha256_confined_regular_file(target, target_file)
        except UnsafeContentError:
            reasons.append(
                f"skipped removal of {rel_path!r}: recorded-entry-unreadable"
            )
            continue
        if on_disk_sha != recorded_sha:
            reasons.append(
                f"skipped removal of {rel_path!r}: recorded-sha256-mismatch"
            )
            continue

        removable.append(rel_path)

    return removable, reasons


def _remove_stale_owned_paths(
    target: Path,
    old_state: dict,
    current_paths: set[str],
) -> tuple[list[str], list[str]]:
    """Remove only the stale paths admitted by :func:`_plan_stale_owned_paths`."""
    removable, warnings = _plan_stale_owned_paths(target, old_state, current_paths)
    removed: list[str] = []

    for rel_path in removable:
        try:
            (target / rel_path).unlink()
            removed.append(rel_path)
        except OSError as exc:
            warnings.append(f"failed to remove {rel_path!r}: {exc}")

    return removed, warnings


def _write_ownership_state(target: Path, state: SelfHostOwnershipState) -> None:
    state_path = target / _OWNERSHIP_STATE_FILE
    if state_path.parent.is_symlink() or state_path.is_symlink():
        raise UnsafeContentError("ownership state path must not be a symlink")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(
        state_path,
        (json.dumps(state.to_dict(), indent=2) + "\n").encode("utf-8"),
    )


def _source_pack_identity(
    source_meta: dict[str, Any], cfg: SelfHostedInitConfig
) -> str:
    """Return the pin recorded in the committed ownership state file.

    Under ``attributed``, that is the source catalogue's name — the accurate
    provenance pin, and permitted because attributed mode makes no promise of
    anonymity.

    Otherwise it is the **derived** catalogue's name. The source name is
    identity anchor #1, and ``verify()`` allows it zero hits anywhere in
    white-label mode. But the leak check runs over the planned ``file_bytes``
    map, and ``_OWNERSHIP_STATE_FILE`` is written afterwards and is never in
    that map — so pinning the source name here would ship the exact banned
    string in a file the adopter commits, past a control that cannot see it.

    Bringing the state file inside the leak check would instead make a usable
    pin impossible in the very mode that most needs control over what ships,
    so the value changes rather than the check's scope.

    The branch is on ``attributed`` rather than on ``white-label`` so that any
    other value fails closed to the non-disclosing pin, matching how
    ``_apply_identity_transform_bytes`` and ``verify`` both treat ``attributed``
    as the single exception.

    Note for editors: this module's own prose is vendored into a target and
    scanned. ``_transform_text`` replaces anchors case-sensitively while
    ``verify`` matches case-insensitively, so a differently-cased echo of an
    anchor value here survives replacement and then fails the leak check. Keep
    identity wording generic.
    """
    if _is_attributed(cfg):
        return source_meta.get("catalogue", {}).get("name", "")
    return cfg.name or ""


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

class ReplayError(Exception):
    """A step 1-6 source or field precondition failed inside :func:`replay_derivation`.

    Carries the exact diagnostic messages ``init_self_hosted``'s inline
    ``_fail()`` closure previously returned directly, plus ``cfg`` as of the
    failure — after ``collect_fields`` when the failure happens downstream of
    it — so a caller reproduces the same ``SelfHostedInitResult`` unchanged.
    """

    def __init__(self, cfg: SelfHostedInitConfig, messages: list[str]) -> None:
        super().__init__("; ".join(messages) or "replay failed")
        self.cfg = cfg
        self.messages = messages


@dataclass
class DerivationReplay:
    """The in-memory result of replaying steps 1-9 of a self-hosted derivation.

    Never touches ``cfg.target``. Carries everything ``init_self_hosted``'s
    write phase (steps 10-14) needs to finish the run, and everything a
    read-only caller such as ``sync`` needs to report a plan without writing.
    """

    config: SelfHostedInitConfig
    source_meta: dict[str, Any]
    source: SelfHostedSource
    old_state: dict[str, Any] | None
    field_collection_mode: str
    recorded_recipe: SelfHostRecipe
    pack_names: list[str]
    profile_names: list[str]
    file_bytes: dict[str, bytes]
    file_kinds: dict[str, str]
    anchors: dict[str, str]
    identity_replacements: list[dict]
    violations: list[Violation]
    diagnostics: list[str]


def replay_derivation(
    cfg: SelfHostedInitConfig, *, interactive: bool = True
) -> DerivationReplay:
    """Replay steps 1-9 of a self-hosted derivation without writing.

    Validates the source, resolves fields, selects packs and profiles, builds
    the in-memory file plan, applies the identity transform, and runs the
    identity leak check — the same one ``init`` applies, against the same
    anchor set built from the same source metadata. Raises
    :class:`ReplayError` on any step 1-6 precondition failure. ``cfg.target``
    is read (old ownership state) but never written.

    ``interactive`` threads through to :func:`collect_fields`: ``init`` calls
    this with the default ``True`` so a TTY still prompts; a read-only replay
    caller such as ``sync`` passes ``False``.
    """
    diagnostics: list[str] = []

    def _fail(*msgs: str) -> NoReturn:
        raise ReplayError(cfg, [*diagnostics, *msgs])

    # 1. Validate source (read catalogue.toml).
    source_meta, err = _read_source_catalogue(cfg.source)
    if err:
        _fail(err)

    # 2. Check for outdated export-catalogue skill.
    export_cat_path = (
        cfg.source / "packs" / "catalogue-curation"
        / ".apm" / "skills" / "export-catalogue"
    )
    if export_cat_path.is_dir():
        _fail(
            "source contains outdated catalogue-curation with export-catalogue — "
            "update source to 0.2.0 or later"
        )

    # 3. Vendored mode source validation.
    if cfg.tooling == "vendored":
        agentbundle_src = cfg.source / "packages" / "agentbundle"
        if not agentbundle_src.is_dir() or agentbundle_src.is_symlink():
            _fail(
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

    old_state = _load_ownership_state(cfg.target, diagnostics)
    recipe = _load_self_host_recipe(old_state, cfg.source, diagnostics)

    # 4. Collect fields (TTY prompts + defaults).
    # Capture whether any field was already supplied before defaults are filled in.
    field_collection_mode = "explicit" if any(
        [cfg.name, cfg.display_name, cfg.description, cfg.owner_name, cfg.owner_email]
    ) else "default"
    cfg = collect_fields(cfg, source_meta, recipe, interactive=interactive)

    # 5. Transform the replay values, then validate the exact values that the
    # ownership state will record.
    anchors = _build_anchors(source_meta)
    recorded_recipe = SelfHostRecipe(
        guides=cfg.guides,
        attribution=cfg.attribution,
        tooling=cfg.tooling,
        name=_transform_recipe_string(cfg.name, anchors, cfg) or "",
        display_name=_transform_recipe_string(cfg.display_name, anchors, cfg) or "",
        description=_transform_recipe_string(cfg.description, anchors, cfg) or "",
        owner_name=_transform_recipe_string(cfg.owner_name, anchors, cfg) or "",
        owner_email=_transform_recipe_string(cfg.owner_email, anchors, cfg) or "",
        preferred_adapter=(
            _transform_recipe_string(cfg.preferred_adapter, anchors, cfg) or ""
        ),
        repository_url=_transform_recipe_string(cfg.repository_url, anchors, cfg),
    )
    errors = validate_fields(cfg, recorded_recipe=recorded_recipe)
    if errors:
        _fail(*errors)

    # 6. Select packs and profiles.
    try:
        pack_names = select_packs(cfg.source, cfg.packs)
        profile_names = _select_profiles(cfg.source, cfg.profiles)
    except ValueError as exc:
        _fail(str(exc))

    # 7. Build in-memory file content plan.
    file_bytes: dict[str, bytes] = {}
    file_kinds: dict[str, str] = {}

    def _collect_source_dir(
        src_dir: Path,
        dst_prefix: str,
        *,
        kind: str,
        exclude: tuple[str, ...] = (),
    ) -> str | None:
        try:
            _collect_dir_bytes(
                src_dir,
                dst_prefix,
                file_bytes,
                file_kinds,
                kind=kind,
                exclude=exclude,
            )
        except UnsafeContentError as exc:
            return f"unsafe source content: {exc}"
        return None

    # Copy packs.
    for pack_name in pack_names:
        src_pack = cfg.source / "packs" / pack_name
        collect_error = _collect_source_dir(
            src_pack, f"packs/{pack_name}", kind="pack"
        )
        if collect_error:
            _fail(collect_error)

    # Copy profiles.
    for profile_name in profile_names:
        src_profile = cfg.source / "profiles" / f"{profile_name}.toml"
        if src_profile.is_file() and not src_profile.is_symlink():
            rel = f"profiles/{profile_name}.toml"
            try:
                file_bytes[rel] = read_confined_regular_file(
                    cfg.source / "profiles", src_profile
                )
            except UnsafeContentError as exc:
                _fail(f"unsafe source content: {exc}")
            file_kinds[rel] = "profile"

    # Copy guides/_shared/ if requested.
    if cfg.guides == "selected":
        src_guides = cfg.source / "guides" / "_shared"
        if src_guides.is_dir() and not src_guides.is_symlink():
            collect_error = _collect_source_dir(
                src_guides, "guides/_shared", kind="guide"
            )
            if collect_error:
                _fail(collect_error)
        else:
            diagnostics.append("guides/_shared/ not found in source; skipping guide copy")

    # Root catalogue conformance ships in both tooling modes. Roster tests are
    # deliberately outside this explicit source boundary.
    src_conformance = cfg.source / "tests" / "conformance"
    if src_conformance.is_dir() and not src_conformance.is_symlink():
        collect_error = _collect_source_dir(
            src_conformance,
            "tests/conformance",
            kind="conformance",
        )
        if collect_error:
            _fail(collect_error)

    # The credbroker package source travels with the pack that vendors it, in
    # BOTH tooling modes — it is a build input the user-libs projection resolves
    # by relative path, not an install source. See _USER_LIBS_PACKAGE_DIR.
    if _USER_LIBS_PACK in pack_names:
        src_user_libs = cfg.source / _USER_LIBS_PACKAGE_DIR
        if src_user_libs.is_dir() and not src_user_libs.is_symlink():
            collect_error = _collect_source_dir(
                src_user_libs,
                _USER_LIBS_PACKAGE_DIR,
                kind="package",
                exclude=_USER_LIBS_PACKAGE_EXCLUDE,
            )
            if collect_error:
                _fail(collect_error)
        else:
            diagnostics.append(
                f"{_USER_LIBS_PACKAGE_DIR}/ not found in source; the "
                f"{_USER_LIBS_PACK} pack ships without its package source, so "
                "the user-libs projection and its drift gate stay inert"
            )

    # Vendored mode: copy agentbundle source and catalogue-curation.
    if cfg.tooling == "vendored":
        src_agentbundle = cfg.source / "packages" / "agentbundle"
        collect_error = _collect_source_dir(
            src_agentbundle,
            f"{_VENDORED_TOOLING_ROOT}/agentbundle",
            kind="vendored",
            exclude=_VENDORED_ENGINE_EXCLUDE,
        )
        if collect_error:
            _fail(collect_error)
        src_curation = cfg.source / "packs" / "catalogue-curation"
        if src_curation.is_dir() and not src_curation.is_symlink():
            collect_error = _collect_source_dir(
                src_curation,
                f"{_VENDORED_TOOLING_ROOT}/packs/catalogue-curation",
                kind="vendored",
                exclude=_VENDORED_PACK_EXCLUDE,
            )
            if collect_error:
                _fail(collect_error)
        else:
            diagnostics.append(
                "packs/catalogue-curation/ not found in source; skipping vendored curation copy"
            )

    # Generate catalogue.toml.
    cat_toml_content = _generate_catalogue_toml(cfg)
    file_bytes["catalogue.toml"] = cat_toml_content.encode("utf-8")
    file_kinds["catalogue.toml"] = "catalogue"

    # 8. Apply identity transform in-memory (white-label mode only).
    identity_replacements = _apply_identity_transform_bytes(file_bytes, anchors, cfg)

    # 9. Leak check (in-memory via tmpdir — runs in both real and dry-run mode
    # so --dry-run correctly surfaces violations without any target writes).
    id_violations, ci_violations = _verify_bytes_in_tmpdir(file_bytes, anchors, cfg)
    all_violations = id_violations + ci_violations

    return DerivationReplay(
        config=cfg,
        source_meta=source_meta,
        source=source_provenance,
        old_state=old_state,
        field_collection_mode=field_collection_mode,
        recorded_recipe=recorded_recipe,
        pack_names=pack_names,
        profile_names=profile_names,
        file_bytes=file_bytes,
        file_kinds=file_kinds,
        anchors=anchors,
        identity_replacements=identity_replacements,
        violations=all_violations,
        diagnostics=diagnostics,
    )


def init_self_hosted(cfg: SelfHostedInitConfig) -> SelfHostedInitResult:
    """Initialize a self-hosted catalogue at cfg.target from cfg.source.

    Returns a SelfHostedInitResult with ok=True on success.
    Exit semantics: result.ok=False → exit 1; violations present → exit 1.
    Usage errors (bad config) are raised as ValueError before this is called.
    """
    try:
        replay = replay_derivation(cfg)
    except ReplayError as exc:
        return SelfHostedInitResult(
            ok=False,
            dry_run=exc.cfg.dry_run,
            name=exc.cfg.name or "",
            diagnostics=exc.messages,
            violations=[],
        )

    cfg = replay.config
    diagnostics: list[str] = list(replay.diagnostics)
    pack_names = replay.pack_names
    profile_names = replay.profile_names
    file_bytes = replay.file_bytes
    all_violations = replay.violations

    def _fail(*msgs: str, violations: list[Violation] | None = None) -> SelfHostedInitResult:
        return SelfHostedInitResult(
            ok=False,
            dry_run=cfg.dry_run,
            name=cfg.name or "",
            diagnostics=[*diagnostics, *msgs],
            violations=violations or [],
        )

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
            field_collection_mode=replay.field_collection_mode,
            identity_replacements=replay.identity_replacements,
            leak_scan_result={
                "ok": False,
                "violation_count": len(all_violations),
            },
            source=replay.source,
            summary="self-hosted init failed: identity leak check found violations",
        )
    leak_scan_result: dict = {"ok": True, "violation_count": 0}

    # 10. Load old ownership state; split planned files into owned vs new.
    old_owned_paths: set[str] = set()
    if replay.old_state:
        for entry in _migrate_managed_paths(replay.old_state):
            if isinstance(entry, dict) and "path" in entry:
                old_owned_paths.add(entry["path"])

    owned_planned: list[tuple[str, bytes]] = [
        (rp, file_bytes[rp]) for rp in sorted(file_bytes) if rp in old_owned_paths
    ]
    new_planned_files: list[PlannedFile] = [
        PlannedFile(rel_path=rp, kind=replay.file_kinds.get(rp, "file"), content=file_bytes[rp])
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
        if replay.old_state:
            _removed, skip_warnings = _remove_stale_owned_paths(
                cfg.target, replay.old_state, set(file_bytes.keys())
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
            source_pack_identity=_source_pack_identity(replay.source_meta, cfg),
            source_root_kind="self-hosted-source",
            recipe=SelfHostRecipe(
                packs=pack_names,
                profiles=profile_names,
                guides=cfg.guides,
                attribution=cfg.attribution,
                tooling=cfg.tooling,
                name=replay.recorded_recipe.name,
                display_name=replay.recorded_recipe.display_name,
                description=replay.recorded_recipe.description,
                owner_name=replay.recorded_recipe.owner_name,
                owner_email=replay.recorded_recipe.owner_email,
                preferred_adapter=replay.recorded_recipe.preferred_adapter,
                repository_url=replay.recorded_recipe.repository_url,
            ),
            pin=SelfHostPin(
                source_uri=str(cfg.source.resolve()) if _is_attributed(cfg) else None,
                source_revision=None,
                archive_sha256=None,
                synced_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        try:
            _write_ownership_state(cfg.target, new_state)
        except (OSError, UnsafeContentError):
            return _fail("write failed: ownership state path is unsafe")
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
        field_collection_mode=replay.field_collection_mode,
        identity_replacements=replay.identity_replacements,
        leak_scan_result=leak_scan_result,
        source=replay.source,
        summary=(
            f"self-hosted init {'(dry run) ' if cfg.dry_run else ''}complete: "
            f"{n_written} file(s) written to {cfg.name}"
        ),
    )
