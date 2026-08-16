from __future__ import annotations

import pytest
from knowledge_test_support import (
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    valid_capture_request,
)
from test_topic_store import mutation_proposal


@pytest.fixture
def store():
    return load_knowledge_store_module()


def test_ac32_topic_map_merge_rebuilds_distinct_and_refuses_same_topic(tmp_path, store) -> None:
    initialize_empty_v1_repo(tmp_path / "merged", store)
    request = valid_capture_request()
    request["observed_at"] = "2026-08-13T12:34:56Z"
    left_receipt = store.seed_previously_admitted_capture(tmp_path / "merged", request)
    right_request = valid_capture_request(
        lesson="Suggest work intake when no verification oracle exists."
    )
    right_request["observed_at"] = "2026-08-13T12:34:56Z"
    right_receipt = store.seed_previously_admitted_capture(tmp_path / "merged", right_request)
    left = store.complete_mutation_proposal(
        mutation_proposal(
            capture_id=left_receipt["capture_id"],
            topic_key="contracts/public-contracts",
        )
    )
    right = store.complete_mutation_proposal(
        mutation_proposal(
            capture_id=right_receipt["capture_id"],
            topic_key="routes/verification-oracles",
            title="Route verification gaps through work intake",
            synthesis={
                "kind": "pattern",
                "body": "Suggest work intake when no verification oracle exists.",
            },
        )
    )
    merged = store.merge_topic_trees(tmp_path, [left], [right])
    assert merged["map_bytes"] == store.rebuild_map_bytes(tmp_path / "merged" / "docs" / "knowledge")

    with pytest.raises(store.KnowledgeStoreError):
        store.merge_topic_trees(
            tmp_path,
            [left],
            [store.complete_mutation_proposal(mutation_proposal(topic_key=left["topic_key"]))],
        )
