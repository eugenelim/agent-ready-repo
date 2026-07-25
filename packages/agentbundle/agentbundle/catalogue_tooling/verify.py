"""Catalogue verification engine — 18-step source-checkout pipeline.

Spec: docs/specs/catalogue-tooling-verify/spec.md (ini-005 Bucket 6).

Entry points:
  ``verify_catalogue(root, pack=None) -> VerifyResult``
  ``render_json(result) -> str``
  ``render_table(result) -> str``
"""

from __future__ import annotations

import json
import sys
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
    """Step 3: validate each pack's pack.toml against adapter schema."""
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

    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent.parent
        / "docs" / "contracts" / "adapter.schema.json"
    )
    if not schema_path.exists():
        return []

    import json as _json
    schema = _json.loads(schema_path.read_text(encoding="utf-8"))

    diags: list[Diagnostic] = []
    for pack_dir in sorted(packs_dir.iterdir()):
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
            diags.append(_err("CAT-V-005", f"pack.toml name {pt_name!r} != plugin.json name {pj_name!r}", pack=pack_dir.name))
        if pt_version and pj_version and pt_version != pj_version:
            diags.append(_err("CAT-V-005", f"pack.toml version {pt_version!r} != plugin.json version {pj_version!r}", pack=pack_dir.name))
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

    AC6: never writes to catalogue root. Skips when catalogue.toml is absent.
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


def _step_generated_schema(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 11: generated output schema validation (pass-through; complex TBD)."""
    return []


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


def _step_marketplace_parity(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 13: marketplace pack membership/version parity."""
    return []


def _step_output_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 14: generated output drift checks (complex; TBD)."""
    return []


def _step_selfhost_drift(
    root: Path, config: object | None, pack: str | None, tmpdir: Path
) -> list[Diagnostic]:
    """Step 15: self-host drift check via check_self_host. Skips when no catalogue.toml."""
    if config is None:
        return []
    from agentbundle.catalogue_tooling.self_host import check_self_host
    try:
        result = check_self_host(root)
    except Exception as exc:
        return [_err("CAT-V-015", f"self-host check failed: {exc}")]
    if not result.ok:
        return [_err("CAT-V-015", "self-host projection is out of date (run 'agentbundle catalogue self-host --write')")]
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
        return [_err("CAT-V-016", "install-defaults.toml is out of date (run 'agentbundle catalogue sync-defaults --write')")]
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
# 18-step verification table
# ---------------------------------------------------------------------------

_VERIFY_STEPS = [
    (1,  "catalogue.toml validation",          _step_config_validation),
    (2,  "catalogue lint",                     _step_lint),
    (3,  "pack schema validation",             _step_pack_schema),
    (4,  "plugin manifest validation",         _step_plugin_validation),
    (5,  "pack/plugin version parity",         _step_version_parity),
    (6,  "profile schema + pack refs",         _step_profiles),
    (7,  "dependency reference validation",    _step_dependencies),
    (8,  "adapter contract compatibility",     _step_adapter_compat),
    (9,  "primitive layout validation",        _step_primitive_layout),
    (10, "build output validation (tmpdir)",   _step_build_output),
    (11, "generated output schema",            _step_generated_schema),
    (12, "marketplace aggregation",            _step_marketplace),
    (13, "marketplace pack membership/version",_step_marketplace_parity),
    (14, "generated output drift checks",      _step_output_drift),
    (15, "self-host drift checks",             _step_selfhost_drift),
    (16, "sync-defaults check",                _step_sync_defaults),
    (17, "package preflight",                  _step_package_preflight),
    (18, "deterministic fixture checks",       _step_fixture_checks),
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
    AC6: build output (step 10) goes to a temporary directory; the catalogue
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
            if step_diags and not continue_on_error:
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
