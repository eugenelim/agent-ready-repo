"""Frozen outcomes of the captured-item cases, written in today's shape.

Spec: docs/specs/captured-item-files/spec.md (AC-0007 to AC-0013, AC-0042, AC-0045).
Verification mode: TDD, paired fixtures.

Each case is one repository in today's shape: the captured item's registry entry
points at a note outside ``docs/product/captured/``, and a dependent spec names
the item in a ``Depends on:`` header. The outcome of the engine at commit
``ce30822a0`` (finding codes and paths, and ``dispatch_by_path``
dispatchability) is frozen in ``fixtures/captured-item-files/expected.json``.

Since the switch, today's shape is refused with ``unmigrated_captured_item``, so the
frozen file is the reference the migrated form and the cooled cases are compared
with. The recorder still has to be run against the ``ce30822a0`` engine.

To re-record, check that commit out as a ``git worktree`` so its sibling modules
are that commit's, then run this file with
``CAPTURED_ITEM_FILES_ENGINE=<worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py``
and ``CAPTURED_ITEM_FILES_RECORD=1`` set. Without ``CAPTURED_ITEM_FILES_RECORD``,
the tests assert that the current engine reproduces the recorded file.
"""
from __future__ import annotations

import builtins
import dataclasses
import importlib.util
import json
import os
import pathlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK_ROOT / ".apm/skills/workspace-status/scripts"
_ENGINE_PATH = Path(
    os.environ.get("CAPTURED_ITEM_FILES_ENGINE", _SCRIPTS / "workspace_status_engine.py")
)
_EXPECTED_PATH = Path(__file__).parent / "fixtures/captured-item-files/expected.json"
_RECORD = os.environ.get("CAPTURED_ITEM_FILES_RECORD") == "1"
_MODULE_NAME = "workspace_status_engine_captured_item_files_equivalence"

WAITER = "docs/specs/waiter/spec.md"


