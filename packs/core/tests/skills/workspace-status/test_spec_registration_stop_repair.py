"""Construction tests for the `spec-entry-drop` repair step.

Spec: docs/specs/spec-registration-stop/spec.md (AC-0014 to AC-0020, AC-0042).
Verification mode: TDD.

Each test plants a repository under ``tmp_path`` and runs ``repair-plan`` and
``repair-apply`` in process through the script's ``main``; ``dispatch.py`` is
called in process the same way.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

_PACKS = Path(__file__).resolve().parents[3] / ".apm/skills"
_WS_MODULE = "workspace_status_spec_registration_stop_repair"
_DISPATCH_MODULE = "dispatch_spec_registration_stop_repair"


def _load(name: str, path: Path) -> ModuleType:
    """Load a module by file path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WS = _load(_WS_MODULE, _PACKS / "workspace-status/scripts/workspace_status.py")
DISPATCH = _load(_DISPATCH_MODULE, _PACKS / "work-loop/scripts/dispatch.py")
PLAN = ".workspace-repair-plan.json"
DROP = "spec-entry-drop"
ABSENT: Any = object()
BRIEFS = "docs/product/briefs"
BRIEF = f"{BRIEFS}/parent.md"
# A need the repair refuses (a brief that does not exist) keeps `needs` non-empty.
STUCK = '[{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]'


def spec_path(slug: str) -> str:
    return f"docs/specs/{slug}/spec.md"


def row(
    path: str,
    *,
    kind: str = "spec",
    mode: str = "repo-origin",
    parent: Any = ABSENT,
    needs: str | None = "[]",
) -> str:
    """One registry entry as an inline table."""
    if mode == "repo-origin":
        clause = "" if parent is ABSENT else f', parent = "{parent}"'
        source = f'{{mode = "repo-origin"{clause}}}'
    else:
        source = '{mode = "tracker-origin", ref = "example-service://ABC-1", revision = "r1"}'
    tail = "" if needs is None else f", needs = {needs}"
    return f'{{path = "{path}", kind = "{kind}", source = {source}, summary = "fixture"{tail}}}'


def record(slug: str, locator: str, parent: str | None = None) -> str:
    """A schema-valid Cooling lifecycle record, with `parent` when given."""
    payload: dict[str, Any] = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": slug,
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
        payload["parent"] = parent
    return json.dumps(payload)


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plant(
    root: Path,
    *,
    queue: list[str] | None = None,
    active: list[str] | None = None,
    shipped: list[str] | None = None,
    shaping: list[str] | None = None,
    open_: list[str] | None = None,
    files: dict[str, str] | None = None,
    comment: str = "",
) -> Path:
    """Write a registry, one spec file pair per spec entry, and ``files``."""

    def rows(values: list[str] | None) -> str:
        return "[\n" + "".join(f"  {v},\n" for v in values or []) + "]"

    text = (
        "# fixture header comment\n"
        f"[backlog]\nopen = {rows(open_)}\nclosed = []\n\n"
        '["ini-001"]\nname = "Fixture"\nstatus = "active"\nmilestone = "m1"\n\n'
        f'["ini-001".work]\nqueue = {rows(queue)}\nactive = {rows(active)}\n'
        f"shipped = {rows(shipped)}\n\n"
        f'["ini-001".shaping_queue]\nactive = {rows(shaping)}\nbacklog = []\n{comment}'
    )
    write(root, "workspace.toml", text)
    write(root, "AGENTS.md", "# Agents\n")
    for rel, body in (files or {}).items():
        write(root, rel, body)
    return root


def spec_files(*slugs: str, status: str = "Approved") -> dict[str, str]:
    files: dict[str, str] = {}
    for slug in slugs:
        files[spec_path(slug)] = f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n"
        files[f"docs/specs/{slug}/plan.md"] = "# Plan\n\n- **Status:** Approved\n"
    return files


def cooled_files(slug: str, parent: str | None = None, status: str = "Shipped") -> dict[str, str]:
    return {
        **spec_files(slug, status=status),
        f"docs/lifecycle/{slug}.json": record(slug, spec_path(slug), parent),
    }


def run(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = WS.main([*args, "--root", str(root)])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1]) if out else {}


