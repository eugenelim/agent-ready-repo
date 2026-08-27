"""Build pipeline: recipe loader, pack discovery, adapter dispatch,
marketplace aggregation.

Recipes live next to this module under `recipes/`. Each recipe carries
a `type` (`per-pack` | `aggregate` | `overlay` | `composite`) that
determines how the pipeline interprets it. The four default recipes are
per-pack-claude-plugin, per-pack-apm-package, per-pack-agent-plugin, and
marketplace; the other three (per-pack-overlay, composite-agents-md,
composite-marketplace)
are consumed by T7's self-host writer.

Pack discovery globs the configured `--packs-dir` for subdirectories
whose `pack.toml` validates. Pack-internal name collisions (two
primitives with the same local name inside a single pack) are rejected
before any adapter runs, with a stderr message naming both source
paths.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.hook_wiring_rules import (
    claude_projection_paths,
)
from agentbundle.build.projections.plugin_hooks import compile_plugin_hooks
from agentbundle.build.scope_rails import check_hooks
from agentbundle.build.validate import validate as validate_instance
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    list_confined_directories,
    list_confined_regular_files,
    read_confined_regular_file,
    validate_confined_directory,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
RECIPES_DIR = PACKAGE_ROOT / "recipes"
REPO_ROOT = PACKAGE_ROOT.parent.parent.parent.parent

# Canonical branch name for the published Claude-plugins distribution.
# All marketplace entries' source.branch must match this value so `claude plugin
# install` fetches from the right branch.
_DIST_BRANCH = "claude-plugins-dist"

# Marketplace description included in both the dist and self-hosted marketplace.json.
# The description field is required for `claude plugin validate --strict` to pass.
_MARKETPLACE_DESCRIPTION = (
    "Agent skills, subagents, and hooks for Claude Code and other coding agents."
)

# Match https://github.com/owner/repo (optional trailing .git and slash).
# HTTPS only: an `http://` link is rejected outright rather than upgraded,
# because `git-subdir` moves the fetch host from the schema into data.
_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$"
)
# Matched separately so an insecure link raises instead of silently falling
# through the "not a GitHub URL" branch, which emits no `source` at all.
_INSECURE_GITHUB_URL_RE = re.compile(
    r"^http://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$"
)
_COMPILED_PLUGIN_HOOK_COMMAND_RE = re.compile(
    r'^(python|python3|sh|bash) "\$\{CLAUDE_PLUGIN_ROOT\}/([^"]+)"$'
)
_AGENT_PLUGIN_SCHEMA_ID = (
    "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
)
_AGENT_PLUGIN_NAME_RE = re.compile(
    r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$"
)
_AGENT_PLUGIN_PACK_TOML_MAX_BYTES = 1024 * 1024
_AGENT_PLUGIN_FILE_MAX_BYTES = 2 * 1024 * 1024
_AGENT_PLUGIN_FILE_COUNT_MAX = 4096
_AGENT_PLUGIN_TOTAL_BYTES_MAX = 32 * 1024 * 1024
_AGENT_PLUGIN_PATH_DEPTH_MAX = 20
_AGENT_PLUGIN_EXTENSION_JSON_MAX_BYTES = 8 * 1024 * 1024
_AGENT_PLUGIN_EXTENSION_DEPTH_MAX = 20
_AGENT_PLUGIN_EXTENSION_MEMBER_MAX = 4096
_AGENT_PLUGIN_EXTENSION_STRING_MAX_BYTES = 64 * 1024
_AGENT_PLUGIN_EXTENSION_ARRAY_MAX = 256
_AGENT_PLUGIN_NAMESPACE_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$"
)
_AGENT_PLUGIN_SCHEMA_PATH_RE = re.compile(
    r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+/"
    r"v?[0-9]+(?:\.[0-9]+)*/[A-Za-z0-9._-]+\.schema\.json$"
)
_AGENT_PLUGIN_PRIMITIVE_PATHS = {
    "skill": ".apm/skills",
    "agent": ".apm/agents",
    "command": ".apm/commands",
    "hook-body": ".apm/hooks",
    "hook-wiring": ".apm/hook-wiring",
    "kiro-ide-hook": ".apm/kiro-ide-hooks",
    "shared-libs": ".apm/shared-libs",
    "adapter-root-bins": ".apm/adapter-root-bins",
    "user-libs": ".apm/user-libs",
}
_AGENT_PLUGIN_SUPPORTED_SCHEMA_KEYWORDS = {
    "type",
    "properties",
    "required",
    "enum",
    "pattern",
    "items",
    "additionalProperties",
    "minItems",
    "maxItems",
    "contains",
    "if",
    "then",
    "else",
}
_AGENT_PLUGIN_SCHEMA_ANNOTATION_KEYWORDS = {
    "$id",
    "$schema",
    "title",
    "description",
    "default",
    "examples",
}


def _bundled_or_repo(name: str) -> Path:
    """Locate a data file shipped under both `agentbundle/_data/` and
    `<repo>/contracts/`.

    Prefer the bundled copy when present on disk (works in a `pip install`
    and a dev checkout); fall back to the repo path for dev checkouts
    whose `_data/` hasn't been synced. Inside a `zipapp` neither path is
    a real filesystem location — callers should use `_read_bundled` to
    get the text content instead of trying to open the returned Path.
    """
    bundled = PACKAGE_ROOT.parent / "_data" / name
    if bundled.exists():
        return bundled
    return REPO_ROOT / "contracts" / name


def _read_bundled(name: str) -> str:
    """Read a packaged data file, transparently handling the zipapp case.

    Resolution order:
      1. `<package>/_data/<name>` via `importlib.resources` — works for
         filesystem installs AND inside a `zipapp` archive.
      2. `<repo>/contracts/<name>` — dev fallback for source trees
         whose `_data/` hasn't been populated.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath(f"_data/{name}")
        if resource.is_file():
            return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return (REPO_ROOT / "contracts" / name).read_text(encoding="utf-8")


CONTRACT_PATH = _bundled_or_repo("adapter.toml")
ROUTE_CONTRACT_PATH = _bundled_or_repo("distribution-routes.toml")
ROUTE_SCHEMA_PATH = _bundled_or_repo("distribution-routes.schema.json")
PACK_SCHEMA_PATH = _bundled_or_repo("pack.schema.json")
PLUGIN_MANIFEST_SCHEMA_PATH = _bundled_or_repo("plugin-manifest.schema.json")
PRIMITIVE_DIRS = ("skills", "agents", "hooks", "hook-wiring", "commands")

# The canonical SessionStart hook command synthesised into each derived
# plugin.json (claude-plugins route). Shell-exec contract:
# when CLAUDE_PLUGIN_ROOT is substituted the double-quoted path survives
# spaces. The trailing `--install-route claude-plugins` flag is required by
# the writer's argparse (apm-install-route-parity); the build
# pipeline and the projected command stay coupled at projection time via
# `make build` so a refreshed writer always ships next to a refreshed
# command — the apm route ships the same writer at a second path.
_SESSION_START_COMMAND = (
    'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'
    ' --install-route claude-plugins'
)

_SESSION_START_HOOK_ENTRY = {
    "hooks": [
        {
            "type": "command",
            "command": _SESSION_START_COMMAND,
            "timeout": 10,
        }
    ]
}

# The canonical APM-route SessionStart hook command synthesised into each
# derived dist/apm/<pack>/.apm/hooks/install-marker.json. APM's HookIntegrator
# rewrites ${PLUGIN_ROOT} to per-target tokens (${CLAUDE_PLUGIN_ROOT},
# ${CURSOR_PLUGIN_ROOT}, …); the writer's data-directory shim resolves the
# hash-file location precedence.
_SESSION_START_COMMAND_APM = (
    'python3 "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"'
    ' --install-route apm'
)

# JSON shape emitted into dist/apm/<pack>/.apm/hooks/install-marker.json.
# Authored as a Python dict so json.dumps controls indentation.
_APM_INSTALL_MARKER_HOOK_JSON = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": _SESSION_START_COMMAND_APM,
                        "timeout": 10,
                    }
                ]
            }
        ]
    }
}


def _read_install_marker_template() -> bytes:
    """Read the canonical install-marker.py template as bytes.

    Resolution order (mirrors _read_bundled pattern):
      1. `<package>/_data/install-marker.py` via importlib.resources — works
         for filesystem installs AND inside a zipapp archive.
      2. `<repo>/packages/agentbundle/templates/install-marker.py` — dev
         fallback for source trees.
    """
    try:
        from importlib.resources import files

        resource = files("agentbundle").joinpath("_data/install-marker.py")
        if resource.is_file():
            return resource.read_bytes()
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return (
        REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"
    ).read_bytes()


def _project_pack_readme(pack_path: Path, per_pack_output: Path) -> None:
    """Copy a pack's ``README.md`` into its per-pack dist route, if present.

    enriched-pack-manifest T5: the README is the sole portable per-pack doc,
    and the manifest's ``readme = "README.md"`` pointer resolves relative to
    the route directory. A pack without a README projects none and does not
    error (the ``readme`` field is then simply absent / unresolved — never a
    build failure). ``follow_symlinks=False`` mirrors the pack.toml copy so a
    symlinked README is not dereferenced into ``dist/`` at build time.
    """
    readme_src = pack_path / "README.md"
    if readme_src.is_file():
        shutil.copy2(
            readme_src, per_pack_output / "README.md", follow_symlinks=False
        )


def validate_derived_plugin_manifest_dict(manifest: dict, label: str = "<derived>") -> None:
    """Validate an in-memory derived plugin manifest dict against the derived schema.

    Call this BEFORE writing to disk so a synthesis bug does not land a
    malformed plugin.json in dist/ (Blocker-3: pre-write validation).
    """
    schema = json.loads(_read_bundled("plugin-manifest.derived.schema.json"))
    errors = validate_instance(manifest, schema)
    if errors:
        raise ValueError(
            f"derived plugin manifest {label} failed schema: "
            + "; ".join(errors)
        )


def validate_derived_plugin_manifest(plugin_json_path: Path) -> None:
    """Validate a derived .claude-plugin/plugin.json (with synthesised hooks)
    against derived schema.

    Defence-in-depth: also available as validate_derived_plugin_manifest_dict
    for pre-write validation before the file is written to disk.
    """
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    validate_derived_plugin_manifest_dict(manifest, label=str(plugin_json_path))


