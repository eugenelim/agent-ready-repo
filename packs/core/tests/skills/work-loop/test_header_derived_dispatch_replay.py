"""Case replay: header-derived `dispatch.py` against the base engine's recorded outcomes.

Spec: docs/specs/header-derived-dispatch/spec.md (AC-0018).
Verification mode: TDD with frozen fixtures.

Each case is one repository. Its spec memberships are registered in
`workspace.toml` as the base engine needs them, and the unregistered cases keep
a `workspace.toml` that omits only that spec's entry. For every spec file the
suite compares the base outcome, frozen once in
`fixtures/header-derived-dispatch/expected.json`, with `dispatch.py`'s result
over the same tree: ready and active membership, and the decision for argless
start, argless resume, a named start and a named resume.

The base outcome comes from `workspace-status reconcile` at commit `95a8cc985`,
checked out as a `git worktree` so its sibling modules are that commit's. The
base decision transcribes `work-loop`'s SKILL.md lines 168-195 at that commit.
To record only the cases missing from the file (a recorded key is never rewritten), run this file with
`HEADER_DISPATCH_BASE=<worktree>` and `HEADER_DISPATCH_RECORD=1` set.

`CLASSIFICATION` names every difference by case, spec path and field, with the
expected base and header values. Any difference it does not name with those
exact values fails, and every entry must be used. An argless field is keyed by
the path `*`, because it belongs to the repository and not to one spec.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

_HERE = Path(__file__).resolve().parent
_PACK = _HERE.parents[2]
_WORKSPACE_TESTS = _PACK / "tests/skills/workspace-status"
_EXPECTED_PATH = _HERE / "fixtures/header-derived-dispatch/expected.json"
_BASE = os.environ.get("HEADER_DISPATCH_BASE")
_RECORD = os.environ.get("HEADER_DISPATCH_RECORD") == "1"
_BASE_STATUS = "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
_COUNTER = itertools.count()


def _load_by_path(path: Path, stem: str) -> ModuleType:
    """Load a test module by file path under a unique, pack-and-skill-named module."""
    name = f"core_work_loop_header_replay_{stem}_{next(_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


TD = _load_by_path(_HERE / "test_dispatch.py", "dispatch_helpers")
EQ = _load_by_path(_WORKSPACE_TESTS / "test_depends_on_headers_equivalence.py", "equivalence")
Repo, entry, render_workspace, SPEC = TD.Repo, TD.entry, TD.render_workspace, TD.SPEC

BRIEF = "docs/product/briefs/target.md"
LEGACY_TABLE = '{slug = "%s", type = "spec", source = "x", summary = "s", needs = []}'
TRACKER = ', ref = "example-service://ABC-1", revision = "r1"'
AUTHORITY = (
    "\n```toml source-authority\n"
    'contract_version = "source-authority.v1"\nmode = "tracker-origin"\n'
    'source_ref = "example-service://ABC-1"\nsource_revision = "r1"\n\n'
    '[owned_fields]\nOutcome = "local"\n```\n'
)


# --- the case set ----------------------------------------------------------------


@dataclass(frozen=True)
class RCase:
    """One replay case. `build(repo, side)` plants the tree for `base` or `header`.

    The two sides differ only where a record's `parent` field exists: the base
    cooling schema refuses it, so the base reads the entry's `source.parent`.
    """

    name: str
    build: Callable[[Any, str], None]
    extra_paths: tuple[str, ...] = ()
    named_codes: tuple[tuple[str, str], ...] = ()  # (spec path, code of the named start)


def _p(slug: str) -> str:
    return SPEC.format(slug)


def _e(slug: str, **kw: Any) -> str:
    return entry(_p(slug), **kw)


def _simple(name: str, build: Callable[[Any], None], **kw: Any) -> RCase:
    return RCase(name, lambda repo, side: build(repo), **kw)


def _symlink(repo: Any, link: str, target: str) -> None:
    path = repo.root / link
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def _dependency_case(case: Any) -> RCase:
    return RCase(
        f"dep-{case.case_id}", lambda repo, side: EQ._write_repo(repo.root, case, "header")
    )


def _cooled_child(name: str, entry_parent: str | None, record_parent: str | None) -> RCase:
    """A cooled child spec under a Shipped brief. The base declares its parent on the entry."""
    child = _p("child")
    files = {
        BRIEF: "# Brief: target\n\n- **Status:** Shipped\n- **Slug:** target\n",
        child: EQ._spec_file("child", "Shipped"),
        "docs/specs/child/plan.md": "# Plan\n\n- **Status:** Done\n",
    }
    kw = {} if entry_parent is None else {"parent": entry_parent}
    case = EQ.Case(
        case_id=name, waiting_path=EQ.WAITER, target="brief:target",
        needs=f"[{EQ._local_need('brief', BRIEF)}]",
        files={**EQ._waiter_files(), **files},
        extras=(
            ("work", "shipped", EQ._entry(child, **kw)),
            ("brief_queue", "shipped", EQ._entry(BRIEF, "brief")),
        ),
    )

    def build(repo: Any, side: str) -> None:
        EQ._write_repo(repo.root, case, "header")
        repo.cool(child, parent=record_parent if side == "header" else None, name="child")

    return RCase(name, build)


def _cases() -> list[RCase]:
    cases = [_dependency_case(c) for c in (*EQ.CASES, *EQ.COOLED_BRIEF_CASES)]

    cases += [
        _cooled_child("cooled-child-declared-parent", BRIEF, BRIEF),
        _cooled_child("cooled-child-parent-none", "none", "none"),
        _cooled_child("cooled-child-record-predates-parent", BRIEF, None),
        _cooled_child("cooled-child-none-record-predates-parent", "none", None),
    ]

    def cooled_named(repo: Any) -> None:
        repo.spec("done", "Shipped")
        repo.spec("queued")
        repo.cool(_p("done"))
        repo.cool(_p("queued"))
        repo.workspace(queue=[_e("queued")], shipped=[_e("done")])

    cases.append(_simple("cooled-named-start-and-resume", cooled_named))

    # Registry-settled dependencies.
    def defect_settled(repo: Any) -> None:
        repo.spec("waiter", depends="docs/product/captured/settled.md")
        repo.put("docs/product/captured/settled.md", "# Defect\n\n- **Status:** Open\n- **Kind:** defect\n")
        repo.workspace(
            queue=[_e("waiter")],
            backlog_closed=[entry("docs/product/captured/settled.md", "defect")],
        )

    def target_with_findings(repo: Any) -> None:
        repo.spec("waiter", depends="spec:target")
        repo.spec("target", "Shipped")
        repo.workspace(queue=[_e("waiter")], shipped=[_e("target"), _e("target")])

    def kind_differs(repo: Any) -> None:
        repo.spec("waiter", depends="intent:target")
        repo.put(
            "docs/product/intents/target.md",
            "# Intent: target\n\n- **Status:** Accepted\n- **Slug:** target\n",
        )
        repo.workspace(
            queue=[_e("waiter")],
            brief_executing=[entry("docs/product/intents/target.md", "brief")],
        )

    cases += [
        _simple("registry-settled-defect", defect_settled),
        _simple("registry-settled-target-with-findings", target_with_findings),
        _simple("registry-settled-kind-differs", kind_differs),
    ]

    # Fail-closed and provenance findings.
    def provenance_mismatch(repo: Any) -> None:
        repo.spec("pm")
        repo.workspace(queue=[entry(_p("pm"), source_extra=', parent = "docs/product/briefs/b.md"')])

    def provenance_reference(repo: Any) -> None:
        repo.spec("pr", brief="docs/specs/other/spec.md")
        repo.workspace(queue=[_e("pr", source_extra=', parent = "docs/specs/other/spec.md"')])

    def invalid_authority(repo: Any) -> None:
        path = repo.spec("isa")
        path.write_text(path.read_text() + "\n```toml source-authority\nnot = [valid\n```\n")
        repo.workspace(queue=[_e("isa", mode="tracker-origin", source_extra=TRACKER)])

    def missing_plan(repo: Any) -> None:
        repo.spec("registered", plan=None)
        repo.spec("unregistered", plan=None)
        repo.workspace(queue=[_e("registered")])

    def unreadable(repo: Any) -> None:
        repo.spec("registered").chmod(0)
        repo.spec("unregistered").chmod(0)
        repo.spec("anchor", "Shipped")
        repo.workspace(queue=[_e("registered")], shipped=[_e("anchor")])

    def unapproved(repo: Any) -> None:
        repo.spec("draft", "Draft")
        repo.workspace(queue=[_e("draft")])

    def missing_artifact(repo: Any) -> None:
        repo.workspace(queue=[_e("ghost")])

    def invalid_path(repo: Any) -> None:
        outside = repo.root.parent / "outside-spec.md"
        outside.write_text("# Spec: x\n\n- **Status:** Approved\n- **Brief:** none\n")
        repo.put("docs/specs/esc/plan.md", "# Plan\n\n- **Status:** Approved\n")
        _symlink(repo, "docs/specs/esc/spec.md", str(outside))
        repo.workspace(queue=[_e("esc")])

    def impossible(repo: Any) -> None:
        repo.spec("shipped-in-queue", "Shipped")
        repo.spec("approved-in-active", "Approved")
        repo.workspace(queue=[_e("shipped-in-queue")], active=[_e("approved-in-active")])

    def duplicate(repo: Any) -> None:
        repo.spec("dup")
        repo.workspace(queue=[_e("dup"), _e("dup")])

    def configuration_mismatch(repo: Any) -> None:
        repo.spec("a")
        locator = (
            '{surface_role = "delivery-contract", locator = {kind = "external", '
            'value = "example-tracker:delivery/42"}, kind = "spec", '
            'source = {mode = "repo-origin"}, summary = "s", needs = []}'
        )
        repo.workspace(queue=[_e("a"), locator])

    cases += [
        _simple("provenance-mismatch", provenance_mismatch),
        _simple("provenance-reference", provenance_reference),
        _simple("invalid-source-authority", invalid_authority),
        _simple("missing-plan", missing_plan),
        _simple("unreadable-artifact", unreadable),
        _simple("unapproved-spec", unapproved),
        _simple("missing-artifact", missing_artifact, extra_paths=(_p("ghost"),)),
        _simple("invalid-artifact-path", invalid_path),
        _simple("impossible-transition", impossible),
        _simple("duplicate-membership", duplicate),
        _simple("configuration-mismatch", configuration_mismatch),
    ]

    # Status and registration.
    def bare_status(repo: Any) -> None:
        repo.spec("bare", status_line="**Status:** Approved\n")
        repo.workspace(queue=[_e("bare")])

    def symlink_spec_file(repo: Any) -> None:
        repo.spec("real")
        _symlink(repo, "docs/specs/sl/spec.md", str(repo.root / _p("real")))
        repo.put("docs/specs/sl/plan.md", "# Plan\n\n- **Status:** Approved\n")
        repo.workspace(queue=[_e("real"), _e("sl")])

    def symlink_spec_dir(repo: Any) -> None:
        repo.spec("real")
        _symlink(repo, "docs/specs/alias", str(repo.root / "docs/specs/real"))
        repo.workspace(queue=[_e("real"), _e("alias")])

    def legacy_string(repo: Any) -> None:
        repo.spec("legacy-one")
        repo.workspace(queue=['"spec/legacy-one"'])

    def legacy_table(repo: Any) -> None:
        repo.spec("legacy-tbl")
        repo.workspace(backlog_open=[LEGACY_TABLE % "legacy-tbl"])

    def needs_not_array(repo: Any) -> None:
        repo.spec("bad-needs")
        repo.workspace(queue=[_e("bad-needs", needs='""')])

    def linked_entry(repo: Any) -> None:
        repo.spec("ok")
        outside = repo.root.parent / "outside-dir"
        outside.mkdir(exist_ok=True)
        _symlink(repo, "docs/specs/linked", str(outside))
        repo.workspace(queue=[_e("ok")])

    def readme_link(repo: Any) -> None:
        repo.spec("ok")
        _symlink(repo, "docs/specs/README.md", str(repo.root / _p("ok")))
        repo.workspace(queue=[_e("ok")])

    def tracker(valid: bool) -> Callable[[Any], None]:
        def build(repo: Any) -> None:
            path = repo.spec("trk")
            path.write_text(path.read_text() + AUTHORITY)
            revision = "r1" if valid else "r2"
            repo.workspace(queue=[_e(
                "trk", mode="tracker-origin",
                source_extra=f', ref = "example-service://ABC-1", revision = "{revision}"',
            )])
        return build

    def unregistered(status: str) -> Callable[[Any], None]:
        def build(repo: Any) -> None:
            repo.spec("loose", status)
            repo.spec("anchor", "Shipped")
            repo.workspace(shipped=[_e("anchor")])
        return build

    def inactive(repo: Any) -> None:
        repo.spec("paused")
        repo.workspace(queue=[_e("paused")], ini_status="paused")

    cases += [
        _simple("bare-status-line", bare_status),
        _simple("symlink-spec-file", symlink_spec_file),
        _simple("symlink-spec-dir-alias", symlink_spec_dir),
        RCase("legacy-string-alias", lambda r, s: legacy_string(r),
              named_codes=((_p("legacy-one"), "unsupported_legacy"),)),
        RCase("legacy-table-alias", lambda r, s: legacy_table(r),
              named_codes=((_p("legacy-tbl"), "unsupported_legacy"),)),
        RCase("needs-not-an-array", lambda r, s: needs_not_array(r),
              named_codes=((_p("bad-needs"), "invalid_entry"),)),
        _simple("symlink-entry-beside-ready", linked_entry),
        _simple("symlink-readme-gives-no-finding", readme_link),
        _simple("tracker-origin-valid", tracker(True)),
        _simple("tracker-origin-invalid", tracker(False)),
        _simple("unregistered-approved", unregistered("Approved")),
        _simple("unregistered-implementing", unregistered("Implementing")),
        _simple("inactive-initiative", inactive),
    ]

    # Selection and refusals.
    def several_ready(repo: Any) -> None:
        for slug in ("one", "two", "three"):
            repo.spec(slug)
        repo.workspace(queue=[_e("one"), _e("two"), _e("three")])

    def several_active(repo: Any) -> None:
        for slug in ("one", "two"):
            repo.spec(slug, "Implementing")
        repo.workspace(active=[_e("one"), _e("two")])

    def unmigrated_needs(repo: Any) -> None:
        repo.spec("ok")
        repo.spec("waiting")
        need = '[{type = "local", kind = "spec", path = "docs/specs/ok/spec.md"}]'
        repo.workspace(queue=[_e("ok"), _e("waiting", needs=need)])

    def unmigrated_captured(repo: Any) -> None:
        repo.spec("ok")
        repo.put("docs/product/captured/cap.md", "# Captured\n\n- **Kind:** defect\n")
        repo.workspace(
            queue=[_e("ok")],
            backlog_open=[entry("docs/product/captured/cap.md", "defect")],
        )

    def tracker_inactive(repo: Any) -> None:
        repo.spec("ok")
        repo.spec("trk-paused")
        repo.workspace(
            queue=[_e("ok")],
            extra='["ini-002"]\nname = "Other"\nstatus = "paused"\n["ini-002".work]\nqueue = ['
            + _e("trk-paused", mode="tracker-origin", source_extra=TRACKER) + "]\n",
        )

    def dependent_finding(repo: Any) -> None:
        repo.spec("waited", "Implementing")
        repo.spec("dependent", "Draft", depends="spec:waited")
        repo.workspace(active=[_e("waited")], queue=[_e("dependent")])

    def dotted_slug(repo: Any) -> None:
        repo.spec("dotted-1.0", "Shipped", plan="Done")
        repo.workspace(shipped=[_e("dotted-1.0")])

    cases += [
        _simple("dependent-finding-names-spec", dependent_finding),
        _simple("dotted-slug-selector", dotted_slug),
        _simple("several-ready", several_ready),
        _simple("several-active", several_active),
        _simple("unmigrated-needs-beside-ready", unmigrated_needs),
        _simple("unmigrated-captured-item-beside-ready", unmigrated_captured),
        _simple("tracker-origin-under-inactive-initiative", tracker_inactive),
    ]
    return cases


CASES = _cases()
SKIP_AS_ROOT = {"unreadable-artifact"}


def _spec_paths(case: RCase, root: Path) -> list[str]:
    """Every `docs/specs/<name>/spec.md` that exists under the tree, and the case's extras."""
    found = set(case.extra_paths)
    specs = root / "docs/specs"
    if specs.is_dir():
        for child in sorted(specs.iterdir()):
            if os.path.lexists(child / "spec.md"):
                found.add(f"docs/specs/{child.name}/spec.md")
    return sorted(found)


