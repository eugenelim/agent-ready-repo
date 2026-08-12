"""Unit tests for agentbundle.catalogue_tooling.verify (Wave 3, ini-005).

Coverage:
  - verify_catalogue(root, pack=None) -> VerifyResult
  - render_json(result) -> str
  - render_table(result) -> str
  - agentbundle catalogue verify CLI (subprocess smoke tests)

Monkeypatching strategy:
  - test_verify_bad_pack_lint_fails_step2 patches load_catalogue_config to
    return a non-None mock so that step 2 (lint) is reached, then patches
    lint_catalogue to return an ERROR result — triggering the CAT-V-002 path
    without needing a fully-valid catalogue.toml on disk.
  - Structural and formatter tests use focused real or constructed results.
    Dedicated missing-config tests prove lint failure reaches verify and its
    CLI JSON surface.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from agentbundle.catalogue_tooling.results import Diagnostic, LintResult, Severity, VerifyResult
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml
from agentbundle.catalogue_tooling.verify import (
    render_json,
    render_table,
    verify_catalogue,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(*, ok: bool = True, diagnostics: list[Diagnostic] | None = None) -> VerifyResult:
    """Construct a VerifyResult directly for formatter tests."""
    return VerifyResult(
        ok=ok,
        diagnostics=diagnostics or [],
        schema_version=1,
        command="catalogue verify",
        operation="source-checkout",
        agentbundle_version="test",
        catalogue_schema_version=1,
    )


def _make_error_diag(code: str = "CAT-V-999", message: str = "test error") -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        pack=None,
        path=None,
        line=None,
        col=None,
        message=message,
        remediation=None,
    )


# ---------------------------------------------------------------------------
# verify_catalogue — structural / happy-path
# ---------------------------------------------------------------------------


def test_verify_empty_dir_reports_missing_catalogue(tmp_path):
    """An empty source root fails verify through the lint step."""
    result = verify_catalogue(tmp_path)
    assert result.ok is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CAT-V-002"]


def test_verify_non_catalogue_with_agents_file_reports_missing_catalogue(tmp_path):
    """An unrelated AGENTS.md does not make a config-less root a catalogue."""
    (tmp_path / "AGENTS.md").write_text("# Catalogue\n", encoding="utf-8", newline="\n")
    result = verify_catalogue(tmp_path)
    assert result.ok is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CAT-V-002"]


def test_verify_invalid_config_path_reports_diagnostic(tmp_path):
    """Invalid configured paths remain inside the verify result contract."""
    config = emit_catalogue_toml(
        name="test-catalogue",
        display_name="Test Catalogue",
        description="A catalogue fixture with an invalid configured path.",
        minimum_agentbundle_version="0.33.0",
        owner_name="Example Maintainer",
        preferred_adapter="kiro-ide",
    ).replace('packs        = "packs"', 'packs        = "../outside"')
    (tmp_path / "catalogue.toml").write_text(config, encoding="utf-8", newline="\n")
    (tmp_path / "packs").mkdir()

    result = verify_catalogue(tmp_path)

    assert result.ok is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CAT-V-001"]


def test_verify_result_has_expected_fields(tmp_path):
    """VerifyResult contains all expected fields."""
    result = verify_catalogue(tmp_path)
    assert hasattr(result, "schema_version")
    assert hasattr(result, "command")
    assert hasattr(result, "operation")
    assert hasattr(result, "agentbundle_version")
    assert hasattr(result, "ok")
    assert hasattr(result, "diagnostics")


def test_verify_command_is_catalogue_verify(tmp_path):
    """result.command == 'catalogue verify'."""
    result = verify_catalogue(tmp_path)
    assert result.command == "catalogue verify"


# ---------------------------------------------------------------------------
# verify_catalogue — lint failure path
# ---------------------------------------------------------------------------


def test_verify_bad_pack_lint_fails_step2(tmp_path, monkeypatch):
    """Step 2 (lint) wraps lint errors as CAT-V-002 diagnostics → ok=False.

    Monkeypatch strategy:
      1. load_catalogue_config → returns a minimal non-None mock so the lint
         step is not skipped (config is not None).
      2. lint_catalogue → returns a LintResult with one ERROR diagnostic so
         that _step_lint wraps it as CAT-V-002.
    The loop stops after step 2 (continue_on_error defaults to False), so no
    later steps (including the build step) are reached.
    """

    class _MockConfig:
        schema = 1
        paths = None
        distribution = None

    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.config.load_catalogue_config",
        lambda root: _MockConfig(),
    )

    error_lint_result = LintResult(
        ok=False,
        diagnostics=[_make_error_diag(code="CAT-L-001", message="simulated lint error")],
        schema_version=1,
        command="catalogue lint",
        operation="source-checkout",
        agentbundle_version="test",
        catalogue_schema_version=1,
    )
    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.lint.lint_catalogue",
        lambda root, pack=None: error_lint_result,
    )

    result = verify_catalogue(tmp_path)

    assert not result.ok
    assert any("CAT-V-002" in d.code for d in result.diagnostics)


# ---------------------------------------------------------------------------
# render_json
# ---------------------------------------------------------------------------


def test_render_json(tmp_path):
    """render_json returns valid JSON with an 'ok' key."""
    result = _make_result(ok=True)
    output = render_json(result)
    doc = json.loads(output)
    assert "ok" in doc
    assert doc["ok"] is True


def test_render_json_contains_all_fields():
    """render_json output contains all VerifyResult fields."""
    result = _make_result(ok=False, diagnostics=[_make_error_diag()])
    doc = json.loads(render_json(result))
    for key in (
        "schema_version",
        "command",
        "operation",
        "agentbundle_version",
        "ok",
        "diagnostics",
    ):
        assert key in doc, f"missing key {key!r} in render_json output"


# ---------------------------------------------------------------------------
# render_table
# ---------------------------------------------------------------------------


def test_render_table_ok():
    """A result with no diagnostics → 'catalogue verify: ok'."""
    result = _make_result(ok=True)
    output = render_table(result)
    assert output == "catalogue verify: ok"


def test_render_table_errors():
    """A result with one error diagnostic → table contains the diagnostic code."""
    diag = _make_error_diag(code="CAT-V-999", message="something broke")
    result = _make_result(ok=False, diagnostics=[diag])
    output = render_table(result)
    assert "CAT-V-999" in output


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


def test_cli_verify_help():
    """agentbundle catalogue verify --help exits 0 and mentions --root."""
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "verify", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--root" in proc.stdout


def test_cli_verify_format_json(tmp_path):
    """CLI JSON reports the missing-catalogue lint failure."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "verify",
            "--root",
            str(tmp_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stderr
    doc = json.loads(proc.stdout)
    assert doc["ok"] is False
    assert [diagnostic["code"] for diagnostic in doc["diagnostics"]] == ["CAT-V-002"]


# ---------------------------------------------------------------------------
# Task 6: _step_agent_artifacts (step 11)
# ---------------------------------------------------------------------------


def test_step_agent_artifacts_no_claude_dir(tmp_path):
    """No .claude/ dir → empty list (graceful skip)."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert result == []


def test_step_agent_artifacts_skill_missing_name(tmp_path):
    """Skill with no name key → CAT-V-011, 'frontmatter missing required key: name'."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\ndescription: A skill\n---\nBody text.\n", encoding="utf-8", newline="\n"
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert any(
        d.code == "CAT-V-011" and "frontmatter missing required key: name" in d.message
        for d in result
    )


def test_step_agent_artifacts_agent_missing_model(tmp_path):
    """Agent without model → CAT-V-011."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "my-agent.md").write_text(
        "---\nname: my-agent\ndescription: An agent\n---\nAgent body.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-011" for d in result)


def test_step_agent_artifacts_credentialed_skill_bad_auth(tmp_path):
    """Skill with invalid auth value → CAT-V-011."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    skill_dir = tmp_path / ".claude" / "skills" / "cred-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: cred-skill\ndescription: A skill\nmetadata:\n  auth: bad-broker\n---\nBody.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-011" for d in result)


def test_step_agent_artifacts_unknown_skill_key(tmp_path):
    """Skill with unknown frontmatter key → CAT-V-011."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: A skill\nunknown-key: value\n---\nBody.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-011" for d in result)


def test_step_agent_artifacts_broken_link(tmp_path):
    """Skill with broken relative link → CAT-V-011."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: A skill\n---\nSee [this](missing.md).\n",
        encoding="utf-8",
        newline="\n",
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-011" for d in result)


def test_step_agent_artifacts_pyyaml_absent(tmp_path, monkeypatch):
    """When PyYAML unavailable → exactly one CAT-V-011 with 'PyYAML required'."""
    import builtins
    import sys as _sys

    monkeypatch.delitem(_sys.modules, "yaml", raising=False)

    real_import = builtins.__import__

    def _mock_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)

    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)

    assert len(result) == 1
    assert result[0].code == "CAT-V-011"
    assert result[0].severity == Severity.WARN
    assert "PyYAML required" in result[0].message


