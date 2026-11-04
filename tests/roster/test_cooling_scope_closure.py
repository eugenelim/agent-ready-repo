import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType

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
    extra_queue_entries: list[tuple[str, str]] | None = None,
    migration_authorization: bool = False,
) -> None:
    """Write a workspace containing canonical and optional legacy memberships."""
    root.mkdir(parents=True, exist_ok=True)
    queue_entries = [_workspace_entry(path) for path in queue or []]
    queue_entries.extend(
        _workspace_entry(path, kind=kind) for path, kind in extra_queue_entries or []
    )
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


def _workspace_entry(path: str, *, kind: str = "spec") -> str:
    """Render one canonical workspace entry as a TOML inline table."""
    return (
        f'{{path = {json.dumps(path)}, kind = {json.dumps(kind)}, '
        'source = {mode = "repo-origin"}, summary = "s", needs = []}'
    )


def _toml_array(name: str, entries: list[str]) -> str:
    """Render a TOML array while preserving bare quoted legacy entries."""
    if not entries:
        return f"{name} = []"
    rendered_entries = "\n".join(f"  {entry}," for entry in entries)
    return f"{name} = [\n{rendered_entries}\n]"


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


def test_ac13_wave6_roster_name_set_is_unchanged() -> None:
    """AC13: no test function is added to or removed from the Wave 6 roster.

    The roster was re-struck when `workspace-status` kept only the repair: the
    cases that drove the retired status output left it, which took the count
    from 67 to 29. The bound still fails on the next unplanned addition or
    removal.
    """
    text = (
        ROOT / "tests/roster/test_status_projection_and_context_exclusion.py"
    ).read_text(encoding="utf-8")
    names = sorted(
        match.group(1) for match in re.finditer(r"^def (test_\w+)", text, re.M)
    )

    assert len(names) == 29, "a test function was added or removed"
    assert hashlib.sha256("\n".join(names).encode()).hexdigest() == (
        "fa29f973df7c2e5fc26676f950e5c11ad2bf13920d104e1874a160da39f79a28"
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


def test_ac23_pinned_files_are_byte_unchanged() -> None:
    """AC23: every frozen dependency retains its approved byte digest."""
    expected_digests = {
        # Re-pinned 2026-10-29 (docs/specs/header-derived-dispatch/spec.md): only
        # the optional `parent` field was added to cooling.py and to the schema,
        # and the `parent` reader's HTML-comment pattern gained `re.DOTALL`.
        "packs/core/.apm/skills/close-work/scripts/cooling.py": (
            "fd1f2cb6a8c38341099c420f5ad87c508a7a52e6d9c0d31a8106bd73ed916215"
        ),
        "contracts/jsonschema/delivery-lifecycle-record.schema.json": (
            "f44b5536ff18657c007b402897cecc99aeef042c0fc8947cef5e052727a06bc3"
        ),
        # Re-pinned 2026-09-12: this spec's Status-line supersession pointer named
        # ADR-0106, an ordinal that was held by two accepted records and has since
        # been repaired. The pointer now names ADR-0110. Only that line changed,
        # and a Status-line pointer is the one edit a frozen spec accepts, so the
        # frozen dependency this guard protects is intact.
        # Re-pinned 2026-10-26: the workspace-status repair moved this spec's two
        # registry `needs` edges onto one added `- **Depends on:**` preamble line.
        # Only that line was added, and its edges are the ones the registry held.
        "docs/specs/status-projection-and-context-exclusion/spec.md": (
            "9f6210e8b69ea5e5c7b9e618bef8955031587151c80ebfca74eefbb2dde529b1"
        ),
        "docs/specs/status-projection-and-context-exclusion/plan.md": (
            "93958585c454ab761a79f2e358e546f5d0cc7e7c8e722a8cf42114ab22a7c487"
        ),
        "docs/specs/thirty-day-cooling-and-retirement/spec.md": (
            "3b38fc9a00fc49c33ca32ac08d1c3021ec451f81356603077fa6f2b1cfe3fa39"
        ),
        "docs/specs/thirty-day-cooling-and-retirement/plan.md": (
            "cd5e2f3cfa4948892228a237f3fa1fd2affc0725d0e1aa8da262d670d55bb99d"
        ),
    }

    for relative_path, expected_digest in expected_digests.items():
        actual_digest = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_digest == expected_digest, relative_path


def test_ac15_skill_drops_authoritative_queue_claim() -> None:
    """AC15: the workspace-status skill drops the authoritative queue claim."""
    normalized = " ".join(
        (
            ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
        ).read_text(encoding="utf-8").split()
    )

    assert "is the authoritative check" not in normalized


def test_ac25_wave_ownership_statements_survive() -> None:
    """AC25: the repair-verb and cooling-independence statements survive."""
    normalized = " ".join(
        (
            ROOT / "docs/architecture/work-intake-and-artifact-routing.md"
        ).read_text(encoding="utf-8").split()
    )

    for statement in (
        "`workspace-status` has two verbs, `repair-plan` and `repair-apply`",
        "`prune`, `retirement-candidates`, and `repair-rollback` have no replacement",
        "Terminal status and artifact retention are independent",
    ):
        assert statement in normalized, statement
    assert "Wave 6 and 7 own ordinary-context exclusion" not in normalized


def test_ac26_architecture_names_cooling_record_and_writer() -> None:
    """AC26: the architecture surface names the cooling record and its writer."""
    normalized = " ".join(
        (
            ROOT / "docs/architecture/work-intake-and-artifact-routing.md"
        ).read_text(encoding="utf-8").split()
    )

    for statement in (
        "Cooling lifecycle record",
        "`close-work` (sole writer)",
        "cooling or deletion policy never substitutes for `Shipped`",
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

    # AC29 wants one thing from this count: that a new erratum is signed. Its
    # wording says "twice" because one occurrence pre-existed in the
    # 2026-08-27 entry, so a single occurrence could not distinguish a signed
    # new erratum from an unsigned one. An exact equality breaks on every
    # later signed erratum — RFC-0096 gained a third on 2026-09-03 — and a
    # >= 2 floor is worse than useless: with three entries it still passes
    # when a signature is stripped, so it cannot fail for the reason it
    # exists. Assert the property itself instead: every entry is signed.
    entries = re.findall(r"- \*\*(\d{4}-\d{2}-\d{2})([^*]*)", errata)
    assert len(entries) >= 2, entries
    unsigned = [d for d, tail in entries if "(Approver:" not in tail]
    assert unsigned == [], f"unsigned erratum entries: {unsigned}"
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
    changelog = (ROOT / "docs/product/changelog.md").read_text(encoding="utf-8")

    pack_version = re.search(r'^version = "([^"]+)"', pack, re.M).group(1)
    heading = re.search(r"^## \[core\]\[([^\]]+)\] — \d{4}-\d{2}-\d{2}", changelog, re.M)

    # pack<->plugin agreement is already pinned by
    # tests/conformance/test_pack_metadata.py, and pack<->newest-[core]-release by
    # tests/roster/test_security_checklists_okf_projection.py. What is not
    # gated elsewhere is that the heading is dated and that the version clears
    # the floor, so only those are asserted here.
    assert heading is not None, "no dated [core] changelog heading found"

    parsed = tuple(int(part) for part in pack_version.split("."))
    assert parsed > (2, 19, 0), parsed
