import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
STATUS_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"


def _load_module(path: Path, label: str) -> ModuleType:
    """Load a module from a file without retaining its temporary registration."""
    module_name = f"_cooling_scope_{label}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


ENGINE = _load_module(ENGINE_PATH, "engine")
STATUS = _load_module(STATUS_PATH, "status")


def write_spec(root: Path, slug: str, status: str = "Approved", plan: bool = True) -> str:
    """Write a specification and optional approved plan, returning its locator."""
    spec_directory = root / "docs" / "specs" / slug
    spec_directory.mkdir(parents=True, exist_ok=True)
    spec_path = spec_directory / "spec.md"
    spec_path.write_text(f"# Spec: {slug}\n\n- **Status:** {status}\n", encoding="utf-8")
    if plan:
        (spec_directory / "plan.md").write_text(
            f"# Plan: {slug}\n\n- **Status:** Approved\n",
            encoding="utf-8",
        )
    return f"docs/specs/{slug}/spec.md"


def write_record(
    root: Path,
    delivery_id: str,
    locator: str,
    *,
    aliases: tuple[str, ...] = (),
    unreadable: bool = False,
) -> Path:
    """Write a valid or deliberately unreadable delivery lifecycle record."""
    lifecycle_directory = root / "docs" / "lifecycle"
    lifecycle_directory.mkdir(parents=True, exist_ok=True)
    record_path = lifecycle_directory / f"{delivery_id}.json"
    if unreadable:
        record_path.write_bytes(b"{ not json")
        return record_path

    repository_authority = {"status": "repository-owned"}
    record = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": delivery_id,
        "locator": locator,
        "aliases": list(aliases),
        "fingerprint": "sha256:" + "0" * 64,
        "confirmation_proof": "sha256:" + "0" * 64,
        "disposition": "cool-30-days",
        "post_closeout_result": "Cooling",
        "completion_event": "merge",
        "completion_evidence_ref": "pr:1",
        "completed_on": "2026-08-01",
        "timezone": "UTC",
        "review_on": "2026-08-31",
        "authority": {
            "source": repository_authority.copy(),
            "write": repository_authority.copy(),
            "delete": repository_authority.copy(),
        },
    }
    record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return record_path


def write_workspace(
    root: Path,
    *,
    queue: list[str] | None = None,
    active: list[str] | None = None,
    shipped: list[str] | None = None,
    status: str = "active",
    legacy_queue: list[str] | None = None,
    migration_authorization: bool = False,
) -> None:
    """Write a workspace containing canonical and optional legacy memberships."""
    root.mkdir(parents=True, exist_ok=True)
    queue_entries = [_workspace_entry(path) for path in queue or []]
    queue_entries.extend(json.dumps(path) for path in legacy_queue or [])
    active_entries = [_workspace_entry(path) for path in active or []]
    shipped_entries = [_workspace_entry(path) for path in shipped or []]

    sections: list[str] = []
    if migration_authorization:
        sections.extend(
            [
                "[authorization.migration]",
                'contract_version = "work-intake-migration-authorization.v1"',
                'approver_roles = ["migration-approver"]',
                "",
            ]
        )
    sections.extend(
        [
            '["ini-002"]',
            'name = "Cooling fixture"',
            f"status = {json.dumps(status)}",
            'milestone = "workspace.toml"',
            "",
            '["ini-002".work]',
            _toml_array("queue", queue_entries),
            _toml_array("active", active_entries),
            _toml_array("shipped", shipped_entries),
            "",
            "[backlog]",
            "open = []",
            "closed = []",
            "",
        ]
    )
    (root / "workspace.toml").write_text("\n".join(sections), encoding="utf-8")


def _workspace_entry(path: str) -> str:
    """Render one canonical workspace entry as a TOML inline table."""
    return (
        f'{{path = {json.dumps(path)}, kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "s", needs = []}'
    )


def _toml_array(name: str, entries: list[str]) -> str:
    """Render a TOML array while preserving bare quoted legacy entries."""
    if not entries:
        return f"{name} = []"
    rendered_entries = "\n".join(f"  {entry}," for entry in entries)
    return f"{name} = [\n{rendered_entries}\n]"


