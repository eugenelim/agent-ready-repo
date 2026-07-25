"""Portable catalogue lint engine.

Spec: docs/specs/catalogue-tooling-lint/spec.md (ini-005 Bucket 5).

Entry point: lint_catalogue(root, pack=None) -> LintResult

Rules split into three tiers:
  - Catalogue-level (_CatalogueRules): presence, duplicates, config paths
  - Pack-level (_PackRules): per-pack TOML/JSON/frontmatter/metadata checks
  - Portability (via lint_packs.lint_pack): symlinks, Windows-poisonous names

All rules are read-only. No file is written during a lint run.
Output sorted by (pack, path, line, col, code).
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import asdict
from pathlib import Path

from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config
from agentbundle.catalogue_tooling.diagnostics import DiagnosticCode
from agentbundle.catalogue_tooling.results import Diagnostic, LintResult, Severity

# Frontmatter regex: matches the YAML front-matter block at the top of a file
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Required SKILL.md frontmatter keys
_SKILL_REQUIRED_KEYS = ("name", "description")

# Agent frontmatter required keys
_AGENT_REQUIRED_KEYS = ("name", "description")

# Adapter names cache
_ADAPTER_NAMES: frozenset[str] | None = None

# Allowed scope values per adapter contract
_ALLOWED_SCOPES = frozenset({"repo", "user"})

# Max lengths from lint_packs
_MAX_NAME_LEN = 64
_MAX_DESC_LEN = 1024

# Primitive name pattern
_PRIM_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

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


def _get_adapter_names() -> frozenset[str]:
    global _ADAPTER_NAMES
    if _ADAPTER_NAMES is None:
        try:
            from agentbundle.catalogue_tooling.config import _load_adapter_names
            _ADAPTER_NAMES = _load_adapter_names()
        except Exception:
            _ADAPTER_NAMES = frozenset()
    return _ADAPTER_NAMES


def _diag(
    code: DiagnosticCode,
    severity: Severity,
    message: str,
    *,
    pack: str | None = None,
    path: str | None = None,
    line: int | None = None,
    col: int | None = None,
    remediation: str | None = None,
) -> Diagnostic:
    return Diagnostic(
        code=code.value,
        severity=severity,
        pack=pack,
        path=path,
        line=line,
        col=col,
        message=message,
        remediation=remediation,
    )


def _sort_key(d: Diagnostic) -> tuple:
    return (d.pack or "", d.path or "", d.line or 0, d.col or 0, d.code)


def _load_pack_schema() -> dict | None:
    try:
        from importlib.resources import files
        resource = files("agentbundle").joinpath("_data/pack.schema.json")
        if resource.is_file():
            return json.loads(resource.read_text(encoding="utf-8"))
    except Exception:
        pass
    here = Path(__file__).resolve()
    schema_path = here.parents[1] / "_data" / "pack.schema.json"
    if schema_path.exists():
        try:
            return json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse YAML-style frontmatter from a markdown file. Returns None if absent."""
    m = _FM_RE.match(text)
    if not m:
        return None
    fields: dict[str, str] = {}
    for raw_line in m.group(1).splitlines():
        if ":" in raw_line:
            k, _, v = raw_line.partition(":")
            fields[k.strip()] = v.strip()
    return fields


# ---------------------------------------------------------------------------
# Catalogue-level rules
# ---------------------------------------------------------------------------