def derive_projectable_subset(pack_toml: dict) -> dict:
    """Map a parsed ``pack.toml`` to the projectable plugin-manifest subset.

    enriched-pack-manifest: ``pack.toml`` is the rich
    metadata source of truth; the build projects a *lossy*, schema-compliant
    subset into the claude-plugins + apm routes (the ``plugin.json`` /
    ``marketplace.json`` entry). Fixed mapping:

      - ``author``      ← first ``[[pack.maintainers]]``, as object
        ``{"name": ..., "email": ...}`` (email omitted when absent).
      - ``source``      ← derived from ``[pack.links].repository`` when it is an
        **https** GitHub URL: ``{"source": "git-subdir",
        "url": "https://github.com/owner/name.git", "path": pack.name,
        "ref": _DIST_BRANCH}``. Claude Code's ``github`` source accepts only
        ``repo``/``ref``/``sha`` and has no subdirectory support, so the former
        ``branch``/``directory`` keys were silently dropped and the installer
        cloned the default branch at repo root — every adopter received an
        empty plugin. An ``http://`` repository link **raises**: silently
        upgrading it to ``https`` would fabricate a URL the author did not
        write, and silently omitting ``source`` would reintroduce the same
        class of quiet failure.
      - ``license``     ← ``[pack].license`` (verbatim).
      - ``homepage``    ← ``[pack.links].homepage`` (verbatim).
      - ``repository``  ← ``[pack.links].repository`` (verbatim).
      - ``keywords``    ← ``[pack].keywords`` (string entries, verbatim).
      - ``category``    ← ``categories[0]``.
      - ``displayName`` ← ``[pack].display_name``.

    **Emit-only-when-present** is the load-bearing invariant: a key appears in
    the output only when its source field is present and non-empty, so a
    legacy ``pack.toml`` declaring none of the enriched fields yields ``{}``
    and the projected manifest is byte-identical to the pre-enrichment output
    (legacy-invariance AC). This is a pure function — no I/O, no schema read.
    """
    pack = pack_toml.get("pack", {})
    if not isinstance(pack, dict):
        return {}
    out: dict = {}

    maintainers = pack.get("maintainers")
    if isinstance(maintainers, list) and maintainers:
        first = maintainers[0]
        if isinstance(first, dict):
            name = first.get("name")
            email = first.get("email")
            if isinstance(name, str) and name:
                author_obj: dict = {"name": name}
                if isinstance(email, str) and email:
                    author_obj["email"] = email
                out["author"] = author_obj

    license_ = pack.get("license")
    if isinstance(license_, str) and license_:
        out["license"] = license_

    links = pack.get("links")
    if isinstance(links, dict):
        homepage = links.get("homepage")
        if isinstance(homepage, str) and homepage:
            out["homepage"] = homepage
        repository = links.get("repository")
        if isinstance(repository, str) and repository:
            out["repository"] = repository
            # Derive source field: tells Claude Code where to fetch the plugin
            # from the canonical distribution branch.
            pack_name = pack.get("name", "")
            if isinstance(pack_name, str) and pack_name:
                if _INSECURE_GITHUB_URL_RE.match(repository):
                    raise ValueError(
                        f"[pack.links].repository must be https, got "
                        f"{repository!r}. Refusing to upgrade it silently: the "
                        f"emitted url is what an adopter's client clones and "
                        f"then executes."
                    )
                m = _GITHUB_URL_RE.match(repository)
                if m:
                    out["source"] = {
                        "source": "git-subdir",
                        "url": f"https://github.com/{m.group(1)}.git",
                        "path": pack_name,
                        "ref": _DIST_BRANCH,
                    }

    keywords = pack.get("keywords")
    if isinstance(keywords, list):
        kws = [k for k in keywords if isinstance(k, str) and k]
        if kws:
            out["keywords"] = kws

    categories = pack.get("categories")
    if isinstance(categories, list) and categories:
        first_cat = categories[0]
        if isinstance(first_cat, str) and first_cat:
            out["category"] = first_cat

    display_name = pack.get("display_name")
    if isinstance(display_name, str) and display_name:
        out["displayName"] = display_name

    return out


# The four default recipes that plain `make build` invokes.
# The self-host recipes (per-pack-overlay, composite-agents-md,
# composite-marketplace) fire only under --self.
DEFAULT_RECIPES = (
    "per-pack-claude-plugin",
    "per-pack-apm-package",
    "per-pack-agent-plugin",
    "marketplace",
)


@dataclass
class Recipe:
    name: str
    type: str
    route: str | None
    adapter: str | None
    output_subdir: str | None
    input_subdir: str | None
    output_file: str | None
    units: list[str]
    fragment_path: str | None
    manifest_path: str | None


@dataclass(frozen=True)
class ResolvedDistributionRoute:
    """Validated semantics consumed by the explicit package projectors."""

    identity: str
    package_projector: str
    adapter_projector: str | None
    admission_policy: str
    output_subdir: str
    component_capabilities: dict[str, dict[str, str]]
    marketplace_projector: str
    lifecycle_trigger: str


@dataclass
class Pack:
    name: str
    path: Path


@dataclass(frozen=True)
class _AgentPluginSourceFile:
    """One preflighted source file ready for a fresh route write."""

    relative_path: Path
    spool_offset: int
    byte_count: int
    executable: bool


@dataclass(frozen=True)
class _PreparedAgentPlugin:
    """Complete preflight result for one admitted pack."""

    pack_name: str
    manifest: dict
    files: tuple[_AgentPluginSourceFile, ...]


def _agent_plugin_display(value: str) -> str:
    """Render untrusted route context as one deterministic ASCII JSON string."""
    return json.dumps(value, ensure_ascii=True)


def _agent_plugin_error(pack_name: str, component: str, error_class: str) -> ValueError:
    """Build a sanitized portable-route refusal without source values or paths."""
    return ValueError(
        "agent-plugin: pack "
        f"{_agent_plugin_display(pack_name)} component {component} "
        f"error {error_class}"
    )


def _is_reparse_point(inspected: os.stat_result) -> bool:
    """Return whether a no-follow stat identifies a Windows reparse point."""
    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(inspected, "st_file_attributes", 0) & attribute)


def _validate_agent_plugin_pack_root(pack: Pack) -> None:
    """Reject a link-like pack root before inspecting any route input."""
    try:
        validate_confined_directory(pack.path.parent, pack.path)
    except UnsafeContentError as exc:
        raise _agent_plugin_error(pack.name, "pack-root", "unsafe-source") from exc


def _agent_plugin_excluding_primitives(pack: Pack) -> list[str]:
    """Return sorted dropped primitives whose canonical source is non-empty."""
    excluded: list[str] = []
    for primitive, relative in _AGENT_PLUGIN_PRIMITIVE_PATHS.items():
        if primitive == "skill":
            continue
        source = pack.path / relative
        try:
            before = source.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise _agent_plugin_error(
                pack.name, primitive, "source-inspection-failed"
            ) from exc
        if (
            not stat.S_ISDIR(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or _is_reparse_point(before)
        ):
            raise _agent_plugin_error(pack.name, primitive, "unsafe-source")
        try:
            validate_confined_directory(pack.path, source)
            with os.scandir(source) as iterator:
                present = next(iterator, None) is not None
            after = source.lstat()
        except (UnsafeContentError, OSError, RuntimeError) as exc:
            raise _agent_plugin_error(pack.name, primitive, "unsafe-source") from exc
        if (
            (before.st_dev, before.st_ino, before.st_mode)
            != (after.st_dev, after.st_ino, after.st_mode)
            or not stat.S_ISDIR(after.st_mode)
            or stat.S_ISLNK(after.st_mode)
            or _is_reparse_point(after)
        ):
            raise _agent_plugin_error(pack.name, primitive, "unsafe-source")
        if present:
            excluded.append(primitive)
    return sorted(excluded)


def _read_agent_plugin_pack_metadata(pack: Pack) -> dict:
    """Read canonical pack metadata through the confined single-link seam."""
    try:
        contents = read_confined_regular_file(
            pack.path,
            pack.path / "pack.toml",
            max_bytes=_AGENT_PLUGIN_PACK_TOML_MAX_BYTES,
        )
        return tomllib.loads(contents.decode("utf-8"))
    except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise _agent_plugin_error(pack.name, "pack.toml", "unsafe-metadata") from exc


def _validate_agent_plugin_extension_registry(registry: dict) -> None:
    """Validate allocation identity, ownership, lifecycle, and schema paths."""
    if registry.get("contract") != {"version": "1.0"}:
        raise ValueError("agent-plugin: extension-registry error invalid-contract")
    namespaces = registry.get("namespace")
    if not isinstance(namespaces, dict):
        raise ValueError("agent-plugin: extension-registry error invalid-contract")
    seen_names: set[str] = set()
    seen_owners: set[str] = set()
    for namespace, allocation in namespaces.items():
        if (
            not isinstance(namespace, str)
            or not _AGENT_PLUGIN_NAMESPACE_RE.fullmatch(namespace)
            or namespace.casefold() in seen_names
        ):
            raise ValueError("agent-plugin: extension-registry error invalid-namespace")
        seen_names.add(namespace.casefold())
        if not isinstance(allocation, dict):
            raise ValueError("agent-plugin: extension-registry error invalid-allocation")
        owner = allocation.get("owner")
        state = allocation.get("state")
        schema_path = allocation.get("schema")
        if not isinstance(owner, str) or not owner or owner in seen_owners:
            raise ValueError("agent-plugin: extension-registry error invalid-owner")
        seen_owners.add(owner)
        if state not in {"reserved", "active"}:
            raise ValueError("agent-plugin: extension-registry error invalid-state")
        if state == "active":
            if not isinstance(schema_path, str) or not _AGENT_PLUGIN_SCHEMA_PATH_RE.fullmatch(
                schema_path
            ):
                raise ValueError("agent-plugin: extension-registry error invalid-schema")
        elif schema_path is not None:
            raise ValueError("agent-plugin: extension-registry error invalid-schema")


def _validate_agent_plugin_extension_schema(schema: object) -> None:
    """Reject extension schemas whose constraints this runtime would ignore."""

    def walk(candidate: object) -> None:
        if not isinstance(candidate, dict):
            raise ValueError("agent-plugin: extension-registry error invalid-schema")
        unsupported = set(candidate) - (
            _AGENT_PLUGIN_SUPPORTED_SCHEMA_KEYWORDS
            | _AGENT_PLUGIN_SCHEMA_ANNOTATION_KEYWORDS
        )
        if unsupported:
            raise ValueError("agent-plugin: extension-registry error invalid-schema")

        expected_type = candidate.get("type")
        if expected_type is not None and expected_type not in {
            "object",
            "array",
            "string",
            "integer",
            "boolean",
        }:
            raise ValueError("agent-plugin: extension-registry error invalid-schema")

        required = candidate.get("required")
        if required is not None and (
            not isinstance(required, list)
            or not all(isinstance(name, str) for name in required)
            or len(required) != len(set(required))
        ):
            raise ValueError("agent-plugin: extension-registry error invalid-schema")

        enum = candidate.get("enum")
        if enum is not None and not isinstance(enum, list):
            raise ValueError("agent-plugin: extension-registry error invalid-schema")

        pattern = candidate.get("pattern")
        if pattern is not None:
            if not isinstance(pattern, str):
                raise ValueError(
                    "agent-plugin: extension-registry error invalid-schema"
                )
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    "agent-plugin: extension-registry error invalid-schema"
                ) from exc

        for keyword in ("minItems", "maxItems"):
            bound = candidate.get(keyword)
            if bound is not None and (
                isinstance(bound, bool)
                or not isinstance(bound, int)
                or bound < 0
            ):
                raise ValueError(
                    "agent-plugin: extension-registry error invalid-schema"
                )
        minimum_items = candidate.get("minItems")
        maximum_items = candidate.get("maxItems")
        if (
            isinstance(minimum_items, int)
            and isinstance(maximum_items, int)
            and minimum_items > maximum_items
        ):
            raise ValueError("agent-plugin: extension-registry error invalid-schema")

        properties = candidate.get("properties")
        if properties is not None:
            if not isinstance(properties, dict):
                raise ValueError(
                    "agent-plugin: extension-registry error invalid-schema"
                )
            for child in properties.values():
                walk(child)

        if "additionalProperties" in candidate:
            additional = candidate["additionalProperties"]
            if not isinstance(additional, bool):
                walk(additional)

        for keyword in ("items", "contains", "if", "then", "else"):
            if keyword in candidate:
                walk(candidate[keyword])

    walk(schema)