def _plant(case: RCase, root: Path, side: str) -> Any:
    repo = Repo(root)
    case.build(repo, side)
    return repo


# --- the base decision (SKILL.md lines 168-195 at 95a8cc985) ---------------------


def _matches(canonical: dict[str, Any], target: str) -> list[dict[str, Any]]:
    """The `canonical.blocked` and `canonical.findings` entries that name `target`."""
    slug = target.split("/")[2]
    spellings = {target, f"spec/{slug}", slug}
    return [
        item for item in (*canonical["blocked"], *canonical["findings"])
        if item["path"] in spellings
    ]


def _codes(items: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for item in items:
        found += [f["code"] for f in item["findings"]] if "findings" in item else [item["code"]]
    return sorted(set(found))


def _decision(action: str, path: str | None = None, candidates: list[str] | None = None) -> dict[str, Any]:
    return {"action": action, "path": path, "candidates": sorted(candidates or [])}


def base_named(canonical: dict[str, Any], mode: str, target: str) -> tuple[dict[str, Any], list[str]]:
    """A supplied spec path continues only with a matching evaluation and no matching block."""
    pool = canonical["ready"] if mode == "start" else canonical["active"]
    matching = _matches(canonical, target)
    if any(item["path"] == target for item in pool) and not matching:
        return _decision(mode, target), []
    evaluated = any(item["path"] == target for item in canonical["evaluations"])
    codes = _codes(matching)
    if not evaluated and not codes:
        codes = ["unregistered_work"]
    return _decision("refuse"), codes


def base_argless(canonical: dict[str, Any]) -> dict[str, Any]:
    """One active resumes, several ask, none falls to the first ready, else none."""
    active = [item["path"] for item in canonical["active"]]
    if len(active) == 1:
        return _decision("resume", active[0])
    if active:
        return _decision("ask", candidates=active)
    if canonical["ready"]:
        first = canonical["ready"][0]["path"]
        if _matches(canonical, first):
            return _decision("refuse")
        return _decision("start", first)
    return _decision("none")


def _base_record(case: RCase, root: Path, base: Path) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, str(base / _BASE_STATUS), "reconcile", "--root", str(root)],
        check=False, capture_output=True, text=True,
    )
    canonical = json.loads(done.stdout)["canonical"]
    assert done.returncode == 0 and "evaluations" in canonical, (case.name, done.stdout[:400])
    specs: dict[str, Any] = {}
    named_codes: dict[str, Any] = {}
    for path in _spec_paths(case, root):
        start, start_codes = base_named(canonical, "start", path)
        resume, resume_codes = base_named(canonical, "resume", path)
        specs[path] = {
            "ready": any(i["path"] == path for i in canonical["ready"]),
            "active": any(i["path"] == path for i in canonical["active"]),
            "start": start, "resume": resume,
        }
        named_codes[path] = {"start": start_codes, "resume": resume_codes}
    argless = base_argless(canonical)
    return {
        "specs": specs, "argless_start": argless, "argless_resume": argless,
        "named_codes": named_codes,
    }


