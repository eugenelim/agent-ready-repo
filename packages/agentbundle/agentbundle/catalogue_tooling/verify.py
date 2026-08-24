"""Catalogue verification engine — 19-step source-checkout pipeline.

Entry points:
  ``verify_catalogue(root, pack=None) -> VerifyResult``
  ``render_json(result) -> str``
  ``render_table(result) -> str``
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
)
from agentbundle.catalogue_tooling.manifest import MANIFEST_NAME, plugin_json_path
from agentbundle.catalogue_tooling.results import Diagnostic, Severity, VerifyResult

_AGENTBUNDLE_VERSION: str | None = None
_PACK_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _get_agentbundle_version() -> str:
    global _AGENTBUNDLE_VERSION
    if _AGENTBUNDLE_VERSION is None:
        try:
            from agentbundle import __version__
            _AGENTBUNDLE_VERSION = __version__
        except Exception:
            _AGENTBUNDLE_VERSION = "unknown"
    return _AGENTBUNDLE_VERSION


def _err(code: str, message: str, pack: str | None = None, path: str | None = None) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        pack=pack,
        path=path,
        line=None,
        col=None,
        message=message,
        remediation=None,
    )


def _warn(code: str, message: str, pack: str | None = None, path: str | None = None) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.WARN,
        pack=pack,
        path=path,
        line=None,
        col=None,
        message=message,
        remediation=None,
    )


def _info(code: str, message: str, pack: str | None = None, path: str | None = None) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.INFO,
        pack=pack,
        path=path,
        line=None,
        col=None,
        message=message,
        remediation=None,
    )


def _load_bundled_json(name: str) -> dict:
    """Load a JSON contract through the package's zipapp-safe reader."""
    from agentbundle.build.main import _read_bundled

    return json.loads(_read_bundled(name))


def _path_is_junction(path: Path) -> bool:
    """Return whether *path* is a Windows junction when the runtime supports it."""
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def _confined_pack_candidate(packs_dir: Path, slug: object) -> tuple[Path | None, str | None]:
    """Resolve a pack slug beneath *packs_dir* without following link-like escapes."""
    if not isinstance(slug, str) or not _PACK_SLUG_RE.fullmatch(slug):
        return None, "pack reference must use the canonical lowercase slug grammar"
    candidate = packs_dir / slug
    try:
        if candidate.is_symlink() or _path_is_junction(candidate):
            return None, "pack reference refused: link is outside the packs root"
        canonical_root = packs_dir.resolve()
        canonical_candidate = candidate.resolve()
    except (OSError, RuntimeError):
        return None, "pack reference refused: path cannot be resolved safely"
    if not canonical_candidate.is_relative_to(canonical_root):
        return None, "pack reference refused: path is outside the packs root"
    return canonical_candidate, None


def _confined_directory_issue(root: Path, path: Path) -> str | None:
    """Describe why *path* is not a real directory confined below *root*."""
    if path.is_symlink() or _path_is_junction(path):
        return "link-like"
    try:
        canonical_root = root.resolve(strict=True)
        canonical_path = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return "unresolvable"
    if not canonical_path.is_relative_to(canonical_root):
        return "outside its pack root"
    return None


def _diagnostic_path(root: Path, path: Path) -> str:
    """Return a repository-relative label without exposing an outside path."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return "<outside-root>"


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def _step_config_validation(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 1: validate catalogue.toml if present."""
    # load_catalogue_config already ran and produced config; absence is fine.
    return []


