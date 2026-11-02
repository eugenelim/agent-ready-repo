"""RFC-0096 Wave 6 — cooling module loading and cooled locator resolution."""

import ast
import datetime
import importlib.util
import json
import re
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
    ("retain-exception", "Reclassified"),
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


def _depend_on(root: Path, slug: str, *refs: str, receipts: str = "") -> None:
    """Record a spec's dependencies in its own `Depends on:` header.

    `receipts` is the text of a `Dependency receipts:` line, when one is needed.
    The lines go directly after the spec's `Brief:` line, inside the preamble.
    """
    spec = root / "docs/specs" / slug / "spec.md"
    lines = [f"- **Depends on:** {', '.join(refs)}\n"]
    if receipts:
        lines.append(f"- **Dependency receipts:** {receipts}\n")
    text = spec.read_text(encoding="utf-8")
    marker = "- **Brief:**"
    start = text.index(marker)
    end = text.index("\n", start) + 1
    spec.write_text(text[:end] + "".join(lines) + text[end:], encoding="utf-8")


def _workspace(
    root: Path,
    *,
    queue: str,
    active: str = "",
    shipped: str = "",
    status: str = "active",
    backlog_open: str = "",
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
        "backlog = []\n"
        + (f"\n[backlog]\nopen = [{backlog_open}]\nclosed = []\n" if backlog_open else ""),
        encoding="utf-8",
    )


def _entry(slug: str, *, needs: str = "[]") -> str:
    """Return a canonical spec work-entry literal for fixture TOML."""
    return (
        '{path = "docs/specs/' + slug + '/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "fixture", needs = ' + needs + "}"
    )


