"""Unit tests for agentbundle.catalogue_tooling.lint (Wave 2, ini-005).

Coverage:
  - lint_catalogue(root, pack=None) -> LintResult
  - render_json / render_table formatters
  - Each rule exercised by a minimal filesystem fixture using tmp_path.

Monkeypatching strategy:
  - agentbundle.build.lint_packs.lint_pack is stubbed to [] in all tests
    unless a specific finding is under test (test 14). The stub avoids
    pulling in portability-check machinery and platform-specific state.
  - agentbundle.catalogue_tooling.lint._load_pack_schema is stubbed to
    return None where schema-validation results are not the focus.
    When None is returned, _check_pack_schema_validation emits CAT-L006
    at WARN severity, which does not affect ok.
  - No catalogue.toml is created in any fixture: load_catalogue_config
    returns None naturally (file absent), so the linter uses default
    paths (packs/ and .claude-plugin/marketplace.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import agentbundle.build.lint_packs as _lp_module
import agentbundle.catalogue_tooling.lint as _lint_module
from agentbundle.catalogue_tooling.lint import lint_catalogue, render_json, render_table
from agentbundle.catalogue_tooling.results import Diagnostic, LintResult, Severity


# ---------------------------------------------------------------------------
# Shared filesystem helpers
# ---------------------------------------------------------------------------


def _setup_markers(root: Path) -> None:
    """Create the default catalogue structural markers lint requires."""
    (root / "packs").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8"
    )


def _add_pack(
    root: Path,
    dir_name: str,
    *,
    pack_toml: str | None = None,
    plugin_json: str | None = None,
) -> Path:
    """Create a pack directory under root/packs/ with optional pack files."""
    pack_dir = root / "packs" / dir_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    if pack_toml is not None:
        (pack_dir / "pack.toml").write_text(pack_toml, encoding="utf-8")
    if plugin_json is not None:
        (pack_dir / "plugin.json").write_text(plugin_json, encoding="utf-8")
    return pack_dir


_PACK_A_TOML = "[pack]\nname = \"pack-a\"\nversion = \"0.1.0\"\n"
_PACK_A_JSON = '{"name": "pack-a", "version": "0.1.0"}'


# ---------------------------------------------------------------------------
# 1. test_no_catalogue_toml
# ---------------------------------------------------------------------------


def test_no_catalogue_toml(tmp_path, monkeypatch):
    """No catalogue.toml present: load_catalogue_config returns None naturally.

    With both default markers (packs/ dir and marketplace.json) present and
    an empty packs directory, no rules fire → ok=True, no diagnostics.
    """
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    _setup_markers(tmp_path)
    result = lint_catalogue(tmp_path)
    assert result.ok is True
    assert result.diagnostics == []


# ---------------------------------------------------------------------------
# 2. test_clean_catalogue
# ---------------------------------------------------------------------------


def test_clean_catalogue(tmp_path, monkeypatch):
    """One pack with valid pack.toml + plugin.json → ok=True, no ERROR diagnostics."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON)
    result = lint_catalogue(tmp_path)
    assert result.ok is True
    errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
    assert errors == []


# ---------------------------------------------------------------------------
# 3. test_pack_filter
# ---------------------------------------------------------------------------


def test_pack_filter(tmp_path, monkeypatch):
    """pack='pack-a' scope: pack-b diagnostics are excluded from the result."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON)
    # pack-b: dir/name mismatch → would produce CAT-L004 when pack-b is in scope
    _add_pack(
        tmp_path,
        "pack-b",
        pack_toml="[pack]\nname = \"pack-x\"\nversion = \"0.1.0\"\n",
    )
    result = lint_catalogue(tmp_path, pack="pack-a")
    packs_with_diags = {d.pack for d in result.diagnostics if d.pack is not None}
    assert "pack-b" not in packs_with_diags


# ---------------------------------------------------------------------------
# 4. test_cat_l003_duplicate_identity
# ---------------------------------------------------------------------------


def test_cat_l003_duplicate_identity(tmp_path, monkeypatch):
    """Two packs with the same [pack].name → CAT-L003 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    shared_toml = "[pack]\nname = \"shared-name\"\nversion = \"0.1.0\"\n"
    _add_pack(tmp_path, "pack-a", pack_toml=shared_toml)
    _add_pack(tmp_path, "pack-b", pack_toml=shared_toml)
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L003" in codes


# ---------------------------------------------------------------------------
# 5. test_cat_l004_dir_name_mismatch
# ---------------------------------------------------------------------------


def test_cat_l004_dir_name_mismatch(tmp_path, monkeypatch):
    """Directory named 'pack-a' but [pack].name is 'pack-b' → CAT-L004 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(
        tmp_path,
        "pack-a",
        pack_toml="[pack]\nname = \"pack-b\"\nversion = \"0.1.0\"\n",
    )
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L004" in codes


# ---------------------------------------------------------------------------
# 6. test_cat_l005_unparse_pack_toml
# ---------------------------------------------------------------------------


def test_cat_l005_unparse_pack_toml(tmp_path, monkeypatch):
    """pack.toml with invalid TOML syntax → CAT-L005 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml="this = [[ not valid toml")
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L005" in codes


# ---------------------------------------------------------------------------
# 7. test_cat_l006_schema_absent_warns
# ---------------------------------------------------------------------------


