import hashlib
import importlib.util
import json
import re
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
    surviving_active: bool = False,
    initiative_status: str = "active",
) -> Path:
    """Build the standard canonical fixture with optional cooling variants.

    `surviving_active` adds an uncooled `work.active` entry alongside the cooled
    queue entry, so the queue-alone shape can be pinned with the exclusion live
    rather than on the short-circuited path.
    """
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
    if surviving_active:
        active_entries.append(write_spec(root, "active-uncooled"))
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
def test_ac9_incomplete_reading_withholds_affirmative(
    tmp_path: Path, mode: str
) -> None:
    """AC9: an incomplete cooled reading withholds affirmative closeout."""
    result = run_status(
        cooled_initiative(tmp_path, cooled=True, unreadable=True), mode
    )

    assert result["closeout"]["cooling_context_visible"] is True
    assert (
        "cooling-context-incomplete"
        in result["closeout"]["closeout_blockers"]
    )
    assert result["closeout"]["next_action"] != "invoke-close-work"


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


def test_ac12_wave6_residual_assertion_is_replaced() -> None:
    """AC12: Wave 6's residual assertion is replaced in place."""
    text = (
        ROOT / "tests/roster/test_status_projection_and_context_exclusion.py"
    ).read_text(encoding="utf-8")

    assert "def test_a_fully_cooled_initiative_still_reports_unshipped_specs" not in text
    assert "def test_a_fully_cooled_initiative_reports_all_specs_shipped" in text
    assert 'projection["closeout"]["all_specs_shipped"] is True' in text


def test_ac13_wave6_roster_name_set_is_unchanged() -> None:
    """AC13: the Wave 6 roster changes by only the residual-test rename."""
    text = (
        ROOT / "tests/roster/test_status_projection_and_context_exclusion.py"
    ).read_text(encoding="utf-8")
    names = sorted(
        match.group(1) for match in re.finditer(r"^def (test_\w+)", text, re.M)
    )

    assert hashlib.sha256("\n".join(names).encode()).hexdigest() == (
        "6fff3ededf8da2f1899dd9ea7560867abdec728dc4e139b861559097f103b637"
    )