def test_step_agent_artifacts_no_module_scope_yaml():
    """verify.py must not import yaml at module scope."""
    import agentbundle.catalogue_tooling.verify as verify_mod

    assert not hasattr(verify_mod, "yaml")


def test_step_agent_artifacts_clean(tmp_path):
    """A clean skill → empty list."""
    from agentbundle.catalogue_tooling.verify import _step_agent_artifacts

    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: A clean skill\n---\nBody.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = _step_agent_artifacts(tmp_path, None, None, tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# Task 7: _step_plugin_manifests (step 13)
# ---------------------------------------------------------------------------


def test_step_plugin_manifests_no_dist_dir(tmp_path):
    """No dist/claude-plugins dir → empty list (graceful skip)."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    result = _step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert result == []


def test_step_plugin_manifests_invalid_manifest(tmp_path):
    """plugin.json failing schema → CAT-V-013."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    plugin_dir = tmp_path / "dist" / "claude-plugins" / "my-pack.claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps({}), encoding="utf-8", newline="\n")
    result = _step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-013" for d in result)


def test_step_plugin_manifests_marketplace_with_hooks(tmp_path):
    """marketplace.json with hooks in plugin entry → CAT-V-013."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    dist_dir = tmp_path / "dist" / "claude-plugins"
    dist_dir.mkdir(parents=True)
    marketplace = {"plugins": [{"name": "my-pack", "hooks": {"PostInstall": []}}]}
    (dist_dir / "marketplace.json").write_text(
        json.dumps(marketplace), encoding="utf-8", newline="\n"
    )
    result = _step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert any(d.code == "CAT-V-013" for d in result)


def test_step_plugin_manifests_clean(tmp_path):
    """Empty dist/claude-plugins dir (no manifests, no marketplace.json) → empty list."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    (tmp_path / "dist" / "claude-plugins").mkdir(parents=True)
    result = _step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert result == []


