"""Roster coverage for the review-sustained repair round (T9–T12).

Spec: ``docs/specs/work-item-promotion-handoff`` — repair tasks. T9: the
route transaction is collision-safe and its rollback never deletes a
complete artifact. T10: one bad record never aborts the whole drain. T11:
a materialized captured-item file parses under the destination owner's own
grammar. T12: a closure's evidence rides the run report beside it.
"""

from __future__ import annotations

import copy
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

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


DRAIN = _load_module("_roster_promotion_drain_repair", SCRIPTS_DIR / "promotion_drain.py")
KS = DRAIN.KS
WL = _load_module(
    "_roster_header_readiness_repair",
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "_header_readiness.py",
)
H = WL
_CAPTURED_FILE_RE = WL._CAPTURED_FILE_RE


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


def _seed_store(repo: Path, requests: list[dict[str, Any]]) -> list[str]:
    (repo / "docs" / "knowledge" / "topics").mkdir(parents=True)
    (repo / "docs" / "product" / "captured").mkdir(parents=True)
    KS.rebuild_topic_map(repo)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "-m", "map"],
        cwd=repo, check=True, capture_output=True,
    )
    return [
        KS.seed_previously_admitted_capture(repo, request)["capture_id"]
        for request in requests
    ]


def _git_repo(base: Path, name: str) -> Path:
    repo = base / name
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    return repo


def _captured_files(repo: Path) -> list[str]:
    captured = repo / "docs" / "product" / "captured"
    return sorted(path.name for path in captured.iterdir()) if captured.exists() else []


# --- T9: collision-safe, non-destructive route transaction --------------------


def test_two_routes_sharing_a_slug_prefix_both_commit(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t9-collision")
    prefix = "collision " * 10  # 100 chars; the slug truncates at 60
    ids = _seed_store(
        repo,
        [
            _request("defect", prefix + " first defect needs routing",
                     observed="The drain reports the item as unplaced today.",
                     intended="The drain reports the item at its owner."),
            _request("defect", prefix + " second defect needs routing",
                     observed="The drain reports the item as unplaced today too.",
                     intended="The drain reports the item at its owner as well."),
        ],
    )
    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})
    assert report["counts"] == {"routed": 2, "held": 0, "closed": 0}, report
    assert len(_captured_files(repo)) == 2, _captured_files(repo)
    for capture_id in ids:
        dispositions = [
            d for d in DRAIN.store_terminal_dispositions(repo)
            if d["capture_id"] == capture_id
        ]
        assert [d["disposition"] for d in dispositions] == ["routed"]


def test_preexisting_differing_target_is_never_deleted(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t9-preexisting")
    _seed_store(
        repo,
        [_request("defect", "A defect whose target is already taken",
                  observed="The target path holds another file.",
                  intended="The transaction must refuse without deleting it.")],
    )
    capture = DRAIN.read_open_captures(repo)["captures"][0]
    offer = {
        "capture_id": capture["capture_id"],
        "partition": capture["partition"],
        "request": capture["request"],
    }
    target = repo / DRAIN._captured_item_target(offer)
    target.write_bytes(b"an operator's complete file, not this transaction's")
    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})
    assert report["counts"] == {"routed": 0, "held": 1, "closed": 0}, report
    assert target.read_bytes() == b"an operator's complete file, not this transaction's"