def plan(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    code, data = run(root, capsys, "repair-plan")
    assert code == 0, data
    return data


def apply(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    return run(root, capsys, "repair-apply", "--yes")


def drops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [op for op in data["automatic_operations"] if op["operation_type"] == DROP]


def drop_paths(data: dict[str, Any]) -> set[str]:
    return {op["path"] for op in drops(data)}


def held(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f.get("reason") == "held-record-lacks-parent"]


def queue_ops(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        op for op in data["automatic_operations"]
        if op["operation_type"] in ("queue-to-shipped", "queue-remove")
    ]


def registry_text(root: Path) -> str:
    return (root / "workspace.toml").read_text(encoding="utf-8")


def rewrite_plan(root: Path, change: Callable[[dict[str, Any]], None]) -> None:
    data = json.loads((root / PLAN).read_text(encoding="utf-8"))
    change(data)
    data["plan_id"] = WS._recompute_plan_id(data)
    (root / PLAN).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def lifecycle_digest(root: Path) -> list[tuple[str, str, int]]:
    """Path, content digest and modification time of every file under docs/lifecycle/."""
    base = root / "docs" / "lifecycle"
    if not base.exists():
        return []
    return sorted(
        (
            p.relative_to(root).as_posix(),
            hashlib.sha256(p.read_bytes()).hexdigest(),
            p.stat().st_mtime_ns,
        )
        for p in base.rglob("*")
        if p.is_file()
    )


def dispatch_stdout(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    capsys.readouterr()
    assert DISPATCH.main(["--root", str(root)]) == 0
    return capsys.readouterr().out


# ── AC-0016: which entries are drop candidates ───────────────────────────────


def test_one_drop_per_candidate_and_none_for_any_other_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    files = spec_files("q", "a", "s", "b", "t", "k", "sh", "stuck")
    repo = plant(
        tmp_path,
        queue=[row(spec_path("q")), row(spec_path("stuck"), needs=STUCK)],
        active=[row(spec_path("a"))],
        shipped=[row(spec_path("s"))],
        open_=[row(spec_path("b")), row("docs/product/notes/n.md", kind="design")],
        shaping=[row(spec_path("sh"))],
        files={**files, "docs/product/notes/n.md": "# Note\n"},
    )
    # A tracker-origin spec, and a spec outside `work.` and `backlog.` (above).
    write(repo, "workspace.toml", registry_text(repo).replace(
        "queue = [\n", f"queue = [\n  {row(spec_path('t'), mode='tracker-origin')},\n"
    ))
    data = plan(repo, capsys)
    assert drop_paths(data) == {spec_path(s) for s in ("q", "a", "s", "b")}
    by_path = {op["path"]: op for op in drops(data)}
    queue_op = by_path[spec_path("q")]
    assert set(queue_op) == {
        "operation_type", "entry_locator", "path", "kind", "registry_fingerprint",
    }
    assert queue_op["kind"] == "spec"
    assert queue_op["entry_locator"]["ini_slug"] == "ini-001"
    assert queue_op["entry_locator"]["collection"] == "work.queue"
    assert by_path[spec_path("b")]["entry_locator"] == {
        "ini_slug": "", "collection": "backlog.open", "index": 0,
    }
    assert len(queue_op["registry_fingerprint"]) == 64
    assert WS._validate_plan_structure(data) is None


def test_an_entry_with_no_needs_key_gets_no_drop_and_keeps_its_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("bare"), needs=None), row(spec_path("ok"))],
        files=spec_files("bare", "ok"),
    )
    data = plan(repo, capsys)
    assert drop_paths(data) == {spec_path("ok")}
    assert any(
        f["path"] == spec_path("bare") for f in data["canonical"]["findings"]
    ), data["canonical"]["findings"]


def test_an_entry_whose_needs_the_same_plan_empties_is_a_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    need = f'[{{type = "local", kind = "spec", path = "{spec_path("peer")}"}}]'
    repo = plant(
        tmp_path,
        queue=[row(spec_path("waiter"), needs=need), row(spec_path("peer"))],
        files=spec_files("waiter", "peer"),
    )
    data = plan(repo, capsys)
    assert {op["operation_type"] for op in data["automatic_operations"]} == {
        "needs-to-header", DROP,
    }
    assert drop_paths(data) == {spec_path("waiter"), spec_path("peer")}
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert "docs/specs" not in registry_text(repo)
    assert "- **Depends on:** spec:peer" in (repo / spec_path("waiter")).read_text()


# ── AC-0014: queue operations skip a drop candidate ──────────────────────────