def _load_status_module():
    """Load the source CLI module, leaving no engine entry in `sys.modules`.

    The CLI execs its own engine copy: `_bind_engine` builds a spec from the
    file path, creates a fresh module and binds every symbol from *that* object,
    so a caller cannot inject one. An earlier version of this helper
    pre-registered the fixture's engine and documented that the two would share
    a module — `setdefault` only suppressed the registration, and
    `status.run_canonical_reconciliation is engine.run_canonical_reconciliation`
    stayed False. The claim is removed rather than left for a future test to
    rely on. A monkeypatch on the `engine` fixture reaches the CLI only through
    the result object a test passes to `_build_json`, never through the CLI's
    own copy.

    The parameter was dropped with the claim: a call site reading
    `_load_status_module(engine)` implies an injection that does not happen. The
    `sys.modules` cleanup below is kept — that part does work, and is what stops
    the CLI's copy leaking into every suite that runs afterwards.
    """
    spec = importlib.util.spec_from_file_location("wave6_status", STATUS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sentinel = object()
    previous = sys.modules.get("workspace_status_engine", sentinel)
    try:
        spec.loader.exec_module(module)
        assert module._bind_engine()
    finally:
        sys.modules.pop(spec.name, None)
        if previous is sentinel:
            sys.modules.pop("workspace_status_engine", None)
        else:
            sys.modules["workspace_status_engine"] = previous
    return module


def _reconcile_json(root: Path, engine, *, now: datetime.datetime | None = None) -> dict:
    """Build the reconcile projection from the source CLI and source engine."""
    status = _load_status_module()
    return status._build_json(root, engine.analyze(root, now=now), "reconcile")


def test_the_fixture_pairs_are_the_engine_pairs(engine) -> None:
    """The parametrization is the engine's own predicate, not a copy of it.

    AC1 drives its cases from the list above. Left unasserted, the engine could
    gain or lose a pair and AC1 would keep testing the old set, reporting a
    coverage it no longer had.
    """
    assert frozenset(COOLING_PAIRS) == engine._COOLING_PAIRS


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
    """AC3: a live obligation changes neither the scan count nor `ready`.

    Asserted on the two surfaces the criterion names, against a control with
    `docs/lifecycle/` removed. The earlier form asserted the internal cooled
    set, which cannot see an emission filter that drops `Retained` artifacts
    after the set is computed correctly.
    """
    records = [
        _record(disposition="retain-exception", result="Retained"),
        _record(delivery_id="beta", disposition="retain-exception", result="ExternalAdvisory"),
    ]
    live = _tree(tmp_path / "live", records=records, specs=())
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    for root in (live, control):
        _spec(root, "alpha")
        _spec(root, "beta")
        _workspace(root, queue=", ".join([_entry("alpha"), _entry("beta")]))

    live_json = _reconcile_json(live, engine)
    control_json = _reconcile_json(control, engine)
    assert [i["path"] for i in live_json["canonical"]["ready"]] == [
        i["path"] for i in control_json["canonical"]["ready"]
    ]
    assert (
        live_json["scan"]["declared_spec_files_read"]
        == control_json["scan"]["declared_spec_files_read"]
    )
    # Both specs are genuinely offered, so the equality above is between two
    # populated runs rather than between two empty ones.
    assert len(live_json["canonical"]["ready"]) == 2


# STUB: AC4
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
# STUB: AC9
# STUB: AC10
# STUB: AC11
# STUB: AC12
def _normalized(relative: str) -> str:
    """Whitespace-normalized file text, the idiom these criteria name."""
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


def test_prose_criteria_have_their_verification_artifact() -> None:
    """AC49, AC50, AC51 and AC52 assert the strings and digest they name.

    All four were declared covered while nothing asserted them: the literal
    strings appeared only in the documents they describe and in the spec, and
    AC52's digest existed only as spec prose, so an edit to a Frozen body was
    undetectable. Prose cannot hold a pinned digest.
    """
    import hashlib

    reference = _normalized("guides/core/reference/work-intake-routing-and-lifecycle.md")
    assert "closeout blockers, cooling visibility" not in reference  # AC49
    assert "never loads a cooled artifact body" in reference

    skill = _normalized("packs/core/.apm/skills/workspace-status/SKILL.md")  # AC50
    assert "remains visible because ordinary-context exclusion is not part of this wave" not in skill

    spec = (ROOT / "docs/specs/status-projection-and-context-exclusion/spec.md").read_text(
        encoding="utf-8"
    )
    for slug in ("cooling-repair-migration-scope", "wave6-dependency-scoped-completion-receipts"):
        row = next(
            (line for line in spec.splitlines() if line.startswith(f"| `{slug}` |")),
            None,
        )
        assert row is not None, slug  # AC51
        # "each with an owner" is part of the criterion, so assert the cell.
        assert row.rstrip().rstrip("|").rsplit("|", 1)[-1].strip(), f"{slug} has no owner"
    # Per criterion line, not per file: the Follow-ons prose names the token to
    # explain why this spec does not use one, and a whole-file search cannot
    # tell that mention apart from a use.
    # Both box states. Matching only `- [ ] **AC` deadlocked closeout against
    # lint-spec-status invariant (ii), which requires every criterion `[x]` at
    # the ship transition: the two gates could not both pass.
    criteria = [
        line for line in spec.splitlines()
        if re.match(r"- \[[ x]\] \*\*AC", line.lstrip())
    ]
    assert criteria, "no criterion lines found; the shape this asserts has changed"
    assert not [line for line in criteria if "(deferred:" in line]

    frozen = ROOT / "docs/specs/close-work-extraction-and-immediate-disposition/spec.md"
    digest = hashlib.sha256(frozen.read_bytes()).hexdigest()  # AC52
    assert digest == "4f1b98e7fdb53a4726a65432ef2993a7f0db1f65987c46bd00763a999915de8a", (
        "Wave 4's frozen spec changed; AC52 pins its bytes"
    )


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
# STUB: AC39
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
        # Both callables: _load_cooling_module guards the whole contract the
        # projection uses, so a planted module defining only load_record would
        # be refused for its shape and never reach the execution question this
        # criterion is about.
        f"def load_record(root, path):\n    return None\n"
        f"def is_due(record, now):\n    return None\n",
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
        # Both callables: _load_cooling_module guards the whole contract the
        # projection uses, so a planted module defining only load_record would
        # be refused for its shape and never reach the execution question this
        # criterion is about.
        f"def load_record(root, path):\n    return None\n"
        f"def is_due(record, now):\n    return None\n",
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


def test_cooled_spec_raises_no_type1_finding(tmp_path, engine) -> None:
    """AC-0041: the Type 1 audit is empty for a cooled tree as for a control tree."""
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _workspace(root, queue="")

    control_findings = _reconcile_json(control, engine)["reconciliation"]["type1"]
    cooled_findings = _reconcile_json(cooled, engine)["reconciliation"]["type1"]
    assert control_findings == []
    assert cooled_findings == []


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
    assert cooled_json["reconciliation"]["type1"] == []


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

    # A legacy entry is now unsupported_legacy and lands in canonical.findings,
    # not in blocked.  Both control and cooled have the same blocked set (only
    # canonical entries with evaluation findings appear there).
    control_blocked = [item["path"] for item in control_json["canonical"]["blocked"]]
    cooled_blocked = [item["path"] for item in cooled_json["canonical"]["blocked"]]
    assert "spec/alpha" not in control_blocked
    assert "spec/alpha" not in cooled_blocked

    # The `unsupported_legacy` finding is deliberately retained: it is a fact
    # about the workspace entry's shape, not about the artifact.  Pinning it
    # keeps the boundary explicit, so a later blanket filter over findings has
    # to change this line and state why.
    assert ("unsupported_legacy", "spec/alpha") in {
        (f["code"], f["path"]) for f in cooled_json["canonical"]["findings"]
    }


DEFECT_PATH = "docs/product/captured/alpha.md"


def _defect_fixture(base: Path, *, cooled: bool) -> Path:
    """A queued spec waiting on an open defect, itself cooled when asked.

    A defect is a captured item, so the header names its path, a record in
    `docs/product/captured/`. Its registered `backlog.open` membership gives the
    reference its kind without opening a cooled body.
    """
    root = _tree(
        base,
        records=[_record(locator=DEFECT_PATH)] if cooled else [],
        specs=(),
        lifecycle=cooled,
    )
    defect = root / DEFECT_PATH
    defect.parent.mkdir(parents=True, exist_ok=True)
    defect.write_text("# Defect\n\n- **Status:** Open\n- **Kind:** defect\n", encoding="utf-8")
    _spec(root, "beta")
    _depend_on(root, "beta", DEFECT_PATH)
    _workspace(
        root,
        queue=_entry("beta"),
        backlog_open=(
            f'{{path = "{DEFECT_PATH}", kind = "defect", '
            'source = {mode = "repo-origin"}, summary = "fixture", needs = []}'
        ),
    )
    return root


def test_cooling_never_satisfies_an_unclosed_defect_dependency(tmp_path, engine) -> None:
    """AC56: a cooled defect still requires backlog.closed membership."""
    root = _defect_fixture(tmp_path, cooled=True)

    ready = _reconcile_json(root, engine)["canonical"]["ready"]
    assert all(item["path"] != "docs/specs/beta/spec.md" for item in ready)

    # The gate is the closed membership, not the kind. The mutation that kills
    # this criterion is hoisting `if cooled_dependency: return True` above the
    # defect branch. Deleting that branch's refusal does NOT kill it — the
    # dependency falls through to the probe and still returns
    # `unsatisfied_dependency`, so `beta` stays out of `ready`; only
    # test_cooled_defect_dependency_does_not_read_its_body dies to that one.


def _cross_repo_fixture(root: Path, *, cooled: bool, brief_on_disk: bool = True) -> Path:
    """Build a queued spec needing a cross-repo receipt carried by a brief."""
    _spec(root, "beta")
    _depend_on(
        root, "beta", "brief:gamma",
        receipts="brief:gamma coordination brief r1 rev1",
    )
    brief = root / "docs/product/briefs/gamma.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    if brief_on_disk:
        brief.write_text("# Gamma\n", encoding="utf-8")
    if cooled:
        directory = root / "docs/lifecycle"
        directory.mkdir(parents=True, exist_ok=True)
        record = _record(delivery_id="gamma", locator="docs/product/briefs/gamma.md")
        (directory / "gamma.json").write_text(json.dumps(record), encoding="utf-8")
    _workspace(root, queue=_entry("beta"))
    return root


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


def test_repository_identity_does_not_read_cooled_bodies(tmp_path, engine, monkeypatch) -> None:
    """The identity fingerprint is derived without opening a cooled artifact.

    This was round 2's largest production defect and it landed with no guard:
    `canonical_repository_identity` iterates the deliberately-unfiltered
    memberships and fingerprinted each artifact by reading it, twice per run, on
    all four ordinary surfaces. AC13 cannot see it because only the SHA-256
    reaches the output, so the read has to be observed directly.
    """
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        entry = _entry("alpha")
        _workspace(root, queue=entry, active=entry, shipped=entry)

    seen: list[str] = []
    real_fingerprint = engine.extract_spec_status_with_fingerprint
    real_metadata = engine._metadata_from_root

    def probe_fingerprint(path):
        seen.append(str(path))
        return real_fingerprint(path)

    def probe_metadata(root_arg, entry_arg):
        if entry_arg.path == "docs/specs/alpha/spec.md":
            seen.append(entry_arg.path)
        return real_metadata(root_arg, entry_arg)

    monkeypatch.setattr(engine, "extract_spec_status_with_fingerprint", probe_fingerprint)
    monkeypatch.setattr(engine, "_metadata_from_root", probe_metadata)

    def identity(root):
        seen.clear()
        workspace = engine.parse_workspace(root / "workspace.toml")
        canonical = engine.run_canonical_reconciliation(
            workspace, root, engine._resolve_cooled_state(root)[0]
        )
        engine.canonical_repository_identity(workspace, canonical, root)
        return list(seen)

    assert identity(control), "control never reached the artifact; the probe proves nothing"
    assert identity(cooled) == []


def test_cooled_defect_dependency_does_not_read_its_body(tmp_path, engine, monkeypatch) -> None:
    """Mutation guard: the defect probe avoids cooled artifact metadata reads."""
    control = _defect_fixture(tmp_path / "control", cooled=False)
    cooled = _defect_fixture(tmp_path / "cooled", cooled=True)
    real = engine._metadata_from_root
    seen: list[str] = []

    def probe(root_arg, entry):
        """Record the synthetic dependency target before its metadata is read."""
        if entry.path == DEFECT_PATH:
            seen.append(entry.path)
        return real(root_arg, entry)

    real_record = engine._captured_record_metadata

    def probe_record(root_arg, entry):
        """A captured-item file's probe reads through its record reader."""
        if entry.path == DEFECT_PATH:
            seen.append(entry.path)
        return real_record(root_arg, entry)

    monkeypatch.setattr(engine, "_metadata_from_root", probe)
    monkeypatch.setattr(engine, "_captured_record_metadata", probe_record)
    engine.run_canonical_reconciliation(
        engine.parse_workspace(control / "workspace.toml"), control
    )
    # The control reaches the probe through the dependency on an unclosed
    # defect; it only has to prove the probe is reachable.
    assert seen, "control never read the defect; the probe proves nothing"
    seen.clear()
    engine.run_canonical_reconciliation(
        engine.parse_workspace(cooled / "workspace.toml"),
        cooled,
        engine._resolve_cooled_state(cooled)[0],
    )
    assert seen == []


def test_an_inactive_initiative_is_still_reported_for_a_cooled_entry(tmp_path, engine) -> None:
    """The cooled branch keeps every membership-derived finding, not just one.

    Only `duplicate_membership` was pinned, so moving the cooled early return
    above the `inactive_initiative` check silently stopped reporting a live
    workspace fact for any cooled entry, with the suite green.
    """
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    for root in (cooled, control):
        _spec(root, "alpha")
        _workspace(root, queue=_entry("alpha"), status="paused")

    def codes(root):
        return {
            (f["code"], f["path"])
            for f in _reconcile_json(root, engine)["canonical"]["findings"]
        }

    expected = ("inactive_initiative", "docs/specs/alpha/spec.md")
    assert expected in codes(control)
    assert expected in codes(cooled)


def test_cooling_both_halves_of_a_duplicate_still_reports_it(tmp_path, engine) -> None:
    """A duplicate workspace entry survives cooling both of its memberships.

    `duplicate_membership` is a fact about the `workspace.toml` entries, which
    AC20 settles is still owed whatever the artifact's state. Cooled
    memberships are excluded from `evaluations`, and the emitted finding list is
    built from those, so cooling both halves erased the finding entirely while
    a live third membership would have kept it — which is why a single-cooled
    fixture could not see this.
    """
    entry = _entry("alpha")
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    for root in (cooled, control):
        _spec(root, "alpha")
        _workspace(root, queue=entry, active=entry)

    def duplicates(root):
        return {
            (f["code"], f["path"])
            for f in _reconcile_json(root, engine)["canonical"]["findings"]
            if f["code"] == "duplicate_membership"
        }

    assert duplicates(control) == {("duplicate_membership", "docs/specs/alpha/spec.md")}
    assert duplicates(cooled) == {("duplicate_membership", "docs/specs/alpha/spec.md")}


def test_absent_lifecycle_directory_is_clean_even_with_no_cooling_module(
    tmp_path, engine, monkeypatch
) -> None:
    """AC7 holds for the input it was actually failing on.

    The precheck exists for one case -- no `docs/lifecycle/` AND no resolvable
    closure -- which neither AC7's nor AC38's fixture produced, so deleting it
    survived the suite.
    """
    root = _tree(tmp_path, lifecycle=False, specs=())
    _workspace(root, queue="")
    monkeypatch.setattr(
        engine, "_load_cooling_module", lambda: (_ for _ in ()).throw(RuntimeError())
    )
    assert engine._resolve_cooled_state(root) == (frozenset(), ())
    assert _emitted_codes(root, engine) == []


def test_packaged_layout_does_not_reach_a_sibling_cooling_module(
    tmp_path, engine, monkeypatch
) -> None:
    """The confinement predicate is exercised on the layout it exists for.

    AC40 covers only the allowed branch, so `sibling_reach_allowed = True`
    survived. Under a `_data/`-shaped path the sibling candidate must not be
    resolved at all.
    """
    data_dir = tmp_path / "pkg" / "agentbundle" / "_data"
    data_dir.mkdir(parents=True)
    sibling = tmp_path / "pkg" / "close-work" / "scripts"
    sibling.mkdir(parents=True)
    (sibling / "cooling.py").write_text("raise AssertionError('sibling executed')\n")

    monkeypatch.setattr(engine, "__file__", str(data_dir / "workspace_status_engine.py"))
    assert engine._cooling_module_path() is None

    # Control: the same plant in a skills-shaped tree IS reachable, so the
    # assertion above is about the layout and not about the file being absent.
    skills = tmp_path / "tree" / ".apm" / "skills"
    (skills / "workspace-status" / "scripts").mkdir(parents=True)
    reachable = skills / "close-work" / "scripts"
    reachable.mkdir(parents=True)
    (reachable / "cooling.py").write_text("# placeholder\n")
    monkeypatch.setattr(
        engine, "__file__",
        str(skills / "workspace-status" / "scripts" / "workspace_status_engine.py"),
    )
    assert engine._cooling_module_path() == (reachable / "cooling.py").resolve()


# ── AC59: brief child scope ────────────────────────────────────────────────────

BRIEF_PATH = "docs/product/briefs/brief-1.md"
BRIEF_REF = "brief:brief-1"  # the brief has no `Slug:`, so its file stem names it


def _brief_body(root: Path, *, status: str = "Shipped") -> None:
    """Write a brief artifact body."""
    path = root / BRIEF_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Brief\n\n- **Status:** {status}\n",
        encoding="utf-8",
    )


