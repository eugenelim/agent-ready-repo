"""Projection and end-to-end tests for workspace-status scripts/ (Order 1A).

Coverage:
- Source scripts exist in the pack.
- claude-code adapter projects both scripts under `.claude/skills/workspace-status/scripts/`.
- Real-tree invariant: both scripts present in the self-hosted projection.
- End-to-end installed CLI: exit 0, schema_version == 1, semantic counts plausible.
"""

from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from typing import Any

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.scope import shipped_adapters_from_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "adapter.toml"
CORE_PACK = REPO_ROOT / "packs" / "core"
SKILL_NAME = "workspace-status"
_SCRIPTS = ("workspace_status.py", "workspace_status_engine.py")
_SCHEMAS = REPO_ROOT / "contracts" / "jsonschema"
_PACKAGED_DATA = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"
)


def _load_workspace_status_engine():
    path = (
        CORE_PACK
        / ".apm"
        / "skills"
        / SKILL_NAME
        / "scripts"
        / "workspace_status_engine.py"
    )
    spec = importlib.util.spec_from_file_location(
        "workspace_status_engine_contract", path
    )
    engine = importlib.util.module_from_spec(spec)
    sys.modules["workspace_status_engine_contract"] = engine
    spec.loader.exec_module(engine)
    return engine


def test_t1_group2_schema_constants_match_engine() -> None:
    engine = _load_workspace_status_engine()
    workspace_schema = json.loads(
        (_SCHEMAS / "workspace-entry.schema.json").read_text(encoding="utf-8")
    )
    intake_schema = json.loads(
        (_SCHEMAS / "normalized-intake.schema.json").read_text(encoding="utf-8")
    )

    assert tuple(workspace_schema["required"]) == engine.WORKSPACE_ENTRY_REQUIRED_FIELDS
    assert tuple(
        workspace_schema["$defs"]["artifactKind"]["enum"]
    ) == engine.WORKSPACE_ARTIFACT_KINDS
    assert tuple(
        workspace_schema["$defs"]["surfaceRole"]["enum"]
    ) == engine.SURFACE_ROLES
    assert tuple(
        intake_schema["properties"]["action"]["enum"]
    ) == engine.NORMALIZED_INTAKE_ACTIONS


def test_workspace_status_package_runtimes_match_canonical_sources() -> None:
    status_engine = (
        CORE_PACK
        / ".apm"
        / "skills"
        / SKILL_NAME
        / "scripts"
        / "workspace_status_engine.py"
    )
    refresh_runtime = (
        CORE_PACK
        / ".apm"
        / "skills"
        / "work-intake"
        / "scripts"
        / "refresh.py"
    )

    assert (_PACKAGED_DATA / "workspace_status_engine.py").read_bytes() == (
        status_engine.read_bytes()
    )
    assert (_PACKAGED_DATA / "work_intake_refresh.py").read_bytes() == (
        refresh_runtime.read_bytes()
    )


def _documented_finding_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for code, reason, action in re.findall(
        r"^\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|$",
        text,
        flags=re.MULTILINE,
    ):
        rows[code] = (reason.strip(), action.strip())
    return rows


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _product_release_heading_version(text: str, name: str) -> str:
    # Version correspondence only. Either heading level is accepted because the
    # 59 pre-RFC-0095 nested entries include some artifacts' CURRENT release
    # (agentbundle 0.38.5 among them), so a `##`-only match would read a stale
    # free-standing heading. RFC-0095 D3 is enforced by the ratchet in
    # `test_no_new_release_is_nested_under_unreleased`, not here.
    match = re.search(
        rf"^#{{2,3}} \[{re.escape(name)}\]\[([^\]]+)\]", text, re.MULTILINE
    )
    assert match, f"missing {name} changelog heading"
    return match.group(1)


# RFC-0095 D3 baseline. 59 versioned entries were nested under a `## [Unreleased]`
# heading when D3 was accepted; every one is invisible to the `/now/` projection
# permanently, because nothing ever moves an entry out. Their promotion needs
# per-section artifact attribution (48 genuinely-unreleased bare sections are
# interleaved across three `[Unreleased]` regions) and is tracked in
# `workspace.toml [backlog].open` as `changelog-promote-marooned-entries`.
#
# This is a RATCHET, not a floor: it may only ever go DOWN. It is the mechanical
# enforcement of D3 — the correspondence check in
# `_product_release_heading_version` deliberately accepts either level.
_MAROONED_RELEASE_BASELINE = 59