def test_queue_operations_skip_candidates_and_stay_for_other_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[
            row(spec_path("done")),
            row(spec_path("stuck-done"), needs=STUCK),
            row(spec_path("stuck-gone"), needs=STUCK),
        ],
        files={
            **spec_files("done", status="Shipped"),
            **spec_files("stuck-done", status="Shipped"),
            **spec_files("stuck-gone", status="Archived"),
        },
    )
    data = plan(repo, capsys)
    assert {(op["operation_type"], op["spec_path"]) for op in queue_ops(data)} == {
        ("queue-to-shipped", spec_path("stuck-done")),
        ("queue-remove", spec_path("stuck-gone")),
    }
    assert drop_paths(data) == {spec_path("done")}


# ── AC-0017: held entries and the declared parent ────────────────────────────


@pytest.mark.parametrize(
    ("parent", "expected"),
    [
        (ABSENT, None),
        ("none", "none"),
        (BRIEF, BRIEF),
        # Not a brief file: nothing is listed under that name.
        (f"{BRIEFS}/missing.md", None),
        # A brief file, but outside the record's pattern.
        (f"{BRIEFS}/Upper_Case.md", None),
        ("brief:parent", BRIEF),
    ],
)
def test_a_cooled_candidate_is_held_only_when_it_declares_a_parent_the_record_lacks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], parent: Any, expected: str | None
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("c"), parent=parent)],
        files={
            **cooled_files("c"),
            BRIEF: "# Brief\n\n- **Status:** Ready\n",
            f"{BRIEFS}/Upper_Case.md": "# Brief\n\n- **Status:** Ready\n",
        },
    )
    data = plan(repo, capsys)
    if expected is None:
        assert drop_paths(data) == {spec_path("c")}
        assert held(data) == []
        return
    assert drops(data) == []
    [item] = held(data)
    assert item["spec_path"] == spec_path("c")
    assert item["record_path"] == "docs/lifecycle/c.json"
    assert item["parent"] == expected
    assert item["finding_type"] == 6