# --- the header side -------------------------------------------------------------


@pytest.fixture(scope="module")
def D(tmp_path_factory: pytest.TempPathFactory) -> ModuleType:
    skills = TD._copy_skills(tmp_path_factory.mktemp("planted"))
    return TD._load(skills / "work-loop" / "scripts" / "dispatch.py")


def _slim(decision: dict[str, Any]) -> dict[str, Any]:
    return _decision(decision["action"], decision["path"], decision["candidates"])


def _header_named(D: ModuleType, root: Path, mode: str, path: str) -> dict[str, Any]:
    """A named decision; an invalid selector is the action `invalid_selector`, as in the replay tool."""
    try:
        return D.dispatch(root, mode, path)["decision"]
    except D._InvalidSelector:
        return {**_decision("invalid_selector"), "findings": []}


def _header_observe(D: ModuleType, case: RCase, root: Path) -> dict[str, Any]:
    result = D.dispatch(root)
    ready = {i["path"] for i in result["ready"]}
    active = {i["path"] for i in result["active"]}
    specs: dict[str, Any] = {}
    named_codes: dict[str, Any] = {}
    for path in _spec_paths(case, root):
        named = {mode: _header_named(D, root, mode, path) for mode in ("start", "resume")}
        specs[path] = {
            "ready": path in ready, "active": path in active,
            "start": _slim(named["start"]), "resume": _slim(named["resume"]),
        }
        named_codes[path] = {
            mode: sorted({f["code"] for f in named[mode]["findings"]}) for mode in named
        }
    argless = _slim(result["decision"])
    return {
        "specs": specs, "argless_start": argless, "argless_resume": argless,
        "named_codes": named_codes,
    }