def _nested_release_entries(text: str) -> list[str]:
    """Versioned changelog entries nested under an `[Unreleased]` heading."""
    nested: list[str] = []
    unreleased_level: int | None = None
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if not heading:
            continue
        level, title = len(heading.group(1)), heading.group(2)
        if unreleased_level is not None and level <= unreleased_level:
            unreleased_level = None
        if re.search(r"unreleased", title, re.IGNORECASE) and not re.match(
            r"\[[a-z0-9-]+\]\[", title
        ):
            unreleased_level = level
            continue
        if unreleased_level is not None and re.match(
            r"^\[.*\]\[.*\].*\d{4}-\d{2}-\d{2}", title
        ):
            nested.append(title)
    return nested


def test_no_new_release_is_nested_under_unreleased() -> None:
    """RFC-0095 D3: a released section is free-standing, never nested.

    Ratchet — this count may only decrease. A new release written as
    `### [artifact][version]` under `[Unreleased]` increments it and fails here.
    """
    changelog = (REPO_ROOT / "docs/product/changelog.md").read_text(encoding="utf-8")
    nested = _nested_release_entries(changelog)
    assert len(nested) <= _MAROONED_RELEASE_BASELINE, (
        f"{len(nested)} versioned entries are nested under `[Unreleased]`, above the "
        f"RFC-0095 D3 baseline of {_MAROONED_RELEASE_BASELINE}. A release carries a "
        f"version and a date, so it is written free-standing at `##` — nested entries "
        f"never publish to `/now/`. Newest nested entries: {nested[:3]}"
    )


