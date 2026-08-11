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
  - Shared fixtures create a valid catalogue.toml with the default paths and
    claude-code preferred adapter. Dedicated negative tests omit or customize
    it explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path

import agentbundle.build.lint_packs as _lp_module
import agentbundle.catalogue_tooling.lint as _lint_module
import pytest
from agentbundle.catalogue_tooling.lint import lint_catalogue, render_json, render_table
from agentbundle.catalogue_tooling.results import Diagnostic, LintResult, Severity
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

# ---------------------------------------------------------------------------
# Shared filesystem helpers
# ---------------------------------------------------------------------------


def _write_catalogue_config(
    root: Path,
    *,
    preferred_adapter: str = "claude-code",
    packs_path: str = "packs",
) -> None:
    text = emit_catalogue_toml(
        name="test-catalogue",
        display_name="Test catalogue",
        description="Catalogue lint fixture.",
        minimum_agentbundle_version="0.32.0",
        owner_name="Example User",
        preferred_adapter=preferred_adapter,
    )
    text = text.replace('packs        = "packs"', f'packs        = "{packs_path}"')
    (root / "catalogue.toml").write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )


def _setup_markers(root: Path) -> None:
    """Create a valid Claude-targeting catalogue with generated marketplace."""
    _write_catalogue_config(root)
    (root / "packs").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
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
        (pack_dir / "pack.toml").write_text(pack_toml, encoding="utf-8", newline="\n")
    if plugin_json is not None:
        (pack_dir / "plugin.json").write_text(plugin_json, encoding="utf-8", newline="\n")
    return pack_dir


_PACK_A_TOML = (
    '[pack]\nname = "pack-a"\nversion = "0.1.0"\n\n'
    '[pack.first-value]\n'
    'audience-posture = "technical"\n'
    'surfaces = ["claude"]\n'
    'prerequisites = []\n'
    'verification = "run tests"\n'
    'recovery = "revert"\n'
)
_PACK_A_JSON = '{"name": "pack-a", "version": "0.1.0"}'


# ---------------------------------------------------------------------------
# 1. test_no_catalogue_toml
# ---------------------------------------------------------------------------


def test_no_catalogue_toml(tmp_path, monkeypatch):
    """A source root without catalogue.toml is not a lintable catalogue."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    (tmp_path / "packs").mkdir()
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
    )
    result = lint_catalogue(tmp_path)
    assert result.ok is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CAT-L002"]


def test_kiro_only_catalogue_does_not_require_claude_marketplace(tmp_path, monkeypatch):
    """Kiro-only projection succeeds without a Claude marketplace artifact."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    _write_catalogue_config(tmp_path, preferred_adapter="kiro-ide")
    (tmp_path / "packs").mkdir()
    result = lint_catalogue(tmp_path)
    assert result.ok is True
    assert all(diagnostic.code != "CAT-L002" for diagnostic in result.diagnostics)


def test_literal_root_packs_and_configured_packs_are_checked_separately(
    tmp_path,
    monkeypatch,
):
    """A configured packs path cannot replace the literal root identity marker."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    _write_catalogue_config(tmp_path, packs_path="catalogue-packs")
    configured_packs = tmp_path / "catalogue-packs"
    configured_packs.mkdir()
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
    )

    missing_root_marker = lint_catalogue(tmp_path)
    assert any(
        diagnostic.code == "CAT-L002" and str(tmp_path / "packs") in diagnostic.message
        for diagnostic in missing_root_marker.diagnostics
    )

    (tmp_path / "packs").mkdir()
    configured_packs.rmdir()
    missing_configured_content = lint_catalogue(tmp_path)
    assert any(
        diagnostic.code == "CAT-L002" and str(configured_packs) in diagnostic.message
        for diagnostic in missing_configured_content.diagnostics
    )


def test_configured_packs_symlink_escape_is_not_inspected(tmp_path, monkeypatch):
    """Configured pack content outside the catalogue root is never inspected."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    for name in ("one", "two"):
        pack_dir = outside / name
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            '[pack]\nname = "duplicate"\nversion = "0.1.0"\n',
            encoding="utf-8",
            newline="\n",
        )
    linked_packs = tmp_path / "linked-packs"
    try:
        linked_packs.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform/filesystem")
    _write_catalogue_config(tmp_path, packs_path="linked-packs")
    (tmp_path / "packs").mkdir()
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
    )
    result = lint_catalogue(tmp_path)
    error_codes = [
        diagnostic.code
        for diagnostic in result.diagnostics
        if diagnostic.severity == Severity.ERROR
    ]
    assert error_codes == ["CAT-L001"]