def _run_workspace_status(
    root: Path, mode: str, *arguments: str
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    """Run one workspace-status CLI mode and parse its JSON output."""
    completed = subprocess.run(
        [
            sys.executable,
            str(STATUS_PATH),
            mode,
            "--root",
            str(root),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"workspace-status exited {completed.returncode}: {completed.stderr}"
        ) from error
    return completed, payload


def _write_migration_selection(root: Path, operation_nonce: str) -> tuple[Path, dict]:
    """Write a reviewed selection derived from the fixture's legacy finding."""
    workspace_path = root / "workspace.toml"
    workspace_bytes = workspace_path.read_bytes()
    workspace = ENGINE.parse_workspace(workspace_path)
    canonical = ENGINE.run_canonical_reconciliation(workspace, root)
    assert len(canonical.legacy_memberships) == 1
    finding = ENGINE.build_migration_finding(
        workspace_bytes, canonical.legacy_memberships[0]
    )
    locator = "docs/specs/legacy/spec.md"
    selection = {
        "contract_version": "work-intake-migration-selection.v1",
        "legacy_finding_id": finding["legacy_finding_id"],
        "workspace_fingerprint": hashlib.sha256(workspace_bytes).hexdigest(),
        "source_membership": finding["source_membership"],
        "target_entry": {
            "path": locator,
            "kind": "spec",
            "source": {
                "mode": "repo-origin",
                "ref": f"tracker/{operation_nonce}",
            },
            "summary": f"Reviewed migration target {operation_nonce}",
            "needs": [],
        },
        "target_membership": {
            "ini_slug": "ini-002",
            "collection": "work.queue",
        },
        "owning_processor": "new-spec",
        "provenance_reference": locator,
        "legacy_content_approved_for_ledger": True,
    }
    selection_path = root / "migration-selection.json"
    selection_path.write_text(json.dumps(selection) + "\n", encoding="utf-8")
    return selection_path, selection


def _plan_migration(
    root: Path, operation_nonce: str
) -> tuple[Path, dict, dict[str, object]]:
    """Write a selection and obtain its planned migration operation."""
    selection_path, selection = _write_migration_selection(root, operation_nonce)
    completed, payload = _run_workspace_status(
        root,
        "repair-plan",
        "--migration-selection",
        selection_path.name,
    )
    assert completed.returncode == 0, completed.stderr
    migration = payload["migration"]
    assert isinstance(migration, dict)
    assert migration["result_code"] == "planned"
    operation = payload["proposed_operation"]
    assert isinstance(operation, dict)
    return selection_path, selection, operation


def _write_migration_confirmation(
    root: Path,
    operation: dict[str, object],
    *,
    action: str,
    confirmation_token: str,
    subject_token: str,
    confirmed_at: str,
) -> Path:
    """Write fresh test-only migration evidence under the fixture root."""
    confirmation = {
        "contract_version": "work-intake-migration-confirmation.v1",
        "confirmation_id": f"confirmation-{confirmation_token}",
        "action": action,
        "operation_id": operation["operation_id"],
        "operation_digest": operation["operation_digest"],
        "authorization_subject": f"subject-{subject_token}",
        "role": "migration-approver",
        "confirmed_at": confirmed_at,
        "authorization_source": "current-human-session",
    }
    confirmation_path = root / f"{action}-confirmation.json"
    confirmation_path.write_text(json.dumps(confirmation) + "\n", encoding="utf-8")
    return confirmation_path


def _fresh_confirmation_timestamp() -> str:
    """Return a current UTC timestamp accepted by migration confirmation checks."""
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")


def test_ac17_repair_plan_output_is_identical_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC17: repair planning ignores lifecycle cooling evidence."""
    outputs = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = cooled_initiative(
            tmp_path / directory,
            cooled=cooled,
            shipped_queue_spec=True,
        )
        completed, payload = _run_workspace_status(root, "repair-plan")
        assert completed.returncode == 0, completed.stderr
        assert payload["automatic_operations"]
        outputs.append(payload)

    assert outputs[0] == outputs[1]


def test_ac18_repair_apply_writes_identical_bytes_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC18: independently planned repair applications ignore cooling."""
    resulting_workspace_bytes = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = cooled_initiative(
            tmp_path / directory,
            cooled=cooled,
            shipped_queue_spec=True,
        )
        workspace_path = root / "workspace.toml"
        before = workspace_path.read_bytes()
        plan_path = root / "repair-plan.json"
        planned, plan_payload = _run_workspace_status(
            root,
            "repair-plan",
            "--plan-file",
            str(plan_path),
        )
        assert planned.returncode == 0, planned.stderr
        assert plan_payload["automatic_operations"]

        applied, _payload = _run_workspace_status(
            root,
            "repair-apply",
            "--plan-file",
            str(plan_path),
            "--yes",
        )
        assert applied.returncode == 0, applied.stderr
        after = workspace_path.read_bytes()
        assert after != before
        resulting_workspace_bytes.append(after)

    assert resulting_workspace_bytes[0] == resulting_workspace_bytes[1]


def test_ac19_migration_plan_output_is_identical_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC19: migration planning ignores lifecycle cooling evidence."""
    assert_migration_fixture_is_real(tmp_path / "realness")
    outputs = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = migration_fixture(tmp_path / "identity" / directory, cooled=cooled)
        selection_path, _selection = _write_migration_selection(
            root, "ac19-identity"
        )
        completed, payload = _run_workspace_status(
            root,
            "repair-plan",
            "--migration-selection",
            selection_path.name,
        )
        assert completed.returncode == 0, completed.stderr
        assert payload["migration"]["result_code"] == "planned"
        outputs.append(payload)

    assert outputs[0] == outputs[1]


def test_ac20_migration_apply_is_identical_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC20: migration application ignores lifecycle cooling evidence."""
    assert_migration_fixture_is_real(tmp_path / "realness")
    import secrets

    operation_nonce = secrets.token_hex(16)
    confirmation_token = secrets.token_hex(16)
    subject_token = secrets.token_hex(16)
    confirmed_at = _fresh_confirmation_timestamp()
    result_codes = []
    workspace_bytes = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = migration_fixture(tmp_path / directory, cooled=cooled)
        selection_path, _selection, operation = _plan_migration(
            root, operation_nonce
        )
        confirmation_path = _write_migration_confirmation(
            root,
            operation,
            action="apply",
            confirmation_token=confirmation_token,
            subject_token=subject_token,
            confirmed_at=confirmed_at,
        )
        completed, payload = _run_workspace_status(
            root,
            "repair-apply",
            "--migration-selection",
            selection_path.name,
            "--operation-id",
            str(operation["operation_id"]),
            "--confirmation-file",
            confirmation_path.name,
        )
        assert completed.returncode == 0, completed.stderr
        result_codes.append(payload["migration"]["result_code"])
        workspace_bytes.append((root / "workspace.toml").read_bytes())

    assert result_codes == ["applied", "applied"]
    assert workspace_bytes[0] == workspace_bytes[1]


def test_ac21_pending_migration_recovery_is_identical_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC21: pending migration recovery ignores lifecycle cooling evidence."""
    assert_migration_fixture_is_real(tmp_path / "realness")
    import secrets

    assert STATUS._bind_engine()
    operation_nonce = secrets.token_hex(16)
    initial_confirmation_token = secrets.token_hex(16)
    initial_subject_token = secrets.token_hex(16)
    recovery_confirmation_token = secrets.token_hex(16)
    recovery_subject_token = secrets.token_hex(16)
    confirmed_at = _fresh_confirmation_timestamp()
    result_codes = []
    workspace_bytes = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = migration_fixture(tmp_path / directory, cooled=cooled)
        selection_path, selection, operation = _plan_migration(root, operation_nonce)
        initial_confirmation_path = _write_migration_confirmation(
            root,
            operation,
            action="apply",
            confirmation_token=initial_confirmation_token,
            subject_token=initial_subject_token,
            confirmed_at=confirmed_at,
        )
        initial_confirmation = json.loads(
            initial_confirmation_path.read_text(encoding="utf-8")
        )
        interrupted = STATUS.apply_migration_operation(
            root,
            selection,
            str(operation["operation_id"]),
            initial_confirmation,
            failure_point="workspace_replace_after",
        )
        assert interrupted["result_code"] == "write_failed"
        ledger = json.loads(
            (root / ".workspace-migrations.json").read_text(encoding="utf-8")
        )
        assert ledger["operations"][0]["state"] == "pending"
        assert b"docs/specs/legacy/spec.md" in (
            root / "workspace.toml"
        ).read_bytes()

        recovery_confirmation_path = _write_migration_confirmation(
            root,
            operation,
            action="apply",
            confirmation_token=recovery_confirmation_token,
            subject_token=recovery_subject_token,
            confirmed_at=confirmed_at,
        )
        completed, payload = _run_workspace_status(
            root,
            "repair-apply",
            "--migration-selection",
            selection_path.name,
            "--operation-id",
            str(operation["operation_id"]),
            "--confirmation-file",
            recovery_confirmation_path.name,
        )
        assert completed.returncode == 0, completed.stderr
        result_codes.append(payload["migration"]["result_code"])
        workspace_bytes.append((root / "workspace.toml").read_bytes())

    assert result_codes == ["applied", "applied"]
    assert workspace_bytes[0] == workspace_bytes[1]


def test_ac22_migration_rollback_is_identical_with_and_without_cooling(
    tmp_path: Path,
) -> None:
    """AC22: migration rollback ignores lifecycle cooling evidence."""
    assert_migration_fixture_is_real(tmp_path / "realness")
    import secrets

    operation_nonce = secrets.token_hex(16)
    apply_confirmation_token = secrets.token_hex(16)
    apply_subject_token = secrets.token_hex(16)
    rollback_confirmation_token = secrets.token_hex(16)
    rollback_subject_token = secrets.token_hex(16)
    confirmed_at = _fresh_confirmation_timestamp()
    result_codes = []
    workspace_bytes = []
    for directory, cooled in (("cooled", True), ("uncooled", False)):
        root = migration_fixture(tmp_path / directory, cooled=cooled)
        original_workspace_bytes = (root / "workspace.toml").read_bytes()
        selection_path, _selection, operation = _plan_migration(
            root, operation_nonce
        )
        apply_confirmation_path = _write_migration_confirmation(
            root,
            operation,
            action="apply",
            confirmation_token=apply_confirmation_token,
            subject_token=apply_subject_token,
            confirmed_at=confirmed_at,
        )
        applied, apply_payload = _run_workspace_status(
            root,
            "repair-apply",
            "--migration-selection",
            selection_path.name,
            "--operation-id",
            str(operation["operation_id"]),
            "--confirmation-file",
            apply_confirmation_path.name,
        )
        assert applied.returncode == 0, applied.stderr
        assert apply_payload["migration"]["result_code"] == "applied"

        rollback_confirmation_path = _write_migration_confirmation(
            root,
            operation,
            action="rollback",
            confirmation_token=rollback_confirmation_token,
            subject_token=rollback_subject_token,
            confirmed_at=confirmed_at,
        )
        rolled_back, rollback_payload = _run_workspace_status(
            root,
            "repair-rollback",
            "--operation-id",
            str(operation["operation_id"]),
            "--confirmation-file",
            rollback_confirmation_path.name,
        )
        assert rolled_back.returncode == 0, rolled_back.stderr
        result_codes.append(rollback_payload["migration"]["result_code"])
        rolled_back_workspace_bytes = (root / "workspace.toml").read_bytes()
        assert rolled_back_workspace_bytes == original_workspace_bytes
        workspace_bytes.append(rolled_back_workspace_bytes)

    assert result_codes == ["rolled_back", "rolled_back"]
    assert workspace_bytes[0] == workspace_bytes[1]


def test_ac23_pinned_files_are_byte_unchanged() -> None:
    """AC23: every frozen dependency retains its approved byte digest."""
    expected_digests = {
        "packs/core/.apm/skills/close-work/scripts/cooling.py": (
            "d6bd7c6e47d5a23e45a9f5ee5a8d5506d3435b1da00facde96f1fbfba5bf061c"
        ),
        "contracts/jsonschema/delivery-lifecycle-record.schema.json": (
            "557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878"
        ),
        "docs/specs/status-projection-and-context-exclusion/spec.md": (
            "2cac21ca5f84e0f4e477a6bab432429a55034f6851dc152cfcd93611e9e3523d"
        ),
        "docs/specs/status-projection-and-context-exclusion/plan.md": (
            "93958585c454ab761a79f2e358e546f5d0cc7e7c8e722a8cf42114ab22a7c487"
        ),
        "docs/specs/thirty-day-cooling-and-retirement/spec.md": (
            "3255b1a8b12e2cfaeccc5e6c97a7047467e8ca8e001467fdefc6757318d4c95f"
        ),
        "docs/specs/thirty-day-cooling-and-retirement/plan.md": (
            "2c416277c607b9f7b2b617e06a79a58f6059f43bd2d6c2ebef35ea6af810e3e7"
        ),
    }

    for relative_path, expected_digest in expected_digests.items():
        actual_digest = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_digest == expected_digest, relative_path


def test_ac24_two_reconciliation_calls_still_pass_one_argument() -> None:
    """AC24: exactly two reconciliation call sites remain single-argument."""
    import ast

    tree = ast.parse(STATUS_PATH.read_text(encoding="utf-8"))
    single_argument_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_canonical_reconciliation"
        and len(node.args) == 1
        and not node.keywords
    ]

    assert len(single_argument_calls) == 2


def test_ac14_skill_states_cooled_exclusion() -> None:
    """AC14: the workspace-status skill states the cooled exclusion."""
    normalized = " ".join(
        (
            ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
        ).read_text(encoding="utf-8").split()
    )

    assert "the queue emptiness flag excludes entries named by a lifecycle record" in normalized


def test_ac15_skill_drops_authoritative_queue_claim() -> None:
    """AC15: the workspace-status skill drops the authoritative queue claim."""
    normalized = " ".join(
        (
            ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
        ).read_text(encoding="utf-8").split()
    )

    assert "is the authoritative check" not in normalized


def test_ac16_skill_withholds_closeout_for_blockers() -> None:
    """AC16: the workspace-status skill withholds closeout for blockers."""
    normalized = " ".join(
        (
            ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
        ).read_text(encoding="utf-8").split()
    )

    assert "do not offer closeout while `closeout_blockers` is non-empty" in normalized


def test_ac25_wave_ownership_statements_survive() -> None:
    """AC25: the three wave-ownership statements survive unchanged."""
    normalized = " ".join(
        (
            ROOT / "docs/architecture/work-intake-and-artifact-routing.md"
        ).read_text(encoding="utf-8").split()
    )

    for statement in (
        "Wave 5 has shipped the lifecycle record, review-date, due-state, and retirement engine",
        "Wave 6 has shipped ordinary-context exclusion",
        "Wave 7 owns historical migration and pruning behavior",
    ):
        assert statement in normalized, statement
    assert "Wave 6 and 7 own ordinary-context exclusion" not in normalized


def test_ac26_architecture_names_four_wave_slices() -> None:
    """AC26: the architecture surface names all four Wave 7 slices."""
    normalized = " ".join(
        (
            ROOT / "docs/architecture/work-intake-and-artifact-routing.md"
        ).read_text(encoding="utf-8").split()
    )

    for statement in (
        "Wave 7a-i closes cooling scope",
        "Wave 7a-ii projects the completion receipt",
        "Wave 7b classifies history",
        "Wave 7c prunes proven-eligible artifacts",
    ):
        assert statement in normalized, statement


def test_ac27_reference_states_closeout_derivation() -> None:
    """AC27: the reference guide states the closeout derivation."""
    normalized = " ".join(
        (
            ROOT / "guides/core/reference/work-intake-routing-and-lifecycle.md"
        ).read_text(encoding="utf-8").split()
    )

    assert (
        "an entry named by a lifecycle record counts toward neither closeout consumer"
        in normalized
    )


def test_ac32_skill_retains_queue_and_shipped_conditions() -> None:
    """AC32: the workspace-status skill retains both further conditions."""
    normalized = " ".join(
        (
            ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
        ).read_text(encoding="utf-8").split()
    )

    assert "`initiatives[i].queue_empty` is `true`" in normalized
    assert "filtered shipped is non-empty" in normalized


def _normalized_rfc_errata() -> str:
    """Return whitespace-normalized text scoped to RFC-0096's Errata section."""
    document = (
        ROOT / "docs/rfc/0096-portable-delivery-artifact-lifecycle.md"
    ).read_text(encoding="utf-8")
    errata = document[document.index("## Errata") :]
    next_section = re.search(r"\n## ", errata[len("## Errata") :])
    if next_section is not None:
        errata = errata[: len("## Errata") + next_section.start()]
    return " ".join(errata.split())


def test_ac28_rfc_wave_seven_body_is_byte_unchanged() -> None:
    """AC28: RFC-0096 section 9 retains its approved byte digest."""
    rfc_bytes = (
        ROOT / "docs/rfc/0096-portable-delivery-artifact-lifecycle.md"
    ).read_bytes()
    start = rfc_bytes.index(b"## 9. Initiative waves")
    end = rfc_bytes.index(b"## 10. Risks and revisit conditions")

    assert hashlib.sha256(rfc_bytes[start:end]).hexdigest() == (
        "e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e"
    )


def test_ac29_erratum_records_four_wave_slices() -> None:
    """AC29: the signed erratum records the four Wave 7 slices."""
    errata = _normalized_rfc_errata()

    assert errata.count("Approver: eugenelim") == 2
    for statement in (
        "cooling-scope-closure",
        "Wave 7a-i closes cooling scope",
        "Wave 7a-ii projects the completion receipt",
        "Wave 7b classifies history",
        "Wave 7c prunes proven-eligible artifacts",
    ):
        assert statement in errata, statement


def test_ac30_erratum_registers_follow_ons_and_corrected_basis() -> None:
    """AC30: the erratum records open follow-ons and the corrected basis."""
    errata = _normalized_rfc_errata()

    for statement in (
        "rfc0096-wave7a-ii-completion-receipts",
        "rfc0096-wave7b-historical-classification",
        "rfc0096-wave7c-pruning",
        "cooling-brief-child-scope",
        "owned by Wave 7a-ii",
        "owned by Wave 7b",
        "owned by Wave 7c",
        "admits any documented code",
    ):
        assert statement in errata, statement


def test_ac33_erratum_records_closures_residual_and_receipt_rename() -> None:
    """AC33: the erratum records closures, the residual, and the rename."""
    errata = _normalized_rfc_errata()

    for statement in (
        "cooling-closeout-eligibility",
        "cooling-repair-migration-scope",
        "closed by cooling-scope-closure",
        "without being verified against its artifact",
        "registered here as rfc0096-wave7a-ii-completion-receipts",
    ):
        assert statement in errata, statement


def test_ac31_release_surfaces_agree_above_the_floor() -> None:
    """AC31: the three core release surfaces hold one identical version.

    The floor is a floor, not an equality: `origin/main` released three times
    while this contract was in review, so a literal cannot track it. Clearing a
    collision is the release checklist's job, re-deriving the number from
    `git show origin/main:packs/core/pack.toml` at commit time — a test that read
    the remote would depend on fetch state.
    """
    pack = (ROOT / "packs/core/pack.toml").read_text(encoding="utf-8")
    plugin = json.loads(
        (ROOT / "packs/core/.claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    changelog = (ROOT / "docs/product/changelog.md").read_text(encoding="utf-8")

    pack_version = re.search(r'^version = "([^"]+)"', pack, re.M).group(1)
    plugin_version = plugin["version"]
    heading = re.search(r"^## \[core\]\[([^\]]+)\] — \d{4}-\d{2}-\d{2}", changelog, re.M)

    # pack<->plugin agreement is already pinned by
    # tests/conformance/test_pack_metadata.py, and pack<->topmost-[core] by
    # tests/roster/test_security_checklists_okf_projection.py. What is not
    # gated elsewhere is that the heading is dated and that the version clears
    # the floor, so only those are asserted here.
    assert heading is not None, "no dated [core] changelog heading found"

    parsed = tuple(int(part) for part in pack_version.split("."))
    assert parsed > (2, 19, 0), parsed


@pytest.mark.parametrize("mode", ["status", "reconcile"])
def test_ac5_queue_empty_counts_the_queue_alone_with_a_cooled_set(
    tmp_path: Path, mode: str
) -> None:
    """AC5: the queue-alone shape holds on the filtered path too.

    AC5's own fixture has no lifecycle record, so `_surviving_work` returns
    before the exclusion runs. A widening of `queue_empty` to span queue and
    active applied only when a cooled set is present would pass every other
    criterion, so the shape is pinned here with the filter live: one cooled
    queue entry and one uncooled active entry surviving.
    """
    root = cooled_initiative(
        tmp_path, cooled=True, surviving_active=True
    )
    result = run_status(root, mode)

    assert result["initiatives"][0]["queue_empty"] is True
    assert result["closeout"]["all_specs_shipped"] is False
