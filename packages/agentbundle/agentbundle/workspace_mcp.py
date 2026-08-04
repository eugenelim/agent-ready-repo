"""agentbundle.workspace_mcp — per-session MCP server (Stage 1).

Entry points
------------
    python3 -m agentbundle.workspace_mcp      # module mode (production)
    python3 -I -m agentbundle.workspace_mcp   # isolated mode (CI / testing)
    python3 workspace_mcp_server.py           # core-pack alias wrapper

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

_MCP_PROTOCOL_VERSION = "2024-11-05"
_FRAME_SIZE_LIMIT = 1 * 1024 * 1024  # 1 MiB
_GIT_TIMEOUT = 30  # seconds
_ELICIT_POLL_TIMEOUT = 300  # seconds
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
uncommitted files, git_commit(paths, message) for the matching paths, then \
git_push(branch) if it is available. Do not skip steps that are available.\
"""

# ── Repo-root helper ──────────────────────────────────────────────────────────

_GIT_OVERRIDE_VARS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
})


def _get_repo_root() -> Path:
    safe_env = {k: v for k, v in os.environ.items() if k not in _GIT_OVERRIDE_VARS}
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", check=False,
        env=safe_env,
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

    candidates = [
        repo_root / ".claude/skills/workspace-status/scripts/workspace_status_engine.py",
        repo_root / ".agents/skills/workspace-status/scripts/workspace_status_engine.py",
        repo_root / ".kiro/skills/workspace-status/scripts/workspace_status_engine.py",
        # Source path (development / pre-build-self):
        Path(__file__).resolve().parents[3]
        / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("workspace_status_engine", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["workspace_status_engine"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise RuntimeError("workspace_status_engine.py not found in any skill root")


# ── _EventBridge ──────────────────────────────────────────────────────────────

class _EventBridge(threading.Thread):
    """Daemon thread: polls .loop-run/events.jsonl every 200 ms.

    Tracks byte offset + inode for torn-write recovery and inode-change reset.
    Maintains internal FSM state (current_state, gate fields) for workspace_status().
    Notifications are generated but NOT relayed to ACP (spike (c) fallback).
    """

    def __init__(self, repo_root: Path, spec_dir: Path | None = None) -> None:
        super().__init__(daemon=True)
        self._repo_root = repo_root
        self._jsonl_path = repo_root / ".loop-run" / "events.jsonl"
        self._spec_dir = spec_dir
        self._lock = threading.Lock()

        # Tracking state
        self._offset: int = 0
        self._inode: int | None = None
        self._buf: str = ""
        self._last_seq: int = -1

        # FSM state (exposed via workspace_status)
        self._current_state: str | None = None
        self._gate_pending: bool = False
        self._gate: str | None = None
        self._gate_question: str | None = None
        self._review_findings: str | None = None

        self._shutdown = threading.Event()

    def stop(self) -> None:
        self._shutdown.set()

    def get_fsm_state(self) -> dict:
        with self._lock:
            return {
                "current_state": self._current_state,
                "gate_pending": self._gate_pending,
                "gate": self._gate,
                "gate_question": self._gate_question,
                "review_findings": self._review_findings,
            }

    def _reset_file_state(self) -> None:
        self._offset = 0
        self._inode = None
        self._buf = ""
        self._current_state = None
        self._gate_pending = False
        self._gate = None
        self._gate_question = None
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
        if not path.exists():
            # File missing — check if it was expected (spec_dir set and engine-state exists)
            if self._spec_dir and (self._spec_dir / "engine-state.json").exists():
                with self._lock:
                    if self._current_state is not None or self._gate_pending:
                        self._reset_file_state()
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
                return

            try:
                with path.open("r", encoding="utf-8") as fh:
                    fh.seek(self._offset)
                    chunk = fh.read(st.st_size - self._offset)
            except OSError:
                return

            self._inode = st.st_ino
            self._offset += len(chunk.encode("utf-8"))
            self._buf += chunk

            # Process complete lines; hold any partial line
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
                seq = event.get("seq")
                if seq is None or seq <= self._last_seq:
                    continue  # dedup
                self._last_seq = seq
                self._apply_event(event)

    def _apply_event(self, event: dict) -> None:
        to_state = event.get("to", "")
        self._current_state = to_state
        if to_state.endswith("-HUMAN-GATE"):
            self._gate_pending = True
            self._gate = to_state
            self._gate_question = self._read_gate_question()
            self._review_findings = self._read_review_findings()
        else:
            self._gate_pending = False
            self._gate = None
            self._gate_question = None
            self._review_findings = None

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

        # Check for events.jsonl (spike (c) fallback)
        jsonl_path = repo_root / ".loop-run" / "events.jsonl"
        fsm_state = self._bridge.get_fsm_state()
        if not jsonl_path.exists() and (repo_root / ".loop-run").exists():
            # .loop-run/ exists but events.jsonl missing → warn
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

        # Work queue items (ready / blocked)
        for cls in result.ready:
            entry = cls.entry
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.path):
                _log.warning("workspace_status: unsafe slug in ready item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get("work", {})
            item: dict[str, Any] = {
                "ini_slug": cls.ini_slug,
                "type": "work",
                "slug": entry.path,
                "dispatch_skill": manifest.get("dispatch_skill"),
            }
            skill = manifest.get("dispatch_skill")
            if skill and not _is_skill_present(skill, repo_root):
                item["available"] = False
                item["required_pack"] = manifest.get("required_pack")
            ready_items.append(item)

        for cls in result.blocked:
            entry = cls.entry
            if not _is_safe_slug(cls.ini_slug) or not _is_safe_slug(entry.path):
                _log.warning("workspace_status: unsafe slug in blocked item; skipping")
                continue
            manifest = _LIFECYCLE_MANIFEST.get("work", {})
            item = {
                "ini_slug": cls.ini_slug,
                "type": "work",
                "slug": entry.path,
                "dispatch_skill": manifest.get("dispatch_skill"),
                "unmet_needs": cls.blocking_needs,
            }
            blocked_items.append(item)

        # Shaping items
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
            }
            skill = manifest.get("dispatch_skill")
            if skill and not _is_skill_present(skill, repo_root):
                item["available"] = False
                item["required_pack"] = manifest.get("required_pack")
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
    ) -> None:
        self._has_elicitation = has_elicitation
        self._shutdown = shutdown_event
        self._request_map = request_map
        self._write_lock = write_lock
        self._write = write_fn
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

        req = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "elicitation/create",
            "params": {
                "message": message,
                "requestedSchema": {
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                },
            },
        }
        if context is not None:
            req["params"]["context"] = context
        if options is not None:
            req["params"]["options"] = options

        with self._write_lock:
            self._write(req)

        # Wait for response from the client
        while not self._shutdown.is_set():
            if result_event.wait(timeout=1.0):
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

        # Poll until overwritten by control plane (temp-and-rename protocol)
        deadline = time.monotonic() + _ELICIT_POLL_TIMEOUT
        while time.monotonic() < deadline:
            if self._shutdown.is_set():
                return {"error": "elicitation cancelled: session shutting down"}
            with contextlib.suppress(Exception):
                raw = response_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                if _ELICIT_RESPONSE_KEY in data:
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
        dispatched = os.environ.get("WORKSPACE_MCP_DISPATCHED_ITEM")
        self._discovery_mode = not spec_path and not dispatched
        self._output_pattern: list[str] | None = self._resolve_output_pattern(dispatched)
        self._session_branch: str | None = self._read_head_branch()

    def _resolve_output_pattern(self, dispatched: str | None) -> list[str] | None:
        if dispatched is None:
            return None
        # dispatched = "ini_slug/type:slug"
        try:
            ini_slug, rest = dispatched.split("/", 1)
            item_type, slug = rest.split(":", 1)
            manifest = _LIFECYCLE_MANIFEST.get(item_type, {})
            patterns = manifest.get("output_pattern")
            if patterns is None:
                return None
            return [p.format(slug=slug) for p in (
                patterns if isinstance(patterns, list) else [patterns]
            )]
        except Exception:
            return None

    def _read_head_branch(self) -> str | None:
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, encoding="utf-8",
                cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
            )
            if r.returncode == 0:
                return r.stdout.strip()
        return None

    def git_status(self) -> dict:
        r = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        return {"output": r.stdout, "returncode": r.returncode}

    def git_branch(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_branch is not available in discovery mode"}
        name = arguments.get("name", "")
        if arguments.get("base") is not None:
            return {"error": "base parameter not supported; always branches from HEAD"}
        # Validate name via check-ref-format --branch (rejects leading dashes and invalid chars)
        r = subprocess.run(
            ["git", "check-ref-format", "--branch", name],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode != 0:
            return {"error": f"invalid branch name: {name!r}"}
        # Create and check out (no -- : branch name is an option arg, not a pathspec)
        r = subprocess.run(
            ["git", "checkout", "-b", name],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode != 0:
            return {"error": r.stderr.strip() or f"git checkout -b failed (exit {r.returncode})"}
        self._session_branch = name
        return {"branch": name}

    def git_commit(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_commit is not available in discovery mode"}
        message = arguments.get("message", "workspace-mcp: commit artifacts")
        if self._output_pattern is None:
            return {"error": "git_commit unavailable: no output_pattern (work-loop owns git)"}
        import fnmatch
        # Get uncommitted paths
        r = subprocess.run(
            ["git", "status", "--short", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode != 0:
            return {"error": f"git status failed: {r.stderr.strip()}"}
        uncommitted = []
        for line in r.stdout.splitlines():
            if len(line) >= 3:
                uncommitted.append(line[3:].strip())
        # Intersect with output_pattern
        matched = [
            p for p in uncommitted
            if any(fnmatch.fnmatch(p, pat) for pat in self._output_pattern)
        ]
        if not matched:
            return {"error": "no uncommitted files match the dispatched item's output_pattern"}
        r = subprocess.run(
            ["git", "add", "--", *matched],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode != 0:
            return {"error": f"git add failed: {r.stderr.strip()}"}
        r = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode != 0:
            return {"error": f"git commit failed: {r.stderr.strip()}"}
        return {"committed": matched, "message": message}

    def git_push(self, arguments: dict) -> dict:
        if self._discovery_mode:
            return {"error": "git_push is not available in discovery mode"}
        branch = arguments.get("branch", "")
        # Two-sided check: branch arg must equal session-bound branch AND HEAD must equal it
        if not branch or branch != self._session_branch:
            return {
                "error": (
                    f"branch {branch!r} does not match session branch {self._session_branch!r}"
                )
            }
        current = self._read_head_branch()
        if current != branch:
            return {"error": f"HEAD is on {current!r}, not {branch!r}"}
        r = subprocess.run(
            ["git", "push", "--", "origin", branch],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._repo_root), timeout=_GIT_TIMEOUT, check=False,
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
    ) -> None:
        self._status = status_tool
        self._elicit = elicit_tool
        self._git = git_tools
        self._shutdown = shutdown_event
        self._request_map = request_map
        self._write_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False
        self._has_elicitation = False
        self._next_server_id = 1
        self._id_lock = threading.Lock()

    def _write(self, msg: dict) -> None:
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        with self._write_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    def _make_server_id(self) -> str:
        with self._id_lock:
            sid = f"srv-{self._next_server_id}"
            self._next_server_id += 1
        return sid

    def _error_response(self, req_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _ok_response(self, req_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _tool_result(self, req_id: Any, data: Any) -> dict:
        return self._ok_response(req_id, {
            "content": [{"type": "text", "text": json.dumps(data)}]
        })

    def _read_frame(self) -> str | None:
        """Read one line from stdin; enforce frame-size cap.

        Returns None on EOF or if stdin is closed.
        """
        buf: list[str] = []
        total = 0
        while True:
            ch = sys.stdin.read(1)
            if not ch:
                return None  # EOF
            if ch == "\n":
                return "".join(buf)
            total += 1
            if total > _FRAME_SIZE_LIMIT:
                # Drain and quarantine the oversized frame
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
                "description": "Return DAG-resolved workspace queue and FSM state.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "elicit",
                "description": "Route a question or approval to the control plane.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "context": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "git_status",
                "description": "Return the current git status.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "git_branch",
                "description": "Create and check out a new branch.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            },
            {
                "name": "git_commit",
                "description": "Stage and commit files matching the item's output_pattern.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            },
            {
                "name": "git_push",
                "description": "Push the session-bound branch to origin.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"branch": {"type": "string"}},
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
        resp_val = resp_result.get("response") if isinstance(resp_result, dict) else None
        if resp_val is not None:
            result_holder.append(resp_val)
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

            # Client response to a server-initiated request (no "method" field)
            if not method and req_id is not None and "result" in msg:
                self._handle_client_response(msg)
                continue

            if method == "initialize":
                self._handle_initialize(req_id, params)
            elif method == "initialized":
                pass  # notification; no response needed
            elif method == "tools/list":
                self._write(self._ok_response(req_id, {"tools": self._build_tools_list()}))
            elif method == "tools/call":
                name = params.get("name", "")
                args = params.get("arguments") or {}
                self._dispatch_tool(req_id, name, args)
            elif method.startswith("notifications/"):
                pass  # inbound notifications; ignore
            elif req_id is not None:
                self._write(self._error_response(req_id, -32601, f"method not found: {method!r}"))

        self._shutdown.set()
        self._executor.shutdown(wait=False)


# ── Session bootstrap ─────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    """Entry point for the workspace-mcp MCP server."""
    # Reconfigure stdio for binary-safe newline-delimited JSON
    sys.stdin.reconfigure(encoding="utf-8", newline="")  # type: ignore[attr-defined]
    sys.stdout.reconfigure(encoding="utf-8", newline="")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[attr-defined]

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
    request_map: dict = {}
    write_lock = threading.Lock()

    # Start event bridge
    bridge = _EventBridge(repo_root, spec_dir)
    bridge.start()

    # Build tools
    status_tool = _WorkspaceStatusTool(repo_root, bridge)
    git_tools = _GitTools(repo_root)

    def _write(msg: dict) -> None:
        line = json.dumps(msg, separators=(",", ":")) + "\n"
        with write_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    elicit_tool = _ElicitTool(
        has_elicitation=False,       # updated at initialize handshake
        shutdown_event=shutdown_event,
        request_map=request_map,
        write_lock=write_lock,
        write_fn=_write,
    )

    loop = _StdioLoop(
        status_tool=status_tool,
        elicit_tool=elicit_tool,
        git_tools=git_tools,
        shutdown_event=shutdown_event,
        request_map=request_map,
    )
    loop._write = _write  # wire up shared write function

    # Run until stdin closes (per-session, no port binding)
    try:
        loop.run()
    finally:
        bridge.stop()
        elicit_tool.cleanup()
        # Ensure exit within 5 s (AC22)
        shutdown_event.set()


if __name__ == "__main__":
    main(sys.argv[1:])