def _cool_child(root: Path) -> None:
    """Write a Cooling lifecycle record for docs/specs/child/spec.md."""
    directory = root / "docs/lifecycle"
    directory.mkdir(parents=True, exist_ok=True)
    record = _record(delivery_id="child", locator="docs/specs/child/spec.md")
    (directory / "child.json").write_text(json.dumps(record), encoding="utf-8")


def _reconcile_canonical(root: Path, engine):
    """Run canonical reconciliation with the resolved cooled set."""
    workspace = engine.parse_workspace(root / "workspace.toml")
    cooled, _ = engine._resolve_cooled_state(root)
    return engine.run_canonical_reconciliation(workspace, root, cooled)


def _brief_workspace(
    root: Path,
    *,
    child_collection: str,
    child_source_parent: str | None,
    brief_collection: str,
    include_dependant: bool = True,
) -> None:
    """Write workspace.toml for brief-child cooling tests.

    child_collection    — "shipped" | "active" | "queue" for the child spec
    child_source_parent — source.parent in the TOML entry, or None to omit
    brief_collection    — "shipped" | "executing" for the brief
    include_dependant   — include the dependant spec (with kind=brief dep) in queue
    """
    parent_clause = (
        f', parent = "{child_source_parent}"' if child_source_parent is not None else ""
    )
    child_entry = (
        f'{{path = "docs/specs/child/spec.md", kind = "spec", '
        f'source = {{mode = "repo-origin"{parent_clause}}}, '
        f'summary = "fixture", needs = []}}'
    )
    dep_entry = (
        '{path = "docs/specs/dependant/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, '
        'summary = "fixture", needs = []}'
    )
    if include_dependant:
        _depend_on(root, "dependant", BRIEF_REF)
    brief_entry = (
        f'{{path = "{BRIEF_PATH}", kind = "brief", '
        f'source = {{mode = "repo-origin"}}, summary = "fixture", needs = []}}'
    )
    work: dict[str, str] = {"queue": "", "active": "", "shipped": ""}
    work[child_collection] = child_entry
    if include_dependant:
        work["queue"] = dep_entry + ("," + child_entry if child_collection == "queue" else "")
    elif child_collection == "queue":
        work["queue"] = child_entry
    brief_shipped = brief_entry if brief_collection == "shipped" else ""
    # Use the full table form in a list so the brief becomes a WorkspaceMembership
    # (not a LegacyWorkspaceMembership) and appears in evaluate_dispatch output.
    # A bare string like "docs/product/briefs/..." is treated as a legacy_entry.
    executing_list = f"[{brief_entry}]" if brief_collection == "executing" else "[]"
    (root / "workspace.toml").write_text(
        '["ini-002"]\n'
        'name = "Cooling fixture"\n'
        'status = "active"\n'
        'milestone = "M1"\n\n'
        '["ini-002".work]\n'
        f'queue = [{work["queue"]}]\n'
        f'active = [{work["active"]}]\n'
        f'shipped = [{work["shipped"]}]\n\n'
        '["ini-002".shaping_queue]\n'
        'active = []\n'
        'backlog = []\n\n'
        '["ini-002".brief_queue]\n'
        'draft = []\n'
        'ready = []\n'
        f'executing = {executing_list}\n'
        f'shipped = [{brief_shipped}]\n',
        encoding="utf-8",
    )