def _load_agent_plugin_extension_registry() -> dict:
    """Load the bundled, closed extension allocation contract."""
    registry = tomllib.loads(_read_bundled("agent-plugin-extension-namespaces.toml"))
    schema = json.loads(
        _read_bundled("agent-plugin-extension-namespaces.schema.json")
    )
    if validate_instance(registry, schema):
        raise ValueError("agent-plugin: extension-registry error invalid-contract")
    _validate_agent_plugin_extension_registry(registry)
    for allocation in registry["namespace"].values():
        if allocation["state"] != "active":
            continue
        _load_agent_plugin_extension_schema(allocation["schema"])
    return registry


def _load_agent_plugin_extension_schema(schema_path: str) -> dict:
    """Load one active schema with stable, path-free refusal diagnostics."""
    try:
        schema = json.loads(_read_bundled(schema_path))
    except (OSError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "agent-plugin: extension-registry error invalid-schema"
        ) from exc
    _validate_agent_plugin_extension_schema(schema)
    return schema


def _agent_plugin_extension_values(pack_toml: dict, *, pack_name: str) -> dict:
    """Return validated manifest extension values from the sole metadata path."""
    pack = pack_toml.get("pack", {})
    metadata = pack.get("metadata", {}) if isinstance(pack, dict) else {}
    route_metadata = (
        metadata.get("agent-plugin", {}) if isinstance(metadata, dict) else {}
    )
    extensions = (
        route_metadata.get("extensions", {})
        if isinstance(route_metadata, dict)
        else {}
    )
    if extensions is None:
        return {}
    if not isinstance(extensions, dict):
        raise _agent_plugin_error(pack_name, "extension", "invalid-metadata")
    casefolded = [str(name).casefold() for name in extensions]
    if len(casefolded) != len(set(casefolded)):
        raise _agent_plugin_error(pack_name, "extension", "case-collision")
    return extensions


def _check_agent_plugin_extension_limits(value: object, *, pack_name: str) -> None:
    """Bound strict JSON extension data before namespace-schema validation."""
    members = 0

    def walk(item: object, depth: int) -> None:
        nonlocal members
        if depth > _AGENT_PLUGIN_EXTENSION_DEPTH_MAX:
            raise _agent_plugin_error(pack_name, "extension", "manifest-limit")
        if isinstance(item, dict):
            members += len(item)
            if members > _AGENT_PLUGIN_EXTENSION_MEMBER_MAX:
                raise _agent_plugin_error(pack_name, "extension", "manifest-limit")
            for key, child in item.items():
                if (
                    not isinstance(key, str)
                    or len(key.encode("utf-8"))
                    > _AGENT_PLUGIN_EXTENSION_STRING_MAX_BYTES
                ):
                    raise _agent_plugin_error(pack_name, "extension", "manifest-limit")
                walk(child, depth + 1)
        elif isinstance(item, list):
            if len(item) > _AGENT_PLUGIN_EXTENSION_ARRAY_MAX:
                raise _agent_plugin_error(pack_name, "extension", "manifest-limit")
            for child in item:
                walk(child, depth + 1)
        elif isinstance(item, str):
            if len(item.encode("utf-8")) > _AGENT_PLUGIN_EXTENSION_STRING_MAX_BYTES:
                raise _agent_plugin_error(pack_name, "extension", "manifest-limit")
        elif item is not None and not isinstance(item, (bool, int, float)):
            raise _agent_plugin_error(pack_name, "extension", "strict-json")

    walk(value, 1)
    try:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except RecursionError as exc:
        raise _agent_plugin_error(pack_name, "extension", "manifest-limit") from exc
    except (TypeError, ValueError) as exc:
        raise _agent_plugin_error(pack_name, "extension", "strict-json") from exc
    if len(serialized) > _AGENT_PLUGIN_EXTENSION_JSON_MAX_BYTES:
        raise _agent_plugin_error(pack_name, "extension", "manifest-limit")


def _validated_agent_plugin_extensions(pack_toml: dict, *, pack_name: str) -> dict:
    """Validate declared extension objects against active allocations."""
    registry = _load_agent_plugin_extension_registry()
    values = _agent_plugin_extension_values(pack_toml, pack_name=pack_name)
    _check_agent_plugin_extension_limits(values, pack_name=pack_name)
    allocations = registry["namespace"]
    for namespace, value in values.items():
        if not isinstance(namespace, str) or not _AGENT_PLUGIN_NAMESPACE_RE.fullmatch(
            namespace
        ):
            raise _agent_plugin_error(pack_name, "extension", "invalid-namespace")
        allocation = allocations.get(namespace)
        if allocation is None:
            raise _agent_plugin_error(pack_name, "extension", "unallocated")
        if allocation["state"] != "active":
            raise _agent_plugin_error(pack_name, "extension", "inactive")
        if not isinstance(value, dict):
            raise _agent_plugin_error(pack_name, "extension", "invalid-metadata")
        schema = _load_agent_plugin_extension_schema(allocation["schema"])
        if validate_instance(value, schema):
            raise _agent_plugin_error(pack_name, "extension", "schema-invalid")
    return values


def derive_agent_plugin_manifest(pack_toml: dict, *, pack_name: str) -> dict:
    """Derive the privacy-minimal Agent Plugins 1.0.0 root manifest."""
    if not _AGENT_PLUGIN_NAME_RE.fullmatch(pack_name):
        raise _agent_plugin_error(pack_name, "pack-name", "invalid-identity")
    pack = pack_toml.get("pack")
    if not isinstance(pack, dict):
        raise _agent_plugin_error(pack_name, "pack.toml", "invalid-metadata")
    declared_name = pack.get("name")
    if declared_name != pack_name:
        raise _agent_plugin_error(pack_name, "pack-name", "identity-mismatch")

    extensions = _validated_agent_plugin_extensions(pack_toml, pack_name=pack_name)
    try:
        json.dumps(pack_toml, allow_nan=False)
    except (RecursionError, TypeError, ValueError) as exc:
        raise _agent_plugin_error(pack_name, "manifest", "strict-json") from exc

    manifest: dict = {"$schema": _AGENT_PLUGIN_SCHEMA_ID, "name": pack_name}
    for field in ("version", "description", "license"):
        value = pack.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise _agent_plugin_error(pack_name, field, "invalid-metadata")
            if value:
                manifest[field] = value

    maintainers = pack.get("maintainers")
    if isinstance(maintainers, list) and maintainers:
        first = maintainers[0]
        if isinstance(first, dict):
            name = first.get("name")
            if isinstance(name, str) and name:
                manifest["author"] = {"name": name}

    links = pack.get("links")
    if isinstance(links, dict):
        for field in ("homepage", "repository"):
            value = links.get(field)
            if isinstance(value, str) and value:
                manifest[field] = value

    keywords = pack.get("keywords")
    if isinstance(keywords, list) and keywords:
        if not all(isinstance(item, str) for item in keywords):
            raise _agent_plugin_error(pack_name, "keywords", "invalid-metadata")
        manifest["keywords"] = keywords

    if extensions:
        manifest["extensions"] = extensions

    schema = json.loads(
        _read_bundled("vendor/agent-plugins/1.0.0/plugin.schema.json")
    )
    errors = validate_instance(manifest, schema)
    if errors:
        raise _agent_plugin_error(pack_name, "manifest", "schema-invalid")
    try:
        json.dumps(manifest, allow_nan=False, ensure_ascii=False)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defence in depth
        raise _agent_plugin_error(pack_name, "manifest", "strict-json") from exc
    return manifest


def _collect_agent_plugin_source_files(
    pack: Pack,
    source_root: Path,
    destination_prefix: Path,
    component: str,
    prepared: list[_AgentPluginSourceFile],
    total_bytes: int,
    spool: BinaryIO,
) -> int:
    """Collect one confined input tree into a combined preflight inventory."""
    try:
        source_root.lstat()
        sources = list_confined_regular_files(
            pack.path,
            source_root,
            max_files=_AGENT_PLUGIN_FILE_COUNT_MAX - len(prepared),
            max_depth=_AGENT_PLUGIN_PATH_DEPTH_MAX,
        )
        for source in sorted(
            sources,
            key=lambda path: path.relative_to(source_root).as_posix(),
        ):
            relative = source.relative_to(source_root)
            destination = destination_prefix / relative
            if len(relative.parts) > _AGENT_PLUGIN_PATH_DEPTH_MAX:
                raise _agent_plugin_error(pack.name, component, "source-limit")
            contents, source_mode = read_confined_regular_file(
                pack.path,
                source,
                max_bytes=_AGENT_PLUGIN_FILE_MAX_BYTES,
                include_mode=True,
            )
            total_bytes += len(contents)
            if (
                len(prepared) + 1 > _AGENT_PLUGIN_FILE_COUNT_MAX
                or total_bytes > _AGENT_PLUGIN_TOTAL_BYTES_MAX
            ):
                raise _agent_plugin_error(pack.name, component, "source-limit")
            spool_offset = spool.tell()
            spool.write(contents)
            prepared.append(
                _AgentPluginSourceFile(
                    relative_path=destination,
                    spool_offset=spool_offset,
                    byte_count=len(contents),
                    executable=bool(source_mode & 0o111),
                )
            )
    except FileNotFoundError:
        return total_bytes
    except ValueError as exc:
        if str(exc).startswith("agent-plugin:"):
            raise
        error_class = "source-limit" if "limit" in str(exc) else "unsafe-source"
        raise _agent_plugin_error(pack.name, component, error_class) from exc
    except (OSError, RuntimeError) as exc:
        raise _agent_plugin_error(pack.name, component, "unsafe-source") from exc
    return total_bytes


def _validate_agent_plugin_skill_root(pack: Pack) -> bool:
    """Validate the canonical skill ancestors without enumerating content."""
    apm_root = pack.path / ".apm"
    skills_root = pack.path / _AGENT_PLUGIN_PRIMITIVE_PATHS["skill"]
    try:
        apm_root.lstat()
        validate_confined_directory(pack.path, apm_root)
        skills_root.lstat()
        validate_confined_directory(pack.path, skills_root)
        return True
    except FileNotFoundError:
        return False
    except (UnsafeContentError, OSError, RuntimeError) as exc:
        raise _agent_plugin_error(pack.name, "skill", "unsafe-source") from exc


def _agent_plugin_skill_directories(pack: Pack) -> list[Path]:
    """Return the immediate, real canonical skill directories for one pack."""
    skills_root = pack.path / _AGENT_PLUGIN_PRIMITIVE_PATHS["skill"]
    if not _validate_agent_plugin_skill_root(pack):
        return []
    try:
        directories = list_confined_directories(pack.path, skills_root)
        with os.scandir(skills_root) as iterator:
            entry_names = {entry.name for entry in iterator}
        if entry_names != {directory.name for directory in directories}:
            raise _agent_plugin_error(pack.name, "skill", "unsafe-source")
        return sorted(directories, key=lambda directory: directory.name)
    except ValueError as exc:
        if str(exc).startswith("agent-plugin:"):
            raise
        raise _agent_plugin_error(pack.name, "skill", "unsafe-source") from exc
    except (OSError, RuntimeError) as exc:
        raise _agent_plugin_error(pack.name, "skill", "unsafe-source") from exc


