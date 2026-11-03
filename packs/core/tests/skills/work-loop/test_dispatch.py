"""Header-derived dispatch: `work-loop`'s read-only `dispatch.py`.

Spec: docs/specs/header-derived-dispatch/spec.md (AC-0001 to AC-0012).
Verification mode: TDD. Each test plants one repository under `tmp_path`, loads
`dispatch.py` from a planted `skills/` tree that holds only the five `work-loop` files
it loads as siblings, and asserts the dispatch result. Nothing above `packs/core` is read.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import itertools
import json
import os
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_PACK = Path(__file__).resolve().parents[3]
_SKILLS = _PACK / ".apm" / "skills"
_COUNTER = itertools.count()
_SIBLINGS = ("dispatch.py", "_header_readiness.py", "file_safety.py", "cooling.py", "close_work.py")

SPEC = "docs/specs/{}/spec.md"
UNMIGRATED_NEXT_ACTION = (
    "Run workspace-status repair-plan, then repair-apply, to move the remaining "
    "workspace.toml entries onto their artifacts; rewrite or remove by hand any entry "
    "the repair leaves."
)
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _copy_skills(destination: Path, *, name: str = "skills") -> Path:
    """Plant the work-loop files dispatch loads as siblings under `destination`."""
    skills = destination / name
    scripts = skills / "work-loop" / "scripts"
    scripts.mkdir(parents=True)
    for module in _SIBLINGS:
        shutil.copy2(_SKILLS / "work-loop" / "scripts" / module, scripts / module)
    return skills


def _load(dispatch_path: Path) -> ModuleType:
    """Load `dispatch.py` under a unique name that names its pack and skill."""
    name = f"core_work_loop_dispatch_test_{next(_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, dispatch_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def base_skills(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _copy_skills(tmp_path_factory.mktemp("planted"))


@pytest.fixture(scope="module")
def D(base_skills: Path) -> ModuleType:
    return _load(base_skills / "work-loop" / "scripts" / "dispatch.py")


@pytest.fixture(scope="module")
def R(base_skills: Path) -> ModuleType:
    """The header-readiness module, loaded from the planted tree under a unique name."""
    return _load(base_skills / "work-loop" / "scripts" / "_header_readiness.py")


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A private skills tree a test may break."""
    return _copy_skills(tmp_path / "private")


# --- repository planting ----------------------------------------------------------


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def put(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def spec(
        self,
        slug: str,
        status: str = "Approved",
        *,
        plan: str | None = "Approved",
        depends: str | None = None,
        brief: str = "none",
        status_line: str | None = None,
    ) -> Path:
        line = status_line if status_line is not None else f"- **Status:** {status}\n"
        text = f"# Spec: {slug}\n\n{line}- **Brief:** {brief}\n"
        if depends is not None:
            text += f"- **Depends on:** {depends}\n"
        path = self.put(SPEC.format(slug), text)
        if plan is not None:
            self.put(f"docs/specs/{slug}/plan.md", f"# Plan\n\n- **Status:** {plan}\n")
        return path

    def workspace(self, **collections: list[str]) -> None:
        self.put("workspace.toml", render_workspace(**collections))

    def cool(self, locator: str, *, parent: str | None = None, name: str | None = None) -> None:
        record: dict[str, Any] = {
            "schema": "delivery-lifecycle-record.v1",
            "delivery_id": name or "d-" + hashlib.sha256(locator.encode()).hexdigest()[:8],
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
        if parent is not None:
            record["parent"] = parent
        self.put(f"docs/lifecycle/{record['delivery_id']}.json", json.dumps(record))


def entry(
    path: str,
    kind: str = "spec",
    *,
    mode: str = "repo-origin",
    needs: str | None = "[]",
    source_extra: str = "",
) -> str:
    needs_clause = "" if needs is None else f", needs = {needs}"
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "{mode}"{source_extra}}}, '
        f'summary = "fixture"{needs_clause}}}'
    )


def render_workspace(
    *,
    queue: list[str] = (),  # type: ignore[assignment]
    active: list[str] = (),  # type: ignore[assignment]
    shipped: list[str] = (),  # type: ignore[assignment]
    brief_executing: list[str] = (),  # type: ignore[assignment]
    backlog_open: list[str] = (),  # type: ignore[assignment]
    backlog_closed: list[str] = (),  # type: ignore[assignment]
    ini: str = "ini-001",
    ini_status: str = "active",
    extra: str = "",
) -> str:
    def array(items: list[str]) -> str:
        return "[" + ", ".join(items) + "]"

    return "\n".join(
        [
            f'["{ini}"]', 'name = "Fixture"', f'status = "{ini_status}"', "",
            f'["{ini}".work]',
            f"queue = {array(queue)}", f"active = {array(active)}", f"shipped = {array(shipped)}",
            "", f'["{ini}".brief_queue]', f"executing = {array(brief_executing)}",
            "", "[backlog]", f"open = {array(backlog_open)}", f"closed = {array(backlog_closed)}",
            "", extra, "",
        ]
    )


def paths(items: list[dict[str, Any]]) -> list[str]:
    return [item["path"] for item in items]


def codes(findings: list[dict[str, Any]]) -> list[str]:
    return [finding["code"] for finding in findings]


def assert_unmigrated(D: ModuleType, root: Path) -> None:
    """AC-0003: argless, `--start` and `--resume` each print the one `unmigrated_workspace` refusal."""
    for mode, selector in ((None, None), ("start", "a"), ("resume", "a")):
        result = D.dispatch(root, mode, selector)
        assert result["ready"] == [] and result["active"] == [] and result["blocked"] == []
        assert result["decision"]["action"] == "refuse"
        assert [(f["code"], f["path"]) for f in result["findings"]] == [
            ("unmigrated_workspace", "workspace.toml")
        ]
        assert result["findings"][0]["dispatchable"] is False
        assert result["findings"][0]["next_action"] == UNMIGRATED_NEXT_ACTION
        assert result["decision"]["findings"] == result["findings"]
        assert result["decision"]["path"] is None and result["decision"]["candidates"] == []


def drop_workspace(repo: Repo) -> None:
    """Remove the planted `workspace.toml`, leaving the same specs entry-free."""
    (repo.root / "workspace.toml").unlink()


def snapshot(root: Path) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for current, directories, files in os.walk(root):
        for name in (*directories, *files):
            path = Path(current) / name
            info = path.lstat()
            data = path.read_bytes() if stat.S_ISREG(info.st_mode) else None
            state[str(path)] = (data, info.st_mtime_ns)
    return state


def encode(result: dict[str, Any]) -> bytes:
    return json.dumps(result, sort_keys=True).encode()


# --- AC-0001 to AC-0004: the dispatch result ------------------------------------


