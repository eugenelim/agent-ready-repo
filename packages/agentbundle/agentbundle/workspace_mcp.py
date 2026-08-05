"""agentbundle.workspace_mcp — per-session MCP server (Stage 1).

Entry points
------------
    python -m agentbundle.workspace_mcp      # module mode (production)
    python -I -m agentbundle.workspace_mcp   # isolated mode (CI / testing)
    python workspace_mcp_server.py           # core-pack alias wrapper

Spawned once per session by the Claude Code adapter (Class A). Provides:
  - workspace_status()  — DAG-resolved workspace queue + FSM state fields
  - elicit()            — route AI questions to the control plane
  - git_status / git_branch / git_commit / git_push — scoped git lifecycle

Design constraints (ADR-0062 through ADR-0069):
  - Per-session only; stdin close → process exit within 5 s (no port, no daemon).
  - Pure stdlib Python 3.11+; no new runtime dependencies.
  - events.jsonl polling; notifications generated but not relayed (spike (c)).
  - Daemon threads + bounded pool (max_workers=4).

Known limitation: the response-file O_EXCL guard does not prevent a same-uid
process from racing the creation window. Only use the response-file fallback on
known-incapable adapters (Codex, Kiro CLI); prefer elicitation/create.
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid as _uuid_mod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.WARNING,
    format="workspace-mcp: %(levelname)s %(message)s",
    stream=sys.stderr,
)
_log = logging.getLogger("workspace_mcp")

# ── Constants ─────────────────────────────────────────────────────────────────

_MCP_PROTOCOL_VERSION = "2025-06-18"
_FRAME_SIZE_LIMIT = 1 * 1024 * 1024  # 1 MiB
_GIT_TIMEOUT = 30  # seconds
_ELICIT_POLL_TIMEOUT = 300  # seconds
_PENDING_EVENTS_CAP = 1000  # max buffered events before overflow warning
_ELICIT_RESPONSE_KEY = "response"
_BRIDGE_POLL_INTERVAL = 0.2  # 200 ms

# Slug safety: ^[a-zA-Z0-9._-]+$, not "." or "..", not starting with "-"
_SAFE_SLUG_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

# ── Lifecycle manifest (ADR-0067 built-in defaults) ───────────────────────────
#
# Maps each initiative item type to its lifecycle metadata.
# NOT computed at runtime from workspace.toml — embedded constant per ADR-0067.
# workspace-types.d/ extension deferred to Stage 3.

_LIFECYCLE_MANIFEST: dict[str, dict] = {
    "work": {
        "dispatch_skill": "work-loop",
        "output_pattern": None,         # work-loop manages git itself
        "has_gates": True,
        "required_pack": "core",
    },
    "research": {
        "dispatch_skill": "desk-research-project-start",
        "output_pattern": ["docs/product/research/*-{slug}/**"],
        "has_gates": False,
        "required_pack": "desk-research",
    },
    "shape": {
        "dispatch_skill": "frame-intent",
        "output_pattern": [
            "docs/product/intents/{slug}.md",
            "docs/product/shaping/{slug}/**",
        ],
        "has_gates": False,
        "required_pack": "product-engineering",
    },
    "design": {
        "dispatch_skill": "journey-mapping",
        "output_pattern": [
            "docs/design/journeys/{slug}.md",
            "docs/design/blueprints/{slug}.md",
            "docs/design/screens/{slug}/**",
            "docs/design/screens/{slug}-flow.md",
        ],
        "has_gates": False,
        "required_pack": "experience-design",
    },
    "strategy": {
        "dispatch_skill": "frame-situation",
        "output_pattern": ["docs/product/shaping/{slug}/**"],
        "has_gates": False,
        "required_pack": "product-engineering",
    },
    "signal": {
        "dispatch_skill": None,
        "output_pattern": None,
        "has_gates": False,
        "required_pack": None,
    },
    "brief": {
        "dispatch_skill": "receive-brief",
        "output_pattern": None,
        "has_gates": False,
        "required_pack": None,
    },
}

# ── Session instruction (Component 3) ─────────────────────────────────────────

DEFAULT_SESSION_INSTRUCTION = """\
You are operating in a workspace managed by workspace-mcp. Follow these rules \
for this entire session — they apply to every turn, including follow-up user messages.

1. If the `workspace_status` tool is available, call workspace_status() at session \
start to understand the current queue before doing any work.

2. Do not call git commands (git commit, git push, git checkout, etc.) directly. \
Use the git_* tools provided by workspace-mcp. Exception: if you are running the \
work-loop skill and an active FSM run is underway, work-loop owns its git lifecycle \
directly — do not intercept or override its git operations via the git_* tools.

3. When you would ask the user a question, request approval, show options, or elicit \
any response — check if the `elicit` workspace-mcp tool is available. If it is, \
call elicit(message, context, options) and wait for the returned response instead \
of emitting text to the user.

4. The workspace-mcp tools remain available for the duration of the session.

5. Before writing artifacts for a non-FSM item (any item where work-loop is not \
managing the session), call git_branch(<ini_slug>/<type>/<slug>) if not already \
on the item's feature branch. Derive the three-component branch name from the \
ini_slug, type, and slug as reported by workspace_status() — `workspace_status().slug` \
and `workspace_status().ini_slug` are the canonical forms. Skip if the current \
branch name equals `<ini_slug>/<type>/<slug>` exactly.

6. When instructed to commit and push artifacts, call git_status() to identify \
uncommitted files, git_commit(message) to stage and commit the matching paths, then \
git_push(branch) if it is available. Do not skip steps that are available.\
"""

# ── Repo-root helper ──────────────────────────────────────────────────────────

_GIT_OVERRIDE_VARS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
})


def _git_env() -> dict[str, str]:
    """Return os.environ with git repository-override variables stripped."""
    return {k: v for k, v in os.environ.items() if k not in _GIT_OVERRIDE_VARS}


def _get_repo_root() -> Path:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", check=False,
        env=_git_env(), timeout=_GIT_TIMEOUT,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("could not determine repo root (git rev-parse --show-toplevel failed)")
    return Path(r.stdout.strip()).resolve()


# ── Slug safety ───────────────────────────────────────────────────────────────

def _is_safe_slug(segment: str) -> bool:
    """Return True if segment is safe to embed in a path glob."""
    if not _SAFE_SLUG_RE.match(segment):
        return False
    if segment in (".", ".."):
        return False
    return not segment.startswith("-")


# ── Pack-presence probe ───────────────────────────────────────────────────────

_SKILL_ROOTS: list[str] = [
    ".claude/skills/{skill}/SKILL.md",
    ".agents/skills/{skill}/SKILL.md",
    ".kiro/skills/{skill}/SKILL.md",
]
_USER_SKILL_ROOTS: list[str] = [
    str(Path.home() / ".claude/skills/{skill}/SKILL.md"),
    str(Path.home() / ".agents/skills/{skill}/SKILL.md"),
    str(Path.home() / ".kiro/skills/{skill}/SKILL.md"),
]


def _is_skill_present(dispatch_skill: str | None, repo_root: Path) -> bool:
    """Return True if dispatch_skill's SKILL.md exists in any of the 6 probe roots."""
    if dispatch_skill is None:
        return False
    for tmpl in _SKILL_ROOTS:
        path = repo_root / tmpl.format(skill=dispatch_skill)
        if path.exists():
            return True
    for tmpl in _USER_SKILL_ROOTS:
        path = Path(tmpl.format(skill=dispatch_skill))
        if path.exists():
            return True
    return False


# ── workspace_status_engine discovery ────────────────────────────────────────