def _agent_plugin_extension_directories(
    pack: Pack, manifest: dict
) -> dict[str, Path]:
    """Admit only declared active reverse-domain pack-root directories."""
    declared = manifest.get("extensions", {})
    declared_by_case = {namespace.casefold(): namespace for namespace in declared}
    allocations = _load_agent_plugin_extension_registry()["namespace"]
    candidates: dict[str, tuple[str, Path]] = {}
    try:
        with os.scandir(pack.path) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
        for entry in entries:
            folded = entry.name.casefold()
            if not _AGENT_PLUGIN_NAMESPACE_RE.fullmatch(folded):
                continue
            inspected = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
                raise _agent_plugin_error(pack.name, "extension", "unsafe-source")
            if not stat.S_ISDIR(inspected.st_mode):
                declared_name = declared_by_case.get(folded)
                allocation = allocations.get(entry.name)
                if declared_name is not None and entry.name != declared_name:
                    raise _agent_plugin_error(
                        pack.name, "extension", "case-collision"
                    )
                if declared_name is not None:
                    raise _agent_plugin_error(
                        pack.name, "extension", "unsafe-source"
                    )
                if allocation is not None:
                    error_class = (
                        "inactive"
                        if allocation["state"] != "active"
                        else "undeclared"
                    )
                    raise _agent_plugin_error(pack.name, "extension", error_class)
                continue
            if folded in candidates:
                raise _agent_plugin_error(pack.name, "extension", "case-collision")
            candidates[folded] = (entry.name, Path(entry.path))
    except ValueError as exc:
        if str(exc).startswith("agent-plugin:"):
            raise
        raise _agent_plugin_error(pack.name, "extension", "unsafe-source") from exc
    except (OSError, RuntimeError) as exc:
        raise _agent_plugin_error(pack.name, "extension", "unsafe-source") from exc

    admitted: dict[str, Path] = {}
    for folded, (name, path) in sorted(candidates.items()):
        declared_name = declared_by_case.get(folded)
        if declared_name is not None and name != declared_name:
            raise _agent_plugin_error(pack.name, "extension", "case-collision")
        if name not in declared:
            allocation = allocations.get(name)
            error_class = (
                "inactive"
                if allocation is not None and allocation["state"] != "active"
                else "undeclared"
            )
            raise _agent_plugin_error(pack.name, "extension", error_class)
        if name in {"mcp.json", "plugin.json"}:
            raise _agent_plugin_error(pack.name, "extension", "destination-collision")
        try:
            validate_confined_directory(pack.path, path)
        except UnsafeContentError as exc:
            raise _agent_plugin_error(pack.name, "extension", "unsafe-source") from exc
        admitted[name] = path
    return admitted


def _prepare_agent_plugin(pack: Pack, spool: BinaryIO) -> _PreparedAgentPlugin:
    """Preflight skill and declared extension inputs before output mutation."""
    _validate_agent_plugin_pack_root(pack)
    metadata = _read_agent_plugin_pack_metadata(pack)
    manifest = derive_agent_plugin_manifest(metadata, pack_name=pack.name)
    prepared: list[_AgentPluginSourceFile] = []
    total_bytes = 0
    for skill_directory in _agent_plugin_skill_directories(pack):
        total_bytes = _collect_agent_plugin_source_files(
            pack,
            skill_directory,
            Path("skills") / skill_directory.name,
            "skill",
            prepared,
            total_bytes,
            spool,
        )
    extension_directories = _agent_plugin_extension_directories(pack, manifest)
    for namespace, extension_directory in sorted(extension_directories.items()):
        total_bytes = _collect_agent_plugin_source_files(
            pack,
            extension_directory,
            Path(namespace),
            "extension",
            prepared,
            total_bytes,
            spool,
        )
    return _PreparedAgentPlugin(pack.name, manifest, tuple(prepared))


def _audit_agent_plugin_output(route_root: Path) -> None:
    """Reject link-like, hard-linked, or non-regular completed output."""
    try:
        _validate_agent_plugin_output_root(route_root)
        for path in list_confined_regular_files(route_root, route_root):
            read_confined_regular_file(route_root, path)
    except (UnsafeContentError, OSError, RuntimeError) as exc:
        raise ValueError("agent-plugin: output error unsafe-output") from exc


def _validate_agent_plugin_output_root(route_root: Path) -> None:
    """Refuse a link-like or non-directory portable route root."""
    try:
        inspected = route_root.lstat()
    except OSError as exc:
        raise ValueError("agent-plugin: output error unsafe-output") from exc
    if (
        not stat.S_ISDIR(inspected.st_mode)
        or stat.S_ISLNK(inspected.st_mode)
        or _is_reparse_point(inspected)
    ):
        raise ValueError("agent-plugin: output error unsafe-output")