def _flatten(case_name: str, observed: dict[str, Any]) -> dict[tuple[str, str, str], Any]:
    flat: dict[tuple[str, str, str], Any] = {}
    for path, fields in observed["specs"].items():
        for field, value in fields.items():
            flat[(case_name, path, field)] = value
    for field in ("argless_start", "argless_resume"):
        flat[(case_name, "*", field)] = observed[field]
    return flat


# --- the classification table ----------------------------------------------------

REPRODUCED = "reproduced"
REMOVAL = "accepted removal"
D1 = "RFC-0106 D1"
D3 = "RFC-0106 D3"


def _errata(case: str) -> str:
    return f"RFC-0106 § Errata: {case}"


_REFUSE = _decision("refuse")
_NONE = _decision("none")


def _removal(
    case: str, path: str, field: str, base: Any, header: Any, authority: str
) -> dict[tuple[str, str, str], tuple[Any, Any, str, str | None]]:
    return {(case, path, field): (base, header, REMOVAL, authority)}


def _unregistered(
    case: str, slug: str, verb: str, field: str, authority: str
) -> dict[tuple[str, str, str], tuple[Any, Any, str, str | None]]:
    """A spec the base never saw, or refused, that the headers admit.

    The base answers `refuse` for the named shape, `none` for the argless shapes
    and `False` for membership; the header admits it and the three agree on the
    one path.
    """
    path = _p(slug)
    argless = _decision(verb, path)
    table = _removal(case, path, field, False, True, authority)
    table |= _removal(case, path, verb, _REFUSE, argless, authority)
    for shape in ("argless_start", "argless_resume"):
        table |= _removal(case, "*", shape, _NONE, argless, authority)
    return table