def test_configured_packs_symlink_loop_is_diagnostic(tmp_path, monkeypatch):
    """A circular configured packs path is diagnostic rather than exceptional."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    loop = tmp_path / "loop"
    try:
        loop.symlink_to(loop, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform/filesystem")
    _write_catalogue_config(tmp_path, packs_path="loop")
    (tmp_path / "packs").mkdir()
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
    )
    result = lint_catalogue(tmp_path)
    error_codes = [
        diagnostic.code
        for diagnostic in result.diagnostics
        if diagnostic.severity == Severity.ERROR
    ]
    assert error_codes in (["CAT-L001"], ["CAT-L002"], ["CAT-L021"])


@pytest.mark.parametrize(
    ("projects_claude", "expects_missing_marketplace"),
    [(False, False), (True, True)],
)
def test_claude_marketplace_requirement_uses_shared_projection_predicate(
    tmp_path,
    monkeypatch,
    projects_claude,
    expects_missing_marketplace,
):
    """Claude-targeting lint delegates marketplace policy to self-host."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(
        _lint_module,
        "projects_claude_artifacts",
        lambda preferred_adapter: projects_claude,
    )
    _write_catalogue_config(tmp_path, preferred_adapter="claude-code")
    (tmp_path / "packs").mkdir()
    result = lint_catalogue(tmp_path)
    has_missing_marketplace = any(
        diagnostic.code == "CAT-L002" for diagnostic in result.diagnostics
    )
    assert has_missing_marketplace is expects_missing_marketplace


def test_allowed_adapter_requires_claude_marketplace(tmp_path, monkeypatch):
    """An already-allowed adapter retains Claude linting through real config."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    _write_catalogue_config(tmp_path, preferred_adapter="codex")
    (tmp_path / "packs").mkdir()
    result = lint_catalogue(tmp_path)
    assert any(diagnostic.code == "CAT-L002" for diagnostic in result.diagnostics)


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
        newline="\n",
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


# ---------------------------------------------------------------------------
# Task 2 — _CatalogueRules._check_profiles() (CAT-L028)
# ---------------------------------------------------------------------------


def _setup_profile(root: Path, name: str, content: str) -> Path:
    """Write a profile TOML file under root/profiles/."""
    (root / "profiles").mkdir(parents=True, exist_ok=True)
    p = root / "profiles" / f"{name}.toml"
    p.write_text(content, encoding="utf-8", newline="\n")
    return p


def _add_pack_full(
    root: Path,
    name: str,
    *,
    version: str = "0.1.0",
    allowed_scopes: list[str] | None = None,
    required_deps: list[dict] | None = None,
) -> Path:
    """Add a pack with full pack.toml for profiles tests."""
    pack_dir = root / "packs" / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    install_section = ""
    if allowed_scopes is not None:
        scopes_str = ", ".join(f'"{s}"' for s in allowed_scopes)
        install_section = f'\n[pack.install]\nallowed-scopes = [{scopes_str}]'
    deps_section = ""
    if required_deps:
        deps_lines = "\n".join(
            f'  {{ pack = "{d["pack"]}", version = "{d["version"]}" }}'
            for d in required_deps
        )
        deps_section = f"\n[pack.dependencies]\nrequired = [\n{deps_lines},\n]"
    (pack_dir / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "{version}"\n'
        f'{install_section}{deps_section}\n',
        encoding="utf-8",
        newline="\n",
    )
    return pack_dir


def test_check_profiles_no_profiles_dir(tmp_path, monkeypatch):
    """No profiles/ directory → no CAT-L028 diagnostics."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L028" for d in result.diagnostics)


def test_check_profiles_invalid_scope_value(tmp_path, monkeypatch):
    """Profile with invalid scope value → CAT-L028 mentioning 'invalid scope' or 'scope must be'."""  # noqa: E501
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _setup_profile(tmp_path, "bad-scope", 'scope = "cluster"\npacks = []')
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for invalid scope value"
    assert any("scope must be" in d.message for d in l028)


