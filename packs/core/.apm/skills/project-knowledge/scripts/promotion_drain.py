"""Drain-side read half for the work-item promotion drain.

Spec: ``docs/specs/work-item-promotion-handoff/spec.md`` — the store's
drain-side reader. Every drain offer assembles from what this module returns:
the open work-item captures with their records and terminal state.

Read-only by construction. Every access goes through ``knowledge_store``'s
own confined read helpers, and no write path is reachable from here. A
record the store's read rules refuse — a malformed merged record, a capture
spread over two partitions — surfaces as the store's ``KnowledgeStoreError``
rather than being offered.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_knowledge_store() -> Any:
    """Load the sibling store module, the way its own siblings do."""
    spec = importlib.util.spec_from_file_location(
        "_project_knowledge_store_drain", SCRIPT_DIR / "knowledge_store.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("knowledge store module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


KS = _load_knowledge_store()


def read_open_captures(repo_root: Path | str) -> list[dict[str, Any]]:
    """Return every open work-item capture in the store, with its record.

    A capture is open when no ``observation.dispositioned`` event names its
    capture id. Only ``work-item`` captures are returned: the drain routes
    work items, and knowledge observations (pattern, gotcha, antipattern)
    belong to their own distillation path. Envelope-only records —
    disposition events, which carry no request payload — and dispositioned
    captures are never returned.

    A record the store's read rules refuse raises ``KnowledgeStoreError``
    from the store itself; the reader neither swallows the refusal nor
    offers the record. A capture id appearing in two partitions is refused
    the same way ``knowledge_store._find_capture`` refuses it. No store file
    is written, moved, or quarantined by this read.
    """
    root = KS.resolve_worktree_root(repo_root)
    captures: dict[str, dict[str, Any]] = {}
    home_partitions: dict[str, str] = {}
    for partition in KS._observation_partitions(root):
        events = KS._read_events(KS._journal_path(root, partition), partition)
        terminal = KS._terminal_capture_ids(events)
        for event in events:
            if event["event_type"] != KS._CAPTURED:
                continue
            if event["request"]["kind"] != "work-item":
                continue
            capture_id = event["capture_id"]
            home = home_partitions.get(capture_id)
            if home is not None and home != event["partition"]:
                # The same capture id in two partitions is store corruption
                # the store's own read path refuses; mirror it here.
                KS._refuse("postimage_mismatch")
            home_partitions[capture_id] = event["partition"]
            if capture_id in terminal:
                continue
            captures[capture_id] = {
                "capture_id": capture_id,
                "partition": event["partition"],
                "captured_at": event["captured_at"],
                "request": event["request"],
                "terminal_disposition": None,
            }
    return [
        captures[capture_id]
        for capture_id in sorted(
            captures,
            key=lambda capture_id: (
                captures[capture_id]["partition"],
                captures[capture_id]["captured_at"],
                capture_id,
            ),
        )
    ]
