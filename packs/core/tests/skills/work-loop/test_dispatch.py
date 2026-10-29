"""Header-derived dispatch: `work-loop`'s read-only `dispatch.py`.

Spec: docs/specs/header-derived-dispatch/spec.md (AC-0001 to AC-0012).
Verification mode: TDD. Each test plants one repository under `tmp_path`, loads
`dispatch.py` from a planted `skills/` tree that also holds a copy of the engine,
its siblings, `close-work`'s `cooling.py` and `work-loop`'s `file_safety.py`, and
asserts the dispatch result. Nothing above `packs/core` is read.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import itertools
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_PACK = Path(__file__).resolve().parents[3]
_SKILLS = _PACK / ".apm" / "skills"
_COUNTER = itertools.count()

SPEC = "docs/specs/{}/spec.md"
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _copy_skills(destination: Path, *, name: str = "skills") -> Path:
    """Plant the real engine, cooling module and work-loop scripts under `destination`."""
    skills = destination / name
    ignore = shutil.ignore_patterns("__pycache__")
    for relative in ("workspace-status/scripts", "close-work/scripts"):
        shutil.copytree(_SKILLS / relative, skills / relative, ignore=ignore)
    scripts = skills / "work-loop" / "scripts"
    scripts.mkdir(parents=True)
    for module in ("dispatch.py", "file_safety.py"):
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


def test_dropped_entries_raise_no_registry_findings(D: ModuleType, tmp_path: Path) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.spec("b", "Implementing")
    repo.workspace(
        queue=[entry(SPEC.format("a")), entry(SPEC.format("b")), entry(SPEC.format("a"))],
        active=[entry(SPEC.format("a"))],
        shipped=[entry(SPEC.format("b"))],
    )
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


def test_output_is_independent_of_dropped_entries(D: ModuleType, tmp_path: Path) -> None:
    bare = Repo(tmp_path / "bare")
    one = Repo(tmp_path / "one")
    two = Repo(tmp_path / "two")
    only = Repo(tmp_path / "only")
    for repo in (bare, one, two, only):
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
    reference = encode(D.dispatch(bare.root))
    for repo in (one, two, only):
        assert encode(D.dispatch(repo.root)) == reference


@pytest.mark.parametrize(
    "needs",
    [None, '""', "{}", '[{type = "local", kind = "spec", path = "docs/specs/b/spec.md"}]'],
    ids=["missing", "string", "table", "nonempty"],
)
def test_spec_entry_without_an_empty_needs_array_is_kept(
    D: ModuleType, tmp_path: Path, needs: str | None
) -> None:
    repo = Repo(tmp_path / "r")
    repo.spec("a")
    repo.spec("b")
    repo.workspace(queue=[entry(SPEC.format("a"), needs=needs)])
    result = D.dispatch(repo.root)
    # A kept entry is evaluated by the engine as the registry holds it.
    kept = [i for i in (*result["ready"], *result["blocked"]) if i["path"] == SPEC.format("a")]
    assert len(kept) <= 1
    named = D.dispatch(repo.root, "start", "a")["decision"]
    if needs in (None, '""', "{}"):
        assert named["action"] == "refuse"
        assert "invalid_entry" in codes(named["findings"])


def test_kept_entries_of_each_kind_are_judged_by_the_engine(
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
    result = D.dispatch(repo.root)
    listed = {item["path"] for item in (*result["ready"], *result["active"], *result["blocked"])}
    assert SPEC.format("trk") in listed
    inactive = {i["path"]: i for i in result["blocked"]}[SPEC.format("inactive")]
    assert "inactive_initiative" in codes(inactive["findings"])
    for slug, code in (("legacy-str", "unsupported_legacy"),):
        decision = D.dispatch(repo.root, "start", slug)["decision"]
        assert decision["action"] == "refuse" and code in codes(decision["findings"])
    decision = D.dispatch(repo.root, "start", "legacy-tbl")["decision"]
    assert decision["action"] == "refuse" and decision["findings"]
    assert SPEC.format("legacy-str") not in paths(result["ready"])
    assert SPEC.format("legacy-tbl") not in paths(result["ready"])


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
    repo.workspace(queue=[entry(SPEC.format("a"))])
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
    assert decision["candidates"] == [SPEC.format("only"), SPEC.format("other")][::-1] or (
        decision["candidates"] == sorted(decision["candidates"])
    )
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
    # rule 2: blocked findings
    assert "missing_plan" in _refusal(D, repo, "start", "noplan")
    # rule 3: a kept entry without evaluation findings still refuses
    kept = Repo(tmp_path / "kept")
    kept.spec("k", "Implementing")
    kept.workspace(active=[entry(SPEC.format("k"), needs='[{type = "local", kind = "spec", '
                                 'path = "docs/specs/x/spec.md"}]')])
    assert _refusal(D, kept, "start", "k")
    assert "unsupported_legacy" in _refusal(D, repo, "start", "legacy-one")
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


def test_unreadable_spec_gives_one_finding_unless_a_kept_entry_names_it(
    D: ModuleType, tmp_path: Path
) -> None:
    if IS_ROOT:
        pytest.skip("permission bits do not bind root")
    repo = Repo(tmp_path / "r")
    locked = repo.spec("locked")
    named = repo.spec("named")
    repo.workspace(queue=[entry(SPEC.format("named"), needs="[]  ")])
    # `named` keeps its entry only because the entry below is not droppable.
    repo.workspace(queue=[entry(SPEC.format("named"), needs='""')])
    locked.chmod(0)
    named.chmod(0)
    try:
        result = D.dispatch(repo.root)
    finally:
        locked.chmod(0o644)
        named.chmod(0o644)
    unreadable = [f for f in result["findings"] if f["code"] == "unreadable_artifact"]
    assert [f["path"] for f in unreadable] == [SPEC.format("locked")]


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


def test_missing_engine(tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tree / "workspace-status/scripts/workspace_status_engine.py").unlink()
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_engine_symlinked_out_of_the_tree(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = tree / "workspace-status/scripts/workspace_status_engine.py"
    outside = tmp_path / "outside-engine.py"
    shutil.copy2(engine, outside)
    engine.unlink()
    engine.symlink_to(outside)
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_engine_import_raises(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree / "workspace-status/scripts/workspace_status_engine.py").write_text(
        "raise RuntimeError('boom')\n", encoding="utf-8"
    )
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


def test_engine_without_the_entry_point(
    tree: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree / "workspace-status/scripts/workspace_status_engine.py").write_text(
        "X = 1\n", encoding="utf-8"
    )
    module = _load(tree / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


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


def test_dispatch_outside_a_skills_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = _copy_skills(tmp_path / "other", name="not-skills")
    module = _load(other / "work-loop" / "scripts" / "dispatch.py")
    _exits_2_unavailable(module, _repo_with_spec(tmp_path), capsys)


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