def _child_spec(root: Path, *, status: str = "Implementing", brief: str = "none") -> None:
    """Write the child spec body so the cooled-locator resolver finds it on disk.

    `brief` sets the body-only parent link. It is the shape the residual turns
    on: a link the engine can read while the artifact is live and cannot read
    once it is cooled.
    """
    path = root / "docs/specs/child/spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Spec\n\n- **Status:** {status}\n- **Brief:** {brief}\n",
        encoding="utf-8",
    )


def test_cooled_attributed_child_refuses_brief_dependency(tmp_path, engine) -> None:
    """AC59 Defect 1: an attributed cooled child makes its parent brief's dep fail closed.

    Before the fix: the cooled child in work.shipped had its state fabricated as
    "Shipped" via _membership_status, so the brief_queue.shipped parent's
    invalid_child_scope predicate saw only {"Shipped"} and fired no finding.
    A downstream spec with kind="brief" dependency then saw a clean brief and
    was dispatched — a lifecycle record promoted a structurally blocked spec.

    After the fix: the cooled child is excluded from child states; the brief is
    recorded in briefs_with_cooled_children; _dependency_is_satisfied refuses the
    dep and the downstream spec stays out of canonical.ready.

    Killing mutation: remove the `dep.kind == "brief" and dep.path in
    briefs_with_cooled_children` check from _dependency_is_satisfied — the dep
    becomes satisfied (brief body is "Shipped", no structural findings on brief),
    the dependant reaches canonical.ready, and the first assertion fails.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    # The child file must exist so _cooled_locators adds it to the cooled set.
    # Its body is never read after that — the cooled branch short-circuits all
    # body-dependent predicates. source.parent in the workspace entry attributes
    # the child to the brief read-free.
    _child_spec(root, status="Shipped")
    _spec(root, "dependant", status="Approved", brief="none")
    _brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent=BRIEF_PATH,
        brief_collection="shipped",
    )

    # AC59 names a two-run observable. Without this control the brief is blocked
    # in both runs and the assertions below cannot attribute anything to cooling.
    control = _reconcile_canonical(root, engine)
    assert "docs/specs/dependant/spec.md" in {
        e.entry.path for e in control.evaluations if e.dispatchable
    }, "control never dispatched the dependant; the cooled run proves nothing"
    assert not [f for f in control.findings if f.path == BRIEF_PATH]

    _cool_child(root)
    result = _reconcile_canonical(root, engine)
    ready_paths = {e.entry.path for e in result.evaluations if e.dispatchable}
    assert "docs/specs/dependant/spec.md" not in ready_paths, (
        "dependant reached canonical.ready — cooled attributed child fabricated Shipped"
    )
    assert any(
        f.code == "unsatisfied_dependency" and f.path == BRIEF_PATH
        for f in result.findings
    ), "expected unsatisfied_dependency for the brief whose attributed child was cooled"


def test_a_cooled_child_does_not_erase_a_live_childs_violation(tmp_path, engine) -> None:
    """AC59: suppression covers only the arm a missing child can flip.

    `brief_queue.ready` and `brief_queue.shipped` assert over the states
    observed; an unknown extra child can add a state but never remove one, so a
    violation raised by a live, readable child stays a violation. Only
    `brief_queue.executing` asserts a state is PRESENT, so only it can be
    flipped by absence. Suppressing all three let cooling one child erase a
    finding that a different, fully readable child caused.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    for slug, status in (("childa", "Implementing"), ("childb", "Shipped")):
        directory = root / "docs/specs" / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "spec.md").write_text(
            f"# Spec\n\n- **Status:** {status}\n- **Brief:** none\n", encoding="utf-8"
        )
        (directory / "plan.md").write_text("# Plan\n", encoding="utf-8")
    _spec(root, "dependant", status="Approved", brief="none")

    def entry(slug: str) -> str:
        return (
            f'{{path = "docs/specs/{slug}/spec.md", kind = "spec", '
            f'source = {{mode = "repo-origin", parent = "{BRIEF_PATH}"}}, '
            f'summary = "fixture", needs = []}}'
        )

    brief_entry = (
        f'{{path = "{BRIEF_PATH}", kind = "brief", source = {{mode = "repo-origin"}}, '
        f'summary = "fixture", needs = []}}'
    )
    (root / "workspace.toml").write_text(
        '["ini-002"]\nname = "x"\nstatus = "active"\nmilestone = "M1"\n\n'
        '["ini-002".work]\n'
        f'queue = []\nactive = [{entry("childa")}]\nshipped = [{entry("childb")}]\n\n'
        '["ini-002".brief_queue]\ndraft = []\nready = []\nexecuting = []\n'
        f'shipped = [{brief_entry}]\n',
        encoding="utf-8",
    )

    def scope_findings(result):
        return [
            f for f in result.findings
            if f.code == "impossible_transition" and f.path == BRIEF_PATH
        ]

    assert scope_findings(_reconcile_canonical(root, engine)), (
        "control raised no child-scope finding; the assertion below proves nothing"
    )
    # Cool childb only. childa is live, readable, and still contributes
    # "Implementing" to a brief_queue.shipped parent, so the violation stands.
    (root / "docs/lifecycle").mkdir(parents=True, exist_ok=True)
    (root / "docs/lifecycle/childb.json").write_text(
        json.dumps(_record(delivery_id="childb", locator="docs/specs/childb/spec.md")),
        encoding="utf-8",
    )
    assert scope_findings(_reconcile_canonical(root, engine)), (
        "cooling one child erased a violation raised by a different live child"
    )