def test_check_profiles_empty_packs_list(tmp_path, monkeypatch):
    """Profile with empty packs list → CAT-L028 mentioning 'non-empty list'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _setup_profile(tmp_path, "empty-packs", 'scope = "repo"\npacks = []')
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for empty packs list"
    assert any("non-empty list" in d.message for d in l028)


def test_check_profiles_pack_not_found(tmp_path, monkeypatch):
    """Profile references pack not in packs/ → CAT-L028 mentioning 'not found in packs/'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _setup_profile(
        tmp_path, "missing-pack",
        'scope = "repo"\n[[packs]]\npack = "nonexistent-pack"\n'
    )
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for pack not found"
    assert any("not found in packs/" in d.message for d in l028)


def test_check_profiles_scope_homogeneity_violation(tmp_path, monkeypatch):
    """Profile scope 'user' but pack only allows 'repo' → CAT-L028 mentioning 'does not allow scope'."""  # noqa: E501
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_full(tmp_path, "repo-only", allowed_scopes=["repo"])
    _setup_profile(
        tmp_path, "scope-mismatch",
        'scope = "user"\n[[packs]]\npack = "repo-only"\n'
    )
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for scope homogeneity violation"
    assert any("does not allow scope" in d.message for d in l028)


def test_check_profiles_dependency_incomplete(tmp_path, monkeypatch):
    """Pack has required dep not in profile → CAT-L028 mentioning 'dependency-incomplete'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_full(
        tmp_path, "pack-a", allowed_scopes=["repo"],
        required_deps=[{"pack": "pack-b", "version": "^0.1"}],
    )
    _setup_profile(
        tmp_path, "missing-dep",
        'scope = "repo"\n[[packs]]\npack = "pack-a"\n'
    )
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for dependency-incomplete"
    assert any("dependency-incomplete" in d.message for d in l028)


def test_check_profiles_order_invalid(tmp_path, monkeypatch):
    """Dep listed after dependent pack → CAT-L028 mentioning 'mis-ordered'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_full(tmp_path, "pack-base", allowed_scopes=["repo"])
    _add_pack_full(
        tmp_path, "pack-ext", allowed_scopes=["repo"],
        required_deps=[{"pack": "pack-base", "version": "^0.1"}],
    )
    # pack-ext before pack-base (wrong order)
    _setup_profile(
        tmp_path, "wrong-order",
        'scope = "repo"\n[[packs]]\npack = "pack-ext"\n[[packs]]\npack = "pack-base"\n'
    )
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for mis-ordered deps"
    assert any("mis-ordered" in d.message for d in l028)


def test_check_profiles_unsupported_range_grammar(tmp_path, monkeypatch):
    """Pack dep uses unsupported range grammar → CAT-L028 mentioning 'unsupported version range'."""  # noqa: E501
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_full(tmp_path, "pack-base", allowed_scopes=["repo"])
    _add_pack_full(
        tmp_path, "pack-ext", allowed_scopes=["repo"],
        required_deps=[{"pack": "pack-base", "version": "~=0.1"}],
    )
    _setup_profile(
        tmp_path, "bad-range",
        'scope = "repo"\n[[packs]]\npack = "pack-base"\n[[packs]]\npack = "pack-ext"\n'
    )
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for unsupported range grammar"
    assert any("unsupported version range" in d.message for d in l028)


def test_check_profiles_parse_failure(tmp_path, monkeypatch):
    """Malformed TOML profile → CAT-L028 mentioning 'cannot parse'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _setup_profile(tmp_path, "bad-toml", "this = [[ invalid toml")
    result = lint_catalogue(tmp_path)
    l028 = [d for d in result.diagnostics if d.code == "CAT-L028"]
    assert l028, "expected CAT-L028 for parse failure"
    assert any("cannot parse" in d.message for d in l028)


def test_check_profiles_clean(tmp_path, monkeypatch):
    """Valid profile → no CAT-L028 diagnostics."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_full(tmp_path, "pack-a", allowed_scopes=["repo"])
    _setup_profile(
        tmp_path, "clean",
        'scope = "repo"\n[[packs]]\npack = "pack-a"\n'
    )
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L028" for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Task 3 — _PackRules._check_seeds() (CAT-L029)
# ---------------------------------------------------------------------------