def test_t3_work_loop_step0_requires_canonical_preflight() -> None:
    skill = (CORE_PACK / ".apm" / "skills" / "work-loop" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    normalized = " ".join(skill.split())
    assert "canonical.ready" in normalized
    assert "only queue-ready set" in normalized
    assert "matching `canonical.ready` evaluation" in normalized
    assert "matching `canonical.active`" in normalized
    assert "Raw workspace `[work].queue` membership never authorizes PLAN" in normalized
    assert "Raw `[work].active` membership never authorizes PLAN" in normalized
    assert "collect all paths in `[\"ini-NNN\".work].active`" not in skill
    assert "use it and proceed to PLAN" not in skill
    assert "Do not re-read raw `[work].queue` or `[work].active`" in normalized


def test_packaged_engine_projection_matches_canonical_source() -> None:
    source = (
        CORE_PACK
        / ".apm"
        / "skills"
        / SKILL_NAME
        / "scripts"
        / "workspace_status_engine.py"
    )
    packaged = (
        REPO_ROOT
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "_data"
        / "workspace_status_engine.py"
    )

    assert packaged.read_bytes() == source.read_bytes()


# STUB: AC8
def test_migration_planner_is_projected_byte_identically() -> None:
    source_engine = _load_workspace_status_engine()
    assert callable(getattr(source_engine, "compute_migration_plan", None))
    packaged_spec = importlib.util.spec_from_file_location(
        "packaged_workspace_status_migration", _PACKAGED_DATA / "workspace_status_engine.py"
    )
    packaged_engine = importlib.util.module_from_spec(packaged_spec)
    sys.modules[packaged_spec.name] = packaged_engine
    packaged_spec.loader.exec_module(packaged_engine)
    assert callable(getattr(packaged_engine, "compute_migration_plan", None))


# STUB: AC10
def test_migration_rollback_contract_is_projected_byte_identically() -> None:
    source_engine = _load_workspace_status_engine()
    assert callable(getattr(source_engine, "validate_migration_ledger_invariants", None))


def test_t4_repair_determinism_projection_and_release_surface() -> None:
    engine_path = (
        CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts" / "workspace_status_engine.py"
    )
    spec = importlib.util.spec_from_file_location("workspace_status_engine_t4", engine_path)
    engine = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("workspace_status_engine_t4", engine)
    spec.loader.exec_module(engine)

    fixture = Path(tempfile.mkdtemp())
    workspace_path = fixture / "workspace.toml"
    spec_dir = fixture / "docs" / "specs" / "t4"
    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    schema_dir = fixture / "schemas"
    adapter_contract = fixture / "adapter.toml"
    contract_versions_path = fixture / "contract_versions.json"

    def write_workspace(extra_ini: bool = False) -> None:
        extra = """
["ini-002"]
name = "Empty"
status = "active"
milestone = "M2"

["ini-002".work]
queue = []
active = []
shipped = []

["ini-002".shaping_queue]
active = []
backlog = []
""" if extra_ini else ""
        workspace_path.write_text(
            """\
["ini-001"]
name = "T4"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/t4/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "T4 deterministic identity", needs = []}]
active = []
shipped = []

["ini-001".shaping_queue]
active = []
backlog = []
""" + extra,
            encoding="utf-8",
        )

    def provenance_digest(metadata: object) -> str:
        return hashlib.sha256(
            json.dumps({
                "parent": metadata.parent,
                "ref": metadata.ref,
                "revision": metadata.revision,
                "refresh_conflict": metadata.refresh_conflict,
            }, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def derive_identity_inputs(
        *,
        schema_paths: list[Path],
        tracker_profile: dict[str, str],
        routing_version: str,
    ) -> tuple[object, dict[str, object]]:
        workspace_data = engine.parse_workspace(workspace_path)
        canonical_result = engine.run_canonical_reconciliation(workspace_data, fixture)
        status, status_fp = engine.extract_spec_status_with_fingerprint(spec_path)
        assert status == "Approved"
        assert status_fp is not None
        metadata = engine._metadata_from_root(
            fixture,
            canonical_result.memberships[0].entry,
        )
        contract_versions = tuple(json.loads(contract_versions_path.read_text()))
        return canonical_result, {
            "schema_ids": tuple(path.name for path in schema_paths),
            "schema_content_digests": {
                path.name: _sha256_file(path) for path in schema_paths
            },
            "contract_versions": contract_versions,
            "semantic_workspace_digest": hashlib.sha256(
                json.dumps(workspace_data, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "artifact_status_fingerprints": {"docs/specs/t4/spec.md": status_fp},
            "artifact_provenance_fingerprints": {
                "docs/specs/t4/spec.md": provenance_digest(metadata)
            },
            "adapter_contract_version": _sha256_file(adapter_contract),
            "tracker_profile": tracker_profile,
            "routing_configuration_version": routing_version,
        }

    try:
        spec_dir.mkdir(parents=True)
        schema_dir.mkdir()
        write_workspace()
        spec_path.write_text(
            "# Spec: T4\n\n- **Status:** Approved\n- **Brief:** none\n",
            encoding="utf-8",
        )
        plan_path.write_text("# Plan: T4\n", encoding="utf-8")
        schema_paths = [
            schema_dir / "workspace-entry.schema.json",
            schema_dir / "normalized-intake.schema.json",
        ]
        shutil.copy2(REPO_ROOT / "contracts/jsonschema/workspace-entry.schema.json", schema_paths[0])
        shutil.copy2(
            REPO_ROOT / "contracts/jsonschema/normalized-intake.schema.json",
            schema_paths[1],
        )
        shutil.copy2(CONTRACT_PATH, adapter_contract)
        contract_versions_path.write_text(json.dumps([
            engine.WORKSPACE_ENTRY_CONTRACT_VERSION,
            engine.NORMALIZED_INTAKE_CONTRACT_VERSION,
        ]), encoding="utf-8")
        canonical, base = derive_identity_inputs(
            schema_paths=schema_paths,
            tracker_profile={"id": "profile-a", "version": "profile-v1"},
            routing_version=engine.ROUTING_CONFIGURATION_VERSION,
        )
        assert engine.canonical_result_identity(canonical, **base) == engine.canonical_result_identity(
            canonical,
            **base,
        )
        baseline_identity = engine.canonical_result_identity(canonical, **base)
        baseline_snapshot = engine.canonical_result_snapshot(canonical, **base)
        baseline_classification = {
            key: baseline_snapshot[key]
            for key in ("evaluations", "legacy_memberships", "findings")
        }

        def assert_identity_changes(
            *,
            schema_paths_arg: list[Path] | None = None,
            tracker_profile: dict[str, str] | None = None,
            routing_version: str | None = None,
            classification_stable: bool = True,
        ) -> None:
            changed_canonical, changed_inputs = derive_identity_inputs(
                schema_paths=schema_paths_arg or schema_paths,
                tracker_profile=tracker_profile or {"id": "profile-a", "version": "profile-v1"},
                routing_version=routing_version or engine.ROUTING_CONFIGURATION_VERSION,
            )
            assert engine.canonical_result_identity(
                changed_canonical,
                **changed_inputs,
            ) != baseline_identity
            if classification_stable:
                changed_snapshot = engine.canonical_result_snapshot(
                    changed_canonical,
                    **changed_inputs,
                )
                assert {
                    key: changed_snapshot[key]
                    for key in ("evaluations", "legacy_memberships", "findings")
                } == baseline_classification

        renamed_schema = schema_dir / "workspace-entry-renamed.schema.json"
        schema_paths[0].rename(renamed_schema)
        schema_paths[0] = renamed_schema
        assert_identity_changes(schema_paths_arg=schema_paths)
        renamed_schema.rename(schema_dir / "workspace-entry.schema.json")
        schema_paths[0] = schema_dir / "workspace-entry.schema.json"

        schema_paths[0].write_text(
            schema_paths[0].read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        assert_identity_changes(schema_paths_arg=schema_paths)
        shutil.copy2(REPO_ROOT / "contracts/jsonschema/workspace-entry.schema.json", schema_paths[0])

        contract_versions_path.write_text(json.dumps([
            "workspace-entry.v2",
            engine.NORMALIZED_INTAKE_CONTRACT_VERSION,
        ]), encoding="utf-8")
        assert_identity_changes()
        contract_versions_path.write_text(json.dumps([
            engine.WORKSPACE_ENTRY_CONTRACT_VERSION,
            engine.NORMALIZED_INTAKE_CONTRACT_VERSION,
        ]), encoding="utf-8")

        write_workspace(extra_ini=True)
        assert_identity_changes()
        write_workspace()

        spec_path.write_text(
            "# Spec: T4\n\n- **Status:** Approved \n- **Brief:** none\n",
            encoding="utf-8",
        )
        assert_identity_changes()
        spec_path.write_text(
            "# Spec: T4\n\n- **Status:** Approved\n- **Brief:** none\n",
            encoding="utf-8",
        )

        spec_path.write_text(
            "# Spec: T4\n\n- **Status:** Approved\n- **Brief:** none\n- **Ref:** example-service://stable\n",
            encoding="utf-8",
        )
        assert_identity_changes()
        spec_path.write_text(
            "# Spec: T4\n\n- **Status:** Approved\n- **Brief:** none\n",
            encoding="utf-8",
        )

        adapter_contract.write_text(
            adapter_contract.read_text(encoding="utf-8") + "\n# local mutation\n",
            encoding="utf-8",
        )
        assert_identity_changes()
        shutil.copy2(CONTRACT_PATH, adapter_contract)

        assert_identity_changes(tracker_profile={"id": "profile-b", "version": "profile-v1"})
        assert_identity_changes(tracker_profile={"id": "profile-a", "version": "profile-v2"})
        assert_identity_changes(routing_version="workspace-routing.v2")

        workspace_for_subprocess = engine.parse_workspace(workspace_path)
        script = f"""
import importlib.util, sys
path = {str(engine_path)!r}
spec = importlib.util.spec_from_file_location('workspace_status_engine_t4_subprocess', path)
engine = importlib.util.module_from_spec(spec)
sys.modules.setdefault('workspace_status_engine_t4_subprocess', engine)
spec.loader.exec_module(engine)
workspace = {workspace_for_subprocess!r}
canonical = engine.run_canonical_reconciliation(workspace, None)
print(engine.canonical_result_identity(canonical, **{base!r}))
"""
        first = subprocess.check_output([sys.executable, "-c", script], text=True)
        second = subprocess.check_output([sys.executable, "-c", script], text=True)
        assert first == second
    finally:
        shutil.rmtree(fixture, ignore_errors=True)

    skill = (CORE_PACK / ".apm" / "skills" / SKILL_NAME / "SKILL.md").read_text(
        encoding="utf-8"
    )
    reference = (
        REPO_ROOT / "guides" / "core" / "reference" / "workspace-toml-schema.md"
    ).read_text(encoding="utf-8")
    finding_codes = set(engine._FINDING_NEXT_ACTIONS)
    for text in (skill, reference):
        documented_findings = _documented_finding_rows(text)
        assert set(documented_findings) >= finding_codes
        for code in finding_codes:
            reason, action = documented_findings[code]
            assert reason
            assert action
    for text in (skill, reference):
        assert "```toml coordination-receipts" in text
        assert "invalid_receipt" in text
        assert "refresh_conflict = false" in text
        receipt_blocks = re.findall(
            r"```toml coordination-receipts\n(.*?)\n```",
            text,
            flags=re.DOTALL,
        )
        assert receipt_blocks
        parsed_receipts = [
            receipt
            for block in receipt_blocks
            for receipt in tomllib.loads(block)["coordination_receipts"]
        ]
        assert any(
            set(receipt) == engine._COORDINATION_RECEIPT_FIELDS
            and receipt["accepted_revision"] == "remote-rev-9"
            for receipt in parsed_receipts
        )
        for receipt in parsed_receipts:
            assert set(receipt).issubset(engine._COORDINATION_RECEIPT_FIELDS)

    pack_version = tomllib.loads((CORE_PACK / "pack.toml").read_text(encoding="utf-8"))[
        "pack"
    ]["version"]
    plugin_version = json.loads(
        (CORE_PACK / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    assert pack_version == plugin_version
    marketplace = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    assert marketplace.exists()
    marketplace_plugins = json.loads(marketplace.read_text(encoding="utf-8"))["plugins"]
    core_plugins = [plugin for plugin in marketplace_plugins if plugin["name"] == "core"]
    assert core_plugins == []
    pyproject_version = tomllib.loads(
        (REPO_ROOT / "packages/agentbundle/pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    version_py = (
        REPO_ROOT / "packages/agentbundle/agentbundle/version.py"
    ).read_text(encoding="utf-8")
    version_match = re.search(r'^CLI_VERSION = "([^"]+)"$', version_py, re.MULTILINE)
    assert version_match
    assert pyproject_version == version_match.group(1)
    package_changelog = (
        REPO_ROOT / "packages/agentbundle/CHANGELOG.md"
    ).read_text(encoding="utf-8")
    assert re.search(
        rf"^## \[{re.escape(pyproject_version)}\] — \d{{4}}-\d{{2}}-\d{{2}}$",
        package_changelog,
        re.MULTILINE,
    )
    product_changelog = (REPO_ROOT / "docs/product/changelog.md").read_text(encoding="utf-8")
    assert _product_release_heading_version(product_changelog, "agentbundle") == pyproject_version
    assert _product_release_heading_version(product_changelog, "core") == pack_version

    for adapter_name in shipped_adapters_from_contract():
        assert adapter_name in ADAPTERS


def test_production_identity_derives_repository_inputs() -> None:
    engine_path = (
        CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts" / "workspace_status_engine.py"
    )
    spec = importlib.util.spec_from_file_location("workspace_status_engine_identity", engine_path)
    engine = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("workspace_status_engine_identity", engine)
    spec.loader.exec_module(engine)
    fixture = Path(tempfile.mkdtemp())
    try:
        contract_dir = fixture / "contracts"
        schema_dir = contract_dir / "jsonschema"
        spec_dir = fixture / "docs" / "specs" / "identity"
        schema_dir.mkdir(parents=True)
        spec_dir.mkdir(parents=True)
        workspace_path = fixture / "workspace.toml"
        workspace_template = '''\
["ini-001"]
name = "Identity"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/identity/spec.md", kind = "spec", source = {mode = "repo-origin", tracker_profile = {id = "%s", version = "%s"}}, summary = "%s", needs = []}]
active = []
shipped = []

["ini-001".shaping_queue]
active = []
backlog = []
'''
        workspace_path.write_text(
            workspace_template % ("profile-a", "v1", "initial"), encoding="utf-8"
        )
        spec_path = spec_dir / "spec.md"
        spec_path.write_text(
            "# Identity\n\n- **Status:** Approved\n- **Brief:** none\n",
            encoding="utf-8",
        )
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        workspace_schema = schema_dir / "workspace-entry.schema.json"
        intake_schema = schema_dir / "normalized-intake.schema.json"
        adapter_contract = contract_dir / "adapter.toml"
        shutil.copy2(
            REPO_ROOT / "contracts/jsonschema/workspace-entry.schema.json",
            workspace_schema,
        )
        shutil.copy2(
            REPO_ROOT / "contracts/jsonschema/normalized-intake.schema.json",
            intake_schema,
        )
        shutil.copy2(CONTRACT_PATH, adapter_contract)

        def identity() -> str:
            workspace = engine.parse_workspace(workspace_path)
            result = engine.run_canonical_reconciliation(workspace, fixture)
            return engine.canonical_repository_identity(workspace, result, fixture)

        baseline = identity()
        workspace_schema.write_text(
            workspace_schema.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        assert identity() != baseline
        shutil.copy2(
            REPO_ROOT / "contracts/jsonschema/workspace-entry.schema.json",
            workspace_schema,
        )
        adapter_contract.write_text(
            adapter_contract.read_text(encoding="utf-8") + "\n# mutation\n",
            encoding="utf-8",
        )
        assert identity() != baseline
        shutil.copy2(CONTRACT_PATH, adapter_contract)
        workspace_path.write_text(
            workspace_template % ("profile-b", "v1", "initial"), encoding="utf-8"
        )
        assert identity() != baseline
        workspace_path.write_text(
            workspace_template % ("profile-a", "v1", "summary-only change"),
            encoding="utf-8",
        )
        assert identity() == baseline
        spec_path.write_text(
            "# Identity\n\n- **Status:** Approved \n- **Brief:** none\n",
            encoding="utf-8",
        )
        assert identity() != baseline
        spec_path.write_text(
            "# Identity\n\n- **Status:** Approved\n- **Brief:** none\n",
            encoding="utf-8",
        )
        previous_routing_version = engine.ROUTING_CONFIGURATION_VERSION
        engine.ROUTING_CONFIGURATION_VERSION = "workspace-routing.v2"
        try:
            assert identity() != baseline
        finally:
            engine.ROUTING_CONFIGURATION_VERSION = previous_routing_version
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


class SourceInvariantTests(unittest.TestCase):
    """Precondition: source scripts must exist in the pack."""

    _scripts_dir = CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts"

    def test_scripts_directory_exists(self) -> None:
        self.assertTrue(
            self._scripts_dir.is_dir(),
            f"scripts/ directory not found at {self._scripts_dir}",
        )

    def test_cli_script_present_in_pack(self) -> None:
        self.assertTrue(
            (self._scripts_dir / "workspace_status.py").is_file(),
            "workspace_status.py not found in pack scripts/",
        )

    def test_engine_script_present_in_pack(self) -> None:
        self.assertTrue(
            (self._scripts_dir / "workspace_status_engine.py").is_file(),
            "workspace_status_engine.py not found in pack scripts/",
        )

    def test_old_engine_not_in_tools(self) -> None:
        stale = REPO_ROOT / "tools" / "workspace_status_engine.py"
        self.assertFalse(
            stale.exists(),
            f"Old engine copy still exists at {stale} — should have been git mv'd",
        )


class AdapterProjectionTests(unittest.TestCase):
    """Both scripts appear under every shipped adapter's projection."""

    contract: Any = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def _project_to_tmp(self, adapter_name: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        if adapter_name == "kiro":
            with self.assertWarnsRegex(
                DeprecationWarning,
                "deprecated alias for kiro-ide",
            ):
                ADAPTERS[adapter_name](CORE_PACK, self.contract, tmp)
        else:
            ADAPTERS[adapter_name](CORE_PACK, self.contract, tmp)
        return tmp

    def test_scripts_project_for_all_adapters(self) -> None:
        """scripts/ present under every shipped adapter's skill output."""
        for adapter_name in shipped_adapters_from_contract():
            with self.subTest(adapter=adapter_name):
                out = self._project_to_tmp(adapter_name)
                # Each adapter places skills under its own prefix; find by rglob.
                script_dirs = list(out.rglob(f"{SKILL_NAME}/scripts"))
                self.assertTrue(
                    len(script_dirs) >= 1,
                    f"{adapter_name}: no scripts/ directory found under {out}",
                )
                for name in _SCRIPTS:
                    found = any((d / name).is_file() for d in script_dirs)
                    self.assertTrue(
                        found,
                        f"{adapter_name}: {name} not found in any scripts/ dir",
                    )

    def test_skill_md_projects_for_claude_code(self) -> None:
        out = self._project_to_tmp("claude-code")
        skill_md = out / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md not projected alongside scripts/ for claude-code")

    def test_projected_cli_invokes_ok(self) -> None:
        """Projected CLI (claude-code) exits 0 against the real repo root (exercise)."""
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, f"CLI failed: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)

    def test_exit2_stderr_no_root_path(self) -> None:
        """Exit-2 stderr must not expose the --root path."""
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        # Pass an existing file (not a dir) as --root to force NotADirectoryError → exit 2.
        fake_file = out / "not_a_dir.txt"
        fake_file.write_bytes(b"")
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(fake_file)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r.returncode, 2, f"Expected exit 2, got {r.returncode}; stderr={r.stderr!r}")
        self.assertNotIn(str(fake_file), r.stderr,
            "exit-2 stderr exposes the --root path; it must be redacted to <root>")

    def test_projected_cli_against_fixture_workspace(self) -> None:
        """Projected CLI against a fixture workspace (not the real repo).

        Exercises the install path end-to-end: projects to a temp dir, invokes the
        CLI from a CWD outside the fixture, parses the JSON, and cross-checks
        key semantic fields against the source-engine CLI to detect installed/source
        divergence.
        """
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        fixture = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture, True)
        (fixture / "workspace.toml").write_bytes(b"# fixture\n")

        # Invoke from a CWD that is neither the fixture nor the repo root.
        outside_cwd = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside_cwd, True)
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(fixture)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(outside_cwd),
        )
        self.assertEqual(r.returncode, 0, f"CLI failed on fixture: {r.stderr}")
        installed = json.loads(r.stdout)
        self.assertEqual(installed.get("schema_version"), 1)
        self.assertTrue(installed.get("workspace_present"), "workspace_present should be True")

        # Cross-check against source engine — same fixture, same CWD.
        source_cli = CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        r_src = subprocess.run(
            [sys.executable, str(source_cli), "--root", str(fixture)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(outside_cwd),
        )
        self.assertEqual(r_src.returncode, 0, f"Source CLI failed: {r_src.stderr}")
        source = json.loads(r_src.stdout)
        for key in ("schema_version", "workspace_present", "work", "shaping", "reconciliation"):
            self.assertEqual(
                installed.get(key), source.get(key),
                f"Installed vs source engine mismatch on {key!r}",
            )


class RealTreeProjectionTests(unittest.TestCase):
    """Real-tree invariant: self-hosted scripts are byte-identical to source."""

    _source_scripts = CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts"
    _projected_script_dirs = (
        REPO_ROOT / ".claude" / "skills" / SKILL_NAME / "scripts",
        REPO_ROOT / ".agents" / "skills" / SKILL_NAME / "scripts",
    )

    def test_scripts_in_real_tree_projection(self) -> None:
        """Both self-hosted projections must match the pack sources.

        If this test fails, run `make build-self` (or
        `python3 -m agentbundle catalogue self-host --root . --write --force`)
        to regenerate the projection.
        """
        for projected_scripts in self._projected_script_dirs:
            self.assertTrue(
                projected_scripts.is_dir(),
                f"self-hosted scripts/ not found at {projected_scripts}",
            )
            for name in _SCRIPTS:
                with self.subTest(projection=projected_scripts, script=name):
                    projected = projected_scripts / name
                    source = self._source_scripts / name
                    self.assertTrue(
                        projected.is_file(),
                        f"{name} absent from self-hosted projection at {projected_scripts}",
                    )
                    self.assertEqual(
                        projected.read_bytes(),
                        source.read_bytes(),
                        f"{projected} is stale; regenerate the self-hosted projection",
                    )


class EndToEndCLITests(unittest.TestCase):
    """Installed CLI executed end-to-end; result recorded."""

    _cli = REPO_ROOT / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
    _skip_reason: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if not cls._cli.exists():
            cls._skip_reason = (
                f"Installed CLI not found at {cls._cli} — run make build-self"
            )
        else:
            cls._skip_reason = None

    def _skip_if_not_installed(self) -> None:
        if self._skip_reason:
            self.skipTest(self._skip_reason)

    def test_installed_cli_exit_0(self) -> None:
        """Installed CLI returns exit 0 against the real repo."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, f"CLI failed.\nstdout: {r.stdout[:500]}\nstderr: {r.stderr[:500]}")

    def test_installed_cli_schema_version(self) -> None:
        """Output is valid JSON with schema_version == 1."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)
        # Record semantic counts (printed to the test runner output)
        work = data.get("work", {})
        diag = data.get("diagnostics", {})
        print(
            f"\nAC17 record — installed CLI against real repo:\n"
            f"  exit_code=0  schema_version=1\n"
            f"  work.ready={len(work.get('ready', []))}"
            f"  work.blocked={len(work.get('blocked', []))}"
            f"  work.active={len(work.get('active', []))}"
            f"  work.shipped={len(work.get('shipped', []))}\n"
            f"  diagnostics.spec_files_read={diag.get('spec_files_read', '?')}",
            flush=True,
        )

    def test_installed_cli_workspace_present(self) -> None:
        """workspace_present is True for the real repo."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("workspace_present"), "workspace_present should be True for the real repo")


class RepositoryLifecycleRatchetTests(unittest.TestCase):
    """Ratchet the repository's own workspace.toml against lifecycle drift.

    Nothing else in CI runs the reconciliation engine over the real
    `workspace.toml`, so the fail-closed findings that core 2.12.4 drove to zero
    could silently return. This asserts the repaired state directly.

    The excluded codes are the known, deliberately non-empty compatibility
    backlog -- `unsupported_legacy` and `legacy_entry` are retained legacy
    records scheduled as later cleanup groups, and `missing_plan` /
    `unsatisfied_dependency` track real queued work. They are ratcheted by
    count below rather than required to be zero.
    """

    #: Legacy-shaped entries per collection, measured at core 2.12.4. Lower is
    #: always allowed; higher fails. `[backlog].closed` is deliberately absent:
    #: it is append-only history, every closure record there is legacy-shaped by
    #: established practice, and ratcheting it would nag on every future
    #: closure without preventing any drift.
    _LEGACY_SHAPE_CEILINGS = {
        "backlog.open": 160,
        "ini-002.shaping_queue.backlog": 1,
        "ini-002.work.shipped": 1,
    }

    @staticmethod
    def _is_legacy_shaped(entry: object) -> bool:
        """A bare string, or an inline table with no `path` key."""
        if isinstance(entry, str):
            return True
        return isinstance(entry, dict) and "path" not in entry

    def _legacy_counts(self) -> dict[str, int]:
        with (REPO_ROOT / "workspace.toml").open("rb") as handle:
            data = tomllib.load(handle)
        counts: dict[str, int] = {}
        for key, section in data.items():
            if not (isinstance(section, dict) and key.startswith("ini-")):
                continue
            for name in ("work", "shaping_queue", "brief_queue"):
                sub = section.get(name)
                if not isinstance(sub, dict):
                    continue
                for list_name, entries in sub.items():
                    if isinstance(entries, str):
                        entries = [entries] if entries else []
                    if not isinstance(entries, list):
                        continue
                    total = sum(1 for e in entries if self._is_legacy_shaped(e))
                    if total:
                        counts[f"{key}.{name}.{list_name}"] = total
        open_entries = data.get("backlog", {}).get("open", [])
        total = sum(1 for e in open_entries if self._is_legacy_shaped(e))
        if total:
            counts["backlog.open"] = total
        return counts

    def _canonical(self):
        engine = _load_workspace_status_engine()
        workspace = engine.parse_workspace(REPO_ROOT / "workspace.toml")
        return engine.run_canonical_reconciliation(workspace, REPO_ROOT)

    def test_no_fail_closed_lifecycle_findings(self) -> None:
        canonical = self._canonical()
        for code in (
            "missing_artifact",
            "inactive_initiative",
            "duplicate_membership",
            "invalid_artifact_path",
            "missing_dependency",
            "invalid_entry",
            "invalid_workspace",
            "dependency_cycle",
        ):
            offenders = sorted(f.path for f in canonical.findings if f.code == code)
            self.assertEqual(offenders, [], f"{code} reappeared: {offenders}")

    def test_legacy_shaped_entries_do_not_grow(self) -> None:
        """New work must be registered canonically, not by copying a neighbour.

        This is the write-side ratchet: legacy records are retained
        deliberately as later cleanup groups, but no collection may gain one.
        """
        counts = self._legacy_counts()
        for collection, total in sorted(counts.items()):
            ceiling = self._LEGACY_SHAPE_CEILINGS.get(collection, 0)
            self.assertLessEqual(
                total,
                ceiling,
                f"{collection} now holds {total} legacy-shaped entries "
                f"(ceiling {ceiling}). Register the new entry canonically as "
                f"{{path, kind, source, summary, needs}} -- see the shape "
                f"guidance at the top of workspace.toml. Do not raise this "
                f"ceiling to make the check pass.",
            )

    def test_tolerated_finding_counts_do_not_regress(self) -> None:
        """Fail-open finding classes stay bounded, so drift cannot hide in them."""
        canonical = self._canonical()
        counts = collections.Counter(f.code for f in canonical.findings)
        for code, ceiling in (
            ("legacy_entry", 2),
            ("unsatisfied_dependency", 8),
            ("missing_plan", 5),
            ("impossible_transition", 1),
        ):
            self.assertLessEqual(
                counts.get(code, 0),
                ceiling,
                f"{code} rose above its 2.12.4 ceiling: {counts.get(code, 0)}",
            )

    def test_every_legacy_finding_is_individually_attributable(self) -> None:
        """The 2.12.4 diagnostic property, asserted against the real file."""
        canonical = self._canonical()
        legacy = [f for f in canonical.findings if f.code == "unsupported_legacy"]
        identifiers = [f.path for f in legacy]
        self.assertNotIn("workspace.toml", identifiers,
                         "findings collapsed back onto the containing file")
        self.assertEqual(
            len(set(identifiers)), len(identifiers),
            "two legacy records share one identifier",
        )