def _load_workspace_status_engine(repo_root: Path):
    """Import workspace_status_engine from the projected adapter skills directory."""
    import importlib.util

    # Checkout-relative paths are valid for trusted-repo sessions only. When running
    # in isolated mode (`python -I`), skip them — a malicious checkout could replace
    # these scripts and defeat the -I isolation guarantee. Stage 1 targets trusted-repo
    # sessions; untrusted-repo (-I) use requires the engine to ship with the package.
    candidates: list[Path] = []
    if not sys.flags.isolated:
        candidates = [
            repo_root / ".claude/skills/workspace-status/scripts/workspace_status_engine.py",
            repo_root / ".agents/skills/workspace-status/scripts/workspace_status_engine.py",
            repo_root / ".kiro/skills/workspace-status/scripts/workspace_status_engine.py",
        ]
    # Package-relative source path (development / pre-build-self; also the only
    # candidate in isolated mode, where __file__ is inside site-packages):
    candidates.append(
        Path(__file__).resolve().parents[3]
        / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
    )
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("workspace_status_engine", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["workspace_status_engine"] = mod
            spec.loader.exec_module(mod)
            return mod
    if sys.flags.isolated:
        raise RuntimeError(
            "workspace_status_engine.py not found — Stage 1 requires trusted-repo mode "
            "(do not use python -I; run agentbundle install core to set up adapter "
            "projections). Isolated-module untrusted-repo support is deferred to Stage 2."
        )
    raise RuntimeError("workspace_status_engine.py not found in any skill root")


# ── _EventBridge ──────────────────────────────────────────────────────────────

class _EventBridge(threading.Thread):
    """Daemon thread: polls .loop-run/events.jsonl every 200 ms.

    Tracks byte offset + inode for torn-write recovery and inode-change reset.
    Maintains internal FSM state (current_state, gate fields) for workspace_status().
    Notifications are generated but NOT relayed to ACP (spike (c) fallback).
    """

    def __init__(
        self,
        repo_root: Path,
        spec_dir: Path | None = None,
        notify_fn=None,
        mcp_initialized: threading.Event | None = None,
    ) -> None:
        super().__init__(daemon=True)
        self._repo_root = repo_root
        self._jsonl_path = repo_root / ".loop-run" / "events.jsonl"
        self._spec_dir = spec_dir
        self._lock = threading.Lock()
        # callable(dict) → None; called outside lock after _apply_event
        self._notify_fn = notify_fn
        # Gate notification emission until the MCP initialize handshake completes.
        self._mcp_initialized = mcp_initialized

        # Tracking state
        self._offset: int = 0
        self._inode: int | None = None
        self._buf: str = ""
        self._last_seq: int = -1
        self._bound_run_id: str | None = None  # lazily bound from engine-state.json
        self._pending_events: list[dict] = []  # buffered until run_id is known
        self._buffer_overflow: bool = False

        # FSM state (exposed via workspace_status)
        self._current_state: str | None = None
        self._gate_pending: bool = False
        self._gate: str | None = None
        self._gate_question: str | None = None
        self._review_findings: str | None = None
        self._gate_seq: int = -1  # transition seq when current gate was entered

        self._shutdown = threading.Event()

    def stop(self) -> None:
        self._shutdown.set()

    def has_anchored_engine_state(self) -> bool:
        """Return True when an anchored engine-state.json is present."""
        return bool(self._spec_dir and (self._spec_dir / "engine-state.json").exists())

    def _read_anchored_run_id(self) -> str | None:
        """Read run_id from the anchored spec's engine-state.json; None on failure."""
        if self._spec_dir is None:
            return None
        try:
            data = json.loads(
                (self._spec_dir / "engine-state.json").read_text(encoding="utf-8")
            )
            return data.get("run_id") or None
        except Exception:
            return None

    def get_fsm_state(self) -> dict:
        with self._lock:
            state: dict = {
                "current_state": self._current_state,
                "gate_pending": self._gate_pending,
                "gate": self._gate,
                "gate_seq": self._gate_seq,
                "gate_question": self._gate_question,
                "review_findings": self._review_findings,
                "run_id": self._bound_run_id,
            }
            if self._buffer_overflow:
                state["warning"] = "EVENTS-BUFFER-OVERFLOW"
            return state

    def _reset_file_state(self) -> None:
        self._offset = 0
        self._inode = None
        self._buf = ""
        self._last_seq = -1  # reset so new run's seq=1 is not filtered as duplicate
        self._bound_run_id = None  # re-bind run_id from engine-state.json on next poll
        self._pending_events = []  # discard buffered events from previous run
        self._buffer_overflow = False
        self._current_state = None
        self._gate_pending = False
        self._gate = None
        self._gate_question = None
        self._review_findings = None
        self._gate_seq = -1

    def _bootstrap_from_engine_state(self) -> None:
        """Sync FSM state from engine-state.json when events.jsonl is caught up.

        Called while the lock is already held. Handles two cases:
        1. Window between loop-engine init (empty events.jsonl) and the first transition.
        2. Graceful-degradation path: events.jsonl append failed after the atomic
           engine-state write, so the file is caught up but FSM state is stale.
        In both cases, apply only if engine-state has a higher seq than last seen.
        """
        if self._spec_dir is None:
            return
        try:
            data = json.loads(
                (self._spec_dir / "engine-state.json").read_text(encoding="utf-8")
            )
        except Exception:
            return
        state_val = data.get("state")
        if not state_val:
            return
        es_seq = int(data.get("transition_sequence", -1))
        if es_seq <= self._last_seq:
            return  # engine-state not ahead; nothing to apply
        self._bound_run_id = data.get("run_id") or self._bound_run_id
        self._current_state = state_val
        self._gate_pending = bool(state_val and state_val.endswith("-HUMAN-GATE"))
        self._gate = state_val if self._gate_pending else None
        self._gate_question = data.get("gate_question")
        if self._gate_pending:
            self._gate_seq = es_seq
            self._review_findings = self._read_review_findings()
        else:
            self._gate_seq = -1
            self._review_findings = None

    def run(self) -> None:
        while not self._shutdown.is_set():
            try:
                self._poll()
            except Exception as exc:
                _log.warning("EventBridge poll error: %s", exc)
            self._shutdown.wait(timeout=_BRIDGE_POLL_INTERVAL)

    def _poll(self) -> None:
        path = self._jsonl_path
        _notifications: list[dict] = []
        if not path.exists():
            # Events file missing (loop-engine reset or not yet started).
            # Reset all FSM state so workspace_status() doesn't return stale gate/state.
            with self._lock:
                if self._current_state is not None or self._gate_pending:
                    self._reset_file_state()
                    self._current_state = None
                    self._gate_pending = False
                    self._gate = None
                    self._gate_seq = -1
                    self._gate_question = None
                    self._review_findings = None
            return

        try:
            st = path.stat()
        except OSError:
            return

        with self._lock:
            # Inode change or truncation → reset
            if self._inode != st.st_ino or st.st_size < self._offset:
                self._reset_file_state()
                self._inode = st.st_ino

            if st.st_size == self._offset:
                # File caught up — sync from engine-state.json if it is ahead.
                # Covers two cases: (a) initial window before first transition;
                # (b) graceful-degradation path where append failed after the atomic
                # engine-state write, leaving events.jsonl size unchanged while
                # engine-state.json has a newer seq.
                if self._spec_dir is not None:
                    _was_bound = self._bound_run_id
                    self._bootstrap_from_engine_state()
                    # If bootstrap just established a run binding, drain any events that
                    # were buffered while _read_anchored_run_id() was unavailable.
                    if _was_bound is None and self._bound_run_id is not None:
                        for ev in self._pending_events:
                            if ev.get("run_id") != self._bound_run_id:
                                continue
                            s = ev.get("seq")
                            if s is None or s <= self._last_seq:
                                continue
                            self._last_seq = s
                            _notifications.extend(self._apply_event(ev))
                        self._pending_events.clear()
                # Fall through (no return) so _notifications are emitted below.
            else:
                try:
                    with path.open("r", encoding="utf-8") as fh:
                        fh.seek(self._offset)
                        chunk = fh.read(st.st_size - self._offset)
                except OSError:
                    chunk = ""  # emit any notifications accumulated before the error

                self._inode = st.st_ino
                self._offset += len(chunk.encode("utf-8"))
                self._buf += chunk

            # Lazily bind run_id from engine-state.json. Until bound, events are
            # buffered rather than applied so historical foreign-run events cannot
            # update FSM state or advance _last_seq before the anchored run is known.
            if self._bound_run_id is None:
                self._bound_run_id = self._read_anchored_run_id()
                if self._bound_run_id is not None:
                    # Replay buffered events that belong to the now-known run_id.
                    for ev in self._pending_events:
                        if ev.get("run_id") != self._bound_run_id:
                            continue
                        s = ev.get("seq")
                        if s is None or s <= self._last_seq:
                            continue
                        self._last_seq = s
                        _notifications.extend(self._apply_event(ev))
                    self._pending_events.clear()

            # Process complete lines; hold any partial line.
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    _log.warning("EventBridge: malformed event line; skipping")
                    continue
                if self._bound_run_id is None:
                    # run_id not yet known — buffer without applying
                    if len(self._pending_events) >= _PENDING_EVENTS_CAP:
                        self._buffer_overflow = True
                        _log.warning("EventBridge: pending buffer cap reached; dropping event")
                        continue
                    self._pending_events.append(event)
                    continue
                # Discard foreign-run events once run_id is bound
                if event.get("run_id") != self._bound_run_id:
                    continue
                seq = event.get("seq")
                if seq is None or seq <= self._last_seq:
                    continue  # dedup
                self._last_seq = seq
                _notifications.extend(self._apply_event(event))

        # Emit notifications only after MCP initialization completes.
        # Custom server notifications are invalid during the initialize handshake.
        mcp_ready = self._mcp_initialized is None or self._mcp_initialized.is_set()
        if self._notify_fn is not None and mcp_ready:
            for notif in _notifications:
                with contextlib.suppress(Exception):
                    self._notify_fn(notif)

    def _apply_event(self, event: dict) -> list[dict]:
        """Update FSM state and return MCP notifications to emit outside the lock."""
        to_state = event.get("to", "")
        seq = int(event.get("seq", -1))
        run_id = self._bound_run_id
        self._current_state = to_state
        notifications: list[dict] = [
            {
                "jsonrpc": "2.0",
                "method": "_agentbundle.core/skill-state-change",
                # Full seven-field event payload per design.md notification contract.
                "params": {
                    "seq": seq,
                    "run_id": run_id,
                    "spec": event.get("spec"),
                    "from": event.get("from"),
                    "event": event.get("event"),
                    "to": to_state,
                    "at": event.get("at"),
                },
            }
        ]
        if to_state.endswith("-HUMAN-GATE"):
            self._gate_pending = True
            self._gate = to_state
            self._gate_seq = seq
            self._gate_question = self._read_gate_question()
            self._review_findings = self._read_review_findings()
            notifications.append({
                "jsonrpc": "2.0",
                "method": "_agentbundle.core/human-gate-pending",
                "params": {
                    "gate": to_state,
                    "question": self._gate_question,
                    "spec_path": str(self._spec_dir) if self._spec_dir else None,
                    "review_findings": self._review_findings,
                    "run_id": run_id,
                    "seq": seq,
                },
            })
        else:
            self._gate_pending = False
            self._gate = None
            self._gate_seq = -1
            self._gate_question = None
            self._review_findings = None
        return notifications

    def _read_gate_question(self) -> str | None:
        if self._spec_dir is None:
            return None
        state_path = self._spec_dir / "engine-state.json"
        with contextlib.suppress(Exception):
            data = json.loads(state_path.read_text(encoding="utf-8"))
            return data.get("gate_question")
        return None

    def _read_review_findings(self) -> str | None:
        if self._spec_dir is None:
            return None
        # Look for the most recent reviewer report file in the spec dir
        for name in ("review-report.md", "adversarial-report.md"):
            candidate = self._spec_dir / name
            if candidate.exists():
                with contextlib.suppress(Exception):
                    return candidate.read_text(encoding="utf-8")
        return None


# ── _WorkspaceStatusTool ──────────────────────────────────────────────────────

class _WorkspaceStatusTool:
    """Implements the workspace_status() MCP tool.

    Calls workspace_status_engine.analyze_bounded(repo_root, autonomous_dispatch=True).
    Applies pack-presence filter (6 roots, OR logic) and slug safety guard.
    Also exposes FSM state fields from _EventBridge (spike (c) fallback).
    """

    def __init__(self, repo_root: Path, bridge: _EventBridge) -> None:
        self._repo_root = repo_root
        self._bridge = bridge
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = _load_workspace_status_engine(self._repo_root)
        return self._engine

    def call(self) -> dict:
        from agentbundle.safety import assert_under
        repo_root = self._repo_root

        # Check for events.jsonl (spike (c) fallback).
        # Warn when events.jsonl is missing but observability was expected: either
        # .loop-run/ exists (partial teardown) or engine-state.json is anchored
        # (graceful-degradation: loop-engine wrote engine state but not the events dir).
        jsonl_path = repo_root / ".loop-run" / "events.jsonl"
        fsm_state = self._bridge.get_fsm_state()
        if not jsonl_path.exists() and (
            (repo_root / ".loop-run").exists() or self._bridge.has_anchored_engine_state()
        ):
            fsm_state["warning"] = "EVENTS-FILE-MISSING"

        try:
            engine = self._get_engine()
            result = engine.analyze_bounded(repo_root, autonomous_dispatch=True)
        except Exception as exc:
            _log.warning("workspace_status: analyze_bounded failed: %s", exc)
            return {"error": f"workspace_status analysis failed: {exc}", **fsm_state}

        ready_items: list[dict] = []
        blocked_items: list[dict] = []
        shaping_items: list[dict] = []
        active_items: list[dict] = []

        # Active work items (AC8: "active" key)
        for ini in result.initiatives:
            if ini.status not in ("active",):
                continue
            for entry in ini.work.active:
                if not _is_safe_slug(ini.slug) or not _is_safe_slug(entry.slug):
                    _log.warning("workspace_status: unsafe slug in active item; skipping")
                    continue
                manifest = _LIFECYCLE_MANIFEST.get("work", {})
                active_items.append({
                    "ini_slug": ini.slug,
                    "type": "work",
                    "slug": entry.slug,
                    "dispatch_skill": manifest.get("dispatch_skill"),
                    "output_pattern": manifest.get("output_pattern"),
                    "has_gates": manifest.get("has_gates", False),
                    "required_pack": manifest.get("required_pack"),
                })

        # Work queue items (ready / blocked)
        for cls in result.ready:
            entry = cls.entry
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.slug):
                _log.warning("workspace_status: unsafe slug in ready item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get("work", {})
            item: dict[str, Any] = {
                "ini_slug": cls.ini_slug,
                "type": "work",
                "slug": entry.slug,
                "dispatch_skill": manifest.get("dispatch_skill"),
                "output_pattern": manifest.get("output_pattern"),
                "has_gates": manifest.get("has_gates", False),
                "required_pack": manifest.get("required_pack"),
            }
            skill = manifest.get("dispatch_skill")
            if skill and not _is_skill_present(skill, repo_root):
                item["available"] = False
            ready_items.append(item)

        for cls in result.blocked:
            entry = cls.entry
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.slug):
                _log.warning("workspace_status: unsafe slug in blocked item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get("work", {})
            item = {
                "ini_slug": cls.ini_slug,
                "type": "work",
                "slug": entry.slug,
                "dispatch_skill": manifest.get("dispatch_skill"),
                "output_pattern": manifest.get("output_pattern"),
                "has_gates": manifest.get("has_gates", False),
                "required_pack": manifest.get("required_pack"),
                "unmet_needs": cls.blocking_needs,
            }
            blocked_items.append(item)

        # Shaping items (ready + blocked, excluding signals)
        for cls in result.blocked_shaping:
            entry = cls.entry
            item_type = entry.entry_type
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.slug):
                _log.warning("workspace_status: unsafe slug in blocked shaping item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get(item_type, {})
            item = {
                "ini_slug": cls.ini_slug,
                "type": item_type,
                "slug": entry.slug,
                "dispatch_skill": manifest.get("dispatch_skill"),
                "output_pattern": manifest.get("output_pattern"),
                "has_gates": manifest.get("has_gates", False),
                "required_pack": manifest.get("required_pack"),
                "unmet_needs": cls.blocking_needs,
            }
            skill = manifest.get("dispatch_skill")
            if skill and not _is_skill_present(skill, repo_root):
                item["available"] = False
            shaping_items.append(item)

        for cls in result.ready_shaping:
            entry = cls.entry
            item_type = entry.entry_type
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.slug):
                _log.warning("workspace_status: unsafe slug in shaping item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get(item_type, {})
            item = {
                "ini_slug": cls.ini_slug,
                "type": item_type,
                "slug": entry.slug,
                "dispatch_skill": manifest.get("dispatch_skill"),
                "output_pattern": manifest.get("output_pattern"),
                "has_gates": manifest.get("has_gates", False),
                "required_pack": manifest.get("required_pack"),
            }
            skill = manifest.get("dispatch_skill")
            if skill and not _is_skill_present(skill, repo_root):
                item["available"] = False
            # Slug containment check for output_pattern formatting
            patterns = manifest.get("output_pattern")
            if patterns:
                static_base = repo_root
                for pattern in (patterns if isinstance(patterns, list) else [patterns]):
                    try:
                        resolved = (repo_root / pattern.format(slug=entry.slug)).resolve()
                        assert_under(static_base, resolved)
                    except Exception as exc:
                        _log.warning(
                            "workspace_status: slug containment failed for %s:%s (%s); skipping",
                            item_type, entry.slug, exc,
                        )
                        break
                else:
                    shaping_items.append(item)
                    continue
            else:
                shaping_items.append(item)

        return {
            "ready": ready_items,
            "shaping": shaping_items,
            "blocked": blocked_items,
            "active": active_items,
            **fsm_state,
        }


# ── _ElicitTool ───────────────────────────────────────────────────────────────

class _ElicitTool:
    """Implements elicit() — routes questions to the control plane.

    Delivery path selected at init-handshake time:
      - elicitation/create path (AC11): when client declares elicitation capability
      - response-file fallback (AC12): when elicitation is absent from client capabilities

    The response-file path is used only for known-incapable adapters (Codex, Kiro CLI).
    Its same-OS-user limitation (O_EXCL does not prevent same-uid racing) is documented.
    """

    def __init__(
        self,
        has_elicitation: bool,
        shutdown_event: threading.Event,
        request_map: dict,           # {str(request_id): threading.Event | queue}
        write_lock: threading.Lock,
        write_fn,                    # callable(dict) → None
        session_id: str = "",
        get_gate_fn=None,            # callable() → str | None — returns pending gate id
    ) -> None:
        self._has_elicitation = has_elicitation
        self._shutdown = shutdown_event
        self._request_map = request_map
        self._write_lock = write_lock
        self._write = write_fn
        self._session_id = session_id
        self._get_gate = get_gate_fn
        self._consumed_gate_key: tuple | None = None  # (gate, gate_seq) when last consumed
        self._tmp_dir: Path | None = None
        self._elicit_seq = 0
        self._seq_lock = threading.Lock()

    def setup_response_dir(self) -> None:
        """Create secure temp dir (0700) for response-file fallback."""
        if not self._has_elicitation:
            tmp = tempfile.mkdtemp()
            Path(tmp).chmod(stat.S_IRWXU)
            self._tmp_dir = Path(tmp)

    def cleanup(self) -> None:
        import shutil
        if self._tmp_dir and self._tmp_dir.exists():
            with contextlib.suppress(Exception):
                shutil.rmtree(self._tmp_dir)

    def call(self, arguments: dict) -> dict:
        message = arguments.get("message", "")
        context = arguments.get("context")
        options = arguments.get("options")

        with self._seq_lock:
            self._elicit_seq += 1
            seq = self._elicit_seq

        if self._has_elicitation:
            return self._call_via_elicitation(message, context, options, seq)
        return self._call_via_response_file(message, context, options, seq)

    def _call_via_elicitation(
        self, message: str, context: Any, options: Any, seq: int
    ) -> dict:
        """Send elicitation/create to client; block until response arrives."""
        request_id = str(_uuid_mod.uuid4())
        result_event = threading.Event()
        result_holder: list[Any] = []
        self._request_map[request_id] = (result_event, result_holder)

        # Encode choices in requestedSchema when options are provided (AC11).
        if options:
            resp_schema: dict = {
                "type": "string",
                "enum": [str(o) for o in options],
            }
        else:
            resp_schema = {"type": "string"}
        # Append context to message so it reaches the human via the native path (AC11).
        full_message = f"{message}\n\nContext: {context}" if context else message
        req = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "elicitation/create",
            "params": {
                "message": full_message,
                "requestedSchema": {
                    "type": "object",
                    "properties": {"response": resp_schema},
                },
            },
        }

        # _write already holds write_lock internally; do not re-acquire here
        # (re-acquiring a non-reentrant Lock from the same thread deadlocks).
        self._write(req)

        # Wait for response from the client (bounded by _ELICIT_POLL_TIMEOUT).
        deadline = time.monotonic() + _ELICIT_POLL_TIMEOUT
        while not self._shutdown.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                del self._request_map[request_id]
                return {"error": "elicitation timed out (no response within 300 s)"}
            if result_event.wait(timeout=min(1.0, remaining)):
                break
        else:
            del self._request_map[request_id]
            return {"error": "elicitation cancelled: session shutting down"}

        del self._request_map[request_id]
        if result_holder:
            return {"response": result_holder[0]}
        return {"error": "elicitation produced no response"}

    def _call_via_response_file(
        self, message: str, context: Any, options: Any, seq: int
    ) -> dict:
        """Response-file fallback (AC12): O_EXCL creation, 300s poll timeout."""
        if self._tmp_dir is None:
            return {"error": "response-file directory not initialised"}

        response_path = self._tmp_dir / f"elicit-{seq}.json"
        # Create with O_EXCL (0600) — raises FileExistsError if pre-seeded
        try:
            fd = os.open(str(response_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, json.dumps({"question": message}).encode())
            os.close(fd)
        except FileExistsError:
            return {"error": "response file already exists; possible pre-seed attempt"}
        except OSError as exc:
            return {"error": f"could not create response file: {exc}"}

        # Derive correlation_id: set to the pending gate state when this is the
        # first elicitation for that gate entry; null for subsequent informal questions.
        # Use (gate, gate_seq) as the key so re-entering the same gate state after
        # blocker-applied correctly sets correlation_id again (FSM allows re-entry).
        gate_state = self._get_gate() if self._get_gate is not None else None
        gate_key: tuple | None = None
        if gate_state is not None:
            # get_gate_fn returns the full fsm_state dict; include run_id so
            # a reset+reinit in the same MCP session gets a fresh key even if
            # the gate name and seq happen to match the previous run.
            if isinstance(gate_state, dict):
                gate_key = (
                    gate_state.get("run_id"),
                    gate_state.get("gate"),
                    gate_state.get("gate_seq", -1),
                )
                gate_id = gate_state.get("gate")
            else:
                gate_id = gate_state
                gate_key = (None, gate_state, -1)
        else:
            gate_id = None
        correlation_id = gate_id if gate_id and gate_key != self._consumed_gate_key else None

        # Notify the control plane where to write the answer before blocking.
        # Method name and payload per design.md:346 (ADR-0068 namespace).
        self._write({
            "jsonrpc": "2.0",
            "method": "_agentbundle.core/elicitation-pending",
            "params": {
                "message": message,
                "context": context,
                "options": options,
                "session_id": self._session_id,
                "elicit_seq": seq,
                "correlation_id": correlation_id,
                "response_path": str(response_path),
            },
        })

        # Poll until overwritten by control plane (temp-and-rename protocol)
        deadline = time.monotonic() + _ELICIT_POLL_TIMEOUT
        while time.monotonic() < deadline:
            if self._shutdown.is_set():
                return {"error": "elicitation cancelled: session shutting down"}
            with contextlib.suppress(Exception):
                raw = response_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                if _ELICIT_RESPONSE_KEY in data:
                    # Mark gate elicitation consumed so subsequent informal questions
                    # in the same gate carry correlation_id=None (design.md:351).
                    if correlation_id is not None:
                        self._consumed_gate_key = gate_key
                    return {"response": data[_ELICIT_RESPONSE_KEY]}
            time.sleep(0.5)

        return {"error": "elicitation timed out (no response within 300 s)"}


# ── _GitTools ─────────────────────────────────────────────────────────────────

class _GitTools:
    """Implements git_status, git_branch, git_commit, git_push (AC14, AC15).

    Discovery mode (no WORKSPACE_MCP_SPEC_PATH or WORKSPACE_MCP_DISPATCHED_ITEM):
      - git_status allowed
      - git_branch, git_commit, git_push → error

    Injection defence:
      - git_branch: check-ref-format --branch form (rejects names starting with "-")
      - git_commit: paths intersected with output_pattern; stages via git add -- <paths>
      - git_push: two-sided branch check + git push -- origin <branch>
      - All subprocess calls: shell=False, timeout=30
    """

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        spec_path = os.environ.get("WORKSPACE_MCP_SPEC_PATH")
        # Capture raw env presence BEFORE validation: FSM mode is determined by
        # whether the operator SUPPLIED WORKSPACE_MCP_SPEC_PATH, not whether it
        # passes path validation.  An invalid path still activates the FSM guard
        # (fail-closed); git writes are blocked even if spec anchoring fails.
        _spec_path_supplied = bool(spec_path)
        dispatched = os.environ.get("WORKSPACE_MCP_DISPATCHED_ITEM")
        # Validate spec_path: must resolve inside repo_root. An out-of-repo or malformed
        # path is treated as absent for event-bridge anchoring only — FSM mode
        # is already locked by _spec_path_supplied above.
        if spec_path:
            try:
                if not Path(spec_path).resolve().is_relative_to(repo_root.resolve()):
                    _log.warning(
                        "WORKSPACE_MCP_SPEC_PATH %r outside repo_root; treating as absent",
                        spec_path,
                    )
                    spec_path = None
            except Exception as _e:
                _log.warning(
                    "WORKSPACE_MCP_SPEC_PATH validation failed (%s); treating as absent", _e
                )
                spec_path = None
        # Validate dispatched: if it fails to parse into a known type, treat as absent.
        self._output_pattern: list[str] | None = self._resolve_output_pattern(dispatched)
        if dispatched and self._output_pattern is None:
            _log.warning(
                "WORKSPACE_MCP_DISPATCHED_ITEM %r is malformed or uses unknown type; "
                "treating as absent — git writes are blocked",
                dispatched,
            )
            dispatched = None
        self._discovery_mode = not spec_path and not dispatched
        # FSM mode: WORKSPACE_MCP_SPEC_PATH was supplied → FSM mode, regardless of
        # whether it passed validation (fail-closed: invalid path still blocks git
        # writes).  When BOTH env vars are supplied (unsupported per the one-variable
        # contract), SPEC_PATH wins and a startup warning is logged.
        if _spec_path_supplied and dispatched is not None:
            _log.warning(
                "Both WORKSPACE_MCP_SPEC_PATH and WORKSPACE_MCP_DISPATCHED_ITEM are set "
                "(unsupported); WORKSPACE_MCP_SPEC_PATH takes precedence — "
                "FSM mode active, git writes blocked"
            )
        self._fsm_mode = _spec_path_supplied
        # Expected branch from dispatched item (ini_slug/type:slug → ini_slug/type/slug)
        self._expected_branch: str | None = self._derive_expected_branch(dispatched)
        self._session_branch: str | None = self._read_head_branch()
        # Once git_branch() sets the work branch, no subsequent call may rebind it.
        # This prevents progressive rebinding across multiple git_branch() calls from
        # widening the push target beyond the immutable session-bound branch (AC14).
        # Pre-lock in two situations:
        # 1. Resumed session: HEAD is already on the expected dispatched branch.
        # 2. FSM mode without DISPATCHED_ITEM: lock to startup HEAD so the session
        #    cannot redirect git_push to an arbitrary caller-chosen ref (AC14).
        self._branch_locked = (
            # Case 1: resumed dispatched session
            (self._expected_branch is not None
             and self._session_branch == self._expected_branch)
            # Case 2: FSM mode (SPEC_PATH supplied); lock to startup HEAD so the
            # session cannot redirect git_push to an arbitrary caller-chosen ref.
            # _fsm_mode blocks mutating tools anyway; this lock is belt-and-suspenders.
            or (_spec_path_supplied and self._session_branch is not None)
        )
        # Serialize all mutating git operations: prevents index.lock collisions
        # and TOCTOU races on _session_branch between concurrent tool calls.
        self._git_lock = threading.Lock()
        # Track active Popen objects for forced-exit cleanup (F15 / AC22).
        self._procs_lock = threading.Lock()
        self._active_procs: list[subprocess.Popen] = []
        # Set True by block_new_procs() before terminate_all_procs() to prevent
        # worker threads from spawning git children after the snapshot is taken.
        self._no_new_procs: bool = False

    def block_new_procs(self) -> None:
        """Prevent new git subprocesses. Call before terminate_all_procs() on shutdown."""
        with self._procs_lock:
            self._no_new_procs = True

    def terminate_all_procs(self, grace: float = 3.0) -> None:
        """Terminate tracked git process groups; called by the force-exit timer.

        Each _run_git() process was started with start_new_session=True, placing it
        (and any hooks it spawns) in a fresh process group. SIGTERM is sent to the
        whole group, followed by a bounded grace period, then SIGKILL for survivors.
        """
        with self._procs_lock:
            # Set flag atomically with the snapshot so _run_git cannot slip a new
            # process in after we've snapshotted but before we've set the flag.
            self._no_new_procs = True
            procs = list(self._active_procs)
        # With start_new_session=True, proc.pid == pgid at spawn time; use it
        # directly to avoid os.getpgid() failing if the process has already exited.
        pgids: set[int] = {proc.pid for proc in procs}
        _killpg = getattr(os, "killpg", None)
        if _killpg is not None:
            for pgid in pgids:
                with contextlib.suppress(Exception):
                    _killpg(pgid, signal.SIGTERM)
        else:
            for proc in procs:
                with contextlib.suppress(Exception):
                    proc.terminate()
        # Wait up to grace seconds for each tracked process to exit.
        deadline = time.monotonic() + grace
        for proc in procs:
            remaining = max(0.0, deadline - time.monotonic())
            with contextlib.suppress(Exception):
                proc.wait(timeout=remaining)
        # SIGKILL any surviving process groups (POSIX) or kill each process (Windows).
        if _killpg is not None:
            for pgid in pgids:
                with contextlib.suppress(Exception):
                    _killpg(pgid, signal.SIGKILL)
        else:
            for proc in procs:
                with contextlib.suppress(Exception):
                    proc.kill()

    def _run_git(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        """subprocess.Popen wrapper that tracks processes for forced-exit cleanup.

        Popen-incompatible subprocess.run() kwargs (timeout, text, encoding, check,
        capture_output) are stripped from the Popen call; timeout is used only for
        communicate() and encoding is used only when decoding the returned bytes.
        start_new_session=True isolates git and its hooks in their own process group
        so terminate_all_procs() can send SIGTERM to the whole group.
        """
        _POPEN_ONLY_EXCLUDE = frozenset({"timeout", "text", "encoding", "check", "capture_output"})
        timeout = kwargs.get("timeout", _GIT_TIMEOUT)
        encoding = kwargs.get("encoding", "utf-8")
        popen_kwargs = {k: v for k, v in kwargs.items() if k not in _POPEN_ONLY_EXCLUDE}
        popen_kwargs.setdefault("start_new_session", True)
        popen_kwargs.setdefault("env", _git_env())
        # Flag check, Popen creation, and registration are all under _procs_lock so
        # terminate_all_procs() cannot snapshot _active_procs between the check and
        # the registration, leaving the new process untracked for forced-exit cleanup.
        with self._procs_lock:
            if self._no_new_procs:
                raise RuntimeError("git subprocess creation blocked: session is shutting down")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **popen_kwargs,
            )
            # With start_new_session=True the spawned process is its own group
            # leader, so proc.pid == pgid at spawn time.  Capture before communicate()
            # so the PGID remains valid even after the Git parent exits (e.g. when a
            # daemonised hook inherits the output pipes).
            _pgid: int = proc.pid
            self._active_procs.append(proc)
        # Lock released; communicate() can block indefinitely, so it must run outside.
        try:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                # POSIX: kill the entire process group so hook children holding
                # the pipes also die.  Windows: fall back to per-process termination
                # (start_new_session=True isolates the child but killpg is absent).
                _killpg = getattr(os, "killpg", None)
                if _killpg is not None:
                    with contextlib.suppress(Exception):
                        _killpg(_pgid, signal.SIGTERM)
                    _kg_deadline = time.monotonic() + 2.0
                    with contextlib.suppress(Exception):
                        proc.wait(timeout=max(0.0, _kg_deadline - time.monotonic()))
                    with contextlib.suppress(Exception):
                        _killpg(_pgid, signal.SIGKILL)
                else:
                    with contextlib.suppress(Exception):
                        proc.terminate()
                    with contextlib.suppress(Exception):
                        proc.wait(timeout=2.0)
                    with contextlib.suppress(Exception):
                        proc.kill()
                stdout, stderr = proc.communicate(timeout=5)
        finally:
            with self._procs_lock, contextlib.suppress(ValueError):
                self._active_procs.remove(proc)
        return subprocess.CompletedProcess(
            args=proc.args,
            returncode=proc.returncode,
            stdout=stdout.decode(encoding, errors="replace"),
            stderr=stderr.decode(encoding, errors="replace"),
        )

    def _derive_expected_branch(self, dispatched: str | None) -> str | None:
        """Return ini_slug/type/slug from WORKSPACE_MCP_DISPATCHED_ITEM, or None."""
        if dispatched is None:
            return None
        try:
            ini_slug, rest = dispatched.split("/", 1)
            item_type, slug = rest.split(":", 1)
            return f"{ini_slug}/{item_type}/{slug}"
        except ValueError:
            return None

    def _resolve_output_pattern(self, dispatched: str | None) -> list[str] | None:
        if dispatched is None:
            return None
        # dispatched = "ini_slug/type:slug"
        try:
            ini_slug, rest = dispatched.split("/", 1)
            item_type, slug = rest.split(":", 1)
        except ValueError:
            _log.warning("WORKSPACE_MCP_DISPATCHED_ITEM has unexpected shape: %r", dispatched)
            return None
        # Validate each path component to match the AC10 slug guard used in the
        # workspace_status path — prevents a crafted env var from widening the
        # commit pattern (defense-in-depth; the env var is set by the orchestrator).
        for component in (ini_slug, slug):
            if not _is_safe_slug(component):
                _log.warning(
                    "WORKSPACE_MCP_DISPATCHED_ITEM contains unsafe slug %r; "
                    "git_commit will be unavailable",
                    component,
                )
                return None
        try:
            manifest = _LIFECYCLE_MANIFEST.get(item_type, {})
            raw_patterns = manifest.get("output_pattern")
            if raw_patterns is None:
                return None
            patterns_list: list[str] = (
                raw_patterns if isinstance(raw_patterns, list) else [raw_patterns]
            )
            # Apply agentbundle-layout.toml overrides (user-scope > repo-scope > default).
            # Stage 1: resolve at bind-time; Stage 2 defers to first git_branch() call.
            patterns_list = self._apply_layout_overrides(item_type, patterns_list)
            return [p.format(slug=slug) for p in patterns_list]
        except Exception:
            return None

    # Maps item_type → (layout_toml_key, default_base_in_pattern)
    _LAYOUT_TYPE_BASES: dict[str, tuple[str, str]] = {
        "research": ("research", "docs/product/research"),
        "shape": ("product", "docs/product"),
        "strategy": ("product", "docs/product"),
        "design": ("design", "docs/design"),
    }

    def _apply_layout_overrides(
        self, item_type: str, patterns: list[str]
    ) -> list[str]:
        """Substitute configured output_dir into patterns per layout.toml precedence."""
        if item_type not in self._LAYOUT_TYPE_BASES:
            return patterns
        toml_key, default_base = self._LAYOUT_TYPE_BASES[item_type]
        layout = self._read_layout_bases()
        configured = layout.get(toml_key)
        if configured is None:
            return patterns
        return [p.replace(default_base, configured, 1) for p in patterns]

    def _read_layout_bases(self) -> dict[str, str]:
        """Read output_dir from agentbundle-layout.toml with type-specific precedence.

        research: user-scope wins (personal vault applies across repos).
        product, design: repo-scope wins (team convention takes priority).
        """
        import tomllib

        def _read_scope(path: Path) -> dict[str, str]:
            if not path.exists() or path.is_symlink():
                return {}
            out: dict[str, str] = {}
            with contextlib.suppress(Exception):
                with path.open("rb") as fh:
                    data = tomllib.load(fh)
                for key in ("research", "product", "design"):
                    if isinstance(data.get(key), dict):
                        raw = data[key].get("output_dir", "")
                        if raw:
                            out[key] = str(Path(raw).expanduser().resolve())
            return out

        repo = _read_scope(self._repo_root / "agentbundle-layout.toml")
        user = _read_scope(Path.home() / ".agentbundle" / "agentbundle-layout.toml")
        result: dict[str, str] = {}
        # research: user-scope wins
        result["research"] = user.get("research") or repo.get("research", "")
        # product/design: repo-scope wins
        result["product"] = repo.get("product") or user.get("product", "")
        result["design"] = repo.get("design") or user.get("design", "")
        return {k: v for k, v in result.items() if v}

    def _read_head_branch(self) -> str | None:
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, encoding="utf-8",
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
                env=_git_env(),
            )
            if r.returncode == 0:
                return r.stdout.strip()
        return None

    def git_status(self) -> dict:
        r = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
            env=_git_env(),
        )
        return {"output": r.stdout, "returncode": r.returncode}

    def git_branch(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_branch is not available in discovery mode"}
        if self._fsm_mode:
            return {
                "error": (
                    "git_branch is not available in work-loop (FSM) mode — "
                    "work-loop manages its own git lifecycle"
                )
            }
        name = arguments.get("name", "")
        if arguments.get("base") is not None:
            return {"error": "base parameter not supported; always branches from HEAD"}
        # Validate name via check-ref-format --branch (rejects leading dashes and invalid chars)
        r = subprocess.run(
            ["git", "check-ref-format", "--branch", name],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
            env=_git_env(),
        )
        if r.returncode != 0:
            return {"error": f"invalid branch name: {name!r}"}
        # When a dispatched item is bound, the branch name must match the expected
        # ini_slug/type/slug form derived from WORKSPACE_MCP_DISPATCHED_ITEM (AC14).
        if self._expected_branch is not None and name != self._expected_branch:
            return {
                "error": (
                    f"branch {name!r} does not match the dispatched-item branch "
                    f"{self._expected_branch!r} (AC14)"
                )
            }
        # _git_lock serializes all mutating git operations to prevent index.lock
        # collisions and TOCTOU races on _session_branch across concurrent calls.
        with self._git_lock:
            if self._branch_locked:
                return {
                    "error": (
                        f"session branch already set to {self._session_branch!r}; "
                        "git_branch may only be called once per session (AC14)"
                    )
                }
            # Create and check out (no -- : branch name is an option arg, not a pathspec)
            r = self._run_git(
                ["git", "checkout", "-b", name],
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT,
            )
            if r.returncode != 0:
                return {"error": r.stderr.strip() or f"git checkout -b failed (rc={r.returncode})"}
            self._session_branch = name
            self._branch_locked = True
        return {"branch": name}

    def git_commit(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_commit is not available in discovery mode"}
        if self._fsm_mode:
            return {
                "error": (
                    "git_commit is not available in work-loop (FSM) mode — "
                    "work-loop manages its own git lifecycle"
                )
            }
        message = arguments.get("message", "workspace-mcp: commit artifacts")
        if self._output_pattern is None:
            return {"error": "git_commit unavailable: no output_pattern (work-loop owns git)"}

        # Build scope entries for each pattern (design.md:524-526).
        # Two cases:
        #   file         — no "/*": match the exact resolved file path
        #   wildcard_dir — contains "/*": check containment under static root AND
        #                  first varying component ends with the literal suffix of the
        #                  wildcard component (e.g. research/*-slug/** → suffix="-slug")
        # Note: find("/*") always points at "/" followed by "*", so _remainder always
        # starts with "*" — there is no reachable non-wildcard "dir" case.
        _scope_entries: list[tuple] = []
        for _pat in self._output_pattern:
            _idx = _pat.find("/*")
            if _idx == -1:
                # Exact file
                _scope_entries.append(("file", (self._repo_root / _pat).resolve()))
            else:
                _static = _pat[:_idx]
                _remainder = _pat[_idx + 1:]           # strip leading / only; keep *
                _next_comp = _remainder.split("/")[0]  # first wildcard component
                _dir = (self._repo_root / _static).resolve()
                _suffix = _next_comp.lstrip("*")       # literal suffix after *
                _scope_entries.append(("wildcard_dir", _dir, _suffix))

        def _in_scope(rel_path: str) -> bool:
            try:
                abs_p = (self._repo_root / rel_path).resolve()
                for entry in _scope_entries:
                    if entry[0] == "file":
                        if abs_p == entry[1]:
                            return True
                    else:  # wildcard_dir
                        _, root, sfx = entry
                        if abs_p.is_relative_to(root):
                            first = abs_p.relative_to(root).parts
                            if first and (not sfx or first[0].endswith(sfx)):
                                return True
                return False
            except Exception:
                return False

        with self._git_lock:
            # -z: NUL-delimited output — avoids "old -> new" display for renames.
            # --untracked-files=all: expand untracked dirs so first-run artifacts are visible.
            r = subprocess.run(
                ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                capture_output=True, text=True, encoding="utf-8",
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
                env=_git_env(),
            )
            if r.returncode != 0:
                return {"error": f"git status failed: {r.stderr.strip()}"}
            uncommitted: list[str] = []
            staged_outside: list[str] = []
            # NUL-delimited records: "XY path" for normal files; for renames "XY new"
            # followed by a separate NUL field containing the old path.
            _fields = r.stdout.split("\0")
            _fi = 0
            while _fi < len(_fields):
                _field = _fields[_fi]
                _fi += 1
                if len(_field) < 4 or _field[2] != " ":
                    continue
                _x, _y = _field[0], _field[1]
                _path = _field[3:]
                # For staged renames/copies: the very next NUL field is the old path.
                # The -z format guarantees exactly one origin field follows R/C with no
                # "XY " prefix — consume it unconditionally (don't heuristic-test it).
                _orig: str | None = None
                if _x in ("R", "C") and _fi < len(_fields):
                    _orig = _fields[_fi]
                    _fi += 1
                uncommitted.append(_path)
                if _orig:
                    uncommitted.append(_orig)
                if _x not in (" ", "?"):
                    if not _in_scope(_path):
                        staged_outside.append(_path)
                    if _orig and not _in_scope(_orig):
                        staged_outside.append(_orig)
            if staged_outside:
                return {
                    "error": (
                        f"refusing commit: {len(staged_outside)} pre-staged file(s) outside "
                        f"output_pattern would be included: {staged_outside[:5]!r}"
                    )
                }
            # Intersect with output_pattern using scope entries
            matched = [p for p in uncommitted if _in_scope(p)]
            if not matched:
                return {"error": "no uncommitted files match the dispatched item's output_pattern"}
            r = self._run_git(
                ["git", "add", "--", *matched],
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT,
            )
            if r.returncode != 0:
                return {"error": f"git add failed: {r.stderr.strip()}"}
            r = self._run_git(
                ["git", "commit", "-m", message],
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT,
            )
            if r.returncode != 0:
                return {"error": f"git commit failed: {r.stderr.strip()}"}
        return {"committed": matched, "message": message}

    def git_push(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_push is not available in discovery mode"}
        if self._fsm_mode:
            return {
                "error": (
                    "git_push is not available in work-loop (FSM) mode — "
                    "work-loop manages its own git lifecycle"
                )
            }
        branch = arguments.get("branch", "")
        with self._git_lock:
            # Require the session branch to have been explicitly established via
            # git_branch(). This prevents pushing the startup branch (e.g. main)
            # before the session has created its own work branch (AC14).
            if not self._branch_locked:
                return {
                    "error": (
                        "git_push requires a session branch established by git_branch(); "
                        "call git_branch() first (AC14)"
                    )
                }
            # Two-sided check under lock: branch arg must equal session-bound
            # branch AND HEAD must equal it. Lock prevents TOCTOU between the
            # HEAD check and the push across concurrent git_branch / git_push calls.
            if not branch or branch != self._session_branch:
                return {
                    "error": (
                        f"branch {branch!r} does not match session branch "
                        f"{self._session_branch!r}"
                    )
                }
            current = self._read_head_branch()
            if current != branch:
                return {"error": f"HEAD is on {current!r}, not {branch!r}"}
            r = self._run_git(
                ["git", "push", "--", "origin", branch],
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT,
            )
            if r.returncode != 0:
                return {"error": f"git push failed: {r.stderr.strip()}"}
        return {"pushed": branch}


# ── _StdioLoop ────────────────────────────────────────────────────────────────

class _StdioLoop:
    """Main MCP stdio loop — JSON-RPC 2.0 over newline-delimited stdin/stdout.

    Frame-size cap: 1 MiB enforced during bounded read (AC16a).
    Malformed JSON: quarantined and discarded with error response (AC16b).
    Unknown request_id on elicitation/create response: discarded (AC16c).
    """

    def __init__(
        self,
        status_tool: _WorkspaceStatusTool,
        elicit_tool: _ElicitTool,
        git_tools: _GitTools,
        shutdown_event: threading.Event,
        request_map: dict,
        write_lock: threading.Lock | None = None,  # unused; kept for API compat
        write_fn=None,
        mcp_initialized: threading.Event | None = None,
    ) -> None:
        self._status = status_tool
        self._elicit = elicit_tool
        self._git = git_tools
        self._shutdown = shutdown_event
        self._request_map = request_map
        # Keep _write_lock as a separate internal lock independent from write_fn's
        # internal lock to avoid re-entrant deadlock: line 1358 acquires _write_lock,
        # then _write() calls _write_fn which acquires the main write_lock.
        self._write_lock = threading.Lock()
        self._write_fn = write_fn
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False
        self._has_elicitation = False
        self._mcp_initialized = mcp_initialized

    def _write(self, msg: dict) -> None:
        if self._write_fn is not None:
            self._write_fn(msg)
            return
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        with self._write_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    def _error_response(self, req_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _ok_response(self, req_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _tool_result(self, req_id: Any, data: Any) -> dict:
        return self._ok_response(req_id, {
            "content": [{"type": "text", "text": json.dumps(data)}]
        })

    def _read_frame(self) -> str | None:
        """Read one line from stdin; enforce byte-accurate frame-size cap.

        The cap is enforced during the read (no full-frame accumulation).
        Counts encoded bytes, not characters, so a 1 MiB cap is 1 MiB.
        Returns None on EOF or if stdin is closed.
        """
        buf: list[str] = []
        byte_total = 0
        while True:
            ch = sys.stdin.read(1)
            if not ch:
                return None  # EOF
            if ch == "\n":
                return "".join(buf)
            byte_total += len(ch.encode("utf-8"))
            if byte_total > _FRAME_SIZE_LIMIT:
                # Drain and quarantine the oversized frame without accumulating it
                _log.warning("frame exceeds 1 MiB cap; quarantining")
                while True:
                    ch2 = sys.stdin.read(1)
                    if not ch2 or ch2 == "\n":
                        break
                raise ValueError("frame-size cap exceeded")
            buf.append(ch)

    def _handle_initialize(self, req_id: Any, params: dict) -> None:
        caps = params.get("capabilities", {})
        self._has_elicitation = "elicitation" in caps
        self._elicit._has_elicitation = self._has_elicitation
        if not self._has_elicitation:
            self._elicit.setup_response_dir()
        self._initialized = True

        tools = self._build_tools_list()
        self._write(self._ok_response(req_id, {
            "protocolVersion": _MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "workspace-mcp", "version": "1.0.0"},
            "tools": tools,
        }))

    def _build_tools_list(self) -> list[dict]:
        return [
            {
                "name": "workspace_status",
                "description": (
                    "Returns the current workspace queue and active-run state. "
                    "Call this at session start before doing any work. "
                    "Response fields: "
                    "ready[] — items that can be dispatched immediately, each with "
                    "ini_slug, type, slug, and dispatch_skill; "
                    "blocked[] — items whose dependencies are not yet met; "
                    "active[] — items currently in progress; "
                    "shaping[] — non-implementation items (research, design, shape, strategy); "
                    "current_state — current work-loop phase name (null when idle); "
                    "gate_pending — true when human input is required before work can continue; "
                    "gate — name of the pending gate (e.g. SPEC-HUMAN-GATE, REVIEW-HUMAN-GATE); "
                    "gate_question — the specific question the work-loop is asking."
                ),
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "elicit",
                "description": (
                    "Send a question to the human operator and wait for their response. "
                    "Use this instead of emitting free-form text whenever you need "
                    "approval, a decision, or clarifying input. "
                    "Blocks until the operator replies or the 300-second timeout expires. "
                    "Returns {response: string} on success, or {error: string} on timeout."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The question or prompt to display to the operator.",
                        },
                        "context": {
                            "type": "string",
                            "description": (
                                "Optional background text shown alongside the question."
                            ),
                        },
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional list of allowed responses. When provided, the "
                                "operator must choose one of these values."
                            ),
                        },
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "git_status",
                "description": (
                    "Use this instead of running 'git status' directly. "
                    "Returns uncommitted file changes in the repo "
                    "(equivalent to git status --short). "
                    "Returns {output: string, returncode: int}."
                ),
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "git_branch",
                "description": (
                    "Use this instead of running 'git checkout -b' directly — "
                    "raw git branch commands bypass the scoping guard that locks "
                    "the session to exactly one branch for the dispatched item. "
                    "Creates and checks out a new feature branch. "
                    "The branch name must follow the ini_slug/type/slug format "
                    "(e.g. my-initiative/work/fix-bug) and must match the dispatched item. "
                    "May only be called once per session; subsequent calls are rejected. "
                    "Not available when no item has been dispatched."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": (
                                "Branch name in ini_slug/type/slug format "
                                "(e.g. my-initiative/work/fix-bug)."
                            ),
                        }
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "git_commit",
                "description": (
                    "Use this instead of running 'git add' and 'git commit' directly — "
                    "raw git commit bypasses the output-path filter and may silently "
                    "include files outside the dispatched item's scope. "
                    "Stages and commits only files under the item's configured output "
                    "paths; unstaged files outside those paths are excluded automatically. "
                    "If any files outside the output paths are already pre-staged (via "
                    "git add), the commit is refused — unstage them first. "
                    "Not available when no item has been dispatched, or for work-loop "
                    "items (work-loop manages its own git lifecycle)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": (
                                "Git commit message. "
                                "Defaults to 'workspace-mcp: commit artifacts'."
                            ),
                        }
                    },
                },
            },
            {
                "name": "git_push",
                "description": (
                    "Use this instead of running 'git push' directly — "
                    "raw git push bypasses the branch check that prevents pushing "
                    "to a branch other than the one established for this session. "
                    "Pushes the session branch to origin. "
                    "The session branch must be established before pushing: "
                    "call git_branch() in a new session, or in a resumed "
                    "dispatched session the branch may already be locked from "
                    "the prior run (no git_branch() call required in that case). "
                    "Not available when no item has been dispatched."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": (
                                "Branch name to push. Must match the session-bound "
                                "branch established by git_branch() or inherited "
                                "from session startup."
                            ),
                        }
                    },
                    "required": ["branch"],
                },
            },
        ]

    def _dispatch_tool(self, req_id: Any, name: str, arguments: dict) -> None:
        """Dispatch tool call in thread pool; write response from worker."""
        def _run() -> None:
            try:
                if name == "workspace_status":
                    result = self._status.call()
                elif name == "elicit":
                    result = self._elicit.call(arguments)
                elif name == "git_status":
                    result = self._git.git_status()
                elif name == "git_branch":
                    result = self._git.git_branch(arguments)
                elif name == "git_commit":
                    result = self._git.git_commit(arguments)
                elif name == "git_push":
                    result = self._git.git_push(arguments)
                else:
                    result = {"error": f"unknown tool: {name!r}"}
            except Exception as exc:
                result = {"error": str(exc)}
            with self._write_lock:
                self._write(self._tool_result(req_id, result))
        self._executor.submit(_run)

    def _handle_client_response(self, msg: dict) -> None:
        """Route a client response (to a server-issued request) to the waiting worker."""
        req_id = str(msg.get("id", ""))
        entry = self._request_map.get(req_id)
        if entry is None:
            _log.warning("unknown request_id %r in client response; discarding", req_id)
            return
        result_event, result_holder = entry
        resp_result = msg.get("result", {})
        if isinstance(resp_result, dict):
            action = resp_result.get("action", "")
            if action == "accept":
                content = resp_result.get("content", {})
                resp_val = content.get("response") if isinstance(content, dict) else None
                if resp_val is not None:
                    result_holder.append(resp_val)
            # decline / cancel: leave result_holder empty → "elicitation produced no response"
        result_event.set()

    def run(self) -> None:
        """Main loop: read frames until stdin closes."""
        while not self._shutdown.is_set():
            try:
                frame = self._read_frame()
            except ValueError:
                # Oversized frame quarantined; send error with null id
                self._write(self._error_response(None, -32600, "frame-size cap exceeded"))
                continue
            if frame is None:
                break  # stdin closed
            frame = frame.strip()
            if not frame:
                continue
            try:
                msg = json.loads(frame)
            except json.JSONDecodeError:
                self._write(self._error_response(None, -32700, "malformed JSON"))
                continue
            if not isinstance(msg, dict):
                continue
            method = msg.get("method", "")
            req_id = msg.get("id")
            params = msg.get("params") or {}

            # Client response to a server-initiated request (no "method" field):
            # route both result and error envelopes so waiting workers are unblocked.
            if not method and req_id is not None and ("result" in msg or "error" in msg):
                self._handle_client_response(msg)
                continue

            if method == "initialize":
                self._handle_initialize(req_id, params)
            elif method == "notifications/initialized":
                # MCP handshake completes when client sends notifications/initialized.
                # Only now is it safe to emit server notifications.
                if self._mcp_initialized is not None:
                    self._mcp_initialized.set()
            elif method == "tools/list":
                self._write(self._ok_response(req_id, {"tools": self._build_tools_list()}))
            elif method == "tools/call":
                name = params.get("name", "")
                args = params.get("arguments") or {}
                self._dispatch_tool(req_id, name, args)
            elif method == "ping":
                self._write(self._ok_response(req_id, {}))
            elif method.startswith("notifications/"):
                pass  # inbound notifications; ignore
            elif req_id is not None:
                self._write(self._error_response(req_id, -32601, f"method not found: {method!r}"))

        self._shutdown.set()
        # cancel_futures=True cancels queued-but-not-started tasks (Python ≥3.9).
        self._executor.shutdown(wait=False, cancel_futures=True)


