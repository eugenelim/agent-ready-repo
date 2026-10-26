"""Frozen outcomes of the captured-item cases, written in today's shape.

Spec: docs/specs/captured-item-files/spec.md (AC-0007, AC-0009, AC-0010, AC-0042).
Verification mode: TDD, paired fixtures.

Each case is one repository in today's shape: the captured item's registry entry
points at a note outside ``docs/product/captured/``, and a dependent spec names
the item in a ``Depends on:`` header. The outcome of the engine at commit
``ce30822a0`` (finding codes and paths, and ``dispatch_by_path``
dispatchability) is frozen in ``fixtures/captured-item-files/expected.json``.

To re-record, check that commit out as a ``git worktree`` so its sibling modules
are that commit's, then run this file with
``CAPTURED_ITEM_FILES_ENGINE=<worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py``
and ``CAPTURED_ITEM_FILES_RECORD=1`` set. Without ``CAPTURED_ITEM_FILES_RECORD``,
the tests assert that the current engine reproduces the recorded file.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
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


def _note_path(name: str) -> str:
    return f"docs/backlog/{name}.md"


def _lifecycle_case(
    case_id: str, kind: str, status: str | None, table: str, name: str,
    resolution: str | None = None,
) -> Case:
    """A captured note and its membership, with no dependent."""
    path = _note_path(name)
    collection = table.split(".", 1)[1]
    return Case(
        case_id, {path: _note(kind, status, resolution)},
        ((table.split(".", 1)[0], collection, _entry(path, kind)),),
    )


def _dependent_case(
    case_id: str, kind: str, status: str | None, table: str, name: str,
    dispatchable: bool, resolution: str | None = None, cooled: bool = False,
) -> Case:
    """A spec whose header names a captured note held in ``table``."""
    base = _lifecycle_case(case_id, kind, status, table, name, resolution)
    path = _note_path(name)
    files = dict(base.files)
    if cooled:
        files[f"docs/lifecycle/{name}.json"] = _record(name, path)
    return dataclasses.replace(
        base, files=files, depends_on=path, cooled=(path,) if cooled else (),
        waiter_dispatchable=dispatchable,
    )


def _build_cases() -> list[Case]:
    cases: list[Case] = []
    # Lifecycle cases: the note alone, in today's shape.
    cases.append(_lifecycle_case("defect-no-status-open", "defect", None, "backlog.open", "d-nostatus"))
    cases.append(_lifecycle_case("defect-closed-in-open", "defect", "Closed", "backlog.open", "d-closed-open", "fixed"))
    for status in ("Draft", "Approved"):
        low = status.lower()
        cases.append(_lifecycle_case(f"design-{low}-in-open", "design", status, "backlog.open", f"g-{low}-open"))
        cases.append(_lifecycle_case(f"design-{low}-in-shaping-backlog", "design", status, "shaping_queue.backlog", f"g-{low}-shaping"))
    cases.append(_lifecycle_case("defect-open-in-closed", "defect", "Open", "backlog.closed", "d-open-closed"))
    for resolution in ("fixed", "declined", "superseded"):
        cases.append(_lifecycle_case(
            f"defect-closed-{resolution}", "defect", "Closed", "backlog.closed",
            f"d-{resolution}", resolution,
        ))
    # AC-0009, AC-0010: dependencies on non-cooled captured items.
    for status in ("Draft", "Approved"):
        low = status.lower()
        cases.append(_dependent_case(
            f"depends-on-design-{low}", "design", status, "backlog.open", f"g-dep-{low}", False,
        ))
    for resolution in ("fixed", "declined", "superseded"):
        cases.append(_dependent_case(
            f"depends-on-defect-{resolution}", "defect", "Closed", "backlog.closed",
            f"d-dep-{resolution}", resolution == "fixed", resolution,
        ))
    # AC-0042: dependencies on cooled captured items.
    cases.append(_dependent_case(
        "depends-on-cooled-defect-closed-member", "defect", "Closed", "backlog.closed",
        "d-cooled-member", True, "fixed", cooled=True,
    ))
    cases.append(_dependent_case(
        "depends-on-cooled-defect-no-closed-member", "defect", "Open", "backlog.open",
        "d-cooled-loose", False, cooled=True,
    ))
    cases.append(_dependent_case(
        "depends-on-cooled-design", "design", "Draft", "backlog.open",
        "g-cooled", True, cooled=True,
    ))
    return cases


CASES = _build_cases()


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


@pytest.mark.skipif(_RECORD, reason="recording")
@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_old_shape_reproduces_the_frozen_outcome(tmp_path: Path, case: Case) -> None:
    """AC-0007, AC-0009, AC-0010, AC-0042: today's shape gives the recorded outcome."""
    assert _observe_case(tmp_path, case) == _expected()[case.case_id]


@pytest.mark.skipif(_RECORD, reason="recording")
def test_frozen_outcomes_match_case_meaning() -> None:
    """Each recorded waiter dispatchability is the one its case says."""
    expected = _expected()
    assert set(expected) == {case.case_id for case in CASES}
    for case in CASES:
        if case.waiter_dispatchable is not None:
            got = expected[case.case_id]["dispatchable"][WAITER]
            assert got is case.waiter_dispatchable, case.case_id
