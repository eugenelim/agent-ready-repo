"""Roster coverage for the drain run, its ordering, and its recovery (§ D1).

Spec: ``docs/specs/work-item-promotion-handoff`` — task T6. The terminal
disposition is the sole commit point: a crash at any effect boundary ahead
of it leaves the capture open, and a re-run drain completes the sequence
without a second artifact or a second terminal event. The crash driver
injects at the effect seams the drain already exposes — the transaction and
the disposition writer — with no new failure hook. The store-derived counts
and the run report agree member for member.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts"
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DRAIN = _load_module("_roster_promotion_drain_run", SCRIPTS_DIR / "promotion_drain.py")
KS = DRAIN.KS


class Crash(Exception):
    """The crash driver's injected failure."""


def _request(shape: str, statement: str, **extra: str) -> dict[str, Any]:
    work_item: dict[str, Any] = {
        "statement": statement,
        "shape": shape,
        "blocker": "dependency",
        "finished_state": "The item sits with its owning route.",
        "necessity_rationale": "The route decides what happens to the item.",
    }
    if shape == "question":
        work_item["answered_by"] = "docs/knowledge/reference/work-items.md"
    work_item.update(extra)
    return {
        "contract_version": "knowledge-captured-observation.v2",
        "kind": "work-item",
        "work_item": work_item,
        "project_scope": {"paths": ["docs"], "audience": "project"},
        "competency_facets": ["CQ-ROUTE"],
        "destination_hint": {
            "type": "route-suggestion",
            "path": "docs/knowledge/reference/work-items.md",
        },
        "producer": {"workflow": "work-loop", "workflow_version": "2.6.0"},
        "semantic_gate": {"name": "plan-locked", "artifact": "docs/specs/example/plan.md"},
        "provenance": {
            "sources": [
                {"path": "docs/specs/example/plan.md", "line_start": 10, "line_end": 20}
            ]
        },
        "freshness_anchor": {
            "path": "docs/specs/example/plan.md",
            "digest": {"kind": "sha256-bytes-v1", "sha256": "a" * 64, "byte_length": 100},
        },
        "observed_at": "2026-11-04T10:00:00Z",
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
    }