def _run_per_pack_agent_plugin(
    recipe: Recipe,
    packs: list[Pack],
    output_dir: Path,
    resolved_route: ResolvedDistributionRoute,
) -> dict:
    """Build the portable route from a bounded, disk-backed source snapshot."""
    prepared: list[_PreparedAgentPlugin] = []
    excluded: dict[str, list[str]] = {}
    route_root = output_dir / resolved_route.output_subdir
    try:
        route_root.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ValueError("agent-plugin: output error unsafe-output") from exc
    else:
        _validate_agent_plugin_output_root(route_root)
    _assert_under(route_root, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # TemporaryFile is unlinked immediately on POSIX and requires no directory
    # cleanup.  The route retains a validated byte snapshot without retaining
    # every eligible pack's source bytes in memory.
    with tempfile.TemporaryFile(mode="w+b", dir=output_dir) as spool:
        for pack in packs:
            _validate_agent_plugin_pack_root(pack)
            primitives = _agent_plugin_excluding_primitives(pack)
            if primitives:
                excluded[pack.name] = primitives
                continue
            prepared.append(_prepare_agent_plugin(pack, spool))

        for pack_name, primitives in sorted(excluded.items()):
            print(
                "agent-plugin: pack "
                f"{_agent_plugin_display(pack_name)} excluded by dropped primitives "
                + json.dumps(primitives, ensure_ascii=True, separators=(",", ":")),
                file=sys.stderr,
            )

        try:
            route_root.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise ValueError("agent-plugin: output error unsafe-output") from exc
        else:
            _validate_agent_plugin_output_root(route_root)
            shutil.rmtree(route_root)
        try:
            route_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError("agent-plugin: output error unsafe-output") from exc

        produced: dict[str, str] = {}
        schema = json.loads(
            _read_bundled("vendor/agent-plugins/1.0.0/plugin.schema.json")
        )
        for item in prepared:
            pack_root = route_root / item.pack_name
            _assert_under(pack_root, route_root)
            pack_root.mkdir()
            manifest_path = pack_root / "plugin.json"
            manifest_path.write_text(
                json.dumps(
                    item.manifest,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            manifest_path.chmod(0o644)
            written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if validate_instance(written_manifest, schema):
                raise _agent_plugin_error(
                    item.pack_name, "manifest", "schema-invalid"
                )
            for source in item.files:
                target = pack_root / source.relative_path
                _assert_under(target, pack_root)
                target.parent.mkdir(parents=True, exist_ok=True)
                spool.seek(source.spool_offset)
                contents = spool.read(source.byte_count)
                if len(contents) != source.byte_count:
                    raise ValueError("agent-plugin: output error unsafe-output")
                target.write_bytes(contents)
                target.chmod(0o755 if source.executable else 0o644)
            produced[item.pack_name] = str(pack_root)

        _audit_agent_plugin_output(route_root)
    return {
        "recipe": recipe.name,
        "type": recipe.type,
        "produced": produced,
        "excluded": excluded,
    }


def load_recipe(name: str, recipes_dir: Path = RECIPES_DIR) -> Recipe:
    """Load a recipe by name.

    Tries the filesystem first (dev/install case), then falls back to
    `importlib.resources` (zipapp case where the package contents live
    inside a `.pyz` archive that `Path.exists()` cannot traverse).
    """
    recipe_path = recipes_dir / f"{name}.toml"
    if recipe_path.exists():
        return _parse_recipe_text(recipe_path.read_text(encoding="utf-8"))
    # Zipapp fallback: read via importlib.resources.
    try:
        from importlib.resources import files

        resource = files("agentbundle.build").joinpath(f"recipes/{name}.toml")
        if resource.is_file():
            return _parse_recipe_text(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    raise FileNotFoundError(f"recipe {name!r} not found at {recipe_path}")


def load_recipe_from_path(path: Path) -> Recipe:
    return _parse_recipe(path)


def _parse_recipe(path: Path) -> Recipe:
    return _parse_recipe_text(path.read_text(encoding="utf-8"))


def _parse_recipe_text(toml_text: str) -> Recipe:
    data = tomllib.loads(toml_text)
    body = data["recipe"]
    recipe_name = body.get("name", "<unnamed>")
    recipe_type = body["type"]
    route = body.get("route")
    if recipe_type in {"per-pack", "aggregate"} and not isinstance(route, str):
        raise ValueError(
            f"recipe {recipe_name!r}: field 'route' is required for "
            f"{recipe_type} distribution recipes"
        )
    if recipe_type not in {"per-pack", "aggregate"} and route is not None:
        raise ValueError(
            f"recipe {recipe_name!r}: field 'route' is not allowed for "
            f"{recipe_type} recipes"
        )
    return Recipe(
        name=body["name"],
        type=recipe_type,
        adapter=body.get("adapter"),
        output_subdir=body.get("output-subdir"),
        input_subdir=body.get("input-subdir"),
        output_file=body.get("output-file"),
        units=body.get("units", []),
        fragment_path=body.get("fragment-path"),
        manifest_path=body.get("manifest-path"),
        route=route,
    )


def _resolve_distribution_route(
    recipe: Recipe, route_contract: dict
) -> ResolvedDistributionRoute:
    """Resolve one explicit route, rejecting inconsistent declarations."""
    route_name = recipe.route
    if route_name not in {"apm", "claude-plugins", "agent-plugin"}:
        raise ValueError(
            f"recipe {recipe.name!r}: field 'route' names unknown "
            f"distribution route {route_name!r}"
        )
    routes = route_contract.get("route")
    if not isinstance(routes, dict) or not isinstance(routes.get(route_name), dict):
        raise ValueError(
            f"recipe {recipe.name!r}: field 'route' names missing "
            f"distribution route {route_name!r}"
        )
    raw_route = routes[route_name]

    # Give the security-sensitive admission mismatch a concise route-local
    # refusal before the exact schema reports the wider declaration diff.
    expected_admission = {
        "apm": "all-packs",
        "claude-plugins": "user-publishable-with-consent",
        "agent-plugin": "skills-only",
    }[route_name]
    manifest = raw_route.get("manifest-projector")
    if not isinstance(manifest, dict):
        raise ValueError(
            f"recipe {recipe.name!r}: route {route_name!r} field "
            "'manifest-projector' must be an object"
        )
    if manifest.get("admission-policy") != expected_admission:
        raise ValueError(
            f"recipe {recipe.name!r}: route {route_name!r} field "
            f"'manifest-projector.admission-policy' must be {expected_admission!r}"
        )
    expected_adapter = {
        "apm": None,
        "claude-plugins": "claude-code",
        "agent-plugin": None,
    }[route_name]
    if recipe.type == "per-pack" and recipe.adapter != expected_adapter:
        raise ValueError(
            f"recipe {recipe.name!r}: field 'adapter' value {recipe.adapter!r} "
            f"does not match route {route_name!r} adapter-projector "
            f"{expected_adapter!r}"
        )
    marketplace_projector = raw_route.get("marketplace-projector")
    if recipe.type == "aggregate":
        if marketplace_projector == "none":
            raise ValueError(
                f"recipe {recipe.name!r}: field 'route' selects {route_name!r}, "
                "whose 'marketplace-projector' is 'none'"
            )
        if recipe.adapter is not None and recipe.adapter != expected_adapter:
            raise ValueError(
                f"recipe {recipe.name!r}: field 'adapter' value "
                f"{recipe.adapter!r} does not match route {route_name!r} "
                f"adapter-projector {expected_adapter!r}"
            )

    schema = json.loads(_read_bundled("distribution-routes.schema.json"))
    errors = validate_instance(route_contract, schema)
    if errors:
        raise ValueError(
            f"recipe {recipe.name!r}: distribution route contract is invalid: "
            + "; ".join(errors)
        )

    layout = raw_route["package-layout"]
    output_subdir = layout["output-subdir"]
    output_path = Path(output_subdir)
    if output_path.is_absolute() or ".." in output_path.parts:
        raise ValueError(
            f"recipe {recipe.name!r}: route {route_name!r} field "
            f"'package-layout.output-subdir' is unsafe: {output_subdir!r}"
        )
    if recipe.type == "per-pack" and recipe.output_subdir != output_subdir:
        raise ValueError(
            f"recipe {recipe.name!r}: field 'output-subdir' value "
            f"{recipe.output_subdir!r} does not match route {route_name!r} "
            f"layout {output_subdir!r}"
        )
    if recipe.type == "aggregate":
        expected_output_file = f"{output_subdir}/marketplace.json"
        if recipe.input_subdir != output_subdir:
            raise ValueError(
                f"recipe {recipe.name!r}: field 'input-subdir' value "
                f"{recipe.input_subdir!r} does not match route {route_name!r} "
                f"layout {output_subdir!r}"
            )
        if recipe.output_file != expected_output_file:
            raise ValueError(
                f"recipe {recipe.name!r}: field 'output-file' value "
                f"{recipe.output_file!r} does not match route {route_name!r} "
                f"output {expected_output_file!r}"
            )

    adapter_projector = manifest["adapter-projector"]
    return ResolvedDistributionRoute(
        identity=raw_route["identity"],
        package_projector=manifest["name"],
        adapter_projector=(
            None if adapter_projector == "none" else adapter_projector
        ),
        admission_policy=manifest["admission-policy"],
        output_subdir=output_subdir,
        component_capabilities=raw_route["component-capabilities"],
        marketplace_projector=marketplace_projector,
        lifecycle_trigger=raw_route["lifecycle-trigger"],
    )


def _load_distribution_route_contract() -> dict:
    """Decode and validate the bundled distribution-route contract."""
    route_contract = tomllib.loads(_read_bundled("distribution-routes.toml"))
    schema = json.loads(_read_bundled("distribution-routes.schema.json"))
    errors = validate_instance(route_contract, schema)
    if errors:
        raise ValueError(
            "distribution route contract is invalid: " + "; ".join(errors)
        )
    return route_contract


def discover_packs(
    packs_dir: Path, *, diagnostic_route: str | None = None
) -> list[Pack]:
    """Discover validated packs with optional route-sanitized refusals."""
    if not packs_dir.exists():
        return []
    if diagnostic_route != "agent-plugin":
        # Preserve the established APM/Claude/render/install discovery
        # behavior.  The stricter no-follow metadata boundary belongs only to
        # the new agent-plugin route and its default-build admission pass.
        generic_packs: list[Pack] = []
        for entry in sorted(packs_dir.iterdir()):
            if entry.name.startswith("_"):
                continue
            if entry.is_dir() and (entry / "pack.toml").exists():
                validate_pack_metadata(entry / "pack.toml")
                generic_packs.append(Pack(name=entry.name, path=entry))
        return generic_packs

    packs: list[Pack] = []
    try:
        with os.scandir(packs_dir) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
    except OSError as exc:
        raise ValueError("pack discovery: unsafe-packs-root") from exc
    for candidate in entries:
        if candidate.name.startswith("_"):
            continue  # reserved authoring asset — not catalogue payload
        try:
            inspected = candidate.stat(follow_symlinks=False)
        except OSError as exc:
            if diagnostic_route == "agent-plugin":
                raise _agent_plugin_error(
                    candidate.name, "pack-root", "unsafe-source"
                ) from exc
            raise ValueError("pack discovery: unsafe-pack-root") from exc
        if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
            if diagnostic_route == "agent-plugin":
                raise _agent_plugin_error(
                    candidate.name, "pack-root", "unsafe-source"
                )
            raise ValueError("pack discovery: unsafe-pack-root")
        if not stat.S_ISDIR(inspected.st_mode):
            continue
        entry = Path(candidate.path)
        try:
            validate_confined_directory(packs_dir, entry)
        except UnsafeContentError as exc:
            if diagnostic_route == "agent-plugin":
                raise _agent_plugin_error(
                    candidate.name, "pack-root", "unsafe-source"
                ) from exc
            raise ValueError("pack discovery: unsafe-pack-root") from exc
        pack_toml = entry / "pack.toml"
        try:
            pack_toml.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            if diagnostic_route == "agent-plugin":
                raise _agent_plugin_error(
                    candidate.name, "pack.toml", "unsafe-metadata"
                ) from exc
            raise ValueError("pack metadata is unsafe") from exc
        try:
            validate_pack_metadata(pack_toml, confined=True)
        except (ValueError, tomllib.TOMLDecodeError) as exc:
            if diagnostic_route == "agent-plugin":
                error_class = (
                    "unsafe-metadata"
                    if str(exc) == "pack metadata is unsafe"
                    else "invalid-metadata"
                )
                raise _agent_plugin_error(
                    candidate.name, "pack.toml", error_class
                ) from exc
            raise
        packs.append(Pack(name=entry.name, path=entry))
    return packs


# ---------------------------------------------------------------------------
# Claude-plugin route membership (docs/specs/claude-plugin-route-scope)
#
# The route is a user-scope distribution channel: a plugin's code always lives
# in the adopter's global cache, and `claude plugin install` defaults to
# `--scope user`. A pack declaring `allowed-scopes = ["repo"]` therefore forbids
# the only install this route offers, and publishing it contradicts the refusal
# contract ADR-0002 defines. One predicate decides membership; every writer that
# can publish calls it.
# ---------------------------------------------------------------------------

def is_publishable(pack_meta: dict, *, slug: str) -> bool:
    """Does this pack belong on the Claude-plugin route?

    Three conditions, all required (spec § The derived set):

    1. the slug is not underscore-prefixed (reserved authoring asset);
    2. — checked by the caller, which knows whether `.claude-plugin/plugin.json`
       is present; `discover_packs` requires only `pack.toml` today, so this
       function does not assume the manifest;
    3. the resolved scopes admit ``"user"``.

    Scope resolution reuses ``commands.validate._allowed_scopes`` rather than
    re-deriving it. That helper's real gate is ``[pack.adapter-contract].version``,
    **not** ``[pack.install]``: a pack declaring ``allowed-scopes`` with no
    contract version resolves ``["repo"]``. Re-deriving would fork that rule.
    """
    if slug.startswith("_"):
        return False
    from agentbundle.commands.validate import _allowed_scopes

    return "user" in _allowed_scopes(pack_meta)


def pack_is_publishable(pack_path: Path) -> bool:
    """`is_publishable` on disk, including manifest and hook-consent rails."""
    pack_toml = pack_path / "pack.toml"
    if not pack_toml.exists():
        return False
    if not (pack_path / ".claude-plugin" / "plugin.json").exists():
        return False
    meta = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
    return (
        is_publishable(meta, slug=pack_path.name)
        and _plugin_hook_consent_error(pack_path, meta) is None
    )


def _plugin_hook_consent_error(pack_path: Path, pack_meta: dict) -> str | None:
    """Return Rail B's refusal for user-capable hook packs without opt-in."""
    from agentbundle.commands.validate import _allowed_scopes

    pack = pack_meta.get("pack", {})
    install = pack.get("install", {}) if isinstance(pack, dict) else {}
    opted_in = (
        isinstance(install, dict)
        and install.get("user-scope-hooks") is True
    )
    return check_hooks(
        pack_path,
        _allowed_scopes(pack_meta),
        user_scope_hooks=opted_in,
    )


AGGREGATE_SCOPES = frozenset({"catalogue", "single-pack"})


def _skip_reason(pack_path: Path) -> str:
    """Why a pack is not publishable, in the reader's terms.

    Reporting a scope refusal for a pack that simply has no manifest is
    self-contradicting — it prints `allowed-scopes=['repo', 'user'] does not
    admit 'user'` and sends the reader to the wrong file.
    """
    if not (pack_path / "pack.toml").exists():
        return "no pack.toml"
    if not (pack_path / ".claude-plugin" / "plugin.json").exists():
        return "no .claude-plugin/plugin.json (required on this route)"
    from agentbundle.commands.validate import _allowed_scopes

    meta = tomllib.loads((pack_path / "pack.toml").read_text(encoding="utf-8"))
    consent_error = _plugin_hook_consent_error(pack_path, meta)
    if consent_error is not None:
        return (
            f"{consent_error}; set [pack.install] user-scope-hooks = true "
            "to consent to user-scope hook publication"
        )
    return (
        f"allowed-scopes={_allowed_scopes(meta)!r} does not admit 'user'"
    )


def _empty_marketplace_warning(excluded: list[str]) -> str:
    """What to say when the filter leaves a marketplace with no entries.

    Warn-and-continue, matching `self_host.py`'s sibling writer. This was a
    hard error until round thirteen, on the reasoning that "a catalogue that
    publishes nothing is a defect". That holds for *this* repository and is
    guarded precisely by `tools/lint-plugin-roster.py`, which pins the roster
    literally. It does not hold for an adopter: `contracts/pack.schema.json`
    makes `[pack.adapter-contract]` optional, so an adopter whose packs are
    all repo-scoped — a shape this project explicitly endorses — resolves to
    an empty plugin route through no fault of their own. Failing their
    `agentbundle catalogue build` outright is a regression in a published
    command, and it broke the catalogue-tooling smoke gate's own fixture.
    """
    detail = (
        f"{len(excluded)} excluded here: {', '.join(sorted(excluded))}"
        if excluded
        else "none reached this writer — the per-pack recipe filtered them "
        "upstream"
    )
    return (
        "marketplace: no packs reach the claude-plugins route "
        f"({detail}), so the marketplace is empty. That is a valid state for "
        "a catalogue whose packs all install at repo scope; they are reached "
        "with `agentbundle install`. If you expected entries here, check each "
        "pack's [pack.adapter-contract] version and [pack.install] "
        "allowed-scopes."
    )


def validate_pack_metadata(
    pack_toml_path: Path, *, confined: bool = False
) -> None:
    """Validate pack metadata, opting into route-local confined reads."""
    if confined:
        try:
            contents = read_confined_regular_file(
                pack_toml_path.parent,
                pack_toml_path,
                max_bytes=_AGENT_PLUGIN_PACK_TOML_MAX_BYTES,
            )
            metadata = tomllib.loads(contents.decode("utf-8"))
        except (UnsafeContentError, UnicodeDecodeError) as exc:
            raise ValueError("pack metadata is unsafe") from exc
    else:
        metadata = tomllib.loads(pack_toml_path.read_text(encoding="utf-8"))
    schema = json.loads(_read_bundled("pack.schema.json"))
    errors = validate_instance(metadata, schema)
    if errors:
        raise ValueError(
            f"pack metadata at {pack_toml_path} failed schema: "
            + "; ".join(errors)
        )


def validate_plugin_manifest(plugin_json_path: Path) -> None:
    """Validate a per-pack .claude-plugin/plugin.json against schema."""
    manifest = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    schema = json.loads(_read_bundled("plugin-manifest.schema.json"))
    errors = validate_instance(manifest, schema)
    if errors:
        raise ValueError(
            f"plugin manifest at {plugin_json_path} failed schema: "
            + "; ".join(errors)
        )


def validate_pack_uniqueness(pack: Pack) -> None:
    """Raise if a pack has two primitives with the same local name.

    The local name is the stem for most primitives, except `hooks` where
    `.sh` and `.py` are both legal (the spec § Hook extensions makes both
    valid in `packs/<pack>/.apm/hooks/`) — so for hooks we key by the
    full filename so `baz.sh` and `baz.py` coexist.
    """
    apm_root = pack.path / ".apm"
    if not apm_root.exists():
        return
    seen: dict[str, Path] = {}
    for primitive_dir_name in PRIMITIVE_DIRS:
        primitive_dir = apm_root / primitive_dir_name
        if not primitive_dir.exists():
            continue
        for child in primitive_dir.iterdir():
            local_name = child.name if primitive_dir_name == "hooks" else child.stem
            key = f"{primitive_dir_name}:{local_name}"
            if key in seen:
                raise ValueError(
                    f"pack {pack.name!r}: duplicate primitive {key!r} — "
                    f"{seen[key]} and {child}"
                )
            seen[key] = child


def run_recipe(
    recipe: Recipe,
    packs: Iterable[Pack],
    output_dir: Path,
    contract: dict,
    *,
    aggregate_scope: str,
    route_contract: dict | None = None,
) -> dict:
    """Execute a recipe and return a description of what it produced.

    `aggregate_scope` is required and has no default: it decides whether a
    pack skipped on the claude-plugins route is announced. A catalogue build
    names every exclusion (AC1); a single-pack render stays silent, because
    that is the flagship *successful* repo-scope path — `agentbundle install
    --pack core` — and a route refusal there reads as an error on a command
    that worked. A default would let `render_packs_to_dir` and `cmd_build
    --recipe` inherit the wrong policy silently. One of "catalogue" |
    "single-pack". The self-host writer is absent deliberately: it runs after
    adapters and seeds are written and warns inline.
    """
    if aggregate_scope not in AGGREGATE_SCOPES:
        # Validate here, not only where it is read: a typo at a per-pack call
        # site would otherwise pass silently.
        raise ValueError(
            f"aggregate_scope must be one of {sorted(AGGREGATE_SCOPES)}; "
            f"got {aggregate_scope!r}"
        )
    resolved_route: ResolvedDistributionRoute | None = None
    if recipe.type in {"per-pack", "aggregate"}:
        if recipe.route is None:
            raise ValueError(
                f"recipe {recipe.name!r}: field 'route' is required for "
                f"{recipe.type} distribution recipes"
            )
        if route_contract is None:
            route_contract = _load_distribution_route_contract()
        resolved_route = _resolve_distribution_route(recipe, route_contract)

    packs_list = list(packs)
    for pack in packs_list:
        if resolved_route is not None and resolved_route.identity == "agent-plugin":
            # Route admission owns the pack-authored filesystem boundary.  Run
            # its no-follow root checks before generic uniqueness inspection,
            # which is intentionally route-agnostic and may enumerate a
            # primitive directory after following its path.
            _validate_agent_plugin_pack_root(pack)
            _agent_plugin_excluding_primitives(pack)
            _validate_agent_plugin_skill_root(pack)
        try:
            validate_pack_uniqueness(pack)
        except (OSError, ValueError) as exc:
            if resolved_route is not None and resolved_route.identity == "agent-plugin":
                error_class = (
                    "duplicate" if isinstance(exc, ValueError) else "unsafe-source"
                )
                raise _agent_plugin_error(
                    pack.name, "primitive", error_class
                ) from exc
            raise

    if recipe.type == "per-pack":
        return _run_per_pack(
            recipe, packs_list, output_dir, contract,
            resolved_route=resolved_route,
            aggregate_scope=aggregate_scope,
        )
    if recipe.type == "aggregate":
        return _run_aggregate(
            recipe,
            output_dir,
            packs=packs_list,
            aggregate_scope=aggregate_scope,
            resolved_route=resolved_route,
        )
    if recipe.type == "overlay":
        return _run_overlay(recipe, packs_list)
    if recipe.type == "composite":
        return _run_composite(recipe, packs_list)
    raise ValueError(f"unknown recipe type {recipe.type!r}")


def _assert_under(target: Path, base: Path) -> None:
    """Refuse if `target.resolve()` would escape `base.resolve()`.

    Defense-in-depth against traversal in recipe `output-subdir` and
    contract `target-path` values. Repo-owned today; the CLI accepts
    external recipe paths via `--recipe path.toml`, so this guard is
    load-bearing the moment an operator points the CLI at untrusted TOML.
    """
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    try:
        target_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"refusing to write outside output root: {target_resolved} not under {base_resolved}"
        ) from exc


def _run_per_pack(
    recipe: Recipe,
    packs: list[Pack],
    output_dir: Path,
    contract: dict,
    *,
    resolved_route: ResolvedDistributionRoute | None,
    aggregate_scope: str,
) -> dict:
    if resolved_route is not None and resolved_route.package_projector == "apm-package":
        _preflight_route_source_trees(packs, resolved_route)
        return _run_per_pack_apm(recipe, packs, output_dir, resolved_route)
    if (
        resolved_route is not None
        and resolved_route.package_projector == "agent-plugin-root-manifest"
    ):
        return _run_per_pack_agent_plugin(
            recipe, packs, output_dir, resolved_route
        )
    adapter_projector = (
        resolved_route.adapter_projector
        if resolved_route is not None
        else recipe.adapter
    )
    if adapter_projector not in ADAPTERS:
        raise ValueError(f"unknown adapter target {adapter_projector!r}")
    if adapter_projector not in contract["adapter"]:
        raise ValueError(
            f"adapter {adapter_projector!r} declared in recipe but not in contract"
        )
    project = ADAPTERS[adapter_projector]
    produced: dict[str, str] = {}
    route_filtered = (
        resolved_route is not None
        and resolved_route.identity == "claude-plugins"
    )
    admitted_packs: list[Pack] = []
    for pack in packs:
        plugin_manifest = pack.path / ".claude-plugin" / "plugin.json"
        pack_toml = pack.path / "pack.toml"
        pack_meta = (
            tomllib.loads(pack_toml.read_text(encoding="utf-8"))
            if pack_toml.is_file()
            else {}
        )
        if route_filtered:
            consent_error = _plugin_hook_consent_error(pack.path, pack_meta)
            if consent_error is not None:
                raise ValueError(
                    f"pack {pack.name!r}: claude-plugins recipe: "
                    f"{consent_error}; set [pack.install] "
                    "user-scope-hooks = true to consent to user-scope hook "
                    "publication"
                )
        if route_filtered and not plugin_manifest.exists():
            wiring_source = contract["primitive"]["hook-wiring"]["source-path"]
            wiring_dir = pack.path / wiring_source.rstrip("/")
            has_wiring = wiring_dir.is_dir() and any(
                item.is_file() and item.suffix == ".toml"
                for item in wiring_dir.iterdir()
            )
            if has_wiring and is_publishable(pack_meta, slug=pack.name):
                raise ValueError(
                    f"pack {pack.name!r}: claude-plugins recipe: pack ships "
                    "hook wiring but has no .claude-plugin/plugin.json to "
                    "receive it"
                )
        if route_filtered and not pack_is_publishable(pack.path):
            # Route membership, not an error: a repo-only pack forbids the only
            # install this route offers. Named on stderr so an exclusion is
            # never silent (spec § AC1, AC3).
            if aggregate_scope == "catalogue":
                # Catalogue builds name every exclusion. A single-pack render —
                # which is what `agentbundle install --pack core` and every
                # render_pack consumer runs — would otherwise print a route
                # refusal on the flagship successful repo-scope path.
                print(
                    f"claude-plugins: skipping {pack.name} — "
                    f"{_skip_reason(pack.path)}",
                    file=sys.stderr,
                )
            continue
        admitted_packs.append(pack)

    if resolved_route is not None:
        _preflight_route_source_trees(admitted_packs, resolved_route)

    for pack in admitted_packs:
        try:
            _run_per_pack_single(
                pack,
                recipe,
                project,
                output_dir,
                contract,
                produced,
                resolved_route=resolved_route,
            )
        except ValueError as exc:
            # Pack-authored validation failures are expected input errors. Keep
            # their type so command handlers render a normal refusal instead of
            # leaking a traceback; prefix the pack for validators whose own
            # message does not already identify it.
            raise ValueError(f"pack {pack.name!r}: {exc}") from exc
        except Exception as exc:
            # Concern-9: surface the pack name so the operator knows which pack failed.
            raise RuntimeError(f"pack {pack.name!r}: {exc}") from exc
    return {"recipe": recipe.name, "type": recipe.type, "produced": produced}


def _projection_contract_for_route(
    contract: dict, resolved_route: ResolvedDistributionRoute
) -> dict:
    """Build a fresh adapter input from route capabilities without mutation."""
    if resolved_route.identity != "claude-plugins":
        return contract
    projection: list[dict] = []
    for source_entry in contract["adapter"]["claude-code"].get("projection", []):
        primitive = source_entry["primitive"]
        capability = resolved_route.component_capabilities[primitive]
        if (
            capability["status"] == "dropped"
            or capability["mode"] == "compiled-manifest"
        ):
            # Hook wiring is compiled separately into plugin.json; the runtime
            # adapter projector must not also retain stale direct-install
            # destinations or conflict semantics.
            entry = {"primitive": primitive, "mode": "dropped"}
        else:
            entry = dict(source_entry)
            entry["mode"] = capability["mode"]
            entry["target-path"] = capability["target-path"]
        projection.append(entry)
    adapters = dict(contract["adapter"])
    adapters["claude-code"] = {
        **contract["adapter"]["claude-code"],
        "projection": projection,
    }
    return {**contract, "adapter": adapters}


def _validate_route_source_tree(
    pack_root: Path, source_relative: str, *, route: str
) -> None:
    """Reject a source-root link that copytree would dereference into output."""
    source = pack_root / source_relative
    try:
        source.lstat()
    except FileNotFoundError:
        return
    if source.is_symlink():
        raise ValueError(
            f"{route}: refusing symlinked source root {source_relative!r}"
        )
    if not source.is_dir():
        raise ValueError(
            f"{route}: route source root {source_relative!r} is not a directory"
        )
    source_root = source.resolve(strict=True)
    try:
        source_root.relative_to(pack_root.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(
            f"{route}: route source root {source_relative!r} escapes the pack"
        ) from exc
    for directory, child_dirs, child_files in os.walk(source, followlinks=False):
        directory_path = Path(directory)
        for child_name in child_dirs + child_files:
            child = directory_path / child_name
            if not child.is_symlink():
                continue
            target = child.readlink()
            if target.is_absolute():
                raise ValueError(
                    f"{route}: unsafe absolute source link "
                    f"{child.relative_to(pack_root)}"
                )
            resolved_target = (child.parent / target).resolve(strict=False)
            try:
                resolved_target.relative_to(source_root)
            except ValueError as exc:
                raise ValueError(
                    f"{route}: source link {child.relative_to(pack_root)} "
                    "escapes its route source tree"
                ) from exc


def _preflight_route_source_trees(
    packs: Iterable[Pack], resolved_route: ResolvedDistributionRoute
) -> None:
    """Validate admitted route copy roots before any route output mutation."""
    for pack in packs:
        _validate_route_source_tree(pack.path, ".apm", route=resolved_route.identity)
        _validate_route_source_tree(pack.path, "seeds", route=resolved_route.identity)


def _run_per_pack_single(
    pack: Pack,
    recipe: Recipe,
    project,
    output_dir: Path,
    contract: dict,
    produced: dict[str, str],
    *,
    resolved_route: ResolvedDistributionRoute | None,
) -> None:
    """Execute the derivation pipeline for a single pack."""
    plugin_route = (
        resolved_route is not None
        and resolved_route.identity == "claude-plugins"
    )
    authored_hooks: dict[str, list[dict]] = {}
    plugin_manifest = pack.path / ".claude-plugin" / "plugin.json"
    if plugin_route:
        repo_prefix, plugin_prefix, hook_source, wiring_source = (
            claude_projection_paths(
                contract, resolved_route.component_capabilities
            )
        )
        authored_hooks = compile_plugin_hooks(
            pack.path,
            repo_hook_prefix=repo_prefix,
            plugin_hook_prefix=plugin_prefix,
            hook_source_path=hook_source,
            wiring_source_path=wiring_source,
            pack_name=pack.name,
        )
        wiring_dir = pack.path / wiring_source.rstrip("/")
        has_wiring = wiring_dir.is_dir() and any(
            p.is_file() and p.suffix == ".toml" for p in wiring_dir.iterdir()
        )
        if has_wiring and not plugin_manifest.exists():
            raise ValueError(
                "claude-plugins recipe: pack ships hook wiring but has no "
                ".claude-plugin/plugin.json to receive it"
            )
    projection_contract = (
        _projection_contract_for_route(contract, resolved_route)
        if resolved_route is not None
        else contract
    )
    route_output_subdir = (
        resolved_route.output_subdir
        if resolved_route is not None
        else recipe.output_subdir
    )
    per_pack_output = output_dir / route_output_subdir / pack.name
    _assert_under(per_pack_output, output_dir)
    # Transactional cleanup (Blocker-4): remove any prior partial or
    # crashed build so phantom files do not survive into this build.
    if per_pack_output.exists():
        shutil.rmtree(per_pack_output)
    per_pack_output.mkdir(parents=True, exist_ok=True)
    project(pack.path, projection_contract, per_pack_output)
    if plugin_manifest.exists():
        # Validate source-tree manifest against the source schema
        # (forbids hooks; additionalProperties: false ensures any stray
        # hooks block is caught here before synthesis).
        validate_plugin_manifest(plugin_manifest)
        destination = per_pack_output / ".claude-plugin" / "plugin.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Load, splice in synthesised SessionStart hook, re-serialise.
        derived = json.loads(plugin_manifest.read_text(encoding="utf-8"))
        # Claude Code 2.1.209+ hook contract: each event entry is an object
        # with a nested "hooks" array of typed hook objects, not a flat
        # {command} object. The old flat shape ({command}) is rejected with
        # "hooks: Invalid input" by the plugin validator.
        merged_hooks: dict[str, list[dict]] = {
            "SessionStart": [_SESSION_START_HOOK_ENTRY]
        }
        for event, entries in authored_hooks.items():
            merged_hooks.setdefault(event, []).extend(entries)
        derived["hooks"] = merged_hooks
        # enriched-pack-manifest: merge the projectable metadata subset derived
        # from this pack's pack.toml (emit-only-when-present, so a legacy pack
        # adds no keys and the output stays byte-identical).
        pack_toml_for_subset = pack.path / "pack.toml"
        if pack_toml_for_subset.exists():
            pack_meta = tomllib.loads(
                pack_toml_for_subset.read_text(encoding="utf-8")
            )
            derived.update(derive_projectable_subset(pack_meta))
        # Strip marketplace-only fields from the per-pack plugin.json.
        # "source" and "category" belong only in marketplace.json entries;
        # the Claude plugin validator warns they are ignored in plugin.json.
        # _run_aggregate re-adds them from pack.toml when building marketplace.json.
        for _marketplace_key in ("source", "category"):
            derived.pop(_marketplace_key, None)
        # Validate the derived manifest IN MEMORY before writing to disk
        # (Blocker-3: pre-write validation so a synthesis bug never lands
        # a malformed plugin.json in dist/).
        validate_derived_plugin_manifest_dict(
            derived, label=str(destination)
        )
        destination.write_text(
            json.dumps(derived, indent=2, sort_keys=False) + "\n",
            encoding="utf-8", newline="\n",
        )
        # Defence-in-depth: re-validate the written file against the schema
        # to catch any serialise/parse divergence introduced by json.dumps.
        validate_derived_plugin_manifest(destination)

    # Project pack.toml verbatim (writer reads it for name/version/allowed-scopes).
    pack_toml_src = pack.path / "pack.toml"
    if pack_toml_src.exists():
        shutil.copy2(pack_toml_src, per_pack_output / "pack.toml", follow_symlinks=False)

    # enriched-pack-manifest T5: project the pack's README.md into the route so
    # the manifest's `readme = "README.md"` pointer resolves. The README is the
    # sole portable per-pack doc. follow_symlinks=False mirrors the pack.toml
    # copy's posture (a symlinked README is not dereferenced into dist/).
    _project_pack_readme(pack.path, per_pack_output)

    # Project the canonical install-marker.py writer into scripts/.
    scripts_dir = per_pack_output / ".claude-plugin" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "install-marker.py").write_bytes(_read_install_marker_template())

    # Issue #190: ship the pack's seeds/ inside the plugin artifact so the
    # governance content travels with the pack on the Claude-plugin route
    # symlinks=True preserves a seed symlink as a
    # symlink rather than dereferencing the build host's file into dist/
    # at build time — matching the APM recipe's copytree posture.
    seeds_src = pack.path / "seeds"
    if seeds_src.is_dir():
        shutil.copytree(seeds_src, per_pack_output / "seeds", symlinks=True)

    produced[pack.name] = str(per_pack_output)


def _run_per_pack_apm(
    recipe: Recipe,
    packs: list[Pack],
    output_dir: Path,
    resolved_route: ResolvedDistributionRoute,
) -> dict:
    produced: dict[str, str] = {}
    writer_bytes = _read_install_marker_template()
    for pack in packs:
        per_pack_output = output_dir / resolved_route.output_subdir / pack.name
        _assert_under(per_pack_output, output_dir)
        # Transactional cleanup: remove any prior partial or crashed build
        # so phantom files do not survive into this build (mirrors the
        # claude-plugins derivation rail).
        if per_pack_output.exists():
            shutil.rmtree(per_pack_output)
        per_pack_output.mkdir(parents=True, exist_ok=True)
        pack_metadata = tomllib.loads((pack.path / "pack.toml").read_text(encoding="utf-8"))
        (per_pack_output / "apm.yml").write_text(
            _render_apm_yml(pack_metadata.get("pack", {})),
            encoding="utf-8", newline="\n",
        )
        apm_source = pack.path / ".apm"
        if apm_source.exists():
            apm_dest = per_pack_output / ".apm"
            if apm_dest.exists():
                shutil.rmtree(apm_dest)
            # symlinks=True preserves symlinks as symlinks rather than
            # dereferencing them — a pack containing a symlink to /etc/passwd
            # cannot exfiltrate the target into the published dist/ tree.
            shutil.copytree(apm_source, apm_dest, symlinks=True)

        # Project install-marker
        # artifacts (writer + JSON hook) and pack.toml into the per-pack
        # output. The writer is byte-identical to the canonical template
        # — drift gate enforces this at make build-check.
        hooks_dir = per_pack_output / ".apm" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "install-marker.py").write_bytes(writer_bytes)
        (hooks_dir / "install-marker.json").write_text(
            json.dumps(_APM_INSTALL_MARKER_HOOK_JSON, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )

        # Project pack.toml verbatim. The writer reads it for
        # name/version/allowed-scopes — same role as in the claude-plugins
        # derivation.
        pack_toml_src = pack.path / "pack.toml"
        if pack_toml_src.exists():
            shutil.copy2(
                pack_toml_src,
                per_pack_output / "pack.toml",
                follow_symlinks=False,
            )

        # enriched-pack-manifest T5: project the pack's README into the APM
        # route too (the sole portable per-pack doc; same posture as above).
        _project_pack_readme(pack.path, per_pack_output)

        # Issue #190: ship the pack's seeds/ inside the APM
        # package so the governance content travels with the pack on the APM
        # route. symlinks=True preserves a seed symlink as a symlink rather
        # than dereferencing the build host's file into dist/ at build time.
        seeds_src = pack.path / "seeds"
        if seeds_src.is_dir():
            shutil.copytree(seeds_src, per_pack_output / "seeds", symlinks=True)

        produced[pack.name] = str(per_pack_output)
    return {"recipe": recipe.name, "type": recipe.type, "produced": produced}


def _authored_hook_disclosure(hooks: object) -> str | None:
    """Render marketplace-safe metadata for compiled authored hooks.

    The synthetic marker is recognized structurally only at its guaranteed
    first ``SessionStart`` position. Executable hooks remain solely in the
    per-plugin manifest; this string is disclosure, not a registration source.
    """
    if not isinstance(hooks, dict):
        return None
    inventory: list[str] = []
    for event, entries in hooks.items():
        if not isinstance(event, str) or not isinstance(entries, list):
            raise ValueError("marketplace: derived hooks cannot be disclosed safely")
        for index, outer in enumerate(entries):
            if (
                event == "SessionStart"
                and index == 0
                and outer == _SESSION_START_HOOK_ENTRY
            ):
                continue
            if not isinstance(outer, dict):
                raise ValueError("marketplace: derived hook entry is not an object")
            matcher = outer.get("matcher", "*")
            inner_hooks = outer.get("hooks", [])
            if not isinstance(matcher, str) or not isinstance(inner_hooks, list):
                raise ValueError("marketplace: derived hook metadata is not disclosable")
            for inner in inner_hooks:
                if not isinstance(inner, dict):
                    raise ValueError("marketplace: derived command hook is not an object")
                command = inner.get("command")
                if not isinstance(command, str):
                    raise ValueError("marketplace: derived hook command is not a string")
                match = _COMPILED_PLUGIN_HOOK_COMMAND_RE.fullmatch(command)
                if match is None:
                    raise ValueError(
                        "marketplace: authored hook command cannot be rendered "
                        "as complete disclosure metadata"
                    )
                timeout = inner.get("timeout", 60)
                if not isinstance(timeout, int):
                    raise ValueError("marketplace: derived hook timeout is not an integer")
                inventory.append(
                    f"- {event} | matcher={matcher} | timeout={timeout}s | "
                    f"interpreter={match.group(1)} | path={match.group(2)}"
                )
    if not inventory:
        return None
    return "\n\nAuthored hooks ({}):\n{}".format(
        len(inventory), "\n".join(inventory)
    )


def _render_apm_yml(pack_metadata: dict) -> str:
    """Render the per-pack APM package metadata.

    Stdlib-only — no PyYAML. Values are JSON-encoded scalars (YAML is
    a JSON superset, so a JSON-quoted string is always a valid YAML
    scalar). This blocks YAML-key injection from a pack name or
    description containing newlines or YAML control characters.
    """
    lines = [
        f"name: {json.dumps(pack_metadata.get('name', ''))}",
        f"version: {json.dumps(pack_metadata.get('version', '0.0.0'))}",
    ]
    description = pack_metadata.get("description")
    if description:
        lines.append(f"description: {json.dumps(description)}")
    return "\n".join(lines) + "\n"


def _run_aggregate(
    recipe: Recipe,
    output_dir: Path,
    *,
    packs: list[Pack],
    aggregate_scope: str,
    resolved_route: ResolvedDistributionRoute | None = None,
) -> dict:
    """Aggregate per-pack manifests into a marketplace file.

    Membership is resolved from the **source** tree (`packs/<slug>/pack.toml`),
    never from the projected copy under `dist/`: `make build` has no dependency
    on `clean`, so a stale dist directory carries the *old* declaration and
    would republish contrary to the pack's current intent (spec § AC4).
    """
    input_subdir = (
        resolved_route.output_subdir
        if resolved_route is not None
        else recipe.input_subdir
    )
    input_dir = output_dir / input_subdir
    _assert_under(input_dir, output_dir)
    source_by_name = {p.name: p for p in packs}
    entries: list[dict] = []
    excluded: list[str] = []
    # Two distinct causes, kept apart. Reporting a stale directory as a scope
    # refusal sends the reader to a `pack.toml` that no longer exists — the
    # same self-contradiction `_skip_reason` exists to prevent at the per-pack
    # site.
    stale: list[str] = []
    # `aggregate_scope` is read at the emptiness warning below, and by
    # `_run_per_pack` for the skip line. Both are disclosure decisions the
    # caller owns.
    if input_dir.exists():
        for plugin_dir in sorted(input_dir.iterdir()):
            if plugin_dir.name == "marketplace.json" or not plugin_dir.is_dir():
                continue
            source = source_by_name.get(plugin_dir.name)
            # A dist directory with no source pack is stale — `make build` has
            # no `clean` dependency, so it survives a pack's deletion. Fail
            # closed: absent from the source tree means not publishable.
            if source is None:
                stale.append(plugin_dir.name)
                continue
            if not pack_is_publishable(source.path):
                excluded.append(plugin_dir.name)
                continue
            manifest = plugin_dir / ".claude-plugin" / "plugin.json"
            if manifest.exists():
                entry = json.loads(manifest.read_text(encoding="utf-8"))
                disclosure = _authored_hook_disclosure(entry.get("hooks"))
                # hooks are per-plugin installation artifacts, not marketplace
                # metadata; strip them from marketplace entries.
                entry.pop("hooks", None)
                if disclosure is not None:
                    description = entry.get("description", "")
                    if isinstance(description, str):
                        entry["description"] = description + disclosure
                # Re-add marketplace-only fields (source, category) from the
                # projected pack.toml (also present in the dist directory).
                # These were stripped from plugin.json to keep it clean of
                # fields the Claude plugin loader ignores at runtime.
                pack_toml_path = plugin_dir / "pack.toml"
                if pack_toml_path.exists():
                    pack_meta = tomllib.loads(
                        pack_toml_path.read_text(encoding="utf-8")
                    )
                    subset = derive_projectable_subset(pack_meta)
                    for _mk in ("source", "category"):
                        if _mk in subset:
                            entry[_mk] = subset[_mk]
                entries.append(entry)
    output_file = (
        f"{resolved_route.output_subdir}/marketplace.json"
        if resolved_route is not None
        else recipe.output_file
    )
    output_path = output_dir / output_file
    _assert_under(output_path, output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Derive marketplace name and owner from `source.url` (populated above from
    # pack.toml via derive_projectable_subset). This
    # reads `url` rather than the former `repo`: a `git-subdir` source carries
    # no `repo`, so leaving the old split in place would silently drop the
    # envelope's `name`, `owner` and `description` — the same defect the
    # 2026-07 "marketplace missing top-level name" fix already corrected once.
    # Every surviving entry must agree. Taking the FIRST match let a filtered
    # set silently re-key the marketplace to whichever pack happened to sort
    # first — identity derived from pack-supplied metadata, decided by an
    # unrelated membership change. Refuse on disagreement instead (spec AC7).
    identities: set[tuple[str, str]] = set()
    for entry in entries:
        src = entry.get("source")
        if not isinstance(src, dict):
            continue
        url = src.get("url", "")
        if not isinstance(url, str):
            continue
        m = _GITHUB_URL_RE.match(url)
        if m and "/" in m.group(1):
            owner_part, name_part = m.group(1).split("/", 1)
            identities.add((owner_part, name_part))

    if len(identities) > 1:
        rendered = ", ".join(f"{o}/{n}" for o, n in sorted(identities))
        raise ValueError(
            "marketplace: surviving entries disagree on the repository identity "
            f"the envelope is derived from ({rendered}). Publishing would key "
            "the marketplace to whichever pack sorted first."
        )

    marketplace_name: str | None = None
    marketplace_owner: dict | None = None
    if identities:
        owner_part, name_part = next(iter(identities))
        marketplace_name = name_part
        marketplace_owner = {"name": owner_part}

    payload: dict = {}
    if marketplace_name:
        payload["name"] = marketplace_name
        payload["description"] = _MARKETPLACE_DESCRIPTION
    if marketplace_owner:
        payload["owner"] = marketplace_owner
    payload["plugins"] = entries

    # All three lines take the caller's disclosure policy, not just the
    # emptiness warning below. No in-tree caller can reach the difference:
    # every `single-pack` caller renders into a fresh directory, so `excluded`
    # and `stale` are empty there. The gate guards an out-of-tree caller of
    # the public `render_pack_to_dir` that reuses one `output_dir` across
    # packs — it would otherwise get the `stale` line, mislabelled at that:
    # its pack list was narrowed, not deleted from the source tree.
    if aggregate_scope == "catalogue":
        if excluded:
            print(
                f"marketplace: excluded {len(excluded)} pack(s) not installable "
                f"at user scope: {', '.join(sorted(excluded))}",
                file=sys.stderr,
            )
        if stale:
            print(
                f"marketplace: excluded {len(stale)} directory/ies no longer "
                f"present in the source tree (stale dist/ — `make build` has no "
                f"`clean` dependency): {', '.join(sorted(stale))}",
                file=sys.stderr,
            )
    # Gated on the caller's mode, exactly like the per-pack skip line: a
    # single-pack render of a repo-only pack is a *successful* `agentbundle
    # install --pack core`, and announcing an empty marketplace there reads as
    # an error on a command that worked. Round thirteen added this warning
    # ungated and regressed AC12's single-pack silence.
    if aggregate_scope == "catalogue" and source_by_name and not entries:
        print(_empty_marketplace_warning(excluded + stale), file=sys.stderr)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    return {"recipe": recipe.name, "type": recipe.type, "entries": len(entries)}


def _run_overlay(recipe: Recipe, packs: list[Pack]) -> dict:
    expansion = {
        pack.name: [str(pack.path / unit.rstrip("/")) for unit in recipe.units]
        for pack in packs
    }
    return {"recipe": recipe.name, "type": recipe.type, "expansion": expansion}


def _run_composite(recipe: Recipe, packs: list[Pack]) -> dict:
    composed: list[str] = []
    for pack in packs:
        target = pack.path / (recipe.fragment_path or recipe.manifest_path or "")
        if target.exists():
            composed.append(str(target))
    return {"recipe": recipe.name, "type": recipe.type, "composed": composed}


def run_default_build(
    packs_dir: Path, output_dir: Path, contract: dict | None = None
) -> list[dict]:
    """Run the four default recipes — what plain `make build` invokes."""
    if contract is None:
        contract = tomllib.loads(_read_bundled("adapter.toml"))
    route_contract = _load_distribution_route_contract()
    packs = discover_packs(packs_dir, diagnostic_route="agent-plugin")
    results: list[dict] = []
    for recipe_name in DEFAULT_RECIPES:
        recipe = load_recipe(recipe_name)
        results.append(
            run_recipe(
                recipe,
                packs,
                output_dir,
                contract,
                aggregate_scope="catalogue",
                route_contract=route_contract,
            )
        )
    return results


def cmd_build(args) -> int:
    """argparse entrypoint for the `build` subcommand."""
    output_dir = Path(args.output_dir).resolve()
    packs_dir = Path(args.packs_dir).resolve()
    try:
        contract = tomllib.loads(_read_bundled("adapter.toml"))
        route_contract = _load_distribution_route_contract()
    except Exception as exc:
        print(f"build: failed to load contract: {exc}", file=sys.stderr)
        return 1

    if args.recipe:
        try:
            if "/" in args.recipe or args.recipe.endswith(".toml"):
                recipe = load_recipe_from_path(Path(args.recipe))
            else:
                recipe = load_recipe(args.recipe)
        except (FileNotFoundError, ValueError) as exc:
            print(f"build: recipe {args.recipe!r}: {exc}", file=sys.stderr)
            return 1
        try:
            packs = discover_packs(
                packs_dir,
                diagnostic_route=(
                    "agent-plugin" if recipe.route == "agent-plugin" else None
                ),
            )
            # `--pack` narrows an explicit `--recipe` run to one pack (the
            # `make build RECIPE=... PACK=...` form). That is a
            # single-pack aggregate, not a catalogue: an emptied marketplace is
            # the expected outcome for a repo-only pack, not a defect.
            aggregate_scope = "catalogue"
            if args.pack:
                # An aggregate recipe writes ONE shared marketplace over the
                # whole dist tree. Narrowing its pack list made it rewrite that
                # file down to the single pack and exit 0 — a silent truncation
                # of an artifact other packs share. Per-pack recipes are fine.
                if recipe.type == "aggregate":
                    print(
                        f"build: --pack is not meaningful for the "
                        f"{recipe.name!r} aggregate recipe, which writes one "
                        f"marketplace over the whole dist tree; drop --pack or "
                        f"choose a per-pack recipe",
                        file=sys.stderr,
                    )
                    return 1
                packs = [p for p in packs if p.name == args.pack]
                aggregate_scope = "single-pack"
            run_recipe(
                recipe,
                packs,
                output_dir,
                contract,
                aggregate_scope=aggregate_scope,
                route_contract=route_contract,
            )
        except ValueError as exc:
            print(f"build: {exc}", file=sys.stderr)
            return 1
        return 0

    # Default `build` (no --recipe): run the four default recipes.
    try:
        run_default_build(packs_dir, output_dir, contract)
    except ValueError as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 1
    return 0
