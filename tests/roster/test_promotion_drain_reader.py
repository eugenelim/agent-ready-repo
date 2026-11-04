"""Roster coverage for the drain-side open-capture reader.

Spec: ``docs/specs/work-item-promotion-handoff`` — task T1, the store's
drain-side reader. The fixture store holds every record kind the reader must
separate: an open work-item capture, a dispositioned work-item capture (whose
disposition line is an envelope-only record — no request payload, per the
capture spec's layer table), and an open non-work-item observation, which
belongs to the distillation path and never to the drain. A malformed merged
record placed by direct file write must refuse under the store's own read
rules rather than reach an offer.
"""

from __future__ import annotations

import hashlib
import importlib.util
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


# The module under test loads its own store instance; seeding and the
# exception class must come from that same instance, or a raised
# ``KnowledgeStoreError`` is a different class object than the one expected.
DRAIN = _load_module("_roster_promotion_drain_reader", SCRIPTS_DIR / "promotion_drain.py")
KS = DRAIN.KS


def _request(kind: str, *, statement: str, observed_at: str) -> dict[str, Any]:
    """A minimal valid capture request of ``kind`` ("work-item" or "pattern")."""
    request: dict[str, Any] = {
        "contract_version": "knowledge-captured-observation.v2",
        "kind": kind,
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
        "observed_at": observed_at,
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
    }
    if kind == "work-item":
        request["work_item"] = {
            "statement": statement,
            "shape": "question",
            "blocker": "decision",
            "finished_state": "The routing question is answered in the work-item reference guide.",
            "necessity_rationale": "The answer decides where the drain records the disposition.",
            "answered_by": "docs/knowledge/reference/work-items.md",
        }
    else:
        request["lesson"] = statement
    return request


def _append_line(root: Path, partition: str, line: bytes) -> None:
    """Append a journal line the way a merged record arrives: a direct file
    write that bypasses every write-time control."""
    path = root / "docs" / "knowledge" / partition
    with path.open("ab") as handle:
        handle.write(line)


def _seed(root: Path) -> dict[str, dict[str, Any]]:
    """Seed the fixture store and return each record's capture receipt."""
    open_receipt = KS.seed_previously_admitted_capture(
        root,
        _request(
            "work-item",
            statement="Where does a promoted work item land?",
            observed_at="2026-11-04T10:00:00Z",
        ),
    )
    closed_receipt = KS.seed_previously_admitted_capture(
        root,
        _request(
            "work-item",
            statement="Which guide owns the routing table?",
            observed_at="2026-11-04T10:05:00Z",
        ),
    )
    pattern_receipt = KS.seed_previously_admitted_capture(
        root,
        _request(
            "pattern",
            statement="Prefer the store's own reader over a new one.",
            observed_at="2026-11-04T10:10:00Z",
        ),
    )
    # The closed capture's disposition: an envelope-only record (no request
    # payload), serialized by the store's own line writer so the fixture
    # bytes match what a real writer emits.
    _append_line(
        root,
        closed_receipt["partition"],
        KS._event_line(
            {
                "event_type": "observation.dispositioned",
                "schema_version": "observation-event.v1",
                "capture_id": closed_receipt["capture_id"],
                "partition": closed_receipt["partition"],
                "disposition": "routed",
                "reason_code": "routed-to-owner",
                "recorded_at": "2026-11-04T11:00:00Z",
            }
        ),
    )
    return {"open": open_receipt, "closed": closed_receipt, "pattern": pattern_receipt}


def _tree_digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_reader_yields_exactly_the_open_work_item_captures(git_repo: Path) -> None:
    seeded = _seed(git_repo)

    read = DRAIN.read_open_captures(git_repo)

    # Only the open work-item capture: not the dispositioned one, not its
    # envelope-only disposition line, not the pattern observation. The
    # malformed-record case is covered below; a clean store quarantines
    # nothing.
    assert read["quarantined"] == []
    assert [capture["capture_id"] for capture in read["captures"]] == [
        seeded["open"]["capture_id"]
    ]
    record = read["captures"][0]
    assert record["partition"] == seeded["open"]["partition"]
    assert record["captured_at"] == "2026-11-04T10:00:00Z"
    assert record["terminal_disposition"] is None
    assert record["request"]["kind"] == "work-item"
    assert (
        record["request"]["work_item"]["statement"]
        == "Where does a promoted work item land?"
    )


def test_read_leaves_every_store_file_unchanged(git_repo: Path) -> None:
    _seed(git_repo)
    before = _tree_digests(git_repo / "docs" / "knowledge")

    DRAIN.read_open_captures(git_repo)

    assert _tree_digests(git_repo / "docs" / "knowledge") == before


def test_malformed_merged_record_is_refused_rather_than_offered(
    git_repo: Path,
) -> None:
    seeded = _seed(git_repo)
    # A merged record the write path never validated: well-formed JSON the
    # store's event grammar refuses. The reader excludes it through the
    # store's own quarantine and the clean capture is still offered — one
    # bad record never aborts the whole read.
    _append_line(
        git_repo,
        seeded["open"]["partition"],
        b'{"event_type": "observation.merged", "schema_version": "observation-event.v1"}\n',
    )

    read = DRAIN.read_open_captures(git_repo)

    # The store's own closure rule for dependents: an invalid line whose
    # target cannot be identified hides the whole partition — nothing from
    # it is offered, and the quarantine names both the line and the hidden
    # partition. (The T10 repair test covers the identifiable dirty line,
    # which quarantines itself alone.)
    assert read["captures"] == []
    reasons = [entry["reason_code"] for entry in read["quarantined"]]
    assert reasons == ["malformed", "partition_hidden"]
    assert read["quarantined"][0]["line"] == 4