class _CatalogueRules:
    def __init__(self, root: Path, config: object | None) -> None:
        self._root = root
        self._config = config

    def collect(self, pack_filter: str | None) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        diagnostics.extend(self._check_markers())
        diagnostics.extend(self._check_duplicate_identities())
        diagnostics.extend(self._check_config_paths())
        return diagnostics

    def _packs_dir(self) -> Path:
        if self._config is not None:
            return self._root / self._config.paths.packs  # type: ignore[attr-defined]
        return self._root / "packs"

    def _marketplace_path(self) -> Path:
        if self._config is not None:
            return self._root / self._config.paths.marketplace  # type: ignore[attr-defined]
        return self._root / ".claude-plugin" / "marketplace.json"

    def _check_markers(self) -> list[Diagnostic]:
        diags: list[Diagnostic] = []
        packs_dir = self._packs_dir()
        if not packs_dir.is_dir():
            diags.append(_diag(
                DiagnosticCode.CAT_L002,
                Severity.ERROR,
                f"packs directory missing: {packs_dir}",
                remediation="Create the packs directory or update catalogue.toml paths.packs.",
            ))
        mp = self._marketplace_path()
        if not mp.exists():
            diags.append(_diag(
                DiagnosticCode.CAT_L002,
                Severity.ERROR,
                f"marketplace.json missing: {mp}",
                remediation="Run 'make build-self' or 'agentbundle catalogue self-host --write'.",
            ))
        return diags

    def _check_duplicate_identities(self) -> list[Diagnostic]:
        packs_dir = self._packs_dir()
        if not packs_dir.is_dir():
            return []
        seen_names: dict[str, str] = {}
        diags: list[Diagnostic] = []
        for entry in sorted(packs_dir.iterdir()):
            if not entry.is_dir() or not (entry / "pack.toml").exists():
                continue
            try:
                data = tomllib.loads((entry / "pack.toml").read_text(encoding="utf-8"))
                pack_name = data.get("pack", {}).get("name", "")
            except Exception:
                continue
            if pack_name in seen_names:
                diags.append(_diag(
                    DiagnosticCode.CAT_L003,
                    Severity.ERROR,
                    f"duplicate pack identity {pack_name!r}: found in {seen_names[pack_name]!r} and {entry.name!r}",
                    pack=entry.name,
                    remediation="Each pack must have a unique [pack].name.",
                ))
            else:
                seen_names[pack_name] = entry.name
        return diags

    def _check_config_paths(self) -> list[Diagnostic]:
        if self._config is None:
            return []
        diags: list[Diagnostic] = []
        root = self._root.resolve()
        paths_obj = self._config.paths  # type: ignore[attr-defined]
        for field in ("packs", "profiles", "contracts", "marketplace", "build_output"):
            val = getattr(paths_obj, field, None)
            if not val:
                continue
            try:
                resolved = (self._root / val).resolve()
                if not resolved.is_relative_to(root):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L021,
                        Severity.ERROR,
                        f"catalogue.paths.{field} resolves outside catalogue root: {val!r}",
                        remediation="Use a relative path that stays within the catalogue root.",
                    ))
            except OSError:
                pass
        return diags


# ---------------------------------------------------------------------------
# Pack-level rules
# ---------------------------------------------------------------------------