def test_repeated_transact_is_idempotent(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t9-idempotent")
    _seed_store(
        repo,
        [_request("defect", "A defect routed twice by re-drive",
                  observed="A crash can land between dispatch and disposition.",
                  intended="The re-drive completes the sequence once.")],
    )
    capture = DRAIN.read_open_captures(repo)["captures"][0]
    offer = {
        "capture_id": capture["capture_id"],
        "partition": capture["partition"],
        "request": capture["request"],
    }
    first = DRAIN.transact_route(repo, offer, {"route": "defect-processor"})
    second = DRAIN.transact_route(repo, offer, {"route": "defect-processor"})
    assert first["committed"] and second["committed"]
    assert len(_captured_files(repo)) == 1


# --- T10: per-record isolation in the open-capture reader ---------------------


def _dirty_merged_line(request: dict[str, Any]) -> bytes:
    """One merge-path journal line: identity fields recomputed over prose
    the write-time controls would refuse."""
    capture_id = "kco-202611-" + "0" * 64
    digest = KS.PK.digest_bytes(KS.PK._canonical_json_bytes(request))["sha256"]
    event = {
        "event_type": "observation.captured",
        "schema_version": "observation-event.v1",
        "capture_id": capture_id,
        "partition": "observations/work-item/2026-11.jsonl",
        "captured_at": "2026-11-04T10:00:00Z",
        "state": "pending",
        "request": request,
        "request_sha256": digest,
    }
    return KS._event_line(event)


def test_one_dirty_merged_record_holds_only_itself(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t10-dirty")
    ids = _seed_store(
        repo,
        [_request("defect", "A clean capture beside a dirty merged record",
                  observed="The dirty record must not block the clean one.",
                  intended="The drain holds the bad record alone.")],
    )
    journal = repo / "docs" / "knowledge" / "observations" / "work-item" / "2026-11.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    dirty = _request(
        "defect", "Check /Users/leaker/credentials.txt before routing",
        observed="The merge path can land unvalidated prose.",
        intended="The read path quarantines the record.",
    )
    with journal.open("ab") as handle:
        handle.write(_dirty_merged_line(dirty))

    read = DRAIN.read_open_captures(repo)
    assert [capture["capture_id"] for capture in read["captures"]] == ids
    assert len(read["quarantined"]) == 1
    assert read["quarantined"][0]["reason_code"] == "policy_invalid"

    report = DRAIN.drain(repo)
    assert report["counts"] == {"routed": 0, "held": 2, "closed": 0}, report
    reasons = {item.get("reason") for item in report["items"]}
    assert "unattended" in reasons
    assert "quarantined:policy_invalid" in reasons


def test_reader_reads_through_the_store_pending_path(
    git_repo: Path, monkeypatch: Any
) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t10-identity")
    _seed_store(
        repo,
        [_request("defect", "A capture read through the pending path",
                  observed="The reader delegates to the store.",
                  intended="No second validation implementation.")],
    )
    calls: list[dict[str, Any]] = []
    real = KS.pending_page

    def spy(root: Any, request: dict[str, Any]) -> dict[str, Any]:
        calls.append(copy.deepcopy(request))
        return real(root, request)

    monkeypatch.setattr(KS, "pending_page", spy)
    DRAIN.read_open_captures(repo)
    assert calls and all(
        request["selection_mode"] == "direct-maintainer-pending" for request in calls
    )


# --- T11: grammar-conforming materialization ---------------------------------


def test_defect_artifact_parses_under_the_owner_grammar(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t11-defect")
    _seed_store(
        repo,
        [_request("defect", "A defect whose artifact must parse",
                  observed="The captured-item grammar is the owner's contract.",
                  intended="The materialized file parses valid under it.")],
    )
    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})
    assert report["counts"] == {"routed": 1, "held": 0, "closed": 0}, report
    (artifact,) = (repo / "docs" / "product" / "captured").iterdir()
    fields, failing = WL.parse_captured_item(artifact.read_text(encoding="utf-8"))
    assert fields is not None, failing
    assert fields["kind"] == "defect"
    assert fields["detail"] == "docs/knowledge/observations/work-item/2026-11.jsonl"


