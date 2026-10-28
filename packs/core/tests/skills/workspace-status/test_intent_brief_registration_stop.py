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