class _PackRules:
    def __init__(self, pack_dir: Path) -> None:
        self._dir = pack_dir
        self._name = pack_dir.name
        self._pack_toml: dict | None = None
        self._pack_toml_loaded = False

    def _get_pack_toml(self) -> dict | None:
        if not self._pack_toml_loaded:
            self._pack_toml_loaded = True
            toml_path = self._dir / "pack.toml"
            if toml_path.exists():
                try:
                    self._pack_toml = tomllib.loads(toml_path.read_text(encoding="utf-8"))
                except Exception:
                    self._pack_toml = None
        return self._pack_toml

    def collect(self) -> list[Diagnostic]:
        diags: list[Diagnostic] = []
        diags.extend(self._check_dir_name_vs_pack_toml())
        diags.extend(self._check_pack_toml_parseable())
        diags.extend(self._check_pack_schema_validation())
        diags.extend(self._check_plugin_json())
        diags.extend(self._check_name_version_parity())
        diags.extend(self._check_skills())
        diags.extend(self._check_agents())
        return diags

    def _check_dir_name_vs_pack_toml(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        pack_name = pt.get("pack", {}).get("name", "")
        if pack_name and pack_name != self._name:
            return [_diag(
                DiagnosticCode.CAT_L004,
                Severity.ERROR,
                f"directory name {self._name!r} differs from [pack].name {pack_name!r}",
                pack=self._name,
                path=str(self._dir / "pack.toml"),
                remediation="Rename the directory to match [pack].name, or update [pack].name.",
            )]
        return []

    def _check_pack_toml_parseable(self) -> list[Diagnostic]:
        toml_path = self._dir / "pack.toml"
        if not toml_path.exists():
            return []
        try:
            tomllib.loads(toml_path.read_text(encoding="utf-8"))
            return []
        except Exception as exc:
            return [_diag(
                DiagnosticCode.CAT_L005,
                Severity.ERROR,
                f"pack.toml is not valid TOML: {exc}",
                pack=self._name,
                path=str(toml_path),
                remediation="Fix the TOML syntax error in pack.toml.",
            )]

    def _check_pack_schema_validation(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        schema = _load_pack_schema()
        if schema is None:
            return [_diag(
                DiagnosticCode.CAT_L006,
                Severity.WARN,
                "pack.schema.json not found; skipping schema validation",
                pack=self._name,
                remediation="Ensure pack.schema.json is bundled with agentbundle.",
            )]
        from agentbundle.build.validate import validate
        errors = validate(pt, schema)
        if errors:
            return [_diag(
                DiagnosticCode.CAT_L006,
                Severity.ERROR,
                f"pack.toml fails schema validation: {errors[0]}",
                pack=self._name,
                path=str(self._dir / "pack.toml"),
                remediation="Fix the pack.toml field(s) reported by the schema validator.",
            )]
        return []

    def _check_plugin_json(self) -> list[Diagnostic]:
        plugin_path = self._dir / "plugin.json"
        if not plugin_path.exists():
            return []
        try:
            data = json.loads(plugin_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return [_diag(
                DiagnosticCode.CAT_L007,
                Severity.ERROR,
                f"plugin.json is not valid JSON: {exc}",
                pack=self._name,
                path=str(plugin_path),
                remediation="Fix the JSON syntax error in plugin.json.",
            )]
        # Basic schema check: must have name and version
        diags: list[Diagnostic] = []
        for key in ("name", "version"):
            if key not in data:
                diags.append(_diag(
                    DiagnosticCode.CAT_L008,
                    Severity.ERROR,
                    f"plugin.json missing required key: {key!r}",
                    pack=self._name,
                    path=str(plugin_path),
                    remediation=f"Add {key!r} to plugin.json.",
                ))
        return diags

    def _check_name_version_parity(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        plugin_path = self._dir / "plugin.json"
        if not plugin_path.exists():
            return []
        try:
            plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        pack_name = pt.get("pack", {}).get("name", "")
        pack_ver = pt.get("pack", {}).get("version", "")
        plugin_name = plugin_data.get("name", "")
        plugin_ver = plugin_data.get("version", "")
        diags: list[Diagnostic] = []
        if pack_name and plugin_name and pack_name != plugin_name:
            diags.append(_diag(
                DiagnosticCode.CAT_L009,
                Severity.ERROR,
                f"name mismatch: pack.toml={pack_name!r}, plugin.json={plugin_name!r}",
                pack=self._name,
                remediation="Keep [pack].name and plugin.json name in sync.",
            ))
        if pack_ver and plugin_ver and pack_ver != plugin_ver:
            diags.append(_diag(
                DiagnosticCode.CAT_L009,
                Severity.ERROR,
                f"version mismatch: pack.toml={pack_ver!r}, plugin.json={plugin_ver!r}",
                pack=self._name,
                remediation="Keep [pack].version and plugin.json version in sync.",
            ))
        return diags

    def _check_skills(self) -> list[Diagnostic]:
        skills_dir = self._dir / ".apm" / "skills"
        if not skills_dir.is_dir():
            return []
        diags: list[Diagnostic] = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                diags.append(_diag(
                    DiagnosticCode.CAT_L010,
                    Severity.ERROR,
                    f"skill directory {skill_dir.name!r} missing SKILL.md",
                    pack=self._name,
                    path=str(skill_dir),
                    remediation="Add a SKILL.md with name and description frontmatter.",
                ))
                continue
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            if fm is None:
                diags.append(_diag(
                    DiagnosticCode.CAT_L011,
                    Severity.ERROR,
                    f"SKILL.md missing frontmatter",
                    pack=self._name,
                    path=str(skill_md),
                    remediation="Add --- frontmatter with name and description.",
                ))
                continue
            for key in _SKILL_REQUIRED_KEYS:
                if not fm.get(key):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L011,
                        Severity.ERROR,
                        f"SKILL.md frontmatter missing required key: {key!r}",
                        pack=self._name,
                        path=str(skill_md),
                        remediation=f"Add {key!r} to the SKILL.md frontmatter.",
                    ))
            # Check description length
            desc = fm.get("description", "")
            if len(desc) > _MAX_DESC_LEN:
                diags.append(_diag(
                    DiagnosticCode.CAT_L026,
                    Severity.ERROR,
                    f"SKILL.md description exceeds {_MAX_DESC_LEN} chars ({len(desc)})",
                    pack=self._name,
                    path=str(skill_md),
                    remediation="Shorten the description field.",
                ))
        return diags

    def _check_agents(self) -> list[Diagnostic]:
        agents_dir = self._dir / ".apm" / "agents"
        if not agents_dir.is_dir():
            return []
        diags: list[Diagnostic] = []
        for agent_file in sorted(agents_dir.rglob("*.md")):
            text = agent_file.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            if fm is None:
                diags.append(_diag(
                    DiagnosticCode.CAT_L012,
                    Severity.ERROR,
                    f"agent file {agent_file.name!r} missing frontmatter",
                    pack=self._name,
                    path=str(agent_file),
                    remediation="Add --- frontmatter with name and description.",
                ))
                continue
            for key in _AGENT_REQUIRED_KEYS:
                if not fm.get(key):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L012,
                        Severity.ERROR,
                        f"agent file frontmatter missing required key: {key!r}",
                        pack=self._name,
                        path=str(agent_file),
                        remediation=f"Add {key!r} to the agent frontmatter.",
                    ))
        return diags