def _step_lint(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 2: run catalogue lint, including its source-identity checks."""
    from agentbundle.catalogue_tooling.lint import lint_catalogue
    result = lint_catalogue(root, pack=pack)
    diags: list[Diagnostic] = []
    for d in result.diagnostics:
        if d.severity == Severity.ERROR:
            diags.append(_err("CAT-V-002", f"lint: {d.message}", pack=d.pack, path=d.path))
    return diags


def _step_pack_schema(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 3: validate each pack's pack.toml against pack schema."""
    if config is None:
        return []
    try:
        from agentbundle.build.validate import validate as validate_schema
    except ImportError:
        return []

    packs_dir_name = getattr(config, "paths", None)
    packs_dir = root / (getattr(packs_dir_name, "packs", "packs") if packs_dir_name else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-003",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []

    try:
        schema = _load_bundled_json("pack.schema.json")
    except (OSError, ValueError):
        return []

    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if pack_dir.name.startswith("_"):
            continue  # reserved authoring asset
        if not pack_dir.is_dir():
            continue
        if pack and pack_dir.name != pack:
            continue
        pack_issue = _confined_directory_issue(packs_dir, pack_dir)
        if pack_issue is not None:
            diags.append(
                _err(
                    "CAT-V-003",
                    f"refused {pack_issue} pack directory",
                    pack=pack_dir.name,
                    path=_diagnostic_path(root, pack_dir),
                )
            )
            continue
        pack_toml = pack_dir / "pack.toml"
        if not (pack_toml.exists() or pack_toml.is_symlink() or _path_is_junction(pack_toml)):
            continue
        try:
            import tomllib
            content = read_confined_regular_file(pack_dir, pack_toml).decode("utf-8")
            contract = tomllib.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            diags.append(_err("CAT-V-003", f"pack.toml parse error: {exc}", pack=pack_dir.name))
            continue
        errors = validate_schema(contract, schema)
        for error in errors:
            diags.append(_err("CAT-V-003", f"pack schema: {error}", pack=pack_dir.name))
    return diags


def _plugin_json_path(pack_dir: Path) -> Path:
    """Manifest location for a pack — the only one the build pipeline reads.

    Thin alias over the shared convention in `catalogue_tooling.manifest`, kept
    so this module's many call sites read unchanged.
    """
    return plugin_json_path(pack_dir)


def _step_plugin_validation(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 4: validate plugin.json presence and JSON parse."""
    packs_dir_name = getattr(config, "paths", None)
    packs_dir = root / (getattr(packs_dir_name, "packs", "packs") if packs_dir_name else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-004",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []

    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if pack_dir.name.startswith("_"):
            continue  # reserved authoring asset
        if not pack_dir.is_dir():
            continue
        if pack and pack_dir.name != pack:
            continue
        pack_issue = _confined_directory_issue(packs_dir, pack_dir)
        if pack_issue is not None:
            diags.append(
                _err(
                    "CAT-V-004",
                    f"refused {pack_issue} pack directory",
                    pack=pack_dir.name,
                    path=_diagnostic_path(root, pack_dir),
                )
            )
            continue
        # The pack root is not a manifest location. A plugin.json there is
        # invisible to every consumer while looking present in the tree —
        # whether it is a misplaced manifest or a leftover stale copy.
        if (pack_dir / MANIFEST_NAME).exists():
            diags.append(_err(
                "CAT-V-004",
                "plugin.json is at the pack root; it belongs at .claude-plugin/plugin.json",
                pack=pack_dir.name,
            ))
        plugin_json = _plugin_json_path(pack_dir)
        if not (
            plugin_json.exists()
            or plugin_json.is_symlink()
            or _path_is_junction(plugin_json)
        ):
            continue  # a pack need not ship a manifest; catalogue lint agrees
        try:
            content = read_confined_regular_file(pack_dir, plugin_json).decode("utf-8")
            json.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            diags.append(_err("CAT-V-004", f"plugin.json parse error: {exc}", pack=pack_dir.name))
    return diags


def _step_version_parity(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 5: pack.toml and plugin.json name/version must match."""
    packs_dir_name = getattr(config, "paths", None)
    packs_dir = root / (getattr(packs_dir_name, "packs", "packs") if packs_dir_name else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-005",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []

    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if pack_dir.name.startswith("_"):
            continue  # reserved authoring asset
        if not pack_dir.is_dir():
            continue
        if pack and pack_dir.name != pack:
            continue
        pack_issue = _confined_directory_issue(packs_dir, pack_dir)
        if pack_issue is not None:
            diags.append(
                _err(
                    "CAT-V-005",
                    f"refused {pack_issue} pack directory",
                    pack=pack_dir.name,
                    path=_diagnostic_path(root, pack_dir),
                )
            )
            continue
        pack_toml_path = pack_dir / "pack.toml"
        manifest_path = _plugin_json_path(pack_dir)
        pack_toml_present = (
            pack_toml_path.exists()
            or pack_toml_path.is_symlink()
            or _path_is_junction(pack_toml_path)
        )
        manifest_present = (
            manifest_path.exists()
            or manifest_path.is_symlink()
            or _path_is_junction(manifest_path)
        )
        if not pack_toml_present or not manifest_present:
            continue
        try:
            import tomllib
            pack_content = read_confined_regular_file(pack_dir, pack_toml_path).decode("utf-8")
            manifest_content = read_confined_regular_file(pack_dir, manifest_path).decode("utf-8")
            pt = tomllib.loads(pack_content)
            pj = json.loads(manifest_content)
        except (
            UnsafeContentError,
            UnicodeDecodeError,
            tomllib.TOMLDecodeError,
            json.JSONDecodeError,
        ) as exc:
            diags.append(
                _err(
                    "CAT-V-005",
                    f"version parity inputs cannot be read safely: {exc}",
                    pack=pack_dir.name,
                )
            )
            continue
        pt_name = (pt.get("pack") or {}).get("name")
        pt_version = (pt.get("pack") or {}).get("version")
        pj_name = pj.get("name")
        pj_version = pj.get("version")
        if pt_name and pj_name and pt_name != pj_name:
            diags.append(_err(
                "CAT-V-005",
                f"pack.toml name {pt_name!r} != plugin.json name {pj_name!r}",
                pack=pack_dir.name,
            ))
        if pt_version and pj_version and pt_version != pj_version:
            diags.append(_err(
                "CAT-V-005",
                f"pack.toml version {pt_version!r} != plugin.json version {pj_version!r}",
                pack=pack_dir.name,
            ))
    return diags


def _step_profiles(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 6: validate profile schema and confined local pack references."""
    profiles_dir_name = getattr(config, "paths", None)
    profiles_dir = root / (
        getattr(profiles_dir_name, "profiles", "profiles") if profiles_dir_name else "profiles"
    )
    profiles_present = (
        profiles_dir.exists()
        or profiles_dir.is_symlink()
        or _path_is_junction(profiles_dir)
    )
    profiles_issue = (
        _confined_directory_issue(root, profiles_dir) if profiles_present else None
    )
    if profiles_issue is not None:
        return [
            _err(
                "CAT-V-006",
                f"refused {profiles_issue} profiles directory",
                path=_diagnostic_path(root, profiles_dir),
            )
        ]
    if not profiles_dir.is_dir():
        return []
    packs_dir = root / (
        getattr(profiles_dir_name, "packs", "packs") if profiles_dir_name else "packs"
    )
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-006",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    try:
        schema = _load_bundled_json("profile.schema.json")
        from agentbundle.build.validate import validate as validate_schema
    except (OSError, ValueError, ImportError) as exc:
        return [_err("CAT-V-006", f"profile schema is unavailable: {exc}")]

    diags: list[Diagnostic] = []
    for profile_file in sorted(profiles_dir.iterdir()):
        if profile_file.suffix not in (".toml", ".json"):
            continue
        try:
            content = read_confined_regular_file(profiles_dir, profile_file).decode("utf-8")
            if profile_file.suffix == ".toml":
                import tomllib
                profile_data = tomllib.loads(content)
            else:
                profile_data = json.loads(content)
        except (UnsafeContentError, UnicodeDecodeError) as exc:
            diags.append(
                _err(
                    "CAT-V-006",
                    f"profile {profile_file.name!r} is unsafe: {exc}",
                    path=_diagnostic_path(root, profile_file),
                )
            )
            continue
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            diags.append(
                _err(
                    "CAT-V-006",
                    f"profile {profile_file.name!r} parse error: {exc}",
                    path=_diagnostic_path(root, profile_file),
                )
            )
            continue

        errors = validate_schema(profile_data, schema)
        for error in errors:
            diags.append(
                _err(
                    "CAT-V-006",
                    f"profile {profile_file.name!r} schema: {error}",
                    path=str(profile_file.relative_to(root)),
                )
            )
        if errors or not isinstance(profile_data, dict):
            continue
        for entry in profile_data.get("packs", []):
            if not isinstance(entry, dict):
                continue
            slug = entry.get("pack")
            candidate, reason = _confined_pack_candidate(packs_dir, slug)
            if reason:
                diags.append(
                    _err(
                        "CAT-V-006",
                        f"profile {profile_file.name!r}: {reason}",
                        path=str(profile_file.relative_to(root)),
                    )
                )
            elif candidate is not None and not candidate.is_dir():
                diags.append(
                    _err(
                        "CAT-V-006",
                        f"profile {profile_file.name!r}: pack {slug!r} is missing",
                        path=str(profile_file.relative_to(root)),
                    )
                )
    return diags


def _step_dependencies(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 7: validate dependency grammar, local resolution, and required cycles."""
    import tomllib

    from agentbundle.catalogue_tooling.version_ranges import (
        parse_version_range,
        version_satisfies,
    )

    paths = getattr(config, "paths", None)
    packs_dir = root / (getattr(paths, "packs", "packs") if paths else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-007",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []
    catalogue_name = getattr(config, "name", None) if config else None
    diags: list[Diagnostic] = []
    contracts: dict[str, dict | None] = {}

    def load_pack(name: str) -> dict | None:
        """Load one safely named pack manifest once."""
        if name in contracts:
            return contracts[name]
        candidate, reason = _confined_pack_candidate(packs_dir, name)
        if reason or candidate is None or not candidate.is_dir():
            contracts[name] = None
            return None
        manifest = candidate / "pack.toml"
        if not manifest.is_file():
            contracts[name] = None
            return None
        try:
            content = read_confined_regular_file(candidate, manifest).decode("utf-8")
            value = tomllib.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            diags.append(
                _err(
                    "CAT-V-007",
                    f"pack {name!r}: pack.toml cannot be read safely: {exc}",
                    pack=name,
                    path=_diagnostic_path(root, manifest),
                )
            )
            contracts[name] = None
            return None
        contracts[name] = value
        return value

    if pack is not None:
        initial_names = [pack]
    else:
        initial_names = [
            candidate.name
            for candidate in sorted(packs_dir.iterdir())
            if candidate.is_dir()
            and not candidate.name.startswith("_")
            and not candidate.is_symlink()
            and not _path_is_junction(candidate)
        ]

    graph: dict[str, set[str]] = {}
    queue = list(initial_names)
    processed: set[str] = set()
    while queue:
        owner = queue.pop(0)
        if owner in processed:
            continue
        processed.add(owner)
        contract = load_pack(owner)
        if contract is None:
            continue
        graph.setdefault(owner, set())
        dependencies = contract.get("pack", {}).get("dependencies", {})
        if not isinstance(dependencies, dict):
            continue
        has_entries = any(
            dependencies.get(kind)
            for kind in ("required", "recommended", "conflicts")
        )
        warned_unknown_identity = False
        for kind in ("required", "recommended", "conflicts"):
            entries = dependencies.get(kind) or []
            if not isinstance(entries, list):
                diags.append(
                    _err(
                        "CAT-V-007",
                        f"pack {owner!r}: dependencies.{kind} must be a list",
                        pack=owner,
                    )
                )
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    diags.append(
                        _err(
                            "CAT-V-007",
                            f"pack {owner!r}: {kind} dependency must be an object",
                            pack=owner,
                        )
                    )
                    continue
                dep_catalogue = entry.get("catalogue")
                dep_name = entry.get("pack")
                dep_range = entry.get("version")
                fields = (dep_catalogue, dep_name, dep_range)
                if not all(isinstance(value, str) and value for value in fields):
                    diags.append(
                        _err(
                            "CAT-V-007",
                            f"pack {owner!r}: {kind} dependency requires catalogue, "
                            "pack, and version",
                            pack=owner,
                        )
                    )
                    continue
                if not parse_version_range(dep_range):
                    diags.append(
                        _err(
                            "CAT-V-007",
                            f"pack {owner!r}: dependency {dep_name!r} has invalid "
                            f"version range {dep_range!r}",
                            pack=owner,
                        )
                    )
                    continue
                if catalogue_name is None:
                    if has_entries and not warned_unknown_identity:
                        diags.append(
                            _info(
                                "CAT-V-007",
                                "catalogue identity unknown (no catalogue.toml); "
                                f"local dependency classification skipped for pack {owner!r}",
                                pack=owner,
                            )
                        )
                        warned_unknown_identity = True
                    continue
                if dep_catalogue != catalogue_name:
                    continue

                candidate, reason = _confined_pack_candidate(packs_dir, dep_name)
                if _PACK_SLUG_RE.fullmatch(dep_name):
                    diagnostic_path = str((packs_dir / dep_name).relative_to(root))
                else:
                    diagnostic_path = str(packs_dir.relative_to(root) / "<invalid-pack-reference>")
                if reason:
                    diags.append(
                        _err(
                            "CAT-V-007",
                            f"pack {owner!r}: {reason}",
                            pack=owner,
                            path=diagnostic_path,
                        )
                    )
                    continue
                if kind == "conflicts":
                    continue
                if candidate is None or not candidate.is_dir():
                    if kind == "required":
                        diags.append(
                            _err(
                                "CAT-V-007",
                                f"pack {owner!r}: missing required dependency {dep_name!r}",
                                pack=owner,
                                path=diagnostic_path,
                            )
                        )
                    continue
                dep_contract = load_pack(dep_name)
                if kind == "required":
                    graph[owner].add(dep_name)
                    graph.setdefault(dep_name, set())
                    if pack is not None and dep_name not in processed:
                        queue.append(dep_name)
                    dep_version = (
                        dep_contract.get("pack", {}).get("version")
                        if dep_contract is not None
                        else None
                    )
                    if version_satisfies(dep_version, dep_range) is not True:
                        diags.append(
                            _err(
                                "CAT-V-007",
                                f"pack {owner!r}: dependency {dep_name!r} version {dep_version!r} "
                                f"does not satisfy {dep_range!r}",
                                pack=owner,
                                path=diagnostic_path,
                            )
                        )

    visited: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()
    for start in sorted(graph):
        if start in visited:
            continue
        stack: list[tuple[str, list[str], int]] = [(start, sorted(graph[start]), 0)]
        active: list[str] = [start]
        active_set = {start}
        while stack:
            node, neighbours, index = stack[-1]
            if index >= len(neighbours):
                stack.pop()
                active_set.discard(node)
                if active and active[-1] == node:
                    active.pop()
                visited.add(node)
                continue
            neighbour = neighbours[index]
            stack[-1] = (node, neighbours, index + 1)
            if neighbour in active_set:
                cycle_start = active.index(neighbour)
                cycle = active[cycle_start:] + [neighbour]
                cycle_key = frozenset(cycle)
                if cycle_key not in reported_cycles:
                    reported_cycles.add(cycle_key)
                    for cycle_pack in sorted(cycle_key):
                        diags.append(
                            _err(
                                "CAT-V-007",
                                f"{' -> '.join(cycle)}: circular required dependency",
                                pack=cycle_pack,
                            )
                        )
                continue
            if neighbour in visited:
                continue
            active.append(neighbour)
            active_set.add(neighbour)
            stack.append((neighbour, sorted(graph.get(neighbour, set())), 0))
    return diags


def _step_adapter_compat(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 8: reject unknown adapters declared by non-legacy packs."""
    from agentbundle.config import pack_spec_version
    from agentbundle.scope import shipped_adapters_from_contract

    try:
        known_adapters = set(shipped_adapters_from_contract())
    except (OSError, ValueError) as exc:
        return [_err("CAT-V-008", f"adapter contract is unavailable: {exc}")]
    import tomllib
    paths = getattr(config, "paths", None)
    packs_dir = root / (getattr(paths, "packs", "packs") if paths else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-008",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []
    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if (
            not pack_dir.is_dir()
            or pack_dir.name.startswith("_")
            or pack_dir.is_symlink()
            or _path_is_junction(pack_dir)
            or (pack is not None and pack_dir.name != pack)
        ):
            continue
        manifest = pack_dir / "pack.toml"
        if not manifest.is_file():
            continue
        try:
            content = read_confined_regular_file(pack_dir, manifest).decode("utf-8")
            contract = tomllib.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            diags.append(
                _err(
                    "CAT-V-008",
                    f"pack.toml cannot be read safely: {exc}",
                    pack=pack_dir.name,
                    path=_diagnostic_path(root, manifest),
                )
            )
            continue
        version = pack_spec_version(contract)
        if version is None or version == "0.1":
            continue
        install = contract.get("pack", {}).get("install", {})
        allowed = install.get("allowed-adapters", []) if isinstance(install, dict) else []
        if not isinstance(allowed, list):
            continue
        for adapter in allowed:
            if isinstance(adapter, str) and adapter not in known_adapters:
                diags.append(
                    _err(
                        "CAT-V-008",
                        f"unknown allowed adapter {adapter!r}",
                        pack=pack_dir.name,
                        path=str(manifest.relative_to(root)),
                    )
                )
    return diags


def _step_primitive_layout(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 9: primitive layout validation (delegated to lint step 2)."""
    return []


def _step_build_output(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 10: build into tmpdir and check for errors.

    Never writes to catalogue root. Skips when catalogue.toml is absent.
    """
    if config is None:
        return []
    from agentbundle.catalogue_tooling.build import build_catalogue
    build_output = tmpdir / "dist"
    build_output.mkdir(parents=True, exist_ok=True)
    try:
        result = build_catalogue(root, output=build_output, pack=pack)
    except Exception as exc:
        return [_err("CAT-V-010", f"build step failed: {exc}")]
    if not result.ok:
        return [_err("CAT-V-010", "build output validation failed")]
    return []


def _step_agent_artifacts(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 11: lint portable .claude/ agent artifact contracts.

    ALL yaml.* references live inside this function body — none at module scope.
    """
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        return [_warn("CAT-V-011",
                      "PyYAML required for agent-artifact lint — install agentbundle[lint]")]

    # --- Duplicate-key detection (inside PyYAML fence) ---

    class _DuplicateKeyError(Exception):
        def __init__(self, key: object, line: int) -> None:
            self.key = key
            self.line = line

    class _FrontmatterLoader(yaml.SafeLoader):
        pass

    def _construct_mapping_no_dups(loader: object, node: object, deep: bool = False) -> dict:
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None,
                f"expected a mapping node, got {node.id}",  # type: ignore[attr-defined]
                node.start_mark,  # type: ignore[attr-defined]
            )
        mapping: dict = {}
        for key_node, value_node in node.value:  # type: ignore[attr-defined]
            key = loader.construct_object(key_node, deep=deep)  # type: ignore[attr-defined]
            if key in mapping:
                raise _DuplicateKeyError(key, key_node.start_mark.line + 1)
            mapping[key] = loader.construct_object(value_node, deep=deep)  # type: ignore[attr-defined]
        return mapping

    _FrontmatterLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_mapping_no_dups,
    )

    # --- Constants ---

    KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")
    LINK = re.compile(r"\]\(([^)]+)\)")
    ALLOWED_SKILL_KEYS = {"name", "description", "license", "compatibility",
                          "metadata", "allowed-tools"}
    ALLOWED_PRIMITIVE_CLASSES = {"credentialed-cli", "mcp-server"}
    ALLOWED_AUTH_BROKERS = ("env", "cli", "creds", "sso-cookie")
    # Claude Code agent frontmatter. `skills` (preload set) is admitted because
    # it is the portable field carrying "which skills may this agent reach". An
    # empty `skills` list is the portable no-skill opt-out — the Kiro projectors
    # consume it to suppress their `skill://` resource injection; a non-empty
    # list is a build error until `skill://` URI templating exists (see
    # `contracts/adapter.toml` on the kiro-ide `inject-resources` entry).
    # Kiro's own `resources` is deliberately NOT admitted: it is consumer-native,
    # not valid Claude Code frontmatter, and a source agent declaring it would
    # land verbatim in `.claude/agents/` via the byte-copy `direct-file`
    # projection.
    ALLOWED_AGENT_KEYS = {"name", "description", "tools", "model", "skills"}
    ALLOWED_COMMAND_KEYS = {"description", "allowed-tools", "model", "argument-hint"}
    diags: list[Diagnostic] = []

    def _report(path: Path, msg: str) -> None:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        diags.append(_err("CAT-V-011", msg, path=str(rel)))

    def parse_frontmatter(path: Path):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None, 0, text, None
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is None:
            return None, 0, text, "frontmatter opened with --- but never closed"
        fm_text = "\n".join(lines[1:end])
        body_start_line = end + 2
        body = "\n".join(lines[end + 1:])
        try:
            fields = yaml.load(fm_text, Loader=_FrontmatterLoader)  # nosec B506
        except _DuplicateKeyError as exc:
            return None, 0, text, (
                f"duplicate frontmatter key {exc.key!r} (line {exc.line + 1})"
            )
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            problem = getattr(exc, "problem", None) or str(exc)
            if mark is not None:
                return None, 0, text, (
                    f"malformed frontmatter (line {mark.line + 2}): {problem}"
                )
            return None, 0, text, f"malformed frontmatter: {problem}"
        if fields is None:
            fields = {}
        if not isinstance(fields, dict):
            return None, 0, text, (
                "frontmatter must be a mapping at the top level "
                f"(got {type(fields).__name__})"
            )
        return fields, body_start_line, body, None

    def check_links(path: Path, body: str, body_start_line: int) -> None:
        base = path.parent
        for _offset, line in enumerate(body.splitlines()):
            for match in LINK.finditer(line):
                target = match.group(1).split("#", 1)[0].strip()
                if not target:
                    continue
                if re.match(r"^[a-z]+:", target):
                    continue
                resolved = (base / target).resolve()
                if not resolved.exists():
                    _report(path, f"broken link → {match.group(1)}")

    def check_skill(path: Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            _report(path, ferr)
            return
        if fields is None:
            _report(path, "missing YAML frontmatter (--- ... ---)")
            return
        name = fields.get("name")
        if name is None or name == "":
            _report(path, "frontmatter missing required key: name")
        elif not isinstance(name, str):
            _report(path, f"frontmatter key 'name' must be a string "
                         f"(got {type(name).__name__}) — quote "
                         f"Norway-style scalars like 'yes' / 'no' / 'on' / "
                         f"'off' to keep them as text")
        elif not KEBAB.match(name):
            _report(path, f"name {name!r} must be kebab-case ([a-z][a-z0-9-]*)")
        elif name != path.parent.name:
            _report(path, f"name {name!r} does not match directory "
                         f"{path.parent.name!r}")
        desc = fields.get("description")
        if desc is None or desc == "":
            _report(path, "frontmatter missing required key: description")
        elif not isinstance(desc, str):
            _report(path, f"frontmatter key 'description' must be a string "
                         f"(got {type(desc).__name__}) — "
                         f"quote Norway-style scalars like 'yes' / 'no'")
        unknown = set(fields) - ALLOWED_SKILL_KEYS
        if unknown:
            _report(path, f"unknown frontmatter keys: {sorted(unknown)} "
                         f"(allowed: {sorted(ALLOWED_SKILL_KEYS)})")
        metadata = fields.get("metadata")
        if metadata is not None and metadata != "" and not isinstance(metadata, dict):
            _report(path, f"frontmatter key 'metadata' must be a nested "
                         f"mapping (got {type(metadata).__name__})")
            metadata = None
        meta = metadata if isinstance(metadata, dict) else {}
        if "credentialed" in meta:
            cval = meta["credentialed"]
            if cval is not True and cval is not False:
                _report(path, f"frontmatter key 'metadata.credentialed' must "
                             f"be boolean (true|false), got {cval!r}")
        if "primitive-class" in meta:
            pval = meta["primitive-class"]
            if pval not in ALLOWED_PRIMITIVE_CLASSES:
                _report(path, f"frontmatter key 'metadata.primitive-class' "
                             f"must be one of: "
                             f"{', '.join(sorted(ALLOWED_PRIMITIVE_CLASSES))} "
                             f"(got {pval!r})")
        auth_present = "auth" in meta
        if auth_present:
            aval = meta["auth"]
            if aval not in ALLOWED_AUTH_BROKERS:
                _report(path, f"frontmatter key 'metadata.auth' must be one of "
                             f"{{{', '.join(ALLOWED_AUTH_BROKERS)}}}; "
                             f"got {aval!r}")
        if meta.get("credentialed") is True and not auth_present:
            _report(path, "frontmatter key 'metadata.auth' is required when "
                         "metadata.credentialed: true "
                         f"(declare one of {{{', '.join(ALLOWED_AUTH_BROKERS)}}})")
        if not body.strip():
            _report(path, "body is empty")
        check_links(path, body, body_start)

    def check_agent(path: Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            _report(path, ferr)
            return
        if fields is None:
            _report(path, "missing YAML frontmatter (--- ... ---)")
            return
        expected_name = path.stem
        name = fields.get("name")
        if name is None or name == "":
            _report(path, "frontmatter missing required key: name")
        elif not isinstance(name, str):
            _report(path, f"frontmatter key 'name' must be a string "
                         f"(got {type(name).__name__}) — quote "
                         f"Norway-style scalars like 'yes' / 'no' / 'on' / "
                         f"'off' to keep them as text")
        elif not KEBAB.match(name):
            _report(path, f"name {name!r} must be kebab-case ([a-z][a-z0-9-]*)")
        elif name != expected_name:
            _report(path, f"name {name!r} does not match filename "
                         f"{expected_name!r}")
        desc = fields.get("description")
        if desc is None or desc == "":
            _report(path, "frontmatter missing required key: description")
        elif not isinstance(desc, str):
            _report(path, f"frontmatter key 'description' must be a string "
                         f"(got {type(desc).__name__}) — "
                         f"quote Norway-style scalars like 'yes' / 'no'")
        model = fields.get("model")
        if model is None or model == "":
            _report(path, "frontmatter missing required key: model "
                         "(see docs/CONVENTIONS.md#model-selection)")
        elif not isinstance(model, str):
            _report(path, f"frontmatter key 'model' must be a string "
                         f"(got {type(model).__name__}) — "
                         f"quote Norway-style scalars like 'on' / 'off'")
        unknown = set(fields) - ALLOWED_AGENT_KEYS
        if unknown:
            _report(path, f"unknown frontmatter keys: {sorted(unknown)} "
                         f"(allowed: {sorted(ALLOWED_AGENT_KEYS)})")
        if not body.strip():
            _report(path, "body is empty")
        check_links(path, body, body_start)

    def check_command(path: Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            _report(path, ferr)
            return
        if fields is not None:
            desc = fields.get("description")
            if desc is None or desc == "":
                _report(path, "frontmatter missing required key: description")
            elif not isinstance(desc, str):
                _report(path, f"frontmatter key 'description' must be a string "
                             f"(got {type(desc).__name__}) — "
                             f"quote Norway-style scalars like 'yes' / 'no'")
            unknown = set(fields) - ALLOWED_COMMAND_KEYS
            if unknown:
                _report(path, f"unknown frontmatter keys: {sorted(unknown)} "
                             f"(allowed: {sorted(ALLOWED_COMMAND_KEYS)})")
        if not body.strip():
            _report(path, "body is empty")
        check_links(path, body, body_start)

    # --- Scan .claude/ artifacts ---

    claude_dir = root / ".claude"
    if not claude_dir.exists():
        return diags

    skills_dir = claude_dir / "skills"
    agents_dir = claude_dir / "agents"
    commands_dir = claude_dir / "commands"

    if skills_dir.exists():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            check_skill(skill_md)
        for stray in sorted(skills_dir.glob("*/*.md")):
            if stray.name != "SKILL.md":
                _report(stray,
                        "unexpected file in skill dir; skill bodies must be named SKILL.md")
        for skill_dir_path in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            if not (skill_dir_path / "SKILL.md").exists():
                _report(skill_dir_path, "skill directory missing SKILL.md")

    if agents_dir.exists():
        for agent_md in sorted(agents_dir.glob("*.md")):
            if agent_md.name.upper() == "README.MD":
                continue
            check_agent(agent_md)

    if commands_dir.exists():
        for cmd_md in sorted(commands_dir.glob("*.md")):
            if cmd_md.name.upper() == "README.MD":
                continue
            check_command(cmd_md)

    return diags


def _step_marketplace(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 12: validate the configured source marketplace when it exists."""
    paths = getattr(config, "paths", None)
    marketplace = root / (
        getattr(paths, "marketplace", ".claude-plugin/marketplace.json")
        if paths
        else ".claude-plugin/marketplace.json"
    )
    marketplace_present = (
        marketplace.exists()
        or marketplace.is_symlink()
        or _path_is_junction(marketplace)
    )
    if not marketplace_present:
        return []
    try:
        content = read_confined_regular_file(root, marketplace).decode("utf-8")
        json.loads(content)
    except (UnsafeContentError, UnicodeDecodeError) as exc:
        return [
            _err(
                "CAT-V-012",
                f"marketplace.json is unsafe: {exc}",
                path=_diagnostic_path(root, marketplace),
            )
        ]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [
            _err(
                "CAT-V-012",
                f"marketplace.json parse error: {exc}",
                path=_diagnostic_path(root, marketplace),
            )
        ]
    return []


def _validate_marketplace_entries(
    payload: object,
    entry_schema: dict,
    label: str,
) -> list[Diagnostic]:
    """Validate marketplace entries shared by source and archive verification."""
    from agentbundle.build.validate import validate as validate_manifest

    if not isinstance(payload, dict):
        return [_err(
            "CAT-V-013",
            f"{label} must contain a JSON object",
            path=label,
        )]

    plugin_entries = payload.get("plugins", [])
    if not isinstance(plugin_entries, list):
        return [_err(
            "CAT-V-013",
            f"{label} 'plugins' must be a JSON array",
            path=label,
        )]

    diags: list[Diagnostic] = []
    for plugin_entry in plugin_entries:
        if not isinstance(plugin_entry, dict):
            diags.append(_err(
                "CAT-V-013",
                "marketplace plugin entry must be a JSON object",
                path=label,
            ))
            continue
        name = plugin_entry.get("name", "unknown")
        if "source" not in plugin_entry:
            # WARN, not ERROR. `[pack.links].repository` is optional, the
            # shipped scaffold pack omits it, and an external catalogue may
            # legitimately hold packs it does not publish for marketplace
            # install. Surface the consequence without failing the build.
            diags.append(_warn(
                "CAT-V-013",
                f"marketplace entry '{name}' has no 'source' — set "
                f"[pack.links].repository in that pack's pack.toml so the "
                f"build can emit one, or adopters cannot install it",
                path=label,
            ))
        if "hooks" in plugin_entry:
            diags.append(_err(
                "CAT-V-013",
                f"plugin '{name}' contains 'hooks' — "
                "hooks must not appear in marketplace entries",
                path=label,
            ))
        for error in validate_manifest(plugin_entry, entry_schema):
            diags.append(_err(
                "CAT-V-013",
                f"marketplace entry '{name}': {error}",
                path=label,
            ))
    return diags


def _step_plugin_manifests(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 13: validate generated claude-plugin manifests against schema."""
    dist_dir = tmpdir / "dist" / "claude-plugins"
    root_marketplace = root / ".claude-plugin" / "marketplace.json"
    # No early return on `dist_dir` alone: the ROOT marketplace is checked
    # independently, so gating both on a built dist tree would make the root
    # check unreachable whenever `dist/` is absent — a gate that only looks
    # like a gate.
    if not dist_dir.exists() and not root_marketplace.exists():
        return []

    try:
        from agentbundle.build.main import _read_bundled
        from agentbundle.build.validate import validate as _validate_manifest
    except ImportError:
        return []

    diags: list[Diagnostic] = []

    # Fail CLOSED on an unresolvable schema. Loading both in one `try` with a
    # bare `return []` meant a single missing file silently disabled the whole
    # step — including the plugin.json validation that already worked — and
    # `catalogue verify` still reported ok. That is the looks-like-a-gate
    # failure this spec exists to remove, so a missing schema is a diagnostic,
    # never a quiet pass.
    def _load(name: str) -> dict | None:
        try:
            return json.loads(_read_bundled(name))
        except Exception as exc:
            diags.append(_err(
                "CAT-V-013",
                f"{name} unavailable — cannot validate plugin manifests: {exc}",
            ))
            return None

    schema = _load("plugin-manifest.derived.schema.json")
    entry_schema = _load("marketplace-entry.schema.json")
    if schema is None or entry_schema is None:
        return diags

    def _check_marketplace(path: Path, label: str) -> None:
        """Validate every ``plugins[]`` entry in a marketplace file.

        Entries need their own schema: ``plugin.json`` must *not* carry
        ``source`` (``build/main.py`` pops it) while an entry must require it,
        and entries carry ``category``, which the derived schema forbids under
        ``additionalProperties: false``. Until this ran, marketplace entries
        were validated by nothing at all.
        """
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-013", f"{label} parse error: {exc}",
                              path=label))
            return
        diags.extend(_validate_marketplace_entries(payload, entry_schema, label))

    for manifest_path in sorted(dist_dir.rglob("*.claude-plugin/plugin.json")) \
            if dist_dir.exists() else []:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-013", f"plugin.json parse error: {exc}",
                              path=str(manifest_path.relative_to(tmpdir))))
            continue
        errors = _validate_manifest(manifest, schema)
        for error in errors:
            diags.append(_err("CAT-V-013", f"plugin manifest schema: {error}",
                               path=str(manifest_path.relative_to(tmpdir))))

    # Both marketplace files, not just dist: the ROOT `.claude-plugin/
    # marketplace.json` is the file `claude plugin marketplace add <owner>/<repo>`
    # actually reads, and it is written by a second writer
    # (`build/self_host.py:_aggregate_marketplace`).
    dist_marketplace = dist_dir / "marketplace.json"
    if dist_marketplace.exists():
        _check_marketplace(dist_marketplace,
                           str(dist_marketplace.relative_to(tmpdir)))

    if root_marketplace.exists():
        _check_marketplace(root_marketplace, ".claude-plugin/marketplace.json")

    return diags


def _step_output_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 14: compare configured output with a safely confined fresh build."""
    import os

    from agentbundle.catalogue_tooling.file_safety import (
        UnsafeContentError,
        sha256_confined_regular_file,
    )

    paths = getattr(config, "paths", None)
    output_dir = root / (getattr(paths, "build_output", "dist") if paths else "dist")
    if not output_dir.is_dir():
        return []
    if output_dir.is_symlink() or _path_is_junction(output_dir):
        return [
            _err(
                "CAT-V-014",
                f"refused output root {output_dir.relative_to(root).as_posix()}: link-like root",
                path=output_dir.relative_to(root).as_posix(),
            )
        ]
    fresh_dir = tmpdir / "dist"
    if not fresh_dir.is_dir():
        from agentbundle.catalogue_tooling.build import build_catalogue

        fresh_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_result = build_catalogue(root, output=fresh_dir, pack=pack)
        except Exception as exc:
            return [_err("CAT-V-014", f"fresh output build failed: {exc}")]
        if not build_result.ok:
            return [_err("CAT-V-014", "fresh output build failed")]

    diags: list[Diagnostic] = []

    projection_roots = {"claude-plugins", "apm"}

    def in_scope(relative: Path) -> bool:
        return (
            len(relative.parts) >= 2
            and relative.parts[0] in projection_roots
            and (pack is None or relative.parts[1] == pack)
        )

    def directory_may_contain_scope(relative: Path) -> bool:
        if not relative.parts:
            return True
        if relative.parts[0] not in projection_roots:
            return False
        return pack is None or len(relative.parts) < 2 or relative.parts[1] == pack

    def walk_files(tree: Path, *, source_tree: bool) -> dict[Path, Path]:
        """Return confined regular files keyed relative to *tree*."""
        files: dict[Path, Path] = {}
        if not tree.is_dir():
            return files
        try:
            canonical_tree = tree.resolve()
        except (OSError, RuntimeError) as exc:
            diags.append(_err("CAT-V-014", f"output root cannot be resolved: {exc}"))
            return files
        visited: set[Path] = set()
        for current_text, dirnames, filenames in os.walk(tree, topdown=True, followlinks=False):
            current = Path(current_text)
            try:
                resolved_current = current.resolve()
            except (OSError, RuntimeError):
                dirnames[:] = []
                continue
            if not resolved_current.is_relative_to(canonical_tree) or resolved_current in visited:
                dirnames[:] = []
                continue
            visited.add(resolved_current)
            safe_directories: list[str] = []
            for dirname in sorted(dirnames):
                child = current / dirname
                if not directory_may_contain_scope(child.relative_to(tree)):
                    continue
                rel_to_catalogue = (
                    child.relative_to(root)
                    if source_tree
                    else output_dir.relative_to(root) / child.relative_to(tree)
                )
                try:
                    unsafe_link = child.is_symlink() or _path_is_junction(child)
                    resolved_child = child.resolve()
                    unsafe_escape = not resolved_child.is_relative_to(canonical_tree)
                    repeated = resolved_child in visited
                except (OSError, RuntimeError):
                    unsafe_link = True
                    unsafe_escape = True
                    repeated = True
                if unsafe_link or unsafe_escape or repeated:
                    kind = "junction" if _path_is_junction(child) else "link or loop"
                    diags.append(
                        _err(
                            "CAT-V-014",
                            f"refused output {kind} {rel_to_catalogue.as_posix()}: "
                            "target is outside the output root or repeats a visited directory",
                            path=rel_to_catalogue.as_posix(),
                        )
                    )
                    continue
                safe_directories.append(dirname)
            dirnames[:] = safe_directories
            for filename in sorted(filenames):
                candidate = current / filename
                if not in_scope(candidate.relative_to(tree)):
                    continue
                if candidate.is_symlink() or _path_is_junction(candidate):
                    rel_to_catalogue = (
                        candidate.relative_to(root)
                        if source_tree
                        else output_dir.relative_to(root) / candidate.relative_to(tree)
                    )
                    diags.append(
                        _err(
                            "CAT-V-014",
                            f"refused output link {rel_to_catalogue.as_posix()}",
                            path=rel_to_catalogue.as_posix(),
                        )
                    )
                    continue
                try:
                    resolved_file = candidate.resolve()
                except (OSError, RuntimeError):
                    continue
                if resolved_file.is_relative_to(canonical_tree) and candidate.is_file():
                    files[candidate.relative_to(tree)] = candidate
        return files

    configured = walk_files(output_dir, source_tree=True)
    fresh = walk_files(fresh_dir, source_tree=False)

    configured = {relative: path for relative, path in configured.items() if in_scope(relative)}
    fresh = {relative: path for relative, path in fresh.items() if in_scope(relative)}
    for relative in sorted(configured.keys() | fresh.keys()):
        diagnostic_path = (output_dir.relative_to(root) / relative).as_posix()
        if relative not in fresh:
            diags.append(
                _err(
                    "CAT-V-014",
                    f"stale generated output: {diagnostic_path}",
                    path=diagnostic_path,
                )
            )
            continue
        if relative not in configured:
            diags.append(
                _err(
                    "CAT-V-014",
                    f"missing generated output: {diagnostic_path}",
                    path=diagnostic_path,
                )
            )
            continue
        try:
            configured_digest = sha256_confined_regular_file(
                output_dir, configured[relative]
            )
            fresh_digest = sha256_confined_regular_file(fresh_dir, fresh[relative])
            differs = configured_digest != fresh_digest
        except (OSError, UnsafeContentError) as exc:
            diags.append(
                _err(
                    "CAT-V-014",
                    f"cannot compare generated output {diagnostic_path}: {exc}",
                    path=diagnostic_path,
                )
            )
            continue
        if differs:
            diags.append(
                _err(
                    "CAT-V-014",
                    f"generated output differs: {diagnostic_path}",
                    path=diagnostic_path,
                )
            )
    return diags


def _step_selfhost_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 15: self-host drift check via check_self_host.

    Skips when no catalogue.toml or no self-host projection.
    """
    if config is None:
        return []
    # `.adapt-discovery.toml` is required by run_self_host (fail-fast). Its
    # absence means this catalogue has no self-host projection to drift-check.
    if not (root / ".adapt-discovery.toml").exists():
        return []
    from agentbundle.catalogue_tooling.self_host import check_self_host
    try:
        result = check_self_host(root)
    except Exception as exc:
        return [_err("CAT-V-015", f"self-host check failed: {exc}")]
    if not result.ok:
        return [_err(
            "CAT-V-015",
            "self-host projection is out of date"
            " (run 'agentbundle catalogue self-host --write')",
        )]
    return []


def _step_sync_defaults(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 16: sync-defaults check — only when install-defaults-output is configured."""
    dist_cfg = getattr(config, "distribution", None) if config else None
    ab_cfg = getattr(dist_cfg, "agentbundle", None) if dist_cfg else None
    output_path = getattr(ab_cfg, "install_defaults_output", None) if ab_cfg else None
    if not output_path:
        return []
    from agentbundle.catalogue_tooling.defaults import check_defaults
    try:
        result = check_defaults(root)
    except Exception as exc:
        return [_err("CAT-V-016", f"sync-defaults check failed: {exc}")]
    if not result.ok:
        return [_err(
            "CAT-V-016",
            "install-defaults.toml is out of date"
            " (run 'agentbundle catalogue sync-defaults --write')",
        )]
    return []


def _step_package_preflight(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 17: parse and schema-check each selected pack manifest."""
    import tomllib

    from agentbundle.build.validate import validate as validate_schema

    paths = getattr(config, "paths", None)
    packs_dir = root / (getattr(paths, "packs", "packs") if paths else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-017",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_dir),
            )
        ]
    if not packs_dir.is_dir():
        return []
    try:
        schema = _load_bundled_json("pack.schema.json")
    except (OSError, ValueError) as exc:
        return [_err("CAT-V-017", f"pack schema is unavailable: {exc}")]
    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if (
            not pack_dir.is_dir()
            or pack_dir.name.startswith("_")
            or pack_dir.is_symlink()
            or _path_is_junction(pack_dir)
            or (pack is not None and pack_dir.name != pack)
        ):
            continue
        manifest = pack_dir / "pack.toml"
        diagnostic_path = str(manifest.relative_to(root))
        if not manifest.is_file():
            diags.append(
                _err(
                    "CAT-V-017",
                    "pack.toml is missing",
                    pack=pack_dir.name,
                    path=diagnostic_path,
                )
            )
            continue
        try:
            content = read_confined_regular_file(pack_dir, manifest).decode("utf-8")
            contract = tomllib.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            diags.append(
                _err(
                    "CAT-V-017",
                    f"pack.toml parse error: {exc}",
                    pack=pack_dir.name,
                    path=diagnostic_path,
                )
            )
            continue
        for error in validate_schema(contract, schema):
            diags.append(
                _err(
                    "CAT-V-017",
                    f"pack schema: {error}",
                    pack=pack_dir.name,
                    path=diagnostic_path,
                )
            )
    return diags


def _step_fixture_checks(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 18: validate skill eval manifests without parsing opaque payloads."""
    from agentbundle.catalogue_tooling.skill_spec_lint import (
        _check_eval_queries,
        _check_evals_json,
    )

    paths = getattr(config, "paths", None)
    packs_dir = root / (getattr(paths, "packs", "packs") if paths else "packs")
    packs_present = packs_dir.exists() or packs_dir.is_symlink() or _path_is_junction(packs_dir)
    packs_issue = _confined_directory_issue(root, packs_dir) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-018",
                f"refused {packs_issue} packs directory",
                path=str(packs_dir.relative_to(root)),
            )
        ]
    if not packs_dir.is_dir():
        return []
    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if (
            not pack_dir.is_dir()
            or pack_dir.name.startswith("_")
            or pack_dir.is_symlink()
            or _path_is_junction(pack_dir)
            or (pack is not None and pack_dir.name != pack)
        ):
            continue
        try:
            canonical_pack = pack_dir.resolve(strict=True)
        except (OSError, RuntimeError):
            diags.append(
                _err(
                    "CAT-V-018",
                    "refused unresolvable pack directory",
                    pack=pack_dir.name,
                    path=str(pack_dir.relative_to(root)),
                )
            )
            continue
        apm_dir = pack_dir / ".apm"
        if apm_dir.is_symlink() or _path_is_junction(apm_dir):
            diags.append(
                _err(
                    "CAT-V-018",
                    "refused link-like .apm directory",
                    pack=pack_dir.name,
                    path=str(apm_dir.relative_to(root)),
                )
            )
            continue
        if not apm_dir.is_dir():
            continue
        apm_issue = _confined_directory_issue(canonical_pack, apm_dir)
        if apm_issue is not None:
            diags.append(
                _err(
                    "CAT-V-018",
                    f"refused {apm_issue} .apm directory",
                    pack=pack_dir.name,
                    path=str(apm_dir.relative_to(root)),
                )
            )
            continue
        skills_dir = apm_dir / "skills"
        if skills_dir.is_symlink() or _path_is_junction(skills_dir):
            diags.append(
                _err(
                    "CAT-V-018",
                    "refused link-like skills directory",
                    pack=pack_dir.name,
                    path=str(skills_dir.relative_to(root)),
                )
            )
            continue
        if not skills_dir.is_dir():
            continue
        skills_issue = _confined_directory_issue(canonical_pack, skills_dir)
        if skills_issue is not None:
            diags.append(
                _err(
                    "CAT-V-018",
                    f"refused {skills_issue} skills directory",
                    pack=pack_dir.name,
                    path=str(skills_dir.relative_to(root)),
                )
            )
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_symlink() or _path_is_junction(skill_dir):
                diags.append(
                    _err(
                        "CAT-V-018",
                        "refused link-like skill directory",
                        pack=pack_dir.name,
                        path=str(skill_dir.relative_to(root)),
                    )
                )
                continue
            if not skill_dir.is_dir():
                continue
            skill_issue = _confined_directory_issue(canonical_pack, skill_dir)
            if skill_issue is not None:
                diags.append(
                    _err(
                        "CAT-V-018",
                        f"refused {skill_issue} skill directory",
                        pack=pack_dir.name,
                        path=str(skill_dir.relative_to(root)),
                    )
                )
                continue
            evals_dir = skill_dir / "evals"
            if evals_dir.is_symlink() or _path_is_junction(evals_dir):
                diags.append(
                    _err(
                        "CAT-V-018",
                        "refused link-like evals directory",
                        pack=pack_dir.name,
                        path=str(evals_dir.relative_to(root)),
                    )
                )
                continue
            if not evals_dir.is_dir():
                continue
            evals_issue = _confined_directory_issue(canonical_pack, evals_dir)
            if evals_issue is not None:
                diags.append(
                    _err(
                        "CAT-V-018",
                        f"refused {evals_issue} evals directory",
                        pack=pack_dir.name,
                        path=str(evals_dir.relative_to(root)),
                    )
                )
                continue
            manifests = (
                (evals_dir / "evals.json", "evals"),
                (evals_dir / "eval_queries.json", "queries"),
            )
            for manifest, manifest_kind in manifests:
                if manifest.is_symlink() or _path_is_junction(manifest):
                    diags.append(
                        _err(
                            "CAT-V-018",
                            "refused link-like eval manifest",
                            pack=pack_dir.name,
                            path=str(manifest.relative_to(root)),
                        )
                    )
                    continue
                try:
                    manifest.lstat()
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    diags.append(
                        _err(
                            "CAT-V-018",
                            f"eval manifest cannot be inspected safely: {exc}",
                            pack=pack_dir.name,
                            path=str(manifest.relative_to(root)),
                        )
                    )
                    continue
                try:
                    content = read_confined_regular_file(pack_dir, manifest).decode("utf-8")
                except (UnsafeContentError, UnicodeDecodeError) as exc:
                    diags.append(
                        _err(
                            "CAT-V-018",
                            f"refused unsafe eval manifest: {exc}",
                            pack=pack_dir.name,
                            path=str(manifest.relative_to(root)),
                        )
                    )
                    continue
                if manifest_kind == "evals":
                    messages = _check_evals_json(
                        skill_dir,
                        manifest,
                        skill_dir.name,
                        content=content,
                    )
                else:
                    messages = _check_eval_queries(manifest, content=content)
                for message in messages:
                    diags.append(
                        _err(
                            "CAT-V-018",
                            message,
                            pack=pack_dir.name,
                            path=str(manifest.relative_to(root)),
                        )
                    )
    return diags


# ---------------------------------------------------------------------------
# Step 19 helpers
# ---------------------------------------------------------------------------

_SEMVER_ATOM_RE = re.compile(
    r"^(?:[~^]|[<>]=?)?(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)(?:-[\w.]+)?)?)?$"
)
_SEMVER_HYPHEN_RE = re.compile(r"^\d[\d.]* - \d[\d.]*$")


def _is_valid_semver_range(version: str) -> bool:
    """Return True if *version* is a valid npm-compatible semver range.

    Handles: exact versions, caret/tilde/comparison prefixes, hyphen ranges,
    and ``||`` unions. No new dependencies — pure regex.
    """
    for part in version.split("||"):
        part = part.strip()
        if not part:
            return False
        if _SEMVER_HYPHEN_RE.match(part):
            continue
        for atom in part.split():
            if not _SEMVER_ATOM_RE.match(atom):
                return False
    return True


def _resolve_primitive_ref(ref: object, pack_dir: Path) -> tuple[bool, str | None]:
    """Resolve a type-qualified primitive ref without following link-like paths.

    Mapping:
      skill:<name>   → directory  pack_dir/.apm/skills/<name>/
      agent:<name>   → file       pack_dir/.apm/agents/<name>.md
      command:<name> → file       pack_dir/.apm/commands/<name>.md
      hook:<name>    → any file   pack_dir/.apm/hooks/<name>.*  (stem match)
    """
    if not isinstance(ref, str) or ":" not in ref:
        return False, "reference must be a type-qualified string"
    type_str, name = ref.split(":", 1)
    if not _PACK_SLUG_RE.fullmatch(name):
        return False, "primitive name must use the canonical lowercase slug grammar"

    def real_directory(path: Path) -> tuple[bool, str | None]:
        try:
            relative = path.relative_to(pack_dir)
        except ValueError:
            return False, "primitive path escapes its pack"
        current = pack_dir
        for component in relative.parts:
            current /= component
            if not current.is_dir():
                return False, "primitive directory not found"
            issue = _confined_directory_issue(pack_dir, current)
            if issue is not None:
                return False, f"refused {issue} primitive directory"
        return True, None

    def regular_file(path: Path) -> tuple[bool, str | None]:
        if not (path.exists() or path.is_symlink() or _path_is_junction(path)):
            return False, "primitive file not found"
        parent_ok, parent_reason = real_directory(path.parent)
        if not parent_ok:
            return False, parent_reason
        try:
            read_confined_regular_file(pack_dir, path)
        except UnsafeContentError as exc:
            return False, f"refused unsafe primitive file: {exc}"
        return True, None

    if type_str == "skill":
        return real_directory(pack_dir / ".apm" / "skills" / name)
    if type_str == "agent":
        return regular_file(pack_dir / ".apm" / "agents" / f"{name}.md")
    if type_str == "command":
        return regular_file(pack_dir / ".apm" / "commands" / f"{name}.md")
    if type_str == "hook":
        hooks_dir = pack_dir / ".apm" / "hooks"
        hooks_ok, hooks_reason = real_directory(hooks_dir)
        if not hooks_ok:
            return False, hooks_reason
        unsafe_reason: str | None = None
        for candidate in sorted(hooks_dir.iterdir()):
            if candidate.stem != name:
                continue
            candidate_ok, candidate_reason = regular_file(candidate)
            if candidate_ok:
                return True, None
            unsafe_reason = candidate_reason
        return False, unsafe_reason or "primitive hook not found"
    return False, f"unsupported primitive type {type_str!r}"


def _step_integration_validation(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 19: validate [[pack.integrations]] entries (Wave 2).

    Rules checked (schema-layer rules are NOT re-implemented here):
      - id is unique within each declaring pack
      - consumer primitive refs resolve in the declaring pack
      - a pack does not target itself
      - version, when present, is a valid semver range
      - an absent target pack is not an error (portable across catalogues)
      - provider primitive refs resolve in the target pack when present
    """
    import tomllib

    packs_path = getattr(getattr(config, "paths", None), "packs", None) or "packs"
    packs_root = root / packs_path
    packs_present = (
        packs_root.exists()
        or packs_root.is_symlink()
        or _path_is_junction(packs_root)
    )
    packs_issue = _confined_directory_issue(root, packs_root) if packs_present else None
    if packs_issue is not None:
        return [
            _err(
                "CAT-V-019",
                f"refused {packs_issue} packs directory",
                path=_diagnostic_path(root, packs_root),
            )
        ]
    if not packs_root.is_dir():
        return []

    diags: list[Diagnostic] = []
    scan_diags: list[Diagnostic] = []

    # Pass 1: build full pack-name → pack-dir map (cross-reference)
    all_packs: dict[str, tuple[Path, dict]] = {}
    for candidate in sorted(packs_root.iterdir()):
        if candidate.name.startswith("_"):
            continue
        if candidate.is_symlink() or _path_is_junction(candidate):
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    "refused link-like pack directory",
                    pack=candidate.name,
                    path=_diagnostic_path(root, candidate),
                )
            )
            continue
        if not candidate.is_dir():
            continue
        candidate_issue = _confined_directory_issue(packs_root, candidate)
        if candidate_issue is not None:
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    f"refused {candidate_issue} pack directory",
                    pack=candidate.name,
                    path=_diagnostic_path(root, candidate),
                )
            )
            continue
        toml_path = candidate / "pack.toml"
        if not (
            toml_path.exists()
            or toml_path.is_symlink()
            or _path_is_junction(toml_path)
        ):
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    "pack.toml is missing; integrations cannot be validated",
                    pack=candidate.name,
                    path=_diagnostic_path(root, toml_path),
                )
            )
            continue
        try:
            content = read_confined_regular_file(candidate, toml_path).decode("utf-8")
            data = tomllib.loads(content)
        except (UnsafeContentError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    f"pack.toml cannot be read safely: {exc}",
                    pack=candidate.name,
                    path=_diagnostic_path(root, toml_path),
                )
            )
            continue
        pack_table = data.get("pack", {})
        if not isinstance(pack_table, dict):
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    "pack must be a table",
                    pack=candidate.name,
                    path=_diagnostic_path(root, toml_path),
                )
            )
            continue
        pack_name = pack_table.get("name") or candidate.name
        if not isinstance(pack_name, str):
            scan_diags.append(
                _err(
                    "CAT-V-019",
                    "pack name must be a string",
                    pack=candidate.name,
                    path=_diagnostic_path(root, toml_path),
                )
            )
            continue
        all_packs[pack_name] = (candidate, data)

    relevant_packs: set[str] | None = None
    if pack is not None:
        relevant_packs = {pack}
        selected = all_packs.get(pack)
        if selected is not None:
            _selected_dir, selected_data = selected
            selected_table = selected_data.get("pack", {})
            if isinstance(selected_table, dict):
                selected_integrations = selected_table.get("integrations") or []
                if isinstance(selected_integrations, list):
                    for entry in selected_integrations:
                        if not isinstance(entry, dict):
                            continue
                        target = entry.get("pack")
                        if isinstance(target, str):
                            relevant_packs.add(target)
    diags.extend(
        diagnostic
        for diagnostic in scan_diags
        if relevant_packs is None or diagnostic.pack in relevant_packs
    )

    # Pass 2: validate integrations in each (optionally filtered) pack
    for pack_name, (pack_dir, data) in all_packs.items():
        if pack is not None and pack_name != pack:
            continue
        pack_table = data.get("pack", {})
        if not isinstance(pack_table, dict):
            continue  # rejected while building all_packs above
        integrations = pack_table.get("integrations") or []
        if not integrations:
            continue
        if not isinstance(integrations, list):
            diags.append(
                _err(
                    "CAT-V-019",
                    "pack.integrations must be an array of tables",
                    pack=pack_name,
                )
            )
            continue

        seen_ids: set[str] = set()  # reset per declaring pack (scopes to pack)
        for integration_index, entry in enumerate(integrations):
            if not isinstance(entry, dict):
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration at index {integration_index} must be a table",
                        pack=pack_name,
                    )
                )
                continue
            entry_id = entry.get("id", "")
            if not isinstance(entry_id, str):
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration at index {integration_index} has a non-string id",
                        pack=pack_name,
                    )
                )
                continue

            # Duplicate id within this pack
            if entry_id in seen_ids:
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"duplicate integration id {entry_id!r} in pack {pack_name!r}",
                        pack=pack_name,
                    )
                )
            seen_ids.add(entry_id)

            # Consumer refs must resolve in declaring pack
            consumers = entry.get("consumers", [])
            if not isinstance(consumers, list):
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration {entry_id!r}: consumers must be an array",
                        pack=pack_name,
                    )
                )
                consumers = []
            for ref in consumers:
                resolved, reason = _resolve_primitive_ref(ref, pack_dir)
                if not resolved:
                    diags.append(
                        _err(
                            "CAT-V-019",
                            f"integration {entry_id!r}: consumer ref {ref!r} "
                            f"is invalid in {pack_name!r}: {reason}",
                            pack=pack_name,
                        )
                    )

            # No self-targeting
            target = entry.get("pack", "")
            if not isinstance(target, str):
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration {entry_id!r}: target pack must be a string",
                        pack=pack_name,
                    )
                )
                target = ""
            if target == pack_name:
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration {entry_id!r}: pack {pack_name!r} targets itself"
                        " (self-reference not allowed)",
                        pack=pack_name,
                    )
                )

            # Version, if present, must be a valid semver range
            version = entry.get("version")
            if version is not None and (
                not isinstance(version, str) or not _is_valid_semver_range(version)
            ):
                diags.append(
                    _err(
                        "CAT-V-019",
                        f"integration {entry_id!r}: version range {version!r} is not"
                        " a valid semver range",
                        pack=pack_name,
                    )
                )

            # If target is in this catalogue, check provider refs
            if target in all_packs:
                target_dir, _target_data = all_packs[target]
                providers = entry.get("providers", [])
                if not isinstance(providers, list):
                    diags.append(
                        _err(
                            "CAT-V-019",
                            f"integration {entry_id!r}: providers must be an array",
                            pack=pack_name,
                        )
                    )
                    providers = []
                for ref in providers:
                    resolved, reason = _resolve_primitive_ref(ref, target_dir)
                    if not resolved:
                        diags.append(
                            _err(
                                "CAT-V-019",
                                f"integration {entry_id!r}: provider ref {ref!r} is invalid"
                                f" in target pack {target!r}: {reason}",
                                pack=pack_name,
                            )
                        )
            # Target absent → no error (portable across catalogues)

    return diags