def test_step_plugin_manifests_pipeline_integration(tmp_path):
    """A fixture-built plugin manifest passes the packaged schema."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    fixture = (
        Path(__file__).resolve().parents[1]
        / "build_pipeline"
        / "fixtures"
        / "packs"
        / "core"
        / ".claude-plugin"
        / "plugin.json"
    )
    manifest = tmp_path / "dist" / "claude-plugins" / "core.claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    shutil.copyfile(fixture, manifest)
    result = _step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert result == [], [d.message for d in result]

    manifests = list((tmp_path / "dist" / "claude-plugins").rglob("*.claude-plugin/plugin.json"))
    assert len(manifests) >= 1, "no plugin.json files found — integration test is vacuous"


def test_step_selfhost_drift_maps_special_projection_failure_to_cat_v_015(tmp_path):
    """Step 15 exposes a failed special projection check as CAT-V-015."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from agentbundle.catalogue_tooling.verify import _step_selfhost_drift

    (tmp_path / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n', encoding="utf-8"
    )
    with patch(
        "agentbundle.catalogue_tooling.self_host.check_self_host",
        return_value=SimpleNamespace(ok=False),
    ):
        diagnostics = _step_selfhost_drift(
            tmp_path, object(), None, tmp_path / "tmp"
        )

    assert [diagnostic.code for diagnostic in diagnostics] == ["CAT-V-015"]