def run_status(root: Path, mode: str = "status") -> dict:
    """Run workspace-status and return its JSON payload."""
    completed = subprocess.run(
        [sys.executable, str(STATUS_PATH), mode, "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in {0, 1}:
        raise AssertionError(
            f"workspace-status exited {completed.returncode}: {completed.stderr}"
        )
    return json.loads(completed.stdout)


def cooled_initiative(
    root: Path,
    *,
    cooled: bool = True,
    alias: bool = False,
    active: bool = False,
    extra_uncooled: bool = False,
    unreadable: bool = False,
    shipped_queue_spec: bool = False,
    initiative_status: str = "active",
) -> Path:
    """Build the standard canonical fixture with optional cooling variants."""
    cooled_locator = write_spec(
        root,
        "cooled-one",
        status="Shipped" if shipped_queue_spec else "Approved",
    )
    shipped_locator = write_spec(root, "shipped-one", status="Shipped")
    queue = [] if active else [cooled_locator]
    active_entries = [cooled_locator] if active else []
    if extra_uncooled:
        queue.append(write_spec(root, "live-one"))
    write_workspace(
        root,
        queue=queue,
        active=active_entries,
        shipped=[shipped_locator],
        status=initiative_status,
    )

    if cooled:
        if alias:
            write_record(
                root,
                "cooled-one",
                "docs/specs/other/spec.md",
                aliases=(cooled_locator,),
            )
        else:
            write_record(root, "cooled-one", cooled_locator)
    if unreadable:
        write_record(root, "broken", "docs/specs/broken/spec.md", unreadable=True)
    return root


def migration_fixture(root: Path, *, cooled: bool = True) -> Path:
    """Build a legacy migration fixture with optional cooling evidence."""
    locator = write_spec(root, "legacy")
    write_workspace(
        root,
        legacy_queue=["spec/legacy"],
        migration_authorization=True,
    )
    if cooled:
        write_record(root, "legacy", locator)
    return root


def assert_migration_fixture_is_real(tmp_path: Path) -> None:
    """Prove cooling removes a real legacy membership from canonical status."""
    uncooled = migration_fixture(tmp_path / "migration-uncooled", cooled=False)
    cooled = migration_fixture(tmp_path / "migration-cooled", cooled=True)

    uncooled_memberships = run_status(uncooled)["canonical"]["legacy_memberships"]
    cooled_memberships = run_status(cooled)["canonical"]["legacy_memberships"]
    assert [membership["path"] for membership in uncooled_memberships] == ["spec/legacy"]
    assert [membership["path"] for membership in cooled_memberships] == []


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac1_cooled_queue_entry_counts_toward_neither(
    tmp_path: Path, mode: str
) -> None:
    """AC1: a cooled queue entry is absent from both closeout consumers."""
    result = run_status(cooled_initiative(tmp_path, cooled=True), mode)
    initiative = next(
        item for item in result["initiatives"] if item["slug"] == "ini-002"
    )

    assert result["closeout"]["all_specs_shipped"] is True
    assert initiative["queue_empty"] is True


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac2_uncooled_control_reports_both_false(tmp_path: Path, mode: str) -> None:
    """AC2: the uncooled queue entry keeps both closeout values false."""
    result = run_status(cooled_initiative(tmp_path, cooled=False), mode)
    initiative = next(
        item for item in result["initiatives"] if item["slug"] == "ini-002"
    )

    assert result["closeout"]["all_specs_shipped"] is False
    assert initiative["queue_empty"] is False


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac3_both_consumers_move_together(tmp_path: Path, mode: str) -> None:
    """AC3: both closeout consumers move between cooled and plain fixtures."""
    cooled = run_status(
        cooled_initiative(tmp_path / "cooled", cooled=True), mode
    )
    uncooled = run_status(
        cooled_initiative(tmp_path / "uncooled", cooled=False), mode
    )
    cooled_initiative_out = next(
        item for item in cooled["initiatives"] if item["slug"] == "ini-002"
    )
    uncooled_initiative_out = next(
        item for item in uncooled["initiatives"] if item["slug"] == "ini-002"
    )

    assert (
        cooled["closeout"]["all_specs_shipped"]
        != uncooled["closeout"]["all_specs_shipped"]
    )
    assert (
        cooled_initiative_out["queue_empty"]
        != uncooled_initiative_out["queue_empty"]
    )


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac4_alias_cooled_entry_moves_both_consumers(
    tmp_path: Path, mode: str
) -> None:
    """AC4: an alias-cooled queue entry moves both closeout consumers."""
    cooled = run_status(
        cooled_initiative(tmp_path / "cooled", cooled=True, alias=True), mode
    )
    uncooled = run_status(
        cooled_initiative(tmp_path / "uncooled", cooled=False, alias=True), mode
    )
    cooled_initiative_out = next(
        item for item in cooled["initiatives"] if item["slug"] == "ini-002"
    )
    uncooled_initiative_out = next(
        item for item in uncooled["initiatives"] if item["slug"] == "ini-002"
    )

    assert cooled["closeout"]["all_specs_shipped"] is True
    assert cooled_initiative_out["queue_empty"] is True
    assert (
        cooled["closeout"]["all_specs_shipped"]
        != uncooled["closeout"]["all_specs_shipped"]
    )
    assert (
        cooled_initiative_out["queue_empty"]
        != uncooled_initiative_out["queue_empty"]
    )


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac5_queue_empty_still_counts_queue_alone(
    tmp_path: Path, mode: str
) -> None:
    """AC5: an uncooled active entry blocks shipping but not queue emptiness."""
    result = run_status(
        cooled_initiative(tmp_path, cooled=False, active=True), mode
    )
    initiative = next(
        item for item in result["initiatives"] if item["slug"] == "ini-002"
    )

    assert result["closeout"]["all_specs_shipped"] is False
    assert initiative["queue_empty"] is True


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac6_cooled_active_entry_counts_toward_shippedness(
    tmp_path: Path, mode: str
) -> None:
    """AC6: a cooled active entry stops blocking projected shipped-ness."""
    cooled = run_status(
        cooled_initiative(tmp_path / "cooled", cooled=True, active=True), mode
    )
    uncooled = run_status(
        cooled_initiative(tmp_path / "uncooled", cooled=False, active=True), mode
    )

    assert cooled["closeout"]["all_specs_shipped"] is True
    assert uncooled["closeout"]["all_specs_shipped"] is False


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac7_uncooled_sibling_still_blocks(tmp_path: Path, mode: str) -> None:
    """AC7: an uncooled queue sibling keeps both closeout values false."""
    result = run_status(
        cooled_initiative(tmp_path, cooled=True, extra_uncooled=True), mode
    )
    initiative = next(
        item for item in result["initiatives"] if item["slug"] == "ini-002"
    )

    assert result["closeout"]["all_specs_shipped"] is False
    assert initiative["queue_empty"] is False


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac8_cooled_queue_entry_has_no_unshipped_blocker(
    tmp_path: Path, mode: str
) -> None:
    """AC8: a cooled queue entry does not emit the unshipped-specs blocker."""
    result = run_status(cooled_initiative(tmp_path, cooled=True), mode)

    assert "unshipped-specs" not in result["closeout"]["closeout_blockers"]


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac10_clean_cooled_reading_keeps_affirmative_instruction(
    tmp_path: Path, mode: str
) -> None:
    """AC10: a complete cooled reading keeps the affirmative closeout action."""
    result = run_status(cooled_initiative(tmp_path, cooled=True), mode)

    assert result["closeout"]["cooling_context_visible"] is False
    assert result["closeout"]["next_action"] == "invoke-close-work"
    assert (
        "cooling-context-incomplete"
        not in result["closeout"]["closeout_blockers"]
    )


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac11_paused_projection_omits_initiative_queue_empty(
    tmp_path: Path, mode: str
) -> None:
    """AC11: a paused projection emits closeout without an initiative row."""
    result = run_status(
        cooled_initiative(tmp_path, initiative_status="paused"), mode
    )

    assert result["closeout"]["paused"] is True
    assert result["closeout"]["next_action"] == "resume-or-keep-paused"
    assert result["initiatives"] == []