def test_cat_l006_schema_absent_warns(tmp_path, monkeypatch):
    """No pack schema available → CAT-L006 WARN (not ERROR); ok stays True."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON)
    result = lint_catalogue(tmp_path)
    l006_diags = [d for d in result.diagnostics if d.code == "CAT-L006"]
    assert l006_diags, "expected at least one CAT-L006 diagnostic when schema is absent"
    assert l006_diags[0].severity == Severity.WARN
    # WARN does not set ok=False
    assert result.ok is True


# ---------------------------------------------------------------------------
# 8. test_cat_l007_unparse_plugin_json
# ---------------------------------------------------------------------------


def test_cat_l007_unparse_plugin_json(tmp_path, monkeypatch):
    """plugin.json with invalid JSON → CAT-L007 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(
        tmp_path,
        "pack-a",
        pack_toml=_PACK_A_TOML,
        plugin_json="{ not valid json }",
    )
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L007" in codes


# ---------------------------------------------------------------------------
# 9. test_cat_l009_name_version_mismatch
# ---------------------------------------------------------------------------


def test_cat_l009_name_version_mismatch(tmp_path, monkeypatch):
    """pack.toml name differs from plugin.json name → CAT-L009 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(
        tmp_path,
        "pack-a",
        pack_toml="[pack]\nname = \"pack-a\"\nversion = \"1.0.0\"\n",
        plugin_json='{"name": "pack-b", "version": "1.0.0"}',
    )
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L009" in codes


# ---------------------------------------------------------------------------
# 10. test_cat_l010_skill_missing_skill_md
# ---------------------------------------------------------------------------


def test_cat_l010_skill_missing_skill_md(tmp_path, monkeypatch):
    """Skill subdirectory exists but has no SKILL.md → CAT-L010 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(
        tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON
    )
    (pack_dir / ".apm" / "skills" / "my-skill").mkdir(parents=True)
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L010" in codes


# ---------------------------------------------------------------------------
# 11. test_cat_l011_skill_missing_frontmatter_key
# ---------------------------------------------------------------------------


def test_cat_l011_skill_missing_frontmatter_key(tmp_path, monkeypatch):
    """SKILL.md with frontmatter but missing 'name' key → CAT-L011 error."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(
        tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON
    )
    skill_dir = pack_dir / ".apm" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    # Frontmatter has 'description' but not 'name'
    (skill_dir / "SKILL.md").write_text(
        "---\ndescription: Does something useful\n---\n\nBody.\n",
        encoding="utf-8",
    )
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L011" in codes


# ---------------------------------------------------------------------------
# 12. test_render_json
# ---------------------------------------------------------------------------


def test_render_json():
    """render_json returns valid JSON with 'ok' bool key and 'diagnostics' array."""
    result = LintResult(
        ok=True,
        diagnostics=[],
        schema_version=1,
        command="catalogue lint",
        operation="lint",
        agentbundle_version="0.0.0",
        catalogue_schema_version=1,
    )
    output = render_json(result)
    parsed = json.loads(output)
    assert "ok" in parsed
    assert parsed["ok"] is True
    assert isinstance(parsed["diagnostics"], list)


# ---------------------------------------------------------------------------
# 13. test_render_table
# ---------------------------------------------------------------------------


def test_render_table():
    """render_table with one ERROR diagnostic includes the code in output text."""
    diag = Diagnostic(
        code="CAT-L004",
        severity=Severity.ERROR,
        pack="pack-a",
        path="/packs/pack-a/pack.toml",
        line=None,
        col=None,
        message="directory name 'pack-a' differs from [pack].name 'pack-b'",
        remediation="Rename the directory.",
    )
    result = LintResult(
        ok=False,
        diagnostics=[diag],
        schema_version=1,
        command="catalogue lint",
        operation="lint",
        agentbundle_version="0.0.0",
        catalogue_schema_version=1,
    )
    output = render_table(result)
    assert "CAT-L004" in output


# ---------------------------------------------------------------------------
# 14. test_lint_packs_symlink_translated
# ---------------------------------------------------------------------------


def test_lint_packs_symlink_translated(tmp_path, monkeypatch):
    """lint_pack finding containing 'symlink not portable to Windows' → CAT-L022."""
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    symlink_finding = "pack-a: symlink not portable to Windows: some/linked/file"
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [symlink_finding])
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML, plugin_json=_PACK_A_JSON)
    result = lint_catalogue(tmp_path)
    codes = [d.code for d in result.diagnostics]
    assert "CAT-L022" in codes
    # CAT-L022 is WARN, not ERROR
    l022 = [d for d in result.diagnostics if d.code == "CAT-L022"]
    assert l022[0].severity == Severity.WARN


# ---------------------------------------------------------------------------
# 15. test_ok_false_on_any_error
# ---------------------------------------------------------------------------


def test_ok_false_on_any_error(tmp_path, monkeypatch):
    """A single ERROR diagnostic in the result makes ok=False."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    # dir='pack-a', [pack].name='pack-b' → CAT-L004 ERROR
    _add_pack(
        tmp_path,
        "pack-a",
        pack_toml="[pack]\nname = \"pack-b\"\nversion = \"0.1.0\"\n",
    )
    result = lint_catalogue(tmp_path)
    assert result.ok is False
    assert any(d.severity == Severity.ERROR for d in result.diagnostics)