# ---------------------------------------------------------------------------
# Legacy finding translator (lint_packs string → Diagnostic)
# ---------------------------------------------------------------------------


def _translate_legacy_finding(pack_name: str, finding: str) -> Diagnostic:
    """Map a lint_packs string finding to a Diagnostic with a stable code."""
    # "pack: symlink not portable to Windows: relpath"
    if "symlink not portable to Windows" in finding:
        path_part = finding.split(": ", 2)[-1] if finding.count(": ") >= 2 else ""
        return _diag(
            DiagnosticCode.CAT_L022,
            Severity.WARN,
            finding,
            pack=pack_name,
            path=path_part or None,
        )
    # Windows-poisonous name → CAT-L023
    return _diag(
        DiagnosticCode.CAT_L023,
        Severity.ERROR,
        finding,
        pack=pack_name,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def lint_catalogue(root: Path, pack: str | None = None, *, deep: bool = False) -> LintResult:
    """Run all portable catalogue lint rules against *root*.

    When *pack* is given, pack-level diagnostics are filtered to that pack.
    Catalogue-level rules (CAT-L001, CAT-L002) always run against the full
    catalogue. Read-only; raises no exceptions (all errors become diagnostics).

    When *deep* is ``True``, runs the full agentskills.io spec-compliance lint
    via :mod:`agentbundle.catalogue_tooling.skill_spec_lint`.  Requires the
    ``pyyaml`` optional extra (``pip install 'agentbundle[lint]'``); raises
    ``ImportError`` when PyYAML is absent so the CLI can exit 2.
    """
    from agentbundle.build.lint_packs import lint_pack as _lint_pack

    diagnostics: list[Diagnostic] = []

    # Step 1: load catalogue.toml; emit CAT-L001 and return early on error
    config = None
    try:
        config = load_catalogue_config(root)
    except CatalogueConfigError as exc:
        diagnostics.append(_diag(
            DiagnosticCode.CAT_L001,
            Severity.ERROR,
            f"catalogue.toml is present but invalid: {exc}",
            remediation="Fix the reported validation error in catalogue.toml.",
        ))
        diagnostics.sort(key=_sort_key)
        return LintResult(
            ok=False,
            diagnostics=diagnostics,
            schema_version=1,
            command="catalogue lint",
            operation="lint",
            agentbundle_version=_get_agentbundle_version(),
            catalogue_schema_version=1,
        )

    # Step 2: catalogue-level rules
    cat_rules = _CatalogueRules(root, config)
    diagnostics.extend(cat_rules.collect(pack))

    # Step 3: determine packs dir
    if config is not None:
        packs_dir = root / config.paths.packs
    else:
        packs_dir = root / "packs"

    # Step 4+5: per-pack rules
    if packs_dir.is_dir():
        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir() or not (pack_dir / "pack.toml").exists():
                continue
            pack_name = pack_dir.name
            if pack is not None and pack_name != pack:
                continue

            # Pack-level rules
            pack_rules = _PackRules(pack_dir)
            diagnostics.extend(pack_rules.collect())

            # Portability rules from lint_packs
            legacy_findings = _lint_pack(pack_dir)
            for finding in legacy_findings:
                diagnostics.append(_translate_legacy_finding(pack_name, finding))

    # Deep spec-compliance pass
    if deep:
        from agentbundle.catalogue_tooling.skill_spec_lint import lint_skill_spec
        deep_diags = lint_skill_spec(root, pack=pack)
        diagnostics.extend(deep_diags)

    diagnostics.sort(key=_sort_key)
    ok = not any(d.severity == Severity.ERROR for d in diagnostics)

    return LintResult(
        ok=ok,
        diagnostics=diagnostics,
        schema_version=1,
        command="catalogue lint",
        operation="lint",
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=config.schema if config else 1,
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_json(result: LintResult) -> str:
    """Return a single valid JSON document for *result*. Deterministic."""
    data = {
        "schema_version": result.schema_version,
        "command": result.command,
        "operation": result.operation,
        "agentbundle_version": result.agentbundle_version,
        "catalogue_schema_version": result.catalogue_schema_version,
        "ok": result.ok,
        "diagnostics": [
            {
                "code": d.code,
                "severity": d.severity.name,
                "pack": d.pack,
                "path": d.path,
                "line": d.line,
                "col": d.col,
                "message": d.message,
                "remediation": d.remediation,
            }
            for d in result.diagnostics
        ],
    }
    return json.dumps(data, sort_keys=True, indent=2)


def render_table(result: LintResult) -> str:
    """Return a grouped plain-text table for *result*."""
    if not result.diagnostics:
        return f"ok: catalogue lint clean ({result.agentbundle_version})"

    lines: list[str] = []
    by_pack: dict[str, list[Diagnostic]] = {}
    for d in result.diagnostics:
        key = d.pack or "(catalogue)"
        by_pack.setdefault(key, []).append(d)

    for pack_key in sorted(by_pack):
        lines.append(f"── {pack_key} ──")
        for d in by_pack[pack_key]:
            loc = ""
            if d.path:
                loc = d.path
                if d.line is not None:
                    loc += f":{d.line}"
            sev = d.severity.name
            lines.append(f"  [{d.code}] {sev} {loc}")
            lines.append(f"    {d.message}")
            if d.remediation:
                lines.append(f"    → {d.remediation}")
        lines.append("")

    status = "ok" if result.ok else "FAIL"
    lines.append(f"{status}: {len(result.diagnostics)} finding(s)")
    return "\n".join(lines)
