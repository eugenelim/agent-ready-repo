"""Construction tests for the `tracker-entry-drop` repair step.

Spec: docs/specs/tracker-origin-registration-stop/spec.md (AC-0010, AC-0030,
AC-0011, AC-0027, AC-0012, AC-0013, AC-0014, AC-0015).
Verification mode: TDD.

Each test plants a repository under ``tmp_path`` and runs ``repair-plan`` and
``repair-apply`` in process through the script's ``main``; ``dispatch.py`` is
called in process the same way.
"""
from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Callable

import pytest

_SKILLS = Path(__file__).resolve().parents[3] / ".apm/skills"


def _load(name: str, path: Path) -> ModuleType:
    """Load a module by file path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WS = _load(
    "workspace_status_tracker_entry_drop", _SKILLS / "workspace-status/scripts/workspace_status.py"
)
DISPATCH = _load("dispatch_tracker_entry_drop", _SKILLS / "work-loop/scripts/dispatch.py")
REFRESH = _load("work_intake_refresh_tracker_entry_drop", _SKILLS / "work-intake/scripts/refresh.py")
ROUTER = _load("work_intake_router_tracker_entry_drop", _SKILLS / "work-intake/scripts/intake_router.py")

PLAN = ".workspace-repair-plan.json"
DROP = "tracker-entry-drop"
REF = "example-service://ABC-1"
# A need the repair refuses (a brief that does not exist) keeps `needs` non-empty.
STUCK = '[{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]'
PROFILE = {"id": "example-profile", "version": "1"}
BRIEFS = "docs/product/briefs"
BRIEF = f"{BRIEFS}/parent.md"

# kind -> (path, collection, header line)
KINDS: dict[str, tuple[str, str, str]] = {
    "intent": ("docs/product/intents/t-intent.md", "shaping_queue.backlog", "# Intent: t-intent"),
    "brief": (f"{BRIEFS}/t-brief.md", "brief_queue.draft", "# Brief: t-brief"),
    "spec": ("docs/specs/t-spec/spec.md", "work.queue", "# Spec: t-spec"),
}
SECTIONS = {
    "shaping_queue.backlog": ("shaping_queue", "backlog"),
    "brief_queue.draft": ("brief_queue", "draft"),
    "work.queue": ("work", "queue"),
    "work.shipped": ("work", "shipped"),
}


def record_block(
    *, ref: str = REF, profile: dict[str, str] | None = None, note: str = ""
) -> str:
    """A closed source-authority record, with a profile table when given."""
    table = (
        f'\n[tracker_profile]\nid = "{profile["id"]}"\nversion = "{profile["version"]}"\n'
        if profile
        else ""
    )
    return (
        "```toml source-authority\n"
        'contract_version = "source-authority.v1"\n'
        'mode = "tracker-origin"\n'
        f'source_ref = "{ref}"\n'
        f'source_revision = "r1"\n{table}\n[owned_fields]\n```\n{note}'
    )


def artifact(
    kind: str, *, status: str = "Draft", block: str | None = None, ref: str = REF,
    profile: dict[str, str] | None = None,
) -> str:
    """An artifact whose record sits between prose that must survive the write."""
    title = KINDS[kind][2]
    body = record_block(ref=ref, profile=profile) if block is None else block
    return (
        f"{title}\n\n- **Status:** {status}\n- **Slug:** {title.split(': ')[1]}\n\n"
        f"Before the record.\n\n{body}\n\nAfter the record.\n\n"
    )


def tracker_row(
    path: str | None,
    kind: str,
    *,
    profile: dict[str, str] | None = PROFILE,
    ref: str = REF,
    needs: str = "[]",
    parent: str | None = None,
) -> str:
    """One tracker-origin entry as an inline table."""
    pieces = ['mode = "tracker-origin"', f'ref = "{ref}"', 'revision = "r1"']
    if parent is not None:
        pieces.append(f'parent = "{parent}"')
    if profile is not None:
        pieces.append(
            f'tracker_profile = {{id = "{profile["id"]}", version = "{profile["version"]}"}}'
        )
    head = f'path = "{path}", ' if path is not None else (
        'surface_role = "delivery-brief", locator = {kind = "external", value = "example-service://ABC-1"}, '
    )
    return f'{{{head}kind = "{kind}", source = {{{", ".join(pieces)}}}, summary = "fixture", needs = {needs}}}'


def repo_spec_row(path: str, needs: str = "[]") -> str:
    return (
        f'{{path = "{path}", kind = "spec", source = {{mode = "repo-origin"}}, '
        f'summary = "fixture", needs = {needs}}}'
    )


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plant(root: Path, rows: dict[str, list[str]], files: dict[str, str] | None = None) -> Path:
    """Write a registry holding ``rows`` per collection, and ``files``."""
    sections: dict[str, dict[str, list[str]]] = {}
    for collection, values in rows.items():
        section, name = SECTIONS[collection]
        sections.setdefault(section, {})[name] = values
    text = '# fixture header comment\n[backlog]\nopen = []\nclosed = []\n\n'
    text += '["ini-001"]\nname = "Fixture"\nstatus = "active"\nmilestone = "m1"\n\n'
    for section in ("work", "shaping_queue", "brief_queue"):
        names = sections.get(section, {})
        if not names:
            continue
        text += f'["ini-001".{section}]\n'
        for name, values in names.items():
            text += f"{name} = [\n" + "".join(f"  {v},  # keep\n" for v in values) + "]\n"
        text += "\n"
    write(root, "workspace.toml", text)
    write(root, "AGENTS.md", "# Agents\n")
    for rel, body in (files or {}).items():
        write(root, rel, body)
    return root


def lifecycle(slug: str, locator: str, parent: str | None = None) -> str:
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


def tracker_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in data["manual_findings"] if f.get("finding_type") == 7]


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


def dispatch_stdout(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    capsys.readouterr()
    DISPATCH.main(["--root", str(root)])
    return capsys.readouterr().out


class _RecordingResolver:
    """Records each (id, version) asked for an acquisition-capable processor."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, str]] = []

    def resolve(self, profile_id: str, profile_version: str, capability: str | None = None) -> Any:
        if capability == "acquire":
            self.asked.append((profile_id, profile_version))
            raise ValueError("stop before acquisition")
        return SimpleNamespace(name="recording-processor")


