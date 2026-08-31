"""RFC-0096 Wave 6 — cooling module loading and cooled locator resolution."""

import ast
import datetime
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
STATUS_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
MCP_PATH = ROOT / "packages/agentbundle/agentbundle/workspace_mcp.py"
CLOSE_WORK_SCRIPTS = ROOT / "packs/core/.apm/skills/close-work/scripts"
PACKAGED_DATA = ROOT / "packages/agentbundle/agentbundle/_data"
PACKAGED_CLOSURE = ("cooling.py", "close_work.py", "file_safety.py")
COOLING_PAIRS = (
    ("cool-30-days", "Cooling"),
    ("cool-30-days", "Retired"),
    ("retain-exception", "Retired"),
)


@pytest.fixture()
def engine():
    """Load the source engine without depending on an installed projection."""
    spec = importlib.util.spec_from_file_location("wave6_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _record(*, delivery_id="alpha", disposition="cool-30-days", result="Cooling", **overrides) -> dict:
    """Return a schema-valid delivery lifecycle record payload."""
    payload = {
        "schema": "delivery-lifecycle-record.v1", "delivery_id": delivery_id,
        "locator": f"docs/specs/{delivery_id}/spec.md", "aliases": [],
        "fingerprint": "sha256:" + "0" * 64, "disposition": disposition,
        "post_closeout_result": result, "completion_event": "merge",
        "completion_evidence_ref": "commit:" + "1" * 40,
        "completed_on": "2026-01-01", "timezone": "Asia/Singapore",
        "review_on": "2026-01-31",
        "authority": {name: {"status": "confirmed"} for name in ("source", "write", "delete")},
        "confirmation_proof": "sha256:" + "2" * 64,
    }
    if disposition == "retain-exception":
        payload["exception"] = {"reason": "audit-obligation", "owner_role": "maintainer", "review_on": "2026-02-01"}
    payload.update(overrides)
    return payload


def _tree(tmp_path, *, records=(), specs=("alpha",), lifecycle=True):
    """Build a repository fixture; absent lifecycle is the control state."""
    for slug in specs:
        path = tmp_path / "docs/specs" / slug / "spec.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Spec\n", encoding="utf-8")
    if lifecycle:
        directory = tmp_path / "docs/lifecycle"
        directory.mkdir(parents=True, exist_ok=True)
        for record in records:
            (directory / f"{record['delivery_id']}.json").write_text(json.dumps(record), encoding="utf-8")
    return tmp_path


def _spec(root: Path, slug: str, *, status: str = "Approved", brief: str = "none") -> None:
    """Write a canonical spec and its sibling plan for a workspace fixture."""
    directory = root / "docs/specs" / slug
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "spec.md").write_text(
        f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** {brief}\n",
        encoding="utf-8",
    )
    (directory / "plan.md").write_text("# Plan\n", encoding="utf-8")


def _workspace(
    root: Path,
    *,
    queue: str,
    active: str = "",
    shipped: str = "",
    status: str = "active",
) -> None:
    """Write one active initiative using already-rendered TOML work entries."""
    (root / "workspace.toml").write_text(
        "[\"ini-002\"]\n"
        "name = \"Cooling fixture\"\n"
        f"status = \"{status}\"\n"
        "milestone = \"M1\"\n\n"
        "[\"ini-002\".work]\n"
        f"queue = [{queue}]\n"
        f"active = [{active}]\n"
        f"shipped = [{shipped}]\n\n"
        "[\"ini-002\".shaping_queue]\n"
        "active = []\n"
        "backlog = []\n",
        encoding="utf-8",
    )


def _entry(slug: str, *, needs: str = "[]") -> str:
    """Return a canonical spec work-entry literal for fixture TOML."""
    return (
        '{path = "docs/specs/' + slug + '/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "fixture", needs = ' + needs + "}"
    )


