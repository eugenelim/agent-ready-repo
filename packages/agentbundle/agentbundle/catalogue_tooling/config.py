"""catalogue.toml configuration loading and validation.

Implements load_catalogue_config — the entry point Wave 2-4 specs call to
read the repo's catalogue.toml. All validation logic is here; no business
logic belongs in this module.

Validation order:
  1. JSON Schema (structural) via agentbundle.build.validate (Assumption 2)
  2. Business rules — symlink escape, credentials, version comparability, etc.

Python 3.11 stdlib only.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

# Bundled recipe IDs that are always valid without a path on disk.
_BUNDLED_RECIPES: frozenset[str] = frozenset({"default"})

# Safe identifier pattern for catalogue names.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")

# Safe name pattern for Artifactory repository/bundle fields.
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# Simple semver / PEP-440 subset — version must start with a digit.
_VERSION_RE = re.compile(r"^\d+(\.\d+)*([.\-+][A-Za-z0-9._+\-]*)?$")

# Query-param names that signal embedded credentials.
_CREDENTIAL_PARAMS = frozenset({"token", "password", "key", "secret", "api_key", "apikey"})


class CatalogueConfigError(ValueError):
    """Raised when catalogue.toml fails validation."""


@dataclass
class CataloguePaths:
    packs: str
    profiles: str
    contracts: str
    marketplace: str
    build_output: str


@dataclass
class CatalogueBuild:
    recipes: list[str]
    self_host: bool
    claude_plugin_branch: str
    marketplace_description: str


@dataclass
class CataloguePackage:
    include: list[str]
    required: list[str]


@dataclass
class ArtifactoryConfig:
    enabled: bool
    base_url: str | None = None
    repository: str | None = None
    bundle: str | None = None


@dataclass
class AgentbundleDistribution:
    install_defaults_output: str
    preferred_adapter: str
    default_source: str
    artifactory: ArtifactoryConfig


@dataclass
class DistributionConfig:
    agentbundle: AgentbundleDistribution


@dataclass
class CatalogueConfig:
    schema: int
    name: str
    display_name: str
    description: str
    minimum_agentbundle_version: str
    paths: CataloguePaths
    build: CatalogueBuild
    package: CataloguePackage
    distribution: DistributionConfig


def _load_schema() -> dict:
    """Load catalogue.schema.json from the bundled _data directory.

    Raises CatalogueConfigError when the schema cannot be found or is
    invalid JSON — the validator cannot run without it.
    """
    # Primary: importlib.resources (installed package path)
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/catalogue.schema.json")
        if resource.is_file():
            return json.loads(resource.read_text(encoding="utf-8"))
    except Exception:
        pass

    # Fallback: filesystem path relative to this file (editable install)
    here = Path(__file__).resolve()
    data_schema = here.parents[1] / "_data" / "catalogue.schema.json"
    if data_schema.exists():
        try:
            return json.loads(data_schema.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogueConfigError(
                f"catalogue.toml: cannot load catalogue.schema.json: {exc}"
            ) from exc

    raise CatalogueConfigError(
        "catalogue.toml: catalogue.schema.json not found in _data/ — "
        "cannot validate without the schema"
    )


def _apply_schema_validation(raw: dict) -> None:
    """Run JSON Schema validation via the existing build/validate.py subset."""
    from agentbundle.build.validate import validate

    schema = _load_schema()
    errors = validate(raw, schema)
    if errors:
        raise CatalogueConfigError(
            "catalogue.toml: schema validation failed:\n  " + "\n  ".join(errors)
        )


def _load_adapter_names() -> frozenset[str]:
    """Return adapter names from the bundled adapter contract.

    Raises CatalogueConfigError if the contract cannot be loaded — the
    preferred-adapter check cannot pass without the contract (fail-closed).
    """
    # Primary: importlib.resources
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

    # Fallback: filesystem path relative to repo root
    here = Path(__file__).resolve()
    # packages/agentbundle/agentbundle/catalogue_tooling/config.py -> repo root
    repo_root = here.parents[4]
    adapter_toml = repo_root / "docs" / "contracts" / "adapter.toml"
    if adapter_toml.exists():
        try:
            data = tomllib.loads(adapter_toml.read_text(encoding="utf-8"))
            adapters = data.get("adapter", {})
            if isinstance(adapters, dict):
                return frozenset(adapters.keys())
        except Exception as exc:
            raise CatalogueConfigError(
                f"catalogue.toml: cannot load adapter contract for preferred-adapter "
                f"validation: {exc}"
            ) from exc

    raise CatalogueConfigError(
        "catalogue.toml: adapter contract (adapter.toml) not found — "
        "cannot validate preferred-adapter without it"
    )


def _check_no_credentials(value: str, field_name: str) -> None:
    """Raise CatalogueConfigError if *value* looks like a credential-bearing URL."""
    if not isinstance(value, str):
        return
    parsed = urlsplit(value)
    if "@" in parsed.netloc:
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} must not contain credentials (userinfo in URL)"
        )
    if parsed.query:
        params = {p.split("=", 1)[0].lower() for p in parsed.query.split("&") if "=" in p}
        bad = params & _CREDENTIAL_PARAMS
        if bad:
            raise CatalogueConfigError(
                f"catalogue.toml: {field_name!r} must not contain credential query params: "
                f"{sorted(bad)}"
            )


def _validate_path(root: Path, p: str, field_name: str) -> None:
    """Validate that *p* is a relative, non-traversal, non-symlink-escape path."""
    if not isinstance(p, str):
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} must be a string, got {type(p).__name__}"
        )
    # Must not be absolute
    if p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} path must be relative, not absolute: {p!r}"
        )
    # No leading ..
    parts = Path(p).parts
    if ".." in parts:
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} path must not traverse outside root: {p!r}"
        )
    # Resolve and check inside root (catches symlinks)
    resolved_root = root.resolve()
    try:
        resolved_path = (root / p).resolve()
    except OSError:
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} path cannot be resolved: {p!r}"
        )
    if not resolved_path.is_relative_to(resolved_root):
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} path escapes catalogue root "
            f"(symlink or traversal): {p!r}"
        )


def _validate_source(value: str, field_name: str) -> None:
    """Validate a source URL using agentbundle.source_defaults._is_valid_source.

    Raises CatalogueConfigError if the validator cannot be imported (fail-closed).
    """
    try:
        from agentbundle.source_defaults import _is_valid_source  # type: ignore[import]
    except ImportError as exc:
        raise CatalogueConfigError(
            f"catalogue.toml: cannot import source validator for {field_name!r}: {exc}"
        ) from exc

    if not _is_valid_source(value):
        raise CatalogueConfigError(
            f"catalogue.toml: {field_name!r} is not a valid catalogue source: {value!r}"
        )


def load_catalogue_config(root: Path) -> CatalogueConfig | None:
    """Load and validate catalogue.toml at *root*.

    Returns ``None`` when catalogue.toml is absent (backward compat).
    Raises ``CatalogueConfigError`` on any validation failure.
    """
    toml_path = root / "catalogue.toml"
    if not toml_path.exists():
        return None

    try:
        raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise CatalogueConfigError(f"catalogue.toml: TOML parse error: {exc}") from exc

    # --- Step 1: JSON Schema structural validation (Assumption 2) ---
    _apply_schema_validation(raw)

    # --- Step 2: Business rules beyond schema ---

    # Rule 1: schema is integer 1 (redundant with schema enum, belt-and-suspenders)
    schema_val = raw.get("schema")
    if schema_val != 1:
        raise CatalogueConfigError(
            f"catalogue.toml: 'schema' must be integer 1, got {schema_val!r}"
        )

    cat = raw.get("catalogue", {})

    # Rule 2: safe name
    name = cat.get("name", "")
    if not _SAFE_NAME_RE.match(name):
        raise CatalogueConfigError(
            f"catalogue.toml: catalogue.name must match ^[A-Za-z0-9][A-Za-z0-9_\\-]*$, "
            f"got {name!r}"
        )

    display_name = cat.get("display-name")
    if not display_name:
        raise CatalogueConfigError("catalogue.toml: catalogue.display-name is required")

    description = cat.get("description")
    if not description:
        raise CatalogueConfigError("catalogue.toml: catalogue.description is required")

    min_version = cat.get("minimum-agentbundle-version", "")

    # Rule 11: minimum-agentbundle-version is safe-comparable
    if not isinstance(min_version, str) or not _VERSION_RE.match(min_version):
        raise CatalogueConfigError(
            f"catalogue.toml: minimum-agentbundle-version must be a valid version string, "
            f"got {min_version!r}"
        )

    # --- [catalogue.paths] --- Rules 3 & 4
    paths_raw = cat.get("paths", {})
    path_fields = {
        "packs": paths_raw.get("packs", ""),
        "profiles": paths_raw.get("profiles", ""),
        "contracts": paths_raw.get("contracts", ""),
        "marketplace": paths_raw.get("marketplace", ""),
        "build-output": paths_raw.get("build-output", ""),
    }
    for field_key, path_val in path_fields.items():
        _validate_path(root, path_val, f"catalogue.paths.{field_key}")

    paths = CataloguePaths(
        packs=path_fields["packs"],
        profiles=path_fields["profiles"],
        contracts=path_fields["contracts"],
        marketplace=path_fields["marketplace"],
        build_output=path_fields["build-output"],
    )

    # --- [catalogue.build] --- Rule 6
    build_raw = cat.get("build", {})
    recipes = build_raw.get("recipes", [])

    for recipe in recipes:
        if not isinstance(recipe, str):
            raise CatalogueConfigError(
                f"catalogue.toml: recipe entry must be a string, got {type(recipe).__name__}"
            )
        if recipe in _BUNDLED_RECIPES:
            continue
        if not recipe.endswith(".toml"):
            raise CatalogueConfigError(
                f"catalogue.toml: unknown recipe {recipe!r} — not a bundled recipe "
                f"({sorted(_BUNDLED_RECIPES)}) and not a .toml path"
            )
        # Route through _validate_path: catches absolute paths (including Windows
        # drive-absolute), traversal, and symlink escape, matching the same
        # rigor applied to [catalogue.paths] entries.
        _validate_path(root, recipe, f"catalogue.build.recipes ({recipe!r})")

    build = CatalogueBuild(
        recipes=recipes,
        self_host=build_raw.get("self-host", False),
        claude_plugin_branch=build_raw.get("claude-plugin-branch", "main"),
        marketplace_description=build_raw.get("marketplace-description", ""),
    )

    # --- [catalogue.package] --- Rule 5
    pkg_raw = cat.get("package", {})
    include = pkg_raw.get("include", [])
    required = pkg_raw.get("required", [])

    include_set = set(include)
    required_set = set(required)
    not_in_include = required_set - include_set
    if not_in_include:
        raise CatalogueConfigError(
            f"catalogue.toml: package.required entries not in package.include: "
            f"{sorted(not_in_include)}"
        )

    package = CataloguePackage(include=include, required=required)

    # --- [distribution.agentbundle] ---
    dist_raw = raw.get("distribution", {})
    ab_raw = dist_raw.get("agentbundle", {})

    preferred_adapter = ab_raw.get("preferred-adapter", "")
    default_source = ab_raw.get("default-source", "")
    install_defaults_output = ab_raw.get("install-defaults-output", "")

    # Rule 7: preferred-adapter ∈ adapter contract (fail-closed)
    known_adapters = _load_adapter_names()
    if preferred_adapter not in known_adapters:
        raise CatalogueConfigError(
            f"catalogue.toml: distribution.agentbundle.preferred-adapter "
            f"{preferred_adapter!r} is not in the adapter contract. "
            f"Known: {sorted(known_adapters)}"
        )

    # Rules 8 & 10: default-source valid, no credentials
    _check_no_credentials(default_source, "distribution.agentbundle.default-source")
    _validate_source(default_source, "distribution.agentbundle.default-source")

    # --- [distribution.agentbundle.artifactory] --- Rule 9
    art_raw = ab_raw.get("artifactory", {})
    art_enabled = art_raw.get("enabled", False)
    art = ArtifactoryConfig(enabled=bool(art_enabled))

    if art_enabled:
        base_url = art_raw.get("base-url")
        if not base_url:
            raise CatalogueConfigError(
                "catalogue.toml: distribution.agentbundle.artifactory.base-url "
                "is required when enabled = true"
            )
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise CatalogueConfigError(
                "catalogue.toml: distribution.agentbundle.artifactory.base-url "
                "must start with 'https://'"
            )
        parsed_art = urlsplit(base_url)
        if "@" in parsed_art.netloc:
            raise CatalogueConfigError(
                "catalogue.toml: distribution.agentbundle.artifactory.base-url "
                "must not contain userinfo"
            )
        if parsed_art.query:
            raise CatalogueConfigError(
                "catalogue.toml: distribution.agentbundle.artifactory.base-url "
                "must not contain a query string"
            )

        repository = art_raw.get("repository")
        bundle = art_raw.get("bundle")
        for seg_name, seg_val in (("repository", repository), ("bundle", bundle)):
            if not seg_val:
                raise CatalogueConfigError(
                    f"catalogue.toml: distribution.agentbundle.artifactory.{seg_name} "
                    "is required when enabled = true"
                )
            if not isinstance(seg_val, str) or not _SAFE_SEGMENT_RE.match(seg_val):
                raise CatalogueConfigError(
                    f"catalogue.toml: distribution.agentbundle.artifactory.{seg_name} "
                    f"must match [A-Za-z0-9._-]+, got {seg_val!r}"
                )
        art.base_url = base_url
        art.repository = repository
        art.bundle = bundle

    agentbundle_dist = AgentbundleDistribution(
        install_defaults_output=install_defaults_output,
        preferred_adapter=preferred_adapter,
        default_source=default_source,
        artifactory=art,
    )
    distribution = DistributionConfig(agentbundle=agentbundle_dist)

    return CatalogueConfig(
        schema=schema_val,
        name=name,
        display_name=display_name,
        description=description,
        minimum_agentbundle_version=min_version,
        paths=paths,
        build=build,
        package=package,
        distribution=distribution,
    )