def _load_engine() -> ModuleType:
    """Load the engine by file path under a unique module name."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {_ENGINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(_MODULE_NAME, None)
    return module


ENGINE = _load_engine()


@dataclasses.dataclass(frozen=True)
class Case:
    """One case: the files, the registry entries beyond the waiter, and the edge.

    ``extras`` are ``(table, list, rendered_entry)``. ``depends_on`` is the
    captured-item path the waiting spec's header names, or ``None`` when the
    case has no waiter. ``cooled`` lists note paths that get a lifecycle record.
    ``waiter_dispatchable`` is the meaning of the case, independent of the record.
    """

    case_id: str
    files: dict[str, str]
    extras: tuple[tuple[str, str, str], ...]
    depends_on: str | None = None
    cooled: tuple[str, ...] = ()
    waiter_dispatchable: bool | None = None


def _entry(path: str, kind: str) -> str:
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "repo-origin"}}, '
        f'summary = "fixture", needs = []}}'
    )


def _note(kind: str, status: str | None, resolution: str | None = None) -> str:
    lines = [f"# {kind.title()} note", ""]
    if status is not None:
        lines.append(f"- **Status:** {status}")
    if resolution is not None:
        lines.append(f"- **Resolution:** {resolution}")
    lines.append(f"- **Kind:** {kind}")
    return "\n".join(lines) + "\n"


def _record(delivery_id: str, locator: str) -> str:
    """A schema-valid Cooling lifecycle record, as JSON text."""
    return json.dumps(
        {
            "schema": "delivery-lifecycle-record.v1",
            "delivery_id": delivery_id,
            "locator": locator,
            "aliases": [],
            "fingerprint": "sha256:" + "0" * 64,
            "disposition": "cool-30-days",
            "post_closeout_result": "Cooling",
            "completion_event": "merge",
            "completion_evidence_ref": "commit:" + "1" * 40,
            "completed_on": "2026-01-01",
            "timezone": "Asia/Singapore",
            "review_on": "2026-01-31",
            "authority": {n: {"status": "confirmed"} for n in ("source", "write", "delete")},
            "confirmation_proof": "sha256:" + "2" * 64,
        }
    )


OLD_DIR = "docs/backlog"
NEW_DIR = "docs/product/captured"


def _note_path(name: str, migrated: bool = False) -> str:
    return f"{NEW_DIR if migrated else OLD_DIR}/{name}.md"


def _lifecycle_case(
    case_id: str, kind: str, status: str | None, table: str, name: str,
    resolution: str | None = None, migrated: bool = False,
) -> Case:
    """A captured note (or record, when ``migrated``) and its membership."""
    path = _note_path(name, migrated)
    collection = table.split(".", 1)[1]
    return Case(
        case_id, {path: _note(kind, status, resolution)},
        ((table.split(".", 1)[0], collection, _entry(path, kind)),),
    )


def _dependent_case(
    case_id: str, kind: str, status: str | None, table: str, name: str,
    dispatchable: bool, resolution: str | None = None, cooled: bool = False,
    migrated: bool = False,
) -> Case:
    """A spec whose header names a captured note held in ``table``."""
    base = _lifecycle_case(case_id, kind, status, table, name, resolution, migrated)
    path = _note_path(name, migrated)
    files = dict(base.files)
    if cooled:
        files[f"docs/lifecycle/{name}.json"] = _record(name, path)
    return dataclasses.replace(
        base, files=files, depends_on=path, cooled=(path,) if cooled else (),
        waiter_dispatchable=dispatchable,
    )


# T1 cases whose old shape already has a lifecycle finding. Their record cannot
# say what the old note said (`Draft` and `Approved` are not record statuses), so
# they have no migrated form: AC-0007's conflict cases below cover them.
_NO_MIGRATED_FORM = frozenset({
    "defect-closed-in-open",
    "design-approved-in-open",
    "design-approved-in-shaping-backlog",
    "defect-open-in-closed",
    "depends-on-design-approved",
})


def _build_cases(migrated: bool = False) -> list[Case]:
    """T1's cases in today's shape, or in their migrated form (a record)."""
    cases: list[Case] = []
    if migrated:
        def status_of(old: str | None, table: str) -> str | None:
            return "Closed" if table == "backlog.closed" else "Open"
    else:
        def status_of(old: str | None, table: str) -> str | None:
            return old

    def life(case_id: str, kind: str, status: str | None, table: str, name: str,
             resolution: str | None = None) -> None:
        cases.append(_lifecycle_case(
            case_id, kind, status_of(status, table), table, name, resolution, migrated,
        ))

    def dep(case_id: str, kind: str, status: str | None, table: str, name: str,
            dispatchable: bool, resolution: str | None = None,
            cooled: bool = False) -> None:
        cases.append(_dependent_case(
            case_id, kind, status_of(status, table), table, name, dispatchable,
            resolution, cooled, migrated,
        ))

    # Lifecycle cases: the note alone.
    life("defect-no-status-open", "defect", None, "backlog.open", "d-nostatus")
    life("defect-closed-in-open", "defect", "Closed", "backlog.open", "d-closed-open", "fixed")
    for status in ("Draft", "Approved"):
        low = status.lower()
        life(f"design-{low}-in-open", "design", status, "backlog.open", f"g-{low}-open")
        life(f"design-{low}-in-shaping-backlog", "design", status, "shaping_queue.backlog", f"g-{low}-shaping")
    life("defect-open-in-closed", "defect", "Open", "backlog.closed", "d-open-closed")
    for resolution in ("fixed", "declined", "superseded"):
        life(f"defect-closed-{resolution}", "defect", "Closed", "backlog.closed",
             f"d-{resolution}", resolution)
    # AC-0009, AC-0010: dependencies on non-cooled captured items.
    for status in ("Draft", "Approved"):
        low = status.lower()
        dep(f"depends-on-design-{low}", "design", status, "backlog.open", f"g-dep-{low}", False)
    for resolution in ("fixed", "declined", "superseded"):
        dep(f"depends-on-defect-{resolution}", "defect", "Closed", "backlog.closed",
            f"d-dep-{resolution}", resolution == "fixed", resolution)
    # AC-0042: dependencies on cooled captured items.
    dep("depends-on-cooled-defect-closed-member", "defect", "Closed", "backlog.closed",
        "d-cooled-member", True, "fixed", cooled=True)
    dep("depends-on-cooled-defect-no-closed-member", "defect", "Open", "backlog.open",
        "d-cooled-loose", False, cooled=True)
    dep("depends-on-cooled-design", "design", "Draft", "backlog.open",
        "g-cooled", True, cooled=True)
    if migrated:
        cases = [case for case in cases if case.case_id not in _NO_MIGRATED_FORM]
    return cases


CASES = _build_cases()
MIGRATED_CASES = _build_cases(migrated=True)


def _write_repo(root: Path, case: Case) -> None:
    """Write the case's files and a workspace.toml holding its memberships."""
    files = dict(case.files)
    tables: dict[tuple[str, str], list[str]] = {}
    if case.depends_on is not None:
        files[WAITER] = (
            "# Spec: waiter\n\n- **Status:** Approved\n- **Brief:** none\n"
            f"- **Depends on:** {case.depends_on}\n"
        )
        files["docs/specs/waiter/plan.md"] = "# Plan\n\n- **Status:** Approved\n"
        tables[("work", "queue")] = [_entry(WAITER, "spec")]
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for table, name, rendered in case.extras:
        tables.setdefault((table, name), []).append(rendered)

    def array(key: tuple[str, str]) -> str:
        return "[" + ", ".join(tables.get(key, [])) + "]"

    lines = [
        '["ini-001"]', 'name = "Captured item fixture"', 'status = "active"',
        'milestone = "m1"', "", '["ini-001".work]',
    ]
    lines += [f"{n} = {array(('work', n))}" for n in ("queue", "active", "shipped")]
    lines += ["", '["ini-001".shaping_queue]']
    lines += [f"{n} = {array(('shaping_queue', n))}" for n in ("active", "backlog")]
    lines += ["", '["ini-001".brief_queue]']
    lines += [
        f"{n} = {array(('brief_queue', n))}"
        for n in ("draft", "ready", "executing", "shipped", "withdrawn", "cancelled")
    ]
    lines += ["", "[backlog]", f"open = {array(('backlog', 'open'))}",
              f"closed = {array(('backlog', 'closed'))}", ""]
    (root / "workspace.toml").write_text("\n".join(lines), encoding="utf-8")