def _load_status_module():
    """Load the source CLI module with its source engine binding."""
    spec = importlib.util.spec_from_file_location("wave6_status", STATUS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        assert module._bind_engine()
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _reconcile_json(root: Path, engine, *, now: datetime.datetime | None = None) -> dict:
    """Build the reconcile projection from the source CLI and source engine."""
    status = _load_status_module()
    return status._build_json(root, engine.analyze(root, now=now), "reconcile")


# STUB: AC1
@pytest.mark.parametrize("pair", COOLING_PAIRS)
def test_only_finished_work_cools(tmp_path, engine, pair) -> None:
    root = _tree(tmp_path, records=[_record(disposition=pair[0], result=pair[1])])
    cooled, findings = engine._resolve_cooled_state(root)
    assert cooled == {(root / "docs/specs/alpha/spec.md").resolve()}
    assert findings == ()


# STUB: AC2
def test_aliases_cool_with_the_locator(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=[_record(aliases=["docs/specs/old-alpha/spec.md"])], specs=("alpha", "old-alpha"))
    cooled, _ = engine._resolve_cooled_state(root)
    assert cooled == {(root / "docs/specs/alpha/spec.md").resolve(), (root / "docs/specs/old-alpha/spec.md").resolve()}


# STUB: AC3
def test_live_obligation_stays_visible(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=[_record(disposition="retain-exception", result="Retained"), _record(delivery_id="beta", disposition="retain-exception", result="ExternalAdvisory")], specs=("alpha", "beta"))
    assert engine._resolve_cooled_state(root)[0] == frozenset()


# STUB: AC4
def test_settled_exception_cools(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=[_record(disposition="retain-exception", result="Retired")])
    assert (root / "docs/specs/alpha/spec.md").resolve() in engine._resolve_cooled_state(root)[0]


def _emitted_findings(root: Path, engine) -> list[dict]:
    """Return `canonical.findings` from the emitted reconcile JSON.

    Six criteria name this surface. Asserting `_resolve_cooled_state`'s internal
    tuple instead let all six pass while the findings reached no output at all,
    because the projection rebuilds findings from a second reconciliation that
    never saw them.
    """
    if not (root / "workspace.toml").exists():
        _workspace(root, queue="")
    return _reconcile_json(root, engine)["canonical"]["findings"]


def _emitted_codes(root: Path, engine) -> list[str]:
    """Return the emitted `canonical.findings` codes for a fixture root."""
    return [finding["code"] for finding in _emitted_findings(root, engine)]


# STUB: AC5
def test_invalid_record_cools_nothing_and_is_named(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=(), specs=())
    (root / "docs/lifecycle/spec-bad.json").write_text('{"schema":"delivery-lifecycle-record.v1"}', encoding="utf-8")
    assert not engine._resolve_cooled_state(root)[0]
    assert [(f["code"], f["path"]) for f in _emitted_findings(root, engine)] == [
        ("invalid_lifecycle_record", "docs/lifecycle/spec-bad.json")
    ]


# STUB: AC6
def test_non_record_file_is_skipped_silently(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=(), specs=())
    (root / "docs/lifecycle/README.md").write_text("not a record", encoding="utf-8")
    assert engine._resolve_cooled_state(root)[0] == frozenset()
    assert "invalid_lifecycle_record" not in _emitted_codes(root, engine)


# STUB: AC7
def test_absent_directory_is_not_an_error(tmp_path, engine) -> None:
    root = _tree(tmp_path, lifecycle=False, specs=())
    assert engine._resolve_cooled_state(root)[0] == frozenset()
    assert not {"invalid_lifecycle_record", "cooling_state_unavailable"} & set(
        _emitted_codes(root, engine)
    )


# STUB: AC8
def test_unusable_directory_is_named(tmp_path, engine) -> None:
    root = _tree(tmp_path, lifecycle=False, specs=())
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle").write_text("not a directory", encoding="utf-8")
    assert _emitted_codes(root, engine) == ["cooling_state_unavailable"]


# STUB: AC9
def test_lifecycle_directory_is_confined(tmp_path, engine) -> None:
    root = _tree(tmp_path / "repo", lifecycle=False, specs=())
    outside = _tree(tmp_path / "outside", records=[_record()], specs=("alpha",)) / "docs/lifecycle"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle").symlink_to(outside, target_is_directory=True)
    assert not engine._resolve_cooled_state(root)[0]
    assert _emitted_codes(root, engine) == ["cooling_state_unavailable"]


# STUB: AC10
def test_symlinked_record_is_refused(tmp_path, engine, monkeypatch) -> None:
    root = _tree(tmp_path, records=[_record()])
    link = root / "docs/lifecycle/spec-link.json"
    link.symlink_to(root / "docs/lifecycle/alpha.json")

    # The refusal alone cannot distinguish the engine's guard from file_safety's
    # own O_NOFOLLOW, which would reject the same link one layer down and emit
    # the same code. What the guard uniquely does is refuse *before* handing the
    # path to the reader, so that is what this pins.
    real = engine._load_cooling_module()
    seen: list[str] = []

    class _Probe:
        """Record every record path handed to the reader, delegating the rest.

        Delegation is not convenience: the emitted projection also calls
        `is_due` and reads record attributes, and a probe that enumerated only
        the methods it knew about would break whenever the engine used one
        more.
        """

        def load_record(self, root_arg, path):
            seen.append(Path(path).name)
            return real.load_record(root_arg, path)

        def __getattr__(self, name):
            return getattr(real, name)

    monkeypatch.setattr(engine, "_load_cooling_module", lambda: _Probe())
    assert ("invalid_lifecycle_record", "docs/lifecycle/spec-link.json") in {
        (f["code"], f["path"]) for f in _emitted_findings(root, engine)
    }
    assert "spec-link.json" not in seen, "symlinked record reached the reader"


# STUB: AC11
def test_oversized_record_refuses_without_raising(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=[])
    (root / "docs/lifecycle/alpha.json").write_bytes(b" " * (65 * 1024))
    assert _emitted_codes(root, engine) == ["invalid_lifecycle_record"]


# STUB: AC12
def test_membership_is_decided_on_the_real_file(tmp_path, engine) -> None:
    """AC12: an alias path is excluded because it resolves to the cooled file.

    The criterion names `canonical.ready`, and only that surface can show it.
    The earlier form asserted the cooled set, whose second clause compared an
    unresolved `Path` against a set of resolved ones -- a membership test that
    cannot hold whatever the code does.
    """
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    (root / "docs/specs/alias-alpha").symlink_to(root / "docs/specs/alpha", target_is_directory=True)
    _workspace(root, queue=_entry("alias-alpha"))

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert all(item["path"] != "docs/specs/alias-alpha/spec.md" for item in ready)

    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    _spec(control, "alpha")
    (control / "docs/specs/alias-alpha").symlink_to(control / "docs/specs/alpha", target_is_directory=True)
    _workspace(control, queue=_entry("alias-alpha"))
    control_ready = [item["path"] for item in _reconcile_json(control, engine)["canonical"]["ready"]]
    assert "docs/specs/alias-alpha/spec.md" in control_ready


# STUB: AC37
def test_packaged_runtime_carries_the_whole_closure() -> None:
    for name in PACKAGED_CLOSURE:
        assert (PACKAGED_DATA / name).read_bytes() == (CLOSE_WORK_SCRIPTS / name).read_bytes()

    # Byte equality alone only proves the files are on disk right now; it does
    # not prove the build declares them, so a shrunk projection list would keep
    # this green until the next clean checkout silently lost the closure.
    source = ast.parse((ROOT / "packages/agentbundle/agentbundle/build/self_host.py").read_text(encoding="utf-8"))
    declared = {
        node.value
        for fn in ast.walk(source)
        if isinstance(fn, ast.FunctionDef) and fn.name == "_runtime_projections"
        for node in ast.walk(fn)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert set(PACKAGED_CLOSURE) <= declared, f"_runtime_projections omits {set(PACKAGED_CLOSURE) - declared}"


# STUB: AC38
def test_every_resolution_route_failing_is_named(tmp_path, engine, monkeypatch) -> None:
    monkeypatch.setattr(engine, "_cooling_module_path", lambda: None)
    monkeypatch.setattr(engine.importlib, "import_module", lambda name: (_ for _ in ()).throw(ImportError(name)))
    assert _emitted_codes(_tree(tmp_path), engine) == ["cooling_state_unavailable"]


# STUB: AC39
def test_failed_cooling_resolution_uses_its_own_finding_code(tmp_path, engine, monkeypatch) -> None:
    monkeypatch.setattr(engine, "_load_cooling_module", lambda: (_ for _ in ()).throw(RuntimeError()))
    assert [f.code for f in engine._resolve_cooled_state(_tree(tmp_path))[1]] == ["cooling_state_unavailable"]


# STUB: AC40
def _candidate_slot(base: Path, slot: int) -> tuple[Path, Path]:
    """Return (engine __file__, candidate cooling.py) for one resolution slot.

    Slot 3 is the dev-source route the shipped source-authority precedent leaves
    unconfined; Wave 6 confines it, so it is the slot the deviation rests on.
    """
    engine_file = base / "pkg/sub/skills/ws/scripts/engine.py"
    engine_file.parent.mkdir(parents=True, exist_ok=True)
    candidate = {
        1: base / "pkg/sub/skills/close-work/scripts/cooling.py",
        2: base / "pkg/sub/skills/ws/scripts/cooling.py",
        3: base / "pkg/packs/core/.apm/skills/close-work/scripts/cooling.py",
    }[slot]
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return engine_file, candidate


# STUB: AC40
@pytest.mark.parametrize("slot", (1, 2, 3))
def test_escaping_module_candidate_is_not_executed(tmp_path, engine, monkeypatch, slot) -> None:
    monkeypatch.setenv("AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY", "1")

    # Escaping half: the candidate is a symlink whose real path leaves its
    # declared root. Its body would write the marker if it were ever executed.
    esc = tmp_path / "escape"
    engine_file, candidate = _candidate_slot(esc, slot)
    esc_marker = tmp_path / f"escaped-{slot}.marker"
    outside = tmp_path / f"outside-{slot}.py"
    outside.write_text(
        f"from pathlib import Path\n"
        f"Path({str(esc_marker)!r}).write_text('x')\n"
        f"def load_record(root, path):\n    return None\n",
        encoding="utf-8",
    )
    candidate.symlink_to(outside)
    monkeypatch.setattr(engine, "__file__", str(engine_file))
    engine._load_cooling_module()  # falls through to a later route
    assert not esc_marker.exists(), f"slot {slot} candidate body executed despite escaping its root"

    # Control half: the same candidate inside its declared root must execute,
    # or the escaping assertion above proves nothing.
    ok = tmp_path / "inroot"
    engine_file, candidate = _candidate_slot(ok, slot)
    ok_marker = tmp_path / f"inroot-{slot}.marker"
    candidate.write_text(
        f"from pathlib import Path\n"
        f"Path({str(ok_marker)!r}).write_text('x')\n"
        f"def load_record(root, path):\n    return None\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(engine, "__file__", str(engine_file))
    engine._load_cooling_module()
    assert ok_marker.exists(), f"slot {slot} control candidate did not execute"


def _plant_close_work(base: Path, script_dir: Path) -> Path:
    """Copy the packaged close_work.py to a layout and plant a live resolver.

    The resolver writes a marker on import, so executing it is observable. It
    also defines every name `_load_regular_sibling` requires, which makes the
    refusal attributable to containment rather than to an incomplete module.
    """
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "close_work.py").write_bytes((PACKAGED_DATA / "close_work.py").read_bytes())
    resolver = script_dir.parents[1] / "work-intake/scripts/surface_resolver.py"
    resolver.parent.mkdir(parents=True, exist_ok=True)
    marker = base / "executed.marker"
    resolver.write_text(
        "import pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text('executed')\n"
        "SURFACE_ROLES = ()\n"
        "class SurfaceCandidate:\n    pass\n"
        "def resolve_surface(*args, **kwargs):\n    return None\n",
        encoding="utf-8",
    )
    return marker


def _load_planted(script_dir: Path, name: str):
    """Load a planted close_work.py copy under its own module name."""
    spec = importlib.util.spec_from_file_location(name, script_dir / "close_work.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: close_work.py defines dataclasses, and dataclasses
    # resolves `sys.modules[cls.__module__]` while building each one.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# STUB: AC41
def test_packaged_closure_opens_nothing_outside_itself(tmp_path) -> None:
    """AC41: the packaged layout refuses the sibling-skill reach.

    The previous form loaded the real `_data/close_work.py` and asserted only
    that the call raised. It raised because nothing sat at that relative path,
    so it would have stayed green while the reach executed an arbitrary planted
    module. Planting one is what makes the refusal mean containment.
    """
    packaged = tmp_path / "packaged"
    marker = _plant_close_work(packaged, packaged / "agentbundle/_data")
    try:
        module = _load_planted(packaged / "agentbundle/_data", "wave6_packaged_close_work")
        with pytest.raises(ImportError):
            module.surface_resolver()
    finally:
        sys.modules.pop("wave6_packaged_close_work", None)
    assert not marker.exists(), "planted resolver was executed from the packaged closure"


def test_installed_skills_tree_still_reaches_its_sibling(tmp_path) -> None:
    """AC41 control: the guard refuses the layout, not the call.

    Without this, a `surface_resolver()` that always raised would satisfy the
    criterion above while removing the capability from every real install.
    """
    installed = tmp_path / "installed"
    marker = _plant_close_work(installed, installed / ".apm/skills/close-work/scripts")
    try:
        module = _load_planted(installed / ".apm/skills/close-work/scripts", "wave6_installed_close_work")
        assert module.surface_resolver() is not None
    finally:
        sys.modules.pop("wave6_installed_close_work", None)
        sys.modules.pop("_close_work_surface_resolver", None)
    assert marker.exists(), "installed layout did not reach its sibling skill"


def test_cooled_body_never_reaches_the_output(tmp_path, engine) -> None:
    """AC13: canonical dependency probes do not read cooled artifacts."""
    needs = '[{type = "local", kind = "spec", path = "docs/specs/alpha/spec.md"}]'
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha", brief="COOLSENTINEL42")
        _spec(root, "beta")
        _workspace(root, queue=_entry("beta", needs=needs))

    control_json = _reconcile_json(control, engine)
    cooled_json = _reconcile_json(cooled, engine)

    assert "COOLSENTINEL42" in json.dumps(control_json)
    assert "COOLSENTINEL42" not in json.dumps(cooled_json)


def test_cooled_dependency_does_not_block_its_dependant(tmp_path, engine) -> None:
    """AC14: a cooled local spec dependency counts as satisfied."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _spec(root, "beta")
    _workspace(
        root,
        queue=_entry(
            "beta",
            needs='[{type = "local", kind = "spec", path = "docs/specs/alpha/spec.md"}]',
        ),
    )

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert [item["path"] for item in ready] == ["docs/specs/beta/spec.md"]


def test_cooled_spec_raises_no_type1_finding(tmp_path, engine) -> None:
    """AC15: the global scan omits cooled, untracked specs."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _workspace(root, queue="")

    control_findings = _reconcile_json(control, engine)["reconciliation"]["type1"]
    cooled_findings = _reconcile_json(cooled, engine)["reconciliation"]["type1"]
    assert [item["spec_path"] for item in control_findings] == ["spec/alpha"]
    assert all(item["spec_path"] != "spec/alpha" for item in cooled_findings)


def test_global_scan_counter_moves_by_exactly_one(tmp_path, engine) -> None:
    """AC16: the cooled Type 1 item is skipped before its read counter increments."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _spec(root, "gamma")
        _workspace(root, queue="")

    control_json = _reconcile_json(control, engine)
    cooled_json = _reconcile_json(cooled, engine)
    assert (
        cooled_json["scan"]["global_scan_spec_files_read"]
        == control_json["scan"]["global_scan_spec_files_read"] - 1
    )
    assert [item["spec_path"] for item in cooled_json["reconciliation"]["type1"]] == ["spec/gamma"]


def test_cooled_queue_entry_never_becomes_dispatchable(tmp_path, engine) -> None:
    """AC17: canonical evaluation drops cooled entries before metadata reads."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    canonical = _reconcile_json(root, engine)["canonical"]
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in canonical["ready"])
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in canonical["evaluations"])


def test_alias_cooled_queue_entry_never_becomes_dispatchable(tmp_path, engine) -> None:
    """Mutation guard: aliases participate in canonical cooling selection."""
    root = _tree(
        tmp_path,
        records=[_record(locator="docs/specs/retired/spec.md", aliases=["docs/specs/alpha/spec.md"])],
        specs=(),
    )
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    canonical = _reconcile_json(root, engine)["canonical"]
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in canonical["evaluations"])