def _admitted(case: str, slug: str, authority: str) -> dict[tuple[str, str, str], Any]:
    return _unregistered(case, slug, "start", "ready", authority)


def _dependent_finding() -> dict[tuple[str, str, str], tuple[Any, Any, str, str | None]]:
    """The base names `waited` in the Draft `dependent`'s finding; a Draft has no membership now."""
    case, path = "dependent-finding-names-spec", _p("waited")
    return _removal(case, path, "resume", _REFUSE, _decision("resume", path), _errata(case))


def _dotted_slug() -> dict[tuple[str, str, str], tuple[Any, Any, str, str | None]]:
    """A dotted slug is no accepted selector: the headers exit 2 where the base refused."""
    case, path = "dotted-slug-selector", _p("dotted-1.0")
    refused = _decision("invalid_selector")
    table = _removal(case, path, "start", _REFUSE, refused, _errata(case))
    return table | _removal(case, path, "resume", _REFUSE, refused, _errata(case))


def _table() -> dict[tuple[str, str, str], tuple[Any, Any, str, str | None]]:
    table: dict[tuple[str, str, str], tuple[Any, Any, str, str | None]] = {}
    # RFC-0106 D1: a spec that is not registered is dispatched from its header.
    table |= _admitted("dep-spec-open", "target", D1)
    table |= _admitted("unregistered-approved", "loose", D1)
    table |= _unregistered("unregistered-implementing", "loose", "resume", "active", D1)
    # RFC-0106 D3: several ready specs are asked about, not picked in list order.
    several = [_p("one"), _p("three"), _p("two")]
    for shape in ("argless_start", "argless_resume"):
        table |= _removal(
            "several-ready", "*", shape,
            _decision("start", _p("one")), _decision("ask", candidates=several), D3,
        )
    # RFC-0106 § Errata (2026-10-29): the two cases below, approved by the owner.
    table |= _dependent_finding()
    table |= _dotted_slug()
    # Each below needs an RFC-0106 § Errata entry, written after the owner approves it.
    for case, slug in (
        ("duplicate-membership", "dup"),
        ("provenance-mismatch", "pm"),
        ("inactive-initiative", "paused"),
        ("impossible-transition", "approved-in-active"),
        ("registry-settled-target-with-findings", "waiter"),
    ):
        table |= _admitted(case, slug, _errata(case))
    for case, slug in (("symlink-spec-file", "sl"), ("symlink-spec-dir-alias", "alias")):
        path = _p(slug)
        authority = _errata(case)
        table |= _removal(case, path, "ready", True, False, authority)
        table |= _removal(case, path, "start", _decision("start", path), _REFUSE, authority)
    case = "cooled-child-none-record-predates-parent"
    waiter = _p("waiter")
    authority = _errata(case)
    table |= _removal(case, waiter, "ready", True, False, authority)
    table |= _removal(case, waiter, "start", _decision("start", waiter), _REFUSE, authority)
    for shape in ("argless_start", "argless_resume"):
        table |= _removal(case, "*", shape, _decision("start", waiter), _NONE, authority)
    return table