# ---------------------------------------------------------------------------
# 19-step verification table
# ---------------------------------------------------------------------------

_VERIFY_STEPS = [
    (1, "catalogue.toml validation", _step_config_validation),
    (2, "catalogue lint", _step_lint),
    (3, "pack schema validation", _step_pack_schema),
    (4, "plugin manifest validation", _step_plugin_validation),
    (5, "pack/plugin version parity", _step_version_parity),
    (6, "profile schema + pack refs", _step_profiles),
    (7, "dependency reference validation", _step_dependencies),
    (8, "adapter contract compatibility", _step_adapter_compat),
    (9, "primitive layout validation", _step_primitive_layout),
    (10, "build output validation (tmpdir)", _step_build_output),
    (11, "agent artifact lint", _step_agent_artifacts),
    (12, "marketplace aggregation", _step_marketplace),
    (13, "plugin manifest schema validation", _step_plugin_manifests),
    (14, "generated output drift checks", _step_output_drift),
    (15, "self-host drift checks", _step_selfhost_drift),
    (16, "sync-defaults check", _step_sync_defaults),
    (17, "package preflight", _step_package_preflight),
    (18, "deterministic fixture checks", _step_fixture_checks),
    (19, "pack integration validation", _step_integration_validation),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_catalogue(
    root: Path,
    pack: str | None = None,
    continue_on_error: bool = False,
) -> VerifyResult:
    """Verify a catalogue at *root* against its contracts.

    Runs the 19-step verification sequence defined by the catalogue contract.
    Stops at first step failure unless ``continue_on_error=True``.
    Build output (step 10) goes to a temporary directory; the catalogue
    root has zero new or modified files after verify completes.
    """
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    try:
        config = load_catalogue_config(root)
    except CatalogueConfigError:
        return VerifyResult(
            ok=False,
            diagnostics=[
                _err("CAT-V-001", "catalogue.toml is invalid", path="catalogue.toml")
            ],
            schema_version=1,
            command="catalogue verify",
            operation="source-checkout",
            agentbundle_version=_get_agentbundle_version(),
            catalogue_schema_version=1,
        )
    catalogue_schema_version = getattr(config, "schema", 1) if config else 1

    all_diags: list[Diagnostic] = []

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        for _step_num, _step_name, step_fn in _VERIFY_STEPS:
            try:
                step_diags = step_fn(root, config, pack, tmpdir)
            except Exception as exc:
                step_diags = [_err(
                    f"CAT-V-{_step_num:03d}",
                    f"step {_step_num} ({_step_name}) raised unexpected error: {exc}",
                )]
            all_diags.extend(step_diags)
            if any(d.severity == Severity.ERROR for d in step_diags) and not continue_on_error:
                break

    return VerifyResult(
        ok=not any(d.severity == Severity.ERROR for d in all_diags),
        diagnostics=all_diags,
        schema_version=1,
        command="catalogue verify",
        operation="source-checkout",
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=catalogue_schema_version,
    )


def render_json(result: VerifyResult) -> str:
    """Render a VerifyResult as a JSON string (deterministic)."""
    import dataclasses
    doc = {
        "schema_version": result.schema_version,
        "command": result.command,
        "operation": result.operation,
        "agentbundle_version": result.agentbundle_version,
        "catalogue_schema_version": result.catalogue_schema_version,
        "ok": result.ok,
        "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
    }
    return json.dumps(doc, sort_keys=True, indent=2)


def render_table(result: VerifyResult) -> str:
    """Render a VerifyResult as a human-readable table string."""
    if not result.diagnostics:
        return "catalogue verify: ok"
    lines: list[str] = []
    for d in result.diagnostics:
        sev = d.severity.name
        loc = d.path or ""
        pack = d.pack or ""
        lines.append(f"[{sev}] {d.code}  {pack}  {loc}  {d.message}")
    return "\n".join(lines)