def test_an_empty_parent_is_not_a_membership_so_it_gets_neither_drop_nor_hold(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The engine refuses an empty `source.parent` entry, so the iterator never yields it."""
    repo = plant(
        tmp_path,
        queue=[row(spec_path("c"), parent="")],
        files=cooled_files("c"),
    )
    data = plan(repo, capsys)
    assert drops(data) == [] and held(data) == []
    assert [f["path"] for f in data["canonical"]["findings"]] == [spec_path("c")]


def test_a_record_that_already_has_parent_does_not_hold_the_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("c"), parent=BRIEF)],
        files={**cooled_files("c", parent=BRIEF), BRIEF: "# Brief\n\n- **Status:** Ready\n"},
    )
    data = plan(repo, capsys)
    assert drop_paths(data) == {spec_path("c")} and held(data) == []


def test_a_held_entry_in_work_queue_keeps_its_collection_through_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("c"), parent="none"), row(spec_path("free"))],
        files={**cooled_files("c"), **spec_files("free")},
    )
    data = plan(repo, capsys)
    assert queue_ops(data) == [] and drop_paths(data) == {spec_path("free")}
    code, result = apply(repo, capsys)
    assert code == 0, result
    text = registry_text(repo)
    assert spec_path("c") in text and spec_path("free") not in text
    assert "shipped = [\n]" in text or "shipped = []" in text
    assert text.count(spec_path("c")) == 1


# ── AC-0018: nothing under docs/lifecycle/ changes ───────────────────────────


def test_plan_and_apply_leave_docs_lifecycle_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = plant(
        tmp_path,
        queue=[
            row(spec_path("held"), parent="none"),
            row(spec_path("cooled")),
            row(spec_path("plain")),
        ],
        files={**cooled_files("held"), **cooled_files("cooled"), **spec_files("plain")},
    )
    before = lifecycle_digest(repo)
    assert len(before) == 2
    plan(repo, capsys)
    assert lifecycle_digest(repo) == before
    code, _ = apply(repo, capsys)
    assert code == 0
    assert lifecycle_digest(repo) == before


# ── AC-0019: apply order, one comment-preserving write, lock-time checks ─────


def test_apply_removes_drops_in_one_write_and_keeps_comments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = plant(
        tmp_path,
        queue=[
            row(spec_path("a")),
            row(spec_path("keep"), needs=STUCK),
            row(spec_path("b")),
        ],
        files=spec_files("a", "keep", "b"),
        comment="\n# trailing comment\n",
    )
    original = registry_text(repo)
    plan(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 2, result
    expected = original.replace(f"  {row(spec_path('a'))},\n", "").replace(
        f"  {row(spec_path('b'))},\n", ""
    )
    assert registry_text(repo) == expected
    assert "# fixture header comment" in registry_text(repo)
    assert not (repo / ".workspace-repair.lock").exists()


def test_a_plan_naming_a_spec_outside_work_and_backlog_is_refused_under_the_lock(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import tomllib

    repo = plant(
        tmp_path,
        shaping=[row(spec_path("sh"))],
        queue=[row(spec_path("q"))],
        files=spec_files("sh", "q"),
    )
    plan(repo, capsys)
    workspace = tomllib.loads(registry_text(repo))
    raw = workspace["ini-001"]["shaping_queue"]["active"][0]
    forged = {
        "operation_type": DROP,
        "entry_locator": {"ini_slug": "ini-001", "collection": "shaping_queue.active", "index": 0},
        "path": spec_path("sh"),
        "kind": "spec",
        "registry_fingerprint": WS._entry_fingerprint("ini-001", "shaping_queue.active", 0, raw),
    }
    rewrite_plan(repo, lambda data: data["automatic_operations"].append(forged))
    code, result = apply(repo, capsys)
    assert code == 0, result
    text = registry_text(repo)
    assert spec_path("sh") in text and spec_path("q") not in text
    refused = [item for item in result["per_operation"] if item.get("applied") is False]
    assert [item["path"] for item in refused] == [spec_path("sh")]
    assert refused[0]["reason"] == "entry_not_droppable"


def test_a_drop_whose_entry_changed_or_moved_since_the_plan_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("a")), row(spec_path("b"))],
        files=spec_files("a", "b"),
    )
    plan(repo, capsys)
    # The plan names the entry at index 0 by the path of the one at index 1.
    rewrite_plan(repo, lambda data: [
        op.update(path=spec_path("b")) for op in data["automatic_operations"]
        if op["entry_locator"]["index"] == 0
    ])
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    reasons = [item["reason"] for item in result["per_operation"] if not item["applied"]]
    assert reasons == ["entry_locator_mismatch"]
    assert spec_path("a") in registry_text(repo)
    assert registry_text(repo) != before  # `b` still dropped


def test_a_drop_is_refused_when_needs_are_still_non_empty_at_that_point(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    need = f'[{{type = "local", kind = "spec", path = "{spec_path("peer")}"}}]'
    repo = plant(
        tmp_path,
        queue=[row(spec_path("waiter"), needs=need)],
        files=spec_files("waiter", "peer"),
    )
    data = plan(repo, capsys)
    assert drop_paths(data) == {spec_path("waiter")}
    with (repo / spec_path("waiter")).open("a", encoding="utf-8") as handle:
        handle.write("changed\n")  # the needs operation is refused: the file changed
    code, result = apply(repo, capsys)
    assert code == 0, result
    reasons = {item["reason"] for item in result["per_operation"]}
    assert reasons == {"waiting_item_changed", "entry_has_needs"}
    assert spec_path("waiter") in registry_text(repo)


def test_a_drop_is_refused_when_the_entry_is_held_at_lock_time(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = plant(
        tmp_path,
        queue=[row(spec_path("c"), parent=BRIEF)],
        files={**cooled_files("c", parent=BRIEF), BRIEF: "# Brief\n\n- **Status:** Ready\n"},
    )
    assert drop_paths(plan(repo, capsys)) == {spec_path("c")}
    write(repo, "docs/lifecycle/c.json", record("c", spec_path("c")))  # parent removed
    before = registry_text(repo)
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [item["reason"] for item in result["per_operation"]] == ["entry_held"]
    assert registry_text(repo) == before


@pytest.mark.parametrize("kind", ["intent", "brief", "defect"])
def test_a_spec_drop_naming_another_kind_is_invalid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    repo = plant(tmp_path, queue=[row(spec_path("a"))], files=spec_files("a"))
    plan(repo, capsys)
    rewrite_plan(repo, lambda data: data["automatic_operations"][0].update(kind=kind))
    _code, result = apply(repo, capsys)
    assert result["reason"] == "plan_invalid"
    assert spec_path("a") in registry_text(repo)


# ── AC-0020: one run leaves no candidate, and a held entry drops once it can ─


def test_one_run_leaves_no_candidate_and_a_record_gaining_parent_releases_the_hold(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = plant(
        tmp_path,
        queue=[row(spec_path("held"), parent=BRIEF), row(spec_path("plain"))],
        shipped=[row(spec_path("old"), parent="none")],
        files={
            **cooled_files("held"),
            **cooled_files("old"),
            **spec_files("plain"),
            BRIEF: "# Brief\n\n- **Status:** Ready\n",
        },
    )
    first = plan(repo, capsys)
    assert drop_paths(first) == {spec_path("plain")}
    assert {f["spec_path"] for f in held(first)} == {spec_path("held"), spec_path("old")}
    code, _ = apply(repo, capsys)
    assert code == 0
    second = plan(repo, capsys)
    assert drops(second) == [] and len(held(second)) == 2
    # The record gains `parent` between the runs, as a person adds it.
    write(repo, "docs/lifecycle/held.json", record("held", spec_path("held"), BRIEF))
    third = plan(repo, capsys)
    assert drop_paths(third) == {spec_path("held")}
    assert [f["spec_path"] for f in held(third)] == [spec_path("old")]
    code, _ = apply(repo, capsys)
    assert code == 0
    assert spec_path("held") not in registry_text(repo)
    assert drops(plan(repo, capsys)) == []


# ── AC-0042: dispatch.py's output does not change across an apply ────────────


def _dispatch_cases() -> dict[str, Callable[[Path], None]]:
    def plain(root: Path) -> None:
        plant(root, queue=[row(spec_path("p"))], files=spec_files("p"))

    def absent_parent(root: Path) -> None:
        plant(
            root,
            queue=[row(spec_path("c")), row(spec_path("p"))],
            files={**cooled_files("c"), **spec_files("p")},
        )

    def held(root: Path) -> None:
        plant(
            root,
            queue=[row(spec_path("c"), parent="none"), row(spec_path("p"))],
            files={**cooled_files("c"), **spec_files("p")},
        )

    def record_has_parent(root: Path) -> None:
        plant(
            root,
            queue=[row(spec_path("c"), parent=BRIEF), row(spec_path("p"))],
            files={
                **cooled_files("c", parent=BRIEF),
                **spec_files("p"),
                BRIEF: "# Brief\n\n- **Status:** Ready\n",
            },
        )

    def shipped_and_backlog(root: Path) -> None:
        plant(
            root,
            queue=[row(spec_path("p"))],
            shipped=[row(spec_path("s"))],
            open_=[row(spec_path("b"))],
            files=spec_files("p", "b") | spec_files("s", status="Shipped"),
        )

    return {
        "plain": plain,
        "absent-parent": absent_parent,
        "held": held,
        "record-has-parent": record_has_parent,
        "shipped-and-backlog": shipped_and_backlog,
    }


@pytest.mark.parametrize("case", list(_dispatch_cases()))
def test_dispatch_output_is_byte_identical_before_and_after_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    pytest.importorskip("tomlkit")
    _dispatch_cases()[case](tmp_path)
    data = plan(tmp_path, capsys)
    assert not any(
        op["operation_type"] in ("needs-to-header", "needs-drop-cooled")
        for op in data["automatic_operations"]
    )
    before = dispatch_stdout(tmp_path, capsys)
    code, _ = apply(tmp_path, capsys)
    assert code == 0
    assert dispatch_stdout(tmp_path, capsys) == before


def test_dispatch_output_is_identical_across_a_held_entrys_second_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    plant(
        tmp_path,
        queue=[row(spec_path("c"), parent=BRIEF), row(spec_path("p"))],
        files={
            **cooled_files("c"),
            **spec_files("p"),
            BRIEF: "# Brief\n\n- **Status:** Ready\n",
        },
    )
    plan(tmp_path, capsys)
    first = dispatch_stdout(tmp_path, capsys)
    assert apply(tmp_path, capsys)[0] == 0
    assert dispatch_stdout(tmp_path, capsys) == first
    write(tmp_path, "docs/lifecycle/c.json", record("c", spec_path("c"), BRIEF))
    assert drop_paths(plan(tmp_path, capsys)) == {spec_path("c")}
    second = dispatch_stdout(tmp_path, capsys)
    assert apply(tmp_path, capsys)[0] == 0
    assert dispatch_stdout(tmp_path, capsys) == second