# ── Session bootstrap ─────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    """Entry point for the workspace-mcp MCP server."""
    # Reconfigure stdio for binary-safe newline-delimited JSON
    sys.stdin.reconfigure(encoding="utf-8", newline="")  # type: ignore[union-attr]
    sys.stdout.reconfigure(encoding="utf-8", newline="")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]

    if argv and "--help" in argv:
        print(__doc__, file=sys.stderr)
        return

    # Resolve repo root
    try:
        repo_root = _get_repo_root()
    except RuntimeError as exc:
        _log.error("cannot start: %s", exc)
        sys.exit(1)

    # Resolve spec_dir from environment (FSM mode)
    spec_path_str = os.environ.get("WORKSPACE_MCP_SPEC_PATH")
    spec_dir: Path | None = None
    if spec_path_str:
        candidate = Path(spec_path_str).resolve()
        with contextlib.suppress(ValueError):
            candidate.relative_to(repo_root)
            spec_dir = candidate

    # Shared state
    shutdown_event = threading.Event()
    mcp_initialized_event = threading.Event()
    request_map: dict = {}
    write_lock = threading.Lock()

    def _write(msg: dict) -> None:
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        with write_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    # Start event bridge — notifications gated until MCP initialize handshake completes
    bridge = _EventBridge(
        repo_root, spec_dir,
        notify_fn=_write,
        mcp_initialized=mcp_initialized_event,
    )
    bridge.start()

    # Build tools
    status_tool = _WorkspaceStatusTool(repo_root, bridge)
    git_tools = _GitTools(repo_root)

    session_id = str(_uuid_mod.uuid4())
    elicit_tool = _ElicitTool(
        has_elicitation=False,       # updated at initialize handshake
        shutdown_event=shutdown_event,
        request_map=request_map,
        write_lock=write_lock,
        write_fn=_write,
        session_id=session_id,
        get_gate_fn=lambda: bridge.get_fsm_state(),
    )

    loop = _StdioLoop(
        status_tool=status_tool,
        elicit_tool=elicit_tool,
        git_tools=git_tools,
        shutdown_event=shutdown_event,
        request_map=request_map,
        write_lock=write_lock,
        write_fn=_write,
        mcp_initialized=mcp_initialized_event,
    )

    # Run until stdin closes (per-session, no port binding)
    try:
        loop.run()
    finally:
        bridge.stop()
        elicit_tool.cleanup()
        # Ensure exit within 5 s (AC22). Non-daemon executor threads from in-flight git
        # subprocesses can outlive the session; the force-exit timer guarantees the
        # process terminates even if a worker is blocked on a 30-second git timeout.
        shutdown_event.set()

        def _force_exit() -> None:
            # AC22: total exit budget is 5 s from stdin close.  Cleanup fits
            # within 3 s (SIGTERM → bounded wait → SIGKILL), leaving 2 s for
            # scheduling overhead, then unconditional exit.
            # Block new subprocess creation before taking the snapshot so worker
            # threads cannot spawn git children between the snapshot and os._exit.
            git_tools.block_new_procs()
            git_tools.terminate_all_procs(grace=3.0)
            os._exit(0)  # noqa: SLF001

        threading.Thread(target=_force_exit, daemon=True, name="workspace-mcp-exit-guard").start()


if __name__ == "__main__":
    main(sys.argv[1:])