def test_declared_spec_counter_moves_by_exactly_one(tmp_path, engine) -> None:
    """AC18: declared scans omit one cooled entry while retaining beta."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _spec(root, "beta")
        _workspace(root, queue=", ".join((_entry("alpha"), _entry("beta"))))

    control_json = _reconcile_json(control, engine)
    cooled_json = _reconcile_json(cooled, engine)
    assert (
        cooled_json["scan"]["declared_spec_files_read"]
        == control_json["scan"]["declared_spec_files_read"] - 1
    )


def test_uncooled_sibling_still_dispatches(tmp_path, engine) -> None:
    """AC19: cooling alpha does not suppress the uncooled beta sibling."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _spec(root, "beta")
    _workspace(root, queue=", ".join((_entry("alpha"), _entry("beta"))))

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert [item["path"] for item in ready] == ["docs/specs/beta/spec.md"]


def test_legacy_entry_is_excluded_identically(tmp_path, engine) -> None:
    """AC20: legacy entries resolve to cooled files before declared scans read them."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _spec(root, "beta")
        _workspace(root, queue='"spec/alpha", ' + _entry("beta"))

    control_json = _reconcile_json(control, engine)
    cooled_json = _reconcile_json(cooled, engine)
    assert (
        cooled_json["scan"]["declared_spec_files_read"]
        == control_json["scan"]["declared_spec_files_read"] - 1
    )
    assert [item["path"] for item in cooled_json["canonical"]["ready"]] == ["docs/specs/beta/spec.md"]

    # A legacy entry lands in `blocked` through legacy_memberships, not through
    # evaluations, so the assertions above never observed it. The control pins
    # that it is there to be excluded.
    control_blocked = [item["path"] for item in control_json["canonical"]["blocked"]]
    cooled_blocked = [item["path"] for item in cooled_json["canonical"]["blocked"]]
    assert "spec/alpha" in control_blocked
    assert "spec/alpha" not in cooled_blocked


def test_bounded_mode_excludes_identically(tmp_path, engine) -> None:
    """AC21: status's bounded analysis carries the cooled set to canonical evaluation."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    status = _load_status_module()
    data = status._build_json(root, engine.analyze_bounded(root), "status")
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["canonical"]["ready"])