def test_question_route_materializes_no_artifact(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t11-question")
    _seed_store(repo, [_request("question", "Where does a routed question land?")])
    dispatched: list[str] = []

    def spying_transact(offer: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        return DRAIN.transact_route(
            repo, offer, decision,
            dispatch_processor=lambda: dispatched.append(decision["classification"]),
        )

    report = DRAIN.drain(
        repo,
        classify=lambda message: "spec",
        confirmer=lambda offer, proposal: {"confirm": True},
        transact=spying_transact,
    )
    assert report["counts"] == {"routed": 1, "held": 0, "closed": 0}, report
    assert dispatched == ["spec"]
    assert _captured_files(repo) == []


# --- T12: closure evidence rides the run report -------------------------------


def test_closure_evidence_rides_the_report(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t12-evidence")
    ids = _seed_store(
        repo,
        [_request("defect", "A capture closed as overtaken",
                  observed="The blocker is unresolved today.",
                  intended="A later decision resolves the blocker.")],
    )
    evidence = {
        "what_was_run": "grep -F 'the-blocking-decision' docs/specs/example/plan.md",
        "what_it_showed": "The blocking decision was resolved in the plan's latest revision.",
    }

    def close(_offer: dict[str, Any], _proposal: dict[str, Any]) -> dict[str, Any]:
        return {
            "close": {
                "ground": "overtaken",
                "test_passes": True,
                "evidence": evidence,
            }
        }

    report = DRAIN.drain(repo, confirmer=close)
    assert report["counts"] == {"routed": 0, "held": 0, "closed": 1}, report
    (closed,) = [item for item in report["items"] if item["action"] == "closed"]
    assert closed["capture_id"] == ids[0]
    assert closed["ground"] == "overtaken"
    assert closed["evidence"] == evidence


# --- T13: a refused disposition write holds the item, not the run --------------


def _mixed_store(repo: Path) -> None:
    """One clean capture plus one privacy-dirty merged line (T10's fixture)."""
    KS.seed_previously_admitted_capture(
        repo, _request("defect", "A clean capture beside a dirty merged record",
                       observed="The dirty record must not block the clean one.",
                       intended="The drain holds the bad record alone."))
    journal = repo / "docs" / "knowledge" / "observations" / "work-item" / "2026-11.jsonl"
    dirty = _request(
        "defect", "Check /Users/leaker/credentials.txt before routing",
        observed="The merge path can land unvalidated prose.",
        intended="The read path quarantines the record.",
    )
    with journal.open("ab") as handle:
        handle.write(_dirty_merged_line(dirty))


def test_refused_route_disposition_holds_the_item(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t13-route")
    _seed_store(repo, [])
    _mixed_store(repo)

    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})

    # The quarantined record is held by the read; the clean capture's route
    # transaction commits, its disposition write is refused by the store's
    # strict read, and the item is held with the refusing reason — no
    # exception escapes the run.
    assert report["counts"] == {"routed": 0, "held": 2, "closed": 0}, report
    reasons = {item.get("reason") for item in report["items"]}
    assert "quarantined:policy_invalid" in reasons
    assert any(
        str(reason).startswith("disposition-refused:") for reason in reasons
    ), reasons
    (artifact,) = (repo / "docs" / "product" / "captured").iterdir()
    assert artifact.suffix == ".md"


def test_refused_closure_disposition_holds_the_item(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t13-closure")
    _seed_store(repo, [])
    _mixed_store(repo)

    def close(_offer: dict[str, Any], _proposal: dict[str, Any]) -> dict[str, Any]:
        return {
            "close": {
                "ground": "overtaken",
                "test_passes": True,
                "evidence": {"what_was_run": "the closing check", "what_it_showed": "it passed"},
            }
        }

    report = DRAIN.drain(repo, confirmer=close)

    assert report["counts"] == {"routed": 0, "held": 2, "closed": 0}, report
    reasons = {item.get("reason") for item in report["items"]}
    assert any(
        str(reason).startswith("disposition-refused:") for reason in reasons
    ), reasons


def test_clean_store_dispositions_are_unchanged(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t13-clean")
    ids = _seed_store(
        repo,
        [_request("defect", "A clean routed defect",
                  observed="The store holds no quarantined record.",
                  intended="The disposition write succeeds.")],
    )
    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})
    assert report["counts"] == {"routed": 1, "held": 0, "closed": 0}, report
    assert [d["capture_id"] for d in DRAIN.store_terminal_dispositions(repo)] == ids


# --- T14: one read path — dispositions through the exclusion reader ----------


def test_store_terminal_dispositions_tolerates_quarantined_records(
    git_repo: Path,
) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t14")
    ids = _seed_store(
        repo,
        [_request("defect", "A dispositioned capture beside a dirty record",
                  observed="The dirty record must not block the count.",
                  intended="The dispositions helper reads through it.")],
    )
    KS.write_terminal_disposition(
        repo, ids[0], "routed", reason_code="route-handoff-accepted",
        recorded_at="2026-11-04T12:00:00Z"
    )
    _mixed_store(repo)

    dispositions = DRAIN.store_terminal_dispositions(repo)

    # The clean capture's disposition is derivable; the quarantined record
    # is excluded by the store's own reader rather than aborting the read.
    assert dispositions == [
        {"capture_id": ids[0], "disposition": "routed",
         "reason_code": "route-handoff-accepted"}
    ], dispositions


def test_store_terminal_dispositions_clean_store_unchanged(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t14-clean")
    ids = _seed_store(
        repo,
        [_request("defect", "A clean dispositioned capture",
                  observed="No quarantined records exist.",
                  intended="The dispositions list is unchanged.")],
    )
    KS.write_terminal_disposition(
        repo, ids[0], "rejected", reason_code="not-a-defect",
        recorded_at="2026-11-04T12:00:00Z"
    )

    dispositions = DRAIN.store_terminal_dispositions(repo)

    assert dispositions == [
        {"capture_id": ids[0], "disposition": "rejected",
         "reason_code": "not-a-defect"}
    ], dispositions


# --- T15: the captured-item filename stays inside the owner's grammar --------


def _routed_defect_with_statement(repo: Path, statement: str) -> dict[str, Any]:
    ids = _seed_store(
        repo, [_request("defect", statement,
                        observed="The filename must match the owner grammar.",
                        intended="The owner listing sees the item.")]
    )
    report = DRAIN.drain(repo, confirmer=lambda offer, proposal: {"confirm": True})
    assert report["counts"] == {"routed": 1, "held": 0, "closed": 0}, report
    return {"capture_id": ids[0], "report": report}


def test_nonascii_statement_lands_inside_owner_grammar(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t15")
    _routed_defect_with_statement(
        repo, "Le café du matin n'est pas prêt"
    )

    captured = repo / "docs" / "product" / "captured"
    (artifact,) = captured.iterdir()
    assert _CAPTURED_FILE_RE.match(artifact.name), artifact.name

    listing = H.list_captured_items(repo, frozenset())
    assert not listing.findings
    assert [item["path"] for item in listing.items] == [
        artifact.relative_to(repo).as_posix()
    ]


def test_ascii_statement_filename_unchanged(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t15-ascii")
    seeded = _routed_defect_with_statement(
        repo, "Router drops held items on re-run"
    )
    tail = seeded["capture_id"][-12:]

    captured = repo / "docs" / "product" / "captured"
    (artifact,) = captured.iterdir()
    assert artifact.name == f"router-drops-held-items-on-re-run-{tail}.md"


# --- T16: the work-intake dispatch rides the transaction's failure shape ------


def test_failing_question_dispatch_holds_the_item(git_repo: Path) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t16")
    ids = _seed_store(
        repo,
        [
            _request("question", "Where does the question route dispatch?",
                     observed="A failing dispatch must not abort the drain.",
                     intended="The item is held; later items are still offered."),
            _request("question", "A second question still routed",
                     observed="The drain continues past a held item.",
                     intended="Both items are processed."),
        ],
    )
    dispatched: list[str] = []

    def transact(offer, decision):
        if offer["capture_id"] == ids[0]:
            return DRAIN.transact_route(
                repo, offer, decision,
                dispatch_processor=lambda: (_ for _ in ()).throw(
                    RuntimeError("processor exploded")
                ),
            )
        return DRAIN.transact_route(
            repo, offer, decision, dispatch_processor=lambda: dispatched.append(
                offer["capture_id"]
            )
        )

    report = DRAIN.drain(
        repo,
        classify=lambda message: "spec",
        confirmer=lambda offer, proposal: {"confirm": True},
        transact=transact,
    )

    # The failing item is held with the failed stage named — no exception
    # text escapes — and the second item is still routed.
    assert report["counts"] == {"routed": 1, "held": 1, "closed": 0}, report
    held = [item for item in report["items"] if item["action"] == "held"]
    assert held == [
        {"capture_id": ids[0], "action": "held", "reason": "transaction-failed",
         "failed_stage": "processor_dispatch"}
    ], held
    assert dispatched == [ids[1]]


# --- T18: partition enumeration rides the same quarantine collector ----------


def test_store_terminal_dispositions_tolerates_misnamed_partition(
    git_repo: Path,
) -> None:
    repo = _git_repo(git_repo.parent, f"{git_repo.name}-t18")
    ids = _seed_store(
        repo,
        [_request("defect", "A dispositioned capture beside a misnamed partition",
                  observed="A misnamed partition must not block the count.",
                  intended="The dispositions helper reads through it.")],
    )
    KS.write_terminal_disposition(
        repo, ids[0], "routed", reason_code="route-handoff-accepted",
        recorded_at="2026-11-04T12:00:00Z",
    )
    (repo / "docs" / "knowledge" / "observations" / "work-item" / "2026-1x.jsonl").write_bytes(b"")

    # The reader quarantines the misnamed partition; the dispositions helper
    # reads through it and still derives the clean capture's disposition.
    read = DRAIN.read_open_captures(repo)
    assert [q["reason_code"] for q in read["quarantined"]] == ["unsafe"], read
    dispositions = DRAIN.store_terminal_dispositions(repo)
    assert dispositions == [
        {"capture_id": ids[0], "disposition": "routed",
         "reason_code": "route-handoff-accepted"}
    ], dispositions
