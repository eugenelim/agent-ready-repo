"""Construction tests for an unregistered intent or brief in the engine.

Spec: docs/specs/intent-brief-registration-stop/spec.md (AC-0007 to AC-0012).
Verification mode: TDD for AC-0007 and AC-0010; AC-0008, AC-0011 and AC-0012
are regression guards that pass at commit ``ff33d0dcc``.

Each case plants one repository with the depends-on-headers shape and asserts
the outcome of the canonical reconciliation. The AC-0011 outcomes are literals
recorded once from the engine at commit ``ff33d0dcc``.
"""
from __future__ import annotations

import builtins
import importlib.util
import io
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

_TESTS = Path(__file__).parent
_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/scripts"
_ENGINE_MODULE = "workspace_status_engine_intent_brief_registration_stop"
_HELPERS_MODULE = "workspace_status_test_helpers_intent_brief_stop"


def _load(name: str, path: Path) -> ModuleType:
    """Load a module by file path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


ENGINE = _load(_ENGINE_MODULE, _SCRIPTS / "workspace_status_engine.py")
_H = _load(_HELPERS_MODULE, _TESTS / "test_depends_on_headers_equivalence.py")
Case, WAITER, observe = _H.Case, _H.WAITER, _H.observe
_entry, _record, _spec_file, _write_repo = _H._entry, _H._record, _H._spec_file, _H._write_repo

BRIEFS = "docs/product/briefs"
INTENTS = "docs/product/intents"
CHILD = "docs/specs/child/spec.md"
UNKNOWN = "cooled_child_scope_unknown"
UNSATISFIED = "unsatisfied_dependency"


def _brief(slug: str, status: str = "Ready", extra: str = "") -> str:
    return f"# Brief: {slug}\n\n- **Status:** {status}\n- **Slug:** {slug}\n{extra}"


def _intent(slug: str, status: str, extra: str = "") -> str:
    return f"# Intent: {slug}\n\n- **Status:** {status}\n- **Slug:** {slug}\n{extra}"


def _lifecycle(slug: str, locator: str) -> dict[str, str]:
    return {f"docs/lifecycle/{slug}.json": _record(slug, locator)}


def _cooled_child(parent: str | None) -> tuple[dict[str, str], tuple[Any, ...]]:
    """Files and the registry entry of a cooled child spec declaring ``parent``."""
    files = {
        CHILD: _spec_file("child", "Shipped"),
        "docs/specs/child/plan.md": "# Plan\n\n- **Status:** Done\n",
        **_lifecycle("child", CHILD),
    }
    entry = _entry(CHILD) if parent is None else _entry(CHILD, parent=parent)
    return files, (("work", "shipped", entry),)


def _plant(
    root: Path,
    files: dict[str, str],
    extras: tuple[Any, ...] = (),
    target: str = "spec:target",
    waiters: dict[str, str] | None = None,
) -> None:
    """Write a repository: the first waiter through the case, others as extras.

    ``waiters`` maps a waiting spec slug to the reference its header names.
    """
    waiters = waiters if waiters is not None else {"waiter": target}
    first_slug = next(iter(waiters))
    all_files = dict(files)
    all_extras = list(extras)
    for slug, reference in list(waiters.items())[1:]:
        path = f"docs/specs/{slug}/spec.md"
        all_files[path] = _spec_file(slug) + f"- **Depends on:** {reference}\n"
        all_files[f"docs/specs/{slug}/plan.md"] = "# Plan\n\n- **Status:** Approved\n"
        all_extras.append(("work", "queue", _entry(path)))
    if "docs/specs/target/spec.md" not in all_files and target == "spec:target":
        all_files["docs/specs/target/spec.md"] = _spec_file("target", "Shipped")
        all_files["docs/specs/target/plan.md"] = "# Plan\n\n- **Status:** Approved\n"
    case = Case(
        case_id="p",
        waiting_path=f"docs/specs/{first_slug}/spec.md",
        target=waiters[first_slug],
        needs="[]",
        files=all_files,
        extras=tuple(all_extras),
    )
    # The first waiter's own files come from the case builder's waiter shape.
    case.files.update({
        f"docs/specs/{first_slug}/spec.md": _spec_file(first_slug),
        f"docs/specs/{first_slug}/plan.md": "# Plan\n\n- **Status:** Approved\n",
    })
    _write_repo(root, case, "header")


def _findings(root: Path) -> list[list[str]]:
    return observe(root)["findings"]


def _dispatchable(root: Path, slug: str = "waiter") -> bool:
    return observe(root)["dispatchable"][f"docs/specs/{slug}/spec.md"]


# AC-0007, AC-0008: the cooled child's declared parent ---------------------

ATTRIBUTED = "attributed"
UNKNOWN_SCOPE = "unknown"
# A malformed path is refused by the entry check before scope is read: it is
# never attributed, and the entry is named by either finding.
REFUSED = "refused"
PARENT = f"{BRIEFS}/parent.md"


def _brief_dir_files() -> dict[str, str]:
    return {PARENT: _brief("parent", "Shipped")}


def _symlink(root: Path, link: str, target: str) -> None:
    (root / link).symlink_to(target)


def _swap_dir_for_link(root: Path, directory: str) -> None:
    """Move a real directory aside and put a symbolic link in its place."""
    real = root / directory
    moved = real.with_name(real.name + "-real")
    real.rename(moved)
    real.symlink_to(moved.name)


def _no_op(root: Path) -> None:
    return None


def _link_to_real(root: Path) -> None:
    _symlink(root, f"{BRIEFS}/link.md", "parent.md")


def _link_to_cooled(root: Path) -> None:
    _symlink(root, f"{BRIEFS}/link.md", "parent.md")


def _briefs_dir_link(root: Path) -> None:
    _swap_dir_for_link(root, BRIEFS)


def _product_dir_link(root: Path) -> None:
    _swap_dir_for_link(root, "docs/product")


# (id, declared value, extra brief-dir files, mutation, expected)
_SCOPE_CASES: list[tuple[str, str | None, dict[str, str], Callable[[Path], None], str]] = [
    ("file-no-entry", PARENT, {}, _no_op, ATTRIBUTED),
    ("slug-form", "brief:parent", {}, _no_op, ATTRIBUTED),
    (
        "cooled-kept",
        PARENT,
        _lifecycle("parent", PARENT),
        _no_op,
        ATTRIBUTED,
    ),
    ("neither", f"{BRIEFS}/absent.md", {}, _no_op, UNKNOWN_SCOPE),
    (
        "cooled-pruned",
        f"{BRIEFS}/pruned.md",
        _lifecycle("pruned", f"{BRIEFS}/pruned.md"),
        _no_op,
        UNKNOWN_SCOPE,
    ),
    ("case-variant", f"{BRIEFS}/Parent.md", {}, _no_op, UNKNOWN_SCOPE),
    ("symlink-to-real", f"{BRIEFS}/link.md", {}, _link_to_real, UNKNOWN_SCOPE),
    (
        "symlink-to-cooled",
        f"{BRIEFS}/link.md",
        _lifecycle("parent", PARENT),
        _link_to_cooled,
        UNKNOWN_SCOPE,
    ),
    (
        "cooled-outside-briefs",
        "docs/other/parent.md",
        {"docs/other/parent.md": _brief("parent", "Shipped"),
         **_lifecycle("other", "docs/other/parent.md")},
        _no_op,
        UNKNOWN_SCOPE,
    ),
    ("nested", f"{BRIEFS}/sub/parent.md", {f"{BRIEFS}/sub/parent.md": _brief("parent")}, _no_op, UNKNOWN_SCOPE),
    ("dot-segment", f"{BRIEFS}/./parent.md", {}, _no_op, REFUSED),
    ("dotdot-segment", f"{BRIEFS}/../briefs/parent.md", {}, _no_op, REFUSED),
    ("trailing-slash", f"{PARENT}/", {}, _no_op, REFUSED),
    ("briefs-dir-link", PARENT, {}, _briefs_dir_link, UNKNOWN_SCOPE),
    ("product-dir-link", PARENT, {}, _product_dir_link, UNKNOWN_SCOPE),
]


def _plant_scope_case(root: Path, declared: str | None, extra: dict[str, str]) -> None:
    child_files, child_extras = _cooled_child(declared)
    _plant(root, {**_brief_dir_files(), **extra, **child_files}, child_extras)


@pytest.mark.parametrize(
    ("declared", "extra", "mutate", "expected"),
    [case[1:] for case in _SCOPE_CASES],
    ids=[case[0] for case in _SCOPE_CASES],
)
def test_cooled_child_declared_parent_scope(
    tmp_path: Path,
    declared: str | None,
    extra: dict[str, str],
    mutate: Callable[[Path], None],
    expected: str,
) -> None:
    """AC-0007 and AC-0008: only a listed regular brief file attributes the child."""
    _plant_scope_case(tmp_path, declared, extra)
    mutate(tmp_path)
    findings = _findings(tmp_path)
    named = [UNKNOWN, CHILD] in findings
    if expected == REFUSED:
        assert not named
        assert ["invalid_artifact_path", declared] in findings
    else:
        assert named is (expected == UNKNOWN_SCOPE)


def test_briefs_directory_missing_keeps_scope_unknown(tmp_path: Path) -> None:
    """AC-0008: no briefs directory lists no brief file."""
    child_files, child_extras = _cooled_child(PARENT)
    _plant(tmp_path, child_files, child_extras)
    assert not (tmp_path / BRIEFS).exists()
    assert [UNKNOWN, CHILD] in _findings(tmp_path)


def test_unreadable_briefs_directory_keeps_scope_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0008: a listing that raises lists no brief file."""
    _plant_scope_case(tmp_path, PARENT, {})
    real_listdir = os.listdir

    def failing(path: Any = ".") -> list[str]:
        if str(path).rstrip("/").endswith(BRIEFS):
            raise PermissionError("denied")
        return real_listdir(path)

    monkeypatch.setattr(ENGINE.os, "listdir", failing)
    assert [UNKNOWN, CHILD] in _findings(tmp_path)