def _mcp_call(root: Path, engine, monkeypatch) -> dict:
    """Invoke the MCP status tool bound to the source engine."""
    spec = importlib.util.spec_from_file_location("wave6_mcp", MCP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, "_load_workspace_status_engine", lambda _: engine)
        bridge = type("Bridge", (), {"get_fsm_state": lambda self: {}, "has_anchored_engine_state": lambda self: False})()
        return module._WorkspaceStatusTool(root, bridge).call()
    finally:
        sys.modules.pop(spec.name, None)


def test_mcp_surface_inherits_the_exclusion(tmp_path, engine, monkeypatch) -> None:
    """AC22: the MCP status tool uses bounded analysis with cooling exclusion."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    data = _mcp_call(root, engine, monkeypatch)
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["ready"])


def test_mcp_surface_names_a_failed_cooling_resolution(tmp_path, engine, monkeypatch) -> None:
    """AC22: the MCP surface carries cooling findings, not only the exclusion.

    Inheriting the exclusion and reporting why it could not be performed are
    separate obligations. Asserting only the first would stay green on a
    surface that silently claimed an exclusion it never made.
    """
    root = _tree(tmp_path, lifecycle=False, specs=())
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle").write_text("not a directory", encoding="utf-8")
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    data = _mcp_call(root, engine, monkeypatch)
    codes = [f["code"] for f in data["canonical"]["findings"]]
    assert codes == ["cooling_state_unavailable"]


def test_explain_mode_excludes_too(tmp_path, engine) -> None:
    """AC36: explain's canonical projection receives bounded cooling state."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    status = _load_status_module()
    data = status._build_explain_json(root, engine.analyze_bounded(root), "alpha", {})
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["canonical"]["evaluations"])