# (case, spec path, field) -> (base value, header value, class, authority)
CLASSIFICATION: dict[tuple[str, str, str], tuple[Any, Any, str, str | None]] = _table()


def _differences(D: ModuleType, tmp_path: Path) -> tuple[dict[Any, tuple[Any, Any]], set[str]]:
    expected = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))
    diffs: dict[Any, tuple[Any, Any]] = {}
    built: set[str] = set()
    for case in CASES:
        if IS_ROOT and case.name in SKIP_AS_ROOT:
            built.add(case.name)
            continue
        built.add(case.name)
        root = tmp_path / case.name
        _plant(case, root, "header")
        try:
            header = _flatten(case.name, _header_observe(D, case, root))
        finally:
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    path.chmod(0o644)
        base = _flatten(case.name, expected[case.name])
        assert set(base) == set(header), case.name
        for key in base:
            if base[key] != header[key]:
                diffs[key] = (base[key], header[key])
    return diffs, built


# --- tests -----------------------------------------------------------------------


def test_record_the_base_outcomes_once(tmp_path: Path) -> None:
    """The recorder: run against a worktree of 95a8cc985; it never overwrites."""
    if not (_RECORD and _BASE):
        pytest.skip("set HEADER_DISPATCH_BASE=<worktree> and HEADER_DISPATCH_RECORD=1 to record")
    recorded: dict[str, Any] = (
        json.loads(_EXPECTED_PATH.read_text(encoding="utf-8")) if _EXPECTED_PATH.exists() else {}
    )
    for case in CASES:
        if case.name in recorded:
            continue  # frozen: a recorded key is never overwritten
        root = tmp_path / case.name
        _plant(case, root, "base")
        try:
            recorded[case.name] = _base_record(case, root, Path(_BASE))
        finally:
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    path.chmod(0o644)
    assert recorded, "nothing recorded"
    _EXPECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    _EXPECTED_PATH.write_text(json.dumps(recorded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pytest.skip("recorded expected.json from the base engine")


def test_built_cases_equal_the_recorded_cases() -> None:
    expected = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))
    names = [case.name for case in CASES]
    assert len(names) == len(set(names))
    assert set(names) == set(expected)


