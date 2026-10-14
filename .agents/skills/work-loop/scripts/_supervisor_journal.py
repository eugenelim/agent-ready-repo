"""_supervisor_journal — the supervisor's local, deletable state.

Nothing here is read for a decision. ``<spec>/.supervisor/`` holds the advisory
journal, ``run.json`` for the workspace bridge, the security-event audit log,
and the run lock; it ignores itself in Git. ``.loop-run/events.jsonl`` gets one
line per supervisor step, projected from supervisor commits, so a lost or
duplicated append is repaired at the next call.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_commit = _supervisor("_supervisor_commit.py")
Commit = _commit.Commit
ensure_directory = _commit.ensure_directory
kill_point = _commit.kill_point
sibling = _commit.sibling

__all__ = ["LocalState", "OPERATION_STAGE", "STAGES"]

STAGES = ("admitted", "implementing", "gating", "reviewing", "awaiting-human", "terminal")

# The stage a step of each operation leaves the run in. A replan keeps the stage.
OPERATION_STAGE: dict[str, str | None] = {
    "approval": "admitted",
    "replan": None,
    "stub": "implementing",
    "red": "implementing",
    "implement": "implementing",
    "gate-fail": "implementing",
    "evidence": "gating",
    "review": "reviewing",
    "effect-intent": "implementing",
    "effect-dispatch": "implementing",
    "effect-receipt": "implementing",
    "claim": "implementing",
    "resolution": "awaiting-human",
    "terminal": "terminal",
}
_MAX_LOCAL_BYTES = 64 * 1024 * 1024


class LocalState:
    """Local files for one spec directory."""

    def __init__(self, root: Path, spec_rel: str, *, clock: Callable[[], str]) -> None:
        self.root = root
        self.spec_rel = spec_rel
        self.clock = clock
        self.local_rel = f"{spec_rel}/.supervisor"
        self.run_json = root / self.local_rel / "run.json"
        self.journal = root / self.local_rel / "journal.jsonl"
        self.security_events = root / self.local_rel / "security-events.jsonl"
        self.lock_target = root / self.local_rel / "run"
        self.events = root / ".loop-run" / "events.jsonl"

    def ensure(self) -> None:
        """Create ``.supervisor/`` with a self-ignoring ``.gitignore``."""
        cm = sibling("_confined_mutation.py")
        directory = ensure_directory(self.root, self.local_rel)
        marker = directory / ".gitignore"
        if not marker.exists():
            cm.confined_create(self.root, marker, b"*\n")

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        cm = sibling("_confined_mutation.py")
        line = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if not path.exists():
            cm.confined_create(self.root, path, b"")
        cm.confined_append(self.root, path, line, max_bytes=_MAX_LOCAL_BYTES)

    def write_run(self, status: dict[str, Any]) -> None:
        """Replace ``run.json`` atomically."""
        self.ensure()
        cm = sibling("_confined_mutation.py")
        body = (json.dumps(status, indent=2, sort_keys=True) + "\n").encode("utf-8")
        cm.confined_atomic_replace(self.root, self.run_json, body)

    def append_journal(self, line: dict[str, Any]) -> None:
        """Append one advisory ``mechanical-journal.v1`` line."""
        self.ensure()
        self._append(self.journal, {"schema_version": 1, **line})
        kill_point("journal")

    def security_sink(self) -> Callable[[object], None]:
        """An audit sink that durably appends each security event locally."""

        def sink(event: object) -> None:
            if dataclasses.is_dataclass(event) and not isinstance(event, type):
                record: object = dataclasses.asdict(event)
            else:
                record = event
            if not isinstance(record, dict):
                raise OSError("security event must be a dataclass or a mapping")
            try:
                self.ensure()
                self._append(self.security_events, record)
            except OSError:
                raise
            except Exception as exc:  # noqa: BLE001 - any store failure fails closed
                raise OSError("security-event log unavailable") from exc

        return sink

    # ── events ──────────────────────────────────────────────────────────────

    def _recorded_steps(self, run_id: str) -> set[str]:
        fs = sibling("_file_safety.py")
        if not self.events.exists():
            return set()
        raw = bytes(
            fs.read_confined_regular_file(self.root, self.events, max_bytes=_MAX_LOCAL_BYTES)
        )
        steps = set()
        for line in raw.splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and record.get("run_id") == run_id:
                step = record.get("step_id")
                if isinstance(step, str):
                    steps.add(step)
        return steps

    def reconcile_events(self, run_id: str, commits: list[Commit]) -> None:
        """Append an event line for every reachable step that has none.

        The shared event log is advisory: when it is over the size bound or
        unreadable, the projection is skipped so it never stops a verb that
        commits delivery state, and a later call repairs it once it is readable.
        """
        try:
            recorded = self._recorded_steps(run_id)
        except (OSError, ValueError):
            return
        missing = [c for c in commits if c.step not in recorded]
        if not missing:
            return
        ensure_directory(self.root, ".loop-run")
        stage = "admitted"
        for seq, commit in enumerate(commits):
            before = stage
            stage = OPERATION_STAGE.get(commit.operation) or stage
            if commit.step in recorded:
                continue
            self._append(
                self.events,
                {
                    "schema": 1,
                    "seq": seq,
                    "run_id": run_id,
                    "spec": self.spec_rel,
                    "from": before,
                    "event": commit.operation,
                    "to": stage,
                    "at": commit.committed_at,
                    "awaiting_input": stage == "awaiting-human",
                    "step_id": commit.step,
                },
            )
            recorded.add(commit.step)
            kill_point("event")