def test_cooling_never_satisfies_a_blocked_dependency(tmp_path, engine) -> None:
    """AC55: a structural block beats cooling satisfaction, on the real surface.

    The block is earned rather than injected: `alpha` is registered twice, so it
    is a duplicate membership and therefore structurally blocked, and it is also
    cooled. Passing a synthetic `structurally_blocked_paths` to
    `_dependency_is_satisfied` proved only that the first line of that function
    runs -- it could not show that a cooled artifact still reaches the set.
    """
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _spec(root, "beta")
    needs = '[{type = "local", kind = "spec", path = "docs/specs/alpha/spec.md"}]'
    _workspace(
        root,
        queue=", ".join([_entry("alpha"), _entry("alpha"), _entry("beta", needs=needs)]),
    )

    canonical = _reconcile_json(root, engine)["canonical"]
    assert all(item["path"] != "docs/specs/beta/spec.md" for item in canonical["ready"])
    assert ("unsatisfied_dependency", "docs/specs/alpha/spec.md") in {
        (f["code"], f["path"]) for f in canonical["findings"]
    }

    # Control: the same cooled dependency without the duplicate. `beta` is ready,
    # so the refusal above is attributable to the structural block and not to
    # cooling refusing every dependency it touches.
    control = _tree(tmp_path / "control", records=[_record()], specs=())
    _spec(control, "alpha")
    _spec(control, "beta")
    _workspace(control, queue=", ".join([_entry("alpha"), _entry("beta", needs=needs)]))
    control_ready = [item["path"] for item in _reconcile_json(control, engine)["canonical"]["ready"]]
    assert control_ready == ["docs/specs/beta/spec.md"]


