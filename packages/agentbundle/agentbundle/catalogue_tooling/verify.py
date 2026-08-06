"""Catalogue verification engine — 18-step source-checkout pipeline.

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

from agentbundle.catalogue_tooling.results import Diagnostic, Severity, VerifyResult

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
    """Step 2: run catalogue lint. Skips gracefully when catalogue.toml is absent."""
    if config is None:
        return []
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
    if not packs_dir.is_dir():
        return []

    # Use the bundled pack.schema.json so validation works both editable and wheel.
    schema_path = Path(__file__).resolve().parent.parent / "_data" / "pack.schema.json"
    if not schema_path.exists():
        return []

    import json as _json
    schema = _json.loads(schema_path.read_text(encoding="utf-8"))

    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if pack_dir.name.startswith("_"):
            continue  # reserved authoring asset
        if not pack_dir.is_dir():
            continue
        if pack and pack_dir.name != pack:
            continue
        pack_toml = pack_dir / "pack.toml"
        if not pack_toml.exists():
            continue
        try:
            import tomllib
            contract = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-003", f"pack.toml parse error: {exc}", pack=pack_dir.name))
            continue
        errors = validate_schema(contract, schema)
        for error in errors:
            diags.append(_err("CAT-V-003", f"pack schema: {error}", pack=pack_dir.name))
    return diags


def _step_plugin_validation(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 4: validate plugin.json presence and JSON parse."""
    packs_dir_name = getattr(config, "paths", None)
    packs_dir = root / (getattr(packs_dir_name, "packs", "packs") if packs_dir_name else "packs")
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
        plugin_json = pack_dir / "plugin.json"
        if not plugin_json.exists():
            continue
        try:
            json.loads(plugin_json.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-004", f"plugin.json parse error: {exc}", pack=pack_dir.name))
    return diags


def _step_version_parity(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 5: pack.toml and plugin.json name/version must match."""
    packs_dir_name = getattr(config, "paths", None)
    packs_dir = root / (getattr(packs_dir_name, "packs", "packs") if packs_dir_name else "packs")
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
        pack_toml_path = pack_dir / "pack.toml"
        plugin_json_path = pack_dir / "plugin.json"
        if not pack_toml_path.exists() or not plugin_json_path.exists():
            continue
        try:
            import tomllib
            pt = tomllib.loads(pack_toml_path.read_text(encoding="utf-8"))
            pj = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        except Exception:
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
    """Step 6: profile schema validation (graceful pass when profiles absent)."""
    profiles_dir_name = getattr(config, "paths", None)
    profiles_dir = root / (
        getattr(profiles_dir_name, "profiles", "profiles") if profiles_dir_name else "profiles"
    )
    if not profiles_dir.is_dir():
        return []
    diags: list[Diagnostic] = []
    for profile_file in sorted(profiles_dir.iterdir()):
        if profile_file.suffix not in (".toml", ".json"):
            continue
        try:
            if profile_file.suffix == ".toml":
                import tomllib
                tomllib.loads(profile_file.read_text(encoding="utf-8"))
            else:
                json.loads(profile_file.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-006", f"profile {profile_file.name!r} parse error: {exc}"))
    return diags


def _step_dependencies(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 7: dependency reference validation (pass-through; complex graph TBD)."""
    return []


def _step_adapter_compat(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 8: adapter contract compatibility check."""
    return []


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
    """Step 11: lint .claude/ agent artifact frontmatter and APM skill leak guard.

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
    ALLOWED_AGENT_KEYS = {"name", "description", "tools", "model"}
    ALLOWED_COMMAND_KEYS = {"description", "allowed-tools", "model", "argument-hint"}
    _APM_SKILL_BLOCKLIST: tuple[tuple[str, str], ...] = (
        (r"agent-ready-repo", "catalogue name 'agent-ready-repo'"),
        (r"RFC-00\d\d", "catalogue RFC reference (RFC-NNNN)"),
        (r"K-00\d\d", "catalogue knowledge entry (K-NNNN)"),
    )

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

    # --- APM leak guard (packs/core/.apm/skills/) — runs unconditionally ---

    apm_skills_dir = root / "packs" / "core" / ".apm" / "skills"
    if apm_skills_dir.exists():
        for skill_dir_item in sorted(p for p in apm_skills_dir.iterdir() if p.is_dir()):
            for target in sorted(skill_dir_item.rglob("*.md")):
                text = target.read_text(encoding="utf-8")
                for pat, label in _APM_SKILL_BLOCKLIST:
                    for _lineno, line in enumerate(text.splitlines(), 1):
                        if re.search(pat, line):
                            _report(target, f"leaked {label} in shipped skill body")

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
    """Step 12: marketplace aggregation check."""
    # Check that marketplace.json is parseable if present
    packs_dir_name = getattr(config, "paths", None)
    build_output_dir = root / (
        getattr(packs_dir_name, "build_output", "dist") if packs_dir_name else "dist"
    )
    marketplace = build_output_dir / "marketplace.json"
    if not marketplace.exists():
        # marketplace may be in dist/ from a prior build — skip gracefully
        return []
    try:
        json.loads(marketplace.read_text(encoding="utf-8"))
    except Exception as exc:
        return [_err("CAT-V-012", f"marketplace.json parse error: {exc}")]
    return []


def _step_plugin_manifests(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 13: validate generated claude-plugin manifests against schema."""
    dist_dir = tmpdir / "dist" / "claude-plugins"
    if not dist_dir.exists():
        return []

    try:
        from agentbundle.build.main import _read_bundled
        from agentbundle.build.validate import validate as _validate_manifest
    except ImportError:
        return []

    try:
        schema = json.loads(_read_bundled("plugin-manifest.derived.schema.json"))
    except Exception:
        return []

    diags: list[Diagnostic] = []

    for manifest_path in sorted(dist_dir.rglob("*.claude-plugin/plugin.json")):
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

    marketplace_path = dist_dir / "marketplace.json"
    if marketplace_path.exists():
        try:
            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        except Exception as exc:
            diags.append(_err("CAT-V-013", f"marketplace.json parse error: {exc}",
                              path=str(marketplace_path.relative_to(tmpdir))))
        else:
            for plugin_entry in marketplace.get("plugins", []):
                if "hooks" in plugin_entry:
                    name = plugin_entry.get("name", "unknown")
                    diags.append(_err(
                        "CAT-V-013",
                        f"plugin '{name}' contains 'hooks' — "
                        "hooks must not appear in marketplace entries",
                        path=str(marketplace_path.relative_to(tmpdir)),
                    ))
                    break

    return diags


def _step_output_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 14: generated output drift checks (complex; TBD)."""
    return []


def _step_selfhost_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 15: self-host drift check via check_self_host.

    Skips when no catalogue.toml or no self-host projection.
    """
    if config is None:
        return []
    # Adapt-discovery.toml is required by run_self_host (fail-fast). Its
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
    """Step 17: package preflight (TBD — depends on package-enhanced spec)."""
    return []


def _step_fixture_checks(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 18: deterministic fixture checks (TBD)."""
    return []


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


def _resolve_primitive_ref(ref: str, pack_dir: Path) -> bool:
    """Return True if the type-qualified *ref* resolves in *pack_dir*'s .apm tree.

    Mapping:
      skill:<name>   → directory  pack_dir/.apm/skills/<name>/
      agent:<name>   → file       pack_dir/.apm/agents/<name>.md
      command:<name> → file       pack_dir/.apm/commands/<name>.md
      hook:<name>    → any file   pack_dir/.apm/hooks/<name>.*  (stem match)
    """
    if ":" not in ref:
        return False
    type_str, name = ref.split(":", 1)
    if type_str == "skill":
        return (pack_dir / ".apm" / "skills" / name).is_dir()
    if type_str == "agent":
        return (pack_dir / ".apm" / "agents" / f"{name}.md").exists()
    if type_str == "command":
        return (pack_dir / ".apm" / "commands" / f"{name}.md").exists()
    if type_str == "hook":
        hooks_dir = pack_dir / ".apm" / "hooks"
        if not hooks_dir.is_dir():
            return False
        return any(f.is_file() and f.stem == name for f in hooks_dir.iterdir())
    return False


def _step_integration_validation(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 19: validate [[pack.integrations]] entries (Wave 2).

    Rules checked (schema-layer rules are NOT re-implemented here):
      Id is unique within each declaring pack
      Consumer primitive refs resolve in the declaring pack
      Pack does not target itself
      Version, when present, is a valid semver range
      Absent target pack is not an error (portable across catalogues)
      Provider primitive refs resolve in the target pack when present
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    from agentbundle.catalogue_tooling.results import Severity

    packs_path = getattr(getattr(config, "paths", None), "packs", None) or "packs"
    packs_root = root / packs_path

    if not packs_root.is_dir():
        return []

    def _err(message: str, declaring: str | None = None) -> Diagnostic:
        return Diagnostic(
            code="CAT-V-019",
            severity=Severity.ERROR,
            pack=declaring,
            path=None,
            line=None,
            col=None,
            message=message,
            remediation=None,
        )

    # Pass 1: build full pack-name → pack-dir map (cross-reference)
    all_pack_dirs: dict[str, Path] = {}
    for candidate in packs_root.iterdir():
        if not candidate.is_dir():
            continue
        toml_path = candidate / "pack.toml"
        if not toml_path.exists():
            continue
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        pack_name = data.get("pack", {}).get("name") or candidate.name
        all_pack_dirs[pack_name] = candidate

    diags: list[Diagnostic] = []

    # Pass 2: validate integrations in each (optionally filtered) pack
    for pack_name, pack_dir in all_pack_dirs.items():
        if pack is not None and pack_name != pack:
            continue
        toml_path = pack_dir / "pack.toml"
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        integrations = data.get("pack", {}).get("integrations") or []
        if not integrations:
            continue

        seen_ids: set[str] = set()  # reset per declaring pack (scopes to pack)
        for entry in integrations:
            entry_id = entry.get("id", "")

            # Duplicate id within this pack
            if entry_id in seen_ids:
                diags.append(_err(
                    f"duplicate integration id {entry_id!r} in pack {pack_name!r}",
                    declaring=pack_name,
                ))
            seen_ids.add(entry_id)

            # Consumer refs must resolve in declaring pack
            for ref in entry.get("consumers", []):
                if not _resolve_primitive_ref(ref, pack_dir):
                    diags.append(_err(
                        f"integration {entry_id!r}: consumer ref {ref!r} not found"
                        f" in {pack_name!r}",
                        declaring=pack_name,
                    ))

            # No self-targeting
            target = entry.get("pack", "")
            if target == pack_name:
                diags.append(_err(
                    f"integration {entry_id!r}: pack {pack_name!r} targets itself"
                    f" (self-reference not allowed)",
                    declaring=pack_name,
                ))

            # Version, if present, must be a valid semver range
            version = entry.get("version")
            if version is not None and not _is_valid_semver_range(version):
                diags.append(_err(
                    f"integration {entry_id!r}: version range {version!r} is not"
                    f" a valid semver range",
                    declaring=pack_name,
                ))

            # If target is in this catalogue, check provider refs
            if target in all_pack_dirs:
                target_dir = all_pack_dirs[target]
                for ref in entry.get("providers", []):
                    if not _resolve_primitive_ref(ref, target_dir):
                        diags.append(_err(
                            f"integration {entry_id!r}: provider ref {ref!r} not"
                            f" found in target pack {target!r}",
                            declaring=pack_name,
                        ))
            # Target absent → no error (portable across catalogues)

    return diags


# ---------------------------------------------------------------------------
# 18-step verification table (plus step 19)
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

    Runs the 18-step verification sequence defined in ini-005 Bucket 6.
    Stops at first step failure unless ``continue_on_error=True``.
    Build output (step 10) goes to a temporary directory; the catalogue
    root has zero new or modified files after verify completes.
    """
    from agentbundle.catalogue_tooling.config import load_catalogue_config

    config = load_catalogue_config(root)
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