def _add_pack_with_seeds(
    root: Path,
    pack_name: str,
    *,
    lint_seeds: bool = True,
    seeds: dict[str, str] | None = None,
) -> Path:
    """Create a pack with opt-in lint-seeds flag and optional seed files."""
    pack_dir = root / "packs" / pack_name
    (pack_dir / "seeds").mkdir(parents=True, exist_ok=True)
    flag = "true" if lint_seeds else "false"
    (pack_dir / "pack.toml").write_text(
        f'[pack]\nname = "{pack_name}"\nversion = "0.1.0"\nlint-seeds = {flag}\n',
        encoding="utf-8",
        newline="\n",
    )
    if seeds:
        for rel, content in seeds.items():
            seed_path = pack_dir / "seeds" / rel
            seed_path.parent.mkdir(parents=True, exist_ok=True)
            seed_path.write_text(content, encoding="utf-8", newline="\n")
    return pack_dir


def test_check_seeds_opt_out(tmp_path, monkeypatch):
    """Pack without lint-seeds = true → no CAT-L029 even with unknown seed."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_with_seeds(
        tmp_path, "pack-a", lint_seeds=False, seeds={"AGENTS.md": "<project-name>"}
    )
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L029" for d in result.diagnostics)


def test_check_seeds_unknown_seed(tmp_path, monkeypatch):
    """Seed not in REQUIRED_PLACEHOLDERS → CAT-L029 fail-loud mentioning 'declare its expected'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_with_seeds(
        tmp_path, "pack-a", lint_seeds=True,
        seeds={"unknown-file.md": "some content"},
    )
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    assert l029, "expected CAT-L029 for unknown seed file"
    assert any("declare its expected" in d.message for d in l029)


def test_check_seeds_blocklist_hit(tmp_path, monkeypatch):
    """Seed contains 'agent-ready-repo' → CAT-L029."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_with_seeds(
        tmp_path, "pack-a", lint_seeds=True,
        seeds={"AGENTS.md": "This is for agent-ready-repo\n<project-name>"},
    )
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    assert l029, "expected CAT-L029 for blocklist hit"


def test_check_seeds_missing_placeholder(tmp_path, monkeypatch):
    """Seed missing required placeholder token → CAT-L029."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    # AGENTS.md requires '<project-name>'
    _add_pack_with_seeds(
        tmp_path, "pack-a", lint_seeds=True,
        seeds={"AGENTS.md": "No placeholder here\n"},
    )
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    assert l029, "expected CAT-L029 for missing placeholder"
    assert any("required placeholder missing" in d.message for d in l029)


def test_check_seeds_sentinel_exemption(tmp_path, monkeypatch):
    """Seed with sentinel above blocklist hit → no CAT-L029."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    content = (
        "<project-name>\n"
        "<!-- seed-content-lint-ignore: intentional -->\n"
        "agent-ready-repo\n"
    )
    _add_pack_with_seeds(tmp_path, "pack-a", lint_seeds=True, seeds={"AGENTS.md": content})
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L029" for d in result.diagnostics)


def test_check_seeds_stacked_sentinel(tmp_path, monkeypatch):
    """Two back-to-back sentinels → CAT-L029 mentioning 'stacked sentinel'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    content = (
        "<project-name>\n"
        "<!-- seed-content-lint-ignore: first -->\n"
        "<!-- seed-content-lint-ignore: second -->\n"
        "some content\n"
    )
    _add_pack_with_seeds(tmp_path, "pack-a", lint_seeds=True, seeds={"AGENTS.md": content})
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    assert l029, "expected CAT-L029 for stacked sentinel"
    assert any("stacked sentinel" in d.message for d in l029)


def test_check_seeds_patterns_jsonl_nonempty(tmp_path, monkeypatch):
    """patterns.jsonl with content → CAT-L029."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    seeds = {
        "AGENTS.md": "<project-name>",
        "docs/knowledge/patterns.jsonl": '{"pattern": "example"}\n',
    }
    pack_dir = tmp_path / "packs" / "pack-a"
    (pack_dir / "seeds" / "docs" / "knowledge").mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "pack-a"\nversion = "0.1.0"\nlint-seeds = true\n',
        encoding="utf-8",
        newline="\n",
    )
    for rel, content in seeds.items():
        p = pack_dir / "seeds" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    assert l029, "expected CAT-L029 for non-empty patterns.jsonl"
    assert any("must be empty" in d.message for d in l029)


def test_check_seeds_clean(tmp_path, monkeypatch):
    """Opt-in pack with clean seeds → no CAT-L029."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_with_seeds(
        tmp_path, "pack-a", lint_seeds=True,
        seeds={"AGENTS.md": "<project-name>"},
    )
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L029" for d in result.diagnostics)