def test_cooling_never_satisfies_an_unclosed_defect_dependency(tmp_path, engine) -> None:
    """AC56: a cooled defect still requires backlog.closed membership."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _spec(root, "beta")
    dependency = '[{type = "local", kind = "defect", path = "docs/specs/alpha/spec.md"}]'
    _workspace(root, queue=_entry("beta", needs=dependency))

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert all(item["path"] != "docs/specs/beta/spec.md" for item in ready)

    # The gate is the closed membership, not the kind. Deleting the defect
    # branch's `cooled_dependency` refusal reddens this criterion and
    # test_cooled_defect_dependency_does_not_read_its_body.


def _cross_repo_fixture(root: Path, *, cooled: bool, brief_on_disk: bool = True) -> Path:
    """Build a queued spec needing a cross-repo receipt carried by a brief."""
    _spec(root, "beta")
    brief = root / "docs/product/briefs/gamma.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    if brief_on_disk:
        brief.write_text("# Gamma\n", encoding="utf-8")
    if cooled:
        directory = root / "docs/lifecycle"
        directory.mkdir(parents=True, exist_ok=True)
        record = _record(delivery_id="gamma", locator="docs/product/briefs/gamma.md")
        (directory / "gamma.json").write_text(json.dumps(record), encoding="utf-8")
    _workspace(
        root,
        queue=_entry(
            "beta",
            needs=(
                '[{type = "cross-repo", kind = "brief", '
                'path = "docs/product/briefs/gamma.md", '
                'containing_brief = "docs/product/briefs/gamma.md", '
                'receipt_id = "r1", accepted_revision = "rev1"}]'
            ),
        ),
    )
    return root


def _cross_repo_codes(root: Path, engine) -> set[str]:
    """Return the finding codes the reconcile projection emits for a fixture."""
    canonical = _reconcile_json(root, engine)["canonical"]
    assert all(item["path"] != "docs/specs/beta/spec.md" for item in canonical["ready"])
    return {finding["code"] for finding in canonical["findings"]}


def test_cooled_cross_repo_dependency_is_refused_without_a_read(tmp_path, engine) -> None:
    """AC57: the cooled cross-repo path refuses before the brief body is opened."""
    control = _cross_repo_fixture(_tree(tmp_path / "control", lifecycle=False, specs=()), cooled=False)
    cooled = _cross_repo_fixture(_tree(tmp_path / "cooled", specs=()), cooled=True)

    # `invalid_receipt` is emitted only inside `_cross_repo_receipt_satisfied`,
    # so its presence is the signal that the read path was entered.
    assert _cross_repo_codes(control, engine) == {"invalid_receipt"}
    assert _cross_repo_codes(cooled, engine) == {"unsatisfied_dependency"}


def test_cooled_cross_repo_refusal_never_enters_the_receipt_reader(
    tmp_path, engine, monkeypatch
) -> None:
    """Mutation guard: the cooled branch returns before the brief is opened.

    The read this criterion forbids is `brief_path.read_text` inside
    `_cross_repo_receipt_satisfied`, which no other cooled check guards. Proving
    the absence by deleting the brief would prove nothing: an absent locator
    also drops out of the cooled set, so the run would fall through to the read
    path for that reason instead. Recording entry to the reader is the only
    observable that distinguishes the two.
    """
    control = _cross_repo_fixture(_tree(tmp_path / "control", lifecycle=False, specs=()), cooled=False)
    cooled = _cross_repo_fixture(_tree(tmp_path / "cooled", specs=()), cooled=True)
    real = engine._cross_repo_receipt_satisfied
    seen: list[str] = []

    def probe(dep, root_arg):
        """Record the dependency whose brief body is about to be opened."""
        seen.append(dep.path)
        return real(dep, root_arg)

    monkeypatch.setattr(engine, "_cross_repo_receipt_satisfied", probe)
    engine.run_canonical_reconciliation(
        engine.parse_workspace(control / "workspace.toml"), control
    )
    assert seen == ["docs/product/briefs/gamma.md"]
    seen.clear()
    engine.run_canonical_reconciliation(
        engine.parse_workspace(cooled / "workspace.toml"),
        cooled,
        engine._resolve_cooled_state(cooled)[0],
    )
    assert seen == []


def test_cooled_defect_dependency_does_not_read_its_body(tmp_path, engine, monkeypatch) -> None:
    """Mutation guard: the defect probe avoids cooled artifact metadata reads."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _spec(root, "beta")
        _workspace(
            root,
            queue=_entry(
                "beta",
                needs='[{type = "local", kind = "defect", path = "docs/specs/alpha/spec.md"}]',
            ),
        )
    real = engine._metadata_from_root
    seen: list[str] = []

    def probe(root_arg, entry):
        """Record the synthetic dependency target before its metadata is read."""
        if entry.path == "docs/specs/alpha/spec.md":
            seen.append(entry.path)
        return real(root_arg, entry)

    monkeypatch.setattr(engine, "_metadata_from_root", probe)
    engine.run_canonical_reconciliation(
        engine.parse_workspace(control / "workspace.toml"), control
    )
    assert seen == ["docs/specs/alpha/spec.md"]
    seen.clear()
    engine.run_canonical_reconciliation(
        engine.parse_workspace(cooled / "workspace.toml"),
        cooled,
        engine._resolve_cooled_state(cooled)[0],
    )
    assert seen == []