def test_result_shape_and_sorting(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("zeta")
    repo.spec("alpha")
    repo.spec("beta-active", "Implementing")
    repo.spec("noplan", plan=None)
    result = D.dispatch(repo.root)
    assert set(result) == {"schema_version", "ready", "active", "blocked", "findings", "decision"}
    assert result["schema_version"] == 1
    assert paths(result["ready"]) == [SPEC.format("alpha"), SPEC.format("zeta")]
    assert paths(result["active"]) == [SPEC.format("beta-active")]
    for item in (*result["ready"], *result["active"], *result["blocked"]):
        assert set(item) == {"path", "slug", "status", "findings"}
    assert result["ready"][0]["slug"] == "alpha"
    assert result["ready"][0]["status"] == "Approved"
    assert paths(result["blocked"]) == [SPEC.format("noplan")]
    blocked_findings = result["blocked"][0]["findings"]
    assert blocked_findings and set(blocked_findings[0]) == {
        "code", "path", "dispatchable", "next_action",
    }
    assert set(result["decision"]) == {"action", "path", "candidates", "findings"}
    for key in ("ready", "active", "blocked", "findings"):
        assert paths(result[key]) == sorted(paths(result[key]))
    text = json.dumps(result)
    assert "ini-" not in text and "fixture" not in text


def test_shipped_and_draft_specs_are_not_listed(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("done", "Shipped")
    repo.spec("idea", "Draft")
    result = D.dispatch(repo.root)
    assert result["ready"] == [] and result["active"] == [] and result["blocked"] == []
    assert result["decision"]["action"] == "none"


def test_active_with_a_finding_is_blocked_and_findings_exclude_blocked(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("busy", "Implementing", plan=None)
    result = D.dispatch(repo.root)
    assert result["active"] == []
    assert paths(result["blocked"]) == [SPEC.format("busy")]
    blocked_codes = set(codes(result["blocked"][0]["findings"]))
    assert blocked_codes and not blocked_codes & set(codes(result["findings"]))


def test_dependency_kinds(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("base", "Shipped")
    repo.spec("open-dep", "Approved")
    repo.spec("waits-on-shipped", depends="spec:base")
    repo.spec("waits-on-open", depends="spec:open-dep")
    repo.spec("waits-on-missing", depends="spec:nowhere")
    repo.put(
        "docs/product/briefs/b.md",
        "# Brief: b\n\n- **Status:** Shipped\n",
    )
    repo.spec("waits-on-brief", depends="brief:b")
    result = D.dispatch(repo.root)
    ready = paths(result["ready"])
    assert SPEC.format("waits-on-shipped") in ready
    assert SPEC.format("waits-on-open") not in ready
    assert SPEC.format("waits-on-missing") not in ready
    blocked = {item["path"]: item for item in result["blocked"]}
    assert blocked[SPEC.format("waits-on-open")]["findings"]
    assert blocked[SPEC.format("waits-on-missing")]["findings"]


def test_cooling_findings_reach_findings(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("live")
    repo.put("docs/lifecycle/broken.json", "{not json")
    result = D.dispatch(repo.root)
    assert "invalid_lifecycle_record" in codes(result["findings"])
    assert paths(result["ready"]) == [SPEC.format("live")]


def test_cooled_child_scope_unknown_reaches_findings(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.put("docs/product/briefs/parent.md", "# Brief: parent\n\n- **Status:** Executing\n")
    repo.put("docs/specs/kid/spec.md", "# Spec: kid\n\n- **Status:** Shipped\n")
    repo.cool(SPEC.format("kid"))
    repo.workspace(brief_executing=[entry("docs/product/briefs/parent.md", "brief")])
    assert_unmigrated(D, repo.root)
    drop_workspace(repo)
    result = D.dispatch(repo.root)
    assert "cooled_child_scope_unknown" in codes(result["findings"])


@pytest.mark.parametrize("parent", [None, "none", "docs/product/briefs/parent.md"])
def test_cooled_parent_forms_are_read_from_the_record(
    D: ModuleType, tmp_path: Path, parent: str | None
) -> None:
    repo = Repo(tmp_path / "r")
    repo.put("docs/product/briefs/parent.md", "# Brief: parent\n\n- **Status:** Executing\n")
    repo.put("docs/specs/kid/spec.md", "# Spec: kid\n\n- **Status:** Shipped\n")
    repo.cool(SPEC.format("kid"), parent=parent)
    repo.workspace(brief_executing=[entry("docs/product/briefs/parent.md", "brief")])
    assert_unmigrated(D, repo.root)
    drop_workspace(repo)
    result = D.dispatch(repo.root)
    unknown = "cooled_child_scope_unknown" in codes(result["findings"])
    assert unknown is (parent is None)
    for mode in ("start", "resume"):
        decision = D.dispatch(repo.root, mode, "kid")["decision"]
        assert decision["action"] == "refuse"
        assert codes(decision["findings"]) == ["impossible_transition"]


def test_no_cooled_body_is_opened(
    D: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("cooled", "Shipped")
    repo.cool(SPEC.format("cooled"))
    repo.spec("live")
    D.dispatch(repo.root, "start", "cooled")  # warm the module caches
    opened: list[str] = []
    real_io_open, real_os_open = io.open, os.open

    def spy_io(file: Any, *args: Any, **kwargs: Any) -> Any:
        opened.append(str(file))
        return real_io_open(file, *args, **kwargs)

    def spy_os(path: Any, *args: Any, **kwargs: Any) -> Any:
        opened.append(str(path))
        return real_os_open(path, *args, **kwargs)

    monkeypatch.setattr(io, "open", spy_io)
    monkeypatch.setattr("builtins.open", spy_io)
    monkeypatch.setattr(os, "open", spy_os)
    for mode, selector in ((None, None), ("start", "cooled"), ("resume", "cooled")):
        D.dispatch(repo.root, mode, selector)
    assert not [name for name in opened if "specs/cooled" in name]
    assert any("specs/live" in name for name in opened)


# --- AC-0005, AC-0006: dropped entries never reach the engine -------------------


def test_registered_entries_are_refused_and_their_absence_raises_no_registry_findings(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.spec("b", "Implementing")
    repo.workspace(
        queue=[entry(SPEC.format("a")), entry(SPEC.format("b")), entry(SPEC.format("a"))],
        active=[entry(SPEC.format("a"))],
        shipped=[entry(SPEC.format("b"))],
    )
    assert_unmigrated(D, repo.root)
    drop_workspace(repo)
    result = D.dispatch(repo.root)
    assert paths(result["ready"]) == [SPEC.format("a")]
    assert paths(result["active"]) == [SPEC.format("b")]
    forbidden = {
        "unregistered_work", "duplicate_membership", "unsupported_legacy",
        "configuration_mismatch", "impossible_transition", "provenance_mismatch",
    }
    for item in (*result["ready"], *result["active"], *result["blocked"]):
        assert not forbidden & set(codes(item["findings"]))
    assert result["findings"] == []


def test_the_refusal_is_independent_of_the_entries_and_the_headers(
    D: ModuleType, tmp_path: Path
) -> None:
    bare = Repo(tmp_path / "bare")
    one = Repo(tmp_path / "one")
    two = Repo(tmp_path / "two")
    only = Repo(tmp_path / "only")
    empty = Repo(tmp_path / "empty")
    for repo in (bare, one, two, only, empty):
        repo.spec("a")
        repo.spec("b", "Implementing")
    one.workspace(queue=[entry(SPEC.format("a"))], active=[entry(SPEC.format("b"))])
    two.workspace(
        queue=[entry(SPEC.format("b")), entry(SPEC.format("a"))],
        shipped=[entry(SPEC.format("a"))],
        ini="ini-007",
        ini_status="paused",
    )
    only.workspace(queue=[entry(SPEC.format("a"))])
    empty.workspace(ini="ini-007")
    reference = encode(D.dispatch(bare.root))
    assert encode(D.dispatch(empty.root)) == reference
    refusal = encode(D.dispatch(one.root))
    assert refusal != reference
    for repo in (one, two, only):
        assert encode(D.dispatch(repo.root)) == refusal


def _remaining_entry(kind: str) -> str:
    """A `workspace.toml` text that holds one entry, in the named collection kind."""
    item = entry(SPEC.format("a"))
    return {
        "backlog": f'[backlog]\nopen = [{item}]\nclosed = []\n',
        "initiative-work": f'["ini-001".work]\nqueue = [{item}]\n',
        "brief_queue": f'["ini-001".brief_queue]\nexecuting = [{item}]\n',
        "shaping_queue": f'["ini-001".shaping_queue]\nbacklog = [{item}]\n',
        "repo-origin-spec-with-empty-needs": f'["ini-001".work]\nqueue = [{entry(SPEC.format("a"), needs="[]")}]\n',
    }[kind]


@pytest.mark.parametrize(
    "kind",
    ["backlog", "initiative-work", "brief_queue", "shaping_queue", "repo-origin-spec-with-empty-needs"],
)
def test_one_entry_of_each_collection_kind_is_refused(
    D: ModuleType, tmp_path: Path, kind: str
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.put("workspace.toml", _remaining_entry(kind))
    assert_unmigrated(D, repo.root)


def test_an_authorization_table_alone_does_not_refuse(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.put(
        "workspace.toml",
        '[authorization.migration]\napprover_roles = ["owner"]\n'
        '[authorization.refresh]\nitems = [{id = "x"}]\n',
    )
    result = D.dispatch(repo.root)
    assert result["decision"]["action"] == "start"
    assert result["findings"] == []
    # The same array under any other key is an entry.
    repo.put("workspace.toml", '[other]\napprover_roles = ["owner"]\n')
    assert_unmigrated(D, repo.root)


def test_a_nested_non_empty_array_is_an_entry(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.put("workspace.toml", '[deep.er.table]\nx = [1]\n')
    assert_unmigrated(D, repo.root)
    repo.put("workspace.toml", '[deep.er.table]\nx = []\n')
    assert D.dispatch(repo.root)["decision"]["action"] == "start"


@pytest.mark.parametrize(
    "needs",
    [None, '""', "{}", '[{type = "local", kind = "spec", path = "docs/specs/b/spec.md"}]'],
    ids=["missing", "string", "table", "nonempty"],
)
def test_spec_entry_without_an_empty_needs_array_is_refused(
    D: ModuleType, tmp_path: Path, needs: str | None
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.spec("b")
    repo.workspace(queue=[entry(SPEC.format("a"), needs=needs)])
    assert_unmigrated(D, repo.root)


def test_registered_entries_of_each_kind_are_refused_whole(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("plain")
    repo.spec("legacy-str")
    repo.spec("legacy-tbl")
    repo.put("docs/product/captured/cap.md", "# Captured\n\n- **Kind:** defect\n")
    repo.workspace(
        queue=[
            entry(SPEC.format("plain")),
            entry(SPEC.format("trk"), mode="tracker-origin",
                  source_extra=', ref = "example-service://ABC-1", revision = "r1"'),
            '"spec/legacy-str"',
        ],
        backlog_open=[
            entry("docs/product/captured/cap.md", "defect", needs="[]"),
            '{slug = "legacy-tbl", type = "spec", source = "x", summary = "s", needs = []}',
        ],
        extra='["ini-002"]\nname = "Other"\nstatus = "paused"\n'
        '["ini-002".work]\nqueue = [' + entry(SPEC.format("inactive"), mode="tracker-origin",
        source_extra=', ref = "example-service://ABC-2", revision = "r1"') + "]\n",
    )
    repo.spec("trk")
    repo.spec("inactive")
    assert_unmigrated(D, repo.root)
    for slug in ("legacy-str", "legacy-tbl"):
        decision = D.dispatch(repo.root, "start", slug)["decision"]
        assert decision["action"] == "refuse"
        assert codes(decision["findings"]) == ["unmigrated_workspace"]


def test_a_kept_initiative_named_ini_999_does_not_collide(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.workspace(ini="ini-999")
    result = D.dispatch(repo.root)
    assert paths(result["ready"]) == [SPEC.format("a")]
    assert result["findings"] == []


# --- AC-0007: a run writes nothing ----------------------------------------------


def test_a_run_writes_nothing(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.spec("b", "Implementing")
    repo.spec("c", "Shipped")
    repo.cool(SPEC.format("c"))
    for planted in (True, False):
        if planted:
            repo.workspace(queue=[entry(SPEC.format("a"))])
        else:
            drop_workspace(repo)
        before = snapshot(repo.root)
        for mode, selector in ((None, None), ("start", "a"), ("resume", "b"), ("start", "c")):
            D.dispatch(repo.root, mode, selector)
        assert snapshot(repo.root) == before


# --- AC-0008: the decision -------------------------------------------------------


def test_decision_with_no_selector(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    assert D.dispatch(repo.root)["decision"] == {
        "action": "none", "path": None, "candidates": [], "findings": [],
    }
    repo.spec("only")
    assert D.dispatch(repo.root)["decision"] == {
        "action": "start", "path": SPEC.format("only"), "candidates": [], "findings": [],
    }
    repo.spec("other")
    decision = D.dispatch(repo.root)["decision"]
    assert decision["action"] == "ask" and decision["path"] is None
    assert decision["candidates"] == sorted([SPEC.format("only"), SPEC.format("other")])
    repo.spec("running", "Implementing")
    assert D.dispatch(repo.root)["decision"]["action"] == "resume"
    assert D.dispatch(repo.root)["decision"]["path"] == SPEC.format("running")
    repo.spec("running-two", "Implementing")
    decision = D.dispatch(repo.root)["decision"]
    assert decision["action"] == "ask"
    assert decision["candidates"] == sorted(
        [SPEC.format("running"), SPEC.format("running-two")]
    )


def test_decision_ignores_discovery_order_and_mtimes(D: ModuleType, tmp_path: Path) -> None:
    left = Repo(tmp_path / "left")
    right = Repo(tmp_path / "right")
    for repo, order in ((left, ("m", "a", "z", "b")), (right, ("b", "z", "a", "m"))):
        for index, slug in enumerate(order):
            path = repo.spec(slug)
            os.utime(path, (1_000_000 + index * 997, 1_000_000 + index * 997))
            os.utime(path.parent, (2_000_000 - index * 31, 2_000_000 - index * 31))
    assert encode(D.dispatch(left.root)) == encode(D.dispatch(right.root))


# --- AC-0009: named invocations --------------------------------------------------


def test_named_start_and_resume_succeed(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("ready")
    repo.spec("live", "Implementing")
    for selector in ("ready", "spec/ready", "docs/specs/ready", "docs/specs/ready/",
                     "docs/specs/ready/spec.md"):
        decision = D.dispatch(repo.root, "start", selector)["decision"]
        assert decision == {
            "action": "start", "path": SPEC.format("ready"), "candidates": [], "findings": [],
        }
    assert D.dispatch(repo.root, "resume", "live")["decision"]["action"] == "resume"


@pytest.mark.parametrize("selector", ["", "..", "a/b/c", "docs/specs/../x", "/abs", "-x",
                                      "a\\b", "C:x", "x" * 201, "spec/", "docs/specs"])
def test_invalid_selector_exits_2(
    D: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], selector: str
) -> None:
    repo = Repo(tmp_path / "r")
    code = D.main(["--root", str(repo.root), f"--start={selector}"])
    captured = capsys.readouterr()
    assert code == 2 and captured.out == ""
    assert "invalid_selector" in captured.err


def _refusal(D: ModuleType, repo: Repo, mode: str, selector: str) -> list[str]:
    decision = D.dispatch(repo.root, mode, selector)["decision"]
    assert decision["action"] == "refuse" and decision["path"] is None
    assert decision["candidates"] == []
    assert decision["findings"]
    for finding in decision["findings"]:
        assert finding["next_action"]
    return codes(decision["findings"])


def test_named_refusals_by_rule(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("noplan", plan=None)
    repo.spec("kept-open", "Approved")
    repo.spec("draft", "Draft")
    repo.spec("live", "Implementing")
    repo.spec("done", "Shipped")
    repo.spec("cooled", "Shipped")
    repo.cool(SPEC.format("cooled"))
    repo.put("docs/specs/nospec/readme.txt", "x")
    repo.workspace(active=[entry(SPEC.format("kept-open"))], queue=['"spec/legacy-one"'])
    repo.spec("legacy-one")
    # A workspace that still holds an entry refuses every named run with its one finding.
    assert _refusal(D, repo, "start", "noplan") == ["unmigrated_workspace"]
    assert _refusal(D, repo, "start", "legacy-one") == ["unmigrated_workspace"]
    drop_workspace(repo)
    # rule 2: blocked findings
    assert "missing_plan" in _refusal(D, repo, "start", "noplan")
    # rule 4: cooled, from the record alone
    assert _refusal(D, repo, "start", "cooled") == ["impossible_transition"]
    assert _refusal(D, repo, "resume", "cooled") == ["impossible_transition"]
    # rule 5: the entry exists but is not a spec file
    assert _refusal(D, repo, "start", "nospec") == ["invalid_artifact_path"]
    # rule 6: nothing there
    assert _refusal(D, repo, "start", "ghost") == ["missing_artifact"]
    # rule 8
    assert _refusal(D, repo, "start", "live") == ["impossible_transition"]
    assert _refusal(D, repo, "start", "done") == ["impossible_transition"]
    assert _refusal(D, repo, "resume", "done") == ["impossible_transition"]
    # rule 9
    assert _refusal(D, repo, "start", "draft") == ["unapproved_spec"]
    assert _refusal(D, repo, "resume", "draft") == ["impossible_transition"]
    assert _refusal(D, repo, "resume", "kept-open")  # Approved is not Implementing


def test_resume_of_an_approved_header_spec_is_impossible(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("fresh")
    repo.spec("live", "Implementing")
    assert _refusal(D, repo, "resume", "fresh") == ["impossible_transition"]
    assert _refusal(D, repo, "start", "live") == ["impossible_transition"]


def test_rule_7_unreadable_artifact(D: ModuleType, tmp_path: Path) -> None:
    if IS_ROOT:
        pytest.skip("permission bits do not bind root")
    repo = Repo(tmp_path / "r")
    path = repo.spec("locked")
    path.chmod(0)
    try:
        assert _refusal(D, repo, "start", "locked") == ["unreadable_artifact"]
    finally:
        path.chmod(0o644)


def test_named_refusal_under_an_unusable_workspace_is_that_runs_finding(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.put("workspace.toml", "not = [valid")
    assert _refusal(D, repo, "start", "a") == ["invalid_workspace"]


# --- AC-0010: the refusals -------------------------------------------------------


def _assert_workspace_refused(D: ModuleType, repo: Repo) -> None:
    result = D.dispatch(repo.root)
    assert result["ready"] == [] and result["active"] == [] and result["blocked"] == []
    assert result["decision"]["action"] == "refuse"
    assert codes(result["findings"]) == ["invalid_workspace"]
    assert result["findings"][0]["path"] == "workspace.toml"
    assert result["findings"][0]["next_action"]
    assert result["decision"]["findings"] == result["findings"]


def test_malformed_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.put("workspace.toml", "this is = = not toml")
    _assert_workspace_refused(D, repo)


def test_symlinked_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    (tmp_path / "real.toml").write_text(render_workspace(), encoding="utf-8")
    (repo.root / "workspace.toml").symlink_to(tmp_path / "real.toml")
    _assert_workspace_refused(D, repo)


def test_dangling_symlinked_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    (repo.root / "workspace.toml").symlink_to(tmp_path / "nowhere.toml")
    _assert_workspace_refused(D, repo)


def test_hard_linked_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.workspace()
    os.link(repo.root / "workspace.toml", tmp_path / "second-link.toml")
    _assert_workspace_refused(D, repo)


def test_directory_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    (repo.root / "workspace.toml").mkdir()
    _assert_workspace_refused(D, repo)


def test_oversized_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    (repo.root / "workspace.toml").write_bytes(b"#" * (8 * 1024 * 1024 + 1))
    _assert_workspace_refused(D, repo)
    (repo.root / "workspace.toml").write_bytes(b"#" * (8 * 1024 * 1024))
    assert D.dispatch(repo.root)["decision"]["action"] == "none"


def test_unreadable_workspace_is_refused(D: ModuleType, tmp_path: Path) -> None:
    if IS_ROOT:
        pytest.skip("permission bits do not bind root")
    repo = Repo(tmp_path / "r")
    path = repo.put("workspace.toml", render_workspace())
    path.chmod(0)
    try:
        _assert_workspace_refused(D, repo)
    finally:
        path.chmod(0o644)


def test_every_initiative_slug_used_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.put(
        "workspace.toml",
        "\n".join(f'["ini-{n:03d}"]\nname = "n"\nstatus = "active"\n' for n in range(1000)),
    )
    _assert_workspace_refused(D, repo)


def test_absent_workspace_is_not_a_refusal(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    assert D.dispatch(repo.root)["decision"]["action"] == "start"


# --- AC-0011: the spec files ------------------------------------------------------


def test_docs_and_specs_absent_is_quiet(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    result = D.dispatch(repo.root)
    assert result["findings"] == [] and result["decision"]["action"] == "none"
    (repo.root / "docs").mkdir()
    assert D.dispatch(repo.root)["findings"] == []


def _docs_specs_finding(result: dict[str, Any]) -> None:
    assert result["ready"] == [] and result["active"] == [] and result["blocked"] == []
    assert [(f["code"], f["path"]) for f in result["findings"]] == [
        ("invalid_artifact_path", "docs/specs")
    ]


def test_docs_specs_symlink_out_of_the_root(D: ModuleType, tmp_path: Path) -> None:
    outside = Repo(tmp_path / "outside")
    outside.spec("sneaky")
    repo = Repo(tmp_path / "r")
    (repo.root / "docs").mkdir()
    (repo.root / "docs" / "specs").symlink_to(outside.root / "docs" / "specs")
    _docs_specs_finding(D.dispatch(repo.root))


def test_docs_specs_dangling_link_is_not_absent(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    (repo.root / "docs").mkdir()
    (repo.root / "docs" / "specs").symlink_to(tmp_path / "nowhere")
    _docs_specs_finding(D.dispatch(repo.root))


def test_docs_symlink_is_refused(D: ModuleType, tmp_path: Path) -> None:
    outside = Repo(tmp_path / "outside")
    outside.spec("sneaky")
    repo = Repo(tmp_path / "r")
    (repo.root / "docs").symlink_to(outside.root / "docs")
    _docs_specs_finding(D.dispatch(repo.root))


def test_docs_specs_that_is_a_file_is_refused(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.put("docs/specs", "not a directory")
    _docs_specs_finding(D.dispatch(repo.root))


def test_unlistable_docs_specs_is_refused(D: ModuleType, tmp_path: Path) -> None:
    if IS_ROOT:
        pytest.skip("permission bits do not bind root")
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    specs = repo.root / "docs" / "specs"
    specs.chmod(0)
    try:
        _docs_specs_finding(D.dispatch(repo.root))
    finally:
        specs.chmod(0o755)


def test_each_bad_entry_fails_only_itself(D: ModuleType, tmp_path: Path) -> None:
    outside = Repo(tmp_path / "outside")
    outside.spec("elsewhere")
    repo = Repo(tmp_path / "r")
    repo.spec("good")
    repo.spec("original")
    (repo.root / "docs/specs/linked").symlink_to(repo.root / "docs/specs/original")
    (repo.root / "docs/specs/escape").symlink_to(outside.root / "docs/specs/elsewhere")
    (repo.root / "docs/specs/linkfile").mkdir()
    (repo.root / "docs/specs/linkfile/spec.md").symlink_to(repo.root / "docs/specs/good/spec.md")
    (repo.root / "docs/specs/fifo").mkdir()
    os.mkfifo(repo.root / "docs/specs/fifo/spec.md")
    (repo.root / "docs/specs/afile").write_text("x", encoding="utf-8")
    (repo.root / "docs/specs/README.md").symlink_to(repo.root / "docs/specs/good/spec.md")
    (repo.root / "docs/specs/.hidden").mkdir()
    result = D.dispatch(repo.root)
    assert paths(result["ready"]) == [SPEC.format("good"), SPEC.format("original")]
    assert sorted((f["code"], f["path"]) for f in result["findings"]) == sorted(
        ("invalid_artifact_path", SPEC.format(name))
        for name in ("linked", "escape", "linkfile", "fifo", "afile")
    )
    assert result["decision"]["action"] == "ask"
    assert _refusal(D, repo, "start", "linked") == ["invalid_artifact_path"]
    assert _refusal(D, repo, "start", "fifo") == ["invalid_artifact_path"]


def test_unreadable_spec_gives_one_finding_each(D: ModuleType, tmp_path: Path) -> None:
    if IS_ROOT:
        pytest.skip("permission bits do not bind root")
    repo = Repo(tmp_path / "r")
    locked = repo.spec("locked")
    named = repo.spec("named")
    repo.workspace(queue=[entry(SPEC.format("named"), needs='""')])
    assert_unmigrated(D, repo.root)
    drop_workspace(repo)
    locked.chmod(0)
    named.chmod(0)
    try:
        result = D.dispatch(repo.root)
    finally:
        locked.chmod(0o644)
        named.chmod(0o644)
    unreadable = [f for f in result["findings"] if f["code"] == "unreadable_artifact"]
    assert [f["path"] for f in unreadable] == [SPEC.format("locked"), SPEC.format("named")]


def test_plan_problems_block_rather_than_hide_a_spec(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("planless", plan=None)
    repo.spec("linkplan")
    (repo.root / "docs/specs/linkplan/plan.md").unlink()
    (tmp_path / "elsewhere-plan.md").write_text("# Plan\n\n- **Status:** Approved\n")
    (repo.root / "docs/specs/linkplan/plan.md").symlink_to(tmp_path / "elsewhere-plan.md")
    repo.spec("lockedplan")
    plan = repo.root / "docs/specs/lockedplan/plan.md"
    if not IS_ROOT:
        plan.chmod(0)
    try:
        result = D.dispatch(repo.root)
    finally:
        plan.chmod(0o644)
    blocked = set(paths(result["blocked"]))
    assert SPEC.format("planless") in blocked
    if not IS_ROOT:
        locked = {i["path"]: i for i in result["blocked"]}[SPEC.format("lockedplan")]
        assert "unreadable_artifact" in codes(locked["findings"])
    linked = {i["path"]: i for i in result["blocked"]}[SPEC.format("linkplan")]
    assert "invalid_artifact_path" in codes(linked["findings"])


def test_status_word_forms(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("approved", "Approved")
    repo.spec("implementing", "Implementing")
    repo.spec("shipped", "Shipped")
    repo.spec("bare", status_line="**Status:** Approved\n")
    result = D.dispatch(repo.root)
    assert SPEC.format("approved") in paths(result["ready"])
    assert SPEC.format("implementing") in paths(result["active"])
    assert SPEC.format("shipped") not in paths(result["ready"] + result["active"])
    # The engine's status reader does not accept a bare `**Status:**` line.
    assert SPEC.format("bare") not in paths(result["ready"] + result["active"] + result["blocked"])


# --- AC-0012: the confined load ---------------------------------------------------


def _exits_2_unavailable(module: ModuleType, repo: Repo, capsys: pytest.CaptureFixture[str]) -> None:
    code = module.main(["--root", str(repo.root)])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "engine_unavailable" in captured.err


def _repo_with_spec(tmp_path: Path) -> Repo:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    return repo


def test_cli_prints_one_json_object_and_exits_zero(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    repo = _repo_with_spec(tmp_path)
    assert module.main(["--root", str(repo.root)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["decision"]["action"] == "start"
    assert module.main(["--root", str(repo.root), "--start", "nope"]) == 0
    assert json.loads(capsys.readouterr().out)["decision"]["action"] == "refuse"


@pytest.mark.parametrize(
    "argv",
    [[], ["--root"], ["--root", "{root}", "--start", "a", "--resume", "a"],
     ["--root", "{root}", "--bogus"]],
    ids=["no-root", "root-without-value", "both-selectors", "unknown-flag"],
)
def test_usage_errors_exit_2(
    D: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    repo = _repo_with_spec(tmp_path)
    (tmp_path / "plain-file").write_text("x")
    argv = [
        part.format(root=repo.root, missing=tmp_path / "missing", file=tmp_path / "plain-file")
        for part in argv
    ]
    with pytest.raises(SystemExit) as raised:
        D.main(argv)
    assert raised.value.code == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("name", ["missing", "plain-file"])
def test_a_root_that_is_not_a_directory_exits_2(
    D: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    (tmp_path / "plain-file").write_text("x")
    assert D.main(["--root", str(tmp_path / name)]) == 2
    assert capsys.readouterr().out == ""


def test_help_names_keys_actions_and_exit_codes(
    D: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        D.main(["--help"])
    assert raised.value.code == 0
    text = capsys.readouterr().out + (D.__doc__ or "")
    for word in ("schema_version", "ready", "active", "blocked", "findings", "decision",
                 "start", "resume", "ask", "none", "refuse", "candidates",
                 "dispatchable", "next_action", "exit 0", "exit 2"):
        assert word in text, word


_LOADED = ("_header_readiness.py", "file_safety.py")
_CALLED_NAME = {"_header_readiness.py": "_finding", "file_safety.py": "read_confined_regular_file"}


def _assert_unavailable_names(
    module: ModuleType, repo: Repo, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    """AC-0027: exit 2, nothing on standard output, standard error starts with the file name."""
    code = module.main(["--root", str(repo.root)])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err.startswith(f"engine_unavailable: {file_name}")


@pytest.mark.parametrize("file_name", _LOADED)
def test_missing_engine(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    (tree / "work-loop/scripts" / file_name).unlink()
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _assert_unavailable_names(module, _repo_with_spec(tmp_path), capsys, file_name)


@pytest.mark.parametrize("file_name", _LOADED)
def test_engine_symlinked_out_of_the_tree(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    link = tree / "work-loop/scripts" / file_name
    outside = tmp_path / f"outside-{file_name}"
    shutil.copy2(link, outside)
    link.unlink()
    link.symlink_to(outside)
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _assert_unavailable_names(module, _repo_with_spec(tmp_path), capsys, file_name)


@pytest.mark.parametrize("file_name", _LOADED)
def test_engine_import_raises(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    (tree / "work-loop/scripts" / file_name).write_text(
        "raise RuntimeError('boom')\n", encoding="utf-8"
    )
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _assert_unavailable_names(module, _repo_with_spec(tmp_path), capsys, file_name)


@pytest.mark.parametrize("file_name", _LOADED)
def test_engine_without_the_entry_point(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    (tree / "work-loop/scripts" / file_name).write_text("X = 1\n", encoding="utf-8")
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _assert_unavailable_names(module, _repo_with_spec(tmp_path), capsys, file_name)


@pytest.mark.parametrize("file_name", _LOADED)
def test_engine_name_that_is_not_callable(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], file_name: str
) -> None:
    broken = tree / "work-loop/scripts" / file_name
    broken.write_text(
        broken.read_text(encoding="utf-8") + f"\n{_CALLED_NAME[file_name]} = 'not callable'\n",
        encoding="utf-8",
    )
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    code = module.main(["--root", str(_repo_with_spec(tmp_path).root)])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    # The load-time refusal names the file; a run-time failure would say
    # "engine run failed", so this pins the callable check itself.
    assert captured.err.startswith(f"engine_unavailable: {file_name}")
    assert "engine run failed" not in captured.err


def test_missing_file_safety(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree / "work-loop/scripts/file_safety.py").unlink()
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_file_safety_without_the_reader(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree / "work-loop/scripts/file_safety.py").write_text("X = 1\n", encoding="utf-8")
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_file_safety_symlinked_out_of_the_tree(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    link = tree / "work-loop/scripts/file_safety.py"
    outside = tmp_path / "outside-file-safety.py"
    shutil.copy2(link, outside)
    link.unlink()
    link.symlink_to(outside)
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_dispatch_outside_a_scripts_directory(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    moved = tree / "work-loop" / "bin"
    moved.mkdir()
    for module_name in ("dispatch.py", "file_safety.py"):
        shutil.copy2(tree / "work-loop/scripts" / module_name, moved / module_name)
    module = _load(moved / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_dispatch_runs_from_a_directory_that_is_not_a_skills_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every load is a sibling load, so the layout the base required no longer matters."""
    other = _copy_skills(tmp_path / "other", name="not-skills")
    module = _load(other / "work-loop" / "scripts" / "dispatch.py")
    assert module.main(["--root", str(_repo_with_spec(tmp_path).root)]) == 0
    assert json.loads(capsys.readouterr().out)["decision"]["action"] == "start"


def test_loading_leaves_sys_path_and_the_tree_unchanged(
    tree: Path, tmp_path: Path
) -> None:
    before_path = list(sys.path)
    before_tree = snapshot(tree)
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    repo = _repo_with_spec(tmp_path)
    module.dispatch(repo.root)
    assert sys.path == before_path
    assert snapshot(tree) == before_tree
    assert not list(tree.rglob("__pycache__"))
    assert not list(repo.root.rglob("__pycache__"))


def test_main_runs_as_a_subprocess_with_utf8_json(tree: Path, tmp_path: Path) -> None:
    import subprocess

    repo = _repo_with_spec(tmp_path)
    done = subprocess.run(
        [sys.executable, "-I", str(tree / "work-loop/scripts/dispatch.py"), "--root", str(repo.root)],
        capture_output=True, check=False,
    )
    assert done.returncode == 0
    assert json.loads(done.stdout.decode("utf-8"))["decision"]["action"] == "start"
    broken = subprocess.run(
        [sys.executable, "-I", str(tree / "work-loop/scripts/dispatch.py"), "--root",
         str(tmp_path / "missing")],
        capture_output=True, check=False,
    )
    assert broken.returncode == 2 and broken.stdout == b""


# --- parity with workspace-status's selector rule ---------------------------------

_SELECTOR_TABLE = (
    "ok", "spec/ok", "docs/specs/ok", "docs/specs/ok/spec.md", "a_b-1", "A1",
    "", "..", "a/b/c", "docs/specs/../x", "/abs", "-x", "a\\b", "C:x", "x" * 201,
    "spec/", "docs/specs", "dotted.1", "spec/a/b", "docs/specs/ok/plan.md", "docs//specs/ok",
)


# What `workspace-status`'s selector rule returned for each input at the base:
# the canonical spec path, or None for a refusal. Recorded from that rule, so the
# test still fails if dispatch's rule drifts from it.
_SELECTOR_EXPECTED = {
    "ok": "docs/specs/ok/spec.md",
    "spec/ok": "docs/specs/ok/spec.md",
    "docs/specs/ok": "docs/specs/ok/spec.md",
    "docs/specs/ok/spec.md": "docs/specs/ok/spec.md",
    "a_b-1": "docs/specs/a_b-1/spec.md",
    "A1": "docs/specs/A1/spec.md",
    "": None,
    "..": None,
    "a/b/c": None,
    "docs/specs/../x": None,
    "/abs": None,
    "-x": None,
    "a\\b": None,
    "C:x": None,
    "x" * 201: None,
    "spec/": None,
    "docs/specs": None,
    "dotted.1": None,
    "spec/a/b": None,
    "docs/specs/ok/plan.md": None,
    "docs//specs/ok": None,
}


def test_selector_rule_matches_the_recorded_workspace_status_rule(D: ModuleType) -> None:
    """The one named difference: `docs/specs/<slug>/` is accepted here and was refused there."""

    def header(selector: str) -> str | None:
        try:
            return D._selector_path(selector)
        except D._InvalidSelector:
            return None

    assert set(_SELECTOR_EXPECTED) == set(_SELECTOR_TABLE)
    for selector, expected in _SELECTOR_EXPECTED.items():
        assert header(selector) == expected, selector
    assert header("docs/specs/ok/") == SPEC.format("ok")


# --- AC-0031: the cooling chain is confined to dispatch's own directory ------------

_COOLING_FILES = ("cooling.py", "close_work.py")
_COOLING_BREAKS = ("missing", "symlinked-out", "import-raises", "lacks-a-called-name")


def _plant_decoys(tree: Path, marker: Path) -> Path:
    """Plant files that record that they ran, where a cross-skill or outside load would find them."""
    decoy_text = f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
    for relative in ("close-work/scripts/cooling.py", "close-work/scripts/close_work.py",
                     "workspace-status/scripts/cooling.py"):
        decoy = tree / relative
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text(decoy_text, encoding="utf-8")
    outside = tree.parent / "outside-decoy.py"
    outside.write_text(decoy_text, encoding="utf-8")
    return outside


def _break_cooling(scripts: Path, file_name: str, how: str, outside: Path) -> None:
    target = scripts / file_name
    if how == "missing":
        target.unlink()
    elif how == "symlinked-out":
        target.unlink()
        target.symlink_to(outside)
    elif how == "import-raises":
        target.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    else:
        target.write_text("X = 1\n", encoding="utf-8")


def _cooled_repo(tmp_path: Path) -> Repo:
    repo = Repo(tmp_path / "r")
    repo.spec("cooled")
    repo.spec("other")
    repo.cool(SPEC.format("cooled"))
    return repo


def test_a_working_cooling_chain_excludes_the_cooled_spec(tree: Path, tmp_path: Path) -> None:
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    result = module.dispatch(_cooled_repo(tmp_path).root)
    assert paths(result["ready"]) == [SPEC.format("other")]
    assert "cooling_state_unavailable" not in codes(result["findings"])


@pytest.mark.parametrize("how", _COOLING_BREAKS)
@pytest.mark.parametrize("file_name", _COOLING_FILES)
def test_a_broken_cooling_file_is_cooling_state_unavailable(
    tree: Path, tmp_path: Path, file_name: str, how: str
) -> None:
    marker = tmp_path / "decoy-ran"
    outside = _plant_decoys(tree, marker)
    scripts = tree / "work-loop" / "scripts"
    _break_cooling(scripts, file_name, how, outside)
    module = _load(scripts / "dispatch.py")
    repo = _cooled_repo(tmp_path)
    result = module.dispatch(repo.root)
    assert "cooling_state_unavailable" in codes(result["findings"])
    # No artifact is treated as cooled: the spec the record names is still dispatchable.
    assert paths(result["ready"]) == [SPEC.format("cooled"), SPEC.format("other")]
    assert not marker.exists()


@pytest.mark.parametrize("file_name", _COOLING_FILES)
def test_an_absent_lifecycle_directory_loads_no_cooling_file(
    tree: Path, tmp_path: Path, file_name: str
) -> None:
    (tree / "work-loop/scripts" / file_name).unlink()
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    result = module.dispatch(_repo_with_spec(tmp_path).root)
    assert result["findings"] == []


def test_a_failed_cooling_load_leaves_no_registered_module(tree: Path, tmp_path: Path) -> None:
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    before = sys.modules.get("cooling_close_work")
    module.dispatch(_cooled_repo(tmp_path).root)
    assert sys.modules.get("cooling_close_work") is before


# --- AC-0006: one planted repository per finding code the headers can raise --------

_RECEIPT_BLOCK = (
    '[[coordination_receipts]]\nid = "remote-prereq"\nremote_kind = "brief"\n'
    'remote_ref = "example-service://projects/example-artifact"\n'
    'accepted_revision = "remote-rev-7"\nrequired_status = "Shipped"\n'
    'reported_status = "Shipped"\nreviewed_by = "Example Reviewer"\n'
    'reviewed_at = "2026-08-10T00:00:00Z"\nrefresh_conflict = false\n'
)


def _waiter(repo: Repo, header: str) -> None:
    repo.put(
        "docs/specs/a/spec.md",
        f"# Spec: a\n\n- **Status:** Approved\n- **Brief:** none\n{header}",
    )
    repo.put("docs/specs/a/plan.md", "# Plan\n\n- **Status:** Approved\n")


def _plant_dependency(repo: Repo, case: str) -> None:
    if case == "dependency_cycle":
        repo.spec("a", depends="spec:b")
        repo.spec("b", depends="spec:a")
    elif case == "missing_dependency":
        repo.spec("a", depends="spec:nowhere")
    elif case == "invalid_dependency":
        repo.spec("a", depends="!!garbage!!")
    elif case == "unsatisfied_dependency":
        repo.spec("open")
        repo.spec("a", depends="spec:open")
    elif case == "invalid_completion_receipt":
        _waiter(
            repo,
            "- **Depends on:** spec:gone\n- **Dependency receipts:** spec:gone completion "
            "delivery-123 invalid merge pr:123\n",
        )
    elif case == "invalid_receipt":
        _waiter(
            repo,
            "- **Depends on:** brief:remote\n- **Dependency receipts:** brief:remote "
            "coordination brief remote-prereq remote-rev-8\n",
        )
        repo.put(
            "docs/product/briefs/remote.md",
            "# Brief: remote\n\n- **Status:** Shipped\n- **Slug:** remote\n\n"
            f"```toml coordination-receipts\n{_RECEIPT_BLOCK}```\n",
        )
    else:
        assert case == "refresh_conflict"
        repo.spec("a")
        path = repo.root / "docs/specs/a/spec.md"
        path.write_text(path.read_text(encoding="utf-8") + "- **Refresh conflict:** true\n",
                        encoding="utf-8")


@pytest.mark.parametrize(
    "case",
    ["dependency_cycle", "missing_dependency", "invalid_dependency", "unsatisfied_dependency",
     "invalid_completion_receipt", "invalid_receipt", "refresh_conflict"],
)
def test_a_header_raises_each_dependency_and_conflict_finding(
    D: ModuleType, tmp_path: Path, case: str
) -> None:
    repo = Repo(tmp_path / "r")
    _plant_dependency(repo, case)
    result = D.dispatch(repo.root)
    blocked = {item["path"]: item for item in result["blocked"]}
    assert case in codes(blocked[SPEC.format("a")]["findings"])
    assert SPEC.format("a") not in paths(result["ready"])


def test_a_captured_item_with_a_bad_field_is_an_invalid_captured_item(
    R: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.put("docs/product/captured/bad.md", "# Defect\n\n- **Status:** Bogus\n- **Kind:** defect\n")
    item, finding = R.read_captured_item(repo.root, "bad.md", frozenset())
    assert item == {"path": "docs/product/captured/bad.md", "slug": "bad", "invalid": True}
    assert finding is not None
    assert finding.code == "invalid_captured_item"
    assert finding.next_action == R._FINDING_NEXT_ACTIONS["invalid_captured_item"]
    assert "invalid_captured_item" in R._FINDING_NEXT_ACTIONS


@pytest.mark.parametrize(
    ("block", "code"),
    [("", "source_authority_migration_required"),
     ("\n```toml source-authority\nmode = 1\n```\n", "invalid_source_authority")],
)
def test_a_tracker_origin_artifact_without_a_valid_authority_block_is_refused(
    R: ModuleType, tmp_path: Path, block: str, code: str
) -> None:
    repo = Repo(tmp_path / "r")
    path = repo.spec("trk")
    path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")
    source = R.SourceRecord(mode="tracker-origin", ref="example-service://ABC-1", revision="r1")
    tracked = R.WorkspaceEntry(
        path=SPEC.format("trk"), kind="spec", source=source, summary="t", needs=[]
    )
    metadata = R._metadata_from_root(repo.root, tracked)
    assert metadata is not None and metadata.authority_error == code
    found = R._structural_findings(
        R.WorkspaceMembership(tracked, "work.queue"), metadata, set(), {}, repo.root
    )
    assert code in codes([{"code": f.code} for f in found])


# --- AC-0006: the finding table ----------------------------------------------------

_DISPATCH_SUITES = (
    "test_dispatch.py", "test_header_derived_dispatch_replay.py",
    "test_work_intake_dispatch.py", "test_dispatch_isolation.py",
)


def _asserted_strings(path: Path) -> set[str]:
    """String constants in each `assert` of the module, and in the parametrize lists of a test."""
    tree = ast.parse(path.read_text(encoding="utf-8"))

    def strings(node: ast.AST) -> set[str]:
        return {
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }

    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            found |= strings(node)
        elif isinstance(node, ast.FunctionDef) and any(
            isinstance(child, ast.Assert) for child in ast.walk(node)
        ):
            for decorator in node.decorator_list:
                found |= strings(decorator)
    return found


def test_every_code_in_the_finding_table_is_asserted_by_a_dispatch_suite(
    base_skills: Path,
) -> None:
    table = _load(base_skills / "work-loop/scripts/_header_readiness.py")._FINDING_NEXT_ACTIONS
    asserted: set[str] = set()
    for name in _DISPATCH_SUITES:
        asserted |= _asserted_strings(Path(__file__).with_name(name))
    assert "unmigrated_workspace" in table
    assert sorted(code for code in table if code not in asserted) == []


def test_every_finding_dispatch_prints_is_a_table_pair(
    D: ModuleType, base_skills: Path, tmp_path: Path
) -> None:
    table = _load(base_skills / "work-loop/scripts/_header_readiness.py")._FINDING_NEXT_ACTIONS
    repo = Repo(tmp_path / "r")
    repo.spec("noplan", plan=None)
    repo.spec("draft", "Draft", depends="spec:nowhere")
    repo.spec("approved")
    repo.spec("waits", depends="spec:approved")
    repo.put("docs/lifecycle/broken.json", "{not json")
    repo.put("docs/specs/afile", "x")
    seen: list[dict[str, Any]] = []
    for mode, selector in ((None, None), ("start", "draft"), ("start", "ghost")):
        result = D.dispatch(repo.root, mode, selector)
        seen += [*result["findings"], *result["decision"]["findings"]]
        for item in (*result["ready"], *result["active"], *result["blocked"]):
            seen += item["findings"]
    assert seen
    for finding in seen:
        assert table[finding["code"]] == finding["next_action"]


# --- `--captured` (repair-only-workspace-status AC-0005) -----------------------------

_CAPTURED_FIXTURES = Path(__file__).parent / "fixtures" / "captured-projection"
_BASE_KEYS = {"schema_version", "ready", "active", "blocked", "findings", "decision"}


def _plant_fixture(root: Path, repository: dict[str, Any]) -> None:
    """Plant the exact repository bytes a fixture's `captured` literal was computed from."""
    for relative, text in repository["files"].items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for relative, data in repository["binary"].items():
        (root / relative).write_bytes(bytes.fromhex(data))
    for relative, target in repository["symlinks"].items():
        (root / relative).symlink_to(target)


# Literal paths, so the pack-test boundary lint can see each read stays in the pack.
_CAPTURED_FIXTURE_FILES = {
    "mixed-empty-workspace": _CAPTURED_FIXTURES / "mixed-empty-workspace.json",
    "mixed-no-workspace": _CAPTURED_FIXTURES / "mixed-no-workspace.json",
    "mixed-unmigrated-workspace": _CAPTURED_FIXTURES / "mixed-unmigrated-workspace.json",
    "no-captured-directory": _CAPTURED_FIXTURES / "no-captured-directory.json",
}


def _fixture_names() -> list[str]:
    return sorted(_CAPTURED_FIXTURE_FILES)


@pytest.mark.skipif(not hasattr(os, "symlink") or os.name == "nt", reason="needs symlinks")
@pytest.mark.parametrize("name", _fixture_names())
@pytest.mark.parametrize("mode", [(None, None), ("start", "a"), ("resume", "a")])
def test_captured_equals_recorded_base_projection(
    D: ModuleType, tmp_path: Path, name: str, mode: tuple[str | None, str | None]
) -> None:
    fixture = json.loads(_CAPTURED_FIXTURE_FILES[name].read_text(encoding="utf-8"))
    root = tmp_path / "r"
    root.mkdir()
    _plant_fixture(root, fixture["repository"])
    flagged = D.dispatch(root, *mode, captured=True)
    plain = D.dispatch(root, *mode)
    assert flagged["captured"] == fixture["captured"]
    assert set(plain) == _BASE_KEYS
    assert {key: flagged[key] for key in _BASE_KEYS} == plain


def test_every_captured_fixture_file_is_listed() -> None:
    assert sorted(path.stem for path in _CAPTURED_FIXTURES.glob("*.json")) == _fixture_names()


def test_captured_fixtures_cover_every_route_and_failure() -> None:
    fixture = json.loads((_CAPTURED_FIXTURES / "mixed-no-workspace.json").read_text("utf-8"))
    items = fixture["captured"]["items"]
    assert {i.get("type") for i in items} >= {"shape", "research", "strategy", "design", "signal"}
    assert any(i.get("invalid") for i in items) and any(i.get("unreadable") for i in items)
    assert set(_fixture_names()) == {
        "mixed-no-workspace", "mixed-empty-workspace", "mixed-unmigrated-workspace",
        "no-captured-directory",
    }


def test_captured_flag_prints_one_extra_key(
    D: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = Repo(tmp_path / "r")
    repo.put("docs/product/captured/a.md", "# A\n\n- **Status:** Open\n- **Kind:** defect\n")
    assert D.main(["--root", str(repo.root), "--captured"]) == 0
    flagged = json.loads(capsys.readouterr().out)
    assert D.main(["--root", str(repo.root)]) == 0
    assert set(json.loads(capsys.readouterr().out)) == _BASE_KEYS
    assert set(flagged) == _BASE_KEYS | {"captured"}
    assert [i["slug"] for i in flagged["captured"]["items"]] == ["a"]


# --- repairs from the first implementation review ---------------------------------
#
# Every expectation below is a literal computed from the base engine's dispatch
# (commit ab4e4b71c) on the same planted repository; nothing here calls the base.
# The one exception is the `brief_queue.executing` case, which pins the settled output.

_INVALID_WORKSPACE_NEXT_ACTION = "Correct workspace.toml, then rerun reconciliation."


def _invalid_workspace(path: str) -> dict[str, Any]:
    return {
        "code": "invalid_workspace", "path": path, "dispatchable": False,
        "next_action": _INVALID_WORKSPACE_NEXT_ACTION,
    }


_ALPHA, _BETA = SPEC.format("alpha"), SPEC.format("beta")
# Each structural shape the base membership extraction refused, no entry anywhere:
# the file, and the path the base put on its one top-level finding.
_STRUCTURAL_SHAPES = {
    "top-level entry section that is not a table": ('backlog = "x"\n', "backlog"),
    "lifecycle collection that is a string": ('[backlog]\nopen = "x"\n', "workspace.toml"),
    "non-canonical initiative key": ('[ini-abc]\nname = "x"\n', "workspace.toml"),
    "initiative section that is not a table": ('ini-001 = "x"\n', "workspace.toml"),
    "initiative subsection that is not a table": ('[ini-001]\nwork = "x"\n', "ini-001.work"),
    "initiative lifecycle list that is a string": (
        '[ini-001.work]\nqueue = "x"\n', "workspace.toml"
    ),
    "initiative key with a trailing newline": ('"ini-001\\n" = {a = 1}\n', "workspace.toml"),
}


@pytest.mark.parametrize("shape", list(_STRUCTURAL_SHAPES))
def test_a_malformed_entry_free_workspace_gives_the_base_invalid_workspace_output(
    D: ModuleType, tmp_path: Path, shape: str
) -> None:
    toml, top_path = _STRUCTURAL_SHAPES[shape]
    repo = Repo(tmp_path / "r")
    repo.spec("alpha")
    repo.spec("beta", "Implementing")
    repo.put("workspace.toml", toml)
    blocked = [
        {"path": path, "slug": slug, "status": status, "findings": [_invalid_workspace(path)]}
        for path, slug, status in ((_ALPHA, "alpha", "Approved"), (_BETA, "beta", "Implementing"))
    ]
    top = [_invalid_workspace(top_path)]
    assert D.dispatch(repo.root) == {
        "schema_version": 1, "ready": [], "active": [], "blocked": blocked, "findings": top,
        "decision": {"action": "none", "path": None, "candidates": [], "findings": []},
    }
    for mode, selector, path in (("start", "alpha", _ALPHA), ("resume", "beta", _BETA)):
        assert D.dispatch(repo.root, mode, selector) == {
            "schema_version": 1, "ready": [], "active": [], "blocked": blocked, "findings": top,
            "decision": {
                "action": "refuse", "path": None, "candidates": [],
                "findings": [_invalid_workspace(path)],
            },
        }


def test_a_string_in_brief_queue_executing_is_not_a_structural_fault(
    D: ModuleType, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("alpha")
    # Pins the settled output: the base also reported `unsupported_legacy` here, which
    # this slice drops by design.
    repo.put("workspace.toml", '[ini-001.brief_queue]\nexecuting = "x"\n')
    result = D.dispatch(repo.root)
    assert paths(result["ready"]) == [_ALPHA] and result["findings"] == []


@pytest.mark.parametrize("depth", [700, 990, 2000])
def test_a_deeply_nested_dotted_key_workspace_gives_the_entry_free_base_output(
    D: ModuleType, tmp_path: Path, depth: int
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("alpha")
    repo.spec("beta", "Implementing")
    repo.put("workspace.toml", "a" + ".a" * depth + " = 1\n")
    ready = {"path": _ALPHA, "slug": "alpha", "status": "Approved", "findings": []}
    active = {"path": _BETA, "slug": "beta", "status": "Implementing", "findings": []}
    if depth == 2000:
        text = "a" + ".a" * depth + " = 1\n"
        try:
            tomllib.loads(text)
        except (RecursionError, tomllib.TOMLDecodeError):
            pass
        else:
            pytest.skip(
                "this tomllib accepts 2000-part keys; the 700 and 990 cases pin recursion safety"
            )
        # Past the parser's own depth limit: the base refused the file as unusable.
        refused = [_invalid_workspace("workspace.toml")]
        assert D.dispatch(repo.root) == {
            "schema_version": 1, "ready": [], "active": [], "blocked": [], "findings": refused,
            "decision": {"action": "refuse", "path": None, "candidates": [], "findings": refused},
        }
        return
    assert D.dispatch(repo.root) == {
        "schema_version": 1, "ready": [ready], "active": [active], "blocked": [], "findings": [],
        "decision": {"action": "resume", "path": _BETA, "candidates": [], "findings": []},
    }
    assert D.dispatch(repo.root, "start", "alpha")["decision"] == {
        "action": "start", "path": _ALPHA, "candidates": [], "findings": [],
    }


@pytest.mark.parametrize(
    "brief", ["../outside.md", "/etc/passwd", "docs\\x.md", "https://example.com/x"]
)
def test_an_unsafe_brief_parent_gives_the_base_output(
    D: ModuleType, tmp_path: Path, brief: str
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("alpha", brief=brief)
    assert D.dispatch(repo.root) == {
        "schema_version": 1, "ready": [], "active": [], "blocked": [],
        "findings": [
            {
                "code": "invalid_artifact_path", "path": "workspace.toml", "dispatchable": False,
                "next_action": "Replace it with a confined canonical repository-relative path.",
            }
        ],
        "decision": {"action": "none", "path": None, "candidates": [], "findings": []},
    }
    assert D.dispatch(repo.root, "start", "alpha")["decision"] == {
        "action": "refuse", "path": None, "candidates": [],
        "findings": [
            {
                "code": "unapproved_spec", "path": _ALPHA, "dispatchable": False,
                "next_action": "Complete the spec approval gate.",
            }
        ],
    }


def test_a_dependent_of_an_unsafe_brief_spec_stays_blocked(D: ModuleType, tmp_path: Path) -> None:
    """The refused spec still blocks its dependent; literals computed from the base dispatch."""
    repo = Repo(tmp_path / "r")
    repo.spec("alpha", depends="spec:beta")
    repo.spec("beta", brief="../outside.md")
    unsatisfied = {
        "code": "unsatisfied_dependency", "path": _BETA, "dispatchable": False,
        "next_action": "Complete or explicitly revise the dependency.",
    }
    assert D.dispatch(repo.root) == {
        "schema_version": 1, "ready": [], "active": [],
        "blocked": [
            {"path": _ALPHA, "slug": "alpha", "status": "Approved", "findings": [unsatisfied]}
        ],
        "findings": [
            {
                "code": "invalid_artifact_path", "path": "workspace.toml", "dispatchable": False,
                "next_action": "Replace it with a confined canonical repository-relative path.",
            }
        ],
        "decision": {"action": "none", "path": None, "candidates": [], "findings": []},
    }
    assert D.dispatch(repo.root, "start", "alpha")["decision"] == {
        "action": "refuse", "path": None, "candidates": [], "findings": [unsatisfied],
    }