def test_every_difference_is_classified_exactly(D: ModuleType, tmp_path: Path) -> None:
    """AC-0018: no unnamed difference, no wrong value, no unused table entry."""
    if _RECORD:
        pytest.skip("recording")
    diffs, _ = _differences(D, tmp_path)
    if os.environ.get("HEADER_DISPATCH_DUMP"):
        print(json.dumps([[*k, v[0], v[1]] for k, v in sorted(diffs.items())], indent=1))
    skipped = {k for k in CLASSIFICATION if IS_ROOT and k[0] in SKIP_AS_ROOT}
    unnamed = {k: v for k, v in diffs.items() if k not in CLASSIFICATION}
    assert not unnamed, f"unnamed differences: {unnamed}"
    for key, (base, header, kind, authority) in CLASSIFICATION.items():
        if key in skipped:
            continue
        assert kind in (REPRODUCED, REMOVAL), key
        if kind == REMOVAL:
            assert authority, key
            assert key in diffs, f"unused classification entry: {key}"
            assert diffs[key] == (base, header), (key, diffs[key])
        else:
            assert key not in diffs and base == header, f"reproduced entry differs: {key}"


def test_every_dependency_case_reproduces(D: ModuleType, tmp_path: Path) -> None:
    """A dependency case that differs would keep spec registration: it is never a removal.

    The one difference in a dependency case is `dep-spec-open`'s target, an
    Approved spec the base never registered. The waiting spec's own outcome, which
    is what the edge decides, reproduces in every case.
    """
    if _RECORD:
        pytest.skip("recording")
    diffs, _ = _differences(D, tmp_path)
    edge_cases = {c.name for c in CASES if c.name.startswith("dep-")}
    edge_cases |= {c.name for c in CASES if c.name.startswith("cooled-child-")}
    edge_cases -= {"cooled-child-none-record-predates-parent"}
    edge_paths = {EQ.WAITER, EQ.PEER, "docs/specs/child/spec.md"}
    differing = [k for k in diffs if k[0] in edge_cases and k[1] in edge_paths]
    assert not differing, differing
    assert {k for k in diffs if k[0] in edge_cases and k[1] == "*"} <= {
        ("dep-spec-open", "*", "argless_start"), ("dep-spec-open", "*", "argless_resume"),
    }