def test_alias_declared_dependency_does_not_read_its_body(tmp_path, engine) -> None:
    """Mutation guard: dependency cooling compares resolved artifact paths."""
    root = _tree(tmp_path, records=[_record(locator="docs/specs/alias-alpha/spec.md")], specs=())
    _spec(root, "alpha", brief="COOLSENTINEL42")
    (root / "docs/specs/alias-alpha").symlink_to(root / "docs/specs/alpha", target_is_directory=True)
    _spec(root, "beta")
    _workspace(
        root,
        queue=_entry(
            "beta",
            needs='[{type = "local", kind = "spec", path = "docs/specs/alpha/spec.md"}]',
        ),
    )

    assert "COOLSENTINEL42" not in json.dumps(_reconcile_json(root, engine))


def test_due_reviews_are_counted_and_named(tmp_path, engine) -> None:
    """AC23–AC26: due records project bounded review and evidence fields."""
    root = _tree(tmp_path, records=[
        _record(delivery_id="spec-a", completed_on="2026-07-02", review_on="2026-08-01"),
        _record(delivery_id="spec-b", completed_on="2098-12-02", review_on="2099-01-01"),
    ], specs=("spec-a", "spec-b"))
    _workspace(root, queue="")
    data = _reconcile_json(
        root, engine, now=datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    )
    cooling = data["cooling"]
    assert cooling["due_count"] == 1
    assert {record["delivery_id"] for record in cooling["records"]} == {"spec-a", "spec-b"}
    assert cooling["due"] == [{
        "delivery_id": "spec-a", "locator": "docs/specs/spec-a/spec.md", "review_on": "2026-08-01",
    }]
    record = next(item for item in cooling["records"] if item["delivery_id"] == "spec-a")
    assert set(record) == {
        "delivery_id", "locator", "disposition", "post_closeout_result",
        "completion_event", "completion_evidence_ref", "review_on", "due",
    }
    assert (record["completion_event"], record["completion_evidence_ref"]) == (
        "merge", "commit:" + "1" * 40,
    )


def test_retention_exceptions_and_retired_records_project_correctly(tmp_path, engine) -> None:
    """AC27–AC28: retained work is visible; retired work is never due."""
    root = _tree(tmp_path, records=[
        _record(delivery_id="retained", disposition="retain-exception", result="Retained"),
        _record(delivery_id="retired", disposition="retain-exception", result="Retired", completed_on="2026-07-02", review_on="2026-08-01"),
    ], specs=("retained", "retired"))
    _workspace(root, queue="")
    cooling = _reconcile_json(
        root, engine, now=datetime.datetime(2026, 8, 30, tzinfo=datetime.UTC)
    )["cooling"]
    assert cooling["exceptions"] == [{
        "delivery_id": "retained", "locator": "docs/specs/retained/spec.md",
        "owner_role": "maintainer", "reason": "audit-obligation", "review_on": "2026-02-01",
    }]
    retired = next(item for item in cooling["records"] if item["delivery_id"] == "retired")
    assert retired["due"] is False
    assert all(item["delivery_id"] != "retired" for item in cooling["due"] + cooling["exceptions"])