def test_check_seeds_symlinked_dir_skipped(tmp_path, monkeypatch):
    """A symlinked directory inside seeds/ must not be traversed by the linter.

    On Python 3.11/3.12, Path.rglob() follows symlinked directories;
    os.walk(followlinks=False) does not. This test pins the fix: files
    reachable only through a symlinked dir produce no CAT-L029 violations.

    Skipped on platforms where os.symlink is unavailable (some Windows configs).
    """
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack_with_seeds(tmp_path, "pack-a", lint_seeds=True,
                                    seeds={"AGENTS.md": "<project-name>"})
    # Plant a symlinked directory inside seeds/ pointing to /etc (or tmp).
    # On Windows, creating symlinks may require elevated privileges — skip.
    link = pack_dir / "seeds" / "evil-link"
    target = tmp_path / "outside"
    target.mkdir()
    (target / "passwd").write_text("root:x:0:0\n", encoding="utf-8", newline="\n")
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform/filesystem")
    result = lint_catalogue(tmp_path)
    l029 = [d for d in result.diagnostics if d.code == "CAT-L029"]
    # The planted AGENTS.md is clean → should be zero violations.
    # If the symlinked dir were traversed, "passwd" would produce an
    # "unknown seed file" violation.
    assert not l029, (
        "symlinked directory inside seeds/ must not be traversed: "
        + "; ".join(d.message for d in l029)
    )


def test_check_seeds_symlinked_file_skipped(tmp_path, monkeypatch):
    """A symlinked file inside seeds/ must not be read by the linter."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack_with_seeds(tmp_path, "pack-a", lint_seeds=True,
                                    seeds={"AGENTS.md": "<project-name>"})
    outside = tmp_path / "outside.md"
    outside.write_text("<project-name>", encoding="utf-8", newline="\n")
    link = pack_dir / "seeds" / "AGENTS.md"
    link.unlink()
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform/filesystem")
    # The symlinked AGENTS.md is skipped → no violation (it could have been
    # a clean file, so no violation is expected either way; the key invariant
    # is that we do not read through a symlink).
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L029" for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Task 4 — _PackRules._check_first_value() (CAT-L030)
# ---------------------------------------------------------------------------

_FV_SECTION = """
[pack.first-value]
audience-posture = "technical"
surfaces = ["claude"]
prerequisites = []
verification = "run tests"
recovery = "revert the change"
"""


def _add_pack_fv(root: Path, name: str, *, pack_toml_extra: str = "") -> Path:
    """Add a pack with allowed-adapters = [\"claude\"] and optional extra TOML."""
    pack_dir = root / "packs" / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\n'
        f'[pack.install]\nallowed-adapters = ["claude"]\n'
        f'{pack_toml_extra}\n',
        encoding="utf-8",
        newline="\n",
    )
    return pack_dir


def test_check_first_value_missing_section(tmp_path, monkeypatch):
    """Pack without [pack.first-value] → silently skipped (adoption is opt-in)."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack_fv(tmp_path, "pack-a")
    result = lint_catalogue(tmp_path)
    l030 = [d for d in result.diagnostics if d.code == "CAT-L030"]
    assert not l030, "expected no CAT-L030 when [pack.first-value] section is absent"


def test_check_first_value_level_a_missing_field(tmp_path, monkeypatch):
    """Pack with first-value but missing 'verification' → CAT-L030."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    # missing 'verification'
    extra = (
        "[pack.first-value]\n"
        'audience-posture = "technical"\n'
        'surfaces = ["claude"]\n'
        "prerequisites = []\n"
        'recovery = "revert"\n'
    )
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    l030 = [d for d in result.diagnostics if d.code == "CAT-L030"]
    assert l030, "expected CAT-L030 for missing Level A field"
    assert any("verification" in d.message for d in l030)