@pytest.mark.parametrize(
    "name", [c.name for c in CASES if c.named_codes], ids=lambda n: n
)
def test_named_start_of_a_kept_entry_carries_its_code(D: ModuleType, tmp_path: Path, name: str) -> None:
    """The legacy aliases and the non-array `needs` refuse a named start with one code."""
    case = next(c for c in CASES if c.name == name)
    root = tmp_path / name
    _plant(case, root, "header")
    header = _header_observe(D, case, root)["named_codes"]
    base = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))[name]["named_codes"]
    for path, code in case.named_codes:
        assert code in base[path]["start"], (path, base[path])
        assert code in header[path]["start"], (path, header[path])


def test_a_symbolic_link_entry_gives_one_finding_and_spares_the_sibling(
    D: ModuleType, tmp_path: Path
) -> None:
    case = next(c for c in CASES if c.name == "symlink-entry-beside-ready")
    _plant(case, tmp_path / "r", "header")
    result = D.dispatch(tmp_path / "r")
    assert [(f["code"], f["path"]) for f in result["findings"]] == [
        ("invalid_artifact_path", "docs/specs/linked/spec.md")
    ]
    assert [i["path"] for i in result["ready"]] == [_p("ok")]


def test_a_symbolic_link_readme_gives_no_finding(D: ModuleType, tmp_path: Path) -> None:
    case = next(c for c in CASES if c.name == "symlink-readme-gives-no-finding")
    _plant(case, tmp_path / "r", "header")
    assert D.dispatch(tmp_path / "r")["findings"] == []
