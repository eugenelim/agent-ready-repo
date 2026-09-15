"""Unit tests for catalogue init — Tasks 1-10.

Coverage map (per plan.md):
  T1 — Schema relaxation (optional contracts, owner)
  T2 — Config loading optional fields
  T3 — InitResult / FileAction types
  T4 — sync-defaults no-op when install-defaults-output absent
  T5 — Scaffold loader extensions (validate_manifest_paths etc.)
  T6 — TOML emitter
  T7 — Empty marketplace generator
  T8 — Init engine pure functions (metadata resolution, conflict detection)
  T9 — catalogue_init command handler shape
  T10 — CLI registration

Also: atomic_write symlink hardening (docs/specs/atomic-write-symlink-harden).
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# T1 — Schema relaxation
# ---------------------------------------------------------------------------


class TestSchemaRelaxation:
    def _load_schema(self) -> dict:
        here = Path(__file__).resolve()
        # tests/unit/ → tests/ → agentbundle-pkg/ → agentbundle-src/
        data = here.parents[2] / "agentbundle" / "_data" / "catalogue.schema.json"
        return json.loads(data.read_text(encoding="utf-8"))

    def test_contracts_is_not_required(self):
        schema = self._load_schema()
        paths_required = (
            schema["properties"]["catalogue"]["properties"]["paths"]["required"]
        )
        assert "contracts" not in paths_required

    def test_install_defaults_output_not_required(self):
        schema = self._load_schema()
        ab_required = (
            schema["properties"]["distribution"]["properties"]["agentbundle"]["required"]
        )
        assert "install-defaults-output" not in ab_required

    def test_default_source_not_required(self):
        schema = self._load_schema()
        ab_required = (
            schema["properties"]["distribution"]["properties"]["agentbundle"]["required"]
        )
        assert "default-source" not in ab_required

    def test_owner_schema_exists(self):
        schema = self._load_schema()
        owner_schema = (
            schema["properties"]["catalogue"]["properties"].get("owner")
        )
        assert owner_schema is not None

    def test_packs_still_required(self):
        schema = self._load_schema()
        paths_required = (
            schema["properties"]["catalogue"]["properties"]["paths"]["required"]
        )
        assert "packs" in paths_required

    def test_profiles_still_required(self):
        schema = self._load_schema()
        paths_required = (
            schema["properties"]["catalogue"]["properties"]["paths"]["required"]
        )
        assert "profiles" in paths_required


# ---------------------------------------------------------------------------
# T2 — Config optional fields
# ---------------------------------------------------------------------------

class TestConfigOptionalFields:
    def test_catalogue_paths_contracts_optional(self):
        from agentbundle.catalogue_tooling.config import CataloguePaths

        p = CataloguePaths(
            packs="packs",
            profiles="profiles",
            marketplace=".claude-plugin/marketplace.json",
            build_output="dist",
        )
        assert p.contracts is None

    def test_catalogue_paths_contracts_set_when_provided(self):
        from agentbundle.catalogue_tooling.config import CataloguePaths

        p = CataloguePaths(
            packs="packs",
            profiles="profiles",
            marketplace=".claude-plugin/marketplace.json",
            build_output="dist",
            contracts="contracts",
        )
        assert p.contracts == "contracts"

    def test_agentbundle_distribution_install_defaults_optional(self):
        from agentbundle.catalogue_tooling.config import AgentbundleDistribution, ArtifactoryConfig

        d = AgentbundleDistribution(
            preferred_adapter="claude-code",
            artifactory=ArtifactoryConfig(enabled=False),
        )
        assert d.install_defaults_output is None

    def test_agentbundle_distribution_default_source_optional(self):
        from agentbundle.catalogue_tooling.config import AgentbundleDistribution, ArtifactoryConfig

        d = AgentbundleDistribution(
            preferred_adapter="claude-code",
            artifactory=ArtifactoryConfig(enabled=False),
        )
        assert d.default_source is None

    def test_owner_optional_on_catalogue_config(self):
        from agentbundle.catalogue_tooling.config import (
            AgentbundleDistribution,
            ArtifactoryConfig,
            CatalogueBuild,
            CatalogueConfig,
            CataloguePackage,
            CataloguePaths,
            DistributionConfig,
        )

        cfg = CatalogueConfig(
            schema=1,
            name="test",
            display_name="Test",
            description="Test catalogue.",
            minimum_agentbundle_version="0.24.0",
            paths=CataloguePaths(
                packs="packs",
                profiles="profiles",
                marketplace=".claude-plugin/marketplace.json",
                build_output="dist",
            ),
            build=CatalogueBuild(
                recipes=["default"],
                self_host=False,
                claude_plugin_branch="main",
                marketplace_description="Test.",
            ),
            package=CataloguePackage(include=[], required=[]),
            distribution=DistributionConfig(
                agentbundle=AgentbundleDistribution(
                    preferred_adapter="claude-code",
                    artifactory=ArtifactoryConfig(enabled=False),
                )
            ),
        )
        assert cfg.owner is None

    def test_owner_set_when_provided(self):
        from agentbundle.catalogue_tooling.config import CatalogueOwner

        owner = CatalogueOwner(name="Acme Corp")
        assert owner.name == "Acme Corp"


# ---------------------------------------------------------------------------
# T3 — InitResult / FileAction types
# ---------------------------------------------------------------------------

class TestInitResultTypes:
    def test_file_action_values(self):
        from agentbundle.catalogue_tooling.results import FileAction

        assert FileAction.CREATE.value == "create"
        assert FileAction.ALREADY_PRESENT.value == "already-present"
        assert FileAction.CONFLICT.value == "conflict"

    def test_file_plan_shape(self):
        from agentbundle.catalogue_tooling.results import FileAction, FilePlan

        fp = FilePlan(
            path="catalogue.toml",
            kind="generated",
            action=FileAction.CREATE,
            sha256="abc123",
        )
        assert fp.conflict_reason is None

    def test_init_result_ok_shape(self):
        import dataclasses

        from agentbundle.catalogue_tooling.results import (
            InitCatalogueMeta,
            InitResult,
            InitSummary,
            InitVerification,
        )

        r = InitResult(
            ok=True,
            diagnostics=[],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version="0.24.0",
            catalogue_schema_version=1,
            dry_run=False,
            target="/tmp/test",
            catalogue=InitCatalogueMeta("n", "d", "desc", "o", "claude-code", "0.24.0"),
            files=[],
            verification=InitVerification(ok=True, diagnostic_count=0),
            summary=InitSummary(create=3, already_present=0, conflict=0, total=3),
        )
        assert r.ok
        assert r.agentbundle_version == "0.24.0"
        assert r.catalogue_schema_version == 1
        doc = dataclasses.asdict(r)
        assert "agentbundle_version" in doc
        assert "catalogue_schema_version" in doc

    def test_init_result_json_serializable(self):
        import dataclasses

        from agentbundle.catalogue_tooling.results import (
            InitCatalogueMeta,
            InitResult,
            InitSummary,
            InitVerification,
        )

        r = InitResult(
            ok=False,
            diagnostics=[],
            schema_version=1,
            command="catalogue init",
            operation="init",
            agentbundle_version="0.24.0",
            catalogue_schema_version=1,
            dry_run=True,
            target=".",
            catalogue=InitCatalogueMeta("n", "d", "desc", "o", "claude-code", "0.24.0"),
            files=[],
            verification=InitVerification(ok=False, diagnostic_count=0),
            summary=InitSummary(0, 0, 0, 0),
        )
        doc = dataclasses.asdict(r)
        assert json.dumps(doc)  # no TypeError


# ---------------------------------------------------------------------------
# T4 — sync-defaults no-op
# ---------------------------------------------------------------------------

class TestSyncDefaultsNoOp:
    def _make_config_without_defaults(self):
        from agentbundle.catalogue_tooling.config import (
            AgentbundleDistribution,
            ArtifactoryConfig,
            CatalogueBuild,
            CatalogueConfig,
            CataloguePackage,
            CataloguePaths,
            DistributionConfig,
        )

        return CatalogueConfig(
            schema=1,
            name="test",
            display_name="Test",
            description="Test.",
            minimum_agentbundle_version="0.24.0",
            paths=CataloguePaths(
                packs="packs",
                profiles="profiles",
                marketplace=".claude-plugin/marketplace.json",
                build_output="dist",
            ),
            build=CatalogueBuild(
                recipes=["default"],
                self_host=False,
                claude_plugin_branch="main",
                marketplace_description="Test.",
            ),
            package=CataloguePackage(include=[], required=[]),
            distribution=DistributionConfig(
                agentbundle=AgentbundleDistribution(
                    preferred_adapter="claude-code",
                    artifactory=ArtifactoryConfig(enabled=False),
                    install_defaults_output=None,
                )
            ),
        )

    def test_check_defaults_noop_when_not_configured(self, tmp_path):
        import agentbundle.catalogue_tooling.defaults as mod

        config = self._make_config_without_defaults()
        with patch.object(mod, "load_catalogue_config", return_value=config):
            result = mod.check_defaults(tmp_path)
        assert result.ok
        assert any("CAT-SD-000" in d.code for d in result.diagnostics)

    def test_write_defaults_noop_when_not_configured(self, tmp_path):
        import agentbundle.catalogue_tooling.defaults as mod

        config = self._make_config_without_defaults()
        with patch.object(mod, "load_catalogue_config", return_value=config):
            result = mod.write_defaults(tmp_path)
        assert result.ok
        assert not (tmp_path / "install-defaults.toml").exists()


# ---------------------------------------------------------------------------
# T5 — Scaffold loader extensions
# ---------------------------------------------------------------------------

class TestScaffoldLoaderExtensions:
    def test_validate_manifest_paths_accepts_safe(self):
        from agentbundle.scaffold import validate_manifest_paths

        manifest = {"files": {"packs/README.md": "abc", "profiles/AGENTS.md": "def"}}
        assert validate_manifest_paths(manifest) == []

    def test_validate_manifest_paths_rejects_absolute(self):
        from agentbundle.scaffold import validate_manifest_paths

        manifest = {"files": {"/etc/passwd": "abc"}}
        errors = validate_manifest_paths(manifest)
        assert errors

    def test_validate_manifest_paths_rejects_traversal(self):
        from agentbundle.scaffold import validate_manifest_paths

        manifest = {"files": {"../outside/file.txt": "abc"}}
        errors = validate_manifest_paths(manifest)
        assert errors

    def test_validate_manifest_paths_rejects_case_collision(self):
        from agentbundle.scaffold import validate_manifest_paths

        manifest = {"files": {"packs/README.md": "abc", "packs/readme.md": "def"}}
        errors = validate_manifest_paths(manifest)
        assert errors

    def test_validate_manifest_paths_rejects_windows_reserved(self):
        from agentbundle.scaffold import validate_manifest_paths

        for name in ("CON", "con", "PRN", "AUX", "NUL", "CON.md"):
            manifest = {"files": {name: "abc"}}
            errors = validate_manifest_paths(manifest)
            assert errors, f"Expected error for {name!r}"

    def test_list_files_with_hashes_matches_manifest(self):
        from agentbundle.scaffold import list_files_with_hashes, load_manifest

        hashes = list_files_with_hashes()
        manifest = load_manifest()
        assert hashes == dict(sorted(manifest["files"].items()))

    def test_verify_hashes_detailed_all_pass(self):
        from agentbundle.scaffold import verify_hashes_detailed

        results = verify_hashes_detailed()
        assert results
        for path, result in results.items():
            assert result is None, f"{path}: {result}"

    def test_read_file_returns_bytes(self):
        from agentbundle.scaffold import list_files, read_file

        files = list_files()
        assert files
        first = files[0]
        content = read_file(first)
        assert isinstance(content, bytes)
        assert len(content) > 0

    def test_find_unexpected_files_empty_for_clean_scaffold(self):
        from agentbundle.scaffold import find_unexpected_files

        unexpected = find_unexpected_files()
        assert unexpected == [], f"Unexpected scaffold files: {unexpected}"


# ---------------------------------------------------------------------------
# T6 — TOML emitter
# ---------------------------------------------------------------------------

class TestTomlEmitter:
    def test_emit_str_basic(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        assert emit_str("hello") == '"hello"'

    def test_emit_str_escapes_backslash(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        result = emit_str("path\\to\\file")
        assert "\\\\" in result

    def test_emit_str_escapes_quote(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        result = emit_str('say "hi"')
        assert '\\"' in result

    def test_emit_str_escapes_newline(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        result = emit_str("line1\nline2")
        assert "\\n" in result

    def test_emit_str_unicode_passthrough(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        result = emit_str("café")
        assert "café" in result

    def test_emit_str_escapes_del(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        assert emit_str("\x7f") == '"\\u007F"'

    def test_emit_str_escapes_c0_control(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_str

        # U+0001 (SOH) — forbidden unescaped in TOML 1.0 §2.1
        assert emit_str("\x01") == '"\\u0001"'

    def test_emit_bool(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_bool

        assert emit_bool(True) == "true"
        assert emit_bool(False) == "false"

    def test_emit_array_of_strings(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_array_of_strings

        result = emit_array_of_strings(["a", "b"])
        assert result == '["a", "b"]'

    def test_emit_array_of_strings_empty(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_array_of_strings

        assert emit_array_of_strings([]) == "[]"

    def test_catalogue_toml_deterministic(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

        kwargs = {
            "name": "test",
            "display_name": "Test",
            "description": "Test catalogue.",
            "minimum_agentbundle_version": "0.24.0",
            "owner_name": "Test Owner",
            "preferred_adapter": "claude-code",
        }
        assert emit_catalogue_toml(**kwargs) == emit_catalogue_toml(**kwargs)

    def test_catalogue_toml_no_credentials(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

        toml_str = emit_catalogue_toml(
            name="test",
            display_name="Test",
            description="Test.",
            minimum_agentbundle_version="0.24.0",
            owner_name="Test",
            preferred_adapter="claude-code",
        )
        # No token, API key, password in the output
        for bad in ("token", "api_key", "password", "secret", "bearer"):
            assert bad not in toml_str.lower(), f"Credential keyword found: {bad!r}"

    def test_catalogue_toml_valid_toml(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

        toml_str = emit_catalogue_toml(
            name="my-catalogue",
            display_name="My Catalogue",
            description="A test catalogue.",
            minimum_agentbundle_version="0.24.0",
            owner_name="My Org",
            preferred_adapter="claude-code",
        )
        data = tomllib.loads(toml_str)
        assert data["schema"] == 1
        assert data["catalogue"]["name"] == "my-catalogue"
        assert data["distribution"]["agentbundle"]["preferred-adapter"] == "claude-code"

    def test_catalogue_toml_marketplace_path(self):
        from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

        toml_str = emit_catalogue_toml(
            name="x",
            display_name="X",
            description="X.",
            minimum_agentbundle_version="0.24.0",
            owner_name="X",
            preferred_adapter="claude-code",
        )
        data = tomllib.loads(toml_str)
        assert data["catalogue"]["paths"]["marketplace"] == ".claude-plugin/marketplace.json"


# ---------------------------------------------------------------------------
# T7 — Empty marketplace generator
# ---------------------------------------------------------------------------

class TestEmptyMarketplaceGenerator:
    def test_empty_marketplace_valid_json(self):
        from agentbundle.catalogue_tooling.initialise import generate_empty_marketplace

        content = generate_empty_marketplace("test", "Test.", "Test Org")
        doc = json.loads(content)
        assert isinstance(doc, dict)

    def test_empty_marketplace_shape(self):
        from agentbundle.catalogue_tooling.initialise import generate_empty_marketplace

        content = generate_empty_marketplace("my-cat", "My catalogue.", "My Org")
        doc = json.loads(content)
        assert doc["name"] == "my-cat"
        assert doc["description"] == "My catalogue."
        assert doc["owner"]["name"] == "My Org"
        assert doc["plugins"] == []

    def test_empty_marketplace_deterministic(self):
        from agentbundle.catalogue_tooling.initialise import generate_empty_marketplace

        a = generate_empty_marketplace("x", "X.", "X")
        b = generate_empty_marketplace("x", "X.", "X")
        assert a == b

    def test_empty_marketplace_no_invented_url(self):
        from agentbundle.catalogue_tooling.initialise import generate_empty_marketplace

        content = generate_empty_marketplace("test", "Test.", "Test Org")
        doc = json.loads(content)
        text = json.dumps(doc)
        assert "http" not in text.lower()

    def test_empty_marketplace_utf8_final_newline(self):
        from agentbundle.catalogue_tooling.initialise import generate_empty_marketplace

        content = generate_empty_marketplace("test", "Test.", "Org")
        assert isinstance(content, bytes)
        assert content.endswith(b"\n")
        content.decode("utf-8")  # must be valid UTF-8


# ---------------------------------------------------------------------------
# T8 — Init engine pure functions
# ---------------------------------------------------------------------------

class TestMetadataResolution:
    def test_resolve_name_from_flag(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        meta, errors = resolve_metadata(tmp_path, name="my-cat", display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert not errors
        assert meta.name == "my-cat"

    def test_resolve_name_from_dir_basename(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        target = tmp_path / "acme-catalogue"
        target.mkdir()
        meta, errors = resolve_metadata(target, name=None, display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert not errors
        assert meta.name == "acme-catalogue"

    def test_resolve_name_invalid_requires_flag(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        # Basename consists only of dashes — _derive_name strips leading/trailing
        # dashes resulting in an empty string that fails _SAFE_NAME_RE.
        target = tmp_path / "---"
        meta, errors = resolve_metadata(target, name=None, display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert errors

    def test_resolve_display_name_humanize(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        target = tmp_path / "acme-catalogue"
        target.mkdir()
        meta, errors = resolve_metadata(target, name=None, display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert not errors
        assert meta.display_name == "Acme Catalogue"

    def test_resolve_description_default(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        target = tmp_path / "my-catalogue"
        target.mkdir()
        meta, errors = resolve_metadata(target, name=None, display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert not errors
        assert meta.description  # non-empty

    def test_resolve_owner_name_default(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        target = tmp_path / "test-cat"
        target.mkdir()
        meta, errors = resolve_metadata(target, name=None, display_name=None,
                                        description=None, owner_name=None, preferred_adapter=None)
        assert not errors
        assert meta.owner_name == meta.display_name

    def test_resolve_preferred_adapter_from_flag(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import resolve_metadata

        target = tmp_path / "test"
        target.mkdir()
        meta, errors = resolve_metadata(target, name="test", display_name=None,
                                        description=None, owner_name=None,
                                        preferred_adapter="kiro-ide")
        assert not errors
        assert meta.preferred_adapter == "kiro-ide"


class TestConflictDetection:
    def _make_planned(self, rel: str, content: bytes):
        from agentbundle.catalogue_tooling.initialise import PlannedFile
        return PlannedFile(rel_path=rel, kind="generated", content=content)

    def test_conflict_detection_create(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        planned = [self._make_planned("newfile.toml", b"content")]
        plans = classify_conflicts(tmp_path, planned)
        assert plans[0].action == FileAction.CREATE

    def test_conflict_detection_already_present(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        content = b"same content"
        (tmp_path / "file.md").write_bytes(content)
        planned = [self._make_planned("file.md", content)]
        plans = classify_conflicts(tmp_path, planned)
        assert plans[0].action == FileAction.ALREADY_PRESENT

    def test_conflict_detection_different_content(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        (tmp_path / "file.md").write_bytes(b"existing")
        planned = [self._make_planned("file.md", b"different")]
        plans = classify_conflicts(tmp_path, planned)
        assert plans[0].action == FileAction.CONFLICT

    def test_conflict_detection_symlink(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        link_target = tmp_path / "real.txt"
        link_target.write_bytes(b"real")
        (tmp_path / "link.md").symlink_to(link_target)
        planned = [self._make_planned("link.md", b"content")]
        plans = classify_conflicts(tmp_path, planned)
        assert plans[0].action == FileAction.CONFLICT

    def test_conflict_detection_directory_instead_of_file(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        (tmp_path / "subdir").mkdir()
        planned = [self._make_planned("subdir", b"content")]
        plans = classify_conflicts(tmp_path, planned)
        assert plans[0].action == FileAction.CONFLICT

    def test_case_insensitive_collision_among_planned(self, tmp_path):
        from agentbundle.catalogue_tooling.initialise import classify_conflicts
        from agentbundle.catalogue_tooling.results import FileAction

        planned = [
            self._make_planned("README.md", b"content1"),
            self._make_planned("readme.md", b"content2"),
        ]
        plans = classify_conflicts(tmp_path, planned)
        actions = {p.path: p.action for p in plans}
        # At least one of them is a conflict
        assert FileAction.CONFLICT in actions.values()


# ---------------------------------------------------------------------------
# T9 — command handler shape
# ---------------------------------------------------------------------------

class TestCatalogueInitHandler:
    def test_module_importable(self):
        import agentbundle.commands.catalogue_init  # noqa: F401

    def test_run_function_exists(self):
        from agentbundle.commands.catalogue_init import run

        assert callable(run)


# ---------------------------------------------------------------------------
# T10 — CLI registration
# ---------------------------------------------------------------------------

class TestCliRegistration:
    def test_catalogue_help_exits_0(self):
        import subprocess

        r = subprocess.run(
            [sys.executable, "-m", "agentbundle", "catalogue", "--help"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"catalogue --help exited {r.returncode}: {r.stderr}"

    def test_init_in_catalogue_help_output(self):
        import subprocess

        r = subprocess.run(
            [sys.executable, "-m", "agentbundle", "catalogue", "--help"],
            capture_output=True, text=True,
        )
        assert "init" in r.stdout, "init not listed in catalogue --help"

    def test_init_help_exits_0(self):
        import subprocess

        r = subprocess.run(
            [sys.executable, "-m", "agentbundle", "catalogue", "init", "--help"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"catalogue init --help exited {r.returncode}: {r.stderr}"

    def test_target_default_is_dot(self):
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["catalogue", "init"])
        assert args.target == "."

    def test_target_explicit_path(self):
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["catalogue", "init", "/some/path"])
        assert args.target == "/some/path"

    def test_init_all_flags_registered(self):
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args([
            "catalogue", "init",
            "--name", "test",
            "--display-name", "Test",
            "--description", "Test catalogue.",
            "--owner-name", "Test Org",
            "--preferred-adapter", "claude-code",
            "--dry-run",
            "--format", "json",
        ])
        assert args.name == "test"
        assert args.display_name == "Test"
        assert args.description == "Test catalogue."
        assert args.owner_name == "Test Org"
        assert args.preferred_adapter == "claude-code"
        assert args.dry_run is True
        assert args.format == "json"

    def test_target_in_path_bearing_attrs(self):
        from agentbundle.cli import _PATH_BEARING_ATTRS

        assert "target" in _PATH_BEARING_ATTRS


# ---------------------------------------------------------------------------
# atomic_write symlink hardening — docs/specs/atomic-write-symlink-harden
# ---------------------------------------------------------------------------

_FIXED = b"\xde\xad\xbe\xef\xde\xad\xbe\xef"
_FIXED_STAGING = f".abtmp-{_FIXED.hex()}"


class TestAtomicWriteSymlinkHardening:
    """`atomic_write` must not open a caller-derivable staging path."""

    @staticmethod
    def _atomic_write(dest: Path, content: bytes) -> None:
        from agentbundle.catalogue_tooling.initialise import atomic_write

        atomic_write(dest, content)

    def test_planted_symlink_at_legacy_staging_path_is_not_written_through(
        self, tmp_path: Path
    ) -> None:
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            (tmp_path / "catalogue.toml.abtmp").symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        self._atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"

    def test_entry_at_the_staging_path_refuses_instead_of_being_followed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pin the random component so the staging name is knowable, then occupy
        # it. Exclusive creation must refuse; following the link would overwrite
        # the victim, which is the whole defect.
        monkeypatch.setattr(os, "urandom", lambda n: _FIXED[:n])
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            (tmp_path / _FIXED_STAGING).symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        with pytest.raises(FileExistsError):
            self._atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"

    def test_staging_path_differs_between_calls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        staged: list[str] = []
        real_replace = os.replace

        def _spy(src, dst, **kwargs):  # type: ignore[no-untyped-def]
            staged.append(str(src))
            return real_replace(src, dst, **kwargs)

        monkeypatch.setattr(os, "replace", _spy)
        dest = tmp_path / "catalogue.toml"
        self._atomic_write(dest, b"ONE")
        self._atomic_write(dest, b"TWO")

        assert len(staged) == 2
        assert staged[0] != staged[1]

    def test_planted_symlink_at_dest_is_replaced_not_followed(
        self, tmp_path: Path
    ) -> None:
        victim = tmp_path / "victim.txt"
        victim.write_bytes(b"ORIGINAL")
        dest = tmp_path / "catalogue.toml"
        try:
            dest.symlink_to(victim)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks unavailable")

        self._atomic_write(dest, b"WRITTEN")

        assert victim.read_bytes() == b"ORIGINAL"
        assert not dest.is_symlink()
        assert dest.read_bytes() == b"WRITTEN"

    # The runner's own umask is almost always 022, where 0o644 and 0o664 are
    # indistinguishable — so a mode mutation would pass unnoticed unless the
    # test drives the umask itself. 002 is what separates them; 000 is what
    # separates "not world-writable" from "whatever write_bytes asked for".
    @pytest.mark.parametrize("umask", [0o022, 0o002, 0o077, 0o027, 0o007, 0o000])
    def test_written_file_keeps_the_umask_derived_mode(
        self, tmp_path: Path, umask: int
    ) -> None:
        previous = os.umask(umask)
        try:
            control = tmp_path / "control.toml"
            control.write_bytes(b"CONTROL")
            dest = tmp_path / "catalogue.toml"

            self._atomic_write(dest, b"WRITTEN")

            control_mode = stat.S_IMODE(control.stat().st_mode)
            written_mode = stat.S_IMODE(dest.stat().st_mode)
        finally:
            os.umask(previous)

        # The comparison value is a file the replaced implementation's own call
        # produced, in the same directory under the same umask. The `& 0o664`
        # is the one deliberate difference: the helper never requests the
        # other-write bit that `Path.write_bytes` asks for, so a null umask
        # cannot leave a catalogue file world-writable. Group-write survives,
        # because under umask 002 it is what a shared catalogue tree relies on.
        assert written_mode == control_mode & 0o664

    def test_successful_write_leaves_no_other_entry(self, tmp_path: Path) -> None:
        dest = tmp_path / "catalogue.toml"
        self._atomic_write(dest, b"WRITTEN")
        assert sorted(p.name for p in tmp_path.iterdir()) == ["catalogue.toml"]

    @pytest.mark.parametrize("failing_stage", ["write", "move"])
    def test_failure_propagates_and_leaves_no_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failing_stage: str
    ) -> None:
        # A sentinel instance, so the assertion below distinguishes "the
        # original error reached the caller" from "some OSError did".
        sentinel = OSError("stage refused")

        def _boom(*args: object, **kwargs: object) -> None:
            raise sentinel

        if failing_stage == "write":
            # A proxy around the real handle: the fd is still owned and closed,
            # but the write itself raises. Injecting only at the move would
            # leave an implementation that guards the move but not the write
            # looking correct.
            real_fdopen = os.fdopen

            class _FailingHandle:
                def __init__(self, inner: object) -> None:
                    self._inner = inner

                def write(self, data: bytes) -> int:
                    raise sentinel

                def __getattr__(self, name: str) -> object:
                    return getattr(self._inner, name)

                def __enter__(self) -> _FailingHandle:
                    return self

                def __exit__(self, *exc: object) -> bool:
                    self._inner.close()  # type: ignore[attr-defined]
                    return False

            monkeypatch.setattr(
                os, "fdopen", lambda *a, **k: _FailingHandle(real_fdopen(*a, **k))
            )
        else:
            monkeypatch.setattr(os, "replace", _boom)

        with pytest.raises(OSError) as caught:
            self._atomic_write(tmp_path / "catalogue.toml", b"WRITTEN")
        assert caught.value is sentinel
        assert list(tmp_path.iterdir()) == []

    def test_descriptor_is_closed_when_the_handle_cannot_be_opened(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # os.fdopen owns the descriptor only once it returns. If it raises,
        # only the helper can close it — and nothing else in this class would
        # notice the leak.
        opened: list[int] = []
        real_open = os.open
        sentinel = OSError("handle refused")

        def _record(*args: object, **kwargs: object) -> int:
            fd = real_open(*args, **kwargs)  # type: ignore[arg-type]
            opened.append(fd)
            return fd

        def _refuse(*args: object, **kwargs: object) -> None:
            raise sentinel

        monkeypatch.setattr(os, "open", _record)
        monkeypatch.setattr(os, "fdopen", _refuse)

        with pytest.raises(OSError) as caught:
            self._atomic_write(tmp_path / "catalogue.toml", b"WRITTEN")

        assert caught.value is sentinel
        assert len(opened) == 1
        with pytest.raises(OSError):  # EBADF — the descriptor was closed
            os.fstat(opened[0])
        assert list(tmp_path.iterdir()) == []

    def test_a_failed_cleanup_names_the_leftover_without_replacing_the_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sentinel = OSError("move refused")

        def _boom(*args: object, **kwargs: object) -> None:
            raise sentinel

        def _unlink_refused(*args: object, **kwargs: object) -> None:
            raise PermissionError("cleanup refused")

        monkeypatch.setattr(os, "replace", _boom)
        monkeypatch.setattr(Path, "unlink", _unlink_refused)

        with pytest.raises(OSError) as caught:
            self._atomic_write(tmp_path / "catalogue.toml", b"WRITTEN")

        assert caught.value is sentinel
        notes = getattr(caught.value, "__notes__", [])
        assert any(".abtmp-" in note for note in notes)