def test_a_cooled_child_contributes_no_fabricated_state(tmp_path, engine) -> None:
    """AC59: a cooled child's collection-derived state never reaches a predicate.

    `_membership_status` returns "Shipped" for anything in `work.shipped`
    whatever the body says. With the `shipped` arm now evaluated for briefs that
    have a cooled child, letting that fabricated state through would report a
    brief as compliant on the strength of the collection alone.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    # Body says Implementing; the collection says Shipped. Only the body is true.
    _child_spec(root, status="Implementing")
    _spec(root, "dependant", status="Approved", brief="none")
    _brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent=BRIEF_PATH,
        brief_collection="shipped",
    )

    assert [
        f for f in _reconcile_canonical(root, engine).findings
        if f.code == "impossible_transition" and f.path == BRIEF_PATH
    ], "control did not flag the brief; the assertion below proves nothing"

    _cool_child(root)
    assert not [
        f for f in _reconcile_canonical(root, engine).findings
        if f.code == "impossible_transition" and f.path == BRIEF_PATH
    ], "a cooled child injected its collection-derived state into the predicate"


def test_a_cooled_parentless_spec_leaves_an_unrelated_brief_alone(tmp_path, engine) -> None:
    """ADR-0110: a cooled spec leaves an unrelated brief alone once it declares `none`.

    Superseded in part by ADR-0110. AC59 held that an undeclared `source.parent`
    marked no brief, so absence carried the availability guarantee. ADR-0110
    splits absence in two: a declared **empty** value marks nothing and releases
    every dependency, while an **absent** key is unknown scope and fails closed.
    The availability half this case pins therefore survives unchanged in
    substance -- it is now conditioned on declaring `none` rather than on
    declaring nothing at all, which is what gives a maintainer a way out.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    _child_spec(root, status="Shipped")
    _spec(root, "dependant", status="Approved", brief="none")
    _brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent="none",
        brief_collection="shipped",
    )

    before = _reconcile_canonical(root, engine)
    ready_before = {e.entry.path for e in before.evaluations if e.dispatchable}
    assert "docs/specs/dependant/spec.md" in ready_before, (
        "control never dispatched the dependant; the comparison below proves nothing"
    )

    _cool_child(root)
    after = _reconcile_canonical(root, engine)
    ready_after = {e.entry.path for e in after.evaluations if e.dispatchable}
    assert "docs/specs/dependant/spec.md" in ready_after, (
        "cooling a spec that declares an empty source.parent refused an unrelated brief"
    )
    assert not [f for f in after.findings if f.path == BRIEF_PATH]
    assert not [
        f for f in after.findings if f.code == "cooled_child_scope_unknown"
    ], "a declared empty value is an answer, not unknown scope"


