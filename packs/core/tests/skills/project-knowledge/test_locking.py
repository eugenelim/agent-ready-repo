from __future__ import annotations

from pathlib import Path

import pytest
from knowledge_test_support import (
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


def test_ac13_lost_lock_is_never_removed_or_reused(repo: Path, store) -> None:
    lock_path = store.knowledge_lock_path(repo)
    lock_path.write_text("foreign-lock\n", encoding="utf-8")

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.capture_observation(
            repo,
            valid_capture_request(observed_at="2026-08-13T12:34:56Z"),
            writer_time="2026-08-13T12:40:00Z",
            lock_timeout=0.01,
        )
    assert refused.value.diagnostic["reason_code"] == "lock_contention"
    assert lock_path.read_text(encoding="utf-8") == "foreign-lock\n"


def test_ac13_capture_and_distill_contend_on_one_global_lock(repo: Path, store) -> None:
    with store.hold_writer_lock(repo), pytest.raises(store.KnowledgeStoreError) as refused:
        with store.begin_distill(repo, lock_timeout=0.01):
            raise AssertionError("distill lock should not be acquired")
        assert refused.value.diagnostic["reason_code"] == "lock_contention"

    with store.hold_writer_lock(repo):
        with pytest.raises(store.KnowledgeStoreError) as refused:
            store.capture_observation(
                repo,
                valid_capture_request(observed_at="2026-08-13T12:34:56Z"),
                writer_time="2026-08-13T12:40:00Z",
                lock_timeout=0.01,
            )
        assert refused.value.diagnostic["reason_code"] == "lock_contention"
    assert list((repo / "docs" / "knowledge").glob("*.tmp-*")) == []


def test_ac13_successful_write_leaves_no_lock_or_target_residue(repo: Path, store) -> None:
    target = store._lock_target(repo)
    lock_path = store.knowledge_lock_path(repo)

    store.capture_observation(
        repo,
        valid_capture_request(observed_at="2026-08-13T12:34:56Z"),
        writer_time="2026-08-13T12:40:00Z",
    )

    assert not target.exists()
    assert not lock_path.exists()
