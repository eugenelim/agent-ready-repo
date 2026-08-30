"""RFC-0096 Wave 6 — cooling module loading and cooled locator resolution."""

import ast
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


def _workspace(root: Path, *, queue: str, active: str = "", shipped: str = "") -> None:
    """Write one active initiative using already-rendered TOML work entries."""
    (root / "workspace.toml").write_text(
        "[\"ini-002\"]\n"
        "name = \"Cooling fixture\"\n"
        "status = \"active\"\n"
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


def _reconcile_json(root: Path, engine) -> dict:
    """Build the reconcile projection from the source CLI and source engine."""
    status = _load_status_module()
    return status._build_json(root, engine.analyze(root), "reconcile")


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


# STUB: AC5
def test_invalid_record_cools_nothing_and_is_named(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=(), specs=())
    (root / "docs/lifecycle/spec-bad.json").write_text('{"schema":"delivery-lifecycle-record.v1"}', encoding="utf-8")
    cooled, findings = engine._resolve_cooled_state(root)
    assert not cooled and [(f.code, f.path) for f in findings] == [("invalid_lifecycle_record", "docs/lifecycle/spec-bad.json")]


# STUB: AC6
def test_non_record_file_is_skipped_silently(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=(), specs=())
    (root / "docs/lifecycle/README.md").write_text("not a record", encoding="utf-8")
    assert engine._resolve_cooled_state(root) == (frozenset(), ())


# STUB: AC7
def test_absent_directory_is_not_an_error(tmp_path, engine) -> None:
    root = _tree(tmp_path, lifecycle=False, specs=())
    assert engine._resolve_cooled_state(root) == (frozenset(), ())


# STUB: AC8
def test_unusable_directory_is_named(tmp_path, engine) -> None:
    root = _tree(tmp_path, lifecycle=False, specs=())
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle").write_text("not a directory", encoding="utf-8")
    assert [f.code for f in engine._resolve_cooled_state(root)[1]] == ["cooling_state_unavailable"]


# STUB: AC9
def test_lifecycle_directory_is_confined(tmp_path, engine) -> None:
    root = _tree(tmp_path / "repo", lifecycle=False, specs=())
    outside = _tree(tmp_path / "outside", records=[_record()], specs=("alpha",)) / "docs/lifecycle"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle").symlink_to(outside, target_is_directory=True)
    cooled, findings = engine._resolve_cooled_state(root)
    assert not cooled and [f.code for f in findings] == ["cooling_state_unavailable"]


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
        def load_record(self, root_arg, path):
            seen.append(Path(path).name)
            return real.load_record(root_arg, path)

    monkeypatch.setattr(engine, "_load_cooling_module", lambda: _Probe())
    _, findings = engine._resolve_cooled_state(root)
    assert ("invalid_lifecycle_record", "docs/lifecycle/spec-link.json") in {(f.code, f.path) for f in findings}
    assert "spec-link.json" not in seen, "symlinked record reached the reader"


# STUB: AC11
def test_oversized_record_refuses_without_raising(tmp_path, engine) -> None:
    root = _tree(tmp_path, records=[])
    (root / "docs/lifecycle/alpha.json").write_bytes(b" " * (65 * 1024))
    assert [f.code for f in engine._resolve_cooled_state(root)[1]] == ["invalid_lifecycle_record"]


# STUB: AC12
def test_membership_is_decided_on_the_real_file(tmp_path, engine) -> None:
    # The record names the artifact through an in-root alias symlink, so the
    # stored member differs from the literal locator unless it is resolved.
    root = _tree(tmp_path, records=[_record(locator="docs/specs/alias-alpha/spec.md")])
    (root / "docs/specs/alias-alpha").symlink_to(root / "docs/specs/alpha", target_is_directory=True)
    cooled, _ = engine._resolve_cooled_state(root)
    assert cooled == {(root / "docs/specs/alpha/spec.md").resolve()}
    assert (root / "docs/specs/alias-alpha/spec.md") not in cooled


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
    assert [f.code for f in engine._resolve_cooled_state(_tree(tmp_path))[1]] == ["cooling_state_unavailable"]


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


# STUB: AC41
def test_packaged_closure_opens_nothing_outside_itself() -> None:
    spec = importlib.util.spec_from_file_location("packaged_close_work", PACKAGED_DATA / "close_work.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: close_work.py defines dataclasses, and dataclasses
    # resolves `sys.modules[cls.__module__]` while building each one.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        with pytest.raises((ImportError, OSError, ValueError)):
            module.surface_resolver()
    finally:
        sys.modules.pop(spec.name, None)


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


def test_bounded_mode_excludes_identically(tmp_path, engine) -> None:
    """AC21: status's bounded analysis carries the cooled set to canonical evaluation."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    status = _load_status_module()
    data = status._build_json(root, engine.analyze_bounded(root), "status")
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["canonical"]["ready"])


def test_mcp_surface_inherits_the_exclusion(tmp_path, engine, monkeypatch) -> None:
    """AC22: the MCP status tool uses bounded analysis with cooling exclusion."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))
    spec = importlib.util.spec_from_file_location("wave6_mcp", MCP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, "_load_workspace_status_engine", lambda _: engine)
        bridge = type("Bridge", (), {"get_fsm_state": lambda self: {}, "has_anchored_engine_state": lambda self: False})()
        data = module._WorkspaceStatusTool(root, bridge).call()
    finally:
        sys.modules.pop(spec.name, None)

    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["ready"])


def test_explain_mode_excludes_too(tmp_path, engine) -> None:
    """AC36: explain's canonical projection receives bounded cooling state."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))

    status = _load_status_module()
    data = status._build_explain_json(root, engine.analyze_bounded(root), "alpha", {})
    assert all(item["path"] != "docs/specs/alpha/spec.md" for item in data["canonical"]["evaluations"])


def test_cooling_never_satisfies_a_blocked_dependency(tmp_path, engine) -> None:
    """AC55: a structural block beats local-spec cooling satisfaction."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    dependency = engine.Dependency(
        type="local",
        kind="spec",
        path="docs/specs/alpha/spec.md",
    )
    satisfied, finding = engine._dependency_is_satisfied(
        dependency,
        {},
        {},
        {dependency.path},
        root,
        engine._resolve_cooled_state(root)[0],
    )
    assert not satisfied
    assert finding is not None and finding.code == "unsatisfied_dependency"


def test_cooling_satisfies_only_local_spec_dependencies(tmp_path, engine) -> None:
    """AC56: a cooled defect still requires backlog.closed membership."""
    root = _tree(tmp_path, records=[_record()], specs=())
    _spec(root, "alpha")
    _spec(root, "beta")
    dependency = '[{type = "local", kind = "defect", path = "docs/specs/alpha/spec.md"}]'
    _workspace(root, queue=_entry("beta", needs=dependency))

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert all(item["path"] != "docs/specs/beta/spec.md" for item in ready)


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