def observe(root: Path) -> dict[str, Any]:
    """Run the reconciliation and return finding codes, paths, and dispatchability."""
    workspace = ENGINE.parse_workspace(root / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(root)
    canonical = ENGINE.run_canonical_reconciliation(workspace, root, cooled)
    return {
        "findings": sorted([f.code, f.path] for f in canonical.findings),
        "dispatchable": {
            path: ev.dispatchable for path, ev in sorted(canonical.dispatch_by_path.items())
        },
    }


def _observe_case(tmp_path: Path, case: Case) -> dict[str, Any]:
    _write_repo(tmp_path, case)
    return observe(tmp_path)


def _expected() -> dict[str, Any]:
    return json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))


def test_case_ids_are_unique() -> None:
    ids = [case.case_id for case in CASES]
    assert len(ids) == len(set(ids))


def test_record_expectations(tmp_path: Path) -> None:
    """The recorder: run against the engine at commit ce30822a0 to write the file."""
    if not _RECORD:
        pytest.skip("set CAPTURED_ITEM_FILES_RECORD=1 to record")
    observed = {
        case.case_id: _observe_case(tmp_path / case.case_id, case) for case in CASES
    }
    _EXPECTED_PATH.write_text(
        json.dumps(observed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pytest.skip("recorded expected.json from the engine in use")


def _migrated(text: str) -> str:
    """The recorded outcome with each old path mapped to its record path."""
    return text.replace(OLD_DIR, NEW_DIR)


def _expected_for(case_id: str, *, migrated: bool) -> dict[str, Any]:
    outcome = _expected()[case_id]
    if not migrated:
        return outcome
    return json.loads(_migrated(json.dumps(outcome)))


def _captured_paths(case: Case) -> list[str]:
    return [
        path for path in case.files
        if path.startswith((OLD_DIR + "/", NEW_DIR + "/"))
    ]


def _make_unreadable(root: Path, relative: str) -> None:
    """Replace a file with a directory: present, but never readable as a file."""
    target = root / relative
    target.unlink()
    target.mkdir()


@pytest.fixture
def opens(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every path the process opens through the stdlib's open calls."""
    seen: list[str] = []
    real_builtin, real_os, real_path = builtins.open, os.open, pathlib.Path.open

    def note(target: object) -> None:
        if isinstance(target, (str, bytes, os.PathLike)):
            seen.append(os.fsdecode(target))

    def spy_builtin(file, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(file)
        return real_builtin(file, *args, **kwargs)

    def spy_os(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(path)
        return real_os(path, *args, **kwargs)

    def spy_path(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(self)
        return real_path(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy_builtin)
    monkeypatch.setattr(os, "open", spy_os)
    monkeypatch.setattr(pathlib.Path, "open", spy_path)
    return seen


def _opened(opens: list[str], relative: str) -> bool:
    return any(path.endswith("/" + relative) for path in opens)


def _expected_old_shape(case: Case, cooled: bool) -> dict[str, Any]:
    """AC-0011, AC-0013: a non-cooled old shape is refused, a cooled one is not."""
    if cooled:
        return _expected()[case.case_id]
    path = _captured_paths(case)[0]
    findings = [["unmigrated_captured_item", path]]
    dispatchable = {path: False}
    if case.depends_on is not None:
        findings.append(["unsatisfied_dependency", path])
        dispatchable[WAITER] = False
    return {"findings": sorted(findings), "dispatchable": dict(sorted(dispatchable.items()))}


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_old_shape_is_refused_unless_cooled(tmp_path: Path, case: Case) -> None:
    """AC-0011, AC-0013, AC-0045: today's shape gives `unmigrated_captured_item`.

    A cooled one gives T1's outcome with its file unreadable.
    """
    cooled = bool(case.cooled)
    _write_repo(tmp_path, case)
    if cooled:
        _make_unreadable(tmp_path, case.cooled[0])
    assert observe(tmp_path) == _expected_old_shape(case, cooled)


@pytest.mark.skipif(_RECORD, reason="recording")
def test_unmigrated_finding_names_the_repair(tmp_path: Path) -> None:
    """AC-0011: the finding's next action names `workspace-status repair-plan`."""
    case = CASES[0]
    _write_repo(tmp_path, case)
    workspace = ENGINE.parse_workspace(tmp_path / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(tmp_path)
    found = [
        f for f in ENGINE.run_canonical_reconciliation(workspace, tmp_path, cooled).findings
        if f.code == "unmigrated_captured_item"
    ]
    assert [f.path for f in found] == [_captured_paths(case)[0]]
    assert "workspace-status repair-plan" in found[0].next_action


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize(
    "case", MIGRATED_CASES, ids=[case.case_id for case in MIGRATED_CASES]
)
def test_migrated_form_gives_the_frozen_outcome(tmp_path: Path, case: Case) -> None:
    """AC-0007, AC-0009, AC-0010, AC-0042: a record gives T1's codes and dispatchability.

    A cooled record is made unreadable to show it is not opened.
    """
    _write_repo(tmp_path, case)
    if case.cooled:
        _make_unreadable(tmp_path, case.cooled[0])
    assert observe(tmp_path) == _expected_for(case.case_id, migrated=True)


def _conflict_case(case_id: str, kind: str, status: str, table: str,
                   resolution: str | None = None) -> Case:
    return _lifecycle_case(case_id, kind, status, table, "conflict", resolution, True)


CONFLICTS = [
    # (case, the T1 case with the same conflict, or None)
    (_conflict_case("closed-record-in-open", "defect", "Closed", "backlog.open", "fixed"),
     "defect-closed-in-open"),
    (_conflict_case("closed-record-in-shaping-backlog", "design", "Closed",
                    "shaping_queue.backlog"), None),
    (_conflict_case("closed-record-in-shaping-active", "design", "Closed",
                    "shaping_queue.active"), None),
    (_conflict_case("open-record-in-closed", "defect", "Open", "backlog.closed"),
     "defect-open-in-closed"),
]


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize(
    "case,frozen", CONFLICTS, ids=[case.case_id for case, _ in CONFLICTS]
)
def test_status_conflicts_give_impossible_transition(
    tmp_path: Path, case: Case, frozen: str | None
) -> None:
    """AC-0007: a `Closed` record in an open collection or an `Open` one in closed."""
    got = _observe_case(tmp_path, case)
    path = _captured_paths(case)[0]
    assert got["findings"] == [["impossible_transition", path]]
    assert got["dispatchable"] == {path: False}
    if frozen is not None:
        # The same conflict in today's shape gave the same code, not dispatchable.
        old = _expected()[frozen]
        assert [code for code, _ in old["findings"]] == ["impossible_transition"]
        assert list(old["dispatchable"].values()) == [False]


def _single_record_case(kind: str, text: str | None) -> Case:
    path = _note_path("single", True)
    files = {} if text is None else {path: text}
    return Case(
        "single", files, (("backlog", "open", _entry(path, kind)),),
    )


@pytest.mark.skipif(_RECORD, reason="recording")
def test_kind_mismatch_gives_one_finding(tmp_path: Path) -> None:
    """AC-0007: the record's `Kind:` differs from the membership's `kind`."""
    path = _note_path("single", True)
    case = _single_record_case("defect", _note("design", "Open"))
    assert _observe_case(tmp_path, case)["findings"] == [["impossible_transition", path]]


@pytest.mark.skipif(_RECORD, reason="recording")
def test_invalid_record_gives_only_its_finding(tmp_path: Path) -> None:
    """AC-0008: an invalid record gives its `invalid_captured_item` and nothing else."""
    path = _note_path("single", True)
    text = "# Broken\n\n- **Status:** Maybe\n- **Kind:** defect\n"
    case = _single_record_case("defect", text)
    assert _observe_case(tmp_path, case)["findings"] == [["invalid_captured_item", path]]


@pytest.mark.skipif(_RECORD, reason="recording")
def test_unreadable_record_gives_only_its_finding(tmp_path: Path) -> None:
    """AC-0008: an unreadable record gives its `unreadable_artifact` and nothing else."""
    path = _note_path("single", True)
    case = _single_record_case("defect", _note("defect", "Open"))
    _write_repo(tmp_path, case)
    # A symlink is a file the reader refuses to follow.
    (tmp_path / path).unlink()
    (tmp_path / path).symlink_to(tmp_path / "workspace.toml")
    assert observe(tmp_path)["findings"] == [["unreadable_artifact", path]]


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize("linked", ["outside", "dangling"])
def test_linked_or_dangling_record_gives_only_unreadable_artifact(
    tmp_path: Path, linked: str
) -> None:
    """AC-0008, AC-0041: a record linked outside the repository, or dangling, is unreadable."""
    path = _note_path("single", True)
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo(repo, _single_record_case("defect", _note("defect", "Open")))
    (repo / path).unlink()
    target = tmp_path / "elsewhere.md"
    if linked == "outside":
        target.write_text(_note("defect", "Open"), encoding="utf-8")
    (repo / path).symlink_to(target)
    assert observe(repo)["findings"] == [["unreadable_artifact", path]]


def _identity(root: Path, reads: list[bytes] | None = None) -> str:
    """The routing identity; `reads` is cleared once the reconciliation has run."""
    workspace = ENGINE.parse_workspace(root / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(root)
    canonical = ENGINE.run_canonical_reconciliation(workspace, root, cooled)
    if reads is not None:
        reads.clear()
    return ENGINE.canonical_repository_identity(workspace, canonical, root)


@pytest.fixture
def reads(monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
    """Every chunk `os.read` and `Path.read_text` return."""
    seen: list[bytes] = []
    real_read, real_text = os.read, pathlib.Path.read_text

    def spy_read(fd, length):  # type: ignore[no-untyped-def]
        chunk = real_read(fd, length)
        seen.append(chunk)
        return chunk

    def spy_text(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        text = real_text(self, *args, **kwargs)
        seen.append(text.encode("utf-8"))
        return text

    monkeypatch.setattr(os, "read", spy_read)
    monkeypatch.setattr(pathlib.Path, "read_text", spy_text)
    return seen


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize("linked", ["symlink", "hard-link-to-cooled"])
def test_identity_never_reads_a_linked_record(
    tmp_path: Path, reads: list[bytes], linked: str
) -> None:
    """AC-0041: the routing identity reads a record only through the confined reader."""
    path = _note_path("single", True)
    cooled_path = _note_path("cooled-note")
    repo = tmp_path / "repo"
    repo.mkdir()
    cooled_case = _dependent_case(
        "cooled", "defect", "Open", "backlog.open", "cooled-note", False, cooled=True
    )
    single = _single_record_case("defect", _note("defect", "Open"))
    _write_repo(repo, dataclasses.replace(
        single,
        files={**single.files, **cooled_case.files},
        extras=single.extras + cooled_case.extras,
    ))
    (repo / path).unlink()
    if linked == "symlink":
        target = tmp_path / "elsewhere.md"
        target.write_text(_note("defect", "Open"), encoding="utf-8")
        (repo / path).symlink_to(target)
    else:
        target = repo / cooled_path
        os.link(target, repo / path)

    def body(marker: str) -> None:
        target.write_text(
            _note("defect", "Open") + f"- **Detail:** {marker}\n", encoding="utf-8"
        )

    body("SECRET-ONE")
    first = _identity(repo, reads)
    assert not any(b"SECRET-ONE" in chunk for chunk in reads)
    body("SECRET-TWO")
    assert _identity(repo) == first


@pytest.mark.skipif(_RECORD, reason="recording")
def test_missing_record_is_a_missing_artifact(tmp_path: Path) -> None:
    """A registered record that does not exist keeps `missing_artifact`."""
    path = _note_path("single", True)
    case = _single_record_case("defect", None)
    assert _observe_case(tmp_path, case)["findings"] == [["missing_artifact", path]]


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize(
    "case",
    [case for case in CASES if not case.cooled],
    ids=[case.case_id for case in CASES if not case.cooled],
)
def test_unmigrated_file_is_never_opened(
    tmp_path: Path, opens: list[str], case: Case
) -> None:
    """AC-0012: no read site opens an unmigrated path, and its header gives no edge."""
    path = _captured_paths(case)[0]
    files = dict(case.files)
    # An edge planted in the unmigrated file must not be read.
    files[path] += f"- **Depends on:** {OLD_DIR}/planted-edge.md\n"
    planted = dataclasses.replace(case, files=files)
    _write_repo(tmp_path, planted)
    workspace = ENGINE.parse_workspace(tmp_path / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(tmp_path)
    opens.clear()
    canonical = ENGINE.run_canonical_reconciliation(workspace, tmp_path, cooled)
    ENGINE.canonical_repository_identity(workspace, canonical, tmp_path)
    if case.depends_on is not None:
        assert _opened(opens, WAITER)  # the spy sees reads
    assert not _opened(opens, path)
    assert path not in canonical.header_edges


@pytest.mark.skipif(_RECORD, reason="recording")
def test_dependency_on_unmigrated_path_is_unsatisfied(tmp_path: Path) -> None:
    """AC-0013: a spec naming an unmigrated path gives `unsatisfied_dependency`."""
    case = next(case for case in CASES if case.case_id == "depends-on-defect-fixed")
    _write_repo(tmp_path, case)
    workspace = ENGINE.parse_workspace(tmp_path / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(tmp_path)
    canonical = ENGINE.run_canonical_reconciliation(workspace, tmp_path, cooled)
    reasons = [
        f.detail for f in canonical.findings if f.code == "unsatisfied_dependency"
    ]
    assert reasons == ["captured item unmigrated"]
    assert canonical.dispatch_by_path[WAITER].dispatchable is False


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case.cooled],
    ids=[case.case_id for case in CASES if case.cooled],
)
def test_cooled_captured_file_is_never_opened(
    tmp_path: Path, opens: list[str], case: Case
) -> None:
    """AC-0042, AC-0045: a cooled file, migrated or not, is not opened."""
    for form in (case, MIGRATED_BY_ID[case.case_id]):
        root = tmp_path / ("new" if form is not case else "old")
        _write_repo(root, form)
        opens.clear()
        workspace = ENGINE.parse_workspace(root / "workspace.toml")
        cooled, _ = ENGINE._resolve_cooled_state(root)
        canonical = ENGINE.run_canonical_reconciliation(workspace, root, cooled)
        ENGINE.canonical_repository_identity(workspace, canonical, root)
        assert not _opened(opens, form.cooled[0])


MIGRATED_BY_ID = {case.case_id: case for case in MIGRATED_CASES}


@pytest.mark.skipif(_RECORD, reason="recording")
def test_frozen_outcomes_match_case_meaning() -> None:
    """Each recorded waiter dispatchability is the one its case says."""
    expected = _expected()
    assert set(expected) == {case.case_id for case in CASES}
    for case in CASES:
        if case.waiter_dispatchable is not None:
            got = expected[case.case_id]["dispatchable"][WAITER]
            assert got is case.waiter_dispatchable, case.case_id