def test_check_first_value_level_b_required_when_flagged(tmp_path, monkeypatch):
    """Pack with level-b = true missing starter-task → CAT-L030."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    extra = (
        "[pack.first-value]\n"
        'audience-posture = "technical"\n'
        'surfaces = ["claude"]\n'
        "prerequisites = []\n"
        'verification = "run tests"\n'
        'recovery = "revert"\n'
        "level-b = true\n"
        # missing starter-task, starter-prompt, expected-result, next-action
    )
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    l030 = [d for d in result.diagnostics if d.code == "CAT-L030"]
    assert l030, "expected CAT-L030 for missing Level B fields"
    assert any("starter-task" in d.message for d in l030)


def test_check_first_value_writes_to_repo_gate(tmp_path, monkeypatch):
    """Pack with writes-to-repo = true missing safety-gate → CAT-L030."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    extra = (
        "[pack.first-value]\n"
        'audience-posture = "technical"\n'
        'surfaces = ["claude"]\n'
        "prerequisites = []\n"
        'verification = "run tests"\n'
        'recovery = "revert"\n'
        "writes-to-repo = true\n"
        # missing safety-gate
    )
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    l030 = [d for d in result.diagnostics if d.code == "CAT-L030"]
    assert l030, "expected CAT-L030 for missing safety-gate"
    assert any("safety-gate" in d.message for d in l030)


def test_check_first_value_tutorial_missing_file(tmp_path, monkeypatch):
    """Pack declares tutorial that doesn't exist → CAT-L030 mentioning 'does not exist'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    extra = (
        "[pack.first-value]\n"
        'audience-posture = "technical"\n'
        'surfaces = ["claude"]\n'
        "prerequisites = []\n"
        'verification = "run tests"\n'
        'recovery = "revert"\n'
        'tutorial = "guides/tutorials/nonexistent.md"\n'
    )
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    l030 = [d for d in result.diagnostics if d.code == "CAT-L030"]
    assert l030, "expected CAT-L030 for missing tutorial file"
    assert any("does not exist" in d.message for d in l030)


def test_check_first_value_clean(tmp_path, monkeypatch):
    """Pack with complete valid first-value section → no CAT-L030."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    extra = (
        "[pack.first-value]\n"
        'audience-posture = "technical"\n'
        'surfaces = ["claude"]\n'
        "prerequisites = []\n"
        'verification = "run tests"\n'
        'recovery = "revert the change"\n'
    )
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L030" for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Task 5 — _PackRules._check_credentialed_skills() (CAT-L031)
# ---------------------------------------------------------------------------


def _add_credentialed_skill(
    pack_dir: Path,
    skill_name: str,
    *,
    skill_md_content: str,
    script_content: str | None = None,
) -> None:
    """Add a credentialed skill to pack_dir/.apm/skills/<skill_name>/."""
    skill_dir = pack_dir / ".apm" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8", newline="\n")
    if script_content is not None:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "run.py").write_text(script_content, encoding="utf-8", newline="\n")


_CLEAN_SKILL_MD = """\
---
name: my-skill
description: Does something
metadata:
  credentialed: false
---

# My Skill
"""

# Flat frontmatter — auth: cli (matches actual skill format; no nested auth block)
_CLI_SKILL_MD_TEMPLATE = """\
---
name: {name}
description: A credentialed CLI skill
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: cli
---

### Security rules (non-negotiable)

**Never** read that store, print it, or echo the token
**Never** put the token on the command line
do not run it for them

## Usage

Call with: `my-tool --flag value`
"""

# Flat frontmatter — auth: env with namespace + keys as flat fields
_ENV_SKILL_MD_TEMPLATE = """\
---
name: {name}
description: A credentialed env skill
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: env
  namespace: MY_TOOL
  keys: ["API_KEY"]
---

### Security rules (non-negotiable)

**Never** print, log, or echo the value of MY_TOOL_API_KEY
**Never** put the credential on the command line
Do not write the value anywhere yourself

## Usage

Call with MY_TOOL_API_KEY set.
"""


def test_check_credentialed_skills_no_skills_dir(tmp_path, monkeypatch):
    """Pack without .apm/skills/ → no CAT-L031."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L031" for d in result.diagnostics)


def test_check_credentialed_skills_missing_security_heading(tmp_path, monkeypatch):
    """Credentialed skill missing '### Security rules (non-negotiable)' heading → CAT-L031."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    # Flat frontmatter (required by parser), no security heading
    skill_md = """\
---
name: cred-skill
description: Credentialed
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: cli
---

## Usage

No security section here.
"""
    _add_credentialed_skill(pack_dir, "cred-skill", skill_md_content=skill_md)
    result = lint_catalogue(tmp_path)
    l031 = [d for d in result.diagnostics if d.code == "CAT-L031"]
    assert l031, "expected CAT-L031 for missing security heading"
    assert any("Security" in d.message or "security" in d.message for d in l031)