def test_cooled_parentless_child_scope_closure_is_pinned(tmp_path, engine) -> None:
    """ADR-0110 closes the gap this case was written to pin.

    The child still names its brief in the artifact body only, so the link is
    still not recoverable without the read RFC-0096 section 7 forbids. What
    changed is the answer to an absent `source.parent`: the entry's scope is
    unknown, so every `kind = "brief"` dependency fails closed and the run names
    the entry a maintainer can edit rather than the brief they cannot.

    The pinning worked as intended -- closing the gap had to change this test
    deliberately, which is what happened. The function name was corrected to
    match the body; frozen AC17 remains a historical record that the three
    Wave-6 cases were updated rather than deleted.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    _child_spec(root, status="Implementing", brief=BRIEF_PATH)
    _spec(root, "dependant", status="Approved", brief="none")
    _brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent=None,
        brief_collection="shipped",
    )

    before = _reconcile_canonical(root, engine)
    assert any(
        f.code == "impossible_transition" and f.path == BRIEF_PATH for f in before.findings
    ), "control did not flag the brief; the change below is not demonstrated"

    _cool_child(root)
    after = _reconcile_canonical(root, engine)
    # The observable has inverted. The brief's dependants ARE held back now,
    # and the entry is named. The erased `impossible_transition` stays erased
    # under this closure as it did under the gap, so it is still not asserted
    # here -- an absence that both states share pins nothing.
    assert "docs/specs/dependant/spec.md" not in {
        e.entry.path for e in after.evaluations if e.dispatchable
    }, "an undeclared parent on a cooled entry no longer fails closed"
    assert [
        f for f in after.findings
        if f.code == "cooled_child_scope_unknown"
        and f.path == "docs/specs/child/spec.md"
    ], "the refusal fired without naming the entry a maintainer must repair"
    assert [
        f for f in after.findings
        if f.code == "unsatisfied_dependency" and f.path == BRIEF_PATH
    ], "the brief dependency was not refused"


def test_unrelated_cooled_spec_affects_different_initiative_brief(
    tmp_path, engine
) -> None:
    """ADR-0110: the unknown-scope floor crosses initiative boundaries.

    Superseded in part by ADR-0110. There is still no initiative filter, and
    this is still an attribution test rather than a scoping one. What changed is
    the direction of the answer: a cooled spec that declares no parent at all no
    longer marks *no* brief, it makes *every* brief's scope unknown, because the
    brief it belongs to is exactly what nobody recorded. The ini-003 spec below
    is left undeclared and cooled deliberately, so what this case now pins is
    that the floor is repository-wide and not initiative-scoped.

    Killing mutation: scope the refusal to the cooled entry's own initiative --
    the ini-002 dependant dispatches and the cross-initiative floor is lost.

    The function name was corrected to match the body; frozen AC17 remains a
    historical record that the three Wave-6 cases were updated rather than
    deleted.
    """
    root = tmp_path
    _brief_body(root, status="Shipped")
    # Child of brief in ini-002 — NOT cooled, status Shipped, attributed.
    _spec(root, "child", status="Shipped", brief=BRIEF_PATH)
    _spec(root, "dependant", status="Approved", brief="none")
    # Unrelated spec in ini-003 — will be cooled, no parent link anywhere.
    _spec(root, "unrelated", status="Shipped", brief="none")

    # Cool only the ini-003 spec; the ini-002 child is NOT cooled.
    directory = root / "docs/lifecycle"
    directory.mkdir(parents=True, exist_ok=True)
    record_unrelated = _record(
        delivery_id="unrelated",
        locator="docs/specs/unrelated/spec.md",
    )
    (directory / "unrelated.json").write_text(json.dumps(record_unrelated), encoding="utf-8")

    child_entry = (
        f'{{path = "docs/specs/child/spec.md", kind = "spec", '
        f'source = {{mode = "repo-origin", parent = "{BRIEF_PATH}"}}, '
        f'summary = "fixture", needs = []}}'
    )
    _depend_on(root, "dependant", BRIEF_REF)
    dep_entry = (
        '{path = "docs/specs/dependant/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "fixture", needs = []}'
    )
    brief_entry = (
        f'{{path = "{BRIEF_PATH}", kind = "brief", '
        f'source = {{mode = "repo-origin"}}, summary = "fixture", needs = []}}'
    )
    unrelated_entry = (
        '{path = "docs/specs/unrelated/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "fixture", needs = []}'
    )
    (root / "workspace.toml").write_text(
        '["ini-002"]\n'
        'name = "Brief initiative"\n'
        'status = "active"\n'
        'milestone = "M1"\n\n'
        '["ini-002".work]\n'
        f'queue = [{dep_entry}]\n'
        'active = []\n'
        f'shipped = [{child_entry}]\n\n'
        '["ini-002".shaping_queue]\n'
        'active = []\n'
        'backlog = []\n\n'
        '["ini-002".brief_queue]\n'
        'draft = []\n'
        'ready = []\n'
        'executing = ""\n'
        f'shipped = [{brief_entry}]\n\n'
        '["ini-003"]\n'
        'name = "Unrelated initiative"\n'
        'status = "active"\n'
        'milestone = "M2"\n\n'
        '["ini-003".work]\n'
        'queue = []\n'
        'active = []\n'
        f'shipped = [{unrelated_entry}]\n\n'
        '["ini-003".shaping_queue]\n'
        'active = []\n'
        'backlog = []\n',
        encoding="utf-8",
    )

    result = _reconcile_canonical(root, engine)
    ready_paths = {e.entry.path for e in result.evaluations if e.dispatchable}
    assert "docs/specs/dependant/spec.md" not in ready_paths, (
        "a cooled undeclared spec in ini-003 left the ini-002 brief dispatchable; "
        "the unknown-scope floor is not crossing initiative boundaries"
    )
    assert [
        f for f in result.findings
        if f.code == "cooled_child_scope_unknown"
        and f.path == "docs/specs/unrelated/spec.md"
    ], "the ini-003 entry was not named as the one to repair"