def assert_refresh_resolves_former_profile(root: Path, path: str, kind: str) -> None:
    """Refresh on a migrated artifact asks the registry for the entry's former profile."""
    resolver = _RecordingResolver()
    signals = ROUTER.RoutingSignals(
        action="refresh", artifact=path, artifact_kind=kind, authority_mode="tracker-origin"
    )
    request = SimpleNamespace(
        artifact_path=path,
        artifact_kind=kind,
        lifecycle="Approved",
        authority_mode="tracker-origin",
        current_revision="r1",
        compared_revision="r2",
        profile_id=PROFILE["id"],
        profile_version=PROFILE["version"],
    )
    result = ROUTER.invoke_refresh(signals, resolver, request, root)
    assert result.remediation != "add-record-tracker-profile", result
    assert resolver.asked == [(PROFILE["id"], PROFILE["version"])]


def assert_dispatch_unchanged_by_apply(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Run ``repair-apply --yes`` and compare ``dispatch.py`` output before and after."""
    before = dispatch_stdout(root, capsys)
    code, result = apply(root, capsys)
    assert code == 0, result
    assert dispatch_stdout(root, capsys) == before


def unusable_lifecycle(root: Path, outside: Path) -> None:
    """Make ``docs/lifecycle/`` a link out of the root, which cooling cannot trust."""
    outside.mkdir()
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "lifecycle").symlink_to(outside, target_is_directory=True)


def matched_tree(root: Path, kind: str, *, profile: dict[str, str] | None = None) -> Path:
    path, collection, _ = KINDS[kind]
    # A spec is judged from its headers either way, once Approved.
    files = {path: artifact(kind, status="Approved" if kind == "spec" else "Draft", profile=profile)}
    if kind == "spec":
        files["docs/specs/t-spec/plan.md"] = "# Plan\n\n- **Status:** Approved\n"
    return plant(root, {collection: [tracker_row(path, kind)]}, files)


# ── AC-0010, AC-0012, AC-0014, AC-0015: matched entries ──────────────────────


@pytest.mark.parametrize("kind", ["intent", "brief", "spec"])
def test_a_matched_entry_gets_an_operation_and_apply_moves_its_profile(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    pytest.importorskip("tomlkit")
    path, collection, _ = KINDS[kind]
    repo = matched_tree(tmp_path, kind)
    before_text = (repo / path).read_text(encoding="utf-8")
    data = plan(repo, capsys)
    [op] = drops(data)
    assert tracker_items(data) == [] and held(data) == []
    assert op["path"] == path and op["kind"] == kind
    assert op["entry_locator"] == {
        "ini_slug": "ini-001", "collection": collection, "index": 0,
    }
    assert op["profile"] == PROFILE
    assert op["artifact_sha256"] == hashlib.sha256(before_text.encode()).hexdigest()
    assert len(op["registry_fingerprint"]) == 64
    dispatch_before = dispatch_stdout(repo, capsys)

    code, result = apply(repo, capsys)
    assert code == 0, result
    assert result["operations_applied"] == 1
    # The entry left in the same write that kept the comment on the other rows.
    assert path not in registry_text(repo)
    assert "# fixture header comment" in registry_text(repo)
    after_text = (repo / path).read_text(encoding="utf-8")
    old = REFRESH.parse_source_authority(before_text)
    new = REFRESH.parse_source_authority(after_text)
    assert new == dataclasses.replace(old, tracker_profile=PROFILE)
    assert after_text.count("```toml source-authority") == 1
    # Every byte outside the record is unchanged.
    start = before_text.index("```toml source-authority")
    end = before_text.index("```\n", start + 3) + 4
    assert after_text.startswith(before_text[:start])
    assert after_text.endswith(before_text[end:])
    # AC-0014: nothing left to plan, and refresh's parser reads the profile.
    again = plan(repo, capsys)
    assert drops(again) == [] and tracker_items(again) == []
    # AC-0014: refresh on the migrated artifact resolves the entry's former profile.
    assert_refresh_resolves_former_profile(repo, path, kind)
    # AC-0015
    assert dispatch_stdout(repo, capsys) == dispatch_before


def test_a_record_already_holding_an_equal_table_gets_an_operation_with_no_profile(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = matched_tree(tmp_path, "brief", profile=PROFILE)
    path = KINDS["brief"][0]
    before = (repo / path).read_bytes()
    [op] = drops(plan(repo, capsys))
    assert op["profile"] is None
    dispatch_before = dispatch_stdout(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 1, result
    assert dispatch_stdout(repo, capsys) == dispatch_before
    assert (repo / path).read_bytes() == before
    assert path not in registry_text(repo)
    assert_refresh_resolves_former_profile(repo, path, "brief")


# ── AC-0011: manual items ────────────────────────────────────────────────────


def _unmatched(tmp_path: Path, reason: str) -> tuple[Path, str | None]:
    """A tree with one tracker-origin brief entry that fails ``reason``; returns its path."""
    tmp_path = tmp_path / "repo"
    path = KINDS["brief"][0]
    row = tracker_row(path, "brief")
    files = {path: artifact("brief")}
    collection = "brief_queue.draft"
    if reason == "cooling-state-unavailable":
        path, collection = KINDS["spec"][0], "work.queue"
        row = tracker_row(path, "spec")
        files = {
            path: artifact("spec", status="Approved"),
            "docs/specs/t-spec/plan.md": "# Plan\n\n- **Status:** Approved\n",
        }
    elif reason == "path-missing":
        row = tracker_row(None, "brief")
        files = {}
        path = None  # type: ignore[assignment]
    elif reason == "artifact-missing":
        files = {}
    elif reason == "record-missing-or-invalid":
        files = {path: artifact("brief", block="no record here")}
    elif reason == "ref-mismatch":
        files = {path: artifact("brief", ref="example-service://OTHER-2")}
    elif reason == "entry-profile-invalid":
        row = tracker_row(path, "brief", profile=None)
    elif reason == "profile-mismatch":
        files = {path: artifact("brief", profile={"id": "other", "version": "9"})}
    elif reason == "needs-present":
        row = tracker_row(
            path, "brief",
            needs='[{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]',
        )
    elif reason == "other-write-pending":
        row = tracker_row(path, "brief") + ",\n  " + tracker_row(path, "brief")
    plant(tmp_path, {collection: [row]}, files)
    if reason == "cooling-state-unavailable":
        unusable_lifecycle(tmp_path, tmp_path.parent / "outside")
    return tmp_path, path


@pytest.mark.parametrize(
    "reason",
    [
        "artifact-missing",
        "record-missing-or-invalid",
        "ref-mismatch",
        "entry-profile-invalid",
        "profile-mismatch",
        "needs-present",
        "other-write-pending",
        "cooling-state-unavailable",
    ],
)
def test_an_unmatched_entry_gets_one_manual_item_with_the_first_failing_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reason: str
) -> None:
    repo, path = _unmatched(tmp_path, reason)
    data = plan(repo, capsys)
    assert drops(data) == []
    items = tracker_items(data)
    # One manual item per planted entry: the pending-write case plants two.
    planted = 2 if reason == "other-write-pending" else 1
    assert [item["reason"] for item in items] == [reason] * planted
    expected = "work.queue" if reason == "cooling-state-unavailable" else "brief_queue.draft"
    for item in items:
        assert item["spec_path"] == (path or "")
        assert item["entry_locator"]["collection"] == expected


def test_an_entry_with_no_path_is_named_by_its_locator(tmp_path: Path) -> None:
    # The engine's canonical check refuses a pathless entry before `repair-plan`
    # reaches this step, so the planner function is called directly.
    repo, _ = _unmatched(tmp_path, "path-missing")
    WS._bind_engine()
    ops, manual, queue_keys = WS._build_tracker_drop_operations(
        repo, (repo / "workspace.toml").read_bytes(), []
    )
    assert ops == [] and queue_keys == frozenset()
    [item] = manual
    assert item["reason"] == "path-missing" and item["spec_path"] == ""
    assert item["entry_locator"] == {
        "ini_slug": "ini-001", "collection": "brief_queue.draft", "index": 0,
    }


def _entry_finding_tree(root: Path) -> Path:
    """A tracker-origin brief whose status disagrees with its collection.

    The engine reports ``impossible_transition`` for it, and no other entry
    holds an operation that would move the dispatch output.
    """
    path = KINDS["brief"][0]
    return plant(
        root,
        {"brief_queue.draft": [tracker_row(path, "brief")]},
        {path: artifact("brief", status="Ready")},
    )


def test_an_entry_with_an_entry_level_finding_gets_the_entry_finding_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _entry_finding_tree(tmp_path)
    data = plan(repo, capsys)
    assert drops(data) == []
    assert [item["reason"] for item in tracker_items(data)] == ["entry-finding"]


# ── AC-0030: queue operations ────────────────────────────────────────────────


def test_an_archived_tracker_spec_in_the_queue_gets_no_queue_remove(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    tracked, plain = KINDS["spec"][0], "docs/specs/plain/spec.md"
    repo = plant(
        tmp_path,
        {"work.queue": [tracker_row(tracked, "spec"), repo_spec_row(plain, STUCK)]},
        {
            tracked: artifact("spec", status="Archived"),
            "docs/specs/t-spec/plan.md": "# Plan\n\n- **Status:** Approved\n",
            plain: "# Spec: plain\n\n- **Status:** Archived\n- **Brief:** none\n",
            "docs/specs/plain/plan.md": "# Plan\n\n- **Status:** Approved\n",
        },
    )
    data = plan(repo, capsys)
    assert [op["path"] for op in drops(data)] == [tracked]
    # Every other entry keeps the operations it holds at the base.
    assert queue_ops(data) and all(op["spec_path"] != tracked for op in queue_ops(data))
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert tracked not in registry_text(repo)
    assert "tracker_profile" in (repo / tracked).read_text(encoding="utf-8")
    assert_refresh_resolves_former_profile(repo, tracked, "spec")


def test_dispatch_output_differs_only_by_the_archived_spec_blocked_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Alone in the queue: another entry's own queue-remove would move the output.
    pytest.importorskip("tomlkit")
    tracked = KINDS["spec"][0]
    repo = plant(
        tmp_path,
        {"work.queue": [tracker_row(tracked, "spec")]},
        {
            tracked: artifact("spec", status="Archived"),
            "docs/specs/t-spec/plan.md": "# Plan\n\n- **Status:** Approved\n",
        },
    )
    assert [op["path"] for op in drops(plan(repo, capsys))] == [tracked]
    before = json.loads(dispatch_stdout(repo, capsys))
    code, result = apply(repo, capsys)
    assert code == 0, result
    after = json.loads(dispatch_stdout(repo, capsys))
    # dispatch.py lists an Archived spec as blocked only while a queue entry names
    # it, so the one allowed difference is that item leaving the blocked list.
    [archived] = [item for item in before["blocked"] if item["path"] == tracked]
    assert "unapproved_spec" in [finding["code"] for finding in archived["findings"]]
    before["blocked"] = [item for item in before["blocked"] if item is not archived]
    assert after == before
    assert tracked not in registry_text(repo)


# ── AC-0027: held entries ────────────────────────────────────────────────────


def test_a_held_entry_gets_the_held_item_until_its_record_gains_parent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    path = KINDS["spec"][0]
    repo = plant(
        tmp_path,
        {"work.queue": [tracker_row(path, "spec", parent=BRIEF)]},
        {
            path: artifact("spec", status="Shipped"),
            "docs/specs/t-spec/plan.md": "# Plan\n\n- **Status:** Done\n",
            BRIEF: "# Brief: parent\n\n- **Status:** Ready\n",
            "docs/lifecycle/t-spec.json": lifecycle("t-spec", path),
        },
    )
    first = plan(repo, capsys)
    assert drops(first) == [] and tracker_items(first) == []
    [item] = held(first)
    assert item["spec_path"] == path
    assert item["record_path"] == "docs/lifecycle/t-spec.json"
    assert item["parent"] == BRIEF
    before = dispatch_stdout(repo, capsys)
    code, result = apply(repo, capsys)
    assert code == 0 and result["operations_applied"] == 0, result
    assert path in registry_text(repo)
    assert dispatch_stdout(repo, capsys) == before

    write(repo, "docs/lifecycle/t-spec.json", lifecycle("t-spec", path, BRIEF))
    second = plan(repo, capsys)
    assert held(second) == []
    assert [op["path"] for op in drops(second)] == [path]
    assert_dispatch_unchanged_by_apply(repo, capsys)
    assert path not in registry_text(repo)
    assert_refresh_resolves_former_profile(repo, path, "spec")


# ── AC-0013: refusals under the lock ─────────────────────────────────────────


def test_apply_refuses_an_operation_whose_fingerprint_no_longer_matches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = matched_tree(tmp_path, "intent")
    path = KINDS["intent"][0]
    before = (repo / path).read_bytes()
    registry = registry_text(repo)
    plan(repo, capsys)
    rewrite_plan(repo, lambda d: [
        op.update(registry_fingerprint="0" * 64) for op in d["automatic_operations"]
    ])
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["entry_locator_mismatch"]
    assert (repo / path).read_bytes() == before and registry_text(repo) == registry


def test_apply_refuses_an_operation_whose_artifact_bytes_changed_since_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = matched_tree(tmp_path, "intent")
    path = KINDS["intent"][0]
    registry = registry_text(repo)
    plan(repo, capsys)
    with (repo / path).open("a", encoding="utf-8") as handle:
        handle.write("edited after the plan\n")
    changed = (repo / path).read_bytes()
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["artifact_changed"]
    assert (repo / path).read_bytes() == changed and registry_text(repo) == registry


def test_apply_refuses_an_operation_whose_entry_is_no_longer_matched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = matched_tree(tmp_path, "intent")
    path = KINDS["intent"][0]
    registry = registry_text(repo)
    plan(repo, capsys)
    # The profile the plan would write no longer equals what the entry derives.
    rewrite_plan(repo, lambda d: [
        op.update(profile={"id": "forged", "version": "2"}) for op in d["automatic_operations"]
    ])
    before = (repo / path).read_bytes()
    code, result = apply(repo, capsys)
    assert code == 0, result
    assert [i["reason"] for i in result["per_operation"]] == ["entry_not_matched"]
    assert (repo / path).read_bytes() == before and registry_text(repo) == registry


# ── AC-0015: dispatch identity on each planted tree ──────────────────────────


@pytest.mark.parametrize(
    "reason",
    [
        "artifact-missing",
        "record-missing-or-invalid",
        "ref-mismatch",
        "entry-profile-invalid",
        "profile-mismatch",
        "needs-present",
        "other-write-pending",
        "cooling-state-unavailable",
    ],
)
def test_dispatch_output_is_identical_across_apply_on_unmatched_trees(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reason: str
) -> None:
    pytest.importorskip("tomlkit")
    repo, _ = _unmatched(tmp_path, reason)
    plan(repo, capsys)
    assert_dispatch_unchanged_by_apply(repo, capsys)


def test_dispatch_output_is_identical_across_apply_on_a_pathless_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # `repair-plan` cannot reach a pathless entry, so no plan exists to apply and
    # `repair-apply` refuses; the output must still not move.
    pytest.importorskip("tomlkit")
    repo, _ = _unmatched(tmp_path, "path-missing")
    before = dispatch_stdout(repo, capsys)
    apply(repo, capsys)
    assert dispatch_stdout(repo, capsys) == before


def test_dispatch_output_is_identical_across_apply_on_an_entry_finding_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("tomlkit")
    repo = _entry_finding_tree(tmp_path)
    plan(repo, capsys)
    assert_dispatch_unchanged_by_apply(repo, capsys)


# ── AC-0013: apply refusals for state that changes after the plan ────────────


def _planned_spec(tmp_path: Path, capsys: pytest.CaptureFixture[str], *, parent: str | None = None):
    """A matched tracker-origin spec in ``work.queue``, planned; returns repo, path, bytes."""
    pytest.importorskip("tomlkit")
    path = KINDS["spec"][0]
    repo = plant(
        tmp_path / "repo",
        {"work.queue": [tracker_row(path, "spec", parent=parent)]},
        {
            path: artifact("spec", status="Approved").replace(
                "- **Status:** Approved\n", f"- **Status:** Approved\n- **Brief:** {BRIEF}\n"
            ) if parent else artifact("spec", status="Approved"),
            "docs/specs/t-spec/plan.md": "# Plan\n\n- **Status:** Approved\n",
            BRIEF: "# Brief: parent\n\n- **Status:** Ready\n",
        },
    )
    assert [op["path"] for op in drops(plan(repo, capsys))] == [path]
    return repo, path, (repo / path).read_bytes()


def _assert_refused(
    repo: Path, path: str, artifact_bytes: bytes, registry: str, result: dict[str, Any], reason: str
) -> None:
    assert [item["reason"] for item in result["per_operation"]] == [reason]
    assert (repo / path).read_bytes() == artifact_bytes
    assert registry_text(repo) == registry


def test_apply_refuses_an_entry_held_after_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, path, before = _planned_spec(tmp_path, capsys, parent=BRIEF)
    registry = registry_text(repo)
    write(repo, "docs/lifecycle/t-spec.json", lifecycle("t-spec", path))
    code, result = apply(repo, capsys)
    assert code == 0, result
    _assert_refused(repo, path, before, registry, result, "entry_held")


def test_apply_refuses_when_cooling_state_becomes_unreadable_after_the_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, path, before = _planned_spec(tmp_path, capsys)
    registry = registry_text(repo)
    unusable_lifecycle(repo, tmp_path / "outside")
    code, result = apply(repo, capsys)
    assert code == 0, result
    _assert_refused(repo, path, before, registry, result, "cooling_state_unavailable")


def test_apply_refuses_a_record_that_cannot_take_the_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, path, before = _planned_spec(tmp_path, capsys)
    registry = registry_text(repo)
    real = WS._load_refresh_module()

    class DropsTheTable:
        """The refresh module, whose renderer loses the table it was asked to add."""

        def __getattr__(self, name: str) -> Any:
            return getattr(real, name)

        @staticmethod
        def render_source_authority(authority: Any) -> str:
            return real.render_source_authority(dataclasses.replace(authority, tracker_profile=None))

    monkeypatch.setattr(WS, "_load_refresh_module", lambda: DropsTheTable())
    code, result = apply(repo, capsys)
    assert code == 0, result
    _assert_refused(repo, path, before, registry, result, "record_not_writable")


def test_apply_refuses_when_the_artifact_cannot_be_replaced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, path, before = _planned_spec(tmp_path, capsys)
    registry = registry_text(repo)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise OSError("injected")

    monkeypatch.setattr(WS, "_replace_waiting_file", fail)
    code, result = apply(repo, capsys)
    assert code == 0, result
    _assert_refused(repo, path, before, registry, result, "artifact_write_failed")
