"""T0 (RFC-0052): cross-process state-write lock.

The lock is the mechanism behind the concurrency AC (two simultaneous installs
of different adapter rows of one pack both land). Tests cover mutual
exclusion, stale reclaim, timeout, no-leftover-lockfile, and the
read-merge-write of ``persist_state_locked``.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from agentbundle import config, statelock


def test_mutual_exclusion(tmp_path: Path) -> None:
    state_path = tmp_path / "state.toml"
    events: list[str] = []
    start = threading.Barrier(2)

    def worker(tag: str) -> None:
        start.wait()
        with statelock.state_lock(state_path, timeout=5.0):
            events.append(f"enter-{tag}")
            time.sleep(0.1)
            events.append(f"exit-{tag}")

    t1 = threading.Thread(target=worker, args=("a",))
    t2 = threading.Thread(target=worker, args=("b",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Whoever entered first must exit before the other enters — no interleave.
    assert events[0].startswith("enter-")
    assert events[1] == events[0].replace("enter", "exit")
    assert events[2].startswith("enter-")
    assert events[3] == events[2].replace("enter", "exit")


def test_stale_lock_reclaimed(tmp_path: Path) -> None:
    state_path = tmp_path / "state.toml"
    lock_path = state_path.with_name(state_path.name + ".lock")
    lock_path.write_text("99999", encoding="utf-8")
    # Backdate the lockfile beyond the stale threshold.
    import os
    old = time.time() - 120
    os.utime(lock_path, (old, old))

    with statelock.state_lock(state_path, timeout=1.0, stale_after=60.0):
        pass  # Acquired (reclaimed) rather than timing out.
    assert not lock_path.exists()


def test_timeout_when_held(tmp_path: Path) -> None:
    state_path = tmp_path / "state.toml"
    held = threading.Event()
    release = threading.Event()

    def holder() -> None:
        with statelock.state_lock(state_path, timeout=5.0):
            held.set()
            release.wait(timeout=5.0)

    t = threading.Thread(target=holder)
    t.start()
    held.wait(timeout=5.0)
    try:
        with pytest.raises(statelock.StateLockTimeout):
            with statelock.state_lock(state_path, timeout=0.2, stale_after=999):
                pass
    finally:
        release.set()
        t.join()


def test_happy_path_leaves_no_lockfile(tmp_path: Path) -> None:
    state_path = tmp_path / "state.toml"
    lock_path = state_path.with_name(state_path.name + ".lock")
    with statelock.state_lock(state_path):
        assert lock_path.exists()
    assert not lock_path.exists()


def test_persist_state_locked_merges_concurrent_rows(tmp_path: Path) -> None:
    state_path = tmp_path / "state.toml"
    # Seed a v0.4 file with one row.
    seed = config.State()
    seed.packs[("research", "claude-code")] = config.PackState(
        installed_version="1.0.0", adapter="claude-code", scope="repo",
        files={".claude/skills/x/SKILL.md": {"sha": "1"}},
    )
    state_path.write_text(config.dump_state(seed), encoding="utf-8")

    def add_codex(state: config.State) -> None:
        state.packs[("research", "codex")] = config.PackState(
            installed_version="1.0.0", adapter="codex", scope="repo",
            files={".agents/skills/x/SKILL.md": {"sha": "2"}},
        )

    statelock.persist_state_locked(state_path, add_codex)

    reloaded = config.load_state(state_path)
    assert reloaded.has_pack("research")
    assert reloaded.adapters_for_pack("research") == ["claude-code", "codex"]