def test_closeout_facts_are_projected(tmp_path, engine) -> None:
    """AC29–AC32: closeout reflects pause, queue state, and reconciliation."""
    root = _tree(tmp_path, records=[_record()], specs=("alpha",))
    _workspace(root, queue="")
    closeout = _reconcile_json(root, engine)["closeout"]
    assert set(closeout) == {
        "paused", "all_specs_shipped", "closeout_blockers", "initiative_eligible",
        "next_action", "cooling_context_visible",
    }
    assert closeout["next_action"] == "invoke-close-work"
    _workspace(root, queue="", status="paused")
    assert _reconcile_json(root, engine)["closeout"]["next_action"] == "resume-or-keep-paused"
    _workspace(root, queue=_entry("alpha"))
    assert "unshipped-specs" in _reconcile_json(root, engine)["closeout"]["closeout_blockers"]


@pytest.mark.parametrize("mode", ("status", "reconcile"))
@pytest.mark.parametrize("failure", ("invalid", "unavailable"))
def test_exclusion_claim_is_earned_not_declared(tmp_path, engine, mode, failure) -> None:
    """AC33: lifecycle refusals fail closed on the exclusion claim."""
    root = _tree(tmp_path, records=[_record()], specs=("alpha",))
    _workspace(root, queue="")
    if failure == "invalid":
        (root / "docs/lifecycle/alpha.json").write_text(
            '{"schema":"delivery-lifecycle-record.v1"}', encoding="utf-8"
        )
    else:
        root = _tree(tmp_path / "unavailable", lifecycle=False, specs=("alpha",))
        _workspace(root, queue="")
        (root / "docs/lifecycle").write_text("unavailable", encoding="utf-8")
    status = _load_status_module()
    result = engine.analyze_bounded(root) if mode == "status" else engine.analyze(root)
    assert status._build_json(root, result, mode)["closeout"]["cooling_context_visible"] is True


def test_clean_cooling_state_and_unrelated_canonical_refusal_keep_claim_false(tmp_path, engine) -> None:
    """AC33–AC34: only cooling findings determine the visibility claim."""
    root = _tree(tmp_path, records=[_record()], specs=("alpha",))
    _workspace(root, queue=(
        '{locator = {kind = "external", value = "https://example.test/alpha"}, '
        'kind = "spec", surface_role = "user-documentation", source = {mode = "repo-origin"}, '
        'summary = "fixture", needs = []}'
    ))
    data = _reconcile_json(root, engine)
    assert any(
        finding["code"] == "configuration_mismatch"
        for item in data["canonical"]["evaluations"]
        for finding in item["findings"]
    )
    assert data["closeout"]["cooling_context_visible"] is False


def test_only_ordinary_orientation_carries_cooling_and_closeout(tmp_path, engine) -> None:
    """AC35: repair-plan's shared builder stays outside the positive mode gate."""
    root = _tree(tmp_path, records=[_record()], specs=("alpha",))
    _workspace(root, queue="")
    status = _load_status_module()
    result = engine.analyze(root)
    repair = status._build_repair_plan_json(root, result, engine.compute_repair_plan(result, root / "workspace.toml"))
    explain = status._build_explain_json(root, engine.analyze_bounded(root), "alpha", {})
    assert {"cooling", "closeout"}.isdisjoint(repair)
    assert {"cooling", "closeout"}.isdisjoint(explain)


def test_dueness_uses_the_recorded_zone_and_default_clock(tmp_path, engine) -> None:
    """AC42–AC43: projection delegates to Wave 5 with an aware production clock."""
    root = _tree(tmp_path, records=[_record(completed_on="2026-08-01", review_on="2026-08-31")])
    _workspace(root, queue="")
    zone_boundary = datetime.datetime(2026, 8, 30, 16, 30, tzinfo=datetime.UTC)
    assert _reconcile_json(root, engine, now=zone_boundary)["cooling"]["records"][0]["due"] is True
    root = _tree(tmp_path / "default", records=[_record(completed_on="2019-12-02", review_on="2020-01-01")])
    _workspace(root, queue="")
    assert _reconcile_json(root, engine)["cooling"]["due_count"] == 1


def test_non_boolean_visibility_fact_is_refused(engine) -> None:
    """AC44: the Wave 4 type guard survives context-exclusion support."""
    with pytest.raises(ValueError, match="boolean facts"):
        engine.project_closeout_status(
            paused=False,
            all_specs_shipped=True,
            closeout_blockers=[],
            cooling_context_visible="no",
        )