def test_check_credentialed_skills_argv_ban(tmp_path, monkeypatch):
    """Credentialed skill script uses banned argv flag → CAT-L031 mentioning 'argv-borne credential flag'."""  # noqa: E501
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    _add_credentialed_skill(
        pack_dir, "cred-skill",
        skill_md_content=_CLI_SKILL_MD_TEMPLATE.format(name="cred-skill"),
        script_content=(
            "import argparse\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--api-key')\n"
        ),
    )
    result = lint_catalogue(tmp_path)
    l031 = [d for d in result.diagnostics if d.code == "CAT-L031"]
    assert l031, "expected CAT-L031 for argv-borne credential flag"
    assert any("argv-borne credential flag" in d.message for d in l031)


def test_check_credentialed_skills_env_missing_env_read(tmp_path, monkeypatch):
    """Env broker skill missing expected os.environ read → CAT-L031."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    # namespace=MY_TOOL + keys=["API_KEY"] → expected env read is MY_TOOL_API_KEY
    # script does NOT read MY_TOOL_API_KEY → CAT-L031
    _add_credentialed_skill(
        pack_dir, "env-skill",
        skill_md_content=_ENV_SKILL_MD_TEMPLATE.format(name="env-skill"),
        script_content="import os\nval = os.environ.get('SOME_OTHER_VAR')\nprint(val)\n",
    )
    result = lint_catalogue(tmp_path)
    l031 = [d for d in result.diagnostics if d.code == "CAT-L031"]
    assert l031, "expected CAT-L031 for missing env read"


def test_check_credentialed_skills_denyset_incomplete(tmp_path, monkeypatch):
    """D2b: deny-set with 2+ banned flags but missing others → CAT-L031 mentioning 'deny-set'."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    # Flat frontmatter: auth: cli, primitive-class: credentialed-cli
    skill_md = _CLI_SKILL_MD_TEMPLATE.format(name="cli-skill")
    # deny-set has 2 banned flags (--token, --api-key) but is missing the other 4
    # → denyset_flag_groups yields {'token', 'api_key'}, len >= 2 → D2b fires
    script = (
        "import argparse\n"
        "_DENY_FLAGS = frozenset({'--token', '--api-key'})\n"
    )
    _add_credentialed_skill(
        pack_dir, "cli-skill", skill_md_content=skill_md, script_content=script
    )
    result = lint_catalogue(tmp_path)
    l031 = [d for d in result.diagnostics if d.code == "CAT-L031"]
    assert l031, "expected CAT-L031 for deny-set incomplete"
    assert any("deny-set" in d.message.lower() for d in l031)


def test_check_credentialed_skills_dotfile_read(tmp_path, monkeypatch):
    """D3: script reads .agentbundle/credentials.env via AST path chain → CAT-L031 mentioning 'dotfile'."""  # noqa: E501
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    # auth: cli avoids env-read enforcement (just D1 + D3 checks apply)
    skill_md = _CLI_SKILL_MD_TEMPLATE.format(name="dotfile-skill")
    # Script reads credentials dotfile inline (path chain must be on the same expression as read_text)  # noqa: E501
    script = (
        "from pathlib import Path\n"
        "content = (Path.home() / '.agentbundle' / 'credentials.env').read_text()\n"
    )
    _add_credentialed_skill(
        pack_dir, "dotfile-skill", skill_md_content=skill_md, script_content=script
    )
    result = lint_catalogue(tmp_path)
    l031 = [d for d in result.diagnostics if d.code == "CAT-L031"]
    assert l031, "expected CAT-L031 for dotfile read"
    assert any("dotfile" in d.message.lower() for d in l031)


def test_check_credentialed_skills_clean(tmp_path, monkeypatch):
    """Pack with non-credentialed skill → no CAT-L031."""
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    pack_dir = _add_pack(tmp_path, "pack-a", pack_toml=_PACK_A_TOML)
    _add_credentialed_skill(pack_dir, "my-skill", skill_md_content=_CLEAN_SKILL_MD)
    result = lint_catalogue(tmp_path)
    assert not any(d.code == "CAT-L031" for d in result.diagnostics)