def _seed_store(repo: Path, shapes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """A store with a coherent committed topic map and one capture per name.

    `shapes` maps a name to the kwargs of `_request` for that capture; the
    returned dict maps the name to its capture receipt."""
    (repo / "docs" / "knowledge" / "topics").mkdir(parents=True)
    # The transaction resolves the configured parent strictly, so the
    # captured-item destination must exist in the worktree.
    (repo / "docs" / "product" / "captured").mkdir(parents=True)
    # The store's own rebuild writes the canonical empty map, so the
    # disposition writer's coherence checks pass.
    KS.rebuild_topic_map(repo)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "-m", "map"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return {
        name: KS.seed_previously_admitted_capture(repo, _request(**kwargs))
        for name, kwargs in shapes.items()
    }


def _confirm_all(_offer: dict[str, Any], _proposal: dict[str, Any]) -> dict[str, Any]:
    return {"confirm": True}


def _dispositions_for(repo: Path, capture_id: str) -> list[dict[str, Any]]:
    return [
        item
        for item in DRAIN.store_terminal_dispositions(repo)
        if item["capture_id"] == capture_id
    ]


def _captured_files(repo: Path) -> list[str]:
    captured = repo / "docs" / "product" / "captured"
    return sorted(path.name for path in captured.iterdir()) if captured.exists() else []


ARTIFACT_STATEMENT = "The drain leaves routed items unplaced"


def _artifact_name(repo: Path, capture_id: str) -> str:
    translated = "".join(
        character if character.isalnum() else "-"
        for character in ARTIFACT_STATEMENT.lower()
    )
    slug = "-".join(part for part in translated.split("-") if part)[:60]
    return f"{slug}-{capture_id[-12:]}.md"


@pytest.mark.parametrize(
    "stage",
    ["before_transaction", "inside_transaction", "after_transaction", "after_disposition"],
)
def test_crash_at_each_effect_boundary_then_re_drive_completes_once(
    git_repo: Path, stage: str
) -> None:
    repo = git_repo.parent / f"{git_repo.name}-{stage}"
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    seeded = _seed_store(
        repo,
        {
            "routed": {
                "shape": "defect",
                "statement": "The drain leaves routed items unplaced",
                "observed": "The drain reports the item as unplaced today.",
                "intended": "The drain reports the item at its owner.",
            }
        },
    )
    capture_id = seeded["routed"]["capture_id"]
    artifact = repo / "docs" / "product" / "captured" / _artifact_name(repo, capture_id)

    def partial_then_raise(confined: Path) -> None:
        # The materializer's own failure mode: partial bytes in the `.tmp`
        # file the atomic replace never reaches.
        confined.with_name(f"{confined.name}.tmp").write_bytes(b"partial")
        raise Crash(stage)

    def crashing_transact(offer: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        if stage == "before_transaction":
            raise Crash(stage)
        if stage == "inside_transaction":
            return DRAIN.transact_route(
                repo, offer, decision, materialize=partial_then_raise, dispatch_processor=lambda: None
            )
        result = DRAIN.transact_route(repo, offer, decision, dispatch_processor=lambda: None)
        if stage == "after_transaction":
            raise Crash(stage)
        return result

    def crashing_write(cid: str, disposition: str, reason_code: str) -> Any:
        result = KS.write_terminal_disposition(
            repo, cid, disposition, reason_code=reason_code, recorded_at="2026-11-04T12:00:00Z"
        )
        if stage == "after_disposition":
            raise Crash(stage)
        return result

    if stage == "inside_transaction":
        # A crash inside the transaction is the transaction's own rollback:
        # the drain survives it, holds the item, and nothing committed.
        first = DRAIN.drain(
            repo,
            confirmer=_confirm_all,
            transact=crashing_transact,
            write_disposition=crashing_write,
            recorded_at="2026-11-04T12:00:00Z",
        )
        assert first["counts"] == {"routed": 0, "held": 1, "closed": 0}
    else:
        with pytest.raises(Crash):
            DRAIN.drain(
                repo,
                confirmer=_confirm_all,
                transact=crashing_transact,
                write_disposition=crashing_write,
                recorded_at="2026-11-04T12:00:00Z",
            )

    if stage == "after_disposition":
        # The sequence completed before the crash: one terminal event, one
        # artifact.
        assert len(_dispositions_for(repo, capture_id)) == 1
        assert artifact.exists()
    else:
        # A crash anywhere ahead of the disposition leaves the capture open.
        assert _dispositions_for(repo, capture_id) == []
        if stage in ("before_transaction", "inside_transaction"):
            # Either nothing happened, or the transaction's own rollback
            # removed the partial artifact.
            assert _captured_files(repo) == [], _captured_files(repo)

    # A clean re-drive completes the sequence exactly once — or, when the
    # crash landed after the disposition, finds it already complete and
    # performs no further effect.
    report = DRAIN.drain(
        repo, confirmer=_confirm_all, dispatch_processor=lambda: None, recorded_at="2026-11-04T12:00:00Z"
    )

    expected_counts = (
        {"routed": 0, "held": 0, "closed": 0}
        if stage == "after_disposition"
        else {"routed": 1, "held": 0, "closed": 0}
    )
    assert report["counts"] == expected_counts
    assert len(_dispositions_for(repo, capture_id)) == 1
    assert _captured_files(repo) == [_artifact_name(repo, capture_id)]
    assert "The drain leaves routed items unplaced" in artifact.read_text(encoding="utf-8")


def test_closure_path_crash_and_identical_disposition_no_op(git_repo: Path) -> None:
    seeded = _seed_store(
        git_repo,
        {"closed": {"shape": "defect", "statement": "The overtaken defect was fixed elsewhere already", "observed": "The drain reports the deviation is gone.", "intended": "The drain reports the item at its owner."}},
    )
    capture_id = seeded["closed"]["capture_id"]

    def closer(_offer: dict[str, Any], _proposal: dict[str, Any]) -> dict[str, Any]:
        return {
            "close": {
                "ground": "overtaken",
                "test_passes": True,
                "evidence": {"what": "the deviation no longer shows"},
            }
        }

    def crashing_write(cid: str, disposition: str, reason_code: str) -> Any:
        KS.write_terminal_disposition(
            git_repo, cid, disposition, reason_code=reason_code, recorded_at="2026-11-04T12:00:00Z"
        )
        raise Crash("after_disposition")

    with pytest.raises(Crash):
        DRAIN.drain(
            git_repo,
            confirmer=closer,
            write_disposition=crashing_write,
            recorded_at="2026-11-04T12:00:00Z",
        )
    assert len(_dispositions_for(git_repo, capture_id)) == 1

    # Re-driving: the capture is closed, so the drain offers it no second
    # disposition (AC-0012), and the store's identical-disposition no-op
    # holds — writing the same disposition again changes nothing.
    report = DRAIN.drain(git_repo, confirmer=closer, recorded_at="2026-11-04T12:00:00Z")
    assert report["counts"] == {"routed": 0, "held": 0, "closed": 0}
    KS.write_terminal_disposition(
        git_repo,
        capture_id,
        "rejected",
        reason_code="closed_overtaken",
        recorded_at="2026-11-04T12:00:00Z",
    )
    assert len(_dispositions_for(git_repo, capture_id)) == 1


def test_store_derived_counts_agree_with_the_run_report(git_repo: Path) -> None:
    seeded = _seed_store(
        git_repo,
        {
            "routed": {
                "shape": "defect",
                "statement": "The drain leaves routed items unplaced",
                "observed": "The drain reports the item as unplaced today.",
                "intended": "The drain reports the item at its owner.",
            },
            "held": {
                "shape": "decision",
                "statement": "The governance sibling should own routing decisions",
                "significance": ["architecturally-significant"],
            },
            "closed": {
                "shape": "defect",
                "statement": "The overtaken defect was fixed elsewhere already",
                "observed": "The drain reports the item as unplaced today.",
                "intended": "The drain reports the item at its owner.",
            },
        },
    )
    by_id = {seeded[key]["capture_id"]: key for key in ("routed", "held", "closed")}

    def operator(offer: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
        name = by_id[offer["capture_id"]]
        if name == "routed":
            return {"confirm": True}
        if name == "closed":
            return {
                "close": {
                    "ground": "overtaken",
                    "test_passes": True,
                    "evidence": {"what": "the deviation no longer shows"},
                }
            }
        return {}

    report = DRAIN.drain(git_repo, confirmer=operator, dispatch_processor=lambda: None, recorded_at="2026-11-04T12:00:00Z")

    assert report["counts"] == {"routed": 1, "held": 1, "closed": 1}
    dispositions = DRAIN.store_terminal_dispositions(git_repo)
    assert {
        item["capture_id"] for item in dispositions if item["disposition"] == "routed"
    } == {seeded["routed"]["capture_id"]}
    assert {
        item["capture_id"]
        for item in dispositions
        if item["disposition"] in ("rejected", "superseded")
    } == {seeded["closed"]["capture_id"]}
    report_actions = {item["capture_id"]: item["action"] for item in report["items"]}
    assert report_actions[seeded["routed"]["capture_id"]] == "routed"
    assert report_actions[seeded["closed"]["capture_id"]] == "closed"
    assert report_actions[seeded["held"]["capture_id"]] == "held"
    # The held item is the one capture still open in the store.
    assert {
        capture["capture_id"] for capture in DRAIN.read_open_captures(git_repo)["captures"]
    } == {seeded["held"]["capture_id"]}


def test_materialize_never_writes_through_a_planted_tmp_symlink(git_repo: Path) -> None:
    """The temp file sits beside the artifact under a predictable name, so a
    committed symlink there must neither be written through nor block the
    route: the target file outside the repository stays untouched."""
    repo = git_repo.parent / f"{git_repo.name}-symlink"
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    seeded = _seed_store(
        repo,
        {
            "routed": {
                "shape": "defect",
                "statement": ARTIFACT_STATEMENT,
                "observed": "The drain reports the item as unplaced today.",
                "intended": "The drain reports the item at its owner.",
            }
        },
    )
    capture_id = seeded["routed"]["capture_id"]
    outside = git_repo.parent / f"{git_repo.name}-outside.txt"
    outside.write_text("untouched")
    planted = repo / "docs" / "product" / "captured" / f"{_artifact_name(repo, capture_id)}.tmp"
    planted.symlink_to(outside)

    DRAIN.drain(repo, confirmer=_confirm_all, dispatch_processor=lambda: None, recorded_at="2026-11-04T12:00:00Z")

    assert outside.read_text() == "untouched"
    artifact = repo / "docs" / "product" / "captured" / _artifact_name(repo, capture_id)
    assert not artifact.is_symlink()
    assert artifact.exists() and artifact.read_bytes() != b"untouched"


def test_no_dispatch_wired_holds_routable_items_before_any_effect(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # § D1's dispatch rule (AC-0025): a drain invoked with no dispatch
    # wired — no `transact` override, no `dispatch_processor` — holds every
    # confirmed route ahead of any transaction effect: no lock taken, no
    # artifact materialized, no terminal disposition, on both route shapes.
    _seed_store(
        git_repo,
        {
            "defect": {
                "shape": "defect",
                "statement": "A ready defect needs a dispatch to route",
                "observed": "The drain holds the item without a dispatch.",
                "intended": "The route commits only through a real dispatch.",
            },
            "question": {
                "shape": "question",
                "statement": "A classified question needs a dispatch to route",
            },
        },
    )
    loader_calls: list[str] = []

    def spying_loader() -> Any:
        loader_calls.append("transaction-runner")
        raise AssertionError("the no-dispatch hold precedes the transaction runner")

    monkeypatch.setattr(DRAIN, "_load_intake_transaction", spying_loader)

    report = DRAIN.drain(
        git_repo,
        confirmer=_confirm_all,
        classify=lambda message: "spec",
        recorded_at="2026-11-05T10:00:00Z",
    )

    assert report["counts"] == {"routed": 0, "held": 2, "closed": 0}, report["items"]
    assert [item["reason"] for item in report["items"]] == ["no-dispatch-wired", "no-dispatch-wired"]
    # The hold precedes every transaction effect (AC-0025): the transaction
    # runner — through which alone the workspace lock is taken — was never
    # reached, no captured-item artifact exists, and no terminal event was
    # recorded for either capture.
    assert loader_calls == []
    assert _captured_files(git_repo) == []
    assert DRAIN.store_terminal_dispositions(git_repo) == []
    assert not (git_repo / ".workspace-repair.lock").exists()


def test_wired_dispatch_routes_both_shapes(git_repo: Path) -> None:
    # The same drain with a real dispatch wired routes both shapes (AC-0025
    # names the hold's trigger: no dispatch; a wired dispatch routes).
    _seed_store(
        git_repo,
        {
            "defect": {
                "shape": "defect",
                "statement": "A ready defect routes through a dispatch",
                "observed": "The drain routes the item with a dispatch.",
                "intended": "The route commits through the wired dispatch.",
            },
            "question": {
                "shape": "question",
                "statement": "A classified question routes through a dispatch",
            },
        },
    )

    report = DRAIN.drain(
        git_repo,
        confirmer=_confirm_all,
        classify=lambda message: "spec",
        dispatch_processor=lambda: None,
        recorded_at="2026-11-05T10:00:00Z",
    )

    assert report["counts"] == {"routed": 2, "held": 0, "closed": 0}, report["items"]
    assert len(_captured_files(git_repo)) == 1
    assert len(DRAIN.store_terminal_dispositions(git_repo)) == 2
