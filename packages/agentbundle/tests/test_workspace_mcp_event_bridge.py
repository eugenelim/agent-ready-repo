"""Tests for _EventBridge — events.jsonl polling, inode tracking, seq deduplication."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


# Helper: locate workspace_mcp module
def _import_wsmcp():
    import importlib.util
    src = Path(__file__).resolve().parents[1] / "agentbundle" / "workspace_mcp.py"
    spec = importlib.util.spec_from_file_location("workspace_mcp", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestEventBridgePoll:
    """_EventBridge.run() picks up new events within 2 × poll interval."""

    def test_bridge_reads_new_event_within_poll_interval(self, tmp_path: Path) -> None:
        assert False  # STUB: AC3 — write an event to events.jsonl; confirm bridge picks it up within 2×200ms

    def test_bridge_byte_offset_tracks_position(self, tmp_path: Path) -> None:
        assert False  # STUB: AC3 — write two events; bridge must read only new bytes on second poll

    def test_bridge_seq_dedup_skips_lower_seq(self, tmp_path: Path) -> None:
        assert False  # STUB: AC4 — write seq=2 then replay seq=1; second event must not update state

    def test_bridge_gate_pending_set_on_human_gate_state(self, tmp_path: Path) -> None:
        assert False  # STUB: AC7 — to field ending "-HUMAN-GATE" → gate_pending=True


class TestEventBridgeInodeReset:
    """_EventBridge resets byte offset and state when inode changes (AC5)."""

    def test_bridge_resets_on_inode_change(self, tmp_path: Path) -> None:
        assert False  # STUB: AC5 — delete + recreate events.jsonl; bridge must reset to offset=0 and re-read

    def test_bridge_resets_on_truncation(self, tmp_path: Path) -> None:
        assert False  # STUB: AC5 variant — truncate existing file (st_size < offset); bridge must reset


class TestEventBridgeStop:
    """_EventBridge.stop() terminates the daemon thread."""

    def test_bridge_stop_exits_thread(self, tmp_path: Path) -> None:
        assert False  # STUB: AC3 — call stop(); confirm thread.is_alive() is False within 1 s
