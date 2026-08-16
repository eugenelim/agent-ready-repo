from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from knowledge_test_support import (
    PROJECT_KNOWLEDGE_SCRIPT,
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    valid_capture_request,
)


@pytest.fixture
def store():
    return load_knowledge_store_module()


@pytest.fixture
def repo(tmp_path: Path, store) -> Path:
    return initialize_empty_v1_repo(tmp_path, store)


def _request(**overrides: Any) -> dict[str, Any]:
    request = valid_capture_request()
    request["observed_at"] = "2026-08-13T12:34:56Z"
    request.update(overrides)
    return request


def _capture(repo: Path, store, **overrides: Any) -> dict[str, Any]:
    return store.capture_observation(
        repo,
        _request(**overrides),
        writer_time="2026-08-13T12:40:00Z",
    )


def test_ac4_capture_can_remain_pending_and_non_queryable(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    page = store.pending_page(repo, {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"})
    assert [event["capture_id"] for event in page["pending"]] == [receipt["capture_id"]]
    assert store.enquire_worktree(repo, {"question": "What should I use?"})["selected_topic_ids"] == []


def test_ac19_pending_cursor_refuses_partition_drift_without_skipping(repo: Path, store) -> None:
    receipts = []
    for month in range(1, 8):
        receipts.append(
            store.capture_observation(
                repo,
                _request(
                    lesson=f"Use the bounded partition cursor for month {month}.",
                    observed_at=f"2026-{month:02d}-13T12:35:56Z",
                ),
                writer_time=f"2026-{month:02d}-13T12:40:00Z",
            )
        )
    request = {
        "selection_mode": "direct-maintainer-pending",
        "scope": "packs/core",
    }
    first_page = store.pending_page(repo, request)
    assert [event["capture_id"] for event in first_page["pending"]] == [
        receipt["capture_id"] for receipt in receipts[:6]
    ]

    weakened = store._cursor_decode(first_page["cursor"])
    weakened["bound_partitions"] = []
    with pytest.raises(store.KnowledgeStoreError) as weakened_refused:
        store.pending_page(repo, request | {"cursor": store._cursor_encode(weakened)})
    assert weakened_refused.value.diagnostic["reason_code"] == "cursor_stale"

    store.write_terminal_disposition(
        repo,
        receipts[1]["capture_id"],
        "rejected",
        reason_code="not_reusable",
        recorded_at="2026-08-13T12:41:00Z",
    )
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(repo, request | {"cursor": first_page["cursor"]})
    assert refused.value.diagnostic["reason_code"] == "cursor_stale"

    restarted = store.pending_page(repo, request)
    assert receipts[1]["capture_id"] not in {
        event["capture_id"] for event in restarted["pending"]
    }


@pytest.mark.parametrize("cursor", ([], {}, "not-base64!", 7))
def test_ac19_pending_refuses_malformed_cursor_without_traceback(
    repo: Path, store, cursor: Any
) -> None:
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(
            repo,
            {
                "selection_mode": "direct-maintainer-pending",
                "scope": "packs/core",
                "cursor": cursor,
            },
        )
    assert refused.value.diagnostic["reason_code"] == "cursor_stale"


def test_ac19_cursor_digest_refuses_non_regular_partition(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    path = store._journal_path(repo, receipt["partition"])
    path.unlink()
    path.mkdir()

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(
            repo,
            {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"},
        )
    assert refused.value.diagnostic["reason_code"] == "confinement"


def test_ac4_pending_drain_is_explicit_scoped_and_receipted(repo: Path, store) -> None:
    included = _capture(
        repo,
        store,
        project_scope={"paths": ["packages/core"], "audience": "project"},
    )
    excluded = _capture(
        repo,
        store,
        lesson="Keep a scoped pending drain within its selected subtree.",
        observed_at="2026-08-13T12:35:56Z",
        project_scope={"paths": ["services/api"], "audience": "project"},
    )
    request = {"selection_mode": "direct-maintainer-pending", "scope": "packages/core"}
    page = store.pending_page(repo, request)
    assert [event["capture_id"] for event in page["pending"]] == [included["capture_id"]]
    assert excluded["capture_id"] not in {
        event["capture_id"] for event in page["pending"]
    }
    receipt = store.distill_pending(repo, request)
    assert receipt["selection_mode"] == "direct-maintainer-pending"
    assert receipt["scope"] == "packages/core"
    assert set(receipt["counts"]) == {"pending", "processed", "unresolved"}

    with pytest.raises(store.KnowledgeStoreError):
        store.distill_pending(
            repo,
            {"selection_mode": "workflow-receipts", "scope": "packages/core"},
        )


def test_ac4_broad_non_root_pending_scope_excludes_descendant_capture(
    repo: Path, store
) -> None:
    receipt = _capture(
        repo,
        store,
        project_scope={"paths": ["packages/core"], "audience": "project"},
    )

    broad = store.pending_page(
        repo,
        {"selection_mode": "direct-maintainer-pending", "scope": "packages"},
    )
    root = store.pending_page(
        repo,
        {"selection_mode": "direct-maintainer-pending", "scope": "."},
    )

    assert receipt["capture_id"] not in {
        event["capture_id"] for event in broad["pending"]
    }
    assert receipt["capture_id"] in {
        event["capture_id"] for event in root["pending"]
    }


def test_ac4_workflow_selection_uses_only_explicit_receipts(repo: Path, store) -> None:
    receipt = _capture(repo, store)
    other = _capture(
        repo,
        store,
        lesson="Do not let a workflow drain the maintainer pending corpus.",
        observed_at="2026-08-13T12:36:56Z",
    )
    unrelated = repo / "docs/knowledge/observations/gotcha/2026-07.jsonl"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"not-json\n")
    request = {
        "selection_mode": "workflow-receipts",
        "receipts": [
            {
                "capture_id": receipt["capture_id"],
                "partition": receipt["partition"],
            }
        ],
    }
    page = store.pending_page(repo, request)
    assert [event["capture_id"] for event in page["pending"]] == [receipt["capture_id"]]
    assert other["capture_id"] not in {event["capture_id"] for event in page["pending"]}

    drain = store.distill_pending(repo, request)
    assert [event["capture_id"] for event in drain["pending"]] == [receipt["capture_id"]]
    cli = subprocess.run(
        [
            sys.executable,
            str(PROJECT_KNOWLEDGE_SCRIPT),
            "--distill",
            "--pending",
            "--repo-root",
            str(repo),
        ],
        input=json.dumps(request).encode("utf-8"),
        capture_output=True,
        check=True,
    )
    cli_result = json.loads(cli.stdout)
    assert [event["capture_id"] for event in cli_result["pending"]] == [
        receipt["capture_id"]
    ]

    wrong_partition = {
        "selection_mode": "workflow-receipts",
        "receipts": [
            {
                "capture_id": receipt["capture_id"],
                "partition": "observations/gotcha/2026-07.jsonl",
            }
        ],
    }
    with pytest.raises(store.KnowledgeStoreError):
        store.pending_page(repo, wrong_partition)

    broad = copy.deepcopy(page)
    broad["pending"].append({"capture_id": other["capture_id"]})
    assert len(broad["pending"]) == 2


def test_ac19_scoped_cursor_reaches_matching_later_partition(repo: Path, store) -> None:
    for month in range(1, 7):
        observed = f"2026-{month:02d}-01T12:34:56Z"
        store.capture_observation(
            repo,
            _request(
                lesson=f"Nonmatching scoped observation for month {month}.",
                observed_at=observed,
                project_scope={"paths": ["services/api"], "audience": "project"},
            ),
            writer_time=f"2026-{month:02d}-01T12:40:00Z",
        )
    matching = store.capture_observation(
        repo,
        _request(
            lesson="The seventh partition remains reachable through paging.",
            observed_at="2026-07-01T12:34:56Z",
            project_scope={"paths": ["packages/core"], "audience": "project"},
        ),
        writer_time="2026-07-01T12:40:00Z",
    )
    request = {
        "selection_mode": "direct-maintainer-pending",
        "scope": "packages/core",
    }
    first = store.pending_page(repo, request)
    assert first["pending"] == []
    assert first["cursor"] is not None

    second = store.pending_page(repo, request | {"cursor": first["cursor"]})
    assert [event["capture_id"] for event in second["pending"]] == [
        matching["capture_id"]
    ]
    assert second["cursor"] is None


def test_ac19_hot_partition_refuses_without_partial_pending_output(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    template = store.captured_event_for_request(
        _request(),
        writer_time="2026-08-13T12:40:00Z",
    )
    events = []
    for index in range(10_001):
        event = copy.deepcopy(template)
        event["capture_id"] = f"kco-202608-{index:064x}"
        events.append(event)
    partition = events[0]["partition"]
    with store.hold_writer_lock(repo):
        store._replace_atomic(
            store._journal_path(repo, partition),
            b"".join(store._event_line(event) for event in events),
        )

    # Event validation has focused malformed-input coverage. Isolate this construction
    # test to the selector's bounded streaming behavior so a >10k corpus stays fast.
    monkeypatch.setattr(store, "_validate_event", lambda event, _partition: event)

    request = {
        "selection_mode": "direct-maintainer-pending",
        "scope": "packs/core",
        "page_event_limit": 10,
    }
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(repo, request)
    assert refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac19_pending_stops_before_reading_partition_beyond_byte_window(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = store.capture_observation(
        repo,
        _request(observed_at="2026-01-13T12:35:56Z"),
        writer_time="2026-01-13T12:40:00Z",
    )
    first_path = store._journal_path(repo, first["partition"])
    second_path = repo / "docs/knowledge/observations/pattern/2026-02.jsonl"
    second_path.write_bytes(b"not-json-and-must-not-be-read\n")
    monkeypatch.setitem(
        store.PK._BUDGETS,
        "pending_page_bytes",
        first_path.stat().st_size + second_path.stat().st_size - 1,
    )

    page = store.pending_page(
        repo,
        {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"},
    )

    assert [event["capture_id"] for event in page["pending"]] == [first["capture_id"]]
    assert page["partitions"] == [first["partition"]]
    assert page["cursor"] is not None


def test_ac19_pending_refuses_when_complete_partitions_exceed_event_page(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    for month in (1, 2):
        store.capture_observation(
            repo,
            _request(
                lesson=f"Complete partition event budget {month}.",
                observed_at=f"2026-{month:02d}-13T12:35:56Z",
            ),
            writer_time=f"2026-{month:02d}-13T12:40:00Z",
        )
    monkeypatch.setitem(store.PK._BUDGETS, "pending_page_events", 1)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(
            repo,
            {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"},
        )

    assert refused.value.diagnostic["reason_code"] == "journal_capacity"


def test_ac19_pending_refuses_over_retained_partition_inventory(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    for month in (1, 2):
        store.capture_observation(
            repo,
            _request(
                lesson=f"Retained partition budget {month}.",
                observed_at=f"2026-{month:02d}-13T12:35:56Z",
            ),
            writer_time=f"2026-{month:02d}-13T12:40:00Z",
        )
    monkeypatch.setitem(store.PK._BUDGETS, "retained_partitions", 1)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.pending_page(
            repo,
            {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"},
        )

    assert refused.value.diagnostic["reason_code"] == "journal_capacity"