def test_lstat_failure_keeps_scope_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0008: an lstat that raises lists no brief file."""
    _plant_scope_case(tmp_path, PARENT, {})
    real_lstat = os.lstat

    def failing(path: Any, *args: Any, **kwargs: Any) -> Any:
        if str(path).endswith("briefs/parent.md"):
            raise OSError("denied")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(ENGINE.os, "lstat", failing)
    assert [UNKNOWN, CHILD] in _findings(tmp_path)


def test_registered_brief_attributes_the_child(tmp_path: Path) -> None:
    """AC-0007: a registered brief gives the same attribution as at `ff33d0dcc`."""
    child_files, child_extras = _cooled_child(PARENT)
    _plant(
        tmp_path,
        {**_brief_dir_files(), **child_files},
        (*child_extras, ("brief_queue", "shipped", _entry(PARENT, "brief"))),
    )
    assert [UNKNOWN, CHILD] not in _findings(tmp_path)


def test_empty_declaration_is_not_unknown_and_absent_key_is(tmp_path: Path) -> None:
    """The empty-value and absent-key distinction is kept."""
    _plant_scope_case(tmp_path / "empty", "none", {})
    _plant_scope_case(tmp_path / "absent", None, {})
    assert [UNKNOWN, CHILD] not in _findings(tmp_path / "empty")
    assert [UNKNOWN, CHILD] in _findings(tmp_path / "absent")


def test_no_brief_body_is_opened(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The brief file is listed and lstat-ed, never opened."""
    _plant_scope_case(tmp_path, PARENT, {})
    opened: list[str] = []

    def spy(real: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(file: Any, *args: Any, **kwargs: Any) -> Any:
            opened.append(str(file))
            return real(file, *args, **kwargs)

        return wrapper

    monkeypatch.setattr(builtins, "open", spy(builtins.open))
    monkeypatch.setattr(io, "open", spy(io.open))
    monkeypatch.setattr(os, "open", spy(os.open))
    workspace = ENGINE.parse_workspace(tmp_path / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(tmp_path)
    memberships = ENGINE._extract_canonical_memberships(workspace)[0]
    _, affected, unknown = ENGINE._brief_child_spec_states(
        memberships, workspace, tmp_path, cooled
    )
    assert affected == frozenset({PARENT})
    assert unknown == frozenset()
    assert not [path for path in opened if "docs/product/briefs" in path]


# AC-0007: waiters beside a cooled child of an unregistered brief -----------


def _two_brief_files() -> dict[str, str]:
    return {
        f"{BRIEFS}/b1.md": _brief("b1", "Ready"),
        f"{BRIEFS}/b2.md": _brief("b2", "Ready"),
        f"{BRIEFS}/kept.md": _brief("kept", "Shipped"),
        **_lifecycle("kept", f"{BRIEFS}/kept.md"),
    }


def test_cooled_child_of_unregistered_brief_scopes_only_that_brief(tmp_path: Path) -> None:
    """AC-0007: the waiter on the declared brief is refused; the others are not."""
    child_files, child_extras = _cooled_child(f"{BRIEFS}/b1.md")
    _plant(
        tmp_path,
        {**_two_brief_files(), **child_files},
        child_extras,
        waiters={"on-b1": "brief:b1", "on-b2": "brief:b2", "on-kept": "brief:kept"},
    )
    result = observe(tmp_path)
    assert [UNKNOWN, CHILD] not in result["findings"]
    assert result["findings"] == [[UNSATISFIED, f"{BRIEFS}/b1.md"]]
    assert result["dispatchable"]["docs/specs/on-b1/spec.md"] is False
    assert result["dispatchable"]["docs/specs/on-b2/spec.md"] is True
    assert result["dispatchable"]["docs/specs/on-kept/spec.md"] is True


# AC-0010: the child-state refusal on an unregistered brief -----------------


def _active_child(brief_slug: str, slug: str = "child") -> tuple[dict[str, str], tuple[Any, ...]]:
    path = f"docs/specs/{slug}/spec.md"
    files = {
        path: _spec_file(slug, "Approved").replace(
            "**Brief:** none", f"**Brief:** brief:{brief_slug}"
        ),
        f"docs/specs/{slug}/plan.md": "# Plan\n\n- **Status:** Approved\n",
    }
    return files, (("work", "active", _entry(path, parent=f"{BRIEFS}/{brief_slug}.md")),)


def _brief_waiter(
    root: Path, status: str, children: int, extra: str = ""
) -> dict[str, Any]:
    files: dict[str, str] = {f"{BRIEFS}/target.md": _brief("target", status, extra)}
    extras: tuple[Any, ...] = ()
    for index in range(children):
        child_files, child_extras = _active_child("target", f"child{index}")
        files.update(child_files)
        extras += child_extras
    _plant(root, files, extras, target="brief:target", waiters={"waiter": "brief:target"})
    return observe(root)


def _waiter_findings(result: dict[str, Any]) -> list[list[str]]:
    return [f for f in result["findings"] if f[1] == f"{BRIEFS}/target.md"]


@pytest.mark.parametrize(
    ("status", "children"),
    [("Ready", 1), ("Draft", 1), ("Executing", 0), ("Shipped", 1)],
    ids=["ready-with-implementing", "draft-with-implementing", "executing-none", "shipped-implementing"],
)
def test_child_state_break_refuses_the_unregistered_brief(
    tmp_path: Path, status: str, children: int
) -> None:
    """AC-0010: a break of the child-state rule refuses the dependency."""
    result = _brief_waiter(tmp_path, status, children)
    assert result["dispatchable"][WAITER] is False
    assert [UNSATISFIED, f"{BRIEFS}/target.md"] in result["findings"]


@pytest.mark.parametrize(
    ("status", "children"),
    [("Ready", 0), ("Executing", 1), ("Shipped", 0)],
    ids=["ready-no-child", "executing-with-implementing", "shipped-no-child"],
)
def test_unregistered_brief_that_keeps_the_rule_is_satisfied(
    tmp_path: Path, status: str, children: int
) -> None:
    """AC-0010 regression: a brief that keeps the rule settles by its `Status:`."""
    result = _brief_waiter(tmp_path, status, children)
    assert result["dispatchable"][WAITER] is True
    assert _waiter_findings(result) == []


def test_invalid_own_parent_reports_the_safety_finding_first(tmp_path: Path) -> None:
    """AC-0010: the dependency safety finding precedes the child-state check."""
    result = _brief_waiter(tmp_path, "Ready", 1, "- **Parent:** ../outside.md\n")
    assert result["dispatchable"][WAITER] is False
    assert _waiter_findings(result) == [["invalid_artifact_path", f"{BRIEFS}/target.md"]] or (
        ["invalid_artifact_path", "../outside.md"] in result["findings"]
        and [UNSATISFIED, f"{BRIEFS}/target.md"] not in result["findings"]
    )


# AC-0011: an unregistered intent -------------------------------------------

INTENT = f"{INTENTS}/target.md"
_INTENT_STATUSES = ("Draft", "Proposed", "Accepted", "Fulfilled", "Rejected")

# Recorded once from the engine at commit ff33d0dcc: the waiter's dispatchability
# and every finding, for an intent that depends back on the waiting spec.
_AC0011_LITERALS: dict[str, dict[str, Any]] = {
    "Draft": {"findings": [["unsatisfied_dependency", "docs/product/intents/target.md"]], "dispatchable": {"docs/specs/waiter/spec.md": False}},
    "Proposed": {"findings": [["unsatisfied_dependency", "docs/product/intents/target.md"]], "dispatchable": {"docs/specs/waiter/spec.md": False}},
    "Accepted": {"findings": [], "dispatchable": {"docs/specs/waiter/spec.md": True}},
    "Fulfilled": {"findings": [], "dispatchable": {"docs/specs/waiter/spec.md": True}},
    "Rejected": {"findings": [["unsatisfied_dependency", "docs/product/intents/target.md"]], "dispatchable": {"docs/specs/waiter/spec.md": False}},
}


def _intent_cycle(root: Path, status: str) -> dict[str, Any]:
    files = {INTENT: _intent("target", status, "- **Depends on:** spec:waiter\n")}
    _plant(root, files, target="intent:target", waiters={"waiter": "intent:target"})
    return observe(root)


@pytest.mark.parametrize("status", _INTENT_STATUSES)
def test_unregistered_intent_settles_as_at_ff33d0dcc(tmp_path: Path, status: str) -> None:
    """AC-0011: no `dependency_cycle`, and the settlement is the recorded one."""
    result = _intent_cycle(tmp_path, status)
    assert not [f for f in result["findings"] if f[0] == "dependency_cycle"]
    recorded = _AC0011_LITERALS[status]
    assert result["findings"] == recorded["findings"]
    assert result["dispatchable"] == recorded["dispatchable"]


# AC-0012: no finding names an unregistered target --------------------------


def test_status_names_no_unregistered_intent_or_brief(tmp_path: Path) -> None:
    """AC-0012: whatever the `Status:` and `Depends on:` of an unregistered target."""
    files: dict[str, str] = {}
    unregistered: list[str] = []
    for status in _INTENT_STATUSES:
        for slug, extra in (
            (f"missing-{status.lower()}", "- **Depends on:** intent:gone\n"),
            (f"cycle-{status.lower()}", "- **Depends on:** intent:cycle-peer\n"),
        ):
            files[f"{INTENTS}/{slug}.md"] = _intent(slug, status, extra)
            unregistered.append(f"{INTENTS}/{slug}.md")
    files[f"{INTENTS}/cycle-peer.md"] = _intent(
        "cycle-peer", "Draft", "- **Depends on:** intent:cycle-draft\n"
    )
    unregistered.append(f"{INTENTS}/cycle-peer.md")
    for status in ("Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"):
        slug = f"b-{status.lower()}"
        files[f"{BRIEFS}/{slug}.md"] = _brief(slug, status, "- **Depends on:** brief:b-gone\n")
        unregistered.append(f"{BRIEFS}/{slug}.md")
    tracker = f"{BRIEFS}/tracked.md"
    files[tracker] = _brief("tracked", "Draft", "- **Depends on:** brief:b-gone\n")
    tracker_entry = (
        f'{{path = "{tracker}", kind = "brief", source = {{mode = "tracker-origin", '
        f'ref = "example-service://ABC-1", revision = "r1"}}, summary = "fixture", needs = []}}'
    )
    _plant(tmp_path, files, (("brief_queue", "draft", tracker_entry),))
    named = {path for _, path in _findings(tmp_path)}
    assert not named & set(unregistered)


# AC-0001 to AC-0006: the `intent-brief-drop` repair step ----------------------

import copy  # noqa: E402
import json  # noqa: E402
import tomllib  # noqa: E402

_WS_MODULE = "workspace_status_intent_brief_registration_stop_repair"
_DROP = "intent-brief-drop"
_PLAN = ".workspace-repair-plan.json"
_NOTES = "docs/product/notes"
_CAPTURED = "docs/product/captured"
_PEER = "docs/specs/peer/spec.md"
_SHIPPED = "docs/specs/shipped-one/spec.md"


def _load_ws() -> ModuleType:
    spec = importlib.util.spec_from_file_location(_WS_MODULE, _SCRIPTS / "workspace_status.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_WS_MODULE] = module
    spec.loader.exec_module(module)
    return module


def _row(
    path: str, kind: str, mode: str = "repo-origin", needs: str = "[]", summary: str = "fixture"
) -> str:
    source = (
        '{mode = "repo-origin"}'
        if mode == "repo-origin"
        else '{mode = "tracker-origin", ref = "example-service://ABC-1", revision = "r1"}'
    )
    return (
        f'{{path = "{path}", kind = "{kind}", source = {source}, '
        f'summary = "{summary}", needs = {needs}}}'
    )


def _intent_file(slug: str, extra: str = "") -> str:
    return _intent(slug, "Draft", extra)


def _drop_fixture(root: Path) -> Path:
    """A registry holding every case the step must tell apart."""
    typed = f'[{{type = "local", kind = "spec", path = "{_PEER}"}}]'
    files = {
        f"{INTENTS}/open-a.md": _intent_file("open-a"),
        f"{INTENTS}/backlog-b.md": _intent_file("backlog-b"),
        f"{INTENTS}/mis.md": _intent_file("mis"),
        f"{INTENTS}/typed.md": _intent_file("typed"),
        f"{INTENTS}/cooled.md": _intent_file("cooled"),
        f"{INTENTS}/open-c.md": _intent_file("open-c"),
        f"{BRIEFS}/b-one.md": _brief("b-one", "Executing"),
        f"{BRIEFS}/b-two.md": _brief("b-two", "Executing"),
        f"{BRIEFS}/b-three.md": _brief("b-three", "Executing"),
        f"{BRIEFS}/tracked.md": _brief("tracked", "Draft"),
        f"{_NOTES}/cap.md": "# A note\n\n- **Status:** Draft\n",
        f"{_CAPTURED}/done.md": "# Done\n\n- **Status:** Open\n- **Kind:** intent\n",
        _PEER: _spec_file("peer"),
        "docs/specs/peer/plan.md": "# Plan\n\n- **Status:** Approved\n",
        _SHIPPED: _spec_file("shipped-one", "Shipped"),
        "docs/specs/shipped-one/plan.md": "# Plan\n\n- **Status:** Done\n",
        "docs/lifecycle/cooled.json": _record("cooled", f"{INTENTS}/cooled.md"),
        "AGENTS.md": "# Agents\n",
    }
    text = f"""# fixture header comment
[backlog]
open = [
  # comment before open-a
  {_row(f"{INTENTS}/open-a.md", "intent")},
  # comment before the captured entry
  {_row(f"{_NOTES}/cap.md", "intent")},
  {_row(f"{_CAPTURED}/done.md", "intent")},
  # comment before typed
  {_row(f"{INTENTS}/typed.md", "intent", needs=typed)},
  # comment before cooled
  {_row(f"{INTENTS}/cooled.md", "intent", needs=typed)},
  # comment before open-c
  {_row(f"{INTENTS}/open-c.md", "intent")},
]
closed = []

["ini-001"]
name = "One"
status = "active"
milestone = "m1"

["ini-001".work]
queue = [
  {_row(_SHIPPED, "spec")},
  {_row(f"{INTENTS}/mis.md", "intent")},
  {_row(_PEER, "spec")},
]
active = []
shipped = []

["ini-001".shaping_queue]
active = []
backlog = [
  # comment before backlog-b
  {_row(f"{INTENTS}/backlog-b.md", "intent")},
]

["ini-001".brief_queue]
draft = [{_row(f"{BRIEFS}/tracked.md", "brief", mode="tracker-origin")}]
executing = [
  {_row(f"{BRIEFS}/b-one.md", "brief")},
  # comment between the briefs
  {_row(f"{BRIEFS}/b-two.md", "brief")},
]

["ini-002"]
name = "Two"
status = "active"
milestone = "m2"

["ini-002".brief_queue]
executing = [
  {_row(f"{BRIEFS}/b-three.md", "brief")},
]
"""
    root.mkdir(parents=True, exist_ok=True)
    (root / "workspace.toml").write_text(text, encoding="utf-8")
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return root


def _cli(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = _WS.main([*args, "--root", str(root)])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1]) if out else {}


def _plan_of(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    code, data = _cli(root, capsys, "repair-plan")
    assert code == 0, data
    return data


def _drops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == _DROP]


def _rewrite_plan(root: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    data = json.loads((root / _PLAN).read_text(encoding="utf-8"))
    mutate(data)
    data["plan_id"] = _WS._recompute_plan_id(data)
    (root / _PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def _registry(root: Path) -> dict[str, Any]:
    return tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))


def _paths(registry: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and "kind" in node:
                found.append(node["path"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(registry)
    return found


_WS = _load_ws()
_REPO_ORIGIN = {
    f"{INTENTS}/open-a.md",
    f"{INTENTS}/backlog-b.md",
    f"{INTENTS}/mis.md",
    f"{INTENTS}/typed.md",
    f"{INTENTS}/cooled.md",
    f"{INTENTS}/open-c.md",
    f"{BRIEFS}/b-one.md",
    f"{BRIEFS}/b-two.md",
    f"{BRIEFS}/b-three.md",
}


@pytest.fixture
def drop_repo(tmp_path: Path) -> Path:
    pytest.importorskip("tomlkit")
    return _drop_fixture(tmp_path)


def test_plan_holds_one_drop_per_repo_origin_intent_or_brief(
    drop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0001 and AC-0002: tracker-origin and other kinds get none."""
    data = _plan_of(drop_repo, capsys)
    drops = _drops(data)
    assert {op["path"] for op in drops} == _REPO_ORIGIN
    assert len(drops) == len(_REPO_ORIGIN)
    by_path = {op["path"]: op for op in drops}
    # A captured item's entry is kept whatever its kind, moving or already moved.
    assert f"{_NOTES}/cap.md" not in by_path and f"{_CAPTURED}/done.md" not in by_path
    assert by_path[f"{INTENTS}/open-a.md"]["entry_locator"] == {
        "ini_slug": "", "collection": "backlog.open", "index": 0,
    }
    assert by_path[f"{INTENTS}/backlog-b.md"]["entry_locator"] == {
        "ini_slug": "ini-001", "collection": "shaping_queue.backlog", "index": 0,
    }
    assert by_path[f"{BRIEFS}/b-two.md"]["entry_locator"] == {
        "ini_slug": "ini-001", "collection": "brief_queue.executing", "index": 1,
    }
    assert by_path[f"{BRIEFS}/b-three.md"]["entry_locator"] == {
        "ini_slug": "ini-002", "collection": "brief_queue.executing", "index": 0,
    }
    assert by_path[f"{INTENTS}/mis.md"]["entry_locator"]["collection"] == "work.queue"
    assert by_path[f"{INTENTS}/cooled.md"]["kind"] == "intent"
    assert by_path[f"{BRIEFS}/b-one.md"]["kind"] == "brief"
    assert all(len(op["registry_fingerprint"]) == 64 for op in drops)
    assert all(
        set(op) == {"operation_type", "entry_locator", "path", "kind", "registry_fingerprint"}
        for op in drops
    )
    assert f"{BRIEFS}/tracked.md" not in by_path
    assert _SHIPPED not in by_path and _PEER not in by_path
    assert json.loads((drop_repo / _PLAN).read_text())["automatic_operations"] == (
        data["automatic_operations"]
    )


def _apply_without_drops(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    """The registry the same plan produces with its drop operations left out."""
    _rewrite_plan(
        root,
        lambda d: d.update(
            automatic_operations=[
                op for op in d["automatic_operations"] if op["operation_type"] != _DROP
            ]
        ),
    )
    code, result = _cli(root, capsys, "repair-apply", "--yes")
    assert code == 0, result
    return _registry(root)


def _prune(node: Any, doomed: set[str]) -> Any:
    if isinstance(node, dict):
        return {k: _prune(v, doomed) for k, v in node.items()}
    if isinstance(node, list):
        return [
            _prune(v, doomed)
            for v in node
            if not (isinstance(v, dict) and v.get("path") in doomed)
        ]
    return node


def test_apply_removes_drops_in_the_same_write_and_keeps_comments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0003: the registry equals the drop-less apply minus the drop entries."""
    pytest.importorskip("tomlkit")
    with_drops = _drop_fixture(tmp_path / "a")
    without = _drop_fixture(tmp_path / "b")
    _plan_of(without, capsys)
    expected_base = _apply_without_drops(without, capsys)
    _plan_of(with_drops, capsys)
    before = (with_drops / "workspace.toml").read_text(encoding="utf-8")
    code, result = _cli(with_drops, capsys, "repair-apply", "--yes")
    assert code == 0, result
    assert result["applied"] is True
    dropped = set(_REPO_ORIGIN)
    assert _registry(with_drops) == _prune(expected_base, dropped)
    after = (with_drops / "workspace.toml").read_text(encoding="utf-8")
    assert not any(path in after for path in _REPO_ORIGIN)
    assert f"{_CAPTURED}/cap.md" in after and f"{_CAPTURED}/done.md" in after
    assert "# fixture header comment" in after
    for kept in ("typed", "cooled", "open-c", "open-a", "backlog-b"):
        assert f"# comment before {kept}" in after
    assert "# comment between the briefs" in after
    assert before != after
    assert f"{BRIEFS}/tracked.md" in after
    assert [r for r in result["per_operation"] if r.get("applied") is False] == []


def test_one_plan_and_apply_leaves_none_and_the_next_plan_holds_no_drop(
    drop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0005."""
    _plan_of(drop_repo, capsys)
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    registry = _registry(drop_repo)
    remaining = set(_paths(registry))
    assert not remaining & _REPO_ORIGIN
    assert f"{BRIEFS}/tracked.md" in remaining
    assert _PEER in remaining
    assert {f"{_CAPTURED}/cap.md", f"{_CAPTURED}/done.md"} <= remaining
    assert _drops(_plan_of(drop_repo, capsys)) == []


def test_a_refused_needs_operation_keeps_the_entry_and_its_needs(
    drop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0004: a drop whose needs operation was refused keeps its entry."""
    _plan_of(drop_repo, capsys)
    waiter = drop_repo / INTENTS / "typed.md"
    waiter.write_text(waiter.read_text(encoding="utf-8") + "\nedited after planning\n")
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    refused = [r for r in result["per_operation"] if r.get("applied") is False]
    assert any(r["reason"] == "waiting_item_changed" for r in refused)
    assert any(r["reason"] == "entry_has_needs" for r in refused)
    registry = _registry(drop_repo)
    kept = [
        e for e in registry["backlog"]["open"] if e["path"] == f"{INTENTS}/typed.md"
    ]
    assert len(kept) == 1 and kept[0]["needs"]
    assert not set(_paths(registry)) & (_REPO_ORIGIN - {f"{INTENTS}/typed.md"})


def test_a_stale_locator_under_a_recomputed_plan_id_is_refused(
    drop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0004: the entry at the planned index is not the planned one."""
    _plan_of(drop_repo, capsys)

    def stale(data: dict[str, Any]) -> None:
        for op in data["automatic_operations"]:
            if op["operation_type"] == _DROP and op["path"] == f"{INTENTS}/open-a.md":
                op["entry_locator"]["index"] = 1

    _rewrite_plan(drop_repo, stale)
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    assert [r["reason"] for r in result["per_operation"] if r.get("applied") is False] == [
        "entry_locator_mismatch"
    ]
    assert f"{INTENTS}/open-a.md" in _paths(_registry(drop_repo))
    assert f"{_CAPTURED}/cap.md" in _paths(_registry(drop_repo))


@pytest.mark.parametrize(
    ("target", "locator"),
    [
        (_PEER, {"ini_slug": "ini-001", "collection": "work.queue", "index": 2}),
        (
            f"{BRIEFS}/tracked.md",
            {"ini_slug": "ini-001", "collection": "brief_queue.draft", "index": 0},
        ),
    ],
    ids=["spec-entry", "tracker-origin-entry"],
)
def test_an_edited_plan_naming_a_spec_or_tracker_entry_is_refused(
    drop_repo: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    locator: dict[str, Any],
) -> None:
    """AC-0004: only a repo-origin intent or brief canonical entry is dropped."""
    _plan_of(drop_repo, capsys)
    kind = "spec" if target == _PEER else "brief"

    def edit(data: dict[str, Any]) -> None:
        template = next(op for op in data["automatic_operations"] if op["operation_type"] == _DROP)
        forged = copy.deepcopy(template)
        forged.update(path=target, kind="brief" if kind == "spec" else kind)
        forged["entry_locator"] = locator
        data["automatic_operations"].append(forged)

    _rewrite_plan(drop_repo, edit)
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    assert target in _paths(_registry(drop_repo))
    refused = [r for r in result["per_operation"] if r.get("applied") is False]
    assert len(refused) == 1


def test_a_queue_operation_that_shifts_an_array_cannot_misdirect_a_drop(
    drop_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The mis-collected intent sits behind a spec a queue operation removes."""
    data = _plan_of(drop_repo, capsys)
    assert any(op["operation_type"] == "queue-to-shipped" for op in data["automatic_operations"])
    mis = next(op for op in _drops(data) if op["path"] == f"{INTENTS}/mis.md")
    assert mis["entry_locator"]["index"] == 1
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    registry = _registry(drop_repo)
    assert [e["path"] for e in registry["ini-001"]["work"]["queue"]] == [_PEER]
    assert [e["path"] for e in registry["ini-001"]["work"]["shipped"]] == [_SHIPPED]


def test_legacy_migration_routes_and_selections_are_unchanged(
    drop_repo: Path,
) -> None:
    """AC-0006: the repair adds a step and touches neither the routes nor the selections."""
    assert _DROP in _WS._VALID_OPERATION_TYPES
    for name in ("_plan_legacy_item", "_LEGACY_KIND_BY_TYPE", "_CAPTURED_LEGACY_COLLECTIONS"):
        assert hasattr(_WS, name)
    assert frozenset(
        {"backlog.open", "backlog.closed", "shaping_queue.backlog", "shaping_queue.active"}
    ) == _WS._CAPTURED_LEGACY_COLLECTIONS
    assert _WS._LEGACY_KIND_BY_TYPE == {
        "shape": "intent", "strategy": "intent", "research": "research", "design": "design",
    }
    assert frozenset(
        {"shape", "research", "strategy", "design", "signal"}
    ) == _WS._CAPTURED_SHAPING_TYPES
    assert frozenset({"defect", "design", "research", "intent"}) == _WS._CAPTURED_RECORD_KINDS


def test_a_legacy_entry_is_not_dropped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-0006: a legacy entry keeps its route and gets no drop operation."""
    pytest.importorskip("tomlkit")
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / "workspace.toml").write_text(
        '[backlog]\nopen = [{slug = "old-thing", type = "shape", summary = "an old shape"}]\n'
        "closed = []\n",
        encoding="utf-8",
    )
    data = _plan_of(tmp_path, capsys)
    assert _drops(data) == []
    kinds = [op["operation_type"] for op in data["automatic_operations"]]
    assert kinds == ["captured-to-file"]
    assert data["automatic_operations"][0]["entry_locator"] == {
        "collection": "backlog.open", "index": 0,
    }


@pytest.mark.parametrize(
    ("target", "after_move"),
    [(f"{_NOTES}/cap.md", f"{_CAPTURED}/cap.md"), (f"{_CAPTURED}/done.md", f"{_CAPTURED}/done.md")],
    ids=["moving-captured-intent", "migrated-captured-intent"],
)
def test_an_edited_plan_naming_a_captured_intent_entry_is_refused(
    drop_repo: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    after_move: str,
) -> None:
    """AC-0002, AC-0004: a captured item's entry is kept, by its pre-move path too."""
    workspace = _registry(drop_repo)
    index = next(i for i, e in enumerate(workspace["backlog"]["open"]) if e["path"] == target)
    fingerprint = _WS._entry_fingerprint(
        "", "backlog.open", index, workspace["backlog"]["open"][index]
    )
    _plan_of(drop_repo, capsys)

    def edit(data: dict[str, Any]) -> None:
        data["automatic_operations"].append({
            "operation_type": _DROP,
            "entry_locator": {"ini_slug": "", "collection": "backlog.open", "index": index},
            "path": target,
            "kind": "intent",
            "registry_fingerprint": fingerprint,
        })

    _rewrite_plan(drop_repo, edit)
    code, result = _cli(drop_repo, capsys, "repair-apply", "--yes")
    assert code == 0, result
    assert [r["reason"] for r in result["per_operation"] if r.get("applied") is False] == [
        "entry_not_droppable"
    ]
    assert after_move in _paths(_registry(drop_repo))
