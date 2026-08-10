"""Integration tests for agentbundle catalogue init (spec catalogue-tooling-init, Bucket 11).

Test matrix per plan.md § Task 14:
  - new-target full lifecycle
  - existing-repo unrelated files untouched
  - idempotence (second run all ALREADY_PRESENT)
  - conflict on catalogue.toml
  - conflict on packs/README.md
  - conflict on symlink
  - rollback on staged-verify failure (mocked)
  - dry-run: no target created
  - JSON output parses
  - no network request during init
  - dogfood: blank catalogue passes verify
  - dogfood: no host files leaked
  - list-packs zero after init
  - list-profiles zero after init
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_init(target: Path, **kwargs):
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    return init_catalogue(target=target, **kwargs)


def _assert_materialised_conformance_passes(target: Path) -> None:
    """Execute the exact suite delivered to the initialized catalogue."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/conformance", "-q"],
        cwd=target,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _run_cli_init(target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Invoke the public CLI from source with an isolated target."""
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(PACKAGE_ROOT)
        if not current
        else str(PACKAGE_ROOT) + os.pathsep + current
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "init",
            str(target),
            "--name",
            "cli-catalogue",
            *extra,
        ],
        cwd=PACKAGE_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------

def test_new_target_full_lifecycle(tmp_path):
    """Init into a fresh directory → ok=True, all files created, verify passes."""
    target = tmp_path / "new-catalogue"
    result = _run_init(target, name="new-catalogue")

    assert result.ok, f"Init failed: {result.diagnostics}"
    assert target.is_dir(), "Target directory not created"
    assert (target / "catalogue.toml").is_file()
    assert (target / ".claude-plugin" / "marketplace.json").is_file()
    assert (target / "packs" / "README.md").is_file()
    assert (target / "profiles" / "README.md").is_file()
    assert (target / "tests" / "conformance" / "test_pack_metadata.py").is_file()
    assert not (target / "tests" / "roster").exists()
    # Check summary
    assert result.summary.create > 0
    assert result.summary.conflict == 0
    # Verify passes
    from agentbundle.catalogue_tooling.verify import verify_catalogue
    vr = verify_catalogue(target)
    errors = [d.message for d in vr.diagnostics if d.severity.name == "ERROR"]
    assert vr.ok, f"Verify failed after init: {errors}"
    _assert_materialised_conformance_passes(target)


def test_default_init_cli_materialises_runnable_conformance(tmp_path: Path) -> None:
    """The documented bare init route delivers a suite that actually runs."""
    target = tmp_path / "cli-catalogue"

    result = _run_cli_init(target)

    assert result.returncode == 0, result.stdout + result.stderr
    _assert_materialised_conformance_passes(target)


def test_init_writes_valid_catalogue_toml(tmp_path):
    """Generated catalogue.toml is valid TOML with correct name."""
    import tomllib

    target = tmp_path / "toml-check"
    result = _run_init(target, name="toml-check")
    assert result.ok

    raw = (target / "catalogue.toml").read_text(encoding="utf-8")
    data = tomllib.loads(raw)
    assert data["catalogue"]["name"] == "toml-check"
    assert data["distribution"]["agentbundle"]["preferred-adapter"]


def test_init_writes_valid_marketplace_json(tmp_path):
    """Generated marketplace.json is valid JSON with correct shape."""
    import json

    target = tmp_path / "mp-check"
    result = _run_init(target, name="mp-check", owner_name="Test Org")
    assert result.ok

    raw = (target / ".claude-plugin" / "marketplace.json").read_bytes()
    doc = json.loads(raw)
    assert doc["name"] == "mp-check"
    assert doc["owner"]["name"] == "Test Org"
    assert doc["plugins"] == []


# ---------------------------------------------------------------------------
# Unrelated files untouched
# ---------------------------------------------------------------------------

def test_existing_repo_unrelated_files_untouched(tmp_path):
    """Files in the target not in the scaffold are left alone."""
    target = tmp_path / "existing"
    target.mkdir()
    existing = target / "existing-file.txt"
    existing.write_text("my existing content", encoding="utf-8")

    result = _run_init(target, name="existing")
    assert result.ok, f"Init failed: {result.diagnostics}"
    assert existing.read_text(encoding="utf-8") == "my existing content"


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------

def test_idempotence(tmp_path):
    """Second run on the same target → ok=True, all create files are now ALREADY_PRESENT."""
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "idempotent"

    r1 = _run_init(target, name="idempotent")
    assert r1.ok, f"First init failed: {r1.diagnostics}"

    r2 = _run_init(target, name="idempotent")
    assert r2.ok, f"Second init failed: {r2.diagnostics}"
    assert r2.summary.conflict == 0
    # All files from the plan should now be already-present
    for fp in r2.files:
        assert fp.action == FileAction.ALREADY_PRESENT, (
            f"{fp.path!r} is {fp.action} on second run"
        )


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_conflict_catalogue_toml_different_content(tmp_path):
    """catalogue.toml with different content blocks init."""
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "conflict-toml"
    target.mkdir()
    (target / "catalogue.toml").write_text(
        'schema = 0\n[catalogue]\nname = "other"', encoding="utf-8"
    )

    result = _run_init(target, name="conflict-toml")
    assert not result.ok
    conflicts = [fp for fp in result.files if fp.action == FileAction.CONFLICT]
    assert any(fp.path == "catalogue.toml" for fp in conflicts)


def test_conflict_packs_readme_different_content(tmp_path):
    """packs/README.md with different content blocks init."""
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "conflict-readme"
    target.mkdir()
    (target / "packs").mkdir()
    (target / "packs" / "README.md").write_text("# CUSTOM\n", encoding="utf-8")

    result = _run_init(target, name="conflict-readme")
    assert not result.ok
    conflicts = [fp for fp in result.files if fp.action == FileAction.CONFLICT]
    assert any(fp.path == "packs/README.md" for fp in conflicts)


def test_conflict_symlink_blocks_init(tmp_path):
    """A symlink at a planned path blocks init with conflict."""
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "conflict-symlink"
    target.mkdir()
    link_target = tmp_path / "elsewhere.toml"
    link_target.write_bytes(b"somewhere")
    (target / "catalogue.toml").symlink_to(link_target)

    result = _run_init(target, name="conflict-symlink")
    assert not result.ok
    conflicts = [fp for fp in result.files if fp.action == FileAction.CONFLICT]
    assert any(fp.path == "catalogue.toml" for fp in conflicts)


def test_single_conflict_blocks_all_writes(tmp_path):
    """When any file conflicts, no files are written at all."""
    target = tmp_path / "single-conflict"
    target.mkdir()
    # Create a conflicting catalogue.toml
    (target / "catalogue.toml").write_text(
        'schema = 0\n[catalogue]\nname = "x"', encoding="utf-8"
    )

    result = _run_init(target, name="single-conflict")
    assert not result.ok
    # packs/README.md should NOT have been written
    assert not (target / "packs" / "README.md").exists()


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def test_rollback_on_commit_failure_removes_created_files(tmp_path):
    """If the commit step raises mid-way, only newly-created files are removed."""
    from agentbundle.catalogue_tooling import initialise as mod

    target = tmp_path / "rollback-test"

    original_commit = mod._commit_files

    call_count = [0]

    def _failing_commit(t, planned, file_plan):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("Simulated disk failure")
        return original_commit(t, planned, file_plan)

    with patch.object(mod, "_commit_files", side_effect=_failing_commit):
        result = _run_init(target, name="rollback-test")

    assert not result.ok
    # Target should be clean (either removed or no scaffold files)
    if target.exists():
        assert not (target / "catalogue.toml").exists()


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------

def test_dry_run_no_target_created(tmp_path):
    """--dry-run=True does not create the target directory."""
    target = tmp_path / "dry-run-no-create"
    result = _run_init(target, name="dry-run-no-create", dry_run=True)

    assert result.ok
    assert result.dry_run is True
    assert not target.exists(), "Target directory was created in dry run"


def test_dry_run_existing_target_no_files_written(tmp_path):
    """--dry-run on an existing target writes nothing."""
    target = tmp_path / "dry-run-existing"
    target.mkdir()

    result = _run_init(target, name="dry-run-existing", dry_run=True)

    assert result.ok
    assert result.dry_run is True
    # No catalogue.toml should have been written
    assert not (target / "catalogue.toml").exists()


def test_dry_run_reports_would_create(tmp_path):
    """Dry-run still reports what files would be created."""
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "dry-run-check"
    result = _run_init(target, name="dry-run-check", dry_run=True)

    creates = [fp for fp in result.files if fp.action == FileAction.CREATE]
    assert creates, "Dry run should report files to create"


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_parses(tmp_path):
    """init_catalogue result converts to valid JSON (matches json schema)."""
    import dataclasses
    import json

    target = tmp_path / "json-test"
    result = _run_init(target, name="json-test")
    assert result.ok

    doc = {
        "schema_version": result.schema_version,
        "command": result.command,
        "operation": result.operation,
        "agentbundle_version": result.agentbundle_version,
        "catalogue_schema_version": result.catalogue_schema_version,
        "ok": result.ok,
        "dry_run": result.dry_run,
        "target": result.target,
        "catalogue": dataclasses.asdict(result.catalogue),
        "summary": dataclasses.asdict(result.summary),
        "files": [dataclasses.asdict(f) for f in result.files],
        "verification": dataclasses.asdict(result.verification),
        "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
    }
    serialized = json.dumps(doc)
    parsed = json.loads(serialized)
    assert parsed["ok"] is True
    assert parsed["agentbundle_version"]
    assert parsed["catalogue_schema_version"] == 1


# ---------------------------------------------------------------------------
# No network request
# ---------------------------------------------------------------------------

def test_no_network_request_during_init(tmp_path):
    """init_catalogue must not make any network calls."""
    import socket

    target = tmp_path / "no-network"

    def _refuse_connect(*args, **kwargs):
        raise AssertionError("Network call made during init — forbidden")

    with patch.object(socket.socket, "connect", side_effect=_refuse_connect):
        result = _run_init(target, name="no-network")

    assert result.ok, f"Init failed (not due to network): {result.diagnostics}"


# ---------------------------------------------------------------------------
# Dogfooding
# ---------------------------------------------------------------------------

def test_dogfood_blank_catalogue_passes_verify(tmp_path):
    """An initialized catalogue passes verify with no ERROR diagnostics."""
    from agentbundle.catalogue_tooling.verify import verify_catalogue

    target = tmp_path / "dogfood"
    result = _run_init(target, name="dogfood", owner_name="Dogfood Org")
    assert result.ok, f"Init failed: {result.diagnostics}"

    vr = verify_catalogue(target)
    errors = [d for d in vr.diagnostics if d.severity.name == "ERROR"]
    assert vr.ok, f"Verify failed: {errors}"
    assert not errors


def test_dogfood_no_host_files_leaked(tmp_path):
    """Init does not leak any host-repo files beyond the declared scaffold."""
    from agentbundle.scaffold import list_files

    target = tmp_path / "leak-check"
    result = _run_init(target, name="leak-check")
    assert result.ok

    scaffold_paths = set(list_files())
    # Generated files
    generated_paths = {"catalogue.toml", ".claude-plugin/marketplace.json"}
    allowed = scaffold_paths | generated_paths

    # Walk target and collect all files
    written: set[str] = set()
    for f in target.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(target)).replace("\\", "/")
            written.add(rel)

    leaked = written - allowed
    assert not leaked, f"Host files leaked into init target: {leaked}"


# ---------------------------------------------------------------------------
# Post-init discovery
# ---------------------------------------------------------------------------

def test_list_packs_zero_after_init(tmp_path):
    """After init, discover_packs returns no real packs (only _example, which is excluded)."""
    from agentbundle.build.main import discover_packs

    target = tmp_path / "list-packs-test"
    result = _run_init(target, name="list-packs-test")
    assert result.ok

    packs = discover_packs(target / "packs")
    assert packs == [], f"Expected no discoverable packs, got: {[p.name for p in packs]}"


def test_list_profiles_zero_after_init(tmp_path):
    """After init, list_profiles returns no real profiles (only _example, which is excluded)."""
    from agentbundle.commands.profile import list_profiles

    target = tmp_path / "list-profiles-test"
    result = _run_init(target, name="list-profiles-test")
    assert result.ok

    profiles = list_profiles(target)
    assert profiles == [], f"Expected no profiles, got: {profiles}"


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

def test_metadata_flags_propagated(tmp_path):
    """Custom flags are written into catalogue.toml."""
    import tomllib

    target = tmp_path / "flags-test"
    result = _run_init(
        target,
        name="flags-cat",
        display_name="Flags Catalogue",
        description="A flags test catalogue.",
        owner_name="Flags Org",
        preferred_adapter="claude-code",
    )
    assert result.ok

    data = tomllib.loads((target / "catalogue.toml").read_text(encoding="utf-8"))
    assert data["catalogue"]["name"] == "flags-cat"
    assert data["catalogue"]["display-name"] == "Flags Catalogue"
    assert data["catalogue"]["owner"]["name"] == "Flags Org"
